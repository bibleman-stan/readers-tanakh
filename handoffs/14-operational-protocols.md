# 14 — Operational Protocols

This file codifies the "work smarter" practices that govern how Claude Code should approach corpus-wide changes, bug fixes, and methodology refinements in the Tanakh Reader project. These protocols are ported from the sibling Reader's GNT and BOM Reader projects (`readers-bofm/handoffs/14-operational-protocols.md`, `readers-gnt/handoffs/04-editorial-workflow.md`) where they were established through hard experience — every violation of the patterns below has resulted in either a bottleneck, a regression, or a partial fix that had to be redone.

**These are not optional. They are the operating discipline of the project.**

If the patterns described here feel unfamiliar in mid-session, you have probably drifted into the failure modes they exist to prevent. Re-read the relevant section before continuing the action you were about to take.

---

## A. Standard Operating Procedures

### A1. When Fixing a Bug

**Identify the CLASS of problem, not the single instance.**

When you find one bug, do not fix only the one bug. Find every instance of the same class in the corpus and fix them all in one commit.

1. Identify the class of problem (the underlying pattern)
2. Enumerate ALL instances of that class across the entire corpus (39 books × 23,000+ verses)
3. Fix them all in one commit (or one per-class commit, see I6)
4. Verify no remaining instances after the fix

**Example from this project (2026-04-30):** When the cascade hit RUNAWAY at Gen 24:38, the surface fix would have been "add a guard to h11_2_mid_verse_short_fronting." The class fix was: audit ALL 42 merge specs for the missing oscillation-blocker guard trio (`next_line_is_vav_coord_pp` / `_vav_coord_np` / `_wayyiqtol`), find that 18 were missing one or more, and add them all in one mechanical script. One bug surfaced; the class remediation prevented 17 future failures.

**The class identification habit:** when you find a problem, ask "what is the broader pattern this is an instance of?" and search for that pattern, not just the surface symptom. The `feedback_persistence_means_coverage_gap` memory captures the principle: persistence after a cascade pass = coverage gap, not "edge case to live with."

### A2. When Changing the Pipeline (MANDATORY Two-Phase Pattern)

Pipeline changes must always be two separate dispatches:

1. **Phase 1 — Algorithm change:** ONE agent modifies the script (e.g., `morphology.py`, `spec_runner.py`, `apply_specs.py`, `parse_teamim.py`). This is a single-file code change. The agent does only the code change, not the rebuild.

2. **Phase 2 — Corpus rebuild:** SEPARATE agents run the modified script on the natural cluster groups. For Tanakh Reader, the 6 clusters codified in CLAUDE.md are:
   - **Torah** — Genesis, Exodus, Leviticus, Numbers, Deuteronomy
   - **Former Prophets** — Joshua, Judges, 1-2 Samuel, 1-2 Kings
   - **Latter Prophets** — Isaiah, Jeremiah, Ezekiel, the 12 Minor Prophets
   - **Writings (prose)** — Ruth, Esther, Daniel, Ezra-Nehemiah, 1-2 Chronicles, Ecclesiastes prose
   - **Sifrei Emet (poetic)** — Psalms, Proverbs, Job 3:1–42:6
   - **Embedded Poetry (prose-routed)** — Exod 15, Deut 32, Deut 33, Judg 5, 1 Sam 2, 2 Sam 22, Isa 12, Hab 3, Lam 1-5, Song of Songs, Eccl 3:2-8

These are ALWAYS two separate dispatches. **Never dispatch one agent to do both code change AND full corpus rebuild.** Never run one agent on all 39 books — the Latter Prophets cluster alone is larger than several other clusters combined.

When the task is "find and fix," each cluster agent should find AND fix in its section, not just report. Otherwise the "find" phase becomes a sequential bottleneck where Claude has to manually consolidate findings before dispatching fix agents.

**Threshold rule (from CLAUDE.md):** Any batch of ≥25 surgical fixes spanning 3+ clusters MUST be split by cluster. No exceptions.

