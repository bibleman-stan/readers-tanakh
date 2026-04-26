# Te'amim Inventory Reference

Authoritative inventory of the Tiberian cantillation accents (te'amim) for the Tanakh Reader project. Two systems are documented: the **prose system** used in the 21 books, and the **Sifrei Emet (poetic) system** used in Psalms, Proverbs, and Job 3:1–42:6. The remainder of Job (1:1–2:13 and 42:7–17) uses the prose system.

This file is reference, not canon. Editorial guidance and break-decision rules live in `private/01-method/colometry-canon.md` (Rules H8 and H11). Glyphs are given as Unicode code points in the Hebrew accent block (U+0591–U+05AF); where a glyph is contextually positioned (above vs. below the consonant) or where canonical Unicode point assignment is ambiguous, the named character form is used.

The Wickes four-tier scheme (Emperors / Kings / Dukes / Counts) below is **pedagogical, not Masoretic**. The Masoretes did not classify accents into four ranks; the tiers approximate observed disjunctive strength but are heuristic, not taxonomic. Wickes 1887 and Yeivin 1980 disagree on the tier placement of several accents (notably *revia*).

---

## Section 1 — Prose Accent System (21 Books)

| Name (transliteration) | Hebrew name | Glyph | Tier (Wickes) | Function notes |
|---|---|---|---|---|
| silluq | סִלּוּק | ֽ (U+05BD) | 1 (Emperor) | Verse-final disjunctive; identical glyph to meteg, distinguished by sof pasuq (׃) |
| atnach (etnachta) | אֶתְנַחְתָּא | ֑ (U+0591) | 1 (Emperor) | Bisects the verse; primary mid-verse division |
| segolta | סְגוֹלְתָּא | ֒ (U+0592) | 2 (King) | Major disjunctive in the first half of long verses; postpositive |
| zaqef qaton | זָקֵף קָטֹן | ֔ (U+0594) | 2 (King) | Common mid-clause major disjunctive |
| zaqef gadol | זָקֵף גָּדוֹל | ֕ (U+0595) | 2 (King) | Variant of zaqef qaton; used when no preceding conjunctive |
| tifcha | טִפְחָא | ֖ (U+0596) | 2 (King) | *Often a servant of atnach/silluq — see canon Rule H11* |
| revia | רְבִיעַ | ֗ (U+0597) | 3 (Duke) | *Wickes treats as Duke; Yeivin sometimes higher — see canon Rule H8* |
| zarqa | זַרְקָא | ֮ (U+05AE) | 3 (Duke) | Postpositive; precedes segolta in segolta-domain; same glyph/position as Sifrei Emet *tzinnor* |
| pashta | פַּשְׁטָא | ֙ (U+0599) | 3 (Duke) | Postpositive; common precursor to zaqef qaton |
| yetiv | יְתִיב | ֚ (U+059A) | 3 (Duke) | Prepositive; substitute for pashta when on monosyllable / first syllable |
| tevir | תְּבִיר | ֛ (U+059B) | 3 (Duke) | Common precursor to tifcha |
| geresh (azla) | גֶּרֶשׁ | ֜ (U+059C) | 4 (Count) | Lower disjunctive; precedes revia |
| gershayim | גֵּרְשַׁיִם | ֞ (U+059E) | 4 (Count) | Variant of geresh on monosyllabic / oxytone words |
| telisha gedolah | תְּלִישָׁא גְדוֹלָה | ֠ (U+05A0) | 4 (Count) | Prepositive; weakest disjunctive class |
| pazer | פָּזֵר | ֡ (U+05A1) | 4 (Count) | Lower disjunctive; in long pre-revia stretches |
| munach legarmeih | מוּנַח לְגַרְמֵיהּ | ֣ (U+05A3) + ׀ (U+05C0) | 4 (Count) | *Munach + paseq (׀); the paseq is what makes it disjunctive* |
| shalshelet | שַׁלְשֶׁלֶת | ֓ (U+0593) | 4 (Count) | Rare; substitute for segolta when no preceding conjunctive; followed by paseq |

---

## Section 2 — Sifrei Emet Accent System (Psalms, Proverbs, Job 3:1–42:6)

The Sifrei Emet system has fewer accents than the prose system and a different distribution. Several accents share a Unicode code point with their prose counterparts but carry different names and functions in the poetic system.

| Name (transliteration) | Hebrew name | Glyph | Function | Prose-system equivalent |
|---|---|---|---|---|
| silluq | סִלּוּק | ֽ (U+05BD) | Verse-final; same as prose | silluq (same accent) |
| atnach | אֶתְנַחְתָּא | ֑ (U+0591) | Often divides verse into 2 or 3 stichs (not strict bisection) | atnach (same accent, different distribution) |
| oleh ve-yored | עוֹלֶה וְיוֹרֵד | ֫ (U+05AB) above + ֥ (U+05A5) below | Strongest Sifrei-Emet disjunctive after silluq; two-mark accent | (no direct equivalent) |
| revia mugrash | רְבִיעַ מֻגְרָשׁ | ֜ (U+059C) + ֗ (U+0597) | Positional form of revia in Sifrei Emet; "mugrash" = "expelled" (geresh-marked); positional context, not a separate accent | revia (positionally adapted) |
| revia gadol | רְבִיעַ גָּדוֹל | ֗ (U+0597) | Major disjunctive in stichs lacking oleh ve-yored | revia |
| dechi (dehi) | דֶּחִי | ֭ (U+05AD) | Prepositive; mid-stich disjunctive preceding atnach | tifcha (positionally analogous, prepositive in poetic) |
| tzinnor (tsinnor) | צִנּוֹר | ֮ (U+05AE) | Postpositive; **same glyph and positional function as prose zarqa** | zarqa (same accent, different name) |
| pazer | פָּזֵר | ֡ (U+05A1) | Lower disjunctive; same glyph as prose pazer | pazer |
| mehuppakh legarmeih | מְהֻפָּךְ לְגַרְמֵיהּ | ֤ (U+05A4) + ׀ (U+05C0) | *Conjunctive mehuppakh — disjunctive ONLY when followed by paseq (׀)* | (no direct prose equivalent) |
| azla legarmeih | אַזְלָא לְגַרְמֵיהּ | ֝ + ׀ (U+05C0) | *Conjunctive azla — disjunctive ONLY when followed by paseq (׀)* | (no direct prose equivalent) |
| shalshelet gedolah | שַׁלְשֶׁלֶת גְּדוֹלָה | ֓ (U+0593) + ׀ (U+05C0) | Rare lower disjunctive; followed by paseq | shalshelet (related; functions slightly differ) |
| legarmeih (general) | לְגַרְמֵיהּ | (any conjunctive) + ׀ (U+05C0) | "By itself" — naming convention for any conjunctive made disjunctive by paseq | munach legarmeih (prose analog) |

---

## Section 3 — Disambiguation Table

Cross-reference for confusing cases that have caused factual errors in earlier project documents.

| Case | Clarification |
|---|---|
| **zarqa (prose) = tzinnor (Sifrei Emet)** | Same glyph (U+05AE), same postpositive position, same disjunctive function. Different names by accent system only. They are **not two separate accents.** |
| **revia (prose) vs. revia mugrash (Sifrei Emet)** | Positionally related but distinct: revia mugrash carries a preceding geresh (֜) in the Sifrei Emet system; the "mugrash" qualifier names this positional variant. Treat as the Sifrei-Emet positional form of revia, not a wholly separate accent — but do not collapse them: their distributions differ. |
| **mehuppakh-legarmeih and azla-legarmeih are CONJUNCTIVES by base form** | Mehuppakh (֤) and azla (geresh-shaped, ֝) are conjunctives. They function disjunctively *only* when followed by the paseq vertical bar ׀ (U+05C0). The "-legarmeih" suffix ("by itself") signals this paseq-induced disjunctive role. Without the trailing paseq, they remain conjunctive. See Yeivin §§253–290. |
| **paseq (׀) is the disjunctive trigger for any -legarmeih form** | The paseq itself is not strictly an accent but a separator mark. Its presence after a conjunctive (munach, mehuppakh, azla, etc.) elevates that conjunctive to disjunctive force. This pattern is shared across both systems. |
| **shalshelet appears in both systems** | In prose: substitute for segolta when no preceding conjunctive exists, followed by paseq. In Sifrei Emet (shalshelet gedolah): rare lower disjunctive with paseq. Functions are slightly different despite shared glyph and name root. |
| **silluq vs. meteg** | Identical glyph (ֽ U+05BD). Distinguished only by context: silluq immediately precedes sof pasuq (׃ U+05C3); meteg occurs elsewhere as a metrical/secondary-stress mark and is not an accent. |
| **geresh vs. azla** | Same name in some literatures (azla = geresh as a conjunctive in Sifrei Emet contexts; geresh as a disjunctive in prose). Azla in Sifrei Emet is conjunctive-by-base-form (becomes disjunctive only with paseq). |

---

## Section 4 — Scholarly References

- **William Wickes**, *A Treatise on the Accentuation of the Twenty-One So-Called Prose Books of the Old Testament* (Oxford: Clarendon, 1887). Foundational for the prose system; source of the four-tier pedagogical scheme used above.
- **William Wickes**, *A Treatise on the Accentuation of the Three So-Called Poetical Books of the Old Testament: Psalms, Proverbs, and Job* (Oxford: Clarendon, 1881). Foundational for the Sifrei Emet system.
- **Israel Yeivin**, *Introduction to the Tiberian Masorah*, trans. and ed. E. J. Revell (Society of Biblical Literature Masoretic Studies 5; Missoula: Scholars Press, 1980). See especially §§253–290 on conjunctive-with-disjunctive force (the -legarmeih + paseq mechanism).

**Tier-classification disagreement.** Wickes (1887) and Yeivin (1980) disagree on the tier placement of *revia* and on the disjunctive weight of *tifcha* in atnach-domain. Canon Rule H11 names the tifcha-as-servant-of-atnach position explicitly and adopts Wickes's treatment; canon Rule H8 frames the tier classifications generally as evidence-weighting rather than break-licensing thresholds, side-stepping the strongest forms of the Wickes/Yeivin tier dispute.

---

Status: initial scholarly inventory 2026-04-26; corrects predecessor stub canon §3.2 factual errors (tzinnor=zarqa positionally, mehuppakh/azla-legarmeih are conjunctive-with-paseq, revia mugrash is positional revia).
