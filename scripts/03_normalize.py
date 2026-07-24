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
import collections
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

# ORCID canonicalization — DISABLED 2026-07-23 by ruling. NOT a feature awaiting
# activation: do not flip this back without a new ruling. See SCIKG_SCHEMA.md
# "Node: Researcher -> ORCID (Added 2026-07-23)".
#
# ORCIDs are now populated as PROPERTIES on Researcher nodes (from CrossRef
# structured metadata). The ruling is properties only — node identifiers are NOT
# repointed. With this enabled, Pass 3 below retires researcher:* to orcid:* and
# rewrites AUTHORED_BY endpoints through the crosswalk; because 05 is MERGE-only
# and cannot retire the superseded nodes (KI-14), that would mint a DUPLICATE
# Researcher node set at orcid:* identifiers with authorship split across both,
# instead of setting a property on the existing nodes.
ENABLE_ORCID_CANONICALIZATION = False

# Instrument identifiers are left stable in this draft; canonical_name and
# psi_ms_id are filled into properties instead of re-minting the identifier.
# Re-minting to a canonical instrument ID (and rewriting USES_INSTRUMENT edges
# through the crosswalk) is a deliberate future option, not assumed here.
REMINT_INSTRUMENT_IDS = False

# ---------------- instrument typo/spacing dedup (Pass 4.5) -----------
# Table-driven, EXACT-slug retirements of OCR/spacing variants that the PDF
# instrument transform's signature-collapse mechanically missed. Each pair is
# the SAME physical instrument spelled two ways (reviewed against
# data/processed/review/instrument_review.md; verification pass 2026-07-21).
# Matching is EXACT identifier only — NEVER substring: shimadzu_toc_l_cph_cpn
# contains "lcph" and must never be swept in. DELIBERATELY EXCLUDED (deferred to
# David): the generics ruling (ft_icr/fticr/ft_icr_ms/fticr_ms/fticrms) and the
# ltq_velos hybrid-vs-ion-trap question. No magnet-strength node is touched.
INSTRUMENT_TYPO_MERGES = [
    # (retire_variant_id, survivor_id)  — survivor is an EXISTING live node.
    ("instrument:raw:custombuilt_hybrid_linear_ion_trap_ft_icr_ms",
     "instrument:raw:custom_built_hybrid_linear_ion_trap_ft_icr_ms"),           # grp 1
    ("instrument:raw:doc_labor_lc_ocd_sizeexclusion_chromatography_system",
     "instrument:raw:doc_labor_lc_ocd_size_exclusion_chromatography_system"),   # grp 2
    ("instrument:raw:inductively_coupled_plasma_highresolution_mass_spectrom",
     "instrument:raw:inductively_coupled_plasma_high_resolution_mass_spectro"),  # grp 6 (survivor slug is truncated at 60 chars — the exact live form)
    ("instrument:raw:pegasus_gchrt_4d",
     "instrument:raw:pegasus_gc_hrt_4d"),                                        # grp 7
    ("instrument:raw:shimadzu_toc_lcph_analyzer",
     "instrument:raw:shimadzu_toc_l_cph_analyzer"),                             # grp 8 (TOC-L CPH spacing)
    ("instrument:raw:shimadzu_tocl_cph_analyzer",
     "instrument:raw:shimadzu_toc_l_cph_analyzer"),                             # grp 8
    ("instrument:raw:shimadzu_toclcph_analyzer",
     "instrument:raw:shimadzu_toc_l_cph_analyzer"),                             # grp 8
    ("instrument:raw:spectrum_two_ftir_spectrophotometer",
     "instrument:raw:spectrum_two_ft_ir_spectrophotometer"),                    # grp 9
]

