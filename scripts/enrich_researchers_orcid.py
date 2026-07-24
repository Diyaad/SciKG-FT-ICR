"""
enrich_researchers_orcid.py — add CrossRef ORCIDs to researchers.jsonl in place.

Adds `orcid` + `orcid_authenticated` to the Researcher records whose identifiers
passed the eligibility filter, and relabels ONLY those records
`source_type: merged_csv_api` with a list `source_id` carrying both origins.

Why in place rather than a second file: all eligible identifiers already exist in
researchers.jsonl. A second file would not merge (03 Pass 2 dedups WITHIN a file),
would pass 04 (duplicate identifiers are counted, not fatal), and would reach 05 as
a second MERGE on the same node — where `SET n += props` overwrites the six
provenance properties, so whichever file sorted last would silently decide the
node's provenance. One record per node is the only shape that keeps provenance true.

READ-THEN-WRITE DISCIPLINE (the overwrite lesson): the input is the COMMITTED
version of researchers.jsonl recovered from git, never the working copy, and never
reconstructed from Neo4j. Records are enriched, never replaced; every record not in
the eligible set is passed through byte-for-byte identical.

Confidence is deliberately NOT changed. See SCIKG_SCHEMA.md, "`merged_csv_api`
(added 2026-07-23) — COMPOSED fields, NOT corroborated ones."

Usage:
    python3 scripts/enrich_researchers_orcid.py --source <recovered.jsonl>            # dry run
    python3 scripts/enrich_researchers_orcid.py --source <recovered.jsonl> --apply
"""

import argparse
import collections
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(REPO, "data", "processed", "entities", "researchers.jsonl")
PROPOSED = os.path.join(REPO, "data", "processed", "review",
                        "proposed_researcher_orcid_entities.jsonl")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True,
                    help="git-recovered committed researchers.jsonl to enrich from")
    ap.add_argument("--apply", action="store_true",
                    help="write the result to data/processed/entities/researchers.jsonl")
    args = ap.parse_args()

    proposals = {}
    for line in open(PROPOSED, encoding="utf-8"):
        rec = json.loads(line)
        proposals[rec["identifier"]] = rec

    src = [json.loads(l) for l in open(args.source, encoding="utf-8")]

    out = []
    enriched = 0
    untouched = 0
    ids_enriched = set()
    conf_changed = 0
    for rec in src:
        ident = rec.get("identifier")
        prop = proposals.get(ident)
        if prop is None or rec.get("entity_type") != "Researcher":
            out.append(rec)
            untouched += 1
            continue

        new = dict(rec)
        props = dict(rec.get("properties") or {})
        # Add only; never remove or overwrite an existing identity field.
        props["orcid"] = prop["properties"]["orcid"]
        props["orcid_authenticated"] = prop["properties"]["orcid_authenticated"]
        new["properties"] = props

        # Composite provenance: this record's fields now come from two sources.
        new["source_type"] = "merged_csv_api"
        orig_sid = rec.get("source_id")
        orcid_sids = prop["source_id"]
        if isinstance(orcid_sids, str):
            orcid_sids = [orcid_sids]
        sids = ([orig_sid] if isinstance(orig_sid, str) else list(orig_sid or []))
        for s in orcid_sids:
            if s not in sids:
                sids.append(s)
        new["source_id"] = sids

        new["evidence_note"] = (
            (rec.get("evidence_note") or "").rstrip()
            + " | " + prop["evidence_note"]
        )
        # confidence deliberately untouched — composed, not corroborated.
        if new.get("confidence") != rec.get("confidence"):
            conf_changed += 1

        out.append(new)
        enriched += 1
        ids_enriched.add(ident)

    print("source records read              : %d" % len(src))
    print("records enriched                 : %d" % enriched)
    print("records passed through unchanged : %d" % untouched)
    print("distinct identifiers enriched    : %d (of %d proposed)"
          % (len(ids_enriched), len(proposals)))
    missing = set(proposals) - ids_enriched
    if missing:
        print("WARNING: %d proposed identifiers not found in source: %s"
              % (len(missing), sorted(missing)[:5]))
    print("confidence values changed        : %d (MUST be 0)" % conf_changed)
    st = collections.Counter(r.get("source_type") for r in out)
    print("source_type distribution after   : %s" % dict(st))

    if not args.apply:
        print("\nDRY RUN — nothing written. Re-run with --apply to write %s" % TARGET)
        return

    with open(TARGET, "w", encoding="utf-8") as fh:
        for rec in out:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("\nWROTE %s (%d records)" % (TARGET, len(out)))


if __name__ == "__main__":
    main()
