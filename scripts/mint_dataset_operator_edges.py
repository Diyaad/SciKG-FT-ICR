#!/usr/bin/env python3
"""
mint_dataset_operator_edges.py — the missing pipeline step that reconciles two
minting gaps, written so a full reload will not recreate the gap.

Two gaps this closes
--------------------
(1) PDF-extracted `dataset_accession` was never turned into
    Publication -[:HAS_DATASET]-> Dataset. Papers therefore sit disconnected
    from deposits they explicitly cite — e.g. `10.1126/science.aaz5284`'s PDF
    cites `PXD026123`, which ALREADY EXISTS as a Dataset node, but no edge links
    them. This script reconciles the cited accession to the existing node.

(2) FOXDEN `instrumentMethod.Creator` (the only populated operator signal on the
    Blood Proteoform Atlas PXD raw files) was never turned into
    RawDataFile -[:OPERATED_BY]-> Researcher. 888 PXD RawDataFiles carry zero
    operators; 243 of them have a creator handle that CAN be minted honestly.

Design contract (non-negotiable)
--------------------------------
- DEFAULT IS DRY-RUN. Nothing is written unless invoked with `--apply`.
- Phase 1 (default) reads sources, classifies every (paper, accession) pair into
  exactly one disposition (LINK / MINT / REVIEW), inventories operator edges, and
  writes a REVIEWABLE ledger (`proposed_dataset_operator_edges.jsonl`) plus a
  human report. It EXECUTES NOTHING against the graph.
- Phase 2 (`--apply`) reads that same ledger and MERGEs ONLY the rows whose
  `apply` flag is true. Every REVIEW row is written with `apply: false`, so
  `--apply` skips them unless a human flips the flag. FUZZY PROPOSES, HUMAN
  DISPOSES: the ledger is the disposition record; edit it to scope the apply.
- NO FABRICATION. Every minted node/edge carries all six universal provenance
  properties (SCIKG_SCHEMA.md). `evidence_note` is the grounded PDF snippet or
  the exact FOXDEN field — never inferred. Missing values are null, not guessed.
- NEVER reconcile a raw operator handle to a CSV author node. Operator identities
  are minted AS-IS (`researcher:{handle}`); surname look-alikes are reported as a
  human-only follow-up, never merged here.
- NEVER fuzzy-merge across accession schemes (PXD / MSV / MassIVE-DOI). Only an
  EXACT normalized-key match links to an existing node; anything cross-scheme is
  REVIEW, untouched.
- MERGE (never CREATE); ON CREATE SET the provenance block so existing properties
  are never overwritten and a re-run is a true no-op.

This script does NO git. It reports what changed; the human commits.

Usage
-----
    python scripts/mint_dataset_operator_edges.py            # Phase 1 dry-run
    python scripts/mint_dataset_operator_edges.py --offline  # dry-run, disk only
    python scripts/mint_dataset_operator_edges.py --apply    # Phase 2 (after review)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# scripts/db.py — connection layer ONLY (connect / run_query / close). Credentials
# come from .env via db.load_dotenv(); this script never reads or echoes them.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import db  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
PDF_EXTRACTION = REPO / "data/raw/pdf_extraction/pdf_extraction_378papers.jsonl"
VALIDATED = REPO / "data/processed/validated/entities"
# Pre-normalize inputs — where emitted records must land so 03->04->05 recreate
# them on a clean rebuild (graph = f(files)). Fixed filenames so re-emission is
# idempotent and a reviewer knows exactly which files carry the reconciliation.
ENTITIES_DIR = REPO / "data/processed/entities"
RELATIONSHIPS_DIR = REPO / "data/processed/relationships"
EMIT_ENTITIES_NAME = "pdf_dataset_entities.jsonl"
EMIT_RELATIONSHIPS_NAME = "pdf_dataset_relationships.jsonl"
DATASETS_DISK = VALIDATED / "datasets.jsonl"
RAWFILES_PXD_DISK = VALIDATED / "rawfiles_pxd.jsonl"
PUBLICATIONS_DISK = VALIDATED / "publications.jsonl"
REVIEW_DIR = REPO / "data/processed/review"
LEDGER = REVIEW_DIR / "proposed_dataset_operator_edges.jsonl"
REPORT = REVIEW_DIR / "mint_edges_phase1_report.md"

SCHEMA_VERSION = "v1.0"
PROVENANCE_PROPS = (
    "source_type", "confidence", "extracted_at",
    "evidence_note", "source_id", "schema_version",
)

# --------------------------------------------------------------------------- #
# Accession normalization — PROPOSE, never silently hardcode.
#
# Each cited accession string is scanned for known repository patterns. Every
# match yields a canonical KEY (`scheme:value`) used for cross-scheme-safe
# matching, plus the identifier we would MINT if no node already carries that key.
# Two representations of one deposit (e.g. `https://osf.io/4azm8/` and
# `DOI 10.17605/OSF.IO/4AZM8`) normalize to the SAME key and collapse to one row.
#
# `mintable` gates the disposition when no existing node matches:
#   unambiguous   -> MINT (clean accession, established namespace)
#   new_namespace -> MINT but FLAG the proposed namespace for approval
#   review        -> REVIEW (may be the same deposit as an existing node under a
#                    different scheme; a bridge cannot be proven mechanically)
# --------------------------------------------------------------------------- #

# Patterns are tolerant of the OCR artefacts observed in existing identifiers
# (stray spaces after '.' and around '/').
# OSF matches the URL form (osf.io/CODE), the bare form (OSF.IO/CODE), and the
# DOI form (10.17605/OSF.IO/CODE). The optional `10.17605/` prefix is CONSUMED so
# the catch-all DOI scanner does not re-flag the same deposit as unrecognized.
_OSF = re.compile(r"(?:10\.17605\s*/\s*)?OSF\.?\s*IO\s*/\s*([A-Za-z0-9]{5})", re.I)
_PXD = re.compile(r"PXD\s*_?\s*(\d{6,})", re.I)
_MSV = re.compile(r"MSV\s*(\d{9})", re.I)
_ZENODO = re.compile(r"zenodo[.\s/]+(\d{5,})", re.I)
_MENDELEY = re.compile(r"10\.17632/\s*([A-Za-z0-9]+(?:\.\d+)?)", re.I)
_IEDA = re.compile(r"10\.26022/\s*IEDA\s*/\s*(\d+)", re.I)
_HYDROSHARE = re.compile(r"10\.4211/\s*hs\.?\s*([A-Za-z0-9]+)", re.I)
_USGS = re.compile(r"10\.5066/\s*([A-Za-z0-9]+)", re.I)
_PASTA = re.compile(r"10\.6073/\s*pasta/\s*([A-Za-z0-9]+)", re.I)
_SRA = re.compile(r"\b(SR[PRXZ]\d{6,})\b", re.I)
_BIOPROJECT = re.compile(r"\b(PRJ[A-Z]{2}\d+)\b")
_BCODMO = re.compile(r"BCO-?DMO\s*/?\s*(\d+)", re.I)
# Any DOI at all — the last-resort catch used only to flag DOIs that no specific
# handler recognized, so nothing is ever silently dropped.
_ANY_DOI = re.compile(r"10\.\d{4,}/\s*\S+", re.I)


def _urls(text: str) -> list[str]:
    return re.findall(r"https?://\S+", text or "")


def _source_url_for(raw: str, needle: str) -> str | None:
    """Return the URL in `raw` that contains `needle` (the accession value), if
    any — the honest source URL. Never fabricated: null when no URL carries it."""
    n = needle.replace(" ", "").lower()
    for u in _urls(raw):
        if n in u.replace(" ", "").lower():
            return u.rstrip(".,;)")
    return None


def normalize_accessions(raw: str) -> list[dict]:
    """Scan one cited `dataset_accession` string; return one dict per distinct
    deposit found. Keys returned per entry:
        scheme, key, accession, repository, mint_identifier, mintable, source_url
    """
    out: dict[str, dict] = {}   # canonical key -> entry (dedupes within a value)
    covered_spans: list[tuple[int, int]] = []

    def add(scheme, key, accession, repository, mint_identifier, mintable, span):
        covered_spans.append(span)
        if key not in out:
            out[key] = {
                "scheme": scheme,
                "key": key,
                "accession": accession,
                "repository": repository,
                "mint_identifier": mint_identifier,
                "mintable": mintable,
                "source_url": _source_url_for(raw, accession),
            }

    for m in _PXD.finditer(raw):
        acc = "PXD" + m.group(1)
        add("proteomexchange", f"proteomexchange:{acc.lower()}", acc,
            "ProteomeXchange", f"dataset:proteomexchange:{acc.lower()}",
            "unambiguous", m.span())
    for m in _MSV.finditer(raw):
        acc = "MSV" + m.group(1)
        # MassIVE MSV accession may already exist as a MassIVE-DOI node
        # (dataset:other:10.25345/...). The MSV<->DOI bridge is not derivable
        # mechanically -> REVIEW, never a fuzzy merge.
        add("massive-msv", f"massive-msv:{acc.lower()}", acc,
            "MassIVE", f"dataset:massive:{acc.lower()}", "review", m.span())
    for m in _OSF.finditer(raw):
        code = m.group(1)
        add("osf", f"osf:{code.lower()}", code.upper(),
            "OSF", f"dataset:osf:{code.lower()}", "unambiguous", m.span())
    for m in _ZENODO.finditer(raw):
        n = m.group(1)
        add("zenodo", f"zenodo:{n}", n,
            "Zenodo", f"dataset:zenodo:{n}", "unambiguous", m.span())
    for m in _MENDELEY.finditer(raw):
        v = m.group(1).lower()
        add("mendeley", f"mendeley:{v}", f"10.17632/{v}",
            "Mendeley Data", f"dataset:other:10.17632/{v}", "unambiguous", m.span())
    for m in _IEDA.finditer(raw):
        n = m.group(1)
        add("ieda", f"ieda:{n}", f"10.26022/IEDA/{n}",
            "IEDA/EarthChem", f"dataset:other:10.26022/ieda/{n}", "unambiguous", m.span())
    for m in _HYDROSHARE.finditer(raw):
        h = m.group(1).lower()
        add("hydroshare", f"hydroshare:{h}", f"10.4211/hs.{h}",
            "HydroShare", f"dataset:other:10.4211/hs.{h}", "unambiguous", m.span())
    for m in _USGS.finditer(raw):
        v = m.group(1).lower()
        add("usgs", f"usgs:{v}", f"10.5066/{v}",
            "USGS ScienceBase", f"dataset:other:10.5066/{v}", "unambiguous", m.span())
    for m in _PASTA.finditer(raw):
        v = m.group(1).lower()
        add("pasta", f"pasta:{v}", f"10.6073/pasta/{v}",
            "EDI", f"dataset:other:10.6073/pasta/{v}", "unambiguous", m.span())
    for m in _SRA.finditer(raw):
        acc = m.group(1).upper()
        add("sra", f"sra:{acc.lower()}", acc,
            "NCBI SRA", f"dataset:sra:{acc.lower()}", "new_namespace", m.span())
    for m in _BIOPROJECT.finditer(raw):
        acc = m.group(1).upper()
        add("bioproject", f"bioproject:{acc.lower()}", acc,
            "NCBI BioProject", f"dataset:bioproject:{acc.lower()}", "new_namespace", m.span())
    for m in _BCODMO.finditer(raw):
        n = m.group(1)
        add("bco-dmo", f"bco-dmo:{n}", f"BCO-DMO {n}",
            "BCO-DMO", f"dataset:bco-dmo:{n}", "new_namespace", m.span())

    # Catch-all: any DOI a specific handler did NOT claim -> flag, never drop.
    for m in _ANY_DOI.finditer(raw):
        s, e = m.span()
        if any(cs <= s < ce or cs < e <= ce for cs, ce in covered_spans):
            continue
        val = m.group(0).replace(" ", "").rstrip(".,;)").lower()
        key = f"unrecognized:{val}"
        if key not in out:
            out[key] = {
                "scheme": "unrecognized", "key": key, "accession": val,
                "repository": "Other", "mint_identifier": f"dataset:other:{val}",
                "mintable": "review", "source_url": _source_url_for(raw, val),
            }
    return list(out.values())


def keys_from_identifier(identifier: str) -> list[str]:
    """Derive canonical match keys directly from an existing Dataset identifier
    (`dataset:{namespace}:{value}`). Covers the clean namespaces; the messy
    `dataset:other:...` DOIs are handled by re-normalizing accession/url text."""
    parts = identifier.split(":", 2)
    if len(parts) < 3 or parts[0] != "dataset":
        return []
    ns, val = parts[1], parts[2]
    ns_map = {
        "osf": "osf", "proteomexchange": "proteomexchange",
        "zenodo": "zenodo", "massive": "massive-msv",
    }
    if ns in ns_map:
        return [f"{ns_map[ns]}:{val.strip().lower()}"]
    return []


# --------------------------------------------------------------------------- #
# Loading existing graph state (LINK vs MINT truth). Prefers the live graph;
# falls back to the validated on-disk records (what 05 loaded) when --offline or
# the DB is unreachable. Reads only — never writes in Phase 1.
# --------------------------------------------------------------------------- #
def _iter_jsonl(path: Path):
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_existing_from_graph(driver):
    datasets = db.run_query(
        driver,
        "MATCH (d:Dataset) RETURN d.identifier AS id, d.accession AS acc, "
        "d.source_url AS url",
    )
    pubs = {r["id"] for r in db.run_query(
        driver, "MATCH (p:Publication) RETURN p.identifier AS id")}
    raws = {r["id"] for r in db.run_query(
        driver, "MATCH (r:RawDataFile) RETURN r.identifier AS id")}
    has_ds = {(r["p"], r["d"]) for r in db.run_query(
        driver,
        "MATCH (p:Publication)-[:HAS_DATASET]->(d:Dataset) "
        "RETURN p.identifier AS p, d.identifier AS d")}
    op_by = {(r["a"], r["b"]) for r in db.run_query(
        driver,
        "MATCH (a:RawDataFile)-[:OPERATED_BY]->(b:Researcher) "
        "RETURN a.identifier AS a, b.identifier AS b")}
    researchers = {r["id"] for r in db.run_query(
        driver, "MATCH (r:Researcher) RETURN r.identifier AS id")}
    return _index_existing(datasets, pubs, raws, has_ds, op_by, researchers)


def load_existing_from_disk():
    datasets = []
    for rec in _iter_jsonl(DATASETS_DISK):
        p = rec.get("properties", {})
        datasets.append({"id": rec["identifier"], "acc": p.get("accession"),
                         "url": p.get("source_url")})
    pubs, raws = set(), set()
    for rec in _iter_jsonl(PUBLICATIONS_DISK):
        pubs.add(rec["identifier"])
    for rec in _iter_jsonl(RAWFILES_PXD_DISK):
        ident = rec["identifier"]
        if ident.startswith("rawfile:"):
            raws.add(ident)
        elif ident.startswith("dataset:"):
            p = rec.get("properties", {})
            datasets.append({"id": ident, "acc": p.get("accession"),
                             "url": p.get("source_url")})
    # Disk cannot see already-loaded HAS_DATASET/OPERATED_BY/Researcher edges the
    # pipeline itself created; treat as empty (idempotency still holds via MERGE).
    researchers = set()
    for rec in _iter_jsonl(VALIDATED / "researchers.jsonl"):
        researchers.add(rec["identifier"])
    return _index_existing(datasets, pubs, raws, set(), set(), researchers)


def _index_existing(datasets, pubs, raws, has_ds, op_by, researchers):
    key_to_id: dict[str, str] = {}
    for d in datasets:
        ident = d["id"]
        text = " ".join(str(x) for x in (d.get("acc"), d.get("url"), ident) if x)
        keys = set(keys_from_identifier(ident))
        for e in normalize_accessions(text):
            keys.add(e["key"])
        for k in keys:
            key_to_id.setdefault(k, ident)
    return {
        "dataset_key_to_id": key_to_id,
        "dataset_ids": {d["id"] for d in datasets},
        "pub_ids": pubs,
        "raw_ids": raws,
        "has_dataset": has_ds,
        "operated_by": op_by,
        "researcher_ids": researchers,
    }


# --------------------------------------------------------------------------- #
# Phase 1 — dataset disposition
# --------------------------------------------------------------------------- #
def build_dataset_proposals(existing) -> tuple[list[dict], list[dict]]:
    """Return (ledger_rows, review_notes). One ledger row per (paper, deposit)."""
    key_to_id = existing["dataset_key_to_id"]
    pub_ids = existing["pub_ids"]
    has_dataset = existing["has_dataset"]

    rows: list[dict] = []
    notes: list[dict] = []
    seen_pairs: set[tuple[str, str]] = set()

    for rec in _iter_jsonl(PDF_EXTRACTION):
        da = rec.get("dataset_accession")
        if not isinstance(da, dict):
            continue
        val = (da.get("value") or "").strip()
        if not val or not da.get("grounded"):
            continue
        doi = (rec.get("doi") or "").strip().lower()
        pub_id = f"doi:{doi}"
        snippet = (da.get("source_snippet") or "").strip()
        char_span = da.get("char_span")
        extracted_at = rec.get("extracted_at")

        for e in normalize_accessions(val):
            pair = (pub_id, e["key"])
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            evidence = (
                f"PDF-extracted dataset_accession (grounded) for {pub_id}: "
                f"snippet {snippet!r}"
                + (f" at char_span {char_span}" if char_span else "")
                + f"; raw value {val!r}"
            )
            prov = {
                "source_type": "llm_extraction",
                "confidence": "medium",
                "extracted_at": extracted_at,
                "evidence_note": evidence,
                "source_id": pub_id,
                "schema_version": SCHEMA_VERSION,
            }

            existing_id = key_to_id.get(e["key"])
            pub_missing = pub_id not in pub_ids

            if existing_id:
                disposition = "LINK"
                already = (pub_id, existing_id) in has_dataset
                rows.append({
                    "kind": "dataset_link",
                    "disposition": "LINK",
                    "apply": (not pub_missing) and (not already),
                    "reason": ("already linked" if already else
                               "publication node missing" if pub_missing else
                               "exact key match to existing Dataset node"),
                    "paper": pub_id,
                    "accession_raw": val,
                    "accession": e["accession"],
                    "canonical_key": e["key"],
                    "dataset_identifier": existing_id,
                    "edge_provenance": prov,
                })
            elif e["mintable"] in ("unambiguous", "new_namespace"):
                disposition = "MINT"
                flag = (" [NEW NAMESPACE — approve the proposed identifier scheme]"
                        if e["mintable"] == "new_namespace" else "")
                node_props = {
                    "repository": e["repository"],
                    "accession": e["accession"],
                    "source_url": e["source_url"],
                    "access_status": "unknown",
                }
                rows.append({
                    "kind": "dataset_mint",
                    "disposition": "MINT",
                    "apply": not pub_missing,
                    "reason": ("publication node missing" if pub_missing
                               else "no existing node; unambiguous accession" + flag),
                    "paper": pub_id,
                    "accession_raw": val,
                    "accession": e["accession"],
                    "canonical_key": e["key"],
                    "dataset_identifier": e["mint_identifier"],
                    "node_properties": {k: v for k, v in node_props.items()
                                        if v is not None},
                    "node_provenance": dict(prov),
                    "edge_provenance": prov,
                })
            else:
                disposition = "REVIEW"
                reason = ("MSV accession may already exist as a MassIVE-DOI node "
                          "(dataset:other:10.25345/...) — cross-scheme bridge not "
                          "mechanically derivable" if e["scheme"] == "massive-msv"
                          else f"unrecognized/ambiguous accession ({e['scheme']})")
                rows.append({
                    "kind": "dataset_review",
                    "disposition": "REVIEW",
                    "apply": False,
                    "reason": reason,
                    "paper": pub_id,
                    "accession_raw": val,
                    "accession": e["accession"],
                    "canonical_key": e["key"],
                    "proposed_mint_identifier": e["mint_identifier"],
                    "edge_provenance": prov,
                })

    return rows, notes


# --------------------------------------------------------------------------- #
# Phase 1 — operator disposition. Source: FOXDEN instrumentMethod.Creator, which
# the pipeline already fused onto each PXD RawDataFile as `method_creator_raw`.
# --------------------------------------------------------------------------- #
def build_operator_proposals(existing) -> tuple[list[dict], list[dict]]:
    raw_ids = existing["raw_ids"]
    op_by = existing["operated_by"]

    handle_files: dict[str, list[str]] = defaultdict(list)
    rows: list[dict] = []
    minted_nodes: set[str] = set()

    for rec in _iter_jsonl(RAWFILES_PXD_DISK):
        ident = rec.get("identifier", "")
        if not ident.startswith("rawfile:"):
            continue
        props = rec.get("properties", {})
        handle = props.get("method_creator_raw")
        if not handle:
            continue   # no operator signal -> mint nothing, never fabricated
        handle = str(handle).strip().lower()
        filename = props.get("filename")
        researcher_id = f"researcher:{handle}"
        handle_files[handle].append(ident)

        evidence = (
            f"FOXDEN user_metadata.hasPart.instrumentMethod.Creator = {handle!r} "
            f"for RAW file {filename!r}"
        )
        prov = {
            "source_type": "fisher_py",
            "confidence": "medium",
            "extracted_at": rec.get("extracted_at"),
            "evidence_note": evidence,
            "source_id": ident,
            "schema_version": SCHEMA_VERSION,
        }

        # Mint the operator identity node once (raw, unreconciled), then the edge.
        if researcher_id not in minted_nodes:
            minted_nodes.add(researcher_id)
            rows.append({
                "kind": "researcher_mint",
                "disposition": "MINT",
                "apply": True,
                "reason": "FOXDEN operator handle minted as-is (NOT reconciled to "
                          "any author node)",
                "researcher_identifier": researcher_id,
                "node_properties": {
                    "name_full": handle,
                    "family_name": handle,       # raw token as-is; NOT parsed
                    "is_foxden_operator": True,
                    "reconciled_to_author": None,
                },
                "node_provenance": {
                    "source_type": "fisher_py",
                    "confidence": "medium",
                    "extracted_at": rec.get("extracted_at"),
                    "evidence_note": (
                        f"FOXDEN instrumentMethod.Creator operator handle {handle!r}; "
                        "raw identity, deliberately NOT reconciled to a CSV author "
                        "node (see reconciliation follow-up)."),
                    "source_id": ident,
                    "schema_version": SCHEMA_VERSION,
                },
            })

        rows.append({
            "kind": "operator_edge",
            "disposition": "MINT",
            "apply": (ident in raw_ids) and ((ident, researcher_id) not in op_by),
            "reason": ("rawfile node missing" if ident not in raw_ids else
                       "already linked" if (ident, researcher_id) in op_by else
                       "FOXDEN operator edge"),
            "rawfile_identifier": ident,
            "researcher_identifier": researcher_id,
            "edge_provenance": prov,
        })

    return rows, [{"handle": h, "n_files": len(v)} for h, v in handle_files.items()]


# --------------------------------------------------------------------------- #
# File emission (durable path) — build pre-normalize records for the approved
# rows so 03->04->05 recreate them on a clean rebuild (graph = f(files)). The
# record BUILDING is dataset-specific; the WRITER below is entity-agnostic and
# stable/idempotent so the researcher-merge can lift the same two functions.
# --------------------------------------------------------------------------- #
def _write_jsonl_stable(path, records, sort_key) -> int:
    """Write `records` to `path` as JSONL, stably sorted. Records are serialized in
    their existing (canonical) key order, so a re-run with the same inputs yields a
    byte-identical file. Entity-agnostic — reusable by any reconciliation step."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(records, key=sort_key)
    with path.open("w") as f:
        for rec in ordered:
            f.write(json.dumps(rec, ensure_ascii=False))
            f.write("\n")
    return len(ordered)