# Group 5 — BOTH live slugs are OCR-defective (one has the "cyclo_tron" break,
# the other "fouriertransform" run-together), so neither is an acceptable
# survivor. Retire BOTH onto a NEW clean canonical id. This repairs ONE hi-res
# descriptor spelled two broken ways; it is NOT the deferred bare-generic FT-ICR
# collapse (the id is the full hi-res phrase, not ft_icr/fticr/ft_icr_ms).
INSTRUMENT_TYPO_NEW_SURVIVOR = {
    "survivor_id": ("instrument:raw:high_resolution_fourier_transform_ion_"
                    "cyclotron_resonance_mass_spectrometer"),
    "survivor_name": ("High-Resolution Fourier Transform Ion Cyclotron "
                      "Resonance Mass Spectrometry"),
    "retire": [
        "instrument:raw:high_resolution_fourier_transform_ion_cyclo_tron_resona",
        "instrument:raw:high_resolution_fouriertransform_ion_cyclotron_resonanc",
    ],
}

# Guardrail: no slug in the typo tables may be a protected node — the 21T node
# or any magnet-strength node. (The bare-generic FT-ICR nodes and the ltq_velos
# family are NO LONGER protected here: David authorized the FT-ICR collapse
# (Op1) and the Velos split (Op2), which are handled by their own passes below.)
# Pass 4.5 HARD-STOPS if a typo/Op1 table touches a protected slug.
INSTRUMENT_DEDUP_PROTECTED = {
    "instrument:raw:21t_icr",
}
# A magnet-strength token in a slug: e.g. 4t_, 5_6t_, 9_4t_, 12t_, 21t_ (tesla).
MAGNET_TOKEN_RE = re.compile(r"(^|_)\d+(_\d+)?t(_|$)")

# ---------------- Op1: FT-ICR generic collapse (David-authorized) ---
# The 13 Bucket-A generic FT-ICR spelling variants collapse into ONE node,
# canonicalized to MS:1003948 (FT-ICR instrument class). Qualifier- (hi-res),
# magnet-, vendor-, and ionization-specific FT-ICR nodes stay SEPARATE
# (verification 2026-07-21). EXACT slug only. name_raw accumulated (lossless).
INSTRUMENT_GENERIC_COLLAPSE = {
    "survivor_id": "instrument:raw:ft_icr_ms",
    "canonical_name": "FT-ICR MS",
    "psi_ms_id": "MS:1003948",
    "retire": [
        "instrument:raw:fourier_transform_ion_cyclotron_resonance_mass_spectrom",
        "instrument:raw:fticr_ms",
        "instrument:raw:ft_icr_mass_spectrometer",
        "instrument:raw:ft_icr",
        "instrument:raw:ft_icr_mass_spectrometry",
        "instrument:raw:ion_cyclotron_resonance_mass_analyzer",
        "instrument:raw:fticrms",
        "instrument:raw:ft_icr_mass_analyzer",
        "instrument:raw:ft_icr_ms_instrument",
        "instrument:raw:fticr",
        "instrument:raw:fourier_transform_ion_cyclotron_resonance",
        "instrument:raw:fourier_ion_cyclotron_resonance_mass_spectrometer",
    ],
}

