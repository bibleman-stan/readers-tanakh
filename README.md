# Tanakh Reader — Colometric Reading Edition of the Hebrew Bible

[![Text: CC-BY-4.0](https://img.shields.io/badge/STEPBible--TAHOT-CC--BY--4.0-green.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Code: MIT](https://img.shields.io/badge/Code-MIT-blue.svg)](LICENSE)
[![Live](https://img.shields.io/badge/Live-tanakh--reader.com-blue.svg)](https://tanakh-reader.com)

A colometric reading edition of the Hebrew Bible. The Masoretic Text is reformatted into **sense-lines** — each line one **atomic thought unit (ATU)** — and rendered alongside three conforming layers: transliteration, an interlinear morphological gloss, and the King James English. The formatting recovers compositional architecture that prose paragraphs hide and lets a non-expert reader take Scripture one atomic thought at a time.

**Live at [tanakh-reader.com](https://tanakh-reader.com).** All 39 books are in editorial work; ongoing rule refinement and per-verse review continue corpus-wide.

## What This Edition Provides

- **Four conforming layers per cola.** Hebrew (RTL, pointed) / transliteration / interlinear morphological gloss / KJV English — all line-aligned to the same atomic-thought break.
- **Modern-mode pill** toggles the English row between the KJV verbatim and a modernized rendering; the underlying anchor remains the KJV.
- **Toggleable niqqud and te'amim** on the Hebrew row (preserved for textual fidelity; do not drive editorial decisions — see *Method*).
- **Ketiv / Qere** display with hover for the alternate reading.
- **Petucha / Setuma** divisions preserved as structural cues.
- **TaNaK book order** (Torah / Nevi'im / Ketuvim) with Hebrew-primary versification and a Christian-numbering crosswalk.

## Method

This edition implements the **ATU Method** — a cross-corpus methodology framework maintained at [atu-method](https://github.com/bibleman-stan/atu-method) and shared with the sibling readers ([readers-gnt](https://github.com/bibleman-stan/readers-gnt), [readers-bofm](https://github.com/bibleman-stan/readers-bofm)).

Every editorial break is positively justified. Three forces operate at every candidate boundary:

- **Generative.** Each proposition splits by default (`framework.md §1.1`). Five structural justifications (J1–J5: parallel series, portrait accumulation, speech-act announcement, classical commata, substantive adjunct) extend the rule to non-predicated atomic thoughts.
- **Subtractive.** Four merge-overrides (M1–M4: bonded-pair, complement integrity, bare-governor indivisibility, fragmented atomic thought) catch cases where naïve application of split-triggers would fragment a unit that should stay whole.
- **Diagnostic.** When the generative and subtractive forces leave a candidate boundary genuinely ambiguous, a single-image / camera-angle check is the tiebreaker.

The Hebrew layer is the segmentation target; the other three layers conform. The KJV is structurally anchored to the Hebrew via deterministic Strong's-number routing (using the [STEPBible TAHOT](https://github.com/STEPBible/STEPBible-Data) and [viz.bible MetaV](https://viz.bible) substrates). The KJV is the display anchor, never the editorial canvas.

**The te'amim are textual evidence, not editorial authority.** Niqqud, te'amim, sof pasuq, paseq, and versification are preserved as part of the Masoretic textual tradition but carry no force in editorial decisions (this was an explicit canon revision; the project does not implement a te'amim-prior or te'amim-derivative segmentation). The Westminster Leningrad Codex (transmitted via STEPBible TAHOT) is the textual base; OSHB and UXLC serve as transcription cross-checks; Miqra `al pi ha-Mesorah is vendored as Aleppo-tradition reference. The project does not adjudicate the Masoretic Text against ancient versions.

The methodology's grammatical grounding follows standard reference grammars — **Waltke & O'Connor**, *An Introduction to Biblical Hebrew Syntax* (1990), and **Arnold & Choi**, *A Guide to Biblical Hebrew Syntax* (2003) — supplemented by Joüon-Muraoka and GKC.

## Architecture

The repository contains the **editorial corpus** (Hebrew text + per-word display layers + built HTML) and the **Tanakh-specific rules and validators**. The cross-corpus methodology framework, the KJV alignment library, and the shared discipline memories live in [atu-method](https://github.com/bibleman-stan/atu-method).

Pipeline:

| Tier | Path | Source |
|---|---|---|
| v0 | `data/text-files/v0/prose/` | Raw STEPBible TAHOT (never edited) |
| v1 | `data/text-files/v1/he-baseline/` | Historical mechanical draft from te'amim parse (retained for reference) |
| **v2** | `data/text-files/v2/heb/` | **Hand-edited Hebrew, single source of truth** |
| v2 derived | `data/text-files/v2/{translit,eng-interlinear,eng-kjv}/` | Regenerated from v2/heb per build run |
| books | `books/<book>/<book>-NN.html` | Built reader pages (one per chapter) |

The Tanakh canon (`private/01-method/colometry-canon.md`) instantiates the framework for Hebrew-specific rules (H1–H19) — maqqef-group indivisibility, construct-chain handling, complement integrity, FEF *wayehi*-protasis, casus pendens, and the rest. A validator suite (`validators/syntax/` for Layer 1 grammatical legality, `validators/colometry/` for Layer 3 editorial rules) runs against every commit through a pre-commit baseline check.

## Data Sources

| Source | Role | Tradition | License |
|---|---|---|---|
| [STEPBible TAHOT](https://github.com/STEPBible/STEPBible-Data) | Primary base text + Strong's tagging | Leningrad | CC-BY-4.0 |
| [viz.bible MetaV](https://viz.bible) | Per-KJV-word Strong's anchor | n/a | open |
| [Open Scriptures Hebrew Bible](https://github.com/openscriptures/morphhb) | Transcription cross-check | Leningrad | CC-BY-4.0 |
| [Tanach.us (UXLC)](https://tanach.us/) | Transcription cross-check | Leningrad | No restrictions |
| [Miqra `al pi ha-Mesorah](https://opensiddur.org/readings-and-sourcetexts/mekorot/tanakh/miqra-al-pi-ha-mesorah-a-new-experimental-edition-of-the-tanakh-online/) | Tradition reference | Aleppo | CC-BY-SA |
| [Macula Hebrew lowfat](https://github.com/Clear-Bible/macula-hebrew) | Constituent-tree syntactic primitive (validators) | n/a | CC-BY-4.0 |

## How to Cite

```
Stan the Bible Man. Tanakh Reader: A Colometric Reading Edition of the
Hebrew Bible. 2026.
https://github.com/bibleman-stan/readers-tanakh
https://tanakh-reader.com

Stan the Bible Man. ATU Method: Computational Colometry for Canonical
Texts. 2026. https://github.com/bibleman-stan/atu-method
```

Machine-readable citation: [CITATION.cff](CITATION.cff) (auto-rendered by GitHub's "Cite this repository" widget).

## License

- **Hebrew text (primary):** CC-BY-4.0 (STEPBible / Tyndale House Cambridge)
- **Other vendored sources:** see *Data Sources* above
- **Scripts and web app:** MIT License

## Contributing

Issues and suggestions welcome via GitHub Issues. Colometric corrections should reference the specific verse and proposed line-break change with the Hebrew-syntactic or atomic-thought rationale; corrections framed purely on te'amim grounds will be evaluated against the canon's positive criteria (see *Method* above).
