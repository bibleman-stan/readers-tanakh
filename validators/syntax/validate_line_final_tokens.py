#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate Layer 1 line-final token rules across the Tanakh v1-he-baseline corpus.

Checks six REQUIRED-MERGE patterns from data/syntax-reference/hebrew-break-legality.md.
Each is a hard grammatical failure — a break here violates generic Hebrew syntax
regardless of editorial policy:

  - Maqqef glyph (U+05BE ־) at line end: the maqqef-group continues on the
    next line, which violates Rule H1 (canon §5 H1; Joüon-Muraoka §13).

  - Conjunction-prefix וְ / וַ / וּ stranded at line end: the conjunction leads
    its content; stranding it alone is illegal (hebrew-break-legality.md row 2).

  - Prepositional prefix מ / ב / כ / ל stranded from its object at line end:
    prefixed prepositions are proclitics; they cannot stand alone
    (Joüon-Muraoka §103).

  - Definite article הַ / הָ / הֶ stranded from its noun at line end:
    the article is a proclitic; it cannot stand alone (Joüon-Muraoka §137).

  - Direct-object marker אֵת / אֶת stranded from its object at line end:
    (Joüon-Muraoka §125).

  - Negation לֹא / אַל / אַיִן stranded from the negated word at line end:
    (Joüon-Muraoka §160).

Output format:
    [MALFORMED]  file:line_number  rule  brief description

Exit code: 0 if zero violations, 1 if violations found, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/syntax/validate_line_final_tokens.py
    PYTHONIOENCODING=utf-8 py -3 validators/syntax/validate_line_final_tokens.py --book jonah
    PYTHONIOENCODING=utf-8 py -3 validators/syntax/validate_line_final_tokens.py --v4
"""

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants — use v1-he-baseline (renamed path; not v1-teamim)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1-he-baseline"
V4_DIR = REPO_ROOT / "data" / "text-files" / "v4-editorial"

# ---------------------------------------------------------------------------
# Hebrew Unicode constants
# ---------------------------------------------------------------------------

# Maqqef glyph U+05BE
MAQQEF = "־"

# Niqqud / cantillation marks to strip when isolating consonant skeleton
# U+0591–U+05C7: Hebrew cantillation and points
HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")


def strip_points(token: str) -> str:
    """Return token with niqqud and te'amim stripped (consonants + maqqef only)."""
    return HEBREW_POINTS_RE.sub("", token)


# ---------------------------------------------------------------------------
# Line-final token detectors
# Each returns a (rule_tag, brief) tuple or None.
# ---------------------------------------------------------------------------

def check_line_final_maqqef(line: str):
    """Maqqef at line end → maqqef-group split across lines (Rule H1)."""
    stripped = line.rstrip()
    if not stripped:
        return None
    # Last character (after stripping trailing whitespace) is maqqef
    # The maqqef may be followed only by whitespace, which we've stripped.
    last_char = stripped[-1]
    if last_char == MAQQEF:
        return ("H1/maqqef", "line-final maqqef ־ — maqqef-group split across lines")
    return None


# Conjunction prefixes in isolation or attached to next word.
# In v1-he-baseline lines, a stranded conjunction prefix will appear as a
# standalone token at line end: וְ, וַ, וּ (with or without following niqqud
# on the same character — but by definition it's stranded if it's the only
# token on the line or the last token with nothing following it).
# We detect the consonant ו followed optionally by a vowel mark and nothing else
# in the last whitespace-delimited token.
#
# Pattern: last token stripped of points is just ו (one consonant).
CONJUNCTION_RE = re.compile(r"^ו$")  # ו alone after stripping points


def check_stranded_conjunction(line: str):
    """Conjunction prefix וְ/וַ/וּ stranded at line end (break-legality row 2)."""
    token = _last_token(line)
    if token is None:
        return None
    bare = strip_points(token)
    if CONJUNCTION_RE.match(bare):
        return ("L1/conjunction", "stranded conjunction prefix וְ/וַ/וּ at line end")
    return None


# Prepositional prefixes: מ ב כ ל — when the entire last token consists of
# just one of these consonants (plus optional points), it is a stranded prefix.
PREP_PREFIX_RE = re.compile(r"^[מבכל]$")  # מ ב כ ל


def check_stranded_prep_prefix(line: str):
    """Prep prefix מ/ב/כ/ל stranded from object at line end (break-legality row 3)."""
    token = _last_token(line)
    if token is None:
        return None
    bare = strip_points(token)
    if PREP_PREFIX_RE.match(bare):
        return ("L1/prep-prefix", f"stranded prepositional prefix at line end: {token!r}")
    return None


# Definite article: הַ/הָ/הֶ — bare ה at line end.
ARTICLE_RE = re.compile(r"^ה$")  # ה alone after stripping points


