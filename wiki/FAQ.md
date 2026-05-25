# FAQ

## What is `pxseek` best at?

`pxseek` is best for metadata discovery and shortlist-building across ProteomeXchange datasets.

## Does it download spectra or raw files?

No. It helps you find relevant datasets and capture metadata such as descriptions, identifiers, and FTP locations.

## Why is `fetch` separate from `lookup`?

Because they serve different stages. `fetch` gives you a fast broad summary table. `lookup` gives you richer per-dataset detail only for the shortlist you care about.

## When should I use `--deep`?

Use `--deep` when the key biological term is likely to appear in the longer description rather than in the summary title or keyword fields.

## Can I start without knowing any PXD IDs?

Yes. That is the normal workflow. Start with species, repository, date, instrument, or keywords, then use `lookup` on the filtered shortlist.
