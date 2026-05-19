# 1500 Item 2 follow-up — MVP pipeline build

## Trigger context

Stan triggered Item 2 build via the Item 3 NO-INCORPORATE + Item 2 GO message (2026-05-17 mid-afternoon). Canonical artifacts pulled from `atu-method` at SHA `2992b10`:
- `atu-method/docs/prompts/minimal_rubric_hebrew.md` → copied to `scripts/atu_pipeline/prompts/minimal_rubric_hebrew.md` (unchanged per Stan's "do NOT reinvent the prompt")
- `atu-method/docs/editorial-review-protocol.md` → consumed as Stage-3 output spec

Item 3 decisions logged (both NO-INCORPORATE confirming audit recommendations) — no canon §5 changes; the 1500 reply update is in this follow-up's context section.

Working-tree diff Stan asked me to surface: **GONE** — the Gen 22 / Ps 23 changes that were uncommitted earlier in the day were lost during pull/rebase/stash cycles. The Item 3 audit established that current HEAD `genesis-22.txt` already has the H5b-correct split at Gen 22:1, so the methodologically-correct state is what's committed. Whatever those uncommitted changes were either moved toward an incorrect merge (loss methodology-correct) or were vault-side intentional edits that need re-derivation. Detail in the prior message; no recovery path identified.

## §7.3 pre-build audit summary

Per directive Item 2 audit triggers: dispatched ≥2 parallel Sonnet adversarial agents BEFORE any script build.

### Audit α — Prompt design

7 findings, 1 must-fix, 5 should-revise, 1 non-issue. **Verdict: REVISE-PROMPT**.

**Must-fix Finding 7**: Aramaic interludes (Dan 2:4b–7:28; Ezra 4:8–6:18, 7:12–26) need BAIL behavior — the Hebrew minimal-rubric prompt cannot be silently applied to Aramaic.

**Should-revise findings** 2–6: casuistic-protasis scope expansion / genealogy formula coverage / acrostic letter-heading handling / Proverbs antithetic distich diagnostic / long-chapter chunking.

**Resolution path applied**: per Stan's "do NOT reinvent the prompt" directive, the canonical prompt at `scripts/atu_pipeline/prompts/minimal_rubric_hebrew.md` was kept UNCHANGED. Audit revisions integrated at SCRIPT level instead:
- Aramaic BAIL → `run_pipeline.py` pre-flight (ARAMAIC_RANGES dict; explicit BAIL marker; exit 0 without dispatch)
- Long-chapter chunking → `render_atus.py` (`--chunk-size` default 40 verses; auto-shards chapters > threshold with sequential chunks)
- Findings 2–5 (genre coverage gaps) deferred to future canonical-prompt revision directive; LLM general Hebrew-syntax knowledge handles them at lower confidence in v1

### Audit β — Script architecture + integration risks

8 findings, 4 must-fix, 3 should-revise, 1 non-issue (clarification). **Verdict: REVISE-ARCHITECTURE**.

**Must-fix Finding 1**: Line-alignment problem when 3 passes propose different line counts. **Resolution**: agreement scoring at VERSE granularity (whitespace-normalized exact-match of full verse rendering) — implemented in `render_atus.py:score_agreement()`.

**Must-fix Finding 3**: HARD/auto-override contradiction between catalog and editorial-review-protocol. **Resolution**: dropped HARD auto-override from v1 entirely. All constraint violations surface to editorial review per `editorial-review-protocol.md` line 138. HARD/ADVISORY tier informs report formatting (precedence ordering) only; never auto-corrects. Implemented in `audit_constraints.py` (3-way verdict taxonomy: CONFLICT / CORROBORATE / ADVISORY; no auto-override code path).

**Must-fix Finding 4**: Macula operationalization aspirational for ~40% of catalog entries; building `audit_constraints.py` that claims all 26 is worse than transparent coverage reporting. **Resolution**: explicit `coverage_preflight()` function that reports "running N of 26 constraints; M not yet operationalized" before any audit run. Coverage report on first invocation. Implemented as `--coverage-only` flag.

**Must-fix Finding 8**: Legacy validator stack will emit false positives on new-pipeline output. **Resolution**: `--pipeline-mode` flag on `run_pipeline.py` that sets `ATU_PIPELINE_MODE=1` env var; legacy pre-commit hook should read this and suppress the producer-mode validator cascade. (Hook update is a separate follow-up; flag plumbing is in place.)

**Should-revise findings**: parallel Opus calls via asyncio.gather (implemented); intermediate JSONL writes under `data/reports/atu_pipeline/` (gitignored under existing `data/reports/` rule); Ps 1 integration-test exact-match required (no whitespace tolerance — documented in code comments).

**Non-issue Finding 7**: `audit_constraints.py` does NOT reuse `audit_rendered_output.py` (which is a prompt-formatter, not a constraint-checker). The intended reuse target is `validators/_shared/macula_constituents.py` for future Macula upgrades.

## Build deliverables

### Scripts (all compile-clean; smoke-tested)

| File | LOC | Purpose |
|---|---|---|
| [scripts/atu_pipeline/render_atus.py](../../scripts/atu_pipeline/render_atus.py) | ~280 | Stage 1: Opus 3-pass orchestrator with verse-granularity agreement scoring |
| [scripts/atu_pipeline/audit_constraints.py](../../scripts/atu_pipeline/audit_constraints.py) | ~260 | Stage 2: catalog runner with coverage pre-flight + 3-way verdict taxonomy |
| [scripts/atu_pipeline/run_pipeline.py](../../scripts/atu_pipeline/run_pipeline.py) | ~240 | Stage 3: orchestrator + Aramaic BAIL pre-flight + editorial-review-surface format |
| `scripts/atu_pipeline/prompts/minimal_rubric_hebrew.md` | 99 | Canonical prompt (verbatim from atu-method `2992b10`; unchanged per Stan directive) |

### Architecture properties (per audit revisions)

- **Parallel Opus**: `asyncio.gather` with `return_exceptions=False`; failed pass → MAJORITY-UNCERTAIN scoring (degrades gracefully)
- **Agreement granularity**: whitespace-normalized exact-match of full verse rendering; resilient to line-count differences across passes
- **Long-chapter chunking**: default 40 verses/chunk; auto-shards Ps 119 (176 verses → 5 chunks), Num 7 (89 → 3 chunks)
- **Aramaic detection**: pre-flight on chapter range (ARAMAIC_RANGES dict in run_pipeline.py); explicit BAIL exit before any LLM dispatch
- **Coverage transparency**: pre-flight prints "N active / M not-yet-implemented" before audit run
- **Severity discipline**: all verdicts advisory; never tags STRONG; no auto-override of LLM draft regardless of HARD/ADVISORY tier
- **Reproducibility**: model-ID + canonical prompt hash recorded in per-chapter JSONL output (via git SHA in pipeline report header)
- **Cost controls**: `--dry-run` flag formats prompt + emits token estimate without API call; tested on Ps 1 (~$0.52 for 3-pass run)

### Smoke-test results

1. **Compile**: all 3 scripts `py_compile` clean
2. **Coverage pre-flight**:
   ```
   Loaded 26 constraint entries from canon\constraint_catalog_v1.md
   Coverage pre-flight:
     Total in catalog:   26
     Active (check reg): 4   (JM13, JM103, JM103e, JM158-restrictive)
     Not-yet-impl:       22  (require Macula primitive integration; deferred)
   ```
3. **Ps 1 dry-run**:
   ```
   Chapter: data\text-files\v2\heb\19-psalms\psalms-01.txt (6 verses)
   {"verses": 6, "chunks": 1, "passes": 3,
    "input_tokens_total": 4410, "output_tokens_total": 6000,
    "estimated_cost_usd": 0.516}
   ```

### Active constraint check coverage (v1)

The 4 active constraints (surface-form mechanical; no Macula required) are:
- `JM13-maqqef-group` — maqqef glyph at line boundary
- `JM103-proclitic-stranding` — bare proclitic prefix at line end
- `JM103e-compound-prep-object` — compound preposition stranded from object
- `JM158-restrictive-relative` — leading-אֲשֶׁר heuristic (ADVISORY)

The 22 NOT-YET-IMPLEMENTED constraints need Macula constituent-tree / role-label / frame-arg queries that are not yet wired through `validators/_shared/macula_constituents.py` into the audit script. Wiring those is follow-up work; the catalog is the spec, the script reports honest coverage.

## Ps 1 integration test — NOT YET RUN

Stan's directive: "Integration test on Ps 1 (Stan-validated 14-ATU baseline) once 3 scripts pass — verify pipeline produces baseline exactly. Ps 1 is the empirical gold standard."

This requires LIVE API call (3 Opus passes × $0.52). Pre-conditions met (scripts compile + dry-run validated). Awaiting `ANTHROPIC_API_KEY` available + Stan-trigger to authorize the spend.

**Test plan** (to run when authorized):
```bash
export ANTHROPIC_API_KEY=<key>
PYTHONIOENCODING=utf-8 py -3 scripts/atu_pipeline/run_pipeline.py \
    --book 19-psalms --chapter 1 --batch-name ps-1-integration-test
```

Expected:
- 6 verses processed
- 3 parallel Opus passes per chunk (single chunk; chapter ≤ 40 verses)
- Verse-granularity agreement scoring; expected mostly UNANIMOUS per the 100% poetic accuracy benchmark
- Editorial-review surface at `directives/replies/2026-05-17-1500-pipeline-batch-ps-1-integration-test.md`
- Auto-applied count should equal 14 ATUs (the Stan-validated baseline at commit `90d3af55b`); review surface should be empty or contain only AMBIGUOUS edges

**Exact-match check** (Audit β Finding 6, no whitespace tolerance): comparison of pipeline-proposed rendering against `data/text-files/v2/heb/19-psalms/psalms-01.txt` line-by-line; any divergence = REVIEW-REQUIRED, not silent pass.

## Per-item disposition

| # | Status |
|---|---|
| §7.3 pre-build audit (prompt design α) | DONE — 1 must-fix + 5 should-revise applied at script level (canonical prompt unchanged per Stan) |
| §7.3 pre-build audit (architecture β) | DONE — 4 must-fix + 3 should-revise integrated into scripts |
| `render_atus.py` build | DONE — parallel Opus + verse-granularity agreement + long-chapter chunking |
| `audit_constraints.py` build | DONE — catalog parser + coverage pre-flight + 3-way taxonomy + 4 active checks |
| `run_pipeline.py` build | DONE — Aramaic BAIL pre-flight + orchestration + editorial-review-surface |
| Smoke tests | DONE — compile-clean; catalog parses (26 entries); dry-run token estimate |
| **Ps 1 integration test (live API)** | **BLOCKED on API key + Stan trigger** |
| Macula primitive wiring (22 NYI constraints) | DEFERRED — follow-up directive |
| Legacy validator suppression (pipeline-mode hook update) | DEFERRED — `--pipeline-mode` flag in place; hook code update is separate scope |

## Cost summary

- This turn's audits: 2 Sonnet pre-build audits ≈ $0.05
- Script builds: zero cost (no LLM calls)
- Ps 1 integration test (when run): ~$0.52 (estimated)
- Genesis production batch (50 chapters, when authorized): ~$31–62 per directive 1500 §Cost estimate

## What unlocks after Item 2 integration test

- Item 4 (chapter-by-chapter validation against new pipeline) — substrate ready (Ps 1 baseline + Deut 6 partial + 6 Phase 1.5 reports)
- Directive 1700 (Torah production render) — dependency unblocked
- Sunset Stage 1 (per Item 5 plan) — pipeline operational satisfies the "5 chapters across 3 genres validated by Stan" gate after integration test + book-batch validation

Phase 1.5 chapter review (Stan-work; out of Tanakh-Claude scope) remains independent gate input.
