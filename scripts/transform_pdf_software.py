#!/usr/bin/env python3
"""PDF software_tools -> Software nodes + USES_SOFTWARE edges.

Transcribes docs/pdf_transform_logic.md Sec 9 (RULED). Nothing here is
re-derived: every rule below cites the section it comes from. Where Sec 9
records a gap (trailing-ref strip) or a pending ruling (CERES, databases),
this script routes to REVIEW/HOLD rather than inventing a rule.

Reads:  data/raw/pdf_extraction/pdf_extraction_378papers.jsonl
        (gitignored, local-only -- like 02f, this stage cannot be
        reproduced from a clean clone)
Writes (--dry-run, the default): data/processed/review/software_review.md
Writes (--apply, NOT enabled):   would append entities/relationships.

--apply is deliberately unimplemented. Sec 9.4 requires the transform to
re-query bio.tools at build time and write a re-runnable registry artifact;
that is an external API call, which CLAUDE.md forbids without explicit
instruction. Minting cannot be honest until that ruling lands.

Envelope follows 02c_extract_rawfiles.py: the six provenance fields
(source_type, confidence, extracted_at, evidence_note, source_id,
schema_version) are set once in _provenance().
"""

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

INPUT = Path("data/raw/pdf_extraction/pdf_extraction_378papers.jsonl")
REVIEW_OUT = Path("data/processed/review/software_review.md")

SCHEMA_VERSION = "v1.0"
EVIDENCE_NODE = ("Software extracted from PDF via Docling + LangExtract (model "
                 "llama3.1:8b), grounded verbatim in article text; identity "
                 "unverified. Canonicalized per docs/pdf_transform_logic.md Sec 9. "
                 "Representative source_id retained; every contributing paper "
                 "carries its own source_id on its USES_SOFTWARE edge. "
                 "biotools_status 'proposed' means an exact-name bio.tools hit "
                 "exists but NO human has confirmed it -- biotools_id is null "
                 "until docs/software_registry_review.md returns.")
EVIDENCE_EDGE = ("Software mention extracted from this paper's PDF via Docling + "
                 "LangExtract (model llama3.1:8b), grounded verbatim in article "
                 "text. Version (when present) is a per-usage edge fact, not "
                 "identity (Sec 9.1).")

ENTITIES_OUT = Path("data/processed/entities/pdf_entities.jsonl")
RELS_OUT = Path("data/processed/relationships/pdf_relationships.jsonl")
PUBS = Path("data/processed/entities/publications.jsonl")
SOFTWARE_EXISTING = Path("data/processed/entities/software.jsonl")
SOURCE_TYPE = "llm_extraction"
CONFIDENCE = "medium"

# Sec 2.-1 extraction-failure guard. Field list per 02d's output shape.
EXTRACTION_FIELDS = ["instrument", "ionization_method", "sample_type",
                     "facility", "software_tools", "dataset_accession"]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def failure_reason(rec):
    """Sec 2.-1. Failed extraction is MISSING data, not absent data."""
    if rec.get("pdf_source") == "none":
        return "no_pdf"
    if "No PDF could be acquired" in (rec.get("evidence_note") or ""):
        return "evidence_note_flag"
    all_null = all((rec.get(f) or {}).get("value") is None
                   for f in EXTRACTION_FIELDS)
    if all_null and len(rec.get("all_field_extractions", [])) == 0:
        return "ran_but_empty"
    return None


# ===================== CORPUS RULES (Sec 9) =====================
# Sec 9.8 confirm bucket -- Diya's calls, recorded 2026-07-16.
# FUZZY PROPOSES, HUMAN DISPOSES: these are applied only because a human
# accepted them. CERES stays PENDING (David) and routes to HOLD.
# Keys are the POST-normalization forms -- a pre-strip spelling is unreachable
# (the assertion below enforces this). "petrorg data processing software" and
# "predator data station" were both dead: descriptor-strip reduces them to
# "petrorg" / "predator" before the lookup runs.
CONFIRM_ACCEPTED = {
    "xcaliber": "Xcalibur",
    "petrorg": "PetroOrg",   # Sec 9.8 ACCEPTED: "Petrorg data processing software"
                             # (one-o spelling; "petroorg" is the separate CANONICAL key)
}
CONFIRM_PENDING = {"ceres processing": "PENDING -- David"}

