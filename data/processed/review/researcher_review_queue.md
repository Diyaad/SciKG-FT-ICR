# Researcher identity — review & no-action queues (non-MERGE-HIGH)

> **Read-only holding file. Nothing here is resolved or scheduled — it exists so no ledger row is lost.** The 13 anchored MERGE-HIGH pairs live in `researcher_merge_13_humanread.md`; this file captures everything else.

---

## 1. REVIEW — fuzzy candidates requiring human adjudication (141)

**These are FUZZY name-similarity candidates, NOT pre-poster work and NOT approved merges.** Each needs a human to decide whether the two nodes are the same person. The detection tier that produced them requires matching initials + a surname within Levenshtein 1–2, so most rows are same-initial pairs. **Same-initial / different-surname pairs (e.g. `dang_x`→`wang_x`) are EXPECTED FALSE POSITIVES — dismiss them (keep-separate).** A shared-anchor count of 0 is a strong signal to keep separate; a high count is worth a closer look but is still not proof (two real collaborators can have near-identical surnames).

**Reading the columns:** `shared_anchors` = shared co-authors + institutions + DOIs. **`shared_anchors = 0` is the strongest keep-separate signal** (no evidence the two nodes are the same person beyond a near-identical string). A non-zero count warrants a look but is not proof. Whether a surname difference is a *typo of one name* (e.g. `angstrom`/`anstrom`) or *two genuinely different short surnames* (e.g. `dang`/`wang`) cannot be decided by rule — that judgment is exactly what this queue defers to a human.

Decision column: `keep-separate` / `merge` / `uncertain` (blank = not yet reviewed).

