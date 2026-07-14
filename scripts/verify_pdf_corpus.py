#!/usr/bin/env python3
"""
verify_pdf_corpus.py -- pre-extraction integrity check for the SciKG PDF corpus.

Two jobs, neither currently done anywhere in the pipeline:

  1. DEDUP      -- flag PDFs that are byte-identical (the same paper uploaded
                   twice under different names), both within this batch and
                   against past runs (via a small hash ledger).

  2. FILENAME   -- confirm each PDF's *contents* match the DOI in its filename,
     <-> CONTENT   by checking the DOI actually appears in the extracted text.
                   Punctuation is stripped on both sides, so it doesn't matter
                   that '_' in the filename could have been a '.' or a '/'.
                   Also flags access-wall/error pages saved as PDFs and files
                   with no extractable text (scanned / unreadable).

Writes a per-file CSV report (a provenance record of what was verified, when)
and updates a running hash ledger. NEVER deletes or renames anything -- raw
stays immutable; you decide what to do with the flags.

Run after every OnDemand upload:
    python scripts/verify_pdf_corpus.py --pdf-dir data/raw/pdfs

Optional, cuts false 'DOI_MISMATCH' flags on PDFs that don't print their DOI,
by corroborating against CrossRef titles from the worklist:
    ... --titles-csv data/raw/download_worklist_by_citations.csv

Exit code is nonzero when a hard problem is found, so it can gate 02d. By
default only DUPLICATE and SUSPECT_ACCESS_WALL are hard fails; add --strict
to also fail on DOI_MISMATCH and NO_TEXT.
"""

import argparse, csv, glob, hashlib, json, os, re, sys, datetime
from collections import Counter

MIN_TEXT = 100          # below this many chars of text -> treat as "no text"
TITLE_OK = 0.6          # title-word overlap that rescues a missing-DOI file

ACCESS_WALL_HINTS = [
    "access denied", "sign in to", "please sign in", "get access",
    "purchase this", "purchase pdf", "your institution", "institutional login",
    "verify you are human", "unusual traffic", "captcha", "log in to",
    "subscribe to", "does not subscribe", "not subscribe",
]


def normkey(s: str) -> str:
    """Lowercase and drop everything but a-z0-9. Makes DOI matching immune to
    how dots/slashes became underscores in the filename."""
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_text(path: str):
    """Return (text, total_pages). Reads page 0, 1, and the last page --
    covers the title page (DOI + title) and the footer/references (DOI again).
    Empty string on any failure."""
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("pypdf not installed -- run: pip install pypdf")
    try:
        reader = PdfReader(path)
        n = len(reader.pages)
        idxs = sorted({i for i in (0, 1, n - 1) if 0 <= i < n})
        return "\n".join((reader.pages[i].extract_text() or "") for i in idxs), n
    except Exception:
        return "", 0


def looks_like_wall(text: str, size_bytes: int) -> bool:
    t = text.lower()
    if size_bytes < 20 * 1024 and len(text.strip()) < 400:
        return True
    return any(h in t for h in ACCESS_WALL_HINTS) and len(text.strip()) < 3000


def load_titles(csv_path):
    """normkey(filename-without-ext) -> CrossRef title, best-effort."""
    titles = {}
    if not csv_path or not os.path.exists(csv_path):
        return titles
    try:
        for r in csv.DictReader(open(csv_path, newline="", encoding="utf-8-sig")):
            fn = (r.get("target_filename") or "").strip()
            fn = fn[:-4] if fn.lower().endswith(".pdf") else fn
            if fn and r.get("title"):
                titles[normkey(fn)] = r["title"]
    except Exception:
        pass
    return titles


