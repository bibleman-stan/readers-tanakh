# Editorial Review — Genesis chapters 01–10

**Directive:** 2026-05-17-1700-torah-production-render
**Pipeline HEAD:** `7c919980c`
**Constraint catalog:** `canon/constraint_catalog_v1.md` @ HEAD (26 entries, all active)
**Generated:** 2026-05-17
**Pipeline path:** Agent-dispatch (3 Opus passes per chapter, parallel) → `scripts/atu_pipeline/score_and_apply.py` (agreement scoring + source-byte reassembly) → `scripts/atu_pipeline/audit_constraints.py` (Stage 2)

**Source-byte preservation note:** LLM output NFC-normalizes Hebrew vowel marks (e.g., dagesh-then-sheva → sheva-then-dagesh). Pipeline uses LLM line-break decisions only; word content is taken from source v2/heb bytes (TAHOT/WLC canonical order preserved). Drafts integrate to v2/heb byte-identically to source except for line-break placement.

## Batch summary

- Chapters processed: **10** (Genesis 1–10)
- Total verses: **267**
- **UNANIMOUS**: 197 (73%)
- **MAJORITY**: 64 (23%)
- **ALL-DISAGREE**: 6 (2%)
- **INSUFFICIENT-PASSES / MISSING-FROM-PASSES**: 0

- Stage 2 audit: **16 HARD (CONFLICT)** + **118 ADVISORY** firings

## Per-chapter agreement summary

| Ch | Verses | UNANIMOUS | MAJORITY | ALL-DISAGREE | HARD firings | ADVISORY firings |
|---|---|---|---|---|---|---|
| 1 | 31 | 30 (96%) | 1 | 0 | 4 | 18 |
| 2 | 25 | 24 (96%) | 1 | 0 | 1 | 14 |
| 3 | 24 | 11 (45%) | 9 | 4 | 2 | 17 |
| 4 | 26 | 21 (80%) | 5 | 0 | 1 | 18 |
| 5 | 32 | 16 (50%) | 16 | 0 | 1 | 3 |
| 6 | 22 | 17 (77%) | 4 | 1 | 4 | 10 |
| 7 | 24 | 18 (75%) | 6 | 0 | 3 | 9 |
| 8 | 22 | 16 (72%) | 6 | 0 | 0 | 7 |
| 9 | 29 | 21 (72%) | 7 | 1 | 0 | 12 |
| 10 | 32 | 23 (71%) | 9 | 0 | 0 | 10 |

## Recurring failure-mode classes (≥3 chapters — catalog-revision candidates per §Discipline)

- **`JM154-verbless-clause-nucleus`** — HARD 6 / ADVISORY 2 across chapters [1, 2, 5, 7]
- **`JM174-gapped-verb`** — HARD 0 / ADVISORY 102 across chapters [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
- **`JM168-purpose-clause`** — HARD 0 / ADVISORY 8 across chapters [1, 2, 3, 4, 9]
- **`JM157-ki-recitativum`** — HARD 0 / ADVISORY 3 across chapters [2, 6, 8]

Per §Discipline: surface only; do NOT extend canon mid-run.

## HARD firings (16 CONFLICT verdicts)

Each requires editorial decision: accept the rendering (override the constraint) or amend the rendering to satisfy.

### Genesis 1:21 — `JM125-coordinated-objects` (tier HARD, precedence 2)
**Reason:** verb 'יִּבְרָ֣א' has coordinated A1 tokens split across lines 1 and 2 (combined weight 3 <= 8)
**Details:** `{"line_n": 1, "line_n_plus_1": 2, "verb": "יִּבְרָ֣א", "a1_on_n": ["תַּנִּינִ֖ם"], "a1_on_n1": ["נֶ֣פֶשׁ", "ע֤וֹף"]}`

**Stage 1 draft (post-agreement, source-byte reassembled):**
```
וַיִּבְרָ֣א אֱלֹהִ֔ים אֶת־הַתַּנִּינִ֖ם הַגְּדֹלִ֑ים
וְאֵ֣ת כָּל־נֶ֣פֶשׁ הַֽחַיָּ֣ה׀ הָֽרֹמֶ֡שֶׂת אֲשֶׁר֩ שָׁרְצ֨וּ הַמַּ֜יִם לְמִֽינֵהֶ֗ם וְאֵ֨ת כָּל־ע֤וֹף כָּנָף֙ לְמִינֵ֔הוּ
וַיַּ֥רְא אֱלֹהִ֖ים כִּי־טֽוֹב׃
```

**Editorial decision:** _BLANK_

### Genesis 1:25 — `JM125-coordinated-objects` (tier HARD, precedence 2)
**Reason:** verb 'יַּ֣עַשׂ' has coordinated A1 tokens split across lines 1 and 2 (combined weight 3 <= 8)
**Details:** `{"line_n": 1, "line_n_plus_1": 2, "verb": "יַּ֣עַשׂ", "a1_on_n": ["חַיַּ֨ת", "בְּהֵמָה֙"], "a1_on_n1": ["רֶ֥מֶשׂ"]}`

**Stage 1 draft (post-agreement, source-byte reassembled):**
```
וַיַּ֣עַשׂ אֱלֹהִים֩ אֶת־חַיַּ֨ת הָאָ֜רֶץ לְמִינָ֗הּ וְאֶת־הַבְּהֵמָה֙ לְמִינָ֔הּ
וְאֵ֛ת כָּל־רֶ֥מֶשׂ הָֽאֲדָמָ֖ה לְמִינֵ֑הוּ
וַיַּ֥רְא אֱלֹהִ֖ים כִּי־טֽוֹב׃
```

**Editorial decision:** _BLANK_

### Genesis 1:29 — `JM125-coordinated-objects` (tier HARD, precedence 2)
**Reason:** verb 'נָתַ֨תִּי' has coordinated A1 tokens split across lines 2 and 3 (combined weight 2 <= 8)
**Details:** `{"line_n": 2, "line_n_plus_1": 3, "verb": "נָתַ֨תִּי", "a1_on_n": ["עֵ֣שֶׂב"], "a1_on_n1": ["עֵ֛ץ"]}`

**Stage 1 draft (post-agreement, source-byte reassembled):**
```
וַיֹּ֣אמֶר אֱלֹהִ֗ים
הִנֵּה֩ נָתַ֨תִּי לָכֶ֜ם אֶת־כָּל־עֵ֣שֶׂב׀ זֹרֵ֣עַ זֶ֗רַע אֲשֶׁר֙ עַל־פְּנֵ֣י כָל־הָאָ֔רֶץ
וְאֶת־כָּל־הָעֵ֛ץ אֲשֶׁר־בּ֥וֹ פְרִי־עֵ֖ץ זֹרֵ֣עַ זָ֑רַע
לָכֶ֥ם יִֽהְיֶ֖ה לְאָכְלָֽה׃
```

**Editorial decision:** _BLANK_

### Genesis 1:29 — `JM154-verbless-clause-nucleus` (tier HARD, precedence 3)
**Reason:** verbless-clause subject on line 3 separated from its PP predicate on line 4 — BIND: nucleus must stay together
**Details:** `{"line_n": 3, "line_n_plus_1": 4, "n1_opens_with": "לָ", "n1_is_pp": true, "n1_is_nominal_pred": false}`

**Stage 1 draft (post-agreement, source-byte reassembled):**
```
וַיֹּ֣אמֶר אֱלֹהִ֗ים
הִנֵּה֩ נָתַ֨תִּי לָכֶ֜ם אֶת־כָּל־עֵ֣שֶׂב׀ זֹרֵ֣עַ זֶ֗רַע אֲשֶׁר֙ עַל־פְּנֵ֣י כָל־הָאָ֔רֶץ
וְאֶת־כָּל־הָעֵ֛ץ אֲשֶׁר־בּ֥וֹ פְרִי־עֵ֖ץ זֹרֵ֣עַ זָ֑רַע
לָכֶ֥ם יִֽהְיֶ֖ה לְאָכְלָֽה׃
```

**Editorial decision:** _BLANK_

### Genesis 2:23 — `JM154-verbless-clause-nucleus` (tier HARD, precedence 3)
**Reason:** verbless-clause subject on line 2 separated from its PP predicate on line 3 — BIND: nucleus must stay together
**Details:** `{"line_n": 2, "line_n_plus_1": 3, "n1_opens_with": "לְ", "n1_is_pp": true, "n1_is_nominal_pred": false}`

**Stage 1 draft (post-agreement, source-byte reassembled):**
```
וַיֹּאמֶר֮ הָֽאָדָם֒
זֹ֣את הַפַּ֗עַם עֶ֚צֶם מֵֽעֲצָמַ֔י וּבָשָׂ֖ר מִבְּשָׂרִ֑י
לְזֹאת֙ יִקָּרֵ֣א אִשָּׁ֔ה
כִּ֥י מֵאִ֖ישׁ לֻֽקֳחָה־זֹּֽאת׃
```

**Editorial decision:** _BLANK_

### Genesis 3:6 — `JM125-coordinated-objects` (tier HARD, precedence 2)
**Reason:** verb 'תֵּ֣רֶא' has coordinated A1 tokens split across lines 1 and 2 (combined weight 3 <= 8)
**Details:** `{"line_n": 1, "line_n_plus_1": 2, "verb": "תֵּ֣רֶא", "a1_on_n": ["טוֹב֩"], "a1_on_n1": ["תַֽאֲוָה", "נֶחְמָ֤ד"]}`

**Stage 1 draft (post-agreement, source-byte reassembled):**
```
וַתֵּ֣רֶא הָֽאִשָּׁ֡ה כִּ֣י טוֹב֩ הָעֵ֨ץ לְמַאֲכָ֜ל
וְכִ֧י תַֽאֲוָה־ה֣וּא לָעֵינַ֗יִם וְנֶחְמָ֤ד הָעֵץ֙ לְהַשְׂכִּ֔יל
וַתִּקַּ֥ח מִפִּרְי֖וֹ
וַתֹּאכַ֑ל
וַתִּתֵּ֧ן גַּם־לְאִישָׁ֛הּ עִמָּ֖הּ וַיֹּאכַֽל׃
```

**Editorial decision:** _BLANK_

### Genesis 3:14 — `JM157-complement-integrity` (tier HARD, precedence 2)
**Reason:** complement verb 'יֹּאמֶר֩' (lemma 'אָמַר') at line 1 with obligatory 'כִּ֣י'-clause beginning line 2 — BIND: verb + complement must stay on same line
**Details:** `{"line_n": 1, "line_n_plus_1": 2, "verb": "יֹּאמֶר֩", "verb_lemma": "אָמַר", "complementizer": "כִּ֣י"}`

**Stage 1 draft (post-agreement, source-byte reassembled):**
```
וַיֹּאמֶר֩ יְהֹוָ֨ה אֱלֹהִ֥ים׀ אֶֽל־הַנָּחָשׁ֮
כִּ֣י עָשִׂ֣יתָ זֹּאת֒ אָר֤וּר אַתָּה֙ מִכָּל־הַבְּהֵמָ֔ה
וּמִכֹּ֖ל חַיַּ֣ת הַשָּׂדֶ֑ה עַל־גְּחֹנְךָ֣ תֵלֵ֔ךְ
וְעָפָ֥ר תֹּאכַ֖ל כָּל־יְמֵ֥י חַיֶּֽיךָ׃
```

**Editorial decision:** _BLANK_

### Genesis 4:22 — `JM129-construct-chain` (tier HARD, precedence 2)
**Reason:** NPofNP construct chain split across sense lines 1 / 2: regens 'חֹרֵ֥שׁ' on line 1, rectum 'נְחֹ֖שֶׁת' on line 2
**Details:** `{"constituent_rule": "NPofNP", "regens_text": "חֹרֵ֥שׁ", "regens_line": 1, "rectum_text": "נְחֹ֖שֶׁת", "rectum_line": 2, "pass": "A-constituent"}`

**Stage 1 draft (post-agreement, source-byte reassembled):**
```
וְצִלָּ֣ה גַם־הִ֗וא יָֽלְדָה֙ אֶת־תּ֣וּבַל קַ֔יִן
לֹטֵ֕שׁ כָּל־חֹרֵ֥שׁ נְחֹ֖שֶׁת וּבַרְזֶ֑ל
וַֽאֲח֥וֹת תּֽוּבַל־קַ֖יִן נַֽעֲמָֽה׃
```

**Editorial decision:** _BLANK_

### Genesis 5:1 — `JM154-verbless-clause-nucleus` (tier HARD, precedence 3)
**Reason:** verbless-clause subject on line 1 separated from its PP predicate on line 2 — BIND: nucleus must stay together
**Details:** `{"line_n": 1, "line_n_plus_1": 2, "n1_opens_with": "בִּ", "n1_is_pp": true, "n1_is_nominal_pred": false}`

**Stage 1 draft (post-agreement, source-byte reassembled):**
```
זֶ֣ה סֵ֔פֶר תּוֹלְדֹ֖ת אָדָ֑ם בְּי֗וֹם בְּרֹ֤א אֱלֹהִים֙ אָדָ֔ם
בִּדְמ֥וּת אֱלֹהִ֖ים עָשָׂ֥ה אֹתֽוֹ׃
```

**Editorial decision:** _BLANK_

### Genesis 6:1 — `JM-wayehi-fef-protasis` (tier HARD, precedence 4)
**Reason:** wayehi-FEF SPLIT required: וַיְהִי + protasis + main clause appear collapsed on line 1 — protasis and main clause must occupy separate sense-lines
**Details:** `{"arm": "SPLIT", "wayehi_line": 1, "finite_verb_count_on_line": 2, "line": "וַֽיְהִי֙ כִּֽי־הֵחֵ֣ל הָֽאָדָ֔ם לָרֹ֖ב עַל־פְּנֵ֣י הָֽאֲדָמָ֑ה", "macula_used": true}`

**Stage 1 draft (post-agreement, source-byte reassembled):**
```
וַֽיְהִי֙ כִּֽי־הֵחֵ֣ל הָֽאָדָ֔ם לָרֹ֖ב עַל־פְּנֵ֣י הָֽאֲדָמָ֑ה
וּבָנ֖וֹת יֻלְּד֥וּ לָהֶֽם׃
```

**Editorial decision:** _BLANK_

### Genesis 6:5 — `JM125-verb-object-bond` (tier HARD, precedence 2)
**Reason:** finite verb 'יַּ֣רְא' frame-arg A1 ['רַבָּ֛ה'] stranded on line 2
**Details:** `{"line_n": 1, "line_n_plus_1": 2, "verb": "יַּ֣רְא", "a1_tokens": ["רַבָּ֛ה"]}`

**Stage 1 draft (post-agreement, source-byte reassembled):**
```
וַיַּ֣רְא יְהוָ֔ה
כִּ֥י רַבָּ֛ה רָעַ֥ת הָאָדָ֖ם בָּאָ֑רֶץ
וְכָל־יֵ֙צֶר֙ מַחְשְׁבֹ֣ת לִבּ֔וֹ רַ֥ק רַ֖ע כָּל־הַיּֽוֹם׃
```

**Editorial decision:** _BLANK_

### Genesis 6:5 — `JM157-complement-integrity` (tier HARD, precedence 2)
**Reason:** complement verb 'יַּ֣רְא' (lemma 'רָאָה') at line 1 with obligatory 'כִּ֥י'-clause beginning line 2 — BIND: verb + complement must stay on same line
**Details:** `{"line_n": 1, "line_n_plus_1": 2, "verb": "יַּ֣רְא", "verb_lemma": "רָאָה", "complementizer": "כִּ֥י"}`

**Stage 1 draft (post-agreement, source-byte reassembled):**
```
וַיַּ֣רְא יְהוָ֔ה
כִּ֥י רַבָּ֛ה רָעַ֥ת הָאָדָ֖ם בָּאָ֑רֶץ
וְכָל־יֵ֙צֶר֙ מַחְשְׁבֹ֣ת לִבּ֔וֹ רַ֥ק רַ֖ע כָּל־הַיּֽוֹם׃
```

**Editorial decision:** _BLANK_

### Genesis 6:13 — `JM103e-compound-prep-object` (tier HARD, precedence 1)
**Reason:** line 2 ends with bare compound prep 'לפני'
**Details:** `{"line": 2, "prep": "לפני"}`

**Stage 1 draft (post-agreement, source-byte reassembled):**
```
וַיֹּ֨אמֶר אֱלֹהִ֜ים לְנֹ֗חַ
קֵ֤ץ כָּל־בָּשָׂר֙ בָּ֣א לְפָנַ֔י
כִּֽי־מָלְאָ֥ה הָאָ֛רֶץ חָמָ֖ס מִפְּנֵיהֶ֑ם
וְהִנְנִ֥י מַשְׁחִיתָ֖ם אֶת־הָאָֽרֶץ׃
```

**Editorial decision:** _BLANK_

### Genesis 7:3 — `JM154-verbless-clause-nucleus` (tier HARD, precedence 3)
**Reason:** verbless-clause subject on line 1 separated from its PP predicate on line 2 — BIND: nucleus must stay together
**Details:** `{"line_n": 1, "line_n_plus_1": 2, "n1_opens_with": "לְ", "n1_is_pp": true, "n1_is_nominal_pred": false}`

**Stage 1 draft (post-agreement, source-byte reassembled):**
```
גַּ֣ם מֵע֧וֹף הַשָּׁמַ֛יִם שִׁבְעָ֥ה שִׁבְעָ֖ה זָכָ֣ר וּנְקֵבָ֑ה
לְחַיּ֥וֹת זֶ֖רַע עַל־פְּנֵ֥י כָל־הָאָֽרֶץ׃
```

**Editorial decision:** _BLANK_

### Genesis 7:8 — `JM154-verbless-clause-nucleus` (tier HARD, precedence 3)
**Reason:** verbless-clause subject on line 1 separated from its PP predicate on line 2 — BIND: nucleus must stay together
**Details:** `{"line_n": 1, "line_n_plus_1": 2, "n1_opens_with": "וּ", "n1_is_pp": true, "n1_is_nominal_pred": false}`

**Stage 1 draft (post-agreement, source-byte reassembled):**
```
מִן־הַבְּהֵמָה֙ הַטְּהוֹרָ֔ה
וּמִן־הַ֨בְּהֵמָ֔ה אֲשֶׁ֥ר אֵינֶ֖נָּה טְהֹרָ֑ה
וּמִ֨ן־הָע֔וֹף
וְכֹ֥ל אֲשֶׁר־רֹמֵ֖שׂ עַל־הָֽאֲדָמָֽה׃
```

**Editorial decision:** _BLANK_

### Genesis 7:21 — `JM154-verbless-clause-nucleus` (tier HARD, precedence 3)
**Reason:** verbless-clause subject on line 2 separated from its PP predicate on line 3 — BIND: nucleus must stay together
**Details:** `{"line_n": 2, "line_n_plus_1": 3, "n1_opens_with": "וּ", "n1_is_pp": true, "n1_is_nominal_pred": false}`

**Stage 1 draft (post-agreement, source-byte reassembled):**
```
וַיִּגְוַ֞ע כָּל־בָּשָׂ֣ר׀ הָרֹמֵ֣שׂ עַל־הָאָ֗רֶץ בָּע֤וֹף
וּבַבְּהֵמָה֙
וּבַ֣חַיָּ֔ה
וּבְכָל־הַשֶּׁ֖רֶץ הַשֹּׁרֵ֣ץ עַל־הָאָ֑רֶץ
וְכֹ֖ל הָאָדָֽם׃
```

**Editorial decision:** _BLANK_

## ADVISORY firings rollup (118 total)

| Constraint ID | Firings |
|---|---|
| `JM174-gapped-verb` | 102 |
| `JM168-purpose-clause` | 8 |
| `JM157-ki-recitativum` | 3 |
| `JM147-vocative-extraclausal` | 3 |
| `JM154-verbless-clause-nucleus` | 2 |

ADVISORY firings are informational; they do NOT block auto-apply. Surfaced per directive §9 rollup requirement.

## Non-UNANIMOUS verses (70 total) — per-pass diffs

For each verse: source bytes, three pass renderings (LLM raw — may be NFC-normalized), and (for MAJORITY) the resolved draft (source-byte reassembled per the matching pair's line-break decision). ALL-DISAGREE verses have draft=source (no automated resolution at Stage 1).

### Chapter 1 — 1 verses

#### Genesis 1:28 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיְבָ֣רֶךְ אֹתָם֮ אֱלֹהִים֒
וַיֹּ֨אמֶר לָהֶ֜ם אֱלֹהִ֗ים
פְּר֥וּ וּרְב֛וּ וּמִלְא֥וּ אֶת־הָאָ֖רֶץ
וְכִבְשֻׁ֑הָ
וּרְד֞וּ בִּדְגַ֤ת הַיָּם֙
וּבְע֣וֹף הַשָּׁמַ֔יִם
וּבְכָל־חַיָּ֖ה הָֽרֹמֶ֥שֶׂת עַל־הָאָֽרֶץ׃
```

**Pass 1:**
```
וַיְבָ֣רֶךְ אֹתָם֮ אֱלֹהִים֒
וַיֹּ֨אמֶר לָהֶ֜ם אֱלֹהִ֗ים
פְּר֥וּ וּרְב֛וּ וּמִלְא֥וּ אֶת־הָאָ֖רֶץ וְכִבְשֻׁ֑הָ
וּרְד֞וּ בִּדְגַ֤ת הַיָּם֙ וּבְע֣וֹף הַשָּׁמַ֔יִם וּבְכָל־חַיָּ֖ה הָֽרֹמֶ֥שֶׂת עַל־הָאָֽרֶץ׃
```

**Pass 2:**
```
וַיְבָ֣רֶךְ אֹתָם֮ אֱלֹהִים֒
וַיֹּ֨אמֶר לָהֶ֜ם אֱלֹהִ֗ים
פְּר֥וּ וּרְב֛וּ וּמִלְא֥וּ אֶת־הָאָ֖רֶץ וְכִבְשֻׁ֑הָ
וּרְד֞וּ בִּדְגַ֤ת הַיָּם֙ וּבְע֣וֹף הַשָּׁמַ֔יִם וּבְכָל־חַיָּ֖ה הָֽרֹמֶ֥שֶׂת עַל־הָאָֽרֶץ׃
```

**Pass 3:**
```
וַיְבָ֣רֶךְ אֹתָם֮ אֱלֹהִים֒
וַיֹּ֨אמֶר לָהֶ֜ם אֱלֹהִ֗ים
פְּר֥וּ וּרְב֛וּ וּמִלְא֥וּ אֶת־הָאָ֖רֶץ
וְכִבְשֻׁ֑הָ
וּרְד֞וּ בִּדְגַ֤ת הַיָּם֙ וּבְע֣וֹף הַשָּׁמַ֔יִם וּבְכָל־חַיָּ֖ה הָֽרֹמֶ֥שֶׂת עַל־הָאָֽרֶץ׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיְבָ֣רֶךְ אֹתָם֮ אֱלֹהִים֒
וַיֹּ֨אמֶר לָהֶ֜ם אֱלֹהִ֗ים
פְּר֥וּ וּרְב֛וּ וּמִלְא֥וּ אֶת־הָאָ֖רֶץ וְכִבְשֻׁ֑הָ
וּרְד֞וּ בִּדְגַ֤ת הַיָּם֙ וּבְע֣וֹף הַשָּׁמַ֔יִם וּבְכָל־חַיָּ֖ה הָֽרֹמֶ֥שֶׂת עַל־הָאָֽרֶץ׃
```

**Audit firings:**
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): lines 1–2 have similar length (3, 3 words) — possible gapped bicolon (INFORM). Surface length heuristic only.

**Editorial decision:** _BLANK_

---

### Chapter 2 — 1 verses

#### Genesis 2:23 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיֹּאמֶר֮ הָֽאָדָם֒ זֹ֣את הַפַּ֗עַם עֶ֚צֶם מֵֽעֲצָמַ֔י
וּבָשָׂ֖ר מִבְּשָׂרִ֑י לְזֹאת֙ יִקָּרֵ֣א אִשָּׁ֔ה כִּ֥י מֵאִ֖ישׁ לֻֽקֳחָה־זֹּֽאת׃
```

**Pass 1:**
```
וַיֹּאמֶר֮ הָֽאָדָם֒
זֹ֣את הַפַּ֗עַם עֶ֚צֶם מֵֽעֲצָמַ֔י וּבָשָׂ֖ר מִבְּשָׂרִ֑י
לְזֹאת֙ יִקָּרֵ֣א אִשָּׁ֔ה
כִּ֥י מֵאִ֖ישׁ לֻֽקֳחָה־זֹּֽאת׃
```

**Pass 2:**
```
וַיֹּאמֶר֮ הָֽאָדָם֒ זֹ֣את הַפַּ֗עַם עֶ֚צֶם מֵֽעֲצָמַ֔י וּבָשָׂ֖ר מִבְּשָׂרִ֑י
לְזֹאת֙ יִקָּרֵ֣א אִשָּׁ֔ה
כִּ֥י מֵאִ֖ישׁ לֻֽקֳחָה־זֹּֽאת׃
```

**Pass 3:**
```
וַיֹּאמֶר֮ הָֽאָדָם֒
זֹ֣את הַפַּ֗עַם עֶ֚צֶם מֵֽעֲצָמַ֔י וּבָשָׂ֖ר מִבְּשָׂרִ֑י
לְזֹאת֙ יִקָּרֵ֣א אִשָּׁ֔ה
כִּ֥י מֵאִ֖ישׁ לֻֽקֳחָה־זֹּֽאת׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיֹּאמֶר֮ הָֽאָדָם֒
זֹ֣את הַפַּ֗עַם עֶ֚צֶם מֵֽעֲצָמַ֔י וּבָשָׂ֖ר מִבְּשָׂרִ֑י
לְזֹאת֙ יִקָּרֵ֣א אִשָּׁ֔ה
כִּ֥י מֵאִ֖ישׁ לֻֽקֳחָה־זֹּֽאת׃
```

**Audit firings:**
- `JM154-verbless-clause-nucleus` (CONFLICT, tier HARD): verbless-clause subject on line 2 separated from its PP predicate on line 3 — BIND: nucleus must stay together
- `JM168-purpose-clause` (ADVISORY, tier ADVISORY): line 3 begins with ל-prefixed word ('לְזֹאת֙', skel='לזאת') and is short (3 words) — possible purpose-clause infinitive (JUDGMENT-REQUIRED). Surface heuristic.
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): lines 3–4 have similar length (3, 3 words) — possible gapped bicolon (INFORM). Surface length heuristic only.

**Editorial decision:** _BLANK_

---

### Chapter 3 — 13 verses

#### Genesis 3:3 — **ALL-DISAGREE** (reassembly: `SOURCE (no resolution at Stage 1)`)

**Source:**
```
וּמִפְּרִ֣י הָעֵץ֮ אֲשֶׁ֣ר בְּתוֹךְ־הַגָּן֒
אָמַ֣ר אֱלֹהִ֗ים
לֹ֤א תֹֽאכְלוּ֙ מִמֶּ֔נּוּ וְלֹ֥א תִגְּע֖וּ בּ֑וֹ פֶּן־תְּמֻתֽוּן׃
```

**Pass 1:**
```
וּמִפְּרִ֣י הָעֵץ֮ אֲשֶׁ֣ר בְּתוֹךְ־הַגָּן֒
אָמַ֣ר אֱלֹהִ֗ים
לֹ֤א תֹֽאכְלוּ֙ מִמֶּ֔נּוּ וְלֹ֥א תִגְּע֖וּ בּ֑וֹ פֶּן־תְּמֻתֽוּן׃
```

**Pass 2:**
```
וּמִפְּרִ֣י הָעֵץ֮ אֲשֶׁ֣ר בְּתוֹךְ־הַגָּן֒ אָמַ֣ר אֱלֹהִ֗ים
לֹ֤א תֹֽאכְלוּ֙ מִמֶּ֔נּוּ וְלֹ֥א תִגְּע֖וּ בּ֑וֹ פֶּן־תְּמֻתֽוּן׃
```

**Pass 3:**
```
וּמִפְּרִ֣י הָעֵץ֮ אֲשֶׁ֣ר בְּתוֹךְ־הַגָּן֒ אָמַ֣ר אֱלֹהִ֗ים
לֹ֤א תֹֽאכְלוּ֙ מִמֶּ֔נּוּ וְלֹ֥א תִגְּע֖וּ בּ֑וֹ
פֶּן־תְּמֻתֽוּן׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 3:5 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
כִּ֚י יֹדֵ֣עַ אֱלֹהִ֔ים כִּ֗י בְּיוֹם֙ אֲכָלְכֶ֣ם מִמֶּ֔נּוּ וְנִפְקְח֖וּ עֵֽינֵיכֶ֑ם
וִהְיִיתֶם֙ כֵּֽאלֹהִ֔ים יֹדְעֵ֖י ט֥וֹב וָרָֽע׃
```

**Pass 1:**
```
כִּ֚י יֹדֵ֣עַ אֱלֹהִ֔ים כִּ֗י בְּיוֹם֙ אֲכָלְכֶ֣ם מִמֶּ֔נּוּ וְנִפְקְח֖וּ עֵֽינֵיכֶ֑ם
וִהְיִיתֶם֙ כֵּֽאלֹהִ֔ים יֹדְעֵ֖י ט֥וֹב וָרָֽע׃
```

**Pass 2:**
```
כִּ֚י יֹדֵ֣עַ אֱלֹהִ֔ים כִּ֗י בְּיוֹם֙ אֲכָלְכֶ֣ם מִמֶּ֔נּוּ וְנִפְקְח֖וּ עֵֽינֵיכֶ֑ם
וִהְיִיתֶם֙ כֵּֽאלֹהִ֔ים יֹדְעֵ֖י ט֥וֹב וָרָֽע׃
```

**Pass 3:**
```
כִּ֚י יֹדֵ֣עַ אֱלֹהִ֔ים
כִּ֗י בְּיוֹם֙ אֲכָלְכֶ֣ם מִמֶּ֔נּוּ וְנִפְקְח֖וּ עֵֽינֵיכֶ֑ם
וִהְיִיתֶם֙ כֵּֽאלֹהִ֔ים יֹדְעֵ֖י ט֥וֹב וָרָֽע׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
כִּ֚י יֹדֵ֣עַ אֱלֹהִ֔ים כִּ֗י בְּיוֹם֙ אֲכָלְכֶ֣ם מִמֶּ֔נּוּ וְנִפְקְח֖וּ עֵֽינֵיכֶ֑ם
וִהְיִיתֶם֙ כֵּֽאלֹהִ֔ים יֹדְעֵ֖י ט֥וֹב וָרָֽע׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 3:6 — **ALL-DISAGREE** (reassembly: `SOURCE (no resolution at Stage 1)`)

**Source:**
```
וַתֵּ֣רֶא הָֽאִשָּׁ֡ה כִּ֣י טוֹב֩ הָעֵ֨ץ לְמַאֲכָ֜ל
וְכִ֧י תַֽאֲוָה־ה֣וּא לָעֵינַ֗יִם וְנֶחְמָ֤ד הָעֵץ֙ לְהַשְׂכִּ֔יל
וַתִּקַּ֥ח מִפִּרְי֖וֹ
וַתֹּאכַ֑ל
וַתִּתֵּ֧ן גַּם־לְאִישָׁ֛הּ עִמָּ֖הּ וַיֹּאכַֽל׃
```

**Pass 1:**
```
וַתֵּ֣רֶא הָֽאִשָּׁ֡ה כִּ֣י טוֹב֩ הָעֵ֨ץ לְמַאֲכָ֜ל
וְכִ֧י תַֽאֲוָה־ה֣וּא לָעֵינַ֗יִם וְנֶחְמָ֤ד הָעֵץ֙ לְהַשְׂכִּ֔יל
וַתִּקַּ֥ח מִפִּרְי֖וֹ
וַתֹּאכַ֑ל
וַתִּתֵּ֧ן גַּם־לְאִישָׁ֛הּ עִמָּ֖הּ וַיֹּאכַֽל׃
```

**Pass 2:**
```
וַתֵּ֣רֶא הָֽאִשָּׁ֡ה כִּ֣י טוֹב֩ הָעֵ֨ץ לְמַאֲכָ֜ל
וְכִ֧י תַֽאֲוָה־ה֣וּא לָעֵינַ֗יִם וְנֶחְמָ֤ד הָעֵץ֙ לְהַשְׂכִּ֔יל
וַתִּקַּ֥ח מִפִּרְי֖וֹ
וַתֹּאכַ֑ל
וַתִּתֵּ֧ן גַּם־לְאִישָׁ֛הּ עִמָּ֖הּ
וַיֹּאכַֽל׃
```

**Pass 3:**
```
וַתֵּ֣רֶא הָֽאִשָּׁ֡ה כִּ֣י טוֹב֩ הָעֵ֨ץ לְמַאֲכָ֜ל
וְכִ֧י תַֽאֲוָה־ה֣וּא לָעֵינַ֗יִם
וְנֶחְמָ֤ד הָעֵץ֙ לְהַשְׂכִּ֔יל
וַתִּקַּ֥ח מִפִּרְי֖וֹ
וַתֹּאכַ֑ל
וַתִּתֵּ֧ן גַּם־לְאִישָׁ֛הּ עִמָּ֖הּ
וַיֹּאכַֽל׃
```

**Audit firings:**
- `JM125-coordinated-objects` (CONFLICT, tier HARD): verb 'תֵּ֣רֶא' has coordinated A1 tokens split across lines 1 and 2 (combined weight 3 <= 8)
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): line 1 has finite verb; line 2 has no finite verb but parallel structure (matching roles: {'p'}) — probable gapped bicolon (INFORM: propositionally complete).

**Editorial decision:** _BLANK_

---

#### Genesis 3:10 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיֹּ֕אמֶר אֶת־קֹלְךָ֥
שָׁמַ֖עְתִּי בַּגָּ֑ן
וָאִירָ֛א כִּֽי־עֵירֹ֥ם אָנֹ֖כִי
וָאֵחָבֵֽא׃
```

**Pass 1:**
```
וַיֹּ֕אמֶר אֶת־קֹלְךָ֥ שָׁמַ֖עְתִּי בַּגָּ֑ן
וָאִירָ֛א כִּֽי־עֵירֹ֥ם אָנֹ֖כִי
וָאֵחָבֵֽא׃
```

**Pass 2:**
```
וַיֹּ֕אמֶר
אֶת־קֹלְךָ֥ שָׁמַ֖עְתִּי בַּגָּ֑ן
וָאִירָ֛א כִּֽי־עֵירֹ֥ם אָנֹ֖כִי
וָאֵחָבֵֽא׃
```

**Pass 3:**
```
וַיֹּ֕אמֶר
אֶת־קֹלְךָ֥ שָׁמַ֖עְתִּי בַּגָּ֑ן
וָאִירָ֛א כִּֽי־עֵירֹ֥ם אָנֹ֖כִי
וָאֵחָבֵֽא׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיֹּ֕אמֶר
אֶת־קֹלְךָ֥ שָׁמַ֖עְתִּי בַּגָּ֑ן
וָאִירָ֛א כִּֽי־עֵירֹ֥ם אָנֹ֖כִי
וָאֵחָבֵֽא׃
```

**Audit firings:**
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): lines 2–3 have similar length (3, 3 words) — possible gapped bicolon (INFORM). Surface length heuristic only.

