# CLI Quickstart

## What `pxseek` does

`pxseek` works in three stages:

1. `fetch` downloads the ProteomeCentral summary listing as a clean artifact.
2. `filter` narrows that summary by metadata such as species, repository, keywords, dates, and instruments.
3. `lookup` fetches detailed XML-derived metadata for one or more dataset IDs.

If you only remember one rule, remember this one:

- `filter` expects the clean summary artifact produced by `pxseek fetch`, not the raw ProteomeCentral TSV export.

## First-time workflow

```bash
pxseek fetch -o px_datasets.tsv
pxseek filter -i px_datasets.tsv -s "Homo sapiens" -o human.tsv
pxseek lookup --input human.tsv -o detailed.tsv
```

This gives you:

- `px_datasets.tsv`: the clean summary table.
- `human.tsv`: the filtered subset.
- `detailed.tsv`: the lookup output with description, contacts, DOI, and FTP location.

## Machine-friendly workflow

If you want JSON artifacts for pipelines or notebooks, keep the same command order and change only the format.

```bash
pxseek fetch --format json -o px_datasets.json
pxseek filter -i px_datasets.json -s "Homo sapiens" -o human.json
pxseek lookup --input human.json --format json -o detailed.json
```

If you need stdout for shell pipelines, use `-o -`. Artifact content goes to stdout and status lines go to stderr.

## Common command patterns

```bash
# Force a fresh summary download
pxseek fetch --refresh -o px_datasets.tsv

# Filter by repository and keyword
pxseek filter -i px_datasets.tsv -r PRIDE -k "cancer" -o pride-cancer.tsv

# Filter by instrument family
pxseek filter -i px_datasets.tsv --instrument "Orbitrap|timsTOF" -o instruments.tsv

# Use deep search after narrowing first
pxseek filter -i px_datasets.tsv -s "Homo sapiens" -k "ubiquitylation" --deep --yes -o deep.tsv

# Inspect the final shortlist in detail
pxseek lookup --input deep.tsv -o detailed.tsv
```

## What to read next

- Go to [Search Recipes](Search-Recipes) for biology-first workflows.
- Go to [Data Formats](Data-Formats) for TSV, CSV, and JSON artifact details.
- Go to [Troubleshooting](Troubleshooting) if a command behaves differently than expected.