def title_overlap(title: str, text: str) -> float:
    """Fraction of distinct 4+ letter title words that appear in the text."""
    words = set(re.findall(r"[a-z]{4,}", (title or "").lower()))
    if not words:
        return -1.0
    tl = text.lower()
    return round(sum(1 for w in words if w in tl) / len(words), 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf-dir", default="data/raw/pdfs")
    ap.add_argument("--report", default="data/processed/logs/pdf_corpus_check.csv")
    ap.add_argument("--ledger", default="data/processed/logs/pdf_ledger.json")
    ap.add_argument("--titles-csv", default="",
                    help="optional worklist CSV, for title corroboration")
    ap.add_argument("--strict", action="store_true",
                    help="also hard-fail on DOI_MISMATCH and NO_TEXT")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.pdf_dir, "*.pdf")))
    if not files:
        sys.exit(f"No PDFs found in {args.pdf_dir}")

    titles = load_titles(args.titles_csv)

    ledger = {}
    if os.path.exists(args.ledger):
        try:
            ledger = json.load(open(args.ledger))
        except Exception:
            ledger = {}
    seen_before = ledger.get("by_hash", {})     # sha -> filename first ever seen
    now = datetime.datetime.now().isoformat(timespec="seconds")

    # pass 1: hash everything, group to find byte-identical duplicates
    hash_to_names = {}
    meta = {}
    for p in files:
        name = os.path.basename(p)
        sha = sha256_file(p)
        hash_to_names.setdefault(sha, []).append(name)
        meta[name] = {"path": p, "sha256": sha, "size_bytes": os.path.getsize(p)}

    # pass 2: per-file content / DOI check + status
    hard_statuses = {"DUPLICATE", "SUSPECT_ACCESS_WALL"}
    if args.strict:
        hard_statuses |= {"DOI_MISMATCH", "NO_TEXT"}

    rows, hard_fail = [], 0
    for name in sorted(meta):
        m = meta[name]
        sha = m["sha256"]
        stem = name[:-4] if name.lower().endswith(".pdf") else name
        expected_key = normkey(stem)

        text, n_pages = extract_text(m["path"])
        text_chars = len(text.strip())
        doi_in_text = (text_chars >= MIN_TEXT) and (expected_key in normkey(text))

        # duplicate: another file on disk with the same bytes, or a byte-match
        # seen under a different name in a prior run
        dupes = [n for n in hash_to_names[sha] if n != name]
        prev = seen_before.get(sha)
        if prev and prev != name and prev not in hash_to_names[sha]:
            dupes.append(f"{prev} (prior run)")

        title = titles.get(expected_key)
        overlap = title_overlap(title, text) if title else -1.0

        if dupes:
            status = "DUPLICATE"
        elif looks_like_wall(text, m["size_bytes"]):
            status = "SUSPECT_ACCESS_WALL"
        elif text_chars < MIN_TEXT:
            status = "NO_TEXT"
        elif doi_in_text:
            status = "OK"
        elif overlap >= TITLE_OK:
            status = "OK_TITLE_ONLY"            # DOI not printed, but title matches
        else:
            status = "DOI_MISMATCH"             # DOI absent AND title uncorroborated

        if status in hard_statuses:
            hard_fail += 1

        rows.append({
            "file": name, "status": status, "sha256": sha[:16],
            "size_bytes": m["size_bytes"], "pages": n_pages,
            "text_chars": text_chars, "doi_in_text": doi_in_text,
            "title_overlap": overlap if overlap >= 0 else "",
            "duplicate_of": "; ".join(dupes),
        })

    # write report
    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    with open(args.report, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # update ledger (first-seen hash per file, for cross-run dup detection)
    by_hash = dict(seen_before)
    for name in meta:
        by_hash.setdefault(meta[name]["sha256"], name)
    json.dump({"by_hash": by_hash, "last_run": now},
              open(args.ledger, "w"), indent=2)

    # summary
    counts = Counter(r["status"] for r in rows)
    print(f"\nChecked {len(rows)} PDFs in {args.pdf_dir}")
    for s in ["OK", "OK_TITLE_ONLY", "NO_TEXT",
              "DUPLICATE", "SUSPECT_ACCESS_WALL", "DOI_MISMATCH"]:
        if counts.get(s):
            print(f"  {s:22} {counts[s]}")
    print(f"Report:  {args.report}")
    print(f"Ledger:  {args.ledger}")

    flagged = [r for r in rows if r["status"] not in ("OK", "OK_TITLE_ONLY")]
    if flagged:
        print("\nNeeds a look:")
        for r in flagged:
            extra = f"  (dup of {r['duplicate_of']})" if r["duplicate_of"] else ""
            print(f"  {r['status']:22} {r['file']}{extra}")

    if hard_fail:
        print(f"\n{hard_fail} hard failure(s). Fix before running 02d.")
        sys.exit(1)
    print("\nNo hard failures.")


if __name__ == "__main__":
    main()
