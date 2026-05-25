# Installation

## Requirements

- Python 3.12, 3.13, or 3.14
- pip or [uv](https://docs.astral.sh/uv/) for package management
- An internet connection (first fetch downloads from ProteomeCentral)

## Install from source (recommended for development)

```bash
git clone https://github.com/LangeLab/pxseek.git
cd pxseek
uv sync
```

This creates a virtual environment and installs all runtime dependencies. Run the CLI from the repo root:

```bash
uv run pxseek --help
```

The repo includes a pinned `uv.lock` and a `.python-version` file, so you get the same dependency versions every time.

## Install with pip from source

If you do not use uv:

```bash
git clone https://github.com/LangeLab/pxseek.git
cd pxseek
pip install .
```

## Install from PyPI

After a maintainer publishes a release:

```bash
pip install pxseek
```

Or pin a specific version:

```bash
pip install pxseek==0.5.1
```

## Optional extras

- `pxseek[dev]` installs pytest and ruff for running tests and linting.
- `pxseek[rich]` enables richer terminal output (used automatically when available).

With uv:

```bash
uv sync --extra dev
uv sync --extra rich
```

With pip:

```bash
pip install "pxseek[dev,rich]"
```

## Included example files

The repo ships with a keyword file at `examples/pediatric_cancer_keywords.txt`. You can pass this file directly to `pxseek filter -k` (see [Search Recipes](Search-Recipes)).

## Verify the installation

```bash
pxseek --version
pxseek fetch --help
pxseek filter --help
pxseek lookup --help
```

Each `--help` flag should print the command's options and exit cleanly.
