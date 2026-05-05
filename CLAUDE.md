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
- **Item Zero — historical commit-title mismatch:** commit `4e1857e25` ("chore(analytics): wire Google Analytics") actually bundled (i) the GA snippet, (ii) the round-4 cluster cascade (~8K STRONG-MERGE applications), (iii) the `_validate_override_quotes` hook hardening, (iv) the `apply_validators` blank-safe-target patch, (v) the `validate_short_orphan_line` M4 direction fix, (vi) the `.baseline.json` refresh. The mismatch happened because pre-existing staged work from the prior session ("kill everything, stop") sat in the tree when the GA commit landed. Lesson: **`git status --short` before any `git add` or `git commit`** — see "Tree-state self-check" below.

---

## Read the Handoff Docs First

Before any substantive work, read the handoffs directory in order:

| File | Covers |
|---|---|
| `handoffs/00-index.md` | Index and update protocol |
| `handoffs/01-project-overview.md` | Vision, scholarly landscape, methodological commitments, source-text rationale |
| `handoffs/03-architecture.md` | Repo structure, build pipeline (planned), private folder convention |
| `handoffs/04-editorial-workflow.md` | How a chapter goes from raw TAHOT to gold-standard reading edition |
| `handoffs/14-operational-protocols.md` | **READ THIS CAREFULLY** — codified work-smarter discipline ported from sibling projects: find-the-class fixes, mandatory two-phase pipeline pattern, parallel dispatch, adversarial testing, tools-over-bash, tanakh-specific failure modes |

The methodology canon (`private/01-method/colometry-canon.md`) is the authoritative rule reference once editorial work begins. Read it before any rule-interpretation or methodology-touching work.

---

## Session bookend protocol

Stan is the sole authority for this project. Session bookends produce artifacts in a per-session folder.

### Session folder convention

Each Claude Code session (JSONL boundary) gets its own folder:

`private/03-sessions/yyyy-mm-dd-brief_description/`

Use the **session start date**. A compaction-wake starts a new session; create a new folder with a new descriptor, even if the calendar date is the same as the pre-compaction folder.

The folder is the persistent write surface for the session. Session memory evaporates at compaction; the folder survives.

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

### Context-threshold discipline

- **Green zone (0–60%)**: execute normally.
- **Yellow zone (60–80%)**: start drafting `session-notes.md`; consider wrapping at natural breakpoints.
- **Red zone (80%+)**: stop new execution, wrap up.

Compaction-resume: still run the full CHECK-IN protocol when resuming from a compaction summary.

### Intra-session Log

Maintain a running tally during a session in the session folder (`private/03-sessions/yyyy-mm-dd-*/intra-session-log.md`):

- **Discipline failures**: Stan corrections received + memory file updates triggered
- **Withdrawn proposals**: things proposed and rolled back, with rationale
- **Workflow use-count**: agent dispatches (with model tier breakdown), commits, cascade runs
- **In-flight agents**: live count + IDs of background agents

Update after each significant event (every 5-10 dispatches or every Stan correction). Compaction-resume agents read this for fast situational awareness.

---

## Key Files

Current as of 2026-05-05 (post Macula-pivot promotion sweep + round-4 cascade + CLAUDE.md rebuild). Re-date this header whenever the table is reviewed for stale entries.

