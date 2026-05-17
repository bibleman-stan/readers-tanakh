# Rules Audit — Constraint-vs-Producer Catalog
**Directive:** `directives/pending/2026-05-17-1100-rules-audit-constraint-catalog.md`
**Date:** 2026-05-17

---

## Item 1 — Per-Validator Categorization

### Summary Table

| Category | Count | Validators |
|----------|-------|-----------|
| CONSTRAINT | 14 | validate_maqqef_integrity, validate_line_final_tokens, validate_compound_preposition_object, validate_verb_object_bond, validate_bare_construct_head, validate_bare_discourse_particle, validate_bonded_pair, validate_complement_integrity, validate_construct_chain, validate_coordinated_object, validate_cross_verse_continuity, validate_interrogative_clause, validate_oath_formula, validate_wayehi_protasis |
| PRODUCER | 5 | validate_parallel_clause_split, validate_blessed_cursed_chain, validate_parallel_series_uniformity, validate_genealogy_uniformity, validate_speech_intro_framing |
| MIXED | 6 | validate_causal_ki, validate_clause_nucleus_split, validate_participial_speech_frame, validate_short_orphan_line, validate_short_verse_fronting, validate_wayehi_protasis* |
| META | 2 | validate_canon_retirement_residue, validate_doc_pointers |

*validate_wayehi_protasis appears in both CONSTRAINT and MIXED depending on arm — see per-entry below.

---

### Per-Validator Detail

#### Syntax (4)

---

**validate_compound_preposition_object**
- **Encoded question:** Does a line end with a compound preposition whose object NP begins the next line?
- **Categorization:** CONSTRAINT
- Reasoning: Encodes Layer 1 grammatical prohibition. Compound prepositions (מִלִּפְנֵי, מִפְּנֵי, מִתַּחַת, etc.) require their governed NP on the same line. JM §103e. No editorial preference encoded; purely a syntactic well-formedness check.
- **Canon citation:** Layer 1 (hebrew-break-legality.md row 11); H7 substrate
- **Baseline finding count:** 0 (corpus is already clean on v2)
- **Coverage:** Unique: no sibling validator covers compound-preposition object stranding specifically. validate_line_final_tokens covers simpler prep-prefix stranding; this covers the multi-morpheme compound preposition case.

---

**validate_line_final_tokens**
- **Encoded question:** Does a line end with a proclitic (conjunction-prefix וְ/וַ/וּ, prep-prefix מ/ב/כ/ל, definite article הַ/הָ/הֶ, direct-object marker אֵת/אֶת, negation לֹא/אַל) that cannot stand alone?
- **Categorization:** CONSTRAINT
- Reasoning: Pure Layer 1 syntactic prohibition. Each trigger is a morphological proclitic that cannot constitute a prosodic word boundary. No editorial judgment; all cases are MALFORMED by Hebrew grammar.
- **Canon citation:** Layer 1 (hebrew-break-legality.md rows 1–6); JM §103, §137, §125, §160
- **Baseline finding count:** 2
- **Coverage:** Core Layer 1 gate. Unique coverage of these proclitic classes; no sibling covers this directly.

---

**validate_maqqef_integrity**
- **Encoded question:** Does a line end with a maqqef glyph (U+05BE), splitting a prosodic unit across lines?
- **Categorization:** CONSTRAINT
- Reasoning: Layer 1 orthographic fact. Maqqef joins tokens into a single prosodic word; a break inside is categorically illegal. Zero editorial judgment.
- **Canon citation:** H1 (Maqqef-Group Indivisibility); Layer 1; JM §13
- **Baseline finding count:** 0 (corpus clean)
- **Coverage:** Unique; the only validator checking the maqqef glyph at line-end position.

---

**validate_verb_object_bond**
- **Encoded question:** Does a finite verb's direct-object (Macula frame-arg A1, nominal) appear on the next sense-line rather than the same line as the verb?
- **Categorization:** CONSTRAINT
- Reasoning: Encodes M2 (Verb-Object Clause-Nucleus Bond) — a closed-list merge-override rooted in Hebrew clause structure. The finite verb + its nominal direct-object form the minimal clause nucleus; splitting them violates complement integrity. Detection is now IR-driven (Macula frame-args), making this a pure structural query rather than a heuristic.
- **Canon citation:** M2 (canon §1 merge-overrides); H7 substrate; JM §125; WO §10.2.1
- **Baseline finding count:** 135
- **Coverage:** Unique for verb-A1 frame-arg stranding. Partially overlaps validate_complement_integrity (which covers clausal complements) but covers nominal direct-objects that validate_complement_integrity does not.

---

#### Colometry (23)

---

**validate_bare_construct_head**
- **Encoded question:** Does a line end with a bare construct-state noun (regens) whose rectum begins the next line, splitting a construct chain?
- **Categorization:** CONSTRAINT
- Reasoning: Implements M3 (Bare-Governor Indivisibility) for the construct-chain case. A bare regens without its rectum fails the atomic-thought test: it is grammatical machinery awaiting content. The rule answers a yes/no question about construct-state dependency. Now IR-backed via Macula NPofNP constituent detection, suppressing redundant findings when validate_construct_chain already covers them.
- **Canon citation:** M3 (canon §1); H2 substrate; JM §129; WO §9.3
- **Baseline finding count:** 18
- **Coverage:** Complementary to validate_construct_chain. Catches parser-missed construct-chain splits where Macula's NPofNP recall fails. Somewhat redundant in IR-confirmed cases (suppressed by the IR cross-check), unique for the ~15–35 parser-missed cases.

---

**validate_bare_discourse_particle**
- **Encoded question:** Does a line consist solely of a bare discourse particle (הִנֵּה, לָכֵן, עַל־כֵּן, אָז, וְעַתָּה, etc.) with its governed content on the next line?
- **Categorization:** CONSTRAINT
- Reasoning: Implements M3 (Bare-Governor Indivisibility) for the discourse-particle case. A bare particle cannot form an ATU; it fails the atomic-thought test. The test is binary: is this particle alone on a line when its governed content follows? No editorial preference; the rule is a syntactic well-formedness check.
- **Canon citation:** M3 (canon §1) + H14 (discourse particles lead content); canon §5 H14
- **Baseline finding count:** 0 (corpus clean)
- **Coverage:** Unique coverage of the single-token bare-particle-on-own-line pattern. Conceptually related to validate_clause_nucleus_split but distinct detection signature.

---

