from __future__ import annotations

from arxiv_radar.arxiv_api import Paper
from arxiv_radar.config import RadarConfig
from arxiv_radar.filtering import match_keywords


def score_paper(paper: Paper, config: RadarConfig) -> Paper:
    title = paper.title.casefold()
    summary = paper.summary.casefold()
    score = 0

    score += _score_keywords(config.high_priority_keywords, title, summary, title_points=10, summary_points=5)
    score += _score_keywords(config.method_keywords, title, summary, title_points=8, summary_points=4)
    score += _score_keywords(
        config.broader_discovery_keywords,
        title,
        summary,
        title_points=4,
        summary_points=2,
    )

    if _matches_author_watchlist(paper, config.author_watchlist):
        score += 10
    if paper.primary_category == "quant-ph":
        score += 3

    matched_keywords = paper.matched_keywords or match_keywords(paper, config)
    score += len(matched_keywords)
    return paper.model_copy(update={"matched_keywords": matched_keywords, "score": score})


def score_and_sort_papers(papers: list[Paper], config: RadarConfig) -> list[Paper]:
    scored = [score_paper(paper, config) for paper in papers]
    return sorted(scored, key=lambda paper: (paper.score, paper.published), reverse=True)


def _score_keywords(
    keywords: list[str],
    title: str,
    summary: str,
    title_points: int,
    summary_points: int,
) -> int:
    score = 0
    for keyword in keywords:
        normalized = keyword.casefold()
        if normalized in title:
            score += title_points
        if normalized in summary:
            score += summary_points
    return score


def _matches_author_watchlist(paper: Paper, watchlist: list[str]) -> bool:
    normalized_authors = [author.casefold() for author in paper.authors]
    for watched in watchlist:
        watched_name = watched.casefold()
        if any(watched_name in author for author in normalized_authors):
            return True
    return False

