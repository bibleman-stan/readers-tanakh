# Relative Clauses — Constraint Sub-file

Constraints governing restrictive and non-restrictive אֲשֶׁר-clauses.
Master index: [../constraint_catalog_v1.md](../constraint_catalog_v1.md)

## Constraints in this file

- **JM158-restrictive-relative** — Restrictive relative-clause binding (Prec 5, ADVISORY, BIND)
- **JM158-nonrestrictive-relative** — Non-restrictive relative-clause licensing (Prec 7, ADVISORY, INFORM)

## Interaction notes

JM158-restrictive fires BEFORE JM158-nonrestrictive when both could apply.
The disambiguation heuristic (proper name / uniquely-identified head = likely
non-restrictive; indefinite or definite common noun = likely restrictive) is
applied in order: check restrictive first; if head is proper name or YHWH,
route to non-restrictive.

Both entries are ADVISORY because the restrictive/non-restrictive distinction
requires contextual evaluation that the catalog cannot mechanically resolve.
HARD tier would require a reliable Macula-based disambiguation oracle for this
contrast, which does not yet exist.

## Macula primitive

`Constituent.is_relative_clause` — True when `wg_class == "relp"` or
`wg_rule == "relCL"`. This is the primary detection primitive for both entries.
The discriminating test (restrictive vs. non-restrictive) is based on:
- Head-noun type: `Token.type_ == "proper"` → non-restrictive candidate
- Definiteness + uniqueness: definite article + semantically unique referent → non-restrictive candidate
- Indefinite or generic common noun → restrictive default

## Validator coverage

| Constraint | Primary Validator | Notes |
|---|---|---|
| JM158-restrictive | validate_restrictive_relative_binding.py (PROPOSED) | Requires §7.3 audit before build |
| JM158-nonrestrictive | No dedicated validator — INFORM only | Surfaces via rendering-prompt audit |

Note: `validate_restrictive_relative_binding.py` is listed in the 1100 reply
Item 3 as a proposed validator. It requires its own §7.3 adversarial audit
(≥2 parallel agents) before any code is written. The Macula `relp` constituent
is the right primitive (confirmed in 1100 reply Item 3).
