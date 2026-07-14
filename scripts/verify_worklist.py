#!/usr/bin/env python3
"""
verify_worklist.py -- deterministic integrity check for the download worklist.

Answers, without any LLM in the loop: does every DOI I'm downloading trace back
to a real DOI in the supervisor's master list, and is the worklist internally
consistent? Pure stdlib, read-only, reproducible. Meant to be committed and run
before any download batch (and gate-able: exits nonzero on hard failure).

Checks
------
  [1] REAL DOIs only      -- every 'doi' cell in the worklist is a well-formed
                             DOI (10.NNNN/...). URLs / blanks are flagged; these
                             are the rows to fix. (HARD FAIL)
  [2] MEMBERSHIP          -- every well-formed worklist DOI appears in the
                             source's DOI column. Anything not in the source is
                             FOREIGN and must be justified. (HARD FAIL)
  [3] NO DUP DOIs         -- no DOI appears on two worklist rows. (HARD FAIL)
  [4] FILENAME <-> DOI    -- target_filename equals the DOI-derived name
                             (dots+slashes -> underscores, + .pdf). (HARD FAIL)
  [5] SOURCE HYGIENE      -- (report only) source rows whose own DOI column holds
                             a URL or is blank: these are backfill candidates,
                             the reason a URL ever leaks into the worklist.
  [6] DISK RECON          -- (optional, --pdf-dir) reconcile source DOIs against
                             what's actually downloaded: on-worklist vs
                             already-on-disk (open-access) vs unaccounted.

Usage
-----
  python scripts/verify_worklist.py \
      --source data/raw/maglab_icr_publications.csv \
      --worklist data/raw/download_worklist_by_citations.csv

  # add disk reconciliation:
      --pdf-dir data/raw/pdfs

Column names are configurable via flags if the CSV headers ever change.
"""

import argparse, csv, glob, os, re, sys
from collections import Counter, defaultdict

WELLFORMED_DOI = re.compile(r'^10\.\d{4,9}/\S+$')


def norm_doi(s: str) -> str:
    """Strip doi.org wrappers and lowercase. A publisher URL (nature.com, etc.)
    is left intact and will simply fail the well-formed test."""
    s = (s or '').strip().lower()
    for pre in ('https://doi.org/', 'http://doi.org/', 'https://dx.doi.org/',
                'http://dx.doi.org/', 'doi.org/', 'dx.doi.org/'):
        if s.startswith(pre):
            s = s[len(pre):]
            break
    return s.rstrip('/')


def doi_to_filename(d: str) -> str:
    """Project convention: dots and slashes -> underscores, then .pdf.
    Hyphens are preserved (e.g. 10_1038_s41467-017-01123-0.pdf)."""
    return d.replace('.', '_').replace('/', '_') + '.pdf'


