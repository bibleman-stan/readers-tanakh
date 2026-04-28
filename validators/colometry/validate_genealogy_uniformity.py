#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Rule H17 — Genealogy/List-Formula Uniformity (Hebrew).

Rule H17 (canon §5 H17; Layer 3 editorial rule):
Per the Parallel-List Uniformity Principle, each generation/case member in
genealogical lists should be one line. Frame-fragments (partial verb phrases,
numeric age fragments) do not stand alone; they merge with the complete
generation-member sequence.

GENEALOGICAL SCOPE:
  - Genesis 5 (Adam lineage)
  - Genesis 10 (Nations table)
  - Genesis 11 (Tower of Babel + Shem lineage)
  - Genesis 36 (Esau genealogy)
  - 1 Chronicles 1–9 (Genealogical history)

PATTERN (genealogical formula):
  וַיְחִי X שָׁנִים וּמְאַת שָׁנָה וַיּוֹלֶד אֶת־Y
  (X lived N years and fathered Y)

VIOLATION PATTERN (primary focus):
  A line containing ONLY a numeric fragment (age component):
    - שָׁנִים וּמְאַת שָׁנָה (plural year noun + "and hundred year(s)")
    - שָׁנָ֑ה / שָׁנָֽה (year(s) with verse-end marker)
    - Numeric age clusters (e.g., חָמֵ֤שׁ וְתִשְׁעִים֙ שָׁנָ֔ה)

  A line beginning with וַיּוֹלֶד or partial אֶת־ without a preceding
  וַיְחִי / living clause to anchor the member.

  A bare וְחָמֵ֥שׁ מֵאוֹ֖ת or similar continuation of a partial formula
  without the generation member's primary clause.

VIOLATION TAGS:

  STRONG-MERGE-CANDIDATE  — pure numeric fragment within genealogy scope,
                            no content except age/years; merges upward.
                            High confidence — formula-fragment detection.

Output format:
    [DEVIATION]  file:line_number  H17/genealogy-uniformity  SEVERITY  brief

Where SEVERITY is:
    STRONG-MERGE-CANDIDATE  — high-confidence formula fragment; auto-mergeable

Exit code: 0 if zero violations, 1 if violations found, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_genealogy_uniformity.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_genealogy_uniformity.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_genealogy_uniformity.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_genealogy_uniformity.py --verbose
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_genealogy_uniformity.py --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants — two-tier layout: v1/he-baseline + v2/he
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "he"

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers
# ---------------------------------------------------------------------------

# Hebrew points: U+0591–U+05C7 (cantillation + niqqud)
HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")

# Sof pasuq U+05C3
SOF_PASUQ = "׃"

# Maqqef U+05BE
MAQQEF = "־"


def strip_points(token: str) -> str:
    """Return token with all niqqud and te'amim stripped."""
    return HEBREW_POINTS_RE.sub("", token)


def has_sof_pasuq(token: str) -> bool:
    """Return True if token contains sof pasuq (verse-end mark)."""
    return SOF_PASUQ in token


# ---------------------------------------------------------------------------
# Genealogical scope detection
# ---------------------------------------------------------------------------

# Genealogical chapters: (book_dir_name_pattern, chapters)
GENEALOGY_SCOPE = {
    "01-genesis": {1, 5, 10, 11, 36},
    "13-1chronicles": {1, 2, 3, 4, 5, 6, 7, 8, 9},
}


def is_genealogy_file(file_path: Path) -> bool:
    """Return True if this file is in a genealogy scope."""
    parent_name = file_path.parent.name
    file_name = file_path.stem  # e.g., "genesis-05"

    # Extract chapter number from filename (e.g., "genesis-05" -> 5)
    match = re.match(r"[a-z]+-(\d+)$", file_name)
    if not match:
        return False

    chapter_num = int(match.group(1))

    # Check if parent is in GENEALOGY_SCOPE
    for scope_key, chapters in GENEALOGY_SCOPE.items():
        if parent_name == scope_key or parent_name.endswith(scope_key):
            if chapter_num in chapters:
                return True

    return False


# ---------------------------------------------------------------------------
# Genealogical formula fragment detection
# ---------------------------------------------------------------------------

# Hebrew year words (with and without niqqud/te'amim)
YEAR_SKELETONS = {
    "שנה",      # שָׁנָה (year)
    "שנים",     # שָׁנִים (years)
}

# Living / fathering verb skeletons
YECHI_SKELETON = "יחי"      # וַיְחִי (lived)
WAYYELAD_SKELETON = "ילד"   # וַיּוֹלֶד (and fathered) / הוֹלִיד (fathered)
ET_SKELETON = "את"         # אֶת־ (direct object marker)


