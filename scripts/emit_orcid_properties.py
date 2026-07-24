"""
emit_orcid_properties.py — stage Researcher ORCID property updates for review.

DRY-RUN BY DEFAULT. Writes only to data/processed/review/. Nothing reaches the
pipeline inputs (data/processed/entities/) and nothing touches Neo4j.

Reads the staged candidates produced by scripts/analyze_orcid_coverage.py and
applies the eligibility ruling of 2026-07-23:

  EXCLUDE  (a) FUSED nodes — a node holding two people cannot carry one ORCID
           (b) reverse-error nodes — 2+ distinct ORCIDs on one node
           (c) MATCH-MULTIPLE / UNMATCHED classes
  DEDUPE   one value per node; papers disagreeing on ORCID is a CONFLICT and is
           excluded, never resolved by picking one. Where the same ORCID appears
           both authenticated and publisher-asserted, authenticated wins and the
           split is recorded.

ORCIDs are only ever CrossRef-returned values (author[].ORCID). Nothing here
constructs, infers, or repairs an ORCID.

Usage:
    python3 scripts/emit_orcid_properties.py            # dry-run -> review dir
    python3 scripts/emit_orcid_properties.py --report   # print tables only
"""

import argparse
import collections
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REVIEW_DIR = os.path.join(REPO, "data", "processed", "review")
CANDIDATES = os.path.join(REVIEW_DIR, "orcid_candidates.jsonl")
OUT_RECORDS = os.path.join(REVIEW_DIR, "proposed_researcher_orcid_entities.jsonl")
OUT_EXCLUSIONS = os.path.join(REVIEW_DIR, "orcid_exclusions.jsonl")

SCHEMA_VERSION = "v1.0"
ORCID_RE = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")

# A node whose name_full/family_name matches any of these is a collective or
# team rather than one person, so an ORCID cannot attach to it.
COLLECTIVE_RE = re.compile(
    r"\b(et\s*al|group|team|consortium|collaboration|laborator|network|"
    r"committee|society|institute|center|centre|working\s+group)\b",
    re.I,
)


def load_graph_researchers():
    """Return {identifier: record} for every Researcher node, with its provenance."""
    driver = db.connect()
    try:
        rows = db.run_query(
            driver,
            """
            MATCH (r:Researcher)
            RETURN r.identifier AS identifier, r.name_full AS name_full,
                   r.family_name AS family_name, r.given_name AS given_name,
                   r.source_type AS source_type, r.source_id AS source_id,
                   r.orcid AS orcid
            """,
        )
    finally:
        db.close(driver)
    return {r["identifier"]: r for r in rows}


