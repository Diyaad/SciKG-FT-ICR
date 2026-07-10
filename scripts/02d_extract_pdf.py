"""
02d_extract_pdf.py — SciKG pipeline stage 2d (PDF gap-field extract)

An EXTRACT-layer stage, sibling to 02_extract.py (CrossRef), the CSV
extractor, and the RAW-file extractor. It runs AFTER the CrossRef stage and
only adds the handful of fields CrossRef cannot provide — instrument,
ionization method, sample type, facility, software tools, dataset accession —
by reading the paper's PDF. It NEVER re-fetches or overwrites a CrossRef
bibliographic field, and it never infers a value that is not present in the
PDF text. Missing or unfound fields are written as null.

Four stages run per DOI, each one logged:

  1. ACQUIRE PDF   — reuse a local PDF at data/raw/pdfs/{doi_safe}.pdf if
                     present; otherwise ask the Unpaywall API for an
                     open-access PDF URL and download it there. If no PDF can
                     be obtained, the DOI is logged "no_pdf_found" and skipped
                     to the next DOI — the run never aborts and no field is
                     fabricated.

  2. PDF -> TEXT   — Layer 1. Docling converts the PDF to structured Markdown.
                     The full Markdown is saved to
                     data/processed/pdf_text/{doi_safe}.md as a human-
                     inspectable debugging artifact. The Methods/Experimental
                     section and the data-availability statement are isolated
                     when they can be found; otherwise the full text is used,
                     and which was used is logged. The Layer-1 extractor is
                     swappable (see convert_pdf_to_text) so pdfplumber can be
                     dropped in later without changing the rest of the script.

  3. TEXT -> FIELDS — Layer 2. LangExtract pulls the six target gap fields from
                     the text using a prompt plus a couple of generic few-shot
                     examples (deliberately NOT drawn from the ground-truth set,
                     so no answers leak into the extractor). LangExtract's
                     source grounding is captured for every field: the exact
                     source snippet and character span. A field LangExtract
                     cannot locate in the source text (its hallucination signal)
                     is marked "ungrounded" with a null snippet — the flag is
                     never dropped silently.

  4. CROSS-CHECK   — identity verification against the CrossRef record for the
                     same DOI (loaded once from
                     data/processed/entities/publications.jsonl). The primary
                     purpose is to confirm we extracted from the RIGHT PDF: the
                     PDF title (and the DOI string, when printed) is compared to
                     the CrossRef title/doi using normalized, fuzzy matching. A
                     clear mismatch is flagged loudly ("pdf_identity_mismatch")
                     so a human reviews it — the record is never discarded and
                     its values are never altered. As a secondary step, any
                     target field that ALSO appears in the CrossRef record (in
                     practice only dataset_accession ever might) is reconciled;
                     CrossRef always wins and the PDF value is recorded only as
                     a logged disagreement.

This stage writes JSONL only. It does NOT touch Neo4j, and it does NOT modify
any existing file in data/raw/ — it only adds new PDF files there and appends
a stage marker to the operational manifest, exactly as 01/02 already do.

Dependencies (see requirements.txt): docling, langextract, requests.
The LLM model id and API key are read from the environment / a .env file
(LANGEXTRACT_MODEL_ID, LANGEXTRACT_API_KEY). .env is already git-ignored.
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional at runtime; env vars still work
    pass

# --- Default input ---------------------------------------------------------
# General by design: this script takes ANY DOIs. Provide them on the command
# line (each arg a DOI, or a single arg pointing at a text file with one DOI
# per line), or edit this default list. Empty by default so a bare run never
# guesses at a corpus.
DOIS = []

# --- Paths -----------------------------------------------------------------
PDFS_DIR = Path("data/raw/pdfs")
PDF_TEXT_DIR = Path("data/processed/pdf_text")
CROSSREF_ENTITIES = Path("data/processed/entities/publications.jsonl")
OUTPUT = Path("data/processed/entities/pdf_extracted.jsonl")
LOG = Path("data/processed/logs/pdf_extraction_log.jsonl")
MANIFEST = Path("data/raw/manifest.json")

# --- External services -----------------------------------------------------
# Unpaywall requires a contact email in every request. Set this to a real,
# monitored address before running against many DOIs.
UNPAYWALL_EMAIL = "scikg@research.org"
DOWNLOAD_HEADERS = {"User-Agent": "SciKG/0.1 (mailto:scikg@research.org)"}

# --- LLM / extractor config ------------------------------------------------
# Model choice and API key come from the environment / .env (never hard-coded).
# LangExtract's documented default provider is Gemini; override LANGEXTRACT_MODEL_ID
# to point at whatever provider this project standardizes on.
DEFAULT_MODEL_ID = "gemini-2.5-flash"
MODEL_ID = os.environ.get("LANGEXTRACT_MODEL_ID", DEFAULT_MODEL_ID)
LANGEXTRACT_API_KEY = os.environ.get("LANGEXTRACT_API_KEY")
# Backend: "ollama" (default, local, no API key) or "gemini".
LANGEXTRACT_BACKEND = os.environ.get("LANGEXTRACT_BACKEND", "ollama")
OLLAMA_MODEL_ID = os.environ.get("OLLAMA_MODEL_ID", "llama3.1:8b")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
# The model that actually runs — use this for provenance/logging.
ACTIVE_MODEL = OLLAMA_MODEL_ID if LANGEXTRACT_BACKEND == "ollama" else MODEL_ID

# --- Layer-1 backend (swappable) -------------------------------------------
# "docling" (default) or "pdfplumber". The rest of the script does not care
# which backend produced the text — see convert_pdf_to_text().
PDF_TEXT_BACKEND = "docling"

# --- Target gap fields -----------------------------------------------------
# The ONLY fields this stage produces. CrossRef does not supply these; that is
# the entire reason this stage exists.
TARGET_FIELDS = [
    "instrument",
    "ionization_method",
    "sample_type",
    "facility",
    "software_tools",
    "dataset_accession",
]

# LangExtract alignment statuses we accept as grounded.
ACCEPTED_ALIGNMENTS = ("MATCH_EXACT", "MATCH_FUZZY")
# For any other status, the aligned span must cover at least this
# fraction of the extracted value's length.
MIN_SPAN_COVERAGE = 0.55

SOURCE_LABEL = "pdf_docling_langextract"

# Title-similarity threshold for the identity check (token Jaccard). Documented,
# deliberately simple, not over-engineered.
TITLE_JACCARD_THRESHOLD = 0.7


def _is_grounded(ex, char):
    if char is None:
        return False
    status = str(getattr(ex, "alignment_status", "") or "")
    if any(status.endswith(s) for s in ACCEPTED_ALIGNMENTS):
        return True
    # MATCH_LESSER and anything unrecognised: require the aligned span to
    # cover most of the value, so a one-word overlap cannot ground a long
    # fabricated string.
    value_len = len(ex.extraction_text or "")
    span_len = max(0, char.end_pos - char.start_pos)
    return value_len > 0 and (span_len / value_len) >= MIN_SPAN_COVERAGE


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def make_doi_safe(doi):
    # Same rule as 01_fetch.py so PDF filenames line up with raw fetch outputs.
    return doi.replace("/", "_").replace(".", "_")


# ---------------------------------------------------------------------------
# CrossRef reference index (loaded once at startup)
# ---------------------------------------------------------------------------
def load_crossref_index(path):
    """Index the stage-02 CrossRef output by normalized DOI.

    Missing file or unparsable lines are tolerated: a DOI with no CrossRef
    record is handled downstream as "unverifiable", never as a failure.
    """
    index = {}
    if not path.exists():
        return index
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            doi = rec.get("doi")
            if doi:
                index[doi.lower().strip()] = rec
    return index


# ---------------------------------------------------------------------------
# Manifest stage-tracking (mirrors 01/02; the manifest is the operational
# pipeline-state tracker that 01/02 already maintain, not raw scientific data)
# ---------------------------------------------------------------------------
def load_manifest():
    if not MANIFEST.exists():
        return None
    try:
        with open(MANIFEST, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_manifest(manifest):
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def manifest_key_for(manifest, doi):
    if not manifest:
        return None
    for key in manifest.get("papers", {}):
        if key.lower() == doi.lower():
            return key
    return None


def mark_manifest_pdf_extract(manifest, key):
    stages = manifest["papers"][key].setdefault("stages_complete", [])
    if "pdf_extract" not in stages:
        stages.append("pdf_extract")
    save_manifest(manifest)


# ---------------------------------------------------------------------------
# STAGE 1 — acquire PDF
# ---------------------------------------------------------------------------
def query_unpaywall(doi):
    """Return an open-access PDF URL for this DOI, or None."""
    url = f"https://api.unpaywall.org/v2/{doi}?email={UNPAYWALL_EMAIL}"
    response = requests.get(url, timeout=30)
    time.sleep(1)
    if response.status_code != 200:
        return None
    data = response.json()
    location = data.get("best_oa_location") or {}
    return location.get("url_for_pdf")


def download_pdf(url, dest):
    """Download a PDF to dest. Returns True on success.

    Verifies the payload is actually a PDF (starts with the %PDF- magic bytes)
    before writing. Publishers routinely return HTML paywall/error pages with
    HTTP 200; since data/raw/pdfs is immutable after write, saving one would
    poison every future run, so a non-PDF response is rejected and logged rather
    than written.
    """
    response = requests.get(url, headers=DOWNLOAD_HEADERS, timeout=60)
    time.sleep(1)
    if response.status_code != 200 or not response.content:
        return False
    if not response.content.startswith(b"%PDF-"):
        preview = response.content[:80].decode("utf-8", errors="replace")
        print(
            "REJECT non-PDF download (not written): "
            f"url={url} status={response.status_code} "
            f"content_type={response.headers.get('Content-Type')!r} "
            f"first80={preview!r}",
            file=sys.stderr,
        )
        return False
    dest.write_bytes(response.content)
    return True


def acquire_pdf(doi, doi_safe):
    """Return (path, source) where source is "local", "unpaywall", or "none".

    A local PDF is reused and never overwritten (data/raw is immutable). A
    downloaded PDF is written only if one is not already present.
    """
    local = PDFS_DIR / f"{doi_safe}.pdf"
    if local.exists():
        return local, "local"

    try:
        pdf_url = query_unpaywall(doi)
    except requests.RequestException:
        pdf_url = None

    if pdf_url:
        try:
            PDFS_DIR.mkdir(parents=True, exist_ok=True)
            if download_pdf(pdf_url, local):
                return local, "unpaywall"
        except requests.RequestException:
            pass

    return None, "none"


# ---------------------------------------------------------------------------
# STAGE 2 — PDF -> text (Layer 1, swappable backend)
# ---------------------------------------------------------------------------
def _docling_to_text(pdf_path):
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    # OCR disabled: RapidOCR is broken on this install
    # ("Unsupported configuration: torch.PP-OCRv6.det.small") and the PDFs are
    # born-digital, so OCR is unnecessary.
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    result = converter.convert(str(pdf_path))
    return result.document.export_to_markdown()


def _pdfplumber_to_text(pdf_path):
    # Fallback Layer-1 backend. Kept here so it can be selected via
    # PDF_TEXT_BACKEND without touching the rest of the script.
    import pdfplumber

    pages = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n\n".join(pages)


def convert_pdf_to_text(pdf_path, backend=PDF_TEXT_BACKEND):
    """Stable Layer-1 interface: PDF path -> text. Returns None on failure.

    Dispatches to the configured backend. Any backend just needs to return a
    string of extracted text; nothing downstream depends on which one ran, so a
    new backend (e.g. pdfplumber) can be dropped in without other changes.
    """
    try:
        if backend == "docling":
            return _docling_to_text(pdf_path)
        if backend == "pdfplumber":
            return _pdfplumber_to_text(pdf_path)
        raise ValueError(f"unknown PDF_TEXT_BACKEND: {backend}")
    except Exception:
        # Backend missing or conversion failed — caller flags docling_failed.
        return None


# Section headers that mark the regions where the target fields live.
_METHODS_RE = re.compile(
    r"^#{1,6}\s*.*(methods?|experimental|materials\s+and\s+methods)",
    re.IGNORECASE,
)
_DATA_AVAIL_RE = re.compile(
    r"^#{1,6}\s*.*(data\s+availability|availability\s+of\s+data|"
    r"accession|deposited)",
    re.IGNORECASE,
)

# Docling flattens all headings to level 2, so heading level carries no
# information. A Methods section therefore runs until the next MAJOR
# section, identified by name. Derived from the 8-paper ground-truth set;
# papers using other conventions fall back to full text via
# MIN_SECTION_CHARS.
_SECTION_STOP_RE = re.compile(
    r"^#{1,6}\s*[\W_]*\s*(?:\d+(?:\.\d+)*\.?\s*)?"
    r"(results?|discussion|conclusions?|acknowledg(?:e)?ments?|"
    r"references?|associated\s+content|author\s+information|"
    r"abbreviations?|supporting\s+information|footnotes?|"
    r"data\s+availability|competing\s+interests?|conflicts?\s+of\s+interest)"
    r"\b",
    re.IGNORECASE,
)

# A slice shorter than this is treated as a failed isolation, not a short
# section — fall back to the full text rather than feeding the model a
# heading-only stub (the original bug reproduced the few-shot examples).
MIN_SECTION_CHARS = 500

def isolate_relevant_sections(markdown):
    """Return (text, text_source) where text_source is "methods" or "full".

    Pulls the Methods/Experimental section and the data-availability statement
    (the regions where instrument/ionization/sample/facility/software/accession
    are reported). Because Docling flattens every heading to level 2, heading
    level carries no information; a section instead runs from its heading until
    the next heading matching _SECTION_STOP_RE (a named major section), or the
    document end. Every other heading — subsections, repeated running headers —
    is ignored and its content collected. A stop heading that is ALSO a
    data-availability heading ends the current span and begins a new one (that is
    where an accession is found), so it is never swallowed. Overlapping or nested
    spans are merged so a section is not emitted twice. Falls back to the full
    text when no span is found or the joined slice is shorter than
    MIN_SECTION_CHARS.
    """
    lines = markdown.splitlines()
    spans = []
    for i, line in enumerate(lines):
        if not (_METHODS_RE.match(line) or _DATA_AVAIL_RE.match(line)):
            continue
        # Collect lines until the next MAJOR-section heading (or document end).
        # Start scanning at i+1 so this heading never terminates its own span,
        # even when it is itself a stop heading (e.g. "## Data availability").
        end = len(lines)
        for j in range(i + 1, len(lines)):
            if _SECTION_STOP_RE.match(lines[j]):
                end = j
                break
        spans.append((i, end))

    spans.sort()
    merged = []
    for s, e in spans:
        if merged and s < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    if merged:
        text = "\n\n".join("\n".join(lines[s:e]) for s, e in merged)
        if len(text) >= MIN_SECTION_CHARS:
            return text, "methods"
    return markdown, "full"


# ---------------------------------------------------------------------------
# STAGE 3 — text -> fields (Layer 2, LangExtract)
# ---------------------------------------------------------------------------
# Extraction prompt for mass-spectrometry papers.
EXTRACTION_PROMPT = (
    "Extract experimental metadata from this mass-spectrometry methods text. "
    "Pull only values explicitly stated in the text; do not infer or guess. "
    "Use these extraction classes: instrument (the mass spectrometer model), "
    "ionization_method (e.g. ESI, MALDI, nanoESI), sample_type (what was "
    "analyzed), facility (the named lab or core facility), software_tools "
    "(data-analysis software), dataset_accession (a repository accession such "
    "as a ProteomeXchange/MassIVE/OSF/Zenodo identifier). Use the exact words "
    "from the source text for each extraction."
)


def build_examples():
    """Few-shot examples for LangExtract.

    IMPORTANT: these are generic, illustrative extractor-priming snippets — NOT
    records loaded into the graph, and deliberately drawn from unrelated MS
    contexts (Orbitrap bottom-up proteomics, MALDI imaging) so that NO answer
    from the ground-truth FT-ICR set leaks into the extractor.
    """
    import langextract as lx

    return [
        lx.data.ExampleData(
            text=(
                "Tryptic peptides were analyzed on a Thermo Q Exactive HF "
                "Orbitrap mass spectrometer equipped with a nanoelectrospray "
                "ionization source. Raw files were processed with MaxQuant "
                "v1.6. Data are available at ProteomeXchange under accession "
                "PXD012345."
            ),
            extractions=[
                lx.data.Extraction(
                    extraction_class="instrument",
                    extraction_text="Thermo Q Exactive HF Orbitrap",
                ),
                lx.data.Extraction(
                    extraction_class="ionization_method",
                    extraction_text="nanoelectrospray ionization",
                ),
                lx.data.Extraction(
                    extraction_class="sample_type",
                    extraction_text="Tryptic peptides",
                ),
                lx.data.Extraction(
                    extraction_class="software_tools",
                    extraction_text="MaxQuant v1.6",
                ),
                lx.data.Extraction(
                    extraction_class="dataset_accession",
                    extraction_text="PXD012345",
                ),
            ],
        ),
        lx.data.ExampleData(
            text=(
                "Tissue sections were imaged using matrix-assisted laser "
                "desorption/ionization (MALDI) on a Bruker timsTOF instrument "
                "at the Proteomics Core Facility. Spectra were analyzed in "
                "SCiLS Lab."
            ),
            extractions=[
                lx.data.Extraction(
                    extraction_class="instrument",
                    extraction_text="Bruker timsTOF",
                ),
                lx.data.Extraction(
                    extraction_class="ionization_method",
                    extraction_text=(
                        "matrix-assisted laser desorption/ionization (MALDI)"
                    ),
                ),
                lx.data.Extraction(
                    extraction_class="sample_type",
                    extraction_text="Tissue sections",
                ),
                lx.data.Extraction(
                    extraction_class="facility",
                    extraction_text="Proteomics Core Facility",
                ),
                lx.data.Extraction(
                    extraction_class="software_tools",
                    extraction_text="SCiLS Lab",
                ),
            ],
        ),
    ]


def empty_field():
    return {
        "value": None,
        "source_snippet": None,
        "grounded": False,
        "confidence": None,
        "char_span": None,
    }


def extract_fields(text):
    """Run LangExtract over the text.

    Returns (fields, all_extractions, flags). `fields` maps each target field
    to {value, source_snippet, grounded, confidence, char_span}. Source
    grounding is captured for every extraction; an extraction LangExtract
    cannot locate in the source (char_interval is None) is recorded as
    ungrounded with a null snippet and raises the "ungrounded_field" flag — the
    hallucination signal is never dropped silently. Returns
    (None, [], ["langextract_failed"]) if the extractor errors.
    """
    fields = {f: empty_field() for f in TARGET_FIELDS}
    all_extractions = []
    flags = []

    try:
        import langextract as lx

        if LANGEXTRACT_BACKEND == "ollama":
            result = lx.extract(
                text_or_documents=text,
                prompt_description=EXTRACTION_PROMPT,
                examples=build_examples(),
                model_id=OLLAMA_MODEL_ID,
                model_url=OLLAMA_URL,
                fence_output=False,
                use_schema_constraints=True,
            )
        else:
            result = lx.extract(
                text_or_documents=text,
                prompt_description=EXTRACTION_PROMPT,
                examples=build_examples(),
                model_id=MODEL_ID,
                api_key=LANGEXTRACT_API_KEY,
            )
    except Exception as e:
        import traceback
        print("LANGEXTRACT ERROR:", repr(e))
        traceback.print_exc()
        return None, [], ["langextract_failed"]

    # Collect, per extraction_class, ONLY the grounded extractions, preserving
    # order and de-duplicating on the normalized extraction_text so the same
    # value is not listed twice. Every extraction (grounded or not) is still
    # appended to all_extractions, unchanged, as the full provenance record.
    grounded_by_class = {f: [] for f in TARGET_FIELDS}
    seen_by_class = {f: set() for f in TARGET_FIELDS}
    seen_classes = set()

    for ex in getattr(result, "extractions", []) or []:
        cls = ex.extraction_class
        char = getattr(ex, "char_interval", None)
        grounded = _is_grounded(ex, char)
        span = [char.start_pos, char.end_pos] if char is not None else None
        align = getattr(ex, "alignment_status", None)
        span_len = max(0, char.end_pos - char.start_pos) if char is not None else 0
        value_len = len(ex.extraction_text or "")

        all_extractions.append(
            {
                "field": cls,
                "value": ex.extraction_text,
                "grounded": grounded,
                "char_span": span,
                "alignment_status": str(align) if align is not None else None,
                "span_coverage": round(span_len / value_len, 3)
                if (char and ex.extraction_text)
                else None,
            }
        )

        if cls in seen_by_class:
            seen_classes.add(cls)

        if not grounded:
            flags.append("ungrounded_field")
            continue

        if cls not in grounded_by_class:
            continue

        # De-dup on case-insensitive, whitespace-collapsed text.
        norm = re.sub(r"\s+", " ", ex.extraction_text).strip().lower()
        if norm in seen_by_class[cls]:
            continue
        seen_by_class[cls].add(norm)
        grounded_by_class[cls].append(ex)

    # Fill each field from its grounded extractions. If a class had extractions
    # but none grounded, record it so the log distinguishes "model said
    # nothing" from "model hallucinated and we rejected it". Never fall back to
    # an ungrounded value — null-never-inferred.
    for cls in TARGET_FIELDS:
        grounded_exs = grounded_by_class[cls]
        if grounded_exs:
            first = grounded_exs[0]
            fields[cls] = {
                "value": "; ".join(g.extraction_text for g in grounded_exs),
                "source_snippet": first.extraction_text,
                "grounded": True,
                "confidence": "grounded",
                "char_span": [first.char_interval.start_pos, first.char_interval.end_pos],
            }
        elif cls in seen_classes:
            flags.append("field_all_ungrounded:" + cls)

    return fields, all_extractions, flags


# ---------------------------------------------------------------------------
# STAGE 4 — cross-check against CrossRef
# ---------------------------------------------------------------------------
def normalize_text(value):
    if not value:
        return ""
    value = value.lower()
    value = re.sub(r"[^\w\s]", " ", value)  # strip punctuation
    value = re.sub(r"\s+", " ", value).strip()
    return value


def titles_match(pdf_title, crossref_title):
    """Documented, deliberately-simple title match.

    Normalize (lowercase, strip punctuation, collapse whitespace) then treat as
    a match if one normalized title contains the other OR token Jaccard overlap
    >= TITLE_JACCARD_THRESHOLD. Returns True/False, or None if either title is
    empty after normalization.
    """
    a = normalize_text(pdf_title)
    b = normalize_text(crossref_title)
    if not a or not b:
        return None
    if a in b or b in a:
        return True
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return None
    jaccard = len(ta & tb) / len(ta | tb)
    return jaccard >= TITLE_JACCARD_THRESHOLD


def extract_pdf_title(markdown):
    """Best-effort PDF title: first Markdown H1, else first non-empty line."""
    if not markdown:
        return None
    for line in markdown.splitlines():
        m = re.match(r"^#\s+(.*\S)", line)
        if m:
            return m.group(1).strip()
    for line in markdown.splitlines():
        if line.strip():
            return line.strip()
    return None


def cross_check(doi, markdown, fields, crossref_rec):
    """Identity verification + overlap reconciliation. Returns (check, flags).

    CrossRef always wins on any overlapping field; the PDF value is recorded
    only as a logged disagreement. The record is never discarded and its values
    are never altered here.
    """
    flags = []
    check = {
        "crossref_record_found": crossref_rec is not None,
        "identity_status": None,
        "title_match": None,
        "doi_in_pdf_match": None,
        "field_disagreements": [],
    }

    if crossref_rec is None:
        check["identity_status"] = "unverifiable"
        flags.append("crossref_record_missing")
        return check, flags

    # --- Identity check (primary) ---
    pdf_title = extract_pdf_title(markdown)
    crossref_title = crossref_rec.get("title")

    if pdf_title is None:
        check["title_match"] = None
        check["identity_status"] = "unverifiable"
        flags.append("identity_unverifiable")
    else:
        match = titles_match(pdf_title, crossref_title)
        if match is True:
            check["title_match"] = True
            check["identity_status"] = "ok"
        elif match is False:
            check["title_match"] = False
            check["identity_status"] = "mismatch"
            flags.append("pdf_identity_mismatch")
        else:
            check["title_match"] = None
            check["identity_status"] = "unverifiable"
            flags.append("identity_unverifiable")

    # DOI printed on the page? Only confirm a positive match; absence is not a
    # mismatch (many PDFs do not print the DOI), so it stays null.
    crossref_doi = (crossref_rec.get("doi") or doi or "").lower().strip()
    normalized_md = normalize_text(markdown)
    if crossref_doi and normalize_text(crossref_doi) in normalized_md:
        check["doi_in_pdf_match"] = True

    # --- Overlap reconciliation (secondary) ---
    # In practice only dataset_accession may overlap; CrossRef records from
    # stage 02 do not carry these gap fields, so this is usually empty.
    for field in TARGET_FIELDS:
        crossref_value = crossref_rec.get(field)
        pdf_value = fields.get(field, {}).get("value") if fields else None
        if crossref_value and pdf_value:
            if normalize_text(str(crossref_value)) != normalize_text(str(pdf_value)):
                check["field_disagreements"].append(
                    {
                        "field": field,
                        "crossref_value": crossref_value,
                        "pdf_value": pdf_value,
                    }
                )
                flags.append("field_disagreement")

    return check, flags


# ---------------------------------------------------------------------------
# Record + log builders
# ---------------------------------------------------------------------------
def append_jsonl(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def build_output_record(doi, fields, all_extractions, pdf_source, text_source,
                        crossref_check, evidence_note):
    record = {
        "doi": doi,
        "source": SOURCE_LABEL,
        "pdf_source": pdf_source,
        "text_source": text_source,
        "model_used": ACTIVE_MODEL,
        "extracted_at": now_iso(),
        "evidence_note": evidence_note,
        "crossref_check": crossref_check,
        "all_field_extractions": all_extractions,
    }
    # Target gap fields live at the top level of the record.
    for field in TARGET_FIELDS:
        record[field] = (fields or {}).get(field, empty_field())
    return record


def build_log_record(doi, pdf_source, docling_ok, text_source, fields,
                     identity_status, flags):
    field_log = {}
    for field in TARGET_FIELDS:
        slot = (fields or {}).get(field, empty_field())
        field_log[field] = {
            "value": slot["value"],
            "grounded": slot["grounded"],
        }
    return {
        "timestamp": now_iso(),
        "doi": doi,
        "pdf_acquisition": {
            "status": "found" if pdf_source != "none" else "no_pdf_found",
            "source": pdf_source,
        },
        "docling_succeeded": docling_ok,
        "text_source": text_source,
        "fields": field_log,
        "identity_status": identity_status,
        "flags": sorted(set(flags)),
        "model_used": ACTIVE_MODEL,
    }


# ---------------------------------------------------------------------------
# Input resolution
# ---------------------------------------------------------------------------
def resolve_input_dois(argv):
    """DOIs from argv (each arg a DOI, or one arg = a file of DOIs), else DOIS."""
    if not argv:
        return list(DOIS)
    if len(argv) == 1 and Path(argv[0]).exists():
        dois = []
        with open(argv[0], encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    dois.append(line)
        return dois
    return list(argv)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    dois = resolve_input_dois(sys.argv[1:])

    if not dois:
        print(
            "No DOIs supplied. Pass DOIs as arguments, give a file of DOIs "
            "(one per line), or set the DOIS list at the top of the script."
        )
        return

    # Ensure output directories exist (creating new dirs only; never modifying
    # existing data/raw files).
    PDF_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)

    crossref_index = load_crossref_index(CROSSREF_ENTITIES)
    manifest = load_manifest()

    # Run aggregates for the human-readable summary.
    total = len(dois)
    pdfs_found = 0
    fields_extracted = 0
    ungrounded_count = 0
    flagged_count = 0
    identity_counts = {"ok": 0, "mismatch": 0, "unverifiable": 0}
    mismatch_dois = []

    for doi_index, doi in enumerate(dois):
        # Rate-limit to stay under the free-tier Gemini limit (5 req/min).
        # Delay BETWEEN papers only — never before the first, never after the
        # last. Placed at the top of the loop so it applies on every path,
        # including the early `continue` branches below.
        if doi_index > 0 and LANGEXTRACT_BACKEND != "ollama":
            time.sleep(15)

        doi_safe = make_doi_safe(doi)
        crossref_rec = crossref_index.get(doi.lower().strip())

        # Idempotency: skip DOIs already marked pdf_extract in the manifest.
        manifest_key = manifest_key_for(manifest, doi)
        if manifest_key and "pdf_extract" in (
            manifest["papers"][manifest_key].get("stages_complete", [])
        ):
            print(f"SKIP    {doi} (already pdf-extracted)")
            continue

        flags = []

        # --- STAGE 1: acquire PDF ---
        pdf_path, pdf_source = acquire_pdf(doi, doi_safe)
        if pdf_path is None:
            flags.append("no_pdf_found")
            crossref_check = {
                "crossref_record_found": crossref_rec is not None,
                "identity_status": "unverifiable",
                "title_match": None,
                "doi_in_pdf_match": None,
                "field_disagreements": [],
            }
            record = build_output_record(
                doi, None, [], "none", None, crossref_check,
                "No PDF could be acquired; no fields extracted.",
            )
            append_jsonl(OUTPUT, record)
            append_jsonl(
                LOG,
                build_log_record(doi, "none", False, None, None,
                                 "unverifiable", flags),
            )
            identity_counts["unverifiable"] += 1
            flagged_count += 1
            print(f"NO_PDF  {doi}")
            continue

        pdfs_found += 1

        # --- STAGE 2: PDF -> text ---
        markdown = convert_pdf_to_text(pdf_path)
        docling_ok = markdown is not None
        if not docling_ok:
            flags.append("docling_failed")
            crossref_check = {
                "crossref_record_found": crossref_rec is not None,
                "identity_status": "unverifiable",
                "title_match": None,
                "doi_in_pdf_match": None,
                "field_disagreements": [],
            }
            record = build_output_record(
                doi, None, [], pdf_source, None, crossref_check,
                "PDF acquired but text conversion failed; no fields extracted.",
            )
            append_jsonl(OUTPUT, record)
            append_jsonl(
                LOG,
                build_log_record(doi, pdf_source, False, None, None,
                                 "unverifiable", flags),
            )
            identity_counts["unverifiable"] += 1
            flagged_count += 1
            print(f"NOTEXT  {doi} (Docling failed)")
            continue

        # Save the full Markdown as a human-inspectable debugging artifact.
        # Docling can emit undecodable bytes as lone surrogates; a strict UTF-8
        # write would raise and kill the whole run on a single bad paper. Write
        # with errors="replace" and, when any character actually had to be
        # replaced, flag the paper so the log records which ones were affected
        # instead of silently corrupting them.
        try:
            markdown.encode("utf-8")
        except UnicodeEncodeError:
            flags.append("text_decode_replaced")
        (PDF_TEXT_DIR / f"{doi_safe}.md").write_text(
            markdown, encoding="utf-8", errors="replace"
        )

        text, text_source = isolate_relevant_sections(markdown)

        # --- STAGE 3: text -> fields ---
        fields, all_extractions, field_flags = extract_fields(text)
        flags.extend(field_flags)

        # --- STAGE 4: cross-check against CrossRef ---
        check, check_flags = cross_check(doi, markdown, fields, crossref_rec)
        flags.extend(check_flags)

        identity_status = check["identity_status"]
        if identity_status in identity_counts:
            identity_counts[identity_status] += 1
        if identity_status == "mismatch":
            mismatch_dois.append(doi)

        evidence_note = (
            "Gap fields extracted from PDF via Docling + LangExtract "
            f"(model {ACTIVE_MODEL}); identity cross-checked against CrossRef "
            "record. CrossRef bibliographic fields are never overwritten."
        )
        record = build_output_record(
            doi, fields, all_extractions, pdf_source, text_source, check,
            evidence_note,
        )
        append_jsonl(OUTPUT, record)
        append_jsonl(
            LOG,
            build_log_record(doi, pdf_source, True, text_source, fields,
                             identity_status, flags),
        )

        # Tally grounded / ungrounded fields and flags for the summary.
        for field in TARGET_FIELDS:
            slot = (fields or {}).get(field, empty_field())
            if slot["value"] is not None and slot["grounded"]:
                fields_extracted += 1
            if slot["value"] is not None and not slot["grounded"]:
                ungrounded_count += 1
        if flags:
            flagged_count += 1

        # Manifest stage-tracking (only for DOIs already in the manifest).
        if manifest_key:
            mark_manifest_pdf_extract(manifest, manifest_key)

        print(
            f"PDF     {doi} [{pdf_source}/{text_source}] "
            f"identity={identity_status}"
        )

    # --- Human-readable summary ---
    print()
    print("=== PDF extraction summary ===")
    print(f"Total DOIs processed : {total}")
    print(f"PDFs found           : {pdfs_found}")
    print(f"Grounded fields      : {fields_extracted}")
    print(f"Ungrounded fields    : {ungrounded_count}")
    print(f"DOIs with any flag   : {flagged_count}")
    print(
        "Identity status      : "
        f"ok={identity_counts['ok']} "
        f"mismatch={identity_counts['mismatch']} "
        f"unverifiable={identity_counts['unverifiable']}"
    )
    if mismatch_dois:
        print()
        print("!! PDF IDENTITY MISMATCH — review these DOIs before trusting "
              "their fields:")
        for doi in mismatch_dois:
            print(f"   - {doi}")


if __name__ == "__main__":
    main()