**validate_blessed_cursed_chain**
- **Encoded question:** Is a blessed/cursed formula member (בָּרוּךְ/אָרוּר + content) fragmented across multiple lines within the Deut 27–28 list?
- **Categorization:** PRODUCER
- Reasoning: Encodes a procedural uniformity preference for a specific corpus corpus region (Deut 27:15–26; 28:3–6, 16–19). The rule creates ATU rendering decisions ("each cursed/blessed member should be one line") rather than checking a syntactic constraint. The underlying real constraint is the Parallel-List Uniformity Principle, but the validator's action is to prescribe how many lines each member occupies — a production decision. Scope is artificially narrow (3 chapter-ranges in one book).
- **Canon citation:** Parallel-List Uniformity Principle (canon §1)
- **Baseline finding count:** 5
- **Coverage:** Covered at a higher level by validate_parallel_series_uniformity. This is a narrow specialization of the same principle; its independent existence is mainly for precision within the named scope.

---

**validate_bonded_pair**
- **Encoded question:** Does a line end with skeleton1 and the next line begin with וְ+skeleton2, where (skeleton1, skeleton2) is a known M1 bonded pair (hendiadys/merism)?
- **Categorization:** CONSTRAINT
- Reasoning: Implements M1 (Bonded Pair merge-override). The test is structural: given two conjoined nouns in the closed bonded-pair lexicon, the pair must stay together. The guard (no finite verb on either line) prevents misfiring on verbal clauses. The closed-list is small (13 pair-entries) and well-defined.
- **Canon citation:** M1 (canon §1 merge-overrides); JM §177; WO §4.6.5
- **Baseline finding count:** 1
- **Coverage:** Unique for the closed-list bonded-pair test. Note: the larger BONDED_LEMMA_PAIRS (88 pairs) is dormant per canon §1 M1; this validator only fires on the core 13-pair structural list.

---

**validate_canon_retirement_residue**
- **Encoded question:** Do active references to retired canon items appear in canon/CLAUDE.md/handoffs?
- **Categorization:** META (not a Hebrew syntactic constraint; process hygiene)
- Reasoning: Checks documentation consistency, not Hebrew syntax. Irrelevant to the CONSTRAINT/PRODUCER distinction.
- **Canon citation:** §7 Change Protocol; §8 Update Log discipline
- **Baseline finding count:** 11
- **Coverage:** Unique meta-role; no other validator checks doc hygiene.

---

**validate_causal_ki**
- **Encoded question:** Does a line followed by כִּי + finite verb represent a causal-כִּי clause that was split off from its matrix statement?
- **Categorization:** MIXED
- Reasoning: CONSTRAINT arm: the causal-vs-complement disambiguation (guard 1: prior line ends with cognition/speech verb → H7 territory; skip) is a genuine syntactic question. PRODUCER arm: the finding's recommendation ("this causal-כִּי may justify its own line per structural justification 5") is a production recommendation rather than a pure constraint check. The validator surfaces candidates for editorial judgment rather than catching a clear violation. The severity is STRONG-SPLIT-CANDIDATE, which means it recommends a split — producer behavior.
- **Canon citation:** H7 substrate (complement-vs-causal disambiguation); SJ5 (substantive adjunct)
- **Baseline finding count:** 992 — highest review-requiring volume in the stack
- **Coverage:** The causal-כִּי vs. complement-כִּי disambiguation is not covered elsewhere. The constraint arm is genuinely novel. But the production arm (recommending splits) makes this a MIXED validator.
- **FP priority:** High — 992 findings, REVIEW-REQUIRED severity means zero auto-apply. In the new architecture, this validator should be re-framed as a pure constraint audit: "Is this כִּי a causal subordinate clause whose separation from its matrix is syntactically licensed?" That is the real question; the split recommendation should be removed.

---

**validate_clause_nucleus_split**
- **Encoded question (H18):** Does a line ending with NP (no finite verb) precede a line beginning with predicate (PP/participle/verb-PP-complement), suggesting a verbless/participial/verb-PP-complement clause nucleus split across lines?
- **Categorization:** MIXED
- Reasoning: H18.1 (verbless subject + predicate split) and H18.2 (participial predicate split) are genuine Hebrew syntactic constraints — verbless clauses are complete predications in Hebrew, and splitting their subject from predicate violates clause-nucleus integrity (H18). H18.3 (verb + PP complement) is also a constraint (M2 extension). However, the validator's guards include several editorial heuristics (H4 vocative skip, H14 discourse particle skip, H15 casus pendens skip, H16 FEF skip, M3 bare-governing-participle skip) that are applied as producers — the guards decide not just "is this a violation?" but "should we apply a split or merge here?" making this MIXED.
- **Canon citation:** H18 (Clause-Nucleus Integrity); M2 (§1); JM §154; WO §8.4
- **Baseline finding count:** 421
- **Coverage:** Primary (and unique) detector for verbless-clause and participial-predicate nucleus splits. H18.3 partially overlaps validate_verb_object_bond; H18.1/H18.2 are unique.

---

**validate_complement_integrity**
- **Encoded question:** Does a cognition/volition/causative verb appear at line-end with its obligatory כִּי-clause complement starting the next line?
- **Categorization:** CONSTRAINT
- Reasoning: Directly implements H7 (Complement Integrity). The question is syntactically binary: does the line-final verb's valence require a כִּי-clause that is grammatically obligatory (per the closed-list OBLIGATORY_COMPLEMENT_VERBS)? Yes → MERGE. The guards (long-complement exception, parallel כִּי-series) are also syntactically grounded. The validate_complement_integrity focus is the prototypical constraint form.
- **Canon citation:** H7 (canon §5); SJ2 (syntax forbids splits — complement integrity); JM §157; WO §38.3
- **Baseline finding count:** 3 (corpus largely clean)
- **Coverage:** Unique for the closed-list cognition-verb + כִּי-complement split. Partially covered in a secondary way by validate_causal_ki (which guards cognition verbs to skip them); this validator specifically fires on them.

---

**validate_construct_chain**
- **Encoded question:** Does a Macula NPofNP constituent span across two editorial sense-lines (i.e., is a construct chain split)?
- **Categorization:** CONSTRAINT
- Reasoning: IR-driven implementation of H2 (Construct Chain Default) using Macula NPofNP constituent boundaries. Pure syntactic constraint: the NPofNP is a grammatical unit; splitting it violates clause-nucleus integrity. No editorial preference.
- **Canon citation:** H2 (Construct Chain Default); JM §129; WO §9.3, §9.5
- **Baseline finding count:** 437
- **Coverage:** Primary detector for construct-chain splits. Partially overlaps validate_bare_construct_head (complementary; see that entry). The IR path is the authoritative mechanism; validate_bare_construct_head handles parser-missed cases.

---

**validate_coordinated_object**
- **Encoded question:** Does a finite verb have multiple frame-arg A1 (direct object) tokens landing on distinct sense-lines?
- **Categorization:** CONSTRAINT
- Reasoning: IR-driven implementation of M2 + SJ1 (compound list). The structural question is: is a single verb's A1 object fragmented across lines? Guards (combined weight >8 words, heavy NP on A1) are syntactic weight-checks, not editorial preferences. The STRONG path is safe to auto-apply because Macula frame-args are authoritative.
- **Canon citation:** M2 (canon §1 merge-overrides); SJ1 (formally-marked parallel series compound list break signals); JM §137; WO §10.2.1
- **Baseline finding count:** 385
- **Coverage:** Unique for the coordinated-DO frame-arg stranding case. Partially inverse of validate_verb_object_bond (which catches DO on next line; this catches multiple DOs spread across lines).