**Editorial decision:** _BLANK_

---

#### Genesis 3:13 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיֹּ֨אמֶר יְהוָ֧ה אֱלֹהִ֛ים לָאִשָּׁ֖ה
מַה־זֹּ֣את עָשִׂ֑ית
וַתֹּ֙אמֶר֙ הָֽאִשָּׁ֔ה
הַנָּחָ֥שׁ הִשִּׁיאַ֖נִי וָאֹכֵֽל׃
```

**Pass 1:**
```
וַיֹּ֨אמֶר יְהוָ֧ה אֱלֹהִ֛ים לָאִשָּׁ֖ה
מַה־זֹּ֣את עָשִׂ֑ית
וַתֹּ֙אמֶר֙ הָֽאִשָּׁ֔ה
הַנָּחָ֥שׁ הִשִּׁיאַ֖נִי וָאֹכֵֽל׃
```

**Pass 2:**
```
וַיֹּ֨אמֶר יְהוָ֧ה אֱלֹהִ֛ים לָאִשָּׁ֖ה
מַה־זֹּ֣את עָשִׂ֑ית
וַתֹּ֙אמֶר֙ הָֽאִשָּׁ֔ה
הַנָּחָ֥שׁ הִשִּׁיאַ֖נִי
וָאֹכֵֽל׃
```

**Pass 3:**
```
וַיֹּ֨אמֶר יְהוָ֧ה אֱלֹהִ֛ים לָאִשָּׁ֖ה
מַה־זֹּ֣את עָשִׂ֑ית
וַתֹּ֙אמֶר֙ הָֽאִשָּׁ֔ה
הַנָּחָ֥שׁ הִשִּׁיאַ֖נִי
וָאֹכֵֽל׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיֹּ֨אמֶר יְהוָ֧ה אֱלֹהִ֛ים לָאִשָּׁ֖ה
מַה־זֹּ֣את עָשִׂ֑ית
וַתֹּ֙אמֶר֙ הָֽאִשָּׁ֔ה
הַנָּחָ֥שׁ הִשִּׁיאַ֖נִי
וָאֹכֵֽל׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 3:14 — **ALL-DISAGREE** (reassembly: `SOURCE (no resolution at Stage 1)`)

**Source:**
```
וַיֹּאמֶר֩ יְהֹוָ֨ה אֱלֹהִ֥ים׀ אֶֽל־הַנָּחָשׁ֮
כִּ֣י עָשִׂ֣יתָ זֹּאת֒ אָר֤וּר אַתָּה֙ מִכָּל־הַבְּהֵמָ֔ה
וּמִכֹּ֖ל חַיַּ֣ת הַשָּׂדֶ֑ה עַל־גְּחֹנְךָ֣ תֵלֵ֔ךְ
וְעָפָ֥ר תֹּאכַ֖ל כָּל־יְמֵ֥י חַיֶּֽיךָ׃
```

**Pass 1:**
```
וַיֹּאמֶר֩ יְהֹוָ֨ה אֱלֹהִ֥ים׀ אֶֽל־הַנָּחָשׁ֮
כִּ֣י עָשִׂ֣יתָ זֹּאת֒ אָר֤וּר אַתָּה֙ מִכָּל־הַבְּהֵמָ֔ה
וּמִכֹּ֖ל חַיַּ֣ת הַשָּׂדֶ֑ה עַל־גְּחֹנְךָ֣ תֵלֵ֔ךְ
וְעָפָ֥ר תֹּאכַ֖ל כָּל־יְמֵ֥י חַיֶּֽיךָ׃
```

**Pass 2:**
```
וַיֹּאמֶר֩ יְהֹוָ֨ה אֱלֹהִ֥ים׀ אֶֽל־הַנָּחָשׁ֮
כִּ֣י עָשִׂ֣יתָ זֹּאת֒ אָר֤וּר אַתָּה֙ מִכָּל־הַבְּהֵמָ֔ה וּמִכֹּ֖ל חַיַּ֣ת הַשָּׂדֶ֑ה
עַל־גְּחֹנְךָ֣ תֵלֵ֔ךְ
וְעָפָ֥ר תֹּאכַ֖ל כָּל־יְמֵ֥י חַיֶּֽיךָ׃
```

**Pass 3:**
```
וַיֹּאמֶר֩ יְהֹוָ֨ה אֱלֹהִ֥ים׀ אֶֽל־הַנָּחָשׁ֮
כִּ֣י עָשִׂ֣יתָ זֹּאת֒
אָר֤וּר אַתָּה֙ מִכָּל־הַבְּהֵמָ֔ה וּמִכֹּ֖ל חַיַּ֣ת הַשָּׂדֶ֑ה
עַל־גְּחֹנְךָ֣ תֵלֵ֔ךְ
וְעָפָ֥ר תֹּאכַ֖ל כָּל־יְמֵ֥י חַיֶּֽיךָ׃
```

**Audit firings:**
- `JM157-complement-integrity` (CONFLICT, tier HARD): complement verb 'יֹּאמֶר֩' (lemma 'אָמַר') at line 1 with obligatory 'כִּ֣י'-clause beginning line 2 — BIND: verb + complement must stay on same line
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): lines 2–3 have similar length (6, 5 words) — possible gapped bicolon (INFORM). Surface length heuristic only.
- `JM147-vocative-extraclausal` (ADVISORY, tier ADVISORY): vocative/extra-clausal element detected on 1 line(s); review placement per canon H4

**Editorial decision:** _BLANK_

---

