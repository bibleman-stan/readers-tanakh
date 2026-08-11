# Psalm 1 mechanical-first pilot — v3 three-way comparison

Comparison of refined v1.5 pipeline against principled cold-eye baseline AND Lexham Discourse Hebrew Bible (LDHB).


## Headline

| Source | Total ATUs / units |
|---|---|
| Refined pipeline (v1.5 only) | 14 |
| Principled cold-eye | 14 |
| LDHB | 16 |

## Verse-count agreement

| Comparison | Verses with same ATU count |
|---|---|
| All three agree | 4 / 6 |
| Pipeline = cold-eye | 6 / 6 |
| Pipeline = LDHB | 4 / 6 |
| Cold-eye = LDHB | 4 / 6 |

## Boundary-level alignment (pipeline vs LDHB, Hebrew normalization)

| Metric | Value |
|---|---|
| Boundary TP (both place a break) | 8 |
| Boundary FP (pipeline break LDHB doesn't have) | 0 |
| Boundary FN (LDHB break pipeline doesn't have) | 2 |
| Boundary precision (pipeline against LDHB) | 100.0% |
| Boundary recall (LDHB coverage by pipeline) | 80.0% |
| Boundary F1 | 88.9% |

## Per-verse ATU counts

| Verse | Pipeline | Cold-eye | LDHB | All match? |
|---|---|---|---|---|
| 1:1 | 3 | 3 | 4 |  |
| 1:2 | 2 | 2 | 2 | ✓ |
| 1:3 | 3 | 3 | 4 |  |
| 1:4 | 2 | 2 | 2 | ✓ |
| 1:5 | 2 | 2 | 2 | ✓ |
| 1:6 | 2 | 2 | 2 | ✓ |

## Per-verse side-by-side (divergent verses only)


### 1:1  ·  pipeline 3 / cold-eye 3 / LDHB 4

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | אַ֥שְֽׁרֵי־הָאִ֗ישׁ אֲשֶׁ֤ר׀ לֹ֥א הָלַךְ֮ בַּעֲצַ֢ת רְשָׁ֫עִ֥ים | ashrei | ha'ish | asher | lo | halakh | ba'atzat | resha'im | אַ֥שְֽׁרֵי־הָאִ֗ישׁ |
| 2 | וּבְדֶ֣רֶךְ חַ֭טָּאִים לֹ֥א עָמָ֑ד | uvederekh | chata'im | lo | amad | אֲשֶׁ֤ר׀ לֹ֥א הָלַךְ֮ בַּעֲצַ֪ת רְשָׁ֫עִ֥ים |
| 3 | וּבְמֹושַׁ֥ב לֵ֝צִ֗ים לֹ֣א יָשָֽׁב׃ | uvemoshav | letzim | lo | yashav | וּבְדֶ֣רֶךְ חַ֭טָּאִים לֹ֥א עָמָ֑ד |
| 4 |  |  | וּבְמוֹשַׁ֥ב לֵ֝צִ֗ים לֹ֣א יָשָֽׁב׃ |

### 1:3  ·  pipeline 3 / cold-eye 3 / LDHB 4

| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |
|---|---|---|---|
| 1 | וְֽהָיָ֗ה כְּעֵץ֮ שָׁת֢וּל עַֽל־פַּלְגֵ֫י מָ֥יִם אֲשֶׁ֤ר פִּרְיֹ֨ו׀ יִתֵּ֬ן בְּעִתֹּ֗ו | vehayah | ke'etz | shatul | al | palgei | mayim | asher | piryo | yiten | be'ito | וְֽהָיָ֗ה כְּעֵץ֮ שָׁת֪וּל עַֽל־פַּלְגֵ֫י מָ֥יִם |
| 2 | וְעָלֵ֥הוּ לֹֽא־יִבֹּ֑ול | ve'alehu | lo | yibol | אֲשֶׁ֤ר פִּרְיֹ֨ו׀ יִתֵּ֬ן בְּעִתּ֗וֹ |
| 3 | וְכֹ֖ל אֲשֶׁר־יַעֲשֶׂ֣ה יַצְלִֽיחַ׃ | vekhol | asher | ya'aseh | yatzliach | וְעָלֵ֥הוּ לֹֽא־יִבּ֑וֹל |
| 4 |  |  | וְכֹ֖ל אֲשֶׁר־יַעֲשֶׂ֣ה יַצְלִֽיחַ׃ |