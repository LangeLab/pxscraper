"""Shared helpers for reading, rendering, and writing workflow artifacts."""

import json
import sys
from pathlib import Path

import pandas as pd

SUPPORTED_ARTIFACT_FORMATS = ("tsv", "csv", "json")
_JSON_ARTIFACT_SHAPE_ERROR = (
    "JSON artifacts must contain valid JSON as an object or a list of objects"
)
_UNKNOWN_SUFFIX_ERROR = "Unknown artifact file suffix"

_SUFFIX_TO_FORMAT = {
    ".tsv": "tsv",
    ".csv": "csv",
    ".json": "json",
}


def _validate_artifact_read_path(path: Path) -> None:
    """Validate that an artifact read path points to a file-like target."""
    if path.exists() and path.is_dir():
        raise ValueError(f"Artifact path is a directory, not a file: {path}")


def _validate_artifact_write_path(path: Path) -> None:
    """Validate that an artifact write path points to a writable file target."""
    if path.exists() and path.is_dir():
        raise ValueError(f"Artifact path is a directory, not a file: {path}")

    parent = path.parent
    if parent.exists() and not parent.is_dir():
        raise ValueError(f"Parent path is not a directory: {parent}")


def _load_json_payload(raw_text: str) -> list[dict]:
    """Return validated JSON artifact records from raw text."""
    if not raw_text.strip():
        return []

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(_JSON_ARTIFACT_SHAPE_ERROR) from exc

    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        raise ValueError(_JSON_ARTIFACT_SHAPE_ERROR)
    if any(not isinstance(item, dict) for item in payload):
        raise ValueError(_JSON_ARTIFACT_SHAPE_ERROR)

    return payload


def _resolve_stdin_format(raw_text: str, format: str | None = None) -> str:
    """Infer stdin artifact format when no file suffix is available."""
    if format and format.lower() != "auto":
        return resolve_artifact_format(format=format)

    stripped = raw_text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        return "json"

    first_line = raw_text.splitlines()[0] if raw_text.splitlines() else ""
    if "\t" in first_line:
        return "tsv"
    if "," in first_line:
        return "csv"
    return "tsv"


def resolve_artifact_format(
    path: str | Path | None = None,
    format: str | None = None,
    *,
    default: str = "tsv",
) -> str:
    """Return the artifact format from an explicit value or file suffix."""
    if format:
        normalized = format.lower()
        if normalized == "auto":
            format = None
        elif normalized in SUPPORTED_ARTIFACT_FORMATS:
            return normalized
        else:
            raise ValueError(f"Unsupported artifact format: {format!r}")

    if path is None or str(path) == "-":
        return default

    suffix = Path(path).suffix.lower()
    if not suffix:
        return default
    if suffix in _SUFFIX_TO_FORMAT:
        return _SUFFIX_TO_FORMAT[suffix]
    raise ValueError(f"{_UNKNOWN_SUFFIX_ERROR}: {suffix}")


def render_artifact(df: pd.DataFrame, *, format: str = "tsv") -> str:
    """Render a DataFrame as TSV, CSV, or JSON text."""
    normalized = resolve_artifact_format(format=format)

    if normalized == "tsv":
        return df.to_csv(sep="\t", index=False)
    if normalized == "csv":
        return df.to_csv(index=False)
    return df.to_json(orient="records", indent=2, force_ascii=False) + "\n"


def write_artifact(
    df: pd.DataFrame,
    path: str | Path,
    *,
    format: str | None = None,
) -> Path:
    """Write a DataFrame artifact to disk."""
    if str(path) == "-":
        raise ValueError("Use render_artifact() for stdout output")

    resolved_path = Path(path)
    _validate_artifact_write_path(resolved_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    text = render_artifact(df, format=resolve_artifact_format(resolved_path, format))
    resolved_path.write_text(text, encoding="utf-8")
    return resolved_path


def read_artifact(path: str | Path, *, format: str | None = None) -> pd.DataFrame:
    """Read a TSV, CSV, or JSON artifact into a DataFrame."""
    if str(path) == "-":
        raw_text = sys.stdin.read()
        normalized = _resolve_stdin_format(raw_text, format)

        if normalized == "tsv":
            return pd.read_csv(pd.io.common.StringIO(raw_text), sep="\t", dtype=str)
        if normalized == "csv":
            return pd.read_csv(pd.io.common.StringIO(raw_text), dtype=str)

        payload = _load_json_payload(raw_text)
        return pd.DataFrame(payload)

    resolved_path = Path(path)
    _validate_artifact_read_path(resolved_path)
    normalized = resolve_artifact_format(resolved_path, format)

    if normalized == "tsv":
        return pd.read_csv(resolved_path, sep="\t", dtype=str)
    if normalized == "csv":
        return pd.read_csv(resolved_path, dtype=str)

    raw_text = resolved_path.read_text(encoding="utf-8")
    payload = _load_json_payload(raw_text)
    return pd.DataFrame(payload)


__all__ = [
    "SUPPORTED_ARTIFACT_FORMATS",
    "read_artifact",
    "render_artifact",
    "resolve_artifact_format",
    "write_artifact",
]
