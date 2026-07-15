# PDF-transform — FACILITY field logic (build reference)

Build note to lift into the consolidated PDF-transform script once all six fields
(instrument, ionization, software, dataset, sample, facility) are built to the same
pattern. Not authoritative schema — see `docs/SCIKG_SCHEMA.md`. Working impl lives in
scratch: `finalize_pdf_facility.py` (to be promoted to `scripts/`).

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
- **TODO**: promote scratch `finalize_pdf_facility.py` into `scripts/` as a
  consolidated PDF-transform stage once instrument / ionization / software / dataset /
  sample fields are built to this same four-way pattern. Stale line to fix then:
  Institution node section still says "Sources 1 and 2." above the status block —
  nodes now come from PDF extraction.

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
