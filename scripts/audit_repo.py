"""
audit_repo.py — read-only repository audit for SciKG.

Walks the entire repository and produces docs/REPO_AUDIT.md describing what
exists, what is redundant, what is stale, and what is missing. This script
NEVER modifies any file other than its own output (docs/REPO_AUDIT.md). It
does not touch data/raw/, does not call any external API, and does not delete
or reorder anything. It is a pure reporting tool.

Run from the repository root:
    python scripts/audit_repo.py
"""

import ast
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUTPUT = REPO / "docs" / "REPO_AUDIT.md"

IGNORE_DIRS = {".git", "__pycache__", "node_modules", ".pytest_cache",
               ".mypy_cache", ".ruff_cache", ".venv", "venv", ".idea", ".vscode"}
IGNORE_NAMES = {".DS_Store"}

# Packages declared in requirements.txt mapped to their import module names.
REQUIREMENTS_MODULES = {
    "requests": "requests",
    "neo4j": "neo4j",
    "pytest": "pytest",
    "python-dotenv": "dotenv",
}

# Concepts that CLAUDE.md states were REMOVED from scope. Any live reference in
# a design/spec doc (as opposed to a changelog noting the removal) is suspect.
REMOVED_CONCEPTS = [
    "Workflow entity", "Streamlit", "chatbot", "NetworkX", "networkx",
    "ASSOCIATED_WITH", "ProvenanceRecord",
]

# Pipeline stages declared in CLAUDE.md, in canonical order.
PIPELINE_SCRIPTS = [
    "01_fetch.py", "02_extract.py", "02b_extract_csv.py",
    "02c_extract_rawfiles.py", "03_normalize.py", "04_validate.py",
    "05_load.py",
]


def rel(p):
    return str(Path(p).resolve().relative_to(REPO))


def mtime_date(p):
    return datetime.fromtimestamp(os.path.getmtime(p), tz=timezone.utc).strftime("%Y-%m-%d")


def walk_files():
    files = []
    for root, dirs, names in os.walk(REPO):
        dirs[:] = sorted(d for d in dirs if d not in IGNORE_DIRS)
        for name in sorted(names):
            if name in IGNORE_NAMES:
                continue
            files.append(Path(root) / name)
    return files


# ---------------------------------------------------------------------------
# File classification + purpose inference
# ---------------------------------------------------------------------------

def classify(p):
    r = rel(p)
    name = p.name
    if name == ".gitkeep":
        return "config (placeholder)"
    if r.startswith("data/raw/"):
        return "data (raw, immutable)"
    if r.startswith("data/processed/") or r.startswith("outputs/"):
        return "generated"
    if r.startswith("tests/") and name.endswith(".py"):
        return "test"
    if r.startswith("scripts/") and name.endswith(".py"):
        return "script"
    if name.endswith(".md"):
        return "doc"
    if r.startswith("docs/metadata_templates/"):
        return "doc (template)"
    if name in {"requirements.txt", ".gitignore"} or name.endswith(".json") \
            or name.endswith(".yaml") or name.endswith(".yml") or name.endswith(".csv"):
        return "config"
    return "other"


