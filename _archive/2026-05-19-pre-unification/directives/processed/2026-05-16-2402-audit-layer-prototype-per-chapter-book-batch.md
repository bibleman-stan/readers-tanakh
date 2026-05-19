# Audit-layer prototype — per-chapter script + book-batch execution

## Context

Three validations of the extended bidirectional ATU test landed today (2026-05-16):

- **Deut 6:1-12** (deuteronomic prose) — 9/12 verses over-broken; coordinate-series fragmentation. 9-verse re-rendering committed (`6933d793f`).
- **Gen 22:1-12** (narrative + dialogue) — 7/12 over-broken; speech-verb extraction pattern. Vault-side report only.
- **Ps 1** (lyric poetry) — 4/6 over-broken; the cognitive-unity gate did load-bearing work on v.1 (synonymous tricolon) and v.6 (antithetic bicolon, where the necessary condition alone passed for both cola). 4-verse re-rendering committed (`39f39d886`).

The unifying rubric — necessary condition (forward grammatical closure + backward referential self-containment) + sufficiency extension for parallel poetry (synonymous / antithetic / synthetic class handling) — catches genre-specific over-breaking patterns systematically without genre-specific rules. Over-breaking rates are consistent ~60-75% across all three genres tested.

This directive productionizes that rubric. Full toolset-architecture context: `atu-method/docs/toolset-architecture.md` (`4bf65de`).

**Audit triggers: §7.3 trigger #10 (discipline-shifting addition that shapes how the apparatus is operated).** Pre-build adversarial audit mandatory per BoFM-2203 + GNT-2400 precedent.

## Items

### Phase 1 — Pre-build adversarial audit

1. **Dispatch ≥2 parallel Opus agents** against the proposed script design + prompt template (below). Each agent receives:
   - The three validated experiments (Deut 6, Gen 22, Ps 1) as evidence base
   - The extended bidirectional test rubric (necessary condition + cognitive-unity extension)
   - The proposed script architecture (per-chapter input → Sonnet dispatch → markdown report output)
   - The proposed Sonnet prompt template (mirroring what the three vault-side experiments used)

   And probes for:
   - **Prompt design fragility** — what cases would the rubric mis-handle? Edge cases beyond the three tested? Are the parallelism class definitions tight enough?
   - **Cross-validator interaction risk** — the existing R/H validators consume parses; this audit consumes RENDERED OUTPUT. Are there interactions where the audit's proposed merges would invalidate point-rule verdicts?
   - **Cascade risk** — when audit-flagged merges land in v2, the existing pre-commit cascade will rerun validators. Are baseline regressions expected? Acceptable?
   - **Genre-detection assumption** — the script applies the same prompt across all books. Does that work for distinct genres (legal prose, narrative, lyric poetry, prophetic poetry, wisdom poetry)?
   - **Cognitive-unity gate over-firing risk** — could the gate cause false-positive merges in synthetic-parallelism cases where B genuinely advances A?

2. **If audit clears (no must-fix findings):** proceed to Phase 2. **If audit surfaces must-fix findings:** STOP and surface for Stan-review per the 2203/2400 STOP-gate protocol.

### Phase 2 — Build the script

3. **Build `scripts/audit_rendered_output.py`**:
   - Input: `--book <book-id>` + `--chapter <N>` (or `--chapter all` for a full book sweep)
   - Reads: `data/text-files/v2/heb/<book-dir>/<book>-<chapter>.txt`
   - Dispatches: Sonnet (per `feedback_model_selection_frugality` — structured judgment within defined rubric)
   - Captures: per-line verdicts (KEEP-AS-IS / MERGE-WITH-PRIOR / MERGE-WITH-NEXT / AMBIGUOUS), reasoning, proposed corrected rendering, observed patterns
   - Output: `data/reports/audit/<book>-<chapter>.md`

4. **Prompt template** (Sonnet system + user prompt; see Appendix below for the validated template from vault-side experiments).

5. **Output schema** (markdown report per chapter):
   - Per-verse: line-by-line verdict + reasoning
   - Summary: over-broken verses (with parallelism-class diagnosis where applicable) vs well-segmented
   - Proposed corrected rendering per over-broken verse
   - Observed patterns at the chapter level

6. **Read-only by default.** Script does NOT modify v2/heb. Reports are diagnostic surface. A separate follow-on directive authorizes auto-apply (or hand-apply) after Stan-review.

### Phase 3 — Book-batch execution

