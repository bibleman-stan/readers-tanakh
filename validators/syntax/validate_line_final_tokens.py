#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate Layer 1 line-final token rules across the Tanakh corpus.

Default scan target: v1/he-baseline (the te'amim-driven machine baseline).
With --v2, scans v2/he (the editorial gold standard).

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
    PYTHONIOENCODING=utf-8 py -3 validators/syntax/validate_line_final_tokens.py --v2
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants — collapsed two-tier layout: v1/he-baseline + v2/he
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "he"

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
# In v1/he-baseline lines, a stranded conjunction prefix will appear as a
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

# Compound prepositions (multi-character orthographic words) that must govern
# an object on the SAME line — if they appear as the last token on a line their
# object is stranded on the next line.  Consonant skeletons after point-stripping.
COMPOUND_PREP_SKELETONS = {
    "מלפני",    # מִלִּפְנֵי — from before (מן + לפני)
    "מפני",     # מִפְּנֵי  — from before / because of
    "לפני",     # לִפְנֵי  — before / in front of
    "אחרי",     # אַחֲרֵי  — after / behind
    "מאחרי",    # מֵאַחֲרֵי — from behind
    "אצל",      # אֵצֶל   — beside / next to
    "בתוך",     # בְּתוֹךְ — in the midst of / within
    "מתוך",     # מִתּוֹךְ — from the midst of
    "בקרב",     # בְּקֶרֶב — in the midst of
    "בעבר",     # בְּעֵבֶר — across / beyond
    "מעל",      # מֵעַל   — from upon / above
    "מתחת",     # מִתַּחַת — from under / beneath
    "סביב",     # סָבִיב  — around / surrounding
    "נגד",      # נֶגֶד   — before / opposite
    "מנגד",     # מִנֶּגֶד — from opposite / in front of
    "בלתי",     # בִּלְתִּי — without / except
    "תחת",      # תַּחַת  — under / instead of
    "עד",       # עַד     — until / as far as (common preposition governing next noun)
    "על",       # עַל    — upon / over (standalone prep token)
    "אל",       # אֶל    — to / toward (standalone prep token)
    "בין",      # בֵּין  — between
    "מבין",     # מִבֵּין — from between
}


def check_stranded_prep_prefix(line: str):
    """Prep prefix מ/ב/כ/ל stranded from object at line end (break-legality row 3).

    Also catches compound (multi-character) prepositions stranded from their object
    at line end — e.g. מִלִּפְנֵי / לִפְנֵי / מֵעַל etc. (Bug 4 fix).
    """
    token = _last_token(line)
    if token is None:
        return None
    bare = strip_points(token)
    if PREP_PREFIX_RE.match(bare):
        return ("L1/prep-prefix", f"stranded prepositional prefix at line end: {token!r}")
    if bare in COMPOUND_PREP_SKELETONS:
        # False-positive guard 1: if the token ends with sof pasuq (׃) the
        # preposition is verse-final and self-contained (e.g. לְפָנַי׃ — "before
        # me" with pronominal suffix as object).  Not stranded.
        if "׃" in token:
            return None
        # False-positive guard 2: if the stripped skeleton is LONGER than the
        # base skeleton entry, the extra consonants are a pronominal suffix
        # (יוֹ, כָה, נוּ, etc.) — the object is the suffix, not the next line.
        # We detect this by checking known suffixed expansions: if bare == key
        # exactly, it's bare construct form (potentially stranded).  If bare
        # starts with the key but has extra consonants appended, it has a suffix.
        # Since the set stores exact skeletons, `bare in COMPOUND_PREP_SKELETONS`
        # means an EXACT match — already bare construct.  So sof-pasuq guard
        # above is the primary control; suffix guard is belt-and-suspenders:
        # mark stranded only if next line exists (caller handles this).
        return ("L1/compound-prep", f"stranded compound preposition at line end: {token!r}")
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

SOF_PASUQ = "׃"  # ׃ — verse-final marker; a line ending with sof pasuq cannot
                      # contain a stranded proclitic (the verse is complete).


def _last_token(line: str):
    """Return the last whitespace-delimited token of `line`, or None if empty.

    Returns None if the last token ends with the sof pasuq glyph (U+05C3 ׃)
    — a verse-final line cannot contain a stranded proclitic by definition.
    This guards against false positives where verse-final divine names (אֵֽל׃),
    pronouns (אָֽתְּ׃), and existential particles (אָֽיִן׃) match the bare-
    consonant patterns for negation (אל) or object marker (את) after
    niqqud-stripping removes the sof pasuq from the comparison string.
    """
    tokens = line.rstrip().split()
    if not tokens:
        return None
    last = tokens[-1]
    if SOF_PASUQ in last:
        return None
    return last


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

# ---------------------------------------------------------------------------
# Rule metadata for JSON output
# Maps rule_tag → (rule_id, rule_short)
# All Layer 1 findings are STRONG-MERGE-CANDIDATE / merge_with_next per spec.
# ---------------------------------------------------------------------------
RULE_META: dict[str, tuple[str, str]] = {
    "H1/maqqef":         ("L1.1", "line-final maqqef — maqqef-group split"),
    "L1/conjunction":    ("L1.2", "stranded conjunction prefix"),
    "L1/prep-prefix":    ("L1.3", "stranded prepositional prefix"),
    "L1/compound-prep":  ("L1.3b", "stranded compound preposition"),
    "L1/article":        ("L1.4", "stranded definite article"),
    "L1/dot-marker":     ("L1.5", "stranded direct-object marker"),
    "L1/negation":       ("L1.6", "stranded negation particle"),
}


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
        # i is already 1-based; lines is 0-based, so lines[i] is the next line
        next_line = lines[i] if i < len(lines) else ""
        next_line_num = i + 1 if i < len(lines) else None
        for check_fn in CHECKS:
            result = check_fn(line)
            if result:
                rule_tag, brief = result
                violations.append(
                    {
                        "file": path.name,
                        "file_path": path,
                        "line_num": i,
                        "rule": rule_tag,
                        "brief": brief,
                        "line": line.rstrip(),
                        "next_line_num": next_line_num,
                        "next_line": next_line.rstrip(),
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
        "--v2",
        action="store_true",
        help="Scan v2/he (editorial gold standard) instead of v1/he-baseline.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as a single JSON document to STDOUT instead of human-readable lines.",
    )
    args = parser.parse_args()

    base_dir = V2_DIR if args.v2 else V1_DIR
    tier_label = "v2/he" if args.v2 else "v1/he-baseline"

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

    exit_code = 1 if all_violations else 0

    # --- JSON output mode ---
    if args.json:
        findings = []
        for v in all_violations:
            rule_tag = v["rule"]
            rule_id, rule_short = RULE_META.get(rule_tag, (rule_tag, rule_tag))
            findings.append({
                "file": str(v["file_path"].relative_to(REPO_ROOT)).replace("\\", "/"),
                "line": v["line_num"],
                "severity": "MALFORMED",
                "tag": "STRONG-MERGE-CANDIDATE",
                "rule_id": rule_id,
                "rule_short": rule_short,
                "brief": v["brief"],
                "next_line": v.get("next_line_num"),
                "applied_action": "merge_with_next",
            })

        by_severity: dict[str, int] = {}
        by_tag: dict[str, int] = {}
        for f in findings:
            by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1
            by_tag[f["tag"]] = by_tag.get(f["tag"], 0) + 1

        doc = {
            "validator": "validate_line_final_tokens",
            "rule": "Layer 1 break-legality",
            "layer": 1,
            "book": args.book or "all",
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": findings,
            "summary": {
                "total_findings": len(findings),
                "by_severity": by_severity,
                "by_tag": by_tag,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output (default) ---
    print("=" * 72)
    print(f"Layer 1 line-final token validator — Tanakh {tier_label} corpus")
    print("Covers: maqqef, conjunction-prefix, prep-prefix, compound-prep, article, obj-marker, negation")
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

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
