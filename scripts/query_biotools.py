#!/usr/bin/env python3
"""bio.tools exact-name query -> data/processed/software_registry.jsonl

Sec 9.4's durable fix (S2): registry data lives in a regenerable file, not in
a prose table. The transform reads this artifact; it never reads Sec 9.4's
seed table. Re-run this script to refresh.

Sec 9.2 rules enforced here (match rule ruled 2026-07-16):
  - Name match: whitespace REMOVED, case-insensitive. Reaches
    QIIME2 == "QIIME 2"; keeps the stored-casing variants of real tools
    (dada2, msConvert, msalign) that a case-as-stored rule would drop.
  - TWO guards, both checked BEFORE the name test, in order:
      GUARD 1 NHMFL_AUTHORED -- provenance-based, pre-query. Primary.
      GUARD 2 REJECT_HITS    -- Sec 9.2's blacklist. Secondary, and a LIVE
        RUNTIME GUARD, not a record of past decisions: removing an entry
        re-admits the false positive on the next run.
    Guard 2 exists because Guard 1 only knows tools WE author. Collisions on
    third-party tools are invisible to it -- see ATHENA in Sec 9.2.
  - biotools_status is has_id | searched_none. Never not_attempted, EXCEPT
    on query failure: asserting searched_none after a failed query would
    claim an absence never established (Sec 2.-1's guard, same shape).
  - RRID is NEVER queried or guessed here. SciCrunch name search is
    API-key-gated (Sec 9.2), so rrid_status stays not_attempted for
    everything except the one hand-verified value (Sec 9.4).

Authorized by Diya 2026-07-16 (D3). CLAUDE.md forbids external API calls
without explicit instruction; this is that instruction, recorded.
"""

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("data/processed/software_registry.jsonl")
API = "https://bio.tools/api/t/"
DELAY = 0.5          # be polite to a public API
TIMEOUT = 30

# The one hand-verified RRID (Sec 9.4). Never guessed, never queried.
RRID_VERIFIED = {"Xcalibur": "SCR_014593"}

# ---- GUARD 1 (primary): NHMFL-authored tools cannot have a bio.tools record.
# Checked BEFORE any query -- no API call is made at all. This rests on
# PROVENANCE we hold (who wrote the tool), not on name shape or description
# shape, so it cannot be defeated by a future registry entry that happens to
# collide on name. Sec 9.3 records the fact; this enforces it.
#   MIDAS added 2026-07-16 (Diya): Modular ICR Data Acquisition System,
#   NHMFL-authored, Predator's PREDECESSOR (not its parent) -- corroborated on
#   disk by "custom-built MIDAS software" (10.1038/s42004-018-0031-1).
#   CoreMS is NOT here: see Sec 9.2: its authorship is not establishable from
#   the repo, and guessing it would be the thing this guard exists to prevent.
NHMFL_AUTHORED = {"PetroOrg", "Predator", "EnviroOrg", "MIDAS"}

# ---- GUARD 2 (secondary): Sec 9.2's blacklist. A RUNTIME GUARD, not a record
# of past decisions -- it is checked before the name test on every run, and
# removing an entry RE-ADMITS the false positive. It catches collisions on
# tools we do NOT author, which GUARD 1 cannot see (it only knows our own).
# Keyed by the hit's VERBATIM stored name.
# ATHENA added 2026-07-16 (Diya, human-read): bio.tools ATHENA (biotoolsID
# athena, AI4SCR) is a spatial-omics framework; OUR Athena is the XAS/XANES
# tool of the Demeter/IFEFFIT suite (Ravel & Newville 2005) -- confirmed on
# disk via the CLS SGM beamline (10.1016/j.gca.2025.08.041) and SSRL
# (10.1021/acs.est.3c01347), both bundled with Fityk. This is the ONLY live
# entry: it is the collision guard 1 cannot see, because we do not author
# Athena. The other three are dead (see Sec 9.2b).
REJECT_HITS = {"ATHENA", "predatoR", "PreyTouch", "RelEx", "compareMS2"}

# ---- Sec 9.3 fourth state, RULED 2026-07-16 (Diya).
# biotools_status in {has_id, proposed, searched_none, not_attempted}.
#   proposed = an exact-name hit came back, NO human has read the description.
#   has_id   = a human read the description and confirmed it.
# An unread hit is a PROPOSAL, not a confirm -- writing has_id for it is an
# auto-accept, the same failure as auto-accepting a fuzzy match. Only names
# listed here have been read and confirmed by a human.
HUMAN_CONFIRMED = set()   # empty: no bio.tools hit has been confirmed yet.


