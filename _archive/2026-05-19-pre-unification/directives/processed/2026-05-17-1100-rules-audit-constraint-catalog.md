# Rules audit — re-role validator stack from producers to constraints

## Context — methodological breakthrough 2026-05-17

A multi-experiment investigation on Psalm 1 surfaced that the architecture did not match the method:

- **Method**: ATUs are cognitive units identified by the bidirectional test (forward grammatical closure + backward referential self-containment). Syntactic rules CONSTRAIN ATU well-formedness but do NOT CREATE ATUs. Parallelism is a poetic-rhetorical feature operating on a separate axis from ATU rendering.
- **Architecture (as-built)**: R/H validators ran FIRST and produced ATU rendering via procedural rules; LLM ran SECOND as residue cleanup / audit. Order inverted relative to the method.

The empirical evidence base:

- **Two-leg / three-leg on Ps 1 original (16-line state)**: 0 of 4 needed corrections caught. Validators leave the over-broken/under-broken state untouched on this verse-class.
- **Four-leg with conservative cognitive-unity gate**: 5 of 6 verses match Stan's manual baseline (14 ATUs); over-merges v.5 because no gapped-verb rule.
- **Pure LLM with bidirectional test alone**: 5 of 6 verses match (same accuracy as four-leg); over-splits v.3 because no restrictive-relative rule.
- **Pure LLM without cognitive-unity gate**: 5 of 6 verses match — IDENTICAL result. The gate is empirically inert.
- **Stan's manual baseline**: 14 ATUs (ground truth).

Conclusion: the LLM with parse-aware bidirectional test does the load-bearing work. Validators don't produce correct ATU rendering on this verse-class. The cognitive-unity gate is empirically unnecessary. What WOULD close the remaining accuracy gap: targeted Hebrew syntactic constraints applied as AUDIT (constraints on LLM-proposed ATU boundaries), not as PRODUCERS.

This directive begins the architecture-to-method realignment by auditing the existing validator stack against a constraint-vs-producer criterion.

## Items

### Item 1 — Per-validator categorization (full stack)

For each validator in `validators/colometry/` and `validators/syntax/`:

1. **Encoded question**: what does this validator's rule check? Express in one sentence.
2. **Categorization**:
   - **CONSTRAINT** — encodes a Hebrew syntactic rule answering a yes/no grammatical question (is this break inside a construct chain? does this verb have its obligatory complement on the same line? is this relative clause restrictive?). KEEP — re-role to audit mode.
   - **PRODUCER** — encodes a procedural rule that creates ATU rendering decisions (split parallel clauses; split at clause boundaries within bicola; etc.). PROBABLY RETIRE or REFINE to constraint form if a real constraint underlies it.
   - **MIXED** — partly constraint, partly producer. Surface for decomposition.
3. **FP rate sample**: take 20 random current findings per validator. LLM-classify each as TP / FP / AMBIGUOUS. Compute FP rate. If FP rate >30%, surface for refinement priority.
4. **Coverage**: does this validator catch a real syntactic constraint that doesn't otherwise exist in the stack? If yes, keep priority. If a sibling validator already catches the same constraint, surface for consolidation.

### Item 2 — Enumerate missing constraints

Per the Ps 1 analysis, the following Hebrew syntactic constraints are NOT currently captured by the validator stack but are REAL grammatical phenomena that should constrain ATU breaks:

- **Restrictive relative clause binding**: restrictive (defining) `אֲשֶׁר`-clauses bind to their head noun and cannot form standalone ATUs regardless of internal completeness. Diagnostic: would removing the relative clause leave the head uniquely identified? If no → restrictive → bind.
- **Non-restrictive relative clause licensing**: non-restrictive (descriptive) relative clauses may stand alone as ATUs when they pass the bidirectional test AND the head is already identified.
- **Gapped finite verb in immediate parallel cola**: a colon whose finite verb is gapped from the immediately preceding parallel colon counts as forward-closed if the gapped verb is unambiguously recoverable. Currently NO validator captures this; the strict-bidirectional reading mis-fails such cola.
- **Discourse particle + governed content**: particles like `לָכֵן` / `וְעַתָּה` / `הִנֵּה` / `אַשְׁרֵי` lead content and bind to it; the particle alone does not form an ATU, but particle + governed NP/clause does.
- **Coordinate vs subordinate `וְ`**: a `וְ`-led clause may be coordinate (separate ATU) or subordinate (dependent on prior). The distinction is syntactic and grammatically determinable; currently no validator enforces it.

