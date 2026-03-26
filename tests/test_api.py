"""Tests for pxseek.api module."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from pxseek.api import (
    DATASET_XML_URL,
    SUMMARY_URL,
    _session,
    fetch_dataset_xml,
    fetch_datasets_xml,
    fetch_summary,
)
from pxseek.models import USER_AGENT, validate_pxd_id

# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


class TestSession:
    def test_user_agent_set(self):
        s = _session()
        assert s.headers["User-Agent"] == USER_AGENT

    def test_returns_session_instance(self):
        s = _session()
        assert isinstance(s, requests.Session)


# ---------------------------------------------------------------------------
# fetch_summary
# ---------------------------------------------------------------------------


MOCK_TSV = (
    "Dataset Identifier\tTitle\tRepos\n"
    "PXD000001\tTest\tPRIDE\n"
)


class TestFetchSummary:
    def test_returns_text(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = MOCK_TSV
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        result = fetch_summary(session=mock_session)
        assert result == MOCK_TSV
        mock_session.get.assert_called_once_with(SUMMARY_URL, timeout=60)
        mock_resp.raise_for_status.assert_called_once()

    def test_raises_on_http_error(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_session.get.return_value = mock_resp

        with pytest.raises(requests.HTTPError):
            fetch_summary(session=mock_session)

    def test_creates_own_session_if_none(self):
        with patch("pxseek.api._session") as mock_session_fn:
            mock_session = MagicMock()
            mock_resp = MagicMock()
            mock_resp.text = MOCK_TSV
            mock_resp.raise_for_status = MagicMock()
            mock_session.get.return_value = mock_resp
            mock_session_fn.return_value = mock_session

            result = fetch_summary()
            assert result == MOCK_TSV
            mock_session_fn.assert_called_once()


# ---------------------------------------------------------------------------
# fetch_dataset_xml
# ---------------------------------------------------------------------------


MOCK_XML = '<?xml version="1.0"?><ProteomeXchangeDataset id="PXD000001"/>'


class TestFetchDatasetXml:
    def test_returns_xml(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = MOCK_XML
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        result = fetch_dataset_xml("PXD000001", session=mock_session, delay=0)
        assert result == MOCK_XML
        expected_url = DATASET_XML_URL.format(dataset_id="PXD000001")
        mock_session.get.assert_called_once_with(expected_url, timeout=60)

    def test_applies_delay(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = MOCK_XML
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        with patch("pxseek.api.time.sleep") as mock_sleep:
            fetch_dataset_xml("PXD000001", session=mock_session, delay=0.5)
            mock_sleep.assert_called_once_with(0.5)

    def test_no_delay_when_zero(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = MOCK_XML
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        with patch("pxseek.api.time.sleep") as mock_sleep:
            fetch_dataset_xml("PXD000001", session=mock_session, delay=0)
            mock_sleep.assert_not_called()

    def test_raises_on_http_error(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("404")
        mock_session.get.return_value = mock_resp

        with pytest.raises(requests.HTTPError):
            fetch_dataset_xml("PXD000001", session=mock_session, delay=0)

    def test_rejects_invalid_dataset_id(self):
        with pytest.raises(ValueError, match="Invalid dataset ID"):
            fetch_dataset_xml("INVALID", delay=0)

    def test_rejects_empty_dataset_id(self):
        with pytest.raises(ValueError, match="Invalid dataset ID"):
            fetch_dataset_xml("", delay=0)

    def test_rejects_partial_pxd_id(self):
        with pytest.raises(ValueError, match="Invalid dataset ID"):
            fetch_dataset_xml("PXD12", delay=0)


# ---------------------------------------------------------------------------
# fetch_datasets_xml (batch)
# ---------------------------------------------------------------------------


class TestFetchDatasetsXml:
    """Tests for the batch fetch_datasets_xml function."""

    def _make_session(self, xml_text=MOCK_XML):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = xml_text
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp
        return mock_session

    def test_returns_dict_of_xml(self):
        mock_session = self._make_session()
        with patch("pxseek.api.time.sleep"):
            result = fetch_datasets_xml(["PXD000001"], session=mock_session, delay=0)
        assert result == {"PXD000001": MOCK_XML}

    def test_multiple_ids(self):
        mock_session = self._make_session()
        ids = ["PXD000001", "PXD000002", "PXD000003"]
        with patch("pxseek.api.time.sleep"):
            result = fetch_datasets_xml(ids, session=mock_session, delay=0)
        assert set(result.keys()) == set(ids)
        assert all(v == MOCK_XML for v in result.values())

    def test_empty_list_returns_empty_dict(self):
        result = fetch_datasets_xml([], delay=0)
        assert result == {}

    def test_invalid_id_raises_before_any_request(self):
        mock_session = self._make_session()
        with pytest.raises(ValueError, match="Invalid dataset ID"):
            fetch_datasets_xml(["PXD000001", "BADID"], session=mock_session, delay=0)
        mock_session.get.assert_not_called()

    def test_per_id_http_error_stores_none(self):
        mock_session = MagicMock()
        good_resp = MagicMock()
        good_resp.text = MOCK_XML
        good_resp.raise_for_status = MagicMock()

        bad_resp = MagicMock()
        bad_resp.raise_for_status.side_effect = requests.HTTPError("404")

        mock_session.get.side_effect = [good_resp, bad_resp]

        with patch("pxseek.api.time.sleep"):
            result = fetch_datasets_xml(["PXD000001", "PXD000002"], session=mock_session, delay=0)

        assert result["PXD000001"] == MOCK_XML
        assert result["PXD000002"] is None

    def test_per_id_connection_error_stores_none(self):
        mock_session = MagicMock()
        mock_session.get.side_effect = requests.ConnectionError("network down")

        with patch("pxseek.api.time.sleep"):
            result = fetch_datasets_xml(["PXD000001"], session=mock_session, delay=0)

        assert result["PXD000001"] is None

    def test_all_fail_returns_all_none(self):
        mock_session = MagicMock()
        mock_session.get.side_effect = requests.Timeout("timed out")

        with patch("pxseek.api.time.sleep"):
            result = fetch_datasets_xml(
                ["PXD000001", "PXD000002"], session=mock_session, delay=0
            )

        assert result == {"PXD000001": None, "PXD000002": None}

    def test_keyboard_interrupt_returns_partial(self):
        """KeyboardInterrupt mid-batch returns whatever was already fetched."""
        fetched = []

        def _side_effect(url, timeout):
            if len(fetched) == 0:
                resp = MagicMock()
                resp.text = MOCK_XML
                resp.raise_for_status = MagicMock()
                fetched.append(resp)
                return resp
            raise KeyboardInterrupt

        mock_session = MagicMock()
        mock_session.get.side_effect = _side_effect

        with patch("pxseek.api.time.sleep"):
            result = fetch_datasets_xml(
                ["PXD000001", "PXD000002"], session=mock_session, delay=0
            )

        # Only PXD000001 was successfully fetched before interrupt
        assert result["PXD000001"] == MOCK_XML
        assert "PXD000002" not in result

    def test_delay_is_passed_through(self):
        mock_session = self._make_session()
        with patch("pxseek.api.time.sleep") as mock_sleep:
            fetch_datasets_xml(["PXD000001"], session=mock_session, delay=1.5)
        mock_sleep.assert_called_once_with(1.5)

    def test_creates_own_session_if_none(self):
        with patch("pxseek.api._session") as mock_session_fn:
            mock_session = self._make_session()
            mock_session_fn.return_value = mock_session
            with patch("pxseek.api.time.sleep"):
                result = fetch_datasets_xml(["PXD000001"], delay=0)
            mock_session_fn.assert_called_once()
            assert "PXD000001" in result


# ---------------------------------------------------------------------------
# validate_pxd_id
# ---------------------------------------------------------------------------


class TestValidatePxdId:
    def test_valid_six_digit(self):
        assert validate_pxd_id("PXD000001") == "PXD000001"

    def test_valid_long_id(self):
        assert validate_pxd_id("PXD0632194") == "PXD0632194"

    def test_strips_whitespace(self):
        assert validate_pxd_id("  PXD063194  ") == "PXD063194"

    def test_rejects_lowercase(self):
        with pytest.raises(ValueError):
            validate_pxd_id("pxd000001")

    def test_rejects_no_digits(self):
        with pytest.raises(ValueError):
            validate_pxd_id("PXD")

    def test_rejects_too_few_digits(self):
        with pytest.raises(ValueError):
            validate_pxd_id("PXD123")

    def test_rejects_non_pxd_prefix(self):
        with pytest.raises(ValueError):
            validate_pxd_id("MSV000001")

    def test_rejects_empty(self):
        with pytest.raises(ValueError):
            validate_pxd_id("")

    def test_rejects_path_traversal(self):
        with pytest.raises(ValueError):
            validate_pxd_id("../etc/passwd")
