# Authorize 2200 audit revisions — Gap 1 + Gap 3 fixes

## Context

The 2200 retroactive adversarial audit (`directives/replies/2026-05-16-2200-retroactive-adversarial-audit.md`) identified must-fix findings on both validators:

**validate_speech_intro_framing (Gap 1) — REVISE recommended (3 must-fix):**
- Maqfek-coverage gap (Audit B F1) — 60 silently missed splits — LARGEST IMPACT
- Literary *נאם* genitive-attribution FP class (Audits A F2 + B F2) — ≥4 confirmed FPs in 108 emissions
- 2 Sam 23:3 doubled *נאם* / ונאם (Audits A F3 + B F3) — 1 confirmed FP

**validate_list_formula_uniformity (Gap 3) — STAND with 1 must-fix:**
- V1_DIR default in main() (Audit D F2) — semantic mismatch with regression-audit purpose

Stan authorizes implementation of all 4 must-fix items per the audit's proposed revisions. Nice-to-haves are at Tanakh-Claude's judgment.

## Items

### Must-fix 1 — Maqfek-coverage gap in validate_speech_intro_framing

1. Implement the `_all_sub_skels` extension per Audit B's proposed code in the 2200 reply (see "Proposed revision" block under Must-fix #1). Replace the existing כה-trigger branch to handle the maqfek-joined `כֹּֽה־אָמַ֤ר` single-token case.

2. **Pre-implementation morphology check**: confirm the 83 cases Audit B identified (maqfek-joined `tokens[0]` with first-sub "כה" + second-sub "אמר*") match the actual corpus data. If count diverges materially (>10%), surface for Stan before proceeding.

3. **Post-implementation corpus run**: capture STRONG-SPLIT emission count. Expected: 108 + ~60 = ~168 cases. If count is materially different from 168 ± 10, surface for Stan-review before commit.

### Must-fix 2 — Literary *נאם* FP gate in validate_speech_intro_framing

4. Implement the Macula-IR primary + lexicon fallback per Audit A's proposed revision (see 2200 reply Must-fix #2). When the post-*נאם* NP is a participle (TAHOT `Vqr*`) or article + common noun (`HC/Nc*`) that begins a relative-clause cluster, return None (no split).

5. **Spot-check the 4 known FPs after implementation**:
   - Ps 36:2 (*נְאֻם־פֶּשַׁע* — "oracle of transgression")
   - Prov 30:1 (*נְאֻם הַגֶּבֶר לְאִיתִיאֵל*)
   - Num 24:4 (Balaam title)
   - Num 24:16 (Balaam title)

   All four should NOT emit STRONG-SPLIT post-fix. If any still fires, surface for Stan before commit.

6. **Sifrei Emet meter-carve-out**: deferred. Audit A surfaced it as optional; not in scope of this directive.

### Must-fix 3 — 2 Sam 23:3 vav-cluster (ונאם)

7. Add `"ונאם"` to `FORMULA_CLUSTER_CONTINUATION_SKELS` (one-token addition; one corpus instance — 2 Sam 23:3). Confirm post-fix that 2 Sam 23:3 no longer emits STRONG-SPLIT at the false position.

### Must-fix 4 — Gap 3 V1_DIR → V2_DIR default flip

8. Per Audit D F2: in `validators/colometry/validate_list_formula_uniformity.py` `main()`, flip the default from V1_DIR to V2_DIR. Add explicit `--v1` flag for legacy access.

9. **Verify run_all.py auto-invocation**: confirm run_all.py invokes the validator with `--json` (which would pass the V1_DIR default through silently in the current shape, switching to V2_DIR silently post-fix). Surface if the invocation path needs updating.

### Nice-to-haves (Tanakh-Claude judgment)

10. **Josh 22:16 quantifier *כל***: add to `FORMULA_CLUSTER_CONTINUATION_SKELS` (one corpus instance). Same shape as Must-fix #3; low risk; do if convenient.

11. **Zech 12:1 participial relative-clause modifier**: overlaps with Must-fix #2's Vqr* gate fix; likely auto-resolved.

12. **הוי woe-series extension to LIST_FORMULA_PEERS**: **Stan-decision needed** — does הוי belong in LIST_FORMULA_PEERS? Tanakh-Claude reads canon §5 H17 and decides. If yes, add and update canon prose. If no, document in reply and move on. Three unprotected series (Isa 5:20-22, Isa 45:9-10, Zech 2:10-11) are currently line-leading so no regression risk today; adding protects against future edits.

13. **Docstring count correction**: update validate_list_formula_uniformity docstring from "6 series" to actual corpus count (4 *אשרי* + Deut 27 + Deut 28).

14. **Verse-ref regex tightening**: `_VERSE_REF_RE` → `re.compile(r"^\d+:\d+\s*$")`. Latent FP; 0 real cases today.

15. **Dead-code cleanup**: `cur_verse` field; `is_skippable` verse-ref branch.

### Post-implementation

16. **Run alignment-check** post all fixes. Expected: verdicts unchanged (9 ALIGNED / 6 EDITORIAL_ACK / 2 DRIFT remain stable — these fixes don't address the H5/H17 naming-drift items).

17. **Update baselines**: validate_speech_intro_framing baseline 449 → ~163 (per Audit A's post-revision estimate); validate_list_formula_uniformity baseline 0 → 0 (V1→V2 default flip doesn't change verdict counts in this case but verify).

## Reporting

Reply at `directives/replies/2026-05-16-2400-authorize-2200-revisions.md`:

- Per must-fix: commit hash + before/after counts + spot-check results
- Nice-to-have dispositions (Stan-decision items annotated)
- Final alignment-check verdicts
- Baseline updates
- Any cases where the fix's behavior diverged from the audit's prediction (surfacing required)

## Audit triggers

Revisions to existing validators:
- Must-fix #1 (maqfek-coverage) — code-correctness fix; was silently dropping cases the rule scope already includes. **§7.4 audit-skippable** (no rule scope change; bug fix on existing rule).
- Must-fix #2 (literary *נאם* gate) — adds detection logic but tightens existing trigger, not extending it. **§7.4 audit-skippable** (no rule scope expansion; FP reduction).
- Must-fix #3 (vav-cluster) — one-token addition to existing closed list. **§7.4 audit-skippable** (closed-list refinement, not extension to new rule scope).
- Must-fix #4 (V1→V2 default flip) — configuration fix; no rule change. **§7.4 audit-skippable.**

**Important reverse-check** per 2203 audit precedent: if during implementation any of the fixes turns out to ACTUALLY be a scope expansion (not just bug-fix or tightening), STOP and surface for Stan re-decision rather than proceeding. The §7.4 classification rests on the fixes being structurally what the audit characterized them as.