| candidate_a | candidate_b | edit_dist | shared_anchors | decision |
|---|---|:--:|:--:|---|
| `researcher:hoeschen_c_2022` | `researcher:hoschen_c_2021` | 1 | 15 |  |
| `researcher:wang_y_2024` | `researcher:yang_y_2024` | 1 | 15 |  |
| `researcher:song_j_2013` | `researcher:wang_j_2024` | 2 | 14 |  |
| `researcher:chen_z_2025` | `researcher:shen_z_2025` | 1 | 14 |  |
| `researcher:chamot_rook_j_2019` | `researcher:chamot_rooke_j_2020` | 1 | 9 |  |
| `researcher:pa_a_toli_l_2020` | `researcher:pasa_tolic_l_2019` | 1 | 9 |  |
| `researcher:sets_e_2021` | `researcher:stets_e_2023` | 1 | 9 |  |
| `researcher:chen_y_2020` | `researcher:zheng_y_2014` | 2 | 6 |  |
| `researcher:ahif_d_2009` | `researcher:ahlf_d_2012` | 1 | 6 |  |
| `researcher:tang_x_2018` | `researcher:wang_x_2021` | 1 | 5 |  |
| `researcher:dzeilewski_a_2006` | `researcher:dzwilewski_a_2006` | 1 | 5 |  |
| `researcher:rodgers_r_2026` | `researcher:rogers_r_2006` | 1 | 5 |  |
| `researcher:jeppensen_e_2019` | `researcher:jeppesen_e_2021` | 1 | 5 |  |
| `researcher:pa_a_toli_l_2020` | `researcher:pa_sa_toli_l_2014` | 2 | 5 |  |
| `researcher:pa_sa_toli_l_2014` | `researcher:pasa_tolic_l_2019` | 1 | 5 |  |
| `researcher:tzortiziou_m_2023` | `researcher:tzortziou_m_2025` | 1 | 4 |  |
| `researcher:wang_y_2024` | `researcher:zhang_y_2025` | 2 | 4 |  |
| `researcher:yang_y_2024` | `researcher:zhang_y_2025` | 2 | 4 |  |
| `researcher:angstrom_j_2004` | `researcher:anstrom_j_2004` | 1 | 3 |  |
| `researcher:oomens_j_2010` | `researcher:oomes_j_2010` | 1 | 3 |  |
| `researcher:dehghanizade_m_2021` | `researcher:dehghanizadeh_m_2021` | 1 | 3 |  |
| `researcher:arumanayagam_a_2020` | `researcher:asumanayagam_a_2024` | 1 | 3 |  |
| `researcher:zimmerman_r_2023` | `researcher:zimmermann_r_2025` | 1 | 3 |  |
| `researcher:colilo_y_2014` | `researcher:corilo_y_2024` | 1 | 3 |  |
| `researcher:nagirnov_k_2024` | `researcher:nagornov_k_2020` | 1 | 3 |  |
| `researcher:standford_l_2005` | `researcher:stanford_l_2009` | 1 | 3 |  |
| `researcher:wang_x_2021` | `researcher:wnag_x_2025` | 2 | 2 |  |
| `researcher:auman_j_2010` | `researcher:putman_j_2020` | 2 | 2 |  |
| `researcher:meyer_baese_a_2010` | `researcher:meyer_b_se_a_2010` | 1 | 2 |  |
| `researcher:chen_m_2021` | `researcher:schon_m_2024` | 2 | 2 |  |
| `researcher:harir_m_2020` | `researcher:tarr_m_2024` | 2 | 2 |  |
| `researcher:huang_h_2020` | `researcher:yang_h_2025` | 2 | 2 |  |
| `researcher:vladimirov_g_2012` | `researcher:vladimirova_g_2015` | 1 | 2 |  |
| `researcher:tian_w_2021` | `researcher:xiao_w_2018` | 2 | 2 |  |
| `researcher:huang_c_2025` | `researcher:wang_c_2023` | 2 | 2 |  |
| `researcher:ding_y_2019` | `researcher:wang_y_2024` | 2 | 2 |  |
| `researcher:ding_y_2019` | `researcher:yang_y_2024` | 2 | 2 |  |
| `researcher:tang_y_2024` | `researcher:yang_y_2024` | 1 | 2 |  |
| `researcher:zhang_r_2021` | `researcher:zhao_r_2024` | 2 | 2 |  |
| `researcher:hawkings_j_2025` | `researcher:hawkins_j_2024` | 1 | 2 |  |
| `researcher:guluyz_k_2011` | `researcher:gulyuz_k_2011` | 2 | 2 |  |
| `researcher:feng_l_2021` | `researcher:meng_l_2023` | 1 | 2 |  |
| `researcher:avery_g_2015` | `researcher:avery_jr_g_2021` | 2 | 2 |  |
| `researcher:dang_x_2016` | `researcher:wang_x_2021` | 1 | 1 |  |
| `researcher:dang_x_2016` | `researcher:zhang_x_2024` | 2 | 1 |  |
| `researcher:wang_x_2021` | `researcher:zhang_x_2024` | 2 | 1 |  |
| `researcher:angstrom_j_2004` | `researcher:nystrom_j_2006` | 2 | 1 |  |
| `researcher:anstrom_j_2004` | `researcher:nystrom_j_2006` | 2 | 1 |  |
| `researcher:auman_j_2010` | `researcher:lanman_j_2004` | 2 | 1 |  |
| `researcher:cheng_j_2026` | `researcher:zhang_j_2024` | 2 | 1 |  |
| `researcher:wang_j_2024` | `researcher:zhang_j_2024` | 2 | 1 |  |
| `researcher:alber_m_2021` | `researcher:albu_m_2017` | 2 | 1 |  |
| `researcher:dong_h_2023` | `researcher:wang_h_2021` | 2 | 1 |  |
| `researcher:dong_h_2023` | `researcher:yang_h_2025` | 2 | 1 |  |
| `researcher:dong_h_2023` | `researcher:zeng_h_2013` | 2 | 1 |  |
| `researcher:huang_h_2020` | `researcher:wang_h_2021` | 2 | 1 |  |
| `researcher:wang_h_2021` | `researcher:yang_h_2025` | 1 | 1 |  |
| `researcher:wang_h_2021` | `researcher:zeng_h_2013` | 2 | 1 |  |
| `researcher:yang_h_2025` | `researcher:zeng_h_2013` | 2 | 1 |  |
| `researcher:chen_g_2022` | `researcher:zheng_g_2013` | 2 | 1 |  |
| `researcher:huang_c_2025` | `researcher:zhang_c_2025` | 2 | 1 |  |
| `researcher:song_c_2005` | `researcher:wang_c_2023` | 2 | 1 |  |
| `researcher:wang_c_2023` | `researcher:zhang_c_2025` | 2 | 1 |  |
| `researcher:zhang_c_2025` | `researcher:zhao_c_2023` | 2 | 1 |  |
| `researcher:tang_y_2024` | `researcher:wang_y_2024` | 1 | 1 |  |
| `researcher:tang_y_2024` | `researcher:zhang_y_2025` | 2 | 1 |  |
| `researcher:zhang_y_2025` | `researcher:zhao_y_2017` | 2 | 1 |  |
| `researcher:huang_t_2025` | `researcher:ouyang_t_2024` | 2 | 1 |  |
| `researcher:cheng_q_2024` | `researcher:zhang_q_2015` | 2 | 1 |  |
| `researcher:jiang_q_2025` | `researcher:wang_q_2024` | 2 | 1 |  |
| `researcher:jiang_q_2025` | `researcher:zhang_q_2015` | 2 | 1 |  |
| `researcher:mathews_j_2012` | `researcher:matthews_j_2024` | 1 | 1 |  |
| `researcher:curry_d_2010` | `researcher:murray_d_2020` | 2 | 1 |  |
| `researcher:baily_l_2023` | `researcher:early_l_2017` | 2 | 1 |  |
| `researcher:zhang_l_2015` | `researcher:zheng_l_2015` | 1 | 1 |  |
| `researcher:chen_z_2025` | `researcher:zheng_z_2024` | 2 | 1 |  |
| `researcher:shen_z_2025` | `researcher:zheng_z_2024` | 2 | 1 |  |
| `researcher:zhang_z_2025` | `researcher:zheng_z_2024` | 1 | 1 |  |
| `researcher:schulga_y_2005` | `researcher:shul_ga_y_2005` | 1 | 1 |  |
| `researcher:chen_x_2009` | `researcher:shen_x_2010` | 1 | 0 |  |
| `researcher:dang_x_2016` | `researcher:feng_x_2024` | 2 | 0 |  |
| `researcher:dang_x_2016` | `researcher:liang_x_2013` | 2 | 0 |  |
| `researcher:dang_x_2016` | `researcher:tang_x_2018` | 1 | 0 |  |
| `researcher:feng_x_2024` | `researcher:tang_x_2018` | 2 | 0 |  |
| `researcher:feng_x_2024` | `researcher:wang_x_2021` | 2 | 0 |  |
| `researcher:liang_x_2013` | `researcher:tang_x_2018` | 2 | 0 |  |
| `researcher:liang_x_2013` | `researcher:wang_x_2021` | 2 | 0 |  |
| `researcher:liang_x_2013` | `researcher:zhang_x_2024` | 2 | 0 |  |
| `researcher:tang_x_2018` | `researcher:zhang_x_2024` | 2 | 0 |  |
| `researcher:bailey_j_2017` | `researcher:walley_j_2024` | 2 | 0 |  |
| `researcher:chen_j_2013` | `researcher:cheng_j_2026` | 1 | 0 |  |
| `researcher:chen_j_2013` | `researcher:shen_j_2004` | 1 | 0 |  |
| `researcher:cheng_j_2026` | `researcher:shen_j_2004` | 2 | 0 |  |
| `researcher:song_j_2013` | `researcher:vonk_j_2021` | 2 | 0 |  |
| `researcher:baker_a_2022` | `researcher:parker_a_2018` | 2 | 0 |  |
| `researcher:dagan_a_2013` | `researcher:dalai_a_2015` | 2 | 0 |  |
| `researcher:qiao_p_2020` | `researcher:zito_p_2025` | 2 | 0 |  |
| `researcher:albu_m_2017` | `researcher:audu_m_2022` | 2 | 0 |  |
| `researcher:huang_m_2025` | `researcher:zhang_m_2018` | 2 | 0 |  |
| `researcher:tigges_m_2018` | `researcher:wigger_m_2002` | 2 | 0 |  |
| `researcher:dong_h_2023` | `researcher:tang_h_2010` | 2 | 0 |  |
| `researcher:gharibi_h_2024` | `researcher:hariri_h_2013` | 2 | 0 |  |
| `researcher:huang_h_2020` | `researcher:tang_h_2010` | 2 | 0 |  |
| `researcher:tang_h_2010` | `researcher:wang_h_2021` | 1 | 0 |  |
| `researcher:tang_h_2010` | `researcher:yang_h_2025` | 1 | 0 |  |
| `researcher:tang_h_2010` | `researcher:zeng_h_2013` | 2 | 0 |  |
| `researcher:chen_w_2006` | `researcher:zheng_w_2025` | 2 | 0 |  |
| `researcher:ding_w_2019` | `researcher:jiang_w_2014` | 2 | 0 |  |
| `researcher:ding_w_2019` | `researcher:kang_w_2014` | 2 | 0 |  |
| `researcher:jiang_w_2014` | `researcher:kang_w_2014` | 2 | 0 |  |
| `researcher:jiang_w_2014` | `researcher:tian_w_2021` | 2 | 0 |  |
| `researcher:heil_c_2023` | `researcher:neill_c_2019` | 2 | 0 |  |
| `researcher:o_malley_c_2016` | `researcher:ovalles_c_2022` | 2 | 0 |  |
| `researcher:zhao_c_2023` | `researcher:zhou_c_2024` | 2 | 0 |  |
| `researcher:shung_b_2025` | `researcher:zhang_b_2024` | 2 | 0 |  |
| `researcher:wang_b_2022` | `researcher:zhang_b_2024` | 2 | 0 |  |
| `researcher:ding_y_2019` | `researcher:fang_y_2012` | 2 | 0 |  |
| `researcher:ding_y_2019` | `researcher:tang_y_2024` | 2 | 0 |  |
| `researcher:ding_y_2019` | `researcher:xiong_y_2022` | 2 | 0 |  |
| `researcher:fang_y_2012` | `researcher:tang_y_2024` | 1 | 0 |  |
| `researcher:fang_y_2012` | `researcher:wang_y_2024` | 1 | 0 |  |
| `researcher:fang_y_2012` | `researcher:yang_y_2024` | 1 | 0 |  |
| `researcher:fang_y_2012` | `researcher:zhang_y_2025` | 2 | 0 |  |
| `researcher:liao_y_2012` | `researcher:zhao_y_2017` | 2 | 0 |  |
| `researcher:zhang_y_2025` | `researcher:zheng_y_2014` | 1 | 0 |  |
| `researcher:zhao_y_2017` | `researcher:zhou_y_2021` | 2 | 0 |  |
| `researcher:marce_r_2020` | `researcher:martz_r_2017` | 2 | 0 |  |
| `researcher:marce_r_2020` | `researcher:ware_r_2020` | 2 | 0 |  |
| `researcher:huang_t_2025` | `researcher:jiang_t_2018` | 2 | 0 |  |
| `researcher:wang_q_2024` | `researcher:zhang_q_2015` | 2 | 0 |  |
| `researcher:wagner_d_2010` | `researcher:walker_d_2020` | 2 | 0 |  |
| `researcher:jorner_k_2015` | `researcher:koerner_k_2010` | 2 | 0 |  |
| `researcher:feng_l_2021` | `researcher:zheng_l_2015` | 2 | 0 |  |
| `researcher:meng_l_2023` | `researcher:menin_l_2020` | 2 | 0 |  |
| `researcher:meng_l_2023` | `researcher:zheng_l_2015` | 2 | 0 |  |
| `researcher:cheng_f_2024` | `researcher:zheng_f_2021` | 1 | 0 |  |
| `researcher:wang_f_2003` | `researcher:yang_f_2020` | 1 | 0 |  |
| `researcher:meng_z_2024` | `researcher:zheng_z_2024` | 2 | 0 |  |
| `researcher:zhang_z_2025` | `researcher:zhao_z_2021` | 2 | 0 |  |
| `researcher:zhao_z_2021` | `researcher:zhou_z_2022` | 2 | 0 |  |
| `researcher:kieber_r_2021` | `researcher:weber_r_2019` | 2 | 0 |  |