# Sec 9.6 Bruker canonicalization: three strings collapse to one node.
# SmartFormula and Compound Discoverer are their own nodes.
CANONICAL = {
    # Sec 9.6's three Bruker strings all arrive here as "data analysis":
    # vendor-strip (step 4) removes "Bruker"/"Bruker Daltonics" BEFORE the
    # lookup. The pre-strip spellings were keys once; they were unreachable by
    # construction and are gone -- see _assert_keys_reachable() below.
    "data analysis": "DataAnalysis",
    "dataanalysis": "DataAnalysis",
    "smartformula": "SmartFormula",
    "compound discoverer": "Compound Discoverer",
    "petroorg": "PetroOrg",
    "predator": "Predator",
    "enviroorg": "EnviroOrg",
    "xcalibur": "Xcalibur",
    "matlab": "MATLAB",
    "prosight lite": "ProSight Lite",
    "prosightpc": "ProSightPC",
    "prosight pc": "ProSightPC",
    "prosight pd": "ProSight PD",
    "maxquant": "MaxQuant",
    "proteowizard": "ProteoWizard",
    "msconvert": "MSConvert",
    "unidec": "UniDec",
    "clipsms": "ClipsMS",
    "pyc2mc": "PyC2MC",
    "msalign": "MSAlign",
    "fiji": "Fiji",
    "igv": "IGV",
    "corems": "CoreMS",
    "tdportal": "TDPortal",
    "tdvalidator": "TDValidator",
    "fragariyo": "Fragariyo",
    "mascot": "Mascot",
    "metamorpheus": "MetaMorpheus",
    "proteoform suite": "Proteoform Suite",
    "graphpad prism": "GraphPad Prism",
    "ggplot2": "ggplot2",
    "qiime2": "QIIME2",
    "dada2": "DADA2",
    "vegan": "vegan",
    "python": "Python",
    "r": "R",
    "originpro": "OriginPro",
    "origin": "OriginPro",
    "magicplot": "Magicplot",
    # Mnova RULED 2026-07-16 (Diya): ONE node. Mnova is Mestrelab's NMR
    # package -- "Mnova NMR software" is a paper spelling out what it is, not
    # naming a variant. "mnova nmr software" removed: unreachable (descriptor-
    # strip removes "software" before the lookup ever sees it).
    "mnova": "Mnova",
    "mnova nmr": "Mnova",
    "adf": "ADF",
    # ProteinProspector is ALSO a proposed bio.tools id awaiting Veronika
    # (docs/software_registry_review.md). Minting the node is fine; the node
    # carries biotools_status: proposed until she returns it. 16 tools are in
    # both states -- see Sec 9.3.
    "proteinprospector": "ProteinProspector",
    "biotools": "BioTools",
    # --- RULED MINT 2026-07-16 (Diya): real named tools, same basis as the 11.
    # Previously in this map with no ruling behind them; now decided.
    "drEEM toolbox".lower(): "drEEM",
    "dreem": "drEEM",
    # --- The 11 REVIEW tools, RULED MINT by Diya 2026-07-16. Sec 9.7 says
    # mint tools with a clear proper name; Sec 2.1 biased them to REVIEW.
    "microsoft excel": "Microsoft Excel",
    "excel": "Microsoft Excel",
    "jmp": "JMP",
    "jmp pro": "JMP",
    "spss": "SPSS",
    "cutadapt": "Cutadapt",
    "chromcalc": "ChromCALC",
    "empower3": "EMPOWER3",
    "arcgis": "ArcGIS",
    "factoextra": "factoextra",
    # Athena = the XAS/XANES tool (Demeter/IFEFFIT, Ravel & Newville 2005).
    # NOT the bio.tools "ATHENA" (spatial-omics) -- see Sec 9.2's ATHENA note.
    "athena": "Athena",
    # MIDAS = Modular ICR Data Acquisition System, NHMFL, Predator's
    # PREDECESSOR -- so "MIDAS Predator" is TWO tools (split below).
    "midas": "MIDAS",
    # Composer: Sierra Analytics; Composer64 is the same tool.
    "composer": "Composer",
    "composer64": "Composer",
}

# REMOVED 2026-07-16 (Diya) -- dead entries: no corpus referent AND no ruling.
# Do not re-add without evidence.
#   "mash suite" -> MASH Suite : its only corpus appearance is descriptive prose
#       INSIDE the ReSpect parenthetical ("...as implemented, for example in the
#       MASH Suite"), naming where an algorithm lives -- never a tool the paper ran.
#   "coremos"    -> CoreMS     : a typo. ("corems" is the real key and has a referent.)
#   "imagej"     -> ImageJ     : Ruling 1 routes "Fiji ImageJ ..." to Fiji, so ImageJ
#       has no independent referent.

# ---- RULING 1 (Diya 2026-07-16): suite/component and host/toolbox tokens.
# A token naming a suite and its component, or a host and its toolbox, is ONE
# tool reference -- mint the COMPONENT, because that is what the paper ran.
# The suite is NOT minted as a peer node: the paper did not use them as peers.
# The verbatim raw string is kept as an alias on the node (SUITE_ALIAS below).
#
# Deliberately NOT a space-split rule: splitting these would shatter them into
# peer nodes and assert a paper used both, which is false. Token-level
# canonical mapping only.
#
# CONTRAST -- "MIDAS Predator Analysis" is NOT this shape. MIDAS and Predator
# are COORDINATE tools (predecessor and successor), so they are two references
# and split into two rows via ADJACENT_PAIRS. Suite/component = one; coordinate
# tools = two.
# NOT covered: "ProSight PD ™ (Thermo Fisher Scientific PD version 2.1,
# ProSightPC version 4.0)" -- stays REVIEW under the n=1 ruling; no rule built.
SUITE_COMPONENT = {
    "proteowizard msconvert": "MSConvert",   # msConvert ships inside ProteoWizard
    "fiji imagej using the plot pro fi les function": "Fiji",  # Fiji = the
    #     ImageJ distribution actually run; trailing function phrase stripped
    "dreem toolbox for matlab": "drEEM",
    "dreem toolbox in matlab": "drEEM",
    "matlab with the dreem toolbox": "drEEM",
}

