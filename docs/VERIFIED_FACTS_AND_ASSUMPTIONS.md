# Verified Facts, Proposed Ideas & Unknowns

This file exists to keep SciKG documentation honest. It separates what is
**actually known** from what is **proposed** and what is **unknown**, and records
**assumptions that were removed** during the integrity audit.

> **Rule of thumb:** if something is not listed under "Verified Facts" with a
> traceable basis, it should be read as proposed or unknown — not as established
> fact.

Last updated: 2026-06-29.

---

## Verified Facts

Facts supported by the project brief, by widely published external standards, or
by the current state of this repository. Each carries its basis.

| # | Fact | Basis / Source |
|---|---|---|
| 1 | The project is named SciKG and its stated aim is to improve the Findability, Accessibility, Interoperability, and Reusability (FAIR) of scientific research assets. | Project brief provided by the user/supervisor. |
| 2 | The project brief names the NHMFL (National High Magnetic Field Laboratory) publication ecosystem, including FT-ICR–related publications, as **one candidate** data source — explicitly not a scope limit. | Project brief. (No NHMFL data has been accessed, observed, or catalogued.) |
| 3 | The current stage is documentation/design only: no scraping, no databases, no dependency installation, no real data ingestion. | Project brief + current repository contents. |
| 4 | The repository contains these folders: `data/raw`, `data/processed`, `scripts`, `outputs`, `docs`, `notebooks`; and these top-level files: `README.md`, `CLAUDE.md`, `requirements.txt`, `.gitignore`. | Direct observation of the repository. |
| 5 | The FAIR principles, including their canonical sub-principles (F1–F4, A1–A2, I1–I3, R1.1–R1.3), are an externally published framework. | Wilkinson et al. (2016), *The FAIR Guiding Principles for scientific data management and stewardship*, Scientific Data 3:160018. https://doi.org/10.1038/sdata.2016.18 |
| 6 | The external standards/identifiers referenced as *candidates* (DOI, ORCID, ROR, RRID, IGSN, Crossref Funder ID; schema.org, Dublin Core, DCAT, PROV-O, FOAF, ORG, SPAR/FaBiO/CiTO) exist as real, published specifications. | These are well-known public standards. SciKG's *use* of any of them is not yet decided (see Proposed Ideas / Unknowns). |
| 7 | `requirements.txt` lists candidate dependencies only; none are installed and none are pinned. | Direct observation of the file. |
| 8 | Knowledge graph entity/relationship model is now locked in `docs/SCIKG_SCHEMA.md`. | Schema v1.0 locked 2026-06-23 after team review. (Moved from Proposed Ideas.) |
| 9 | Graph backend confirmed: Neo4j. | Decided 2026-06-24. (Moved from Proposed Ideas.) |
| 10 | Persistent-identifier strategy confirmed: reuse external PIDs and mint internal PIDs. | Decided 2026-06-23. (Moved from Proposed Ideas.) |
| 11 | Provenance model confirmed: PROV-O, realized via the 6 universal properties on every node and edge. | Adopted in `docs/SCIKG_SCHEMA.md`. (Moved from Proposed Ideas.) |
| 12 | Standard vocabularies adopted: DataCite, Bioschemas, PSI-MS, UNIMOD, NCBI Taxonomy, UniProt, ORCID, ROR, PROV-O. | Adopted across `controlled_vocabulary.md` and `docs/SCIKG_SCHEMA.md`. (Moved from Proposed Ideas.) |

> Note: item 6 verifies only that these standards *exist*. Items 8–12 record
> which of those candidates SciKG has since adopted.

---

## Confirmed This Week (2026-06-23 to 2026-06-29)

| Fact | Basis / Source |
|---|---|
| Schema v1.0 locked in docs/SCIKG_SCHEMA.md | Locked 2026-06-23 after team review |
| Neo4j Aura Free is the v1.0 graph database | Decided 2026-06-24 |
| Naming conventions adopted: snake_case properties, PascalCase entity labels, SCREAMING_SNAKE_CASE relationships, namespace:value identifiers | Locked in CLAUDE.md and SCIKG_SCHEMA.md |
| DOI is preferred Publication identifier when present; pub:maglab:{id} is the fallback for the 404 papers without DOI | Decided 2026-06-23 |
| Software is a logged entity (Tier 3) with PSI-MS IDs where available | Decision reversed from "excluded" on 2026-06-23 |
| Funder and Grant are separate node types | Confirmed 2026-06-23 |
| Author emails from CSV are never propagated. Author emails from PDF byline or footnote can be extracted in Phase 2 if present. | CSV emails are MagLab-internal contact data; PDF emails are publicly published. |
| 02b_extract_csv.py written and run on full 806-row MagLab CSV | Completed 2026-06-29 |
| WCL in RAW file filenames means "Whole Cell Lysate" | Confirmed 2026-06-29 |
| "J" in M9-J-YYYYMMDD is a run letter assigned to a sample preparation series. Letters A through J have been observed in this corpus. Position is not interpreted as ordering. | Confirmed 2026-06-29 |
| Magnet System Status column from CSV is excluded from the graph | Confirmed 2026-06-29 |
| magnet_system_raw property on Instrument is excluded | Decided 2026-06-29 |
| instrument_model_raw on RawDataFile (from FOXDEN/Thermo headers) is retained as distinct from CSV Magnet Systems | Decided 2026-06-29 |

---

