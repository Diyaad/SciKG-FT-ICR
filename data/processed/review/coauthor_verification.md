# Co-author edge verification vs Crossref (READ-ONLY)

_Verified the 79 `coauthor_edge_fix_ledger.jsonl` rows against Crossref by DOI (mailto=davidsbutcher@protonmail.com). No graph writes; no ledger row dropped._

## Counts

- **CONFIRMED** (Crossref lists the author): 6
- **MISSING** (Crossref has paper, not the author — FLAG): 0
- **NO-RECORD** (Crossref returned nothing for the DOI — check by hand): 0
- **NoDOI** (no DOI in graph or CSV — not Crossref-checkable; keeps CSV-string evidence): 73

_Of 79 rows, 6 independently confirmed via Crossref; 0 flagged for a human; 73 not DOI-checkable (older no-DOI papers — evidence stays the raw MagLab CSV author string that already grounds the ledger). **No row was auto-dropped.**_

## All 79 rows

| DOI / paper | second author | matched | tag | evidence |
|---|---|:--:|---|---|
| 10.5670/oceanog.2016.77 | Reddy, C.M. | Y | CONFIRMED | Crossref author: 'Christopher Reddy' |
| 10.1016/j.chroma.2016.10.005 | Stenson, A.C. | Y | CONFIRMED | Crossref author: 'Alexandra C. Stenson' |
| 10.1021/acs.est.6b05126 | Rosario-Ortiz, F.L. | Y | CONFIRMED | Crossref author: 'Fernando L. Rosario-Ortiz' |
| 10.1021/acs.analchem.7b01461 | Håkansson, K. | Y | CONFIRMED | Crossref author: 'Kristina Håkansson' |
| 10.1016/j.bmcl.2017.04.070 | Krajewski, L. | Y | CONFIRMED | Crossref author: 'Logan Krajewski' |
| 10.1007/s13361-014-0871-6 | Hendrickson, C.L. | Y | CONFIRMED | Crossref author: 'Christopher L. Hendrickson' |
| pub:maglab:3297 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:4556 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:5674 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:5672 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:3298 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:4560 | Hatcher, P.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:6580 | Cooper, W.T. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:3204 | Greig, M.J. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:6486 | Cooper, W.T. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:6070 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:1977 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:1768 | Nilsson, C.L. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:2918 | Nilsson, C.L. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:175 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:1849 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:254 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:4299 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:4543 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:4709 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:5164 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:5167 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:5178 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:5481 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:5483 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:6075 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:6214 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:4750 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:1439 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:6103 | Hsu, C.S. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:5492 | Cooper, W.T. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:7258 | Cooper, W.T. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:258 | Qian, K. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:5538 | van Stipdonk, M.J. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:1325 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:1496 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:2460 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:837 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:5491 | Cooper, H.J. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:1493 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:1985 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:9248 | Cooper, W.T. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:5814 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:257 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:3596 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:6211 | Yang, X.-L. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:2481 | Nilsson, C.L. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:4150 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:1495 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:9152 | Alabugin, I.V. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:5480 | Mullins, O.C. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:2367 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:5172 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:6721 | Guo, M. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:182 | Robinson, C.V. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:4153 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:8945 | Stroupe, M.E. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:3295 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:8775 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:1492 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:259 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:8935 | Williams, H.N. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:3541 | Paizs, B. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:2919 | Nilsson, C.L. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:3343 | Nilsson, C.L. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:4555 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:6733 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:514 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:2461 | Marshall, A.G. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:8547 | Kim, S. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:9251 | Stenson, A.C. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:6756 | Podgorski, D.C. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:8849 | Podgorski, D.C. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |
| pub:maglab:8936 | Echegoyen, L. | N | NoDOI | no DOI in graph or CSV — cannot Crossref-verify; evidence remains MagLab CSV author string |