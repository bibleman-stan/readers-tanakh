# Coordinate-series over-breaking diagnostic — reply

## Methodology

Built a one-off detection script (not committed; ran from `C:/tmp/`). Definition: detect N≥2 consecutive content lines where each line begins with a vav-conjunctive (וְ / וַ / וּ / וָ) and (optionally) include the prior non-vav-prefixed head line as the series anchor. Token threshold for SHORT-MEMBER: ≤4 prosodic words per member.

100-case stratified sample drawn (25 per structural type: NP-series / PP-series / bare-verb-series / mixed). Sonnet dispatched per `feedback_model_selection_frugality` (structured per-instance judgment within defined rubric). Single pass, ~6.5 min wall-time.

## Survey output (Item 1)

**Corpus-wide coordinate-series detection** (v2/heb, post-Stan-revisions):

- Total series detected: **14,607**
- Short-member series (all members ≤4 toks): **6,191** (42.4% of all series)
- Long-member series (≥1 member >4 toks): 8,416

**Top books by series count** (short-member subset in parentheses):

| Book | Total series | Short-member |
|---|---|---|
| Genesis | 1,125 | 463 |
| Jeremiah | 946 | 323 |
| Ezekiel | 861 | 278 |
| Isaiah | 858 | 411 |
| Exodus | 813 | 302 |
| 1 Samuel | 731 | 285 |
| Numbers | 712 | 289 |
| 2 Chronicles | 676 | 216 |
| **Psalms** | **663** | **562** (84.8% short-member ratio) |
| 1 Kings | 641 | 209 |
| Deuteronomy | 624 | 241 |

**Psalms anomaly**: 84.8% short-member ratio confirms the poetic-compression pattern. Sifrei Emet density of compressed parallel bicola/tricola drives the high short-member ratio.

## Structural-type classification (Item 2)

Per first-member token-shape heuristic (mechanical; verified by Sonnet sample):

| Type | Count |
|---|---|
| mixed | 3,392 |
| NP-series | 1,323 |
| bare-verb-series | 1,111 |
| PP-series | 365 |
| **TOTAL short-member** | **6,191** |

The `mixed` category dominates because my classifier sees DIFFERENT first-token types across the prior-head member (non-vav-prefixed) and the vav-prefixed continuations. This is mechanical noise; the Sonnet sample re-classifies each case based on actual structural function.

## 100-case classification (Item 3)

Sonnet verdicts per structural type:

| Type | CORRECT | OVER-BROKEN | AMBIGUOUS |
|---|---|---|---|
| NP-series (25) | 3 | 19 | 3 |
| PP-series (25) | 0 | 23 | 2 |
| bare-verb-series (25) | 6 | 12 | 7 |
| mixed (25) | 0 | 15 | 10 |
| **OVERALL** | **9** | **69** | **21** |

**Headline finding**: **69% of short-member coordinate-series are over-broken corpus-wide.**

If the 100-case sample's rate extrapolates to the 6,191 corpus short-member series: ~4,272 over-broken instances + ~1,300 ambiguous + ~557 correct.

The directive's vault-Claude hypothesis ("J1 firing on coordinator וְ without length/content-density check") is confirmed strongly. The 60-75% over-breaking rate observed in the three vault-side experiments (Deut 6, Gen 22, Ps 1) is consistent with this corpus-wide 100-case sample.

## Pattern analysis (Item 4)

### Over-broken rates per structural type

- **PP-series**: 92% over-broken (23/25) — highest rate. Coordinate PP members filling one syntactic slot (purpose-infinitive pairs, parallel place-clauses, paired temporal-frames, prepositional merism pairs) are almost never CORRECT.
- **mixed**: 60% over-broken (15/25) + 40% ambiguous. The mixed-type's variability creates ambiguity but with a strong over-break tilt.
- **NP-series**: 76% over-broken (19/25). Pure NP coordinate extensions are routinely over-broken.
- **bare-verb-series**: 48% over-broken (12/25) — lowest rate. Wayyiqtol narrative chains with distinct propositional advance produce genuine sequential ATUs more often than other types.

### Sub-pattern surfacing (from Sonnet's analysis)

1. **Speech-formula pairs** (*answered/said*, *took up oracle/said*, *X-said/to-Y*): universally over-broken when split (Cases 60, 64, 73, 74, 75, 77). The "answered and said" pattern is a single speech-introduction token; splitting is the most mechanical FP in the dataset.

2. **Itinerary formula** (*departed from / camped at*): one ATU per stage of wilderness march. Case 71 (Num 33:17) over-broken.

3. **Merism pairs** (*many/few*, *morning/night*, *from-here/from-there*, *iron/clay*, *strong-hand* × 2): universally over-broken (Cases 14, 44, 47, 80, 85, 94). Both members are required jointly to state the full range.

