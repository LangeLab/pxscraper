"""ProteomeCentral API client.

Endpoints used:
    GET summary TSV endpoint                 -> raw TSV text
    GET dataset XML endpoint by PXD / RPXD   -> raw XML text

This module handles HTTP requests, retry policy, politeness delay, and User-Agent
configuration. Parsing of TSV and XML payloads belongs in :mod:`pxseek.parse`.
"""

import logging
import time

import requests

from pxseek.models import HTTP_TIMEOUT, USER_AGENT, XML_REQUEST_DELAY, validate_pxd_id

log = logging.getLogger(__name__)

SUMMARY_URL = (
    "https://proteomecentral.proteomexchange.org/cgi/GetDataset?action=summary&outputMode=tsv"
)

DATASET_XML_URL = (
    "https://proteomecentral.proteomexchange.org/cgi/GetDataset?outputMode=XML&ID={dataset_id}"
)

# Retry settings for XML fetches, exponential backoff (1s, 2s, 4s).
XML_RETRY_BACKOFF: list[int] = [1, 2, 4]


def _session() -> requests.Session:
    """Create a requests Session with a polite User-Agent."""
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def fetch_summary(session: requests.Session | None = None) -> str:
    """Download the full ProteomeXchange dataset summary TSV.

    Parameters
    ----------
    session:
        Optional shared :class:`requests.Session`. When omitted, a new session
        with the project User-Agent is created.

    Returns
    -------
    str
        Raw TSV text returned by the summary endpoint.

    Raises
    ------
    requests.HTTPError
        If the summary endpoint returns a non-success HTTP response.
    """
    s = session or _session()
    resp = s.get(SUMMARY_URL, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.text


def fetch_dataset_xml(
    dataset_id: str,
    session: requests.Session | None = None,
    delay: float = XML_REQUEST_DELAY,
) -> str:
    """Download the XML metadata for a single PXD dataset.

    Parameters
    ----------
    dataset_id:
        ProteomeXchange dataset identifier, e.g. ``"PXD000001"``.
    session:
        Optional shared :class:`requests.Session`. When omitted, a new session
        with the project User-Agent is created.
    delay:
        Seconds to wait before the first request for API politeness.

    Returns
    -------
    str
        Raw XML text returned by ProteomeCentral.

    Raises
    ------
    ValueError
        If ``dataset_id`` is not a valid ``PXD`` or ``RPXD`` identifier.
    requests.HTTPError
        If the server returns a non-success HTTP response.
    requests.ConnectionError
        If all retry attempts fail with a connection-level error.
    requests.Timeout
        If all retry attempts fail with a timeout.

    Retries up to 3 times with exponential backoff (1s, 2s, 4s) on
    connection-level errors (ConnectionError, Timeout). HTTP 4xx/5xx
    responses are *not* retried.

    Includes a polite delay before the first attempt to avoid overloading
    the ProteomeCentral server.
    """
    dataset_id = validate_pxd_id(dataset_id)
    if delay > 0:
        time.sleep(delay)

    s = session or _session()
    url = DATASET_XML_URL.format(dataset_id=dataset_id)
    last_exc: Exception | None = None

    for attempt in range(len(XML_RETRY_BACKOFF) + 1):
        try:
            resp = s.get(url, timeout=HTTP_TIMEOUT)
            resp.raise_for_status()
            return resp.text
        except requests.HTTPError:
            raise  # never retry 4xx/5xx
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_exc = exc
            if attempt < len(XML_RETRY_BACKOFF):
                wait = XML_RETRY_BACKOFF[attempt]
                log.info("Retrying %s in %ss (attempt %d)", dataset_id, wait, attempt + 1)
                time.sleep(wait)

    assert last_exc is not None
    raise last_exc


def fetch_datasets_xml(
    ids: list[str],
    session: requests.Session | None = None,
    delay: float = XML_REQUEST_DELAY,
) -> dict[str, str | None]:
    """Download XML metadata for a list of PXD dataset IDs.

    Parameters
    ----------
    ids:
        Dataset identifiers to fetch. All identifiers are validated before any
        request is started.
    session:
        Optional shared :class:`requests.Session`. When omitted, a new session
        with the project User-Agent is created.
    delay:
        Seconds to wait between individual XML requests.

    Returns
    -------
    dict[str, str | None]
        Mapping of each validated dataset ID to raw XML text, or ``None`` when
        the fetch for that dataset fails.

    Raises
    ------
    ValueError
        If any identifier in ``ids`` is not a valid ``PXD`` or ``RPXD`` value.

    All IDs are validated upfront before any requests are made.
    Raises ``ValueError`` if any ID is invalid.

    For each ID, the XML is fetched with a polite *delay* between requests.
    If a single fetch fails (network error, HTTP error, timeout), the ID is
    mapped to ``None`` and a warning is logged, the rest continue.

    On ``KeyboardInterrupt`` the partial results collected so far are returned
    so callers can still write whatever was already fetched.

    Returns a dict mapping each (validated) ID to the XML string, or ``None``
    on failure.
    """
    from tqdm import tqdm

    # Validate all IDs upfront so caller learns about bad IDs before waiting.
    validated = [validate_pxd_id(i) for i in ids]

    s = session or _session()
    results: dict[str, str | None] = {}

    try:
        for dataset_id in tqdm(validated, desc="Fetching XML", unit="dataset", leave=True):
            try:
                xml = fetch_dataset_xml(dataset_id, session=s, delay=delay)
                results[dataset_id] = xml
            except (ValueError, requests.RequestException) as exc:
                log.warning("Failed to fetch %s: %s", dataset_id, exc)
                results[dataset_id] = None
    except KeyboardInterrupt:
        log.warning("Interrupted after %d / %d datasets.", len(results), len(validated))

    return results
