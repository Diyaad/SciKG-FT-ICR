"""
02f_extract_pxd_rawfiles.py — extract RawDataFile + Dataset entities and
DERIVED_FROM relationships from the local-only PXD FOXDEN sweep.

SOURCE (LOCAL-ONLY, GITIGNORED — never commit): data/raw/rawfiles_pxd/
    952 FOXDEN JSON records for the Blood Proteoform Atlas deposition
    (ProteomeXchange PXD026123–PXD026154). These files carry internal
    hostnames, IPs, and Windows user paths. NONE of that leaves this script.

SCOPE FLAG (supervisor decision 2026-07-10: include all, flag provenance)
    ALL 952 files are emitted as RawDataFile nodes. There is no scope filter.
    Each node instead carries a boolean recording whether MagLab acquisition
    could be CONFIRMED:
        maglab_acquired_confirmed = (instrument serial == "LTQ40421")
    true  = confirmed MagLab-acquired (the 199 LTQ FT Ultra files).
    false = NOT confirmed — the FOXDEN record did not yield the MagLab serial.
            This is "unconfirmed", NOT "confirmed external". Never read false as
            a claim that the file is non-MagLab.

    Sanity check (not a halt): flag-true is expected to be 199 and flag-false
    753. A mismatch prints a WARNING but does not stop the run — the old STOP
    guard belonged to the filter, which no longer exists.

OUTPUTS (this stage exclusively owns these files; they are regenerated, not
appended-to, so re-running yields exactly one record per source file, never
duplicates):
    data/processed/entities/rawfiles_pxd.jsonl               (RawDataFile + Dataset)
    data/processed/relationships/rawfiles_pxd_relationships.jsonl  (DERIVED_FROM)
    data/processed/logs/pxd_extract_log.jsonl   (nulls, read errors, anomalies)
The scope skiplog is gone: with nothing excluded there is nothing to skip-log;
genuinely unreadable files are still recorded in the extract log. 02c's
rawfiles.jsonl is never touched.

GROUNDING RULE: every field is read from an explicit source path. If a path is
absent the value is null AND the omission is logged — nothing is ever inferred.
The one derived field, date_acquired, is PARSED FROM THE FILENAME (dateCreated
is the 2025 FOXDEN-sweep timestamp and is wrong for acquisition); if the
filename yields no unambiguous real date, the value is null and it is logged.

Standard library only. Python 3.11+. Run from the repository root:
    python scripts/02f_extract_pxd_rawfiles.py --dry-run   # report only, no writes
    python scripts/02f_extract_pxd_rawfiles.py             # write outputs
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO / "data" / "raw" / "rawfiles_pxd"
ENTITIES_OUT = REPO / "data" / "processed" / "entities" / "rawfiles_pxd.jsonl"
RELS_OUT = REPO / "data" / "processed" / "relationships" / "rawfiles_pxd_relationships.jsonl"
# SHARED entity files (also written by 02b/02c). 02f APPENDS Instrument/Software
# nodes here so 03's identifier-keyed dedup merges a shared instrument (e.g.
# instrument:raw:ltq_ft_ultra, minted by both 02c and 02f) into one node.
INSTRUMENTS_OUT = REPO / "data" / "processed" / "entities" / "instruments.jsonl"
SOFTWARE_OUT = REPO / "data" / "processed" / "entities" / "software.jsonl"
LOGS_DIR = REPO / "data" / "processed" / "logs"
EXTRACTLOG = LOGS_DIR / "pxd_extract_log.jsonl"

SCHEMA_VERSION = "v1.0"
SOURCE_TYPE = "fisher_py"
EVIDENCE_NOTE = ("Local-only PXD FOXDEN sweep (data/raw/rawfiles_pxd/, Blood "
                 "Proteoform Atlas, PXD026123–PXD026154).")

# --- MagLab-acquisition flag ------------------------------------------------
# The serial that confirms a file was acquired on the MagLab LTQ FT Ultra. Its
# presence is the ONLY positive evidence of MagLab acquisition in these records;
# its absence is unconfirmed, not disproof (see maglab_acquired_confirmed).
MAGLAB_SERIAL = "LTQ40421"
EXPECTED_MAGLAB_CONFIRMED = 199   # sanity check only; does NOT halt the run

# --- filename date parsing --------------------------------------------------
# Acquisition years for this corpus sit ~2017–2020. The window disambiguates the
# two filename formats: a YYYYMMDD token starts 19/20 (an invalid MM for the
# MMDDYYYY reading), an MMDDYYYY token starts 01–12 (an implausible YYYY for the
# YYYYMMDD reading), so no single 8-digit token is valid under both formats.
MIN_YEAR, MAX_YEAR = 1995, 2030
_EIGHT_DIGIT = re.compile(r"(?<!\d)\d{8}(?!\d)")
_PXD = re.compile(r"PXD\d+", re.IGNORECASE)


# --------------------------- value helpers ----------------------------------
def slugify(text):
    """Lowercase, collapse any run of non-alphanumerics to a single underscore.
    Byte-for-byte identical to 02b/02c so identifiers match across stages
    (e.g. "LTQ FT Ultra" -> "ltq_ft_ultra")."""
    if text is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")


def clean(value):
    """Trim strings; empty/whitespace-only -> None. Non-strings pass through.
    Mirrors 02c so identifier inputs match and no empty slug is ever produced."""
    if isinstance(value, str):
        v = value.strip()
        return v or None
    return value


# --------------------------- structural helpers -----------------------------
def first_dict(x):
    """FOXDEN emits some blocks (instrument, software, instrumentMethod) as a
    bare dict on 199 files but as a single-element LIST on 709 others. Coerce to
    the dict either way; anything else becomes {} so lookups stay total."""
    if isinstance(x, dict):
        return x
    if isinstance(x, list):
        for e in x:
            if isinstance(e, dict):
                return e
    return {}


def has_part_0(record):
    hp = (record.get("user_metadata") or {}).get("hasPart") or []
    return first_dict(hp[0]) if hp else {}


def instrument_serial(record):
    inst = first_dict(has_part_0(record).get("instrument"))
    return first_dict(inst.get("serialNumber")).get("value")


def maglab_acquired_confirmed(record):
    """True iff the file's instrument serial confirms MagLab acquisition.
    IMPORTANT: False means "not confirmed" — the FOXDEN record did not yield the
    MagLab serial — NOT "confirmed external". Never read False as a claim that
    the file is non-MagLab."""
    return instrument_serial(record) == MAGLAB_SERIAL


# ------------------------------ field parsing -------------------------------
def collect_activation_types(instrument_method):
    """Sorted unique list of every "Activation Type" value found anywhere under
    the instrumentMethod subtree (values live in per-segment scan_events).

    Returns None — NOT [] — when nothing is found. The 753 Orbitrap files use a
    FOXDEN method format this parser does not fully read, so a zero-find there
    means "not parsed / unknown" and must not be reported as "no fragmentation".
    None = unknown; a non-empty list = what was actually recovered. We never emit
    [], because we cannot tell a genuinely fragmentation-free run from an unparsed
    method, and asserting [] would over-claim."""
    found = set()

    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "Activation Type" and isinstance(v, str) and v.strip():
                    found.add(v.strip())
                else:
                    walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(instrument_method)
    return sorted(found) if found else None


def parse_acquisition_date(filename):
    """Parse acquisition date from the filename. Returns (iso_date_or_None,
    reason_or_None). Tries YYYYMMDD then MMDDYYYY on every 8-digit token, keeping
    only tokens that land in [MIN_YEAR, MAX_YEAR]. Exactly one distinct valid
    date -> use it; none -> (None, 'date_unparseable'); more than one distinct ->
    (None, 'date_ambiguous'). Never guesses between candidates."""
    candidates = {}  # iso date -> format label
    for tok in _EIGHT_DIGIT.findall(filename):
        for fmt in ("%Y%m%d", "%m%d%Y"):
            try:
                dt = datetime.strptime(tok, fmt)
            except ValueError:
                continue
            if MIN_YEAR <= dt.year <= MAX_YEAR:
                candidates[dt.date().isoformat()] = fmt
    if len(candidates) == 1:
        return next(iter(candidates)), None
    if not candidates:
        return None, "date_unparseable"
    return None, "date_ambiguous"


def extract_pxd(record):
    m = _PXD.search(record.get("filepath") or "")
    return m.group().upper() if m else None


# ------------------------------ record builders -----------------------------
def build_rawfile_entity(record, run_ts, log_events):
    """Emit the RawDataFile node. Grounds each property to an explicit source
    path; missing paths become null and are collected in null_fields. Excludes
    system_ip_address, system_name, instrument serial, and every Windows path."""
    hp = has_part_0(record)
    inst = first_dict(hp.get("instrument"))
    sw = first_dict(hp.get("software"))
    im = first_dict(hp.get("instrumentMethod"))

    filename = record.get("filename")
    date_acquired, date_reason = parse_acquisition_date(filename or "")
    if date_reason:
        log_events.append({"event": date_reason, "filename": filename,
                           "note": "date_acquired set to null; not inferred."})

    props = {
        "filename": filename,
        "sha256": record.get("sha256_hash"),
        # KEEP the raw model string. Do NOT use instrument.name — for this
        # corpus it says "Orbitrap Velos Pro" and is wrong; model is authoritative.
        "instrument_model_raw": inst.get("model"),
        "software_name": sw.get("name"),
        "software_version": sw.get("softwareVersion"),
        # RAW creator string only — never resolved to a Researcher identifier here.
        "method_creator_raw": im.get("Creator"),
        "ms_run_time_min": im.get("MS Run Time (min)"),
        "scan_count": inst.get("Number of scans"),
        # None (not []) when no activation type was recovered — see
        # collect_activation_types. null here = "not parsed", NOT "no fragmentation".
        "activation_types_raw": collect_activation_types(im),
        "date_acquired": date_acquired,
        # true only when the MagLab serial is present. false = attribution not
        # recovered (UNCONFIRMED), NOT a claim the file is external.
        "maglab_acquired_confirmed": maglab_acquired_confirmed(record),
    }

    # Log every null-valued field so an absent value stays auditable and is never
    # silently read as a real one. null distinguishes "not recoverable from
    # source" from a real value and is never fabricated. (maglab_acquired_confirmed
    # is always a real boolean, so it never appears here.)
    null_fields = [k for k, v in props.items() if v is None]
    if null_fields:
        log_events.append({"event": "null_fields", "filename": filename,
                           "null_fields": null_fields,
                           "note": "Value not recoverable from source; wrote null, "
                                   "did not infer."})

    return {
        "identifier": f"rawfile:{filename}",
        "entity_type": "RawDataFile",
        "properties": props,
        "source_type": SOURCE_TYPE,
        "confidence": "high",
        "extracted_at": run_ts,
        "evidence_note": EVIDENCE_NOTE,
        "source_id": filename,
        "schema_version": SCHEMA_VERSION,
    }


def build_dataset_entity(pxd, source_filename, run_ts):
    """One Dataset node per distinct PXD accession. source_id records the
    in-scope file that first surfaced the accession (deterministic, sorted)."""
    # Namespace MUST match 02b's dataset_identifier() so the same real dataset
    # gets one identifier from both sources and 03's identifier-keyed dedup
    # merges it. 02b mints ProteomeXchange accessions as
    # dataset:proteomexchange:{accession_lower}; we mirror it exactly. The
    # repository *property* is also "ProteomeXchange" to match 02b and avoid a
    # merge-time property conflict; the PRIDE archive (the host) is recorded in
    # the url property instead.
    return {
        "identifier": f"dataset:proteomexchange:{pxd.lower()}",
        "entity_type": "Dataset",
        "properties": {
            "accession": pxd,
            "repository": "ProteomeXchange",
            "url": f"https://www.ebi.ac.uk/pride/archive/projects/{pxd}",
        },
        "source_type": SOURCE_TYPE,
        "confidence": "high",
        "extracted_at": run_ts,
        "evidence_note": EVIDENCE_NOTE,
        "source_id": source_filename,
        "schema_version": SCHEMA_VERSION,
    }


def build_derived_from(filename, pxd, run_ts):
    return {
        "relationship_type": "DERIVED_FROM",
        "subject_id": f"rawfile:{filename}",
        "subject_type": "RawDataFile",
        "object_id": f"dataset:proteomexchange:{pxd.lower()}",
        "object_type": "Dataset",
        "properties": {},
        "source_type": SOURCE_TYPE,
        "confidence": "high",
        "extracted_at": run_ts,
        "evidence_note": EVIDENCE_NOTE,
        "source_id": filename,
        "schema_version": SCHEMA_VERSION,
    }


def build_instrument_entity(identifier, name_raw, model_raw, run_ts, source_filename):
    """Instrument node in 02c's exact 4-field shape, for the SHARED
    instruments.jsonl. name_raw/model_raw are the cleaned raw strings;
    canonical_name/psi_ms_id stay null — 03_normalize.py fills them. The caller
    derives `identifier` from .model (fallback .name), so the MagLab LTQ FT Ultra
    gets ONE identifier shared with 02c despite the stale PXD .name."""
    return {
        "identifier": identifier,
        "entity_type": "Instrument",
        "properties": {
            "name_raw": name_raw,
            "model_raw": model_raw,
            "canonical_name": None,
            "psi_ms_id": None,
        },
        "source_type": SOURCE_TYPE,
        "confidence": "high",
        "extracted_at": run_ts,
        "evidence_note": EVIDENCE_NOTE,
        "source_id": source_filename,
        "schema_version": SCHEMA_VERSION,
    }


def build_software_entity(identifier, name, version, run_ts, source_filename):
    """Software node in 02c's exact 2-field shape, for the SHARED software.jsonl.
    identifier is software:{slug(name)}:{slug(version)} (version part of identity,
    matching 02c)."""
    return {
        "identifier": identifier,
        "entity_type": "Software",
        "properties": {"name": name, "version": version},
        "source_type": SOURCE_TYPE,
        "confidence": "high",
        "extracted_at": run_ts,
        "evidence_note": EVIDENCE_NOTE,
        "source_id": source_filename,
        "schema_version": SCHEMA_VERSION,
    }


def build_collected_on(filename, instrument_id, run_ts):
    return {
        "relationship_type": "COLLECTED_ON",
        "subject_id": f"rawfile:{filename}",
        "subject_type": "RawDataFile",
        "object_id": instrument_id,
        "object_type": "Instrument",
        "properties": {},
        "source_type": SOURCE_TYPE,
        "confidence": "high",
        "extracted_at": run_ts,
        "evidence_note": EVIDENCE_NOTE,
        "source_id": filename,
        "schema_version": SCHEMA_VERSION,
    }


def build_acquired_with(filename, software_id, run_ts):
    return {
        "relationship_type": "ACQUIRED_WITH",
        "subject_id": f"rawfile:{filename}",
        "subject_type": "RawDataFile",
        "object_id": software_id,
        "object_type": "Software",
        "properties": {},
        "source_type": SOURCE_TYPE,
        "confidence": "high",
        "extracted_at": run_ts,
        "evidence_note": EVIDENCE_NOTE,
        "source_id": filename,
        "schema_version": SCHEMA_VERSION,
    }


# --------------------------------- io ---------------------------------------
def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False))
            f.write("\n")


def append_jsonl(path, records):
    """Append records to a SHARED entity file (instruments/software) without
    truncating what 02b/02c already wrote."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False))
            f.write("\n")


