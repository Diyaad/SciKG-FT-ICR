# Instrument — PDF transform review (378-paper batch, intra-batch dedup)
**STATUS — APPLIED & LOADED, then partly SUPERSEDED (2026-07-21).** This was a DRY RUN when
generated (original banner: *"No entity output written. 03 not run. No git."*). Its decisions
were applied and the raw-form Instrument nodes are live in the graph (they were the PDF-sourced
Instruments in the original load). Option A raw-form nodes; 03 canonicalizes via CV. David's
rulings applied. Inherits failure guard + exact→fuzzy resolver (FUZZY PROPOSES, HUMAN DISPOSES).

**SUPERSEDED 2026-07-21** by a later dedup pass in `scripts/03_normalize.py` (David re-ruled the
two items this doc had left to him; all now RESOLVED and loaded — graph went 469 → **443**
Instruments):
- **FT-ICR generics — ruling 1 REVERSED.** This doc minted the 13 bare-generic FT-ICR spellings
  as SEPARATE class-name nodes (§ GENERICS SPLIT). David re-ruled they should **collapse**: the
  12 variants now retire into one **`instrument:raw:ft_icr_ms`** canonicalized to **MS:1003948**.
  (Magnet-strength, hi-res/ultra-hi-res, vendor, ionization-prefixed, and custom-built FT-ICR
  nodes stay separate — unchanged.)
- **Velos conflation SPLIT.** This doc's INTRA-BATCH COLLAPSE (row `ltq_velos_ion_trap_mass_spectrometer`)
  merged hybrid *LTQ Orbitrap Velos* with plain *LTQ Velos / Velos Pro*. David ruled these are
  **different instruments**: split by per-edge reassignment into **`ltq_orbitrap_velos`**
  (MS:1001742, hybrid), **`velos_pro_linear_ion_trap`** (MS:1003495), and **`ltq_velos`** (null,
  no CV accession). `ltqorbitrap` (plain LTQ Orbitrap) kept separate.
- **Safe OCR/spacing typo merges applied.** Variants this doc's signature-collapse mechanically
  missed (e.g. `custombuilt_…`↔`custom_built_…`, the `shimadzu_toc_l_cph` spacing variants,
  `pegasus_gchrt_4d`↔`pegasus_gc_hrt_4d`) were merged; one hi-res FT-ICR descriptor spelled two
  broken ways was repaired into a clean node. See KI-14 and `docs/KNOWN_ISSUES.md`.

## HOW DECISIONS WERE HANDLED (historical — decisions below are APPLIED, with the 2026-07-21 revisions above)
1. **INTRA-BATCH COLLAPSE** / **CONFIRM-RESOLVE** / **PROCESSING-vs-ANALYTICAL** were the decision sections.
2. AUTO-MINTED / AUTO-REJECTED / MISROUTES / SKIPPED-PERIPHERALS reflected standing rulings.
3. Applied via `apply instrument_review.md`; later revised per the SUPERSEDED note above.

## COUNTS
- Three-way: **354 with a value / 23 genuine negatives / 1 failed** (excluded 10.1016/j.tube.2017.08.011, ran_but_empty).
- Distinct strings: 747. OCR fired: {'modified': 4, 'Scientific': 41, '21 Tesla': 16, 'FT-ICR': 2, 'time-of-flight': 1}.
- **Mint nodes: 509 pre-collapse → intra-batch collapse removes 45 → 464 POST.** (MS 164 · NON-MS 292 · NMR 8)
- Resolve→existing 7: 78 (all fuzzy). Reject: settings 2, software 3, processing 10, vendor 1, contentless-generics 11. Misroute 3. Skip-peripheral 20.
- NOTE vs v1 (349): the mint base is now 509 because your rulings MINT the 155 ambiguous + 13 class-naming generics (v1 held these in review). The collapse fix removed 45 true duplicates.

## GENERICS FACT-CHECK (why generics are safe to mint / not needed)
`03` matches by EXACT normalized-key dict lookup (`vocab.get(norm_match_key(raw))`, 03_normalize.py:399)
over the Instruments table ONLY; the generic `FT-ICR MS` (MS:1000079) sits in the Methods table (not read).
Every 21T alias carries the `21 t` token, so a bare `FT-ICR` can NEVER collapse into a specific magnet —
it stays unmapped/null. Class-naming generics are minted (honest label); contentless ones are rejected (noise).

## INTRA-BATCH COLLAPSE — proposed (FUZZY PROPOSES, HUMAN DISPOSES)  [30 groups + 1 NMR]
Exact distinctive-signature match (class/vendor-boilerplate/version tokens stripped). No chaining; model
numbers are distinguishing (Agilent 8900 ≠ 7900). `confirm` = merge the member slugs into one node.
| → canonical node | signature | member strings | DOI(s) | DECISION |
|---|---|---|---|---|
| `instrument:raw:9_4_ft_icr_mass_spectrometer` | ['9.4'] | (+) APPI 9.4 T FT-ICR MS · 9.4 FT-ICR mass spectrometer · 9.4 T FT-ICR · 9.4 T FT-ICR MS · 9.4 T FT-ICR Mass Spectrometer · 9.4 T FT-ICR mass spectrometer | 10.1002/2017JG004343; 10.1002/aic.15147; 10.1002/lom3.10558 (+58) | **confirm** |
| `instrument:raw:ltq_velos_ion_trap_mass_spectrometer` | ['ltq', 'velos'] | LTQ Orbitrap Velos · LTQ Orbitrap Velos (Thermo Fisher Scientific) · LTQ Velos · LTQ Velos ion trap mass spectrometer · LTQ-Velos · Velos LTQ-Orbitrap Mass Spectrometer | 10.1002/jms.3345; 10.1002/pmic.201300438; 10.1016/j.chroma.2016.10.005 (+3) | **confirm** |
| `instrument:raw:ultrahigh_resolution_ft_icr_mass_spectrometer` | ['ultrahigh'] | Ultrahigh Resolution Mass Spectrometer · Ultrahigh-Resolution FT-ICR Mass Spectrometer · Ultrahigh-Resolution Mass Spectrometer · home-built ultrahigh resolution FT-ICR MS · ultrahigh resolution mass spectrometer · ultrahigh-resolution mass spectrometer | 10.1007/s00027-017-0540-5; 10.1016/j.watres.2019.115048; 10.1021/acs.energyfuels.0c01564 (+3) | **confirm** |
| `instrument:raw:shimadzu_toc_total_organic_carbon_analyzer` | ['shimadzu'] | Shimadzu TOC total organic carbon analyzer · Shimadzu Total Organic Carbon Analyzer · Shimadzu Total Organic Carbon analyzer · Shimadzu total organic carbon (TOC) analyzer · TOC analyzer (Shimadzu) · TOC-analyzer (Shimadzu) | 10.1002/etc.5742; 10.1016/j.gca.2016.05.015; 10.1016/j.isci.2022.104916 (+3) | **confirm** |
| `instrument:raw:illumina_miseq_sequencing_system` | ['illumina', 'miseq'] | Illumina MiSeq · Illumina MiSeq Platform · Illumina MiSeq Sequencer · Illumina MiSeq System · Illumina MiSeq sequencing system | 10.1007/s10533-018-00534-5; 10.1007/s11783-022-1567-y; 10.1016/j.ecolind.2024.111884 (+5) | **confirm** |
| `instrument:raw:modified_ltq_fourier_transform_ion_cyclotron_resonance_` | ['ltq'] | LTQ · LTQ linear ion trap · LTQ mass spectrometer · modified LTQ Fourier transform ion cyclotron resonance (FT-ICR) mass spectrometer | 10.1002/jms.3345; 10.1002/rcm.4655; 10.1007/s13361-018-1897-y (+2) | **confirm** |
| `instrument:raw:fourier_transform_ion_cyclotron_resonance_mass_spectrom` | ['icrms'] | ESI FT-ICRMS · FT-ICRMS · Fourier-transform ion cyclotron resonance Mass Spectrometer (FT-ICRMS) · custom-built FT-ICRMS | 10.1002/pca.70001; 10.1021/acs.energyfuels.1c02107; 10.1021/acs.est.8b01788 (+1) | **confirm** |
| `instrument:raw:velos_pro_linear_ion_trap` | ['pro', 'velos'] | Orbitrap Velos Pro · Velos Pro · Velos Pro linear ion trap · custom-built Velos Pro | 10.1007/s13361-015-1182-2; 10.1007/s13361-017-1602-6; 10.1007/s13361-019-02290-8 (+7) | **confirm** |
| `instrument:raw:element_xr_inductively_coupled_plasma_mass_spectrometer` | ['element'] | Element XR · Element XR Inductively Coupled Plasma Mass Spectrometer · ICP MS (Thermo Scientific Element XR) · Thermo Scientific Element XR | 10.1021/acs.energyfuels.0c03349; 10.1021/acs.energyfuels.1c02173; 10.1021/acs.energyfuels.8b02788 (+1) | **confirm** |
| `instrument:raw:horiba_scientific_aqualog_spectrofluorometer` | ['aqualog', 'horiba'] | Horiba Aqualog · Horiba Aqualog fluorometer · Horiba Scientific Aqualog · Horiba Scientific Aqualog spectrofluorometer | 10.1002/lno.11417; 10.1007/s00027-017-0540-5; 10.1007/s10533-019-00619-9 (+12) | **confirm** |
| `instrument:raw:shimadzu_toc_vcph_analyzer` | ['shimadzu', 'vcph'] | Shimadzu TOC-VCPH · Shimadzu TOC-VCPH analyzer · Shimadzu TOC-Vcph | 10.1002/2017JG004343; 10.1002/lol2.10388; 10.1021/acs.est.1c03592 (+1) | **confirm** |
| `instrument:raw:shimadzu_toc_lcph_analyzer` | ['lcph', 'shimadzu'] | Shimadzu TOC -LCPH analyzer · Shimadzu TOC-LCPH · Shimadzu TOC-LCPH analyzer | 10.1002/lno.11857; 10.1021/acs.est.7b01278; 10.1029/2017JG004311 (+5) | **confirm** |
| `instrument:raw:shimadzu_toc_l_total_organic_carbon_analyzer` | ['l', 'shimadzu'] | Shimadzu TOC-L · Shimadzu TOC-L total organic carbon analyzer · TOC -L series (Shimadzu) | 10.1002/lno.12436; 10.1016/j.watres.2023.120808; 10.1021/acs.energyfuels.1c02373 (+4) | **confirm** |
| `instrument:raw:shimadzu_high_temperature_catalytic_oxidation_total_org` | ['catalytic', 'cph', 'l', 'oxidation', 'shimadzu', 'temperature'] | Shimadzu TOC-L CPH high temperature catalytic oxidation total organic analyzer · Shimadzu TOC-L CPH high temperature catalytic oxidation total organic carbon analyzer · Shimadzu high-temperature catalytic oxidation total organic carbon analyzer (TOC-L CPH) | 10.1016/j.orggeochem.2024.104846; 10.1029/2021JG006578; 10.1029/2022JG007073 | **confirm** |
| `instrument:raw:keck_carbon_cycle_accelerator_mass_spectrometer` | ['accelerator', 'cycle', 'keck'] | Keck Carbon Cycle Accelerator Mass Spectrometer · Keck Carbon Cycle Accelerator Mass Spectrometry | 10.1002/2017JG004343; 10.5194/bg-15-6637-2018 | **confirm** |
| `instrument:raw:custombuilt_hybrid_linear_ion_trap_ft_icr_ms` | ['custombuilt'] | custombuilt FT-ICR mass spectrometer · custombuilt hybrid linear ion trap/FT-ICR MS | 10.1007/s10533-015-0103-6; 10.1029/2024GB008212 | **confirm** |
| `instrument:raw:orbitrap_fusion` | ['fusion'] | Orbitrap Fusion · Thermo Fusion | 10.1007/s13361-015-1182-2; 10.1016/j.biortech.2020.123454; 10.3389/fmars.2016.00243 | **confirm** |
| `instrument:raw:hybrid_quadrupole_ft_icr_instrument` | ['solarixr'] | SolariXR · hybrid quadrupole FT-ICR instrument (SolariXR, Bruker Daltonics) | 10.1021/acs.energyfuels.0c02525; 10.3390/pr8111472 | **confirm** |
| `instrument:raw:bruker_solarix_ft_icr_ms` | ['solarix'] | Bruker SolariX FT -ICR MS · FT-ICR Solarix XR | 10.1021/acs.energyfuels.2c00840; 10.1021/acsestwater.4c00832 | **confirm** |
| `instrument:raw:apex_ii_ultra_ft_ms` | ['apex'] | Apex II Ultra FT-MS · Bruker Apex Ultra | 10.1021/jasms.4c00120; 10.1029/2018JG004743 | **confirm** |
| `instrument:raw:thermo_delta_v_isotope_ratio_mass_spectrometer` | ['delta', 'v'] | Delta V IRMS · Thermo Delta V Isotope Ratio Mass Spectrometer | 10.1029/2017JG004311; 10.1029/2024GB008359; 10.1111/gcb.14889 | **confirm** |
| `instrument:raw:agilent_model_8453_photodiode_array_spectrophotometer` | ['8453', 'agilent'] | Agilent 8453 · Agilent Model 8453 photodiode array spectrophotometer | 10.1002/2016JG003431; 10.1029/2017JG004327; 10.1029/2018JG004982 | **confirm** |
| `instrument:raw:shimadzu_toc_l_cph_analyzer` | ['cph', 'l', 'shimadzu'] | Shimadzu TOC-L CPH · Shimadzu TOC-L CPH analyzer | 10.1002/2017JG004337; 10.1007/s10533-019-00619-9; 10.1007/s10533-021-00852-1 (+11) | **confirm** |
| `instrument:raw:dual_beam_shimadzu_uv_1800_spectrophotometer` | ['1800', 'shimadzu'] | Shimadzu UV-1800 spectrophotometer · dual-beam Shimadzu UV-1800 spectrophotometer | 10.1002/lno.11385; 10.1029/2020GB006871; 10.5194/bg-15-6637-2018 | **confirm** |
| `instrument:raw:agilent_7890_a_gas_chromatograph` | ['7890', 'agilent'] | Agilent 7890 · Agilent 7890 A Gas Chromatograph | 10.1016/j.jhazmat.2021.127598; 10.1021/acs.est.7b05346 | **confirm** |
| `instrument:raw:hitachi_f_7000_spectrofluorometer` | ['7000', 'f', 'hitachi'] | Hitachi F-7000 · Hitachi F-7000 spectrofluorometer | 10.1002/lno.11385; 10.1021/acsestwater.4c00832 | **confirm** |
| `instrument:raw:bruker_biospin_avance_iii_400_mhz_wb` | ['400', 'avance'] | Bruker AVANCE 400 MHz · Bruker BioSpin Avance III 400 MHz WB | 10.1002/2017JG004343; 10.1021/acs.energyfuels.4c01959 | **confirm** |
| `instrument:raw:thermo_fisher_ultimate_3000` | ['3000', 'ultimate'] | Thermo Fisher UltiMate 3000 · Thermo Ultimate 3000 system | 10.1002/pmic.201300438; 10.1029/2024GB008359 | **confirm** |
| `instrument:raw:thermo_flash_2000` | ['2000', 'flash'] | FLASH 2000 · Thermo FLASH 2000 | 10.1021/acs.energyfuels.3c02599; 10.1089/ast.2022.0021 | **confirm** |
| `instrument:raw:dionex_ultimate_3000_lc_system` | ['3000', 'dionex', 'ultimate'] | Dionex Ultimate 3000 LC system · UltiMate 3000 Dionex | 10.1021/acs.energyfuels.4c01959; 10.1038/s43247-024-01965-9 | **confirm** |
| `instrument:raw:600mhz_14_1t_solid_state_nmr` | NMR (ruling 3) | 'a 600 MHz/14.1 T solid-state NMR spectrometer' · '1 T solid-state NMR spectrometer' · '600 MHz/14' | 10.1021/acs.analchem.1c03058 | **confirm (same paper, same instrument)** |

