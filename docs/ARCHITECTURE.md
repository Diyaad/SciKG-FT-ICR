# SciKG Future Architecture

Forward-looking architecture *notes* for SciKG as it might evolve from a research
foundation into an AI-assisted scientific knowledge-graph platform.

> **Status: PROPOSED — nothing here is final or approved.** Most components do
> not exist. **Every technology choice is deferred/undecided** unless this
> document explicitly states it has been verified and adopted (none has been so
> far). The diagram and layers describe *possibilities* for discussion, not a
> committed design. Decisions are made in later stages of the proposed workflow
> (see [ROADMAP.md](ROADMAP.md)), and recorded in the decision log below.

> **Architectural principles:** extensible, schema-driven, provenance-preserving,
> FAIR-aligned, and reproducible (`raw → processed → outputs`, never reversed).

---

## High-level view

SciKG is layered. Data flows upward from sources to interfaces; provenance flows
downward so any answer traces back to its origin.

```
┌───────────────────────────────────────────────────────────────────────┐
│  6. Interaction Layer                                                   │
│     NL search · agent-based retrieval · APIs · notebooks · dashboards   │
├───────────────────────────────────────────────────────────────────────┤
│  5. AI / Retrieval Layer                                                │
│     LLMs · NL→query translation · RAG over graph · embeddings/semantic  │
├───────────────────────────────────────────────────────────────────────┤
│  4. Knowledge Graph Layer                                               │
│     graph store (RDF and/or property graph) · query (SPARQL/Cypher)     │
├───────────────────────────────────────────────────────────────────────┤
│  3. Semantic / Schema Layer                                             │
│     entity & relationship schemas · vocabularies · identifiers · PROV   │
├───────────────────────────────────────────────────────────────────────┤
│  2. Processing Layer                                                    │
│     ingestion · cleaning · normalization · entity resolution · mapping  │
├───────────────────────────────────────────────────────────────────────┤
│  1. Source / Data Layer                                                 │
│     external repositories · APIs · exports · data/raw → data/processed  │
└───────────────────────────────────────────────────────────────────────┘
         ▲ provenance is captured at every layer and attached to nodes/edges ▲
```

---

## Layer-by-layer

### 1. Source / Data Layer
- External repositories, APIs, and bulk exports (the project brief names the
  NHMFL / FT-ICR publication ecosystem as one *candidate* source — not yet
  investigated, and not a scope limit).
- Lands as **immutable** raw data in `data/raw/`; derived data in
  `data/processed/`.
- Each source is catalogued via the metadata inventory
  ([METADATA_INVENTORY.md](METADATA_INVENTORY.md)) before ingestion.

### 2. Processing Layer
- Ingestion, cleaning, normalization, parsing of unstructured fields.
- **Entity resolution / deduplication** across sources *(deferred — strategy
  undecided, for a later stage)*.
- Field→entity mapping per the entity-mapping templates.
- Every transformation emits a provenance record.
- Lives in `scripts/`; exploratory work in `notebooks/`.

### 3. Semantic / Schema Layer
- Machine-readable entity & relationship schemas (JSON Schema / SHACL).
- Vocabulary alignment (schema.org, Dublin Core, DCAT, PROV-O, SPAR, domain
  ontologies).
- **Identifier strategy**: reuse external PIDs (DOI/ORCID/ROR/RRID/IGSN), mint
  internal PIDs otherwise.
- **Provenance model**: PROV-O Entity/Activity/Agent on every node and edge.
- See [KNOWLEDGE_GRAPH_DESIGN.md](KNOWLEDGE_GRAPH_DESIGN.md).

### 4. Knowledge Graph Layer
- The canonical graph: typed, multi-relational, identifier-anchored (proposed
  properties).
- **Backend choice *(deferred — undecided)*:** RDF triplestore vs. labeled
  property graph vs. hybrid are all candidates. Each has trade-offs (interop vs.
  edge-property ergonomics); none has been selected.
- Query via SPARQL and/or Cypher (depends on the undecided backend); a library of
  saved query patterns is a possible future output.