#### Genesis 3:15 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וְאֵיבָ֣ה׀ אָשִׁ֗ית בֵּֽינְךָ֙
וּבֵ֣ין הָֽאִשָּׁ֔ה
וּבֵ֥ין זַרְעֲךָ֖
וּבֵ֣ין זַרְעָ֑הּ ה֚וּא יְשׁוּפְךָ֣ רֹ֔אשׁ וְאַתָּ֖ה
תְּשׁוּפֶ֥נּוּ עָקֵֽב׃
```

**Pass 1:**
```
וְאֵיבָ֣ה׀ אָשִׁ֗ית בֵּֽינְךָ֙
וּבֵ֣ין הָֽאִשָּׁ֔ה
וּבֵ֥ין זַרְעֲךָ֖
וּבֵ֣ין זַרְעָ֑הּ ה֚וּא יְשׁוּפְךָ֣ רֹ֔אשׁ
וְאַתָּ֖ה תְּשׁוּפֶ֥נּוּ עָקֵֽב׃
```

**Pass 2:**
```
וְאֵיבָ֣ה׀ אָשִׁ֗ית בֵּֽינְךָ֙ וּבֵ֣ין הָֽאִשָּׁ֔ה וּבֵ֥ין זַרְעֲךָ֖ וּבֵ֣ין זַרְעָ֑הּ
ה֚וּא יְשׁוּפְךָ֣ רֹ֔אשׁ
וְאַתָּ֖ה תְּשׁוּפֶ֥נּוּ עָקֵֽב׃
```

**Pass 3:**
```
וְאֵיבָ֣ה׀ אָשִׁ֗ית בֵּֽינְךָ֙ וּבֵ֣ין הָֽאִשָּׁ֔ה וּבֵ֥ין זַרְעֲךָ֖ וּבֵ֣ין זַרְעָ֑הּ
ה֚וּא יְשׁוּפְךָ֣ רֹ֔אשׁ
וְאַתָּ֖ה תְּשׁוּפֶ֥נּוּ עָקֵֽב׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וְאֵיבָ֣ה׀ אָשִׁ֗ית בֵּֽינְךָ֙ וּבֵ֣ין הָֽאִשָּׁ֔ה וּבֵ֥ין זַרְעֲךָ֖ וּבֵ֣ין זַרְעָ֑הּ
ה֚וּא יְשׁוּפְךָ֣ רֹ֔אשׁ
וְאַתָּ֖ה תְּשׁוּפֶ֥נּוּ עָקֵֽב׃
```

**Audit firings:**
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): lines 2–3 have similar length (3, 3 words) — possible gapped bicolon (INFORM). Surface length heuristic only.

**Editorial decision:** _BLANK_

---

#### Genesis 3:16 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
אֶֽל־הָאִשָּׁ֣ה אָמַ֗ר הַרְבָּ֤ה אַרְבֶּה֙ עִצְּבוֹנֵ֣ךְ וְהֵֽרֹנֵ֔ךְ
בְּעֶ֖צֶב תֵּֽלְדִ֣י בָנִ֑ים
וְאֶל־אִישֵׁךְ֙ תְּשׁ֣וּקָתֵ֔ךְ
וְה֖וּא יִמְשָׁל־בָּֽךְ׃
```

**Pass 1:**
```
אֶֽל־הָאִשָּׁ֣ה אָמַ֗ר הַרְבָּ֤ה אַרְבֶּה֙ עִצְּבוֹנֵ֣ךְ וְהֵֽרֹנֵ֔ךְ
בְּעֶ֖צֶב תֵּֽלְדִ֣י בָנִ֑ים
וְאֶל־אִישֵׁךְ֙ תְּשׁ֣וּקָתֵ֔ךְ
וְה֖וּא יִמְשָׁל־בָּֽךְ׃
```

**Pass 2:**
```
אֶֽל־הָאִשָּׁ֣ה אָמַ֗ר הַרְבָּ֤ה אַרְבֶּה֙ עִצְּבוֹנֵ֣ךְ וְהֵֽרֹנֵ֔ךְ
בְּעֶ֖צֶב תֵּֽלְדִ֣י בָנִ֑ים
וְאֶל־אִישֵׁךְ֙ תְּשׁ֣וּקָתֵ֔ךְ
וְה֖וּא יִמְשָׁל־בָּֽךְ׃
```

**Pass 3:**
```
אֶֽל־הָאִשָּׁ֣ה אָמַ֗ר
הַרְבָּ֤ה אַרְבֶּה֙ עִצְּבוֹנֵ֣ךְ וְהֵֽרֹנֵ֔ךְ
בְּעֶ֖צֶב תֵּֽלְדִ֣י בָנִ֑ים
וְאֶל־אִישֵׁךְ֙ תְּשׁ֣וּקָתֵ֔ךְ
וְה֖וּא יִמְשָׁל־בָּֽךְ׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
אֶֽל־הָאִשָּׁ֣ה אָמַ֗ר הַרְבָּ֤ה אַרְבֶּה֙ עִצְּבוֹנֵ֣ךְ וְהֵֽרֹנֵ֔ךְ
בְּעֶ֖צֶב תֵּֽלְדִ֣י בָנִ֑ים
וְאֶל־אִישֵׁךְ֙ תְּשׁ֣וּקָתֵ֔ךְ
וְה֖וּא יִמְשָׁל־בָּֽךְ׃
```

**Audit firings:**
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): line 2 has finite verb; line 3 has no finite verb but parallel structure (similar length) — probable gapped bicolon (INFORM: propositionally complete).

**Editorial decision:** _BLANK_

---

#### Genesis 3:17 — **ALL-DISAGREE** (reassembly: `SOURCE (no resolution at Stage 1)`)

**Source:**
```
וּלְאָדָ֣ם אָמַ֗ר כִּֽי־שָׁמַעְתָּ֮ לְק֣וֹל אִשְׁתֶּךָ֒
וַתֹּ֙אכַל֙ מִן־הָעֵ֔ץ אֲשֶׁ֤ר צִוִּיתִ֙יךָ֙
לֵאמֹ֔ר
לֹ֥א תֹאכַ֖ל מִמֶּ֑נּוּ אֲרוּרָ֤ה הָֽאֲדָמָה֙ בַּֽעֲבוּרֶ֔ךָ
בְּעִצָּבוֹן֙ תֹּֽאכֲלֶ֔נָּה כֹּ֖ל יְמֵ֥י חַיֶּֽיךָ׃
```

**Pass 1:**
```
וּלְאָדָ֣ם אָמַ֗ר כִּֽי־שָׁמַעְתָּ֮ לְק֣וֹל אִשְׁתֶּךָ֒
וַתֹּ֙אכַל֙ מִן־הָעֵ֔ץ אֲשֶׁ֤ר צִוִּיתִ֙יךָ֙ לֵאמֹ֔ר
לֹ֥א תֹאכַ֖ל מִמֶּ֑נּוּ
אֲרוּרָ֤ה הָֽאֲדָמָה֙ בַּֽעֲבוּרֶ֔ךָ
בְּעִצָּבוֹן֙ תֹּֽאכֲלֶ֔נָּה כֹּ֖ל יְמֵ֥י חַיֶּֽיךָ׃
```

**Pass 2:**
```
וּלְאָדָ֣ם אָמַ֗ר כִּֽי־שָׁמַעְתָּ֮ לְק֣וֹל אִשְׁתֶּךָ֒
וַתֹּ֙אכַל֙ מִן־הָעֵ֔ץ אֲשֶׁ֤ר צִוִּיתִ֙יךָ֙ לֵאמֹ֔ר לֹ֥א תֹאכַ֖ל מִמֶּ֑נּוּ
אֲרוּרָ֤ה הָֽאֲדָמָה֙ בַּֽעֲבוּרֶ֔ךָ
בְּעִצָּבוֹן֙ תֹּֽאכֲלֶ֔נָּה כֹּ֖ל יְמֵ֥י חַיֶּֽיךָ׃
```

**Pass 3:**
```
וּלְאָדָ֣ם אָמַ֗ר
כִּֽי־שָׁמַעְתָּ֮ לְק֣וֹל אִשְׁתֶּךָ֒
וַתֹּ֙אכַל֙ מִן־הָעֵ֔ץ אֲשֶׁ֤ר צִוִּיתִ֙יךָ֙ לֵאמֹ֔ר לֹ֥א תֹאכַ֖ל מִמֶּ֑נּוּ
אֲרוּרָ֤ה הָֽאֲדָמָה֙ בַּֽעֲבוּרֶ֔ךָ
בְּעִצָּבוֹן֙ תֹּֽאכֲלֶ֔נָּה כֹּ֖ל יְמֵ֥י חַיֶּֽיךָ׃
```

**Audit firings:**
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): lines 1–2 have similar length (5, 4 words) — possible gapped bicolon (INFORM). Surface length heuristic only.
- `JM147-vocative-extraclausal` (ADVISORY, tier ADVISORY): vocative/extra-clausal element detected on 4 line(s); review placement per canon H4

**Editorial decision:** _BLANK_

---

#### Genesis 3:19 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
בְּזֵעַ֤ת אַפֶּ֙יךָ֙ תֹּ֣אכַל לֶ֔חֶם עַ֤ד שֽׁוּבְךָ֙ אֶל־הָ֣אֲדָמָ֔ה
כִּ֥י מִמֶּ֖נָּה לֻקָּ֑חְתָּ כִּֽי־עָפָ֣ר אַ֔תָּה
וְאֶל־עָפָ֖ר תָּשֽׁוּב׃
```

**Pass 1:**
```
בְּזֵעַ֤ת אַפֶּ֙יךָ֙ תֹּ֣אכַל לֶ֔חֶם עַ֤ד שֽׁוּבְךָ֙ אֶל־הָ֣אֲדָמָ֔ה
כִּ֥י מִמֶּ֖נָּה לֻקָּ֑חְתָּ כִּֽי־עָפָ֣ר אַ֔תָּה
וְאֶל־עָפָ֖ר תָּשֽׁוּב׃
```

**Pass 2:**
```
בְּזֵעַ֤ת אַפֶּ֙יךָ֙ תֹּ֣אכַל לֶ֔חֶם עַ֤ד שֽׁוּבְךָ֙ אֶל־הָ֣אֲדָמָ֔ה
כִּ֥י מִמֶּ֖נָּה לֻקָּ֑חְתָּ
כִּֽי־עָפָ֣ר אַ֔תָּה
וְאֶל־עָפָ֖ר תָּשֽׁוּב׃
```

**Pass 3:**
```
בְּזֵעַ֤ת אַפֶּ֙יךָ֙ תֹּ֣אכַל לֶ֔חֶם עַ֤ד שֽׁוּבְךָ֙ אֶל־הָ֣אֲדָמָ֔ה
כִּ֥י מִמֶּ֖נָּה לֻקָּ֑חְתָּ
כִּֽי־עָפָ֣ר אַ֔תָּה
וְאֶל־עָפָ֖ר תָּשֽׁוּב׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
בְּזֵעַ֤ת אַפֶּ֙יךָ֙ תֹּ֣אכַל לֶ֔חֶם עַ֤ד שֽׁוּבְךָ֙ אֶל־הָ֣אֲדָמָ֔ה
כִּ֥י מִמֶּ֖נָּה לֻקָּ֑חְתָּ
כִּֽי־עָפָ֣ר אַ֔תָּה
וְאֶל־עָפָ֖ר תָּשֽׁוּב׃
```

**Audit firings:**
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): line 2 has finite verb; line 3 has no finite verb but parallel structure (similar length) — probable gapped bicolon (INFORM: propositionally complete).

**Editorial decision:** _BLANK_

---

#### Genesis 3:22 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיֹּ֣אמֶר׀ יְהוָ֣ה אֱלֹהִ֗ים
הֵ֤ן הָֽאָדָם֙ הָיָה֙ כְּאַחַ֣ד מִמֶּ֔נּוּ
לָדַ֖עַת ט֣וֹב וָרָ֑ע
וְעַתָּ֣ה׀ פֶּן־יִשְׁלַ֣ח יָד֗וֹ וְלָקַח֙ גַּ֚ם מֵעֵ֣ץ הַֽחַיִּ֔ים
וְאָכַ֖ל
וָחַ֥י לְעֹלָֽם׃
```

**Pass 1:**
```
וַיֹּ֣אמֶר׀ יְהוָ֣ה אֱלֹהִ֗ים
הֵ֤ן הָֽאָדָם֙ הָיָה֙ כְּאַחַ֣ד מִמֶּ֔נּוּ לָדַ֖עַת ט֣וֹב וָרָ֑ע
וְעַתָּ֣ה׀ פֶּן־יִשְׁלַ֣ח יָד֗וֹ וְלָקַח֙ גַּ֚ם מֵעֵ֣ץ הַֽחַיִּ֔ים
וְאָכַ֖ל
וָחַ֥י לְעֹלָֽם׃
```

**Pass 2:**
```
וַיֹּ֣אמֶר׀ יְהוָ֣ה אֱלֹהִ֗ים
הֵ֤ן הָֽאָדָם֙ הָיָה֙ כְּאַחַ֣ד מִמֶּ֔נּוּ לָדַ֖עַת ט֣וֹב וָרָ֑ע
וְעַתָּ֣ה׀ פֶּן־יִשְׁלַ֣ח יָד֗וֹ וְלָקַח֙ גַּ֚ם מֵעֵ֣ץ הַֽחַיִּ֔ים
וְאָכַ֖ל
וָחַ֥י לְעֹלָֽם׃
```

**Pass 3:**
```
וַיֹּ֣אמֶר׀ יְהוָ֣ה אֱלֹהִ֗ים
הֵ֤ן הָֽאָדָם֙ הָיָה֙ כְּאַחַ֣ד מִמֶּ֔נּוּ לָדַ֖עַת ט֣וֹב וָרָ֑ע
וְעַתָּ֣ה׀ פֶּן־יִשְׁלַ֣ח יָד֗וֹ
וְלָקַח֙ גַּ֚ם מֵעֵ֣ץ הַֽחַיִּ֔ים
וְאָכַ֖ל
וָחַ֥י לְעֹלָֽם׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיֹּ֣אמֶר׀ יְהוָ֣ה אֱלֹהִ֗ים
הֵ֤ן הָֽאָדָם֙ הָיָה֙ כְּאַחַ֣ד מִמֶּ֔נּוּ לָדַ֖עַת ט֣וֹב וָרָ֑ע
וְעַתָּ֣ה׀ פֶּן־יִשְׁלַ֣ח יָד֗וֹ וְלָקַח֙ גַּ֚ם מֵעֵ֣ץ הַֽחַיִּ֔ים
וְאָכַ֖ל
וָחַ֥י לְעֹלָֽם׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 3:23 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַֽיְשַׁלְּחֵ֛הוּ יְהוָ֥ה אֱלֹהִ֖ים מִגַּן־עֵ֑דֶן
לַֽעֲבֹד֙ אֶת־הָ֣אֲדָמָ֔ה אֲשֶׁ֥ר לֻקַּ֖ח מִשָּֽׁם׃
```

**Pass 1:**
```
וַֽיְשַׁלְּחֵ֛הוּ יְהוָ֥ה אֱלֹהִ֖ים מִגַּן־עֵ֑דֶן
לַֽעֲבֹד֙ אֶת־הָ֣אֲדָמָ֔ה אֲשֶׁ֥ר לֻקַּ֖ח מִשָּֽׁם׃
```

**Pass 2:**
```
וַֽיְשַׁלְּחֵ֛הוּ יְהוָ֥ה אֱלֹהִ֖ים מִגַּן־עֵ֑דֶן לַֽעֲבֹד֙ אֶת־הָ֣אֲדָמָ֔ה אֲשֶׁ֥ר לֻקַּ֖ח מִשָּֽׁם׃
```

**Pass 3:**
```
וַֽיְשַׁלְּחֵ֛הוּ יְהוָ֥ה אֱלֹהִ֖ים מִגַּן־עֵ֑דֶן
לַֽעֲבֹד֙ אֶת־הָ֣אֲדָמָ֔ה אֲשֶׁ֥ר לֻקַּ֖ח מִשָּֽׁם׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַֽיְשַׁלְּחֵ֛הוּ יְהוָ֥ה אֱלֹהִ֖ים מִגַּן־עֵ֑דֶן
לַֽעֲבֹד֙ אֶת־הָ֣אֲדָמָ֔ה אֲשֶׁ֥ר לֻקַּ֖ח מִשָּֽׁם׃
```

**Audit firings:**
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): lines 1–2 have similar length (4, 5 words) — possible gapped bicolon (INFORM). Surface length heuristic only.

**Editorial decision:** _BLANK_

---

#### Genesis 3:24 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיְגָ֖רֶשׁ אֶת־הָֽאָדָ֑ם
וַיַּשְׁכֵּן֩ מִקֶּ֨דֶם לְגַן־עֵ֜דֶן אֶת־הַכְּרֻבִ֗ים
וְאֵ֨ת לַ֤הַט הַחֶ֙רֶב֙ הַמִּתְהַפֶּ֔כֶת לִשְׁמֹ֕ר
אֶת־דֶּ֖רֶךְ עֵ֥ץ הַֽחַיִּֽים׃
```

**Pass 1:**
```
וַיְגָ֖רֶשׁ אֶת־הָֽאָדָ֑ם
וַיַּשְׁכֵּן֩ מִקֶּ֨דֶם לְגַן־עֵ֜דֶן אֶת־הַכְּרֻבִ֗ים
וְאֵ֨ת לַ֤הַט הַחֶ֙רֶב֙ הַמִּתְהַפֶּ֔כֶת לִשְׁמֹ֕ר אֶת־דֶּ֖רֶךְ עֵ֥ץ הַֽחַיִּֽים׃
```

**Pass 2:**
```
וַיְגָ֖רֶשׁ אֶת־הָֽאָדָ֑ם
וַיַּשְׁכֵּן֩ מִקֶּ֨דֶם לְגַן־עֵ֜דֶן אֶת־הַכְּרֻבִ֗ים וְאֵ֨ת לַ֤הַט הַחֶ֙רֶב֙ הַמִּתְהַפֶּ֔כֶת
לִשְׁמֹ֕ר אֶת־דֶּ֖רֶךְ עֵ֥ץ הַֽחַיִּֽים׃
```

**Pass 3:**
```
וַיְגָ֖רֶשׁ אֶת־הָֽאָדָ֑ם
וַיַּשְׁכֵּן֩ מִקֶּ֨דֶם לְגַן־עֵ֜דֶן אֶת־הַכְּרֻבִ֗ים וְאֵ֨ת לַ֤הַט הַחֶ֙רֶב֙ הַמִּתְהַפֶּ֔כֶת
לִשְׁמֹ֕ר אֶת־דֶּ֖רֶךְ עֵ֥ץ הַֽחַיִּֽים׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיְגָ֖רֶשׁ אֶת־הָֽאָדָ֑ם
וַיַּשְׁכֵּן֩ מִקֶּ֨דֶם לְגַן־עֵ֜דֶן אֶת־הַכְּרֻבִ֗ים וְאֵ֨ת לַ֤הַט הַחֶ֙רֶב֙ הַמִּתְהַפֶּ֔כֶת
לִשְׁמֹ֕ר אֶת־דֶּ֖רֶךְ עֵ֥ץ הַֽחַיִּֽים׃
```

**Editorial decision:** _BLANK_

---

### Chapter 4 — 5 verses

#### Genesis 4:1 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וְהָ֣אָדָ֔ם יָדַ֖ע אֶת־חַוָּ֣ה אִשְׁתּ֑וֹ
וַתַּ֙הַר֙ וַתֵּ֣לֶד אֶת־קַ֔יִן
וַתֹּ֕אמֶר קָנִ֥יתִי אִ֖ישׁ אֶת־יְהוָֽה׃
```

**Pass 1:**
```
וְהָ֣אָדָ֔ם יָדַ֖ע אֶת־חַוָּ֣ה אִשְׁתּ֑וֹ
וַתַּ֙הַר֙
וַתֵּ֣לֶד אֶת־קַ֔יִן
וַתֹּ֕אמֶר
קָנִ֥יתִי אִ֖ישׁ אֶת־יְהוָֽה׃
```

**Pass 2:**
```
וְהָ֣אָדָ֔ם יָדַ֖ע אֶת־חַוָּ֣ה אִשְׁתּ֑וֹ
וַתַּ֙הַר֙ וַתֵּ֣לֶד אֶת־קַ֔יִן
וַתֹּ֕אמֶר קָנִ֥יתִי אִ֖ישׁ אֶת־יְהוָֽה׃
```

