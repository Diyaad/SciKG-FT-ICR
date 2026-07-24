# CLAUDE.md — SciKG Project Rules

## What this project is
A provenance-aware scientific knowledge graph for FT-ICR and
proteomics research at NHMFL. Built from 806 ICR journal articles
(from the MagLab CSV) plus five other sources. Six data sources
total: CrossRef API, the MagLab CSV (806 papers), the Web Applications
Group publications export, 46 Thermo RAW files, manual annotations, and
the 952 Blood Proteoform Atlas PXD files (local-only — gitignored, not
reproducible from a clean clone).
Loaded into Neo4j AuraDB (cloud, neo4j+s://): 4,900 nodes, 11,663 edges
(validation_report.json, load_cleared, 2026-07-24; live-graph verified;
instrument dedup 469 -> 443 Instrument; dataset-accession mint across three
batches, Dataset 289 -> 306, HAS_DATASET 279 -> 299; ORCID enrichment applied
as Researcher properties — no node/edge change). NOTE: docs/DISCOVERY_QUESTIONS.md
cites 4,909 / 11,668 (measured 2026-07-20, v1.0) — HIGHER than the current graph
by 9 nodes / 5 edges and not explained by the mints; flagged, not reconciled
(POSTER_FINDINGS.md T2). Do not overwrite that file's figure until it is traced.
Validation uses a
ground-truth set of 8 papers manually annotated by the team. 2-person
team, CI Compass Fellowship, June 1 – July 31 (8 weeks).

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
                469 Instrument [raw, pre-dedup; 03 dedups to 443 in the graph],
                51 Software) + INVOLVES_INSTITUTION,
                USES_INSTRUMENT, USES_SOFTWARE edges. Split across scripts:
                - transform_pdf_software.py  (BUILT, in scripts/): Software nodes
                  + USES_SOFTWARE edges; reads + preserves the Institution/
                  Instrument nodes already in pdf_entities.jsonl.
                - facility->Institution transform (finalize.py) and instrument
                  transform (finalize_inst.py): NOT in scripts/ — they lived in
                  session scratch and were RECOVERED to ~/scikg-scratch-all.
                  Both are CONFIRMED against the pickles their own runs wrote:
                  facility by exact identifier set (62 Institution + 89
                  INVOLVES_INSTITUTION); instrument on 461/462 nodes + 962/968
                  USES_INSTRUMENT edges (the one difference is one physical
                  instrument under two slugs, KI-7a, not a different producer).
                The real risk is REGENERATION, not reproducibility: pdf_entities.jsonl
                is committed, so a clean clone has all 524 Institution/Instrument
                nodes and the graph works. But transform_pdf_software.py READS
                pdf_entities.jsonl rather than creating it, so re-running the PDF
                transform after a fresh extraction produces Software only, silently,
                and the 524 Institution/Instrument nodes vanish. Anyone re-extracting
                must know this. Promotion is not a copy (the scratch scripts use
                per-module BASE/REPO literals and do repo I/O at import time).
                See docs/KNOWN_ISSUES.md KI-13.
03_normalize.py reads  data/processed/entities/
                writes data/processed/normalized/
04_validate.py  (built)
                reads  data/processed/normalized/
                writes data/processed/validated/entities/
                writes data/processed/validated/relationships/
                writes data/processed/validated/validation_report.json
                writes data/processed/validated/quarantine.jsonl
                exits non-zero on any quarantine or blocker
05_load.py      (run — graph loaded)
                reads  data/processed/validated/
                writes to Neo4j AuraDB via scripts/db.py
                Loaded 4,900 nodes + 11,663 edges (validation_report.json,
                load_cleared: true, 2026-07-24).
                NOTE: 05 is MERGE-only and cannot shrink the graph — a load that
                RETIRES nodes/edges (e.g. the instrument dedup) leaves stale data
                that needs a manual reconcile until a --prune step exists. See KI-14.
mint_dataset_operator_edges.py
                (run — human-gated post-load reconciliation, applied 2026-07-22)
                Mints PDF-extracted dataset_accession -> HAS_DATASET edges that
                02d extracts but never links (the C4 gap: PDF dataset accessions
                were extracted to disk but never became edges). Separate from 02d
                and GATED because these accessions carry FUZZY / hallucinated
                values (wrong-repo, mis-OCR'd, or invented accessions) that need
                human confirmation before they enter the graph — 02d must stay
                fabrication-free, so the human-review gate lives here, not in
                extraction. Flow: proposes edges to
                data/processed/review/proposed_dataset_operator_edges.jsonl for
                review; on approval, --emit writes the approved records to
                PRE-NORMALIZE JSONL (data/processed/entities/pdf_dataset_entities.jsonl,
                data/processed/relationships/pdf_dataset_relationships.jsonl) so they
                flow through 03 -> 04 -> 05 like any other extracted record. This
                preserves graph = f(files): the mint is committed source, not a
                direct graph write — PROVEN by a files-only rebuild into an empty
                Neo4j instance reproducing the 297/290 counts. First application
                added 8 Dataset + 11 HAS_DATASET (289 -> 297, 279 -> 290).
                HELD for David's ruling (NOT minted): MSV000* accessions (MassIVE
                native IDs, pending a namespace decision); new-namespace deposits
                (SRA / BioProject / BCO-DMO — no repository handler yet); PXD026178
                (cited in a PDF but no raw-file lineage in the graph); the
                other:0516284a PRIDE search-URL node (a candidate to fold into the
                Blood Proteoform Atlas PXD set); and raw-file OPERATORS, left
                intentionally unmodeled (FOXDEN data_creator carries no reliable
                person identity — no OPERATED_BY minted for PXD files).