## GENERICS SPLIT (ruling 1)  — MINT class-naming [13] / REJECT contentless [11]
| String | fate |
|---|---|
| FT-ICR | **mint** (class name, ontology PSI-MS) |
| FT-ICR MS | **mint** (class name, ontology PSI-MS) |
| FT-ICR Mass Spectrometer | **mint** (class name, ontology PSI-MS) |
| FT-ICR mass spectrometer | **mint** (class name, ontology PSI-MS) |
| FTICR | **mint** (class name, ontology PSI-MS) |
| FTICR MS | **mint** (class name, ontology PSI-MS) |
| Fourier Transform Ion Cyclotron Resonance Mass Spectrometry | **mint** (class name, ontology PSI-MS) |
| Fourier transform ion cyclotron resonance | **mint** (class name, ontology PSI-MS) |
| Orbitrap | **mint** (class name, ontology PSI-MS) |
| custom-built FT-ICR MS | **mint** (class name, ontology PSI-MS) |
| custom-built FT-ICR mass spectrometer | **mint** (class name, ontology PSI-MS) |
| high-resolution FT-ICR mass spectrometer | **mint** (class name, ontology PSI-MS) |
| orbitrap | **mint** (class name, ontology PSI-MS) |
| 1-T magnet spectrometer | **reject** (contentless — null props, meaningless name) |
| 4 T ESI-FT mass spectrometer | **reject** (contentless — null props, meaningless name) |
| 9.4 T instrument | **reject** (contentless — null props, meaningless name) |
| 9.4 tesla | **reject** (contentless — null props, meaningless name) |
| 9.4-T instrument | **reject** (contentless — null props, meaningless name) |
| High Resolution Mass Spectrometer | **reject** (contentless — null props, meaningless name) |
| High-Resolution Mass Spectrometer | **reject** (contentless — null props, meaningless name) |
| a 9.4-T instrument | **reject** (contentless — null props, meaningless name) |
| custom-built mass spectrometer | **reject** (contentless — null props, meaningless name) |
| high-resolution mass spectrometer | **reject** (contentless — null props, meaningless name) |
| mass spectrometer | **reject** (contentless — null props, meaningless name) |

## AMBIGUOUS → MINTED as raw label-only (ruling 2)  [155]
Not reviewed per-string (none are in the CV; PSI-MS vs null → identical 03 output). MS-marker split:
**2 → ontology PSI-MS, 153 → null.** Verbatim string preserved in name_raw.
CV-term exact-hits among the 155 ambiguous (where your ontology ruling could change 03 output): **0** — none.

## PROCESSING-vs-ANALYTICAL — your call  [4]
| String | note | DOI(s) | DECISION |
|---|---|---|---|
| C1000 Touch Thermocycler | processing-vs-analytical deferred (thermocycler/sensor/DGGE) | 10.1007/s12010-019-03055-5 | **review** |
| Eppendorf Mastercycler pro S | processing-vs-analytical deferred (thermocycler/sensor/DGGE) | 10.1007/s10533-018-00534-5 | **review** |
| StepOnePlusTM thermocycler | processing-vs-analytical deferred (thermocycler/sensor/DGGE) | 10.1186/s40538-025-00789-9 | **review** |
| denaturing gradient gel electrophoresis (DGGE) gel | processing-vs-analytical deferred (thermocycler/sensor/DGGE) | 10.1038/ismej.2015.129 | **review** |

