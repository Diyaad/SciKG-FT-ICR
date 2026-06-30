"""
02b_extract_csv.py — SciKG pipeline stage 2b (extract from MagLab CSV)

Reads data/raw/maglab_icr_publications.csv (806 rows, 48 columns) and writes
one JSONL file per entity type plus one relationships file:

  data/processed/entities/publications.jsonl   (APPEND to existing)
  data/processed/entities/researchers.jsonl    (new)
  data/processed/entities/journals.jsonl       (new)
  data/processed/entities/facilities.jsonl     (new)
  data/processed/entities/instruments.jsonl    (new)
  data/processed/entities/datasets.jsonl       (new)
  data/processed/entities/funders.jsonl        (new)
  data/processed/relationships/csv_relationships.jsonl   (new)

This stage ONLY extracts fields explicitly present in the CSV. Nothing is
inferred. Missing/blank/"N/A"-style fields are written as null. Email columns
and the 0%-coverage / admin columns are excluded entirely (see EXCLUDE list in
the project task spec). All identifiers, labels, and property names follow the
v1.0 schema conventions documented in CLAUDE.md and the project task spec:

  - Property names ....... snake_case        (publication_year)
  - Entity type labels ... PascalCase         (Publication, Researcher)
  - Relationship types ... SCREAMING_SNAKE     (AUTHORED_BY, HAS_DATASET)
  - Identifiers .......... namespace:value     (doi:10.x/y, researcher:foo_a_2019)

Record envelope (chosen to mirror the relationship envelope given in the task
spec — properties nested, the six provenance keys flat at top level — and to
stay consistent with the flat-record style already used by 02_extract.py):

  Entity record:
    {"identifier": "...", "entity_type": "Publication",
     "properties": {...}, <6 provenance keys>}
  Relationship record:
    {"relationship_type": "...", "subject_id": "...", "subject_type": "...",
     "object_id": "...", "object_type": "...", "properties": {...},
     <6 provenance keys>}

Standard library only: csv, json, re, datetime, pathlib, hashlib. No API calls,
no third-party packages.
"""

import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- Paths -----------------------------------------------------------------
CSV_PATH = Path("data/raw/maglab_icr_publications.csv")
ENTITIES_DIR = Path("data/processed/entities")
RELATIONSHIPS_DIR = Path("data/processed/relationships")
PUBLICATIONS_FILE = ENTITIES_DIR / "publications.jsonl"
RELATIONSHIPS_FILE = RELATIONSHIPS_DIR / "csv_relationships.jsonl"
MANIFEST = Path("data/raw/manifest.json")

# Map each entity type label to its output file.
ENTITY_FILES = {
    "Publication": ENTITIES_DIR / "publications.jsonl",
    "Researcher": ENTITIES_DIR / "researchers.jsonl",
    "Journal": ENTITIES_DIR / "journals.jsonl",
    "Facility": ENTITIES_DIR / "facilities.jsonl",
    "Instrument": ENTITIES_DIR / "instruments.jsonl",
    "Dataset": ENTITIES_DIR / "datasets.jsonl",
    "Funder": ENTITIES_DIR / "funders.jsonl",
}

SCHEMA_VERSION = "v1.0"
SOURCE_TYPE = "csv"
CONFIDENCE = "high"

# Tokens that mean "no value" when they appear as a cell's entire content.
NULL_TOKENS = {"", "n/a", "na", "none", "null"}

DOI_RE = re.compile(r"^10\.\d{4,}/.+")

GROUND_TRUTH_DOIS = None  # lazily loaded


def load_ground_truth_dois():
    """Load DOIs of the 8 annotated ground-truth papers."""
    global GROUND_TRUTH_DOIS
    if GROUND_TRUTH_DOIS is not None:
        return GROUND_TRUTH_DOIS
    GROUND_TRUTH_DOIS = set()
    annotations_path = Path("docs/annotations/paper_reviews.md")
    if annotations_path.exists():
        with open(annotations_path, encoding="utf-8") as f:
            content = f.read()
        for match in re.findall(r'10\.\d{4,}/[^\s\)\]]+', content):
            GROUND_TRUTH_DOIS.add(match.lower())
    return GROUND_TRUTH_DOIS


