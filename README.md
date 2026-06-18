# SciKG — Scientific Knowledge Graph for FAIR Scientific Data Discovery

SciKG is a long-term research platform for improving the **discoverability,
accessibility, interoperability, and reusability** of scientific research
assets through structured metadata, knowledge graph technologies, and
AI-assisted exploration.

> **Status:** Active build — Week 1 of 6. 2-person team.
> CI Compass Fellowship. Pipeline under construction.
> No production data loaded yet.

---

## Why SciKG

Scientific facilities and research organizations repeatedly face the same
structural problems:

- Fragmented datasets spread across systems, formats, and storage tiers
- Inconsistent or missing metadata
- Limited provenance tracking
- Difficulty locating historical experiments
- Weak connections between publications, datasets, instruments, researchers,
  projects, grants, and scientific concepts
- Barriers to knowledge reuse and scientific reproducibility

SciKG treats these as a **knowledge-organization problem**: if research assets
and their relationships are captured as a well-described graph, they become
findable, linkable, and reusable — by both humans and machines.

---

## Vision

Build a flexible, extensible platform that models the scientific research
ecosystem as a knowledge graph and layers AI-assisted retrieval on top, so that
a researcher can ask *"what experiments used instrument X on sample type Y, and
which publications and grants are connected to them?"* and get a grounded,
traceable answer.

The architecture is designed from day one to integrate (over time):

publications · datasets · experimental metadata · research projects · grants &
funding · instruments & facilities · samples & materials · researchers &
collaborators · processing workflows · provenance records · scientific methods ·
external repositories · knowledge graph databases · large language models ·
agent-based retrieval · natural-language search interfaces

---

## FAIR Alignment

SciKG is designed around the [FAIR principles](docs/FAIR_PRINCIPLES.md):

| Principle | How SciKG approaches it |
|---|---|
| **Findable** | Rich metadata, persistent identifiers, searchable relationships |
| **Accessible** | Standardized retrieval mechanisms, clear access pathways |
| **Interoperable** | Structured schemas, standard vocabularies, machine-readable metadata |
| **Reusable** | Provenance tracking, context preservation, documentation & reproducibility support |

---

## Repository Layout

```
scikg/
├── data/
│   ├── raw/            # Immutable source data (never edited by hand)
│   └── processed/      # Cleaned / transformed data derived from raw
├── scripts/            # Pipeline & utility code (future)
├── notebooks/          # Exploratory analysis & prototyping
├── outputs/            # Generated artifacts: graphs, reports, exports
├── docs/               # Research foundation (see below)
│   ├── ROADMAP.md
│   ├── FAIR_PRINCIPLES.md
│   ├── KNOWLEDGE_GRAPH_DESIGN.md
│   ├── METADATA_INVENTORY.md
│   ├── ARCHITECTURE.md
│   ├── VERIFIED_FACTS_AND_ASSUMPTIONS.md
│   ├── REVIEW_LOG.md
│   └── metadata_templates/
├── README.md
├── CLAUDE.md           # Guidance for AI coding assistants
├── requirements.txt    # Candidate dependencies (not yet installed)
└── .gitignore
```

## Documentation Index

| Document | Purpose |
|---|---|
| [docs/ROADMAP.md](docs/ROADMAP.md) | Proposed, evolving research workflow (not an approved plan) |
| [docs/FAIR_PRINCIPLES.md](docs/FAIR_PRINCIPLES.md) | FAIR notes and how each principle maps to design decisions |
| [docs/KNOWLEDGE_GRAPH_DESIGN.md](docs/KNOWLEDGE_GRAPH_DESIGN.md) | Entity/relationship model and ontology notes |
| [docs/METADATA_INVENTORY.md](docs/METADATA_INVENTORY.md) | Metadata cataloguing approach + template usage |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Forward-looking architecture notes (nothing finalized) |
| [docs/VERIFIED_FACTS_AND_ASSUMPTIONS.md](docs/VERIFIED_FACTS_AND_ASSUMPTIONS.md) | Verified facts vs. proposed ideas vs. unknowns |
| [docs/REVIEW_LOG.md](docs/REVIEW_LOG.md) | Log of review-worthy changes and assumptions |
| [docs/metadata_templates/](docs/metadata_templates/) | Fillable inventory templates (CSV/YAML), no fabricated rows |

---

## Current Focus

Building a provenance-aware knowledge graph prototype from ~50
FT-ICR and proteomics papers sourced from the MagLab publications
page. Metadata fetched via CrossRef and OpenAlex APIs. Graph
loaded into Neo4j. Validated against an 11-paper manually reviewed
ground-truth set.

This is a feasibility prototype — Phase 1 of an extensible system.
Phase 2 will scale to 500+ papers and additional NHMFL facilities.

Out of scope for this phase: scraping, LLM inference, natural
language interface, Streamlit UI, chatbot, NetworkX.

---

## Getting Started (contributors)

```bash
# 1. Read the foundation docs in this order:
#    README.md → docs/ROADMAP.md → docs/FAIR_PRINCIPLES.md
#    → docs/KNOWLEDGE_GRAPH_DESIGN.md → docs/ARCHITECTURE.md
# 2. Review the metadata templates in docs/metadata_templates/
# 3. Propose changes via PR; keep raw data immutable.
```

A Python environment will be introduced in a later phase. `requirements.txt`
lists *candidate* dependencies for planning only — do not install yet.

---

## License & Citation

License and citation guidance to be defined in a later phase. Until then, treat
this repository as internal research material.
