# Ground-up rebuild — Items 1/3/5 reply (Items 2/4/6 deferred to follow-up)

## Scope of this reply

Per directive 2026-05-17-1500-ground-up-rebuild-architecture.md + Stan's pre-trigger guidance ("Treat the 1100 reply as INPUT to 1500's Item 1 and Item 5; don't redo the 27-validator categorization; translate old-framework labels"):

**Done this turn:**
- Item 1 (Hebrew Constraint Catalog v1) — built with §7.3-audit-revised scope
- Item 3 (rubric refinements) — both candidates audited; STOP-AND-SURFACE; recommendations surfaced
- Item 5 (sunset plan) — staged plan with gate condition

**Deferred to follow-up `directive` triggers:**
- Item 2 (MVP pipeline build) — requires its own §7.3 pre-build audit on prompt design + integration audit on render→audit chain; not initiated in this turn
- Item 4 (chapter-by-chapter validation status) — requires Phase 1.5 reports + Ps 1 baseline cross-check; partial substrate exists (6 reports from `directive 2402` follow-up)
- Item 6 (cross-corpus port) — downstream of Items 1-5 reaching production

## Item 1 — Hebrew Constraint Catalog v1 (built)

### §7.3 pre-build audit summary (2 parallel Sonnet agents)

Both audits returned **REVISE-SCOPE** with overlapping must-fix on per-constraint format. Combined must-fix items integrated into build:

**Scope additions** (from Audit 1):
- §156 Casus pendens / left-dislocation
- §123–124 Infinitive constructions (absolute + construct)
- §160–162 Negation patterns (אֵין / לֹא / אַל)
- §147 Vocative + extra-clausal elements
- §125 Object marker אֵת + DO
- §132–140 PP governance

**Verdict family extensions** (from both audits):
- Original 5 (BIND / SPLIT / MERGE / VIOLATION-FLAG / NO-EFFECT)
- + JUDGMENT-REQUIRED (constraint detects pattern but verdict needs context — G4 coordinate-vs-subordinate, G6 conditional protasis weight, G11 כִּי recitativum vs causal)
- + INFORM / ADVISORY (constraint provides context, no required change — gapped-verb identification, non-restrictive relative licensing)

**Per-constraint format additions** (mandatory fields):
1. Encoded question (yes/no)
2. Verdict family (extended to 7 categories)
3. **Tier**: HARD (catalog violation auto-overrides LLM draft) vs ADVISORY (catalog flags for editorial queue)
4. **Precedence** (integer 1–9; analogous to M1–M4 ordering)
5. Source reference (Joüon §X.Y or other)
6. **Macula operationalization** (constituent type / role label / frame-arg; or "Macula: none — surface heuristic required")
7. **Status**: DRAFT / VALIDATED / DEPRECATED
8. Diagnostic examples (≥2 positive, ≥2 negative)
9. Edge-case handling

**Catalog-level fields**:
- catalog_version, last_reviewed, open_gaps, composition_rule, bidirectional-test exclusion statement

### Catalog v1 contents

**Files**:
- Master index: [`canon/constraint_catalog_v1.md`](../../canon/constraint_catalog_v1.md) (636 lines; LLM-consumable audit surface; all 26 entries with full format)
- Per-construction sub-files at [`canon/constraints/`](../../canon/constraints/):
  - `relative_clauses.md` (43 lines)
  - `subordinate_clauses.md` (57 lines)
  - `clause_nucleus.md` (49 lines)
  - `particles_and_particles.md` (43 lines)
  - `bound_nominals.md` (26 lines)
  - `bonded_and_formula.md` (48 lines)

**26 constraints v1**:
- **By verdict family**: BIND (19) / SPLIT (1) / JUDGMENT-REQUIRED (3) / INFORM (3)
- **By tier**: HARD (19) / ADVISORY (7)
- **Top-3 precedence** (fire before all others):
  1. `JM13-maqqef-group` — Maqqef-group indivisibility (Layer 1 orthographic floor)
  2. `JM103-proclitic-stranding` — Proclitic line-final stranding
  3. `JM103e-compound-prep-object` — Compound-preposition object stranding