---

**validate_cross_verse_continuity**
- **Encoded question:** Does a verse-end create an artificial break inside a grammatical unit that spans the verse boundary (subordinator stranded, construct-chain crossing, speech-frame without content)?
- **Categorization:** CONSTRAINT
- Reasoning: Implements H10 (Cross-Verse Continuity Merge). The test is syntactic: are the final tokens of verse N grammatically incomplete without the opening tokens of verse N+1? The four sub-cases (subordinator stranding, conjunction stranding, construct crossing, speech-intro without content) are all syntactic constraint checks.
- **Canon citation:** H10 (Cross-Verse Continuity Merge); §1 versification-not-a-break-signal
- **Baseline finding count:** 888 — second-highest volume
- **Coverage:** Unique. No other validator checks cross-verse boundaries specifically.
- **FP note:** High finding count (888) across STRONG and REVIEW severities. The REVIEW-REQUIRED arm is a genuine constraint audit; the STRONG-MERGE-CANDIDATE arm fires on high-confidence cases (bare subordinator at verse-end). In the new architecture, this is a canonical constraint validator.

---

**validate_doc_pointers**
- **Encoded question:** Are file-path references in canon/CLAUDE.md/handoffs pointing to files that exist?
- **Categorization:** META (process hygiene, not Hebrew syntax)
- **Canon citation:** §7 Change Protocol
- **Baseline finding count:** 33
- **Coverage:** Unique meta-role.

---

**validate_genealogy_uniformity**
- **Encoded question:** Within genealogical-formula scope (Gen 5, 10, 11, 36; 1 Chr 1–9), is a generation-member's formula fragmented (numeric fragment on its own line, partial וַיּוֹלֶד without anchor)?
- **Categorization:** PRODUCER
- Reasoning: Encodes the Parallel-List Uniformity Principle for a specific corpus class (genealogical lists). The rule prescribes how many lines each generation-member occupies — a rendering decision. The underlying Hebrew grammar does not forbid a numeric-age fragment on its own line by syntactic necessity; the rule prefers a single-line-per-generation-member treatment for readability and list uniformity. PRODUCER.
- **Canon citation:** H17 (Genealogy/List-Formula Handling); Parallel-List Uniformity Principle (canon §1)
- **Baseline finding count:** 0 (corpus clean)
- **Coverage:** Unique scope (genealogical formula). No overlap with other validators.

---

**validate_interrogative_clause**
- **Encoded question:** Does a line end with a bare interrogative particle (הֲ-, מִי, מָה, אַיֵּה, אֵיךְ, לָמָה, מַדּוּעַ) with its clause content beginning the next line?
- **Categorization:** CONSTRAINT
- Reasoning: The interrogative particle + its governed clause form a syntactic unit — the interrogative dependency cannot be severed across lines without producing a fragment that fails the atomic-thought test. The particle alone is a bare governor (M3). The test is binary: is this particle stranded from its clause? No editorial preference.
- **Canon citation:** M3 (Bare-Governor Indivisibility); §1 No-Anchor Test
- **Baseline finding count:** 29
- **Coverage:** Unique for interrogative particle stranding. Slightly overlaps validate_bare_discourse_particle in concept (both cover bare particles), but the interrogative case is morphologically distinct (interrogative particles vs. discourse particles) and has different complements.

---

**validate_list_formula_uniformity**
- **Encoded question** (from doc header): Are members of parallel list formulas treated uniformly?
- **Categorization:** PRODUCER
- Reasoning: Parallel-List Uniformity Principle implementation. Prescribes line-count uniformity across list members — a rendering decision. No baseline findings (0); likely scope is very narrow or not yet activated.
- **Canon citation:** Parallel-List Uniformity Principle (canon §1); SJ1
- **Baseline finding count:** 0
- **Coverage:** Overlaps validate_parallel_series_uniformity in principle; may be a narrow specialization.

---

**validate_maqqef_integrity** (see Syntax section above)

---

**validate_oath_formula**
- **Encoded question:** Does a line end with an oath formula skeleton (חַי + maqqef + divine name/pronoun) with its asseveration content on the next line?
- **Categorization:** CONSTRAINT
- Reasoning: Implements M4 (Fragmented Atomic Thought-Unit) for the frozen-formula case. An oath formula is a lexicalized unit (formula integrity per §1); splitting the formula from its asseveration would produce a fragment that fails the atomic-thought test. The trigger is the formula marker itself — a syntactic/lexicographic fact.
- **Canon citation:** M4 (canon §1 merge-overrides); §1 formula integrity (Layer 3)
- **Baseline finding count:** 23
- **Coverage:** Unique for oath-formula integrity. The formula-integrity principle is also covered by validate_speech_intro_framing (for כֹּה אָמַר יְהוָה / נְאֻם־יְהוָה), but oath formulas are a distinct class.

---

**validate_parallel_clause_split**
- **Encoded question:** Does a single v2/heb line contain tokens spanning ≥2 distinct Macula clause boundaries, each with its own finite-verb head?
- **Categorization:** PRODUCER (primary arm) / MIXED (gapped-restatement arm)
- Reasoning: The primary detection arm (STRONG-SPLIT-CANDIDATE) recommends splitting merged parallel clauses. This is a production decision: "these two finite-verb-headed clauses should be on separate lines." The canon §1 empirical evidence (Ps 1 analysis) explicitly found this validator produces 0 of 4 needed corrections on the verse-class it was designed for, and that LLM with bidirectional test without this validator achieves the same accuracy. The underlying question (are two independent finite-verb clauses merged?) is a real syntactic fact, but the split recommendation is producer behavior.
- **Canon citation:** Hpar rule; Parallel-List Uniformity Principle (canon §1); SJ1
- **Baseline finding count:** 2,051 — highest volume in the stack by far
- **Coverage:** Unique for the Macula-clause-boundary multi-clause-on-one-line detection. Significant FP mass (32% of 3,207 raw findings were structurally confident FPs per the classifier, per the source code comments).
- **Retirement priority: HIGH** — per directive, per empirical Ps 1 evidence, per the FP classifier's 32% confident-FP rate. See Item 4.

---

