# pxscraper

Query, filter, and retrieve proteomics dataset metadata from [ProteomeXchange](http://www.proteomexchange.org/).

> **v0.1.0** — Project scaffolding and package structure. CLI commands are stubbed; implementation is in progress.

## Overview

`pxscraper` replaces the original Selenium-based web scraper with a clean, API-driven approach using the ProteomeCentral bulk TSV and per-dataset XML endpoints. No browser or ChromeDriver required.

### Planned commands

```bash
pxscraper fetch      Download the full dataset listing from ProteomeCentral
pxscraper filter     Filter datasets by species, repository, keywords, dates, etc.
pxscraper lookup     Fetch detailed metadata for specific PXD identifiers
```

## Installation

Requires **Python 3.12+** and [uv](https://pypi.org/project/uv/) for package management.

```bash
# From source (development)
git clone https://github.com/LangeLab/pxscraper.git
cd pxscraper
uv sync

# Run the CLI
uv run pxscraper --help
```

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Lint
uv run ruff check src/
```

## Project structure

```bash
src/pxscraper/
├── __init__.py      # Package version
├── cli.py           # Click CLI entry point
├── api.py           # ProteomeCentral API client
├── parse.py         # TSV + XML parsing
├── filter.py        # DataFrame filtering logic
├── models.py        # Column names, constants
└── cache.py         # Local caching
```

## Legacy

The original single-file Selenium scraper is preserved in `legacy/proteomeXchange_scraper.py` for reference.

## License

MIT License. See [LICENSE](LICENSE) for details.
