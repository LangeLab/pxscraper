# Python API

pxseek is CLI-first, but it exposes a small documented Python API for code that should not need to shell out to the CLI. The same functions, cache, and artifact formats work in both paths.

## Stable entry points

Import from the package root:

```python
from pxseek import (
    fetch_datasets,
    filter_datasets,
    lookup_datasets,
    FetchResult,
    LookupResult,
    read_artifact,
    render_artifact,
    write_artifact,
)
```

These six functions and two dataclasses are the stable surface for the 0.5.x series. Everything else in the package is implementation detail.

## fetch_datasets()

Downloads, parses, and caches the ProteomeXchange summary table.

```python
from pxseek import fetch_datasets

result = fetch_datasets()
summary_df = result.df
```

**Parameters**

- `refresh` (`bool`, default `False`)
  When True, bypass the cache and download fresh data.
- `cache_dir` (`Path | str | None`, default `None`)
  Base directory for `.pxseek_cache/`. Defaults to current working directory.
- `use_stale_on_error` (`bool`, default `True`)
  When True, return cached data if the network request fails with a connection error or timeout.

**Returns**

A `FetchResult` dataclass with these fields:

- `df` (`pd.DataFrame`)
  Clean summary with 9 columns (see [Data Formats](Data-Formats)).
- `from_cache` (`bool`)
  True if the data came from the local cache.
- `stale_fallback` (`bool`)
  True if stale cached data was returned after a network failure.
- `parse_result` (`ParseResult | None`)
  Parse diagnostics for freshly downloaded data. None when served from cache.

```python
result = fetch_datasets()
print(result.from_cache)          # True or False
print(result.stale_fallback)      # True if network failed and stale cache was used
print(len(result.df))             # Row count
```

## filter_datasets()

Filters a summary DataFrame using the same rules as the CLI.

```python
from pxseek import fetch_datasets, filter_datasets

summary_df = fetch_datasets().df
filtered_df, summary = filter_datasets(
    summary_df,
    species="Homo sapiens",
    keywords="cancer, proteomics",
    match_all=True,
)
```

**Parameters**

- `df` (`pd.DataFrame`, required)
  Clean summary DataFrame from `fetch_datasets()`.
- `species` (`str | None`, default `None`)
  Species regex (case-insensitive).
- `repository` (`str | None`, default `None`)
  Comma-separated repository names.
- `keywords` (`str | None`, default `None`)
  Comma-separated keywords or path to a keyword file.
- `keyword_columns` (`str | None`, default `None`)
  Comma-separated column names to search (defaults to `title,keywords`).
- `after` (`str | None`, default `None`)
  Lower date bound in YYYY-MM-DD format.
- `before` (`str | None`, default `None`)
  Upper date bound in YYYY-MM-DD format.
- `instrument` (`str | None`, default `None`)
  Instrument regex (case-insensitive).
- `match_all` (`bool`, default `False`)
  When True, all keywords must match (AND logic).
- `deep` (`bool`, default `False`)
  When True, also search within XML descriptions. Requires `keywords`.
- `cache_dir` (`Path | str | None`, default `None`)
  Cache directory used by deep search for XML files.
- `delay` (`float`, default `1.0`)
  Seconds between XML requests during deep search.

**Returns**

A tuple of `(pd.DataFrame, dict)`.

The DataFrame is the filtered subset with the same columns as the input. When `deep=True`, it also includes a `description` column.

The summary dict contains:

- `original_count` (`int`)
  Rows before any filtering.
- `filtered_count` (`int`)
  Rows after all filters.
- `active_filters` (`list[str]`)
  Human-readable descriptions of each active filter.
- `nat_count` (`int`)
  Number of unparseable dates dropped (only present when a date filter is active).

```python
filtered_df, summary = filter_datasets(summary_df, species="Homo sapiens")
print(summary["original_count"])    # e.g. 50000
print(summary["filtered_count"])    # e.g. 12000
print(summary["active_filters"])    # ["species: Homo sapiens"]
```

## lookup_datasets()

Fetches detailed XML metadata for specific dataset identifiers.

