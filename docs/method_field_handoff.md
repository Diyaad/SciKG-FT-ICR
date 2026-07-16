# Method / ionization field — handoff from the instrument-field build (2026-07-15)

Strings the INSTRUMENT transform pulled out because they belong to the method/ionization
build, not Instrument nodes. That build should read this file as an input instead of
rediscovering them. Source: data/raw/pdf_extraction/*.jsonl, consolidated instrument field.
No entity data here — a routing handoff only.

## MISROUTES — method/acquisition strings (flagged by: instrument field)
| String (verbatim) | source DOI(s) | belongs to |
|---|---|---|
| CFX Connect ™ Real-Time PCR Detection System | 10.1029/2018JG004712 | method/ionization field |
| LC-ICP-MS method | 10.1038/s43247-024-01965-9 | method/ionization field |
| high-resolution mass spectrometry detection | 10.1021/acs.energyfuels.1c01837 | method/ionization field |

## SETTINGS — rejected from Instrument; may belong to Method properties (that build to rule)
These are acquisition SETTINGS, not instruments. Rejected as Instrument nodes; listed here
because they may become Method/acquisition-parameter properties.
| String (verbatim) | source DOI(s) |
|---|---|
| 300 -4000 m/z scan range | 10.1007/s13361-019-02290-8 |
| instrument settings: 120,000 resolving power at m/z 400 | 10.1007/s13361-019-02290-8 |

## Note
The instrument build also rejected software/model strings (PC-SAFT, CPA, CEOS) that may
belong to the SOFTWARE field — see instrument_review.md AUTO-REJECTED (software) section.

---

# Handoff from the software-field build (2026-07-15)

Strings the SOFTWARE transform's rulings routed OUT of `software_tools` because they are not
Software nodes. RULED, NOT IMPLEMENTED — the software transform is not built; this records the
routing decisions for the method/ionization build to consume. Source: `data/raw/pdf_extraction/*.jsonl`,
consolidated `software_tools` field; DOIs traced to disk. No entity data here.

## ALGORITHMS — not Software nodes (flagged by: software_tools field)
Deconvolution / signal-processing / statistical algorithms. They belong to Method (or an
acquisition-parameter property), not a Software node.
| String (verbatim) | source DOI(s) |
|---|---|
| Xtract / xTract | 10.1002/pmic.201300438; 10.1007/s13361-019-02290-8; 10.1016/j.ijms.2017.11.012; 10.1016/j.mcpro.2024.100814; 10.1021/acs.analchem.0c01064; 10.1021/acs.analchem.8b03294; 10.1021/jasms.0c00036; 10.1021/jasms.1c00291; 10.1101/455527 |
| THRASH | 10.1021/acs.analchem.9b04954; 10.1021/jasms.0c00036 |
| ReSpect | 10.1021/jasms.0c00036; 10.1101/455527 |
| SWIFT (stored waveform inverse Fourier transform) | 10.1002/mas.21666 |
| SNAP | 10.1021/jasms.0c00036 |
| MaxEnt / MaximumEntropyDeconvolution | 10.1002/pmic.201300438; 10.1021/jasms.0c00036 |
| cRAWler | 10.1002/pmic.201300438 |
| NIPALS (nonlinear iterative partial least-squares) | 10.1021/acs.est.7b04445 |
| k-Means clustering | 10.1021/acs.energyfuels.4c02605 |
| Molecular Formula Calculator | 10.1016/j.gca.2016.05.015 |
| Young Algorithm | 10.1074/mcp.M114.046441 |

**Explicitly NOT an algorithm:** `Internal Release June 2014` (10.1074/mcp.M114.046441) — a
build label (B9), handled as an edge `version` when attached to a named tool, rejected when
bare. Do not add it to this inbox.

## METHOD MISROUTES (flagged by: software_tools field)
| String (verbatim) | source DOI(s) | belongs to |
|---|---|---|
| SDS-PAGE | 10.1101/455527 | method field |
| high-throughput 16S rRNA gene sequencing | 10.1007/s11783-022-1567-y | method field |
| Kendrick mass defect analysis | 10.1002/lno.11857; 10.1021/ef1001502 | method field |
| GPC analysis (with polystyrene standards) | 10.1021/acs.energyfuels.1c01837 | method field |
| Atomic Force Microscopy imaging | 10.1021/acs.energyfuels.1c02107 | method field |
| Gas chromatography/mass spectrometry | 10.1021/acs.energyfuels.7b01803 | method field |
| ANOVA / Tukey / t-tests | 10.1021/acsomega.0c00566; 10.1074/mcp.M114.046441 | method field |

## Gaps surfaced by this field — see `docs/KNOWN_ISSUES.md`
Two gaps this field exposed are NOT re-described here: (a) reagents with no node type
(Qubit, SYPRO Ruby, Pro-Q Diamond, PowerUp SYBR Green); (b) three instrument strings absent
from the completed instrument field (Tri-carb 2800TR, StepOne, JED-2300). Both are filed in
`docs/KNOWN_ISSUES.md`, marked "needs a ruling — do not fix."