# ---- RULING 2 (Diya 2026-07-16): MSAlign and MS-Align+ are DIFFERENT tools.
# "MSAlign +" in 10.1002/pmic.201800361 sits in a bundle of three top-down
# proteomics tools (Proteoform Suite; MetaMorpheus; MSAlign +) and reads as
# MS-Align+, the top-down search engine. bio.tools `msalign` is an LC-MS
# ALIGNMENT tool -- a different thing. The spacing matches the Docling artifact
# seen elsewhere in this corpus ("Plot Pro fi les", "Thermo Scienti fi c").
# UNRESOLVED from the repo: data/processed/pdf_text/ does not exist, so the
# source span [59560, 59569] cannot be read. Veronika has the PDFs.
# MS-Align+ was NEVER queried under this name -> biotools_id null,
# biotools_status not_attempted (NOT proposed -- no query was made).
MS_ALIGN_PLUS = {"msalign +": "MS-Align+"}

NEVER_QUERIED = {"MS-Align+"}   # status not_attempted, never proposed

# ---- F3 (Diya 2026-07-16): full name -> abbreviation.
# An EXPLICIT MAP, not a guessed rule. Every entry is a string measured on disk.
# Sec 9.7 already rules that BLAST "mints normally" -- it was never in the
# canonical map, so a recorded ruling was silently dead on disk.
FULL_NAME = {
    "integrative genomics viewer": "IGV",
    "basic local alignment search tool": "BLAST",       # Sec 9.7 ruling
    "basic local alignment search tool server": "BLAST",
    "blast": "BLAST",
    "empower 3": "EMPOWER3",                            # spacing variant
    "empower 3 chromatography data": "EMPOWER3",
    "comprehensive localization of internal protein sequences": "ClipsMS",
}

# ---- F3, derived half: when a parenthetical holds a name we ALREADY
# canonicalize, that name IS the tool (Diya 2026-07-16). The paper hands us the
# mapping -- "Comprehensive Localization of Internal Protein Sequences
# (ClipsMS)", "Custom software (PetroOrg)", "modular ICR data station
# (Predator)". Whole paren content only, never split on its commas: that is what
# keeps "ProSight PD (Thermo Fisher Scientific PD version 2.1, ProSightPC
# version 4.0)" in REVIEW as ruled, and "UniDec (Oxford University, UK)" too.
PAREN_GROUP = re.compile(r"\(([^()]*)\)")


def _paren_abbrev(tok):
    """Return the canonical name if a parenthetical is exactly a known tool."""
    for inner in PAREN_GROUP.findall(tok):
        # F2: symbols are stripped upstream now (strip_symbols), so this handler
        # no longer does its own -- one place, not two.
        cleaned = norm(inner).strip(" ,.;")
        if cleaned in CANONICAL:
            return CANONICAL[cleaned]
    return None


# Diya 2026-07-16: MIDAS is Predator's predecessor, NOT its parent -- the
# adjacency in "MIDAS Predator" is two tools listed together, not one name.
# Sec 9.6's separator list cannot see this (no delimiter), so it is a recorded
# corpus rule, applied after descriptor-strip.
ADJACENT_PAIRS = {"midas predator": ["MIDAS", "Predator"]}

# Vendors that appear only in these rulings' strings.
VENDOR_EXTRA = {"Composer": "Sierra Analytics"}

# Sec 9.4 -- the ONE verified RRID. Sec 9.2: never guessed.
# R / MATLAB / GraphPad Prism stay not_attempted until the Sec 9.9 SciCrunch
# hand-verification returns. An RRID is never LLM-generated.
RRID_VERIFIED = {"Xcalibur": "SCR_014593"}

# Sec 9.4 durable fix: registry data comes from this re-runnable artifact
# (scripts/query_biotools.py), never from Sec 9.4's seed table.
REGISTRY = Path("data/processed/software_registry.jsonl")


def load_registry():
    if not REGISTRY.exists():
        return {}
    out = {}
    for line in REGISTRY.open(encoding="utf-8"):
        line = line.strip()
        if line:
            r = json.loads(line)
            if r.get("_meta"):
                continue
            out[norm(r["name"])] = r
    return out

# Sec 9.7 REJECT, reasons verbatim from the doc.
REJECT_EXACT = {
    "n/a": "N/A",
    # F4 2026-07-16: Sec 9.7's ruled rejects were in the doc and not in the code
    # -- same class as BLAST. Reasons quoted from Sec 9.7.
    "known databases 35": "known databases 35, 36",
    "36": "known databases 35, 36",
    "ai": "AI and elemental ratios...",
    "elemental ratios of molecular formulas (h/c and o/c)": "AI and elemental ratios...",
    "nmr": "method-description phrase",
    "high-resolution ms analyses": "method-description phrase",
    "fouriertransform": "bare fouriertransform",
    "known databases 35, 36": "known databases 35, 36",
    "methods of soil analysis. part 3": "book, not software",
}
REJECT_SUBSTR = [
    ("peak lists (uncalibrated", "Peak lists (uncalibrated...)"),
    ("ai and elemental ratios", "AI and elemental ratios..."),
]

