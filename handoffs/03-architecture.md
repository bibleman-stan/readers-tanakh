# 03 — Architecture & Build Pipeline

## Position in the four-plane architecture

readers-tanakh participates in the cross-corpus **four-plane architecture** documented at [`../atu-method/docs/architecture.md`](../atu-method/docs/architecture.md). The decomposition:

| Plane | Where | This repo's role |
|---|---|---|
| Universal | `../atu-method/` | **Consumes.** KJV alignment engine (`atu_method.kjv_alignment`), swap engine (`atu_method.swaps`), MetaV CSVs, STEPBible Strong's lexicons, swap lists. |
| Engine | `validators/`, `scripts/build_books.py`, `scripts/refresh_book.py`, pre-commit hook | **Owns.** Hebrew-side validators, build pipeline, cascade orchestration. |
| Corpus | `data/text-files/v2/he/`, `data/text-files/v0/prose/` | **Owns.** TAHOT-sourced Hebrew, hand-edited gold standard. |
| Editorial | `private/01-method/colometry-canon.md` | **Owns** Hebrew-specific application (rules H1–H18, M1–M4 overrides). Cross-corpus framework body lives at `../atu-method/docs/framework.md`. |

The repo structure below covers planes 2–3 (engine + corpus) plus the public-facing web app. Plane 1 (universal) is consumed via relative paths into the sibling repo. Plane 4 (editorial) lives in gitignored `private/`.

## Repo Structure (planned)

```
readers-tanakh/
  CLAUDE.md                              # Claude Code orientation doc
  README.md                              # Public-facing description
  CNAME                                  # Custom-domain pointer (tanakh-reader.com)
  LICENSE                                # MIT (code only; data licenses in README)
  .gitignore                             # Ignores research/, private/, OS files, etc.
  index.html                             # Main web app (planned; RTL, all CSS/JS inline)
  data/
    text-files/
      README.md                          # Tier system documentation
      v0/
        prose/                           # Per-chapter files derived from TAHOT (NEVER edit)
          01-genesis/, 02-exodus/, ...
      v1/
        he-baseline/                     # Hebrew baseline cola draft (machine-generated)
          01-genesis/, 02-exodus/, ...
        eng-interlinear/                 # Per-word English (cola-aligned to v1/he-baseline)
        eng-gloss/                       # Naturalized English (one per cola)
        translit/                        # Per-word translit (cola-aligned)
      v2/
        he/                              # Hand-edited Hebrew gold standard (single source of truth)
          01-genesis/, 02-exodus/, ...
        eng-interlinear/                 # Re-segmented per v2/he cola structure (propagator)
        eng-gloss/                       # Re-segmented; smooth English (deferred for hand-edit)
        translit/                        # Re-segmented per v2/he cola structure
    versification-crosswalk.json         # Hebrew ↔ Christian numbering map (vendored from Sefaria)
    lemma_index.json                     # Searchable Hebrew lemma index (built later)
  books/                                 # Generated HTML fragment files
    genesis.html, exodus.html, ...
  scripts/                               # Build, parse, scan, validate
    ingest_tahot.py                      # TAHOT TSV → v0-prose chapter files (primary path)
    ingest_oshb.py                       # OSHB OSIS → sibling tree (on-demand cross-check) [planned, not yet built]
    ingest_uxlc.py                       # UXLC → sibling tree (on-demand cross-check) [planned, not yet built]
    ingest_mam.py                        # MAM → sibling tree (Aleppo tradition reference) [planned, not yet built]
    diff_sources.py                      # For any verse, show how each vendored source renders it [planned, not yet built]
    parse_teamim.py                      # Te'amim parser (prose + Sifrei Emet) → v1/* layers
    propagate_editorial_layers.py        # v2/he cola changes → re-segment v2/{eng-*,translit}/
    build_books.py                       # v2/* (cascade to v1/*) → books/*.html
    ...
  validators/                            # Layer-1 (syntax) and Layer-3 (colometry) checks
    syntax/                              # Hebrew break-legality rules
    colometry/                           # Methodology rule checks
      validate_clause_nucleus_split.py   # Rule H18 — Clause-Nucleus Integrity; REVIEW-REQUIRED only; not adopted
    _shared/                             # Shared helper modules for validators
      poetic_register.py                 # Detects Sifrei Emet chapters (Psalms, Proverbs, Job 3:1–42:6)
  handoffs/                              # Project documentation (this folder)
  research/                              # Gitignored — vendored external corpora
    stepbible-tahot/                     # STEPBible TAHOT TSV (Leningrad; primary)
    morphhb/                             # OSHB OSIS XML (Leningrad; transcription cross-check)
    uxlc/                                # Tanach.us UXLC (Leningrad; transcription cross-check)
    mam/                                 # Miqra `al pi ha-Mesorah (Aleppo; tradition reference)
    jps-1917/                            # JPS 1917 English (deferred comparator)
  private/                               # Gitignored — strategic / pre-publication workspace
                                         # (Windows junction → Dropbox; see below)
