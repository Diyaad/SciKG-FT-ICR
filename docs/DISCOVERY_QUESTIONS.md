# SciKG Discovery Questions
# Real researcher-submitted evaluation set — David Butcher and FT-ICR facility researchers.
# These are the actual evaluation questions (exact wording preserved), NOT placeholders.
# Every answerability tag below was VERIFIED by running Cypher against the loaded
# Neo4j graph (v1.0: 4,909 nodes, 11,668 edges) on 2026-07-20 — measured, not assumed.

## Legend

- ✅ **ANSWERABLE** — a query was written, run, and returned real results (query + evidence shown).
- ◐ **PARTIAL** — answerable for a subset only; the covered fraction and the specific gap are stated.
- ○ **FUTURE WORK** — the data is not in the graph. The exact missing field / 0-record node type /
  un-ingested source is named, along with what ingesting it would take. No misleading empty query
  is dressed up as an answer.

> Note on tags: **no single question as worded is a clean ✅**, because each bundles a
> fully-supported capability (e.g. co-authorship, instrument usage) with one the graph does not yet
> support (e.g. topic tags, citation counts, per-experiment parameters tied to publications). The
> underlying *capabilities* do split cleanly into ✅ / ◐ / ○ — see the summary table at the end.

---

## The questions

### 1. What study areas is FT-ICR MS primarily used in?  ○ FUTURE WORK
`MATCH (p:Publication) RETURN p.resource_type, count(*)` → **`JournalArticle`: 805** (single value).
Publication carries no subject / discipline / keyword property. `resource_type` is uniform across all
805 papers, so it cannot distinguish study areas.
**Missing:** subject/study-area tagging (e.g. MeSH, CrossRef `subject`, or full-text topic
classification). Journal titles exist and could serve as a weak future proxy.

### 2. Where are opportunities for developing new techniques in FT-ICR MS?  ○ FUTURE WORK
Interpretive/analytical synthesis, not a retrieval query. Depends on the subject/trend data absent
in Q1 plus expert reasoning over gaps.
**Missing:** subject tagging + temporal trend data; the answer is generated, not stored.

### 3. Of MagLab-resource publications: (a) global distribution of authors, (b) global distribution of field samples.  ○ FUTURE WORK
`MATCH (n:Institution) … WHERE key CONTAINS 'countr'/'geo'/'city'/'lat'` → **0 fields**.
Same check on Researcher (`countr`/`geo`/`affil`) → **0 fields**. Sample nodes (3) carry growth
medium/strain/state but **no geographic origin**.
**Missing:** affiliation→country resolution for authors, and sampling-location fields for samples.
Would require parsing affiliation strings / ROR→country lookup and a sample-geography source.

### 4. What are the most commonly used methodologies?  ◐ PARTIAL
Instrument and software *usage* are fully queryable, and fractionation methods exist for the MagLab
RAW subset:
```cypher
MATCH (r:RawDataFile) WHERE r.fractionation_method <> ''
RETURN r.fractionation_method, count(*) ORDER BY count(*) DESC
```
→ **GELFrEE 24, PEPPI 18, below30kDa 4** (46 MagLab RAW files).
`MATCH (s:Software) RETURN s.category, count(*)` → **category is null for 50 of 51 Software nodes**
(only 1 tagged `acquisition`).
**Covers:** ranked instrument usage (see Q5), software usage counts, and fractionation methods on 46
files. **Missing:** a publication-level methodology taxonomy — there is no "method" classification on
the 805 papers (and no `Method` node type in the schema). "Methodology" is proxied, not modeled.

### 5. Similarities/differences between publications using MagLab instruments vs. instruments at PNNL?  ○ FUTURE WORK
The MagLab side is rich:
```cypher
MATCH (:Publication)-[:USES_INSTRUMENT]->(i:Instrument)
RETURN coalesce(i.canonical_name,i.model_raw) AS instrument, count(*) AS pubs ORDER BY pubs DESC
```
→ **21T FT-ICR MS: 168 pubs, 9.4T FT-ICR MS: 60, custom-built FT-ICR: 21, …** (465 instruments).
But there is nothing to compare against: a "Pacific Northwest National Laboratory" Institution node
exists yet has **0 INVOLVES_INSTITUTION edges** (orphan), and instruments carry **no
facility/location field** (`key CONTAINS 'facil'/'locat'/'site'` → 0). This is a single-corpus graph.
**Missing:** a PNNL comparison corpus (their publications/instrument usage) and instrument-location
modeling. Neither is derivable from what is loaded.

### 6. Of direct-infusion FT-ICR MS on dissolved organic matter: (a) fields of study, (b) sample types with most vs. fewest peaks, (c) elements assigned.  ○ FUTURE WORK
DOM papers can be *loosely* identified by title only:
`MATCH (p:Publication) WHERE toLower(p.title) CONTAINS 'dissolved organic' RETURN count(*)` → **106**.
But this cannot isolate *direct-infusion* specifically, and all three sub-asks fail: a search for any
`peak` / `element` / `formula` property across every node returned **0 fields**.
**Missing:** (a) field-of-study tags, (b) per-spectrum peak counts, (c) elemental/formula
assignments. None are in the graph; they live in spectra/supplementary data not yet ingested.

