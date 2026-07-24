# Researcher equivalence — review sheet for David

**Non-destructive.** These propose `POSSIBLY_SAME_AS` edges (inferred). Nothing is merged, retired, or repointed; both nodes and both names are always kept. Tick one box per row.

- **3 `SAME_AS` edges** (PROVEN, shared author-verified ORCID) were emitted separately — NOT in this sheet (no review needed): hoeschen↔hoschen, aguilera↔chacón-patiño (surname change), salvato_vallverdu↔vallverdu.
- **25 `POSSIBLY_SAME_AS` candidates** below — mechanical artifacts the transliteration slug-fix could NOT collapse. Awaiting your sign-off before any edge is created.
- **12 pairs excluded as different people** (§2) + ~80 common-Chinese-surname confusables excluded upstream — shown so you can see the judgment was applied, not skipped.

## 1. POSSIBLY_SAME_AS candidates — decide same / different

### period-parse (Last. First → wrong family; strong co-author)

| node A | name A | node B | name B | mechanism | conf | shared co-auth | decision |
|---|---|---|---|---|---|--:|---|
| `researcher:rodgers_r` | Rodgers, R.P. | `researcher:rodgers_r_p_x` | Rodgers. R.P. | period_parse | high | 4 | ☐ same ☐ different |
| `researcher:peru_k` | Peru, K.M. | `researcher:peru_k_m_x` | Peru. K.M. | period_parse | high | 5 | ☐ same ☐ different |

### OCR / typo — distinctive surname (lev-1)

| node A | name A | node B | name B | mechanism | conf | shared co-auth | decision |
|---|---|---|---|---|---|--:|---|
| `researcher:angstrom_j` | Angstrom, J. | `researcher:anstrom_j` | Anstrom, J. | ocr_variant | high | 3 | ☐ same ☐ different |
| `researcher:arumanayagam_a` | Arumanayagam, A.S. | `researcher:asumanayagam_a` | Asumanayagam, A.S. | ocr_variant | high | 3 | ☐ same ☐ different |
| `researcher:chamot_rook_j` | Chamot-Rook, J. | `researcher:chamot_rooke_j` | Chamot-Rooke, J. | ocr_variant | high | 9 | ☐ same ☐ different |
| `researcher:colilo_y` | Colilo, Y.E. | `researcher:corilo_y` | Corilo, Y.E. | ocr_variant | high | 3 | ☐ same ☐ different |
| `researcher:dehghanizade_m` | Dehghanizade, M. | `researcher:dehghanizadeh_m` | Dehghanizadeh, M. | ocr_variant | high | 3 | ☐ same ☐ different |
| `researcher:dzeilewski_a` | Dzeilewski, A. | `researcher:dzwilewski_a` | Dzwilewski, A. | ocr_variant | high | 5 | ☐ same ☐ different |
| `researcher:nagirnov_k` | Nagirnov, K.O. | `researcher:nagornov_k` | Nagornov, K.O. | ocr_variant | high | 3 | ☐ same ☐ different |
| `researcher:standford_l` | Standford, L.A. | `researcher:stanford_l` | Stanford, L.A. | ocr_variant | high | 3 | ☐ same ☐ different |
| `researcher:tzortiziou_m` | Tzortiziou, M. | `researcher:tzortziou_m` | Tzortziou, M. | ocr_variant | high | 4 | ☐ same ☐ different |
| `researcher:jeppensen_e` | Jeppensen, E. | `researcher:jeppesen_e` | Jeppesen, E. | ocr_variant | high | 5 | ☐ same ☐ different |
| `researcher:hawkings_j` | Hawkings, J.R. | `researcher:hawkins_j` | Hawkins, J.R. | ocr_variant | medium | 2 | ☐ same ☐ different |
| `researcher:mathews_j` | Mathews, J.P. | `researcher:matthews_j` | Matthews, J.P. | ocr_variant | medium | 1 | ☐ same ☐ different |
| `researcher:rodgers_r` | Rodgers, R.P. | `researcher:rogers_r` | Rogers, R.P. | spelling_variant | medium | 5 | ☐ same ☐ different |
| `researcher:zimmerman_r` | Zimmerman, R. | `researcher:zimmermann_r` | Zimmermann, R. | spelling_variant | medium | 3 | ☐ same ☐ different |
| `researcher:meyer_baese_a` | Meyer-Baese, A. | `researcher:meyer_base_a` | Meyer-Bäse, A. | spelling_variant (ae/ä digraph, not a slug miss) | medium | 2 | ☐ same ☐ different |

