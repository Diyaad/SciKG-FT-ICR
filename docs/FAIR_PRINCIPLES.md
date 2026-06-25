# FAIR Data Notes

SciKG is designed around the **FAIR** principles — that scientific assets should
be **F**indable, **A**ccessible, **I**nteroperable, and **R**eusable, by humans
_and_ machines. This document records what each principle means for SciKG and
how it maps to concrete design decisions.

> Reference: Wilkinson et al. (2016), _The FAIR Guiding Principles for
> scientific data management and stewardship_, Scientific Data 3:160018.
> https://doi.org/10.1038/sdata.2016.18
> The canonical numbered sub-principles (F1–F4, A1–A2, I1–I3, R1) are summarized
> below in SciKG terms.

Last updated: 2026-06-23

---

## F — Findable

_If you can't find it, you can't use it._ Findability comes first because the
other principles depend on it.

**Sub-principles (FAIR canonical)**

- **F1** — (Meta)data are assigned globally unique, persistent identifiers.
- **F2** — Data are described with rich metadata.
- **F3** — Metadata clearly and explicitly include the identifier of the data
  they describe.
- **F4** — (Meta)data are registered or indexed in a searchable resource.

**SciKG design implications**

- Every entity (publication, dataset, instrument, researcher, …) carries a
  **persistent identifier** — reuse external PIDs where they exist (DOI, ORCID,
  ROR, PSI-MS, UNIMOD, UniProt, NCBI Taxonomy) and mint internal PIDs otherwise.
- **Rich metadata** is the default, not an afterthought; see
  [METADATA_INVENTORY.md](METADATA_INVENTORY.md).
- The **knowledge graph itself is the searchable index** — relationships are
  first-class and queryable, not buried in free text.
- Metadata records explicitly reference the identifier of what they describe.

---

## A — Accessible

_Once found, how is it retrieved?_ Accessible does **not** mean "open" — it
means the access conditions and mechanism are clear and standardized. Metadata
should remain accessible even when the underlying data cannot be.

**Sub-principles (FAIR canonical)**

- **A1** — (Meta)data are retrievable by their identifier using a standardized,
  open, free, universally implementable protocol.
- **A1.1 / A1.2** — The protocol supports authentication/authorization where
  necessary.
- **A2** — Metadata remain accessible even when the data are no longer
  available.

**SciKG design implications**

- **Standardized retrieval**: identifier-resolvable access via Cypher queries on
  the Neo4j graph; future JSON-LD export for external interoperability.
- **Clear access pathways**: each source's access method, protocol, and any
  authentication/licensing constraints are documented.
- **Metadata persistence**: descriptive metadata and provenance survive even if
  the original data become unavailable or restricted. The 46 Thermo RAW files
  illustrate this: the binaries live on the MagLab computer (46 GB, never in
  the repo), but the FOXDEN-formatted metadata for each file lives in the graph.
- Access conditions are explicit — restricted ≠ undocumented.

---

## I — Interoperable

_Data needs to integrate with other data, and with tools and workflows._

**Sub-principles (FAIR canonical)**

- **I1** — (Meta)data use a formal, accessible, shared, broadly applicable
  language for knowledge representation.
- **I2** — (Meta)data use vocabularies that themselves follow FAIR principles.
- **I3** — (Meta)data include qualified references to other (meta)data.

**SciKG design implications**

- **Structured schema**: entities and relationships defined in
  [SCIKG_SCHEMA.md](SCIKG_SCHEMA.md) with explicit property names, types, and
  identifier strategies.
- **Standard vocabularies**: every controlled vocabulary in SciKG resolves to an
  established external ontology (PSI-MS, UNIMOD, NCBI Taxonomy, UniProt, ORCID,
  ROR, DataCite). See the full alignment table below.
- **Linked-data ready**: FOXDEN output for RAW files is already JSON-LD with
  schema.org, PROV-O, PRIDE, modsci, SOSA, and SPDX contexts. SciKG preserves
  these mappings so the graph can be exported as JSON-LD with minimal remapping.
- **Qualified links**: relationships are typed and meaningful (e.g.
  `USES_INSTRUMENT`, `FUNDED_BY`, `COLLECTED_ON`) rather than untyped pointers.

---

## R — Reusable

_The ultimate goal: optimize reuse._ Reuse requires rich context and clear terms
of use.

**Sub-principles (FAIR canonical)**

- **R1** — (Meta)data are richly described with a plurality of accurate and
  relevant attributes.
- **R1.1** — (Meta)data are released with a clear and accessible data-usage
  license.
- **R1.2** — (Meta)data are associated with detailed provenance.
- **R1.3** — (Meta)data meet domain-relevant community standards.

**SciKG design implications**

