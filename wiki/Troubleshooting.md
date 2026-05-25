# Troubleshooting and FAQ

## The most common mistake

`filter` expects the clean summary artifact written by `pxseek fetch`, not the raw ProteomeCentral TSV export.

```bash
# Correct
pxseek fetch -o px_datasets.tsv
pxseek filter -i px_datasets.tsv -s "Homo sapiens" -o human.tsv

# Wrong: do not point filter at a raw download
```

If you downloaded the TSV directly from ProteomeCentral in a browser, it will have HTML tags in the cells and column names that do not match what `filter` expects. Always use `pxseek fetch` to produce the input for `filter`.

## Quick checks

- If `filter` says no filters were specified, add at least one: species, repository, keywords, date, or instrument.
- If `--deep` fails, make sure you also passed `-k` or `--keywords`. Deep search requires keywords.
- If you are piping artifacts, use `-o -` to write to stdout and `-i -` or `--input -` to read from stdin.
- If pxseek says `Unknown artifact file suffix`, use `.tsv`, `.csv`, `.json`, no suffix, or pass `--format` explicitly.
- If `lookup` rejects an identifier, check that it is a `PXD` or `RPXD` followed by at least 6 digits. Native IDs from partner repositories (like `MSV` from MassIVE or `JPST` from jPOST) are not accepted by the ProteomeCentral API.
- If nothing matches your filter, remove filters and add them back one at a time to find the one that is too restrictive.
- If a command seems to hang, it is probably waiting for HTTP responses. The default delay between requests is 1 second. A `lookup` of 100 datasets takes at least 100 seconds plus transfer time.

## Artifact input and output paths

`pxseek` accepts TSV, CSV, and JSON artifacts. In `auto` mode, file-based format detection is strict:

- `.tsv` means TSV.
- `.csv` means CSV.
- `.json` means JSON.
- No suffix falls back to TSV.
- Any other suffix raises an error instead of silently defaulting to TSV.

If you want a custom extension like `results.txt`, pass `--format` explicitly:

```bash
pxseek fetch -o results.txt --format tsv
```

When writing to disk, pxseek creates missing parent directories automatically. This works:

```bash
pxseek fetch -o results/run1/summary.json --format json
```

If the target path itself is a directory, or if a cache base path points to a file instead of a directory, pxseek now fails with a friendly CLI error instead of a raw filesystem exception.

## Stdin pipelines

Artifacts can flow through stdin as well as files. Use `-` as the input or output path:

```bash
pxseek fetch -o - | pxseek filter -i - -s "Homo sapiens" -o - | pxseek lookup --input - -o details.tsv
```

For stdin artifacts, pxseek auto-detects JSON, TSV, and CSV from the content when no suffix exists. If you are debugging a pipeline, check the boundary one stage at a time:

1. Run `pxseek fetch -o -` by itself and inspect the output.
2. Pipe that into `pxseek filter -i - ... -o -` and confirm the filtered artifact looks correct.
3. Only then add `pxseek lookup --input -` to the end of the pipeline.

## Cache behavior

pxseek caches data in `.pxseek_cache/` in the current working directory. This directory is gitignored and safe to delete if you want to clear all cached data.

**Summary cache.** The ProteomeXchange summary listing is cached for 24 hours by default. If you run `pxseek fetch` twice within 24 hours, the second run uses the cache unless you pass `--refresh`.

**XML cache.** Individual dataset XML files are cached permanently. ProteomeXchange metadata is immutable once published, so there is no expiration. Cached XML is reused across `lookup` and `filter --deep` runs.

**Stale cache fallback.** If the network is down and you have cached summary data, `pxseek fetch` and `pxseek filter` serve the cached data with a warning instead of failing. An error is raised only when there is no cache at all.

**Clearing the cache.** Delete the `.pxseek_cache/` directory:

```bash
rm -rf .pxseek_cache/
```

Or use a different cache directory with `--cache-dir` to keep multiple caches for different projects.

## Confirmation prompts

When `lookup` or `filter --deep` needs to fetch XML for more than 50 datasets, pxseek shows a confirmation prompt with the estimated time:

```bash
Fetch XML for 150 dataset(s)? (~150s at 1.0s/request) [y/N]:
```

Answer `n` or press Ctrl-C to abort. Answer `y` to proceed.

Use the `--yes` or `-y` flag to skip the prompt in scripts or when you have already confirmed the size.

## Partial failures in lookup

If some datasets fail to fetch or parse during `lookup`, the successful results are still written to the output file. A warning lists the failed identifiers. When there are more than 10 failures, the list is truncated with "and N more". Use `-v` (verbose) to see the full list.

```bash
# Partial failure warning
Warning: 3 dataset(s) could not be fetched/parsed: PXD999998, PXD999999, PXD000000
```

If all lookups fail, pxseek exits with an error and writes no output file.

## RPXD reanalysis identifiers

pxseek supports both `PXD` and `RPXD` identifiers. RPXD identifiers are used for reanalysis datasets. All commands (`filter`, `lookup`, `--deep`) work the same way with RPXD IDs.

## Rate limiting and politeness

pxseek adds a 1-second delay between individual XML requests to avoid overloading the ProteomeCentral server. You can adjust this with the `--delay` option (set to `0` for tests or private servers, though this is not recommended for normal use).

If a single XML request fails with a connection-level error, pxseek retries up to 3 times with exponential backoff (1 second, 2 seconds, 4 seconds). HTTP errors like 404 or 500 are not retried.

## Best debug sequence

1. Run `pxseek fetch -o px_datasets.tsv` and confirm it produces output.
2. Test one simple filter: `pxseek filter -i px_datasets.tsv -s "Homo sapiens"`.
3. Inspect the output (column names, a few rows of data).
4. Add more filters gradually, one at a time.
5. Use `lookup` or `--deep` only after the summary stage looks right.
6. If deep search is slow, check how many candidates it needs to fetch XML for.

## FAQ

### What is pxseek best at?

Metadata discovery and shortlist-building across ProteomeXchange datasets. It answers questions like "how many human cancer proteomics datasets were published in 2024?" or "what phosphoproteomics datasets exist for mouse brain tissue?"

### Does it download spectra or raw files?

No. pxseek helps you find relevant datasets and capture metadata such as descriptions, identifiers, DOIs, and FTP locations. Downloading the actual data files from the FTP servers is up to you.

### Why is fetch separate from lookup?

They serve different stages of the workflow. `fetch` gives you a fast broad summary table in one HTTP request. `lookup` gives you richer per-dataset detail, but it requires one HTTP request per dataset. You would not want to fetch detailed XML for 50,000 datasets, so you filter first and look up only the shortlist.

### When should I use --deep?

Use `--deep` when the key term is likely to appear in the dataset description rather than in the title or keyword fields. For example, "ubiquitylation" might be described in detail in the abstract but not appear in the short title.

### Can I start without knowing any PXD IDs?

Yes. That is the normal workflow. Start with species, repository, date, instrument, or keywords. After filtering down to a manageable shortlist, use `lookup` to get the detailed metadata.

### How do I get help?

- Run `pxseek --help` or `pxseek <command> --help`.
- Check the other pages in this wiki.
- Open an issue at <https://github.com/LangeLab/pxseek/issues>.