| File | Status | Purpose |
|---|---|---|
| `index.html` | live | Main web app — RTL Hebrew layout, all CSS/JS inline |
| `scripts/ingest_tahot.py` | live | Reads STEPBible TAHOT TSV → per-book/per-chapter v0-prose files |
| `scripts/parse_teamim.py` | live | Parses te'amim hierarchy → v1-he-baseline cola + per-word layers |
| `scripts/build_books.py` | live | 3-tier cascade (v2 → v1) → per-chapter HTML files under `books/<slug>/` + `manifest.json` |
| `scripts/propagate_editorial_layers.py` | live | Re-segments v1 per-word layers (interlinear/translit/gloss) when v2/he changes cola structure |
| `validators/run_all.py` | live | Dashboard + baseline gate (--baseline-check / --update-baseline) |
| `validators/check_canon_extensions.py` | live | Commit-msg gate against canon-extension diffs |
| `data/text-files/v0/prose/*/` | populated | Raw text from TAHOT — **NEVER EDIT** |
| `data/text-files/v1/he-baseline/*/` | populated | Te'amim-baseline cola draft (script-emitted) |
| `data/text-files/v1/{eng-interlinear,eng-gloss,translit}/*/` | populated | Per-word layers in lockstep with v1/he-baseline |
| `data/text-files/v2/he/*/` | all 39 books, 929 chapters | Hand-edited Hebrew gold standard — single source of truth. ~13K STRONG validator findings applied through the 2026-05-04 round-4 cascade. |
| `data/text-files/v2/{eng-interlinear,eng-gloss,translit}/*/` | all 39 books | Per-word layers aligned to v2/he cola structure (regenerated by `scripts/propagate_editorial_layers.py` via the pre-commit cascade). |
| `data/syntax-reference/hebrew-break-legality.md` | live | Layer 1 surface (shape-capped, 22/24 rows) |
| `data/syntax-reference/teamim-inventory.md` | TODO | Te'amim glyph inventory (not yet created) |
| `private/01-method/colometry-canon.md` | live (force-staged) | Layer 3 editorial methodology |
| `validators/colometry/validate_clause_nucleus_split.py` | live | Layer 3 colometry validator — Rule H18 (Clause-Nucleus Integrity). Adopted 2026-05-04 (Macula-pivot promotion sweep) — emits both STRONG-MERGE-CANDIDATE and STRONG-SPLIT-CANDIDATE; in `ADOPTED_VALIDATORS`. Uses `validators/_shared/poetic_register.py` only as calibration, not authorization. |
| `validators/_shared/poetic_register.py` | live | Shared helper — detects poetic register (Sifrei Emet chapters) for validators that need register-aware behavior |
| `books/<slug>/manifest.json` | generated | Per-book manifest `{slug, book_name, chapters:[1..N]}` for JS nav |
| `books/<slug>/<slug>-NN.html` | generated | Per-chapter HTML fragment (one `<div class="chapter">` block) — fetched lazily by the client |
| `.git/hooks/{pre-commit,commit-msg}` | installed | Mechanical gates (sourced from `validators/hooks/`) |

---

## CRITICAL: Source Text Rules

Multiple free Hebrew-text editions are vendored in `research/` (gitignored): STEPBible TAHOT (primary, Leningrad), OSHB and UXLC (Leningrad transcription cross-checks), MAM (Aleppo tradition reference). The **primary** that feeds `data/text-files/v0/prose/` is currently TAHOT; the others are cross-references and not part of the build pipeline. See `handoffs/03-architecture.md` for the full source table.

**NEVER:**
- Modify any vendored source file in `research/`
- Modify a `v0/prose/` file
- Alter the Hebrew consonants, niqqud, or te'amim
- Add or remove words
- Adopt readings from non-vendored versions (LXX, DSS, Samaritan, Targums, Peshitta, Vulgate) into source files — see textual-posture statement in `private/01-method/colometry-canon.md §0.1`
- Run te'amim parsers without checking if hand-edited chapters in `v2/he/` will be overwritten

**ALWAYS:**
- Work in `v2/he/` — the only editorial tool is where lines break
- Present proposed changes for review before finalizing
- Preserve verse references and Ketiv/Qere markers for alignment with standard editions
- Use `PYTHONIOENCODING=utf-8` when running Python scripts on Windows (Hebrew Unicode)

---

## Te'amim as Evidence

The te'amim are the editor's starting draft, not the editor's authority. Operating rules:

1. **The v1-he-baseline layer is the baseline.** Every editorial decision in `v2/he/` starts from what the accent hierarchy produces. Departing from it requires a documented reason — which of the three forces (generative, subtractive, diagnostic) is doing the work and why.

2. **Three criteria, not four.** The criteria are atomic thought, single image, and Hebrew syntax. Breath is not a criterion — the te'amim are literally the historical record of Masoretic cantorial phrasing; if breath were a valid prior, the te'amim would encode it perfectly by definition. Both sibling projects (empirical retirement, 2026) confirmed zero cases where breath was the sole deciding factor.

3. **No overlay has deterministic force.** Te'amim, sof pasuq, paseq, niqqud, versification, and punctuation are all evidence. None license a break by themselves.

This is the project's principal differentiator from prior critical editions and the source of its methodological defensibility.

---

## Tier Discipline

The pipeline is **v0 → v1 → v2**. The earlier 5-tier scheme (v0/v1/v2-he-syntax/v3-he-colometry/v4-editorial) was collapsed 2026-04-27 — see canon §8 entry for rationale.

| Tier | Directory | Engine | What it does |
|---|---|---|---|
| v0 | `data/text-files/v0/prose/` | `scripts/ingest_tahot.py` | Raw text from TAHOT. Never edited. |
| v1 | `data/text-files/v1/he-baseline/` | `scripts/parse_teamim.py` | Te'amim-as-evidence baseline cola draft. Editor's starting draft, not a normative "version 1." |
| v2 | `data/text-files/v2/he/` | Stan + Claude | Hand-edited Hebrew gold standard. Applies the three forces (generative, subtractive, diagnostic) and the four merge-overrides; consumes Layer 1 + Layer 3 validator findings as a work queue. Single source of truth for the build. |

