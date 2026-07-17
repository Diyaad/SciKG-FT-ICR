"""
03_normalize.py — normalize the extracted SciKG entities and relationships.

Runs after all extraction stages (02, 02b, 02c, and later 02d/02e). Reads every
JSONL in data/processed/entities/ and data/processed/relationships/, resolves
duplicate entities, rewrites relationship endpoints through an ID crosswalk,
maps raw instrument strings to the controlled vocabulary, and writes normalized
copies to data/processed/normalized/. Inputs are never modified.

This is a DRAFT for the current data state. Hooks that depend on data not yet in
the pipeline (ORCID canonicalization, institution deduplication, PDF/annotation
sources) are present but inert until those sources land — each is labeled.

Design notes
------------
Crosswalk (the load-bearing piece): entity dedup can retire an ID in one pass and
retire its survivor again in a later pass (e.g. a natural-key researcher survivor
that later shares an ORCID). A naive single-lookup rewrite would then land on a
retired, dangling ID. This script uses union-find with path compression so every
ID resolves to its TERMINAL survivor, closing that chaining gap.

Nothing is dropped silently. Every merge, rewrite, vocab hit/miss, and dropped
edge is written to normalization_log.jsonl or review_queue.jsonl with a reason.

Standard library only. Python 3.11+. Run from the repository root:
    python scripts/03_normalize.py
"""
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES_DIR = REPO / "data" / "processed" / "entities"
RELATIONSHIPS_DIR = REPO / "data" / "processed" / "relationships"
VOCAB_PATH = REPO / "docs" / "controlled_vocabulary.md"
OUTPUT_DIR = REPO / "data" / "processed" / "normalized"

SCHEMA_VERSION = "v1.0"

# ============================== CONFIG ==============================
# Adjust after reading the code. Nothing here is applied silently.

# Trust ranking used to pick the SURVIVING record when two entities share an
# identifier. Lower number = higher trust = wins on field conflicts.
# DRAFT DEFAULT — confirm this ordering matches project policy before load.
SOURCE_PRECEDENCE = {
    "manual_annotation": 0,   # hand-verified ground truth (8 annotated papers)
    "api": 1,                 # CrossRef / OpenAlex — never overwritten by lower ranks
    "fisher_py": 2,           # instrument headers read directly from RAW files
    "csv": 3,                 # MagLab internal CSV
    "llm_extraction": 4,      # 02d PDF extraction — lowest, pending evaluation
}
DEFAULT_RANK = 99

# The Aliases cell in the controlled-vocabulary Instruments table is split on
# these separators. FLAGGED ASSUMPTION: if aliases use a different delimiter,
# affected instruments surface in review_queue.jsonl (fails loud, not silent).
ALIAS_SEPARATORS = [";", ",", "|"]

# ORCID canonicalization. Inert today (0 ORCIDs in researchers.jsonl). Goes live
# once 02e (annotation extractor) and/or 02d emit ORCID-bearing researcher
# records. Leaving it enabled simply no-ops when no ORCID is present.
ENABLE_ORCID_CANONICALIZATION = True

# Instrument identifiers are left stable in this draft; canonical_name and
# psi_ms_id are filled into properties instead of re-minting the identifier.
# Re-minting to a canonical instrument ID (and rewriting USES_INSTRUMENT edges
# through the crosswalk) is a deliberate future option, not assumed here.
REMINT_INSTRUMENT_IDS = False
# ====================================================================


# ----------------------------- io helpers ---------------------------
def load_jsonl(path):
    records = []
    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{lineno} invalid JSON: {exc}") from exc
    return records


def write_jsonl(path, records):
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False))
            f.write("\n")


