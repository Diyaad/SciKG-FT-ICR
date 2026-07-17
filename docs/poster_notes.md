# Poster Notes — honest numbers and limitations

For whoever reads the poster. Same underlying facts as `docs/KNOWN_ISSUES.md`, framed for
a reader rather than a fixer: what the graph does and does not support, stated plainly, each
with its issue number and a pointer to the corresponding KI entry.

**Pointer status (measured this session):** `KNOWN_ISSUES.md` currently holds **KI-1 through
KI-9**. **KI-10 and KI-11 are NOT yet filed there** — they are recorded here from this
session's findings and still need a KI entry written. Where this file cites KI-10/KI-11, the
target ticket does not yet exist on disk.

---

## Limitations

### KI-7 — Instruments are mostly uncanonicalized, because the corpus is broader than mass spec
*(→ KNOWN_ISSUES.md KI-7)*

The controlled vocabulary for instruments holds **34 aliases**. There are **469** distinct
Instrument nodes; **462 of them are uncanonicalized** (no `canonical_name` — 7 canonicalized).
This is **not an extraction failure**: the vocabulary was built for mass spectrometry, and the
papers name instruments far outside that — TOC analyzers, spectrofluorometers, ion
chromatography, sequencers (Illumina MiSeq), accelerator MS, elemental analyzers, UV-Vis,
NMR. The uncanonicalized instruments are real nodes; they simply have no vocabulary term to
map to. Every unmapped term is logged to the review queue — nothing is hidden or dropped.

### KI-5 — "144 papers with no software" means "no grounded value," not "reported none"
*(→ KNOWN_ISSUES.md KI-5)*

02d accepts a software value only if an aligned text span covers enough of it. When the LLM
correctly returns a value naming **several** tools, the aligned span is usually just the first
tool name, so span coverage collapses and the whole value is dropped. **Up to 51 of the 144
papers counted as "no software" actually had software we lost this way.** The honest phrasing
is **"144 papers with no grounded software value,"** not "144 papers that reported none." The
headline count is wrong in the direction that inflates negatives.

### KI-11 — Review articles cannot be separated from research articles
*(pointer target NOT yet filed in KNOWN_ISSUES.md — recorded here this session)*

`resource_type` is **"JournalArticle" on all 805** publication records. Review articles are
therefore indistinguishable from research articles. Consequence: **"a tool named in a paper"
cannot be systematically separated from "a tool used in a paper"** — a review that surveys a
method is recorded the same as a study that ran it. **Two confirmed instances** of this
name-vs-use conflation are known; **both were found by a human reading the paper**, not by any
systematic check.

### KI-10 — Fuzzy-matched extractions enter with no coverage check at all
*(pointer target NOT yet filed in KNOWN_ISSUES.md — recorded here this session)*

`MATCH_FUZZY` extractions bypass the span-coverage guard entirely. **1,057 such extractions
enter across all fields**, including **274 instrument** and **23 facility**. **One confirmed
fabrication** has been found this way — **MaxQuant on `10.1021/jasms.4c00232`**, caught by a
human reading the PDF. This is **exposure, not confirmed error**: the 1,057 are not known to
be wrong, but they entered without the check the rest of the pipeline applies, and the exposure
**cannot be audited without 297 PDF reads.**

---

## What the provenance discipline bought

The graph withholds registry identifiers until a human confirms them, and every node and edge
carries its source. Two concrete payoffs:

### Two wrong registry identifiers caught before minting

Both were **correct records for real tools** — the registry match was not a database error.
Only the **paper's actual usage** revealed that the matched tool was the wrong one:

- **predatoR** — a network-based mutation-impact prediction tool — name-matched our FT-ICR
  **data station**.
- **ATHENA** — the AI4SCR spatial-omics tool — name-matched our **XAS/XANES** program.

A name-only match would have minted either as fact. Requiring human confirmation against the
paper's usage stopped both.

### Provenance on everything; registry IDs null until confirmed

- **Every node and every edge carries the six provenance properties** — `source_type`,
  `confidence`, `extracted_at`, `evidence_note`, `source_id`, `schema_version`.
- **Registry IDs stay null until a human confirms them.** The `proposed` status exists
  precisely so that an unconfirmed exact-name registry hit **cannot reach the graph as fact**:
  `biotools_status: proposed` marks the hit, and `biotools_id` remains null until review
  returns.

---

*Sources: `docs/KNOWN_ISSUES.md` (KI-5, KI-7), `docs/SCIKG_SCHEMA.md` (instrument counts,
provenance properties, `proposed`/registry-ID rules), and this session's measurements. KI-10
and KI-11 are recorded from this session and still need KI entries filed. No number in this
file is invented; each is quoted from those sources.*
