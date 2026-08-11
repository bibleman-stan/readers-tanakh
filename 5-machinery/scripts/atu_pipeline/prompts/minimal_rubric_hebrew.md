# Minimal Rubric — Hebrew (Stage 1 canonical prompt)

This is the canonical Stage 1 prompt for Hebrew ATU rendering. Three Opus passes use this prompt; agreement scoring across the three passes determines auto-apply (unanimous) vs editorial review (non-unanimous). See `../toolset-architecture.md` §Stage 1.

The prompt embodies the minimal rubric: bidirectional test + restrictive-relative binding + a small set of Hebrew-specific syntactic constraints + default KEEP-AS-IS. NO cognitive-unity gate. NO parallelism class adjudication. NO genre anchors as primary licenses.

---

## The Prompt

Render the following Hebrew chapter into Atomic Thought Units (ATUs) per the minimal rubric.

### What an ATU is

An ATU is the smallest cognitive chunk an attentive reader processes as a discrete unit. One ATU per line in the rendered output.

### Bidirectional test (the criterion)

A line is a legitimate standalone ATU only if BOTH:

**1. Forward grammatical closure** (Hebrew terms):

- Finite verb: subject encoded by inflection is sufficient (Hebrew pro-drop OK)
- Verbless / nominal-predicate clause: subject + non-verbal predicate (NP / PP / Adj) in juxtaposition counts as closed (Hebrew has no overt copula in present-tense verbless clauses)
- Participial predication: subject + active/passive participle counts as closed (participle fills the slot of a finite verb)
- Exclamatory / declarative particle-headed (`אַשְׁרֵי X` / `הִנֵּה X` / `הָבָה X`): closed when NP complement is present on the line
- Conditional protasis (`אִם` / `כִּי` + verb) in legal-casuistic case-law (Exod 21–23, Lev 1–7, Num 5, Deut 19–25): closed even though grammatically open toward the apodosis; protasis AND apodosis are distinct ATUs
- Bare construct-state noun awaiting genitive on next line: **FAILS** forward closure (bare-governor indivisibility)

**2. Backward referential self-containment**:

- Overt referents present on the line OR recoverable from finite-verb morphology OR same discourse-active subject as immediately prior ATU (wayyiqtol chains, sequential imperatives, legal-section addressee)
- Chain breaks at: speaker change in direct speech, vocative redirecting addressee, parenthetical `כִּי` clause, intervening clause with overt new subject NP
- FAILS when long-range antecedents (>1 ATU back, no chain-continuity) are required

A break between two adjacent lines is licensed if and only if BOTH lines independently satisfy these two conditions.

The test is **asymmetric**: cataphoric reference (forward-pointing — presentative `הִנֵּה` + indefinite NP introducing new content; `thus says X:` announcing speech) does NOT fail the test; only anaphoric unresolved-backward-dependence fails.

### Restrictive relative clause binding

Restrictive (defining) `אֲשֶׁר`-clauses bind to head noun and cannot stand as standalone ATUs regardless of internal completeness. Diagnostic: would removing the relative clause leave the head uniquely identified? If no → restrictive → BIND.

Non-restrictive (descriptive) relative clauses may stand alone as ATUs when they pass the bidirectional test AND the head is already identified.

### Hebrew-specific constraints

- **Gapped finite verb in immediate parallel cola**: a colon whose finite verb is gapped from the immediately preceding parallel colon counts as forward-closed if the gapped verb is unambiguously recoverable.
- **Discourse particle + governed content**: particles like `לָכֵן` / `וְעַתָּה` / `הִנֵּה` / `אַשְׁרֵי` lead content and bind to it. Particle alone fails forward closure; particle + governed NP/clause forms one ATU.
- **Speech-intro + short particle-led reply/vocative**: `וַיֹּאמֶר X` + short particle-led unit (vocative call, `הִנֵּנִי`, etc.) = ONE ATU. Speech-intro and short reply bind.
- **Resumptive pronoun integrity** (legal lists): resumptive pronouns alone on their line (`אֹתָהּ` / `אֹתוֹ` alone) FAIL backward containment — merge with the case-clause they resume.

### What is NOT in the rubric (do NOT apply)

- Cognitive-unity gate on parallel cola (empirically inert)
- Parallelism class adjudication (synonymous / antithetic / synthetic categorization)
- Genre anchors as primary licenses
- Aesthetic / colometric preferences
- Te'amim hierarchy as adjudicator (te'amim are performance anchors, not cognitive)

### Under-broken cases

A line containing two independent propositions where each half passes forward-closure + backward-containment independently → SPLIT.

### Default

**KEEP-AS-IS** unless the bidirectional test, restrictive-relative rule, or Hebrew-specific constraint affirmatively fires.

### Output format

Per verse:

```
## Verse [reference]

### Source state
[source lines as in file]

### Minimal-rubric state
[ATU-segmented lines]

### Per-line verdicts
- Line N: [KEEP-AS-IS / MERGE-PRIOR / MERGE-NEXT / SPLIT / AMBIGUOUS]
  Rationale: [one sentence citing the gate that fired]
```

CRITICAL: do NOT modify Hebrew characters or cantillation marks. Only regroup line breaks. Preserve maqqef, sof pasuq, vowels, and accents exactly.

End of chapter: write a summary block:

```
## Chapter summary
- Source content lines: N
- Total ATUs: M
- Net delta: +/- K
- Failure-mode classes that recurred: [list]
- AMBIGUOUS flags: [list verses]
```