# ----------------------------- crosswalk ----------------------------
class Crosswalk:
    """Union-find over entity IDs. retire(old, survivor) records old -> survivor;
    resolve(x) returns the terminal survivor with path compression, so no chain
    of retired IDs is ever left dangling."""

    def __init__(self):
        self._parent = {}

    def retire(self, old_id, survivor_id):
        if old_id == survivor_id:
            return
        # Point old at survivor's terminal, so retiring a prior survivor chains
        # correctly rather than creating A->B while B->C already exists.
        root = self.resolve(survivor_id)
        if self.resolve(old_id) != root:
            self._parent[old_id] = root

    def resolve(self, x):
        # Walk to terminal, compressing the path.
        path = []
        while x in self._parent:
            path.append(x)
            x = self._parent[x]
        for node in path:
            self._parent[node] = x
        return x

    def is_retired(self, x):
        return x in self._parent

    def as_records(self):
        return [
            {"retired_id": old, "canonical_id": self.resolve(old)}
            for old in sorted(self._parent)
        ]


# ------------------------- normalization utils ----------------------
def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def source_rank(rec):
    return SOURCE_PRECEDENCE.get(rec.get("source_type"), DEFAULT_RANK)


def norm_match_key(s):
    """Normalize a string for controlled-vocabulary matching: lowercase, turn
    separators into spaces, collapse whitespace, drop surrounding punctuation."""
    if s is None:
        return ""
    s = s.lower().replace("_", " ").replace("-", " ")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def canonicalize_identifier(identifier):
    """Enforce the namespace:value shape and lowercase the DOI value. Returns the
    (possibly unchanged) identifier. Whitespace is always stripped."""
    if identifier is None:
        return identifier
    ident = identifier.strip()
    if ident.lower().startswith("doi:"):
        # DOIs are the lowercase master key; only the value part is touched.
        ident = "doi:" + ident[4:].lower()
    return ident


def merge_entities(survivor, other, log, reason):
    """Merge `other` into `survivor` (survivor already chosen by source rank).
    Survivor's non-null property values win; survivor nulls are filled from
    other; is_ground_truth is preserved if either side has it. Provenance of the
    survivor is kept intact. The merge is recorded in the log."""
    s_props = dict(survivor.get("properties") or {})
    o_props = other.get("properties") or {}
    filled = []
    for key, o_val in o_props.items():
        if o_val is None:
            continue
        if s_props.get(key) is None:
            s_props[key] = o_val
            filled.append(key)
    # Ground-truth flag must survive a merge from either direction.
    if o_props.get("is_ground_truth") or s_props.get("is_ground_truth"):
        s_props["is_ground_truth"] = True
    survivor["properties"] = s_props
    log.append({
        "action": "merge_entity",
        "entity_type": survivor.get("entity_type"),
        "survivor_id": survivor.get("identifier"),
        "retired_id": other.get("identifier"),
        "survivor_source": survivor.get("source_type"),
        "retired_source": other.get("source_type"),
        "filled_null_fields": filled,
        "reason": reason,
        "at": now_iso(),
    })
    return survivor


# --------------------------- vocab parsing --------------------------
def parse_instrument_vocab(md_path, log):
    """Parse the Instruments table (Canonical | PSI-MS ID | Aliases | Vendor)
    from the controlled-vocabulary markdown. Returns {match_key: {canonical,
    psi_ms_id}} covering every alias plus the canonical name itself."""
    vocab = {}
    if not md_path.is_file():
        log.append({"action": "vocab_missing", "path": str(md_path), "at": now_iso()})
        return vocab

    lines = md_path.read_text(encoding="utf-8").splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        low = line.lower()
        if "|" in line and "canonical" in low and "psi-ms" in low:
            header_idx = i
            break
    if header_idx is None:
        log.append({"action": "vocab_table_not_found", "path": str(md_path), "at": now_iso()})
        return vocab

    def cells(row):
        parts = [c.strip() for c in row.strip().strip("|").split("|")]
        return parts

    header = [c.lower() for c in cells(lines[header_idx])]
    try:
        col_canon = header.index("canonical")
        col_psi = next(i for i, c in enumerate(header) if "psi-ms" in c)
        col_alias = next(i for i, c in enumerate(header) if "alias" in c)
    except (ValueError, StopIteration):
        log.append({"action": "vocab_header_unparsed", "header": header, "at": now_iso()})
        return vocab

    for line in lines[header_idx + 1:]:
        if "|" not in line:
            break  # table ended
        if re.match(r"^\s*\|?[\s:-]+\|", line):
            continue  # separator row ---|---
        row = cells(line)
        if len(row) <= max(col_canon, col_psi, col_alias):
            continue
        canonical = row[col_canon]
        psi = row[col_psi] or None
        if not canonical:
            continue
        entry = {"canonical": canonical, "psi_ms_id": psi}
        keys = {norm_match_key(canonical)}
        alias_cell = row[col_alias]
        if alias_cell:
            sep_pattern = "|".join(re.escape(s) for s in ALIAS_SEPARATORS)
            for alias in re.split(sep_pattern, alias_cell):
                k = norm_match_key(alias)
                if k:
                    keys.add(k)
        for k in keys:
            if k:
                vocab[k] = entry
    log.append({"action": "vocab_loaded", "instrument_terms": len(vocab), "at": now_iso()})
    return vocab


