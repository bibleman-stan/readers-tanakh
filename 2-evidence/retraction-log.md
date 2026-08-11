# Retraction-Precedent Log — readers-tanakh

Per [`atu-method/4-process/retraction-log-protocol.md`](../atu-method/4-process/retraction-log-protocol.md).
Append-only; chronological. When 3 retractions share the same factor AND
sub-pattern, the sub-pattern is promoted to
[`atu-method/memories/feedback_three_anti_default_factors.md`](../atu-method/memories/feedback_three_anti_default_factors.md)
and [`atu-method/memories/feedback_rule_proposal_gates.md`](../atu-method/memories/feedback_rule_proposal_gates.md).

Inaugural entries seeded 2026-05-17 from the methodology-shift retrospective.
Seeding pass is audit-skippable per change-protocol §7.4 (codifies
already-completed retractions; no new claims asserted).

---

## Retractions

### 2026-05-17 — Cognitive-unity gate retracted
- **Factor:** structural
- **Sub-pattern:** rule that was patching architecture-method mismatch rather than closing a real cognitive gap
- **What was retracted:** the "cognitive-unity gate" extension to the bidirectional test for parallel poetic cola
- **What surfaced it:** empirical experiment 2026-05-17 (pure LLM with vs without cognitive-unity gate on Ps 1 → identical output; gate was empirically inert)
- **Reference:** atu-method commit `d2972dc` (toolset-architecture.md retraction)

### 2026-05-17 — "Sonnet for prose, Opus for poetry" mixed-tier framing retracted
- **Factor:** C
- **Sub-pattern:** cost-optimization-overweighted-vs-quality-evidence (failure to fully test premium tier before recommending tier mix)
- **What was retracted:** the mixed-tier production recommendation (Sonnet 3-pass for prose, Opus 3-pass for poetry)
- **What surfaced it:** full cross-tier × cross-genre matrix 2026-05-17 (Opus 3-pass: 94% prose / 100% poetic unanimous accuracy; Sonnet: 60–81%)
- **Reference:** atu-method commit `75a4de5` (production tier specification: Opus 3-pass universal)

### 2026-05-17 — v0.2 prompt direction retracted
- **Factor:** B
- **Sub-pattern:** "more elaboration assumed = more quality" (new-rule-reflex variant)
- **What was retracted:** the assumption that adding few-shot examples + failure-mode warnings to the minimal-rubric prompt would improve quality
- **What surfaced it:** A/B test 2026-05-17 (Sonnet v0.1 81% → Sonnet v0.2 70% baseline match; over-correction on Failure Mode A warnings)
- **Reference:** empirical study results (no commit; observation captured in `feedback_production_tier_empirical.md`)

### 2026-05-17 — Four-leg architecture / J1-J5 / M1-M4 framework superseded
- **Factor:** structural
- **Sub-pattern:** whole-framework supersession
- **What was retracted:** the four-leg toolset partitioning; J1-J5 structural justifications; M1-M4 merge-overrides; N=2/N=3+ adjudication; "three forces" (generative/subtractive/diagnostic); Layer 1/Layer 3 stack framing
- **What surfaced it:** methodology realignment 2026-05-17 — the cognitive-first three-stage pipeline (LLM identification → constraint catalog audit → editorial review) supersedes the prior framework
- **Reference:** atu-method docs ground-up rewrite at `f6e834a` and `82e20b8`; readers-tanakh CLAUDE.md trim `31c040bb8`

### 2026-05-17 — Validator-stack-as-producer architecture retracted
- **Factor:** structural
- **Sub-pattern:** "rules that GENERATE rendering vs rules that AUDIT proposed rendering" — producer-style framing dressed as constraints
- **What was retracted:** the validator-stack-as-producer architecture (5-machinery/validators GENERATE ATU rendering decisions)
- **What surfaced it:** architecture-method alignment audit — producer 5-machinery/validators don't match the method's claim that "rules constrain, not create"
- **Reference:** directive `2026-05-17-1500-ground-up-rebuild-architecture.md`; atu-method memories cascade `c9ab999`
