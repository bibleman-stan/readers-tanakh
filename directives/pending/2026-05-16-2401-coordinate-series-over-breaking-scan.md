# Coordinate-series over-breaking diagnostic — corpus-wide scan

## Context

Stan-observation on Deut 6 (via vault-Claude tracking, 2026-05-16 late evening):

> *"looking at the chapter, i am seeing some real question marks about whether it's over-broken"*

Specific patterns surfaced in Deut 6 v2/heb:

- **v.2** `אַתָּה / וּבִנְךָ / וּבֶן־בִּנְךָ` — three bare coordinate NPs ("you / and your son / and your son's son") each on their own line. Three ATU lines for three pronouns expanding a single apposition.
- **v.5** `בְּכָל־לְבָבְךָ / וּבְכָל־נַפְשְׁךָ / וּבְכָל־מְאֹדֶךָ` — the Shema's heart/soul/might tricolon, each on its own line.
- **v.7** `בְּשִׁבְתְּךָ / וּבְלֶכְתְּךָ / וּבְשָׁכְבְּךָ / וּבְקוּמֶךָ` — four infinitival temporal PPs, line per member.
- **v.11** `וְאָכַלְתָּ֖ / וְשָׂבָֽעְתָּ` — two bare verbs ("and you shall eat / and be satisfied") on **two separate lines** with no content beyond the bare verbs.

**Pattern hypothesis (vault-Claude surface):** J1 (parallel-series convention) is firing on the coordinator `וְ` without a length/content-density check. The implicit rule may need an M-override along the lines of *"if all coordinate members are below threshold-N tokens AND share verb/predicate, merge as single ATU."*

If this hypothesis holds corpus-wide, it affects every list-heavy passage (Shema-style enumerations, stock verb pairs, infinitival temporal PPs, possibly genealogies though those may be intentionally exempt).

**Diagnostic only.** Bound the problem before designing the intervention.

## Items

1. **Survey v2/heb for coordinate-series breaks corpus-wide.** Definition: any sequence of ≥2 consecutive ATU lines where each line begins with a `וְ`-prefixed token (or a bare coordinate continuation of the prior line's predicate structure) AND each line's token-count is below a threshold (suggest 4 tokens as initial threshold; surface the choice).

   For each detected series, capture:
   - Verse reference + start/end line indices
   - Number of members in the series
   - Token count per member (mean, max, min)
   - First member's primary token + UPOS (from TAHOT) — distinguishes NP-series / PP-series / verb-series / mixed
   - Whether all members share a verb / predicate context (single-verb-multiple-arguments shape) or are independent clauses

2. **Classify each series by structural type:**
   - **NP-series** — coordinate noun-phrase members (Deut 6:2 pattern)
   - **PP-series** — coordinate prepositional-phrase members (Deut 6:5 / 6:7 pattern)
   - **Bare-verb-series** — coordinate finite verbs with no objects/complements (Deut 6:11 *eat/be-satisfied* pattern)
   - **Mixed-or-complex** — series with members of different types
   - **Long-member** — series where at least one member exceeds the token threshold (these are likely legitimately broken; surface for comparison)

3. **Sample 100 short-member series for editorial-correctness classification.** Stratify sample across the 4 short-member structural types (25 per type). For each sampled series, classify:
   - **Correctly broken** — series is structurally one-ATU-per-member; current breaks are right
   - **Over-broken (should merge)** — series is structurally one ATU with internal parallelism; current breaks are too aggressive
   - **Ambiguous** — judgment call; surface for review

   Use Sonnet per `feedback_model_selection_frugality` (structured per-instance judgment within defined rubric). 100 cases × 1 dispatch = ~5-10 min wall-time.

4. **Pattern analysis from the 100-case sample:**
   - Over-broken rate per structural type (which types are systematically over-broken?)
   - Token-count distribution of over-broken vs correctly-broken (does threshold-N predict over-broken-ness?)
   - Verb/predicate-sharing correlation (do shared-verb series over-break more than independent-clause series?)
   - Book / genre patterns (does over-breaking concentrate in narrative prose, legal prose, poetry, Shema-style enumerations?)
   - Sub-pattern surfacing: stock verb-pairs (*eat/be-satisfied*, *go-and-do*, *hear-and-do* etc.) — count + flag as distinct sub-class

5. **Recommend intervention shape:**
   - **Option A**: M-override codification (new merge-override rule subsuming below-threshold coordinate-series). Specify threshold, structural-type scope, exceptions. Would trip §7.3 trigger #1 (new merge-override rule).
   - **Option B**: Per-pattern targeted closed lists (e.g., STOCK_VERB_PAIRS closed list catching *eat/be-satisfied*, *bow-and-worship*, *hear-and-do* etc.). Smaller scope; might miss the broader pattern. Trips §7.3 trigger #1 + #2.
   - **Option C**: Bare editorial-rule annotation in canon (no validator change; surface the pattern in canon §5 for human editorial reference). Smallest commitment.
   - **Option D**: Per-corpus override JSON for the specific over-broken instances (analogous to BoFM 2400 Option A pattern). Bounded by sample-survey results.
   - **Option E**: Defer pending further investigation.

   Don't recommend yet — surface the data + options for Stan-decision.

6. **Don't fix anything.** Diagnostic only. No v2/heb modifications. No validator changes. No canon edits.

## Reporting

Reply at `directives/replies/2026-05-16-2401-coordinate-series-over-breaking-scan.md`:

- Survey output (Item 1) — per-book counts of detected series + structural-type distribution
- 100-case classification table (Item 3) — verse refs + structural type + verdict + reasoning
- Pattern analysis findings (Item 4) — by-type over-broken rates + token-count correlation + sub-pattern surfacing
- Intervention options (Item 5) with the data each option draws on; no ranking, no recommendation
- Specific verdict on the Deut 6 trigger cases (v.2, v.5, v.7, v.11) — are they over-broken per the 100-case-sample's structural classifier?

## Audit triggers

Diagnostic scan; no validator changes; no rule changes; no canon edits. **Audit-skippable per §7.4.**

If/when an intervention from Options A-D is selected, that's a separate directive with its own audit trigger assessment:
- Option A (M-override) — §7.3 trigger #1; per 2203 + GNT-2400 precedent, requires ≥2 parallel adversarial agents
- Option B (closed lists) — §7.3 trigger #1 + #2
- Option C (canon annotation) — §7.4 skippable (editorial-rule documentation, no code change)
- Option D (per-instance override) — §7.4 skippable (per-case data layer)

## Cost note

1 Sonnet pass at 100 cases. Modest. Per `feedback_model_selection_frugality`, Sonnet is right tier for structured classification within a defined rubric.

The corpus survey (Item 1) is a one-off script that doesn't need LLM dispatch — mechanical token-count + TAHOT-tag inspection.

## Parallelism note

Runs independently of any other queued directives. Tanakh-Claude can process whenever triggered. The Deut 6 trigger cases are explicit in Item 6 reporting requirements so the diagnostic surfaces Stan's specific concern directly + the corpus-wide pattern context together.

## Cross-corpus note

If this scan surfaces over-breaking as a systemic Tanakh issue, parallel scans in BoFM + GNT may be warranted (especially BoFM where the J1 parallel-series convention is most aggressively applied per the corpus's heavy use of stock formulaic prose). Cross-corpus comparison would inform whether the merge-override (Option A) should be a cross-corpus shared discipline or Tanakh-specific. Out of scope for this directive; tracked for follow-on if results warrant.
