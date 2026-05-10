"""TSV and XML parsing utilities."""

import html
import io
import re
from dataclasses import dataclass, field

import pandas as pd
from lxml import etree

from pxseek.models import DROP_COLUMNS, RAW_TO_CLEAN_COLUMNS, SUMMARY_COLUMNS

# Maximum preview length for a skipped-line snippet
_PREVIEW_WIDTH = 80

# Regex to strip HTML tags but keep inner text
_HTML_TAG_RE = re.compile(r"<[^>]+>")

# Pattern to detect the start of a data row in the ProteomeCentral summary TSV.
# Data rows begin with <a href=...>PXD...</a> or bare PXD###### / RPXD######.
_DATA_ROW_START_RE = re.compile(r"^\s*(?:<a\s+href=|(?:R)?PXD\d{6,})")

# Valid PXD / RPXD dataset ID pattern (RPXD is used for reanalysis datasets)
_PXD_ID_RE = re.compile(r"^(?:R)?PXD\d{6,}$")


def _preview_line(line: str, width: int = _PREVIEW_WIDTH) -> str:
    """First *width* chars of *line*, squashing internal whitespace."""
    compact = re.sub(r"\s+", " ", line).strip()
    if len(compact) <= width:
        return compact
    return compact[: width - 3] + "..."


@dataclass
class SkippedLine:
    """Details about a single malformed row that was skipped."""

    line_number: int
    reason: str
    cols_found: int
    expected_range: str
    preview: str


@dataclass
class ParseResult:
    """Result of parsing summary TSV, including diagnostics."""

    df: pd.DataFrame
    total_raw_lines: int = 0
    skipped_lines: list[int] = field(default_factory=list)
    skipped_details: list[SkippedLine] = field(default_factory=list)
    dropped_ids: list[str] = field(default_factory=list)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped_lines)

    def report(self) -> str:
        lines: list[str] = []
        lines.append(f"parsed {len(self.df)} dataset(s) from {self.total_raw_lines} raw row(s)")

        if self.skipped_details:
            lines.append(f"  {len(self.skipped_details)} malformed row(s) skipped:")
            for s in self.skipped_details:
                lines.append(
                    f"    line {s.line_number}: {s.reason}"
                    f" ({s.cols_found} cols, expected {s.expected_range})"
                    f"  preview: {s.preview}"
                )

        if self.dropped_ids:
            lines.append(f"  {len(self.dropped_ids)} row(s) dropped after parse"
                         " (invalid dataset ID):")
            n_show = min(len(self.dropped_ids), 5)
            for bogus in self.dropped_ids[:n_show]:
                lines.append(f"    id={bogus!r}")
            rest = len(self.dropped_ids) - n_show
            if rest > 0:
                lines.append(f"    ... and {rest} more")

        return "\n".join(lines)


def strip_html(text: str) -> str:
    """Remove HTML tags from a string, keeping the inner text, and decode HTML entities."""
    if not isinstance(text, str):
        return text
    return html.unescape(_HTML_TAG_RE.sub("", text).strip())


def _repair_multiline_tsv(raw_tsv: str) -> str:
    """Merge continuation lines caused by newlines within unquoted TSV fields.

    The ProteomeCentral summary TSV can contain literal newlines inside fields
    (e.g. multi-line titles) without quoting.  This function detects lines that
    are *not* the start of a new data row and appends them to the preceding
    line, separated by a space.
    """
    lines = raw_tsv.splitlines()
    if not lines:
        return raw_tsv

    repaired = [lines[0]]  # header row
    for line in lines[1:]:
        stripped = line.lstrip()
        if not stripped:
            continue
        if _DATA_ROW_START_RE.match(stripped):
            repaired.append(line)
        else:
            repaired[-1] = repaired[-1].rstrip() + " " + line.lstrip()
    return "\n".join(repaired)


