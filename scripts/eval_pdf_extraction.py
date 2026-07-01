"""
eval_pdf_extraction.py — Blind evaluation harness for 02d_extract_pdf.py

Scores the six gap fields extracted by 02d against manually annotated ground
truth for the 8 ground-truth papers. Produces per-field and overall precision,
recall, and F1. Writes a Markdown report and a JSONL results file.

Usage:
    python scripts/eval_pdf_extraction.py
    python scripts/eval_pdf_extraction.py --print-ground-truth   # self-check

Design principles:
  - BLIND: ground truth is parsed at runtime from paper_reviews.md. No
    ground-truth value is ever hardcoded in this script so it cannot leak
    into the LLM extraction (02d must be run BEFORE this script is used
    to score its output; this script reads what 02d already produced).
  - READ-ONLY on all inputs: never modifies paper_reviews.md or any output
    from 02d. Only writes the two output files.
  - Standard library only: csv, json, re, datetime, pathlib. No third-party
    packages required.

Matching strategy (per field, applied in priority order):
  1. Exact match after normalisation (lowercase, collapse whitespace/punctuation)
  2. Substring / overlap match (predicted token appears in expected string or
     vice versa) — catches verbatim-extraction vs. abbreviated annotation
  3. Canonical match via controlled_vocabulary.md alias tables — catches
     "nanoelectrospray" matching canonical "ESI"
  A prediction is a True Positive if any level matches. A predicted value when
  the annotation is N/A / absent is a False Positive (hallucination). A null
  prediction when the annotation has a value is a False Negative.

Multi-value fields (instrument, ionization_method, sample_type, software_tools,
dataset_accession) are scored per element: for each annotated value, check
whether any predicted value matches it (recall); for each predicted value,
check whether any annotated value matches it (precision).

Ground truth is parsed from section 3 (FT-ICR/facility information) and
section 4 (metadata) of each paper's review block in paper_reviews.md.
"""

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (relative to repo root; run from repo root)
# ---------------------------------------------------------------------------
PAPER_REVIEWS = Path("docs/annotations/paper_reviews.md")
CONTROLLED_VOCAB = Path("docs/controlled_vocabulary.md")
PREDICTIONS_FILE = Path("data/processed/entities/pdf_extracted.jsonl")
REPORT_OUT = Path("docs/PDF_EXTRACTION_EVAL.md")
RESULTS_JSONL = Path("outputs/pdf_eval_results.jsonl")

# The six gap fields this harness evaluates.
TARGET_FIELDS = [
    "instrument",
    "ionization_method",
    "sample_type",
    "facility",
    "software_tools",
    "dataset_accession",
]

# Section-3 table rows that map to each gap field.
SECTION3_FIELD_MAP = [
    (r"instrument\s*/\s*magnet\s+stated", "instrument"),
    (r"facility\s+named", "facility"),
    (r"ionization\s*/\s*technique\s+stated", "ionization_method"),
    (r"software\s*/\s*data.processing\s+tools\s+named", "software_tools"),
]

# Section-4 metadata row patterns.
SECTION4_DATASET_RE = re.compile(
    r"dataset\s+identifier\s*/\s*accession", re.IGNORECASE
)
SECTION4_SAMPLE_RE = re.compile(
    r"sample\s*/\s*specimen\s+identifiers", re.IGNORECASE
)

# Accession patterns for extracting identifiers from section-4 notes.
ACCESSION_RE = re.compile(
    r"\b(MSV\d{6,}|PXD\d{4,}|10\.17605/OSF\.IO/[A-Za-z0-9]+|osf\.io/[A-Za-z0-9]+)\b",
    re.IGNORECASE,
)

# Null tokens — annotation cells that mean "no value present."
NULL_TOKENS = {
    "n/a", "na", "none", "null", "", "no", "not stated",
    "no other software or datasets were used",
}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def now_iso():
    return datetime.now(timezone.utc).isoformat()


def normalise(text):
    """Lowercase; collapse punctuation/whitespace to single space; strip."""
    if not text:
        return ""
    t = text.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def is_null(value):
    """True when value represents an absent / N/A annotation."""
    if value is None:
        return True
    return normalise(str(value)) in NULL_TOKENS