### short typo

| node A | name A | node B | name B | mechanism | conf | shared co-auth | decision |
|---|---|---|---|---|---|--:|---|
| `researcher:ahif_d` | Ahif, D.R. | `researcher:ahlf_d` | Ahlf, D.R. | ocr_variant | high | 6 | ☐ same ☐ different |
| `researcher:oomens_j` | Oomens, J. | `researcher:oomes_j` | Oomes, J. | ocr_variant | high | 3 | ☐ same ☐ different |
| `researcher:sets_e` | Sets, E.G. | `researcher:stets_e` | Stets, E.G. | ocr_variant | high | 9 | ☐ same ☐ different |
| `researcher:wang_x` | Wang, X. | `researcher:wnag_x` | Wnag, X. | transposition | medium | 2 | ☐ same ☐ different |

### transposition / transliteration

| node A | name A | node B | name B | mechanism | conf | shared co-auth | decision |
|---|---|---|---|---|---|--:|---|
| `researcher:guluyz_k` | Guluyz, K. | `researcher:gulyuz_k` | Gulyuz, K. | transposition | high | 2 | ☐ same ☐ different |
| `researcher:schulga_y` | Schulga, Y.M. | `researcher:shul_ga_y` | Shul'ga, Y.M. | transliteration | medium | 1 | ☐ same ☐ different |
| `researcher:pa_sa_toli_l` | Pa-sa-Toli, L. | `researcher:pasa_tolic_l` | Pasa-Tolic, L. | transliteration (Paša-Tolić) | high | 5 | ☐ same ☐ different |

### suffix

| node A | name A | node B | name B | mechanism | conf | shared co-auth | decision |
|---|---|---|---|---|---|--:|---|
| `researcher:avery_g` | Avery, G.B. | `researcher:avery_jr_g` | Avery Jr., G.B. | suffix_Jr | high | 2 | ☐ same ☐ different |

## 2. Excluded as different people (NOT candidates — for your audit)

| node A | name A | node B | name B | why excluded |
|---|---|---|---|---|
| `researcher:vladimirov_g` | Vladimirov, G. | `researcher:vladimirova_g` | Vladimirova, G. | Slavic masculine/feminine surname → different people |
| `researcher:angstrom_j` | Angstrom, J. | `researcher:nystrom_j` | Nystrom, J. | Ångström ≠ Nyström — different surnames |
| `researcher:auman_j` | Auman, J. | `researcher:lanman_j` | Lanman, J. | distinct surnames |
| `researcher:auman_j` | Auman, J. | `researcher:putman_j` | Putman, J. | distinct surnames |
| `researcher:bailey_j` | Bailey, J. | `researcher:walley_j` | Walley, J. | distinct surnames |
| `researcher:baker_a` | Baker, A. | `researcher:parker_a` | Parker, A. | distinct surnames |
| `researcher:curry_d` | Curry, D. | `researcher:murray_d` | Murray, D. | distinct surnames |
| `researcher:gharibi_h` | Gharibi, H. | `researcher:hariri_h` | Hariri, H. | distinct surnames |
| `researcher:jorner_k` | Jorner, K. | `researcher:koerner_k` | Koerner, K. | distinct surnames |
| `researcher:kieber_r` | Kieber, R.J. | `researcher:weber_r` | Weber, R.J. | distinct surnames |
| `researcher:tigges_m` | Tigges, M. | `researcher:wigger_m` | Wigger, M. | distinct surnames |
| `researcher:wagner_d` | Wagner, D. | `researcher:walker_d` | Walker, D. | distinct surnames |

_Also excluded upstream: ~80 short common-Chinese-surname pairs one edit apart (wang/yang, chen/shen, zhang/zheng, …) — different people, never same-person candidates._