### 5. AI / Retrieval Layer
- **Embeddings / semantic search** for fuzzy discovery over entities and text.
- **NL→structured-query translation** grounded in the schema (the schema
  constrains generation, reducing hallucination).
- **RAG over the graph**: answers are assembled from graph facts and **cited
  back to provenance**.
- **Agent-based retrieval**: multi-step traversal across entity types for
  compound questions.
- LLM choice is **undecided**; Anthropic Claude is one candidate, not a committed
  default.

### 6. Interaction Layer
- Natural-language search interface.
- Programmatic APIs and structured query endpoints.
- Notebooks, reports, and (later) dashboards.
- Generated artifacts land in `outputs/`.

---

## Cross-cutting concerns

### Provenance (mandatory, every layer)
Every fact records source, activity, agent, and time (PROV-O). This is what makes
SciKG reusable and reproducible and lets the AI layer cite its sources.

### FAIR compliance
Each component is checked against [FAIR_PRINCIPLES.md](FAIR_PRINCIPLES.md). FAIR
is a design constraint, not a feature.

### Reproducibility
`data/processed/` and `outputs/` must be regenerable from `data/raw/` plus code.
Raw is never edited in place.

### Data versioning *(deferred)*
Strategy for versioning `data/` (DVC, git-lfs, snapshots) and the graph itself
(temporal modeling vs. immutable snapshots) — to be decided.

### Security, access & governance *(deferred)*
Access control, licensing enforcement, and governance — to be designed before any
multi-source scale-up (a later stage). FAIR ≠ open: restricted assets are
described FAIRly with explicit access conditions.

### Observability & validation
Schema validation (SHACL/JSON Schema), provenance completeness checks, and
quality reports emitted to `outputs/`.

---

## Component-to-repository mapping

| Architecture component | Repository location |
|---|---|
| Raw source data | `data/raw/` |
| Processed / derived data | `data/processed/` |
| Ingestion & processing code | `scripts/` (future) |
| Schemas & vocabularies | `docs/` now → dedicated schema dir later |
| Exploration & prototyping | `notebooks/` |
| Generated graphs, exports, reports | `outputs/` |
| Design & decisions | `docs/` |

*(This mapping describes intended locations; the code/data components themselves
do not exist yet.)*

---

## Technology candidates (evaluate, don't commit yet)

Everything in this table is a **candidate under evaluation**. None has been
selected, installed, or committed to.

| Concern | Candidates |
|---|---|
| Graph store (RDF) | triplestore w/ SPARQL endpoint |
| Graph store (property) | Neo4j |
| Schema/validation | JSON Schema, SHACL (`pyshacl`) |
| Serialization | JSON-LD, RDF/Turtle |
| Graph libraries | `rdflib`, `networkx` |
| Identifiers | DOI, ORCID, ROR, RRID, IGSN, internal PIDs |
| Embeddings / semantic search | `sentence-transformers` + a vector store |
| LLM / agents | Anthropic Claude |
| Orchestration | TBD (depends on ingestion complexity) |

See `requirements.txt` for the candidate dependency list (none installed at this
stage).

---

## Key deferred decisions (decision log)

All decisions below are **Open** — no preference has been adopted. The "when"
column is an indicative grouping only, not an approved schedule.

| # | Decision | When (indicative) | Status |
|---|---|---|---|
| 1 | RDF vs. property graph vs. hybrid | later stage | Open — no option chosen |
| 2 | Canonical vocabularies | later stage | Open |
| 3 | Internal PID minting scheme | later stage | Open |
| 4 | Entity-resolution strategy | later stage | Open |
| 5 | Data/graph versioning approach | later stage | Open |
| 6 | Access control & governance model | later stage | Open |
| 7 | Vector store selection | later stage | Open |
| 8 | Implementation language (Python assumed) | later stage | Open |
| 9 | LLM provider (Claude is a candidate) | later stage | Open |

Record outcomes here as decisions are actually made, with date and rationale, so
the architecture remains a living, traceable document. Until then, do not present
any of these as settled elsewhere in the docs.
