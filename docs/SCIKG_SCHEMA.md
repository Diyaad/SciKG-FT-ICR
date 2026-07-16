# SciKG Schema v1.0

The authoritative specification for what enters the SciKG knowledge graph.
Every node type, every relationship type, every property is defined here. If 
real-world data does not fit, raise it for review — do not silently extend 
the schema.

**Status:** v1.0 active  
**Last updated:** 2026-06-29  
**Database:** Neo4j (Aura Free tier; Community Edition as fallback)  
**Supersedes:** docs/archive/KNOWLEDGE_GRAPH_DESIGN.md  
**Schema version property:** every node and relationship carries 
`schema_version: "v1.0"`

---

## How to Read This Document

The schema is organized by entity type. Each section defines:
- The Neo4j label
- The identifier strategy
- Properties marked M (mandatory), R (recommended), O (optional)
- The source — which of the 5 data sources contributes each property
- Standards alignment

Relationship types follow node definitions. Normalization rules and 
validation rules are at the end.

### The 5 data sources contributing to v1.0

| # | Source | Contributes |
|---|---|---|
| 1 | CrossRef + OpenAlex API | Publication, Researcher, Institution, Journal, Grant, Funder |
| 2 | MagLab CSV (806 papers) | Publication corpus, Researcher, Facility, Instrument, Dataset, Funder |
| 3 | Web Applications Group export | Publication cross-validation |
| 4 | Manual annotations (8 papers) | Method, Sample, Protein, Organism, Modification, Software |
| 5 | RAW files (46 files) | RawDataFile, Instrument, Software, Sample, Researcher |

---

## Neo4j Implementation

This schema maps to Neo4j as follows:

- **Each entity type → a Neo4j label** (e.g., `:Publication`, `:Researcher`)
- **Each relationship type → a Neo4j relationship** (e.g., `:AUTHORED_BY`)
- **Identifier properties → uniqueness constraints** created at database setup
- **Relationship properties → key-value pairs on edges** (e.g., 
  `author_sequence` on `AUTHORED_BY`)
- **All provenance properties** are duplicated on every node and every 
  relationship — Neo4j does not enforce inheritance

### Cypher constraints (run at database setup via `scripts/db.py`)

```cypher
// Every node keys on a single top-level `identifier` (namespace:value).
CREATE CONSTRAINT publication_identifier  FOR (p:Publication)  REQUIRE p.identifier IS UNIQUE;
CREATE CONSTRAINT researcher_identifier   FOR (r:Researcher)   REQUIRE r.identifier IS UNIQUE;
CREATE CONSTRAINT institution_identifier  FOR (i:Institution)  REQUIRE i.identifier IS UNIQUE;
CREATE CONSTRAINT journal_identifier      FOR (j:Journal)      REQUIRE j.identifier IS UNIQUE;
CREATE CONSTRAINT grant_identifier        FOR (g:Grant)        REQUIRE g.identifier IS UNIQUE;
CREATE CONSTRAINT funder_identifier       FOR (f:Funder)       REQUIRE f.identifier IS UNIQUE;
CREATE CONSTRAINT facility_identifier     FOR (f:Facility)     REQUIRE f.identifier IS UNIQUE;
CREATE CONSTRAINT instrument_identifier   FOR (i:Instrument)   REQUIRE i.identifier IS UNIQUE;
CREATE CONSTRAINT dataset_identifier      FOR (d:Dataset)      REQUIRE d.identifier IS UNIQUE;
CREATE CONSTRAINT method_identifier       FOR (m:Method)       REQUIRE m.identifier IS UNIQUE;
CREATE CONSTRAINT sample_identifier       FOR (s:Sample)       REQUIRE s.identifier IS UNIQUE;
CREATE CONSTRAINT protein_identifier      FOR (p:Protein)      REQUIRE p.identifier IS UNIQUE;
CREATE CONSTRAINT organism_identifier     FOR (o:Organism)     REQUIRE o.identifier IS UNIQUE;
CREATE CONSTRAINT modification_identifier FOR (m:Modification) REQUIRE m.identifier IS UNIQUE;
CREATE CONSTRAINT software_identifier     FOR (s:Software)     REQUIRE s.identifier IS UNIQUE;
// RawDataFile: identifier (rawfile:{filename}) is NOT globally unique across the
// two RAW sources; global uniqueness is enforced on the checksum instead.
CREATE CONSTRAINT rawfile_sha256          FOR (r:RawDataFile)  REQUIRE r.sha256_hash IS UNIQUE;
```

---

## Naming Conventions (Required)

- **Property names:** snake_case (e.g., `publication_year`, `is_nhmfl_author`)
- **Entity labels:** PascalCase (e.g., `Publication`, `RawDataFile`)
- **Relationship types:** SCREAMING_SNAKE_CASE (e.g., `AUTHORED_BY`, 
  `USES_INSTRUMENT`)
- **Identifiers:** lowercase namespace + `:` + value
  - `doi:10.1021/acs.analchem.5c06165`
  - `pub:maglab:18517`
  - `researcher:lastname_f_2019`
  - `facility:icr_facility`
  - `instrument:raw:21t_icr`
- **PSI-MS IDs:** uppercase, `MS:XXXXXXX` format
- **UNIMOD IDs:** uppercase, `UNIMOD:XX` format
- **ORCID:** four-group format with dashes, `0000-0000-0000-0000`
- **ROR:** full URL form, `https://ror.org/XXXXXXXXX`
- **NCBI Taxonomy:** integer

---

## Universal Identity

Every node carries a single top-level `identifier` (lowercase `namespace:value`)
— this is THE required, unique identity field for **every** node type, and it is
100% populated on disk across all 10 populated types. The on-disk key name is
`identifier`, **not** `id`: where a per-node property table below shows an `id`
row, it refers to this top-level `identifier`.

Domain keys — `doi`, `issn`, `accession`, `filename`, `ror_id` — live **inside
`properties`**, not as the identity field. The per-node "Identifier:" lines
describe how the `identifier` *value* is minted (e.g. `doi:{doi}` or
`pub:maglab:{id}`); they are not separate fields. External-PID-preferred rules
are aspirational only: in the current data Researcher never uses `orcid:`,
Journal never `issn:`, Software/Instrument never `ms:` — all use minted internal
PIDs.

