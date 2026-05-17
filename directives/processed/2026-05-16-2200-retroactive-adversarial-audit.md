# Retroactive adversarial audit — Gaps 1 + 3 validators

## Context

The prior directive `2026-05-16-1500-three-gaps-and-scholarship.md` flagged Items 1 (SOLEMNITY_PREFIXES build) and 3 (LIST_FORMULA_PEERS build) as tripping §7.3 trigger #1 (new named rule / sub-clause / category) AND trigger #2 (closed-list-based rule), requiring **≥2 parallel adversarial agents BEFORE non-trivial implementation** per CLAUDE.md adversarial-audit discipline.

The reply at `directives/replies/2026-05-16-1500-three-gaps-and-scholarship.md` self-surfaced that the discipline was NOT formally honored — corpus pre-flight (393-instance morphology scan) + spot-check (108-finding verification) was substituted. This is empirical, but structurally different from adversarial audit: pre-flight CONFIRMS "does my design fire on the cases I designed for"; adversarial PROBES "what FP classes / corner cases / cross-rule interactions did I MISS."

This directive retroactively dispatches the missing adversarial audit. **The builds stand unless this audit surfaces something specific.** Frame the agents accordingly — they are looking for genuine flaws, not seeking to confirm the existing design.

## Items

1. **Dispatch 2 parallel Sonnet agents against `validators/colometry/validate_speech_intro_framing.py`** (post-SOLEMNITY_PREFIXES extension, commit `c28cdf1c5`). Each agent receives:
   - The validator file (post-extension)
   - The §5 H-rule canon entries for the affected rules (prophetic-formula introductions; SOLEMNITY_PREFIXES specifically)
   - The 108-finding pre-flight + spot-check results from the prior reply
   - The 4 morphology-variation classes Tanakh-Claude already surfaced (compound divine titles, article-prefixed forms, human-speaker uses, non-formula *כה*)

   And probes for: **FP classes** the trigger guards miss (non-formula uses outside the *תאמר* / *תברכו* / comparative *יהיה* set already caught); **corner cases** (defective spellings, Aramaic interludes, post-exilic formula variants, parenthetical/quoted formulas in narrative); **cross-rule interactions** with H5 (same default), H7 (Tetragrammaton), H14 (vocative clusters); **parser-shape assumptions** (does the build assume TAHOT proper-noun tagging is always present? what about chapters where TAHOT coverage is partial?); **maqqef edge cases** the normalizer might miss.

2. **Dispatch 2 parallel Sonnet agents against `validators/colometry/validate_list_formula_uniformity.py`** (new validator, commit `c28cdf1c5`). Each agent receives:
   - The validator file
   - The §5 H-rule canon entry for LIST_FORMULA_PEERS (`ארור` / `ברוך` / `אשרי`)
   - The Deut 27 / Deut 28 / Ps 144 / 2 Chr 9 pre-build pre-flight cases
   - The verse-level consecutive-series detection logic

   And probes for: **FP classes** (lexeme uses outside list-formula contexts — non-curse `ארור`, non-blessing `ברוך`, non-beatitude `אשרי`); **corner cases** (vav-prefix variants, defective spellings, nested list-formulas, amen-response interruptions of a series, vocative-adjacent uses); **series-detection edge cases** (what if a series is interrupted by a non-formula verse? what if `אשרי` is mixed with `ברוך`?); **cross-rule interactions** with H11 (parallelism) and H17 (genealogy uniformity, since this was forked from genealogy).

3. **Dispatch protocol per agent:** independent dispatch (no cross-agent context); Sonnet-tier per `feedback_model_selection_frugality`; ~4-8 minute wall-time per agent acceptable; total 4 audits across both validators.

4. **Compile findings** in the reply:
   - Per-validator, per-agent findings list
   - Cross-agent agreement (which issues both agents independently flagged — high-confidence findings vs single-agent findings)
   - Severity classification per finding: **must-fix** (validator produces incorrect dispositions on real corpus cases) / **nice-to-have** (edge-case robustness) / **non-issue** (agent flagged but on inspection the design handles it)

5. **Recommendation per validator: stand / revise / retire.** Default is **stand** unless findings cross severity threshold. If revision recommended: surface specific code changes proposed for Stan-review; **do NOT auto-revise validators based on audit findings**. Audit output is diagnostic; revision decisions are Stan's.

## Reporting

Reply at `directives/replies/2026-05-16-2200-retroactive-adversarial-audit.md`:
- Per-validator audit findings (full enumeration, not summary)
- Cross-agent agreement table
- Per-finding severity classification with reasoning
- Stand / revise / retire recommendation per validator
- If revision recommended: specific code changes proposed for Stan-review

If findings cross severity threshold for revision: STOP at the recommendation step. Do NOT implement revisions. Stan reviews the audit report + decides whether to authorize revision via a follow-on directive.

## Audit triggers

This directive IS an audit; no separate audit-triggers fire on the audit itself. Audit-skippable per §7.4 (audit-of-the-audit recursion stops here).

## Cost note

4 Sonnet audits (2 per validator × 2 validators). Per `feedback_model_selection_frugality` Sonnet is the right tier for adversarial probing of structured rule designs. Total cost: modest — a few hundred Sonnet calls.
