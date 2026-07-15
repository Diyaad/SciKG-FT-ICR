#!/usr/bin/env python3
"""
repair_pdf_extracted_dois.py -- normalize the DOI key in pdf_extracted.jsonl.

WHY:
  02d writes the real DOI when it resolves a CrossRef record, and falls back to
  the filename stem when it doesn't. The 378-paper run produced 326 records keyed
  '10.1002/aic.15147' and 52 keyed '10_1002_2016JG003431' (the open-access papers
  01b fetched, which were never on the worklist).

  03_normalize.py joins on this key. The 52 stem-keyed records would silently
  fail to match anything CrossRef-derived -- no error, just 52 papers missing
  from the graph.

HOW:
  This is a LOOKUP, not an un-mangling heuristic. You cannot tell which '_' in a
  stem was a '.' and which was a '/'. But every PDF on disk was named by
  doi_to_filename(doi) from a DOI in maglab_icr_publications.csv, so we invert
  that exact map. Anything that doesn't resolve is REPORTED, never guessed.

PROVENANCE:
  Writes a NEW file; the input is untouched. Repaired records carry
  'doi_repaired_from' recording the original stem, so the change is auditable
  and nothing is silently rewritten.

USAGE:
  python scripts/repair_pdf_extracted_dois.py \
      --in  data/processed/entities/pdf_extracted.jsonl \
      --source data/raw/maglab_icr_publications.csv \
      --out data/processed/entities/pdf_extracted_fixed.jsonl

  Exits nonzero if any stem fails to resolve -- fix those before handing off.
"""

import argparse, csv, json, re, sys
from collections import defaultdict

WELLFORMED_DOI = re.compile(r'^10\.\d{4,9}/\S+$')


def norm_doi(s):
    """Strip doi.org wrappers. Does NOT lowercase -- DOI suffixes are
    case-preserving on disk (10.1002/2016JG003431 -> 10_1002_2016JG003431),
    and lowercasing here silently breaks the stem lookup."""
    s = (s or '').strip()
    for pre in ('https://doi.org/', 'http://doi.org/', 'doi.org/'):
        if s.lower().startswith(pre):
            s = s[len(pre):]
            break
    return s.rstrip('/')


def doi_to_stem(d):
    """The exact naming rule used for the PDFs on disk."""
    return d.replace('.', '_').replace('/', '_')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--source', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--overrides', default='',
                    help='optional CSV: stem,doi,reason,verified_by -- for stems '
                         'the source cannot resolve (misnamed files, URL/blank '
                         'DOI cells). Hand-verified only, never guessed.')
    ap.add_argument('--doi-col', default='Digital Object Identifier')
    args = ap.parse_args()

    # --- build stem -> real DOI from the supervisor's list ---
    # key on the lowercased stem so lookup is case-insensitive, but STORE the
    # original-case DOI -- that's what CrossRef and 03_normalize expect.
    stem_map = defaultdict(set)
    with open(args.source, newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            d = norm_doi(r.get(args.doi_col, ''))
            if WELLFORMED_DOI.match(d):
                stem_map[doi_to_stem(d).lower()].add(d)

    # a stem that maps to 2+ distinct DOIs is ambiguous -- refuse to pick
    ambiguous = {s: v for s, v in stem_map.items() if len(v) > 1}
    lookup = {s: next(iter(v)) for s, v in stem_map.items() if len(v) == 1}
    print(f"source: {len(lookup)} unambiguous stems"
          + (f", {len(ambiguous)} AMBIGUOUS (skipped)" if ambiguous else ""))
    for s, v in ambiguous.items():
        print(f"   AMBIGUOUS stem {s} -> {sorted(v)}")

    # --- hand-verified overrides (applied only where the source cannot resolve) ---
    overrides = {}
    if args.overrides:
        with open(args.overrides, newline='', encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                s = (r.get('stem') or '').strip()
                d = norm_doi(r.get('doi', ''))
                if s and WELLFORMED_DOI.match(d):
                    overrides[s.lower()] = (d, (r.get('verified_by') or '').strip())
                elif s:
                    print(f"   BAD OVERRIDE (not a well-formed DOI): {s} -> {r.get('doi')!r}")
        print(f"overrides: {len(overrides)} loaded from {args.overrides}")

    # --- repair ---
    repaired, already_ok, unresolved = 0, 0, []
    from_override = 0
    out_lines = []
    with open(args.inp, encoding='utf-8') as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            d = rec.get('doi', '')
            if '/' in d:
                already_ok += 1
            else:
                real = lookup.get(d.lower())
                src_tag = 'source_csv'
                if not real and d.lower() in overrides:
                    real, src_tag = overrides[d.lower()][0], overrides[d.lower()][1]
                    from_override += 1
                if real:
                    rec['doi_repaired_from'] = d
                    rec['doi_repair_source'] = src_tag
                    rec['doi'] = real
                    repaired += 1
                else:
                    unresolved.append((ln, d))
            out_lines.append(json.dumps(rec, ensure_ascii=False))

    with open(args.out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_lines) + '\n')

    print(f"\nrecords:      {len(out_lines)}")
    print(f"  already DOI-keyed: {already_ok}")
    print(f"  repaired:          {repaired}  ({repaired - from_override} via source, {from_override} via overrides)")
    print(f"  UNRESOLVED:        {len(unresolved)}")
    for ln, d in unresolved:
        print(f"     line {ln}: {d!r}")

    # --- post-condition: every key must now be a well-formed DOI, no dups ---
    keys = [json.loads(l)['doi'] for l in out_lines]
    bad = [k for k in keys if not WELLFORMED_DOI.match(k)]
    dups = {k for k in keys if keys.count(k) > 1}
    print(f"\npost-check: {len(keys)} keys, {len(bad)} malformed, {len(dups)} duplicated")
    for k in sorted(dups):
        print(f"   DUPLICATE KEY: {k}")

    print(f"\nwrote {args.out}")
    if unresolved or bad or dups:
        print("NOT clean -- do not hand off until resolved.")
        sys.exit(1)
    print("clean -- safe to hand to 03_normalize.")


if __name__ == '__main__':
    main()