**Pass 3:**
```
וְהָ֣אָדָ֔ם יָדַ֖ע אֶת־חַוָּ֣ה אִשְׁתּ֑וֹ
וַתַּ֙הַר֙ וַתֵּ֣לֶד אֶת־קַ֔יִן
וַתֹּ֕אמֶר קָנִ֥יתִי אִ֖ישׁ אֶת־יְהוָֽה׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וְהָ֣אָדָ֔ם יָדַ֖ע אֶת־חַוָּ֣ה אִשְׁתּ֑וֹ
וַתַּ֙הַר֙ וַתֵּ֣לֶד אֶת־קַ֔יִן
וַתֹּ֕אמֶר קָנִ֥יתִי אִ֖ישׁ אֶת־יְהוָֽה׃
```

**Audit firings:**
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): lines 1–2 have similar length (4, 3 words) — possible gapped bicolon (INFORM). Surface length heuristic only.

**Editorial decision:** _BLANK_

---

#### Genesis 4:9 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיֹּ֤אמֶר יְהוָה֙ אֶל־קַ֔יִן
אֵ֖י הֶ֣בֶל אָחִ֑יךָ
וַיֹּ֙אמֶר֙
לֹ֣א יָדַ֔עְתִּי הֲשֹׁמֵ֥ר אָחִ֖י אָנֹֽכִי׃
```

**Pass 1:**
```
וַיֹּ֤אמֶר יְהוָה֙ אֶל־קַ֔יִן
אֵ֖י הֶ֣בֶל אָחִ֑יךָ
וַיֹּ֙אמֶר֙
לֹ֣א יָדַ֔עְתִּי
הֲשֹׁמֵ֥ר אָחִ֖י אָנֹֽכִי׃
```

**Pass 2:**
```
וַיֹּ֤אמֶר יְהוָה֙ אֶל־קַ֔יִן
אֵ֖י הֶ֣בֶל אָחִ֑יךָ
וַיֹּ֙אמֶר֙ לֹ֣א יָדַ֔עְתִּי
הֲשֹׁמֵ֥ר אָחִ֖י אָנֹֽכִי׃
```

**Pass 3:**
```
וַיֹּ֤אמֶר יְהוָה֙ אֶל־קַ֔יִן
אֵ֖י הֶ֣בֶל אָחִ֑יךָ
וַיֹּ֙אמֶר֙ לֹ֣א יָדַ֔עְתִּי
הֲשֹׁמֵ֥ר אָחִ֖י אָנֹֽכִי׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיֹּ֤אמֶר יְהוָה֙ אֶל־קַ֔יִן
אֵ֖י הֶ֣בֶל אָחִ֑יךָ
וַיֹּ֙אמֶר֙ לֹ֣א יָדַ֔עְתִּי
הֲשֹׁמֵ֥ר אָחִ֖י אָנֹֽכִי׃
```

**Audit firings:**
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): line 1 has finite verb; line 2 has no finite verb but parallel structure (similar length) — probable gapped bicolon (INFORM: propositionally complete).

**Editorial decision:** _BLANK_

---

#### Genesis 4:10 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיֹּ֖אמֶר
מֶ֣ה עָשִׂ֑יתָ ק֚וֹל דְּמֵ֣י אָחִ֔יךָ צֹעֲקִ֥ים אֵלַ֖י מִן־הָֽאֲדָמָֽה׃
```

**Pass 1:**
```
וַיֹּ֖אמֶר
מֶ֣ה עָשִׂ֑יתָ
ק֚וֹל דְּמֵ֣י אָחִ֔יךָ צֹעֲקִ֥ים אֵלַ֖י מִן־הָֽאֲדָמָֽה׃
```

**Pass 2:**
```
וַיֹּ֖אמֶר מֶ֣ה עָשִׂ֑יתָ
ק֚וֹל דְּמֵ֣י אָחִ֔יךָ צֹעֲקִ֥ים אֵלַ֖י מִן־הָֽאֲדָמָֽה׃
```

**Pass 3:**
```
וַיֹּ֖אמֶר מֶ֣ה עָשִׂ֑יתָ
ק֚וֹל דְּמֵ֣י אָחִ֔יךָ צֹעֲקִ֥ים אֵלַ֖י מִן־הָֽאֲדָמָֽה׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיֹּ֖אמֶר מֶ֣ה עָשִׂ֑יתָ
ק֚וֹל דְּמֵ֣י אָחִ֔יךָ צֹעֲקִ֥ים אֵלַ֖י מִן־הָֽאֲדָמָֽה׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 4:11 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וְעַתָּ֖ה אָר֣וּר אָ֑תָּה מִן־הָֽאֲדָמָה֙ אֲשֶׁ֣ר פָּצְתָ֣ה אֶת־פִּ֔יהָ
לָקַ֛חַת אֶת־דְּמֵ֥י אָחִ֖יךָ מִיָּדֶֽךָ׃
```

**Pass 1:**
```
וְעַתָּ֖ה אָר֣וּר אָ֑תָּה מִן־הָֽאֲדָמָה֙ אֲשֶׁ֣ר פָּצְתָ֣ה אֶת־פִּ֔יהָ לָקַ֛חַת אֶת־דְּמֵ֥י אָחִ֖יךָ מִיָּדֶֽךָ׃
```

**Pass 2:**
```
וְעַתָּ֖ה אָר֣וּר אָ֑תָּה מִן־הָֽאֲדָמָה֙ אֲשֶׁ֣ר פָּצְתָ֣ה אֶת־פִּ֔יהָ לָקַ֛חַת אֶת־דְּמֵ֥י אָחִ֖יךָ מִיָּדֶֽךָ׃
```

**Pass 3:**
```
וְעַתָּ֖ה אָר֣וּר אָ֑תָּה מִן־הָֽאֲדָמָה֙ אֲשֶׁ֣ר פָצְתָ֣ה אֶת־פִּ֔יהָ לָקַ֛חַת אֶת־דְּמֵ֥י אָחִ֖יךָ מִיָּדֶֽךָ׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וְעַתָּ֖ה אָר֣וּר אָ֑תָּה מִן־הָֽאֲדָמָה֙ אֲשֶׁ֣ר פָּצְתָ֣ה אֶת־פִּ֔יהָ לָקַ֛חַת אֶת־דְּמֵ֥י אָחִ֖יךָ מִיָּדֶֽךָ׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 4:17 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיֵּ֤דַע קַ֙יִן֙ אֶת־אִשְׁתּ֔וֹ
וַתַּ֖הַר
וַתֵּ֣לֶד אֶת־חֲנ֑וֹךְ
וַֽיְהִי֙ בֹּ֣נֶה עִ֔יר
וַיִּקְרָא֙ שֵׁ֣ם הָעִ֔יר כְּשֵׁ֖ם בְּנ֥וֹ חֲנֽוֹךְ׃
```

**Pass 1:**
```
וַיֵּ֤דַע קַ֙יִן֙ אֶת־אִשְׁתּ֔וֹ
וַתַּ֖הַר
וַתֵּ֣לֶד אֶת־חֲנ֑וֹךְ
וַֽיְהִי֙ בֹּ֣נֶה עִ֔יר
וַיִּקְרָא֙ שֵׁ֣ם הָעִ֔יר כְּשֵׁ֖ם בְּנ֥וֹ חֲנֽוֹךְ׃
```

**Pass 2:**
```
וַיֵּ֤דַע קַ֙יִן֙ אֶת־אִשְׁתּ֔וֹ
וַתַּ֖הַר
וַתֵּ֣לֶד אֶת־חֲנ֑וֹךְ
וַֽיְהִי֙ בֹּ֣נֶה עִ֔יר
וַיִּקְרָא֙ שֵׁ֣ם הָעִ֔יר כְּשֵׁ֖ם בְּנ֥וֹ חֲנֽוֹךְ׃
```

**Pass 3:**
```
וַיֵּ֤דַע קַ֙יִן֙ אֶת־אִשְׁתּ֔וֹ
וַתַּ֖הַר וַתֵּ֣לֶד אֶת־חֲנ֑וֹךְ
וַֽיְהִי֙ בֹּ֣נֶה עִ֔יר
וַיִּקְרָא֙ שֵׁ֣ם הָעִ֔יר כְּשֵׁ֖ם בְּנ֥וֹ חֲנֽוֹךְ׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיֵּ֤דַע קַ֙יִן֙ אֶת־אִשְׁתּ֔וֹ
וַתַּ֖הַר
וַתֵּ֣לֶד אֶת־חֲנ֑וֹךְ
וַֽיְהִי֙ בֹּ֣נֶה עִ֔יר
וַיִּקְרָא֙ שֵׁ֣ם הָעִ֔יר כְּשֵׁ֖ם בְּנ֥וֹ חֲנֽוֹךְ׃
```

**Editorial decision:** _BLANK_

---

### Chapter 5 — 16 verses

#### Genesis 5:5 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיִּֽהְי֞וּ כָּל־יְמֵ֤י אָדָם֙ אֲשֶׁר־חַ֔י תְּשַׁ֤ע מֵאוֹת֙ שָׁנָ֔ה
וּשְׁלֹשִׁ֖ים שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Pass 1:**
```
וַיִּֽהְי֞וּ כָּל־יְמֵ֤י אָדָם֙ אֲשֶׁר־חַ֔י תְּשַׁ֤ע מֵאוֹת֙ שָׁנָ֔ה
וּשְׁלֹשִׁ֖ים שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Pass 2:**
```
וַיִּֽהְי֞וּ כָּל־יְמֵ֤י אָדָם֙ אֲשֶׁר־חַ֔י תְּשַׁ֤ע מֵאוֹת֙ שָׁנָ֔ה וּשְׁלֹשִׁ֖ים שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Pass 3:**
```
וַיִּֽהְי֞וּ כָּל־יְמֵ֤י אָדָם֙ אֲשֶׁר־חַ֔י תְּשַׁ֤ע מֵאוֹת֙ שָׁנָ֔ה וּשְׁלֹשִׁ֖ים שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיִּֽהְי֞וּ כָּל־יְמֵ֤י אָדָם֙ אֲשֶׁר־חַ֔י תְּשַׁ֤ע מֵאוֹת֙ שָׁנָ֔ה וּשְׁלֹשִׁ֖ים שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 5:7 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַֽיְחִי־שֵׁ֗ת אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־אֱנ֔וֹשׁ
שֶׁ֣בַע שָׁנִ֔ים וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 1:**
```
וַֽיְחִי־שֵׁ֗ת אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־אֱנ֔וֹשׁ
שֶׁ֣בַע שָׁנִ֔ים וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 2:**
```
וַֽיְחִי־שֵׁ֗ת אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־אֱנ֔וֹשׁ שֶׁ֣בַע שָׁנִ֔ים וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 3:**
```
וַֽיְחִי־שֵׁ֗ת אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־אֱנ֔וֹשׁ שֶׁ֣בַע שָׁנִ֔ים וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַֽיְחִי־שֵׁ֗ת אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־אֱנ֔וֹשׁ שֶׁ֣בַע שָׁנִ֔ים וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 5:10 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַֽיְחִ֣י אֱנ֗וֹשׁ אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־קֵינָ֔ן חֲמֵ֤שׁ עֶשְׂרֵה֙ שָׁנָ֔ה
וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 1:**
```
וַֽיְחִ֣י אֱנ֗וֹשׁ אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־קֵינָ֔ן חֲמֵ֤שׁ עֶשְׂרֵה֙ שָׁנָ֔ה
וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 2:**
```
וַֽיְחִ֣י אֱנ֗וֹשׁ אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־קֵינָ֔ן חֲמֵ֤שׁ עֶשְׂרֵה֙ שָׁנָ֔ה וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 3:**
```
וַֽיְחִ֣י אֱנ֗וֹשׁ אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־קֵינָ֔ן חֲמֵ֤שׁ עֶשְׂרֵה֙ שָׁנָ֔ה וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַֽיְחִ֣י אֱנ֗וֹשׁ אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־קֵינָ֔ן חֲמֵ֤שׁ עֶשְׂרֵה֙ שָׁנָ֔ה וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 5:11 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיִּֽהְיוּ֙ כָּל־יְמֵ֣י אֱנ֔וֹשׁ
חָמֵ֣שׁ שָׁנִ֔ים וּתְשַׁ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Pass 1:**
```
וַיִּֽהְיוּ֙ כָּל־יְמֵ֣י אֱנ֔וֹשׁ
חָמֵ֣שׁ שָׁנִ֔ים וּתְשַׁ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Pass 2:**
```
וַיִּֽהְיוּ֙ כָּל־יְמֵ֣י אֱנ֔וֹשׁ חָמֵ֣שׁ שָׁנִ֔ים וּתְשַׁ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Pass 3:**
```
וַיִּֽהְיוּ֙ כָּל־יְמֵ֣י אֱנ֔וֹשׁ חָמֵ֣שׁ שָׁנִ֔ים וּתְשַׁ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיִּֽהְיוּ֙ כָּל־יְמֵ֣י אֱנ֔וֹשׁ חָמֵ֣שׁ שָׁנִ֔ים וּתְשַׁ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 5:13 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיְחִ֣י קֵינָ֗ן אַחֲרֵי֙ הוֹלִיד֣וֹ אֶת־מַֽהֲלַלְאֵ֔ל אַרְבָּעִ֣ים שָׁנָ֔ה
וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 1:**
```
וַיְחִ֣י קֵינָ֗ן אַחֲרֵי֙ הוֹלִיד֣וֹ אֶת־מַֽהֲלַלְאֵ֔ל אַרְבָּעִ֣ים שָׁנָ֔ה
וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 2:**
```
וַיְחִ֣י קֵינָ֗ן אַחֲרֵי֙ הוֹלִיד֣וֹ אֶת־מַֽהֲלַלְאֵ֔ל אַרְבָּעִ֣ים שָׁנָ֔ה וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 3:**
```
וַיְחִ֣י קֵינָ֗ן אַחֲרֵי֙ הוֹלִיד֣וֹ אֶת־מַֽהֲלַלְאֵ֔ל אַרְבָּעִ֣ים שָׁנָ֔ה וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיְחִ֣י קֵינָ֗ן אַחֲרֵי֙ הוֹלִיד֣וֹ אֶת־מַֽהֲלַלְאֵ֔ל אַרְבָּעִ֣ים שָׁנָ֔ה וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 5:14 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיִּֽהְיוּ֙ כָּל־יְמֵ֣י קֵינָ֔ן
עֶ֣שֶׂר שָׁנִ֔ים וּתְשַׁ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Pass 1:**
```
וַיִּֽהְיוּ֙ כָּל־יְמֵ֣י קֵינָ֔ן
עֶ֣שֶׂר שָׁנִ֔ים וּתְשַׁ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Pass 2:**
```
וַיִּֽהְיוּ֙ כָּל־יְמֵ֣י קֵינָ֔ן עֶ֣שֶׂר שָׁנִ֔ים וּתְשַׁ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Pass 3:**
```
וַיִּֽהְיוּ֙ כָּל־יְמֵ֣י קֵינָ֔ן עֶ֣שֶׂר שָׁנִ֔ים וּתְשַׁ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיִּֽהְיוּ֙ כָּל־יְמֵ֣י קֵינָ֔ן עֶ֣שֶׂר שָׁנִ֔ים וּתְשַׁ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 5:16 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַֽיְחִ֣י מַֽהֲלַלְאֵ֗ל אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־יֶ֔רֶד שְׁלֹשִׁ֣ים שָׁנָ֔ה
וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 1:**
```
וַֽיְחִ֣י מַֽהֲלַלְאֵ֗ל אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־יֶ֔רֶד שְׁלֹשִׁ֣ים שָׁנָ֔ה
וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 2:**
```
וַֽיְחִ֣י מַֽהֲלַלְאֵ֗ל אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־יֶ֔רֶד שְׁלֹשִׁ֣ים שָׁנָ֔ה וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 3:**
```
וַֽיְחִ֣י מַֽהֲלַלְאֵ֗ל אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־יֶ֔רֶד שְׁלֹשִׁ֣ים שָׁנָ֔ה וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַֽיְחִ֣י מַֽהֲלַלְאֵ֗ל אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־יֶ֔רֶד שְׁלֹשִׁ֣ים שָׁנָ֔ה וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 5:17 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיִּהְיוּ֙ כָּל־יְמֵ֣י מַהֲלַלְאֵ֔ל חָמֵ֤שׁ וְתִשְׁעִים֙ שָׁנָ֔ה
וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Pass 1:**
```
וַיִּהְיוּ֙ כָּל־יְמֵ֣י מַהֲלַלְאֵ֔ל חָמֵ֤שׁ וְתִשְׁעִים֙ שָׁנָ֔ה
וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Pass 2:**
```
וַיִּהְיוּ֙ כָּל־יְמֵ֣י מַהֲלַלְאֵ֔ל חָמֵ֤שׁ וְתִשְׁעִים֙ שָׁנָ֔ה וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Pass 3:**
```
וַיִּהְיוּ֙ כָּל־יְמֵ֣י מַהֲלַלְאֵ֔ל חָמֵ֤שׁ וְתִשְׁעִים֙ שָׁנָ֔ה וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיִּהְיוּ֙ כָּל־יְמֵ֣י מַהֲלַלְאֵ֔ל חָמֵ֤שׁ וְתִשְׁעִים֙ שָׁנָ֔ה וּשְׁמֹנֶ֥ה מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 5:18 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַֽיְחִי־יֶ֕רֶד
שְׁתַּ֧יִם וְשִׁשִּׁ֛ים שָׁנָ֖ה וּמְאַ֣ת שָׁנָ֑ה
וַיּ֖וֹלֶד אֶת־חֲנֽוֹךְ׃
```

**Pass 1:**
```
וַֽיְחִי־יֶ֕רֶד
שְׁתַּ֧יִם וְשִׁשִּׁ֛ים שָׁנָ֖ה וּמְאַ֣ת שָׁנָ֑ה
וַיּ֖וֹלֶד אֶת־חֲנֽוֹךְ׃
```

**Pass 2:**
```
וַֽיְחִי־יֶ֕רֶד שְׁתַּ֧יִם וְשִׁשִּׁ֛ים שָׁנָ֖ה וּמְאַ֣ת שָׁנָ֑ה
וַיּ֖וֹלֶד אֶת־חֲנֽוֹךְ׃
```

**Pass 3:**
```
וַֽיְחִי־יֶ֕רֶד שְׁתַּ֧יִם וְשִׁשִּׁ֛ים שָׁנָ֖ה וּמְאַ֣ת שָׁנָ֑ה
וַיּ֖וֹלֶד אֶת־חֲנֽוֹךְ׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַֽיְחִי־יֶ֕רֶד שְׁתַּ֧יִם וְשִׁשִּׁ֛ים שָׁנָ֖ה וּמְאַ֣ת שָׁנָ֑ה
וַיּ֖וֹלֶד אֶת־חֲנֽוֹךְ׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 5:22 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיִּתְהַלֵּ֨ךְ חֲנ֜וֹךְ אֶת־הָֽאֱלֹהִ֗ים אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־מְתוּשֶׁ֔לַח
שְׁלֹ֥שׁ מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 1:**
```
וַיִּתְהַלֵּ֨ךְ חֲנ֜וֹךְ אֶת־הָֽאֱלֹהִ֗ים אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־מְתוּשֶׁ֔לַח
שְׁלֹ֥שׁ מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 2:**
```
וַיִּתְהַלֵּ֨ךְ חֲנ֜וֹךְ אֶת־הָֽאֱלֹהִ֗ים אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־מְתוּשֶׁ֔לַח שְׁלֹ֥שׁ מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 3:**
```
וַיִּתְהַלֵּ֨ךְ חֲנ֜וֹךְ אֶת־הָֽאֱלֹהִ֗ים אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־מְתוּשֶׁ֔לַח שְׁלֹ֥שׁ מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיִּתְהַלֵּ֨ךְ חֲנ֜וֹךְ אֶת־הָֽאֱלֹהִ֗ים אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־מְתוּשֶׁ֔לַח שְׁלֹ֥שׁ מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 5:25 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיְחִ֣י מְתוּשֶׁ֔לַח
שֶׁ֧בַע וּשְׁמֹנִ֛ים שָׁנָ֖ה וּמְאַ֣ת שָׁנָ֑ה
וַיּ֖וֹלֶד אֶת־לָֽמֶךְ׃
```

**Pass 1:**
```
וַיְחִ֣י מְתוּשֶׁ֔לַח
שֶׁ֧בַע וּשְׁמֹנִ֛ים שָׁנָ֖ה וּמְאַ֣ת שָׁנָ֑ה
וַיּ֖וֹלֶד אֶת־לָֽמֶךְ׃
```

