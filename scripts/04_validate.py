#!/usr/bin/env python3
"""
04_validate.py — validate normalized entities and relationships before load.

Stage 04 of the SciKG pipeline. Reads data/processed/normalized/, applies the
validation rules in docs/SCIKG_SCHEMA.md ("Validation Rules (applied by
04_validate.py)"), and writes:

    data/processed/validated/quarantine.jsonl        one record per FAILED item
    data/processed/validated/validation_report.json  counts + counted categories + blockers

It NEVER writes to Neo4j and NEVER modifies its inputs.

Exit code (R1): 0 iff quarantine is empty AND no blockers, else non-zero. The
quarantined/blocker counts are printed to stdout on every run.

------------------------------------------------------------------------------
DESIGN NOTES — the rulings this file encodes (Diya, 2026-07-17). Each conditional
is isolated in REQUIRED_SET / the constants below so a re-ruling is a one-line
change, not a rewrite.

  R1  exit non-zero iff anything quarantined OR any blocker present (RULED 2026-07-17:
      a validator holding a known 05 blocker must not exit 0).
  R2  Instrument.canonical_name null  -> counted 'uncanonicalized', NOT fatal.
  R3  reads normalized/ ONLY; never review_queue.jsonl. The 3 dangling edges 03
      withheld are already absent from normalized/ — the endpoint check still runs
      to catch any 03 missed (measured 0 on 2026-07-17).
  R10 edge endpoints are checked against SURVIVING nodes (post-quarantine), not all
      entities. A missing endpoint splits two ways: dangling_endpoint (exists nowhere)
      vs orphaned_by_quarantine (exists but failed validation this run). One level,
      non-recursive — see validate_edge().
  R4  outputs under data/processed/validated/.
  R5  the required-set is REQUIRED_SET below, derived from the schema M/R/O columns
      with every conditional ruled by Diya. "M when present" fields fail only on a
      malformed value, never on absence. Coverage-gap fields (④a/b/c/⑦) are counted
      'missing_coverage', never quarantined.
  R6  provenance: PRESENCE is fatal (a missing prov prop quarantines); VALUE is not
      enum-checked — an out-of-enum source_type/confidence is counted
      'provenance_out_of_enum', NOT fatal.
  R7  uniqueness pre-validated. Duplicate identifiers -> counted 'duplicate_identifier'.
      KI-8 remediated (2026-07-20): RawDataFile identity is the composite
      rawfile:{filename}:{sha16}, so its `identifier` IS uniqueness-checked like every
      other type. sha256_hash is a non-unique property; hashes shared across nodes are
      reported as the counted 'byte_identical_sets' category, not a blocker.
  R8  entity glob = every normalized/*.jsonl whose records carry entity_type, MINUS
      normalization_log.jsonl (a log that carries entity_type on 5002 rows) and
      review_queue.jsonl. See ENTITY_FILES / EXCLUDED_FILES.

  M1 / KI-8 — REMEDIATED (2026-07-20). RawDataFile identity moved to the composite
      rawfile:{filename}:{sha16} (03 Pass 1.5); uniqueness is on `identifier`, and
      sha256_hash is a non-unique property. Byte-identical files across distinct
      identifiers are now expected, not a violation: reported as the COUNTED,
      non-fatal category `byte_identical_sets` (one entry per hash shared by >1 node),
      and materialized as Advisory nodes + FLAGS edges by 03. No longer gates the exit
      code (SHA256_COLLISION_IS_BLOCKER = False).
------------------------------------------------------------------------------
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths (R4)
# --------------------------------------------------------------------------- #
REPO = Path(__file__).resolve().parent.parent
NORM_DIR = REPO / "data" / "processed" / "normalized"
OUT_DIR = REPO / "data" / "processed" / "validated"
QUARANTINE_PATH = OUT_DIR / "quarantine.jsonl"
REPORT_PATH = OUT_DIR / "validation_report.json"
# L1: passing records are materialized here, one file per input file, split into
# entities/ and relationships/ subdirs. This is what 05_load.py reads — it loads
# what is on disk, with no knowledge of quarantine and no subtraction.
VALIDATED_ENT_DIR = OUT_DIR / "entities"
VALIDATED_REL_DIR = OUT_DIR / "relationships"

# --------------------------------------------------------------------------- #
# Inputs (R8)
# --------------------------------------------------------------------------- #
# Entity tables = normalized/*.jsonl carrying entity_type, minus these two.
#   normalization_log.jsonl carries entity_type on log rows (a trap — measured
#   5002 rows on 2026-07-17); review_queue.jsonl is 03's human queue (R3).
EXCLUDED_FILES = {"normalization_log.jsonl", "review_queue.jsonl", "crosswalk.jsonl"}
# Relationship tables carry relationship_type. review_queue.jsonl also carries a
# few relationship_type rows and is excluded here too (never read for validation).
RELATIONSHIP_FILES = {
    "csv_relationships.jsonl",
    "pdf_relationships.jsonl",
    "rawfile_relationships.jsonl",
    "rawfiles_pxd_relationships.jsonl",
    "advisory_relationships.jsonl",   # KI-8: FLAGS edges (Advisory -> RawDataFile)
}

# --------------------------------------------------------------------------- #
# Universal properties
# --------------------------------------------------------------------------- #
PROVENANCE_PROPS = (
    "source_type",
    "confidence",
    "extracted_at",
    "evidence_note",
    "source_id",
    "schema_version",
)
SCHEMA_VERSION = "v1.0"

# Value spaces — R6: out-of-enum is COUNTED, never fatal.
SOURCE_TYPE_ENUM = {
    "api", "csv", "manual_annotation", "fisher_py", "merged_csv_foxden", "llm_extraction",
    "merged_csv_llm",  # E1: same-fact CSV+PDF agreement (the 74 USES_INSTRUMENT), merged edge
    "graph_derived",   # KI-8: Advisory nodes + FLAGS edges computed by the pipeline from its
                       # own data, not extracted from a source document.
}
CONFIDENCE_ENUM = {"high", "medium", "low"}

# Format rules from the schema Validation Rules section.
DOI_RE = re.compile(r"^10\.\d{4,}/.+")
ORCID_RE = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")

# KI-8 REMEDIATED (2026-07-20): RawDataFile identity is now the composite
# rawfile:{filename}:{sha16}, uniqueness enforced on `identifier`. sha256_hash is a
# non-unique property, so byte-identical files across distinct identifiers are NO
# LONGER a load blocker — they are an expected, reported fact. The former blocker
# becomes a COUNTED, non-fatal category (byte_identical_sets), one entry per hash
# shared by >1 node, mirroring the Advisory sets 03 emits.
SHA256_COLLISION_IS_BLOCKER = False

# --------------------------------------------------------------------------- #
# THE REQUIRED-SET (R5) — one entry per entity_type present on disk.
#   hard              : absence quarantines (reason missing_required:<field>)
#   when_present      : {field: regex} — quarantine only if present AND malformed
#   coverage_gap      : absence -> counted 'missing_coverage:<field>', NOT fatal (④a/b/c/⑦)
#   uncanonicalized   : absence -> counted 'uncanonicalized', NOT fatal (R2)
#   unique_on         : uniqueness key OTHER than identifier (RawDataFile -> sha256_hash)
#   id_not_unique     : True -> skip identifier-uniqueness check (RawDataFile, R7)
# `identifier` + the six provenance props are universal and checked for every type.
# --------------------------------------------------------------------------- #
REQUIRED_SET: dict[str, dict] = {
    "Publication": {
        "hard": ["maglab_id", "title", "publication_year", "resource_type", "is_ground_truth"],
        "when_present": {"doi": DOI_RE},            # ① "M when present" — malformed fails, absent passes
        "coverage_gap": ["publisher"],               # ④a
    },
    "Researcher": {
        "hard": ["name_full", "family_name"],
        "when_present": {"orcid": ORCID_RE},
    },
    "Institution": {"hard": ["name"]},
    "Journal": {
        "hard": ["name"],
        # issn is "M when present" but the schema states no malformed-issn rule,
        # so absence passes and there is nothing to check when present.
    },
    "Funder": {"hard": ["name"]},
    "Facility": {"hard": ["name"]},
    "Instrument": {
        "hard": [],
        "uncanonicalized": ["canonical_name"],       # R2 / KI-7
    },
    "Dataset": {"hard": ["repository", "accession", "source_url"]},   # ⑤ source_url (was 'url')
    "Sample": {
        "hard": [],
        "coverage_gap": ["canonical_name"],          # ⑦
    },
    "Software": {"hard": ["canonical_name"]},         # category is O (T4b)
    "RawDataFile": {
        "hard": ["filename", "sha256_hash"],
        "coverage_gap": ["operator_initials", "date_acquired"],   # ④b / ④c
        # KI-8 remediated: identity is now the composite rawfile:{filename}:{sha16},
        # so `identifier` IS globally unique and is uniqueness-checked like every
        # other type. sha256_hash is a non-unique property (byte-identical sets are
        # expected and reported, not a uniqueness violation).
    },
    "Advisory": {
        # KI-8: graph-derived metadata about a byte-identical content set. Not tied
        # to a Publication (no node type is required to be). source_type graph_derived.
        "hard": ["advisory_type", "sha256_hash"],
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_field(record: dict, name: str):
    """Identity + provenance live at top level; domain props live under 'properties'."""
    if name == "identifier" or name in PROVENANCE_PROPS or name == "entity_type":
        return record.get(name, _MISSING)
    return (record.get("properties") or {}).get(name, _MISSING)


_MISSING = object()


def _absent(value) -> bool:
    return value is _MISSING or value is None or value == ""


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            yield lineno, json.loads(line)


def discover_files():
    """Return (entity_files, relationship_files) by inspecting the first typed row."""
    entity_files, rel_files = [], []
    for path in sorted(NORM_DIR.glob("*.jsonl")):
        if path.name in EXCLUDED_FILES:
            continue
        has_entity = has_rel = False
        for _, obj in iter_jsonl(path):
            if "entity_type" in obj:
                has_entity = True
            if "relationship_type" in obj:
                has_rel = True
            break  # one row is enough to classify
        if has_entity:
            entity_files.append(path)
        elif has_rel and path.name in RELATIONSHIP_FILES:
            rel_files.append(path)
    return entity_files, rel_files


# --------------------------------------------------------------------------- #
# Node validation
# --------------------------------------------------------------------------- #
def validate_node(record: dict):
    """Return (fatal_reasons, counted_flags) for one entity record."""
    fatal: list[str] = []
    counted: list[str] = []

    etype = record.get("entity_type")
    spec = REQUIRED_SET.get(etype)

    # Universal: identifier present.
    if _absent(get_field(record, "identifier")):
        fatal.append("missing_required:identifier")

    # Universal: all six provenance props present (R6 — presence is fatal).
    for prop in PROVENANCE_PROPS:
        if _absent(get_field(record, prop)):
            fatal.append(f"missing_provenance:{prop}")

    # schema_version must equal v1.0.
    if get_field(record, "schema_version") not in (_MISSING, None) and \
            record.get("schema_version") != SCHEMA_VERSION:
        fatal.append(f"bad_schema_version:{record.get('schema_version')}")

    # R6: provenance VALUE out of enum -> counted, not fatal.
    st = record.get("source_type")
    if st is not None and st not in SOURCE_TYPE_ENUM:
        counted.append(f"provenance_out_of_enum:source_type={st}")
    conf = record.get("confidence")
    if conf is not None and conf not in CONFIDENCE_ENUM:
        counted.append(f"provenance_out_of_enum:confidence={conf}")

    if spec is None:
        # Unknown entity_type — not in the required-set; flag, don't guess.
        counted.append(f"unknown_entity_type:{etype}")
        return fatal, counted

    # Hard-required properties.
    for field in spec.get("hard", []):
        if _absent(get_field(record, field)):
            fatal.append(f"missing_required:{field}")

    # "M when present" — malformed only.
    for field, rx in spec.get("when_present", {}).items():
        val = get_field(record, field)
        if not _absent(val) and not rx.match(str(val)):
            fatal.append(f"malformed:{field}={val}")

    # Coverage-gap fields (④a/b/c/⑦) — counted, non-fatal.
    for field in spec.get("coverage_gap", []):
        if _absent(get_field(record, field)):
            counted.append(f"missing_coverage:{field}")

    # Uncanonicalized (R2) — counted, non-fatal.
    for field in spec.get("uncanonicalized", []):
        if _absent(get_field(record, field)):
            counted.append("uncanonicalized")

    return fatal, counted


# --------------------------------------------------------------------------- #
# Edge validation
# --------------------------------------------------------------------------- #
def validate_edge(record: dict, surviving_ids: set, all_node_ids: set):
    """Endpoints are checked against SURVIVING nodes (R10): an edge whose endpoint
    04 just quarantined cannot load, so passing it would defeat 04. Two distinct
    diagnoses, same effect on 05, opposite fix:

      dangling_endpoint      — endpoint exists in NO entity file. Upstream data bug.
      orphaned_by_quarantine — endpoint exists but FAILED validation this run. Fix
                               the node and the edge returns.

    ONE LEVEL, not recursive: quarantining an edge never removes a node, so there is
    no cascade past this first hop — an orphaned edge cannot orphan anything further.
    """
    fatal: list[str] = []
    for prop in PROVENANCE_PROPS:
        if _absent(record.get(prop, _MISSING)):
            fatal.append(f"missing_provenance:{prop}")
    if record.get("schema_version") != SCHEMA_VERSION:
        fatal.append(f"bad_schema_version:{record.get('schema_version')}")
    for endpoint_key in ("subject_id", "object_id"):
        endpoint = record.get(endpoint_key)
        if endpoint not in surviving_ids:
            if endpoint in all_node_ids:
                fatal.append(f"orphaned_by_quarantine:{endpoint_key}={endpoint}")
            else:
                fatal.append(f"dangling_endpoint:{endpoint_key}={endpoint}")
    return fatal


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="Validate normalized SciKG data (stage 04).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Compute and print the report but write no files.")
    args = ap.parse_args()

    entity_files, rel_files = discover_files()

    quarantine: list[dict] = []
    passed = 0
    by_type = defaultdict(lambda: Counter())
    counted_totals = Counter()
    # missing_coverage is broken out PER FIELD, never summed: publisher (④a),
    # operator_initials (④b), date_acquired (④c) and Sample.canonical_name (⑦)
    # have four different causes and one total would hide all four.
    missing_coverage_by_field = Counter()
    prov_out_of_enum_detail = Counter()
    quarantine_reasons = Counter()

    # ---- Pass 1: entities + build the identifier universe --------------- #
    # all_node_ids  = every entity identifier, pass or fail (for the dangling vs
    #                 orphaned distinction). surviving_ids = passed nodes only —
    #                 the set an edge endpoint must be in to load (R10).
    all_node_ids: set = set()
    surviving_ids: set = set()
    identifier_owner = defaultdict(list)     # identifier -> [(type, file)]  (non-RawDataFile)
    sha_owner = defaultdict(list)            # sha256_hash -> [identifier]   (RawDataFile)
    # L1: passing records are MATERIALIZED to validated/, one file per input file,
    # so 05 loads what it reads instead of recomputing "what passed". Keyed by
    # source basename to preserve the input layout the way 03 does.
    passing_entities = defaultdict(list)     # source basename -> [record, ...]
    passing_edges = defaultdict(list)        # source basename -> [record, ...]

    for path in entity_files:
        for _, rec in iter_jsonl(path):
            etype = rec.get("entity_type")
            ident = rec.get("identifier")
            if ident is not None:
                all_node_ids.add(ident)
            spec = REQUIRED_SET.get(etype, {})
            if ident is not None and not spec.get("id_not_unique"):
                identifier_owner[ident].append((etype, path.name))
            if etype == "RawDataFile":
                sha = (rec.get("properties") or {}).get("sha256_hash")
                if sha is not None:
                    sha_owner[sha].append(ident)

            fatal, counted = validate_node(rec)
            for flag in counted:
                cat = flag.split(":", 1)[0]
                by_type[etype][cat] += 1
                if cat == "missing_coverage":
                    missing_coverage_by_field[flag.split(":", 1)[1]] += 1
                elif cat == "provenance_out_of_enum":
                    prov_out_of_enum_detail[flag.split(":", 1)[1]] += 1
                else:
                    counted_totals[cat] += 1
            if fatal:
                rec_out = dict(rec)
                rec_out["_quarantine_reasons"] = fatal
                rec_out["_source_file"] = path.name
                quarantine.append(rec_out)
                by_type[etype]["quarantined"] += 1
                for r in fatal:
                    quarantine_reasons[r.split(":", 1)[0]] += 1
            else:
                passed += 1
                by_type[etype]["passed"] += 1
                passing_entities[path.name].append(rec)
                if ident is not None:
                    surviving_ids.add(ident)   # only passed nodes can anchor an edge (R10)

    # ---- Uniqueness (R7) ------------------------------------------------- #
    dup_identifiers = {i: [o for o in owners] for i, owners in identifier_owner.items()
                       if len(owners) > 1}
    counted_totals["duplicate_identifier"] += len(dup_identifiers)

    # ---- Counted (KI-8 remediated): byte-identical content sets ---------- #
    # COUNT-FREE, held to the T3 standard: one entry per sha256_hash shared by more
    # than one RawDataFile node. Post-composite these are EXPECTED (distinct files,
    # same content) — 03 emits an Advisory node per set. No longer a blocker.
    byte_identical_sets = [
        {"sha256_hash": sha, "identifiers": idents}
        for sha, idents in sha_owner.items() if len(idents) > 1
    ]

    # ---- Pass 2: edges (endpoints checked vs SURVIVING nodes, R10) ------- #
    edges_total = 0
    edges_dangling = 0            # endpoint exists nowhere — upstream data bug
    edges_orphaned = 0           # endpoint exists but was quarantined this run
    # E2 (2026-07-17): per-triple duplicate detector. 03 dedups edges WITHIN a
    # file; a (type, subject, object) triple repeated ACROSS files is invisible to
    # it and to every other 04 check, yet 05's MERGE (a)-[:TYPE]->(b) collapses it
    # (last SET wins) and destroys one edge's provenance silently. Not malformed —
    # a duplicate triple is a fact 05 must DECIDE about (merge / keep) — so this is
    # a COUNTED category, never a quarantine.
    edge_triple_counts = Counter()
    for path in rel_files:
        for _, rec in iter_jsonl(path):
            edges_total += 1
            edge_triple_counts[(rec.get("relationship_type"),
                                rec.get("subject_id"), rec.get("object_id"))] += 1
            fatal = validate_edge(rec, surviving_ids, all_node_ids)
            if fatal:
                rec_out = dict(rec)
                rec_out["_quarantine_reasons"] = fatal
                rec_out["_source_file"] = path.name
                quarantine.append(rec_out)
                for r in fatal:
                    quarantine_reasons[r.split(":", 1)[0]] += 1
                if any(r.startswith("dangling_endpoint") for r in fatal):
                    edges_dangling += 1
                if any(r.startswith("orphaned_by_quarantine") for r in fatal):
                    edges_orphaned += 1
            else:
                passed += 1
                passing_edges[path.name].append(rec)

    # E2: duplicate (relationship_type, subject_id, object_id) triples — counted.
    dup_triples = {k: v for k, v in edge_triple_counts.items() if v > 1}
    dup_triple_by_type = Counter(k[0] for k in dup_triples)

    # ---- Report ---------------------------------------------------------- #
    report = {
        "generated_at": now_iso(),
        # L5 gate: 05_load.py refuses to load unless this is True. It is the
        # materialized equivalent of "04 exited 0" — clean iff nothing quarantined.
        # KI-8 remediated: byte-identical sets are counted, not a blocker.
        "load_cleared": (len(quarantine) == 0),
        "inputs": {
            "entity_files": [p.name for p in entity_files],
            "relationship_files": [p.name for p in rel_files],
            "excluded_files": sorted(EXCLUDED_FILES),
            "identifier_universe_all_nodes": len(all_node_ids),
            "identifier_universe_surviving": len(surviving_ids),
        },
        "passed": passed,
        "quarantined": len(quarantine),
        "quarantined_by_reason": dict(quarantine_reasons),
        "by_entity_type": {t: dict(c) for t, c in sorted(by_type.items())},
        "counted_categories": {
            "note": "Visible, counted, NON-fatal (R2/R6/R7). Not quarantined.",
            "totals": dict(counted_totals),
            "missing_coverage_by_field": dict(missing_coverage_by_field),
            "provenance_out_of_enum": dict(prov_out_of_enum_detail),
            "duplicate_identifiers": {i: owners for i, owners in list(dup_identifiers.items())[:50]},
            # KI-8 remediated: one entry per sha256_hash shared by >1 RawDataFile.
            # Expected post-composite (distinct files, same content); 03 emits an
            # Advisory node per set. COUNTED, non-fatal.
            "byte_identical_sets_count": len(byte_identical_sets),
            "byte_identical_sets": byte_identical_sets,
        },
        "edges": {
            "total": edges_total,
            "dangling_endpoint": edges_dangling,
            "orphaned_by_quarantine": edges_orphaned,
            # E2: counted, NOT fatal. Number of (type, subject, object) triples that
            # appear more than once (cross-file agreement 05 must decide about).
            "duplicate_edge_triple": len(dup_triples),
            "duplicate_edge_triple_by_type": dict(dup_triple_by_type),
        },
        "blockers": {
            "note": ("KI-8 remediated 2026-07-20: RawDataFile identity is the composite "
                     "rawfile:{filename}:{sha16}; uniqueness on identifier. sha256_hash "
                     "collisions are no longer a blocker — see counted_categories."
                     "byte_identical_sets."),
            # Kept for shape compatibility with 05's L5 gate reader; always empty now.
            "sha256_hash_collisions": [],
        },
    }

    blocker_count = 0  # KI-8 remediated: byte-identical sets no longer block.
    print(f"[04_validate] passed={passed} quarantined={len(quarantine)} "
          f"byte_identical_sets={len(byte_identical_sets)} "
          f"uncanonicalized={counted_totals.get('uncanonicalized', 0)}")
    print(f"[04_validate] missing_coverage_by_field={dict(missing_coverage_by_field)}")
    if prov_out_of_enum_detail:
        print(f"[04_validate] provenance_out_of_enum={dict(prov_out_of_enum_detail)}")
    print(f"[04_validate] edges: total={edges_total} dangling_endpoint={edges_dangling} "
          f"orphaned_by_quarantine={edges_orphaned} "
          f"duplicate_edge_triple={len(dup_triples)} {dict(dup_triple_by_type)}")
    if quarantine_reasons:
        print(f"[04_validate] quarantine by reason: {dict(quarantine_reasons)}")

    if not args.dry_run:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        with QUARANTINE_PATH.open("w", encoding="utf-8") as fh:
            for rec in quarantine:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        with REPORT_PATH.open("w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)
        # L1: materialize the passing records, one file per input file, in the
        # entities/ and relationships/ layout 05 reads. Clear stale files first so
        # a re-run never leaves a removed input's records behind.
        for subdir, buckets in ((VALIDATED_ENT_DIR, passing_entities),
                                (VALIDATED_REL_DIR, passing_edges)):
            subdir.mkdir(parents=True, exist_ok=True)
            for stale in subdir.glob("*.jsonl"):
                stale.unlink()
            for name, recs in buckets.items():
                with (subdir / name).open("w", encoding="utf-8") as fh:
                    for rec in recs:
                        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        n_ent = sum(len(v) for v in passing_entities.values())
        n_rel = sum(len(v) for v in passing_edges.values())
        print(f"[04_validate] wrote {QUARANTINE_PATH.relative_to(REPO)}, "
              f"{REPORT_PATH.relative_to(REPO)}, and "
              f"validated/entities ({n_ent} recs) + validated/relationships ({n_rel} recs)")
    else:
        print("[04_validate] --dry-run: no files written")

    # ---- Exit code (R1) -------------------------------------------------- #
    fail = bool(quarantine) or (SHA256_COLLISION_IS_BLOCKER and blocker_count > 0)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
