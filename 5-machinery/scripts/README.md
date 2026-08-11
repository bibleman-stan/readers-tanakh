# 5-machinery/scripts/ — Tanakh Reader Tooling

This directory carries the pipeline 5-machinery/scripts, diagnostic scans, validator-meta tools, fixture 5-machinery/tests, and dormant-lexicon reference builders for the Tanakh reader. Scripts no longer in regular use live in [`5-machinery/scripts/archive/`](archive/) for provenance.

## Pipeline stages

The canonical editorial pipeline runs Stages 1–6. Per-stage detail in [`3-project/02-text-editorial.md`](../handoffs/04-editorial-workflow.md).

| Stage | Script | Purpose |
|---|---|---|
| 1 — Ingest (one-time per book) | `ingest_tahot.py` | Convert STEPBible TAHOT TSV into per-chapter `v0/prose/` files |
| 2 — Generate v1 layers | `parse_teamim.py` | Te'amim parser → v1 he-baseline + interlinear + gloss + translit (historical mechanical artifact; 1-method/canon §1 retired te'amim consultative role 2026-05-05) |
| 4a — Propagate per-word layers | `propagate_editorial_layers.py` | Re-segment translit + eng-interlinear to v2/heb token boundaries (word-stream invariant enforced) |
| 4b — Regenerate KJV English | `regenerate_english.py` | KJV 1769 verbatim per Hebrew ATU cola via Strong's-number matching (atu_method.kjv_alignment) |
| 5 — Build | `build_books.py` | Regenerate `books/{book}.html` from v2 (cascade falls through to v1 for unedited chapters) |
| Orchestrator | `refresh_book.py` | Stages 4a + 4b + 5 atomically (called by pre-commit hook) |
| Full pipeline | `run_full_pipeline.py` | End-to-end orchestrator from v0 → v2 → built HTML |
| 6 — Validate | `run_validators.py` | Validator-suite runner (preferred entry point: `5-machinery/validators/run_all.py`) |
| Apply | `apply_validators.py` | Cat-A mechanical apply from STRONG validator findings (registry: `ADOPTED_VALIDATORS` + `ALL_VALIDATORS`) |
| Apply (spec-driven) | `apply_specs.py` | YAML-spec-driven apply via `5-machinery/validators/_shared/spec_runner.py` |

## Diagnostic 5-machinery/scripts

Standalone scanners that surface rule-class candidates or audit drift across the corpus. Run on-demand during 1-method/canon revision or validator development.

| Script | Purpose |
|---|---|
| `scan_multi_finite_verb_line.py` | Hmfv scanner — surfaces multi-finite-verb lines (1-method/canon §5 H3 corpus-evidence rule) |
| `audit_anaphoric_frame_macula.py` | Detector for the 13-verse anaphoric-frame Cat-B editorial set (1-method/canon §5 H19 retraction evidence) |
| `scan_construct_chain_breaks.py` | Surface construct-chain breaks (1-method/canon §5 H2) |
| `scan_atomic_thought_violations.py` | M4 atomic-thought-fragment scanner |
| `scan_english_drift.py` | English-layer vs Hebrew-layer drift detection |
| `scan_under_broken.py` | Under-broken case surfacer |
| `audit_morphology_vs_tahot.py` | Cross-check morphology helpers against TAHOT tags |
| `check_cascade_alignment.py` | Post-cascade misalignment warning checker (v2 eng-interlinear vs v2 heb) |
| `trace_verse_cascade.py` | Trace a specific verse through the cascade pipeline |
| `triage_validator_findings.py` | Triage utility for validator finding queues |

## Validator-meta 5-machinery/scripts

Tools used during validator FP-rate measurement, cluster-cascade work, and infrastructure-level quality work.

| Script | Purpose |
|---|---|
| `measure_validator_fp_rate.py` | Measure validator FP rates against gold-standard fixtures |
| `sample_findings_by_cluster.py` | Cluster-cascade sampling tool (per CLAUDE.md cluster routing) |
| `classify_hpar_findings.py` | Parallel-clause-split (Hpar) finding classifier |
| `spot_audit_kjv_distribution.py` | KJV distribution spot-audit (reusable infra per CLAUDE.md sample-audit-before-cascade discipline) |
| `verify_kjv_distribution.py` | KJV distribution diff verifier (engine-change verification) |
| `quality_dashboard.py` | Cross-corpus quality dashboard rendering |

## Fixture 5-machinery/tests

Standalone test fixtures (kept in `5-machinery/scripts/` rather than `5-machinery/tests/` per current convention).

| Script | Purpose |
|---|---|
| `test_h3_distinct_subject_signature.py` | Fixture for proposed AC §3.5.4(a) distinct-subject interruption STRONG-promotion signature (1-method/canon §5 H3) |

## Reference tools — dormant-lexicon builders

These build the BONDED_LEMMA_PAIRS lexicon at `data/syntax-reference/hendiadys-lexicon.tsv` (88-pair set; 1-method/canon §1 M1 closed-list dormancy codified 2026-05-16 — kept for potential future activation if a context-discrimination protocol is built). Rerun only when source data updates.

| Script | Purpose |
|---|---|
| `build_hendiadys_lexicon.py` | Phase A: ingest door43 unfoldingWord Translation Notes → lexicon TSV |
| `extract_hendiadys_lemma_pairs.py` | Extract finite-verb lemma pairs from verse-keyed lexicon via Macula clause-walking |

## Apply tools (active, not archived)

| Script | Purpose | Note |
|---|---|---|
| `apply_multi_finite_verb_strong.py` | Apply Hmfv STRONG-SPLIT findings to v2/heb as cola splits | Kept (multi-finite-verb merge is a recurring corpus pattern) |

## Archived 5-machinery/scripts

See [`archive/README.md`](archive/) for per-script disposition history. Currently archived (2026-05-16):
- 3 one-time cascade-apply 5-machinery/scripts (anaphoric-frame H19 / formula-integrity Gen 1 / hpar high-confidence)
- 1 revert utility (re-promote if recurring use emerges)
- 2 HPar one-time extracts (extract + review formatter)
