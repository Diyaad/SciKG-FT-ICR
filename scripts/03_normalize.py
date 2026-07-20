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
import argparse
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

# KI-8 remediation (R1). RawDataFile identity becomes the composite
# rawfile:{filename}:{sha16}, sha16 = first N hex chars of sha256_hash. N=16 is
# collision-safe well past corpus scale (measured floor for the 913 distinct
# hashes is 6; 16 = 64 bits of margin). This is the ONLY number in the pass, and
# it is a hash-prefix length, not a count of files or of collisions.
SHA16_LEN = 16
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
        # "Ontology ID" is the current header (renamed from "PSI-MS ID", R6); accept
        # either so an older CV still parses.
        if "|" in line and "canonical" in low and ("ontology id" in low or "psi-ms" in low):
            header_idx = i
            break
    if header_idx is None:
        log.append({"action": "vocab_table_not_found", "path": str(md_path), "at": now_iso()})
        return vocab

    def cells(row):
        parts = [c.strip() for c in row.strip().strip("|").split("|")]
        return parts

    def find_col(header, *subs, required=True):
        for i, c in enumerate(header):
            if any(s in c for s in subs):
                return i
        if required:
            raise ValueError(subs)
        return None

    header = [c.lower() for c in cells(lines[header_idx])]
    try:
        col_canon = header.index("canonical")
        col_ont = find_col(header, "ontology id", "psi-ms")   # accession col (R6 rename)
        col_alias = find_col(header, "alias")
    except (ValueError, StopIteration):
        log.append({"action": "vocab_header_unparsed", "header": header, "at": now_iso()})
        return vocab
    # New optional columns (R4/R5/R6); None if a legacy CV lacks them.
    col_src = find_col(header, "ontology source", required=False)
    col_tesla = find_col(header, "magnetic field", "tesla", required=False)
    col_mhz = find_col(header, "frequency", "mhz", required=False)

    def num(cell):
        cell = (cell or "").strip()
        if not cell:
            return None
        try:
            return float(cell)
        except ValueError:
            return None

    need = max(c for c in (col_canon, col_ont, col_alias, col_src, col_tesla, col_mhz)
               if c is not None)
    for line in lines[header_idx + 1:]:
        if "|" not in line:
            break  # table ended
        if re.match(r"^\s*\|?[\s:-]+\|", line):
            continue  # separator row ---|---
        row = cells(line)
        if len(row) <= need:
            continue
        canonical = row[col_canon]
        psi = row[col_ont] or None
        if not canonical:
            continue
        entry = {
            "canonical": canonical,
            "psi_ms_id": psi,
            "ontology_source": (row[col_src].strip() or None) if col_src is not None else None,
            "magnetic_field_tesla": num(row[col_tesla]) if col_tesla is not None else None,
            "nmr_frequency_mhz": num(row[col_mhz]) if col_mhz is not None else None,
        }
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
def main(dry_run=False):
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

    # --- Pass 1.5: RawDataFile composite identity (KI-8 remediation, R1) -----
    # Retire rawfile:{filename} -> rawfile:{filename}:{sha16}. COUNT-FREE: the
    # composite is built for EVERY RawDataFile from its OWN filename + hash — no
    # reference to 21, to pairs, or to any fixed count. Recorded in the crosswalk
    # so Pass 6 rewrites every RawDataFile edge endpoint onto the composite.
    #   KI-1  same filename + same hash      -> same composite  -> Pass 2 collapses to 1 node.
    #   KI-8  same hash, different filename   -> different composite -> stay distinct nodes.
    #   (c)   same filename, different hash   -> different composite -> stay distinct (0 today).
    # sha256_hash stays a property; identity moves into `identifier`. Ordered
    # BEFORE Pass 2 so the dedup key Pass 2 groups on is already the composite.
    composite_events = 0
    for records in entities_by_file.values():
        for rec in records:
            if rec.get("entity_type") != "RawDataFile":
                continue
            props = rec.get("properties") or {}
            sha = props.get("sha256_hash")
            fname = props.get("filename")
            if not sha or not fname:
                # Cannot form composite identity — a silent identity change would be
                # worse than stopping. HARD STOP (R1).
                missing = "sha256_hash" if not sha else "filename"
                print(f"HARD STOP (R1): RawDataFile {rec.get('identifier')!r} is missing "
                      f"{missing}; cannot form composite identity. No output written.")
                return 1
            old = rec["identifier"]
            new = f"rawfile:{fname}:{sha[:SHA16_LEN]}"
            if new != old:
                rec["identifier"] = new
                crosswalk.retire(old, new)
                composite_events += 1
                log.append({"action": "rawfile_composite_id", "from": old, "to": new,
                            "sha16": sha[:SHA16_LEN], "at": now_iso()})
    log.append({"action": "rawfile_composite_summary", "retired": composite_events,
                "sha16_len": SHA16_LEN, "at": now_iso()})

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
                # R4/R5/R6: fill ontology_source + field-strength from the CV, only
                # when the CV states a value (null stays absent, not written null).
                if hit.get("ontology_source"):
                    props["ontology_source"] = hit["ontology_source"]
                if hit.get("magnetic_field_tesla") is not None:
                    props["magnetic_field_tesla"] = hit["magnetic_field_tesla"]
                if hit.get("nmr_frequency_mhz") is not None:
                    props["nmr_frequency_mhz"] = hit["nmr_frequency_mhz"]
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

    # --- Pass 5.5: Advisory generation (byte-identical sets, R2) -------------
    # Group the surviving RawDataFile nodes by sha256_hash. COUNT-FREE, held to the
    # T3 standard: emit ONE Advisory per hash whose member count > 1 (any N, never
    # assumes 2), and one FLAGS edge per member (N edges for an N-member set).
    # Provenance is graph_derived — this node is computed by the pipeline from its
    # own data, not extracted from a source document.
    #
    # deposit: a member's PXD accession comes from its DERIVED_FROM edge
    # (dataset:proteomexchange:{pxd}). If the whole set is intra-deposit (one
    # accession) it is recorded; a cross-deposit set records null.
    rawfile_deposit = defaultdict(set)      # composite rawfile id -> {pxd accession}
    for rels in rels_by_file.values():
        for rel in rels:
            if rel.get("relationship_type") != "DERIVED_FROM":
                continue
            subj = crosswalk.resolve(canonicalize_identifier(rel.get("subject_id")))
            m = re.match(r"^dataset:proteomexchange:(.+)$", rel.get("object_id") or "")
            if m:
                rawfile_deposit[subj].add(m.group(1))

    rdf_by_hash = defaultdict(list)
    for records in entities_by_file.values():
        for rec in records:
            if rec.get("entity_type") != "RawDataFile":
                continue
            sha = (rec.get("properties") or {}).get("sha256_hash")
            rdf_by_hash[sha].append(rec)

    advisory_nodes = []
    flags_edges = []
    adv_ts = now_iso()
    for sha, members in rdf_by_hash.items():
        if len(members) <= 1:            # <-- the rule: any hash with >1 member; never 2
            continue
        sha16 = sha[:SHA16_LEN]
        member_ids = [m["identifier"] for m in members]
        member_fns = [(m.get("properties") or {}).get("filename") for m in members]
        deposits = set()
        for mid in member_ids:
            deposits |= rawfile_deposit.get(mid, set())
        deposit = next(iter(deposits)) if len(deposits) == 1 else None
        adv_id = f"advisory:byte_identical:{sha16}"
        advisory_nodes.append({
            "identifier": adv_id,
            "entity_type": "Advisory",
            "properties": {
                "advisory_type": "byte_identical_content",
                "sha256_hash": sha,
                "member_identifiers": member_ids,
                "member_filenames": member_fns,
                "deposit": deposit,
            },
            "source_type": "graph_derived",
            "confidence": "high",
            "extracted_at": adv_ts,
            "evidence_note": ("byte-identical content set detected during normalization; "
                              f"members share sha256 {sha}"),
            "source_id": member_ids,
            "schema_version": SCHEMA_VERSION,
        })
        for mid in member_ids:
            flags_edges.append({
                "relationship_type": "FLAGS",
                "subject_id": adv_id,
                "subject_type": "Advisory",
                "object_id": mid,
                "object_type": "RawDataFile",
                "properties": {},
                "source_type": "graph_derived",
                "confidence": "high",
                "extracted_at": adv_ts,
                "evidence_note": ("Advisory flags a member of a byte-identical content set "
                                  f"(sha256 {sha})."),
                "source_id": [adv_id, mid],
                "schema_version": SCHEMA_VERSION,
            })
    if advisory_nodes:
        entities_by_file["advisories.jsonl"] = advisory_nodes
        for adv in advisory_nodes:
            surviving_ids.add(adv["identifier"])
    log.append({"action": "advisory_summary", "sets": len(advisory_nodes),
                "flags_edges": len(flags_edges), "at": now_iso()})

    # --- Pass 6: relationship rewrite + dedup + integrity -------------
    rels_out = {}
    dangling = 0
    rel_dups = 0
    # R1 hard-stop accounting: every edge endpoint typed RawDataFile must resolve
    # (through the crosswalk) onto a surviving composite node. A RawDataFile
    # endpoint that dangles after the composite rewrite is a HARD STOP, not a soft
    # withhold — the composite retirement would have orphaned a real edge.
    rawfile_endpoints_total = 0
    rawfile_endpoints_ok = 0
    rawfile_dangling = []
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
            for ep_val, ep_type in ((subj, rel.get("subject_type")),
                                    (obj, rel.get("object_type"))):
                if ep_type == "RawDataFile":
                    rawfile_endpoints_total += 1
                    if ep_val in surviving_ids:
                        rawfile_endpoints_ok += 1
                    else:
                        rawfile_dangling.append(
                            {"relationship_type": rel.get("relationship_type"),
                             "endpoint": ep_val, "in_file": fname})
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

    # --- Pass 6.5: cross-file edge reconciliation (E1 / KI-12) --------
    # EDGES ONLY. Two extractors (02b CSV, the PDF transform) can write the SAME
    # (type, subject, object) edge to DIFFERENT relationship files. Pass 6 dedups
    # WITHIN a file and structurally cannot see the cross-file pair, so 05's
    # MERGE (a)-[:TYPE]->(b) would collapse it and destroy one source's provenance
    # silently (KI-12). Here we reconcile a multi-source triple into ONE edge that
    # KEEPS BOTH origins (source_id becomes a list; confidence high — two independent
    # sources agreeing is stronger than either).
    #
    # DO NOT EXTEND THIS TO NODES. Cross-file node overlap is 0 BY DESIGN, and the
    # two-file convention (Instrument / Dataset / Software split across entity files)
    # depends on 03 NOT merging entities across files: merging would collide their
    # frozen identifiers and break that invariant. Edges have no such invariant; nodes
    # do. The asymmetry is intentional — measured cross-file: entities 0, edges 74.
    #
    # SCOPE: only the ruled shape merges — exactly two records whose source_types are
    # {csv, llm_extraction} (E1). Any other multi-source triple is a FINDING, left
    # unmerged and sent to review_queue (Q2 proved the 74 are the only cross-file
    # triples, so this must fire exactly 74 times and touch nothing else).
    SAFE_MERGE_SOURCES = {"csv", "llm_extraction"}
    triple_groups = {}
    for fname, rels in rels_out.items():
        for rel in rels:
            k = (rel.get("relationship_type"), rel.get("subject_id"), rel.get("object_id"))
            triple_groups.setdefault(k, []).append((fname, rel))
    cross_file_merges = 0
    cross_file_findings = 0
    drop_ids = set()          # id() of constituent rel dicts to remove
    add_to_file = {}          # fname -> [merged rel, ...]
    for k, members in triple_groups.items():
        if len(members) < 2:
            continue
        srcs = {rel.get("source_type") for _, rel in members}
        if len(members) == 2 and srcs == SAFE_MERGE_SOURCES:
            bysrc = {rel.get("source_type"): (fname, rel) for fname, rel in members}
            csv_fname, csv_rel = bysrc["csv"]
            _, llm_rel = bysrc["llm_extraction"]
            merged = dict(csv_rel)                       # same triple either way
            merged["source_type"] = "merged_csv_llm"
            merged["confidence"] = "high"
            merged["source_id"] = [csv_rel.get("source_id"), llm_rel.get("source_id")]  # list (E1)
            merged["evidence_note"] = (
                "Two independent sources attest this edge (cross-source corroboration "
                "-> confidence high). CSV: " + str(csv_rel.get("evidence_note"))
                + " | PDF: " + str(llm_rel.get("evidence_note")))
            props = dict(csv_rel.get("properties") or {})
            for pk, pv in (llm_rel.get("properties") or {}).items():
                props.setdefault(pk, pv)
            merged["properties"] = props
            merged["extracted_at"] = now_iso()
            drop_ids.add(id(csv_rel))
            drop_ids.add(id(llm_rel))
            add_to_file.setdefault(csv_fname, []).append(merged)   # merged edge -> CSV file
            cross_file_merges += 1
            log.append({"action": "cross_file_edge_merge", "key": list(k),
                        "source_ids": merged["source_id"], "at": now_iso()})
        else:
            cross_file_findings += 1
            review.append({"action": "unexpected_multi_source_edge",
                           "relationship_type": k[0], "subject_id": k[1], "object_id": k[2],
                           "source_types": sorted(s for s in srcs if s is not None),
                           "member_count": len(members),
                           "note": "Cross-file duplicate triple whose source set is NOT "
                                   "{csv, llm_extraction}; left UNMERGED for review (E1 scope).",
                           "at": now_iso()})
    if drop_ids or add_to_file:
        for fname in list(rels_out.keys()):
            kept = [rel for rel in rels_out[fname] if id(rel) not in drop_ids]
            kept.extend(add_to_file.get(fname, []))
            rels_out[fname] = kept

    # --- Pass 6.6: HARD STOP if any RawDataFile edge endpoint dangled (R1) ----
    # The composite retirement must leave every RawDataFile edge endpoint pointing
    # at a surviving node. If not, the rewrite orphaned a real edge — stop before
    # writing anything, so a half-rewritten graph never reaches disk.
    if rawfile_dangling:
        print(f"HARD STOP (R1): {len(rawfile_dangling)} RawDataFile edge endpoint(s) did "
              f"not resolve to a surviving composite node after Pass 6 rewrite. "
              f"No output written. First few: {rawfile_dangling[:5]}")
        return 1

    # FLAGS edges (Advisory -> RawDataFile) join the output as their own file. They
    # are built from final composite ids + minted advisory ids (both in surviving_ids),
    # so they need no rewrite; assert that invariant before writing.
    if flags_edges:
        bad_flags = [e for e in flags_edges
                     if e["subject_id"] not in surviving_ids or e["object_id"] not in surviving_ids]
        if bad_flags:
            print(f"HARD STOP (R2): {len(bad_flags)} FLAGS edge(s) reference a non-surviving "
                  f"node. No output written. First few: {bad_flags[:5]}")
            return 1
        rels_out["advisory_relationships.jsonl"] = flags_edges

    # --- Pass 7: write outputs ---------------------------------------
    total_out = sum(len(records) for records in entities_by_file.values())
    rawfile_out = sum(1 for records in entities_by_file.values()
                      for r in records if r.get("entity_type") == "RawDataFile")
    derived_out = sum(1 for rels in rels_out.values()
                      for r in rels if r.get("relationship_type") == "DERIVED_FROM")
    if not dry_run:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        for fname, records in entities_by_file.items():
            write_jsonl(OUTPUT_DIR / fname, records)
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
    print(f"  cross-file edges merged: {cross_file_merges}  (E1/KI-12, source_type merged_csv_llm)")
    print(f"  cross-file findings:     {cross_file_findings}  (unexpected multi-source; NOT merged)")
    print(f"  dangling edges withheld: {dangling}  (see review_queue.jsonl)")
    print(f"  review queue entries:    {len(review)}")
    print("  --- KI-8 remediation (R1/R2) ---")
    print(f"  RawDataFile composite ids minted: {composite_events}")
    print(f"  RawDataFile nodes out:            {rawfile_out}")
    print(f"  Advisory nodes:                   {len(advisory_nodes)}")
    print(f"  FLAGS edges:                      {len(flags_edges)}")
    print(f"  RawDataFile edge endpoints:       {rawfile_endpoints_ok}/{rawfile_endpoints_total} "
          f"rewritten onto composite (dangling {len(rawfile_dangling)})")
    print(f"  DERIVED_FROM edges out:           {derived_out}")
    if dry_run:
        print("  output written to:       [--dry-run: NOTHING written]")
    else:
        print(f"  output written to:       {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Normalize extracted SciKG data (stage 03).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Run all passes and print the summary but write no files.")
    cli = ap.parse_args()
    sys.exit(main(dry_run=cli.dry_run))
