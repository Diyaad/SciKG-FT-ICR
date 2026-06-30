"""
02c_extract_rawfiles.py — SciKG pipeline stage 2c (extract from RAW-file metadata)

Reads the 46 enriched FOXDEN JSON files in data/processed/rawfiles_enriched/
(produced by scripts/merge_rawfile_metadata.py: a manual "filename_metadata"
block prepended onto the original fisher_py/FOXDEN content) and writes:

  data/processed/entities/rawfiles.jsonl                     (new)
  data/processed/entities/samples.jsonl                      (new)
  data/processed/entities/instruments.jsonl                  (APPEND, dedupe)
  data/processed/entities/software.jsonl                     (new)
  data/processed/relationships/rawfile_relationships.jsonl   (new)

This stage ONLY extracts fields explicitly present in the enriched files.
Nothing is inferred. Blank fields are written as null. It mirrors the entity /
relationship envelope, provenance keys, JSONL output, idempotency, and
end-of-run validation of scripts/02b_extract_csv.py:

  - Property names ....... snake_case
  - Entity type labels ... PascalCase         (RawDataFile, Sample, Instrument)
  - Relationship types ... SCREAMING_SNAKE     (COLLECTED_ON, OPERATED_BY)
  - Identifiers .......... namespace:value     (rawfile:..., sample:..., ...)

Provenance source_type by entity (per task spec):
  RawDataFile -> "merged_csv_foxden"   Sample    -> "manual_annotation"
  Instrument  -> "fisher_py"           Software  -> "fisher_py"
Relationship source_type follows the evidence the edge is drawn from:
  COLLECTED_ON / ACQUIRED_WITH -> "fisher_py"      (FOXDEN instrument/software)
  OPERATED_BY  / CONTAINS_SAMPLE -> "manual_annotation"  (filename_metadata)

The operator of all 46 files is one person who already exists in
researchers.jsonl as "researcher:butcher_d_2024" (from 02b). That identifier is
reused verbatim for every OPERATED_BY edge; no new Researcher is minted and the
operator name is never parsed. If that identifier is absent when this stage
runs, it stops rather than guessing.

Standard library only: json, re, sys, datetime, pathlib. No API calls, no
third-party packages. Inputs in data/raw/ and data/processed/rawfiles_enriched/
are never modified.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- Paths -----------------------------------------------------------------
RAWFILES_DIR = Path("data/processed/rawfiles_enriched")
ENTITIES_DIR = Path("data/processed/entities")
RELATIONSHIPS_DIR = Path("data/processed/relationships")
RESEARCHERS_FILE = ENTITIES_DIR / "researchers.jsonl"
RELATIONSHIPS_FILE = RELATIONSHIPS_DIR / "rawfile_relationships.jsonl"

# Each entity type label -> its output file.
ENTITY_FILES = {
    "RawDataFile": ENTITIES_DIR / "rawfiles.jsonl",
    "Sample": ENTITIES_DIR / "samples.jsonl",
    "Instrument": ENTITIES_DIR / "instruments.jsonl",
    "Software": ENTITIES_DIR / "software.jsonl",
}

SCHEMA_VERSION = "v1.0"
CONFIDENCE = "high"

# Provenance source_type per entity type.
SOURCE_RAWFILE = "merged_csv_foxden"
SOURCE_SAMPLE = "manual_annotation"
SOURCE_INSTRUMENT = "fisher_py"
SOURCE_SOFTWARE = "fisher_py"

# The operator of every RAW file already exists as a Researcher (from 02b).
# Reused verbatim — never minted, never parsed from operator_name.
OPERATOR_RESEARCHER_ID = "researcher:butcher_d_2024"

# Filename-metadata keys copied straight onto the RawDataFile record.
FILENAME_METADATA_FIELDS = [
    "operator_initials", "operator_name", "date_acquired",
    "sample_organism_strain", "sample_state", "sample_growth_medium",
    "sample_growth_date", "bioreplicate_id", "sample_prep_method",
    "fractionation_method", "fraction_id", "experimental_parameters",
    "run_number",
]

# Sample-node identity fields, in identifier order (null fields skipped).
SAMPLE_IDENTITY_FIELDS = [
    "sample_organism_strain", "sample_state",
    "sample_growth_medium", "sample_growth_date",
]


# ---------------------------------------------------------------------------
# Small value helpers (kept byte-for-byte consistent with 02b_extract_csv.py)
# ---------------------------------------------------------------------------
def now_iso():
    """UTC ISO-8601 with a trailing Z, matching the task-spec examples."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def clean(value):
    """Trim strings; map empty string to None. Non-strings pass through.

    The enriched files already use JSON null for missing values, so this is a
    light guard rather than the CSV-style placeholder scrub.
    """
    if value is None:
        return None
    if isinstance(value, str):
        v = value.strip()
        return v or None
    return value


