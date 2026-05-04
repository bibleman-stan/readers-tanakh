# Validator IR-Port Status

Tracks per-validator migration from morph-tag-walking detection to declarative
queries against the Macula Hebrew lowfat constituent-query IR
(`validators/_shared/macula_constituents.py`).

**Update protocol:** edit this file in the same commit that lands a port.
The status column reflects **detection-side primary path**; fallback paths
to morph_tags or skel-heuristics may remain as graceful degradation.

## Status legend

- **IR-PORTED** — fully Macula-driven; no tag-walking primary path
- **IR+HYBRID** — IR for the new arm / new pattern; legacy paths preserved
  for non-IR cases
- **IR+FALLBACK** — IR primary; tag-walker preserved as graceful fallback
  for chapters where lowfat alignment fails
- **TAG-WALKING** — original tag-driven implementation; no IR path
- **NO-PORT-PLANNED** — audited and deliberately not ported (IR adds no
  value over existing implementation; see Notes column for rationale)
- **DEFER** — audited; tag path adequate; revisit if FP rate increases
- **NOT-AUDITED** — not yet evaluated for IR-port feasibility

## Registry

| Validator | Layer | Status | Last commit | Notes |
|---|---|---|---|---|
| `validate_verb_object_bond` | L1 syntax | IR-PORTED | c6bd30576 | Frame-args resolution + 3 license-guards (speech-verb, clausal-A1, coordinated-object). Replaced ~320 lines net. |
| `validate_cross_verse_continuity` | L3 colometry | IR+HYBRID | 428836ee0 | Pattern (e) pronoun-resumption is IR-only (uses `participantref`); patterns (a)-(d) tag/skel-driven, unchanged. |
| `validate_construct_chain` | L3 colometry | IR-PORTED | 5bc7d88a8 | NPofNP constituent query replaces 3 heuristics. 2371 → 1116 findings. |
| `validate_participial_speech_frame` | L3 colometry | IR-PORTED | 07974d52b | `Token.is_active_participle` + lemma + `ancestor_with(wg_class="relp")` for relative-clause guard. 8 → 11 findings. |
| `validate_speech_intro_framing` | L3 colometry | IR+FALLBACK | 3727ddacc | H5b arm IR-driven (frame-args A1 = quoted-content head); H5c arm tag-driven (deferred). 1056 → 649 findings. |
| `validate_clause_nucleus_split` (H18) | L3 colometry | IR+HYBRID | 14e6d86b1 | IR-aware sibling helpers for Guards 9, 10, 5 (finite-verb / participle / preposition / wayehi). Heuristic helpers retained as fallback for chapters without lowfat alignment + for guards where IR adds no capability (vocative, discourse particle, casus pendens, heavy subject). 351 → 382 findings. |
| `validate_wayehi_protasis` (H16) | L3 colometry | IR-PORTED | 14e6d86b1 | Lemma+aspect FEF detection (`Token.lemma == "הָיָה"` + `is_wayyiqtol`); `is_finite_verb` replaces `וי`-prefix heuristic. 357 → 383 findings. |
| `validate_coordinated_object` | L3 colometry | IR-PORTED | (this commit) | Frame-args A1 multi-token detection: a verb's coordinated A1 spans multiple sense-lines = candidate. 20 → 612 findings (IR catches asyndetic + ו-prefixed objects without את that the skel trigger missed). REVIEW-only floor. |
| `validate_short_orphan_line` (M4 weqatal arm) | L3 | NO-PORT-PLANNED | — | Audit Wave B: M4 weqatal-apodosis guard already optimal via `morph_tags.is_weqatal()`. Other M4 arms (subject-pronoun, atomic-thought) not yet ported — IR+HYBRID candidate per Wave-C audit (subject-pronoun arm only, ~5-10% of finding set). |
| `validate_maqqef_integrity` | L1 | NO-PORT-PLANNED | — | Audit Wave B: pure orthographic check (U+05BE on token end). Text-pattern scanner equivalent and simpler than IR query. |
| `validate_circumstantial_clause` | L3 | NO-PORT-PLANNED | — | Audit Wave C: scene-setting weight is editorial judgment, not structural. IR's Token.is_finite_verb is a marginal robustness win; high TP rate on existing 2391 findings shows current heuristics are well-calibrated. |
| `validate_causal_ki` | L3 | NO-PORT-PLANNED | — | Audit Wave C: Macula lowfat does NOT distinguish causal vs complement כִּי senses (both glossed `(dm).that`). IR adds no semantic disambiguation; existing heuristic guards adequate. |
| `validate_complement_integrity` | L3 | NO-PORT-PLANNED | — | Audit Wave C: cognition-verb + כִּי-clause complement detection. Macula doesn't expose כִּי-clause as a distinct frame-arg slot (no A2-clausal label). Root+skeleton pattern is simpler and equally correct. |
| `validate_bare_construct_head` (M3) | L3 | DEFER | — | Audit Wave C: ~60-70% redundant with construct_chain IR-port. Could merge as fallback for ~15-35 parser-missed cases, but current heuristic works and merge has STRONG-MERGE auto-apply blast risk. Revisit after editorial triage of construct_chain IR findings. |
| `validate_oath_formula` | L3 | NO-PORT-PLANNED | — | Audit Wave C rapid survey: closed-list formula matching (חַי + divine name); morpho-syntactic pattern is mature. |
| `validate_doc_pointers` | L3 | NO-PORT-PLANNED | — | Audit Wave C rapid survey: documentation file-path validator; no corpus text involvement. |
| `validate_bare_discourse_particle` | L3 | NO-PORT-PLANNED | — | Audit Wave C rapid survey: closed-lexicon discourse-particle (הִנֵה, וְעַתָּה, ...); IR adds no precision. |
| `validate_canon_retirement_residue` | L3 | NO-PORT-PLANNED | — | Audit Wave C rapid survey: documentation hygiene; no corpus text. |
| `validate_bonded_pair` | L3 | NO-PORT-PLANNED | — | Audit Wave C rapid survey: closed-list hendiadys (חֶסֶד+אֱמֶת etc.); 6 findings; semantic phenomenon orthogonal to syntactic constituency. |
| `validate_blessed_cursed_chain` | L3 | NO-PORT-PLANNED | — | Audit Wave C rapid survey: scope-limited (Deut 27-28); 7 findings; tag path precise. |
| `validate_parallel_series_uniformity` | L3 | NO-PORT-PLANNED | — | Audit Wave C rapid survey: meta-structural uniformity check; 5 findings; editorial intent, not grammar. |
| `validate_interrogative_clause` | L3 | DEFER | — | Audit Wave C rapid survey: 29 findings; tag path works. Revisit if verb-detection FPs emerge in editorial review. |
| `validate_compound_preposition_object` | L1 | NOT-AUDITED | — | 0 findings — clean validator. |
| `validate_genealogy_uniformity` | L3 | NOT-AUDITED | — | 1 finding — minimal scope. |
| `validate_line_final_tokens` | L1 | NOT-AUDITED | — | 2 findings — minimal scope. |
| `validate_short_verse_fronting` | L3 | NOT-AUDITED | — | 0 findings — clean validator. |

