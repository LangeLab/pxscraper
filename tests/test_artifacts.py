"""Tests for shared artifact IO helpers."""

import io
import json
from unittest.mock import patch

import pandas as pd
import pytest

from pxseek import read_artifact, render_artifact, write_artifact


def test_write_and_read_json_artifact(tmp_path):
    df = pd.DataFrame(
        {
            "dataset_id": ["PXD000001", "PXD000002"],
            "title": ["Cancer atlas", "Mouse phospho"],
        }
    )
    artifact_path = tmp_path / "datasets.json"

    write_artifact(df, artifact_path)
    loaded = read_artifact(artifact_path)

    assert artifact_path.exists()
    assert loaded.to_dict(orient="records")[0]["dataset_id"] == "PXD000001"
    assert list(loaded.columns) == ["dataset_id", "title"]


def test_render_json_artifact_for_stdout():
    df = pd.DataFrame({"dataset_id": ["PXD000001"], "repository": ["PRIDE"]})

    rendered = render_artifact(df, format="json")
    payload = json.loads(rendered)

    assert payload == [{"dataset_id": "PXD000001", "repository": "PRIDE"}]


def test_write_csv_artifact(tmp_path):
    df = pd.DataFrame({"dataset_id": ["PXD000001"], "species": ["Homo sapiens"]})
    artifact_path = tmp_path / "datasets.csv"

    write_artifact(df, artifact_path)
    loaded = read_artifact(artifact_path)

    assert loaded.iloc[0]["dataset_id"] == "PXD000001"


def test_write_artifact_creates_missing_parent_directories(tmp_path):
    df = pd.DataFrame({"dataset_id": ["PXD000001"]})
    artifact_path = tmp_path / "nested" / "results" / "datasets.json"

    write_artifact(df, artifact_path)

    assert artifact_path.exists()


def test_write_artifact_rejects_unknown_suffix(tmp_path):
    df = pd.DataFrame({"dataset_id": ["PXD000001"]})
    artifact_path = tmp_path / "datasets.txt"

    with pytest.raises(ValueError, match="Unknown artifact file suffix"):
        write_artifact(df, artifact_path)


def test_read_artifact_rejects_unknown_suffix(tmp_path):
    artifact_path = tmp_path / "datasets.txt"
    artifact_path.write_text("dataset_id\nPXD000001\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Unknown artifact file suffix"):
        read_artifact(artifact_path)


def test_read_json_artifact_rejects_scalar_list(tmp_path):
    artifact_path = tmp_path / "datasets.json"
    artifact_path.write_text(json.dumps(["PXD000001", "PXD000002"]), encoding="utf-8")

    with pytest.raises(ValueError, match="list of objects"):
        read_artifact(artifact_path)


def test_read_json_artifact_rejects_mixed_list(tmp_path):
    artifact_path = tmp_path / "datasets.json"
    artifact_path.write_text(
        json.dumps([{"dataset_id": "PXD000001"}, "PXD000002"]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="list of objects"):
        read_artifact(artifact_path)


def test_read_json_artifact_rejects_invalid_json_syntax(tmp_path):
    artifact_path = tmp_path / "datasets.json"
    artifact_path.write_text('{"dataset_id": "PXD000001"', encoding="utf-8")

    with pytest.raises(ValueError, match="valid JSON"):
        read_artifact(artifact_path)


def test_read_artifact_rejects_directory_path(tmp_path):
    with pytest.raises(ValueError, match="directory"):
        read_artifact(tmp_path)


def test_read_artifact_reads_json_from_stdin():
    stdin = io.StringIO('[{"dataset_id": "PXD000001", "title": "Foo"}]')

    with patch("sys.stdin", stdin):
        loaded = read_artifact("-", format="json")

    assert loaded.iloc[0]["dataset_id"] == "PXD000001"


def test_read_artifact_reads_tsv_from_stdin():
    stdin = io.StringIO("dataset_id\ttitle\nPXD000001\tFoo\n")

    with patch("sys.stdin", stdin):
        loaded = read_artifact("-")

    assert loaded.iloc[0]["title"] == "Foo"


def test_write_artifact_rejects_directory_path(tmp_path):
    df = pd.DataFrame({"dataset_id": ["PXD000001"]})

    with pytest.raises(ValueError, match="directory"):
        write_artifact(df, tmp_path)