### 7. Most common instrumental parameters in studies involving E. coli samples?  ◐ PARTIAL
E. coli is present and identifiable:
```cypher
MATCH (r:RawDataFile) WHERE r.sample_organism_strain='MG1655'
RETURN count(*) AS total,
       sum(CASE WHEN r.scan_count IS NULL THEN 0 ELSE 1 END) AS scan,
       sum(CASE WHEN r.activation_types_raw IS NULL THEN 0 ELSE 1 END) AS activation,
       sum(CASE WHEN r.acquisition_software_name IS NULL THEN 0 ELSE 1 END) AS acq_sw
```
→ **total 28, scan 0, activation 0, acq_sw 28.** All 28 are MagLab files (`source_type=merged_csv_foxden`).
Available for them: organism **MG1655**, state **lysate**, medium **M9** (3 Sample nodes), and
acquisition software **Xcalibur 2.7.0 SP2** (28 files).
**Covers:** E. coli sample prep + acquisition software. **Missing:** the actual *instrumental*
parameters (scan settings, activation, run time) are **NULL for all 28 E. coli files** — those fields
are populated only on the human-blood PXD files (Q8). MagLab's own RAW headers weren't extracted to
that depth.

### 8. Most common ion-activation / fragmentation parameters?  ◐ PARTIAL
Returns a clean ranked answer:
```cypher
MATCH (r:RawDataFile) WHERE r.activation_types_raw IS NOT NULL
UNWIND r.activation_types_raw AS act RETURN act, count(*) ORDER BY count(*) DESC
```
→ **CID 162, HCD 44, PQD 37.** Populated on **243 / 934 RawDataFiles (26%)**.
**Covers:** the 243-file subset. **Missing/caveat:** all 243 come from a single external deposit
(`source_type=fisher_py` = the 952-file Blood Proteoform Atlas, human blood); **0** of MagLab's own 46
FT-ICR files carry activation data, and none of it is linked to a Publication. So it answers "what
activation types are in the raw data we ingested," but that data is one non-MagLab deposit.

### 9. What data-acquisition strategies (e.g. DDA) appear in the raw data?  ○ FUTURE WORK
`MATCH (r:RawDataFile) WHERE … CONTAINS 'dda'/'dia'/'dependent'` across filename,
`experimental_parameters`, and method fields → **0 files**. The only `experimental_parameters` values
present (29/934) are freeform tags: **`screen` 24, `normMS1_typicalparams` 4, `shortgradient` 1** —
not an acquisition-strategy field.
**Missing:** a structured acquisition-mode field (DDA/DIA/targeted). Not captured during extraction.

### 10. Predict optimal parameters for a top-down proteomics study of an E. coli whole-cell lysate.  ○ FUTURE WORK
Predictive/generative task, not a retrieval query — and it depends on exactly the parameter data shown
absent in Q7–Q9 (scan/activation/run-time are NULL for the E. coli files).
**Missing:** a populated instrumental-parameter set for MagLab RAW files, plus a modeling step run
outside the graph.

### 11. Most impactful ICR publications by citation count?  ○ FUTURE WORK
`MATCH (p:Publication) … WHERE key CONTAINS 'cit'/'impact'` → **0 fields**. Citation counts are not a
Publication property.
**Missing:** citation data — ingest CrossRef `is-referenced-by-count` (or a citation index) onto the
805 papers; a single-field addition per publication.

### 12. What funders beyond the NSF Cooperative Agreement are associated with MagLab ICR publications?  ○ FUTURE WORK
`MATCH (f:Funder) RETURN f.name` → **only "National Science Foundation" (1 node)**; all **382**
FUNDED_BY edges point to it. `acknowledged_nsf_grant` is True for 382 / False for 19 publications.
The graph therefore models **no funder other than NSF** — it cannot answer "beyond NSF" affirmatively.
**Missing:** the full CrossRef `funder` array (per-DOI). The fetch currently captures only the NSF
acknowledgment; ingesting CrossRef funders would populate the non-NSF funders this question asks for.

### 13. Which raw files correspond to specific publications, and what parameters (polarity, scan, activation) were used?  ○ FUTURE WORK
**Linkage does not exist.** Datasets partition cleanly with zero overlap:
```cypher
MATCH (ds:Dataset)
WITH ds, EXISTS { (ds)<-[:DERIVED_FROM]-(:RawDataFile) } AS hasraw,
         EXISTS { (ds)<-[:HAS_DATASET]-(:Publication) }  AS haspub
RETURN hasraw, haspub, count(*) ORDER BY count(*) DESC
```
→ **(raw only) 32, (pub only) 257, (both) 0.** RawDataFiles reach 32 ProteomeXchange datasets;
Publications reach 257 OSF/Other/Zenodo datasets; **no dataset is shared**, so there is no
raw-file→publication path. (Consistent with project rules: `ANALYZED_IN` (RAW→Publication) is UNDER
REVIEW and deliberately not loaded.) Also, **no `polarity` field exists** on RawDataFile.
**Available but orphaned from publications:** `scan_count` 888/934, `activation_types_raw` 243/934,
`ms_run_time_min` 243/934. **Missing:** the RAW→Publication relationship (pending `ANALYZED_IN`
confirmation) and a polarity field.

