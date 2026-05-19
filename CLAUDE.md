# Tanakh Reader — Claude Code Instructions

A colometric reading edition of the Hebrew Bible. Each line on the page is an atomic thought unit (ATU); four layers stack per Hebrew cola — Hebrew (RTL pointed) / Translit / Interlinear / KJV verbatim. Modern pill toggles archaic→modern on the English row only.

---

## Orientation reads

**MANDATORY at every wake:**

1. This CLAUDE.md
2. `git log --oneline -10`
3. `directives/pending/` (if any files present)

**CONSULT-ON-TRIGGER (read only when the trigger fires):**

| File / dir | Trigger |
|---|---|
| `../atu-method/docs/framework.md` | Any methodology / rule-design / canon-touching question |
| `../atu-method/docs/binding-rules-hebrew.md` | Any work on the binding-rule catalog (B1-B14) |
| `../atu-method/docs/toolset-architecture.md` | Pipeline implementation (v0→v3 stages) |
| `../atu-method/docs/apparatus.md` | English-layer work, swap-system, 4-layer integrity |
| `validators/_shared/macula_constituents.py` | Hebrew-side or Hebrew-derived question (Macula is the syntactic primitive) |
| `research/atu-pilot-mechanical-first/` | Current authoritative pipeline implementation |
| `private/01-method/colometry-canon.md` | Tanakh-specific operational details (slimmed; main methodology lives in atu-method) |

**Self-report before first substantive response**: one line per mandatory file read; pending-item disposition; red flags. Silent skip = orientation failure.

**Compaction-resume**: per `../atu-method/memories/feedback_compaction_resume_protocol.md`, after orientation reads, read the last 20-30 user↔assistant turns from the session JSONL verbatim.

**Directive-queue**: per `../atu-method/memories/feedback_directive_protocol.md`, on wake, after orientation reads, check `directives/pending/` for files in commit-order. Process each in turn: read, execute, write reply at `directives/replies/<same-name>.md`, move processed directive to `directives/processed/<same-name>.md`, commit + push per directive.

---

## Production pipeline (mechanical-first)

ATU rendering uses the **mechanical-first pipeline** specified in `../atu-method/docs/framework.md` §3 and `../atu-method/docs/toolset-architecture.md`. Implementation reference at `research/atu-pilot-mechanical-first/`.

**Pipeline stages:**

```
v0  Source text (data/text-files/v0/prose/{book-folder}/{book-stem}.txt)
  ↓
v1  BHSA clause-atom extraction via Text-Fabric
  ↓
v1.5  14 binding rules applied (B1-B14, B4 retired)
        See ../atu-method/docs/binding-rules-hebrew.md
  ↓
v2  (Optional) Narrow-task LLM adjudication on residuals
  ↓
v3  Editorial review → final ATU rendering committed to data/text-files/v2/heb/
```

**Validation status** (per `../atu-method/docs/framework.md` §5): four chapters / four genres tested. Boundary F1 stays 85-91% across narrative, poetic, and casuistic Hebrew. Pipeline output is an editorially-refinable draft requiring 5-25% absorption depending on genre.

**To run on a new chapter**: edit `research/atu-pilot-mechanical-first/pilot_config.py` (5 lines: BOOK_NAME, CHAPTER_NUM, BOOK_FOLDER, BOOK_FILE_STEM, CHAPTER_DISPLAY), then run `build_baseline_docx.py` → `v1_extract_clauses.py` → `v1_5_apply_bindings.py`.

---

## Legacy infrastructure (retained for reference)

The May-17 Stage-1/2/3 pipeline at `scripts/atu_pipeline/` (Opus 3-pass + 26-entry constraint catalog) is **retired**. It is preserved on disk for reference and historical commits but no longer the authoritative pipeline. New work uses the mechanical-first pipeline above.

Specifically retired:
- `scripts/atu_pipeline/render_atus.py` (Stage 1 Opus 3-pass)
- `scripts/atu_pipeline/audit_constraints.py` (Stage 2 constraint catalog)
- `scripts/atu_pipeline/checks_*.py` (5 cluster check modules)
- `canon/constraint_catalog_v1.md` (26-entry catalog)

**Do not extend these.** All canon-touching work goes through `../atu-method/docs/binding-rules-hebrew.md` and the pilot scripts.

---

## Editorial discipline

### Stan-flagged verse = class-investigation directive

When Stan flags a problem at a specific verse:

1. Diagnose: what's the underlying class/pattern?
2. **Audit yourself first** — walk the bidirectional test + restrictive-relative binding + the relevant binding rules (per `../atu-method/docs/framework.md §2` and `binding-rules-hebrew.md`) against the actual case.
3. Only if step 2 finds a real gap, investigate corpus-wide.
4. If a new binding rule is needed: follow `binding-rules-hebrew.md` §"Adding a rule" — identify BHSA features, justify via bidirectional test, retest against the validated chapter set (Gen 22 / Psalm 1 / Isaiah 53 / Lev 11), no regression allowed.

### Anchor in Hebrew syntax, not English-translation surface

