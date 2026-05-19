# Retroactive adversarial audit — Gaps 1 + 3 validators — reply

## Dispatch summary

Per directive items 1+2: 4 Sonnet agents dispatched in parallel (2 per validator). Per item 3: independent dispatch (no cross-agent context). All 4 returned with structured findings. Total wall-time: ~4–8 minutes per agent. Per directive item 5: **no validator auto-revised**; specific code changes proposed below for Stan review.

## Cross-agent agreement table — validate_speech_intro_framing (Gap 1)

| Finding | Agent A | Agent B | Agreement | Severity |
|---|---|---|---|---|
| Literary *נאם* FP (Ps 36:2, Prov 30:1, Num 24:4–6) | ✓ (F1+F2) | ✓ (F2) | **HIGH-CONFIDENCE** | must-fix |
| 2 Sam 23:3 doubled *נאם* (ונאם) | ✓ (F3) | ✓ (F3) | **HIGH-CONFIDENCE** | must-fix |
| Maqqef-joined *כה־אמר* single-token miss (~60 missed splits) | — | ✓ (F1) | single-agent | **must-fix** (largest impact) |
| Josh 22:16 quantifier *כל* — split position offset | ✓ (F4) | — | single-agent | nice-to-have |
| Zech 12:1 participial relative-clause modifier | ✓ (F5) | — | single-agent | nice-to-have (overlaps with literary *נאם* FP class) |
| Cross-rule collision (leemor / H5b / H7) | non-issue (F7) | non-issue (F4) | agreement | non-issue |
| Aramaic / nested human-formula | — | non-issue (F5+F6) | single-agent | non-issue |

## Cross-agent agreement table — validate_list_formula_uniformity (Gap 3)

| Finding | Agent C | Agent D | Agreement | Severity |
|---|---|---|---|---|
| V1_DIR default in `main()` (semantic mismatch with regression-audit purpose) | — | ✓ (F2) | single-agent | **must-fix** |
| `LIST_FORMULA_PEERS` excludes הוי woe-series (3 unprotected: Isa 5:20–22, Isa 45:9–10, Zech 2:10–11) | — | ✓ (F1) | single-agent | nice-to-have |
| Docstring pre-flight count wrong (4 אשרי series, not 2 — Ps 84 + Ps 119 omitted) | ✓ (F1) | — | single-agent | nice-to-have |
| Ps 119:1–2 acrostic series undocumented | ✓ (F2) | — | single-agent | nice-to-have |
| `\w` in verse-ref regex matches Hebrew consonants (latent) | ✓ (F3) | — | single-agent | nice-to-have |
| `cur_verse` stored but never used in series detection | ✓ (F4) | ✓ (F3) | agreement | non-issue (dead code) |
| `is_skippable` verse-ref branch unreachable | ✓ (F5) | — | single-agent | non-issue (dead code) |
| Closed-list cognate completeness (מקלל, יברך, בריך) | non-issue (F6) | — | single-agent | non-issue (verified) |
| Missing-verse-ref silent mis-grouping | — | non-issue (F5) | single-agent | non-issue |
| N=2 threshold rationale | — | non-issue (F6) | single-agent | non-issue |

## Per-finding detail and proposed revisions

### Gap 1 — validate_speech_intro_framing SOLEMNITY extension

**Must-fix #1 — Maqqef-joined *כה־אמר* coverage gap (Agent B F1) — LARGEST IMPACT**

Trigger logic at line ~947:
```python
if first_sub == "כה" and len(tokens) > 1:
    second_sub = _first_subtoken_skel(tokens[1])  # ← checks tokens[1], not subs of tokens[0]
    if second_sub not in ("אמר", "אמרו"):
        return None
```

When `כֹּֽה־אָמַ֤ר` is one maqqef-joined orthographic token, `tokens[0]` = the joined word; `_first_subtoken_skel(tokens[0])` correctly returns "כה" (first sub-skel). But `tokens[1]` is then the subject NP (יהוה / המלך / …), NOT "אמר". Trigger short-circuits and never fires.

Agent B's corpus scan: **83 lines have `tokens[0]` first-sub = "כה" + second-sub starts with "אמר*" inside the same maqqef-joined token**. Of those, **60 have non-cluster content beyond the subject NP** = same-line cases the validator silently misses. Cited examples: `exodus-10.txt:15`, `judges-06.txt:38`, `2samuel-12.txt:41`, `1kings-02.txt:169`.

**Proposed revision**: extend the כה-trigger to also accept the case where "אמר" appears as a sub-skel inside `tokens[0]` itself. Roughly:

