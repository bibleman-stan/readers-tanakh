# Clause Nucleus — Constraint Sub-file

Constraints governing clause-nucleus integrity: verb-object bonds, complements,
verbless clauses, and participial predicates.
Master index: [../constraint_catalog_v1.md](../constraint_catalog_v1.md)

## Constraints in this file

- **JM125-verb-object-bond** — Verb–direct-object nucleus bond (Prec 2, HARD, BIND)
- **JM125-coordinated-objects** — Coordinated direct-object integrity (Prec 2, HARD, BIND)
- **JM157-complement-integrity** — Obligatory-complement integrity (Prec 2, HARD, BIND)
- **JM154-verbless-clause-nucleus** — Verbless-clause nucleus integrity (Prec 3, HARD, BIND)
- **JM121-participial-predicate** — Participial-predicate nucleus integrity (Prec 3, HARD, BIND)
- **JM133-verb-pp-complement** — Verb–PP complement bond (Prec 3, HARD, BIND)

## Interaction notes

JM125-verb-object-bond and JM125-coordinated-objects are two arms of the same
underlying constraint (M2 Verb-Object Clause-Nucleus Bond). The single-DO case
uses frame-arg A1 on one token; the coordinated case uses multiple A1 tokens.
The colometry validator `validate_verb_object_bond.py` covers both but the
coordinated case has its own validator `validate_coordinated_object.py`.

JM157-complement-integrity is closely related but distinct: it covers the
clausal-complement case (כִּי-clause as obligatory argument of cognition/speech
verbs), not the nominal-DO case. When a verb takes BOTH a nominal DO and a
כִּי-clause (rare), both JM125 and JM157 apply independently.

JM154 (verbless-clause subject + predicate) and JM121 (subject + participial
predicate) are mutually exclusive at any given boundary: JM121 fires when the
line-N+1 predicate is participial; JM154 fires when it is a PP or nominal. When
uncertain whether the N+1 predicate is participial, check `Token.is_participle`
first (JM121 wins as the narrower rule).

JM133 (verb + obligatory PP complement) may co-fire with JM125 when a verb
governs both a nominal DO and an obligatory PP. In that case, both constraints
bind; the priority ordering (JM125 Prec 2 > JM133 Prec 3) means JM125 fires
first and the PP constraint is evaluated as an additional BIND.

## Validator coverage

| Constraint | Primary Validator | Notes |
|---|---|---|
| JM125-verb-object-bond | validate_verb_object_bond.py | Macula frame-arg A1 |
| JM125-coordinated-objects | validate_coordinated_object.py | Multiple A1 tokens |
| JM157-complement-integrity | validate_complement_integrity.py | Closed-list cognition verbs |
| JM154-verbless-clause-nucleus | validate_clause_nucleus_split.py (H18.1) | Macula clause constituent |
| JM121-participial-predicate | validate_clause_nucleus_split.py (H18.2) | Token.is_participle |
| JM133-verb-pp-complement | validate_clause_nucleus_split.py (H18.3) | Obligatory-PP verb list |
