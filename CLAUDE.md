# Tanakh Reader — Claude Code Instructions

Read this file completely before doing anything in this repo. It is your orientation document for every session.

---

## What This Project Is

A colometric reading edition of the Hebrew Bible (Tanakh). The Masoretic Text is reformatted from standard prose paragraphs into **sense-lines (cola)** — each line a natural breath unit based on Hebrew prosodic and grammatical structure, designed for oral delivery and comprehension.

The methodology has two foundations:

1. **The te'amim (cantillation accents) are the structural prior.** The disjunctive accents form a four-tier hierarchy that already encodes Masoretic sense-unit boundaries. Two parsers are required: one for the prose accent system (used by 21 books) and one for the *Sifrei Emet* poetic accent system (Psalms, Proverbs, and Job 3:1–42:6).

2. **Four override criteria, applied with burden of proof.** Departures from accent-induced breaks must be warranted by atomic-thought, single-image, breath-unit, or Hebrew-syntax considerations. An accent disagreement is a flag, not a license.

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
| `scripts/parse_teamim_prose.py` | Parses prose accent hierarchy → v1-teamim baseline cola |
| `scripts/parse_teamim_poetic.py` | Parses *Sifrei Emet* accent hierarchy for Pss / Prov / Job 3:1–42:6 |
| `scripts/build_books.py` | Converts text files → HTML fragments |
| `data/text-files/v0-prose/*/` | Chapter files derived from TAHOT — **NEVER EDIT** |
| `data/text-files/v1-teamim/*/` | Te'amim-driven baseline — machine-deterministic |
| `data/text-files/v4-editorial/*/` | Hand-edited gold standard — single source of truth |
| `data/text-files/eng-gloss/*/` | Structural English glosses (planned, deferred behind Hebrew MVP) |
| `books/` | Generated HTML fragment files |

---

## CRITICAL: Source Text Rules

Multiple free Hebrew-text editions are vendored in `research/` (gitignored): STEPBible TAHOT (primary, Leningrad), OSHB and UXLC (Leningrad transcription cross-checks), MAM (Aleppo tradition reference). The **primary** that feeds `data/text-files/v0-prose/` is currently TAHOT; the others are cross-references and not part of the build pipeline. See `handoffs/03-architecture.md` for the full source table.

**NEVER:**
- Modify any vendored source file in `research/`
- Modify a `v0-prose/` file
- Alter the Hebrew consonants, niqqud, or te'amim
- Add or remove words
- Adopt readings from non-vendored versions (LXX, DSS, Samaritan, Targums, Peshitta, Vulgate) into source files — see textual-posture statement in `private/01-method/colometry-canon.md §1.1`
- Run te'amim parsers without checking if hand-edited chapters in `v4-editorial/` will be overwritten

**ALWAYS:**
- Work in `v4-editorial/` — the only editorial tool is where lines break
- Present proposed changes for review before finalizing
- Preserve verse references and Ketiv/Qere markers for alignment with standard editions
- Use `PYTHONIOENCODING=utf-8` when running Python scripts on Windows (Hebrew Unicode)

---

## Te'amim-Prior Discipline

The te'amim are the project's spine. Two operating rules:

1. **Every editorial line break should be either (a) accent-induced or (b) explicitly justified as an override.** A `v4-editorial/` line break that matches no disjunctive accent and has no documented override warrant is a defect.

2. **Override warrants live in the canon.** The four criteria (atomic thought, single image, breath unit, Hebrew syntax) are not free-floating intuitions — each override should cite which criterion is invoked and why the accent system is wrong here. The canon documents the recurring override patterns as they're discovered.

This is the project's principal differentiator from prior critical editions and the source of its methodological defensibility.

---

## Tier Discipline

Start with **v0 → v1-teamim → v4-editorial** only. Defer v2 (BHSA syntax-tree refinements) and v3 (rhetorical/parallelism patterns) until they earn their existence.

The GNT project (sibling Greek edition; not referenced publicly) iterated through five tiers and discovered that v2 and v3 mechanical layers introduced 10–12% error rates that v4 had to fix. The Tanakh project starts lean and adds tiers only when they demonstrably improve v4 input quality.

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
- Has final say on all colometric and te'amim-override decisions
- Decides which books / chapters to work on next

**Claude Code:**
- Proposes line-break revisions with rationale, citing te'amim and override criteria
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