4. **Pure NP/PP extensions** (*and his wife*, *and my daughters*, *and the half-tribe*, *and the heavens of heavens*, *and many words*): universally over-broken (Cases 8, 15, 17, 20, 25, 28, 29, 89). The extension fills the same syntactic slot as the head.

5. **Synonymous verb-pairs describing one act** (*harm/destroy*, *blossom/flower*, *thwart/no-success*): routinely over-broken (Cases 3, 9, 13, 26, 46).

6. **Antithetic wisdom proverbs** (*youth/age*, *righteous/wicked*, *plans-of-man/plan-of-God*): universally over-broken (Cases 5, 12, 23, 45, 81). The contrast IS the proverb; neither limb stands alone.

7. **Purpose/result clause pairs** (*came/to-speak*, *rose/said*, *go/gather*): routinely over-broken (Cases 55, 62, 64, 66, 86, 87). When L2 is the purpose or result of L1 with the same subject, one ATU.

8. **Genealogical chain entries** (*X begat Y / Y begat Z*): CORRECT (Cases 7, 22). Each link is a distinct individual.

9. **Stock verb pairs** (*eat/be-satisfied*, *bow/worship*, *hear/do*): consistently over-broken when each verb gets its own line and both share the same subject.

### Book / genre patterns

- **Wisdom literature** (Psalms, Proverbs, Job, Ecclesiastes): concentrates over-broken cases in synonymous + antithetic parallelism. The two-part wisdom-verse is almost never correctly split.
- **Prose narrative** (Samuel/Kings/Chronicles/Joshua/Judges): produces the bulk of AMBIGUOUS and CORRECT cases, specifically wayyiqtol chains with genuine propositional advance.
- **Legal/priestly texts** (Numbers, Deuteronomy, Exodus): over-broken almost universally in PP-series.
- **Genealogical register** (Ruth, Chronicles, Gen 5/10/11/36): the one sub-genre where NP-series breaks are routinely CORRECT.
- **Prophetic poetry** (Isaiah, Jeremiah, Micah, Amos, Zechariah): concentrated over-broken cases in synonymous parallelism (bicolon split at colon boundary).

### Token-count distribution

The directive proposed threshold-N=4 as the SHORT-MEMBER discriminator. The sample's over-broken rate is consistent across the 1-4 token range — the threshold captures the diagnostic surface but doesn't sub-discriminate within it. Long-member series (>4 toks/member) were excluded from sample; 100-case sample doesn't speak to their over-broken rate.

## Deut 6 trigger-case verdicts (Item 6)

Per directive Item 6, the Deut 6 trigger cases referenced in vault-Claude's surfacing are v.2 (3-NP), v.5 (Shema tricolon), v.7 (4-PP), v.11 (verb-pair).

**Important note**: these cases were re-rendered in commit `6933d793f` (Stan's 9-verse Deut 6 re-rendering, 2026-05-16 22:03). The current v2/heb of Deut 6:2, 6:5, 6:7, 6:11 NO LONGER over-breaks — those merges have been applied. My survey scanned the POST-revision state, so the trigger cases don't appear in the survey output. **They were the seed; the merges are already landed.**

From the 100-case sample's structural classifier applied to the PRE-revision shapes (as described in vault-Claude's directive):

- **6:2** (3 bare-NP addressees *אַתָּה / וּבִנְךָ / וּבֶן־בִּנְךָ*): NP-series, 1-token-per-member → would classify as OVER-BROKEN (each addressee fills one syntactic-subject slot per the appositional expansion pattern; matches Cases 8, 15, 17, 20, 28, 29, 89 of the sample).
- **6:5** (Shema heart/soul/might tricolon): PP-series, ~2-token-per-member → OVER-BROKEN (parallel bi-prefixed PP members filling one with-all-of-X slot; matches Cases 26, 34, 42, 43, 47, 50, 80 of the sample).
- **6:7** (4 infinitival temporal PPs *בְּשִׁבְתְּךָ / וּבְלֶכְתְּךָ / וּבְשָׁכְבְּךָ / וּבְקוּמֶךָ*): PP-series, 1-token-per-member → OVER-BROKEN (four-fold temporal-merism in one when-X-and-Y-and-Z slot; matches the merism-pair pattern at sample-broadened scale).
- **6:11** (*וְאָכַלְתָּ / וְשָׂבָֽעְתָּ*): bare-verb-series, 1-token-per-member → OVER-BROKEN (stock verb-pair eat/be-satisfied describing one act; matches Cases 13, 55, 62, 73, 74, 75 of the sample).

All four trigger cases fit the over-broken pattern of the 100-case sample. Their re-merger in `6933d793f` is methodology-consistent with the corpus-wide finding.

