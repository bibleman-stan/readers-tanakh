# Handoff Index — Tanakh Reader

These documents capture project state so that any session (human or AI) can spin up with full context. Read them in order.

| File | Covers |
|---|---|
| `00-index.md` | This index and update protocol |
| `01-project-overview.md` | Project vision, scholarly landscape, methodological commitments, source-text rationale |
| `03-architecture.md` | Repo structure, build pipeline (planned), private folder convention, data sources |
| `04-editorial-workflow.md` | How a chapter goes from raw TAHOT to gold-standard reading edition |
| `14-operational-protocols.md` | **READ THIS CAREFULLY** — work-smarter operating discipline ported from sibling projects: find-the-class fixes, mandatory two-phase pipeline pattern, parallel dispatch, adversarial testing, tools-over-bash, tanakh-specific failure modes |

The slots `02-` and `05-13-` are intentionally skipped. Methodology (the colometry 1-method/canon) lives in `private/01-method/colometry-canon.md`, not in handoffs, because it is pre-publication scholarly material. The `14-` slot mirrors the bofm/gnt convention so the operational-protocols file occupies the same numeric position across sibling projects (an internal convention only — repos remain publicly siloed per CLAUDE.md).

**Methodology and architecture references**: this repo's methodology 1-method/canon at `private/01-method/colometry-canon.md` and several handoffs (01, 03, 04) cite framework material that now lives authoritatively in `../atu-method/docs/` (`framework.md`, `architecture.md`, `apparatus.md`, `change-protocol.md`, `glossary.md`). When reading those handoffs, treat framework-level content as a recap and the atu-method docs as normative.

---

## Update Protocol

When updating handoff docs, append a dated block at the bottom of the relevant file:

```markdown
---
### Update — 2026-MM-DD
- What changed
- What was decided
- New state
```

Never overwrite history — always append.

