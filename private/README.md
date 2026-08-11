# private/ — layout and conventions

**This folder is gitignored** and intended to be Dropbox-backed (via Windows directory junction; see `handoffs/03-architecture.md` for the one-time setup). It holds pre-publication material, methodology canon, session artifacts, and active working documents that should not land in the public repository.

## Numbered subdirectory layout

| Dir | Purpose |
|---|---|
| `01-method/` | Methodology canon (`colometry-canon.md`), te'amim references, methodology comparisons |
| `02-book-briefs/` | Per-book editorial briefs and register notes |
| `02-rule-examples/` | Corpus-anchored worked examples for H-rules H1–H17 (one file per rule) |
| `03-sessions/` | Dated session artifacts — one subdirectory per session (e.g. `2026-04-25-scaffolding/`) |
| `04-audits/` | Self-audits, scan outputs, diagnostic findings |

Numbering leaves gaps for future categories without renaming existing folders. Empty placeholder directories are not created — add a numbered folder when actual content needs a home.

## When creating new files

- **Methodology refinements** → `01-method/colometry-canon.md` (the canon) or a new file in `01-method/`
- **Paper drafts, bibliography, strategy** → `02-research/`
- **Session-specific findings** → `03-sessions/[YYYY-MM-DD]-[topic-slug]/`
- **Scan / audit outputs** → `04-audits/`
- **Anything unclear** → drop at `private/` root; next session pass will file it

## Why private?

Three reasons:

1. **Pre-publication scholarly material.** The colometry canon, paper drafts, and methodology comparisons may eventually inform published work; they should not be world-readable in their working state.
2. **Project siloing.** Cross-references to sibling projects, comparative methodology notes, and overseer-style coordination documents live here so the public repo can present as an independent effort.
3. **Working noise.** Session notes, scan outputs, candidate lists, and audit drafts accumulate quickly and would clutter the public repo's commit history.

## Dropbox-junction convention

Sibling projects use a Windows directory junction so `private/` is a regular-looking folder in the repo but actually points at a Dropbox-synced location. This gives auto-backup, version history, and cross-machine access without interfering with `.gitignore`.

See `handoffs/03-architecture.md` for the one-time `mklink /J` setup. Until you set up the junction, `private/` is a normal local folder and edits are not auto-backed-up.
