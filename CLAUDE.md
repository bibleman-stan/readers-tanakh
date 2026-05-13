# Tanakh Reader — Claude Code Instructions

A colometric reading edition of the Hebrew Bible. Each line on the page is an atomic thought unit (ATU); four layers stack per Hebrew cola — Hebrew (RTL pointed) / Translit / Interlinear / KJV verbatim. Modern pill toggles archaic→modern on the English row only.

---

## Orientation reads

**MANDATORY at every wake (including short pings; compaction-resume runs from scratch):**
1. This CLAUDE.md
2. `handoffs/14-operational-protocols.md`
3. `git log --oneline -10`
4. `private/03-sessions/yyyy-mm-dd-*/pending.md` if a recent one exists

**CONSULT-ON-TRIGGER:**
- `private/01-method/colometry-canon.md` — anything touching `validators/`, `scripts/apply_*.py`, `data/text-files/v2/heb/`, syntax-reference, or rule-interpretation. Skip only for pure UX/deploy/build-tooling.
- `../atu-method/docs/apparatus.md` + `architecture.md` — English-layer work, swap-system, anything touching 4-layer integrity. Picture-shaped: what the reader sees on tanakh-reader.com when done.
- `../atu-method/docs/framework.md` — methodology, rule-design, autonomy-boundary. Authoritative cross-corpus body.
- `../atu-method/docs/change-protocol.md` — any canon revision.
- `../atu-method/docs/glossary.md` — ambiguous term (ATU, cola, anchor, swap).

**Self-report before first substantive response:** one line per mandatory file read; pending-item disposition (each = executing-now / retired-with-rationale / re-deferred-with-concrete-trigger; "awaiting Stan direction" / "until Stan re-surfaces" are drift not defers); red flags. Silent skip = orientation failure.

The JSONL at `~/.claude/projects/c--Users-bibleman-repos-readers-tanakh/<session-id>.jsonl` is the verbatim record. After compaction, grep into it. Don't write wrap artifacts / session-notes / full-transcript dumps; surface state inline. `pending.md` only for extended multi-cycle hand-offs.

---

## Editorial discipline (highest-violation surface)

### Stan-flagged verse = class-investigation directive

When Stan flags a problem at a specific verse, that's a directive to investigate the rule set, not patch the verse. Right shape:

1. Diagnose: what's the underlying class/pattern Stan's intuition is responding to?
2. **Audit yourself FIRST** — walk M1 / M2 / M3 / M4 / J1–J5 / formula-integrity / N=2 / N=3+ explicitly against the actual canon. Pay attention to **explicit exclusions** (e.g., M1 §1.5 explicitly excludes sequential narrative bonding). If the framework's existing answer is "split, this is excluded," that's a real answer — not a gap.
3. Only if step 2 finds a real gap, investigate corpus-wide.
4. **New rules trigger §7.3 adversarial audit** — ≥2 parallel agents BEFORE any engine infrastructure. NO scanner / applier / FORMULAE entry until the rule passes. Building infrastructure first is the "fake rule" failure mode.
5. If audit holds: fix at engine layer, apply mechanically corpus-wide.
6. If audit fails or framework already answers: report Stan the actual framework answer; offer Category B per-verse editorial-judgment fallback.

### Anchor in Hebrew syntax, not English-translation surface

KJV systematically smooths Hebrew wayyiqtol chains into English-idiomatic temporal subordinations ("**when** she saw") and infinitive purpose-clauses ("**to** fetch it") that don't exist in the Hebrew. Before agreeing OR disagreeing with an editorial intuition sourced from the English layer, check Macula `_morph_tag`:
- Wayyiqtols (`Vqw*` / `Vnw*` / etc.) without intervening subordinator (אִם / כִּי / כַּאֲשֶׁר / אֲשֶׁר / לְ + infinitive) = sequential narrative chain → split per framework.
- KJV's "when" / "to" / "and then" are translation choices, not Hebrew syntactic facts.

Push back on English-driven intuitions with Hebrew morph evidence ("any time it looks like i'm wrong, push back" — codified 2026-05-12).

### Editorial-call structure

