# CLI Quickstart

## What pxseek does

The tool has three stages, and you run them in order:

1. **fetch** downloads the full ProteomeXchange summary listing from ProteomeCentral and writes a clean artifact (TSV, CSV, or JSON).
2. **filter** reads that artifact and narrows it down by species, repository, keywords, dates, or instrument.
3. **lookup** takes a shortlist of dataset IDs and fetches detailed XML metadata (description, contacts, publications, FTP links).

One rule matters most. `filter` expects the clean artifact from `pxseek fetch`, not the raw ProteomeCentral TSV export. Follow that and you will be fine.

## The shortest useful workflow

```bash
pxseek fetch -o px_datasets.tsv
pxseek filter -i px_datasets.tsv -s "Homo sapiens" -o human.tsv
pxseek lookup --input human.tsv -o detailed.tsv
```

This gives you three files:

- `px_datasets.tsv`: the clean summary of every dataset on ProteomeXchange.
- `human.tsv`: only the human datasets.
- `detailed.tsv`: full metadata for those human datasets, with descriptions, contacts, DOIs, and FTP locations.

## Commands in detail

### fetch

Downloads and parses the ProteomeCentral summary TSV.

```bash
pxseek fetch -o px_datasets.tsv
```

- `-o`, `--output` (default: `px_datasets.tsv`)
  Output file path. Use `-` for stdout.
- `--format` (default: `auto`)
  Output format: `tsv`, `csv`, `json`, or `auto` (detects from the `-o` suffix when present).
- `--cache-dir` (default: `.pxseek_cache/` in cwd)
  Where cached data lives.
- `--refresh` (default: off)
  Ignore cache and re-download from ProteomeCentral.
- `-v`, `--verbose` (default: off)
  Print progress messages.

If the summary was downloaded in the last 24 hours, `fetch` uses the cached copy. Use `--refresh` to force a fresh download.

ProteomeCentral returns thousands of rows. `fetch` strips HTML from every cell, renames columns to clean names, drops empty rows, and validates dataset IDs. When you use `-o -`, status and diagnostics go to stderr so stdout stays machine-readable.

### filter

Narrows a summary artifact by metadata filters.

```bash
pxseek filter -i px_datasets.tsv -s "Homo sapiens" -k "cancer" -o cancer.tsv
```

- `-i`, `--input` (default: auto-fetch)
  Input artifact from `fetch`. Use `-` to read an artifact from stdin. If omitted, pxseek fetches or uses cache automatically.
- `-o`, `--output` (default: `filtered_datasets.tsv`)
  Output path. Use `-` for stdout.
- `--format` (default: `auto`)
  Output format: `tsv`, `csv`, `json`, `auto`.
- `-s`, `--species` (default: none)
  Species regex (case-insensitive). Example: `"Homo sapiens"`, `"mus|rattus"`.
- `-r`, `--repo` (default: none)
  Repository name or comma-separated list. Example: `"PRIDE"`, `"PRIDE,MassIVE"`.
- `-k`, `--keywords` (default: none)
  Comma-separated keywords or path to a keyword file (one per line).
- `--after` (default: none)
  Include datasets on or after this date (`YYYY-MM-DD`).
- `--before` (default: none)
  Include datasets on or before this date (`YYYY-MM-DD`).
- `--instrument` (default: none)
  Instrument regex (case-insensitive). Example: `"Orbitrap|Q Exactive"`.
- `--keyword-columns` (default: `title,keywords`)
  Comma-separated column names to search for keywords.
- `--match-all`, `-a` (default: off)
  Require ALL keywords to match instead of any one.
- `--deep` (default: off)
  Also search within dataset descriptions (fetches XML for candidates).
- `--delay` (default: `1.0`)
  Seconds between XML requests when using `--deep`.
- `--yes`, `-y` (default: off)
  Skip the confirmation prompt for large `--deep` fetches.
- `--cache-dir` (default: `.pxseek_cache/` in cwd)
  Where cached data lives.
- `-v`, `--verbose` (default: off)
  Print progress messages.

At least one filter is required. If you do not provide `--input`, `filter` will automatically use the cache or download from ProteomeCentral.

**On --deep.** Normal keyword search only looks in the `title` and `keywords` columns (or whatever you set with `--keyword-columns`). With `--deep`, pxseek fetches the XML description for every dataset that passed the other filters and searches there too. This is useful when the biological term you care about is more likely to appear in the abstract than in the short title. Because it fetches one HTTP request per dataset, it can be slow for large shortlists. A confirmation prompt fires when more than 50 datasets need XML. Use `--yes` to skip it in scripts.