Parallel per-word layers under `v2/` (`v2/eng-interlinear/`, `v2/eng-gloss/`, `v2/translit/`) are produced by `scripts/propagate_editorial_layers.py` from the v2/he Hebrew structure plus the v1 per-word streams. The build cascade (`scripts/build_books.py`) picks v2 if present per chapter, otherwise falls through to v1.

**Why the collapse:** the old v2-he-syntax (auto-apply Layer 1 STRONG candidates) and v3-he-colometry (auto-apply Layer 3 STRONG candidates) tiers added complexity without adding capability — STRONG findings now feed the editorial work queue directly, where the editor applies them with the same reasoning Categories A/B/C the canon already governs (§2 Mechanical-rule authority). The closed-list rule set (H1, H2, H5, H7, H11, H16) was not the failure surface that mechanical-tier expansion in sibling projects had been; the tiers' autonomy boundary was already established at the canon level. Two tiers (baseline + editorial) are sufficient.

**Validator findings are the work queue, not a separate tier.** `validators/run_all.py` produces the dashboard; STRONG-tagged findings on v1 → v2 transitions are Category A (apply confidently per §2); REVIEW-REQUIRED items go to per-item editorial judgment. The `≥80%` adoption gate (canon §7) governs when a validator's STRONG findings are trusted as Category A. The previous "tier-diff audit gate" is replaced by commit-time discipline (the pre-commit and commit-msg gates documented below).

### Rule-derivative vs ad-hoc changes (do not gate the wrong one)

A rule-derivative change is one a validator with adopted STRONG-tag emission has classified — the rule is mechanical, the application is mechanical, the editor's role is to run it and verify post-cascade. An ad-hoc change is editorial judgment on a verse the validators didn't classify, or where the validator emitted REVIEW-REQUIRED — the editor's role is to decide.

**Gate the right one.** Ad-hoc changes go through editorial review. Rule-derivative changes (validator STRONG-MERGE / STRONG-SPLIT findings on validators in `ADOPTED_VALIDATORS`) get **applied**, then the post-cascade dashboard surfaces the diff for spot-check. Walking Stan through N verse-level confirmations on rule-derivative changes is exactly the failure this corollary exists to prevent — it treats a mechanical rule as advisory, wastes context budget, and pushes the editor into a review queue rather than applying the validator's work queue. Stan's mantra: *"good rules → validators → mechanical apply at scale → swat the bug class, not the instance."*

If the validator is wrong, fix the validator (and re-cascade), don't gate every emission. If the validator's STRONG-tag confidence is uncalibrated, the answer is FP-rate measurement (Phase 2 Deferred Work item 1) — not surfacing every finding to Stan.

---

## Three-Layer Validation Architecture & Mechanical Gates

Mirrors the `bibleman-stan/readers-bofm` sibling architecture (codified there 2026-04-19, ported here 2026-04-27):

| Layer | What it is | Where it lives | Validator error class |
|---|---|---|---|
| **1** | Generic Hebrew grammar surface — universal facts, language-level | `data/syntax-reference/hebrew-break-legality.md` | `[MALFORMED]` |
| **2** | Validators — enforce both layers with distinct error classes | `validators/syntax/` (L1) + `validators/colometry/` (L3) | emits L1 / L3 |
| **3** | Tanakh-specific editorial methodology | `private/01-method/colometry-canon.md` | `[DEVIATION]` |

**Discipline:** Layer 1 is a permission/prohibition surface — it catalogs what Hebrew grammar **forbids** or **permits**; it does not prescribe choices among permitted alternatives. Layer 3 operates **within** Layer 1's permitted-either space and codifies project-specific editorial calls. Mixing them in either direction is a regression. The shape cap on Layer 1's table prevents prose-creep; the `[MALFORMED]` vs `[DEVIATION]` error classes prevent confusing a syntax illegality with an editorial deviation.

**Imposing vs revealing — the Layer 3 constraint.** When adding to Layer 3 (canon rules, M-overrides, validators that emit `[DEVIATION]`), don't codify rules from one or two session observations; don't add scope-exclusion carve-outs (Sifrei Emet skip, acrostic skip, register guard) unless the carve-out is methodologically grounded in the three criteria (atomic thought, single image, Hebrew syntax) — not in editorial overlay categories. **Editorial overlays — te'amim, niqqud, versification, register classification — are calibration evidence, not authorization.** If a Layer 3 rule fires on a verse and the candidate fix happens to be in Sifrei Emet, the answer is "is the fix correct under the three criteria?", not "Sifrei Emet is exempt." The 2026-05-04 methodology audit removed 11 `is_poetic_register` skips that had been treating overlay as authorization; future skip-list additions face the same test. (See `private/03-sessions/2026-05-04-macula-promotion-and-methodology-audit/session-notes.md` Wave B.)

