# bio.tools registry review — proposed IDs awaiting a human read

**STATUS: RETURNED — Veronika, 2026-07-17.** 14 CONFIRM → `has_id` (ClipsMS, Cutadapt, DADA2, Fiji, ggplot2, IGV, MSConvert, ProSight Lite, ProteinProspector, PyC2MC, QIIME2, SPSS, vegan, MaxQuant). MetaMorpheus and Proteoform Suite NOT confirmed (stay `proposed`); their review-article edges on `10.1002/pmic.201800361` removed. MaxQuant node confirmed but its edge on `10.1021/jasms.4c00232` removed (fuzzy hallucination — **KI-10**). MS-Align+ string authentic; identity open. Verdicts filled per-row below.

Companion to `docs/pdf_transform_logic.md` §9.2 / §9.2b / §9.3. bio.tools facts from a live re-query; corpus evidence from `data/raw/pdf_extraction/pdf_extraction_378papers.jsonl` (gitignored, local-only). Every quoted string is verbatim.

## Triage

| | count | what it needs |
|---|---:|---|
| **Rows needing your read** | **16** | CONFIRM / REJECT / UNSURE |
| **Needs the PDF, not a verdict** | 1 | `MS-Align+` — one question: **does the paper write "MS-Align+"? YES / NO** |
| **Blocked on us, not you** | 1 | `UniDec` — our string doesn't resolve; **no decision needed** |
| **Resolved by ruling, no action** | 2 | `MSAlign`, `ProteoWizard` |
| **Total rows** | 20 | |

## Paper lists are FLOORS, not totals

**Every "papers resolving to this tool" count below is a lower bound.** `KI-5`
(`docs/KNOWN_ISSUES.md`) records that **02d drops some multi-tool extractions upstream** on
span coverage: when one extracted value names several tools, the aligned span covers only the
first, coverage collapses, and the whole value is discarded before this transform ever sees
it. Those tools are real and present in their papers — they are simply invisible here.

**Known to be affected in this file: QIIME2, DADA2, ProSight Lite, MSConvert, ggplot2,
vegan** — and that list is itself a floor.

