# ORCID coverage and Researcher-node matching — read-only survey

**Status: MEASUREMENT ONLY. Nothing in this pass was applied.** No graph writes, no properties set, no nodes merged, no git operations. The two artifacts produced (`orcid_coverage_report.md`, `orcid_candidates.jsonl`) are proposals for review.

**Schema note.** `docs/SCIKG_SCHEMA.md` defines no `orcid` property on `Researcher`. Adding one is a schema decision for Diya, and nothing in `orcid_candidates.jsonl` can be applied until that is ruled. Every row in the candidate file carries `apply: false`.

**Method.** ORCIDs come from CrossRef's structured author array (`author[].ORCID`, `author[].authenticated-orcid`) — a deterministic per-DOI lookup, not an LLM extraction. No ORCID was inferred; no name-based lookup against the ORCID registry was performed. Matching is bounded per paper: a CrossRef author is compared **only** against the Researcher nodes already linked to that Publication by `AUTHORED_BY`. There is no global name search anywhere in the pipeline.

## 1. Coverage pass

### 1.1 Which publications are queryable at all

| Class | Count | Share of corpus |
|---|---:|---:|
| Publication nodes in graph | 805 | 100% |
| Has a `doi` property (queryable) | 397 | 49.3% |
| No `doi` property (**not** queryable) | 408 | 50.7% |

All 397 DOI values are well-formed (`^10\.\d{4,9}/\S+$`); there are no malformed DOIs to repair. The gap is not malformation — it is **absence**.

The 408 DOI-less records are essentially the pre-2016 tail (407 of 408 fall before 2016; the exceptions are 1 later records). They break down as:

| DOI-less subclass | Count | Note |
|---|---:|---|
| URL contains a recoverable DOI | 38 | e.g. `pubs.acs.org/doi/abs/10.1021/ac504166t` — the DOI is literally in the stored URL |
| URL present, no DOI in it | 131 | publisher landing/abstract pages, PubMed links |
| No URL at all | 239 | nothing to resolve from |

**This pass queried only the 397 records that already carry a `doi` property.** The 38 URL-recoverable DOIs are a real, cheap expansion of coverage — the DOI is present in committed source, so extracting it is a parse, not an inference — but harvesting them changes what the graph's `doi` field means and is out of scope for a read-only measurement. Flagged for Diya as a follow-up.

The split is almost perfectly chronological: DOI-less records span 2000–2019, DOI-bearing records span 2003–2026. The MagLab CSV simply did not record DOIs for older entries.

### 1.2 Fetch outcomes

| Outcome | Count |
|---|---:|
| not_found | 2 |

### 1.3 ORCID coverage among queried papers

| Metric | Value |
|---|---:|
| Papers queried | 395 |
| Papers returning >=1 author ORCID | 285 (72.2% of queried) |
| Papers returning no author ORCID | 110 (27.8% of queried) |
| Author positions in CrossRef | 3078 |
| Author positions carrying an ORCID | 1159 (37.7% of author positions) |
| **Total distinct ORCIDs found** | **495** |
| `authenticated-orcid: true` (instances) | 561 (48.4%) |
| `authenticated-orcid: false` (instances) | 598 (51.6%) |
| Distinct ORCIDs authenticated at least once | 205 |

For scale: the graph holds 3032 `AUTHORED_BY` edges on these DOI papers, against 3078 CrossRef author positions — within 1.5% of each other. For the DOI-bearing (i.e. modern) part of the corpus the MagLab CSV recorded essentially complete author lists, which is why the match rate in section 2 is high.

### 1.4 By publication year

