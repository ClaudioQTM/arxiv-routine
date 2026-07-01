from datetime import datetime, timezone

from arxiv_radar.arxiv_api import Paper
from arxiv_radar.config import RadarConfig
from arxiv_radar.filtering import filter_recent_papers, match_keywords


def make_paper(title: str, summary: str, published: datetime, updated: datetime | None = None) -> Paper:
    return Paper(
        title=title,
        authors=["A. Author"],
        published=published,
        updated=updated or published,
        arxiv_id="2606.00001",
        abstract_url="https://arxiv.org/abs/2606.00001",
        pdf_url="https://arxiv.org/pdf/2606.00001",
        primary_category="quant-ph",
        categories=["quant-ph"],
        summary=summary,
    )


def test_match_keywords_case_insensitive() -> None:
    paper = make_paper(
        title="Few-Photon Scattering in a Waveguide",
        summary="A resolvent method.",
        published=datetime(2026, 6, 30, tzinfo=timezone.utc),
    )

    matched = match_keywords(paper, RadarConfig())

    assert "few-photon scattering" in matched
    assert "resolvent" in matched


def test_filter_recent_papers_uses_published_by_default() -> None:
    now = datetime(2026, 7, 1, tzinfo=timezone.utc)
    old_but_updated = make_paper(
        title="Waveguide QED",
        summary="photon scattering",
        published=datetime(2026, 6, 1, tzinfo=timezone.utc),
        updated=datetime(2026, 6, 30, tzinfo=timezone.utc),
    )

    assert filter_recent_papers([old_but_updated], RadarConfig(), days=7, now=now) == []
    assert filter_recent_papers(
        [old_but_updated],
        RadarConfig(),
        days=7,
        include_updated=True,
        now=now,
    )


def test_filter_drops_papers_without_matched_keyword() -> None:
    now = datetime(2026, 7, 1, tzinfo=timezone.utc)
    paper = make_paper(
        title="Unrelated condensed matter topic",
        summary="No configured phrases here.",
        published=datetime(2026, 6, 30, tzinfo=timezone.utc),
    )

    assert filter_recent_papers([paper], RadarConfig(), days=7, now=now) == []