## AUTO-MINTED — MS (PSI-MS)  [164 nodes]
| node | ontology_source | #strings | example string(s) | DOI(s) |
|---|---|---|---|---|
| `instrument:raw:9_4_ft_icr_mass_spectrometer` | PSI-MS | 38 | (+) APPI 9.4 T FT-ICR MS · 9.4 FT-ICR mass spectrometer | 10.1002/2017JG004343; 10.1002/aic.15147; 10.1002/lom3.10558 (+58) |
| `instrument:raw:fourier_transform_ion_cyclotron_resonance_mass_spectrom` | PSI-MS | 13 | ESI FT-ICRMS · FT-ICRMS | 10.1002/hlca.201900046; 10.1002/lno.11857; 10.1002/pca.70001 (+16) |
| `instrument:raw:9_4t_ft_icr` | PSI-MS | 9 | 9.4-T ESI-FT-ICRMS · SolariX 9.4 T FT-ICR MS | 10.1021/ac0108461; 10.1021/acs.energyfuels.7b01803; 10.1021/acs.energyfuels.9b00626 (+6) |
| `instrument:raw:14_5t_ft_icr` | PSI-MS | 7 | 14.5 T FT-ICR MS · 14.5T FT-ICR mass spectrometer | 10.1002/rcm.7783; 10.1021/acs.biochem.8b00766; 10.1021/acs.energyfuels.6b01514 (+4) |
| `instrument:raw:4t_ft_icr` | PSI-MS | 7 | 4 T FT-ICR · 4 T FT-ICR MS | 10.1002/2016JG003431; 10.1002/lno.11857; 10.1016/j.orggeochem.2023.104667 (+7) |
| `instrument:raw:ltq_velos_ion_trap_mass_spectrometer` | PSI-MS | 6 | LTQ Orbitrap Velos · LTQ Orbitrap Velos (Thermo Fisher Scientific) | 10.1002/jms.3345; 10.1002/pmic.201300438; 10.1016/j.chroma.2016.10.005 (+3) |
| `instrument:raw:ultrahigh_resolution_ft_icr_mass_spectrometer` | PSI-MS | 6 | Ultrahigh Resolution Mass Spectrometer · Ultrahigh-Resolution FT-ICR Mass Spectrometer | 10.1007/s00027-017-0540-5; 10.1016/j.watres.2019.115048; 10.1021/acs.energyfuels.0c01564 (+3) |
| `instrument:raw:element_xr_inductively_coupled_plasma_mass_spectrometer` | PSI-MS | 4 | Element XR · Element XR Inductively Coupled Plasma Mass Spectrometer | 10.1021/acs.energyfuels.0c03349; 10.1021/acs.energyfuels.1c02173; 10.1021/acs.energyfuels.8b02788 (+1) |
| `instrument:raw:modified_ltq_fourier_transform_ion_cyclotron_resonance_` | PSI-MS | 4 | LTQ · LTQ linear ion trap | 10.1002/jms.3345; 10.1002/rcm.4655; 10.1007/s13361-018-1897-y (+2) |
| `instrument:raw:velos_pro_linear_ion_trap` | PSI-MS | 4 | Orbitrap Velos Pro · Velos Pro | 10.1007/s13361-015-1182-2; 10.1007/s13361-017-1602-6; 10.1007/s13361-019-02290-8 (+7) |
| `instrument:raw:7t_ft_icr` | PSI-MS | 3 | 7 T APEX Qe FT-ICR mass spectrometer · 7 T FTICR mass spectrometer (Bruker Corp., Billerica, MA) | 10.1021/acs.analchem.3c00393; 10.1021/acs.energyfuels.2c04274; 10.1021/jasms.4c00232 |
| `instrument:raw:custom_built_hybrid_linear_ion_trap_ft_icr_mass_spectro` | PSI-MS | 3 | custom-built hybrid linear ion trap FT ICR mass spectrometer · custom-built hybrid linear ion trap FT-ICR mass spectrometer | 10.1002/etc.5742; 10.1016/j.chemosphere.2024.142042; 10.1016/j.jenvman.2023.119719 (+18) |
| `instrument:raw:esi_ft_icr_ms` | PSI-MS | 3 | ESI FT-ICR MS · ESI-FT-ICR MS | 10.1002/pca.70001; 10.1021/acs.energyfuels.1c01837; 10.1029/2018JG004470 |
| `instrument:raw:ft_icr_ms` | PSI-MS | 3 | FT ICR-MS · FT-ICR MS | 10.1002/lno.11417; 10.1002/lom3.10558; 10.1002/mas.21666 (+82) |
| `instrument:raw:maldi_tof_ms` | PSI-MS | 3 | MALDI ToF-MS · MALDI-TOF MS | 10.1016/j.bmcl.2017.04.070; 10.1021/acs.energyfuels.1c02002; 10.1021/acs.jproteome.0c00303 |
| `instrument:raw:orbitrap_eclipse_tribrid` | PSI-MS | 3 | Orbitrap Eclipse Tribrid · Orbitrap Eclipse Tribrid (Thermo Fisher Scientific) | 10.1021/acs.analchem.5c06165; 10.1021/acs.energyfuels.4c05674; 10.1515/cclm-2020-1072 |
| `instrument:raw:5t_ft_icr` | PSI-MS | 2 | 5 T FT-ICR mass spectrometer · 5 T Fourier transform ion cyclotron resonance mass spectrometer | 10.1021/acs.biochem.8b00733; 10.1371/journal.pone.0181869 |
| `instrument:raw:apex_ii_ultra_ft_ms` | PSI-MS | 2 | Apex II Ultra FT-MS · Bruker Apex Ultra | 10.1021/jasms.4c00120; 10.1029/2018JG004743 |
| `instrument:raw:appi_ft_icr_ms` | PSI-MS | 2 | (+) APPI FT-ICR MS · APPI FT-ICR MS | 10.1021/acs.energyfuels.1c02002; 10.1021/acs.energyfuels.1c02107 |
| `instrument:raw:bruker_solarix_ft_icr_ms` | PSI-MS | 2 | Bruker SolariX FT -ICR MS · FT-ICR Solarix XR | 10.1021/acs.energyfuels.2c00840; 10.1021/acsestwater.4c00832 |
| `instrument:raw:custom_built_fourier_transform_ion_cyclotron_resonance_` | PSI-MS | 2 | custom-built Fourier transform ion cyclotron resonance (FT-ICR) mass spectrometer · custom-built Fourier transform ion cyclotron resonance mass spectrometer | 10.1016/j.gca.2016.05.015; 10.1016/j.jhazmat.2021.127598; 10.1021/acs.energyfuels.9b04408 (+3) |
| `instrument:raw:custom_built_ft_icr_ms` | PSI-MS | 2 | custom-built FT-ICR MS · custom-built FT-ICR-MS | 10.1002/lno.11385; 10.1007/s10533-022-00906-y; 10.1016/j.chemosphere.2019.125399 (+1) |
| `instrument:raw:custombuilt_hybrid_linear_ion_trap_ft_icr_ms` | PSI-MS | 2 | custombuilt FT-ICR mass spectrometer · custombuilt hybrid linear ion trap/FT-ICR MS | 10.1007/s10533-015-0103-6; 10.1029/2024GB008212 |
| `instrument:raw:ft_icr_mass_spectrometer` | PSI-MS | 2 | FT-ICR Mass Spectrometer · FT-ICR mass spectrometer | 10.1002/pmic.201700442; 10.1007/s13361-015-1182-2; 10.1016/j.ijms.2015.12.005 (+6) |
| `instrument:raw:fticr_ms` | PSI-MS | 2 | FTICR MS · FTICR-MS | 10.1002/lno.11716; 10.1016/j.jece.2021.106255; 10.1016/j.watres.2017.11.040 (+8) |
| `instrument:raw:hybrid_quadrupole_ft_icr_instrument` | PSI-MS | 2 | SolariXR · hybrid quadrupole FT-ICR instrument (SolariXR, Bruker Daltonics) | 10.1021/acs.energyfuels.0c02525; 10.3390/pr8111472 |
| `instrument:raw:keck_carbon_cycle_accelerator_mass_spectrometry` | PSI-MS | 2 | Keck Carbon Cycle Accelerator Mass Spectrometer · Keck Carbon Cycle Accelerator Mass Spectrometry | 10.1002/2017JG004343; 10.5194/bg-15-6637-2018 |
| `instrument:raw:lc_ft_icr_ms` | PSI-MS | 2 | LC FT-ICR MS · LC-FT-ICR MS | 10.1016/j.orggeochem.2024.104880; 10.1038/s41598-021-89025-6 |
| `instrument:raw:orbitrap` | PSI-MS | 2 | Orbitrap · orbitrap | 10.1021/acs.est.0c01997; 10.1021/es302468q; 10.1038/s43247-024-01965-9 (+2) |
| `instrument:raw:orbitrap_fusion` | PSI-MS | 2 | Orbitrap Fusion · Thermo Fusion | 10.1007/s13361-015-1182-2; 10.1016/j.biortech.2020.123454; 10.3389/fmars.2016.00243 |
| `instrument:raw:orbitrap_ms` | PSI-MS | 2 | Orbitrap MS · Orbitrap-MS | 10.1021/acs.energyfuels.3c04994; 10.1021/es302468q; 10.21037/atm.2019.12.67 |
| `instrument:raw:thermo_delta_v_isotope_ratio_mass_spectrometer` | PSI-MS | 2 | Delta V IRMS · Thermo Delta V Isotope Ratio Mass Spectrometer | 10.1029/2017JG004311; 10.1029/2024GB008359; 10.1111/gcb.14889 |
| `instrument:raw:12_0t_ft_icr` | PSI-MS | 1 | 12.0 tesla hybrid quadrupole FT-ICR, FT-MS mass spectrometer (Bruker Daltonics) | 10.1002/pmic.201300438 |
| `instrument:raw:12t_ft_icr` | PSI-MS | 1 | 12 T ApexQe hybrid Fourier transform-ion cyclotron resonance (FT-ICR) mass spectrometer | 10.1002/pmic.201300438 |
| `instrument:raw:3t_ft_icr` | PSI-MS | 1 | commercial 3 T FT-ICR | 10.1002/mas.21666 |
| `instrument:raw:5973_gc_ms` | PSI-MS | 1 | 5973 GC/MS | 10.1021/acs.analchem.6b01652 |
| `instrument:raw:5_6t_ft_icr` | PSI-MS | 1 | 5.6-T FT-ICR | 10.1021/ar020177t |
| `instrument:raw:7_t_bruker_solarix` | PSI-MS | 1 | 7 T Bruker SolariX | 10.1016/j.mcpro.2024.100814; 10.1021/acs.analchem.7b01461 |
| `instrument:raw:accelerator_mass_spectrometry_facility_at_the_national_` | PSI-MS | 1 | accelerator mass spectrometry (AMS) facility at the National Ocean Sciences accelerator mass spectrometer (NOSAMS) | 10.1038/s41467-023-41900-8 |
| `instrument:raw:acustom_built_ft_icr` | PSI-MS | 1 | Acustom-built FT-ICR | 10.3390/life11030234 |
| `instrument:raw:agilent_5973_mass_spectrometer` | PSI-MS | 1 | Agilent 5973 mass spectrometer | 10.1021/acs.energyfuels.7b01803 |
| `instrument:raw:agilent_7700_series_icp_ms` | PSI-MS | 1 | Agilent 7700 Series ICP MS | 10.1021/acs.energyfuels.0c02525 |
| `instrument:raw:agilent_triple_quadrupole_ms_system` | PSI-MS | 1 | Agilent triple quadrupole MS system | 10.1021/acs.energyfuels.2c00656 |
| `instrument:raw:bruker_12_t_solarix_xr_ftms` | PSI-MS | 1 | Bruker 12 T solariX XR FTMS | 10.1002/pmic.201300438 |
| `instrument:raw:bruker_daltonics_10_tesla_apex_qe` | PSI-MS | 1 | Bruker Daltonics 10 Tesla Apex Qe | 10.1039/d4em00023d |
| `instrument:raw:bruker_microflex_lrf` | PSI-MS | 1 | Bruker Microflex LRF | 10.1002/hlca.201900046 |
| `instrument:raw:bruker_ultraflextreme_maldi_tof` | PSI-MS | 1 | Bruker Ultraflextreme MALDI-TOF | 10.1021/acs.energyfuels.3c05200 |
| `instrument:raw:chip_tof_mass_spectrometer` | PSI-MS | 1 | Chip-TOF mass spectrometer | 10.1021/acs.analchem.9b04855 |
| `instrument:raw:custom_built_ft_icr_mass_spectrometer` | PSI-MS | 1 | custom-built FT-ICR mass spectrometer | 10.1002/2017JG004337; 10.1016/j.isci.2022.104916; 10.1016/j.orggeochem.2016.11.004 (+18) |
| `instrument:raw:custom_built_hybrid_linear_ion_trap_fourier_transform_i` | PSI-MS | 1 | custom-built hybrid linear ion trap Fourier transform ion cyclotron resonance mass spectrometer | 10.1038/s43247-024-01965-9 |
| `instrument:raw:custom_built_hybrid_linear_ion_trap_ft_icr_ms` | PSI-MS | 1 | custom-built hybrid linear ion trap FT-ICR MS | 10.1016/j.orggeochem.2024.104846; 10.1016/j.watres.2023.120808; 10.1016/j.watres.2024.122130 (+4) |
| `instrument:raw:custom_built_hybrid_linear_ion_trap_ultra_high_resoluti` | PSI-MS | 1 | custom-built hybrid linear ion trap ultra-high resolution FT-ICR mass spectrometer | 10.1029/2023GB007917; 10.1029/2025GB008545 |
| `instrument:raw:delta_v_advantage_isotope_ratio_mass_spectrometer` | PSI-MS | 1 | Delta V Advantage Isotope Ratio Mass Spectrometer | 10.1038/s41467-022-29711-9 |
| `instrument:raw:direct_inlet_probe_high_resolution_time_of_flight_mass_` | PSI-MS | 1 | Direct Inlet Probe-High-Resolution Time-of-Flight Mass Spectrometer | 10.1021/acs.energyfuels.1c02107 |
| `instrument:raw:direct_insertion_probe_mass_spectrometer` | PSI-MS | 1 | Direct Insertion Probe-Mass Spectrometer | 10.1021/acs.energyfuels.1c02107 |
| `instrument:raw:double_focusing_sector_field_inductively_coupled_plasma` | PSI-MS | 1 | double-focusing sector field inductively coupled plasma mass spectrometer (Element XR, Thermo Fisher Scientific) | 10.3390/pr8111472 |
| `instrument:raw:dual_inlet_isotope_ratio_mass_spectrometer` | PSI-MS | 1 | dual-inlet isotope ratio mass spectrometer | 10.1029/2020JG005977 |
| `instrument:raw:electrospray_ionization_fourier_transform_ion_cyclotron` | PSI-MS | 1 | electrospray ionization fourier transform ion cyclotron resonance mass spectrometry (ESI FT-ICR MS) | 10.1021/acs.energyfuels.3c01462 |
| `instrument:raw:esi_ft_icr_mass_spectrometer` | PSI-MS | 1 | ESI FT-ICR mass spectrometer | 10.1021/ar020177t |
| `instrument:raw:esi_ft_icr_ms_based` | PSI-MS | 1 | ESI( -) FT-ICR MS-based | 10.1021/acs.molpharmaceut.5c00679 |
| `instrument:raw:esi_negative_ion_ft_icr_ms` | PSI-MS | 1 | ESI Negative Ion FT-ICR MS | 10.1021/acs.energyfuels.1c02107 |
| `instrument:raw:etd_ft_icr` | PSI-MS | 1 | ETD-FT-ICR | 10.1016/j.mcpro.2024.100814 |
| `instrument:raw:fourier_ion_cyclotron_resonance_mass_spectrometer` | PSI-MS | 1 | Fourier Ion Cyclotron Resonance Mass Spectrometer | 10.1029/2022JG007188 |
| `instrument:raw:fourier_transform_ion_cyclotron_resolution_mass_spectro` | PSI-MS | 1 | Fourier transform ion cyclotron resolution mass spectrometry (FT-ICR MS) | 10.1021/ef100149n |
| `instrument:raw:fourier_transform_ion_cyclotron_resonance` | PSI-MS | 1 | Fourier transform ion cyclotron resonance | 10.1016/j.chempr.2017.07.011 |
| `instrument:raw:fourier_transform_mass_spectrometer` | PSI-MS | 1 | Fourier-transform (FT) mass spectrometer | 10.1101/455527 |
| `instrument:raw:ft_icr` | PSI-MS | 1 | FT-ICR | 10.1021/acs.energyfuels.4c02605; 10.1021/acs.energyfuels.8b04219; 10.1021/ef1001502 (+1) |
| `instrument:raw:ft_icr_mass_analyzer` | PSI-MS | 1 | FT-ICR mass analyzer | 10.1002/mas.21666 |
| `instrument:raw:ft_icr_mass_spectrometry` | PSI-MS | 1 | FT-ICR Mass Spectrometry | 10.1021/acs.energyfuels.0c01564; 10.1021/acs.energyfuels.1c02107; 10.1021/acs.energyfuels.3c01462 |
| `instrument:raw:ft_icr_ms_40` | PSI-MS | 1 | FT-ICR MS 40 | 10.1021/acs.est.7b05346 |
| `instrument:raw:ft_icr_ms_instrument` | PSI-MS | 1 | FT-ICR MS instrument | 10.1021/acs.energyfuels.5c04213 |
| `instrument:raw:fticr` | PSI-MS | 1 | FTICR | 10.1021/acs.est.1c01135 |
| `instrument:raw:fticrms` | PSI-MS | 1 | FTICRMS | 10.1016/j.orggeochem.2020.104164 |
| `instrument:raw:gas_chromatograph_mass_spectrometer` | PSI-MS | 1 | gas chromatograph-mass spectrometer (GC-MS) | 10.1038/s41467-023-41900-8 |
| `instrument:raw:gas_chromatography_atmospheric_pressure_chemical_ioniza` | PSI-MS | 1 | gas chromatography/atmospheric pressure chemical ionization mass spectrometer (GC/APCI-MS) | 10.1016/j.epsl.2020.116411 |
| `instrument:raw:gc_ms_system` | PSI-MS | 1 | GC-MS system (7890A, Agilent Technologies) | 10.1016/j.dib.2020.105989; 10.1016/j.indcrop.2020.112311 |
| `instrument:raw:gcxgc_tof_ms` | PSI-MS | 1 | GCxGC/TOF-MS | 10.1038/s41598-024-79780-7 |
| `instrument:raw:gel_permeation_chromatography_inductively_coupled_plasm` | PSI-MS | 1 | gel permeation chromatography inductively coupled plasma high-resolution mass spectrometry (GPCICP-HRMS) | 10.1021/acs.energyfuels.3c01462 |
| `instrument:raw:high_fi_eld_fourier_transform_ion_cyclotron_resonance_m` | PSI-MS | 1 | high- fi eld Fourier transform ion cyclotron resonance mass spectrometer | 10.1021/acs.energyfuels.1c02107 |
| `instrument:raw:high_performance_liquid_chromatography_inductively_coup` | PSI-MS | 1 | High-Performance Liquid Chromatography-Inductively Coupled Plasma-Mass Spectrometry | 10.1021/acs.est.1c01135 |
| `instrument:raw:high_resolution_fourier_transform_ion_cyclo_tron_resona` | PSI-MS | 1 | high resolution Fourier transform ion cyclo- tron resonance (FT-ICR) mass spectrometer | 10.1002/hlca.201900046 |
| `instrument:raw:high_resolution_fouriertransform_ion_cyclotron_resonanc` | PSI-MS | 1 | high resolution Fouriertransform ion cyclotron resonance mass spectrometry | 10.1021/acs.energyfuels.1c01837 |
| `instrument:raw:high_resolution_ft_icr_mass_spectrometer` | PSI-MS | 1 | high-resolution FT-ICR mass spectrometer | 10.1039/c4sc02268h |
| `instrument:raw:high_resolution_icp_mass_spectrometer` | PSI-MS | 1 | high-resolution ICP mass spectrometer (Thermo) | 10.1021/acs.energyfuels.0c02687 |
| `instrument:raw:high_resolution_tof` | PSI-MS | 1 | high-resolution TOF | 10.1021/acs.energyfuels.1c02002 |
| `instrument:raw:highresolution_time_of_fl_ight_mass_spectrometer` | PSI-MS | 1 | highresolution ( m / Δ m 50% ≈ 4000) time-of- fl ight mass spectrometer | 10.1021/acs.est.7b05346 |
| `instrument:raw:hybrid_linear_ion_trap_ft_icr_mass_spectrometer` | PSI-MS | 1 | hybrid linear ion trap FT-ICR mass spectrometer | 10.1021/acsestwater.1c00494 |
| `instrument:raw:icap_q_ms` | PSI-MS | 1 | iCAP Q MS (Thermo Scientific) | 10.1021/jasms.4c00380 |
| `instrument:raw:icp_ms` | PSI-MS | 1 | ICP-MS | 10.1021/acs.energyfuels.1c01837 |
| `instrument:raw:icp_ms_on_an_icap_rq` | PSI-MS | 1 | ICP-MS on an iCAP RQ | 10.1038/s43247-024-01965-9 |
| `instrument:raw:inductively_coupled_plasma_high_resolution_mass_spectro` | PSI-MS | 1 | Inductively Coupled Plasma High-Resolution Mass Spectrometry | 10.1021/acs.energyfuels.1c02107 |
| `instrument:raw:inductively_coupled_plasma_highresolution_mass_spectrom` | PSI-MS | 1 | Inductively Coupled Plasma HighResolution Mass Spectrometry | 10.1021/acs.energyfuels.1c01837 |
| `instrument:raw:inductively_coupled_plasma_mass_spectrometer` | PSI-MS | 1 | inductively coupled plasma mass spectrometer (ICP-MS) | 10.1039/d0se01662d |
| `instrument:raw:ion_cyclotron_resonance_mass_analyzer` | PSI-MS | 1 | ion cyclotron resonance (ICR) mass analyzer | 10.1021/acs.jproteome.0c00303; 10.1021/acs.jproteome.0c00403 |
| `instrument:raw:isotope_ratio_mass_spectrometer` | PSI-MS | 1 | isotope ratio mass spectrometer | 10.1073/pnas.2504769122 |
| `instrument:raw:la_icp_ms` | PSI-MS | 1 | LA-ICP-MS | 10.1021/acs.energyfuels.0c02525 |
| `instrument:raw:laser_desorption_fourier_transform_ion_cyclotron_resona` | PSI-MS | 1 | Laser desorption Fourier transform ion cyclotron resonance mass spectrometery (LD FT-ICR MS) | 10.1021/acs.joc.6b02301 |
| `instrument:raw:lc_and_hesi_source_settings_were_the_same_as_those_in_m` | PSI-MS | 1 | LC and HESI source settings were the same as those in MS 1 analyses | 10.1021/jasms.4c00380 |
| `instrument:raw:lc_fticr_ms_ms` | PSI-MS | 1 | LC FTICR MS/MS | 10.1021/acs.est.1c01135 |
| `instrument:raw:lc_orbitrap` | PSI-MS | 1 | LC-Orbitrap | 10.1016/j.orggeochem.2024.104880 |
| `instrument:raw:lc_qtof` | PSI-MS | 1 | LC-QTOF | 10.1021/acs.est.0c01997 |
| `instrument:raw:lcq` | PSI-MS | 1 | LCQ | 10.1002/jms.3345 |
| `instrument:raw:ldi_tof_ms` | PSI-MS | 1 | LDI TOF-MS | 10.1021/acs.energyfuels.1c02002 |
| `instrument:raw:linear_ion_trap_mass_spectrometer` | PSI-MS | 1 | linear ion-trap mass spectrometer | 10.1021/acs.energyfuels.8b04219 |
| `instrument:raw:linear_trapping_quadrupole` | PSI-MS | 1 | linear trapping quadrupole | 10.1007/s13361-018-1897-y |
| `instrument:raw:liquid_chromatography_high_resolution_multistage_mass_s` | PSI-MS | 1 | liquid chromatography-high resolution multistage mass spectrometry | 10.2138/gselements.18.2.107 |
| `instrument:raw:lower_field_ft_icr_ms` | PSI-MS | 1 | lower-field FT-ICR MS | 10.21037/atm.2019.12.67 |
| `instrument:raw:ltq_orbitrapvelos` | PSI-MS | 1 | LTQ OrbitrapVelos | 10.1021/jp503413s |
| `instrument:raw:ltqorbitrap` | PSI-MS | 1 | LTQOrbitrap | 10.1021/acs.energyfuels.3c00856 |
| `instrument:raw:maldi` | PSI-MS | 1 | MALDI | 10.1021/acs.energyfuels.0c02525 |
| `instrument:raw:maldi_tof` | PSI-MS | 1 | MALDI-TOF | 10.1021/acs.energyfuels.1c02002 |
| `instrument:raw:maldiand_esi_fourier_transform_ion_cyclotron_resonance` | PSI-MS | 1 | MALDIand ESI-Fourier Transform Ion Cyclotron Resonance | 10.1021/acs.est.1c01135 |
| `instrument:raw:mat_253_isotope_ratio_mass_spectrometer` | PSI-MS | 1 | MAT-253 isotope ratio mass spectrometer | 10.1016/j.watres.2023.119812 |
| `instrument:raw:mft_solarix_icr_paracell` | PSI-MS | 1 | mFT Solarix ICR ParaCell | 10.1021/jasms.4c00232 |
| `instrument:raw:micromass_premier_double_focussing_magnetic_sector_mass` | PSI-MS | 1 | Micromass Premier double-focussing magnetic sector mass spectrometer | 10.1016/j.aca.2019.01.007 |
| `instrument:raw:mini_carbon_dating_accelerator_mass_spectrometer_system` | PSI-MS | 1 | mini carbon dating accelerator mass spectrometer (MICADAS) system | 10.1002/lno.12436 |
| `instrument:raw:modified_velos_pro_linear_ion_trap_assembly` | PSI-MS | 1 | modified Velos Pro linear ion trap assembly | 10.1016/j.jbc.2022.102768 |
| `instrument:raw:negative_ion_appi_ft_icr_ms` | PSI-MS | 1 | negative-ion APPI FT-ICR MS | 10.1016/j.dib.2020.105989 |
| `instrument:raw:negative_ion_esi_ft_icr_ms` | PSI-MS | 1 | negative-ion ESI-FT-ICR-MS | 10.1021/acs.energyfuels.6b02643 |
| `instrument:raw:nexion_250d_mass_spectrometer` | PSI-MS | 1 | NexION 250D mass spectrometer | 10.1039/D2EM00184E |
| `instrument:raw:online_sec_uv_ft_icr_ms` | PSI-MS | 1 | online SEC-UV-FT-ICR MS | 10.1021/acs.energyfuels.3c00856 |
| `instrument:raw:orbitrap_eclipse` | PSI-MS | 1 | Orbitrap Eclipse | 10.1515/cclm-2020-1072 |
| `instrument:raw:orbitrap_exploris_120` | PSI-MS | 1 | Orbitrap Exploris 120 | 10.1016/j.watres.2025.124698 |
| `instrument:raw:orbitrap_high_resolution_mass_spectrometer_platform` | PSI-MS | 1 | Orbitrap high-resolution mass spectrometer platform | 10.1021/acs.energyfuels.2c02122 |
| `instrument:raw:orbitrap_mass_analyzer` | PSI-MS | 1 | Orbitrap mass analyzer | 10.1021/acs.energyfuels.2c02122 |
| `instrument:raw:orbitrap_mass_spectrometer` | PSI-MS | 1 | Orbitrap mass spectrometer | 10.1021/acs.energyfuels.1c02002 |
| `instrument:raw:orbitrap_mass_spectrometer_detector` | PSI-MS | 1 | Orbitrap mass spectrometer detector | 10.2138/gselements.18.2.107 |
| `instrument:raw:orbitrap_mass_spectrometry` | PSI-MS | 1 | Orbitrap Mass Spectrometry | 10.1021/acs.energyfuels.1c02107 |
| `instrument:raw:orbitraps` | PSI-MS | 1 | Orbitraps | 10.2138/gselements.18.2.107 |
| `instrument:raw:perkinelmer_nexion_350x_icp_ms` | PSI-MS | 1 | PerkinElmer Nexion 350X ICP-MS | 10.1021/acs.est.1c02272 |
| `instrument:raw:positive_ion_appi_ft_icr_ms` | PSI-MS | 1 | positive-ion APPI FT-ICR MS | 10.1016/j.dib.2020.105989 |
| `instrument:raw:qe_hf_mass_spectrometer` | PSI-MS | 1 | QE-HF mass spectrometer | 10.1016/j.jbc.2022.102768 |
| `instrument:raw:qp5050a_ei_quadrupole` | PSI-MS | 1 | QP5050A EI quadrupole | 10.1007/s12155-018-9919-y |
| `instrument:raw:quadrupole_mass_spectrometer` | PSI-MS | 1 | quadrupole mass spectrometer | 10.1021/acs.energyfuels.2c04274; 10.1063/1.5116925 |
| `instrument:raw:quadrupole_trap` | PSI-MS | 1 | quadrupole trap | 10.1007/s13361-015-1182-2 |
| `instrument:raw:sfc_icp_ms` | PSI-MS | 1 | SFC-ICP-MS | 10.1021/acs.energyfuels.3c01462 |
| `instrument:raw:shimadzu_gcms_qp2010_se` | PSI-MS | 1 | Shimadzu GCMS-QP2010 SE | 10.1021/acs.energyfuels.4c01959 |
| `instrument:raw:shimadzu_maldi_8020` | PSI-MS | 1 | Shimadzu MALDI-8020 | 10.1021/acs.jproteome.0c00303 |
| `instrument:raw:supercritical_fluid_chromatography_inductively_coupled_` | PSI-MS | 1 | supercritical fluid chromatography inductively coupled plasma mass spectrometry (SFC-ICPMS) | 10.1021/acs.energyfuels.3c01462 |
| `instrument:raw:synapt_g2_hdms` | PSI-MS | 1 | Synapt G2 HDMS | 10.1021/acs.energyfuels.6b01191 |
| `instrument:raw:t_ft_icr` | PSI-MS | 1 | T FT-ICR | 10.1021/jasms.4c00261 |
| `instrument:raw:thermo_finnigan_253_gas_mass_spectrometer` | PSI-MS | 1 | Thermo Finnigan 253 gas mass spectrometer | 10.1038/s43247-024-01832-7 |
| `instrument:raw:thermo_fisher_scientific_orbitrap_eclipse_tm_tribrid_tm` | PSI-MS | 1 | Thermo Fisher Scientific Orbitrap Eclipse TM Tribrid TM MS | 10.1021/acs.analchem.5c05562 |
| `instrument:raw:thermo_scientific_element_2_hr_icp_ms` | PSI-MS | 1 | Thermo Scientific™ Element 2™ HR-ICP-MS | 10.1029/2022JG006852 |
| `instrument:raw:thermo_scientific_orbitrap_iq_x` | PSI-MS | 1 | Thermo Scientific Orbitrap IQ-X | 10.1016/j.orggeochem.2024.104880 |
| `instrument:raw:thermofisher_lcq` | PSI-MS | 1 | ThermoFisher LCQ | 10.1038/s41467-017-01123-0 |
| `instrument:raw:thermoscientific_ltq_xl_lit` | PSI-MS | 1 | ThermoScientific LTQ-XL LIT | 10.1016/j.ijms.2015.12.005 |
| `instrument:raw:time_of_flight_mass_spectrometer` | PSI-MS | 1 | time-of-flight (TOF) mass spectrometer | 10.1021/acs.energyfuels.1c02107 |
| `instrument:raw:time_of_flight_secondary_ion_mass_spectrometry` | PSI-MS | 1 | time-of-flight secondary ion mass spectrometry (ToF-SIMS) | 10.2138/gselements.18.2.107 |
| `instrument:raw:tims_ft_icr_ms_ms` | PSI-MS | 1 | TIMS-FT-ICR MS/MS | 10.1021/acs.energyfuels.1c02107 |
| `instrument:raw:tof` | PSI-MS | 1 | TOF | 10.1021/jasms.0c00036 |
| `instrument:raw:tof_mass_analyzer` | PSI-MS | 1 | TOF mass analyzer | 10.1021/acs.energyfuels.6b02411 |
| `instrument:raw:tof_mass_spectrometer` | PSI-MS | 1 | TOF mass spectrometer | 10.1021/acs.energyfuels.7b03204 |
| `instrument:raw:triple_quadrupole_instruments` | PSI-MS | 1 | triple quadrupole instruments | 10.1373/clinchem.2019.305631 |
| `instrument:raw:ultra_high_resolution_ft_icr_ms` | PSI-MS | 1 | Ultra-high resolution FT-ICR MS | 10.1038/s43017-020-0046-x |
| `instrument:raw:ultra_high_resolution_mass_spectrometer` | PSI-MS | 1 | Ultra-High-Resolution Mass Spectrometer | 10.1021/acs.energyfuels.1c01837 |
| `instrument:raw:velos` | PSI-MS | 1 | Velos | 10.1002/jms.3345 |
| `instrument:raw:velos_pro_dual_cell_linear_rf_ion_trap` | PSI-MS | 1 | Velos-Pro dual cell linear RF ion trap | 10.1021/jasms.4c00261 |
| `instrument:raw:velos_pro_dual_cell_rf_ion_trap_assembly` | PSI-MS | 1 | Velos Pro dual cell rf ion trap assembly | 10.1007/s13361-017-1702-3 |
| `instrument:raw:velos_pro_dualcell_linear_ion_trap` | PSI-MS | 1 | Velos Pro dualcell linear ion trap | 10.1021/acs.energyfuels.4c05674 |
| `instrument:raw:waters_autospec_premier_double_sector_mass_spectrometer` | PSI-MS | 1 | Waters AutoSpec Premier double-sector mass spectrometer | 10.1073/pnas.1803866115 |
| `instrument:raw:waters_synapt_g2_hdms` | PSI-MS | 1 | Waters Synapt G2 HDMS | 10.1007/s13361-018-1897-y |
| `instrument:raw:waters_xevo_g2_xs_qtof_ms` | PSI-MS | 1 | Waters Xevo G2-XS QToF-MS | 10.1038/s42004-018-0031-1 |
| `instrument:raw:waters_xevo_g2_xs_quadrupole_time_of_flight` | PSI-MS | 1 | Waters Xevo G2-XS quadrupole time-of-flight | 10.1016/j.aca.2019.01.007 |

