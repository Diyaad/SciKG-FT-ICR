#!/usr/bin/env python3
"""
build_vocabulary.py -- generate the PDF vocabulary + provenance files from
02d's extraction output.

GROUNDED ONLY. Every string emitted here appeared verbatim in a source PDF
(LangExtract returned a char_span that aligned to the text). Ungrounded values
are model output with no textual anchor -- they are counted and reported, but
never enter the vocabulary, because an unanchored value cannot be traced to
evidence and has no place in a provenance-aware graph.

Outputs:
  vocabulary_v<N>_<M>papers.txt   -- human-readable, per-field, count-sorted
  vocabulary_provenance_<M>papers.csv -- field,value,source_doi,source_pdf,char_span

Usage:
  python scripts/build_vocabulary.py \
      --in data/processed/entities/pdf_extracted_fixed.jsonl \
      --version 3 \
      --outdir data/processed/vocab
"""

import argparse, csv, json, os, re
from collections import Counter, defaultdict

# The fields 02d is *asked* to extract. Anything else the model returns is an
# invented extraction class -- reported separately, never silently mixed in.
TARGET_FIELDS = ["instrument", "ionization_method", "sample_type",
                 "facility", "software_tools", "dataset_accession"]


def doi_to_stem(d):
    return d.replace('.', '_').replace('/', '_')