**Uniqueness:** `identifier` is unique for every type **except `RawDataFile`**,
whose `rawfile:{filename}` value is not globally unique across the two RAW
sources (64 PXD cross-deposits share filenames). RawDataFile global uniqueness is
enforced on `sha256_hash` instead (see that node).

**One type spans multiple files:** `Dataset` records live in **two** files —
`datasets.jsonl` (CSV) and embedded in `rawfiles_pxd.jsonl` (32 PXD datasets).
Identity, uniqueness, and dangling-reference checks must scan **all** entity
files, not assume one file per type.

---

## Universal Provenance Properties

Every node and every relationship carries these six properties. This is 
what makes the graph FAIR (R1.2) and PROV-O-aligned.

| Property | Type | Allowed values | PROV-O mapping |
|---|---|---|---|
| `source_type` | string | `api`, `csv`, `manual_annotation`, `fisher_py`, `merged_csv_foxden`, `llm_extraction` | `prov:wasGeneratedBy` |
| `confidence` | string | `high`, `medium`, `low` | — |
| `extracted_at` | ISO 8601 | `2026-06-29T14:00:00Z` | `prov:generatedAtTime` |
| `evidence_note` | string | Free text, human-readable basis | — |
| `source_id` | string | DOI, MagLab Id, filename, annotation file path | `prov:hadPrimarySource` |
| `schema_version` | string | `v1.0` | — |

**Convention:** in Neo4j, these properties are stored directly on the 
node or relationship. They are not abstracted into a separate provenance 
object.

**Note on `source_type`:** this is provenance, not a query gate — do not use it
to hard-filter records. Values on disk: `csv`, `fisher_py`, `manual_annotation`,
and `merged_csv_foxden` (the 46 Thermo RawDataFiles). The PXD (6th) source reuses
`fisher_py` and is distinguished by file/prefix, not by `source_type`. `api` and
`llm_extraction` are defined but currently unused (source 1 and stage 02d are
dormant).

**Note on `confidence`:** the value reflects source trust (API and curated 
records are high; LLM extractions are medium), not factual accuracy of the 
value itself.

---

## Node: Publication

The central entity of the graph. Sources 1, 2, and 3.

**Conforms to:** DataCite 4.5, Bioschemas ScholarlyArticle 0.3, schema.org/ScholarlyArticle  
**Identifier:** `doi:{lowercase_doi}` when present; otherwise `pub:maglab:{maglab_id}`  
**Coverage:** Tier 1 — 806 papers from MagLab CSV; 17 of these are enriched 
with CrossRef metadata

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `doi` | string | M when present | CrossRef, CSV | Lowercased, no URL prefix |
| `maglab_id` | integer | M | CSV | Always present, even when DOI is null |
| `title` | string | M | CrossRef, CSV | |
| `publication_year` | integer | M | CrossRef, CSV | |
| `publisher` | string | M | CrossRef | |
| `resource_type` | string | M | derived | Default `"JournalArticle"` |
| `volume` | string | O | CrossRef, CSV | Kept as string (Excel corruption possible) |
| `issue` | string | O | CrossRef, CSV | Kept as string |
| `pages` | string | O | CSV | Kept as string |
| `abstract` | string | O | CrossRef | About 41% coverage |
| `month_published` | string | O | CSV | Month name |
| `maglab_significant` | boolean | O | CSV | Supervisor flag |
| `acknowledged_nsf_grant` | boolean | O | CSV | |
| `software_mentioned` | list[string] | O | annotation | Raw strings |
| `facilities_mentioned_raw` | array[string] | O | PDF (llm_extraction) | Verbatim facility/location strings from PDF extraction that are too generic to identify a specific organization (e.g. "the laboratory", "greenhouse facility", "Clinical Haematology Department"). Text-only provenance carried on the Publication; never resolved to a node, never an identifier or edge endpoint. Distinct from `CONDUCTED_AT` (→Facility) and `INVOLVES_INSTITUTION` (→Institution): those assert a real place; this preserves an unmintable mention without fabricating one. Two papers sharing such a string do NOT imply the same location. Rationale mirrors the controlled-vocabulary peripherals rule (record as text, not as a node). |
| `instruments_mentioned_raw` | array[string] | O | PDF (llm_extraction) | Verbatim instrument-adjacent strings from PDF extraction that the controlled vocabulary (controlled_vocabulary.md lines 50–54) excludes from Instrument nodes: LC/UPLC/nanoLC systems, ion sources, ICR cells, NanoMate, APPI Ion Max, MIDAS, GELFrEE. Text-only provenance carried on the Publication; never a node, never an identifier or edge endpoint. Implements the CV's explicit peripherals rule; mirrors `facilities_mentioned_raw`. Distinct from `USES_INSTRUMENT` (→Instrument), which asserts a real instrument node. |
| `software_mentioned_raw` | array[string] | O | PDF (llm_extraction) | Verbatim software strings from PDF extraction that are real but too generic to mint as a Software node (`in-house software`, `custom in-house software`, `Custom software`, `homemade Python scripts Jupyter Notebooks`, `Multiple Analytical Tools`). Text-only provenance carried on the Publication; never a node, never an identifier or edge endpoint. Distinct from `USES_SOFTWARE` (→Software), which asserts a real tool. Two papers sharing such a string do NOT imply the same tool. Mirrors `facilities_mentioned_raw` / `instruments_mentioned_raw`. **Active — on 5 publications (2026-07-16)**; ruled in `docs/pdf_transform_logic.md` §9.7. |
| `is_ground_truth` | boolean | M | derived | True for the 8 annotated papers |

### Source merge rule

When CrossRef and CSV both provide a field:
- **Bibliographic fields** (title, journal, year, volume, issue, abstract): 
  CrossRef wins
- **MagLab-specific fields** (maglab_id, NHMFL flags, dataset URLs, magnet 
  systems): CSV wins
- Disagreements logged to `data/processed/normalized/normalization_log.jsonl`

---

## Node: Researcher

Sources 1, 2, 4, and 5 (RAW file operator).

