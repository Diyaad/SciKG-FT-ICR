#!/usr/bin/env python3
"""
05_load.py — load validated SciKG data into Neo4j (the final pipeline stage).

Reads `data/processed/validated/` (04's materialized passing records) and MERGEs
them into Neo4j via `scripts/db.py`. It NEVER reads normalized/ and never subtracts
the quarantine set — it loads exactly what 04 wrote, per the L1 input contract.

    reads   data/processed/validated/validation_report.json   (the L5 gate)
            data/processed/validated/entities/*.jsonl          (nodes)
            data/processed/validated/relationships/*.jsonl     (edges)
    writes  Neo4j (constraints + nodes + edges) via scripts/db.py

------------------------------------------------------------------------------
RULINGS THIS FILE ENCODES (Diya, pre-build report R4 + L1–L6, 2026-07-17)

  L1  Input is validated/, materialized by 04. Load what is on disk; no knowledge
      of quarantine, no computation of "what passed."
  L2  MERGE key is `identifier` for EVERY node type, INCLUDING RawDataFile. KI-8
      remediated 2026-07-20: RawDataFile identity is now the composite
      rawfile:{filename}:{sha16}, and the uniqueness CONSTRAINT is on `identifier`
      too (no longer sha256_hash). MERGE key and uniqueness key are the same key for
      every type. Byte-identical files (KI-8's 21) carry DIFFERENT composites, so
      they MERGE to distinct nodes and the constraint accepts them; a re-ingested
      identical file (KI-1) shares its composite and MERGEs to one node. See
      SCIKG_SCHEMA.md "MERGE key vs uniqueness constraint".
  L3  05 CREATEs the constraints (CREATE CONSTRAINT ... IF NOT EXISTS) BEFORE
      loading, so a violation fails fast at setup, not 900 nodes in. db.py stays a
      connection wrapper. All 16 constraints incl. the 5 PLANNED types (harmless at
      0 records, self-documenting).
  L5  05 REFUSES to load unless 04's report says `load_cleared: true`. That is the
      materialized equivalent of "04 exited 0". KI-8 remediated 2026-07-20: byte-
      identical sets are counted, not a blocker, so load_cleared reflects the
      quarantine set alone.
  L6  Batched UNWIND, BATCH_SIZE below. Batching is for TRANSACTION BOUNDARIES, not
      memory (4,888 nodes fit in memory trivially). Re-run safety: MERGE is
      idempotent, and for edges the MERGE pattern (a)-[:REL]->(b) matches 03's edge
      dedup key EXACTLY — (relationship_type, subject, object) — so a re-run creates
      no duplicate node OR edge; it only re-SETs properties.

  CREDENTIALS: obtained solely via db.connect() -> db.py's load_dotenv()/os.environ.
  This file never reads, logs, or reports .env, the URI, the user, or any value.
  A connection failure is reported as `Connection failed: <driver error>` only.
------------------------------------------------------------------------------
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import db  # scripts/db.py — connection layer ONLY (connect / run_query / close)

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
REPO = Path(__file__).resolve().parent.parent
VALIDATED = REPO / "data" / "processed" / "validated"
ENT_DIR = VALIDATED / "entities"
REL_DIR = VALIDATED / "relationships"
REPORT_PATH = VALIDATED / "validation_report.json"

# L6: transaction-boundary size, not a memory bound. Small enough to keep each
# Aura transaction well within limits and to give per-batch failure isolation;
# large enough to avoid per-row round trips. One UNWIND = one auto-commit txn.
BATCH_SIZE = 1000

# --------------------------------------------------------------------------- #
# Allowlists — labels and relationship types reach the query ONLY from these
# constants (never interpolated from record data unchecked), so a stray or
# PLANNED type cannot be minted. A record whose type is absent here aborts 05.
# --------------------------------------------------------------------------- #
NODE_LABELS = {
    "Publication", "Researcher", "Institution", "Journal", "Funder", "Facility",
    "Instrument", "Dataset", "Sample", "Software", "RawDataFile",
    "Advisory",   # KI-8: graph-derived byte-identical-content sets (03 Pass 5.5)
    # PLANNED (0 records today) — accepted so a future population loads cleanly:
    "Grant", "Method", "Protein", "Organism", "Modification",
}
# The 13 Active edge types. PLANNED/PENDING types (ANALYZED_IN, AFFILIATED_WITH,
# AWARDED_BY, CITES, USES_METHOD, ANALYZES_SAMPLE, ANALYZES_PROTEIN,
# INVOLVES_ORGANISM, STUDIES_PTM) are intentionally NOT here: if one ever appears
# in validated/, 05 aborts rather than load an unruled edge.
REL_TYPES = {
    "AUTHORED_BY", "PUBLISHED_IN", "FUNDED_BY", "CONDUCTED_AT", "INVOLVES_INSTITUTION",
    "USES_INSTRUMENT", "HAS_DATASET", "USES_SOFTWARE", "COLLECTED_ON", "OPERATED_BY",
    "CONTAINS_SAMPLE", "ACQUIRED_WITH", "DERIVED_FROM",
    "FLAGS",   # KI-8: Advisory -> RawDataFile (byte-identical set membership)
}

PROVENANCE_PROPS = (
    "source_type", "confidence", "extracted_at", "evidence_note", "source_id",
    "schema_version",
)

# L3: all constraints, verbatim from SCIKG_SCHEMA.md, as IF NOT EXISTS. Created
# before any load. (name, label, property)
IDENTIFIER_CONSTRAINTS = [
    ("publication_identifier", "Publication", "identifier"),
    ("researcher_identifier", "Researcher", "identifier"),
    ("institution_identifier", "Institution", "identifier"),
    ("journal_identifier", "Journal", "identifier"),
    ("grant_identifier", "Grant", "identifier"),
    ("funder_identifier", "Funder", "identifier"),
    ("facility_identifier", "Facility", "identifier"),
    ("instrument_identifier", "Instrument", "identifier"),
    ("dataset_identifier", "Dataset", "identifier"),
    ("method_identifier", "Method", "identifier"),
    ("sample_identifier", "Sample", "identifier"),
    ("protein_identifier", "Protein", "identifier"),
    ("organism_identifier", "Organism", "identifier"),
    ("modification_identifier", "Modification", "identifier"),
    ("software_identifier", "Software", "identifier"),
    ("advisory_identifier", "Advisory", "identifier"),   # KI-8 Advisory nodes
]
# RawDataFile: KI-8 remediated 2026-07-20. Identity is now the composite
# rawfile:{filename}:{sha16}, so uniqueness is on `identifier` like every other
# type; sha256_hash is a non-unique property. (Was: sha256_hash IS UNIQUE.)
RAWFILE_CONSTRAINT = ("rawfile_identifier", "RawDataFile", "identifier")


def constraint_statements():
    stmts = []
    for name, label, prop in IDENTIFIER_CONSTRAINTS + [RAWFILE_CONSTRAINT]:
        stmts.append(
            f"CREATE CONSTRAINT {name} IF NOT EXISTS "
            f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
        )
    return stmts


# --------------------------------------------------------------------------- #
# Reading + shaping
# --------------------------------------------------------------------------- #
def _iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def _clean(mapping: dict) -> dict:
    """Drop null/empty values — Neo4j has no null property; absent == no value.
    (psi_ms_id=null, category=null, publisher-absent, etc. become absent props.)"""
    return {k: v for k, v in mapping.items() if v is not None and v != ""}


def _node_props(rec: dict) -> dict:
    """Flat, Neo4j-safe property map: domain properties + the six provenance props.
    `identifier` is the MERGE key and is set by MERGE, so it is not duplicated here."""
    props = dict(rec.get("properties") or {})
    for p in PROVENANCE_PROPS:
        props[p] = rec.get(p)
    return _clean(props)


def _edge_props(rec: dict) -> dict:
    props = dict(rec.get("properties") or {})
    for p in PROVENANCE_PROPS:
        props[p] = rec.get(p)
    return _clean(props)


def read_nodes():
    """label -> [ {id, props}, ... ], grouped across ALL entity files (Dataset,
    Instrument, Software each span two files — L1 preserves that; we regroup by label)."""
    by_label = defaultdict(list)
    for path in sorted(ENT_DIR.glob("*.jsonl")):
        for rec in _iter_jsonl(path):
            label = rec.get("entity_type")
            if label not in NODE_LABELS:
                raise SystemExit(f"ABORT: unknown node label {label!r} in {path.name} "
                                 f"(not in NODE_LABELS allowlist)")
            ident = rec.get("identifier")
            if not ident:
                raise SystemExit(f"ABORT: node with no identifier in {path.name}")
            by_label[label].append({"id": ident, "props": _node_props(rec)})
    return by_label


def read_edges():
    """(subj_label, obj_label, rel_type) -> [ {s, o, props}, ... ]."""
    by_group = defaultdict(list)
    for path in sorted(REL_DIR.glob("*.jsonl")):
        for rec in _iter_jsonl(path):
            rt = rec.get("relationship_type")
            if rt not in REL_TYPES:
                raise SystemExit(f"ABORT: relationship type {rt!r} in {path.name} is not "
                                 f"an Active type (PLANNED/PENDING must not load)")
            sl, ol = rec.get("subject_type"), rec.get("object_type")
            if sl not in NODE_LABELS or ol not in NODE_LABELS:
                raise SystemExit(f"ABORT: edge {rt} has unknown endpoint label(s) "
                                 f"{sl!r}/{ol!r} in {path.name}")
            by_group[(sl, ol, rt)].append(
                {"s": rec.get("subject_id"), "o": rec.get("object_id"), "props": _edge_props(rec)}
            )
    return by_group


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


# --------------------------------------------------------------------------- #
# Writing (batched, with counters)
# --------------------------------------------------------------------------- #
def _run_write(driver, cypher, rows):
    """One auto-commit transaction; returns (nodes_created, rels_created, props_set)."""
    with driver.session() as session:
        summary = session.run(cypher, rows=rows).consume()
        c = summary.counters
        return c.nodes_created, c.relationships_created, c.properties_set


def load_nodes(driver, by_label):
    print("[05_load] nodes:")
    tot_created = tot_seen = 0
    for label in sorted(by_label):
        rows = by_label[label]
        # Label is from the allowlist, never from unchecked input.
        cypher = f"UNWIND $rows AS row MERGE (n:{label} {{identifier: row.id}}) SET n += row.props"
        created = 0
        for batch in _chunks(rows, BATCH_SIZE):
            nc, _, _ = _run_write(driver, cypher, batch)
            created += nc
        tot_created += created
        tot_seen += len(rows)
        print(f"    {label:14s} {len(rows):5d} merged ({created} created, {len(rows) - created} matched)")
    print(f"  nodes total: {tot_seen} merged, {tot_created} newly created")


def load_edges(driver, by_group):
    print("[05_load] edges:")
    tot_created = tot_seen = 0
    for (sl, ol, rt) in sorted(by_group):
        rows = by_group[(sl, ol, rt)]
        cypher = (
            f"UNWIND $rows AS row "
            f"MATCH (a:{sl} {{identifier: row.s}}) "
            f"MATCH (b:{ol} {{identifier: row.o}}) "
            f"MERGE (a)-[r:{rt}]->(b) SET r += row.props"
        )
        created = 0
        for batch in _chunks(rows, BATCH_SIZE):
            _, rc, _ = _run_write(driver, cypher, batch)
            created += rc
        tot_created += created
        tot_seen += len(rows)
        print(f"    {rt:22s} {sl}->{ol}: {len(rows):5d} merged ({created} created)")
    print(f"  edges total: {tot_seen} merged, {tot_created} newly created")


def create_constraints(driver):
    print("[05_load] constraints (CREATE ... IF NOT EXISTS, before load):")
    for stmt in constraint_statements():
        db.run_query(driver, stmt)
    print(f"    {len(constraint_statements())} constraints ensured")


# --------------------------------------------------------------------------- #
# Gate (L5)
# --------------------------------------------------------------------------- #
def check_gate():
    """Refuse the load unless 04's report exists AND load_cleared is True."""
    if not REPORT_PATH.exists():
        raise SystemExit(f"ABORT: {REPORT_PATH.relative_to(REPO)} not found — run "
                         f"04_validate.py first.")
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    if report.get("load_cleared") is not True:
        blockers = len((report.get("blockers") or {}).get("sha256_hash_collisions", []))
        quar = report.get("quarantined", "?")
        raise SystemExit(
            "ABORT (L5 gate): 04 did not clear the load "
            f"(load_cleared={report.get('load_cleared')!r}; quarantined={quar}; "
            f"sha256 blockers={blockers}). Resolve KI-8 / quarantine and re-run 04. "
            "05 does not load while 04 is non-clean."
        )
    return report


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="Load validated SciKG data into Neo4j (stage 05).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Read validated/ + gate + print the plan. Does NOT connect to Neo4j.")
    args = ap.parse_args()

    report = check_gate()  # L5 — aborts before any connection if not clear
    print(f"[05_load] gate OK: load_cleared=True "
          f"(passed={report.get('passed')}, quarantined={report.get('quarantined')})")

    by_label = read_nodes()
    by_group = read_edges()
    n_nodes = sum(len(v) for v in by_label.values())
    n_edges = sum(len(v) for v in by_group.values())

    if args.dry_run:
        print(f"[05_load] --dry-run: would create {len(constraint_statements())} constraints, "
              f"MERGE {n_nodes} nodes across {len(by_label)} labels and {n_edges} edges "
              f"across {len(by_group)} (label,label,type) groups. No connection made.")
        return 0

    driver = None
    try:
        driver = db.connect()
        create_constraints(driver)
        load_nodes(driver, by_label)
        load_edges(driver, by_group)
        print(f"[05_load] DONE: {n_nodes} nodes, {n_edges} edges loaded (idempotent; safe to re-run).")
        return 0
    except Exception as e:  # never surfaces credentials/URI — driver error text only
        print(f"Connection failed: {e}")
        return 1
    finally:
        db.close(driver)


if __name__ == "__main__":
    sys.exit(main())