## AUTO-MINTED — NON-MS (null)  [292 nodes]
| node | ontology_source | #strings | example string(s) | DOI(s) |
|---|---|---|---|---|
| `instrument:raw:shimadzu_toc_total_organic_carbon_analyzer` | null | 6 | Shimadzu TOC total organic carbon analyzer · Shimadzu Total Organic Carbon Analyzer | 10.1002/etc.5742; 10.1016/j.gca.2016.05.015; 10.1016/j.isci.2022.104916 (+3) |
| `instrument:raw:illumina_miseq_sequencing_system` | null | 5 | Illumina MiSeq · Illumina MiSeq Platform | 10.1007/s10533-018-00534-5; 10.1007/s11783-022-1567-y; 10.1016/j.ecolind.2024.111884 (+5) |
| `instrument:raw:horiba_scientific_aqualog_spectrofluorometer` | null | 4 | Horiba Aqualog · Horiba Aqualog fluorometer | 10.1002/lno.11417; 10.1007/s00027-017-0540-5; 10.1007/s10533-019-00619-9 (+12) |
| `instrument:raw:shimadzu_toc_l_cph_high_temperature_catalytic_oxidation` | null | 3 | Shimadzu TOC-L CPH high temperature catalytic oxidation total organic analyzer · Shimadzu TOC-L CPH high temperature catalytic oxidation total organic carbon analyzer | 10.1016/j.orggeochem.2024.104846; 10.1029/2021JG006578; 10.1029/2022JG007073 |
| `instrument:raw:shimadzu_toc_l_total_organic_carbon_analyzer` | null | 3 | Shimadzu TOC-L · Shimadzu TOC-L total organic carbon analyzer | 10.1002/lno.12436; 10.1016/j.watres.2023.120808; 10.1021/acs.energyfuels.1c02373 (+4) |
| `instrument:raw:shimadzu_toc_lcph_analyzer` | null | 3 | Shimadzu TOC -LCPH analyzer · Shimadzu TOC-LCPH | 10.1002/lno.11857; 10.1021/acs.est.7b01278; 10.1029/2017JG004311 (+5) |
| `instrument:raw:shimadzu_toc_vcph_analyzer` | null | 3 | Shimadzu TOC-VCPH · Shimadzu TOC-VCPH analyzer | 10.1002/2017JG004343; 10.1002/lol2.10388; 10.1021/acs.est.1c03592 (+1) |
| `instrument:raw:agilent_7890_a_gas_chromatograph` | null | 2 | Agilent 7890 · Agilent 7890 A Gas Chromatograph | 10.1016/j.jhazmat.2021.127598; 10.1021/acs.est.7b05346 |
| `instrument:raw:agilent_model_8453_photodiode_array_spectrophotometer` | null | 2 | Agilent 8453 · Agilent Model 8453 photodiode array spectrophotometer | 10.1002/2016JG003431; 10.1029/2017JG004327; 10.1029/2018JG004982 |
| `instrument:raw:dionex_aquion_ion_chromatography_system` | null | 2 | Dionex Aquion Ion Chromatography System · Dionex Aquion ion chromatography system | 10.1007/s11356-024-35140-6; 10.1021/acsestwater.4c00588 |
| `instrument:raw:dionex_ultimate_3000_2_dual_analytical_system` | null | 2 | Dionex UltiMate 3000 × 2 Dual Analytical System · Dionex UltiMate 3000 × 2 Dual Analytical system | 10.1002/pmic.201700442; 10.1074/mcp.M114.046441; 10.1074/mcp.M116.058412 |
| `instrument:raw:dionex_ultimate_3000_lc_system` | null | 2 | Dionex Ultimate 3000 LC system · UltiMate 3000 Dionex | 10.1021/acs.energyfuels.4c01959; 10.1038/s43247-024-01965-9 |
| `instrument:raw:dual_beam_shimadzu_uv_1800_spectrophotometer` | null | 2 | Shimadzu UV-1800 spectrophotometer · dual-beam Shimadzu UV-1800 spectrophotometer | 10.1002/lno.11385; 10.1029/2020GB006871; 10.5194/bg-15-6637-2018 |
| `instrument:raw:hitachi_f_7000_spectrofluorometer` | null | 2 | Hitachi F-7000 · Hitachi F-7000 spectrofluorometer | 10.1002/lno.11385; 10.1021/acsestwater.4c00832 |
| `instrument:raw:shimadzu_toc_l_cph_analyzer` | null | 2 | Shimadzu TOC-L CPH · Shimadzu TOC-L CPH analyzer | 10.1002/2017JG004337; 10.1007/s10533-019-00619-9; 10.1007/s10533-021-00852-1 (+11) |
| `instrument:raw:thermo_finnigan_elemental_analyzer` | null | 2 | Thermo Finnigan Elemental Analyzer · Thermo Finnigan Elemental Analyzer (FLASH EA 112) | 10.1021/acs.energyfuels.7b03944; 10.1021/acs.est.6b01156 |
| `instrument:raw:thermo_fisher_ultimate_3000` | null | 2 | Thermo Fisher UltiMate 3000 · Thermo Ultimate 3000 system | 10.1002/pmic.201300438; 10.1029/2024GB008359 |
| `instrument:raw:thermo_flash_2000` | null | 2 | FLASH 2000 · Thermo FLASH 2000 | 10.1021/acs.energyfuels.3c02599; 10.1089/ast.2022.0021 |
| `instrument:raw:uv_vis_spectrophotometer` | null | 2 | UV -vis spectrophotometer · UV-Vis spectrophotometer | 10.1007/s11356-024-35140-6; 10.1021/acs.est.6b05126 |
| `instrument:raw:9_4_and_14_5_t_instruments` | null | 1 | 9.4 and 14.5 T instruments | 10.1002/jms.3345 |
| `instrument:raw:acros_eop_icp_aes` | null | 1 | Acros-EOP ICP/AES | 10.1016/j.orggeochem.2016.11.004 |
| `instrument:raw:agilent_6560c` | null | 1 | Agilent 6560c | 10.1016/j.mcpro.2024.100814 |
| `instrument:raw:agilent_6890n_gas_chromatograph` | null | 1 | Agilent 6890N gas chromatograph | 10.1021/acs.energyfuels.1c02642 |
| `instrument:raw:agilent_6890n_gc_5975_ms` | null | 1 | Agilent 6890N GC/5975 MS | 10.1002/2017JG004337; 10.1007/s10533-019-00619-9; 10.1029/2020JG005988 |
| `instrument:raw:agilent_8453_uv_visible_spectroscopy_system` | null | 1 | Agilent 8453 UV-visible spectroscopy system | 10.1002/lno.11857 |
| `instrument:raw:agilent_8900` | null | 1 | Agilent 8900 | 10.1038/s43247-022-00407-8 |
| `instrument:raw:agilent_gc6890n` | null | 1 | Agilent GC6890N | 10.1016/j.watres.2019.115048 |
| `instrument:raw:agilent_technologies_1260_infinity` | null | 1 | Agilent Technologies 1260 Infinity | 10.1038/s41598-017-16959-1 |
| `instrument:raw:akta_purifier_liquid_chromatography_system` | null | 1 | AKTA purifier liquid chromatography system | 10.1021/acs.energyfuels.0c01522; 10.1021/acs.energyfuels.8b02788 |
| `instrument:raw:alliance_e2695_separation_module` | null | 1 | Alliance e2695 separation module | 10.1021/acs.energyfuels.0c02158 |
| `instrument:raw:alpkem_rfa_300_autoanalyzer` | null | 1 | Alpkem RFA-300 autoanalyzer | 10.1126/sciadv.abn0035 |
| `instrument:raw:appisource` | null | 1 | APPISource | 10.1021/ef100149n |
| `instrument:raw:aqualog` | null | 1 | Aqualog | 10.1016/j.scitotenv.2020.142411 |
| `instrument:raw:aurora_1030_w_toc_analyzer` | null | 1 | Aurora 1030 W TOC Analyzer | 10.1038/s41467-023-41900-8 |
| `instrument:raw:aurora_1030c` | null | 1 | Aurora 1030C | 10.1126/sciadv.abn0035 |
| `instrument:raw:autoanalyzer_aa3` | null | 1 | autoanalyzer (AA3 | 10.1073/pnas.1714597115 |
| `instrument:raw:automated_nitrogen_carbon_analyzer_sercon` | null | 1 | Automated Nitrogen Carbon Analyzer, SerCon | 10.1002/lno.12436 |
| `instrument:raw:autosal_salinometer` | null | 1 | Autosal salinometer | 10.1126/sciadv.abn0035 |
| `instrument:raw:aviv_202sf_circular_dichroism_spectrometer` | null | 1 | AVIV 202SF circular dichroism spectrometer | 10.1021/acs.biochem.8b00733 |
| `instrument:raw:aviv_410_cd_spectrometer` | null | 1 | AVIV 410 CD spectrometer | 10.1016/j.chempr.2017.07.011 |
| `instrument:raw:axio_imager_m2` | null | 1 | Axio Imager M2 (Zeiss) | 10.1021/acs.analchem.3c00393 |
| `instrument:raw:beckman_model_j2_21` | null | 1 | Beckman model J2-21 | 10.1016/j.scitotenv.2023.167382 |
| `instrument:raw:beckman_optima_xl_i` | null | 1 | Beckman Optima XL-I | 10.1016/j.str.2017.08.002 |
| `instrument:raw:bioinert_ultimate_rslcnano_3000_lc_system` | null | 1 | bioinert Ultimate RSLCnano 3000 LC system | 10.1016/j.orggeochem.2024.104880 |
| `instrument:raw:bran_and_luebbe` | null | 1 | Bran and Luebbe) | 10.1073/pnas.1714597115 |
| `instrument:raw:bruker_compass_dataanalysis` | null | 1 | Bruker Compass Dataanalysis | 10.1002/pmic.201300438 |
| `instrument:raw:bruker_gc_apci_ii` | null | 1 | Bruker GC-APCI II | 10.1021/jasms.4c00120 |
| `instrument:raw:bruker_ultra_fl_extreme` | null | 1 | Bruker Ultra fl eXtreme | 10.1021/acs.est.8b06861 |
| `instrument:raw:canadian_light_source_spherical_grating_monochromator_b` | null | 1 | Canadian Light Source spherical grating monochromator (SGM) beamline | 10.1016/j.gca.2025.08.041 |
| `instrument:raw:cary_100_bio_uv_visible_spectrophotometer` | null | 1 | Cary 100 Bio UV-Visible Spectrophotometer | 10.1016/j.orggeochem.2020.104164 |
| `instrument:raw:cary_eclipse_spectrofluorometer` | null | 1 | Cary Eclipse spectrofluorometer | 10.1126/sciadv.abn0035 |
| `instrument:raw:cary_varian_100_dual_beam_uv_vis_spectrometer` | null | 1 | Cary Varian 100 dual beam UV/Vis spectrometer | 10.1016/j.gca.2016.05.015 |
| `instrument:raw:cfp_unit` | null | 1 | CFP unit | 10.1039/C9SE00837C |
| `instrument:raw:chriascan_cd_spectrometer` | null | 1 | Chriascan CD spectrometer | 10.1038/s41598-017-16959-1 |
| `instrument:raw:controlled_growth_mercury_electrode` | null | 1 | controlled growth mercury electrode | 10.3389/fmars.2016.00243 |
| `instrument:raw:custom_built` | null | 1 | custom-built | 10.1021/acs.energyfuels.7b00490; 10.1021/acs.est.3c02962; 10.1021/acs.est.7b05513 (+1) |
| `instrument:raw:custom_instrument` | null | 1 | custom instrument | 10.1029/2022JG006852 |
| `instrument:raw:custom_made_purge_and_trap_system` | null | 1 | custom-made purge-and-trap system | 10.1126/sciadv.abn0035 |
| `instrument:raw:cyan_flow_cytometer` | null | 1 | CyAn Flow Cytometer | 10.1111/1462-2920.14344 |
| `instrument:raw:deltatox_ii_photometer` | null | 1 | Deltatox II photometer | 10.1021/acs.est.8b00016 |
| `instrument:raw:dib_s4pt` | null | 1 | DIB-s4PT | 10.1063/1.5116925 |
| `instrument:raw:dionex_dx_500` | null | 1 | Dionex DX 500 | 10.1007/s10533-015-0103-6 |
| `instrument:raw:dionex_high_performance_liquid_chromatography_system` | null | 1 | Dionex High-Performance Liquid Chromatography system | 10.3390/pr8111472 |
| `instrument:raw:dionex_ics_1100` | null | 1 | Dionex ICS-1100 | 10.1007/s10533-018-00534-5 |
| `instrument:raw:dionex_ion_chromatography_system` | null | 1 | Dionex Ion Chromatography System | 10.1038/s41467-022-29711-9 |
| `instrument:raw:dionex_series_3000_ion_chromatography_system` | null | 1 | Dionex Series 3000 Ion Chromatography System | 10.1021/acs.est.7b01278 |
| `instrument:raw:dlk_micro_pstat_1` | null | 1 | DLK Micro-Pstat-1 | 10.1021/acs.est.3c01782 |
| `instrument:raw:doc_labor_lc_ocd_size_exclusion_chromatography_system` | null | 1 | DOC-LABOR LC-OCD size-exclusion chromatography system | 10.1016/j.gca.2020.01.022 |
| `instrument:raw:doc_labor_lc_ocd_sizeexclusion_chromatography_system` | null | 1 | DOC-LABOR LC-OCD sizeexclusion chromatography system | 10.1016/j.watres.2019.115201 |
| `instrument:raw:double_beam_spectrophotometer` | null | 1 | double beam spectrophotometer | 10.1016/j.orggeochem.2020.104164 |
| `instrument:raw:dreem_toolbox_22_for_matlab` | null | 1 | drEEM toolbox 22 for MATLAB | 10.1021/acs.est.9b01894 |
| `instrument:raw:dri_model_2015_series_1_multiwavelength_thermal_optical` | null | 1 | DRI Model 2015 Series 1 multiwavelength thermal-optical carbon analyzer (TOCA) | 10.1021/acs.energyfuels.2c02122 |
| `instrument:raw:drop_tensiometer` | null | 1 | drop tensiometer | 10.1021/acs.energyfuels.6b02897 |
| `instrument:raw:dynamically_harmonized_icr` | null | 1 | dynamically harmonized ICR | 10.1021/acs.energyfuels.3c02599 |
| `instrument:raw:electron_spin_resonance` | null | 1 | electron spin resonance | 10.1021/acs.energyfuels.0c01564 |
| `instrument:raw:elemental_analyzer` | null | 1 | elemental analyzer (Thermo Flash EA 1112) | 10.1016/j.watres.2017.11.040 |
| `instrument:raw:eosense_instruments` | null | 1 | eosense instruments | 10.1038/s43247-022-00407-8 |
| `instrument:raw:eosfd` | null | 1 | eosFD | 10.1038/s43247-022-00407-8 |
| `instrument:raw:escalab250xi` | null | 1 | ESCALAB250Xi | 10.1038/s41467-017-01123-0 |
| `instrument:raw:f_7000_fluorescence_spectrometer` | null | 1 | F-7000 fluorescence spectrometer | 10.1016/j.scitotenv.2018.05.180 |
| `instrument:raw:fe_sem` | null | 1 | FE-SEM | 10.1038/s43247-022-00407-8 |
| `instrument:raw:fei_talos_f200x` | null | 1 | FEI Talos F200X | 10.1021/acs.energyfuels.3c05200 |
| `instrument:raw:fei_titan_krios` | null | 1 | FEI Titan Krios | 10.1016/j.str.2017.08.002 |
| `instrument:raw:fei_tm_tecnai_f20` | null | 1 | FEI TM Tecnai F20 | 10.1021/acs.est.8b06861 |
| `instrument:raw:finnigan_deltaplus_xp_elemental_analyzer` | null | 1 | Finnigan DeltaPlus XP elemental analyzer | 10.1029/2018JG004712 |
| `instrument:raw:finnigan_matdeltaplusxl` | null | 1 | Finnigan MATDeltaplusXL | 10.1016/j.watres.2017.11.040 |
| `instrument:raw:fl_uorometer` | null | 1 | fl uorometer (AquaFlour model: 80000-010) | 10.1016/j.chemosphere.2019.125399 |
| `instrument:raw:flame_atomic_absorption_spectrometry` | null | 1 | Flame Atomic Absorption Spectrometry (FAAS) | 10.1021/acs.energyfuels.3c01462 |
| `instrument:raw:flash_ea` | null | 1 | Flash EA | 10.1038/s41561-019-0384-9 |
| `instrument:raw:flash_ea1112_analyzer` | null | 1 | Flash EA1112 analyzer | 10.1016/j.scitotenv.2018.05.180 |
| `instrument:raw:flash_smart_analyzer` | null | 1 | Flash SMART analyzer | 10.1021/acs.energyfuels.3c02599 |
| `instrument:raw:fluoromax_4_spectrofluorometer` | null | 1 | Fluoromax-4 spectrofluorometer | 10.1002/lol2.10082 |
| `instrument:raw:fs5_spectrofluorometer` | null | 1 | FS5 spectrofluorometer | 10.1016/j.palaeo.2025.112798 |
| `instrument:raw:ftir` | null | 1 | FTIR | 10.1038/s41467-017-01123-0 |
| `instrument:raw:gas_chromatograph` | null | 1 | gas chromatograph | 10.1038/s41561-019-0384-9 |
| `instrument:raw:gc_apci_ms` | null | 1 | GC/APCI-MS | 10.1021/acs.analchem.6b01652; 10.1021/acs.est.7b04445 |
| `instrument:raw:gc_apci_ms_ms` | null | 1 | GC/APCI-MS/MS | 10.1021/acs.est.7b04445 |
| `instrument:raw:gc_fid` | null | 1 | GC-FID | 10.1021/acs.energyfuels.2c00656 |
| `instrument:raw:gc_gc_ei_hrtof_ms` | null | 1 | GC × GC EI-HRToF MS | 10.1021/acs.molpharmaceut.5c00679 |
| `instrument:raw:gc_gc_tofms_from_leco` | null | 1 | GC × GC-TOFMS from LECO (USA) | 10.1007/s12155-018-9919-y |
| `instrument:raw:ge_sievers_900_portable_total_organic_carbon_analyzer` | null | 1 | GE Sievers 900 Portable Total Organic Carbon Analyzer | 10.1007/s10533-018-00534-5 |
| `instrument:raw:ge_sievers_m9_toc_analyzer` | null | 1 | GE Sievers M9 TOC analyzer | 10.1029/2024GB008359 |
| `instrument:raw:genesys_10_s_series_spectrophotometer` | null | 1 | Genesys 10 s Series Spectrophotometer | 10.1007/s10533-018-00534-5 |
| `instrument:raw:genesys_20_thermo_scientific` | null | 1 | Genesys 20-Thermo scientific | 10.1063/5.0287657 |
| `instrument:raw:global_explorer_rov` | null | 1 | Global Explorer ROV | 10.1016/j.epsl.2020.116411 |
| `instrument:raw:gpc_columns` | null | 1 | GPC columns | 10.1021/acs.energyfuels.6b02899 |
| `instrument:raw:gpc_icp_hrms` | null | 1 | GPC-ICP-HRMS | 10.1021/acs.energyfuels.3c00856 |
| `instrument:raw:graphite_electrode_arc_process` | null | 1 | graphite electrode arc process | 10.1002/hlca.201900046 |
| `instrument:raw:hach_dr6000_uv_vis_spectrophotometer` | null | 1 | Hach DR6000 UV Vis spectrophotometer | 10.1016/j.jenvman.2023.119719 |
| `instrument:raw:handheld_fluorometer_multispeq_v_2_0` | null | 1 | handheld fluorometer MultiSpeQ V 2.0 | 10.1186/s40538-025-00789-9 |
| `instrument:raw:headspace_gas_chromatography` | null | 1 | headspace gas chromatography | 10.3389/feart.2020.552731 |
| `instrument:raw:high_purity_germanium_spectrometer` | null | 1 | high-purity Germanium (HPGe) γ -spectrometer | 10.1016/j.palaeo.2025.112798 |
| `instrument:raw:high_temperature_combustion` | null | 1 | high-temperature combustion | 10.1002/lom3.10558 |
| `instrument:raw:high_temperature_elemental_analyser` | null | 1 | high temperature elemental analyser (Thermo Fisher Flash 2000 HT EA) | 10.1016/j.watres.2019.115201 |
| `instrument:raw:high_toc_ii` | null | 1 | High TOC II | 10.1038/s43247-022-00407-8 |
| `instrument:raw:hitachi_ht7800` | null | 1 | Hitachi HT7800 | 10.1021/acs.est.2c05145 |
| `instrument:raw:horiba_aqualog_3d_fluorometer` | null | 1 | Horiba Aqualog 3D fluorometer | 10.1016/j.orggeochem.2020.104164 |
| `instrument:raw:horiba_aqualog_uv_800_c` | null | 1 | Horiba Aqualog-UV-800-C | 10.1029/2017JG004327; 10.1029/2021JG006516 |
| `instrument:raw:horiba_fluoromax_4` | null | 1 | Horiba FluoroMax-4 | 10.1021/acs.est.6b05126 |
| `instrument:raw:horiba_jobin_yvon_fluoromax_4_spectrofluorometer` | null | 1 | Horiba Jobin-Yvon Fluoromax-4 Spectrofluorometer | 10.1007/s10533-018-00534-5 |
| `instrument:raw:horiba_jobin_yvon_labram_hr` | null | 1 | Horiba Jobin Yvon LabRAM HR | 10.1021/acs.est.8b06861 |
| `instrument:raw:horiba_scienti_c_aqualog` | null | 1 | Horiba Scienti  c Aqualog | 10.1039/D2EM00184E |
| `instrument:raw:horiba_scientific_aqualog_46` | null | 1 | Horiba Scientific Aqualog 46 | 10.1021/acs.est.3c01782 |
| `instrument:raw:horiba_scientific_aqualog_benchtop_fl_uorometer` | null | 1 | Horiba Scientific Aqualog benchtop fl uorometer | 10.1021/acs.energyfuels.7b00490 |
| `instrument:raw:horiba_w_23xd_water_quality_monitoring_system` | null | 1 | Horiba W-23XD Water Quality Monitoring System | 10.5194/bg-15-6637-2018 |
| `instrument:raw:hot_block` | null | 1 | hot block (Environmental Express) | 10.1016/j.scitotenv.2023.167382 |
| `instrument:raw:hplc3` | null | 1 | HPLC3 | 10.1021/acs.energyfuels.7b02589 |
| `instrument:raw:icp_hr_ms` | null | 1 | ICP HR MS | 10.1021/acs.energyfuels.6b02899 |
| `instrument:raw:icp_oes` | null | 1 | ICP-OES | 10.1021/acs.energyfuels.3c01462 |
| `instrument:raw:icr_instrument` | null | 1 | ICR instrument | 10.1002/mas.21666 |
| `instrument:raw:icr_mass_analyzer` | null | 1 | ICR mass analyzer | 10.1021/acs.jproteome.6b00696 |
| `instrument:raw:illumina_hiseq` | null | 1 | Illumina HiSeq | 10.3389/fmicb.2020.01753 |
| `instrument:raw:illumina_platform` | null | 1 | Illumina platform | 10.1038/s41598-024-79780-7 |
| `instrument:raw:in_house_fabricated_analytical_column` | null | 1 | in-house-fabricated analytical column | 10.1021/acs.jproteome.0c00303 |
| `instrument:raw:jemarm200cf` | null | 1 | JEMARM200cF | 10.1021/acsestwater.4c00588 |
| `instrument:raw:jeol_jsm_6500f` | null | 1 | Jeol JSM-6500F | 10.1038/s43247-022-00407-8 |
| `instrument:raw:jobin_yvon_horiba_fluoromax_3` | null | 1 | Jobin-Yvon Horiba Fluoromax-3 | 10.1002/2016JG003431 |
| `instrument:raw:jobin_yvon_spex_fluoromax_4_spectrometer` | null | 1 | Jobin Yvon SPEX Fluoromax-4 spectrometer | 10.1016/j.gca.2016.05.015 |
| `instrument:raw:jsm_7100f` | null | 1 | JSM 7100F | 10.1021/acsomega.0c00566 |
| `instrument:raw:kinexus_pro` | null | 1 | Kinexus-Pro | 10.1063/5.0287657 |
| `instrument:raw:kintek_rqf_3_rapid_quench_flow` | null | 1 | KinTek RQF-3 Rapid Quench-Flow | 10.1021/acs.biochem.8b00022 |
| `instrument:raw:kongsberg_em2000_multibeam_echosounder` | null | 1 | Kongsberg EM2000 multibeam echosounder | 10.1016/j.epsl.2020.116411 |
| `instrument:raw:kongsberg_geoacoustics_subbottom_profiler` | null | 1 | Kongsberg GeoAcoustics subbottom profiler | 10.1016/j.epsl.2020.116411 |
| `instrument:raw:lachat_flow_injection_analyser` | null | 1 | Lachat flow injection analyser | 10.1016/j.watres.2019.115201 |
| `instrument:raw:lambda_35_uv_vis_spectrophotometer` | null | 1 | Lambda 35 UV/Vis spectrophotometer | 10.1016/j.orggeochem.2018.03.005 |
| `instrument:raw:lc_ocd` | null | 1 | LC-OCD | 10.1038/s41467-022-29711-9 |
| `instrument:raw:leco` | null | 1 | LECO | 10.1021/acsomega.0c00566 |
| `instrument:raw:leco_gc_3_gc` | null | 1 | LECO GC 3 GC | 10.1016/j.isci.2022.104916 |
| `instrument:raw:leco_pegasus_4d_system` | null | 1 | Leco Pegasus 4D system | 10.1021/acs.energyfuels.7b00865; 10.1021/acs.energyfuels.8b00596 |
| `instrument:raw:leco_pegasus_gc_3_gc_hrt` | null | 1 | LECO Pegasus GC 3 GC-HRT | 10.1016/j.isci.2022.104916 |
| `instrument:raw:lgr_dlt_100` | null | 1 | LGR DLT-100 | 10.1016/j.scitotenv.2019.01.220 |
| `instrument:raw:linear_rf_ion_trap` | null | 1 | linear RF ion trap | 10.1021/jasms.4c00261 |
| `instrument:raw:mat253_plus` | null | 1 | MAT253 plus | 10.1016/j.watres.2023.120808 |
| `instrument:raw:mcr_302_rheometer` | null | 1 | MCR 302 rheometer | 10.1021/acs.energyfuels.6b02897 |
| `instrument:raw:metrohm_881_compact_ic_pro` | null | 1 | Metrohm 881 Compact IC pro | 10.3389/fmicb.2020.01753 |
| `instrument:raw:metrohm_compact_ic_flex` | null | 1 | Metrohm Compact IC Flex | 10.1029/2022JG006852 |
| `instrument:raw:microchannel` | null | 1 | microchannel | 10.1021/acs.energyfuels.8b03835 |
| `instrument:raw:microtox_model_500_analyzer` | null | 1 | Microtox model 500 analyzer | 10.1021/acs.energyfuels.4c03951; 10.1021/acs.est.2c00582 |
| `instrument:raw:mitsubishi_tn2100_v_analyzer` | null | 1 | Mitsubishi TN2100 V analyzer | 10.1021/acs.energyfuels.3c02599 |
| `instrument:raw:model_6725_semi_micro_bomb_calorimeter` | null | 1 | model 6725 semi-micro bomb calorimeter | 10.3389/fsufs.2021.658592 |
| `instrument:raw:modular_icr_data_acquisition_system` | null | 1 | modular ICR data acquisition system (PREDATOR) | 10.1021/acs.energyfuels.9b04288 |
| `instrument:raw:multimode_viii` | null | 1 | MultiMode VIII (BRUKER) | 10.1021/acs.energyfuels.0c02687 |
| `instrument:raw:n_a` | null | 1 | N/A | 10.1021/acs.est.7b05513 |
| `instrument:raw:nanodrop_1000` | null | 1 | Nanodrop 1000 | 10.1038/s43247-022-00407-8 |
| `instrument:raw:nanodrop_2000_uv_vis_spectrophotometer` | null | 1 | NanoDrop 2000 UV-vis spectrophotometer | 10.1021/acs.energyfuels.1c02642 |
| `instrument:raw:nicolet_6700_ftir_from_thermo` | null | 1 | Nicolet 6700 FTIR from Thermo | 10.1089/ast.2022.0021 |
| `instrument:raw:nicolet_is5` | null | 1 | Nicolet iS5 (Thermo Fisher Scientific) | 10.1021/jp503413s |
| `instrument:raw:nicolet_is50_ft_ir_spectrophotometer` | null | 1 | Nicolet IS50 FT-IR spectrophotometer | 10.1016/j.jenvman.2023.119719 |
| `instrument:raw:nicolet_is50_ftir_spectrometer` | null | 1 | Nicolet iS50 FTIR spectrometer | 10.1016/j.scitotenv.2023.167382 |
| `instrument:raw:nist_calibrated_mitutoyo_micrometer` | null | 1 | NIST-calibrated Mitutoyo micrometer | 10.1021/acs.est.1c02272 |
| `instrument:raw:nova_2000` | null | 1 | Nova 2000 | 10.1038/s41467-017-01123-0 |
| `instrument:raw:novaseq6000_platform` | null | 1 | NovaSEQ6000 platform | 10.1039/D2EM00184E |
| `instrument:raw:o_i_analytical_model_1030_total_organic_carbon_analyzer` | null | 1 | O.I. Analytical Model 1030 Total Organic Carbon Analyzer | 10.1016/j.gca.2020.01.022 |
| `instrument:raw:o_i_analytical_model_700` | null | 1 | O.I. Analytical Model 700 | 10.1002/2016JG003431 |
| `instrument:raw:ocean_optics_uv_visible_light_absorbance_spectrophotome` | null | 1 | Ocean Optics UV-visible light absorbance spectrophotometer | 10.1029/2024JG008233 |
| `instrument:raw:oceanographic_instrumentation` | null | 1 | Oceanographic instrumentation | 10.1038/s43017-020-0046-x |
| `instrument:raw:oi_analytical_four_channel_rapid_flow_analyzer` | null | 1 | OI Analytical four-channel Rapid Flow Analyzer | 10.1007/s00027-017-0540-5 |
| `instrument:raw:open_cylindrical_ion_trap` | null | 1 | open cylindrical ion trap | 10.1038/ncomms1853 |
| `instrument:raw:open_cylindrical_penning_ion_trap` | null | 1 | open cylindrical penning ion trap | 10.1021/acs.energyfuels.9b00469 |
| `instrument:raw:packed_columns_or_trayed_towers` | null | 1 | packed columns or trayed towers | 10.1016/j.jece.2021.106255 |
| `instrument:raw:pegasus_gc_hrt_4d` | null | 1 | Pegasus GC-HRT 4D | 10.1021/acs.molpharmaceut.5c00679 |
| `instrument:raw:pegasus_gchrt_4d` | null | 1 | Pegasus GCHRT 4D | 10.1021/acs.analchem.4c01288 |
| `instrument:raw:perkin_elmer_nexion_300d` | null | 1 | Perkin Elmer NexION 300D | 10.1038/s41467-022-29711-9 |
| `instrument:raw:perkin_elmer_optima_7300_inductively_coupled_plasma_opt` | null | 1 | Perkin Elmer Optima 7300 inductively coupled plasma (ICP) optical emission spectrometer | 10.1016/j.gca.2020.01.022 |
| `instrument:raw:perkin_elmer_quantulus_tm` | null | 1 | Perkin Elmer Quantulus TM | 10.1016/j.gca.2020.01.022 |
| `instrument:raw:perkin_elmer_spectrum_two_infrared_spectrometer` | null | 1 | Perkin-Elmer Spectrum Two Infrared Spectrometer | 10.3389/fpls.2021.660224 |
| `instrument:raw:perkinelmer_frontier_ftir_spectrometer` | null | 1 | PerkinElmer Frontier FTIR spectrometer | 10.1021/acs.energyfuels.3c05200 |
| `instrument:raw:perkinelmer_lambda_650s` | null | 1 | PerkinElmer Lambda 650s | 10.1021/acs.est.1c02272 |
| `instrument:raw:perkinelmer_spectrum_100_atr_ft_ir_spectrometer` | null | 1 | PerkinElmer Spectrum 100 ATR FT-IR spectrometer | 10.1021/acs.energyfuels.7b00865; 10.1021/acs.energyfuels.8b00596 |
| `instrument:raw:photon_technology_international_fluorescence_spectromet` | null | 1 | Photon Technology International (PTI) fluorescence spectrometer | 10.1021/acs.biochem.8b00733 |
| `instrument:raw:picarro_2140_i_wavelength_scanned_cavity_ring_down_spec` | null | 1 | Picarro 2140-i Wavelength-Scanned Cavity Ring Down Spectrometer | 10.1029/2022JG007188 |
| `instrument:raw:picarro_g2101_i_isotopic_co2_cavity_ring_down_spectrome` | null | 1 | Picarro G2101-i Isotopic CO2 cavity ring down spectrometer (CRDS) | 10.1038/s41467-023-41900-8 |
| `instrument:raw:picarro_inc_l2130i_liquid_water_cavity_ring_down_spectr` | null | 1 | Picarro Inc. L2130i liquid water cavity ring-down spectroscopy | 10.1029/2022GB007495 |
| `instrument:raw:poros_gopure_50_d_resin_functionalized_with_dimethylami` | null | 1 | POROS GoPure 50 D resin functionalized with dimethylaminopropyl groups (Thermo Fisher Scientific) | 10.1021/acs.analchem.5c05562 |
| `instrument:raw:quaatro39_continuous_segmented_flow_analyzer` | null | 1 | QuAAtro39 continuous segmented flow analyzer | 10.1029/2020GB006719 |
| `instrument:raw:quantachrome_autosorb_iq_adsorption_chemisorption_syste` | null | 1 | Quantachrome Autosorb iQ adsorption/chemisorption system | 10.1016/j.isci.2022.104916 |
| `instrument:raw:quantachrome_autosorb_iq_tpx` | null | 1 | Quantachrome Autosorb iQ TPX | 10.1016/j.isci.2022.104916; 10.1039/d0se01662d |
| `instrument:raw:qubit_2_0_fluorometer` | null | 1 | Qubit 2.0 fluorometer | 10.1126/sciadv.abn0035 |
| `instrument:raw:qubit_3_fluorometer` | null | 1 | Qubit 3 fluorometer | 10.1029/2022JG006852 |
| `instrument:raw:quenching_column` | null | 1 | quenching column | 10.1016/j.jece.2021.106255 |
| `instrument:raw:rigaku_automatic_instrument` | null | 1 | Rigaku automatic instrument (Geigerflex) | 10.1039/d0se01662d |
| `instrument:raw:scanning_electron_microscopy` | null | 1 | Scanning electron microscopy (SEM) | 10.1038/s41467-017-01123-0 |
| `instrument:raw:seal_aq2` | null | 1 | Seal AQ2 (Seal Analytical) | 10.1038/s41598-020-65520-0 |
| `instrument:raw:sebia_hydrasys_scan_2` | null | 1 | Sebia Hydrasys Scan 2 | 10.1515/cclm-2020-1072 |
| `instrument:raw:semi_micro_calorimeter` | null | 1 | semi-micro calorimeter | 10.1039/d0se01662d |
| `instrument:raw:series_ii_2400_elemental_analyzer` | null | 1 | Series II 2400 elemental analyzer | 10.1021/acs.energyfuels.1c01336; 10.3389/fsufs.2021.658592 |
| `instrument:raw:shimadzu_5000a_toc_analyzer` | null | 1 | Shimadzu 5000A TOC analyzer | 10.1021/acs.est.1c02272 |
| `instrument:raw:shimadzu_ft_ir_spectrometer` | null | 1 | Shimadzu FT-IR spectrometer | 10.26434/chemrxiv-2022-0k0jg |
| `instrument:raw:shimadzu_gc17a_qp5050a` | null | 1 | Shimadzu GC17A/QP5050A | 10.1007/s12010-019-03055-5; 10.1007/s12155-018-9919-y; 10.1021/acsomega.0c00566 |
| `instrument:raw:shimadzu_high_temperature_catalytic_oxidation_total_oc_` | null | 1 | Shimadzu high-temperature catalytic oxidation total OC analyzer (TOC-L CPH) | 10.1029/2024JG008445 |
| `instrument:raw:shimadzu_iraffinity_1s` | null | 1 | Shimadzu IRAffinity-1S | 10.1063/5.0287657 |
| `instrument:raw:shimadzu_japan` | null | 1 | Shimadzu, Japan | 10.21203/rs.3.rs-691992/v1 |
| `instrument:raw:shimadzu_photo_diode_array_detector` | null | 1 | Shimadzu photo diode array detector | 10.1038/s41598-020-65520-0 |
| `instrument:raw:shimadzu_qp_2010_se` | null | 1 | Shimadzu QP 2010 SE | 10.1039/D4SE01294A |
| `instrument:raw:shimadzu_toc_l_chp` | null | 1 | Shimadzu TOC-L CHP | 10.1002/lno.11417; 10.1029/2020JG005988 |
| `instrument:raw:shimadzu_toc_l_cph_cpn_analyzer` | null | 1 | Shimadzu TOC-L CPH/CPN analyzer | 10.1029/2024GB008359 |
| `instrument:raw:shimadzu_toc_l_csh_csn_analyzer` | null | 1 | Shimadzu TOC-L CSH/CSN analyzer | 10.1029/2022JG007027 |
| `instrument:raw:shimadzu_toc_l_high_temperature_catalytic_combustion_an` | null | 1 | Shimadzu™ TOC-L high temperature catalytic combustion analyzer | 10.1029/2022JG006852 |
| `instrument:raw:shimadzu_toc_lcph_cpn` | null | 1 | Shimadzu TOC-LCPH/CPN | 10.1029/2024GB008212 |
| `instrument:raw:shimadzu_toc_lcsh` | null | 1 | Shimadzu TOC-LCSH | 10.5194/bg-22-41-2025 |
| `instrument:raw:shimadzu_toc_lcsn` | null | 1 | Shimadzu TOC-LCSN | 10.1021/acs.est.3c06678 |
| `instrument:raw:shimadzu_toc_tn_analyzer` | null | 1 | Shimadzu TOC/TN analyzer | 10.1029/2020GB006871 |
| `instrument:raw:shimadzu_toc_v_analyzer` | null | 1 | Shimadzu TOC-V analyzer | 10.1007/s10533-023-01101-3 |
| `instrument:raw:shimadzu_toc_v_cpn_analyser` | null | 1 | Shimadzu TOC-V CPN Analyser | 10.1016/j.orggeochem.2024.104886 |
| `instrument:raw:shimadzu_toc_v_ws_analyzer` | null | 1 | Shimadzu TOC-V WS analyzer | 10.1021/acs.energyfuels.4c03951 |
| `instrument:raw:shimadzu_toc_vcsh_total_organic_carbon_analyzer` | null | 1 | Shimadzu TOC-VCSH Total Organic Carbon Analyzer | 10.1039/d4em00023d |
| `instrument:raw:shimadzu_toc_vcsn` | null | 1 | Shimadzu TOC Vcsn | 10.1021/acs.est.8b00016 |
| `instrument:raw:shimadzu_tocl_cph_analyzer` | null | 1 | Shimadzu TOCL CPH analyzer | 10.3389/fmars.2021.781580 |
| `instrument:raw:shimadzu_toclc_tn_analyzer` | null | 1 | Shimadzu TOCLC/TN analyzer | 10.1007/s10533-022-00906-y |
| `instrument:raw:shimadzu_toclcph_analyzer` | null | 1 | Shimadzu TOCLCPH analyzer | 10.5194/tc-19-2769-2025 |
| `instrument:raw:shimadzu_tocv_csh_analyzer` | null | 1 | Shimadzu TOCV CSH analyzer | 10.1021/acs.est.5c08206 |
| `instrument:raw:shimadzu_uv_1601pc` | null | 1 | Shimadzu UV-1601PC | 10.1021/acs.est.7b01914 |
| `instrument:raw:sievers_innovox_toc_analyzer` | null | 1 | Sievers InnovOx TOC Analyzer | 10.1021/acs.est.0c01997 |
| `instrument:raw:sm_21` | null | 1 | SM-21 | 10.1021/acs.est.8b01788 |
| `instrument:raw:specim_single_core_scanner` | null | 1 | Specim Single Core Scanner | 10.2138/gselements.18.2.107 |
| `instrument:raw:spectrofluorometer` | null | 1 | spectrofluorometer | 10.1029/2020GB006719 |
| `instrument:raw:spectrum_two_ft_ir_spectrophotometer` | null | 1 | Spectrum Two FT-IR spectrophotometer | 10.1021/acs.energyfuels.1c01336 |
| `instrument:raw:spectrum_two_ftir_spectrophotometer` | null | 1 | Spectrum Two FTIR spectrophotometer | 10.1016/j.indcrop.2020.112311 |
| `instrument:raw:sri_8610c` | null | 1 | SRI 8610C | 10.1007/s11356-024-35140-6 |
| `instrument:raw:stelar_spinmaster_ffc_2000` | null | 1 | Stelar SpinMaster FFC-2000 | 10.1038/s41467-017-01123-0 |
| `instrument:raw:storm_820` | null | 1 | Storm 820 | 10.1021/acs.biochem.8b00766 |
| `instrument:raw:subglacial_underwater_reconnaissance_flow_through_fluor` | null | 1 | Subglacial Underwater Reconnaissance Flow-through Fluorescence Spectrometer (SURFFS) | 10.1029/2022JG006852 |
| `instrument:raw:superdex_200_increase_10_300_gl` | null | 1 | Superdex 200 Increase 10/300 GL | 10.1016/j.str.2017.08.002 |
| `instrument:raw:surffs` | null | 1 | SURFFS | 10.1029/2022JG006852 |
| `instrument:raw:synrad_48_2` | null | 1 | Synrad 48-2 | 10.1039/D0EM00390E |
| `instrument:raw:tektronix_mdo3014` | null | 1 | Tektronix MDO3014 | 10.1007/s13361-019-02290-8 |
| `instrument:raw:tg_209` | null | 1 | TG 209 | 10.1021/acs.analchem.4c01288 |
| `instrument:raw:thermo_commercial_station` | null | 1 | Thermo commercial station | 10.1016/j.watres.2025.125251 |
| `instrument:raw:thermo_finnigan_mat_deltaplus` | null | 1 | Thermo Finnigan MAT Deltaplus | 10.1016/j.scitotenv.2019.01.220 |
| `instrument:raw:thermo_fisher_ea_isolink_cnsoh_elemental_analyzer` | null | 1 | Thermo Fisher EA-Isolink-CNSOH elemental analyzer | 10.1029/2024JG008233 |
| `instrument:raw:thermo_fisher_ion_maxx_appi_source` | null | 1 | Thermo-Fisher Ion Maxx APPI source | 10.1021/acs.energyfuels.7b02859 |
| `instrument:raw:thermo_fisher_scientific` | null | 1 | Thermo Fisher Scientific | 10.1016/j.jmsacl.2023.01.004; 10.1373/clinchem.2018.295766 |
| `instrument:raw:thermo_fisher_scientific_inc_san_jose_ca` | null | 1 | Thermo-Fisher Scientific, Inc., San Jose, CA | 10.1021/acs.est.0c05206 |
| `instrument:raw:thermo_scientific_element_xrsector_fi_eld_icp_hrms` | null | 1 | Thermo Scientific Element XRsector fi eld ICP-HRMS | 10.1021/acs.energyfuels.0c02158 |
| `instrument:raw:thermo_scientific_evolution_300_spectrophotometer` | null | 1 | Thermo Scientific Evolution 300 spectrophotometer | 10.1016/j.orggeochem.2016.11.004 |
| `instrument:raw:thermo_scientific_flash_2000_element_analyzer` | null | 1 | Thermo Scientific FLASH 2000 element analyzer | 10.1038/s43247-024-01832-7 |
| `instrument:raw:thermo_scientific_gas_bench_ii` | null | 1 | Thermo Scientific Gas Bench II | 10.1002/lno.12436 |
| `instrument:raw:thermo_trace_1310_gc` | null | 1 | Thermo Trace 1310 GC | 10.1021/acs.est.3c09797 |
| `instrument:raw:thermofisher_dualbeam_helios_g4_sem_microscope` | null | 1 | ThermoFisher Dualbeam Helios G4 SEM microscope | 10.1016/j.seh.2024.100114 |
| `instrument:raw:third_octopole` | null | 1 | third octopole | 10.1038/ncomms1853 |
| `instrument:raw:toc_analyzer` | null | 1 | TOC analyzer | 10.1016/j.palaeo.2025.112798 |
| `instrument:raw:toc_v_wp_total_organic_carbon_analyzer` | null | 1 | TOC-V WP total organic carbon analyzer | 10.1016/j.scitotenv.2020.142411 |
| `instrument:raw:tocvcpn_total_organic_c_n_analyzer` | null | 1 | TOCVCPN total organic C/N analyzer | 10.1016/j.seh.2023.100023 |
| `instrument:raw:total_organic_carbon_analyzer` | null | 1 | total organic carbon analyzer | 10.1039/d0se01662d |
| `instrument:raw:transmission_electron_microscope_philips_tecnai_10` | null | 1 | Transmission Electron Microscope (TEM) Philips Tecnai 10 | 10.1186/s12934-023-02113-2 |
| `instrument:raw:turbiscan_lab` | null | 1 | Turbiscan Lab | 10.1021/acs.energyfuels.7b02859 |
| `instrument:raw:ultimate_3000_autosampler` | null | 1 | UltiMate 3000 autosampler | 10.3390/pr8111472 |
| `instrument:raw:ultimate_3000_dionex_highperformance_liquid_chromatogra` | null | 1 | UltiMate 3000 Dionex highperformance liquid chromatography system | 10.1021/acs.energyfuels.4c02496 |
| `instrument:raw:ultimate_3000_microflow_pump` | null | 1 | UltiMate 3000 microflow pump | 10.3390/pr8111472 |
| `instrument:raw:uv_2501_pc_shimadzu` | null | 1 | UV-2501 PC, Shimadzu | 10.1021/acsestwater.4c00588 |
| `instrument:raw:uv_3600_spectrophotometer` | null | 1 | UV-3600 spectrophotometer | 10.1016/j.watres.2023.119812; 10.1016/j.watres.2023.120808 |
| `instrument:raw:varian_3400_gas_chromatograph` | null | 1 | Varian 3400 gas chromatograph | 10.1038/s41467-023-41900-8 |
| `instrument:raw:varian_cp_3800` | null | 1 | Varian CP-3800 | 10.1016/j.biortech.2020.123454 |
| `instrument:raw:varian_gas_chromatograph` | null | 1 | Varian gas chromatograph | 10.1126/sciadv.abn0035 |
| `instrument:raw:vario_micro_cube_elemental_analyzer` | null | 1 | Vario Micro Cube elemental analyzer | 10.1021/acs.energyfuels.2c04274 |
| `instrument:raw:vcph_model_toc_analyzer` | null | 1 | VCPH model TOC analyzer | 10.1016/j.orggeochem.2016.11.004 |
| `instrument:raw:vertex_80_v` | null | 1 | Vertex 80 v (Bruker) | 10.1038/s41467-017-01123-0 |
| `instrument:raw:video_plankton_recorder` | null | 1 | Video Plankton Recorder (VPR) | 10.1038/s43017-020-0046-x |
| `instrument:raw:voyager_de_pro` | null | 1 | Voyager-DE PRO | 10.1021/jp503413s |
| `instrument:raw:vp_detectors` | null | 1 | VP detectors | 10.21203/rs.3.rs-691992/v1 |
| `instrument:raw:vp_itc_microcalorimeter` | null | 1 | VP-ITC microcalorimeter | 10.1016/j.str.2017.08.002 |
| `instrument:raw:waters_gct_premier` | null | 1 | Waters GCT Premier | 10.1021/acs.energyfuels.8b00596 |
| `instrument:raw:winkler_titration_system` | null | 1 | Winkler titration system | 10.1126/sciadv.abn0035 |
| `instrument:raw:x_ray_powder_diffractometer` | null | 1 | X-ray powder diffractometer | 10.1016/j.isci.2022.104916 |
| `instrument:raw:xplora` | null | 1 | Xplora | 10.1039/d0se01662d |
| `instrument:raw:ysi_6600_multiprobe` | null | 1 | YSI 6600 multiprobe | 10.1007/s00027-017-0540-5 |
| `instrument:raw:ysi_6600_v2_multisensor_sonde` | null | 1 | YSI 6600 V2 multisensor sonde | 10.1021/acs.est.8b02163 |
| `instrument:raw:ysi_exo2_multi_parameter_water_quality_sonde` | null | 1 | YSI EXO2 multi-parameter water quality sonde | 10.1016/j.scitotenv.2019.01.220 |
| `instrument:raw:ysi_pro_plus_sonde` | null | 1 | YSI Pro Plus sonde | 10.1002/lno.11385 |
| `instrument:raw:zeiss_axio_observer_7_confocal_microscope` | null | 1 | Zeiss Axio Observer 7 confocal microscope | 10.1016/j.jbc.2022.102768 |
| `instrument:raw:zeiss_sigma_sem` | null | 1 | Zeiss Sigma SEM | 10.1038/s41467-017-01123-0 |
| `instrument:raw:zorbax_sb_c18_column` | null | 1 | Zorbax SB-C18 column | 10.1021/jasms.4c00380 |

