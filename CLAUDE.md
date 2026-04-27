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
- **Live site:** tanakh-reader.com (planned; domain secured, GitHub Pages not yet configured)
- **Base text:** STEPBible TAHOT — CC-BY-4.0
- **User:** Stan (thebibleman77@gmail.com)
- **Stage:** scaffolding complete; no editorial text yet; MVP target is Jonah

---

## Read the Handoff Docs First

Before any substantive work, read the handoffs directory in order:

| File | Covers |
|---|---|
| `handoffs/00-index.md` | Index and update protocol |
| `handoffs/01-project-overview.md` | Vision, scholarly landscape, methodological commitments, source-text rationale |
| `handoffs/03-architecture.md` | Repo structure, build pipeline (planned), private folder convention |
| `handoffs/04-editorial-workflow.md` | How a chapter goes from raw TAHOT to gold-standard reading edition |

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
2. The most recent `private/03-sessions/yyyy-mm-dd-*/session-notes.md` (for carry-forwards and prior-session context)
3. `git log --oneline -10`

**CONSULT-ON-TRIGGER:**
- `private/01-method/colometry-canon.md` — **trigger:** ANY editorial, rule-interpretation, or methodology-touching work. **Skip when:** pure infrastructure / code / UX / deployment work with no canon touching.
- `private/README.md` — **trigger:** writing a new file under `private/` and don't already know the subdirectory layout.

**Self-report before first substantive response**: one line per mandatory file (e.g., `- CLAUDE.md: read`). A silent skip is a check-in failure.

### WRAP-UP (at session end, or when context crosses ~60%)

Produce in the session folder:

1. **`session-notes.md`** — session arc, what landed (commits), discipline observations, withdrawn proposals, carry-forwards for next session.
2. **`full-transcript.md`** — verbatim dialogue extraction from the session JSONL (dispatch a Sonnet agent with the JSONL path to stream-process).
3. **`dialogue-notes.md`** — produce only for methodology-heavy sessions where the dialogue arc itself is the work.
4. **`review-lists/`** (subfolder) — only when the session produced candidate lists requiring Stan review.

### Context-threshold discipline

- **Green zone (0–60%)**: execute normally.
- **Yellow zone (60–80%)**: start drafting `session-notes.md`; consider wrapping at natural breakpoints.
- **Red zone (80%+)**: stop new execution, wrap up.

Compaction-resume: still run the full CHECK-IN protocol when resuming from a compaction summary.

---

## Key Files

Most of these do not exist yet. They are listed so you know the planned layout when scaffolding scripts in future sessions.

| File | Purpose |
|---|---|
| `index.html` | Main web app — RTL Hebrew layout, all CSS/JS inline |
| `scripts/ingest_tahot.py` | Reads STEPBible TAHOT TSV → splits to per-book/per-chapter v0-prose files |
| `scripts/parse_teamim_prose.py` | Parses prose accent hierarchy → v1-he-baseline cola |
| `scripts/parse_teamim_poetic.py` | Parses *Sifrei Emet* accent hierarchy for Pss / Prov / Job 3:1–42:6 |
| `scripts/build_books.py` | Converts text files → HTML fragments |
| `data/text-files/v0/prose/*/` | Chapter files derived from TAHOT — **NEVER EDIT** |
| `data/text-files/v1/he-baseline/*/` | Hebrew baseline cola draft — machine-generated starting point for editorial work in v2 |
| `data/text-files/v2/he/*/` | Hand-edited Hebrew gold standard — single source of truth |
| `data/text-files/v2/eng-gloss/*/` | Structural English glosses (planned, deferred behind Hebrew MVP) |
| `books/` | Generated HTML fragment files |

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

---

## Three-Layer Validation Architecture & Mechanical Gates

Mirrors the `bibleman-stan/readers-bofm` sibling architecture (codified there 2026-04-19, ported here 2026-04-27):

| Layer | What it is | Where it lives | Validator error class |
|---|---|---|---|
| **1** | Generic Hebrew grammar surface — universal facts, language-level | `data/syntax-reference/hebrew-break-legality.md` | `[MALFORMED]` |
| **2** | Validators — enforce both layers with distinct error classes | `validators/syntax/` (L1) + `validators/colometry/` (L3) | emits L1 / L3 |
| **3** | Tanakh-specific editorial methodology | `private/01-method/colometry-canon.md` | `[DEVIATION]` |