def emit_records(entities, relationships, entities_path, relationships_path):
    """Persist entity + relationship records to their pre-normalize JSONL files,
    stable-sorted (entities by identifier; relationships by
    (subject_id, relationship_type, object_id)) and idempotent. Returns
    (n_entities, n_relationships). Content/provenance are the caller's; this is a
    generic writer so every reconciliation step shares it."""
    n_ent = _write_jsonl_stable(entities_path, entities, lambda r: r.get("identifier", ""))
    n_rel = _write_jsonl_stable(
        relationships_path, relationships,
        lambda r: (r.get("subject_id", ""), r.get("relationship_type", ""), r.get("object_id", "")))
    return n_ent, n_rel


# --------------------------------------------------------------------------- #
# 04_validate.py hard-requires source_url on every Dataset. Where a paper cited a
# resolvable identifier but no full URL, canonicalize it LOSSLESSLY to a resolvable
# URL — a reformatting of a value the paper gave, NOT a lookup or invention. If the
# cited string is vaguer than a resolvable identifier, return None so the caller
# HOLDS the row from the auto-load path rather than fabricating a URL.
_OSF_DOI_FORM = re.compile(r"10\.17605\s*/\s*OSF\.?\s*IO\s*/\s*([A-Za-z0-9]{5})", re.I)
_OSF_CODE_FORM = re.compile(r"OSF\.?\s*IO\s*/\s*([A-Za-z0-9]{5})", re.I)


