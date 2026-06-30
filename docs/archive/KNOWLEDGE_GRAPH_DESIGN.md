# Knowledge Graph Design Notes

Design notes for the SciKG knowledge graph: candidate entities, how they might
relate, and modeling choices that would keep the graph FAIR and extensible.

> **Status: CONCEPTUAL / PROPOSED.** This is a draft model, **not validated
> against any real data** and not approved. No database is built. Entity names,
> attributes, relationships, and identifier choices are all candidates that may
> change. A concrete, machine-readable schema would come in a later stage (see
> [ROADMAP.md](ROADMAP.md)).

---

## Modeling goals

1. **Extensibility first.** New entity and relationship types must be additive —
   never require reworking the core.
2. **Relationships are the value.** The point of a graph is the *connections*
   between assets; edges are first-class and typed.
3. **Provenance everywhere.** Every node and edge can answer "where did this come
   from and how do I know?"
4. **Identifier-anchored.** Every entity resolves to a persistent identifier.
5. **Vocabulary alignment.** Prefer terms from established vocabularies/ontologies
   over bespoke ones.

---

## Core entity types

A *candidate* entity catalogue. Each would get a formal schema later; here we
capture intent only. (Entity names, attribute lists, and identifier choices are
indicative and unverified, not final. The "candidate identifier" column lists
external standards that *could* apply — none has been adopted.)

| Entity | Description | Example key attributes | Candidate identifier |
|---|---|---|---|
| **Publication** | Paper, report, preprint | title, authors, venue, date, abstract | DOI |
| **Dataset** | A described collection of data | title, description, format, size, access | DOI / internal PID |
| **ExperimentalMetadata** | Metadata about an experiment/run | parameters, conditions, date | internal PID |
| **Project** | Research project / effort | name, description, period | internal PID |
| **Grant** | Funding award | award number, funder, amount, period | award ID / funder PID |
| **FundingSource** | Funding body | name, type | ROR / Crossref Funder ID |
| **Instrument** | Scientific instrument | name, type, specs | RRID / internal PID |
| **Facility** | Lab / facility | name, location | ROR |
| **Sample** | Physical/biological sample | type, material, origin | IGSN / internal PID |
| **Material** | Material / substance | name, composition | internal PID |
| **Researcher** | Person / collaborator | name, affiliation | ORCID |
| **Organization** | Institution / collaborator org | name, type | ROR |
| **Workflow** | Processing workflow | steps, version | internal PID |
| **ProvenanceRecord** | Origin/derivation record | source, agent, activity, time | internal PID |
| **Method** | Scientific method/technique | name, description | vocabulary term / internal PID |
| **Concept** | Scientific concept/topic | label, definition | vocabulary/ontology IRI |
| **ExternalRepository** | External source/repo | name, endpoint, protocol | URL / internal PID |

> The list is deliberately broad to explore whether the model *could* hold the
> full ecosystem. If implementation proceeds, it would likely start from a small
> subset and grow outward — but which subset is **to be decided**, not assumed.

---

## Core relationship types

Relationships are **typed and directional**. Naming aligns with PROV-O and
schema.org where natural.

| Relationship (subject → object) | Meaning |
|---|---|
| Publication `authoredBy` Researcher | authorship |
| Publication `describes` Dataset | a paper reports on a dataset |
| Publication `mentionsConcept` Concept | topical link |
| Publication `usedInstrument` Instrument | instrument used in the work |
| Publication `usedMethod` Method | method/technique used |
| Dataset `wasGeneratedBy` Workflow | derivation |
| Dataset `wasDerivedFrom` Dataset | data lineage |
| Dataset `measuredWith` Instrument | acquisition instrument |
| ExperimentalMetadata `describes` Dataset | experiment ↔ data |
| ExperimentalMetadata `usedSample` Sample | sample used |
| Sample `composedOf` Material | sample composition |
| Researcher `affiliatedWith` Organization | affiliation |
| Researcher `memberOf` Project | participation |
| Project `fundedBy` Grant | funding |
| Grant `awardedBy` FundingSource | funder |
| Instrument `locatedAt` Facility | location |
| Workflow `hasStep` Method | workflow composition |
| Entity `wasAttributedTo` Researcher | provenance attribution (PROV-O) |
| Entity `wasGeneratedBy` Activity | provenance generation (PROV-O) |
| Entity `hasProvenance` ProvenanceRecord | links to origin record |
| Entity `sourcedFrom` ExternalRepository | external origin |

