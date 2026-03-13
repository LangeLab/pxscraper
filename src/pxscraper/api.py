"""ProteomeCentral API client."""

SUMMARY_URL = (
    "https://proteomecentral.proteomexchange.org/cgi/GetDataset"
    "?action=summary&outputMode=tsv"
)

DATASET_XML_URL = (
    "https://proteomecentral.proteomexchange.org/cgi/GetDataset"
    "?outputMode=XML&ID={dataset_id}"
)