**Constraint ID convention**: JM-section-anchored (e.g., `JM158-restrictive-relative`) with backward-compat G-label noted where applicable. Old-framework labels (M1-M4, J1-J5, Layer 1, §1 forces) translated per Stan-directive intake:
- M1-M4 → catalog entries where they encoded real Hebrew syntactic constraints; producer-style merge-overrides retired
- J1-J5 → mostly retired; J3 speech-act announcement carried forward as audit-mode H5b check
- Layer 1 → catalog members (highest precedence)
- §1 forces → minimal rubric absorbs (bidirectional test universal; cognitive-unity gate dropped per Ps 1 empirical evidence)

**Coverage against directive scope**: all canon §5 H-rules surviving 1100's categorization (H1/H2/H3 partial / H5/H5b/H7/H10/H14/H15/H16/H18) + all 1100 NOT-COVERED (G1-G5, G9) + all Audit 1 scope additions (§156 / §123-124 / §160-162 / §147 / §125 / §132-140).

**5 open gaps documented**:
1. `JM123-inf-abs-predicate` (predicative sub-case) — Macula role assignment not yet confirmed empirically
2. `JM156-general-fronting` — generalized fronted-constituent binding (non-casus-pendens); topicalization role label not confirmed
3. `JM172-coordinate-vs-subordinate` — systematic clause-type-level discrimination
4. `JM160-negation-scope` (scope-distance) — multi-clause negation governing distant predicate
5. `JM125-DO-marker-scope` — heavy multi-token אֵת + NP spread across two lines

All entries carry Status: DRAFT pending corpus-fixture validation in a follow-up directive.

### Item 1 post-build audit — NOT YET RUN

Per directive: "Item 1 (constraint catalog): pre-build audit on catalog scope + organization; post-build audit on coverage gaps". The post-build coverage-gap audit is NOT yet run; recommend dispatching as follow-up `directive` trigger before Item 2 MVP pipeline build consumes the catalog.

## Item 3 — Rubric refinements (BOTH STOP-AND-SURFACE)

### Candidate 1: speech-intro + short particle-led reply/vocative binding

**§7.3 pre-build audit verdict: STOP-AND-SURFACE** (Sonnet agent; 7 findings, 3 must-fix)

Key findings:
1. **The corpus already handles Gen 22:1 correctly per H5b.** The v2/heb rendering of Gen 22:1 already splits frame and reply across lines. If the 8-chapter cross-corpus test showed a merge, that was a TEST-RENDERING deviation, not a corpus gap. The refinement may be solving a problem that does not exist in the corpus.
2. **`הִנֵּנִי` is propositionally complete** — verbless-clause predication (particle + 1cs suffix = "Behold me"). Length is not a merge license per H5b explicit text. There is no syntactic basis for merging it with the speech intro.
3. **H5b's forced-no-merge clause is explicit and its exception list is closed.** Adding a new exception class requires full §7.3 treatment as a new rule, not as a "calibration item."

**Recommended next action for Stan**:
- Confirm whether Gen 22:1 is actually a problem in the v2/heb corpus or only in the 8-chapter test rendering (different question — corpus gap vs test prompt calibration).
- If the test prompt diverges from canonical v2/heb, investigate test prompt calibration (not a rubric change).
- If a genuine merge case exists at a verse other than Gen 22:1, surface that verse with the specific Hebrew text. The refinement can only be evaluated against concrete failing cases.

The narrow sub-question (whether responsory `הִנֵּנִי` / `הִנְנִי` should merge with its speech-intro frame) is worth a separate scoped investigation grounded in corpus evidence — distinguishing from content-initiating `הִנֵּה` constructions (which correctly split per H14).

### Candidate 2: wayyiqtol hendiadys

**§7.3 pre-build audit verdict: STOP-AND-SURFACE** (Sonnet agent; 5 findings, 3 must-fix)

Key findings:
1. **The rule already exists in the canon at H3 line 761.** Canon §5 Rule H3 enumerates exactly this class: "Tight narrative pairs (*וַיָּקָם וַיֵּלֶךְ*, *וַיַּעַן וַיֹּאמֶר*, *וַיָּבֹא וַיֵּשֶׁב*): two wayyiqtol clauses describing tightly-bonded sequential actions in one image — merge under M1 bonded-pair logic." The Gen 22 case is **already covered**. The 8-chapter test's fragmentation indicates the minimal-rubric prompt does not yet include H3's tight-pair exception — the gap is in the prompt/constraint-catalog, not in the canon.
2. **BoFM-precedent revival risk is REAL if implemented as a closed-list mechanical merge.** Canon §1 M1 dormancy codification (line 250) explicitly gates lemma-pair list reactivation behind a context-discrimination protocol that does not yet exist.
3. **Macula IR avoids the BoFM risk entirely.** Bare-second-wayyiqtol-with-no-independent-argument is the discriminating condition. This is a Macula constituent-membership + argument-structure query, not a lemma-pair lookup.