```

Most of the directories under `data/text-files/`, `scripts/`, `validators/`, `books/`, and `research/` do not yet exist. They will be created as the relevant sessions populate them.

## Data Sources

Multiple Hebrew-text sources are vendored to enable transcription cross-checking, tradition awareness, and empirical re-pick of the primary if a candidate proves more useful in practice.

| Source | Role | Tradition | License | URL |
|---|---|---|---|---|
| **STEPBible TAHOT** | Primary (feeds `v0/prose/`) | Leningrad / WLC | CC-BY-4.0 | github.com/STEPBible/STEPBible-Data |
| **Open Scriptures Hebrew Bible (OSHB)** | Transcription cross-check | Leningrad / WLC | Text PD; lemma + morph CC-BY-4.0 | github.com/openscriptures/morphhb |
| **Tanach.us (UXLC)** | Transcription cross-check | Leningrad / WLC | No restrictions | tanach.us |
| **Miqra `al pi ha-Mesorah (MAM)** | Tradition reference (not adopted as base) | Aleppo | CC-BY-SA | opensiddur.org / Wikisource |
| **Sefaria versification map** | Hebrew ↔ Christian crosswalk | — | CC-BY (per-edition) | github.com/Sefaria/Sefaria-Project |
| **JPS 1917** | English comparator (deferred) | — | Public domain | sefaria.org / Wikisource |

All vendored corpora live in `research/` (gitignored). The `data/` folder holds *our* derivative work and cross-references.

**Constraint:** `data/text-files/v0/prose/` has exactly one source feeding it at any time. Currently that source is TAHOT. Re-picking the primary is an editorial decision (write a different `ingest_*.py`), not an architectural one. The non-primary WLC-derived sources serve as cross-checks via a `scripts/diff_sources.py` tool (planned, not yet built) that will surface transcription disagreements at the verse level.

**Textual posture:** This is a colometric reading edition based on a single textual tradition (Tiberian MT, Leningrad). LXX, Dead Sea Scrolls, Samaritan Pentateuch, Targums, Peshitta, and Vulgate are explicitly out of scope. See `private/01-method/colometry-canon.md §1.1` for the full statement.

## Private Workspace (`private/`)

The `private/` folder contains strategic, pre-publication, and methodology material that is intentionally kept out of the public repo: the colometry canon, paper drafts, session artifacts, scan outputs, and adversarial audit reports. The folder is excluded via `.gitignore` per the project-siloing decision.

### Numbered subdirectory layout

| Dir | Purpose |
|---|---|
| `01-method/` | Methodology canon (`colometry-canon.md`), te'amim references, methodology comparisons |
| `02-research/` | Paper drafts, prospectus material, bibliography, strategy notes |
| `03-sessions/` | Dated session artifacts — one subdirectory per session |
| `04-audits/` | Self-audits, scan outputs, diagnostic findings |

Numbering leaves gaps for future categories. Empty placeholder directories are not created — add a numbered folder when actual content needs a home.

