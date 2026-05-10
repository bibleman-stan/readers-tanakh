# Tanakh Reader — Colometric Reading Edition of the Hebrew Bible

[![Text: CC-BY-4.0](https://img.shields.io/badge/STEPBible--TAHOT-CC--BY--4.0-green.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Code: MIT](https://img.shields.io/badge/Code-MIT-blue.svg)](LICENSE)
[![Live](https://img.shields.io/badge/Live-tanakh--reader.com-blue.svg)](https://tanakh-reader.com)

A colometric reading edition of the Hebrew Bible. The Masoretic Text is reformatted into **sense-lines (cola)** — each line one atomic thought, motivated by Hebrew grammatical and prosodic structure. The formatting recovers compositional architecture that prose paragraphs hide.

**In progress** — see *Project Stage* below.

## The Gap This Fills

Colometric study of the Hebrew Bible has a deep tradition (Lowth 1753; Kugel 1981; Berlin 1985; Dobbs-Allsopp 2015) and the Masoretes themselves encoded a hierarchical sense-unit system in the **te'amim** (cantillation accents) over a thousand years ago. Modern critical editions (BHS, BHQ) lay out poetry in sense-lines but leave prose in paragraphs and apply editorial line-breaking inconsistently. No complete, freely-licensed, web-native reading edition has been produced that treats the te'amim as its most important evidence about how the medieval Jewish reading tradition understood the text's structure, applies consistent atomic-thought criteria to every editorial line-break decision, and presents the result for oral and devotional reading.

This project provides that edition.

## Method

Every editorial sense-line in this edition is an atomic propositional unit: it contains one complete thought, not merely a grammatically convenient fragment. The Tiberian Masoretic cantillation accents — the **te'amim** (~9th–10th c. CE) — are the most important single piece of evidence about how the medieval Jewish reading tradition understood the text's structure. The disjunctive accent hierarchy (and a separate system for the poetic books *Sifrei Emet* — Psalms, Proverbs, and Job 3:1–42:6) supplies the machine-generated first draft of every chapter's cola. But the te'amim are evidence, not authority: they corroborate editorial decisions; they do not determine them. Where accent structure and atomic-thought analysis converge — roughly 70–80% of the time — the line break is straightforward. Where they diverge, atomic thought prevails.

Each editorial line-break decision is positively justified: the line stands because it contains an atomic thought. Three criteria apply:

- **Atomic thought** — the line is one complete propositional unit
- **Single image** — where the thought is imagistic, one mental picture per line
- **Hebrew syntax** — the break falls at a Hebrew grammatical joint

Breath is not a separate criterion: the te'amim are themselves the chant-breath record of the Masoretic reading tradition, so treating breath independently would double-count that evidence. The methodology draws on William Wickes's foundational work on the accent systems (1881, 1887), Israel Yeivin's *Introduction to the Tiberian Masorah* (1980), and modern colometric scholarship.

## Structural English Gloss (planned)

A toggleable English layer is planned for after the Hebrew MVP stabilizes. It will be a structural gloss aligned by construction to the Hebrew sense-lines — not a published translation. JPS 1917 (public domain) will serve as a comparator, not the rendered layer.

## Features (planned)

- RTL Hebrew web reader with sense-line display
- Toggleable niqqud (vowel points) and te'amim (cantillation marks)
- Ketiv / Qere display with hover for the alternate reading
- Petucha / Setuma paragraph divisions as primary structural cue
- Hebrew-primary versification with Christian-numbering crosswalk
- TaNaK book order (Torah / Nevi'im / Ketuvim)

## Textual Posture

This is a **colometric reading edition based on a single textual tradition: the Tiberian Masoretic Text in its Leningrad recension**. It is not a critical or eclectic edition. It does not adjudicate the Masoretic Text against ancient versions (LXX, Dead Sea Scrolls, Samaritan Pentateuch, Targums, Peshitta, Vulgate), and adopts no readings from them. Where Aleppo and Leningrad disagree, the project follows Leningrad. Where the Masoretic Text preserves variants internally (Ketiv/Qere, sebirin), standard reader-edition convention is followed (Qere primary; Ketiv accessible as hover/footnote).

Multiple free digital editions are vendored as transcription cross-checks and tradition references; the primary source feeding the published text is identified in the table below.

## Data Sources

| Source | Role | Tradition | License |
|---|---|---|---|
| [STEPBible TAHOT](https://github.com/STEPBible/STEPBible-Data) | Primary base text | Leningrad | CC-BY-4.0 |
| [Open Scriptures Hebrew Bible](https://github.com/openscriptures/morphhb) | Transcription cross-check | Leningrad | CC-BY-4.0 |
| [Tanach.us (UXLC)](https://tanach.us/) | Transcription cross-check | Leningrad | No restrictions |
| [Miqra `al pi ha-Mesorah](https://opensiddur.org/readings-and-sourcetexts/mekorot/tanakh/miqra-al-pi-ha-mesorah-a-new-experimental-edition-of-the-tanakh-online/) | Tradition reference | Aleppo | CC-BY-SA |

## Project Stage

Scaffolding only. No editorial text yet. The MVP target is the book of **Jonah** — chosen because its four chapters exercise both the prose accent system (chapters 1, 3, 4) and the *Sifrei Emet* poetic accent system (the prayer in chapter 2), with no Aramaic, no major Ketiv/Qere complications, and a story familiar enough to reviewers that the colometric layout can be evaluated against intuition.

## How to Cite

If you use this edition or build on it, please credit both the edition and the underlying methodology:

```
Stan the Bible Man. Tanakh Reader: A Colometric Reading Edition of the
Hebrew Bible. 2026.
https://github.com/bibleman-stan/readers-tanakh
https://tanakh-reader.com

Stan the Bible Man. ATU Method: Computational Colometry for Canonical
Texts. 2026. https://github.com/bibleman-stan/atu-method
```

For machine-readable citation, see [CITATION.cff](CITATION.cff) (auto-rendered by GitHub's "Cite this repository" widget).

The methodology and Python apparatus that produced this edition live in [atu-method](https://github.com/bibleman-stan/atu-method) — the shared mechanical-layer repository consumed by this and sibling reader editions.

## License

- **Hebrew text (primary):** CC-BY-4.0 (STEPBible / Tyndale House Cambridge)
- **Other vendored sources:** see Data Sources table above
- **Scripts and web app:** MIT License

## Contributing

Issues and suggestions are welcome via GitHub Issues. Colometric corrections should reference the specific verse and proposed line-break change with grammatical or prosodic rationale (citing the relevant te'amim where applicable).