### Mechanical gates (enforced by git hooks)

| Component | What it does |
|---|---|
| `validators/run_all.py` | Dashboard. Discovers all `validate_*.py`, runs each with `--json --v2`, aggregates per-validator finding counts. Modes: default (report-only), `--baseline-check` (regression gate against `validators/.baseline.json`), `--update-baseline` (capture current state). |
| `validators/.baseline.json` | Per-validator finding counts captured at the moment of last `--update-baseline`. The reference state for regression detection. |
| `.git/hooks/pre-commit` (← `validators/hooks/pre-commit`) | Two-phase gate. **Phase 1 (rebuild cascade):** when `data/text-files/v2/he/<book>/` paths are staged, auto-runs `scripts/refresh_book.py --book <book> --build` for each affected book and stages the regenerated derived layers (`v2/eng-interlinear/`, `v2/eng-gloss/`, `v2/translit/`, `books/<book>/`) before the commit lands. Multiple books in one commit are rebuilt sequentially; any rebuild failure aborts the commit. **Phase 2 (regression gate):** runs `run_all.py --baseline-check`; blocks on finding count increase vs baseline. |
| `.git/hooks/commit-msg` (← `validators/hooks/commit-msg`) | Runs `validators/check_canon_extensions.py` on the proposed commit message. Detects canon extensions (new `Rule HN`, new `MN.` merge-override, new dated principle, closed-list table row, new §7 trigger, new SCOPE-exclusion bullet). Requires audit-evidence keyword (`audit`, `§7`, `post-codification`, etc.) OR skip-safe claim (`typo`, `formatting`, `audit-skippable`). Closes the smuggling-during-unrelated-commit failure mode. |
| `validators/colometry/validate_clause_nucleus_split.py` | Layer 3 colometry validator for Rule H18 — Clause-Nucleus Integrity (see canon §5 H18). Adopted 2026-05-04 in the Macula-pivot promotion sweep (apply_validators.py ADOPTED_VALIDATORS line 164). Emits both `[DEVIATION]`-class STRONG-MERGE-CANDIDATE and STRONG-SPLIT-CANDIDATE findings; the round-4 cascade applied these mechanically. Uses `validators/_shared/poetic_register.py` as calibration evidence only, never as authorization. |
| `validators/_shared/poetic_register.py` | Shared helper module. Detects whether a chapter is in poetic register (Psalms, Proverbs, Job 3:1–42:6) so that register-sensitive validators can adjust behavior. Imported by `validate_clause_nucleus_split.py` and available to future validators needing the same discriminant. **Use only as calibration, never as authorization** (see "Imposing vs revealing" above) — register membership cannot license suppressing a finding that the three criteria say is real. |
| `.claude/hooks/check_bash_discipline.py` `_validate_override_quotes()` | Override quote-validation gate (added 2026-05-04 per colonoscopy audit). When any override comment (`# disciplined-allow:`, `# split-justified:`, `# audit-skippable:`) cites a quoted phrase ≥20 chars attributed to Stan, the hook walks the recent JSONL transcript user-turns and refuses the override if the cited phrase is not present verbatim or fuzzy-matched (SequenceMatcher ratio ≥0.92). Closes the hallucinated-citation bypass that allowed two hook violations in 90 minutes. **This is the one mechanical binding that has demonstrably changed Claude behavior at the moment of decision** — preserve. |

**Override (Stan-only, explicit decision):** `git commit --no-verify`

**One-time setup after fresh clone (or when hooks are missing):**

```bash
bash validators/hooks/install.sh
```

(Manual fallback if the script is missing: `cp validators/hooks/pre-commit .git/hooks/pre-commit && cp validators/hooks/commit-msg .git/hooks/commit-msg && chmod +x .git/hooks/pre-commit .git/hooks/commit-msg`)

**Routine commands:**

```bash
PYTHONIOENCODING=utf-8 py -3 validators/run_all.py                   # dashboard
PYTHONIOENCODING=utf-8 py -3 validators/run_all.py --baseline-check  # gate (what the pre-commit hook runs)
PYTHONIOENCODING=utf-8 py -3 validators/run_all.py --update-baseline # capture new baseline after intentional changes
```

