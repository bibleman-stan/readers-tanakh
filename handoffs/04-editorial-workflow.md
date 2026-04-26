# 04 — Editorial Workflow

This document describes how a chapter moves from raw source to finished reading edition. It is a stub at scaffolding time; it will mature through the Jonah MVP pass and subsequent chapters.

## Stage 1 — Ingest (one-time per book)

Run `scripts/ingest_tahot.py` to convert the vendored STEPBible TAHOT TSV (in `research/stepbible-tahot/`) into per-chapter `v0-prose/` files.

Output convention:

- One subdirectory per book: `data/text-files/v0-prose/{NN-book}/` where `NN` is the TaNaK-order index and `book` is a slug.
- One file per chapter: `{abbr}-{NN}.txt` (e.g., `gen-01.txt`, `jonah-02.txt`).
- File contents: verse-marked plain text with full niqqud, full te'amim, ketiv/qere markers preserved, prose paragraph form (no editorial line breaks yet).

`v0-prose/` is the canonical reference. **Never edit by hand.** Re-run `ingest_tahot.py` if the upstream TAHOT vendor is updated; the regenerated v0 should match bit-for-bit unless TAHOT changed.

## Stage 2 — Generate v1-teamim baseline

Run the appropriate parser on the chapter:

- `scripts/parse_teamim_prose.py` for the 21 prose books
- `scripts/parse_teamim_poetic.py` for Psalms, Proverbs, and Job 3:1–42:6 (with the prose parser handling Job's prose frame: 1:1–2:13 and 42:7–17)

Output: `data/text-files/v1-teamim/{NN-book}/{abbr}-{NN}.txt` — a plain-text colometric formatting where every line break corresponds to a disjunctive accent at or above the threshold defined in the canon.

`v1-teamim/` is machine-deterministic. Re-running the parser on identical v0 input must produce identical v1 output.

## Stage 3 — Editorial pass (the human work)

Open the v1-teamim file and the v0-prose file side-by-side. For each chapter, produce `data/text-files/v4-editorial/{NN-book}/{abbr}-{NN}.txt`.

**Editorial moves allowed:**

- **Merge an accent break** — e.g., the parser broke at a tifcha that the editor judges does not warrant a colon boundary. Each editorial line break must positively justify itself as containing an atomic thought, citing which of the three editorial criteria (atomic thought, single image, Hebrew syntax) and any relevant structural justification (per colometry-canon.md §1) supports the break. Te'amim agreement or disagreement is documented as evidence.
- **Insert a non-accent break** — e.g., a long colon contains two atomic thoughts that the accent system left fused. The insertion must cite which criterion warrants the additional break.
- **Adjust whitespace and verse-number formatting** for readability.

**Editorial moves not allowed:**

- Modify the consonants, niqqud, te'amim, or word order
- Add, remove, or substitute words
- Change verse numbering

Every editorial decision should be defensible against the canon. When the canon has no clear rule for a decision, that's a signal to either (a) note it for canon revision, or (b) flag it for Stan review.

## Stage 4 — Build

Run `scripts/build_books.py` to regenerate `books/{book}.html` from `v4-editorial/`. Once English glosses exist, the cascade rule applies: any Hebrew edit triggers English regeneration, then HTML rebuild.

```bash
PYTHONIOENCODING=utf-8 py -3 scripts/build_books.py --book jonah
```

## Stage 5 — Validate

Run validators in `validators/`:

- **Layer 1 (Hebrew break-legality)** — checks for syntactic patterns that should not be split (e.g., maqqef-joined words; preposition + bound noun; construct chains kept together).
- **Layer 3 (colometry)** — checks for methodology compliance (every line positively justified as an atomic thought per canon §1; no orphaned lines; balanced colon lengths within reason).

Validators report issues as candidates for review, not as automatic rewrites.

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

Every divergence from the v1-teamim baseline should leave a trail. The simplest convention:

- The v4-editorial file itself is the trail — comparing v1-teamim against v4-editorial reveals every divergence (merges of accent breaks and splits not in v1)
- A periodic sweep produces a "divergence census": count of divergences per book, per chapter, per criterion-invoked
- Divergence hot-spots (chapters with unusually high divergence rates) are candidates for canon revision — either the criteria need refinement, or the te'amim parser is producing systematic noise

Divergence rate from v1-teamim is a key diagnostic metric. A v4-editorial that diverges from te'amim breaks at >50% suggests either (a) the v1-teamim baseline is over-fragmenting via tifcha-as-servant (canon Rule H11) and the editor is correctly merging back, or (b) the editor's atomic-thought criterion is firing too aggressively and warrants review for canon compliance. Both cases are diagnostic, not failures per se — the te'amim are evidence, not authority. A v4-editorial that diverges 0% from v1-teamim suggests the editorial pass isn't adding value.

---

### Established — 2026-04-25 (scaffolding session)

- Workflow stages defined: ingest, parse, edit, build, validate
- Cascade rule and mechanical-merge pattern documented (carried forward from sibling-project lessons)
- Override tracking framing established as a key methodological metric
- No actual workflow runs yet; document will mature through Jonah MVP and first-book completion