_Of 141 fuzzy rows, 62 have zero shared anchors (default: keep-separate). Rows are sorted by anchor strength, so the strongest merge candidates are at the top and the zero-anchor rows at the bottom._

---

## 2. DISPLAY-ONLY — no action (single representation, no canonical twin) (23)

Each is a real person whose ONLY node carries a mangled/accented spelling. There is no clean twin to merge into, so **no merge and no Researcher-count change.** Optional future work: a display-name cleanup (restore proper spelling on `name_full`) — cosmetic only, not a merge, not blocking.

| researcher_id | name_full (as stored) | note |
|---|---|---|
| `researcher:b_lin_i_2006` | Bölin, I. |  |
| `researcher:b_ttcher_m_2024` | Böttcher, M.E. |  |
| `researcher:br_gger_c_2020` | Brügger, C. |  |
| `researcher:ca_as_j_2010` | Cañas, J.A. |  |
| `researcher:coley_t_2017` | Coley, T. and Jaffé, R. | ⚠ fused-author string — really re-parse (see §3), not display-only |
| `researcher:crespo_p_rez_v_2023` | Crespo-Pérez, V. |  |
| `researcher:d_az_s_nchez_l_2025` | Díaz-Sánchez, L.M. |  |
| `researcher:dupr_m_2020` | Dupré, M. |  |
| `researcher:ferr_b_2020` | Ferré, B. |  |
| `researcher:g_mez_torres_a_2019` | Gómez‐Torres, A. |  |
| `researcher:g_rke_r_2010` | Görke, R. |  |
| `researcher:giraldo_d_vila_d_2018` | Giraldo-Dávila, D. |  |
| `researcher:gr_ndger_f_2020` | Gründger, F. |  |
| `researcher:guti_rrez_sama_s_2018` | Gutiérrez Sama, S. |  |
| `researcher:h_kansson_k_2024` | Håkansson, K. |  |
| `researcher:k_ster_k_2024` | Köster, K. |  |
| `researcher:lvarez_salgado_x_2023` | ÁlvarezSalgado, X.A. |  |
| `researcher:meyer_b_se_a_2010` | Meyer-Bäse, A. |  |
| `researcher:morales_mart_nez_r_2019` | Morales‐Martínez, R. |  |
| `researcher:pa_a_toli_l_2020` | Paa-Tolić, L. |  |
| `researcher:ram_rez_c_2024` | Ramírez, C.R. |  |
| `researcher:rodr_guez_fortea_x_2013` | Rodríguez-Fortea |  |
| `researcher:sj_blom_j_2006` | Sjöblom, J. and Marshall, A.G. | ⚠ fused-author string — really re-parse (see §3), not display-only |