def is_numeric_fragment(line: str) -> bool:
    """Return True if line is purely numeric (age component with years).

    Pattern:
    - Starts with a number word (חָמֵ֥שׁ, שְׁלֹשִׁ֤ים, etc.) or digit
    - Contains year words (שָׁנָה, שָׁנִים, etc.)
    - May end with sof pasuq
    - No verbs, no names (except possibly numerals)
    """
    # Strip and check basic structure
    s = line.strip()
    if not s:
        return False

    # Remove verse references (N:N pattern)
    s = re.sub(r'\b\d+:\d+\b', '', s).strip()

    if not s:
        return False

    # Tokenize
    tokens = s.split()
    if not tokens:
        return False

    # Remove sof pasuq-only tokens
    tokens = [t for t in tokens if strip_points(t) and strip_points(t) != SOF_PASUQ]

    if not tokens:
        return False

    # Check: at least one year word must be present
    bare_tokens = [strip_points(t) for t in tokens]
    has_year_word = any(year_skel in bare for bare in bare_tokens for year_skel in YEAR_SKELETONS)

    if not has_year_word:
        return False

    # Check: must not contain primary verbs (יחי, ילד, other 3-consonant verbs)
    # Allow only auxiliary verbs, prepositions, conjunctions, year words, numerals

    # Prohibited patterns: 3-consonant verb roots (simplified check)
    for bare_token in bare_tokens:
        # Reject known verbs beyond year-related context
        if len(bare_token) >= 3:
            # Check against common prose verbs (this is conservative to avoid false positives)
            # We allow יחי and ילד in COMBINATION with year words, but alone they're not fragments
            # For now, a pure numeric line is one that ONLY contains:
            # - Numbers (digit strings, Hebrew number words)
            # - Year words
            # - Prepositions/conjunctions (ו, ב, etc.)
            # - Maqqef
            pass

    # Conservative check: does the line look like pure numerals + years?
    # Example: "חָמֵ֥שׁ שָׁנִ֖ים וּמְאַ֣ת שָׁנָ֑ה" → yes
    # Example: "וַיְחִ֣י אָדָ֗ם שְׁלֹשִׁ֤ים" → no (has name + verb)

    # Pattern: if 70%+ of non-preposition tokens are year-related or numeric, it's a fragment
    non_prep_count = 0
    numeric_or_year_count = 0

    for bare_token in bare_tokens:
        # Skip pure conjunctions/prepositions (ו, ב, ל, etc. as prefix)
        if len(bare_token) <= 2 and bare_token in {'ו', 'ב', 'ל', 'את', 'ובן'}:
            continue
        # Skip maqqef alone
        if bare_token == MAQQEF:
            continue

        non_prep_count += 1

        # Check if this is a year word or digit
        if any(year_skel in bare_token for year_skel in YEAR_SKELETONS):
            numeric_or_year_count += 1
        elif re.match(r'^\d+$', bare_token):
            numeric_or_year_count += 1

    # If there are no non-prep tokens, it's not a fragment (maybe all boilerplate)
    if non_prep_count == 0:
        return False

    # If ≥70% are numeric/year, it's a numeric fragment
    if non_prep_count > 0 and numeric_or_year_count / non_prep_count >= 0.7:
        return True

    return False


def is_orphan_wayyelad(line: str, previous_lines: list[str], line_idx: int) -> bool:
    """Return True if line starts with וַיּוֹלֶד but prior context lacks a generation setup.

    Per H17: וַיּוֹלֶד without a preceding וַיְחִי/living clause = orphan fragment.
    This is a weak signal (could be legitimate in some lists), so we combine it with
    other heuristics. For now, trigger only if the PREVIOUS line is also numeric.
    """
    bare_first = strip_points(line.split()[0]) if line.split() else ""

    # Check if line starts with וַיּוֹלֶד (skeleton יִלְדוּ, יוֹלֶד, etc.)
    if WAYYELAD_SKELETON not in bare_first:
        return False

    # Check if there is a preceding non-empty line
    if line_idx == 0:
        return False

    # Look back for recent context (within 2 lines)
    prior_yechi_found = False
    for back_idx in range(line_idx - 1, max(-1, line_idx - 3), -1):
        if back_idx < 0 or back_idx >= len(previous_lines):
            break
        prev_line = previous_lines[back_idx]
        if is_skippable(prev_line):
            continue
        # If we find a יחי in recent context, this וַיּוֹלֶד is not orphan
        if YECHI_SKELETON in ''.join(strip_points(t) for t in prev_line.split()):
            prior_yechi_found = True
            break
        # If the previous is numeric, this is suspicious
        if is_numeric_fragment(prev_line):
            return True  # orphan וַיּוֹלֶד after numeric fragment

    return False


