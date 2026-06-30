# CLAUDE.md — SciKG Project Rules

## What this project is
A provenance-aware scientific knowledge graph for FT-ICR and
proteomics research at NHMFL. Built from 806 ICR journal articles
(from the MagLab CSV) plus four other sources. Five data sources
total: CrossRef API, the MagLab CSV (806 papers), the Web Applications
Group publications export, 46 Thermo RAW files, and manual annotations.
Loaded into Neo4j (local). Validation uses a ground-truth set of 8
papers manually annotated by the team. 2-person team, CI Compass
Fellowship, June 1 – July 31 (8 weeks).

## Pipeline — always run in this exact order
01_fetch.py     reads  data/raw/doi_list.csv
                writes data/raw/publications/{doi_safe}.json
02_extract.py   reads  data/raw/publications/
                writes data/processed/entities/
02b_extract_csv.py
                reads  data/raw/maglab_icr_publications.csv
                writes data/processed/entities/
02c_extract_rawfiles.py
                reads  data/raw/rawfile_names.txt and local .raw files
                writes data/processed/entities/rawfiles.jsonl
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

## Architecture decisions — do not revisit
- Graph database: Neo4j, running locally (Neo4j Desktop)
- Metadata sources: five sources (CrossRef API, MagLab CSV, Web Apps
  export, 46 Thermo RAW files, manual annotations). DOI is the master
  key for publications
- Provenance: properties on nodes and edges, no ProvenanceRecord node
- Corpus: 806 ICR journal articles from the MagLab CSV
- Ground truth: 8 manually annotated papers (validation set only)
- Software and Instrument are logged entities
- Removed from scope: Workflow entity, Streamlit UI, chatbot, NetworkX,
  ASSOCIATED_WITH relationship, ProvenanceRecord node
- UNDER REVIEW (pending confirmation): RAW-file relationships —
  whether a RAW file links to a publication, a dataset deposit such as
  OSF/MassIVE, a project, or stands alone. Do not assert a RAW-file
  relationship as decided until confirmed

## If unsure whether something is allowed
Check docs/VERIFIED_FACTS_AND_ASSUMPTIONS.md first.
If not answered there, ask before acting.
