# Tanakh Reader — Claude Code Instructions (thin stub)

This repo is operated by the **unified user-home orchestrator-Claude** at `C:\Users\bibleman\`. Stan opens VSCode at user-home, not at this repo.

If you are a Claude that spawned in this workspace (VSCode opened at this repo): **hand off**. Tell Stan to switch to a vault-Claude window at `C:\Users\bibleman\`. The unified Claude has full cross-repo context; per-repo Claudes don't.

## What this project is (for collaborators / forks)

A colometric reading edition of the Hebrew Bible at **tanakh-reader.com**. Each line on the page is an atomic thought unit (ATU); four layers stack per Hebrew cola — Hebrew (RTL pointed) / Translit / Interlinear / KJV verbatim. Modern pill toggles archaic→modern on the English row only. Sibling to readers-bofm + readers-gnt.

- **Data sources**: TAHOT for v0/v1 (word-stream canon); BHSA via Text-Fabric for ATU boundary identification (in `~/repos/biblical-corpora/bhsa/`)
- **Source files**: `data/text-files/v2/heb/` (hand-edited ATU partitions, single source of truth)
- **Build**: `PYTHONIOENCODING=utf-8 py -3 scripts/refresh_book.py --book <slug> --build` runs `apply_validators.py → propagate_editorial_layers.py → regenerate_english.py → build_books.py` with regression-gate enforced
- **Live deploy**: tanakh-reader.com (GitHub Pages, auto-deploys from main)
- **Pipeline implementation**: `scripts/atu_pipeline_v2/` (mechanical-first, 14 binding rules); validated draft at `data/text-files/v2-pipeline-draft/` (not yet promoted to v2/heb — see BHSA-canon-migration future arc)

## For more detail

- **Full prior operational discipline** (183-line CLAUDE.md, authored before the 2026-05-19 vault unification) is archived at [`_archive/2026-05-19-pre-unification/CLAUDE.md`](_archive/2026-05-19-pre-unification/CLAUDE.md). Includes editorial discipline (Stan-flagged verse procedure, Hebrew syntax anchor, cascade integrity rules), source text rules, file layout, validator infrastructure.
- **Prior cross-repo directives queue** (22 historical replies + processed entries from the pre-unification coordination system) is archived at [`_archive/2026-05-19-pre-unification/directives/`](_archive/2026-05-19-pre-unification/directives/). No new directives accepted — coordination happens via the unified Claude.
- **Canonical methodology** (cross-corpus): `~/repos/atu-method/docs/` — framework.md, binding-rules-hebrew.md, toolset-architecture.md, apparatus.md.

## Migration arc

This thin stub is part of the **master-blaster vault unification** (2026-05-19). Stan retired per-repo Claudes in favor of a single orchestrator at `C:\Users\bibleman\`. See `~/.claude/projects/C--Users-bibleman/memory/_named_arcs.md` for the arc.

`Audit-skippable per §7.3 (master-blaster Phase 6 — documentation-only stub demotion; no code, no canon, no rule, no data; archive preserves prior content for collaborator forkability)`
