<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to pxseek are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Planned

- CLI output infrastructure (`_output.py`), input validation hardening, expanded coverage.

---

## [0.4.4] - 2026-05-10

### Fixed

- HTML entities (`&amp;`, `&lt;`, `&gt;`, `&nbsp;`, `&#39;`, `&#x27;`, `&apos;`) now decoded in `strip_html` via `html.unescape()` (#5).
- Cache `_metadata.json` corruption now backs up the corrupted file to `.bak` before recovering; metadata writes use atomic `.tmp` + `os.replace` to prevent partial-write corruption (#6).
- Unsafe key access in `is_stale` — missing or empty metadata entries return `True` (stale) instead of crashing with `KeyError` (#7).
- Keyword word boundaries (`\b`) now conditionally applied per side — keywords with leading/trailing non-word characters (`.mzML`, `+H`, `LC-MS`, `T-cell`) match correctly (#8).
- Date coercion `NaT` count is now surfaced through `apply_filters()` summary dict for CLI warning (#9).
- Lookup failure list truncated at 10 IDs with "and N more" suffix; full list shown in verbose mode (#10).

### Added

- 8 tests for HTML entity decoding in `strip_html`.
- 2 tests for cache corruption backup and atomic write.
- 2 tests for missing timestamp / empty entry staleness.
- 6 tests for keyword boundary edge cases with non-word characters.
- 5 tests for date coercion `nat_count` tracking.
- 3 tests for lookup failure list truncation.

### Changed

- All source and test files formatted with `ruff format` for consistent style.
- Line-length lint in `parse.py` fixed.

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