**validate_parallel_series_uniformity**
- **Encoded question:** Within a detected multi-verse series with shared lexical anchor, do some members have significantly different line counts than others?
- **Categorization:** PRODUCER
- Reasoning: The Parallel-List Uniformity Principle prescribes rendering decisions (uniform line count per member), not syntactic constraints. The validator recommends REVIEW-REQUIRED when members are non-uniform, but the underlying rule is editorial preference, not syntactic prohibition.
- **Canon citation:** Parallel-List Uniformity Principle (canon §1); SJ1
- **Baseline finding count:** 5
- **Coverage:** Overlaps with validate_blessed_cursed_chain and validate_genealogy_uniformity (all implement the same underlying principle for different scopes). Could be consolidated.

---

**validate_participial_speech_frame**
- **Encoded question (H5d):** Does a line contain a predicative speech-participle (קוֹרֵא, אֹמֵר with speech content) followed by an imperative or finite-verb clause that is the quoted content, without a line break between them?
- **Categorization:** MIXED
- Reasoning: The underlying rule (H5d, participial speech-frame split) has a genuine constraint arm: the speech-frame and the quoted content are syntactically distinct cognitive frames (H5b principle). However, the validator's recommendation is STRONG-SPLIT-CANDIDATE — it produces a split. The distinction between the announcement frame and the quoted content is a structural/syntactic fact (Macula IR-driven), but the action prescribed is a production decision. MIXED.
- **Canon citation:** H5d (H5 family extension); H5b (Speech-Act Announcement Default); SJ3
- **Baseline finding count:** 14
- **Coverage:** Unique for the predicative-participle speech-frame case. Complements validate_speech_intro_framing (which covers finite speech-act verbs).

---

**validate_short_orphan_line**
- **Encoded question (M4):** Does a line consist of exactly 1 prosodic word that is NOT in the closed list of standalone-permitted categories (sentence-final verb, classical comma, vocative)?
- **Categorization:** MIXED
- Reasoning: M4 (Fragmented Atomic Thought-Unit) is a genuine constraint — a single-token line failing the atomic-thought test is a real violation. However, the validator's categorization of what counts as "standalone-permitted" involves editorial judgment lists (sentence-final verbs, classical commas, vocatives), and the REVIEW-REQUIRED severity means the validator does not auto-apply. The underlying constraint is real but the implementation mixes constraint detection with editorial allowance lists that require human confirmation. MIXED.
- **Canon citation:** M4 (canon §1 merge-overrides); §5.0 No-Anchor Test; Goldilocks Q1
- **Baseline finding count:** 2,453 — second highest volume
- **Coverage:** Unique for single-token orphan line detection. Partially overlaps validate_clause_nucleus_split (H18) for some cases where a bare noun begins a verbless clause.
- **FP priority:** Very high — 2,453 findings at REVIEW-REQUIRED. Requires FP-rate sampling.

---

**validate_short_verse_fronting**
- **Encoded question:** In a short verse (≤6 prosodic words total), is the first line a single fronted constituent (PP, temporal word) while the second line starts a finite predication, suggesting a merge per the fronting paradox?
- **Categorization:** MIXED
- Reasoning: The "fronting paradox" (canon §1: marked Hebrew word order argues for MERGE for tight bound constituents) is a genuine syntactic insight. However, the validator restricts to "short verses" and "single-word fronted PP" — these are heuristic scope restrictions rather than syntactic definitions. The fronting paradox is a real constraint; the validator's implementation scope is a production heuristic. MIXED.
- **Canon citation:** §1 "The Fronting Paradox" (marked Hebrew word order argues for MERGE); M4
- **Baseline finding count:** 0 (corpus clean or very narrow scope)
- **Coverage:** Unique for the fronting-paradox constraint, but narrow scope. A more general fronting-paradox validator would need to query Macula syntactic position (fronted constituent role, topicalization).

---

**validate_speech_intro_framing**
- **Encoded question:** Does a speech-introduction frame (containing לֵאמֹר or bare speech verb) appear on the same line as the quoted content (STRONG-SPLIT), or as a solo speech-verb at line-end without content following (REVIEW for bare-speech-verb arm)?
- **Categorization:** PRODUCER
- Reasoning: This validator primarily recommends splits (STRONG-SPLIT-CANDIDATE for the long-frame-with-speech arm; REVIEW-REQUIRED for the bare-speech-verb arm). Rule H5b establishes that the announcement and content are separate ATUs, but this is a split-production rule: "put the announcement on its own line." The constraint form would be: "Is the speech-intro frame and quoted content on the same line (a violation)?" The validator does check this, but the dominant finding class (603 findings) is producing split recommendations.
- **Canon citation:** H5 + H5b (Direct-Speech Framing Default + Speech-Act Announcement Default); SJ3
- **Baseline finding count:** 603
- **Coverage:** Primary (and largely unique) detector for H5/H5b violations. The participial_speech_frame validator covers a specialized sub-case.

---

**validate_wayehi_protasis**
- **Encoded question:** Is a וַיְהִי FEF protasis either (a) split across multiple lines without main-clause closure (STRONG-MERGE), or (b) collapsed onto the same line as the main clause (STRONG-SPLIT)?
- **Categorization:** MIXED — the MERGE arm is CONSTRAINT; the SPLIT arm is PRODUCER
- Reasoning: The merge arm (protasis continuation fragmented) is a constraint: the wayehi protasis is a single temporal frame that must stay together (formula integrity + M4). The split arm (protasis collapsed with main clause) is a production decision: "the main clause should start on its own line." H16 (FEF Wayehi Protasis) is the authoritative rule. In the new architecture, the MERGE arm is a constraint audit; the SPLIT arm is a production recommendation.
- **Canon citation:** H16 (FEF Wayehi Protasis); SJ5 (substantive adjunct); formula integrity (§1)
- **Baseline finding count:** 396
- **Coverage:** Unique for the wayehi-FEF pattern. No other validator covers this specific construction.

---

### FP-Sampling Priority (for follow-up directive)

Validators classified PRODUCER or MIXED with significant finding counts, prioritized for FP-rate sampling:

| Priority | Validator | Count | Category | FP risk signal |
|----------|-----------|-------|----------|----------------|
| 1 | validate_parallel_clause_split | 2,051 | PRODUCER | 32% confident FP per classifier (from source code comments) |
| 2 | validate_short_orphan_line | 2,453 | MIXED | High count, REVIEW-REQUIRED only, no auto-apply |
| 3 | validate_causal_ki | 992 | MIXED | 992 findings, REVIEW-REQUIRED, 7 guard iterations to reduce FP in build history |
| 4 | validate_cross_verse_continuity | 888 | CONSTRAINT | High count — REVIEW-REQUIRED arm may have significant FP rate |
| 5 | validate_speech_intro_framing | 603 | PRODUCER | 603 split-recommendations; bare-speech-verb arm has lower confidence |

---

## Item 2 — Hebrew Syntactic Constraint Catalog

This catalog enumerates Hebrew syntactic constraints relevant to ATU rendering. For each: constraint description, current validator coverage, source authority.

