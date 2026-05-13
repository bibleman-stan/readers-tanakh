# 01 — Project Overview

## What This Is

A colometric reading edition of the Hebrew Bible (Tanakh). The Masoretic Text is reformatted into **sense-lines (cola)** — each line one atomic thought, one image, motivated by Hebrew prosodic and grammatical structure. The edition is designed for oral delivery, devotional reading, and as an analytical substrate for compositional research.

Live at (planned): `tanakh-reader.com`. Domain secured via Cloudflare. GitHub Pages configuration pending until the MVP book ships.

## Origin

The Tanakh project was scoped on 2026-04-25 as a sibling effort to existing colometric reading editions Stan has built. The methodological inheritance is real but is intentionally kept out of public-facing files — the project presents as an independent effort to the public (see *Project Siloing* below).

What initially looked like the Tanakh problem's distinguishing asset — the **te'amim** (Tiberian cantillation accents) encoding a hierarchical sense-unit system over a thousand years ago — turned out to be a methodological trap. After 2026-05-05 the canon retired te'amim as a consultative criterion entirely (canon §1, §8 entry). They served as one-time mechanical input to `parse_teamim.py` for the v1-he-baseline draft and remain operationally relevant for the Sifrei Emet vs prose corpus partition (cluster routing), but they are not consulted in editorial decisions. The disjunctive accent hierarchy still exists as a textual artifact preserved for fidelity; it is not an editorial criterion.

The methodological question is "where does the atomic thought lie, and how do the three forces (atomic thought, single image, Hebrew syntax) resolve the case?" — the same question every other colometric reading edition asks. The Hebrew Bible is not methodologically special on this point; it is methodologically special in that it has rich Macula constituent-tree + frame-semantics data (lowfat XML) that aids morpho-syntactic analysis.

## The Scholarly Landscape

### What exists (analysis, not complete reading editions):

1. **William Wickes**, *A Treatise on the Accentuation of the Twenty-One So-Called Prose Books of the Old Testament* (1887) and *...the Three So-Called Poetical Books* (1881) — the foundational critical analysis of the accent systems. Both public domain.

2. **Israel Yeivin**, *Introduction to the Tiberian Masorah* (SBL, 1980) — modern reference work on the entire Masoretic apparatus including the accent systems.

3. **Robert Lowth**, *Lectures on the Sacred Poetry of the Hebrews* (1753; English 1787) — established *parallelismus membrorum*. The conceptual ancestor of every line-broken English Bible.

4. **James Kugel**, *The Idea of Biblical Poetry* (1981) — dismantled Lowth's strict three-fold parallel typology. Argued the "B" line characteristically advances rather than restating.

5. **Adele Berlin**, *The Dynamics of Biblical Parallelism* (1985) — refined Kugel; analyzed parallelism at grammatical, lexical, semantic, and phonological levels.

6. **F.W. Dobbs-Allsopp**, *On Biblical Poetry* (Oxford, 2015) — current state of the art on unit boundaries.

7. **The Pericope project** (Korpel & Oesch and collaborators) — *Delimitation Criticism* series mapping unit delimiters across MT, LXX, Targums, and Vulgate manuscripts. Methodological precedent for using ancient delimiters (petucha/setuma + accents) as structural cues.

8. **Computational** — the **BHSA database** (ETCBC at VU Amsterdam) provides full syntactic trees on top of the Westminster Leningrad Codex. Free for academic use, ambiguous commercially. Accessible via the Text-Fabric Python library.

### What exists (reader's editions of the Hebrew Bible, but not colometric):

- Crossway's *Hebrew Old Testament Reader's Edition* — single-column running text with bottom-of-page glosses for low-frequency vocabulary. Not colometric.
- The Koren *Reader's Tanakh*.
- Miklal e-reader Bibles.

### What exists (colometric layout of the Bible, but not Hebrew):

- BHS and BHQ apparatus lay out *Sifrei Emet* (and parts of prophetic poetry in BHQ) on multiple lines per verse, but these are copyrighted (Deutsche Bibelgesellschaft) and the methodology is editorial/inconsistent. Hobbins has noted that BHQ "does not honor the prosodic implications of the neumes MT preserves consistently."
- Robert Alter's *The Hebrew Bible: A Translation with Commentary* (Norton, 2018–19) presents the entire Tanakh in line-broken **English** with deliberate verset attention. Closest existing precedent in spirit, but English translation, not Hebrew, and copyrighted.

### The gap this project fills:

**No free, web-native, fully-colometric Hebrew Tanakh exists.** No critical reading edition applies positive-justification colometric criteria (atomic thought, single image, Hebrew syntax) to Hebrew text while treating the te'amim as primary evidence about the Masoretic reading tradition. This project provides that edition and that methodology.

## Methodological Commitments

The methodology rests on **atomic thought as the prior**, three editorial criteria (atomic thought / single image / Hebrew syntax), and the three-forces architecture (generative / subtractive / diagnostic). Each editorial break is not an override of any external authority but a positive identification that the boundary encloses an atomic thought; structural justifications and Hebrew morpho-syntactic constraints are the evidence informing that identification.

**Authoritative definition: [`../atu-method/docs/framework.md`](../atu-method/docs/framework.md) §§0–2** (mission, generative principle, syntax-forbids-splits, five justifications, four merge-overrides, autonomy boundary, decision procedure). Hebrew-specific application is captured in [`private/01-method/colometry-canon.md`](../private/01-method/colometry-canon.md). Breath is not a separate criterion. Te'amim play no role in editorial decisions (canon §1, retired-as-consultative-criterion 2026-05-05); the v1-he-baseline they drove via `parse_teamim.py` exists as historical artifact.

The criteria are grounded in:
- Ancient rhetorical theory (Pseudo-Demetrius *On Style*; Aristotle *Rhetoric*; Cicero *Orator*) on the colon as a basic unit
- Modern Hebrew poetic scholarship (Lowth, Kugel, Berlin, Dobbs-Allsopp)
- Cognitive linguistics (Chafe's intonation units; Miller's chunking)

## Source Text Rationale

### Multi-source vendoring

Multiple free digital editions are vendored into `research/` (gitignored). Vendoring is cheap, licenses are compatible, and having parallel sources enables transcription cross-checking, tradition awareness, and empirical re-pick of the primary if a candidate proves more useful in practice.

| Source | Role | Tradition | License |
|---|---|---|---|
| **STEPBible TAHOT** | Primary (feeds `v0/prose/`) | Leningrad / WLC | CC-BY-4.0 |
| **Open Scriptures Hebrew Bible (OSHB)** | Transcription cross-check | Leningrad / WLC | Text PD; lemma + morph CC-BY-4.0 |
| **Tanach.us (UXLC)** | Transcription cross-check, ongoing typo corrections | Leningrad / WLC | No restrictions |
| **Miqra `al pi ha-Mesorah (MAM)** | Tradition reference (not adopted as base) | Aleppo | CC-BY-SA |
| **JPS 1917** | English comparator (deferred) | — | Public domain |

The constraint: **`v0/prose/` has exactly one source feeding it at any given time** — because v0 cascades into v1-he-baseline and v2/heb, and a forked v0 would multiply downstream ambiguity. Which source is primary is a swappable editorial decision, not an architectural lock-in.

### TAHOT as primary (current)

1. **License**: CC-BY-4.0 on the entire dataset including morphology and lemma data.
2. **Quality**: WLC text corrected against color manuscript scans. Among the highest-quality free morphology available; richer than OSHB on parsing (sequential perfectives, jussive disambiguation).
3. **Format**: TSV. Faster to ingest than OSIS XML.
4. **Coverage**: Hebrew + Aramaic flagged at the word level; Ketiv/Qere variants in-line.

### Textual posture

This is a **colometric reading edition based on a single textual tradition: the Tiberian Masoretic Text in its Leningrad recension**. It is not a critical or eclectic edition. The project does not adjudicate MT against ancient versions (LXX, Dead Sea Scrolls, Samaritan Pentateuch, Targums, Peshitta, Vulgate), and adopts no readings from them. Where Aleppo and Leningrad disagree, the project follows Leningrad; MAM is vendored for tradition awareness, not adoption. Where MT preserves variants internally (Ketiv/Qere, sebirin), standard reader-edition convention is followed (Qere primary, Ketiv as hover/footnote).

The full statement of textual posture lives in `private/01-method/colometry-canon.md §0.1`. The posture is intentional and matches the inheritance pattern used in the sibling Greek edition (which accepts the SBLGNT eclectic text as fixed input). Hebrew text criticism is its own scholarly field, well-served by existing critical editions (BHS, BHQ, HUB, HBCE); duplicating that work would dilute this project's contribution, which is colometric.

A future extension could add a comparator layer that exposes how MT differs from a selected version at the colon level. Such an extension would be additive and explicitly opt-in; it would not change the textual base of the rendered edition.

### Off-limits

- **BHS and BHQ** — Deutsche Bibelgesellschaft holds copyright on the printed editions including their stichometry. Reference only, never quoted in source files.
- **HUB (Hebrew University Bible)** and **HBCE (Hebrew Bible: A Critical Edition)** — copyrighted critical editions; consulted as scholarly reference, not vendored.

## Versification and Book Order

**Hebrew versification is primary.** Christian numbering disagreements are accommodated via:
- A vendored crosswalk table (Sefaria publishes a tested mapping)
- URL aliases (`#1sam-15` redirects to `#shmuel-15`)
- Verse-popover hover metadata showing the cross-reference