def source_pdf_for(rec):
    """The filename actually on disk. For repaired records the file still
    carries the original stem, so use that -- not the corrected DOI."""
    if rec.get('doi_repaired_from'):
        return rec['doi_repaired_from'] + '.pdf'
    return doi_to_stem(rec['doi']) + '.pdf'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--version', type=int, required=True)
    ap.add_argument('--outdir', default='.')
    ap.add_argument('--stopwords', default='',
                    help='optional CSV (term,reason). When given, ALSO writes a '
                         '_filtered vocabulary with these terms and pure-numeric '
                         'values omitted. The raw vocabulary is always written '
                         'and is never altered -- it is the evidence record.')
    ap.add_argument('--note', default='', help='extra line for the file header')
    args = ap.parse_args()

    recs = [json.loads(l) for l in open(args.inp, encoding='utf-8') if l.strip()]
    n_papers = len(recs)
    os.makedirs(args.outdir, exist_ok=True)

    vocab = defaultdict(Counter)          # field -> Counter(value)
    prov_rows = []
    ungrounded = Counter()
    totals = Counter()
    offtarget = []

    for rec in recs:
        doi = rec['doi']
        pdf = source_pdf_for(rec)
        for e in rec.get('all_field_extractions', []):
            f = e.get('field')
            v = (e.get('value') or '').strip()
            totals[f] += 1
            if f not in TARGET_FIELDS:
                offtarget.append((doi, f, v, e.get('grounded')))
                continue
            if not e.get('grounded'):
                ungrounded[f] += 1
                continue
            if not v:
                continue
            vocab[f][v] += 1
            prov_rows.append({
                'field': f, 'value': v, 'source_doi': doi,
                'source_pdf': pdf, 'char_span': json.dumps(e.get('char_span')),
            })

    # --- vocabulary txt ---
    vpath = os.path.join(args.outdir, f'vocabulary_v{args.version}_{n_papers}papers.txt')
    with open(vpath, 'w', encoding='utf-8') as f:
        f.write(f'SciKG PDF vocabulary v{args.version} - GROUNDED only ({n_papers} papers)\n')
        f.write('Every string appears verbatim in a source PDF. Counts = number of occurrences.\n')
        if args.note:
            f.write(args.note.rstrip() + '\n')
        f.write('NOTE: raw surface forms - some OCR artifacts / fragments, needs a cleaning pass.\n')
        f.write('Ungrounded model output is EXCLUDED (see the grounding summary at the end).\n')
        for field in TARGET_FIELDS:
            c = vocab[field]
            f.write(f'\n=== {field} ({len(c)} distinct) ===\n')
            for val, n in sorted(c.items(), key=lambda x: (-x[1], x[0].lower())):
                f.write(f'  x{n}  {val}\n')

        f.write('\n\n=== grounding summary (why values were dropped) ===\n')
        f.write(f'{"field":22} {"grounded":>9} {"ungrounded":>11} {"total":>7}  {"kept%":>6}\n')
        for field in TARGET_FIELDS:
            g = sum(vocab[field].values())
            u = ungrounded[field]
            t = totals[field]
            f.write(f'{field:22} {g:>9} {u:>11} {t:>7}  {(g/t*100 if t else 0):>5.0f}%\n')
        gt = sum(sum(vocab[x].values()) for x in TARGET_FIELDS)
        tt = sum(totals[x] for x in TARGET_FIELDS)
        f.write(f'{"TOTAL":22} {gt:>9} {tt-gt:>11} {tt:>7}  {(gt/tt*100 if tt else 0):>5.0f}%\n')

        if offtarget:
            f.write('\n=== off-target extraction classes (NOT in TARGET_FIELDS) ===\n')
            f.write('The model invented these field names. Excluded from the vocabulary.\n')
            for doi, fld, val, gr in offtarget:
                f.write(f'  {doi}\n    field={fld!r}\n    value={val!r}  grounded={gr}\n')

    # --- provenance csv ---
    ppath = os.path.join(args.outdir, f'vocabulary_provenance_{n_papers}papers.csv')
    with open(ppath, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=['field', 'value', 'source_doi',
                                          'source_pdf', 'char_span'])
        w.writeheader()
        w.writerows(prov_rows)

    # --- optional filtered vocabulary (SEPARATE file; raw is never altered) ---
    if args.stopwords:
        stop, reasons = set(), {}
        with open(args.stopwords, newline='', encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                t = (r.get('term') or '').strip()
                if t:
                    stop.add(t.lower())
                    reasons[t.lower()] = (r.get('reason') or '').strip()

        def is_junk(v):
            s = v.strip()
            if s.lower() in stop:
                return 'stopword'
            if len(s) < 2:
                return 'too short'
            if re.fullmatch(r'[\d\s.,;:%+\-/()]+', s):
                return 'numeric/punctuation only'
            return None

        fpath = os.path.join(args.outdir,
                             f'vocabulary_v{args.version}_{n_papers}papers_filtered.txt')
        dropped = Counter()
        drop_log = []
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(f'SciKG PDF vocabulary v{args.version} - GROUNDED + FILTERED ({n_papers} papers)\n')
            f.write('Derived from the raw vocabulary by OMITTING junk terms. Nothing is\n')
            f.write('altered: every surviving string still appears verbatim in a source PDF\n')
            f.write('at its recorded char_span. The raw file remains the evidence record.\n')
            f.write(f'Stopword list: {os.path.basename(args.stopwords)} (extend it as needed).\n')
            f.write('Junk = stopword match, <2 chars, or numeric/punctuation only.\n')
            for field in TARGET_FIELDS:
                kept = {v: n for v, n in vocab[field].items() if not is_junk(v)}
                for v, n in vocab[field].items():
                    why = is_junk(v)
                    if why:
                        dropped[field] += 1
                        drop_log.append((field, v, n, why))
                f.write(f'\n=== {field} ({len(kept)} distinct) ===\n')
                for val, n in sorted(kept.items(), key=lambda x: (-x[1], x[0].lower())):
                    f.write(f'  x{n}  {val}\n')
            f.write('\n\n=== omitted as junk (audit) ===\n')
            for field, v, n, why in sorted(drop_log):
                f.write(f'  {field:20} x{n:<4} {v!r}   [{why}]\n')

        print(f'\nfiltered vocabulary: dropped {sum(dropped.values())} distinct values')
        for field in TARGET_FIELDS:
            if dropped[field]:
                print(f'  {field:20} -{dropped[field]}')
        print(f'wrote {fpath}')

    print(f'papers: {n_papers}')
    for field in TARGET_FIELDS:
        print(f'  {field:20} {len(vocab[field]):>5} distinct  '
              f'({sum(vocab[field].values())} grounded / {totals[field]} total)')
    print(f'\nprovenance rows: {len(prov_rows)}')
    print(f'off-target classes: {len(offtarget)}')
    print(f'\nwrote {vpath}')
    print(f'wrote {ppath}')


if __name__ == '__main__':
    main()
