<!-- markdownlint-disable MD010 -->

# Data Formats

`pxseek` uses two table shapes and can serialize them as `tsv`, `csv`, or `json`.

Format selection rules:

- `.tsv` writes tab-separated text.
- `.csv` writes comma-separated text.
- `.json` writes a JSON array of row objects.
- `-o -` writes the selected artifact format to stdout.

The data shape stays the same across formats. Only the serialization changes.

## Summary artifact

The summary artifact is written by `fetch` and reused by summary-level `filter`.

Columns:

- `dataset_id`
- `title`
- `repository`
- `species`
- `instrument`
- `publication`
- `lab_head`
- `announce_date`
- `keywords`

Example preview:

| dataset_id | title | repository | species | instrument | publication | lab_head | announce_date | keywords |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PXD036143 | Comprehensive discovery of the accessible primary amino group containing segments from cell surface proteins by fine-tuning high-throughput biotinylation method | MassIVE | Homo sapiens | maXis II | no publication | Lilla Turiak, Tamas Lango | 2026-03-13 | biotinylated peptides, cell surface proteins, affinity enrichment, solid phase extraction, HPLC, mass spectrometry, surfaceome |

`filter` expects this cleaned summary shape, not the raw ProteomeCentral export.

Example JSON row:

```json
[
	{
		"dataset_id": "PXD036143",
		"title": "Comprehensive discovery of the accessible primary amino group containing segments from cell surface proteins by fine-tuning high-throughput biotinylation method",
		"repository": "MassIVE",
		"species": "Homo sapiens",
		"instrument": "maXis II",
		"publication": "no publication",
		"lab_head": "Lilla Turiak, Tamas Lango",
		"announce_date": "2026-03-13",
		"keywords": "biotinylated peptides, cell surface proteins, affinity enrichment, solid phase extraction, HPLC, mass spectrometry, surfaceome"
	}
]
```

## Lookup artifact

The lookup artifact is written by `lookup` and contains richer XML-derived metadata.

Key fields:

- `dataset_id`
- `title`
- `description`
- `species`
- `instruments`
- `modifications`
- `keywords`
- `review_level`
- `announce_date`
- `repository`
- `pubmed_ids`
- `dois`
- `ftp_location`

Example preview:

| dataset_id | title | repository | species | review_level | pubmed_ids | dois | ftp_location |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PXD063194 | Treadmill training and venlafaxine treatment on brain changes induced by prenatal dexamethasone. | PRIDE | Rattus norvegicus (Rat) | Peer-reviewed dataset | 40738385 | 10.1016/j.neuropharm.2025.110604 | ftp://ftp.pride.ebi.ac.uk/pride/data/archive/2026/03/PXD063194 |

Example JSON row:

```json
[
	{
		"dataset_id": "PXD063194",
		"title": "Treadmill training and venlafaxine treatment on brain changes induced by prenatal dexamethasone.",
		"repository": "PRIDE",
		"species": "Rattus norvegicus (Rat)",
		"review_level": "Peer-reviewed dataset",
		"pubmed_ids": "40738385",
		"dois": "10.1016/j.neuropharm.2025.110604",
		"ftp_location": "ftp://ftp.pride.ebi.ac.uk/pride/data/archive/2026/03/PXD063194"
	}
]
```

## Python helpers

The Python API exposes the same artifact contract through:

- `read_artifact()`
- `render_artifact()`
- `write_artifact()`

Use these helpers when you want the same JSON, CSV, TSV, and stdout behavior outside the CLI.
