"""Local caching of fetched data.

Cache is stored in `.pxseek_cache/` in the current working directory
so users can see and manage it directly. The directory is gitignored.
"""

import json
import os
import time
from pathlib import Path

import pandas as pd

from pxseek.models import CACHE_DIR_NAME, CACHE_META_FILE, DEFAULT_CACHE_MAX_AGE_HOURS

type CacheEntry = dict[str, float | int | str]
type CacheMeta = dict[str, CacheEntry]


def get_cache_dir(base: Path | None = None) -> Path:
    """Return the cache directory path, creating it if needed.

    Parameters
    ----------
    base:
        Optional base directory under which the cache directory is created.
        When omitted, the current working directory is used.

    Returns
    -------
    Path
        Path to the cache directory.

    By default, uses `.pxseek_cache/` in the current working directory.
    """
    base = base or Path.cwd()
    cache_dir = base / CACHE_DIR_NAME
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _meta_path(cache_dir: Path) -> Path:
    """Return the metadata JSON path for a cache directory."""
    return cache_dir / CACHE_META_FILE


def _read_meta(cache_dir: Path) -> CacheMeta:
    """Load cache metadata from disk.

    If the metadata file is corrupt JSON, it is renamed to ``.json.bak`` and an
    empty metadata mapping is returned.
    """
    meta_path = _meta_path(cache_dir)
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text())
        except json.JSONDecodeError:
            backup = meta_path.with_suffix(".json.bak")
            meta_path.rename(backup)
            return {}
    return {}


def _write_meta(cache_dir: Path, meta: CacheMeta) -> None:
    """Write cache metadata atomically to disk."""
    tmp = _meta_path(cache_dir).with_suffix(".json.tmp")
    tmp.write_text(json.dumps(meta, indent=2))
    os.replace(tmp, _meta_path(cache_dir))


def save(df: pd.DataFrame, name: str, cache_dir: Path | None = None) -> Path:
    """Save a DataFrame to cache as TSV and record cache metadata.

    Parameters
    ----------
    df:
        DataFrame to write to disk.
    name:
        Cache key used to build the TSV filename and metadata entry.
    cache_dir:
        Optional cache directory. When omitted, the project cache directory is used.

    Returns
    -------
    Path
        Path to the written TSV file.
    """
    cache_dir = cache_dir or get_cache_dir()
    filepath = cache_dir / f"{name}.tsv"
    df.to_csv(filepath, sep="\t", index=False)

    meta = _read_meta(cache_dir)
    meta[name] = {"timestamp": time.time(), "rows": len(df), "file": str(filepath.name)}
    _write_meta(cache_dir, meta)

    return filepath


def load(name: str, cache_dir: Path | None = None) -> pd.DataFrame | None:
    """Load a cached DataFrame by name.

    Parameters
    ----------
    name:
        Cache key used to resolve the TSV filename.
    cache_dir:
        Optional cache directory. When omitted, the project cache directory is used.

    Returns
    -------
    pd.DataFrame | None
        Cached DataFrame, or ``None`` if no cached TSV exists for ``name``.
    """
    cache_dir = cache_dir or get_cache_dir()
    filepath = cache_dir / f"{name}.tsv"
    if not filepath.exists():
        return None
    return pd.read_csv(filepath, sep="\t", dtype=str)


def is_stale(
    name: str,
    max_age_hours: float = DEFAULT_CACHE_MAX_AGE_HOURS,
    cache_dir: Path | None = None,
) -> bool:
    """Check if a cached dataset is older than max_age_hours.

    Parameters
    ----------
    name:
        Cache key used to look up metadata.
    max_age_hours:
        Maximum allowed cache age in hours.
    cache_dir:
        Optional cache directory. When omitted, the project cache directory is used.

    Returns
    -------
    bool
        ``True`` if the cache entry is missing or older than ``max_age_hours``.

    Returns True if cache is missing or stale.
    """
    cache_dir = cache_dir or get_cache_dir()
    meta = _read_meta(cache_dir)
    entry = meta.get(name)
    if entry is None:
        return True
    ts = entry.get("timestamp")
    if ts is None:
        return True
    age_hours = (time.time() - ts) / 3600
    return age_hours > max_age_hours


def cache_info(name: str, cache_dir: Path | None = None) -> CacheEntry | None:
    """Return metadata about a cached dataset.

    Parameters
    ----------
    name:
        Cache key used to look up metadata.
    cache_dir:
        Optional cache directory. When omitted, the project cache directory is used.

    Returns
    -------
    CacheEntry | None
        Metadata for the cache entry, or ``None`` if the entry does not exist.
    """
    cache_dir = cache_dir or get_cache_dir()
    meta = _read_meta(cache_dir)
    return meta.get(name)


# ---------------------------------------------------------------------------
# Per-dataset XML cache
# ---------------------------------------------------------------------------


def save_xml(dataset_id: str, raw_xml: str, cache_dir: Path | None = None) -> Path:
    """Write the raw XML for *dataset_id* to ``<cache_dir>/<dataset_id>.xml``.

    Parameters
    ----------
    dataset_id:
        ProteomeXchange dataset identifier.
    raw_xml:
        Raw XML document to cache on disk.
    cache_dir:
        Optional cache directory. When omitted, the project cache directory is used.

    Returns
    -------
    Path
        Path to the written XML file.

    Raises
    ------
    ValueError
        If ``dataset_id`` is not a valid ``PXD`` or ``RPXD`` identifier.

    ProteomeXchange XML is immutable once published, so no TTL is tracked.
    """
    from pxseek.models import validate_pxd_id

    dataset_id = validate_pxd_id(dataset_id)
    cache_dir = cache_dir or get_cache_dir()
    filepath = cache_dir / f"{dataset_id}.xml"
    filepath.write_text(raw_xml, encoding="utf-8")
    return filepath


def load_xml(dataset_id: str, cache_dir: Path | None = None) -> str | None:
    """Return cached XML for *dataset_id*.

    Parameters
    ----------
    dataset_id:
        ProteomeXchange dataset identifier.
    cache_dir:
        Optional cache directory. When omitted, the project cache directory is used.

    Returns
    -------
    str | None
        Cached XML text, or ``None`` if no XML file exists for ``dataset_id``.

    Raises
    ------
    ValueError
        If ``dataset_id`` is not a valid ``PXD`` or ``RPXD`` identifier.
    """
    from pxseek.models import validate_pxd_id

    dataset_id = validate_pxd_id(dataset_id)
    cache_dir = cache_dir or get_cache_dir()
    filepath = cache_dir / f"{dataset_id}.xml"
    if not filepath.exists():
        return None
    return filepath.read_text(encoding="utf-8")


def is_xml_cached(dataset_id: str, cache_dir: Path | None = None) -> bool:
    """Return ``True`` if an XML file for *dataset_id* exists on disk.

    Parameters
    ----------
    dataset_id:
        ProteomeXchange dataset identifier.
    cache_dir:
        Optional cache directory. When omitted, the project cache directory is used.

    Returns
    -------
    bool
        ``True`` if the XML file exists on disk.

    Raises
    ------
    ValueError
        If ``dataset_id`` is not a valid ``PXD`` or ``RPXD`` identifier.
    """
    from pxseek.models import validate_pxd_id

    dataset_id = validate_pxd_id(dataset_id)
    cache_dir = cache_dir or get_cache_dir()
    return (cache_dir / f"{dataset_id}.xml").exists()
