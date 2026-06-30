# SciKG — Scientific Knowledge Graph for FAIR Scientific Data Discovery

SciKG is a long-term research platform for improving the **discoverability,
accessibility, interoperability, and reusability** of scientific research
assets through structured metadata, knowledge graph technologies, and
AI-assisted exploration.

> **Status:** Active build — 8-week project, June 1 – July 31.
> 2-person team. CI Compass Fellowship. Extraction complete for all
> three sources (CrossRef, MagLab CSV, 46 RAW files); normalization,
> validation, and Neo4j load (stages 03-05) are the current work.

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
│   ├── raw/                         # Immutable source data
│   │   ├── publications/            # Raw CrossRef/OpenAlex responses
│   │   ├── maglab_icr_publications.csv
│   │   ├── rawfiles_metadata.csv    # Manual RAW-file filename metadata
│   │   ├── rawfiles_metadata/       # Original FOXDEN JSON (46 files)
│   │   ├── doi_list.csv
│   │   └── manifest.json            # Pipeline state tracker
│   └── processed/                   # Pipeline output at each stage
│       ├── rawfiles_enriched/       # FOXDEN + filename metadata merged (46 files)
│       ├── entities/                # Extracted records (JSONL)
│       ├── relationships/           # Extracted relationships (JSONL)
│       ├── normalized/              # (not yet populated)
│       └── validated/               # (not yet populated)
├── scripts/                         # Pipeline scripts — run in order
│   ├── 01_fetch.py
│   ├── 02_extract.py
│   ├── 02b_extract_csv.py
│   ├── merge_rawfile_metadata.py
│   ├── 02c_extract_rawfiles.py
│   ├── 03_normalize.py              # (not yet written)
│   ├── 04_validate.py              # (not yet written)
│   ├── 05_load.py                  # (not yet written)
│   └── db.py                       # (not yet written)
├── tests/                           # One test file per pipeline script
│   ├── test_fetch.py
│   ├── test_extract.py
│   ├── test_extract_csv.py
│   ├── test_extract_rawfiles.py
│   ├── test_normalize.py
│   ├── test_validate.py
│   └── test_load.py
├── notebooks/                       # Exploratory analysis and demo
├── outputs/                    
├── docs/                            # Project documentation
│   ├── SCIKG_SCHEMA.md
│   ├── ROADMAP.md
│   ├── FAIR_PRINCIPLES.md
│   ├── METADATA_INVENTORY.md
│   ├── VERIFIED_FACTS_AND_ASSUMPTIONS.md
│   ├── REVIEW_LOG.md
│   ├── controlled_vocabulary.md
│   ├── DISCOVERY_QUESTIONS.md
│   ├── archive/                     # Superseded design docs
│   │   ├── KNOWLEDGE_GRAPH_DESIGN.md
│   │   └── ARCHITECTURE.md
│   └── metadata_templates/
├── README.md
├── CLAUDE.md
├── requirements.txt
└── .gitignore
```

## Documentation Index

| Document | Purpose |
|---|---|
| [docs/SCIKG_SCHEMA.md](docs/SCIKG_SCHEMA.md) | Authoritative v1.0 schema — node types, relationships, identifiers, provenance rules |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Proposed, evolving research workflow (not an approved plan) |
| [docs/FAIR_PRINCIPLES.md](docs/FAIR_PRINCIPLES.md) | FAIR notes and how each principle maps to design decisions |
| [docs/METADATA_INVENTORY.md](docs/METADATA_INVENTORY.md) | Metadata cataloguing approach + template usage |
| [docs/DISCOVERY_QUESTIONS.md](docs/DISCOVERY_QUESTIONS.md) | The 17 questions the graph is designed to answer |
| [docs/VERIFIED_FACTS_AND_ASSUMPTIONS.md](docs/VERIFIED_FACTS_AND_ASSUMPTIONS.md) | Verified facts vs. proposed ideas vs. unknowns |
| [docs/REVIEW_LOG.md](docs/REVIEW_LOG.md) | Log of review-worthy changes and assumptions |
| [docs/archive/KNOWLEDGE_GRAPH_DESIGN.md](docs/archive/KNOWLEDGE_GRAPH_DESIGN.md) | Entity/relationship model and ontology notes (superseded by SCIKG_SCHEMA.md) |
| [docs/archive/ARCHITECTURE.md](docs/archive/ARCHITECTURE.md) | Forward-looking architecture notes (superseded) |
| [docs/metadata_templates/](docs/metadata_templates/) | Fillable inventory templates (CSV/YAML), no fabricated rows |

---

## Current Focus

Extraction stages are complete for all three sources (CrossRef API,
MagLab CSV, and 46 RAW files). Normalization, validation, and Neo4j
load (stages 03-05) are the current work.

Building a provenance-aware knowledge graph from 806 ICR journal
articles (from the MagLab CSV) plus four other sources: the CrossRef
API, the Web Applications Group publications export, 46 Thermo RAW
files, and manual annotations. Graph loaded into Neo4j (local).
Validated against a ground-truth set of 8 manually annotated papers.
Software and Instrument are logged as entities.

Extending coverage to further NHMFL facilities is a future phase.

Out of scope for this phase: scraping, chatbot, Streamlit UI, NetworkX.

---

## Getting Started (contributors)

```bash
# 1. Clone the repository
git clone <repo-url>
cd scikg

# 2. Install dependencies (requests, neo4j, pytest, python-dotenv)
pip install -r requirements.txt

# 3. Set up a local Neo4j instance (Neo4j Desktop)

# 4. Run the pipeline scripts in order
python scripts/01_fetch.py
python scripts/02_extract.py
python scripts/02b_extract_csv.py
python scripts/02c_extract_rawfiles.py
python scripts/03_normalize.py
python scripts/04_validate.py
python scripts/05_load.py
```

Read the foundation docs first: README.md → docs/ROADMAP.md →
docs/FAIR_PRINCIPLES.md → docs/KNOWLEDGE_GRAPH_DESIGN.md →
docs/ARCHITECTURE.md. Propose changes via PR; keep raw data immutable.

---

## License & Citation

License and citation guidance to be defined in a later phase. Until then, treat
this repository as internal research material.
