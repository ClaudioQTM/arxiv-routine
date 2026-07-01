from arxiv_radar.config import RadarConfig, load_config, write_default_config


def test_default_config_has_research_profile() -> None:
    config = RadarConfig()

    assert "quant-ph" in config.categories
    assert "waveguide QED" in config.high_priority_keywords
    assert "Lindblad" in config.method_keywords


def test_write_and_load_config(tmp_path) -> None:
    path = tmp_path / "config.yaml"

    write_default_config(path)
    loaded = load_config(path)

    assert loaded.categories[:2] == ["quant-ph", "physics.optics"]