def derive_source_url(accession_raw: str):
    """Return (source_url, derivation_note) from a cited locator, or (None, reason)
    to HOLD the row. Lossless canonicalization only — no invented prefixes."""
    raw = (accession_raw or "").strip()
    m = _OSF_DOI_FORM.search(raw)
    if m:
        code = m.group(1).upper()
        url = f"https://doi.org/10.17605/OSF.IO/{code}"
        return url, (f"source_url derived from cited DOI 10.17605/OSF.IO/{code}; "
                     f"canonicalized to resolvable URL {url} "
                     f"(lossless reformatting of a cited identifier, not a lookup)")
    m = _OSF_CODE_FORM.search(raw)
    if m:
        code = m.group(1).lower()
        url = f"https://osf.io/{code}/"
        return url, (f"source_url derived from cited OSF locator OSF.IO/{code.upper()}; "
                     f"canonicalized to resolvable URL {url} "
                     f"(lossless reformatting of a cited identifier, not a lookup)")
    return None, f"cited string {raw!r} is not a losslessly-canonicalizable identifier"


# Canonical on-disk key order (matches datasets.jsonl / csv_relationships.jsonl).
def _entity_record(identifier, properties, prov) -> dict:
    return {
        "identifier": identifier,
        "entity_type": "Dataset",
        "properties": properties,
        "source_type": prov["source_type"],
        "confidence": prov["confidence"],
        "extracted_at": prov["extracted_at"],
        "evidence_note": prov["evidence_note"],
        "source_id": prov["source_id"],
        "schema_version": prov["schema_version"],
    }