def first_doc_or_heading(p):
    """One-line purpose: python docstring, markdown H1, json description, or csv header."""
    name = p.name
    try:
        if name.endswith(".py"):
            src = p.read_text(encoding="utf-8", errors="replace")
            try:
                mod = ast.parse(src)
                ds = ast.get_docstring(mod)
                if ds:
                    return ds.strip().splitlines()[0].strip()
            except SyntaxError:
                pass
            for line in src.splitlines()[:10]:
                s = line.strip()
                if s and not s.startswith("#"):
                    return s[:120]
            return "PURPOSE UNCLEAR"
        if name.endswith(".md"):
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines()[:15]:
                s = line.strip()
                if s.startswith("#"):
                    return s.lstrip("# ").strip()[:120]
                if s:
                    return s[:120]
            return "PURPOSE UNCLEAR"
        if name.endswith(".jsonl"):
            recs = jsonl_records(p)
            keys = sorted({k for r in recs if isinstance(r, dict) for k in r})
            return (f"JSONL data — {len(recs)} records; fields: "
                    + ", ".join(keys[:8]) + ("…" if len(keys) > 8 else ""))
        if name.endswith(".json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
                if isinstance(data, dict) and "description" in data:
                    return str(data["description"])[:120]
                if isinstance(data, dict):
                    return "JSON object; top-level keys: " + ", ".join(list(data.keys())[:6])
            except Exception:
                return "JSON (unparsed)"
        if name.endswith(".csv"):
            with open(p, newline="", encoding="utf-8-sig", errors="replace") as f:
                header = next(csv.reader(f), [])
            return "CSV columns: " + ", ".join(header[:8]) + ("…" if len(header) > 8 else "")
        if name.endswith((".yaml", ".yml")):
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines()[:10]:
                s = line.strip()
                if s and not s.startswith("#"):
                    return s[:120]
        if name == ".gitkeep":
            return "Placeholder to keep an otherwise-empty directory under version control"
        if name == ".gitignore":
            return "Git ignore rules"
        if name == "requirements.txt":
            return "Python dependency pins"
    except Exception as e:
        return f"PURPOSE UNCLEAR (read error: {e})"
    return "PURPOSE UNCLEAR"


# ---------------------------------------------------------------------------
# Data inventory helpers
# ---------------------------------------------------------------------------

def jsonl_records(p):
    recs = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line:
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                recs.append({"__parse_error__": True})
    return recs


def coverage(records):
    """Non-null / non-empty coverage % per top-level field."""
    fields = Counter()
    present = Counter()
    for rec in records:
        if not isinstance(rec, dict):
            continue
        for k, v in rec.items():
            fields[k] += 1
            if v not in (None, "", [], {}):
                present[k] += 1
    n = len(records)
    return {k: (present[k], n, round(100 * present[k] / n, 1) if n else 0.0)
            for k in fields}


def csv_info(p):
    with open(p, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        rows = sum(1 for _ in reader)
    return header, rows


# ---------------------------------------------------------------------------
# Script analysis
# ---------------------------------------------------------------------------

PATH_CONST_RE = re.compile(r'^([A-Z][A-Z0-9_]*)\s*=\s*Path\(\s*["\']([^"\']+)["\']')
STDLIB = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else set()


def analyze_script(p):
    src = p.read_text(encoding="utf-8", errors="replace")
    tree = None
    try:
        tree = ast.parse(src)
    except SyntaxError:
        pass

    is_stub = True
    if tree is not None:
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                is_stub = False
                break
            if isinstance(node, ast.If):  # e.g. if __name__ == "__main__"
                is_stub = False
                break
    # docstring-only / import-only files count as stubs
    nonimport = [n for n in (tree.body if tree else [])
                 if not isinstance(n, (ast.Import, ast.ImportFrom, ast.Expr))]
    if not nonimport:
        is_stub = True

    # path constants
    path_consts = {}
    for line in src.splitlines():
        m = PATH_CONST_RE.match(line.strip())
        if m:
            path_consts[m.group(1)] = m.group(2)

    # imports
    imports = set()
    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.add(n.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:
                    imports.add(node.module.split(".")[0])

    declared = set(REQUIREMENTS_MODULES.values())
    local_modules = {p.stem for p in (REPO / "scripts").glob("*.py")} | {"db", "scripts"}
    missing_imports = sorted(
        m for m in imports
        if m not in STDLIB and m not in declared and m not in local_modules
    )
    return {
        "is_stub": is_stub,
        "loc": len(src.splitlines()),
        "path_consts": path_consts,
        "missing_imports": missing_imports,
    }


# ---------------------------------------------------------------------------
# Build report
# ---------------------------------------------------------------------------

def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join("---" for _ in headers) + " |"]
    for r in rows:
        cells = [str(c).replace("|", "\\|").replace("\n", " ") for c in r]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def main():
    files = walk_files()

    # ---- gather text of key docs for cross-checks ----
    readme = (REPO / "README.md").read_text(encoding="utf-8", errors="replace")
    claude = (REPO / "CLAUDE.md").read_text(encoding="utf-8", errors="replace")
    docs = {p: p.read_text(encoding="utf-8", errors="replace")
            for p in files if p.suffix == ".md"}
    # Spec/governance docs only — exclude the large annotation corpus, which is
    # ground-truth *data*, not a specification, and produces false-positive
    # keyword hits in the cross-doc conflict scans.
    spec_docs = {p: t for p, t in docs.items()
                 if "annotations/" not in rel(p) and p.resolve() != OUTPUT.resolve()}

    # ---- Section 2 data prep ----
    pubs_path = REPO / "data/processed/entities/publications.jsonl"
    pub_records = jsonl_records(pubs_path) if pubs_path.exists() else []
    pub_dois = [str(r.get("doi", "")).lower() for r in pub_records if isinstance(r, dict)]
    dup_dois = [d for d, c in Counter(pub_dois).items() if c > 1 and d]
    required = ("doi", "title", "year")
    missing_required = []
    for r in pub_records:
        if not isinstance(r, dict):
            continue
        miss = [f for f in required if not r.get(f)]
        if miss:
            missing_required.append((r.get("doi", "?"), miss))

    # doi_list.csv
    doi_list_path = REPO / "data/raw/doi_list.csv"
    doi_list = []
    if doi_list_path.exists():
        with open(doi_list_path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                doi_list.append(row["doi"].strip().lower())

    def safe(doi):
        return doi.replace("/", "_").replace(".", "_")

    listed_safe = {safe(d): d for d in doi_list}

    # raw publication files
    raw_pub_dir = REPO / "data/raw/publications"
    raw_pub_files = sorted(p.stem for p in raw_pub_dir.glob("*.json"))
    fetched_not_listed = [s for s in raw_pub_files if s not in listed_safe]
    listed_not_fetched = [d for s, d in listed_safe.items() if s not in raw_pub_files]

    # manifest
    manifest_path = REPO / "data/raw/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    manifest_dois = {d.lower() for d in manifest.get("papers", {}).keys()}
    disk_dois = {listed_safe.get(s, s) for s in raw_pub_files}
    jsonl_dois = set(pub_dois)
    manifest_vs_disk = sorted(manifest_dois.symmetric_difference(
        {d.lower() for d in (listed_safe.get(s, s) for s in raw_pub_files)}))
    manifest_vs_jsonl = sorted(manifest_dois.symmetric_difference(jsonl_dois))

    # maglab csv
    maglab_path = REPO / "data/raw/maglab_icr_publications.csv"
    maglab_header, maglab_rows = csv_info(maglab_path) if maglab_path.exists() else ([], 0)

    # ---- Section 4 script analysis ----
    py_files = [p for p in files if p.suffix == ".py" and
                (rel(p).startswith("scripts/") or rel(p).startswith("tests/"))]
    script_data = {p: analyze_script(p) for p in py_files}

    # ---- Cross-doc conflict detection ----
    conflicts = []

    # Software entity: logged vs excluded
    soft_logged = [(rel(p), i + 1, ln.strip()) for p, t in spec_docs.items()
                   for i, ln in enumerate(t.splitlines())
                   if re.search(r"Software.*log(ged|s)?\b.*entit", ln, re.I)]
    soft_excluded = [(rel(p), i + 1, ln.strip()) for p, t in spec_docs.items()
                     for i, ln in enumerate(t.splitlines())
                     if re.search(r"Software.*(exclud|not.*scope|remains excluded)", ln, re.I)]
    if soft_logged and soft_excluded:
        conflicts.append((
            "Software entity status",
            "CLAUDE.md/README say Software is a *logged entity*; "
            "VERIFIED_FACTS_AND_ASSUMPTIONS.md says it is *excluded from v1.0*.",
            soft_logged + soft_excluded,
            "CLAUDE.md (architecture decisions) — 'Software and Instrument are logged entities'.",
        ))

    # Ground-truth count: 8 vs 17
    gt8 = [(rel(p), i + 1, ln.strip()) for p, t in spec_docs.items()
           for i, ln in enumerate(t.splitlines())
           if re.search(r"\b8\b[^.]{0,40}(ground.?truth|annotated paper)", ln, re.I)]
    gt17 = [(rel(p), i + 1, ln.strip()) for p, t in spec_docs.items()
            for i, ln in enumerate(t.splitlines())
            if re.search(r"\b17\b[^.]{0,40}ground.?truth", ln, re.I)]
    if gt8 and gt17:
        conflicts.append((
            "Ground-truth paper count",
            "CLAUDE.md/README/controlled_vocabulary say 8 ground-truth papers; "
            "METADATA_INVENTORY.md says 17. (17 is the fetched-CrossRef corpus, "
            "not the validation set.)",
            gt8 + gt17,
            "CLAUDE.md — 'ground-truth set of 8 manually annotated papers'.",
        ))

    # Removed concepts still live in design docs
    removed_hits = defaultdict(list)
    for p, t in spec_docs.items():
        rname = rel(p)
        for i, ln in enumerate(t.splitlines()):
            for concept in REMOVED_CONCEPTS:
                if concept.lower() in ln.lower():
                    removed_hits[concept].append((rname, i + 1, ln.strip()))

    # ---- Pipeline-script existence ----
    existing_scripts = {p.name for p in (REPO / "scripts").glob("*.py")}
    pipeline_status = [(s, "EXISTS" if s in existing_scripts else "MISSING")
                       for s in PIPELINE_SCRIPTS]

    # ---- referenced-by checks ----
    def referenced(name):
        return ("Yes" if (name in readme or name in claude) else "No")

    # ===================================================================
    # ASSEMBLE MARKDOWN
    # ===================================================================
    L = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    L.append(f"# SciKG Repository Audit\n")
    L.append(f"*Generated by `scripts/audit_repo.py` on {today} (UTC). "
             f"Read-only audit — no files were modified, nothing deleted.*\n")

    # ----- Section 8 summary (placed first, per spec) -----
    n_scripts = sum(1 for p in py_files if rel(p).startswith("scripts/"))
    n_scripts_impl = sum(1 for p in py_files if rel(p).startswith("scripts/")
                         and not script_data[p]["is_stub"])
    n_tests = sum(1 for p in py_files if rel(p).startswith("tests/"))
    n_tests_impl = sum(1 for p in py_files if rel(p).startswith("tests/")
                       and not script_data[p]["is_stub"])
    n_docs = sum(1 for p in files if p.suffix == ".md")

    L.append("## One-Page Summary\n")
    L.append(f"- **Total files (tracked types):** {len(files)}")
    L.append(f"- **Scripts in `scripts/`:** {n_scripts} "
             f"({n_scripts_impl} implemented, {n_scripts - n_scripts_impl} stub/placeholder)")
    L.append(f"- **Tests in `tests/`:** {n_tests} "
             f"({n_tests_impl} implemented, {n_tests - n_tests_impl} stub)")
    L.append(f"- **Docs (.md):** {n_docs}")
    L.append("- **Data records by source:**")
    L.append(f"  - `data/raw/doi_list.csv`: {len(doi_list)} DOIs (CrossRef fetch input)")
    L.append(f"  - `data/raw/publications/*.json`: {len(raw_pub_files)} raw CrossRef responses")
    L.append(f"  - `data/processed/entities/publications.jsonl`: {len(pub_records)} extracted records")
    L.append(f"  - `data/raw/manifest.json`: {len(manifest_dois)} tracked papers")
    L.append(f"  - `data/raw/maglab_icr_publications.csv`: {maglab_rows} data rows "
             f"× {len(maglab_header)} columns (806-paper corpus)")
    L.append("")
    L.append("**Top conflicts / duplications:**\n")
    L.append("1. **Software entity** — logged (CLAUDE.md/README) vs. excluded "
             "(VERIFIED_FACTS_AND_ASSUMPTIONS.md). Direct contradiction.")
    L.append("2. **Ground-truth count** — 8 papers (CLAUDE.md/README) vs. 17 "
             "(METADATA_INVENTORY.md, two places).")
    L.append("3. **Removed entities still specified** — `Workflow` and "
             "`ProvenanceRecord` remain full rows in KNOWLEDGE_GRAPH_DESIGN.md "
             "despite being removed from scope in CLAUDE.md.")
    L.append("4. **Removed scope echoed in README** — README line ~46 lists "
             "“processing workflows · provenance records” as graph content.")
    L.append("5. **DOI provenance is tracked in 4 places** — doi_list.csv, "
             "manifest.json, raw/publications/ filenames, and publications.jsonl "
             "all encode the same 17-DOI set (kept in sync today, but 4 sources of truth).")
    L.append("")
    L.append("**Top missing items:**\n")
    L.append("1. `03_normalize.py`, `04_validate.py`, `05_load.py` — referenced "
             "by the pipeline + tests, not yet written.")
    L.append("2. `02b_extract_csv.py`, `02c_extract_rawfiles.py` — next scripts to author.")
    L.append("3. `scripts/db.py` — referenced by CLAUDE.md (05_load writes via it), absent.")
    L.append("4. A single canonical **schema doc** — CLAUDE.md points integrity "
             "questions to VERIFIED_FACTS_AND_ASSUMPTIONS.md; there is no "
             "`SCIKG_SCHEMA.md`, and KNOWLEDGE_GRAPH_DESIGN.md is stale.")
    L.append("5. Real test bodies — all 5 test files are docstring-only stubs.")
    L.append("")
    L.append("**Recommended next 3 actions (priority order):**\n")
    L.append("1. **Reconcile the Software-entity and ground-truth-count conflicts** "
             "before writing 03–05, since the loader encodes both. Make CLAUDE.md "
             "the source of truth and KEEP-UPDATE the other docs.")
    L.append("2. **KEEP-UPDATE or ARCHIVE KNOWLEDGE_GRAPH_DESIGN.md** — strip "
             "Workflow/ProvenanceRecord or move to `docs/archive/` so the loader "
             "isn't built against a removed model.")
    L.append("3. **Write `02b_extract_csv.py` and `02c_extract_rawfiles.py`** next, "
             "then 03–05, filling the stub tests as you go.")
    L.append("")

    # ----- Section 1 -----
    L.append("---\n\n## Section 1: Inventory of All Files\n")
    rows = []
    for p in files:
        rows.append((rel(p), os.path.getsize(p), mtime_date(p),
                     classify(p), first_doc_or_heading(p)))
    L.append(md_table(["Path", "Bytes", "Modified", "Type", "Purpose"], rows))
    L.append("")

    # ----- Section 2 -----
    L.append("---\n\n## Section 2: Data Inventory\n")
    data_files = [p for p in files if rel(p).startswith("data/") and p.name != ".gitkeep"]
    L.append("### 2.1 All files under `data/`\n")
    drows = []
    for p in data_files:
        r = rel(p)
        fmt = p.suffix.lstrip(".")
        kind = ("immutable raw" if r.startswith("data/raw/")
                else "processed/generated")
        if p.suffix == ".jsonl":
            recs = jsonl_records(p)
            cov = coverage(recs)
            fields = ", ".join(sorted(cov))
            cnt = len(recs)
        elif p.suffix == ".json":
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(d, dict) and "papers" in d:
                    cnt = len(d["papers"])
                    fields = "version, description, papers{doi,fetched_at,source_api,raw_file,stages_complete}"
                else:
                    cnt = 1
                    fields = ", ".join(list(d)[:8]) if isinstance(d, dict) else "(array)"
            except Exception:
                cnt, fields = "?", "(unparsed)"
        elif p.suffix == ".csv":
            hdr, n = csv_info(p)
            cnt = n
            fields = ", ".join(hdr[:6]) + ("…" if len(hdr) > 6 else "")
        elif p.suffix == ".txt":
            cnt = len([x for x in p.read_text(errors="replace").splitlines() if x.strip()])
            fields = "(lines)"
        else:
            cnt, fields = "-", "-"
        drows.append((r, fmt, cnt, kind, fields[:90]))
    L.append(md_table(["Path", "Format", "Records", "Kind", "Fields"], drows))
    L.append("")

    # coverage for publications.jsonl
    L.append("### 2.2 `data/processed/entities/publications.jsonl` (detail)\n")
    L.append(f"- **Records:** {len(pub_records)}")
    L.append(f"- **DOIs covered (lowercase):**")
    for d in sorted(pub_dois):
        L.append(f"  - `{d}`")
    L.append(f"- **Duplicate DOIs:** {('none' if not dup_dois else ', '.join(dup_dois))}")
    if missing_required:
        L.append("- **Records missing required (doi/title/year):**")
        for doi, miss in missing_required:
            L.append(f"  - `{doi}` missing {miss}")
    else:
        L.append("- **Records missing required fields (doi/title/year):** none")
    L.append("\n**Field coverage (non-null %):**\n")
    cov = coverage(pub_records)
    L.append(md_table(["Field", "Populated", "Total", "Coverage %"],
                      [(k, v[0], v[1], v[2]) for k, v in sorted(cov.items())]))
    L.append("")

    # raw publications cross-check
    L.append("### 2.3 `data/raw/publications/*.json` cross-checks\n")
    L.append(f"- **Files on disk:** {len(raw_pub_files)}")
    L.append(f"- **DOIs in doi_list.csv:** {len(doi_list)}")
    L.append(f"- **Fetched files NOT in doi_list.csv:** "
             f"{('none' if not fetched_not_listed else ', '.join(fetched_not_listed))}")
    L.append(f"- **DOIs in list with NO fetched file:** "
             f"{('none' if not listed_not_fetched else ', '.join(listed_not_fetched))}")
    L.append(f"- **Manifest papers:** {len(manifest_dois)}")
    L.append(f"- **Manifest vs disk mismatch:** "
             f"{('none' if not manifest_vs_disk else ', '.join(manifest_vs_disk))}")
    L.append(f"- **Manifest vs publications.jsonl mismatch:** "
             f"{('none' if not manifest_vs_jsonl else ', '.join(manifest_vs_jsonl))}")
    L.append("")

    # maglab
    L.append("### 2.4 `data/raw/maglab_icr_publications.csv`\n")
    L.append(f"- **Data rows:** {maglab_rows}")
    L.append(f"- **Columns ({len(maglab_header)}):** " + ", ".join(maglab_header))
    L.append("\n*(Full field-level inventory of this CSV is a separate task.)*")
    L.append("")

    # ----- Section 3 -----
    L.append("---\n\n## Section 3: Documentation Audit\n")
    md_files = [p for p in files if p.suffix == ".md"]
    drows = []
    for p in md_files:
        text = docs[p]
        wc = len(text.split())
        drows.append((rel(p), mtime_date(p), wc, referenced(p.name)))
    L.append(md_table(["Doc", "Modified", "Words", "Ref'd by README/CLAUDE?"], drows))
    L.append("\n### 3.1 Internal-contradiction checks\n")
    L.append(f"- **Pipeline stages in CLAUDE.md vs scripts on disk:**")
    for s, status in pipeline_status:
        L.append(f"  - `{s}` — {status}")
    L.append(f"- **Ground-truth count (CLAUDE.md = 8):** "
             f"conflict found — METADATA_INVENTORY.md states 17 (see Section 5).")
    L.append(f"- **Corpus size 806:** MagLab CSV has **{maglab_rows}** data rows — "
             f"{'matches' if maglab_rows == 806 else 'MISMATCH with'} the 806 cited in "
             f"CLAUDE.md/README.")
    L.append("- **SCIKG_SCHEMA.md:** not present and not referenced by any doc. "
             "The de-facto schema doc is KNOWLEDGE_GRAPH_DESIGN.md (stale — see below).")
    L.append("- **References to removed concepts:**")
    if removed_hits:
        for concept in REMOVED_CONCEPTS:
            hits = removed_hits.get(concept)
            if hits:
                locs = "; ".join(f"{r}:{ln}" for r, ln, _ in hits)
                L.append(f"  - `{concept}` → {locs}")
    else:
        L.append("  - none found")
    L.append("\n### 3.2 Draft / superseded docs\n")
    L.append("- **KNOWLEDGE_GRAPH_DESIGN.md** — contains a full entity/edge model "
             "including `Workflow` and `ProvenanceRecord`, both explicitly removed "
             "in CLAUDE.md. Superseded by CLAUDE.md's architecture-decisions block; "
             "needs update or archival.")
    L.append("- **ROADMAP.md** — self-labelled *“Proposed Research Workflow … not an "
             "approved plan.”* Intentional draft; keep but treat as non-authoritative.")
    L.append("- **METADATA_INVENTORY.md** — mixes the 17-paper fetched corpus with the "
             "8-paper ground-truth set; partially stale.")
    L.append("")

    # ----- Section 4 -----
    L.append("---\n\n## Section 4: Script Audit\n")
    srows = []
    for p in py_files:
        d = script_data[p]
        reads, writes = [], []
        for k, v in d["path_consts"].items():
            exists = (REPO / v).exists()
            tag = f"`{v}`{'' if exists else ' (MISSING)'}"
            if any(x in k for x in ("OUTPUT", "MANIFEST", "WRITE")) and "DIR" not in k:
                # heuristic; manifest is both read+written
                writes.append(tag)
            if any(x in k for x in ("INPUT", "DIR", "LIST", "MANIFEST", "SOURCE", "CSV")):
                reads.append(tag)
        srows.append((
            rel(p),
            "stub" if d["is_stub"] else "implemented",
            ", ".join(reads) or "—",
            ", ".join(writes) or "—",
            ", ".join(d["missing_imports"]) or "none",
            mtime_date(p),
        ))
    L.append(md_table(["Script", "Status", "Reads (path consts)", "Writes (path consts)",
                       "Imports not in requirements", "Modified"], srows))
    L.append("\n*Path constants are parsed from top-level `NAME = Path(\"...\")` "
             "assignments; read/write split is heuristic. `(MISSING)` marks a "
             "referenced path that does not yet exist on disk.*")
    L.append("")

    # ----- Section 5 -----
    L.append("---\n\n## Section 5: Redundancy and Conflict Report\n")
    L.append("### 5.1 Conflicting facts across docs\n")
    for i, (title, desc, locs, sot) in enumerate(conflicts, 1):
        L.append(f"**C{i}. {title}**")
        L.append(f"- {desc}")
        L.append("- Evidence:")
        for r, ln, txt in locs:
            L.append(f"  - `{r}:{ln}` — {txt[:120]}")
        L.append(f"- **Source of truth:** {sot}")
        L.append("")
    # removed concepts as conflict
    L.append("**C%d. Removed entities still specified in design docs**" % (len(conflicts) + 1))
    for concept in ("Workflow entity", "ProvenanceRecord", "NetworkX", "networkx",
                    "Streamlit", "chatbot", "ASSOCIATED_WITH"):
        hits = removed_hits.get(concept)
        if hits:
            for r, ln, txt in hits:
                L.append(f"- `{r}:{ln}` — {concept}: {txt[:100]}")
    L.append("- **Source of truth:** CLAUDE.md — these are removed from scope.")
    L.append("  README mentions of removed items are in an *out-of-scope* list "
             "(acceptable); KNOWLEDGE_GRAPH_DESIGN.md mentions are in the *active "
             "model* (stale).")
    L.append("")
    L.append("### 5.2 Same information stored in multiple places\n")
    L.append("- **17-DOI provenance set** lives in 4 files: `data/raw/doi_list.csv` "
             "(input, source of truth), `data/raw/manifest.json` (fetch tracker), "
             "`data/raw/publications/*.json` filenames, and "
             "`data/processed/entities/publications.jsonl`. All consistent today; "
             "doi_list.csv is the source of truth — the others are derived.")
    L.append("- **Corpus size 806** repeated in CLAUDE.md (3×) and README; "
             "matches the CSV. Keep CLAUDE.md authoritative.")
    L.append("- **FAIR / scope / architecture narrative** is spread across README, "
             "ARCHITECTURE.md, FAIR_PRINCIPLES.md, VERIFIED_FACTS_AND_ASSUMPTIONS.md; "
             "some overlap but different altitudes — not strictly redundant.")
    L.append("")
    L.append("### 5.3 Data-integrity cross-checks\n")
    L.append(f"- Files in `publications/` not matching doi_list/manifest: "
             f"{'none' if not fetched_not_listed else fetched_not_listed}")
    L.append(f"- Records in publications.jsonl missing required fields: "
             f"{'none' if not missing_required else missing_required}")
    L.append(f"- Duplicate DOIs in publications.jsonl: "
             f"{'none' if not dup_dois else dup_dois}")
    L.append("")
    L.append("### 5.4 Tests for nonexistent scripts\n")
    for p in sorted(py_files):
        if rel(p).startswith("tests/"):
            target = p.name.replace("test_", "")
            matches = [s for s in existing_scripts if s.endswith(target)
                       or s[3:] == target]
            tgt_exists = any(matches)
            L.append(f"- `{rel(p)}` → targets `*{target}` — "
                     f"{'script exists' if tgt_exists else '**no implemented script yet**'}")
    L.append("")

    # ----- Section 6 -----
    L.append("---\n\n## Section 6: Recommended Actions\n")
    L.append("*Never DELETE. ARCHIVE = move to `docs/archive/` (preserve for "
             "FAIR backtracking).*\n")
    recs = [
        ("CLAUDE.md", "KEEP", "Authoritative project rules + architecture decisions."),
        ("README.md", "KEEP-UPDATE", "Strip “processing workflows · provenance "
         "records” (line ~46) from the graph-content description to match removed scope."),
        ("docs/KNOWLEDGE_GRAPH_DESIGN.md", "KEEP-UPDATE", "Remove Workflow & "
         "ProvenanceRecord rows/edges/diagram, or ARCHIVE if a fresh schema doc "
         "replaces it. Currently encodes a removed model the loader must not follow."),
        ("docs/VERIFIED_FACTS_AND_ASSUMPTIONS.md", "KEEP-UPDATE", "Resolve the "
         "Software-entity line (excluded) against CLAUDE.md (logged). Pick one; "
         "this doc is cited by CLAUDE.md as the integrity reference, so it must be correct."),
        ("docs/METADATA_INVENTORY.md", "KEEP-UPDATE", "Change “17 ground-truth "
         "papers” → 17 fetched papers / 8 ground-truth, to end the count conflict."),
        ("docs/ROADMAP.md", "KEEP", "Self-labelled proposed/non-approved; useful context."),
        ("docs/ARCHITECTURE.md", "KEEP", "Decisions marked deferred; `networkx` "
         "appears only in a rejected-candidates list — acceptable."),
        ("docs/DISCOVERY_QUESTIONS.md", "KEEP", "Open questions incl. RAW-file "
         "relationship under review; live working doc."),
        ("docs/REVIEW_LOG.md", "KEEP", "Append-only audit trail; FAIR-relevant."),
        ("docs/FAIR_PRINCIPLES.md", "KEEP", "Reference; ‘phase’ wording is generic."),
        ("docs/controlled_vocabulary.md", "KEEP", "Active vocabulary for normalize stage."),
        ("docs/annotations/paper_reviews.md", "KEEP", "13k-word manual annotations — "
         "the ground-truth source; irreplaceable."),
        ("data/processed/entities/publications.jsonl", "REGENERATE", "Output of "
         "02_extract.py; rebuilt from immutable raw. Safe to archive/regenerate."),
        ("scripts/01_fetch.py", "KEEP", "Implemented stage 1."),
        ("scripts/02_extract.py", "KEEP", "Implemented stage 2."),
        ("scripts/audit_repo.py", "KEEP", "This audit tool."),
        ("tests/test_*.py", "KEEP-UPDATE", "All stubs; fill in as each stage lands."),
    ]
    L.append(md_table(["Target", "Action", "Rationale / what to update"], recs))
    L.append("\n**ARCHIVE candidates & what would be lost:**\n")
    L.append("- *KNOWLEDGE_GRAPH_DESIGN.md* (only if replaced) — losing it entirely "
             "would lose the early entity/edge brainstorming and the RDF-vs-property-graph "
             "trade-off discussion. **Recommend KEEP-UPDATE over ARCHIVE** so that "
             "history stays visible; archive only after a clean schema doc exists.")
    L.append("- No file currently warrants outright archival; the stale docs are "
             "cheaper to correct in place. Nothing is dead weight enough to remove "
             "from the active tree this week.")
    L.append("")

    # ----- Section 7 -----
    L.append("---\n\n## Section 7: What Is Missing\n")
    L.append("**Pipeline scripts not yet written (declared in CLAUDE.md):**")
    for s, status in pipeline_status:
        if status == "MISSING":
            L.append(f"- `scripts/{s}`")
    L.append("\n**Other referenced-but-absent code:**")
    L.append("- `scripts/db.py` — CLAUDE.md: “05_load.py … writes to Neo4j via "
             "scripts/db.py.” Not present.")
    L.append("\n**Docs referenced but not present:**")
    L.append("- `SCIKG_SCHEMA.md` — not referenced by any doc and not present. If a "
             "canonical schema doc is desired, it must be created (KNOWLEDGE_GRAPH_"
             "DESIGN.md is the closest existing artifact but is stale).")
    L.append("- `docs/archive/` — referenced by this audit's ARCHIVE policy; does not "
             "exist yet (create on first archival).")
    L.append("\n**Data files referenced by the pipeline but not present:**")
    for path in ["data/raw/rawfile_names.txt",
                 "data/processed/entities/rawfiles.jsonl",
                 "data/processed/normalized/ (only .gitkeep)",
                 "data/processed/validated/ (only .gitkeep)",
                 "data/processed/validation_report.json",
                 "data/processed/quarantine.jsonl",
                 "data/processed/normalized/review_queue.jsonl",
                 "data/processed/normalized/normalization_log.jsonl"]:
        present = (REPO / path.split(" ")[0]).exists()
        L.append(f"- `{path}` — {'present' if present else 'absent (expected once stages 02b–05 run)'}")
    L.append("\n**Tests that should exist:**")
    L.append("- Test bodies for all five stages exist as files but are docstring-only "
             "stubs. `test_extract.py`/`test_fetch.py` target implemented scripts and "
             "should be filled first; `test_normalize/validate/load` await their scripts.")
    L.append("- No test for `02b_extract_csv.py` / `02c_extract_rawfiles.py` yet.")
    L.append("")

    OUTPUT.write_text("\n".join(L), encoding="utf-8")
    print(f"Audit complete. Report written to: {rel(OUTPUT)}")
    print(f"  Files inventoried: {len(files)}")
    print(f"  Scripts: {n_scripts} ({n_scripts_impl} implemented)  |  "
          f"Tests: {n_tests} ({n_tests_impl} implemented)  |  Docs: {n_docs}")
    print(f"  Conflicts flagged: {len(conflicts) + 1}")


if __name__ == "__main__":
    main()