```python
def _all_sub_skels(orig_token: str) -> list[str]:
    """All maqqef-separated sub-skels of an original token."""
    normalized = _HEBREW_KEEP_MAQQEF_RE.sub("", orig_token)
    return normalized.split("־")

# In detect_solemnity_split_position(), replace the כה-branch:
if first_sub == "כה":
    # Check sub-skels of tokens[0] for "אמר" (maqqef-joined כה־אמר case)
    subs0 = _all_sub_skels(orig_tokens[0])
    if len(subs0) >= 2 and subs0[1] in ("אמר", "אמרו"):
        idx = 1  # past the כה־אמר maqqef-group (one orthographic token)
    elif len(orig_tokens) >= 2:
        # Standard whitespace-separated case
        second_sub = _first_subtoken_skel(orig_tokens[1])
        if second_sub in ("אמר", "אמרו"):
            idx = 2  # past prefix + verb
        else:
            return None
    else:
        return None
```

Expected post-fix emission count: 108 + ~60 = ~168 STRONG-SPLIT findings.

**Must-fix #2 — Literary *נאם* genitive-attribution FP class (Agents A F2 + B F2)**

Confirmed corpus FPs:
- **Ps 36:2** — *נְאֻם־פֶּשַׁע לָרָשָׁע…* — "oracle of transgression" (personification; not divine/prophetic speaker)
- **Prov 30:1** — *נְאֻם הַגֶּבֶר לְאִיתִיאֵל…* — wisdom-book attribution (subscription, not speech-frame)
- **Num 24:4** — *נְאֻם שֹׁמֵעַ אִמְרֵי־אֵל…* — Balaam title (participial relative clause as attribution)
- **Num 24:16** — same Balaam-title pattern

Root cause: trigger fires on any line beginning with *נאם* without verifying the post-*נאם* NP is an attested speaker class. Cluster-walk treats the participle / common-noun head as "content."

**Proposed revision** (Macula-IR primary, lexicon fallback):
- When Macula IR is available for the verse, query whether the post-*נאם* NP constituent has a Speaker/Attribution role label. If not, return None (no split).
- As lower-cost fallback: if the post-*נאם* token's TAHOT tag is `Vqr*` (active participle) OR `HC/Nc*` (article + common noun) AND the participle/noun begins a relative-clause cluster, return None.
- Sifrei Emet meter-carve-out could optionally demote *נאם* FPs to REVIEW-REQUIRED (Ps 36:2 is in Sifrei Emet); annotation-only.

**Must-fix #3 — 2 Sam 23:3 doubled *נאם* (Agents A F3 + B F3)**

Line: *נְאֻם דָּוִד בֶּן־יִשַׁי וּנְאֻם הַגֶּבֶר הֻקַם עָל מְשִׁיחַ אֱלֹהֵי יַעֲקֹב וּנְעִים זְמִרוֹת יִשְׂרָאֵל׃*

Cluster walk: idx=1 דָּוִד (Np) ✓, idx=2 בֶּן (in cluster) ✓, idx=3 וּנְאֻם — first-sub "ונאם" ≠ "נאם" → cluster ends → fires STRONG-SPLIT at idx=3. But this is a coordinate double-attribution; entire verse is title, no content.

**Proposed revision**: add "ונאם" to `FORMULA_CLUSTER_CONTINUATION_SKELS` (one-token addition; only one corpus instance). Or extend cluster-walk to recognize vav-prefixed *נאם* as a coordinate continuation of the formula.

**Nice-to-have #1 — Josh 22:16 quantifier *כל* (Agent A F4)**

Line opens *כֹּה אָמְרוּ כָּל עֲדַת יְהוָה מָה־הַמַּעַל…* — split fires at idx=2 (`כל`) because quantifier is not in cluster, not Np. Emission itself is correct (line IS a same-line case), but `split_pos` reports 2 instead of 5 (the true end-of-subject-NP). If apply_validators uses `split_pos` mechanically, the produced split is wrong.

**Proposed revision**: add "כל" to `FORMULA_CLUSTER_CONTINUATION_SKELS` as quantifier-can-precede-subject-NP, OR extend cluster-walk to accept TAHOT `Aq` (quantifier) tags. One corpus instance.

**Nice-to-have #2 — Zech 12:1 participial relative-clause modifier (Agent A F5)**

Line: *נְאֻם יְהוָה נֹטֶה שָׁמַיִם וְיֹסֵד אָרֶץ וְיֹצֵר רוּחַ אָדָם…* — split fires at idx=2 (נטה). Same class as Must-fix #2 (literary *נאם*) — participial relative clause modifying speaker treated as content. Fixed by same Macula-IR / Vqr* gate.

### Gap 3 — validate_list_formula_uniformity

**Must-fix #1 — V1_DIR default in main() (Agent D F2)**

Code at line ~217:
```python
root = V2_DIR if args.v2 else V1_DIR
```

