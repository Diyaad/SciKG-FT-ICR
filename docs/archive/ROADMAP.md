# SciKG Proposed Research Workflow

> **Status: PROPOSED / EVOLVING — not an approved plan.**
> This document is a *suggested* way of sequencing the work. It was drafted as a
> starting point and has **not** been reviewed or approved by the research
> supervisor. The number of stages, their order, their scope, and whether any of
> them happen at all are all open. Treat everything below as a thinking aid, not
> a commitment. Stages may be added, removed, merged, reordered, or abandoned as
> the research develops.

This is a workflow sketch, not a roadmap with fixed phases or timelines. There
are **no approved phase counts, no approved scope, and no timelines.** Dates are
deliberately absent.

> **Guiding intent (proposed):** keep the work FAIR-aligned and
> provenance-preserving throughout. See [FAIR_PRINCIPLES.md](FAIR_PRINCIPLES.md).

---

## How to read this document

- Stages are described by *intent*, not as a locked sequence.
- "Possible activities" and "possible outputs" are options to consider, not
  deliverables that have been agreed.
- Anything that depends on real data (e.g. cataloguing a source) has **not** been
  done; describing it here does not imply it has.

---

## Current stage — Research foundation & design *(where the project is now)*

**Intent:** Understand the scientific metadata ecosystem and establish an
extensible documentation/design foundation before writing any pipeline code.

**Possible activities**
- Establish repository structure and documentation (done as initial scaffolding).
- Survey scientific metadata standards, vocabularies, and persistent-identifier
  systems relevant to research assets.
- Draft an initial, conceptual knowledge-graph entity/relationship model.
- Draft metadata inventory templates.
- Identify *candidate* data sources to consider later (the project brief names the
  NHMFL / FT-ICR publication ecosystem as one candidate; it has **not** been
  investigated or catalogued).

**Possible outputs**
- Project documentation (`README.md`, `CLAUDE.md`)
- This proposed-workflow document
- FAIR data notes (`FAIR_PRINCIPLES.md`)
- Conceptual knowledge graph design notes (`KNOWLEDGE_GRAPH_DESIGN.md`)
- Metadata inventory templates (`metadata_templates/`)
- Forward-looking architecture notes (`ARCHITECTURE.md`)

**Explicitly out of scope right now:** scraping scripts, databases, dependency
installs, any real data ingestion.

---

## Possible later stages (unordered, unapproved)

The following are *candidate* directions the research could take. They are listed
for context only. None is scheduled, scoped, or approved, and the grouping below
is one possible decomposition among many.

### Metadata ecosystem mapping *(possible)*
- Catalogue available metadata fields for a candidate source using the inventory
  templates — **only after** a source is selected and access is confirmed.
- Assess metadata quality, completeness, consistency, and identifier coverage
  using real, observed values (never inferred).
- Map source fields to the conceptual entity model (gap analysis).
- Document access pathways, licensing, and constraints.

### Schema & vocabulary specification *(possible)*
- Turn the conceptual model into machine-readable schemas (e.g. JSON Schema /
  SHACL) — vocabulary and format choices remain open.
- Consider alignment with standard vocabularies (candidates only; none chosen).
- Consider a persistent-identifier strategy.
- Consider a provenance model.

### Ingestion & knowledge graph construction *(possible — first stage that would write code / provision storage)*
- Implement ingestion for a selected source into `data/raw` → `data/processed`.
- Construct a knowledge graph in a backend **to be decided** (see
  [ARCHITECTURE.md](ARCHITECTURE.md) — no backend has been chosen).
- Validate against schemas; capture provenance for every node/edge.

### Discovery & retrieval interfaces *(possible)*
- Structured query interface and saved query patterns.
- Faceted / metadata-driven search.
- Semantic search via embeddings (candidate approach).

### AI-assisted & agent-based retrieval *(possible)*
- Natural-language → structured-query translation grounded in a schema.
- Retrieval-augmented answering with citations back to provenance.
- Agent-based multi-step retrieval.

### Scale, integration & sustainability *(possible)*
- Additional sources and external repositories.
- Entity resolution / deduplication across sources.
- Access control, licensing/governance, maintenance, versioning, citation policy.

---

## Cross-cutting intentions (proposed, apply throughout)

- **FAIR alignment** — check designs against `FAIR_PRINCIPLES.md`.
- **Provenance preservation** — outputs should trace to raw sources.
- **Reproducibility** — processed data and outputs should regenerate from raw +
  code.
- **Data integrity** — no fabricated, inferred, or placeholder data; missing
  values remain as they are in the source/schema (see `CLAUDE.md`).
- **Extensibility** — additive, schema-driven changes over hard-coded
  assumptions.
- **Documentation** — record design decisions in `docs/` as they are actually
  made, and log review-worthy changes in [REVIEW_LOG.md](REVIEW_LOG.md).

## Open questions (to revisit continuously)

- RDF triplestore vs. property graph (or hybrid)? — undecided.
- Which standard vocabularies, if any, become canonical for SciKG? — undecided.
- Internal PID minting strategy vs. reliance on external PIDs? — undecided.
- Entity-resolution strategy across heterogeneous sources? — undecided.
- Data-versioning approach for `data/`? — undecided.
- Which candidate data source (if any) is investigated first? — undecided.

See [VERIFIED_FACTS_AND_ASSUMPTIONS.md](VERIFIED_FACTS_AND_ASSUMPTIONS.md) for a
clear separation of what is known versus proposed versus unknown.