The graph is **multi-relational**: any two entities may be connected by more than
one relationship type.

---

## Conceptual schema sketch

```
        ┌──────────────┐  authoredBy   ┌──────────────┐  affiliatedWith ┌──────────────┐
        │ Publication  │──────────────▶│  Researcher  │────────────────▶│ Organization │
        └──────┬───────┘               └──────┬───────┘                 └──────────────┘
   usedMethod  │ usedInstrument                │ memberOf
        ┌──────▼───────┐    locatedAt   ┌──────▼───────┐   fundedBy   ┌───────┐ awardedBy ┌──────────────┐
        │  Instrument  │───────────────▶│   Project    │─────────────▶│ Grant │──────────▶│ FundingSource│
        └──────────────┘   ┌─Facility   └──────────────┘              └───────┘           └──────────────┘
                           │
        ┌──────────────┐ measuredWith    ┌──────────────────────┐ usedSample ┌──────────┐ composedOf ┌──────────┐
        │   Dataset    │◀────────────────│ ExperimentalMetadata │───────────▶│  Sample  │───────────▶│ Material │
        └──────┬───────┘                 └──────────────────────┘            └──────────┘            └──────────┘
   wasGeneratedBy │
        ┌──────▼───────┐
        │   Workflow   │   (every node/edge ── hasProvenance ──▶ ProvenanceRecord)
        └──────────────┘
```

---

## Identifiers & persistence

- **Reuse external PIDs** when they exist: DOI (publications/datasets), ORCID
  (researchers), ROR (organizations/facilities), Crossref Funder ID (funders),
  RRID (instruments/resources), IGSN (samples).
- **Mint internal PIDs** for everything else, under a stable internal namespace,
  resolvable within SciKG.
- Identifiers are required at creation time — no "anonymous" nodes in the
  canonical graph.

---

## Provenance model

Provenance is a **first-class concern**, modeled on **PROV-O**'s
Entity / Activity / Agent triad:

- **Entity** — a thing (e.g. a dataset record).
- **Activity** — a process that produced/changed it (e.g. an ingestion run).
- **Agent** — who/what is responsible (a researcher, a script, SciKG itself).

Every fact in the graph should be traceable: *which source*, *which activity*,
*which agent*, *when*. This is what makes the graph reusable and reproducible
(see [FAIR_PRINCIPLES.md](FAIR_PRINCIPLES.md) → R1.2).

---

## Graph backend: RDF vs. property graph

**Undecided — decision deferred to a later stage.** Both are viable; the
trade-off is recorded here so it is explicit. No preference has been adopted.

| | RDF / triplestore (e.g. SPARQL) | Labeled property graph (e.g. Neo4j) |
|---|---|---|
| Standards / interop | Strong (W3C: RDF, OWL, SHACL, PROV-O, JSON-LD) | Weaker formal-semantics story |
| Vocabularies / linked data | Native, IRI-based | Possible but not native |
| Properties on edges | Verbose (reification / RDF-star) | First-class, natural |
| Query language | SPARQL | Cypher / GQL |
| Tooling ergonomics | Steeper | Often friendlier for app devs |

**No decision has been made.** Arguments exist on both sides — RDF for
standards/interoperability, property graphs for ergonomic edge properties and
serving — and a hybrid is also possible. This is an open question, not a
preference. **Record the eventual decision in
[ARCHITECTURE.md](ARCHITECTURE.md).**

---

## Candidate vocabularies / ontologies

Candidates to evaluate in a later stage (none adopted; these are real external
standards listed as options only):

- **schema.org** — general-purpose, web-friendly typing
- **Dublin Core (DC/DCTERMS)** — descriptive metadata
- **DCAT** — datasets and data catalogues
- **PROV-O** — provenance
- **FOAF / ORG** — people and organizations
- **FaBiO / CiTO (SPAR ontologies)** — bibliographic entities and citations
- Domain ontologies (e.g. chemistry/mass-spectrometry vocabularies) for
  FT-ICR–style sources

---

## Open design questions

- Minimal viable entity subset for the first real graph?
- Edge properties (e.g. confidence, timestamp, source) — RDF-star vs. property
  graph implications?
- Entity resolution: how do we decide two records are the same researcher /
  instrument across sources?
- Versioning: how do we represent change over time in the graph?
- How much reasoning/inference (if any) do we want the backend to perform?
