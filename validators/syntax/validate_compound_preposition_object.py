#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate Layer 1 — Compound Preposition Object Stranding.

Layer 1 break-legality rule (hebrew-break-legality.md row 11):
Compound preposition (מִלִּפְנֵי, מִפְּנֵי, מִתַּחַת, מִבֵּין) stranded from object —
REQUIRED-MERGE

When a line ends with a compound preposition, the object noun phrase must follow
on the same line. If the compound preposition is at line end and the object NP
begins the next line, the line break is a hard grammatical violation (Joüon-Muraoka §103e).

Compound prepositions triggering this rule:
  - מִלִּפְנֵי — from before (מן + לפני)
  - מִפְּנֵי  — from before / because of
  - מִתַּחַת  — from under / beneath
  - מִבֵּין   — from between

And extended compound/prepositional phrases that demand object-same-line:
  - לִפְנֵי   — before / in front of
  - אַחֲרֵי   — after / behind
  - מֵאַחֲרֵי — from behind
  - אֵצֶל   — beside / next to
  - בְּתוֹךְ — in the midst of / within
  - מִתּוֹךְ — from the midst of
  - בְּקֶרֶב — in the midst of
  - בְּעֵבֶר — across / beyond
  - מֵעַל   — from upon / above
  - סָבִיב  — around / surrounding
  - נֶגֶד   — before / opposite
  - מִנֶּגֶד — from opposite / in front of
  - בִּלְתִּי — without / except
  - תַּחַת  — under / instead of
  - עַד     — until / as far as (governs object NP)
  - עַל     — upon / over (can be standalone prep token)
  - אֶל     — to / toward (standalone prep token)
  - בֵּין   — between
  - בִלְתִּי — without / except

Detection strategy:
  - A line ending with a compound-preposition consonant skeleton (after niqqud/te'amim
    stripping) indicates object stranding.
  - The line must NOT end with sof pasuq (׃), which would mark verse end and
    mean the preposition has a pronominal suffix as its object (not stranded).
  - The next line must contain text (non-empty, non-verse-reference).

Output format:
    [MALFORMED]  file:line_number  rule  brief description

Exit code: 0 if zero violations, 1 if violations found, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/syntax/validate_compound_preposition_object.py
    PYTHONIOENCODING=utf-8 py -3 validators/syntax/validate_compound_preposition_object.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/syntax/validate_compound_preposition_object.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/syntax/validate_compound_preposition_object.py --json
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

# Niqqud / cantillation marks to strip when isolating consonant skeleton
# U+0591–U+05C7: Hebrew cantillation and points
HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")

# Compound preposition consonant skeletons (after point-stripping)
# These are multi-consonant orthographic words that must govern an object NP
# on the same line.
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
    "עד",       # עַד     — until / as far as (governs next noun)
    "על",       # עַל     — upon / over (standalone prep token)
    "אל",       # אֶל     — to / toward (standalone prep token)
    "בין",      # בֵּין   — between
    "מבין",     # מִבֵּין — from between
}


def strip_points(token: str) -> str:
    """Return token with niqqud and te'amim stripped (consonants + maqqef only)."""
    return HEBREW_POINTS_RE.sub("", token)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SOF_PASUQ = "׃"  # ׃ — verse-final marker


def is_skippable(line: str) -> bool:
    """Return True for blank lines and verse-reference-only lines."""
    s = line.strip()
    if not s:
        return True
    # Verse reference lines: e.g. "1:1" or "Jonah 1:1"
    if re.match(r"^(\w+\s+)?\d+:\d+$", s):
        return True
    return False


def _last_token(line: str) -> str | None:
    """Return the last whitespace-delimited token of `line`, or None if empty.

    Returns None if the last token ends with the sof pasuq glyph (U+05C3 ׃)
    — a verse-final line cannot contain a stranded preposition by definition.
    """
    tokens = line.rstrip().split()
    if not tokens:
        return None
    last = tokens[-1]
    if SOF_PASUQ in last:
        return None
    return last


def is_noun_phrase_start(line: str) -> bool:
    """Heuristic: does the line begin with a noun phrase?

    A simple heuristic: the first non-whitespace token should be a noun-like
    form (ends with a noun pattern in Hebrew, or is preceded by a preposition/article).
    For now, we use a permissive approach: if the next line is non-empty and
    non-verse-reference, assume it could be an NP continuation.

    This is a conservative check: we require the next line to exist and not be
    obviously a verse reference.
    """
    stripped = line.strip()
    if not stripped:
        return False
    # Reject verse reference
    if re.match(r"^(\w+\s+)?\d+:\d+$", stripped):
        return False
    # Any non-empty, non-verse-ref line is treated as potential NP
    return True


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path) -> list[dict]:
    """Scan one text file for compound-preposition object-stranding violations."""
    violations = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    for i, line in enumerate(lines, start=1):
        if is_skippable(line):
            continue

        # Check if this line ends with a compound preposition
        token = _last_token(line)
        if token is None:
            continue

        bare = strip_points(token)

        # Is this token a compound preposition?
        if bare not in COMPOUND_PREP_SKELETONS:
            continue

        # Check if there's a next line
        next_line_idx = i  # i is 1-based; lines is 0-based
        if next_line_idx >= len(lines):
            # No next line; preposition is at EOF (unusual but not our concern here)
            continue

        next_line = lines[next_line_idx]

        # Does the next line look like it could be the object NP?
        if not is_noun_phrase_start(next_line):
            # Next line is empty or only verse-reference; no object follows
            continue

        # We have a compound preposition at line end followed by a potential NP
        violations.append(
            {
                "file": path.name,
                "file_path": path,
                "line_num": i,
                "rule": "L1/compound-prep-object",
                "brief": f"stranded compound preposition at line end: {token!r}",
                "line": line.rstrip(),
                "next_line_num": i + 1,
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
        help="Restrict scan to one book folder name (e.g. 'genesis', 'jonah'). "
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
            findings.append({
                "file": str(v["file_path"].relative_to(REPO_ROOT)).replace("\\", "/"),
                "line": v["line_num"],
                "severity": "MALFORMED",
                "tag": "STRONG-MERGE-CANDIDATE",
                "rule_id": "L1.11",
                "rule_short": "compound preposition stranded from object",
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
            "validator": "validate_compound_preposition_object",
            "rule": "Layer 1 break-legality — Compound preposition object stranding",
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
    print(f"Layer 1 Compound Preposition validator — Tanakh {tier_label}")
    print(f"Reference: hebrew-break-legality.md row 11 (REQUIRED-MERGE)")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Violations    : {len(all_violations)}")
    print()

    if all_violations:
        for v in all_violations:
            print(f"[MALFORMED]  {v['file']}:{v['line_num']}  {v['rule']}  {v['brief']}")
            print(f"    {v['line'][:120]}")
            print(f"    → {v['next_line'][:120]}")
            print()
    else:
        print("No violations found. Compound prepositions are not stranded from objects.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
