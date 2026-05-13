#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate oath formula integrity — frozen unit cohesion.

Pattern: Oath formulas (חַי־יְהוָה, חַי־אָנִי, חַי־פַרְעֹה) are
grammatically frozen units and should not be split from their asseveration
content. The v1-he-baseline frequently splits the formula skeleton (oath
particle + divine name/pronoun/royal title) from the asseveration (אִם /
אִם לֹא ... clause), placing them on separate lines.

TRIGGER:
Line ends with oath formula skeleton (חַי + maqqef + divine name / pronoun /
royal title); next line begins with asseveration content (אִם / אִם לֹא
Hebrew oath idioms, or continuation of oath semantics).

SEVERITY:
STRONG-MERGE-CANDIDATE — oath formulas are frozen units with no optional
overrides (per canon §5 M4).

ARCHITECTURAL CONSTRAINT — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. The te'amim
Unicode range (U+0591–U+05AF) does NOT appear in any predicate that decides
whether to fire a finding. Te'amim MAY appear in finding annotations as
informational defensibility-capture (Rule H8) — the trigger must remain
syntactic.

FORCED-NO-MERGE GUARDS (skip BEFORE emitting):
  1. Poetic register skip — SUPERSEDED 2026-05-04 methodology audit.
     Oath formulas appear in poetry; poetic register is calibration, not
     authorization. Three editorial criteria (atomic thought, single image,
     Hebrew syntax) adjudicate all registers uniformly.
  2. Oath formula is interior to a larger construct-chain NP (rare but
     possible in complex titles; skip to avoid false positives).
  3. Asseveration is pure interrogative or rhetorical (אִם־כֵּן, אִם־לֹא,
     אִם־כָּל) without a following consequence clause (isolated oath → skip).

Output format:
    [DEVIATION]  file:line  M4/oath-formula-split  STRONG-MERGE-CANDIDATE  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_oath_formula.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_oath_formula.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_oath_formula.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_oath_formula.py --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants — two-tier layout: v1/he-baseline + v2/heb
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files"  / "v2" / "heb"

# Make _shared importable when this script is run as __main__.
sys.path.insert(0, str(REPO_ROOT / "validators"))
from _shared.poetic_register import is_poetic_register  # noqa: E402
from _shared import morphology as M  # noqa: E402
from _shared import morph_alignment as MA  # noqa: E402

# ---------------------------------------------------------------------------
# Unicode constants — sourced from shared helpers
# ---------------------------------------------------------------------------
SOF_PASUQ = M.SOF_PASUQ
MAQQEF = M.MAQQEF


def strip_points(token: str) -> str:
    """Strip niqqud and te'amim, preserving maqqef/paseq/sof-pasuq.

    Delegates to M.strip_apparatus (shared helper).
    """
    return M.strip_apparatus(token)


# ---------------------------------------------------------------------------
# Verse-reference / blank line handling
# ---------------------------------------------------------------------------

VERSE_REF_RE = re.compile(r"^(\S+\s+)?\d+:\d+\s*$")


