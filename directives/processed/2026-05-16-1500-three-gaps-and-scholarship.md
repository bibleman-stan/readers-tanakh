# Three real gaps + scholarship/ + scripts/README

## Context

Alignment-script fix per new protocol + EDITORIAL_ACK reclassifications + H7 path/naming + H16 scale-back work committed in `599d28c19`. Scoreboard now 0 NO_IMPL / 3 DRIFT / 6 EDITORIAL_ACK / 8 ALIGNED. Three real gaps surfaced with per-gap recommendations from Tanakh Claude; plus scholarship/ + scripts/README follow-on.

## Items

1. **Gap 1 — SOLEMNITY_PREFIXES (*koh amar YHWH* / *neum YHWH*) — BUILD.** Stan recommends build per your recommendation. Implementation: 2-entry frozenset hard-coded as STRONG-SPLIT enforcer in `validate_speech_intro_framing.py`. ~2 hours; high corpus impact in prophets (Isaiah, Jeremiah, Ezekiel, the Twelve). **Before building**, confirm there's no morphological variation in the formulas (suffixes like *koh-amar-X-YHWH*, construct forms, defective spelling, *koh amar adonai YHWH* variants) that would turn this into a harder problem. If variation found, surface specific examples before implementation. If formulas are stable as bare 2-token strings, proceed.

2. **Gap 2 — VOCATIVE_CLUSTER_PEERS — ACKNOWLEDGE editorial-only.** Stan recommends acknowledge per your recommendation. H14 inherits H4's EDITORIAL_ACK posture since H4 vocative-position detection requires editorial judgment (Hebrew has no morphological vocative case). Reclassify H14 from DRIFT to ALIGNED via canon §5 update with explicit `Applier: (none — editorial-judgment rule)` notation. Building a vocative-cluster validator before H4 is solvable is premature.

3. **Gap 3 — LIST_FORMULA_PEERS — BUILD with FORK (not extend).** Stan recommends BUILD per your recommendation, but with FORK to `validate_list_formula_uniformity.py` rather than extending `validate_genealogy_uniformity.py`. Reasoning: bundling curse/blessing/beatitude under a "genealogy"-named validator creates naming-truth drift — the file name would no longer describe what it checks. Implementation: 3-lemma frozenset (*arur* / *baruk* / *ashrei*) + parallel-structure uniformity check in the new validator file. ~4 hours. If you have a specific architectural reason to extend rather than fork (e.g., the genealogy uniformity logic is genuinely the same shape and would duplicate substantially), surface the reason before proceeding; otherwise fork.

4. **Scholarship/ directory creation.** Parallel to GNT (created at `708feeef`) and BoFM (likely created in `cdfb096` — verify). Create `private/01-method/scholarship/`. When future §5 work touches rules with scholarly-grounding citations (Joüon-Muraoka, Yeivin, Wickes, Waltke-O'Connor, etc.) inline in the rule body, MOVE them to `scholarship/h{N}.md` per `rule-template.md`, don't delete. Force-add past gitignore if `private/` is gitignored.

5. **scripts/README survey.** Survey scripts in `scripts/`. Categorize: active pipeline tools (regular use) vs archival/diagnostic/one-off scripts (candidates for `scripts/archive/`, which exists with stub README). Propose categorization for Stan review BEFORE writing `scripts/README.md`. The previously-suggested fork from validate_canon_retirement_residue.py as alignment-script precedent is a useful model.

## Reporting

Per item: completed (commit hash) / proposed-for-Stan-review / blocked (reason).

For #1 (after morphology-variation confirmation), #2, #4: implement and commit + push autonomously.

For #3: confirm the FORK direction (or surface counter-argument) before building. After confirmation, implement.

For #5: propose categorization for Stan review BEFORE writing the README.

## Audit triggers

Item #1 (new SOLEMNITY_PREFIXES closed list — STRONG-SPLIT enforcer) trips §7.3 trigger #1 (new named rule / sub-clause / category) AND trigger #2 (closed-list-based rule). Run ≥2 parallel adversarial agents BEFORE any validator infrastructure per CLAUDE.md adversarial-audit discipline.

Item #3 (new LIST_FORMULA_PEERS validator + closed list) trips §7.3 trigger #1 AND #2. Same adversarial-audit requirement.

Item #2 (reclassification) is rule-status change; audit-skippable per §7.4 (matches canon's own existing notation about H4).

Item #4 (scholarship/ directory) is infrastructure; audit-skippable per §7.4.

Item #5 (navigability survey) is infrastructure; audit-skippable per §7.4.