| Year | Papers queried | With >=1 ORCID | % | ORCID instances |
|---:|---:|---:|---:|---:|
| 2003 | 1 | 0 | 0.0% | 0 |
| 2005 | 1 | 0 | 0.0% | 0 |
| 2006 | 1 | 0 | 0.0% | 0 |
| 2010 | 2 | 0 | 0.0% | 0 |
| 2011 | 1 | 0 | 0.0% | 0 |
| 2012 | 2 | 0 | 0.0% | 0 |
| 2013 | 1 | 0 | 0.0% | 0 |
| 2014 | 9 | 0 | 0.0% | 0 |
| 2015 | 2 | 0 | 0.0% | 0 |
| 2016 | 23 | 1 | 4.3% | 1 |
| 2017 | 33 | 23 | 69.7% | 45 |
| 2018 | 44 | 37 | 84.1% | 86 |
| 2019 | 31 | 26 | 83.9% | 82 |
| 2020 | 56 | 46 | 82.1% | 192 |
| 2021 | 38 | 29 | 76.3% | 160 |
| 2022 | 36 | 29 | 80.6% | 148 |
| 2023 | 34 | 27 | 79.4% | 116 |
| 2024 | 46 | 37 | 80.4% | 170 |
| 2025 | 29 | 26 | 89.7% | 143 |
| 2026 | 5 | 4 | 80.0% | 16 |

This is not a gradual skew — it is a **cliff between 2016 and 2017**. Through 2016, 1 of 43 papers carry any author ORCID (2.3%); from 2017 onward, 284 of 352 do (80.7%), and the rate never drops below ~70% again. That boundary is when the major publishers in this corpus began pushing ORCID through their submission systems, and it means ORCID is a usable identity signal for the modern corpus only.

Compounding effect worth stating plainly: the ORCID-rich years are exactly the years that have DOIs at all. The pre-2016 corpus is unreachable twice over — no DOI to query, and no ORCID even if queried. Any ORCID-based identity work will only ever touch the recent half of the graph.

### 1.5 By journal (CrossRef `container-title`, papers >= 3)

| Journal | Papers | With >=1 ORCID | % | ORCID instances |
|---|---:|---:|---:|---:|
| Energy & Fuels | 73 | 65 | 89.0% | 251 |
| Environmental Science & Technology | 40 | 36 | 90.0% | 124 |
| Journal of Geophysical Research: Biogeosciences | 24 | 23 | 95.8% | 132 |
| Analytical Chemistry | 23 | 20 | 87.0% | 75 |
| Journal of the American Society for Mass Spectrometry | 14 | 7 | 50.0% | 43 |
| Water Research | 11 | 7 | 63.6% | 24 |
| Global Biogeochemical Cycles | 9 | 9 | 100.0% | 89 |
| Organic Geochemistry | 7 | 1 | 14.3% | 3 |
| Biogeochemistry | 7 | 6 | 85.7% | 9 |
| Science of The Total Environment | 6 | 3 | 50.0% | 6 |
| (unknown journal) | 6 | 4 | 66.7% | 18 |
| Limnology and Oceanography | 5 | 5 | 100.0% | 11 |
| Fuel | 5 | 1 | 20.0% | 3 |
| Journal of Proteome Research | 5 | 4 | 80.0% | 11 |
| Proceedings of the National Academy of Sciences | 4 | 3 | 75.0% | 8 |
| Geochimica et Cosmochimica Acta | 4 | 3 | 75.0% | 11 |
| Communications Earth & Environment | 4 | 4 | 100.0% | 29 |
| Molecular & Cellular Proteomics | 4 | 2 | 50.0% | 14 |
| Scientific Reports | 4 | 2 | 50.0% | 5 |
| Nature Communications | 4 | 4 | 100.0% | 21 |
| Limnology and Oceanography Letters | 3 | 3 | 100.0% | 31 |
| Environmental Research | 3 | 1 | 33.3% | 1 |
| Soil & Environmental Health | 3 | 3 | 100.0% | 13 |
| ACS ES&T Water | 3 | 3 | 100.0% | 10 |
| Environmental Science: Processes & Impacts | 3 | 3 | 100.0% | 14 |
| Sustainable Energy & Fuels | 3 | 3 | 100.0% | 17 |
| Journal of Hazardous Materials | 3 | 1 | 33.3% | 2 |
| Frontiers in Marine Science | 3 | 0 | 0.0% | 0 |
| PROTEOMICS | 3 | 0 | 0.0% | 0 |
| Biochemistry | 3 | 3 | 100.0% | 8 |
| Bioorganic & Medicinal Chemistry Letters | 3 | 1 | 33.3% | 1 |
| _(93 journals with 1–2 papers)_ | 103 | 55 | 53.4% | 175 |

