# Bonded Pairs, Formulae, and Continuity — Constraint Sub-file

Constraints governing bonded pairs, frozen formulaic units, cross-verse
continuity, and the wayehi FEF construction.
Master index: [../constraint_catalog_v1.md](../constraint_catalog_v1.md)

## Constraints in this file

- **JM177-bonded-pair** — Bonded pair hendiadys/merism (Prec 2, HARD, BIND)
- **JM-oath-formula** — Oath-formula integrity (Prec 3, HARD, BIND)
- **JM-cross-verse-continuity** — Cross-verse grammatical-unit continuity (Prec 4, HARD, BIND)
- **JM-wayehi-fef-protasis** — Wayehi-FEF protasis integrity (Prec 4, HARD, BIND/SPLIT)

## Interaction notes

JM177 (bonded pair) fires BEFORE JM-wayehi-fef because Prec 2 < Prec 4. If a
wayyiqtol pair appears within a FEF protasis, JM177 applies to the pair first.
In practice, bonded wayyiqtol pairs in FEF protases are rare.

JM-wayehi-fef has a dual verdict: BIND for fragmentation of the protasis,
SPLIT for collapse of protasis + apodosis onto one line. This is the only
constraint in the catalog with a dual verdict family; both arms are HARD.

JM-cross-verse-continuity overlaps with JM103-proclitic-stranding and
JM129-construct-chain at verse boundaries — those constraints apply at all
positions including verse-end; this entry specifically addresses the
VERSIFICATION boundary as a potential false split trigger.

JM-oath-formula is governed by formula-integrity (canon §1), not a Joüon-
section grammar rule per se. The JM §147 citation covers the broader category
of oaths and adjurations; the specific oath-formula constraint derives from
canon M4 + formula-integrity.

## Closed lists referenced

- 13-pair bonded-pair structural list: `5-machinery/validators/_shared/hendiadys_lemma_pairs.py` (active)
- 88-pair BONDED_LEMMA_PAIRS: DORMANT (not mechanically consulted; reference only)
- OATH_FORMULA_PATTERNS: חֵי + divine-name, בְּחֵי + divine-name
- SPEECH_FRAME_VERBS: subset relevant to cross-verse continuity arm 3

## Validator coverage

| Constraint | Primary Validator | Notes |
|---|---|---|
| JM177 | validate_bonded_pair.py | 13-pair closed list, HARD |
| JM-oath-formula | validate_oath_formula.py | Formula integrity + M4 |
| JM-cross-verse | validate_cross_verse_continuity.py | 4 sub-cases |
| JM-wayehi-fef | validate_wayehi_protasis.py | BIND (merge arm) + SPLIT (split arm) |
