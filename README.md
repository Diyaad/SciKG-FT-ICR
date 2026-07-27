# SciKG — Scientific Knowledge Graph for FAIR Scientific Data Discovery

SciKG is a long-term research platform for improving the **discoverability,
accessibility, interoperability, and reusability** of scientific research
assets through structured metadata, knowledge graph technologies, and
AI-assisted exploration.

> **Status:** Active build — 8-week project, June 1 – July 31.
> 2-person team. CI Compass Fellowship. Extraction covers the ICR
> publication corpus (CrossRef + MagLab CSV), the 46 Thermo RAW
> files, and the 952 Blood Proteoform Atlas PXD files; PDF gap-field
> extraction (stage 02d) exists and is under evaluation. Normalization,
> validation, and load (stages 03-05) are DONE — the graph is loaded into
> Neo4j AuraDB (4,886 nodes, 11,690 edges; instrument dedup, dataset-accession mint, ORCID enrichment, and a researcher-identifier slug fix — transliterate accents, drop the year — 2,076→2,062, all applied 2026-07-24). The researcher-equivalence layer is production-loaded: 27 `SAME_AS` edges, 24 of them added 2026-07-25 from human review. Current focus: graph
> validation/analysis against the researcher discovery questions and the poster.

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
a researcher can ask _"what experiments used instrument X on sample type Y, and
which publications and grants are connected to them?"_ and get a grounded,
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

