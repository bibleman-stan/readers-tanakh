#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate subordinator-content bond pattern (frozen-phrase / subordinator-content).

Pattern: Subordinator (פֶּן, לְמַעַן, אַחֲרֵי, עַל־כֵּן, יַעַן, בִּגְלַל, בִּשְׁבִיל, בַּעֲבוּר)
appears at the end of a line; finite-verb clause or NP clause head begins on the
next line. These subordinators form frozen phrases with their content and should
not be split across lines.

VIOLATION PATTERN:
  A line ends with a subordinator token (last content token after stripping
  niqqud + te'amim → consonant skeleton) matches a subordinator skeleton,
  and the NEXT line begins with a finite verb or NP that is the clause head.
  Fix: merge the subordinator onto the same line as its clause content.

SEVERITY:
  STRONG-MERGE-CANDIDATE — subordinators are frozen to their content clause.

SUBORDINATOR SKELETONS (consonants only, after stripping points):
  פן     — pen          "lest" (negative purpose)
  למען   — lema'an      "for the sake of / in order that"
  אחרי   — acharei      "after"
  עלכן   — al-ken       "for this reason / therefore" (also with maqqef)
  יען    — ya'an        "because / seeing that"
  בגלל   — biglal       "on account of / because"
  בשביל  — bishhvil     "for the sake of"
  בעבור  — ba'avur      "for the sake of / because"

No te'amim glyphs in the detection logic. The pattern is purely syntactic:
subordinator + blank line + clause head (verb or NP).

Output format:
    [DEVIATION]  file:line_number  subordinator-content-bond  SEVERITY  brief

Exit code: 0 if zero violations, 1 if violations found, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_pen_subordinator.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_pen_subordinator.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_pen_subordinator.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_pen_subordinator.py --json
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_pen_subordinator.py --verbose
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

# Make _shared importable when this script is run as __main__.
sys.path.insert(0, str(REPO_ROOT / "validators"))
from _shared.poetic_register import is_poetic_register  # noqa: E402

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers
# ---------------------------------------------------------------------------

# Maqqef glyph (U+05BE ־)
MAQQEF = "־"

# Sof pasuq glyph (U+05C3 ׃)
SOF_PASUQ = "׃"

# Hebrew points range U+0591–U+05C7: cantillation accents + niqqud vowels
HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")


def strip_points(token: str) -> str:
    """Return token with all niqqud and te'amim stripped (consonant skeleton only)."""
    return HEBREW_POINTS_RE.sub("", token)


# ---------------------------------------------------------------------------
# Subordinator skeleton set
# ---------------------------------------------------------------------------

SUBORDINATOR_SKELETONS: set[str] = {
    "פן",      # פֶּן / פֶּן־        "lest" (negative purpose)
    "למען",    # לְמַעַן            "for the sake of / in order that"
    "אחרי",    # אַחֲרֵי            "after"
    "עלכן",    # עַל־כֵּן           "for this reason / therefore"
    "יען",     # יַעַן              "because / seeing that"
    "בגלל",    # בִּגְלַל           "on account of / because"
    "בשביל",   # בִּשְׁבִיל         "for the sake of"
    "בעבור",   # בַּעֲבוּר          "for the sake of / because"
}

# Common finite-verb indicators at start of line.
# After stripping points, match consonant skeletons of common finite verbs.
# We focus on high-frequency verbs to avoid false negatives.
FINITE_VERB_STARTS: set[str] = {
    "היה",     # הָיָה / וַיְהִי
    "אמר",     # אָמַר / וַיֹּאמֶר
    "עשה",     # עָשָׂה / וַיַּעַשׂ
    "נתן",     # נָתַן / וַיִּתֵּן
    "לקח",     # לָקַח / וַיִּקַּח
    "בוא",     # בָּא / וַיָּבֹא
    "ראה",     # רָאָה / וַיַּרְא
    "שמע",     # שָׁמַע / וַיִּשְׁמַע
    "ידע",     # יָדַע / וַיֵּדַע
    "הלך",     # הָלַךְ / וַיֵּלֶךְ
    "ישב",     # יָשַׁב / וַיֵּשֶׁב
    "קם",      # קָם / וַיָּקָם
    "חזר",     # חָזַר / וַיָּשָׁב
    "רצה",     # רָצָה / וַיִּרְצֶה
    "שם",      # שָׂם / וַיָּשֶׂם
    "דבר",     # דִּבֵּר / וַיְדַבֵּר
    "בחר",     # בָּחַר
    "גם",      # also (particle, but can front a clause)
    "הנה",     # behold (sentence-initial deictic)
    "ועתה",    # and now (discourse pivot)
}

# NP clause head indicators (article + noun, proper noun, pronoun).
# These patterns identify noun phrases that typically head a clause.
NP_START_PATTERNS = [
    r"^ה",     # Article ה (definite NP: the X)
    r"^יהוה",  # Divine name YHWH
    r"^אלהים", # אֱלֹהִים
    r"^אדני",  # אֲדֹנָי
    r"^אדם",   # אָדָם (human)
    r"^כל",    # כָּל (all)
    r"^זה",    # זֶה (this)
    r"^הוא",   # הוּא (he/that)
    r"^היא",   # הִיא (she/that)
]

# Punctuation-only tokens to skip when looking for the last content token.
PUNCTUATION_SKELETONS: set[str] = {
    "׃",   # sof pasuq
    "׀",   # paseq
    "ס",   # setuma paragraph marker
    "פ",   # petucha paragraph marker
    "",    # empty after stripping
}

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


def parse_verse_ref(line: str):
    """If line is a 'C:V' verse-reference line, return (chapter, verse). Else None."""
    s = line.strip()
    m = re.match(r"^(?:\S+\s+)?(\d+):(\d+)\s*$", s)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def is_punctuation_only(skeleton: str) -> bool:
    """Return True if this token's skeleton is pure punctuation / empty."""
    return skeleton in PUNCTUATION_SKELETONS or skeleton == MAQQEF


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
    """Return the skeleton of the first non-punctuation token on the line.

    Returns None if all tokens are punctuation or the line is empty.
    """
    tokens = line.strip().split()
    for tok in tokens:
        skel = strip_points(tok)
        if not is_punctuation_only(skel):
            return skel
    return None


def is_finite_verb_start(skeleton: str) -> bool:
    """Return True if skeleton looks like a finite verb start."""
    return skeleton in FINITE_VERB_STARTS


def is_np_start(skeleton: str) -> bool:
    """Return True if skeleton looks like an NP clause head."""
    for pattern in NP_START_PATTERNS:
        if re.match(pattern, skeleton):
            return True
    return False


def line_ends_at_clause_boundary(line: str) -> bool:
    """Return True if the last non-whitespace CHARACTER of the line is sof-pasuq.

    Sof-pasuq marks the end of a Masoretic verse — a clause-end positioning
    is a different editorial question from subordinator stranding.
    Do not flag subordinators at clause-end even if they are the last content token.
    """
    stripped = line.rstrip()
    if not stripped:
        return False
    return stripped[-1] == SOF_PASUQ


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    """Scan one text file for subordinator-content-bond violations."""
    violations: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    book = book_name_from_path(path)
    chapter_from_file = chapter_from_path(path)

    # Track current chapter/verse as we scan (updated from verse-reference lines)
    cur_chapter: int | None = chapter_from_file
    cur_verse: int | None = None

    for i, line in enumerate(lines):
        # Update chapter/verse tracking before skippability check
        ref = parse_verse_ref(line)
        if ref is not None:
            cur_chapter, cur_verse = ref
            continue

        if is_skippable(line):
            continue

        line_no = i + 1  # 1-based

        # Guard 0: poetic register — suppress false positives in Sifrei Emet
        # and embedded-poetry chapters (Song of Songs, Lamentations, etc.).
        if cur_chapter is not None and is_poetic_register(book, cur_chapter, cur_verse):
            continue

        # Guard 1: clause-boundary — subordinator at verse-end is not stranded.
        if line_ends_at_clause_boundary(line):
            continue

        # Find the last non-punctuation consonant skeleton on this line.
        skeleton = last_content_token(line)
        if skeleton is None:
            continue

        # Guard 2: only flag if this skeleton is a subordinator.
        if skeleton not in SUBORDINATOR_SKELETONS:
            continue

        # Find next non-empty content line (the line whose clause the
        # subordinator should introduce).
        next_content = ""
        next_content_line_num: int | None = None
        for j in range(i + 1, len(lines)):
            if not is_skippable(lines[j]):
                next_content = lines[j].strip()
                next_content_line_num = j + 1  # 1-based
                break

        # Only report if there IS a next line (the subordinator is genuinely
        # stranded with content clause below it).
        if not next_content:
            continue

        # Check if next line begins with finite verb or NP clause head.
        next_skeleton = first_content_token(next_content)
        if next_skeleton is None:
            continue

        # Guard 3: require the next line to look like clause content (finite
        # verb or NP head). This implements the is_clause_content gate that
        # was computed but pass'd unused in the original code — the comment
        # "don't skip even if not in explicit lists" was the bug.
        is_clause_content = is_finite_verb_start(next_skeleton) or is_np_start(next_skeleton)
        if not is_clause_content:
            continue

        # Identify the original token (with pointing) for display.
        tokens = line.rstrip().split()
        display_token = tokens[-1] if tokens else skeleton  # raw form for display

        violations.append({
            "file": path.name,
            "file_path": path,
            "line_num": line_no,
            "rule": "subordinator-content-bond",
            "severity": "STRONG-MERGE-CANDIDATE",
            "skeleton": skeleton,
            "display_token": display_token,
            "brief": (
                f"subordinator ‫{display_token}‬ stranded at line end; "
                f"merge with next line (clause content begins with ‫{next_skeleton}‬)"
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
                "severity": "DEVIATION",
                "tag": v["severity"],       # "STRONG-MERGE-CANDIDATE"
                "rule_id": "subordinator-content-bond",
                "rule_short": "Frozen-phrase subordinator bond",
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
            "validator": "validate_pen_subordinator",
            "rule": "Frozen-phrase subordinator-content bond",
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
    print(f"Subordinator-Content Bond validator — Tanakh {tier_label}")
    print(
        "Subordinators: פֶּן לְמַעַן אַחֲרֵי "
        "עַל־כֵּן יַעַן בִּגְלַל בִּשְׁבִיל בַּעֲבוּר"
    )
    print("Reference: Frozen-phrase pattern — subordinators bond to clause content")
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
                f"[DEVIATION]  {v['file']}:{v['line_num']}  "
                f"{v['rule']}  {v['severity']}  {v['brief']}"
            )
            print(f"    {v['line'][:120]}")
            if args.verbose and v.get("next_line"):
                print(f"    → {v['next_line'][:120]}")
            print()
    else:
        print(
            "No violations found. Subordinator-content bonds are clean."
        )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