def split_multi(value):
    """Split a multi-value annotation cell into individual items.

    Splits on semicolons and newlines (the two separators used in
    paper_reviews.md). Does NOT split on commas — many software names
    and sample identifiers contain commas.
    """
    if not value:
        return []
    parts = re.split(r"[;\n]+", value)
    return [p.strip() for p in parts if p.strip()]


# ---------------------------------------------------------------------------
# Controlled vocabulary — alias to canonical mapping
# ---------------------------------------------------------------------------
def load_aliases(vocab_path):
    """Parse controlled_vocabulary.md into {normalised_alias: canonical}.

    Reads every markdown table that has a Canonical column and an Aliases
    column. Maps each alias (and the canonical itself) to the canonical.
    Returns an empty dict if the file is absent.
    """
    alias_map = {}
    if not vocab_path.exists():
        return alias_map

    content = vocab_path.read_text(encoding="utf-8")
    in_table = False
    canonical_col = None
    alias_col = None

    for line in content.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            in_table = False
            canonical_col = None
            alias_col = None
            continue

        cells = [c.strip() for c in line.strip("|").split("|")]

        if not in_table:
            lower = [c.lower() for c in cells]
            if "canonical" in lower:
                in_table = True
                canonical_col = lower.index("canonical")
                alias_col = lower.index("aliases") if "aliases" in lower else None
            continue

        if all(re.fullmatch(r":?-+:?", c) for c in cells if c):
            continue

        if canonical_col is not None and canonical_col < len(cells):
            canonical = cells[canonical_col]
            if not canonical or canonical.startswith("#"):
                continue
            alias_map[normalise(canonical)] = canonical
            if alias_col is not None and alias_col < len(cells):
                for alias in split_multi(cells[alias_col]):
                    if alias:
                        alias_map[normalise(alias)] = canonical

    return alias_map


# ---------------------------------------------------------------------------
# Ground truth parser
# ---------------------------------------------------------------------------
def _parse_markdown_table_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _cell_to_value(cell):
    if not cell or not cell.strip():
        return None
    cell = re.sub(r"\[([^\]]*)\]\([^\)]*\)", r"\1", cell)
    cell = re.sub(r"https?://\S+", "", cell)
    cell = cell.strip()
    if not cell or normalise(cell) in NULL_TOKENS:
        return None
    return cell


def parse_ground_truth(reviews_path):
    """Parse paper_reviews.md and return {doi: {field: [values...]}} dict.

    The DOI is taken from the At-a-glance table (DOI row).
    The six gap fields are drawn from:
      Section 3 table rows matching SECTION3_FIELD_MAP
      Section 4 dataset-identifier note for dataset_accession
      Section 4 sample/specimen note for sample_type (supplement)

    Absent / N/A cells produce an empty list (expected-null).
    """
    if not reviews_path.exists():
        raise FileNotFoundError(f"paper_reviews.md not found: {reviews_path}")

    content = reviews_path.read_text(encoding="utf-8")
    paper_blocks = re.split(r"\n(?=# [✅✓])", content)

    ground_truth = {}

    for block in paper_blocks:
        if not block.strip():
            continue

        doi = _extract_ataglance_doi(block)
        if not doi:
            continue

        fields = {f: [] for f in TARGET_FIELDS}
        _parse_section3(block, fields)
        _parse_section4(block, fields)

        ground_truth[doi] = fields

    return ground_truth


def _extract_ataglance_doi(block):
    ataglance = re.search(
        r"at-a-glance.*?\n(.*?)(?=###|\Z)", block,
        re.IGNORECASE | re.DOTALL,
    )
    if not ataglance:
        return None

    section = ataglance.group(1)
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = _parse_markdown_table_row(line)
        if len(cells) < 2:
            continue
        label = cells[0].lower().strip()
        if label == "doi":
            return _doi_from_cell(cells[1])
    return None