- **Provenance tracking** is mandatory: every node and edge records six
  properties — `source_type`, `confidence`, `extracted_at`, `evidence_note`,
  `source_id`, `schema_version`. This is SciKG's operational mapping of PROV-O.
- **Context preservation**: experimental context, methods, instruments, samples,
  and project/grant linkages are retained, not discarded during processing.
- **Documentation & reproducibility**: processed data and outputs must be
  regenerable from raw sources plus code; transformations are documented.
- **Licensing**: usage terms recorded per asset (to be specified in a later
  phase).
- **Community standards**: SciKG adopts MIAPE (proteomics experiment reporting),
  SDRF-Proteomics (sample-data relationships), PSI-MS (mass spectrometry
  vocabulary), and DataCite (dataset metadata).

---

## FAIR ≠ Open

FAIR is about being _well-described and machine-actionable_, independent of
whether data are openly available. SciKG can describe restricted assets FAIRly:
the **metadata and provenance are rich and accessible** even when the data
itself is access-controlled. The 46 RAW files demonstrate this directly — the
binaries are not redistributed, but every RAW file is fully described in the
graph with operator, date, instrument, software, and method.

---

## How SciKG operationalizes FAIR

| FAIR need              | SciKG mechanism                                                                                                                  |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Persistent identifiers | External PIDs (DOI/ORCID/ROR/PSI-MS/UNIMOD/UniProt/NCBI Taxonomy) + internal PID minting                                         |
| Rich metadata          | Per-node property definitions in [SCIKG_SCHEMA.md](SCIKG_SCHEMA.md); inventory in [METADATA_INVENTORY.md](METADATA_INVENTORY.md) |
| Searchable index       | The Neo4j knowledge graph + Cypher queries                                                                                       |
| Standard retrieval     | Documented query patterns; future JSON-LD export                                                                                 |
| Interoperable formats  | JSON-LD-ready property names; standard vocabularies on every node                                                                |
| Typed relationships    | All 19 edge types defined in [SCIKG_SCHEMA.md](SCIKG_SCHEMA.md)                                                                  |
| Provenance             | Six PROV-O–aligned properties on every node and edge                                                                             |
| Reproducibility        | `raw → processed → outputs` data flow + immutable raw data + versioned code                                                      |

---

## Standards and Ontologies — Full Alignment

SciKG aligns with the following established standards. Every controlled term in
the graph traces back to one of these sources. The "Status" column reflects v1.0
adoption.

### Identifier standards

| Standard           | Scope                  | Source            | Status | Use in SciKG                                            |
| ------------------ | ---------------------- | ----------------- | ------ | ------------------------------------------------------- |
| DOI                | Publications           | https://doi.org   | Active | Master key on Publication nodes (lowercase, no prefix)  |
| ORCID              | Researchers            | https://orcid.org | Active | Optional identifier on Researcher nodes                 |
| ROR                | Research organizations | https://ror.org   | Active | Optional identifier on Institution and Facility nodes   |
| Crossref Funder ID | Funding bodies         | CrossRef API      | Active | Optional identifier on Grant nodes                      |
| MagLab Id          | Internal MagLab papers | MagLab CSV        | Active | Secondary identifier on Publication nodes (~806 corpus) |

### Domain ontologies — Mass Spectrometry

| Standard                     | Scope                                             | Source                                                                                   | Status  | Use in SciKG                                                |
| ---------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------------- | ------- | ----------------------------------------------------------- |
| PSI-MS Controlled Vocabulary | MS instruments, methods, software, properties     | https://github.com/HUPO-PSI/psi-ms-CV (browser: https://www.ebi.ac.uk/ols/ontologies/ms) | Active  | Required identifier on Instrument, Method, Software nodes   |
| UNIMOD                       | Protein post-translational modifications          | https://www.unimod.org (browser: https://www.ebi.ac.uk/ols4/ontologies/unimod)           | Active  | Required identifier on Modification nodes                   |
| PRIDE Ontology               | Proteomics measurement techniques                 | https://github.com/PRIDE-Archive/pride-ontology                                          | Active  | `measurementTechnique` property on RawDataFile (via FOXDEN) |
| MIAPE                        | Minimum Information About a Proteomics Experiment | https://www.psidev.info/miape                                                            | Phase 2 | Field target list for PDF extraction                        |
| SDRF-Proteomics              | Sample-Data Relationship Format                   | https://github.com/bigbio/proteomics-sample-metadata                                     | Active  | Field name alignment for Sample and RawDataFile nodes       |

### Domain ontologies — Biology

| Standard      | Scope     | Source                                | Status | Use in SciKG                          |
| ------------- | --------- | ------------------------------------- | ------ | ------------------------------------- |
| NCBI Taxonomy | Organisms | https://www.ncbi.nlm.nih.gov/taxonomy | Active | Required identifier on Organism nodes |
| UniProt       | Proteins  | https://www.uniprot.org               | Active | Optional accession on Protein nodes   |

