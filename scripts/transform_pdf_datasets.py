#!/usr/bin/env python3
"""PDF dataset_accession -> HAS_DATASET edges (Publication -> existing Dataset).

Mints the ONE relationship that closes the Q13 gap ("(both) 0" in
docs/DISCOVERY_QUESTIONS.md) WITHOUT ANALYZED_IN: a paper that names a deposit
accession is linked to the Dataset node its raw files already point to via
DERIVED_FROM, creating a raw-file <-> publication path through the shared
Dataset.

Modeled on scripts/transform_pdf_software.py. Every rule is measured, not
asserted; nothing is re-derived from the live graph at build time -- the
transform reads only on-disk pipeline artifacts, so it is reproducible and
its output is exactly what 03 -> 04 -> 05 will load.

Reads:
    data/raw/pdf_extraction/pdf_extracted_fixed.jsonl   (378 records, source 6)
    data/processed/entities/datasets.jsonl              (CSV Dataset nodes)
    data/processed/entities/rawfiles_pxd.jsonl          (32 PXD Dataset nodes)
    data/processed/relationships/rawfiles_pxd_relationships.jsonl  (DERIVED_FROM)
    data/processed/relationships/csv_relationships.jsonl           (existing HAS_DATASET)
    data/processed/pdf_text/{doi_safe}.md               (bucket-D confirmation, 8 papers only)

Writes (dry-run, the DEFAULT -- writes files but never touches Neo4j):
    data/processed/relationships/pdf_dataset_relationships.jsonl   (bucket A + new-B edges)
    data/processed/review/dataset_review.md                        (buckets C/D + skipped-existing)

Nothing loads until a human reviews and the pipeline (03_normalize ->
04_validate -> 05_load) is re-run. This script does NOT run the pipeline.

HARD RULES honored (CLAUDE.md + task brief):
  - Six provenance props on every minted edge; source on every edge.
  - Mint ONLY to a Dataset node that already exists (matched by normalized
    accession). No new Dataset nodes are minted in this pass.
  - EXACT accession match auto-mints; anything else -> REVIEW, never minted.
  - An edge that already exists in the graph is NOT re-emitted: 05 does
    `MERGE (a)-[r]->(b) SET r += row.props`, so re-emitting a CSV-sourced
    HAS_DATASET edge would OVERWRITE its `source_type: csv` provenance with
    `llm_extraction` -- a provenance downgrade. Skipped and logged instead.
"""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

# --- inputs ---------------------------------------------------------------
INPUT = Path("data/raw/pdf_extraction/pdf_extracted_fixed.jsonl")
DATASETS = Path("data/processed/entities/datasets.jsonl")
PXD_DATASETS = Path("data/processed/entities/rawfiles_pxd.jsonl")
PXD_RELS = Path("data/processed/relationships/rawfiles_pxd_relationships.jsonl")
CSV_RELS = Path("data/processed/relationships/csv_relationships.jsonl")
PDF_TEXT_DIR = Path("data/processed/pdf_text")

# --- outputs --------------------------------------------------------------
RELS_OUT = Path("data/processed/relationships/pdf_dataset_relationships.jsonl")
REVIEW_OUT = Path("data/processed/review/dataset_review.md")

SCHEMA_VERSION = "v1.0"
SOURCE_TYPE = "llm_extraction"
CONFIDENCE = "medium"   # grounded in text, but LLM-extracted; same basis as 02d/software


# --- extraction-failure guard (Sec 2.-1, per transform_pdf_software) ------
EXTRACTION_FIELDS = ["instrument", "ionization_method", "sample_type",
                     "facility", "software_tools", "dataset_accession"]


def failure_reason(rec):
    if rec.get("pdf_source") == "none":
        return "no_pdf"
    if "No PDF could be acquired" in (rec.get("evidence_note") or ""):
        return "evidence_note_flag"
    all_null = all((rec.get(f) or {}).get("value") is None
                   for f in EXTRACTION_FIELDS)
    if all_null and len(rec.get("all_field_extractions", [])) == 0:
        return "ran_but_empty"
    return None


def doi_safe(doi):
    return re.sub(r"[^A-Za-z0-9]+", "_", doi)