### A. Constraints Currently Covered

| # | Constraint Description | Covered By | Authority |
|---|----------------------|-----------|-----------|
| C1 | Maqqef-group indivisibility: a prosodic unit (maqqef-joined tokens) cannot be split across lines | validate_maqqef_integrity | JM §13; WO §15.2 |
| C2 | Proclitic stranding: a morphological proclitic (conjunction וְ/וַ, prep-prefix מ/ב/כ/ל, definite article הַ, DO-marker אֵת, negation לֹא) cannot stand line-final without its governed word | validate_line_final_tokens | JM §103, §125, §137, §160 |
| C3 | Compound-preposition object stranding: a multi-morpheme compound preposition (מִלִּפְנֵי etc.) requires its object NP on the same line | validate_compound_preposition_object | JM §103e |
| C4 | Construct-chain integrity: a bound *nomen regens* and its *nomen rectum* form a single NP that cannot be split | validate_construct_chain + validate_bare_construct_head | JM §129; WO §9.3, §9.5 |
| C5 | Verb–direct-object bond: a finite verb and its nominal direct-object (frame-arg A1) form the minimal clause nucleus; splitting them is a hard syntactic violation | validate_verb_object_bond | M2; WO §10.2.1; JM §125 |
| C6 | Coordinated direct-object integrity: when a single verb governs multiple coordinated A1 objects, all A1 tokens belong together within the clause nucleus | validate_coordinated_object | M2; SJ1 compound-list; WO §10.2.1 |
| C7 | Obligatory-complement integrity: a cognition/volition/causative verb with a grammatically obligatory כִּי-clause complement cannot be split from that complement | validate_complement_integrity | H7; JM §157; WO §38.3 |
| C8 | Bare construct-head indivisibility: a bare construct-state noun (regens) without its rectum cannot constitute a standalone ATU | validate_bare_construct_head | M3; JM §129 |
| C9 | Bare discourse-particle indivisibility: a discourse particle (הִנֵּה, לָכֵן, וְעַתָּה, etc.) cannot constitute a standalone ATU without its governed content | validate_bare_discourse_particle | M3 + H14; JM §155 |
| C10 | Bare interrogative-particle indivisibility: an interrogative particle (מִי, מָה, הֲ-, etc.) cannot stand alone; it requires its governed clause | validate_interrogative_clause | M3; JM §161 |
| C11 | Bonded-pair integrity: a closed-list hendiadys/merism pair (חֶסֶד וֶאֱמֶת, שָׁמַיִם וָאָרֶץ, etc.) must be kept on one line | validate_bonded_pair | M1; JM §177; WO §4.6.5 |
| C12 | Oath-formula integrity: an oath formula (חַי + divine name/pronoun) is a frozen lexicalized unit; splitting it from its asseveration violates formula integrity | validate_oath_formula | M4 + §1 formula integrity |
| C13 | Cross-verse continuity: a grammatical unit whose completion requires tokens from the following verse must not be split at the verse boundary | validate_cross_verse_continuity | H10; §1 versification-not-a-break-signal |
| C14 | Wayehi-FEF protasis integrity: a וַיְהִי temporal frame must be held together as one colon; the protasis cannot be fragmented | validate_wayehi_protasis (MERGE arm) | H16; SJ5; WO §33.1.1c |
| C15 | Verbless-clause nucleus integrity: a verbless-clause subject and its predicative PP/participle form a single clause nucleus | validate_clause_nucleus_split (H18.1) | H18; JM §154; WO §8.4 |
| C16 | Participial-predicate nucleus integrity: a subject NP and its predicative participle form a single clause nucleus | validate_clause_nucleus_split (H18.2) | H18; JM §121; WO §37.6 |
| C17 | Verb–PP-complement bond: a finite verb and its obligatory PP complement (שָׁמַע לְ, פָּנָה אֶל) form an indivisible clause nucleus | validate_clause_nucleus_split (H18.3) + validate_verb_object_bond | H18.3 / M2; JM §133; WO §11.4.1 |

### B. Constraints Identified as NOT COVERED (or under-covered)

| # | Constraint Description | Gap Type | Authority |
|---|----------------------|----------|-----------|
| G1 | **Restrictive relative-clause binding**: a restrictive (defining) אֲשֶׁר-clause binds to its head noun and cannot be treated as a standalone ATU or split from its antecedent | NOT COVERED | JM §158; WO §19.1 |
| G2 | **Non-restrictive relative-clause licensing**: a non-restrictive (descriptive) אֲשֶׁר-clause may stand alone as an ATU when the head is already uniquely identified and the clause passes the bidirectional test | NOT COVERED | JM §158; WO §19.3 |
| G3 | **Gapped finite verb in parallel bicolon**: in synonymous/formal parallelism, a colon whose finite verb is gapped (elided) from the immediately preceding parallel colon is forward-closed by the gapped verb's recoverability; no STRONG-SPLIT should fire on the gapped colon as if it lacks an anchor | NOT COVERED | JM §174 (gapping); WO §8.3.2 |
| G4 | **Coordinate vs. subordinate וְ**: a וְ-led clause may be coordinate (separate ATU candidate) or subordinate (dependent on prior, no ATU boundary). The distinction is determinable by clause type (finite independent clause = coordinate; participial/verbless continuation = subordinate) | PARTIAL — validate_clause_nucleus_split covers some cases; coordinate-vs-subordinate discrimination is not explicit | JM §159, §172-177; WO §39.1, §39.2 |
| G5 | **Purpose-clause infinitive binding**: a לְ + infinitive-construct purpose clause modifying a matrix verb is subordinate; it cannot form a standalone ATU separated from its matrix | NOT COVERED | JM §168; WO §36.2.2 |
| G6 | **Conditional protasis–apodosis integrity (אִם ... אָז / אִם ... וְ)**: a conditional protasis (אִם + clause) and its apodosis form a bipartite syntactic structure; splitting the protasis alone may violate ATU integrity when the protasis is referentially anaphoric without its apodosis | PARTIAL — validate_cross_verse_continuity covers the cross-verse case; within-verse not covered | JM §159e; WO §38.1 |
| G7 | **Fronted constituent binding (tight fronting)**: a syntactically fronted but grammatically bound constituent (topic-fronted object without resumptive, fronted PP in unmarked position) should merge with its clause per the fronting paradox — unless it is a casus pendens (resumptive pronoun present) | PARTIAL — validate_short_verse_fronting covers short-verse case; general case not covered | JM §156; WO §16.3.2 |
| G8 | **Casus pendens (left-dislocation) own-line**: a casus pendens (topic-fronted NP + resumptive pronoun in main clause) must appear on its own line (SJ5) | PARTIAL — covered inside validate_clause_nucleus_split as H15 guard but not as a positive detector | JM §156; WO §4.7 |
| G9 | **Infinitive absolute as predicate binding**: an infinitive absolute used predicatively (בָּרֹךְ אֶבֹרֶכְךָ) is a rhetorical intensification bound to its finite verb cognate and cannot be split from it | NOT COVERED | JM §123; WO §35.3 |
| G10 | **Participle as predicate in verbless clause — discourse function**: a predicative participle heading a verbless clause that represents ongoing/durative action (וְרוּחַ אֱלֹהִים מְרַחֶפֶת) must keep its subject and predicate on the same line | COVERED — validate_clause_nucleus_split H18.2 | JM §121; WO §37.6 |
| G11 | **Reported speech כִּי recitativum vs. causal-כִּי**: the recitativum-כִּי (direct-speech marker in divine speech contexts, כִּי + first-person divine content) is not a causal clause; it should be treated as SJ3 speech-act announcement content, not as a separate causal ATU | PARTIAL — validate_causal_ki guards for divine-speech contexts but not systematically | JM §157.3; WO §39.3.4 |
| G12 | **Verbless clause as complete predication**: a verbless clause with explicit subject + predicate nominal/adjectival is a complete atomic thought; it must not be merged with a following clause merely because it lacks an overt finite verb | PARTIAL — validate_clause_nucleus_split H18.1 guards against SPLITTING them; no validator guards against MERGING them when they should split | JM §154; WO §8.4 |

