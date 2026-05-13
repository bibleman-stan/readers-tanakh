# Tanakh Colometry — Operating Canon

**Version:** 1.0 (2026-04-26 rewrite from scratch)
**Predecessor:** `archive/colometry-canon-stub-2026-04-25-retired-2026-04-26.md` — retained for reference, no longer authoritative. The predecessor's central commitment (te'amim-prior with override-warrant discipline) was demoted on the grounds that the te'amim are a Tiberian-Masoretic editorial overlay (~9th–10th c. CE), not a structural prior. This canon corrects that.

---

**What is this document?**

This canon mixes philosophy (the why) with operational rules (the how); section headers tell you which character predominates in each section.

- **Part I (The Method, §§0-2)** is the constitutional core: foundational methodology (§§0-1) and autonomy boundary (§2). Each section header discloses whether the section is mainly philosophical, mainly operational, or dual-natured.
- **Part II (Operating Rules, §§3-6)** carries the quick-reference rule table, Layer 1 pointers, rule detail, and the validator suite.
- **Part III (Process and Meta, §§7-8)** is change protocol and the chronological update log.

**Reader's guide:**

- **Editor making editorial decisions** (a Claude session working on the corpus): focus on §§3-6 and §7. Consult §§0-1 for grounding when proposing or evaluating rules.
- **Scholar reading the method as a published artifact**: focus on §§0-1 (foundational method + framework theory) and §7 (change protocol + defensibility).
- **Tracking how a decision evolved**: §8 carries the reasoning trail.

Some sections are dual-natured by design: §1 interleaves theoretical principles with their operational corollaries. **Treat bolded paragraphs as load-bearing** in those sections regardless of the surrounding prose's character. When revising philosophical prose in dual-natured sections, leave bolded paragraphs untouched unless the change is intentional and audited per §7.

---

# Part I — Method

*Everything in Part I is authoritative and current. Sections 0 through 2 contain the foundational method; §2 Autonomy Boundary governs when to apply vs. flag.*

## §0 Purpose and Stance

*Purpose: **mainly philosophical** — mission, intellectual origin, pragmatic stance, scope. Ground for §1. §0.1 Textual Posture is dual-natured: methodological commitment (philosophical) with operational scope enumeration.*

### Mission

**We are revealing atomic thought units (ATUs) — the discrete units a reader can process as a single complete thought.** Each line is a unit of meaning the reader can take in before needing the next. We are not revealing rhetorical parallelism (Lowth / Berlin parallelism analysis is a separate scholarly layer that may overlap with ours but is not our target). We are not mechanizing the te'amim or any other historical reading-tradition's chant structure. We are formatting the text so that any reader — novice or experienced — can take Scripture one atomic thought at a time.

### Origin

**Stan's premise:** *"Humans think, compose, and deconstruct (read and hear) in sense-lines — atomic thought-units that correspond to how ideas are generated, encoded, and recovered."* This is the working hypothesis driving the project.

**Intellectual lineage.** Royal Skousen's demonstration that the Book of Mormon could be reduced to sense-lines (*The Earliest Text*, 2009/2022) was the original trigger. Skousen's stated rationale in *The Earliest Text* was specific to the Book of Mormon: his sense-lines aim to convey "a dictated rather than a written text," approximating how the original translation might have sounded during Joseph Smith's dictation. Stan took the term as a starting point and expanded the concept beyond Skousen's specific rationale — applying it first to the Book of Mormon English text (sibling project), then to the Greek New Testament (sibling project), and from those experiments concluded the hypothesis applies to *any* text. **The Tanakh Reader is the analogical extension to biblical Hebrew** — what is true for the BoFM and the GNT is likely true for the Tanakh, and perhaps any text.

The methodology itself — three forces, structural justifications, merge-overrides, autonomy boundary, audit triggers — was not invented for Hebrew. It emerged from ~13 months of hands-on editorial experimentation across the BoFM corpus and the GNT corpus, was iteratively refined against ~50+ documented reverts and adversarial-audit catches, and converged on the architecture this canon now ports. The Tanakh project does not need to re-invent any of it. It does need to slot in Hebrew-specific material where the corpus diverges from its siblings — which is where Part II §5 and the Hebrew-specific sections of Part I §1 do their work.

### Method

**The mission is sense-driven. The method is syntax-constrained.** These are different things and they belong in different parts of this document.

The method leads with syntax (§1 "Syntax Forbids Splits") not because syntax is primary to the mission, but because **syntactic violation is fatal while sense ambiguity is recoverable within the permitted space.** A break that violates Hebrew syntax is always wrong no matter how strong the sense argument; a sense judgment inside the permitted space can be revisited by editorial review. Leading with syntax preserves the discipline that lets sense work — it doesn't demote the mission.

Novel rules can and do originate from sense-driven observation. The method accommodates this: sense proposes, syntax filters, the combination becomes a rule. But every break that survives to the corpus must be affirmable by Hebrew syntax. This is the non-negotiable operational floor.

### Pragmatic stance

This methodology is a set of conventions that reflect what we are trying to reveal. It is not derived from a cognitive theory; we are not claiming otherwise. It is also not derived from any particular Hebrew-poetics theory (Lowth / Kugel / Berlin / Dobbs-Allsopp). Later work may investigate why it works and how it relates to standing scholarship. For now, we operate it honestly as what it is: a consistently-applied editorial practice grounded in Hebrew syntax, tested against the corpus, and refined by validator sweeps and adversarial audits.

### Ground

