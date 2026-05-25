<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to pxseek are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

---

## [0.5.1] - 2026-05-25 - [Tagged]

### Added

- Real stdin artifact support for CLI workflows: `filter -i -` and `lookup --input -` can now consume TSV, CSV, or JSON artifacts from stdin, keeping the documented pipeline examples true.
- Regression coverage for stdin artifact reads in shared helpers and end-to-end CLI stdin pipelines.
- Regression coverage for malformed deep-search XML handling, invalid JSON artifact syntax and shape validation, empty batch API fetch behavior, and hostile artifact/cache path handling.

### Changed

- Internal code-quality pass across the core modules to remove duplicated control flow and centralize small helpers in artifact loading, workflow deep-search parsing, cache handling, CLI stale-cache fallback, XML parsing, keyword filtering, and batch API fetch flow.
- Artifact auto-detection is now strict in `auto` mode: `.tsv`, `.csv`, `.json`, or no suffix are accepted, while unknown suffixes require an explicit format instead of silently defaulting to TSV.
- Artifact writes now create missing parent directories automatically for nested output paths.

### Fixed

- Deep filtering in the CLI and workflow API no longer aborts the whole operation when one cached or fetched XML payload is malformed. Bad XML is skipped while valid datasets still flow through.
- JSON artifact loading now fails early and consistently for invalid JSON syntax and invalid JSON shapes, instead of leaking raw parser or pandas errors.
- Hostile artifact and cache path inputs now fail with friendly CLI errors instead of raw `IsADirectoryError` or `NotADirectoryError` exceptions.
- Cache metadata JSON reads and writes now use explicit UTF-8 consistently.
- Empty batch XML fetches now return immediately without creating an HTTP session or progress wrapper.
- Trusted Publishing workflow now builds from a clean `dist/` directory, rejects manual PyPI publishes from non-tag refs, and pins the PyPI publish action to a concrete release commit.

---

## [0.5.0] - 2026-05-25 - [Tagged]

### Added

- GitHub wiki documentation set covering installation, CLI quickstart, data formats, search recipes, and troubleshooting.
- Small workflow-oriented Python API exported at package root: `fetch_datasets()`, `filter_datasets()`, `lookup_datasets()`, plus `FetchResult` and `LookupResult`.
- Shared artifact helpers exported at package root: `read_artifact()`, `render_artifact()`, and `write_artifact()`.
- Project metadata links for homepage, repository, issues, and changelog in package metadata.
- 7 tests for the documented workflow API surface.
- 3 tests for shared artifact helpers and JSON / CSV round-tripping.
- 2 CLI integration tests covering JSON stdout output and JSON artifact input for `lookup`.

### Changed

- CLI `fetch`, `filter`, and `lookup` now share one artifact contract with `tsv`, `csv`, and `json` output support.
- CLI artifact output now supports `-o -` for stdout while status lines move to stderr to stay machine-friendly.
- `filter` and `lookup` can now read JSON artifacts produced by the shared helpers or other `pxseek` commands.
- CI workflow refreshed for Python 3.12-3.14 across Ubuntu, macOS, and Windows with explicit `uv` interpreter selection.
- GitHub Actions updated to Node 24-compatible major versions and the Windows runner pinned to `windows-2025`.
- README simplified to focus on installation, the shortest useful CLI path, and the GitHub wiki as the main documentation surface.
- CLI quickstart, Python API, and data format docs updated to reflect the shared JSON / CSV / TSV artifact story.
- Development and release planning docs updated to match the current repository state.

### Fixed

- Windows parser fixture tests now read UTF-8 data explicitly instead of relying on platform-default encodings.
- Matrix CI jobs no longer fail with `Failed to spawn: pytest` due to `uv run` selecting the wrong interpreter or environment.

---

## [0.4.5] - 2026-05-10

### Added

- `--match-all` / `-a` flag for `pxseek filter`: requires ALL keywords to match (AND logic). Default OR behaviour is preserved. Works with comma-separated keywords and keyword files (#14).
- Stale cache fallback: on `ConnectionError` or `Timeout`, `pxseek fetch` and `pxseek filter` now serve cached data with a warning timestamp instead of aborting. Only raises an error when no cache exists at all (#12).
- XML fetch retry: `fetch_dataset_xml` retries failed requests up to 3 times with exponential backoff (1s, 2s, 4s). Only connection-level errors are retried; HTTP 4xx/5xx fail immediately (#13).

### Changed

- `validate_pxd_id` now accepts RPXD reanalysis IDs alongside PXD. Partner-native IDs (MassIVE `MSV`, jPOST `JPST`, etc.) remain unsupported by the ProteomeCentral API (#11).
- README header redesigned with centered layout and project badges (version, Python, license, tests, changelog, citation).
- Version bumped to 0.4.5.

### Added (tests)

- 1 test for RPXD acceptance in `validate_pxd_id`.
- 5 tests for `by_keywords` with `match_all=True` (AND logic, file support, single keyword equivalence, missing column).
- 3 tests for `match_all` through `apply_filters`.

---

## [0.4.4] - 2026-05-10

### Fixed

- HTML entities (`&amp;`, `&lt;`, `&gt;`, `&nbsp;`, `&#39;`, `&#x27;`, `&apos;`) now decoded in `strip_html` via `html.unescape()` (#5).
- Cache `_metadata.json` corruption now backs up the corrupted file to `.bak` before recovering; metadata writes use atomic `.tmp` + `os.replace` to prevent partial-write corruption (#6).
- Unsafe key access in `is_stale`: missing or empty metadata entries return `True` (stale) instead of crashing with `KeyError` (#7).
- Keyword word boundaries (`\b`) now conditionally applied per side: keywords with leading/trailing non-word characters (`.mzML`, `+H`, `LC-MS`, `T-cell`) match correctly (#8).
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

[0.5.0]: https://github.com/LangeLab/pxseek/releases/tag/v0.5.0
[0.5.1]: https://github.com/LangeLab/pxseek/releases/tag/v0.5.1