**Pass 2:**
```
וַיְחִ֣י מְתוּשֶׁ֔לַח שֶׁ֧בַע וּשְׁמֹנִ֛ים שָׁנָ֖ה וּמְאַ֣ת שָׁנָ֑ה
וַיּ֖וֹלֶד אֶת־לָֽמֶךְ׃
```

**Pass 3:**
```
וַיְחִ֣י מְתוּשֶׁ֔לַח שֶׁ֧בַע וּשְׁמֹנִ֛ים שָׁנָ֖ה וּמְאַ֣ת שָׁנָ֑ה
וַיּ֖וֹלֶד אֶת־לָֽמֶךְ׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיְחִ֣י מְתוּשֶׁ֔לַח שֶׁ֧בַע וּשְׁמֹנִ֛ים שָׁנָ֖ה וּמְאַ֣ת שָׁנָ֑ה
וַיּ֖וֹלֶד אֶת־לָֽמֶךְ׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 5:26 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַֽיְחִ֣י מְתוּשֶׁ֗לַח אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־לֶ֔מֶךְ שְׁתַּ֤יִם וּשְׁמוֹנִים֙ שָׁנָ֔ה
וּשְׁבַ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 1:**
```
וַֽיְחִ֣י מְתוּשֶׁ֗לַח אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־לֶ֔מֶךְ שְׁתַּ֤יִם וּשְׁמוֹנִים֙ שָׁנָ֔ה
וּשְׁבַ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 2:**
```
וַֽיְחִ֣י מְתוּשֶׁ֗לַח אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־לֶ֔מֶךְ שְׁתַּ֤יִם וּשְׁמוֹנִים֙ שָׁנָ֔ה וּשְׁבַ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 3:**
```
וַֽיְחִ֣י מְתוּשֶׁ֗לַח אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־לֶ֔מֶךְ שְׁתַּ֤יִם וּשְׁמוֹנִים֙ שָׁנָ֔ה וּשְׁבַ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַֽיְחִ֣י מְתוּשֶׁ֗לַח אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־לֶ֔מֶךְ שְׁתַּ֤יִם וּשְׁמוֹנִים֙ שָׁנָ֔ה וּשְׁבַ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 5:27 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיִּהְיוּ֙ כָּל־יְמֵ֣י מְתוּשֶׁ֔לַח
תֵּ֤שַׁע וְשִׁשִּׁים֙ שָׁנָ֔ה וּתְשַׁ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Pass 1:**
```
וַיִּהְיוּ֙ כָּל־יְמֵ֣י מְתוּשֶׁ֔לַח
תֵּ֤שַׁע וְשִׁשִּׁים֙ שָׁנָ֔ה וּתְשַׁ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Pass 2:**
```
וַיִּהְיוּ֙ כָּל־יְמֵ֣י מְתוּשֶׁ֔לַח תֵּ֤שַׁע וְשִׁשִּׁים֙ שָׁנָ֔ה וּתְשַׁ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Pass 3:**
```
וַיִּהְיוּ֙ כָּל־יְמֵ֣י מְתוּשֶׁ֔לַח תֵּ֤שַׁע וְשִׁשִּׁים֙ שָׁנָ֔ה וּתְשַׁ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיִּהְיוּ֙ כָּל־יְמֵ֣י מְתוּשֶׁ֔לַח תֵּ֤שַׁע וְשִׁשִּׁים֙ שָׁנָ֔ה וּתְשַׁ֥ע מֵא֖וֹת שָׁנָ֑ה
וַיָּמֹֽת׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 5:28 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַֽיְחִי־לֶ֕מֶךְ
שְׁתַּ֧יִם וּשְׁמֹנִ֛ים שָׁנָ֖ה וּמְאַ֣ת שָׁנָ֑ה
וַיּ֖וֹלֶד בֵּֽן׃
```

**Pass 1:**
```
וַֽיְחִי־לֶ֕מֶךְ
שְׁתַּ֧יִם וּשְׁמֹנִ֛ים שָׁנָ֖ה וּמְאַ֣ת שָׁנָ֑ה
וַיּ֖וֹלֶד בֵּֽן׃
```

**Pass 2:**
```
וַֽיְחִי־לֶ֕מֶךְ שְׁתַּ֧יִם וּשְׁמֹנִ֛ים שָׁנָ֖ה וּמְאַ֣ת שָׁנָ֑ה
וַיּ֖וֹלֶד בֵּֽן׃
```

**Pass 3:**
```
וַֽיְחִי־לֶ֕מֶךְ שְׁתַּ֧יִם וּשְׁמֹנִ֛ים שָׁנָ֖ה וּמְאַ֣ת שָׁנָ֑ה
וַיּ֖וֹלֶד בֵּֽן׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַֽיְחִי־לֶ֕מֶךְ שְׁתַּ֧יִם וּשְׁמֹנִ֛ים שָׁנָ֖ה וּמְאַ֣ת שָׁנָ֑ה
וַיּ֖וֹלֶד בֵּֽן׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 5:29 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיִּקְרָ֧א אֶת־שְׁמ֛וֹ נֹ֖חַ
לֵאמֹ֑ר זֶ֠ה יְנַחֲמֵ֤נוּ מִֽמַּעֲשֵׂ֙נוּ֙
וּמֵעִצְּב֣וֹן יָדֵ֔ינוּ מִן־הָ֣אֲדָמָ֔ה אֲשֶׁ֥ר אֵֽרְרָ֖הּ יְהוָֽה׃
```

**Pass 1:**
```
וַיִּקְרָ֧א אֶת־שְׁמ֛וֹ נֹ֖חַ
לֵאמֹ֑ר זֶ֠ה יְנַחֲמֵ֤נוּ מִֽמַּעֲשֵׂ֙נוּ֙
וּמֵעִצְּב֣וֹן יָדֵ֔ינוּ מִן־הָ֣אֲדָמָ֔ה אֲשֶׁ֥ר אֵֽרְרָ֖הּ יְהוָֽה׃
```

**Pass 2:**
```
וַיִּקְרָ֧א אֶת־שְׁמ֛וֹ נֹ֖חַ לֵאמֹ֑ר
זֶ֠ה יְנַחֲמֵ֤נוּ מִֽמַּעֲשֵׂ֙נוּ֙ וּמֵעִצְּב֣וֹן יָדֵ֔ינוּ מִן־הָ֣אֲדָמָ֔ה אֲשֶׁ֥ר אֵֽרְרָ֖הּ יְהוָֽה׃
```

**Pass 3:**
```
וַיִּקְרָ֧א אֶת־שְׁמ֛וֹ נֹ֖חַ לֵאמֹ֑ר
זֶ֠ה יְנַחֲמֵ֤נוּ מִֽמַּעֲשֵׂ֙נוּ֙ וּמֵעִצְּב֣וֹן יָדֵ֔ינוּ מִן־הָ֣אֲדָמָ֔ה אֲשֶׁ֥ר אֵֽרְרָ֖הּ יְהוָֽה׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיִּקְרָ֧א אֶת־שְׁמ֛וֹ נֹ֖חַ לֵאמֹ֑ר
זֶ֠ה יְנַחֲמֵ֤נוּ מִֽמַּעֲשֵׂ֙נוּ֙ וּמֵעִצְּב֣וֹן יָדֵ֔ינוּ מִן־הָ֣אֲדָמָ֔ה אֲשֶׁ֥ר אֵֽרְרָ֖הּ יְהוָֽה׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 5:30 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַֽיְחִי־לֶ֗מֶךְ אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־נֹ֔חַ
חָמֵ֤שׁ וְתִשְׁעִים֙ שָׁנָ֔ה
וַחֲמֵ֥שׁ מֵאֹ֖ת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 1:**
```
וַֽיְחִי־לֶ֗מֶךְ אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־נֹ֔חַ
חָמֵ֤שׁ וְתִשְׁעִים֙ שָׁנָ֔ה
וַחֲמֵ֥שׁ מֵאֹ֖ת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 2:**
```
וַֽיְחִי־לֶ֗מֶךְ אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־נֹ֔חַ חָמֵ֤שׁ וְתִשְׁעִים֙ שָׁנָ֔ה וַחֲמֵ֥שׁ מֵאֹ֖ת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Pass 3:**
```
וַֽיְחִי־לֶ֗מֶךְ אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־נֹ֔חַ חָמֵ֤שׁ וְתִשְׁעִים֙ שָׁנָ֔ה וַחֲמֵ֥שׁ מֵאֹ֖ת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַֽיְחִי־לֶ֗מֶךְ אַֽחֲרֵי֙ הוֹלִיד֣וֹ אֶת־נֹ֔חַ חָמֵ֤שׁ וְתִשְׁעִים֙ שָׁנָ֔ה וַחֲמֵ֥שׁ מֵאֹ֖ת שָׁנָ֑ה
וַיּ֥וֹלֶד בָּנִ֖ים וּבָנֽוֹת׃
```

**Editorial decision:** _BLANK_

---

### Chapter 6 — 5 verses

#### Genesis 6:3 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיֹּ֣אמֶר יְהוָ֗ה
לֹֽא־יָד֨וֹן רוּחִ֤י בָֽאָדָם֙ לְעֹלָ֔ם בְּשַׁגַּ֖ם
ה֣וּא בָשָׂ֑ר
וְהָי֣וּ יָמָ֔יו
מֵאָ֥ה וְעֶשְׂרִ֖ים שָׁנָֽה׃
```

**Pass 1:**
```
וַיֹּ֣אמֶר יְהוָ֗ה
לֹֽא־יָד֨וֹן רוּחִ֤י בָֽאָדָם֙ לְעֹלָ֔ם
בְּשַׁגַּ֖ם ה֣וּא בָשָׂ֑ר
וְהָי֣וּ יָמָ֔יו מֵאָ֥ה וְעֶשְׂרִ֖ים שָׁנָֽה׃
```

**Pass 2:**
```
וַיֹּ֣אמֶר יְהוָ֗ה
לֹֽא־יָד֨וֹן רוּחִ֤י בָֽאָדָם֙ לְעֹלָ֔ם
בְּשַׁגַּ֖ם ה֣וּא בָשָׂ֑ר
וְהָי֣וּ יָמָ֔יו מֵאָ֥ה וְעֶשְׂרִ֖ים שָׁנָֽה׃
```

**Pass 3:**
```
וַיֹּ֣אמֶר יְהוָ֗ה
לֹֽא־יָד֨וֹן רוּחִ֤י בָֽאָדָם֙ לְעֹלָ֔ם בְּשַׁגַּ֖ם ה֣וּא בָשָׂ֑ר
וְהָי֣וּ יָמָ֔יו מֵאָ֥ה וְעֶשְׂרִ֖ים שָׁנָֽה׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיֹּ֣אמֶר יְהוָ֗ה
לֹֽא־יָד֨וֹן רוּחִ֤י בָֽאָדָם֙ לְעֹלָ֔ם
בְּשַׁגַּ֖ם ה֣וּא בָשָׂ֑ר
וְהָי֣וּ יָמָ֔יו מֵאָ֥ה וְעֶשְׂרִ֖ים שָׁנָֽה׃
```

**Audit firings:**
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): line 2 has finite verb; line 3 has no finite verb but parallel structure (similar length) — probable gapped bicolon (INFORM: propositionally complete).

**Editorial decision:** _BLANK_

---

#### Genesis 6:4 — **ALL-DISAGREE** (reassembly: `SOURCE (no resolution at Stage 1)`)

**Source:**
```
הַנְּפִלִ֞ים הָי֣וּ בָאָרֶץ֮ בַּיָּמִ֣ים הָהֵם֒
וְגַ֣ם אַֽחֲרֵי־כֵ֗ן אֲשֶׁ֨ר יָבֹ֜אוּ בְּנֵ֤י הָֽאֱלֹהִים֙ אֶל־בְּנ֣וֹת הָֽאָדָ֔ם
וְיָלְד֖וּ לָהֶ֑ם
הֵ֧מָּה הַגִּבֹּרִ֛ים אֲשֶׁ֥ר מֵעוֹלָ֖ם אַנְשֵׁ֥י הַשֵּֽׁם׃
```

**Pass 1:**
```
הַנְּפִלִ֞ים הָי֣וּ בָאָרֶץ֮ בַּיָּמִ֣ים הָהֵם֒
וְגַ֣ם אַֽחֲרֵי־כֵ֗ן אֲשֶׁ֨ר יָבֹ֜אוּ בְּנֵ֤י הָֽאֱלֹהִים֙ אֶל־בְּנ֣וֹת הָֽאָדָ֔ם וְיָלְד֖וּ לָהֶ֑ם
הֵ֧מָּה הַגִּבֹּרִ֛ים אֲשֶׁ֥ר מֵעוֹלָ֖ם אֲנְשֵׁ֥י הַשֵּֽׁם׃
```

**Pass 2:**
```
הַנְּפִלִ֞ים הָי֣וּ בָאָרֶץ֮ בַּיָּמִ֣ים הָהֵם֒
וְגַ֣ם אַֽחֲרֵי־כֵ֗ן אֲשֶׁ֨ר יָבֹ֜אוּ בְּנֵ֤י הָֽאֱלֹהִים֙ אֶל־בְּנ֣וֹת הָֽאָדָ֔ם וְיָלְד֖וּ לָהֶ֑ם
הֵ֧מָּה הַגִּבֹּרִ֛ים אֲשֶׁ֥ר מֵעוֹלָ֖ם אַנְשֵׁ֥י הַשֵּֽׁם׃
```

**Pass 3:**
```
הַנְּפִלִ֞ים הָי֣וּ בָאָרֶץ֮ בַּיָּמִ֣ים הָהֵם֒
וְגַ֣ם אַֽחֲרֵי־כֵ֗ן אֲשֶׁ֨ר יָבֹ֜אוּ בְּנֵ֤י הָֽאֱלֹהִים֙ אֶל־בְּנ֣וֹת הָֽאָדָ֔ם וְיָלְד֖וּ לָהֶ֑ם
הֵ֧מָּה הַגִּבֹּרִ֛ים אֲשֶׁ֥ר מֵעוֹלָ֖ם א֤נְשֵׁי הַשֵּֽׁם׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 6:6 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיִּנָּ֣חֶם יְהוָ֔ה
כִּֽי־עָשָׂ֥ה אֶת־הָֽאָדָ֖ם בָּאָ֑רֶץ וַיִּתְעַצֵּ֖ב אֶל־לִבּֽוֹ׃
```

**Pass 1:**
```
וַיִּנָּ֣חֶם יְהוָ֔ה כִּֽי־עָשָׂ֥ה אֶת־הָֽאָדָ֖ם בָּאָ֑רֶץ
וַיִּתְעַצֵּ֖ב אֶל־לִבּֽוֹ׃
```

**Pass 2:**
```
וַיִּנָּ֣חֶם יְהוָ֔ה
כִּֽי־עָשָׂ֥ה אֶת־הָֽאָדָ֖ם בָּאָ֑רֶץ
וַיִּתְעַצֵּ֖ב אֶל־לִבּֽוֹ׃
```

**Pass 3:**
```
וַיִּנָּ֣חֶם יְהוָ֔ה כִּֽי־עָשָׂ֥ה אֶת־הָֽאָדָ֖ם בָּאָ֑רֶץ
וַיִּתְעַצֵּ֖ב אֶל־לִבּֽוֹ׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיִּנָּ֣חֶם יְהוָ֔ה כִּֽי־עָשָׂ֥ה אֶת־הָֽאָדָ֖ם בָּאָ֑רֶץ
וַיִּתְעַצֵּ֖ב אֶל־לִבּֽוֹ׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 6:10 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיּ֥וֹלֶד נֹ֖חַ שְׁלֹשָׁ֣ה בָנִ֑ים אֶת־שֵׁ֖ם אֶת־חָ֥ם וְאֶת־יָֽפֶת׃
```

**Pass 1:**
```
וַיּ֥וֹלֶד נֹ֖חַ שְׁלֹשָׁ֣ה בָנִ֑ים
אֶת־שֵׁ֖ם אֶת־חָ֥ם וְאֶת־יָֽפֶת׃
```

**Pass 2:**
```
וַיּ֥וֹלֶד נֹ֖חַ שְׁלֹשָׁ֣ה בָנִ֑ים אֶת־שֵׁ֖ם אֶת־חָ֥ם וְאֶת־יָֽפֶת׃
```

**Pass 3:**
```
וַיּ֥וֹלֶד נֹ֖חַ שְׁלֹשָׁ֣ה בָנִ֑ים
אֶת־שֵׁ֖ם אֶת־חָ֥ם וְאֶת־יָֽפֶת׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיּ֥וֹלֶד נֹ֖חַ שְׁלֹשָׁ֣ה בָנִ֑ים
אֶת־שֵׁ֖ם אֶת־חָ֥ם וְאֶת־יָֽפֶת׃
```

**Audit firings:**
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): line 1 has finite verb; line 2 has no finite verb but parallel structure (similar length) — probable gapped bicolon (INFORM: propositionally complete).

**Editorial decision:** _BLANK_

---

#### Genesis 6:17 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַאֲנִ֗י הִנְנִי֩ מֵבִ֨יא אֶת־הַמַּבּ֥וּל מַ֙יִם֙ עַל־הָאָ֔רֶץ
לְשַׁחֵ֣ת כָּל־בָּשָׂ֗ר אֲשֶׁר־בּוֹ֙ ר֣וּחַ חַיִּ֔ים מִתַּ֖חַת הַשָּׁמָ֑יִם
כֹּ֥ל אֲשֶׁר־בָּאָ֖רֶץ יִגְוָֽע׃
```

**Pass 1:**
```
וַאֲנִ֗י הִנְנִי֩ מֵבִ֨יא אֶת־הַמַּבּ֥וּל מַ֙יִם֙ עַל־הָאָ֔רֶץ לְשַׁחֵ֣ת כָּל־בָּשָׂ֗ר אֲשֶׁר־בּוֹ֙ ר֣וּחַ חַיִּ֔ים מִתַּ֖חַת הַשָּׁמָ֑יִם
כֹּ֥ל אֲשֶׁר־בָּאָ֖רֶץ יִגְוָֽע׃
```

**Pass 2:**
```
וַאֲנִ֗י הִנְנִי֩ מֵבִ֨יא אֶת־הַמַּבּ֥וּל מַ֙יִם֙ עַל־הָאָ֔רֶץ
לְשַׁחֵ֣ת כָּל־בָּשָׂ֗ר אֲשֶׁר־בּוֹ֙ ר֣וּחַ חַיִּ֔ים מִתַּ֖חַת הַשָּׁמָ֑יִם
כֹּ֥ל אֲשֶׁר־בָּאָ֖רֶץ יִגְוָֽע׃
```

**Pass 3:**
```
וַאֲנִ֗י הִנְנִי֩ מֵבִ֨יא אֶת־הַמַּבּ֥וּל מַ֙יִם֙ עַל־הָאָ֔רֶץ לְשַׁחֵ֣ת כָּל־בָּשָׂ֗ר אֲשֶׁר־בּוֹ֙ ר֣וּחַ חַיִּ֔ים מִתַּ֖חַת הַשָּׁמָ֑יִם
כֹּ֥ל אֲשֶׁר־בָּאָ֖רֶץ יִגְוָֽע׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַאֲנִ֗י הִנְנִי֩ מֵבִ֨יא אֶת־הַמַּבּ֥וּל מַ֙יִם֙ עַל־הָאָ֔רֶץ לְשַׁחֵ֣ת כָּל־בָּשָׂ֗ר אֲשֶׁר־בּוֹ֙ ר֣וּחַ חַיִּ֔ים מִתַּ֖חַת הַשָּׁמָ֑יִם
כֹּ֥ל אֲשֶׁר־בָּאָ֖רֶץ יִגְוָֽע׃
```

**Editorial decision:** _BLANK_

---

### Chapter 7 — 6 verses

#### Genesis 7:4 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
כִּי֩ לְיָמִ֨ים ע֜וֹד שִׁבְעָ֗ה אָֽנֹכִי֙ מַמְטִ֣יר עַל־הָאָ֔רֶץ אַרְבָּעִ֣ים י֔וֹם
וְאַרְבָּעִ֖ים לָ֑יְלָה
וּמָחִ֗יתִי אֶֽת־כָּל־הַיְקוּם֙ אֲשֶׁ֣ר עָשִׂ֔יתִי מֵעַ֖ל פְּנֵ֥י הָֽאֲדָמָֽה׃
```

