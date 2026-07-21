# Facility / Institution — PDF extraction transform review (378-paper batch)
**STATUS — APPLIED (baked into the corpus; live in the graph).** This was a DRY RUN when
generated 2026-07-15 (original banner: *"No entity output written; 03 not run; no git"*), but
its decisions were **applied subsequently** and this doc is now a **record of what was applied**,
not a pending proposal. The §1 confirmed aliases and all **41 §2 mints** were written into the
committed `data/processed/entities/pdf_entities.jsonl`, flow through `validated/`, and load into
Neo4j as part of the **62 Institution** nodes. Verified 2026-07-21: **41/41 §2 mint identifiers
present in the loaded graph** and the §1 aliases present on their target nodes.
- **APPLIED & LOADED:** §1 (aliases), §2 (41 mints), §5 (rejects — correctly no nodes), §7
  (NHMFL/MagLab skip — CSV owns via CONDUCTED_AT, correctly not minted).
- **STILL PENDING (NOT applied):** **§4** — `facilities_mentioned_raw` Publication property;
  needs schema approval; touches Publications, not the Institution count.
- **CONFIRM-ONLY (no load impact):** **§3** — 4 ROR-lookup rejections (nothing minted either
  way); **§6** — null `ror_id` confirmations on §2 mints (the mints are loaded with those
  `ror_id` values, incl. the nulls; awaiting sign-off that null is correct).

Regenerated 2026-07-15 with David's rulings pre-applied. Resolver = exact+fuzzy hybrid
(see `pdf_transform_facility_logic.md` §2/§7). Source: `data/raw/pdf_extraction/pdf_extraction_378papers.jsonl`
(378 papers, 171 with a grounded facility, 166 distinct strings).

## HOW DECISIONS WERE HANDLED (historical — decisions below are APPLIED per the status above)
1. Rows were **pre-filled** with the disposition in the `DECISION` column.
   Valid values: `confirm` · `mint-institution` · `map-to-existing:<identifier>` · `pub-property` ·
   `reject` · `review`.
2. Sections 1, 2, 5, 7 were **READY** and are now applied/loaded. Sections 3, 4, 6 carried
   **OPEN** items — §4 (schema approval) remains open; §3/§6 are confirm-only (see status).
3. Applied via `apply facility_institution_review.md` (the mints/aliases were written into
   `pdf_entities.jsonl`; every `03 → 04 → 05` since carries them).

---

## Section 1 — CONFIRM-RESOLVE (fuzzy proposals, rulings applied)  [READY]
Fuzzy layer PROPOSED these; your rulings applied. `confirm` = add raw string as a new alias to the
existing node (identifier frozen). 11 confirmed + 1 rejected-proposal (NOSAMS).

| # | String (verbatim) | → existing node | Match reason | Paper DOI(s) | DECISION |
|---|---|---|---|---|---|
| 1 | cloning and sequencing facility at Florida State University (Florida, USA) | `inst:florida_state_university` | substring:'Florida State University' | 10.1007/s11356-024-35140-6 | **confirm** |
| 2 | Florida State University, Department of Biological Science, Core Facilities | `inst:florida_state_university` | substring:'Florida State University' | 10.2166/wst.2024.139 | **confirm** |
| 3 | Florida State University, Wiley Online Library | `inst:florida_state_university` | substring:'Florida State University' | 10.1002/lol2.70046 | **confirm** |
| 4 | LIP at ETH Zurich | `inst:eth_zurich` | substring:'ETH Zurich' | 10.1002/lno.12436 | **confirm** |
| 5 | Mark Wainwright Analytical Centre at UNSW | `inst:unsw_sydney` | acronym:UNSW | 10.1016/j.watres.2019.115201 | **confirm** |
| 6 | Microsynth AG (Switzerland) | `inst:microsynth_ag` | substring:'Microsynth AG' | 10.1038/s43247-022-00407-8; 10.21203/rs.3.rs-691992/v1 | **confirm** |
| 7 | National Resource for Translational and Developmental Proteomics (Northwestern University, Evanston, IL) | `inst:northwestern_university` | substring:'Northwestern University' | 10.1021/jasms.2c00242 | **confirm** |
| 8 | National Resource for Translational and Developmental Proteomics (NRTDP) | `inst:northwestern_university` | acronym:NRTDP | 10.1021/acs.jproteome.0c00303 | **confirm** |
| 9 | NIST (National Institute of Standards and Technology), Gaithersburg, MD | `inst:national_institute_of_standards_and_technology` | substring:'National Institute of Standards and Technology' | 10.1016/j.aca.2019.01.007 | **confirm** |
| 10 | University of Miami, Rosenstiel School of Marine and Atmospheric Sciences | `inst:university_of_miami` | substring:'University of Miami' | 10.1002/lno.11385 | **confirm** |
| 11 | University of New South Wales (UNSW), Sydney | `inst:unsw_sydney` | substring:'University of New South Wales' | 10.1016/j.gca.2020.01.022 | **confirm** |
| 12 | National Ocean Sciences Accelerator Mass Spectrometry Facility at Woods Hole Oceanographic Institution, USA | ~~inst:woods_hole_oceanographic_institution~~ | substring:'Woods Hole Oceanographic Institution' | 10.1029/2024GB008359 | **REJECT proposal → mint `inst:nosams`** (see §2) |