**This is not optional. Every violation of this pattern has resulted in a bottleneck.**

### A3. When Proposing Rule or Helper Changes

#### A3 Step 0 — Audit-evidence gate (mechanically enforced)

Before any non-trivial implementation, the **FIRST tool call** in your response must be either:

- **(a) Parallel Agent dispatches for adversarial audit** — at least 2 dimensions, in **one message** with multiple Agent tool_use blocks. The audits must complete and inform the design before any Edit/Write of the substantive implementation. The audit findings are the design input, not a post-hoc check.

- **(b) Explicit acknowledgment of audit-skip**: a one-line declaration `Audit-skippable: <reason>` citing a recognized trivial class:
  - **Port of already-validated sibling code** (with file:line reference to the source — e.g. "ported from `readers-bofm/validators/colometry/validate_doc_pointers.py`")
  - **Mechanical ingestion-script change** (no classification logic; just plumbing data through layers)
  - **Test or fixture file** (testing existing logic, not introducing new logic)
  - **Orchestrator / runner / glue** with no judgment (just calls other things in sequence)
  - **Scratch diagnostic** in `C:/tmp/`

**Mechanically gated** by `.claude/hooks/check_bash_discipline.py` at batch-boundary signals (`apply_specs --all-books`, `apply_validators --all-books`, `refresh_book --all-books`). The hook walks the recent transcript turns; if **<2 Agent dispatches** are found in the lookback window AND no `# audit-skippable:` prefix is on the command, the cascade is refused. Override mechanisms (visible in the JSONL trace for later audit):

- `# disciplined-allow: <reason>` — universal override (use sparingly)
- `# split-justified: <reason>` — A2-specific (cascade-on-main-thread permitted for true initial-exploration single pass)
- `# audit-skippable: <reason>` — A3-Step0-specific (audit not required because change is in a trivial class above)

#### A3 process (what to dispatch in case (a) above)

Before implementing a new colometric spec, helper, or validator:

1. Generate **multiple candidate approaches** (3–5 angles), not just the first instinct
2. Dispatch parallel adversarial agents to evaluate EACH approach against real corpus data
3. Each evaluation agent tests:
   - Accuracy rate (how often it produces the desired result)
   - False positive rate (how often it produces unwanted side effects on the 39-book corpus)
   - Implementation complexity (how hard it is to write and maintain)
   - Interaction with existing rules / specs (cross-rule consistency)
4. Compile a ranked recommendation with data BEFORE implementing anything
5. Only implement the top-ranked approach (or top 2 if complementary)

This prevents building the wrong solution and having to undo it. The "I'll just try it and see" approach is exactly the pattern Stan rejected on 2026-04-30 ("i kind of expect better from you - you're a coder par excellence; think through the possible code loop issues, use some adversarial audits if need be (in parallel, obviously); surely 'throw script out there and see what happens' can't be the smartest approach?"). See `feedback_round_wheel_before_rolling.md`.

**Why Step 0 has both procedural and mechanical layers:** the procedural layer (this section + CLAUDE.md hot-path) primes the cognitive default ("audit before propose"); the mechanical layer (the hook) catches drift when the cognitive default fails — exactly the same pattern used for canon-extension audits (CLAUDE.md "Pre-commit Adversarial-Audit Discipline" + `validators/hooks/commit-msg`). Directives without gates become decoration; gates without directives are friction. Both are required.

### A4. When Running Adversarial Agents

1. **Specific scoped mandates**, not "review all of X." Instead: "check Genesis 1, 24, Jonah 1, Ps 1, Prov 1 for these 5 specific patterns."
2. **Match model to task complexity** — don't default everything to Opus. Stan pays per-token; routing matters. See `feedback_haiku_default_for_mechanical.md`.
3. Each agent should **find AND fix**, not just find — avoid the sequential bottleneck where you have to manually consolidate findings and dispatch fix agents
4. **Split by cluster group** for corpus-wide reviews (see A2 for the 6 groups)

