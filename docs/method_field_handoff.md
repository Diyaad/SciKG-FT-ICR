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
