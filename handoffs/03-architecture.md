# 03 — Architecture & Build Pipeline

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
      v2/
        he-syntax/                       # Layer 1 syntax pass — STRONG Rule H1/H11 auto-applied
          01-genesis/, 02-exodus/, ...
      v3/
        he-colometry/                    # Layer 3 colometry pass — STRONG Rule H2/H5/H7/H16 auto-applied
          01-genesis/, 02-exodus/, ...
      v4/
        editorial/                       # Hand-edited gold standard (single source of truth)
          01-genesis/, 02-exodus/, ...
        eng-gloss/                       # Structural English glosses (deferred)
          01-genesis/, 02-exodus/, ...
    versification-crosswalk.json         # Hebrew ↔ Christian numbering map (vendored from Sefaria)
    lemma_index.json                     # Searchable Hebrew lemma index (built later)
  books/                                 # Generated HTML fragment files
    genesis.html, exodus.html, ...
  scripts/                               # Build, parse, scan, validate
    ingest_tahot.py                      # TAHOT TSV → v0-prose chapter files (primary path)
    ingest_oshb.py                       # OSHB OSIS → sibling tree (on-demand cross-check)
    ingest_uxlc.py                       # UXLC → sibling tree (on-demand cross-check)
    ingest_mam.py                        # MAM → sibling tree (Aleppo tradition reference)
    diff_sources.py                      # For any verse, show how each vendored source renders it
    parse_teamim_prose.py                # Prose accent parser → v1/he-baseline
    parse_teamim_poetic.py               # Sifrei Emet accent parser → v1/he-baseline
    build_books.py                       # v4/editorial (+ v4/eng-gloss) → books/*.html
    ...
  validators/                            # Layer-1 (syntax) and Layer-3 (colometry) checks
    syntax/                              # Hebrew break-legality rules
    colometry/                           # Methodology rule checks
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

**Constraint:** `data/text-files/v0/prose/` has exactly one source feeding it at any time. Currently that source is TAHOT. Re-picking the primary is an editorial decision (write a different `ingest_*.py`), not an architectural one. The non-primary WLC-derived sources serve as cross-checks via a `scripts/diff_sources.py` tool that surfaces transcription disagreements at the verse level.

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

The pipeline runs v0 → v1 → v2 → v3 → v4. All five tiers are active as of 2026-04-26.

| Tier | Directory | Engine | Status |
|---|---|---|---|
| v0 | `v0/prose/` | `ingest_tahot.py` | Derived from TAHOT — verse-marked, full niqqud, full te'amim, ketiv/qere preserved. **NEVER EDIT.** Reference baseline. |
| v1 | `v1/he-baseline/` | `parse_teamim_prose.py` / `parse_teamim_poetic.py` | Machine-generated Hebrew baseline cola draft. Te'amim-as-evidence starting point; editor's draft, not a normative "version 1." |
| v2 | `v2/he-syntax/` | `apply_v2.py` (consumes `validators/syntax/` JSON output) | Layer 1 break-legality pass. Auto-applies STRONG-tagged candidates from `validate_maqqef_integrity.py` (Rule H1) and `validate_line_final_tokens.py` (stranded prefixes/proclitics). Output: syntactically-clean Hebrew. |
| v3 | `v3/he-colometry/` | `apply_v3.py` (consumes `validators/colometry/` JSON output) | Layer 3 colometry-rule pass. Auto-applies STRONG-tagged candidates from `validate_speech_intro_framing.py` (Rules H5, H16) and `validate_construct_chain.py` (Rules H2 with H7 complement integrity). Output: rule-clean under codified Layer 3 mechanical rules. |
| v4 | `v4/editorial/` | Stan + Claude | Hand-edited gold standard. Single source of truth for the web app. Handles REVIEW-REQUIRED items, Category B/C judgment calls, and the three forces (atomic thought, single image, Hebrew syntax) on whatever the mechanical layers cannot decide. |

**Apply scripts (v2, v3):** `apply_v2.py` and `apply_v3.py` consume the JSON output of their respective validator suites and apply only STRONG-tagged candidates to produce the next tier. REVIEW-REQUIRED items are passed through unchanged, becoming v4 work-queue items. Each apply run produces a unified diff against the previous tier; a sweep-scale of ≥5 instances triggers a canon §7 mandatory audit. The apply scripts are a separate implementation track; the architectural commitment is established here.

**Risk mitigations against the GNT/BoFM 10–12% mechanical-error trap:**
1. Only STRONG-tagged candidates are applied automatically; REVIEW-REQUIRED items stay on the v4 work queue.
2. ≥80% adoption gate per validator before its STRONG output is wired into an apply script (canon §7 proposed-rule adoption protocol).
3. Tier-diff audit gate — every apply run produces a unified diff; sweep-scale ≥5 triggers a canon §7 mandatory audit.

**Why this differs from the GNT/BoFM trap:** v2 and v3 apply only the closed list of mechanical rules (H1, H2, H5, H7, H11, H16). They do not generate breaks from external structural assumptions (syntax trees, rhetorical patterns). Error-rate exposure is bounded by the closed rule set.

## Build Pipeline (planned)

The cascade rule (once English layer exists): **Hebrew edit → English regen → HTML rebuild**.

For the Hebrew-only MVP: **Hebrew edit → HTML rebuild**.

Pipeline:

```
research/stepbible-tahot/  →  (ingest_tahot.py)
                           →  data/text-files/v0/prose/{NN-book}/{abbr}-{ch}.txt
                           →  (parse_teamim_prose.py / parse_teamim_poetic.py)
                           →  data/text-files/v1/he-baseline/{NN-book}/{abbr}-{ch}.txt
                           →  (apply_v2.py ← validators/syntax/ JSON)
                           →  data/text-files/v2/he-syntax/{NN-book}/{abbr}-{ch}.txt
                           →  (apply_v3.py ← validators/colometry/ JSON)
                           →  data/text-files/v3/he-colometry/{NN-book}/{abbr}-{ch}.txt
                           →  (manual editorial work on REVIEW-REQUIRED + judgment calls)
                           →  data/text-files/v4/editorial/{NN-book}/{abbr}-{ch}.txt
                           →  (build_books.py)
                           →  books/{book}.html
                           →  index.html (loads via fetch on demand)
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
