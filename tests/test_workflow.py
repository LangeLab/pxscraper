"""Tests for the small workflow-oriented Python API."""

from unittest.mock import patch

import pandas as pd
import pytest
import requests

from pxseek import (
    FetchResult,
    LookupResult,
    cache,
    fetch_datasets,
    filter_datasets,
    lookup_datasets,
)

RAW_TSV = (
    "Dataset Identifier\tTitle\tRepos\tSpecies\tInstrument\tPublication\t"
    "LabHead\tAnnounce Date\tKeywords\tannouncementXML\n"
    '<a href="http://x.org/cgi/GetDataset?ID=PXD000001" target="_blank">PXD000001</a>\t'
    "Cancer atlas\tPRIDE\tHomo sapiens\tOrbitrap\tno pub\tJ Doe\t2025-01-01\tproteomics,\t\n"
    '<a href="http://x.org/cgi/GetDataset?ID=PXD000002" target="_blank">PXD000002</a>\t'
    "Mouse phospho\tMassIVE\tMus musculus\tQ Exactive\tno pub\tA Smith\t2025-02-01\tphospho,\t\n"
)

DETAIL_XML = """<?xml version="1.0"?>
<ProteomeXchangeDataset id="PXD000001">
  <DatasetSummary title="Cancer atlas" announceDate="2025-01-01" hostingRepository="PRIDE">
    <Description>Ubiquitylation workflow validation dataset.</Description>
  </DatasetSummary>
</ProteomeXchangeDataset>
"""


@pytest.fixture
def summary_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dataset_id": ["PXD000001", "PXD000002"],
            "title": ["Cancer atlas", "Mouse phospho"],
            "repository": ["PRIDE", "MassIVE"],
            "species": ["Homo sapiens", "Mus musculus"],
            "instrument": ["Orbitrap", "Q Exactive"],
            "publication": ["no pub", "no pub"],
            "lab_head": ["J Doe", "A Smith"],
            "announce_date": ["2025-01-01", "2025-02-01"],
            "keywords": ["proteomics", "phospho"],
        }
    )


class TestFetchDatasets:
    def test_fetch_downloads_and_caches_summary(self, tmp_path):
        with patch("pxseek.workflow.api.fetch_summary", return_value=RAW_TSV):
            result = fetch_datasets(cache_dir=tmp_path)

        assert isinstance(result, FetchResult)
        assert result.from_cache is False
        assert result.parse_result is not None
        assert len(result.df) == 2

        cached = cache.load("summary", cache_dir=cache.get_cache_dir(tmp_path))
        assert cached is not None
        assert len(cached) == 2

    def test_fetch_uses_fresh_cache_before_network(self, tmp_path, summary_df):
        resolved_cache_dir = cache.get_cache_dir(tmp_path)
        cache.save(summary_df, "summary", cache_dir=resolved_cache_dir)

        with patch("pxseek.workflow.api.fetch_summary") as mock_fetch:
            result = fetch_datasets(cache_dir=tmp_path)

        assert result.from_cache is True
        mock_fetch.assert_not_called()

    def test_fetch_uses_stale_cache_on_connection_error(self, tmp_path, summary_df):
        resolved_cache_dir = cache.get_cache_dir(tmp_path)
        cache.save(summary_df, "summary", cache_dir=resolved_cache_dir)

        with patch(
            "pxseek.workflow.api.fetch_summary",
            side_effect=requests.ConnectionError("offline"),
        ):
            result = fetch_datasets(refresh=True, cache_dir=tmp_path)

        assert result.from_cache is True
        assert result.stale_fallback is True


class TestFilterDatasets:
    def test_standard_filter_returns_dataframe_and_summary(self, summary_df):
        filtered_df, summary = filter_datasets(summary_df, species="Homo sapiens")

        assert len(filtered_df) == 1
        assert filtered_df.iloc[0]["dataset_id"] == "PXD000001"
        assert summary["filtered_count"] == 1

    def test_deep_filter_uses_description_text(self, summary_df, tmp_path):
        with patch(
            "pxseek.workflow.api.fetch_datasets_xml",
            return_value={"PXD000001": DETAIL_XML, "PXD000002": None},
        ):
            filtered_df, summary = filter_datasets(
                summary_df,
                keywords="ubiquitylation",
                deep=True,
                cache_dir=tmp_path,
                delay=0,
            )

        assert len(filtered_df) == 1
        assert filtered_df.iloc[0]["dataset_id"] == "PXD000001"
        assert "description" in filtered_df.columns
        assert "deep keywords: title, keywords, description" in summary["active_filters"]


class TestLookupDatasets:
    def test_lookup_returns_rows_and_failed_ids(self, tmp_path):
        with patch(
            "pxseek.workflow.api.fetch_datasets_xml",
            return_value={"PXD000001": DETAIL_XML, "PXD000002": None},
        ):
            result = lookup_datasets(["PXD000001", "PXD000002"], cache_dir=tmp_path, delay=0)

        assert isinstance(result, LookupResult)
        assert len(result.df) == 1
        assert result.df.iloc[0]["dataset_id"] == "PXD000001"
        assert result.failed_ids == ["PXD000002"]

    def test_lookup_rejects_invalid_ids(self):
        with pytest.raises(ValueError):
            lookup_datasets(["MSV000000001"])
