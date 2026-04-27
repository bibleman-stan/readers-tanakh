# data/text-files/ — tier system

This directory holds *our* derivative work on the Hebrew biblical text. Vendored upstream corpora live in `research/` (gitignored).

## Tiers

| Tier | Origin | Editable? | Status |
|---|---|---|---|
| `v0/prose/` | Generated from STEPBible TAHOT by `scripts/ingest_tahot.py`. Verse-marked, full niqqud, full te'amim, ketiv/qere preserved, no editorial line breaks. | **Never.** Re-run the ingest if upstream changes. | Reference baseline |
| `v0/eng-baseline/` | Generated from TAHOT in lockstep with `v0/prose/`. Per-orthographic-word English glosses preserving TAHOT bracket markup. | Never directly — only via ingest changes. | Editorial input |
| `v0/translit-baseline/` | Generated from TAHOT in lockstep. Per-orthographic-word transliterations, modern Israeli style. | Never directly — only via ingest changes. | Editorial input |
| `v1/he-baseline/` | Generated from `v0/prose/` by `scripts/parse_teamim.py`. Te'amim-driven cola starting draft. Machine-deterministic. | Never directly — only via parser changes. | Editorial input |
| `v1/eng-interlinear/` | Generated from `v0/eng-baseline/` in lockstep with `v1/he-baseline/` (cola structure follows Hebrew). | Never directly — only via parser changes. | Editorial input |
| `v1/eng-gloss/` | Naturalized smooth English, one per cola. Generated from `v0/eng-baseline/` in lockstep. | Never directly — only via parser changes. | Editorial input |
| `v1/translit/` | Per-orthographic-word translit, cola-segmented in lockstep. | Never directly — only via parser changes. | Editorial input |
| `v2/he/` | Hand-edited from `v1/he-baseline/`. Single source of truth for the published Hebrew reading edition. | Yes. This is where editorial work happens. | Active |
| `v2/eng-interlinear/` | Re-segmented from `v1/eng-interlinear/` to match `v2/he/` cola structure by `scripts/propagate_editorial_layers.py`. | Mechanically-derived; manual edits go in v1 source then propagate. | Active |
| `v2/eng-gloss/` | Re-segmented from `v1/eng-gloss/` to match `v2/he/`. Synthesized fallback when editorial cola partial-overlaps a v1 cola. | Hand-edits become primary once English MVP begins. | Deferred (Hebrew MVP first) |
| `v2/translit/` | Re-segmented from `v1/translit/` to match `v2/he/`. | Mechanically-derived; manual edits go in v1 source then propagate. | Active |

## File naming

Within each tier, files are organized by book, then by chapter:

```
v2/he/
  01-genesis/
    gen-01.txt
    gen-02.txt
    ...
  02-exodus/
    exod-01.txt
    ...
  ...
```

- The `NN-book` directory prefix uses TaNaK book order (Torah / Nevi'im / Ketuvim).
- The `abbr-NN` filename uses Hebrew-tradition book unity: Samuel/Kings/Chronicles/Ezra-Nehemiah are each *one* book, the Twelve Minor Prophets are one book *Trei Asar* in a single subdirectory.
- Chapter numbers follow Hebrew versification. Christian-numbering aliases are handled at the URL/route layer in the web app, not in filenames.

## Cascade rule

Once `v2/eng-gloss/` reaches MVP-ready state:

> **Hebrew edit (`v2/he/`) → English regen (`v2/eng-gloss/`) → HTML rebuild (`books/`) → commit.**

Skipping a stage produces drift between Hebrew and English files that is hard to detect retrospectively.

For the Hebrew-only MVP: **Hebrew edit (`v2/he/`) → propagator (`scripts/propagate_editorial_layers.py`) → HTML rebuild (`scripts/build_books.py`) → commit.**

---

**2026-04-26 update:** v1-teamim directory renamed to v1-he-baseline; path references updated throughout this doc to align with the canon's te'amim-as-evidence framing (no longer te'amim-as-prior).

**2026-04-26 update:** `data/text-files/` restructured into per-tier subfolders (v0/, v1/, v2/, v3/, v4/). Tier-name identity strings (v1-he-baseline, v2-he-syntax, etc.) unchanged; only filesystem layout. Path references in this doc updated to the new layout.

**2026-04-27 update:** Tier collapse — the previous 5-tier scheme (v0 → v1 → v2-he-syntax → v3-he-colometry → v4-editorial) is replaced by a 3-tier scheme (v0 → v1 → v2). The Hebrew editorial gold standard moves from `v4/editorial/` to `v2/he/`; the parallel per-word layers move from `v4/{eng-interlinear,eng-gloss,translit}/` to `v2/{eng-interlinear,eng-gloss,translit}/`. The intermediate auto-apply tiers (v2-he-syntax, v3-he-colometry) are retired; STRONG-tagged validator findings now feed the editorial work queue directly per canon §2 Mechanical-rule authority, with the same per-finding Category A/B/C reasoning the canon already governs. See canon §8 entry 2026-04-27 for full rationale.
