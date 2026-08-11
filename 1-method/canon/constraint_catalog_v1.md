# Hebrew Constraint Catalog v1

> **Restored from `_archive/` on 2026-08-11.** Commit `922001bc0` (2026-05-18)
> moved this file out, describing it as *"superseded"* by the mechanical-first
> rewrite. It was not superseded. `atu-method/1-method/binding-rules-hebrew.md`
> operates at the **clause-atom binding** layer — vocative, restrictive ʾăšer,
> wayhi frames, casus pendens, neʾum. This catalog operates at the **prosodic
> and NP** layer — maqqef groups, proclitic stranding, construct chains, bonded
> pairs. Word counts across the two files: maqqef 15 / 0, proclitic 11 / 0,
> bonded 13 / 0, construct chain 20 / 0. They are complementary, not rival
> versions of one thing, and archiving this left the prosodic layer with no
> documentation at all while the validators implementing it kept running.
>
> **What the supersession got right, and this file still owes.** The B-rules
> justify every rule against the bidirectional test, carry counter-examples that
> must *not* fire, and state known limitations. This catalog does none of that.
> A `Source` line is a weaker warrant than it looks: Joüon §129 establishes that
> the construct chain is a nominal unit — it does not license never breaking one
> across a colometric line. That inference is ours and is nowhere stated here.
>
> **Therefore neither document is finished.** The target is a merged catalog in
> which every constraint carries BOTH an external `Source` (anchoring the unit,
> checkable by a peer) AND a bidirectional-test justification (doing the
> editorial work), with the inferential step between them named rather than
> assumed. Tracked in `atu-method/2-evidence/traceability-tanakh.md`.
>
> **`Status: DRAFT` below stands.** No entry here has been corpus-fixture
> validated. Restoration reconnects the six live sub-files in `constraints/`
> to their master index; it does not promote this to settled canon.

```yaml
catalog_version: v1
last_reviewed: 2026-05-17
status: DRAFT — all entries Status: DRAFT pending corpus-fixture validation
composition_rule: >
  Highest-priority HARD constraint wins. Two BIND constraints on the same
  boundary → JUDGMENT-REQUIRED. HARD always overrides ADVISORY. Within the
  same tier and precedence, lower precedence-integer wins.
implementation_conventions:
  - >
    **NFC normalization discipline (mandatory).** All Hebrew string literals
    used in Token.lemma / Token.pos / closed-list comparisons MUST be
    NFC-normalized at module load. Use `unicodedata.normalize("NFC", literal)`
    on every literal. Lowfat XML normalizes to NFC at parse; comparison strings
    must match. Failing to NFC-normalize produces silent matching failures.
  - >
    **Prosodic-word counting.** Every weight-threshold guard (≤N / ≥N prosodic
    words) MUST use `validators._shared.macula_constituents.prosodic_word_count(
    tokens)` for the count. Raw token-length is wrong: maqqef-bound tokens
    collapse to one prosodic word.
  - >
    **Sense-line → token mapping preamble.** For every constraint that operates
    on sense-line content (every line-boundary constraint), the implementation
    MUST start by retrieving the line's tokens via
    `match_sense_line_tokens(verse_tokens, sense_line_text, start_idx)`.
    Predicates on `Token` cannot be applied to raw sense-line strings.
  - >
    **Frame-arg safety pattern.** `Token.frame_args` is sparse in lowfat —
    many verbs lack frame annotation. Use `verb.frame_args.get("A1") or []`,
    never `verb.frame_args["A1"]`. Implement surface fallback for missing frame
    coverage (e.g., אֵת-marker detection for direct objects).
  - >
    **Bonded-noun-pair lookup.** JM177 uses the 13-pair structural list at
    `validators/_shared/bonded_noun_pairs.py` (`BONDED_NOUN_PAIRS` frozenset
    of frozensets; `is_bonded_pair(lemma_a, lemma_b)` helper). NOT the 88-pair
    `BONDED_LEMMA_PAIRS` in `hendiadys_lemma_pairs.py` (DORMANT verb list,
    reference-only).
bidirectional_test: >
  This catalog EXCLUDES bidirectional-test logic. Forward closure
  (does this line's proposition carry forward?) and backward containment
  (is this line self-referentially complete?) are the ATU rendering prompt's
  domain — not the constraint catalog's. Constraints here encode Hebrew
  syntactic dependency arcs that prohibit or require specific line boundaries
  regardless of propositional bidirectional weight.
open_gaps:
  - JM123-inf-abs-predicate: infinitive-absolute predicate binding (G9) — Macula
    operationalization unclear; `type_="infinitive absolute"` exists but
    predicate-role detection requires clause-function disambiguation
  - JM156-general-fronting: generalized fronted-constituent binding beyond
    short-verse case — Macula topicalization role label needed; lowfat `role`
    values for fronted-topic not confirmed
  - JM172-coordinate-vs-subordinate: systematic coordinate/subordinate-waw
    discrimination — Macula `wg_class="cjp"` identifies conjunction phrases
    but subordinate-vs-coordinate clause-type still needs clause-head
    verb-type query
  - JM160-negation-scope: negation-scope binding across line boundaries —
    `pos="particle"` + negation lemma present but scope determination is
    clause-head distance, not yet formalized
  - JM125-DO-marker-scope: אֵת + heavy NP spread across two lines — overlaps
    JM125-verb-object-bond but needs dedicated multi-token DO-marker case
```

---

## Master Index

