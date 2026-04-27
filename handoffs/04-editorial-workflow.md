# 04 — Editorial Workflow

This document describes how a chapter moves from raw source to finished reading edition. It is a stub at scaffolding time; it will mature through the Jonah MVP pass and subsequent chapters.

## Stage 1 — Ingest (one-time per book)

Run `scripts/ingest_tahot.py` to convert the vendored STEPBible TAHOT TSV (in `research/stepbible-tahot/`) into per-chapter `v0/prose/` files.

Output convention:

- One subdirectory per book: `data/text-files/v0/prose/{NN-book}/` where `NN` is the TaNaK-order index and `book` is a slug.
- One file per chapter: `{abbr}-{NN}.txt` (e.g., `gen-01.txt`, `jonah-02.txt`).
- File contents: verse-marked plain text with full niqqud, full te'amim, ketiv/qere markers preserved, prose paragraph form (no editorial line breaks yet).

`v0-prose/` is the canonical reference. **Never edit by hand.** Re-run `ingest_tahot.py` if the upstream TAHOT vendor is updated; the regenerated v0 should match bit-for-bit unless TAHOT changed.

## Stage 2 — Generate v1 layers

Run the te'amim parser on the chapter:

- `scripts/parse_teamim.py` — handles both the prose accent system (21 prose books + Job's prose frame 1:1–2:13 and 42:7–17) and the *Sifrei Emet* accent system (Psalms, Proverbs, and Job 3:1–42:6); per-book registry routes chapters to the appropriate breaker set.

Output (in lockstep, all four parallel layers):

- `data/text-files/v1/he-baseline/{NN-book}/{abbr}-{NN}.txt` — Hebrew cola
- `data/text-files/v1/eng-interlinear/{NN-book}/{abbr}-{NN}.txt` — per-word English
- `data/text-files/v1/eng-gloss/{NN-book}/{abbr}-{NN}.txt` — naturalized English (one per cola)
- `data/text-files/v1/translit/{NN-book}/{abbr}-{NN}.txt` — per-word translit

Every line break in v1/he-baseline corresponds to a disjunctive accent at or above the threshold defined in the canon. The other three layers are 1:1-aligned to the Hebrew at the cola level.

`v1/` is machine-deterministic. Re-running the parser on identical v0 input must produce identical v1 output.

## Stage 3 — Editorial pass (the human work)

Open the v1/he-baseline file and the v0-prose file side-by-side. For each chapter, produce `data/text-files/v2/he/{NN-book}/{abbr}-{NN}.txt`.

Run the validator dashboard to get the work queue:

```bash
PYTHONIOENCODING=utf-8 py -3 validators/run_all.py
```

Findings tagged `STRONG-MERGE-CANDIDATE` or `STRONG-SPLIT-CANDIDATE` are Category A per canon §2 Mechanical-rule authority — apply confidently. Findings tagged `REVIEW-REQUIRED` need per-item editorial judgment.

**Editorial moves allowed:**

- **Merge an accent break** — e.g., the parser broke at a tifcha that the editor judges does not warrant a colon boundary. Each editorial line break must positively justify itself as containing an atomic thought, citing which of the three editorial criteria (atomic thought, single image, Hebrew syntax) and any relevant structural justification (per colometry-canon.md §1) supports the break. Te'amim agreement or disagreement is documented as evidence.
- **Insert a non-accent break** — e.g., a long colon contains two atomic thoughts that the accent system left fused. The insertion must cite which criterion warrants the additional break.
- **Adjust whitespace and verse-number formatting** for readability.

**Editorial moves not allowed:**

- Modify the consonants, niqqud, te'amim, or word order
- Add, remove, or substitute words
- Change verse numbering

Every editorial decision should be defensible against the canon. When the canon has no clear rule for a decision, that's a signal to either (a) note it for canon revision, or (b) flag it for Stan review.

## Stage 4 — Propagate parallel layers

Once v2/he/ Hebrew is settled for a chapter, re-segment the parallel per-word layers (eng-interlinear, eng-gloss, translit) to match the new cola structure:

```bash
PYTHONIOENCODING=utf-8 py -3 scripts/propagate_editorial_layers.py --book 05-jonah
```

Output: `data/text-files/v2/{eng-interlinear,eng-gloss,translit}/{NN-book}/{abbr}-{NN}.txt`. The propagator enforces a word-stream invariant — v1 Hebrew word stream MUST equal v2 Hebrew word stream (same words, same order, same count); editorial work changes only line breaks, never adds/removes/reorders words. Script exits with error on violation.

## Stage 5 — Build

Run `scripts/build_books.py` to regenerate `books/{book}.html` from `v2/` (cascade falls through to v1 for any chapter without a v2 file):

```bash
PYTHONIOENCODING=utf-8 py -3 scripts/build_books.py --book jonah
```

## Stage 6 — Validate

The validator suite under `validators/` runs on demand and at commit time (via the pre-commit hook):

- **Layer 1 (Hebrew break-legality)** — checks for syntactic patterns that should not be split (e.g., maqqef-joined words; preposition + bound noun; construct chains kept together).
- **Layer 3 (colometry)** — checks for methodology compliance (every line positively justified as an atomic thought per canon §1; no orphaned lines; balanced colon lengths within reason).

Validator output is a work queue, not a review queue (canon §6). STRONG-tagged findings are application-ready; REVIEW-REQUIRED items need per-item editorial judgment.

```bash
PYTHONIOENCODING=utf-8 py -3 validators/run_all.py                   # dashboard
PYTHONIOENCODING=utf-8 py -3 validators/run_all.py --baseline-check  # gate (what pre-commit runs)
```

## Cascade Rule

When the English gloss layer is added, the cascade is mandatory:

> **Hebrew edit → English regen → HTML rebuild → commit → push (atomic operation).**

Skipping a stage produces drift between Hebrew and English files that is hard to detect and harder to fix retrospectively. The cascade is enforced by convention; future tooling may add a pre-commit check.

## Mechanical-Merge Pattern (for systematic corrections at scale)

When a recurring colometric error class is identified across multiple books, the workflow shifts from per-chapter editing to scan-then-apply:

1. Describe the error class structurally (grammatical or prosodic signature)
2. Build a scanner in `scripts/` that finds it and cites evidence
3. Build an applier that mirrors the operation across affected files
4. Pilot on 2–3 books from different genres; verify zero residual
5. Run corpus-wide with `--save-candidates`
6. Rebuild and verify integrity
7. Commit with merge counts per book

This pattern is the default for systematic cleanup once the corpus is large enough to make per-chapter editing inefficient. For the MVP and through the first complete book, per-chapter editing is the primary mode.

## Divergence Tracking

Every divergence from the v1-he-baseline should leave a trail. The simplest convention:

- The v2/he file itself is the trail — comparing v1/he-baseline against v2/he reveals every divergence (merges of accent breaks and splits not in v1)
- A periodic sweep produces a "divergence census": count of divergences per book, per chapter, per criterion-invoked
- Divergence hot-spots (chapters with unusually high divergence rates) are candidates for canon revision — either the criteria need refinement, or the te'amim parser is producing systematic noise

Divergence rate from v1/he-baseline is a key diagnostic metric. A v2/he that diverges from te'amim breaks at >50% suggests either (a) v1/he-baseline is over-fragmenting via tifcha-as-servant (canon Rule H11) and the editor is correctly merging back, or (b) the editor's atomic-thought criterion is firing too aggressively and warrants review for canon compliance. Both cases are diagnostic, not failures per se — the te'amim are evidence, not authority. A v2/he that diverges 0% from v1/he-baseline suggests the editorial pass isn't adding value.

---

### Established — 2026-04-25 (scaffolding session)

- Workflow stages defined: ingest, parse, edit, build, validate
- Cascade rule and mechanical-merge pattern documented (carried forward from sibling-project lessons)
- Override tracking framing established as a key methodological metric
- No actual workflow runs yet; document will mature through Jonah MVP and first-book completion

---

**2026-04-26 update:** v1-teamim directory renamed to v1-he-baseline; path references updated throughout this doc to align with the canon's te'amim-as-evidence framing (no longer te'amim-as-prior).

**2026-04-26 update:** Four-tier pipeline adopted. Stages 3 and 4 (v2-he-syntax and v3-he-colometry mechanical passes) inserted between the v1 parse stage and the v4 editorial pass. Old Stages 3–5 renumbered to 5–7. v2 applies STRONG Layer 1 syntax candidates (Rules H1, H11 stranded-token); v3 applies STRONG Layer 3 colometry candidates (Rules H2, H5, H7, H16). REVIEW-REQUIRED items from both layers feed the v4 editorial work queue. The editorial pass now opens v3-he-colometry (not v1-he-baseline) as its starting draft.

**2026-04-26 update:** `data/text-files/` restructured into per-tier subfolders (v0/, v1/, v2/, v3/, v4/). Tier-name identity strings (v1-he-baseline, v2-he-syntax, etc.) unchanged; only filesystem layout. Path references in this doc updated to the new layout.

**2026-04-27 update:** Tier collapse — both 2026-04-26 multi-tier updates above are superseded. Pipeline simplified from 7 stages to **6 stages** (ingest / parse / editorial / propagate / build / validate); the auto-apply mechanical stages (old Stages 3–4) are retired. Editorial pass now opens v1/he-baseline as its starting draft and writes to `v2/he/` (was `v4/editorial/`). STRONG-tagged validator findings feed the editorial work queue directly, with the same Category A/B/C reasoning the canon already governs. Parallel per-word layers re-segmented by `propagate_editorial_layers.py` into `v2/{eng-interlinear,eng-gloss,translit}/`. See canon §8 entry 2026-04-27 for full rationale.