def _doi_from_cell(cell):
    """Extract and normalise a DOI from a markdown table cell.

    Handles three formats present in paper_reviews.md:
      1. Markdown link with doi.org URL in the target:
         [https://doi.org/10.x/y](https://doi.org/10.x/y)
      2. Plain DOI string: 10.x/y
      3. Plain doi.org URL: https://doi.org/10.x/y
    """
    if not cell:
        return None

    # 1. Markdown link: extract DOI from the link target URL.
    m = re.search(r"\]\((https?://[^\)]+)\)", cell)
    if m:
        return _normalise_doi(m.group(1))

    # 2. Markdown link display text that is itself a URL (no separate target).
    m = re.search(r"\[([^\]]+)\]", cell)
    if m:
        result = _normalise_doi(m.group(1))
        if result:
            return result

    # 3. Plain DOI or URL (no markdown markup).
    return _normalise_doi(cell.strip())


def _normalise_doi(raw):
    if not raw:
        return None
    low = raw.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/",
                   "http://dx.doi.org/", "doi.org/"):
        if low.startswith(prefix):
            low = low[len(prefix):]
            break
    return low if re.match(r"^10\.\d{4,}/.+", low) else None


def _parse_section3(block, fields):
    sec3 = re.search(
        r"###\s*\**3[.\s\\]*FT.ICR.*?\n(.*?)(?=###|\Z)",
        block, re.IGNORECASE | re.DOTALL,
    )
    if not sec3:
        return

    section = sec3.group(1)
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = _parse_markdown_table_row(line)
        if len(cells) < 2:
            continue
        label = cells[0].lower().strip()
        value_cell = _cell_to_value(cells[1]) if len(cells) > 1 else None

        for pattern, field in SECTION3_FIELD_MAP:
            if re.search(pattern, label, re.IGNORECASE):
                if value_cell and not is_null(value_cell):
                    items = split_multi(value_cell)
                    fields[field].extend(items)
                break


def _parse_section4(block, fields):
    sec4 = re.search(
        r"###\s*\**4[.\s\\]*Metadata.*?\n(.*?)(?=###|\Z)",
        block, re.IGNORECASE | re.DOTALL,
    )
    if not sec4:
        return

    section = sec4.group(1)
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = _parse_markdown_table_row(line)
        if len(cells) < 3:
            continue
        label = cells[0]
        present = cells[1].strip().lower()
        note = _cell_to_value(cells[2]) if len(cells) > 2 else None

        if SECTION4_DATASET_RE.search(label):
            if present in ("yes", "y") and note:
                for m in ACCESSION_RE.finditer(note):
                    acc = m.group(0).strip()
                    if acc and acc not in fields["dataset_accession"]:
                        fields["dataset_accession"].append(acc)

        if SECTION4_SAMPLE_RE.search(label):
            if present in ("yes", "y") and note and not is_null(note):
                items = split_multi(note)
                for item in items:
                    if item not in fields["sample_type"]:
                        fields["sample_type"].append(item)


