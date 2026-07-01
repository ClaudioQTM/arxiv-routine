from typer.testing import CliRunner

from arxiv_radar.cli import app


def test_cli_init_config_and_show_config(tmp_path) -> None:
    runner = CliRunner()
    config_path = tmp_path / "arxiv-radar.yaml"

    init_result = runner.invoke(app, ["init-config", "--path", str(config_path)])
    assert init_result.exit_code == 0

    show_result = runner.invoke(app, ["show-config", "--config", str(config_path)])
    assert show_result.exit_code == 0
    assert "waveguide QED" in show_result.stdout

