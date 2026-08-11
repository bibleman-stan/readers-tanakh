# Colometry Rule Validators

Mechanical 5-machinery/validators for the Tanakh colometry 1-method/canon. Split into two layers
matching the project's theoretical stack per 1-method/canon §6.

## Directory layout

```
5-machinery/validators/
  syntax/      — Layer 1: generic Hebrew grammar checks
  colometry/   — Layer 3: Tanakh-specific editorial rule checks
```

---

## `syntax/` — Layer 1 (generic Hebrew grammar)

These 5-machinery/validators check facts about Hebrew grammar that hold regardless of
Tanakh-specific editorial policy. A failure here is a structural error in the
line break — a hard grammatical violation that any competent Hebrew editor
would flag.

**Reference:** `data/syntax-reference/hebrew-break-legality.md` (10-row first-pass
inventory; expand as break-legality cases surface in editorial work)

**Error class: `[MALFORMED]`** — hard grammatical failure; fix before any
editorial review is meaningful.

| Validator | Rules covered | Notes |
|---|---|---|
| `validate_line_final_tokens.py` | Layer 1 REQUIRED-MERGE patterns: line-final maqqef, stranded וְ, stranded prep prefix (מ/ב/כ/ל), stranded article הַ, stranded אֵת, stranded negation (לֹא/אַל/אַיִן) | Fully mechanical for maqqef and pure-prefix forms; heuristic for negation (some archaic post-positioned uses) |
| `validate_maqqef_integrity.py` | Canon Rule H1 — Maqqef-Group Indivisibility | Scans for maqqef glyph (U+05BE) at line end (the group's members are split across lines) |

**Run:**
```bash
PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/syntax/validate_line_final_tokens.py
PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/syntax/validate_line_final_tokens.py --book jonah
PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/syntax/validate_maqqef_integrity.py
PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/syntax/validate_maqqef_integrity.py --book jonah
```

---

## `colometry/` — Layer 3 (Tanakh-specific editorial rules)

These 5-machinery/validators check whether editorial line-break decisions conform to the
settled rules of the Tanakh colometry 1-method/canon (H1–H17). A failure here is a
policy deviation — the rule says the break should be elsewhere.

**Reference:** `private/01-method/colometry-canon.md` §5

**Error class: `[DEVIATION]`** — editorial policy violation; review before
deciding whether to merge, split, or document an override.

| Validator | Rule | Notes |
|---|---|---|
| `validate_speech_intro_framing.py` | Canon Rule H5 — Direct-Speech Framing Default | Detects לֵאמֹר boundary; counts prosodic words in framing clause; flags short/long boundary cases |
| `validate_construct_chain.py` | Canon Rule H2 — Construct Chain Default | Detects nomen regens in construct state followed by a line break before the nomen rectum; STRONG-MERGE-CANDIDATE for unmodified chains |

**Run:**
```bash
PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_speech_intro_framing.py
PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_speech_intro_framing.py --book jonah
PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_construct_chain.py
PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_construct_chain.py --book jonah
```

---

## Error class distinction

| Tag | Layer | Meaning | Action |
|---|---|---|---|
| `[MALFORMED]` | syntax/ | Hard grammatical failure — line break violates generic Hebrew structural grammar | Fix before editorial review |
| `[DEVIATION]` | colometry/ | Editorial policy violation — break diverges from 1-method/canon rule H1–H17 | Review; document exception or merge/split |
| `STRONG-MERGE-CANDIDATE` | colometry/ | Category A per 1-method/canon §2 — application-ready; merge without per-item review | Apply |
| `STRONG-SPLIT-CANDIDATE` | colometry/ | Category A per 1-method/canon §2 — application-ready; split without per-item review | Apply |
| `REVIEW-REQUIRED` | colometry/ | Category C per 1-method/canon §2 — editorial judgment needed before acting | Per-item editorial decision |

**Validator output is a work queue, not a review queue.** `STRONG-*-CANDIDATE`
tags are application-ready Category A per 1-method/canon §2; only `REVIEW-REQUIRED`
items need per-item editorial judgment (1-method/canon §6 principle, ported from sibling
BoFM 1-method/canon §6).

---

## Exit codes

All 5-machinery/validators use the same convention:

- `0` — zero violations found; corpus is clean for this rule
- `1` — violations found; output lists each with file, line number, tag, and brief
- `2` — setup error (e.g., data directory not found)

---

## Output format

Each violation is one line:

```
[TAG]  file:line_number  rule  brief description
```

Example:
```
[MALFORMED]  jonah-01.txt:14  H1/maqqef  line-final maqqef — group split across lines
[DEVIATION]  jonah-01.txt:3   H5/speech-framing  REVIEW-REQUIRED — boundary case (3 prosodic words)
[DEVIATION]  jonah-01.txt:7   H2/construct  STRONG-MERGE-CANDIDATE — construct chain split at line end
```

---

## File scope

Validators run against:

- `data/text-files/v1/he-baseline/<book>/` — te'amim-driven machine baseline (default scan target)
- `data/text-files/v2/heb/<book>/` — hand-edited Hebrew gold standard (when `--v2` flag is passed)

The `--book` argument accepts the book-folder name (e.g., `jonah`, `genesis`).
Default: all books present in the target directory.

---

## Philosophy

A rule earns a validator when three conditions hold:

1. **Mechanical trigger** — the trigger reduces to morphology, orthography,
   or closed lexical lists. No semantic judgment required at the point of
   detection (judgment happens at REVIEW-REQUIRED output, not at scan time).
2. **Error cost × token frequency** — the rule fires frequently enough that
   systematic drift is possible, and a wrong call is visible.
3. **Systematicity of the failure mode** — violations tend to be systematic
   (same pattern missed across many verses), not idiosyncratic one-offs.

Rules failing condition 1 stay as editorial principles without 5-machinery/validators.
The validator-build exercise is also a canon-pruning exercise: asking "does
this rule earn a validator?" forces "does this rule earn its place?"

---

## Adding a new validator

1. Determine whether the rule is Layer 1 (generic Hebrew grammar) or Layer 3
   (Tanakh-specific editorial policy). Place in the matching subfolder.
2. Name the file `validate_<rule_shortname>.py`.
3. Add a header docstring citing the 1-method/canon rule (e.g., "Validates 1-method/canon Rule H2").
4. Use `argparse` with `--book` parameter (see existing 5-machinery/validators for pattern).
5. Read from `v1/he-baseline/` by default; add `--v2` flag to switch to
   `v2/heb/` when editorial files exist.
6. Output: `[TAG]  file:line  rule  brief` to stdout.
7. Exit 0 (clean) or 1 (violations); exit 2 on setup error.
8. Register in this README table under the correct layer.
9. AST-parse verify before committing:
   ```bash
   PYTHONIOENCODING=utf-8 py -3 -c "import ast; ast.parse(open('5-machinery/validators/<layer>/<filename>.py').read())"
   ```