## AUTO-MINTED — NMR (NMRCV)  [8 nodes]
| node | ontology_source | #strings | example string(s) | DOI(s) |
|---|---|---|---|---|
| `instrument:raw:bruker_avance` | NMRCV | 2 | Bruker AVANCE · Bruker Avance | 10.1021/acs.jproteome.7b00457; 10.3389/fpls.2021.660224 |
| `instrument:raw:bruker_biospin_avance_iii_400_mhz_wb` | NMRCV | 2 | Bruker AVANCE 400 MHz · Bruker BioSpin Avance III 400 MHz WB | 10.1002/2017JG004343; 10.1021/acs.energyfuels.4c01959 |
| `instrument:raw:1_t_solid_state_nmr_spectrometer` | NMRCV | 1 | 1 T solid-state NMR spectrometer | 10.1021/acs.analchem.1c03058 |
| `instrument:raw:600_mhz_14` | NMRCV | 1 | 600 MHz/14 | 10.1021/acs.analchem.1c03058 |
| `instrument:raw:a_600_mhz_14_1_t_solid_state_nmr_spectrometer` | NMRCV | 1 | a 600 MHz/14.1 T solid-state NMR spectrometer | 10.1021/acs.analchem.1c03058 |
| `instrument:raw:bruker_avance_iii_600_mhz` | NMRCV | 1 | Bruker Avance III 600 MHz | 10.1038/s41467-017-01123-0 |
| `instrument:raw:bruker_biospin_avance_iii_500_mhz_nmr_spectrometer` | NMRCV | 1 | Bruker BioSpin Avance III 500 MHz NMR spectrometer | 10.1016/j.seh.2025.100148 |
| `instrument:raw:bruker_neo_avance_400` | NMRCV | 1 | Bruker Neo Avance 400 | 10.1039/D4SE01294A |

