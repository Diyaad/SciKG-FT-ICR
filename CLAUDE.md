# CLAUDE.md — SciKG Project Rules

## What this project is
A provenance-aware scientific knowledge graph for FT-ICR and
proteomics research at NHMFL. Built from ~50 papers fetched via
CrossRef and OpenAlex APIs, loaded into Neo4j, validated against
an 11-paper manual ground-truth set. 2-person team.
CI Compass Fellowship project.

## Pipeline — always run in this exact order
01_fetch.py     reads  data/raw/doi_list.csv
                writes data/raw/publications/{doi_safe}.json
02_extract.py   reads  data/raw/publications/
                writes data/processed/entities/
03_normalize.py reads  data/processed/entities/
                writes data/processed/normalized/
04_validate.py  reads  data/processed/normalized/
                writes data/processed/validated/
                writes data/processed/validation_report.json
                writes data/processed/quarantine.jsonl
05_load.py      reads  data/processed/validated/
                writes to Neo4j via scripts/db.py

## Non-negotiable rules
- Never fabricate scientific data, metadata, or relationships
- Never infer metadata not explicitly present in a source document
  or API response
- Never add nodes or edges to the graph without a traceable
  source reference
- Never modify any file in data/raw/ — immutable after write
- Never skip or reorder pipeline stages
- Never write data directly to Neo4j without running the full
  pipeline first
- Never create placeholder or synthetic scientific records
- Never call external APIs without explicit instruction
- Never install packages not in requirements.txt without asking

## What you may do
- Write or edit files in scripts/
- Write or edit files in docs/
- Write or edit files in tests/
- Read any file in the repository
- Suggest additions to requirements.txt with justification

## Ownership
Person 1 owns: scripts/, Neo4j setup, schema
Person 2 owns: data/raw/doi_list.csv, docs/controlled_vocabulary.md,
               docs/DISCOVERY_QUESTIONS.md, all WEEK_FINDINGS.md files
Shared: docs/SCIKG_SCHEMA.md, docs/VERIFIED_FACTS_AND_ASSUMPTIONS.md,
        docs/REVIEW_LOG.md, tests/

## Architecture decisions — do not revisit
- Graph database: Neo4j (or Kuzu if server setup is a blocker)
- Metadata sources: CrossRef API then OpenAlex API. DOI is master key
- Provenance: properties on nodes and edges, no ProvenanceRecord node
- Corpus: ~50 FT-ICR and proteomics papers from MagLab publications page
- 11 manually reviewed papers are ground-truth validation set only
- Removed from scope: Software entity, Workflow entity, Streamlit UI,
  chatbot, NetworkX, ASSOCIATED_WITH relationship, ProvenanceRecord node

## If unsure whether something is allowed
Check docs/VERIFIED_FACTS_AND_ASSUMPTIONS.md first.
If not answered there, ask before acting.
