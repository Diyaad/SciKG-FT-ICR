# SciKG — researcher-equivalence EMIT (CC-ready) — from Veronika's review

Input to the SAME_AS emit step. Veronika reviewed all 37 pairs in
`researcher_equivalence_review_packet.md`. Result: **24 SAME_AS to emit** (all
`anchor_type='human_review'`), **1 held** (unsure), **11 confirmed different** (no edge).
Nothing is merged — both nodes and both names are always kept.

## Emit rules (read first)
- `SAME_AS` is **undirected**; stored `a -> b` with `a < b` lexicographic (already sorted below).
  Always query it as `-[:SAME_AS]-` (no arrow).
- `anchor_type = 'human_review'` for all 24 — the proof is Veronika's judgment, NOT a shared ORCID
  (distinct from the 3 ORCID-proven `SAME_AS` already in the graph).
- Six provenance properties on each edge; `evidence_note` = the basis text; source is human review.
- Confirm `SAME_AS` is registered in **both** `04_validate.py` (`RELATIONSHIP_FILES`) and `05_load.py`
  (`REL_TYPES`) before loading (KI-17) — the type already exists for the 3 ORCID edges, so the
  human_review edges reuse it.
- Run on the canonical / poster instance; the other instance rebuilds or re-emits after. (Which
  instance is canonical is Diya's call.)

## 1 — SAME_AS edges to emit (24) — JSONL
```jsonl
{"a":"researcher:rodgers_r","b":"researcher:rodgers_r_p_x","anchor_type":"human_review","mechanism":"period_parse","basis":"Rodgers R.P.; period-parse split; 4 shared co-authors incl. Marshall, McKenna. SEE FLAG A (node A name_full is itself fused)."}
{"a":"researcher:rodgers_r","b":"researcher:rogers_r","anchor_type":"human_review","mechanism":"spelling_variant","basis":"Rodgers R.P.; dropped 'd'; 6 shared co-authors incl. Marshall. Part of Rodgers cluster (FLAG A)."}
{"a":"researcher:peru_k","b":"researcher:peru_k_m_x","anchor_type":"human_review","mechanism":"period_parse","basis":"Kerry M. Peru; period-parse; 5 shared co-authors incl. Rodgers, Headley."}
{"a":"researcher:arumanayagam_a","b":"researcher:asumanayagam_a","anchor_type":"human_review","mechanism":"ocr_variant","basis":"Anitha Christy Sigamani Arumanayagam; OCR r/s; 3 shared co-authors."}
{"a":"researcher:chamot_rook_j","b":"researcher:chamot_rooke_j","anchor_type":"human_review","mechanism":"ocr_variant","basis":"Julia Chamot-Rooke; OCR dropped final e; 10 shared co-authors."}
{"a":"researcher:colilo_y","b":"researcher:corilo_y","anchor_type":"human_review","mechanism":"ocr_variant","basis":"Yuri E. Corilo; OCR l/r; 3 shared co-authors."}
{"a":"researcher:dehghanizade_m","b":"researcher:dehghanizadeh_m","anchor_type":"human_review","mechanism":"ocr_variant","basis":"Mostafa Dehghanizadeh; truncated final h."}
{"a":"researcher:dzeilewski_a","b":"researcher:dzwilewski_a","anchor_type":"human_review","mechanism":"ocr_variant","basis":"Andrzej Dzwilewski; OCR."}
{"a":"researcher:nagirnov_k","b":"researcher:nagornov_k","anchor_type":"human_review","mechanism":"ocr_variant","basis":"Konstantin Nagornov; OCR i/o."}
{"a":"researcher:standford_l","b":"researcher:stanford_l","anchor_type":"human_review","mechanism":"ocr_variant","basis":"Lateefah A. Stanford; extra d."}
{"a":"researcher:tzortiziou_m","b":"researcher:tzortziou_m","anchor_type":"human_review","mechanism":"ocr_variant","basis":"Maria Tzortziou; OCR extra i."}
{"a":"researcher:jeppensen_e","b":"researcher:jeppesen_e","anchor_type":"human_review","mechanism":"ocr_variant","basis":"Erik Jeppesen; extra n."}
{"a":"researcher:hawkings_j","b":"researcher:hawkins_j","anchor_type":"human_review","mechanism":"ocr_variant","basis":"Hawkings J.R.; ORCID on hawkings_j; shared co-authors. (medium confidence)"}
{"a":"researcher:mathews_j","b":"researcher:matthews_j","anchor_type":"human_review","mechanism":"ocr_variant","basis":"Jonathan P. Mathews; single/double t. (medium confidence)"}
{"a":"researcher:zimmerman_r","b":"researcher:zimmermann_r","anchor_type":"human_review","mechanism":"spelling_variant","basis":"Ralf Zimmermann; single/double n."}
{"a":"researcher:meyer_baese_a","b":"researcher:meyer_base_a","anchor_type":"human_review","mechanism":"spelling_variant_ae_umlaut","basis":"Anke Meyer-Baese; ae/a-umlaut transliteration."}
{"a":"researcher:ahif_d","b":"researcher:ahlf_d","anchor_type":"human_review","mechanism":"ocr_variant","basis":"Dorothy R. Ahlf; OCR l/i."}
{"a":"researcher:oomens_j","b":"researcher:oomes_j","anchor_type":"human_review","mechanism":"ocr_variant","basis":"Jos Oomens; dropped n."}
{"a":"researcher:sets_e","b":"researcher:stets_e","anchor_type":"human_review","mechanism":"ocr_variant","basis":"Edward Stets; dropped t; 9 shared co-authors."}
{"a":"researcher:guluyz_k","b":"researcher:gulyuz_k","anchor_type":"human_review","mechanism":"transposition","basis":"Kerim Gulyuz; transposition."}
{"a":"researcher:schulga_y","b":"researcher:shul_ga_y","anchor_type":"human_review","mechanism":"transliteration","basis":"Shul'ga Y.M.; transliteration."}
{"a":"researcher:pa_sa_toli_l","b":"researcher:pasa_tolic_l","anchor_type":"human_review","mechanism":"transliteration","basis":"Ljiljana Pasa-Tolic; old accent-mangling; 8 shared co-authors."}
{"a":"researcher:avery_g","b":"researcher:avery_jr_g","anchor_type":"human_review","mechanism":"suffix_jr","basis":"G. Brooks Avery; Jr. suffix."}
{"a":"researcher:vladimirov_g","b":"researcher:vladimirova_g","anchor_type":"human_review","mechanism":"corrected_exclusion","basis":"Gleb Vladimirov (one man); was excluded on a masculine/feminine surname assumption — Veronika corrected to SAME."}
```

## 2 — ORCID node properties to SET (where the node's orcid IS null; never overwrite)
Includes ORCIDs Veronika found during review, normalized (id only, no `https://`, doubled-typing
fixed). **Set only where `r.orcid` is null. Never overwrite. If a value here already sits on a
DIFFERENT node, STOP and flag** (possible missed equivalence or an error).
```
researcher:rodgers_r         0000-0003-1302-2850
researcher:peru_k            0000-0002-2819-8595
researcher:arumanayagam_a    0000-0001-6924-0705
researcher:chamot_rooke_j    0000-0002-9427-543X
researcher:corilo_y          0000-0002-1368-8217    # cleaned: raw note had it typed twice
researcher:dehghanizadeh_m   0000-0002-6283-0101
researcher:jeppesen_e        0000-0002-0542-369X
researcher:hawkings_j        0000-0003-4813-8474
researcher:tzortziou_m       0000-0002-4510-7827
researcher:zimmermann_r      0000-0002-6280-3218
researcher:meyer_base_a      0000-0001-6363-2687
researcher:stets_e           0000-0001-5375-0196
researcher:shul_ga_y         0000-0001-8020-4465
researcher:pasa_tolic_l      0000-0001-9853-5457
# excluded pairs, but real ORCIDs Veronika found — for provenance / keys, NO SAME_AS:
researcher:putman_j          0000-0002-1944-3990
researcher:baker_a           0000-0002-1552-6166
researcher:jorner_k          0000-0002-4191-6790
```
**Do NOT set** `researcher:parker_a` — Parker and Baker are different people (excluded pair 31); the
`0000-0002-1552-6166` belongs to Baker only.

## 3 — Special handling (read before emitting)
- **FLAG A — Rodgers is a 3-node cluster.** `rodgers_r` links to BOTH `rodgers_r_p_x` and `rogers_r`.
  Emit both edges; they converge on `rodgers_r`. Treat as one equivalence set of three — any "complete
  Rodgers output" query traverses all `SAME_AS` from `rodgers_r`.
- **FLAG B — `rodgers_r.name_full` is itself fused.** It reads "Rodgers, R.P., Weinheber, P." — two
  people. Weinheber, P. was swallowed and has no node/edge on those papers. This is the co-author
  fusion / parser bug on the canonical Rodgers node, **not** a `SAME_AS` matter — route it to the
  parser fix, do not touch it here.
- **HELD (no edge yet):** `angstrom_j` ↔ `anstrom_j` (Pair 3, UNSURE) → second look / David. Note this
  is distinct from the *confirmed-different* `angstrom_j` ↔ `nystrom_j` (Pair 27) — the open question is
  Angstrom vs Anstrom only.
- **Confirmed different (no edge):** pairs 27–37 minus 26 — 11 exclusions upheld.

## Do NOT
Merge any nodes (SAME_AS keeps both). Emit an edge for the HELD pair. Set an ORCID onto a node that
already has a different one, or onto Parker. Emit the Weinheber fusion as an equivalence. Run git.

---

## Note appended 2026-07-25 (not part of the received document)

Everything above is the review input exactly as received and is the `source_id`
(`review:researcher_equivalence_EMIT.md`) recorded on all 24 `human_review` `SAME_AS` edges in
production. It is preserved unaltered; this note is additive only.

The `researcher_equivalence_review_packet.md` referenced in the header is an **out-of-band hand-off
artifact** — it was sent directly to the reviewer and is **deliberately not tracked in this repo**, so
that filename does not resolve to anything in a clone (the on-disk copy is also a `.txt`, not the `.md`
spelled above). The tracked equivalents are:

- **`docs/researcher_equivalence_review.md`** — the committed review sheet: candidates by mechanism
  with their same/different dispositions.
- **`docs/KNOWN_ISSUES.md` KI-17** — the recorded outcome: 24 emitted as `SAME_AS`
  (`anchor_type='human_review'`), 1 HELD (`angstrom_j`↔`anstrom_j`), 11 confirmed different,
  0 `POSSIBLY_SAME_AS` ever written.

Cite those two, not the packet.
