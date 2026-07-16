# SciKG — Known Issues

Real issues found and ruled out of the current scope, kept visible so they aren't rediscovered
or silently lost. `gh` is not installed in this environment; this file is the ticket home.
Each entry states what it is, how it was measured, and whether it needs a ruling or a fix.
Add new issues at the top.

---

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
