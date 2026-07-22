# Researcher merge — MERGE-HIGH sign-off sheet (13 pairs)

> **Confirm each pair is the same person before setting apply:true. Applies to both instances. Changes Researcher count 2076->~2063 and the co-authorship network.**

_Extracted read-only from `researcher_merge_ledger.jsonl`. 13 MERGE-HIGH rows, sorted by anchor strength (most shared co-authors first). To approve: set `apply: true` on the matching row in the ledger, then run Phase 2 (`scripts/merge_researcher_nodes.py --apply`)._

| ☐ | mangled_id | → proposed_canonical_id | reconstructed_name | shared_coauthors | shared_institution | shared_doi | evidence |
|:--:|---|---|---|:--:|:--:|:--:|---|
| ☐ | `researcher:barr_re_mangote_c_2025` | `researcher:barrere_mangote_c_2024` | Barrere-Mangote, C. | 14 | 0 | — | exact normalized-name key 'barreremangotec'; 14 shared co-authors, 0 shared inst, 0 shared DOI |
| ☐ | `researcher:sch_n_m_2023` | `researcher:schon_m_2024` | Schon, M. | 9 | 0 | — | exact normalized-name key 'schonm'; 9 shared co-authors, 0 shared inst, 0 shared DOI |
| ☐ | `researcher:srzenti_k_2020` | `researcher:srzentic_k_2022` | Srzentic, K. | 6 | 0 | — | exact normalized-name key 'srzentick'; 6 shared co-authors, 0 shared inst, 0 shared DOI |
| ☐ | `researcher:rodr_guez_fortea_a_2019` | `researcher:rodriguez_fortea_a_2018` | Rodriguez-Fortea, A. | 6 | 0 | — | exact normalized-name key 'rodriguezforteaa'; 6 shared co-authors, 0 shared inst, 0 shared DOI |
| ☐ | `researcher:chac_n_pati_o_m_2022` | `researcher:chacon_patino_m_2025` | Chacon Patino, M.L. | 5 | 0 | — | exact normalized-name key 'chaconpatinoml'; 5 shared co-authors, 0 shared inst, 0 shared DOI |
| ☐ | `researcher:bouyssi_re_b_2018` | `researcher:bouyssiere_b_2025` | Bouyssiere, B. | 5 | 0 | — | exact normalized-name key 'bouyssiereb'; 5 shared co-authors, 0 shared inst, 0 shared DOI |
| ☐ | `researcher:peru_k_m_x_2012` | `researcher:peru_k_2024` | Peru, K.M. | 5 | 0 | — | exact normalized-name key 'perukm'; 5 shared co-authors, 0 shared inst, 0 shared DOI |
| ☐ | `researcher:w_gberg_t_2008` | `researcher:wagberg_t_2005` | Wagberg, T. | 5 | 0 | — | exact normalized-name key 'wagbergt'; 5 shared co-authors, 0 shared inst, 0 shared DOI |
| ☐ | `researcher:hedenstr_m_m_2008` | `researcher:hedenstrom_m_2005` | Hedenstrom, M. | 5 | 0 | — | exact normalized-name key 'hedenstromm'; 5 shared co-authors, 0 shared inst, 0 shared DOI |
| ☐ | `researcher:rodgers_r_p_x_2012` | `researcher:rodgers_r_2026` | Rodgers, R.P. | 4 | 0 | — | exact normalized-name key 'rodgersrp'; 4 shared co-authors, 0 shared inst, 0 shared DOI |
| ☐ | `researcher:r_ger_c_2024` | `researcher:ruger_c_2025` | Ruger, C.P. | 4 | 0 | — | exact normalized-name key 'rugercp'; 4 shared co-authors, 0 shared inst, 0 shared DOI |
| ☐ | `researcher:nystr_m_j_2006` | `researcher:nystrom_j_2006` | Nystrom, J. | 2 | 0 | — | exact normalized-name key 'nystromj'; 2 shared co-authors, 0 shared inst, 0 shared DOI |
| ☐ | `researcher:sch_fer_m_2009` | `researcher:schafer_m_2004` | Schafer, M. | 1 | 0 | — | exact normalized-name key 'schaferm'; 1 shared co-authors, 0 shared inst, 0 shared DOI |

## Per-pair detail (co-author identifiers backing each merge)