**Three-tier model routing for agent dispatch:**

- **Haiku** (cheapest, fastest): file moves, renames, glob/ls formatting, mechanical reference lookups (find all X, count Y), single-file reads-and-summarize with no judgment, yes/no checks against file content, set-membership tests, template fills.
- **Sonnet** (mid-tier): scanner runs where rules are already defined, quick consistency checks with narrow scope, documentation updates following a clear template, short adversarial checks on a single specific question, cross-project consistency checks once both sides are stable, mirroring edits between files.
- **Opus** (reasoning-heavy): multi-angle adversarial audits requiring deep reasoning, methodology synthesis across multiple sources, restructuring major documents, novel rule design or hierarchy reframes, anything where the judgment IS the work product.

**When in doubt, Sonnet is the right default** — it handles most scoped tasks capably at a fraction of Opus cost. Reserve Opus for tasks where the reasoning quality directly determines the output's value. **Always translate sub-agent "human-hours" estimates to agentic wall-time before relaying to Stan** (`feedback_haiku_default_for_mechanical.md`).

### A5. When Adding Split/Merge Specs or Morphology Helpers

1. Every split spec must validate that **both halves are viable cola** (each passes the atomic-thought test)
2. Every merge spec MUST carry the post-split-block guard trio: `next_line_is_vav_coord_pp` / `next_line_is_vav_coord_np` / `next_line_is_wayyiqtol` (see canon §2 plus the 2026-04-30 oscillation-runaway lesson). Without these, S1/S2/S3 splits → merge → split oscillation can occur.
3. After any spec change, re-run the cascade to convergence; verify max-passes stays well under MAX_PASSES=25
4. **Test on gold standard chapters before corpus-wide rollout.** For Tanakh Reader, the gold standards are:
   - **Jonah 1** — only v2/he chapter hand-edited start to finish; primary regression baseline
   - **Genesis 1** — creation account, dense parallelism + repetition, exercises wayyiqtol/refrain handling
   - **Deuteronomy 6:4-9** — Shema, classic vocative + relative chain
   - **Psalm 1** — short Sifrei Emet chapter, exercises poetic_register guards
   - **Proverbs 10** — short bicolon-saturated chapter
   - **Genesis 5 / 11 / Ezra 2** — genealogies, exercises numeral chain handling
   - **Genesis 24:38** — known oscillation site (post-2026-04-30 fix)

5. Never split or weaken: maqqef-joined prosodic words, construct chains (head + rectum), preposition + complement, atomic discourse formulas (וַיְהִי־כֵן etc.), Tetragrammaton in any compound divine name.

---

## B. Adversarial Testing Pattern

After ANY significant change to merge/split rules or morphology helpers, dispatch parallel adversarial agents BEFORE committing:

1. **Feature-specific adversary** — tests the new rule for over-merges, under-merges, and edge cases. "I just changed X. Find every place where X might be wrong on the gold-standard chapters AND on a representative sample from the 6 clusters."

2. **Rule-interaction adversary** — tests all rules together for cascading errors and oscillation between passes. "Spec X interacts with spec Y. Find conflicts. Especially: does X create line-shapes that Y will undo?"

3. **Benchmark regression adversary** — re-runs known-good test cases to check for regressions. "Check that Jonah 1, Genesis 1, Deut 6, Psalm 1 still look right."

4. **Cluster-coverage adversary (tanakh-specific)** — confirms the change behaves correctly across all 6 clusters, not just prose. "Stan-correction: 'are all these efforts fixing things globally or is this really only narrative books and we need separate looks at poetic literature?'" Embedded poetry and Sifrei Emet are easy to forget. See `feedback_rhetoric_bandwagon.md` (full-corpus sweeps beat spot-checks).

This pattern catches HIGH severity issues (rule interactions, oscillation, over-broad triggers) that code review alone misses.

**The pattern: change → cascade → dispatch adversaries → fix what they find → commit.** Not change → cascade → commit → discover issues later.