**Conforms to:** schema.org/Person, DataCite creator  
**Identifier:** `orcid:{value}` when present; otherwise `researcher:{family_lower}_{given_initial}_{first_pub_year}`

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `id` | string | M | derived | The primary identifier |
| `name_full` | string | M | CrossRef, CSV | Display form |
| `family_name` | string | M | CrossRef, CSV | |
| `given_name` | string | R | CrossRef, CSV | |
| `orcid` | string | O | CrossRef | `0000-0000-0000-0000` format |
| `initials` | string | O | RAW filename | e.g., "DSB" |
| `is_nhmfl_author` | boolean | O | CSV | |
| `is_corresponding_author` | boolean | O | CSV | |

### Email handling

Author emails from the **CSV** are MagLab-internal contact data and are 
**never** propagated to JSONL outputs or the graph (privacy rule).

Author emails from the **PDF** (corresponding author footnote, byline) 
are publicly published in the article and **may** be extracted in Phase 2 
when present. This applies only to emails appearing on the published page 
itself, not to any other PDF location.

### Entity resolution

1. If ORCID is present on both records, match by ORCID
2. Otherwise: match by `family_name` + first letter of `given_name` + 
   Jaccard overlap (≥ 0.3) of co-authors within the same paper
3. If still unresolved: mint a new node, send to 
   `data/processed/normalized/review_queue.jsonl`

---

## Node: Institution

Currently populated from PDF extraction (the 378-paper gap-field extraction,
`llm_extraction`). The CrossRef/CSV affiliation path (sources 1 and 2) is PLANNED.

**Status: Active — partially populated.** 62 Institution nodes on disk, all
from PDF extraction (`source_type: llm_extraction`): EXTERNAL organizations named
in article methods (analysis cores, contract labs, collaborating institutions),
linked to their publications via `INVOLVES_INSTITUTION` (89 edges). Grown from 21
(134-paper batch) to 62 by the 378-paper batch via an alias-aware exact+fuzzy
resolver (existing identifiers frozen, no duplicates). CrossRef (source 1)
affiliation extraction remains unbuilt, so the CrossRef/CSV population path and
the `AFFILIATED_WITH` (Researcher → Institution) edge are still PLANNED.

**Conforms to:** schema.org/Organization, DataCite affiliation, ROR  
**Identifier:** `ror:{ror_id}` when present; otherwise `inst:{normalized_name}`

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `id` | string | M | derived | |
| `name` | string | M | CrossRef, CSV | Canonical name |
| `aliases` | array of strings | O | ROR API + observed raw strings | Verified alternate names and acronyms for the same real-world entity (e.g. `["ETH Zürich", "Swiss Federal Institute of Technology Zurich", "ETHZ"]`). Populated from a matched ROR record's `aliases` + `acronyms` fields, PLUS auto-collected from the raw strings that actually resolved to this node. **Never LLM-generated** — a hallucinated alias would mis-resolve future mentions, so aliases come only from ROR (fetched) or actually-observed source strings. |
| `ror_id` | string | R | ROR API | The institution's ROR identifier (`https://ror.org/...`) when resolved via the ROR API. Enables future dedup with CrossRef-affiliation institutions that are also ROR-keyed. |
| `university` | string | O | CSV | |
| `department` | string | O | CSV | |
| `city` | string | O | CSV | |
| `state` | string | O | CSV | |
| `country` | string | O | CSV | |

**Note:** Per the MagLab CSV inventory, the University/Department/City/
State/Country columns are 0% populated in the corpus. These properties 
exist for future enrichment from CrossRef affiliations.

**Alias-aware matching:** when resolving a new institution string, check it
against existing nodes' `name` AND `aliases` before minting a new node, so variant
spellings/acronyms resolve to the existing node instead of duplicating it. Matching
behavior for the transform — not a Cypher constraint.

---

## Node: Journal

Sources 1 and 2.

**Conforms to:** schema.org/Periodical  
**Identifier:** `issn:{issn}` when present; otherwise `journal:{normalized_name}`

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `issn` | string | M when present | CrossRef | |
| `name` | string | M | CrossRef, CSV | Full name |
| `abbreviation` | string | O | CSV | |

---

## Node: Grant

Source 1 only.

**Status: PLANNED — not yet built.** Zero Grant nodes and zero `AWARDED_BY`
edges on disk. The Grant layer was collapsed: `FUNDED_BY` currently goes
Publication → Funder directly (see Relationships). Grant / `AWARDED_BY` remain
planned for when CrossRef (source 1) is extracted.

**Conforms to:** DataCite fundingReference  
**Identifier:** `grant:{funder_normalized}:{award_id}`

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `id` | string | M | derived | |
| `award_id` | string | M | CrossRef | |

When built, Funder details live on the Funder node, connected via `AWARDED_BY`.

---

## Node: Funder

Source 1 and controlled vocabulary.

**Conforms to:** schema.org/FundingAgency, DataCite Funder, ROR  
**Identifier:** `ror:{ror_id}` when present; otherwise `funder:{normalized_name}`

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `id` | string | M | derived | |
| `name` | string | M | CrossRef, controlled vocab | E.g., NSF, NIH |
| `ror_id` | string | R | controlled vocab | |
| `crossref_funder_id` | string | O | CrossRef | |

**Note:** Only canonical funders in `docs/controlled_vocabulary.md` become 
Funder nodes. Smaller acknowledgments stay as text on Grant.

---

## Node: Facility

Source 2.

**Conforms to:** schema.org/Place, ROR  
**Identifier:** `ror:{ror_id}` when present; otherwise `facility:{canonical_name}`  
**Coverage:** All 806 papers

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `id` | string | M | derived | |
| `name` | string | M | CSV | Canonical name, from "Facilities" column |
| `aliases` | array of strings | O | ROR API + observed raw strings | Verified alternate names and acronyms for the same facility (e.g. NHMFL variants: `["NHMFL", "National High Magnetic Field Laboratory", "ICR User Facility"]`). Populated from a matched ROR record's `aliases` + `acronyms` fields, PLUS auto-collected from the raw strings that actually resolved to this node. **Never LLM-generated** — a hallucinated alias would mis-resolve future mentions, so aliases come only from ROR (fetched) or actually-observed source strings. |
| `ror_id` | string | O | ROR API | The facility's ROR identifier (`https://ror.org/...`) when resolved via the ROR API. Enables future dedup with ROR-keyed institutions. |

