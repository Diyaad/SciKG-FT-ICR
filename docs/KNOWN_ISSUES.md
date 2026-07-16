# SciKG — Known Issues

Real issues found and ruled out of the current scope, kept visible so they aren't rediscovered
or silently lost. `gh` is not installed in this environment; this file is the ticket home.
Each entry states what it is, how it was measured, and whether it needs a ruling or a fix.
Add new issues at the top.

---

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