## Spec layer (validators/specs/*.yaml)

**NO-PORT-PLANNED.** YAML specs consumed by `spec_runner.py` are a
declarative prosodic layer (line-slice operations + closed-list pattern
matching), not a syntactic-tree layer. The `spec_runner` primitives
(e.g., `next_line_is_purpose_infinitive`, `combined_lines_s6_eligible`)
already use TAHOT tags as authoritative oracles where needed; the lowfat
IR doesn't expose constituent-role information that would clean up this
layer. See audit verdict (2026-05-05 Wave B): "Specs are working well;
they're fine as-is."

## Pivot timeline

| Wave | Date | Commits | Theme |
|---|---|---|---|
| Wave A | 2026-05-05 | 08a0f5f63, c6bd30576, 428836ee0 | IR module + first port (verb_object_bond) + first new-capability (H10 pattern e) |
| Wave B | 2026-05-05 | 5bc7d88a8, 78c94b6cd, 07974d52b, 3727ddacc, c81011ccb | Construct-chain port + H5d port + H5b arm port + IR_PORT_STATUS doc |
| Wave C | 2026-05-05 | 9ac935415, 14e6d86b1, (this commit) | weqatal IR fix + H18 partial port + wayehi port + coord_obj port + 8 NO-PORT verdicts |