*Auto-resolved by EXACT match (silent, no action — 18 strings → 17 existing nodes; already aliased, 0 new aliases):*

- `inst:australian_nuclear_science_and_technology_organisation` ← "ANSTO"
- `inst:australian_nuclear_science_and_technology_organisation` ← "Australian Nuclear Science and Technology Organisation (ANSTO)"
- `inst:technical_university_of_munich` ← "Chair of Soil Science (TU München, Germany)"
- `inst:eth_zurich` ← "ETH Zurich"
- `inst:exxonmobil_united_states` ← "ExxonMobil's Clinton campus"
- `inst:florida_state_university` ← "Florida State University"
- `inst:gfz_helmholtz_centre_for_geosciences` ← "GFZ Potsdam, Germany"
- `inst:university_of_eastern_finland` ← "ILMARI laboratory of the University of Eastern Finland"
- `inst:intertek` ← "Intertek"
- `inst:unsw_sydney` ← "Mark Wainwright Analytical Centre (UNSW Sydney)"
- `inst:pennsylvania_state_university` ← "Materials Research Institute at The Pennsylvania State University"
- `inst:midwest_micro_lab` ← "Midwest Micro Lab, Indianapolis, IN, USA"
- `inst:northwestern_university` ← "NRTDP (Evanston, IL)"
- `inst:princeton_university` ← "Onstott Lab at Princeton University"
- `inst:research_and_testing_laboratories_llc` ← "Research and Testing Laboratories, LLC (Lubbock, TX)"
- `inst:university_of_wisconsin_madison` ← "University of Wisconsin-Madison Biotechnology Center"
- `inst:university_of_new_hampshire` ← "Water Quality Analysis Laboratory at the University of New Hampshire"
- `inst:woods_hole_oceanographic_institution` ← "Woods Hole Oceanographic Institution"

## Section 2 — MINT AS INSTITUTION  [READY]  [41 new nodes]
`name_raw` preserves the verbatim string(s). `ror_id` = ROR top match, else **null** (never guessed).
Parent asserted ONLY where the string names the parent; distinctive named units & national user
facilities are minted as their OWN node (no parent guessed).