When Stan names a verse with a specific desired partition: line 1 = "Got it — [Stan's reading]"; line 2-N = the diff. NO leading analytical defense of an alternative. Analysis is value-add ONLY when Stan asks "what should it be?"

### Class-fix vs instance-fix

Same FP class in 2+ specs OR 2+ validators in one session = engine-level fix at `validators/_shared/spec_runner.py` / `validators/_shared/*` / `scripts/apply_*.py`. Per-spec/per-validator guard the second time = whack-a-mole. Stan's mantra: *swat the bug class, not the instance.*

### Adversarial-audit discipline (pre-implementation)

Before non-trivial implementation (new validator with classification logic, new spec, new shared helper, new mechanism, new canon rule, **OR ANY edit to `atu-method/atu_method/*` cross-corpus shared infrastructure**), FIRST tool call must be ≥2 parallel Agent adversarial dispatches in one message OR `Audit-skippable: <named-trivial-class>`. The cascade-iteration `engine-tried` bypass is NEVER legitimate when the engine edit itself is the unaudited change.

Pre-commit on canon-touching commits: include `Audit-skippable per §7 ([reason])` OR `Audit dispatched: [evidence]`. When uncertain, dispatch.

### Apply causes regression

Revert the apply → root-cause why → fix the apply → re-attempt with integrity gate verified post-apply. Do NOT build downstream-recovery tools first. Cluster-agent "pass" reports don't substitute for the integrity gate.

### Cascade leaves corpus in known-wrong state at task-arc end

Don't park it. Either fix inline now (revert + re-cascade with corrected rules) OR explicitly retire to a follow-up commit with named verses listing the wrongness.

### Stan-escalation phrasing ("WHY are you still doing this", "stop wasting my time")

STOP iterating on the surface fix. Frame-reset to class level. Ask: what's the COMMON pattern across recent commits that I've been treating as separate instances?

---

## Methodology stack

Methodology rests on three forces operating simultaneously: **generative** (atomic thought drives line creation; J1–J5 structural justifications), **subtractive** (Hebrew syntax + complement + formula integrity trigger merges; M1–M4 merge-overrides), **diagnostic** (single image as tiebreaker). Authoritative body: [`../atu-method/docs/framework.md`](../atu-method/docs/framework.md).

**No editorial overlay has force.** Te'amim, niqqud, sof-pasuq, paseq, versification: preserved for textual fidelity, zero force in editorial decisions or defensibility-capture (canon §1, retired 2026-05-05). Sifrei Emet vs prose partition is book/chapter-membership, not runtime te'amim check. The v1-he-baseline (parse_teamim.py output) is a historical mechanical artifact, not a normative starting draft.

**Layer 3 must REVEAL not IMPOSE.** Don't add scope-exclusion carve-outs (Sifrei Emet skip, register guard, acrostic skip) — overlays are calibration evidence, not authorization. If a Layer 3 rule fires in Sifrei Emet, the question is "is the fix correct under the three criteria?" not "is Sifrei Emet exempt?"

---

## Pipeline & files

**Source text rules.** NEVER modify vendored sources in `research/`, `v0/prose/` files, Hebrew consonants/niqqud/te'amim, word counts, or adopt LXX/DSS/Samaritan readings (canon §0.1). NEVER run te'amim parsers without checking if hand-edited `v2/heb/` would be overwritten. ALWAYS work in `v2/heb/`, preserve verse-refs and Ketiv/Qere markers, use `PYTHONIOENCODING=utf-8` on Windows.

**Pipeline** (post-Wave-6 substrate, 2026-05-12):

| Tier | Directory | Engine |
|---|---|---|
| v0 | `data/text-files/v0/prose/` | `scripts/ingest_tahot.py` (raw TAHOT, never edited) |
| v1 | `data/text-files/v1/he-baseline/` | `scripts/parse_teamim.py` (historical mechanical draft) |
| v2 | `data/text-files/v2/heb/` | Stan + Claude hand-edited, single source of truth |

