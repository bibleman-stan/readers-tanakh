# Hebrew Break Legality Reference

**Purpose:** Tanakh project's **Layer 1** — the universal Hebrew grammatical floor that every line in the corpus must respect. A **permission/prohibition surface**, not a rival canon. This document catalogs where Hebrew grammar **forbids** or **permits** line breaks; it does **not** prescribe choices among permitted alternatives. Editorial decisions about *which* permitted break to take live in the colometry canon at `private/01-method/colometry-canon.md` (Layer 3).

**Three-Layer Architecture** (mirrors `bibleman-stan/readers-bofm`):

| Layer | What it is | Where it lives |
|---|---|---|
| **1** | Generic Hebrew grammar — universal facts, language-level | This document |
| **2** | Validators — enforce both layers, distinct error classes | `validators/syntax/` (Layer 1) + `validators/colometry/` (Layer 3) |
| **3** | Tanakh-specific editorial methodology | `private/01-method/colometry-canon.md` |

**Error classes (Layer 2 emits):**

- `[MALFORMED]` — Layer 1 violation. Hard grammatical failure. Must fix before editorial review is meaningful.
- `[DEVIATION]` — Layer 3 violation. Editorial-policy deviation. Review required before deciding merge / split / document-exception.

**Shape-cap discipline:** The break-legality table (below) is **table-only**. No prose explanations of editorial decisions, no examples beyond a token-pattern signature, no exceptions or sub-rules in table cells. The shape cap **IS** the scope-creep prevention — there is nowhere to put prose, so editorial policy cannot be smuggled in as "just grammar." Any line that needs a paragraph belongs in the colometry canon.

**Reference grammars:**
- **Joüon-Muraoka**, *A Grammar of Biblical Hebrew* (2nd ed., Pontifical Biblical Institute, 2006). Cited as `JM §X`.
- **Waltke-O'Connor**, *An Introduction to Biblical Hebrew Syntax* (Eisenbrauns, 1990). Cited as `WO §X.Y`.
- **GKC** = Gesenius-Kautzsch-Cowley, *Hebrew Grammar* (2nd English ed., 1910). Cited as `GKC §X`.

---

## Legality Vocabulary

| Term | Meaning |
|---|---|
| `REQUIRED-MERGE` | Break forbidden here; units must stay on the same line |
| `PERMITTED-EITHER` | Both split and merge are grammatically legal; editorial judgment governs |
| `REQUIRED-BREAK` | Break mandatory here (no Hebrew cases identified in first-pass inventory) |

## Break Legality Table

| Pattern signature | Legality | Reference |
|---|---|---|
| Maqqef-group split (break inside ־ joined words) | `REQUIRED-MERGE` | Joüon-Muraoka §13 |
| Conjunction-prefix וְ stranded line-final | `REQUIRED-MERGE` | The וְ leads its content |
| Prepositional prefix מ/ב/כ/ל stranded from object | `REQUIRED-MERGE` | Joüon-Muraoka §103 |
| Definite article הַ stranded from noun | `REQUIRED-MERGE` | Joüon-Muraoka §137 |
| Direct-object marker אֵת stranded from object | `REQUIRED-MERGE` | Joüon-Muraoka §125 |
| Construct chain split (no intervening modifier) | `REQUIRED-MERGE` | Joüon-Muraoka §129; Waltke-O'Connor §9 |
| Compound divine name split (יְהוָה צְבָאוֹת, יְהוָה אֱלֹהִים, יְהוָה אֱלֹהֵי הַשָּׁמַיִם) | `REQUIRED-MERGE` | Fixed lexicalized formulas |
| Negation (לֹא, אַל, אַיִן) stranded from negated word | `REQUIRED-MERGE` | Joüon-Muraoka §160 |
| Vocative unit split (multi-word direct-address phrase) | `REQUIRED-MERGE` | — |
| Frozen formula split (כֹּה אָמַר יְהוָה, נְאֻם־יְהוָה, divine-name compounds) | `REQUIRED-MERGE` | Fixed lexicalized formulas |
| Compound preposition (מִלִּפְנֵי, מִפְּנֵי, מִתַּחַת, מִבֵּין, etc.) stranded from object | `REQUIRED-MERGE` | JM §103e |
| Vav-consecutive verb form split from prefix (wayyiqtol — one orthographic word) | `REQUIRED-MERGE` | JM §47 |
| Bound enclitic pronoun split from host (always orthographically attached; sanity row) | `REQUIRED-MERGE` | JM §61, §94 |
| Coordinated clause boundary (וְ + new finite verb, with subject continuity or shift) | `PERMITTED-EITHER` | JM §177 |
| Subordinated finite clause boundary (כִּי / אֲשֶׁר / אִם / לְמַעַן / בַּעֲבוּר introducing finite clause) | `PERMITTED-EITHER` | JM §157, §168, §169 |
| Casus pendens / left-dislocation boundary (fronted NP + resumptive pronoun) | `PERMITTED-EITHER` | JM §156; WO §4.7 |
| Vocative boundary (vocative NP, with or without הוֹי / אוֹי / אֲהָהּ) | `PERMITTED-EITHER` | JM §137g |
| Speech-frame boundary (frame ending in לֵאמֹר or bare speech verb, then direct discourse) | `PERMITTED-EITHER` | JM §177i |
| Apposition boundary (apposed NP explicating head noun, no copula) | `PERMITTED-EITHER` | JM §131; WO §12 |
| Relative-clause boundary (אֲשֶׁר / שֶׁ- introducing relative clause) | `PERMITTED-EITHER` | JM §158; WO §19 |
| Adverbial-clause boundary (purpose / result / cause / time / condition / concession finite clause) | `PERMITTED-EITHER` | JM §168, §169 |
| Wayyehi / wehayah protasis boundary (fronted FEF temporal marker with following apodosis) | `PERMITTED-EITHER` | JM §118; WO §33 |

