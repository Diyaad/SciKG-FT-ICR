#!/usr/bin/env python3
"""01b_fetch_pdfs.py — acquire open-access PDFs for the MagLab ICR corpus.

MUST RUN ON A LOGIN NODE. RCC compute nodes have no outbound internet; a
requests.get() from a compute node blocks on a TCP handshake that never
completes, and the job appears hung rather than failing.

Reads:  data/raw/maglab_icr_publications.csv
Writes: data/raw/pdfs/{doi_safe}.pdf          (only verified PDFs)
        data/processed/logs/pdf_fetch_log.jsonl   (one line per DOI attempted)

Reuses query_unpaywall(), download_pdf(), and make_doi_safe() from
02d_extract_pdf.py, so the %PDF- magic-byte check applies here too. An HTML
paywall page is never written to data/raw/.

Never overwrites an existing PDF: data/raw/ is immutable after write
(CLAUDE.md). A DOI whose PDF is already on disk is logged as "already_present"
and skipped, which makes the script resumable after an interruption.

Requires UNPAYWALL_EMAIL in the environment or in a .env file at the repo root.
Unpaywall's terms require a real, working contact address.

Usage
-----
    python scripts/01b_fetch_pdfs.py --limit 50            # random 50, seed 42
    python scripts/01b_fetch_pdfs.py --limit 50 --seed 7   # a different sample
    python scripts/01b_fetch_pdfs.py --all                 # every DOI in the CSV
    python scripts/01b_fetch_pdfs.py --limit 10 --dry-run  # resolve, download nothing

Only rows with a non-empty "Digital Object Identifier" are eligible. 404 of the
806 CSV rows have no DOI and cannot be fetched at all.
"""

import argparse
import csv
import importlib.util
import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

CSV_PATH = Path("data/raw/maglab_icr_publications.csv")
PDFS_DIR = Path("data/raw/pdfs")
LOG_PATH = Path("data/processed/logs/pdf_fetch_log.jsonl")
EXTRACT_SCRIPT = Path("scripts/02d_extract_pdf.py")

DOI_COLUMN = "Digital Object Identifier"
DEFAULT_SEED = 42

# Unpaywall asks for <= 100k calls/day and a courteous rate. 02d's
# query_unpaywall already sleeps 1s; this is an extra margin between DOIs.
INTER_DOI_SLEEP = 0.5


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_env_email():
    """UNPAYWALL_EMAIL from the environment, else from a .env at the repo root."""
    email = os.environ.get("UNPAYWALL_EMAIL", "").strip()
    if email:
        return email

    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            if key.strip() == "UNPAYWALL_EMAIL":
                return value.strip().strip("'\"")
    return ""


def load_02d():
    """Import 02d as a module so we reuse its acquisition helpers verbatim.

    Its heavy dependencies (docling, langextract) are imported lazily inside
    functions, so this is cheap and safe on a login node.
    """
    if not EXTRACT_SCRIPT.exists():
        sys.exit(f"ERROR: {EXTRACT_SCRIPT} not found. Run from the repo root.")
    spec = importlib.util.spec_from_file_location("extract02d", EXTRACT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def eligible_rows():
    """Every CSV row carrying a DOI. utf-8-sig strips the Excel byte-order mark."""
    if not CSV_PATH.exists():
        sys.exit(f"ERROR: {CSV_PATH} not found. Run from the repo root.")

    with CSV_PATH.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))

    if DOI_COLUMN not in (rows[0] if rows else {}):
        sys.exit(f"ERROR: column {DOI_COLUMN!r} not in CSV. Found: "
                 f"{list(rows[0].keys())[:6] if rows else 'no rows'}")

    eligible = [r for r in rows if (r.get(DOI_COLUMN) or "").strip()]
    return rows, eligible