**Why this matters:** validators are on-demand reports nobody runs unless gated. With the gates, regressions block automatically — `run_all.py --baseline-check` runs in pre-commit when canon / corpus / validator files are staged, and `check_canon_extensions.py` runs in commit-msg when canon-extension patterns are detected, requiring audit-evidence keywords.

---

## Pre-implementation Adversarial-Audit Discipline (Step 0)

Before any non-trivial implementation (new validator with classification logic, new spec, new helper in `validators/_shared/`, new mechanism, new canon rule), the **FIRST tool call** in your response must be either parallel Agent dispatches for adversarial evaluation (≥2 dimensions, one message, multiple Agent tool_use blocks) **or** a one-line `Audit-skippable: <reason>` declaration citing a recognized trivial class (port of validated sibling code, mechanical ingestion change, test/fixture, runner/glue, scratch diagnostic).

**Enforcement is the hook**, not this prose. `.claude/hooks/check_bash_discipline.py` fires at batch-boundary signals (`apply_specs.py --all-books` / `apply_validators.py --all-books` / `refresh_book.py --all-books`); if <2 Agent dispatches are in the recent transcript window AND no `# audit-skippable:` override is on the command, the cascade is refused. Override comments that cite a Stan quote are quote-validated against the actual transcript (see Mechanical gates table). See `handoffs/14-operational-protocols.md §A3` for the full process and trivial-class definitions.

---

## Pre-commit Adversarial-Audit Discipline

**Before any commit that modifies `private/01-method/colometry-canon.md`, check whether the change matches a mandatory-audit trigger per canon §7.** The 12 triggers are listed in canon §7; re-read them when uncertain. If the change matches any trigger, audit evidence (hostile-agent dispatch + verdict + application) must be present in the commit message or the canon §8 Update Log entry.

**Audit-skippable.** Canon edits that do NOT match any trigger (typo fixes, cross-reference updates without precedence claims, deletions of same-session reverts, defensibility-capture additions to already-settled rules without scope changes, Category A mechanical corpus edits that are not part of a ≥5-instance sweep) proceed without audit.

**When uncertain.** Dispatch the audit. The cost of a false-positive audit (Stan reads a no-op result) is small; the cost of a false-negative audit (a bogus rule lands silently) is large.

**Required commit-message declaration.** Every commit message that touches `private/01-method/colometry-canon.md` must declare audit-status explicitly: either `Audit-skippable per §7 ([reason])` with the reason citing one of the named audit-skippable categories above, OR `Audit dispatched: [evidence]` with concrete reference (parallel-agent verdicts, §8 entry, prior-commit pointer). Omission is itself a discipline failure — visible at a glance in `git log`. The mechanical gate (`validators/hooks/commit-msg` via `check_canon_extensions.py`) detects extension patterns and requires an audit-evidence keyword; the declaration is the editor-side discipline that front-loads (and complements) the gate.

**Self-test to run pre-commit** (faster than full trigger-list scan):
- Does this change include a scope claim, a precedence claim, a closed-list extension, or a named-category carve-out? → audit.
- Does this change rest on spot-check evidence rather than a full-corpus classification? → audit.
- Does this change reclassify or delete previously-settled canon content? → audit.
- If no to all three → probably skip-safe.

**Parallelize audits by default.** When triggered, dispatch multiple audit dimensions in parallel (one message, multiple Agent tool calls). Sequential only when audit A's verdict determines whether audit B should run. Canon §7 codifies this default.

This discipline complements (does NOT replace) the **Self-consistency audit trigger** in canon §7 (when a session adds ≥2 new canon subsections, rules, or merge-overrides, run a light self-consistency audit before wrap). Pre-commit is per-change; self-consistency is session-rollup. See canon §2 Autonomy Boundary for the Category-B-by-default rule this self-test instantiates, and canon §7 for the full trigger list.

---

## Pre-flight Audit Pattern (parallel-by-default)

When the scope of a proposed change is unclear (corpus-wide impact, cross-rule precedence, methodology-touching), dispatch N parallel verification agents BEFORE executing.

**When to invoke:**
- Adding a new H-rule or M-override → dispatch hostile audit + grammar-grounding + cross-rule integrity (parallel)
- Sweep ≥5 instances under a settled rule → dispatch FP-precheck per cluster (6 agents)
- Proposing a validator → dispatch one fixture-oracle agent per regression chapter

**Pattern:** all audit dispatches go in a single message. Agents run concurrently; wall-time = max(per-agent), not sum.

**Worked example (2026-04-28 H18 codification):** 6 parallel hostile audits (tifcha-servant, verbless-clause, Wickes/Yeivin, JM/WO, Sifrei Emet danger zone, cross-rule integrity) → adjudicated → design corrected (Option A vs B) → built. Saved a wider-than-realized scope.