# Sec 9.7 -- generic-but-real; Publication.software_mentioned_raw, not a node.
PUB_PROPERTY = {
    "in-house software", "custom in-house software", "custom software",
    "homemade python scripts jupyter notebooks", "multiple analytical tools",
}

# Sec 9.7 -- HOLD for David: are reference databases Software nodes?
DB_HOLD = {"silva", "rdp", "colmar"}

# docs/method_field_handoff.md -- the 11 algorithms, routed OUT of software.
ALGORITHMS = {
    "xtract", "xtract algorithm", "thrash", "respect", "swift", "snap",
    "maxent", "maximumentropydeconvolution", "crawler", "crawler algorithm",
    "nipals", "k-means clustering", "molecular formula calculator",
    "young algorithm",
    # F6 2026-07-16: ruled in method_field_handoff.md, never checked by the code.
    "young", "crawler algorithm inside prosightpc", "respect algorithm",
    "stored waveform inverse fourier transform",
    "nonlinear iterative partial least-squares",
    "one-way analysis of variance", "tukey", "tukey's honest significant difference",
    "anova", "t-tests",
}

# F6: instruments that surfaced in software_tools. KI-3: 3 of these 4 have no
# Instrument node and that field is COMPLETE -- the handoff is the inbox.
# "belongs to" per docs/method_field_handoff.md.
INSTRUMENT_ROUTE = {
    "nanodrop 2000c spectrophotometer": "instrument field",
    "tri-carb 2800tr scintillation counter": "instrument field (KI-3: no node on disk)",
    "stepone from applied biosystems": "instrument field (KI-3: no node on disk)",
    "jed-2300 series standard software": "instrument field (KI-3: no node on disk)",
    "jed-2300 series standard": "instrument field (KI-3: no node on disk)",
}

# R2 RESOLVED (Diya 2026-07-16): AFM and GPC route out to the method field.
# method_field_handoff.md names both with DOIs; Sec 9.7's competing reject clause
# is generic ("method-description phrases"). A NAMED ROUTE-OUT BEATS A GENERIC
# REJECT -- and both are methods. Keys carry the handoff's form AND the verbatim
# corpus spelling, which is longer; the raw string is kept verbatim on the record.
# Precedence is enforced structurally: the ROUTE_OUT check runs BEFORE the REJECT
# clauses in classify().
# docs/method_field_handoff.md -- method misroutes.
METHOD_MISROUTE = {
    "sds-page", "kendrick mass defect analysis", "gpc analysis",
    "atomic force microscopy imaging", "gas chromatography/mass spectrometry",
    # R2 (Diya 2026-07-16): AFM and GPC route out to the method field. The
    # handoff names both WITH DOIs; Sec 9.7's competing clause is generic
    # ("method-description phrases"). A NAMED ROUTE-OUT BEATS A GENERIC REJECT,
    # and both are methods. Handoff form is above; the verbatim corpus spelling
    # is longer, so it is keyed explicitly rather than matched by prefix:
    "gpc analysis (with polystyrene standards)",
    "gpc analysis with polystyrene standards",
    "gpc analysis with polystyrene standards for calibration",
    "atomic force microscopy molecular imaging",
    # F6 post-strip forms (the dual-form check also covers these):
    "kendrick mass defect",
    "anova", "tukey", "t-tests", "lc-icp-ms method",
    "high-resolution mass spectrometry detection",
    "high-throughput 16s rrna gene sequencing",
    "cfx connect ™ real-time pcr detection system",
    "internal release june 2014",
}

VENDORS = ["Bruker Daltonics", "Bruker", "Thermo Fisher Scientific",
           "Thermo Scientific", "Thermo Scienti fi c", "Thermo",
           "Protein Metrics", "Agilent", "Waters", "Sciex"]

# ===================== Sec 9.5 NORMALIZATION ORDER =====================

# Step 1: ref-strip. Runs of comma-separated bare integers at a
# string/delimiter boundary, followed by a letter-initial token.
# Boundary-anchored so "8900 QQQ" (mid-string) and "R i386 2.15.2" survive.
REF_RUN = re.compile(r"(^|[;,])\s*\d+(?:\s*,\s*\d+)*\s+(?=[A-Za-z])")

# Sec 9.5 -- trailing refs are an UNBUILT gap. Detect and route to REVIEW;
# do NOT strip. A trailing bare integer is ambiguous with a version
# ("ADF 2017") -- disambiguating needs a ruling that was never made.
TRAILING_REF = re.compile(r"[A-Za-z)]\s+\d{1,3}\s*$")

# F3 (2026-07-16): the N-prefixed alternative is FIRST so it wins. Sec 9.5 gives
# N-18.3 / N8.6 / N13.3 / N-15.0 as PetroOrg's build format -- the WHOLE string is
# the version, so the captured value is "N-18.3", not "18.3". Without this the
# regex took only the numeric tail and left "PetroOrg N-", which matched nothing.
VERSION = re.compile(
    r"(?:\b(?:version|ver|v)\.?\s*)?"
    r"(\bN-?\d+(?:\.\d+)+\b"
    r"|\d+(?:\.\d+)+(?:[-/][\w.]+)*|\b(?:19|20)\d{2}\b)",
    re.I)

