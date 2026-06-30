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
CREATE CONSTRAINT publication_doi    FOR (p:Publication)  REQUIRE p.doi IS UNIQUE;
CREATE CONSTRAINT researcher_id      FOR (r:Researcher)   REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT institution_id     FOR (i:Institution)  REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT journal_issn       FOR (j:Journal)      REQUIRE j.issn IS UNIQUE;
CREATE CONSTRAINT grant_id           FOR (g:Grant)        REQUIRE g.id IS UNIQUE;
CREATE CONSTRAINT funder_id          FOR (f:Funder)       REQUIRE f.id IS UNIQUE;
CREATE CONSTRAINT facility_id        FOR (f:Facility)     REQUIRE f.id IS UNIQUE;
CREATE CONSTRAINT instrument_id      FOR (i:Instrument)   REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT dataset_id         FOR (d:Dataset)      REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT method_id          FOR (m:Method)       REQUIRE m.id IS UNIQUE;
CREATE CONSTRAINT sample_id          FOR (s:Sample)       REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT protein_id         FOR (p:Protein)      REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT organism_id        FOR (o:Organism)     REQUIRE o.id IS UNIQUE;
CREATE CONSTRAINT modification_id    FOR (m:Modification) REQUIRE m.id IS UNIQUE;
CREATE CONSTRAINT software_id        FOR (s:Software)     REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT rawfile_filename   FOR (r:RawDataFile)  REQUIRE r.filename IS UNIQUE;
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

## Universal Provenance Properties

Every node and every relationship carries these six properties. This is 
what makes the graph FAIR (R1.2) and PROV-O-aligned.

| Property | Type | Allowed values | PROV-O mapping |
|---|---|---|---|
| `source_type` | string | `api`, `csv`, `manual_annotation`, `fisher_py`, `llm_extraction` | `prov:wasGeneratedBy` |
| `confidence` | string | `high`, `medium`, `low` | — |
| `extracted_at` | ISO 8601 | `2026-06-29T14:00:00Z` | `prov:generatedAtTime` |
| `evidence_note` | string | Free text, human-readable basis | — |
| `source_id` | string | DOI, MagLab Id, filename, annotation file path | `prov:hadPrimarySource` |
| `schema_version` | string | `v1.0` | — |

**Convention:** in Neo4j, these properties are stored directly on the 
node or relationship. They are not abstracted into a separate provenance 
object.

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

Sources 1 and 2.

**Conforms to:** schema.org/Organization, DataCite affiliation, ROR  
**Identifier:** `ror:{ror_id}` when present; otherwise `inst:{normalized_name}`

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `id` | string | M | derived | |
| `name` | string | M | CrossRef, CSV | Canonical or raw |
| `ror_id` | string | R | controlled vocab | |
| `university` | string | O | CSV | |
| `department` | string | O | CSV | |
| `city` | string | O | CSV | |
| `state` | string | O | CSV | |
| `country` | string | O | CSV | |

**Note:** Per the MagLab CSV inventory, the University/Department/City/
State/Country columns are 0% populated in the corpus. These properties 
exist for future enrichment from CrossRef affiliations.

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

**Conforms to:** DataCite fundingReference  
**Identifier:** `grant:{funder_normalized}:{award_id}`

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `id` | string | M | derived | |
| `award_id` | string | M | CrossRef | |

Funder details live on the Funder node, connected via `AWARDED_BY`.

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
| `name` | string | M | CSV | From "Facilities" column |
| `ror_id` | string | O | controlled vocab | |

**Note:** v1.0 corpus is dominated by "NHMFL ICR Facility."

---

## Node: Instrument

Sources 2, 4, and 5.

**Conforms to:** PSI-MS  
**Identifier:** `instrument:{normalized_canonical_name}` after normalization; 
during extraction, `instrument:raw:{normalized_raw_string}`

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `id` | string | M | derived | |
| `canonical_name` | string | M after normalization | controlled vocab | E.g., "21T FT-ICR MS" |
| `psi_ms_id` | string | M after normalization | controlled vocab | E.g., "MS:1000079" |
| `instrument_model_raw` | string | O | fisher_py | FOXDEN `instrument.model` |

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

**Conforms to:** PSI-MS  
**Identifier:** `ms:{psi_ms_id}:{canonical_name_normalized}`  
**Coverage:** Tier 3 — 8 annotated papers + 46 RAW files (acquisition methods)

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `id` | string | M | derived | |
| `canonical_name` | string | M | controlled vocab | |
| `psi_ms_id` | string | M | controlled vocab | |
| `tier` | integer | M | controlled vocab | 1 = primary MS (node), 2 = supporting (property only) |

### Rule

Only Tier 1 methods become Method nodes. Tier 2 methods (Western blot, 
RNA-Seq, etc.) are recorded as `supporting_methods` list property on 
Publication.

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