---

## C. Parallel Dispatch Discipline

### C1. Run Independent Tasks in Parallel

When you have multiple independent tasks (different files, different audits, different scans, different cluster rebuilds), dispatch them as **parallel agents in a single message**, not sequentially. Sequential dispatch turns parallel work into a queue.

**Bad:** Dispatch agent 1, wait for result, dispatch agent 2, wait for result, dispatch agent 3.
**Good:** Single message with three Agent tool calls, all dispatched simultaneously.

See `feedback_parallelize_default.md` and `feedback_parallel_horde_default.md`.

### C2. Don't Batch Tasks That Should Be Independent

When auditing the corpus, don't ask one agent to "audit all 39 books." Split it across the 6 cluster agents. Each agent finishes faster, you get results faster, and any failure is contained to one cluster.

### C3. Don't Be Sequential When You Don't Have To Be

Common Claude failure mode: "first I'll do A, then B, then C." If A, B, and C don't depend on each other, do them simultaneously. The agentic horde is the project's superpower — use it.

### C4. Horde-Amplification Ceiling

The 3-cluster baseline above is the floor, not the ceiling. When work decomposes into N≥4 independent units, dispatch all N — not 1 agent doing N dimensions sequentially. Stan's standing instruction: *"4-8x more agents on everything going forward unless it's a genuine single-point exercise."* Decompose audits per-dimension, corpus surveys per-cluster, fixture inventories per-fixture, validator builds per-subcase. Pre-spawn next-wave verification/integration agents BEFORE the producing wave finishes so the next wave doesn't gate-stall on completion.

### C5. Decompose Questions, Not Just Tasks

Question-answering decomposes the same as task execution. ≥2 lookups = parallel Haiku fan-out. Brevity by default. Never use model size as a latency excuse. See `feedback_decompose_questions_too.md`.

---

## D. Documentation Discipline

### D1. Update Handoffs at Important Decision Points

The handoff docs are the memory layer between sessions. Update them whenever:

1. A decision is made that affects future work
2. A principle is refined or a new rule is established
3. A pattern is identified across the corpus
4. A methodology reset happens (the rules themselves change)
5. A bug class is discovered and fixed
6. A feature is shipped or deprecated
7. A cascade or build pipeline change lands

Don't wait for end of session — update the relevant handoff(s) at the moment the decision is made. Future sessions need the reasoning, not just the result.

### D2. Append Dated Updates — Never Overwrite History

```markdown
---
### Update — 2026-MM-DD
- What changed
- What was decided
- New state
```

Never overwrite existing content. Append at the end. Future sessions need to trace how the methodology evolved, not just what it currently says.

### D3. Document the WHY, Not Just the WHAT

When updating a handoff or writing a commit message, explain *why* the change was made. The "what" can be derived from git diff. The "why" is what makes the decision legible to future sessions.

**Bad:** "Added 18 oscillation guards."
**Good:** "Added oscillation-blocker guard trio (next_line_is_vav_coord_pp / _vav_coord_np / _wayyiqtol) to 18 merge specs missing one or more guards. Discovered when tag-driven finite-verb classification (commit fa68cb5db) unblocked merge candidates that the skel-based mis-classification had been silently suppressing — the missing guards then exposed S1↔M2 oscillation at Gen 24:38, caught by MAX_PASSES=25 safety net. The trio is universally correct on merge specs (N+1 starting with vav-coord-PP/NP/wayyiqtol is recently-split material; merging would undo the split)."

---

## E. Tools-Over-Bash Discipline (Tanakh-Specific Lessons)

### E1. If You Wrote a Multi-Line Bash Heredoc, You Should Have Written a Script

The 2026-04-30 session generated a long list of multi-line Python heredocs run via `bash -c` for one-off operations (diff spec findings, audit guard coverage, bulk-edit yaml specs, verify v0/morph parity, inspect verses). Each one consumed context and broke at least once. Each one is an operation likely to recur.