def raw_instrument_strings(entity):
    """The raw string(s) to match an Instrument entity against the vocabulary.

    ALWAYS RETURNS A LIST. The PDF instrument transform writes `name_raw` as a
    list of observed variants on 54 of its 462 Instrument nodes; the previous
    single-string contract crashed on first contact (AttributeError: 'list'
    object has no attribute 'lower'). The list was never the bug — assuming a
    string was.

    MODEL IS AUTHORITATIVE: prefer model_raw over any name field. For this corpus
    an instrument's .name can be stale (the PXD sweep reports "Orbitrap Velos Pro"
    for the same box .model calls "LTQ FT Ultra"), so 02c/02f build node IDENTITY
    from .model. Vocab matching follows the same rule — otherwise a node keyed
    instrument:raw:ltq_ft_ultra would map to the stale name's term. NOTE: on all
    54 list-valued nodes `model_raw` is present but None, so the preference has
    nothing to prefer and correctly falls through to `name_raw`.

    Falls back to the name fields, then the segment after 'instrument:raw:'."""
    props = entity.get("properties") or {}
    for key in ("instrument_model_raw", "model_raw",
                "instrument_name_raw", "raw_name", "name_raw", "name"):
        val = props.get(key)
        if val:
            return [v for v in (val if isinstance(val, list) else [val]) if v]
    ident = entity.get("identifier", "")
    m = re.match(r"^instrument:raw:(.+)$", ident)
    if m:
        return [m.group(1)]
    # Fall back to whatever follows the last colon.
    return [ident.split(":")[-1] if ":" in ident else ident]


