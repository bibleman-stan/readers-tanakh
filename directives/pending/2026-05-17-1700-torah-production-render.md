# Torah render — production cycle (Opus 3-pass)

## Dependency

Depends on directive `2026-05-17-1500-ground-up-rebuild-architecture.md` completing Items 1-3:

- Item 1: Hebrew Constraint Catalog
- Item 2: MVP pipeline build (`scripts/atu_pipeline/`)
- Item 3: Rubric v0.2 with calibration items incorporated

**Do not begin Torah render until 1500 Items 1-3 are merged.** The directive queue protocol will process 1500 first since it was committed first.

## Scope

Torah — Genesis through Deuteronomy. 187 chapters, ~5,852 verses.

## Per-chapter protocol

Per `../atu-method/docs/toolset-architecture.md` §Stage 1:

1. **Stage 1** — Opus 3-pass with agreement scoring. Unanimous (3/3) verdicts auto-apply; non-unanimous flagged.
2. **Stage 2** — Constraint catalog audit (hard gate). Violations join the editorial-review surface.
3. **Stage 3** — Editorial-review-surface file written; final rendering NOT committed until Stan adjudicates.

Output: `data/text-files/v2/heb/01-genesis/genesis-NN.txt` etc.

## Book sequence

Canonical order:

1. Genesis (50 chapters)
2. Exodus (40)
3. Leviticus (27)
4. Numbers (36)
5. Deuteronomy (34)

## Batch granularity for editorial review

**Surface in batches of 5-10 chapters at a time** — not whole books at once. After each batch, surface to Stan as a single editorial-review pass. Wait for Stan adjudication before continuing the next batch.

Per-batch surface file: `directives/replies/2026-05-17-1700-torah-batch-<book>-NN-MM.md` (e.g., `2026-05-17-1700-torah-batch-genesis-01-10.md`).

## Existing renderings — cross-check, don't re-render

- **Deut 6** (commit `6933d793f`): cross-check new pipeline output against existing rendering; preserve where matching, surface divergences.

## Per-batch reporting

Each batch reply contains:

- Per-chapter unanimous % / majority % / all-disagree %
- Total ATU count + delta vs. source rendering
- Verses flagged for editorial review (non-unanimous + constraint violations)
- Failure-mode classes that recurred
- Chapters with unusual disagreement rates (>50% non-unanimous) — flag for special attention

Commit + push after each batch (rendered files + reply).

## Out of scope

- Non-Torah Tanakh books — separate directive after Torah validates the production workflow.
- Stage 2 constraint catalog construction — directive 1500 owns this.
- Re-rendering Ps 1 baseline — not in Torah, already validated.

## Audit triggers

Audit-skippable per §7.4 — mechanical execution of an already-audited production protocol (per `../atu-method/memories/feedback_production_tier_empirical.md`). Per-chapter 3-pass agreement scoring + Stage 2 constraint catalog audit IS the audit, structurally.

## Pre-staged resources

Grammar references staged at `research/grammars/` (pre-fetched per parallel work). Macula trees at `research/macula-hebrew/` already in place. Use both as resources for the production runs.
