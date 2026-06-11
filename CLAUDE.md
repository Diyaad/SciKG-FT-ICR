# CLAUDE.md — Guidance for AI Coding Assistants

This file orients AI assistants (Claude Code and others) working in the SciKG
repository. Read it before making changes.

## What this project is

SciKG (Scientific Knowledge Graph for FAIR Scientific Data Discovery) is a
long-term research platform to improve the discoverability, accessibility,
interoperability, and reusability (FAIR) of scientific research assets via
structured metadata, knowledge graphs, and AI-assisted retrieval.

See `README.md` for the full vision and `docs/` for the research foundation.

## Current stage: Research foundation

The repository is **documentation-first**. We are designing the architecture and
understanding the metadata ecosystem before writing pipeline code. (The project
does not use an approved, numbered phase plan — see `docs/ROADMAP.md`, which is a
*proposed, evolving* workflow only.)

### Hard constraints (do not violate without explicit user request)

- **Do NOT write scraping or ingestion scripts yet.**
- **Do NOT create or provision databases yet.**
- **Do NOT install dependencies.** `requirements.txt` is a *candidate* list for
  planning only.
- **Do NOT put real datasets in `data/raw/` yet**, and never edit `data/raw/`
  contents by hand once data exists — raw is immutable.

If a task seems to require any of the above, pause and confirm with the user
first; prefer extending the documentation/design instead.

## Data Integrity Policy (strict)

This project enforces a strict no-fabrication policy. When writing or editing any
documentation, template, or (future) data file:

- **No fabricated data.** No invented DOIs, publication titles, author names,
  instruments, datasets, or any other scientific record.
- **No inferred or placeholder metadata.** Do not guess, estimate, or fill in
  values that have not been directly observed from a real source.
- **No invented statistics.** Never invent metadata-completeness or
  field-population percentages. Only record measured values from a real source;
  otherwise leave them blank.
- **No synthetic scientific records.** Templates ship as header + guidance only,
  not with fake example rows.
- **Traceability.** Every scientific claim must be traceable to a source. Clearly
  distinguish verified facts from assumptions (see
  `docs/VERIFIED_FACTS_AND_ASSUMPTIONS.md`).

### Missing-value policy

- **Missing values must remain as they are in the source or schema.** Do not
  infer or fill them.
- If the schema *requires* a placeholder, use exactly one of: `N/A`, `null`, or
  blank.
- **Do not normalize all missing values into a single format** unless the schema
  explicitly requires it. Preserve whatever the source/schema already uses.
- Never convert a missing value into a fabricated value.

### Review-log rule

Whenever Claude Code modifies documentation, removes assumptions, encounters
uncertainty, finds possibly fabricated content, or makes a change that may need
review, it **must** update `docs/REVIEW_LOG.md` with a new row:

`| Date | File | Issue Found | Action Taken | Reason | Review Needed | Notes |`

When unsure whether something needs review, mark **Review Needed = Yes**.

## How to work here

- **Favor docs and design** over code in this phase. New ideas usually belong in
  `docs/`, not in `scripts/`.
- **Keep FAIR front-of-mind.** Before proposing a design, check it against
  `docs/FAIR_PRINCIPLES.md`. Every entity should be findable (has an identifier),
  accessible, interoperable (uses standard vocabularies where possible), and
  reusable (carries provenance).
- **Preserve provenance.** Any transformation must be traceable from output back
  to raw source. Design data flows as `raw → processed → outputs`, never the
  reverse.
- **Be extensible.** The entity model will grow (publications, datasets,
  instruments, grants, samples, methods, …). Prefer additive, schema-driven
  designs over hard-coded assumptions.
- **Match existing style.** When code does arrive, mirror the conventions of
  surrounding files.

## Repository conventions

- `data/raw/` — immutable source data. Read-only by convention.
- `data/processed/` — derived data; must be regenerable from `raw` + code.
- `scripts/` — pipeline/utility code (future).
- `notebooks/` — exploration; not a place for production logic.
- `outputs/` — generated artifacts (graphs, exports, reports); safe to delete
  and regenerate.
- `docs/` — the source of truth for design decisions during this stage.

## Documentation map

- `docs/ROADMAP.md` — proposed, evolving research workflow (not an approved plan)
- `docs/FAIR_PRINCIPLES.md` — FAIR notes and design mapping
- `docs/KNOWLEDGE_GRAPH_DESIGN.md` — conceptual entities, relationships, ontology notes
- `docs/METADATA_INVENTORY.md` — how we would catalogue metadata + templates
- `docs/ARCHITECTURE.md` — forward-looking architecture notes (nothing finalized)
- `docs/VERIFIED_FACTS_AND_ASSUMPTIONS.md` — verified facts vs. proposed vs. unknown
- `docs/REVIEW_LOG.md` — log of review-worthy changes (keep it updated)
- `docs/metadata_templates/` — fillable inventory templates (no fabricated rows)

## When in doubt

Ask. This is a research project whose scope will evolve; surfacing a question is
cheaper than building the wrong thing. Keep changes small, documented, and
reversible.
