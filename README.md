<!-- markdownlint-disable MD010 MD033 MD036 MD041 -->
<p align="center">
  <img src="https://raw.githubusercontent.com/LangeLab/pxseek/main/assets/banner.svg" width="240" alt="pxseek"/>
</p>

<p align="center">
  Query, filter, and retrieve proteomics dataset metadata from <a href="https://www.proteomexchange.org/">ProteomeXchange</a>.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12--3.14-2D7D46?style=flat-square&logo=python&logoColor=white" alt="Python 3.12-3.14">
  <img src="https://img.shields.io/badge/version-0.5.1-8B5CF6?style=flat-square" alt="v0.5.1">
  <img src="https://img.shields.io/badge/status-beta-C17D10?style=flat-square" alt="Beta">
  <a href="https://github.com/LangeLab/pxseek/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/LangeLab/pxseek/ci.yml?branch=main&style=flat-square&label=ci" alt="CI"></a>
  <img src="https://img.shields.io/badge/tests-302%20passed-22C55E?style=flat-square" alt="302 tests passed">
  <img src="https://img.shields.io/badge/license-MIT-4B9D6E?style=flat-square" alt="MIT">
</p>

<p align="center">
  <a href="https://github.com/LangeLab/pxseek/blob/main/CHANGELOG.md"><img src="https://img.shields.io/badge/changelog-CHANGELOG-E05D44?style=flat-square" alt="Changelog"></a>
  <a href="https://github.com/LangeLab/pxseek/blob/main/CITATION.cff"><img src="https://img.shields.io/badge/cite-CITATION.cff-0066CC?style=flat-square" alt="Citation"></a>
  <a href="https://github.com/LangeLab/pxseek/wiki"><img src="https://img.shields.io/badge/docs-GitHub%20Wiki-0F766E?style=flat-square" alt="Wiki"></a>
</p>

`pxseek` replaces the original Selenium-based web scraper with a clean, API-driven approach using the ProteomeCentral bulk TSV and per-dataset XML endpoints. No browser or ChromeDriver required.

`pxseek` has three core commands.

- `fetch` downloads the clean summary table.
- `filter` narrows that table by metadata.
- `lookup` fetches richer XML-derived metadata for a shortlist.

## Installation

Requires **Python 3.12-3.14**.

```bash
pip install pxseek
```

Or with `uv`:

```bash
uv tool install pxseek
```

For development setup and source checkout, see the [Installation](https://github.com/LangeLab/pxseek/wiki/Installation) guide.

## CLI Quickstart

The shortest useful workflow is:

```bash
uv run pxseek fetch -o px_datasets.tsv
uv run pxseek filter -i px_datasets.tsv -s "Homo sapiens" -k "cancer" -o shortlist.tsv
uv run pxseek lookup --input shortlist.tsv -o detailed.tsv
```

One rule matters most. `filter` expects the cleaned artifact written by `pxseek fetch`, not the raw ProteomeCentral export.

If you want machine-friendly outputs, use `--format json` or `-o -` and keep the rest of the workflow the same. The detailed format and pipeline behavior live in the docs.

## Python API

`pxseek` is CLI-first, but it exposes a small stable workflow API for code that should not shell out to the CLI.

```python
from pxseek import fetch_datasets, filter_datasets, lookup_datasets

summary = fetch_datasets().df
filtered, _ = filter_datasets(summary, species="Homo sapiens", keywords="cancer")
details = lookup_datasets(filtered["dataset_id"]).df
```

The supported root imports are `fetch_datasets()`, `filter_datasets()`, `lookup_datasets()`, `read_artifact()`, `render_artifact()`, and `write_artifact()`.

## Documentation

More detailed documentation and examples live in the [GitHub wiki](https://github.com/LangeLab/pxseek/wiki).

- [Installation](https://github.com/LangeLab/pxseek/wiki/Installation)
- [CLI Quickstart](https://github.com/LangeLab/pxseek/wiki/CLI-Quickstart)
- [Python API](https://github.com/LangeLab/pxseek/wiki/Python-API)
- [Data Formats](https://github.com/LangeLab/pxseek/wiki/Data-Formats)
- [Search Recipes](https://github.com/LangeLab/pxseek/wiki/Search-Recipes)
- [Troubleshooting and FAQ](https://github.com/LangeLab/pxseek/wiki/Troubleshooting)

## Development

The local development workflow matches CI.

```bash
uv sync --extra dev
uv run --extra dev pytest
uv run --extra dev ruff check src/ tests/
uv run --extra dev ruff format --check src/ tests/
uv build
```

## Legacy

The original single-file Selenium scraper is preserved in `legacy/proteomeXchange_scraper.py` for reference.

## Citation

If you use pxseek in your work, please cite it:

```bibtex
@software{pxseek2026,
  title = {pxseek: Query, filter, and retrieve proteomics dataset metadata from ProteomeXchange},
  author = {Enes K. Ergin and Kimia Rostin and Philipp F. Lange},
  year = {2026},
  url = {https://github.com/LangeLab/pxseek},
  version = {0.5.1},
}
```

A `CITATION.cff` file is also available in the repository root.

## License

MIT License. See [LICENSE](https://github.com/LangeLab/pxseek/blob/main/LICENSE) for details.
