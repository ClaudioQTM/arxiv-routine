from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from arxiv_radar import __version__
from arxiv_radar.arxiv_api import ArxivApiError
from arxiv_radar.config import (
    DEFAULT_CONFIG_PATH,
    config_to_yaml,
    load_config,
    write_default_config,
)
from arxiv_radar.report import write_reports
from arxiv_radar.workflow import run_radar


app = typer.Typer(help="Collect and rank recent arXiv papers for a research profile.")
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"arxiv-radar {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", callback=version_callback, is_eager=True, help="Show version and exit."),
    ] = False,
) -> None:
    return None


@app.command("init-config")
def init_config(
    path: Annotated[Path, typer.Option("--path", "-p", help="Path to write the YAML config.")] = DEFAULT_CONFIG_PATH,
    force: Annotated[bool, typer.Option("--force", help="Overwrite an existing config file.")] = False,
) -> None:
    """Write a default YAML config file."""
    try:
        written = write_default_config(path, overwrite=force)
    except FileExistsError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    console.print(f"[green]Wrote config:[/green] {written}")


@app.command("show-config")
def show_config(
    config: Annotated[Path | None, typer.Option("--config", help="Path to a YAML config file.")] = None,
) -> None:
    """Print the active config."""
    try:
        active_config = load_config(config)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    console.print(config_to_yaml(active_config))


@app.command("run")
def run(
    config: Annotated[Path | None, typer.Option("--config", help="Path to a YAML config file.")] = None,
    days: Annotated[int, typer.Option("--days", min=1, help="Keep papers from the last N days.")] = 7,
    max_results: Annotated[int, typer.Option("--max-results", min=1, help="Maximum arXiv API results.")] = 100,
    output_dir: Annotated[Path, typer.Option("--output-dir", help="Directory for reports.")] = Path("reports"),
    markdown: Annotated[bool, typer.Option("--markdown/--no-markdown", help="Write a Markdown report.")] = True,
    csv: Annotated[bool, typer.Option("--csv/--no-csv", help="Write a CSV report.")] = True,
    include_updated: Annotated[
        bool,
        typer.Option("--include-updated", help="Filter by updated date instead of published date."),
    ] = False,
    category: Annotated[
        list[str] | None,
        typer.Option("--category", help="Override config categories. Repeatable."),
    ] = None,
    verbose: Annotated[bool, typer.Option("--verbose", help="Print extra run details.")] = False,
) -> None:
    """Query arXiv, filter, score, and write reports."""
    try:
        active_config = load_config(config).with_categories(category)
        if not markdown and not csv:
            raise ValueError("At least one of --markdown or --csv must be enabled.")

        if verbose:
            _print_run_table(active_config.categories, days, max_results, include_updated)

        with console.status("Querying arXiv API..."):
            radar_run = run_radar(
                config_path=config,
                days=days,
                max_results=max_results,
                include_updated=include_updated,
                categories=category,
            )
        markdown_path, csv_path = write_reports(
            radar_run.papers,
            output_dir=output_dir,
            categories=radar_run.config.categories,
            days=days,
            include_updated=include_updated,
            markdown=markdown,
            csv=csv,
        )
    except (ArxivApiError, FileNotFoundError, ValueError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc

    console.print(f"[green]Found {len(radar_run.papers)} matching paper(s).[/green]")
    if markdown_path:
        console.print(f"Markdown: {markdown_path}")
    if csv_path:
        console.print(f"CSV: {csv_path}")


def _print_run_table(categories: list[str], days: int, max_results: int, include_updated: bool) -> None:
    table = Table(title="arXiv Radar Run")
    table.add_column("Setting")
    table.add_column("Value")
    table.add_row("Categories", ", ".join(categories))
    table.add_row("Days", str(days))
    table.add_row("Max results", str(max_results))
    table.add_row("Date field", "updated" if include_updated else "published")
    console.print(table)


if __name__ == "__main__":
    app()
