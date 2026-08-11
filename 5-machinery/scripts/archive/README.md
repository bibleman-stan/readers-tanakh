# Archived Scripts

This directory holds 5-machinery/scripts that are no longer in active use but are preserved for provenance.

## Conventions

- Script moved here when its output is now produced by another path (e.g., a tier collapsed, an editor took over the surface)
- One-line entry per archived script with the date + reason
- Active vs. vestigial boundary stays visible — future sessions don't waste cycles asking "is this still used?"

## Archived

### 2026-05-16 — first archival wave (6 5-machinery/scripts)

Categorized via the 2026-05-16-2204-scripts-readme-finalize directive. Reasoning:
- Apply 5-machinery/scripts that ran a one-time corpus cascade and have no further work to do (the cascade landed; the validator/canon now enforces the pattern; re-running is unnecessary).
- HPar extraction + review tools that fed the dormant-lexicon work (1-method/canon §1 M1 codified BONDED_LEMMA_PAIRS as reference-only dormant 2026-05-16).
- One revert utility (infrastructure-class; re-promote to `5-machinery/scripts/` if recurring need emerges).

| Script | Reason | Active alternative |
|---|---|---|
| `apply_anaphoric_frame_merge.py` | One-time cascade applied 2026-05-13 to merge 13 wayehi+anaphoric-frame verses; 1-method/canon §5 H19 retracted same-day per gnt-reader precedent (bidirectional ATU test is diagnostic, not precedence override). No further apply work. | Per-verse Cat-B editorial review (no validator) |
| `apply_formula_integrity_merge.py` | One-time Gen 1 day-formula cascade. Canon §1 formula-integrity now enforces via `5-machinery/validators/colometry/validate_*` family. | Validator-driven Cat-A apply |
| `apply_hpar_high_confidence.py` | One-time Hpar high-confidence cascade. Hpar findings still emit via `validate_parallel_clause_split.py`; mechanical apply now via main `apply_validators.py`. | `apply_validators.py` |
| `apply_revert_lines.py` | Revert utility (TSV-driven line-merge revert). Used when an audit identifies an over-split cola; not part of the regular pipeline. Re-promote to `5-machinery/scripts/` if recurring use. | Manual edit + `refresh_book.py --build` |
| `extract_hpar_high_confidence.py` | One-time extract producing `data/syntax-reference/hpar-high-confidence.tsv` from the Hpar cascade run. The TSV is stable artifact; no re-extraction planned. | n/a |
| `format_hpar_review.py` | One-time review formatter producing `data/syntax-reference/hpar-high-confidence-review.md` for Stan review. Review completed. | n/a |