def is_ground_truth(doi):
    """Check if a DOI is in the ground-truth annotated set."""
    if not doi:
        return False
    return doi.lower() in load_ground_truth_dois()


# ---------------------------------------------------------------------------
# Small value helpers
# ---------------------------------------------------------------------------
def now_iso():
    """UTC ISO-8601 with a trailing Z, matching the task-spec examples."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def clean(value):
    """Trim whitespace; map empty/N-A-style placeholders to None.

    Only the entire-cell placeholder tokens are nulled — a legitimate value such
    as "No" (MagLab Significant) is kept.
    """
    if value is None:
        return None
    v = value.strip()
    if v.lower() in NULL_TOKENS:
        return None
    return v


def parse_int(value):
    v = clean(value)
    if v is None:
        return None
    try:
        return int(v)
    except ValueError:
        return None


def parse_float(value):
    v = clean(value)
    if v is None:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def parse_bool(value):
    """Yes -> True, No -> False, blank/other -> None."""
    v = clean(value)
    if v is None:
        return None
    low = v.lower()
    if low == "yes":
        return True
    if low == "no":
        return False
    return None


def slugify(text):
    """Lowercase, collapse any run of non-alphanumerics to a single underscore.

    Used for facility/journal/instrument/researcher identifier components, e.g.
    "ICR Facility" -> "icr_facility", "21T ICR" -> "21t_icr".
    """
    if text is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def split_multi(value, sep):
    """Split a multi-value cell on sep, trim each part, drop empties."""
    v = clean(value)
    if v is None:
        return []
    return [p.strip() for p in v.split(sep) if p.strip()]


# ---------------------------------------------------------------------------
# DOI / URL handling
# ---------------------------------------------------------------------------
def normalize_doi(raw):
    """Lowercase a DOI string and strip a leading doi.org URL prefix.

    Returns (doi, is_valid). A valid DOI matches ^10\\.\\d{4,}/.+. The four CSV
    rows whose DOI column actually holds a publisher landing-page URL come back
    is_valid=False so the caller can store the original string as a url instead.
    """
    v = clean(raw)
    if v is None:
        return None, False
    low = v.lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi.org/"):
        if low.startswith(prefix):
            low = low[len(prefix):]
            break
    if DOI_RE.match(low):
        return low, True
    return None, False


def resolve_doi_and_url(doi_col, url_col):
    """Reconcile the 'Digital Object Identifier' and 'Url' columns.

    Returns (doi, url):
      - doi  : a clean bare DOI when the DOI column holds a valid one, else None
      - url  : the article URL when it adds information beyond the DOI, else None
    Rules (from task spec):
      * Valid DOI column  -> doi set.
      * Invalid DOI column (4 publisher URLs) -> doi None, original kept as a
        url candidate.
      * Url column that is a doi.org link duplicating the DOI -> dropped (null).
        Any other Url-column value is kept. The Url column takes precedence; the
        invalid-DOI string is only used as a fallback when Url is empty.
    """
    doi, valid = normalize_doi(doi_col)
    invalid_doi_str = None
    if not valid:
        invalid_doi_str = clean(doi_col)  # original string, may be a URL or None

    url = None
    raw_url = clean(url_col)
    if raw_url is not None:
        if "doi.org" in raw_url.lower() and doi and doi in raw_url.lower():
            url = None  # redundant with the DOI we already captured
        else:
            url = raw_url

    if url is None and invalid_doi_str is not None:
        url = invalid_doi_str

    return doi, url


def publication_identifier(doi, maglab_id):
    """doi:{lowercase_doi} when a valid DOI exists, else pub:maglab:{id}."""
    if doi:
        return f"doi:{doi}"
    return f"pub:maglab:{maglab_id}"


# ---------------------------------------------------------------------------
# Name parsing
# ---------------------------------------------------------------------------
def parse_name(token):
    """Parse a "Last, First Middle" author token (split on FIRST comma only).

    Returns (family_name, given_name, name_full). given_name is None when no
    comma is present. name_full is the original trimmed token.
    """
    t = (token or "").strip()
    if not t:
        return None, None, None
    if "," in t:
        family, given = t.split(",", 1)
        family = family.strip() or None
        given = given.strip() or None
    else:
        family, given = t.strip() or None, None
    return family, given, t


def name_natural_key(family_name, given_name):
    """Stable within-publication key for matching authors to corr-authors."""
    fam = slugify(family_name)
    initial = given_name.strip()[0].lower() if given_name and given_name.strip() else "x"
    if not initial.isalnum():
        # given_name starting with a non-alphanumeric (rare) -> fall back to x
        initial = "x"
    return fam, initial


# ---------------------------------------------------------------------------
# Dataset URL classification
# ---------------------------------------------------------------------------
def _md5_8(url):
    return hashlib.md5(url.encode("utf-8")).hexdigest()[:8]


def classify_dataset_url(url):
    """Classify a single dataset URL.

    Returns one of:
      ("__SKIP__", reason)                  -> ProteoSAFe task ID with no MSV
      (repository, accession, review_flag)  -> a Dataset to create
    review_flag is True for the "Other" repository (unknown/opaque patterns),
    which is surfaced honestly via a manual_review_needed property.
    """
    u = url.strip()
    low = u.lower()

    # 1. OSF (also catches doi.org/10.17605/OSF.IO/<acc> since it contains osf.io)
    if "osf.io" in low:
        m = re.search(r"osf\.io/(?:10\.17605/osf\.io/)?([A-Za-z0-9]+)", u, re.IGNORECASE)
        acc = m.group(1).upper() if m else _md5_8(u).upper()
        return ("OSF", acc, False)

    # 2. MassIVE — needs a clean MSV accession; ProteoSAFe-only links are skipped
    if "massive.ucsd.edu" in low:
        m = re.search(r"MSV\d+", u, re.IGNORECASE)
        if m:
            return ("MassIVE", m.group(0).upper(), False)
        return ("__SKIP__", "ProteoSAFe task ID, no MSV accession")

    # 3. ProteomeXchange
    if "proteomexchange" in low:
        m = re.search(r"PXD\d+", u, re.IGNORECASE)
        acc = m.group(0).upper() if m else _md5_8(u)
        return ("ProteomeXchange", acc, False)

    # 4. Zenodo
    if "zenodo.org" in low or "10.5281/zenodo" in low:
        m = re.search(r"zenodo[\./](\d+)", u, re.IGNORECASE)
        acc = m.group(1) if m else _md5_8(u)
        return ("Zenodo", acc, False)

    # 5. doi.org OSF DOI (fallback; normally already handled by rule 1)
    if re.search(r"doi\.org/10\.17605/osf\.io/", low):
        m = re.search(r"osf\.io/([A-Za-z0-9]+)", u, re.IGNORECASE)
        acc = m.group(1).upper() if m else _md5_8(u).upper()
        return ("OSF", acc, False)

    # 6. doi.org Zenodo DOI (fallback; normally already handled by rule 4)
    if re.search(r"doi\.org/10\.5281/zenodo", low):
        m = re.search(r"zenodo[\./](\d+)", u, re.IGNORECASE)
        acc = m.group(1) if m else _md5_8(u)
        return ("Zenodo", acc, False)

    # 7. doi.org other DOI -> Other, full DOI as accession, flag for review
    m = re.search(r"doi\.org/(10\..+)$", u, re.IGNORECASE)
    if m:
        return ("Other", m.group(1), True)

    # 8. anything else -> Other, md5 fingerprint, flag for review
    return ("Other", _md5_8(u), True)


def dataset_identifier(repository, accession):
    return f"dataset:{repository.lower()}:{accession.lower()}"


# ---------------------------------------------------------------------------
# Extractor — accumulates records in memory so the per-row logic is unit-testable
# without touching the filesystem. main() flushes the collected records to disk.
# ---------------------------------------------------------------------------
class Extractor:
    def __init__(self, seen_publication_ids=None):
        # Publications already present (from a prior run / 02_extract output).
        self.seen = set(seen_publication_ids or [])
        # Natural-key -> minted researcher identifier (keeps the first-seen year).
        self.researcher_registry = {}
        # entity_type -> list of records to write.
        self.entities = {etype: [] for etype in ENTITY_FILES}
        self.relationships = []
        # entity_type -> set of identifiers written (seeded with pre-existing pubs)
        # for the orphan check.
        self.id_sets = {etype: set() for etype in ENTITY_FILES}
        self.id_sets["Publication"] |= self.seen

        self.proteosafe_skips = []  # (maglab_id, url, reason)
        self.counts = {
            "rows_processed": 0,
            "publications_written": 0,
            "publications_skipped": 0,
            "researchers_written": 0,
            "journals_written": 0,
            "facilities_written": 0,
            "instruments_written": 0,
            "datasets_written": 0,
            "datasets_skipped_proteosafe": 0,
            "datasets_flagged_review": 0,
            "funders_written": 0,
            "relationships_written": 0,
            "rows_skipped_no_id": 0,
        }
        # Set per row so the helpers can stamp provenance.
        self._cur_source_id = None
        self._cur_evidence = None

    # --- record builders ---------------------------------------------------
    def _provenance(self):
        return {
            "source_type": SOURCE_TYPE,
            "confidence": CONFIDENCE,
            "extracted_at": now_iso(),
            "evidence_note": self._cur_evidence,
            "source_id": self._cur_source_id,
            "schema_version": SCHEMA_VERSION,
        }

    def add_entity(self, entity_type, identifier, properties, count_key=None):
        record = {
            "identifier": identifier,
            "entity_type": entity_type,
            "properties": properties,
        }
        record.update(self._provenance())
        self.entities[entity_type].append(record)
        self.id_sets[entity_type].add(identifier)
        if count_key:
            self.counts[count_key] += 1
        return identifier

    def add_relationship(self, rel_type, subject_id, subject_type,
                         object_id, object_type, properties):
        record = {
            "relationship_type": rel_type,
            "subject_id": subject_id,
            "subject_type": subject_type,
            "object_id": object_id,
            "object_type": object_type,
            "properties": properties,
        }
        record.update(self._provenance())
        self.relationships.append(record)
        self.counts["relationships_written"] += 1

    # --- researcher minting ------------------------------------------------
    def mint_researcher_id(self, family_name, given_name, year):
        """Mint/reuse a researcher identifier, keeping the first-seen year."""
        fam, initial = name_natural_key(family_name, given_name)
        key = (fam, initial)
        if key in self.researcher_registry:
            return self.researcher_registry[key]
        year_part = str(year) if year is not None else "unknown"
        identifier = f"researcher:{fam}_{initial}_{year_part}"
        self.researcher_registry[key] = identifier
        return identifier

    # --- per-row extraction ------------------------------------------------
    def process_row(self, row):
        """Extract every entity/relationship from a single CSV row.

        Returns True if the row was processed, False if skipped for lack of an
        Id (the only fatal per-row condition). Field-level parse failures null
        the field and never abort the row.
        """
        maglab_id = parse_int(row.get("Id"))
        if maglab_id is None:
            print(f"SKIP row (no Id): {clean(row.get('Title')) or '<no title>'}")
            self.counts["rows_skipped_no_id"] += 1
            return False

        self.counts["rows_processed"] += 1
        self._cur_source_id = f"maglab:{maglab_id}"
        self._cur_evidence = f"Extracted from MagLab CSV row maglab_id={maglab_id}"

        year = parse_int(row.get("Published Year"))
        doi, url = resolve_doi_and_url(
            row.get("Digital Object Identifier"), row.get("Url")
        )
        primary_id = publication_identifier(doi, maglab_id)

        # --- Publication (honor idempotency) ---
        if primary_id in self.seen:
            print(f"SKIP {primary_id} (publication exists)")
            self.counts["publications_skipped"] += 1
        else:
            pub_props = {
                "maglab_id": maglab_id,
                "doi": doi,
                "title": clean(row.get("Title")),
                "publication_year": year,
                "resource_type": "JournalArticle",
                "month_published": clean(row.get("Month Published")),
                "volume": clean(row.get("Volume")),
                "issue": clean(row.get("Issue")),
                "pages": clean(row.get("Pages")),
                "url": url,
                "maglab_significant": parse_bool(row.get("MagLab Significant")),
                "acknowledged_nsf_grant": parse_bool(
                    row.get("Acknowledgement of the MagLab's NSF core grant")
                ),
                "is_ground_truth": is_ground_truth(doi),
            }
            self.add_entity("Publication", primary_id, pub_props,
                            "publications_written")
            self.seen.add(primary_id)

        # --- Researchers from Authors (build first, flag corr-authors after) ---
        # row_researchers: natural_key -> {"id":..., "props":...}
        row_researchers = {}
        author_order = []  # list of (natural_key, sequence)

        authors = split_multi(row.get("Authors"), ";")
        for seq, token in enumerate(authors, start=1):
            family, given, full = parse_name(token)
            if family is None:
                continue
            key = name_natural_key(family, given)
            rid = self.mint_researcher_id(family, given, year)
            if key not in row_researchers:
                row_researchers[key] = {
                    "id": rid,
                    "props": {
                        "family_name": family,
                        "given_name": given,
                        "name_full": full,
                        "is_corresponding_author": None,
                        "is_nhmfl_author": None,
                    },
                }
            author_order.append((key, seq))

        # --- Corresponding authors (slots 1..3) ---
        for n in (1, 2, 3):
            corr_token = clean(row.get(f"Corr Auth {n} Last, First Name"))
            if corr_token is None:
                continue
            family, given, full = parse_name(corr_token)
            if family is None:
                continue
            key = name_natural_key(family, given)
            if key in row_researchers:
                entry = row_researchers[key]
            else:
                rid = self.mint_researcher_id(family, given, year)
                entry = {
                    "id": rid,
                    "props": {
                        "family_name": family,
                        "given_name": given,
                        "name_full": full,
                        "is_corresponding_author": None,
                        "is_nhmfl_author": None,
                    },
                }
                row_researchers[key] = entry
            entry["props"]["is_corresponding_author"] = True

            # NHMFL / Ext flags map onto is_nhmfl_author for THIS corr-author.
            if clean(row.get(f"Corr Auth {n} NHMFL")) == "X":
                entry["props"]["is_nhmfl_author"] = True
            elif clean(row.get(f"Corr Auth {n} Ext")) == "X":
                entry["props"]["is_nhmfl_author"] = False

        # Write all researcher records for this row (dedup happens in 03).
        for entry in row_researchers.values():
            self.add_entity("Researcher", entry["id"], entry["props"],
                            "researchers_written")

        # AUTHORED_BY relationships (only for names that appeared in Authors).
        for key, seq in author_order:
            self.add_relationship(
                "AUTHORED_BY", primary_id, "Publication",
                row_researchers[key]["id"], "Researcher",
                {"author_sequence": seq},
            )

        # --- Journal ---
        journal_name = clean(row.get("Journal Name"))
        if journal_name:
            journal_id = f"journal:{slugify(journal_name)}"
            self.add_entity("Journal", journal_id, {
                "name": journal_name,
                "abbreviation": clean(row.get("Journal Abbreviation")),
            }, "journals_written")
            self.add_relationship("PUBLISHED_IN", primary_id, "Publication",
                                  journal_id, "Journal", {})

        # --- Facilities (multi-value on comma) ---
        for fac in split_multi(row.get("Facilities"), ","):
            facility_id = f"facility:{slugify(fac)}"
            self.add_entity("Facility", facility_id, {"name": fac},
                            "facilities_written")
            self.add_relationship("CONDUCTED_AT", primary_id, "Publication",
                                  facility_id, "Facility", {})

        # --- Instruments (multi-value on comma) ---
        # The CSV Magnet Systems column is used to determine which
        # Instrument node to connect to (via USES_INSTRUMENT relationship),
        # but the raw string is no longer stored as a property.
        # Per established decision 2026-06-29.
        for magnet in split_multi(row.get("Magnet Systems"), ","):
            instrument_id = f"instrument:raw:{slugify(magnet)}"
            self.add_entity("Instrument", instrument_id, {
                "canonical_name": None,  # filled in 03_normalize.py
                "psi_ms_id": None,       # filled in 03_normalize.py
            }, "instruments_written")
            self.add_relationship("USES_INSTRUMENT", primary_id, "Publication",
                                  instrument_id, "Instrument", {})

        # --- Datasets (multi-value on comma) ---
        seen_dataset_ids = set()  # avoid duplicate HAS_DATASET within one row
        for ds_url in split_multi(row.get("Data Set Urls"), ","):
            result = classify_dataset_url(ds_url)
            if result[0] == "__SKIP__":
                reason = result[1]
                print(f"SKIP dataset URL ({reason}): {ds_url}")
                self.proteosafe_skips.append((maglab_id, ds_url, reason))
                self.counts["datasets_skipped_proteosafe"] += 1
                continue
            repository, accession, review = result
            dataset_id = dataset_identifier(repository, accession)
            if dataset_id in seen_dataset_ids:
                continue
            seen_dataset_ids.add(dataset_id)
            props = {
                "repository": repository,
                "accession": accession,
                "source_url": ds_url,
                "manual_review_needed": review,
            }
            self.add_entity("Dataset", dataset_id, props, "datasets_written")
            if repository == "Other":
                self.counts["datasets_flagged_review"] += 1
            self.add_relationship("HAS_DATASET", primary_id, "Publication",
                                  dataset_id, "Dataset", {})

        # --- Funder (only when the NSF grant was acknowledged) ---
        if parse_bool(row.get("Acknowledgement of the MagLab's NSF core grant")) is True:
            self.add_entity("Funder", "funder:nsf", {
                "name": "National Science Foundation",
                "ror_id": "https://ror.org/021nxhr62",
            }, "funders_written")
            self.add_relationship("FUNDED_BY", primary_id, "Publication",
                                  "funder:nsf", "Funder", {})

        return True


# ---------------------------------------------------------------------------
# I/O — load existing publication ids, flush collected records to disk
# ---------------------------------------------------------------------------
def derive_pub_id(rec):
    """Best-effort publication identifier for a record from publications.jsonl.

    Handles both 02b records (which carry "identifier") and the differently
    shaped 02_extract.py records (which carry "doi"/"year" but no identifier).
    """
    if rec.get("identifier"):
        return rec["identifier"]
    props = rec.get("properties", rec)
    doi = props.get("doi") or rec.get("doi")
    if doi:
        return f"doi:{doi.lower()}"
    mid = props.get("maglab_id") or rec.get("maglab_id")
    if mid is not None:
        return f"pub:maglab:{mid}"
    return None


def load_existing_publication_ids(path):
    seen = set()
    if not path.exists():
        return seen
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            pid = derive_pub_id(rec)
            if pid:
                seen.add(pid)
    return seen


def append_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")


def flush(extractor):
    for entity_type, records in extractor.entities.items():
        if records:
            append_jsonl(ENTITY_FILES[entity_type], records)
    if extractor.relationships:
        append_jsonl(RELATIONSHIPS_FILE, extractor.relationships)


# ---------------------------------------------------------------------------
# Validation checks (run automatically after extraction)
# ---------------------------------------------------------------------------
PROVENANCE_KEYS = {
    "source_type", "confidence", "extracted_at",
    "evidence_note", "source_id", "schema_version",
}
ID_RE = re.compile(r"^[a-z][a-z0-9_]*:.+")


def run_validations(extractor):
    """Return exit code (0 ok, 1 on a hard failure such as a leaked email)."""
    print("\n=== Validation checks ===")
    exit_code = 0

    # 1. Email check — researchers.jsonl must contain no "@" at all.
    researchers_path = ENTITY_FILES["Researcher"]
    at_lines = 0
    if researchers_path.exists():
        with open(researchers_path, encoding="utf-8") as f:
            at_lines = sum(1 for line in f if "@" in line)
    if at_lines:
        print(f"  [1] Email check ......... FAIL — {at_lines} line(s) contain '@'")
        exit_code = 1
    else:
        print("  [1] Email check ......... OK (0 '@' in researchers.jsonl)")

    # The remaining checks validate the records THIS run produced. (publications
    # .jsonl may also hold 02_extract.py records with a different schema; those
    # are intentionally not held to the 02b envelope.)
    all_records = [r for recs in extractor.entities.values() for r in recs]
    all_records += extractor.relationships

    # 2. Provenance check — every written record carries all six keys.
    missing = sum(1 for r in all_records if not PROVENANCE_KEYS.issubset(r))
    if missing:
        print(f"  [2] Provenance check .... FAIL — {missing} record(s) missing keys")
        exit_code = 1
    else:
        print(f"  [2] Provenance check .... OK ({len(all_records)} records, 6 keys each)")

    # 3. Orphan check — every relationship endpoint resolves to an entity id.
    orphans = 0
    for rel in extractor.relationships:
        if rel["subject_id"] not in extractor.id_sets.get(rel["subject_type"], set()):
            orphans += 1
        elif rel["object_id"] not in extractor.id_sets.get(rel["object_type"], set()):
            orphans += 1
    print(f"  [3] Orphan check ........ {orphans} orphaned relationship endpoint(s)")
    if orphans:
        exit_code = 1

    # 4. Identifier format check — namespace:value on every identifier.
    bad = []
    for r in all_records:
        if "identifier" in r and not ID_RE.match(r["identifier"]):
            bad.append(r["identifier"])
        for key in ("subject_id", "object_id"):
            if key in r and not ID_RE.match(r[key]):
                bad.append(r[key])
    if bad:
        print(f"  [4] Identifier format ... FAIL — {len(bad)} malformed, e.g. {bad[:3]}")
        exit_code = 1
    else:
        print("  [4] Identifier format ... OK (all match namespace:value)")

    return exit_code


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------
def update_manifest(rows_processed):
    """Add a csv_extraction stage marker to the operational manifest.

    The manifest is pipeline state (01/02/02d already write it), not immutable
    raw scientific data; existing content is preserved.
    """
    manifest = {}
    if MANIFEST.exists():
        try:
            with open(MANIFEST, encoding="utf-8") as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            manifest = {}
    manifest["csv_extraction"] = {
        "stage_complete": True,
        "completed_at": now_iso(),
        "rows_processed": rows_processed,
        "source_file": str(CSV_PATH).replace("\\", "/"),
    }
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def print_summary(extractor):
    c = extractor.counts
    print("\n=== Extraction summary ===")
    print(f"  Rows processed:                {c['rows_processed']}")
    print(f"  Publications written:          {c['publications_written']}")
    print(f"  Publications skipped (exist):  {c['publications_skipped']}")
    print(f"  Researchers written:           {c['researchers_written']}")
    print(f"  Journals written:              {c['journals_written']}")
    print(f"  Facilities written:            {c['facilities_written']}")
    print(f"  Instruments written:           {c['instruments_written']}")
    print(f"  Datasets written:              {c['datasets_written']}")
    print(f"  Datasets skipped (ProteoSAFe): {c['datasets_skipped_proteosafe']}")
    print(f"  Datasets flagged for review:   {c['datasets_flagged_review']}"
          f"  (repository: \"Other\")")
    print(f"  Funders written:               {c['funders_written']}")
    print(f"  Relationships written:         {c['relationships_written']}")
    print(f"  Rows skipped (no Id):          {c['rows_skipped_no_id']}")


def main():
    if not CSV_PATH.exists():
        print(f"ERROR: input CSV not found: {CSV_PATH}")
        return 1

    ENTITIES_DIR.mkdir(parents=True, exist_ok=True)
    RELATIONSHIPS_DIR.mkdir(parents=True, exist_ok=True)

    seen = load_existing_publication_ids(PUBLICATIONS_FILE)
    print(f"Found {len(seen)} existing Publication records")

    extractor = Extractor(seen_publication_ids=seen)

    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            extractor.process_row(row)

    flush(extractor)
    print_summary(extractor)
    update_manifest(extractor.counts["rows_processed"])

    exit_code = run_validations(extractor)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
