"""Shared helpers for reading, rendering, and writing workflow artifacts."""

import json
from pathlib import Path

import pandas as pd

SUPPORTED_ARTIFACT_FORMATS = ("tsv", "csv", "json")

_SUFFIX_TO_FORMAT = {
    ".tsv": "tsv",
    ".csv": "csv",
    ".json": "json",
}


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

    return _SUFFIX_TO_FORMAT.get(Path(path).suffix.lower(), default)


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
    text = render_artifact(df, format=resolve_artifact_format(resolved_path, format))
    resolved_path.write_text(text, encoding="utf-8")
    return resolved_path


def read_artifact(path: str | Path, *, format: str | None = None) -> pd.DataFrame:
    """Read a TSV, CSV, or JSON artifact into a DataFrame."""
    resolved_path = Path(path)
    normalized = resolve_artifact_format(resolved_path, format)

    if normalized == "tsv":
        return pd.read_csv(resolved_path, sep="\t", dtype=str)
    if normalized == "csv":
        return pd.read_csv(resolved_path, dtype=str)

    raw_text = resolved_path.read_text(encoding="utf-8")
    payload = json.loads(raw_text) if raw_text.strip() else []
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        raise ValueError("JSON artifacts must contain an object or a list of objects")
    return pd.DataFrame(payload)


__all__ = [
    "SUPPORTED_ARTIFACT_FORMATS",
    "read_artifact",
    "render_artifact",
    "resolve_artifact_format",
    "write_artifact",
]
