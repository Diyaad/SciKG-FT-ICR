# SciKG Controlled Vocabulary
#
# Standards and verified sources:
#
# PSI-MS Ontology (Mass Spectrometry CV)
#   Maintained by: HUPO Proteomics Standards Initiative
#   Repository: https://github.com/HUPO-PSI/psi-ms-CV
#   OBO file: https://raw.githubusercontent.com/HUPO-PSI/psi-ms-CV/master/psi-ms.obo
#   Browser: https://www.ebi.ac.uk/ols/ontologies/ms
#   ID format: MS:XXXXXXX
#   Version used: 4.1.237 (February 2026)
#
# nmrCV (Nuclear Magnetic Resonance CV)  (added 2026-07-17, R7)
#   Maintained by: MSI / COSMOS EU / PhenoMeNal EU (nmrML)
#   Browser: https://www.ebi.ac.uk/ols4/ontologies/nmrcv
#   Version IRI: http://nmrml.org/cv/v1.1.0/nmrCV.owl
#   ID format: NMR:XXXXXXX
#   Version used: 1.1.0 (792 terms; checked via OLS4 2026-07-17)
#   Finding (so nobody repeats the lookup): nmrCV names Bruker instruments by
#   CONSOLE GENERATION (Avance I / II / III HD / IVDr, DRX); our corpus names them
#   by 1H FREQUENCY (600/500/400 MHz). No model-level term exists at our
#   granularity, so the CLASS-level link (NMR:1400198 Bruker NMR instrument;
#   NMR:1400059 NMR instrument) is the CORRECT mapping — the same reason FT-ICR
#   takes MS:1003948 (FT-ICR instrument class) rather than a per-magnet term. Not a
#   fallback. nmrCV has NO 1H-frequency term (0 hits for proton/Larmor/spectrometer
#   frequency); it has a field-strength PARAMETER term (NMR:1400027) that is not an
#   instrument identity — see the note below the Instruments table.
#
# UNIMOD (Protein Post-Translational Modifications)
#   Maintained by: UNIMOD community (unimod.org)
#   Website: https://www.unimod.org
#   Downloads: https://www.unimod.org/downloads.html
#   Browser: https://www.ebi.ac.uk/ols4/ontologies/unimod
#   ID format: UNIMOD:XX
#
# NCBI Taxonomy (Organism Names)
#   Maintained by: National Center for Biotechnology Information
#   Source: https://www.ncbi.nlm.nih.gov/taxonomy
#   ID format: integer taxonomy ID
#
# UniProt (Protein Identifiers)
#   Maintained by: UniProt Consortium
#   Source: https://www.uniprot.org
#   ID format: 6-character alphanumeric accession
#
# DataCite (Dataset Metadata Conventions)
#   Maintained by: DataCite
#   Source: https://schema.datacite.org
#   Used for: dataset node structure and repository conventions
#
# ORCID (Researcher Identifiers)
#   Source: https://orcid.org
#   ID format: 0000-0000-0000-0000
#
# ROR (Research Organization Registry)
#   Source: https://ror.org
#   ID format: https://ror.org/XXXXXXXXX
#
# Rule: all entity names in the graph must resolve to
# a canonical label in this file.
# Variants go in the Aliases column.
# Last updated: 2026-07-01

## Instruments

# Peripheral components (LC systems, ion sources, ICR
# cells) are not separate Instrument nodes in v1.0.
# They are recorded as text properties on Publication.
# Peripherals: ACQUITY M-Class, NanoMate, NanoLC,
# APPI Ion Max, MIDAS 160, GELFrEE 8100

