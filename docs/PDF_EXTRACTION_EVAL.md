# PDF Extraction Evaluation Report

Generated: 2026-07-10T19:20:31.675437+00:00

Ground truth source: `docs/annotations/paper_reviews.md`
Predictions source: `data/processed/entities/pdf_extracted.jsonl`

---

## Per-field summary

| Field | TP | FP | FN | TN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| instrument | 6 | 15 | 5 | 0 | 0.29 | 0.55 | 0.37 |
| ionization_method | 8 | 7 | 16 | 0 | 0.53 | 0.33 | 0.41 |
| sample_type | 0 | 14 | 8 | 1 | 0.00 | 0.00 | 0.00 |
| facility | 2 | 1 | 7 | 0 | 0.67 | 0.22 | 0.33 |
| software_tools | 10 | 4 | 30 | 0 | 0.71 | 0.25 | 0.37 |
| dataset_accession | 2 | 1 | 1 | 4 | 0.67 | 0.67 | 0.67 |
| **MICRO TOTAL** | 28 | 42 | 67 | 5 | **0.40** | **0.29** | **0.34** |

**Macro F1 (average across fields): 0.36**


---

## Per-paper detail

### `10.1002/rcm.4655`

| Field | Expected | Predicted | Outcome | Match level |
|---|---|---|---|---|
| instrument | Modified LTQ-FT mass spectrometer, 14.5 T FT-ICR | Advion BioSystems Nanomate; modified hybrid linear quadrupole ion trap/FT-ICR mass spectrometer (LTQ-FT); LTQ | TP | overlap |
| ionization_method | ESI; FT-ICR MS; LC-MS/MS; top-down proteomics; bottom-up proteomics; CID | ESI; CID | TP | exact |
| sample_type | N/A | In-gel trypsin digests; in-gel digested samples; intact protein | FP | N/A |
| facility | Ion Cyclotron Resonance Program, National High Magnetic Field Laboratory | N/A | FN | N/A |
| software_tools | Xcalibur; MIDAS; MASCOT; ProSight 2.0; custom peak-picking algorithm | Xcalibur; Xcalibur and MIDAS | TP | exact |
| dataset_accession | N/A | N/A | TN | N/A |

### `10.1016/j.jbc.2022.102768`

| Field | Expected | Predicted | Outcome | Match level |
|---|---|---|---|---|
| instrument | 21 T FT-ICR MS; Q Exactive HF Hybrid Quadrupole-Orbitrap Mass Spectrometer; Q-Exactive HF BioPharma mass spectrometer | QE-HF mass spectrometer; Q-Exactive HF BioPharma; 21 T FT-ICR mass spectrometer; modi fi ed Velos Pro linear ion trap assembly; Zeiss Axio Observer 7 confocal microscope; Dionex UltiMate 3000 Rapid Separation nanoLC; Q Exactive HF Hybrid Quadrupole-Orbitrap Mass Spectrometer | TP | exact |
| ionization_method | Electrospray ionization (ESI) | electrospray ionization; collision-induced dissociation (CID) or front-end electron-transfer dissociation | TP | overlap |
| sample_type | cell-line names, mutation status, source; CPTAC tumor IDs | cell pellets; Immunopuri fi ed RAS proteins; Immunopuri fi ed KRAS proteoforms; Variants in KRAS, NRAS, and HRAS; HeLa cells on poly-L-lysine -treated coverslips in 12-well dishes; IP fl ow-through fractions, elution fractions preserved in acetone, and IP beads in sample buffer | FP | N/A |
| facility | National High Magnetic Field Laboratory; Northwestern Proteomics Core Facility | NU SeqCore; Proteomics Core Facility | TP | overlap |
| software_tools | ProSight Lite 1.4; ProSight PD 4.0; TDValidator 1.0 (Proteinaceous); Protein Annotator; Xcalibur QualBrowser; Mascot (Matrix Science, version 2.8.0); Scaffold version 5.0.1 (Proteome Software); Fiji ImageJ; Integrative Genomics Viewer (version 2.9.4, Broad Institute); GDC Data Transfer Tool Client (version 1.6.1) | Xcalibur QualBrowser; ProSight Lite 1.4; ProSight PD 4.0; TDValidator 1.0; GDC Data Transfer Tool Client v1.6.1; Integrative Genomics Viewer (version 2.9.4); Fiji ImageJ using the Plot Pro fi les function; Mascot search engine (Matrix Science; version 2.8.0) | TP | exact |
| dataset_accession | MSV000088748 | MSV000088748 | TP | exact |

### `10.1016/j.mcpro.2024.100875`

| Field | Expected | Predicted | Outcome | Match level |
|---|---|---|---|---|
| instrument | N/A | N/A | FN | N/A |
| ionization_method | CAD, ETD (dissociation techniques) | N/A | FN | N/A |
| sample_type | N/A | N/A | TN | N/A |
| facility | NHMFL | N/A | FN | N/A |
| software_tools | Hunt Lab Peptide Fragment Calculator; Predator Protein Fragment Calculator; MS-Product  from Protein Prospector; NIST Mass and Fragment Calculator; UW MS/MS Fragmentation Calculator; CorelDRAW X8; ChemDraw; IsoPro 3.1; SEQUEST; Yergey algorithm | N/A | FN | N/A |
| dataset_accession | N/A | N/A | TN | N/A |