def _rel_record(subject_id, object_id, prov) -> dict:
    return {
        "relationship_type": "HAS_DATASET",
        "subject_id": subject_id,
        "subject_type": "Publication",
        "object_id": object_id,
        "object_type": "Dataset",
        "properties": {},
        "source_type": prov["source_type"],
        "confidence": prov["confidence"],
        "extracted_at": prov["extracted_at"],
        "evidence_note": prov["evidence_note"],
        "source_id": prov["source_id"],
        "schema_version": prov["schema_version"],
    }


def build_emission_records(ledger_rows):
    """From approved ledger rows, build (entities, relationships, held).
    - dataset_mint -> one Dataset entity + one HAS_DATASET edge (source_url filled
      via derive_source_url where absent; HELD if it can't be canonicalized).
    - dataset_link -> one HAS_DATASET edge only (the target Dataset already exists).
    Only apply==true rows are emitted; HELD rows are reported, never written."""
    entities, relationships, held = [], [], []
    for r in ledger_rows:
        if not r.get("apply"):
            continue
        kind = r["kind"]
        if kind == "dataset_link":
            relationships.append(_rel_record(r["paper"], r["dataset_identifier"],
                                              r["edge_provenance"]))
        elif kind == "dataset_mint":
            props = dict(r.get("node_properties") or {})
            node_prov = dict(r["node_provenance"])
            if not props.get("source_url"):
                url, note = derive_source_url(r.get("accession_raw", ""))
                if url is None:
                    held.append({"identifier": r["dataset_identifier"],
                                 "paper": r["paper"], "reason": note})
                    continue
                props["source_url"] = url
                node_prov = dict(node_prov)
                node_prov["evidence_note"] = node_prov["evidence_note"] + " | " + note
            entities.append(_entity_record(r["dataset_identifier"], props, node_prov))
            relationships.append(_rel_record(r["paper"], r["dataset_identifier"],
                                             r["edge_provenance"]))
    return entities, relationships, held