---

## Item 3 — Proposed Validator Specs (Drafts Only)

Each implementation below requires its own §7.3 pre-build adversarial audit (≥2 parallel agents) before any code is written. These are constraint-style draft specs.

---

### validate_restrictive_relative_binding.py

**Constraint description:** A restrictive (defining) אֲשֶׁר-clause cannot form a standalone ATU or be split from its antecedent head noun. The diagnostic: if removing the relative clause would leave the head noun uniquely identifiable without the clause, the clause is non-restrictive (may stand alone if it passes bidirectional test). If not, it is restrictive and must remain bound to the head.

**Trigger pattern:**
- A sense-line ends with a noun phrase (no finite verb) that has a Macula NPofNP or NP parent
- The immediately following sense-line opens with אֲשֶׁר (relative particle)
- Macula IR: the אֲשֶׁר-headed relative clause is a direct `relCL` child of the prior line's head noun's NP constituent

**Diagnostic (yes/no audit question):**
"Is the אֲשֶׁר-clause on sense-line N+1 a restrictive (relCL) modifier of the head noun on sense-line N, making line N referentially incomplete without it?"

**Severity:** REVIEW-REQUIRED (restrictive vs. non-restrictive distinction requires context; edge cases exist)

**Constraint framing:** "Does this ATU break occur inside a restrictive relative-clause dependency arc?" — a pure syntactic well-formedness question.

**Note:** The Macula lowfat IR contains `wg_class="relp"` for relative clause phrase constituents and has the head-noun → relative-clause dependency relationship. This is the right primitive. The validator would walk Macula `relp` constituents, map their head noun to the prior sense-line, and fire when the head is on line N and the relative-clause opener (אֲשֶׁר) is on line N+1.

---

### validate_gapped_verb_parallel.py

**Constraint description:** In a synonymous bicolon where the second colon's verb is gapped (elided) from the first colon's verb, the second colon is still forward-closed (the gapped verb is recoverable). The strict bidirectional test would fail the gapped colon (no explicit finite verb), but the gapping makes it propositionally complete.

**Trigger pattern:**
- Sense-line N has a finite verb (Macula `is_finite_verb`)
- Sense-line N+1 has no finite verb but shares morpho-syntactic parallelism with line N (same PP structure, same nominal subject, parallel predicate role)
- Macula IR: line N+1 tokens are semantically parallel (similar role labels: Subj, Obj, or PP-Adjunct) to line N's non-verbal constituents

**Diagnostic (yes/no audit question):**
"Is the verbless sense-line N+1 in a parallel bicolon where the finite verb from line N is syntactically recoverable (gapped), such that line N+1 is propositionally complete by gapping?"

**Severity:** REVIEW-REQUIRED (gapping identification requires parallel-structure confirmation; FP risk)

**Constraint framing:** "Does this verbless line fail the atomic-thought test falsely because its governing verb is gapped from the parallel preceding line?" — audits the bidirectional-test result for false-fail cases.

**Note:** JM §174 (gapping in parallelism). Macula's symmetry between role labels across parallel cola is the right primitive. This validator would catch the Ps 1:1 failure mode described in the directive (over-split of gapped bicola).

---

### validate_discourse_particle_binding.py

**Note:** This constraint is substantially covered by validate_bare_discourse_particle (M3 + H14). The existing validator catches the most common case (bare particle alone on a line). What it does NOT catch is a particle that leads a clause but is also syntactically stranded from its clause when a line break occurs mid-clause after the particle but before the clause's predicate.

**Trigger pattern (gap extension):**
- Sense-line N ends with לָכֵן / וְעַתָּה / הִנֵּה / אָז + a following NP but no finite verb
- Sense-line N+1 contains the finite verb or predicate completing the particle's governed clause
- This is a "mid-governed-clause break after particle + subject" case (distinct from bare-particle-alone)

**Diagnostic:**
"Is a discourse particle's governed clause split across lines, with the particle + its nominal subject on line N and the finite predicate on line N+1?"

**Severity:** STRONG-MERGE-CANDIDATE where Macula confirms the finite verb on N+1 is the clause head governed by the particle on N.

**Constraint framing:** Extension of M3 to the particle + partial governed clause case (not just the bare-particle case).

---

### validate_purpose_clause_binding.py

**Constraint description:** A לְ + infinitive-construct purpose clause modifying a matrix finite verb is subordinate; it cannot be separated from its matrix verb and treated as an independent ATU.

**Trigger pattern:**
- Sense-line N ends with a finite verb
- Sense-line N+1 begins with לְ + infinitive-construct (Macula: `is_infinitive_construct == True`, `lemma != "אָמַר"` — exclude speech marker לֵאמֹר which is covered by H5)
- Macula IR: the infinitive-construct on N+1 has a purpose-clause (`adv-c` or similar) dependency role to the verb on N

**Diagnostic:**
"Is the לְ + infinitive-construct on sense-line N+1 a purpose-clause modifier of the finite verb on sense-line N, making line N+1 a subordinate ATU that cannot stand independently?"

**Severity:** REVIEW-REQUIRED (purpose-clause vs. substantive-adjunct independence is editorial judgment for substantial purpose clauses; STRONG for short cases where the infinitive is clearly subordinate with no independent predicative content)

**Constraint framing:** "Does this ATU break occur inside a purpose-clause dependency (matrix finite verb on N → purpose infinitive on N+1)?" JM §168; WO §36.2.2.

---

### validate_conditional_protasis_apodosis.py

