"""Column names, constants, and validation helpers.

This module centralizes the normalized summary column names, cache defaults,
HTTP request settings, and dataset ID validation used throughout the project.
"""

import re

from pxseek import __version__

# Raw TSV header → clean column name mapping
RAW_TO_CLEAN_COLUMNS = {
    "Dataset Identifier": "dataset_id",
    "Title": "title",
    "Repos": "repository",
    "Species": "species",
    "Instrument": "instrument",
    "Publication": "publication",
    "LabHead": "lab_head",
    "Announce Date": "announce_date",
    "Keywords": "keywords",
}

# Columns to drop from the raw TSV
DROP_COLUMNS = ["announcementXML"]

SUMMARY_COLUMNS = list(RAW_TO_CLEAN_COLUMNS.values())

# Default cache directory name (created in the current working directory)
CACHE_DIR_NAME = ".pxseek_cache"

# Cache metadata filename
CACHE_META_FILE = "_metadata.json"

# Default cache max age in hours
DEFAULT_CACHE_MAX_AGE_HOURS = 24

# Polite delay between individual XML requests (seconds)
XML_REQUEST_DELAY = 1.0

# Number of IDs above which the 'lookup' command asks for confirmation
LOOKUP_CONFIRM_THRESHOLD = 50

# User-Agent string for API requests
USER_AGENT = f"pxseek/{__version__} (https://github.com/LangeLab/pxseek; academic research tool)"

# HTTP timeout in seconds
HTTP_TIMEOUT = 60

# PXD / RPXD dataset ID pattern (e.g. PXD000001, RPXD055697)
PXD_ID_RE = re.compile(r"^(?:R)?PXD\d{6,}$")


def validate_pxd_id(dataset_id: str) -> str:
    """Validate and return a PXD or RPXD dataset ID, or raise ValueError.

    Parameters
    ----------
    dataset_id:
        Candidate ProteomeXchange dataset identifier.

    Returns
    -------
    str
        Normalized dataset identifier with surrounding whitespace removed.

    Raises
    ------
    ValueError
        If ``dataset_id`` is not a valid ``PXD`` or ``RPXD`` identifier.

    The ProteomeCentral API only accepts PXD-prefixed (and reanalysis RPXD)
    identifiers. Partner-repository native IDs (MassIVE ``MSV``, jPOST
    ``JPST``, etc.) are *not* recognised, those datasets must be looked up
    by their PXD-mapped alias, if one exists.
    """
    dataset_id = dataset_id.strip()
    if not PXD_ID_RE.match(dataset_id):
        raise ValueError(
            f"Invalid dataset ID: {dataset_id!r} "
            f"(expected PXD or RPXD followed by 6+ digits; "
            f"partner-native IDs are not supported by the API)"
        )
    return dataset_id