---

## Rule-to-Table Mapping

The colometry canon's rule sections (`### Rule H1` through `### Rule H17`) cite this table by row signature. The grammatical floor lives here; the editorial overlay lives in the canon. When a rule says "merge X," verify both that the move is editorially preferred (canon §5) **and** that the table doesn't forbid it (this document).

| Canon rule | Layer 1 row(s) cited |
|---|---|
| H1 (Maqqef-Group Indivisibility) | Maqqef-group split |
| H2 (Construct Chain Default) | Construct chain split, Compound divine name split |
| H3 (Vav-Consecutive Clause-Head Policy) | Vav-consecutive split, Coordinated clause boundary |
| H4 (Vocative Handling) | Vocative unit split, Vocative boundary |
| H5 (Direct-Speech Framing Default) | Speech-frame boundary |
| H7 (Complement Integrity, Hebrew) | Bound enclitic split, plus verb-object integrity inherited from canon |
| H9 (Divine-Title Appositives) | Compound divine name split, Apposition boundary |
| H11 (Tifcha-as-Servant-of-Atnach) | All proclitic-stranding rows (conjunction / prep / article / object-marker / negation / compound-prep) |
| H14 (Discourse Particles) | Conjunction-prefix and proclitic-stranding rows |
| H15 (Casus Pendens / Left-Dislocation) | Casus pendens boundary |
| H16 (FEF Wayehi Protasis) | Wayyehi / wehayah boundary |

Other canon rules (H6 Ketiv/Qere, H8 Te'amim-as-Evidence, H10 Cross-Verse Continuity, H12 Petucha/Setuma, H13 Special Letters, H17 Genealogy/List-Formula) operate above this surface — they're textual-tradition policies, editorial-judgment rules, or paragraph-scale concerns where per-line break-legality doesn't apply.

---

## What this surface does NOT contain

Honest limits:

1. **Editorial preferences.** "Short speech-frames merge with first speech-cola" is canon §5 H5, not Layer 1. Hebrew grammar permits both; we choose to merge. That's editorial policy.
2. **Diagnostic rules.** Q1/Q2 Goldilocks, Completing-Predication, single-image diagnostic — tiebreakers within the permitted-either space. They live in canon §1.
3. **Te'amim-derived signals.** The te'amim are textual-tradition evidence informing editorial judgment per canon Rule H8. They are not grammatical legality. The accents do not appear in this table.
4. **Sof pasuq, paseq, niqqud, versification.** All overlay marks. Evidence, not legality.

---

## Update log

- **2026-04-26** — Initial population from colometry-canon.md §4.1 first-pass inventory: 10 REQUIRED-MERGE rows.
- **2026-04-27** — Three-layer architecture documented (Layer 1 / 2 / 3); 12 PERMITTED-EITHER rows added; rule-to-table mapping captured; expanded REQUIRED-MERGE with compound-preposition / vav-consecutive / bound-enclitic patterns.
