# PDF Extraction Evaluation Report

Generated: 2026-07-01T20:45:42.060096+00:00

Ground truth source: `docs\annotations\paper_reviews.md`
Predictions source: `data\processed\entities\pdf_extracted.jsonl`

---

## Per-field summary

| Field | TP | FP | FN | TN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| instrument | 0 | 0 | 8 | 0 | 0.00 | 0.00 | 0.00 |
| ionization_method | 0 | 0 | 13 | 0 | 0.00 | 0.00 | 0.00 |
| sample_type | 0 | 0 | 5 | 4 | 0.00 | 0.00 | 0.00 |
| facility | 0 | 0 | 8 | 0 | 0.00 | 0.00 | 0.00 |
| software_tools | 0 | 0 | 35 | 0 | 0.00 | 0.00 | 0.00 |
| dataset_accession | 0 | 0 | 1 | 7 | 0.00 | 0.00 | 0.00 |
| **MICRO TOTAL** | 0 | 0 | 70 | 11 | **0.00** | **0.00** | **0.00** |

**Macro F1 (average across fields): 0.00**


---

## Per-paper detail

### `10.1002/rcm.4655`

| Field | Expected | Predicted | Outcome | Match level |
|---|---|---|---|---|
| instrument | Modified LTQ-FT mass spectrometer, 14.5 T FT-ICR | N/A | FN | N/A |
| ionization_method | ESI, FT-ICR MS, LC-MS/MS, top-down proteomics, bottom-up proteomics, CID | N/A | FN | N/A |
| sample_type | N/A | N/A | TN | N/A |
| facility | Ion Cyclotron Resonance Program, National High Magnetic Field Laboratory | N/A | FN | N/A |
| software_tools | Xcalibur, MIDAS, MASCOT, ProSight 2.0, custom peak-picking algorithm | N/A | FN | N/A |
| dataset_accession | N/A | N/A | TN | N/A |

### `10.1016/j.jbc.2022.102768`

| Field | Expected | Predicted | Outcome | Match level |
|---|---|---|---|---|
| instrument | 21 T FT-ICR MS, Q Exactive HF Hybrid Quadrupole-Orbitrap Mass Spectrometer, Q-Exactive HF BioPharma mass spectrometer | N/A | FN | N/A |
| ionization_method | Electrospray ionization (ESI) | N/A | FN | N/A |
| sample_type | cell-line names, mutation status, source; CPTAC tumor IDs | N/A | FN | N/A |
| facility | National High Magnetic Field Laboratory, Northwestern Proteomics Core Facility | N/A | FN | N/A |
| software_tools | ProSight Lite 1.4; ProSight PD 4.0; TDValidator 1.0 (Proteinaceous); Protein Annotator; Xcalibur QualBrowser; Mascot (Matrix Science, version 2.8.0); Scaffold version 5.0.1 (Proteome Software); Fiji ImageJ; Integrative Genomics Viewer (version 2.9.4, Broad Institute); GDC Data Transfer Tool Client (version 1.6.1) | N/A | FN | N/A |
| dataset_accession | N/A | N/A | TN | N/A |

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
| instrument | Home-built 9.4 T FTICR instrument | N/A | FN | N/A |
| ionization_method | Electrospray Ionization (ESI) FTICR-MS | N/A | FN | N/A |
| sample_type | N/A | N/A | TN | N/A |
| facility | National High Magnetic Field Laboratory (NHMFL) | N/A | FN | N/A |
| software_tools | Isopro 3.1; MIDAS 160 | N/A | FN | N/A |
| dataset_accession | N/A | N/A | TN | N/A |

### `10.1021/acs.analchem.5c02420`

| Field | Expected | Predicted | Outcome | Match level |
|---|---|---|---|---|
| instrument | Custom-built 21 T FT-ICR mass spectrometer | N/A | FN | N/A |
| ionization_method | ESI, APPI, FT-ICR MS, Mass Difference Analysis (MDA), Walking Calibration | N/A | FN | N/A |
| sample_type | HVGO, BO | N/A | FN | N/A |
| facility | National High Magnetic Field Laboratory (NHMFL) | N/A | FN | N/A |
| software_tools | PyC2MC, Predator Software | N/A | FN | N/A |
| dataset_accession | N/A | N/A | TN | N/A |

### `10.1021/acs.analchem.5c06165`

| Field | Expected | Predicted | Outcome | Match level |
|---|---|---|---|---|
| instrument | 21 T FT-ICR, Orbitrap Eclipse Tribrid | N/A | FN | N/A |
| ionization_method | ESI (positive), Direct Infusion, High-performance liquid chromatography | N/A | FN | N/A |
| sample_type | apomyoglobin (equine, 17 kDa), Protein G (Streptococcus, 21 kDa), and Carbonic Anhydrase II (bovine, 29 kDa) | N/A | FN | N/A |
| facility | National High Magnetic Field Laboratory | N/A | FN | N/A |
| software_tools | FLASHDeconv (OpenMS); ChatGPT/OpenAI noted for manuscript drafting; Agilent ExDViewer | N/A | FN | N/A |
| dataset_accession | N/A | N/A | TN | N/A |

### `10.1021/acs.jproteome.6b00696`

| Field | Expected | Predicted | Outcome | Match level |
|---|---|---|---|---|
| instrument | 21 T FT-ICR MS | N/A | FN | N/A |
| ionization_method | Nano-electrospray ionization (microelectrospray); reverse-phase nano-LC; CID and ETD fragmentation; top-down MS/MS | N/A | FN | N/A |
| sample_type | DLD-1 (HD PAR-086, Horizon Discovery) | N/A | FN | N/A |
| facility | NHMFL FT-ICR | N/A | FN | N/A |
| software_tools | Xcalibur; ProSight PTM 2.0; TDPortal; TDViewer v0.9.0.10; Thermo Fisher Xtract; Venny 2.1; Microsoft Excel | N/A | FN | N/A |
| dataset_accession | MSV000079978 | N/A | FN | N/A |

### `10.21037/atm.2019.12.67`

| Field | Expected | Predicted | Outcome | Match level |
|---|---|---|---|---|
| instrument | 21 T FT-ICR MS | N/A | FN | N/A |
| ionization_method | Dilute and infuse (DnS); top-down MS/MS; MS1/MS2 | N/A | FN | N/A |
| sample_type | N/A | N/A | TN | N/A |
| facility | National High Magnetic Field Laboratory, Florida State University | N/A | FN | N/A |
| software_tools | N/A | N/A | FN | N/A |
| dataset_accession | N/A | N/A | TN | N/A |
