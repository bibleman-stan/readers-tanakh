# Audit-layer prototype — Phase 1 reply — STOP-AND-SURFACE

## Phase 1 dispatch summary

Per directive item 1: dispatched 2 parallel Opus agents (E + F) against the proposed `audit_rendered_output.py` design + prompt template. Each agent received the directive context, three validated experiments (Deut 6 `6933d793f` + Ps 1 `39f39d886` committed; Gen 22 vault-side), the extended bidirectional ATU test rubric, and the proposed Sonnet prompt template. Wall-time: ~3–5 min per agent.

Per directive item 3: independent dispatch (no cross-agent context); Opus-tier per `feedback_model_selection_frugality` (adversarial audit = structure-generation work).

Per directive item 2: **audit verdict CONTAINS MUST-FIX FINDINGS — STOP-AND-SURFACE.** Phase 2 build NOT initiated.

## Cross-agent agreement (HIGH-CONFIDENCE findings — both agents independently flagged)

### HIGH-CONF Must-Fix #1 — Audit-layer authority discipline conflicts with canon §1 line 151

Both agents independently identified that the audit-layer's Phase 4 auto-apply path violates canon §1's explicit constraint at line 151:

> "**Status: informational diagnostic, NOT precedence override.**" — bidirectional atomic-thought test (canon §1.1)

Per `feedback_bidirectional_is_diagnostic_not_override` (Stan-codified 2026-05-13, citing gnt-reader precedent): the bidirectional ATU test surfaces candidates for editorial review but does NOT adjudicate between competing rules or auto-fire validators.

The 2402 directive proposes (Phase 4) to use audit-layer verdicts to MUTATE the corpus — that flips the canon-codified diagnostic-only constraint into apply-driver. The §7.3 trigger #10 (discipline-shifting addition) requires the canon revision to land BEFORE the apparatus that operationalizes it.

**Agent F**: "Phase 4 mentions 'unanimous-high-confidence cases' — meaning N-parallel runs — but Phase 1 design specifies single-pass. The two are operationally incompatible."

### HIGH-CONF Must-Fix #2 — No adjudication hierarchy between audit-layer and existing validators

Both agents identified the cross-validator collision risk:

- 24 existing validators emit STRONG-MERGE-CANDIDATE / STRONG-SPLIT-CANDIDATE at the line level
- The audit-layer would emit its own MERGE/SPLIT verdicts on the same v2/heb files
- The directive does not declare who wins when verdicts collide

Concrete collision example (Agent F): Ps 1:1 audit-merged the synonymous tricolon to one ATU, but `validate_parallel_clause_split.py` (Hpar STRONG-SPLIT) is structurally designed to fire on exactly that shape. Post-merge, Hpar's STRONG-SPLIT would recommend the inverse, putting the line into permanent contradiction.

### HIGH-CONF Should-Revise — Genre under-coverage in evidence base

Both agents flagged that three validated experiments (Deut 6 prose, Gen 22 narrative+dialogue, Ps 1 lyric) cover ~3 genre classes; the proposed first-tier books (Genesis + Isaiah + Psalms) span ~7 distinct genres (legal-casuistic, genealogical formulas, prophetic oracles, wisdom distichs, qinah laments, acrostic structures, embedded poetry).

Agent E proposes a Phase 1.5 six-chapter genre-coverage pre-flight (Gen 5, Lev 11, Isa 6, Prov 10, Lam 1, Exo 15) before Phase 2 corpus-cascade.

## Agent E findings (prompt fragility focus)

10 findings: 3 must-fix, 6 should-revise, 1 nice-to-have. **Phase 1 verdict: REVISE-PROMPT.**

### Must-fix

**E-F1 — Verbless-clause silence in "forward grammatical closure"**:
The rubric defines forward closure as "subj + verb + obligatory complements." Hebrew has no overt copula in present-tense verbless clauses (the dominant clause type in Pss/Prov/Wisdom). Sonnet may interpret unpredictably across chapters.
*Proposed revision*: explicit clause that Hebrew "verb" includes (a) finite verbs with morphologically-encoded subject, (b) verbless/nominal-predicate juxtapositions, (c) participial predications, (d) exclamatory/declarative particle-headed clauses (אַשְׁרֵי, הִנֵּה, הָבָה).

**E-F2 — Backward referential self-containment undefined for pro-drop + long-range antecedents**:
Hebrew finite verbs encode subject via inflection. Implicit subject from morphology in wayyiqtol chains can persist 20+ verses (David thread in 1 Sam 17). Without guidance Sonnet either demands overt subject (over-MERGE) or accepts any morphology-recoverable (under-MERGE).
*Proposed revision*: backward containment satisfied when referents are (a) overtly present, (b) recoverable from finite-verb morphology, OR (c) the same discourse-active subject as the immediately prior ATU. Fails only if new subject intervenes.

