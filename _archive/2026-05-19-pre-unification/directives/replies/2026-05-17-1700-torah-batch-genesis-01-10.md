# Editorial Review — Genesis chapters 01–10

**Directive:** `2026-05-17-1700-torah-batch-genesis-01-10`
**Book:** `01-genesis`
**Chapters:** 1–10 (10 chapters, 267 verses)
**Generated from:** `data/reports/atu_pipeline/01-genesis/chapter-NN.jsonl` + `chapter-NN-audit.jsonl`

**Auto-applicable** (UNANIMOUS + MAJORITY Stage 1, no Stage 2 HARD conflict): **261/267 verses (97.8%).** These integrate to v2/heb verbatim from the JSONL `draft` field.

**Decisions required:** **8** = 6 ALL-DISAGREE verses + 2 HARD-firing classes.

---

## Stage 1 — agreement summary

| Ch | Verses | UNANIMOUS | MAJORITY | ALL-DISAGREE | HARD | ADVISORY |
|---|---|---|---|---|---|---|
| 1 | 31 | 30 (97%) | 1 | 0 | 0 | 22 |
| 2 | 25 | 24 (96%) | 1 | 0 | 0 | 15 |
| 3 | 24 | 11 (46%) | 9 | 4 | 0 | 18 |
| 4 | 26 | 21 (81%) | 5 | 0 | 1 | 18 |
| 5 | 32 | 16 (50%) | 16 | 0 | 0 | 4 |
| 6 | 22 | 17 (77%) | 4 | 1 | 1 | 13 |
| 7 | 24 | 18 (75%) | 6 | 0 | 0 | 12 |
| 8 | 22 | 16 (73%) | 6 | 0 | 0 | 7 |
| 9 | 29 | 21 (72%) | 7 | 1 | 0 | 12 |
| 10 | 32 | 23 (72%) | 9 | 0 | 0 | 10 |

**Aggregate:** UNANIMOUS 197 · MAJORITY 64 · ALL-DISAGREE 6 · HARD 2 · ADVISORY 131

---

## HARD-firing constraint classes (2 classes, 2 firings)

**Per-class adjudication required.** One decision applies to all listed instances in this batch.

Decision options per class:
- `ACCEPT` — override the constraint for these verses (Stage-1 draft stands)
- `AMEND` — re-render the listed verses with the corrective line-break pattern (specify pattern)
- `KEEP-SOURCE` — drop the Stage-1 draft for these verses; preserve source line breaks

### 1. `JM129-construct-chain` — Construct-chain integrity (precedence 2)

**Instances:** 1

- **Genesis 4:22** — NPofNP construct chain split across sense lines 1 / 2: regens 'חֹרֵ֥שׁ' on line 1, rectum 'נְחֹ֖שֶׁת' on line 2
  - `constituent_rule`: NPofNP, `regens_text`: חֹרֵ֥שׁ, `regens_line`: 1, `rectum_text`: נְחֹ֖שֶׁת, `rectum_line`: 2, `pass`: A-constituent

**Decision (class `JM129-construct-chain`):** _BLANK_

---

### 2. `JM-wayehi-fef-protasis` — Wayehi-FEF protasis integrity (precedence 4)

**Instances:** 1

- **Genesis 6:1** — wayehi-FEF SPLIT required: וַיְהִי + protasis + main clause appear collapsed on line 1 — protasis and main clause must occupy separate sense-lines
  - `arm`: SPLIT, `wayehi_line`: 1, `finite_verb_count_on_line`: 2, `line`: וַֽיְהִי֙ כִּֽי־הֵחֵ֣ל הָֽאָדָ֔ם לָרֹ֖ב עַל־פְּנֵ֣י הָֽאֲדָמָ֑ה, `macula_used`: True

**Decision (class `JM-wayehi-fef-protasis`):** _BLANK_

---

## ALL-DISAGREE verses (6 verses)

**Per-verse adjudication required.** All three Opus passes diverged.

Decision options per verse:
- `ACCEPT-PASS-N` (1/2/3) — adopt that pass's rendering
- `KEEP-SOURCE` — preserve source line breaks
- `AMEND` — specify your own line-break layout

### Genesis 3:3 — `ALL-DISAGREE`

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
**Decision (Genesis 3:3):** _BLANK_

---

### Genesis 3:6 — `ALL-DISAGREE`

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
**Decision (Genesis 3:6):** _BLANK_

---

### Genesis 3:14 — `ALL-DISAGREE`

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
**Decision (Genesis 3:14):** _BLANK_

---

### Genesis 3:17 — `ALL-DISAGREE`

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
**Decision (Genesis 3:17):** _BLANK_

---

### Genesis 6:4 — `ALL-DISAGREE`

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
**Decision (Genesis 6:4):** _BLANK_

---

### Genesis 9:15 — `ALL-DISAGREE`

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
**Decision (Genesis 9:15):** _BLANK_

---

## ADVISORY firings (rollup, no per-verse action)

| Constraint | Count | Chapters fired |
|---|---|---|
| `JM174-gapped-verb` | 102 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 |
| `JM168-purpose-clause` | 8 | 1, 2, 3, 4, 9 |
| `JM154-verbless-clause-nucleus` | 8 | 1, 2, 5, 7 |
| `JM125-coordinated-objects` | 4 | 1, 3 |
| `JM157-ki-recitativum` | 3 | 2, 6, 8 |
| `JM147-vocative-extraclausal` | 3 | 3, 7 |
| `JM125-verb-object-bond` | 1 | 6 |
| `JM157-complement-integrity` | 1 | 6 |
| `JM103e-compound-prep-object` | 1 | 6 |

---

## Catalog-revision candidates (recurring patterns — ≥3 chapters)

Per `feedback_three_lens_default_for_plans`: surface only, do NOT extend canon mid-run. Queue for post-batch §7.3 audit cycle.

- `JM174-gapped-verb` — HARD 0 / ADVISORY 102 across chapters 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
- `JM168-purpose-clause` — HARD 0 / ADVISORY 8 across chapters 1, 2, 3, 4, 9
- `JM154-verbless-clause-nucleus` — HARD 0 / ADVISORY 8 across chapters 1, 2, 5, 7
- `JM157-ki-recitativum` — HARD 0 / ADVISORY 3 across chapters 2, 6, 8

---

## Integration path (after adjudication)

1. Fill `_BLANK_` decisions above.
2. Tanakh-Claude reads this file, applies decisions.
3. Auto-applicable verses (261) + adjudicated decisions integrate to `data/text-files/v2/heb/01-genesis/genesis-NN.txt` on pilot branch.
4. Pre-commit hook cascades (refresh_book → propagate_editorial_layers → regenerate_english → build_books → baseline-check).
5. Merge to main; push; tanakh-reader.com rebuilds.
