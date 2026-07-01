from __future__ import annotations

from datetime import datetime, timedelta, timezone

from arxiv_radar.arxiv_api import Paper
from arxiv_radar.config import RadarConfig, dedupe_preserve_order


def match_keywords(paper: Paper, config: RadarConfig) -> list[str]:
    title = paper.title.casefold()
    summary = paper.summary.casefold()
    matched = [
        keyword
        for keyword in config.all_keywords
        if keyword.casefold() in title or keyword.casefold() in summary
    ]
    return dedupe_preserve_order(matched)


def filter_recent_papers(
    papers: list[Paper],
    config: RadarConfig,
    days: int,
    include_updated: bool = False,
    now: datetime | None = None,
) -> list[Paper]:
    if days < 1:
        raise ValueError("days must be at least 1.")

    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    cutoff = current_time.astimezone(timezone.utc) - timedelta(days=days)

    kept: list[Paper] = []
    for paper in papers:
        date_value = paper.updated if include_updated else paper.published
        if date_value.astimezone(timezone.utc) < cutoff:
            continue
        matched_keywords = match_keywords(paper, config)
        if not matched_keywords:
            continue
        kept.append(paper.model_copy(update={"matched_keywords": matched_keywords}))
    return kept

