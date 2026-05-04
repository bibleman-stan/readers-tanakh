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

## Registry

| Validator | Layer | Status | Last commit | Notes |
|---|---|---|---|---|
| `validate_verb_object_bond` | L1 syntax | IR-PORTED | c6bd30576 | Frame-args resolution + 3 license-guards (speech-verb, clausal-A1, coordinated-object). Replaced ~320 lines net. |
| `validate_cross_verse_continuity` | L3 colometry | IR+HYBRID | 428836ee0 | Pattern (e) pronoun-resumption is IR-only (uses `participantref`); patterns (a)-(d) tag/skel-driven, unchanged. |
| `validate_construct_chain` | L3 colometry | IR-PORTED | 5bc7d88a8 | NPofNP constituent query replaces 3 heuristics (definite-article rectum, divine-name compound, common construct endings). 2371 → 1116 findings. |
| `validate_participial_speech_frame` | L3 colometry | IR-PORTED | 07974d52b | `Token.is_active_participle` + lemma + `ancestor_with(wg_class="relp")` for relative-clause guard. 8 → 11 findings (lemma-based catches more variants). |
| `validate_speech_intro_framing` | L3 colometry | IR+FALLBACK | 3727ddacc | H5b arm IR-driven (frame-args A1 = quoted-content head); H5c arm tag-driven (deferred). 1056 → 649 findings. Legacy slot-walker preserved as fallback. |
| `validate_short_orphan_line` (M4 weqatal arm) | L3 | NO-PORT-PLANNED | — | M4 weqatal-apodosis guard already optimal via `morph_tags.is_weqatal()`. Lowfat lacks native weqatal type; IR would add no capability. Audit verdict 2026-05-05. |
| `validate_bare_construct_head` | L3 | TAG-WALKING | — | Not yet audited. |
| `validate_bare_discourse_particle` | L3 | TAG-WALKING | — | Not yet audited. |
| `validate_blessed_cursed_chain` | L3 | TAG-WALKING | — | Not yet audited. |
| `validate_bonded_pair` | L3 | TAG-WALKING | — | Not yet audited. |
| `validate_canon_retirement_residue` | L3 | TAG-WALKING | — | Not yet audited. |
| `validate_causal_ki` | L3 | TAG-WALKING | — | Not yet audited. |
| `validate_circumstantial_clause` | L3 | TAG-WALKING | — | Not yet audited. |
| `validate_clause_nucleus_split` | L3 | TAG-WALKING | — | Not yet audited. |
| `validate_complement_integrity` | L3 | TAG-WALKING | — | Not yet audited. |
| `validate_compound_preposition_object` | L1 | TAG-WALKING | — | Not yet audited. |
| `validate_coordinated_object` | L3 | TAG-WALKING | — | Not yet audited. |
| `validate_doc_pointers` | L3 | TAG-WALKING | — | Not yet audited. |
| `validate_genealogy_uniformity` | L3 | TAG-WALKING | — | Not yet audited. |
| `validate_interrogative_clause` | L3 | TAG-WALKING | — | Not yet audited. |
| `validate_line_final_tokens` | L1 | TAG-WALKING | — | Not yet audited. |
| `validate_maqqef_integrity` | L1 | NO-PORT-PLANNED | — | Pure orthographic check (U+05BE on token end). IR exposes maqqef via `Token.after`, but a text-pattern scanner is equivalent and simpler. Audit verdict 2026-05-05. |
| `validate_oath_formula` | L3 | TAG-WALKING | — | Not yet audited. |
| `validate_parallel_series_uniformity` | L3 | TAG-WALKING | — | Not yet audited. |
| `validate_short_verse_fronting` | L3 | TAG-WALKING | — | Not yet audited. |
| `validate_wayehi_protasis` | L3 | TAG-WALKING | — | Not yet audited. |

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
| Wave B | 2026-05-05 | 5bc7d88a8, 78c94b6cd, 07974d52b, 3727ddacc | Construct-chain port + H5d port + H5b arm port |

## Carry-forward

- **Editorial triage of expansion findings**:
  - `verb_object_bond` ~600 new candidates (clausal-A1 / restrictive-relative / head-quantifier guards still uncovered)
  - `cross_verse_continuity` pattern (e): 857 candidates; pre-flight scan showed ~85% TP on distance-1 + discrete-pronoun + narrative slice
  - `construct_chain` finding-set shift (2371 → 1116): editorial sample needed to confirm parser recall is acceptable
- **H5c port** (within `validate_speech_intro_framing`): deferred per audit; revisit after H5b stabilizes editorially
- **Audits not yet run**: ~15 validators marked TAG-WALKING above; opportunity for further pivot waves once high-value candidates are exhausted
- **Stage 2+ IR features** not yet in scope: chapter-scope predication graphs, discourse-cohesion layer, co-reference resolution beyond `participantref`/`subjref`