### Metadata schemas — Scholarly

| Standard                     | Scope                          | Source                                           | Status              | Use in SciKG                                                  |
| ---------------------------- | ------------------------------ | ------------------------------------------------ | ------------------- | ------------------------------------------------------------- |
| DataCite Metadata Schema 4.5 | Dataset metadata               | https://schema.datacite.org/meta/kernel-4.5/     | Active              | Publication property name alignment                           |
| Bioschemas ScholarlyArticle  | Life-sciences article profile  | https://bioschemas.org/profiles/ScholarlyArticle | Active              | Publication node structure alignment                          |
| schema.org                   | General linked-data vocabulary | https://schema.org/                              | Active (via FOXDEN) | Property name alignment for Publication, Researcher, Software |

### Provenance and linked-data infrastructure

| Standard | Scope                                           | Source                        | Status                | Use in SciKG                                                           |
| -------- | ----------------------------------------------- | ----------------------------- | --------------------- | ---------------------------------------------------------------------- |
| PROV-O   | W3C Provenance Ontology                         | https://www.w3.org/TR/prov-o/ | Active                | Operational mapping into SciKG's 6 provenance properties               |
| modsci   | Modern Science Ontology — Scientific Instrument | https://w3id.org/skgo/modsci# | Optional (via FOXDEN) | Already present in FOXDEN output; PSI-MS is primary for MS instruments |
| SOSA     | Sensor, Observation, Sample, Actuator ontology  | http://www.w3.org/ns/sosa/    | Optional (via FOXDEN) | Already present in FOXDEN output; not required for v1.0                |
| SPDX     | Software Package Data Exchange                  | https://spdx.dev/             | Active (via FOXDEN)   | File integrity properties (sha256_hash) on RawDataFile                 |

These standards make SciKG interoperable with ProteomeXchange, MassIVE, UniProt,
PRIDE Archive, and major proteomics databases without additional mapping.

---

## How each source maps to which node type

A reverse view — which standards apply to which SciKG node:

| Node type    | Identifier standard(s)  | Property name standards                               |
| ------------ | ----------------------- | ----------------------------------------------------- |
| Publication  | DOI, MagLab Id          | DataCite 4.5, Bioschemas ScholarlyArticle, schema.org |
| Researcher   | ORCID                   | schema.org Person                                     |
| Institution  | ROR                     | schema.org Organization                               |
| Journal      | ISSN                    | DataCite, schema.org                                  |
| Grant        | Crossref Funder ID      | DataCite funding properties                           |
| Facility     | ROR                     | schema.org                                            |
| Instrument   | PSI-MS                  | PSI-MS, modsci (optional)                             |
| Dataset      | Repository accession    | DataCite                                              |
| Method       | PSI-MS                  | PSI-MS                                                |
| Sample       | (canonical name)        | SDRF-Proteomics                                       |
| Protein      | UniProt                 | UniProt                                               |
| Organism     | NCBI Taxonomy           | NCBI Taxonomy                                         |
| Modification | UNIMOD                  | UNIMOD                                                |
| Software     | PSI-MS (where assigned) | schema.org SoftwareApplication                        |
| RawDataFile  | (filename)              | SDRF-Proteomics, SPDX, schema.org, PROV-O             |

---

## FAIR Self-Assessment Checklist (use each phase)

- [ ] Does every new entity type have a persistent identifier strategy?
- [ ] Is the metadata for it rich enough to be discovered without the data?
- [ ] Is it retrievable through a documented, standardized mechanism?
- [ ] Are access/licensing conditions explicit?
- [ ] Does it use standard vocabularies and serialize to machine-readable form?
- [ ] Are its relationships typed and qualified?
- [ ] Is provenance captured for every fact?
- [ ] Can processed/output forms be regenerated from raw + code?

---

## Internal Sources — Project-Specific

Beyond external standards, SciKG is grounded in project-internal sources that
validate the schema against real observed data:

| Source                            | Location                             | FAIR role                                                                                            |
| --------------------------------- | ------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| 8 annotated papers                | docs/annotations/paper_reviews.md    | Ground truth for validation; few-shot examples for Phase 2 LLM extraction                            |
| FOXDEN-formatted fisher_py output | data/raw/rawfile_foxden/             | Source of truth for 46 RawDataFile records; pre-linked to schema.org / PRIDE / PROV-O                |
| MagLab CSV                        | data/raw/maglab_icr_publications.csv | 806-paper corpus; source for Publication, Researcher, Facility, Instrument, Dataset                  |
| Discovery questions               | docs/DISCOVERY_QUESTIONS.md          | Defines what the graph must answer; every node/edge must be justified by enabling at least one query |