## Node: Organism

Sources 4 and 5.

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

Sources 4 and 5.

**Conforms to:** schema.org/SoftwareApplication, PSI-MS (where assigned), 
Bioschemas ComputationalTool  
**Identifier:** `ms:{psi_ms_id}` when assigned; otherwise 
`software:{canonical_name}:{version}`  
**Coverage:** 8 annotated papers + 46 RAW files

### Properties

| Property | Type | M/R/O | Source | Notes |
|---|---|---|---|---|
| `id` | string | M | derived | |
| `canonical_name` | string | M | controlled vocab, annotation | E.g., "Xcalibur" |
| `software_version` | string | R | annotation, fisher_py | E.g., "2.7.0 SP2" |
| `psi_ms_id` | string | R | controlled vocab | When assigned |
| `vendor` | string | O | controlled vocab | Thermo, Bruker, etc. |
| `category` | string | O | controlled vocab | `acquisition`, `processing`, `search`, `visualization` |

**Note:** Not all software has a PSI-MS ID. When no ID exists, software 
still becomes a node identified by `canonical_name:version`.

---

## Node: RawDataFile

Source 5 only. One node per Thermo `.raw` file.

**Conforms to:** SDRF-Proteomics, schema.org/DigitalDocument, SPDX 
(for checksum), PROV-O  
**Identifier:** `rawfile:{filename}`  
**Coverage:** 46 `.raw` files

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
| `sha256_hash` | string | R | FOXDEN `spdx:checksum` |
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

| Relationship | Subject → Object | Source | Cardinality |
|---|---|---|---|
| `AUTHORED_BY` | Publication → Researcher | CrossRef, CSV | MANY-MANY |
| `AFFILIATED_WITH` | Researcher → Institution | CrossRef, CSV | MANY-MANY |
| `PUBLISHED_IN` | Publication → Journal | CrossRef, CSV | MANY-ONE |
| `FUNDED_BY` | Publication → Grant | CrossRef | MANY-MANY |
| `AWARDED_BY` | Grant → Funder | CrossRef, controlled vocab | MANY-ONE |
| `CONDUCTED_AT` | Publication → Facility | CSV | MANY-MANY |
| `USES_INSTRUMENT` | Publication → Instrument | CSV, annotations | MANY-MANY |
| `HAS_DATASET` | Publication → Dataset | CSV | MANY-MANY |
| `CITES` | Publication → Publication | CrossRef references | MANY-MANY |

### Tier 3 — Annotated papers only

| Relationship | Subject → Object | Source | Cardinality |
|---|---|---|---|
| `USES_METHOD` | Publication → Method | annotation | MANY-MANY |
| `ANALYZES_SAMPLE` | Publication → Sample | annotation | MANY-MANY |
| `ANALYZES_PROTEIN` | Publication → Protein | annotation | MANY-MANY |
| `INVOLVES_ORGANISM` | Publication → Organism | annotation, RAW | MANY-MANY |
| `STUDIES_PTM` | Publication → Modification | annotation | MANY-MANY |
| `USES_SOFTWARE` | Publication → Software | annotation | MANY-MANY |

### RAW file relationships

| Relationship | Subject → Object | Source | Cardinality | Status |
|---|---|---|---|---|
| `COLLECTED_ON` | RawDataFile → Instrument | fisher_py | MANY-ONE | Active |
| `OPERATED_BY` | RawDataFile → Researcher | manual annotation | MANY-ONE | Active |
| `CONTAINS_SAMPLE` | RawDataFile → Sample | manual annotation | MANY-ONE | Active |
| `ACQUIRED_WITH` | RawDataFile → Software | fisher_py | MANY-ONE | Active |
| `ANALYZED_IN` | RawDataFile → Publication | — | MANY-ONE | **PENDING** |

### ANALYZED_IN status

**PENDING — target not yet confirmed.** Hypothesized to be the PEPPI-MS 
paper (`doi:10.1021/acs.jproteome.0c00303`), but this has not been 
confirmed. To be verified by inspecting RAW file FOXDEN JSONs for embedded 
DOI references after pipeline load (Week 5 task). Not loaded into v1.0 
until verification.

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
`orcid:0000-...`, `ms:1000079`). Internal Neo4j storage may use bare 
values for query efficiency.

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

If any answer is "no," the change does not enter v1.0. Bump to v1.1 instead.

---

## References

- Standards alignment table: `docs/FAIR_PRINCIPLES.md`
- Controlled vocabulary values: `docs/controlled_vocabulary.md`
- Questions the graph must answer: `docs/DISCOVERY_QUESTIONS.md`
- Removed concepts and design history: `docs/archive/KNOWLEDGE_GRAPH_DESIGN.md`
- Verified facts vs proposed: `docs/VERIFIED_FACTS_AND_ASSUMPTIONS.md`
- Repository audit: `docs/REPO_AUDIT.md`