**Recommended next action for Stan** — re-frame Item 3 wayyiqtol-hendiadys not as a new rule but as:
- Encode H3's existing tight-pair exception in the constraint catalog (Item 1) with Macula argument-structure discriminant
- Create `data/syntax-reference/bonded-lemma-pairs.txt` as the missing H3 YAML artifact
- Test against the bare-second-verb corpus population BEFORE any closed-list activation
- For `וַיַּעַן וַיֹּאמֶר + short-reply`: resolve the H3/H5/Item-3-candidate-1 interaction analysis first; write a single unified rule, not three overlapping ones

### Calibration items resolved 2026-05-17 (per directive)

- Doxological NP enumeration (Rev 5:12 seven-fold attribute list): strict minimal rubric got it right — bare-NP enumerations collapse per forward-closure failure. No sub-rule needed. CONFIRMED.

## Item 5 — Sunset plan (staged; gated on Stan-validation)

Per directive: "Once the new pipeline produces book-batch coverage on at least 5 chapters across 3 genres validated by Stan."

### Current gate-status assessment

- **Phase 1.5 reports** (6 chapters, 3 genres, from `directive 2402` follow-up): Gen 5 / Lev 11 / Isa 6 / Prov 10 / Lam 1 / Exo 15. **Not yet Stan-validated** (surfaced in 2402 reply; Stan-review pending).
- **Ps 1 14-ATU baseline** (commit `90d3af55b`): **Stan-validated** (14/14 exact match with manual baseline).
- **Deut 6 partial** (commit `6933d793f`): **Stan-validated** for the 9 verses re-rendered.

**Conclusion**: gate condition NOT yet met. Sunset Stage 1 awaits Stan-validation of Phase 1.5 reports or additional chapter renderings.

### Staged sunset plan

**Stage 0 — Current state** (no change required):
- Legacy validator stack live; producer-style validators continue to emit findings against current baseline
- New pipeline (script + minimal rubric prompt + catalog) is read-only diagnostic
- No corpus mutation from the new pipeline

**Stage 1 — Deprecation marking** (triggered when Stan validates 5 chapters across 3 genres):
- Add `# DEPRECATED 2026-05-XX — superseded by LLM-first pipeline per directive 1500` header comment to each legacy validator file
- Per 1100 retirement table, the 5 PRODUCER + 6 MIXED validators:

| Validator | Retirement | Findings void / restructured |
|---|---|---|
| `validate_parallel_clause_split` | RETIRE production arm; refine to constraint-audit on LLM proposals | 2,051 findings void |
| `validate_blessed_cursed_chain` | RETIRE production arm | TBD count |
| `validate_parallel_series_uniformity` | RETIRE production arm | 5 findings void |
| `validate_genealogy_uniformity` | RETIRE production arm | 0 findings (already clean) |
| `validate_speech_intro_framing` | REFINE to audit-mode H5b check | 603 findings restructured |
| `validate_causal_ki` | SPLIT constraint/production arms | 992 findings restructured |
| `validate_clause_nucleus_split` | SPLIT arms (H15/H16/H18 cluster) | 421 findings restructured |
| `validate_participial_speech_frame` | SPLIT arms | 14 findings restructured |
| `validate_short_orphan_line` | SPLIT arms (REFINE to constraint-mode) | 2,453 findings restructured |
| `validate_short_verse_fronting` | SPLIT arms | 0 findings (already clean) |
| `validate_wayehi_protasis` | SPLIT arms (SPLIT-arm retires; MERGE-arm becomes constraint) | 396 findings restructured |

- Rename retired files: `validate_X_DEPRECATED.py` OR move to `validators/_legacy/`
- Update `validators/.baseline.json` to reflect new finding counts