### Dropbox-junction setup (recommended)

The pattern used in sibling projects is to make `private/` a Windows directory junction pointing at a Dropbox-synced folder, so:

- The `.gitignore` rule keeps it out of the public repo
- Dropbox auto-syncs to the cloud and provides version history
- All file-system operations work transparently through the junction

**One-time setup** (run from a Windows command prompt, not git bash):

```batch
mkdir "C:\Users\bibleman\Dropbox\tanakh-reader-private"
robocopy "C:\Users\bibleman\repos\readers-tanakh\private" "C:\Users\bibleman\Dropbox\tanakh-reader-private" /E
rmdir /S /Q "C:\Users\bibleman\repos\readers-tanakh\private"
mklink /J "C:\Users\bibleman\repos\readers-tanakh\private" "C:\Users\bibleman\Dropbox\tanakh-reader-private"
```

**Verify:**
```bash
ls -la private    # should show: private -> /c/Users/bibleman/Dropbox/tanakh-reader-private
```

**Note for `find`:** the Unix `find` command does not follow junctions by default. Use `find -L private/` if traversing. `ls`, `wc`, the Read tool, and the Grep tool all work transparently.

## Tier System — text-files/

The pipeline runs **v0 → v1 → v2** (3 tiers; collapsed from the 5-tier scheme on 2026-04-27).

