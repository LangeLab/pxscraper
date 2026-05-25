"""Workflow-oriented Python API for pxseek.

This module exposes a small set of stable helpers that mirror the CLI stages:
fetch a clean summary table, filter it, and look up detailed XML metadata.
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

from pxseek import api, cache, models, parse
from pxseek import filter as filt


@dataclass
class FetchResult:
    """Result of fetching the ProteomeXchange summary table.

    Attributes
    ----------
    df:
        Clean summary DataFrame.
    from_cache:
        ``True`` when the returned data came from the local cache.
    stale_fallback:
        ``True`` when cached data was returned after a network failure.
    parse_result:
        Parse diagnostics for freshly downloaded TSV data. ``None`` when the
        result was served directly from cache.
    """

    df: pd.DataFrame
    from_cache: bool
    stale_fallback: bool = False
    parse_result: parse.ParseResult | None = None


@dataclass
class LookupResult:
    """Result of looking up detailed dataset XML metadata.

    Attributes
    ----------
    df:
        Parsed metadata rows for successfully fetched datasets.
    failed_ids:
        Dataset IDs that could not be fetched or parsed.
    """

    df: pd.DataFrame
    failed_ids: list[str] = field(default_factory=list)


def _resolve_cache_dir(cache_dir: Path | str | None) -> Path:
    """Return the effective cache directory for workflow helpers."""
    if cache_dir is None:
        return cache.get_cache_dir()
    return cache.get_cache_dir(Path(cache_dir))


def _extract_description(raw_xml: str) -> str | None:
    """Return the dataset description from raw XML, or ``None`` if parsing fails."""
    try:
        return parse.parse_dataset_xml(raw_xml).get("description", "")
    except Exception:
        return None


def _validate_filters(
    *,
    species: str | None = None,
    instrument: str | None = None,
    after: str | None = None,
    before: str | None = None,
    deep: bool = False,
    keywords: str | None = None,
) -> None:
    """Validate workflow filter arguments using the same rules as the CLI."""
    for name, pattern in (("species", species), ("instrument", instrument)):
        if pattern:
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ValueError(f"Invalid regex for {name!r}: {exc}") from exc

    for name, date_text in (("after", after), ("before", before)):
        if date_text:
            try:
                datetime.strptime(date_text, "%Y-%m-%d")
            except ValueError as exc:
                raise ValueError(
                    f"Invalid date for {name!r}: {date_text!r} (expected YYYY-MM-DD)"
                ) from exc

    if after and before:
        after_dt = datetime.strptime(after, "%Y-%m-%d")
        before_dt = datetime.strptime(before, "%Y-%m-%d")
        if after_dt > before_dt:
            raise ValueError(f"after ({after}) cannot be later than before ({before})")

    if deep and not keywords:
        raise ValueError("deep search requires keywords")


def fetch_datasets(
    *,
    refresh: bool = False,
    cache_dir: Path | str | None = None,
    use_stale_on_error: bool = True,
) -> FetchResult:
    """Fetch the clean summary table used by ``pxseek fetch``.

    Parameters
    ----------
    refresh:
        When ``True``, bypass the summary cache and re-download the TSV.
    cache_dir:
        Optional base directory for the ``.pxseek_cache`` folder.
    use_stale_on_error:
        When ``True``, return cached summary data if the network request fails
        with ``ConnectionError`` or ``Timeout``.

    Returns
    -------
    FetchResult
        Clean summary table plus cache / parse metadata.
    """
    resolved_cache_dir = _resolve_cache_dir(cache_dir)

    if not refresh and not cache.is_stale("summary", cache_dir=resolved_cache_dir):
        cached_df = cache.load("summary", cache_dir=resolved_cache_dir)
        if cached_df is not None:
            return FetchResult(df=cached_df, from_cache=True)

    try:
        raw_tsv = api.fetch_summary()
    except (requests.ConnectionError, requests.Timeout):
        if use_stale_on_error:
            stale_df = cache.load("summary", cache_dir=resolved_cache_dir)
            if stale_df is not None:
                return FetchResult(df=stale_df, from_cache=True, stale_fallback=True)
        raise

    parse_result = parse.parse_summary_tsv(raw_tsv)
    cache.save(parse_result.df, "summary", cache_dir=resolved_cache_dir)
    return FetchResult(
        df=parse_result.df,
        from_cache=False,
        stale_fallback=False,
        parse_result=parse_result,
    )


def filter_datasets(
    df: pd.DataFrame,
    *,
    species: str | None = None,
    repository: str | None = None,
    keywords: str | None = None,
    keyword_columns: str | None = None,
    after: str | None = None,
    before: str | None = None,
    instrument: str | None = None,
    match_all: bool = False,
    deep: bool = False,
    cache_dir: Path | str | None = None,
    delay: float = models.XML_REQUEST_DELAY,
) -> tuple[pd.DataFrame, filt.FilterSummary]:
    """Filter a summary DataFrame using the same semantics as ``pxseek filter``.

    Parameters
    ----------
    df:
        Clean summary DataFrame, typically from :func:`fetch_datasets`.
    species, repository, keywords, keyword_columns, after, before, instrument:
        Filter options matching the CLI command.
    match_all:
        Require all keywords to match instead of any keyword.
    deep:
        Also search dataset descriptions by fetching and parsing XML metadata.
    cache_dir:
        Optional base directory for the ``.pxseek_cache`` folder used by deep search.
    delay:
        Seconds between XML requests during deep search.

    Returns
    -------
    tuple[pd.DataFrame, filt.FilterSummary]
        Filtered DataFrame and the same summary structure returned by
        :func:`pxseek.filter.apply_filters`.
    """
    _validate_filters(
        species=species,
        instrument=instrument,
        after=after,
        before=before,
        deep=deep,
        keywords=keywords,
    )

    if not deep:
        return filt.apply_filters(
            df,
            species=species,
            repository=repository,
            keywords=keywords,
            keyword_columns=keyword_columns,
            after=after,
            before=before,
            instrument=instrument,
            match_all=match_all,
        )

    candidates_df, summary = filt.apply_filters(
        df,
        species=species,
        repository=repository,
        keywords=None,
        after=after,
        before=before,
        instrument=instrument,
    )

    if "dataset_id" not in candidates_df.columns:
        raise ValueError("Input DataFrame must include a 'dataset_id' column for deep search")

    resolved_cache_dir = _resolve_cache_dir(cache_dir)
    candidate_ids = candidates_df["dataset_id"].tolist()
    cached_ids = [
        dataset_id
        for dataset_id in candidate_ids
        if cache.is_xml_cached(dataset_id, cache_dir=resolved_cache_dir)
    ]
    uncached_ids = [
        dataset_id
        for dataset_id in candidate_ids
        if not cache.is_xml_cached(dataset_id, cache_dir=resolved_cache_dir)
    ]

    description_map: dict[str, str] = {}
    for dataset_id in cached_ids:
        raw_xml = cache.load_xml(dataset_id, cache_dir=resolved_cache_dir)
        if raw_xml is not None:
            description = _extract_description(raw_xml)
            if description is not None:
                description_map[dataset_id] = description

    if uncached_ids:
        fetched = api.fetch_datasets_xml(uncached_ids, delay=delay)
        for dataset_id, raw_xml in fetched.items():
            if raw_xml is None:
                continue
            cache.save_xml(dataset_id, raw_xml, cache_dir=resolved_cache_dir)
            description = _extract_description(raw_xml)
            if description is not None:
                description_map[dataset_id] = description

    candidates_df = candidates_df.copy()
    candidates_df["description"] = candidates_df["dataset_id"].map(description_map).fillna("")
    filtered_df = filt.by_keywords(
        candidates_df,
        keywords,
        columns=["title", "keywords", "description"],
        match_all=match_all,
    )
    summary["filtered_count"] = len(filtered_df)
    summary["active_filters"] = list(summary["active_filters"])
    summary["active_filters"].append("deep keywords: title, keywords, description")
    return filtered_df, summary


def lookup_datasets(
    dataset_ids: Iterable[str],
    *,
    cache_dir: Path | str | None = None,
    delay: float = models.XML_REQUEST_DELAY,
) -> LookupResult:
    """Look up detailed XML metadata for dataset IDs.

    Parameters
    ----------
    dataset_ids:
        Iterable of ``PXD`` or ``RPXD`` identifiers.
    cache_dir:
        Optional base directory for the ``.pxseek_cache`` folder.
    delay:
        Seconds between uncached XML requests.

    Returns
    -------
    LookupResult
        Parsed metadata rows and the list of failed IDs.
    """
    unique_ids: list[str] = []
    seen_ids: set[str] = set()
    for raw_dataset_id in dataset_ids:
        dataset_id = models.validate_pxd_id(str(raw_dataset_id))
        if dataset_id not in seen_ids:
            seen_ids.add(dataset_id)
            unique_ids.append(dataset_id)

    resolved_cache_dir = _resolve_cache_dir(cache_dir)
    xml_map: dict[str, str | None] = {}
    cached_ids = [
        dataset_id
        for dataset_id in unique_ids
        if cache.is_xml_cached(dataset_id, cache_dir=resolved_cache_dir)
    ]
    uncached_ids = [
        dataset_id
        for dataset_id in unique_ids
        if not cache.is_xml_cached(dataset_id, cache_dir=resolved_cache_dir)
    ]

    for dataset_id in cached_ids:
        xml_map[dataset_id] = cache.load_xml(dataset_id, cache_dir=resolved_cache_dir)

    if uncached_ids:
        fetched = api.fetch_datasets_xml(uncached_ids, delay=delay)
        for dataset_id, raw_xml in fetched.items():
            xml_map[dataset_id] = raw_xml
            if raw_xml is not None:
                cache.save_xml(dataset_id, raw_xml, cache_dir=resolved_cache_dir)

    rows: list[dict[str, str]] = []
    failed_ids: list[str] = []
    for dataset_id in unique_ids:
        raw_xml = xml_map.get(dataset_id)
        if raw_xml is None:
            failed_ids.append(dataset_id)
            continue
        try:
            rows.append(parse.parse_dataset_xml(raw_xml))
        except Exception:
            failed_ids.append(dataset_id)

    return LookupResult(df=pd.DataFrame(rows), failed_ids=failed_ids)


__all__ = [
    "FetchResult",
    "LookupResult",
    "fetch_datasets",
    "filter_datasets",
    "lookup_datasets",
]
