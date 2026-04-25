# data/text-files/ — tier system

This directory holds *our* derivative work on the Hebrew biblical text. Vendored upstream corpora live in `research/` (gitignored).

## Tiers

| Tier | Origin | Editable? | Status |
|---|---|---|---|
| `v0-prose/` | Generated from STEPBible TAHOT by `scripts/ingest_tahot.py`. Verse-marked, full niqqud, full te'amim, ketiv/qere preserved, no editorial line breaks. | **Never.** Re-run the ingest if upstream changes. | Reference baseline |
| `v1-teamim/` | Generated from `v0-prose/` by `scripts/parse_teamim_prose.py` or `scripts/parse_teamim_poetic.py` (depending on book and verse range). Machine-deterministic. | Never directly — only via parser changes. | Editorial input |
| `v4-editorial/` | Hand-edited from `v1-teamim/`. Single source of truth for the published reading edition. | Yes. This is where editorial work happens. | Active |
| `eng-gloss/` | Hand-written structural English glosses, line-aligned to `v4-editorial/`. | Yes. | Deferred until Hebrew MVP stabilizes |

## File naming

Within each tier, files are organized by book, then by chapter:

```
v4-editorial/
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

## Deferred tiers

The following tiers are **not** part of the initial layout. They will be added if and only if they prove valuable:

- `v2-syntax/` — would apply BHSA syntactic-tree refinements to `v1-teamim/`.
- `v3-rhetorical/` — would apply parallelism / discourse-pattern detection (Lowth / Berlin lineage) to `v2-syntax/`.

Sibling colometric projects discovered that each mechanical tier introduces its own error rate that the editorial pass must clean up. The Tanakh project starts lean.

## Cascade rule

Once `eng-gloss/` exists:

> **Hebrew edit (`v4-editorial/`) → English regen (`eng-gloss/`) → HTML rebuild (`books/`) → commit.**

Skipping a stage produces drift between Hebrew and English files that is hard to detect retrospectively.