**Pass 1:**
```
כִּי֩ לְיָמִ֨ים ע֜וֹד שִׁבְעָ֗ה אָֽנֹכִי֙ מַמְטִ֣יר עַל־הָאָ֔רֶץ אַרְבָּעִ֣ים י֔וֹם וְאַרְבָּעִ֖ים לָ֑יְלָה
וּמָחִ֗יתִי אֶֽת־כָּל־הַיְקוּם֙ אֲשֶׁ֣ר עָשִׂ֔יתִי מֵעַ֖ל פְּנֵ֥י הָֽאֲדָמָֽה׃
```

**Pass 2:**
```
כִּי֩ לְיָמִ֨ים ע֜וֹד שִׁבְעָ֗ה אָֽנֹכִי֙ מַמְטִ֣יר עַל־הָאָ֔רֶץ אַרְבָּעִ֣ים י֔וֹם
וְאַרְבָּעִ֖ים לָ֑יְלָה
וּמָחִ֗יתִי אֶֽת־כָּל־הַיְקוּם֙ אֲשֶׁ֣ר עָשִׂ֔יתִי מֵעַ֖ל פְּנֵ֥י הָֽאֲדָמָֽה׃
```

**Pass 3:**
```
כִּי֩ לְיָמִ֨ים ע֜וֹד שִׁבְעָ֗ה אָֽנֹכִי֙ מַמְטִ֣יר עַל־הָאָ֔רֶץ אַרְבָּעִ֣ים י֔וֹם וְאַרְבָּעִ֖ים לָ֑יְלָה
וּמָחִ֗יתִי אֶֽת־כָּל־הַיְקוּם֙ אֲשֶׁ֣ר עָשִׂ֔יתִי מֵעַ֖ל פְּנֵ֥י הָֽאֲדָמָֽה׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
כִּי֩ לְיָמִ֨ים ע֜וֹד שִׁבְעָ֗ה אָֽנֹכִי֙ מַמְטִ֣יר עַל־הָאָ֔רֶץ אַרְבָּעִ֣ים י֔וֹם וְאַרְבָּעִ֖ים לָ֑יְלָה
וּמָחִ֗יתִי אֶֽת־כָּל־הַיְקוּם֙ אֲשֶׁ֣ר עָשִׂ֔יתִי מֵעַ֖ל פְּנֵ֥י הָֽאֲדָמָֽה׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 7:7 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיָּ֣בֹא נֹ֗חַ וּ֠בָנָיו וְאִשְׁתּ֧וֹ וּנְשֵֽׁי־בָנָ֛יו אִתּ֖וֹ אֶל־הַתֵּבָ֑ה
מִפְּנֵ֖י מֵ֥י הַמַּבּֽוּל׃
```

**Pass 1:**
```
וַיָּ֣בֹא נֹ֗חַ וּ֠בָנָיו וְאִשְׁתּ֧וֹ וּנְשֵֽׁי־בָנָ֛יו אִתּ֖וֹ אֶל־הַתֵּבָ֑ה
מִפְּנֵ֖י מֵ֥י הַמַּבּֽוּל׃
```

**Pass 2:**
```
וַיָּ֣בֹא נֹ֗חַ וּ֠בָנָיו וְאִשְׁתּ֧וֹ וּנְשֵֽׁי־בָנָ֛יו אִתּ֖וֹ אֶל־הַתֵּבָ֑ה
מִפְּנֵ֖י מֵ֥י הַמַּבּֽוּל׃
```

**Pass 3:**
```
וַיָּ֣בֹא נֹ֗חַ וּ֠בָנָיו וְאִשְׁתּ֧וֹ וּנְשֵֽׁי־בָנָ֛יו אִתּ֖וֹ אֶל־הַתֵּבָ֑ה מִפְּנֵ֖י מֵ֥י הַמַּבּֽוּל׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיָּ֣בֹא נֹ֗חַ וּ֠בָנָיו וְאִשְׁתּ֧וֹ וּנְשֵֽׁי־בָנָ֛יו אִתּ֖וֹ אֶל־הַתֵּבָ֑ה
מִפְּנֵ֖י מֵ֥י הַמַּבּֽוּל׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 7:12 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַֽיְהִ֥י הַגֶּ֖שֶׁם עַל־הָאָ֑רֶץ אַרְבָּעִ֣ים י֔וֹם
וְאַרְבָּעִ֖ים לָֽיְלָה׃
```

**Pass 1:**
```
וַֽיְהִ֥י הַגֶּ֖שֶׁם עַל־הָאָ֑רֶץ אַרְבָּעִ֣ים י֔וֹם וְאַרְבָּעִ֖ים לָֽיְלָה׃
```

**Pass 2:**
```
וַֽיְהִ֥י הַגֶּ֖שֶׁם עַל־הָאָ֑רֶץ אַרְבָּעִ֣ים י֔וֹם
וְאַרְבָּעִ֖ים לָֽיְלָה׃
```

**Pass 3:**
```
וַֽיְהִ֥י הַגֶּ֖שֶׁם עַל־הָאָ֑רֶץ אַרְבָּעִ֣ים י֔וֹם וְאַרְבָּעִ֖ים לָֽיְלָה׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַֽיְהִ֥י הַגֶּ֖שֶׁם עַל־הָאָ֑רֶץ אַרְבָּעִ֣ים י֔וֹם וְאַרְבָּעִ֖ים לָֽיְלָה׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 7:13 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
בְּעֶ֨צֶם הַיּ֤וֹם הַזֶּה֙ בָּ֣א נֹ֔חַ וְשֵׁם־וְחָ֥ם
וָיֶ֖פֶת בְּנֵי־נֹ֑חַ
וְאֵ֣שֶׁת נֹ֗חַ
וּשְׁלֹ֧שֶׁת נְשֵֽׁי־בָנָ֛יו אִתָּ֖ם אֶל־הַתֵּבָֽה׃
```

**Pass 1:**
```
בְּעֶ֨צֶם הַיּ֤וֹם הַזֶּה֙ בָּ֣א נֹ֔חַ וְשֵׁם־וְחָ֥ם
וָיֶ֖פֶת בְּנֵי־נֹ֑חַ
וְאֵ֣שֶׁת נֹ֗חַ
וּשְׁלֹ֧שֶׁת נְשֵֽׁי־בָנָ֛יו אִתָּ֖ם אֶל־הַתֵּבָֽה׃
```

**Pass 2:**
```
בְּעֶ֨צֶם הַיּ֤וֹם הַזֶּה֙ בָּ֣א נֹ֔חַ וְשֵׁם־וְחָ֥ם
וָיֶ֖פֶת בְּנֵי־נֹ֑חַ
וְאֵ֣שֶׁת נֹ֗חַ
וּשְׁלֹ֧שֶׁת נְשֵֽׁי־בָנָ֛יו אִתָּ֖ם אֶל־הַתֵּבָֽה׃
```

**Pass 3:**
```
בְּעֶ֨צֶם הַיּ֤וֹם הַזֶּה֙ בָּ֣א נֹ֔חַ וְשֵׁם־וְחָ֥ם וָיֶ֖פֶת בְּנֵי־נֹ֑חַ
וְאֵ֣שֶׁת נֹ֗חַ וּשְׁלֹ֧שֶׁת נְשֵֽׁי־בָנָ֛יו אִתָּ֖ם אֶל־הַתֵּבָֽה׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
בְּעֶ֨צֶם הַיּ֤וֹם הַזֶּה֙ בָּ֣א נֹ֔חַ וְשֵׁם־וְחָ֥ם
וָיֶ֖פֶת בְּנֵי־נֹ֑חַ
וְאֵ֣שֶׁת נֹ֗חַ
וּשְׁלֹ֧שֶׁת נְשֵֽׁי־בָנָ֛יו אִתָּ֖ם אֶל־הַתֵּבָֽה׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 7:14 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
הֵ֜מָּה
וְכָל־הַֽחַיָּ֣ה לְמִינָ֗הּ
וְכָל־הַבְּהֵמָה֙ לְמִינָ֔הּ
וְכָל־הָרֶ֛מֶשׂ הָרֹמֵ֥שׂ עַל־הָאָ֖רֶץ לְמִינֵ֑הוּ
וְכָל־הָע֣וֹף לְמִינֵ֔הוּ
כֹּ֖ל צִפּ֥וֹר כָּל־כָּנָֽף׃
```

**Pass 1:**
```
הֵ֜מָּה וְכָל־הַֽחַיָּ֣ה לְמִינָ֗הּ
וְכָל־הַבְּהֵמָה֙ לְמִינָ֔הּ
וְכָל־הָרֶ֛מֶשׂ הָרֹמֵ֥שׂ עַל־הָאָ֖רֶץ לְמִינֵ֑הוּ
וְכָל־הָע֣וֹף לְמִינֵ֔הוּ
כֹּ֖ל צִפּ֥וֹר כָּל־כָּנָֽף׃
```

**Pass 2:**
```
הֵ֜מָּה וְכָל־הַֽחַיָּ֣ה לְמִינָ֗הּ
וְכָל־הַבְּהֵמָה֙ לְמִינָ֔הּ
וְכָל־הָרֶ֛מֶשׂ הָרֹמֵ֥שׂ עַל־הָאָ֖רֶץ לְמִינֵ֑הוּ
וְכָל־הָע֣וֹף לְמִינֵ֔הוּ
כֹּ֖ל צִפּ֥וֹר כָּל־כָּנָֽף׃
```

**Pass 3:**
```
הֵ֜מָּה
וְכָל־הַֽחַיָּ֣ה לְמִינָ֗הּ
וְכָל־הַבְּהֵמָה֙ לְמִינָ֔הּ
וְכָל־הָרֶ֛מֶשׂ הָרֹמֵ֥שׂ עַל־הָאָ֖רֶץ לְמִינֵ֑הוּ
וְכָל־הָע֣וֹף לְמִינֵ֔הוּ כֹּ֖ל צִפּ֥וֹר כָּל־כָּנָֽף׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
הֵ֜מָּה וְכָל־הַֽחַיָּ֣ה לְמִינָ֗הּ
וְכָל־הַבְּהֵמָה֙ לְמִינָ֔הּ
וְכָל־הָרֶ֛מֶשׂ הָרֹמֵ֥שׂ עַל־הָאָ֖רֶץ לְמִינֵ֑הוּ
וְכָל־הָע֣וֹף לְמִינֵ֔הוּ
כֹּ֖ל צִפּ֥וֹר כָּל־כָּנָֽף׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 7:15 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיָּבֹ֥אוּ אֶל־נֹ֖חַ אֶל־הַתֵּבָ֑ה שְׁנַ֤יִם שְׁנַ֙יִם֙ מִכָּל־הַבָּשָׂ֔ר אֲשֶׁר־בּ֖וֹ
ר֥וּחַ חַיִּֽים׃
```

**Pass 1:**
```
וַיָּבֹ֥אוּ אֶל־נֹ֖חַ אֶל־הַתֵּבָ֑ה שְׁנַ֤יִם שְׁנַ֙יִם֙ מִכָּל־הַבָּשָׂ֔ר אֲשֶׁר־בּ֖וֹ רוּחַ חַיִּֽים׃
```

**Pass 2:**
```
וַיָּבֹ֥אוּ אֶל־נֹ֖חַ אֶל־הַתֵּבָ֑ה שְׁנַ֤יִם שְׁנַ֙יִם֙ מִכָּל־הַבָּשָׂ֔ר אֲשֶׁר־בּ֖וֹ ר֥וּחַ חַיִּֽים׃
```

**Pass 3:**
```
וַיָּבֹ֥אוּ אֶל־נֹ֖חַ אֶל־הַתֵּבָ֑ה שְׁנַ֤יִם שְׁנַ֙יִם֙ מִכָּל־הַבָּשָׂ֔ר אֲשֶׁר־בּ֖וֹ ר֥וּחַ חַיִּֽים׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיָּבֹ֥אוּ אֶל־נֹ֖חַ אֶל־הַתֵּבָ֑ה שְׁנַ֤יִם שְׁנַ֙יִם֙ מִכָּל־הַבָּשָׂ֔ר אֲשֶׁר־בּ֖וֹ ר֥וּחַ חַיִּֽים׃
```

**Editorial decision:** _BLANK_

---

### Chapter 8 — 6 verses

#### Genesis 8:5 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וְהַמַּ֗יִם הָיוּ֙ הָל֣וֹךְ וְחָס֔וֹר עַ֖ד הַחֹ֣דֶשׁ הָֽעֲשִׂירִ֑י בָּֽעֲשִׂירִי֙ בְּאֶחָ֣ד לַחֹ֔דֶשׁ
נִרְא֖וּ רָאשֵׁ֥י הֶֽהָרִֽים׃
```

**Pass 1:**
```
וְהַמַּ֗יִם הָיוּ֙ הָל֣וֹךְ וְחָס֔וֹר עַ֖ד הַחֹ֣דֶשׁ הָֽעֲשִׂירִ֑י בָּֽעֲשִׂירִי֙ בְּאֶחָ֣ד לַחֹ֔דֶשׁ
נִרְא֖וּ רָאשֵׁ֥י הֶֽהָרִֽים׃
```

**Pass 2:**
```
וְהַמַּ֗יִם הָיוּ֙ הָל֣וֹךְ וְחָס֔וֹר עַ֖ד הַחֹ֣דֶשׁ הָֽעֲשִׂירִ֑י
בָּֽעֲשִׂירִי֙ בְּאֶחָ֣ד לַחֹ֔דֶשׁ נִרְא֖וּ רָאשֵׁ֥י הֶֽהָרִֽים׃
```

**Pass 3:**
```
וְהַמַּ֗יִם הָיוּ֙ הָל֣וֹךְ וְחָס֔וֹר עַ֖ד הַחֹ֣דֶשׁ הָֽעֲשִׂירִ֑י
בָּֽעֲשִׂירִי֙ בְּאֶחָ֣ד לַחֹ֔דֶשׁ נִרְא֖וּ רָאשֵׁ֥י הֶֽהָרִֽים׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וְהַמַּ֗יִם הָיוּ֙ הָל֣וֹךְ וְחָס֔וֹר עַ֖ד הַחֹ֣דֶשׁ הָֽעֲשִׂירִ֑י
בָּֽעֲשִׂירִי֙ בְּאֶחָ֣ד לַחֹ֔דֶשׁ נִרְא֖וּ רָאשֵׁ֥י הֶֽהָרִֽים׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 8:8 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיְשַׁלַּ֥ח אֶת־הַיּוֹנָ֖ה מֵאִתּ֑וֹ
לִרְאוֹת֙ הֲקַ֣לּוּ הַמַּ֔יִם מֵעַ֖ל פְּנֵ֥י הָֽאֲדָמָֽה׃
```

**Pass 1:**
```
וַיְשַׁלַּ֥ח אֶת־הַיּוֹנָ֖ה מֵאִתּ֑וֹ לִרְאוֹת֙ הֲקַ֣לּוּ הַמַּ֔יִם מֵעַ֖ל פְּנֵ֥י הָֽאֲדָמָֽה׃
```

**Pass 2:**
```
וַיְשַׁלַּ֥ח אֶת־הַיּוֹנָ֖ה מֵאִתּ֑וֹ
לִרְאוֹת֙ הֲקַ֣לּוּ הַמַּ֔יִם מֵעַ֖ל פְּנֵ֥י הָֽאֲדָמָֽה׃
```

**Pass 3:**
```
וַיְשַׁלַּ֥ח אֶת־הַיּוֹנָ֖ה מֵאִתּ֑וֹ
לִרְאוֹת֙ הֲקַ֣לּוּ הַמַּ֔יִם מֵעַ֖ל פְּנֵ֥י הָֽאֲדָמָֽה׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיְשַׁלַּ֥ח אֶת־הַיּוֹנָ֖ה מֵאִתּ֑וֹ
לִרְאוֹת֙ הֲקַ֣לּוּ הַמַּ֔יִם מֵעַ֖ל פְּנֵ֥י הָֽאֲדָמָֽה׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 8:9 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וְלֹֽא־מָצְאָה֩ הַיּוֹנָ֨ה מָנ֜וֹחַ לְכַף־רַגְלָ֗הּ וַתָּ֤שָׁב אֵלָיו֙ אֶל־הַתֵּבָ֔ה
כִּי־מַ֖יִם עַל־פְּנֵ֣י כָל־הָאָ֑רֶץ וַיִּשְׁלַ֤ח יָדוֹ֙ וַיִּקָּחֶ֔הָ
וַיָּבֵ֥א אֹתָ֛הּ אֵלָ֖יו אֶל־הַתֵּבָֽה׃
```

**Pass 1:**
```
וְלֹֽא־מָצְאָה֩ הַיּוֹנָ֨ה מָנ֜וֹחַ לְכַף־רַגְלָ֗הּ
וַתָּ֤שָׁב אֵלָיו֙ אֶל־הַתֵּבָ֔ה
כִּי־מַ֖יִם עַל־פְּנֵ֣י כָל־הָאָ֑רֶץ
וַיִּשְׁלַ֤ח יָדוֹ֙
וַיִּקָּחֶ֔הָ
וַיָּבֵ֥א אֹתָ֛הּ אֵלָ֖יו אֶל־הַתֵּבָֽה׃
```

**Pass 2:**
```
וְלֹֽא־מָצְאָה֩ הַיּוֹנָ֨ה מָנ֜וֹחַ לְכַף־רַגְלָ֗הּ
וַתָּ֤שָׁב אֵלָיו֙ אֶל־הַתֵּבָ֔ה
כִּי־מַ֖יִם עַל־פְּנֵ֣י כָל־הָאָ֑רֶץ
וַיִּשְׁלַ֤ח יָדוֹ֙
וַיִּקָּחֶ֔הָ
וַיָּבֵ֥א אֹתָ֛הּ אֵלָ֖יו אֶל־הַתֵּבָֽה׃
```

**Pass 3:**
```
וְלֹֽא־מָצְאָה֩ הַיּוֹנָ֨ה מָנ֜וֹחַ לְכַף־רַגְלָ֗הּ
וַתָּ֤שָׁב אֵלָיו֙ אֶל־הַתֵּבָ֔ה כִּי־מַ֖יִם עַל־פְּנֵ֣י כָל־הָאָ֑רֶץ
וַיִּשְׁלַ֤ח יָדוֹ֙ וַיִּקָּחֶ֔הָ
וַיָּבֵ֥א אֹתָ֛הּ אֵלָ֖יו אֶל־הַתֵּבָֽה׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וְלֹֽא־מָצְאָה֩ הַיּוֹנָ֨ה מָנ֜וֹחַ לְכַף־רַגְלָ֗הּ
וַתָּ֤שָׁב אֵלָיו֙ אֶל־הַתֵּבָ֔ה
כִּי־מַ֖יִם עַל־פְּנֵ֣י כָל־הָאָ֑רֶץ
וַיִּשְׁלַ֤ח יָדוֹ֙
וַיִּקָּחֶ֔הָ
וַיָּבֵ֥א אֹתָ֛הּ אֵלָ֖יו אֶל־הַתֵּבָֽה׃
```

**Audit firings:**
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): line 2 has finite verb; line 3 has no finite verb but parallel structure (similar length) — probable gapped bicolon (INFORM: propositionally complete).

**Editorial decision:** _BLANK_

---

#### Genesis 8:18 — **MAJORITY** (reassembly: `FALLBACK-TO-SOURCE (TOKEN-MISMATCH at idx 3: src='וּנְשֵֽׁי־בָנָ֖יו' rendered='וְנְשֵֽׁי־בָנָ֖יו')`)

**Source:**
```
וַיֵּ֖צֵא־נֹ֑חַ וּבָנָ֛יו וְאִשְׁתּ֥וֹ וּנְשֵֽׁי־בָנָ֖יו אִתּֽוֹ׃
```

**Pass 1:**
```
וַיֵּ֖צֵא־נֹ֑חַ וּבָנָ֛יו וְאִשְׁתּ֥וֹ וְנְשֵֽׁי־בָנָ֖יו אִתּֽוֹ׃
```

**Pass 2:**
```
וַיֵּ֖צֵא־נֹ֑חַ וּבָנָ֛יו וְאִשְׁתּ֥וֹ וְנְשֵֽׁי־בָנָ֖יו אִתּֽוֹ׃
```

**Pass 3:**
```
וַיֵּ֖צֵא־נֹ֑חַ וּבָנָ֛יו וְאִשְׁתּ֥וֹ וּנְשֵֽׁי־בָנָ֖יו אִתּֽוֹ׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיֵּ֖צֵא־נֹ֑חַ וּבָנָ֛יו וְאִשְׁתּ֥וֹ וּנְשֵֽׁי־בָנָ֖יו אִתּֽוֹ׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 8:21 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיָּ֣רַח יְהוָה֮ אֶת־רֵ֣יחַ הַנִּיחֹחַ֒
וַיֹּ֨אמֶר יְהוָ֜ה אֶל־לִבּ֗וֹ
לֹֽא־אֹ֠סִף לְקַלֵּ֨ל ע֤וֹד אֶת־הָֽאֲדָמָה֙ בַּעֲב֣וּר הָֽאָדָ֔ם
כִּ֠י יֵ֣צֶר לֵ֧ב הָאָדָ֛ם רַ֖ע מִנְּעֻרָ֑יו
וְלֹֽא־אֹסִ֥ף ע֛וֹד לְהַכּ֥וֹת אֶת־כָּל־חַ֖י כַּֽאֲשֶׁ֥ר עָשִֽׂיתִי׃
```

**Pass 1:**
```
וַיָּ֣רַח יְהוָה֮ אֶת־רֵ֣יחַ הַנִּיחֹחַ֒
וַיֹּ֨אמֶר יְהוָ֜ה אֶל־לִבּ֗וֹ
לֹֽא־אֹ֠סִף לְקַלֵּ֨ל ע֤וֹד אֶת־הָֽאֲדָמָה֙ בַּעֲב֣וּר הָֽאָדָ֔ם
כִּ֠י יֵ֣צֶר לֵ֧ב הָאָדָ֛ם רַ֖ע מִנְּעֻרָ֑יו
וְלֹֽא־אֹסִ֥ף ע֛וֹד לְהַכּ֥וֹת אֶת־כָּל־חַ֖י כַּֽאֲשֶׁ֥ר עָשִֽׂיתִי׃
```

**Pass 2:**
```
וַיָּ֣רַח יְהוָה֮ אֶת־רֵ֣יחַ הַנִּיחֹחַ֒
וַיֹּ֨אמֶר יְהוָ֜ה אֶל־לִבּ֗וֹ
לֹֽא־אֹ֠סִף לְקַלֵּ֨ל ע֤וֹד אֶת־הָֽאֲדָמָה֙ בַּעֲב֣וּר הָֽאָדָ֔ם
כִּ֠י יֵ֣צֶר לֵ֣ב הָאָדָ֛ם רַ֖ע מִנְּעֻרָ֑יו
וְלֹֽא־אֹסִ֥ף ע֛וֹד לְהַכּ֥וֹת אֶת־כָּל־חַ֖י כַּֽאֲשֶׁ֥ר עָשִֽׂיתִי׃
```

**Pass 3:**
```
וַיָּ֣רַח יְהוָה֮ אֶת־רֵ֣יחַ הַנִּיחֹחַ֒
וַיֹּ֨אמֶר יְהוָ֜ה אֶל־לִבּ֗וֹ
לֹֽא־אֹ֠סִף לְקַלֵּ֨ל ע֤וֹד אֶת־הָֽאֲדָמָה֙ בַּעֲב֣וּר הָֽאָדָ֔ם
כִּ֠י יֵ֣צֶר לֵ֧ב הָאָדָ֛ם רַ֖ע מִנְּעֻרָ֑יו
וְלֹֽא־אֹסִ֥ף ע֛וֹד לְהַכּ֥וֹת אֶת־כָּל־חַ֖י כַּֽאֲשֶׁ֥ר עָשִֽׂיתִי׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיָּ֣רַח יְהוָה֮ אֶת־רֵ֣יחַ הַנִּיחֹחַ֒
וַיֹּ֨אמֶר יְהוָ֜ה אֶל־לִבּ֗וֹ
לֹֽא־אֹ֠סִף לְקַלֵּ֨ל ע֤וֹד אֶת־הָֽאֲדָמָה֙ בַּעֲב֣וּר הָֽאָדָ֔ם
כִּ֠י יֵ֣צֶר לֵ֧ב הָאָדָ֛ם רַ֖ע מִנְּעֻרָ֑יו
וְלֹֽא־אֹסִ֥ף ע֛וֹד לְהַכּ֥וֹת אֶת־כָּל־חַ֖י כַּֽאֲשֶׁ֥ר עָשִֽׂיתִי׃
```

**Audit firings:**
- `JM157-ki-recitativum` (ADVISORY, tier ADVISORY): line 4 begins כִּי in possible divine-speech context (line 3 has YHWH-class subject) — JUDGMENT-REQUIRED: recitativum vs. causal disambiguation needed.
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): line 3 has finite verb; line 4 has no finite verb but parallel structure (similar length) — probable gapped bicolon (INFORM: propositionally complete).

**Editorial decision:** _BLANK_

---

#### Genesis 8:22 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
עֹ֖ד כָּל־יְמֵ֣י הָאָ֑רֶץ זֶ֡רַע
וְ֠קָצִיר
וְקֹ֨ר
וָחֹ֜ם
וְקַ֧יִץ
וָחֹ֛רֶף
וְי֥וֹם וָלַ֖יְלָה
לֹ֥א יִשְׁבֹּֽתוּ׃
```