| Tier | Directory | Engine | Status |
|---|---|---|---|
| v0 | `v0/prose/` (+ `v0/eng-baseline/`, `v0/translit-baseline/`) | `ingest_tahot.py` | Derived from TAHOT — verse-marked, full niqqud, full te'amim, ketiv/qere preserved. **NEVER EDIT.** Reference baseline. |
| v1 | `v1/he-baseline/` (+ `v1/eng-interlinear/`, `v1/eng-gloss/`, `v1/translit/`) | `parse_teamim.py` (prose + Sifrei Emet) | Machine-generated cola draft. Te'amim-as-evidence starting point; editor's draft, not a normative "version 1." |
| v2 | `v2/he/` | Stan + Claude | Hand-edited Hebrew gold standard. Single source of truth for the web app. Applies the three forces (atomic thought, single image, Hebrew syntax) and the four merge-overrides; consumes Layer 1 + Layer 3 validator findings as a work queue. |
| v2 | `v2/eng-interlinear/`, `v2/translit/` | `propagate_editorial_layers.py` | Per-word layers re-segmented to v2/he cola structure when Hebrew edits land. Word-stream invariant enforced. |
| v2 | `v2/eng-gloss/` | `regenerate_english.py` (post-Wave-6) | KJV 1769 verbatim distributed per Hebrew ATU cola via `atu_method.kjv_alignment.align_verse()` (Strong's matching against TAHOT's per-Hebrew-token Strong's data). Replaces the retired Macula structural-gloss pipeline. |

**Validator findings as work queue.** Validators in `validators/syntax/` (Layer 1) and `validators/colometry/` (Layer 3) emit STRONG-MERGE-CANDIDATE / STRONG-SPLIT-CANDIDATE / REVIEW-REQUIRED tags. STRONG findings are Category A per canon §2 Mechanical-rule authority — apply confidently. REVIEW-REQUIRED items go to per-item editorial judgment. The `≥80%` adoption gate (canon §7 proposed-rule adoption protocol) governs when a validator's STRONG findings reach Category A confidence.

**Why no separate auto-apply tier:** the previous v2-he-syntax (auto-apply Layer 1 STRONG) and v3-he-colometry (auto-apply Layer 3 STRONG) tiers were retired on 2026-04-27. The intermediate tiers added pipeline complexity without adding capability — STRONG findings now feed the editorial work queue directly with the same Category A/B/C reasoning the canon already governs. The closed-list rule set (H1, H2, H5, H7, H11, H16) was not the mechanical-error surface that drove the original tier expansion in sibling projects; the autonomy boundary is established at the canon level. Two tiers (baseline + editorial) are sufficient. See canon §8 entry 2026-04-27 for full rationale.

**Mechanical-gate enforcement at commit time.** The pre-commit hook runs `validators/run_all.py --baseline-check` when canon / editorial corpus / validator files are staged; the commit-msg hook runs `check_canon_extensions.py` when canon-extension patterns are present. Both block on regression / unaudited extension. See `CLAUDE.md` Three-Layer Validation Architecture & Mechanical Gates section.

## Build Pipeline (planned)

The cascade rule (once English layer exists): **Hebrew edit → English regen → HTML rebuild**.

For the Hebrew-only MVP: **Hebrew edit → HTML rebuild**.

Pipeline:

```
research/stepbible-tahot/  →  (ingest_tahot.py)
                           →  data/text-files/v0/prose/{NN-book}/{abbr}-{ch}.txt
                              + v0/eng-baseline/, v0/translit-baseline/
                           →  (parse_teamim.py — prose + Sifrei Emet)
                           →  data/text-files/v1/he-baseline/{NN-book}/{abbr}-{ch}.txt
                              + v1/eng-interlinear/, v1/eng-gloss/, v1/translit/
                           →  (manual editorial work — three forces + canon rules,
                               consuming validators/{syntax,colometry}/ findings as work queue)
                           →  data/text-files/v2/he/{NN-book}/{abbr}-{ch}.txt
                           ├─→ (propagate_editorial_layers.py — re-segment translit + interlinear)
                           │   →  data/text-files/v2/{eng-interlinear,translit}/{NN-book}/{abbr}-{ch}.txt
                           │
                           └─→ (regenerate_english.py per verse — Wave 6 substrate)
                               via  atu_method.kjv_alignment.align_verse()
                               using  ../atu-method/data/kjv-strongs/MetaV_*.csv (KJV 1769 + Strong's)
                                 +  TAHOT per-Hebrew-token Strong's tags
                               →  data/text-files/v2/eng-gloss/{NN-book}/{abbr}-{ch}.txt

                           →  (build_books.py — cascade picks v2 if present, else v1)
                           →  books/{book}.html (single tree; no parallel KJV/legacy fork post-Wave-6)
                           →  index.html (loads via fetch on demand; 4-layer view + Modern pill)
```

Run scripts with:

```bash
PYTHONIOENCODING=utf-8 py -3 scripts/<script>.py
```

The encoding prefix is mandatory on Windows for any script touching Hebrew Unicode (combining marks, te'amim, niqqud).

## Web App (planned)

`index.html` will mirror the design pattern used in sibling projects (single-file, all CSS/JS inline, hash routing, in-memory book cache, localStorage state) but with the following Hebrew-specific commitments baked in:

- `dir="rtl"` on the Hebrew text container as an HTML attribute, not just CSS
- All Latin-script content (verse numbers, English gloss when present, settings labels) wrapped in `<bdi>` or `<span dir="ltr">` to prevent Bidi reordering
- Mirrored UI layout (nav arrows, gutter, settings panel, progress indicator)
- Three toggles in addition to display-mode: niqqud on/off, te'amim on/off, ketiv-vs-qere
- Hebrew font stack: SBL Hebrew → Ezra SIL → Taamey Frank CLM → system Hebrew fallback
- TaNaK book ordering on the landing-page TOC grid
- URL aliases for Christian book names (`#1sam-15` → `#shmuel-15`)

PWA infrastructure (manifest, service worker, icons) is **not** part of the MVP. Sibling Greek edition shipped without it; Tanakh will match that baseline and revisit later if both projects adopt PWA together.

## Git Workflow

- All work on `main` branch
- Stan pushes from his local machine via GitHub Desktop
- Claude Code prepares commits but cannot push (403 proxy error in this environment)
- Stan's standing instruction: "whenever you finish, do a commit and I'll push"

## Deployment

GitHub Pages from the `main` branch root, with `CNAME` pointing at `tanakh-reader.com`. DNS configuration through Cloudflare (same account that holds the domain). HTTPS enforced.

Pages configuration is **not** yet activated in the repo settings — to be done as part of the MVP-deploy session, once `index.html` and at least one book HTML exist.

---

### Established — 2026-04-25 (scaffolding session)

- Repo skeleton documented; no scripts or text files yet
- Tier system simplified to v0 / v1-he-baseline / v4-editorial; v2 and v3 deferred
- Private folder layout fixed; junction setup documented
- Source-text licensing landscape mapped; TAHOT picked as primary
- Web app design constraints (RTL, font stack, toggle inventory) listed for the eventual web-app session

---

**2026-04-26 update:** v1-teamim directory renamed to v1-he-baseline; path references updated throughout this doc to align with the canon's te'amim-as-evidence framing (no longer te'amim-as-prior).

**2026-04-26 update:** Four-tier pipeline (v0 → v1 → v2 → v3 → v4) documented. v2 and v3 are no longer deferred — they apply the validator infrastructure (Layer 1 syntax + Layer 3 colometry) to the v1-he-baseline mechanically via apply_v2.py and apply_v3.py. Tier-system table, directory tree, and pipeline diagram updated to show `v2-he-syntax/` and `v3-he-colometry/` slots. v4-editorial remains the hand-edited gold standard for REVIEW-REQUIRED items and Category B/C judgment calls.

**2026-04-26 update:** `data/text-files/` restructured into per-tier subfolders (v0/, v1/, v2/, v3/, v4/). Tier-name identity strings (v1-he-baseline, v2-he-syntax, etc.) unchanged; only filesystem layout. Path references in this doc updated to the new layout.

**2026-04-27 update:** Tier collapse — both 2026-04-26 multi-tier updates above are superseded. Pipeline simplified from 5 tiers to **3 tiers** (v0 / v1 / v2). Editorial gold standard moved from `v4/editorial/` to `v2/he/`; parallel per-word layers moved from `v4/{eng-interlinear,eng-gloss,translit}/` to `v2/{eng-interlinear,eng-gloss,translit}/`. The intermediate auto-apply tiers (`v2/he-syntax/` via apply_v2; `v3/he-colometry/` via apply_v3) are retired; `apply_v2.py`, `apply_v3.py`, and `scripts/lib/apply_pipeline.py` removed from `scripts/`. STRONG-tagged validator findings now feed the editorial work queue directly. Build cascade simplified to `v2 → v1`. See canon §8 entry 2026-04-27 for full rationale.

**2026-04-28 update:** Two new validator components added. `validators/colometry/validate_clause_nucleus_split.py` enforces Rule H18 — Clause-Nucleus Integrity (see canon §5 H18); emits REVIEW-REQUIRED findings only (no STRONG tags); not in `ADOPTED_VALIDATORS` pending corpus review. `validators/_shared/poetic_register.py` is a shared helper that detects Sifrei Emet chapters (Psalms, Proverbs, Job 3:1–42:6) for register-aware behavior across validators. Both components registered in `validators/run_all.py` discovery and referenced in CLAUDE.md Key Files table.

**2026-04-28 update (H/E Phase 1):** `index.html` BOOKS registry extended with `hebrew` (Hebrew script name), `transliterated` (Latin transliteration), optional `christianName` (only when it diverges from `name`), and `aliases` (alternate slug forms accepted by the URL hash router). A flat `BOOK_ALIASES` map is built once at load from each book's aliases plus its canonical key; `parseHash()` consults it via the new `resolveBookSlug()` helper, so URLs like `#yonah-1-1`, `#shir-hashirim-2-3`, or `#יונה-1-1` resolve to the canonical English slug. **Canonical-slug invariant:** `setHash()` and `setBookHash()` always emit the canonical English slug (they normalize through `resolveBookSlug` before writing `location.hash`); aliases are read-only inputs accepted by the router, never produced by it. Shared and bookmarked links therefore stabilize on the English form regardless of which tradition's spelling the linker typed.
