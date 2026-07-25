# SciKG — Work Status

**Generated:** 2026-07-25 · **Branch:** `veronika` @ `9071aa2` · **Author:** Veronika
**Method:** every graph figure below was measured by read-only Cypher against the live instance on
2026-07-25. Nothing here is copied forward from a prior document; where a document disagrees with the
live graph, both numbers are shown and the disagreement is flagged.

---

## 1. Graph — live measurement

**Instance:** `neo4j+s://bf9ce500.databases.neo4j.io` (Veronika's own; **not** the `3e16fe28`
production instance).

**Totals: 4,886 nodes / 11,690 edges.**

| Node label | Count |  | Relationship type | Count |
|---|---:|---|---|---:|
| Researcher | 2,062 |  | AUTHORED_BY | 5,026 |
| RawDataFile | 934 |  | USES_INSTRUMENT | 1,023 |
| Publication | 805 |  | DERIVED_FROM | 952 |
| Instrument | 443 |  | COLLECTED_ON | 934 |
| Dataset | 306 |  | ACQUIRED_WITH | 934 |
| Journal | 192 |  | CONDUCTED_AT | 818 |
| Institution | 62 |  | PUBLISHED_IN | 805 |
| Software | 51 |  | FUNDED_BY | 382 |
| Advisory | 21 |  | HAS_DATASET | 299 |
| Facility | 6 |  | USES_SOFTWARE | 267 |
| Sample | 3 |  | INVOLVES_INSTITUTION | 89 |
| Funder | 1 |  | OPERATED_BY | 46 |
| **Total** | **4,886** |  | CONTAINS_SAMPLE | 46 |
| | |  | FLAGS | 42 |
| | |  | SAME_AS | 27 |
| | |  | **Total** | **11,690** |

**Identity layer:**

| Measure | Live value |
|---|---|
| Researcher nodes | 2,062 |
| Year-suffixed identifiers (`researcher:*_20xx`) | **0** — new slug scheme fully in effect |
| ORCID-bearing Researcher nodes | **481** (23.3%) |
| — split | 192 author-verified (`true`) / 279 publisher-asserted (`false`) / 10 `null` |
| `SAME_AS` | **27** — 24 `human_review`, 2 `orcid`, 1 `surname_change` |
| `POSSIBLY_SAME_AS` | **0** — the type does not exist in the database (deliberate) |

**Integrity:** 0 self-loops · 0 nodes missing `identifier` · 0 nodes missing `source_type` ·
0 dangling edge endpoints · 0 duplicate edge triples · 0 quarantined.
6 nodes have degree 0 (unconnected) — noted, not diagnosed.

### Does it match the verified rebuild?

**Partly — and the difference is that this brief's baseline is one step stale, not that the graph is wrong.**

| Measure | Brief's stated baseline | Live | Verdict |
|---|---|---|---|
| Nodes | 4,886 | 4,886 | ✅ match |
| Edges | 11,666 | **11,690** | ⚠️ +24 |
| ORCID-bearing | 471 | **481** | ⚠️ +10 |
| `SAME_AS` | 3 | **27** | ⚠️ +24 |

All three gaps are **the same event**: the 2026-07-25 human-review equivalence emit, which added
24 `SAME_AS` edges (11,666 → 11,690) and set 10 Researcher `orcid` properties the reviewer found
(471 → 481). The live graph matches the **current** documented state in `CLAUDE.md` and
`docs/KNOWN_ISSUES.md` KI-17 **exactly**. The `4,886 / 11,666 / 471 / 3` figures describe the state
*before* that emit. No corrective action needed — the emit is committed, reviewed, and recorded.

### Rebuild status

The wipe-and-reload described in the earlier task brief **was not performed**, and did not need to be.
Pre-flight measured this instance as already carrying the post-fix state (2,062 Researcher, 0
year-suffixed ids, 481 ORCID, 27 `SAME_AS`), i.e. it does *not* predate the identifier fix. The local
validation artifact (`data/processed/validated/validation_report.json`, generated 2026-07-25T22:34:08Z)
reports **16,576 records passed, 0 quarantined, `load_cleared: true`**, consistent with the live graph.

### One observation on the flagship query

`MATCH (:Publication {identifier:'doi:10.1126/science.aaz5284'})-[:HAS_DATASET]->(d)` returns **two**
datasets, not one:

- `dataset:proteomexchange:pxd026123` — `llm_extraction`, confidence `medium` (the expected result) ✅
- `dataset:other:0516284a` — `csv`, confidence `high`, `source_id: maglab:16406`