def slugify(text):
    """Lowercase, collapse any run of non-alphanumerics to a single underscore.

    e.g. "LTQ Orbitrap Velos" -> "ltq_orbitrap_velos", "2019-04-04" ->
    "2019_04_04". Identical to 02b so identifiers stay consistent across stages.
    """
    if text is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")


# ---------------------------------------------------------------------------
# Source-file field access — read-only, never mutates the enriched file
# ---------------------------------------------------------------------------
def first_haspart(record):
    """Return user_metadata.hasPart[0] or {} (all 46 files have exactly one)."""
    hp = (record.get("user_metadata") or {}).get("hasPart")
    if isinstance(hp, list) and hp and isinstance(hp[0], dict):
        return hp[0]
    return {}


def sample_identifier(fm):
    """sample:{organism}_{state}_{medium}_{date} — slugified, null fields skipped.

    Files with identical sample identity fields produce the same identifier and
    therefore share one Sample node.
    """
    parts = [slugify(fm.get(k)) for k in SAMPLE_IDENTITY_FIELDS if clean(fm.get(k))]
    return "sample:" + "_".join(parts)


# ---------------------------------------------------------------------------
# Extractor — accumulates records in memory; main() flushes to disk
# ---------------------------------------------------------------------------
class Extractor:
    def __init__(self, existing_ids=None):
        # entity_type -> set of identifiers already on disk (idempotency + orphan
        # resolution). Includes a "Researcher" set loaded from researchers.jsonl.
        self.existing_ids = existing_ids or {}
        self.entities = {etype: [] for etype in ENTITY_FILES}
        self.relationships = []
        # entity_type -> identifiers created during THIS run.
        self.id_sets = {etype: set() for etype in ENTITY_FILES}
        self._skip_printed = set()
        self.counts = {
            "files_processed": 0,
            "rawfiles_written": 0,
            "rawfiles_skipped": 0,
            "samples_written": 0,
            "instruments_written": 0,
            "software_written": 0,
            "relationships_written": 0,
            "relationships_skipped": 0,
        }
        self._cur_source_id = None
        self._cur_evidence = None

    # --- record builders ---------------------------------------------------
    def _provenance(self, source_type):
        return {
            "source_type": source_type,
            "confidence": CONFIDENCE,
            "extracted_at": now_iso(),
            "evidence_note": self._cur_evidence,
            "source_id": self._cur_source_id,
            "schema_version": SCHEMA_VERSION,
        }

    def add_entity(self, entity_type, identifier, properties, source_type,
                   written_key):
        """Add an entity, deduping within this run and against existing output.

        Returns the identifier so callers can wire relationships even when the
        node was deduped or already on disk.
        """
        if identifier in self.id_sets[entity_type]:
            return identifier  # same node already created this run (e.g. shared)
        if identifier in self.existing_ids.get(entity_type, set()):
            if identifier not in self._skip_printed:
                print(f"SKIP {identifier} ({entity_type} already in output)")
                self._skip_printed.add(identifier)
            self.id_sets[entity_type].add(identifier)  # keep relationships valid
            return identifier
        record = {
            "identifier": identifier,
            "entity_type": entity_type,
            "properties": properties,
        }
        record.update(self._provenance(source_type))
        self.entities[entity_type].append(record)
        self.id_sets[entity_type].add(identifier)
        self.counts[written_key] += 1
        return identifier

    def add_relationship(self, rel_type, subject_id, object_id, object_type,
                         source_type, properties=None):
        record = {
            "relationship_type": rel_type,
            "subject_id": subject_id,
            "subject_type": "RawDataFile",
            "object_id": object_id,
            "object_type": object_type,
            "properties": properties or {},
        }
        record.update(self._provenance(source_type))
        self.relationships.append(record)
        self.counts["relationships_written"] += 1

    # --- per-file extraction ----------------------------------------------
    def process_file(self, path):
        """Extract every entity/relationship from one enriched FOXDEN file."""
        with open(path, encoding="utf-8") as f:
            record = json.load(f)

        self.counts["files_processed"] += 1
        fm = record.get("filename_metadata") or {}
        hp = first_haspart(record)
        instrument = hp.get("instrument") or {}
        software = hp.get("software") or {}

        filename = clean(record.get("filename"))
        self._cur_source_id = f"rawfiles_enriched:{path.name}"
        self._cur_evidence = f"Extracted from {path.name}"

        rawfile_id = f"rawfile:{filename}"

        # --- RawDataFile (idempotency: skip if already written) ---
        if rawfile_id in self.existing_ids.get("RawDataFile", set()):
            print(f"SKIP {rawfile_id} (RawDataFile already in output)")
            self.counts["rawfiles_skipped"] += 1
            self.id_sets["RawDataFile"].add(rawfile_id)
        else:
            props = {k: clean(fm.get(k)) for k in FILENAME_METADATA_FIELDS}
            # run_number stays an int (clean() passes non-strings through).
            props.update({
                "filename": filename,
                "original_filepath": clean(record.get("filepath")),
                "sha256_hash": clean(record.get("sha256_hash")),
                "date_file_created": clean(record.get("dateCreated")),
                "date_file_modified": clean(record.get("dateModified")),
                "instrument_name_raw": clean(instrument.get("name")),
                "instrument_model_raw": clean(instrument.get("model")),
                "acquisition_software_name": clean(software.get("name")),
                "acquisition_software_version": clean(
                    software.get("softwareVersion")),
            })
            self.add_entity("RawDataFile", rawfile_id, props,
                            SOURCE_RAWFILE, "rawfiles_written")

        # --- Sample (always; shared across files with identical identity) ---
        sample_id = sample_identifier(fm)
        sample_props = {k: clean(fm.get(k)) for k in SAMPLE_IDENTITY_FIELDS}
        self.add_entity("Sample", sample_id, sample_props,
                        SOURCE_SAMPLE, "samples_written")
        self.add_relationship("CONTAINS_SAMPLE", rawfile_id, sample_id,
                              "Sample", SOURCE_SAMPLE)

        # --- Operator (reuse existing Researcher; never mint) ---
        self.add_relationship("OPERATED_BY", rawfile_id, OPERATOR_RESEARCHER_ID,
                              "Researcher", SOURCE_SAMPLE)

        # --- Instrument (dedupe across files + against instruments.jsonl) ---
        instrument_name = clean(instrument.get("name"))
        if instrument_name:
            instrument_id = f"instrument:raw:{slugify(instrument_name)}"
            self.add_entity("Instrument", instrument_id, {
                "name_raw": instrument_name,
                "model_raw": clean(instrument.get("model")),
                "canonical_name": None,  # filled in 03_normalize.py
                "psi_ms_id": None,       # filled in 03_normalize.py
            }, SOURCE_INSTRUMENT, "instruments_written")
            self.add_relationship("COLLECTED_ON", rawfile_id, instrument_id,
                                  "Instrument", SOURCE_INSTRUMENT)

        # --- Software (dedupe across files) ---
        software_name = clean(software.get("name"))
        if software_name:
            software_version = clean(software.get("softwareVersion"))
            software_id = (f"software:{slugify(software_name)}"
                           f":{slugify(software_version)}")
            self.add_entity("Software", software_id, {
                "name": software_name,
                "version": software_version,
            }, SOURCE_SOFTWARE, "software_written")
            self.add_relationship("ACQUIRED_WITH", rawfile_id, software_id,
                                  "Software", SOURCE_SOFTWARE)