**Constraint description:** A conditional protasis (אִם + clause) is referentially anaphoric to its apodosis; the protasis alone fails the backward-referential-self-containment prong of the bidirectional ATU test. The protasis should stay with its apodosis unless it is long enough and syntactically rich enough to qualify as SJ5 (substantive adjunct).

**Trigger pattern:**
- Sense-line N begins with אִם (conditional particle) + finite clause
- Sense-line N+1 contains the apodosis clause (usually beginning with wayyiqtol or a bare finite verb)
- AND line N is short (≤4 prosodic words) — suggesting a light protasis that cannot independently qualify as SJ5

**Diagnostic:**
"Is the conditional protasis on sense-line N a light clause (≤4 words) that fails backward self-containment without its apodosis on N+1?"

**Severity:** REVIEW-REQUIRED (protasis weight determines whether SJ5 applies; short protases are strong candidates for merge; long protases with own internal structure may qualify as SJ5)

**Constraint framing:** JM §159e; WO §38.1. Cross-reference the validate_cross_verse_continuity detection of conditional-subordinator stranding (sub-case a).

---

## Item 4 — Retirement / Refinement Proposals

### validate_parallel_clause_split — RETIRE or REFINE-TO-CONSTRAINT (High Priority)

**Current production logic:** Macula clause-boundary scan. When a single v2/heb line contains tokens spanning ≥2 distinct clause boundaries, each with its own finite-verb head, emit STRONG-SPLIT-CANDIDATE.

**Is the underlying rule a real constraint?** Partially. "Two coordinate finite-verb-headed clauses should each be on their own line" IS derivable from the generative principle (each proposition splits by default). But the rule is a production instruction ("split this merged line"), not a syntactic constraint ("this break violates a dependency"). The 32% structurally confident FP rate (COMPLEMENT-FP: matrix verb + clausal complement miscategorized as parallel; SUBORDINATE-FP: subordinate clause miscategorized as parallel) proves the production logic is over-firing.

**What the constraint form would be:** "Is this ATU break proposed by the LLM renderer splitting a line that actually contains two coordinate independent finite-verb-headed clauses?" — an audit question applied to LLM-proposed renderings, not a production instruction applied to merged lines in v2/heb.

**Proposal:** REFINE-TO-CONSTRAINT. In the new architecture, this validator should run in AUDIT mode against LLM-proposed renderings. Its role: "Check whether the proposed ATU boundaries correctly separate coordinate clauses and do not merge two independent finite-verb-headed clauses." The STRONG-SPLIT-CANDIDATE arm is retired; the validator becomes a check on LLM output rather than a production generator.

