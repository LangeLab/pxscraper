"""Tests for shared artifact IO helpers."""

import json

import pandas as pd

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