## 2. Match to existing Researcher nodes (bounded, per paper)

| Class | Count | Share |
|---|---:|---:|
| MATCH-UNIQUE | 1129 | 97.4% |
| MATCH-MULTIPLE | 0 | 0.0% |
| UNMATCHED | 30 | 2.6% |
| **Total ORCID-bearing CrossRef author positions** | **1159** | |

`MATCH-MULTIPLE` is empty, and that is a real result rather than a silent one: the graph's 108 fused nodes all sit in the 2000–2017 range, which is almost entirely the DOI-less tail, so they are barely reachable from a DOI-driven pass. The single fused node that *is* reachable (`researcher:martin_b_2017`) surfaces instead in section 3.3.

#### What the 30 UNMATCHED rows actually are

They are not random misses. Inspecting them against the graph shows a single systematic cause: **the MagLab CSV's name parser treats the last whitespace-delimited word as the family name** and folds everything before it into initials. Compound and particle surnames are therefore stored under the wrong family name:

| CrossRef author | Stored in graph as | Node |
|---|---|---|
| Van Geem, Kevin M. | `Geem, K.M.V.` | `researcher:geem_k_2024` |
| Palacio Lozano, Diana Catalina | `Lozano, D.C.P.` | `researcher:lozano_d_2024` |
| Salvato Vallverdu, Germain | `Vallverdu, G.S.` | `researcher:vallverdu_g_2026` |
| Rojas Ramírez, Carolina | `Ramirez, C.R.` | `researcher:ram_rez_c_2024` |

The matcher deliberately does **not** resolve these: family `Van Geem` does not equal family `Geem`, and bridging that gap would mean guessing. Under the bounded rule they are reported, never assigned. This is worth recording as a distinct data-quality defect in its own right — it affects the graph's author identity independently of ORCID.

## 3. Cross-paper consistency

Grouping the 1129 `MATCH-UNIQUE` candidates by ORCID across all papers.

### 3.1 Clean — one ORCID, one Researcher node everywhere (477)

These are the strongest candidates: the ORCID resolved to the same single node on every paper it appeared on.

**Caveat — 'clean' here means clean *from the ORCID side*, and 13 of these 477 are not safe to apply.** This section groups by ORCID; section 3.3 groups by node. An ORCID can point unambiguously at one node while that node is itself a conflation of two people. `researcher:anderson_l_2026` below is exactly this: the ORCID `0000-0001-8633-0251` resolves to it consistently across 14 papers, yet the node also answers to a second ORCID. Writing the ORCID onto the node would silently assert that the conflated node is one person. **Intersect this list against section 3.3 before applying anything.**

Of these, **134 are corroborated across more than one paper** (the same ORCID independently matching the same node on 2+ DOIs), which is the strongest evidence class here. The remaining 343 rest on a single paper.

