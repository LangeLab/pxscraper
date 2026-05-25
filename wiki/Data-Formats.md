<!-- markdownlint-disable MD010 -->

# Data Formats

`pxseek` uses two TSV shapes.

## Summary TSV

The summary TSV is written by `fetch` and reused by summary-level `filter`.

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

`filter` expects this cleaned summary TSV shape, not the raw ProteomeCentral export.

The actual file saved by `fetch` or `filter` is still TSV.

## Lookup TSV

The lookup TSV is written by `lookup` and contains richer XML-derived metadata.

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

The actual `lookup` output is also TSV.
