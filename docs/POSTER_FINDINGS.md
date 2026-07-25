# SciKG — Poster Findings (running record of VERIFIED results)

**Purpose.** A running record of findings cleared for the poster. Every number here is
traceable to the live graph, `data/processed/review/orcid_coverage_report.md`,
`docs/KNOWN_ISSUES.md`, or a committed artifact.

**Hard rule.** No invention, no embellishment. A number that cannot be traced is listed in
[TO-VERIFY](#to-verify) rather than stated as fact. Where a figure supplied for this record did
not survive verification, the verified figure is used and the discrepancy is noted inline as
`CORRECTED`.

**Tags.** `CAPABILITY` = what the method achieved · `BOUNDARY` = what it structurally cannot
reach · `ARTIFACT` = a defect found and characterized.

**Verification basis.** Graph counts below were re-queried against the live Neo4j AuraDB
instance (read-only `MATCH`/`RETURN` only). Both dated columns are kept: the 2026-07-23 column is
the basis the findings below were originally written against, and the 2026-07-25 column is the
current state. Where a finding's number moved, the entry says so inline.

| Measure | Live (2026-07-23) | Live (2026-07-25) | what moved |
|---|---:|---:|---|
| Nodes | 4,900 | **4,886** | researcher-identifier slug fix, 14 accent-collapse merges (2026-07-24) |
| Edges | 11,663 | **11,690** | +27 `SAME_AS` (3 ORCID-anchored, then +24 human-reviewed on 2026-07-25) |
| Publication | 805 | 805 | — |
| Researcher | 2,076 | **2,062** | the same 14 merges |
| Researcher with `orcid` | 475 | **481** | +10 found during the equivalence review, then −4 from the merges |
| `SAME_AS` | 0 | **27** | the equivalence layer (CAPABILITY 6c) |
| `POSSIBLY_SAME_AS` | 0 | 0 | type defined, never populated |
| Instrument | 443 | 443 | — |
| Dataset | 306 | 306 | — |
| RawDataFile | 934 | 934 | — |
| Advisory | 21 | 21 | — |

> **Note on totals.** Current live state is **4,886 / 11,690** (2026-07-25), and `CLAUDE.md`,
> `README.md`, and KI-17 all now record it. Two corrections are on record from that pass: `CLAUDE.md`
> had said the 3 ORCID-anchored `SAME_AS` edges were "not yet loaded to production" when they had in
> fact already been applied (production was never at 11,663 once they landed), and it had recorded 7
> reverse-error ORCID nodes where `orcid_exclusions.jsonl` measures 6.
> `docs/DISCOVERY_QUESTIONS.md` still cites a third pair (4,909 / 11,668, dated 2026-07-20). Its
> **node** count remains **23 higher** than the live graph and unreconciled — that is the real
> discrepancy. Its **edge** count now reads 22 *lower*, but only because the 2026-07-25 `SAME_AS`
> emit overtook it; the edge gap has flipped sign and is no longer a useful signal. See
> [TO-VERIFY](#to-verify) T2.

---

## CAPABILITY

### 1. End-to-end provenance chain, reproducible from files

- **Tag:** CAPABILITY
- **What was found:** A publication now resolves through its deposit to the raw files and the
  instrument that acquired them — a chain that did not exist before this work. The Blood
  Proteoform Atlas paper `doi:10.1126/science.aaz5284` cited `PXD026123`, which was already
  loaded as `dataset:proteomexchange:pxd026123`, **with no edge between them**. The human-gated
  mint created that edge, and it was emitted through pre-normalize JSONL so the graph remains a
  function of committed files.
- **The numbers:** The verified chain is
  `doi:10.1126/science.aaz5284` → `HAS_DATASET` → `dataset:proteomexchange:pxd026123` →
  `DERIVED_FROM` ← **35** `RawDataFile` → `COLLECTED_ON` → **1** `Instrument`
  (`instrument:raw:orbitrap_fusion_lumos`). Reproducibility was proven by a files-only rebuild
  into an empty Neo4j instance reproducing the counts.
- **`CORRECTED`:** the figure supplied for this entry was "952 raw files". That is **not** this
  chain. 952 is the count of local FOXDEN source JSON files in `data/raw/rawfiles_pxd/`
  (gitignored, local-only). The graph holds **934** `RawDataFile` nodes total (888
  `source_type: fisher_py` + 46 `merged_csv_foxden`), and only **35** of them lie on this
  publication's chain. Do not put 952 on the poster next to this chain.
- **Why it matters:** This is the artifact's central claim — provenance that is *traversable*,
  not merely stored, and reproducible from committed source rather than from a hand-edited
  database.
- **Source:** live graph 2026-07-23; `docs/KNOWN_ISSUES.md` KI-15; commit `f3a5490`.

### 2. Byte-identical duplicate detection (fully deterministic)

- **Tag:** CAPABILITY
- **What was found:** Raw files deposited under different names but byte-for-byte identical are
  detected by hash and recorded rather than silently collapsed. Both copies are retained and each
  collision is recorded by an `Advisory` node, so the duplication is preserved as a fact about
  the deposits.
- **The numbers:** **21** `Advisory` nodes, **42** `FLAGS` edges (verified live) — 21 collision
  sets, each flagging 2 files.
- **Why it matters:** This finding carries **no LLM uncertainty at all**. It is computed from
  SHA-256 hashes of the files themselves, with no extraction step. On a poster that otherwise
  reports extraction-derived results, this is the one class of finding that is deterministic
  end-to-end.
- **Source:** live graph 2026-07-23; `docs/KNOWN_ISSUES.md` KI-8; `docs/SCIKG_SCHEMA.md`
  (Node: Advisory).

### 3. Dataset reconciliation with a human review gate

- **Tag:** CAPABILITY
- **What was found:** PDF-extracted dataset accessions were extracted to disk but never became
  edges (the C4 gap). They were reconciled in three gated batches, each dry-run → dispositioned →
  reviewed → applied, with the approved records written to pre-normalize JSONL so they flowed
  through `03 → 04 → 05` like any other extracted record.
- **The numbers:** **20** `HAS_DATASET` edges added across three batches (**11** original = 3
  link + 8 mint, **3** MassIVE, **6** SRA/BioProject/BCO-DMO). Graph movement: Dataset
  **289 → 306**, HAS_DATASET **279 → 299**. Both endpoints confirmed live on 2026-07-23
  (Dataset **306**, HAS_DATASET **299**). **0** quarantined at validation across all three
  batches.
- **Why it matters:** The gate is the point. Accessions carry fuzzy, mis-OCR'd, and outright
  invented values, so extraction stays fabrication-free and the human confirmation lives in a
  separate, auditable step — while the result still enters through the normal pipeline.
- **Source:** live graph 2026-07-23; `docs/KNOWN_ISSUES.md` KI-15;
  `scripts/mint_dataset_operator_edges.py`.

### 4. Duplicate deposit caught before it was created

- **Tag:** CAPABILITY
- **What was found:** `doi:10.1021/acs.jproteome.0c00403` cites MassIVE accession
  `MSV000085978`. The graph already held that same submission under its DOI form,
  `dataset:other:10.25345/c54n1p` — MassIVE issues both identifiers for one deposit. The
  accession was **held, not minted**, preventing a duplicate node for a deposit already present.
- **The numbers:** **1** accession held. **0** nodes in the graph contain `MSV000085978`
  (verified live). `dataset:other:10.25345/c54n1p` is present and is the dataset linked to that
  paper (verified live). The other **3** MSV accessions were confirmed twin-free by lookup before
  minting, each carrying its paired `10.25345/` DOI in `evidence_note` for a future crosswalk.
- **Why it matters:** A negative result that is invisible in the final graph. The absence of a
  duplicate is the deliverable, and it is only demonstrable because the review step was recorded.
- **Source:** live graph 2026-07-23; `docs/KNOWN_ISSUES.md` KI-15.

### 5. Fusion caught by an independent structured source (proof by contradiction)

- **Tag:** CAPABILITY
- **What was found:** `researcher:martin_b_2017` has `name_full` = `"Martin, B.R. and
  Hakansson, K."` — a MagLab CSV convention that collapsed two authors into a single node.
  CrossRef returned **two distinct ORCIDs for this one node from the same paper**
  (`doi:10.1021/acs.analchem.7b01461`). A paper cannot list one person twice, so this is
  **proof, not inference**, that the node holds two people.
- **The numbers:** **2** ORCIDs (`0000-0002-7136-2397` = Brent R. Martin,
  `0000-0003-1926-0542` = Kristina Håkansson) on **1** node from **1** DOI. This is the only
  same-paper collision among **1,129** MATCH-UNIQUE rows — which also confirms the matcher is
  not over-matching. **108** fused nodes exist in the graph (verified live).
  Independently corroborated: the same person (Håkansson) is *also* hit by accent-collapse —
  ORCID `0000-0003-1926-0542` maps to both `researcher:martin_b_2017` and
  `researcher:h_kansson_k_2024`. One real person, two distinct defects.
- **Why it matters:** Internal consistency checking **could not** have found this — the node is
  self-consistent. It took an independent structured source to contradict it. That is the
  methodological point worth making: provenance-aware integration surfaces errors that
  single-source validation cannot.
- **Source:** live graph 2026-07-23; `data/processed/review/orcid_coverage_report.md` §3.2, §3.3.

### 6. Extraction errors caught by provenance

- **Tag:** CAPABILITY
- **What was found:** A fabricated software extraction is confirmed **absent from the graph**.
  02d grounded `MaxQuant` onto `doi:10.1021/jasms.4c00232` via fuzzy alignment; a human PDF read
  found the paper never mentions MaxQuant. The false edge was removed and the node left
  deliberately edgeless rather than deleted (it is a real tool with a real corpus use whose
  edge was blocked upstream).
- **The numbers:** `doi:10.1021/jasms.4c00232` carries **0** `USES_SOFTWARE` edges (verified
  live). `software:maxquant` exists with **0** edges of any type (verified live) — the
  orphan never re-linked.
- **Why it matters:** Demonstrates the fabrication was contained: it is recorded as a known
  problem rather than silently living in the graph as a scientific claim. The node's
  `evidence_note` was rewritten to state what actually happened, converting a false claim into a
  true record.
- **Source:** live graph 2026-07-23; `docs/KNOWN_ISSUES.md` KI-10 (node-level fallout table,
  X2 ruling 2026-07-17).
- **Not included here:** the "most facet-rich paper reported 10 instruments, ~6–7 real" claim
  supplied for this entry did not verify as worded — see [TO-VERIFY](#to-verify) and
  ARTIFACT 11, which states the part that *is* verified.

### 6b. ORCID enrichment applied to the graph (properties-only, per ruling)

- **Tag:** CAPABILITY
- **What was found:** CrossRef author ORCIDs were written onto Researcher nodes as evidence, from a
  deterministic per-DOI lookup (CrossRef structured `author[].ORCID`) — never text extraction, never
  inferred, and matched only within the bounded per-paper author set (no global name search).
- **The numbers:** **475** of **2,076** Researcher nodes (**22.9%**) carry an `orcid` (verified live
  2026-07-23), split **195** author-verified (`orcid_authenticated: true`) / **280** publisher-asserted
  (`false`) — stored as two properties, never flattened. **63** candidates were EXCLUDED, not applied
  (31 rows on 7 reverse-error nodes, 30 compound-surname UNMATCHED, 2 fused). **0** `orcid:*` identifier
  nodes exist:
  the ruling is properties-only, so `ENABLE_ORCID_CANONICALIZATION` stays False (with it on, 03 would
  retire `researcher:*` -> `orcid:*` and, because 05 is MERGE-only per KI-14, mint a duplicate node set).
- **Why it matters:** The positive result behind BOUNDARY 7 and ARTIFACT 10 — identity enrichment landed
  on the modern corpus without touching node identity, and it flowed through pre-normalize JSONL -> 03 ->
  04 -> 05 so `graph = f(files)` holds.
- **`UPDATED 2026-07-25`:** these figures are the CrossRef path as measured on 2026-07-23 and are kept
  as written. Current live state is **481 of 2,062 (23.3%)**, because (i) the slug fix collapsed 14
  accent-variant nodes, 4 of which were both-ORCID pairs, and (ii) the equivalence review found **10**
  further ORCIDs from a non-CrossRef path. Those 10 carry `orcid_authenticated` **null** — no CrossRef
  attestation exists, and `false` would falsely read as publisher-asserted — so the split above still
  describes the CrossRef path exactly: **481 = 192 true + 279 false + 10 null** (live-verified).
- **Source:** live graph (2026-07-24); `docs/SCIKG_SCHEMA.md` "ORCID (Added 2026-07-23)";
  `docs/KNOWN_ISSUES.md` KI-16.

### 6c. Non-destructive identity resolution: 27 `SAME_AS` edges linking same-person nodes

- **Tag:** CAPABILITY
- **What was found:** Duplicate Researcher nodes for one person can be linked as equivalent **without
  merging anything**. Two undirected `Researcher↔Researcher` edge types were added; the applied one,
  `SAME_AS`, asserts "these two nodes are the same person" while leaving both nodes, both identifiers,
  and **both `name_full` values** in place. This matters because both names are often individually
  correct — a surname change, or a diacritic form the person actually publishes under — so merging would
  destroy a true name to fix a duplicate. Nothing is retired and no `AUTHORED_BY` edge is repointed.
- **The numbers:** **27** `SAME_AS` edges live, spanning **53** distinct Researcher nodes; **0**
  `POSSIBLY_SAME_AS` (the inferred type is defined but deliberately never populated, and is kept out of
  `05_load.py REL_TYPES` so a premature inferred edge aborts the load rather than entering the graph).
  The edges carry **33** distinct publications on their minor side — 33 paper-to-author attributions
  that a name match on the dominant spelling alone does not reach. Split by `anchor_type`:
  - **3 ORCID-anchored** (`orcid` ×2, `surname_change` ×1) — proof is a shared **author-verified**
    ORCID spanning both nodes. No human judgment involved.
  - **24 human-reviewed** (`anchor_type='human_review'`, emitted 2026-07-25) — proof is a reviewer's
    judgment on mechanical-artifact pairs: **14** OCR variants, **2** period-parse, **2** spelling
    variants, **2** transliteration, and 1 each of an ae/umlaut variant, a `Jr.` suffix, a character
    transposition, and one reversed prior exclusion. `properties.orcid` is null on all 24.
- **Honest limit — the two classes are not equally strong.** All 27 carry `confidence='proven'` because
  the schema constrains `SAME_AS` to that value; the weaker basis of the 24 is recorded by
  `anchor_type`, not by `confidence`. A consumer needing ORCID-grade proof must filter on `anchor_type`.
  The poster should not present all 27 as identifier-proven.
- **Audited dispositions, nothing left implicit:** of 37 pairs reviewed, **24** were confirmed same and
  emitted, **11** were confirmed *different* people and upheld as exclusions (no edge), and **1** is
  **HELD** as unresolved (`angstrom_j`↔`anstrom_j`). The held pair has no edge.
- **Why it matters:** It separates *identity resolution* from *data destruction*. The graph can answer
  "everything by this person" through an undirected `SAME_AS` traversal while still reporting each
  name as published — and every edge is reversible, because it is only an edge.
- **Source:** live graph (2026-07-25); `data/processed/relationships/researcher_equivalence.jsonl`
  (27 records, emitted through 03 → 04 → 05, never written to the graph directly);
  `docs/KNOWN_ISSUES.md` KI-17; `docs/SCIKG_SCHEMA.md` "SAME_AS / POSSIBLY_SAME_AS".

---

## BOUNDARY

### 7. The 2017 ORCID cliff (quantified, structural)

- **Tag:** BOUNDARY
- **What was found:** Author-identity enrichment via ORCID is available only for the modern
  corpus, and the cutoff is sharp rather than gradual. The blocker is compounded: the same era
  that lacks ORCIDs also lacks DOIs to query with.
- **The numbers:** Of **805** publications, only **397** carry a DOI — and the blocker is
  *absent* DOIs, not malformed ones (all 397 are well-formed; **0** malformed). Of **395**
  successfully fetched from CrossRef (2 not found, 0 errors), **285 (72.2%)** return ≥1 author
  ORCID: **1,159** of **3,078** author positions, **495** distinct ORCIDs, **205** authenticated
  at least once (561 authenticated instances vs 598 not).
  The cliff: **1 of 43 (2.3%)** papers through 2016 carry any author ORCID; **23 of 33 (69.7%)**
  in 2017; **284 of 352 (80.7%)** from 2017 onward, never below ~70% again.
- **`CORRECTED`:** the figure supplied for this entry was "0 of 40 papers through 2016". The
  verified figure is **1 of 43 (2.3%)** — one 2016 paper does carry an ORCID. The cliff is
  just as sharp, but the poster must not say zero.
- **Why it matters:** This is a boundary of the **source data**, not of the method — the shape
  mirrors ORCID adoption across scholarly publishing. Framed correctly it strengthens the work:
  identity enrichment reaches the post-2017 corpus, and the earlier portion is unreachable twice
  over (no DOI to query, no ORCID if queried).
- **Source:** `data/processed/review/orcid_coverage_report.md` §1.1, §1.3, §1.4.

### 8. Provenance graph, not a spectra/methods database (scope result)

- **Tag:** BOUNDARY
- **What was found:** Against a real researcher-submitted evaluation set, the graph answers
  structural and provenance questions (instrument usage, co-authorship, funder/journal/facility)
  and does not answer scientific-content questions (subject/topic, geography, citations,
  acquisition-mode). Instrument-parameter questions resolve only on an external raw-file subset,
  not across the corpus.
- **The numbers:** **14** researcher-submitted questions, exact wording preserved, every
  answerability tag verified by running Cypher: **4 PARTIAL**, **10 FUTURE WORK**,
  **0 clean ANSWERABLE**.
- **Important nuance — do not overstate:** the source document is explicit that *"no single
  question as worded is a clean ✅"*, because each question bundles a supported capability with
  an unsupported one. The underlying **capabilities** split cleanly; the **questions as asked**
  do not. The poster should claim the capability split, not "4 of 14 answered".
- **Why it matters:** This is the artifact's designed scope and defines the next enrichment
  phase. Stated honestly it is a scoping result, not a defect — and the refusal to dress an
  empty query up as an answer is itself part of the method.
- **Source:** `docs/DISCOVERY_QUESTIONS.md` (legend + per-question tags, verified against the
  graph 2026-07-20).

### 9. Provenance completeness ceiling

- **Tag:** BOUNDARY
- **What was found:** Few papers carry a complete provenance picture. Institution is the
  scarcest facet and is what gates the complete-provenance count.
- **The numbers** (all verified live 2026-07-23, over 805 publications):

  | Facet | Papers with ≥1 edge |
  |---|---:|
  | Instrument (`USES_INSTRUMENT`) | 357 |
  | Dataset (`HAS_DATASET`) | 246 |
  | Software (`USES_SOFTWARE`) | 175 |
  | Institution (`INVOLVES_INSTITUTION`) | 74 |

  **30** papers carry all four facets. **119** carry the three experimental facets
  (instrument + dataset + software). **419** carry none of the four.
- **`CORRECTED`:** three figures supplied for this entry were stale or conflated.
  Dataset coverage is **246**, not 239 (the supplied figure predates the mint batches).
  Three-facet count is **119**, not 116. And "419 papers were never PDF-extracted" conflates two
  different quantities: **419** is the number of papers with **zero facets**; the PDF extraction
  covered **378** papers (`data/raw/pdf_extraction/pdf_extraction_378papers.jsonl`, 378 lines,
  378 distinct papers), so **427** of 805 were never PDF-extracted. Use each number for its own
  claim.
- **Why it matters:** Sparsity here is predominantly *real* literature and deposition sparsity —
  most papers simply never state an institution or deposit data — with a documented
  transform-gap tail. It sets an honest ceiling on what completeness can be claimed.
- **Source:** live graph 2026-07-23; `data/raw/pdf_extraction/pdf_extraction_378papers.jsonl`;
  `docs/KNOWN_ISSUES.md` KI-13.

---

## ARTIFACT

### 10. Four independent researcher-identity defects

- **Tag:** ARTIFACT
- **What was found:** Researcher identity is degraded by four *independent* mechanisms, all
  inherited from the MagLab CSV. They are separable, and two of them were independently
  corroborated by ORCID.
- **The numbers:**

  | # | Mechanism | Evidence | Count |
  |---|---|---|---:|
  | (a) | **Fusion** — one node holds two people (CSV `"A and B"` convention) | `name_full` contains `" and "` | **108** nodes (live) |
  | (b) | **Accent-collapse** — accented characters dropped to `_` in the identifier | e.g. `researcher:chac_n_pati_o_m_2022` vs `researcher:chacon_patino_m_2025`, confirmed same person by shared ORCID | **34** nodes carry non-ASCII `name_full`; **30** of those have an underscore-collapsed identifier stem (live) |
  | (c) | **Compound-surname mis-parse** — the parser takes the *last whitespace-delimited word* as the family name | "Kevin M. Van Geem" → `Geem, K.M.V.`; "Diana Catalina Palacio Lozano" → `Lozano, D.C.P.`; "Germain Salvato Vallverdu" → `Vallverdu, G.S.` | accounts for **all 30** UNMATCHED CrossRef authors |
  | (d) | **Spelling variants** — requiring fuzzy matching | — | count **not verified**, see [TO-VERIFY](#to-verify) |

  ORCID cross-referencing independently corroborated (a) and (b): **6** ORCIDs resolve to more
  than one Researcher node **in the loaded graph** (fragmentation — same person, multiple nodes;
  live-queryable), and **7** nodes carry two ORCIDs each **in the survey** (fusion/conflation —
  multiple people, one node; all 7 excluded, not applied).
- **`CORRECTED`:** `orcid_coverage_report.md` §3.2 reports **7** fragmentation ORCIDs from the
  read-only survey; the applied graph has **6**. The 7th (`0000-0003-1926-0542`) mapped to the fused
  `martin_b_2017`, which was excluded from application — its second node is gone, so that ORCID now
  resolves to a single node. Keep the distinction straight: **7 in the survey, 6 in the loaded graph.**
- **Critical caveat for the poster:** of the 7 reverse-error nodes, only **1** is proven
  (`martin_b_2017`, same-paper — see CAPABILITY 5). The other **6** are cross-paper
  (`Zhang, Y.`, `Huang, C.`, `Lin, Y.`, `Smith, L.C.`, `Anderson, L.C.`, `Zhang, Z.`) — strong
  evidence, but one person holding two ORCID records is rare and possible. These 6 indict the
  identity model itself: `researcher:{family}_{initial}` cannot separate two researchers sharing
  a family name and first initial. Do not present all 7 as proven.
- **Why it matters:** Four distinct mechanisms means four distinct fixes; conflating them into
  "name matching is hard" would lose the diagnosis. (c) in particular damages author identity
  entirely independently of ORCID and was only visible because an external source disagreed.
- **Source:** live graph 2026-07-23; `data/processed/review/orcid_coverage_report.md`
  §2 (UNMATCHED analysis), §3.2, §3.3.

### 11. Instrument vocabulary fragmentation

- **Tag:** ARTIFACT
- **What was found:** Generic, descriptive, magnet-strength, and OCR-damaged instrument spellings
  coexist as separate nodes, inflating per-paper instrument counts and therefore facet totals.
- **The numbers:** **443** Instrument nodes live (after the 469 → 443 dedup). **59** instrument
  slugs contain `icr`. The worst single paper, `doi:10.1021/acs.energyfuels.1c02107`, carries
  **14** distinct Instrument nodes, of which **9** are FT-ICR-family spellings and **3** share
  the *same* CV accession `MS:1003948` (`instrument:raw:21t_icr`,
  `instrument:raw:9_4_ft_icr_mass_spectrometer`, `instrument:raw:ft_icr_ms`). One of the 14
  (`instrument:raw:high_fi_eld_fourier_transform_ion_cyclotron_resonance_m`) is a visible
  OCR ligature break of "high field". Per KI-7 the CV covers **34** aliases against **462**
  PDF-extracted instruments.
- **`CORRECTED`:** the figure supplied was "a paper appeared to use 10 instruments". The live
  maximum is **14** (`energyfuels.1c02107`); the 10-instrument paper is the *second* worst
  (`doi:10.1038/s43247-022-00407-8`). Also, the slug `instrument:raw:9_4_ft_icr` **does not
  exist** — the real nodes are `instrument:raw:9_4_ft_icr_mass_spectrometer` and
  `instrument:raw:9_4t_ft_icr`. Use verified slugs on the poster.
- **Important nuance — do not call this "triple-counting":** per the project's architecture
  decisions, magnet-strength variants (21T, 9.4T) are **deliberately separate** nodes; they share
  `MS:1003948` only because the PSI-MS CV has no more specific row. The genuine inflation is the
  *descriptive/ionization-prefixed* spellings (`appi_ft_icr_ms`, `esi_negative_ion_ft_icr_ms`,
  `ultrahigh_resolution_ft_icr_mass_spectrometer`, the OCR-broken `high_fi_eld_…`) coexisting
  with the collapsed generic `ft_icr_ms`.
- **Why it matters:** Any per-paper instrument count is an upper bound until consolidation lands.
  This is CV-coverage work, not a data error.
- **Source:** live graph 2026-07-23; `docs/KNOWN_ISSUES.md` KI-7, KI-7a;
  `data/processed/review/instrument_review.md` (SUPERSEDED banner).

### 12. A MagLab researcher whose full output is invisible to name matching

- **Tag:** ARTIFACT
- **What was found:** `researcher:chacon_patino_m` ("Chacón-Patiño, M.L.") and
  `researcher:aguilera_m` ("Aguilera, M.L.") are **one MagLab researcher who published under two
  surnames**. Both nodes carry the **same author-verified ORCID** `0000-0002-7273-5343`
  (`orcid_authenticated: true` on both). Neither name is wrong and neither is a typo — this is a real
  surname change, so no amount of string normalization, OCR repair, or transliteration reaches it.
  Only a **persistent identifier** could catch it.
- **The numbers:** `chacon_patino_m` carries **54** publications; `aguilera_m` carries **5**; the
  overlap is **0** papers, and the union via `SAME_AS` is **59**. So a query that name-matches on
  "Chacón-Patiño" — the form a reader would search — returns **54 of 59 (91.5%)** of this person's
  output in the graph, and **5 papers (8.5%) are invisible**, filed under a name a searcher has no
  reason to try. Before the `SAME_AS` edge there was nothing in the graph connecting them.
- **Why it matters:** This is the strongest single argument in the project for persistent identifiers
  over name matching, and it is a **MagLab** researcher, not a hypothetical. Every other identity
  defect on this poster (fusion, OCR, period-parse, accent collapse) is a *processing* artifact — a
  better parser would reduce it. This one is not a defect in our pipeline at all: the source data is
  correct on both sides, and the fragmentation is a fact about how people's names change over a career.
  It sets the floor on what name-based author disambiguation can achieve.
- **Honest limit:** this case is *proven* (shared author-verified ORCID) and should be presented as
  such — distinctly from the 24 human-reviewed equivalences in CAPABILITY 6c, whose basis is a
  reviewer's judgment, not an identifier. The 8.5%-invisible figure is specific to this researcher and
  must not be generalized into a corpus-wide miss rate; no such rate has been measured.
- **Source:** live graph (2026-07-25) — node `orcid`/`orcid_authenticated` and `AUTHORED_BY` counts
  queried directly; `data/processed/relationships/researcher_equivalence.jsonl`
  (`anchor_type='surname_change'`); `docs/KNOWN_ISSUES.md` KI-17.

---

## TO-VERIFY

Claims that are **not** cleared for the poster until confirmed. Do not state these as fact.

| # | Claim | Status | What would settle it |
|---|---|---|---|
| T1 | **Extraction error rate.** The reliability claim currently rests on *individual catches* (CAPABILITY 6), not a measured rate. | **Unmeasured — and the exposure is documented.** KI-10 records that **no audit pass** was run on the **274 instrument + 23 facility** fuzzy-grounded extractions (**297** total), because that is 297 PDF reads and `data/processed/pdf_text/` does not exist to grep. KI-10 explicitly calls this "a poster limitation, not this week's work." | A sampled audit over the 297 fuzzy-grounded extractions, with the sample size and confidence interval stated. Until then the poster may claim *specific errors caught*, never *an error rate*. |
| T2 | **Corpus drift between Aura instances.** | **Confirmed discrepancy, cause unverified. Narrowed to NODES only, 2026-07-25.** History on record: live graph **4,900 / 11,663** (2026-07-24), KI-15 and `CLAUDE.md` both **4,900 / 11,663** (agree; `CLAUDE.md` updated 2026-07-24 from a stale 4,891 / 11,654), and `docs/DISCOVERY_QUESTIONS.md` **4,909 / 11,668** (2026-07-20). As of **2026-07-25** the live graph is **4,886 / 11,690** (slug fix −14 nodes; `SAME_AS` +27 edges). So `DISCOVERY_QUESTIONS.md` is now **23 nodes higher** and **22 edges lower** than live. **Only the node gap is the open question** — the edge gap flipped sign because our own emit added edges, so it no longer indicates drift and should not be cited as evidence of it. Do NOT overwrite `DISCOVERY_QUESTIONS.md`'s figure until the node gap is traced. | Identify which instance `DISCOVERY_QUESTIONS.md` was measured against and reconcile the **23-node** difference (note: the earlier "9-node" framing predates the slug fix), or re-run its verification queries against the current instance. |
| T3 | **"Most facet-rich paper reported 10 instruments; ~6–7 real."** | **Did not verify as worded.** The live maximum is 14 instruments, not 10, and "most facet-rich" was not the selection criterion tested. The "~6–7 real" figure requires a human PDF read that has not been performed and recorded. | A recorded PDF read of the chosen paper establishing the true instrument count. ARTIFACT 11 states the verified portion; use that instead. |
| T4 | **"141 spelling variants held for human review."** | **Source not found.** The figure `141` does not appear anywhere in `docs/` or `data/processed/review/`. | Locate the review artifact that produced it, or re-derive and commit the count. |
| T5 | **952 → 888 raw-file reconciliation.** | **Endpoints verified, mechanism not.** `data/raw/rawfiles_pxd/` holds **952** source JSON files; `data/processed/entities/rawfiles_pxd.jsonl` has **984** lines / **920** distinct identifiers; the graph holds **888** `fisher_py` RawDataFile nodes. KI-1 documents that 02f emits duplicate node lines, which explains 952 → 984, but 920 → 888 is not established. | Trace the 32-node difference through `03`/`04` (dedup vs quarantine) and record it. Until then cite 934 total / 888 PXD-derived (live) and 952 source files separately — never as a chain. |

---

## Maintenance

- Re-verify every live-graph figure before the poster is finalized; the graph has moved twice in
  the last week (KI-15 mint batches) and at least three documents already carry stale totals.
- When adding an entry: state the tag, the exact query or artifact it came from, and the date.
  If a number cannot be traced in one hop, it belongs in TO-VERIFY.
- No figure in this file was copied from a prior document without re-checking it against the live
  graph or its cited source. Supplied or stale figures that did not survive that check are marked
  `CORRECTED` inline (entries 1, 7, 9, 10, 11) or moved to TO-VERIFY (T3, T4). Entry 10's correction
  is the survey-vs-loaded-graph fragmentation count (7 vs 6).
