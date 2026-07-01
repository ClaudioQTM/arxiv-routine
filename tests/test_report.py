from datetime import datetime, timezone

from arxiv_radar.arxiv_api import Paper
from arxiv_radar.report import write_reports


def test_report_generation_writes_markdown_and_csv(tmp_path) -> None:
    paper = Paper(
        title="Waveguide QED with subwavelength arrays",
        authors=["Alice Example"],
        published=datetime(2026, 6, 30, tzinfo=timezone.utc),
        updated=datetime(2026, 6, 30, tzinfo=timezone.utc),
        arxiv_id="2606.12345",
        abstract_url="https://arxiv.org/abs/2606.12345",
        pdf_url="https://arxiv.org/pdf/2606.12345",
        primary_category="quant-ph",
        categories=["quant-ph"],
        summary="We study photon scattering.",
        matched_keywords=["waveguide QED", "photon scattering"],
        score=29,
    )

    markdown_path, csv_path = write_reports(
        [paper],
        tmp_path,
        categories=["quant-ph"],
        days=7,
        include_updated=False,
        generated_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )

    assert markdown_path is not None
    assert csv_path is not None
    assert "Research note:" in markdown_path.read_text(encoding="utf-8")
    assert "matched_keywords" in csv_path.read_text(encoding="utf-8")