# ---------------------------------------------------------------------------
# I/O — load existing identifiers, flush collected records to disk
# ---------------------------------------------------------------------------
def load_existing_entity_ids(path):
    """Set of "identifier" values from an entity JSONL file (empty if absent)."""
    ids = set()
    if not path.exists():
        return ids
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("identifier"):
                ids.add(rec["identifier"])
    return ids


def load_existing_rel_keys(path):
    """Set of (rel_type, subject_id, object_id) for relationship idempotency."""
    keys = set()
    if not path.exists():
        return keys
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            keys.add((rec.get("relationship_type"),
                      rec.get("subject_id"), rec.get("object_id")))
    return keys


def append_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")


def flush(extractor, existing_rel_keys):
    """Write new entities and new (non-duplicate) relationships to disk."""
    for entity_type, records in extractor.entities.items():
        if records:
            append_jsonl(ENTITY_FILES[entity_type], records)
    fresh = []
    for rel in extractor.relationships:
        key = (rel["relationship_type"], rel["subject_id"], rel["object_id"])
        if key in existing_rel_keys:
            extractor.counts["relationships_skipped"] += 1
            extractor.counts["relationships_written"] -= 1
            continue
        existing_rel_keys.add(key)
        fresh.append(rel)
    if fresh:
        append_jsonl(RELATIONSHIPS_FILE, fresh)


# ---------------------------------------------------------------------------
# Validation checks (run automatically after extraction)
# ---------------------------------------------------------------------------
PROVENANCE_KEYS = {
    "source_type", "confidence", "extracted_at",
    "evidence_note", "source_id", "schema_version",
}
ID_RE = re.compile(r"^[a-z][a-z0-9_]*:.+")
EXPECTED_RAWFILES = 46


