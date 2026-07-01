from datetime import datetime, timezone

from arxiv_radar.arxiv_api import Paper
from arxiv_radar.report import papers_to_dataframe
from arxiv_radar.workflow import RadarRun
from arxiv_radar.config import RadarConfig


def test_papers_to_dataframe_is_notebook_friendly() -> None:
    paper = Paper(
        title="Waveguide QED with atomic arrays",
        authors=["Alice Example"],
        published=datetime(2026, 6, 30, tzinfo=timezone.utc),
        updated=datetime(2026, 6, 30, tzinfo=timezone.utc),
        arxiv_id="2606.00001",
        abstract_url="https://arxiv.org/abs/2606.00001",
        pdf_url="https://arxiv.org/pdf/2606.00001",
        primary_category="quant-ph",
        categories=["quant-ph"],
        summary="Photon scattering in arrays.",
        matched_keywords=["waveguide QED", "photon scattering"],
        score=29,
    )

    dataframe = papers_to_dataframe([paper])

    assert list(dataframe.columns)[:4] == ["score", "published", "updated", "title"]
    assert dataframe.loc[0, "matched_keywords"] == "waveguide QED; photon scattering"


def test_radar_run_can_write_reports(tmp_path) -> None:
    radar_run = RadarRun(
        config=RadarConfig(categories=["quant-ph"]),
        raw_papers=[],
        papers=[],
        dataframe=papers_to_dataframe([]),
    )

    markdown_path, csv_path = radar_run.write_reports(output_dir=tmp_path)

    assert markdown_path is not None
    assert csv_path is not None
