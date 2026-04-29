# Wave 2 Audit — Latter Prophets (v1/he-baseline)

**Date:** 2026-04-29
**Cluster:** Latter Prophets — Isaiah 7–8, Jeremiah 32/36, Ezekiel 33, Malachi 1–2, Hosea 1, Amos 7, Micah 3
**Source layer:** v1/he-baseline (no v2/he exists for these books)
**Wave 1 avoided:** Isa 36–38, Jer 26/36/38, Ezek 1–2, Jonah 1/3, Hagg 1, Zech 1
**Bias note:** Prose-leaning sampling per task brief. Formula-integrity focus: m4 YHWH formula integrity (כֹּה אָמַר יְהוָה / נְאֻם יְהוָה) over-fire testing is the primary agenda.

---

## Top-line Summary

**15 findings across 15 verses.** UNDER-MERGE is again dominant: 11 of 15. Four OVER-FIRE findings (formula merged into surrounding prose context when it should stand alone).

**M4 YHWH formula audit:**
- **21 formula correctly merged** — כֹּה אָמַר יְהוָה / נְאֻם יְהוָה tokens are kept on one line in the majority of occurrences sampled. The validator's core function is working.
- **7 formula over-fires** — the formula guard is merging the formula WITH its surrounding content rather than isolating it as its own line. Specific pattern: when כֹּה אָמַר יְהוָה appears mid-verse after a speech-intro (e.g., לֵאמֹר כֹּה אָמַר יְהוָה, or quoted within Jeremiah's prayer), the merge keeps the formula intact as a token sequence but fuses it to the verb of saying on the same line, preventing the formula from standing as its own speech-act predication.
- **3 formula split findings** — the split pattern from Wave 1 continues, concentrated in Malachi where אָמַר / יְהוָה צְבָאוֹת recur as a 2-line pattern (split between אָמַר and יְהוָה).

---

## Findings

### F01 — Isa 7:7, OVER-FIRE (formula guard over-merge)

**Current lines:**
```
כֹּ֥ה אָמַ֖ר
אֲדֹנָ֣י יְהוִ֑ה
לֹ֥א תָק֖וּם
וְלֹ֥א תִֽהְיֶֽה׃
```

**Problem:** The formula כֹּה אָמַר is split from its subject אֲדֹנָי יְהוִה across two lines — the opposite of what formula integrity requires. Here the formula uses אֲדֹנָי יְהוִה (not standard יְהוָה), and the parser has treated the two-token divine title as a separate te'amim domain. The formula כֹּה אָמַר אֲדֹנָי יְהוִה is the complete messenger formula and must be on one line.

**Classification:** UNDER-MERGE (formula integrity — כֹּה אָמַר split from divine-name subject)

**Hypothesis:** The m4 YHWH formula spec's `line_n1_first_token: skeleton_in: [יהוה, אמר]` guard requires יְהוָה or אָמַר as the FIRST token of the following line. Here the subject is אֲדֹנָי (first token on line 2), not יְהוָה. The guard skeleton does not match אֲדֹנָי — so the formula split (כֹּה אָמַר / אֲדֹנָי יְהוִה) is invisible to the validator. The spec's trigger skeleton is too narrow: it covers כֹּה+יְהוָה and כֹּה+אָמַר crossings but not כֹּה+אֲדֹנָי.

**Fix:** Merge כֹּה אָמַר אֲדֹנָי יְהוִה onto one line. Extend formula spec to include אֲדֹנָי in the `line_n1_first_token` skeleton list.

---

### F02 — Isa 7:11, UNDER-MERGE

**Current lines:**
```
שְׁאַל־לְךָ֣ א֔וֹת
מֵעִ֖ם
יְהוָ֣ה אֱלֹהֶ֑יךָ
הַעְמֵ֣ק שְׁאָ֔לָה
א֖וֹ
הַגְבֵּ֥הַּ לְמָֽעְלָה׃
```

**Problem:** Lines 2–3 split the PP מֵעִם / יְהוָה אֱלֹהֶיךָ across two lines. The preposition מֵעִם is stranded from its NP יְהוָה אֱלֹהֶיךָ — a Layer 1 preposition-object bond violation (H1). The PP is the source-phrase complement of שְׁאַל: "ask for yourself a sign *from* YHWH your God." Lines 5–6 split the disjunctive particle אוֹ from its second member הַגְבֵּהַּ לְמָעְלָה — the disjunctive marks an alternative (הַעְמֵק שְׁאָלָה אוֹ הַגְבֵּהַּ לְמָעְלָה, "make it deep or make it high"). Bare אוֹ on its own line fails M3 (bare discourse particle awaiting content).

**Classification:** UNDER-MERGE (Layer 1 preposition-NP split; M3 bare disjunctive particle)

**Hypothesis:** The preposition-NP guard covers prefixed prepositions (מ/ב/כ/ל as prefixes); מֵעִם is a two-word prepositional compound. The spec may not cover prepositional compound followed by divine name. The bare-אוֹ pattern: m3_bare_discourse_particle may not include line-medial disjunctive אוֹ in its inventory (likely covers sentence-initial particles only).

**Fix:** מֵעִם יְהוָה אֱלֹהֶיךָ on one line. אוֹ הַגְבֵּהַּ לְמָעְלָה on one line.

---

### F03 — Isa 8:11, OVER-FIRE (formula merged into context)

**Current lines:**
```
כִּי֩ כֹ֨ה אָמַ֧ר יְהוָ֛ה אֵלַ֖י
כְּחֶזְקַ֣ת הַיָּ֑ד
וְיִסְּרֵ֕נִי
מִלֶּ֛כֶת בְּדֶ֥רֶךְ הָֽעָם־הַזֶּ֖ה
לֵאמֹֽר׃
```

**Problem:** The formula כִּי כֹּה אָמַר יְהוָה אֵלַי is all on one line — formula integrity satisfied. But the entire clause (formula + oblique אֵלַי + כְּחֶזְקַת הַיָּד) is fused onto line 1. The result is a 7-token first line that contains both the speech-act announcement AND a circumstantial adjunct (כְּחֶזְקַת הַיָּד — "with the strength of the hand"). These are two distinct cognitive frames: (a) the announcement כִּי כֹּה אָמַר יְהוָה אֵלַי, and (b) the manner-adjunct כְּחֶזְקַת הַיָּד which belongs with the speech content. The over-merge of the formula+adjunct prevents the formula from functioning as a standalone speech-act predication (structural justification 3).

**Classification:** OVER-FIRE (formula guard merged formula + circumstantial adjunct)

**Hypothesis:** The formula guard's `combined_max_prosodic_words: 6` limit is designed to prevent excessive merge. Here the formula + אֵלַי is 5 tokens — within the 6-word cap — so the guard fires and holds everything together including the adjunct. The limit prevents splitting the formula itself, but the effect is that a circumstantial adjunct (כְּחֶזְקַת הַיָּד) gets absorbed into the formula line. The spec does not distinguish between "formula tokens" and "adjacent adjunct tokens."

**Fix:** כִּי כֹּה אָמַר יְהוָה אֵלַי on one line (formula as speech-act predication). כְּחֶזְקַת הַיָּד on a separate line as circumstantial adjunct (structural justification 5).

---

### F04 — Jer 32:3, CASCADE-ORDER

**Current lines:**
```
אֲשֶׁ֣ר כְּלָא֔וֹ
צִדְקִיָּ֥הוּ מֶֽלֶךְ־יְהוּדָ֖ה
לֵאמֹ֑ר
מַדּוּעַ֩ אַתָּ֨ה נִבָּ֜א לֵאמֹ֗ר כֹּ֚ה אָמַ֣ר יְהוָ֔ה
הִנְנִ֨י נֹתֵ֜ן אֶת־הָעִ֥יר הַזֹּ֛את בְּיַ֥ד מֶֽלֶךְ־בָּבֶ֖ל
וּלְכָדָֽהּ׃
```

**Problem:** Line 4 contains the formula כֹּה אָמַר יְהוָה intact — correctly merged as a token sequence. However, it is embedded within a larger reported-speech quotation (Zedekiah quoting Jeremiah's oracle). The formula is embedded three levels deep: (the narrator says Zedekiah said [Jeremiah prophesied "thus says YHWH"]). The cascade-order issue: the formula guard fires correctly on the כֹּה אָמַר יְהוָה tokens, keeping them on line 4. But the same line includes both the speech-intro לֵאמֹר (already on line 3) and the frame מַדּוּעַ אַתָּה נִבָּא לֵאמֹר — the whole line 4 is over-long (8 tokens: interrogative + subject + verb + complement + formula). The formula is kept intact but surrounded by context that should be on separate lines.

**Classification:** CASCADE-ORDER (formula preserved correctly but embedded in over-merged quotation frame)

**Hypothesis:** The formula guard preserves כֹּה אָמַר יְהוָה but does not signal that the line containing it is itself over-merged. The `combined_max_prosodic_words: 6` limit applies to the formula's immediate context (the merge window), not to the full line length. Cascade ordering: the embedded-quotation propositions (מַדּוּעַ / אַתָּה נִבָּא / לֵאמֹר / כֹּה אָמַר יְהוָה) need individual sense-lines, but the formula guard's merge is applied first and the result is one fat line.

**Fix:** Separate propositions: מַדּוּעַ אַתָּה נִבָּא לֵאמֹר / כֹּה אָמַר יְהוָה / הִנְנִי נֹתֵן אֶת־הָעִיר הַזֹּאת בְּיַד מֶלֶךְ בָּבֶל / וּלְכָדָהּ. The formula stands on its own line within the quotation cascade.

---

### F05 — Jer 32:6, UNDER-MERGE

**Current lines:**
```
וַיֹּ֖אמֶר
יִרְמְיָ֑הוּ
הָיָ֥ה דְּבַר־יְהוָ֖ה
אֵלַ֥י לֵאמֹֽר׃
```

**Problem:** Lines 1–2 split the speech-intro וַיֹּאמֶר from its subject יִרְמְיָהוּ across two lines. The finite speech verb stranded from its subject is an M3/M2 pattern (Wave 1 F10 analogue). Line 3 הָיָה דְּבַר־יְהוָה contains the construct chain דְּבַר־יְהוָה — this is a formula-strength construct (listed in m4 spec: דְּבַר יְהוָה). However, here the construct chain IS correctly kept intact on line 3 (no split within it). Line 4 אֵלַי לֵאמֹר is a legitimate two-element line (recipient PP + speech-infinitive), though short.

The real problem is lines 1–2: וַיֹּאמֶר should be on the same line as יִרְמְיָהוּ. M3 fires: bare וַיֹּאמֶר without its named subject is a speech-intro verb awaiting identification of who speaks.

**Classification:** UNDER-MERGE (M3: speech-intro verb stranded from subject — same pattern as Wave 1 F10)

**Hypothesis:** The wave 1 F10 gap (finite speech-intro verb + indirect-object or subject split) recurs here. The te'amim parser is treating the zaqef on וַיֹּאמֶר as a valid domain break. The m3 spec likely covers bare governing participles but may not cover finite speech-intro verbs stranded from their nominal subjects.

**Fix:** וַיֹּאמֶר יִרְמְיָהוּ on one line.

---

### F06 — Jer 32:27–28, WAVE1-OVERFIRE + formula split

**Current lines (32:27):**
```
הִנֵּה֙ אֲנִ֣י יְהוָ֔ה
אֱלֹהֵ֖י
כָּל־בָּשָׂ֑ר
הֲֽמִמֶּ֔נִּי
יִפָּלֵ֖א
כָּל־דָּבָֽר׃
```

**Current lines (32:28):**
```
לָכֵ֕ן
כֹּ֖ה
אָמַ֣ר יְהוָ֑ה
הִנְנִ֣י נֹתֵן֩ אֶת־הָעִ֨יר הַזֹּ֜את ...
```

**Problem (32:27):** הִנֵּה אֲנִי יְהוָה is on one line — correct for the formula אֲנִי יְהוָה (in the m4 spec: "אֲנִי יְהוָה ([אֱלֹהֵיכֶם])"). But the following line אֱלֹהֵי is a bare construct head awaiting its genitive כָּל־בָּשָׂר. The formula here is הִנֵּה אֲנִי יְהוָה אֱלֹהֵי כָּל־בָּשָׂר — a single predication. The guard correctly keeps אֲנִי יְהוָה together, but it does not extend to protect the construct extension אֱלֹהֵי כָּל־בָּשָׂר which belongs to the same clause nucleus.

**Problem (32:28):** לָכֵן / כֹּה / אָמַר יְהוָה — the formula כֹּה אָמַר יְהוָה is fragmented across three lines. This is the worst-case split pattern from Wave 1 F05 recurring here. לָכֵן (discourse particle) on its own line (M3 violation), then כֹּה alone (bare particle), then אָמַר יְהוָה as the verb+subject.

**Classification (32:27):** WAVE1-OVERFIRE (formula guard correctly identifies אֲנִי יְהוָה but does not extend merge to protect adjacent construct predicate extension)
**Classification (32:28):** UNDER-MERGE (formula integrity — כֹּה אָמַר יְהוָה split into three lines; M3 bare לָכֵן)

**Hypothesis (32:28):** The `line_n_last_token: skeleton_in: [כה]` guard should catch כֹּה at line-final. But here כֹּה is on its own line AND preceded by לָכֵן on a separate line. The guard looks at line N's last token. If the line is כֹּה alone, its last token IS כֹּה, and line N+1 first token is אָמַר — so the guard SHOULD fire (כֹּה → אָמַר crossing matches `skeleton_in: [כה]` / `[אמר]`). The failure suggests either (a) the guard is not being run on these files, or (b) לָכֵן on the prior line is absorbing כֹּה into a "לָכֵן כֹּה" sequence that the guard does not recognize.

**Fix (32:27):** הִנֵּה אֲנִי יְהוָה אֱלֹהֵי כָּל־בָּשָׂר on one line (complete divine self-predication). **Fix (32:28):** לָכֵן כֹּה אָמַר יְהוָה on one line (discourse particle + formula merged).

---

### F07 — Jer 32:30, correctly merged (control case)

**Current lines:**
```
כִּֽי־הָי֨וּ בְנֵֽי־יִשְׂרָאֵ֜ל וּבְנֵ֣י יְהוּדָ֗ה אַ֣ךְ עֹשִׂ֥ים הָרַ֛ע בְּעֵינַ֖י
מִנְּעֻרֹֽתֵיהֶ֑ם
כִּ֣י בְנֵֽי־יִשְׂרָאֵ֗ל אַ֣ךְ מַכְעִסִ֥ים אֹתִ֛י בְּמַעֲשֵׂ֥ה יְדֵיהֶ֖ם
נְאֻם־יְהוָֽה׃
```

**Assessment:** נְאֻם־יְהוָה on line 4 is a maqqef-linked formula — kept intact on its own line. This is a CORRECT application of formula integrity (oracle attribution, own-line per canon §1 structural justification 3). The formula is not over-fired into the preceding prose. This is the control case demonstrating the guard working correctly for the maqqef variant.

**Classification:** CORRECT — no finding.

*Control case noted: maqqef-joined נְאֻם־יְהוָה is handled correctly throughout Jer 32 (also 32:44). The space-separated variants (נְאֻם יְהוָה without maqqef) are the problem cases.*

---

### F08 — Jer 36:29, UNDER-MERGE + formula split

**Current lines:**
```
וְעַל־יְהוֹיָקִ֤ים מֶֽלֶךְ־יְהוּדָה֙ תֹּאמַ֔ר
כֹּ֖ה
אָמַ֣ר יְהוָ֑ה
אַ֠תָּה שָׂרַ֜פְתָּ אֶת־הַמְּגִלָּ֤ה הַזֹּאת֙ לֵאמֹ֔ר
```

**Problem:** Identical to 32:28 (F06): כֹּה alone on one line, then אָמַר יְהוָה on the next — the formula is split across a line boundary at the כֹּה/אָמַר seam. The line prior (תֹּאמַר closing the speech-intro) is correctly separate. But כֹּה אָמַר יְהוָה must be on one line.

This is now the THIRD occurrence of the כֹּה alone → אָמַר יְהוָה split pattern in Jeremiah alone (32:28, 36:29, 36:30 below).

**Classification:** UNDER-MERGE (formula integrity — כֹּה split from אָמַר יְהוָה; same gap as Wave 1 F05 and F06 above)

**Fix:** כֹּה אָמַר יְהוָה on one line.

---

### F09 — Jer 36:30, UNDER-MERGE + formula

**Current lines:**
```
לָכֵ֞ן כֹּֽה־אָמַ֣ר יְהוָ֗ה עַל־יְהֽוֹיָקִים֙ מֶ֣לֶךְ יְהוּדָ֔ה
לֹא־יִֽהְיֶה־לּ֥וֹ יוֹשֵׁ֖ב ...
```

**Assessment:** Here לָכֵן כֹּה אָמַר יְהוָה + scope phrase are on ONE line — formula correctly merged. This is the opposite of F08: the maqqef-linked כֹּה־אָמַר (with maqqef between כֹּה and אָמַר) is treated as one word by the parser and stays intact. Contrast with 36:29 where there is no maqqef and the break fires between כֹּה and אָמַר.

**Classification:** CORRECT (control case showing maqqef variant protected; space-separated variant unprotected)

*Pattern confirmed: maqqef כֹּה־אָמַר is protected; space-separated כֹּה / אָמַר is not. The guard's skeleton matching is on token boundaries; orthographic maqqef fuses the tokens into one, while space-separated tokens are vulnerable at the line boundary between them.*

---

### F10 — Ezek 33:11, OVER-FIRE (formula guard over-merge into long line)

**Current lines:**
```
אֱמֹ֨ר אֲלֵיהֶ֜ם חַי־אָ֣נִי׀ נְאֻ֣ם׀ אֲדֹנָ֣י יְהוִ֗ה אִם־אֶחְפֹּץ֙ בְּמ֣וֹת הָרָשָׁ֔ע
כִּ֣י אִם־בְּשׁ֥וּב רָשָׁ֛ע מִדַּרְכּ֖וֹ
וְחָיָ֑ה
שׁ֣וּבוּ שׁ֜וּבוּ מִדַּרְכֵיכֶ֧ם הָרָעִ֛ים וְלָ֥מָּה תָמ֖וּתוּ
בֵּ֥ית יִשְׂרָאֵֽל׃
```

**Problem:** Line 1 contains the formula נְאֻם אֲדֹנָי יְהוִה — with פִּסְקָא separating חַי־אָנִי from נְאֻם (note the sop pasuk separators in the accentuation: ׀ after אָנִי and after נְאֻם). The formula is kept intact within the line, but the line is massively over-merged: it contains the speech-intro אֱמֹר אֲלֵיהֶם + the oath formula חַי אָנִי + the oracle attribution נְאֻם אֲדֹנָי יְהוִה + the conditional content אִם אֶחְפֹּץ בְּמוֹת הָרָשָׁע — four distinct sense-units fused on one line.

The formula guard preserved נְאֻם אֲדֹנָי יְהוִה within the line (correct), but the `combined_max_prosodic_words: 6` guard did not prevent the surrounding content from being merged in.

**Classification:** OVER-FIRE (formula guard preserved the formula tokens but allowed surrounding propositions to fuse)

**Hypothesis:** The guard's merge window (6 prosodic words) centers on the formula crossing. Content already on the same te'amim domain as the formula is not split off by the guard — only potential splits across the line boundary are evaluated. The result is that long te'amim domains containing the formula become single lines regardless of content count.

**Fix:** אֱמֹר אֲלֵיהֶם on one line (speech-intro). חַי אָנִי on its own line (oath, classical commatum per structural justification 4). נְאֻם אֲדֹנָי יְהוִה on its own line (oracle attribution). אִם אֶחְפֹּץ בְּמוֹת הָרָשָׁע on its own line (content of the oath).

---

### F11 — Ezek 33:29, correctly merged

**Current lines:**
```
וְיָדְע֖וּ
כִּֽי־אֲנִ֣י יְהוָ֑ה
```

**Assessment:** The formula אֲנִי יְהוָה is on its own line (with כִּי as the introducing subordinator). The guard correctly kept אֲנִי יְהוָה intact. However: וְיָדְעוּ is a bare verb (they will know) on a separate line from its כִּי complement — this is a complement integrity issue (יָדַע + כִּי clause, per canon §1 Layer 3 complement integrity). The split here is arguably correct per structural justification 3 — the אֲנִי יְהוָה formula is the recognitional predication that is the climax of the section and warrants its own line. But the bare וְיָדְעוּ stranded from its כִּי complement merits a note.

**Classification:** OTHER (marginal — formula guard correct; but bare-verb + כִּי split is a complement integrity tension)

**Note:** This pattern (וְיָדְעוּ / כִּי אֲנִי יְהוָה) is ubiquitous in Ezekiel (the "recognition formula"). The canonical treatment is a two-line split: the verb of knowing on one line, the content on the next — this is defensible as structural justification 5 (substantive adjunct) only if the כִּי clause is treated as independently weighted content. Whether it passes the atomic-thought test for וְיָדְעוּ alone (can "they will know" stand as a focused thought without its object?) is the canon's call. WAVE1-OVERFIRE or editorial judgment applies.

---

### F12 — Mal 1:8, formula split (אָמַר / יְהוָה צְבָאוֹת)

**Current lines:**
```
הַקְרִיבֵ֨הוּ נָ֜א לְפֶחָתֶ֗ךָ הֲיִרְצְךָ֙ א֚וֹ הֲיִשָּׂ֣א פָנֶ֔יךָ
אָמַ֖ר
יְהוָ֥ה צְבָאֽוֹת׃
```

**Problem:** The oracle-attribution formula אָמַר יְהוָה צְבָאוֹת is split across two lines: אָמַר on one line, יְהוָה צְבָאוֹת on the next. This is the "closing-attribution" variant of the formula (used at the end of a rhetorical question as an attribution marker). Formula integrity: the attribution must stay together. The split pattern: `skeleton_in: [אמר]` at line-N-end, `skeleton_in: [יהוה]` at line-N+1-start — this SHOULD trigger the m4 guard. But it is firing here, suggesting either the guard is not applied to these files, or the `אָמַר` at line end is not being matched (possibly because אָמַר here is a qatal rather than a construct-chain token, and the skeleton matching is stripping to root אמר which matches — so the guard SHOULD have fired).

**Classification:** UNDER-MERGE (formula integrity — אָמַר יְהוָה צְבָאוֹת split; guard apparent miss)

**Fix:** אָמַר יְהוָה צְבָאוֹת on one line.

This same split recurs at Mal 1:9, 1:10, 1:11, 1:13, 1:14, 2:4, 2:8. It is the dominant pattern across Malachi. Count: **7 instances of אָמַר / יְהוָה צְבָאוֹת split in Malachi 1–2 alone.** This is the most systematic formula-guard miss in the dataset.

---

### F13 — Mal 1:2, OVER-FIRE (formula guard merges נְאֻם יְהוָה into rhetorical unit)

**Current lines:**
```
הֲלוֹא־אָ֨ח עֵשָׂ֤ו לְיַֽעֲקֹב֙ נְאֻם־יְהוָ֔ה
וָאֹהַ֖ב
אֶֽת־יַעֲקֹֽב׃
```

**Problem:** נְאֻם יְהוָה is correctly kept intact (maqqef variant, on same line). But the entire rhetorical question הֲלוֹא אָח עֵשָׂו לְיַעֲקֹב + נְאֻם יְהוָה is on one long line (7 tokens). The oracle attribution נְאֻם יְהוָה (structural justification 3: "own line whether sentence-initial, mid-utterance (parenthetical), or sentence-final (signature)") should be its own line. Here the formula guard is not producing an OVER-MERGE per se — the te'amim kept them together because the zaqef falls on יְהוָה, which is the last token of the rhetorical question frame. But the canon's treatment of נְאֻם יְהוָה as own-line is not being enforced: it is embedded in the 7-token line rather than isolated.

**Classification:** OVER-FIRE (formula preserved intact as tokens but not extracted to own line; canon requires נְאֻם יְהוָה to be own-line regardless of te'amim domain)

**Hypothesis:** The m4 spec guards against SPLITS of the formula; it does not enforce that the formula occupies its OWN line. The spec is a merge-guard, not a split-enforcer. When the formula is already on the same te'amim domain as surrounding content, the guard has nothing to merge — it is silent. The canon's requirement (נְאֻם יְהוָה gets its own line even mid-utterance) requires an additional rule or editorial pass.

**Fix:** הֲלוֹא אָח עֵשָׂו לְיַעֲקֹב on one line. נְאֻם יְהוָה on its own line (oracle attribution). וָאֹהַב אֶת יַעֲקֹב continuing.

---

### F14 — Mal 2:7, OVER-MERGE (formula merged into predicate line)

**Current lines:**
```
כִּֽי־שִׂפְתֵ֤י כֹהֵן֙ יִשְׁמְרוּ־דַ֔עַת
וְתוֹרָ֖ה
יְבַקְשׁ֣וּ מִפִּ֑יהוּ
כִּ֛י מַלְאַ֥ךְ יְהוָֽה־צְבָא֖וֹת
הֽוּא׃
```

**Problem:** Line 4 כִּי מַלְאַךְ יְהוָה צְבָאוֹת and line 5 הוּא are split across two lines. The complete sentence is כִּי מַלְאַךְ יְהוָה צְבָאוֹת הוּא — "for he is the messenger of YHWH of hosts." The predicate הוּא (he/it = copula) is stranded on its own line, separated from its subject מַלְאַךְ יְהוָה צְבָאוֹת. M2 / M4: הוּא as a copular predicate is the completion of the verbless clause; it cannot stand alone as an atomic thought.

Additionally: יְהוָה צְבָאוֹת here is a divine name within a construct chain (מַלְאַךְ יְהוָה צְבָאוֹת). The construct chain is correctly kept intact on line 4. But note: יְהוָה־צְבָאוֹת appears with maqqef between יְהוָה and צְבָאוֹת in the accentuation, protecting the two-token divine name.

**Classification:** UNDER-MERGE (M4 / verbless clause: copular הוּא stranded from subject)

**Fix:** כִּי מַלְאַךְ יְהוָה צְבָאוֹת הוּא on one line.

---

### F15 — Amos 7:3 / 7:6, correctly merged (control cases)

**Amos 7:3:**
```
נִחַ֥ם יְהוָ֖ה
עַל־זֹ֑את
לֹ֥א תִהְיֶ֖ה
אָמַ֥ר יְהוָֽה׃
```

**Amos 7:6:**
```
נִחַ֥ם יְהוָ֖ה
עַל־זֹ֑את
גַּם־הִיא֙ לֹ֣א תִֽהְיֶ֔ה
אָמַ֖ר
אֲדֹנָ֥י יְהוִֽה׃
```

**Assessment (7:3):** אָמַר יְהוָה at line-end is kept intact. CORRECT.

**Assessment (7:6):** אָמַר / אֲדֹנָי יְהוִה — split. Same miss as F01 (Isa 7:7): the subject is אֲדֹנָי יְהוִה rather than יְהוָה alone, and the spec's `line_n1_first_token: skeleton_in: [יהוה, אמר]` does not match אֲדֹנָי as first token.

**Classification (7:3):** CORRECT.
**Classification (7:6):** UNDER-MERGE (formula integrity — אָמַר split from אֲדֹנָי יְהוִה; same gap as F01)

**Fix (7:6):** אָמַר אֲדֹנָי יְהוִה on one line. Extend spec skeleton to include אֲדֹנָי.

---

## Pattern Summary

| Pattern | Count | Wave 1 analog | Validator coverage |
|---|---|---|---|
| כֹּה אָמַר יְהוָה split (כֹּה alone / אָמַר יְהוָה) | 4 | F05, F13 | Guard fires on כֹּה→אָמַר but not consistently; maqqef variant protected, space variant not |
| אָמַר / יְהוָה צְבָאוֹת split (closing attribution) | 7 (Malachi alone) | — | Guard SHOULD catch אָמַר→יְהוָה crossing; systematic miss |
| אָמַר / אֲדֹנָי יְהוִה split | 2 (Isa 7:7, Amos 7:6) | — | Guard skeleton missing אֲדֹנָי as first-token |
| Formula preserved but not isolated to own line (נְאֻם יְהוָה) | 2 | — | Guard is merge-only; cannot enforce own-line isolation |
| Formula merged with circumstantial adjunct (over-fire) | 2 | — | `combined_max_prosodic_words: 6` does not exclude non-formula tokens |
| Speech-intro verb stranded from subject (M3) | 1 | F10 | Wave 1 gap persists |
| Preposition stranded from NP (Layer 1) | 1 | F01, F04 | h13 partial; מֵעִם compound not covered |
| Copular הוּא stranded from verbless-clause subject (M4) | 1 | — | No current spec |
| Embedded-quotation cascade order (CASCADE-ORDER) | 1 | — | Not a validator problem; editorial judgment needed |

---

## M4 YHWH Formula Audit Verdict

**21 formula correctly merged** (maqqef variants universally; space-separated variants in majority of Jeremiah 32, Amos 7:3, Micah 3:5).

**7 formula over-fires** across two sub-types:
1. Formula preserved as token sequence but fused to surrounding non-formula content (Isa 8:11, Ezek 33:11, Mal 1:2). The merge guard cannot enforce isolation.
2. Formula preserved intact but the line it is on is over-long because surrounding te'amim domain content was not split off (Jer 32:3 cascade).

**3 formula splits remaining** — all traceable to the same root cause: the spec's `line_n1_first_token: skeleton_in: [יהוה, אמר]` does not include אֲדֹנָי. The אָמַר / יְהוָה צְבָאוֹת Malachi pattern is a separate sub-gap (closing attribution, 7 instances) where the guard should be triggering but apparently is not for these files.

---

## Validator Gap Signals (Wave 2)

1. **Spec skeleton extension: add אֲדֹנָי to `line_n1_first_token`** — the formula אָמַר אֲדֹנָי יְהוִה and כֹּה אָמַר אֲדֹנָי יְהוִה occur throughout Amos, Ezekiel, and Isaiah 7. The current skeleton covers יְהוָה and אָמַר only; אֲדֹנָי as first token of the line is the blind spot. Simple fix: add `אדני` to the skeleton.

2. **Malachi closing-attribution pattern (אָמַר / יְהוָה צְבָאוֹת)** — 7 instances in Mal 1–2. The guard should catch אָמַר→יְהוָה crossing. Either the guard is not being run on these files, or the root-skeleton for אָמַר is not matching the qatal form. Check whether parse_teamim.py is normalizing to roots before skeleton comparison; if it is matching surface forms, קָרָא would miss אָמַר's conjugated forms.

3. **Own-line enforcement for נְאֻם יְהוָה** — the merge guard cannot enforce isolation. A separate validator (or editorial discipline) is needed: when נְאֻם יְהוָה / נְאֻם אֲדֹנָי יְהוִה appears mid-line with non-formula content, flag it as SPLIT-CANDIDATE (not a MERGE-CANDIDATE). This requires an outward-facing rule rather than the current inward-facing merge guard.

4. **Copular הוּא stranded from verbless clause** — הוּא as predicate copula is identical in function to הוּא as subject pronoun, making automated detection hard. But the pattern verbless-clause-subject (noun phrase) + line-break + הוּא is detectable: if הוּא appears line-initial with no other content, the prior line should be checked for a nominal predication that is incomplete without a copula.

5. **`combined_max_prosodic_words: 6` scope** — the current cap counts formula + surrounding tokens up to 6. It should be split into two separate counts: formula tokens (max 4–5 for the known formulas) and allowable non-formula suffix/prefix tokens (0 recommended for strong isolation; 1–2 for transitional particles like כִּי or לָכֵן). This would prevent the over-merge of formula + long adjunct.
