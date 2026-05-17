# Unanchored English-alignment scan — bound the supplement-attachment problem

## Context

A parallel directive in `readers-gnt/directives/pending/2026-05-16-2300-unanchored-alignment-scan.md` surfaces a class of alignment failure: KJV translation supplements (pronouns / auxiliaries / particles) lack a source-text anchor (Strong's number in GNT; TAHOT lemma in Tanakh) and fall back to surface-proximity attachment to neighboring aligned content. When the grammatically-correct attachment target is on a different line than the surface neighbor, the supplement ends up on the wrong line.

The trigger case: Mark 4:6 in GNT — `ἐκαυματίσθη` ("it was scorched") has implicit Greek subject; KJV "it" before "was scorched" is unanchored and got attached to the previous line ("But when the sun was up, it").

**Hypothesis for Tanakh: same failure class, more severe.** Three structural reasons:
1. Hebrew pro-drop is stronger than Greek — implicit subject across all verb forms (perfect, imperfect, wayyiqtol, jussive)
2. KJV-style English Tanakh adds more periphrastic supplementation than NT KJV: "and it came to pass", "behold", "it shall be", "thou shalt" + auxiliary structures
3. Hebrew→English alignment anchoring is structurally weaker than Greek→English: Hebrew word counts diverge more from KJV word counts (construct chains, verbal suffixes, particle clustering)

**This directive bounds the problem before solution design.** Diagnostic scan only; no fixes.

## Items

1. **Identify unanchored English tokens across the Tanakh corpus.** For each verse in v2/eng (or equivalent KJV-style English render), walk the KJV tokens and flag any token whose alignment to Hebrew (via TAHOT lemma anchor or whatever the Tanakh alignment apparatus uses) is null/missing. Output: per-verse list of unanchored tokens with their current line position in v2/heb.

2. **Classify by POS / function:**
   - **Pronouns**: it, he, she, they, we, you, thou, ye, I, him, her, them, us, me, thee
   - **Auxiliaries**: was, were, is, are, am, be, been, has, have, had, shall, will, would, should
   - **Articles**: the, a, an
   - **Conjunctions**: and, but, or, for, nor, so, yet
   - **Particles**: behold, lo, verily
   - **Tanakh-specific KJV idioms**: "came to pass" (often supplied), "it shall be" supplements, vocative supplements (O LORD, etc.)
   - **Other**: anything else surfaced; document categories as they emerge

3. **For each unanchored token, classify its line-attachment correctness:**
   - **OK**: token is on the line where its grammatical attachment target lives
   - **MIS-ATTACHED**: token is on the line BEFORE or AFTER its grammatical target's line
   - **AMBIGUOUS**: can't determine without judgment

   Use Stanza English UD parsing to determine each unanchored token's grammatical attachment target. Match target token's line position in v2/heb / v2/eng.

4. **Report per category:**
   - Total count of unanchored tokens
   - OK count
   - MIS-ATTACHED count + 5-10 representative examples per category
   - AMBIGUOUS count + sample

5. **Identify the top mis-attachment shapes:**
   - "Subject pronoun stranded at end of prior line before its verb" (Mk 4:6 shape adapted) — count
   - "Auxiliary stranded after subject when verb is on next line" — count
   - "Conjunction stranded at end of prior clause" — count
   - "And-it-came-to-pass supplement on wrong line" (Tanakh-specific) — count
   - Other shapes surfaced — count + describe

6. **Intervention-scope estimate for Stan:**
   - Whether the MIS-ATTACHED volume justifies an LLM-resolver pattern (sibling to BoFM's `resolve_review_required.py`)
   - Whether a mechanical heuristic alone would cover the majority (e.g., "unanchored pronoun whose UD target is on next line → attach to next line")
   - Hybrid: mechanical for high-confidence shapes; LLM-resolver for the residue
   - Cost estimate (if LLM-resolver path): expected Sonnet calls per pass corpus-wide

7. **Tanakh-specific scope concern:** if a category emerges that's distinctively a Hebrew-translation-pattern issue (e.g., "and it came to pass" supplementation, vocative supplementation), flag it separately. Cross-corpus comparison with GNT's parallel scan will reveal which categories are universal English-supplement issues vs Hebrew-translation-specific.

8. **Don't fix anything.** Diagnostic only. No alignment changes; no v2 modifications.

## Reporting

Reply at `directives/replies/2026-05-16-2300-unanchored-alignment-scan.md`:

- Per-category counts table (OK / MIS-ATTACHED / AMBIGUOUS)
- Top 5 mis-attachment shapes with counts
- Representative MIS-ATTACHED examples per category (5-10 each)
- Tanakh-specific category surfacing (per Item 7)
- Intervention-scope recommendation: LLM-resolver / mechanical-heuristic / hybrid / hand-fix-only
- Cost estimate (if LLM-resolver): expected Sonnet call volume + tier
- Cross-corpus comparison hooks: what data would let us compare against the GNT scan's results when it lands

## Audit triggers

Diagnostic scan. No alignment changes. No validator changes. No rule changes. **Audit-skippable per §7.4.**

If/when an intervention is selected, that's a separate directive with its own audit trigger assessment.

## Parallelism note

Runs independently of other queued directives. The parallel GNT directive (`readers-gnt/directives/pending/2026-05-16-2300-unanchored-alignment-scan.md`) runs the same scan against Greek→KJV alignment. After both replies land, cross-corpus comparison will inform whether the resolver pattern should be cross-corpus-shared (live in `atu_method.alignment_resolution`) or per-repo (each carries its own `scripts/resolve_alignment_supplements.py`).