ORCID enrichment sub-flow (post-load; properties only, human-gated ruling)
                Source: CrossRef structured author[].ORCID / authenticated-orcid —
                a deterministic per-DOI lookup, NOT text extraction and NOT inferred.
                Matching is bounded per paper (only against Researcher nodes already
                linked to that Publication by AUTHORED_BY; no global name search).
                Coverage: 475 of 2,076 Researcher nodes (22.9%) carry an orcid, split
                195 author-verified (authenticated-orcid: true) / 280 publisher-asserted
                (false). 63 candidates EXCLUDED, not applied: 31 rows on 7 reverse-error
                nodes (one node holding 2+ distinct ORCIDs), 30 compound-surname
                UNMATCHED, 2 fused. Enrichment enters through pre-normalize JSONL and
                flows 03 -> 04 -> 05, so graph = f(files) holds. See KI-16.
fetch_crossref_orcid.py
                caches CrossRef author/ORCID JSON for graph DOIs to
                data/processed/cache/crossref/ (gitignored)
analyze_orcid_coverage.py
                READ-ONLY; cache + graph -> data/processed/review/orcid_coverage_report.md
                + orcid_candidates.jsonl (bounded per-paper match, no global search)
emit_orcid_properties.py
                applies the eligibility ruling -> review/proposed_researcher_orcid_entities.jsonl
                + orcid_exclusions.jsonl (dry-run by default)
enrich_researchers_orcid.py
                writes orcid / orcid_authenticated into the committed
                data/processed/entities/researchers.jsonl in place; then re-run 03 -> 04 -> 05

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
- Graph database: Neo4j AuraDB (cloud), connection scheme neo4j+s://
  (credentials in .env at the repo root, read by scripts/db.py)
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
- Instrument dedup (03_normalize.py, applied 2026-07-21, 469 -> 443).
  Table-driven, EXACT-slug (never substring). Three David-authorized ops:
  (1) safe OCR/spacing typo merges the PDF signature-collapse mechanically
  missed (6 groups + one repaired hi-res node); (2) the 13 bare-generic
  FT-ICR spellings COLLAPSE into instrument:raw:ft_icr_ms @ MS:1003948
  (magnet-strength, hi-res/ultra-hi-res, vendor, ionization-prefixed, and
  custom-built FT-ICR nodes stay SEPARATE — do not fold them); (3) the
  conflated Velos node SPLITS into ltq_orbitrap_velos (hybrid, MS:1001742),
  velos_pro_linear_ion_trap (MS:1003495), and ltq_velos (distinct model,
  psi_ms_id null — CV has no LTQ Velos row); ltqorbitrap (plain LTQ
  Orbitrap) stays separate. 21T (21t_icr, MS:1003948, 168 papers) is
  unchanged. Rulings recorded in data/processed/review/instrument_review.md
  (SUPERSEDED banner). Do not revisit without David.
- RawDataFile identity is the COMPOSITE identifier
  rawfile:{filename}:{sha16} (filename + first 16 hex of sha256), NOT
  filename alone (KI-8, remediated 2026-07-20). Byte-identical files
  deposited under different names therefore load as DISTINCT nodes
  (21 such pairs on the current corpus). Each byte-identical set is
  recorded by an Advisory node (a new node type — 21 nodes) via FLAGS
  edges (42). Advisory carries a new source_type: graph_derived — a fact
  the pipeline computes from its own data, not extracted from a source.
  The uniqueness constraint is on identifier, not sha256_hash (sha256_hash
  is a non-unique property). See KI-8 and docs/SCIKG_SCHEMA.md (Node:
  RawDataFile, Node: Advisory).
- ORCID is PROPERTIES-ONLY; ORCID-as-canonical-identifier is DEFERRED (RULED
  2026-07-23). ENABLE_ORCID_CANONICALIZATION in 03_normalize.py is False and MUST
  NOT be flipped without a new ruling. WHY: with it True, 03 Pass 3 retires
  researcher:* -> orcid:* and rewrites AUTHORED_BY through the crosswalk; because
  05 is MERGE-only and cannot retire the superseded nodes (KI-14), the result is a
  DUPLICATE Researcher node set at orcid:* with authorship split across both — not a
  property set on the existing nodes. The flag was inert only because orcid was
  empty; now that 475 nodes carry ORCIDs, anyone who repopulates or re-runs without
  reading this WILL hit it. See docs/SCIKG_SCHEMA.md "ORCID (Added 2026-07-23)" and
  docs/KNOWN_ISSUES.md KI-16.
- Rebuild is reproducible from COMMITTED FILES, not re-derivable from original
  sources. A fresh clone runs 03 -> 04 -> 05 and reproduces the exact graph
  (files-only rebuild into an empty Neo4j instance — see the mint block above and
  KI-15). BUT data/raw/rawfiles_pxd/ (952 FOXDEN files) and data/raw/pdf_extraction/
  are local-only: a clone CANNOT re-run 02f or the PDF extraction. Their committed
  outputs (rawfiles_pxd.jsonl, pdf_entities.jsonl, pdf_relationships.jsonl) rebuild
  the nodes fine. This is pre-existing (KI-13), not a new gap.
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