# F5: a segment that is ONLY a version ("version 13.1.0") is not a tool -- the
# comma split orphaned it and it died as empty-after-normalization, taking JMP's
# version with it. Re-attach it to the token it belongs to.
BARE_VERSION = re.compile(r"^\s*(?:version|ver|v)\.?\s*[\d.]+\s*$", re.I)


def ref_strip(s):
    prev = None
    while prev != s:
        prev = s
        s = REF_RUN.sub(r"\1 ", s)
    return re.sub(r"\s+", " ", s).strip().strip(",;").strip()


def _paren_depth_scan(s):
    """F1 (2026-07-16): Sec 9.5 steps 2+3 together.

    The spec says split on ';' / ',' / ' and ' / ' or ' **at paren-depth 0**.
    Masking only protected ',' and ';'; the and/or split was a plain regex with
    no depth awareness, so it fired INSIDE parentheses and severed tokens
    mid-parenthetical (it split `ReSpect (... Thermo Scienti fi c AND in an
    open resource ... MASH Suite)` into two garbage fragments and lost MASH
    Suite entirely). A depth-aware scanner enforces the written spec
    structurally, so masking is no longer needed -- depth IS the protection.
    """
    WORDS = (" and ", " or ")
    out, buf, depth, i = [], "", 0, 0
    while i < len(s):
        ch = s[i]
        if ch == "(":
            depth += 1
            buf += ch
            i += 1
            continue
        if ch == ")":
            depth = max(0, depth - 1)
            buf += ch
            i += 1
            continue
        if depth == 0:
            if ch in ";,":
                out.append(buf)
                buf = ""
                i += 1
                continue
            hit = next((w for w in WORDS if s[i:i + len(w)].lower() == w), None)
            if hit:
                out.append(buf)
                buf = ""
                i += len(hit)
                continue
        buf += ch
        i += 1
    out.append(buf)
    parts = [x.strip() for x in out if x.strip()]
    # F5 (2026-07-16): a comma can orphan a bare version ("EnviroOrg; JMP
    # software, version 13.1.0"), which then died as empty-after-normalization
    # and took JMP's version with it. Carry it ALONGSIDE the preceding token as
    # (token, orphan_version) -- never merged INTO the token string. Merging it
    # in would push the descriptor past step 4.5 and re-create the ordering
    # residue: "JMP software version 13.1.0" -> "JMP software" -> matches
    # nothing, costing the node to save the version. This keeps both.
    merged = []
    for x in parts:
        if merged and BARE_VERSION.match(x):
            merged[-1] = (merged[-1][0], re.sub(r"^\s*(?:version|ver|v)\.?\s*", "", x,
                                                flags=re.I).strip())
        else:
            merged.append((x, None))
    return merged


def split_bundle(s):
    """Steps 2-3. Sec 9.6: '/' is NOT a separator; Sec 9.6a: ' ' is not either."""
    return _paren_depth_scan(s)


def extract_vendor(tok):
    """Step 4: vendor-strip -> vendor property."""
    for v in VENDORS:
        pat = re.compile(r"\(?\b" + re.escape(v) + r"\b,?\s*\)?", re.I)
        if pat.search(tok):
            tok = pat.sub(" ", tok)
            canon = "Bruker" if "bruker" in v.lower() else (
                "Thermo" if "thermo" in v.lower() else v)
            return _tidy(re.sub(r"\s+", " ", tok)), canon
    return tok, None


# Step 4.5: descriptor-strip (Sec 9.5). Restored 2026-07-16 -- was in the
# original spec and lost in the migration into this doc; not a new ruling.
# Short, explicit list only. Iterative: "Predator software package" -> Predator.
DESCRIPTORS = ["software", "analysis", "package", "data station", "algorithm",
               "data processing"]   # F1 2026-07-16 (Diya)

# Never strip a token that is part of a tool's ACTUAL name. Checked BEFORE
# each strip, so "Data Analysis" keeps its "Analysis" while "Predator
# Analysis" loses its own.
DESCRIPTOR_PROTECTED = {
    "compound discoverer", "proteoform suite", "prosight lite", "data analysis",
} | PUB_PROPERTY   # Sec 9.7's strings are exact; stripping "software" off
#                    "in-house software" would silently drop them from
#                    software_mentioned_raw.


# F2 (Diya 2026-07-16): strip trademark/copyright marks at TOP LEVEL.
# NOTE: Sec 9.5 does NOT specify this -- it is a NEW rule, not an implementation
# of an existing one. It exists because the behaviour was inconsistent: the
# parenthetical handler stripped these marks, so "Custom software (PetroOrg (c))"
# resolved while a bare "PetroOrg (c)" did not. Now stripped in ONE place, before
# vendor/descriptor/version, and the parenthetical handler no longer does its own.
SYMBOLS = re.compile(r"\u00a9|\u00ae|\u2122|\(\s*[cCrR]\s*\)|(?<=[A-Za-z0-9])\s+TM\b")


def strip_symbols(s):
    return re.sub(r"\s+", " ", SYMBOLS.sub(" ", s)).strip()


