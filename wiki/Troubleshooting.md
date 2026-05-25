# Troubleshooting and FAQ

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

## FAQ

### What is `pxseek` best at?

`pxseek` is best for metadata discovery and shortlist-building across ProteomeXchange datasets.

### Does it download spectra or raw files?

No. It helps you find relevant datasets and capture metadata such as descriptions, identifiers, and FTP locations.

### Why is `fetch` separate from `lookup`?

Because they serve different stages. `fetch` gives you a fast broad summary table. `lookup` gives you richer per-dataset detail only for the shortlist you care about.

### When should I use `--deep`?

Use `--deep` when the key biological term is likely to appear in the longer description rather than in the summary title or keyword fields.

### Can I start without knowing any PXD IDs?

Yes. That is the normal workflow. Start with species, repository, date, instrument, or keywords, then use `lookup` on the filtered shortlist.