Every rule here cites a Hebrew grammatical fact (anchored in standard reference grammars — Joüon-Muraoka, Waltke-O'Connor *Biblical Hebrew Syntax*, GKC — and in specific corpus instances). Rules that cannot be grounded in Hebrew syntax are editorial principles and labeled as such.

### Scope

This canon governs where lines break in the v2/heb editorial source files. It does not govern textual decisions (those follow the textual-posture statement at §0.1; the project does not adjudicate MT against versions), niqqud, te'amim glyph rendering, or layout beyond break positions. Scripts that touch the source text — `scripts/ingest_tahot.py`, `scripts/parse_teamim.py`, `scripts/build_books.py` — implement this canon's mechanical-rule subset; their output (`v0/prose/`, `v1/he-baseline/`, `books/`) is canon-compliant by construction within the limits of mechanical detectability.

### §0.1 Textual Posture

This is a **colometric reading edition based on a single textual tradition: the Tiberian Masoretic Text in its Leningrad recension**. It is not a critical edition and not an eclectic edition. The project does not adjudicate the Masoretic Text against ancient versions, and adopts no readings from them.

**In scope (as textual base):**

- The Westminster Leningrad Codex consonants, niqqud, and te'amim, as transmitted by current free digital editions (STEPBible TAHOT primary; OSHB and UXLC as transcription cross-checks)
- Internal Masoretic apparatus that the Masoretes themselves preserved: Ketiv/Qere, sebirin readings, the petucha/setuma divisions

**In scope (as reference, not adopted):**

- Miqra `al pi ha-Mesorah (Aleppo-tradition base) is vendored as tradition reference. Where Aleppo and Leningrad disagree, the project follows Leningrad. The presence of MAM in `research/` enables tradition-awareness and spot-checking, not textual eclecticism.

**Out of scope:**

- The Septuagint, Old Greek, and recensional traditions (Theodotion, Symmachus, Aquila, Lucianic)
- The Dead Sea Scrolls and pre-Masoretic Hebrew witnesses
- The Samaritan Pentateuch
- The Targums (Onqelos, Jonathan, Pseudo-Jonathan, Neofiti)
- The Peshitta and Vulgate
- BHS / BHQ / HUB / HBCE editorial apparatus and stichometry

These traditions and editions are scholarly resources of the highest importance, and the editorial decisions they document are not trivial. They are excluded here because the project's contribution is colometric — applying a sense-line methodology to a stable textual base — not text-critical. Re-litigating MT against versions is a different project, in another scholar's specialization, and would dilute this project's central methodological commitment. A future extension could add an opt-in comparator layer; it would not change the textual base of the rendered edition.

**Where MT itself preserves variants:**

- Ketiv/Qere — Qere primary, Ketiv accessible as hover/footnote (see §5 Rule H6).
- Sebirin — printed reading is the base; the sebirin alternative is preserved as marginal note where the Masorah records it.
- Tiqqunei sopherim and itture sopherim — the Masorah's own annotations are preserved as marginal notes; the printed text follows the Masoretic form.

### §0.2 Governing Values — The Three C's

The canon and the corpus are evaluated against three governing values. These are decision criteria for canon-level revisions, spec changes, and cascade adoption — invoked when methodological tension surfaces or when an editorial judgment requires explicit ranking of priorities.

**Clarity.** Each rule, principle, and operational test is articulated precisely enough that a reader can apply it without consulting the editor. Tests are named so editors and validators cite them by name. Rationale (the WHY) is documented alongside mechanics (the HOW). Ambiguity in a rule is a defect to fix, not a feature to preserve.

**Consistency.** The corpus matches the canon. The canon matches itself (no internal contradictions between rules, principles, and tests). When canon and corpus diverge, either the corpus is updated (cascade) or the canon is revised — the divergence is not allowed to persist as a known unresolved tension.

**Comprehensiveness.** Canon revisions apply across the full corpus, not just the verse that surfaced the issue. When a methodological insight changes one rule, the implications across the related rules and across the affected corpus are worked out and applied. Forward-only changes (where the rule changes but historical applications are not revisited) are a Category-B exception requiring explicit §7 audit, not a default mode.

**Application.** When a canon revision is proposed, the proposal is evaluated against all three values. A revision that loses on consistency or comprehensiveness while gaining on clarity is generally not adopted; a revision that loses on clarity while gaining on the others is also generally not adopted. The 3 C's are co-equal — no single value dominates the others.

**WHY:** Stated by Stan during the 2026-05-02 Path 1 deliberation: "we need clarity, consistency, and comprehensiveness." Codified here so that future canon decisions invoke the framework explicitly rather than re-deriving it ad hoc. The 3 C's themselves are a methodological commitment, not an operational rule — they shape how canon evolves rather than how the corpus is broken into cola.

**HOW WE KNOW:** Stan-articulation in the Path 1 deliberation (2026-05-02 session-notes archive); pattern observed across prior canon decisions where the same value-trio implicitly governed (te'amim demotion 2026-04-26, tier collapse 2026-04-27, no-permission-loop discipline 2026-04-29).

### §0.2.1 Operationalizing Consistency — Validator Adoption Discipline

A validator emitting a STRONG finding does not, on its own, update the corpus. Three accumulation paths leave validator-state and corpus-state drifting apart silently:

**Adoption-without-cascade.** When a new STRONG arm is added to an adopted validator (or a new validator enters `ADOPTED_VALIDATORS`), its findings sit in the queue until `apply_validators --all-books --diff-apply` is run. `refresh_book.py`'s base-mode `apply_validators` preserves any v2/heb chapter that has diverged from v1 + adopted_validators (the PRESERVE branch), so newly-emitting STRONG findings cannot reach already-edited chapters via base-mode at all. PRESERVE is asymmetric — it protects hand-edits but blocks retroactive cascade.

**Run-without-adoption.** `ADOPTED_VALIDATORS` and `ALL_VALIDATORS` in `scripts/apply_validators.py` are separate registries. A validator marked adopted but missing from `ALL_VALIDATORS` is never invoked — its STRONG findings are invisible to the strong-queue aggregator. Both registries must be updated in lockstep when adopting a new validator (or the registries should be unified; deferred to infrastructure work).

**REVIEW-by-default for tight patterns.** A validator that emits `REVIEW-REQUIRED` for an unambiguous tight pattern leaves that pattern un-applied indefinitely — no `apply_validators` path picks up REVIEW findings. Tight patterns with high-confidence guards (closed-list discriminants, tag-confirmed agreement checks) should be promoted to `STRONG-MERGE-CANDIDATE` / `STRONG-SPLIT-CANDIDATE` so the mechanical cascade reaches them. Per the standing "mechanical apply, not review queue" discipline, REVIEW is reserved for genuinely ambiguous edges, not as a default safety setting.

**Discipline.** Every cycle that adds a new STRONG arm, new STRONG-emitting validator, or promotes REVIEW→STRONG MUST be followed by `apply_validators --all-books --diff-apply` in the same commit chain. Periodic re-cascade (every several sessions) catches drift from registry-mismatch fixes, accumulated PRESERVE-state chapters, and adopted validators that have never been retroactively applied. Without this discipline, the corpus accumulates known-but-unapplied findings — consistency erodes silently and only surfaces under spot-check.

**Gap-detection heuristic.** When a validator's STRONG-count rises but the corpus shows no corresponding line-count change for the same period, suspect drift. Diagnostic: dry-run `apply_validators --all-books --diff-apply`; non-zero "would-apply" count = drift to fix.

**WHY:** Stan's spot-check on Jer 31:33 (וְהֵ֖מָּה orphaned from יִֽהְיוּ־לִי לְעָם) surfaced what was actually a corpus-wide gap from accumulated under-cascading: a validator emitted REVIEW-REQUIRED for the pattern; promotion to STRONG-MERGE-CANDIDATE silently failed to apply because the validator was missing from `ALL_VALIDATORS`; cluster-cascade work was partially lost when a dispatched agent ran `git reset --hard HEAD`; and several adopted validators had findings that had never reached pre-existing PRESERVE chapters. The single visible line was the tip; the gap was structural. Codifying the discipline makes the consistency value enforceable rather than aspirational.

**HOW WE KNOW:** 2026-05-04 session — Jer 31:33 spot-check → three drift mechanisms diagnosed → fixes landed (M4 STRONG arm + ALL_VALIDATORS registry coupling + corpus-wide cascade). Cross-session pattern: every prior canon-revision session has had a similar "rule landed but corpus didn't catch up" footnote in carry-forwards (Path 1 H5b retroactive cascade 2026-05-03 was the largest example: 2,034 splits applied retroactively after the rule was already settled).

---

## §1 The Framework — Proposition-First, Syntax-Constrained

*Purpose: **dual-natured** — generative principle, structural justifications, merge-overrides, decision procedure (operational), and the philosophical grounding for those mechanics (Container-Not-Originator, Imposing vs. Revealing, te'amim demotion). Bolded paragraphs throughout are load-bearing operational content embedded in philosophical framing.*

The framework is: **each proposition splits by default, unless syntax forbids.** Substantive adjuncts (slot-fillers in narrative frames) count as atomic thought units and also earn their own lines. Image sharpens ambiguous cases. (Equivalently at the operational level: at any candidate boundary the default is merge — see §1 Decision Procedure step 1 — and a split is licensed only when a proposition or structural-justification boundary is identified. The two phrasings are scope-distinct: "splits by default" generates the proposition-level inventory; "merge by default" is the per-location heuristic. Same procedure, different vantage points.)

### The Generative Principle

**Each proposition splits by default.** A proposition is the atomic thought-unit — a complete predication (subject + finite verb + complement; or in Hebrew, also the verbless clause with its predicate+subject) that the reader can process as a single cognitive bite. Propositions drive line breaks. There is no positive requirement to break beyond this; there is no positive requirement to merge beyond this. The question at every candidate location is: *is this a proposition boundary?*

"Proposition" also includes the five structural-justification cases (below) — non-predicated units that function as atomic thoughts via formal-structural recoverability. These are the only non-strict-predication units that qualify.

**Hebrew anchor inventory.** A line carries an atomic thought when at least one of these is present:
- A finite verb (qatal, yiqtol, wayyiqtol, weqatal, jussive, cohortative, imperative)
- An infinitive (construct לְ + infinitive, or absolute used as predicate)
- A participle standing as predicate (with explicit or implicit copula; the Hebrew predicative participle is a primary anchor type, not a peripheral one)
- A verbless clause with explicit subject + predicate (Hebrew verbless clauses ARE atomic thoughts; do not import the Greek-canon "every line needs a verb" instinct — Hebrew syntax routinely predicates without an overt copula)
- A substantive head independently predicated on the line (rare; typically a slot-filler under structural justification 5)

### Syntax Forbids Splits — three closed-list ways

Syntax does not generate breaks. Syntax only vetoes them. A split that proposition-first would generate is forbidden when one of these three applies:

1. **Layer 1 mid-phrase prohibitions.** Splits mid-predication, mid-phrase, or mid-lexical-unit — line-final conjunction (וְ, וַ-, אוֹ, אֲבָל), prepositional prefix (מ/ב/כ/ל) stranded from object, definite article הַ stranded from noun, maqqef-group split, vocative unit split, etc. See [`data/syntax-reference/hebrew-break-legality.md`](../../data/syntax-reference/hebrew-break-legality.md) §1 Break Legality Reference.

2. **Layer 3 complement integrity.** When the matrix verb's or adjective's valence is unsatisfied without its clausal complement — e.g., אָמַר ... כִּי / לֵאמֹר + speech content; יָדַע ... כִּי + content; צִוָּה ... אֲשֶׁר + complement — the matrix is grammatically incomplete on its own; the complement must merge unless one of the long-complement exceptions in §5 Rule H7 fires.

3. **Layer 3 formula integrity.** Lexicalized multi-word frames function as single units — וַיְהִי + temporal protasis, כֹּה אָמַר יְהוָה, נְאֻם־יְהוָה, the divine-name compounds (יְהוָה צְבָאוֹת, יְהוָה אֱלֹהִים), the perpetual-qere תֵּת and its frozen forms. Never break inside the frame.

These are the "unless" clauses of "split each proposition unless syntax forbids."

### Image Sharpens Ambiguous Proposition Boundaries

**Single image / camera angle.** When proposition-first is ambiguous (e.g., a short circumstantial clause that could read as continuation of the prior frame or as its own frame), ask: does the mind's eye reposition between candidate frames? Camera-angle shift → SPLIT. No shift → MERGE. This is a tiebreaker for ambiguous cases, not a primary generator.

### The Five Structural Justifications (Closed List)

Non-predicated units that function as atomic thoughts via formal-structural recoverability. The reader can reconstruct "who did what" because formal markers in the text make the missing predicate recoverable.

1. **Formally-marked parallel series.** Members connected by formal markers (וְ chains, polysyndetic וְ ... וְ ... וְ, correlative גַּם ... גַּם, anaphoric repeated frames such as Pss 119 stanza markers, Lev 11 dietary catalog frames, Deut 27 curse frames, Prophetic woe-formula chains) where the shared predicate is recoverable from the parallel structure. Each member earns its own beat.

    **Compound list break signals.** In a compound list governed by one preposition or verb, bare *"and [noun]"* items are compound objects and stay merged. A break inside a compound list is justified only when one of these signals is present:
    1. **Elided auxiliary / elided verb** — each item is an implied predication
    2. **Possessive restart** — change of pronominal suffix possessor (e.g., בְּנוֹ to בִּתָּם), or addition of a possessive suffix where the prior items had none. *Repeated identical possessive* (e.g., a king-list with each name + bound suffix) is formulaic and does NOT alone justify stacking.
    3. **Demonstrative restart** — *"and that/this/these"* (וְזֶה, וְהִיא, וְאֵלֶּה) signals a new specified noun phrase
    4. **Relative clause attached** — *"which/who"* (אֲשֶׁר + clause) adds a predication to the item

    Without one of these signals, bare *"and [noun]"* items merge. The possessive-restart vs. repeated-possessive distinction is corpus-critical for genealogies (1 Chr 1–9, Gen 5, Gen 11): king-lists and inheritance-lists frequently trigger false-positive stacking without this test.

    **M1 bonded-pair precedence inside compound lists.** When a compound-list item is itself an M1 bonded pair (hendiadys / merism / cognate pair — *חֶסֶד וֶאֱמֶת*, *שָׁמַיִם וָאָרֶץ*, *יוֹמָם וָלָיְלָה*, *שָׂרִים וְשׁוֹפְטִים*), the bonded pair is the item — the pair treats as one atomic unit within the larger series. None of the four compound-list break signals reaches inside a bonded pair to split it.

2. **Portrait accumulation.** A set of attributes building one mental picture, sharing a copular or attributive frame from context (e.g., the divine attributes formula at Exod 34:6, the description of God in Deut 10:17 *הָאֵל הַגָּדֹל הַגִּבֹּר וְהַנּוֹרָא*). Applies only when the stack IS the portrait, not when it is a catalogue.

3. **Speech-act announcement.** Complete communicative predication introducing direct discourse. Hebrew has rich variety here:
    - **וַיֹּאמֶר X לֵאמֹר** — speech-intro frame, typically own-line-then-content (see §5 Rule H5 / H5b for the framing-and-announcement defaults).
    - **כֹּה אָמַר יְהוָה** — prophetic messenger formula, own line.
    - **נְאֻם־יְהוָה** — oracle attribution, own line whether sentence-initial, mid-utterance (parenthetical), or sentence-final (signature).
    - **לֵאמֹר alone** — the bare infinitive complementizer is a speech-act-announcement marker, gets its own line at the point of speech-onset.

    Announcement and quoted content are separate cognitive frames.

4. **Classical commata.** Short fragmentary utterances carrying full communicative weight (אַשְׁרֵי-formulas; קָדוֹשׁ קָדוֹשׁ קָדוֹשׁ at Isa 6:3; אוֹי-formulas; brief imperatives like שְׁמַע, רְאֵה, הִנֵּה used asyndetically). Typically 1–3 prosodic words; brevity + isolation = deliberate emphasis. The Tanakh has its own inventory of these (Hebrew name to be coined as the canon matures); for now, "classical commata" is the placeholder term ported from sibling projects.

5. **Substantive adjunct as own focus.** A fronted or trailing adjunct (temporal PP, locative PP, causal PP, purpose clause, casus pendens / left-dislocation, circumstantial vav-clause carrying scene-setting weight) that (a) is grammatically peripheral to the matrix predication's core truth AND (b) carries substantial content — enough that the reader processes it as an independent focus rather than background — earns its own line.

    **Hebrew grammatical grounding:** Hebrew treats peripheral adjuncts as syntactically detachable — they can front, trail, or be omitted without breaking the matrix. Casus pendens / topicalization (Topic-fronted NP + resumptive pronoun in the main clause) is the sharpest case; it is universally an own-focus structure (Joüon-Muraoka §156). Circumstantial clauses (vav + non-verb-initial clause indicating background or simultaneous action) are weaker but still detachable.

    **Test:** can the adjunct be paraphrased as its own "when/where/why/how" clause answering a question the matrix leaves open? If yes, it is a slot-filler and earns its own line.

    **Pattern: wayehi protasis as Front-End Frame (FEF).** The Hebrew construction *וַיְהִי* + temporal/circumstantial protasis + main clause is the canonical FEF: the *wayehi* + protasis frames the event, then the main clause resolves. The protasis is held together as one atomic temporal frame even when long; the main clause starts a new line. Jonah 1:1 *וַיְהִי דְבַר־יְהוָה אֶל־יוֹנָה בֶן־אֲמִתַּי לֵאמֹר* is the smallest case — even at five orthographic words the protasis is FEF-shaped and earns its own line, with the speech content (verse 2) starting fresh. Long FEFs (Gen 39:7's whole-verse protasis chain; many Lukan-style narrative openers) hold the protasis together regardless of length.

    **Pattern: prophetic oracle headers and signatures.** *כֹּה אָמַר יְהוָה ... אֲדֹנָי* opening formulas and *נְאֻם־יְהוָה* signatures are substantive adjuncts in the prophetic register; each gets its own line.

    **Exclusion: degree quantifiers.** Short PPs that modify the *degree* of a predicate (בִּמְעַט, מְאֹד as bare adverbs) do NOT pass the slot-paraphrase test — they modify how-much, not when/where/why. They are predicate modifiers, not slot-fillers.

The list is extensible only by worked example + adversarial validation. A proposed sixth justification must demonstrate (a) that it is a genuinely distinct instance of the same generating principle — formal structure in the text enables cognitive recovery of the full predication, or substantive content independently warrants own focus — and (b) that it survives an adversarial challenge.

### The Four Merge-Override Conditions (Closed List)

**Symmetric counterpart to structural justifications.** Where structural justifications describe cases where the default (merge under propositions-first) is overridden to produce a split, merge-overrides describe cases where an apparent split-trigger is itself overridden — returning the members to one line. The default is still merge; these overrides catch cases where naive application of split-triggers would fragment a unit that should stay whole.

**Generating principle:** Even when a line looks like it could pass the structural prong (formal markers present), merge wins when the resulting fragments would fail on more basic grounds — the chunk is not actually two propositions, the clause nucleus would be ruptured, the fragment cannot stand as atomic thought, or the cognitive prong itself fails.

**Strict-application caveat — rejection ≠ split license.** When a merge-override (M1–M4) does NOT apply to a given case, that does not automatically mean the case should split. It just means THAT override doesn't fire. The default behavior is still determined by the generative principle (proposition-first) and by other applicable rules (other merge-overrides, syntactic vetoes, structural justifications). Do not reason: "M1 rejected → must split." Reason instead: "M1 rejected → apply remaining analysis." Each merge-override's absence is silent, not authorizing.

The list is extensible only by worked example + adversarial validation, same rule as the structural justifications.

#### M1. Bonded Pair (hendiadys / merism / cognate pair)

**Definition:** N=2 coordinate members joined by וְ where the pair functions as a single unified hendiadys, merism, or bonded rhetorical image — not two independent propositions. Even under formal וְ-linkage (which would normally trigger structural justification 1), if the pair is bonded, merge.

**Test:** Can the two members be paraphrased as a single unified image or hendiadys? Do they carry shared rhetorical weight without independent predicative force?

**Hebrew canonical cases:**
- *חֶסֶד וֶאֱמֶת* (covenant loyalty + truthfulness as a unified divine attribute pair) — hendiadys
- *שָׁמַיִם וָאָרֶץ* (heaven and earth as cosmic pair) — merism
- *הַטּוֹב וְהָרָע* (good and evil as moral totality) — merism
- *יוֹמָם וָלָיְלָה* (day and night as temporal totality) — merism
- *שָׂרִים וְשׁוֹפְטִים* (officials and judges as joint civic class) — bonded pair
- *אֱמֶת וּמִשְׁפָּט* (truth and justice as paired civic virtue) — bonded
- *זָכָר וּנְקֵבָה* (male and female as anthropological pair) — merism
- *אַל־תַּסְתֵּר פָּנֶיךָ מִמֶּנִּי* — internal pair *פָּנֶיךָ מִמֶּנִּי* not bonded; counterexample for the test

**Tie-breaker when M1 and structural justification 1 both seem to apply (N=2 formally-marked pair):**
- If each member has a distinct non-synonymous finite verb → structural justification 1 wins (SPLIT).
- If the two members are semantically synonymous, cognate, or intensification variants → M1 wins (MERGE).
- If the members are bonded-pair nouns/adjectives (not verbs) with unified rhetorical weight → M1 wins (MERGE).

This tie-breaker is the canonical specific case of the cross-cutting **N=2 Adjudication Principle** (see below). The same merge-vs-split logic applies wherever a merge-rule and structural justification 1 both fire at N=2.

**Asymmetric-modifier sub-clause.** When an M1-candidate bonded pair has one member carrying a PP modifier or relative clause the other lacks (*חֶסֶד וֶאֱמֶת לִבְרִיתוֹ*, *שָׁמַיִם וָאָרֶץ אֲשֶׁר עָשָׂה*), M1 still wins → MERGE if the modifier attaches semantically to the pair AS A UNIT (answering "in/on what?" where the modifier's referent is the joint object of both members). SPLIT only if the modifier scopes over only one member to the exclusion of the other, producing genuinely distinct predicative force.

**Grammatical grounding:** Joüon-Muraoka §177 on hendiadys; Waltke-O'Connor §4.6.5 on coordinate noun-pairs as merism.

#### M2. Verb-Object Clause-Nucleus Bond

**Definition:** A finite verb and its direct object (or obligatory complement) on short phrases stay on one line, even under split-trigger pressure. The clause nucleus is the minimal atomic predication and cannot be fragmented.

**Test:** Would splitting strand the verb without its complement, or strand the object without its governor? If yes, MERGE.

**Hebrew specifics:**
- Verb + direct-object marker אֵת + NP: never split between verb and אֵת+NP.
- Verb + pronominal suffix (object incorporated morphologically): obviously never breakable.
- Verb + obligatory PP complement (שָׁמַע ל, נָשַׂא עֵינַיִם אֶל, פָּנָה אֶל): never split between verb and PP.

#### M3. Bare-Governor Indivisibility

**Definition:** A head word — participial adjective standing alone (גָּדוֹל, רַב, מָלֵא + pending complement), governing participle without complement (יוֹדֵעַ, אוֹמֵר, רוֹאֶה without object/clause), discourse particle standing alone (וְעַתָּה, לָכֵן, עַל־כֵּן without following content), or bare construct head awaiting *nomen rectum* — cannot stand on its own line without at least one complement, object, or dependent. The bare governor fails the atomic-thought test because it is grammatical machinery awaiting content, not a complete predication.

**Test:** Can the isolated head-word be read as a complete thought? Or does the reader's attention dangle forward, expecting completion on the next line?

**Hebrew canonical cases:**
- Bare construct head: דְּבַר־ alone, בֵּית־ alone, קוֹל alone awaiting genitive — fails M3.
- Bare governing participle: אוֹמֵר alone without speech complement; יוֹדֵעַ alone without כִּי-clause — fails M3.
- Bare discourse particle: וְעַתָּה alone, לָכֵן alone, עַל־כֵּן alone, הִנֵּה alone — fails M3.

**Contrast with speech-intro (structural justification 3):** Finite speech-act formulas (וַיֹּאמֶר אֵלָיו לֵאמֹר as a complete frame; כֹּה אָמַר יְהוָה as a complete prophetic-messenger predication) ARE complete speech-act predications — the speech act itself is the content. Bare governing participles (אֹמֵר without speech) are not; they await content.

#### M4. Fragmented Atomic Thought-Unit

**Definition:** If splitting a line would produce fragments that individually fail the atomic-thought test, merge. This is the inverse of the cognitive prong: the cognitive prong requires each resulting chunk to be its own atomic thought for a split to proceed; if any resulting fragment fails that test, the split is blocked.

**Test:** Read each proposed resulting line aloud as a standalone unit. Does it constitute one focused-attention chunk with bounded information? If any resulting line fails, the split is over-fragmenting.

**Scope discipline — prospective not retroactive.** M4 fires ONLY when evaluating a PROPOSED split. It is evaluated by reading each of the two proposed fragments as standalone units; if either fails atomic-thought, the proposed split is blocked → MERGE. **M4 is NOT a retrospective merge generator.** When an existing split shows both fragments individually passing atomic-thought, M4 does not fire, even if the two events are causally, narratively, or rhetorically linked. "Narrative completion" and "atomic-thought failure" are different tests; conflating them is a documented sibling-project failure mode (BoFM 2026-04-22 reverts of Alma 47:24, 1 Ne 5:4, Ether 14:29). The operational rule: ask *"does THIS line, alone, constitute one focused-attention chunk?"* — not *"would merging produce a more complete narrative beat?"* The former fires M4 when appropriate; the latter is aesthetic reasoning outside M4's scope.

**Precedence over structural justifications.** M4 fires ONLY when splitting produces a fragment that **fails** the atomic-thought test. A fragment that PASSES atomic-thought via another structural justification's cognitive prong does NOT fail. Specifically:
- **Formally-marked parallel series (justification 1):** members of a 3+ member series pass cognitive-prong via shared-predicate recovery. M4 does NOT fire on series members.
- **Substantive adjunct (justification 5):** substantial adjuncts (FEF wayehi protases, prophetic oracle headers, casus pendens phrases) earn own lines. M4 does NOT fire on these.

### Summary: the four forces

| Force | Direction | Role |
|-------|-----------|------|
| Propositions (+ 5 structural justifications, including substantive adjunct) | GENERATIVE | Default split at every proposition or justified non-proposition boundary |
| Syntax (Layer 1 + complement integrity + formula integrity) | SUBTRACTIVE | Forbids some splits the generative principle would produce |
| Merge-overrides (M1–M4) | SUBTRACTIVE | Block split-triggers when resulting fragments fail on more basic grounds |
| Image (camera angle) | DIAGNOSTIC | Sharpens ambiguous boundaries |

### Container-Not-Originator (Philosophical Grounding)

**The atomic thought is the primary, originating reality.** It is what the author wants to say, prior to and independent of any particular language. Hebrew, Aramaic, Greek, English, and Chinese speakers all compose in thought units. The atomic-thought target is *language-invariant*.

**Hebrew syntax is the container, not the originator.** Every atomic thought is *always already* shaped by the grammatical framework of the language it was born in — there is no unclothed "pure thought" underneath waiting to be extracted. The container constrains: the biblical authors could not express their thoughts without choosing Hebrew syntactic patterns (verb-subject-object as the unmarked clause type, the construct chain for genitival relations, the *wayyiqtol*-chain narrative engine, the qatal/yiqtol/participle aspectual contrast), and those patterns imposed fixed structural commitments. But the container does not *originate* the thought. The thought exists first and fits itself into whatever vessel is available.

This is the classical distinction between **logos endiathetos** (the thought in the mind) and **logos prophorikos** (the thought as uttered). Colometric recovery targets the endiathetos through the prophorikos because the prophorikos is all we have.

**Consequences for the framework:**

1. **Propositions (atomic thoughts) are the generative force because they are what we are recovering.**
2. **Hebrew syntax is the subtractive force — the evidence surface through which propositions become visible in this particular language, and simultaneously the floor below which no line can legally sit.** Syntax both reveals where propositions end (thought-marking syntax) and constrains where breaks are legal (Layer 1 break-legality, complement integrity, formula integrity).
3. **Cross-linguistic invariance is preserved.** The atomic thought-units in Genesis are the same units whether read in Hebrew, Greek (LXX), or English. Only the container changes. We are not imposing Hebrew syntax on English readers; we are recovering the shape the Hebrew author's thoughts actually had when composed.

### Imposing vs. Revealing — Scope Discipline

**Line breaks follow structure that already exists in the text. If a rule produces a line that does not match the text's inherent structure, the rule is wrong.**

- We do not impose visual structure that the grammar does not directly support.
- We do not construct grammatical categories to justify editorial instincts.
- If a break cannot be named in standard Hebrew grammatical terms, it is an editorial decision — which is fine, but should be labeled honestly (Category B/C per §2).
- If a proposed rule consistently produces lines that don't sound like the text, the rule is imposing rather than revealing and is rejected.

**This is a presentational layer, not an analytical one.** Our job is to render the text so its grammatical and cognitive structure is visible at the line level. What scholars do on top of that — identify chiasms, mark rhetorical figures, perform parallelism analysis (Lowth / Berlin / Kugel / Dobbs-Allsopp), perform discourse analysis, write commentary — is downstream work that our edition *enables* but does not perform.

**The boundary test:** if a feature requires *interpretation* of authorial intent or rhetorical strategy to detect, it is out of scope. If it can be identified by Hebrew grammar alone (morphology, syntactic position, lexical markers, the te'amim as evidence), it is in scope.

**Corollary — the "reaching-for-split" warning.** When the grammatical case for a split is borderline and you find yourself reaching for chiastic-structure, parallelism-display, prosodic-emphasis, theological-weight, doctrinal-stakes, narrative-climax, pastoral-force, soteriological-significance, or any analogous non-grammatical category as a tiebreaker, **that is the signal that scope creep is happening.** The scope-disciplined default in a borderline case is to keep the grammatical constituent intact — i.e., **prefer merge to split** when the grammar is ambiguous.

This is the "rhetoric-bandwagon" failure mode — the highest predictable risk for the Tanakh project specifically, given Hebrew's deep scholarly literature on parallelism (Lowth 1753; Kugel 1981; Berlin 1985; Dobbs-Allsopp 2015), chiasm (extensive), inclusio, merism, and other rhetorical figures. Importing any of those scholarly categories as a *mechanical* line-break rule is the predictable catastrophic failure. They are evidence, not authority.

**The fronting paradox — marked Hebrew word order argues for MERGE, not split.** Hebrew's unmarked clause order is V-S-O (verb-initial). When a constituent is fronted (subject before verb, object before verb, casus pendens, topic-fronted PP), the natural editorial instinct is to split at the fronted element as a way of "visualizing the emphasis." **This instinct is wrong for tight bound constituents.** The rhetorical effect of fronting depends on the grammatical unity *staying intact*. The marked arrangement is felt as emphatic precisely because the hearer processes the fronted element in a non-default position *within a single breath unit*. Splitting at the fronted-element boundary mechanizes the emphasis — it imposes a pause that was not in the original oral delivery — and paradoxically *diminishes* the rhetorical force.

(Casus pendens / left-dislocation is the *exception* — it is grammatically detached by the resumptive pronoun in the main clause, which is structural justification 5 territory, not a tight-fronting case. The rule applies to fronted-but-grammatically-bound constituents like topic-fronted objects without resumption.)

### The Te'amim Play No Role in Editorial Decisions

The Tiberian **te'amim** (cantillation accents) are a 9th–10th c. CE Masoretic editorial overlay marking cantillation melody, word stress, and phrase-pause boundaries for liturgical chant. They are preserved in the printed text for textual fidelity. They are not consulted in editorial decisions and they are not cited in defensibility-capture. The three forces (atomic thought, single image, Hebrew syntax) carry the entire load.

**Operational uses that survive this retirement:**
- `scripts/parse_teamim.py` generated the v1-he-baseline (`data/text-files/v1/he-baseline/`) as a one-time mechanical starting draft for the v2/heb hand-editing pass. The v1 files exist as historical artifact; they are not "evidence" in the editorial sense.
- The Sifrei Emet vs prose corpus partition (used for cluster-cascade routing per CLAUDE.md cluster-5 definition) is a book/chapter-membership fact, not a runtime te'amim check.
- Sof pasuq (`׃`, U+05C3) remains usable as the structural verse-end punctuation marker (it is not a te'amim glyph proper, U+0591–U+05AF).

**Validator-architecture corollary.** Validators (Layer 2) must trigger on Hebrew morpho-syntactic patterns — lexical class, morphology, syntactic position, formula presence, prefix class, agreement features. Validators must NEVER trigger on te'amim glyph placement or te'amim-derived positional concepts (atnach-domain membership, zaqef-tier hierarchy, paseq presence, etc.). **Diagnostic test:** if the validator wouldn't fire on text stripped of te'amim, its trigger is te'amim-dependent and the architecture is wrong.

**WHY this matters in execution.** The previous canon framed te'amim as "evidence not authority." That consultative status kept producing scope-slippage: every few sessions, a validator-design proposal would attempt to "use the v1-baseline as a starting candidate set" or "demote te'amim by merging across them" — both of which operationally promote the te'amim as the primary candidate-surfacing signal. The 2026-05-05 v1-aware S8 design failed for exactly this reason (proposed trigger "v1 cola count > v2 cola count" defines the universe of candidates by te'amim placement). Removing the consultative role closes the slippage surface entirely.

**Provenance:** Stan flagged the validator-architecture corollary 2026-04-28 against a proposed `validate_tifcha_servant.py`. The full consultative-role retirement was authorized 2026-05-05 after the v1-aware S8 design hit the same corollary. See §8 entry for the audit evidence.

### Punctuation, Te'amim Glyphs, and the Masoretic Apparatus Are Not Break Signals

The Masoretic apparatus — niqqud, te'amim, Ketiv/Qere markings, sof pasuq, paseq, soph pasuq, the maqqef — is preserved in the printed text for fidelity. Of these:

- **Te'amim** play no role in editorial decisions per the section above. Their glyphs are preserved in the text; they are stripped for morphological matching; they are not cited in defensibility-capture.
- **Sof pasuq (`׃`)** is the verse-end mark, structurally distinct from te'amim glyphs proper (U+05C3 vs U+0591–U+05AF). It is the *editorial* boundary between verses, imposed by the Masoretic apparatus on top of compositional structure that often crosses it. Do not treat sof pasuq as a forced line break, but verse-end detection (e.g., for guard predicates that need to know "this is the last token of the verse") is a structural fact and may be used.
- **Paseq (`׀`)** is a post-Masoretic disjunctive added in the medieval period. Its function is contested. Treat as evidence (it usually marks something the Masoretes wanted to disjoin) but not as authority.
- **Maqqef (`־`)** joins two-to-four orthographic words into a single prosodic unit. It IS a break-legality fact (do not break inside a maqqef-group — Layer 1, see §5 Rule H1). It is not by itself a break-license — a maqqef-group ending coincides with a prosodic-word boundary, but most prosodic-word boundaries are not break candidates.
- **Niqqud** affects pronunciation, not line breaks. Ignore for break decisions.

### Versification Is Not a Break Signal

Hebrew chapter divisions were imposed by Stephen Langton (~1227 CE, working from the Latin Vulgate) and adopted into Hebrew Bibles by the Bomberg / Ben Hayyim editions of the 16th century. Hebrew verse divisions are older (Masoretic, marked by sof pasuq) but were pre-Masoretic chant-units, not compositional sense-units. Both are editorial overlays relative to compositional structure. **Neither overrides grammatical continuity.**

The cross-verse continuity convention (ported from sibling GNT canon §3.17 and BoFM canon §1) applies: when a single atomic thought crosses a verse boundary, the sense-line stays intact in the *earlier* verse's block, with a superscript verse-number marker preserving the versification reference. See §5 Rule H10 for the operational mechanism.

**Hebrew vs. Christian versification.** Hebrew verse numbering and Christian (KJV-tradition) verse numbering disagree in roughly 40+ cases (Joel 2:28–32 = MT 3:1–5; Mal 3:19–24 = MT 4:1–6; Ps superscriptions counted as v.1 in MT but not in KJV; Jonah 1:17 = MT 2:1; etc.). The project follows **Hebrew versification primary** (per textual posture §0.1), and a crosswalk JSON (`data/text-files/v0/prose/<book>/<book>-crosswalk.json`) records the mapping for citation lookup.

### Petucha / Setuma Are Evidence, Not Authority

The pre-Masoretic paragraph divisions — **petucha** (open: full-line gap) and **setuma** (closed: gap mid-line) — are preserved in TAHOT and OSHB. They predate the te'amim and reflect a compositional or liturgical tradition older than the Tiberian Masoretic apparatus. They are **the most important single evidence about pre-Masoretic structural divisions above the colon level**, and the canon treats them with corresponding weight.

But they are not authority either. Aleppo, Leningrad, MAM, and BHS disagree on individual cases (Yeivin 1980 §§81–88; Tov 2012). When sources disagree, the project follows Leningrad (per textual posture §0.1).

**Operational role.** Petucha/setuma serve as evidence for major paragraph-level breaks above the colon level. They corroborate atomic-thought analysis at the paragraph scale. They do not by themselves license cola-level breaks within a paragraph; cola-level breaks follow the framework above (atomic thought, structural justifications, merge-overrides, syntax veto). Web-app rendering reflects petucha/setuma as paragraph breaks (blank line for petucha; indented break for setuma); section-level navigation uses petucha boundaries as primary structural cues.

### Parallelism Is Not a Structural Prior

Hebrew parallelism is real. Lowth (1753) was right that biblical poetry is built on parallelistic structures; the question modern scholarship contests is what *kind* of structure parallelism is, not whether it exists. The 250-year debate (Lowth's three-fold synonymous/antithetic/synthetic taxonomy → Kugel 1981's "there is no such thing as parallelism, only seconding — A, and what's more, B" → Berlin 1985's multi-dimensional analysis across phonological/grammatical/lexical levels → Dobbs-Allsopp 2015's free-verse-with-lineation framing) is real, ongoing, and substantial.

**The project does not take a position in that debate.** Parallelism is not a structural prior for line breaks. It is **evidence**, on the same epistemic footing as petucha/setuma — informative about how the author structured a thought, never authoritative for where the editor breaks a line.

Line breaks reveal atomic thoughts; parallelism is a phenomenon the atomic-thought analysis sometimes encounters (especially in Sifrei Emet) but never a generator of breaks in its own right. Importing Lowth's three-fold scheme as a mechanical rule would be the canonical rhetoric-bandwagon failure mode (§1 Imposing vs. Revealing): a scholarly category becoming a line-break authority. Importing Kugel's anti-parallelism stance as a mechanical rule would be the same failure in opposite direction.

**Operational implications:**

- **In Sifrei Emet** (Pss/Prov/poetic Job): the v1-he-baseline (parse_teamim.py output) was the editor's starting draft. v2/heb hand-editing applies the three forces; divergence from v1 is informative but not a defect — same status as in prose.
- **The project does not display parallelism via line layout.** When parallel members appear on parallel lines in the rendered edition, they appear so because each member is itself an atomic thought (structural justification 1), NOT because we are typesetting parallelism for visual effect. This is the anti-Lowth posture from the sibling BoFM canon (which named it explicitly: "split-dominant repeated-frame layout IS the parallelism-display posture the project's stance opposes") applied to the original Hebrew.
- **Berlin's multi-dimensional analysis is a useful diagnostic** when atomic-thought analysis is borderline — when phonological + grammatical + lexical parallelism converge on a structure the v1-baseline did not register, that's high-confidence evidence for an override. But Berlin is an evidence-application tool under criterion #1, not a baseline framework.
- **Macula constituent trees + frame annotations** (lowfat XML, see §0 source-stack) are the structural diagnostic when parallelism-detection is needed — morpho-syntactic subject/verb/role symmetry across a candidate boundary, queried mechanically. This is the canon-aligned alternative to "look at the te'amim."

**Why this matters as a load-bearing canon section.** The parallelism question was the question that surfaced the original te'amim-prior failure: when Stan asked which parallelism stance to take for Sifrei Emet, the framing forced the prior-question — what *is* the prior, the te'amim or the atomic thought? The te'amim retirement (initially demotion to evidence-status; fully retired 2026-05-05) is the answer. This subsection makes the symmetry explicit so future editorial work in poetic books does not accidentally reintroduce a parallelism-as-prior commitment under a different label. Do not relitigate by proposing Lowth/Kugel/Berlin/Dobbs-Allsopp as competing structural priors; they are competing scholarly accounts of a phenomenon the editor encounters as evidence.

### N=2 Adjudication Principle

**The problem this solves.** Several canon rules mandate MERGE for N=2 coordinate constructions — M1 bonded pair, future Hebrew-specific compound-verb rules, two-member coordinate clausal series. Simultaneously, structural justification 1 (formally-marked parallel series) mandates SPLIT when each member earns its own atomic beat. At N=2 both rules can fire on the same construction.

**The principle.** When a merge-mandating rule (M1, compound-verb under shared aspectual frame, two-member clausal series) and a split-mandating rule (structural justification 1) both fire on the same N=2 coordinate construction:

- **Bonded / synonymous / cognate / intensification variants → merge wins.** The two members form a single unified image, action, or proposition under one cognitive chunk. Examples: *חֶסֶד וֶאֱמֶת* (M1 bonded), *שָׁמַיִם וָאָרֶץ* (M1 merism), *שְׁמַע וְהַאֲזִינָה* (cognate-imperative pair).
- **Distinct non-synonymous → split wins.** Each member is its own atomic beat per structural justification 1.

**Diagnostic.** Apply the M1 verb-synonymy / noun-bondedness test: *can the two members be paraphrased as a single unified image or proposition without loss of content?* If yes → merge. If the paraphrase requires dropping semantic content unique to one member → split.

**Does not apply at N=3+.** At N=3+ formally-marked parallel series, structural justification 1 wins regardless of whether a merge-rule is also firing — the cognitive prong is formally recoverable from the series itself, and merge-rules defer. The N=2 vs. N=3+ cliff is principled: two items invite bonding (doublet reading); three or more invite cataloguing (series reading).

**Does not apply to appositional constructions.** Appositives are semantically synonymous by definition — the second member re-names the first — so the synonymy test would mechanically fire "merge" on every appositive. The vocative-with-close-appositive case (vocative + divine-title appositive: *יְהוָה אֱלֹהֵי הַשָּׁמַיִם*) and the proper-name + epithet case are governed by their own rules (see §5 Rule H4 vocatives, §5 Rule H9 divine-title appositives), not the N=2 Principle.

### Authorial Asymmetry Principle

When a passage contains a serial construction (woe-series, blessing-series, beatitude chain, conditional-pair, oracle chain) and the author treats members asymmetrically — expanded mechanism for some, compact for others — **preserve the authorial asymmetry**. Do not pressure compact members to expand, or expanded members to compress, in order to achieve uniform line-treatment across the series.

**Test.** Count the finite verbs, elided verbs, and predicative heads in each member of the series. If counts differ between members in the received text, the asymmetry is authorial and the line-structure reflects it. If counts match but editorial line-treatment diverges, that is editorial drift and should converge.

**Hebrew-attested trigger contexts (representative, not exhaustive — to be expanded as the corpus is edited):**
- Prophetic woe-series with asymmetric member expansion (Isaiah's *הוֹי* chains in Isa 5:8–24, where some woes are 2-line bicola and others expand to 4–6-line oracle blocks).
- Blessing/curse pairs in Deuteronomy (Deut 28's blessing list and curse list both expand asymmetrically and should not be flattened).
- Acrostic structures (Pss 119 stanzas, Lam 1–4 alphabetic chapters): the acrostic letter is the structural anchor; member-level asymmetry within stanzas is authorial.
- Positive/negative conditional pairs (*אִם ... וְאִם לֹא ...*).

**SCOPE.** Does NOT apply to same-rule-uniformly-applied cases — those are governed by the parallel-list uniformity principle below. The Authorial Asymmetry Principle governs the distinct failure mode: **imposed uniform structure where the author wrote variation**. The author's finite-verb count, elided-verb count, and predicative-head count per member is the authoritative signal.

### Parallel-List Uniformity Principle

When a multi-verse list of parallel members exists with a shared explicit frame, list members receive uniform line-treatment regardless of their individual syntactic shape. Per-construction rules yield to the list-uniformity principle within the list's scope.

**Trigger.** All four conditions must hold:
1. **Multi-verse list, N≥3 members.** Two-member coordinate cases are governed by the N=2 Adjudication Principle; isolated occurrences aren't a list.
2. **Shared explicit frame.** A repeated lexical anchor introduces each member: *הַבְּרָכָה ... וְהַקְּלָלָה ...* (Deut 27–28); *אַשְׁרֵי הָאִישׁ אֲשֶׁר ...* (Pss 1, 32, 41); *הוֹי X / הוֹי X / ...* (Isaiah's woe chains); *כֹּה אָמַר יְהוָה ... כֹּה אָמַר יְהוָה ...* (prophetic-oracle chains); *אָרוּר ... אָרוּר ...* (Deut 27 curses); *בָּרוּךְ ... בָּרוּךְ ...* (Deut 28 blessings).
3. **Parallel members.** Each list-item is the same kind of thought (a curse pronounced, a blessing declared, a beatitude, an oracle).
4. **Authorial-symmetric.** Members do NOT have the finite-verb-count or predicative-head-count asymmetries that the Authorial Asymmetry Principle protects.

**Default direction — merge.** Each member's frame + content stays on one line per member. The atomic-thought unit at the list scale is *one curse / one blessing / one beatitude / one oracle* per member; a frame-fragment alone (*אָרוּר*) is not a self-standing atomic thought.

**Why merge wins as the default direction:**
- **Atomic-thought test.** Frame-fragments alone fail it; full members as units pass it.
- **Anti-Lowth (§0 Mission).** Split-dominant treatment with repeated visible frames IS the parallelism-display layout the project's stance opposes. We are formatting the text for sense-line reading, not displaying parallelism.
- **Audience.** ESL readers, beginning Hebrew students, and read-aloud delivery favor one-line-per-member rhythm; double-breath-per-member fragments cadence.
- **Descriptive over interpretive.** Merge describes each member as a unit; split imposes a frame-content rhythmic structure on a syntactic surface that doesn't demand it.

**SCOPE — does NOT apply to:**
- N=2 coordinate cases (governed by N=2 Adjudication Principle).
- Authorial-asymmetric series (Authorial Asymmetry Principle takes precedence — preserve mechanism-count differences; do not flatten variation).
- Lists without a repeated explicit frame (narrative sequences without lexical anchor).
- Within-verse coordinate predications (governed by the N=3+ cliff — justification 1 wins over merge-rules at N=3+).

### Decision Procedure — Application Order

Putting generative, subtractive, and diagnostic forces together, the full editorial decision procedure is:

1. **Default:** merge (propositions share one predicate; atomic-thought test applies at the predication level).
2. **Split-trigger fires** (any of: proposition boundary; one of structural justifications 1–5): tentative split.
3. **Syntax veto** (Layer 1 mid-phrase prohibition; complement integrity; formula integrity): blocks the split → **merge**.
4. **Merge-override fires** (M1 bonded pair, M2 clause-nucleus bond, M3 bare-governor, M4 fragmented fragment): blocks the split → **merge**. **When split-trigger and merge-override both fire on the same line, merge-override wins.**
5. **Image diagnostic** (camera angle): sharpens cases where 1–4 leave room for editorial judgment.

**Step 0 — Input filter.** Punctuation, te'amim, sof pasuq, paseq, niqqud, and versification are never break signals. Petucha/setuma are evidence-not-authority (corroborate paragraph-level breaks; do not by themselves license cola-level breaks). The Authorial Asymmetry Principle governs batch-sweep discipline — filters what counts as a candidate signal *before* generative evaluation begins. None of these operate within the per-location procedure; they operate upstream of it.

**Within-step commutativity.** Within Step 2, multiple structural justifications firing are co-compatible — they all agree on SPLIT; no adjudication needed. Within Step 3, multiple merge-overrides firing are co-compatible — they all agree on MERGE; no adjudication needed. Step 3 wins over Step 2 when both fire on the same location.

The framework is a default-merge with two closed lists of exceptions — five structural justifications (add splits beyond propositions) and four merge-overrides (block splits that would fragment unity) — plus the syntax-subtractive veto and the image diagnostic.

**Breath as a named diagnostic was retired before the Tanakh canon's first version.** Both sibling projects retired breath empirically (BoFM 2026-04-19, GNT 2026-04-20). The Hebrew evidence sharpens the retirement: the te'amim are *literally* the historical record of "where the cantor breathes." If breath were a valid sense-unit prior, the te'amim would by definition encode it perfectly. The cognitive-chunking work breath was informally doing is absorbed by structural justification #5 (substantive adjunct as own focus).

---

## §2 Autonomy Boundary — Categories A / B / C

*Purpose: **mainly operational** — Category A/B/C gating definitions. The Autonomy Boundary determines when a validator finding is apply-ready vs. requires editorial judgment.*

Every proposed change falls into one of three categories:

- **Category A — Editorial slippage.** Suboptimal break with no theological or rhetorical stakes. Apply confidently.
- **Category B — Rhetorical shape.** The break changes how the speaker builds an argument. Flag and ask Stan before applying.
- **Category C — Theological weight.** Break placement carries a doctrinal implication. Flag and discuss with Stan before touching.

**Mechanical-rule authority.** When a settled mechanical rule's signature fires unambiguously and the rule's heuristics resolve without ambiguity, the change is **Category A by default**. The canon IS the approval — no per-item flagging is required. Bump to Category B only when rhetorical weight is independently implicated (e.g., breaking a covenant formula, altering a prophetic rhythm with documented liturgical use). Bump to Category C only when theological weight is independently implicated (e.g., classic exegetical hot spots — to be enumerated as the corpus is edited; representative candidates: Gen 1:1–3 (creation narrative opening), Gen 22 (Aqedah), Exod 3:14 (Tetragrammaton revelation), Deut 6:4–5 (Shema), Isa 7:14 (immanuel), Isa 53 (suffering servant), Ps 22, Ps 110, Dan 7). Default-bumping mechanical hits to B out of caution is a failure mode — it inverts the canon's authority and creates unnecessary friction.

**Default:** when uncertain between mechanical and non-mechanical, treat as mechanical if the signature is clean. When uncertain between A and B/C on editorial/rhetorical grounds, treat as Category B. A false Category A on rhetorical grounds (applying a change that warranted discussion) costs more than a false Category B (flagging something straightforward). A false Category B on mechanical grounds (flagging a clean rule hit for review) costs Stan's time and compounds across sessions.

**Scope/precedence/closed-list/carve-out diagnostic.** Canon additions that include ANY of the following are **Category B by default**, regardless of how they are framed in the commit message or §8 entry:
- A scope claim (*"rule X applies to / does not apply to Y"*)
- A precedence claim (*"rule A trumps rule B"*, *"X wins over Y when both fire"*)
- A closed-list extension (adding a verb class, adding a named category, adding a SCOPE-exclusion item)
- A named-category carve-out (introducing a new gating category, even if cross-referenced to an existing rule)

This diagnostic catches the failure mode where a canon change is self-framed as "documenting existing practice" or "scope clarification" but substantively asserts a new judgment. §7 Change Protocol's mandatory-audit trigger list operationalizes this diagnostic for commit-time discipline.

---

# Part II — Operating Rules

*Applied during editorial work; consulted when proposing or evaluating breaks. Validator output is a work queue, not a review queue (per §2 mechanical-rule authority).*

## §3 Quick-Reference Rule Table

*Purpose: **mainly operational** — quick-reference rule table. An editor's first lookup point; rule detail lives in §5.*

Hebrew-specific rules use the H-prefix to distinguish them from sibling-canon rule numbers (BoFM Rule 1–28, GNT R1–R29) and to signal Tanakh-corpus origin.

| # | Name | Type | Trigger | Action |
|---|------|------|---------|--------|
| H1 | Maqqef-group indivisibility | **Layer 1** → [hebrew-break-legality.md](../../data/syntax-reference/hebrew-break-legality.md) | Maqqef glyph (־) joining tokens | Never break inside |
| H2 | Construct chain default | Mechanical + judgment | Bound *nomen regens + nomen rectum*, no intervening modifier | MERGE (one prosodic unit) |
| H3 | Vav-consecutive clause-head policy | Editorial | Wayyiqtol verb at clause head | Default own line for narrative *wayyiqtol* heads; tighter merging in fast-paced narrative sequences (see §5 H3) |
| H4 | Vocative handling (Hebrew) | Editorial | Address particle (or contextually marked vocative — Hebrew lacks a vocative case) | Default own line; merge under apposition rule (§5 H4) |
| H5 | Direct-speech framing default | Mechanical + judgment | *X לֵאמֹר* speech-intro frame | Frame and quoted content occupy separate lines regardless of frame length (short-framing-default retired). Frame length governs visual display, not merge licensing. Narrow scope-economy carve-out (REVIEW-REQUIRED) for ≥4-turn dialogue chains. See §5 H5. |
| H5b | Speech-Act Announcement Default | Mechanical | Finite speech-act verb closing a speech-intro frame, immediately followed by direct discourse | Speech-act announcement and quoted content occupy separate lines. Forced-merge exceptions: H1 (maqqef), H7 (non-speech complement), H5 scope-economy carve-out. See §5 H5b. |
| H6 | Ketiv/Qere policy | Editorial | K/Q markers in source text | Print Qere by default; Ketiv accessible as hover/footnote (per §5 H6 sub-categories) |
| H7 | Complement integrity (Hebrew) | Mechanical | Verb + obligatory complement (*אָמַר* + speech, *יָדַע* + כִּי-clause, etc.) | MERGE across boundary |
| H8 | RETIRED 2026-05-05 | — | — | Te'amim play no role in editorial decisions. See §1 "The Te'amim Play No Role in Editorial Decisions" + §8 entry. |
| H9 | Divine-title appositives | Editorial | Divine title appositive after *YHWH* or *Elohim* | INTRODUCING (formal anchor) → STACK SPLIT; REFERENCING (default) → MERGE |
| H10 | Cross-verse continuity merge | Mechanical | Atomic thought spans MT verse boundary | Sense-line stays intact in earlier verse's block; superscript verse-marker for boundary |
| H11 | RETIRED 2026-05-05 | — | — | Te'amim-internal heuristic; nothing to govern at canon level once te'amim play no role in editorial decisions. See §8 entry. |
| H12 | Petucha/setuma rendering | Mechanical | Petucha or setuma marker in source | Petucha → blank-line paragraph break; setuma → indented break. Evidence-weighted, not authority |
| H13 | Special letters | Editorial | Suspended nun (Judg 18:30), inverted nuns (Num 10:35–36), large/small letters, scriptio plena/defectiva variants | Preserve graphically; document in marginal note; do not affect line breaks |
| H14 | Discourse particles | Editorial | *הִנֵּה, נָא, אָז, עַתָּה, וְעַתָּה, לָכֵן, עַל־כֵּן* | Lead their content (frame, do not trail); cluster with vocative if both sentence-initial |
| H15 | Casus pendens / left-dislocation | Mechanical | Topic-fronted NP + resumptive pronoun in main clause | Topic earns its own line (structural justification 5) |
| H16 | FEF wayehi protasis | Mechanical | *וַיְהִי* + temporal/circumstantial protasis + main clause | Protasis own line; main clause starts fresh |
| H17 | Genealogy / list-formula handling | Editorial | Genealogical formula (*X הוֹלִיד אֶת־Y וַיֵּלֶד בָּנִים וּבָנוֹת*) | List-uniform per Parallel-List Uniformity Principle; merge per-generation member to one line |
| H18 | Clause-nucleus integrity (verbless / participial / verb-PP-complement) | Mechanical + judgment | NP-ending line followed by prep- or participle-fronted next line, no finite verb either side | MERGE (default for short cases ≤8 prosodic words); SPLIT permitted for heavy predicate, casus pendens, embedded poetry, parallel bicolon |

**Guidelines** (useful tendencies, not strict rules): line length as signal; vocative splitting nuances; fronted-adverbial weight thresholds; compound-divine-name handling.

---

## §4 Layer 1 Reference Pointers

*Purpose: **mainly operational** — cross-references to the Layer 1 syntactic floor + the migration discipline that governs which rules live in Layer 1 vs. here.*

### Three-Layer Architecture

The project enforces a three-layer separation:

| Layer | What it is | Where it lives |
|---|---|---|
| **1** | Generic Hebrew grammar — universal facts, language-level | `data/syntax-reference/hebrew-break-legality.md` |
| **2** | Validators — enforce both layers, with distinct error classes | `validators/syntax/` (Layer 1) + `validators/colometry/` (Layer 3) |
| **3** | Tanakh-specific editorial methodology | This canon |

**Validator error classes:**

- `[MALFORMED]` — Layer 1 violation. Hard grammatical failure. Must fix before editorial review is meaningful.
- `[DEVIATION]` — Layer 3 violation. Editorial-policy deviation. Review required before deciding merge / split / document-exception.

### Migration Discipline

**Rules whose body is generic syntactic prohibition** (line-final POS, complement-bond, maqqef-group integrity) **migrate to Layer 1.** Their canon §5 entry becomes a one-line pointer; the operational substance lives in `data/syntax-reference/hebrew-break-legality.md` as a row in the shape-capped table.

**Rules whose body is project-specific operational meat** (verb-class taxonomies, anchor-exemption catalogues, diagnostic tests like Q1/Q2 Goldilocks or Completing-Predication, register-aware decisions) **kernel-reference Layer 1 but stay in canon.** Their structural kernel may be cited from Layer 1 (e.g., "construct chain integrity" as a row), but the rule body — including the editorial overlay, the operational tests, and the corpus evidence — stays in §5.

The shape cap on Layer 1 is what makes this discipline enforceable. A Layer 1 row admits only `signature | legality | reference`; there is nowhere to put editorial reasoning. If a proposed addition needs more than three columns, it stays in the canon. Layer 1's shape cap (24 rows max) is tracked in the file header.

**Reference grammars cited in Layer 1:**

- Joüon-Muraoka, *A Grammar of Biblical Hebrew* (2nd ed., Pontifical Biblical Institute, 2006). Cited as `JM §X`.
- Waltke-O'Connor, *An Introduction to Biblical Hebrew Syntax* (Eisenbrauns, 1990). Cited as `WO §X.Y`.
- GKC = Gesenius-Kautzsch-Cowley, *Hebrew Grammar* (2nd English ed., 1910). Cited as `GKC §X`.

### 4.1 Hebrew Break Legality Reference

Authoritative table: [`data/syntax-reference/hebrew-break-legality.md`](../../data/syntax-reference/hebrew-break-legality.md). Shape-capped table with columns `Hebrew morphological signature | Legality | Reference`. **Status: populated 2026-04-27** — 22 rows out of the 24-row cap (13 REQUIRED-MERGE, 9 PERMITTED-EITHER, 0 REQUIRED-BREAK).

#### Rule-to-Table Mapping

Canon rules H1–H18 cite Layer 1 rows by signature. The grammatical floor lives in Layer 1; the editorial overlay lives in this canon. When a rule says "merge X," verify both that the move is editorially preferred (canon §5) **and** that the table doesn't forbid it (Layer 1).

| Canon rule | Layer 1 row(s) cited |
|---|---|
| H1 (Maqqef-Group Indivisibility) | Maqqef-group split |
| H2 (Construct Chain Default) | Construct chain split, Compound divine name split |
| H3 (Vav-Consecutive Clause-Head Policy) | Vav-consecutive split, Coordinated clause boundary |
| H4 (Vocative Handling) | Vocative unit split, Vocative boundary |
| H5 (Direct-Speech Framing Default) | Speech-frame boundary |
| H5b (Speech-Act Announcement Default) | Speech-frame boundary (same row as H5) |
| H7 (Complement Integrity, Hebrew) | Bound enclitic split, plus verb-object integrity inherited from canon |
| H9 (Divine-Title Appositives) | Compound divine name split, Apposition boundary |
| H14 (Discourse Particles) | Conjunction-prefix and proclitic-stranding rows |
| H15 (Casus Pendens / Left-Dislocation) | Casus pendens boundary |
| H16 (FEF Wayehi Protasis) | Wayyehi / wehayah boundary |
| H18 (Clause-Nucleus Integrity: verbless / participial / verb-PP-complement) | Apposition boundary, Bound enclitic split (H18.2 participial complement); H18.3 inherits H7's verb-object integrity from canon |

Other canon rules (H6 Ketiv/Qere, H10 Cross-Verse Continuity, H12 Petucha/Setuma, H13 Special Letters, H17 Genealogy/List-Formula) operate above this surface — they are textual-tradition policies, editorial-judgment rules, or paragraph-scale concerns where per-line break-legality does not apply. (H8 and H11 retired 2026-05-05 per te'amim consultative-role removal.)

### 4.2 Te'amim Inventory Reference (operational artifact, no canon role)

File: [`data/syntax-reference/teamim-inventory.md`](../../data/syntax-reference/teamim-inventory.md). Originally populated 2026-04-27 as canon reference; **demoted 2026-05-05** to operational reference for `scripts/parse_teamim.py` only. Te'amim inventory has no canon role since the consultative-role retirement (§8 entry 2026-05-05). The file is preserved as historical artifact and parser implementation reference; it is not cited in editorial decisions.

---

## §5 The Rules (Detail)

*Purpose: **mainly operational** — full rule detail for rules H1–H18. Reference when a §3 table entry is insufficient.*

Each rule below follows the template:
- **Grammatical basis** — the Hebrew syntactic / orthographic / Masoretic fact
- **Trigger** — the mechanical signal
- **Diagnostic** — the test a scanner or human applies
- **Exceptions** — closed list
- **Example(s)** — from the corpus

### §5.0 Named Operational Tests

Five named tests that editors invoke by name at candidate boundaries. They are not separate rules — they are shorthands that instantiate the three forces (generative, subtractive, diagnostic) at the per-location decision point. Cite them by name in commit messages, validator annotations, and editorial review notes to make the discipline visible at the surface.

#### No-Anchor Test

**Question:** Does the candidate line carry an atomic-thought anchor — a finite verb, infinitive, predicative participle, verbless-clause subject+predicate, or substantive head independently predicated?

**Application context:** Generative principle (§1 Generative Principle; Hebrew anchor inventory). Fires first at any proposed split before structural justifications are evaluated.

**WHY:** A line with no anchor fails the atomic-thought test by definition. The failure mode it prevents: splitting off a bare NP, a lone proclitic, or a trailing PP that has no self-standing predicative content. When no anchor is present, the fragment belongs with whichever adjacent line supplies the anchor — merge upward (toward the prior line) unless a structural justification pulls it down.

---

#### Period Test

**Question:** Could a period (English-style sentence end) reasonably fall at this candidate boundary — i.e., does the candidate unit constitute a proposition with proposition-end weight?

**Application context:** Generative principle (proposition boundary). Supplements the No-Anchor Test by checking *propositional completeness*, not just anchor presence. A line can carry an anchor and still not constitute a complete proposition (e.g., a participle awaiting its obligatory complement — M3 bare-governor scenario).

**WHY:** The failure mode it prevents: over-splitting when an anchor is technically present but the predication is not yet closed. The period test externalizes the editor's intuition: *if a translator could end a sentence here, the line has proposition-end weight; if not, something is still dangling forward*. When the answer is no, merge with the complement (complement integrity, §1 Syntax Forbids Splits item 2; Rule H7).

---

#### Propositional Completeness Test

**Question:** Does the candidate line predicate a complete proposition — i.e., (a) does it carry an anchor from the §1 Hebrew anchor inventory (finite verb, infinitive, predicative participle, verbless-clause subject+predicate, or substantive head independently predicated), AND (b) is that anchor's valence satisfied on the line itself (no obligatory complement awaited downstream)?

**Application context:** Generative principle (§1 Generative Principle). This is the **canonical operational test for atomic thought.** It is the primary form of the Period Test and the inverse-direction form of the Completing-Predication Test, named explicitly so that editors and validators can cite it by name without invoking the surrogate diagnostics.

**WHY:** A proposition is what the framework recovers (§1 Container-Not-Originator). The atomic-thought test asks whether the line predicates a complete proposition — not whether the reader has learned everything they want to know about the predicated event. The two are routinely confused, especially around speech-act announcements and short narrative wayyiqtol heads, where the *content* of what was said or what was done sits on the next line. **The reader's downstream curiosity about the content is not a propositional gap.** A finite speech-act verb (*וַיֹּאמֶר*) predicates a complete speech-event (subject + finite verb + speech-act); the quoted utterance is a separate cognitive frame, not a missing complement. The Propositional Completeness Test names this distinction so editors stop merging speech-frames into their content under the false signal that the frame is "incomplete."

**Distinction from informational completeness.** Informational completeness asks: *"after reading this line, does the reader know everything they want to know about the event?"* That is **NOT a canon test.** Many propositionally complete lines are informationally incomplete by design — they predicate an event whose *content* (a speech-utterance, a divine command's specifics, a casus pendens's resumed predication) is the next atomic thought, not a grammatical extension of the current one. Informational completeness would collapse the announcement-content distinction (§1 SJ3) and over-merge wayyiqtol clause heads into their objects (against §5 H3 default own-line policy). It is not a permitted criterion for editorial decisions.

**Diagnostic.**
- (a) Anchor present? → If no, fail (No-Anchor Test fires; merge upward).
- (b) Anchor's valence closed on this line? → If yes (no obligatory complement is awaited), the line is propositionally complete. If no (the matrix verb requires a clausal/PP complement that is grammatically obligatory — see Rule H7's verb-class table), the Completing-Predication Test fires; merge with the complement.
- A bare governing participle (*אוֹמֵר* without speech complement, *יוֹדֵעַ* without כִּי-clause) is **not** propositionally complete — its valence is open (M3 fires).
- A finite speech-act verb (*וַיֹּאמֶר*, *וַיְדַבֵּר*, *וַיְצַו לֵאמֹר*) **is** propositionally complete on its own. The quoted content is a distinct atomic thought (speech-act announcement per SJ3).

**Cite-by-name.** "Propositional Completeness Test → split (frame is complete; speech is separate atomic thought)" or "Propositional Completeness Test → merge (matrix verb's *כִּי* complement is obligatory; valence open)."

---

#### Image Test

**Question:** Does the mind's eye reposition between the candidate frames — a camera-angle shift between them?

**Application context:** Diagnostic force (§1 Image Sharpens Ambiguous Proposition Boundaries). Fires only after generative and subtractive forces leave a genuine ambiguity — it is a tiebreaker, not a primary generator.

**WHY:** The failure mode it prevents: using intuitive "visual" judgment as a primary split-generator instead of holding it to the tiebreaker role the canon assigns. A camera-angle shift → SPLIT (two distinct focal planes, two lines); no shift → MERGE (one image, one line). The test disciplines the editor to ask *does the perspective change* rather than *does this look like two lines*. Prevents scope creep from rhetoric-bandwagon categories (§1 Imposing vs. Revealing).

---

#### Goldilocks Q1/Q2 Diagnostic

**Q1:** Is the candidate line *too short* to stand as atomic thought — a single bare token with no predication and no structural-justification recoverability?

**Q2:** Is the candidate line *too long* to read as one focused-attention chunk — a span that contains what would otherwise be multiple independently licensable propositions?

**Application context:** Length-range sanity check wrapping the atomic-thought test. Both questions apply *after* structural justifications and merge-overrides have run.

- Q1 yes → the line fails the atomic-thought test; merge upward (M4 prospective test / No-Anchor Test).
- Q2 yes → the span contains multiple propositions; look for the internal boundary where a split is licensed.
- Both no (Goldilocks) → leave as-is; neither force applies.

**WHY:** The failure modes it prevents: (a) Q1 — over-splitting that produces widow tokens with no standalone meaning (bare conjunctions, lone preposition-prefixes, bare construct heads — all Layer 1 REQUIRED-MERGE); (b) Q2 — under-splitting that buries multiple propositions in one line, defeating the sense-line purpose. The Goldilocks framing keeps both failure modes in view simultaneously. Note that Q2 is a *signal* to look for an internal split, not itself authorization to split — the licensed split still requires a structural justification or proposition boundary.

---

#### Completing-Predication Test

**Question:** Does the matrix word on the prior line require a downstream complement — a PP, a clausal complement (כִּי-clause, אֲשֶׁר-clause, *לֵאמֹר*-introduced speech, infinitive complement) — to be syntactically complete?

**Application context:** Subtractive force — complement integrity (§1 Syntax Forbids Splits item 2; Rule H7; M3 bare-governor indivisibility). Fires when a proposed split would strand the complement on a separate line from its governing matrix.

**WHY:** The failure mode it prevents: producing lines where the prior line's verb or adjective is syntactically open (valence unsatisfied) and the next line closes it — breaking across a dependency arc that Hebrew grammar treats as one unit. The test is the functional twin of the Period Test: the Period Test checks whether proposition-end weight is present *at the boundary*; the Completing-Predication Test checks whether the *prior* line is already complete or still open. Both must pass for a split to proceed cleanly.

---

**Cite-by-name convention.** In commit messages and validator annotations, reference these tests by their short names: "No-Anchor Test → merge," "Image Test → split (camera shift at *וַיָּקָם*)," "Completing-Predication Test → merge (*יָדַע* still open at כִּי)," etc. This makes the three-force reasoning visible in the audit trail without requiring full prose re-statement of the underlying rule.

---

### Rule H1 — Maqqef-Group Indivisibility

**Grammatical basis.** The maqqef (־, U+05BE) joins two-to-four orthographic words into a single **prosodic word** bearing a single ta'am. The maqqef-group is treated as one cantillation unit by the Masoretic apparatus and as one accentual phrase by Hebrew prosody.

**Trigger.** Presence of maqqef glyph between tokens.

**Diagnostic.** Never break inside a maqqef-group, regardless of length. A 4-word maqqef-group is one prosodic unit even when long.

**Exceptions.** None. Maqqef-group integrity is Layer 1 — generic Hebrew grammatical fact, not an editorial convention.

**Note on rendering.** Display the maqqef glyph between joined orthographic words. The web-app's per-orthographic-word `<span>` structure preserves the joining for downstream layers (translit, interlinear) — the connector glyph (figure dash ‒ in current implementation) marks the prosodic bond visually.

### Rule H2 — Construct Chain Default

**Grammatical basis.** A construct chain (*nomen regens + nomen rectum*, e.g., *דְּבַר־יְהוָה*, *בֵּית הַמֶּלֶךְ*, *מִמְּעֵי הַדָּגָה*) is a single bound noun phrase. The regens is in construct state; the rectum carries the genitival force. Modern reference grammars (Joüon-Muraoka §129; Waltke-O'Connor §9) treat construct chains as one syntactic unit for clause analysis.

**Trigger.** Bound *nomen regens + nomen rectum* sequence with no intervening modifier (no article hopping, no PP intervention, no relative clause attached to regens only).

**Diagnostic.** MERGE — treat the construct chain as one prosodic unit for break decisions, regardless of whether the chain is maqqef-joined or not.

**Exceptions:**
- Chain interrupted by a maqqef-group's natural break point (rare; the maqqef-joining usually coincides with the construct binding).
- Chain with intervening modifier on the regens (e.g., *הַבַּיִת הַגָּדוֹל אֲשֶׁר־לַמֶּלֶךְ*) — modifier may license a break, evaluated case-by-case.
- Long construct chain (3+ levels deep) where the deepest rectum is itself modified by a substantial relative clause — evaluate under structural justification 5 (substantive adjunct).

**Example.** Jonah 2:7 *מִמְּעֵי הַדָּגָה* — construct chain, treat as one unit; do not break between *מִמְּעֵי* and *הַדָּגָה* even though they're not maqqef-joined. Currently widow-line in v1/he-baseline Jonah; v2/heb should merge upward.

### Rule H3 — Vav-Consecutive Clause-Head Policy

**Grammatical basis.** Hebrew narrative is built on chains of *wayyiqtol* (vav-consecutive imperfect) verbs, each marking a sequential narrative event. The *wayyiqtol* form carries narrative-tense morphology (consecutive vav + apocopated yiqtol) and is the dominant clause-head marker in Hebrew prose. The te'amim mark *wayyiqtol* heads inconsistently — sometimes with a strong disjunctive, sometimes with a conjunctive.

**Trigger.** *Wayyiqtol* verb at clause head (verbal morphology: וַ + dagesh forte + yiqtol stem).

**Diagnostic.** **Default own line for narrative wayyiqtol clause heads.** Each wayyiqtol typically introduces its own narrative event and its own atomic thought. Even when the te'amim group multiple wayyiqtol clauses under one atnach, each gets its own line in v2/heb.

**Exceptions:**
- **Tight narrative pairs** (*וַיָּקָם וַיֵּלֶךְ*, *וַיַּעַן וַיֹּאמֶר*, *וַיָּבֹא וַיֵּשֶׁב*): two wayyiqtol clauses describing tightly-bonded sequential actions in one image (rising-and-going, answering-and-saying, coming-and-sitting) merge under M1 bonded-pair logic. The pair functions as a single narrative beat.
- **Speech-intro pair** (*וַיַּעַן ... וַיֹּאמֶר אֵלָיו לֵאמֹר*): the answering+saying pair is a speech-intro frame — merge per structural justification 3 + Rule H5.
- **Hendiadic wayyiqtol-pair**: when the second wayyiqtol modifies the first (e.g., *וַיּוֹסֶף לְדַבֵּר* "he continued speaking"), the pair is one event — merge.

**WHY:** vav-consecutive is the single most frequent break-decision question in Hebrew narrative. Without an explicit policy, every prose chapter would face this in verse 1 (Jonah 1:1 *וַיְהִי* opens the book; the next clause *וַיָּקָם יוֹנָה* in v.3 starts a fresh wayyiqtol chain).

**HOW WE KNOW:** Hebrew narrative grammar (Waltke-O'Connor §33 on wayyiqtol; Niccacci 1990 on the *wayyiqtol* as foreground-narrative engine). Corpus evidence will accumulate as books are edited.

**SCOPE:** prose books only (21 books using prose accent system + Job's prose frame 1:1–2:13 and 42:7–17). Sifrei Emet poetic books rarely use *wayyiqtol* in extended chains; case-by-case there.

### Rule H4 — Vocative Handling

**Grammatical basis.** Hebrew lacks a morphological vocative case. Direct address is marked by:
- Sentence-initial address particle (rare — *הוֹי*, *אוֹי* function as woe-particles + vocative; *אָנָּא* as polite plea + vocative)
- Article-marked NP in address position (*הַמֶּלֶךְ*, *הָאֱלֹהִים*)
- Bare NP in address position with second-person verbal morphology in the surrounding clause
- Proper name in address position
- Compound divine-title address (*יְהוָה אֱלֹהֵי הַשָּׁמַיִם*)

**Trigger.** NP in syntactic address position (initiating direct speech to a named addressee, or coreferential with a 2nd-person verbal form in the same clause).

**Default.** Vocatives get their own line when they initiate or resume direct address. A vocative at the start of a verse, after a speech-introducing boundary, or initiating a new address turn earns its own line as a complete address act.

**Apposition exception.** A vocative merges into the preceding line when it is grammatically appositive to an already-established 2nd-person address in the same clause. Two sub-cases:
1. **Subject-appositive:** vocative names the implicit subject of a 2p finite verb in the same clause.
2. **Object-appositive:** vocative restates an explicit 2p pronoun already in the clause.

**Repeated vocatives as a rhetorical unit stay together.** *אַבְרָהָם אַבְרָהָם* (Gen 22:11), *מֹשֶׁה מֹשֶׁה* (Exod 3:4), *שְׁמוּאֵל שְׁמוּאֵל* (1 Sam 3:10) are one speech act per occurrence.

**Stacked parallel vocatives** (multi-vocative address chains) are treated as a parallel address structure — each vocative on its own line per structural justification 1.

### Rule H5 — Direct-Speech Framing Default

**Grammatical basis.** Hebrew direct speech is introduced by an explicit speech-intro frame, most commonly *X אָמַר/אָמְרוּ + (אֶל-Y) + לֵאמֹר*, where *לֵאמֹר* is the bare infinitive complementizer marking the speech-onset boundary. The frame is an obligatory grammatical construction (Waltke-O'Connor §36.2.3 on *לֵאמֹר*).

**Trigger.** Speech-intro frame ending in *לֵאמֹר* or in a bare *וַיֹּאמֶר* / *וַיְדַבֵּר* / *וַיַּעַן* without *לֵאמֹר* but immediately followed by speech.

**Diagnostic.** **Speech-act announcement and quoted content are separate atomic thoughts.** A finite speech-intro frame (*X אָמַר/דִּבֶּר/עָנָה (אֶל-Y) (לֵאמֹר)*) predicates a complete speech-event — subject, finite verb, optional recipient, optional *לֵאמֹר* complementizer marking speech-onset. The quoted content is a distinct atomic thought (§1 structural justification 3). **Default: split between announcement and content, regardless of framing length.** This is the propositional-completeness reading of SJ3; it harmonizes H5 with §1.

**Length is not a merge license.** Earlier formulations of H5 carried a "short-framing-default" merge stance (frames ≤3 prosodic words merged with speech-opening). That stance treated the framing as informationally incomplete on its own; the Propositional Completeness Test (§5.0) and §1 M3 contrast paragraph make explicit that a finite speech-act verb is propositionally complete. Frame length governs visual display of the announcement; it does not license merging announcement with content.

**Scope-economy carve-out (narrow, REVIEW-REQUIRED).** A two-token bare-frame + ≤3-prosodic-word speech opening (e.g., *וַיֹּאמֶר לוֹ הִנֵּנִי*, *וַיֹּאמֶר כֵּן*, *וַיַּעַן הִנֵּנִי*) MAY be merged when the visual rhythm of the surrounding narrative dialogue chain (≥4 consecutive answer-and-response turns) makes the per-turn split visually noisy. **This is editorial judgment under §2 Category B**, not mechanical default. Validators must surface these as REVIEW-REQUIRED, not STRONG-MERGE.

**Solemnity-prefix and oracle-formula speech-intros.** Prophetic *כֹּה אָמַר יְהוָה* and oracle attribution *נְאֻם־יְהוָה* are atomic formulaic units that get their own line — **same default as ordinary finite speech-frames now.** The earlier "exception" framing is retired; these are no longer exceptional.

**Example contrasts (revised):**
- Jonah 1:6 *וַיֹּאמֶר לוֹ // מַה־לְּךָ נִרְדָּם* — frame on its own line; speech opens on next. (Previously merged under short-framing-default; now split per default.)
- Jonah 1:9 *וַיֹּאמֶר אֲלֵיהֶם // עִבְרִי אָנֹכִי* — frame on its own line; speech opens on next. (Previously merged.)
- Jonah 1:1 *וַיְהִי דְבַר־יְהוָה אֶל־יוֹנָה בֶן־אֲמִתַּי לֵאמֹר // [v.2 speech]* — unchanged; long-framing case already split.

**Connection to Rule H5b.** The split-default formalized here is restated as **Rule H5b — Speech-Act Announcement Default** for cross-rule citation clarity (§5 H5b below).

### Rule H5b — Speech-Act Announcement Default

**Grammatical basis.** Per §1 structural justification 3, a finite speech-act predication (*X אָמַר*, *X דִּבֶּר*, *X עָנָה*, *X צִוָּה (אֶל-Y) (לֵאמֹר)*; prophetic *כֹּה אָמַר יְהוָה*; oracle *נְאֻם־יְהוָה*) constitutes a **complete cognitive frame on its own** — the announcement of a speech-event. The quoted content is a separate atomic thought.

**Trigger.** Finite speech-act verb (qatal, yiqtol, wayyiqtol, weqatal, jussive, cohortative, imperative, infinitive-construct in matrix function, participle in predicative position) heading or closing a speech-introduction frame, immediately followed by direct discourse content.

**Diagnostic.** **Default: the speech-act frame and the quoted content occupy separate lines.** This applies regardless of frame length:
- 1-token bare frame (*וַיֹּאמֶר // [content]*) → split.
- 2-token frame (*וַיֹּאמֶר לוֹ // [content]*) → split.
- Multi-word frame with recipient (*וַיֹּאמֶר יְהוָה אֶל־מֹשֶׁה // [content]*) → split.
- Long frame with FEF wayehi protasis + לֵאמֹר (Jonah 1:1) → split (already covered by H16 FEF + H5b combined).

**Forced-no-merge (this rule wins).** Wherever a speech-act frame and content meet, H5b mandates the split. Other rules that would merge across this boundary (any informational-completeness-style spec) are subordinate.

**Forced-merge exceptions (these rules win over H5b — closed list):**
- **H1 maqqef-group integrity** — never break inside a maqqef-group, even if the maqqef joins an embedded vocative + first content word.
- **H7 complement integrity, NON-speech subset** — the Hebrew speech-frame is *not* the same as cognition/volition/causative + *כִּי* complementation. H7 still merges *יָדַע כִּי*, *רָאָה כִּי*, *רָצָה כִּי*, etc. with their content clauses.
- **Scope-economy carve-out (Category B, REVIEW-REQUIRED)** — see H5 narrow exception above.

**Worked examples (paradigmatic):**
- *כֹּה אָמַר יְהוָה //* [oracle content] — manner adverb + finite verb + subject = complete predication; oracle content is a separate ATU. Split always.
- *נְאֻם־יְהוָה //* [adjacent oracle line] — subject + nominal predicate = complete formulaic ATU. Split always.
- *וַיְהִי דְבַר־יְהוָה אֶל יוֹנָה בֶן־אֲמִתַּי לֵאמֹר //* [Jonah 1:2 content] — full FEF prophetic-intro is one ATU per H16; speech-onset marker *לֵאמֹר* closes the frame; oracle content is separate ATU.
- *וַיֹּאמֶר אֵלַי //* [vision content] — addressee-marked prophetic-vision frame. Frame is complete; vision content is separate.

**Defensibility capture:**
- **WHY:** A finite speech-act verb predicates a complete speech-event. The quoted utterance is the next atomic thought, not a grammatical complement of the announcement verb. Merging announcement with content collapses two cognitive frames into one and violates §1 SJ3. The pre-revision H5 short-framing-default was treating informational completeness ("the reader hasn't been told what was said yet") as if it were propositional incompleteness; the Propositional Completeness Test (§5.0) makes this distinction explicit and H5b operationalizes it.
- **HOW WE KNOW:** §1 SJ3 prose; §1 M3 contrast paragraph which explicitly states finite speech-act formulas ARE complete predications; consistency with H3 (default own line for narrative wayyiqtol clause heads — speech-act wayyiqtol falls under the same principle); validator dashboard re-runs (post-revision) confirm cleaner separation between H5b and H7. Path 1 corpus FP/FN sample (2026-05-02): 75-78% CLEAN, with PROBLEM cases concentrated in three tractable carve-out classes (Job answering-formula, homograph guard for ויוסף/ויען/וידבר, Sifrei Emet meter).
- **SCOPE:** All books (prose 21 + Sifrei Emet + embedded poetry). Speech-act announcement is register-invariant; the cognitive distinction holds in poetic books equally. Does NOT apply to: (a) maqqef-joined frame+content boundaries (H1 wins); (b) cognition/volition/causative *כִּי*/אֲשֶׁר complement clauses where the matrix verb's valence is unsatisfied (H7 wins, NOT speech-act predication).

**Connection to other rules:**
- **Rule H5** (revised): handles the visual length of the announcement frame and the scope-economy carve-out.
- **Rule H3** (vav-consecutive clause-head policy): wayyiqtol speech verbs (*וַיֹּאמֶר*, *וַיְדַבֵּר*) inherit own-line default from H3; H5b reinforces and specializes for the announcement-content boundary.
- **Rule H14** (discourse particles): speech-content frequently opens with *הִנֵּה* — H14 already places *הִנֵּה* on its own line (or leading the content line); H5b's split occurs cleanly at the announcement/content boundary regardless.
- **Rule H16** (FEF wayehi protasis): *וַיְהִי + protasis + לֵאמֹר // content* combines H16 (protasis own line) + H5b (announcement/content split).

### Rule H6 — Ketiv/Qere Policy

**Grammatical basis.** The Masoretic apparatus preserves two layers of textual tradition:
- **Ketiv** (*כְּתִיב* "what is written") — the consonantal text as transmitted in writing.
- **Qere** (*קְרֵי* "what is read") — the oral reading tradition, sometimes diverging from the written consonantal text.

When Ketiv and Qere differ, the Masoretes preserved both: Ketiv stands in the consonantal text; Qere is marked in the marginal masorah parva and is what the reader/cantor actually voices.

**Default policy: Print Qere by default; Ketiv accessible as hover/footnote.**

**WHY:** The project's oral-delivery orientation favors the Qere — what was actually read aloud in the synagogue tradition the te'amim and niqqud serve. The Ketiv preserves the consonantal tradition and remains accessible for the reader who wants it, but does not occupy the primary visual layer.

**Sub-categories — Ketiv/Qere variants the canon must address:**

#### Rule H6.1 — Perpetual Qere (*Qere Perpetuum*)

**Definition.** Words whose Qere is so consistently substituted that the Masorah does not mark each instance individually. The canonical case is the Tetragrammaton יהוה, vocalized with the niqqud of *אֲדֹנָי* (or *אֱלֹהִים* in immediate sequence with *אֲדֹנָי*), to be read as *Adonai* (or *Elohim*) in liturgical context but written as *YHWH* in the consonantal text.

**Policy.** Display the Tetragrammaton consonants יהוה with the niqqud as transmitted. Do not transliterate as *Adonai* in the translit layer (the project's Modern Israeli transliteration convention transliterates as *Yahweh* per scholarly convention; this is a transliteration choice, not a Ketiv/Qere choice). English gloss layer renders as "the LORD" (small caps) per English-reader convention OR as "Yahweh" per scholarly convention — TBD as English layer matures.

#### Rule H6.2 — *Qere ve-La-Ketiv* (Read but Not Written)

**Definition.** Words read aloud (preserved in the Masorah) that do not appear in the written consonantal text. Example: Judg 20:13 omits *בְּנֵי* in the Ketiv but reads it in the Qere.

**Policy.** Render Qere words in the primary text (italicized or otherwise marked as "read but not written") with marginal note documenting the Ketiv omission. Do not add words silently.

#### Rule H6.3 — *Ketiv ve-La-Qere* (Written but Not Read)

**Definition.** Words written in the consonantal text that are not voiced in reading. Example: Jer 51:3 has *יִדְרֹךְ* doubled in some witnesses with one occurrence as Ketiv-only.

**Policy.** Render the read text as primary; Ketiv-only consonants are marked in marginal note. Do not display silent consonants in the primary visual layer.

#### Rule H6.4 — *Sebirin* (Suspected Readings)

**Definition.** The Masorah occasionally marks a reading as *sebirin* — a "supposed" alternative that some manuscripts or readers have substituted but that the masoretic consensus rejects in favor of the printed reading. Roughly ~350 sebirin notes in the Leningrad apparatus (Yeivin 1980 §149).

**Policy.** Print the masoretic-consensus reading (the non-sebirin form). Mark the sebirin alternative in marginal note where the Masorah records it. Do not adopt sebirin readings into the primary text.

#### Rule H6.5 — *Tiqqunei Sopherim* and *Itture Sopherim*

**Definition.** *Tiqqunei sopherim* ("scribal corrections") — early scribal emendations the Masorah identifies as deliberate textual changes from an earlier form (e.g., euphemistic alterations to avoid blasphemy, ~18 cases per masoretic tradition). *Itture sopherim* ("scribal omissions") — instances where the Masorah notes that the text omits a vav that earlier tradition included (~5 cases).

**Policy.** Print the Masoretic form. Document the scribal-correction note in marginal apparatus where the Masorah records it. The project does not "restore" earlier forms; the Masoretic consensus is the textual base.

### Rule H7 — Complement Integrity (Hebrew)

**Grammatical basis.** Verbs requiring a clausal or PP complement form one integrated predication with their complement. The matrix verb alone does not express a complete thought.

**Hebrew verb classes in scope:**

| Class | Hebrew examples | Merges with complement |
|-------|-----------------|------------------------|
| Speech (introducing speech) | *אָמַר לֵאמֹר*, *דִּבֶּר אֵל*, *צִוָּה לֵאמֹר* | Merges with speech-intro frame components (recipient PP, *לֵאמֹר* marker) per Rule H5; does NOT merge with quoted content per Rule H5b. |
| Cognition | *יָדַע כִּי*, *הֵבִין כִּי*, *זָכַר כִּי*, *רָאָה כִּי*, *שָׁמַע כִּי* | Yes (verb + כִּי-clause merges) |
| Volition | *רָצָה כִּי*, *חָפֵץ כִּי*, *בִּקֵּשׁ אֲשֶׁר* | Yes |
| Causative | *צִוָּה אֲשֶׁר*, *גָּזַר כִּי*, *הֵכִין כִּי* | Yes |
| Aspectual | *הוֹסִיף לְ*, *הֵחֵל לְ*, *כִּלָּה לְ* | Yes (verb + infinitive complement merges) |
| Verbless-clause copular-equivalent | *הָיָה X לְ-Y* | Yes (predicative complement merges with היה) |

**Diagnostic.** Matrix verb and its clausal/PP complement stay on the same line. When combined length exceeds a natural line, prefer an alternative restructuring over a mid-predication break.

**Exceptions — complement integrity does NOT apply:**
- Direct discourse (colon or *לֵאמֹר* after speech verb → voice shift, content begins on next line per structural justification 3).
- Long-complement exception (parallel to BoFM Rule 17 long-complement exception): when the matrix is short (verb + recipient), AICTP-equivalent (post-*וַיְהִי*-protasis), with no extended scene-setting, AND the *כִּי*-clause complement is a substantial proposition (≥8 prosodic words with own finite verb), the split is licensed as a structural-justification-3 indirect-discourse announcement.
- Formally-marked parallel *כִּי*-series (frame + first; stack remainder per structural justification 1).
- Direct divine speech with recitativum *כִּי* (*נְאֻם־יְהוָה כִּי [first-person content]*) — recitativum-*כִּי* functions as direct-discourse marker.

**Delete-test diagnostic.** Remove any intervening NP. If the sentence still reads as "[subject] [verb] *כִּי* X," the *כִּי* clause is a complement — MERGE. If the deletion breaks the sentence, the *כִּי* clause is appositive to a noun — DNM (do not merge).

### Rule H8 — RETIRED 2026-05-05

Rule H8 (Te'amim as Evidence — Operational Application) is **retired** as part of the te'amim consultative-role removal. See §1 "The Te'amim Play No Role in Editorial Decisions" and §8 entry "2026-05-05 — Te'amim consultative role retirement" for the retirement rationale.

The v1-he-baseline (`data/text-files/v1/he-baseline/`) was generated mechanically by `scripts/parse_teamim.py` as a one-time starting draft for v2/heb hand-editing. Defensibility-capture for non-trivial breaks cites the three forces (atomic thought, single image, Hebrew syntax) and the named structural-justifications; it does not cite te'amim positions.

Rule numbering preserved (H8 slot stays empty rather than renumbering H9–H17).

### Rule H9 — Divine-Title Appositives

**Grammatical basis.** Divine titles in apposition to *יְהוָה* or *אֱלֹהִים* (e.g., *יְהוָה אֱלֹהֵי הַשָּׁמַיִם* "YHWH God of the heavens" at Jonah 1:9; *יְהוָה צְבָאוֹת* "YHWH of hosts" passim; *אֲדֹנָי יְהוִה* compound) function either as **introducing** (formal naming or first-occurrence revelation) or **referencing** (already-established identity used as a bound name unit).

**Trigger.** Divine-title appositive structure following YHWH or Elohim.

**Diagnostic — requires formal anchor for STACK SPLIT:**

INTRODUCING (stack on own line) earns a split ONLY when one of three formal anchors is present:
1. **Formal naming formula:** *וְקָרָא שְׁמוֹ X / Y / Z* "and his name shall be called X, Y, Z."
2. **First-occurrence context:** identity revealed for the first time in the passage.
3. **Prophetic proclamation frame:** *כֹּה אָמַר יְהוָה X / Y / Z* — divine-title cluster within prophetic introduction.

**REFERENCING (default, MERGE).** Already-established identity used as a name unit. Most divine-title appositives are referencing.

**Example (REFERENCING):** Jonah 1:9 *אֶת־יְהוָה אֱלֹהֵי הַשָּׁמַיִם אֲנִי יָרֵא* — *יְהוָה אֱלֹהֵי הַשָּׁמַיִם* is a bound name unit referencing the established Hebrew deity, not a first-time revelation. MERGE.

**Precedence with Rule H4 (vocative).** When a divine-title appositive sits within a vocative unit (the phrase opens with address particle + title, addressing deity directly in second person), **Rule H4 wins** — the vocative + its close appositive stay whole as one direct-address unit. Rule H9's STACK SPLIT for INTRODUCING appositives applies only to non-vocative narrative or prophetic frames (third-person naming contexts).

### Rule H10 — Cross-Verse Continuity Merge

**Grammatical basis.** When a single atomic thought crosses an MT verse boundary, the sense-line stays intact. The verse boundary is an editorial overlay (Masoretic verse division was pre-Masoretic chant-units, finalized in the Tiberian period; not original to the text); it does not constrain sense-line formation. The sense-line is formed by grammatical/rhetorical continuity, and the versification is carried along by an inline superscript marker.

**Trigger.** Atomic thought continues across a verse boundary (most common in: wayyiqtol narrative chains, prophetic oracle blocks, casus pendens with resumption in the next verse, cross-verse *לֵאמֹר*-introduced speech where the speech opens in the next verse).

**Procedure:**
1. **Identify the boundary** — grammatical continuity indicator (wayyiqtol chain, suspended subject, speech-intro straddle, oracle continuation).
2. **Merge in place** — the sense-line lives in the *earlier* verse's block (where its lead word sits), with the content that MT attributes to the later verse attached inline after a superscript verse-number marker (`²`, `³`, etc.) indicating where the later verse begins visually.
3. **Mirror in English gloss layer** — the same merge, the same superscript position.
4. **Cite using the earlier verse's reference** when referring to the merged colometric line.

**Both directions apply.** Sometimes MT pushes a word *forward* into the next verse where sense-line analysis keeps it with the prior; sometimes MT places a word in the earlier verse where sense-line analysis attaches it to the next clause. Same convention applies — keep the sense-line intact in the verse where its lead word sits, mark the boundary with superscript.

**Hebrew-versification-only.** This rule operates on MT (Hebrew) versification. The Hebrew/Christian versification crosswalk (per textual posture) is independent of cross-verse continuity decisions; the crosswalk is a citation-lookup mechanism, not a structural decision.

**Cross-verse continuity** is the operative convention; Hebrew-specific examples appear in the rule diagnostic above.

### Rule H11 — RETIRED 2026-05-05

Rule H11 (Tifcha-as-Servant-of-Atnach) is **retired** as part of the te'amim consultative-role removal. See §1 "The Te'amim Play No Role in Editorial Decisions" and §8 entry "2026-05-05 — Te'amim consultative role retirement" for the retirement rationale.

Tifcha-as-servant was a te'amim-internal heuristic governing the parse_teamim.py draft generator. Now that te'amim play no role in editorial decisions, the rule has nothing to govern at the canon level. The parse_teamim.py heuristic itself remains as one-time draft-generation code (operational, not consultative); whether it implements tifcha-as-servant or not is an implementation detail, not a canon commitment.

Rule numbering preserved (H11 slot stays empty rather than renumbering H12–H17).

### Rule H12 — Petucha / Setuma Rendering

**Grammatical basis.** See §1 "Petucha / Setuma Are Evidence, Not Authority."

**Trigger.** Petucha (פ marker in TAHOT, or whole-line gap in source manuscripts) or setuma (ס marker, or mid-line gap) in the source apparatus.

**Diagnostic.**
- **Petucha → blank-line paragraph break** in v2/heb and rendered as `<div class="paragraph-break-open">` (or equivalent) in the web app.
- **Setuma → indented paragraph break** in v2/heb and rendered as a smaller-prominence visual break.
- Section-level navigation in the web app uses petucha/setuma boundaries as primary structural cues; chapter/verse divisions are present for citation but not the primary structural framing.

**Tradition-disagreement protocol.** When Aleppo, Leningrad, MAM, and BHS disagree on petucha/setuma placement (which they do at the ~5–10% level per Yeivin 1980; Tov 2012), the project follows Leningrad per textual posture §0.1. Discrepancies may be documented in marginal note for sibling-tradition awareness but do not affect the primary text.

### Rule H13 — Special Letters

**Grammatical basis.** The Masoretic text preserves graphical anomalies that the masoretic consensus identifies as deliberate (not scribal errors):
- **Suspended letters** (large nun in Judg 18:30 *מְ\nנַשֶּׁה*, large ayin in Lev 11:42, etc.).
- **Inverted nuns** (Num 10:35–36, Ps 107:23–28).
- **Large letters** (Gen 1:1 *בּ*, Deut 6:4 *ע* of *שְׁמַע*, Lev 11:42 *ו* of *גָּחוֹן*).
- **Small letters** (Gen 2:4 *ה* of *בְּהִבָּרְאָם*, Lev 1:1 *א* of *וַיִּקְרָא*).
- **Scriptio plena vs. scriptio defectiva** (presence/absence of mater lectionis vowel letters yod/vav across manuscript traditions).

**Trigger.** Source apparatus marks special letter.

**Diagnostic.**
- Preserve graphically in the rendered text (web app must support these — to be implemented).
- Document in marginal note (or hover) with masoretic-tradition reference.
- **Do not affect line breaks.** Special letters are graphical anomalies, not structural cues. The line break decision is independent.

**Scriptio plena/defectiva.** TAHOT preserves the Leningrad orthography. Variants in MAM (Aleppo) or other witnesses are not adopted. Translit layer transliterates the Leningrad form.

### Rule H14 — Discourse Particles

**Grammatical basis.** Hebrew has a rich inventory of discourse particles that signal frame, transition, deixis, or emphasis:
- *הִנֵּה* — deictic ("behold!") + speech-act-announcement framing
- *נָא* — politeness particle, attaches to imperatives
- *אָז* — temporal pivot ("then")
- *עַתָּה* / *וְעַתָּה* — discourse pivot ("now" / "and now")
- *לָכֵן* — inferential ("therefore")
- *עַל־כֵּן* — causal-inferential ("for this reason")
- *אַף* — emphatic addition ("even", "also")

**Default.** These particles **lead their content**, not trail the prior clause. Never orphan them at the end of a line.

**Diagnostic.**
- *הִנֵּה* sentence-initial → own line (deictic/speech-act-announcement framing per structural justification 3).
- *הִנֵּה* mid-clause as parenthetical deictic → merge with preceding clause if short, evaluate case-by-case.
- *נָא* as imperative-suffix → never separate from imperative.
- *אָז*, *עַתָּה*, *וְעַתָּה*, *לָכֵן*, *עַל־כֵּן* sentence-initial → frame next line; merge with content on one line if short, lead next line if content is long.

**Cluster with vocative.** When a sentence-initial discourse particle co-occurs with a vocative, both are extra-clausal elements and cluster on one line; the proposition follows on the next line.

### Rule H15 — Casus Pendens / Left-Dislocation

**Grammatical basis.** Hebrew uses topic-fronting + resumptive pronoun (casus pendens, also called *nominative absolute* or *left-dislocation*) extensively. The fronted topic is grammatically detached; the main clause picks up the topic via a resumptive pronoun. Joüon-Muraoka §156 documents this as a primary Hebrew syntactic device.

**Trigger.** Topic-fronted NP + main clause with resumptive pronoun (often a possessive suffix or independent pronoun referring back to the topic).

**Diagnostic.** The fronted topic earns its own line per structural justification 5 (substantive adjunct as own focus). The main clause begins on the next line.

**Example:** *וְהָאֱלֹהִים יַעֲנֶנּוּ בְקוֹל* "(As for) God / He answers him with [his] voice" — *וְהָאֱלֹהִים* fronted topic; *יַעֲנֶנּוּ* main clause with object-suffix resumption.

**SCOPE:** does not apply to mere subject-fronting without resumption (which is a marked-but-bound word-order variation, not a true casus pendens — fronting paradox applies, see §1 "Imposing vs. Revealing").

### Rule H16 — FEF Wayehi Protasis

**Grammatical basis.** The Hebrew narrative construction *וַיְהִי* + temporal/circumstantial protasis + main clause is the canonical Front-End Frame. The *wayyiqtol* of *הָיָה* introduces a temporal frame; the protasis sets the scene; the main clause resolves.

**Trigger.** *וַיְהִי* + (optional temporal/circumstantial material) + main clause.

**Diagnostic.**
- The *wayehi*-protasis is held together as one atomic temporal frame **regardless of length**.
- The main clause starts a new line.
- Even short protases (Jonah 1:1's 5-orthographic-word *וַיְהִי דְבַר־יְהוָה אֶל־יוֹנָה בֶן־אֲמִתַּי לֵאמֹר*) are FEF-shaped and earn their own line.

**Connection to Rule H5 direct-speech framing.** When *וַיְהִי* + speech-intro frame + *לֵאמֹר* combines (Jonah 1:1 case), the FEF protasis IS the long-speech-intro frame; it gets its own line; the speech opens on the next line.

### Rule H17 — Genealogy / List-Formula Handling

**Grammatical basis.** Hebrew genealogies use formulaic constructions: *X חַי N שָׁנִים וַיּוֹלֶד אֶת־Y וַיְחִי X אַחֲרֵי הוֹלִידוֹ אֶת־Y M שָׁנִים וַיּוֹלֶד בָּנִים וּבָנוֹת וַיִּהְיוּ כָּל־יְמֵי X N+M שָׁנִים וַיָּמֹת* (the Gen 5 generational formula). Legal lists use repeated case-introduction frames (*וְכִי / אִם / לֹא*). Each list-member is one of the same kind of unit.

**Trigger.** Genealogical formula or list-formula context.

**Diagnostic.** Per Parallel-List Uniformity Principle: each generation/case member gets one line. Frame-fragments do not stand alone; the full member-content (X-lived-N-years-and-fathered-Y) is the atomic unit.

**Example.** Gen 5:6 *וַיְחִי שֵׁת חָמֵשׁ שָׁנִים וּמְאַת שָׁנָה וַיּוֹלֶד אֶת־אֱנוֹשׁ* → one line per Seth-generation member, not 4–5 lines for the formula's grammatical sub-parts.

**SCOPE:** Gen 5, Gen 10, Gen 11, Gen 36, 1 Chr 1–9, similar genealogical blocks. Legal lists (Lev 11 dietary, Deut 14 dietary, Deut 27 curses, Deut 28 blessings) per the same principle. Acrostic structures (Pss 119, Lam 1–4) — list-uniform within the acrostic-letter-stanza scope.

### Rule H18 — Clause-Nucleus Integrity (Verbless / Participial / Verb-PP-Complement)

**Grammatical basis.** Hebrew has no overt copula in present-tense verbless clauses (Joüon-Muraoka §154; Waltke-O'Connor §8.4; GKC §141). Subject and predicate sit in juxtaposition and form a single predication. Participial predicates (with or without obligatory complement) similarly fill the slot of a finite verb (JM §121; WO §37.6) and form one predication with their subject. Finite verbs that govern an obligatory PP-complement (*שָׁמַע ל*, *נָשָׂא עֵינַיִם אֶל*, *פָּנָה אֶל*) form one integrated predication with the complement (already in M2's body — extended here with explicit signature for validator detection). The mechanical te'amim-derived v1-baseline frequently splits subject from predicate-PP in verbless clauses and subject from participial predicate, over-fragmenting the basic predication. This rule names the default-MERGE behavior across the three sub-cases.

**Sub-rules:**

- **H18.1 — Verbless predicate integrity.** Subject (NP) + non-verbal predicate (NP / PP / Adj) with no copula. JM §154; WO §8.4. Default-MERGE for short cases.
- **H18.2 — Participial predicate integrity.** Subject (NP) + participial predicate (active or passive participle, with or without obligatory complement). JM §121; WO §37.6 (participle "fills the slot of a finite verb"). Default-MERGE for short cases.
- **H18.3 — Verb-PP-complement integrity (M2 corpus extension).** Finite verb + obligatory PP-complement (*שָׁמַע ל*, *נָשָׂא עֵינַיִם אֶל*, *פָּנָה אֶל*). Already in M2's body; extended here with explicit morpho-syntactic signature for validator detection.

**Trigger** (morpho-syntactic; no te'amim glyph references): line ends in NP not bearing finite-verb skeleton; next line begins with preposition (*עַל*, *אֶל*, *בְּ*, *לְ*, *מִן*, compound-prep) OR bare participle morphology (active or passive). Combined ≤8 prosodic words. NO finite verb on either line.

**Diagnostic.** When the trigger fires and no forced-no-merge exception below applies, MERGE the two lines into a single colometric unit expressing the verbless / participial / verb-PP predication. Combined-length check is a guardrail against over-merging into substantive-adjunct territory (justification 5); cases over 8 prosodic words are evaluated per-instance rather than mechanically merged.

**Forced-no-merge exceptions (cross-rule precedence — these win over H18):**
- H4 (vocative position).
- H9 (divine-title appositive in vocative scope).
- H14 (sentence-initial discourse particle *הִנֵּה* / *אַף* / *עַל־כֵּן* on next line).
- H15 (resumptive pronoun on next line — casus pendens).
- H16 (FEF *wayehi* protasis still open).
- M3 (bare-governing participle without complement).
- Heavy subject (relative clause attached to subject; ≥2 appositives; construct chain ≥3 deep).
- Heavy participial complement (DO + PP, ≥5 prosodic words on participial side).
- Sifrei Emet routing (Pss / Prov / Job 3:1–42:6).
- Embedded-poetry chapter list (Exod 15, Deut 32, Deut 33, Judg 5, 1 Sam 2:1–10, 2 Sam 22, Isa 12, Hab 3, Lam 1–5, Song 1–8, Eccl 3:2–8).
- Acrostic detection (Lam 1–4, Pss 9/10, 25, 34, 37, 111, 112, 119, 145, Pro 31:10–31, Nah 1:2–8).
- Both lines have a finite verb anywhere (parallelism territory, not verbless predication).
- Next-line preposition takes *לְ* + infinitive (justification 5 purpose-PP territory).

**Examples:**

- **MERGE candidate (Gen 1:2):** *וְחֹשֶׁךְ // עַל־פְּנֵי תְהוֹם* — verbless clause subject + locative predicate; combined 5 prosodic words; no fronted topic. H18.1 fires.
- **MERGE candidate (Gen 1:2):** *וְרוּחַ אֱלֹהִים מְרַחֶפֶת // עַל־פְּנֵי הַמָּיִם* — circumstantial-participial clause; participle + obligatory PP-complement. H18.2 fires.
- **PRESERVE-SPLIT (Deut 33:26):** *אֵין כָּאֵל יְשֻׁרוּן // רֹכֵב שָׁמַיִם בְעֶזְרֶךָ* — embedded-poetry chapter (Mosaic blessings); Deut 33 hard-skip applies. H18 does NOT fire.
- **PRESERVE-SPLIT (Lam 3:25):** *טוֹב יְהוָה לְקֹוָיו // לְנֶפֶשׁ תִּדְרְשֶׁנּוּ* — acrostic chapter; Lam 3 hard-skip applies. H18 does NOT fire.
- **PRESERVE-SPLIT (Pro 25:11):** *תַּפּוּחֵי זָהָב בְּמַשְׂכִּיּוֹת כָּסֶף // דָּבָר דָּבֻר עַל־אָפְנָיו* — Sifrei Emet routing applies. H18 does NOT fire. (Even if not routed Sifrei Emet, the next line begins with bare NP not prep / participle, so signature does not match.)

**Defensibility capture (mandatory):**

- **WHY:** Hebrew has no overt copula in present-tense verbless clauses; the te'amim mark prosodic chant pauses, not propositional boundaries. The mechanical te'amim-derived v1-baseline often splits subject from predicate-PP in verbless clauses and subject from participial predicate — over-fragmentation of the basic predication. Naming this as a closed rule prevents the over-fragmentation.
- **HOW WE KNOW:** Joüon-Muraoka §154 (verbless clauses), §121 (participial predicates), §156 (casus pendens exception); Waltke-O'Connor §8.4 (verbless clause word order), §37.6 (participial predicate as verb-equivalent); GKC §141 (nominal sentences). Corpus survey 2026-04-28 found 1,533 strict-signature candidates corpus-wide. Six-agent hostile audit (2026-04-28; verdict: REFINE-FIRST then PROCEED OPTION-A) confirmed grammatical basis and identified the closed-list of forced-no-merge exceptions above.
- **SCOPE:** All books except Sifrei Emet routing + embedded-poetry list + acrostic chapters. Does NOT apply when next line begins with finite verb (parallelism territory). Does NOT apply when subject or predicate is heavy (substantive-adjunct territory per justification 5).

**Note on architectural choice.** Option A (new H18) was chosen over Option B (extend M2). The cross-rule integrity audit identified Option B as closed-list smuggling per §2 scope diagnostic. WO §37.6's "participle fills the slot of a finite verb" is cited in H18.2's grammatical basis without nesting H18 under M2.

---

## §6 Validator Suite

Validators live in two subfolders reflecting the Layer 1 / Layer 3 split. Four active validators as of 2026-04-27:

**Layer 1 — Syntax validators** at `validators/syntax/` (generic Hebrew grammar checks; violations tagged `[MALFORMED]` — hard grammatical failures):
- `validate_maqqef_integrity.py` → Rule H1 (maqqef-group indivisibility). Gate-passed; STRONG findings feed the editorial work queue at Category A confidence.
- `validate_line_final_tokens.py` → Rule H1 sub-check + L1 proclitic-stranding rows from `data/syntax-reference/hebrew-break-legality.md` (conjunction-prefix וְ, prepositional-prefix, definite-article, direct-object-marker אֵת, negation, compound-prep stranded). Gate-passed; STRONG findings feed the editorial work queue at Category A confidence.

**Layer 3 — Colometry validators** at `validators/colometry/` (Tanakh-specific editorial-rule checks; violations tagged `[DEVIATION]`):
- `validate_construct_chain.py` → Rule H2 (construct-chain default). Functioning as a REVIEW-REQUIRED surfacer; STRONG threshold not yet cleared at corpus scale.
- `validate_speech_intro_framing.py` → Rule H5 (direct-speech framing default) + Rule H16 secondary (FEF wayehi-protasis interaction). Gate-passed on STRONG-MERGE findings; REVIEW-REQUIRED items go to per-item editorial judgment.

**Dashboard and gates.** `validators/run_all.py` is the validator dashboard — discovers all `validate_*.py`, runs each with `--json --v2`, aggregates per-validator finding counts. Run with `--baseline-check` to gate against `.baseline.json` (the regression reference). Two git hooks enforce the gate at commit time: the pre-commit hook (`validators/hooks/pre-commit`) runs `run_all.py --baseline-check` when editorial corpus / canon / validator files are staged; the commit-msg hook (`validators/hooks/commit-msg`) runs `check_canon_extensions.py` to require audit-evidence on any commit that extends the canon.

**Validator design constraint — no length caps on merge candidates.** Atomic-thought test is the gate, not line length. A long correctly-merged line is evidence that the original text contains a long single thought. Length is diagnostic (may trigger Category B/C review for unusually long results) but is never a mechanical gate.

**Validator output is a work queue, not a review queue.** When a colometry validator categorizes instances as `STRONG-MERGE-CANDIDATE`, `STRONG-SPLIT-CANDIDATE`, or similar unambiguous labels, those items are **application-ready** — Category A by default per §2 "Mechanical-rule authority." Only items the validator itself flags as `REVIEW-REQUIRED` require per-item editorial judgment.

### Gold-Standard Regression Fixtures

After any pipeline-changing pass (new rule, reformatter update, build script change, mechanical sweep), verify output against these chapters before committing. Each fixture is chosen for diagnostic specificity; if a chapter breaks, it identifies which rule class regressed.

**Initial fixture set (to be expanded as the corpus grows):**

| Fixture | Register | Primary rules tested |
|---|---|---|
| **Jonah 1** | Prose narrative | Rule H5 direct-speech framing (4 instances), Rule H16 FEF wayehi protasis, Rule H3 wayyiqtol clause-head policy |
| **Jonah 2** | Sifrei Emet poetic | Structural justification 1 parallel members in psalmic poetry; FEF wayehi protasis at 2:1 |
| **Genesis 1** | Prose narrative + creation formula | Rule H1 maqqef-group, Rule H17 list-formula (the days-of-creation formula), Parallel-List Uniformity Principle |
| **Deuteronomy 27** | Legal list | Parallel-List Uniformity Principle (the *אָרוּר* curse-series), Authorial Asymmetry test |
| **Psalm 1** | Sifrei Emet wisdom | Sifrei Emet stichometry, te'amim-as-evidence in poetic register, M1 bonded-pair tests on common psalmic doublets |
| **Exodus 15** | Embedded prose-cantillated poetry (Song of the Sea) | Embedded-poetry skip-gate for H18; Authorial Asymmetry; structural justification 1 (parallel bicolon) |
| **Deuteronomy 32** | Embedded prose-cantillated poetry (Ha'azinu) | H18 hard-skip (densest embedded-poetry chapter in Torah); mixed verbal/verbless bicola |
| **Deuteronomy 33** | Embedded prose-cantillated poetry (Mosaic blessings) | H18 hard-skip; **Deut 33:26 canonical regression case** (verbless-NP // bare-participle must NOT merge) |
| **Judges 5** | Embedded prose-cantillated poetry (Song of Deborah) | Long embedded-poetry block; gate completeness across full chapter |
| **2 Samuel 22** | Embedded prose-cantillated poetry (≈ Ps 18) | Cross-system A/B comparison with Ps 18; tests whether validators track poetry vs. accent-system |
| **Habakkuk 3** | Embedded prose-cantillated poetry (*תְּפִלָּה* superscription) | Lexical-anchor register detection; embedded psalm in prose-route prophetic book |
| **Lamentations 3** | Acrostic poetry routed prose | H18 acrostic-detection skip; **Lam 3:25 canonical regression case** (verbless + prep must NOT merge) |
| **Proverbs 25** | Sifrei Emet wisdom couplets (NP \|\| PP density) | Confirms Sifrei Emet hard-skip holds at corpus scale for V2 (Pro 25:11 NP-anchor pair); the *תַּפּוּחֵי זָהָב* style |

**Verification procedure:** diff the rebuilt `books/*.html` for each fixture chapter against the committed baseline after any pipeline change. Any line-count delta or content delta requires inspection before the commit lands.

**Next candidate on the bench:** Ruth 1 (pure prose validation, post-Jonah next-book scoping). Add as sixth fixture when Ruth editorial pass begins.

---

# Part III — Process and Meta

*Read §7 before any canon-touching commit. §8 is the chronological reasoning trail.*

## §7 Change Protocol

*Purpose: **dual-natured** — mandatory-read before canon edits (operational), and the change-protocol rationale (philosophical). §7's Mandatory-audit trigger list is load-bearing operational content.*

Proposals to change an existing rule, add a new rule, or cull a rule must:

Apply the §2 scope/precedence/closed-list/carve-out diagnostic first — any proposal matching any of those four patterns is Category B by default and almost always triggers one of the categories below.

1. **State the Hebrew syntactic / orthographic / Masoretic fact.** If you cannot cite it (Joüon-Muraoka, Waltke-O'Connor, GKC, Yeivin, Wickes), the proposal is insufficient.

2. **Provide corpus evidence.** Worked examples from the actual text — not hypotheticals.

3. **Survive adversarial audit.** For proposals matching any of the following **mandatory-audit triggers**, an adversarial audit (hostile agent or equivalent external skeptical review) MUST be dispatched and its findings must be reflected in the commit. Skipping audit on a triggered proposal is a protocol violation.

   **Mandatory-audit triggers (12 categories — ported from BoFM 2026-04-26 / GNT 2026-04-24, both projects converged on the same list):**

   1. **New named rules / sub-clauses / categories** — including precedence cross-references between rules. Shape-matches feel-tests, enumerated lists, and subjective carve-outs particularly.
   2. **Rule status promotions** — *proposed* → settled. Removes the hedge; stakes increase.
   3. **Spot-check-based proposals** — any canon claim resting on less than full-corpus-sweep evidence. Claims like "I checked 30 instances and the pattern is uniform" must be verified by full-corpus classification before codification.
   4. **Reclassification of canon-recorded Category B/C items** — once a verse, rule, or item is recorded as Category B/C in canon §8 or pending lists, subsequent sessions cannot silently reclassify it under a different rule-framing.
   5. **Rule deletions or SCOPE narrowings that retire live applications** — retiring a rule is as high-stakes as adding one; audit prevents discarding legitimate work.
   6. **Mechanical signature / validator changes under settled rules** — adding a verb class, refining a trigger, or changing validator conditions silently expands or contracts rule coverage.
   7. **Corpus sweeps ≥5 instances under a settled rule** — a sweep asserts "the rule fires cleanly here" N times; the collective scope-claim needs audit even when individual instances are Category A.
   8. **Canonical example additions to settled rules** — examples shape rule interpretation; a poorly-chosen example silently redefines the rule.
   9. **Meta-rule changes to §7 itself** — changes to this protocol must be audited.
   10. **Discipline-shifting memory file additions** — new `feedback_*.md` or `project_*.md` files that shape how Claude approaches canon work are behaviorally-governing, not just observations; they need the same scrutiny as canon.
   11. **Cross-project imports** (BoFM ↔ GNT ↔ Tanakh) **or recoveries from retired canon** — provenance from a sibling project or older version is not validation; the imported claim must have Tanakh-corpus evidence independent of its source.
   12. **Corpus-fit verification — post-codification AND post-detection.**
       - **(a) Post-codification.** When a new rule, sub-clause, or named pattern is codified, the rule is **not "closed" until a corpus-wide goal-fit audit has confirmed (i) all eligible instances conform OR (ii) all residuals are explicitly enumerated** in §8. Codifications based on partial-corpus evidence are vulnerable to undercount; the canon's empirical "HOW WE KNOW" claim must be verified against full-corpus reality.
       - **(b) Post-detection.** This trigger ALSO fires when Stan-eyeball or any audit surfaces a violation of an **existing** (settled) rule. Application drift accumulates on long-codified rules through ongoing corpus modifications and prior partial-sweep gaps. When a violation is detected, schedule a same-rule full-corpus re-sweep within the same session if practical, or as the next session's first task.
       - **Audit dimensions to consider:** goal-fit (does corpus implement codified rules), application-consistency on formulaic phrases (*וַיְהִי*, *לֵאמֹר*, *כֹּה אָמַר יְהוָה*, *אַשְׁרֵי*), application-consistency on parallel-list constructions (genealogies, beatitudes, woe-series, blessed-series, conditional pairs — see §1 Parallel-List Uniformity Principle), self-consistency (cross-references, defensibility triplets), smuggling (judgment-handoff failure mode). Dispatch in parallel by default.

   **Audit dispatch protocol — parallel by default.** When a proposal triggers multiple audit dimensions, dispatch all in a single message with multiple Agent tool calls. Sequential only when audit A's verdict determines whether audit B should run. Parallelization substantially reduces friction and lowers the effective cost per audit.

   **Audit-skippable categories (all must hold for the proposal to bypass audit):**
   - Category A mechanical corpus edits per already-codified rules (sweep-scale ≥5 still triggers #7 regardless)
   - Typo fixes, cross-reference updates that don't assert precedence, internal formatting cleanups
   - Deletions of items already reverted in the same session (audit-trail cleanup)
   - Defensibility-capture additions (WHY/HOW WE KNOW/SCOPE) to already-settled rules without changing the rule's scope

4. **Apply uniformly.** If the rule fires in one place, run the validator or equivalent sweep to catch every instance. Sedimented inconsistency is the primary failure mode.

5. **Defensibility capture (prospective only).** Every new rule, sub-rule, or merge-override added to the canon must carry three elements:
   - **WHY** — the editorial reason the rule exists (what failure mode does it prevent, what pattern does it reveal)
   - **HOW WE KNOW** — corpus evidence + adversarial validation (worked examples, sweep counts, audit findings)
   - **SCOPE** — where the rule applies, where it doesn't (named exclusions, interaction with other rules)
   Retroactive audit of older rules is optional, not required. The purpose is to ensure each new rule is documented well enough that a future reviewer can judge whether it earns its place.

6. **Re-evaluate deferred items when the rule-set changes.** When a rule is adopted or refined, any corpus item previously classified as `REVIEW-REQUIRED` or `deferred-editorial` must be re-evaluated against the updated rule-set before being carried forward as still requiring Stan's judgment. Carrying forward stale classifications wastes session time and hides cases the current rule-set now handles cleanly.

7. **Update this canon.** Append a dated entry to §8 Update Log and add/modify the relevant rule section. Never edit history silently.

**Self-consistency audit trigger.** When a session adds ≥2 new canon subsections, rules, or merge-overrides, run a light self-consistency audit before wrap: check that (a) all new cross-references resolve, (b) no new rule contradicts an existing rule, (c) all three defensibility elements (WHY/HOW WE KNOW/SCOPE) are present for each addition.

### Proposed-rule adoption protocol

A rule labeled *proposed* is a rule awaiting corpus verification. "Proposed" is a testable state, not a hedging license.

**Adoption criteria.** A proposed rule is adopted when its first corpus sweep produces **≥80% clean categorization** — i.e., 80%+ of matched instances resolve to unambiguous SPLIT or MERGE decisions without heuristic ambiguity. Ambiguous residue (`REVIEW-REQUIRED`) ≥20% signals the rule needs refinement before adoption.

**Sweep-then-decide workflow.**
1. Write validator implementing the rule's conditions.
2. Run against full corpus.
3. If clean ≥80% → apply clean decisions mechanically (Category A per §2), remove "proposed" label, append adoption entry to §8 Update Log.
4. If clean <80% → identify the ambiguity pattern, refine the rule with an explicit sub-clause, re-run.
5. Repeat until clean ≥80%, then adopt.

**Do not flag clean categorizations for per-item review.** A proposed rule whose conditions are met is as authoritative as an adopted rule on those specific instances; the "proposed" label only gates corpus-wide sweep confidence, not per-instance application.

---

## §8 Update Log

*Purpose: **dual-natured** — chronological reasoning trail. Recent entries documenting active-rule provenance are operationally referenced; older entries are historical narrative. **Do not rewrite or remove dated entries.** Historical entries retain their original wording; silently revising them falsifies the chronological trail.*

### 2026-04-26 — Intro structure brought into parity with GNT canon's 2026-04-25 voice-cleanup passes

The Tanakh canon was written 2026-04-26 using BoFM v2.0 as architectural template. The GNT canon ran three voice-cleanup passes on 2026-04-25 (commits 514f15d, c787418, b86c13a) that the Tanakh canon didn't inherit because BoFM v2.0 still carried the older HUMAN/ROBOT structure. Stan flagged the gap.

**Edits applied:**
- D1: HUMAN/ROBOT "How to use this document" section replaced with content-led "What is this document?" + Reader's guide by purpose (mirrors GNT lines 31–47).
- D2: Stripped "for humans understanding what we are doing" parenthetical from Part I header; same for Part II/III headers; added brief italic Part-level epigraphs.
- D3: Added PURPOSE italics header to §0 opener.
- D4: Added PURPOSE italics headers to §2, §3, §5, §7, §8 openers (parallel to existing §1 header).
- E2: Added Skousen-dictation-specific rationale clarification to §0 Origin subsection.

WHY: Stan flagged that the GNT canon is fresher than what the Tanakh rewrite was based on, and asked whether the Tanakh canon's intro matches the fresher GNT structure. It didn't. These edits bring intro architecture and PURPOSE-header discipline into parity. No methodological content changed.

HOW WE KNOW: 2026-04-26 background subagent re-read the GNT canon end-to-end against the current Tanakh canon and produced a structured 4-edit diff with file:line citations.

SCOPE: intro architecture + PURPOSE headers + Origin paragraph factual accuracy. No rule content modified, no Hebrew-specific sections changed, no methodological position revised.

### 2026-04-26 — Canon v1.0 written from scratch

The predecessor stub canon (231 lines, established 2026-04-25) was scrapped and the canon rewritten from scratch using BoFM v2.0 as architectural template, GNT canon as content where BoFM is silent or where GNT's formulation is sharper, and Hebrew-specific content extracted from the stub or written net-new.

**Why:** Granular reading of both sibling canons end-to-end (2026-04-26) found the stub:
- Carried "te'amim-prior with override discipline" as central commitment, which contradicts the converged sibling principle that **editorial overlays must not have deterministic force**. The te'amim are the Hebrew analog of NA28 punctuation (sibling GNT) and Pratt's 1879 BoFM versification — late editorial overlays.
- Carried the four-criteria framing both canons retired (BoFM 2026-04-19, GNT 2026-04-20). Breath was empirically retired by both projects after testing showed zero cases where breath was the sole deciding factor.
- Framed discipline as "override warrants against an authority" instead of the converged "positive justification under atomic-thought prior."
- Lacked every architectural element both sibling canons converged on after ~13 months of iteration: three forces, closed-list structural justifications, closed-list merge-overrides, Decision Procedure / Application Order, Category A/B/C autonomy boundary, mandatory-audit triggers, defensibility-capture enforcement, gold-standard regression chapters, withdrawn-proposals discipline.
- Lacked the rhetoric-bandwagon failure-mode awareness, which is the highest-risk failure mode for the Tanakh project specifically given Hebrew's deep scholarly literature on parallelism (Lowth/Kugel/Berlin/Dobbs-Allsopp), chiasm, and other rhetorical figures.

**Stan-validated 2026-04-26** after explicit pushback against earlier hedging that framed the te'amim demotion as a "tradeoff" or "Stan-call between branding and defensibility." Per `feedback_no_false_choice_framing.md`, fixing wrong methodology is not a tradeoff — it is the work.

**Extracted from the predecessor stub (Tanakh-specific decisions retained):**
- Textual posture (Leningrad-only, no LXX/DSS/Samaritan/Targums/Peshitta/Vulgate, MAM as reference). Now §0.1.
- Two-accent-systems reality (prose 21 books, Sifrei Emet for Pss/Prov/poetic Job, Job 3:1–42:6 boundary). Now Rule H8 framing + Te'amim Inventory Reference §4.2 (TODO).
- Petucha/setuma reality. Now §1 "Petucha / Setuma Are Evidence, Not Authority" + Rule H12.
- Maqqef. Now Rule H1 (Layer 1 break-legality fact).
- Ketiv/Qere policy. Now Rule H6 with sub-categories H6.1–H6.5.
- Glossary content extracted to §9.

**Imported from sibling canons:**
- Three-forces framework + structural justifications + merge-overrides + Decision Procedure / Application Order: from BoFM v2.0 §1 / GNT canon §1–§2.
- Container-not-originator framing: from GNT canon §1.
- Imposing vs. Revealing scope discipline + reaching-for-split warning + fronting paradox: from GNT canon §1.
- Punctuation/versification not break signals: from both canons, adapted to add te'amim explicitly to the same category.
- Cross-Verse Continuity Merge: from GNT §3.17 (already imported into BoFM 2026-04-22). Now Rule H10.
- Authorial Asymmetry Principle (R28): from both canons. Now §1 subsection.
- Parallel-List Uniformity Principle: from BoFM 2026-04-26 (most recent addition).
- N=2 Adjudication Principle: from BoFM 2026-04-23.
- Autonomy Boundary (Categories A/B/C) + Mechanical-rule authority + Scope/precedence/closed-list/carve-out diagnostic: from both canons. Now §2.
- §7 Change Protocol with 12 mandatory-audit triggers + audit-skippable + parallelization default + defensibility-capture + proposed-rule adoption protocol: from both canons (BoFM 2026-04-26 most recent).
- FEF treatment for *wayehi* protases: explicitly named in GNT canon §5 as the Hebrew paradigm. Now Rule H16.
- Validator-output-as-work-queue + validator-design-no-length-caps: from BoFM §6.

**Hebrew-specific net-new sections (no sibling source):**
- §1 "The Te'amim Are Not a Structural Prior" — the central methodological correction. Frames the te'amim as evidence-not-authority parallel to NA28 punctuation in GNT and Pratt's versification in BoFM.
- §1 Hebrew anchor inventory (in the Generative Principle subsection) — Hebrew verbless clauses ARE atomic thoughts; do not import the Greek "every line needs a verb" instinct.
- Rule H1 maqqef-group indivisibility (Layer 1 fact) with the joining-glyph rendering note.
- Rule H2 construct-chain default.
- Rule H3 vav-consecutive clause-head policy with bonded-pair / speech-intro-pair / hendiadic exceptions.
- Rule H4 vocative handling (Hebrew lacks morphological vocative case; address-position diagnostic).
- Rule H5 direct-speech framing default with short-vs-long *לֵאמֹר* test.
- Rule H6 Ketiv/Qere policy with sub-categories H6.1–H6.5 (perpetual qere, qere-ve-la-ketiv, ketiv-ve-la-qere, sebirin, tiqqunei sopherim).
- Rule H7 complement integrity for Hebrew verb classes.
- Rule H8 te'amim as evidence (operational application of the §1 framing).
- Rule H9 divine-title appositives.
- Rule H10 cross-verse continuity merge (GNT-imported, Hebrew-specific examples).
- Rule H11 tifcha-as-servant-of-atnach (Wickes 1887; corrects predecessor stub §2.1 default-breaker list).
- Rule H12 petucha/setuma rendering with tradition-disagreement protocol.
- Rule H13 special letters (suspended/inverted nuns, large/small letters, scriptio plena/defectiva).
- Rule H14 discourse particles (*הִנֵּה, נָא, אָז, עַתָּה, וְעַתָּה, לָכֵן, עַל־כֵּן, אַף*).
- Rule H15 casus pendens / left-dislocation.
- Rule H16 FEF wayehi protasis.
- Rule H17 genealogy / list-formula handling.
- Layer 1 reference pointer to `data/syntax-reference/hebrew-break-legality.md` (file TODO; first-pass row inventory listed in §4.1).
- Te'amim Inventory Reference pointer to `data/syntax-reference/teamim-inventory.md` (file TODO; will correct the §3.2 factual errors of the predecessor stub: tzinnor = positional zarqa, mehuppakh-legarmeih is conjunctive-with-paseq, revia mugrash is positional revia).

**Adjudicated decisions captured (do not relitigate):**
- Three criteria not four (no breath) — see `feedback_no_breath_criterion.md`.
- Te'amim are evidence-plus-starting-draft, not authority — locked in §1 "The Te'amim Are Not a Structural Prior."
- Atomic thought is the prior — locked in §1 Generative Principle.
- Parallelism is evidence, not a structural prior — locked in §1 "Parallelism Is Not a Structural Prior." The Lowth/Kugel/Berlin/Dobbs-Allsopp debate is real and substantial; the project does not take a position in it because parallelism's status as evidence-not-authority is the same status the te'amim hold, and the framework is symmetric.

**Follow-up work (carry-forwards, not part of this commit):**
- Update `CLAUDE.md` and `README.md` to reflect new framing (drop te'amim-prior, drop four-criteria, drop breath, point to canon).
- Audit and update `handoffs/` for cross-references that assume the predecessor framing. Most likely candidates: `handoffs/01-project-overview.md`, `handoffs/03-architecture.md`, `handoffs/04-editorial-workflow.md`.
- Create `data/syntax-reference/hebrew-break-legality.md` shape-capped table (Layer 1 reference).
- Create `data/syntax-reference/teamim-inventory.md` (te'amim disambiguation reference, correcting predecessor §3.2 factual errors).
- Update `scripts/parse_teamim.py` to reflect Rule H8's de-authority framing — the script still produces v1-he-baseline as the editor's starting draft (no functional change), but its output is no longer "the structural prior."
- Update `scripts/parse_teamim.py` to reflect Rule H11 — tifcha-as-servant-of-atnach mechanical adjustment (raise its evidence weight; remove or sub-condition the tifcha tier-2 default-breaker behavior).

**Adversarial audit dispatched:** three parallel Opus subagents on 2026-04-26 (GNT-canon mining, BoFM-canon mining, Hebrew-realities hostile audit). Reports synthesized into the canon-revision plan; this v1.0 rewrite is the implementation. Per §7 trigger #11 (cross-project imports), each imported architectural element was vetted for Tanakh-corpus applicability during the rewrite.

### 2026-04-26 — Directory rename: v1-teamim → v1-he-baseline; all canon path references updated

**Summary:** Renamed `data/text-files/v1-teamim/` to `data/text-files/v1-he-baseline/` and updated all eight path and prose references in this canon accordingly.

**WHY:** The directory name `v1-teamim` carried the te'amim-prior implication that the canon v1.0 rewrite eliminated. The directory's role is "starting draft for editorial work" — not "te'amim-prior baseline." Renaming to `v1-he-baseline` aligns directory-name framing with canon framing and achieves symmetry with sibling tier names (`v0-eng-baseline`, `v0-translit-baseline`, `v1-eng-interlinear`, `v1-eng-gloss`, `v1-translit`), where the tier prefix encodes position in the pipeline and the suffix encodes content/tradition — not the generation mechanism.

**HOW WE KNOW:** Stan flagged the inconsistency directly: the old name implies the te'amim are the authoritative basis of the draft, which is precisely the framing the canon v1.0 rewrite retired.

**SCOPE:** Directory rename (`data/text-files/v1-teamim/` → `data/text-files/v1-he-baseline/`) + all path references in this canon + carry-forward TODO in §8 (scripts/parse_teamim.py update). Path references in `scripts/`, `handoffs/`, `CLAUDE.md`, and any memory files referencing the old directory name are carry-forward work for the same session.

### 2026-04-27 — Directory layout: tier subfolders

`data/text-files/` restructured so each pipeline tier (v0, v1, v2, v3, v4) gets its own subfolder. Previously each tier-layer combination was a top-level directory (e.g., `v1-he-baseline/`, `v2-eng-interlinear/`); now they nest under `vN/` (e.g., `v1/he-baseline/`, `v2/eng-interlinear/`). The tier-name identity strings (v1-he-baseline, v2-he-syntax, etc.) are unchanged — only the filesystem layout. Canon path references updated throughout.

**WHY:** directory layout was getting unwieldy as v2 (and eventually v3) were added — 14+ top-level tier directories cluttered `data/text-files/`. Subfolder grouping makes the tier structure visible at a glance.

**HOW WE KNOW:** Stan flagged the clutter directly 2026-04-27 ("create a subfolder for v0 folders, etc.").

**SCOPE:** filesystem layout + path references in scripts, validators, canon, tracked docs. Tier-name identities unchanged. apply_v2/apply_v3 ADOPTED_VALIDATORS gates and decision-procedure semantics unchanged.

### 2026-04-27 — Tier collapse: 5-tier pipeline → 3-tier pipeline

Pipeline simplified from **v0 → v1 → v2-he-syntax → v3-he-colometry → v4-editorial** (5 tiers) to **v0 → v1 → v2** (3 tiers). The intermediate auto-apply tiers (v2-he-syntax via `apply_v2.py`; v3-he-colometry via `apply_v3.py`) are retired. The editorial gold standard moves from `data/text-files/v4/editorial/` to `data/text-files/v2/heb/`; the parallel per-word layers move from `data/text-files/v4/{eng-interlinear,eng-gloss,translit}/` to `data/text-files/v2/{eng-interlinear,eng-gloss,translit}/`. Path references throughout this canon, scripts, validators, hooks, handoffs, and CLAUDE.md updated accordingly.

**WHY:** the auto-apply tiers added pipeline complexity without adding capability. Their function was to auto-apply STRONG-tagged validator findings as a pre-editorial mechanical pass; that work can be done equivalently inside the editorial pass with the same Category A/B/C reasoning the canon already governs (§2 Mechanical-rule authority). `apply_v3.py` was a passthrough (empty `ADOPTED_VALIDATORS` — no Layer 3 validators had cleared the ≥80% adoption gate); `apply_v2.py` had two validators cleared, but their findings (~2 corrections per chapter on Jonah) sit on the editorial work queue without meaningful cost saving. The closed-list rule set (H1, H2, H5, H7, H11, H16) is not the mechanical-error surface that motivated mechanical-tier expansion in sibling projects (where ~10–12% error rates emerged from open-ended pattern-discovery passes); the canon's autonomy boundary already bounds the mechanical surface. Two tiers (baseline + editorial) are sufficient.

**HOW WE KNOW:** the tier collapse was identified in the 2026-04-27 gating-architecture session as a carry-forward (session-notes pt2 carry-forwards: "Tier collapse v0-v4 → v0/v1/v2"), proposed by Claude on grounds of validator-adoption observability (apply_v3 had been a passthrough since inception) and accepted by Stan in principle. Executed as a comprehensive cleanup in the 2026-04-27 tier-collapse-cleanup session, with the file moves landing first (commit `3c6282a`), followed by the script/validator/path updates (commit `7303f28`), then the documentation propagation (this commit).

**SCOPE:** removed scripts (`scripts/apply_v2.py`, `scripts/apply_v3.py`, `scripts/lib/apply_pipeline.py`, `scripts/lib/__init__.py`, empty `scripts/archive/`); removed reports (`data/reports/v2/`); moved Hebrew gold-standard and parallel-layer files from `v4/` to `v2/`; updated build cascade (`scripts/build_books.py`) from 4-tier to 2-tier; updated validator path constants (V4_DIR → V2_DIR; --v4 flag → --v2); updated pre-commit hook regex; updated all canon, handoff, README, and CLAUDE.md prose. Validator suite continues as before; STRONG-tagged findings now feed the editorial work queue directly. Decision-procedure semantics, three forces, four merge-overrides, structural justifications, autonomy boundary — all unchanged.

**Audit dispatched:** stan-authorized comprehensive cleanup per parent-agent amplification (memory `feedback_purge_stale_framing_comprehensively.md` — methodological reframings must propagate through directory names, filenames, identifiers, scripts, comments, and prose). The amplification specified: "all the remnants and loose ends of our clean up should be enforced throughout."

### 2026-04-27 — Carry-forwards from 2026-04-26 canon v1.0 write — closure

The following carry-forwards listed in the 2026-04-26 §8 "Canon v1.0 written from scratch" entry are now complete:

- **`data/syntax-reference/hebrew-break-legality.md` (file TODO)** — file created 2026-04-27; shape-capped table of Layer 1 break-legality rows populated with per-rule mapping (H1, H2, H7, H9, H11, H14, H15, H16 + other-above-surface rules). Status: populated and active; §4.1 references it correctly.
- **`data/syntax-reference/teamim-inventory.md` (file TODO)** — file created 2026-04-27; 82 lines covering full prose and Sifrei Emet accent inventories with glyph/name/positional-function/prose-poetic-equivalence disambiguation. Factual errors from predecessor stub (tzinnor ≠ zarqa, mehuppakh-legarmeih, revia mugrash) corrected. §4.2 status updated from "TODO" to "populated."
- **`scripts/parse_teamim.py` docstring framing** — docstring already carries correct Rule H8 evidence-not-authority framing as of the 2026-04-27 session (confirmed by inspection); the Rule H11 tifcha-as-servant mechanical adjustment carry-forward remains open (script behavior unchanged; editorial work queue absorbs the finding).
- **Validator suite "planned, not yet built"** — validators are now built and active (four validators across `validators/syntax/` and `validators/colometry/`). §6 updated 2026-04-27 to reflect as-built reality.

Remaining open carry-forward: Rule H11 parse_teamim.py mechanical adjustment (tifcha-as-servant behavior in the v1-he-baseline generator). This is an improvement-path item, not a correctness blocker — the editorial pass at v2/heb absorbs the finding.

### 2026-04-28 — Rule H18 Clause-Nucleus Integrity adopted; te'amim-centric validator architecture rejected

**What landed:**
1. New Rule H18 (Verbless / Participial / Verb-PP-complement Clause-Nucleus Integrity) added to §3 and §5. Three sub-rules H18.1 / H18.2 / H18.3.
2. §1 "The Te'amim Are Not a Structural Prior" extended with Validator-architecture corollary: validator triggers must be Hebrew morpho-syntactic, never te'amim-derived.
3. §6 fixture set expanded by 8 chapters (Exod 15, Deut 32, Deut 33, Judg 5, 2 Sam 22, Hab 3, Lam 3, Pro 25) — closes embedded-poetry blind spot.
4. Proposed `validate_tifcha_servant.py` (te'amim-centric architecture) was killed in design after Stan's discomfort flag and 6-agent hostile audit findings.

**Why:** Stan flagged Genesis 1:1 and 1:2 as over-split; corpus survey confirmed pattern at scale (~1,533 strict candidates for verbless / participial; ~16,835 candidates for tifcha-servant signature). Initial proposal included a tifcha-servant validator triggering on the TIPHA glyph; Stan's discomfort with "overreliance on Masoretic punctuation cues for determining thought line breaks" surfaced the architectural problem: even framing a validator as "demoting te'amim by merging across them" operationally centers them as the primary signal. The validator-architecture corollary makes explicit what §1's te'amim demotion already implied.

Hostile audit findings on the original tifcha-servant proposal: the canon's own H11 fixture (Jonah 1) DISCONFIRMED the proposal — 3 of 4 candidate sites in the gold-standard book were SPLIT by Stan's hand-edit decisions (1:4 *בַּיָּ֑ם*, 1:4 *לְהִשָּׁבֵֽר*, 1:5 *מֵֽעֲלֵיהֶ֑ם*). STRONG-MERGE auto-application would have inverted documented gold-standard.

**HOW WE KNOW:** Six-agent parallel hostile audit dispatched 2026-04-28 (Opus, multi-dimensional): hostile audit on tifcha-servant + verbless-clause; Wickes / Yeivin grounding deep-dive; JM / WO grammar deep-dive; Sifrei Emet poetic-bicolon danger zone; cross-rule integrity. Verdicts adjudicated. Architectural choice (Option A new H18 vs. Option B extend M2) decided by cross-rule integrity audit's identification of Option B as closed-list smuggling per §2 scope diagnostic.

**SCOPE:** H18 covers all books except Sifrei Emet routing + embedded-poetry list + acrostic chapters. Validator deployment is REVIEW-REQUIRED-only initially; promotion to STRONG-MERGE awaits at least one hand-edited Tanakh book beyond Jonah showing ≥80% editor-merge agreement on a specific subcase.

**Audit dispatched:** six-agent parallel adversarial audit 2026-04-28; verdicts and design corrections cited above.

### 2026-05-01 — ATU (atomic thought unit) terminology migration applied (parallel to GNT canon §10 same-date entry)

The shorthand "sense-line" carried unwanted intuitive baggage from prosodic / Skousen-typographic registers and obscured the load-bearing concept (the unit of thought, not the surface line). The GNT canon ran an ATU migration on 2026-05-01 that replaced "sense-line" with "atomic thought unit (ATU)" / "ATU" through active-prose §0 / §1 / §3 / §5 sections and codified the term as the canonical reference. This entry records the same-date migration applied to the Tanakh canon's §0 Mission sentence — the historical-narrative §8 entries and §10 entries retain their original "sense-line" wording per the do-not-rewrite-dated-entries rule (now codified in the §8 / §10 header italics). Forward references in active prose use ATU; historical references retain their original term.

The three-repos-same-provenance coordination matters: BoFM, GNT, and Tanakh canons all share the methodology lineage, so the term-migration date should match across all three for cross-repo readers. Without this entry the Tanakh §8 had no record that the migration happened.

**Audit-skippable per §7** — terminology migration without scope change; the rule (atomic thought as one of the three editorial criteria) is unchanged. No closed-list extension; no scope claim; no precedence claim; no carve-out addition. Defensibility-capture only.

### 2026-05-02 — Path 1: Propositional completeness as canonical atomic-thought criterion; H5 short-framing-default retired; H5b Speech-Act Announcement Default added; 3 C's codified as governing values

**What landed:**
1. New §0.2 **Governing Values — The Three C's** (clarity, consistency, comprehensiveness) codified as decision criteria for canon revisions. Stan-articulated during this session; codified to make the framework explicit for future canon work.
2. New named operational test: **Propositional Completeness Test** (§5.0), positioned as the canonical operational form of atomic thought. Distinguishes propositional completeness (anchor + valence-closed-on-line) from **informational completeness** (whether the reader has learned everything about the event), and explicitly retires informational completeness as a canon test.
3. **Rule H5 revised**: short-framing-default merge stance retired. Default is split between announcement frame and quoted content regardless of frame length. Length now governs visual display of the announcement, not merge licensing. Narrow scope-economy carve-out preserved as Category B / REVIEW-REQUIRED for dialogue-chain visual rhythm; mechanical merge prohibited.
4. **New Rule H5b — Speech-Act Announcement Default** added to §3 and §5. Operationalizes §1 SJ3's "announcement and quoted content are separate cognitive frames" as a closed-list rule with explicit forced-merge exceptions (H1, H7-non-speech, narrow scope-economy carve-out). Worked examples include *כֹּה אָמַר יְהוָה*, *נְאֻם־יְהוָה*, the Jonah 1:1 FEF intro, prophetic-vision frames.
5. §3 Quick-Reference Rule Table updated: H5 row description rewritten; H5b row added.
6. §4.1 Rule-to-Table Mapping updated: H5b cites the same "Speech-frame boundary" Layer 1 row as H5.
7. §5 H7 verb-class table — "Speech (introducing speech)" row rephrased to clarify: merges with speech-intro frame components (recipient PP, *לֵאמֹר* marker) per H5; does NOT merge with quoted content per H5b.
8. **Jonah 1 (gold standard) re-edited** to apply H5b retroactively: lines 1:6, 1:9, 1:10, 1:12 split to separate speech-frames from content.
9. Specs/validators retired/refined in this session's Commit B (separate commit): see git history for `m4_solo_speech_verb.yaml`, `validate_speech_intro_framing.py`, and ADOPTED_VALIDATORS in `apply_validators.py`.

**WHY:** §1 SJ3 ("speech-act announcement... announcement and quoted content are separate cognitive frames") and §1 M3 contrast paragraph ("finite speech-act formulas... ARE complete speech-act predications — the speech act itself is the content") are load-bearing propositional-completeness commitments. Pre-revision H5's short-framing-default merge contradicted both. The `m4_solo_speech_verb` spec's "propositionally empty without its complement clause" framing extended the contradiction into the cascade engine. Stan flagged the tension surfacing on Isa 40:6 (a *וְאָמַר // קְרָא* split that the cascade was repeatedly attempting to merge under m4-solo-speech-verb but Stan's editorial judgment held as split per SJ3). The contradiction is principled, not edge-case: the canon's two stances cannot both be true. Path 1 resolves in favor of §1's propositional-completeness commitment; informational-completeness reasoning is named and retired as a non-canonical criterion. Per the newly-codified 3 C's: forward-only Path 1 fails on consistency (corpus contradicts canon) and comprehensiveness (only future edits comply); RETROACTIVE Path 1 (with carve-outs) realizes all three values.

**HOW WE KNOW:** Four parallel adversarial-audit dispatches 2026-05-02 (canon revision drafter Opus, FP/FN sampling Opus on 50 stratified candidates, spec impact survey Sonnet, M2 verbless-predication audit Sonnet). FP/FN audit verdict: 75-78% CLEAN, 17-20% BORDERLINE, 3-5% PROBLEM with PROBLEM concentrated in three tractable classes (Job answering-formula, homograph guard for ויוסף/ויען/וידבר, Sifrei Emet meter). Spec impact survey identified 8 file modifications with only 5 substantive behavioral changes. Canon revision drafter produced full §1/§5/§5.0/§8 text. M2 verbless-predication audit identified a critical design flaw in the proposed `is_verbless_predication` helper (inadequate PP-prefix exclusion) and recommended 3 refinements that bring FP rate below 2%.

**SCOPE:** All books — speech-act announcement is register-invariant. Affects: H5 rewrite, new H5b, §5.0 new test, §0.2 new governing-values section, §3 table, §4.1 mapping, §5 H7 row rephrasing, Jonah 1 re-edit. Specs/validators changed in Commit B: `m4_solo_speech_verb.yaml`, `validate_speech_intro_framing.py`, `apply_validators.py` ADOPTED_VALIDATORS, `m4_c_solo_action_verb.yaml`/`m4_d_*`/`m4_e_*` retag M4→M2, baseline.json reset (significant finding-count changes expected). Does NOT affect: H7 (cognition/volition/causative *כִּי* complementation — orthogonal), H18 (verbless/participial — orthogonal), H3 (wayyiqtol clause-head — H5b reinforces H3 for speech wayyiqtol), H16 (FEF protasis — combines cleanly with H5b).

**Audit dispatched (per §7 multi-trigger requirement):** four parallel agents 2026-05-02 (FP/FN sampling, spec impact survey, M2 verbless integrity, canon revision drafter). Triggers fired: #1 (new named rule H5b + new named test Propositional Completeness Test + new section §0.2 Governing Values); #3 (initial framing rested on Isa 40:6 spot-evidence — full-corpus sweep dispatched as condition of codification); #5 (H5 short-framing-default is a live application being retired); #6 (validator changes under settled rule); #7 (corpus sweep of all H5-merge applications + all m4-solo-speech-verb applications, ≥5 instances expected); #12a (post-codification corpus-wide goal-fit audit scheduled as next-session first task per protocol).

**Audit-status declaration (per CLAUDE.md Pre-commit Adversarial-Audit Discipline):** Audit dispatched: four parallel agents 2026-05-02 (canon revision drafter Opus, FP/FN sampling Opus, spec impact survey Sonnet, M2 verbless audit Sonnet); §8 entry above + corresponding canon edits.

### 2026-05-05 — Te'amim consultative role retirement (full removal)

**What landed.** Te'amim are no longer cited as evidence in editorial decisions. The previous canon stance ("evidence not authority") was demoted further to "play no role in editorial decisions." Operational uses survive (parse_teamim.py one-time v1-baseline generator; Sifrei Emet vs prose corpus partition for cluster routing; sof-pasuq-as-verse-end structural marker). The three forces (atomic thought, single image, Hebrew syntax) carry the entire load.

**Edits applied:**
1. §1 "The Te'amim Are Not a Structural Prior" → renamed and rewritten as **"The Te'amim Play No Role in Editorial Decisions"**. Old section's "most important single piece of evidence" / "evidence-not-authority" / "70-80% corroboration" framing all retired. New section explicitly preserves operational uses and the validator-architecture corollary.
2. §1 "Punctuation, Te'amim Glyphs..." subsection: te'amim bullet rewritten to "play no role in editorial decisions"; sof pasuq bullet preserves verse-end structural use, distinguished from te'amim glyphs proper (U+05C3 vs U+0591–U+05AF).
3. §1 "Parallelism Is Not a Structural Prior": removed te'amim epistemic-footing comparison; replaced "the te'amim missed" with "the v1-baseline did not register"; added Macula constituent trees as the canon-aligned diagnostic for parallelism detection.
4. **Rule H8 retired** (was: Te'amim as Evidence — Operational Application). Replaced with retirement notice + pointer to §1 + this §8 entry. Rule numbering preserved (H8 slot empty rather than renumbering H9–H17).
5. **Rule H11 retired** (was: Tifcha-as-Servant-of-Atnach). Same treatment as H8.
6. §3 Quick-Reference Rule Table: H8 row → RETIRED notice; H11 row → RETIRED notice.
7. §4.1 Rule-to-Table Mapping: H11 row removed (was: tifcha-as-servant cited proclitic-stranding rows). H8 removed from "above this surface" rule list.
8. §4.2 Te'amim Inventory Reference demoted: file preserved as parse_teamim.py implementation reference; no longer canon reference.
9. §6.x Calibration Corpus rows: Jonah 1 row removed Rule H11; Jonah 2 row removed Te'amim-evidence-not-authority + Rule H8 cite; Exodus 15 row removed Rule H11.
10. §9 Glossary: Tifcha entry's "See Rule H11" cross-ref removed; Ta'am entry retained as terminology definition without canon-role implication.
11. **CLAUDE.md** edits: te'amim-as-evidence framing in project intro (line 19) and Te'amim-as-Evidence section (lines 144–146) and v1 tier-table description (line 157) all rewritten to reflect operational-only role.
12. **handoffs/01-project-overview.md** + **handoffs/04-editorial-workflow.md**: te'amim-as-evidence references removed from defensibility-capture descriptions.
13. **validators/specs/m4_b_dibber_formula.yaml**: "atnach typically splits the formula" comment-prose deleted from description (no trigger logic affected).

**WHY.** The previous "te'amim are evidence not authority" framing kept producing scope-slippage. Three concrete failure modes recurred: (a) defensibility-capture-as-smuggled-authority — once "atnach at this position" appears in a commit message as HOW WE KNOW, future agents treat it as warrant rather than re-deriving the atomic-thought defense; (b) validator-design slippage — even framing a validator as "demoting te'amim by merging across them" centers them as the candidate-surfacing signal (the §1 corollary case 2026-04-28; recurred 2026-05-05 with the v1-aware S8 design that proposed trigger "v1 cola count > v2 cola count" — which IS a te'amim-trigger because v1 = parse_teamim.py output); (c) Sifrei Emet vs prose conflation with poetic-register-as-skip (Wave-B 2026-05-04 already removed 11 such skips; the residual te'amim-evidence framing kept re-creating the temptation). Removing the consultative role closes the slippage surface entirely. Adversarial audit found ZERO documented tiebreaker cases in canon or session-notes where the three forces were ambiguous and only te'amim broke the tie — the Decision Procedure (§1, lines ~450–464) names atomic thought / split triggers / syntax veto / merge override / image diagnostic, with te'amim appearing nowhere. The "70–80% corroboration" claim in the prior §1 was unfalsifiable as stated and operationally inert.

**HOW WE KNOW.** Two parallel agents 2026-05-05: (a) Opus adversarial audit (agent ID `ab055c3b0ef3a37ec`) on the proposed removal — verdict "DO IT IF" with three preserved-scope items (sof-pasuq-as-verse-marker, cluster-5 SE/prose routing, parse_teamim.py + v1-baseline files until 39/39 v2 coverage independently verified); (b) Sonnet corpus survey (agent ID `a004131ab06584e0b`) of all te'amim references — found 33 CONSULTATIVE locations across canon + CLAUDE.md + 2 handoffs + 1 YAML + 4 validator output-only blocks; ~85 OPERATIONAL refs (parse_teamim.py, poetic_register.py, sof-pasuq guards, Unicode constants); ~9 HISTORICAL-RECORD blocks in §8/§10 (preserved per historical-record-preservation rule). **Critical survey finding: zero existing validators trigger on te'amim glyphs** — the §1 corollary architecture is already clean; the retirement is forward-looking, not corrective. Imposing-vs-revealing analysis: this is REVEALING (correcting an asymmetry where one Masoretic editorial overlay was given a special epistemic status that the others — sof pasuq, paseq, niqqud, versification — were already denied), not IMPOSING.

**SCOPE.** Canon: §1 te'amim section + parallelism-comparison line + glossary entries; Rules H8 + H11 retired; §3 table + §4.1/§4.2 + §6.x calibration + §8 (this entry). CLAUDE.md: 3 locations. Handoffs: 2 files. YAML specs: m4_b_dibber_formula description prose only (no trigger change). Validators: 4 output-only `teamim_summary()` calls removed (validate_bonded_pair, validate_causal_ki, validate_bare_construct_head, validate_oath_formula); trigger logic unchanged. Operational preservations per audit verdict: parse_teamim.py + v1-baseline files preserved (one-time draft generator; canary-verify 39/39 v2 coverage before retirement); cluster-5 SE/prose routing preserved (book/chapter membership, not runtime te'amim check); sof-pasuq-as-verse-marker preserved (structural punctuation, U+05C3, distinct from te'amim glyphs U+0591–U+05AF). Historical-record entries in §8/§10 referencing the prior te'amim framing preserved per §8 do-not-rewrite-dated-entries rule.

**Closes prior carry-forwards.** §8 carry-forward "Update parse_teamim.py to reflect Rule H8's de-authority framing" (line ~1269) — closed by retirement (script docstring becomes operational-only). §8 carry-forward "Update parse_teamim.py to reflect Rule H11 — tifcha-as-servant mechanical adjustment" (line ~1271) — closed by retirement (parse_teamim.py implementation choice is now an operational detail, not a canon commitment). Te'amim Inventory Reference §4.2 carry-forwards (line ~1216) — closed by demotion to operational reference.

**Audit dispatched (per §7 multi-trigger requirement):** two parallel agents 2026-05-05 (Opus adversarial audit `ab055c3b0ef3a37ec`; Sonnet corpus survey `a004131ab06584e0b`). Triggers fired: #1 (canon-rule retirements: H8 + H11); #5 (te'amim-as-evidence stance is a live application being retired); #6 (validator-output cleanup at 4 sites under settled rule); #7 (corpus survey of all te'amim references); #12a (post-codification spot-check of Macula-parallelism detector design pathway scheduled as next-session task).

**Audit-status declaration (per CLAUDE.md Pre-commit Adversarial-Audit Discipline):** Audit dispatched: two parallel agents 2026-05-05 (Opus adversarial audit `ab055c3b0ef3a37ec`; Sonnet corpus survey `a004131ab06584e0b`); §8 entry above + corresponding canon edits.

---

## §9 Glossary

Hebrew terminology used throughout this canon, in alphabetical order by transliteration.

- **Aleppo Codex** — the Tiberian-tradition codex that, with Leningrad, is one of the two primary witnesses to the Tiberian Masoretic text. Editorial base for MAM.
- **Atnach (etnachta)** — major mid-verse disjunctive ta'am in the prose accent system. Divides each verse into two halves.
- **BHS** — *Biblia Hebraica Stuttgartensia*, the standard scholarly edition of the Hebrew Bible based on Leningrad. BHQ is its successor.
- **Casus pendens** — Hebrew topic-fronting construction with resumptive pronoun in the main clause; equivalent to "left-dislocation" in syntactic terminology. Joüon-Muraoka §156.
- **Construct chain** — bound NP construction with *nomen regens* (head) in construct state + *nomen rectum* (genitive). The chain functions as a single syntactic unit.
- **Disjunctive accent** — a ta'am marking a pause in cantillation. Opposed to *conjunctive accent*, which links words.
- **FEF (Front-End Frame)** — periodic-sentence construction where a discourse marker or clause-opener suspends resolution until the main verb arrives. The Hebrew *wayehi* protasis is the canonical Hebrew FEF.
- **Hendiadys** — figure of speech expressing one idea via two coordinated members (*חֶסֶד וֶאֱמֶת* "covenant-loyalty" expressed as the pair "loyalty and truth"). Joüon-Muraoka §177.
- **Itture sopherim** — "scribal omissions" the Masorah identifies as deliberate textual omissions from earlier forms (~5 cases).
- **Ketiv** (*כְּתִיב*) — the consonantal text as written.
- **Leningrad Codex** — the oldest complete Tiberian-tradition codex (~1008 CE). Editorial base for BHS, BHQ, TAHOT, OSHB, UXLC, this project.
- **Maqqef** (*מַקֵּף*, U+05BE) — Hebrew hyphen joining two-to-four orthographic words into a single prosodic unit bearing one ta'am.
- **MAM** — *Miqra al pi ha-Mesorah*, the Aleppo-tradition online edition. Vendored as tradition reference, not adopted.
- **Merism** — figure of speech expressing totality by naming polar opposites (*שָׁמַיִם וָאָרֶץ* = "all of creation"; *זָכָר וּנְקֵבָה* = "all humans").
- **Niqqud** — Tiberian vowel-pointing system. Subscripts and superscripts indicating vowels; finalized by the Masoretes ~9th–10th c. CE.
- **Nomen regens** — the head noun in a construct chain (in construct state).
- **Nomen rectum** — the genitive noun in a construct chain.
- **OSHB** — *Open Scriptures Hebrew Bible*, free digital edition based on Leningrad, vendored as transcription cross-check.
- **Paseq** — vertical bar (*׀*) added in some Masoretic traditions as a post-Masoretic disjunctive marker; function contested.
- **Petucha** (*פתוחה*, "open") — pre-Masoretic paragraph division marked by a full-line gap in manuscripts. Stronger break than setuma.
- **Pisqa be-emtsa pasuq** — paragraph break occurring mid-verse (e.g., Gen 35:22). Anomalous; preserved per Masoretic tradition.
- **Prosodic word** — accentual unit in Hebrew. A maqqef-group is one prosodic word containing 2–4 orthographic words.
- **Qere** (*קְרֵי*) — the consonantal text as read aloud (Masoretic oral-reading tradition).
- **Sebirin** — masoretic notes marking a "supposed" alternative reading that the consensus rejects in favor of the printed reading.
- **Setuma** (*סתומה*, "closed") — pre-Masoretic paragraph division marked by a gap mid-line in manuscripts. Weaker break than petucha.
- **Sifrei Emet** (*אמ"ת*, acronym from *Iyyov / Mishlei / Tehillim* = Job / Proverbs / Psalms) — the three biblical books that use the poetic accent system. Job's poetic body (3:1–42:6) only; the prose frame uses prose accents.
- **Silluq** — the disjunctive ta'am marking the final tonic syllable of a verse. Always paired with sof pasuq.
- **Sof pasuq** — verse-end punctuation mark (`׃`, U+05C3). Marks the end of each Masoretic verse.
- **Stich** (or *colon*) — a single colometric unit in *Sifrei Emet* terminology. Verses subdivide into 1, 2, or 3 stichs.
- **STEPBible TAHOT** — the primary source-text feeding the project's pipeline. TSV format; CC-BY-4.0; based on Leningrad with morphological tagging.
- **Ta'am / Te'amim** — Tiberian cantillation accents. Primarily melodic; secondarily marks word stress; tertiarily marks phrase-pause boundaries within a verse.
- **TaNaK** — acronym for Torah / Nevi'im / Ketuvim, the Hebrew tripartite division of the canon.
- **Tetragrammaton** — the four-letter divine name יהוה, vocalized as Adonai (or Elohim) in Jewish reading tradition; transliterated as *Yahweh* in this project's translit layer per scholarly convention.
- **Tiqqunei sopherim** — "scribal corrections" the Masorah identifies as deliberate emendations from earlier forms (~18 cases per masoretic tradition).
- **Tifcha** (*טִפְחָא*) — disjunctive ta'am that frequently functions as a *servant of atnach* (mishneh) in many positions. (Rule H11 retired 2026-05-05; see §8 entry.)
- **Trei Asar** — "the Twelve" — the twelve Minor Prophets, treated as one book in Hebrew tradition.
- **UXLC** — Westminster Leningrad Codex digital edition at tanach.us. Vendored as transcription cross-check.
- **Wayyiqtol** (vav-consecutive imperfect) — the dominant clause-head verbal form in Hebrew narrative prose. Marks sequential narrative events. See Rule H3.
- **Zaqef qaton / zaqef gadol** — second-tier disjunctive accents in the prose system.
- **Zarqa / Tzinnor** — the SAME accent positionally; *zarqa* in prose, *tzinnor* in Sifrei Emet terminology. Predecessor stub canon's §3.2 listing them as separate accents was a factual error.

---

## §10 Retired Formulations

*Purpose: **mainly historical** — documents what was explicitly retired and why, so future editors do not accidentally re-propose discarded framings as new ideas. Format mirrors §8 Update Log entries but is deletion-focused rather than addition-focused. Entries are in retirement-date order. **Do not rewrite or remove dated entries.** Historical entries retain their original wording; silently revising them falsifies the chronological trail.*

Each entry records: the retired formulation, the retirement date, why it was retired, and what (if anything) replaced it.

---

### Retired 2026-04-26 — Te'amim-as-prior with override-warrant discipline

**Retired formulation.** The predecessor stub canon (2026-04-25) placed the te'amim as the structural prior for line-break decisions: breaks defaulted to what the te'amim disjunctive hierarchy produced, with documented "override warrants" required to deviate from that prior.

**Why retired.** The te'amim are a Tiberian Masoretic editorial overlay (~9th–10th c. CE), not original compositional structure. The override-warrant framing demoted the editor's evidence-based reasoning to a secondary role relative to a late medieval chant-marker system. The sibling canons (BoFM, GNT) had already converged on the principle that editorial overlays carry no deterministic force — the te'amim in Hebrew are exactly parallel to NA28 punctuation in Greek and Pratt's 1879 versification in the BoFM English text.

**Replacement.** Te'amim-as-evidence: the te'amim are the most important single piece of evidence and the editor's starting draft (v1-he-baseline), but they do not authorize a break by themselves. See §1 "The Te'amim Are Not a Structural Prior" and Rule H8.

**§8 cross-reference.** 2026-04-26 "Canon v1.0 written from scratch" entry — "Stan-validated 2026-04-26 after explicit pushback against earlier hedging that framed the te'amim demotion as a 'tradeoff.'"

---

### Retired 2026-04-26 — Four-criteria framing (atomic thought, single image, syntax, breath)

**Retired formulation.** An earlier framing of the editorial criteria named four: (1) atomic thought, (2) single image, (3) Hebrew syntax, (4) breath / oral phrasing.

**Why retired.** Breath was empirically retired by both sibling projects (BoFM 2026-04-19, GNT 2026-04-20) after full-corpus testing found zero cases where breath was the sole deciding factor in a split/merge adjudication. The Hebrew evidence sharpens the retirement further: the te'amim are *literally* the historical record of Masoretic cantorial phrasing — "where the cantor breathes." If breath were a valid sense-unit prior, the te'amim would by definition encode it perfectly. Breath as a named criterion either collapses into the te'amim (already evidence-not-authority) or is doing no work distinguishable from atomic thought + structural justification 5 (substantive adjunct as own focus). Naming it as a criterion adds confusion without adding discriminatory power.

**Replacement.** Three criteria: atomic thought, single image, Hebrew syntax. See §1 Decision Procedure, §1 summary table (four forces), and `private/memory/feedback_no_breath_criterion.md`.

**§8 cross-reference.** 2026-04-26 "Canon v1.0 written from scratch" entry — "Carried the four-criteria framing both canons retired (BoFM 2026-04-19, GNT 2026-04-20)."

---

### Retired 2026-04-27 — Five-tier pipeline (v0 / v1 / v2-he-syntax / v3-he-colometry / v4-editorial)

**Retired formulation.** The pipeline had five tiers: v0 (raw TAHOT), v1 (te'amim baseline), v2-he-syntax (auto-apply Layer 1 STRONG candidates via `apply_v2.py`), v3-he-colometry (auto-apply Layer 3 STRONG candidates via `apply_v3.py`), v4-editorial (hand-edited gold standard).

**Why retired.** The two intermediate auto-apply tiers added pipeline complexity without adding editorial capability. `apply_v3.py` was a passthrough from inception (no Layer 3 validators had cleared the ≥80% adoption gate). `apply_v2.py` had two validators cleared but their findings (~2 corrections per chapter on Jonah) sit more naturally on the editorial work queue under Category A reasoning (§2 Mechanical-rule authority). The closed-list rule set (H1, H2, H5, H7, H11, H16) is not the large-scale mechanical-error surface that justified intermediate auto-apply tiers in other projects. Two tiers (baseline + editorial) are sufficient for the Tanakh corpus.

**Replacement.** Three-tier pipeline: v0 (raw) → v1 (te'amim-baseline, editor's starting draft) → v2 (hand-edited Hebrew gold standard). Validator STRONG findings feed the editorial work queue directly as Category A items; no intermediate auto-apply tier needed. See §8 "2026-04-27 — Tier collapse" entry and CLAUDE.md Tier Discipline section.

**§8 cross-reference.** 2026-04-27 "Tier collapse: 5-tier pipeline → 3-tier pipeline" entry.

---

### Retired 2026-04-28 — Proposed `validate_tifcha_servant.py` (te'amim-centric validator)

**Retired formulation.** A proposed validator (`validate_tifcha_servant.py`) that would trigger on the tifcha (TIPHA) glyph's presence within atnach domain, flag candidate lines, and recommend merges where tifcha was acting as a "servant of atnach" rather than a primary disjunctive.

**Why retired.** Killed in design after Stan's discomfort flag ("overreliance on Masoretic punctuation cues for determining thought line breaks") and a six-agent hostile audit. Two problems: (1) **Architectural violation:** a validator triggering on te'amim glyph placement operationally centers te'amim as the primary candidate-universe — exactly the te'amim-as-prior the §1 demotion rejects. Even framing the validator as "demoting te'amim by merging across them" doesn't fix the problem: the candidate universe is still defined by tifcha glyph positions. The §1 Validator-architecture corollary (added same session) makes this explicit. (2) **Gold-standard disconfirmation:** the Jonah 1 hand-edited gold standard (the project's existing v2/heb reference) showed 3 of 4 candidate tifcha-servant sites SPLIT by Stan's editorial decisions — STRONG-MERGE auto-application would have inverted the documented gold standard.

**Replacement.** The editorial problem the validator was targeting (tifcha-driven over-fragmentation in v1-he-baseline) is addressed by (a) Rule H11 Tifcha-as-Servant-of-Atnach as editorial guidance for human editors reviewing the v1 draft, and (b) Rule H18 Clause-Nucleus Integrity, which provides the morpho-syntactic (non-te'amim) trigger that catches the same over-fragmentation pattern. See §1 Validator-architecture corollary; Rule H11; Rule H18; §8 "2026-04-28 — Rule H18 adopted; te'amim-centric validator architecture rejected."

**§8 cross-reference.** 2026-04-28 entry — "Proposed `validate_tifcha_servant.py` (te'amim-centric architecture) was killed in design."

---

*End of canon.*
