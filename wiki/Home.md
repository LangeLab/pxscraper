# pxseek

Query, filter, and retrieve proteomics dataset metadata from ProteomeXchange. No browser required.

## What it does

ProteomeXchange holds tens of thousands of mass spectrometry proteomics datasets across partner repositories like PRIDE, MassIVE, and jPOST. Each dataset has a summary record (title, species, instrument, keywords) and a detailed XML record (description, contacts, publications, FTP links).

pxseek gives you three commands that mirror how researchers actually search:

1. **fetch** downloads the full summary listing as a clean table.
2. **filter** narrows that table by species, repository, keywords, date range, or instrument.
3. **lookup** pulls the detailed XML metadata for just the datasets you care about.

The whole thing works through the ProteomeCentral API. No Selenium, no ChromeDriver, no browser at all.

## Why not just browse ProteomeXchange?

The ProteomeXchange web interface is good for one-off lookups but falls apart when you need to:

- Search across thousands of datasets at once
- Combine filters like species + keywords + instrument + date range
- Feed results into a pipeline or script
- Get structured data (TSV, CSV, JSON) instead of HTML pages

pxseek fixes all of that.

## One rule to remember

`filter` expects the clean summary artifact that `pxseek fetch` produces, not the raw ProteomeCentral TSV export. Follow that rule and things just work.

## Next steps

- [Installation](Installation) to get pxseek running.
- [CLI Quickstart](CLI-Quickstart) for the shortest useful workflow.
- [Search Recipes](Search-Recipes) for biology-focused examples.