## Wave-C wash-up notes

- 5 ports landed (verb_object_bond, construct_chain, participial_speech_frame, speech_intro_framing-H5b, cross_verse-pattern-e in waves A-B; H18-partial, wayehi, coord_obj in wave C)
- 1 IR module bug fixed (weqatal — initial Wave-A audit said lowfat lacked native weqatal; empirical re-check showed type='weqatal' IS present)
- 13 validators audited & ruled NO-PORT or DEFER (M4 weqatal arm, maqqef_integrity, circumstantial_clause, causal_ki, complement_integrity, oath_formula, doc_pointers, bare_discourse_particle, canon_retirement_residue, bonded_pair, blessed_cursed_chain, parallel_series_uniformity, interrogative_clause)
- 4 validators left NOT-AUDITED (all 0-2 findings, low priority)
- bare_construct_head + M4 short_orphan_line subject-pronoun arm: DEFER for next session — wave-C race conditions with parallel agents made further ports risky

## Carry-forward

- **Editorial triage of expansion findings** (large new candidate sets from IR-driven detection):
  - `verb_object_bond` ~680 new candidates (clausal-A1 / restrictive-relative / head-quantifier guards still uncovered)
  - `cross_verse_continuity` pattern (e): 857 candidates; pre-flight scan showed ~85% TP on distance-1 + discrete-pronoun + narrative slice
  - `construct_chain` finding-set shift (2371 → 1116): editorial sample needed to confirm parser recall is acceptable
  - `validate_coordinated_object`: 20 → 612 findings; IR catches asyndetic + ו-prefixed coordinations the skel trigger missed
  - `validate_speech_intro_framing` H5b: 1056 → 649; FP suppression mostly clean
  - `validate_wayehi_protasis`: 357 → 383; +26 from IR's tighter is_finite_verb
- **Pending ports (DEFER list above):** bare_construct_head merge (small upside, STRONG-MERGE blast risk), M4 short_orphan_line subject-pronoun arm (audit's IR+HYBRID recommendation)
- **H5c port** (within `validate_speech_intro_framing`): deferred per Wave-B audit; revisit after H5b stabilizes editorially
- **Stage 2+ IR features** not yet in scope: chapter-scope predication graphs, discourse-cohesion layer, co-reference resolution beyond `participantref`/`subjref`

## Operational notes (Wave C lessons)

- **Race conditions with parallel agents**: Wave C dispatched 2 background agents (wayehi, coord_obj) operating on the same working tree as my main-thread H18 port. The wayehi commit accidentally bundled my H18 changes (from a `git add` race). Future waves should use `isolation: "worktree"` agent dispatch to prevent shared-tree races, OR limit parallelism to one writer per file region.
- **Pre-commit overhead**: each commit triggers `run_all.py --baseline-check` (~1 min for all 26 validators). Chained `update-baseline + commit` doubles to ~2 min. Multi-commit waves accumulate quickly; minimize commit count when possible.
- **Empty commits**: a chained command landed an empty commit (8291951b7) due to staging-race with concurrent agents. Recovered with a follow-up commit; CLAUDE.md's no-amend policy means the pollution stays in history.
