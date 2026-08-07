# Scholarship — Per-Rule Defensibility Chain

This directory holds the scholarly-grounding citations for each §5 rule that draws on external reference grammars or Masoretic apparatus literature. Convention parallels [`atu-method/docs/rule-template.md`](../../../../atu-method/docs/rule-template.md) and runs across all three readers (BoFM / GNT / Tanakh).

## Convention

When §5 work touches a rule that has inline scholarly citations (Joüon-Muraoka, Yeivin, Wickes, Waltke-O'Connor, Arnold-Choi, GKC, Niccacci, etc.) in the rule body, MOVE the citation prose to `2-evidence/scholarship/h{N}.md` for that rule. **Don't delete** — preservation of the scholarly defensibility chain is mandatory.

## File naming

- `h{N}.md` per §5 H-rule (e.g., `h7.md` for Rule H7 — Complement Integrity).
- Sub-rule suffixes use letter form: `h5b.md`, `h6_1.md` (for `H6.1 — Perpetual Qere`).
- Index-only file: this README. Per-rule files contain the actual citation prose.

## Per-file structure

```markdown
# Rule H{N} — {title} — Scholarship

## Reference-grammar citations

- **W&O §X.Y** — passage, page-range, quoted relevance to this rule.
- **JM §X.Y** — similar.
- **AC §X.Y** — similar.

## Masoretic-apparatus citations

- **Yeivin 1980 §N** — for petucha/setuma, accent-system, Ketiv/Qere policy.
- **Wickes 1881/1887** — for te'amim distinctions (now historical only; canon §1 retires te'amim consultative role).

## Cross-corpus precedent

Pointers to sibling-canon scholarship files for the analog rule:
- BoFM: `../../../../readers-bofm/private/01-method/2-evidence/scholarship/{R|M}{N}.md`
- GNT: `../../../../readers-gnt/private/01-method/2-evidence/scholarship/{R}{N}.md`

## Editorial decisions touching this scholarship

Brief notes on canon revisions or §7 audit outcomes that turned on the scholarly grounding documented above.
```

## What stays in the canon entry vs moves here

**Stays in the canon §5 entry:**
- Rule statement (Grammatical basis / Trigger / Diagnostic / Exceptions / Examples).
- A one-line `references:` field in the YAML footer pointing here (e.g., `references: 2-evidence/scholarship/h7.md`).
- Worked-example commentary that is operationally load-bearing.

**Moves here:**
- Multi-paragraph quotes from reference grammars.
- Cross-section grammar-of-grammars citations (W&O §X.Y vs AC §X.Y vs JM §X.Y triangulation).
- Historical-tradition justifications (Masoretic apparatus, medieval grammatical tradition).
- Citation chains that no operator reads on a daily work cycle but that the §7 change-protocol audit needs for defensibility verification.

The boundary test: if a citation has to be in front of an editor during a per-verse application, it stays. If it's only consulted during a canon revision or audit, it moves here.

## Backlog (rules with inline scholarship awaiting extraction)

Per audit-on-touch convention: extract per-rule when next touched. Current §5 entries with substantial inline scholarship (estimated ≥3 reference-grammar citations or ≥1 paragraph of citation-heavy prose):

- H2 (Construct Chain) — W&O §9.3, §9.5, §9.3d
- H3 (Vav-Consecutive) — W&O §33.1.1c, §33.1.2g, §33.2.1, §33.2.2, §33.2.3; AC §3.5.1, §3.5.4
- H5 (Speech Framing) — W&O §36.2.3, §36.2.1; AC §3.4.1
- H5b (Speech-Act Announcement) — W&O §34.3, §34.5.1, §34.2; AC §3.3, §3.5.3
- H7 (Complement Integrity) — W&O §10.2.1, §10.2.3, §11.4.1; AC §2.3.1
- H9 (Divine-Title Appositives) — W&O §12.3 (multi-subsection); AC §2.4
- H14 (Discourse Particles) — W&O §39.3 (multi-subsection); AC §4.2, §4.5
- H15 (Casus Pendens) — W&O §4.7, §16; AC §2.1.4
- H16 (FEF Wayehi Protasis) — W&O §33.2.4, §38.7; AC §5.2.4, §5.2.11
- H17 (Genealogy/List-Formula) — W&O §39.2.1, §39.2.5; AC §5.3.4
- H18 (Clause-Nucleus Integrity) — W&O §8.4.1, §8.4.2, §37.6, §37.7; AC §5.1; plus GKC §141, JM §154, §121, §156

Extraction order: opportunistic (when the next §7 audit or canon revision touches the rule). No batch-extraction wave planned.