**Retirement risk:** 2,051 active findings become void. Most of these are currently unapplied REVIEW-REQUIRED findings (the corpus doesn't have 2,051 merged bicola — these are largely false-positive REVIEW findings that have accumulated without application). The risk of retiring the production arm is low.

---

### validate_speech_intro_framing — KEEP-AS-EDITORIAL-NOTE (Refine production arm)

**Current production logic:** Detects לֵאמֹר-bearing lines where frame and speech content appear on the same line (STRONG-SPLIT); detects bare speech-verb at line-end (REVIEW-REQUIRED).

**Is the underlying rule a real constraint?** Yes — H5b (Speech-Act Announcement Default) is grounded in SJ3 (speech-act announcement is a complete predication). The constraint is: "A speech-act announcement and its quoted content form two separate atomic thoughts; a break between them is required."

**However:** The STRONG-SPLIT arm is a production instruction (split this merged line). In the new architecture, this would be an audit check on LLM-proposed renderings that mistakenly merge announcement + content.

**Proposal:** REFINE. The underlying H5b constraint is real and should be preserved as a constraint audit. The STRONG-SPLIT-CANDIDATE arm (which fires when frame + content are merged) is legitimately a constraint check in audit mode (the LLM should not have merged these). Keep the validator; re-frame as post-LLM audit: "Does this sense-line illegally merge a speech-act frame with its quoted content?"

---

### validate_blessed_cursed_chain, validate_genealogy_uniformity, validate_parallel_series_uniformity — KEEP-AS-EDITORIAL-NOTE

**Current production logic:** All three implement the Parallel-List Uniformity Principle for specific corpus scopes. They prescribe rendering decisions.

**Is the underlying rule a real constraint?** No — the Parallel-List Uniformity Principle is a rendering preference, not a syntactic constraint. It says "members of a formally-marked list should have uniform line treatment." This is not a Hebrew grammatical fact; it is an editorial canon.

**Proposal:** In the new architecture, these validators should be retained as editorial-note generators (REVIEW-REQUIRED only, never STRONG). Their role is to surface uniformity violations for editorial review, not to mandate rendering decisions. They remain valid work-queue generators but should not be classified as constraint validators.

---

### validate_causal_ki — REFINE-TO-CONSTRAINT (separate constraint arm from production arm)

**Current production logic:** Fires STRONG-SPLIT-CANDIDATE when a line is followed by כִּי + finite verb that is classified as causal.

**Is the underlying rule a real constraint?** The constraint form is: "Is this כִּי a causal subordinating conjunction introducing a genuine adverbial clause (as opposed to a complement-כִּי)?" — a real syntactic discrimination. But the production arm (recommending a split) is a rendering decision based on that discrimination.

**Proposal:** REFINE. Split into two validators:
1. **validate_causal_ki_guard** (CONSTRAINT): "Is this כִּי a complement (H7 territory) or a causal? If complement, the current break is a H7 violation (should merge)." This arm runs as a constraint audit on LLM-proposed renderings.
2. The split recommendation arm (the current STRONG-SPLIT-CANDIDATE) is retired — in the new architecture the LLM handles this naturally.

---

### validate_short_orphan_line — REFINE (tighten standalone-permitted list; promote STRONG arm)

**Current production logic:** Flags any 1-prosodic-word line not in the standalone-permitted list as REVIEW-REQUIRED.

**Is the underlying rule a real constraint?** Yes — M4 (Fragmented Atomic Thought-Unit) is a genuine constraint. A single bare token that fails the atomic-thought test is a real violation.

**Proposal:** REFINE. The standalone-permitted list (sentence-final verbs, classical commas, vocatives) should be tightened with Macula IR confirmation: if the 1-word line's token has a Macula role that makes it a clause head (finite verb in main-clause position), it passes; if it is a bare nominal without any predicative role, it fails. Promote high-confidence cases (bare nominal, no IR role confirmation) to STRONG-MERGE-CANDIDATE. The 2,453 REVIEW-REQUIRED count likely contains a large number of promotable cases.

---

## Item 5 — Architecture-Pipeline Refactor Scope

### New Pipeline Architecture

Per the directive's empirical evidence (Ps 1 four-leg analysis: LLM + bidirectional test alone = 5/6 match; validators as producers = 0/4 needed corrections caught):

```
Stage 1: LLM-FIRST (audit_rendered_output.py) — primary ATU rendering
Stage 2: CONSTRAINT-AUDIT — refined validator stack runs as CHECK layer
Stage 3: EDITORIAL REVIEW — Stan adjudicates validator constraint flags
```

### Scripts That Touch the Refactor

#### scripts/audit_rendered_output.py
**Current role:** Secondary auditor.
**New role:** Primary ATU rendering engine.
**Changes needed:**
- Prompt revision: remove cognitive-unity gate (empirically inert per Ps 1 analysis); add restrictive-relative-binding rule (to close the Ps 1 v.3 over-split failure); add gapped-verb parallel recognition (to close the Ps 1 v.5 over-merge failure)
- Output format: produce proposed ATU line-breaks per verse, not just audit findings
- Integration: feeds into constraint-audit layer (Stage 2) rather than running as end-stage

#### scripts/apply_validators.py
**Current role:** Applies STRONG validator findings to v2/heb corpus.
**New role:** Runs constraint-audit validators against LLM-proposed renderings.
**Changes needed:**
- New run mode: `--audit-mode` — applies validator stack to LLM-proposed renderings (Stage 2), not to v2/heb corpus directly
- Existing `--diff-apply` mode (Category A mechanical apply) preserved for remaining CONSTRAINT validators
- PRODUCER validators (validate_parallel_clause_split, validate_blessed_cursed_chain, etc.) removed from ADOPTED_VALIDATORS or moved to EDITORIAL_NOTE_VALIDATORS
- New registry: `CONSTRAINT_VALIDATORS` (pure constraint audit, emit CONSTRAINT-VIOLATION findings) vs. `EDITORIAL_NOTE_VALIDATORS` (emit REVIEW-REQUIRED suggestions)

#### scripts/refresh_book.py
**Current role:** Cascades validator findings to v2/heb.
**New role:** Orchestrates three-stage pipeline per chapter.
**Changes needed:**
- Stage 1 call: invoke `audit_rendered_output.py --book X --chapter Y` → produces proposed ATU file
- Stage 2 call: invoke `apply_validators.py --audit-mode --proposed-file <stage1-output>` → produces constraint flags
- Stage 3 output: write constraint flags to review queue (not auto-applied)
- Preserve existing `--diff-apply` path for Category A CONSTRAINT validators that are still auto-applicable (H1, H2, M1, M2, M3 clear-STRONG cases)

#### scripts/build_books.py
**Current role:** Builds HTML from v2/heb.
**Changes needed:** None to the build logic itself. The v2/heb file remains the ground truth. The pipeline's output is a set of proposed edits and constraint flags that flow through editorial review before being committed to v2/heb.

#### validators/apply_validators.py (registry)
**Changes needed:**
- `ADOPTED_VALIDATORS` → split into `CONSTRAINT_VALIDATORS` and `EDITORIAL_NOTE_VALIDATORS`
- Remove from CONSTRAINT_VALIDATORS: validate_parallel_clause_split, validate_blessed_cursed_chain, validate_genealogy_uniformity, validate_parallel_series_uniformity (PRODUCER), validate_speech_intro_framing (move to EDITORIAL_NOTE)
- Keep in CONSTRAINT_VALIDATORS: all 14 CONSTRAINT-classified validators
- Add (after §7.3 audit): validate_restrictive_relative_binding, validate_gapped_verb_parallel, validate_purpose_clause_binding

### Baseline Regression Risk Assessment

**Risk level: MEDIUM-HIGH** for the transition period.

The primary risk is that removing PRODUCER validators from auto-apply may leave the corpus in a state where previously-applied production rules are no longer enforced. Specific risks:

1. **validate_parallel_clause_split retirement:** 2,051 active findings → void. If any were previously applied, corpus changes are not at risk (they're already committed). Future new text won't be checked for merged bicola automatically. Mitigated by: LLM-first pipeline will naturally split coordinate clauses via the bidirectional test.

2. **validate_short_orphan_line:** 2,453 REVIEW-REQUIRED findings remain unapplied. No regression risk from retiring the production arm; the constraint arm (M4 core) should be strengthened with IR confirmation.

3. **validate_causal_ki split:** 992 REVIEW-REQUIRED findings remain unapplied. No regression risk to corpus.

4. **validate_speech_intro_framing re-role:** 603 findings. If re-framed as audit-mode check, previously applied STRONG-SPLIT changes in v2/heb are preserved; new text entering the corpus via LLM-first pipeline will be checked for H5b violations in audit mode.

**Safe order of operations:**
1. Mark PRODUCER validators as `EDITORIAL_NOTE_VALIDATORS` (not removed, just de-escalated to REVIEW-REQUIRED-only)
2. Implement `audit_rendered_output.py` prompt revision (Stage 1 improvements)
3. Build constraint-audit mode in `apply_validators.py` (Stage 2 infrastructure)
4. Run regression check: apply CONSTRAINT validators in audit mode to a sample of existing v2/heb chapters; verify finding counts don't dramatically change
5. Implement new constraint validators (Items G1-G5) one at a time, each with §7.3 adversarial audit

**Regression gate (mandatory before corpus-wide cascade):**
- Baseline: run all CONSTRAINT validators on current v2/heb (record finding counts)
- After refactor: run CONSTRAINT validators on same corpus
- Accept: finding counts stable (±5%) or decreasing (improvements)
- Reject: finding counts increasing >10% without corresponding corpus-error explanation

---

## Summary

**Item 1:** 14 CONSTRAINT, 5 PRODUCER, 6 MIXED, 2 META

**Item 2:** 17 constraints currently covered; 12 identified as NOT COVERED or under-covered (G1–G12), of which 5 are fully NOT COVERED (G1 restrictive-relative, G2 non-restrictive-relative, G3 gapped-verb parallel, G5 purpose-clause binding, G9 infinitive-absolute predicate binding).

**Item 3:** 5 new validator specs drafted (validate_restrictive_relative_binding, validate_gapped_verb_parallel, validate_discourse_particle_binding extension, validate_purpose_clause_binding, validate_conditional_protasis_apodosis). Each requires §7.3 adversarial audit before implementation.

**Item 4 top-3 retirement candidates:**
1. validate_parallel_clause_split — REFINE-TO-CONSTRAINT (retire production arm; 2,051 findings void)
2. validate_causal_ki — REFINE (split constraint arm from production arm; 992 findings restructured)
3. validate_speech_intro_framing — REFINE (re-role as audit-mode H5b constraint check; 603 findings restructured)

**Item 5 blast radius:** Medium. Scripts affected: audit_rendered_output.py (prompt), apply_validators.py (registry + new audit mode), refresh_book.py (three-stage orchestration). build_books.py unchanged. No v2/heb file modifications; pipeline topology changes only. The v2/heb corpus remains the ground truth throughout.