| ID | Short Title | Verdict Family | Tier | Prec | Source |
|---|---|---|---|---|---|
| [JM13-maqqef-group](#jm13-maqqef-group) | Maqqef-group indivisibility | BIND | HARD | 1 | JM §13 |
| [JM103-proclitic-stranding](#jm103-proclitic-stranding) | Proclitic line-final stranding | BIND | HARD | 1 | JM §103 |
| [JM103e-compound-prep-object](#jm103e-compound-prep-object) | Compound-preposition object stranding | BIND | HARD | 1 | JM §103e |
| [JM129-construct-chain](#jm129-construct-chain) | Construct-chain integrity | BIND | HARD | 2 | JM §129 |
| [JM125-verb-object-bond](#jm125-verb-object-bond) | Verb–direct-object nucleus bond | BIND | HARD | 2 | JM §125 |
| [JM125-coordinated-objects](#jm125-coordinated-objects) | Coordinated direct-object integrity | BIND | HARD | 2 | JM §125 |
| [JM157-complement-integrity](#jm157-complement-integrity) | Obligatory-complement integrity | BIND | HARD | 2 | JM §157 |
| [JM177-bonded-pair](#jm177-bonded-pair) | Bonded pair (hendiadys/merism) | BIND | HARD | 2 | JM §177 |
| [JM154-verbless-clause-nucleus](#jm154-verbless-clause-nucleus) | Verbless-clause nucleus integrity | BIND | HARD | 3 | JM §154 |
| [JM121-participial-predicate](#jm121-participial-predicate) | Participial-predicate nucleus integrity | BIND | HARD | 3 | JM §121 |
| [JM133-verb-pp-complement](#jm133-verb-pp-complement) | Verb–PP complement bond | BIND | HARD | 3 | JM §133 |
| [JM155-discourse-particle](#jm155-discourse-particle) | Bare discourse-particle indivisibility | BIND | HARD | 3 | JM §155 |
| [JM161-interrogative-particle](#jm161-interrogative-particle) | Bare interrogative-particle indivisibility | BIND | HARD | 3 | JM §161 |
| [JM156-casus-pendens](#jm156-casus-pendens) | Casus pendens own-line | SPLIT | HARD | 3 | JM §156 |
| [JM-oath-formula](#jm-oath-formula) | Oath-formula integrity | BIND | HARD | 3 | JM §147 / formula integrity |
| [JM-cross-verse-continuity](#jm-cross-verse-continuity) | Cross-verse grammatical-unit continuity | BIND | HARD | 4 | JM §1 / canon H10 |
| [JM-wayehi-fef-protasis](#jm-wayehi-fef-protasis) | Wayehi-FEF protasis integrity | BIND | HARD | 4 | JM §155 / WO §33.1.1c |
| [JM158-restrictive-relative](#jm158-restrictive-relative) | Restrictive relative-clause binding | BIND | ADVISORY | 5 | JM §158 |
| [JM158-nonrestrictive-relative](#jm158-nonrestrictive-relative) | Non-restrictive relative-clause licensing | INFORM | ADVISORY | 7 | JM §158 |
| [JM168-purpose-clause](#jm168-purpose-clause) | Purpose-clause infinitive binding | JUDGMENT-REQUIRED | ADVISORY | 5 | JM §168 |
| [JM159e-conditional-protasis](#jm159e-conditional-protasis) | Conditional protasis–apodosis integrity | JUDGMENT-REQUIRED | ADVISORY | 5 | JM §159e |
| [JM174-gapped-verb](#jm174-gapped-verb) | Gapped finite verb in parallel bicolon | INFORM | ADVISORY | 6 | JM §174 |
| [JM157-ki-recitativum](#jm157-ki-recitativum) | כִּי recitativum vs causal disambiguation | JUDGMENT-REQUIRED | ADVISORY | 5 | JM §157.3 |
| [JM123-inf-abs-predicate](#jm123-inf-abs-predicate) | Infinitive absolute as predicate binding | BIND | HARD | 3 | JM §123 |
| [JM147-vocative-extraclausal](#jm147-vocative-extraclausal) | Vocative and extra-clausal element placement | INFORM | ADVISORY | 6 | JM §147 |
| [JM160-negation-scope](#jm160-negation-scope) | Negation-particle scope binding | BIND | HARD | 2 | JM §160 |

Sub-files (per-construction detail):
- [constraints/bound_nominals.md](constraints/bound_nominals.md) — JM13, JM103, JM103e, JM129
- [constraints/clause_nucleus.md](constraints/clause_nucleus.md) — JM125-verb-object-bond, JM125-coordinated, JM157-complement, JM154-verbless, JM121-participial, JM133-verb-pp
- [constraints/particles_and_particles.md](constraints/particles_and_particles.md) — JM155, JM161, JM160, JM147
- [constraints/bonded_and_formula.md](constraints/bonded_and_formula.md) — JM177, JM-oath-formula, JM-cross-verse, JM-wayehi-fef
- [constraints/relative_clauses.md](constraints/relative_clauses.md) — JM158-restrictive, JM158-nonrestrictive
- [constraints/subordinate_clauses.md](constraints/subordinate_clauses.md) — JM168-purpose, JM159e-conditional, JM157-ki-recitativum, JM174-gapped, JM156-casus-pendens, JM123-inf-abs

---

## Constraint Entries

---

### JM13-maqqef-group

**Maqqef-group indivisibility**

- **Encoded question**: Does a line break fall inside a maqqef-group (two-to-four tokens joined by ־)?
- **Verdict family**: BIND
- **Tier**: HARD
- **Precedence**: 1
- **Source**: Joüon §13; Layer 1 hebrew-break-legality.md row H1
- **Macula operationalization**: `Token.has_maqqef_after()` — True when `token.after == "־"`. Any line boundary between token N (where `has_maqqef_after()` is True) and token N+1 violates this constraint.
- **Status**: DRAFT
- **Backward-compat**: C1 (1100 catalog)
- **Diagnostic examples**:
  - Positive (fires): Gen 1:1 וְאֵת־הָאָרֶץ — maqqef joins אֵת and הָאָרֶץ; line break between them = BIND violation
  - Positive (fires): Jonah 1:4 רוּחַ־גְּדוֹלָה — maqqef joins noun + adjective; break inside = violation
  - Negative (does not fire): Jonah 1:3 דְּבַר־יְהוָה where maqqef is within a construct chain — the maqqef fires; construct-chain constraint JM129 is also present but subordinate; this entry covers the glyph-level prohibition
  - Negative (does not fire): any token where `after` is a space or sof-pasuq — no maqqef, constraint inactive
- **Edge-case handling**: When a maqqef-group spans three or four tokens (e.g., מִן־הַשָּׁמַיִם), the constraint fires for every internal boundary in the chain; the entire group must stay on one line. Maqqef chains at verse-end followed by sof-pasuq do not create a continuation obligation into the next verse — the sof-pasuq closes the group.

---

### JM103-proclitic-stranding

**Proclitic line-final stranding**

- **Encoded question**: Does a line end with a morphological proclitic (conjunction-prefix וְ/וַ/וּ, preposition-prefix מ/ב/כ/ל, definite article הַ/הָ/הֶ, direct-object marker אֵת/אֶת, negation particle לֹא/אַל) that cannot constitute a prosodic word alone?
- **Verdict family**: BIND
- **Tier**: HARD
- **Precedence**: 1
- **Source**: Joüon §103 (prepositions), §137 (conjunction waw), §125 (object marker), §160 (negation)
- **Macula operationalization**: `Token.pos` — proclitic tokens have `pos` in {"conjunction", "preposition", "article", "particle"} combined with `Token.type_` and `Token.lemma` membership in the closed proclitic list. Specifically: conjunction-prefixed words have the conjunction as a morpheme; line-final bare prefixes before their host = VIOLATION. In practice Macula lowfat tokenizes these as prefixed morphemes on the host word, so a standalone line-final proclitic appears as a token whose `pos="conjunction"` or `pos="preposition"` and `lemma` matches the prefix lemma with no host-word text beyond the prefix.
- **Status**: DRAFT
- **Backward-compat**: C2 (1100 catalog)
- **Diagnostic examples**:
  - Positive (fires): line ending with bare וְ (conjunction prefix without host) — MALFORMED, BIND
  - Positive (fires): line ending with bare לְ (preposition prefix without complement noun) — BIND
  - Negative (does not fire): line ending with וְהָאָרֶץ (conjunction + article + noun — full prosodic word, constraint inactive)
  - Negative (does not fire): line ending with הָאָרֶץ (bare noun, no proclitic issue)
- **Edge-case handling**: The negation particles לֹא and אַל are not morphological prefixes in the same sense as וְ/לְ, but they require a following verb or adjective for propositional closure. A line ending with bare לֹא stranded from its verb is a proclitic-stranding violation at the prosodic-word level. אֵין as existential negation (Joüon §160c) requires its predicate on the same line unless the predicate is a full clause licensed by JM156-casus-pendens. Distinguish: לֹא as negation of a finite verb = BIND; לֹא in fixed formulaic use (e.g., לֹא in an oath clause) = evaluate under JM-oath-formula.

---

### JM103e-compound-prep-object

**Compound-preposition object stranding**

- **Encoded question**: Does a line end with a multi-morpheme compound preposition (מִלִּפְנֵי, מִפְּנֵי, מִתַּחַת, מֵאַחֲרֵי, מִנֶּגֶד, בְּתוֹךְ, לִפְנֵי, etc.) whose governed NP begins the next line?
- **Verdict family**: BIND
- **Tier**: ADVISORY  <!-- v1.1 demotion: JM §103e descriptive; see commit message + audit log -->

- **Precedence**: 1
- **Source**: Joüon §103e
- **Macula operationalization**: Macula `wg_class="pp"` (prepositional phrase) where the head preposition token lands on line N but the complement NP tokens (`role="o"` within the pp) begin on line N+1. Query: `Constituent.is_pp` → True, then check if head preposition token is on a different sense-line than its object tokens.
- **Status**: DRAFT
- **Backward-compat**: C3 (1100 catalog)
- **Diagnostic examples**:
  - Positive (fires): line ends with מִלִּפְנֵי, next line begins with הַמֶּלֶךְ — compound prep stranded from object = BIND
  - Positive (fires): line ends with בְּתוֹךְ, next line has NP object — BIND
  - Negative (does not fire): line ends with מִלִּפְנֵי הַמֶּלֶךְ (prep + object on same line) — no stranding
  - Negative (does not fire): simple single-morpheme preposition prefix (בְּ, לְ, מִן) stranded from its noun — covered by JM103-proclitic-stranding, not this entry
- **Edge-case handling**: Some compound prepositions are themselves construct chains (e.g., לִפְנֵי = לְ + פָּנִים construct). The compound-preposition constraint fires on the full preposition unit regardless of internal morpheme structure. When a compound preposition is followed by a pronominal suffix rather than a NP, no line-boundary is possible (suffix is phonologically joined); constraint is vacuously satisfied.

---

### JM129-construct-chain

**Construct-chain integrity**

- **Encoded question**: Does a line boundary fall inside a construct chain (nomen regens in construct state without its nomen rectum)?
- **Verdict family**: BIND
- **Tier**: HARD
- **Precedence**: 2
- **Source**: Joüon §129; WO §9.3, §9.5; canon H2
- **Macula operationalization**: `Constituent.is_construct_chain` — True when `wg_rule == "NPofNP"`. Walk NPofNP constituents; if regens tokens land on line N and rectum tokens on line N+1 = BIND. Primary: `validate_construct_chain.py` (Macula IR path). Fallback: `Token.is_construct` — True when `state == "construct"` — for parser-missed cases.
- **Status**: DRAFT
- **Backward-compat**: C4 (1100 catalog)
- **Diagnostic examples**:
  - Positive (fires): דְּבַר on line N (construct state), יְהוָה on line N+1 — NPofNP split = BIND
  - Positive (fires): בֵּית on line N, הַמֶּלֶךְ on line N+1 — construct chain split = BIND
  - Negative (does not fire): דְּבַר־יְהוָה on one line — maqqef-joined, no boundary possible
  - Negative (does not fire): absolute-state noun at line end — no construct dependency open
- **Edge-case handling**: Long construct chains (3+ levels deep, e.g., בֵּית אֱלֹהֵי הַשָּׁמַיִם) must keep all levels together; the constraint fires for any internal break in the chain. An intervening relative clause attached to the regens only (e.g., הַדָּבָר אֲשֶׁר־שָׁמַעְתָּ דְּבַר הָאֱלֹהִים) is an exception: the relative clause may occupy its own line when it is itself a substantial SJ5 adjunct. Construct chains interrupted by maqqef (internal to the chain) are already covered by JM13-maqqef-group; this entry covers non-maqqef construct chains.

---

### JM125-verb-object-bond

**Verb–direct-object nucleus bond**

- **Encoded question**: Does a finite verb's nominal direct object (Macula frame-arg A1) begin the next sense-line rather than appearing on the same line as the verb?
- **Verdict family**: BIND
- **Tier**: ADVISORY  <!-- v1.1 demotion per §7.3 retroactive audit; see commit + audit log -->
- **Precedence**: 2
- **Source**: Joüon §125; WO §10.2.1; canon M2
- **Macula operationalization**: `Token.frame_args["A1"]` — resolves to list of Token objects. If the finite verb token lands on line N and any A1 token lands on line N+1 = BIND. Use `Token.is_finite_verb` to identify the governing verb. Frame-arg resolution via `parse_frame_str()` on the governing verb's frame attribute in lowfat.
- **Status**: DRAFT
- **Backward-compat**: C5 (1100 catalog)
- **Diagnostic examples**:
  - Positive (fires): וַיֵּלֶךְ on line N, אֶת־הָאִשָּׁה on line N+1 — verb + A1 split = BIND
  - Positive (fires): רָאָה on line N (qatal), אֶת־הָאוֹר on line N+1 — BIND
  - Negative (does not fire): וַיֵּלֶךְ אֶת־הָאִשָּׁה on one line — bond satisfied
  - Negative (does not fire): finite verb at line end whose A0 (subject) or A2 (indirect object) continues — subject/IO stranding is not covered by this entry (different frame-arg)
- **Edge-case handling**: When a verb has a very heavy A1 (NP with relative clause modifier, 6+ tokens), the DO may legitimately begin on a second line if the verb's own line is already at clause-nucleus weight. In such cases, the break should occur AFTER the אֵת DO-marker and the head noun are together with the verb on line N; the relative-clause modifier may begin line N+1. The constraint fires when the DO-marker + head-noun are stranded on N+1 away from the verb.

---

### JM125-coordinated-objects

**Coordinated direct-object integrity**

- **Encoded question**: When a single verb governs multiple coordinated A1 direct objects, are those A1 tokens distributed across distinct sense-lines rather than grouped together?
- **Verdict family**: BIND
- **Tier**: ADVISORY  <!-- v1.1 demotion per §7.3 retroactive audit; see commit + audit log -->
- **Precedence**: 2
- **Source**: Joüon §125; WO §10.2.1; canon M2 + SJ1
- **Macula operationalization**: `Token.frame_args["A1"]` returns multiple tokens when the verb has coordinated objects. If A1 tokens span two or more distinct sense-lines = BIND. Guard: combined token-weight of all A1 tokens ≤8 prosodic words (heavy coordinated objects may justify SJ1 series break).
- **Status**: DRAFT
- **Backward-compat**: C6 (1100 catalog)
- **Diagnostic examples**:
  - Positive (fires): verb takes A1-1 on line N, A1-2 on line N+1 with combined weight ≤8 words — BIND
  - Positive (fires): אֶת־הָאֱלֹהִים on line N, וְאֶת הַמֶּלֶךְ on line N+1, shared verb on line N-1 — BIND
  - Negative (does not fire): coordinated A1 objects combined ≥9 prosodic words — SJ1 series break licensed; constraint yields to JUDGMENT-REQUIRED
  - Negative (does not fire): verb with single A1 — covered by JM125-verb-object-bond, not this entry
- **Edge-case handling**: When a coordinated-object list has 3+ members (SJ1 formally-marked parallel series), the Parallel-List Uniformity Principle may license each member on its own line. This constraint defers to SJ1 for series of 3+ members with formal markers (vav + article or repetition pattern). For N=2 pairs, BIND wins unless combined weight ≥9 words. The N=2 Adjudication Principle (canon §1) applies: if both objects are themselves bonded-pair equivalents (M1), BIND still wins.

---

### JM157-complement-integrity

**Obligatory-complement integrity**

- **Encoded question**: Does a cognition/volition/causative verb appear at line-end with its grammatically obligatory כִּי-clause (or אֲשֶׁר-clause, or speech-content for causative verbs) beginning the next line?
- **Verdict family**: BIND
- **Tier**: ADVISORY  <!-- v1.1 demotion per §7.3 retroactive audit; see commit + audit log -->
- **Precedence**: 2
- **Source**: Joüon §157; WO §38.3; canon H7
- **Macula operationalization**: `Token.lemma` membership in OBLIGATORY_COMPLEMENT_VERBS closed list (יָדַע, רָאָה, שָׁמַע, אָמַר for complement use, צִוָּה, אָמַר ... כִּי class); next sense-line token `pos="conjunction"` + `lemma="כִּי"` or `lemma="אֲשֶׁר"`. Macula frame-arg A2 may carry the clausal complement ID for some verbs. Guard: if next line opens with כִּי that is causal (adverbial, not object), this constraint does NOT fire — see JM157-ki-recitativum for the disambiguation.
- **Status**: DRAFT
- **Backward-compat**: C7 (1100 catalog)
- **Diagnostic examples**:
  - Positive (fires): וַיֵּדַע on line N, כִּי טוֹב הָאוֹר on line N+1 — obligatory complement = BIND
  - Positive (fires): וַיַּרְא אֱלֹהִים on line N, כִּי טוֹב on line N+1 (Gen 1 pattern) — BIND
  - Negative (does not fire): וַיִּשְׁמַע on line N, כִּי as causal ("because he heard...") on line N+1 — causal כִּי, not complement; this entry does not fire
  - Negative (does not fire): verb from OBLIGATORY_COMPLEMENT_VERBS with its כִּי-clause on the same line — complement satisfied, no stranding
- **Edge-case handling**: Long-complement exception: when the כִּי-clause is itself long (≥8 prosodic words or itself contains a relative clause), it may occupy its own line as a substantive complement colon (SJ5 substantive adjunct). In this case the constraint is satisfied but a split is licensed. The HARD BIND fires only when the complement is short (≤7 prosodic words) and its separation from the matrix verb would produce a bare governing verb at line-end failing the Propositional Completeness Test.

---

### JM177-bonded-pair

**Bonded pair (hendiadys / merism / cognate pair)**

- **Encoded question**: Does a line break fall between two elements of a closed-list hendiadys, merism, or cognate pair that must function as a single rhetorical-semantic unit?
- **Verdict family**: BIND
- **Tier**: HARD
- **Precedence**: 2
- **Source**: Joüon §177; WO §4.6.5; canon M1
- **Macula operationalization**: Closed list: 13-pair structural bonded-noun list at `validators/_shared/bonded_noun_pairs.py` (`BONDED_NOUN_PAIRS` frozenset; `is_bonded_pair(lemma_a, lemma_b)` helper). Distinct from the 88-pair DORMANT `BONDED_LEMMA_PAIRS` in `hendiadys_lemma_pairs.py` (verb-pair list, reference-only — do NOT use). Trigger: sense-line N ends with token T1 (`T1.lemma` in some pair), sense-line N+1 begins with `pos == "conjunction"` + lemma "ו" (or proclitic וְ prefix on next token) + token T2 (`T2.lemma` in same pair as T1). Guard: no finite verb on either line (prevents misfiring on verbal coordination). Lemmas MUST be NFC-normalized per implementation_conventions.
- **Status**: DRAFT
- **Backward-compat**: C11 (1100 catalog)
- **Diagnostic examples**:
  - Positive (fires): חֶסֶד on line N, וֶאֱמֶת on line N+1 — M1 bonded pair, BIND
  - Positive (fires): שָׁמַיִם on line N, וָאָרֶץ on line N+1 — merism pair, BIND
  - Negative (does not fire): שָׁמַיִם on line N (finite verb present on same line — guard fires; pair is within a verbal clause, no M1 bonded-pair stranding)
  - Negative (does not fire): two nouns not in 13-pair closed list, separated across lines — not covered by this entry; evaluate under SJ1 or as independent cola
- **Edge-case handling**: The 88-pair BONDED_LEMMA_PAIRS lexicon is DORMANT (codified 2026-05-16) — not mechanically consulted. Only the 13-pair structural list is active. For potential bonded pairs outside the 13-pair list, the verdict is JUDGMENT-REQUIRED at Category B editorial review. Asymmetric-modifier sub-clause: if one pair member carries a PP modifier, BIND still wins if the modifier scopes over the pair-as-unit; SPLIT only if the modifier produces genuinely distinct predicative force over one member only (canon §1 M1 asymmetric-modifier clause).

---

### JM154-verbless-clause-nucleus

**Verbless-clause nucleus integrity**

- **Encoded question**: Is the subject of a verbless clause (nominal / adjectival predication) on line N while the predicative PP or nominal predicate begins line N+1, splitting the verbless-clause nucleus?
- **Verdict family**: BIND
- **Tier**: ADVISORY  <!-- v1.1 demotion per §7.3 retroactive audit; see commit + audit log -->
- **Precedence**: 3
- **Source**: Joüon §154; WO §8.4; canon H18.1
- **Macula operationalization**: Detect verbless-clause pattern: line N ends with NP (no finite verb; `Token.is_finite_verb` = False for all tokens on line N); line N+1 begins with `wg_class="pp"` or nominal predicate (`pos="noun"` or `pos="adjective"` with `role="p"` in Macula). Clause boundary: both token sets are within the same Macula `wg_class="cl"` constituent. Guard: if line N is a casus pendens (resumptive pronoun follows — JM156-casus-pendens), this constraint defers; if line N is a discourse particle (JM155), that constraint takes priority.
- **Status**: DRAFT
- **Backward-compat**: C15 (1100 catalog)
- **Diagnostic examples**:
  - Positive (fires): וְהָאָרֶץ on line N (no verb), הָיְתָה תֹהוּ וָבֹהוּ on N+1 — subject stranded from predicate = BIND (Gen 1:2 pattern)
  - Positive (fires): הַשָּׁמַיִם on line N, כִּסֵּא יְהוָה on N+1 (verbless appositive predicate) — BIND
  - Negative (does not fire): וְהָאָרֶץ הָיְתָה תֹהוּ on one line — nucleus complete on line N, no split
  - Negative (does not fire): NP on line N followed by new finite verb on N+1 introducing a new clause — distinct clauses, not verbless-nucleus split; constraint inactive
- **Edge-case handling**: Heavy predicate exception: when the predicative PP or nominal predicate is itself long (≥6 prosodic words or contains embedded modifier), the split is licensed as SJ5 substantive adjunct. The BIND fires only for short predicate cases. Participial predicate: when line N ends with a subject NP and line N+1 begins with a predicative participle, this is covered by JM121-participial-predicate (which takes priority as a narrower rule).

---

### JM121-participial-predicate

**Participial-predicate nucleus integrity**

- **Encoded question**: Is a subject NP on line N separated from its predicative participle on line N+1, splitting a participial-predicate clause nucleus?
- **Verdict family**: BIND
- **Tier**: ADVISORY  <!-- v1.1 demotion per §7.3 retroactive audit; see commit + audit log -->
- **Precedence**: 3
- **Source**: Joüon §121; WO §37.6; canon H18.2
- **Macula operationalization**: `Token.is_participle` — True when `type_` in ("participle active", "participle passive"). Pattern: line N ends with NP (no finite verb), line N+1 opens with a token where `is_participle` = True. Both tokens fall within the same Macula `wg_class="cl"` constituent where the participle has `role="p"` (predicative). Guard: passive participial used attributively (adjectival modifier of a noun, not predicative) does not fire this constraint — check `role` attribute; attributive role is "a", predicative is "p".
- **Status**: DRAFT
- **Backward-compat**: C16 (1100 catalog)
- **Diagnostic examples**:
  - Positive (fires): וְרוּחַ אֱלֹהִים on line N, מְרַחֶפֶת עַל־פְּנֵי הַמַּיִם on N+1 (Gen 1:2) — subject + predicative participle split = BIND
  - Positive (fires): הַמֶּלֶךְ on line N, יוֹשֵׁב עַל־כִּסְאוֹ on N+1 — subject NP + predicative active participle = BIND
  - Negative (does not fire): הַמֶּלֶךְ הַיּוֹשֵׁב (attributive participle as adjective within NP) — attributive role, not predicative; constraint inactive
  - Negative (does not fire): subject + finite verb on N+1 — finite verb, not participial predicate; covered by JM125-verb-object-bond if applicable
- **Edge-case handling**: A predicative participle heading a verbless clause that represents ongoing action (discourse-function role, Joüon §121c) is subject to this constraint regardless of whether it is active or passive. Participial predicate with heavy complement (participle + PP complement ≥6 tokens) may license a split between the subject on line N and the participle-clause on line N+1 as a SJ5 substantive adjunct — evaluate the participle + its complement as a unit; the split should not occur WITHIN the participle phrase.

---

### JM133-verb-pp-complement

**Verb–PP complement bond**

- **Encoded question**: Is a finite verb with an obligatory PP complement (שָׁמַע לְ, פָּנָה אֶל, בָּטַח בְּ) on line N while that PP complement begins line N+1?
- **Verdict family**: BIND
- **Tier**: ADVISORY  <!-- v1.1 demotion per §7.3 retroactive audit; see commit + audit log -->
- **Precedence**: 3
- **Source**: Joüon §133; WO §11.4.1; canon H18.3 / M2
- **Macula operationalization**: `Constituent.is_pp` — True when `wg_class="pp"`. Check: finite verb token on line N; PP constituent (Macula `wg_class="pp"`) with `role="o"` or `role="pp"` (oblique) as argument of that verb, whose tokens begin line N+1. Closed-list verb-PP pairs for obligatory PP complements: OBLIGATORY_PP_VERBS (שָׁמַע + לְ, פָּנָה + אֶל, שָׁב + אֶל, בָּטַח + בְּ, חָטָא + לְ, etc.) — obligation determined by verb-class semantics.
- **Status**: DRAFT
- **Backward-compat**: C17 (1100 catalog)
- **Diagnostic examples**:
  - Positive (fires): וַיִּשְׁמַע on line N, לְקוֹל הָאִשָּׁה on N+1 — verb + obligatory PP complement stranded = BIND
  - Positive (fires): וַיִּפֶן on line N, אֶל־הַמִּדְבָּר on N+1 — BIND
  - Negative (does not fire): verb with optional/adjunct PP — adjunct PPs may stand on their own line as SJ5; not every verb + PP combination fires this constraint
  - Negative (does not fire): verb + PP on same line — no stranding
- **Edge-case handling**: Obligatory vs. adjunct PP is semantically determined (verbs of hearing, turning, trusting typically require directional PP); adjunct PPs of time, place, manner are optional and may stand independently. When uncertain whether a PP is obligatory, default to ADVISORY tier (JUDGMENT-REQUIRED) rather than HARD BIND.

---

### JM155-discourse-particle

**Bare discourse-particle indivisibility**

- **Encoded question**: Does a sense-line consist solely of a bare discourse particle (הִנֵּה, לָכֵן, עַל־כֵּן, אָז, וְעַתָּה, הֲלֹא) with its governed clause content beginning the next line?
- **Verdict family**: BIND
- **Tier**: HARD
- **Precedence**: 3
- **Source**: Joüon §155; AC §4.5; canon H14 + M3
- **Macula operationalization**: Token set for the line = 1 token; `Token.pos == "particle"` and `Token.lemma` in DISCOURSE_PARTICLE_LEMMAS (הִנֵּה, לָכֵן, עַל־כֵּן, אָז, וְעַתָּה, הֲלֹא, אֵפֹא). Particle alone on a line with no finite verb, no subject, no predicate = BIND (merge with governed clause on next line). Extended pattern: particle + subject NP on line N, finite predicate on N+1 — also BIND (clause nucleus split via the particle; see edge cases).
- **Status**: DRAFT
- **Backward-compat**: C9 (1100 catalog)
- **Diagnostic examples**:
  - Positive (fires): הִנֵּה alone on a line, content follows on N+1 — bare particle = BIND
  - Positive (fires): לָכֵן alone on a line, oracle content on N+1 — bare particle = BIND
  - Negative (does not fire): הִנֵּה followed immediately by subject + predicate on the same line — complete governed clause on same line, no stranding
  - Negative (does not fire): אָז functioning as temporal adverb within a clause (not as sentence-initial discourse frame) — particle integrated into clause, constraint inactive
- **Edge-case handling**: הִנֵּה with a following NP subject (הִנֵּה הָאִשָּׁה) but no predicate on the same line: both particle and subject NP are a partial governed-clause head — the constraint fires. When הִנֵּה introduces a full clause on the same line (הִנֵּה אָנֹכִי שֹׁלֵחַ), the clause is complete on that line; constraint is satisfied. Discourse particles at the end of a line followed by a new clause on N+1 (where the particle closes the prior clause rather than introducing the next) do not fire this constraint — evaluate the particle's governing direction (introductory vs. closing).

---

### JM161-interrogative-particle

**Bare interrogative-particle indivisibility**

- **Encoded question**: Does a line end with a bare interrogative particle (מִי, מָה, אַיֵּה, אֵיךְ, לָמָה, מַדּוּעַ, הֲ- prefixed) with its governed clause content beginning the next line?
- **Verdict family**: BIND
- **Tier**: HARD
- **Precedence**: 3
- **Source**: Joüon §161; canon M3
- **Macula operationalization**: Line-final token: `Token.pos == "particle"` + `Token.type_ == "interrogative"` (Macula `type_` attribute) OR `Token.lemma` in INTERROGATIVE_LEMMAS (מִי, מָה, אַיֵּה, אֵיךְ, לָמָה, מַדּוּעַ, אָן). Also: interrogative prefix הֲ- encoded as separate morpheme in TAHOT; detect via `_morph_tag` interrogative prefix marker. No governed clause on same line = BIND.
- **Status**: DRAFT
- **Backward-compat**: C10 (1100 catalog)
- **Diagnostic examples**:
  - Positive (fires): מִי on line N alone, clause follows on N+1 — bare interrogative = BIND
  - Positive (fires): line ends with מַדּוּעַ, next line opens with interrogative clause — BIND
  - Negative (does not fire): מִי יוֹדֵעַ (interrogative particle + finite verb on same line) — complete interrogative clause, constraint satisfied
  - Negative (does not fire): מָה in non-interrogative pronoun use (e.g., מָה in relative/comparative function) — check `type_` attribute; non-interrogative use does not fire
- **Edge-case handling**: Rhetorical questions where the interrogative opens a bicolon and the second colon completes the question are NOT violations — the first colon carries the interrogative particle + partial question; this is a SJ1 parallel-series structure. The BIND fires only when the particle is stranded with no clause-content at all on its line. The prefixed interrogative הֲ- (prefix morpheme on the first word of a clause) does not produce a standalone line-final particle situation; it fires only if the prefixed word appears alone on the line without its clause.

---

### JM156-casus-pendens

**Casus pendens own-line**

- **Encoded question**: Is a casus pendens (topic-fronted NP + resumptive pronoun in the main clause) present, and does it appear on the same line as the main clause rather than on its own line?
- **Verdict family**: SPLIT
- **Tier**: HARD
- **Precedence**: 3
- **Source**: Joüon §156; WO §4.7; canon H15
- **Macula operationalization**: Pattern detection requires walking from the resumptive pronoun OUTWARD to its antecedent NP (not from NP to pronoun — the API has no backreferences field). Iterate all pronoun / pronominal-suffix tokens (`pos="pronoun"` with `type_="pronominal"`, or suffix tokens) on lines after a candidate topic NP. For each such pronoun, check `pronoun.antecedents` (resolved from `participantref_ids`): if any antecedent is a Token on a prior line whose role is fronted-topic-like (NP at line head, no preceding finite verb on that line), the prior NP is a casus pendens topic. SPLIT fires when both the topic NP and the resumptive-pronoun clause appear on the same line. Note: `participantref` coverage in lowfat is sparse; surface fallback (independent pronoun on line N resuming a pre-verbal NP on line N-1, no chain-continuity from a different antecedent) needed for ~40% of cases.
- **Status**: DRAFT
- **Backward-compat**: G8 (1100 catalog, previously only partial coverage via H15 guard in validate_clause_nucleus_split)
- **Diagnostic examples**:
  - Positive (fires — must split): וְהָאָרֶץ הָיְתָה תֹהוּ וָבֹהוּ (if topic NP + clause on same line when topic is identifiable casus pendens) — SPLIT
  - Positive (fires — must split): אֶת הַכֶּסֶף נְשַׁלֵּם (topic DO + main clause on same line when resumptive reference is present) — SPLIT
  - Negative (does not fire): casus pendens topic on its own line and main clause on next — already split correctly; constraint satisfied
  - Negative (does not fire): fronted constituent without resumptive pronoun — fronted topic without resumption is a different construction (topicalization, not casus pendens); evaluate under JM156-general-fronting (open gap)
- **Edge-case handling**: The casus pendens / fronting-paradox distinction (canon §1): a casus pendens has a resumptive pronoun by definition; a fronted-without-resumptive is tight fronting (the general fronting case, listed as an open gap). When the casus pendens topic is itself a prepositional phrase or an embedded clause, the same own-line rule applies. M4 does NOT fire on casus pendens topics — they earn their own line per SJ5.

---

### JM-oath-formula

**Oath-formula integrity**

- **Encoded question**: Does a line end with an oath formula skeleton (חַי + maqqef + divine name/pronoun — e.g., חֵי יְהוָה, חֵי פַרְעֹה) with its asseveration content beginning the next line?
- **Verdict family**: BIND
- **Tier**: HARD
- **Precedence**: 3
- **Source**: Joüon §147 (oaths and adjurations); canon M4 + §1 formula integrity
- **Macula operationalization**: Closed list: OATH_FORMULA_PATTERNS (חֵי + divine-name lemma; בְּחֵי + divine-name). Token-level: line ends with חֵי token (or בְּחֵי) immediately followed by divine-name or second-person pronoun, with asseveration content (אִם / כִּי / verb) on the next line. `Token.lemma == "חַי"` in oath use + `Token.after == "־"` (maqqef to divine name) = formula unit.
- **Status**: DRAFT
- **Backward-compat**: C12 (1100 catalog)
- **Diagnostic examples**:
  - Positive (fires): חֵי יְהוָה on line N, כִּי [asseveration] on N+1 — oath formula stranded from asseveration = BIND
  - Positive (fires): חֵי פַרְעֹה on line N, [verb content] on N+1 — BIND
  - Negative (does not fire): חַי in non-oath use (e.g., adjective "living" in בַּמַּיִם הַחַיִּים) — lexical adjective, not formula; `Token.lemma` check excludes this
  - Negative (does not fire): oath formula + asseveration on same line — no stranding, constraint satisfied
- **Edge-case handling**: Some oaths begin with the particle אִם before the asseveration (the אִם-oath pattern, Joüon §165 sworn negation). In this case, the formula is חֵי + name / אִם + verb; the constraint covers the חֵי + name unit; the אִם + verb content is the asseveration and must not be separated from the formula head. Double-oath formulas (חֵי יְהוָה וְחֵי נַפְשְׁךָ) are treated as one formula unit — BIND applies to the entire compound.

---

### JM-cross-verse-continuity

**Cross-verse grammatical-unit continuity**

- **Encoded question**: Does a verse boundary artificially split a grammatical unit (subordinate clause stranded, construct chain crossing verse boundary, speech-frame without content closing one verse)?
- **Verdict family**: BIND
- **Tier**: HARD
- **Precedence**: 4
- **Source**: Canon H10; §1 versification-is-not-a-break-signal
- **Macula operationalization**: Four sub-cases. Note: this is the ONLY catalog constraint that requires loading more than one chapter. At chapter-boundary verses (the final verse of a chapter), the check must load the next chapter via `get_chapter(book_slug, chapter+1)` and call `get_verse_tokens(book_slug, chapter+1, 1)` to inspect the continuation. The pipeline must supply the chapter's total verse count so the check knows when a verse is chapter-final.
  1. Bare subordinator at verse-end: `Token.pos == "conjunction"` + subordinating lemma (NFC-normalized: כִּי, אֲשֶׁר, אִם, כַּאֲשֶׁר) at final position of verse N = BIND (subordinator requires clause on verse N+1)
  2. Construct-state noun at verse-end: `Token.is_construct` = True at final token of verse N, nominal continuation on verse N+1 = BIND (same as JM129, applied cross-verse)
  3. Speech-intro frame at verse-end without content: speech-frame token (לֵאמֹר or bare speech verb) at verse-end, speech content beginning verse N+1 = BIND
  4. Conjunction-prefix at verse-end: `Token.pos == "conjunction"` (proclitic וְ) at verse-end token = BIND (same as JM103, applied cross-verse)
- **Status**: DRAFT
- **Backward-compat**: C13 (1100 catalog)
- **Diagnostic examples**:
  - Positive (fires): verse N ends with כִּי (bare subordinator), verse N+1 opens with the subordinate clause — BIND
  - Positive (fires): verse N ends with construct-state noun, verse N+1 begins with its rectum — BIND
  - Negative (does not fire): verse N ends with complete sentence; verse N+1 begins new clause — clean verse boundary, constraint inactive
  - Negative (does not fire): verse N ends with wayyiqtol (complete clause), verse N+1 begins next narrative event — no dependency arc crosses boundary
- **Edge-case handling**: When a grammatical unit spans a verse boundary, the sense-line is kept intact in the earlier verse's block with a superscript verse-number marker (per canon H10 rendering convention). This constraint identifies the BINDING fact; the rendering convention is separate. In practice, most cross-verse continuity cases are identified by `validate_cross_verse_continuity.py`'s STRONG arm.

---

### JM-wayehi-fef-protasis

**Wayehi-FEF protasis integrity**

- **Encoded question**: Is a וַיְהִי FEF protasis either fragmented across multiple lines (BIND against fragmentation) or collapsed onto the same line as the main clause (SPLIT required)?
- **Verdict family**: BIND (fragmentation arm) / SPLIT (collapse arm)
- **Tier**: HARD
- **Precedence**: 4
- **Source**: Joüon §155 / WO §33.1.1c; canon H16
- **Macula operationalization**: Trigger: `Token.is_wayyiqtol` = True + `Token.lemma == "הָיָה"` = True (wayyiqtol of הָיָה = וַיְהִי). The FEF (Frame-Establishing Formula) pattern: וַיְהִי + temporal expression (PP, כַּאֲשֶׁר-clause, infinitive-construct phrase) + main clause. BIND arm: if the temporal expression is split across two lines within the protasis (protasis tokens spread across N and N+1 before main clause arrives), BIND. SPLIT arm: if the protasis + main clause appear on the same line (collapsed), SPLIT required.
- **Status**: DRAFT
- **Backward-compat**: C14 (1100 catalog) + SPLIT arm from validate_wayehi_protasis
- **Diagnostic examples**:
  - Positive BIND: וַיְהִי on line N, כַּאֲשֶׁר שָׁמַע continues on N+1 with protasis incomplete — protasis fragmentation = BIND
  - Positive SPLIT: וַיְהִי כַּאֲשֶׁר שָׁמַע [main clause] all on one line — SPLIT: protasis + main clause must separate
  - Negative (does not fire): וַיְהִי + complete protasis on line N, main clause on line N+1 — correctly split; constraint satisfied
  - Negative (does not fire): וַיְהִי as narrative-sequence "and it came to pass" without a FEF protasis (direct use) — no temporal-expression complement; H3 wayyiqtol policy applies instead
- **Edge-case handling**: The FEF wayehi is distinguished from narrative וַיְהִי by the presence of a temporal expression (כַּאֲשֶׁר, בִּהְיוֹת, PP of time). Without a temporal expression, וַיְהִי is a regular wayyiqtol head (H3). Long protases (≥6 prosodic words in the temporal clause) may be further split if the temporal clause itself is a clause with its own nucleus — evaluate under JM154-verbless-clause-nucleus or JM125-verb-object-bond for the internal structure.

---

### JM158-restrictive-relative

**Restrictive relative-clause binding**

- **Encoded question**: Is the אֲשֶׁר-clause on sense-line N+1 a restrictive (defining) modifier of the head noun on sense-line N, making line N referentially incomplete without it?
- **Verdict family**: BIND
- **Tier**: ADVISORY
- **Precedence**: 5
- **Source**: Joüon §158; WO §19.1
- **Macula operationalization**: `Constituent.is_relative_clause` — True when `wg_class == "relp"` or `wg_rule == "relCL"`. Walk relp constituents: if the relative-clause constituent's tokens begin on line N+1 and the head noun constituent's tokens end on line N, and the Macula constituent tree shows the relp as a child of the head NP, this constraint fires. Restrictive vs. non-restrictive disambiguation: if the head noun is already uniquely identified by a proper name, definite article + unique referent, or pronominal head, the clause is likely non-restrictive; otherwise, treat as restrictive (default for אֲשֶׁר-clauses per Joüon §158a).
- **Status**: DRAFT
- **Backward-compat**: G1 (1100 catalog, previously NOT COVERED)
- **Diagnostic examples**:
  - Positive (fires): הָאִישׁ on line N, אֲשֶׁר־שָׁלַחְתָּ on N+1 — restrictive relative binding head noun = BIND (ADVISORY)
  - Positive (fires): הָאָרֶץ on line N, אֲשֶׁר יְהוָה נֹתֵן לָכֶם on N+1 — restrictive relative = BIND (ADVISORY)
  - Negative (does not fire): יְהוָה אֱלֹהֶיךָ on line N, אֲשֶׁר הוֹצֵאתִיךָ מִמִּצְרַיִם on N+1 — YHWH is uniquely identified; אֲשֶׁר-clause is non-restrictive (appositive/descriptive); see JM158-nonrestrictive
  - Negative (does not fire): אֲשֶׁר opening its own line where head noun has no syntactic dependency arc in Macula (independent usage) — constraint inactive
- **Edge-case handling**: ADVISORY tier reflects the genuine editorial difficulty of restrictive-vs-non-restrictive disambiguation in context. When the Macula constituent tree clearly shows the relp as a modifier-child of the NP (not as a sibling clause), treat as restrictive. When the head noun is already maximally specific (proper name + title), treat as non-restrictive and route to JM158-nonrestrictive. When uncertain, JUDGMENT-REQUIRED is the operative verdict (the ADVISORY tier means this surfaces for editorial review, not auto-apply).

---

### JM158-nonrestrictive-relative

**Non-restrictive relative-clause licensing**

- **Encoded question**: Is the אֲשֶׁר-clause on line N+1 a non-restrictive (descriptive / appositive) modifier of an already-uniquely-identified head, potentially licensable as a standalone ATU?
- **Verdict family**: INFORM
- **Tier**: ADVISORY
- **Precedence**: 7
- **Source**: Joüon §158; WO §19.3
- **Macula operationalization**: Same Macula path as JM158-restrictive-relative: `Constituent.is_relative_clause`. Additional test: head noun is a proper name (`Token.type_ == "proper"`) or is the Tetragrammaton, or carries a pronominal suffix making it uniquely referential. When these conditions hold, the אֲשֶׁר-clause is potentially non-restrictive. INFORM verdict: the clause may stand alone as an ATU if it passes the bidirectional test in the rendering prompt.
- **Status**: DRAFT
- **Backward-compat**: G2 (1100 catalog, previously NOT COVERED)
- **Diagnostic examples**:
  - Positive (informs): יְהוָה אֱלֹהֶיךָ on line N, אֲשֶׁר הוֹצֵאתִיךָ on N+1 — YHWH uniquely identified; אֲשֶׁר-clause is descriptive; INFORM: may stand alone
  - Positive (informs): אַבְרָהָם on line N, אֲשֶׁר אָהַבְתִּיו on N+1 — proper name head; non-restrictive; INFORM
  - Negative (does not inform): indefinite NP head — likely restrictive; route to JM158-restrictive-relative
  - Negative (does not inform): אֲשֶׁר-clause is short (≤3 prosodic words) with no independent predicative weight — too short to stand alone even if non-restrictive; report as INFORM but note weight insufficiency
- **Edge-case handling**: INFORM verdict means the constraint catalog records the syntactic licensing without mandating a split. The rendering prompt's bidirectional test makes the final determination. A non-restrictive relative clause that fails the backward-containment prong of the bidirectional test (its reference is opaque without the prior line) should merge with the head even though it is syntactically non-restrictive. The constraint catalog notes the structural license; the rendering prompt adjudicates.

---

### JM168-purpose-clause

**Purpose-clause infinitive binding**

- **Encoded question**: Is the לְ + infinitive-construct on sense-line N+1 a purpose-clause modifier of the finite verb on sense-line N, making line N+1 a subordinate ATU that cannot stand independently?
- **Verdict family**: JUDGMENT-REQUIRED
- **Tier**: ADVISORY
- **Precedence**: 5
- **Source**: Joüon §168; WO §36.2.2; canon H7 extension
- **Macula operationalization**: `Token.is_infinitive_construct` — True when `type_ == "infinitive construct"`. First token on line N+1 is `pos == "preposition"` + `lemma == "לְ"` followed by an infinitive-construct token. Parent-clause check: the infinitive construct should have a `role == "adv"` or be within a `wg_class == "cl"` child of the matrix clause on line N in the Macula constituent tree. Guard: לֵאמֹר (speech-marker infinitive) is excluded — it is governed by H5 speech-frame rules, not purpose-clause binding.
- **Status**: DRAFT
- **Backward-compat**: G5 (1100 catalog, previously NOT COVERED)
- **Diagnostic examples**:
  - Positive (fires — JUDGMENT-REQUIRED): וַיִּשְׁלַח on line N, לִרְאוֹת אֶת הָאָרֶץ on N+1 — purpose infinitive dependent on matrix verb = JUDGMENT-REQUIRED (short purpose clause suggests BIND; longer ones may stand independently)
  - Positive (fires): וַיָּבֹא on line N, לְקַחַת אֶת הַמִּנְחָה on N+1 — purpose infinitive = JUDGMENT-REQUIRED
  - Negative (does not fire): לֵאמֹר — speech-frame infinitive, governed by H5; not a purpose clause
  - Negative (does not fire): לְ + infinitive that is itself a substantive infinitive (nominal use as subject or object) — nominal infinitive is a clause head, not a purpose modifier; check Macula role: if `role == "s"` (subject) or `role == "o"` (object), not purpose-clause
- **Edge-case handling**: JUDGMENT-REQUIRED because purpose-clause weight varies. Short purpose clauses (≤3 prosodic words) typically bind to their matrix — they cannot stand as independent ATUs. Long purpose clauses (≥5 prosodic words with their own internal argument structure) may qualify as SJ5 substantive adjuncts and earn their own line. The rendering prompt applies the Propositional Completeness Test: does the purpose clause predicate a complete proposition (answer: yes if it carries its own agent + action structure, no if it is merely a bare infinitive + DO)?

---

### JM159e-conditional-protasis

**Conditional protasis–apodosis integrity**

- **Encoded question**: Is the conditional protasis (אִם + clause) on sense-line N referentially incomplete without its apodosis on line N+1 — specifically, is it a short (≤4 prosodic words) protasis that fails backward self-containment?
- **Verdict family**: JUDGMENT-REQUIRED
- **Tier**: ADVISORY
- **Precedence**: 5
- **Source**: Joüon §159e; WO §38.1
- **Macula operationalization**: First token on line N: `Token.lemma == "אִם"` (conditional particle) + `Token.pos == "conjunction"`. Word count of line N ≤4 prosodic words (short-protasis threshold). Next line N+1 contains apodosis (finite verb or weqatal). Guard: if protasis is long (≥5 prosodic words), this constraint does NOT fire — long protases qualify as SJ5 and may stand alone. Cross-verse case: `validate_cross_verse_continuity.py` handles the cross-verse arm; this entry covers within-verse conditional splits.
- **Status**: DRAFT
- **Backward-compat**: G6 partial (1100 catalog, previously PARTIAL coverage for cross-verse case only)
- **Diagnostic examples**:
  - Positive (fires — JUDGMENT-REQUIRED): אִם תֵּלְכִי אִתִּי on line N (4 words), apodosis on N+1 — short protasis, JUDGMENT-REQUIRED (lean toward BIND)
  - Positive (fires): אִם יֵשׁ on line N (2 words), apodosis follows — very short protasis = strong lean toward BIND
  - Negative (does not fire): אִם + long clause (≥5 words) on line N — protasis is substantive, may stand alone; SJ5 applies; constraint inactive
  - Negative (does not fire): אִם in non-conditional use (e.g., אִם in oath-negation formula — "if [then not]...") — oath pattern; governed by JM-oath-formula
- **Edge-case handling**: The JUDGMENT-REQUIRED verdict reflects the weight-dependent nature of protasis independence. Short protases (≤4 words) fail the bidirectional backward-containment test because the protasis condition references an expected apodosis. Long protases with their own temporal setting or complex clause structure qualify as SJ5 substantive adjuncts and earn their own line. When אִם introduces a purpose or object clause (not a conditional), this constraint is inactive — check that אִם is functioning as a conditional subordinator, not as an assertive particle (Joüon §164).

---

### JM174-gapped-verb

**Gapped finite verb in parallel bicolon**

- **Encoded question**: Is sense-line N+1 verbless in the surface text, but propositionally complete because its finite verb is gapped (elided) from the parallel preceding line N — making a false atomic-thought failure?
- **Verdict family**: INFORM
- **Tier**: ADVISORY
- **Precedence**: 6
- **Source**: Joüon §174 (gapping); WO §8.3.2
- **Macula operationalization**: First, retrieve each line's tokens via `match_sense_line_tokens(verse_tokens, sense_line_text, start_idx)` (per the implementation_conventions preamble). Line N: at least one token with `is_finite_verb == True`. Line N+1: no token with `is_finite_verb == True`. Compare role distributions across lines by filtering each line's token list to `token.role in ('s', 'o', 'o2', 'pp', 'adv')`. INFORM verdict fires when line N has a finite verb with role-bearing arguments AND line N+1 has structurally analogous role distribution (subject role present, object role present, no finite verb). Note: `Constituent.tokens_with_role()` is a Constituent method, NOT applicable to a sense-line slice; the per-token `token.role` filter is the correct API at the sense-line level.
- **Status**: DRAFT
- **Backward-compat**: G3 (1100 catalog, previously NOT COVERED)
- **Diagnostic examples**:
  - Positive (informs): Ps 1:1 bicola pattern — line N has verb, line N+1 has parallel structure without verb = INFORM (gapping, colon is complete)
  - Positive (informs): Ps 19:2-3 bicola — יְסַפֵּר / יַגִּיד with gapped second verb — INFORM
  - Negative (does not inform): line N+1 has no verb AND no parallel role-label structure with line N — not gapping; genuine verbless clause (evaluate under JM154-verbless-clause-nucleus)
  - Negative (does not inform): line N+1 has its own independent finite verb — no gapping; both cola are independently predicated
- **Edge-case handling**: INFORM verdict prevents false-positive M4 / No-Anchor Test failures on gapped bicola in Sifrei Emet. This constraint does not generate any required edit; it marks a pattern that the rendering prompt should recognize as propositionally complete without an overt verb. The parallel-structure confirmation (matching role labels across lines) is the key Macula evidence. When role labels do not match (asymmetric parallelism), the gapping identification is less confident — mark as INFORM with low confidence.

---

### JM157-ki-recitativum

**כִּי recitativum vs. causal disambiguation**

- **Encoded question**: Is the כִּי on line N+1 functioning as recitativum (direct-speech marker in divine/prophetic speech: כִּי + first-person divine content) rather than as a causal clause, requiring it to be treated as SJ3 speech-act content rather than a separate causal ATU?
- **Verdict family**: JUDGMENT-REQUIRED
- **Tier**: ADVISORY
- **Precedence**: 5
- **Source**: Joüon §157.3; WO §39.3.4; canon H7 complement integrity
- **Macula operationalization**: Line N+1 opens with `Token.lemma == "כִּי"`. Detection uses a **surface heuristic** (not subjref/participantref, which is too sparse for speaker identification): the first finite verb on the next line has `token.person == "1"` (first-person divine self-reference). Combined trigger: line N opens / continues a speech-act frame (lemma in `{אָמַר, דִּבֵּר, צִוָּה}`) OR line N is in an already-established prophetic-oracle context, AND line N+1's first finite verb has `person == "1"`. Flag as JUDGMENT-REQUIRED. Note: `subjref` is grammatical-subject pointer, not speaker-discourse-role pointer — using subjref to detect YHWH-as-speaker is unreliable.
- **Status**: DRAFT
- **Backward-compat**: G11 partial (1100 catalog, previously PARTIAL)
- **Diagnostic examples**:
  - Positive (fires — JUDGMENT-REQUIRED): divine speech context, כִּי אָנֹכִי on N+1 — possible recitativum; JUDGMENT-REQUIRED
  - Positive (fires): prophetic oracle + כִּי + first-person singular divine verb — recitativum candidate; treat as continuation of speech content, not separate causal ATU
  - Negative (does not fire): כִּי after cognition verb (וַיֵּדַע) — obligatory complement; governed by JM157-complement-integrity
  - Negative (does not fire): כִּי in unambiguous causal use (after narrative event, not speech context) — causal clause, governed by SJ5 substantive adjunct logic
- **Edge-case handling**: The recitativum-כִּי (Joüon §157.3: כִּי as direct-speech introducer without an explicit speech verb, especially in divine speech contexts) is one of the least frequent but most disruptive כִּי ambiguity cases. The JUDGMENT-REQUIRED verdict surfaces these for editorial review. When context clearly establishes divine first-person speech, the כִּי-clause content belongs with the oracle (SJ3 speech content, same ATU line or new speech-content line). The contrast with causal-כִּי is: causal כִּי justifies a preceding clause; recitativum כִּי introduces speech content.

---

### JM123-inf-abs-predicate

**Infinitive absolute as predicate binding**

- **Encoded question**: Is an infinitive absolute used predicatively (בָּרֹךְ אֶבֹרֶכְךָ) or as rhetorical intensification bound to its finite-verb cognate, and is it separated from that verb across a line boundary?
- **Verdict family**: BIND
- **Tier**: HARD
- **Precedence**: 3
- **Source**: Joüon §123; WO §35.3
- **Macula operationalization**: `Token.is_infinitive_absolute` — True when `type_ == "infinitive absolute"`. Two sub-patterns:
  1. Cognate intensification (paronomasia): infinitive-absolute + finite-verb from same root on adjacent tokens (same line or stranded across lines). If stranded = BIND.
  2. Predicative absolute: infinitive absolute functioning as the main predicate in a clause (rare; typically in royal/divine commands). Detect via absence of finite verb on the same line and `role == "v"` in Macula constituent.
  Current gap: Macula role assignment for predicative infinitive absolute is not yet confirmed — mark as DRAFT with "Macula: partial — `type_='infinitive absolute'` confirmed; predicative-role disambiguation needs empirical verification against lowfat corpus."
- **Status**: DRAFT
- **Backward-compat**: G9 (1100 catalog, previously NOT COVERED)
- **Diagnostic examples**:
  - Positive (fires): בָּרֵךְ on line N (infinitive absolute), אֲבָרֶכְךָ on N+1 (finite verb, same root) — paronomasia pair stranded = BIND
  - Positive (fires): הָלֹךְ on line N (inf. abs.), וְיָלַכְתָּ on N+1 (consecutive finite, same root) — BIND
  - Negative (does not fire): infinitive absolute + finite verb on same line — bond satisfied
  - Negative (does not fire): infinitive absolute as standalone verbal complement (לְ + inf. construct mislabeled; check type_ carefully) — not this entry
- **Edge-case handling**: The HARD tier applies to the paronomasia (cognate intensification) case where both members are from the same root — this is a frozen rhetorical-syntactic unit. The predicative-absolute use (where the infinitive absolute stands alone as the clause predicate) is rarer and less clearly constrained — downgrade to ADVISORY for that sub-case pending corpus evidence. The `is_infinitive_absolute` predicate on `Token` is available in Macula but predicate-role detection requires clause-function disambiguation not yet fully validated.

---

### JM147-vocative-extraclausal

**Vocative and extra-clausal element placement**

- **Encoded question**: Does a vocative or extra-clausal element (interjection, response particle) appear in a position that violates its governing rule (own-line default per H4, or integrated into a clause when it should be on its own line)?
- **Verdict family**: INFORM
- **Tier**: ADVISORY
- **Precedence**: 6
- **Source**: Joüon §147 (vocative and extra-clausal elements); WO §4.7; canon H4
- **Macula operationalization**: `Token.pos == "particle"` with `type_ == "interjection"` (הוֹי, אוֹי, אָח, הָהּ) OR proper-name token in address position (`Token.type_ == "proper"` + second-person verbal morphology in adjacent clause). The primary operative rule is canon H4 (Vocative Handling); this catalog entry provides the constraint-catalog anchor for that rule. INFORM: flag vocative-position elements for editorial review of their line assignment.
- **Status**: DRAFT
- **Backward-compat**: new entry (partially under H4 in canon; no 1100 catalog G-label)
- **Diagnostic examples**:
  - Positive (informs): Proper name in address position on same line as command clause — possible vocative that should earn its own line; INFORM
  - Positive (informs): הוֹי or אוֹי at clause head — woe-particle with following content; INFORM for own-line evaluation
  - Negative (does not inform): repeated vocative (Gen 22:11 אַבְרָהָם אַבְרָהָם) — governed by H4 repeated-vocative rule; stays together as one speech act
  - Negative (does not inform): vocative already on its own line — correctly handled; constraint satisfied
- **Edge-case handling**: This entry serves primarily as a catalog-level anchor for the H4 vocative rule, providing the constraint catalog's coverage of extra-clausal elements. The operative decision logic lives in canon H4 (own-line default, apposition exception, repeated-vocative stays-together rule). When the constraint catalog is used to audit rendered output, INFORM fires to surface vocative-placement decisions for editorial review — not as a hard block.

---

### JM160-negation-scope

**Negation-particle scope binding**

- **Encoded question**: Is a negation particle (לֹא, אַל, אֵין, בַּל) stranded at line-end away from the verb or predicate it negates, leaving the negated expression incomplete on that line?
- **Verdict family**: BIND
- **Tier**: HARD
- **Precedence**: 2
- **Source**: Joüon §160 (לֹא / אַל / אֵין); WO §39.3.3
- **Macula operationalization**: `Token.pos == "particle"` + `Token.lemma` in NEGATION_LEMMAS (לֹא, אַל, אֵין, בַּל, לְבִלְתִּי). Line-final negation particle with no following verb or predicate on the same line = BIND. Detect: last token on line N is negation particle; line N+1 opens with the negated verb/adjective. אֵין as existential negation (Joüon §160c) requires its predicate; stranding אֵין from its predicate = BIND.
- **Status**: DRAFT
- **Backward-compat**: partially C2 (JM103-proclitic-stranding covers the prefix forms); this entry covers standalone negation particles
- **Diagnostic examples**:
  - Positive (fires): לֹא alone at line-end, negated verb on N+1 — negation particle stranded from its verb = BIND
  - Positive (fires): אֵין alone at line-end, predicate on N+1 — existential negation stranded from predicate = BIND
  - Negative (does not fire): לֹא + verb on same line (לֹא יֵדַע) — no stranding
  - Negative (does not fire): אַל in an oath-negation formula — governed by JM-oath-formula; this entry is inactive
- **Edge-case handling**: לֹא in a fixed formula (e.g., לֹא תַעֲשֶׂה — command negation in Decalogue) must stay with its verb; the BIND fires if the negation is separated. אֵין followed by a pronominal suffix (אֵינֶנּוּ "he is not") is a complete predication — no stranding is possible; constraint inactive. לְבִלְתִּי (negative purpose complement) requires its following infinitive; stranding לְבִלְתִּי from its infinitive = BIND.

---

*End of constraint entries. Total: 26 constraints.*
