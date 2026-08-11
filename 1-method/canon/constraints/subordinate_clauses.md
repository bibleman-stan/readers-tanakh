# Subordinate Clauses and Special Constructions — Constraint Sub-file

Constraints governing purpose clauses, conditional protases, casus pendens,
כִּי disambiguation, gapped verbs, and infinitive absolute predicates.
Master index: [../constraint_catalog_v1.md](../constraint_catalog_v1.md)

## Constraints in this file

- **JM168-purpose-clause** — Purpose-clause infinitive binding (Prec 5, ADVISORY, JUDGMENT-REQUIRED)
- **JM159e-conditional-protasis** — Conditional protasis–apodosis integrity (Prec 5, ADVISORY, JUDGMENT-REQUIRED)
- **JM157-ki-recitativum** — כִּי recitativum vs. causal disambiguation (Prec 5, ADVISORY, JUDGMENT-REQUIRED)
- **JM174-gapped-verb** — Gapped finite verb in parallel bicolon (Prec 6, ADVISORY, INFORM)
- **JM156-casus-pendens** — Casus pendens own-line (Prec 3, HARD, SPLIT)
- **JM123-inf-abs-predicate** — Infinitive absolute as predicate binding (Prec 3, HARD, BIND)

## Interaction notes

JM156-casus-pendens is HARD / SPLIT despite being in this file with mostly
ADVISORY constraints — it is promoted to HARD because the casus pendens
own-line rule is clear and mechanical (resumptive pronoun = structural marker
that definitively identifies the construction). The SPLIT fires when the topic
NP and its resumptive-pronoun clause appear on the same line.

JM168 and JM159e are both JUDGMENT-REQUIRED because their verdicts depend on
clause-weight evaluation (word count threshold) that the constraint catalog
can detect as a trigger but cannot resolve without rendering-prompt context.

JM157-ki-recitativum is the narrowest of the כִּי disambiguation set. The broader
causal-vs-complement disambiguation is covered by JM157-complement-integrity
(HARD, for the obligatory-complement case) and by validate_causal_ki (MIXED
validator). This entry covers only the recitativum sub-case.

JM174-gapped-verb is INFORM only — it does not require any change. Its role
is to prevent false-positive M4 / No-Anchor Test failures on gapped bicola.

JM123-inf-abs-predicate is HARD for the paronomasia (cognate intensification)
sub-case, ADVISORY for the predicative-absolute sub-case. The catalog entry
marks both at HARD pending confirmation — see edge-case note in master index.

## Weight thresholds

| Constraint | Short threshold (lean BIND) | Long threshold (lean SPLIT/ADVISORY) |
|---|---|---|
| JM168-purpose-clause | ≤3 prosodic words | ≥5 prosodic words |
| JM159e-conditional | ≤4 prosodic words | ≥5 prosodic words |
| JM154-verbless (cross-ref) | ≤5 prosodic words combined | ≥6 words in predicate |

## Validator coverage

| Constraint | Validator / Status |
|---|---|
| JM168 | validate_purpose_clause_binding.py (PROPOSED — §7.3 audit required) |
| JM159e | validate_conditional_protasis_apodosis.py (PROPOSED — §7.3 audit required) |
| JM157-ki | validate_causal_ki.py (partial — causal arm; recitativum arm not separated) |
| JM174 | validate_gapped_verb_parallel.py (PROPOSED — §7.3 audit required) |
| JM156 | validate_clause_nucleus_split.py (H15 guard, positive detector gap) |
| JM123 | No dedicated validator — paronomasia pattern detectable via Token.is_infinitive_absolute + cognate-root check; not yet implemented |
