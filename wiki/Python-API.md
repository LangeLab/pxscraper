# Python API

`pxseek` is designed CLI-first, but it also exposes a small documented Python API for workflow code that should not need to shell out to the CLI.

## Stable entry points

Import from package root:

```python
from pxseek import (
    fetch_datasets,
    filter_datasets,
    lookup_datasets,
    read_artifact,
    render_artifact,
    write_artifact,
)
```

The intended stable workflow surface for `0.5.x` is:

- `fetch_datasets()`
- `filter_datasets()`
- `lookup_datasets()`
- `read_artifact()`
- `render_artifact()`
- `write_artifact()`

Everything else should be treated as lower-level implementation detail unless documented separately.

## Artifact helpers

The artifact helpers give Python workflows the same file and stdout formats as the CLI.

- `read_artifact(path)`: read `tsv`, `csv`, or `json` into a DataFrame.
- `render_artifact(df, format="json")`: turn a DataFrame into text for stdout or an API response.
- `write_artifact(df, path)`: write a DataFrame to disk, inferring format from the file suffix unless overridden.

Supported formats are:

- `tsv`
- `csv`
- `json`

Examples:

```python
from pxseek import fetch_datasets, render_artifact, write_artifact

summary_df = fetch_datasets().df
write_artifact(summary_df, "datasets.json")
json_text = render_artifact(summary_df, format="json")
```

## Minimal example

```python
from pxseek import fetch_datasets, filter_datasets, lookup_datasets

fetch_result = fetch_datasets()
summary_df = fetch_result.df

filtered_df, filter_summary = filter_datasets(
    summary_df,
    species="Homo sapiens",
    keywords="cancer, phosphoproteomics",
    match_all=False,
)

lookup_result = lookup_datasets(filtered_df["dataset_id"])

print(fetch_result.from_cache)
print(filter_summary)
print(lookup_result.df.head())
print(lookup_result.failed_ids)
```

## What each function returns

### `fetch_datasets()`

Returns a `FetchResult` dataclass with:

- `df`: clean summary DataFrame.
- `from_cache`: whether the result came from local cache.
- `stale_fallback`: whether cached data was used after a network error.
- `parse_result`: parse diagnostics for freshly downloaded TSV data.

### `filter_datasets()`

Takes a clean summary DataFrame and returns:

- filtered DataFrame
- summary dict with counts and active filters

The arguments mirror the CLI flags, including `match_all` and `deep`.

### `lookup_datasets()`

Takes an iterable of `PXD` or `RPXD` identifiers and returns a `LookupResult` dataclass with:

- `df`: parsed XML metadata rows for successful lookups.
- `failed_ids`: identifiers that could not be fetched or parsed.

## Notes for workflow code

- The workflow API returns pandas DataFrames directly, and the artifact helpers preserve the CLI file contract when you want to write them.
- The same local cache is used as the CLI path.
- Network failures still raise `requests` exceptions, except when `fetch_datasets(use_stale_on_error=True)` can serve cached summary data.
- `lookup_datasets()` validates IDs up front and raises `ValueError` for unsupported identifiers.
- CLI stdout is now machine-friendly when you use `-o -`; status messages go to stderr while artifact content stays on stdout.