| ORCID | Researcher node | Papers |
|---|---|---:|
| `0000-0001-7213-521X` | `researcher:mckenna_a` | 66 |
| `0000-0003-1302-2850` | `researcher:rodgers_r` | 63 |
| `0000-0001-9375-2532` | `researcher:marshall_a` | 38 |
| `0000-0003-0777-0748` | `researcher:spencer_r` | 38 |
| `0000-0002-7348-4814` | `researcher:kellerman_a` | 27 |
| `0000-0002-6032-6569` | `researcher:chen_h` | 26 |
| `0000-0002-4251-1613` | `researcher:borch_t` | 17 |
| `0000-0002-9569-3158` | `researcher:giusti_p` | 16 |
| `0000-0001-5878-6067` | `researcher:bouyssiere_b` | 16 |
| `0000-0002-4205-9866` | `researcher:blakney_g` | 15 |
| `0000-0001-8633-0251` | `researcher:anderson_l` | 14 |
| `0000-0001-5324-4525` | `researcher:weisbrod_c` | 14 |
| `0000-0002-1070-5923` | `researcher:podgorski_d` | 13 |
| `0000-0002-3487-6612` | `researcher:niles_s` | 12 |
| `0000-0001-7485-0604` | `researcher:young_r` | 10 |
| `0000-0003-3331-0526` | `researcher:smith_d` | 9 |
| `0000-0001-9634-9239` | `researcher:ruger_c` | 8 |
| `0000-0002-4272-2939` | `researcher:hendrickson_c` | 7 |
| `0000-0002-6904-5253` | `researcher:kurek_m` | 7 |
| `0000-0003-3244-3722` | `researcher:dayton_d` | 6 |
| `0000-0002-2406-5664` | `researcher:afonso_c` | 6 |
| `0000-0001-7091-9416` | `researcher:holt_a` | 6 |
| `0000-0001-9930-3690` | `researcher:fellman_j` | 6 |
| `0000-0003-2733-517X` | `researcher:roth_h` | 6 |
| `0000-0002-7011-1940` | `researcher:zito_p` | 6 |
| `0000-0001-8494-2908` | `researcher:tang_y` | 6 |
| `0000-0002-9654-9078` | `researcher:behnke_m` | 6 |
| `0000-0002-6237-0379` | `researcher:johnston_s` | 6 |
| `0000-0003-2333-8410` | `researcher:guillemette_f` | 6 |
| `0000-0001-6114-417X` | `researcher:hood_e` | 5 |

_(104 more)_

### 3.2 FRAGMENTATION — one ORCID, multiple Researcher nodes (4)

**This is definitive same-person-multiple-nodes evidence.** An ORCID is a persistent personal identifier; where one resolves to two or more distinct nodes, those nodes are the same human being. This is the strongest de-duplication signal available to the project — it does not depend on name-similarity heuristics.

| ORCID | Researcher nodes | `name_full` values | Implicated mechanism |
|---|---|---|---|
| `0000-0001-5774-2062` | `researcher:hoeschen_c`<br>`researcher:hoschen_c` | Hoeschen, C.<br>Hoschen, C. | spelling-variant |
| `0000-0002-7273-5343` | `researcher:aguilera_m`<br>`researcher:chacon_patino_m` | Aguilera, M.L.<br>Chacón-Patiño, M.L. | spelling-variant |
| `0000-0003-1116-8776` | `researcher:salvato_vallverdu_g`<br>`researcher:vallverdu_g` | Salvato Vallverdu, G.<br>Vallverdu, G.S. | spelling-variant |
| `0000-0003-1926-0542` | `researcher:hakansson_k`<br>`researcher:martin_b` | Håkansson, K.<br>Martin, B.R. and Hakansson, K. | fused-name/spelling-variant |

### 3.3 REVERSE ERROR — one Researcher node, multiple ORCIDs (7)

**FLAG LOUDLY.** A single node matching two different ORCIDs means that node very likely holds **two different people**. This is the opposite failure from fragmentation and is more damaging: merging would make it worse, and any analysis that treats the node as one person is already wrong.

These split into two evidence strengths, and the difference matters:

- **Same-paper collision (1)** — two ORCIDs landed on one node from the *same* DOI. This is **definitive**: a paper cannot list the same person twice, so the node provably holds two people.
- **Cross-paper only (6)** — the two ORCIDs come from different papers. Very strong, but not airtight: one person holding two ORCID records is rare yet possible, so these want a human glance before being treated as proven conflations.

That only **1 of 1129** MATCH-UNIQUE rows produced a same-paper collision is also a useful check on the matcher itself: it is not systematically over-matching.

