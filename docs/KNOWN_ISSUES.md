# SciKG — Known Issues

Real issues found and ruled out of the current scope, kept visible so they aren't rediscovered
or silently lost. `gh` is not installed in this environment; this file is the ticket home.
Each entry states what it is, how it was measured, and whether it needs a ruling or a fix.
Add new issues at the top.

---

## KI-15 — PDF-extracted dataset_accession was never linked to HAS_DATASET (the C4 gap) — RESOLVED for the confident subset by a human-gated mint
**Status:** resolved for the confident subset (2026-07-22); a held tail awaits David's rulings.
**Surfaced by:** the C4 dropped-field audit + the dataset-identity review (Blood Proteoform Atlas fragmentation), 2026-07-21.

02d extracts a `dataset_accession` per paper (5 corpus papers name a PXD/MSV accession in their
PDF), but the pipeline **never turned it into a HAS_DATASET edge** — datasets came only from the
CSV `Data Set Urls`. So a paper could cite a deposit that already exists as a node and stay
unlinked: e.g. the Blood Proteoform Atlas paper `doi:10.1126/science.aaz5284` cites `PXD026123`,
a loaded `dataset:proteomexchange:pxd026123` node, with **no edge between them**.

**Resolved** by `scripts/mint_dataset_operator_edges.py` — a human-gated post-load reconciliation
(2026-07-22). It proposes edges for review (dataset accessions carry fuzzy/hallucinated values —
wrong-repo, mis-OCR'd, or invented — so 02d stays fabrication-free and the human gate lives
here, not in extraction). On approval, `--emit` writes the approved records to PRE-NORMALIZE
JSONL, which flow through 03 -> 04 -> 05 like any other extracted record, so **graph = f(files)**
still holds — **proven by a files-only rebuild into an empty Neo4j instance reproducing the
counts**. First application: **11 HAS_DATASET edges = 3 link (accession matched an existing
Dataset node) + 8 mint (new Dataset node + edge)** — Dataset 289 -> 297, HAS_DATASET 279 -> 290,
totals 4,883/11,643 -> 4,891/11,654.

**MSV native accessions — RESOLVED 2026-07-22.** After a MassIVE lookup paired each `MSV000*`
with its `10.25345/` DOI and confirmed no in-graph twin, **3 minted** as `dataset:massive:{msv}`
(MSV000094542 -> mcpro.2024.100814, MSV000094385 -> orggeochem.2024.104880, MSV000095816 ->
jasms.4c00380), each carrying its paired DOI in the evidence_note for a future MSV<->DOI
crosswalk. **1 held** — MSV000085978 (jproteome.0c00403), a known duplicate of the existing
`dataset:other:10.25345/c54n1p`. Emitted through the same durable path (Dataset 297 -> 300,
HAS_DATASET 290 -> 293, totals 4,891/11,654 -> 4,894/11,657; read back from Neo4j, load_cleared,
0 quarantined).

**Still HELD (NOT minted — await David's ruling):**
- **MSV000085978** — held as a duplicate of `dataset:other:10.25345/c54n1p` (same submission,
  two accession schemes); reconcile via crosswalk, do not mint a second node.
- **New-namespace deposits** (SRA / BioProject / BCO-DMO) — no repository handler yet.
- **PXD026178** — cited in a PDF but has no raw-file lineage in the graph.
- **`other:0516284a`** — the PRIDE search-URL node (candidate to fold into the Blood Proteoform
  Atlas PXD set).
- **Raw-file operators** — intentionally unmodeled: FOXDEN metadata carries no reliable person
  identity, so no OPERATED_BY is minted for PXD files (distinct from the 46 MagLab RAW files,
  which genuinely are all D.S. Butcher and ARE linked).

---

## KI-14 — 05_load.py is MERGE-only and cannot shrink the graph (node/edge retirements leave stale data)
**Status:** open — needs a fix (a `--prune` step); worked around manually on 2026-07-21.
**Surfaced by:** the instrument dedup load (typo merges + FT-ICR generic collapse + Velos split), 2026-07-21.

`05_load.py` loads with idempotent `MERGE`, which only creates-or-matches. It has **no delete
path**, so when a pipeline run *retires* nodes or reassigns edges, the old ones **remain in
Neo4j**. Measured after the 2026-07-21 instrument reload: `validated/` held 443 Instruments /
1023 USES_INSTRUMENT, but the graph showed **472 / 1108** — 29 stale retired Instrument nodes
plus 85 stale edges (84 pointing to the retired nodes, 1 reassigned-away edge lingering on a
kept node, `doi:10.1007/s13361-019-02290-8 -> velos_pro_linear_ion_trap`).

**Worked around** by a targeted reconcile (Option A): `DETACH DELETE` the Instrument nodes not
in `validated/`, plus `DELETE` the one lingering edge — 30 deletes, after which the graph
matched `validated/` exactly (443 / 1023 / 4883 nodes / 11643 edges, all acceptance checks pass).

**The fix:** add a `--prune` mode to `05_load.py` that, after the MERGE load, deletes any graph
node/edge absent from `validated/`, so the graph becomes a true *projection* of `validated/`
and future dedups don't strand data. Diff-and-delete keyed on the validated identifier set (the
manual reconcile above is the reference implementation). **Do not build yet** (deferred by the
operator 2026-07-21); dry-run it first when built. Until then, any pipeline run that shrinks a
node set needs the manual reconcile as a follow-up, or the graph silently over-reports.

