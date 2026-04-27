# Handoff Index — Tanakh Reader

These documents capture project state so that any session (human or AI) can spin up with full context. Read them in order.

| File | Covers |
|---|---|
| `00-index.md` | This index and update protocol |
| `01-project-overview.md` | Project vision, scholarly landscape, methodological commitments, source-text rationale |
| `03-architecture.md` | Repo structure, build pipeline (planned), private folder convention, data sources |
| `04-editorial-workflow.md` | How a chapter goes from raw TAHOT to gold-standard reading edition |

The slot `02-` is intentionally skipped. Methodology (the colometry canon) lives in `private/01-method/colometry-canon.md`, not in handoffs, because it is pre-publication scholarly material.

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

---

### Established — 2026-04-25 (scaffolding session)

Files created this session:
- `00-index.md` — this file
- `01-project-overview.md` — vision, te'amim methodology framing, source-text choice, project siloing decision, MVP scope
- `03-architecture.md` — repo layout, planned scripts, private folder convention with junction setup
- `04-editorial-workflow.md` — workflow stub (will mature with the Jonah MVP pass)

Decisions locked in this session:
- Source text: multi-source vendoring into `research/`. STEPBible TAHOT primary (feeds `v0/prose/`); OSHB and UXLC as Leningrad-tradition transcription cross-checks; MAM as Aleppo-tradition reference (not adopted as base). All free-licensed.
- Textual posture: this is a colometric reading edition based on a single textual tradition (Tiberian MT, Leningrad). LXX, Dead Sea Scrolls, Samaritan Pentateuch, Targums, Peshitta, Vulgate explicitly out of scope. Mirrors the sibling Greek edition's posture of inheriting an established text and not relitigating textual decisions.
- Methodology: atomic thought is the prior; te'amim are evidence + starting draft, not authority. Three structural criteria (atomic thought, single image, Hebrew syntax). See colometry-canon.md for full architecture.
- Versification: Hebrew primary, Christian crosswalk in URL aliases and metadata
- Book order: TaNaK (Torah / Nevi'im / Ketuvim)
- English layer: structural glosses, deferred behind Hebrew MVP
- First book: Jonah (covers prose + *Sifrei Emet* poetry, no Aramaic, no major K/Q complications)
- Domain: tanakh-reader.com (secured, CNAME committed)
- Repo visibility: public from start, siloed from any sibling projects
- Audio + PWA: skipped for MVP
- Text-file tiers: start with v0 → v1-he-baseline → v4-editorial; defer v2/v3 until proven necessary [SUPERSEDED — see 2026-04-27 update below]

---

**2026-04-26 update:** v1-teamim directory renamed to v1-he-baseline; path references updated throughout this doc to align with the canon's te'amim-as-evidence framing (no longer te'amim-as-prior).

**2026-04-26 update:** The 2026-04-25 decision to "defer v2/v3 until proven necessary" (line above) is superseded. The four-tier pipeline (v0 → v1 → v2 → v3 → v4) is now active. v2 (Layer 1 syntax pass) and v3 (Layer 3 colometry pass) apply only the closed list of mechanical rules via apply_v2.py and apply_v3.py, with STRONG-only auto-application and the ≥80% adoption gate and tier-diff audit gate as risk mitigations. See `03-architecture.md` and `04-editorial-workflow.md` for full documentation.

**2026-04-26 update:** `data/text-files/` restructured into per-tier subfolders (v0/, v1/, v2/, v3/, v4/). Tier-name identity strings (v1-he-baseline, v2-he-syntax, etc.) unchanged; only filesystem layout. Path references in this doc updated to the new layout.

**2026-04-27 update:** Tier collapse — both 2026-04-26 multi-tier updates above are superseded. The auto-apply tiers (v2-he-syntax via apply_v2, v3-he-colometry via apply_v3) are retired; the editorial gold standard moves from `v4/editorial/` to `v2/he/`; the parallel per-word layers move from `v4/{eng-interlinear,eng-gloss,translit}/` to `v2/{eng-interlinear,eng-gloss,translit}/`. Pipeline is now **v0 → v1 → v2** (3 tiers). STRONG-tagged validator findings feed the editorial work queue directly per canon §2 Mechanical-rule authority. See canon §8 entry 2026-04-27 + `03-architecture.md` + `04-editorial-workflow.md` for full updates.
