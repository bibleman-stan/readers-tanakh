# Isaiah 53 mechanical-first pilot — v3 three-way comparison

Comparison of refined v1.5 pipeline against principled cold-eye baseline AND Lexham Discourse Hebrew Bible (LDHB).


## Headline

| Source | Total ATUs / units |
|---|---|
| Refined pipeline (v1.5 only) | 53 |
| Principled cold-eye | 45 |
| LDHB | 48 |

## Verse-count agreement

| Comparison | Verses with same ATU count |
|---|---|
| All three agree | 6 / 12 |
| Pipeline = cold-eye | 7 / 12 |
| Pipeline = LDHB | 7 / 12 |
| Cold-eye = LDHB | 7 / 12 |

## Boundary-level alignment (pipeline vs LDHB, Hebrew normalization)

| Metric | Value |
|---|---|
| Boundary TP (both place a break) | 34 |
| Boundary FP (pipeline break LDHB doesn't have) | 7 |
| Boundary FN (LDHB break pipeline doesn't have) | 2 |
| Boundary precision (pipeline against LDHB) | 82.9% |
| Boundary recall (LDHB coverage by pipeline) | 94.4% |
| Boundary F1 | 88.3% |

## Per-verse ATU counts

| Verse | Pipeline | Cold-eye | LDHB | All match? |
|---|---|---|---|---|
| 53:1 | 2 | 2 | 2 | ✓ |
| 53:2 | 7 | 4 | 5 |  |
| 53:3 | 6 | 4 | 5 |  |
| 53:4 | 3 | 3 | 4 |  |
| 53:5 | 4 | 4 | 4 | ✓ |
| 53:6 | 3 | 2 | 3 |  |
| 53:7 | 8 | 5 | 4 |  |
| 53:8 | 4 | 4 | 4 | ✓ |
| 53:9 | 4 | 4 | 4 | ✓ |
| 53:10 | 3 | 4 | 4 |  |
| 53:11 | 3 | 3 | 3 | ✓ |
| 53:12 | 6 | 6 | 6 | ✓ |

## Per-verse side-by-side (divergent verses only)


### 53:2  ·  pipeline 7 / cold-eye 4 / LDHB 5

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | וַיַּ֨עַל כַּיֹּונֵ֜ק לְפָנָ֗יו | vaiya'al | kaiyonek | lefanav | וַיַּ֨עַל כַּיּוֹנֵ֜ק לְפָנָ֗יו |
| 2 | וְכַשֹּׁ֨רֶשׁ֙ מֵאֶ֣רֶץ צִיָּ֔ה | vekhashoresh | me'eretz | tziyah | וְכַשֹּׁ֙רֶשׁ֙ מֵאֶ֣רֶץ צִיָּ֔ה לֹא־תֹ֥אַר ל֖וֹ |
| 3 | לֹא־תֹ֥אַר לֹ֖ו | lo | to'ar | lo | velo | hadar | וְלֹ֣א הָדָ֑ר |
| 4 | וְלֹ֣א הָדָ֑ר | venir'ehu | velo | mar'eh | venechmedehu | וְנִרְאֵ֥הוּ וְלֹֽא־מַרְאֶ֖ה |
| 5 | וְנִרְאֵ֥הוּ |  | וְנֶחְמְדֵֽהוּ׃ |
| 6 | וְלֹֽא־מַרְאֶ֖ה |  |  |
| 7 | וְנֶחְמְדֵֽהוּ׃ |  |  |

### 53:3  ·  pipeline 6 / cold-eye 4 / LDHB 5

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | נִבְזֶה֙ | nivzeh | vachadal | ishim | נִבְזֶה֙ וַחֲדַ֣ל אִישִׁ֔ים |
| 2 | וַחֲדַ֣ל אִישִׁ֔ים | ish | makh'ovot | vidua | choli | אִ֥ישׁ מַכְאֹב֖וֹת |
| 3 | אִ֥ישׁ מַכְאֹבֹ֖ות | ukhemaster | panim | mimenu | וִיד֣וּעַ חֹ֑לִי |
| 4 | וִיד֣וּעַ חֹ֑לִי | nivzeh | velo | chashavnuhu | וּכְמַסְתֵּ֤ר פָּנִים֙ מִמֶּ֔נּוּ נִבְזֶ֖ה |
| 5 | וּכְמַסְתֵּ֤ר פָּנִים֙ מִמֶּ֔נּוּ נִבְזֶ֖ה |  | וְלֹ֥א חֲשַׁבְנֻֽהוּ׃ |
| 6 | וְלֹ֥א חֲשַׁבְנֻֽהוּ׃ |  |  |

### 53:4  ·  pipeline 3 / cold-eye 3 / LDHB 4

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | אָכֵ֤ן חֳלָיֵ֨נוּ֙ ה֣וּא נָשָׂ֔א | akhen | cholayenu | hu | nasa | אָכֵ֤ן חֳלָיֵ֙נוּ֙ ה֣וּא נָשָׂ֔א |
| 2 | וּמַכְאֹבֵ֖ינוּ סְבָלָ֑ם | umakh'oveinu | sevalam | וּמַכְאֹבֵ֖ינוּ סְבָלָ֑ם |
| 3 | וַאֲנַ֣חְנוּ חֲשַׁבְנֻ֔הוּ נָג֛וּעַ מֻכֵּ֥ה אֱלֹהִ֖ים וּמְעֻנֶּֽה׃ | va'anachnu | chashavnuhu | nagua | mukeh | elohim | ume'uneh | וַאֲנַ֣חְנוּ חֲשַׁבְנֻ֔הוּ נָג֛וּעַ |
| 4 |  |  | מֻכֵּ֥ה אֱלֹהִ֖ים וּמְעֻנֶּֽה׃ |

### 53:6  ·  pipeline 3 / cold-eye 2 / LDHB 3

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | כֻּלָּ֨נוּ֙ כַּצֹּ֣אן תָּעִ֔ינוּ | kulanu | katzon | ta'inu | ish | ledarko | paninu | כֻּלָּ֙נוּ֙ כַּצֹּ֣אן תָּעִ֔ינוּ |
| 2 | אִ֥ישׁ לְדַרְכֹּ֖ו פָּנִ֑ינוּ | Vayahweh | hifgia | bo | et | avon | kulanu | אִ֥ישׁ לְדַרְכּ֖וֹ פָּנִ֑ינוּ |
| 3 | וַֽיהוָה֙ הִפְגִּ֣יעַ בֹּ֔ו אֵ֖ת עֲוֹ֥ן כֻּלָּֽנוּ׃ |  | וַֽיהוָה֙ הִפְגִּ֣יעַ בּ֔וֹ אֵ֖ת עֲוֺ֥ן כֻּלָּֽנוּ׃ |

### 53:7  ·  pipeline 8 / cold-eye 5 / LDHB 4

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | נִגַּ֨שׂ | Nigas | vehu | na'aneh | נִגַּ֨שׂ וְה֣וּא נַעֲנֶה֮ |
| 2 | וְה֣וּא נַעֲנֶה֮ | velo | yiftach | piv | וְלֹ֣א יִפְתַּח־פִּיו֒ |
| 3 | וְלֹ֣א יִפְתַּח־פִּיו֒ | kaseh | latevach | yuval | כַּשֶּׂה֙ לַטֶּ֣בַח יוּבָ֔ל |
| 4 | כַּשֶּׂה֙ | ukherachel | lifnei | gozezeiha | Ne'elamah | וּכְרָחֵ֕ל לִפְנֵ֥י גֹזְזֶ֖יהָ נֶאֱלָ֑מָה וְלֹ֥א יִפְתַּ֖ח פִּֽיו׃ |
| 5 | לַטֶּ֣בַח יוּבָ֔ל | velo | yiftach | piv |  |
| 6 | וּכְרָחֵ֕ל |  |  |
| 7 | לִפְנֵ֥י גֹזְזֶ֖יהָ נֶאֱלָ֑מָה |  |  |
| 8 | וְלֹ֥א יִפְתַּ֖ח פִּֽיו׃ |  |  |

### 53:10  ·  pipeline 3 / cold-eye 4 / LDHB 4

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | וַיהוָ֞ה חָפֵ֤ץ דַּכְּאֹו֙ הֶֽחֱלִ֔י | Vayahweh | chafetz | dake'o | hecheli | וַיהוָ֞ה חָפֵ֤ץ דַּכְּאוֹ֙ הֶֽחֱלִ֔י |
| 2 | אִם־תָּשִׂ֤ים אָשָׁם֙ נַפְשֹׁ֔ו יִרְאֶ֥ה זֶ֖רַע יַאֲרִ֣יךְ יָמִ֑ים | im | tasim | asham | nafsho | yir'eh | zera | אִם־תָּשִׂ֤ים אָשָׁם֙ נַפְשׁ֔וֹ יִרְאֶ֥ה זֶ֖רַע |
| 3 | וְחֵ֥פֶץ יְהוָ֖ה בְּיָדֹ֥ו יִצְלָֽח׃ | ya'arikh | yamim | יַאֲרִ֣יךְ יָמִ֑ים |
| 4 |  | vechefetz | Yahweh | beyado | yitzlach | וְחֵ֥פֶץ יְהוָ֖ה בְּיָד֥וֹ יִצְלָֽח׃ |