# PDF-transform — field logic (build reference)

Covers the shared machinery (§2: extraction-failure guard, hybrid resolver, four-way classify —
every field inherits these) plus per-field logic. Facility is §1–8; Software is §9. The title
was "FACILITY field logic" through 2026-07-14; renamed 2026-07-15 when Software became the
second field to reuse §2, so the shared machinery is not mistaken for facility-specific.

Build note to lift into the consolidated PDF-transform script once all six fields
(instrument, ionization, software, dataset, sample, facility) are built to the same
pattern. Not authoritative schema — see `docs/SCIKG_SCHEMA.md`. Working impl lives in
scratch: `finalize_pdf_facility.py` (to be promoted to `scripts/`).
**⚠ NOT IN THE REPO — see KI-13 (`docs/KNOWN_ISSUES.md`).** This `finalize_pdf_facility.py` is the
early Jul-14 (21-node) version; the **confirmed** producer of the committed **62** Institution + 89
INVOLVES_INSTITUTION is **`finalize.py`**, and of the **462** Instrument + 968 USES_INSTRUMENT is
**`finalize_inst.py`** — both from session `18b6037e`. Neither is in `scripts/`; both **lived in
session scratch, now recovered to `~/scikg-scratch-all`** (the code is NOT lost — the original claim
that it "cannot be regenerated" was wrong; producers confirmed from their runs' pickles, KI-13
Method). Promotion needs the per-module `BASE`/`REPO` path handling fixed, not just a copy (KI-13).

## 1. Purpose
One section of the PDF-extraction → entity transform. Reads the **consolidated
`facility` field** from `data/raw/pdf_extraction_134papers.jsonl` (grounded values
only), splits on `;`, trims, dedupes, and turns **external** organizations into
`Institution` nodes + `INVOLVES_INSTITUTION` edges. NHMFL/MagLab mentions are
**skipped** — the CSV already owns NHMFL attribution via `CONDUCTED_AT`
(Publication → Facility, ~99% `facility:icr_facility`), so PDF "NHMFL" is redundant.

Source read: consolidated field only (`record["facility"] = {value, source_snippet,
grounded, confidence, char_span}`); value is non-null only when `grounded==true`.
Ignore `all_field_extractions` (raw layer, holds the `PXD000000` placeholder etc.).

## 2. Classification pattern
Conservative: never over-drop, never over-assert. **When in doubt → REVIEW, not REJECT.**

### 2.-1 Extraction-failure guard — runs FIRST, field-agnostic (every field inherits)
Before ANY field logic (before the per-field grounded-skip of §2.0/§2.1), classify each
record three ways so a **failed extraction (missing data)** is never mistaken for a
**genuine negative (absent data)** — they look identical if you only check
`grounded == false`. Applies to instrument/software/dataset/ionization/sample too, not
just facility. Lives in `resolver.py` as `extraction_failed(r)`:

```python
EXTRACTION_FIELDS = ['instrument','ionization_method','sample_type','facility',
                     'software_tools','dataset_accession']
def extraction_failed(r):
    if r.get('pdf_source') != 'local':                       return 'no_pdf_acquired'
    if 'No PDF could be acquired' in (r.get('evidence_note') or ''): return 'evidence_note_flag'
    all_null = all((r.get(f) or {}).get('value') is None for f in EXTRACTION_FIELDS)
    if all_null and len(r.get('all_field_extractions', [])) == 0: return 'ran_but_empty'
    return None
```

- **Failed** (reason != None) → EXCLUDE from all field logic; report loudly
  `EXTRACTION_FAILED <doi> (<reason>)`. Missing data, not absent data.
- **Genuine negative** (all fields null BUT `all_field_extractions` > 0 → extraction ran,
  found candidates, none grounded) → NOT a failure; do not quarantine.
- Every field's dry-run report is **THREE-WAY**: *N with a value / M genuine negatives /
  K failed extractions* — never the two-way "N with / rest without" that hides missing
  data inside the negatives.
  - **Counts affected by KI-5** (`docs/KNOWN_ISSUES.md`): 02d drops multi-tool values on span
    coverage, so **the genuine-negatives bucket is inflated — by up to 51 papers for
    `software_tools` (144 negatives)**. Missing data is hiding inside the negatives one level
    *upstream* of this guard. **Do not adjust the number** to compensate: a patched count reads
    as a measured one. The fix is per-tool spans in 02d.