---

## Follow-On Rebuild Cascade (automatic)

**The cascade fires automatically on every commit that touches `data/text-files/v2/he/`.** You do not invoke it manually.

Cascade rule: **v2/he edit (staged) → pre-commit hook detects affected book(s) → `refresh_book.py --book <book> --build` → regenerated `v2/eng-interlinear/`, `v2/eng-gloss/`, `v2/translit/`, and `books/<book>/` (per-chapter files + manifest) staged and included in the same commit → validator regression gate → commit lands.**

The editor commits only the Hebrew change (`v2/he/<book>/<chapter>.txt`). Everything downstream regenerates and commits atomically. Multiple books in one commit are each rebuilt sequentially.

**Manual invocation** (when running outside a commit, e.g. after pulling):

```bash
PYTHONIOENCODING=utf-8 py -3 scripts/refresh_book.py --book 32-jonah --build
PYTHONIOENCODING=utf-8 py -3 scripts/refresh_book.py --all-books --build
```

The `PYTHONIOENCODING=utf-8` prefix is mandatory on Windows for any script touching Hebrew Unicode (combining characters, te'amim, niqqud).

---

## Two-check Post-cascade Gate

After the rebuild cascade fires (any commit touching `data/text-files/v2/he/`), both English-quality scanners must report zero warnings before the commit lands:

1. `scripts/english_quality_check.py` — eng-gloss / eng-interlinear quality (gender-marker leak, alignment, etc.)
2. `scripts/scan_english_drift.py` — drift detection across English layers vs. Hebrew structure

Pre-commit hook should run both. Mandatory zero-warning gate; deviation requires explicit `--no-verify` with Stan-approved reason.

---

## Agent Dispatch — Three-Tier Model Routing

When dispatching subagents via the Agent tool, match model to task complexity. Stan pays per-token and routing matters.

- **Haiku** (cheapest, fastest): file moves, renames, glob/ls formatting, mechanical reference lookups, single-file reads-and-summarize with no judgment, yes/no checks against file content.
- **Sonnet** (mid-tier): scanner runs where rules are already defined, quick consistency checks with narrow scope, documentation updates following a clear template, mirroring edits between files.
- **Opus** (reasoning-heavy): multi-angle adversarial audits, methodology synthesis across multiple sources, restructuring major documents, novel rule design, anything where the judgment IS the work product.

**When in doubt, Sonnet is the right default.** Reserve Opus for tasks where the reasoning quality directly determines the output's value.

---

## Corpus Cluster Splits

For corpus-wide work (validator runs, sweep audits, FP-precheck), split agents by cluster rather than running one agent on all 39 books. **Threshold rule:** any batch of ≥25 surgical fixes spanning 3+ clusters MUST be split by cluster — no exceptions.

### The 6 clusters

1. **Torah** — Genesis, Exodus, Leviticus, Numbers, Deuteronomy
2. **Former Prophets** — Joshua, Judges, 1-2 Samuel, 1-2 Kings
3. **Latter Prophets** — Isaiah, Jeremiah, Ezekiel, the 12 Minor Prophets
4. **Writings (prose)** — Ruth, Esther, Daniel, Ezra-Nehemiah, 1-2 Chronicles, Ecclesiastes prose portions
5. **Sifrei Emet (poetic)** — Psalms, Proverbs, Job 3:1–42:6
6. **Embedded Poetry (prose-routed)** — Exod 15, Deut 32, Deut 33 vv 2-29, Judg 5, 1 Sam 2:1-10, 2 Sam 22, Isa 12, Hab 3, Lam 1-5, Song of Songs, Eccl 3:2-8

The two-phase pipeline-change pattern (algorithm change in one agent → N-cluster parallel rebuild in N agents) is documented in `handoffs/14-operational-protocols.md §A2`. **Don't restate it here; the hook (A2 detection in `check_bash_discipline.py`) is what binds.**

---

## What Stan Does / What Claude Does

**Stan:**
- Makes all final editorial decisions on line breaks
- Reviews all proposed changes
- Pushes to GitHub
- Has final say on all colometric and te'amim-evidence decisions
- Decides which books / chapters to work on next

**Claude Code:**
- Proposes line-break revisions with rationale, citing te'amim and the three editorial criteria (atomic thought, single image, Hebrew syntax)
- Builds and maintains tooling (scripts, build pipeline, web app)
- Maintains documentation and handoffs
- Quantitative analysis (colon counts, accent-pattern detection, override-rate tracking)
- Never touches source text without explicit approval
- Commits when finished; Stan pushes

**Editorial-call structure rule** (when Stan names a specific verse with a specific desired partition): the next assistant turn structure is line 1 = "Got it — [Stan's reading]"; line 2-N = the diff being applied; tail = any cross-verse-class implications. NO leading analytical defense of an alternative reading. NO citation of te'amim hierarchy as authority — the te'amim are evidence per "Te'amim as Evidence", not the basis for arguing against Stan's editorial call. Analysis is value-add ONLY when Stan asks "what should it be?" — never when Stan tells me what it is. Failure shape (2026-05-04 Isa 40:3 incident, codified in `feedback_editorial_call_no_lead_analysis.md`): Stan names X; I produce 47-line analysis of why it might be Y; Stan repeats X with sharper specificity; I re-frame partially-wrong; Stan corrects again. Three round-trips on a single editorial question. Don't.

---

## Connected Resources

- **Academic vault:** `C:\vaults-nano\my_brain\` — Hebrew grammar notes, Bible book files, scholar notes. The `10_Projects\Readers\` subdirectory contains Stan's ATU (atomic thought unit) research-program orientation document and the MOC for the reader-projects family — read this for calibration on what Stan actually wants from the editorial process when the methodology canon and CLAUDE.md feel under-specified.
- **Gospel vault:** `C:\vaults-nano\gospel\` — devotional scripture notes
- **Foundational scholarly references:**
  - William Wickes, *A Treatise on the Accentuation of the Twenty-One So-Called Prose Books of the Old Testament* (1887)
  - William Wickes, *A Treatise on the Accentuation of the Three So-Called Poetical Books* (1881)
  - Israel Yeivin, *Introduction to the Tiberian Masorah* (SBL, 1980)
  - Robert Lowth, *Lectures on the Sacred Poetry of the Hebrews* (1753)
  - James Kugel, *The Idea of Biblical Poetry* (1981)
  - Adele Berlin, *The Dynamics of Biblical Parallelism* (1985)
  - F.W. Dobbs-Allsopp, *On Biblical Poetry* (Oxford, 2015)
- **Domain registrar:** Cloudflare

---

## Git Workflow

- All work on `main` branch
- Stan pushes from his local machine via GitHub Desktop
- Claude Code prepares commits but cannot push (403 proxy error)
- Stan's standing instruction: "whenever you finish, do a commit and I'll push"

### Tree-state self-check before commit (mandatory)

Before any `git add` or `git commit`, run `git status --short | wc -l` (or `--short` directly if the count is small). If the tree contains modified files you didn't author this session — especially under `data/text-files/v2/he/`, `validators/`, or `scripts/` — STOP and surface to Stan before staging. This is the failure mode that produced commit `4e1857e25` (Item Zero in the State block above): a 12-line analytics edit landed as a 4554-file commit because pre-existing staged work from a "kill everything, stop" wrap-up was in the tree and got bundled by the pre-commit cascade.

The rule: **a commit's title should describe its actual scope.** If you're about to commit work you didn't author, either (a) ask Stan first, (b) commit it separately under its own title, or (c) `git stash --keep-index` the unrelated work, commit yours, then unstash.

---

## Project Siloing

This project is **publicly independent**. No cross-references to any other projects in README, CLAUDE.md, handoffs, or any other public-facing files. The connection between this project and any sibling colometric editions exists only in `private/` and in Stan's internal knowledge. Respect this decision.

---

## Update Protocol

When updating handoff docs, append a dated block at the bottom — never overwrite history. After any session where decisions are made, principles are refined, or new patterns identified, update the relevant handoff file.

**CLAUDE.md is the load-bearing doc, not memory files.** Per the 2026-05-04 colonoscopy audit, prose memories under `~/.claude/projects/.../memory/` have a ~50% application-failure rate; the variable that correlates with adherence is surface-detectability of the trigger, not memory age or word count. **Do NOT add new memory files** — for in-session corrections, for session-rebuild work, for cross-cutting principles, for any reason. The freeze applies to all categories. If the correction warrants persistence, it lives in CLAUDE.md or `handoffs/14-operational-protocols.md` (where future-Claude reads it during CHECK-IN), or it lives in a runtime hook (where it binds mechanically). The 5 memory files added in the 2026-05-04 session were judged not-helpful by the colonoscopy audit at the same session — the pattern is well-established. The freeze stays in force until the colonoscopy-audit's TRIGGER-section migration (§3.3) is implemented; until then, prose-memory additions are a known-failed pattern.

**Rejected approaches — do not re-propose** (so future sessions don't re-derive what Stan already killed):
- **Canary-before-cluster-cascade.** Rejected 2026-05-04 with rationale "you either have tools doing the job correctly or not; quit wasting time." If the cascade engine is correct, the cascade is correct. If it's wrong, the canary doesn't save you — it just delays the discovery. Don't add canary steps to cluster-cascade workflows.
- **Adding memory files to encode behavioral discipline.** See above.

---

## Deferred Operational Work (priority order)

These are concrete next-step items surfaced by the 2026-05-04 audits and the 2026-05-05 path-forward review. Each has explicit completion criteria so a future session can pick one up without re-deriving the rationale.

1. **Phase 2 defensibility — first commit (`scripts/measure_validator_fp_rate.py`).** Write a script that takes a 500-verse fixture set (sampling frame: 100 verses per cluster from clusters 1-5, 0 from cluster 6 since embedded poetry is small enough to fixture separately later; within each cluster, stratify by book proportional to chapter count, then sample uniformly within each book), runs `apply_validators.py` in dry-run, and computes per-validator true-positive / false-positive rates against manual-review ground truth. Ground-truth file: `tests/fp-baseline-fixtures.tsv` columns (verse-id, validator-name, expected-action {APPLY, REVIEW, REJECT}, rationale-brief). Output: `validators/.fp-baseline.json` with per-validator TP/FP/uncalibrated counts. **First-commit definition.** Phase 2 is not declared until this script exists and runs clean on the fixture set; "Phase 2" without the script is a CYA pause, not a pivot.

2. **Psa 9:10 parallelism direction fix.** `validate_short_orphan_line.py` currently emits `merge_with_previous` for the M4 atomic-thought arm. For parallelism cases (gapped restatement on the next line), the correct merge is `merge_with_next`. Implement context-aware direction: if the next non-blank line is content sharing morphology/role with the prior verb's complement, prefer `merge_with_next`; if next is blank/verse-end, keep `merge_with_previous`. Single-validator change; no new validator needed (this is a bug fix within the existing arm, NOT proliferation).

3. **Scripts-vs-agents runtime hook.** **BUILT 2026-05-05** — `_agent_violations()` in `.claude/hooks/check_bash_discipline.py` (lines 215+); 13 fixture tests in `tests/test_bash_discipline_hook.py` (`AGENT_TESTS`). Detects Agent dispatches with short prompt bodies (≤2000 chars) matching mechanical-vocabulary regex (count / list all / how many / find all / enumerate / scan every / check whether / look up / pull every / return every / glob for). Bypass: prompt body starts with `# judgment-required: <reason>`. **Settings.json registration requirement:** the `.claude/settings.json` `PreToolUse.matcher` field must be `"Bash|Agent"` (not just `"Bash"`) for the hook to fire on Agent calls. settings.json is gitignored — verify on a fresh clone or after a settings reset. **Do not** build the permission-loop hook (i) or counts-headline hook (iii) until Claude Code's Stop-hook surface stabilizes around the JSONL race condition flagged by the 2026-05-05 audit.

4. **New-validator-creation guard hook.** Mechanical enforcement of the validator-extension-over-creation principle. `PreToolUse` on the **Write tool** (the surface where new files are created — NOT Bash) detects `tool_input.file_path` matching `validators/(syntax|colometry)/validate_*.py` paths; refuses unless the corresponding bypass token `# validator-extension-justified: <reason>` is present in a recent assistant message. The settings.json matcher needs to be updated to include "Write" alongside "Bash|Agent" — currently only "Bash|Agent" is registered. The principle without the hook is a memory; with the hook, it binds. Stan's standing instruction (2026-05-03 session-notes line 67): *"Stop making new validators... The dataset is finite, the grammar is finite. Proliferation creates conflicts."*

5. **GitHub Pages + GA Realtime verification (Stan-side).** Confirm Pages source-setting is `Source: Deploy from a branch / Branch: main / Folder: /`. Visit tanakh-reader.com in one tab + GA Realtime in another; click between chapters; confirm `page_view` events fire on hashchange.

6. **A standalone cascade-alignment scanner** (target name: `scripts/check_cascade_alignment.py`) — port the word-count imbalance scanner from the GNT sibling repo. Tanakh has `scan_english_drift.py` and `english_quality_check.py` already, but lacks an on-demand alignment scanner separate from the pre-commit pipeline. Adapter work: change the sibling's editorial-tier paths to use tanakh's v2/he and v2/eng-interlinear directories. Haiku-tier mechanical port; no judgment work.

Nothing in this list authorizes building a new validator, drafting a new H-rule, adding an M-override, or running a STRONG-promotion sweep. Those are out-of-scope until item 1 lands.