| identifier | name (→canonical) | ror_id | flag | note | source string(s) → DOI(s) | DECISION |
|---|---|---|---|---|---|---|
| `inst:argonne_national_laboratory` | Argonne National Laboratory | https://ror.org/05gvnxz63 | ✓ | national lab | "Argonne National Laboratory" → 10.1039/D2EM00184E | **mint** |
| `inst:australian_national_university` | Australian National University | https://ror.org/019wvm592 | ✓ |  | "Australian National University (ANU)" → 10.1073/pnas.1803866115 | **mint** |
| `inst:duke_university` | Duke University | https://ror.org/00py81415 | ✓ | abbrev 'Duke Univ.' | "Duke Univ." → 10.1038/s43017-020-0046-x | **mint** |
| `inst:ghent_university` | Ghent University | https://ror.org/00cv9y106 | ✓ |  | "Ghent University (Belgium)" → 10.1073/pnas.1714597115 | **mint** |
| `inst:louisiana_state_university` | Louisiana State University | https://ror.org/05ect4e57 | ✓ |  | "Louisiana State University, LA" → 10.1021/acs.est.6b01156 | **mint** |
| `inst:university_of_bremen` | University of Bremen | https://ror.org/04ers2y35 | ✓ |  | "University of Bremen" → 10.2138/gselements.18.2.107 | **mint** |
| `inst:university_of_california_irvine` | University of California, Irvine | https://ror.org/04gyf1771 | ✓ |  | "University of California, Irvine" → 10.1002/2017JG004343 | **mint** |
| `inst:university_of_california_los_angeles` | University of California, Los Angeles | https://ror.org/046rm7j60 | ✓ |  | "University of California, Los Angeles" → 10.1029/2023JG007797 | **mint** |
| `inst:utah_state_university` | Utah State University | https://ror.org/00h6set76 | ✓ |  | "Utah State University" → 10.1029/2020GB006719 | **mint** |
| `inst:university_of_maryland_center_for_environmental_science` | University of Maryland Center for Environmental Science | https://ror.org/04dqdxm60 | ✓ | own ROR | "University of Maryland Center for Environmental Science (UMCES)" → 10.3389/fmicb.2020.545070 | **mint** |
| `inst:changchun_institute_of_applied_chemistry` | Changchun Institute of Applied Chemistry | https://ror.org/00h52n341 | ✓ | CAS institute | "Changchun Institute of Applied Chemistry, China" → 10.1002/2017JG004343 | **mint** |
| `inst:institute_of_biomedical_chemistry` | Institute of Biomedical Chemistry | https://ror.org/040wrkp27 | ✓ | IBMC, Russia | "Institute of Biomedical Chemistry of RAMS (Russia)" → 10.1029/2018JG004743 | **mint** |
| `inst:university_of_central_florida` | University of Central Florida | https://ror.org/036nfer12 | ✓ | parent; unit strings in name_raw | "University of Central Florida (UCF) campus laboratory" → 10.1021/acs.est.8b01788<br>"Bioenvironmental Research Laboratory at UCF" → 10.1021/acs.est.8b01788<br>"bioenvironmental research laboratory at UCF" → 10.1016/j.chemosphere.2024.142042 | **mint** |
| `inst:university_of_colorado_boulder` | University of Colorado Boulder | https://ror.org/02ttsq026 | ✓ | parent | "CU Boulder Laboratory for Environmental and Geological Studies (LEGS)" → 10.1021/acs.est.6b05126<br>"Microbial Community Sequencing Lab (University of Colorado Boulder)" → 10.1021/acs.est.3c09797 | **mint** |
| `inst:montana_state_university` | Montana State University | https://ror.org/02w0trx84 | ✓ | parent | "Department of Chemical and Biological Engineering, Montana State University, USA" → 10.7185/geochemlet.1732<br>"Environmental Analytical Laboratory in the Department of Land Resources and Environmental Sciences at Montana State University (MSU)" → 10.1029/2020GB006719 | **mint** |
| `inst:johns_hopkins_university` | Johns Hopkins University | https://ror.org/00za53h95 | ✓ | parent | "Mass Spectrometry Facility (Johns Hopkins University, Baltimore, MD)" → 10.1007/s12010-019-03055-5<br>"Mass Spectrometry Facility at Johns Hopkins University (Baltimore, MD)" → 10.1007/s12155-018-9919-y<br>"mass spectrometry facility at the Johns Hopkins University (Baltimore, MD)" → 10.1021/acsomega.0c00566 | **mint** |
| `inst:university_of_washington` | University of Washington | https://ror.org/00cvxb145 | ✓ | parent | "University of Washington IsoLab laboratory" → 10.1029/2022GB007495<br>"University of Washington Proteomics Resource NSI source" → 10.1007/s13361-017-1702-3 | **mint** |
| `inst:yale_university` | Yale University | https://ror.org/03v76x132 | ✓ | parent (E. coli Genetic Stock Center) | "Coli Genetic Stock Center, Yale University" → 10.1021/acs.jproteome.0c00303 | **mint** |
| `inst:university_of_oklahoma` | University of Oklahoma | https://ror.org/02aqsxs83 | ✓ | parent | "Institute of Environmental Genomics, University of Oklahoma" → 10.1016/j.ecolind.2024.111884 | **mint** |
| `inst:university_of_waterloo` | University of Waterloo | https://ror.org/01aff2v68 | ✓ | parent | "Environmental Isotope Laboratory at the university of Waterloo" → 10.1029/2022GB007495 | **mint** |
| `inst:international_atomic_energy_agency` | International Atomic Energy Agency | https://ror.org/00gtfax65 | ✓ | parent (IAEA) | "Isotope Hydrology Laboratory of the International Atomic Energy Agency (IAEA, Vienna, Austria)" → 10.1029/2025GB008545 | **mint** |
| `inst:university_of_lausanne` | University of Lausanne | https://ror.org/019whta54 | ✓ | parent | "Stable Isotope Laboratory of the University of Lausanne, Switzerland" → 10.1029/2022JG007188 | **mint** |
| `inst:university_of_california_davis` | University of California, Davis | https://ror.org/05rrcem69 | ✓ | parent | "UC Davis Stable Isotope Facility" → 10.1016/j.gca.2020.01.022 | **mint** |
| `inst:university_of_alaska_fairbanks` | University of Alaska Fairbanks | https://ror.org/01j7nq853 | ✓ | parent | "University of Alaska Stable Isotope Facility, Fairbanks, AK, USA" → 10.1029/2018JG004712 | **mint** |
| `inst:university_of_illinois_at_chicago` | University of Illinois Chicago | https://ror.org/02mpq6x41 | ✓ | parent (ROR name 'University of Illinois Chicago') | "University of Illinois at Chicago Core for Research Informatics (UICCRI)" → 10.1007/s11783-022-1567-y | **mint** |
| `inst:lomonosov_moscow_state_university` | Lomonosov Moscow State University | https://ror.org/010pmpe69 | ✓ | parent (names Lomonosov MSU) | "the laboratory of Dr. Irina Perminova (Lomonosov MSU, Moscow, Russia)" → 10.1515/pac-2019-0809 | **mint** |
| `inst:als_environmental` | ALS Environmental | **null** | ✗ | ROR null — 'ALS Hope Foundation' is an unrelated acronym hit | "ALS Environmental (Tucson, AZ)" → 10.1021/acs.energyfuels.8b01445 | **mint** |
| `inst:cambridge_polymer_group` | Cambridge Polymer Group | https://ror.org/05wj1n164 | ✓ |  | "Cambridge Polymer Group" → 10.1021/acs.est.1c02272 | **mint** |
| `inst:gatc_biotech` | GATC Biotech | https://ror.org/04g8dha87 | ✓ |  | "GATC Biotech AG" → 10.1029/2018JG004712 | **mint** |
| `inst:genentech` | Genentech | https://ror.org/04gndp242 | ✓ |  | "Genentech Inc." → 10.1021/acs.analchem.9b04855 | **mint** |
| `inst:mainstream_engineering` | Mainstream Engineering | https://ror.org/00g3zpx26 | ✓ |  | "Mainstream Engineering" → 10.26434/chemrxiv-2022-0k0jg | **mint** |
| `inst:totalenergies` | TotalEnergies | **null** | ✗ | ROR null — only 'TotalEnergies Foundation' (charity) exists; no corporate record | "TotalEnergies Research and Technology (Gonfreville, France)" → 10.1021/acs.energyfuels.4c01959 | **mint** |
| `inst:bridgestone_americas` | Bridgestone (United States) | https://ror.org/03wpppw84 | ✓ | US entity (Biorubber center is Mesa, AZ), NOT Japanese parent | "Bridgestone Americas Biorubber Processing Research Center (Mesa, AZ)" → 10.1016/j.dib.2020.105989<br>"Bridgestone Biorubber Process Research Center (Mesa, AZ)" → 10.1016/j.indcrop.2020.112311 | **mint** |
| `inst:woodwell_climate_research_center` | Woodwell Climate Research Center | https://ror.org/04cvvej54 | ✓ | fmr Woods Hole Research Center; NOT WHOI | "Woodwell Climate Research Center (WCRC" → 10.1029/2020GB006871<br>"WCRC" → 10.1029/2020GB006871<br>"formerly Woods Hole Research Center)" → 10.1029/2020GB006871 | **mint** |
| `inst:cage` | Centre for Arctic Gas Hydrate, Environment and Climate | https://ror.org/00p8r6x45 | ✓ | own ROR (CAGE); no parent asserted | "CAGE (Centre for Gas Hydrate, Environment and Climate)" → 10.3389/feart.2020.552731 | **mint** |
| `inst:cosmic` | College of Sciences Major Instrumentation Cluster (COSMIC) | **null** | ✗ | ROR null; mint unit, no parent guessed | "College of Sciences Major Instrumentation Cluster (COSMIC)" → 10.1039/d4em00023d | **mint** |
| `inst:colorado_cancer_center_genomics_shared_resource` | Genomics Shared Resource, Colorado Cancer Center | **null** | ✗ | ROR null; mint unit, no parent guessed | "Genomics Shared Resource, Colorado Cancer Center, Denver, CO, USA" → 10.1039/D2EM00184E | **mint** |
| `inst:boiteau_lab` | Boiteau Lab | **null** | ✗ | ROR null; mint unit, no parent guessed | "Boiteau Lab" → 10.1021/acs.est.1c01135 | **mint** |
| `inst:nosams` | National Ocean Sciences Accelerator Mass Spectrometry (NOSAMS) | **null** | ✗ | ROR null; national user facility = OWN node, NOT collapsed into WHOI host (mirrors NHMFL-at-FSU) | "National Ocean Sciences Accelerator Mass Spectrometry (NOSAMS) facility" → 10.1021/acs.est.7b05513<br>"National Ocean Sciences Accelerator Mass Spectrometry (NOSAMS) facility in Woods Hole, MA" → 10.1029/2020JG005977<br>"National Ocean Sciences Accelerator Mass Spectrometry Facility at Woods Hole Oceanographic Institution, USA" → 10.1029/2024GB008359<br>"National Ocean Sciences Accelerator Mass Spectrometry facility" → 10.1021/acs.est.1c02272 | **mint** |
| `inst:stanford_synchrotron_radiation_lightsource` | Stanford Synchrotron Radiation Lightsource | https://ror.org/02vzbm991 | ✓ | own ROR (SSRL); national user facility = own node | "Stanford Synchrotron Radiation Lightsource" → 10.1021/acs.est.3c01347 | **mint** |
| `inst:advanced_light_source` | Advanced Light Source | https://ror.org/00319zh75 | ✓ | own ROR (ALS); national user facility; beamline in name_raw | "Chemical Dynamics Beamline 9.0.2 at the Advanced Light Source" → 10.1021/acs.est.9b03043 | **mint** |