> **⚠ Bucketing caveat:** 2 of these 23 rows are actually **fused-author strings** whose fusion survived only in `name_full` (the identifier lost the `_and_` token, so the ledger classified them DISPLAY-ONLY). They belong with the re-parse work in §3, **not** a display-name cleanup: `researcher:coley_t_2017`, `researcher:sj_blom_j_2006`.

---

## 3. PARSE-FAIL / re-parse — fused & collective author strings (110)

These Researcher nodes carry **more than one person in `name_full`** — a node must be one person. **Do not merge, do not split here** (splitting needs the source paper → future **02-stage extraction fix**: split author strings on " and " / "&" / ";" and attach each name to its own existing node; drop/flag collective "field team / et al" strings). Re-run 02→03→04→05.

### 3a. Detection gap (why the count jumped 2 → 110)

The ledger caught **2** PARSE-FAIL by scanning the **identifier** for an `_and_` token (`researcher:chanton_j_p_and_cooper_w_2012`, `researcher:vanishing_glaciers_field_team_x_2025`). But most fusions survive only in **`name_full`** (the identifier keeps just the first author, e.g. `emmett_m_2012` labeled `"Emmett, M.R. and Marshall, A.G."`). Sweeping `name_full` instead of the identifier finds **110** (107 two-name "X and Y", 3 collective/et-al). The ledger classification stays source-of-record; these are **`name_full`-detected** additions.

