#!/usr/bin/env python3
"""
apply_coauthor_edge_fix.py — add AUTHORED_BY edges for co-authors that were
swallowed into a fused `name_full` token (post-load reconciliation, direction B).

Phase 2 of the swallowed-co-author fix. Detection/staging wrote a dry-run ledger
(`coauthor_edge_fix_ledger.jsonl`); this script consumes it and, for each row a
human approved (`apply: true`), MERGEs the missing `(paper)-[:AUTHORED_BY]->(second
author)` edge with provenance. DRY-RUN IS THE DEFAULT — nothing is written without
--apply.

    reads   data/processed/review/coauthor_edge_fix_ledger.jsonl   (signed ledger)
    writes  Neo4j (AUTHORED_BY edges) via scripts/db.py
    writes  data/processed/review/coauthor_edge_fix_applied.jsonl  (durable log)

Modeled on scripts/merge_researcher_nodes.py (argparse, db.py, allowlist, MERGE
idempotency, verify-before-write, per-instance portability).

WHY EACH EDGE IS NOT A FABRICATION
  A fused node's identifier is its FIRST author and it accumulates ALL that
  author's papers (e.g. emmett_m_2012 = 64 papers). The co-author was swallowed
  only on the papers whose RAW CSV author string actually contains the fused token
  (Emmett: 13 of 64). The staging step grounded every ledger row in that CSV
  string, so each row is a real, source-backed authorship — never "every paper on
  the node." This script does not re-derive that; it trusts the signed ledger and
  re-verifies node/paper existence per instance.

HARD RULES honored (task brief + CLAUDE.md):
  - Apply ONLY rows with apply:true. Never auto-create a Researcher node; the
    second author must already exist (NO-NODE rows are not in this ledger).
  - Verify-before-write (drift-safe, per row): paper + second-author node exist on
    THIS instance; else SKIP + report.
  - MERGE the edge (no duplicate); ON CREATE SET provenance (never overwrite an
    existing edge's provenance). Idempotent: a second run is a no-op.
  - name_full is NOT touched (label cleanup is a separate, flagged follow-up).
  - Root cause is the author-parser in 02/03 (split "X and Y" author tokens); this
    is post-load reconciliation only. Do NOT re-run the pipeline. Git human-only.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import db  # scripts/db.py — connection layer ONLY

REPO = Path(__file__).resolve().parent.parent
REVIEW_DIR = REPO / "data" / "processed" / "review"
DEFAULT_LEDGER = REVIEW_DIR / "coauthor_edge_fix_ledger.jsonl"
APPLIED_LOG = REVIEW_DIR / "coauthor_edge_fix_applied.jsonl"

PROVENANCE_PROPS = ("source_type", "confidence", "extracted_at", "evidence_note",
                    "source_id", "schema_version")
MARSHALL = "researcher:marshall_a_2026"
RODGERS = ["researcher:rodgers_r_2026", "researcher:rodgers_r_p_x_2012"]


def _iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def _now():
    return datetime.now(timezone.utc).isoformat()


def approved_rows(path: Path):
    """apply:true rows that name both a paper and a second-author node."""
    ok, invalid = [], []
    for r in _iter_jsonl(path):
        if r.get("apply") is not True:
            continue
        if r.get("paper") and r.get("second_author_id"):
            ok.append(r)
        else:
            invalid.append(r)
    return ok, invalid


def node_exists(driver, label, identifier):
    rows = db.run_query(driver, f"MATCH (n:{label} {{identifier:$id}}) RETURN count(n) AS c",
                        {"id": identifier})
    return bool(rows and rows[0]["c"] > 0)


def edge_exists(driver, paper, second):
    rows = db.run_query(driver, """
        MATCH (p:Publication {identifier:$p})-[:AUTHORED_BY]->(s:Researcher {identifier:$s})
        RETURN count(*) AS c""", {"p": paper, "s": second})
    return bool(rows and rows[0]["c"] > 0)


def _edge_props(row):
    return {k: row.get(k) for k in PROVENANCE_PROPS if row.get(k) not in (None, "")}


def add_edge(driver, row):
    """MERGE (paper)-[:AUTHORED_BY]->(second); ON CREATE SET provenance.
    Returns rels_created (0 if it already existed)."""
    cypher = ("MATCH (p:Publication {identifier:$p}) "
              "MATCH (s:Researcher {identifier:$s}) "
              "MERGE (p)-[r:AUTHORED_BY]->(s) "
              "ON CREATE SET r += $props")
    with driver.session() as session:
        summary = session.run(cypher, p=row["paper"], s=row["second_author_id"],
                              props=_edge_props(row)).consume()
        return summary.counters.relationships_created


def marshall_rodgers_pair(driver):
    return db.run_query(driver, """
        MATCH (m:Researcher {identifier:$m})<-[:AUTHORED_BY]-(p:Publication)-[:AUTHORED_BY]->(r:Researcher)
        WHERE r.identifier IN $rod RETURN count(DISTINCT p) AS c""",
        {"m": MARSHALL, "rod": RODGERS})[0]["c"]


def duplicate_authored_by(driver, paper, second):
    rows = db.run_query(driver, """
        MATCH (p:Publication {identifier:$p})-[r:AUTHORED_BY]->(s:Researcher {identifier:$s})
        RETURN count(r) AS c""", {"p": paper, "s": second})
    return rows[0]["c"] if rows else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true",
                    help="Perform the writes. Without it, dry-run (verify + plan, no writes).")
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    args = ap.parse_args()

    if not args.ledger.exists():
        raise SystemExit(f"ERROR ledger absent: {args.ledger}")

    approved, invalid = approved_rows(args.ledger)
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"=== apply_coauthor_edge_fix [{mode}] ===")
    print(f"Ledger: {args.ledger}")
    print(f"apply:true rows -> {len(approved)} valid, {len(invalid)} invalid (missing paper/author — refused)")
    if not approved:
        print("No approved rows. Set apply:true on reviewed rows to sign off. Nothing to do.")
        return 0

    driver = None
    try:
        driver = db.connect()
        pair_before = marshall_rodgers_pair(driver)
        print(f"Marshall-Rodgers pair before: {pair_before}")
        print()

        created = skipped = existed = 0
        applied_log = []
        for r in approved:
            paper, sid = r["paper"], r["second_author_id"]
            if not node_exists(driver, "Publication", paper):
                print(f"  SKIP  paper absent: {paper}  ({sid})"); skipped += 1; continue
            if not node_exists(driver, "Researcher", sid):
                print(f"  SKIP  second-author node absent: {sid}  ({paper})"); skipped += 1; continue
            if not args.apply:
                tag = "EXISTS" if edge_exists(driver, paper, sid) else "WOULD-ADD"
                print(f"  {tag:>9}  {paper}  -AUTHORED_BY->  {sid}")
                continue
            rc = add_edge(driver, r)
            if rc:
                created += 1
                applied_log.append({**{k: r[k] for k in ("paper", "second_author_id", "fused_node")},
                                    "applied_at": _now(), "action": "AUTHORED_BY_created",
                                    "source_id": r.get("source_id")})
                print(f"  ADDED  {paper}  -AUTHORED_BY->  {sid}")
            else:
                existed += 1
                print(f"  NOOP   {paper}  -AUTHORED_BY->  {sid} (already present)")

        print("\n=== summary ===")
        if args.apply:
            # post-conditions
            dupes = sum(1 for r in approved
                        if duplicate_authored_by(driver, r["paper"], r["second_author_id"]) > 1)
            pair_after = marshall_rodgers_pair(driver)
            with APPLIED_LOG.open("a", encoding="utf-8") as f:
                for e in applied_log:
                    f.write(json.dumps(e, ensure_ascii=False) + "\n")
            print(f"  edges created: {created}   already-present (noop): {existed}   skipped: {skipped}")
            print(f"  duplicate AUTHORED_BY edges introduced: {dupes} (MERGE guarantees 0)")
            print(f"  Marshall-Rodgers pair: {pair_before} -> {pair_after}")
            print(f"  durable log: appended {len(applied_log)} rows -> {APPLIED_LOG}")
            print("  IDEMPOTENCY: re-run this command; every row should report NOOP and created=0.")
            print("\n  NOTE: root-cause fix is the author-token parser in 02/03 (split 'X and Y' "
                  "author strings) — future work for Diya/Veronika. This was post-load reconciliation.")
        else:
            print(f"  would-add: {len(approved) - skipped - existed}   skipped(drift): {skipped}")
            print("  DRY-RUN COMPLETE. No writes. Re-run with --apply once the ledger is signed.")
        return 0
    except Exception as e:
        print(f"Connection failed: {e}")
        return 1
    finally:
        db.close(driver)


if __name__ == "__main__":
    sys.exit(main())