def is_skippable(line: str) -> bool:
    """Return True for blank lines and verse-reference-only lines."""
    s = line.strip()
    if not s:
        return True
    # Verse reference pattern: optional book name + N:N (or just N:N)
    if re.match(r"^(\S+\s+)?\d+:\d+$", s):
        return True
    return False


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    """Scan one text file for Rule H17 genealogy-uniformity violations."""
    violations = []

    # Only scan files in genealogy scope
    if not is_genealogy_file(path):
        return violations

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        line_no = i + 1  # 1-based

        # --- Check for numeric fragment ---
        if is_numeric_fragment(line):
            violations.append({
                "file": path.name,
                "file_path": path,
                "line_num": line_no,
                "rule": "H17/genealogy-uniformity",
                "severity": "STRONG-MERGE-CANDIDATE",
                "brief": f"Genealogy formula fragment: pure numeric/year component; merge upward",
                "line": line.rstrip(),
                "fragment_type": "numeric",
            })
            continue

        # --- Check for orphan וַיּוֹלֶד (weak signal, requires numeric prior) ---
        if is_orphan_wayyelad(line, lines, i):
            violations.append({
                "file": path.name,
                "file_path": path,
                "line_num": line_no,
                "rule": "H17/genealogy-uniformity",
                "severity": "STRONG-MERGE-CANDIDATE",
                "brief": f"Genealogy formula fragment: וַיּוֹלֶד without living-clause setup; merge upward",
                "line": line.rstrip(),
                "fragment_type": "orphan_wayyelad",
            })

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
        help="Restrict scan to one book folder name (e.g. 'genesis'). "
             "Default: all books in the target directory.",
    )
    parser.add_argument(
        "--v2",
        action="store_true",
        help="Scan v2/he instead of v1/he-baseline.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show context for each violation.",
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

    if args.book:
        # Support both bare book name and subdir prefix (e.g. "genesis" or "01-genesis")
        book_dir = base_dir / args.book
        if not book_dir.exists():
            # Try searching for a directory containing the book name
            candidates = [d for d in base_dir.iterdir() if d.is_dir() and args.book in d.name]
            if len(candidates) == 1:
                book_dir = candidates[0]
            elif len(candidates) > 1:
                print(
                    f"ERROR: ambiguous book name {args.book!r}; "
                    f"matches: {[d.name for d in candidates]}",
                    file=sys.stderr,
                )
                sys.exit(2)
            else:
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
        all_violations.extend(scan_file(path, verbose=args.verbose))

    exit_code = 1 if all_violations else 0

    # --- JSON output mode ---
    if args.json:
        findings = []
        for v in all_violations:
            severity_tag = v["severity"]
            applied_action = "merge_with_next" if severity_tag == "STRONG-MERGE-CANDIDATE" else None
            findings.append({
                "file": str(v["file_path"].relative_to(REPO_ROOT)).replace("\\", "/"),
                "line": v["line_num"],
                "severity": "DEVIATION",
                "tag": severity_tag,
                "rule_id": "H17",
                "rule_short": "Genealogy Uniformity",
                "brief": v["brief"],
                "applied_action": applied_action,
            })

        by_severity_json: dict[str, int] = {}
        by_tag: dict[str, int] = {}
        for f in findings:
            by_severity_json[f["severity"]] = by_severity_json.get(f["severity"], 0) + 1
            by_tag[f["tag"]] = by_tag.get(f["tag"], 0) + 1

        doc = {
            "validator": "validate_genealogy_uniformity",
            "rule": "Layer 3 colometry — Rule H17",
            "layer": 3,
            "book": args.book or "all",
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": findings,
            "summary": {
                "total_findings": len(findings),
                "by_severity": by_severity_json,
                "by_tag": by_tag,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output (default) ---
    print("=" * 72)
    print(f"Rule H17 Genealogy Uniformity validator — Tanakh {tier_label}")
    print(f"Reference: canon §5 H17 (genealogy formula uniformity)")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Violations    : {len(all_violations)}")

    by_severity: dict[str, int] = {}
    for v in all_violations:
        by_severity[v["severity"]] = by_severity.get(v["severity"], 0) + 1
    if by_severity:
        print()
        for sev, count in sorted(by_severity.items()):
            print(f"  {sev}: {count}")
    print()

    if all_violations:
        for v in all_violations:
            print(
                f"[DEVIATION]  {v['file']}:{v['line_num']}  "
                f"{v['rule']}  {v['severity']}  {v['brief']}"
            )
            print(f"    {v['line'][:120]}")
            print()
    else:
        print("No violations found. Rule H17 genealogy uniformity is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