# --- accession candidate extraction ---------------------------------------
# One dataset_accession string may hold >1 accession (';'-separated, or a URL
# plus its DOI form). Return normalized (repository, accession, raw_part) using
# the SAME repository buckets 02b_extract_csv.classify_dataset_url uses, so a
# derived accession lands on the same identifier the CSV path would mint.
# This is DETERMINISTIC pattern extraction, not fuzzy matching: it either finds
# a well-formed accession token or it does not.
def candidates(value):
    out = []
    for part in re.split(r"[;]", value):
        part = part.strip()
        if not part:
            continue
        low = part.lower()
        m = re.search(r"osf\.io/(?:10\.17605/osf\.io/)?([a-z0-9]+)", low)
        if m:
            out.append(("OSF", m.group(1).upper(), part)); continue
        m = re.search(r"(pxd\d+)", low)
        if m:
            out.append(("ProteomeXchange", m.group(1).upper(), part)); continue
        m = re.search(r"(msv\d+)", low)
        if m:
            out.append(("MassIVE", m.group(1).upper(), part)); continue
        m = re.search(r"zenodo[./](\d+)", low)
        if m:
            out.append(("Zenodo", m.group(1), part)); continue
        m = re.search(r"(prjna\d+|srp\d+|srr\d+|srx\d+)", low)
        if m:
            out.append(("SRA/BioProject", m.group(1).upper(), part)); continue
        m = re.search(r"(bco-dmo)\s*(\d+)", low)
        if m:
            out.append(("BCO-DMO", m.group(2), part)); continue
        m = re.search(r"10\.26022/ieda/(\d+)", low)
        if m:
            out.append(("IEDA", m.group(1), part)); continue
        m = re.search(r"doi\.org/(10\.\S+)", low)
        if m:
            out.append(("Other", m.group(1).rstrip("/"), part)); continue
        out.append(("?", part, part))   # unrecognized shape -> REVIEW (bucket D)
    return out


# All-zero placeholder accession (e.g. PXD000000). 02d already gates these out
# of the top-level field, but the guard stays: precision over recall.
PLACEHOLDER = re.compile(r"^\D*0+$")


def is_placeholder(acc):
    return bool(PLACEHOLDER.match(acc))