### `researcher:barr_re_mangote_c_2025` → `researcher:barrere_mangote_c_2024`
- **Reconstructed name:** Barrère-Mangote, C. (mangled) → Barrere-Mangote, C. (canonical)
- **Mechanism:** A_diacritic_collapse
- **Shared co-authors (14):** `researcher:giusti_p_2026`, `researcher:rodgers_r_2026`, `researcher:chacon_patino_m_2025`, `researcher:ruiz_w_2025`, `researcher:gascon_g_2025`, `researcher:ruger_c_2025`, `researcher:dayton_d_2025`, `researcher:mase_c_2025`, `researcher:afonso_c_2025`, `researcher:bouyssiere_b_2025`, `researcher:moulian_r_2023`, `researcher:weisbrod_c_2025`, `researcher:marshall_a_2026`, `researcher:smith_d_2021`
- **Shared institution:** —  ·  **Shared DOI:** 0  ·  **ORCID:** —
- **Evidence:** exact normalized-name key 'barreremangotec'; 14 shared co-authors, 0 shared inst, 0 shared DOI

### `researcher:sch_n_m_2023` → `researcher:schon_m_2024`
- **Reconstructed name:** Schön, M. (mangled) → Schon, M. (canonical)
- **Mechanism:** A_diacritic_collapse
- **Shared co-authors (9):** `researcher:spencer_r_2026`, `researcher:mckenna_a_2026`, `researcher:kellerman_a_2025`, `researcher:holt_a_2025`, `researcher:hood_e_2025`, `researcher:battin_t_2025`, `researcher:peter_h_2025`, `researcher:styllas_m_2024`, `researcher:tolosano_m_2024`
- **Shared institution:** —  ·  **Shared DOI:** 0  ·  **ORCID:** —
- **Evidence:** exact normalized-name key 'schonm'; 9 shared co-authors, 0 shared inst, 0 shared DOI

### `researcher:srzenti_k_2020` → `researcher:srzentic_k_2022`
- **Reconstructed name:** Srzentić, K. (mangled) → Srzentic, K. (canonical)
- **Mechanism:** A_diacritic_collapse
- **Shared co-authors (6):** `researcher:anderson_l_2026`, `researcher:hendrickson_c_2025`, `researcher:kelleher_n_2023`, `researcher:toby_t_2022`, `researcher:seckler_h_2022`, `researcher:fornelli_l_2022`
- **Shared institution:** —  ·  **Shared DOI:** 0  ·  **ORCID:** —
- **Evidence:** exact normalized-name key 'srzentick'; 6 shared co-authors, 0 shared inst, 0 shared DOI

### `researcher:rodr_guez_fortea_a_2019` → `researcher:rodriguez_fortea_a_2018`
- **Reconstructed name:** Rodríguez‐Fortea, A. (mangled) → Rodriguez-Fortea, A. (canonical)
- **Mechanism:** A_diacritic_collapse
- **Shared co-authors (6):** `researcher:dunk_p_2019`, `researcher:echegoyen_l_2019`, `researcher:poblet_j_2019`, `researcher:marshall_a_2026`, `researcher:mulet_gas_m_2018`, `researcher:kroto_h_2015`
- **Shared institution:** —  ·  **Shared DOI:** 0  ·  **ORCID:** —
- **Evidence:** exact normalized-name key 'rodriguezforteaa'; 6 shared co-authors, 0 shared inst, 0 shared DOI

### `researcher:chac_n_pati_o_m_2022` → `researcher:chacon_patino_m_2025`
- **Reconstructed name:** Chacón-Patiño, M.L. (mangled) → Chacon Patino, M.L. (canonical)
- **Mechanism:** A_diacritic_collapse
- **Shared co-authors (5):** `researcher:rodgers_r_2026`, `researcher:gray_m_2023`, `researcher:mckenna_a_2026`, `researcher:weisbrod_c_2025`, `researcher:blakney_g_2024`
- **Shared institution:** —  ·  **Shared DOI:** 0  ·  **ORCID:** —
- **Evidence:** exact normalized-name key 'chaconpatinoml'; 5 shared co-authors, 0 shared inst, 0 shared DOI

### `researcher:bouyssi_re_b_2018` → `researcher:bouyssiere_b_2025`
- **Reconstructed name:** Bouyssière, B. (mangled) → Bouyssiere, B. (canonical)
- **Mechanism:** A_diacritic_collapse
- **Shared co-authors (5):** `researcher:marshall_a_2026`, `researcher:giusti_p_2026`, `researcher:rodgers_r_2026`, `researcher:barr_re_mangote_c_2025`, `researcher:putman_j_2020`
- **Shared institution:** —  ·  **Shared DOI:** 0  ·  **ORCID:** —
- **Evidence:** exact normalized-name key 'bouyssiereb'; 5 shared co-authors, 0 shared inst, 0 shared DOI