**Collapse into existing (spelling variant, not a new node):**
- "Midwest Microlabs" → `inst:midwest_micro_lab` (add as alias) — 10.1016/j.isci.2022.104916  · **DECISION: map-to-existing:inst:midwest_micro_lab**

## Section 3 — ROR LOOKUPS (4 acronyms)  [OPEN — confirm reject]
Queried real `api.ror.org/v2`. **All four returned NO confident registry match.** Per your rule
(registry-match-or-reject, no inferred expansion) → propose **reject**.

| String | ROR result | Proposed | DECISION |
|---|---|---|---|
| ADG CRNR | no ROR record | reject | **reject** |
| MAGU | no ROR record | reject | **reject** |
| U.B.C. | no ROR record (also queried 'UBC' — no confident hit); do NOT infer 'British Columbia' | reject | **reject** |
| UTMSI | no ROR record | reject | **reject** |

## Section 4 — PUBLICATION PROPERTY, not a node  [OPEN — needs schema approval]
Generic descriptors: two papers using the same string mean DIFFERENT places, so one node would
falsely merge them. Proposal: record verbatim on the Publication as `facilities_mentioned_raw`
(array), do NOT mint. **Schema addition NOT applied — see wording below for approval.**

| String (verbatim) | Why generic | Paper DOI(s) | DECISION |
|---|---|---|---|
| Chemical Instrumentation Facility | generic; no institution named  [NOT in your explicit list — placed by same rule, confirm] | 10.1002/mas.21666 | **pub-property** |
| Clinical Haematology Department | generic department | 10.1515/cclm-2020-1072 | **pub-property** |
| Dlila Facility, Israel | unknown generic facility (+ bare geography) | 10.3390/soilsystems2010014 | **pub-property** |
| greenhouse facility | generic | 10.1021/acs.energyfuels.9b00469 | **pub-property** |
| laboratory | generic | 10.1021/acsestwater.4c00832 | **pub-property** |
| long-term monitoring station | generic | 10.1007/s10533-021-00876-7 | **pub-property** |
| N/A | null placeholder | 10.1021/acs.est.7b05513 | **pub-property** |
| North Florida Research | vague fragment | 10.1016/j.scitotenv.2023.167382 | **pub-property** |
| our lab | generic self-reference | 10.1016/j.marpolbul.2016.01.012 | **pub-property** |
| the laboratory | generic; 4 papers = 4 different places | 10.1002/lno.11716; 10.1016/j.ecolind.2024.111884; 10.1021/acs.est.0c05206; 10.1126/sciadv.abn0035 | **pub-property** |
| this lab | generic self-reference | 10.1016/j.bmcl.2016.03.099 | **pub-property** |