**Discipline:** the second time you reach for a multi-line heredoc, stop and turn it into a persistent script under `scripts/`. The first time may be exploratory; the second time is a missing tool.

**Output format default:** every persistent script defaults to a **summary** output (one or a few lines, useful in a commit message or pull-request body). `--verbose`, `--json`, or `--per-finding` flags are opt-in. Never default to dumping the full corpus diff.

### E2. Save Merge / Mutation Scripts to Files, Not Bash Heredocs

Hebrew text contains apostrophes, niqqud, te'amim, maqqef, and other Unicode that interacts badly with bash heredocs and quoting. Always `Write` the script to `C:/tmp/*.py` (or a repo-local scratch dir) and run it via `py -3 C:/tmp/file.py`. Never paste large multi-line mutation scripts through `bash -c` or heredoc.

`/tmp` is **ephemeral between bash invocations on Windows**. Files written there in one Bash tool call may not exist in the next call. Use `C:/tmp/` (persistent) or a repo-local scratch path.

### E3. Content-Based Replacement Beats Line-Number Replacement

Line numbers drift as earlier merges compress the file. A script that uses `text.replace(multiline_before, single_line_after, 1)` with full multi-line context strings is immune to drift and trivially audits itself (the match count must equal the expected count, or something's wrong). Line-number-based scripts need re-sorting and offset math. **Mutation scripts should use exact multi-line content matching, not line indices.**

### E4. Find-the-Class → Build a Scanner > Dispatch Agents (when mechanical)

Before dispatching agents to do colometric judgment, check whether the class can be detected mechanically by:
- Line N tail shape (verb form, last token's morphology tag, ending punctuation)
- Line N+1 opener (preposition, conjunction, vav-coord PP/NP, wayyiqtol)
- Line N+1 absence of finite verb / clause boundary
- Cross-line tag patterns (construct head + non-genitive next, finite verb + bare-NP, etc.)

If yes, build a scanner under `scripts/scan_*.py` (Stan-at-scale pattern; see existing `scan_atomic_thought_violations.py`, `scan_under_broken.py`, etc.). The scanner approach is faster, more deterministic, and produces a discrete reviewable commit.

If no, dispatch atomic-thought-scanning agents (slower than regex but they discover classes regex can't be asked about — see I5 in the bofm version of this doc).

### E5. Multi-Class Scanners and Mutations Should Commit Independently (where practical)

Each colometric class should commit independently:
- Class A scanner findings → commit A
- Class B scanner findings → commit B
- Class C scanner findings → commit C

Reasons: easier to revert if one class goes wrong; cleaner git log; class-by-class diff inspection is humanly readable; and it forces explicit articulation of each class's diagnostic shape in the commit message. The 2026-04-30 cascade was committed as one large commit (`f0246844c`) because the cascade engine produces a single converged state — but the upstream cause (oscillation-guard backfill across 18 specs) could have been its own commit before the cascade ran.

### E6. Encode Invariants as Tests, Don't Spot-Check

Spot-check operations that you'd want to do again — token-tag alignment for specific verses, v0/morph parity with v0/eng-baseline, cascade idempotency for known-stable chapters — should be encoded as tests under `tests/` (or as scanners under `scripts/scan_*.py` if they fit that idiom), not re-run by hand each session. The scanners pattern (Stan-at-scale watchdogs) is exactly this discipline applied to corpus content; the same discipline applies to inner-loop infrastructure checks.

### E7. Tag-Driven Classification Over Skel-Heuristics

The TAHOT morph tag layer (`v0/morph/`, persisted 2026-04-30 in commit b4d90ebe1) is the authoritative classification source. When writing a new helper, classifier, or validator, the default should be: **read the tag, not the orthographic skeleton.** Skel-heuristics survive only as fallback for the rare token without a tag. This applies project-wide, not just to spec_runner — scanners, standalone validators, ingest scripts, propagation logic should all consume tags as the primary primitive. See `validators/_shared/morph_tags.py` (pure tag parsers) and `validators/_shared/morph_alignment.py` (per-chapter loader). Phase 4+ of the TAHOT pivot expands tag-driven classification beyond `is_finite_verb` to construct/participle/infinitive/proper-noun across all consumers.

---

## F. Pre-Commit Checklist

Before committing source text or v2/he changes:

1. ☐ All files saved and verified on disk (run `git diff --shortstat` to confirm scope)
2. ☐ Cascade pipeline ran cleanly (`scripts/refresh_book.py --book <book> --build` or `--all-books`); the pre-commit hook will re-run if v2/he is staged
3. ☐ Spot-check the build output for obvious damage (sense-line view of one affected verse from the gold standards)
4. ☐ Validator regression gate clean (`validators/run_all.py --baseline-check`); the pre-commit hook runs this
5. ☐ Commit message explains WHY, not just WHAT (D3)
6. ☐ Co-author trailer included
7. ☐ For canon edits: audit-status declared (`Audit-skippable per §7 (...)` OR `Audit dispatched: ...`)

Before committing pipeline changes (apply_specs.py, apply_validators.py, morphology.py, spec_runner.py):

1. ☐ Two-phase pattern observed (algorithm change committed separately from the corpus rebuild it triggers)
2. ☐ Adversarial agents dispatched and findings addressed (B1-B4)
3. ☐ Gold standard chapters spot-checked for regressions
4. ☐ The "find the class, not the instance" rule applied — no related forms left unfixed (A1)
5. ☐ Cluster-coverage check: poetic books and embedded poetry verified, not just prose (B4)

Before committing morphology / classification changes:

1. ☐ Doctest or fixture test added under `tests/` or in module docstrings
2. ☐ Tag-driven path used as primary; skel-heuristic only as fallback (E7)
3. ☐ Diff measured: how does this change spec_runner / scanner / validator output? (E1 — use a persistent diff script, not heredoc)

---

## G. The "Don't Be Sequential" Maxim

The single biggest performance gain in this project comes from parallel agent dispatch. When Stan tells you to do something, your default should be: **what parts of this can run simultaneously?**

- Reading multiple files → parallel Read calls in one message
- Auditing multiple books → parallel Agent calls split by cluster group
- Independent fixes across files → parallel Agent calls
- Per-cluster cascade rebuilds → parallel Agent dispatches (NEVER one agent on all 39 books)
- Building multiple independent tools → parallel Sonnet/Haiku agents

The exception is when one task genuinely depends on another's output. But even then, ask: can I dispatch the dependent task speculatively in parallel with a fallback if needed?

The "agentic horde" is not a metaphor. It's the operating model.

**Self-test before any sequence of operations:** if you find yourself thinking "first I'll do A, then B, then C," ask: are A and B and C truly dependent? If not, dispatch them in one message. If yes, can the dependent operation run speculatively? See `feedback_parallel_horde_default.md`.

---

## H. Tanakh-Specific Failure Modes (Lessons-Learned)

### H1. The 2026-04-30 cascade-on-main-thread anti-pattern

I (Claude) ran `apply_specs --all-books` and `refresh_book --all-books --build` on the main conversation thread, sequentially, after a code change. This is a direct violation of A2 (mandatory two-phase pattern). The correct pattern would have been:
- Phase 1: ONE agent commits the spec_runner code change
- Phase 2: SIX parallel cluster agents (Torah / Former Prophets / Latter Prophets / Writings prose / Sifrei Emet / Embedded Poetry) each run apply_specs + refresh_book on their cluster

Wall-time would have been ~max(per-cluster cascade) instead of sum. The same applies to validator runs and scanner runs.

### H2. The git-stash + bash-heredoc diff-capture anti-pattern

To compare spec findings before/after a code change, I used `git stash push → run --json > /tmp/before → git stash pop → run --json > /tmp/after → python diff` in a bash chain. It broke three times in one session: stash didn't pop cleanly, /tmp was ephemeral on Windows, compound chains masked failures. The correct pattern is a persistent `scripts/diff_specs.py` that loads two spec_runner configurations in-process (or accepts two git refs), runs them, and emits the delta — no shell, no stash, no /tmp.

### H3. The "ingest the full git status" anti-pattern

`git status --short | head -10` ingested 3,494 file names (130KB) into context when `git status --porcelain | wc -l` was the right call. Same for `git diff` vs `git diff --shortstat` vs `git diff --numstat`. **Default to summary commands; opt-in to verbose only when needed.** This applies to all script outputs too (E1).

### H4. The two-cascade-engines confusion

`apply_validators.py` (standalone validators with adoption gate) and `apply_specs.py` (spec-runner findings) are two separate cascade engines. `refresh_book.py` only invokes the first. So when a spec_runner change lands, you must manually run `apply_specs --all-books` BEFORE `refresh_book --all-books --build`. This is a footgun unless you already know the architecture. **Eventual fix:** unified cascade pipeline. **Interim discipline:** a comment in CLAUDE.md (Follow-On Rebuild Cascade section) and a warning in apply_specs.py output noting that refresh_book is downstream.

### H5. The dry-run cascade RUNAWAY artifact

`apply_specs.py` cascades to convergence over MAX_PASSES=25 passes. Pre-2026-05-03, dry-run mode skipped writes (lines 217-218, 238-239) but the cascade loop still ran until convergence. Each pass re-read the same unchanged file from disk → identical findings → identical "would-fire" output → MAX_PASSES trip with a misleading "hot verses" report. The hot verses were the FIRST verses each spec fires on per-chapter, not actual oscillators.

This wasted a full session-arc cycle: 2026-05-02 dispatched the m4_e cognition-verb spec investigation against a "Gen 3:5 RUNAWAY" that was a dry-run artifact. m4_e was perfectly innocent — fired zero times on current v2 (Gen 3:5 already merged by hand-edit) and converged in one pass on v1 baseline. The actual oscillation was S4↔M2 at Gen 33:2 et al., entirely unrelated. The session deferred m4_e on a phantom blocker.

**Fixed 2026-05-03:** `apply_specs.py` now exits dry-run after pass 1 with a clear stderr note ("dry-run: pass-1-only; cascade convergence requires real writes"). The post-convergence idempotency assertion (lines 248-261) is also skipped under dry-run for the same reason. Real RUNAWAY messages clarified to "real oscillation" wording.

**Discipline going forward:**
- Dry-run is a single-pass preview. To detect oscillation, re-run without `--dry-run` against a scratch copy of the corpus (under `C:/tmp/`).
- When investigating a "RUNAWAY" report, FIRST check whether the originating run was dry-run. If so, the verses named in the hot-list are not necessarily oscillators — they may just be the first verses any spec fires on.
- Carry-forward (separate cycle): cluster-cascade dispatcher silently bails on apply_specs RUNAWAY exit (code 2) without surfacing the warning to human-visible output. The dispatcher prompt should explicitly capture and report `[RUNAWAY]` lines from stderr. Until fixed, post-cascade verification on a couple of representative books in the main thread (non-dry-run) is essential before assuming cluster cascades converged cleanly.

### H6. Verification-driven discovery is a first-class discovery method

Across multiple 2026-05-02 cycles, engine fixes uncovered latent bugs in OTHER parts of the engine — not by intent, but because cascade verification of the immediate fix exposed pre-existing FPs/FNs that had been masked. Five cycles, four latent-bug surfacings: Sp\*-tail buried-verb in `morph_tags.is_finite_verb`, missing aspect `u` in `_FINITE_VERB_ASPECTS`, cross-verse merge in `validate_speech_intro_framing`, post-cascade misdiagnosis as oscillation that turned out to be dry-run artifact (H5).

**The pattern:** a "cascade & verify" step is not just confirming the immediate change works — it's a fishing trip for latent bugs. Each verification cycle should treat unexpected results as discovery opportunities, not anomalies-to-suppress.

**Discipline:** when verification surfaces unexpected behavior:
1. Bisect against the baseline (stash uncommitted changes; does the issue persist?)
2. If yes → pre-existing latent bug, not introduced by this cycle. Open a new investigation branch, don't try to fix it inside the current cycle.
3. If no → the current change exposed it. Decide: fix in current cycle, or defer with a documented entry in the session's pending notes.

**Companion misdiagnosis-prevention discipline:** before accepting any "X is causing Y" hypothesis from a single observation, run a definitive falsification test:
- For "spec X causes oscillation Y" → run X ALONE on the affected verse, in non-dry-run mode, against a scratch corpus. If 0 changes or single-pass convergence, X is innocent.
- For "verse V is oscillating" → run the cascade on V in non-dry-run mode against a scratch corpus and observe the actual touch count. Don't trust dry-run RUNAWAY reports (H5).
- For "the cascade silently bailed" → check the dispatcher's actual exit code and stderr capture, not just the summary line.

The 2026-05-02 m4_e investigation was based on misdiagnosis A1 ("dry-run RUNAWAY = m4_e oscillating") + A2 ("Gen 5:31 / 24:30 oscillating in committed baseline") — both falsified by 2026-05-03 verification agents in <30 minutes once the falsification tests were dispatched. The investigation work itself was useful (uncovered the dry-run artifact and the real S4↔M2 partner), but the original framing was wrong. Cheaper to falsify-first than to debug-on-a-bad-premise.

---

## I. Origin of These Protocols

These protocols were established in the Reader's GNT project after experience showed that ad hoc workflows don't scale. The same failure modes have surfaced across all three sibling projects (gnt, bofm, tanakh):

- **A1 (find the class):** A bug was fixed in one place, then re-discovered three more times in subsequent sessions before the class was identified
- **A2 (two-phase pattern):** A single agent was given "modify the script and rebuild the corpus" — it spent 90% of its time on the rebuild and never finished the modification properly
- **A3 (multiple candidates):** A first-instinct fix was implemented, shipped, and then had to be undone two sessions later when a better approach was found
- **A4 (haiku for review):** Opus was being used for simple read-only audits at 5x the cost and 3x the latency
- **B (adversarial testing):** A change shipped, looked clean in spot checks, and then dozens of misclassifications were discovered by adversarial review three sessions later
- **C (parallel dispatch):** Sequential agent dispatches were bottlenecking the project — what should have been 30 minutes of parallel work was taking 3 hours sequentially
- **E1-E7 (tools-over-bash):** A 2026-04-30 tanakh session generated multi-line bash heredocs for at least 8 distinct one-off operations, each consuming context and several breaking on Windows-specific issues — that session is the proximate cause of this file existing in tanakh

The Tanakh Reader project hit the same failure modes during the April 2026 sessions. Adopting these protocols formally prevents the same lessons from being relearned.

---

## J. Protocol Self-Audit (End-of-Session)

Before WRAP-UP, ask:

1. Did I dispatch any "all 39 books" agent runs? → Should have been per-cluster.
2. Did I write a multi-line bash heredoc? → Should be a persistent script.
3. Did I spot-check an invariant? → Should be a test or scanner.
4. Did I make a pipeline change without adversarial agents? → Should have run B1-B4.
5. Did I commit a fix without finding the class? → Should re-grep for related instances.
6. Did I use Opus for a Haiku-tier task? → Routing failure.
7. Did I read a verbose tool output when summary would have sufficed? → Output-format failure.

Log violations to `intra-session-log.md` under "Discipline failures" so the pattern shows up across sessions and can drive future protocol refinement.

---

*Created: 2026-04-30 (ported from `readers-bofm/handoffs/14-operational-protocols.md`)*
*Origin: Reader's GNT project (`readers-gnt/handoffs/04-editorial-workflow.md`), via BOM Reader port (`readers-bofm/handoffs/14-operational-protocols.md`)*