| Canonical | Ontology ID | Ontology Source | Aliases | Vendor | Magnetic Field (T) | 1H Frequency (MHz) |
|---|---|---|---|---|---|---|
| 21T FT-ICR MS | MS:1003948 | PSI-MS | 21 T FT-ICR MS, 21 T FT-ICR mass spectrometer, Custom-built 21 T FT-ICR MS, 21T ICR, 21 T FT-ICR, 21 Tesla FT-ICR MS, 21 T FT-ICR MS | — | 21.0 |  |
| 14.5T FT-ICR MS | MS:1003948 | PSI-MS | 14.5 T FT-ICR, 14.5T FT-ICR, 14.5 T superconducting magnet, Modified 14.5 T FT-ICR, LTQ-FT MS | — | 14.5 |  |
| 9.4T FT-ICR MS | MS:1003948 | PSI-MS | 9.4 T FT-ICR MS, 9.4T FT-ICR, Home-built 9.4 T FTICR instrument, 9.4 T FTICR | — | 9.4 |  |
| Orbitrap Eclipse Tribrid | MS:1003029 | PSI-MS | Orbitrap Eclipse Tribrid Mass Spectrometer | — |  |  |
| Q-Exactive HF | MS:1002523 | PSI-MS | Q Exactive HF Hybrid Quadrupole-Orbitrap, Q-Exactive HF BioPharma, Q Exactive HF | — |  |  |
| Velos Pro | MS:1003495 | PSI-MS | Velos Pro dual-cell linear ion trap, Velos Pro linear ion trap | — |  |  |
| TOF MS | MS:1003951 | PSI-MS | TOF, time-of-flight | — |  |  |
| Finnigan TSQ | MS:1000750 | PSI-MS | Finnigan TSQ | — |  |  |
| Finnigan LCQ | MS:1000031 | PSI-MS | Finnigan LCQ, Finnigan LSQ | — [PENDING: MS:1000031 is a generic parent ("instrument model"); no generic PSI-MS LCQ term exists — needs specific submodel, supervisor decision] |  |  |
| LTQ Orbitrap Velos | MS:1001742 | PSI-MS | LTQ Orbitrap Velos | Thermo Scientific |  |  |
| LTQ FT Ultra | MS:1000557 | PSI-MS | LTQ FT Ultra | Thermo Scientific |  |  |
| Bruker Avance | NMR:1400198 | NMRCV | Bruker AVANCE, Bruker Avance | Bruker |  |  |
| Bruker Avance III 600 MHz | NMR:1400198 | NMRCV | Bruker Avance III 600 MHz | Bruker |  | 600 |
| Bruker Avance III 500 MHz | NMR:1400198 | NMRCV | Bruker BioSpin Avance III 500 MHz NMR spectrometer | Bruker |  | 500 |
| Bruker Avance III 400 MHz | NMR:1400198 | NMRCV | Bruker AVANCE 400 MHz, Bruker BioSpin Avance III 400 MHz WB | Bruker |  | 400 |
| Bruker Avance NEO 400 MHz | NMR:1400198 | NMRCV | Bruker Neo Avance 400 | Bruker |  | 400 |
| 600 MHz solid-state NMR spectrometer | NMR:1400059 | NMRCV | 1 T solid-state NMR spectrometer, a 600 MHz/14.1 T solid-state NMR spectrometer, 600 MHz/14 |  | 14.1 | 600 |