def parse_summary_tsv(raw_tsv: str) -> ParseResult:
    """Parse the raw ProteomeCentral summary TSV into a clean DataFrame.

    Returns a ParseResult containing diagnostics including which rows
    were skipped and why.
    """
    # Pre-process: repair multi-line fields caused by newlines inside titles
    raw_tsv = _repair_multiline_tsv(raw_tsv)

    # Count data lines (header is removed from the total).
    # Use splitlines() to avoid stripping trailing tabs (unlike str.strip()).
    raw_lines_input = raw_tsv.splitlines()
    if not raw_lines_input:
        return ParseResult(df=pd.DataFrame(), total_raw_lines=0)

    # Keep originals (pre-repair) for previews
    original_lines = raw_tsv.splitlines()
    while original_lines and original_lines[-1] == "":
        original_lines.pop()

    # Remove any trailing empty lines
    while raw_lines_input and raw_lines_input[-1] == "":
        raw_lines_input.pop()
    total_raw_lines = max(0, len(raw_lines_input) - 1)

    # Expected number of meaningful data columns.  Data rows have 9 fields
    # but may have up to 2 extra trailing tab fields.  Reject rows that are
    # clearly malformed (too few fields = continuation rows; too many =
    # tabs inside values, which crash the C engine).
    min_cols = len(SUMMARY_COLUMNS)  # 9
    max_cols = min_cols + 3  # allow up to 12 fields (9 data + 3 trailing)
    skipped_lines: list[int] = []
    skipped_details: list[SkippedLine] = []
    clean_lines = [raw_lines_input[0]]
    for i, line in enumerate(raw_lines_input[1:], start=2):
        ncols = len(line.split("\t"))
        if min_cols <= ncols <= max_cols:
            clean_lines.append(line)
        else:
            skipped_lines.append(i)
            if ncols < min_cols:
                reason = "too few columns"
            else:
                reason = "too many columns"
            orig = original_lines[i - 1] if i - 1 < len(original_lines) else line
            skipped_details.append(
                SkippedLine(
                    line_number=i,
                    reason=reason,
                    cols_found=ncols,
                    expected_range=f"{min_cols}-{max_cols}",
                    preview=_preview_line(orig),
                )
            )

    clean_tsv = "\n".join(clean_lines)

    try:
        df = pd.read_csv(
            io.StringIO(clean_tsv), sep="\t", dtype=str, on_bad_lines="skip"
        )
    except pd.errors.EmptyDataError:
        return ParseResult(df=pd.DataFrame(), total_raw_lines=0)

    # Strip trailing whitespace from column names (API has trailing tab)
    df.columns = df.columns.str.strip()

    # Drop unwanted columns
    for col in DROP_COLUMNS:
        if col in df.columns:
            df = df.drop(columns=[col])

    # Strip HTML from all cells
    for col in df.columns:
        df[col] = df[col].apply(strip_html)

    # Rename columns
    df = df.rename(columns=RAW_TO_CLEAN_COLUMNS)

    # Drop any unnamed/empty columns (trailing tabs in TSV create these)
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    df = df.loc[:, df.columns.str.strip() != ""]

    # Strip trailing whitespace from string values
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].str.strip()

    # Drop fully empty rows
    df = df.dropna(how="all").reset_index(drop=True)

    # Validate dataset IDs: drop rows whose ID doesn't match PXD######...
    # (These are continuation rows that became independent rows after the
    # multi-line repair, or other forms of data corruption.)
    dropped_ids: list[str] = []
    if "dataset_id" in df.columns:
        valid_mask = df["dataset_id"].str.match(_PXD_ID_RE, na=False)
        bad = df.loc[~valid_mask, "dataset_id"].dropna().tolist()
        dropped_ids.extend(bad)
        df = df[valid_mask].reset_index(drop=True)

    return ParseResult(
        df=df,
        total_raw_lines=total_raw_lines,
        skipped_lines=skipped_lines,
        skipped_details=skipped_details,
        dropped_ids=dropped_ids,
    )


def parse_dataset_xml(raw_xml: str) -> dict:
    """Parse a single ProteomeXchange dataset XML into a flat dict.

    Extracts: dataset_id, title, description, species, instruments,
    modifications, contacts, FTP links, PubMed IDs, keywords, review level.
    """
    root = etree.fromstring(raw_xml.encode("utf-8"))

    # Strip namespace prefixes so all XPath/find() calls work without a
    # namespace map, regardless of whether the XML declares a default xmlns.
    for elem in root.iter():
        if isinstance(elem.tag, str):
            elem.tag = elem.tag.rpartition("}")[2]

    result = {}

    # Dataset ID
    result["dataset_id"] = root.get("id", "")

    # Title and description from DatasetSummary
    ds = root.find("DatasetSummary")
    result["title"] = ds.get("title", "") if ds is not None else ""
    result["announce_date"] = ds.get("announceDate", "") if ds is not None else ""
    result["repository"] = ds.get("hostingRepository", "") if ds is not None else ""

    desc = ds.find("Description") if ds is not None else None
    result["description"] = desc.text.strip() if desc is not None and desc.text else ""

    # Review level
    review_el = root.xpath(".//ReviewLevel/cvParam/@name")
    result["review_level"] = review_el[0] if review_el else ""

    # Species (may be multiple)
    species = root.xpath('.//SpeciesList/Species/cvParam[@name="taxonomy: scientific name"]/@value')
    result["species"] = "; ".join(species)

    # Instruments (may be multiple)
    instruments = root.xpath(".//InstrumentList/Instrument/cvParam/@name")
    result["instruments"] = "; ".join(instruments)

    # Modifications
    mods = root.xpath(".//ModificationList/cvParam/@name")
    result["modifications"] = "; ".join(mods)

    # Keywords
    kw = root.xpath('.//KeywordList/cvParam[@name="submitter keyword"]/@value')
    result["keywords"] = "; ".join(kw)

    # Pre-seed contact fields so the dict always has consistent keys
    for key in (
        "submitter_name", "submitter_email", "submitter_affiliation",
        "lab_head_name", "lab_head_email", "lab_head_affiliation",
    ):
        result[key] = ""

    # Contacts
    for contact in root.xpath(".//ContactList/Contact"):
        contact_id = contact.get("id", "")
        name = contact.xpath('cvParam[@name="contact name"]/@value')
        email = contact.xpath('cvParam[@name="contact email"]/@value')
        affil = contact.xpath('cvParam[@name="contact affiliation"]/@value')

        prefix = "submitter" if contact_id == "project_submitter" else "lab_head"
        result[f"{prefix}_name"] = name[0] if name else ""
        result[f"{prefix}_email"] = email[0] if email else ""
        result[f"{prefix}_affiliation"] = affil[0] if affil else ""

    # Publications
    pmids = root.xpath('.//PublicationList/Publication/cvParam[@name="PubMed identifier"]/@value')
    result["pubmed_ids"] = "; ".join(pmids)

    dois = root.xpath(
        './/PublicationList/Publication/cvParam[@name="Digital Object Identifier (DOI)"]/@value'
    )
    result["dois"] = "; ".join(dois)

    # FTP location
    ftp = root.xpath(
        './/FullDatasetLinkList/FullDatasetLink/cvParam[@name="Dataset FTP location"]/@value'
    )
    result["ftp_location"] = ftp[0] if ftp else ""

    return result