| Principle         | How SciKG approaches it                                                            |
| ----------------- | ---------------------------------------------------------------------------------- |
| **Findable**      | Rich metadata, persistent identifiers, searchable relationships                    |
| **Accessible**    | Standardized retrieval mechanisms, clear access pathways                           |
| **Interoperable** | Structured schemas, standard vocabularies, machine-readable metadata               |
| **Reusable**      | Provenance tracking, context preservation, documentation & reproducibility support |

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
│   │   ├── rawfiles_pxd/            # Blood Proteoform Atlas FOXDEN (952 files, LOCAL-ONLY, gitignored)
│   │   ├── doi_list.csv
│   │   └── manifest.json            # Pipeline state tracker
│   └── processed/                   # Pipeline output at each stage
│       ├── rawfiles_enriched/       # FOXDEN + filename metadata merged (46 files)
│       ├── entities/                # Extracted records (JSONL)
│       ├── relationships/           # Extracted relationships (JSONL)
│       ├── normalized/              # Normalized entities + relationships (03 output)
│       ├── logs/                    # Extraction/normalization logs (JSONL)
│       └── validated/               # 04 output: entities/, relationships/, report, quarantine (populated: 4,886 nodes, 11,690 edges; load_cleared)
├── scripts/                         # Pipeline scripts — run in order
│   ├── 01_fetch.py
│   ├── 01b_fetch_pdfs.py
│   ├── 02_extract.py
│   ├── 02b_extract_csv.py
│   ├── merge_rawfile_metadata.py
│   ├── 02c_extract_rawfiles.py
│   ├── 02f_extract_pxd_rawfiles.py  # Blood Proteoform Atlas PXD (local-only)
│   ├── 02d_extract_pdf.py           # PDF gap-field extraction (under evaluation)
│   ├── transform_pdf_software.py    # PDF Software transform (Software nodes + USES_SOFTWARE)
│   ├── 03_normalize.py
│   ├── 04_validate.py              # (built)
│   ├── 05_load.py                  # (run — graph loaded into Neo4j AuraDB)
│   ├── mint_dataset_operator_edges.py  # human-gated post-load: PDF dataset_accession -> HAS_DATASET
│   ├── fetch_crossref_orcid.py     # ORCID enrichment 1/4: cache CrossRef author/ORCID JSON
│   ├── analyze_orcid_coverage.py   # ORCID enrichment 2/4: read-only coverage + bounded match
│   ├── emit_orcid_properties.py    # ORCID enrichment 3/4: apply ruling -> proposed + exclusions
│   ├── enrich_researchers_orcid.py # ORCID enrichment 4/4: write orcid props into researchers.jsonl
│   ├── db.py
│   └── ...                         # plus helper/verification utilities (build_vocabulary, verify_pdf_corpus, audit_repo, etc.)
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
│   ├── KNOWN_ISSUES.md
│   ├── controlled_vocabulary.md
│   ├── DISCOVERY_QUESTIONS.md
│   ├── PDF_EXTRACTION_EVAL.md
│   ├── annotations/                 # Manual paper-review notes (paper_reviews.md)
│   └── metadata_templates/
├── README.md
├── CLAUDE.md
├── requirements.txt
└── .gitignore
```

## Documentation Index

| Document                                                                         | Purpose                                                                                          |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| [docs/SCIKG_SCHEMA.md](docs/SCIKG_SCHEMA.md)                                     | Authoritative v1.0 schema — node types, relationships, identifiers, provenance rules             |
| [docs/ROADMAP.md](docs/ROADMAP.md)                                               | Proposed, evolving research workflow (not an approved plan)                                      |
| [docs/FAIR_PRINCIPLES.md](docs/FAIR_PRINCIPLES.md)                               | FAIR notes and how each principle maps to design decisions                                       |
| [docs/METADATA_INVENTORY.md](docs/METADATA_INVENTORY.md)                         | Metadata cataloguing approach + template usage                                                   |
| [docs/DISCOVERY_QUESTIONS.md](docs/DISCOVERY_QUESTIONS.md)                       | The 14 real researcher-submitted questions the graph is evaluated against                        |
| [docs/VERIFIED_FACTS_AND_ASSUMPTIONS.md](docs/VERIFIED_FACTS_AND_ASSUMPTIONS.md) | Verified facts vs. proposed ideas vs. unknowns                                                   |
| [docs/REVIEW_LOG.md](docs/REVIEW_LOG.md)                                         | Log of review-worthy changes and assumptions                                                     |
| [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md)                                     | Known issues register — data-quality limitations, caught errors, and their rulings (KI-1..KI-18) |
| [docs/controlled_vocabulary.md](docs/controlled_vocabulary.md)                   | Controlled vocabulary — instrument/method terms mapped to PSI-MS accessions                      |
| [docs/PDF_EXTRACTION_EVAL.md](docs/PDF_EXTRACTION_EVAL.md)                       | PDF gap-field extraction (stage 02d) evaluation results                                          |
| [docs/annotations/](docs/annotations/)                                           | Manual paper-review notes (paper_reviews.md)                                                     |
| [docs/metadata_templates/](docs/metadata_templates/)                             | Fillable inventory templates (CSV/YAML), no fabricated rows                                      |

---

## Current Focus

Extraction now covers the ICR publication corpus (CrossRef API and
MagLab CSV), the 46 Thermo RAW files, and the 952 Blood Proteoform
Atlas PXD files. The graph holds 934 distinct RawDataFile nodes (46
Thermo RAW + the PXD set): 64 files cross-deposited under overlapping
accessions were correctly merged (KI-1), and under KI-8's composite
identity (rawfile:{filename}:{sha16}, remediated 2026-07-20) byte-identical
files deposited under different names load as distinct nodes — 21 such
pairs, each recorded by an Advisory node. A maglab_acquired_confirmed
flag marks the 199 confirmed MagLab-acquired (LTQ FT Ultra), with the
rest unconfirmed (attribution not recoverable from metadata). PDF
gap-field extraction (stage 02d) exists and is under evaluation.
Normalization, validation, and load (stages 03-05) are complete; the
graph is loaded into Neo4j AuraDB (4,886 nodes, 11,690 edges).

A human-gated post-load reconciliation (`mint_dataset_operator_edges.py`,
applied 2026-07-22) mints the PDF-extracted `dataset_accession` values that
02d extracts but never links into `HAS_DATASET` edges. It is deliberately
separate from 02d and gated behind human review because these accessions
carry fuzzy/hallucinated values (wrong-repo, mis-OCR'd, or invented) that
must be confirmed before entering the graph — keeping 02d fabrication-free.
Approved records are `--emit`-ted to pre-normalize JSONL and flow through
03->04->05 like any other extracted record, so `graph = f(files)` still
holds (verified by a files-only rebuild into an empty Neo4j instance). The
first application added 8 Dataset + 11 HAS_DATASET (289->297, 279->290).
Held for rulings, not minted: MSV native accessions, new-namespace deposits
(SRA/BioProject/BCO-DMO), PXD026178, the `other:0516284a` PRIDE search-URL
node, and raw-file operators (intentionally unmodeled — FOXDEN metadata
carries no reliable person identity).

Instrument identity is derived from the FOXDEN 'model' field, so the
same physical instrument deduplicates across sources. Controlled-
vocabulary instrument terms were audited against PSI-MS (via EBI OLS4)
and corrected. A table-driven instrument dedup in 03 (applied 2026-07-21,
469 -> 443) additionally merged OCR/spacing typo variants, collapsed the
bare-generic FT-ICR spellings into one FT-ICR MS node (MS:1003948), and
split the conflated Velos node into distinct hybrid (LTQ Orbitrap Velos)
and ion-trap (Velos Pro, LTQ Velos) instruments. The Dataset repository namespace is ProteomeXchange,
aligned across the CSV (02b) and PXD (02f) extractors.

Author identity was enriched with ORCIDs from CrossRef structured metadata
(author[].ORCID — a deterministic per-DOI lookup, not extraction). 481 of 2,062
Researcher nodes (23.3%) now carry an orcid: 471 from CrossRef (192 author-verified /
279 publisher-asserted) plus 10 found during the 2026-07-25 researcher-equivalence
review. The 10 have `orcid_authenticated` NULL — there is no CrossRef attestation
behind them, and `false` would falsely read as publisher-asserted. Stored as two
properties (orcid + orcid_authenticated), never
flattened. RULED properties-only: ORCID-as-identifier is DEFERRED and
ENABLE_ORCID_CANONICALIZATION stays False (turning it on would mint a duplicate
Researcher node set — see CLAUDE.md and KI-16). Note: docs/DISCOVERY_QUESTIONS.md
cites 4,909 / 11,668 (2026-07-20); its node count is still 23 higher than the current
graph and unreconciled, while its edge count now reads 22 lower only because the
2026-07-25 SAME_AS emit overtook it.

Researcher identifiers were re-minted this session to
`researcher:{translit_family}_{initial}` — NFKD-transliterated accents, separators
normalized, and the YEAR DROPPED (it was order-dependent, and all 14 same-key
collisions were fragmentations of one person, never two people; ORCID-verified 0
false collapses). On collapse the most diacritic-rich `name_full` wins, with fused
"A and B" forms filtered first — slugs are ASCII,
names keep their diacritics. This dissolved 14 accent-variant duplicates (2,076 →
2,062). Two non-destructive equivalence edge types were added: `SAME_AS` (PROVEN) and
`POSSIBLY_SAME_AS` (INFERRED, human-confirm), both undirected and additive (nothing
merged, both names kept). **27 `SAME_AS` edges are now live in production** (up from
3), with 0 `POSSIBLY_SAME_AS`. They split by `anchor_type` into two proof classes that
must not be conflated: **3 ORCID-anchored** (a shared author-verified ORCID spans both
nodes — aguilera↔chacón-patiño surname change, hoeschen↔hoschen,
salvato_vallverdu↔vallverdu) and **24 human-reviewed** (`anchor_type='human_review'`,
added 2026-07-25), whose proof is a reviewer's judgment on mechanical-artifact pairs
— OCR variants (14), period-parse residue (2), spelling variants (2),
transliteration (2), and one each of an accent/umlaut variant, a Jr. suffix, a
character transposition, and a corrected exclusion. `properties.orcid` is null on all
24, so a consumer needing ORCID-grade proof filters on `anchor_type`, not on the
`SAME_AS` type alone. The candidate set is now resolved: 24 emitted, 1 held
(angstrom↔anstrom, unresolved), 11 confirmed different. See CLAUDE.md and KI-17.

The graph rebuilds from committed files (03 -> 04 -> 05 into an empty instance) —
VERIFIED 2026-07-24: a clean rebuild from the release commit reproduced 4,886/11,663
exactly; RE-VERIFIED 2026-07-25 after the human-review SAME_AS emit — a files-only
03→04→05 into an empty Docker Neo4j reproduced 4,886/11,690 with `SAME_AS` 27, and the
production load that followed created 0 nodes / 24 edges, matching.
It is reproducible-from-committed-files, NOT re-derivable-from-source:
three curated files are hand-maintained migrations a clean 02x extractor run does
NOT reproduce — `pdf_entities.jsonl` (Institution/Instrument/Software), `pdf_dataset_*.jsonl`
(the dataset mint, its ledger removed from the repo), and `software.jsonl` (the
Xcalibur collapse: 7 versioned nodes → 1, versions moved to the ACQUIRED_WITH edge).
A fresh clone runs 03 -> 04 -> 05 and gets the exact graph; re-running the extractors
overwrites those three (KI-13). Also rawfiles_pxd/ and pdf_extraction/ are local-only.

Building a provenance-aware knowledge graph from 806 ICR journal
articles (from the MagLab CSV) plus five other sources: the CrossRef
API, the Web Applications Group publications export, 46 Thermo RAW
files, manual annotations, and the 952 Blood Proteoform Atlas PXD
files (local-only — gitignored, not reproducible from a clean clone).
Graph loaded into Neo4j AuraDB (cloud).
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

# 3. Provision a Neo4j AuraDB instance and set NEO4J_URI (neo4j+s://...),
#    NEO4J_USER, NEO4J_PASSWORD in .env at the repo root (read by scripts/db.py)

# 4. Run the pipeline scripts in order
python scripts/01_fetch.py
python scripts/02_extract.py
python scripts/02b_extract_csv.py
python scripts/02c_extract_rawfiles.py
python scripts/02f_extract_pxd_rawfiles.py  # Blood Proteoform Atlas PXD files (local-only source; see CLAUDE.md)
python scripts/02d_extract_pdf.py     # PDF gap-field extraction (under evaluation)
python scripts/transform_pdf_software.py  # PDF Software transform (see CLAUDE.md pipeline block + KI-13)
python scripts/03_normalize.py
python scripts/04_validate.py           # (built)
python scripts/05_load.py               # (run — loads validated records into Neo4j AuraDB)
```

Read the foundation docs first: README.md → docs/ROADMAP.md →
docs/FAIR_PRINCIPLES.md. Propose changes via PR; keep raw data immutable.

---

## License & Citation

### License
This repository is currently unlicensed for external reuse; source code and
data pipelines remain internal research material pending a formal license
decision (e.g., MIT).

### Citation
If you use SciKG or reference this work, please cite:

> Adhikari, D., & Saiadian, V. (2026). *SciKG-FT-ICR: A Provenance-Aware
> Knowledge Graph of the MagLab's FT-ICR Research* [Poster]. National High
> Magnetic Field Laboratory, CI Compass Summer Program of the CI Compass Fellowship.

### Third-party data & vocabularies
This graph incorporates data from CrossRef (publication metadata), ORCID
(researcher identifiers), ProteomeXchange/PRIDE (dataset accessions), and
PSI-MS via EBI OLS4 (instrument controlled vocabulary). Each source's own
terms of use govern redistribution of that source's data independent of this
repository's license.
