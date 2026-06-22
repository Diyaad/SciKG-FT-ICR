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
# Last updated: 2026-06-18

## Instruments

# Peripheral components (LC systems, ion sources, ICR
# cells) are not separate Instrument nodes in v1.0.
# They are recorded as text properties on Publication.
# Peripherals: ACQUITY M-Class, NanoMate, NanoLC,
# APPI Ion Max, MIDAS 160, GELFrEE 8100

| Canonical | PSI-MS ID | Aliases |
|---|---|---|
| 21T FT-ICR MS | MS:1000079 | 21 T FT-ICR MS, 21 T FT-ICR mass spectrometer, Custom-built 21 T FT-ICR MS, 21T ICR, 21 T FT-ICR, 21 Tesla FT-ICR MS, 21 T FT-ICR MS |
| 14.5T FT-ICR MS | MS:1000079 | 14.5 T FT-ICR, 14.5T FT-ICR, 14.5 T superconducting magnet, Modified 14.5 T FT-ICR, LTQ-FT MS |
| 9.4T FT-ICR MS | MS:1000079 | 9.4 T FT-ICR MS, 9.4T FT-ICR, Home-built 9.4 T FTICR instrument, 9.4 T FTICR |
| Orbitrap Eclipse Tribrid | MS:1000484 | Orbitrap Eclipse Tribrid Mass Spectrometer |
| Q-Exactive HF | MS:1000484 | Q Exactive HF Hybrid Quadrupole-Orbitrap, Q-Exactive HF BioPharma, Q Exactive HF |
| Velos Pro | MS:1000484 | Velos Pro dual-cell linear ion trap, Velos Pro linear ion trap |
| TOF MS | MS:1000084 | TOF, time-of-flight |
| Finnigan TSQ | MS:1000031 | Finnigan TSQ |
| Finnigan LCQ | MS:1000031 | Finnigan LCQ, Finnigan LSQ |

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
| MS/MS | MS:1000013 | Tandem MS, tandem mass spectrometry |
| Top-down proteomics | MS:1002586 | Top-down MS/MS, top-down LC-MS/MS, TDMS, IP-TDMS, top-down |
| Bottom-up proteomics | MS:1002314 | Bottom-up MS, shotgun proteomics |
| De novo sequencing | MS:1001954 | top-down de novo sequencing, de-novo sequencing |
| Internal calibration | MS:1000787 | Mass Difference Analysis, MDA, Walking Calibration |
| LC-MS/MS | MS:1000073 | reversed-phase nano-LC, nano-LC, LC-MS |

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