Per-word layers regenerated from v2/heb:
- `v2/eng-interlinear/`, `v2/translit/` ← `scripts/propagate_editorial_layers.py` (word-stream invariant: same words, same order, same count; only line breaks move)
- `v2/eng-kjv/` ← `scripts/regenerate_english.py` → `atu_method.kjv_alignment.align_verse()` (KJV 1769 verbatim per Hebrew ATU cola via Strong's-number matching against TAHOT). Renamed from `eng-gloss` 2026-05-12.

Build: `scripts/build_books.py` (v2 if present, else v1). Refresh: `PYTHONIOENCODING=utf-8 py -3 scripts/refresh_book.py --book <slug> --build`.

---

## Validators & mechanical gates

| Layer | Where | Error class |
|---|---|---|
| 1 — Hebrew grammar (universal) | `data/syntax-reference/hebrew-break-legality.md` | `[MALFORMED]` |
| 2 — Validators that enforce both | `validators/syntax/` (L1) + `validators/colometry/` (L3) | emits L1/L3 |
| 3 — Tanakh editorial methodology | `private/01-method/colometry-canon.md` | `[DEVIATION]` |

Layer 1 = permission/prohibition. Layer 3 operates within L1's permitted-either space. Mixing the two is a regression.

**Validator findings = work queue.** STRONG → mechanical apply (Category A). REVIEW-REQUIRED → per-item judgment. Walking Stan through verse-level confirmations on rule-derivative changes treats a mechanical rule as advisory; if a STRONG-tag is uncalibrated, fix the validator and re-cascade — don't gate every emission.

**Hooks** (mechanical gates — read `.claude/hooks/check_bash_discipline.py` for current behaviour, override vocabulary, and bypass syntax). The hooks self-enforce; the bypass tokens (`# judgment-required:` / `# instance-fix-justified:` / `# validator-extension-justified:` / `# audit-dispatched:`) are visible in the JSONL trace and reviewable by Stan.

`git commit --no-verify` = Stan-only explicit override. One-time setup: `bash validators/hooks/install.sh`.

---

## Default decisions (do NOT surface as menus to Stan)

| Decision point | Standing answer |
|---|---|
| Adversarial audit on non-trivial implementation | ≥2 parallel agents in one message, OR `Audit-skippable: <named-trivial-class>`. Never sequential. |
| Extending existing validator vs creating new | Extension. New = `# validator-extension-justified:` with substantive criterion only. |
| Same FP class in 2+ specs/validators in session | STOP. Engine-level fix at `validators/_shared/*` or `scripts/apply_*.py`. |
| Apply causes regression | Revert → root-cause → fix → re-apply with integrity gate. NEVER build recovery tools first. |
| Commit attempt fails | Diagnose with `git log -3` + `git status --short` BEFORE retry. Use `git commit -m "$(cat <<'EOF'...EOF)"` (NEVER `-F /dev/stdin` — Linux-only). Never run two `git commit` in parallel — they race on HEAD lock. |
| "Should I commit now or wait?" | Commit substantive work proactively; status claims AFTER commit. |
| Cascade rebuild after pipeline change | 6 parallel cluster agents; never one agent on 39 books. |
| Per-item judgment work at corpus scale | Parallel cluster-Opus dispatch (5–6 agents, one per cluster); never hand-pass. |

When outside this table, surface. When inside, dispatch the standing answer and report the result.

**Corpus clusters** (for cluster-cascade routing): Torah / Former Prophets / Latter Prophets / Writings prose / Sifrei Emet (Pss/Prov/poetic Job) / Embedded Poetry. Threshold: any batch ≥25 surgical fixes spanning 3+ clusters MUST be split.

**Agent model routing:** Haiku for mechanical lookups; Sonnet for narrow-scope scans where rules are defined; Opus for adversarial audits / methodology synthesis / novel rule design. Sonnet default; reserve Opus for reasoning-heavy work.

---

## Git workflow

All work on `main`. **Commit AND push autonomously after any clean commit on main** (Stan blanket-authorized 2026-05-11). Sequence: `git commit` → if exit 0 → `git push origin main` → THEN report.

**Confirm BEFORE push:** force-pushes; pushes to non-main; pushes containing agent-applied bulk corpus changes I haven't diff-reviewed.

**Tree-state self-check before commit (mandatory):** `git status --short`. If unrelated work is staged, separate it before committing — commit titles must describe actual scope. Either ask first, commit separately, or `git stash --keep-index`.