**Note:** v1.0 corpus is dominated by "NHMFL ICR Facility."

**Alias-aware matching:** when resolving a new facility string, check it against
existing nodes' `name` AND `aliases` before minting a new node, so the many NHMFL
spelling variants resolve to the existing node instead of duplicating it. Matching
behavior for the transform — not a Cypher constraint.

---

## Node: Instrument

Sources 2, 4, 5, and PDF extraction (llm_extraction).

**Status: Active — populated.** 469 Instrument nodes on disk: 7 raw-form nodes from
02c/02f (RAW files, source_type csv/fisher_py) + 462 from the 378-paper PDF extraction
(source_type llm_extraction, raw-form `instrument:raw:{slug}`, `canonical_name`/`psi_ms_id`
null pending 03, `ontology_source` set: 164 PSI-MS · 292 null · 6 NMRCV). Linked to
publications via `USES_INSTRUMENT` (PDF adds 968 edges). The 7 existing identifiers are
frozen; PDF instruments resolve to them where matched (no duplicates). Peripherals the CV
excludes are recorded as `instruments_mentioned_raw` text on the Publication, not as nodes.

**Conforms to:** PSI-MS (MS instruments), nmrCV (NMR instruments); all other 
analytical instruments are label-only (no ontology)  
**Identifier:** `instrument:{normalized_canonical_name}` after normalization; 
during extraction, `instrument:raw:{normalized_raw_string}`

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `id` | string | M | derived | |
| `canonical_name` | string | M after normalization | controlled vocab | E.g., "21T FT-ICR MS" |
| `psi_ms_id` | string | O (nullable) | controlled vocab | On-disk field name (`properties.psi_ms_id`). Value space is generalized beyond PSI-MS: a PSI-MS accession (e.g. `MS:1003948`) **or** an nmrCV accession **or** `null` for non-MS/non-NMR instruments (TOC, ICP-MS, sequencers, microscopes, GC, …), which are label-only by design. |
| `ontology_source` | string | O | Active | Discriminator recording which ontology `psi_ms_id` draws from — one of `PSI-MS`, `NMRCV`, or null. **Emitted** by the PDF instrument transform on the raw-form nodes (PSI-MS for MS instruments, NMRCV for NMR, null for non-MS/non-NMR); 02c/02f nodes predate it (null). |
| `model_raw` | string | O | fisher_py | On-disk field (`properties.model_raw`). FOXDEN `instrument.model`. |
| `name_raw` | string | O | fisher_py | On-disk field (`properties.name_raw`). FOXDEN `instrument.name`. |
| `magnetic_field_tesla` | number | O | controlled vocab | Magnetic field strength in Tesla for magnet-based instruments (FT-ICR: 21.0, 14.5, 9.4). Makes magnet strength queryable/sortable rather than parseable-from-name. Populated by `03` from the controlled vocabulary, **not** asserted by the extraction transform. Null for non-magnet instruments. |
| `nmr_frequency_mhz` | number | O | controlled vocab | Proton (¹H) Larmor frequency in MHz for NMR spectrometers (900, 600, 400) — the conventional way NMR magnets are named. Populated by `03` from the controlled vocabulary. Null for non-NMR instruments. |

### Magnet field strength (Added 2026-07-15)

`magnetic_field_tesla` and `nmr_frequency_mhz` promote magnet strength from a
string trapped in the instrument name to a first-class numeric fact that is
queryable and sortable. The two are convertible by the ¹H gyromagnetic ratio
(42.577 MHz/T): 900 MHz = 21.1 T, 600 MHz = 14.09 T. NMR spectrometers are
conventionally named by their ¹H frequency, hence `nmr_frequency_mhz`; FT-ICR and
other magnet instruments by field in Tesla, hence `magnetic_field_tesla`.

**Undecided (do not assume either way):** whether `magnetic_field_tesla` is ALSO
filled for NMR instruments (via the conversion above) so a single uniform query
(e.g. "magnets ≥ 14 T") spans both FT-ICR and NMR. Pending decision.

Consistent with the raw-node design: the PDF transform mints `instrument:raw:{slug}`
with these fields null; `03` canonicalizes and fills them from the controlled
vocabulary. **Dependency (not addressed here):** the CV's instrument rows need a
field-strength / ¹H-frequency column for `03` to read. `controlled_vocabulary.md`
is a separate file and is NOT edited by this change — flag only.

### Ontology mapping (Established 2026-07-11)

Only mass-spectrometry (PSI-MS) and NMR (nmrCV) instruments are mapped to an 
ontology. Every other analytical instrument is a real node with 
`psi_ms_id = null` — a null value is **valid and expected**, not a validation 
failure. OBI/CHMO are not integrated. `04_validate.py` must accept null 
`psi_ms_id` for non-MS/non-NMR instruments. The on-disk field keeps the name 
`psi_ms_id` (matching the extractor output); the `ontology_source` field (now Active,
emitted by the PDF instrument transform) records which ontology a non-null value comes from.

### Notes on omitted properties

- **`magnet_system_raw` is NOT stored on Instrument.** The CSV's "Magnet 
  Systems" column is used during extraction to determine which Instrument 
  node a Publication should connect to (via `USES_INSTRUMENT`), but the 
  raw string itself is not preserved as a property. (Established 
  2026-06-29.)
- **`magnet_system_status` is NOT stored.** This column from the CSV is 
  excluded from the graph entirely. (Established 2026-06-29.)
- **`instrument_serial` is NOT stored.** Excluded to avoid hardware-tracking 
  detail not needed for any discovery question.

---

## Node: Dataset

Source 2.

**Conforms to:** DataCite Dataset, schema.org/Dataset, Bioschemas Dataset 1.0  
**Identifier:** `dataset:{repository_lower}:{accession_lower}`  
**Coverage:** 242 papers have at least one Dataset URL in the CSV.

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `id` | string | M | derived | |
| `repository` | string | M | derived | `OSF`, `MassIVE`, `ProteomeXchange`, `Zenodo`, `Other` |
| `accession` | string | M | CSV | Repository-specific |
| `url` | string | M | CSV | Original URL |
| `access_status` | string | O | derived | `open`, `restricted`, `unknown` |

