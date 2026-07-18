# CLAUDE.md — SciKG Project Rules

## What this project is
A provenance-aware scientific knowledge graph for FT-ICR and
proteomics research at NHMFL. Built from 806 ICR journal articles
(from the MagLab CSV) plus five other sources. Six data sources
total: CrossRef API, the MagLab CSV (806 papers), the Web Applications
Group publications export, 46 Thermo RAW files, manual annotations, and
the 952 Blood Proteoform Atlas PXD files (local-only — gitignored, not
reproducible from a clean clone).
Loaded into Neo4j (local). Validation uses a ground-truth set of 8
papers manually annotated by the team. 2-person team, CI Compass
Fellowship, June 1 – July 31 (8 weeks).

## Pipeline — always run in this exact order
01_fetch.py     reads  data/raw/doi_list.csv
                writes data/raw/publications/{doi_safe}.json
01b_fetch_pdfs.py
                reads  data/raw/maglab_icr_publications.csv
                writes data/raw/pdfs/{doi_safe}.pdf
                writes data/processed/logs/pdf_fetch_log.jsonl
02_extract.py   reads  data/raw/publications/
                writes data/processed/entities/
02b_extract_csv.py
                reads  data/raw/maglab_icr_publications.csv
                writes data/processed/entities/
merge_rawfile_metadata.py
                reads  data/raw/rawfiles_metadata.csv
                reads  data/raw/rawfiles_metadata/*.json
                writes data/processed/rawfiles_enriched/*.json
02c_extract_rawfiles.py
                reads  data/processed/rawfiles_enriched/*.json
                writes data/processed/entities/rawfiles.jsonl
                writes data/processed/entities/samples.jsonl
                writes data/processed/entities/software.jsonl
                writes data/processed/entities/instruments.jsonl (append)
                writes data/processed/relationships/rawfile_relationships.jsonl
02f_extract_pxd_rawfiles.py
                reads  data/raw/rawfiles_pxd/*.json (LOCAL-ONLY, gitignored)
                writes data/processed/entities/rawfiles_pxd.jsonl
                writes data/processed/entities/instruments.jsonl (append)
                writes data/processed/entities/software.jsonl (append)
                writes data/processed/relationships/rawfiles_pxd_relationships.jsonl
                writes data/processed/logs/pxd_extract_log.jsonl
02d_extract_pdf.py  (built; under evaluation — outputs below produced when run)
                reads  data/processed/entities/publications.jsonl
                reads  data/raw/pdfs/{doi_safe}.pdf
                writes data/processed/pdf_text/{doi_safe}.md
                writes data/processed/entities/pdf_extracted.jsonl
PDF transform (02d extraction -> entity/relationship nodes)
                reads  data/raw/pdf_extraction/pdf_extraction_378papers.jsonl
                writes data/processed/entities/pdf_entities.jsonl
                writes data/processed/relationships/pdf_relationships.jsonl
                Populates THREE of the graph's node types (62 Institution,
                469 Instrument, 51 Software) + INVOLVES_INSTITUTION,
                USES_INSTRUMENT, USES_SOFTWARE edges. Split across scripts:
                - transform_pdf_software.py  (BUILT, in scripts/): Software nodes
                  + USES_SOFTWARE edges; reads + preserves the Institution/
                  Instrument nodes already in pdf_entities.jsonl.
                - facility->Institution transform: NOT in scripts/ (scratch,
                  uncommitted — see docs/pdf_transform_logic.md §6,
                  finalize_pdf_facility.py). Produced the 62 Institution nodes +
                  89 INVOLVES_INSTITUTION edges.
                - instrument transform: NOT in scripts/ (scratch, uncommitted).
                  Produced the 462 PDF Instrument nodes + USES_INSTRUMENT edges.
                (Output is on disk; the two uncommitted transforms cannot be
                re-run from a clean clone. A stage named here without its code is
                still better than an unmentioned stage.)
03_normalize.py reads  data/processed/entities/
                writes data/processed/normalized/
04_validate.py  (built)
                reads  data/processed/normalized/
                writes data/processed/validated/entities/
                writes data/processed/validated/relationships/
                writes data/processed/validated/validation_report.json
                writes data/processed/validated/quarantine.jsonl
                exits non-zero on any quarantine or blocker
05_load.py      (drafted — not yet run)
                reads  data/processed/validated/
                writes to Neo4j via scripts/db.py

## Non-negotiable rules
- Never fabricate scientific data, metadata, or relationships
- Never infer metadata not explicitly present in a source document
  or API response
- Never add nodes or edges to the graph without a traceable
  source reference
- Never modify any file in data/raw/ — immutable after write.
  data/raw/ is immutable source data committed to the repo, WITH ONE
  EXCEPTION: data/raw/rawfiles_pxd/ (952 Blood Proteoform Atlas FOXDEN
  metadata files) is gitignored and local-only. It contains internal
  infrastructure details (hostnames, IPs, Windows paths) and is
  externally-owned data not ours to publish. RawDataFile nodes derived
  from it carry sha256_hash for verification against the originals.
  Consequence: the 02f stage cannot be reproduced from a clean clone —
  it requires the local source, and 02f fails with an explicit message
  if the directory is absent.
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
- Authoritative schema: docs/SCIKG_SCHEMA.md (node types,
  relationships, identifiers, provenance properties, normalization
  and validation rules)
- Graph database: Neo4j, running locally (Neo4j Desktop)
- Metadata sources: six sources (CrossRef API, MagLab CSV, Web Apps
  export, 46 Thermo RAW files, manual annotations, and the 952 Blood
  Proteoform Atlas PXD files — local-only, gitignored). DOI is the
  master key for publications
- Provenance: properties on nodes and edges, no ProvenanceRecord node
- Corpus: 806 ICR journal articles from the MagLab CSV
- Ground truth: 8 manually annotated papers (validation set only)
- Software and Instrument are logged entities
- Instrument identity is derived from the FOXDEN 'model' field, not
  'name' (model is the reliable field; name can be a stale Tune-file
  string). Both 02c and 02f follow this. Controlled-vocabulary
  instrument terms were audited against PSI-MS via EBI OLS4 and
  corrected (several had used generic analyzer/parent accessions as
  specific instruments — the MS:1000079 class).
- Removed from scope: Workflow entity, Streamlit UI, chatbot, NetworkX,
  ASSOCIATED_WITH relationship, ProvenanceRecord node
- RAW-file relationships: OPERATED_BY, CONTAINS_SAMPLE, COLLECTED_ON,
  and ACQUIRED_WITH are active and loaded (confirmed 2026-06-30,
  implemented in 02c_extract_rawfiles.py).
- UNDER REVIEW (pending confirmation): ANALYZED_IN (RAW file ->
  Publication) — target publication not yet confirmed. Do not
  assert this relationship as decided or load it until confirmed.

## If unsure whether something is allowed
Check docs/VERIFIED_FACTS_AND_ASSUMPTIONS.md first.
If not answered there, ask before acting.