---

## KI-13 — the PDF facility and instrument transforms were never committed (producers now confirmed from their runs' pickles)
**Status:** open — **do not fix, do not promote, do not rewrite** (filed 2026-07-17; **rewritten 2026-07-17** after recovery)
**Surfaced by:** the D1 CLAUDE.md pipeline-block audit, 2026-07-17.

**Correction — the original filing was wrong.** It claimed these nodes *"cannot be regenerated by
anyone, ever."* **That is FALSE and has been removed.** The transform code survives, and both
producers are now **confirmed from the pickles their own runs wrote** (see Method). The real issue
was never reproducibility — it is **regeneration** (see The real risk).

**What's committed at `bf97881`** — 62 Institution + 89 INVOLVES_INSTITUTION + 462 PDF Instrument +
968 USES_INSTRUMENT — was produced by transforms that were **never added to `scripts/`; they lived
in session scratch.** (The other 7 of the 469 Instrument nodes are the raw-form 02c/02f ones, which
*do* have committed producers.)

**The scratch is recovered** to **`~/scikg-scratch-all`** (outside the repo, outside `/private/tmp`
— which sweeps at ~3 days and these are Jul 14/15). Session `18b6037e` holds `finalize.py`,
`finalize_inst.py`, `resolver.py`, `inst_classify.py`, `inst_v2.py`, and the two pickles below.

**Facility — CONFIRMED producer: `finalize.py`.** Its committed 62 Institution + 89
INVOLVES_INSTITUTION match `_finalize.pkl` (the pickle its own run wrote, `finalize.py:169`) by
**exact identifier set**. Note the shape: **62 = 21 existing + 41 new** — `finalize.py` ran
**incrementally against an earlier base**, not from scratch.

**Instrument — CONFIRMED producer: `finalize_inst.py`, modulo one node's slug.** Its committed 462
Instrument + 968 USES_INSTRUMENT match `_inst_final.pkl` (`finalize_inst.py:122`) on **461/462 nodes
and 962/968 edges** by identity. The one difference:
`instrument:raw:velos_ltq_orbitrap_mass_spectrometer` (pickle) vs
`instrument:raw:ltq_velos_ion_trap_mass_spectrometer` (committed) — **same instrument, two slugs**,
and the 6 differing USES_INSTRUMENT edges are the 6 papers citing it. This is the **same
one-box-two-identifiers phenomenon as KI-7a**, not a different producer. **The committed slug is the
one that canonicalizes against the CV** (verified: `ltq_velos_ion_trap_mass_spectrometer` → `LTQ
Orbitrap Velos`, `MS:1001742`; the pickle slug is not on disk).

**Method (it matters):** established by **loading the pickles the original runs wrote and comparing
identifier sets — NOT by re-running the scripts.** Re-running was **considered and rejected**: these
transforms read the existing `pdf_entities.jsonl` as their base, and the July-era base they ran
against no longer exists, so an exact re-run **may be impossible in principle**. A pickle from the
run that wrote the file is better evidence than a re-run against a reconstructed base.

**The real risk — NOT reproducibility, REGENERATION.** `pdf_entities.jsonl` is committed, so a clean
clone has all **524** nodes (62 + 462) and the graph works. The danger is what happens on a
**re-extraction**: `scripts/transform_pdf_software.py` **reads** `pdf_entities.jsonl` rather than
creating it, so **re-running the PDF transform after a new extraction produces Software only,
silently, with no error — and the 524 Institution/Instrument nodes vanish.** **Anyone re-running
extractions must know this before they do.**

**Open — promotion is not a copy.** The scripts are not in `scripts/` and are **not promoted**. The
static audit (S1) found their write paths funnel through **per-module `BASE`/`REPO` literals** (each
dependency redeclares `BASE`), and **`inst_v2` does repo I/O at import time with no `__main__`
guard** — so promoting them requires **fixing the path handling, not just copying the files.**
Recorded; **not fixed.**

## KI-12 — CSV and PDF agree on the same fact across two files; three stages are blind to it
**Status:** open — **ruled: merge to one edge (E1); where TBD** (filed 2026-07-17)
**Surfaced by:** a manual 05 pre-flight measurement (P1), 2026-07-17 — **not by any pipeline check.**

**The finding (measured).** **74 `USES_INSTRUMENT` triples appear in two relationship files at
once** — the MagLab CSV (`csv_relationships.jsonl`, `source_type: csv`, `source_id: maglab:{id}`,
`confidence: high`) and the PDF extraction (`pdf_relationships.jsonl`, `source_type:
llm_extraction`, `source_id: doi:{...}`, `confidence: medium`). **All 74 point at the same object,
`instrument:raw:21t_icr`, across 74 distinct papers.** It is the **only** cross-file triple in the
graph — no other relationship type does it (COLLECTED_ON, DERIVED_FROM, etc. are single-source).
The two copies differ only in the six provenance fields; the edge `properties` are empty.

**Three stages, each individually correct, each blind — the shape 04 exists to catch:**
- **03 can't see it** — it dedups edges on `(type, subject, object[, properties])` **within a
  file**; these live in two files, so its key never collides (same class as KI-6).