The second is the PRIDE search-URL node that `CLAUDE.md` records as *held from the mint*. It is in the
graph from the **CSV** path, not from the mint, so this is not a mint leak — but any verification that
asserts this query returns a single row will read as a failure. Worth stating the expectation as
"includes `pxd026123`" rather than "returns `pxd026123`".

---

## 2. Pipeline

All stages present in `scripts/`:

| Stage | File | Status |
|---|---|---|
| 01 | `01_fetch.py` | present |
| 01b | `01b_fetch_pdfs.py` | present |
| 02 | `02_extract.py` | present |
| 02b | `02b_extract_csv.py` | present |
| 02c | `02c_extract_rawfiles.py` | present |
| 02d | `02d_extract_pdf.py` | present — under evaluation |
| 02f | `02f_extract_pxd_rawfiles.py` | present — local-only source, not runnable from a clean clone |
| 03 | `03_normalize.py` | present |
| 04 | `04_validate.py` | present — last run 0 quarantined, `load_cleared: true` |
| 05 | `05_load.py` | present — graph loaded |

Plus 22 supporting scripts (ORCID enrichment, dataset mint, PDF transforms, verification, RCC submit).

**Test suite — thin, and honestly so.** 7 files under `tests/`, but only 2 contain tests:

| File | Tests |
|---|---|
| `test_extract_csv.py` | 15 |
| `test_extract_rawfiles.py` | 14 |
| `test_extract.py`, `test_fetch.py`, `test_normalize.py`, `test_load.py`, `test_validate.py` | **0 — docstring stubs only** |

**29 tests total, covering 2 of 10 stages.** `03`, `04`, and `05` — including the normalization and
validation logic that the whole `graph = f(files)` guarantee rests on — have **no executable test
coverage**, only a docstring describing what the tests would check.

**The suite was not run for this report:** `pytest` is in `requirements.txt` but is not installed in
the active interpreter (Python 3.14.6; `neo4j`, `dotenv`, `requests`, `pandas` are installed).
Installing it is outside a read-only audit and outside the CLAUDE.md package rule. Status: **unknown /
not run**, not "passing".

---

## 3. Researcher track

| Item | Status |
|---|---|
| Identifier rebuild (KI-16 slug fix) | **done** — `researcher:{translit_family}_{initial}`, no year; 0 year-suffixed ids live; 2,076 → 2,062 (14 accent-collapse merges) |
| Equivalence review | **complete** — all 37 candidate pairs dispositioned |
| — confirmed SAME, emitted | **24** `SAME_AS`, `anchor_type='human_review'` |
| — HELD, awaiting second look | **1** — `researcher:angstrom_j` ↔ `researcher:anstrom_j` |
| — confirmed DIFFERENT, exclusion upheld | **11** — decided, not pending |
| ORCID-anchored equivalences | **3** — needed no review (2 `orcid`, 1 `surname_change`) |
| `researcher_equivalence_EMIT.md` | **consumed, not pending** — 27 records emitted and live |
| ORCID enrichment | **done** — 481 of 2,062 (23.3%); properties-only per the 2026-07-23 ruling |

**Note on the brief's framing:** "24 SAME_AS ready to emit … `researcher_equivalence_EMIT.md` ready"
describes a pre-emit state. **The emit already happened** (2026-07-25, commit `808f093`). The 24 edges
are live, `researcher_equivalence.jsonl` holds 27 records, and KI-17 is marked RESOLVED. There is no
pending emit action.

**Still open — the author-fusion parser item: `KI-18`.** The parser bugs that manufactured the
duplicate nodes are *not* fixed by the equivalence layer — `SAME_AS` records the identity, it does not
repair the string. KI-18 quantifies four parser-family defects in `Researcher.name_full`, including
comma-fusion where one node's name holds two people (3 nodes live, e.g. `researcher:rodgers_r` =
`'Rodgers, R.P., Weinheber, P.'`, where Weinheber has no node and no edge at all). **Deliberately
deferred**, not broken-and-unnoticed: repairing `name_full` in place would rewrite committed source
records and re-run the slug/survivor logic, which is exactly how identity churn gets introduced. The
fix belongs upstream in `02b` with a fresh identity pass.

---

## 4. Discovery questions

`docs/DISCOVERY_QUESTIONS.md` — 14 researcher-submitted questions, tags verified by Cypher on
2026-07-20 (v1.0).