# -------------------------------- main ------------------------------
def main():
    if not ENTITIES_DIR.is_dir():
        print(f"ERROR entities dir missing: {ENTITIES_DIR}")
        return 1
    if not RELATIONSHIPS_DIR.is_dir():
        print(f"ERROR relationships dir missing: {RELATIONSHIPS_DIR}")
        return 1

    log = []
    review = []
    crosswalk = Crosswalk()

    # --- Load ---------------------------------------------------------
    entity_files = sorted(ENTITIES_DIR.glob("*.jsonl"))
    rel_files = sorted(RELATIONSHIPS_DIR.glob("*.jsonl"))
    if not entity_files:
        print(f"ERROR no entity JSONL files in {ENTITIES_DIR}")
        return 1

    # entities_by_file preserves which type came from which file, so normalized
    # output mirrors the input layout. entity_index maps final id -> record.
    entities_by_file = {p.name: load_jsonl(p) for p in entity_files}
    rels_by_file = {p.name: load_jsonl(p) for p in rel_files}

    total_in = sum(len(v) for v in entities_by_file.values())

    # --- Pass 1: identifier canonicalization --------------------------
    for records in entities_by_file.values():
        for rec in records:
            old = rec.get("identifier")
            new = canonicalize_identifier(old)
            if new != old:
                rec["identifier"] = new
                crosswalk.retire(old, new)
                log.append({"action": "canonicalize_id", "from": old, "to": new, "at": now_iso()})

    # --- Pass 2: exact-identifier dedup within each entity type --------
    # Two records with the same identifier are the same node; keep the higher
    # trust source as survivor and union the rest of the fields.
    for fname, records in entities_by_file.items():
        groups = defaultdict(list)
        for rec in records:
            groups[rec["identifier"]].append(rec)
        deduped = []
        for ident, group in groups.items():
            if len(group) == 1:
                deduped.append(group[0])
                continue
            group.sort(key=source_rank)  # lowest rank number (highest trust) first
            survivor = group[0]
            for other in group[1:]:
                merge_entities(survivor, other, log, reason="duplicate_identifier")
            deduped.append(survivor)
        entities_by_file[fname] = deduped

    # --- Pass 3: ORCID canonicalization (INERT until ORCIDs present) ---
    # Retire a minted researcher:* identifier to orcid:<value> when the record
    # carries an ORCID. With 0 ORCIDs today this loop simply does nothing.
    if ENABLE_ORCID_CANONICALIZATION:
        orcid_events = 0
        for records in entities_by_file.values():
            for rec in records:
                if rec.get("entity_type") != "Researcher":
                    continue
                props = rec.get("properties") or {}
                orcid = props.get("orcid")
                if not orcid:
                    continue
                canon = "orcid:" + str(orcid).strip()
                old = rec["identifier"]
                if old != canon:
                    crosswalk.retire(old, canon)
                    rec["identifier"] = canon
                    orcid_events += 1
                    log.append({"action": "orcid_canonicalize", "from": old, "to": canon, "at": now_iso()})
        log.append({"action": "orcid_pass_summary", "canonicalized": orcid_events, "at": now_iso()})

    # --- Pass 4: institution dedup (INERT — no institutions.jsonl) -----
    if any(r.get("entity_type") == "Institution"
           for recs in entities_by_file.values() for r in recs):
        review.append({"action": "institution_dedup_todo",
                       "note": "Institution entities present but ROR dedup not yet implemented.",
                       "at": now_iso()})
    else:
        log.append({"action": "institution_pass_skipped",
                    "reason": "no Institution entities in current data", "at": now_iso()})

    # After all retirements, collapse re-dedup: if two identifiers were merged to
    # the same terminal via the crosswalk, fold their records together too.
    def resolved(rec):
        return crosswalk.resolve(rec["identifier"])

    for fname, records in entities_by_file.items():
        groups = defaultdict(list)
        for rec in records:
            rec["identifier"] = resolved(rec)
            groups[rec["identifier"]].append(rec)
        folded = []
        for ident, group in groups.items():
            group.sort(key=source_rank)
            survivor = group[0]
            for other in group[1:]:
                merge_entities(survivor, other, log, reason="crosswalk_terminal_merge")
            folded.append(survivor)
        entities_by_file[fname] = folded

    # --- Pass 5: controlled-vocabulary mapping (instruments) ----------
    vocab = parse_instrument_vocab(VOCAB_PATH, log)
    mapped = unmapped = 0
    for records in entities_by_file.values():
        for rec in records:
            if rec.get("entity_type") != "Instrument":
                continue
            props = rec.setdefault("properties", {})
            variants = raw_instrument_strings(rec)
            # Match EVERY variant. Measured 2026-07-16: 0 nodes have variants
            # hitting two different CV terms, so matching-all is safe today.
            hits = {}
            for v in variants:
                h = vocab.get(norm_match_key(v))
                if h:
                    hits[h["canonical"]] = h
            if len(hits) > 1:
                # UNANIMITY ASSERT. 0 nodes trip this today; it exists so a
                # future CV addition cannot silently create a node whose
                # variants disagree. Do NOT pick a winner -- leave it unmapped.
                unmapped += 1
                review.append({"action": "instrument_cv_conflict",
                               "identifier": rec["identifier"],
                               "raw": variants,
                               "conflicting_terms": sorted(hits),
                               "note": "Variants of ONE node matched DIFFERENT controlled-"
                                       "vocabulary terms. No automatic rule is correct: the "
                                       "node is left unmapped for a human. Adding a CV alias "
                                       "can cause this.", "at": now_iso()})
            elif hits:
                hit = next(iter(hits.values()))
                props["canonical_name"] = hit["canonical"]
                props["psi_ms_id"] = hit["psi_ms_id"]
                mapped += 1
                log.append({"action": "instrument_mapped", "identifier": rec["identifier"],
                            "raw": variants, "matched_variants": len(hits),
                            "variants_tried": len(variants),
                            "canonical": hit["canonical"],
                            "psi_ms_id": hit["psi_ms_id"], "at": now_iso()})
            else:
                unmapped += 1
                review.append({"action": "instrument_unmapped", "identifier": rec["identifier"],
                               "raw": variants,
                               "match_keys": [norm_match_key(v) for v in variants],
                               "note": "No alias match in Instruments vocab for ANY variant. "
                                       "Add an alias or check ALIAS_SEPARATORS.",
                               "at": now_iso()})

    # Build the surviving-node set for relationship integrity checks.
    surviving_ids = set()
    for records in entities_by_file.values():
        for rec in records:
            surviving_ids.add(rec["identifier"])

    # --- Pass 6: relationship rewrite + dedup + integrity -------------
    rels_out = {}
    dangling = 0
    rel_dups = 0
    for fname, rels in rels_by_file.items():
        seen = {}
        kept = []
        for rel in rels:
            subj = crosswalk.resolve(canonicalize_identifier(rel.get("subject_id")))
            obj = crosswalk.resolve(canonicalize_identifier(rel.get("object_id")))
            if subj != rel.get("subject_id"):
                rel["subject_id"] = subj
            if obj != rel.get("object_id"):
                rel["object_id"] = obj
            # Integrity: both endpoints must resolve to a surviving node.
            missing = [e for e in (subj, obj) if e not in surviving_ids]
            if missing:
                dangling += 1
                review.append({"action": "dangling_relationship",
                               "relationship_type": rel.get("relationship_type"),
                               "subject_id": subj, "object_id": obj,
                               "missing_endpoints": missing,
                               "note": "Endpoint has no surviving entity; edge withheld from "
                                       "normalized output and logged here to review_queue; "
                                       "04_validate reads normalized/ only and never sees it.",
                               "at": now_iso()})
                continue
            key = (rel.get("relationship_type"), subj, obj)
            if key in seen:
                rel_dups += 1
                # Union properties of the duplicate edge into the kept one.
                keep = seen[key]
                for k, v in (rel.get("properties") or {}).items():
                    keep.setdefault("properties", {}).setdefault(k, v)
                log.append({"action": "duplicate_relationship", "key": list(key), "at": now_iso()})
                continue
            seen[key] = rel
            kept.append(rel)
        rels_out[fname] = kept

    # --- Pass 7: write outputs ---------------------------------------
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total_out = 0
    for fname, records in entities_by_file.items():
        write_jsonl(OUTPUT_DIR / fname, records)
        total_out += len(records)
    for fname, rels in rels_out.items():
        write_jsonl(OUTPUT_DIR / fname, rels)
    write_jsonl(OUTPUT_DIR / "normalization_log.jsonl", log)
    write_jsonl(OUTPUT_DIR / "review_queue.jsonl", review)
    write_jsonl(OUTPUT_DIR / "crosswalk.jsonl", crosswalk.as_records())

    # --- Summary ------------------------------------------------------
    print("03_normalize summary")
    print(f"  entity files:            {len(entity_files)}")
    print(f"  entities in:             {total_in}")
    print(f"  entities out:            {total_out}")
    print(f"  entities merged:         {total_in - total_out}")
    print(f"  crosswalk entries:       {len(crosswalk.as_records())}")
    print(f"  instruments mapped:      {mapped}")
    print(f"  instruments unmapped:    {unmapped}  (see review_queue.jsonl)")
    rel_in = sum(len(v) for v in rels_by_file.values())
    rel_out = sum(len(v) for v in rels_out.values())
    print(f"  relationships in:        {rel_in}")
    print(f"  relationships out:       {rel_out}")
    print(f"  relationships deduped:   {rel_dups}")
    print(f"  dangling edges withheld: {dangling}  (see review_queue.jsonl)")
    print(f"  review queue entries:    {len(review)}")
    print(f"  output written to:       {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