- Signatures seen (378 batch): `pdf_source:'none'` + "No PDF could be acquired" (hard
  failure, e.g. a double-dot filename 02d couldn't open); `local` + zero
  `all_field_extractions` = `ran_but_empty` (PDF opened, produced nothing — likely
  image-only/OCR miss; quarantine for a human, don't count as a clean negative).

### 2.0 Resolve BEFORE classify — the hybrid resolver (exact + fuzzy)
Every non-SKIP string is first RESOLVED against the existing Institution set
(`pdf_entities.jsonl`: each node's `name` + `aliases` + `name_raw`) in three tiers,
BEFORE any mint/reject/review decision. This is what makes re-running over a bigger
batch batch-safe — previously-seen orgs collapse instead of re-minting.

  1. **EXACT** normalized match (lowercase, collapse whitespace) on name/aliases/
     name_raw → **auto-resolve silently** (no human step). Add the raw string as a new
     alias if novel; never mint a duplicate; identifiers stay frozen.
  2. **FUZZY** → **PROPOSE ONLY** into a `confirm-resolve` bucket for human sign-off.
     NEVER auto-merged. Three signals:
       - (A) a substantial known org-name (≥2 tokens, ≥6 chars) is a contiguous
         substring of the string — or the string inside a variant, but ONLY when the
         string is itself substantial (≥2 tokens, ≥1 distinctive token, ≥10 chars);
       - (B) ≥2 distinctive (non-generic) shared tokens AND token-overlap coeff ≥ 0.5;
       - (C) a distinctive acronym (≥4 chars, all-caps) present as a whole token.
  3. **FALL-THROUGH** (no resolve) → the four-way classify below, plus a **`pub-property`**
     outcome for generic descriptors (see §7 items 5–6).

Rule in one line: **FUZZY PROPOSES, HUMAN DISPOSES.** Nothing fuzzy is ever auto-applied.

### 2.1 Four-way classify (applied to fall-through only)
- **SKIP** (drop silently, count only): NHMFL/MagLab variants. Normalize whitespace,
  lowercase, then skip if string contains `"magnetic field"` OR `"nhmfl"` OR
  `"maglab"`. Catches OCR double-spaces (`National High  Magnetic  Field Laboratory`)
  and all `NHMFL (…)` / `…at Florida State University` variants. Redundant with CSV.
- **MINT** → `Institution` node, `inst:{normalized_name}`. External org with a clear
  proper name.
- **REJECT** (log reason) — unambiguous garbage ONLY:
  - contains `http` / `www.`
  - bare geography (`Amsterdam, Netherlands`; `Massachusetts, USA`)
  - sentence fragments (`in-house`; `the mine`; `the mouth of Taylor Slough (TS)`)
  - data repositories (`…(MassIVE)`)
  - funding phrases (`…start-up funds`)
  - person names (`Bob Allen Keys (BASW)`)
  - instrument vendors (`Thermo Scientific, …`) — belong to instrument provenance
- **REVIEW** → review file (`facility_institution_review.md`), human decides. Anything
  not confidently SKIP/MINT/REJECT.

Implementation note: MINT vs REVIEW is a **judgment call not fully automatable**. The
working script uses a high-precision MINT allowlist + explicit human decision map;
everything else falls to REVIEW. Bias to REVIEW is intentional (cost of minting
garbage >> cost of a human confirming a real institution).

## 3. Decisions made (do not re-litigate)
- External orgs → **`Institution`** nodes (`inst:` prefix per schema §Identifier),
  NOT `Facility`. `Facility` = NHMFL internal facility, CSV-owned.
- **"X Lab at Y University" → mint the PARENT UNIVERSITY**, preserve the specific lab
  string verbatim in `name_raw`. (Onstott Lab→`inst:princeton_university`; ILMARI→
  `inst:university_of_eastern_finland`; Water Quality Lab→`inst:university_of_new_hampshire`;
  Materials Research Institute→`inst:pennsylvania_state_university`; Mark Wainwright
  Analytical Centre→`inst:unsw_sydney`.)
- **FSU → `inst:florida_state_university`** — distinct node from the NHMFL facility
  (NHMFL is physically at FSU, but the org is separate).
- **Commercial labs → mint**: Intertek, Microsynth AG, Midwest Micro Lab,
  Research & Testing Laboratories LLC.
- **Thermo Scientific → reject** (instrument vendor, not a research institution).
- Provenance: `confidence: "medium"` (values grounded/in-text, but LLM-extracted &
  identity unverified); `source_type: "llm_extraction"`.
- New edge **`INVOLVES_INSTITUTION`** (Publication → Institution, MANY-MANY, Active)
  added to `docs/SCIKG_SCHEMA.md`. Distinct from `CONDUCTED_AT` (→Facility) and does
  NOT replace `AFFILIATED_WITH` (Researcher→Institution). Naming: VERB_OBJECTNOUN,
  sibling of `INVOLVES_ORGANISM`.

## 4. Output shape (real samples from what was written)

Node → `data/processed/entities/pdf_entities.jsonl`:
```json
{"identifier":"inst:eth_zurich","entity_type":"Institution","properties":{"name":"ETH Zurich","name_raw":"ETH Zurich"},"source_type":"llm_extraction","confidence":"medium","extracted_at":"2026-07-13T22:52:39.492109+00:00","evidence_note":"External institution extracted from PDF via Docling + LangExtract (model llama3.1:8b), grounded verbatim in article text; identity unverified.","source_id":"doi:10.1038/s41561-019-0384-9","schema_version":"v1.0"}
```
`name` = cleaned canonical; `name_raw` = verbatim string from the PDF (e.g. for the
parent-university remaps `name_raw` keeps `"Onstott Lab at Princeton University"`).

Edge → `data/processed/relationships/pdf_relationships.jsonl`:
```json
{"relationship_type":"INVOLVES_INSTITUTION","subject_id":"doi:10.1038/s41561-019-0384-9","subject_type":"Publication","object_id":"inst:eth_zurich","object_type":"Institution","properties":{},"source_type":"llm_extraction","confidence":"medium","extracted_at":"2026-07-13T22:52:39.492109+00:00","evidence_note":"External institution extracted from PDF via Docling + LangExtract (model llama3.1:8b), grounded verbatim in article text; identity unverified.","source_id":"doi:10.1038/s41561-019-0384-9","schema_version":"v1.0"}
```

Six provenance fields on every node AND edge: `source_type`, `confidence`,
`extracted_at` (from record), `evidence_note`, `source_id` (`doi:{lower}`),
`schema_version` ("v1.0").

**Dedup**: one `Institution` node per distinct `inst:{…}`; one edge per
(institution, paper). Two papers naming the same org → one node, two edges. One paper
naming two orgs → two nodes, two edges (seen: `10.1038/s41467-022-29711-9` → ANSTO +
UNSW; `10.1038/s41561-019-0384-9` → ETH + FSU).

## 5. DOI handling
- Normal: `subject_id`/`source_id` = `doi:{doi.lower()}`.
- 3 lossy underscore-form DOIs (`10_1002_rcm_4655`, `10_1021_ac0108461`,
  `10_1039_D2GC01135B`): resolve via `_pdf_filename` → strip `.pdf` → match against
  `publications.jsonl` identifiers (`doi:` with `/`&`.`→`_`). If unresolvable: **mint
  the node, hold the edge**, list as pending (never attach to a guessed Publication).
- This run: 0 edges held (none of the minted orgs came from the 3 lossy DOIs).

## 6. Status / open items
- **Written**: 17 `Institution` nodes → `pdf_entities.jsonl`; 17
  `INVOLVES_INSTITUTION` edges → `pdf_relationships.jsonl`.
- **Rejected**: 11 (incl. both Thermo strings).
- **Schema**: `Institution` node flipped PLANNED → **Active — partially populated
  (17)**; `INVOLVES_INSTITUTION` edge added (Active).
- **6 review items still pending** (not minted, not rejected — human decision):
  1. `Chair of Soil Science (TU München, Germany)`
  2. `ExxonMobil's Clinton campus`
  3. `GEOTRACES Eastern Pacific Zonal Transect cruise`
  4. `GFZ Potsdam, Germany`
  5. `Hansell Organic Biogeochemistry Laboratory`
  6. `NRTDP (Evanston, IL)`
- **Not run**: 03 normalization not run against this output yet.
- **TODO**: promote the scratch PDF transforms into `scripts/` as a consolidated
  PDF-transform stage once instrument / ionization / software / dataset / sample fields are
  built to this same four-way pattern. **Scope correction (see KI-13):** the producers are not
  just `finalize_pdf_facility.py` — the **confirmed** committed producers are **`finalize.py`**
  (62 Institution + 89 INVOLVES_INSTITUTION) and **`finalize_inst.py`** (462 Instrument + 968
  USES_INSTRUMENT), both from session `18b6037e`, recovered to `~/scikg-scratch-all`. The
  **instrument transform had no TODO anywhere until now** — this is its record. Promotion must
  fix the per-module `BASE`/`REPO` path handling and `inst_v2`'s import-time repo I/O, not just
  copy the files (KI-13 Open). Stale line to fix then: Institution node section still says
  "Sources 1 and 2." above the status block — nodes now come from PDF extraction.

## 7. GROWTH REQUIREMENTS — must hold as more extraction batches arrive
Veronika is extracting more papers; new `pdf_extraction_*.jsonl` files will land.
The consolidated script MUST be built to satisfy all four of these from day one, so
batch 2 does not force a re-architecture.

1. **Glob input, not a hardcoded filename.** Read ALL extraction files from the
   designated dir: **`data/raw/pdf_extraction/*.jsonl`** (confirmed 2026-07-14: the
   original 134-file was MOVED into `data/raw/pdf_extraction/` — not duplicated; old
   top-level path no longer exists). Do NOT hardcode `pdf_extraction_134papers.jsonl`.
   New batches are expected to follow the same `pdf_extraction_*.jsonl` naming inside
   that folder. If two batches ever cover overlapping DOIs, dedup on `doi` so a paper
   read from two files is not double-counted.

2. **Alias-aware dedup ACROSS batches via the HYBRID resolver (§2.0).**
   Before minting any Institution, LOAD THE CURRENT INSTITUTION SET from prior runs
   (`pdf_entities.jsonl`: each node's `name` + `aliases` + `name_raw`). Resolve every new
   raw string through the three tiers in §2.0: EXACT auto-resolves silently; FUZZY
   proposes into `confirm-resolve` (human confirms → the raw string becomes a new alias
   on the frozen node); only genuine non-matches fall through to mint. Do NOT mint a
   duplicate of an org already present.
   - **Why exact-only is not enough (proven on the 378 batch):** exact match caught 18
     strings but MISSED 12 variant spellings of orgs already in the set (e.g.
     `Microsynth AG (Switzerland)` vs alias `Microsynth AG`; `LIP at ETH Zurich`;
     `NIST (…), Gaithersburg, MD`). Exact-only would have minted those as duplicates
     (a second Microsynth, a second NIST). The fuzzy layer recovers them as proposals.
   - **KNOWN TRAP — guard rule A (do not remove):** a short/generic single-token string
     must NOT match by being a substring *inside* a decorated alias. The bare string
     `"laboratory"` matched inside PNNL's alias `"Office of Science Pacific Northwest
     National Laboratory"` — a false positive. Fix: the "string-inside-variant" direction
     of signal (A) fires only when the string is itself substantial (≥2 tokens, ≥1
     distinctive token, ≥10 chars). `"laboratory"` / `"the laboratory"` are then excluded.
   - **REGRESSION LIST (must NOT fuzzy-merge — keep as asserts):**
     `University of Central Florida` ↛ `inst:florida_state_university` (shared "florida");
     `Australian National University (ANU)` ↛ `inst:australian_..._organisation` (ANSTO);
     `University of Washington` / `University of Waterloo` ↛ `inst:university_of_wisconsin_madison`;
     `Woodwell Climate Research Center` ↛ `inst:woods_hole_oceanographic_institution`
     (different orgs, same town "Woods Hole"); `Midwest Microlabs` stays UNMATCHED by
     fuzzy (a spelling variant of `inst:midwest_micro_lab` a human collapses, not the code).
   - Concrete collapse case: `NU SeqCore` + `NRTDP` both resolve to Northwestern (done —
     `inst:northwestern_university`).

3. **Idempotent.** Re-running over batch1+batch2 must NOT duplicate batch1's nodes or
   edges. Regenerate output cleanly by keying on stable identifiers: one node per
   `inst:{slug}` (identifiers frozen once minted), one edge per
   `(subject doi, INVOLVES_INSTITUTION, object inst:)` triple. Dedup on those keys, do
   not blindly append.

4. **Enrich vs mint on re-run.**
   - New alias for an existing institution → add to that node's `aliases` (enrich).
   - Brand-new institution → mint a new node.
   - New `INVOLVES_INSTITUTION` edge for an existing institution → add the edge (unique
     by the triple in #3).
   - **Identifiers are immutable**: never re-slug an existing `inst:{slug}` off a newer
     ROR canonical name — the edges already point at it (re-slugging would dangle them).
     ROR data enriches (`aliases`, `ror_id`, a canonical-name property) but never
     changes `identifier`.

5. **Generic descriptors → `pub-property`, NOT a node.** Strings too generic to identify
   an org — two different papers using the same string mean DIFFERENT places, so one node
   would falsely merge them — are recorded verbatim on the Publication instead of minted:
   e.g. `the laboratory`, `our lab`, `greenhouse facility`, `Clinical Haematology
   Department`, `N/A`. Proposed carrier: a `facilities_mentioned_raw` array on Publication
   (schema addition — PENDING approval, not yet applied). Same principle as the
   controlled-vocabulary peripherals rule: record as text on Publication, not as a node.

6. **National user facility hosted at an institution = its OWN node, not collapsed into
   the host.** Precedent (decided on the 378 batch): NOSAMS is a national user facility
   hosted at WHOI, exactly as the NHMFL is a national user facility hosted at FSU — and we
   keep `facility:icr_facility` distinct from `inst:florida_state_university`. So all NOSAMS
   strings → one own node `inst:nosams`, NOT `inst:woods_hole_oceanographic_institution`;
   likewise SSRL and the Advanced Light Source get their own nodes. The fuzzy layer WILL
   propose the host (it sees "Woods Hole Oceanographic Institution" in the string) — that
   proposal is REJECTED by this rule. Collapsing into the host would also be internally
   inconsistent, since NOSAMS strings that don't name WHOI would mint their own node anyway.

## 8. ROR ENRICHMENT — rules (aliases/ror_id come only from ROR or observed strings)
- Query the real ROR API (`api.ror.org`) per institution; take the top match, but a
  human confirms QUESTIONABLE/NO-MATCH before write (generic terms mis-match, e.g.
  "Midwest Micro Lab" → "Arts Midwest"; a research cruise → a Tanzanian hospital).
- `aliases` = ROR `aliases` + `acronyms` + the observed raw string(s), deduped.
  **Never LLM-generated.** No ROR match → `ror_id: null`, `aliases` = observed raw
  string(s) only.
- `name` = ROR canonical name when matched, else our cleaned name. `name_raw` always
  preserves the verbatim source string. `identifier` stays the existing `inst:{slug}`.
- Sub-units without their own ROR record (cores, named labs, university centers) match
  their PARENT org in ROR — decide per node whether to take the parent's `ror_id` or
  leave `ror_id: null`; do not silently assign a parent ROR id to a sub-unit.

## 9. SOFTWARE field logic — RULED, NOT IMPLEMENTED

The second field built to this doc's shared pattern; it inherits §2's failure guard, hybrid
resolver, and four-way classify. Reads the consolidated `software_tools` field. **RULED, NOT
IMPLEMENTED** — the software transform is not built; this section records the rulings so the
build is a transcription, not a re-derivation. The Xcalibur node migration (2026-07-15,
committed 44fb88f) is the one piece already on disk; everything else here is pending the build.

### 9.1 Identity
- `software:{canonical_name}` — **unconditional**, never contingent on a registry lookup.
- **Version is NOT identity** — it is a per-usage fact on the edge (`ACQUIRED_WITH.version`,
  `USES_SOFTWARE.version`). One node per tool: `software:xcalibur`, `software:petroorg`.
- `psi_ms_id`, `rrid`, `biotools_id` are **properties, not identity**. Rationale: a registry ID
  assigned later would otherwise move the identifier and re-point every edge (the Xcalibur
  collapse re-pointed 934) — the same failure mode as version-in-identity. Same pattern as
  Institution: `ror_id` is a property, `inst:{slug}` is identity.

### 9.2 Registry pattern — enrich, don't canonicalize
- **Rule:** *registry exists → the transform enriches from it; CV exists → 03 canonicalizes.*
  Software follows the **Institution** pattern (enrich from an external registry), NOT the
  Instrument pattern (mint raw → 03 maps to a CV). There is no Software CV table, and 03 has
  nothing to canonicalize Software against.
- **bio.tools** — automated by name via the open API, **exact-name match only**. Fuzzy top-hits
  are rejected: the API's `q=` returned PreyTouch for Predator, RelEx for Xcalibur, compareMS2
  for Mascot, predatoR for Predator — all discarded. A registry name-match is not identity proof.

#### 9.2a Match rule and the two guards — RULED 2026-07-16 (Diya), BUILT
**Match rule:** whitespace **removed**, **case-insensitive**. Whitespace removal is what reaches
`QIIME2 == "QIIME 2"` (collapsing leaves the space and still misses). Case-insensitivity is
load-bearing: `dada2`, `msConvert`, `msalign` are bio.tools' stored casings of real tools we use.

Two guards, both checked **before** the name test, in `scripts/query_biotools.py`:

1. **NHMFL-authored (primary, pre-query).** PetroOrg, Predator, EnviroOrg, MIDAS are
   NHMFL-authored and **cannot** have a bio.tools record → `searched_none`, no query issued.
   This rests on **provenance we hold** — who wrote the tool — not on name shape or description
   shape, so a future registry entry that collides on name cannot defeat it.
2. **`REJECT_HITS` blacklist (secondary).** `predatoR`, `PreyTouch`, `RelEx`, `compareMS2`,
   keyed by the hit's verbatim stored name. **This is a LIVE RUNTIME GUARD, not a record of past
   decisions — deleting an entry re-admits the false positive on the next run.** It exists
   because guard 1 only knows tools *we* author; collisions on third-party tools are invisible
   to it.

**ATHENA — why guard 2 is not redundant (measured 2026-07-16).** `Athena` in two corpus papers
is the **XAS/XANES tool** (Ravel & Newville 2005, Demeter/IFEFFIT): `10.1016/j.gca.2025.08.041`
(instrument: *Canadian Light Source SGM beamline*) and `10.1021/acs.est.3c01347` (facility:
*Stanford Synchrotron Radiation Lightsource*; a sulfur speciation study — S K-edge XANES).
bio.tools stores `ATHENA` (`biotoolsID: athena`, AI4SCR/ATHENA): *"an open-source computational
framework written in Python that facilitates the visualization, processing and analysis of
(spatial) heterogeneity from spatial omics data"* — topics Cytometry/Proteomics/Transcriptomics/
Imaging/Oncology. A different tool. It is **not NHMFL-authored**, so guard 1 cannot see it; only
guard 2 can. Reported, **not yet added** to `REJECT_HITS` — pending Diya. Until it is, a query
for Athena returns a **wrong** `biotools_id`.

#### 9.2b Registry matching is NOT automatable — RULED 2026-07-16 (Diya)
**The blacklist is not a rule. It is the negative cache of human registry confirms; the
canonical map's `has_id`s are the positive cache. Neither is a rule.** Every entry in either was
made by a human reading a description. Q4 established that no rule can replace that read: the
mismatch lives in the paper's *usage*, not in the registry record, so a check reading only the
record cannot see it. Registry matching therefore follows the same **FUZZY PROPOSES, HUMAN
DISPOSES** pattern as §9.8's confirm bucket — each hit needs a human read.

**Live entries: `ATHENA` only.** The other four are dead — measured 2026-07-16 by emptying
`REJECT_HITS` and re-querying: no result changed.

| entry | vs query | live? | why |
|---|---|---|---|
| **`ATHENA`** | Athena | **LIVE** | The only entry doing work. Guard 1 cannot see it — we do not author Athena — so guard 2 is the only thing standing between the graph and a spatial-omics ID on an XAS tool. |
| `predatoR` | Predator | DEAD | **Guard 1 made it redundant**: Predator is NHMFL-authored, so it is never queried and guard 2 is never reached. |
| `PreyTouch` | Predator | DEAD | Never matches the name test (and Predator is never queried anyway). |
| `RelEx` | Xcalibur | DEAD | Never matches the name test under exact matching. |
| `compareMS2` | Mascot | DEAD | Never matches the name test under exact matching. |

Dead entries are **retained**: they are the record of past human confirms, and deleting one
re-admits its false positive if guard 1's list ever changes. But they protect nothing today —
ATHENA is what guard 2 is actually for, and it is the shape to expect again: a real record for a
real tool, colliding on a name we do not own.

**Rejected alternatives — do not re-litigate:**
- **(a) Strict case-as-stored.** Rejects predatoR on its own, but drops `dada2`, `msConvert`,
  `msalign` — stored-casing variants of real tools — turning 3 correct IDs into false
  `searched_none`. Measured: 16 → 14 has_id.
- **(b) A description or topic check. Cannot be stated.** *"Must indicate mass spectrometry"*
  kills DADA2, ggplot2, QIIME2, vegan, Fiji, IGV — the corpus spans FT-ICR, proteomics, 16S, and
  ecology, so no domain filter separates real from false. *Blocking predatoR's topics* blocks
  DADA2 via the shared `Genetic variation` topic. The root cause: **nothing in predatoR's own
  record is anomalous** — it is a correct record for a real tool. The mismatch lives in the
  paper's *usage*, not in the registry record, so no rule reading only the record can see it.
- **RRID / SciCrunch** — name search is API-key-gated, so **NOT automated**. A **hand-verified
  RRID constant map** in the transform's corpus-rules block; values looked up by hand on
  scicrunch.org, **never guessed** (guessing `SCR_` ids and keeping the ones that resolve is
  brute-forcing an identifier space, not a lookup). Only **Thermo Xcalibur = RRID:SCR_014593**
  is verified so far.
- The constant map is, in effect, a **small registry-sourced Software CV** — stated plainly
  rather than claimed as full automation.

### 9.3 Registry status — FOUR states for `biotools_status` (RULED 2026-07-16, Diya)
`null` alone cannot distinguish *searched-and-absent* from *never-searched* — the same shape as
§2's extraction-failure guard. `rrid_status` keeps three states (`has_id | searched_none |
not_attempted`). **`biotools_status` takes four:**

| state | meaning |
|---|---|
| `has_id` | An exact-name hit came back **and a human read the description and confirmed it.** |
| **`proposed`** | An exact-name hit came back; **no human has read it.** A proposal, not a confirm. |
| `searched_none` | Searched, no exact-name hit — or a human read the hit and **rejected** it (Athena). |
| `not_attempted` | Never searched (e.g. the query failed). |

**Why the fourth state:** writing `has_id` for an unread hit is an **auto-accept** — the same
failure as auto-accepting a fuzzy match, and exactly what put a spatial-omics `biotools_id` on
our XAS Athena in a *tracked* artifact. §9.2b: `has_id` is the positive cache of human confirms,
so an unread hit cannot be one.

**`--apply` MUST NOT write a `biotools_id` for a `proposed` status.** The node carries
`biotools_id: null` + `biotools_status: proposed`. The proposed id lives in
`software_registry.jsonl` (`proposed_biotools_id`, with description/topics/homepage) for review,
and reaches the graph only on confirm. As of 2026-07-16: **0 `has_id`, 19 `proposed`,
34 `searched_none`, 0 `not_attempted`** across 53 tools — nothing has been confirmed yet.

> **CONFIRMED 2026-07-17 (Veronika) — the positive cache now has entries.** §9.2b: `has_id`
> is the positive cache of human registry confirms, built one description-read at a time. Its
> first 14 entries, each read and confirmed by Veronika, `biotools_id` written to the node,
> `biotools_status: has_id`: **ClipsMS, Cutadapt, DADA2, Fiji, ggplot2, IGV, MSConvert, ProSight
> Lite, ProteinProspector, PyC2MC, QIIME2, SPSS, vegan, MaxQuant.** **MetaMorpheus** and
> **Proteoform Suite** were read but **not confirmed** — they stay `proposed`. Per-tool verdicts
> and reasoning: `docs/software_registry_review.md`. NOTE: MaxQuant's node is confirmed but its
> only `USES_SOFTWARE` edge was removed as a fuzzy hallucination — see **KI-10**.
>
> **`software_registry.jsonl` deliberately still records these as `proposed` (W5, 2026-07-17).**
> That artifact is the bio.tools **query result** (the staging cache), **not** the decision record.
> The decision lives on the node (`biotools_status: has_id`) and in `software_registry_review.md`.
> A `proposed` there is therefore **not a contradiction** of a `has_id` node — do not "reconcile"
> the artifact back onto the nodes.

Consequence for the headline finding: the
most-used tools (PetroOrg, Predator, EnviroOrg) are NHMFL-authored and honestly carry
`biotools_status: searched_none` + `rrid_status: not_attempted` — "absent from bio.tools
(searched); RRID not yet searched," NOT "unregistered" unqualified.

**NHMFL-authored list — 4, not 3 (updated 2026-07-16).** This list is the input to §9.2a's
primary guard, so an incomplete list is an unguarded rule.

**Basis is stated per tool so this list does not read as memory.** Corpus strings alone are weak
evidence: an authorship marker in a bundle often attaches to a *sibling* tool, not to the tool
named (`Thermo Xcalibur software … and a custom-built script using ZeroBrane Studio` — "custom-
built" is the ZeroBrane script, not Xcalibur; `Predator data station; PetroOrg, in-house
developed MATLAB scripts` — "in-house" is the MATLAB scripts). A naive co-occurrence scan
therefore mis-tags Xcalibur (a Thermo product) as NHMFL-authored. Every row below states which
kind of evidence it rests on.

| Tool | papers | basis |
|---|---:|---|
| PetroOrg | 93 | **direct disk** (marker attaches to the tool): `Custom software (PetroOrg)`; `PetroOrg©,™ (Corilo, 2015)` |
| Predator | 44 | **published evidence** (Diya 2026-07-16): Blakney / Hendrickson / Marshall — sole data station for NHMFL's 9.4 T FT-ICR MS since July 2004. **No direct corpus string**; the bundles that mention Predator attach their authorship markers to siblings. |
| EnviroOrg | 14 | **direct disk**: `EnviroOrg (NHMFL software by Yuri Corilo)`; `in-house software (EnviroOrg)` |
| **MIDAS** | **6** | **published evidence** (Diya 2026-07-16): NHMFL's **M**odular **I**CR **D**ata **A**cquisition **S**ystem, Predator's PREDECESSOR — not its parent, so `MIDAS Predator` is TWO tools. **Also direct disk**: `custom-built MIDAS software` (10.1038/s42004-018-0031-1). |

**Canonical-map audit — RULED 2026-07-16 (Diya).** 9 map entries had **no §9 ruling behind
them** (added on the assistant's own judgment); 6 were minting nodes. Same class as the two
wrong bio.tools IDs: *a map entry nobody decided on*. Resolved:

- **MINT, ruled now** — real named tools, same basis as the 11 ruled 2026-07-16:
  **drEEM, ADF, Magicplot, Python, OriginPro, BioTools**, and **ProteinProspector**.
- **REMOVED — dead: no referent AND no ruling.** Do not re-add without evidence.
  `mash suite` (its only appearance is descriptive prose *inside* the ReSpect parenthetical —
  "…as implemented, for example in the MASH Suite" — naming where an algorithm lives, never a
  tool the paper ran); `coremos` (a typo; `corems` is the real key and has a referent);
  `imagej` (§9.6a routes `Fiji ImageJ …` to Fiji, so it has no independent referent).
- **Mnova — reported, not ruled.** See §9.5 step 4.5's unreachable-key note.

**`biotools_status: proposed` and MINT are independent — 16 tools are in both states.**
Minting a node does not confirm its registry ID. ClipsMS, Cutadapt, DADA2, Fiji, IGV,
MSConvert, MaxQuant, MetaMorpheus, ProSight Lite, **ProteinProspector**, Proteoform Suite,
PyC2MC, QIIME2, SPSS, ggplot2, vegan all mint today and carry `biotools_status: proposed`
until `docs/software_registry_review.md` returns. `--apply` writes `biotools_id: null` for
every one of them.

**Not added — authorship not establishable from the repo:**
- **CoreMS** (1 paper, `10.1016/j.orggeochem.2024.104880`) — **stays out. An inherited
  assertion, not evidence.** Recorded here because the claim is quotable and someone will hit it
  again.
  - **A prior session's report asserted it**, verbatim, in its Part 3 bio.tools coverage table:
    > `ProSightPC, ProSight PD, TDValidator, Fragariyo, CoreMS` | paper count `—` |
    > bio.tools `null (0 results)` | note: **"CoreMS notable — real NHMFL tool, no bio.tools
    > entry"**

    and in its headline paragraph: *"(CoreMS and the ProSight family members ProSightPC/ProSight
    PD/TDPortal/TDValidator are also unregistered — only ProSight Lite is in bio.tools.)"*
  - **No supporting evidence was given for "real NHMFL tool," and a later disk check
    (2026-07-16) found none anywhere in the corpus** — the string is a bare `CoreMS`, one paper,
    no authorship marker. The live query returns `searched_none`, which happens to match the
    value the guard would assign, so nothing is wrong today; CoreMS is simply **unguarded**, not
    established.
  - **The point:** an assertion inherited across sessions reads exactly like a finding once it
    is written down. §9.3's list is the input to §9.2a's primary guard, so it must rest on
    evidence (direct disk, or published and cited), never on an inherited claim. Promoting
    CoreMS on the strength of that note is precisely the failure this guard exists to prevent.
- **Composer** (2 papers) — Diya 2026-07-16: Sierra Analytics FT-ICR software, *developed with*
  the NHMFL FT-ICR facility at FSU but **vendor-authored**, so it is NOT NHMFL-authored and does
  NOT belong in this list. → MINT, `vendor: Sierra Analytics`; `Composer64` is the same tool.
  Live query returns `searched_none`, agreeing.
- **`National High Magnetic Field Laboratory software` / `NHMFL software`** (disk:
  `10.1016/j.orggeochem.2018.03.005`, `10.1016/j.orggeochem.2023.104667`) — generic-but-real
  mentions of *unnamed* NHMFL software. Not a tool name, so not a node and not a guard entry;
  they belong in §9.7's `software_mentioned_raw` bucket, which does not currently list them.

### 9.4 Coverage table — constant-map seed
**Provenance of this table:** `biotools` statuses (and the §9.2 fuzzy-reject examples PreyTouch/
RelEx/compareMS2/predatoR) come from a **bio.tools exact-name API query run 2026-07-15** — a
live registry lookup, reproducible by re-querying, not from the extraction data. Paper counts
are the software-survey's distinct-paper counts over the disk input `data/raw/pdf_extraction/*.jsonl`
(splitter-dependent; see §9.5). Only Xcalibur's RRID is verified (SCR_014593); every other RRID
is `not_attempted` pending the §9.9 shortlist.

> **This table is a SEED, not a source of truth.** Nothing in it was verified against a
> re-runnable artifact. The transform MUST re-query bio.tools at build time and write the
> results to disk. Do not copy these rows into the constant map.

**Statuses only — no literal IDs.** Every `biotools` cell records a *status*
(`has_id` / `searched_none`), never the actual `biotools_id` string. With no IDs in the table
there is nothing to copy, so copy risk is zero — the build gets every ID from the re-query
(below), not from here. (Xcalibur's `rrid` cell is the sole literal ID kept: SCR_014593 is a
**verified** value already on disk from the migration, not a seed.)

**Durable fix (S2) — BUILT 2026-07-16 (Diya authorized D3).** `scripts/query_biotools.py` runs
the exact-name query and writes `data/processed/software_registry.jsonl`; the transform reads
**that artifact**, never the table below. Re-run the script to refresh. 42 tools queried:
**16 `has_id` / 26 `searched_none` / 0 failed.** A failed query records `not_attempted`, never
`searched_none` — asserting an absence never established is the §2.-1 guard's failure mode.

**Seed corrections from the live query** (the seed was wrong; recorded, not silently fixed):

| Tool | seed said | live query | note |
|---|---|---|---|
| Mascot | has_id | **searched_none** | no exact-name record; `q=` returns compareMS2 / PeptideShaker / PIA |
| ImageJ | has_id | **searched_none** | no exact-name record; `q=` returns FijiFISH / SReD / deepImageJ |
| QIIME2 | has_id | **searched_none** | a record exists but is named `QIIME 2` (space) — exact-name match cannot reach it. Whether a name variant may be queried is a ruling, not a fix. |

**`predatoR` — the false positive exact-matching cannot catch.** bio.tools has a record named
`predatoR` (biotoolsID `predator`, "an R package for network-based mutation impact
prediction"). Case-insensitive normalization makes `predatoR` == `Predator`, so it scores as an
*exact* hit for NHMFL's Predator and would have written a wrong `biotools_id`. §9.2 already
names predatoR as rejected; the query script enforces that by blocking the hit **verbatim and
case-sensitively, before** the exact-match test. Predator is `searched_none`, agreeing with the
seed. Proof that a registry name-match is not identity proof (§9.2) — the guard is the ruling,
not the match.

| Tool | papers | biotools | rrid |
|---|---:|---|---|
| PetroOrg | 88 | searched_none | not_attempted |
| Predator | 37 | searched_none (predatoR = different tool, rejected) | not_attempted |
| EnviroOrg | 12 | searched_none | not_attempted |
| R | 17 | searched_none | not_attempted (shortlist) |
| Xcalibur | 16 | searched_none | **has_id SCR_014593** |
| MATLAB | 11 | searched_none | not_attempted (shortlist) |
| ProSight Lite | 7 | has_id | not_attempted |
| ggplot2 | 4 | has_id | not_attempted |
| QIIME2 | 4 | has_id | not_attempted |
| DADA2 | 3 | has_id | not_attempted |
| vegan | 3 | has_id | not_attempted |
| GraphPad Prism | 2 | searched_none | not_attempted (shortlist) |
| MetaMorpheus / Proteoform Suite | 2 | has_id | not_attempted |
| Mascot | 1 | has_id | not_attempted |
| MaxQuant / ProteoWizard / MSConvert / UniDec / ClipsMS / PyC2MC / MSAlign / ImageJ / Fiji / IGV | — | has_id | not_attempted |
| CoreMS / ProSightPC / ProSight PD / TDPortal / TDValidator / Fragariyo | — | searched_none | not_attempted |

### 9.5 Normalization order (Part 5)

> **Two steps below were specified in review, lost in the migration into this doc, and took a
> session each to rediscover from the symptoms:** step 0 (©/™/(c) strip) and step 4.5
> (descriptor-strip). Both were part of the original step-5 spec. **Both are now BUILT and
> recorded here so the doc matches the code.** A rule that lives only in a review thread is a
> rule the next person pays for twice.

0. **Symbol-strip — ©, ®, ™, `(c)`, and a standalone trailing `TM`. BUILT 2026-07-16.**
   Runs first, before vendor/descriptor/version. Was previously done *only* inside the
   parenthetical handler, which is why `Custom software (PetroOrg © )` resolved while a bare
   `PetroOrg ©` did not — the same rule applied in one place and not the other. Now in **one**
   place. Covers `PetroOrg ©`, `PetroOrg©`, `PetroOrg TM`, `PetroOrg(c)`, `Xcalibur TM`,
   `MATLAB ™ v6.9`, `EnviroOrg TM software`, `ReSpect™ algorithm`.
1. **Ref-strip — STEP 1, before anything else.** Strip runs of comma-separated bare integers at
   a string/delimiter boundary when followed by a letter-initial token. `8,76 Predator data
   station` → `Predator data station`; `…, 66 Intact Mass (…)` → `…, Intact Mass (…)`. No
   regression on `2.3-177901/2.3.1.1782`, `R i386 2.15.2`, or model numbers (`8900 QQQ`
   untouched — mid-string, not at a boundary).
   - **Trailing-ref gap — UNBUILT.** Leading refs only. Trailing refs (`ProSight Lite 39`,
     `PetroOrg software 67`, `Predator analysis 37 and PetroOrg 38`) need a separate
     trailing-bare-integer strip. Not built.
2. Mask parens (protect `,`/`;` inside `()`).
3. Split on `;`, then top-level `,` / ` and ` / ` or ` at paren-depth 0.
4. Vendor-strip → `vendor` property.
   - **The vendor list is for VENDORS — parties that sell or ship the tool.** RULED
     2026-07-16 (Diya). Protein Metrics *sells* Intact Mass, so `Intact Mass (Protein Metrics)`
     strips cleanly. **Author institutions are attributions, not vendors, and there is no
     attribution-strip.**
   - **Known case — `UniDec (Oxford University, UK)` (`10.1021/jasms.0c00036`): stays REVIEW.**
     Oxford is UniDec's *home institution*; putting it on `VENDORS` would assert Oxford vends
     UniDec, which is false. One token is not worth a wrong rule. **Do not re-litigate.**
   - Known bug, not fixed: the vendor regex swallows an opening paren, so
     `ProSight PD ™ (Thermo Fisher Scientific PD version 2.1, ProSightPC version 4.0)` cleans to
     the unbalanced `ProSight PD ™ PD , ProSightPC version 4.0)`. It still routes REVIEW, as
     ruled, so nothing wrong reaches the graph.
4.5. **Descriptor-strip — RESTORED 2026-07-16 (Diya).** Was in the original spec and lost in
   the migration into this doc; a restoration, not a new ruling. Strip trailing descriptors
   from an explicit short list only: **`software` / `analysis` / `package` / `data station` /
   `algorithm`**. Applied iteratively (`Predator software package` → `Predator`).
   - **Protected — never stripped**, because the descriptor is part of the tool's real name:
     `Compound Discoverer`, `Proteoform Suite`, `ProSight Lite`, `Data Analysis`. The live case
     is `Data Analysis`: it must keep its `Analysis` while `Predator Analysis` loses its own.
     §9.7's `software_mentioned_raw` strings are protected too — stripping `software` off
     `in-house software` would silently drop them from the pub-property bucket.
   - §9.8's accepted `Petrorg data processing software → PetroOrg` is this strip done by hand.
     It stays as a recorded decision; the pipeline now handles the class.
   - **Unreachable map keys — a map key written in PRE-normalization form can never match**,
     because step 4/4.5 rewrites the token before the lookup sees it. **Mnova is the live case**
     (reported 2026-07-16, not ruled): the corpus has exactly one string, `Mnova NMR software`
     (`10.1002/2017JG004343`). Descriptor-strip does the right thing — it removes `software` (a
     descriptor) and correctly leaves `NMR` (not one) — yielding `Mnova NMR`. The map holds
     `mnova` and `mnova nmr software`; **neither is what arrives**, so Mnova mints zero from two
     keys. **This is a missing map key, not a descriptor-strip gap.** The open question is a
     naming one: is `Mnova NMR` the Mestrelab product (its own node) or `Mnova` with an `NMR`
     qualifier? Same class: `enviroorg software`, `bruker data analysis`,
     `bruker daltonics data analysis` — all unreachable because vendor/descriptor strip fires
     first.
   - **SECOND PASS — BUILT 2026-07-16 (Diya). Step 4.5 runs AGAIN after step 5.**
     Step 4.5 sits before version-extract, so a descriptor that is not *trailing* because a
     version follows it survives the first pass: `JMP software (v. 7.0.1)` → step 5 lifts the
     version → `JMP software` → the descriptor is trailing only *now*. Deferred once as 4
     cosmetic tokens; **F5 showed it costs a node** (JMP minted or its version survived, never
     both), so it is a real gap, not cosmetic. **12 tokens move**, including
     `Thermo Xcalibur software (version 3.0.63)` → Xcalibur `3.0.63`,
     `PetroOrg N-18.3 Software` → PetroOrg `N-18.3`, `Predator Analysis (version 4.1.9)` →
     Predator `4.1.9`, `R software v.3.6.2` → R `3.6.2`.
     **Protected names are re-checked on the second pass** (the strip returns early on them),
     so `Data Analysis` keeps its `Analysis` — verified: DataAnalysis ×5, Compound Discoverer
     ×1, Proteoform Suite ×3, ProSight Lite ×5, unchanged.
5. Version-extract → edge `version`.
- **Counts affected by KI-5** (`docs/KNOWN_ISSUES.md`): 02d drops multi-tool values on span
  coverage, so the **144 genuine negatives is inflated by up to 51 papers**. The numbers below
  are reported as measured and are **not adjusted** — a patched count reads as a measured one.
- Token totals (this splitter): 486 mentions / 333 distinct tokens from 233 bundles / 191
  distinct bundle strings. Counts are unit-dependent — final tallies firm up at build.

### 9.6 Separators and vendor canonicalization (Part 4)
- **`/` is NOT a separator.** Its only 4 corpus occurrences are `2.3-177901/2.3.1.1782`
  (dual-version), `H/C and O/C` (chemistry ratio), `Gas chromatography/mass spectrometry`
  (method name), `nf-core/ampliseq` (pipeline name) — never two distinct tools.
- **Bruker canonicalization** (8 distinct strings): `Bruker Data Analysis` / `DataAnalysis` /
  `Bruker Daltonics Data Analysis` collapse to one `software:dataanalysis` (vendor Bruker);
  `SmartFormula` is its own node; `Compound Discoverer` its own node (vendor Thermo).

#### 9.6a Suite/component tokens — MINT THE COMPONENT (RULED 2026-07-16, Diya)
*Recorded here rather than in §9.5 or §9.7 because §9.6 is the section that already governs
**what is and is not a separator** and **what collapses to one node** — and this ruling is both.*

**A token naming a suite and its component, or a host and its toolbox, is ONE tool reference,
not two. Mint the COMPONENT — that is what the paper actually ran.** The suite is **not** minted
as a peer node: the paper did not use them as peers. The verbatim raw string is kept as an
**alias** on the node.

| verbatim token | → node | why |
|---|---|---|
| `ProteoWizard MSConvert` | **MSConvert** | msConvert ships inside ProteoWizard |
| `Fiji ImageJ using the Plot Pro fi les function` | **Fiji** | Fiji is the ImageJ distribution actually run; trailing function phrase stripped |
| `drEEM toolbox for MATLAB` | **drEEM** | host/toolbox |
| `drEEM toolbox in MATLAB` | **drEEM** | host/toolbox |
| `Matlab with the drEEM toolbox` | **drEEM** | host/toolbox |

- **`  ` is NOT a separator either — do NOT add a space-split rule.** It would shatter these into
  peer nodes and assert a paper used both, which is **false**. This is a **token-level canonical
  mapping**, not a splitter change. (Same spirit as `/` above.)
- **CONTRAST — `MIDAS Predator Analysis` is NOT this shape.** MIDAS and Predator are
  **coordinate** tools (predecessor and successor, §9.3), so they are two references and split
  into two rows via the adjacent-pair rule. **Suite/component = one node; coordinate tools =
  two.** That distinction is the whole ruling.
- **NOT covered:** `ProSight PD ™ (Thermo Fisher Scientific PD version 2.1, ProSightPC version
  4.0)` — stays REVIEW under the n=1 ruling. No rule built.
- **Upstream note:** these are not splitter failures. 02d returned each as a **single grounded
  extraction**, verbatim from the paper (`ProteoWizard MSConvert`, `grounded=True`,
  `char_span=[22117, 22139]` — 22 chars, exactly the string's length, `MATCH_EXACT`). The paper
  writes them contiguously; the extraction is faithful.

#### 9.6b MSAlign ≠ MS-Align+ (RULED 2026-07-16, Diya)
`MSAlign` and `MS-Align+` are **different tools** and split into two rows.
- **`MSAlign`** — bio.tools `msalign`, *"Aligns LC-MS and LC-MS/MS datasets…"*
  (`ms-utils.org/msalign`). **No corpus string refers to it.** Its proposed ID has no referent.
- **`MS-Align+`** — the top-down search engine. `10.1002/pmic.201800361`, bundle
  `Proteoform Suite; MetaMorpheus; MSAlign +` — three top-down tools; raw extraction
  `[20] value='MSAlign +'`, `grounded=True`, `char_span=[59560, 59569]`, `MATCH_EXACT`.
  **`biotools_id: null`, `biotools_status: not_attempted`** — never queried under this name, so
  `proposed` would be wrong.
- **RESOLVED 2026-07-17 (Veronika) — the string is authentic.** The paper writes `MSAlign + , [88]`
  — **no hyphen**. The earlier hypothesis that the spacing was a **Docling artifact** (`Plot Pro fi
  les`, `Thermo Scienti fi c`) is **refuted**: `MSAlign +` is what the paper actually says.
  `biotools_id` stays **null**. **OPEN, not ruled:** whether `MSAlign +` is *MS-Align+* written
  without a hyphen, or a different tool, is unresolved — recorded here, not decided.

### 9.7 Routing (Part 6)
- **MINT** as Software: tools with a clear proper name.
- **ROUTE OUT** to `docs/method_field_handoff.md`: the 11 algorithms and the method misroutes.
- **PRECEDENCE — RULED 2026-07-16 (Diya): a NAMED route-out beats a GENERIC reject.**
  The REJECT clause below ends with *"method-description phrases"* — a generic catch-all. When a
  string is **named, with a DOI, in `method_field_handoff.md`**, that specific row wins and the
  string **routes out**; the generic clause does not reject it. **Enforced structurally**, not
  by convention: the ROUTE_OUT check runs **before** the REJECT clauses in `classify()`.
  - **First application (the case that forced the rule):** `Atomic Force Microscopy Molecular
    Imaging` and `GPC analysis with polystyrene standards for calibration` — both named in the
    handoff with DOIs, both matched by the generic clause. **Both route out; both are methods.**
    Keys carry the handoff's spelling *and* the verbatim corpus spelling, which is longer; the
    raw string is kept verbatim on the record. This will collide again — the clause is generic
    by design and the handoff keeps growing.
- **REJECT (reasons):** `N/A`; bare `fouriertransform`; `Peak lists (uncalibrated…)`; `known
  databases 35, 36`; `AI and elemental ratios…`; method-description phrases; the book `Methods
  of Soil Analysis. Part 3`.
- **`software_mentioned_raw` (Publication property — transform-dependent, lands with the
  build):** generic-but-real mentions too vague to mint — `in-house software`, `custom
  in-house software`, `Custom software`, `homemade Python scripts Jupyter Notebooks`,
  `Multiple Analytical Tools`.
- **Over-drop guard:** OCR/spelling variants of real tools are NOT rejected — they go to the
  confirm bucket (§9.8), never auto-applied. FUZZY PROPOSES, HUMAN DISPOSES.
- **Databases → RULED 2026-07-16 (Diya): their own node type. NOT Software.**
  **RULED, NOT IMPLEMENTED.** *(History: this was previously recorded here as HOLD for David.
  Diya ruled it herself; it no longer awaits him and will not appear under `## Decisions —
  (David)`.)*
  - **Why not Software:** *you search against SILVA, you don't run it.* A
    `USES_SOFTWARE → SILVA` edge would **assert something false**. Modelling call, not an
    availability one — **both bio.tools and SciCrunch register databases**, so a real
    identifier is available either way; the identifier was never the question.
  - **Corpus scope: SILVA, RDP** (Ribosomal Database Project)**, COLMAR.** These three
    **stay in REVIEW until the node type is built** — there is nowhere to send them yet.
  - **BLAST and GTDB-Tk are tools and mint as Software** (already ruled, above). **GTDB**
    (the database) **does not appear as a bare string** in the corpus.
  - **What building it needs — all UNDECIDED.** Listed so the next person does not re-derive
    the question set. **Nothing here is a proposal.**

    | Question | Status |
    |---|---|
    | **Node type name** | undecided — `Database`? `ReferenceDatabase`? Something narrower? |
    | **Identifier scheme** | undecided. §Universal Identity requires one. Registry-derived (bio.tools / RRID) or a local slug? If registry-derived, identity becomes contingent on a lookup — the failure mode §9.1 rejected for Software. |
    | **Relationship + verb** | undecided. `USES_SOFTWARE` is wrong (that is the whole ruling). Direction and subject also undecided: Publication → Database? Method → Database? |
    | **Six universal provenance properties** | not applied. §Universal Provenance (`source_type`, `confidence`, `extracted_at`, `evidence_note`, `source_id`, `schema_version`) is mandatory for every node; the values for a database node are undecided — `source_type` would presumably be `llm_extraction` for these three, but that is not ruled. |
    | **03 normalize** | undecided — is there a CV to canonicalize against (§9.2's *registry exists → transform enriches; CV exists → 03 canonicalizes*), or is 03 a pass-through? |
    | **04 validate** | undecided. 04 is not built. |
    | **05 load** | undecided. 05 is not built; a Neo4j constraint would be needed in `scripts/db.py`. |
    | **Versioning** | undecided — SILVA releases are versioned (e.g. 138.1). Is that identity, a property, or an edge fact? §9.1's Software answer (edge fact) is **not** automatically the database answer. |

### 9.8 CONFIRM BUCKET — Diya's calls (proposals, not applied)
FUZZY PROPOSES, HUMAN DISPOSES. These are transform inputs awaiting sign-off, not facts.

| Verbatim string | papers | proposed | evidence | recommendation | decision |
|---|---:|---|---|---|---|
| `Xcaliber` | 1 (10.1021/ef100149n) | → Xcalibur | one-char OCR/spelling variant of Xcalibur | accept | ACCEPT |
| `Petrorg data processing software` | 1 (10.1029/2025JG008931) | → PetroOrg | case/descriptor variant of PetroOrg | accept | ACCEPT |
| `8,76 Predator data station` | 1 (10.1021/acs.energyfuels.0c03349) | → Predator | ref-digits `8,76` + "Predator data station" | accept (ref-strip §9.5) | ACCEPT |
| `CERES Processing` | 1 (10.1021/jasms.4c00120) | → REVIEW | named self-written MatLab GUI; not clearly a mintable tool | review, don't auto-mint | PENDING — David |
| `MaxQuant software at standard settings` | 1 (10.1016/j.str.2017.08.002) | → MaxQuant | real use; descriptor-strip removes `software` but leaves the trailing prepositional phrase `at standard settings`, so it never resolves. A rule stripping `at standard settings` would be far riskier than one confirm. (KI-10 W3) | confirm the string, invent no rule | **PENDING — Diya** |
| `MetaMorpheus 26` | 1 (10.1021/acs.jproteome.0c00403) | → MetaMorpheus | real use; `26` is a trailing reference and the trailing-ref strip is UNBUILT (D2, §9.5 step 1). Does **not** re-rule D2 — §9.8 is how the bucket compensates for gaps the pipeline leaves open. (KI-10 W3) | confirm the string, invent no rule | **PENDING — Diya** |

> **The two rows added 2026-07-17 (X3)** are the KI-10 W3 blocked tokens — real uses whose edges
> never minted. Recorded here as **one-confirm-per-string proposals, NOT applied**: they mint their
> edges on the **next transform run**, which is **after 05**, not now. FUZZY PROPOSES, HUMAN DISPOSES.

### 9.9 RRID hand-verify shortlist — Diya
Hand-verify on scicrunch.org and add to the constant map: **R** (17 papers), **MATLAB** (11),
**GraphPad Prism** (2). Why these three: each has **no bio.tools ID** and is high-mention, so
the RRID is its only external identifier. Why not the other ~16: they either already carry a
bio.tools ID or have too few mentions to justify manual effort — `not_attempted`/null is
sufficient and honest (§9.3). Xcalibur is already verified (SCR_014593).