**Pass 1:**
```
עֹ֖ד כָּל־יְמֵ֣י הָאָ֑רֶץ זֶ֡רַע וְ֠קָצִיר וְקֹ֨ר וָחֹ֜ם וְקַ֧יִץ וָחֹ֛רֶף וְי֥וֹם וָלַ֖יְלָה לֹ֥א יִשְׁבֹּֽתוּ׃
```

**Pass 2:**
```
עֹ֖ד כָּל־יְמֵ֣י הָאָ֑רֶץ
זֶ֡רַע וְ֠קָצִיר
וְקֹ֨ר וָחֹ֜ם
וְקַ֧יִץ וָחֹ֛רֶף
וְי֥וֹם וָלַ֖יְלָה
לֹ֥א יִשְׁבֹּֽתוּ׃
```

**Pass 3:**
```
עֹ֖ד כָּל־יְמֵ֣י הָאָ֑רֶץ זֶ֡רַע וְ֠קָצִיר וְקֹ֨ר וָחֹ֜ם וְקַ֧יִץ וָחֹ֛רֶף וְי֥וֹם וָלַ֖יְלָה לֹ֥א יִשְׁבֹּֽתוּ׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
עֹ֖ד כָּל־יְמֵ֣י הָאָ֑רֶץ זֶ֡רַע וְ֠קָצִיר וְקֹ֨ר וָחֹ֜ם וְקַ֧יִץ וָחֹ֛רֶף וְי֥וֹם וָלַ֖יְלָה לֹ֥א יִשְׁבֹּֽתוּ׃
```

**Editorial decision:** _BLANK_

---

### Chapter 9 — 8 verses

#### Genesis 9:1 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיְבָ֣רֶךְ אֱלֹהִ֔ים אֶת־נֹ֖חַ וְאֶת־בָּנָ֑יו
וַיֹּ֧אמֶר לָהֶ֛ם
פְּר֥וּ וּרְב֖וּ וּמִלְא֥וּ אֶת־הָאָֽרֶץ׃
```

**Pass 1:**
```
וַיְבָ֣רֶךְ אֱלֹהִ֔ים אֶת־נֹ֖חַ וְאֶת־בָּנָ֑יו
וַיֹּ֧אמֶר לָהֶ֛ם
פְּר֥וּ וּרְב֖וּ וּמִלְא֥וּ אֶת־הָאָֽרֶץ׃
```

**Pass 2:**
```
וַיְבָ֣רֶךְ אֱלֹהִ֔ים אֶת־נֹ֖חַ וְאֶת־בָּנָ֑יו
וַיֹּ֧אמֶר לָהֶ֛ם פְּר֥וּ וּרְב֖וּ וּמִלְא֥וּ אֶת־הָאָֽרֶץ׃
```

**Pass 3:**
```
וַיְבָ֣רֶךְ אֱלֹהִ֔ים אֶת־נֹ֖חַ וְאֶת־בָּנָ֑יו
וַיֹּ֧אמֶר לָהֶ֛ם פְּר֥וּ וּרְב֖וּ וּמִלְא֥וּ אֶת־הָאָֽרֶץ׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיְבָ֣רֶךְ אֱלֹהִ֔ים אֶת־נֹ֖חַ וְאֶת־בָּנָ֑יו
וַיֹּ֧אמֶר לָהֶ֛ם פְּר֥וּ וּרְב֖וּ וּמִלְא֥וּ אֶת־הָאָֽרֶץ׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 9:2 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וּמוֹרַאֲכֶ֤ם וְחִתְּכֶם֙ יִֽהְיֶ֔ה עַ֚ל כָּל־חַיַּ֣ת הָאָ֔רֶץ
וְעַ֖ל כָּל־ע֣וֹף הַשָּׁמָ֑יִם
בְּכֹל֩ אֲשֶׁ֨ר תִּרְמֹ֧שׂ הָֽאֲדָמָ֛ה
וּֽבְכָל־דְּגֵ֥י הַיָּ֖ם
בְּיֶדְכֶ֥ם נִתָּֽנוּ׃
```

**Pass 1:**
```
וּמוֹרַאֲכֶ֤ם וְחִתְּכֶם֙ יִֽהְיֶ֔ה עַ֚ל כָּל־חַיַּ֣ת הָאָ֔רֶץ וְעַ֖ל כָּל־ע֣וֹף הַשָּׁמָ֑יִם בְּכֹל֩ אֲשֶׁ֨ר תִּרְמֹ֧שׂ הָֽאֲדָמָ֛ה וּֽבְכָל־דְּגֵ֥י הַיָּ֖ם
בְּיֶדְכֶ֥ם נִתָּֽנוּ׃
```

**Pass 2:**
```
וּמוֹרַאֲכֶ֤ם וְחִתְּכֶם֙ יִֽהְיֶ֔ה עַ֚ל כָּל־חַיַּ֣ת הָאָ֔רֶץ
וְעַ֖ל כָּל־ע֣וֹף הַשָּׁמָ֑יִם
בְּכֹל֩ אֲשֶׁ֨ר תִּרְמֹ֧שׂ הָֽאֲדָמָ֛ה
וּֽבְכָל־דְּגֵ֥י הַיָּ֖ם
בְּיֶדְכֶ֥ם נִתָּֽנוּ׃
```

**Pass 3:**
```
וּמוֹרַאֲכֶ֤ם וְחִתְּכֶם֙ יִֽהְיֶ֔ה עַ֚ל כָּל־חַיַּ֣ת הָאָ֔רֶץ וְעַ֖ל כָּל־ע֣וֹף הַשָּׁמָ֑יִם בְּכֹל֩ אֲשֶׁ֨ר תִּרְמֹ֧שׂ הָֽאֲדָמָ֛ה וּֽבְכָל־דְּגֵ֥י הַיָּ֖ם
בְּיֶדְכֶ֥ם נִתָּֽנוּ׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וּמוֹרַאֲכֶ֤ם וְחִתְּכֶם֙ יִֽהְיֶ֔ה עַ֚ל כָּל־חַיַּ֣ת הָאָ֔רֶץ וְעַ֖ל כָּל־ע֣וֹף הַשָּׁמָ֑יִם בְּכֹל֩ אֲשֶׁ֨ר תִּרְמֹ֧שׂ הָֽאֲדָמָ֛ה וּֽבְכָל־דְּגֵ֥י הַיָּ֖ם
בְּיֶדְכֶ֥ם נִתָּֽנוּ׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 9:6 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
שֹׁפֵךְ֙ דַּ֣ם הָֽאָדָ֔ם בָּֽאָדָ֖ם
דָּמ֣וֹ יִשָּׁפֵ֑ךְ
כִּ֚י בְּצֶ֣לֶם אֱלֹהִ֔ים עָשָׂ֖ה אֶת־הָאָדָֽם׃
```

**Pass 1:**
```
שֹׁפֵךְ֙ דַּ֣ם הָֽאָדָ֔ם בָּֽאָדָ֖ם
דָּמ֣וֹ יִשָּׁפֵ֑ךְ
כִּ֚י בְּצֶ֣לֶם אֱלֹהִ֔ims עָשָׂ֖ה אֶת־הָאָדָֽם׃
```

**Pass 2:**
```
שֹׁפֵךְ֙ דַּ֣ם הָֽאָדָ֔ם בָּֽאָדָ֖ם דָּמ֣וֹ יִשָּׁפֵ֑ךְ
כִּ֚י בְּצֶ֣לֶם אֱלֹהִ֔ים עָשָׂ֖ה אֶת־הָאָדָֽם׃
```

**Pass 3:**
```
שֹׁפֵךְ֙ דַּ֣ם הָֽאָדָ֔ם בָּֽאָדָ֖ם דָּמ֣וֹ יִשָּׁפֵ֑ךְ
כִּ֚י בְּצֶ֣לֶם אֱלֹהִ֔ים עָשָׂ֖ה אֶת־הָאָדָֽם׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
שֹׁפֵךְ֙ דַּ֣ם הָֽאָדָ֔ם בָּֽאָדָ֖ם דָּמ֣וֹ יִשָּׁפֵ֑ךְ
כִּ֚י בְּצֶ֣לֶם אֱלֹהִ֔ים עָשָׂ֖ה אֶת־הָאָדָֽם׃
```

**Audit firings:**
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): lines 1–2 have similar length (6, 5 words) — possible gapped bicolon (INFORM). Surface length heuristic only.

**Editorial decision:** _BLANK_

---

#### Genesis 9:10 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וְאֵ֨ת כָּל־נֶ֤פֶשׁ הַֽחַיָּה֙ אֲשֶׁ֣ר אִתְּכֶ֔ם בָּע֧וֹף בַּבְּהֵמָ֛ה
וּֽבְכָל־חַיַּ֥ת הָאָ֖רֶץ אִתְּכֶ֑ם
מִכֹּל֙ יֹצְאֵ֣י הַתֵּבָ֔ה לְכֹ֖ל חַיַּ֥ת הָאָֽרֶץ׃
```

**Pass 1:**
```
וְאֵ֨ת כָּל־נֶ֤פֶשׁ הַֽחַיָּה֙ אֲשֶׁ֣ר אִתְּכֶ֔ם בָּע֧וֹף בַּבְּהֵמָ֛ה וּֽבְכָל־חַיַּ֥ת הָאָ֖רֶץ אִתְּכֶ֑ם מִכֹּל֙ יֹצְאֵ֣י הַתֵּבָ֔ה לְכֹ֖ל חַיַּ֥ת הָאָֽרֶץ׃
```

**Pass 2:**
```
וְאֵ֨ת כָּל־נֶ֤פֶשׁ הַֽחַיָּה֙ אֲשֶׁ֣ר אִתְּכֶ֔ם בָּע֧וֹף בַּבְּהֵמָ֛ה
וּֽבְכָל־חַיַּ֥ת הָאָ֖רֶץ אִתְּכֶ֑ם
מִכֹּל֙ יֹצְאֵ֣י הַתֵּבָ֔ה לְכֹ֖ל חַיַּ֥ת הָאָֽרֶץ׃
```

**Pass 3:**
```
וְאֵ֨ת כָּל־נֶ֤פֶשׁ הַֽחַיָּה֙ אֲשֶׁ֣ר אִתְּכֶ֔ם בָּע֧וֹף בַּבְּהֵמָ֛ה וּֽבְכָל־חַיַּ֥ת הָאָ֖רֶץ אִתְּכֶ֑ם מִכֹּל֙ יֹצְאֵ֣י הַתֵּבָ֔ה לְכֹ֖ל חַיַּ֥ת הָאָֽרֶץ׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וְאֵ֨ת כָּל־נֶ֤פֶשׁ הַֽחַיָּה֙ אֲשֶׁ֣ר אִתְּכֶ֔ם בָּע֧וֹף בַּבְּהֵמָ֛ה וּֽבְכָל־חַיַּ֥ת הָאָ֖רֶץ אִתְּכֶ֑ם מִכֹּל֙ יֹצְאֵ֣י הַתֵּבָ֔ה לְכֹ֖ל חַיַּ֥ת הָאָֽרֶץ׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 9:12 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיֹּ֣אמֶר אֱלֹהִ֗ים
זֹ֤את אֽוֹת־הַבְּרִית֙ אֲשֶׁר־אֲנִ֣י נֹתֵ֗ן בֵּינִי֙ וּבֵ֣ינֵיכֶ֔ם
וּבֵ֛ין כָּל־נֶ֥פֶשׁ חַיָּ֖ה אֲשֶׁ֣ר אִתְּכֶ֑ם לְדֹרֹ֖ת עוֹלָֽם׃
```

**Pass 1:**
```
וַיֹּ֣אמֶר אֱלֹהִ֗ים
זֹ֤את אֽוֹת־הַבְּרִית֙ אֲשֶׁר־אֲנִ֣י נֹתֵ֗ן בֵּינִי֙ וּבֵ֣ינֵיכֶ֔ם וּבֵ֛ין כָּל־נֶ֥פֶשׁ חַיָּ֖ה אֲשֶׁ֣ר אִתְּכֶ֑ם לְדֹרֹ֖ת עוֹלָֽם׃
```

**Pass 2:**
```
וַיֹּ֣אמֶר אֱלֹהִ֗ים
זֹ֤את אֽוֹת־הַבְּרִית֙ אֲשֶׁר־אֲנִ֣י נֹתֵ֗ן בֵּינִי֙ וּבֵ֣ינֵיכֶ֔ם
וּבֵ֛ין כָּל־נֶ֥פֶשׁ חַיָּ֖ה אֲשֶׁ֣ר אִתְּכֶ֑ם לְדֹרֹ֖ת עוֹלָֽם׃
```

**Pass 3:**
```
וַיֹּ֣אמֶר אֱלֹהִ֗ים
זֹ֤את אֽוֹת־הַבְּרִית֙ אֲשֶׁר־אֲנִ֣י נֹתֵ֗ן בֵּינִי֙ וּבֵ֣ינֵיכֶ֔ם וּבֵ֛ין כָּל־נֶ֥פֶשׁ חַיָּ֖ה אֲשֶׁ֣ר אִתְּכֶ֑ם לְדֹרֹ֖ת עוֹלָֽם׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיֹּ֣אמֶר אֱלֹהִ֗ים
זֹ֤את אֽוֹת־הַבְּרִית֙ אֲשֶׁר־אֲנִ֣י נֹתֵ֗ן בֵּינִי֙ וּבֵ֣ינֵיכֶ֔ם וּבֵ֛ין כָּל־נֶ֥פֶשׁ חַיָּ֖ה אֲשֶׁ֣ר אִתְּכֶ֑ם לְדֹרֹ֖ת עוֹלָֽם׃
```

**Audit firings:**
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): line 1 has finite verb; line 2 has no finite verb but parallel structure (matching roles: {'s'}) — probable gapped bicolon (INFORM: propositionally complete).

**Editorial decision:** _BLANK_

---

#### Genesis 9:15 — **ALL-DISAGREE** (reassembly: `SOURCE (no resolution at Stage 1)`)

**Source:**
```
וְזָכַרְתִּ֣י אֶת־בְּרִיתִ֗י אֲשֶׁ֤ר בֵּינִי֙ וּבֵ֣ינֵיכֶ֔ם
וּבֵ֛ין כָּל־נֶ֥פֶשׁ חַיָּ֖ה בְּכָל־בָּשָׂ֑ר
וְלֹֽא־יִֽהְיֶ֨ה ע֤וֹד הַמַּ֙יִם֙ לְמַבּ֔וּל
לְשַׁחֵ֖ת כָּל־בָּשָֽׂר׃
```

**Pass 1:**
```
וְזָכַרְתִּ֣י אֶת־בְּרִיתִ֗י אֲשֶׁ֤ר בֵּינִי֙ וּבֵ֣ינֵיכֶ֔ם וּבֵ֛ין כָּל־נֶ֥פֶשׁ חַיָּ֖ה בְּכָל־בָּשָׂ֑ר
וְלֹֽא־יִֽהְיֶ֨ה ע֤וֹד הַמַּ֙יִם֙ לְמַבּ֔וּל לְשַׁחֵ֖ר כָּל־בָּשָֽׂר׃
```

**Pass 2:**
```
וְזָכַרְתִּ֣י אֶת־בְּרִיתִ֗י אֲשֶׁ֤ר בֵּינִי֙ וּבֵ֣ינֵיכֶ֔ם
וּבֵ֛ין כָּל־נֶ֥פֶשׁ חַיָּ֖ה בְּכָל־בָּשָׂ֑ר
וְלֹֽא־יִֽהְיֶ֨ה ע֤וֹד הַמַּ֙יִם֙ לְמַבּ֔וּל לְשַׁחֵ֖ר כָּל־בָּשָֽׂר׃
```