Enumerate the FULL list of Hebrew syntactic constraints relevant to ATU rendering per Joüon-Muraoka §158 (relative clauses), §159 (subordinate clauses), §172-177 (coordination), §150 (verbless clauses), §121 (participial constructions), §174 (gapping), etc. Propose new validator specs for any not yet covered.

### Item 3 — Build missing constraint validators

For constraints surfaced in Item 2 that pass §7.3 audit-discipline:

- `validate_restrictive_relative_binding.py` — checks that restrictive `אֲשֶׁר`-clauses are not split from their head noun
- `validate_gapped_verb_parallel.py` — recognizes verbless cola in synonymous bicola where the verb is gapped from the immediately prior colon; treats as closed (no STRONG-SPLIT recommendation)
- `validate_discourse_particle_binding.py` — checks discourse-particle + content integrity
- Others per Item 2 enumeration

Each new validator requires:
- §7.3 pre-build adversarial audit (≥2 parallel Sonnet agents) per existing precedent
- Constraint-style framing: yes/no answers about syntactic well-formedness, NOT producer-style "do X"
- Integration into the audit-mode pipeline (post-LLM, not pre-LLM)

### Item 4 — Retire / refine producer-style validators

Validators identified in Item 1 as PRODUCER-style or PRODUCER-MIXED:

- `validate_parallel_clause_split` (high priority): empirically a producer of colometric splits on synonymous parallelism. Re-frame: constraint-only check on whether the SPLIT (if proposed) would violate syntactic rules. If the LLM proposes merging two finite-verb-headed clauses into one ATU, the existing detection logic could fire as an audit-mode CONSTRAINT VIOLATION flag. Refine the rule from "do split this" to "if you proposed merging this, here's why that may not be syntactically licensed."
- Other producer-style rules per Item 1 audit findings.

### Item 5 — Architecture-pipeline refactor

After Items 1-4 complete:

1. **LLM-first pipeline**: `scripts/audit_rendered_output.py` (already built) becomes the primary ATU-rendering engine, not just an auditor. The script's prompt is refined to use only the bidirectional test + Hebrew special-case allowances + restrictive-relative binding rule (no cognitive-unity gate, no parallelism category adjudication).
2. **Constraint-audit second**: refined validator stack runs against the LLM-proposed rendering as a CHECK layer. Each constraint validator answers: "is this proposed ATU break grammatically allowed?" Violations are flagged for editorial review, NOT auto-corrected.
3. **Editorial review**: Stan adjudicates conflicts between LLM proposal and constraint flags.

This pipeline is the architecture-method-aligned form.

## Reporting

Reply at `directives/replies/2026-05-17-1100-rules-audit-constraint-catalog.md`:

- Item 1: full per-validator categorization table + FP-rate samples
- Item 2: complete Hebrew syntactic constraint catalog (existing + missing)
- Item 3: proposed validator specs for missing constraints (drafts only — no implementation yet; pre-build adversarial audits gate each implementation per §7.3)
- Item 4: per-producer-validator retirement/refinement proposals
- Item 5: scoping for the architecture-pipeline refactor (which scripts touch, what changes, baseline regression risk)

This is a substantial diagnostic. Expected size: ~$5-10 in Sonnet spend across the per-validator FP sampling. Time scale: 1-2 days of Tanakh-Claude work.

## Audit triggers

This directive itself is diagnostic + planning. Each subsequent implementation (Items 3-5) requires its own §7.3 audit per existing precedent (2203 / 2400 / 2402 lessons).

**Audit-skippable for the categorization + planning work itself per §7.4.**

## Cross-corpus port

Once Tanakh demonstrates the architecture-method-aligned pipeline:

- BoFM: parallel directive — audit BoFM validator stack against the same constraint-vs-producer criterion; enumerate English (EME-register) syntactic constraints relevant to ATU rendering
- GNT: parallel directive — audit GNT validator stack; enumerate Greek syntactic constraints

The architecture is corpus-agnostic; each corpus needs its own grammatically-grounded constraint catalog.

## What this realigns

The fundamental claim: **the architecture going forward matches what the method always actually said.** Cognitive ATU identification (LLM + bidirectional test) is the primary work. Syntactic rules (constraint catalog) audit the candidates. Parallelism is off-axis. Producer-style validators that encoded colometric preferences as if they were ATU rules get retired or refined.
