# Installation

## Requirements

- Python 3.12, 3.13, or 3.14
- `uv` for the documented development workflow

## Install from source

```bash
git clone https://github.com/LangeLab/pxseek.git
cd pxseek
uv sync
```

Run the CLI from the repo root with:

```bash
uv run pxseek --help
```

## Install from a built wheel

```bash
uv build
uv pip install dist/pxseek-0.4.5-py3-none-any.whl
pxseek --help
```

## Install from PyPI

Use this after a maintainer has published the release to PyPI.

```bash
uv pip install pxseek==0.4.5
```

## Verify the installation

```bash
pxseek --version
pxseek fetch --help
pxseek filter --help
pxseek lookup --help
```
