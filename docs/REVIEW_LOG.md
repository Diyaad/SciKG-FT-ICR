# SciKG Documentation & Review Log

This log tracks issues, assumptions, cleanup actions, errors, possible fabricated
content, and any change that may need human review.

**When to update this file:** whenever documentation is modified, an assumption
is removed or rewritten, uncertainty is encountered, possibly fabricated content
is found, or any change is made that may need review. (See the rule in
`CLAUDE.md`.)

Add new rows at the **top** of the table (most recent first). Keep "Review
Needed?" honest — when in doubt, mark **Yes**.

| Date | File | Issue Found | Action Taken | Reason | Review Needed | Notes |
|---|---|---|---|---|---|---|
| 2026-06-11 | docs/metadata_templates/source_inventory_template.yaml | Example filenames/values referenced a specific candidate source; "leave unknowns as null" was too prescriptive | Genericized example filename; restated missing-value note to "leave as-is / N/A / null / blank per schema, never infer" | Avoid implying a source was chosen; align with missing-value policy | No | — |
| 2026-06-11 | docs/metadata_templates/entity_mapping_template.csv | Fabricated illustrative mapping rows (e.g. instrument→Instrument, funding_ack→Grant) implied a real source had been mapped | Removed all example data rows; kept header + column guidance | Data-integrity policy: no fabricated/illustrative records | No | Template now populated only from a real, selected source |
| 2026-06-11 | docs/metadata_templates/field_inventory_template.csv | Fabricated example rows: fake DOI (10.xxxx/xxxxx), fake instrument ("9.4T FT-ICR MS"), invented population percentages (100/92/99/40/55), fake titles/values | Removed all example data rows; kept header + guidance; added explicit "no fabricated rows / blank when unknown" note | Data-integrity policy: no fake DOIs, instruments, percentages, or records | No | — |
| 2026-06-11 | docs/METADATA_INVENTORY.md | "a field that is 12% populated" (invented statistic); worked NHMFL/FT-ICR example listed specific fields as if observed | Removed invented percentage; rewrote worked example as an abstract, clearly-hypothetical procedure with no specific field values | Data-integrity policy: no invented statistics or implied inventories | Yes | Confirm the abstract example is acceptable, or remove entirely |
| 2026-06-11 | docs/ARCHITECTURE.md | "leaning RDF-canonical" and "Anthropic Claude models are the default LLM" presented soft decisions as settled; "Phase N" implied an approved plan | Marked all technology choices as deferred/candidate; removed "leaning"/"default"; changed phase references to "a later stage" | No architecture decision is final; nothing is approved | Yes | Backend, vocabularies, LLM, vector store all still undecided |
| 2026-06-11 | docs/KNOWLEDGE_GRAPH_DESIGN.md | "Leaning: RDF aligns better..." stated a preference; "(likely Publication, Researcher, ...)" assumed a starting subset; "Phase N" references | Reframed RDF/property-graph as a neutral, undecided trade-off; softened the subset to "to be decided"; phase→stage | Keep design conceptual and undecided; nothing approved | Yes | Entity/relationship model is proposed, not validated against real data |
| 2026-06-11 | docs/ROADMAP.md | Generated 7-phase structure implied an approved plan, phase counts, and scope not provided by the supervisor | Rewrote as a "Proposed Research Workflow" with a prominent not-approved banner; replaced fixed phases with unordered, unapproved candidate stages | Avoid implying approved timelines/phase counts/scope | Yes | Supervisor to confirm or replace the proposed workflow |
| 2026-06-11 | README.md | "Phase 0" status language implied an approved phase plan; candidate source needed clearer "not investigated" framing | Reframed status to "research-foundation stage"; clarified NHMFL/FT-ICR is a brief-named candidate that has NOT been investigated; added doc-index entries | Align with proposed-workflow language and data-integrity policy | Yes | NHMFL/FT-ICR mention is traceable to the project brief; no specifics asserted |
| 2026-06-11 | CLAUDE.md | Needed data-integrity / missing-value policy and a review-log rule; "Phase 0" wording | Added Data Integrity Policy (incl. missing-value rule), added REVIEW_LOG.md rule, updated documentation map, softened phase wording | Establish the integrity guardrails this audit enforces | No | — |
| 2026-06-11 | docs/VERIFIED_FACTS_AND_ASSUMPTIONS.md | New file | Created: separates Verified Facts / Proposed Ideas / Unknowns / Removed Assumptions | Make the verified-vs-assumed distinction explicit and auditable | No | — |
| 2026-06-11 | docs/REVIEW_LOG.md | New file | Created this log | Track review-worthy changes going forward | No | — |