EMPTY_PARENS = re.compile(r"\(\s*\)")


def _drop_empty_parens(s):
    """F2 (2026-07-16): version-extract lifts the version out of a parenthetical
    and leaves the shell behind -- 'Integrative Genomics Viewer ( )',
    'DataAnalysis ( )', 'JMP software ( )'. The remnant is why these missed the
    canonical map."""
    return EMPTY_PARENS.sub("", s)


def _tidy(s):
    """Trim separators, and unwrap parens ONLY when they wrap the whole token.
    A blind strip("()") truncates "modular ICR data station (Predator)"."""
    s = s.strip().strip(" ,;").strip()
    while s.startswith("(") and s.endswith(")") and s.count("(") == s.count(")"):
        s = s[1:-1].strip()
    if s.count("(") == s.count(")"):
        return s
    return s.rstrip(" ,;")

_DESC_RE = [re.compile(r"\s*\b" + re.escape(d) + r"\b\s*$", re.I)
            for d in DESCRIPTORS]


def strip_descriptors(tok):
    """Step 4.5. Trailing descriptors only; protected names are never cut."""
    prev = None
    while prev != tok:
        prev = tok
        if norm(tok) in DESCRIPTOR_PROTECTED:
            return tok
        for pat in _DESC_RE:
            cut = _tidy(pat.sub("", tok))
            if cut and cut != tok:
                tok = cut
                break
    return tok


def extract_version(tok):
    """Step 5: version-extract -> edge property, never identity (Sec 9.1)."""
    m = VERSION.search(tok)
    if not m:
        return tok, None
    ver = m.group(1)
    tok = (tok[:m.start()] + " " + tok[m.end():])
    tok = re.sub(r"\b(?:version|ver|v)\.?\s*$", "", tok.strip(), flags=re.I)
    return _tidy(_drop_empty_parens(re.sub(r"\s+", " ", tok))), ver


def norm(s):
    return re.sub(r"\s+", " ", s or "").strip().lower()


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def classify(tok, raw_bundle, pre_strip=None):
    """Sec 9.7 routing. Bias to REVIEW: minting garbage costs more than a
    human confirming a real tool (Sec 2.1 implementation note)."""
    n = norm(tok)
    p = norm(pre_strip) if pre_strip else n
    if not n:
        return "REJECT", "empty after normalization", None
    if n in CONFIRM_PENDING:
        return "HOLD", "Sec 9.8 confirm bucket: PENDING -- David", None
    if n in CONFIRM_ACCEPTED:
        return "MINT", "Sec 9.8 confirm bucket: ACCEPTED", CONFIRM_ACCEPTED[n]
    # F6: checked against BOTH the pre-descriptor-strip and post-strip forms.
    # Neither alone suffices: "Young Algorithm" is only recognisable BEFORE the
    # strip ("Young" alone is a surname, not a safe key), while bare "ReSpect"
    # is only recognisable AFTER it. Checking both keeps each key at its most
    # specific spelling instead of guessing a shorter one.
    for form in (p, n):
        if form in ALGORITHMS:
            return "ROUTE_OUT", "algorithm -> method_field_handoff.md", None
        if form in METHOD_MISROUTE:
            return "ROUTE_OUT", "method misroute -> method_field_handoff.md", None
        if form in INSTRUMENT_ROUTE:
            return "ROUTE_OUT", (f"instrument -> method_field_handoff.md "
                                 f"(belongs to: {INSTRUMENT_ROUTE[form]})"), None
    if n in REJECT_EXACT:
        return "REJECT", REJECT_EXACT[n], None
    for sub, why in REJECT_SUBSTR:
        if sub in n:
            return "REJECT", why, None
    if "http" in n or "www." in n:
        return "REJECT", "URL", None
    if n in PUB_PROPERTY:
        return "PUB_PROPERTY", "generic-but-real; software_mentioned_raw", None
    if n in DB_HOLD:
        return "HOLD", "reference database -- HOLD for David (Sec 9.7)", None
    if TRAILING_REF.search(raw_bundle) and TRAILING_REF.search(tok):
        return "REVIEW", "trailing-ref gap UNBUILT (Sec 9.5) -- needs ruling", None
    if n in FULL_NAME:
        return "MINT", "F3: full name -> abbreviation (explicit map)", FULL_NAME[n]
    pa = _paren_abbrev(tok)
    if pa:
        return "MINT", "F3: parenthetical names a known tool", pa
    if n in SUITE_COMPONENT:
        # Ruling 1: suite/component -> mint the component; raw string = alias.
        return "MINT", "Ruling 1: suite/component -> component", SUITE_COMPONENT[n]
    if n in MS_ALIGN_PLUS:
        # Ruling 2: MS-Align+ is not MSAlign. Never queried under this name.
        return "MINT", "Ruling 2: MS-Align+ (distinct from MSAlign)", MS_ALIGN_PLUS[n]
    if n in CANONICAL:
        return "MINT", "canonical map", CANONICAL[n]
    return "REVIEW", "not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW)", None