```python
from pxseek import lookup_datasets

result = lookup_datasets(["PXD000001", "PXD000002"])
details_df = result.df
```

**Parameters**

- `dataset_ids` (`Iterable[str]`, required)
  PXD or RPXD identifiers. Validated before any HTTP request.
- `cache_dir` (`Path | str | None`, default `None`)
  Base directory for `.pxseek_cache/`.
- `delay` (`float`, default `1.0`)
  Seconds between uncached XML requests.

**Returns**

A `LookupResult` dataclass with these fields:

- `df` (`pd.DataFrame`)
  Parsed metadata rows for successfully fetched datasets.
- `failed_ids` (`list[str]`)
  Identifiers that could not be fetched or parsed.

The DataFrame has 19 columns covering title, description, species, instruments, modifications, contacts, publications, keywords, FTP location, and more. See [Data Formats](Data-Formats) for the full list.

```python
result = lookup_datasets(["PXD000001", "PXD999999"])
print(len(result.df))           # Successful rows
print(result.failed_ids)        # ["PXD999999"] if that one failed
```

## Artifact helpers

These three functions let Python code produce and consume the same file formats as the CLI.

### read_artifact(path, format=None)

Read a TSV, CSV, or JSON artifact into a DataFrame. Format is inferred from the file suffix unless overridden. If `path` is `"-"`, the helper reads from stdin and auto-detects JSON, TSV, or CSV from the content when no explicit format is given.

```python
from pxseek import read_artifact

df = read_artifact("results.tsv")
df = read_artifact("results.json")
df = read_artifact("-", format="json")
df = read_artifact("data.csv", format="csv")
```

### render_artifact(df, format="tsv")

Turn a DataFrame into text for stdout or an API response.

```python
from pxseek import render_artifact

json_text = render_artifact(df, format="json")
tsv_text = render_artifact(df, format="tsv")
```

### write_artifact(df, path, format=None)

Write a DataFrame to disk. Format is inferred from the file suffix unless overridden. In `auto` mode, `.tsv`, `.csv`, `.json`, and no suffix are accepted. Unknown suffixes raise an error unless you pass `format=` explicitly. Missing parent directories are created automatically.

```python
from pxseek import write_artifact

write_artifact(df, "results.tsv")
write_artifact(df, "results.json")
write_artifact(df, "results.csv", format="csv")
```

Supported formats: `tsv`, `csv`, `json`.

## Full workflow example

```python
from pxseek import fetch_datasets, filter_datasets, lookup_datasets

# Step 1: fetch the summary
fetch_result = fetch_datasets()
summary_df = fetch_result.df
print(f"Fetched {len(summary_df)} datasets (from cache: {fetch_result.from_cache})")

# Step 2: filter
filtered_df, summary = filter_datasets(
    summary_df,
    species="Homo sapiens",
    keywords="cancer, phosphoproteomics",
    match_all=False,
)
print(f"Filtered to {len(filtered_df)} datasets")
print(f"Active filters: {summary['active_filters']}")

# Step 3: lookup details
lookup_result = lookup_datasets(filtered_df["dataset_id"])
print(f"Looked up {len(lookup_result.df)} datasets")
print(f"Failed: {lookup_result.failed_ids}")

# Step 4: use the results
detailed_df = lookup_result.df
for _, row in detailed_df.iterrows():
    print(f"{row['dataset_id']}: {row['title']} ({row['species']})")
    print(f"  FTP: {row['ftp_location']}")
    print(f"  PubMed: {row['pubmed_ids']}")
```

## Notes for workflow code

- The workflow API shares the same local cache as the CLI. A fetch in Python means the CLI sees it, and vice versa.
- `fetch_datasets(use_stale_on_error=True)` returns cached data when the network is down, matching the CLI behavior.
- `filter_datasets()` with `deep=True` fetches XML for each candidate dataset. This can be slow for large shortlists. Use `cache_dir` to persist XML across runs.
- `lookup_datasets()` validates all identifiers before making any HTTP requests. It raises `ValueError` if any ID is invalid.
- The artifact helpers produce the exact same output as the CLI. A TSV written by `write_artifact()` can be read by `pxseek filter -i`.