## CONFIRM-RESOLVE — fuzzy proposals to existing 7 nodes  [78]
| String | → existing node | reason | DOI(s) | DECISION |
|---|---|---|---|---|
| (+) APPI 21 T FT-ICR MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.energyfuels.1c02107 | **confirm** |
| 21 T Fourier transform ion cyclotron resonance mass spectrometer (FT-ICR MS) | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.biochem.8b00022 | **confirm** |
| 21 T FT -ICR mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.analchem.8b03294 | **confirm** |
| 21 t FT -ICR MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1029/2018JG004910 | **confirm** |
| 21 T FT-ICR | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.molpharmaceut.5c00679; 10.1101/455527 | **confirm** |
| 21 T FT-ICR mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1007/s13361-017-1702-3; 10.1016/j.gca.2025.08.041; 10.1016/j.jbc.2022.102768 (+7) | **confirm** |
| 21 T FT-ICR Mass Spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.energyfuels.0c01564; 10.1021/acs.energyfuels.1c02107 | **confirm** |
| 21 T FT-ICR MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1002/lol2.10388; 10.1007/s10533-019-00619-9; 10.1016/j.seh.2023.100023 (+18) | **confirm** |
| 21 T FT-ICR MS (Bruker) | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1016/j.scitotenv.2019.01.220 | **confirm** |
| 21 T FT-ICR MS system | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.analchem.0c01064; 10.1021/acs.analchem.1c00847 | **confirm** |
| 21 T FT-ICR system | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.analchem.1c00847 | **confirm** |
| 21 T FT-ICR-MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.est.3c00771 | **confirm** |
| 21 T FTICR | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.analchem.3c00393 | **confirm** |
| 21 T FTICR mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.energyfuels.1c02107 | **confirm** |
| 21 T hybrid linear ion trap FT-ICR MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.est.3c06678 | **confirm** |
| 21 tesla (T) FTICR mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 tesla'+ICR) | 10.1021/acs.analchem.5c06165 | **confirm** |
| 21 tesla (T) FTICR-MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 tesla'+ICR) | 10.1021/acs.est.1c02272 | **confirm** |
| 21 Tesla Fourier Transform - Ion Cyclotron Resonance | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 tesla'+ICR) | 10.1101/455527 | **confirm** |
| 21 Tesla Fourier transform ion cyclotron resonance | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 tesla'+ICR) | 10.21037/atm.2019.12.67 | **confirm** |
| 21 Tesla Fourier transform ion cyclotron resonance -mass spectrometry (FT ICR-MS) | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 tesla'+ICR) | 10.1016/j.scitotenv.2023.167382 | **confirm** |
| 21 tesla Fourier transform ion cyclotron resonance mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 tesla'+ICR) | 10.1002/mas.21666; 10.3389/feart.2019.00275 | **confirm** |
| 21 Tesla Fourier transform ion cyclotron resonance mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 tesla'+ICR) | 10.1073/pnas.1714597115; 10.1073/pnas.2504769122; 10.1089/ast.2022.0021 (+1) | **confirm** |
| 21 Tesla FT -ICR mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 tesla'+ICR) | 10.1073/pnas.2504769122 | **confirm** |
| 21 Tesla FT-ICR | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 tesla'+ICR) | 10.1007/s13361-017-1652-9 | **confirm** |
| 21 Tesla FT-ICR mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 tesla'+ICR) | 10.1101/455527 | **confirm** |
| 21 Tesla FT-ICR MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 tesla'+ICR) | 10.1007/s10533-023-01101-3; 10.1016/j.scitotenv.2018.05.180 | **confirm** |
| 21 tesla FT-ICR MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 tesla'+ICR) | 10.1021/acs.est.3c01347; 10.1029/2021JG006516; 10.1039/D2EM00184E | **confirm** |
| 21 Tesla FT-ICRMS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 tesla'+ICR) | 10.1002/lno.12436 | **confirm** |
| 21 Tesla FTICR MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 tesla'+ICR) | 10.1016/j.orggeochem.2024.104886 | **confirm** |
| 21 Tesla Hybrid FT-ICR Mass Spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 tesla'+ICR) | 10.1007/s13361-015-1182-2 | **confirm** |
| 21-T FT-ICR MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21-t'+ICR) | 10.1016/j.palaeo.2025.112798; 10.1029/2020JG005804 | **confirm** |
| 21-tesla FT-ICR MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21-tesla'+ICR) | 10.1007/s10533-021-00852-1; 10.1016/j.watres.2023.119812; 10.1021/acs.energyfuels.4c01954 | **confirm** |
| 21-Tesla FT-ICR MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21-tesla'+ICR) | 10.1038/s41561-019-0384-9 | **confirm** |
| 21T Fourier transform ion cyclotron resonance mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21t'+ICR) | 10.1021/acs.est.5c07016 | **confirm** |
| 21T FT-ICR | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21t'+ICR) | 10.1038/s43247-022-00407-8; 10.1515/cclm-2020-1072 | **confirm** |
| 21T FT-ICR mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21t'+ICR) | 10.1021/acs.energyfuels.4c02496; 10.3390/pr11102883 | **confirm** |
| 21T FT-ICR MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21t'+ICR) | 10.1002/pca.70001 | **confirm** |
| 21T FT-ICR-MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21t'+ICR) | 10.1002/pca.70001 | **confirm** |
| 21tesla FT-ICR MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21tesla'+ICR) | 10.1111/gcb.14889 | **confirm** |
| custom build 21 T FT-ICR-MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1039/c8en00018b | **confirm** |
| custom hybrid dual-cell linear radiofrequency (RF) ion trap 21 T Fourier transform-ion cyclotron resonance mass spectrometer (FT-ICR MS) | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.analchem.0c01064 | **confirm** |
| custom-built 21 T Fourier transform ion cyclotron resonance mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.est.3c06678 | **confirm** |
| custom-built 21 T FT-ICR mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.analchem.5c02420; 10.1021/acs.energyfuels.0c03349; 10.1021/acs.energyfuels.2c02936 | **confirm** |
| custom-built 21 T FT-ICR MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.analchem.5c05562 | **confirm** |
| custom-built 21 T FTICR | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1016/j.ijms.2017.11.012 | **confirm** |
| custom-built 21 T hybrid ion-trap FTICR mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.analchem.9b04954 | **confirm** |
| custom-built 21 tesla FT-ICR MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 tesla'+ICR) | 10.1029/2020GB006709; 10.5194/bg-22-41-2025 | **confirm** |
| custom-built 21-tesla Fourier-transform ion cyclotron resonance mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21-tesla'+ICR) | 10.1038/s41467-023-41900-8 | **confirm** |
| custom-built 21-tesla FT-ICR mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21-tesla'+ICR) | 10.1021/acs.energyfuels.4c01954 | **confirm** |
| custom-built 21T FT-ICR MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21t'+ICR) | 10.1039/D4SE01294A | **confirm** |
| custom-built hybrid dual ion-trap 21 T FT-ICR mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.energyfuels.0c02158 | **confirm** |
| custom-built hybrid linear ion trap 21 T FT-ICR MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.est.5c08206; 10.1029/2024JG008233 | **confirm** |
| custom-built hybrid linear ion trap 21-T ESI FT-ICR mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21-t'+ICR) | 10.1021/acs.est.3c08123 | **confirm** |
| custom-built hybrid linear ion trap/21 T FT-ICR mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1016/j.seh.2024.100114 | **confirm** |
| custom-built Velso Pro (Thermo Scientific) 21 T FT-ICR mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1016/j.str.2017.08.002 | **confirm** |
| custom-designed 21 T FT-ICR MS | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.analchem.1c01169 | **confirm** |
| custom-designed 21T FT-ICR | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21t'+ICR) | 10.1021/acs.energyfuels.4c05674 | **confirm** |
| hybrid 21 T FT-ICR mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/jasms.2c00242 | **confirm** |
| hybrid linear ion trap -21 Tesla Fourier transform-ion cyclotron resonance mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 tesla'+ICR) | 10.1007/s13361-018-1897-y | **confirm** |
| hybrid linear ion trap 21 T FT-ICR mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 t'+ICR) | 10.1021/acs.analchem.9b04768 | **confirm** |
| Velos Pro-14.5 or 21 tesla Fourier transformion cyclotron resonance (FT-ICR) mass spectrometer | `instrument:raw:21t_icr` | 21 T FT-ICR magnet -> existing node (matched '21 tesla'+ICR) | 10.1002/pmic.201700442 | **confirm** |
| customized hybrid linear quadrupole ion trap/FT-ICR MS (LTQ-FT) | `instrument:raw:ltq_ft_ultra` | LTQ-FT signature | 10.1021/ef100149n | **confirm** |
| hybrid linear quadrupole ion trap/FT-ICR mass spectrometer (LTQ-FT) | `instrument:raw:ltq_ft_ultra` | LTQ-FT signature | 10.1002/rcm.4655 | **confirm** |
| hybrid linear quadrupole ion trap/FTICR MS (LTQ-FT) | `instrument:raw:ltq_ft_ultra` | LTQ-FT signature | 10.21203/rs.3.rs-186208/v1 | **confirm** |
| LTQ-FT Ultra FTMS | `instrument:raw:ltq_ft_ultra` | LTQ-FT signature | 10.1007/s13361-017-1702-3 | **confirm** |
| LTQ Orbitrap Elite | `instrument:raw:orbitrap_elite` | Orbitrap Elite | 10.1021/acs.energyfuels.3c04994 | **confirm** |
| modified Orbitrap Elite | `instrument:raw:orbitrap_elite` | Orbitrap Elite | 10.1007/s13361-019-02290-8 | **confirm** |
| Orbitrap Elite | `instrument:raw:orbitrap_elite` | Orbitrap Elite | 10.1021/acs.analchem.9b04855 | **confirm** |
| ThermoScientific Orbitrap Elite | `instrument:raw:orbitrap_elite` | Orbitrap Elite | 10.1002/pmic.201300438 | **confirm** |
| Fusion Lumos | `instrument:raw:orbitrap_fusion_lumos` | Orbitrap Fusion Lumos | 10.1101/455527 | **confirm** |
| Orbitrap Fusion Lumos | `instrument:raw:orbitrap_fusion_lumos` | Orbitrap Fusion Lumos | 10.1101/455527; 10.1515/cclm-2020-1072 | **confirm** |
| Orbitrap Fusion Lumos (Thermo Fisher Scientific) | `instrument:raw:orbitrap_fusion_lumos` | Orbitrap Fusion Lumos | 10.1016/j.mcpro.2024.100814 | **confirm** |
| Thermo Scientific Orbitrap Fusion Lumos | `instrument:raw:orbitrap_fusion_lumos` | Orbitrap Fusion Lumos | 10.1016/j.mcpro.2024.100814 | **confirm** |
| FTMS (Q Exactive HF, Thermo Scientific) | `instrument:raw:q_exactive_orbitrap` | Q Exactive Orbitrap | 10.1515/cclm-2020-1072 | **confirm** |
| Q Exactive HF | `instrument:raw:q_exactive_orbitrap` | Q Exactive Orbitrap | 10.1515/cclm-2020-1072 | **confirm** |
| Q Exactive HF Hybrid Quadrupole-Orbitrap Mass Spectrometer | `instrument:raw:q_exactive_orbitrap` | Q Exactive Orbitrap | 10.1016/j.jbc.2022.102768 | **confirm** |
| Q-Exactive HF BioPharma | `instrument:raw:q_exactive_orbitrap` | Q Exactive Orbitrap | 10.1016/j.jbc.2022.102768 | **confirm** |
| Q-Exactive HF Orbitrap | `instrument:raw:q_exactive_orbitrap` | Q Exactive Orbitrap | 10.1038/s43247-024-01965-9 | **confirm** |