> **Nature of the defect (measured):** each fused id is the **sole node for its first author** (the identifier is correct); the second name was swallowed into the label, so on the affected papers the swallowed co-author has **no edge to their real node**. The fix re-attaches the co-author, it does not invent a node.

### 3b. STEP-2 sign-off safety

✅ **0 fused nodes appear in the 13 MERGE-HIGH sign-off pairs.** No fused node is at risk of being absorbed into a clean twin by Phase 2. The sign-off sheet is safe as-is.

### 3c. STEP-3 poster impact — the Marshall–Rodgers pair IS affected

**26** fused nodes name **Marshall, A.G.** as the swallowed co-author (135 papers on them). On **83** of those papers the real Marshall node is not attached — hidden Marshall authorship. Crucially for the headline pair:

- Current real **Marshall × Rodgers** shared-paper count in the graph: **56** (the "~55").
- **Ground-truth edge-fix result (measured against raw CSV author strings): 56 → 64 (+8).** The swallowed Marshall co-authorship is real only on the papers whose CSV author string actually contains the fused token. Of the papers with real Rodgers + a Marshall-fused phantom, **8** genuinely had Marshall as an author (the other 8 never did — a node-wide assumption would have fabricated them). Same correction class as the Rodgers `_x` fix; it **does touch the 55**, honest delta **+8**.

  Full per-paper fix (direction B: add missing `AUTHORED_BY` edges) → `coauthor_edge_fix_ledger.jsonl` (79 grounded edges, `apply:false`) + `coauthor_edge_fix_review.md`. **Reconcile with the pending Rodgers `_x` merge — do not stack.**

### 3d. Full fused-author list (110 nodes)

`src` — `id`=identifier caught it (ledger PARSE-FAIL); `nf`=name_full-only (this sweep). `M`=names Marshall.