def run_validations(extractor):
    """Return exit code (0 ok, 1 on any hard failure)."""
    print("\n=== Validation checks ===")
    exit_code = 0

    # 1. Email check — no output file may contain an "@".
    at_files = []
    for path in list(ENTITY_FILES.values()) + [RELATIONSHIPS_FILE]:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                if any("@" in line for line in f):
                    at_files.append(path.name)
    if at_files:
        print(f"  [1] Email check ......... FAIL — '@' in {at_files}")
        exit_code = 1
    else:
        print("  [1] Email check ......... OK (no '@' in any output file)")

    all_records = [r for recs in extractor.entities.values() for r in recs]
    all_records += extractor.relationships

    # 2. Provenance check — every written record carries all six keys.
    missing = sum(1 for r in all_records if not PROVENANCE_KEYS.issubset(r))
    if missing:
        print(f"  [2] Provenance check .... FAIL — {missing} record(s) missing keys")
        exit_code = 1
    else:
        print(f"  [2] Provenance check .... OK ({len(all_records)} records, 6 keys each)")

    # 3. Orphan check — every relationship endpoint resolves to a known entity.
    #    Known = entities created this run OR already present on disk (incl. the
    #    operator Researcher from researchers.jsonl).
    def known(etype):
        return extractor.id_sets.get(etype, set()) | \
            extractor.existing_ids.get(etype, set())
    orphans = 0
    for rel in extractor.relationships:
        if rel["subject_id"] not in known(rel["subject_type"]):
            orphans += 1
        elif rel["object_id"] not in known(rel["object_type"]):
            orphans += 1
    if orphans:
        print(f"  [3] Orphan check ........ FAIL — {orphans} orphaned endpoint(s)")
        exit_code = 1
    else:
        print(f"  [3] Orphan check ........ OK ({len(extractor.relationships)} relationships)")

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

    # 5. Completeness check — all 46 RawDataFiles written or skipped (none lost).
    accounted = extractor.counts["rawfiles_written"] + extractor.counts["rawfiles_skipped"]
    if accounted != EXPECTED_RAWFILES:
        print(f"  [5] RawDataFile count ... FAIL — {accounted} of {EXPECTED_RAWFILES} accounted for")
        exit_code = 1
    else:
        print(f"  [5] RawDataFile count ... OK ({accounted}/{EXPECTED_RAWFILES} written or skipped)")

    return exit_code


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def print_summary(extractor):
    c = extractor.counts
    print("\n=== Extraction summary ===")
    print(f"  Files processed:           {c['files_processed']}")
    print(f"  RawDataFiles written:      {c['rawfiles_written']}")
    print(f"  RawDataFiles skipped:      {c['rawfiles_skipped']}")
    print(f"  Samples written:           {c['samples_written']}")
    print(f"  Instruments written:       {c['instruments_written']}")
    print(f"  Software written:          {c['software_written']}")
    print(f"  Relationships written:     {c['relationships_written']}")
    print(f"  Relationships skipped:     {c['relationships_skipped']}")


def main():
    if not RAWFILES_DIR.exists():
        print(f"ERROR: input directory not found: {RAWFILES_DIR}")
        return 1

    files = sorted(RAWFILES_DIR.glob("*.json"))
    if not files:
        print(f"ERROR: no enriched JSON files in {RAWFILES_DIR}")
        return 1

    ENTITIES_DIR.mkdir(parents=True, exist_ok=True)
    RELATIONSHIPS_DIR.mkdir(parents=True, exist_ok=True)

    # The operator must already exist as a Researcher (minted by 02b). Stop
    # rather than guess if it is absent.
    researcher_ids = load_existing_entity_ids(RESEARCHERS_FILE)
    if OPERATOR_RESEARCHER_ID not in researcher_ids:
        print(f"ERROR: operator Researcher {OPERATOR_RESEARCHER_ID!r} not found "
              f"in {RESEARCHERS_FILE}. Run 02b first, or confirm the operator's "
              f"identifier before proceeding. Stopping rather than minting a new "
              f"Researcher.")
        return 1

    existing_ids = {etype: load_existing_entity_ids(path)
                    for etype, path in ENTITY_FILES.items()}
    existing_ids["Researcher"] = researcher_ids
    existing_rel_keys = load_existing_rel_keys(RELATIONSHIPS_FILE)

    for etype in ENTITY_FILES:
        if existing_ids[etype]:
            print(f"Found {len(existing_ids[etype])} existing {etype} record(s)")

    extractor = Extractor(existing_ids=existing_ids)
    for path in files:
        extractor.process_file(path)

    flush(extractor, existing_rel_keys)
    print_summary(extractor)

    return run_validations(extractor)


if __name__ == "__main__":
    sys.exit(main())
