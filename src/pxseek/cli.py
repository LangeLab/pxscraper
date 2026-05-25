"""CLI entry point for pxseek.

Defines the ``fetch``, ``filter``, and ``lookup`` commands and keeps command-line
interaction separate from the underlying library logic.
"""

import re
from datetime import datetime
from pathlib import Path

import click
import pandas as pd
import requests

from pxseek import __version__, api, cache, models, parse
from pxseek import filter as filt
from pxseek.artifacts import read_artifact, render_artifact, write_artifact

OUTPUT_FORMATS = click.Choice(["auto", "tsv", "csv", "json"], case_sensitive=False)


def _echo_status(message: str, output: str) -> None:
    """Write non-data CLI messages away from stdout when piping artifacts."""
    click.echo(message, err=(output == "-"))


def _write_output(df: pd.DataFrame, output: str, output_format: str) -> str:
    """Write a DataFrame to disk or stdout using the shared artifact helpers."""
    if output == "-":
        click.echo(render_artifact(df, format=output_format), nl=False)
        return "stdout"

    write_artifact(df, output, format=output_format)
    return output


def _stale_fallback_text(stale_df: pd.DataFrame, cache_dir: Path | None) -> str:
    """Return stale cached data as TSV text with a warning to stderr."""

    info = cache.cache_info("summary", cache_dir=cache_dir)
    ts = ""
    if info and "timestamp" in info:
        ts = datetime.fromtimestamp(info["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
    warning_text = "Warning: Could not reach ProteomeCentral, using cached data"
    click.echo(
        warning_text + (f" from {ts}" if ts else ""),
        err=True,
    )
    return stale_df.to_csv(sep="\t", index=False)


def _fetch_summary_safe(verbose: bool = False, cache_dir: Path | None = None) -> str:
    """Fetch summary TSV from ProteomeCentral with friendly error handling.

    On network failure, falls back to stale cache if available.
    Returns raw TSV text (string).
    """
    try:
        if verbose:
            click.echo("Downloading dataset listing from ProteomeCentral...")
        return api.fetch_summary()
    except requests.ConnectionError:
        stale = cache.load("summary", cache_dir=cache_dir)
        if stale is not None:
            return _stale_fallback_text(stale, cache_dir)
        raise click.ClickException(
            "Could not reach ProteomeCentral. Check your network connection."
        )
    except requests.Timeout:
        stale = cache.load("summary", cache_dir=cache_dir)
        if stale is not None:
            return _stale_fallback_text(stale, cache_dir)
        raise click.ClickException("Request to ProteomeCentral timed out. Try again later.")
    except requests.HTTPError as exc:
        raise click.ClickException(f"ProteomeCentral returned an error: {exc}")


@click.group()
@click.version_option(version=__version__, prog_name="pxseek")
def main():
    """Query, filter, and retrieve proteomics dataset metadata from ProteomeXchange."""


@main.command()
@click.option("-o", "--output", default="px_datasets.tsv", help="Output path. Use '-' for stdout.")
@click.option(
    "--format",
    "output_format",
    default="auto",
    show_default=True,
    type=OUTPUT_FORMATS,
    help="Output format. Auto-detects from --output suffix.",
)
@click.option(
    "--cache-dir",
    default=None,
    type=click.Path(),
    help="Cache directory [default: .pxseek_cache/ in cwd].",
)
@click.option("--refresh", is_flag=True, help="Force re-download even if cached.")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output.")
def fetch(output, output_format, cache_dir, refresh, verbose):
    """Download the full ProteomeXchange dataset listing."""
    cache_base = Path(cache_dir) if cache_dir else None
    cdir = cache.get_cache_dir(cache_base)

    # Check cache
    if not refresh and not cache.is_stale("summary", cache_dir=cdir):
        df = cache.load("summary", cache_dir=cdir)
        info = cache.cache_info("summary", cache_dir=cdir)
        if df is not None:
            _echo_status(
                f"Using cached data ({info['rows']} datasets, from cache in {cdir})",
                output,
            )
            destination = _write_output(df, output, output_format)
            _echo_status(f"Wrote {len(df)} datasets to {destination}", output)
            return

    # Fetch from API
    raw_tsv = _fetch_summary_safe(verbose, cache_dir=cdir)

    if verbose:
        click.echo("Parsing TSV...")
    result = parse.parse_summary_tsv(raw_tsv)
    df = result.df

    # Report parse diagnostics
    if result.skipped_count > 0 or result.dropped_ids:
        _echo_status(result.report(), output)
    else:
        if verbose:
            _echo_status(f"Parsed {len(df)} datasets (no issues)", output)

    # Save to cache
    cache.save(df, "summary", cache_dir=cdir)
    if verbose:
        _echo_status(f"Cached {len(df)} datasets in {cdir}", output)

    # Write output
    destination = _write_output(df, output, output_format)
    _echo_status(f"Fetched {len(df)} datasets -> {destination}", output)


@main.command()
@click.option("-i", "--input", "input_file", default=None, help="Input artifact from fetch.")
@click.option(
    "-o",
    "--output",
    default="filtered_datasets.tsv",
    help="Output path. Use '-' for stdout.",
)
@click.option(
    "--format",
    "output_format",
    default="auto",
    show_default=True,
    type=OUTPUT_FORMATS,
    help="Output format. Auto-detects from --output suffix.",
)
@click.option("-s", "--species", default=None, help="Filter by species (regex).")
@click.option("-r", "--repo", default=None, help="Filter by repository (e.g. PRIDE,MassIVE).")
@click.option(
    "-k", "--keywords", default=None, help="Comma-separated keywords or path to keyword file."
)
@click.option(
    "--after",
    default=None,
    help="Include datasets on or after DATE (YYYY-MM-DD).",
)
@click.option(
    "--before",
    default=None,
    help="Include datasets on or before DATE (YYYY-MM-DD).",
)
@click.option("--instrument", default=None, help="Filter by instrument (regex).")
@click.option(
    "--keyword-columns",
    default=None,
    help="Columns to search for keywords (comma-separated) [default: title,keywords].",
)
@click.option(
    "--cache-dir",
    default=None,
    type=click.Path(),
    help="Cache directory [default: .pxseek_cache/ in cwd].",
)
@click.option("-v", "--verbose", is_flag=True, help="Verbose output.")
@click.option("--deep", is_flag=True, help="Also search within dataset descriptions (fetches XML).")
@click.option("--match-all", "-a", is_flag=True, help="Require ALL keywords to match (AND logic).")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt for --deep.")
@click.option(
    "--delay",
    default=1.0,
    type=float,
    show_default=True,
    help="Seconds between XML requests (--deep only).",
)
def filter(
    input_file,
    output,
    output_format,
    species,
    repo,
    keywords,
    after,
    before,
    instrument,
    keyword_columns,
    cache_dir,
    verbose,
    deep,
    match_all,
    yes,
    delay,
):
    """Filter ProteomeXchange datasets by species, repo, keywords, dates, etc."""
    # --- Validate user-supplied regex patterns ---
    for name, pattern in [("species", species), ("instrument", instrument)]:
        if pattern:
            try:
                re.compile(pattern)
            except re.error as e:
                raise click.ClickException(f"Invalid regex for --{name}: {e}")

    # --- Validate date format ---
    for opt_name, date_str in [("after", after), ("before", before)]:
        if date_str:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                raise click.ClickException(
                    f"Invalid date for --{opt_name}: {date_str!r} (expected YYYY-MM-DD)"
                )
    if after and before:
        if datetime.strptime(after, "%Y-%m-%d") > datetime.strptime(before, "%Y-%m-%d"):
            raise click.ClickException(
                f"--after ({after}) cannot be later than --before ({before})"
            )

    # --- Validate --deep requirement ---
    if deep and not keywords:
        raise click.ClickException("--deep requires --keywords (-k)")

    # --- Load input data ---
    if input_file:
        if verbose:
            _echo_status(f"Reading input from {input_file}", output)
        try:
            df = read_artifact(input_file)
        except Exception as exc:
            raise click.ClickException(f"Could not read input file {input_file!r}: {exc}")
    else:
        # Auto-fetch: use cache or download
        cache_base = Path(cache_dir) if cache_dir else None
        cdir = cache.get_cache_dir(cache_base)

        df = None
        if not cache.is_stale("summary", cache_dir=cdir):
            df = cache.load("summary", cache_dir=cdir)
            if df is not None and verbose:
                info = cache.cache_info("summary", cache_dir=cdir)
                _echo_status(f"Using cached data ({info['rows']} datasets)", output)

        if df is None:
            raw_tsv = _fetch_summary_safe(verbose, cache_dir=cdir)

            result = parse.parse_summary_tsv(raw_tsv)
            df = result.df
            cache.save(df, "summary", cache_dir=cdir)
            if verbose:
                _echo_status(f"Fetched and cached {len(df)} datasets", output)

    # --- Check we have at least one filter ---
    has_filter = any([species, repo, keywords, after, before, instrument])
    if not has_filter:
        raise click.ClickException(
            "No filters specified. Use -s, -r, -k, --after, --before, or --instrument."
        )

    # --- Warn about unknown keyword-columns ---
    if keyword_columns:
        cols = [c.strip() for c in keyword_columns.split(",") if c.strip()]
        for col in cols:
            if col not in df.columns:
                click.echo(f"Warning: column '{col}' not found in data, ignored.", err=True)

    # --- Apply filters ---
    if deep:
        # Phase 1: narrow by metadata filters only (skip keywords at summary level)
        candidates_df, pre_summary = filt.apply_filters(
            df,
            species=species,
            repository=repo,
            keywords=None,
            after=after,
            before=before,
            instrument=instrument,
        )

        # Phase 2: fetch XML descriptions for all candidates
        cdir = cache.get_cache_dir(Path(cache_dir) if cache_dir else None)
        if "dataset_id" not in candidates_df.columns:
            raise click.ClickException(
                "Input data has no 'dataset_id' column. It is required for --deep."
            )

        candidate_ids = candidates_df["dataset_id"].tolist()
        cached_ids = [pid for pid in candidate_ids if cache.is_xml_cached(pid, cache_dir=cdir)]
        to_fetch = [pid for pid in candidate_ids if not cache.is_xml_cached(pid, cache_dir=cdir)]

        if verbose and cached_ids:
            click.echo(f"Using cached XML for {len(cached_ids)} dataset(s).")

        if len(to_fetch) > models.LOOKUP_CONFIRM_THRESHOLD and not yes:
            est_seconds = int(len(to_fetch) * delay)
            click.confirm(
                f"Fetch XML for {len(to_fetch)} dataset(s)? (~{est_seconds}s at {delay}s/request)",
                abort=True,
            )

        desc_map: dict[str, str] = {}
        for pid in cached_ids:
            raw = cache.load_xml(pid, cache_dir=cdir)
            if raw:
                desc_map[pid] = parse.parse_dataset_xml(raw).get("description", "")

        if to_fetch:
            try:
                fetched = api.fetch_datasets_xml(to_fetch, delay=delay)
            except requests.ConnectionError:
                raise click.ClickException(
                    "Could not reach ProteomeCentral. Check your network connection."
                )
            except requests.Timeout:
                raise click.ClickException("Request to ProteomeCentral timed out. Try again later.")
            for pid, raw_xml in fetched.items():
                if raw_xml is not None:
                    cache.save_xml(pid, raw_xml, cache_dir=cdir)
                    desc_map[pid] = parse.parse_dataset_xml(raw_xml).get("description", "")

        # Phase 3: merge description column and re-filter on all text fields
        candidates_df = candidates_df.copy()
        candidates_df["description"] = candidates_df["dataset_id"].map(desc_map).fillna("")
        filtered_df = filt.by_keywords(
            candidates_df,
            keywords,
            columns=["title", "keywords", "description"],
            match_all=match_all,
        )

        # Report
        meta_filters = "; ".join(pre_summary["active_filters"]) or "none"
        click.echo(
            f"Filtered {pre_summary['original_count']} -> {len(filtered_df)} datasets "
            f"({meta_filters}; keywords in title/keywords/description)",
            err=(output == "-"),
        )
    else:
        # Standard summary-level filter
        filtered_df, summary = filt.apply_filters(
            df,
            species=species,
            repository=repo,
            keywords=keywords,
            keyword_columns=keyword_columns,
            after=after,
            before=before,
            instrument=instrument,
            match_all=match_all,
        )

        filters_str = "; ".join(summary["active_filters"])
        click.echo(
            f"Filtered {summary['original_count']} -> {summary['filtered_count']} datasets "
            f"({filters_str})",
            err=(output == "-"),
        )

    if len(filtered_df) == 0:
        _echo_status("No datasets matched the given filters.", output)
        return

    # --- Write output ---
    destination = _write_output(filtered_df, output, output_format)
    _echo_status(f"Wrote {len(filtered_df)} datasets to {destination}", output)


@main.command()
@click.option("--ids", default=None, help="Comma-separated PXD IDs.")
@click.option(
    "--ids-file",
    default=None,
    type=click.Path(exists=True),
    help="File with one PXD ID per line.",
)
@click.option(
    "-i",
    "--input",
    "input_file",
    default=None,
    type=click.Path(exists=True),
    help="Artifact from 'filter' or 'fetch': uses the dataset_id column.",
)
@click.option(
    "-o",
    "--output",
    default="lookup_results.tsv",
    help="Output path. Use '-' for stdout.",
)
@click.option(
    "--format",
    "output_format",
    default="auto",
    show_default=True,
    type=OUTPUT_FORMATS,
    help="Output format. Auto-detects from --output suffix.",
)
@click.option(
    "--delay",
    default=1.0,
    type=float,
    show_default=True,
    help="Seconds to wait between requests.",
)
@click.option(
    "--cache-dir",
    default=None,
    type=click.Path(),
    help="Cache directory [default: .pxseek_cache/ in cwd].",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt.",
)
@click.option("-v", "--verbose", is_flag=True, help="Verbose output.")
def lookup(ids, ids_file, input_file, output, output_format, delay, cache_dir, yes, verbose):
    """Fetch detailed metadata for specific PXD identifiers."""
    # ------------------------------------------------------------------ #
    # 1. Collect IDs from all sources                                      #
    # ------------------------------------------------------------------ #
    raw_ids: list[str] = []

    if ids:
        raw_ids.extend(i.strip() for i in ids.split(",") if i.strip())

    if ids_file:
        path = Path(ids_file)
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                raw_ids.append(line)

    if input_file:
        try:
            tsv_df = read_artifact(input_file)
        except Exception as exc:
            raise click.ClickException(f"Could not read input file {input_file!r}: {exc}")
        if "dataset_id" not in tsv_df.columns:
            raise click.ClickException(f"Input file {input_file!r} has no 'dataset_id' column.")
        raw_ids.extend(str(v).strip() for v in tsv_df["dataset_id"].dropna() if str(v).strip())

    if not raw_ids:
        raise click.ClickException("No PXD IDs provided. Use --ids, --ids-file, or --input.")

    # ------------------------------------------------------------------ #
    # 2. Validate all IDs upfront                                          #
    # ------------------------------------------------------------------ #
    validated: list[str] = []
    bad: list[str] = []
    for raw in raw_ids:
        try:
            validated.append(models.validate_pxd_id(raw))
        except ValueError:
            bad.append(raw)

    if bad:
        raise click.ClickException(f"Invalid PXD ID(s): {', '.join(bad)}")

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_ids: list[str] = []
    for pid in validated:
        if pid not in seen:
            seen.add(pid)
            unique_ids.append(pid)

    # ------------------------------------------------------------------ #
    # 3. Cache: skip already-fetched IDs                                   #
    # ------------------------------------------------------------------ #
    cache_base = Path(cache_dir) if cache_dir else None
    cdir = cache.get_cache_dir(cache_base)

    cached_ids = [pid for pid in unique_ids if cache.is_xml_cached(pid, cache_dir=cdir)]
    to_fetch = [pid for pid in unique_ids if not cache.is_xml_cached(pid, cache_dir=cdir)]

    if verbose and cached_ids:
        click.echo(f"Using cached XML for {len(cached_ids)} dataset(s).")

    # ------------------------------------------------------------------ #
    # 4. Confirmation prompt for large fetches                             #
    # ------------------------------------------------------------------ #
    if len(to_fetch) > models.LOOKUP_CONFIRM_THRESHOLD and not yes:
        est_seconds = int(len(to_fetch) * delay)
        click.confirm(
            f"Fetch XML for {len(to_fetch)} dataset(s)? (~{est_seconds}s at {delay}s/request)",
            abort=True,
        )

    # ------------------------------------------------------------------ #
    # 5. Fetch from API (cached items loaded from disk)                    #
    # ------------------------------------------------------------------ #
    xml_map: dict[str, str | None] = {}

    # Load cached XML
    for pid in cached_ids:
        xml_map[pid] = cache.load_xml(pid, cache_dir=cdir)

    # Fetch uncached XML
    if to_fetch:
        try:
            fetched = api.fetch_datasets_xml(to_fetch, delay=delay)
        except requests.ConnectionError:
            raise click.ClickException(
                "Could not reach ProteomeCentral. Check your network connection."
            )
        except requests.Timeout:
            raise click.ClickException("Request to ProteomeCentral timed out. Try again later.")

        for pid, raw_xml in fetched.items():
            xml_map[pid] = raw_xml
            if raw_xml is not None:
                cache.save_xml(pid, raw_xml, cache_dir=cdir)

    # ------------------------------------------------------------------ #
    # 6. Parse XML → rows; report failures                                 #
    # ------------------------------------------------------------------ #
    rows: list[dict] = []
    failed: list[str] = []

    for pid in unique_ids:
        raw_xml = xml_map.get(pid)
        if raw_xml is None:
            failed.append(pid)
            continue
        try:
            rows.append(parse.parse_dataset_xml(raw_xml))
        except Exception as exc:  # noqa: BLE001
            click.echo(f"Warning: could not parse XML for {pid}: {exc}", err=True)
            failed.append(pid)

    if failed:
        msg = f"Warning: {len(failed)} dataset(s) could not be fetched/parsed: "
        if verbose or len(failed) <= 10:
            msg += ", ".join(failed)
        else:
            msg += ", ".join(failed[:10]) + f" and {len(failed) - 10} more"
        click.echo(msg, err=True)

    if not rows:
        raise click.ClickException("No data to write. All lookups failed.")

    # ------------------------------------------------------------------ #
    # 7. Write output                                                       #
    # ------------------------------------------------------------------ #
    result_df = pd.DataFrame(rows)
    destination = _write_output(result_df, output, output_format)
    _echo_status(f"Wrote {len(rows)} dataset(s) to {destination}", output)
    if failed:
        _echo_status(f"({len(failed)} failed. See warnings above)", output)