# -------------------------------- main --------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="Extract all PXD RAW files, flagging MagLab-confirmed ones.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Classify and report only; write no output files.")
    args = ap.parse_args()

    if not SOURCE_DIR.is_dir():
        print(f"ERROR source dir missing: {SOURCE_DIR}")
        return 1

    run_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    files = sorted(SOURCE_DIR.glob("*.json"))
    if not files:
        print(f"ERROR no JSON files in {SOURCE_DIR}")
        return 1

    log_events = []
    records = []
    read_errors = 0

    # --- Load ALL files (no scope filter; every readable file becomes a node) -
    for path in files:
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError) as exc:
            read_errors += 1
            log_events.append({"event": "read_error", "filename": path.name,
                               "error": str(exc)})

    confirmed = sum(1 for r in records if maglab_acquired_confirmed(r))
    unconfirmed = len(records) - confirmed

    print("02f_extract_pxd summary")
    print(f"  source files scanned:  {len(files)}")
    print(f"  read OK:               {len(records)}")
    print(f"  read errors:           {read_errors}  (logged in extract log)")
    print(f"  maglab_acquired_confirmed = true:   {confirmed}")
    print(f"  maglab_acquired_confirmed = false:  {unconfirmed}  (unconfirmed, not external)")

    # --- Sanity check (warn only; the flag is advisory, never a filter) -----
    if confirmed != EXPECTED_MAGLAB_CONFIRMED:
        print(f"  WARNING: confirmed count {confirmed} != expected "
              f"{EXPECTED_MAGLAB_CONFIRMED}. Serial path may have drifted or the "
              f"source changed — continuing anyway (no halt).")

    # --- Build records for EVERY successfully-read file ---------------------
    entities, relationships = [], []
    datasets = {}       # pxd -> entity (deduped across files; first sorted file wins)
    instruments = {}    # identifier -> Instrument entity (deduped within this run)
    software = {}        # identifier -> Software entity (deduped within this run)
    for record in records:
        entities.append(build_rawfile_entity(record, run_ts, log_events))
        filename = record.get("filename")

        # --- Instrument node + COLLECTED_ON edge (mirror 02c) ---------------
        # NOTE: must run BEFORE the no-PXD `continue` below, or files lacking a
        # PXD accession would silently skip instrument/software extraction.
        hp = has_part_0(record)
        inst = first_dict(hp.get("instrument"))
        sw = first_dict(hp.get("software"))
        name_raw = clean(inst.get("name"))
        model_raw = clean(inst.get("model"))
        # Identity from the reliable .model; .name is stale for this corpus.
        # Fall back to .name only when .model is absent, and log it so an empty
        # identifier is never produced silently.
        id_source = model_raw
        if not id_source and name_raw:
            id_source = name_raw
            log_events.append({"event": "instrument_model_fallback",
                               "filename": filename,
                               "note": "instrument.model empty; identifier "
                                       "derived from instrument.name (logged, "
                                       "never a silent empty id)."})
        if id_source:
            instrument_id = f"instrument:raw:{slugify(id_source)}"
            if instrument_id not in instruments:
                instruments[instrument_id] = build_instrument_entity(
                    instrument_id, name_raw, model_raw, run_ts, filename)
            relationships.append(
                build_collected_on(filename, instrument_id, run_ts))

        # --- Software node + ACQUIRED_WITH edge (mirror 02c) ---------------
        sw_name = clean(sw.get("name"))
        if sw_name:
            sw_version = clean(sw.get("softwareVersion"))
            software_id = f"software:{slugify(sw_name)}:{slugify(sw_version)}"
            if software_id not in software:
                software[software_id] = build_software_entity(
                    software_id, sw_name, sw_version, run_ts, filename)
            relationships.append(
                build_acquired_with(filename, software_id, run_ts))

        # --- Deliberate divergence from 02c: NO Sample / CONTAINS_SAMPLE ---
        # 02c mints a Sample from its manual filename_metadata block and links it
        # via CONTAINS_SAMPLE. The PXD FOXDEN records carry only EMPTY sosa:Sample
        # blocks — there is no sample identity to ground — so we intentionally mint
        # neither node nor edge. Absent data, not an oversight.
        #
        # --- Deliberate divergence from 02c: NO Researcher / OPERATED_BY ---
        # 02c links a pre-existing Researcher via OPERATED_BY. The PXD records give
        # only a free-text method Creator, kept verbatim as method_creator_raw on
        # the RawDataFile (build_rawfile_entity). We do NOT resolve it to a
        # Researcher identifier or emit OPERATED_BY. Intentional, per existing
        # decision.

        pxd = extract_pxd(record)
        if not pxd:
            log_events.append({"event": "no_pxd_in_path", "filename": filename,
                               "note": "No PXD accession in filepath; RawDataFile "
                                       "emitted, Dataset link skipped."})
            continue
        if pxd not in datasets:
            datasets[pxd] = build_dataset_entity(pxd, filename, run_ts)
        relationships.append(build_derived_from(filename, pxd, run_ts))

    entities.extend(datasets[p] for p in sorted(datasets))

    # --- Report --------------------------------------------------------------
    rawfile_n = sum(1 for e in entities if e["entity_type"] == "RawDataFile")

    def rel_n(t):
        return sum(1 for r in relationships if r["relationship_type"] == t)

    print(f"  RawDataFile nodes:     {rawfile_n}")
    print(f"  Dataset nodes (PXD):   {len(datasets)}  {sorted(datasets)}")
    print(f"  Instrument nodes:      {len(instruments)}  {sorted(instruments)}")
    print(f"  Software nodes:        {len(software)}  {sorted(software)}")
    print(f"  DERIVED_FROM edges:    {rel_n('DERIVED_FROM')}")
    print(f"  COLLECTED_ON edges:    {rel_n('COLLECTED_ON')}")
    print(f"  ACQUIRED_WITH edges:   {rel_n('ACQUIRED_WITH')}")
    print(f"  extract-log events:    {len(log_events)}")

    if args.dry_run:
        print("\n--dry-run: no files written.")
        return 0

    # --- Write --------------------------------------------------------------
    # rawfiles_pxd.jsonl / rawfiles_pxd_relationships.jsonl are owned by this
    # stage and fully regenerated (truncate). Instrument/Software nodes instead
    # APPEND to the SHARED files (02b/02c also write them). 02f is NOT
    # independently idempotent against those shared files by design: they are
    # cleared and regenerated as a set (02b -> 02c -> 02f), and 03 dedups a shared
    # identifier (e.g. instrument:raw:ltq_ft_ultra) across sources by identifier.
    write_jsonl(ENTITIES_OUT, entities)
    write_jsonl(RELS_OUT, relationships)
    write_jsonl(EXTRACTLOG, log_events)
    append_jsonl(INSTRUMENTS_OUT, list(instruments.values()))
    append_jsonl(SOFTWARE_OUT, list(software.values()))
    print(f"\n  entities   -> {ENTITIES_OUT}")
    print(f"  relations  -> {RELS_OUT}")
    print(f"  extractlog -> {EXTRACTLOG}")
    print(f"  instruments-> {INSTRUMENTS_OUT}  (append, {len(instruments)} node(s))")
    print(f"  software   -> {SOFTWARE_OUT}  (append, {len(software)} node(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
