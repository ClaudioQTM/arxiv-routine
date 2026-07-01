from pathlib import Path

from arxiv_radar.arxiv_api import build_search_query, parse_feed


def test_build_search_query_targets_title_abstract_and_categories() -> None:
    query = build_search_query(["waveguide QED"], ["quant-ph", "physics.optics"])

    assert 'ti:"waveguide QED"' in query
    assert 'abs:"waveguide QED"' in query
    assert "cat:quant-ph" in query
    assert "cat:physics.optics" in query


def test_parse_feed_from_atom_fixture() -> None:
    xml = Path("tests/fixtures/arxiv_feed.xml").read_text(encoding="utf-8")

    papers = parse_feed(xml)

    assert len(papers) == 1
    paper = papers[0]
    assert paper.title == "Waveguide QED with subwavelength arrays"
    assert paper.authors == ["Alice Example", "Bob Researcher"]
    assert paper.arxiv_id == "2606.12345"
    assert paper.primary_category == "quant-ph"
    assert paper.pdf_url == "http://arxiv.org/pdf/2606.12345v1"