### Normalization

- Multi-URL cells split on comma; whitespace stripped
- URL pattern determines repository
- ProteoSAFe task IDs without MSV accession are excluded
- Other URLs receive repository `"Other"` and a `manual_review_needed` flag

---

## Node: Method

Sources 4 and 5.

**Status: PLANNED — not yet populated.** Zero Method nodes on disk. The
annotation path (source 4) is dormant, and RAW-file activation is currently held
as the `activation_types_raw` property on RawDataFile (all 998 files), not yet
promoted to Method nodes (see Activation modeling below).

**Conforms to:** PSI-MS  
**Identifier:** `ms:{psi_ms_id}:{canonical_name_normalized}`  
**Coverage:** Tier 3 — 8 annotated papers + 46 RAW files (acquisition methods)

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `id` | string | M | derived | |
| `canonical_name` | string | M | controlled vocab | |
| `psi_ms_id` | string | M | controlled vocab | |
| `activation_types` | list[string] | O — PLANNED | controlled vocab | Intended: dissociation methods for the RAW file, e.g. `[CID, HCD]`. PSI-MS CV terms: CID `MS:1000133`, HCD `MS:1000422`, ETD `MS:1000598`, etc. **Not yet on Method** — currently lives as `activation_types_raw` on RawDataFile. |
| `tier` | integer | M | controlled vocab | 1 = primary MS (node), 2 = supporting (property only) |

### Rule

Only Tier 1 methods become Method nodes. Tier 2 methods (Western blot, 
RNA-Seq, etc.) are recorded as `supporting_methods` list property on 
Publication.

### Activation modeling (decided 2026-07-11 — PLANNED, not yet built)

The intended model: one Method node per RAW file, carrying that file's
activation/fragmentation techniques as the `activation_types` list, with
dissociation-method CV terms applied; fragmentation is **not** modeled as
per-scan-event nodes. This is **not yet built** — today the data lives as the
`activation_types_raw` property on every RawDataFile (998 files) and there are
zero Method nodes.

---

## Node: Sample

Sources 4 and 5.

**Conforms to:** SDRF-Proteomics characteristics  
**Identifier:** `sample:{canonical_name_normalized}`  
**Coverage:** Tier 3 — 8 annotated papers + 46 RAW files

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `id` | string | M | derived | |
| `canonical_name` | string | M | controlled vocab | |
| `sample_class` | string | O | controlled vocab | E.g., "Intact proteins" |
| `organism_strain` | string | O | RAW filename | E.g., "MG1655" |
| `sample_state` | string | O | RAW filename | E.g., "WCL" (= Whole Cell Lysate) |
| `growth_medium` | string | O | RAW filename | E.g., "M9" |
| `growth_date` | date | O | RAW filename | ISO 8601 |
| `growth_label` | string | O | RAW filename | Run letter from a series. Letters A through J have been observed. Position is not interpreted as ordering. |
| `prep_method` | string | O | RAW filename | E.g., "below30kDa" |

---

## Node: Protein

Source 4. Phase 2 will add from PDF extraction.

**Status: PLANNED — not yet populated.** Zero Protein nodes on disk; manual
annotation (source 4, Tier 3) is not extracted.

**Conforms to:** UniProt  
**Identifier:** `uniprot:{accession}` when present; otherwise 
`protein:{canonical_name_normalized}`  
**Coverage:** Tier 3 — 8 annotated papers

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `id` | string | M | derived | |
| `canonical_name` | string | M | controlled vocab | |
| `uniprot` | string | R | controlled vocab | 6-character accession |

---

## Node: (reference database) — NAME UNDECIDED

Source 6 (PDF extraction).

**Status: RULED, NOT IMPLEMENTED — 2026-07-16 (Diya).** Reference databases get **their own
node type. NOT Software.** Zero nodes on disk. **Nothing below is decided** — this section
records the ruling and the open question set so it is not re-derived. **No node type,
relationship, or property has been added; nothing is minted.**

**The ruling:** *you search against SILVA, you don't run it.* A `USES_SOFTWARE → SILVA` edge
would **assert something false**. This is a **modelling call, not an availability one** — both
bio.tools and SciCrunch register databases, so a real identifier is available either way.

**Corpus scope:** `SILVA`, `RDP` (Ribosomal Database Project), `COLMAR` — three strings, from
`software_tools` (source 6). They **stay in REVIEW** in
`data/processed/review/software_review.md` until this node type is built; there is nowhere to
route them. **BLAST** and **GTDB-Tk** are **tools** and mint as `Software`
(`docs/pdf_transform_logic.md` §9.7). **GTDB** (the database) does not appear as a bare string.

**Undecided — every item. No proposals:**

| Question | Bearing |
|---|---|
| **Node type name** | `Database`? `ReferenceDatabase`? Something narrower? |
| **Identifier** | §Universal Identity requires one. Registry-derived (bio.tools / RRID) or a local slug? Registry-derived would make identity **contingent on a lookup** — the failure mode rejected for Software (§9.1 / the Xcalibur collapse). |
| **Relationship + verb** | `USES_SOFTWARE` is excluded by the ruling. Verb, direction, and subject all open: Publication → ? Method → ? |
| **Universal provenance** | §Universal Provenance Properties is **mandatory for every node** — `source_type`, `confidence`, `extracted_at`, `evidence_note`, `source_id`, `schema_version`. Values for a database node are undecided (`llm_extraction` is the likely `source_type` for these three, but that is **not ruled**). |
| **03 normalize** | Is there a CV to canonicalize against, or is 03 a pass-through? (§9.2: *registry exists → the transform enriches; CV exists → 03 canonicalizes.*) |
| **04 validate** | Undecided; 04 is not built. |
| **05 load** | Undecided; 05 is not built. A Cypher constraint in `scripts/db.py` would be required. |
| **Versioning** | SILVA releases are versioned (138.1). Identity, property, or edge fact? Software's answer (edge fact, §9.1) does **not** automatically transfer. |

---

