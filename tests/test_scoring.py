from datetime import datetime, timezone

from arxiv_radar.arxiv_api import Paper
from arxiv_radar.config import RadarConfig
from arxiv_radar.scoring import score_and_sort_papers, score_paper


def make_paper(title: str, summary: str, authors: list[str] | None = None) -> Paper:
    return Paper(
        title=title,
        authors=authors or ["A. Author"],
        published=datetime(2026, 6, 30, tzinfo=timezone.utc),
        updated=datetime(2026, 6, 30, tzinfo=timezone.utc),
        arxiv_id="2606.00002",
        abstract_url="https://arxiv.org/abs/2606.00002",
        pdf_url="https://arxiv.org/pdf/2606.00002",
        primary_category="quant-ph",
        categories=["quant-ph"],
        summary=summary,
    )


def test_score_paper_uses_transparent_rules() -> None:
    config = RadarConfig(author_watchlist=["Watched Author"])
    paper = make_paper(
        title="Waveguide QED via Bethe ansatz",
        summary="We study photon scattering and dark states.",
        authors=["Watched Author"],
    )

    scored = score_paper(paper, config)

    assert scored.score == 10 + 8 + 5 + 2 + 10 + 3 + 4
    assert scored.matched_keywords == ["waveguide QED", "photon scattering", "Bethe ansatz", "dark states"]


def test_score_and_sort_papers_orders_by_score_then_date() -> None:
    config = RadarConfig()
    lower = make_paper("Waveguide QED", "A short note.")
    higher = make_paper("Waveguide QED scattering matrix", "photon scattering")

    ordered = score_and_sort_papers([lower, higher], config)

    assert ordered[0].title == "Waveguide QED scattering matrix"

