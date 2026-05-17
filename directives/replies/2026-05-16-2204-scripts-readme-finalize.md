# scripts/README finalize — reply

## Per-item status

### 1. Archive moves — completed

6 scripts moved to `scripts/archive/` via `git mv`:

| Script | Destination | Category |
|---|---|---|
| `apply_anaphoric_frame_merge.py` | `scripts/archive/` | one-time cascade (H19 retraction 2026-05-13) |
| `apply_formula_integrity_merge.py` | `scripts/archive/` | one-time cascade (Gen 1 day-formula) |
| `apply_hpar_high_confidence.py` | `scripts/archive/` | one-time cascade (Hpar) |
| `apply_revert_lines.py` | `scripts/archive/` | revert utility — re-promote if recurring use emerges |
| `extract_hpar_high_confidence.py` | `scripts/archive/` | one-time extract |
| `format_hpar_review.py` | `scripts/archive/` | one-time review formatter |

`apply_multi_finite_verb_strong.py` retained in `scripts/` per Stan disposition.

### 2. Reasoning notes — recorded in `scripts/archive/README.md`

Per-script reasoning table added inline (matches the convention requested). Both split decisions documented:
- `apply_revert_lines.py` archived: revert utilities are infrastructure-class, not pipeline-class
- `apply_multi_finite_verb_strong.py` kept: multi-finite-verb merge remains recurring corpus pattern

### 3. `scripts/README.md` written — completed

Structure:
- **Pipeline stages** — table mapping Stages 1–6 + orchestrators + apply phases to scripts
- **Diagnostic scripts** — 10-row table with per-script one-liner (canon-§5-referenced scanners marked)
- **Validator-meta scripts** — 6-row table (FP-rate, cluster sampling, KJV spot-audit, etc.)
- **Fixture tests** — `test_h3_distinct_subject_signature.py`
- **Reference tools — dormant-lexicon builders** — 2 hendiadys lexicon builders with M1 dormancy context
- **Apply tools (active, not archived)** — `apply_multi_finite_verb_strong.py` with kept-rationale
- **Archived scripts** — pointer to `archive/README.md`

Total: 30 active scripts + 6 archived = 36 .py files (matches `scripts/` inventory).

### 4. `scripts/archive/README.md` — updated

Added "2026-05-16 — first archival wave (6 scripts)" section with per-script reason + active-alternative columns, matching the convention from the existing "Archived" section header.

### 5. Commit — single coherent commit

Single commit landing all 6 git-mv operations + both READMEs (per directive item 5 authorization "bundled is acceptable since this is navigability cleanup").

## Edge cases / surprises

None of note. The `git mv` operations preserved file content; `git status --short` confirms all 6 moves recognized as renames (R prefix). No code references to the archived scripts in active `scripts/` files were found (the archived scripts are leaf-of-tree utility scripts).

## Audit triggers

Navigability / infrastructure per directive. Audit-skippable §7.4.