## Proposed Ideas

Future concepts, architecture ideas, KG designs, retrieval/chatbot ideas, and
implementation possibilities. **None of these is decided, approved, or
implemented.**

- **Layered architecture** — the six-layer design in `ARCHITECTURE.md` is a
  forward-looking sketch; most components do not exist.
- **AI-assisted & agent-based retrieval** — embeddings/semantic search, NL→query
  translation, RAG-with-citations, agentic multi-step retrieval, and a
  natural-language search interface are all proposed future capabilities.
- **LLM choice** — Anthropic Claude is a proposed candidate for the AI layer, not
  a committed dependency.
- **Proposed research workflow** — the stages in `ROADMAP.md` are a suggested,
  unapproved sequence; counts, order, and scope are all open.
- **Metadata inventory method** — the templates and procedure are a proposed way
  to catalogue a source once one is selected and accessed.

---

## Unknowns / Research Questions

Open questions that require investigation. These must **not** be treated as
facts or quietly resolved by assumption.

- **ANALYZED_IN target for the 46 RAW files** — target publication not yet
  identified. To be checked after pipeline load by inspecting the RAW file
  FOXDEN JSONs for embedded DOI references. This relationship is **not loaded
  in v1.0** until confirmed.
- RCC access setup completion.
- LangExtract vs. Gemini API decision for PDF extraction.
- Which candidate data source (if any) is investigated first, and is access to it
  actually available and licensed for this use?
- What metadata fields does any real candidate source actually expose, and how
  complete/consistent are they? (No field has been observed yet.)
- How is entity resolution / deduplication handled across heterogeneous sources?
- How are `data/` and the graph itself versioned over time?
- What are the access-control, licensing, and governance requirements?
- Which embedding model and vector store (if any) are appropriate?
- Should this repository be a git repository? (It is not currently initialized as
  one.)
- What are the licensing and citation terms for SciKG itself?

---

## Removed Assumptions

Assumptions, fabricated examples, and unverified claims removed from the
documentation during the integrity audit (see `REVIEW_LOG.md` for the
file-by-file record).

- **Invented population statistic** — "a field that is 12% populated" in
  `METADATA_INVENTORY.md`. Removed: no field has been measured.
- **Fabricated field-inventory rows** in `field_inventory_template.csv`:
  - fake DOI string `10.xxxx/xxxxx` and "92% populated"
  - fake instrument value `9.4T FT-ICR MS` and "40% populated"
  - fake title/value `FT-ICR analysis of ...` and "100% populated"
  - fake author value `Smith, J.; Doe, A.` and "99% populated"
  - fake funding text `Supported by NSF ...` and "55% populated"
  - All removed; template now ships header + guidance only.
- **Fabricated entity-mapping rows** in `entity_mapping_template.csv` — illustrative
  mappings that implied a real source had been catalogued. Removed.
- **Implied completed inventory** — the worked NHMFL/FT-ICR example in
  `METADATA_INVENTORY.md` presented specific source fields as if observed.
  Rewritten as an abstract, clearly-hypothetical procedure with no specific
  values.
- **Soft decisions stated as settled** — "leaning RDF-canonical" and "Anthropic
  Claude models are the default LLM" in `ARCHITECTURE.md`; "Leaning: RDF aligns
  better…" in `KNOWLEDGE_GRAPH_DESIGN.md`. Reframed as undecided candidates.
- **Assumed starting entity subset** — "(likely Publication, Researcher,
  Instrument, Method, Concept)" in `KNOWLEDGE_GRAPH_DESIGN.md`. Softened to
  "to be decided."
- **Approved-plan framing** — the fixed 7-phase structure in `ROADMAP.md` implied
  an approved plan, phase count, and scope not provided by the supervisor.
  Reframed as a proposed, unapproved, evolving workflow of unordered candidate
  stages.

---

## Maintenance

When new facts are confirmed (with a traceable basis), move the relevant item
from "Proposed Ideas" or "Unknowns" into "Verified Facts" and cite the basis.
When an assumption is removed or a claim rewritten, record it here and in
`REVIEW_LOG.md`.

## Schema additions confirmed — 2026-06-18

- Modification (PTM) added as first-class node type 
  in v1.0. UNIMOD IDs used as canonical identifiers.
  Source: https://www.unimod.org
- Protein added as first-class node type in v1.0.
  UniProt accessions used where available.
  Source: https://www.uniprot.org
- Organism added as first-class node type in v1.0.
  NCBI Taxonomy IDs used.
  Source: https://www.ncbi.nlm.nih.gov/taxonomy
- Two-tier method normalization adopted: Tier 1 MS 
  methods become Method nodes with PSI-MS IDs,
  Tier 2 supporting methods stored as text properties.
  Source: https://github.com/HUPO-PSI/psi-ms-CV
- Dataset repositories documented using DataCite 
  conventions: MassIVE, OSF, ProteomeXchange, Zenodo.
  Source: https://schema.datacite.org
- Software included as a logged entity in v1.0.
  Corrected 2026-06-30: the earlier 2026-06-18 entry
  excluded Software ("too variable across papers, not a
  primary discovery entity for this corpus"). That is
  superseded — the RAW-file (fisher_py/FOXDEN) metadata
  yields clean, consistent acquisition-software records
  (name + version), so Software is a logged entity, as
  CLAUDE.md already states. Software nodes are written by
  02c_extract_rawfiles.py.