# ---------------------------------------------------------------------------
# Prediction loader
# ---------------------------------------------------------------------------
def load_predictions(path):
    """Load pdf_extracted.jsonl into {doi: {field: value_or_None}} dict."""
    predictions = {}
    if not path.exists():
        return predictions

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            doi = _normalise_doi(rec.get("doi", ""))
            if not doi:
                continue

            pred = {}
            for field in TARGET_FIELDS:
                slot = rec.get(field, {})
                val = None
                if isinstance(slot, dict):
                    val = slot.get("value")
                elif isinstance(slot, str):
                    val = slot if slot else None
                pred[field] = val
            predictions[doi] = pred

    return predictions


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------
def match_values(predicted_val, expected_items, alias_map):
    """Check whether predicted_val matches any item in expected_items.

    Returns the match level: "exact", "overlap", "canonical", or None.
    """
    if not predicted_val or not expected_items:
        return None

    pred_norm = normalise(predicted_val)
    pred_canonical = alias_map.get(pred_norm, pred_norm)

    for exp in expected_items:
        exp_norm = normalise(exp)
        exp_canonical = alias_map.get(exp_norm, exp_norm)

        if pred_norm == exp_norm:
            return "exact"

        if pred_norm in exp_norm or exp_norm in pred_norm:
            return "overlap"

        if normalise(pred_canonical) == normalise(exp_canonical):
            return "canonical"

        pred_tokens = set(pred_canonical.lower().split())
        exp_tokens = set(exp_canonical.lower().split())
        if pred_tokens & exp_tokens:
            return "canonical"

    return None


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
def score_field(doi, field, predicted_val, expected_items, alias_map):
    """Score one field for one paper. Returns a dict with outcome and counts."""
    expected_null = len(expected_items) == 0
    predicted_null = is_null(predicted_val)

    if expected_null and predicted_null:
        return {"outcome": "TN", "tp": 0, "fp": 0, "fn": 0, "tn": 1, "match": None}

    if expected_null and not predicted_null:
        return {"outcome": "FP", "tp": 0, "fp": 1, "fn": 0, "tn": 0, "match": None}

    if not expected_null and predicted_null:
        return {
            "outcome": "FN",
            "tp": 0, "fp": 0,
            "fn": len(expected_items),
            "tn": 0,
            "match": None,
        }

    predicted_values = split_multi(predicted_val) if predicted_val else []

    tp_count = 0
    fn_count = 0
    fp_count = 0
    best_match = None

    for exp_item in expected_items:
        matched = False
        for pv in predicted_values:
            ml = match_values(pv, [exp_item], alias_map)
            if ml:
                if best_match is None:
                    best_match = ml
                matched = True
                break
        if matched:
            tp_count += 1
        else:
            fn_count += 1

    for pv in predicted_values:
        ml = match_values(pv, expected_items, alias_map)
        if not ml:
            fp_count += 1
        else:
            if best_match is None:
                best_match = ml

    if tp_count > 0:
        outcome = "TP"
    elif fp_count > 0:
        outcome = "FP"
    else:
        outcome = "FN"

    return {
        "outcome": outcome,
        "tp": tp_count,
        "fp": fp_count,
        "fn": fn_count,
        "tn": 0,
        "match": best_match,
    }


