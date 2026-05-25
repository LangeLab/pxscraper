# Troubleshooting

## The most common mistake

`filter` expects the clean summary TSV written by `pxseek fetch`.

```bash
pxseek fetch -o px_datasets.tsv
pxseek filter -i px_datasets.tsv -s "Homo sapiens" -o human.tsv
```

Do not pass the raw ProteomeCentral export directly to `filter`.

## Quick checks

- If `filter` says no filters were specified, add at least one of species, repository, keyword, date, or instrument.
- If `--deep` fails, make sure you supplied `-k` or `--keywords`.
- If `lookup` fails on an identifier, confirm that it is a `PXD...` or `RPXD...` accession.
- If nothing matches, remove filters and add them back one at a time.

## Cache behavior

- Summary data is cached for 24 hours.
- `fetch --refresh` forces a fresh summary download.
- `lookup` caches XML by dataset ID on disk.

## Best debug sequence

1. Run `pxseek fetch -o px_datasets.tsv`.
2. Test one simple filter.
3. Inspect the TSV header and a few rows.
4. Add more filters gradually.
5. Use `lookup` or `--deep` only after the summary stage looks right.