def emit_to(ledger_rows, emit_dir):
    """Build records from the approved ledger and write them via the shared writer.
    emit_dir=None -> the real pre-normalize dirs; else a flat review/preview dir."""
    entities, relationships, held = build_emission_records(ledger_rows)
    if emit_dir:
        ent_path = Path(emit_dir) / EMIT_ENTITIES_NAME
        rel_path = Path(emit_dir) / EMIT_RELATIONSHIPS_NAME
    else:
        ent_path = ENTITIES_DIR / EMIT_ENTITIES_NAME
        rel_path = RELATIONSHIPS_DIR / EMIT_RELATIONSHIPS_NAME
    n_ent, n_rel = emit_records(entities, relationships, ent_path, rel_path)
    print(f"[emit] {n_ent} Dataset entities  -> {ent_path}")
    print(f"[emit] {n_rel} HAS_DATASET edges -> {rel_path}")
    if held:
        print(f"[emit] HELD from auto-load ({len(held)} — not written):")
        for h in held:
            print(f"    {h['identifier']}  ({h['paper']}): {h['reason']}")
    return ent_path, rel_path, held


# --------------------------------------------------------------------------- #
# Phase 2 — apply the ledger (only rows with apply==true)
# --------------------------------------------------------------------------- #
def _clean(m: dict) -> dict:
    return {k: v for k, v in m.items() if v is not None and v != ""}


