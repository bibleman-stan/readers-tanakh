# Leviticus 11 mechanical-first pilot — v3 three-way comparison

Comparison of refined v1.5 pipeline against principled cold-eye baseline AND Lexham Discourse Hebrew Bible (LDHB).


## Headline

| Source | Total ATUs / units |
|---|---|
| Refined pipeline (v1.5 only) | 41 |
| Principled cold-eye | 30 |
| LDHB | 37 |

## Verse-count agreement

| Comparison | Verses with same ATU count |
|---|---|
| All three agree | 3 / 12 |
| Pipeline = cold-eye | 3 / 12 |
| Pipeline = LDHB | 7 / 12 |
| Cold-eye = LDHB | 4 / 12 |

## Boundary-level alignment (pipeline vs LDHB, Hebrew normalization)

| Metric | Value |
|---|---|
| Boundary TP (both place a break) | 23 |
| Boundary FP (pipeline break LDHB doesn't have) | 6 |
| Boundary FN (LDHB break pipeline doesn't have) | 2 |
| Boundary precision (pipeline against LDHB) | 79.3% |
| Boundary recall (LDHB coverage by pipeline) | 92.0% |
| Boundary F1 | 85.2% |

## Per-verse ATU counts

| Verse | Pipeline | Cold-eye | LDHB | All match? |
|---|---|---|---|---|
| 11:1 | 1 | 1 | 1 | ✓ |
| 11:2 | 2 | 2 | 2 | ✓ |
| 11:3 | 5 | 2 | 4 |  |
| 11:4 | 5 | 3 | 5 |  |
| 11:5 | 4 | 2 | 4 |  |
| 11:6 | 4 | 2 | 4 |  |
| 11:7 | 5 | 3 | 4 |  |
| 11:8 | 3 | 3 | 3 | ✓ |
| 11:9 | 3 | 4 | 2 |  |
| 11:10 | 3 | 4 | 4 |  |
| 11:11 | 3 | 2 | 3 |  |
| 11:12 | 3 | 2 | 1 |  |

## Per-verse side-by-side (divergent verses only)


### 11:3  ·  pipeline 5 / cold-eye 2 / LDHB 4

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | כֹּ֣ל׀ מַפְרֶ֣סֶת פַּרְסָ֗ה | kol | mafreset | parsah | veshosa'at | shesa | perasot | ma'alat | gerah | babehemah | כֹּ֣ל׀ |
| 2 | וְשֹׁסַ֤עַת שֶׁ֨סַע֙ פְּרָסֹ֔ת | otah | tokhelu | מַפְרֶ֣סֶת פַּרְסָ֗ה וְשֹׁסַ֤עַת שֶׁ֙סַע֙ פְּרָסֹ֔ת |
| 3 | מַעֲלַ֥ת גֵּרָ֖ה |  | מַעֲלַ֥ת גֵּרָ֖ה בַּבְּהֵמָ֑ה |
| 4 | בַּבְּהֵמָ֑ה |  | אֹתָ֖הּ תֹּאכֵֽלוּ׃ |
| 5 | אֹתָ֖הּ תֹּאכֵֽלוּ׃ |  |  |

### 11:4  ·  pipeline 5 / cold-eye 3 / LDHB 5

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | אַ֤ךְ אֶת־זֶה֙ לֹ֣א תֹֽאכְל֔וּ מִֽמַּעֲלֵי֙ הַגֵּרָ֔ה וּמִמַּפְרִיסֵ֖י הַפַּרְסָ֑ה | akh | et | zeh | lo | tokhelu | mima'alei | hagerah | umimafrisei | haparsah | אַ֤ךְ אֶת־זֶה֙ לֹ֣א תֹֽאכְל֔וּ מִֽמַּעֲלֵי֙ הַגֵּרָ֔ה וּמִמַּפְרִיסֵ֖י הַפַּרְסָ֑ה |
| 2 | אֶֽת־הַ֠גָּמָל | et | hagamol | ki | ma'aleh | gerah | hu | ufarsah | einenu | mafris | אֶֽת־הַ֠גָּמָל |
| 3 | כִּֽי־מַעֲלֵ֨ה גֵרָ֜ה ה֗וּא | tame | hu | lakhem | כִּֽי־מַעֲלֵ֨ה גֵרָ֜ה ה֗וּא |
| 4 | וּפַרְסָה֙ אֵינֶ֣נּוּ מַפְרִ֔יס |  | וּפַרְסָה֙ אֵינֶ֣נּוּ מַפְרִ֔יס |
| 5 | טָמֵ֥א ה֖וּא לָכֶֽם׃ |  | טָמֵ֥א ה֖וּא לָכֶֽם׃ |

### 11:5  ·  pipeline 4 / cold-eye 2 / LDHB 4

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | וְאֶת־הַשָּׁפָ֗ן | ve'et | hashafan | ki | ma'aleh | gerah | hu | ufarsah | lo | yafris | וְאֶת־הַשָּׁפָ֗ן |
| 2 | כִּֽי־מַעֲלֵ֤ה גֵרָה֙ ה֔וּא | tame | hu | lakhem | כִּֽי־מַעֲלֵ֤ה גֵרָה֙ ה֔וּא |
| 3 | וּפַרְסָ֖ה לֹ֣א יַפְרִ֑יס |  | וּפַרְסָ֖ה לֹ֣א יַפְרִ֑יס |
| 4 | טָמֵ֥א ה֖וּא לָכֶֽם׃ |  | טָמֵ֥א ה֖וּא לָכֶֽם׃ |

### 11:6  ·  pipeline 4 / cold-eye 2 / LDHB 4

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | וְאֶת־הָאַרְנֶ֗בֶת | ve'et | ha'arnevet | ki | ma'alat | gerah | hi | ufarsah | lo | hifrisah | וְאֶת־הָאַרְנֶ֗בֶת |
| 2 | כִּֽי־מַעֲלַ֤ת גֵּרָה֙ הִ֔וא | teme'ah | hi | lakhem | כִּֽי־מַעֲלַ֤ת גֵּרָה֙ הִ֔וא |
| 3 | וּפַרְסָ֖ה לֹ֣א הִפְרִ֑יסָה |  | וּפַרְסָ֖ה לֹ֣א הִפְרִ֑יסָה |
| 4 | טְמֵאָ֥ה הִ֖וא לָכֶֽם׃ |  | טְמֵאָ֥ה הִ֖וא לָכֶֽם׃ |

### 11:7  ·  pipeline 5 / cold-eye 3 / LDHB 4

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | וְאֶת־הַ֠חֲזִיר | ve'et | hachazir | ki | mafris | parsah | hu | veshosa | shesa | parsah | vehu | וְאֶת־הַ֠חֲזִיר |
| 2 | כִּֽי־מַפְרִ֨יס פַּרְסָ֜ה ה֗וּא | gerah | lo | yigar | כִּֽי־מַפְרִ֨יס פַּרְסָ֜ה ה֗וּא וְשֹׁסַ֥ע שֶׁ֙סַע֙ פַּרְסָ֔ה |
| 3 | וְשֹׁסַ֥ע שֶׁ֨סַע֙ פַּרְסָ֔ה | tame | hu | lakhem | וְה֖וּא גֵּרָ֣ה לֹֽא־יִגָּ֑ר |
| 4 | וְה֖וּא גֵּרָ֣ה לֹֽא־יִגָּ֑ר |  | טָמֵ֥א ה֖וּא לָכֶֽם׃ |
| 5 | טָמֵ֥א ה֖וּא לָכֶֽם׃ |  |  |

### 11:9  ·  pipeline 3 / cold-eye 4 / LDHB 2

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | אֶת־זֶה֙ תֹּֽאכְל֔וּ מִכֹּ֖ל אֲשֶׁ֣ר בַּמָּ֑יִם | et | zeh | tokhelu | mikol | asher | bamayim | אֶת־זֶה֙ תֹּֽאכְל֔וּ מִכֹּ֖ל אֲשֶׁ֣ר בַּמָּ֑יִם |
| 2 | כֹּ֣ל אֲשֶׁר־לֹו֩ סְנַפִּ֨יר וְקַשְׂקֶ֜שֶׂת בַּמַּ֗יִם בַּיַּמִּ֛ים וּבַנְּחָלִ֖ים | kol | asher | lo | senapir | vekaskeset | bamayim | baiyamim | כֹּ֣ל אֲשֶׁר־לוֹ֩ סְנַפִּ֨יר וְקַשְׂקֶ֜שֶׂת בַּמַּ֗יִם בַּיַּמִּ֛ים וּבַנְּחָלִ֖ים אֹתָ֥ם תֹּאכֵֽלוּ׃ |
| 3 | אֹתָ֥ם תֹּאכֵֽלוּ׃ | uvanechalim |  |
| 4 |  | otam | tokhelu |  |

### 11:10  ·  pipeline 3 / cold-eye 4 / LDHB 4

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | וְכֹל֩ אֲשֶׁ֨ר אֵֽין־לֹ֜ו סְנַפִּ֣יר וְקַשְׂקֶ֗שֶׂת בַּיַּמִּים֙ וּבַנְּחָלִ֔ים | vekhol | asher | ein | lo | senapir | vekaskeset | baiyamim | וְכֹל֩ אֲשֶׁ֨ר אֵֽין־ל֜וֹ סְנַפִּ֣יר וְקַשְׂקֶ֗שֶׂת |
| 2 | מִכֹּל֙ שֶׁ֣רֶץ הַמַּ֔יִם וּמִכֹּ֛ל נֶ֥פֶשׁ הַחַיָּ֖ה אֲשֶׁ֣ר בַּמָּ֑יִם | uvanechalim | mikol | sheretz | hamayim | בַּיַּמִּים֙ וּבַנְּחָלִ֔ים |
| 3 | שֶׁ֥קֶץ הֵ֖ם לָכֶֽם׃ | umikol | nefesh | hachaiyah | asher | bamayim | מִכֹּל֙ שֶׁ֣רֶץ הַמַּ֔יִם וּמִכֹּ֛ל נֶ֥פֶשׁ הַחַיָּ֖ה אֲשֶׁ֣ר בַּמָּ֑יִם |
| 4 |  | sheketz | hem | lakhem | שֶׁ֥קֶץ הֵ֖ם לָכֶֽם׃ |

### 11:11  ·  pipeline 3 / cold-eye 2 / LDHB 3

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | וְשֶׁ֖קֶץ יִהְי֣וּ לָכֶ֑ם | vesheketz | yihyu | lakhem | וְשֶׁ֖קֶץ יִהְי֣וּ לָכֶ֑ם |
| 2 | מִבְּשָׂרָם֙ לֹ֣א תֹאכֵ֔לוּ | mibesaram | lo | tokhelu | ve'et | nivlatam | teshaketzu | מִבְּשָׂרָם֙ לֹ֣א תֹאכֵ֔לוּ |
| 3 | וְאֶת־נִבְלָתָ֖ם תְּשַׁקֵּֽצוּ׃ |  | וְאֶת־נִבְלָתָ֖ם תְּשַׁקֵּֽצוּ׃ |

### 11:12  ·  pipeline 3 / cold-eye 2 / LDHB 1

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | כֹּ֣ל אֲשֶׁ֥ר אֵֽין־לֹ֛ו סְנַפִּ֥יר וְקַשְׂקֶ֖שֶׂת | kol | asher | ein | lo | senapir | vekaskeset | bamayim | כֹּ֣ל אֲשֶׁ֥ר אֵֽין־ל֛וֹ סְנַפִּ֥יר וְקַשְׂקֶ֖שֶׂת בַּמָּ֑יִם שֶׁ֥קֶץ ה֖וּא לָכֶֽם׃ |
| 2 | בַּמָּ֑יִם | sheketz | hu | lakhem |  |
| 3 | שֶׁ֥קֶץ ה֖וּא לָכֶֽם׃ |  |  |