**Stage 2 — Cascade orchestration swap** (after Stage 1 validates):
- Replace `scripts/apply_validators.py` producer-cascade with audit-cascade calling `scripts/atu_pipeline/run_pipeline.py` (Item 2 deliverable; not yet built)
- `scripts/refresh_book.py` orchestration updated: source → LLM render → constraint audit → editorial review → v2/heb commit
- `build_books.py` unchanged (consumes v2/heb regardless of pipeline)

**Stage 3 — Corpus-wide cleanup** (deferred to separate directive):
- Eventual deletion of `validators/_legacy/`
- Canon §5 H-rules consolidated into constraint catalog (rule-template.md per-corpus-vocabulary form)
- CLAUDE.md reorientation: new pipeline as authoritative; legacy stack documented as historical

### Audit-skippable classification per directive

Item 5 sunset plan = §7.4 audit-skippable (porting and deprecation work, not new construction). Each STAGE landing requires its own per-stage commit hygiene but no adversarial audit gate.

## Items 2/4/6 — Deferred status

### Item 2 — MVP pipeline build

Requires:
- §7.3 pre-build audit on prompt design (`scripts/atu_pipeline/prompts/minimal_rubric_hebrew.md` v0.1)
- §7.3 integration audit on render→audit chain
- 3 scripts to build: `render_atus.py` (Opus 3-pass), `audit_constraints.py` (catalog runner), `run_pipeline.py` (orchestrator)
- Catalog v1 from Item 1 above (DONE) is the audit-stage substrate

Recommended next `directive` trigger: build Item 2 MVP pipeline with the catalog v1 + prompt-design adversarial audit.

### Item 4 — Chapter-by-chapter validation status

Substrate exists:
- Ps 1 14-ATU baseline (Stan-validated, commit `90d3af55b`)
- Deut 6:1-12 (Stan-validated, commit `6933d793f`)
- 6 Phase 1.5 chapters from `directive 2402` (Gen 5 / Lev 11 / Isa 6 / Prov 10 / Lam 1 / Exo 15) — Stan-review pending

For each: verify rendering matches what the v0.2 rubric + catalog v1 would propose. Where they match: confirm and lock. Where they diverge: editorial review surface.

Deferred until Item 2 MVP pipeline build lands (the validation requires the new pipeline to RUN against the chapters).

### Item 6 — Cross-corpus port readiness

Tanakh pipeline must demonstrate end-to-end coverage on Item 4 substrate before BoFM + GNT analog directives are triggered. Out of scope for this turn.

## Per-item disposition

| Item | Status |
|---|---|
| 1 — Hebrew Constraint Catalog v1 | **DONE** — 26 constraints; revised scope per §7.3 audit must-fix; canon/constraint_catalog_v1.md + sub-files committed; post-build coverage-gap audit recommended |
| 2 — MVP pipeline build | **DEFERRED** — requires §7.3 pre-build audit + 3 scripts; next `directive` trigger |
| 3 — Rubric refinements | **STOP-AND-SURFACE both candidates** (speech-intro Gen 22:1 may not be a corpus problem; wayyiqtol-hendiadys is canon H3 line 761 already + Macula-IR path avoids BoFM-precedent revival) |
| 4 — Chapter-by-chapter validation | **DEFERRED** — substrate exists (Ps 1 + Deut 6 + 6 Phase 1.5); requires Item 2 pipeline to run |
| 5 — Sunset plan | **DRAFTED** — staged plan with gate condition; current gate-status NOT YET MET (awaits Stan-validation of Phase 1.5 reports) |
| 6 — Cross-corpus port | **DEFERRED** — downstream of Items 1-5 reaching production |

## Working-tree state surfaced

Pre-existing uncommitted Gen 22 / Ps 23 changes from earlier turns still sitting unstaged. The Item 3 audit found that Gen 22:1 is already correctly split in v2/heb per H5b, which makes those uncommitted changes potentially relevant context for Stan's Item 3 decision (test-rendering deviation vs corpus gap).

## Cost summary

This turn: 4 pre-build audits (Sonnet) + 1 catalog build (Sonnet, ~500K tokens) ≈ ~$1-2 Sonnet spend.

Phase 2 MVP pipeline build (next directive): pipeline build itself is small; production rendering at scale uses Opus 3-pass per chapter (per directive's settled production protocol).
