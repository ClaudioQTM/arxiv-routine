# arXiv Radar

`arxiv-radar` is a notebook-first research tool for theoretical quantum optics and waveguide QED literature monitoring. It queries the official arXiv API, filters recent papers by research keywords, scores them transparently, and writes Markdown and CSV reports.

It does not scrape arXiv HTML pages.

## Notebook-First Workflow

This project is managed with `uv`.

```bash
uv sync
```

After that, use the project virtual environment as your notebook kernel:

```text
/Users/wangyangming/research_project/arxiv-radar/.venv/bin/python
```

The recommended daily workflow is:

1. Open [notebooks/using_arxiv_radar.ipynb](notebooks/using_arxiv_radar.ipynb).
2. Select the `.venv` Python interpreter above as the kernel.
3. Run notebook cells that import `arxiv_radar.workflow.run_radar`.
4. Use pandas tables in the notebook to inspect and triage papers.

`uv` is only needed to create and update the package environment. You do not need to use `uv run arxiv-radar` for normal interactive work.

Minimal notebook example:

```python
from pathlib import Path
from arxiv_radar.workflow import run_radar

radar = run_radar(
    config_path=Path("arxiv-radar.yaml"),
    days=14,
    max_results=50,
)

radar.dataframe.head(10)
```

Write Markdown and CSV reports from the notebook:

```python
radar.write_reports(output_dir=Path("reports"), days=14)
```

## Configuration

Create a default YAML config once from Python:

```python
from pathlib import Path
from arxiv_radar.config import write_default_config

config_path = Path("arxiv-radar.yaml")
if not config_path.exists():
    write_default_config(config_path)
```

This writes `arxiv-radar.yaml` in the current directory. Edit the categories, keyword lists, or optional `author_watchlist` to tune the radar.

After that, read and edit `arxiv-radar.yaml` directly, or inspect it in a notebook:

```python
from pathlib import Path
from arxiv_radar.config import load_config

config = load_config(Path("arxiv-radar.yaml"))
config.model_dump()
```

You can also create temporary in-memory config variants inside a notebook without changing the YAML file.

## CLI Fallback

The CLI is still available for automation or quick terminal runs:

```bash
uv run arxiv-radar --help
```

Fetch and report on papers from the last 7 days:

```bash
uv run arxiv-radar run --days 7
```

Search the last 14 days and request more arXiv results:

```bash
uv run arxiv-radar run --days 14 --max-results 200
```

Override categories from the command line:

```bash
uv run arxiv-radar run --category quant-ph --category physics.optics
```

Filter by the arXiv `updated` timestamp instead of `published`:

```bash
uv run arxiv-radar run --include-updated
```

Reports are written to `reports/` by default:

- `arxiv-radar-YYYY-MM-DD.md`
- `arxiv-radar-YYYY-MM-DD.csv`

## Scoring

The score is intentionally simple:

- High-priority keyword in title: +10
- High-priority keyword in abstract: +5
- Method keyword in title: +8
- Method keyword in abstract: +4
- Broader discovery keyword in title: +4
- Broader discovery keyword in abstract: +2
- Author from watchlist: +10
- Primary category is `quant-ph`: +3
- Each matched keyword: +1

Papers are sorted by score descending, then published date descending.

## arXiv API rate limit

The tool uses `https://export.arxiv.org/api/query`. When more than one API request is needed, it waits at least 3 seconds between requests. Keep scheduled runs modest and avoid tight polling loops.

## Weekly scheduling on macOS

### cron

Edit your crontab:

```bash
crontab -e
```

Run every Monday at 9 AM:

```cron
0 9 * * 1 cd /Users/wangyangming/research_project/arxiv-radar && /opt/homebrew/bin/uv run arxiv-radar run --days 7 --output-dir reports
```

Adjust the `uv` path if `which uv` returns a different location.

### launchd

Create `~/Library/LaunchAgents/com.wangyangming.arxiv-radar.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.wangyangming.arxiv-radar</string>
  <key>ProgramArguments</key>
  <array>
    <string>/opt/homebrew/bin/uv</string>
    <string>run</string>
    <string>arxiv-radar</string>
    <string>run</string>
    <string>--days</string>
    <string>7</string>
  </array>
  <key>WorkingDirectory</key>
  <string>/Users/wangyangming/research_project/arxiv-radar</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key>
    <integer>1</integer>
    <key>Hour</key>
    <integer>9</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>/tmp/arxiv-radar.out</string>
  <key>StandardErrorPath</key>
  <string>/tmp/arxiv-radar.err</string>
</dict>
</plist>
```

Load it:

```bash
launchctl load ~/Library/LaunchAgents/com.wangyangming.arxiv-radar.plist
```

## Future extensions

Good next additions would be email delivery, Zotero export, or LLM-assisted summaries. They are intentionally not part of this first version.
