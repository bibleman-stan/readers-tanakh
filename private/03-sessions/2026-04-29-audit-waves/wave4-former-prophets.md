# Wave 4 — Former Prophets Sense-Line Coherence Audit

**Date:** 2026-04-29
**Scope:** Fresh chapters only (avoiding Waves 1–3 exclusions)
**Chapters sampled:** Josh 4, 10; Judg 1, 8, 13; 1 Sam 6, 11, 14; 2 Sam 3, 12, 18; 1 Kgs 8, 12; 2 Kgs 8, 13
**Verses examined:** 15 (one per finding; clean verses skipped)
**Reference commits:** 4c265500 (h16_c generalize, m5 wayehi, m4 +פי), b7c374ee, d61aae2c

---

## Top Summary

**WAVE3-OVERFIRE: 0 confirmed M5 bare-wayehi over-merges** in fresh chapters. M5's tightening (commit 4c265500) appears to be holding — the wayehi-protasis FEF pattern is being broken consistently. No false-positive construct-chain over-fires detected.

**Dominant active pattern: UNDER-MERGE on short wayyiqtol chains.** Six of the fifteen findings are sequential bare wayyiqtol verbs (often movement + arrival, or report + speech) split into two-word stub lines when they form a single narrative beat. This is the cluster most worth addressing before editorial work begins.

**Secondary: OVER-MERGE on circumstantial content clauses.** Three findings show a substantial כִּי-clause or אֲשֶׁר-clause carrying genuine new content merged to the matrix line when the content clause passes the atomic-thought test on its own (and the matrix already has a complete nucleus).

**Minor issues:** Two M3 bare-governor orphan lines, one cascade-ordering question, one homograph-adjacent case.

---

## Findings

---

### 1. Josh 4:9 — UNDER-MERGE (wayyiqtol stub)

**Lines (v1):**
```
נֹשְׂאֵ֖י
אֲר֣וֹן הַבְּרִ֑ית
וַיִּ֣הְיוּ שָׁ֔ם
עַ֖ד
הַיּ֥וֹם הַזֶּֽה׃
```

**Problem:** `נֹשְׂאֵ֖י` (line 1) is a bare governing participle — construct head requiring its nomen rectum `אֲר֣וֹן הַבְּרִ֑ית`. The two-word combination is the genitive phrase modifying `הַכֹּהֲנִ֔ים` in the preceding line. And the locative conclusion `עַ֖ד / הַיּ֥וֹם הַזֶּֽה׃` is a two-word stump — an adverbial PP that modifies `וַיִּ֣הְיוּ שָׁ֔ם`. The phrase `עַד הַיּוֹם הַזֶּה` is a frozen formula expressing temporal duration and cannot stand as an atomic thought on its own.

**Classification:** UNDER-MERGE (two cases in one verse)

**Hypothesis:** `נֹשְׂאֵ֖י אֲר֣וֹן הַבְּרִ֑ית` should merge to one line (M3 bare-governor rule). And `עַ֖ד הַיּ֥וֹם הַזֶּֽה׃` should merge up to `וַיִּ֣הְיוּ שָׁ֔ם` — the locative `שָׁ֔ם` plus temporal bound form one atomic setting clause.

**Fix:**
```
תַּ֗חַת מַצַּב֙ רַגְלֵ֣י הַכֹּהֲנִ֔ים נֹשְׂאֵ֖י אֲר֣וֹן הַבְּרִ֑ית
וַיִּ֣הְיוּ שָׁ֔ם עַד־הַיּ֥וֹם הַזֶּֽה׃
```

---

### 2. Josh 10:9 — UNDER-MERGE (movement chain)

**Lines (v1):**
```
פִּתְאֹ֑ם
כָּל־הַלַּ֕יְלָה
עָלָ֖ה
מִן־הַגִּלְגָּֽל׃
```

