# Gen 22 mechanical-first pilot — v3 three-way comparison

Comparison of refined v1.5 pipeline against principled cold-eye baseline
AND Lexham Discourse Hebrew Bible (LDHB) reference.


## Headline

| Source | Total ATUs / units |
|---|---|
| Refined pipeline (v1.5 only) | 80 |
| Principled cold-eye | 80 |
| LDHB | 82 |

## Verse-count agreement

| Comparison | Verses with same ATU count |
|---|---|
| All three agree | 16 / 24 |
| Pipeline = cold-eye | 20 / 24 |
| Pipeline = LDHB | 20 / 24 |
| Cold-eye = LDHB | 16 / 24 |

## Boundary-level alignment (pipeline vs LDHB, Hebrew normalization)

| Metric | Value |
|---|---|
| Boundary TP (both place a break) | 52 |
| Boundary FP (pipeline break LDHB doesn't have) | 4 |
| Boundary FN (LDHB break pipeline doesn't have) | 6 |
| Boundary precision (pipeline against LDHB) | 92.9% |
| Boundary recall (LDHB coverage by pipeline) | 89.7% |
| Boundary F1 | 91.2% |

## Per-verse ATU counts

| Verse | Pipeline | Cold-eye | LDHB | All match? |
|---|---|---|---|---|
| 22:1 | 4 | 4 | 5 |  |
| 22:2 | 4 | 4 | 5 |  |
| 22:3 | 5 | 4 | 5 |  |
| 22:4 | 2 | 2 | 2 | ✓ |
| 22:5 | 5 | 5 | 5 | ✓ |
| 22:6 | 4 | 4 | 4 | ✓ |
| 22:7 | 7 | 7 | 7 | ✓ |
| 22:8 | 3 | 3 | 3 | ✓ |
| 22:9 | 5 | 5 | 5 | ✓ |
| 22:10 | 2 | 2 | 2 | ✓ |
| 22:11 | 4 | 4 | 4 | ✓ |
| 22:12 | 5 | 5 | 6 |  |
| 22:13 | 6 | 6 | 6 | ✓ |
| 22:14 | 3 | 2 | 3 |  |
| 22:15 | 1 | 1 | 1 | ✓ |
| 22:16 | 4 | 4 | 4 | ✓ |
| 22:17 | 3 | 4 | 3 |  |
| 22:18 | 2 | 2 | 2 | ✓ |
| 22:19 | 3 | 3 | 3 | ✓ |
| 22:20 | 2 | 2 | 2 | ✓ |
| 22:21 | 1 | 2 | 1 |  |
| 22:22 | 1 | 1 | 1 | ✓ |
| 22:23 | 2 | 2 | 2 | ✓ |
| 22:24 | 2 | 2 | 1 |  |

## Per-verse side-by-side (divergent verses only)


### 22:1  ·  pipeline 4 / cold-eye 4 / LDHB 5

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | וַיְהִ֗י אַחַר֙ הַדְּבָרִ֣ים הָאֵ֔לֶּה וְהָ֣אֱלֹהִ֔ים נִסָּ֖ה אֶת־אַבְרָהָ֑ם | vayhi achar hadevarim ha'eleh veha'elohim nisah et Avraham | וַיְהִ֗י אַחַר֙ הַדְּבָרִ֣ים הָאֵ֔לֶּה וְהָ֣אֱלֹהִ֔ים נִסָּ֖ה אֶת־אַבְרָהָ֑ם |
| 2 | וַיֹּ֣אמֶר אֵלָ֔יו אַבְרָהָ֖ם | vaiyomer elav Avraham | וַיֹּ֣אמֶר אֵלָ֔יו |
| 3 | וַיֹּ֥אמֶר | vaiyomer | אַבְרָהָ֖ם |
| 4 | הִנֵּֽנִי׃ | hineni | וַיֹּ֥אמֶר |
| 5 |  |  | הִנֵּֽנִי׃ |

### 22:2  ·  pipeline 4 / cold-eye 4 / LDHB 5

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | וַיֹּ֡אמֶר | vaiyomer | וַיֹּ֡אמֶר |
| 2 | קַח־נָ֠א אֶת־בִּנְךָ֙ אֶת־יְחִֽידְךָ֤ אֲשֶׁר־אָהַ֨בְתָּ֙ אֶת־יִצְחָ֔ק | kach na et binkha et yechidekha asher ahavta et Yitzchak | קַח־נָ֠א אֶת־בִּנְךָ֙ אֶת־יְחִֽידְךָ֤ אֲשֶׁר־אָהַ֙בְתָּ֙ אֶת־יִצְחָ֔ק |
| 3 | וְלֶךְ־לְךָ֔ אֶל־אֶ֖רֶץ הַמֹּרִיָּ֑ה | velekh lekha el eretz Hamoriyah | וְלֶךְ־לְךָ֔ אֶל־אֶ֖רֶץ הַמֹּרִיָּ֑ה |
| 4 | וְהַעֲלֵ֤הוּ שָׁם֙ לְעֹלָ֔ה עַ֚ל אַחַ֣ד הֶֽהָרִ֔ים אֲשֶׁ֖ר אֹמַ֥ר אֵלֶֽיךָ׃ | veha'alehu sham le'olah al achad heharim asher omar eleikha | וְהַעֲלֵ֤הוּ שָׁם֙ לְעֹלָ֔ה עַ֚ל אַחַ֣ד הֶֽהָרִ֔ים |
| 5 |  |  | אֲשֶׁ֖ר אֹמַ֥ר אֵלֶֽיךָ׃ |

### 22:3  ·  pipeline 5 / cold-eye 4 / LDHB 5

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | וַיַּשְׁכֵּ֨ם אַבְרָהָ֜ם בַּבֹּ֗קֶר | vaiyashkem Avraham baboker | וַיַּשְׁכֵּ֨ם אַבְרָהָ֜ם בַּבֹּ֗קֶר |
| 2 | וַֽיַּחֲבֹשׁ֙ אֶת־חֲמֹרֹ֔ו | vaiyachavosh et chamoro vaiyikach et shenei ne'arav ito ve'et Yitzchak beno | וַֽיַּחֲבֹשׁ֙ אֶת־חֲמֹר֔וֹ |
| 3 | וַיִּקַּ֞ח אֶת־שְׁנֵ֤י נְעָרָיו֙ אִתֹּ֔ו וְאֵ֖ת יִצְחָ֣ק בְּנֹ֑ו | vayvaka atzei olah | וַיִּקַּ֞ח אֶת־שְׁנֵ֤י נְעָרָיו֙ אִתּ֔וֹ וְאֵ֖ת יִצְחָ֣ק בְּנ֑וֹ |
| 4 | וַיְבַקַּע֙ עֲצֵ֣י עֹלָ֔ה | vaiyakom vaiyelekh el hamakom asher amar lo ha'elohim | וַיְבַקַּע֙ עֲצֵ֣י עֹלָ֔ה |
| 5 | וַיָּ֣קָם וַיֵּ֔לֶךְ אֶל־הַמָּקֹ֖ום אֲשֶׁר־אָֽמַר־לֹ֥ו הָאֱלֹהִֽים׃ |  | וַיָּ֣קָם וַיֵּ֔לֶךְ אֶל־הַמָּק֖וֹם אֲשֶׁר־אָֽמַר־ל֥וֹ הָאֱלֹהִֽים׃ |

### 22:12  ·  pipeline 5 / cold-eye 5 / LDHB 6

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | וַיֹּ֗אמֶר | vaiyomer | וַיֹּ֗אמֶר |
| 2 | אַל־תִּשְׁלַ֤ח יָֽדְךָ֙ אֶל־הַנַּ֔עַר | al tishlach yadekha el hana'ar | אַל־תִּשְׁלַ֤ח יָֽדְךָ֙ אֶל־הַנַּ֔עַר |
| 3 | וְאַל־תַּ֥עַשׂ לֹ֖ו מְא֑וּמָּה | ve'al ta'as lo me'umah | וְאַל־תַּ֥עַשׂ ל֖וֹ מְא֑וּמָּה |
| 4 | כִּ֣י׀ עַתָּ֣ה יָדַ֗עְתִּי כִּֽי־יְרֵ֤א אֱלֹהִים֙ אַ֔תָּה | ki atah yada'ti ki yere elohim atah | כִּ֣י׀ עַתָּ֣ה יָדַ֗עְתִּי |
| 5 | וְלֹ֥א חָשַׂ֛כְתָּ אֶת־בִּנְךָ֥ אֶת־יְחִידְךָ֖ מִמֶּֽנִּי׃ | velo chasakhta et binkha et yechidekha mimeni | כִּֽי־יְרֵ֤א אֱלֹהִים֙ אַ֔תָּה |
| 6 |  |  | וְלֹ֥א חָשַׂ֛כְתָּ אֶת־בִּנְךָ֥ אֶת־יְחִידְךָ֖ מִמֶּֽנִּי׃ |

### 22:14  ·  pipeline 3 / cold-eye 2 / LDHB 3

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | וַיִּקְרָ֧א אַבְרָהָ֛ם שֵֽׁם־הַמָּקֹ֥ום הַה֖וּא | vaiyikra Avraham shem hamakom hahu Yahweh yir'eh | וַיִּקְרָ֧א אַבְרָהָ֛ם שֵֽׁם־הַמָּק֥וֹם הַה֖וּא |
| 2 | יְהוָ֣ה׀ יִרְאֶ֑ה אֲשֶׁר֙ יֵאָמֵ֣ר הַיֹּ֔ום | asher ye'amer haiyom behar Yahweh yera'eh | יְהוָ֣ה׀ יִרְאֶ֑ה |
| 3 | בְּהַ֥ר יְהוָ֖ה יֵרָאֶֽה׃ |  | אֲשֶׁר֙ יֵאָמֵ֣ר הַיּ֔וֹם בְּהַ֥ר יְהוָ֖ה יֵרָאֶֽה׃ |

### 22:17  ·  pipeline 3 / cold-eye 4 / LDHB 3

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | כִּֽי־בָרֵ֣ךְ אֲבָרֶכְךָ֗ | ki varekh avarekhkha | כִּֽי־בָרֵ֣ךְ אֲבָרֶכְךָ֗ |
| 2 | וְהַרְבָּ֨ה אַרְבֶּ֤ה אֶֽת־זַרְעֲךָ֙ כְּכֹוכְבֵ֣י הַשָּׁמַ֔יִם וְכַחֹ֕ול אֲשֶׁ֖ר עַל־שְׂפַ֣ת הַיָּ֑ם | veharbah arbeh et zar'akha kechokhvei hashamayim | וְהַרְבָּ֨ה אַרְבֶּ֤ה אֶֽת־זַרְעֲךָ֙ כְּכוֹכְבֵ֣י הַשָּׁמַ֔יִם וְכַח֕וֹל אֲשֶׁ֖ר עַל־שְׂפַ֣ת הַיָּ֑ם |
| 3 | וְיִרַ֣שׁ זַרְעֲךָ֔ אֵ֖ת שַׁ֥עַר אֹיְבָֽיו׃ | vekhachol asher al sefat haiyam | וְיִרַ֣שׁ זַרְעֲךָ֔ אֵ֖ת שַׁ֥עַר אֹיְבָֽיו׃ |
| 4 |  | veyirash zar'akha et sha'ar oyevav |  |

### 22:21  ·  pipeline 1 / cold-eye 2 / LDHB 1

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | אֶת־ע֥וּץ בְּכֹרֹ֖ו וְאֶת־בּ֣וּז אָחִ֑יו וְאֶת־קְמוּאֵ֖ל אֲבִ֥י אֲרָֽם׃ | et Utz bekhoro ve'et Buz achiv | אֶת־ע֥וּץ בְּכֹר֖וֹ וְאֶת־בּ֣וּז אָחִ֑יו וְאֶת־קְמוּאֵ֖ל אֲבִ֥י אֲרָֽם׃ |
| 2 |  | ve'et Kemu'el avi Aram |  |

### 22:24  ·  pipeline 2 / cold-eye 2 / LDHB 1

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | וּפִֽילַגְשֹׁ֖ו וּשְׁמָ֣הּ רְאוּמָ֑ה | ufilagsho ushemah Re'umah | וּפִֽילַגְשׁ֖וֹ וּשְׁמָ֣הּ רְאוּמָ֑ה וַתֵּ֤לֶד גַּם־הִוא֙ אֶת־טֶ֣בַח וְאֶת־גַּ֔חַם וְאֶת־תַּ֖חַשׁ וְאֶֽת־מַעֲכָֽה׃ ס |
| 2 | וַתֵּ֤לֶד גַּם־הִוא֙ אֶת־טֶ֣בַח וְאֶת־גַּ֔חַם וְאֶת־תַּ֖חַשׁ וְאֶֽת־מַעֲכָֽה׃ ס | vateled gam hi et Tevach ve'et Gacham ve'et Tachash ve'et Ma'akhah |  |