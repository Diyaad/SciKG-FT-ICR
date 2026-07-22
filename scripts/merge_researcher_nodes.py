#!/usr/bin/env python3
"""
merge_researcher_nodes.py — apply APPROVED researcher-fragmentation merges.

Phase 2 of the researcher de-fragmentation task. Detection (Phase 1) writes a
signed ledger; this script consumes it and, for each row a human has approved
(`apply: true`), repoints the retired (mangled) node's relationships onto the
canonical (clean-spelled) node and deletes the retired node.

    reads   data/processed/review/researcher_merge_ledger.jsonl   (the signed ledger)
    writes  Neo4j (repoint edges, delete retired nodes) via scripts/db.py
    writes  data/processed/review/researcher_merge_crosswalk.jsonl (durable record)

DRY-RUN IS THE DEFAULT. Nothing is written to the graph unless --apply is given.
Modeled on scripts/transform_pdf_datasets.py (argparse, six-prop provenance,
atomic writes) and scripts/05_load.py (db.py connection, allowlisted rel types,
MERGE idempotency, batched counters).

PORTABILITY — this script is safe to run on ANY instance (yours, David's,
Diya's). The reviewed ledger is the portable artifact: the SAME ledger + SAME
script produce the SAME approved merge set everywhere. Per-instance drift is
handled explicitly (verify-before-merge below).

HARD RULES honored (task brief + CLAUDE.md):
  - Merge ONLY rows with apply:true AND a non-null canonical_id. DISPLAY-ONLY and
    PARSE-FAIL rows have canonical_id=null and can never merge; a REVIEW row only
    merges if a human promoted it by setting apply:true (their explicit call).
  - Verify-before-merge, drift-safe (per row):
        retired absent   -> SKIP + report (this instance never had the fragment)
        canonical absent -> HALT that row + report (possible corpus drift -> Diya)
  - Repoint dynamically: enumerate the retired node's relationships from the LIVE
    graph (do not hardcode AUTHORED_BY / OPERATED_BY / ...). Each incident type is
    checked against the schema's Active REL_TYPES allowlist; an unknown type HALTS
    the row rather than silently dropping an edge.
  - No duplicate edges: MERGE (endpoint)-[:TYPE]->(canonical); ON CREATE SET carries
    the original edge's provenance without clobbering an edge canonical already has.
  - Idempotent: existence checks + MERGE mean a second run is a no-op. Proven by the
    post-run remaining-retired count (0) and a re-runnable design.
  - No git. Diya commits.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import db  # scripts/db.py — connection layer ONLY (connect / run_query / close)

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
REPO = Path(__file__).resolve().parent.parent
REVIEW_DIR = REPO / "data" / "processed" / "review"
DEFAULT_LEDGER = REVIEW_DIR / "researcher_merge_ledger.jsonl"
CROSSWALK = REVIEW_DIR / "researcher_merge_crosswalk.jsonl"

# Active relationship types that may touch a Researcher node. Sourced from
# 05_load.REL_TYPES (the schema's Active set). A relationship type incident to a
# retired node that is NOT here means the graph drifted past the schema; we HALT
# that row rather than move an edge we were not told about.
ALLOWED_REL_TYPES = {
    "AUTHORED_BY", "PUBLISHED_IN", "FUNDED_BY", "CONDUCTED_AT", "INVOLVES_INSTITUTION",
    "USES_INSTRUMENT", "HAS_DATASET", "USES_SOFTWARE", "COLLECTED_ON", "OPERATED_BY",
    "CONTAINS_SAMPLE", "ACQUIRED_WITH", "DERIVED_FROM", "FLAGS",
}

SCHEMA_VERSION = "v1.0"


def _iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def _now():
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------- #
# Ledger selection
# --------------------------------------------------------------------------- #
def approved_rows(ledger_path: Path):
    """Return (mergeable, invalid). Mergeable = apply:true with a canonical_id.
    Invalid = apply:true but no canonical_id (nonsensical; reported, never run)."""
    mergeable, invalid = [], []
    for row in _iter_jsonl(ledger_path):
        if row.get("apply") is not True:
            continue
        if not row.get("canonical_id"):
            invalid.append(row)
        else:
            mergeable.append(row)
    return mergeable, invalid


# --------------------------------------------------------------------------- #
# Graph helpers
# --------------------------------------------------------------------------- #
def node_exists(driver, identifier) -> bool:
    rows = db.run_query(
        driver, "MATCH (r:Researcher {identifier:$id}) RETURN count(r) AS c",
        {"id": identifier})
    return bool(rows and rows[0]["c"] > 0)


def researcher_count(driver) -> int:
    return db.run_query(driver, "MATCH (r:Researcher) RETURN count(r) AS c")[0]["c"]


def incident_rel_types(driver, identifier):
    """Distinct (type, outgoing) pairs incident to the retired node, from the
    LIVE graph — dynamic, not hardcoded."""
    return db.run_query(driver, """
        MATCH (r:Researcher {identifier:$id})-[rel]-(other)
        RETURN DISTINCT type(rel) AS t, (startNode(rel).identifier = $id) AS outgoing
    """, {"id": identifier})


def _run_write(driver, cypher, params):
    """One auto-commit txn; return (rels_created, props_set)."""
    with driver.session() as session:
        summary = session.run(cypher, **params).consume()
        c = summary.counters
        return c.relationships_created, c.properties_set


def repoint_type(driver, retired, canonical, rel_type, outgoing):
    """Repoint every rel of one (type, direction) from retired onto canonical.
    rel_type is interpolated ONLY after allowlist validation (05_load pattern).
    ON CREATE SET carries the original edge provenance without overwriting an
    edge canonical already has (no provenance clobber, no duplicate edge)."""
    assert rel_type in ALLOWED_REL_TYPES, f"unvalidated rel type {rel_type!r}"
    if outgoing:
        cypher = (
            f"MATCH (can:Researcher {{identifier:$c}}) "
            f"MATCH (ret:Researcher {{identifier:$r}})-[rel:`{rel_type}`]->(other) "
            f"MERGE (can)-[nr:`{rel_type}`]->(other) "
            f"ON CREATE SET nr += properties(rel)"
        )
    else:
        cypher = (
            f"MATCH (can:Researcher {{identifier:$c}}) "
            f"MATCH (other)-[rel:`{rel_type}`]->(ret:Researcher {{identifier:$r}}) "
            f"MERGE (other)-[nr:`{rel_type}`]->(can) "
            f"ON CREATE SET nr += properties(rel)"
        )
    return _run_write(driver, cypher, {"c": canonical, "r": retired})


def delete_node(driver, identifier):
    with driver.session() as session:
        summary = session.run(
            "MATCH (r:Researcher {identifier:$id}) DETACH DELETE r",
            id=identifier).consume()
        return summary.counters.nodes_deleted


def duplicate_edges_on(driver, identifier) -> int:
    """Count parallel edges (same type + direction + neighbour) on a node — must
    be 0 after a merge, since every repoint used MERGE."""
    rows = db.run_query(driver, """
        MATCH (n:Researcher {identifier:$id})-[rel]-(other)
        WITH n, other, type(rel) AS t, (startNode(rel)=n) AS outgoing, count(*) AS c
        WHERE c > 1
        RETURN coalesce(sum(c - 1), 0) AS dupes
    """, {"id": identifier})
    return rows[0]["dupes"] if rows else 0


# --------------------------------------------------------------------------- #
# Merge one approved row
# --------------------------------------------------------------------------- #
def merge_one(driver, row, apply: bool):
    retired = row["retired_id"]
    canonical = row["canonical_id"]
    result = {"retired": retired, "canonical": canonical,
              "mechanism": row.get("mechanism"), "status": None,
              "types": [], "edges_created": 0}

    ret_here = node_exists(driver, retired)
    can_here = node_exists(driver, canonical)

    if not ret_here and can_here:
        result["status"] = "SKIP_retired_absent"          # instance never had it
        return result
    if not can_here:
        result["status"] = "HALT_canonical_absent"        # corpus drift -> Diya
        return result
    if retired == canonical:
        result["status"] = "SKIP_same_node"
        return result

    types = incident_rel_types(driver, retired)
    unknown = [t["t"] for t in types if t["t"] not in ALLOWED_REL_TYPES]
    if unknown:
        result["status"] = f"HALT_unknown_rel_types:{','.join(sorted(set(unknown)))}"
        return result
    result["types"] = [(t["t"], "out" if t["outgoing"] else "in") for t in types]

    if not apply:
        result["status"] = "WOULD_MERGE"
        return result

    created = 0
    for t in types:
        rc, _ = repoint_type(driver, retired, canonical, t["t"], t["outgoing"])
        created += rc
    deleted = delete_node(driver, retired)
    dupes = duplicate_edges_on(driver, canonical)
    result["edges_created"] = created
    result["deleted"] = deleted
    result["dupes_on_canonical"] = dupes
    result["status"] = "MERGED"
    return result


def crosswalk_entry(row, result, ledger_path):
    return {
        "retired_id": row["retired_id"],
        "canonical_id": row["canonical_id"],
        "mechanism": row.get("mechanism"),
        "edges_repointed_created": result.get("edges_created"),
        "rel_types": [f"{t}:{d}" for t, d in result.get("types", [])],
        # six-prop provenance envelope (graph-derived + human-signed)
        "source_type": "graph_derived",
        "confidence": "high",
        "extracted_at": _now(),
        "evidence_note": (
            f"Researcher fragment merged: {row['retired_id']} -> {row['canonical_id']} "
            f"({row.get('mechanism')}); approved in ledger {ledger_path.name} "
            f"(classification {row.get('classification')}); "
            f"anchors: {row.get('shared_coauthor_n', 0)} co-authors, "
            f"{len(row.get('shared_inst', []))} inst, {row.get('shared_doi', 0)} DOI."
        ),
        "source_id": f"ledger:{ledger_path.name}",
        "schema_version": SCHEMA_VERSION,
    }


def append_crosswalk(entries):
    CROSSWALK.parent.mkdir(parents=True, exist_ok=True)
    with CROSSWALK.open("a", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true",
                    help="Perform the merges. WITHOUT this flag the script is a dry run "
                         "(verifies nodes, prints the plan, writes nothing).")
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER,
                    help=f"Signed ledger path (default: {DEFAULT_LEDGER}).")
    args = ap.parse_args()

    if not args.ledger.exists():
        raise SystemExit(f"ERROR ledger absent: {args.ledger}")

    mergeable, invalid = approved_rows(args.ledger)
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"=== merge_researcher_nodes [{mode}] ===")
    print(f"Ledger: {args.ledger}")
    print(f"apply:true rows -> {len(mergeable)} mergeable, {len(invalid)} invalid (apply:true "
          f"but no canonical_id — REFUSED)")
    for row in invalid:
        print(f"  REFUSED {row['retired_id']} (classification {row.get('classification')}): "
              f"apply:true set on a non-mergeable row; ignoring.")
    if not mergeable:
        print("No mergeable approved rows. Nothing to do. "
              "(Sign off by setting apply:true on MERGE-HIGH rows.)")
        return 0

    driver = None
    try:
        driver = db.connect()
        before = researcher_count(driver)
        print(f"Researcher count before: {before}")
        print()

        results, crosswalk = [], []
        for row in mergeable:
            res = merge_one(driver, row, apply=args.apply)
            results.append(res)
            tinfo = ", ".join(f"{t}:{d}" for t, d in res["types"]) or "no rels"
            print(f"  [{res['status']:>20}] {res['retired']}  ->  {res['canonical']}")
            print(f"       rels: {tinfo}"
                  + (f"  | edges_created={res['edges_created']} deleted={res.get('deleted',0)} "
                     f"dupes_on_canonical={res.get('dupes_on_canonical',0)}"
                     if res["status"] == "MERGED" else ""))
            if res["status"] == "MERGED":
                crosswalk.append(crosswalk_entry(row, res, args.ledger))

        after = researcher_count(driver)
        merged = sum(1 for r in results if r["status"] == "MERGED")
        halted = [r for r in results if r["status"].startswith("HALT")]
        skipped = [r for r in results if r["status"].startswith("SKIP")]

        print()
        print("=== summary ===")
        print(f"  merged:  {merged}")
        print(f"  skipped (retired absent / same node): {len(skipped)}")
        print(f"  HALTED  (canonical absent / drift):   {len(halted)}")
        for r in halted:
            print(f"     HALT {r['retired']} -> {r['canonical']}: {r['status']} "
                  f"(possible corpus drift — tell Diya)")
        print(f"  Researcher count: {before} -> {after}  (delta {after - before})")

        if args.apply:
            # idempotency evidence: every merged retired node is gone
            remaining = [r["retired"] for r in results
                         if r["status"] == "MERGED" and node_exists(driver, r["retired"])]
            total_dupes = sum(r.get("dupes_on_canonical", 0) for r in results
                              if r["status"] == "MERGED")
            append_crosswalk(crosswalk)
            print(f"  duplicate edges introduced: {total_dupes} (MERGE guarantees 0)")
            print(f"  retired nodes remaining after merge: {len(remaining)} (expect 0)")
            print(f"  crosswalk: appended {len(crosswalk)} rows -> {CROSSWALK}")
            print()
            print("IDEMPOTENCY: re-run this exact command; every row should report "
                  "SKIP_retired_absent and the count delta should be 0.")
            if merged:
                print()
                print("DOWNSTREAM FIGURES THAT MOVE (Diya must re-pull poster numbers):")
                print(f"  - Researcher count: {before} -> {after}")
                print("  - Co-authorship pairs / Q14 (~15,379): recompute — merged authors "
                      "consolidate pairs (esp. the Marshall–Rodgers pair).")
                print("  - Any per-researcher statistic (papers/author, top authors).")
                print()
                print("DURABILITY NOTE FOR DIYA: this crosswalk records the mapping so a merge "
                      "is auditable, but a full pipeline reload (03->04->05) would REINTRODUCE "
                      "the fragments. Real durability = wiring "
                      f"{CROSSWALK.name} into 03_normalize (your file) so retired identifiers "
                      "are rewritten to canonical at normalize time. Flagging — not editing 03.")
        else:
            print()
            print("DRY-RUN COMPLETE. No graph changes, no crosswalk written. "
                  "Re-run with --apply once the ledger is signed.")
        return 0
    except Exception as e:  # driver error text only; never surfaces credentials
        print(f"Connection failed: {e}")
        return 1
    finally:
        db.close(driver)


if __name__ == "__main__":
    sys.exit(main())
