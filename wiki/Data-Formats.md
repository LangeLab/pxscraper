# Data Formats

pxseek works with two table shapes and can serialize either one as TSV, CSV, or JSON.

Format selection rules:

- `.tsv` writes tab-separated text.
- `.csv` writes comma-separated text (with headers).
- `.json` writes a JSON array of row objects.
- `-o -` writes the selected format to stdout. Status lines go to stderr.
- `-i -` and `--input -` read an artifact from stdin.

Format is detected from the file suffix when one exists. In `auto` mode, pxseek accepts `.tsv`, `.csv`, `.json`, or no suffix. Unknown suffixes raise an error instead of silently falling back to TSV. You can override detection with `--format`, and stdin input is detected from the content when no suffix is available.

When writing to disk, pxseek creates missing parent directories automatically.

Both shapes use the same column names across all three formats. Only the serialization changes.

## Summary artifact

Written by `pxseek fetch` and read by `pxseek filter`. This is the fast, broad listing of all ProteomeXchange datasets.

9 columns:

`dataset_id`
:  ProteomeCentral TSV. Example: `PXD036143`

`title`
:  ProteomeCentral TSV. Example: `Comprehensive discovery of the accessible primary amino group...`

`repository`
:  ProteomeCentral TSV. Example: `MassIVE`, `PRIDE`, `jPOST`

`species`
:  ProteomeCentral TSV. Example: `Homo sapiens`

`instrument`
:  ProteomeCentral TSV. Example: `maXis II`, `Orbitrap Exploris 480`

`publication`
:  ProteomeCentral TSV. Example: `10.1016/j.neuropharm.2025.110604`

`lab_head`
:  ProteomeCentral TSV. Example: `Lilla Turiak, Tamas Lango`

`announce_date`
:  ProteomeCentral TSV. Example: `2026-03-13`

`keywords`
:  ProteomeCentral TSV. Example: `biotinylated peptides, cell surface proteins`

Example row as JSON:

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

When `filter --deep` is used, the output gets one extra column:

`description`
:  XML description. Example: `Prenatal exposure to dexamethasone...`

## Lookup artifact

Written by `pxseek lookup`. This contains richer metadata extracted from each dataset's ProteomeXchange XML record.

19 columns:

`dataset_id`
:  Example: `PXD063194`

`title`
:  Example: `Treadmill training and venlafaxine treatment...`

`description`
:  Example: `Prenatal exposure to dexamethasone...`

`announce_date`
:  Example: `2026-03-13`

`repository`
:  Example: `PRIDE`

`species`
:  Example: `Rattus norvegicus (Rat)`. Note: this is the raw value from the XML, which sometimes includes a common name in parentheses. The summary artifact uses the scientific name only.

`instruments`
:  Example: `Orbitrap Exploris 480`

`modifications`
:  Example: `iodoacetamide derivatized residue`

`keywords`
:  Example: `frontal cortex, depression, rat, dexamethasone, anxiety`

`review_level`
:  Example: `Peer-reviewed dataset`

`submitter_name`
:  Example: `Maciej Suski`

`submitter_email`
:  Example: `maciej.suski@uj.edu.pl`

`submitter_affiliation`
:  Example: `Chair of Pharmacology`

`lab_head_name`
:  Example: `Maciej Suski`

`lab_head_email`
:  Example: `maciej.suski@uj.edu.pl`

`lab_head_affiliation`
:  Example: `Department of Pharmacology...`

`pubmed_ids`
:  Example: `40738385`

`dois`
:  Example: `10.1016/j.neuropharm.2025.110604`

`ftp_location`
:  Example: `ftp://ftp.pride.ebi.ac.uk/pride/data/archive/2026/03/PXD063194`

Multiple values within a cell (species, instruments, keywords, PubMed IDs, DOIs) are joined with `;`.

Example row as JSON:

```json
[
  {
    "dataset_id": "PXD063194",
    "title": "Treadmill training and venlafaxine treatment on brain changes induced by prenatal dexamethasone.",
    "description": "Prenatal exposure to dexamethasone (DEX) is known to induce long-term behavioral and molecular impairments...",
    "announce_date": "2026-03-13",
    "repository": "PRIDE",
    "species": "Rattus norvegicus (Rat)",
    "instruments": "Orbitrap Exploris 480",
    "modifications": "iodoacetamide derivatized residue",
    "keywords": "frontal cortex, depression, rat, dexamethasone, anxiety",
    "review_level": "Peer-reviewed dataset",
    "submitter_name": "Maciej Suski",
    "submitter_email": "maciej.suski@uj.edu.pl",
    "submitter_affiliation": "Chair of Pharmacology",
    "lab_head_name": "Maciej Suski",
    "lab_head_email": "maciej.suski@uj.edu.pl",
    "lab_head_affiliation": "Department of Pharmacology Faculty of Medicine Jagiellonian University Medical College Krakow, Poland",
    "pubmed_ids": "40738385",
    "dois": "10.1016/j.neuropharm.2025.110604",
    "ftp_location": "ftp://ftp.pride.ebi.ac.uk/pride/data/archive/2026/03/PXD063194"
  }
]
```

## Python helpers

The same formats are available in Python code through `read_artifact()`, `render_artifact()`, and `write_artifact()`. `read_artifact("-")` reads from stdin, and `write_artifact()` creates missing parent directories for output paths. See the [Python API](Python-API) page for usage.