> **Do not read a short paper list as evidence against a tool.** A row showing 1 paper may
> genuinely be used in several. The counts are reported **as measured and unadjusted** — a
> patched count reads as a measured one, which is the failure KI-5 exists to keep visible.
> The fix is per-tool spans in 02d (upstream, Veronika's call), not a correction here.

## What a decision means

- **CONFIRM** — the ID is written to the node as `biotools_id`; `biotools_status` becomes `has_id`. **Identity claim, permanent, goes in the graph.**
- **REJECT** — name collision. Goes to §9.2's `REJECT_HITS`; status becomes `searched_none`.
- **UNSURE** — leave blank. Nothing is written.

## The pattern to look for

Two hits of this exact shape were **already wrong**. Both looked correct in their own record.

| our tool | bio.tools hit | what the record actually describes |
|---|---|---|
| **Predator** — NHMFL FT-ICR data station | `predatoR` | *"An R package for network-based mutation impact prediction."* |
| **Athena** — XAS/XANES (Demeter/IFEFFIT) | `ATHENA` (AI4SCR) | *"…(spatial) heterogeneity from spatial omics data."* |

> **Nothing in either bio.tools record is anomalous** — each is a correct record for a real tool. The mismatch shows **only against how the paper uses the tool**. Every row carries the verbatim `software_tools` bundle: **the bundle decides it, not the description.**

**Suspected third: `MS-Align+`** — needs the PDF; the repo cannot settle it.

## How evidence was gathered

A row's DOIs are papers whose `software_tools` string **resolves to that `canonical_name`** — not substring matches. Substring matching would list one `ProteoWizard MSConvert` bundle under *both* tools, showing false corroboration for a token naming two.

## Least-vouched-for rows

**Fiji**, **IGV**, **ProteinProspector**.

**IGV — flagged, but not because the tool looks wrong.** It is a genomics browser in an FT-ICR corpus, which is why it earned a hard look. But the same bundle names the **GDC Data Transfer Tool** — **GDC is the NIH Genomic Data Commons** — so that paper pulled genomic data, and viewing it in IGV is exactly what you would expect. That is context *for* IGV, not against it.

The reason IGV stays flagged is different and narrower: **the corpus never writes `IGV`.** Its one appearance is spelled out as `Integrative Genomics Viewer (version 2.9.4)`, so the row depends on a full-name→abbreviation map entry (§9.5 F3) rather than on the paper naming the tool as we name it.

**Fiji** — see its row: the bio.tools record's own description field is corrupted.

---

## ClipsMS

| | |
|---|---|
| **Proposed `biotools_id`** | `clipsms` |
| **bio.tools stored name** | `ClipsMS` |
| **Topics** | `Tomography`, `Proteomics experiment`, `Transcription factors and regulatory sites`, `Small molecules`, `Protein modifications` |
| **Homepage** | https://github.com/loolab2020/ClipsMS-Version-1.0.0 |
| **Papers resolving to this tool** | 1 |

**Description (verbatim):**

> An Algorithm for Analyzing Internal Fragments Resulting from Top-Down Mass Spectrometry.

**Corpus evidence — verbatim `software_tools` bundles:**

| DOI | verbatim bundle string |
|---|---|
| `10.1016/j.mcpro.2024.100814` | `Comprehensive Localization of Internal Protein Sequences (ClipsMS); Fragariyo; Excel; Fragariyo, ClipsMS, Xcalibur Qual Browser-embedded 'Xtract' algorithm (Thermo Fisher Scientific)` |

**Aliases recorded on the node (verbatim):** `ClipsMS`, `Comprehensive Localization of Internal Protein Sequences (ClipsMS)`

**Decision:** **CONFIRM — Veronika 2026-07-17.** `biotools_id` written to the node; `biotools_status: has_id`.

---

## Cutadapt

| | |
|---|---|
| **Proposed `biotools_id`** | `cutadapt` |
| **bio.tools stored name** | `Cutadapt` |
| **Topics** | `Genomics`, `Probes and primers`, `Sequencing` |
| **Homepage** | https://pypi.org/project/cutadapt/ |
| **Papers resolving to this tool** | 2 |

**Description (verbatim):**

> Find and remove adapter sequences, primers, poly-A tails and other types of unwanted sequence from your high-throughput sequencing reads.

**Corpus evidence — verbatim `software_tools` bundles:**

| DOI | verbatim bundle string |
|---|---|
| `10.1038/s43247-022-00407-8` | `eosLink-FD; Cutadapt v2.6; QIIME2 version 2019.10.0; DADA2 version 1.10.0; QIIME2 diversity alpha-rarefaction plugin` |
| `10.21203/rs.3.rs-691992/v1` | `Recoil; nf-core/ampliseq v1.1.2, Nextflow v20.10; Cutadapt v2.6; DADA2 version 1.10.0; QIIME2 version 2019.10.0; PICRUSt2 version 2.2.0-b, MinPath; Predator; custom software (PetroOrg)` |

**Aliases recorded on the node (verbatim):** `Cutadapt v2.6`

**Decision:** **CONFIRM — Veronika 2026-07-17.** `biotools_id` written to the node; `biotools_status: has_id`.

---

## DADA2

| | |
|---|---|
| **Proposed `biotools_id`** | `dada2` |
| **bio.tools stored name** | `dada2`  ⚠️ **differs from our name** |
| **Topics** | `Sequencing`, `Genetic variation`, `Microbial ecology`, `Metagenomics` |
| **Homepage** | https://bioconductor.org/packages/release/bioc/html/dada2.html |
| **Papers resolving to this tool** | 2 |

**Description (verbatim):**

> This package infers exact sequence variants (SVs) from amplicon data, replacing the commonly used and coarser OTU clustering approach. This pipeline inputs demultiplexed fastq files, and outputs the sequence variants and their sample-wise abundances after removing substitution and chimera errors. Taxonomic classification is available via a native implementation of the RDP naive Bayesian classifier.

**Corpus evidence — verbatim `software_tools` bundles:**

| DOI | verbatim bundle string |
|---|---|
| `10.1038/s43247-022-00407-8` | `eosLink-FD; Cutadapt v2.6; QIIME2 version 2019.10.0; DADA2 version 1.10.0; QIIME2 diversity alpha-rarefaction plugin` |
| `10.21203/rs.3.rs-691992/v1` | `Recoil; nf-core/ampliseq v1.1.2, Nextflow v20.10; Cutadapt v2.6; DADA2 version 1.10.0; QIIME2 version 2019.10.0; PICRUSt2 version 2.2.0-b, MinPath; Predator; custom software (PetroOrg)` |

**Aliases recorded on the node (verbatim):** `DADA2 version 1.10.0`

**Decision:** **CONFIRM — Veronika 2026-07-17.** `biotools_id` written to the node; `biotools_status: has_id`.

---

## Fiji

| | |
|---|---|
| **Proposed `biotools_id`** | `Fiji` |
| **bio.tools stored name** | `Fiji` |
| **Topics** | `Cell biology`, `Imaging` |
| **Homepage** | https://fiji.sc |
| **Papers resolving to this tool** | 1 |

**Description (verbatim):**

> A quantitative method to analyse F-actin distribution in cells.

ImageJ, with "Batteries Included".

Fiji: A batteries-included distribution of ImageJ.

Fiji bundles together many popular and useful ImageJ plugins for image analysis into one installation, and automatically manages their dependencies and updating.

> ### ⚠️ THE bio.tools RECORD'S OWN DESCRIPTION FIELD IS CORRUPTED
> The description above is quoted **verbatim and unaltered** — that is what the registry
> returns. Its **first sentence belongs to a different tool**: *"A quantitative method to
> analyse F-actin distribution in cells"* is not Fiji, which is a distribution of ImageJ.
> Someone appended one record's description to another's upstream, in bio.tools.
>
> **Judge from the Fiji sentences** ("Batteries Included" / "bundles together many popular and
> useful ImageJ plugins"), not the opening line. The corruption is in the registry's metadata,
> **not evidence that `Fiji` is the wrong ID** — but it does mean this record's description
> cannot be trusted as a whole, which is worth knowing before you CONFIRM.

**Corpus evidence — verbatim `software_tools` bundles:**

| DOI | verbatim bundle string |
|---|---|
| `10.1016/j.jbc.2022.102768` | `Xcalibur QualBrowser; ProSight Lite 1.4; ProSight PD 4.0; TDValidator 1.0; GDC Data Transfer Tool Client v1.6.1; Integrative Genomics Viewer (version 2.9.4); Fiji ImageJ using the Plot Pro fi les function; Mascot search engine (Matrix Science; version 2.8.0)` |

**Aliases recorded on the node (verbatim):** `Fiji ImageJ using the Plot Pro fi les function`

**Decision:** **CONFIRM — Veronika 2026-07-17.** `biotools_id` written to the node; `biotools_status: has_id`.

---

## ggplot2

| | |
|---|---|
| **Proposed `biotools_id`** | `ggplot2` |
| **bio.tools stored name** | `ggplot2` |
| **Topics** | `Data visualisation` |
| **Homepage** | http://ggplot2.org/ |
| **Papers resolving to this tool** | 4 |

**Description (verbatim):**

> Plotting system for R, based on the grammar of graphics.

**Corpus evidence — verbatim `software_tools` bundles:**

| DOI | verbatim bundle string |
|---|---|
| `10.1021/acs.energyfuels.3c04994` | `Composer64 or PetroOrg; R version 4.0.3; ggplot2, a component of the tidyverse package` |
| `10.1029/2022GB007495` | `Predator data station; PetroOrg; R, ggplot2, factoextra` |
| `10.1029/2024GB008212` | `PetroOrg; R; ggplot2; Vegan R package` |
| `10.1029/2025JG008899` | `PetroOrg; RStudio; Microsoft Excel; ggplot2` |

**Decision:** **CONFIRM — Veronika 2026-07-17.** `biotools_id` written to the node; `biotools_status: has_id`.

---

## IGV

| | |
|---|---|
| **Proposed `biotools_id`** | `igv` |
| **bio.tools stored name** | `IGV` |
| **Topics** | `Genomics`, `Data visualisation`, `Sequence analysis` |
| **Homepage** | http://www.broadinstitute.org/igv/ |
| **Papers resolving to this tool** | 1 |

**Description (verbatim):**

> High-performance visualization tool for interactive exploration of large, integrated datasets. It supports a wide variety of data types and format, including short-read alignments in the SAM/BAM format. Data can be viewed from local files or over the web via http.

**Corpus evidence — verbatim `software_tools` bundles:**

| DOI | verbatim bundle string |
|---|---|
| `10.1016/j.jbc.2022.102768` | `Xcalibur QualBrowser; ProSight Lite 1.4; ProSight PD 4.0; TDValidator 1.0; GDC Data Transfer Tool Client v1.6.1; Integrative Genomics Viewer (version 2.9.4); Fiji ImageJ using the Plot Pro fi les function; Mascot search engine (Matrix Science; version 2.8.0)` |

**Aliases recorded on the node (verbatim):** `Integrative Genomics Viewer (version 2.9.4)`

**Decision:** **CONFIRM — Veronika 2026-07-17.** `biotools_id` written to the node; `biotools_status: has_id`.

---

## MaxQuant

| | |
|---|---|
| **Proposed `biotools_id`** | `maxquant` |
| **bio.tools stored name** | `MaxQuant` |
| **Topics** | `Proteomics experiment`, `Proteomics`, `Statistics and probability` |
| **Homepage** | http://www.maxquant.org/ |
| **Papers resolving to this tool** | 1 |

**Description (verbatim):**

> Quantitative proteomics software package designed for analyzing large mass-spectrometric data sets. It is specifically aimed at high-resolution MS data.

**Corpus evidence — verbatim `software_tools` bundles:**

| DOI | verbatim bundle string |
|---|---|
| `10.1021/jasms.4c00232` | `Peak-by-Peak software (Spectroswiss, Lausanne, Switzerland); MaxQuant v1.6; SciPy package` |

**Aliases recorded on the node (verbatim):** `MaxQuant v1.6`

**Decision:** **CONFIRM (node/ID) — Veronika 2026-07-17.** `biotools_id: maxquant`, `biotools_status: has_id`. **But the `USES_SOFTWARE` edge to `10.1021/jasms.4c00232` is REMOVED:** Veronika read the PDF — the paper never mentions MaxQuant. The extraction was a fuzzy hallucination (`value='MaxQuant v1.6'`, span `[4899,4907]`, `MATCH_FUZZY`, `grounded=True` — `MATCH_FUZZY` is in `ACCEPTED_ALIGNMENTS`, so `_is_grounded` accepts it with **no coverage check at all**) — see **KI-10**. Node now has **0 `USES_SOFTWARE` edges (orphan)** — needs a ruling.

---

## MetaMorpheus

| | |
|---|---|
| **Proposed `biotools_id`** | `MetaMorpheus` |
| **bio.tools stored name** | `MetaMorpheus` |
| **Topics** | `Proteomics`, `Proteomics experiment`, `Protein modifications`, `Proteogenomics`, `Small molecules`, `Sequence analysis` |
| **Homepage** | https://github.com/smith-chem-wisc/MetaMorpheus |
| **Papers resolving to this tool** | 1 |

**Description (verbatim):**

> Improved Protein Inference from Multiple Protease Bottom-Up Mass Spectrometry Data | Proteomics search software with integrated calibration, PTM discovery, bottom-up, top-down and LFQ capabilities | MetaMorpheus: Free, Open-Source PTM Discovery | Download the current version here. For first-time Windows users, choose "MetaMorpheusInstaller.msi" and install MetaMorpheus. Check out our getting started video on YouTube

**Corpus evidence — verbatim `software_tools` bundles:**

| DOI | verbatim bundle string |
|---|---|
| `10.1002/pmic.201800361` | `Proteoform Suite; MetaMorpheus; MSAlign +` |

**Decision:** **NOT confirmed — stays `proposed` (Veronika 2026-07-17).** No registry confirm. **`USES_SOFTWARE` edge to `10.1002/pmic.201800361` REMOVED:** that paper is a **review** — it names MetaMorpheus but never ran it, so the edge asserted something false. Node stays; now has **0 `USES_SOFTWARE` edges (orphan)** — needs a ruling.

---

## MS-Align+

| | |
|---|---|
| **Proposed `biotools_id`** | **null — never queried under this name** |
| **bio.tools stored name** | — |
| **Topics** | — |
| **Homepage** | — |
| **`biotools_status`** | `not_attempted` (**not** `proposed`) |
| **Papers resolving to this tool** | 1 |

**Ruling 2:** `MSAlign` and `MS-Align+` are different tools. Raw extraction `[20] value='MSAlign +'`, `grounded=True`, `char_span=[59560, 59569]`, `MATCH_EXACT`. The bundle is three top-down proteomics tools; bio.tools `msalign` is an **LC-MS alignment** tool. Spacing matches the Docling artifact (`Plot Pro fi les`, `Thermo Scienti fi c`).

> ### UNRESOLVED FROM THE REPO — needs the PDF
> `data/processed/pdf_text/` does not exist, so the source span cannot be read. **Veronika: does the paper write `MS-Align+`?** If yes, this is a **third predatoR/ATHENA-class collision**.

**Corpus evidence — verbatim `software_tools` bundles:**

| DOI | verbatim bundle string |
|---|---|
| `10.1002/pmic.201800361` | `Proteoform Suite; MetaMorpheus; MSAlign +` |

**Aliases recorded on the node (verbatim):** `MSAlign +`

**Decision — one question, not a CONFIRM/REJECT.** This cannot be answered from the repo, and
CONFIRM/REJECT would invite a judgement the evidence here does not support:

> ### DOES THE PAPER WRITE "MS-Align+"?   **NO — Veronika 2026-07-17.**
> The paper writes **`MSAlign +`** (no hyphen), followed by `, [88]`. The string is
> **authentic** — the earlier Docling-artifact reading (that the spacing was an OCR
> artifact) is **refuted**. `biotools_id` stays **null**. **OPEN, not ruled:** whether
> `MSAlign +` is *MS-Align+* written without a hyphen, or a different tool, is unresolved.

If **YES** — bio.tools `msalign` (an LC-MS *alignment* tool) is a different tool from the
top-down search engine this paper ran: a **third predatoR/ATHENA-class collision**.
If **NO** — tell us what it does say, and the token goes back for re-canonicalization.

---

## MSConvert

| | |
|---|---|
| **Proposed `biotools_id`** | `msconvert` |
| **bio.tools stored name** | `msConvert`  ⚠️ **differs from our name** |
| **Topics** | `Proteomics`, `Proteomics experiment` |
| **Homepage** | http://proteowizard.sourceforge.net/tools.shtml |
| **Papers resolving to this tool** | 1 |

**Description (verbatim):**

> msConvert is a command-line utility for converting between various mass spectrometry data formats, including from raw data from several commercial companies (with vendor libraries, Windows-only). For Windows users, there is also a GUI, msConvertGUI.

**Corpus evidence — verbatim `software_tools` bundles:**

| DOI | verbatim bundle string |
|---|---|
| `10.1016/j.str.2017.08.002` | `UltraScan III software version 3.3; ProteoWizard MSConvert; StavroX; MaxQuant software at standard settings` |

**Aliases recorded on the node (verbatim):** `ProteoWizard MSConvert`

**Decision:** **CONFIRM — Veronika 2026-07-17.** `biotools_id` written to the node; `biotools_status: has_id`.

---

## ProSight Lite

| | |
|---|---|
| **Proposed `biotools_id`** | `prosight_lite` |
| **bio.tools stored name** | `ProSight Lite` |
| **Topics** | `Proteomics`, `Proteomics experiment`, `Sequence analysis`, `Epigenetics`, `Protein modifications` |
| **Homepage** | http://prosightlite.northwestern.edu/ |
| **Papers resolving to this tool** | 5 |

**Description (verbatim):**

> Free Windows application for matching a single candidate protein sequence and its modifications against a set of mass spectrometric observations.

**Corpus evidence — verbatim `software_tools` bundles:**

| DOI | verbatim bundle string |
|---|---|
| `10.1016/j.jbc.2022.102768` | `Xcalibur QualBrowser; ProSight Lite 1.4; ProSight PD 4.0; TDValidator 1.0; GDC Data Transfer Tool Client v1.6.1; Integrative Genomics Viewer (version 2.9.4); Fiji ImageJ using the Plot Pro fi les function; Mascot search engine (Matrix Science; version 2.8.0)` |
| `10.1021/acs.analchem.8b03294` | `ProSight Lite, Xtract; Xtract parameters` |
| `10.1021/jasms.1c00291` | `Xcalibur 3.0, Xtract; ProSight Lite 30; ProSight Lite` |
| `10.1021/jasms.2c00242` | `Custom software; ProSight Lite; 24 IsoPro 3.1; SciDAVis` |
| `10.1515/cclm-2020-1072` | `Xcalibur Qual Browser; ProSight Lite; TDValidator` |

**Aliases recorded on the node (verbatim):** `ProSight Lite`, `ProSight Lite 1.4`

**Decision:** **CONFIRM — Veronika 2026-07-17.** `biotools_id` written to the node; `biotools_status: has_id`.

---

## ProteinProspector

| | |
|---|---|
| **Proposed `biotools_id`** | `proteinprospector` |
| **bio.tools stored name** | `ProteinProspector` |
| **Topics** | `Proteomics`, `Proteomics experiment`, `Database management` |
| **Homepage** | http://prospector.ucsf.edu |
| **Papers resolving to this tool** | 1 |

**Description (verbatim):**

> A suite of protein identification tools.

**Corpus evidence — verbatim `software_tools` bundles:**

| DOI | verbatim bundle string |
|---|---|
| `10.1002/pmic.201300438` | `BioTools, cRAWler algorithm inside ProSightPC 3.0; ProteinProspector; MaximumEntropyDeconvolution from DataAnalysis (Bruker Daltonics, version 3.4); ProSight PC workflow; Xtract algorithm from Thermo Fisher Scientific; custom in-house software` |

**Decision:** **CONFIRM — Veronika 2026-07-17.** `biotools_id` written to the node; `biotools_status: has_id`.

---

## Proteoform Suite

| | |
|---|---|
| **Proposed `biotools_id`** | `proteoform_suite` |
| **bio.tools stored name** | `Proteoform Suite` |
| **Topics** | `Proteomics`, `Proteomics experiment`, `Protein modifications`, `Sequence analysis`, `Small molecules` |
| **Homepage** | http://smith-chem-wisc.github.io/ProteoformSuite/ |
| **Papers resolving to this tool** | 2 |

**Description (verbatim):**

> Proteoform Analysis and Construction of Proteoform Families in Proteoform Suite.

**Corpus evidence — verbatim `software_tools` bundles:**

| DOI | verbatim bundle string |
|---|---|
| `10.1002/pmic.201800361` | `Proteoform Suite; MetaMorpheus; MSAlign +` |
| `10.1021/acs.jproteome.0c00403` | `Xcalibur; TDPortal 22; Thermo Protein Deconvolution 4.0; Proteoform Suite version 0.3.6; MetaMorpheus 26; Proteoform Suite; TDPortal; Microsoft Excel` |

**Aliases recorded on the node (verbatim):** `Proteoform Suite`, `Proteoform Suite version 0.3.6`

**Decision:** **NOT confirmed — stays `proposed` (Veronika 2026-07-17).** **`USES_SOFTWARE` edge to `10.1002/pmic.201800361` REMOVED** (same review article — named, never run). Node stays; retains its edge from `10.1021/acs.jproteome.0c00403` (**1 edge**).

---

## PyC2MC

| | |
|---|---|
| **Proposed `biotools_id`** | `pyc2mc` |
| **bio.tools stored name** | `PyC2MC` |
| **Topics** | `Proteomics experiment`, `Data visualisation`, `Metagenomics` |
| **Homepage** | https://github.com/iC2MC/PyC2MC_viewer |
| **Papers resolving to this tool** | 2 |

**Description (verbatim):**

> Open-source software solution for visualization and treatment of high-resolution mass spectrometry data.

**Corpus evidence — verbatim `software_tools` bundles:**

| DOI | verbatim bundle string |
|---|---|
| `10.1021/acs.analchem.5c05562` | `Predator, PetroOrg, and PyC2MC; Xcalibur TM` |
| `10.1021/acs.energyfuels.4c05674` | `Predator Acquisition data station; Predator, PetroOrg, PyC2MC; Xcalibur` |

**Decision:** **CONFIRM — Veronika 2026-07-17.** `biotools_id` written to the node; `biotools_status: has_id`.

---

## QIIME2

| | |
|---|---|
| **Proposed `biotools_id`** | `qiime2` |
| **bio.tools stored name** | `QIIME 2`  ⚠️ **differs from our name** |
| **Topics** | `Microbial ecology`, `Metatranscriptomics`, `Metagenomics` |
| **Homepage** | https://qiime2.org |
| **Papers resolving to this tool** | 3 |

**Description (verbatim):**

> QIIME 2 is an AI-ready microbiome multi-omics data science platform that is trusted, free, open source, extensible, and community developed and supported bioinformatics.

**Corpus evidence — verbatim `software_tools` bundles:**

| DOI | verbatim bundle string |
|---|---|
| `10.1016/j.jhazmat.2021.127598` | `drEEM toolbox v. 5.0; QIIME2 (v.2019.1); q-score-joined; q2-deblur; MAFFT; FasTtree2; QIIME2; q2-feature-classify-sklearn plugin` |
| `10.1038/s43247-022-00407-8` | `eosLink-FD; Cutadapt v2.6; QIIME2 version 2019.10.0; DADA2 version 1.10.0; QIIME2 diversity alpha-rarefaction plugin` |
| `10.21203/rs.3.rs-691992/v1` | `Recoil; nf-core/ampliseq v1.1.2, Nextflow v20.10; Cutadapt v2.6; DADA2 version 1.10.0; QIIME2 version 2019.10.0; PICRUSt2 version 2.2.0-b, MinPath; Predator; custom software (PetroOrg)` |

**Aliases recorded on the node (verbatim):** `QIIME2`, `QIIME2 (v.2019.1)`, `QIIME2 version 2019.10.0`

**Decision:** **CONFIRM — Veronika 2026-07-17.** `biotools_id` written to the node; `biotools_status: has_id`.

---

## SPSS

| | |
|---|---|
| **Proposed `biotools_id`** | `spss` |
| **bio.tools stored name** | `SPSS` |
| **Topics** | **NONE — bio.tools lists no topics. The description is the ONLY evidence.** |
| **Homepage** | https://www.ibm.com/spss |
| **Papers resolving to this tool** | 2 |

**Description (verbatim):**

> The IBM SPSS software platform offers advanced statistical analysis, a vast library of machine learning algorithms, text analysis, open-source extensibility, integration with big data and seamless deployment into applications.

**Corpus evidence — verbatim `software_tools` bundles:**

| DOI | verbatim bundle string |
|---|---|
| `10.1016/j.watres.2023.119812` | `PetroOrg; SPSS 19.0; R 4.2.0; factoextra package` |
| `10.1029/2020JG005804` | `PetroOrg; R Core Team using the factoextra package (Kassambara & Mundt, 2017); SPSS` |

**Aliases recorded on the node (verbatim):** `SPSS`, `SPSS 19.0`

**Decision:** **CONFIRM — Veronika 2026-07-17.** `biotools_id` written to the node; `biotools_status: has_id`.

---

## vegan

| | |
|---|---|
| **Proposed `biotools_id`** | `vegan` |
| **bio.tools stored name** | `vegan` |
| **Topics** | `Ecology`, `Phylogenetics`, `Environmental science` |
| **Homepage** | https://cran.r-project.org/web/packages/vegan/index.html |
| **Papers resolving to this tool** | 3 |

**Description (verbatim):**

> Ordination methods, diversity analysis and other functions for community and vegetation ecologists

**Corpus evidence — verbatim `software_tools` bundles:**

| DOI | verbatim bundle string |
|---|---|
| `10.1029/2023JG007797` | `PetroOrg; vegan` |
| `10.1039/D2EM00184E` | `Predator; PetroOrg; QIIME2 pipeline (QIIME2-2019.10), scikitlearn, vegan package; checkM v1.1.2; GTDBTk v1.3.0; dRep v3.0.0; coverM genome v0.6.0` |
| `10.3389/feart.2020.552731` | `R; Vegan; FactoMineR; MASS; indicspecies; Vegan package in R` |

**Aliases recorded on the node (verbatim):** `Vegan`, `vegan`, `vegan package`

**Decision:** **CONFIRM — Veronika 2026-07-17.** `biotools_id` written to the node; `biotools_status: has_id`.

---

## UniDec

| | |
|---|---|
| **Proposed `biotools_id`** | `unidec` |
| **bio.tools stored name** | `UniDec` |
| **Topics** | `Biotherapeutics`, `Proteomics experiment`, `Workflows`, `Proteomics` |
| **Homepage** | https://github.com/michaelmarty/UniDec |
| **Papers resolving to this tool** | 0 |

**Description (verbatim):**

> UniDec processing pipeline for rapid analysis of biotherapeutic mass spectrometry data.

> ### ⚠️ BLOCKED ON US — no decision needed from you
> The one corpus string is **`UniDec (Oxford University, UK)`** (`10.1021/jasms.0c00036`). It does not resolve, so there is no evidence to review against. **This is our bug, not your call.**
>
> Oxford is UniDec's *home institution*, not a vendor — vendor-strip correctly leaves it (§9.5: the vendor list is for parties that **sell or ship** the tool; author institutions are attributions, and there is no attribution-strip). **Ruled: one token is not worth a wrong rule.** Revisit only if the shape recurs.

**No decision needed — recorded for visibility only.**

---

# Resolved by ruling — no action needed

These rows carried a proposed ID but need **no decision**: the rulings moved their evidence to the correct node. Recorded so the IDs are not re-proposed.

## MSAlign — no corpus referent

- Proposed `biotools_id`: `msalign` · stored name `msalign` · homepage http://www.ms-utils.org/msalign/index.html
- Description (verbatim): *"Aligns LC-MS and LC-MS/MS datasets using peptides identified by MS/MS and accurate mass MS."*
- **No corpus string refers to plain MSAlign.** Its only occurrence was `MSAlign +`, which **Ruling 2** resolves to **MS-Align+** (its own row above). The proposed `msalign` ID has **no referent in this corpus**. Its homepage (`ms-utils.org/msalign`) corroborates that it is the LC-MS alignment tool, a different thing from the top-down search engine.

## ProteoWizard — no corpus referent

- Proposed `biotools_id`: `proteowizard` · stored name `ProteoWizard` · homepage http://proteowizard.sourceforge.net/
- Description (verbatim): *"The ProteoWizard Library and Tools are a set of modular and extensible open-source, cross-platform tools and software libraries that facilitate proteomics data analysis."*
- Its only occurrence is inside `ProteoWizard MSConvert`, which **Ruling 1** resolves to **MSConvert** — the component the paper actually ran. The suite is not minted as a peer, so ProteoWizard has **no independent corpus evidence**. This is Ruling 1 working as intended.

