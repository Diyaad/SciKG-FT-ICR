# FAIR Data Notes

SciKG is designed around the **FAIR** principles — that scientific assets should
be **F**indable, **A**ccessible, **I**nteroperable, and **R**eusable, by humans
*and* machines. This document records what each principle means for SciKG and
how it maps to concrete design decisions.

> Reference: Wilkinson et al. (2016), *The FAIR Guiding Principles for
> scientific data management and stewardship*, Scientific Data 3:160018.
> The canonical numbered sub-principles (F1–F4, A1–A2, I1–I3, R1) are summarized
> below in SciKG terms.

---

## F — Findable

*If you can't find it, you can't use it.* Findability comes first because the
other principles depend on it.

**Sub-principles (FAIR canonical)**
- **F1** — (Meta)data are assigned globally unique, persistent identifiers.
- **F2** — Data are described with rich metadata.
- **F3** — Metadata clearly and explicitly include the identifier of the data
  they describe.
- **F4** — (Meta)data are registered or indexed in a searchable resource.

**SciKG design implications**
- Every entity (publication, dataset, instrument, researcher, …) carries a
  **persistent identifier** — reuse external PIDs where they exist (DOI, ORCID,
  ROR, RRID) and mint internal PIDs otherwise.
- **Rich metadata** is the default, not an afterthought; see
  [METADATA_INVENTORY.md](METADATA_INVENTORY.md).
- The **knowledge graph itself is the searchable index** — relationships are
  first-class and queryable, not buried in free text.
- Metadata records explicitly reference the identifier of what they describe.

---

## A — Accessible

*Once found, how is it retrieved?* Accessible does **not** mean "open" — it
means the access conditions and mechanism are clear and standardized. Metadata
should remain accessible even when the underlying data cannot be.

**Sub-principles (FAIR canonical)**
- **A1** — (Meta)data are retrievable by their identifier using a standardized,
  open, free, universally implementable protocol.
- **A1.1 / A1.2** — The protocol supports authentication/authorization where
  necessary.
- **A2** — Metadata remain accessible even when the data are no longer
  available.

**SciKG design implications**
- **Standardized retrieval**: identifier-resolvable access via well-defined
  query interfaces (e.g. SPARQL/Cypher) and documented APIs.
- **Clear access pathways**: each source's access method, protocol, and any
  authentication/licensing constraints are documented (a later stage in the
  proposed workflow; see [ROADMAP.md](ROADMAP.md)).
- **Metadata persistence**: descriptive metadata and provenance survive even if
  the original data become unavailable or restricted.
- Access conditions are explicit — restricted ≠ undocumented.

---

## I — Interoperable

*Data needs to integrate with other data, and with tools and workflows.*

**Sub-principles (FAIR canonical)**
- **I1** — (Meta)data use a formal, accessible, shared, broadly applicable
  language for knowledge representation.
- **I2** — (Meta)data use vocabularies that themselves follow FAIR principles.
- **I3** — (Meta)data include qualified references to other (meta)data.

**SciKG design implications**
- **Structured schemas**: entities/relationships defined in machine-readable
  schemas (JSON Schema / SHACL), not ad-hoc structures.
- **Standard vocabularies**: align with established vocabularies and ontologies
  where possible (e.g. schema.org, Dublin Core, DCAT, PROV-O, domain ontologies)
  rather than inventing terms.
- **Machine-readable metadata**: serialize in interoperable formats (JSON-LD,
  RDF/Turtle) so SciKG can exchange data with external systems.
- **Qualified links**: relationships are typed and meaningful (e.g.
  `wasGeneratedBy`, `usedInstrument`, `fundedBy`) rather than untyped pointers.

---

## R — Reusable

*The ultimate goal: optimize reuse.* Reuse requires rich context and clear terms
of use.

**Sub-principles (FAIR canonical)**
- **R1** — (Meta)data are richly described with a plurality of accurate and
  relevant attributes.
- **R1.1** — (Meta)data are released with a clear and accessible data-usage
  license.
- **R1.2** — (Meta)data are associated with detailed provenance.
- **R1.3** — (Meta)data meet domain-relevant community standards.

**SciKG design implications**
- **Provenance tracking** is mandatory: every node and edge records where it
  came from and how it was derived (`raw → processed → outputs`). PROV-O is the
  candidate provenance model.
- **Context preservation**: experimental context, methods, instruments, samples,
  and project/grant linkages are retained, not discarded during processing.
- **Documentation & reproducibility**: processed data and outputs must be
  regenerable from raw sources plus code; transformations are documented.
- **Licensing**: usage terms recorded per asset (to be specified in a later
  phase).
- **Community standards**: adopt domain-relevant conventions where they exist.

---

## FAIR ≠ Open

FAIR is about being *well-described and machine-actionable*, independent of
whether data are openly available. SciKG can describe restricted assets FAIRly:
the **metadata and provenance are rich and accessible** even when the data
itself is access-controlled.

## How SciKG operationalizes FAIR

| FAIR need | SciKG mechanism |
|---|---|
| Persistent identifiers | External PIDs (DOI/ORCID/ROR/RRID) + internal PID minting |
| Rich metadata | Metadata inventory + schemas ([METADATA_INVENTORY.md](METADATA_INVENTORY.md)) |
| Searchable index | The knowledge graph + query/search interfaces |
| Standard retrieval | Documented query endpoints & APIs |
| Interoperable formats | JSON-LD / RDF, standard vocabularies |
| Typed relationships | Knowledge-graph edges ([KNOWLEDGE_GRAPH_DESIGN.md](KNOWLEDGE_GRAPH_DESIGN.md)) |
| Provenance | PROV-O–style provenance on every node/edge |
| Reproducibility | `raw → processed → outputs` data flow + code |

## FAIR Self-Assessment Checklist (use each phase)

- [ ] Does every new entity type have a persistent identifier strategy?
- [ ] Is the metadata for it rich enough to be discovered without the data?
- [ ] Is it retrievable through a documented, standardized mechanism?
- [ ] Are access/licensing conditions explicit?
- [ ] Does it use standard vocabularies and serialize to machine-readable form?
- [ ] Are its relationships typed and qualified?
- [ ] Is provenance captured for every fact?
- [ ] Can processed/output forms be regenerated from raw + code?

## Ontology and Standards Alignment

SciKG uses the following standard vocabularies to 
ensure interoperability with major scientific databases:

| Standard | Scope | Source | Use in SciKG |
|---|---|---|---|
| PSI-MS ontology | MS methods and instruments | github.com/HUPO-PSI/psi-ms-CV | Canonical IDs on Method and Instrument nodes |
| UNIMOD | Protein modifications | unimod.org | Canonical IDs on Modification nodes |
| NCBI Taxonomy | Organism names | ncbi.nlm.nih.gov/taxonomy | Canonical IDs on Organism nodes |
| UniProt | Protein identifiers | uniprot.org | Accession numbers on Protein nodes |
| DataCite | Dataset metadata | schema.datacite.org | Dataset node structure |
| ORCID | Researcher identifiers | orcid.org | orcid property on Researcher nodes |
| ROR | Research organization IDs | ror.org | Optional property on Institution nodes |
| DOI | Publication identifiers | doi.org | Master key for Publication nodes |

These standards make SciKG interoperable with 
ProteomeXchange, MassIVE, UniProt, and major 
proteomics databases without additional mapping.
