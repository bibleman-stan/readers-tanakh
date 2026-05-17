# Bound Nominals — Constraint Sub-file

Constraints governing prosodic-word and NP-level indivisibility.
Master index: [../constraint_catalog_v1.md](../constraint_catalog_v1.md)

## Constraints in this file

- **JM13-maqqef-group** — Maqqef-group indivisibility (Prec 1, HARD, BIND)
- **JM103-proclitic-stranding** — Proclitic line-final stranding (Prec 1, HARD, BIND)
- **JM103e-compound-prep-object** — Compound-preposition object stranding (Prec 1, HARD, BIND)
- **JM129-construct-chain** — Construct-chain integrity (Prec 2, HARD, BIND)

## Interaction notes

JM13 and JM103 operate at the sub-word level (prosodic-word boundary); they fire before any NP-level or clause-level constraint. JM129 fires at the NP level (NPofNP constituent). When a construct chain is also maqqef-joined, JM13 fires first (Prec 1); JM129 is redundant in that case but fires separately for non-maqqef construct chains.

JM103e (compound preposition) is a superset of JM103 in the sense that any compound preposition whose object is stranded also has a proclitic-stranding issue, but the mechanisms differ: JM103 covers single morpheme-prefix proclitics; JM103e covers multi-morpheme compound prepositions that are orthographically independent words.

## Validator coverage

| Constraint | Primary Validator | Notes |
|---|---|---|
| JM13 | validate_maqqef_integrity.py | Syntax layer |
| JM103 | validate_line_final_tokens.py | Syntax layer |
| JM103e | validate_compound_preposition_object.py | Colometry layer |
| JM129 | validate_construct_chain.py + validate_bare_construct_head.py | IR path + fallback |