**NMR rows added 2026-07-17 (R1–R8). Grouping B — split by 1H frequency, so distinct magnets stay
distinct exactly as 21T/14.5T/9.4T FT-ICR do (three rows, one accession).** Aliases are verbatim
from `data/processed/review/instrument_review.md`'s "AUTO-MINTED — NMR (NMRCV)" block. **8-vs-6
note (R8):** that block lists 8 rows, but three solid-state fragments ("1 T solid-state NMR
spectrometer", "600 MHz/14", "a 600 MHz/14.1 T solid-state NMR spectrometer") were already folded
into one node (`instrument:raw:600mhz_14_1t_solid_state_nmr`) — so 6 nodes, not a loss.

> **[NOTE: NMR:1400198's rdfs:comment is "defneed" — an unauthored placeholder. The term is
> live, not deprecated, not obsolete; its meaning rests on its label, its parent
> (NMR:1400059 NMR instrument), and foaf:homepage https://www.bruker.com/de/products/mr/nmr.html.
> Cited as the most specific TRUE term per this CV's rule. The missing definition is a
> documentation gap in nmrCV v1.1.0, not a defect in the mapping.]**
>
> **Different from Finnigan LCQ (do not conflate, R2):** LCQ is `PENDING` because MS:1000031 is
> the "instrument model" ROOT and a specific LCQ term *ought to exist*. NMR:1400198 is **not**
> pending — it **is** the right term (a Bruker Avance III 600 MHz genuinely *is* a Bruker NMR
> instrument at nmrCV's granularity); only its definition is missing. Different problem, same
> inline-flag convention.
>
> **AVANCE III HD (NMR:1000371) — considered and REJECTED (R3):** it is *specific* but *false* —
> "AVANCE III HD" is a different console from "AVANCE III", so it is not true of our nodes. The
> test is **truth, not specificity** (same error class as predatoR / ATHENA). NMR:1400198 is coarse
> and TRUE; NMR:1000371 is specific and FALSE. Do not re-propose it.
>
> **`nmr_frequency_mhz` has no ontology behind it, deliberately (R4):** nmrCV has **no** 1H/proton/
> Larmor/spectrometer-frequency term (0 hits); "MHz" appears only inside NMR:1400185's prose. So
> `nmr_frequency_mhz` is a plain numeric property, no accession.
>
> **`magnetic_field_tesla` is read from the canonical name where STATED, never converted (R5,
> RULED — resolves SCIKG_SCHEMA.md:462):** 21.0/14.5/9.4 on the FT-ICR rows; 14.1 on the
> solid-state row (its string reads "14.1 T"); null everywhere else. **Do NOT convert MHz→Tesla.**
> 600 MHz ≈ 14.1 T is exact physics, and that is the trap: once written, a derived 14.1 and the
> node-1 *stated* 14.1 are indistinguishable on disk — one is a reading, the other arithmetic.
> nmrCV *has* a defined field-strength term (NMR:1400027, "The intensity of an electric, magnetic,
> or other field", subClassOf NMR:1001954 NMR acquisition parameter) — but it is a **parameter
> slot, not an instrument identity**, so it does NOT go in the Ontology ID column. Available and
> deliberately not used.

## Methods — Tier 1 Primary MS Methods

# These become Method nodes in the graph.
# Canonical IDs from PSI-MS ontology.

| Canonical | PSI-MS ID | Aliases |
|---|---|---|
| FT-ICR MS | MS:1000079 | FTICR-MS, FT-ICR mass spectrometry, Fourier transform ion cyclotron resonance MS |
| ESI | MS:1000073 | Electrospray Ionization, nano-ESI, microelectrospray, ESI Source, nanoelectrospray |
| APPI | MS:1000382 | Atmospheric Pressure Photoionization |
| APCI | MS:1000070 | Atmospheric Pressure Chemical Ionization |
| MALDI | MS:1000075 | Matrix-Assisted Laser Desorption Ionization |
| CAD | MS:1000133 | Collision Activated Dissociation |
| CID | MS:1000133 | Collision Induced Dissociation |
| ETD | MS:1000598 | Electron Transfer Dissociation, front-end ETD |
| ECD | MS:1000250 | Electron Capture Dissociation |
| MS/MS | MS:1000013 | Tandem MS, tandem mass spectrometry [PENDING: MS:1000013 is OBSOLETE and resolves to "resolution type"; no clean PSI-MS replacement — supervisor decision] |
| Top-down proteomics | MS:1003351 | Top-down MS/MS, top-down LC-MS/MS, TDMS, IP-TDMS, top-down |
| Bottom-up proteomics | MS:1003355 | Bottom-up MS, shotgun proteomics |
| De novo sequencing | MS:1001954 | top-down de novo sequencing, de-novo sequencing [PENDING: MS:1001954 resolves to "acquisition parameter" (wrong); no clean PSI-MS term — supervisor decision] |
| Internal calibration | MS:1000759 | Mass Difference Analysis, MDA, Walking Calibration |
| LC-MS/MS | MS:1000073 | reversed-phase nano-LC, nano-LC, LC-MS [PENDING: MS:1000073 resolves to "electrospray ionization" (wrong for LC-MS/MS); no single PSI-MS term — supervisor decision] |

## Methods — Tier 2 Supporting Methods

# Stored as text properties on Publication nodes only.
# Not normalized as Method nodes in v1.0.

| Canonical | Notes |
|---|---|
| Western blot | Supporting method — text property only |
| RNA-Seq | Supporting method — text property only |
| Confocal microscopy | Supporting method — text property only |
| PCR | Supporting method — text property only |
| Whole exome sequencing | Supporting method — text property only |

## Post-Translational Modifications (PTMs)

# Modification is a first-class node type in v1.0.
# UNIMOD IDs from https://www.unimod.org
# Browser: https://www.ebi.ac.uk/ols4/ontologies/unimod
# PTMs observed in 8 annotated papers.

| Canonical | UNIMOD ID | Aliases | Residues |
|---|---|---|---|
| Phosphorylation | UNIMOD:21 | phospho, phospho-S/T/Y, phos | Serine, Threonine, Tyrosine |
| Acetylation | UNIMOD:1 | acetyl, N-terminal acetylation | Lysine, N-terminus |
| O-GlcNAc glycosylation | UNIMOD:43 | O-GlcNAc, OGlcNAc | Serine, Threonine |
| Sulfation | UNIMOD:40 | sulfo, sulfated | Tyrosine |
| Selenomethionine | UNIMOD:162 | SeMet, selenomethionine substitution | Methionine |
| Ubiquitination | UNIMOD:121 | ubiquitylation, GlyGly | Lysine |
| Methylation | UNIMOD:34 | methyl | Lysine, Arginine |

## Sample Types

# WCL is an abbreviation for Whole Cell Lysate, used in RAW file
# filenames and confirmed 2026-06-29.

| Canonical | Aliases |
|---|---|
| Intact proteins | intact protein, whole protein, recombinant protein |
| Peptides | peptide, tryptic peptides, phosphopeptides |
| Glycoproteins | glycoprotein, glycopeptides |
| Proteoforms | proteoform, protein isoform |
| Cell lines | colorectal cancer cells, cancer cell lines |
| Tumor samples | primary tumor, colorectal tumor, CPTAC samples |
| Petroleum samples | Heavy Vacuum Gas Oil, HVGO, crude oil, petroleum |
| Bio-oils | biomass-derived bio-oil, biomass pyrolyzate |
| Dissolved organic matter | DOM, dissolved organic matter |
| Environmental samples | environmental contaminant, groundwater |
| Cerebrospinal fluid | CSF |
| Whole cell lysate | WCL, whole cell lysate, MG1655 WCL |

## Organisms

# Organism is a first-class node type in v1.0.
# NCBI Taxonomy IDs from https://www.ncbi.nlm.nih.gov/taxonomy

| Canonical | NCBI Taxonomy ID | Aliases |
|---|---|---|
| Homo sapiens | 9606 | human, H. sapiens |
| Pyrococcus furiosus | 2261 | P. furiosus |
| Equus caballus | 9796 | horse, equine |
| Bos taurus | 9913 | bovine, cow |
| Streptococcus | 1301 | Streptococcus sp. |

## Proteins

# Protein is a first-class node type in v1.0.
# UniProt accessions from https://www.uniprot.org

| Canonical | UniProt | Aliases |
|---|---|---|
| KRAS | P01116 | KRAS4A, KRAS4B, K-Ras |
| p53 | P04637 | TP53, tumor suppressor p53 |
| Apomyoglobin | P68082 | Myoglobin, apomyoglobin |
| Cas6 | Q8TZP7 | recombinant Cas6 |
| Hemoglobin | P69905 | Hb, hemoglobin variants |
| Carbonic Anhydrase II | P00918 | CAII, Carbonic Anhydrase |

## Facilities

| Canonical | Aliases |
|---|---|
| NHMFL ICR Facility | National High Magnetic Field Laboratory ICR, MagLab ICR, ICR facility, ICR Program NHMFL |

## Funding Agencies

| Canonical | ROR ID | Aliases |
|---|---|---|
| NSF | https://ror.org/021nxhr62 | National Science Foundation |
| NIH | https://ror.org/01cwqze88 | National Institutes of Health |
| HHS | — | Department of Health and Human Services |
| DOE | — | Department of Energy |
| NIGMS | — | National Institute of General Medical Sciences |
| NCI | — | National Cancer Institute |

## Dataset Repositories

# DataCite schema: https://schema.datacite.org
# Used for dataset node structure and repository conventions.

| Canonical | URL | Accession Format |
|---|---|---|
| MassIVE | https://massive.ucsd.edu | MSVxxxxxxxxx |
| OSF | https://osf.io | 10.17605/OSF.IO/XXXXX |
| ProteomeXchange | https://www.proteomexchange.org | PXDxxxxxxx |
| Zenodo | https://zenodo.org | 10.5281/zenodo.XXXXXXX |