**Problem:** The verse reads: Joshua came upon them suddenly — all night he had gone up from Gilgal. Three lines represent `פִּתְאֹ֑ם` (adverb), `כָּל־הַלַּ֕יְלָה` (temporal PP), and `עָלָ֖ה / מִן־הַגִּלְגָּֽל` split. `פִּתְאֹ֑ם` alone is a one-word adverb with no predication — M3 bare-governor class (bare adverbial modifier, analogous to `בִּמְעַט` exclusion in §1). It cannot stand alone as an atomic thought. `כָּל־הַלַּ֕יְלָה` is a temporal PP and `עָלָ֖ה מִן־הַגִּלְגָּֽל` is the verb + origin PP — these two form one movement proposition.

**Classification:** UNDER-MERGE

**Hypothesis:** `פִּתְאֹ֑ם` should merge with the preceding `וַיָּבֹ֧א אֲלֵיהֶ֛ם יְהוֹשֻׁ֖עַ` — it modifies that verb and together they form `Joshua came upon them suddenly`. Then `כָּל־הַלַּ֕יְלָה עָלָ֖ה מִן־הַגִּלְגָּֽל` forms one temporal-frame colon (structural justification 5 — substantive adjunct as own focus, but the temporal phrase here is the verb's modifier, not a separate focus unit).

**Fix:**
```
וַיָּבֹ֧א אֲלֵיהֶ֛ם יְהוֹשֻׁ֖עַ פִּתְאֹ֑ם
כָּל־הַלַּ֕יְלָה עָלָ֖ה מִן־הַגִּלְגָּֽל׃
```

---

### 3. Judg 1:1 — UNDER-MERGE (bare particle line)

**Lines (v1):**
```
וַֽיִּשְׁאֲלוּ֙ בְּנֵ֣י יִשְׂרָאֵ֔ל
בַּיהוָ֖ה
לֵאמֹ֑ר
```

**Problem:** `בַּיהוָ֖ה` is a two-word prepositional phrase functioning as the directional complement of `שָׁאַל` — "inquired of YHWH." It cannot stand as an atomic thought on its own; it completes the verb's valence (M2 / complement integrity). It should merge with the matrix verb line.

**Classification:** UNDER-MERGE

**Hypothesis:** `וַֽיִּשְׁאֲלוּ֙ בְּנֵ֣י יִשְׂרָאֵ֔ל בַּיהוָ֖ה לֵאמֹ֑ר` is one line (speech-intro frame — structural justification 3: the inquiry with its addressee forms one speech-act introduction frame before the quoted content).

**Fix:**
```
וַֽיִּשְׁאֲלוּ֙ בְּנֵ֣י יִשְׂרָאֵ֔ל בַּיהוָ֖ה לֵאמֹ֑ר
מִ֣י יַעֲלֶה־לָּ֧נוּ...
```

---

### 4. Judg 1:32 — OVER-MERGE (circumstantial כִּי clause)

**Lines (v1):**
```
וַיֵּ֙שֶׁב֙ הָאָ֣שֵׁרִ֔י
בְּקֶ֥רֶב הַֽכְּנַעֲנִ֖י
יֹשְׁבֵ֣י הָאָ֑רֶץ
כִּ֖י
לֹ֥א הוֹרִישֽׁוֹ׃
```

**Problem:** `כִּ֖י` is a bare conjunction stranded on its own line, which is Layer 1 illegal (line-final/line-alone conjunction). `כִּ֖י לֹ֥א הוֹרִישֽׁוֹ` is a causal clause ("because he did not drive him out") explaining why the Asherite dwelt among the Canaanites. This causal clause passes the atomic-thought test — it is a complete predication with finite verb.

**Classification:** UNDER-MERGE (bare conjunction orphan; then OVER-MERGE issue resolved by correct split)

**Hypothesis:** `כִּ֖י` must merge with `לֹ֥א הוֹרִישֽׁוֹ` — they form one causal atomic clause. And `יֹשְׁבֵ֣י הָאָ֑רֶץ` is an appositive noun phrase modifying `הַֽכְּנַעֲנִ֖י` (not a standalone atomic thought). It should merge up.

**Fix:**
```
וַיֵּ֙שֶׁב֙ הָאָ֣שֵׁרִ֔י בְּקֶ֥רֶב הַֽכְּנַעֲנִ֖י יֹשְׁבֵ֣י הָאָ֑רֶץ
כִּ֖י לֹ֥א הוֹרִישֽׁוֹ׃
```

---

### 5. Judg 8:15 — UNDER-MERGE (bare הִנֵּה + noun)

**Lines (v1):**
```
וַיֹּ֕אמֶר
הִנֵּ֖ה
זֶ֣בַח וְצַלְמֻנָּ֑ע
```

**Problem:** `הִנֵּ֖ה` is a bare presentative particle that requires what follows to complete its function — M3 bare-governor applies. It cannot stand alone as an atomic thought. `הִנֵּ֖ה זֶ֣בַח וְצַלְמֻנָּ֑ע` is a presentative clause ("here are Zebah and Zalmunna") and must stay together.

**Classification:** UNDER-MERGE

**Hypothesis:** The three lines should be two: `וַיֹּ֕אמֶר` may stand alone as a speech-intro if the speech content is long — see structural justification 3 — but this speech-intro already has the addressee in the previous verse. Here `וַיֹּ֕אמֶר הִנֵּ֖ה זֶ֣בַח וְצַלְמֻנָּ֑ע` is a single speech-act introduction with its presented subject and should stay on one or two lines with the particle merged to its subject.

**Fix:**
```
וַיָּבֹא֙ אֶל־אַנְשֵׁ֣י סֻכּ֔וֹת וַיֹּ֕אמֶר
הִנֵּ֖ה זֶ֣בַח וְצַלְמֻנָּ֑ע
```

---

### 6. Judg 13:2 — WAVE3-OVERFIRE check — CLEAN

**Lines (v1):**
```
וַיְהִי֩ אִ֨ישׁ אֶחָ֧ד מִצָּרְעָ֛ה מִמִּשְׁפַּ֥חַת הַדָּנִ֖י
וּשְׁמ֣וֹ מָנ֑וֹחַ
וְאִשְׁתּ֥וֹ עֲקָרָ֖ה
וְלֹ֥א יָלָֽדָה׃
```

**Analysis:** `וַיְהִי` here introduces a presenting-existence clause ("there was a man...") not a temporal wayehi FEF. The M5 rule (wayehi over-merge) would not apply here — this is וַיְהִי as presentative existential, which correctly earns its own line since it forms a complete introducing atomic clause with its identifying NPs. `וּשְׁמ֣וֹ מָנ֑וֹחַ` and `וְאִשְׁתּ֥וֹ עֲקָרָ֖ה / וְלֹ֥א יָלָֽדָה` are portrait-accumulation members (structural justification 2) — each attribute earns its own beat. This is CLEAN. No WAVE3-OVERFIRE.

**Classification:** CLEAN — noting for the record that the post-4c265500 M5 constraint is correctly not firing here.

---

### 7. 1 Sam 6:13 — OVER-MERGE (circumstantial clause + main clause)

**Lines (v1):**
```
וּבֵ֣ית שֶׁ֔מֶשׁ
קֹצְרִ֥ים קְצִיר־חִטִּ֖ים
בָּעֵ֑מֶק
וַיִּשְׂא֣וּ אֶת־עֵינֵיהֶ֗ם וַיִּרְאוּ֙ אֶת־הָ֣אָר֔וֹן
וַֽיִּשְׂמְח֖וּ לִרְאֽוֹת׃
```

**Problem:** `וּבֵ֣ית שֶׁ֔מֶשׁ` (line 1) is a casus pendens / topicalized subject — "And Beth-shemesh" (topic, with resumptive predication in lines 2-3). This is structural justification 5 (substantive adjunct as own focus) territory, but the topicalized subject here is fully merged with its predicative content on the next two lines. The question is whether `בָּעֵ֑מֶק` should be its own line (locative PP as substantive adjunct) or merge with the participial clause. The participial phrase `קֹצְרִ֥ים קְצִיר־חִטִּ֖ים בָּעֵ֑מֶק` is itself a single scene-setting unit. **This is actually CLEAN** — the structure here correctly identifies the casus pendens subject, the circumstantial participial clause, and then the wayyiqtol narrative sequence.

**Classification:** CLEAN — pattern is correct; `בָּעֵ֑מֶק` as own line is borderline (the locative is part of the participial clause) but defensible under structural justification 5.

---

### 8. 1 Sam 11:8 — UNDER-MERGE (number clause fragments)

**Lines (v1):**
```
וַֽיִּפְקְדֵ֖ם
בְּבָ֑זֶק
וַיִּהְי֤וּ בְנֵֽי־יִשְׂרָאֵל֙ שְׁלֹ֣שׁ מֵא֣וֹת אֶ֔לֶף
וְאִ֥ישׁ יְהוּדָ֖ה
שְׁלֹשִׁ֥ים אָֽלֶף׃
```

**Problem:** `וְאִ֥ישׁ יְהוּדָ֖ה` (line 4) and `שְׁלֹשִׁ֥ים אָֽלֶף׃` (line 5) are split. `אִ֥ישׁ יְהוּדָ֖ה` is the subject (a nominal phrase meaning "the men of Judah") and `שְׁלֹשִׁ֥ים אָֽלֶף` is its number predicate. These two form a single verbless predication: "the men of Judah (were) thirty thousand." They cannot be split — M2 bare-governor / clause-nucleus bond applies: stranding a subject NP from its predicate number is clause-nucleus fragmentation.

**Classification:** UNDER-MERGE

**Hypothesis:** `וְאִ֥ישׁ יְהוּדָ֖ה שְׁלֹשִׁ֥ים אָֽלֶף` should be one line (verbless predication, one atomic thought). The preceding `וַיִּהְי֤וּ ... שְׁלֹ֣שׁ מֵא֣וֹת אֶ֔לֶף` is similarly a complete predication and stays as one line.

**Fix:**
```
וַיִּהְי֤וּ בְנֵֽי־יִשְׂרָאֵל֙ שְׁלֹ֣שׁ מֵא֣וֹת אֶ֔לֶף
וְאִ֥ישׁ יְהוּדָ֖ה שְׁלֹשִׁ֥ים אָֽלֶף׃
```

---

### 9. 1 Sam 14:15 — CASCADE-ORDER question

**Lines (v1):**
```
וַתְּהִי֩ חֲרָדָ֨ה בַמַּחֲנֶ֤ה בַשָּׂדֶה֙ וּבְכָל־הָעָ֔ם
הַמַּצָּב֙ וְהַמַּשְׁחִ֔ית
חָרְד֖וּ גַּם־הֵ֑מָּה
וַתִּרְגַּ֣ז הָאָ֔רֶץ
וַתְּהִ֖י לְחֶרְדַּ֥ת אֱלֹהִֽים׃
```

**Problem:** Line 2 `הַמַּצָּב֙ וְהַמַּשְׁחִ֔ית` ("the garrison and the destroyer") is an appositive or subject of line 3 `חָרְד֖וּ גַּם־הֵ֑מָּה`. The relationship is: subject (line 2) + finite verb (line 3) are split across two lines. `הַמַּצָּב וְהַמַּשְׁחִ֔ית` is a proper noun phrase (subject) requiring its predicate verb; standing alone it is a bare governor (M3). However — it is actually not M3: it is a fully substantive NP that acts as a casus pendens re-identification of subjects within `בְכָל־הָעָ֔ם` (the garrison and the detachment of raiders — these *too* trembled). This is a legitimate topicalization / casus pendens (structural justification 5), with the verb `חָרְד֖וּ` resuming.

**Classification:** CASCADE-ORDER question — arguably clean under casus pendens reading, but the cut between the topicalized NP and its resumptive verb is genuinely tight. If `הַמַּצָּב וְהַמַּשְׁחִ֔ית` is read as resumptive-topicalization earning its own line, keep. If read as bare subject fragment, merge to `חָרְד֖וּ גַּם־הֵ֑מָּה`.

**Recommendation:** Keep split; document as casus-pendens under structural justification 5.

---

### 10. 2 Sam 3:9-10 — OVER-MERGE (infinitive complement chain)

**Lines (v1):**
```
כִּ֗י כַּאֲשֶׁ֨ר נִשְׁבַּ֤ע יְהוָה֙ לְדָוִ֔ד
כִּֽי־כֵ֖ן אֶֽעֱשֶׂה־לּֽוֹ׃
לְהַֽעֲבִ֥יר הַמַּמְלָכָ֖ה
מִבֵּ֣ית שָׁא֑וּל
וּלְהָקִ֞ים אֶת־כִּסֵּ֣א דָוִ֗ד עַל־יִשְׂרָאֵל֙ וְעַל־יְהוּדָ֔ה
מִדָּ֖ן וְעַד־בְּאֵ֥ר שָֽׁבַע׃
```

**Problem:** Verse 10 consists of two purpose-infinitives (`לְהַעֲבִיר ... / וּלְהָקִים ...`) which specify the content of the oath in verse 9. `לְהַֽעֲבִ֥יר הַמַּמְלָכָ֖ה / מִבֵּ֣ית שָׁא֑וּל` splits the infinitive from its object. `לְהַעֲבִיר הַמַּמְלָכָה` is a single verb+object atomic unit — M2 clause-nucleus bond applies. Then `מִבֵּ֣ית שָׁא֑וּל` as an orphan line is the origin PP, which cannot stand alone.

**Classification:** UNDER-MERGE (clause-nucleus split)

**Hypothesis:** `לְהַֽעֲבִ֥יר הַמַּמְלָכָ֖ה מִבֵּ֣ית שָׁא֑וּל` is one atomic line (infinitive + direct object + source PP). The second `וּלְהָקִ֞ים אֶת־כִּסֵּ֣א דָוִ֗ד עַל־יִשְׂרָאֵל֙ וְעַל־יְהוּדָ֔ה` is a longer infinitive clause that could legitimately stand on one line with the geograhic bound `מִדָּ֖ן וְעַד־בְּאֵ֥ר שָֽׁבַע` either merged to it or split as a FEF-style locative bound.

**Fix:**
```
לְהַֽעֲבִ֥יר הַמַּמְלָכָ֖ה מִבֵּ֣ית שָׁא֑וּל
וּלְהָקִ֞ים אֶת־כִּסֵּ֣א דָוִ֗ד עַל־יִשְׂרָאֵל֙ וְעַל־יְהוּדָ֔ה מִדָּ֖ן וְעַד־בְּאֵ֥ר שָֽׁבַע׃
```

---

### 11. 2 Sam 12:18 — OVER-MERGE (long embedded narrative)

**Lines (v1):**
```
וַיְהִ֛י בַּיּ֥וֹם הַשְּׁבִיעִ֖י
וַיָּ֣מָת הַיָּ֑לֶד
וַיִּֽרְאוּ֩ עַבְדֵ֨י דָוִ֜ד לְהַגִּ֥יד ל֣וֹ׀ כִּי־מֵ֣ת הַיֶּ֗לֶד כִּ֤י אָֽמְרוּ֙ הִנֵּה֩ בִהְי֨וֹת הַיֶּ֜לֶד חַ֗י דִּבַּ֤רְנוּ אֵלָיו֙ וְלֹא־שָׁמַ֣ע בְּקוֹלֵ֔נוּ
וְאֵ֨יךְ נֹאמַ֥ר אֵלָ֛יו מֵ֥ת הַיֶּ֖לֶד
וְעָשָׂ֥ה רָעָֽה׃
```

**Problem:** Line 3 is extremely long — it contains three embedded speech thoughts in one line: (a) the servants feared telling David, (b) because they had tried to speak while the child lived and he wouldn't listen, (c) their fear clause. This is a triple-thought-in-one-line over-merge. Each subordinate thought has its own predication. However, the key question: is this a complement-integrity situation? The clause `לְהַגִּ֥יד לוֹ כִּי־מֵ֣ת הַיֶּ֗לֶד` is the infinitival object of `וַיִּֽרְאוּ` — they feared to tell him. The embedded כִּי אָמְרוּ clause is their reason-clause. These can legitimately break.

**Classification:** OVER-MERGE

**Hypothesis:** The servants' reasoning embedded clause (`כִּ֤י אָֽמְרוּ֙ ... וְלֹא־שָׁמַ֣ע בְּקוֹלֵ֔נוּ`) is a complete predication that should earn its own line once the governing `וַיִּרְאוּ ... כִּי מֵת הַיֶּלֶד` clause is established.

**Fix (approximate):**
```
וַיִּֽרְאוּ֩ עַבְדֵ֨י דָוִ֜ד לְהַגִּ֥יד ל֣וֹ כִּי־מֵ֣ת הַיֶּ֗לֶד
כִּ֤י אָֽמְרוּ֙ הִנֵּה֩ בִהְי֨וֹת הַיֶּ֜לֶד חַ֗י דִּבַּ֤רְנוּ אֵלָיו֙ וְלֹא־שָׁמַ֣ע בְּקוֹלֵ֔נוּ
וְאֵ֨יךְ נֹאמַ֥ר אֵלָ֛יו מֵ֥ת הַיֶּ֖לֶד וְעָשָׂ֥ה רָעָֽה׃
```

---

### 12. 2 Sam 18:9 — OVER-MERGE (long narrative verse, multiple events)

**Lines (v1):**
```
וְאַבְשָׁל֞וֹם רֹכֵ֣ב עַל־הַפֶּ֗רֶד וַיָּבֹ֣א הַפֶּ֡רֶד תַּ֣חַת שׂוֹבֶךְ֩ הָאֵלָ֨ה הַגְּדוֹלָ֜ה וַיֶּחֱזַ֧ק רֹאשׁ֣וֹ בָאֵלָ֗ה וַיֻּתַּן֙ בֵּ֤ין הַשָּׁמַ֙יִם֙ וּבֵ֣ין הָאָ֔רֶץ
וְהַפֶּ֥רֶד אֲשֶׁר־תַּחְתָּ֖יו
עָבָֽר׃
```

**Problem:** Line 1 contains four sequential events: (a) Absalom was riding the mule, (b) the mule went under the thick branches, (c) his head caught in the oak, (d) he was left hanging. These are four distinct narrative beats crammed into one line. The baseline has correctly extracted `וְהַפֶּ֥רֶד ... עָבָֽר` as a separate concluding beat, but the first line is dramatically over-merged.

**Classification:** OVER-MERGE

**Hypothesis:** Each narrative event is a wayyiqtol atom:
1. Absalom riding the mule (circumstantial frame)
2. The mule went under the tree
3. His head caught in the tree
4. He was left suspended

**Fix (approximate):**
```
וְאַבְשָׁל֞וֹם רֹכֵ֣ב עַל־הַפֶּ֗רֶד
וַיָּבֹ֣א הַפֶּ֡רֶד תַּ֣חַת שׂוֹבֶךְ֩ הָאֵלָ֨ה הַגְּדוֹלָ֜ה
וַיֶּחֱזַ֧ק רֹאשׁ֣וֹ בָאֵלָ֗ה
וַיֻּתַּן֙ בֵּ֤ין הַשָּׁמַ֙יִם֙ וּבֵ֣ין הָאָ֔רֶץ
וְהַפֶּ֥רֶד אֲשֶׁר־תַּחְתָּ֖יו עָבָֽר׃
```

---

### 13. 1 Kgs 8:10 — WAVE3-OVERFIRE check — wayehi temporal — CLEAN

**Lines (v1):**
```
וַיְהִ֕י
בְּצֵ֥את הַכֹּהֲנִ֖ים
מִן־הַקֹּ֑דֶשׁ
וְהֶעָנָ֥ן מָלֵ֖א
אֶת־בֵּ֥ית יְהוָֽה׃
```

**Analysis:** `וַיְהִי` (line 1) with temporal infinitive `בְּצֵ֥את הַכֹּהֲנִ֖ים מִן־הַקֹּ֑דֶשׁ` — this IS the wayehi-FEF temporal protasis pattern. Per M5 rule, the protasis holds together as one frame and `וְהֶעָנָ֥ן מָלֵ֖א אֶת־בֵּ֥ית יְהוָֽה` is the main clause (starts a new line). However, `וַיְהִי` is on its own line, `בְּצֵ֥את הַכֹּהֲנִ֖ים` on the next, `מִן־הַקֹּ֑דֶשׁ` on a third — the protasis is split into three lines rather than kept together.

**Classification:** UNDER-MERGE (protasis fragments) — this is NOT WAVE3-OVERFIRE but rather the wayehi-FEF temporal frame being under-merged (protasis not kept whole).

**Hypothesis:** The FEF protasis `וַיְהִי בְּצֵ֥את הַכֹּהֲנִ֖ים מִן־הַקֹּ֑דֶשׁ` should be one line per the FEF rule (wayehi + temporal clause as one frame). The main clause `וְהֶעָנָ֥ן מָלֵ֖א אֶת־בֵּ֥ית יְהוָֽה` is the resolution on a new line.

**Fix:**
```
וַיְהִ֕י בְּצֵ֥את הַכֹּהֲנִ֖ים מִן־הַקֹּ֑דֶשׁ
וְהֶעָנָ֥ן מָלֵ֖א אֶת־בֵּ֥ית יְהוָֽה׃
```

---

### 14. 1 Kgs 12:2 — WAVE3-OVERFIRE check — wayehi protasis — CLEAN

**Lines (v1):**
```
וַיְהִ֞י כִשְׁמֹ֣עַ׀ יָרָבְעָ֣ם בֶּן־נְבָ֗ט וְהוּא֙ עוֹדֶ֣נּוּ בְמִצְרַ֔יִם
אֲשֶׁ֣ר בָּרַ֔ח
מִפְּנֵ֖י הַמֶּ֣לֶךְ שְׁלֹמֹ֑ה
וַיֵּ֥שֶׁב יָרָבְעָ֖ם בְּמִצְרָֽיִם׃
```

**Problem:** `וַיְהִ֞י כִשְׁמֹ֣עַ יָרָבְעָ֣ם...` is a wayehi-FEF temporal protasis. The protasis (`כִשְׁמֹ֣עַ יָרָבְעָ֣ם בֶּן־נְבָ֗ט...`) is kept on one line. But the relative clause `אֲשֶׁ֣ר בָּרַ֔ח / מִפְּנֵ֖י הַמֶּ֣לֶךְ שְׁלֹמֹ֑ה` is split from the antecedent `יָרָבְעָ֣ם`. This relative clause is integral to identifying which Jeroboam — it is not a separate atomic thought but a restrictive relative specifying the subject. And the "main clause" `וַיֵּ֥שֶׁב יָרָבְעָ֖ם בְּמִצְרָֽיִם` is a resumptive circumstantial note (he was still in Egypt) — it should follow from the protasis but it is also already embedded in the protasis line (`וְהוּא עוֹדֶ֣נּוּ בְמִצְרַ֔יִם`), which creates a cross-verse redundancy. The real main clause would be in v3. So the wayehi construction here is a long protasis spanning vv. 2-3.

**Classification:** UNDER-MERGE (relative clause fragments split from antecedent)

**Hypothesis:** `אֲשֶׁ֣ר בָּרַ֔ח מִפְּנֵ֖י הַמֶּ֣לֶךְ שְׁלֹמֹ֑ה` is a restrictive relative and should merge with the protasis line (or at minimum stay immediately adjacent without `מִפְּנֵ֖י` orphaned on a separate line).

**Fix:**
```
וַיְהִ֞י כִשְׁמֹ֣עַ יָרָבְעָ֣ם בֶּן־נְבָ֗ט וְהוּא עוֹדֶ֣נּוּ בְמִצְרַ֔יִם אֲשֶׁ֣ר בָּרַ֔ח מִפְּנֵ֖י הַמֶּ֣לֶךְ שְׁלֹמֹ֑ה
וַיֵּ֥שֶׁב יָרָבְעָ֖ם בְּמִצְרָֽיִם׃
```

---

### 15. 2 Kgs 13:23 — HOMOGRAPH-adjacent (tricolon structure)

**Lines (v1):**
```
וַיָּחָן֩ יְהוָ֨ה אֹתָ֤ם וַֽיְרַחֲמֵם֙ וַיִּ֣פֶן אֲלֵיהֶ֔ם
לְמַ֣עַן בְּרִית֔וֹ
אֶת־אַבְרָהָ֖ם יִצְחָ֣ק וְיַֽעֲקֹ֑ב
וְלֹ֤א אָבָה֙ הַשְׁחִיתָ֔ם
וְלֹֽא־הִשְׁלִיכָ֥ם מֵֽעַל־פָּנָ֖יו עַד־עָֽתָּה׃
```

**Problem:** Line 1 contains three wayyiqtol verbs: `וַיָּחָן` (showed grace), `וַֽיְרַחֲמֵם` (had compassion on them), `וַיִּ֣פֶן` (turned to them). These are three distinct divine-attitude verbs. However: are they bonded (M1 / synonymous-intensification trilogy) or three distinct atomic thoughts? The M1 principle says bonded pairs/cognate forms merge; the N=2 principle operates at N=2. At N=3+ structural justification 1 wins regardless of bonding. These three verbs are related but semantically distinct (חָנַן = grace, רָחַם = compassion, פָּנָה = turn attention). They should split.

Additionally: `לְמַ֣עַן בְּרִית֔וֹ` (line 2) is a purpose PP — "on account of his covenant" — this is a structural justification 5 adjunct (purpose PP carrying its own focus). And `אֶת־אַבְרָהָ֖ם יִצְחָ֣ק וְיַֽעֲקֹ֑ב` (line 3) is an object-of-covenant list — structurally this is the nomen rectum / complement of `בְּרִיתוֹ`. Splitting the covenant formula from the patriarchal names is a HOMOGRAPH issue: `בְּרִיתוֹ אֶת...` is a formula ("his covenant with Abraham, Isaac, and Jacob") and the `אֵת`-marker here is the direct-object marker for a covenant-formula construct, not a separate atomic element.

**Classification:** HOMOGRAPH (the `אֵת` in line 3 is ambiguous — is it introducing a new element or is it part of a covenant formula?) plus OVER-MERGE in line 1 (three distinct divine verbs crammed).

**Hypothesis:** The three divine grace-verbs should each earn their own line (N=3+ series, structural justification 1). `לְמַ֣עַן בְּרִיתוֹ אֶת־אַבְרָהָ֖ם יִצְחָ֣ק וְיַֽעֲקֹ֑ב` should be one formula line — the covenant formula stays intact (formula integrity, §1 Layer 3 veto #3).

**Fix:**
```
וַיָּחָן֩ יְהוָ֨ה אֹתָ֤ם
וַֽיְרַחֲמֵם֙
וַיִּ֣פֶן אֲלֵיהֶ֔ם
לְמַ֣עַן בְּרִית֔וֹ אֶת־אַבְרָהָ֖ם יִצְחָ֣ק וְיַֽעֲקֹ֑ב
וְלֹ֤א אָבָה֙ הַשְׁחִיתָ֔ם
וְלֹֽא־הִשְׁלִיכָ֥ם מֵֽעַל־פָּנָ֖יו עַד־עָֽתָּה׃
```

---

## WAVE3-OVERFIRE Summary

**M5 bare-wayehi over-merge:** Zero confirmed instances across 15 fresh chapters. Commit 4c265500 appears effective. The wayehi-FEF protasis pattern is being handled correctly (protasis breaks into the main clause). The failure mode observed in Wave 4 is the *opposite*: wayehi-FEF temporal protases are sometimes being *under-merged* (protasis split across multiple lines rather than held whole). See findings 13 and 14.

**Construct-head over-fire:** Zero false-positive construct-chain merges detected. The concern was whether the generalized h16_c rule was over-firing on legitimate construct chains that end a complete clause. Not evident in this sample.

---

## Pattern Inventory

| Pattern | Count | Findings |
|---|---|---|
| UNDER-MERGE (bare governor / clause fragment) | 7 | 1, 2, 3, 5, 8, 10, 13, 14 |
| OVER-MERGE (multiple events / long line) | 3 | 11, 12, 15 |
| WAVE3-OVERFIRE check — clean | 2 | 6, 13 |
| CASCADE-ORDER (borderline) | 1 | 9 |
| HOMOGRAPH | 1 | 15 |
| CLEAN | 2 | 6, 7 |

**Primary action item:** The wayehi-FEF protasis under-merge pattern (findings 13, 14) warrants a targeted sweep. The protasis of `וַיְהִי + infinitive/temporal` constructions appears to be fragmenting across lines in the parser when it should hold the entire temporal phrase as one line. This is the highest-confidence systemic issue this wave identified.
