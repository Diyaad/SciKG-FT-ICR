# Metadata Inventory

How SciKG catalogues the metadata available from a candidate data source, and
how it maps that metadata into the SciKG knowledge-graph model. The goal of a
metadata inventory is to answer, for any source: *what fields exist, how good are
they, what do they mean, and where do they belong in our model?*

This is an **early-stage** activity — inventory first, schema and ingestion
later. It has **not** been performed yet: no real source has been catalogued.
See the proposed workflow in [ROADMAP.md](ROADMAP.md).

---

## Why inventory before ingesting

- You cannot map what you have not catalogued.
- Quality and completeness drive feasibility — a sparsely populated field may not
  be a reliable join key. (Any such judgement must be based on measured values
  from a real source, never an assumed figure.)
- Gaps between a source's fields and the SciKG model reveal what must be
  enriched or left out. (Gaps are documented, not silently filled — see the
  missing-value policy in `CLAUDE.md`.)
- Identifier coverage (DOI/ORCID/ROR/…) determines how findable and linkable the
  resulting graph will be.

---

## Templates

Fillable templates live in [`metadata_templates/`](metadata_templates/). Use one
**source-level** record per data source and one **field-level** inventory
(many rows) per source.

| Template | Granularity | Purpose |
|---|---|---|
| `source_inventory_template.yaml` | One per source | Describe the source itself: access, licensing, identifiers, volume |
| `field_inventory_template.csv` | One row per field | Catalogue every metadata field and its quality |
| `entity_mapping_template.csv` | One row per field→entity mapping | Map source fields onto SciKG entities/attributes/relationships |

Copy a template, fill it in under a source-specific name (e.g.
`<source>_field_inventory.csv`), and keep completed inventories in `docs/` or
alongside the source's working notes. **Populate only from a real, selected
source** — never with invented or placeholder values.

---

## Field inventory: column meanings

The `field_inventory_template.csv` captures, per source field:

| Column | Meaning |
|---|---|
| `source_field` | The field name as it appears in the source |
| `description` | What the field actually contains |
| `data_type` | string / number / date / list / identifier / boolean / other |
| `example_value` | A representative example (redact sensitive data) |
| `populated_pct` | Approx. % of records where the field is present |
| `cardinality` | one / many (single value vs. list) |
| `controlled_vocab` | Does it use a controlled vocabulary? Which one? |
| `identifier_type` | If an identifier: DOI / ORCID / ROR / RRID / IGSN / internal / none |
| `maps_to_entity` | Target SciKG entity (see KG design) |
| `maps_to_attribute` | Target attribute or relationship on that entity |
| `standard_vocab_candidate` | Candidate standard term (schema.org/DC/DCAT/PROV-O/…) |
| `quality_notes` | Consistency, ambiguity, units, encoding issues |
| `fair_relevance` | Which FAIR principle(s) this field supports (F/A/I/R) |

---

## Quality assessment dimensions

When filling `quality_notes` / `populated_pct`, assess the following — recording
only values actually observed in a real source, and leaving cells blank when a
value has not been measured:

- **Completeness** — how often is the field present and non-empty?
- **Consistency** — same format/units/encoding across records?
- **Accuracy** — does the value match reality where checkable?
- **Uniqueness** — for identifiers, are values actually unique?
- **Conformance** — does it follow a known standard or vocabulary?
- **Timeliness** — is there date/versioning info to judge currency?
- **Resolvability** — for identifiers, do they resolve (e.g. a DOI that works)?

---

## Mapping to the SciKG model

For each field, decide its destination using
[KNOWLEDGE_GRAPH_DESIGN.md](KNOWLEDGE_GRAPH_DESIGN.md):

1. **Entity attribute** — a property of one entity (e.g. publication title).
2. **Relationship** — a typed edge to another entity (e.g. author → Researcher).
3. **Identifier** — a persistent identifier (route to the PID strategy).
4. **Provenance** — origin/derivation info (route to ProvenanceRecord).
5. **Drop / defer** — not modeled yet; record why.

Record each decision in `entity_mapping_template.csv` so the mapping is itself
documented and reviewable (FAIR applies to our own work too).

---

## FAIR lens on metadata

A metadata inventory is where FAIR becomes concrete:

- **Findable** — Are there persistent identifiers? Is the metadata rich enough
  to discover the asset without the data?
- **Accessible** — Is the access method/protocol and licensing documented?
- **Interoperable** — Do fields use standard vocabularies? Can they serialize to
  machine-readable form?
- **Reusable** — Is there enough context and provenance to reuse the asset?

See [FAIR_PRINCIPLES.md](FAIR_PRINCIPLES.md) for the self-assessment checklist.

---

## Procedure (abstract — no inventory has been performed)

> **Important:** No real source has been inventoried. The steps below describe
> the *procedure* in the abstract. They do **not** report any observed fields,
> values, or statistics, and must not be read as a completed inventory. Specific
> field names and values are intentionally omitted until a real source is
> selected and accessed.

For a chosen source, the procedure is:

1. **Enumerate fields** — record each metadata field the real source actually
   exposes, one row per field in `field_inventory_template.csv`.
2. **Observe and record quality** — for each field, capture data type,
   cardinality, controlled vocabulary, and any *measured* population/quality
   figures. Leave figures blank where not measured; never estimate.
3. **Classify identifiers** — note which fields are persistent identifiers and of
   what type, and whether they resolve.
4. **Map to the model** — decide whether each field is an entity attribute, a
   typed relationship, an identifier, provenance, or out of scope, recording the
   decision and a confidence level in `entity_mapping_template.csv`.
5. **Tag FAIR relevance** — note which FAIR principle(s) each field supports.

The real output of this procedure is a documented, quality-aware, source-specific
mapping — produced only from observed data, with gaps left explicit rather than
filled.