**Pass 3:**
```
וְזָכַרְתִּ֣י אֶת־בְּרִיתִ֗י אֲשֶׁ֤ר בֵּינִי֙ וּבֵ֣ינֵיכֶ֔ם וּבֵ֛ין כָּל־נֶ֥פֶשׁ חַיָּ֖ה בְּכָל־בָּשָׂ֑ר
וְלֹֽא־יִֽהְיֶ֨ה ע֤וֹד הַמַּ֙יִם֙ לְמַבּ֔וּל לְשַׁחֵ֖ת כָּל־בָּשָֽׂר׃
```

**Audit firings:**
- `JM168-purpose-clause` (ADVISORY, tier ADVISORY): line 4 begins with ל-prefixed word ('לְשַׁחֵ֖ת', skel='לשחת') and is short (2 words) — possible purpose-clause infinitive (JUDGMENT-REQUIRED). Surface heuristic.
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): line 1 has finite verb; line 2 has no finite verb but parallel structure (similar length) — probable gapped bicolon (INFORM: propositionally complete).

**Editorial decision:** _BLANK_

---

#### Genesis 9:16 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וְהָיְתָ֥ה הַקֶּ֖שֶׁת בֶּֽעָנָ֑ן
וּרְאִיתִ֗יהָ לִזְכֹּר֙ בְּרִ֣ית עוֹלָ֔ם בֵּ֣ין אֱלֹהִ֔ים
וּבֵין֙ כָּל־נֶ֣פֶשׁ חַיָּ֔ה בְּכָל־בָּשָׂ֖ר אֲשֶׁ֥ר עַל־הָאָֽרֶץ׃
```

**Pass 1:**
```
וְהָיְתָ֥ה הַקֶּ֖שֶׁת בֶּֽעָנָ֑ן
וּרְאִיתִ֗יהָ לִזְכֹּר֙ בְּרִ֣ית עוֹלָ֔ם בֵּ֣ין אֱלֹהִ֔ים וּבֵין֙ כָּל־נֶ֣פֶשׁ חַיָּ֔ה בְּכָל־בָּשָׂ֖ר אֲשֶׁ֥ר עַל־הָאָֽרֶץ׃
```

**Pass 2:**
```
וְהָיְתָ֥ה הַקֶּ֖שֶׁת בֶּֽעָנָ֑ן
וּרְאִיתִ֗יהָ לִזְכֹּר֙ בְּרִ֣ית עוֹלָ֔ם בֵּ֣ין אֱלֹהִ֔ים
וּבֵין֙ כָּל־נֶ֣פֶשׁ חַיָּ֔ה בְּכָל־בָּשָׂ֖ר אֲשֶׁ֥ר עַל־הָאָֽרֶץ׃
```

**Pass 3:**
```
וְהָיְתָ֥ה הַקֶּ֖שֶׁת בֶּֽעָנָ֑ן
וּרְאִיתִ֗יהָ לִזְכֹּר֙ בְּרִ֣ית עוֹלָ֔ם בֵּ֣ין אֱלֹהִ֔ים וּבֵין֙ כָּל־נֶ֣פֶשׁ חַיָּ֔ה בְּכָל־בָּשָׂ֖ר אֲשֶׁ֥ר עַל־הָאָֽרֶץ׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וְהָיְתָ֥ה הַקֶּ֖שֶׁת בֶּֽעָנָ֑ן
וּרְאִיתִ֗יהָ לִזְכֹּר֙ בְּרִ֣ית עוֹלָ֔ם בֵּ֣ין אֱלֹהִ֔ים וּבֵין֙ כָּל־נֶ֣פֶשׁ חַיָּ֔ה בְּכָל־בָּשָׂ֖ר אֲשֶׁ֥ר עַל־הָאָֽרֶץ׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 9:17 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַיֹּ֥אמֶר אֱלֹהִ֖ים אֶל־נֹ֑חַ
זֹ֤את אֽוֹת־הַבְּרִית֙ אֲשֶׁ֣ר הֲקִמֹ֔תִי בֵּינִ֕י
וּבֵ֥ין כָּל־בָּשָׂ֖ר אֲשֶׁ֥ר עַל־הָאָֽרֶץ׃
```

**Pass 1:**
```
וַיֹּ֥אמֶר אֱלֹהִ֖ים אֶל־נֹ֑חַ
זֹ֤את אֽוֹת־הַבְּרִית֙ אֲשֶׁ֣ר הֲקִמֹ֔תִי בֵּינִ֕י וּבֵ֥ין כָּל־בָּשָׂ֖ר אֲשֶׁ֥ר עַל־הָאָֽרֶץ׃
```

**Pass 2:**
```
וַיֹּ֥אמֶר אֱלֹהִ֖ים אֶל־נֹ֑חַ
זֹ֤את אֽוֹת־הַבְּרִית֙ אֲשֶׁ֣ר הֲקִמֹ֔תִי בֵּינִ֕י
וּבֵ֥ין כָּל־בָּשָׂ֖ר אֲשֶׁ֥ר עַל־הָאָֽרֶץ׃
```

**Pass 3:**
```
וַיֹּ֥אמֶר אֱלֹהִ֖ים אֶל־נֹ֑חַ
זֹ֤את אֽוֹת־הַבְּרִית֙ אֲשֶׁ֣ר הֲקִמֹ֔תִי בֵּינִ֕י וּבֵ֥ין כָּל־בָּשָׂ֖ר אֲשֶׁ֥ר עַל־הָאָֽרֶץ׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַיֹּ֥אמֶר אֱלֹהִ֖ים אֶל־נֹ֑חַ
זֹ֤את אֽוֹת־הַבְּרִית֙ אֲשֶׁ֣ר הֲקִמֹ֔תִי בֵּינִ֕י וּבֵ֥ין כָּל־בָּשָׂ֖ר אֲשֶׁ֥ר עַל־הָאָֽרֶץ׃
```

**Editorial decision:** _BLANK_

---

### Chapter 10 — 9 verses

#### Genesis 10:2 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
בְּנֵ֣י יֶ֔פֶת
גֹּ֣מֶר וּמָג֔וֹג וּמָדַ֖י
וְיָוָ֣ן
וְתֻבָ֑ל
וּמֶ֖שֶׁךְ
וְתִירָֽס׃
```

**Pass 1:**
```
בְּנֵ֣י יֶ֔פֶת
גֹּ֣מֶר וּמָג֔וֹג וּמָדַ֖י
וְיָוָ֣ן
וְתֻבָ֑ל
וּמֶ֖שֶׁךְ
וְתִירָֽס׃
```

**Pass 2:**
```
בְּנֵ֣י יֶ֔פֶת
גֹּ֣מֶר וּמָג֔וֹג וּמָדַ֖י
וְיָוָ֣ן
וְתֻבָ֑ל
וּמֶ֖שֶׁךְ
וְתִירָֽס׃
```

**Pass 3:**
```
בְּנֵ֣י יֶ֔פֶת גֹּ֣מֶר וּמָג֔וֹג וּמָדַ֖י וְיָוָ֣ן וְתֻבָ֑ל וּמֶ֖שֶׁךְ וְתִירָֽס׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
בְּנֵ֣י יֶ֔פֶת
גֹּ֣מֶר וּמָג֔וֹג וּמָדַ֖י
וְיָוָ֣ן
וְתֻבָ֑ל
וּמֶ֖שֶׁךְ
וְתִירָֽס׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 10:6 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וּבְנֵ֖י חָ֑ם כּ֥וּשׁ וּמִצְרַ֖יִם
וּפ֥וּט וּכְנָֽעַן׃
```

**Pass 1:**
```
וּבְנֵ֖י חָ֑ם כּ֥וּשׁ וּמִצְרַ֖יִם
וּפ֥וּט וּכְנָֽעַן׃
```

**Pass 2:**
```
וּבְנֵ֖י חָ֑ם כּ֥וּשׁ וּמִצְרַ֖יִם
וּפ֥וּט וּכְנָֽעַן׃
```

**Pass 3:**
```
וּבְנֵ֖י חָ֑ם כּ֥וּשׁ וּמִצְרַ֖יִם וּפ֥וּט וּכְנָֽעַן׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וּבְנֵ֖י חָ֑ם כּ֥וּשׁ וּמִצְרַ֖יִם
וּפ֥וּט וּכְנָֽעַן׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 10:7 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וּבְנֵ֣י כ֔וּשׁ
סְבָא֙ וַֽחֲוִילָ֔ה
וְסַבְתָּ֥ה וְרַעְמָ֖ה
וְסַבְתְּכָ֑א וּבְנֵ֥י רַעְמָ֖ה
שְׁבָ֥א וּדְדָֽן׃
```

**Pass 1:**
```
וּבְנֵ֣י כ֔וּשׁ
סְבָא֙ וַֽחֲוִילָ֔ה
וְסַבְתָּ֥ה וְרַעְמָ֖ה
וְסַבְתְּכָ֑א וּבְנֵ֥י רַעְמָ֖ה
שְׁבָ֥א וּדְדָֽן׃
```

**Pass 2:**
```
וּבְנֵ֣י כ֔וּשׁ
סְבָא֙ וַֽחֲוִילָ֔ה
וְסַבְתָּ֥ה וְרַעְמָ֖ה
וְסַבְתְּכָ֑א וּבְנֵ֥י רַעְמָ֖ה
שְׁבָ֥א וּדְדָֽן׃
```

**Pass 3:**
```
וּבְנֵ֣י כ֔וּשׁ סְבָא֙ וַֽחֲוִילָ֔ה וְסַבְתָּ֥ה וְרַעְמָ֖ה וְסַבְתְּכָ֑א
וּבְנֵ֥י רַעְמָ֖ה שְׁבָ֥א וּדְדָֽן׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וּבְנֵ֣י כ֔וּשׁ
סְבָא֙ וַֽחֲוִילָ֔ה
וְסַבְתָּ֥ה וְרַעְמָ֖ה
וְסַבְתְּכָ֑א וּבְנֵ֥י רַעְמָ֖ה
שְׁבָ֥א וּדְדָֽן׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 10:10 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַתְּהִ֨י רֵאשִׁ֤ית מַמְלַכְתּוֹ֙ בָּבֶ֔ל וְאֶ֖רֶךְ
וְאַכַּ֣ד וְכַלְנֵ֑ה בְּאֶ֖רֶץ שִׁנְעָֽר׃
```

**Pass 1:**
```
וַתְּהִ֨י רֵאשִׁ֤ית מַמְלַכְתּוֹ֙ בָּבֶ֔ל וְאֶ֖רֶךְ
וְאַכַּ֣ד וְכַלְנֵ֑ה בְּאֶ֖רֶץ שִׁנְעָֽר׃
```

**Pass 2:**
```
וַתְּהִ֨י רֵאשִׁ֤ית מַמְלַכְתּוֹ֙ בָּבֶ֔ל וְאֶ֖רֶךְ
וְאַכַּ֣ד וְכַלְנֵ֑ה בְּאֶ֖רֶץ שִׁנְעָֽר׃
```

**Pass 3:**
```
וַתְּהִ֨י רֵאשִׁ֤ית מַמְלַכְתּוֹ֙ בָּבֶ֔ל וְאֶ֖רֶךְ וְאַכַּ֣ד וְכַלְנֵ֑ה בְּאֶ֖רֶץ שִׁנְעָֽר׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַתְּהִ֨י רֵאשִׁ֤ית מַמְלַכְתּוֹ֙ בָּבֶ֔ל וְאֶ֖רֶךְ
וְאַכַּ֣ד וְכַלְנֵ֑ה בְּאֶ֖רֶץ שִׁנְעָֽר׃
```

**Audit firings:**
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): line 1 has finite verb; line 2 has no finite verb but parallel structure (similar length) — probable gapped bicolon (INFORM: propositionally complete).

**Editorial decision:** _BLANK_

---

#### Genesis 10:16 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וְאֶת־הַיְבוּסִי֙ וְאֶת־הָ֣אֱמֹרִ֔י
וְאֵ֖ת הַגִּרְגָּשִֽׁי׃
```

**Pass 1:**
```
וְאֶת־הַיְבוּסִי֙ וְאֶת־הָ֣אֱמֹרִ֔י
וְאֵ֖ת הַגִּרְגָּשִֽׁי׃
```

**Pass 2:**
```
וְאֶת־הַיְבוּסִי֙ וְאֶת־הָ֣אֱמֹרִ֔י
וְאֵ֖ת הַגִּרְגָּשִֽׁי׃
```

**Pass 3:**
```
וְאֶת־הַיְבוּסִי֙ וְאֶת־הָ֣אֱמֹרִ֔י וְאֵ֖ת הַגִּרְגָּשִֽׁי׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וְאֶת־הַיְבוּסִי֙ וְאֶת־הָ֣אֱמֹרִ֔י
וְאֵ֖ת הַגִּרְגָּשִֽׁי׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 10:19 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וַֽיְהִ֞י גְּב֤וּל הַֽכְּנַעֲנִי֙ מִצִּידֹ֔ן בֹּאֲכָ֥ה גְרָ֖רָה
עַד־עַזָּ֑ה בֹּאֲכָ֞ה סְדֹ֧מָה וַעֲמֹרָ֛ה וְאַדְמָ֥ה
וּצְבֹיִ֖ם עַד־לָֽשַׁע׃
```

**Pass 1:**
```
וַֽיְהִ֞י גְּב֤וּל הַֽכְּנַעֲנִי֙ מִצִּידֹ֔ן בֹּאֲכָ֥ה גְרָ֖רָה
עַד־עַזָּ֑ה בֹּאֲכָ֞ה סְדֹ֧מָה וַעֲמֹרָ֛ה וְאַדְמָ֥ה
וּצְבֹיִ֖ם עַד־לָֽשַׁע׃
```

**Pass 2:**
```
וַֽיְהִ֞י גְּב֤וּל הַֽכְּנַעֲנִי֙ מִצִּידֹ֔ן בֹּאֲכָ֥ה גְרָ֖רָה עַד־עַזָּ֑ה
בֹּאֲכָ֞ה סְדֹ֧מָה וַעֲמֹרָ֛ה וְאַדְמָ֥ה וּצְבֹיִ֖ם עַד־לָֽשַׁע׃
```

**Pass 3:**
```
וַֽיְהִ֞י גְּב֤וּל הַֽכְּנַעֲנִי֙ מִצִּידֹ֔ן בֹּאֲכָ֥ה גְרָ֖רָה עַד־עַזָּ֑ה
בֹּאֲכָ֞ה סְדֹ֧מָה וַעֲמֹרָ֛ה וְאַדְמָ֥ה וּצְבֹיִ֖ם עַד־לָֽשַׁע׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וַֽיְהִ֞י גְּב֤וּל הַֽכְּנַעֲנִי֙ מִצִּידֹ֔ן בֹּאֲכָ֥ה גְרָ֖רָה עַד־עַזָּ֑ה
בֹּאֲכָ֞ה סְדֹ֧מָה וַעֲמֹרָ֛ה וְאַדְמָ֥ה וּצְבֹיִ֖ם עַד־לָֽשַׁע׃
```

**Audit firings:**
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): line 1 has finite verb; line 2 has no finite verb but parallel structure (matching roles: {'s'}) — probable gapped bicolon (INFORM: propositionally complete).

**Editorial decision:** _BLANK_

---

#### Genesis 10:22 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
בְּנֵ֥י שֵׁ֖ם עֵילָ֣ם וְאַשּׁ֑וּר וְאַרְפַּכְשַׁ֖ד
וְל֥וּד וַֽאֲרָֽם׃
```

**Pass 1:**
```
בְּנֵ֥י שֵׁ֖ם עֵילָ֣ם וְאַשּׁ֑וּר וְאַרְפַּכְשַׁ֖ד
וְל֥וּד וַֽאֲרָֽם׃
```

**Pass 2:**
```
בְּנֵ֥י שֵׁ֖ם עֵילָ֣ם וְאַשּׁ֑וּר וְאַרְפַּכְשַׁ֖ד
וְל֥וּד וַֽאֲרָֽם׃
```

**Pass 3:**
```
בְּנֵ֥י שֵׁ֖ם עֵילָ֣ם וְאַשּׁ֑וּר וְאַרְפַּכְשַׁ֖ד וְל֥וּד וַֽאֲרָֽם׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
בְּנֵ֥י שֵׁ֖ם עֵילָ֣ם וְאַשּׁ֑וּר וְאַרְפַּכְשַׁ֖ד
וְל֥וּד וַֽאֲרָֽם׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 10:23 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וּבְנֵ֖י אֲרָ֑ם
ע֥וּץ וְח֖וּל
וְגֶ֥תֶר וָמַֽשׁ׃
```

**Pass 1:**
```
וּבְנֵ֖י אֲרָ֑ם
ע֥וּץ וְח֖וּל
וְגֶ֥תֶר וָמַֽשׁ׃
```

**Pass 2:**
```
וּבְנֵ֖י אֲרָ֑ם
ע֥וּץ וְח֖וּל
וְגֶ֥תֶר וָמַֽשׁ׃
```

**Pass 3:**
```
וּבְנֵ֖י אֲרָ֑ם ע֥וּץ וְח֖וּל וְגֶ֥תֶר וָמַֽשׁ׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וּבְנֵ֖י אֲרָ֑ם
ע֥וּץ וְח֖וּל
וְגֶ֥תֶר וָמַֽשׁ׃
```

**Editorial decision:** _BLANK_

---

#### Genesis 10:25 — **MAJORITY** (reassembly: `OK`)

**Source:**
```
וּלְעֵ֥בֶר יֻלַּ֖ד שְׁנֵ֣י בָנִ֑ים
שֵׁ֣ם הָֽאֶחָ֞ד פֶּ֗לֶג כִּ֤י בְיָמָיו֙ נִפְלְגָ֣ה הָאָ֔רֶץ וְשֵׁ֥ם אָחִ֖יו יָקְטָֽן׃
```

**Pass 1:**
```
וּלְעֵ֥בֶר יֻלַּ֖ד שְׁנֵ֣י בָנִ֑ים
שֵׁ֣ם הָֽאֶחָ֞ד פֶּ֗לֶג
כִּ֤י בְיָמָיו֙ נִפְלְגָ֣ה הָאָ֔רֶץ
וְשֵׁ֥ם אָחִ֖יו יָקְטָֽן׃
```

**Pass 2:**
```
וּלְעֵ֥בֶר יֻלַּ֖ד שְׁנֵ֣י בָנִ֑ים
שֵׁ֣ם הָֽאֶחָ֞ד פֶּ֗לֶג כִּ֤י בְיָמָיו֙ נִפְלְגָ֣ה הָאָ֔רֶץ
וְשֵׁ֥ם אָחִ֖יו יָקְטָֽן׃
```

**Pass 3:**
```
וּלְעֵ֥בֶר יֻלַּ֖ד שְׁנֵ֣י בָנִ֑ים
שֵׁ֣ם הָֽאֶחָ֞ד פֶּ֗לֶג כִּ֤י בְיָמָיו֙ נִפְלְגָ֣ה הָאָ֔רֶץ
וְשֵׁ֥ם אָחִ֖יו יָקְטָֽן׃
```

**Resolved draft (source bytes per matching pair's line-break decision):**
```
וּלְעֵ֥בֶר יֻלַּ֖ד שְׁנֵ֣י בָנִ֑ים
שֵׁ֣ם הָֽאֶחָ֞ד פֶּ֗לֶג כִּ֤י בְיָמָיו֙ נִפְלְגָ֣ה הָאָ֔רֶץ
וְשֵׁ֥ם אָחִ֖יו יָקְטָֽן׃
```

**Audit firings:**
- `JM174-gapped-verb` (ADVISORY, tier ADVISORY): line 2 has finite verb; line 3 has no finite verb but parallel structure (matching roles: {'p'}) — probable gapped bicolon (INFORM: propositionally complete).

**Editorial decision:** _BLANK_

---

## Adjudication ask

1. **HARD firings (16)** — per-verse: accept Stage 1 draft (override constraint) or amend line breaks to satisfy.
2. **MAJORITY verses (64)** — accept the matching-pair resolved draft, pick a different pass, or hand-edit.
3. **ALL-DISAGREE verses (6)** — hand-edit; passes diverge enough that no automated resolution is sound.
4. **Recurring class flag**: `JM154-verbless-clause-nucleus, JM157-ki-recitativum, JM168-purpose-clause, JM174-gapped-verb` recur across ≥3 chapters — candidate for catalog-revision review (separate directive; do NOT extend mid-run per §Discipline).

Per directive 1700 §11–17: pilot-branch integration (`atu-pilot-genesis-01`) of one adjudicated chapter (Genesis 1 by default) proceeds after Stan adjudicates the surface above. v2/heb remains untouched until then.