- **04 couldn't see it** — it had no edge-duplicate check; its uniqueness (R7) is per-identifier
  on *nodes* only. **Fixed 2026-07-17 (E2):** 04 now counts `duplicate_edge_triple` (74, all
  `USES_INSTRUMENT`) as a NON-fatal category — a duplicate triple is a fact to decide about, not a
  malformed record.
- **05 would have destroyed it** — `MERGE (a)-[:USES_INSTRUMENT]->(b)` matches on `(a, type, b)`
  alone, collapsing each pair to one edge, `SET r += props` last-wins, **one source's provenance
  gone silently, load "succeeds."**

This is the **third bug of this exact shape** — after the endpoint-universe check (R10) and the
sha256 MERGE-key trap (L2/KI-8). All three look correct in isolation and fail silently; catching
them is why 04 exists.

**The ruling (E1) — follow `merged_csv_foxden`'s precedent.** Merge the pair to **one**
`USES_INSTRUMENT` edge: `source_type: merged_csv_llm`, **both** `source_id`s
(`[maglab:{id}, doi:{...}]`), `confidence: high` (two independent sources agreeing is stronger than
either), `evidence_note` quoting both. One paper using the 21 T is **one fact confirmed twice**,
not two facts. Enum added to `SCIKG_SCHEMA.md`. **Where the merge runs (03 cross-file pass vs 05
load-time vs 05-only) is an open recommendation — not yet implemented.**

**Positive finding, recorded deliberately:** these 74 are **74 papers where two independent
sources — a curated CSV and an LLM PDF extraction — agree the paper used the 21 T.** That is
**cross-source corroboration, the strongest evidence in the graph.** The bug is only that the
pipeline would have thrown the corroboration away; the agreement itself is a feature worth keeping
(and is exactly why `confidence: high`).

## KI-11 — a review-mention is not a use, and NO field on disk can tell reviews from research
**Status:** open — **do not fix** (filed 2026-07-17)
**Surfaced by:** Veronika's registry review, 2026-07-17 (MetaMorpheus + Proteoform Suite on a review).
**Sibling of KI-10:** KI-10 invents a value the paper never contains; KI-11 attaches a **real**
value (the tool IS named) to a paper that **names but never ran it**. Both put a false
`USES_SOFTWARE` edge in the graph; the mechanisms are different.

**The two confirmed instances.** `10.1002/pmic.201800361` is a **review**. It names
**MetaMorpheus** and **Proteoform Suite**; the extraction faithfully grounded both (they are in the
text), and both minted `USES_SOFTWARE` edges. But the review did not *run* either tool, so both
edges asserted a use that never happened. **Both edges removed 2026-07-17** (Veronika). They were
found **only because a human read the paper** — see below for why that does not scale.

**Why it can't be found systematically — measured 2026-07-17:**
`Publication.resource_type` holds exactly one value across all 805 publications:

| resource_type | count |
|---|---:|
| `JournalArticle` | 805 |

There is **no other value** — no `Review`, no `review-article`, nothing. So **no field on disk
distinguishes a review from a research article**, and the "named-but-not-run" class cannot be
filtered for. The exposure is not confined to software: the same `USES_INSTRUMENT` /
`INVOLVES_INSTITUTION` / `CONDUCTED_AT` edges are minted from the **same** PDF extraction over the
**same** undistinguished review articles, and **instrument (469 nodes) and facility (62)** are
already shipped and committed.

**Consequence:** the only detection is a human reading each paper. There is no queryable signal to
enumerate the others. **Reported, not fixed** — a fix would need a review/research discriminator
(e.g. a CrossRef `type` field), which the corpus does not carry. Recorded as a **poster
limitation**.

## KI-10 — LangExtract fuzzy alignment grounds a FABRICATED value onto unrelated text (the INVERSE of KI-5)
**Status:** open — **do not fix, do not change the threshold** (filed 2026-07-17)
**Surfaced by:** Veronika's registry review, 2026-07-17 (the MaxQuant edge on `10.1002/... jasms.4c00232`).
**This is the worst class found.** It **invents data** and the pipeline **cannot detect it** — it
violates CLAUDE.md's non-negotiable rule (*never fabricate metadata not present in the source*).

**The confirmed instance.** For `10.1021/jasms.4c00232`, 02d emitted `software_tools` naming
**MaxQuant**. Veronika read the PDF: **the paper never mentions MaxQuant.** Measured:
`value='MaxQuant v1.6'` (13 chars), `char_span=[4899,4907]` (8 chars), `alignment_status=MATCH_FUZZY`,
`grounded=True`. LangExtract **fuzzy-matched a fabricated value onto unrelated text**, and
`02d_extract_pdf.py::_is_grounded()` accepted it **with no coverage check at all** (see below).

### Mechanism — corrected 2026-07-17: there is NO guard, not a blind guard
The originally-filed framing (*"8/13 = 0.62 clears `MIN_SPAN_COVERAGE`"*) was **wrong**.
`MATCH_FUZZY` is in `ACCEPTED_ALIGNMENTS`, and `_is_grounded` returns `True` for it **before any
coverage arithmetic runs**. The `MIN_SPAN_COVERAGE` (0.55) check lives **only** in the `else`
branch — for `MATCH_LESSER` and unrecognised statuses. Verbatim (`scripts/02d_extract_pdf.py`):

