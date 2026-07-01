from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from arxiv_radar.arxiv_api import Paper, fetch_papers
from arxiv_radar.config import RadarConfig, load_config
from arxiv_radar.filtering import filter_recent_papers
from arxiv_radar.report import papers_to_dataframe, write_reports
from arxiv_radar.scoring import score_and_sort_papers


@dataclass(frozen=True)
class RadarRun:
    """Notebook-friendly result object for one arXiv Radar run."""

    config: RadarConfig
    raw_papers: list[Paper]
    papers: list[Paper]
    dataframe: pd.DataFrame

    def write_reports(
        self,
        output_dir: Path = Path("reports"),
        days: int = 7,
        include_updated: bool = False,
        markdown: bool = True,
        csv: bool = True,
    ) -> tuple[Path | None, Path | None]:
        return write_reports(
            self.papers,
            output_dir=output_dir,
            categories=self.config.categories,
            days=days,
            include_updated=include_updated,
            markdown=markdown,
            csv=csv,
        )


def run_radar(
    config_path: Path | None = None,
    days: int = 7,
    max_results: int = 100,
    include_updated: bool = False,
    categories: list[str] | None = None,
) -> RadarRun:
    """Fetch, filter, score, and return papers for interactive notebooks."""
    config = load_config(config_path).with_categories(categories)
    raw_papers = fetch_papers(
        keywords=config.all_keywords,
        categories=config.categories,
        max_results=max_results,
    )
    filtered = filter_recent_papers(
        raw_papers,
        config,
        days=days,
        include_updated=include_updated,
    )
    papers = score_and_sort_papers(filtered, config)
    return RadarRun(
        config=config,
        raw_papers=raw_papers,
        papers=papers,
        dataframe=papers_to_dataframe(papers),
    )