# --- disk loaders ---------------------------------------------------------
def _iter_jsonl(path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_dataset_index():
    """accession.upper() -> dataset identifier, from the on-disk Dataset nodes.
    Also returns the full identifier set. Datasets span two files (schema)."""
    acc_index = {}
    identifiers = set()
    for path in (DATASETS, PXD_DATASETS):
        if not path.exists():
            continue
        for rec in _iter_jsonl(path):
            if rec.get("entity_type") != "Dataset":
                continue
            ident = rec["identifier"]
            identifiers.add(ident)
            acc = (rec.get("properties") or {}).get("accession")
            if acc:
                acc_index.setdefault(acc.upper(), ident)
    return acc_index, identifiers


def load_hasraw():
    """dataset identifier -> # DERIVED_FROM raw files (0 if none)."""
    counts = defaultdict(int)
    for rec in _iter_jsonl(PXD_RELS):
        if rec.get("relationship_type") == "DERIVED_FROM":
            counts[rec["object_id"]] += 1
    return counts


def load_existing_has_dataset():
    """set of (subject_id, object_id) HAS_DATASET pairs already on disk."""
    pairs = set()
    for rec in _iter_jsonl(CSV_RELS):
        if rec.get("relationship_type") == "HAS_DATASET":
            pairs.add((rec["subject_id"], rec["object_id"]))
    return pairs


def confirm_in_pdftext(doi, acc, raw_part):
    """Bucket-D gate. If the paper's pdf_text exists, require the accession
    string to be present; else fall back to the extraction grounding flag
    (only 8 ground-truth papers have pdf_text on disk)."""
    p = PDF_TEXT_DIR / f"{doi_safe(doi)}.md"
    if not p.exists():
        return ("no_pdftext", "pdf_text absent (only 8 ground-truth papers have it); "
                              "relying on extraction grounding flag")
    tl = p.read_text(encoding="utf-8", errors="ignore").lower()
    if acc.lower() in tl or raw_part.lower() in tl:
        return ("confirmed_in_text", "accession present in pdf_text")
    return ("NOT_in_text", "accession ABSENT from pdf_text -> suspected extraction artifact")


# --- provenance envelope (six props, 02c/transform_pdf_software pattern) ---
def _provenance(doi, extracted_at, evidence):
    return {
        "source_type": SOURCE_TYPE,
        "confidence": CONFIDENCE,
        "extracted_at": extracted_at,
        "evidence_note": evidence,
        "source_id": f"doi:{doi}",
        "schema_version": SCHEMA_VERSION,
    }


def build_edge(doi, dataset_id, acc, snippet, extracted_at, grounded):
    """HAS_DATASET: Publication -> existing Dataset. relationship_type property
    = 'primary' (STEP 2: no supplementary signal is available in the record)."""
    evidence = (f"Repository accession '{acc}' extracted from this paper's PDF "
                f"(dataset_accession field) via Docling + LangExtract "
                f"(model llama3.1:8b), grounded={grounded}; source snippet: "
                f"{snippet!r}. Linked to the existing Dataset node matched by "
                f"normalized accession. Identity of the extraction is unverified "
                f"against the deposit; the Dataset node itself is pre-existing.")
    rec = {
        "relationship_type": "HAS_DATASET",
        "subject_id": f"doi:{doi.lower()}",
        "subject_type": "Publication",
        "object_id": dataset_id,
        "object_type": "Dataset",
        "properties": {"relationship_type": "primary"},
    }
    rec.update(_provenance(doi, extracted_at, evidence))
    return rec


# --- core: bucket every extracted accession -------------------------------
def analyze():
    acc_index, identifiers = load_dataset_index()
    hasraw = load_hasraw()
    existing_edges = load_existing_has_dataset()

    buckets = {"A": [], "B_new": [], "B_existing": [], "C": [], "D": []}
    failed = []

    for rec in _iter_jsonl(INPUT):
        why = failure_reason(rec)
        if why:
            failed.append((rec.get("doi"), why))
            continue
        doi = rec["doi"]
        da = (rec.get("dataset_accession") or {})
        value = da.get("value")
        if not value:
            continue
        snippet = da.get("source_snippet")
        grounded = da.get("grounded")
        extracted_at = rec.get("extracted_at")

        for repo, acc, raw_part in candidates(value):
            row = {"doi": doi, "value": value, "repo": repo, "acc": acc,
                   "raw_part": raw_part, "snippet": snippet, "grounded": grounded,
                   "extracted_at": extracted_at}

            # D: placeholder / unrecognized shape
            if is_placeholder(acc) or repo == "?":
                row["why"] = ("placeholder/all-zero accession" if is_placeholder(acc)
                              else "unrecognized accession shape")
                buckets["D"].append(row)
                continue

            # D: not confirmable in pdf_text (only checkable for the 8 papers)
            conf_status, conf_note = confirm_in_pdftext(doi, acc, raw_part)
            row["conf_status"] = conf_status
            row["conf_note"] = conf_note
            if conf_status == "NOT_in_text":
                row["why"] = conf_note
                buckets["D"].append(row)
                continue

            ident = acc_index.get(acc.upper())
            if not ident:
                row["why"] = "well-formed accession, no matching Dataset node"
                buckets["C"].append(row)
                continue

            row["dataset_id"] = ident
            row["nraw"] = hasraw.get(ident, 0)
            row["edge_exists"] = (f"doi:{doi.lower()}", ident) in existing_edges

            if row["nraw"] > 0:
                if row["edge_exists"]:
                    # A dataset WITH raw files whose edge already exists would
                    # still be a no-op re-mint; skip to avoid provenance clobber.
                    buckets["B_existing"].append(row)
                else:
                    buckets["A"].append(row)
            else:
                if row["edge_exists"]:
                    buckets["B_existing"].append(row)
                else:
                    buckets["B_new"].append(row)

    return buckets, failed, identifiers


# --- write ----------------------------------------------------------------
def _write_swap(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".new")
    with tmp.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    tmp.replace(path)


def build_edges(buckets):
    """Mint bucket A + bucket B_new only. Dedup by (subject, object)."""
    seen = set()
    edges = []
    for b in ("A", "B_new"):
        for row in buckets[b]:
            key = (f"doi:{row['doi'].lower()}", row["dataset_id"])
            if key in seen:
                continue
            seen.add(key)
            edges.append(build_edge(row["doi"], row["dataset_id"], row["acc"],
                                    row["snippet"], row["extracted_at"],
                                    row["grounded"]))
    return edges


def write_review(buckets, failed, edge_count):
    def tbl(rows, cols):
        L = ["| " + " | ".join(cols) + " |\n",
             "|" + "|".join("---" for _ in cols) + "|\n"]
        for r in rows:
            L.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |\n")
        return "".join(L)

    L = ["# HAS_DATASET minting -- DRY RUN (nothing loaded)\n\n",
         f"Generated by `scripts/transform_pdf_datasets.py`. Input: `{INPUT}`.\n\n",
         "Buckets A + B_new are minted to "
         f"`{RELS_OUT}`. B_existing / C / D are REVIEW-only (never minted).\n\n",
         "## Counts\n\n",
         f"- **A** (mintable, Q13-flipping -- Dataset has DERIVED_FROM raw files): "
         f"{len(buckets['A'])}\n",
         f"- **B_new** (mintable, matched Dataset has 0 raw files, edge is new): "
         f"{len(buckets['B_new'])}\n",
         f"- **B_existing** (matched Dataset, HAS_DATASET edge ALREADY on disk -- "
         f"SKIPPED to avoid clobbering CSV provenance): {len(buckets['B_existing'])}\n",
         f"- **C** (well-formed accession, no Dataset node -- REVIEW / candidate new): "
         f"{len(buckets['C'])}\n",
         f"- **D** (placeholder / unrecognized / not confirmable -- REVIEW, never mint): "
         f"{len(buckets['D'])}\n",
         f"- **Extraction failures** (missing, not absent): {len(failed)}\n\n",
         f"**Edges written to JSONL: {edge_count}** "
         f"(A + B_new, deduped by subject/object).\n\n",
         "## A -- mintable AND Q13-flipping\n\n",
         tbl(buckets["A"], ["doi", "acc", "dataset_id", "nraw", "conf_status"]),
         "\n## B_new -- mintable, no raw files, new edge\n\n",
         tbl(buckets["B_new"], ["doi", "acc", "dataset_id", "conf_status"]),
         "\n## B_existing -- SKIPPED (edge already on disk; not re-minted)\n\n",
         tbl(buckets["B_existing"], ["doi", "acc", "dataset_id", "nraw"]),
         "\n## C -- REVIEW: well-formed accession, no matching Dataset node\n\n",
         tbl(buckets["C"], ["doi", "repo", "acc", "raw_part", "conf_status"]),
         "\n## D -- REVIEW: precision-suspect, never mint\n\n",
         tbl(buckets["D"], ["doi", "acc", "why"]),
         ]
    REVIEW_OUT.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_OUT.write_text("".join(L), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-write", action="store_true",
                    help="analyze and print only; do not write the JSONL/review")
    args = ap.parse_args()

    if not INPUT.exists():
        raise SystemExit(f"ERROR input absent: {INPUT}")

    buckets, failed, identifiers = analyze()
    edges = build_edges(buckets)

    print("=== HAS_DATASET dry-run (nothing loaded) ===")
    print(f"Existing Dataset nodes on disk: {len(identifiers)}")
    print(f"A  (mintable, Q13-flipping) : {len(buckets['A'])}")
    print(f"B_new  (mintable, no raw)   : {len(buckets['B_new'])}")
    print(f"B_existing (SKIPPED)        : {len(buckets['B_existing'])}")
    print(f"C  (REVIEW, no node)        : {len(buckets['C'])}")
    print(f"D  (REVIEW, suspect)        : {len(buckets['D'])}")
    print(f"Extraction failures         : {len(failed)}")
    print(f"--> edges to write (A+B_new, deduped): {len(edges)}")
    print()
    print("Proposed edges:")
    for e in edges:
        rt = e["properties"].get("relationship_type")
        print(f"  {e['subject_id']}  -HAS_DATASET({rt})->  {e['object_id']}")

    if not args.no_write:
        _write_swap(RELS_OUT, edges)
        write_review(buckets, failed, len(edges))
        print(f"\nwrote {len(edges)} edges -> {RELS_OUT}")
        print(f"wrote review -> {REVIEW_OUT}")
        print("\nDRY RUN COMPLETE. NOT loaded. Re-run 03->04->05 only after human review.")


if __name__ == "__main__":
    main()
