# Ground-up rebuild — LLM-first ATU pipeline + constraint catalog

## Status of prior 2026-05-17-1100 directive

The rules-audit + constraint-catalog directive (`2026-05-17-1100`) is **SUPERSEDED by this one.** That directive assumed a modification path (audit each validator, retire/refine producers, build missing constraints into the existing stack). The empirical evidence from the 2026-05-17 cross-corpus experiments — 8 chapters across 3 corpora, Stan's hand-verification confirming the minimal rubric produces "clearly superior" renderings "100% aligned with how I see the line breaks" — supports a cleaner approach: build the architecture-method-aligned pipeline from the ground up.

Item 2 of `2026-05-17-1100` (enumerate Hebrew syntactic constraints from Joüon-Muraoka) is the only item that survives. It expands into the full Hebrew Constraint Catalog as a primary artifact under this directive.

## Context — what was empirically established 2026-05-17

The minimal rubric:
- Bidirectional test (forward grammatical closure + backward referential self-containment)
- Restrictive relative clause binding
- Small set of language-specific syntactic constraints (Hebrew gapped-verb tolerance; speech-frame binding; discourse-particle binding)
- NO cognitive-unity gate
- NO parallelism class adjudication
- NO genre anchors as primary licenses
- Default KEEP-AS-IS unless rule affirmatively fires

Empirical evidence base:
- Ps 1: 14/14 exact match with Stan's manual baseline
- 8-chapter cross-genre test (Gen 22, Lev 11, Isa 53, Jonah 1, Mt 28, Eph 1, Rev 5, Enos): every chapter produced "clearly superior" results to source rendering on Stan's hand-verification

Calibration items surfaced (for incorporation, not rubric replacement):
- Speech-intro + short particle-led reply/vocative binding (Gen 22:1 inconsistency)
- Doxological NP enumeration handling (Rev 5:12 seven-fold attribute list)
- Continuative-vs-restrictive `ἐν ᾧ` distinction (Eph 1)
- Wayyiqtol hendiadys handling (`וַיָּקָם וַיֵּלֶךְ` in Gen 22)

## Architecture to build

**Pipeline (corpus-agnostic; this directive scopes the Hebrew/Tanakh instance):**

```
Source text (with verse markers, current line breaks if any)
  ↓
LLM with minimal-rubric prompt → proposes ATU-segmented rendering
  ↓
Constraint-catalog audit → grammatical yes/no questions; flag violations
  ↓
Editorial review surface → Stan adjudicates conflicts
  ↓
Final ATU rendering committed to text-files/v2/heb/
```

**KEEP from existing infrastructure:**
- Data layer: Macula constituent trees, TAHOT alignment, source text files, Strong's anchoring, render-pipeline file structure under `data/text-files/`
- Manually-validated renderings (Ps 1 baseline, Deut 6 partial — wherever Stan has hand-edited)
- `scripts/audit_rendered_output.py` Phase 2 build — extends into the new pipeline's audit stage
- Per-chapter book-batch execution harness from directive 2402

**DECLARE LEGACY (stop work, sunset after new pipeline supersedes):**
- `validators/colometry/` — producer-style validators (parallel clause split, etc.)
- `validators/syntax/` — producer-style validators (causal_ki, hadassah constructs, etc.)
- Cascade orchestration scripts that ran validators-as-producers
- `validate_rendering.py` if it depends on producer-mode logic (verify; some logic may be salvageable)

**REPLACE:**
- Pipeline orchestration — was designed around validator-first execution; new pipeline is LLM-first.

## Items

### Item 1 — Hebrew Constraint Catalog (primary new artifact)

Build a comprehensive constraint catalog for Biblical Hebrew syntactic well-formedness, organized as yes/no grammatical questions applicable to ATU boundary decisions.

Source authorities (sequence):
1. **Joüon-Muraoka** *A Grammar of Biblical Hebrew* (primary)
   - §158 Relative clauses (restrictive vs. non-restrictive binding)
   - §159 Subordinate clauses
   - §170–177 Coordination (especially `וְ` coordinate vs. subordinate)
   - §150 Verbless clauses (subject-predicate juxtaposition)
   - §121 Participial constructions
   - §174 Gapping
   - §155 Construct chains and bare-governor indivisibility
   - §164–169 Conditional structures (legal-casuistic, hypothetical, real)
2. **GKC (Gesenius-Kautzsch-Cowley)** — secondary cross-reference
3. **Waltke-O'Connor** *An Introduction to Biblical Hebrew Syntax* — modern syntactic framing
4. Existing Tanakh-Claude work captured in `canon/` where it documents real syntactic phenomena

Constraint format (yes/no grammatical questions):
- "Is this break inside a construct chain (bare governor + genitive)?" → if yes, MERGE
- "Is this `אֲשֶׁר`-clause restrictive (head not uniquely identified without it)?" → if yes, BIND
- "Is this `וְ` coordinating two finite verbs with the same subject?" → if yes, candidate SPLIT (each may be its own ATU)
- "Is this colon's finite verb gapped from the immediately preceding parallel colon?" → if yes, COUNT AS CLOSED
- "Is this discourse particle (`לָכֵן`, `וְעַתָּה`, `הִנֵּה`, etc.) bare on its line?" → if yes, MERGE-NEXT
- (and so on)