def is_fused(node):
    """True if the node holds more than one person, or is a collective."""
    nf = node.get("name_full") or ""
    fam = node.get("family_name") or ""
    ident = node.get("identifier") or ""
    if " and " in nf or "_and_" in ident or " and " in fam:
        return "fused_two_people"
    if COLLECTIVE_RE.search(nf) or COLLECTIVE_RE.search(fam):
        return "collective_or_team"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true",
                    help="print the tables only; write no files")
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(CANDIDATES, encoding="utf-8")]
    graph = load_graph_researchers()

    exclusions = []          # {researcher_id, orcid, reason, detail}
    excl_counts = collections.Counter()
    kept_rows = []

    # ---- Step 1: eligibility ------------------------------------------ #
    for r in rows:
        rid = r.get("researcher_id")
        klass = r.get("match_class")

        if klass != "MATCH-UNIQUE":
            excl_counts["c_match_class_%s" % klass] += 1
            exclusions.append({"researcher_id": rid, "orcid": r.get("orcid"),
                               "reason": "match_class", "detail": klass,
                               "source_doi": r.get("source_doi")})
            continue

        node = graph.get(rid)
        if node is None:
            excl_counts["node_absent_from_graph"] += 1
            exclusions.append({"researcher_id": rid, "orcid": r.get("orcid"),
                               "reason": "node_absent_from_graph", "detail": None,
                               "source_doi": r.get("source_doi")})
            continue

        fused = is_fused(node)
        if fused:
            excl_counts["a_" + fused] += 1
            exclusions.append({"researcher_id": rid, "orcid": r.get("orcid"),
                               "reason": fused, "detail": node.get("name_full"),
                               "source_doi": r.get("source_doi")})
            continue

        if r.get("node_maps_to_multiple_orcids"):
            excl_counts["b_reverse_error"] += 1
            exclusions.append({"researcher_id": rid, "orcid": r.get("orcid"),
                               "reason": "reverse_error_node_carries_multiple_orcids",
                               "detail": node.get("name_full"),
                               "source_doi": r.get("source_doi")})
            continue

        orcid = (r.get("orcid") or "").strip().upper()
        if not ORCID_RE.match(orcid):
            excl_counts["malformed_orcid"] += 1
            exclusions.append({"researcher_id": rid, "orcid": r.get("orcid"),
                               "reason": "malformed_orcid", "detail": None,
                               "source_doi": r.get("source_doi")})
            continue

        kept_rows.append(r)

    # ---- Step 2: dedupe by node --------------------------------------- #
    by_node = collections.defaultdict(list)
    for r in kept_rows:
        by_node[r["researcher_id"]].append(r)

    records = []
    conflicts = 0
    auth_split = 0
    for rid, rs in sorted(by_node.items()):
        orcids = {(r["orcid"] or "").strip().upper() for r in rs}
        if len(orcids) > 1:
            # Papers disagree. Never pick one.
            conflicts += 1
            excl_counts["conflict_node_papers_disagree"] += len(rs)
            exclusions.append({"researcher_id": rid, "orcid": sorted(orcids),
                               "reason": "conflict_papers_disagree", "detail": None,
                               "source_doi": sorted({r["source_doi"] for r in rs})})
            continue

        orcid = orcids.pop()
        auth_flags = {bool(r.get("authenticated")) for r in rs}
        authenticated = True in auth_flags
        if len(auth_flags) > 1:
            auth_split += 1

        dois = sorted({r["source_doi"] for r in rs})
        node = graph[rid]

        # Corroboration across independent papers is the confidence signal here;
        # the author-verified/publisher-asserted distinction is carried by
        # orcid_authenticated, NOT folded into confidence.
        confidence = "high" if len(dois) > 1 else "medium"

        note = (
            "ORCID from CrossRef structured metadata (author[].ORCID) for "
            + ", ".join(dois)
            + ". Deterministic per-DOI API lookup, NOT text extraction and NOT "
            "inferred. Matched to this node within the bounded set of Researcher "
            "nodes already linked to that Publication by AUTHORED_BY (no global "
            "name search); match_class MATCH-UNIQUE on "
            + ("%d papers" % len(dois) if len(dois) > 1 else "1 paper")
            + ". authenticated-orcid="
            + ("true (author-verified at deposit)" if authenticated
               else "false (publisher-asserted)")
            + (" [both values seen across papers; author-verified preferred]"
               if len(auth_flags) > 1 else "")
            + "."
        )

        records.append({
            "identifier": rid,
            "entity_type": "Researcher",
            "properties": {
                # Name fields are carried so the record satisfies 04's hard
                # required-set for Researcher on its own; values are copied from
                # the node they already describe, not re-derived.
                "name_full": node.get("name_full"),
                "family_name": node.get("family_name"),
                "given_name": node.get("given_name"),
                "orcid": orcid,
                "orcid_authenticated": authenticated,
            },
            "source_type": "api",
            "confidence": confidence,
            "extracted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "evidence_note": note,
            "source_id": ["doi:" + d for d in dois] if len(dois) > 1 else "doi:" + dois[0],
            "schema_version": SCHEMA_VERSION,
        })

    # ---- report -------------------------------------------------------- #
    print("=" * 68)
    print("STEP 1 — ELIGIBILITY")
    print("=" * 68)
    print("candidate rows in file                : %d" % len(rows))
    for k in sorted(excl_counts):
        print("  excluded [%-38s] : %d" % (k, excl_counts[k]))
    print("rows surviving eligibility            : %d" % len(kept_rows))
    print()
    print("=" * 68)
    print("STEP 2 — DEDUPE BY NODE")
    print("=" * 68)
    print("distinct nodes among surviving rows   : %d" % len(by_node))
    print("  excluded, papers disagree (conflict): %d" % conflicts)
    print("  nodes with mixed authenticated flags: %d (author-verified preferred)"
          % auth_split)
    print("ELIGIBLE PROPERTY-UPDATE RECORDS      : %d" % len(records))
    print()
    auth_true = sum(1 for r in records if r["properties"]["orcid_authenticated"])
    print("  orcid_authenticated=true            : %d" % auth_true)
    print("  orcid_authenticated=false           : %d" % (len(records) - auth_true))
    conf = collections.Counter(r["confidence"] for r in records)
    print("  confidence high (2+ papers)         : %d" % conf["high"])
    print("  confidence medium (1 paper)         : %d" % conf["medium"])

    if args.report:
        return

    os.makedirs(REVIEW_DIR, exist_ok=True)
    with open(OUT_RECORDS, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with open(OUT_EXCLUSIONS, "w", encoding="utf-8") as fh:
        for e in exclusions:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    print()
    print("DRY RUN — wrote review artifacts only, nothing staged to pipeline inputs:")
    print("  %s  (%d records)" % (OUT_RECORDS, len(records)))
    print("  %s  (%d rows)" % (OUT_EXCLUSIONS, len(exclusions)))


if __name__ == "__main__":
    main()
