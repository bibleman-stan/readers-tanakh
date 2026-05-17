# scripts/README finalize — 4 Stan-confirmed dispositions

## Context

The prior directive `2026-05-16-1500-three-gaps-and-scholarship.md` Item 5 surveyed 38 scripts in `scripts/` and surfaced 4 questions for Stan-decision (see reply at `directives/replies/2026-05-16-1500-three-gaps-and-scholarship.md`).

Stan has reviewed and returned dispositions:

1. **27-script KEEP set confirmed** (10 pipeline + 10 diagnostic + 6 validator-meta + 1 fixture-test)
2. **Apply scripts**: archive `apply_revert_lines.py`; KEEP `apply_multi_finite_verb_strong.py`
3. **Hendiadys lexicon builders**: KEEP in `scripts/` as dormant-lexicon reference tools
4. **README format**: confirmed (stage-mapping table + diagnostics section + per-archive-script disposition history + per-active-script one-liner)

## Items

1. **Archive moves** via `git mv`:
   - `apply_revert_lines.py` → `scripts/archive/`
   - The 5 historical apply scripts identified in the prior reply → `scripts/archive/` (excluding `apply_multi_finite_verb_strong.py` which stays)
   - The 2 HPar one-time extracts → `scripts/archive/`
   - Any other ARCHIVE-candidates from the prior categorization

2. **Reasoning notes** on the two split decisions (record inline in the archive README or commit message):
   - `apply_revert_lines.py` archived: revert utilities are infrastructure-class (use when needed), not pipeline-class. Re-promote if recurring use emerges.
   - `apply_multi_finite_verb_strong.py` kept: multi-finite-verb merge is a recurring corpus pattern; tool retains operational value.

3. **Write `scripts/README.md`** per the confirmed format:
   - Top: brief purpose statement + stage-mapping table (Stages 1-6 + apply phases)
   - Stage section: per-stage list of pipeline scripts + one-liner
   - Diagnostics section: per-script one-liner for the 10 active diagnostic scripts
   - Validator-meta section: per-script one-liner for the 6 validator-meta scripts
   - Fixture section: the 1 fixture-test script
   - Reference tools section: hendiadys lexicon builders + any other dormant-lexicon tools (note they're dormant)

4. **Update `scripts/archive/README.md`** with the new arrivals organized by archival category (historical apply / HPar one-time / revert utility / etc.) — match BoFM/GNT precedent in convention.

5. **Commit cleanly.** Single commit OR per-archive-category commits — your judgment. Bundled is acceptable since this is navigability cleanup.

## Reporting

Reply at `directives/replies/2026-05-16-2204-scripts-readme-finalize.md`:
- Commit hash(es)
- List of archived scripts with destination paths
- New `scripts/README.md` summary (table of contents only; full file in repo)
- Any edge cases or surprises encountered

## Audit triggers

Navigability / infrastructure. No validator changes. No rule changes. Audit-skippable per §7.4.