def apply_ledger(driver, ledger_rows) -> None:
    counts = Counter()
    before = _graph_counts(driver)

    for row in ledger_rows:
        if not row.get("apply"):
            continue
        kind = row["kind"]
        if kind == "dataset_link":
            props = _clean(row["edge_provenance"])
            summary = _write(
                driver,
                "MATCH (p:Publication {identifier:$p}) "
                "MATCH (d:Dataset {identifier:$d}) "
                "MERGE (p)-[r:HAS_DATASET]->(d) "
                "ON CREATE SET r += $props",
                {"p": row["paper"], "d": row["dataset_identifier"], "props": props},
            )
            counts["HAS_DATASET"] += summary.counters.relationships_created
        elif kind == "dataset_mint":
            node_props = _clean({**row["node_properties"], **row["node_provenance"]})
            s1 = _write(
                driver,
                "MERGE (d:Dataset {identifier:$id}) ON CREATE SET d += $props",
                {"id": row["dataset_identifier"], "props": node_props},
            )
            counts["Dataset"] += s1.counters.nodes_created
            s2 = _write(
                driver,
                "MATCH (p:Publication {identifier:$p}) "
                "MATCH (d:Dataset {identifier:$d}) "
                "MERGE (p)-[r:HAS_DATASET]->(d) ON CREATE SET r += $props",
                {"p": row["paper"], "d": row["dataset_identifier"],
                 "props": _clean(row["edge_provenance"])},
            )
            counts["HAS_DATASET"] += s2.counters.relationships_created
        elif kind == "researcher_mint":
            node_props = _clean({**row["node_properties"], **row["node_provenance"]})
            s1 = _write(
                driver,
                "MERGE (r:Researcher {identifier:$id}) ON CREATE SET r += $props",
                {"id": row["researcher_identifier"], "props": node_props},
            )
            counts["Researcher"] += s1.counters.nodes_created
        elif kind == "operator_edge":
            s2 = _write(
                driver,
                "MATCH (a:RawDataFile {identifier:$a}) "
                "MATCH (b:Researcher {identifier:$b}) "
                "MERGE (a)-[r:OPERATED_BY]->(b) ON CREATE SET r += $props",
                {"a": row["rawfile_identifier"], "b": row["researcher_identifier"],
                 "props": _clean(row["edge_provenance"])},
            )
            counts["OPERATED_BY"] += s2.counters.relationships_created

    after = _graph_counts(driver)
    print("\n[apply] created this run:")
    for k in ("Dataset", "Researcher", "HAS_DATASET", "OPERATED_BY"):
        print(f"    {k:14s} +{counts[k]}")
    print("\n[apply] graph counts before -> after:")
    for k in sorted(before):
        print(f"    {k:14s} {before[k]:6d} -> {after[k]:6d}")


def _write(driver, cypher, params):
    with driver.session() as session:
        return session.run(cypher, **params).consume()


