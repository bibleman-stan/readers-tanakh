# Tanakh Reader — Claude Code Instructions (thin stub)

This repo is operated by the **unified user-home orchestrator-Claude** at `C:\Users\bibleman\`. Stan opens VSCode at user-home, not at this repo.

If you are a Claude that spawned in this workspace (VSCode opened at this repo): **hand off**. Tell Stan to switch to a vault-Claude window at `C:\Users\bibleman\`. The unified Claude has full cross-repo context; per-repo Claudes don't.

## What this project is (for collaborators / forks)

A colometric reading edition of the Hebrew Bible at **tanakh-reader.com**. Each line on the page is an atomic thought unit (ATU); four layers stack per Hebrew cola — Hebrew (RTL pointed) / Translit / Interlinear / KJV verbatim. Modern pill toggles archaic→modern on the English row only. Sibling to readers-bofm + readers-gnt.

- **Data sources**: TAHOT for v0/v1 (word-stream canon); BHSA via Text-Fabric for ATU boundary identification (in `~/repos/biblical-corpora/bhsa/`)
- **Source files**: `data/text-files/v2/heb/` — the **deployed mechanical-first pipeline** ATU output (BHSA clause-atoms + binding rules; 37 books published 2026-05-22, Aramaic verses held). Single source of truth the reader builds from. The *source text* (v0 forms / consonants / niqqud / te'amim) is never modified; the ATU partitions are regenerable method output, **not** a hand-edit oracle. (Authoritative live-state record: [`atu-method/docs/deployment-status.md`](../atu-method/docs/deployment-status.md).)
- **Build**: `PYTHONIOENCODING=utf-8 py -3 scripts/refresh_book.py --book <slug> --build` runs `apply_validators.py → propagate_editorial_layers.py → regenerate_english.py → build_books.py` with regression-gate enforced
- **Live deploy**: tanakh-reader.com (GitHub Pages, auto-deploys from main)
- **Pipeline implementation**: `scripts/atu_pipeline_v2/` (mechanical-first, 14 binding rules). The mechanical-first ATU breaks ARE promoted/live (`v2/heb`, 37 books; commits `0f9471b1c`/`921b76324`). What remains **deferred** is the separate **BHSA-canon-migration** — switching the word-*form* source from TAHOT to BHSA (the 823-verse form-mismatch arc); `data/text-files/v2-pipeline-draft/` is scratch for that, NOT the ATU-break status.

## Editorial discipline (Tanakh-specific; applies whenever touching this repo)

Moved here 2026-05-29 from user-level `~/.claude/CLAUDE.md` as part of the orientation-file restructure (per-repo-shard recommendation from the absorption audit). These ALL stay load-bearing whenever Hebrew/Tanakh work is in scope:

- **Anchor in Hebrew syntax, not English-translation surface.** KJV smooths wayyiqtol chains into English temporal subordinations ("when she saw"). Check Macula `_morph_tag` before agreeing/disagreeing with an editorial intuition sourced from English. Wayyiqtols (`Vqw*`, `Vnw*`) without intervening subordinator = sequential chain → split per framework.
- **Stan-flagged verse = class-investigation directive.** Diagnose underlying pattern → audit self first (bidirectional test + binding rules from `binding-rules-hebrew.md`) → only if step 2 finds a real gap, investigate corpus-wide.
- **Editorial-call structure.** When Stan names a verse with desired partition: line 1 = "Got it — [Stan's reading]"; line 2-N = the diff. No leading analytical defense of alternatives.
- **Cascade integrity.** `apply_validators.py` causes regression → revert → root-cause → fix → re-apply with integrity gate. Do NOT build downstream-recovery tools first.
- **No editorial overlay has force.** Te'amim, niqqud, sof-pasuq, paseq, versification: preserved for textual fidelity, zero force in editorial decisions.
- **Audit the foundation, don't assume it.** When residuals cluster and look "irreducible," suspect the substrate first (normalizer/parser/treebank) and verify each form against the ACTUAL parser, not a spelling heuristic — an unaudited foundation poisons every rule above it (51% of EME -eth/-est verbs were mis-tagged behind a suffix-only gap-detector).
- **Read full untruncated lines; audit proactively.** Truncation hides fractures (subject severed from predicate). When Stan flags ONE symptom, do a full untruncated line-by-line audit of the affected book and surface the rest yourself — don't make him flag them one at a time. Verify expected behavior, not just the absence of a diff.
- **User-facing site copy stays scholarly — NO internal jargon.** Internal substrate/method terms (gold, spray, judgment-residual, fly-swatting, v1.5/v2 stage labels) must NEVER appear in live reader text — name the actual scholarly object. Scan ported/rebranded reader copy for leaks before deploy.

## For more detail

- **Full prior operational discipline** (183-line CLAUDE.md, authored before the 2026-05-19 vault unification) is archived at [`_archive/2026-05-19-pre-unification/CLAUDE.md`](_archive/2026-05-19-pre-unification/CLAUDE.md). Includes editorial discipline (Stan-flagged verse procedure, Hebrew syntax anchor, cascade integrity rules), source text rules, file layout, validator infrastructure.
- **Prior cross-repo directives queue** (22 historical replies + processed entries from the pre-unification coordination system) is archived at [`_archive/2026-05-19-pre-unification/directives/`](_archive/2026-05-19-pre-unification/directives/). No new directives accepted — coordination happens via the unified Claude.
- **Canonical methodology** (cross-corpus): `~/repos/atu-method/docs/` — framework.md, binding-rules-hebrew.md, toolset-architecture.md, apparatus.md.

## Migration arc

This thin stub is part of the **master-blaster vault unification** (2026-05-19). Stan retired per-repo Claudes in favor of a single orchestrator at `C:\Users\bibleman\`. See `~/.claude/projects/C--Users-bibleman/memory/_named_arcs.md` for the arc.

`Audit-skippable per §7.3 (master-blaster Phase 6 — documentation-only stub demotion; no code, no canon, no rule, no data; archive preserves prior content for collaborator forkability)`