def load_source_dois(path, doi_col):
    """Return (set_of_wellformed_dois, list_of_bad_rows). bad_rows = rows whose
    DOI cell is a URL or blank."""
    good, bad = set(), []
    with open(path, newline='', encoding='utf-8-sig') as f:
        rdr = csv.DictReader(f)
        if doi_col not in (rdr.fieldnames or []):
            sys.exit(f"[fatal] source has no column {doi_col!r}. "
                     f"Columns: {rdr.fieldnames}")
        for r in rdr:
            d = norm_doi(r.get(doi_col, ''))
            if WELLFORMED_DOI.match(d):
                good.add(d)
            else:
                bad.append({'id': r.get('Id', ''), 'raw': (r.get(doi_col, '') or '').strip(),
                            'title': (r.get('Title', '') or '')[:70]})
    return good, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True)
    ap.add_argument('--worklist', required=True)
    ap.add_argument('--pdf-dir', default='', help='optional: enables disk reconciliation')
    ap.add_argument('--source-doi-col', default='Digital Object Identifier')
    ap.add_argument('--worklist-doi-col', default='doi')
    ap.add_argument('--worklist-fname-col', default='target_filename')
    ap.add_argument('--report', default='', help='optional CSV path for the per-row verdict')
    args = ap.parse_args()

    for p in (args.source, args.worklist):
        if not os.path.exists(p):
            sys.exit(f"[fatal] file not found: {p}")

    src_dois, src_bad = load_source_dois(args.source, args.source_doi_col)

    # load worklist
    with open(args.worklist, newline='', encoding='utf-8-sig') as f:
        rdr = csv.DictReader(f)
        for c in (args.worklist_doi_col, args.worklist_fname_col):
            if c not in (rdr.fieldnames or []):
                sys.exit(f"[fatal] worklist has no column {c!r}. Columns: {rdr.fieldnames}")
        wl = list(rdr)

    not_real, foreign, fname_bad = [], [], []
    doi_rows = defaultdict(list)
    verdict = []

    for i, r in enumerate(wl):
        raw = (r.get(args.worklist_doi_col, '') or '').strip()
        d = norm_doi(raw)
        fname = (r.get(args.worklist_fname_col, '') or '').strip()
        status = 'OK'

        if not WELLFORMED_DOI.match(d):
            not_real.append({'row': i + 2, 'raw': raw, 'title': (r.get('title', '') or '')[:60]})
            status = 'NOT_A_DOI'
        else:
            doi_rows[d].append(i + 2)
            if d not in src_dois:
                foreign.append({'row': i + 2, 'doi': d, 'title': (r.get('title', '') or '')[:60]})
                status = 'FOREIGN'
            expect = doi_to_filename(d)
            if fname and fname.lower() != expect.lower():
                fname_bad.append({'row': i + 2, 'doi': d, 'have': fname, 'want': expect})
                status = 'FILENAME_MISMATCH' if status == 'OK' else status
        verdict.append({'row': i + 2, 'doi_cell': raw, 'status': status, 'target_filename': fname})

    dup_dois = {d: rows for d, rows in doi_rows.items() if len(rows) > 1}

    # ---- report ----
    print(f"source:   {args.source}")
    print(f"worklist: {args.worklist}")
    print(f"\nsource well-formed DOIs: {len(src_dois)}   (source rows with URL/blank DOI cell: {len(src_bad)})")
    print(f"worklist rows: {len(wl)}   well-formed DOIs: {len(doi_rows)}   non-DOI cells: {len(not_real)}")

    print(f"\n[1] worklist cells that are NOT a real DOI: {len(not_real)}   {'FAIL' if not_real else 'ok'}")
    for x in not_real:
        print(f"      row {x['row']}: {x['raw']!r}  (...{x['title']})")

    print(f"\n[2] worklist DOIs not found in source: {len(foreign)}   {'FAIL' if foreign else 'ok'}")
    for x in foreign:
        print(f"      row {x['row']}: {x['doi']}  (...{x['title']})")

    print(f"\n[3] duplicate DOIs within worklist: {len(dup_dois)}   {'FAIL' if dup_dois else 'ok'}")
    for d, rows in dup_dois.items():
        print(f"      {d}  on rows {rows}")

    print(f"\n[4] target_filename != DOI-derived name: {len(fname_bad)}   {'FAIL' if fname_bad else 'ok'}")
    for x in fname_bad:
        print(f"      row {x['row']}: have {x['have']!r}  want {x['want']!r}")

    print(f"\n[5] source rows with URL/blank DOI cell (backfill candidates, report only): {len(src_bad)}")
    for x in src_bad[:12]:
        print(f"      Id {x['id']}: {x['raw']!r}  (...{x['title']})")
    if len(src_bad) > 12:
        print(f"      ... and {len(src_bad) - 12} more")

    # ---- [6] optional disk reconciliation ----
    if args.pdf_dir:
        disk = {os.path.basename(p).lower() for p in glob.glob(os.path.join(args.pdf_dir, '*.pdf'))}
        wl_dois = set(doi_rows)
        missing = src_dois - wl_dois
        oa_on_disk = {d for d in missing if doi_to_filename(d).lower() in disk}
        unaccounted = sorted(missing - oa_on_disk)
        print(f"\n[6] disk reconciliation ({args.pdf_dir}): {len(disk)} PDFs on disk")
        print(f"      source DOIs {len(src_dois)} = worklist {len(src_dois & wl_dois)}"
              f" + OA-on-disk {len(oa_on_disk)} + unaccounted {len(unaccounted)}")
        for d in unaccounted:
            print(f"      UNACCOUNTED (in source, not on worklist, not on disk): {d}")

    if args.report:
        os.makedirs(os.path.dirname(args.report) or '.', exist_ok=True)
        with open(args.report, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=list(verdict[0].keys()))
            w.writeheader(); w.writerows(verdict)
        print(f"\nper-row verdict -> {args.report}")

    hard = bool(not_real or foreign or dup_dois or fname_bad)
    print("\n" + ("HARD FAILURES present -- fix before downloading." if hard
                  else "All hard checks passed."))
    sys.exit(1 if hard else 0)


if __name__ == '__main__':
    main()
