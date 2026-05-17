# Particles and Negation — Constraint Sub-file

Constraints governing discourse particles, interrogative particles, negation,
and vocative/extra-clausal elements.
Master index: [../constraint_catalog_v1.md](../constraint_catalog_v1.md)

## Constraints in this file

- **JM155-discourse-particle** — Bare discourse-particle indivisibility (Prec 3, HARD, BIND)
- **JM161-interrogative-particle** — Bare interrogative-particle indivisibility (Prec 3, HARD, BIND)
- **JM160-negation-scope** — Negation-particle scope binding (Prec 2, HARD, BIND)
- **JM147-vocative-extraclausal** — Vocative and extra-clausal element placement (Prec 6, ADVISORY, INFORM)

## Interaction notes

JM155 and JM161 both fire on particle-tokens at line position; they are mutually
exclusive (a particle is either a discourse particle or an interrogative, not
both — check `Token.type_` to discriminate). JM160 covers negation particles,
which are a third distinct category.

JM160 at Prec 2 fires before JM155 and JM161 at Prec 3 when a negation particle
appears in contexts also involving discourse particles. In practice negation and
discourse particles occupy distinct syntactic positions and do not co-fire.

JM147 is ADVISORY / INFORM and does not block or require any line change on its
own. It surfaces vocative-position elements for editorial review. Canon H4
(Vocative Handling) is the operative rule; this catalog entry anchors it in the
constraint taxonomy.

## Closed lists referenced

- DISCOURSE_PARTICLE_LEMMAS: הִנֵּה, לָכֵן, עַל־כֵּן, אָז, וְעַתָּה, הֲלֹא, אֵפֹא
- INTERROGATIVE_LEMMAS: מִי, מָה, אַיֵּה, אֵיךְ, לָמָה, מַדּוּעַ, אָן
- NEGATION_LEMMAS: לֹא, אַל, אֵין, בַּל, לְבִלְתִּי

## Validator coverage

| Constraint | Primary Validator | Notes |
|---|---|---|
| JM155 | validate_bare_discourse_particle.py | M3 + H14 |
| JM161 | validate_interrogative_clause.py | M3 |
| JM160 | validate_line_final_tokens.py (partial) | Negation-stranding sub-check |
| JM147 | No dedicated validator — editorial (H4) | Surfaced via review sweeps |