**Discipline:** Layer 1 is a permission/prohibition surface — it catalogs what Hebrew grammar **forbids** or **permits**; it does not prescribe choices among permitted alternatives. Layer 3 operates **within** Layer 1's permitted-either space and codifies project-specific editorial calls. Mixing them in either direction is a regression. The shape cap on Layer 1's table prevents prose-creep; the `[MALFORMED]` vs `[DEVIATION]` error classes prevent confusing a syntax illegality with an editorial deviation.

### Mechanical gates (enforced by git hooks)

| Component | What it does |
|---|---|
| `validators/run_all.py` | Dashboard. Discovers all `validate_*.py`, runs each with `--json --v2`, aggregates per-validator finding counts. Modes: default (report-only), `--baseline-check` (regression gate against `validators/.baseline.json`), `--update-baseline` (capture current state). |
| `validators/.baseline.json` | Per-validator finding counts captured at the moment of last `--update-baseline`. The reference state for regression detection. |
| `.git/hooks/pre-commit` (← `validators/hooks/pre-commit`) | Fires when staged files match `data/text-files/v2/he/`, `private/01-method/colometry-canon.md`, `data/syntax-reference/`, or `validators/`. Runs `run_all.py --baseline-check`; blocks on regression (finding count INCREASED vs baseline). |
| `.git/hooks/commit-msg` (← `validators/hooks/commit-msg`) | Runs `validators/check_canon_extensions.py` on the proposed commit message. Detects canon extensions (new `Rule HN`, new `MN.` merge-override, new dated principle, closed-list table row, new §7 trigger, new SCOPE-exclusion bullet). Requires audit-evidence keyword (`audit`, `§7`, `post-codification`, etc.) OR skip-safe claim (`typo`, `formatting`, `audit-skippable`). Closes the smuggling-during-unrelated-commit failure mode. |

**Override (Stan-only, explicit decision):** `git commit --no-verify`

**One-time setup after fresh clone (or when hooks are missing):**

```bash
cp validators/hooks/pre-commit  .git/hooks/pre-commit
cp validators/hooks/commit-msg  .git/hooks/commit-msg
chmod +x .git/hooks/pre-commit .git/hooks/commit-msg
```

**Routine commands:**

```bash
PYTHONIOENCODING=utf-8 py -3 validators/run_all.py                   # dashboard
PYTHONIOENCODING=utf-8 py -3 validators/run_all.py --baseline-check  # gate (what the pre-commit hook runs)
PYTHONIOENCODING=utf-8 py -3 validators/run_all.py --update-baseline # capture new baseline after intentional changes
```

**Why this matters:** validators are on-demand reports nobody runs unless gated. With the gates, regressions block automatically — `run_all.py --baseline-check` runs in pre-commit when canon / corpus / validator files are staged, and `check_canon_extensions.py` runs in commit-msg when canon-extension patterns are detected, requiring audit-evidence keywords.

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

## Build Pipeline (planned)

The cascade rule (once English layer exists): **Hebrew edit → English regen → HTML rebuild**.

For the Hebrew-only MVP: **Hebrew edit → HTML rebuild**.

Scripts will live in `scripts/`. Run them with:

```bash
PYTHONIOENCODING=utf-8 py -3 scripts/<script>.py
```

The `PYTHONIOENCODING=utf-8` prefix is mandatory on Windows for any script touching Hebrew Unicode (combining characters, te'amim, niqqud).

---

## Agent Dispatch — Three-Tier Model Routing

When dispatching subagents via the Agent tool, match model to task complexity. Stan pays per-token and routing matters.

- **Haiku** (cheapest, fastest): file moves, renames, glob/ls formatting, mechanical reference lookups, single-file reads-and-summarize with no judgment, yes/no checks against file content.
- **Sonnet** (mid-tier): scanner runs where rules are already defined, quick consistency checks with narrow scope, documentation updates following a clear template, mirroring edits between files.
- **Opus** (reasoning-heavy): multi-angle adversarial audits, methodology synthesis across multiple sources, restructuring major documents, novel rule design, anything where the judgment IS the work product.

**When in doubt, Sonnet is the right default.** Reserve Opus for tasks where the reasoning quality directly determines the output's value.

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

---

## Connected Resources

- **Academic vault:** `C:\vaults-nano\my_brain\` — Hebrew grammar notes, Bible book files, scholar notes
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

---

## Project Siloing

This project is **publicly independent**. No cross-references to any other projects in README, CLAUDE.md, handoffs, or any other public-facing files. The connection between this project and any sibling colometric editions exists only in `private/` and in Stan's internal knowledge. Respect this decision.

---

## Update Protocol

When updating handoff docs, append a dated block at the bottom — never overwrite history. After any session where decisions are made, principles are refined, or new patterns identified, update the relevant handoff file.