### `researcher:peru_k_m_x_2012` → `researcher:peru_k_2024`
- **Reconstructed name:** Peru. K.M. (mangled) → Peru, K.M. (canonical)
- **Mechanism:** middle_initial_x
- **Shared co-authors (5):** `researcher:rodgers_r_2026`, `researcher:mcmartin_d_2024`, `researcher:headley_j_2024`, `researcher:lobodin_v_2020`, `researcher:mapolelo_m_2019`
- **Shared institution:** —  ·  **Shared DOI:** 0  ·  **ORCID:** —
- **Evidence:** exact normalized-name key 'perukm'; 5 shared co-authors, 0 shared inst, 0 shared DOI

### `researcher:w_gberg_t_2008` → `researcher:wagberg_t_2005`
- **Reconstructed name:** Wågberg, T. (mangled) → Wagberg, T. (canonical)
- **Mechanism:** A_diacritic_collapse
- **Shared co-authors (5):** `researcher:marshall_a_2026`, `researcher:tsybin_y_2024`, `researcher:purcell_j_2010`, `researcher:noreus_d_2008`, `researcher:sato_t_2008`
- **Shared institution:** —  ·  **Shared DOI:** 0  ·  **ORCID:** —
- **Evidence:** exact normalized-name key 'wagbergt'; 5 shared co-authors, 0 shared inst, 0 shared DOI

### `researcher:hedenstr_m_m_2008` → `researcher:hedenstrom_m_2005`
- **Reconstructed name:** Hedenström, M. (mangled) → Hedenstrom, M. (canonical)
- **Mechanism:** A_diacritic_collapse
- **Shared co-authors (5):** `researcher:marshall_a_2026`, `researcher:tsybin_y_2024`, `researcher:purcell_j_2010`, `researcher:noreus_d_2008`, `researcher:sato_t_2008`
- **Shared institution:** —  ·  **Shared DOI:** 0  ·  **ORCID:** —
- **Evidence:** exact normalized-name key 'hedenstromm'; 5 shared co-authors, 0 shared inst, 0 shared DOI

### `researcher:rodgers_r_p_x_2012` → `researcher:rodgers_r_2026`
- **Reconstructed name:** Rodgers. R.P. (mangled) → Rodgers, R.P. (canonical)
- **Mechanism:** middle_initial_x
- **Shared co-authors (4):** `researcher:mckenna_a_2026`, `researcher:marshall_a_2026`, `researcher:podgorski_d_2025`, `researcher:nyadong_l_2019`
- **Shared institution:** —  ·  **Shared DOI:** 0  ·  **ORCID:** —
- **Evidence:** exact normalized-name key 'rodgersrp'; 4 shared co-authors, 0 shared inst, 0 shared DOI

### `researcher:r_ger_c_2024` → `researcher:ruger_c_2025`
- **Reconstructed name:** Rüger, C.P. (mangled) → Ruger, C.P. (canonical)
- **Mechanism:** A_diacritic_collapse
- **Shared co-authors (4):** `researcher:chacon_patino_m_2025`, `researcher:zimmermann_r_2025`, `researcher:neumann_a_2024`, `researcher:rodgers_r_2026`
- **Shared institution:** —  ·  **Shared DOI:** 0  ·  **ORCID:** —
- **Evidence:** exact normalized-name key 'rugercp'; 4 shared co-authors, 0 shared inst, 0 shared DOI

### `researcher:nystr_m_j_2006` → `researcher:nystrom_j_2006`
- **Reconstructed name:** Nyström, J. (mangled) → Nystrom, J. (canonical)
- **Mechanism:** A_diacritic_collapse
- **Shared co-authors (2):** `researcher:carlsohn_e_2006`, `researcher:svennerholm_a_2006`
- **Shared institution:** —  ·  **Shared DOI:** 0  ·  **ORCID:** —
- **Evidence:** exact normalized-name key 'nystromj'; 2 shared co-authors, 0 shared inst, 0 shared DOI

### `researcher:sch_fer_m_2009` → `researcher:schafer_m_2004`
- **Reconstructed name:** Schäfer, M. (mangled) → Schafer, M. (canonical)
- **Mechanism:** A_diacritic_collapse
- **Shared co-authors (1):** `researcher:hendrickson_c_2025`
- **Shared institution:** —  ·  **Shared DOI:** 0  ·  **ORCID:** —
- **Evidence:** exact normalized-name key 'schaferm'; 1 shared co-authors, 0 shared inst, 0 shared DOI