## Node: Organism

Sources 4 and 5.

**Status: PLANNED — not yet populated.** Zero Organism nodes on disk; the
annotation (source 4) and organism-from-RAW paths are not extracted.

**Conforms to:** NCBI Taxonomy, Bioschemas Taxon  
**Identifier:** `ncbitaxon:{taxonomy_id}`  
**Coverage:** Tier 3 — 8 annotated papers + 46 RAW files (E. coli MG1655)

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `id` | string | M | derived | |
| `canonical_name` | string | M | controlled vocab | Scientific name |
| `ncbi_taxonomy_id` | integer | M | controlled vocab | |

---

## Node: Modification

Source 4. Phase 2 will add from PDF extraction.

**Status: PLANNED — not yet populated.** Zero Modification nodes on disk;
manual annotation (source 4, Tier 3) is not extracted.

**Conforms to:** UNIMOD  
**Identifier:** `unimod:{id}`  
**Coverage:** Tier 3 — 8 annotated papers

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `id` | string | M | derived | |
| `canonical_name` | string | M | controlled vocab | |
| `unimod_id` | string | M | controlled vocab | `UNIMOD:XX` |

---

## Node: Software

Sources 4 and 5, and source 6 (PDF extraction).

**Status: Active — 51 distinct nodes (2026-07-16).** Split across two files by
SOURCE, following the Institution/Instrument convention: **1** node in
`entities/software.jsonl` (`software:xcalibur`, `fisher_py`, from the 02c/02f
Xcalibur migration) and **50** in `entities/pdf_entities.jsonl`
(`llm_extraction`, from the PDF software transform). Cross-file identifier
overlap is **0** and must stay 0: `03_normalize.py` dedups by identifier
**within a file only** (pass 2), so a cross-file collision would pass straight
through to 05's uniqueness constraint. `software:xcalibur` is therefore minted
by exactly one stage and skipped by the other.

**`category`** is `null` on all 50 PDF nodes: 02c derives it from RAW-file
context, and a PDF mention carries no source for it. Inventing values would be
fabricating metadata.

**`biotools_status: proposed`** on 16 nodes means an exact-name bio.tools hit
exists but **no human has confirmed it** — `biotools_id` stays `null` until
`docs/software_registry_review.md` returns. See §9.3.

**Conforms to:** schema.org/SoftwareApplication, PSI-MS (where assigned), 
Bioschemas ComputationalTool  
**Identifier:** `software:{canonical_name}` — always; never contingent on a
registry lookup. `psi_ms_id`, `rrid`, `biotools_id` are properties, not identity
(a later-assigned PSI-MS/registry ID must not move the identifier and re-point edges).  
**Status: Active — 1 node on disk** (`software:xcalibur`, collapsed from 7 versioned
fisher_py nodes on 2026-07-15). The PDF software transform that would populate the
rest is **RULED, NOT IMPLEMENTED** — see `docs/pdf_transform_logic.md` §9.  
**Coverage (measured 2026-07-15):** 934 distinct RAW files carry an `ACQUIRED_WITH`
edge to Software — 46 Thermo (02c) + 888 PXD (02f). Manual annotation (the 8
ground-truth papers) has contributed **0** Software entities to date; only the RAW
sources (5 and 6) have.

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `id` | string | M | derived | |
| `canonical_name` | string | M | registry, annotation | E.g., "Xcalibur" |
| `psi_ms_id` | string | O | PSI-MS (where assigned) | Property, NOT identity |
| `rrid` | string | O | SciCrunch (hand-verified map) | E.g., "SCR_014593"; null if none |
| `rrid_status` | enum | R | lookup | `has_id` \| `searched_none` \| `not_attempted` |
| `biotools_id` | string | O | bio.tools API (by name) | E.g., "biotools:prosight_lite"; null if none |
| `biotools_status` | enum | R | lookup | `has_id` \| `searched_none` \| `not_attempted` |
| `aliases` | list[string] | O | registry + observed raw strings | Never LLM-generated |
| `vendor` | string | O | registry, annotation | Thermo, Bruker, etc. |
| `category` | string | O | registry, annotation | `acquisition`, `processing`, `search`, `visualization` |

**Note:** Version is NOT part of identity — it is a per-usage fact carried on the
edge (`ACQUIRED_WITH.version`, `USES_SOFTWARE.version`). One node per tool
(`software:{canonical_name}`); a PSI-MS ID, when it exists, is recorded in
`psi_ms_id` but never in the identifier. Registry status is three-way
(`has_id`/`searched_none`/`not_attempted`) so an absent ID is distinguishable
from an unsearched one.

---

## Node: RawDataFile

Sources 5 and 6. One node per RAW file — 46 Thermo `.raw` files (source 5) plus
952 Blood Proteoform Atlas PXD files (source 6, local-only, gitignored).

**Conforms to:** SDRF-Proteomics, schema.org/DigitalDocument, SPDX 
(for checksum), PROV-O  
**Identifier:** `rawfile:{filename}` — human-readable, but **not** globally
unique (filenames repeat across the two RAW sources; 64 PXD cross-deposits
share filenames). Global uniqueness is enforced on `sha256_hash` instead.  
**Coverage:** 998 files (46 Thermo + 952 PXD; PXD dedups to 888 distinct nodes)

### Properties from manual filename metadata (data/raw/rawfile_metadata.csv)

| Property | Type | M/R/O | Notes |
|---|---|---|---|
| `filename` | string | M | Full name including `.raw` |
| `operator_initials` | string | M | E.g., "DSB" |
| `operator_name` | string | R | Full name of the operator (expands operator_initials) |
| `date_acquired` | date | M | ISO 8601 |
| `sample_organism_strain` | string | R | E.g., "EcoliMG1655" |
| `sample_state` | string | O | E.g., "WCL" (= Whole Cell Lysate). Confirmed 2026-06-29. |
| `sample_growth_medium` | string | O | E.g., "M9" |
| `sample_growth_date` | date | O | |
| `sample_growth_label` | string | O | Run letter assigned to a sample preparation series. Letters A through J have been observed in this corpus. Position in sequence is not interpreted as ordering. Confirmed 2026-06-29. |
| `sample_prep_method` | string | O | |
| `fractionation_method` | string | O | `GELFrEE`, `PEPPI`, or null |
| `processing_id` | string | O | E.g., "GF01", "F01" |
| `experimental_parameters` | string | O | E.g., "screen", "normMS1_typicalparams" |
| `run_number` | string | O | E.g., "01" |

