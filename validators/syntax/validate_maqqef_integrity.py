#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Rule H1 — Maqqef-Group Indivisibility.

Rule H1 (canon §5 H1; Layer 1 REQUIRED-MERGE per hebrew-break-legality.md):
The maqqef glyph (U+05BE ־) joins two-to-four orthographic words into a single
prosodic unit bearing a single ta'am. No line break may occur inside a
maqqef-group. A break inside a maqqef-group is a hard grammatical violation
(Joüon-Muraoka §13), not an editorial judgment call.

Detection strategy:
  - A maqqef at the END of a line (last non-whitespace character is ־) indicates
    that the token before the maqqef and the continuation token on the next line
    are members of the same maqqef-group but appear on separate lines.
  - This is a precise mechanical check: any line whose last visible character
    is ־ is a Rule H1 violation.

Output format:
    [MALFORMED]  file:line_number  H1/maqqef  brief description

Exit code: 0 if zero violations, 1 if violations found, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/syntax/validate_maqqef_integrity.py
    PYTHONIOENCODING=utf-8 py -3 validators/syntax/validate_maqqef_integrity.py --book jonah
    PYTHONIOENCODING=utf-8 py -3 validators/syntax/validate_maqqef_integrity.py --v4
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
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1-he-baseline"
V4_DIR = REPO_ROOT / "data" / "text-files" / "v4-editorial"

# Maqqef glyph
MAQQEF = "־"  # U+05BE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_skippable(line: str) -> bool:
    """Return True for blank lines and verse-reference-only lines."""
    s = line.strip()
    if not s:
        return True
    # Verse reference lines: "1:1" or "Jonah 1:1"
    if re.match(r"^(\w+\s+)?\d+:\d+$", s):
        return True
    return False


def line_ends_with_maqqef(line: str) -> bool:
    """Return True if the line's last visible character is the maqqef glyph.

    Hebrew combining marks (niqqud, te'amim) may follow the maqqef in the
    encoded string, but visually/prosodically the maqqef is the joining
    connector. We detect this by scanning right-to-left past any combining
    diacritics to find the last base character.
    """
    # Strip trailing whitespace first
    stripped = line.rstrip()
    if not stripped:
        return False

    # Hebrew combining character ranges: U+0591–U+05C7 (cantillation + points)
    # Walk backwards past any trailing combining marks
    i = len(stripped) - 1
    while i >= 0 and ("֑" <= stripped[i] <= "ׇ"):
        i -= 1

    if i < 0:
        return False

    return stripped[i] == MAQQEF


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path) -> list[dict]:
    """Scan one text file for Rule H1 maqqef-group integrity violations."""
    violations = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    for i, line in enumerate(lines, start=1):
        if is_skippable(line):
            continue

        if line_ends_with_maqqef(line):
            # i is 1-based; lines is 0-based, so lines[i] is the next line
            next_line = lines[i] if i < len(lines) else ""
            next_line_num = i + 1 if i < len(lines) else None
            violations.append(
                {
                    "file": path.name,
                    "file_path": path,
                    "line_num": i,
                    "rule": "H1/maqqef",
                    "brief": "line-final maqqef ־ — maqqef-group split across lines",
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
        help="Restrict scan to one book folder name (e.g. 'jonah'). "
             "Default: all books in the target directory.",
    )
    parser.add_argument(
        "--v4",
        action="store_true",
        help="Scan v4-editorial files instead of v1-he-baseline.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show next-line context for each violation.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as a single JSON document to STDOUT instead of human-readable lines.",
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

    exit_code = 1 if all_violations else 0

    # --- JSON output mode ---
    if args.json:
        findings = []
        for v in all_violations:
            findings.append({
                "file": str(v["file_path"].relative_to(REPO_ROOT)).replace("\\", "/"),
                "line": v["line_num"],
                "severity": "MALFORMED",
                "tag": "STRONG-MERGE-CANDIDATE",
                "rule_id": "H1.1",
                "rule_short": "maqqef-group split across lines",
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
            "validator": "validate_maqqef_integrity",
            "rule": "Rule H1 — Maqqef-Group Indivisibility",
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
    print(f"Rule H1 Maqqef-Group Integrity validator — Tanakh {tier_label}")
    print(f"Reference: canon §5 H1 + hebrew-break-legality.md (REQUIRED-MERGE)")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Violations    : {len(all_violations)}")
    print()

    if all_violations:
        for v in all_violations:
            print(f"[MALFORMED]  {v['file']}:{v['line_num']}  {v['rule']}  {v['brief']}")
            print(f"    {v['line'][:120]}")
            if args.verbose and v["next_line"]:
                print(f"    → {v['next_line'][:120]}")
            print()
    else:
        print("No violations found. Rule H1 maqqef-group integrity is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