def _graph_counts(driver) -> dict:
    q = {
        "Dataset": "MATCH (n:Dataset) RETURN count(n) AS c",
        "Researcher": "MATCH (n:Researcher) RETURN count(n) AS c",
        "HAS_DATASET": "MATCH ()-[r:HAS_DATASET]->() RETURN count(r) AS c",
        "OPERATED_BY": "MATCH ()-[r:OPERATED_BY]->() RETURN count(r) AS c",
    }
    return {k: db.run_query(driver, v)[0]["c"] for k, v in q.items()}


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def write_ledger(rows) -> None:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def reconciliation_candidates(op_handles, existing) -> dict[str, list[str]]:
    """For each operator handle, list existing Researcher author nodes whose
    surname looks like a match. This is REPORTING ONLY — never acted on. The
    operator->author merge is a separate, non-guessable, human-only ruling."""
    ids = existing["researcher_ids"]
    out: dict[str, list[str]] = {}
    for h in op_handles:
        handle = h["handle"]
        # 'donsmith' is a given+family run-together token; its surname is 'smith'.
        surname = "smith" if handle == "donsmith" else handle
        cands = sorted(i for i in ids if i.startswith(f"researcher:{surname}_"))
        out[handle] = cands
    return out


def david_flags(ds_rows, op_handles, existing) -> str:
    lines = ["\n## Flags for David — do NOT act; explicit human rulings required\n"]

    # (1) The Blood Proteoform Atlas campaign scope.
    pxd_mint = [r for r in ds_rows if r["kind"] == "dataset_mint"
                and r["canonical_key"].startswith("proteomexchange:")]
    lines.append("### 1. science.aaz5284 — Blood Proteoform Atlas campaign scope\n")
    lines.append("- `PXD026123` is LINKed to the existing node (the clean fix).")
    if pxd_mint:
        for r in pxd_mint:
            lines.append(f"- `{r['accession']}` is proposed as a NEW node "
                         f"(`{r['dataset_identifier']}`): it is a distinct "
                         "ProteomeXchange accession with no existing node.")
    lines.append("- **David's ruling:** are `PXD026123`–`PXD026154` (the 32 "
                 "per-run nodes) plus `PXD026178` one umbrella campaign deposit? "
                 "This script links science.aaz5284 ONLY to the exact accessions "
                 "its PDF cites (PXD026123, PXD026178); it does NOT auto-extend to "
                 "all 32, and asserts no campaign structure.\n")

    # (2) The CSV-minted PRIDE search-URL node.
    lines.append("### 2. `dataset:other:0516284a` — CSV-minted PRIDE search URL\n")
    lines.append("- This node wraps a PRIDE keyword-search URL (\"Data for the "
                 "Blood...\"), not a real deposit accession. It is NOT touched, "
                 "retired, or folded by this script.")
    lines.append("- **David's ruling:** fold/retire it toward the real Blood "
                 "Proteoform Atlas PXD deposits, or keep it? Execute nothing here.\n")

    # (3) Operator -> author reconciliation candidates.
    cands = reconciliation_candidates(op_handles, existing)
    lines.append("### 3. Operator handle -> author node reconciliation (NOT done)\n")
    lines.append("Operator identities are minted AS-IS (`researcher:{handle}`). "
                 "Surname look-alikes below are candidates ONLY — never merged by "
                 "this script (guessing a person's identity from an operator handle "
                 "is forbidden). A human must rule each one.\n")
    lines.append("| operator handle | candidate author node(s) |")
    lines.append("|---|---|")
    for h in sorted(op_handles, key=lambda x: -x["n_files"]):
        handle = h["handle"]
        c = cands.get(handle) or []
        lines.append(f"| `researcher:{handle}` | "
                     f"{', '.join(f'`{x}`' for x in c) if c else '(none found)'} |")
    lines.append("")
    return "\n".join(lines)


