# Search Recipes

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

## Repository-plus-species workflow

Use repository filtering when archive choice matters.

```bash
pxseek filter -i px_datasets.tsv -s "Homo sapiens" -r PRIDE -o human-pride.tsv
```

## Instrument-first workflow

Use instrument family first when platform comparability matters.

```bash
pxseek filter -i px_datasets.tsv --instrument "Orbitrap|Q Exactive|Exploris" -o orbitrap-family.tsv
```

Then layer species or date:

```bash
pxseek filter -i px_datasets.tsv --instrument "Orbitrap|Q Exactive|Exploris" -s "Mus musculus" --after 2024-01-01 -o mouse-orbitrap-recent.tsv
```

## Deep-description workflow

Use `--deep` when the relevant term is more likely to appear in the longer dataset description than in the summary fields.

```bash
pxseek filter -i px_datasets.tsv -s "Homo sapiens" -k "ubiquitylation" --deep --yes -o deep-ubiquitylation.tsv
```

## Shortlist-to-lookup workflow

Once you have a biologically relevant shortlist, use `lookup` to inspect description, identifiers, contacts, and FTP location.

```bash
pxseek lookup --input deep-ubiquitylation.tsv -o deep-ubiquitylation-detailed.tsv
```