def log_line(fh, **fields):
    fh.write(json.dumps(fields, ensure_ascii=False) + "\n")
    fh.flush()   # the run is long; do not lose the log to an interruption


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--limit", type=int, help="fetch a random sample of N DOIs")
    group.add_argument("--first", type=int, metavar="N",
                       help="fetch the first N DOIs in CSV order (newest-first; "
                            "biased toward recent years — see --limit for a spread)")
    group.add_argument("--all", action="store_true", help="fetch every DOI in the CSV")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help=f"random seed for --limit (default {DEFAULT_SEED}); "
                             "the same seed always selects the same papers")
    parser.add_argument("--dry-run", action="store_true",
                        help="query Unpaywall, report what would be fetched, download nothing")
    args = parser.parse_args()

    email = load_env_email()
    if not email:
        sys.exit("ERROR: UNPAYWALL_EMAIL is not set.\n"
                 "  echo 'UNPAYWALL_EMAIL=you@example.com' > .env\n"
                 "Unpaywall's terms require a real contact address.")

    mod = load_02d()
    # 02d hardcodes a placeholder address. Override it with the real one.
    mod.UNPAYWALL_EMAIL = email

    all_rows, eligible = eligible_rows()
    print(f"CSV rows:        {len(all_rows)}")
    print(f"With a DOI:      {len(eligible)}  ({100 * len(eligible) / max(len(all_rows), 1):.1f}%)")

    if args.all:
        selected = eligible
        print(f"Selected:        all {len(selected)}")
    elif args.first:
        selected = eligible[:args.first]
        years = [(r.get("Published Year") or "?").strip() for r in selected]
        span = f"{min(years)}-{max(years)}" if years else "n/a"
        print(f"Selected:        first {len(selected)} in CSV order  (years {span})")
        print("                 NOTE: the CSV is newest-first, so this is a recent-era slice.")
    else:
        n = min(args.limit, len(eligible))
        rng = random.Random(args.seed)
        selected = rng.sample(eligible, n)
        print(f"Selected:        {n} at random (seed {args.seed})")

    if args.dry_run:
        print("MODE:            dry run — nothing will be downloaded")
    print()

    PDFS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    counts = {"already_present": 0, "fetched": 0, "no_oa_location": 0,
              "download_failed": 0, "unpaywall_error": 0, "would_fetch": 0}
    started = time.time()

    with LOG_PATH.open("a", encoding="utf-8") as log:
        for i, row in enumerate(selected, 1):
            doi = row[DOI_COLUMN].strip()
            doi_safe = mod.make_doi_safe(doi)
            dest = PDFS_DIR / f"{doi_safe}.pdf"
            year = (row.get("Published Year") or "").strip()
            journal = (row.get("Journal Name") or "").strip()

            base = {"timestamp": now_iso(), "doi": doi, "doi_safe": doi_safe,
                    "maglab_id": (row.get("Id") or "").strip(),
                    "year": year, "journal": journal}

            # data/raw is immutable; never re-download or overwrite.
            if dest.exists():
                counts["already_present"] += 1
                log_line(log, outcome="already_present", pdf_path=str(dest), **base)
                print(f"[{i:>4}/{len(selected)}] SKIP  {doi}  (already on disk)")
                continue

            try:
                pdf_url = mod.query_unpaywall(doi)
            except Exception as exc:                      # network, JSON, timeout
                counts["unpaywall_error"] += 1
                log_line(log, outcome="unpaywall_error", error=repr(exc)[:200], **base)
                print(f"[{i:>4}/{len(selected)}] ERR   {doi}  ({type(exc).__name__})")
                time.sleep(INTER_DOI_SLEEP)
                continue

            if not pdf_url:
                counts["no_oa_location"] += 1
                log_line(log, outcome="no_oa_location", **base)
                print(f"[{i:>4}/{len(selected)}] CLOSED {doi}")
                time.sleep(INTER_DOI_SLEEP)
                continue

            if args.dry_run:
                counts["would_fetch"] += 1
                log_line(log, outcome="would_fetch", pdf_url=pdf_url, **base)
                print(f"[{i:>4}/{len(selected)}] OA    {doi}  -> {pdf_url[:70]}")
                time.sleep(INTER_DOI_SLEEP)
                continue

            # download_pdf verifies the %PDF- magic bytes and refuses to write
            # an HTML paywall page. It returns False for both a bad payload and
            # an HTTP failure; its own logging distinguishes them on stderr.
            ok = mod.download_pdf(pdf_url, dest)
            if ok:
                counts["fetched"] += 1
                size = dest.stat().st_size
                log_line(log, outcome="fetched", pdf_url=pdf_url,
                         pdf_path=str(dest), bytes=size, **base)
                print(f"[{i:>4}/{len(selected)}] OK    {doi}  ({size / 1024:.0f} KB)")
            else:
                counts["download_failed"] += 1
                log_line(log, outcome="download_failed", pdf_url=pdf_url, **base)
                print(f"[{i:>4}/{len(selected)}] FAIL  {doi}  (not a PDF, or download error)")

            time.sleep(INTER_DOI_SLEEP)

    elapsed = time.time() - started
    attempted = len(selected) - counts["already_present"]
    resolved = counts["fetched"] + counts["download_failed"] + counts["would_fetch"]

    print()
    print("=" * 62)
    print(f"Selected            {len(selected)}")
    print(f"  already on disk   {counts['already_present']}")
    print(f"  fetched           {counts['fetched']}")
    if args.dry_run:
        print(f"  would fetch       {counts['would_fetch']}")
    print(f"  no OA location    {counts['no_oa_location']}")
    print(f"  download failed   {counts['download_failed']}")
    print(f"  Unpaywall error   {counts['unpaywall_error']}")
    print("-" * 62)
    if attempted:
        print(f"Unpaywall found an OA PDF for {resolved}/{attempted} "
              f"newly attempted DOIs ({100 * resolved / attempted:.1f}%)")
    print(f"Elapsed             {elapsed:.0f}s")
    print(f"Log                 {LOG_PATH}")
    print("=" * 62)
    print()
    print("The open-access rate above is the number to quote. It is measured, not estimated.")


if __name__ == "__main__":
    main()