## Intervention options (Item 5)

Per directive Item 5: surface options + data each draws on, **no ranking, no recommendation**.

### Option A — M-override codification (new merge-override rule)

Add a Layer-3 merge-override to canon §1 M1–M4 family. Signature: "if all coordinate members are below threshold-N tokens AND share verb/predicate/syntactic-slot, merge as single ATU." 

**Data points draws on**:
- ~6,191 short-member series corpus-wide, ~69% over-broken
- 9 sub-patterns identified (formula pairs / merism / extensions / synonymous verb-pairs / antithetic wisdom / purpose-result / stock verb-pairs / genealogical exclusion / itinerary)
- Exception classes documented (wayyiqtol narrative chains with distinct propositional content; genealogical chain entries)

**Audit-trigger cost**: §7.3 trigger #1 (new merge-override rule). Requires ≥2 parallel adversarial agents BEFORE infrastructure per CLAUDE.md.

### Option B — Per-pattern targeted closed lists

Multiple narrower closed lists (one per sub-pattern): `STOCK_VERB_PAIRS` (eat/be-satisfied, bow/worship, hear/do, etc.), `ITINERARY_PAIRS` (depart/camp), `SPEECH_FORMULA_PAIRS` (answered/said, took-up-oracle/said). Each fires a specific validator.

**Data points**: 9 sub-patterns enumerated; each is bounded and enumerable.

**Audit-trigger cost**: §7.3 trigger #1 + #2 per new closed list. Multiple audits required.

### Option C — Bare editorial-rule annotation in canon

Add an editorial-rule note to canon §5 documenting the coordinate-series-over-breaking pattern. No validator change. Surfaces the pattern for human editorial reference only.

**Data points**: 100-case sample's pattern catalog; sub-pattern enumeration.

**Audit-trigger cost**: §7.4 audit-skippable (editorial documentation only).

### Option D — Per-corpus override JSON for specific over-broken instances

Generate a JSON file listing the ~4,272 over-broken corpus instances (extrapolated from sample) for surgical hand-apply. Analogous to BoFM 2400 Option A pattern.

**Data points**: 6,191 corpus short-member series + classification rate from sample.

**Audit-trigger cost**: §7.4 audit-skippable (per-case data layer; corpus-mutation is hand-apply per-instance).

### Option E — Defer pending further investigation

Hold the diagnostic; surface 2402 audit-layer prototype (parallel directive) as the broader investigation surface.

**Data points**: 2402 directive's broader scope subsumes this diagnostic.

**Audit-trigger cost**: zero (no action).

## Per-item disposition

| Item | Status |
|---|---|
| 1 — Corpus-wide survey | Done (14,607 total / 6,191 short-member) |
| 2 — Structural-type classification | Done (4-type breakdown) |
| 3 — 100-case Sonnet classification | Done (9 correct / 69 over-broken / 21 ambiguous) |
| 4 — Pattern analysis | Done (rates per type + 9 sub-patterns + book/genre patterns + token-count) |
| 5 — Intervention options | Done — A/B/C/D/E surfaced WITHOUT recommendation per directive |
| 6 — Deut 6 trigger cases | Done — 6:2 / 6:5 / 6:7 / 6:11 all match OVER-BROKEN pattern; already re-merged in `6933d793f` |
| 7 — Tanakh-specific scope concern | Done — speech-formula pairs + itinerary formulas + Sifrei Emet density flagged as Hebrew-specific; cross-corpus comparison TBD via GNT parallel scan |
| 8 — Don't fix anything | Honored — no v2/heb / validator / canon mutations from this directive |

## Surfaced for cross-corpus comparison

Per directive Cross-corpus note: if Tanakh-side over-breaking is systemic (it is — 69% rate on stratified sample), parallel scans in BoFM + GNT may be warranted. The merge-override (Option A path) decision should be informed by:

- BoFM: heaviest use of J1 parallel-series convention per stock formulaic prose; would likely show similar or higher over-break rate
- GNT: Greek κάι coordination differs from Hebrew vav-conjunctive structurally; rate may be lower; comparison would inform whether merge-override is cross-corpus-shared or Tanakh-specific

Out of scope for this directive; flagged for follow-on Stan-directed cross-corpus parallel scans if Option A is selected.

## Relationship to 2402 directive

Directive 2402 (audit-layer prototype) operates at a passage-level layer that subsumes coordinate-series over-breaking as a special case. Directive 2401's hypothesis is confirmed by independent data here; whether Option A–E intervention happens through 2402's audit-layer apparatus or through standalone validator/canon work is a Stan-decision contingent on 2402's Phase 1 audit outcome (which the parallel reply 2026-05-16-2402-audit-layer-prototype-per-chapter-book-batch.md surfaces).
