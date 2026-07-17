# Software field -- DRY RUN (nothing minted)

Generated 2026-07-16T22:23:26.195985+00:00 by `scripts/transform_pdf_software.py`.
Input: `data/raw/pdf_extraction/pdf_extraction_378papers.jsonl` (gitignored, local-only).

## Three-way extraction accounting (Sec 2.-1)

- **233** with a software value
- **144** genuine negatives (ran, found nothing grounded)
- **1** failed extractions -- missing, not absent
  - `10.1016/j.tube.2017.08.011` (ran_but_empty)

## Routing

486 tokens from 191 distinct bundle strings.

| route | tokens |
|---|---:|
| MINT | 280 |
| REVIEW | 164 |
| ROUTE_OUT | 28 |
| REJECT | 9 |
| PUB_PROPERTY | 5 |

## Per-token

| raw string | token | canonical_name | vendor | version | route | why |
|---|---|---|---|---|---|---|
| `ADF 2017; ADF` | `ADF 2017` | `ADF` | -- | `2017` | **MINT** | canonical map |
| `ADF 2017; ADF` | `ADF` | `ADF` | -- | -- | **MINT** | canonical map |
| `ArcGIS 10.2; MATLAB R2015b; R i386 2.15.2` | `ArcGIS 10.2` | `ArcGIS` | -- | `10.2` | **MINT** | canonical map |
| `Basic Local Alignment Search Tool server` | `Basic Local Alignment Search Tool server` | `BLAST` | -- | -- | **MINT** | F3: full name -> abbreviation (explicit map) |
| `BioTools, cRAWler algorithm inside ProSightPC 3.0; ProteinPr` | `BioTools` | `BioTools` | -- | -- | **MINT** | canonical map |
| `BioTools, cRAWler algorithm inside ProSightPC 3.0; ProteinPr` | `ProteinProspector` | `ProteinProspector` | -- | -- | **MINT** | canonical map |
| `Bruker Daltonics Data Analysis software` | `Bruker Daltonics Data Analysis software` | `DataAnalysis` | `Bruker` | -- | **MINT** | canonical map |
| `Bruker Data Analysis 4.0 or Predator Analysis 4.1.8` | `Bruker Data Analysis 4.0` | `DataAnalysis` | `Bruker` | `4.0` | **MINT** | canonical map |
| `Bruker Data Analysis 4.0 or Predator Analysis 4.1.8` | `Predator Analysis 4.1.8` | `Predator` | -- | `4.1.8` | **MINT** | canonical map |
| `Bruker Data Analysis 5.1, SmartFormula` | `Bruker Data Analysis 5.1` | `DataAnalysis` | `Bruker` | `5.1` | **MINT** | canonical map |
| `Bruker Data Analysis 5.1, SmartFormula` | `SmartFormula` | `SmartFormula` | -- | -- | **MINT** | canonical map |
| `CDS 3.02A software made by AVIV Biomedical, Inc.; Felix 3.2;` | `Microsoft Excel` | `Microsoft Excel` | -- | -- | **MINT** | canonical map |
| `ChromCALC` | `ChromCALC` | `ChromCALC` | -- | -- | **MINT** | canonical map |
| `Composer` | `Composer` | `Composer` | `Sierra Analytics` | -- | **MINT** | canonical map |
| `Composer64 or PetroOrg; R version 4.0.3; ggplot2, a componen` | `Composer64` | `Composer` | `Sierra Analytics` | -- | **MINT** | canonical map |
| `Composer64 or PetroOrg; R version 4.0.3; ggplot2, a componen` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Composer64 or PetroOrg; R version 4.0.3; ggplot2, a componen` | `R version 4.0.3` | `R` | -- | `4.0.3` | **MINT** | canonical map |
| `Composer64 or PetroOrg; R version 4.0.3; ggplot2, a componen` | `ggplot2` | `ggplot2` | -- | -- | **MINT** | canonical map |
| `Comprehensive Localization of Internal Protein Sequences (Cl` | `Comprehensive Localization of Internal P` | `ClipsMS` | -- | -- | **MINT** | F3: parenthetical names a known tool |
| `Comprehensive Localization of Internal Protein Sequences (Cl` | `Fragariyo` | `Fragariyo` | -- | -- | **MINT** | canonical map |
| `Comprehensive Localization of Internal Protein Sequences (Cl` | `Excel` | `Microsoft Excel` | -- | -- | **MINT** | canonical map |
| `Comprehensive Localization of Internal Protein Sequences (Cl` | `Fragariyo` | `Fragariyo` | -- | -- | **MINT** | canonical map |
| `Comprehensive Localization of Internal Protein Sequences (Cl` | `ClipsMS` | `ClipsMS` | -- | -- | **MINT** | canonical map |
| `CoreMS` | `CoreMS` | `CoreMS` | -- | -- | **MINT** | canonical map |
| `Custom software (PetroOrg © )` | `Custom software (PetroOrg © )` | `PetroOrg` | -- | -- | **MINT** | F3: parenthetical names a known tool |
| `Custom software; ProSight Lite; 24 IsoPro 3.1; SciDAVis` | `ProSight Lite` | `ProSight Lite` | -- | -- | **MINT** | canonical map |
| `DataAnalysis (ver. 4.4); OriginPro (ver. 2016)` | `DataAnalysis (ver. 4.4)` | `DataAnalysis` | -- | `4.4` | **MINT** | canonical map |
| `DataAnalysis (ver. 4.4); OriginPro (ver. 2016)` | `OriginPro (ver. 2016)` | `OriginPro` | -- | `2016` | **MINT** | canonical map |
| `DataAnalysis software (Bruker); 'Transhumus' software` | `DataAnalysis software (Bruker)` | `DataAnalysis` | `Bruker` | -- | **MINT** | canonical map |
| `EMPOWER3` | `EMPOWER3` | `EMPOWER3` | -- | -- | **MINT** | canonical map |
| `EMPOWER3; Predator Analysis, PetroOrg` | `EMPOWER3` | `EMPOWER3` | -- | -- | **MINT** | canonical map |
| `EMPOWER3; Predator Analysis, PetroOrg` | `Predator Analysis` | `Predator` | -- | -- | **MINT** | canonical map |
| `EMPOWER3; Predator Analysis, PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Empower 3 Chromatography Data Software; 8,76 Predator data s` | `Empower 3 Chromatography Data Software` | `EMPOWER3` | -- | -- | **MINT** | F3: full name -> abbreviation (explicit map) |
| `Empower 3 Chromatography Data Software; 8,76 Predator data s` | `Predator data station` | `Predator` | -- | -- | **MINT** | canonical map |
| `Empower 3 Chromatography Data Software; 8,76 Predator data s` | `Predator Software` | `Predator` | -- | -- | **MINT** | canonical map |
| `Empower 3 Chromatography Data Software; 8,76 Predator data s` | `PetroOrg Software` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `EnviroOrg` | `EnviroOrg` | `EnviroOrg` | -- | -- | **MINT** | canonical map |
| `EnviroOrg` | `EnviroOrg` | `EnviroOrg` | -- | -- | **MINT** | canonical map |
| `EnviroOrg` | `EnviroOrg` | `EnviroOrg` | -- | -- | **MINT** | canonical map |
| `EnviroOrg` | `EnviroOrg` | `EnviroOrg` | -- | -- | **MINT** | canonical map |
| `EnviroOrg TM software` | `EnviroOrg TM software` | `EnviroOrg` | -- | -- | **MINT** | canonical map |
| `EnviroOrg software` | `EnviroOrg software` | `EnviroOrg` | -- | -- | **MINT** | canonical map |
| `EnviroOrg; CO2Calc program; fouriertransform Python package` | `EnviroOrg` | `EnviroOrg` | -- | -- | **MINT** | canonical map |
| `EnviroOrg; DADA2 pipeline; R software v.3.6.2; Tri-carb 2800` | `EnviroOrg` | `EnviroOrg` | -- | -- | **MINT** | canonical map |
| `EnviroOrg; DADA2 pipeline; R software v.3.6.2; Tri-carb 2800` | `R software v.3.6.2` | `R` | -- | `3.6.2` | **MINT** | canonical map |
| `EnviroOrg; JMP software, version 13.1.0` | `EnviroOrg` | `EnviroOrg` | -- | -- | **MINT** | canonical map |
| `EnviroOrg; JMP software, version 13.1.0` | `JMP software` | `JMP` | -- | `13.1.0` | **MINT** | canonical map |
| `EnviroOrg; Prism 6 by GraphPad; Fourier transform Python pac` | `EnviroOrg` | `EnviroOrg` | -- | -- | **MINT** | canonical map |
| `FT-ICR MS; ChromCALC; PetroOrg` | `ChromCALC` | `ChromCALC` | -- | -- | **MINT** | canonical map |
| `FT-ICR MS; ChromCALC; PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Fityk; Athena; PetroOrg ©; R package 'vegan'` | `Athena` | `Athena` | -- | -- | **MINT** | canonical map |
| `Fityk; Athena; PetroOrg ©; R package 'vegan'` | `PetroOrg ©` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Gas chromatography/mass spectrometry; Predator; Custom softw` | `Predator` | `Predator` | -- | -- | **MINT** | canonical map |
| `Gas chromatography/mass spectrometry; Predator; Custom softw` | `Custom software (PetroOrg)` | `PetroOrg` | -- | -- | **MINT** | F3: parenthetical names a known tool |
| `MATLAB (R2014A); Microsoft Excel 2016; MATLAB` | `Microsoft Excel 2016` | `Microsoft Excel` | -- | `2016` | **MINT** | canonical map |
| `MATLAB (R2014A); Microsoft Excel 2016; MATLAB` | `MATLAB` | `MATLAB` | -- | -- | **MINT** | canonical map |
| `MATLAB ™ v6.9; R.3.5.0` | `MATLAB ™ v6.9` | `MATLAB` | -- | `6.9` | **MINT** | canonical map |
| `MATLAB; DrEEM toolbox; JMP Pro 12 (SAS Institute)` | `MATLAB` | `MATLAB` | -- | -- | **MINT** | canonical map |
| `MATLAB; DrEEM toolbox; JMP Pro 12 (SAS Institute)` | `DrEEM toolbox` | `drEEM` | -- | -- | **MINT** | canonical map |
| `MATLAB; Primer v.6.2; Primer 6 (version 6.1.13)` | `MATLAB` | `MATLAB` | -- | -- | **MINT** | canonical map |
| `MIDAS` | `MIDAS` | `MIDAS` | -- | -- | **MINT** | canonical map |
| `MIDAS Predator Analysis` | `MIDAS Predator Analysis` | `MIDAS` | -- | -- | **MINT** | adjacent-pair split (Diya) |
| `MIDAS Predator Analysis` | `MIDAS Predator Analysis` | `Predator` | -- | -- | **MINT** | adjacent-pair split (Diya) |
| `MIDAS Predator Analysis and Molecular Formula Calculator; FL` | `MIDAS Predator Analysis` | `MIDAS` | -- | -- | **MINT** | adjacent-pair split (Diya) |
| `MIDAS Predator Analysis and Molecular Formula Calculator; FL` | `MIDAS Predator Analysis` | `Predator` | -- | -- | **MINT** | adjacent-pair split (Diya) |
| `MIDAS Predator Analysis, PetroOrg` | `MIDAS Predator Analysis` | `MIDAS` | -- | -- | **MINT** | adjacent-pair split (Diya) |
| `MIDAS Predator Analysis, PetroOrg` | `MIDAS Predator Analysis` | `Predator` | -- | -- | **MINT** | adjacent-pair split (Diya) |
| `MIDAS Predator Analysis, PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Magicplot` | `Magicplot` | `Magicplot` | -- | -- | **MINT** | canonical map |
| `Magicplot` | `Magicplot` | `Magicplot` | -- | -- | **MINT** | canonical map |
| `MatLab` | `MatLab` | `MATLAB` | -- | -- | **MINT** | canonical map |
| `Matlab, drEEM toolbox (Murphy et al., 2013)` | `Matlab` | `MATLAB` | -- | -- | **MINT** | canonical map |
| `Microsoft Excel 2013` | `Microsoft Excel 2013` | `Microsoft Excel` | -- | `2013` | **MINT** | canonical map |
| `Mnova NMR software` | `Mnova NMR software` | `Mnova` | -- | -- | **MINT** | canonical map |
| `Modgraph implemented in MestReNova 10.0.1 (Mestrelab Researc` | `Predator Analysis (version 4.1.9)` | `Predator` | -- | `4.1.9` | **MINT** | canonical map |
| `NMR and high-resolution MS analyses; PetroOrg N-15.0` | `PetroOrg N-15.0` | `PetroOrg` | -- | `N-15.0` | **MINT** | canonical map |
| `NovaWin; PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PREDATOR, PetroOrg N-18.3 Software` | `PREDATOR` | `Predator` | -- | -- | **MINT** | canonical map |
| `PREDATOR, PetroOrg N-18.3 Software` | `PetroOrg N-18.3 Software` | `PetroOrg` | -- | `N-18.3` | **MINT** | canonical map |
| `PREDATOR; PetroOrg` | `PREDATOR` | `Predator` | -- | -- | **MINT** | canonical map |
| `PREDATOR; PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PREDATOR; PetroOrg` | `PREDATOR` | `Predator` | -- | -- | **MINT** | canonical map |
| `PREDATOR; PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Peak-by-Peak software (Spectroswiss, Lausanne, Switzerland);` | `MaxQuant v1.6` | `MaxQuant` | -- | `1.6` | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg ` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg ; XLStat` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg N-16.0 Software` | `PetroOrg N-16.0 Software` | `PetroOrg` | -- | `N-16.0` | **MINT** | canonical map |
| `PetroOrg N-18.3` | `PetroOrg N-18.3` | `PetroOrg` | -- | `N-18.3` | **MINT** | canonical map |
| `PetroOrg N-18.3 Software` | `PetroOrg N-18.3 Software` | `PetroOrg` | -- | `N-18.3` | **MINT** | canonical map |
| `PetroOrg N13.3` | `PetroOrg N13.3` | `PetroOrg` | -- | `N13.3` | **MINT** | canonical map |
| `PetroOrg N8.6` | `PetroOrg N8.6` | `PetroOrg` | -- | `N8.6` | **MINT** | canonical map |
| `PetroOrg Software` | `PetroOrg Software` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg Software` | `PetroOrg Software` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg Software; factoextra package` | `PetroOrg Software` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg Software; factoextra package` | `factoextra package` | `factoextra` | -- | -- | **MINT** | canonical map |
| `PetroOrg TM; R Statistical Software v.4.1.3; 'rstatix' v.0.7` | `PetroOrg TM` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg software` | `PetroOrg software` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg software` | `PetroOrg software` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg software (version 18.0.5)` | `PetroOrg software (version 18.0.5)` | `PetroOrg` | -- | `18.0.5` | **MINT** | canonical map |
| `PetroOrg(c)` | `PetroOrg(c)` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg, Kendrick mass defect analysis with PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg; EnviroOrg (NHMFL software by Yuri Corilo); NHMFL s` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg; GraphPad Prism 10.4` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg; GraphPad Prism 10.4` | `GraphPad Prism 10.4` | `GraphPad Prism` | -- | `10.4` | **MINT** | canonical map |
| `PetroOrg; JMP software (v. 7.0.1)` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg; JMP software (v. 7.0.1)` | `JMP software (v. 7.0.1)` | `JMP` | -- | `7.0.1` | **MINT** | canonical map |
| `PetroOrg; Matlab with the drEEM toolbox` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg; Matlab with the drEEM toolbox` | `Matlab with the drEEM toolbox` | `drEEM` | -- | -- | **MINT** | Ruling 1: suite/component -> component |
| `PetroOrg; Multiple Analytical Tools` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg; NanoDrop 2000c spectrophotometer; GraphPad Prism v` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg; NanoDrop 2000c spectrophotometer; GraphPad Prism v` | `GraphPad Prism version 10.3.1` | `GraphPad Prism` | -- | `10.3.1` | **MINT** | canonical map |
| `PetroOrg; R` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg; R` | `R` | `R` | -- | -- | **MINT** | canonical map |
| `PetroOrg; R` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg; R` | `R` | `R` | -- | -- | **MINT** | canonical map |
| `PetroOrg; R (Version 1.1.463); FactoMine R package; Ecodist ` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg; R (Version 1.1.463); FactoMine R package; Ecodist ` | `R (Version 1.1.463)` | `R` | -- | `1.1.463` | **MINT** | canonical map |
| `PetroOrg; R Core Team using the factoextra package (Kassamba` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg; R Core Team using the factoextra package (Kassamba` | `SPSS` | `SPSS` | -- | -- | **MINT** | canonical map |
| `PetroOrg; R version 4.1.2` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg; R version 4.1.2` | `R version 4.1.2` | `R` | -- | `4.1.2` | **MINT** | canonical map |
| `PetroOrg; R; ggplot2; Vegan R package` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg; R; ggplot2; Vegan R package` | `R` | `R` | -- | -- | **MINT** | canonical map |
| `PetroOrg; R; ggplot2; Vegan R package` | `ggplot2` | `ggplot2` | -- | -- | **MINT** | canonical map |
| `PetroOrg; RStudio; Microsoft Excel; ggplot2` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg; RStudio; Microsoft Excel; ggplot2` | `Microsoft Excel` | `Microsoft Excel` | -- | -- | **MINT** | canonical map |
| `PetroOrg; RStudio; Microsoft Excel; ggplot2` | `ggplot2` | `ggplot2` | -- | -- | **MINT** | canonical map |
| `PetroOrg; SPSS 19.0; R 4.2.0; factoextra package` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg; SPSS 19.0; R 4.2.0; factoextra package` | `SPSS 19.0` | `SPSS` | -- | `19.0` | **MINT** | canonical map |
| `PetroOrg; SPSS 19.0; R 4.2.0; factoextra package` | `R 4.2.0` | `R` | -- | `4.2.0` | **MINT** | canonical map |
| `PetroOrg; SPSS 19.0; R 4.2.0; factoextra package` | `factoextra package` | `factoextra` | -- | -- | **MINT** | canonical map |
| `PetroOrg; k-Means clustering analysis; RStudio version 2023.` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg; vegan` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `PetroOrg; vegan` | `vegan` | `vegan` | -- | -- | **MINT** | canonical map |
| `PetroOrg©,™ (Corilo, 2015)` | `PetroOrg©` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Petrorg data processing software` | `Petrorg data processing software` | `PetroOrg` | -- | -- | **MINT** | Sec 9.8 confirm bucket: ACCEPTED |
| `Predator` | `Predator` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator` | `Predator` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator` | `Predator` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator` | `Predator` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator` | `Predator` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator Acquisition data station; Predator, PetroOrg, PyC2M` | `Predator` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator Acquisition data station; Predator, PetroOrg, PyC2M` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Predator Acquisition data station; Predator, PetroOrg, PyC2M` | `PyC2MC` | `PyC2MC` | -- | -- | **MINT** | canonical map |
| `Predator Acquisition data station; Predator, PetroOrg, PyC2M` | `Xcalibur` | `Xcalibur` | -- | -- | **MINT** | canonical map |
| `Predator Analysis software; R` | `Predator Analysis software` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator Analysis software; R` | `R` | `R` | -- | -- | **MINT** | canonical map |
| `Predator Analysis, PetroOrg` | `Predator Analysis` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator Analysis, PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Predator Analysis; PetroOrg` | `Predator Analysis` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator Analysis; PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Predator Software` | `Predator Software` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator analysis software; R` | `Predator analysis software` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator analysis software; R` | `R` | `R` | -- | -- | **MINT** | canonical map |
| `Predator analysis, PetroOrg` | `Predator analysis` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator analysis, PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Predator and PetroOrg` | `Predator` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator and PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Predator and PetroOrg` | `Predator` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator and PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Predator data station, Xian et al.; PetroOrg; Athena; R stat` | `Predator data station` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator data station, Xian et al.; PetroOrg; Athena; R stat` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Predator data station, Xian et al.; PetroOrg; Athena; R stat` | `Athena` | `Athena` | -- | -- | **MINT** | canonical map |
| `Predator data station; PetroOrg, in-house developed MATLAB s` | `Predator data station` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator data station; PetroOrg, in-house developed MATLAB s` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Predator data station; PetroOrg; R, ggplot2, factoextra` | `Predator data station` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator data station; PetroOrg; R, ggplot2, factoextra` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Predator data station; PetroOrg; R, ggplot2, factoextra` | `R` | `R` | -- | -- | **MINT** | canonical map |
| `Predator data station; PetroOrg; R, ggplot2, factoextra` | `ggplot2` | `ggplot2` | -- | -- | **MINT** | canonical map |
| `Predator data station; PetroOrg; R, ggplot2, factoextra` | `factoextra` | `factoextra` | -- | -- | **MINT** | canonical map |
| `Predator software package` | `Predator software package` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator, PetroOrg Software` | `Predator` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator, PetroOrg Software` | `PetroOrg Software` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Predator, PetroOrg, and PyC2MC; Xcalibur TM` | `Predator` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator, PetroOrg, and PyC2MC; Xcalibur TM` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Predator, PetroOrg, and PyC2MC; Xcalibur TM` | `PyC2MC` | `PyC2MC` | -- | -- | **MINT** | canonical map |
| `Predator, PetroOrg, and PyC2MC; Xcalibur TM` | `Xcalibur TM` | `Xcalibur` | -- | -- | **MINT** | canonical map |
| `Predator; PC-Ord software (version 4, MjM Software Design)` | `Predator` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator; PetroOrg` | `Predator` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator; PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Predator; PetroOrg` | `Predator` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator; PetroOrg` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Predator; PetroOrg software` | `Predator` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator; PetroOrg software` | `PetroOrg software` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Predator; PetroOrg; QIIME2 pipeline (QIIME2-2019.10), scikit` | `Predator` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator; PetroOrg; QIIME2 pipeline (QIIME2-2019.10), scikit` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `Predator; PetroOrg; QIIME2 pipeline (QIIME2-2019.10), scikit` | `vegan package` | `vegan` | -- | -- | **MINT** | canonical map |
| `Predator; Ribosomal Database Project (RDP), Silva database` | `Predator` | `Predator` | -- | -- | **MINT** | canonical map |
| `Predator; THRASH algorithm; ProSight Lite (v1.4, build 1.4.6` | `Predator` | `Predator` | -- | -- | **MINT** | canonical map |
| `ProSight Lite, Xtract; Xtract parameters` | `ProSight Lite` | `ProSight Lite` | -- | -- | **MINT** | canonical map |
| `Proteoform Suite; MetaMorpheus; MSAlign +` | `Proteoform Suite` | `Proteoform Suite` | -- | -- | **MINT** | canonical map |
| `Proteoform Suite; MetaMorpheus; MSAlign +` | `MetaMorpheus` | `MetaMorpheus` | -- | -- | **MINT** | canonical map |
| `Proteoform Suite; MetaMorpheus; MSAlign +` | `MSAlign +` | `MS-Align+` | -- | -- | **MINT** | Ruling 2: MS-Align+ (distinct from MSAlign) |
| `Python` | `Python` | `Python` | -- | -- | **MINT** | canonical map |
| `Python` | `Python` | `Python` | -- | -- | **MINT** | canonical map |
| `Qubit protein assay kit; Xcalibur` | `Xcalibur` | `Xcalibur` | -- | -- | **MINT** | canonical map |
| `R version 3.5` | `R version 3.5` | `R` | -- | `3.5` | **MINT** | canonical map |
| `R, phyloseq library` | `R` | `R` | -- | -- | **MINT** | canonical map |
| `R; Vegan; FactoMineR; MASS; indicspecies; Vegan package in R` | `R` | `R` | -- | -- | **MINT** | canonical map |
| `R; Vegan; FactoMineR; MASS; indicspecies; Vegan package in R` | `Vegan` | `vegan` | -- | -- | **MINT** | canonical map |
| `R; rstatix` | `R` | `R` | -- | -- | **MINT** | canonical map |
| `Recoil; nf-core/ampliseq v1.1.2, Nextflow v20.10; Cutadapt v` | `Cutadapt v2.6` | `Cutadapt` | -- | `2.6` | **MINT** | canonical map |
| `Recoil; nf-core/ampliseq v1.1.2, Nextflow v20.10; Cutadapt v` | `DADA2 version 1.10.0` | `DADA2` | -- | `1.10.0` | **MINT** | canonical map |
| `Recoil; nf-core/ampliseq v1.1.2, Nextflow v20.10; Cutadapt v` | `QIIME2 version 2019.10.0` | `QIIME2` | -- | `2019.10.0` | **MINT** | canonical map |
| `Recoil; nf-core/ampliseq v1.1.2, Nextflow v20.10; Cutadapt v` | `Predator` | `Predator` | -- | -- | **MINT** | canonical map |
| `Recoil; nf-core/ampliseq v1.1.2, Nextflow v20.10; Cutadapt v` | `custom software (PetroOrg)` | `PetroOrg` | -- | -- | **MINT** | F3: parenthetical names a known tool |
| `Thermo Compound Discoverer` | `Thermo Compound Discoverer` | `Compound Discoverer` | `Thermo` | -- | **MINT** | canonical map |
| `Thermo Xcalibur software (version 3.0.63) and a custom-built` | `Thermo Xcalibur software (version 3.0.63` | `Xcalibur` | `Thermo` | `3.0.63` | **MINT** | canonical map |
| `UltraScan III software version 3.3; ProteoWizard MSConvert; ` | `ProteoWizard MSConvert` | `MSConvert` | -- | -- | **MINT** | Ruling 1: suite/component -> component |
| `Xcaliber` | `Xcaliber` | `Xcalibur` | -- | -- | **MINT** | Sec 9.8 confirm bucket: ACCEPTED |
| `Xcalibur` | `Xcalibur` | `Xcalibur` | -- | -- | **MINT** | canonical map |
| `Xcalibur 2.1; ProSightPC` | `Xcalibur 2.1` | `Xcalibur` | -- | `2.1` | **MINT** | canonical map |
| `Xcalibur 2.1; ProSightPC` | `ProSightPC` | `ProSightPC` | -- | -- | **MINT** | canonical map |
| `Xcalibur 2.1; R 3.3` | `Xcalibur 2.1` | `Xcalibur` | -- | `2.1` | **MINT** | canonical map |
| `Xcalibur 2.1; R 3.3` | `R 3.3` | `R` | -- | `3.3` | **MINT** | canonical map |
| `Xcalibur 3.0, Xtract; ProSight Lite 30; ProSight Lite` | `Xcalibur 3.0` | `Xcalibur` | -- | `3.0` | **MINT** | canonical map |
| `Xcalibur 3.0, Xtract; ProSight Lite 30; ProSight Lite` | `ProSight Lite` | `ProSight Lite` | -- | -- | **MINT** | canonical map |
| `Xcalibur Qual Browser; ProSight Lite; TDValidator` | `ProSight Lite` | `ProSight Lite` | -- | -- | **MINT** | canonical map |
| `Xcalibur Qual Browser; ProSight Lite; TDValidator` | `TDValidator` | `TDValidator` | -- | -- | **MINT** | canonical map |
| `Xcalibur QualBrowser; ProSight Lite 1.4; ProSight PD 4.0; TD` | `ProSight Lite 1.4` | `ProSight Lite` | -- | `1.4` | **MINT** | canonical map |
| `Xcalibur QualBrowser; ProSight Lite 1.4; ProSight PD 4.0; TD` | `ProSight PD 4.0` | `ProSight PD` | -- | `4.0` | **MINT** | canonical map |
| `Xcalibur QualBrowser; ProSight Lite 1.4; ProSight PD 4.0; TD` | `TDValidator 1.0` | `TDValidator` | -- | `1.0` | **MINT** | canonical map |
| `Xcalibur QualBrowser; ProSight Lite 1.4; ProSight PD 4.0; TD` | `Integrative Genomics Viewer (version 2.9` | `IGV` | -- | `2.9.4` | **MINT** | F3: full name -> abbreviation (explicit map) |
| `Xcalibur QualBrowser; ProSight Lite 1.4; ProSight PD 4.0; TD` | `Fiji ImageJ using the Plot Pro fi les fu` | `Fiji` | -- | -- | **MINT** | Ruling 1: suite/component -> component |
| `Xcalibur software (Thermo Fisher Scientific)` | `Xcalibur software (Thermo Fisher Scienti` | `Xcalibur` | `Thermo` | -- | **MINT** | canonical map |
| `Xcalibur; Predator analysis software` | `Xcalibur` | `Xcalibur` | -- | -- | **MINT** | canonical map |
| `Xcalibur; Predator analysis software` | `Predator analysis software` | `Predator` | -- | -- | **MINT** | canonical map |
| `Xcalibur; TDPortal 22; Thermo Protein Deconvolution 4.0; Pro` | `Xcalibur` | `Xcalibur` | -- | -- | **MINT** | canonical map |
| `Xcalibur; TDPortal 22; Thermo Protein Deconvolution 4.0; Pro` | `Proteoform Suite version 0.3.6` | `Proteoform Suite` | -- | `0.3.6` | **MINT** | canonical map |
| `Xcalibur; TDPortal 22; Thermo Protein Deconvolution 4.0; Pro` | `Proteoform Suite` | `Proteoform Suite` | -- | -- | **MINT** | canonical map |
| `Xcalibur; TDPortal 22; Thermo Protein Deconvolution 4.0; Pro` | `TDPortal` | `TDPortal` | -- | -- | **MINT** | canonical map |
| `Xcalibur; TDPortal 22; Thermo Protein Deconvolution 4.0; Pro` | `Microsoft Excel` | `Microsoft Excel` | -- | -- | **MINT** | canonical map |
| `Xcalibur; Xcalibur 3.0` | `Xcalibur` | `Xcalibur` | -- | -- | **MINT** | canonical map |
| `Xcalibur; Xcalibur 3.0` | `Xcalibur 3.0` | `Xcalibur` | -- | `3.0` | **MINT** | canonical map |
| `Xcalibur; Xcalibur and MIDAS` | `Xcalibur` | `Xcalibur` | -- | -- | **MINT** | canonical map |
| `Xcalibur; Xcalibur and MIDAS` | `Xcalibur` | `Xcalibur` | -- | -- | **MINT** | canonical map |
| `Xcalibur; Xcalibur and MIDAS` | `MIDAS` | `MIDAS` | -- | -- | **MINT** | canonical map |
| `Xtract algorithm; ReSpect™ algorithm; Mascot; SDS-PAGE; Pro-` | `Mascot` | `Mascot` | -- | -- | **MINT** | canonical map |
| `drEEM toolbox for MATLAB; EnviroOrg` | `drEEM toolbox for MATLAB` | `drEEM` | -- | -- | **MINT** | Ruling 1: suite/component -> component |
| `drEEM toolbox for MATLAB; EnviroOrg` | `EnviroOrg` | `EnviroOrg` | -- | -- | **MINT** | canonical map |
| `drEEM toolbox in MATLAB` | `drEEM toolbox in MATLAB` | `drEEM` | -- | -- | **MINT** | Ruling 1: suite/component -> component |
| `drEEM toolbox v. 5.0; QIIME2 (v.2019.1); q-score-joined; q2-` | `drEEM toolbox v. 5.0` | `drEEM` | -- | `5.0` | **MINT** | canonical map |
| `drEEM toolbox v. 5.0; QIIME2 (v.2019.1); q-score-joined; q2-` | `QIIME2 (v.2019.1)` | `QIIME2` | -- | `2019.1` | **MINT** | canonical map |
| `drEEM toolbox v. 5.0; QIIME2 (v.2019.1); q-score-joined; q2-` | `QIIME2` | `QIIME2` | -- | -- | **MINT** | canonical map |
| `drEEM toolbox; MatLab code` | `drEEM toolbox` | `drEEM` | -- | -- | **MINT** | canonical map |
| `eosLink-FD; Cutadapt v2.6; QIIME2 version 2019.10.0; DADA2 v` | `Cutadapt v2.6` | `Cutadapt` | -- | `2.6` | **MINT** | canonical map |
| `eosLink-FD; Cutadapt v2.6; QIIME2 version 2019.10.0; DADA2 v` | `QIIME2 version 2019.10.0` | `QIIME2` | -- | `2019.10.0` | **MINT** | canonical map |
| `eosLink-FD; Cutadapt v2.6; QIIME2 version 2019.10.0; DADA2 v` | `DADA2 version 1.10.0` | `DADA2` | -- | `1.10.0` | **MINT** | canonical map |
| `in-house software (EnviroOrg); ArcMap 10` | `in-house software (EnviroOrg)` | `EnviroOrg` | -- | -- | **MINT** | F3: parenthetical names a known tool |
| `modular ICR data station (Predator)` | `modular ICR data station (Predator)` | `Predator` | -- | -- | **MINT** | F3: parenthetical names a known tool |
| `modular ICR data station (Predator)` | `modular ICR data station (Predator)` | `Predator` | -- | -- | **MINT** | F3: parenthetical names a known tool |
| `modular ion cyclotron resonance data acquisition system, Pet` | `PetroOrg` | `PetroOrg` | -- | -- | **MINT** | canonical map |
| `BioTools, cRAWler algorithm inside ProSightPC 3.0; ProteinPr` | `custom in-house software` | -- | -- | -- | **PUB_PROPERTY** | generic-but-real; software_mentioned_raw |
| `Custom software; ProSight Lite; 24 IsoPro 3.1; SciDAVis` | `Custom software` | -- | -- | -- | **PUB_PROPERTY** | generic-but-real; software_mentioned_raw |
| `PetroOrg; Multiple Analytical Tools` | `Multiple Analytical Tools` | -- | -- | -- | **PUB_PROPERTY** | generic-but-real; software_mentioned_raw |
| `homemade Python scripts Jupyter Notebooks` | `homemade Python scripts Jupyter Notebook` | -- | -- | -- | **PUB_PROPERTY** | generic-but-real; software_mentioned_raw |
| `in-house software` | `in-house software` | -- | -- | -- | **PUB_PROPERTY** | generic-but-real; software_mentioned_raw |
| `AI and elemental ratios of molecular formulas (H/C and O/C)` | `AI` | -- | -- | -- | **REJECT** | AI and elemental ratios... |
| `AI and elemental ratios of molecular formulas (H/C and O/C)` | `elemental ratios of molecular formulas (` | -- | -- | -- | **REJECT** | AI and elemental ratios... |
| `N/A` | `N/A` | -- | -- | -- | **REJECT** | N/A |
| `NMR and high-resolution MS analyses; PetroOrg N-15.0` | `NMR` | -- | -- | -- | **REJECT** | method-description phrase |
| `NMR and high-resolution MS analyses; PetroOrg N-15.0` | `high-resolution MS analyses` | -- | -- | -- | **REJECT** | method-description phrase |
| `Peak lists (uncalibrated, global calibration, mass differenc` | `Peak lists (uncalibrated, global calibra` | -- | -- | -- | **REJECT** | Peak lists (uncalibrated...) |
| `fouriertransform` | `fouriertransform` | -- | -- | -- | **REJECT** | bare fouriertransform |
| `known databases 35, 36` | `known databases 35` | -- | -- | -- | **REJECT** | known databases 35, 36 |
| `known databases 35, 36` | `36` | -- | -- | -- | **REJECT** | known databases 35, 36 |
| `'MixSIAR' package in R 4.2.0 software` | `'MixSIAR' package in R 4.2.0 software` | -- | -- | `4.2.0` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `ArcGIS 10.2; MATLAB R2015b; R i386 2.15.2` | `MATLAB R2015b` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `ArcGIS 10.2; MATLAB R2015b; R i386 2.15.2` | `R i386 2.15.2` | -- | -- | `2.15.2` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `BioTools, cRAWler algorithm inside ProSightPC 3.0; ProteinPr` | `MaximumEntropyDeconvolution from DataAna` | -- | `Bruker` | `3.4` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `BioTools, cRAWler algorithm inside ProSightPC 3.0; ProteinPr` | `ProSight PC workflow` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `BioTools, cRAWler algorithm inside ProSightPC 3.0; ProteinPr` | `Xtract algorithm from Thermo Fisher Scie` | -- | `Thermo` | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `BiodieselAnalyzer Version 2.2` | `BiodieselAnalyzer Version 2.2` | -- | -- | `2.2` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `CDS 3.02A software made by AVIV Biomedical, Inc.; Felix 3.2;` | `CDS 3.02A software made by AVIV Biomedic` | -- | -- | `3.02` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `CDS 3.02A software made by AVIV Biomedical, Inc.; Felix 3.2;` | `Inc.` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `CDS 3.02A software made by AVIV Biomedical, Inc.; Felix 3.2;` | `Felix 3.2` | -- | -- | `3.2` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `CDS 3.02A software made by AVIV Biomedical, Inc.; Felix 3.2;` | `IGOR Pro` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `CaGe program; Schlegel diagrams` | `CaGe program` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `CaGe program; Schlegel diagrams` | `Schlegel diagrams` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Centrifuge` | `Centrifuge` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `ChromaTOF HRT software (v5.10)` | `ChromaTOF HRT software (v5.10)` | -- | -- | `5.10` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `ChromaTOF software (version 4.50)` | `ChromaTOF software (version 4.50)` | -- | -- | `4.50` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Composer64 or PetroOrg; R version 4.0.3; ggplot2, a componen` | `a component of the tidyverse package` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Comprehensive Localization of Internal Protein Sequences (Cl` | `Xcalibur Qual Browser-embedded 'Xtract' ` | -- | `Thermo` | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Custom software; ProSight Lite; 24 IsoPro 3.1; SciDAVis` | `IsoPro 3.1` | -- | -- | `3.1` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Custom software; ProSight Lite; 24 IsoPro 3.1; SciDAVis` | `SciDAVis` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `DataAnalysis software (Bruker); 'Transhumus' software` | `'Transhumus' software` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `EnviroOrg Software E 2.0` | `EnviroOrg Software E 2.0` | -- | -- | `2.0` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `EnviroOrg; CO2Calc program; fouriertransform Python package` | `CO2Calc program` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `EnviroOrg; CO2Calc program; fouriertransform Python package` | `fouriertransform Python package` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `EnviroOrg; DADA2 pipeline; R software v.3.6.2; Tri-carb 2800` | `DADA2 pipeline` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `EnviroOrg; Prism 6 by GraphPad; Fourier transform Python pac` | `Prism 6 by GraphPad` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `EnviroOrg; Prism 6 by GraphPad; Fourier transform Python pac` | `Fourier transform Python package (Heming` | -- | -- | `2017` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `FT-ICR MS; ChromCALC; PetroOrg` | `FT-ICR MS` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Fityk; Athena; PetroOrg ©; R package 'vegan'` | `Fityk` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Fityk; Athena; PetroOrg ©; R package 'vegan'` | `R package 'vegan'` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Freestyle (Thermo Scienti fi c)` | `Freestyle (Thermo Scienti fi c)` | -- | `Thermo` | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Geographic Resources Analysis Support System (GRASS v7.2)` | `Geographic Resources Analysis Support Sy` | -- | -- | `7.2` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Inkscape v0.91` | `Inkscape v0.91` | -- | -- | `0.91` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Isopro 3.1` | `Isopro 3.1` | -- | -- | `3.1` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `JED-2300 Series Standard software; one-way analysis of varia` | `Tukey 's Honest Significant Difference p` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `MATLAB (R2014A); Microsoft Excel 2016; MATLAB` | `MATLAB (R2014A)` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `MATLAB R2016a` | `MATLAB R2016a` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `MATLAB R2019a using DOMFluor toolbox; a browser-based softwa` | `MATLAB R2019a using DOMFluor toolbox` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `MATLAB R2019a using DOMFluor toolbox; a browser-based softwa` | `a browser-based software (Leefmann et al` | -- | -- | `2019` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `MATLAB R2020b` | `MATLAB R2020b` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `MATLAB ™ v6.9; R.3.5.0` | `R.3.5.0` | -- | -- | `3.5.0` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `MATLAB; DrEEM toolbox; JMP Pro 12 (SAS Institute)` | `JMP Pro 12 (SAS Institute)` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `MATLAB; Primer v.6.2; Primer 6 (version 6.1.13)` | `Primer v.6.2` | -- | -- | `6.2` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `MATLAB; Primer v.6.2; Primer 6 (version 6.1.13)` | `Primer 6 (version 6.1.13)` | -- | -- | `6.1.13` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `MIDAS Predator Analysis and Molecular Formula Calculator; FL` | `FL Toolbox 1.91 in MATLAB` | -- | -- | `1.91` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `MassLynx 4.1; PetroOrg with a nonlinear iterative partial le` | `MassLynx 4.1` | -- | -- | `4.1` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `MassLynx 4.1; PetroOrg with a nonlinear iterative partial le` | `PetroOrg with a nonlinear iterative part` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `MatLab (R2023a); Peak-by-Peak (Base Edition, Version 2023.5.` | `MatLab (R2023a)` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `MatLab (R2023a); Peak-by-Peak (Base Edition, Version 2023.5.` | `Peak-by-Peak (Base Edition, Version 2023` | -- | -- | `2023.5.0` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Matlab, drEEM toolbox (Murphy et al., 2013)` | `drEEM toolbox (Murphy et al., 2013)` | -- | -- | `2013` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Methods of Soil Analysis. Part 3 - Chemical Methods` | `Methods of Soil Analysis. Part 3 - Chemi` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Modgraph implemented in MestReNova 10.0.1 (Mestrelab Researc` | `Modgraph implemented in MestReNova 10.0.` | -- | -- | `10.0.1` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Modgraph implemented in MestReNova 10.0.1 (Mestrelab Researc` | `COLMAR database` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Modgraph implemented in MestReNova 10.0.1 (Mestrelab Researc` | `NMRPipe` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Molecular Evolutionary Genetics Analysis version 11 (MEGA11)` | `Molecular Evolutionary Genetics Analysis` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Molecular Evolutionary Genetics Analysis version 11 (MEGA11)` | `vsearch 2.21.1` | -- | -- | `2.21.1` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `MØD platform; Gephi` | `MØD platform` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `MØD platform; Gephi` | `Gephi` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Nanoscope ver. 8.15` | `Nanoscope ver. 8.15` | -- | -- | `8.15` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `National High Magnetic Field Laboratory software; PROC GLM o` | `National High Magnetic Field Laboratory ` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `National High Magnetic Field Laboratory software; PROC GLM o` | `PROC GLM of SAS 9.4` | -- | -- | `9.4` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `NovaWin; PetroOrg` | `NovaWin` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Peak-by-Peak software (Spectroswiss, Lausanne, Switzerland);` | `Peak-by-Peak software (Spectroswiss, Lau` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Peak-by-Peak software (Spectroswiss, Lausanne, Switzerland);` | `SciPy package` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `PetroOrg ; XLStat` | `XLStat` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `PetroOrg TM; R Statistical Software v.4.1.3; 'rstatix' v.0.7` | `R Statistical Software v.4.1.3` | -- | -- | `4.1.3` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `PetroOrg TM; R Statistical Software v.4.1.3; 'rstatix' v.0.7` | `'rstatix' v.0.7.0 (Kassambara, 2021)` | -- | -- | `0.7.0` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `PetroOrg TM; R Statistical Software v.4.1.3; 'rstatix' v.0.7` | `'Hmisc' v.4.6.0 (Harrell, 2021)` | -- | -- | `4.6.0` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `PetroOrg TM; R Statistical Software v.4.1.3; 'rstatix' v.0.7` | `'tidyverse' (Wickham et al., 2019) v.1.3` | -- | -- | `2019` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `PetroOrg TM; R Statistical Software v.4.1.3; 'rstatix' v.0.7` | `'ggfortify' v. 0.4.14 (Horikoshi & Tang,` | -- | -- | `0.4.14` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `PetroOrg software 67` | `PetroOrg software 67` | -- | -- | -- | **REVIEW** | trailing-ref gap UNBUILT (Sec 9.5) -- needs ruling |
| `PetroOrg, Kendrick mass defect analysis with PetroOrg` | `Kendrick mass defect analysis with Petro` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `PetroOrg; EnviroOrg (NHMFL software by Yuri Corilo); NHMFL s` | `EnviroOrg (NHMFL software by Yuri Corilo` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `PetroOrg; EnviroOrg (NHMFL software by Yuri Corilo); NHMFL s` | `NHMFL software` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `PetroOrg; R (Version 1.1.463); FactoMine R package; Ecodist ` | `FactoMine R package` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `PetroOrg; R (Version 1.1.463); FactoMine R package; Ecodist ` | `Ecodist R package` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `PetroOrg; R Core Team using the factoextra package (Kassamba` | `R Core Team using the factoextra package` | -- | -- | `2017` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `PetroOrg; R; ggplot2; Vegan R package` | `Vegan R package` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `PetroOrg; RStudio; Microsoft Excel; ggplot2` | `RStudio` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `PetroOrg; k-Means clustering analysis; RStudio version 2023.` | `RStudio version 2023.12.1 + 402` | -- | -- | `2023.12.1` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `PetroOrg; k-Means clustering analysis; RStudio version 2023.` | `'factoextra' package` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `PetroOrg©,™ (Corilo, 2015)` | `™ (Corilo, 2015)` | -- | -- | `2015` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Predator Acquisition data station; Predator, PetroOrg, PyC2M` | `Predator Acquisition data station` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Predator Software Corev1.2.3` | `Predator Software Corev1.2.3` | -- | -- | `1.2.3` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Predator analysis 37 and PetroOrg 38` | `Predator analysis 37` | -- | -- | -- | **REVIEW** | trailing-ref gap UNBUILT (Sec 9.5) -- needs ruling |
| `Predator analysis 37 and PetroOrg 38` | `PetroOrg 38` | -- | -- | -- | **REVIEW** | trailing-ref gap UNBUILT (Sec 9.5) -- needs ruling |
| `Predator data station, Xian et al.; PetroOrg; Athena; R stat` | `Xian et al.` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Predator data station, Xian et al.; PetroOrg; Athena; R stat` | `R statistical software (v. 4.0.4)` | -- | -- | `4.0.4` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Predator data station; PetroOrg, in-house developed MATLAB s` | `in-house developed MATLAB scripts (R2018` | -- | -- | `9.4.0.813654` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Predator; PC-Ord software (version 4, MjM Software Design)` | `PC-Ord software (version 4, MjM Software` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Predator; PetroOrg; QIIME2 pipeline (QIIME2-2019.10), scikit` | `QIIME2 pipeline (QIIME2-2019.10)` | -- | -- | `2019.10` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Predator; PetroOrg; QIIME2 pipeline (QIIME2-2019.10), scikit` | `scikitlearn` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Predator; PetroOrg; QIIME2 pipeline (QIIME2-2019.10), scikit` | `checkM v1.1.2` | -- | -- | `1.1.2` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Predator; PetroOrg; QIIME2 pipeline (QIIME2-2019.10), scikit` | `GTDBTk v1.3.0` | -- | -- | `1.3.0` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Predator; PetroOrg; QIIME2 pipeline (QIIME2-2019.10), scikit` | `dRep v3.0.0` | -- | -- | `3.0.0` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Predator; PetroOrg; QIIME2 pipeline (QIIME2-2019.10), scikit` | `coverM genome v0.6.0` | -- | -- | `0.6.0` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Predator; Ribosomal Database Project (RDP), Silva database` | `Ribosomal Database Project (RDP)` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Predator; Ribosomal Database Project (RDP), Silva database` | `Silva database` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Predator; THRASH algorithm; ProSight Lite (v1.4, build 1.4.6` | `ProSight Lite (v1.4, build 1.4.6)` | -- | -- | `1.4` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `ProSight Lite 39` | `ProSight Lite 39` | -- | -- | -- | **REVIEW** | trailing-ref gap UNBUILT (Sec 9.5) -- needs ruling |
| `ProSight Lite, Xtract; Xtract parameters` | `Xtract parameters` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `ProSight PD ™ (Thermo Fisher Scientific PD version 2.1, ProS` | `ProSight PD ™ (Thermo Fisher Scientific ` | -- | `Thermo` | `2.1` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `ProSight PD ™ (Thermo Fisher Scientific PD version 2.1, ProS` | `Xcalibur ™ Qual Browser software (Thermo` | -- | `Thermo` | `4.0` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `ProSight PTM 2.0` | `ProSight PTM 2.0` | -- | -- | `2.0` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `QIIME v1.8` | `QIIME v1.8` | -- | -- | `1.8` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Qubit protein assay kit; Xcalibur` | `Qubit protein assay kit` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `R, phyloseq library` | `phyloseq library` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `R-studio 0.97.551 (R i386 2.15.2); MATLAB R2016b` | `R-studio 0.97.551 (R i386 2.15.2)` | -- | -- | `0.97.551` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `R-studio 0.97.551 (R i386 2.15.2); MATLAB R2016b` | `MATLAB R2016b` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `R; Vegan; FactoMineR; MASS; indicspecies; Vegan package in R` | `FactoMineR` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `R; Vegan; FactoMineR; MASS; indicspecies; Vegan package in R` | `MASS` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `R; Vegan; FactoMineR; MASS; indicspecies; Vegan package in R` | `indicspecies` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `R; Vegan; FactoMineR; MASS; indicspecies; Vegan package in R` | `Vegan package in R` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `R; rstatix` | `rstatix` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `RStudio utilizing R software (V4.1.2)` | `RStudio utilizing R software (V4.1.2)` | -- | -- | `4.1.2` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Recoil; nf-core/ampliseq v1.1.2, Nextflow v20.10; Cutadapt v` | `Recoil` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Recoil; nf-core/ampliseq v1.1.2, Nextflow v20.10; Cutadapt v` | `nf-core/ampliseq v1.1.2` | -- | -- | `1.1.2` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Recoil; nf-core/ampliseq v1.1.2, Nextflow v20.10; Cutadapt v` | `Nextflow v20.10` | -- | -- | `20.10` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Recoil; nf-core/ampliseq v1.1.2, Nextflow v20.10; Cutadapt v` | `PICRUSt2 version 2.2.0-b` | -- | -- | `2.2.0-b` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Recoil; nf-core/ampliseq v1.1.2, Nextflow v20.10; Cutadapt v` | `MinPath` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Scikit's KNeighborsClassifier; SCANPY; MATLAB 2020b; microMS` | `Scikit's KNeighborsClassifier` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Scikit's KNeighborsClassifier; SCANPY; MATLAB 2020b; microMS` | `SCANPY` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Scikit's KNeighborsClassifier; SCANPY; MATLAB 2020b; microMS` | `MATLAB 2020b` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Scikit's KNeighborsClassifier; SCANPY; MATLAB 2020b; microMS` | `microMS` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `StepOne from Applied Biosystems and PowerUp SYBR Green Maste` | `PowerUp SYBR Green Master Mix` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Thermo Xcalibur software (version 3.0.63) and a custom-built` | `a custom-built script using ZeroBrane St` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Toolbox for Environmental Research (TEnvR) in MATLAB 2022a` | `Toolbox for Environmental Research (TEnv` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Transhumus software based on the open-source R environment` | `Transhumus software based on the open-so` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `UltraScan III software version 3.3; ProteoWizard MSConvert; ` | `UltraScan III software version 3.3` | -- | -- | `3.3` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `UltraScan III software version 3.3; ProteoWizard MSConvert; ` | `StavroX` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `UltraScan III software version 3.3; ProteoWizard MSConvert; ` | `MaxQuant software at standard settings` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Xcalibur 3.0, Xtract; ProSight Lite 30; ProSight Lite` | `ProSight Lite 30` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Xcalibur Qual Browser; ProSight Lite; TDValidator` | `Xcalibur Qual Browser` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Xcalibur QualBrowser; ProSight Lite 1.4; ProSight PD 4.0; TD` | `Xcalibur QualBrowser` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Xcalibur QualBrowser; ProSight Lite 1.4; ProSight PD 4.0; TD` | `GDC Data Transfer Tool Client v1.6.1` | -- | -- | `1.6.1` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Xcalibur QualBrowser; ProSight Lite 1.4; ProSight PD 4.0; TD` | `Mascot search engine (Matrix Science; ve` | -- | -- | `2.8.0` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Xcalibur; TDPortal 22; Thermo Protein Deconvolution 4.0; Pro` | `TDPortal 22` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Xcalibur; TDPortal 22; Thermo Protein Deconvolution 4.0; Pro` | `Thermo Protein Deconvolution 4.0` | -- | `Thermo` | `4.0` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Xcalibur; TDPortal 22; Thermo Protein Deconvolution 4.0; Pro` | `MetaMorpheus 26` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Xtract algorithm; ReSpect™ algorithm; Mascot; SDS-PAGE; Pro-` | `Pro-Q Diamond phosphoprotein gel stain` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Xtract algorithm; ReSpect™ algorithm; Mascot; SDS-PAGE; Pro-` | `SYPRO Ruby fluorescent protein stain` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Xtract algorithm; ReSpect™ algorithm; Mascot; SDS-PAGE; Pro-` | `ReSpect™ algorithm in BioPharma Finder` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Xtract, THRASH, ReSpect (found in both a commercial package ` | `ReSpect (found in both a commercial pack` | -- | `Thermo` | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Xtract, THRASH, ReSpect (found in both a commercial package ` | `Intact Mass (Protein Metrics)` | -- | `Protein Metrics` | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Xtract, THRASH, ReSpect (found in both a commercial package ` | `UniDec (Oxford University, UK)` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Young Algorithm, Internal Release June 2014; ANOVA tests, t-` | `ANOVA tests` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `custom code written in Igor 6.3.7 (Wavemetrics)` | `custom code written in Igor 6.3.7 (Wavem` | -- | -- | `6.3.7` | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `custom-built MIDAS software` | `custom-built MIDAS software` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `drEEM toolbox v. 5.0; QIIME2 (v.2019.1); q-score-joined; q2-` | `q-score-joined` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `drEEM toolbox v. 5.0; QIIME2 (v.2019.1); q-score-joined; q2-` | `q2-deblur` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `drEEM toolbox v. 5.0; QIIME2 (v.2019.1); q-score-joined; q2-` | `MAFFT` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `drEEM toolbox v. 5.0; QIIME2 (v.2019.1); q-score-joined; q2-` | `FasTtree2` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `drEEM toolbox v. 5.0; QIIME2 (v.2019.1); q-score-joined; q2-` | `q2-feature-classify-sklearn plugin` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `drEEM toolbox; MatLab code` | `MatLab code` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `eosLink-FD; Cutadapt v2.6; QIIME2 version 2019.10.0; DADA2 v` | `eosLink-FD` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `eosLink-FD; Cutadapt v2.6; QIIME2 version 2019.10.0; DADA2 v` | `QIIME2 diversity alpha-rarefaction plugi` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `factoextra package in R` | `factoextra package in R` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `in-house software (EnviroOrg); ArcMap 10` | `ArcMap 10` | -- | -- | -- | **REVIEW** | trailing-ref gap UNBUILT (Sec 9.5) -- needs ruling |
| `modular ICR data station` | `modular ICR data station` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `modular ion cyclotron resonance data acquisition system, Pet` | `modular ion cyclotron resonance data acq` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `parameters were set in Xtract` | `parameters were set in Xtract` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `self-written MatLab algorithms and routines combined in a gr` | `self-written MatLab algorithms` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `self-written MatLab algorithms and routines combined in a gr` | `routines combined in a graphical user in` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `stored waveform inverse Fourier transform (SWIFT)` | `stored waveform inverse Fourier transfor` | -- | -- | -- | **REVIEW** | not confidently MINT/REJECT (Sec 2.1 bias-to-REVIEW) |
| `Atomic Force Microscopy Molecular Imaging` | `Atomic Force Microscopy Molecular Imagin` | -- | -- | -- | **ROUTE_OUT** | method misroute -> method_field_handoff.md |
| `BioTools, cRAWler algorithm inside ProSightPC 3.0; ProteinPr` | `cRAWler algorithm inside ProSightPC 3.0` | -- | -- | `3.0` | **ROUTE_OUT** | algorithm -> method_field_handoff.md |
| `EnviroOrg; DADA2 pipeline; R software v.3.6.2; Tri-carb 2800` | `Tri-carb 2800TR scintillation counter` | -- | -- | -- | **ROUTE_OUT** | instrument -> method_field_handoff.md (belongs to: instrument field (KI-3: no node on disk)) |
| `GPC analysis with polystyrene standards for calibration` | `GPC analysis with polystyrene standards ` | -- | -- | -- | **ROUTE_OUT** | method misroute -> method_field_handoff.md |
| `Gas chromatography/mass spectrometry; Predator; Custom softw` | `Gas chromatography/mass spectrometry` | -- | -- | -- | **ROUTE_OUT** | method misroute -> method_field_handoff.md |
| `JED-2300 Series Standard software; one-way analysis of varia` | `JED-2300 Series Standard software` | -- | -- | -- | **ROUTE_OUT** | instrument -> method_field_handoff.md (belongs to: instrument field (KI-3: no node on disk)) |
| `JED-2300 Series Standard software; one-way analysis of varia` | `one-way analysis of variance` | -- | -- | -- | **ROUTE_OUT** | algorithm -> method_field_handoff.md |
| `Kendrick mass defect analysis` | `Kendrick mass defect analysis` | -- | -- | -- | **ROUTE_OUT** | method misroute -> method_field_handoff.md |
| `MIDAS Predator Analysis and Molecular Formula Calculator; FL` | `Molecular Formula Calculator` | -- | -- | -- | **ROUTE_OUT** | algorithm -> method_field_handoff.md |
| `PetroOrg; NanoDrop 2000c spectrophotometer; GraphPad Prism v` | `NanoDrop 2000c spectrophotometer` | -- | -- | -- | **ROUTE_OUT** | instrument -> method_field_handoff.md (belongs to: instrument field) |
| `PetroOrg; k-Means clustering analysis; RStudio version 2023.` | `k-Means clustering analysis` | -- | -- | -- | **ROUTE_OUT** | algorithm -> method_field_handoff.md |
| `Predator; THRASH algorithm; ProSight Lite (v1.4, build 1.4.6` | `THRASH algorithm` | -- | -- | -- | **ROUTE_OUT** | algorithm -> method_field_handoff.md |
| `ProSight Lite, Xtract; Xtract parameters` | `Xtract` | -- | -- | -- | **ROUTE_OUT** | algorithm -> method_field_handoff.md |
| `ProSight PD ™ (Thermo Fisher Scientific PD version 2.1, ProS` | `XTract algorithm (Thermo Fisher Scientif` | -- | `Thermo` | -- | **ROUTE_OUT** | algorithm -> method_field_handoff.md |
| `StepOne from Applied Biosystems and PowerUp SYBR Green Maste` | `StepOne from Applied Biosystems` | -- | -- | -- | **ROUTE_OUT** | instrument -> method_field_handoff.md (belongs to: instrument field (KI-3: no node on disk)) |
| `Xcalibur 3.0, Xtract; ProSight Lite 30; ProSight Lite` | `Xtract` | -- | -- | -- | **ROUTE_OUT** | algorithm -> method_field_handoff.md |
| `Xtract algorithm; ReSpect™ algorithm; Mascot; SDS-PAGE; Pro-` | `Xtract algorithm` | -- | -- | -- | **ROUTE_OUT** | algorithm -> method_field_handoff.md |
| `Xtract algorithm; ReSpect™ algorithm; Mascot; SDS-PAGE; Pro-` | `ReSpect™ algorithm` | -- | -- | -- | **ROUTE_OUT** | algorithm -> method_field_handoff.md |
| `Xtract algorithm; ReSpect™ algorithm; Mascot; SDS-PAGE; Pro-` | `SDS-PAGE` | -- | -- | -- | **ROUTE_OUT** | method misroute -> method_field_handoff.md |
| `Xtract, THRASH, ReSpect (found in both a commercial package ` | `Xtract` | -- | -- | -- | **ROUTE_OUT** | algorithm -> method_field_handoff.md |
| `Xtract, THRASH, ReSpect (found in both a commercial package ` | `THRASH` | -- | -- | -- | **ROUTE_OUT** | algorithm -> method_field_handoff.md |
| `Xtract, THRASH, ReSpect (found in both a commercial package ` | `SNAP` | -- | -- | -- | **ROUTE_OUT** | algorithm -> method_field_handoff.md |
| `Xtract, THRASH, ReSpect (found in both a commercial package ` | `MaxEnt (Bruker Daltonics)` | -- | `Bruker` | -- | **ROUTE_OUT** | algorithm -> method_field_handoff.md |
| `Young Algorithm, Internal Release June 2014; ANOVA tests, t-` | `Young Algorithm` | -- | -- | -- | **ROUTE_OUT** | algorithm -> method_field_handoff.md |
| `Young Algorithm, Internal Release June 2014; ANOVA tests, t-` | `Internal Release June 2014` | -- | -- | `2014` | **ROUTE_OUT** | method misroute -> method_field_handoff.md |
| `Young Algorithm, Internal Release June 2014; ANOVA tests, t-` | `t-tests` | -- | -- | -- | **ROUTE_OUT** | algorithm -> method_field_handoff.md |
| `high-throughput 16S rRNA gene sequencing` | `high-throughput 16S rRNA gene sequencing` | -- | -- | -- | **ROUTE_OUT** | method misroute -> method_field_handoff.md |
| `xTract` | `xTract` | -- | -- | -- | **ROUTE_OUT** | algorithm -> method_field_handoff.md |