def check_stranded_article(line: str):
    """Definite article הַ stranded from noun at line end (break-legality row 4)."""
    token = _last_token(line)
    if token is None:
        return None
    bare = strip_points(token)
    if ARTICLE_RE.match(bare):
        return ("L1/article", "stranded definite article הַ at line end")
    return None


# Direct-object marker: אֵת / אֶת (also אֹת- in construct, but the isolated
# form is the check target here). Consonant skeleton: את.
DOT_MARKER_RE = re.compile(r"^את$")  # את


def check_stranded_dot_marker(line: str):
    """Direct-object marker אֵת stranded from object at line end (break-legality row 5)."""
    token = _last_token(line)
    if token is None:
        return None
    bare = strip_points(token)
    if DOT_MARKER_RE.match(bare):
        return ("L1/dot-marker", "stranded direct-object marker אֵת at line end")
    return None


# Negation particles: לֹא (לא), אַל (אל), אַיִן (אין).
# Stripped consonant skeletons.
NEGATION_RE = re.compile(r"^(לא|אל|אין)$")  # לא | אל | אין


def check_stranded_negation(line: str):
    """Negation לֹא/אַל/אַיִן stranded from negated word at line end (break-legality row 8)."""
    token = _last_token(line)
    if token is None:
        return None
    bare = strip_points(token)
    if NEGATION_RE.match(bare):
        return ("L1/negation", f"stranded negation particle at line end: {token!r}")
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _last_token(line: str):
    """Return the last whitespace-delimited token of `line`, or None if empty."""
    tokens = line.rstrip().split()
    if not tokens:
        return None
    return tokens[-1]


def is_skippable(line: str) -> bool:
    """Return True for blank lines and verse-reference-only lines."""
    s = line.strip()
    if not s:
        return True
    # Verse reference lines: e.g. "1:1" or "Jonah 1:1"
    if re.match(r"^(\w+\s+)?\d+:\d+$", s):
        return True
    return False


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

CHECKS = [
    check_line_final_maqqef,
    check_stranded_conjunction,
    check_stranded_prep_prefix,
    check_stranded_article,
    check_stranded_dot_marker,
    check_stranded_negation,
]


def scan_file(path: Path) -> list[dict]:
    """Scan one text file for Layer 1 line-final token violations."""
    violations = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    for i, line in enumerate(lines, start=1):
        if is_skippable(line):
            continue
        # Peek at next line to detect cross-line continuation context
        next_line = lines[i] if i < len(lines) else ""  # i is already 1-based; lines is 0-based
        # next line index in 0-based list is i (because enumerate starts at 1 so i-1 is current)
        for check_fn in CHECKS:
            result = check_fn(line)
            if result:
                rule_tag, brief = result
                violations.append(
                    {
                        "file": path.name,
                        "line_num": i,
                        "rule": rule_tag,
                        "brief": brief,
                        "line": line.rstrip(),
                    }
                )
    return violations


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--book",
        metavar="BOOK",
        help="Restrict scan to one book folder name (e.g. 'jonah', 'genesis'). "
             "Default: all books in the target directory.",
    )
    parser.add_argument(
        "--v4",
        action="store_true",
        help="Scan v4-editorial files instead of v1-he-baseline.",
    )
    args = parser.parse_args()

    base_dir = V4_DIR if args.v4 else V1_DIR
    tier_label = "v4-editorial" if args.v4 else "v1-he-baseline"

    if not base_dir.exists():
        print(
            f"ERROR: {base_dir} not found. "
            f"Run the ingest/baseline scripts first.",
            file=sys.stderr,
        )
        sys.exit(2)

    # Collect files
    if args.book:
        book_dir = base_dir / args.book
        if not book_dir.exists():
            print(f"ERROR: book directory not found: {book_dir}", file=sys.stderr)
            sys.exit(2)
        files = sorted(book_dir.glob("*.txt"))
    else:
        files = sorted(base_dir.rglob("*.txt"))

    if not files:
        print(f"No .txt files found under {base_dir}", file=sys.stderr)
        sys.exit(2)

    all_violations: list[dict] = []
    for path in files:
        all_violations.extend(scan_file(path))

    # Report
    print("=" * 72)
    print(f"Layer 1 line-final token validator — Tanakh {tier_label} corpus")
    print("Covers: maqqef, conjunction-prefix, prep-prefix, article, obj-marker, negation")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Violations    : {len(all_violations)}")
    print()

    if all_violations:
        for v in all_violations:
            print(f"[MALFORMED]  {v['file']}:{v['line_num']}  {v['rule']}  {v['brief']}")
            print(f"    {v['line'][:120]}")
            print()
    else:
        print("No violations found. Layer 1 line-final token rules are clean.")

    sys.exit(1 if all_violations else 0)


if __name__ == "__main__":
    main()