def is_skippable(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    if VERSE_REF_RE.match(s):
        return True
    return False


def parse_verse_ref(line: str):
    """If `line` is a 'C:V' verse-reference line, return (chapter, verse). Else None."""
    s = line.strip()
    m = re.match(r"^(?:\S+\s+)?(\d+):(\d+)\s*$", s)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


# ---------------------------------------------------------------------------
# Chapter / book name extraction from path
# ---------------------------------------------------------------------------

CHAPTER_FILENAME_RE = re.compile(r"-(\d+)\.txt$", re.IGNORECASE)


def book_name_from_path(path: Path) -> str:
    """Return the book directory name (e.g. '01-genesis')."""
    return path.parent.name


def chapter_from_path(path: Path) -> int | None:
    m = CHAPTER_FILENAME_RE.search(path.name)
    if not m:
        return None
    return int(m.group(1))


# ---------------------------------------------------------------------------
# Token helpers — use shared M helpers where available
# ---------------------------------------------------------------------------

def content_tokens(line: str) -> list[str]:
    """Split a line into tokens, dropping pure-sof-pasuq and verse-reference tokens."""
    out = []
    for tok in line.split():
        bare = strip_points(tok)
        if bare in ("", SOF_PASUQ):
            continue
        if re.match(r"^\d+:\d+$", bare):
            continue
        out.append(tok)
    return out


def first_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[0] if toks else None


def last_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[-1] if toks else None


# ---------------------------------------------------------------------------
# Oath formula heuristics
# ---------------------------------------------------------------------------

# Oath formula skeleton patterns (after stripping points).
# Pattern: חַי־<divine name|pronoun|title>
# Common forms:
#   חי־יהוה      (by the life of YHWH)
#   חי־אני       (by my life)
#   חי־נפשך / חי־נפשי / חי־נפשו  (by your/my/his life)
#   חי־פרעה      (by the life of Pharaoh)

OATH_FORMULA_HEADS = {
    "חי",        # oath particle base
}

OATH_DIVINE_NAMES = {
    "יהוה",      # YHWH
    "אלהים",    # God
    "אדני",     # Lord (Adonai)
}

OATH_PRONOUNS_AND_TITLES = {
    "אני",       # I / me
    "נפשך",      # your life
    "נפשי",      # my life
    "נפשו",      # his life
    "נפשה",      # her life
    "נפשם",      # their (m) life
    "נפשן",      # their (f) life
    "פרעה",      # Pharaoh
    "מלך",       # king (generic title)
}

# Asseveration opening patterns (positive and negative Hebrew oath idioms)
# Pattern: אִם or אִם לֹא (if [not] ... ) marking the consequence clause
ASSEVERATION_OPENERS = {
    "אם",        # if (positive oath)
    "אם־לא",     # if not (negative oath)
    "אם־כי",     # if surely (emphatic)
    "אם־כן",     # if so (consequence marker)
}

# Additional oath-continuation markers (when no explicit אִם present)
OATH_CONTINUATION_MARKERS = {
    "כי",        # surely (strengthens oath)
    "נאם",       # says (oracle formula paired with oath)
}


def is_oath_formula_skeleton(token: str) -> bool:
    """Check if token is an oath formula: חַי־<name/pronoun/title>."""
    bare = strip_points(token).rstrip(SOF_PASUQ)
    if not bare:
        return False

    # Must contain maqqef (חי־...)
    if MAQQEF not in bare:
        return False

    parts = bare.split(MAQQEF)
    if len(parts) < 2:
        return False

    head = parts[0]
    obj = MAQQEF.join(parts[1:])  # Rejoin in case of multiple maqqefs

    # Head must be oath particle
    if head != "חי":
        return False

    # Object must be divine name, pronoun, or title
    if obj in OATH_DIVINE_NAMES or obj in OATH_PRONOUNS_AND_TITLES:
        return True

    return False


def line_ends_with_oath_formula(line: str) -> bool:
    """True if any content token on the line is an oath formula skeleton.

    We check all tokens, not just the last, because the oath formula might be
    followed by other elements like sof pasuq or other punctuation. The key
    test is whether the line CONTAINS an oath formula, which marks it as the
    beginning of an oath unit.
    """
    for tok in content_tokens(line):
        if is_oath_formula_skeleton(tok):
            return True
    return False


def line_starts_with_asseveration(line: str) -> bool:
    """True if the line begins with an asseveration opener (אִם / אִם לֹא) or related marker."""
    first = first_content_token(line)
    if not first:
        return False
    bare = strip_points(first)

    # Direct match
    if bare in ASSEVERATION_OPENERS:
        return True

    # Handle compound with maqqef
    if MAQQEF in bare:
        head = bare.split(MAQQEF, 1)[0]
        if head in ASSEVERATION_OPENERS:
            return True

    # Continuation markers (כי, נאם) — stricter, only after proven oath formula
    if bare in OATH_CONTINUATION_MARKERS:
        return True

    return False


# ---------------------------------------------------------------------------
# Verse partitioning
# ---------------------------------------------------------------------------

def partition_into_verses(lines: list[str]) -> list[tuple[int | None, int | None, list[int]]]:
    """Group line indices by verse.

    Returns a list of (chapter, verse, [line_indices]) tuples in source order.
    Verse-reference lines themselves are included as part of their verse but
    are skippable for content scanning.
    """
    verses: list[tuple[int | None, int | None, list[int]]] = []
    cur_chapter: int | None = None
    cur_verse: int | None = None
    cur_indices: list[int] = []
    for i, line in enumerate(lines):
        ref = parse_verse_ref(line)
        if ref is not None:
            # Flush current
            if cur_indices:
                verses.append((cur_chapter, cur_verse, cur_indices))
            cur_chapter, cur_verse = ref
            cur_indices = []
            continue
        if not line.strip():
            continue
        cur_indices.append(i)
    if cur_indices:
        verses.append((cur_chapter, cur_verse, cur_indices))
    return verses


# ---------------------------------------------------------------------------
# Te'amim annotation helper (informational only — NOT in trigger predicates)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Per-file scanner — tag-aware via morph_alignment (skel fallback automatic)
# ---------------------------------------------------------------------------

def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    findings: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    book = book_name_from_path(path)
    chapter_from_file = chapter_from_path(path)

    # Load TAHOT morph alignment for this chapter (None if morph file absent).
    # The oath formula trigger is purely lexical (frozen form detection), so
    # tag data is loaded for infrastructure completeness and future guards.
    chapter_morph = MA.load_chapter_morph(path)

    verses = partition_into_verses(lines)

    # Build a lookup: line_index → (chapter, verse, position_within_verse)
    line_to_verse: dict[int, tuple[int | None, int | None, int, list[int]]] = {}
    for ch, vs, indices in verses:
        for pos, idx in enumerate(indices):
            line_to_verse[idx] = (ch, vs, pos, indices)

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        # Determine verse context
        v_ctx = line_to_verse.get(i)
        chapter = v_ctx[0] if v_ctx else chapter_from_file
        verse = v_ctx[1] if v_ctx else None
        pos_in_verse = v_ctx[2] if v_ctx else 0
        verse_indices = v_ctx[3] if v_ctx else []

        line_no = i + 1  # 1-based

        # --- Check if line ends with oath formula ---
        if not line_ends_with_oath_formula(line):
            continue

        # --- Find next content line in the SAME verse (no cross-verse fire) ---
        next_idx: int | None = None
        for j in range(i + 1, len(lines)):
            if is_skippable(lines[j]):
                continue
            # Same verse?
            n_ctx = line_to_verse.get(j)
            if v_ctx and n_ctx and (n_ctx[0], n_ctx[1]) != (v_ctx[0], v_ctx[1]):
                break
            next_idx = j
            break
        if next_idx is None:
            continue
        next_line = lines[next_idx]
        next_line_no = next_idx + 1

        # --- Check if next line starts with asseveration ---
        if not line_starts_with_asseveration(next_line):
            continue

        # --- Guard 1: poetic register skip — SUPERSEDED 2026-05-04 methodology audit ---
        # Oath formulas (חַי + divine name) appear in poetry; suppressing them there
        # is calibration override, not editorial adjudication. Removed so that the
        # three criteria (atomic thought, single image, Hebrew syntax) apply uniformly
        # across all registers.  is_poetic_register import retained for other callers.

        # --- Guard 2: isolated asseveration (no consequence clause) ---
        # Skip if next line is ONLY the asseveration opener (אִם, אִם לֹא, etc.)
        # without a consequence clause. These are sometimes standalone oaths.
        next_toks = content_tokens(next_line)
        if next_toks:
            first_bare = strip_points(next_toks[0])
            # If the line starts with asseveration marker and has only 1-2 tokens
            # (just the marker, possibly with a negation), it's likely interrogative
            # or rhetorical without a consequence — risky to merge. Skip.
            if first_bare in ("אם", "אם־לא"):
                if len(next_toks) <= 2:
                    continue

        # --- All guards passed; emit STRONG-MERGE-CANDIDATE finding ---
        prior_text = line.strip()
        next_text = next_line.strip()
        annotation = (
            "Oath formula skeleton (חַי + divine name/pronoun/title) split from asseveration content. "
            "Oath formulas are frozen units (canon §5 M4)."
        )
        suggested = "MERGE candidate per M4"
        brief = f"oath formula split from asseveration — {prior_text} // {next_text}"

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "M4/oath-formula-split",
            "severity": "STRONG-MERGE-CANDIDATE",
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "prior_line": prior_text,
            "next_line": next_text,
            "annotation": annotation,
            "suggested_action": suggested,
            "brief": brief,
        })

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def resolve_book_dir(base_dir: Path, book_arg: str) -> Path:
    """Resolve a --book argument permissively (matches complement_integrity)."""
    direct = base_dir / book_arg
    if direct.exists():
        return direct
    candidates = [d for d in base_dir.iterdir() if d.is_dir() and book_arg.lower() in d.name.lower()]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        print(
            f"ERROR: ambiguous book name {book_arg!r}; "
            f"matches: {[d.name for d in candidates]}",
            file=sys.stderr,
        )
        sys.exit(2)
    print(f"ERROR: book directory not found: {direct}", file=sys.stderr)
    sys.exit(2)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--book", metavar="BOOK", help="Restrict to one book.")
    parser.add_argument("--v2", action="store_true", help="Scan v2/heb (default if v1 missing).")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show context.")
    parser.add_argument("--json", action="store_true", help="Emit JSON document.")
    args = parser.parse_args()

    base_dir = V2_DIR if args.v2 else V1_DIR
    tier_label = "v2/heb" if args.v2 else "v1/he-baseline"
    if not base_dir.exists():
        # Fall back to the other tier rather than failing — v1 may be absent.
        alt = V2_DIR if not args.v2 else V1_DIR
        if alt.exists():
            base_dir = alt
            tier_label = "v2/heb" if alt is V2_DIR else "v1/he-baseline"
        else:
            print(f"ERROR: neither {V1_DIR} nor {V2_DIR} found.", file=sys.stderr)
            sys.exit(2)

    if args.book:
        book_dir = resolve_book_dir(base_dir, args.book)
        files = sorted(book_dir.glob("*.txt"))
    else:
        files = sorted(base_dir.rglob("*.txt"))

    if not files:
        print(f"No .txt files found under {base_dir}", file=sys.stderr)
        sys.exit(2)

    all_findings: list[dict] = []
    for path in files:
        all_findings.extend(scan_file(path, verbose=args.verbose))

    exit_code = 1 if all_findings else 0

    if args.json:
        findings_json = []
        for f in all_findings:
            findings_json.append({
                "file": f["file_rel"],
                "line": f["line_num"],
                "rule": f["rule"],
                "severity": f["severity"],
                "book": f["book"],
                "chapter": f["chapter"],
                "verse": f["verse"],
                "prior_line": f["prior_line"],
                "next_line": f["next_line"],
                "next_line_num": f["next_line_num"],
                "annotation": f["annotation"],
                "suggested_action": f["suggested_action"],
            })

        counts = {"STRONG-MERGE-CANDIDATE": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        doc = {
            "validator": "validate_oath_formula",
            "rule": "M4",
            "version": "1.1.0",
            "layer": 3,
            "book": args.book or "all",
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": findings_json,
            "counts": counts,
            "summary": {
                "total_findings": len(findings_json),
                "by_severity": counts,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output ---
    print("=" * 72)
    print(f"Rule M4 Oath Formula Integrity validator — Tanakh {tier_label}")
    print(f"Reference: canon §5 M4 (oath formula frozen units)")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Findings      : {len(all_findings)}")
    print()

    if all_findings:
        for f in all_findings:
            print(
                f"[DEVIATION]  {f['file_rel']}:{f['line_num']}  "
                f"{f['rule']}  {f['severity']}  {f['brief']}"
            )
            if args.verbose:
                print(f"    {f['prior_line'][:120]}")
                print(f"    → {f['next_line'][:120]}")
                print(f"    {f['annotation']}")
                print()
    else:
        print("No findings. Rule M4 oath formula integrity is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
