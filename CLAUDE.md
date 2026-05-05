# Tanakh Reader — Claude Code Instructions

Read this file completely before doing anything in this repo. It is your orientation document for every session.

---

## What This Project Is

A colometric reading edition of the Hebrew Bible (Tanakh). The Masoretic Text is reformatted from standard prose paragraphs into **sense-lines (cola)** — each line a grammatically and semantically self-contained unit, designed for oral delivery and comprehension.

The full methodology is at [`private/01-method/colometry-canon.md`](private/01-method/colometry-canon.md). Read it before any methodology-touching work.

The methodology rests on three forces operating simultaneously:

- **Generative** — atomic thought (one proposition per colon) drives line creation; five closed-list structural patterns justify breaks.
- **Subtractive** — Hebrew syntax integrity, complement integrity, and formula integrity trigger merges; four closed-list merge-overrides govern exceptions.
- **Diagnostic** — single image acts as tiebreaker when generative and subtractive forces are in tension.

The te'amim (cantillation accents) are **the most important single piece of evidence** — they preserve roughly a millennium of expert Masoretic reading tradition (Tiberian, ~9th–10th c. CE) and form the v1-he-baseline that editors revise from. The disjunctive accent hierarchy requires two parsers: one for the prose accent system (21 books) and one for the *Sifrei Emet* system (Psalms, Proverbs, Job 3:1–42:6). But the te'amim are evidence, not authority; any editorial overlay (te'amim, sof pasuq, paseq, niqqud, versification) is evidence that informs the editor's judgment, not a break-licensing rule.

- **Repo:** github.com/bibleman-stan/readers-tanakh (public)
- **Live site:** tanakh-reader.com — `CNAME` file is in repo root; verify GitHub Pages source-setting (Settings → Pages → branch `main`, folder `/`) before assuming the site is serving the latest commit and GA is firing.
- **Base text:** STEPBible TAHOT — CC-BY-4.0
- **User:** Stan (thebibleman77@gmail.com)
- **State (2026-05-04):** all 39 books populated in `data/text-files/v2/he/` at canonical chapter counts (929 chapters, ~40K colometric lines). Macula Hebrew lowfat IR is wired across the validator suite; ~13K STRONG findings have been mechanically applied across the corpus through the round-4 cascade. **Open carry-forwards** in priority order:
  1. **Psa 9:10 parallelism direction** — the orphan `מִשְׂגָּב` was merged with the prior verb-line; editorially correct grouping is parallelism (gapped restatement on the next line). Validator merge-direction needs context-aware logic, not the global default.
  2. **M4 atomic-thought arm Sifrei Emet re-audit** — Wave-B removed overlay-as-authorization skips per the methodology audit, but the Sifrei Emet bound on this specific arm wasn't fully reconsidered. Single-pronoun orphans are colometric errors in any register; verify before next cascade.
  3. **GH Pages source-setting verification + GA Realtime test** (Stan-side, not Claude-side).
---

## Required reading

`handoffs/14-operational-protocols.md` (operating discipline — read at every session start). The methodology canon at `private/01-method/colometry-canon.md` is consult-on-trigger per the CHECK-IN rules below.

---

## Session bookend protocol

Stan is sole authority. Each session writes to `private/03-sessions/yyyy-mm-dd-brief_description/` (start-date; compaction-wake = new folder).

### CHECK-IN (at session start)

**MANDATORY:**
1. This CLAUDE.md in full
2. `handoffs/14-operational-protocols.md` in full — the operating-discipline file. Without this, you will drift into the failure modes it codifies (sequential dispatch, bash heredocs for recurring ops, single-agent-on-39-books cascades, spot-checking instead of testing). Re-read every wake; the patterns are easy to forget mid-session.
3. The most recent `private/03-sessions/yyyy-mm-dd-*/session-notes.md` (for carry-forwards and prior-session context)
4. `git log --oneline -10`

**CONSULT-ON-TRIGGER:**
- `private/01-method/colometry-canon.md` — **trigger:** anything touching `validators/`, `scripts/apply_*.py`, `scripts/parse_teamim.py`, the data files under `data/text-files/v2/he/`, the syntax-reference, or any editorial / rule-interpretation question. **Skip ONLY when:** the work is pure UX / deployment / build-tooling / web-app frontend with no validator-or-rule surface. When in doubt, read it. The "skip-when" boundary is the elision surface that produced 5 sessions of source-stack blindness in 2026-04-27→2026-05-01 — don't elide silently.
- `private/README.md` — **trigger:** writing a new file under `private/` and don't already know the subdirectory layout.

**This protocol applies to all wake signals, including brief "hey" pings.** A short prompt does not shorten the check-in. Compaction-resume runs the full protocol from scratch.

**Carry-forward disposition (mandatory after reading prior session-notes).** Enumerate every carry-forward item from the prior session-notes and classify each as one of:
- **(a) Executing this session** — picked up in current task surface
- **(b) Explicitly retired** — name the rationale (no longer applicable, superseded by X, won't be done because Y)
- **(c) Re-deferred** — name the trigger condition that would re-prioritize it (waiting on hook X, blocked on Stan-side verification, etc.)

Without explicit disposition, items drift across sessions and silently disappear (the NEW-2 longitudinal pattern from the 2026-05-04 prior-sessions audit: "user-facing items never ship because infrastructure work keeps bumping them"). The disposition table is a one-paragraph block in your check-in self-report — visible to Stan, who can correct if you re-deferred something he wanted executed.

**Self-report before first substantive response**: one line per mandatory file (e.g., `- CLAUDE.md: read`), the carry-forward disposition table, AND any red flags noticed during check-in (stale carry-forwards, uncommitted work in tree from prior session, baseline drift, conflicts between session-notes and current state). Silent skip = check-in failure.

### WRAP-UP (at session end, or when context crosses ~60%)

Produce in the session folder:

1. **`session-notes.md`** (mandatory) — session arc, what landed (commits), discipline observations, withdrawn proposals, carry-forwards for next session.
2. **`review-lists/`** (subfolder, when applicable) — only when the session produced candidate lists requiring Stan review.

On-request (not default — only produce when the session warrants it or Stan asks):
- **`full-transcript.md`** — verbatim dialogue extraction. Useful for retrospective audits; not useful for next-session carry-forward (that's `session-notes.md`'s job). Don't dispatch a Sonnet agent for this by default.
- **`dialogue-notes.md`** — only for methodology-heavy sessions where the dialogue arc itself is the work product.

The 2026-05-04 colonoscopy audit found these tail artifacts had low cross-session retrieval value relative to their wrap cost. `session-notes.md` is the load-bearing carry-forward surface.

**Carry-forward integrity (mandatory before writing the carry-forward section).** Every carry-forward item MUST have one of:
- **A concrete next-action** Claude can execute without further Stan input — names the file/script/agent dispatch that will run.
- **A concrete trigger condition** — a named file change, hook event, named-deliverable arrival, Stan-side artifact (only if explicitly Stan-blocked), or dated calendar event.

The following phrasings are **drift, not defers** — they MUST be replaced before the wrap-up commit:
- "Awaiting Stan direction" → either name the standing default and dispatch (per "Default decisions" below), or pin down the question concretely with proposed answer + ≥2 adversarial audits, or retire.
- "Until Stan re-surfaces / brings up again / asks again" → Stan won't re-surface; the item evaporates. Either re-read the prior turn where Stan flagged it and pin down the specific items NOW (named verses, named files, named patterns), or retire with rationale.
- "Stan-direction needed" without a concrete decision-point → the same. Default actions for known classes are listed below; only escalate genuinely novel questions.
- "Defer until [vague event]" → either name the concrete trigger or retire.

This is the WRAP-UP-side complement to the CHECK-IN carry-forward disposition. CHECK-IN catches drift on the next session's read; WRAP-UP catches drift at this session's write — closer to the source.

### Default decisions (standing answers — do NOT surface these as menus)

These decision points have a standing answer per project discipline. Surfacing them as menus to Stan is a permission-loop. Only escalate when the actual decision falls *outside* one of these patterns.

| Decision point | Standing answer | Authority |
|---|---|---|
| Per-item judgment work at corpus scale (e.g., labeling 500-verse FP fixture) | Parallel cluster-Opus dispatch (5–6 agents, one per cluster) + Stan spot-audit on edge cases. Never hand-pass. | `feedback_scripts_default_agents_only_for_judgment.md` + Corpus Cluster Splits |
| Validator FP-rate measurement | Cluster-Opus labeling, NOT manual review. The script `scripts/measure_validator_fp_rate.py` consumes the labels regardless of who produced them. | Phase 2 first-commit definition |
| "Should I run validators or read the chapter manually?" | Validators first. Always. Manual commentary is an overlay on tool output, not a substitute. | `feedback_persistence_means_coverage_gap.md` + Five Diagnostic Questions |
| Adversarial audit on a non-trivial implementation | ≥2 parallel agents in one message, OR `Audit-skippable: <reason>` with named trivial class. Never sequential dispatch. | A3 Step 0 (mechanically gated) |
| Choosing between extending an existing validator vs creating a new one | Extension. Always default to extension; new-validator is `# validator-extension-justified:` only with substantive criterion. | Validator-creation guard hook |
| Cascade rebuild after pipeline change | 6 parallel cluster agents (Phase 2 of two-phase pattern). Never one agent on all 39 books. | A2 mandatory two-phase pattern (mechanically gated) |
| "Should I commit now or wait?" | Commit substantive work proactively. Status claims AFTER the commit, not before. | `feedback_commit_only_finished_work.md` |
| **Same FP class manifests in 2+ specs OR 2+ validators within a session** | **Stop. Fix at engine level (`scripts/spec_runner.py` `_check_morphology` / `validators/_shared/*` / `scripts/apply_*.py`), NOT per-spec or per-validator.** Writing a guard for "the same conceptual FP" the second time = engine-level fix opportunity that's being missed. | Stan-mantra ("swat the bug class, not the instance") + Class-fix discipline below |
| **Stan escalation phrasing** ("WHY are you still doing this", "you screwed up again", "you have to quit taking so long", "stop wasting my time") | **STOP iterating on the surface fix. Frame-reset to class level. Read the recent commits and ask: what's the COMMON pattern across them that I've been treating as separate instances?** Don't continue the surgical-fix path past the escalation. | 2026-05-05 Sifrei-Emet purge arc — three iterations of per-spec guards before engine-level fix; escalation came at iteration 3 and was met with iteration 4 instead of frame-reset |
| **Cascade leaves corpus in known-wrong state at session end** | **Don't wrap. Either fix it inline this session (revert + re-cascade with the corrected rules) OR explicitly retire to a follow-up commit with named verses listing the wrongness; never park "Psa 23:4 still split, Psa 23:5 still over-merged" as a vague carry-forward.** | 2026-05-05 cluster-5 cascade arc — wrap landed with corpus in known-wrong state at the named-verse leading-indicators that motivated the cascade |

When a decision point is genuinely outside this table, surface it. When it's inside, dispatch the standing answer and report the result. The discipline-failure shape is: surfacing a known-default decision as if Stan needs to pick.

### Context-threshold discipline

Green (0–60%): execute. Yellow (60–80%): start drafting `session-notes.md`. Red (80%+): stop new execution, wrap up. Compaction-resume runs full CHECK-IN.

---

## Key Files

Current as of 2026-05-05 (post Macula-pivot promotion sweep + round-4 cascade + CLAUDE.md rebuild). Re-date this header whenever the table is reviewed for stale entries.

| Path | Purpose |
|---|---|
| `index.html` | Main web app (RTL Hebrew, inline CSS/JS) |
| `scripts/ingest_tahot.py` | TAHOT TSV → v0-prose |
| `scripts/parse_teamim.py` | Te'amim hierarchy → v1-he-baseline cola + per-word layers |
| `scripts/build_books.py` | v2→v1 cascade → per-chapter HTML + manifest |
| `scripts/propagate_editorial_layers.py` | Re-segments v1 per-word layers when v2/he cola changes |
| `validators/run_all.py` | Dashboard + baseline gate |
| `validators/check_canon_extensions.py` | Commit-msg gate against canon-extension diffs |
| `data/text-files/v0/prose/*/` | Raw TAHOT — **NEVER EDIT** |
| `data/text-files/v1/{he-baseline,eng-interlinear,eng-gloss,translit}/*/` | Te'amim-baseline cola + lockstep per-word layers |
| `data/text-files/v2/he/*/` | All 39 books / 929 chapters hand-edited (single source of truth, post round-4 cascade) |
| `data/text-files/v2/{eng-interlinear,eng-gloss,translit}/*/` | Per-word layers aligned to v2/he (regenerated by propagate_editorial_layers.py) |
| `data/syntax-reference/hebrew-break-legality.md` | Layer 1 surface (shape-capped) |
| `private/01-method/colometry-canon.md` | Layer 3 editorial methodology |
| `.git/hooks/{pre-commit,commit-msg}` | Mechanical gates (sourced from `validators/hooks/`) |

---

## CRITICAL: Source Text Rules

**NEVER:** modify vendored sources in `research/`; modify `v0/prose/` files; alter Hebrew consonants/niqqud/te'amim; add or remove words; adopt readings from non-vendored versions (LXX/DSS/Samaritan/Targums/Peshitta/Vulgate) into source files (see canon §0.1); run te'amim parsers without checking if hand-edited `v2/he/` chapters will be overwritten.

**ALWAYS:** work only in `v2/he/` (the editorial surface is where lines break); preserve verse-refs and Ketiv/Qere markers; use `PYTHONIOENCODING=utf-8` for Python on Windows (Hebrew Unicode).

---

## Te'amim as Evidence

The te'amim are the editor's starting draft, not the editor's authority. The v1-he-baseline is what the accent hierarchy produces; departures need a documented reason (which of the three forces is doing the work). **Three criteria, not four** — atomic thought, single image, Hebrew syntax. Breath is NOT a criterion. **No overlay has deterministic force** — te'amim, sof pasuq, paseq, niqqud, versification all are evidence; none license a break alone.

---

## Tier Discipline

The pipeline is **v0 → v1 → v2**. The earlier 5-tier scheme (v0/v1/v2-he-syntax/v3-he-colometry/v4-editorial) was collapsed 2026-04-27 — see canon §8 entry for rationale.

| Tier | Directory | Engine | What it does |
|---|---|---|---|
| v0 | `data/text-files/v0/prose/` | `scripts/ingest_tahot.py` | Raw text from TAHOT. Never edited. |
| v1 | `data/text-files/v1/he-baseline/` | `scripts/parse_teamim.py` | Te'amim-as-evidence baseline cola draft. Editor's starting draft, not a normative "version 1." |
| v2 | `data/text-files/v2/he/` | Stan + Claude | Hand-edited Hebrew gold standard. Applies the three forces (generative, subtractive, diagnostic) and the four merge-overrides; consumes Layer 1 + Layer 3 validator findings as a work queue. Single source of truth for the build. |

Parallel per-word layers (`v2/eng-interlinear/`, `v2/eng-gloss/`, `v2/translit/`) are produced by `scripts/propagate_editorial_layers.py` from v2/he. `scripts/build_books.py` picks v2 if present per chapter, otherwise v1.

**Validator findings are the work queue.** `validators/run_all.py` is the dashboard; STRONG-tagged findings get mechanically applied (Category A per canon §2); REVIEW-REQUIRED → per-item editorial judgment. Canon §7's ≥80% adoption gate governs when STRONG is trusted.

### Rule-derivative vs ad-hoc

Rule-derivative = adopted-validator STRONG findings → mechanical apply, dashboard surfaces post-cascade for spot-check. Ad-hoc = REVIEW-REQUIRED or unclassified → per-item editorial judgment. Walking Stan through verse-level confirmations on rule-derivative changes treats a mechanical rule as advisory — wrong. If a validator's STRONG-tag is uncalibrated, fix the validator and re-cascade; don't gate every emission.

---

## Three-Layer Validation Architecture

| Layer | What | Where | Error class |
|---|---|---|---|
| 1 | Generic Hebrew grammar — universal, language-level | `data/syntax-reference/hebrew-break-legality.md` | `[MALFORMED]` |
| 2 | Validators that enforce both layers | `validators/syntax/` (L1) + `validators/colometry/` (L3) | emits L1 / L3 |
| 3 | Tanakh-specific editorial methodology | `private/01-method/colometry-canon.md` | `[DEVIATION]` |

Layer 1 is permission/prohibition (what grammar forbids/permits, not what to choose); Layer 3 operates within Layer 1's permitted-either space. Mixing the two is a regression.

**Imposing vs revealing — the Layer 3 constraint.** Don't codify rules from one or two session observations; don't add scope-exclusion carve-outs (Sifrei Emet skip, acrostic skip, register guard) unless grounded in the three criteria — not in editorial overlay categories. **Editorial overlays (te'amim, niqqud, versification, register classification) are calibration evidence, not authorization.** If a Layer 3 rule fires in Sifrei Emet, the answer is "is the fix correct under the three criteria?" not "Sifrei Emet is exempt." (Wave B 2026-05-04 audit removed 11 such skips.)

### Mechanical gates (enforced by git hooks)

| Component | What |
|---|---|
| `validators/run_all.py` | Dashboard + `--baseline-check` (regression gate) + `--update-baseline` |
| `.git/hooks/pre-commit` | Phase 1: auto-run `refresh_book.py` per affected book, stage derived layers. Phase 2: `run_all.py --baseline-check`. |
| `.git/hooks/commit-msg` | `check_canon_extensions.py` — refuses canon-extension commits without audit-evidence keyword |
| `.claude/hooks/check_bash_discipline.py` | Bash/Agent/Write/Stop hook — heredoc, cascade-on-main-thread, verbose-git, A3-Step0, scripts-vs-agents, validator-creation, permission-loop, counts-headline, override-quote-validation. Five hooks bind at runtime. |
| `validators/colometry/validate_clause_nucleus_split.py` | H18 (Clause-Nucleus Integrity) — adopted; emits STRONG-MERGE + STRONG-SPLIT |
| `validators/_shared/poetic_register.py` | Sifrei Emet detector — calibration only, NEVER authorization |

**Override:** `git commit --no-verify` (Stan-only, explicit).

**One-time setup:** `bash validators/hooks/install.sh`

**Routine:** `PYTHONIOENCODING=utf-8 py -3 validators/run_all.py [--baseline-check | --update-baseline]`

---

## Class-fix vs instance-fix discipline

Stan's mantra: *"good rules → validators → mechanical apply at scale → swat the bug class, not the instance."* The 2026-05-05 Sifrei-Emet purge ran three iterations of per-spec guards (h18_1, m2_4_b, h16_c) before the engine-level fix at `_check_morphology("prep")` in `scripts/spec_runner.py`. Each surgical fix looked locally rational; the aggregate was whack-a-mole. Stan escalated at iteration 3; the class fix landed at iteration 4.

**Self-test at the moment of writing a per-spec/per-validator guard:** "Have I added a similar guard for the same FP class in this session?" If yes → STOP. Fix at the engine layer (`scripts/spec_runner.py`, `validators/_shared/*`, `scripts/apply_*.py`), not the next per-spec file. Per-spec/per-validator guards are correct only when the logic is genuinely local and would not generalize.

When a cluster cascade leaves corpus in a known-wrong state at the named-verse leading-indicators, walk the failure back to root and re-cascade — don't park it as carry-forward.

---

## Five Diagnostic Questions (Before Writing New Specs or Tools)

Before adding a new validator, proposing a new H-rule, or building infrastructure:

1. Is there already a validator, spec, or helper for this? (check `validators/_shared/`, `validators/colometry/`, `validators/syntax/`)
2. Does Macula lowfat XML already provide the signal as a constituent role-label or frame annotation, such that a 20-line XPath query replaces 200 lines of TAHOT-tag walking?
3. Am I answering the question Stan asked, or a different question? (when Stan asks for a spot-check, run the spot-check; don't build tooling)
4. Did Stan specify a model, approach, or constraint I'm about to ignore?
5. What's the smallest version that would test the hypothesis?

If you answer any of (1)–(4) affirmatively, STOP and re-scope before building.

Imported from GNT-Reader sibling 2026-05-05.

---

## Adversarial-audit discipline

**Step 0 (pre-implementation).** Before non-trivial implementation (new validator with classification logic, new spec, new shared helper, new mechanism, new canon rule), FIRST tool call must be either ≥2 parallel Agent adversarial dispatches in one message, OR a `Audit-skippable: <reason>` declaration citing a trivial class (port-of-validated, mechanical-ingest, test/fixture, runner/glue, scratch). Hook-enforced at cascade-boundary signals.

**Pre-commit (canon-touching commits).** Every commit that modifies `private/01-method/colometry-canon.md` declares audit-status: `Audit-skippable per §7 ([reason])` OR `Audit dispatched: [evidence]`. When uncertain, dispatch — false-positive audit cost is small, false-negative cost is large. The 12 trigger conditions are in canon §7. The commit-msg hook refuses canon-extension patterns without the keyword.

---

## Follow-on rebuild cascade

**Automatic on every commit touching `data/text-files/v2/he/`.** Pre-commit hook detects affected books and runs `refresh_book.py --book <book> --build`, staging regenerated `v2/eng-{interlinear,gloss,translit}/` + `books/<book>/` into the same commit. Editor commits only the Hebrew; everything downstream regenerates atomically.

**Manual:** `PYTHONIOENCODING=utf-8 py -3 scripts/refresh_book.py --book <slug> --build`. The PYTHONIOENCODING prefix is mandatory on Windows for any script touching Hebrew Unicode.

**When running BOTH apply_validators AND apply_specs (cluster cascade after spec change):** order is `apply_validators` FIRST, then `apply_specs`, then `refresh_book`. Validators establish structure (STRONG-MERGE work queue) that specs are calibrated against; reverse order over-merges. Each cluster-agent commits its diff before the next stage.

---

## Agent dispatch — model routing

Haiku for mechanical lookups (file moves, set-membership, single-file reads). Sonnet for narrow-scope scans where rules are already defined. Opus for adversarial audits, methodology synthesis, novel rule design — anything where reasoning quality IS the deliverable. **Sonnet is default; reserve Opus for reasoning-heavy work.**

---

## Corpus cluster splits

Split agents by cluster for corpus-wide work; never one agent on all 39 books. **Threshold:** any batch of ≥25 surgical fixes spanning 3+ clusters MUST be split.

1. **Torah** — Genesis, Exodus, Leviticus, Numbers, Deuteronomy
2. **Former Prophets** — Joshua, Judges, 1-2 Samuel, 1-2 Kings
3. **Latter Prophets** — Isaiah, Jeremiah, Ezekiel, the 12 Minor Prophets
4. **Writings (prose)** — Ruth, Esther, Daniel, Ezra-Nehemiah, 1-2 Chronicles, Ecclesiastes prose
5. **Sifrei Emet (poetic)** — Psalms, Proverbs, Job 3:1–42:6
6. **Embedded Poetry** — Exod 15, Deut 32, Deut 33:2-29, Judg 5, 1 Sam 2:1-10, 2 Sam 22, Isa 12, Hab 3, Lam 1-5, Song of Songs, Eccl 3:2-8

Two-phase pipeline-change pattern (one agent for code, N-cluster parallel agents for rebuild) is in `handoffs/14 §A2` — hook-enforced.

---

## Editorial-call structure rule

When Stan names a specific verse with a specific desired partition, the next assistant turn structure is: line 1 = "Got it — [Stan's reading]"; line 2-N = the diff being applied. NO leading analytical defense of an alternative reading. Analysis is value-add ONLY when Stan asks "what should it be?" — not when Stan tells me what it is.

---

## Connected Resources

`C:\vaults-nano\my_brain\10_Projects\Readers\` — Stan's ATU research-program orientation + reader-projects MOC. Read for calibration when methodology canon and CLAUDE.md feel under-specified.

---

## Git workflow

All work on `main`. Claude commits; Stan pushes. Standing instruction: commit substantive work proactively, status claims AFTER the commit.

### Tree-state self-check before commit (mandatory)

Before any `git add` or `git commit`, run `git status --short | wc -l` (or `--short` directly if the count is small). If the tree contains modified files you didn't author this session — especially under `data/text-files/v2/he/`, `validators/`, or `scripts/` — STOP and surface to Stan before staging. This is the failure mode that produced commit `4e1857e25` (Item Zero in the State block above): a 12-line analytics edit landed as a 4554-file commit because pre-existing staged work from a "kill everything, stop" wrap-up was in the tree and got bundled by the pre-commit cascade.

The rule: **a commit's title should describe its actual scope.** If you're about to commit work you didn't author, either (a) ask Stan first, (b) commit it separately under its own title, or (c) `git stash --keep-index` the unrelated work, commit yours, then unstash.

---

## Project siloing

Publicly independent. No cross-references to sibling projects in README/CLAUDE.md/handoffs. Connection lives only in `private/` and Stan's head.

---

## Update protocol

CLAUDE.md is the load-bearing doc. **Do NOT add new memory files** — prose memories bind at ~50%; CLAUDE.md / handoffs/14 / runtime hooks are where corrections persist. The freeze is in force until the colonoscopy-audit's TRIGGER-section format migration ships.

**Rejected approaches — do not re-propose:**
- **Canary-before-cluster-cascade** (rejected 2026-05-04: "if the tools work, the canary doesn't save you").
- **Adding memory files to encode behavioral discipline.**

---

## Built mechanical hooks (2026-05-05 session)

Five hooks now binding behavior at runtime. All pass `tests/test_bash_discipline_hook.py` (56/56 fixtures).

| Hook | Event/Tool | What it catches | Bypass |
|---|---|---|---|
| Override quote-validation | PreToolUse / Bash | Hallucinated-Stan-citation in `# disciplined-allow:` / `# split-justified:` / `# audit-skippable:` / `# judgment-required:` / `# validator-extension-justified:` reasons | Drop the fabricated quote |
| Bash heredoc / cascade / verbose-git / A3-Step0 | PreToolUse / Bash | Multi-line Python heredocs, `--all-books` on main thread, bare `git status` / `git diff`, cascades without ≥2 recent Agent dispatches | `# disciplined-allow:` / `# split-justified:` / `# audit-skippable:` (visible in JSONL) |
| Scripts-vs-agents (`[SCRIPTS-DEFAULT]`) | PreToolUse / Agent | Short prompt body (≤2000 chars) with mechanical-vocabulary verb (count/list all/how many/find all/enumerate/scan every/check whether/look up/pull every/return every/glob for) | `# judgment-required: <reason>` (substance-validated against closed criterion vocabulary) |
| Validator-creation guard (`[VALIDATOR-PROLIFERATION]`) | PreToolUse / Write | Creating new `validators/(syntax\|colometry)/validate_*.py` files | `# validator-extension-justified: <reason>` in recent assistant message (substance-validated) |
| Permission-loop coda (`[PERMISSION-LOOP]`) | Stop | Outgoing message ends with `?` AND recent `TodoWrite` has non-completed todos | `<!-- question-required: <reason> -->` HTML comment (renders invisible in markdown) |
| Counts-headline (`[COUNTS-HEADLINE]`) | Stop | First paragraph contains bare integer ≥100 not contextualized as a verse/chapter/line/word/file/book reference | `<!-- counts-ok: <reason> -->` HTML comment |

Override-substance validation: `# judgment-required:` reason must match closed vocabulary (classify / synthesis / adversarial / precedence / edge-case / ambiguous / multi-source / cross-rule / methodology / FP-rate / per-item / judgment-call). `# validator-extension-justified:` requires (extend / new-arm / new-subcase / distinct-failure / orthogonal / cannot-be-added / existing-validator-misses / fundamentally-different). Quote-validation universal. Settings.json (gitignored): `PreToolUse.matcher = "Bash|Agent|Write"` + separate `Stop` event entry.

---

## Deferred Operational Work (priority order)

These are concrete next-step items surfaced by the 2026-05-04 audits and the 2026-05-05 path-forward review. Each has explicit completion criteria so a future session can pick one up without re-deriving the rationale.

1. **Phase 2 defensibility — first commit (`scripts/measure_validator_fp_rate.py`).** Write a script that takes a 500-verse fixture set (sampling frame: 100 verses per cluster from clusters 1-5, 0 from cluster 6 since embedded poetry is small enough to fixture separately later; within each cluster, stratify by book proportional to chapter count, then sample uniformly within each book), runs `apply_validators.py` in dry-run, and computes per-validator true-positive / false-positive rates against manual-review ground truth. Ground-truth file: `tests/fp-baseline-fixtures.tsv` columns (verse-id, validator-name, expected-action {APPLY, REVIEW, REJECT}, rationale-brief). Output: `validators/.fp-baseline.json` with per-validator TP/FP/uncalibrated counts. **First-commit definition.** Phase 2 is not declared until this script exists and runs clean on the fixture set; "Phase 2" without the script is a CYA pause, not a pivot.

2. **Psa 9:10 parallelism direction fix.** `validate_short_orphan_line.py` currently emits `merge_with_previous` for the M4 atomic-thought arm. For parallelism cases (gapped restatement on the next line), the correct merge is `merge_with_next`. Implement context-aware direction: if the next non-blank line is content sharing morphology/role with the prior verb's complement, prefer `merge_with_next`; if next is blank/verse-end, keep `merge_with_previous`. Single-validator change; no new validator needed (this is a bug fix within the existing arm, NOT proliferation).

3. **GitHub Pages + GA Realtime verification (Stan-side).** Confirm Pages source-setting is `Source: Deploy from a branch / Branch: main / Folder: /`. Visit tanakh-reader.com in one tab + GA Realtime in another; click between chapters; confirm `page_view` events fire on hashchange.

4. **A standalone cascade-alignment scanner** (target name: `scripts/check_cascade_alignment.py`) — port the word-count imbalance scanner from the GNT sibling repo. Tanakh has `scan_english_drift.py` and `english_quality_check.py` already, but lacks an on-demand alignment scanner separate from the pre-commit pipeline. Adapter work: change the sibling's editorial-tier paths to use tanakh's v2/he and v2/eng-interlinear directories. Haiku-tier mechanical port; no judgment work.

Nothing in this list authorizes building a new validator, drafting a new H-rule, adding an M-override, or running a STRONG-promotion sweep. Those are out-of-scope until item 1 lands AND the validator-creation guard hook lets you through (it won't, by design, unless you can name a substantive criterion).