# ---------------- Op2: Velos split (David-authorized) ---------------
# LTQ Orbitrap Velos (hybrid) and LTQ Velos / Velos Pro (plain ion traps) are
# DIFFERENT instruments. The PDF signature-collapse conflated them into two
# nodes; split by per-EDGE reassignment keyed on (paper_doi, source_node) ->
# target, because the disambiguating verbatim lives only in pdf_extraction, not
# on the edge. name_raw per target is CURATED (not blind-accumulated) so the
# conflated node's mixed strings do not cross-contaminate the split.
INSTRUMENT_VELOS_SPLIT = {
    "targets": {
        "instrument:raw:ltq_orbitrap_velos": {
            "new": True, "template": "instrument:raw:ltq_orbitrapvelos",
            "canonical_name": "LTQ Orbitrap Velos", "psi_ms_id": "MS:1001742",
            "name_raw": ["LTQ Orbitrap Velos", "LTQ OrbitrapVelos",
                         "LTQ Orbitrap Velos (Thermo Fisher Scientific)",
                         "Velos LTQ-Orbitrap Mass Spectrometer", "Orbitrap Velos Pro"],
        },
        "instrument:raw:ltq_velos": {
            "new": True, "template": "instrument:raw:ltq_velos_ion_trap_mass_spectrometer",
            "canonical_name": "LTQ Velos", "psi_ms_id": None,
            "name_raw": ["LTQ Velos", "LTQ-Velos",
                         "LTQ Velos ion trap mass spectrometer", "Velos"],
        },
        "instrument:raw:velos_pro_linear_ion_trap": {
            "new": False,
            "canonical_name": "Velos Pro", "psi_ms_id": "MS:1003495",
            "name_raw": ["Velos Pro", "Velos Pro linear ion trap",
                         "custom-built Velos Pro",
                         "Velos Pro dual cell rf ion trap assembly",
                         "Velos-Pro dual cell linear RF ion trap",
                         "Velos Pro dualcell linear ion trap",
                         "modified Velos Pro linear ion trap assembly"],
        },
    },
    # Per-edge reassignment: (paper_doi, current_object_node) -> target_node.
    "edge_moves": [
        ("doi:10.1021/jp503413s", "instrument:raw:ltq_orbitrapvelos", "instrument:raw:ltq_orbitrap_velos"),
        ("doi:10.1002/pmic.201300438", "instrument:raw:ltq_velos_ion_trap_mass_spectrometer", "instrument:raw:ltq_orbitrap_velos"),
        ("doi:10.1016/j.str.2017.08.002", "instrument:raw:ltq_velos_ion_trap_mass_spectrometer", "instrument:raw:ltq_orbitrap_velos"),
        ("doi:10.1007/s13361-019-02290-8", "instrument:raw:velos_pro_linear_ion_trap", "instrument:raw:ltq_orbitrap_velos"),
        ("doi:10.1002/jms.3345", "instrument:raw:ltq_velos_ion_trap_mass_spectrometer", "instrument:raw:ltq_velos"),
        ("doi:10.1016/j.chroma.2016.10.005", "instrument:raw:ltq_velos_ion_trap_mass_spectrometer", "instrument:raw:ltq_velos"),
        ("doi:10.1074/jbc.m116.719591", "instrument:raw:ltq_velos_ion_trap_mass_spectrometer", "instrument:raw:ltq_velos"),
        ("doi:10.3390/life11030234", "instrument:raw:ltq_velos_ion_trap_mass_spectrometer", "instrument:raw:ltq_velos"),
        ("doi:10.1002/jms.3345", "instrument:raw:velos", "instrument:raw:ltq_velos"),
        ("doi:10.1021/jasms.4c00261", "instrument:raw:velos_pro_dual_cell_linear_rf_ion_trap", "instrument:raw:velos_pro_linear_ion_trap"),
        ("doi:10.1007/s13361-017-1702-3", "instrument:raw:velos_pro_dual_cell_rf_ion_trap_assembly", "instrument:raw:velos_pro_linear_ion_trap"),
        ("doi:10.1021/acs.energyfuels.4c05674", "instrument:raw:velos_pro_dualcell_linear_ion_trap", "instrument:raw:velos_pro_linear_ion_trap"),
        ("doi:10.1016/j.jbc.2022.102768", "instrument:raw:modified_velos_pro_linear_ion_trap_assembly", "instrument:raw:velos_pro_linear_ion_trap"),
    ],
    # Source nodes expected EMPTY after reassignment -> retire (remove record).
    "retire_if_empty": [
        "instrument:raw:ltq_orbitrapvelos",
        "instrument:raw:ltq_velos_ion_trap_mass_spectrometer",
        "instrument:raw:velos",
        "instrument:raw:velos_pro_dual_cell_linear_rf_ion_trap",
        "instrument:raw:velos_pro_dual_cell_rf_ion_trap_assembly",
        "instrument:raw:velos_pro_dualcell_linear_ion_trap",
        "instrument:raw:modified_velos_pro_linear_ion_trap_assembly",
    ],
    # Explicitly NOT part of the split (plain LTQ Orbitrap, not a Velos).
    "excluded": ["instrument:raw:ltqorbitrap"],
}

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
    # Distinct Instrument identifiers on input (pre-dedup) — for the typo-dedup report.
    inst_in = len({rec["identifier"]
                   for recs in entities_by_file.values() for rec in recs
                   if rec.get("entity_type") == "Instrument"})
    uses_in = sum(1 for recs in rels_by_file.values() for r in recs
                  if r.get("relationship_type") == "USES_INSTRUMENT")

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

    # --- Pass 4.5: instrument typo/spacing dedup (table-driven, EXACT slug) ---
    # Seed crosswalk retirements for OCR/spacing variants the PDF signature-collapse
    # missed. The terminal-merge fold below rewrites node identity; Pass 6 rewrites
    # USES_INSTRUMENT edge endpoints onto the survivor. EXACT-slug only (never
    # substring). Generics + ltq_velos excluded; no magnet-strength node touched.
    inst_ids_now = {rec["identifier"]
                    for recs in entities_by_file.values() for rec in recs
                    if rec.get("entity_type") == "Instrument"}

    def _guard_dedup_slug(slug):
        """Refuse to touch a protected or magnet-strength slug. Returns True if OK."""
        if slug in INSTRUMENT_DEDUP_PROTECTED:
            print(f"HARD STOP (instrument dedup): protected slug in merge table: "
                  f"{slug!r}. No output written.")
            return False
        if MAGNET_TOKEN_RE.search(slug.replace("instrument:raw:", "")):
            print(f"HARD STOP (instrument dedup): magnet-strength token in merge slug: "
                  f"{slug!r}. No output written.")
            return False
        return True

    typo_events = 0
    survivor_to_retired = defaultdict(list)   # survivor_id -> [retired_id, ...]
    # Lossless: name_raw strings of every retired node, captured BEFORE the fold
    # (which keeps only the survivor's name_raw), accumulated per survivor.
    alias_accumulate = defaultdict(list)

    def _capture_aliases(node_id, survivor_id):
        rec = next((r for recs in entities_by_file.values() for r in recs
                    if r.get("identifier") == node_id), None)
        nr = (rec.get("properties") or {}).get("name_raw") if rec else None
        for s in (nr if isinstance(nr, list) else [nr] if nr else []):
            if s and s not in alias_accumulate[survivor_id]:
                alias_accumulate[survivor_id].append(s)

    # (a) Standard pairs — both variant and survivor must be live Instrument nodes.
    for variant, survivor in INSTRUMENT_TYPO_MERGES:
        for slug in (variant, survivor):
            if not _guard_dedup_slug(slug):
                return 1
        if variant not in inst_ids_now:
            print(f"HARD STOP (instrument dedup): retire slug is not a live Instrument "
                  f"node: {variant!r}. No output written.")
            return 1
        if survivor not in inst_ids_now:
            print(f"HARD STOP (instrument dedup): survivor slug is not a live Instrument "
                  f"node: {survivor!r}. No output written.")
            return 1
        _capture_aliases(variant, survivor)
        crosswalk.retire(variant, survivor)
        survivor_to_retired[survivor].append(variant)
        typo_events += 1
        log.append({"action": "instrument_typo_merge", "retired": variant,
                    "survivor": survivor, "at": now_iso()})

    # (a2) Op1 — FT-ICR generic collapse into the existing ft_icr_ms survivor.
    gc = INSTRUMENT_GENERIC_COLLAPSE
    fticr_survivor = gc["survivor_id"]
    if not _guard_dedup_slug(fticr_survivor):
        return 1
    if fticr_survivor not in inst_ids_now:
        print(f"HARD STOP (FT-ICR collapse): survivor {fticr_survivor!r} is not a live "
              f"Instrument node. No output written.")
        return 1
    fticr_retired = []
    for variant in gc["retire"]:
        if not _guard_dedup_slug(variant):
            return 1
        if variant not in inst_ids_now:
            print(f"HARD STOP (FT-ICR collapse): retire slug {variant!r} is not a live "
                  f"Instrument node. No output written.")
            return 1
        _capture_aliases(variant, fticr_survivor)
        crosswalk.retire(variant, fticr_survivor)
        survivor_to_retired[fticr_survivor].append(variant)
        fticr_retired.append(variant)
        log.append({"action": "instrument_fticr_collapse", "retired": variant,
                    "survivor": fticr_survivor, "at": now_iso()})

    # (b) Group 5 — retire BOTH OCR-defective slugs onto a NEW clean canonical id.
    # Capture the original verbatim strings BEFORE the fold (merge_entities keeps
    # only the survivor's name_raw), so Pass 4.6 can preserve both as provenance.
    g5 = INSTRUMENT_TYPO_NEW_SURVIVOR
    if not _guard_dedup_slug(g5["survivor_id"]):
        return 1
    g5_live = [v for v in g5["retire"] if v in inst_ids_now]
    g5_originals = []
    if g5_live:
        if g5["survivor_id"] in inst_ids_now:
            print(f"HARD STOP (instrument dedup): group-5 clean survivor already exists as "
                  f"a live node: {g5['survivor_id']!r}. No output written.")
            return 1
        for v in g5["retire"]:
            if not _guard_dedup_slug(v):
                return 1
        for v in g5_live:
            rec = next((r for recs in entities_by_file.values() for r in recs
                        if r.get("identifier") == v), None)
            nr = (rec.get("properties") or {}).get("name_raw") if rec else None
            for s in (nr if isinstance(nr, list) else [nr] if nr else []):
                if s and s not in g5_originals:
                    g5_originals.append(s)
            crosswalk.retire(v, g5["survivor_id"])
            survivor_to_retired[g5["survivor_id"]].append(v)
            typo_events += 1
            log.append({"action": "instrument_typo_merge", "retired": v,
                        "survivor": g5["survivor_id"], "group": "g5_ocr_repair",
                        "at": now_iso()})
    log.append({"action": "instrument_typo_dedup_summary", "retired": typo_events,
                "survivors": len(survivor_to_retired), "at": now_iso()})

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

    # --- Pass 4.6: finalize the group-5 clean survivor name -----------
    # The fold merged the two OCR-defective records into the clean id but kept a
    # defective name_raw. Set the clean display form, PRESERVING both original
    # verbatim strings as provenance. No fabricated data — the clean form is the
    # same descriptor with the OCR damage repaired.
    if g5_live:
        found = False
        for recs in entities_by_file.values():
            for rec in recs:
                if rec.get("identifier") == g5["survivor_id"]:
                    props = rec.setdefault("properties", {})
                    props["name_raw"] = [g5["survivor_name"]] + [
                        o for o in g5_originals if o != g5["survivor_name"]]
                    found = True
                    log.append({"action": "instrument_typo_g5_name_set",
                                "identifier": g5["survivor_id"],
                                "clean_name": g5["survivor_name"],
                                "preserved_raw": g5_originals, "at": now_iso()})
        if not found:
            print(f"HARD STOP (instrument dedup): group-5 clean survivor "
                  f"{g5['survivor_id']!r} not present after fold. No output written.")
            return 1

    def _find_entity(ident):
        for recs in entities_by_file.values():
            for rec in recs:
                if rec.get("identifier") == ident:
                    return rec
        return None

    # Lossless name_raw accumulation onto every typo/Op1 survivor (append the
    # retired nodes' strings after the survivor's own, de-duplicated). The
    # group-5 survivor is excluded — it was set explicitly above.
    for survivor_id, extra in alias_accumulate.items():
        if survivor_id == g5["survivor_id"]:
            continue
        rec = _find_entity(survivor_id)
        if rec is None:
            continue
        props = rec.setdefault("properties", {})
        cur = props.get("name_raw")
        cur = list(cur) if isinstance(cur, list) else ([cur] if cur else [])
        for s in extra:
            if s not in cur:
                cur.append(s)
        props["name_raw"] = cur

    # Op1 — set the FT-ICR survivor's canonical name + accession directly (the
    # generic phrase is not in the Instruments CV, so Pass 5 leaves it unmapped;
    # this is the authoritative assignment, David-ruled MS:1003948).
    _fticr = _find_entity(fticr_survivor)
    if _fticr is not None:
        _fp = _fticr.setdefault("properties", {})
        _fp["canonical_name"] = gc["canonical_name"]
        _fp["psi_ms_id"] = gc["psi_ms_id"]
        log.append({"action": "instrument_fticr_collapse_finalize",
                    "survivor": fticr_survivor, "canonical_name": gc["canonical_name"],
                    "psi_ms_id": gc["psi_ms_id"], "retired": len(fticr_retired),
                    "at": now_iso()})

    # --- Pass 4.7: Velos split (per-edge reassignment, Op2) -----------
    # NOT node retirement: the conflated nodes send different edges to different
    # targets by (paper_doi, source_node). Create the target nodes, rewrite the
    # matching edge object_ids, then retire the emptied source nodes. Every move
    # must match EXACTLY one live edge and every retire_if_empty node must reach
    # zero edges, else HARD STOP (a silent miss would orphan an edge).
    vs = INSTRUMENT_VELOS_SPLIT
    # (i) Create the two new target node records from a template (deep-ish copy),
    # overriding identity/name/accession. Provenance carries from the template
    # (a real PDF extraction), which is honest — the node is derived, not invented.
    velos_new_created = []
    for tid, spec in vs["targets"].items():
        if not spec.get("new"):
            continue
        if _find_entity(tid) is not None:
            print(f"HARD STOP (Velos split): new target {tid!r} already exists. "
                  f"No output written.")
            return 1
        tmpl = _find_entity(spec["template"])
        if tmpl is None:
            print(f"HARD STOP (Velos split): template {spec['template']!r} for {tid!r} "
                  f"not found. No output written.")
            return 1
        newrec = dict(tmpl)
        newrec["identifier"] = tid
        newprops = dict(tmpl.get("properties") or {})
        newprops["name_raw"] = list(spec["name_raw"])
        newprops["canonical_name"] = spec["canonical_name"]
        newprops["psi_ms_id"] = spec["psi_ms_id"]
        newrec["properties"] = newprops
        # Instrument nodes live in pdf_entities.jsonl; add the new record there.
        entities_by_file.setdefault("pdf_entities.jsonl", []).append(newrec)
        velos_new_created.append(tid)
        log.append({"action": "velos_split_new_node", "identifier": tid,
                    "template": spec["template"], "psi_ms_id": spec["psi_ms_id"],
                    "at": now_iso()})

    # (ii) Curate name_raw + accession on the reused Velos Pro survivor.
    for tid, spec in vs["targets"].items():
        if spec.get("new"):
            continue
        rec = _find_entity(tid)
        if rec is None:
            print(f"HARD STOP (Velos split): reused target {tid!r} not found. "
                  f"No output written.")
            return 1
        p = rec.setdefault("properties", {})
        p["name_raw"] = list(spec["name_raw"])
        p["canonical_name"] = spec["canonical_name"]
        p["psi_ms_id"] = spec["psi_ms_id"]

    # (iii) Per-edge reassignment on the relationship records. Match on
    # canonicalized DOI + exact source object_id; each move must hit exactly one.
    velos_move_hits = collections.Counter()
    for rels in rels_by_file.values():
        for rel in rels:
            if rel.get("relationship_type") != "USES_INSTRUMENT":
                continue
            subj = canonicalize_identifier(rel.get("subject_id"))
            obj = rel.get("object_id")
            for mv_doi, mv_from, mv_to in vs["edge_moves"]:
                if obj == mv_from and subj == canonicalize_identifier(mv_doi):
                    rel["object_id"] = mv_to
                    velos_move_hits[(mv_doi, mv_from, mv_to)] += 1
                    log.append({"action": "velos_split_edge_move", "doi": mv_doi,
                                "from": mv_from, "to": mv_to, "at": now_iso()})
                    break
    bad_moves = [m for m in vs["edge_moves"] if velos_move_hits.get(m, 0) != 1]
    if bad_moves:
        print(f"HARD STOP (Velos split): {len(bad_moves)} edge move(s) did not match "
              f"exactly one edge. No output written. First few: "
              f"{[(m[0], m[1].replace('instrument:raw:',''), velos_move_hits.get(m,0)) for m in bad_moves[:5]]}")
        return 1

    # (iv) Retire the emptied source nodes — assert each now has ZERO edges.
    remaining = collections.Counter()
    for rels in rels_by_file.values():
        for rel in rels:
            remaining[rel.get("object_id")] += 1
            remaining[rel.get("subject_id")] += 1
    still_referenced = [n for n in vs["retire_if_empty"] if remaining.get(n, 0) > 0]
    if still_referenced:
        print(f"HARD STOP (Velos split): retire_if_empty nodes still have edges: "
              f"{[(n.replace('instrument:raw:',''), remaining[n]) for n in still_referenced]}. "
              f"No output written.")
        return 1
    velos_retired = []
    for fname, records in entities_by_file.items():
        kept = [r for r in records if r.get("identifier") not in vs["retire_if_empty"]]
        if len(kept) != len(records):
            velos_retired += [r["identifier"] for r in records
                              if r.get("identifier") in vs["retire_if_empty"]]
            entities_by_file[fname] = kept
    log.append({"action": "velos_split_summary", "new_nodes": velos_new_created,
                "retired_nodes": velos_retired, "edge_moves": len(vs["edge_moves"]),
                "at": now_iso()})

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

    # --- Pass 5.6: force the David-ruled accessions (win over CV) ------
    # Op1/Op2 accessions are authoritative rulings; re-assert them AFTER Pass 5 so
    # a CV alias match can never overwrite them. (For the hybrid + Velos Pro nodes
    # Pass 5 already lands the same value; this is bulletproofing, not a change.)
    _force = {gc["survivor_id"]: (gc["canonical_name"], gc["psi_ms_id"])}
    for tid, spec in INSTRUMENT_VELOS_SPLIT["targets"].items():
        _force[tid] = (spec["canonical_name"], spec["psi_ms_id"])
    for records in entities_by_file.values():
        for rec in records:
            if rec.get("identifier") in _force:
                cn, psi = _force[rec["identifier"]]
                p = rec.setdefault("properties", {})
                p["canonical_name"] = cn
                p["psi_ms_id"] = psi

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

    # --- instrument typo/spacing dedup report (safe OCR/spacing merges) ---
    if survivor_to_retired:
        inst_out = len({rec["identifier"]
                        for recs in entities_by_file.values() for rec in recs
                        if rec.get("entity_type") == "Instrument"})
        uses_out = sum(1 for rels in rels_out.values() for r in rels
                       if r.get("relationship_type") == "USES_INSTRUMENT")
        uses_out_by_obj = defaultdict(int)
        for rels in rels_out.values():
            for r in rels:
                if r.get("relationship_type") == "USES_INSTRUMENT":
                    uses_out_by_obj[r.get("object_id")] += 1
        alive_ids = {rec["identifier"]
                     for recs in entities_by_file.values() for rec in recs}
        print("  --- instrument dedup: 3 operations ---")
        print(f"  instrument nodes:        {inst_in} -> {inst_out}  "
              f"(net {inst_out - inst_in})")

        print("  [Op typo] 6 groups + group-5 clean node:")
        for survivor in sorted(survivor_to_retired):
            if survivor == fticr_survivor:
                continue
            retired = survivor_to_retired[survivor]
            short = survivor.replace("instrument:raw:", "")
            print(f"    survivor {short}  (+{len(retired)}) "
                  f"-> USES_INSTRUMENT now {uses_out_by_obj.get(survivor, 0)}")

        print("  [Op1 FT-ICR generic collapse]:")
        print(f"    survivor {fticr_survivor.replace('instrument:raw:','')}  "
              f"(+{len(fticr_retired)} retired) -> USES_INSTRUMENT now "
              f"{uses_out_by_obj.get(fticr_survivor, 0)}  "
              f"[canonical_name/psi_ms_id set: {gc['psi_ms_id']}]")
        for v in fticr_retired:
            print(f"        retired {v.replace('instrument:raw:', '')}")

        print("  [Op2 Velos split] target edge counts + retired sources:")
        for tid in ("instrument:raw:ltq_orbitrap_velos",
                    "instrument:raw:velos_pro_linear_ion_trap",
                    "instrument:raw:ltq_velos"):
            spec = INSTRUMENT_VELOS_SPLIT["targets"][tid]
            print(f"    {tid.replace('instrument:raw:','')}  "
                  f"({'new' if spec.get('new') else 'reused'}, psi={spec['psi_ms_id']}) "
                  f"-> USES_INSTRUMENT now {uses_out_by_obj.get(tid, 0)}")
        print(f"    retired (emptied) source nodes: "
              f"{[n.replace('instrument:raw:','') for n in velos_retired]}")
        excl = INSTRUMENT_VELOS_SPLIT['excluded'][0]
        print(f"    EXCLUDED (untouched): {excl.replace('instrument:raw:','')}="
              f"{'live' if excl in alive_ids else 'GONE!'} "
              f"({uses_out_by_obj.get(excl,0)} edge)")

        print(f"  USES_INSTRUMENT edges:   {uses_in} -> {uses_out}  "
              f"(net drop {uses_in - uses_out}; cross-file merges + same-paper dups only)")

        # Guardrails — must all hold.
        g5id = INSTRUMENT_TYPO_NEW_SURVIVOR["survivor_id"]
        magnets = ["instrument:raw:3t_ft_icr", "instrument:raw:4t_ft_icr",
                   "instrument:raw:5t_ft_icr", "instrument:raw:5_6t_ft_icr",
                   "instrument:raw:7t_ft_icr", "instrument:raw:9_4t_ft_icr",
                   "instrument:raw:9_4_ft_icr_mass_spectrometer",
                   "instrument:raw:12t_ft_icr", "instrument:raw:12_0t_ft_icr",
                   "instrument:raw:14_5t_ft_icr", "instrument:raw:21t_icr"]
        quals = ["instrument:raw:ultra_high_resolution_ft_icr_ms",
                 "instrument:raw:ultrahigh_resolution_ft_icr_mass_spectrometer",
                 "instrument:raw:high_resolution_ft_icr_mass_spectrometer",
                 "instrument:raw:lower_field_ft_icr_ms",
                 "instrument:raw:bruker_solarix_ft_icr_ms"]
        print(f"  guardrails: 21T={'live' if 'instrument:raw:21t_icr' in alive_ids else 'GONE!'}"
              f"({uses_out_by_obj.get('instrument:raw:21t_icr',0)}), "
              f"all magnets live={all(m in alive_ids for m in magnets)}, "
              f"qualifier FT-ICR live={all(q in alive_ids for q in quals)}, "
              f"group-5 hi-res live={g5id in alive_ids}")
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
