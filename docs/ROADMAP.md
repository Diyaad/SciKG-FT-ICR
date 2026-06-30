# SciKG 8-Week Roadmap

CI Compass Fellowship project: June 1 - July 31, 2026
2-person team: Diya and Veronika, mentored by David Butcher at NHMFL.

## Week 1 (Jun 1-7) - Foundation
Status: DONE

- Repository setup
- CrossRef fetch (01_fetch.py)
- 17 papers extracted (02_extract.py)
- Controlled vocabulary drafted with PSI-MS, UNIMOD, NCBI Taxonomy, UniProt
- FAIR principles documented

## Week 2 (Jun 8-15) - Design
Status: DONE

- Manual annotation of 8 ground-truth papers (paper_reviews.md)
- Initial schema sketched
- Ontology standards confirmed: PSI-MS, UNIMOD, NCBI Taxonomy, UniProt, 
  ORCID, ROR, DataCite, Bioschemas, PROV-O

## Week 3 (Jun 16-22) - Extraction infrastructure
Status: DONE

- MagLab CSV with 806 papers integrated into raw data
- Repository audit run (audit_repo.py)
- Schema locked in docs/SCIKG_SCHEMA.md
- Naming conventions and identifier strategy decided
- 02b_extract_csv.py written and run on full 806-row CSV
- 7 entity JSONL files and 1 relationships file produced
- FOXDEN-formatted metadata for 46 RAW files added to data/raw/

## Week 4 (Jun 23-29) - RAW files and normalization
Status: IN PROGRESS

- Decisions confirmed with David: WCL = Whole Cell Lysate, J = run 
  letter
- ANALYZED_IN target still pending verification
- 02c_extract_rawfiles.py to be written this week
- 03_normalize.py started

## Week 5 (Jun 30 - Jul 6) - Neo4j load and validation
Status: PLANNED

- Neo4j Aura Free instance setup
- 04_validate.py written and run
- 05_load.py written and run
- Full pipeline runs end-to-end producing the graph
- ANALYZED_IN target verification: inspect RAW file FOXDEN JSONs for 
  DOI references to confirm or reject the PEPPI-MS hypothesis
- Optional: start PDF extraction (02d_extract_pdf.py) on RCC

## Week 6 (Jul 7-13) - Discovery queries and refinement
Status: PLANNED

- Cypher queries for all 17 discovery questions
- Query performance tuning
- Accuracy checks against the 8 annotated papers
- ICR group review of results

## Week 7 (Jul 14-20) - Poster and documentation
Status: PLANNED

- Poster design
- README finalization
- Schema diagram export
- Deliverable package for handoff

## Week 8 (Jul 21-27) - Buffer and presentation
Status: PLANNED

- Final fixes from poster feedback
- Presentation rehearsal
- Optional extensions

## Open questions (still pending)
- RCC access setup completion
- LangExtract vs Gemini API decision for PDF extraction
- PDF extraction approach refinement
- ANALYZED_IN target for 46 RAW files
