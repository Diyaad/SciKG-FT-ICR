# Co-author edge-fix — dry-run ledger review (READ-ONLY, awaiting sign-off)

_Instance `bf9ce500.databases.neo4j.io`. Direction (B): add the AUTHORED_BY edge for co-authors swallowed into a fused `name_full` token. **No graph writes; nothing applied.**_

## Identity model (STEP 0)
One node per person (not per person-year): `marshall_a_2026` is the sole Marshall node (202 papers). Year suffix in identifiers is not a person-splitter. A resolved second author therefore links to exactly one node.

## CRITICAL — why 79, not 198 (no fabrication)

A fused node's identifier is its **first** author, and it accumulates ALL that author's papers (e.g. `emmett_m_2012` = 64 papers). The co-author was swallowed only on the papers whose **raw CSV author string actually contains the fused token** (Emmett: 13 of 64; Purcell: 1 of 21). Staging an edge for every paper on the node would **fabricate 119 co-authorships**. This ledger stages an edge ONLY where the CSV author string for that specific paper contains the fused token — ground-truth evidence, per paper.

## STEP 1 resolution classes (110 fused nodes)

- **RESOLVED** (2nd author = exactly one node): 57 nodes -> **79 grounded edges** (this ledger)
- **AMBIGUOUS** (>1 candidate node): 0  (none — one-node-per-person)
- **NO-NODE** (2nd author has no standalone node -> needs a mint, separate call): 50
- **COLLECTIVE** (et-al / field-team, not a person): 3

## Projected impact (STEP 3) — edge-fix effect ALONE

- Edges to add: **79** across 57 nodes.
- To top author **Marshall, A.G.**: 44 edges.
- **Marshall–Rodgers shared papers: 56 -> 64** (+8 newly-grounded co-authored papers).

> **Reconcile, do not stack:** the pending Rodgers `_x` merge (`rodgers_r_p_x_2012` -> `rodgers_r_2026`) ALSO moves this pair. This projection already counts BOTH real Rodgers nodes, so it is merge-invariant — but whoever recomputes the poster number must apply the two corrections **together and once**, not add them twice.

## Top edge counts by second author

- Marshall, A.G.: 44
- Cooper, W.T.: 5
- Nilsson, C.L.: 5
- Stenson, A.C.: 2
- Podgorski, D.C.: 2
- Reddy, C.M.: 1
- Hatcher, P.G.: 1
- Greig, M.J.: 1
- Hsu, C.S.: 1
- Qian, K.: 1
- van Stipdonk, M.J.: 1
- Cooper, H.J.: 1

## REVIEW — NOT in the apply ledger (need a human / a separate call)

### NO-NODE — second author has no standalone Researcher node (needs a mint)

| fused node | swallowed second author | normalized key |
|---|---|---|
| `researcher:abadi_g_2014` | Manning, T.J. | `manningtj` |
| `researcher:al_naggar_i_2007` | Bubb, M.R. | `bubbmr` |
| `researcher:allis_c_2004` | Burllingame, A.L. | `burllingameal` |
| `researcher:baykut_g_2004` | Hakansson, P. | `hakanssonp` |
| `researcher:blennow_k_2004` | Davidsson, P. | `davidssonp` |
| `researcher:boismenu_d_2005` | Kerney, R.E. | `kerneyre` |
| `researcher:coley_t_2017` | Jaffé, R. | `jaffer` |
| `researcher:conrad_b_2001` | Perala, S.M. | `peralasm` |
| `researcher:czarnecki_j_2007` | Wu, X.A. | `wuxa` |
| `researcher:ebright_r_2004` | Scott, R.A. | `scottra` |
| `researcher:eyler_j_2010` | Polfer, N.C. | `polfernc` |
| `researcher:gauthier_t_2010` | Guibard, I. | `guibardi` |
| `researcher:gibson_j_2016` | Bythell, B.J. | `bythellbj` |
| `researcher:gray_n_2014` | Marto, J.A. | `martoja` |
| `researcher:green_l_2005` | Olmstead, W.N. | `olmsteadwn` |
| `researcher:green_n_2015` | Perdue, E.M. | `perdueem` |
| `researcher:gresham_g_2010` | Mcllwain, M.E. | `mcllwainme` |
| `researcher:griffin_j_2010` | Marto, J.A. | `martoja` |
| `researcher:guan_s_2010` | Burlingame, A.L. | `burlingameal` |
| `researcher:horwitz_s_2003` | Orr, G.A. | `orrga` |
| `researcher:isolani_p_2001` | Vicentini, G. | `vicentinig` |
| `researcher:jennings_k_2001` | Eyler, J.R. | `eylerjr` |
| `researcher:keffer_d_2014` | Johs, A. | `johsa` |
| `researcher:koleske_a_2017` | Boggon, T.J. | `boggontj` |
| `researcher:lang_f_2010` | Conrad, C.A. | `conradca` |
| `researcher:lavrinovicha_m_2002` | Bergstrom, S. | `bergstroms` |
| `researcher:legault_p_2005` | Omichinski, J.G. | `omichinskijg` |
| `researcher:liu_t_2007` | Conrad, C.A. | `conradca` |
| `researcher:lu_h_2008` | Xia, Y.Y. | `xiayy` |
| `researcher:mccammon_c_2006` | Dubrovinsky, L. | `dubrovinskyl` |
| `researcher:meijer_e_2002` | Meskers, S.C.J. | `meskersscj` |
| `researcher:mookherjee_a_2009` | Armentrout, P.B. | `armentroutpb` |
| `researcher:muller_h_2008` | Koseoglu, O.R. | `koseogluor` |
| `researcher:noble_l_2008` | Manning, T.J. | `manningtj` |
| `researcher:rios_o_2014` | Johs, A. | `johsa` |
| `researcher:ryan_m_2001` | Eyler, J.R. | `eylerjr` |
| `researcher:sakalian_m_2004` | Prevelige, P.E., Jr. | `preveligepejr` |
| `researcher:sato_t_2008` | Johnel, D. | `johneld` |
| `researcher:sharon_n_2002` | Krengel, U. | `krengelu` |
| `researcher:stagg_s_2017` | Li, H. | `lih` |
| `researcher:stewart_m_2009` | Roberts, T.M. | `robertstm` |
| `researcher:tan_y_2007` | Xia, Y.Y. | `xiayy` |
| `researcher:tung_y_2016` | Noble, R.T. | `noblert` |
| `researcher:tyler_p_2010` | Schramm, V.L. | `schrammvl` |
| `researcher:walton_d_2008` | Peterson, I.R. | `petersonir` |
| `researcher:wang_d_2011` | Polfer, N.C. | `polfernc` |
| `researcher:wenger_l_2005` | Mankiewicz, P. | `mankiewiczp` |
| `researcher:wu_x_2007` | Taylor, S. | `taylors` |
| `researcher:zhou_h_2013` | Ghosh, A. | `ghosha` |
| `researcher:zuttel_a_2005` | Billups, W.E. | `billupswe` |

### COLLECTIVE — not a person, no edge

- `researcher:buckley_j_2013` — collective/et-al token: 'et al.'
- `researcher:meijer_g_2006` — collective first-author string
- `researcher:vanishing_glaciers_field_team_x_2025` — collective first-author string


## Label cleanup — FLAGGED, NOT staged (name_full may be CrossRef-sourced)

The 110 fused nodes' `name_full` should later be trimmed "First and Second" -> "First". **This fix adds edges only; it does not overwrite `name_full`.** Optional follow-up for Diya, separate from this reconciliation. Full list in `researcher_review_queue.md` §3.