**E-F5 — Genealogical formulas + legal lists not addressed**:
Genesis is first-tier; Gen 5/10/11/36 are pure genealogical formula. The cognitive-unity gate naively applied says "one member = one cognitive unit = one ATU" and merges 4 lines into 1 — destroying chant-cadence. Same problem in Lev 11 dietary, Deut 27 curse list, Num 7 tribal offerings.
*Proposed revision*: explicit genre-anchor for formulaic structures (J1 formula-integrity at per-member level; cross-member boundary preserved as formula cadence).

### Should-revise (selected)

**E-F3** — Synthetic-parallelism "judgment call" → MERGE bias amplified by genre prior (60-75% over-breaking framing seeds Sonnet's prior). Wisdom genres (Prov 10-22 antithetic distichs) would be mass-merged.
**E-F7** — "Be honest" instruction insufficient against agreeableness bias; verdict tokens (3 merge-direction + 1 keep) are asymmetric.
**E-F8** — No confidence stratification (HIGH/MED/LOW) for triage; backlog problem at corpus scale.
**E-F9** — Three-experiment evidence base under-samples genre space.

## Agent F findings (cross-validator + discipline focus)

7 findings: 3 must-fix, 2 should-revise, 2 nice-to-have. **Phase 1 verdict: REVISE-DESIGN — STOP-AND-SURFACE.**

### Must-fix

**F-F1 — No declared adjudication hierarchy** (HIGH-CONF; see cross-agent above):
*Proposed revision*: (a) audit-layer verdicts are REVIEW-REQUIRED severity by default, never STRONG; (b) where audit-MERGE conflicts with a STRONG-SPLIT validator, the validator wins unless audit verdict is hand-promoted by Stan; (c) the report must FLAG each line where audit verdict differs from current validator-finding state.

**F-F2 — Cascade baseline regression on `.baseline.json` mathematically certain on Phase 4 auto-apply, not budgeted**:
Merging coordinate-series lines into one cola produces NEW shapes that validators (Hpar STRONG-SPLIT on synonymous bicola; M4 short-orphan-line on residual orphans; H18 H7 reclassification) will fire on. Pre-commit baseline-check exits 1 and blocks commit.
*Proposed revision*: pre-cascade dry-run simulating each proposed merge against the validator suite + per-chapter "validator-collision count" header; Phase 4 auto-apply gated on `.baseline.json` update being explicitly authorized by Stan, not absorbed silently.

**F-F3 — Audit-layer is Layer 4 in all but name; canon §7.3 trigger #10 requires canon revision BEFORE Phase 2** (HIGH-CONF; see cross-agent above):
*Proposed revision*: STOP Phase 2 until Stan authors (or directs Claude to draft) a canon §1.1 amendment that explicitly: (a) defines audit-layer as Layer 4 (passage-level); (b) restates whether layer's verdicts are diagnostic / advisory / apply-eligible; (c) defines the hierarchy in F-F1; (d) defines §7.4 adoption threshold for audit-layer verdicts (analog to the existing ≥80% TP threshold for validator STRONG promotion).

### Should-revise

**F-F4** — Verdict-source auditability broken under §7 change-protocol (no baseline file analog, no rule-citation, no reproducibility). Sonnet is non-deterministic without temperature 0 + fixed prompt hash + per-call recording.
**F-F5** — Single-pass Sonnet for auto-apply is a §7-discipline regression vs the §7.3 audit gate.

## Phase 1 verdict — STOP-AND-SURFACE

Per directive Item 2: "If audit clears (no must-fix findings): proceed to Phase 2. **If audit surfaces must-fix findings: STOP and surface for Stan-review per the 2203/2400 STOP-gate protocol.**"

Both agents returned must-fix findings. Cross-agent HIGH-CONFIDENCE findings:
1. Canon §1 line 151 conflict with audit-layer authority (HIGH-CONF, 2 agents)
2. No adjudication hierarchy with existing validators (HIGH-CONF, 2 agents)

**Phase 2 NOT initiated.** No `scripts/audit_rendered_output.py` built. No Phase 3 execution attempted. Stan-review of the audit report is the next gate.

## Specific code changes proposed for Stan-review

Per directive Item 5 (per-revision proposals; do NOT auto-revise — Stan reviews):

### Proposed canon §1.1 amendment (anticipated; not authored)

The audit-layer needs to be declared explicitly in canon. Suggested amendment scope:

- Define "audit-layer" / "Layer 4" — passage-level LLM-driven editorial-review surface above point-rule validators
- State verdicts default to REVIEW-REQUIRED (advisory); STRONG-equivalent severity requires §7.4-style ≥80% TP threshold demonstrated
- Hierarchy: when audit-verdict conflicts with STRONG-tagged validator finding, validator wins absent explicit Stan-hand-promotion
- Reproducibility constraint: audit-layer dispatch records temperature, model-ID, prompt-hash; non-deterministic verdicts surface as AMBIGUOUS

### Proposed prompt-template revisions (anticipated; not applied)

If Stan authorizes proceeding after canon work:

- Add explicit Hebrew verbless-clause / pro-drop / discourse-referent handling (E-F1 + E-F2)
- Add genre-anchor section for genealogical formulas + legal lists + acrostic + qinah (E-F5)
- Remove the "60-75% over-breaking" framing from any Sonnet preamble (E-F3 / E-F7)
- Add HIGH/MED/LOW confidence stratification per verdict (E-F8)
- Pre-flight Phase 1.5: six-chapter genre-coverage audit (Gen 5 genealogy, Lev 11 legal list, Isa 6 oracle+narrative, Prov 10 wisdom distichs, Lam 1 qinah acrostic, Exo 15 embedded poetry) BEFORE Phase 2 corpus-cascade (E-F9)

### Proposed cross-validator discipline (anticipated; not applied)

- Audit-layer report MUST include a "validator-collision count" header per chapter
- For each line with collision, include both verdicts (audit's + validator's) + the canon-rule each cites
- Phase 4 auto-apply requires no-collision check against existing STRONG findings on that line

## Per-item disposition

| Item | Status |
|---|---|
| 1 — Dispatch 2 parallel Opus audits | DONE |
| 2 — If audit clears: proceed Phase 2; if must-fix: STOP-AND-SURFACE | **STOP-AND-SURFACE** (must-fix findings present from both agents) |
| 3 — Phase 2 build | BLOCKED on Phase 1 verdict |
| 4 — Prompt template | UNCHANGED (Phase 2 not entered) |
| 5 — Output schema | UNCHANGED (Phase 2 not entered) |
| 6 — Read-only default | N/A (Phase 2 not entered) |
| 7 — Execution order | BLOCKED (Phase 3 requires Phase 2) |
| 8 — Per-chapter pass | BLOCKED |
| 9 — Cost estimate | unchanged from directive ($15-30 Genesis+Isaiah+Psalms; modest) |
| 10 — Progress log | N/A |
| Phase 4 anticipatory items | BLOCKED on Phase 1 canon work |

## Cost note

4 Opus audits across both 2400 and 2402 directives so far this turn. Modest absolute cost. The Phase 1 audit cost is sunk; if Stan re-authorizes after revisions, the next round can use Sonnet-tier for the audit-of-revised-prompt (per `feedback_model_selection_frugality` — checking against a defined rubric is per-instance judgment, not novel structure-generation, so Sonnet suffices).

## Cross-corpus dimension

Per Agent F-F6: cross-corpus port from day one is premature. The directive flags `atu_method/audit_rendering/` shared-module as the eventual home; recommend baking Tanakh-side first, then porting after Phase 3 produces ≥3 genre-clean reports + Stan reviews calibration sample. Match the pattern of `validators/_shared/macula_constituents.py` — proven Tanakh-side first.

## Relationship to 2401 (companion directive)

The 2401 coordinate-series over-breaking diagnostic (reply also landed this turn) confirmed Stan's vault-side hypothesis on coordinate-series fragmentation (69% over-broken rate on stratified 100-case sample). 2401's data ARE a subset of what 2402's audit-layer would surface at corpus scale.

If Stan authorizes 2402 after canon work + prompt revisions, 2402's reports would supersede the standalone 2401 intervention options (A-E) by providing the same data via a unified passage-level audit apparatus.

If Stan declines 2402 or defers indefinitely, the 2401 options A-E remain on the table as independent intervention paths.

## Surfaced for Stan-decision

The audit recommends Stan author (or direct Claude to draft via follow-up directive) the canon §1.1 amendment FIRST, then re-issue the 2402 directive with:
- Phase 1 revised-prompt re-audit (Sonnet-tier sufficient)
- Phase 1.5 six-chapter genre-coverage pre-flight
- Explicit audit-vs-validator hierarchy declared
- Pre-cascade dry-run + collision-count discipline baked in
- Confidence stratification + N-of-M unanimity for any auto-apply path

OR: Stan declines the audit-layer apparatus entirely (Option E from 2401 — defer pending further investigation) and addresses coordinate-series over-breaking via standalone Option A-D from 2401.

OR: Stan directs Claude to revise the prompt template per the must-fix findings + re-dispatch Phase 1 within this directive's scope (deviation from STOP-gate protocol; requires explicit Stan-override).

Stopping at recommendation step per directive Item 2 + 2203/2400 STOP-gate precedent.
