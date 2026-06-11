# Verified Facts, Proposed Ideas & Unknowns

This file exists to keep SciKG documentation honest. It separates what is
**actually known** from what is **proposed** and what is **unknown**, and records
**assumptions that were removed** during the integrity audit.

> **Rule of thumb:** if something is not listed under "Verified Facts" with a
> traceable basis, it should be read as proposed or unknown — not as established
> fact.

Last updated: 2026-06-11.

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

> Note: item 6 verifies only that these standards *exist*. Whether SciKG adopts
> any specific one is a proposed idea / open question, not a fact.

---

## Proposed Ideas

Future concepts, architecture ideas, KG designs, retrieval/chatbot ideas, and
implementation possibilities. **None of these is decided, approved, or
implemented.**

- **Knowledge graph entity/relationship model** — the entity catalogue and
  relationship types in `KNOWLEDGE_GRAPH_DESIGN.md` are a *conceptual draft*, not
  validated against any real data.
- **Layered architecture** — the six-layer design in `ARCHITECTURE.md` is a
  forward-looking sketch; most components do not exist.
- **Graph backend** — RDF triplestore vs. labeled property graph vs. hybrid:
  proposed options, undecided.
- **Persistent-identifier strategy** — reusing external PIDs and minting internal
  PIDs: a proposed approach, undecided.
- **Provenance model** — PROV-O (Entity/Activity/Agent) is a proposed candidate.
- **Standard vocabularies** — schema.org / DC / DCAT / PROV-O / SPAR etc. are
  proposed candidates for alignment; none chosen.
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

- Which candidate data source (if any) is investigated first, and is access to it
  actually available and licensed for this use?
- What metadata fields does any real candidate source actually expose, and how
  complete/consistent are they? (No field has been observed yet.)
- RDF vs. property graph vs. hybrid — which backend, and why?
- Which standard vocabularies (if any) become canonical for SciKG?
- What is the internal PID minting scheme, if internal PIDs are used at all?
- How is entity resolution / deduplication handled across heterogeneous sources?
- How are `data/` and the graph itself versioned over time?
- What are the access-control, licensing, and governance requirements?
- Which embedding model and vector store (if any) are appropriate?
- Is Python the right implementation language? (Currently an assumption implied by
  `requirements.txt`.)
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