def compute_metrics(tp, fp, fn, tn):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0 else 0.0
    )
    return precision, recall, f1


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------
def build_report(per_paper_results, field_totals):
    lines = [
        "# PDF Extraction Evaluation Report",
        f"\nGenerated: {now_iso()}",
        f"\nGround truth source: `{PAPER_REVIEWS}`",
        f"Predictions source: `{PREDICTIONS_FILE}`",
        "\n---\n",
        "## Per-field summary\n",
    ]

    lines.append("| Field | TP | FP | FN | TN | Precision | Recall | F1 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    micro_tp = micro_fp = micro_fn = micro_tn = 0

    for field in TARGET_FIELDS:
        t = field_totals[field]
        tp, fp, fn, tn = t["tp"], t["fp"], t["fn"], t["tn"]
        p, r, f1 = compute_metrics(tp, fp, fn, tn)
        lines.append(
            f"| {field} | {tp} | {fp} | {fn} | {tn} "
            f"| {p:.2f} | {r:.2f} | {f1:.2f} |"
        )
        micro_tp += tp
        micro_fp += fp
        micro_fn += fn
        micro_tn += tn

    mp, mr, mf1 = compute_metrics(micro_tp, micro_fp, micro_fn, micro_tn)
    lines.append(
        f"| **MICRO TOTAL** | {micro_tp} | {micro_fp} | {micro_fn} | {micro_tn} "
        f"| **{mp:.2f}** | **{mr:.2f}** | **{mf1:.2f}** |"
    )

    field_f1s = []
    for field in TARGET_FIELDS:
        t = field_totals[field]
        _, _, f1 = compute_metrics(t["tp"], t["fp"], t["fn"], t["tn"])
        field_f1s.append(f1)
    macro_f1 = sum(field_f1s) / len(field_f1s) if field_f1s else 0.0
    lines.append(f"\n**Macro F1 (average across fields): {macro_f1:.2f}**\n")

    lines.append("\n---\n\n## Per-paper detail\n")
    for doi, paper_result in sorted(per_paper_results.items()):
        lines.append(f"### `{doi}`\n")
        lines.append("| Field | Expected | Predicted | Outcome | Match level |")
        lines.append("|---|---|---|---|---|")
        for field in TARGET_FIELDS:
            fr = paper_result.get(field, {})
            expected_disp = "; ".join(fr.get("expected", [])) or "N/A"
            predicted_disp = fr.get("predicted") or "N/A"
            outcome = fr.get("outcome", "N/A")
            match = fr.get("match") or "N/A"
            lines.append(
                f"| {field} | {expected_disp} | {predicted_disp} "
                f"| {outcome} | {match} |"
            )
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(print_gt_only=False):
    alias_map = load_aliases(CONTROLLED_VOCAB)
    ground_truth = parse_ground_truth(PAPER_REVIEWS)

    if print_gt_only:
        print(f"Parsed ground truth for {len(ground_truth)} papers:\n")
        for doi, fields in sorted(ground_truth.items()):
            print(f"  {doi}")
            for field, values in fields.items():
                vals = "; ".join(values) if values else "N/A"
                print(f"    {field:22s}: {vals}")
        print()
        return 0

    if not ground_truth:
        print(f"ERROR: no ground truth parsed from {PAPER_REVIEWS}")
        return 1

    predictions = load_predictions(PREDICTIONS_FILE)
    if not predictions:
        print(
            f"No predictions found at {PREDICTIONS_FILE}.\n"
            "Run 02d_extract_pdf.py on the 8 ground-truth DOIs first, "
            "then re-run this harness to score them."
        )

    per_paper_results = {}
    field_totals = {f: {"tp": 0, "fp": 0, "fn": 0, "tn": 0} for f in TARGET_FIELDS}
    jsonl_rows = []

    for doi, expected_fields in ground_truth.items():
        pred = predictions.get(doi, {})
        paper_result = {}

        for field in TARGET_FIELDS:
            expected_items = expected_fields.get(field, [])
            predicted_val = pred.get(field)

            s = score_field(doi, field, predicted_val, expected_items, alias_map)

            paper_result[field] = {
                "expected": expected_items,
                "predicted": predicted_val,
                "outcome": s["outcome"],
                "match": s["match"],
            }

            for k in ("tp", "fp", "fn", "tn"):
                field_totals[field][k] += s[k]

        per_paper_results[doi] = paper_result
        jsonl_rows.append({
            "doi": doi,
            "scored_at": now_iso(),
            "fields": {
                f: {
                    "expected": expected_fields.get(f, []),
                    "predicted": pred.get(f),
                    "outcome": paper_result[f]["outcome"],
                    "match": paper_result[f]["match"],
                }
                for f in TARGET_FIELDS
            },
        })

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_JSONL.parent.mkdir(parents=True, exist_ok=True)

    report_text = build_report(per_paper_results, field_totals)
    REPORT_OUT.write_text(report_text, encoding="utf-8")

    with open(RESULTS_JSONL, "w", encoding="utf-8") as f:
        for row in jsonl_rows:
            f.write(json.dumps(row) + "\n")

    print(f"\nEvaluated {len(ground_truth)} papers x {len(TARGET_FIELDS)} fields")
    print(f"Predictions matched: {len(predictions)} of {len(ground_truth)} papers")
    print()
    print(f"{'Field':<24} {'P':>6} {'R':>6} {'F1':>6}")
    print("-" * 45)
    macro_f1s = []
    for field in TARGET_FIELDS:
        t = field_totals[field]
        p, r, f1 = compute_metrics(t["tp"], t["fp"], t["fn"], t["tn"])
        macro_f1s.append(f1)
        print(f"  {field:<22} {p:>6.2f} {r:>6.2f} {f1:>6.2f}")
    print("-" * 45)
    macro = sum(macro_f1s) / len(macro_f1s)
    print(f"  {'Macro F1':<22} {'':>6} {'':>6} {macro:>6.2f}")
    print()
    print(f"Report: {REPORT_OUT}")
    print(f"Results JSONL: {RESULTS_JSONL}")
    return 0


if __name__ == "__main__":
    flag = "--print-ground-truth" in sys.argv
    sys.exit(main(print_gt_only=flag))