```python
ACCEPTED_ALIGNMENTS = ("MATCH_EXACT", "MATCH_FUZZY")
MIN_SPAN_COVERAGE = 0.55

def _is_grounded(ex, char):
    if char is None:
        return False
    status = str(getattr(ex, "alignment_status", "") or "")
    if any(status.endswith(s) for s in ACCEPTED_ALIGNMENTS):
        return True                      # <-- MATCH_FUZZY returns here; NO coverage check
    # MATCH_LESSER and anything unrecognised: require the aligned span to
    # cover most of the value, so a one-word overlap cannot ground a long
    # fabricated string.
    value_len = len(ex.extraction_text or "")
    span_len = max(0, char.end_pos - char.start_pos)
    return value_len > 0 and (span_len / value_len) >= MIN_SPAN_COVERAGE
```

So the coverage threshold **never applies to the 1,057 `MATCH_FUZZY` extractions** — they are
accepted outright. That makes KI-10 **worse than filed**: not a blind spot in a guard, but the
**absence of any guard** for every fuzzy alignment. KI-5 is the *opposite* failure of the *same*
`_is_grounded`: the coverage check (the `else` branch) drops real `MATCH_LESSER` values for being
complete.

| | KI-5 | KI-10 |
|---|---|---|
| alignment | `MATCH_LESSER` → coverage checked | `MATCH_FUZZY` → **accepted, no check** |
| failure | coverage check drops a **real** value | no check runs; grounds a **fabricated** value |
| effect | **loses** data | **invents** data |
| detectable downstream? | yes (empty/short value visible) | **no** — reads as a normal grounded extraction |

**KI-10 is worse than KI-5:** lost data can be recovered upstream; invented data enters the graph
indistinguishable from a real extraction and violates the non-negotiable rule.

### Blast radius (measured 2026-07-17, `data/raw/pdf_extraction/pdf_extraction_378papers.jsonl`, `all_field_extractions`)
**`alignment_status=MATCH_FUZZY` AND `grounded=True`, by field:**

| field | fuzzy+grounded |
|---|---:|
| sample_type | 416 |
| ionization_method | 300 |
| **instrument** | **274** |
| software_tools | 39 |
| **facility** | **23** |
| dataset_accession | 5 |
| **TOTAL** | **1057** |

By alignment type, `grounded=True`: `MATCH_EXACT` 3811 · **`MATCH_FUZZY` 1057** · `MATCH_LESSER` 195.
(Every `MATCH_FUZZY` entry in the file — all 1057 — is `grounded=True`.)

**instrument (469 shipped nodes) and facility (62 shipped nodes) are both in the blast radius**
(274 and 23 fuzzy-grounded extractions). These fields already loaded, so the fabrication class is
not confined to software. This is a **count of exposure, not of confirmed fabrications** — each
would need a PDF read like the MaxQuant one; 1057 is the population to audit, not 1057 known-bad.

### Node-level fallout — ONLY MaxQuant; the review class does NOT corrupt node provenance (W2, corrected X1 2026-07-17)
This is a **KI-10-only** problem. `software:maxquant`'s `source_id` points at a paper that does not
contain the string, so its `evidence_note` *"grounded verbatim in article text"* was **false**:

| node | `source_id` on disk | node provenance |
|---|---|---|
| `software:maxquant` | `doi:10.1021/jasms.4c00232` | **FALSE** — paper never mentions MaxQuant (the fabrication) |

**MetaMorpheus is NOT in this table (X1 ruling).** Its `source_id` `doi:10.1002/pmic.201800361`
**does** name MetaMorpheus verbatim in the text, so the node's provenance is **accurate**. The
review-article class (**KI-11**) corrupts the `USES_SOFTWARE` **edge** (*"named" ≠ "used"*), which
is already removed — it does **not** touch node provenance. The node is fine.