def transform(rec):
    """One record -> list of per-token dicts."""
    raw = (rec.get("software_tools") or {}).get("value")
    if not raw:
        return []
    stripped = ref_strip(raw)
    rows = []
    for tok, orphan_ver in split_bundle(stripped):
        t = strip_symbols(tok)            # F2, before everything else
        t, vendor = extract_vendor(t)
        pre = t                           # F6: pre-descriptor-strip form
        t = strip_descriptors(t)          # step 4.5
        t, version = extract_version(t)
        # R1 (Diya 2026-07-16): SECOND descriptor pass. Step 5 can EXPOSE a
        # descriptor that was not trailing when step 4.5 first ran --
        # "JMP software (v. 7.0.1)" -> step 5 lifts the version -> "JMP
        # software" -> the descriptor is trailing only now. Deferred once as 4
        # cosmetic tokens; F5 showed it costs a node (JMP), so it is a real gap.
        # Protected names are re-checked on this pass too (strip_descriptors
        # returns early on them), so "Data Analysis" is safe.
        t = strip_descriptors(t)
        version = version or orphan_ver          # F5
        # Recorded corpus rule: split adjacent tool names (MIDAS Predator).
        for canon_name in ADJACENT_PAIRS.get(norm(t), [None]):
            if canon_name is None:
                route, reason, canon = classify(t, raw, pre_strip=pre)
                cleaned = t
            else:
                route, reason, canon = "MINT", "adjacent-pair split (Diya)", canon_name
                cleaned = canon_name
            rows.append({
                "doi": rec["doi"], "raw": raw, "token": tok, "cleaned": cleaned,
                "canonical_name": canon,
                "vendor": vendor or VENDOR_EXTRA.get(canon or ""),
                "version": version, "route": route, "reason": reason,
            })
    return rows


def _provenance(source_id, evidence):
    """Six provenance fields, 02c pattern."""
    return {
        "source_type": SOURCE_TYPE,
        "confidence": CONFIDENCE,
        "extracted_at": now_iso(),
        "evidence_note": evidence,
        "source_id": source_id,
        "schema_version": SCHEMA_VERSION,
    }


def build_node(canonical_name, vendor, doi, registry=None, aliases=None):
    """Sec 9.1: software:{canonical_name}, unconditional. Version is NOT
    identity. rrid/biotools_id are properties. Sec 9.3: four-way status.

    Property schema MATCHES the Software node already on disk (software:xcalibur,
    02c/fisher_py): canonical_name (NOT name), psi_ms_id, category, aliases.
    A second shape would split the Software field in two.
    """
    rrid = RRID_VERIFIED.get(canonical_name)
    reg = (registry or {}).get(norm(canonical_name))
    props = {
        "canonical_name": canonical_name,
        "psi_ms_id": None,
        "rrid": rrid,
        "rrid_status": "has_id" if rrid else "not_attempted",
        # Ruling 2 / Sec 9.3: a PROPOSED id must NOT reach the graph.
        "biotools_id": (reg or {}).get("biotools_id") if reg else None,
        "biotools_status": ("not_attempted" if canonical_name in NEVER_QUERIED
                            else (reg["biotools_status"] if reg else "not_attempted")),
        "vendor": vendor,
        # category: NULL. 02c derives "acquisition" from RAW-file context; there
        # is no source for it in a PDF mention. Inventing values would be
        # fabricating scientific metadata. Ruled null 2026-07-16 (Diya).
        "category": None,
        # Ruling 1: the verbatim raw string is kept as an alias.
        "aliases": sorted(set(aliases or [])),
    }
    rec = {"identifier": f"software:{slug(canonical_name)}",
           "entity_type": "Software", "properties": props}
    rec.update(_provenance(f"doi:{doi}", EVIDENCE_NODE))
    return rec


def build_edge(doi, software_id, version):
    """USES_SOFTWARE: Publication -> Software. Version is an EDGE fact (Sec 9.1),
    never identity. subject_id is lowercased to match publications.jsonl."""
    rec = {
        "relationship_type": "USES_SOFTWARE",
        "subject_id": f"doi:{doi.lower()}",
        "subject_type": "Publication",
        "object_id": software_id,
        "object_type": "Software",
        "properties": ({"version": version} if version else {}),
    }
    rec.update(_provenance(f"doi:{doi}", EVIDENCE_EDGE))
    return rec


def _read_jsonl(p):
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


def _write_swap(path, records):
    """Write-new, then swap. NEVER mutate in place."""
    tmp = path.with_suffix(path.suffix + ".new")
    with tmp.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    tmp.replace(path)


