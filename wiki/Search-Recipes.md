# Search Recipes

These are biology-focused workflows that start from real research questions.

## Species-first workflow

Use species first when the biological system is the main constraint.

```bash
pxseek fetch -o px_datasets.tsv
pxseek filter -i px_datasets.tsv -s "Homo sapiens" -o human.tsv
```

Then add narrower biology:

```bash
pxseek filter -i px_datasets.tsv -s "Homo sapiens" -k "cancer" -o human-cancer.tsv
```

Or use a regex to grab multiple species at once:

```bash
pxseek filter -i px_datasets.tsv -s "mus|rattus" -o rodent.tsv
```

## Repository-plus-species workflow

Use repository filtering when the archive matters, for example because you want datasets stored in a specific repository.

```bash
pxseek filter -i px_datasets.tsv -s "Homo sapiens" -r PRIDE -o human-pride.tsv
```

You can specify multiple repositories with a comma:

```bash
pxseek filter -i px_datasets.tsv -s "Homo sapiens" -r "PRIDE,MassIVE" -o human-pride-massive.tsv
```

## Instrument-first workflow

Use instrument family when platform comparability is important.

```bash
pxseek filter -i px_datasets.tsv --instrument "Orbitrap|Q Exactive|Exploris" -o orbitrap-family.tsv
```

Then layer species or date:

```bash
pxseek filter -i px_datasets.tsv --instrument "Orbitrap|Q Exactive|Exploris" -s "Mus musculus" --after 2024-01-01 -o mouse-orbitrap-recent.tsv
```

## Keyword file workflow (pediatric cancer)

When you have a long list of keywords, put them in a file and pass the path to `-k`. The repo includes a ready-to-use example:

```bash
pxseek filter -i px_datasets.tsv -k examples/pediatric_cancer_keywords.txt -o pediatric-cancer.tsv
```

The file contains terms like `child`, `pediatric`, `leukemia`, `neuroblastoma`, and many others. Each term is on its own line. The search uses OR logic by default.

You can create your own keyword file the same way. One keyword per line, blank lines are ignored.

## AND logic with match-all

By default, multiple keywords use OR logic (any match is enough). When you need results that mention ALL of your terms, use `--match-all`.

```bash
pxseek filter -i px_datasets.tsv -s "Homo sapiens" -k "cancer,phosphoproteomics" --match-all -o human-cancer-phospho.tsv
```

This returns only human datasets where both "cancer" and "phosphoproteomics" appear somewhere in the title or keywords.

## Date range workflow

Filter datasets announced in a specific time window.

```bash
pxseek filter -i px_datasets.tsv --after 2023-01-01 --before 2023-12-31 -o datasets-2023.tsv
```

Combine date range with species for a biologically relevant window:

```bash
pxseek filter -i px_datasets.tsv -s "Homo sapiens" -k "COVID" --after 2020-01-01 --before 2023-12-31 -o human-covid-2020-2023.tsv
```

## Deep description workflow

Use `--deep` when the term you care about is more likely to appear in the longer dataset description than in the short title or keyword fields.

```bash
pxseek filter -i px_datasets.tsv -s "Homo sapiens" -k "ubiquitylation" --deep --yes -o deep-ubiquitylation.tsv
```

The `--yes` flag skips the confirmation prompt that normally appears when more than 50 datasets need XML fetching. If you omit `--yes`, you will be asked to confirm.

Deep search can be combined with other filters. It first narrows by species, repository, instrument, and date, then fetches XML descriptions for the remaining candidates and re-applies the keyword filter on title, keywords, and description together.

## Pipeline workflow with pipes

You can chain commands with `-o -` and `-i -` to avoid writing intermediate files. Stdin artifacts are detected from content, so the same pattern works for TSV and JSON pipelines.

```bash
pxseek fetch -o - | pxseek filter -i - -s "Homo sapiens" -k "cancer,proteomics" -o - | pxseek lookup --input - -o final-details.tsv
```

This fetches, filters, and looks up in one line. The first `-o -` sends the summary to stdout, the second `-o -` sends the filtered results, and the final `-o` writes the lookup output to a file.

If you write artifacts to disk instead, `pxseek` creates missing parent directories automatically. In `auto` mode, use `.tsv`, `.csv`, `.json`, or no suffix. Other suffixes require an explicit `--format`.

## Shortlist-to-lookup workflow

Once you have a biologically relevant shortlist, use `lookup` to inspect description, identifiers, contacts, and FTP location.

```bash
pxseek lookup --input deep-ubiquitylation.tsv -o deep-ubiquitylation-detailed.tsv
```

You can also pass IDs directly on the command line for ad-hoc lookups:

```bash
pxseek lookup --ids PXD000001,PXD000002,PXD000003 -o details.tsv
```

Or combine a file of IDs with command-line IDs:

```bash
pxseek lookup --ids PXD000001 --ids-file my_ids.txt -o combined.tsv
```

## What to read next

- [CLI Quickstart](CLI-Quickstart) for the full command reference.
- [Data Formats](Data-Formats) for the column layout of each artifact.