## Section 5 — REJECT (confirm no over-drop)  [READY]
| String (verbatim) | Reason | Paper DOI(s) | DECISION |
|---|---|---|---|
| Amsterdam, Netherlands | bare geography (prior-confirmed) | 10.1021/acs.energyfuels.4c01959 | **reject** |
| Bemidji site | bare field site | 10.1021/acs.est.5c07016 | **reject** |
| coastal Georgia, USA | bare geography | 10.1029/2018JG004982 | **reject** |
| in-house | sentence fragment (prior-confirmed) | 10.1021/acs.analchem.1c00847 | **reject** |
| International Laboratory Comparison | generic phrase, not an institution | 10.1021/acs.est.1c01135 | **reject** |
| in vitro cultivated fraction of C. angustifolia roots | sample description, not a place | 10.1002/pca.70001 | **reject** |
| Karlsruhe, Germany | bare geography | 10.1016/j.seh.2025.100148 | **reject** |
| Mass Spectrometry Interactive Virtual Environment (MassIVE) | data repository (prior-confirmed) | 10.1038/s43247-024-01965-9 | **reject** |
| Massachusetts, USA | bare geography (prior-confirmed) | 10.1021/acs.energyfuels.4c01959 | **reject** |
| National Center for Biotechnology Information | database/repository NCBI (cf. MassIVE) | 10.1126/sciadv.abn0035 | **reject** |
| PerkinElmer, Waltham, MA | instrument/reagent vendor (cf. Thermo) | 10.1016/j.orggeochem.2018.03.005 | **reject** |
| SEWRF | acronym of the municipal water plant (sample site) | 10.1016/j.scitotenv.2023.166291 | **reject** |
| Southeast Water Reclamation Facility (SEWRF) | municipal water plant = sample site, not an institution | 10.1016/j.scitotenv.2023.166291 | **reject** |
| Stordalen | field site (Stordalen Mire) / geography | 10.1016/j.gca.2016.05.015 | **reject** |
| the mine | sentence fragment (prior-confirmed) | 10.1038/s41467-023-41900-8 | **reject** |
| Thermo Scienti fi c, San Jose, CA | instrument vendor (prior-confirmed) | 10.1021/acs.energyfuels.0c03349 | **reject** |
| Thermo Scienti fi c, UK | instrument vendor (prior-confirmed) | 10.1038/s41467-017-01123-0 | **reject** |
| Vanishing Glacier Project | research project (cf. GEOTRACES cruise) | 10.1029/2024GB008359 | **reject** |

## Section 6 — ROR FLAGS on Section-2 mints (rulings applied)  [OPEN — confirm nulls]
| identifier | ruling | resolved ror_id |
|---|---|---|
| `inst:als_environmental` | ROR null — 'ALS Hope Foundation' is an unrelated acronym hit | **null** |
| `inst:totalenergies` | corporate/research record sought; ROR has ONLY 'TotalEnergies Foundation' (charity) → null | **null** |
| `inst:bridgestone_americas` | use Americas entity (Mesa, AZ), not Japanese parent | https://ror.org/03wpppw84 |

## Section 7 — NHMFL/MagLab SKIPPED (CSV owns via CONDUCTED_AT)  [READY]  [49 strings]
Confirm the skip is correct (CSV already attributes NHMFL per paper). Sample:

- Florida State University 's National High Magnetic Field Laboratory
- MagLab of Florida State University
- national FT-ICR MS user facility at the National High Magnetic Field Laboratory
- National High  Magnetic  Field Laboratory
- National High Magnetic Field Lab
- National High Magnetic Field Lab in Tallahassee, FL
- National High Magnetic Field Laboratory
- National High Magnetic Field Laboratory (Florida State University, Tallahassee, FL)
- …and 41 more NHMFL/MagLab variants.