**On --match-all.** By default, multiple keywords use OR logic (any keyword can match). With `--match-all`, every keyword must appear in at least one searched column. For example, `-k "cancer,proteomics" --match-all` finds datasets that mention both terms.

**On keyword files.** Instead of typing `-k "child,pediatric,leukemia"` on the command line, you can put one keyword per line in a text file and pass the path: `-k examples/pediatric_cancer_keywords.txt`.

### lookup

Fetches detailed XML metadata for specific PXD identifiers.

```bash
pxseek lookup --ids PXD000001,PXD000002 -o details.tsv
```

- `--ids` (default: none)
  Comma-separated PXD or RPXD identifiers.
- `--ids-file` (default: none)
  File with one identifier per line. Lines starting with `#` are ignored.
- `-i`, `--input` (default: none)
  Artifact from `filter` or `fetch`; uses the `dataset_id` column. Use `-` to read from stdin.
- `-o`, `--output` (default: `lookup_results.tsv`)
  Output path. Use `-` for stdout.
- `--format` (default: `auto`)
  Output format: `tsv`, `csv`, `json`, `auto`.
- `--delay` (default: `1.0`)
  Seconds between XML requests.
- `--cache-dir` (default: `.pxseek_cache/` in cwd)
  Where cached data lives.
- `--yes`, `-y` (default: off)
  Skip the confirmation prompt for large lookups.
- `-v`, `--verbose` (default: off)
  Print progress messages.

You need at least one source of IDs: `--ids`, `--ids-file`, or `--input`. They can be combined; duplicates are removed automatically.

**On confirmation prompts.** When more than 50 datasets need XML fetching, pxseek asks for confirmation and shows the estimated time. Use `--yes` to skip this in scripts.

**On partial failures.** If some datasets fail to fetch or parse, the successful ones are still written to the output file. A warning lists the failed identifiers.

## Machine-friendly workflows

**On artifact format detection.** In `auto` mode, pxseek accepts `.tsv`, `.csv`, `.json`, or no suffix. Unknown suffixes do not silently fall back to TSV anymore. Pass `--format` explicitly if you want to write `results.txt` or another custom extension.

**On output directories.** When you write to a nested path like `results/run1/datasets.json`, pxseek creates the missing parent directories automatically.

### JSON instead of TSV

```bash
pxseek fetch --format json -o px_datasets.json
pxseek filter -i px_datasets.json -s "Homo sapiens" -o human.json
pxseek lookup --input human.json --format json -o detailed.json
```

### stdout for pipelines

Use `-o -` to send artifact content to stdout and `-i -` or `--input -` to read artifacts from stdin. For stdin artifacts, pxseek auto-detects JSON, TSV, and CSV from the content when no suffix is available. Status messages go to stderr, so they do not pollute piped data.

```bash
pxseek fetch -o - | pxseek filter -i - -s "Homo sapiens" -o - | pxseek lookup --input - -o details.tsv
```

## Common patterns

```bash
# Force a fresh summary download
pxseek fetch --refresh -o px_datasets.tsv

# Filter by repository and keyword
pxseek filter -i px_datasets.tsv -r PRIDE -k "cancer" -o pride-cancer.tsv

# Multiple repositories
pxseek filter -i px_datasets.tsv -r "PRIDE,MassIVE" -o multi-repo.tsv

# Filter by instrument family
pxseek filter -i px_datasets.tsv --instrument "Orbitrap|timsTOF" -o instruments.tsv

# Date range
pxseek filter -i px_datasets.tsv --after 2024-01-01 --before 2024-12-31 -o datasets-2024.tsv

# Keywords from file with AND logic
pxseek filter -i px_datasets.tsv -k examples/pediatric_cancer_keywords.txt --match-all -o pediatric-cancer.tsv

# Deep search after narrowing first
pxseek filter -i px_datasets.tsv -s "Homo sapiens" -k "ubiquitylation" --deep --yes -o deep.tsv

# Inspect the final shortlist in detail
pxseek lookup --input deep.tsv -o detailed.tsv
```

## What to read next

- [Search Recipes](Search-Recipes) has biology-focused workflows.
- [Data Formats](Data-Formats) describes the column layout of each artifact.
- [Python API](Python-API) covers the same features from Python code.
- [Troubleshooting](Troubleshooting) if something does not work as expected.