### `10.1021/ac0108461`

| Field | Expected | Predicted | Outcome | Match level |
|---|---|---|---|---|
| instrument | Home-built 9.4 T FTICR instrument | homebuilt 9.4-T FTICR | FP | N/A |
| ionization_method | Electrospray Ionization (ESI) FTICR-MS | electrospray ionization; broadband negative ion ESI; Positive-ion ESI; ESI | TP | overlap |
| sample_type | N/A | a mixture of ATP and PAPS with added sodium triflate; peptides; nucleotides; PEGBCME | FP | N/A |
| facility | National High Magnetic Field Laboratory (NHMFL) | N/A | FN | N/A |
| software_tools | Isopro 3.1; MIDAS 160 | N/A | FN | N/A |
| dataset_accession | N/A | N/A | TN | N/A |

### `10.1021/acs.analchem.5c02420`

| Field | Expected | Predicted | Outcome | Match level |
|---|---|---|---|---|
| instrument | Custom-built 21 T FT-ICR mass spectrometer | 21 T FT-ICR mass spectrometer | TP | overlap |
| ionization_method | ESI; APPI; FT-ICR MS; Mass Difference Analysis (MDA); Walking Calibration | positive-ion APPI | TP | overlap |
| sample_type | HVGO; BO | petroleum mass difference database; monoisotopic formula | FP | N/A |
| facility | National High Magnetic Field Laboratory (NHMFL) | N/A | FN | N/A |
| software_tools | PyC2MC; Predator Software | Peak lists (uncalibrated, global calibration, mass difference calibrated, and walking calibrated) | FP | N/A |
| dataset_accession | 10.17605/OSF.IO/D7G3N | OSF.IO/D7G3N | TP | overlap |

### `10.1021/acs.analchem.5c06165`

| Field | Expected | Predicted | Outcome | Match level |
|---|---|---|---|---|
| instrument | 21 T FT-ICR; Orbitrap Eclipse Tribrid | FT-ICR mass spectrometer; custom-built 21 tesla (T) FTICR mass spectrometer; Orbitrap Eclipse Tribrid mass spectrometer (Thermo Fisher Scientific) | TP | overlap |
| ionization_method | ESI (positive); Direct Infusion; High-performance liquid chromatography | Fourier-transform ion cyclotron resonance (FT-ICR); positive electrospray ionization via direct infusion and high-performance liquid chromatography | TP | overlap |
| sample_type | apomyoglobin (equine, 17 kDa); Protein G (Streptococcus, 21 kDa); Carbonic Anhydrase II (bovine, 29 kDa) | N/A | FN | N/A |
| facility | National High Magnetic Field Laboratory | National High Magnetic Field Laboratory (Tallahassee, FL) | TP | overlap |
| software_tools | FLASHDeconv (OpenMS); ChatGPT/OpenAI noted for manuscript drafting; Agilent ExDViewer | R code and Excel spreadsheets | FP | N/A |
| dataset_accession | N/A | http://doi.org/10.17605/OSF.IO/5AR6H | FP | N/A |

### `10.1021/acs.jproteome.6b00696`

| Field | Expected | Predicted | Outcome | Match level |
|---|---|---|---|---|
| instrument | 21 T FT-ICR MS | nano-HPLC system (ACQUITY MClass); ICR mass analyzer | FP | N/A |
| ionization_method | Nano-electrospray ionization (microelectrospray); reverse-phase nano-LC; CID and ETD fragmentation; top-down MS/MS | microelectrospray ionization | FP | N/A |
| sample_type | DLD-1 (HD PAR-086, Horizon Discovery) | DLD-1 parental (KRas wt/G13D) human colorectal cancer cells; Reconstituted protein fractions; Precursor (MS1) and product (MS2) ion spectra | FP | N/A |
| facility | NHMFL FT-ICR | N/A | FN | N/A |
| software_tools | Xcalibur; ProSight PTM 2.0; TDPortal; TDViewer v0.9.0.10; Thermo Fisher Xtract; Venny 2.1; Microsoft Excel | Microsoft Excel 2013 | TP | overlap |
| dataset_accession | MSV000079978 | N/A | FN | N/A |

### `10.21037/atm.2019.12.67`

| Field | Expected | Predicted | Outcome | Match level |
|---|---|---|---|---|
| instrument | 21 T FT-ICR MS | 21 Tesla Fourier transform ion cyclotron resonance mass spectrometer; 21 T FT-ICR MS; orbitrap; high-resolution mass spectrometer | TP | exact |
| ionization_method | Dilute and infuse (DnS); top-down MS/MS; MS1/MS2 | 21 T FT-ICR MS; MS/MS; top-down and middle-down MS/MS | TP | overlap |
| sample_type | N/A | plasma cell disorders; monoclonal immunoglobulin light chains; Hb variants; protein analysis; monoclonal antibodies; HUPO test sample study | FP | N/A |
| facility | National High Magnetic Field Laboratory, Florida State University | N/A | FN | N/A |
| software_tools | N/A | N/A | FN | N/A |
| dataset_accession | N/A | N/A | TN | N/A |