Validator docstring states regression-audit purpose against v2 (source of truth). Default scans v1 (mechanical te'amim draft). Currently silent because both v1 and v2 emit 0 findings, but the semantic contract is inverted vs every other production-use convention (which reads v2). Run_all.py's invocation path needs verification.

**Proposed revision** (flip the default; add explicit --v1 flag for legacy access):
```python
root = V1_DIR if args.v1 else V2_DIR
# … and rename argparse argument:
p.add_argument("--v1", action="store_true",
               help="scan v1/he-baseline mechanical draft (default: v2/heb)")
```

Verify run_all.py auto-discovers and calls with --v2 OR --json (which would pass the v1 default through). If yes, the post-fix default change is silent but correct.

**Nice-to-have #1 — הוי woe-series exclusion (Agent D F1)**

3 corpus series unprotected from future regression:
- Isa 5:20–22 (3 consecutive הוי verses)
- Isa 45:9–10 (2 consecutive)
- Zech 2:10–11 (2 consecutive)

All currently line-leading; validator emits 0 today. But a future edit moving הוי mid-line would not be caught.

**Proposed revision**: add "הוי" (and possibly "אוי") to `LIST_FORMULA_PEERS`. Update canon §5 H17 closed-list description to include woe-formula scope. Stan-decision: add or leave as canon-spec-only?

**Nice-to-have #2 — Docstring count correction (Agent C F1)**

Docstring states 6 series instances: "Deut 27 curse + Deut 28 blessing pairs; 2 Chr 9 + Ps 144 beatitude pairs." Corpus actually has 4 אשרי series (Ps 84:5–6, Ps 119:1–2, 2 Chr 9:7–8, Ps 144:15) + Deut 27 (12-curse run) + Deut 28 series. Update docstring to match.

**Nice-to-have #3 — Verse-ref regex tightening (Agent C F3)**

`_VERSE_REF_RE = re.compile(r"^(\w+\s+)?\d+:\d+\s*$")` — Python's `\w` in Unicode matches Hebrew consonants. Latent FP: a content line of unpointed Hebrew + accidental `N:M` pattern would be eaten. 0 real corpus cases today.

**Proposed revision**: tighten to `re.compile(r"^\d+:\d+\s*$")`. All corpus verse refs are bare `N:M`.

## Per-validator recommendation

### validate_speech_intro_framing SOLEMNITY extension — **REVISE recommended**

3 must-fix findings:
- Maqqef-coverage gap → ~60 silently missed splits (≈60% under-emission vs corrected baseline)
- Literary *נאם* FP class → ≥4 confirmed FPs in 108 emissions (3.7% FP rate; concentrated in Sifrei Emet + Balaam oracles)
- 2 Sam 23:3 doubled *נאם* → 1 confirmed FP

The maqqef-coverage gap is structurally the biggest finding — almost doubles the validator's true coverage. Combined with the FP class (≈4–7 of 108 emissions), the as-built validator is BOTH under-firing (60 misses) AND over-firing (4–7 FPs).

**Recommended fix order** (by impact):
1. Maqqef-coverage gap (largest under-emission)
2. Literary *נאם* FP gate (largest over-emission class)
3. 2 Sam 23:3 ונאם cluster-continuation (single case)
4. Josh 22:16 + Zech 12:1 corner cases (overlap with #2's fix)

If applied as a cluster, post-revision emission estimate: ~168 STRONG-SPLIT (108 + 60 missed) minus ~5 FPs removed = ~163 verified STRONG-SPLIT candidates.

### validate_list_formula_uniformity — **STAND with one MUST-FIX** (V1_DIR default flip)

The validator's core algorithm is correct: Deut 27 12-curse run detected as one series; Deut 28 blessing/curse separated; cognate exclusions verified; closed list correctly scoped for canon §5 H17.

One must-fix: flip the V1_DIR default to V2_DIR.

Nice-to-have items (all low-risk):
- הוי woe-series extension (regression-audit gap; 3 unprotected series)
- Docstring count correction
- Verse-ref regex tightening
- Dead-code cleanup (`cur_verse` field, `is_skippable` verse-ref branch)

## Open Stan-decisions

**For validate_speech_intro_framing**: authorize revision per cluster-fix order above? If yes, follow-up directive to dispatch revision + corpus pre-flight + spot-check.

**For validate_list_formula_uniformity**: flip default V2_DIR (authorize)? Add הוי to LIST_FORMULA_PEERS (Stan judgment-call; canon §5 H17 doesn't name it)?

Per directive item 5 closing: "STOP at the recommendation step. Do NOT implement revisions. Stan reviews the audit report + decides whether to authorize revision via a follow-on directive." — **stopping here**.