| Researcher node | `name_full` | Evidence | ORCIDs | DOIs |
|---|---|---|---|---|
| `researcher:martin_b` | Martin, B.R. and Hakansson, K. | **same-paper — definitive** | `0000-0002-7136-2397`<br>`0000-0003-1926-0542` | `10.1021/acs.analchem.7b01461` |
| `researcher:anderson_l` | Anderson, L.C. | cross-paper | `0000-0001-7738-168X`<br>`0000-0001-8633-0251` | `10.1016/j.jbc.2022.102768`<br>`10.1016/j.mcpro.2024.100814`<br>`10.1016/j.mcpro.2024.100875`<br>`10.1016/j.xphs.2025.01.020`<br>`10.1021/acs.analchem.0c01064`<br>`10.1021/acs.analchem.1c00847` |
| `researcher:huang_c` | Huang, C. | cross-paper | `0000-0002-3865-6414`<br>`0000-0002-9833-5663` | `10.1016/j.envres.2025.123052`<br>`10.1016/j.watres.2023.119812`<br>`10.1016/j.watres.2023.120808` |
| `researcher:lin_y` | Lin, Y.J. | cross-paper | `0000-0001-8653-0050`<br>`0000-0002-0655-9580` | `10.1021/acs.energyfuels.8b03835`<br>`10.1021/jasms.1c00291` |
| `researcher:smith_l` | Smith, L.C. | cross-paper | `0000-0001-6866-5904`<br>`0000-0002-6652-8639` | `10.1029/2022gb007495`<br>`10.1029/2023jg007797`<br>`10.1038/s41592-019-0573-x` |
| `researcher:zhang_y` | Zhang, Y. | cross-paper | `0000-0002-3071-8625`<br>`0000-0002-3382-4570` | `10.1002/lno.11716`<br>`10.1016/j.scitotenv.2018.05.180`<br>`10.1016/j.scitotenv.2019.01.220`<br>`10.1016/j.watres.2019.115048`<br>`10.1021/acs.energyfuels.0c01564` |
| `researcher:zhang_z` | Zhang, Z. | cross-paper | `0000-0002-4472-7653`<br>`0000-0003-3249-0465` | `10.1016/j.wasman.2020.03.011`<br>`10.1021/acsestwater.4c00832`<br>`10.1039/d0ew00376j` |

The same-paper case, `researcher:martin_b_2017` (`"Martin, B.R. and Hakansson, K."`), is the fused-name mechanism caught red-handed: the node is literally two people, and ORCID independently confirms it. Note it appears in section 3.2 as well — it is simultaneously a fragment of Håkansson's identity and a fusion of two people, which is exactly what a first-author-and-last-author CSV string collapsed into one node produces.

The six cross-paper cases are all common family name + single initial (`Zhang, Y.`, `Huang, C.`, `Lin, Y.`, `Smith, L.C.`, `Anderson, L.C.`, `Zhang, Z.`). This points at the identity model itself: `researcher:{family}_{initial}` has no way to separate two researchers who share a family name and first initial, so they silently become one node. ORCID is the only signal in the corpus that can detect this.

## 4. Artifacts emitted

| File | Contents |
|---|---|
| `data/processed/review/orcid_coverage_report.md` | this report |
| `data/processed/review/orcid_candidates.jsonl` | one row per ORCID-bearing CrossRef author position (1159 rows: 1129 MATCH-UNIQUE, 0 MATCH-MULTIPLE, 30 UNMATCHED), every row `apply: false` |

Cached CrossRef responses live in `data/processed/cache/crossref/` (gitignored under `data/processed/*`), so re-running re-queries nothing.

### Nothing here is applied

To apply any of it, three things must happen first, in order:

1. **Schema ruling** — `docs/SCIKG_SCHEMA.md` gains an `orcid` property on `Researcher` (plus a provenance decision: `authenticated-orcid` true/false should be recorded, not dropped).
2. **Reverse-error triage** — the section 3.3 nodes are resolved, since assigning a single ORCID to a node holding two people would bake the error in.
3. **Pipeline route** — per the project's `graph = f(files)` rule, ORCIDs must enter through pre-normalize JSONL and flow 03 -> 04 -> 05, not by direct graph write.

