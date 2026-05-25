# pxseek Wiki

This wiki is the user-facing documentation set for `pxseek`.

## Start here

- [Installation](Installation)
- [CLI Quickstart](CLI-Quickstart)
- [Python API](Python-API)
- [Search Recipes](Search-Recipes)
- [Data Formats](Data-Formats)
- [Troubleshooting and FAQ](Troubleshooting)

## Recommended first path

1. Install `pxseek`.
2. Run the three-step workflow: `fetch`, `filter`, then `lookup`.
3. Use Search Recipes when you want a biologically focused starting point.
4. Use Data Formats or Troubleshooting and FAQ when you need more detail.

## Core idea

`pxseek` helps you search ProteomeXchange dataset metadata without a browser workflow. The main pattern is simple:

```bash
pxseek fetch -o px_datasets.tsv
pxseek filter -i px_datasets.tsv -s "Homo sapiens" -o human.tsv
pxseek lookup --input human.tsv -o detailed.tsv
```

Use the summary TSV for discovery. Use `lookup` on the final shortlist when you need richer metadata.