def summarize(ds_rows, op_rows, op_handles, existing, offline) -> str:
    ds_by_disp = Counter(r["disposition"] for r in ds_rows)
    link_applic = sum(1 for r in ds_rows if r["kind"] == "dataset_link" and r["apply"])
    link_already = sum(1 for r in ds_rows if r["kind"] == "dataset_link"
                       and r["reason"] == "already linked")
    mint_rows = [r for r in ds_rows if r["kind"] == "dataset_mint"]
    mint_new_ns = sum(1 for r in mint_rows if "NEW NAMESPACE" in r["reason"])
    review_rows = [r for r in ds_rows if r["kind"] == "dataset_review"]
    op_edges = [r for r in op_rows if r["kind"] == "operator_edge"]
    op_edges_apply = sum(1 for r in op_edges if r["apply"])
    op_nodes = [r for r in op_rows if r["kind"] == "researcher_mint"]

    lines = []
    lines.append("# Phase 1 dry-run — dataset & operator edge proposals\n")
    lines.append(f"Source of existing graph state: "
                 f"{'ON-DISK validated records (offline)' if offline else 'LIVE GRAPH'}\n")
    lines.append("## Dataset dispositions\n")
    lines.append(f"- LINK  : {ds_by_disp['LINK']}  "
                 f"({link_applic} to apply, {link_already} already linked)")
    lines.append(f"- MINT  : {ds_by_disp['MINT']}  "
                 f"({mint_new_ns} of them under a NEW proposed namespace — need approval)")
    lines.append(f"- REVIEW: {ds_by_disp['REVIEW']}  (held for David; nothing applied)\n")

    lines.append("### LINK — cited accession exactly matches an existing Dataset node\n")
    lines.append("| paper | accession | -> existing Dataset node | apply |")
    lines.append("|---|---|---|---|")
    for r in sorted(ds_rows, key=lambda x: x["paper"]):
        if r["kind"] == "dataset_link":
            lines.append(f"| {r['paper']} | {r['accession']} | "
                         f"{r['dataset_identifier']} | {'yes' if r['apply'] else 'no ('+r['reason']+')'} |")

    lines.append("\n### MINT — no existing node; propose new Dataset + HAS_DATASET\n")
    lines.append("| paper | accession | proposed node identifier | note |")
    lines.append("|---|---|---|---|")
    for r in sorted(mint_rows, key=lambda x: x["paper"]):
        note = "NEW NAMESPACE" if "NEW NAMESPACE" in r["reason"] else ""
        lines.append(f"| {r['paper']} | {r['accession']} | "
                     f"{r['dataset_identifier']} | {note} |")

    lines.append("\n### REVIEW — do NOT act; flagged for David\n")
    lines.append("| paper | accession | reason |")
    lines.append("|---|---|---|")
    for r in sorted(review_rows, key=lambda x: x["paper"]):
        lines.append(f"| {r['paper']} | {r['accession']} | {r['reason']} |")

    lines.append("\n## Operator (OPERATED_BY) proposals\n")
    lines.append(f"- Researcher operator nodes to mint (raw, UNRECONCILED): {len(op_nodes)}")
    for r in op_nodes:
        lines.append(f"    - {r['researcher_identifier']}")
    lines.append(f"- OPERATED_BY edges proposed: {len(op_edges)} "
                 f"({op_edges_apply} to apply)")
    lines.append("- Operator handle -> file counts:")
    for h in sorted(op_handles, key=lambda x: -x["n_files"]):
        lines.append(f"    - {h['handle']!r}: {h['n_files']} RAW files")
    lines.append("\n  These raw operators are **NOT reconciled** to author identities. "
                 "That gap remains by design until ruled on.\n")

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true",
                    help="Phase 2: MERGE the ledger's apply==true rows (default is dry-run)")
    ap.add_argument("--ledger", default=None,
                    help="Phase 2 only: apply from this ledger file instead of the "
                         "default. Use a narrowed, human-approved scope file so the "
                         "apply CANNOT touch any row outside it.")
    ap.add_argument("--emit-dir", default=None,
                    help="Emit the approved rows as pre-normalize JSONL (Dataset "
                         "entities + HAS_DATASET edges) to this directory instead of "
                         "the real data/processed/{entities,relationships}/. Use a "
                         "review/preview dir first; writes FILES only, no graph.")
    ap.add_argument("--emit", action="store_true",
                    help="Emit the pre-normalize files (no graph write). Combine with "
                         "--ledger to scope; with --emit-dir to target a preview dir.")
    ap.add_argument("--offline", action="store_true",
                    help="Phase 1 only: classify against on-disk validated records "
                         "instead of the live graph")
    args = ap.parse_args()

    if args.apply or args.emit:
        ledger_path = Path(args.ledger) if args.ledger else LEDGER
        if not ledger_path.exists():
            print(f"ABORT: ledger not found ({ledger_path}). Run the dry-run first.")
            return 2
        print(f"[apply/emit] source ledger: {ledger_path}")
        rows = list(_iter_jsonl(ledger_path))
        # Emit the durable pre-normalize files. --apply also emits (to the real
        # dirs unless --emit-dir overrides), so the graph fix never drifts from
        # the files that reproduce it.
        if args.emit or args.apply:
            emit_to(rows, args.emit_dir)
        if args.apply:
            driver = db.connect()
            try:
                apply_ledger(driver, rows)
            finally:
                db.close(driver)
        print("\nDone. This script made NO git changes — review and commit yourself.")
        return 0

    # Phase 1 — dry-run
    driver = None
    if not args.offline:
        try:
            driver = db.connect()
            existing = load_existing_from_graph(driver)
            offline = False
        except Exception as e:
            print(f"[warn] graph unreachable ({type(e).__name__}: {e}); "
                  f"falling back to on-disk validated records.")
            existing = load_existing_from_disk()
            offline = True
    else:
        existing = load_existing_from_disk()
        offline = True
    if driver is not None:
        db.close(driver)

    ds_rows, _ = build_dataset_proposals(existing)
    op_rows, op_handles = build_operator_proposals(existing)
    all_rows = ds_rows + op_rows

    write_ledger(all_rows)
    report = (summarize(ds_rows, op_rows, op_handles, existing, offline)
              + david_flags(ds_rows, op_handles, existing))
    REPORT.write_text(report)
    print(report)

    # Closing tallies
    link_apply = sum(1 for r in ds_rows if r["kind"] == "dataset_link" and r["apply"])
    mint_apply = sum(1 for r in ds_rows if r["kind"] == "dataset_mint" and r["apply"])
    review_n = sum(1 for r in ds_rows if r["disposition"] == "REVIEW")
    op_edge_apply = sum(1 for r in op_rows if r["kind"] == "operator_edge" and r["apply"])
    op_node_apply = sum(1 for r in op_rows if r["kind"] == "researcher_mint" and r["apply"])
    print("\n" + "=" * 68)
    print("PHASE 1 COMPLETE — nothing executed, nothing committed.")
    print(f"  Ledger written : {LEDGER}")
    print(f"  Report written : {REPORT}")
    print(f"  Reconciliation win (LINK edges to already-loaded deposits): {link_apply}")
    print(f"  New Dataset nodes to mint (+ their HAS_DATASET edges)      : {mint_apply}")
    print(f"  Held as REVIEW for David                                  : {review_n}")
    print(f"  Operator: {op_node_apply} Researcher nodes + {op_edge_apply} OPERATED_BY edges")
    print("  Operator->author reconciliation gap REMAINS (by design, not done here).")
    print("=" * 68)
    print("\nReview the ledger, then run with --apply to MERGE only apply==true rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