**Fix applied to MaxQuant (X2 ruling, 2026-07-17):** the `evidence_note` was rewritten — `source_id`
left as-is (repointing to `str.2017.08.002` would assert provenance we never derived, since that
paper's token never resolved) — to record what actually happened: 02d grounded the value via
`MATCH_FUZZY`; a human PDF read found no mention. A false claim becomes a true record of a known
problem.

### Why the orphans exist — the real edges were BLOCKED upstream (W3, 2026-07-17)
Each node has a **real** corpus use that never minted an edge, so the false edge was its only one:

| node | real use (paper) | verbatim token | why no edge |
|---|---|---|---|
| MaxQuant | `10.1016/j.str.2017.08.002` | `MaxQuant software at standard settings` | descriptor-strip removes `software`; **`at standard settings` is trailing prose no rule strips** → never canonicalises to `MaxQuant` |
| MetaMorpheus | `10.1021/acs.jproteome.0c00403` | `MetaMorpheus 26` | **`26` is a trailing reference; the trailing-ref strip is UNBUILT (D2, §9.5 step 1)** → never matches `MetaMorpheus` |

So the trailing-ref strip that **D2 ruled UNBUILT as "4 cosmetic tokens"** now costs MetaMorpheus
its **only true edge** — the same shape as the step-4.5 residue, also "4 cosmetic tokens" until it
cost a node. **Recorded, not re-ruled** (do not re-rule D2).

### Ruling + action (2026-07-17, Diya)
- **The orphan nodes STAY.** Both are real tools with real corpus uses; deleting a correct node to
  tidy a count would be deleting data. `software:maxquant` (`has_id`) and `software:metamorpheus`
  (`proposed`) remain, edgeless.
- The one confirmed fabrication edge (MaxQuant→`jasms.4c00232`) is removed; the two review edges
  (KI-11) are removed. **Threshold untouched. 02d not run.**
- **NO audit pass** on the 274 instrument + 23 facility fuzzy-grounded extractions: that is **297
  PDF reads, and `data/processed/pdf_text/` does not exist to grep.** The exposure number is
  recorded; this is a **poster limitation, not this week's work.**
- The real fix is upstream in 02d (Veronika's): a fuzzy alignment needs a **content** check, not a
  coverage check. Not done here.

## KI-9 — Publication.publisher is fetched to disk but never merged into the corpus
**Status:** open — **do not fix** (filed 2026-07-17)
**Surfaced by:** the 04_validate publisher measurement (Change 2), 2026-07-17.
**Not a clean coverage gap:** for the CrossRef papers it is recoverable data loss, not absence.

Measured:
- **17 raw CrossRef JSONs** in `data/raw/publications/` — **all 17 carry `publisher`** (Wiley,
  Elsevier BV, …).
- **`02_extract.py:108` extracts it** (`"publisher": message.get("publisher", None)`) and writes
  `data/processed/entities/publications.jsonl`.
- **But the corpus on disk is not 02_extract's output.** `entities/publications.jsonl` is **805
  records, all `source_type: csv`, zero `api`** — 02b's CSV output (02b appends, has no publisher
  column). The CrossRef path (02_extract) was **never merged in**.
- Of the 17 CrossRef DOIs, **14 appear** in the corpus (as CSV-sourced records with no
  publisher); **3 are absent entirely**.

**Two populations, not one:**
- **~14 papers** with a CrossRef DOI and a raw JSON carrying `publisher` → **fetched,
  extractable, dropped** — recoverable by running/merging the CrossRef path. **Data loss.**
- **~791 CSV-only papers** with no CrossRef record → **no source has it. Genuine coverage gap.**

`04` cannot tell the two apart (both are `missing_coverage:publisher`, 805 total) — the
distinction is provenance, not a per-record property. The schema ④a note is corrected to say so.

**Also recorded, not chased:** **only 17 CrossRef JSONs against 806 papers.** That ratio
suggests `01_fetch` / `02_extract` (the CrossRef path) **barely ran** — 17 of 806 ≈ 2%. Not
investigated here; noted so the next person asks why the API path is nearly empty.

## KI-8 — 21 sha256_hash collisions in rawfiles_pxd.jsonl (the INVERSE of KI-1)
**Status:** open — **needs a ruling, do not fix** (filed 2026-07-17)
**Surfaced by:** the 04_validate spec work (measurement M1), 2026-07-17.
**A 05 blocker.** `db.py`'s `CREATE CONSTRAINT rawfile_sha256 … REQUIRE r.sha256_hash IS UNIQUE`
rejects these at load.

**21 `sha256_hash` values each appear on 2 RawDataFile records = 42 records**, all in
`data/processed/normalized/rawfiles_pxd.jsonl`, all `source_type: fisher_py`, all named
`20170309_ksn5514_FACS_BC_RP4H_10547771_*`. Each pair has **different filenames but
byte-identical content** (identical `sha256_hash`) — one physical file deposited under two
descriptive names:

| sha256 (first 16) | the two identifiers |
|---|---|
| `1097d6d6a7ee2a89` | `…_B_FACS_biorep_01_techrep_01.raw` / `…_D1_B_SEP_tech_rep_02.raw` |
| `418bf6d38458e252` | `…_B_FACS_biorep_01_techrep_02.raw` / `…_D1_B_FACS_tech_rep_02.raw` |
| … (21 groups; 42 distinct identifiers; 0 null hashes) | |

**The INVERSE of KI-1, and not the same batch.** KI-1 is **one filename written twice** —
double-emission from two source JSONs producing a byte-identical node under the *same*
identifier (the `20180615_rmi049_*` batch, filenames shared). **KI-8 is one file under two
names** — *distinct* identifiers, identical content hash (the `20170309_ksn5514_*` set).
Different mechanism, different batch.

**Why 03 cannot catch it.** `03_normalize.py` dedups on `identifier` (pass 2). These 42
records carry 42 distinct identifiers, so the identifier key never collides and a hash
collision is **structurally invisible** to it. RawDataFile identity keys on `sha256_hash`
precisely because filenames are non-unique, so `sha256_hash IS UNIQUE` in `db.py` is what
would reject one of each pair at 05.

**04 behaviour:** `04_validate.py` reports these under `blockers.sha256_hash_collisions`,
**separately from `quarantined`** (different meaning, different fix), and **exits non-zero**
when the blocker list is non-empty — a validator holding a known 05 blocker must not exit 0.
It does **not** auto-quarantine them (removing a record is a fix, and the fix is unruled).

**Open ruling — do not make, do not fix:** merge the pair to one node; keep both with a
shared-content property; or drop the uniqueness constraint. Report only; mint/delete nothing.

## KI-7 — the Instruments CV covers 34 aliases against 462 PDF-extracted instruments
**Status:** open — **needs a ruling, do not fix** (filed 2026-07-16)
**Surfaced by:** the first 03 run against `pdf_entities.jsonl` (2026-07-16).
**Not a bug.** 03 and the CV each do exactly what they were built to do. The gap is coverage.

The controlled vocabulary (`docs/controlled_vocabulary.md`) loads the instrument alias set. The
PDF instrument transform produced **462 Instrument nodes**. **As of 2026-07-17: 03 maps 13 and
logs 456 `instrument_unmapped`** to `review_queue.jsonl` — the correct, visible outcome, not a
failure. **Do not "fix" this by loosening matching**; the number is real and belongs in the
review queue.

**Update 2026-07-17 — the NMR CV rows moved the count from 7/462 to 13/456.** Six NMR (nmrCV)
rows were added to `controlled_vocabulary.md` (Grouping B, split by ¹H frequency; class-level
accessions NMR:1400198 / NMR:1400059), so the **6** extracted NMR instruments now canonicalize
and carry accessions + `ontology_source: NMRCV`. **What that did NOT fix:** the remaining **456**
unmapped are still the open ruling — TOC analyzers, Illumina MiSeq, accelerator MS, elemental
analyzers, UV-Vis, ion chromatography, etc. NMR closed **6 of 462**; whether the CV expands to the
rest of the non-MS/non-NMR instrumentation, or those stop being Instrument nodes, is unchanged
and undecided.

**The 54 list-valued nodes, all 206 variants tried:** **50 match nothing at all.** The 4 that
match are unanimous, and thin:

| node | variants hit | term |
|---|---|---|
| `instrument:raw:9_4_ft_icr_mass_spectrometer` | 1 of **38** | 9.4T FT-ICR MS |
| `instrument:raw:velos_pro_linear_ion_trap` | 1 of 4 | Velos Pro |
| `instrument:raw:ltq_velos_ion_trap_mass_spectrometer` | 1 of 6 | LTQ Orbitrap Velos |
| `instrument:raw:orbitrap_eclipse_tribrid` | 1 of 3 | Orbitrap Eclipse Tribrid |

**The no-hit set is heavily NON-MS**, and the CV was never built to cover it: Shimadzu TOC
analyzers (5 distinct nodes), spectrofluorometers (Hitachi F-7000, Horiba Aqualog), ion
chromatography (Dionex Aquion, UltiMate 3000), **Illumina MiSeq**, **Keck Carbon Cycle
accelerator MS**, elemental analyzers, UV-Vis spectrophotometers, NMR (Bruker Avance). The
corpus is broader than the vocabulary. **The ruling needed:** does the CV expand to non-MS
instrumentation, or do non-MS instruments stop being Instrument nodes?

### KI-7a — one instrument, two identifiers, unmergeable
`instrument:raw:9_4t_ft_icr` (**0 of 9** variants hit) and
`instrument:raw:9_4_ft_icr_mass_spectrometer` (**1 of 38** hit → `9.4T FT-ICR MS`) are **the
same 9.4 T instrument under two identifiers**. One maps, one does not.

**03 cannot merge them.** Its dedup is by **exact identifier** (pass 2), and these differ; the
CV pass assigns `canonical_name` as a *property* and never re-points identity. So the graph
carries two nodes for one box, one canonicalized and one not. Same shape as KI-6's duplication
but worse: KI-6's duplicates share an identifier and collapse; these do not and cannot.
Report only — fixing it means either an identifier ruling or a CV-driven identity merge, and
neither exists.

## KI-6 — `instruments.jsonl` is 159 lines but only 7 instruments
**Status:** open — **do not fix** (filed 2026-07-16)
**Surfaced by:** the software-field `--apply` (2026-07-16), auditing the entity-file layout.
**Same shape as KI-1** (02f emitting duplicate node lines), in a different file.

`data/processed/entities/instruments.jsonl` holds **159 records but 7 distinct identifiers —
152 duplicate node lines.** Measured:

| identifier | lines |
|---|---:|
| `instrument:raw:21t_icr` | **152** |
| `instrument:raw:ltq_ft_ultra` | 2 |
| `instrument:raw:900mhz` | 1 |
| `instrument:raw:600mhz_dnp` | 1 |
| `instrument:raw:orbitrap_fusion_lumos` | 1 |
| `instrument:raw:orbitrap_elite` | 1 |
| `instrument:raw:q_exactive_orbitrap` | 1 |

`source_type`: 154 `csv`, 5 `fisher_py` — so the 152 come from **02b re-emitting the 21 T ICR
node once per CSV paper that used it**, not from one bad run.

**"159 instruments" is 7.** Any count read off this file's line count is wrong by 22×. The
instrument field's real total is **7 (RAW/CSV) + 462 (PDF, in `pdf_entities.jsonl`) = 469
distinct**, which matches the figure recorded elsewhere — so the 469 is right and the 159 is
the misleading number.

**Survivable only because `03_normalize.py` dedups by identifier *within* a file** (pass 2,
line 323), which collapses the 152 to 1 before anything downstream sees them. That is luck of
layout, not design: the same duplication **across** two files would pass straight through (03
does not dedup cross-file) and hit 05's uniqueness constraint. See the Software field's
cross-file-overlap invariant in `SCIKG_SCHEMA.md § Node: Software`.

**Do not fix by deduping the file:** these are additive extractor outputs, and 03 is the
declared dedup stage. The question worth ruling is whether 02b/02c *should* emit one line per
usage at all, or whether the extractors should dedup on write like 02c's `add_entity` already
does for its own run.

## KI-5 — 02d's grounded-only policy drops real extractions that name multiple tools
**Status:** open — **do not fix here.** The fix belongs **upstream in 02d**
(`scripts/02d_extract_pdf.py`) — **Veronika's script, Veronika's call.**
**Surfaced by:** the software-field build (2026-07-16), auditing `software_tools`.
**Affects:** the **three-way count** reported for every field (§2.-1), and §9.5's token totals
(`486 mentions / 333 distinct tokens from 233 bundles / 191 distinct bundle strings`) — all of
which derive from the 233/144/1 split below.

### Mechanism
`02d_extract_pdf.py::_is_grounded()` accepts an alignment outright if its status is in
`ACCEPTED_ALIGNMENTS`; otherwise (`MATCH_LESSER`) it requires
`span_len / value_len >= MIN_SPAN_COVERAGE`. **That guard is sound and must not be loosened** —
it is the only thing stopping a one-word overlap from grounding a long fabricated string.

It fires on a shape it was not aimed at. When the LLM correctly returns a value naming
**several** tools, the aligned span is almost always **exactly the first tool name**, so
coverage is computed as one span against a multi-tool string and collapses. **The value is
punished for being complete.**

### Measurement (2026-07-16, boilerplate non-answers excluded)
| class | values | papers | verdict |
|---|---:|---:|---|
| dropped **with** a `char_span` — extractor **located real text** | **63** | **52** | the bug |
| dropped with **no** `char_span` — never located | 62 | 46 | correctly dropped |

**Dropped-but-real (the span-coverage class):**

| DOI | value | span | coverage |
|---|---|---|---|
| `10.1016/j.mcpro.2024.100814` | `SNAP 2.0, DataAnalysis (Bruker), Agilent MassHunter Qualitative Analysis Navigator B.08.…` | 8 chars for 166 | **0.048** |
| `10.1021/acs.energyfuels.2c04274` | `Predator Acquisition, Predator Analysis, PetroOrg` | 20 chars | **0.408** |
| `10.1002/2017JG004337` | `EnviroOrg (Corilo, 2015)` | 9 chars — exactly `EnviroOrg` | **0.375** |
| `10.1007/s13361-018-1897-y` | `Xcalibur v3.0.63` | 8 chars — exactly `Xcalibur` | 0.5 |
| `10.1021/acs.est.3c09797` | `QIIME2 (release 2021.2), DADA2, scikit-learn` | 23 chars | 0.523 |

All real, domain-correct, and present in the paper. Others in the set name TDPortal, ProSight
Lite, Mascot, MSConvert, ggplot2, vegan, JMP Pro, GraphPad Prism, MSDial, SciPy.

**Correctly dropped (no span) — the guard working:** e.g. `10.1021/jasms.0c00036`'s
`BioPharma Compass, ProSight PC and BioPharma Finder, TDValidator, Peak-by-Peak, AutoVectis,
MASH Suite Pro, …` — 17-char span for a 158-char value, never located. This is the class the
threshold exists for. **The guard works; it just also catches the class above.**

### Consequence — why this is filed, not noted
**51 of the affected papers have an EMPTY consolidated value**, so the drop is **total loss**.
Those papers currently count as **genuine negatives** in the three-way
(**233 with a value / 144 negatives / 1 failed**). **Some fraction of that 144 is missing data,
not absence** — the exact distinction §2.-1's guard exists to preserve, failing one level
upstream of where the guard looks. **The field's headline count is wrong in the direction that
inflates negatives.**

Several dropped values would also **resolve today** if they survived — `Predator Acquisition,
Predator Analysis, PetroOrg` is precisely the adjacency §9.3's MIDAS/Predator ruling covers.

### The fix (upstream, not here)
**Per-tool spans.** LangExtract can return **one extraction per tool**, which makes
`span_len / value_len` meaningful again and leaves the threshold untouched. **Do not loosen
`MIN_SPAN_COVERAGE`.** This is an 02d change and belongs to Veronika; nothing in the software
transform should compensate for it, and no count above should be quietly "corrected" downstream.

## KI-4 — vendor-strip swallows across a paren boundary, producing unbalanced tokens
**Status:** open — a bug, not a ruling — **do not fix** (filed 2026-07-16)
**Belongs to:** `docs/pdf_transform_logic.md` §9.5 **step 4 (vendor-strip)**
**Where:** `scripts/transform_pdf_software.py`, `extract_vendor()`

The vendor regex is `\(?\b<VENDOR>\b,?\s*\)?` — the optional `\(?` lets it consume an **opening
paren that belongs to the surrounding token**, not to the vendor. The closing paren survives, so
the output is unbalanced and the rest of the parenthetical is orphaned.

Measured (`10.1007/s13361-019-02290-8`):

| stage | value |
|---|---|
| token | `ProSight PD ™ (Thermo Fisher Scientific PD version 2.1, ProSightPC version 4.0)` |
| after vendor-strip | `ProSight PD ™ PD version 2.1, ProSightPC version 4.0)` |
| after version-extract | `ProSight PD ™ PD , ProSightPC version 4.0)` ← unbalanced `)` |

**Nothing wrong reaches the graph today — but that is luck, not design.** This token is
*independently* ruled REVIEW (§9.6a: the ProSight PD/ProSightPC case, n=1, no rule built), so
the mangled string is parked in the review file rather than minted. The guard that saves it has
nothing to do with the bug: a token with a vendor inside a parenthetical that was *not*
separately ruled REVIEW would be canonicalized from mangled text. The blast radius is any
`Tool (Vendor …)` shape where the parenthetical carries more than the vendor name.

Note the contrast that shows the regex is *usually* fine: `Intact Mass (Protein Metrics)` and
`MaxEnt (Bruker Daltonics)` strip cleanly to `Intact Mass` / `MaxEnt`, because there the
parenthetical holds **only** the vendor, so eating both parens is harmless. The bug appears only
when the paren has other content.

Do not fix without deciding whether vendor-strip should be paren-aware (like the §9.5 step-3
splitter now is, KI-adjacent — see `_paren_depth_scan`) or whether the `\(?`/`\)?` should simply
be dropped and paren cleanup left to `_tidy`.

## KI-3 — 3 instrument strings absent from the completed instrument field
**Status:** open — needs a ruling — do not fix (do not mint anything)
**Surfaced by:** the software-field build (2026-07-15), reading `software_tools`.

The instrument transform read the `instrument` field and is done (469 nodes on disk). Three
strings that name instruments arrived instead through `software_tools`, so that completed field
never saw them:

| String | On disk as an Instrument node? |
|---|---|
| Tri-carb 2800TR scintillation counter | No |
| StepOne (Applied Biosystems) | No |
| JED-2300 (series standard software) | No |
| NanoDrop 2000c | Yes — `instrument:raw:nanodrop_2000_uv_vis_spectrophotometer` |

3 of 4 are absent — a gap a finished field can't absorb on its own. Report only; mint nothing.
A ruling is needed on how strings that surface in the "wrong" field reach a completed field.

## KI-2 — No reagent node type or inbox
**Status:** open — needs a schema ruling never made — do not fix
**Surfaced by:** the software-field build (2026-07-15), reading `software_tools`.

These reagent/kit/stain strings appeared in `software_tools` but are not Software, and the
schema has **no** reagent node type and no property inbox to route them to:

- Qubit protein assay kit
- SYPRO Ruby fluorescent protein stain
- Pro-Q Diamond phosphoprotein gel stain
- PowerUp SYBR Green Master Mix

Needs a schema decision: a Reagent node type, a Publication property, or out of scope. Until
then they are neither minted nor discarded — recorded here.

## KI-1 — 02f emits duplicate node lines and accession-blind edges for hash-identical cross-deposited files
**Status:** open bug in `scripts/02f_extract_pxd_rawfiles.py` — fix at source when 02f is next touched
**Found:** 2026-07-15, during the software-field / Xcalibur-migration work.

64 Blood Proteoform Atlas files (`20180615_rmi049_75idPLRPS_APA_PBMC_*`) are cross-deposited
under two PXD accessions. 02f processes each once per source JSON, producing per file:
- 2 byte-identical `RawDataFile` node lines (same `sha256_hash`);
- 2 byte-identical `COLLECTED_ON` edges (measured: 64 duplicate pairs);
- 2 byte-identical `ACQUIRED_WITH` edges (64 duplicate pairs);
- 2 **legitimately distinct** `DERIVED_FROM` edges (0 duplicate pairs — one per accession).

`COLLECTED_ON` measured field-by-field on disk: `properties` is `{}` on every row, and each of
the 64 pairs is byte-identical across all fields — `source_id`, `evidence_note`, `extracted_at`,
`confidence`, `source_type`, `schema_version`, `properties` (64/64 each; full-row identical
64/64). Every PXD RawDataFile collects on the same instrument (`instrument:raw:orbitrap_fusion_lumos`),
so `object_id` is constant across a file's two source-JSON runs — the duplication is pure
double-emission, not an accession-distinguishing edge that got flattened.

**Fix — dedup keyed per artifact, NOT blanket:** nodes dedup on `sha256_hash`; edges dedup on
`(subject, object, properties)` **per `relationship_type`**. `DERIVED_FROM`'s object differs by
accession, so its 64 pairs MUST survive — a blanket `(subject, type)` dedup would delete the
second accession and silently drop cross-deposit provenance. `COLLECTED_ON`/`ACQUIRED_WITH`
carry no accession, so their 64 pairs collapse with no loss. (03_normalize already applies this
exact edge key downstream; the fix is to stop emitting the duplicates at source.)

**Note:** the ACQUIRED_WITH duplicates were resolved for Software specifically by the
2026-07-15 Xcalibur migration (998 → 934 on `(subject, object, properties)`). COLLECTED_ON
still carries its 64 duplicates on disk (998); it is out of scope for a Software migration and
03 coalesces it to 934 on the same key. This ticket is the source-level fix for all edge types.