| Tag | Count | Questions |
|---|---:|---|
| ✅ ANSWERABLE (as worded) | **0** | — |
| ◐ PARTIAL | **4** | Q4, Q7, Q8, Q14 |
| ○ FUTURE WORK | **10** | Q1, Q2, Q3, Q5, Q6, Q9, Q10, Q11, Q12, Q13 |

No question as worded is a clean ✅ — the document is explicit that each *bundles* a supported
capability with an unsupported one. The underlying **capabilities** split more favourably (16 tracked):

| | Count | Examples |
|---|---:|---|
| ✅ | **4** | co-authorship networks; instrument usage counts; software usage; full provenance chain |
| ◐ | **4** | fractionation methods; ion-activation types; *E. coli* metadata; institution co-publication |
| ○ | **8** | raw-file↔publication linkage; per-experiment parameters; DDA/DIA; citations; study-area tags; geography; non-NSF funders; comparison corpus |

⚠️ **This file carries a known-stale header.** It cites v1.0 as `4,909 nodes / 11,668 edges`. Live is
`4,886 / 11,690` — **23 nodes higher** than live. Tracked as `POSTER_FINDINGS.md` **T2**; the
instruction there is explicit: *do not overwrite the figure until the node gap is traced*. The edge gap
has flipped sign (our own +24 emit overtook it) and is **no longer evidence of drift** — only the node
gap is. This report does not touch that file.

---

## 5. Error-rate audit

**The brief's "Section 5 error-rate audit" does not resolve to a unique artifact.** There is no
document section by that name. Two things match the description, and they have opposite statuses — so
both are reported rather than guessing which was meant:

**(a) `docs/PDF_EXTRACTION_EVAL.md` — DONE, and it produced numbers.** Generated 2026-07-10 against the
8-paper ground-truth set (`docs/annotations/paper_reviews.md`) vs `pdf_extracted.jsonl`:

| Field | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| instrument | 6 | 15 | 5 | 0.29 | 0.55 | 0.37 |
| ionization_method | 8 | 7 | 16 | 0.53 | 0.33 | 0.41 |
| sample_type | 0 | 14 | 8 | 0.00 | 0.00 | 0.00 |
| facility | 2 | 1 | 7 | 0.67 | 0.22 | 0.33 |
| software_tools | 10 | 4 | 30 | 0.71 | 0.25 | 0.37 |
| dataset_accession | 2 | 1 | 1 | 0.67 | 0.67 | 0.67 |
| **MICRO TOTAL** | **28** | **42** | **67** | **0.40** | **0.29** | **0.34** |

Macro F1 **0.36**. This is a real, reproducible quality measurement on a small (8-paper) sample.

**(b) The fuzzy-grounding audit (`POSTER_FINDINGS.md` T1) — NOT DONE.** No audit pass was run over the
**297** fuzzy-grounded extractions (274 instrument + 23 facility), because that requires 297 PDF reads
and `data/processed/pdf_text/` does not exist to grep. KI-10 calls this "a poster limitation, not this
week's work."

**Consequence for the poster:** the reliability claim rests on *individual errors caught* (CAPABILITY 6),
not on a measured corpus-wide rate. **The poster may claim specific errors caught; it may not claim an
error rate** without stating sample size and confidence interval.

---

## 6. Known issues — open register

18 filed. **1 resolved, 1 resolved-with-tail, 16 open.**

| KI | Status | One line |
|---|---|---|
| KI-17 | **RESOLVED** 2026-07-25 | Researcher equivalences reviewed; 27 `SAME_AS` live, 1 pair held |
| KI-18 | open — deferred, quantified | Parser-family defects in `name_full` (comma-fusion etc.); fix belongs upstream in 02b |
| KI-16 | open — recorded as evidence | ORCID enrichment exposed 4 Researcher-identity defects, all rooted in the CSV name handling |
| KI-15 | **resolved for the confident subset** | PDF dataset accessions minted to `HAS_DATASET`; a held tail awaits David's rulings |
| KI-14 | open — needs a fix | `05_load.py` is MERGE-only and cannot shrink the graph; retirements leave stale data until a `--prune` exists |
| KI-13 | open — do not fix/promote | PDF facility + instrument transforms were never committed; re-extraction silently drops 524 nodes |
| KI-12 | open — ruled, target TBD | CSV and PDF assert the same fact in two files; three stages are blind to it |
| KI-11 | open — do not fix | A review-mention is not a use, and no field on disk distinguishes reviews from research |
| KI-10 | open — do not fix | LangExtract fuzzy alignment grounds a fabricated value onto unrelated text |
| KI-9 | open — do not fix | `Publication.publisher` is fetched to disk but never merged into the corpus |
| KI-8 | **header stale — see note** | 21 `sha256_hash` collisions in `rawfiles_pxd.jsonl` |
| KI-7 | open — needs a ruling | Instrument CV covers 34 aliases against 462 PDF-extracted instruments (+ KI-7a: one instrument, two identifiers) |
| KI-6 | open — do not fix | `instruments.jsonl` is 159 lines but only 7 instruments |
| KI-5 | open — fix upstream in 02d | 02d's grounded-only policy drops real extractions naming multiple tools |
| KI-4 | open — a bug, not a ruling | Vendor-strip swallows across a paren boundary, producing unbalanced tokens |
| KI-3 | open — needs a ruling | 3 instrument strings absent from the completed instrument field |
| KI-2 | open — needs a schema ruling | No reagent node type or inbox |
| KI-1 | open bug in 02f | Duplicate node lines + accession-blind edges for hash-identical cross-deposited files |

