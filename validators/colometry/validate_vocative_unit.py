#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Rule H4 — Vocative Handling (Hebrew).

Rule H4 (canon §5 H4; Layer 3 editorial rule):
Hebrew lacks a morphological vocative case. Direct address is marked by:
  - Sentence-initial address particle (הוֹי, אוֹי, אֲהָהּ, אָנָּא)
  - Article-marked NP in address position
  - Bare NP in address position with 2p verbal morphology
  - Proper name in address position
  - Compound divine-title address (יְהוָה אֱלֹהֵי הַשָּׁמַיִם)

VIOLATION PATTERN — Vocative Unit Split:
  An address-particle-introduced vocative NP is split across a line break.
  Specifically: line N ends with an address particle (or is just the particle),
  and line N+1 begins with the vocative NP head.

  Example violation:
    הוֹי
    אַבְרָהָם

  Should be merged:
    הוֹי אַבְרָהָם

DETECTION:
  1. Line N ends with an address particle skeleton (after stripping niqqud + te'amim)
  2. Line N+1 begins with a likely vocative NP head (heuristic: article-marked noun,
     proper name, or bare noun that could be vocative)
  3. No sof-pasuq on line N (clause-boundary guard)

ADDRESS PARTICLE SKELETONS (consonants only):
  - הוי    "woe/behold" (הוֹי)
  - אוי    "alas" (אוֹי)
  - אהה    "ah" (אֲהָהּ)
  - אנא    "please" (אָנָּא)

Layer classification: This is a Layer 3 editorial rule violation (syntactic integrity —
multi-word vocative units must stay whole). Emit [REQUIRED-MERGE] severity.

Output format:
    [REQUIRED-MERGE]  file:line_number  H4/vocative-unit-split  ADDRESS_PARTICLE  brief description

Exit code: 0 if zero violations, 1 if violations found, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_vocative_unit.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_vocative_unit.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_vocative_unit.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_vocative_unit.py --json
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_vocative_unit.py --verbose
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "he"

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers
# ---------------------------------------------------------------------------

# Sof pasuq glyph (U+05C3 ׃)
SOF_PASUQ = "׃"

# Maqqef glyph (U+05BE ־)
MAQQEF = "־"

# Hebrew points range U+0591–U+05C7: cantillation accents + niqqud vowels
HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")


def strip_points(token: str) -> str:
    """Return token with all niqqud and te'amim stripped (consonant skeleton only)."""
    return HEBREW_POINTS_RE.sub("", token)


# ---------------------------------------------------------------------------
# Address-particle skeleton set
# ---------------------------------------------------------------------------

ADDRESS_PARTICLE_SKELETONS: set[str] = {
    "הוי",    # הוֹי    "woe / behold"
    "אוי",    # אוֹי    "alas"
    "אהה",    # אֲהָהּ   "ah"
    "אנא",    # אָנָּא   "please"
}

# Punctuation to skip when checking line-end content
PUNCTUATION_SKELETONS: set[str] = {
    "׃",   # sof pasuq
    "׀",   # paseq
    "ס",   # setuma paragraph marker
    "פ",   # petucha paragraph marker
    "",    # empty after stripping
}


def is_punctuation_only(skeleton: str) -> bool:
    """Return True if this token's skeleton is pure punctuation / empty."""
    return skeleton in PUNCTUATION_SKELETONS or skeleton == MAQQEF


# ---------------------------------------------------------------------------
# Vocative-head detection heuristics
# ---------------------------------------------------------------------------

ARTICLE_PREFIX = "ה"  # ה prefix (U+05D4)
PREPOSITION_PREFIXES = {"ב", "כ", "ל", "מ", "ש"}  # Can attach to vocatives


def looks_like_vocative_head(skeleton: str) -> bool:
    """Heuristic: does this token skeleton look like a vocative NP head?

    Vocative heads are typically:
      - Article-marked nouns (הַ-prefix): הַמֶּלֶךְ, הָאֱלֹהִים
      - Proper names (uppercase/capitalized, or known names)
      - Bare nouns in address position (harder to detect without context)
      - Pronouns or kinship terms

    This is a heuristic; false negatives are acceptable (missing some vocatives
    is better than false positives). We prioritize article-marked + proper names.
    """

    if not skeleton:
        return False

    # Article prefix (ה)
    if skeleton.startswith(ARTICLE_PREFIX) and len(skeleton) > 1:
        # Common: הַמֶּלֶךְ, הָאֱלֹהִים, הַשָּׁמַיִם
        return True

    # Proper names — common biblical names (partial list for heuristic)
    # These are vocative-common: personal names, place names
    proper_names = {
        "אברהם", "אברם", "יצחק", "יעקב", "יוסף", "משה", "דוד",
        "שלמה", "אליה", "ישראל", "עלי", "שמואל", "שאול",
        "יוחנן", "יהודה", "בנימין", "יוסף", "סימון", "פטר",
        "מרים", "חוה", "שרה", "רבקה", "לאה", "רחל",
        "יהוה", "אלהים", "יהוה", "אדנ", "אל", "צור",
    }
    if skeleton in proper_names:
        return True

    # Kinship/relationship terms (common in vocatives)
    kinship = {
        "אב", "אם", "בן", "בת", "אח", "אחות",
        "דוד", "דודה", "מלך", "מלכה", "כוהן", "נביא",
    }
    if skeleton in kinship:
        return True

    # Pronouns — less common as standalone vocatives but possible
    # Skip for now to reduce false positives

    return False


# ---------------------------------------------------------------------------
# Line helpers
# ---------------------------------------------------------------------------

def is_skippable(line: str) -> bool:
    """Return True for blank lines and verse-reference-only lines."""
    s = line.strip()
    if not s:
        return True
    # Verse reference lines: e.g. "1:1" or "Genesis 1:1"
    if re.match(r"^(\w+\s+)?\d+:\d+$", s):
        return True
    return False


def last_content_token(line: str) -> str | None:
    """Return the skeleton of the last non-punctuation, non-empty token on the line.

    Iterates from the end of the whitespace-split token list, stripping
    points from each token, until a non-punctuation skeleton is found.
    Returns None if all tokens are punctuation or the line is empty.
    """
    tokens = line.rstrip().split()
    for tok in reversed(tokens):
        skel = strip_points(tok)
        if not is_punctuation_only(skel):
            return skel
    return None


def first_content_token(line: str) -> str | None:
    """Return the skeleton of the first non-punctuation, non-empty token on the line."""
    tokens = line.lstrip().split()
    for tok in tokens:
        skel = strip_points(tok)
        if not is_punctuation_only(skel):
            return skel
    return None


def line_ends_at_clause_boundary(line: str) -> bool:
    """Return True if the last non-whitespace CHARACTER of the line is sof-pasuq."""
    stripped = line.rstrip()
    if not stripped:
        return False
    return stripped[-1] == SOF_PASUQ


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    """Scan one text file for Rule H4 vocative-unit-split violations."""
    violations: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        line_no = i + 1  # 1-based

        # Guard: if this line ends at a clause boundary (sof-pasuq),
        # and an address particle appears there, it's a different editorial
        # question (address particle at clause end). Skip for now.
        if line_ends_at_clause_boundary(line):
            continue

        # Check if this line ends with an address particle
        last_tok = last_content_token(line)
        if last_tok is None:
            continue

        if last_tok not in ADDRESS_PARTICLE_SKELETONS:
            continue

        # This line ends with an address particle.
        # Now check if the next non-empty content line starts with a vocative NP head.
        next_content = ""
        next_content_line_num: int | None = None
        first_tok_next = None

        for j in range(i + 1, len(lines)):
            if not is_skippable(lines[j]):
                next_content = lines[j].strip()
                next_content_line_num = j + 1  # 1-based
                first_tok_next = first_content_token(lines[j])
                break

        # If there is no next content line, no violation (particle at EOF).
        if not next_content or first_tok_next is None:
            continue

        # Check if the next line's first token looks like a vocative head.
        if not looks_like_vocative_head(first_tok_next):
            continue

        # Violation found: address particle on line N, vocative head on line N+1.
        violations.append({
            "file": path.name,
            "file_path": path,
            "line_num": line_no,
            "rule": "H4/vocative-unit-split",
            "severity": "STRONG-MERGE-CANDIDATE",
            "particle_skeleton": last_tok,
            "vocative_head_skeleton": first_tok_next,
            "brief": (
                f"address particle ‫{last_tok}‬ separated from vocative NP head ‫{first_tok_next}‬; "
                f"merge onto next line to keep vocative unit whole"
            ),
            "line": line.rstrip(),
            "next_line": next_content,
            "next_line_num": next_content_line_num,
        })

    return violations


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--book",
        metavar="BOOK",
        help="Restrict scan to one book folder name (e.g. 'genesis'). "
             "Default: all books in the target directory.",
    )
    parser.add_argument(
        "--v2",
        action="store_true",
        help="Scan v2/he (post-syntax-pass tier) instead of v1/he-baseline.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show next-line context for each violation.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as a single JSON document to STDOUT instead of "
             "human-readable lines.",
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
            print(
                f"ERROR: book directory not found: {book_dir}",
                file=sys.stderr,
            )
            sys.exit(2)
        files = sorted(book_dir.glob("*.txt"))
    else:
        files = sorted(base_dir.rglob("*.txt"))

    if not files:
        print(f"No .txt files found under {base_dir}", file=sys.stderr)
        sys.exit(2)

    all_violations: list[dict] = []
    for path in files:
        all_violations.extend(scan_file(path, verbose=args.verbose))

    exit_code = 1 if all_violations else 0

    # --- JSON output mode ---
    if args.json:
        findings = []
        for v in all_violations:
            findings.append({
                "file": str(v["file_path"].relative_to(REPO_ROOT)).replace("\\", "/"),
                "line": v["line_num"],
                "severity": "STRONG-MERGE-CANDIDATE",
                "tag": v["severity"],
                "rule_id": "H4",
                "rule_short": "Vocative Unit Split",
                "brief": v["brief"],
                "particle": v["particle_skeleton"],
                "vocative_head": v["vocative_head_skeleton"],
                "next_line": v.get("next_line_num"),
                "applied_action": "merge_with_next",
            })

        by_severity: dict[str, int] = {}
        by_tag: dict[str, int] = {}
        for f in findings:
            by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1
            by_tag[f["tag"]] = by_tag.get(f["tag"], 0) + 1

        doc = {
            "validator": "validate_vocative_unit",
            "rule": "Layer 3 colometry — Rule H4",
            "layer": 3,
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
    print(f"Rule H4 Vocative Unit Split validator — Tanakh {tier_label}")
    print(
        "Address particles: הוֹי אוֹי אֲהָהּ אָנָּא"
    )
    print("Reference: canon §5 H4 — vocative units stay whole")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Violations    : {len(all_violations)}")

    # Severity summary
    by_sev_human: dict[str, int] = {}
    for v in all_violations:
        by_sev_human[v["severity"]] = by_sev_human.get(v["severity"], 0) + 1
    if by_sev_human:
        print()
        for sev, count in sorted(by_sev_human.items()):
            print(f"  {sev}: {count}")
    print()

    if all_violations:
        for v in all_violations:
            print(
                f"[STRONG-MERGE-CANDIDATE]  {v['file']}:{v['line_num']}  "
                f"{v['rule']}  {v['severity']}  {v['brief']}"
            )
            print(f"    {v['line'][:120]}")
            if args.verbose and v.get("next_line"):
                print(f"    → {v['next_line'][:120]}")
            print()
    else:
        print(
            "No violations found. Rule H4 vocative-unit integrity is clean."
        )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
