# CLAUDE.md — SciKG Project Rules

## What this project is
A provenance-aware scientific knowledge graph for FT-ICR and
proteomics research at NHMFL. Built from 806 ICR journal articles
(from the MagLab CSV) plus five other sources. Six data sources
total: CrossRef API, the MagLab CSV (806 papers), the Web Applications
Group publications export, 46 Thermo RAW files, manual annotations, and
the 952 Blood Proteoform Atlas PXD files (local-only — gitignored, not
reproducible from a clean clone).
Loaded into Neo4j AuraDB (cloud, neo4j+s://3e16fe28): 4,886 nodes, 11,690 edges
(production, load_cleared, 2026-07-25; live-graph verified). Researcher
2,076 -> 2,062 via the researcher-identifier slug fix (14 accent-collapse merges,
see Architecture decisions); prior state was 4,900/11,663. Also: instrument dedup
469 -> 443 Instrument; dataset-accession mint across three batches, Dataset
289 -> 306, HAS_DATASET 279 -> 299; ORCID enrichment 481 of 2,062 Researcher
nodes (192 author-verified / 279 publisher-asserted / 10 human-review, no CrossRef
attestation). The researcher-equivalence layer IS loaded to production:
SAME_AS = 27, POSSIBLY_SAME_AS = 0 (live-verified 2026-07-25). It arrived in two
additive loads with NO node change: the 3 ORCID-anchored edges (11,663 -> 11,666)
and then today's 24 human-reviewed edges (11,666 -> 11,690). CORRECTION: this file
previously said the 3 were "NOT yet loaded to production" — they had in fact
already been applied; production was never at 11,663 once they landed.
NOTE: docs/DISCOVERY_QUESTIONS.md cites 4,909 / 11,668 (measured
2026-07-20, v1.0) — its NODE count is still HIGHER than the current graph by 23 and
is not explained by the mints; that is the unreconciled part. Its EDGE count is now
LOWER by 22, but only because today's +24 SAME_AS overtook it — the edge gap flipped
sign and is no longer a useful signal; the node gap is. Flagged, not reconciled
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
                Loaded 4,886 nodes + 11,690 edges (production, load_cleared: true,
                2026-07-25; Researcher 2,062 after the slug fix, SAME_AS 27).
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
                HELD for a maintainer ruling (NOT minted): MSV000* accessions (MassIVE
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
                Coverage from THIS (CrossRef) path: 471 of 2,062 Researcher nodes
                (22.8%) carry an orcid, split 192 author-verified (authenticated-orcid:
                true) / 279 publisher-asserted (false). 63 candidates EXCLUDED, not
                applied: 31 rows on 6 reverse-error nodes (one node holding 2+ distinct
                ORCIDs — anderson_l, huang_c, lin_y, smith_l, zhang_y, zhang_z; this
                file previously said 7, measured 6 in orcid_exclusions.jsonl 2026-07-25),
                30 compound-surname UNMATCHED (researcher_id null — no node to attach
                to), 2 fused (martin_b). Enrichment enters through pre-normalize JSONL
                and flows 03 -> 04 -> 05, so graph = f(files) holds.
                (Was 475/2,076 before the slug fix collapsed 14 accent-variant nodes;
                the 4-node drop is 4 both-ORCID accent pairs merging into one node
                each.) See KI-16.
                A SECOND, non-CrossRef path added 10 more on 2026-07-25 (see the
                researcher-equivalence sub-flow below), bringing the graph total to
                481 of 2,062 (23.3%). Those 10 have orcid_authenticated NULL, so the
                192/279 split above still describes the CrossRef path exactly:
                481 = 192 true + 279 false + 10 null (live-verified).
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
Researcher-equivalence sub-flow (post-load; SAME_AS / POSSIBLY_SAME_AS, KI-17)
                No extractor script — edges are authored to
                data/processed/relationships/researcher_equivalence.jsonl and flow
                03 -> 04 -> 05 like any other relationship file (durable, never
                direct-to-graph). SAME_AS (proven, shared ORCID) is emitted directly;
                POSSIBLY_SAME_AS (inferred) goes through human review before any emit:
                candidates and their dispositions live in the committed review sheet
                docs/researcher_equivalence_review.md, and the outcome is recorded in
                KI-17. The reviewer hand-off itself is sent out of band and is
                deliberately NOT tracked, so no committed file cites it.
                New types must be registered in 04 RELATIONSHIP_FILES + 05 REL_TYPES.
                STATE (live-verified 2026-07-25): 27 SAME_AS in production, 0
                POSSIBLY_SAME_AS. Split by anchor_type: 24 human_review, 2 orcid,
                1 surname_change. All 27 carry source_type graph_derived and
                confidence proven (the schema constrains SAME_AS to both).
                The 24 human_review edges came from the 2026-07-25 emit of the
                reviewed candidate set (input: data/processed/review/
                researcher_equivalence_EMIT.md; source_id review:researcher_
                equivalence_EMIT.md on every edge). Their proof is a reviewer's
                judgment, NOT a shared ORCID — anchor_type human_review is what
                records that distinction, and `properties.orcid` is null on all 24.
                mechanism distribution: 14 ocr_variant, 2 period_parse, 2
                spelling_variant, 2 transliteration, 1 each corrected_exclusion /
                spelling_variant_ae_umlaut / suffix_jr / transposition.
                The same emit SET 10 Researcher `orcid` properties the reviewer
                found. Those node records keep source_type `csv` (unchanged): no
                enum value covers CSV identity + human-review orcid, and
                merged_csv_api is defined as CSV identity + CrossRef-API orcid,
                which these are not. Origin is carried in source_id (orcid:{value}
                + review:researcher_equivalence_EMIT.md) and evidence_note instead.
                orcid_authenticated is left NULL on all 10 — it is the CrossRef
                authenticated-orcid flag and no CrossRef attestation exists, so
                `false` would falsely read as publisher-asserted. Both RULED
                2026-07-25. Do not "fix" either by inventing an enum value.

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
  Table-driven, EXACT-slug (never substring). Three maintainer-authorized ops:
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
  (SUPERSEDED banner). Do not revisit without a new maintainer ruling.
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
  empty; now that 481 nodes carry ORCIDs, anyone who repopulates or re-runs without
  reading this WILL hit it. See docs/SCIKG_SCHEMA.md "ORCID (Added 2026-07-23)" and
  docs/KNOWN_ISSUES.md KI-16.
- Rebuild is reproducible from COMMITTED FILES, but NOT re-derivable from original
  sources — these are different guarantees. A fresh clone runs 03 -> 04 -> 05 and
  reproduces the EXACT graph (VERIFIED 2026-07-24: a clean rebuild from commit 900c651
  into an empty Neo4j instance reproduced 4,886/11,663 exactly. RE-VERIFIED 2026-07-25
  after the human_review SAME_AS emit: a files-only 03 -> 04 -> 05 into an empty Docker
  Neo4j reproduced 4,886/11,690 with SAME_AS 27, and the subsequent production load
  created 0 nodes / 24 edges — the two agree). BUT re-running the
  02x EXTRACTORS does NOT reproduce the graph, because THREE committed files are
  hand-maintained migrations a clean extractor run overwrites/destroys:
    * pdf_entities.jsonl + pdf_relationships.jsonl — 62 Institution + Instrument + 51
      Software; the facility/instrument transforms are not in scripts/ (KI-13).
    * pdf_dataset_entities.jsonl + pdf_dataset_relationships.jsonl — the dataset mint;
      its input ledger was deleted from the repo (mint --emit is non-runnable).
    * software.jsonl — the Xcalibur collapse (7 versioned nodes -> 1 software:xcalibur,
      versions moved to ACQUIRED_WITH.version). A clean 02c/02f run regenerates the 8
      raw versioned nodes WITHOUT canonical_name -> 04 quarantines them (proven this
      session). Also data/raw/rawfiles_pxd/ (952 FOXDEN) and data/raw/pdf_extraction/
      are local-only (02f / PDF extraction can't run from a clean clone).
  RULE: rebuild from committed files (03 -> 04 -> 05), NEVER "clear and re-run all
  extractors" — that was the mistake that destroyed the Xcalibur collapse mid-rebuild.
  A researcher-only change regenerates ONLY researchers.jsonl + AUTHORED_BY (csv_
  relationships) + the OPERATED_BY endpoint; everything else is restored from HEAD.
  See KI-13.
- Researcher identifier scheme (CHANGED 2026-07-24, KI-16). New form
  researcher:{translit_family}_{initial}[_seq]: family is NFKD-transliterated
  (accents dropped, hyphens/spaces normalized together, so "Chacón-Patiño" and
  "Chacon Patino" share one slug), given is the FIRST initial only, and there is
  NO YEAR. The year was dropped because it was order-dependent (first-seen wins in
  02b, so the same person got a different suffix by CSV row order) — a fragmentation
  source, and all 14 same-key collisions were fragmentations (one person), never two
  different people (ORCID-verified 0 false collapses). _seq is appended only on a
  genuine future collision (0 today), deterministically (earliest year -> first DOI).
  SURVIVOR RULE (03_normalize.py, the project's preserve-accents ruling): when accent
  variants collapse, the surviving name_full is the MOST DIACRITIC-RICH form, but
  fused "A and B" forms are FILTERED FIRST (so a co-author's accent never wins the
  name — the Marshall/Brüschweiler inversion). Slugs are ASCII; names keep diacritics.
  translit_family() is researcher-only; slugify() is UNCHANGED for
  instrument/facility/journal (their dedup tables are keyed on the ASCII forms).
- Researcher equivalence (NEW 2026-07-24, EXTENDED 2026-07-25, KI-17). Two
  non-destructive, undirected Researcher<->Researcher edge types, stored ONE per pair
  from the lex-earlier identifier; NEITHER merges/retires/repoints (both nodes and
  names kept). SAME_AS = PROVEN; POSSIBLY_SAME_AS = INFERRED (typo/co-author,
  human-confirm). PRODUCTION: 27 SAME_AS, 0 POSSIBLY_SAME_AS (live-verified
  2026-07-25). Two proof classes share the one SAME_AS type, distinguished by
  anchor_type — do not conflate them:
    * 3 ORCID-ANCHORED (anchor_type orcid x2 / surname_change x1): proof is a shared
      author-verified ORCID spanning both nodes, carried in properties.orcid.
      aguilera<->chacon_patino (surname change), hoeschen<->hoschen,
      salvato_vallverdu<->vallverdu.
    * 24 HUMAN-REVIEWED (anchor_type human_review): proof is a reviewer's judgment on
      mechanical-artifact pairs (OCR/spelling/transliteration/period-parse), NOT a
      shared ORCID; properties.orcid is null on all 24. Emitted 2026-07-25 from
      data/processed/review/researcher_equivalence_EMIT.md.
  All 27 carry source_type graph_derived + confidence proven (schema-constrained).
  A consumer that needs ORCID-grade proof must filter on anchor_type, not on the
  SAME_AS type alone. The candidate set that fed this is now RESOLVED: 24 emitted,
  1 HELD (angstrom_j<->anstrom_j, unresolved), 11 confirmed different (no edge).
  Query undirected: MATCH (a)-[:SAME_AS]-(b). GOTCHA — a NEW relationship type must be
  registered in BOTH scripts/04_validate.py RELATIONSHIP_FILES (valid input files)
  AND scripts/05_load.py REL_TYPES (loadable types); 03 and 04 pass without it but 05
  ABORTS. POSSIBLY_SAME_AS is deliberately kept OUT of REL_TYPES so a premature
  inferred edge aborts 05 rather than loading unreviewed.
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
