from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from arxiv_radar.arxiv_api import Paper


def write_reports(
    papers: list[Paper],
    output_dir: Path,
    categories: list[str],
    days: int,
    include_updated: bool,
    markdown: bool = True,
    csv: bool = True,
    generated_at: datetime | None = None,
) -> tuple[Path | None, Path | None]:
    if not markdown and not csv:
        raise ValueError("At least one report format must be enabled.")

    output_dir.mkdir(parents=True, exist_ok=True)
    generated = generated_at or datetime.now(timezone.utc)
    markdown_path = (
        write_markdown_report(papers, output_dir, categories, days, include_updated, generated)
        if markdown
        else None
    )
    csv_path = write_csv_report(papers, output_dir, generated) if csv else None
    return markdown_path, csv_path


def write_markdown_report(
    papers: list[Paper],
    output_dir: Path,
    categories: list[str],
    days: int,
    include_updated: bool,
    generated_at: datetime | None = None,
) -> Path:
    generated = generated_at or datetime.now(timezone.utc)
    filename = f"arxiv-radar-{generated.date().isoformat()}.md"
    path = output_dir / filename
    date_field = "updated" if include_updated else "published"

    lines = [
        "# arXiv Radar Report",
        "",
        f"- Generated: {generated.isoformat()}",
        f"- Search window: last {days} days by `{date_field}` date",
        f"- Categories searched: {', '.join(categories)}",
        f"- Papers found: {len(papers)}",
        "",
    ]

    if not papers:
        lines.extend(["No matching papers found.", ""])
    for index, paper in enumerate(papers, start=1):
        lines.extend(_paper_markdown(index, paper))

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_csv_report(
    papers: list[Paper],
    output_dir: Path,
    generated_at: datetime | None = None,
) -> Path:
    generated = generated_at or datetime.now(timezone.utc)
    filename = f"arxiv-radar-{generated.date().isoformat()}.csv"
    path = output_dir / filename
    rows = [_paper_row(paper) for paper in papers]
    columns = [
        "title",
        "authors",
        "published",
        "updated",
        "arxiv_id",
        "abstract_url",
        "pdf_url",
        "primary_category",
        "categories",
        "summary",
        "matched_keywords",
        "score",
    ]
    pd.DataFrame(rows, columns=columns).to_csv(path, index=False)
    return path


def papers_to_dataframe(papers: list[Paper]) -> pd.DataFrame:
    """Return notebook-friendly tabular paper data."""
    columns = [
        "score",
        "published",
        "updated",
        "title",
        "authors",
        "matched_keywords",
        "primary_category",
        "categories",
        "arxiv_id",
        "abstract_url",
        "pdf_url",
        "summary",
    ]
    rows = []
    for paper in papers:
        row = _paper_row(paper)
        rows.append({column: row[column] for column in columns})
    return pd.DataFrame(rows, columns=columns)


def _paper_markdown(index: int, paper: Paper) -> list[str]:
    return [
        f"## {index}. {paper.title}",
        "",
        f"- Score: {paper.score}",
        f"- Authors: {', '.join(paper.authors)}",
        f"- Published: {paper.published.date().isoformat()}",
        f"- Updated: {paper.updated.date().isoformat()}",
        f"- arXiv ID: {paper.arxiv_id}",
        f"- Categories: {', '.join(paper.categories)}",
        f"- Matched keywords: {', '.join(paper.matched_keywords)}",
        f"- Abstract URL: {paper.abstract_url}",
        f"- PDF URL: {paper.pdf_url}",
        "",
        "### Abstract",
        "",
        paper.summary,
        "",
        "### Research note:",
        "",
        "- Why relevant:",
        "- Possible citation use:",
        "- Possible loopholes / assumptions to check:",
        "",
    ]


def _paper_row(paper: Paper) -> dict[str, Any]:
    return {
        "title": paper.title,
        "authors": "; ".join(paper.authors),
        "published": paper.published.isoformat(),
        "updated": paper.updated.isoformat(),
        "arxiv_id": paper.arxiv_id,
        "abstract_url": paper.abstract_url,
        "pdf_url": paper.pdf_url,
        "primary_category": paper.primary_category,
        "categories": "; ".join(paper.categories),
        "summary": paper.summary,
        "matched_keywords": "; ".join(paper.matched_keywords),
        "score": paper.score,
    }