### Properties from FOXDEN/fisher_py (data/raw/rawfiles_metadata/*.json)

| Property | Type | M/R/O | Notes |
|---|---|---|---|
| `instrument_name_raw` | string | R | FOXDEN `instrument.name` |
| `instrument_model_raw` | string | R | FOXDEN `instrument.model` |
| `acquisition_software_name` | string | R | FOXDEN `software.name` |
| `acquisition_software_version` | string | R | FOXDEN `software.softwareVersion` |
| `scan_count` | integer | O | FOXDEN `Number of scans` |
| `ms_run_time_minutes` | float | O | FOXDEN `MS Run Time (min)` |
| `acquisition_method_creator` | string | O | FOXDEN `instrumentMethod.Creator` |
| `acquisition_method_file` | string | O | E.g., `DSB_20200531_FT_Top2_CID_msnfills4_125min.meth` |
| `sha256_hash` | string | M | FOXDEN `spdx:checksum`. Global uniqueness key for RawDataFile (filenames are not unique across sources). |
| `activation_types_raw` | list[string] | O | Dissociation/activation techniques parsed from the RAW file, e.g. `[CID, HCD]`. Present on all 998 RawDataFiles today. Promotion to Method nodes is planned (see Method → Activation modeling). |
| `original_filepath` | string | O | FOXDEN `filepath` |
| `date_created` | datetime | R | FOXDEN `dateCreated` |
| `date_modified` | datetime | O | FOXDEN `dateModified` |

### Pending property

| Property | Type | M/R/O | Notes |
|---|---|---|---|
| `analyzed_in_doi` | string | O | PENDING — relationship NOT loaded until verification. See ANALYZED_IN below. |

### Source merge rule

Manual filename metadata and FOXDEN fields are merged into a single record 
per filename. Each property carries its own `source_type`:
- Manual filename metadata → `source_type: "manual_annotation"`
- FOXDEN → `source_type: "fisher_py"`

---

## Relationships

Every relationship carries the six provenance properties listed above.

### Tier 1 — Full corpus

| Relationship | Subject → Object | Source | Cardinality | Status |
|---|---|---|---|---|
| `AUTHORED_BY` | Publication → Researcher | CrossRef, CSV | MANY-MANY | Active |
| `AFFILIATED_WITH` | Researcher → Institution | CrossRef, CSV | MANY-MANY | PLANNED — no Institution nodes |
| `PUBLISHED_IN` | Publication → Journal | CrossRef, CSV | MANY-ONE | Active |
| `FUNDED_BY` | Publication → Funder | CrossRef, CSV | MANY-MANY | Active (direct to Funder — see note) |
| `AWARDED_BY` | Grant → Funder | CrossRef, controlled vocab | MANY-ONE | PLANNED — no Grant nodes |
| `CONDUCTED_AT` | Publication → Facility | CSV | MANY-MANY | Active |
| `INVOLVES_INSTITUTION` | Publication → Institution | PDF (llm_extraction) | MANY-MANY | Active |
| `USES_INSTRUMENT` | Publication → Instrument | CSV, annotations | MANY-MANY | Active |
| `HAS_DATASET` | Publication → Dataset | CSV | MANY-MANY | Active |
| `CITES` | Publication → Publication | CrossRef references | MANY-MANY | PLANNED — not extracted |

**FUNDED_BY goes Publication → Funder directly (383 edges).** The
originally-planned Grant layer (Publication → Grant → Funder via `AWARDED_BY`) is
not built — there are zero Grant nodes and zero `AWARDED_BY` edges. Grant /
`AWARDED_BY` remain PLANNED (see Grant node).

**INVOLVES_INSTITUTION links a Publication to an EXTERNAL institution its work
involved** — analysis cores, contract labs, and collaborating institutions
(e.g. a sequencing core, a national lab that ran a sample). Sourced from PDF
extraction (`source_type: llm_extraction`). It is distinct from `CONDUCTED_AT`,
which names the NHMFL/MagLab `Facility` where the work was *primarily* conducted,
and it does NOT replace `AFFILIATED_WITH` (Researcher → Institution): a
publication involves an institution; a researcher is affiliated with one. The
name follows the VERB_OBJECTNOUN present-tense convention and is the sibling of
`INVOLVES_ORGANISM`. Carries the six universal provenance properties like every
edge. Status is Active: the PDF facility transform populates it directly.

### Tier 3 — Annotated papers only

**All Tier 3 edges are PLANNED — not yet populated.** The manual-annotation
extraction (source 4) is dormant; zero of these edges exist on disk.
(RawDataFile → Software links exist instead via `ACQUIRED_WITH`, below.)

| Relationship | Subject → Object | Source | Cardinality | Status |
|---|---|---|---|---|
| `USES_METHOD` | Publication → Method | annotation | MANY-MANY | PLANNED |
| `ANALYZES_SAMPLE` | Publication → Sample | annotation | MANY-MANY | PLANNED |
| `ANALYZES_PROTEIN` | Publication → Protein | annotation | MANY-MANY | PLANNED |
| `INVOLVES_ORGANISM` | Publication → Organism | annotation, RAW | MANY-MANY | PLANNED |
| `STUDIES_PTM` | Publication → Modification | annotation | MANY-MANY | PLANNED |
| `USES_SOFTWARE` | Publication → Software | PDF (llm_extraction) | MANY-MANY | **Active — 280 edges** (2026-07-16) |

### RAW file relationships

| Relationship | Subject → Object | Source | Cardinality | Status |
|---|---|---|---|---|
| `COLLECTED_ON` | RawDataFile → Instrument | fisher_py | MANY-ONE | Active (998) |
| `OPERATED_BY` | RawDataFile → Researcher | manual annotation | MANY-ONE | Active (46, Thermo only) |
| `CONTAINS_SAMPLE` | RawDataFile → Sample | manual annotation | MANY-ONE | Active (46, Thermo only) |
| `ACQUIRED_WITH` | RawDataFile → Software | fisher_py | MANY-ONE | Active (934); property `version` (string, O) — per-acquisition version |
| `DERIVED_FROM` | RawDataFile → Dataset | fisher_py | MANY-ONE | Active (952, PXD) |
| `ANALYZED_IN` | RawDataFile → Publication | — | MANY-ONE | **PENDING** |