Each constraint:
- Encoded question (yes/no)
- Verdict family (BIND / SPLIT / MERGE / VIOLATION-FLAG / NO-EFFECT)
- Source reference (Joüon §X.Y, or other)
- Diagnostic examples (≥2 positive, ≥2 negative)
- Edge-case handling

Deliverable: `canon/constraint_catalog_v1.md` — single authoritative document. Implementation comes next.

### Item 2 — MVP pipeline build

Build the new pipeline as scripts under `scripts/atu_pipeline/` (new directory):

1. **`scripts/atu_pipeline/render_atus.py`** — wraps an LLM call using the minimal-rubric prompt; outputs ATU-segmented text per chapter. Input: source text file. Output: proposed rendering file.
2. **`scripts/atu_pipeline/audit_constraints.py`** — runs the constraint catalog against a proposed rendering; produces violation report. Reuses the audit-mode logic from `scripts/audit_rendered_output.py`.
3. **`scripts/atu_pipeline/run_pipeline.py`** — orchestrates render → audit → report. Output: proposed rendering + violation report for editorial review.

The minimal-rubric prompt itself: distilled from the 2026-05-17 experiments. Single canonical prompt under `scripts/atu_pipeline/prompts/minimal_rubric_hebrew.md`.

§7.3 audit triggers apply per existing precedent (pre-build adversarial audit on prompt design and constraint catalog before integration).

### Item 3 — Rubric refinements from 2026-05-17 calibration items

Incorporate into the minimal rubric (v0.2):

- **Speech-intro + short particle-led reply/vocative**: Unified discourse-particle binding extension. `וַיֹּאמֶר X` + short particle-led unit (vocative call, `הִנֵּנִי`, etc.) = ONE ATU.
- **Wayyiqtol hendiadys**: candidate carve-out for fixed motion-onset pairs (`וַיָּקָם וַיֵּלֶךְ`, `וַיַּשְׁכֵּם וַ֯`) — pre-decision Stan's call before integration.
- Other items per cross-corpus evidence as they surface.

### Item 4 — Port already-validated renderings forward

Identify chapters where Stan has hand-edited renderings (Ps 1, Deut 6 partial). For each:
- Verify the existing rendering matches what the new pipeline would propose under the v0.2 rubric
- Where they match: confirm and lock
- Where they diverge: editorial review surface

### Item 5 — Sunset plan for legacy validator stacks

Once the new pipeline produces book-batch coverage on at least 5 chapters across 3 genres validated by Stan:

1. Mark legacy validator scripts deprecated (header comment + `_DEPRECATED` suffix on filename OR move to `validators/_legacy/`)
2. Update CLAUDE.md / canon to reference new pipeline as authoritative
3. Cascade orchestration: replace producer-cascade with audit-cascade
4. Eventual deletion deferred to corpus-wide cleanup directive (not this one)

### Item 6 — Cross-corpus port (separate parallel directives)

After Tanakh demonstrates end-to-end pipeline:
- BoFM analogous directive: build EME English Constraint Catalog (Cawdrey, Skousen *Critical Text*, EME grammar references), MVP pipeline, sunset BoFM legacy validators
- GNT analogous directive: build Koine Greek Constraint Catalog (Smyth, Wallace, Robertson, Funk), MVP pipeline, sunset GNT legacy validators

The architecture is corpus-agnostic; each corpus needs its own grammatically-grounded constraint catalog.

## Out of scope (explicitly)

- Rebuilding the data layer (Macula trees, TAHOT alignment, source files) — KEEP
- Re-doing already-validated renderings (Ps 1 baseline) — KEEP, audit against new pipeline only as cross-check
- Adding to the v0.2 rubric without empirical evidence — resist new-rule reflex per [feedback_three_anti_default_factors] / [feedback_minimal_rubric_validated]
- Auditing every legacy validator individually — opportunistic salvage only

## Reporting

Reply at `directives/replies/2026-05-17-1500-ground-up-rebuild-architecture.md` with:

- Item 1: constraint catalog draft (v1, may be large — split into sub-files if needed)
- Item 2: MVP pipeline scripts + adversarial audit results
- Item 3: rubric v0.2 with incorporated calibration items
- Item 4: chapter-by-chapter validation status against new pipeline
- Item 5: deprecation plan with concrete file list
- Item 6: cross-corpus port readiness assessment

## Expected scope

This is a substantial directive. Realistic timeline: 3–5 days of Tanakh-Claude work for Items 1–3; Items 4–5 follow once Items 1–3 land. Item 6 is downstream.

Cost: ~$15–30 in Sonnet spend across constraint catalog construction, pre-build adversarial audits, MVP integration tests.

## Audit triggers

This directive is large enough that each item warrants its own §7.3 audit triggers:
- Item 1 (constraint catalog): pre-build audit on catalog scope + organization; post-build audit on coverage gaps
- Item 2 (MVP pipeline): pre-build audit on prompt design; integration audit on render→audit chain
- Item 3 (rubric v0.2): pre-build audit on each refinement candidate before integration
- Items 4–5: audit-skippable per §7.4 (porting and deprecation, not new construction)

## What this realigns

The fundamental claim: **the architecture going forward IS what the method always actually said.** Cognitive ATU identification (LLM + minimal rubric) is the primary work. Syntactic rules (constraint catalog) audit candidates. Parallelism is off-axis. Producer-style validators are sunset. The minimal rubric was empirically validated as load-bearing on 2026-05-17 across 8 chapters / 3 corpora / 3 languages.

This is the rebuild. The legacy stack served its purpose; this directive replaces it.