### 14. Which collaborators/institutions most frequently co-publish with MagLab ICR users, and are there networks around particular topics?  ◐ PARTIAL
The **collaborator (researcher) network is fully answerable** — ✅-grade evidence:
```cypher
MATCH (a:Researcher)<-[:AUTHORED_BY]-(p:Publication)-[:AUTHORED_BY]->(b:Researcher)
WHERE a.identifier < b.identifier
RETURN a.name_full, b.name_full, count(DISTINCT p) AS shared ORDER BY shared DESC
```
→ **Marshall, A.G. – Rodgers, R.P.: 55; McKenna, A.M. – Spencer, R.G.M.: 36; Chacon Patino – Rodgers:
35; …** (15,379 co-author pairs; **624 researchers have >1 publication**).
**Institution co-publication is thin:**
`MATCH (p:Publication)-[:INVOLVES_INSTITUTION]->(i:Institution) RETURN i.name, count(DISTINCT p)` →
**Florida State University 9, NOSAMS 4, Northwestern 3, …**, but only **74 / 805 publications (9%)**
carry any institution edge.
**Missing:** the "around particular topics" clause — there is no topic/subject tagging to cluster the
network by. So: researcher network ✅, institution frequency ◐ (9% coverage), topic-labelled networks ○.

---

## Summary: capability the questions need → v1.0 status

| Capability | Status | Evidence / gap |
|---|---|---|
| Co-authorship / collaborator networks (researchers) | ✅ | 624 researchers >1 pub; top pair 55 shared; 15,379 pairs |
| Instrument usage & per-instrument counts | ✅ | 21T: 168 pubs, 9.4T: 60, … across 465 instruments |
| Software usage counts | ✅ | USES_SOFTWARE 267 edges (but `category` null for 50/51) |
| Provenance: pub ↔ journal ↔ NSF funding ↔ facility ↔ authors | ✅ | PUBLISHED_IN 805, FUNDED_BY 382, CONDUCTED_AT 818, AUTHORED_BY 5,026 |
| Fractionation methods (MagLab RAW subset) | ◐ | GELFrEE/PEPPI/below30kDa on 46 files only |
| Ion-activation / fragmentation types | ◐ | CID/HCD/PQD on 243/934 files, all one external deposit |
| E. coli sample metadata + acquisition software | ◐ | 28 MG1655 files; scan/activation NULL for them |
| Institution co-publication frequency | ◐ | 62 institutions but only 74/805 pubs (9%) linked |
| Raw-file ↔ publication linkage | ○ | 0 shared datasets; `ANALYZED_IN` not loaded |
| Per-experiment parameters tied to publications (polarity/scan/activation) | ○ | no polarity field; params orphaned from pubs |
| Data-acquisition strategy (DDA/DIA) | ○ | 0 files; no acquisition-mode field |
| Citation counts / impact ranking | ○ | no citation property on Publication |
| Study-area / subject tagging | ○ | `resource_type` = JournalArticle for all 805 |
| Geographic distribution (authors, samples) | ○ | no country/affiliation-geo or sample-location fields |
| Non-NSF funders | ○ | 1 Funder node (NSF); CrossRef funder array not ingested |
| Comparison corpus (PNNL) | ○ | PNNL is an orphan node; single-corpus graph |

## Honest assessment

The graph answers the **structural and provenance** questions completely: who authored and
co-authored what, which instruments and software each publication used and how often, which papers
NSF funded, and where they were published and conducted. Those capabilities are ✅ and return real,
ranked results today — the co-authorship network alone spans 2,076 researchers and 15,379 collaborator
pairs.

The gaps are not scattered; they **cluster into a clear next phase**, and every one of them was named
by a facility researcher's question:

1. **Parameter extraction** (Q7–Q9, Q13) — pull scan/activation/polarity from the RAW headers for
   MagLab's own files and tie them to publications once `ANALYZED_IN` is confirmed.
2. **Citation ingestion** (Q11) — add CrossRef `is-referenced-by-count` per DOI.
3. **Subject / geographic enrichment** (Q1–Q3, Q6) — study-area tags and affiliation→country
   resolution.
4. **Funder enrichment** (Q12) — ingest the full CrossRef `funder` array beyond the NSF acknowledgment.
5. **Comparison corpus** (Q5) — a PNNL (or other-facility) dataset to make cross-lab comparison possible.

That the questions land just past the current graph is a **roadmap, not a shortfall**: v1.0 answers the
provenance layer the project set out to build, and the researcher questions define exactly what the
next ingestion phase should add.

## Note on method

Every ✅ and ◐ above is backed by a query that was run against the live graph and returned the stated
result; every ○ is backed by a query that confirmed the field/relationship is absent (0 rows / 0
fields) rather than assumed. Verified 2026-07-20 against v1.0 (4,909 nodes, 11,668 edges).