def apply_mint():
    """Mint the software field. Authorized by Diya 2026-07-16.

    Destinations follow the EXISTING convention (by source/stage, not by type):
    PDF-derived nodes -> pdf_entities.jsonl (where Institution and the 462 PDF
    Instruments live); edges -> pdf_relationships.jsonl.

    software:xcalibur is SKIPPED: it already exists in software.jsonl from the
    02c/fisher_py migration. Emitting it here would create the repo's first
    CROSS-FILE identifier collision, which 03 does not catch -- it dedups within
    a file only, so the duplicate would pass straight through to 05's uniqueness
    constraint. Its PDF tokens still become edges pointing at the existing node.
    """
    registry = load_registry()
    existing_nodes = _read_jsonl(ENTITIES_OUT)
    existing_rels = _read_jsonl(RELS_OUT)

    # (k) idempotency: refuse rather than double-apply.
    if any(r.get("entity_type") == "Software" for r in existing_nodes):
        raise SystemExit(
            f"ALREADY APPLIED: {ENTITIES_OUT} already contains Software nodes. "
            "Refusing to double-apply. Restore from backup to re-run.")
    if any(r.get("relationship_type") == "USES_SOFTWARE" for r in existing_rels):
        raise SystemExit(
            f"ALREADY APPLIED: {RELS_OUT} already contains USES_SOFTWARE edges. "
            "Refusing to double-apply.")

    on_disk = {r["identifier"] for r in _read_jsonl(SOFTWARE_EXISTING)}

    recs = [r for r in _read_jsonl(INPUT) if not failure_reason(r)]
    aliases, vendors, first_doi, edges, pubprops = {}, {}, {}, [], {}
    for r in recs:
        for row in transform(r):
            if row["route"] == "MINT":
                cn = row["canonical_name"]
                aliases.setdefault(cn, set()).add(row["token"])
                if row["vendor"]:
                    vendors[cn] = row["vendor"]
                first_doi.setdefault(cn, r["doi"])
                edges.append(build_edge(r["doi"], f"software:{slug(cn)}",
                                        row["version"]))
            elif row["route"] == "PUB_PROPERTY":
                pubprops.setdefault(r["doi"], []).append(row["cleaned"])

    nodes = []
    skipped = []
    for cn in sorted(aliases):
        node = build_node(cn, vendors.get(cn), first_doi[cn], registry,
                          aliases[cn])
        if node["identifier"] in on_disk:
            skipped.append(node["identifier"])
            continue
        nodes.append(node)

    # Publication.software_mentioned_raw -- additive, never overwrite.
    pubs = _read_jsonl(PUBS)
    touched = 0
    for p in pubs:
        doi = (p.get("properties") or {}).get("doi")
        if doi and doi in pubprops:
            p["properties"]["software_mentioned_raw"] = sorted(set(pubprops[doi]))
            touched += 1

    _write_swap(ENTITIES_OUT, existing_nodes + nodes)
    _write_swap(RELS_OUT, existing_rels + edges)
    _write_swap(PUBS, pubs)

    print(f"MINTED  {len(nodes)} Software nodes -> {ENTITIES_OUT}")
    print(f"SKIPPED {len(skipped)} already on disk: {skipped}")
    print(f"EDGES   {len(edges)} USES_SOFTWARE -> {RELS_OUT}")
    print(f"PUBS    software_mentioned_raw on {touched} publications")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="NOT IMPLEMENTED -- see module docstring")
    args = ap.parse_args()
    if args.apply:
        return apply_mint()

    if not INPUT.exists():
        raise SystemExit(f"ERROR input absent: {INPUT}")

    withval, negatives, failed = [], 0, []
    for line in INPUT.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        why = failure_reason(rec)
        if why:
            failed.append((rec.get("doi"), why))
            print(f"EXTRACTION_FAILED {rec.get('doi')} ({why})")
            continue
        if (rec.get("software_tools") or {}).get("value"):
            withval.append(rec)
        else:
            negatives += 1

    rows = [r for rec in withval for r in transform(rec)]
    routes = Counter(r["route"] for r in rows)

    L = ["# Software field -- DRY RUN (nothing minted)\n",
         f"\nGenerated {now_iso()} by `scripts/transform_pdf_software.py`.\n",
         f"Input: `{INPUT}` (gitignored, local-only).\n",
         "\n## Three-way extraction accounting (Sec 2.-1)\n",
         f"\n- **{len(withval)}** with a software value\n",
         f"- **{negatives}** genuine negatives (ran, found nothing grounded)\n",
         f"- **{len(failed)}** failed extractions -- missing, not absent\n"]
    for doi, why in failed:
        L.append(f"  - `{doi}` ({why})\n")
    L.append(f"\n## Routing\n\n{len(rows)} tokens from "
             f"{len(set(r['raw'] for r in rows))} distinct bundle strings.\n\n")
    L.append("| route | tokens |\n|---|---:|\n")
    for k, v in routes.most_common():
        L.append(f"| {k} | {v} |\n")

    L.append("\n## Per-token\n\n")
    L.append("| raw string | token | canonical_name | vendor | version | route | why |\n")
    L.append("|---|---|---|---|---|---|---|\n")
    for r in sorted(rows, key=lambda r: (r["route"], r["raw"])):
        def c(x):
            return f"`{x}`" if x else "--"
        L.append(f"| {c(r['raw'][:60])} | {c(r['token'][:40])} | "
                 f"{c(r['canonical_name'])} | {c(r['vendor'])} | "
                 f"{c(r['version'])} | **{r['route']}** | {r['reason']} |\n")

    REVIEW_OUT.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_OUT.write_text("".join(L))
    print(f"\nTHREE-WAY: {len(withval)} with value / {negatives} negatives / "
          f"{len(failed)} failed")
    print("routes:", dict(routes))
    print(f"review -> {REVIEW_OUT}")


if __name__ == "__main__":
    main()