⚠️ **KI-8's header contradicts the rest of the repo.** It still reads *"Status: open — needs a ruling,
do not fix"* and *"A 05 blocker"*, but KI-8 was **remediated 2026-07-20** via the composite identity
`rawfile:{filename}:{sha16}` — as stated in `CLAUDE.md`, `README.md`, and
`validation_report.json` (`blockers.sha256_hash_collisions = []`, 21 byte-identical sets now recorded
as non-fatal `counted_categories`). The body text is stale, not the remediation. **Flagged, not
edited** — this report changes no file but its own.

---

## 7. Deliverables produced

**Documentation (`docs/`, 22 items):** `SCIKG_SCHEMA.md` (authoritative schema) ·
`KNOWN_ISSUES.md` (18 issues, the ticket home) · `POSTER_FINDINGS.md` (verified results + a TO-VERIFY
register) · `DISCOVERY_QUESTIONS.md` (14 researcher questions, Cypher-verified tags) ·
`VERIFIED_FACTS_AND_ASSUMPTIONS.md` · `FAIR_PRINCIPLES.md` · `METADATA_INVENTORY.md` · `ROADMAP.md` ·
`PDF_EXTRACTION_EVAL.md` · `pdf_transform_logic.md` · `controlled_vocabulary.md` ·
`researcher_equivalence_review.md` · `software_registry_review.md` · `REVIEW_LOG.md` ·
`LOAD_SETUP_CHECKLIST.md` · `method_field_handoff.md` · `poster_notes.md` · `annotations/` (ground
truth) · `metadata_templates/` · `doi_overrides.csv` · `vocab_stopwords.csv` ·
`05_load_readiness_report.txt`

**Review sheets & ledgers (`data/processed/review/`, 19 files):**

| File | Role |
|---|---|
| `researcher_equivalence_EMIT.md` | source of the 24 human-review `SAME_AS` edges (consumed) |
| `researcher_merge_ledger.jsonl` (104 KB) | merge evidence ledger |
| `researcher_merge_review.md`, `researcher_merge_13_humanread.md`, `researcher_review_queue.md` | merge review sheets |
| `coauthor_edge_fix_ledger.jsonl` (62 KB), `coauthor_edge_fix_review.md`, `coauthor_verification.md` | co-author edge-fix evidence |
| `orcid_coverage_report.md`, `orcid_candidates.jsonl` (478 KB), `orcid_exclusions.jsonl`, `proposed_researcher_orcid_entities.jsonl` (416 KB), `orcid_harvest_proposal.jsonl` | ORCID enrichment trail |
| `instrument_review.md` (97 KB), `software_review.md` (67 KB), `facility_institution_review.md` | vocabulary/dedup rulings |
| `dataset_review.md`, `approved_apply_scope.jsonl`, `approved_msv_mint_scope.jsonl` | dataset mint approvals |

**Graph:** 4,886 nodes / 11,690 edges in AuraDB, 0 quarantined, reproducible from committed files
(`03 → 04 → 05`).

---

## 8. Summary

The pipeline is complete end to end, the graph is loaded and clean (0 quarantined, 0 dangling, 0
self-loops), and the researcher identity track — rebuild, ORCID enrichment, and the equivalence layer —
is **finished, not pending**. The honest gaps are: **test coverage** (29 tests over 2 of 10 stages;
`03`/`04`/`05` untested), **no measured extraction error rate** on the full corpus (only an 8-paper
eval at F1 0.34), and **16 open KIs**, of which KI-14 (no `--prune`) and KI-13 (uncommitted PDF
transforms) are the two that can actually bite a future rebuild.