**TaNaK book order**: Torah / Nevi'im (Former + Latter) / Ketuvim. Samuel, Kings, Chronicles, Ezra-Nehemiah are each one book. The Twelve Minor Prophets are one book *Trei Asar*.

## English Layer (shipped 2026-05-12)

The English row is **KJV 1769 verbatim**, distributed per Hebrew ATU cola via Strong's-number matching against TAHOT's per-Hebrew-token Strong's data. Implementation is a thin wrapper around `atu_method.kjv_alignment.align_verse()` (see `scripts/regenerate_english.py`). Modern pill toggles archaic→modern surface forms on the English row only — the upper three layers (Hebrew, transliteration, interlinear) do not move (the **4-layer integrity invariant**, enforced by `validators/4-layer-integrity/verify_4_layer_sync.py`).

The previous Macula structural-gloss pipeline (2026-04-26 → 2026-05-11; `generate_english_glosses.py` + `normalize_english_gloss.py` + supporting scanners) was retired in Wave 6 (commit `aece7a310`). The substrate pivot to KJV verbatim happened mid-session when the Macula structural gloss was found to be Hebrew-VSO-ordered and unsuitable as the reading-edition English layer. See `../atu-method/docs/apparatus.md` for the picture-shaped end-state diagram and the mechanism by which Strong's matching distributes KJV phrases across Hebrew cola.

JPS 1917 (public domain) is vendored as a comparator file in `data/`, not as the rendered layer.

## MVP Scope

**First book: Jonah.** Reasons:

- Size: 4 chapters, 48 verses. End-to-end iteration cycles in hours, not days.
- Genre mix in one book: prose narrative (chapters 1, 3, 4) plus a poetic prayer (chapter 2) using the *Sifrei Emet* accent system. Both parsers must exist on day one.
- Petucha/setuma divisions present in the prose sections.
- High recognition: every reviewer can judge whether the colometric layout reads better than prose, because the story is universally known.
- No Ketiv/Qere complications, no Aramaic, no major textual puzzles.

**Sequence after Jonah:** Ruth (pure prose validation), Genesis 1–11 (petucha/setuma at scale), Psalms (highest-value *Sifrei Emet* test). Aramaic portions (Daniel 2:4b–7:28, Ezra 4:8–6:18 + 7:12–26, etc.) handled relatively late, after the Hebrew machinery is settled.

The full Tanakh is roughly 24,000 verses across 39 (Christian-numbered) / 24 (Hebrew-numbered) books — about 3× the size of the GNT corpus. Complete coverage is a multi-year endeavor.

## Hebrew-Specific Web App Considerations

These shape the index.html design choices once the web app session begins:

- **RTL** — `dir="rtl"` on the Hebrew container (HTML attribute, not just CSS). Verse numbers and any Latin-script gloss wrapped in `<bdi>` or `dir="ltr"` spans to prevent Bidi reordering. Mirrored UI (margins, gutters, nav arrows).
- **Font** — SBL Hebrew, Ezra SIL, or Taamey Frank CLM. Test mark stacking on Safari, Chrome, Firefox, iOS WebKit.
- **Niqqud toggle** — default on; toggleable. Most non-fluent readers cannot vocalize unpointed text.
- **Te'amim toggle** — default on; toggleable. Essential for the project's methodological argument; toggleable for users who want a cleaner reading layout.
- **Ketiv / Qere** — print Qere by default (oral reading tradition); expose Ketiv as hover or footnote.
- **Petucha / Setuma** — render as primary structural cue, parallel to the "section" concept.

## Project Siloing

This project is **publicly siloed** — no cross-references in README, CLAUDE.md, handoffs, or any public-facing files to any sibling colometric or reading-edition projects. The connection lives only in `private/` and in Stan's internal knowledge.

**Why:** Multiple reasons Stan chose not to elaborate publicly. Respect this decision and never add cross-references.