| researcher_id | name_full | papers | type | src | M |
|---|---|:--:|---|:--:|:--:|
| `researcher:emmett_m_2012` | Emmett, M.R. and Marshall, A.G. | 64 | two-name-and | nf | ✔ |
| `researcher:purcell_j_2010` | Purcell, J.M. and Marshall, A.G. | 21 | two-name-and | nf | ✔ |
| `researcher:hakansson_k_2005` | Hakansson, K. and Marshall, A.G. | 13 | two-name-and | nf | ✔ |
| `researcher:eyler_j_2010` | Eyler, J.R. and Polfer, N.C. | 11 | two-name-and | nf |  |
| `researcher:phillips_d_2017` | Phillips, D. and Krajewski, L. | 8 | two-name-and | nf |  |
| `researcher:bythell_b_2016` | Bythell, B.J. and Stenson, A.C. | 7 | two-name-and | nf |  |
| `researcher:hudgins_r_2004` | Hudgins, R.R. and Marshall, A.G. | 7 | two-name-and | nf | ✔ |
| `researcher:meijer_g_2006` | Meijer, G., et al. | 7 | collective/et-al | nf |  |
| `researcher:savory_j_2014` | Savory, J.J. and Hendrickson, C.L. | 7 | two-name-and | nf |  |
| `researcher:davidsson_p_2005` | Davidsson, P. and Nilsson, C.L. | 4 | two-name-and | nf |  |
| `researcher:glaser_p_2013` | Glaser, P.H. and Cooper, W.T. | 4 | two-name-and | nf |  |
| `researcher:groenewold_g_2010` | Groenewold, G.S. and Van Stipdonk, M.J. | 4 | two-name-and | nf |  |
| `researcher:abadi_g_2014` | Abadi, G. and Manning, T.J. | 3 | two-name-and | nf |  |
| `researcher:blennow_k_2004` | Blennow, K. and Davidsson, P. | 3 | two-name-and | nf |  |
| `researcher:lang_f_2010` | Lang, F.F. and Conrad, C.A. | 3 | two-name-and | nf |  |
| `researcher:sakalian_m_2004` | Sakalian, M. and Prevelige, P.E., Jr. | 3 | two-name-and | nf |  |
| `researcher:sato_t_2008` | Sato, T. and Johnel, D. | 3 | two-name-and | nf |  |
| `researcher:teclemariam_a_2009` | Teclemariam, A. and Marshall, A.G. | 3 | two-name-and | nf | ✔ |
| `researcher:van_der_rest_g_2001` | van der Rest, G. and Marshall, A.G. | 3 | two-name-and | nf | ✔ |
| `researcher:wang_d_2011` | Wang, D. and Polfer, N.C. | 3 | two-name-and | nf |  |
| `researcher:asomaning_s_2011` | Asomaning, S. and Marshall, A.G. | 2 | two-name-and | nf | ✔ |
| `researcher:baykut_g_2004` | Baykut, G. and Hakansson, P. | 2 | two-name-and | nf |  |
| `researcher:conrad_c_2011` | Conrad, C.A. and Marshall, A.G. | 2 | two-name-and | nf | ✔ |
| `researcher:czarnecki_j_2007` | Czarnecki, J. and Wu, X.A. | 2 | two-name-and | nf |  |
| `researcher:guan_s_2010` | Guan, S.H. and Burlingame, A.L. | 2 | two-name-and | nf |  |
| `researcher:jaffe_r_2015` | Jaffe, R. and Cooper, W.T. | 2 | two-name-and | nf |  |
| `researcher:rios_o_2014` | Rios, O. and Johs, A. | 2 | two-name-and | nf |  |
| `researcher:smith_r_2015` | Smith, R.D. and Marshall, A.G. | 2 | two-name-and | nf | ✔ |
| `researcher:stiegman_a_2003` | Stiegman, A.E. and Marshall, A.G. | 2 | two-name-and | nf | ✔ |
| `researcher:suhai_s_2005` | Suhai, S. and Paizs, B. | 2 | two-name-and | nf |  |
| `researcher:svennerholm_a_2006` | Svennerholm, A.-M. and Nilsson, C.L. | 2 | two-name-and | nf |  |
| `researcher:willey_j_2015` | Willey, J.D. and Podgorski, D.C. | 2 | two-name-and | nf |  |
| `researcher:zuttel_a_2005` | Zuttel, A. and Billups, W.E. | 2 | two-name-and | nf |  |
| `researcher:adhikari_p_2016` | Adhikari, P.L. and Reddy, C.M. | 1 | two-name-and | nf |  |
| `researcher:al_naggar_i_2007` | Al-Naggar, I.M. and Bubb, M.R. | 1 | two-name-and | nf |  |
| `researcher:allis_c_2004` | Allis, C.D. and Burllingame, A.L. | 1 | two-name-and | nf |  |
| `researcher:andrews_b_2006` | Andrews, B. and Marshall, A.G. | 1 | two-name-and | nf | ✔ |
| `researcher:atolia_e_2011` | Atolia, E. and Marshall, A.G. | 1 | two-name-and | nf | ✔ |
| `researcher:balaram_p_2006` | Balaram, P. and Marshall, A.G. | 1 | two-name-and | nf | ✔ |
| `researcher:baldock_j_2009` | Baldock, J.A. and Hatcher, P.G. | 1 | two-name-and | nf |  |
| `researcher:bays_j_2013` | Bays, J.S. and Cooper, W.T. | 1 | two-name-and | nf |  |
| `researcher:boismenu_d_2005` | Boismenu, D. and Kerney, R.E. | 1 | two-name-and | nf |  |
| `researcher:bolanos_b_2006` | Bolanos, B. and Greig, M.J. | 1 | two-name-and | nf |  |
| `researcher:buckley_j_2013` | Buckley, J.S. and et al. | 1 | collective/et-al | nf |  |
| `researcher:chanton_j_p_and_cooper_w_2012` | Chanton J.P. and Cooper, W.T. | 1 | two-name-and | id |  |
| `researcher:coley_t_2017` | Coley, T. and Jaffé, R. | 1 | two-name-and | nf |  |
| `researcher:conrad_b_2001` | Conrad, B.P. and Perala, S.M. | 1 | two-name-and | nf |  |
| `researcher:cundari_t_2004` | Cundari, T.R. and Marshall, A.G. | 1 | two-name-and | nf | ✔ |
| `researcher:ebright_r_2004` | Ebright, R.H. and Scott, R.A. | 1 | two-name-and | nf |  |
| `researcher:fanucci_g_2009` | Fanucci, G.E. and Marshall, A.G. | 1 | two-name-and | nf | ✔ |
| `researcher:gaskell_s_2003` | Gaskell, S.J. and Marshall, A.G | 1 | two-name-and | nf | ✔ |
| `researcher:gauthier_t_2010` | Gauthier, T. and Guibard, I. | 1 | two-name-and | nf |  |
| `researcher:geng_a_2012` | Geng, A. and Hsu, C.S. | 1 | two-name-and | nf |  |
| `researcher:gibson_j_2016` | Gibson, J.K. and Bythell, B.J. | 1 | two-name-and | nf |  |
| `researcher:gray_n_2014` | Gray, N.S. and Marto, J.A. | 1 | two-name-and | nf |  |
| `researcher:greaney_m_2001` | Greaney, M.A. and Qian, K. | 1 | two-name-and | nf |  |
| `researcher:green_l_2005` | Green, L.A. and Olmstead, W.N. | 1 | two-name-and | nf |  |
| `researcher:green_n_2015` | Green, N.W. and Perdue, E.M. | 1 | two-name-and | nf |  |
| `researcher:gresham_g_2010` | Gresham, G.L. and Mcllwain, M.E. | 1 | two-name-and | nf |  |
| `researcher:griffin_j_2010` | Griffin, J.D. and Marto, J.A. | 1 | two-name-and | nf |  |
| `researcher:hannon_m_2010` | Hannon, M.M. and Cooper, H.J. | 1 | two-name-and | nf |  |
| `researcher:horwitz_s_2003` | Horwitz, S.B. and Orr, G.A. | 1 | two-name-and | nf |  |
| `researcher:isolani_p_2001` | Isolani, P.C. and Vicentini, G. | 1 | two-name-and | nf |  |
| `researcher:jennings_k_2001` | Jennings, K.R. and Eyler, J.R. | 1 | two-name-and | nf |  |
| `researcher:just_i_2005` | Just, I. and Marshall, A.G. | 1 | two-name-and | nf | ✔ |
| `researcher:keffer_d_2014` | Keffer, D.J. and Johs, A. | 1 | two-name-and | nf |  |
| `researcher:kelly_p_2001` | Kelly, P.H. and Marshall, A.G. | 1 | two-name-and | nf | ✔ |
| `researcher:khitrov_g_2007` | Khitrov, G.A. and Marshall, A.G. | 1 | two-name-and | nf | ✔ |
| `researcher:kishi_s_2012` | Kishi, S. and Yang, X.-L. | 1 | two-name-and | nf |  |
| `researcher:koleske_a_2017` | Koleske, A.J. and Boggon, T.J. | 1 | two-name-and | nf |  |
| `researcher:korak_a_2017` | Korak, A.N. and Rosario-Ortiz, F.L. | 1 | two-name-and | nf |  |
| `researcher:lavrinovicha_m_2002` | Lavrinovicha, M. and Bergstrom, S. | 1 | two-name-and | nf |  |
| `researcher:legault_p_2005` | Legault, P. and Omichinski, J.G. | 1 | two-name-and | nf |  |
| `researcher:liu_t_2007` | Liu, T.J. and Conrad, C.A. | 1 | two-name-and | nf |  |
| `researcher:lu_h_2008` | Lu, H.J. and Xia, Y.Y. | 1 | two-name-and | nf |  |
| `researcher:mansson_j_2005` | Mansson, J.E. and Nilsson, C.L. | 1 | two-name-and | nf |  |
| `researcher:martin_b_2017` | Martin, B.R. and Hakansson, K. | 1 | two-name-and | nf |  |
| `researcher:martinex_haya_b_2008` | Martinex-Haya, B. and Marshall, A.G. | 1 | two-name-and | nf | ✔ |
| `researcher:mccammon_c_2006` | McCammon, C. and Dubrovinsky, L. | 1 | two-name-and | nf |  |
| `researcher:mclendon_g_2003` | McLendon, G.L. and Marshall, A.G. | 1 | two-name-and | nf | ✔ |
| `researcher:meijer_e_2002` | Meijer, E.W. and Meskers, S.C.J. | 1 | two-name-and | nf |  |
| `researcher:mookherjee_a_2009` | Mookherjee, A. and Armentrout, P.B. | 1 | two-name-and | nf |  |
| `researcher:muller_h_2008` | Muller, H. and Koseoglu, O.R. | 1 | two-name-and | nf |  |
| `researcher:noble_l_2008` | Noble, L. and Manning, T.J. | 1 | two-name-and | nf |  |
| `researcher:ottosson_h_2015` | Ottosson, H. and Alabugin, I.V. | 1 | two-name-and | nf |  |
| `researcher:peters_k_2010` | Peters, K.E. and Mullins, O.C. | 1 | two-name-and | nf |  |
| `researcher:pitt_a_2004` | Pitt, A. and Marshall, A.G. | 1 | two-name-and | nf | ✔ |
| `researcher:razin_e_2013` | Razin, E. and Guo, M. | 1 | two-name-and | nf |  |
| `researcher:rostom_a_2000` | Rostom, A.A. and Robinson, C.V. | 1 | two-name-and | nf |  |
| `researcher:ryan_m_2001` | Ryan, M.F. and Eyler, J.R. | 1 | two-name-and | nf |  |
| `researcher:senko_m_2008` | Senko, M.W. and Marshall, A.G. | 1 | two-name-and | nf | ✔ |
| `researcher:shang_w_2015` | Shang, W. and Stroupe, M.E. | 1 | two-name-and | nf |  |
| `researcher:sharon_n_2002` | Sharon, N. and Krengel, U. | 1 | two-name-and | nf |  |
| `researcher:sj_blom_j_2006` | Sjöblom, J. and Marshall, A.G. | 1 | two-name-and | nf | ✔ |
| `researcher:stagg_s_2017` | Stagg, S.M. and Li, H. | 1 | two-name-and | nf |  |
| `researcher:stewart_m_2009` | Stewart, M. and Roberts, T.M. | 1 | two-name-and | nf |  |
| `researcher:stine_o_2013` | Stine, O.C. and Williams, H.N. | 1 | two-name-and | nf |  |
| `researcher:tan_y_2007` | Tan, Y.J. and Xia, Y.Y. | 1 | two-name-and | nf |  |
| `researcher:trimpin_s_2013` | Trimpin, S. and Marshall, A.G. | 1 | two-name-and | nf | ✔ |
| `researcher:tung_y_2016` | Tung, Y. and Noble, R.T. | 1 | two-name-and | nf |  |
| `researcher:tyler_p_2010` | Tyler, P.C. and Schramm, V.L. | 1 | two-name-and | nf |  |
| `researcher:vanishing_glaciers_field_team_x_2025` | Vanishing Glaciers Field Team, X. | 1 | collective/et-al | id |  |
| `researcher:volmer_d_2005` | Volmer, D.A. and Marshall, A.G. | 1 | two-name-and | nf | ✔ |
| `researcher:walton_d_2008` | Walton, D.J. and Peterson, I.R. | 1 | two-name-and | nf |  |
| `researcher:wang_m_2014` | Wang, M.-W. and Kim, S. | 1 | two-name-and | nf |  |
| `researcher:wenger_l_2005` | Wenger, L.M. and Mankiewicz, P. | 1 | two-name-and | nf |  |
| `researcher:whelton_a_2015` | Whelton, A.J. and Stenson, A.C. | 1 | two-name-and | nf |  |
| `researcher:wu_x_2007` | Wu, X.A. and Taylor, S. | 1 | two-name-and | nf |  |
| `researcher:wudl_f_2015` | Wudl, F. and Echegoyen, L. | 1 | two-name-and | nf |  |
| `researcher:zhou_h_2013` | Zhou, H. and Ghosh, A. | 1 | two-name-and | nf |  |

---

_Sources: `researcher_merge_ledger.jsonl` (179 rows: 13 MERGE-HIGH + 141 REVIEW + 23 DISPLAY-ONLY + 2 identifier-caught PARSE-FAIL) + a read-only `name_full` fused-author sweep of the live graph (110 nodes). No graph changes, no merges, no splits._