## AUTO-REJECTED (confirm no over-drop)
| String | reason | DOI(s) |
|---|---|---|
| 300 -4000 m/z scan range | instrument SETTINGS not an instrument | 10.1007/s13361-019-02290-8 |
| instrument settings: 120,000 resolving power at m/z 400 | instrument SETTINGS not an instrument | 10.1007/s13361-019-02290-8 |
| CEOS | thermodynamic model/software (PC-SAFT/CPA/CEOS) | 10.1021/acs.energyfuels.1c01837 |
| CPA | thermodynamic model/software (PC-SAFT/CPA/CEOS) | 10.1021/acs.energyfuels.1c01837 |
| PC-SAFT | thermodynamic model/software (PC-SAFT/CPA/CEOS) | 10.1021/acs.energyfuels.1c01837 |
| BEC 1 reactor | processing/prep device (no measurement) | 10.1021/acs.est.2c05145 |
| FreeZone 12 L console tray dryer | processing/prep device (no measurement) | 10.1016/j.indcrop.2020.112311 |
| Innova 44R shaker (Eppendorf) | processing/prep device (no measurement) | 10.1186/s12934-023-02113-2 |
| Model 4572 stainless-steel batch reactor | processing/prep device (no measurement) | 10.1021/acs.energyfuels.1c01336 |
| Parr Instruments semimicro calorimeter | processing/prep device (no measurement) | 10.26434/chemrxiv-2022-0k0jg |
| Parr reactor (Model 4561) | processing/prep device (no measurement) | 10.1039/D2GC01135B |
| Thermo Scientific MaxQ 4000 orbital shaker | processing/prep device (no measurement) | 10.1021/acs.energyfuels.4c03951 |
| ThermoFisher Scientific oven | processing/prep device (no measurement) | 10.1021/jp503413s |
| fluidized bed reactor | processing/prep device (no measurement) | 10.1016/j.jece.2021.106255 |
| freeze dryer | processing/prep device (no measurement) | 10.3389/fsufs.2021.658592 |
| Bruker | vendor name only | 10.1021/acs.energyfuels.2c00840 |
| 1-T magnet spectrometer | contentless generic (ruling 1) | 10.1021/acs.energyfuels.3c05200 |
| 4 T ESI-FT mass spectrometer | contentless generic (ruling 1) | 10.1016/j.chroma.2016.10.005 |
| 9.4 T instrument | contentless generic (ruling 1) | 10.1002/jms.3345 |
| 9.4 tesla | contentless generic (ruling 1) | 10.1016/j.isci.2022.104916 |
| 9.4-T instrument | contentless generic (ruling 1) | 10.1021/ac053302y |
| High Resolution Mass Spectrometer | contentless generic (ruling 1) | 10.1021/acs.est.1c01135 |
| High-Resolution Mass Spectrometer | contentless generic (ruling 1) | 10.1021/acs.est.1c01135 |
| a 9.4-T instrument | contentless generic (ruling 1) | 10.1021/ac053302y |
| custom-built mass spectrometer | contentless generic (ruling 1) | 10.1021/acs.energyfuels.7b03204 |
| high-resolution mass spectrometer | contentless generic (ruling 1) | 10.1021/acs.energyfuels.2c02122 |
| mass spectrometer | contentless generic (ruling 1) | 10.1007/s13361-017-1702-3; 10.1021/acs.energyfuels.1c02107; 10.1073/pnas.1803866115 |