KJV systematically smooths Hebrew wayyiqtol chains into English-idiomatic temporal subordinations ("**when** she saw") and infinitive purpose-clauses ("**to** fetch it") that don't exist in the Hebrew. Before agreeing OR disagreeing with an editorial intuition sourced from the English layer, check Macula `_morph_tag`:
- Wayyiqtols (`Vqw*` / `Vnw*` / etc.) without intervening subordinator = sequential narrative chain → split per framework.
- KJV's "when" / "to" / "and then" are translation choices, not Hebrew syntactic facts.

### Editorial-call structure

When Stan names a verse with a specific desired partition: line 1 = "Got it — [Stan's reading]"; line 2-N = the diff. No leading analytical defense of an alternative. Analysis is value-add ONLY when Stan asks "what should it be?"

### Cascade integrity

`apply_validators.py` causes regression: revert → root-cause → fix → re-apply with integrity gate. Do NOT build downstream-recovery tools first.

Cascade leaves corpus in known-wrong state at task-arc end: either fix inline now (revert + re-cascade with corrected rules) OR explicitly retire to a follow-up commit with named verses listing the wrongness.

---

## Source text rules

NEVER modify vendored sources in `research/`, `data/text-files/v0/prose/` files, Hebrew consonants/niqqud/te'amim, word counts, or adopt LXX/DSS/Samaritan readings. ALWAYS work in `data/text-files/v2/heb/`, preserve verse-refs and Ketiv/Qere markers, use `PYTHONIOENCODING=utf-8` on Windows.

**No editorial overlay has force.** Te'amim, niqqud, sof-pasuq, paseq, versification: preserved for textual fidelity, zero force in editorial decisions. The v1 he-baseline is a historical mechanical artifact, not a normative starting draft.

---

## File layout

```
data/text-files/
  v0/prose/         ← raw TAHOT verse-level (never edited)
  v0/translit-baseline/  ← verse-level transliteration
  v1/he-baseline/   ← historical (parse_teamim.py output; not used by new pipeline)
  v2/heb/           ← hand-edited final, single source of truth
  v2/eng-interlinear/ + v2/translit/  ← regenerated from v2/heb via propagate_editorial_layers.py
  v2/eng-kjv/       ← KJV 1769 verbatim per ATU cola via Strong's matching (regenerate_english.py)

books/              ← HTML output (build_books.py)

research/atu-pilot-mechanical-first/  ← CURRENT authoritative ATU pipeline implementation
scripts/atu_pipeline/                 ← LEGACY Stage-1/2/3 pipeline (retired)
validators/                           ← Pre-commit gates + Macula query helpers
private/01-method/colometry-canon.md  ← Tanakh-specific operational notes (slimmed)
canon/                                ← Legacy constraint catalog (retired; see atu-method/docs/binding-rules-hebrew.md)
directives/                           ← Cross-repo coordination queue
```

**Build cascade**: `PYTHONIOENCODING=utf-8 py -3 scripts/refresh_book.py --book <slug> --build` runs `apply_validators.py → propagate_editorial_layers.py → regenerate_english.py → build_books.py` with the regression-gate enforced.

---

## Default decisions (don't surface as menus to Stan)

| Decision point | Standing answer |
|---|---|
| New binding rule needed | Follow `binding-rules-hebrew.md` §"Adding a rule" — BHSA features + bidirectional-test justification + retest the validated chapter set. No regression = ship; regression = revise or reject. |
| Adversarial audit on non-trivial implementation | ≥2 parallel agents in one message, OR `Audit-skippable: <named-trivial-class>`. Never sequential. |
| Apply causes regression | Revert → root-cause → fix → re-apply with integrity gate. NEVER build recovery tools first. |
| Commit attempt fails | Diagnose with `git log -3` + `git status --short` BEFORE retry. Use `git commit -m "$(cat <<'EOF'...EOF)"`. Never two `git commit` in parallel. |
| "Should I commit now or wait?" | Commit substantive work proactively; status claims AFTER commit. |
| Per-item judgment work at corpus scale | Parallel cluster dispatch (5-6 agents, one per cluster). **Default Sonnet** for rule-defined work; Opus only for novel-structure work. |

**Corpus clusters** (for cluster-cascade routing): Torah / Former Prophets / Latter Prophets / Writings prose / Sifrei Emet (Pss/Prov/poetic Job) / Embedded Poetry.

**Agent model routing — frugal-default** (Stan 2026-05-15: *"be smarter and more frugal about using the correct level of model"*):

- **Haiku** when work is mechanical: file lookups, set-membership, template fills, regex-shaped fuzzy queries.
- **Sonnet** for per-instance judgment within a defined rule: per-verse classification, cluster-cascade verse audits.
- **Opus** only when the structure must be generated: adversarial audits, methodology synthesis, novel rule design.

**ATU rendering at scale uses the mechanical-first pipeline (no Opus needed at v1.5). v2 LLM adjudication, if invoked, is narrow-task per-group (Opus 3-pass on residuals only).**

---

## Git workflow

All work on `main`. Commit AND push autonomously after any clean commit on main (Stan blanket-authorized 2026-05-11). Sequence: `git commit` → if exit 0 → `git push origin main` → THEN report.

**Confirm BEFORE push**: force-pushes; pushes to non-main; pushes containing agent-applied bulk corpus changes I haven't diff-reviewed.

**Tree-state self-check before commit (mandatory)**: `git status --short`. If unrelated work is staged, separate it before committing — commit titles must describe actual scope. Either ask first, commit separately, or `git stash --keep-index`.