7. **Execution order** (when Stan triggers via separate `directive` or amends this one):
   - **Genesis** (50 chapters) — first; narrative + some embedded poetry (Jacob's blessings, Gen 49)
   - **Isaiah** (66 chapters) — prophetic poetry + prose; biggest mixed-genre test
   - **Psalms** (150 chapters) — lyric poetry; heaviest parallelism load
   - Other books on demand

8. **Per-chapter pass produces** the report at `data/reports/audit/<book>-<chapter>.md`. Reports accumulate; Stan reviews at his pace.

9. **Cost estimate** (Sonnet at ~$0.05-0.10 per chapter audit pass):
   - Genesis: ~$3-5
   - Isaiah: ~$3-7
   - Psalms: ~$8-15
   - Three-book trio: ~$15-30 corpus-wide. Modest.

10. **Batch progress tracking**: script writes a per-book progress log at `data/reports/audit/<book>-progress.md` so partial sweeps are resumable.

### Phase 4 — Post-execution (deferred to separate directive)

After Stan reviews a meaningful sample of reports:

- **Auto-apply path**: enable the script to write proposed corrections back to v2/heb. Trips §7.3 trigger #10 again (operational discipline shift); requires separate adversarial audit before enabling. Pattern parallel to BoFM auto-apply gate for R19 resolver.
- **Hand-apply path**: Stan applies high-confidence corrections manually using the Python line-index pattern proven on Deut 6 and Ps 1.
- **Hybrid**: auto-apply on unanimous-high-confidence cases within audit-output; manual review for the rest.

Defer Phase 4 design until Phase 3 produces enough data to calibrate confidence thresholds.

## Reporting

Reply at `directives/replies/2026-05-16-2402-audit-layer-prototype-per-chapter-book-batch.md`:

- Phase 1 audit findings + cross-agent agreement
- Phase 2 commit hash for the built script + prompt template artifact
- Phase 3 progress (which book(s) processed; per-chapter report count; baseline diff if any v2 changes happen — they shouldn't in this read-only round)
- Any cases where the audit-cleared design produced unexpected output in actual chapter audits (surfacing required)

## Audit triggers

**§7.3 trigger #10 (discipline-shifting) + new tool class (LLM passage-level audit at production scale).** ≥2 parallel adversarial agents BEFORE implementation per CLAUDE.md + 2203/2400 precedent.

Phase 3 execution itself (running the script on chapters and producing reports) is read-only diagnostic per §7.4 — no audit needed for the per-chapter runs after Phase 1 clears the design.

## Cross-corpus note

This pattern ports cleanly to GNT, BoFM, and (eventually) LXX / Vulgate. After Tanakh validates production-scale execution, the same architecture lands in `atu_method/audit_rendering/` as a cross-corpus shared module. Out of scope for this directive; flagged for follow-on once Tanakh-side results inform whether to share immediately or per-repo specialize first.

## Relationship to 2401

Directive `2026-05-16-2401-coordinate-series-over-breaking-scan.md` (still pending) is a SUBSET of what 2402 produces — Phase 3 output contains coordinate-series over-breaking findings as a special case of the broader audit. Tanakh-Claude can either:
- (a) Process 2401 from 2402's accumulated report data (preferred — single tool, two analyses)
- (b) Process 2401 separately as a focused diagnostic, then 2402 supersedes
- (c) Mark 2401 superseded by 2402 and skip

Stan-judgment via directive editing if preferred.

---

# Appendix — Sonnet prompt template (validated)

Use the following as the user-prompt template per chapter:

```
Evaluate line breaks in Hebrew {book} {chapter} (v2/heb rendering) using the EXTENDED bidirectional ATU test.

# ATU theory + rubric

An ATU is the smallest text unit an attentive reader processes as a discrete cognitive chunk. One ATU per line.

## Necessary condition (universal)
A line is a legitimate standalone ATU only if BOTH:
1. **Forward grammatical closure** — grammatically complete (subj + verb + obligatory complements)
2. **Backward referential self-containment** — referents established or self-introducing

## Sufficiency extension for parallel poetry
Adjacent parallel cola may each pass the necessary condition yet jointly express one propositional content. Classes:
- **Synonymous parallelism** (B paraphrases A) → ONE ATU
- **Antithetic parallelism** (B contrasts A; comparison IS the thought) → ONE ATU
- **Synthetic parallelism** (B advances A with propositionally distinct content) → judgment call

## Caveat
Surface coordination (וְ), parallelism marks, accent disjunctives, editorial punctuation DO NOT auto-license breaks. They are candidate signals; the bidirectional test + cognitive-unity gate adjudicate. Coordinate short members filling one syntactic slot = one ATU.

# Your task

Per line, classify: KEEP-AS-IS / MERGE-WITH-PRIOR / MERGE-WITH-NEXT / AMBIGUOUS. One-sentence reasoning per line citing the specific gate.

# Output (tight)

- Per-verse: each line + verdict + reasoning
- Summary table: over-broken verses + parallelism class + lines→ATUs reduction
- Proposed corrected rendering for each over-broken verse
- Genre observation specific to {book} {chapter}

# Be honest

Don't manufacture verdicts. If a verse is well-segmented, mark KEEP-AS-IS. Aim for accurate diagnosis.

# {book} {chapter} v2/heb

{chapter_text}
```

Tanakh-Claude refines this template if Phase 1 audit surfaces prompt-design improvements. The version above is the one used in the three validated experiments — modify with care; deviations from validated language should be specifically justified in the Phase 1 audit reply.