## MISROUTES → other field  [3]
| String | note | DOI(s) |
|---|---|---|
| CFX Connect ™ Real-Time PCR Detection System | method/acq mention, belongs to method/ionization field | 10.1029/2018JG004712 |
| LC-ICP-MS method | method/acq mention, belongs to method/ionization field | 10.1038/s43247-024-01965-9 |
| high-resolution mass spectrometry detection | method/acq mention, belongs to method/ionization field | 10.1021/acs.energyfuels.1c01837 |

## SKIPPED-PERIPHERALS (CV 50-54; record as Publication text later)  [20]
- APPI Ion Max source (Thermo Fisher Scientific, Inc., San Jose, CA)  (10.1021/acs.energyfuels.3c02599)
- APPI Ion Max source (Thermo-Fisher Scientific)  (10.1021/acs.analchem.4c01288)
- Advion BioSystems Nanomate  (10.1002/rcm.4655)
- Agilent 1100 HPLC system  (10.1021/acs.analchem.7b01461)
- Ä KTA Puri fi er high-performance liquid chromatography (HPLC) instrument  (10.1021/acs.biochem.8b00733)
- Dionex ICS-5000+ capillary HPLC system  (10.1038/s41467-023-41900-8)
- Dionex UltiMate 3000 Rapid Separation nanoLC  (10.1016/j.jbc.2022.102768)
- Dionex Ultimate 3000 HPLC  (10.1029/2024GB008359)
- Ion Max APPI source (Thermo Fisher Scientific)  (10.1021/acs.energyfuels.0c02654)
- Nanospray Flex ion source (Thermo Scientific)  (10.1515/cclm-2020-1072)
- Thermo Fisher Ion Max APPI source  (10.1021/acs.energyfuels.9b04288)
- Thermo-Fisher Ion Max APPI source  (10.1021/acs.energyfuels.0c02752; 10.1021/acs.energyfuels.2c00486; 10.1021/acs.energyfuels.2c01541 (+1))
- ThermoFisher Ion Max  (10.1021/acs.energyfuels.8b01765)
- UPLC-Q-TOF MS  (10.1002/lol2.10082)
- Ultimate 3000 nanoLC (Thermo Scientific)  (10.1515/cclm-2020-1072)
- Ultra Nano HPLC system  (10.1002/rcm.7783)
- Waters Acquity UPLC M-Class System  (10.1007/s13361-017-1602-6; 10.1016/j.ijms.2017.11.012; 10.1021/acs.analchem.8b03294 (+1))
- Waters UPLC-SQD2  (10.1002/pca.70001)
- nano-HPLC system (ACQUITY MClass)  (10.1021/acs.jproteome.6b00696)
- nanoHPLC system (ACQUITY M-Class)  (10.1021/acs.analchem.0c01064)
