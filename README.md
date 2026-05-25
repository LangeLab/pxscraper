<!-- markdownlint-disable MD010 MD033 MD036 MD041 -->
<p align="center">
  <h1 align="center">pxseek</h1>
</p>

<p align="center">
  Query, filter, and retrieve proteomics dataset metadata from <a href="http://www.proteomexchange.org/">ProteomeXchange</a>.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12--3.14-2D7D46?style=flat-square&logo=python&logoColor=white" alt="Python 3.12-3.14">
  <img src="https://img.shields.io/badge/version-0.4.5-8B5CF6?style=flat-square" alt="v0.4.5">
  <img src="https://img.shields.io/badge/status-beta-C17D10?style=flat-square" alt="Beta">
  <img src="https://img.shields.io/badge/tests-269%20passed-22C55E?style=flat-square" alt="269 tests">
  <img src="https://img.shields.io/badge/license-MIT-4B9D6E?style=flat-square" alt="MIT">
</p>

<p align="center">
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/changelog-CHANGELOG-E05D44?style=flat-square" alt="Changelog"></a>
  <a href="CITATION.cff"><img src="https://img.shields.io/badge/cite-CITATION.cff-0066CC?style=flat-square" alt="Citation"></a>
  <a href="https://github.com/LangeLab/pxseek/wiki"><img src="https://img.shields.io/badge/docs-GitHub%20Wiki-0F766E?style=flat-square" alt="Wiki"></a>
</p>

`pxseek` replaces the original Selenium-based web scraper with a clean, API-driven approach using the ProteomeCentral bulk TSV and per-dataset XML endpoints. No browser or ChromeDriver required.

## Commands

| Command         | Status        | Description                                                   |
| --------------- | ------------- | ------------------------------------------------------------- |
| `pxseek fetch`  | **Available** | Download the full dataset listing from ProteomeCentral        |
| `pxseek filter` | **Available** | Filter datasets by species, repository, keywords, dates, etc. |
| `pxseek lookup` | **Available** | Fetch detailed metadata for specific PXD identifiers          |

## Installation

Requires **Python 3.12-3.14** and [uv](https://pypi.org/project/uv/) for package management.

```bash
git clone https://github.com/LangeLab/pxseek.git
cd pxseek
uv sync
```

## CLI Quickstart

The shortest useful workflow is:

```bash
uv run pxseek fetch -o px_datasets.tsv
uv run pxseek filter -i px_datasets.tsv -s "Homo sapiens" -k "cancer" -o shortlist.tsv
uv run pxseek lookup --input shortlist.tsv -o detailed.tsv
```

This gives you:

- `px_datasets.tsv`: the cleaned summary table
- `shortlist.tsv`: your filtered subset
- `detailed.tsv`: detailed XML-derived metadata for the shortlist

One rule matters most:

- `filter` expects the cleaned TSV written by `pxseek fetch`, not the raw ProteomeCentral export.

Use the docs for everything beyond that minimal path.

## Documentation

More detailed documentation and examples live in the [GitHub wiki](https://github.com/LangeLab/pxseek/wiki).

The repository `wiki/` folder tracks the same pages in markdown:

- [Installation](wiki/Installation.md)
- [CLI Quickstart](wiki/CLI-Quickstart.md)
- [Data Formats](wiki/Data-Formats.md)
- [Search Recipes](wiki/Search-Recipes.md)
- [Troubleshooting and FAQ](wiki/Troubleshooting.md)

## Development

The local development workflow matches CI.

```bash
uv sync --extra dev
uv run --extra dev pytest
uv run --extra dev ruff check src/ tests/
uv run --extra dev ruff format --check src/ tests/
uv build
```

## Project structure

```bash
src/pxseek/
├── __init__.py      # Package version
├── cli.py           # Click CLI entry point
├── api.py           # ProteomeCentral API client (polite User-Agent, rate-limited)
├── parse.py         # TSV + XML parsing (HTML stripping, column mapping)
├── cache.py         # Local caching with staleness check
├── models.py        # Column names, constants, configuration
└── filter.py        # DataFrame filtering logic
```

## Legacy

The original single-file Selenium scraper is preserved in `legacy/proteomeXchange_scraper.py` for reference.

## Citation

If you use pxseek in your work, please cite it:

```bibtex
@software{pxseek2025,
  title = {pxseek: Query, filter, and retrieve proteomics dataset metadata from ProteomeXchange},
  author = {Enes K. Ergin and Kimia Rostin and Philipp F. Lange},
  year = {2025},
  url = {https://github.com/LangeLab/pxseek},
  version = {0.4.5},
}
```

A `CITATION.cff` file is also available in the repository root.

## License

MIT License. See [LICENSE](LICENSE) for details.
