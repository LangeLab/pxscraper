<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to pxseek are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Planned

- Phase 4 (v0.4.4): Bug sweep (#5-#10), CLI output infrastructure, expanded test coverage.

---

## [0.4.3] - 2026-05-09

### Fixed

- Multi-line TSV titles caused by unquoted newlines inside dataset titles are now repaired, recovering previously corrupted rows and eliminating spurious continuation rows with bogus dataset IDs.
- Pandas 3.x compatibility: replaced `on_bad_lines="warn"` with pre-parse column-count validation (the C engine silently ignores `on_bad_lines` in pandas 3).
- Post-parse dataset ID validation drops rows with invalid dataset IDs (e.g. continuation row text used as an ID).
- `raw_tsv.strip().split("\n")` replaced with `splitlines()` to preserve trailing tab characters.
- Empty input returns empty `ParseResult` instead of raising `IndexError`.
- C engine crash on malformed lines with extra tab-separated fields handled by `on_bad_lines="skip"`.

### Added

- Enhanced parse diagnostics: `ParseResult.report()` with per-line skip reasons (column count, expected range, content preview) and dropped-ID tracking.
- `CHANGELOG.md` and `CITATION.cff` for project attribution.
- Citation section in README.

---

## [0.4.2] - 2026-05-02

### Added

- `--deep` flag for `filter`: searches dataset descriptions/abstracts by fetching individual XML records.
- 8 integration tests for deep search workflow.

### Fixed

- Namespace-agnostic XML parsing (handles both prefixed and default xmlns).
- Lookup confirmation threshold respected correctly.

---

## [0.4.0] - 2026-04-20

### Added

- `lookup` command: fetch detailed XML metadata for specific PXD identifiers.
- Batch XML fetcher with progress bar and per-dataset disk cache.
- Polite rate-limiting between XML requests.

---

## [0.3.2] - 2026-04-10

### Added

- Date range validation for `--after`/`--before` flags.
- Warning when `--keyword-columns` references non-existent columns.

### Fixed

- Consistent contact role keys in XML parsing (submitter vs lab_head).

---

## [0.3.1] - 2026-04-05

### Changed

- Code hardening: DRY refactoring, edge case handling, PEP 8 compliance.

---

## [0.3.0] - 2026-03-28

### Added

- `filter` command with composable filters: species, repository, keywords, date range, instrument.
- Auto-fetch: filter automatically downloads data if cache is missing.
- Full CLI integration with all filter options.

---

## [0.2.2] - 2026-03-20

### Fixed

- Various correctness and usability improvements.

### Added

- GitHub Actions CI pipeline.
- Expanded test coverage for edge cases.

---

## [0.2.0] - 2026-03-15

### Added

- Phase 1 implementation: API fetch, TSV parsing, column mapping, caching.
- `fetch` command with staleness check and refresh option.
- HTML tag stripping from TSV fields.
- Cache layer with timestamp-based staleness.
- Initial test suite.

---

## [0.1.0] - 2026-03-10

### Added

- Project scaffold: package structure, `pyproject.toml`, basic CLI skeleton.