def norm(s):
    """Sec 9.2 match rule (ruled 2026-07-16): whitespace REMOVED,
    case-insensitive. Whitespace removal is what reaches QIIME2 == "QIIME 2";
    collapsing it would leave the space and still miss. Case-insensitivity is
    load-bearing for stored-casing variants of real tools (dada2, msConvert,
    msalign) -- which is why predatoR needs GUARD 2, not a casing rule."""
    return re.sub(r"\s+", "", (s or "")).lower()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def query(name):
    """Return (biotools_id, matched_name, rejected[list]) for an exact match."""
    url = API + "?" + urllib.parse.urlencode({"q": name, "format": "json"})
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "scikg/1.0 (NHMFL research KG; contact via repo)",
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        data = json.loads(r.read().decode("utf-8"))

    rejected, blocked = [], []
    for hit in data.get("list", []) or []:
        hit_name = hit.get("name") or ""
        if hit_name in REJECT_HITS:
            blocked.append(hit_name)
            rejected.append(hit_name)
            continue
        if norm(hit_name) == norm(name):
            return hit, hit_name, rejected, blocked
        rejected.append(hit_name)
    return None, None, rejected, blocked


def main():
    tools = sys.argv[1:]
    if not tools:
        raise SystemExit("usage: query_biotools.py <tool name> [...]")

    run_at = now_iso()   # run-level, not per-row: a re-run diffs one line.
    rows = []
    for name in tools:
        # GUARD 1 -- before any query. No API call is made.
        if name in NHMFL_AUTHORED:
            rows.append({
                "name": name, "biotools_id": None,
                "biotools_status": "searched_none",
                "guard": "nhmfl_authored",
                "guard_note": "NHMFL-authored (Sec 9.3); cannot have a "
                              "bio.tools record. Not queried.",
                "rrid": RRID_VERIFIED.get(name),
                "rrid_status": "has_id" if name in RRID_VERIFIED else "not_attempted",
                "source": "guard: NHMFL-authored, no query issued",
            })
            print(f"{name:22s} searched_none  [GUARD 1: NHMFL-authored, not queried]")
            continue
        try:
            hit, matched, rejected, blocked = query(name)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            print(f"QUERY_FAILED {name}: {e}")
            # A failed query is NOT searched_none -- that would assert an
            # absence we never established. Sec 2.-1's guard, same shape.
            rows.append({
                "name": name, "biotools_id": None,
                "biotools_status": "not_attempted",
                "query_error": str(e),
            })
            time.sleep(DELAY)
            continue

        flagged = blocked
        bid = hit.get("biotoolsID") if hit else None
        # Ruling 2: an unread hit is PROPOSED, never has_id.
        if not bid:
            status = "searched_none"
        elif name in HUMAN_CONFIRMED:
            status = "has_id"
        else:
            status = "proposed"
        row = {
            "name": name,
            # proposed IDs live here for review; they must NOT reach the graph.
            "biotools_id": bid if status == "has_id" else None,
            "proposed_biotools_id": bid if status == "proposed" else None,
            "biotools_status": status,
            "matched_name": matched,
            "proposed_description": (hit.get("description") or "")[:400] if hit else None,
            "proposed_topics": [t.get("term") for t in (hit.get("topic") or [])] if hit else None,
            "proposed_homepage": hit.get("homepage") if hit else None,
            "rejected_fuzzy_hits": rejected[:8],
            "blocked_false_positives": flagged,
            "rrid": RRID_VERIFIED.get(name),
            "rrid_status": "has_id" if name in RRID_VERIFIED else "not_attempted",
            "source": "bio.tools exact-name API query",
        }
        rows.append(row)
        mark = f"{status} {bid}" if bid else "searched_none"
        extra = f"  [rejected fuzzy: {', '.join(rejected[:3])}]" if rejected else ""
        print(f"{name:22s} {mark}{extra}")
        time.sleep(DELAY)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        # Run-level metadata: one line, so a re-run diffs one line instead of
        # every row (the artifact is tracked -- see .gitignore).
        f.write(json.dumps({
            "_meta": True, "run_at": run_at, "api": API,
            "match_rule": "whitespace-removed, case-insensitive",
            "guards": ["nhmfl_authored (primary, pre-query)",
                       "reject_hits blacklist (secondary, pre-name-test)"],
            "tools_queried": len(rows),
        }) + "\n")
        for r in rows:
            f.write(json.dumps(r) + "\n")

    def n(st): return sum(1 for r in rows if r["biotools_status"] == st)
    print(f"\nqueried={len(rows)} has_id={n('has_id')} proposed={n('proposed')} "
          f"searched_none={n('searched_none')} not_attempted={n('not_attempted')}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