### DERIVED_FROM

`RawDataFile → Dataset`, 952 edges. Links each Blood Proteoform Atlas PXD RAW
file to the ProteomeXchange Dataset it was deposited under. The Dataset objects
are the 32 PXD Dataset nodes embedded in `rawfiles_pxd.jsonl` (not in
`datasets.jsonl`). Carries the six provenance properties (`source_type:
fisher_py`).

### ANALYZED_IN status

**PENDING — target publication not yet identified.** To be identified by 
inspecting RAW file FOXDEN JSONs for embedded DOI references after pipeline 
load (Week 5 task). Not loaded into v1.0 until verification.

### Relationship properties

| Relationship | Property | Type | Notes |
|---|---|---|---|
| `AUTHORED_BY` | `author_sequence` | integer | 1 = first author, 2 = second, etc. |
| `AUTHORED_BY` | `is_corresponding` | boolean | From CSV |
| `FUNDED_BY` | `award_acknowledgment_text` | string | Original acknowledgment string |
| `HAS_DATASET` | `relationship_type` | string | `primary`, `supplementary` |
| `CITES` | `reference_position` | integer | Position in reference list |

---

## Identifier Strategy

In order of preference:

1. **External persistent identifier** — DOI, ORCID, ROR, PSI-MS ID, 
   UniProt, NCBI Taxonomy ID, UNIMOD ID, Crossref Funder ID
2. **Composite key from existing identifiers** — e.g., 
   `{funder_doi}:{award_id}` for grants
3. **Minted internal PID** with type prefix — `pub:`, `researcher:`, 
   `inst:`, `dataset:`, `instrument:`, `sample:`

Internal PIDs are lowercase, underscored, and human-readable. Example: 
`researcher:lastname_f_2019`.

JSON-LD export format uses namespace prefix (`doi:10.1021/...`, 
`orcid:0000-...`, `ms:1003948`). Internal Neo4j storage may use bare 
values for query efficiency.

The ordering above is the *minting* preference for the `identifier` **value**.
On disk the identity is always the single top-level `identifier` field (see
Universal Identity); the external-PID-first tiers are aspirational and, in the
current data, mostly unrealized (Researcher/Journal/Software use minted internal
PIDs).

---

## Normalization Rules (applied by `03_normalize.py`)

1. **DOIs** — lowercased, no `https://doi.org/` prefix
2. **Instruments** — match raw CSV magnet system value against 
   `controlled_vocabulary.md` aliases; unresolved → `review_queue.jsonl`, 
   no node created
3. **Methods** — Tier 1 → Method nodes; Tier 2 → `supporting_methods` 
   text property on Publication
4. **Researchers** — ORCID first; then family name + initial + co-author 
   Jaccard ≥ 0.3
5. **Institutions** — ROR first; then normalized string match (lowercase, 
   no punctuation)
6. **Datasets** — split multi-URL cells, classify by URL pattern, reject 
   if no clean accession
7. **Software** — controlled vocab match; assign PSI-MS ID when available
8. **Emails and contact info** — never propagated to JSONL outputs or 
   the graph from the CSV

Unresolved values go to `data/processed/normalized/review_queue.jsonl` 
with a reason. Nothing is silently dropped. Every normalization decision 
is logged to `data/processed/normalized/normalization_log.jsonl`.

---

## Validation Rules (applied by `04_validate.py`)

A record fails validation and goes to `data/processed/validated/quarantine.jsonl` 
if any of these are true:

- A required property is missing
- DOI present but malformed (does not match `^10\.\d{4,}/.+`)
- ORCID present but malformed (not `0000-0000-0000-0000` format)
- Any of the 6 provenance properties is missing
- Relationship references a node that does not exist in entity tables
- `schema_version` ≠ `"v1.0"`

`data/processed/validated/validation_report.json` records counts of: 
passed, quarantined, by reason, by entity type.

---

## Out of Scope for v1.0

- `Workflow` as a node type
- `ProvenanceRecord` as a node type (provenance is properties, not nodes)
- `ASSOCIATED_WITH` as a generic catch-all relationship
- AI/LLM/RAG layer
- Streamlit UI or chatbot
- RDF serialization (Neo4j is the backend; JSON-LD export is post-load)
- PDF extraction (Phase 2 — stage `02d_extract_pdf.py`)
- Author emails from CSV (never propagated)
- `ANALYZED_IN` relationship loading (pending verification)

---

## Schema Change Process

Before any change to this schema:

1. Does it answer a question in `DISCOVERY_QUESTIONS.md` that v1.0 cannot?
2. Is the change captured in `REVIEW_LOG.md`?
3. Does it require migration of already-loaded records?
4. Does the controlled vocabulary support the new node or property?
5. Does the new entity have a persistent identifier strategy?

If any answer is "no," raise it for review before extending the schema.

**Versioning:** v1.0 is the live version and all records on disk carry
`schema_version: "v1.0"` — including the PXD, DERIVED_FROM, and other additions
reconciled here. Current in-flight work stays under v1.0 (schema and data are
kept in sync in place); do **not** bump to v1.1 or re-tag data for these changes.
`04_validate.py` requires `schema_version == "v1.0"`. A version bump is reserved
for a future breaking change that requires migrating already-loaded records.

---

## References

- Standards alignment table: `docs/FAIR_PRINCIPLES.md`
- Controlled vocabulary values: `docs/controlled_vocabulary.md`
- Questions the graph must answer: `docs/DISCOVERY_QUESTIONS.md`
- Removed concepts and design history: `docs/archive/KNOWLEDGE_GRAPH_DESIGN.md`
- Verified facts vs proposed: `docs/VERIFIED_FACTS_AND_ASSUMPTIONS.md`
- Repository audit: `docs/REPO_AUDIT.md`
