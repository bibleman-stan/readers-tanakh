#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate Parallel-List Uniformity Principle — multi-verse lists with uniform frame.

Rule (1-method/canon §1 Structural Justification 1; Layer 3 editorial rule):
Formally-marked parallel series with shared predicate recovery via formal
markers should have uniform line treatment per member. When N≥3 members
share an explicit lexical anchor (אָרוּר, בָּרוּךְ, אַשְׁרֵי, הוֹי, כֹּה אָמַר יְהוָה,
etc.), the line count should be consistent across members.

PATTERN DETECTION:
  - Multi-verse runs with repeated lexical anchor (verse-initial or frame-initial)
  - Series with N≥3 members (Deut 27 curses: verses 15–26 with אָרוּר)
  - Series with N≥3 members (Deut 28 blessings: verses 3–14 with בָּרוּךְ)
  - Series with N≥3 members (Psalm 119 stanzas with אַשְׁרֵי or other marker)
  - Series with N≥3 members (Prophetic woes: הוֹי chains)
  - Series with N≥3 members (Oracle formulas: כֹּה אָמַר יְהוָה chains)

VIOLATION DETECTION:
  Within each detected series, count content lines per member (skipping verse
  references). If members have mixed line counts (some 1-line, some 3-line,
  etc.), flag as uniformity violation.

SEVERITY:
REVIEW-REQUIRED — uniformity is editorial judgment. Series structure is
identifiable grammatically, but how to achieve uniform treatment is editorial.

ARCHITECTURAL CONSTRAINT — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. Te'amim
(U+0591–U+05AF) do NOT appear in any predicate that decides whether to
fire a finding.

Output format:
    [DEVIATION]  file:verse  parallel-series-uniformity  REVIEW-REQUIRED  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_parallel_series_uniformity.py
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_parallel_series_uniformity.py --book deuteronomy
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_parallel_series_uniformity.py --v2
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_parallel_series_uniformity.py --json
"""

import argparse
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

def _find_repo_root():
    """Repo root by MARKER, not by counting parents.

    Counting encodes this file's depth in the tree, so moving the file silently
    breaks it and no text-based check notices. Anchoring on .git survives any
    move. Added 2026-08-10 after a reorg broke three different counted idioms.
    """
    from pathlib import Path as _P
    _here = _P(__file__).resolve()
    for _p in _here.parents:
        if (_p / ".git").exists():
            return _p
    return _here.parent


# ---------------------------------------------------------------------------
# Path constants — two-tier layout: v1/he-baseline + v2/heb
# ---------------------------------------------------------------------------
REPO_ROOT = _find_repo_root()
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files"  / "v2" / "heb"

# Make _shared importable when this script is run as __main__.
sys.path.insert(0, str(REPO_ROOT / "5-machinery/validators"))

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers
# ---------------------------------------------------------------------------

# Hebrew points (cantillation U+0591–U+05AF + niqqud U+05B0–U+05BC, U+05C1–U+05C2,
# U+05C4–U+05C5, U+05C7). Strip points while PRESERVING maqqef, paseq, sof pasuq.
HEBREW_POINTS_RE = re.compile(r"[֑-ׇֽֿׁׂׅׄ]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"  # ׃

# Maqqef (orthographic word-joiner)
MAQQEF = "־"     # ־


def strip_points(token: str) -> str:
    """Return token with niqqud and te'amim stripped (consonant skeleton + sof pasuq + maqqef)."""
    return HEBREW_POINTS_RE.sub("", token)


# ---------------------------------------------------------------------------
# Verse-reference / blank line handling
# ---------------------------------------------------------------------------

VERSE_REF_RE = re.compile(r"^(\S+\s+)?\d+:\d+\s*$")


def is_skippable(line: str) -> bool:
    """Return True if line is blank or just a verse reference."""
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
    """Return the book directory name (e.g. '05-deuteronomy')."""
    return path.parent.name


def chapter_from_path(path: Path) -> int | None:
    m = CHAPTER_FILENAME_RE.search(path.name)
    if not m:
        return None
    return int(m.group(1))


# ---------------------------------------------------------------------------
# Lexical anchor detection — parallel series frame words
# ---------------------------------------------------------------------------

# Map of anchor skeletons to their scope (range of verses they typically span)
# and description. Each entry: skeleton -> (description, typical_scope)
ANCHOR_PATTERNS = {
    # Deut 27:15–26 — curse formula
    "ארור": ("curse (אָרוּר)", "deut27"),

    # Deut 28:3–6 — short blessings
    # Deut 28:7–14 — longer blessings (mixed with יִתֵּן / יְצַ֨ו / יְקִֽימְךָ / יְרָאוּ / יְהוֹתִר)
    "ברוך": ("blessing (בָּרוּךְ)", "deut28"),

    # Psalm openings / acrostic markers (אַשְׁרֵי is also used as blessing formula)
    "אשרי": ("happy/blessed (אַשְׁרֵי)", "psalm"),

    # Prophetic woes — Isa 5, Isa 10, Amos 5–6, Habakkuk 2, etc.
    "הוי": ("woe (הוֹי)", "prophecy"),

    # Oracle chains — כֹּה אָמַר יְהוָה repeated frame
    "כהאמר": ("thus says YHWH (כֹּה אָמַר יְהוָה)", "oracle"),
}


def get_anchor_skeleton(token: str) -> str:
    """Return the consonant skeleton of a token (for matching anchors)."""
    return strip_points(token)


def detect_anchor_in_line(line: str) -> tuple[str | None, str | None]:
    """Detect if line starts with an anchor pattern.

    Returns (anchor_skeleton, description) if found, (None, None) otherwise.
    """
    toks = line.strip().split()
    if not toks:
        return None, None

    # Check first token and first two tokens (for כֹּה אָמַר יְהוָה)
    bare_first = get_anchor_skeleton(toks[0])

    # Single-token anchors
    if bare_first in ANCHOR_PATTERNS:
        desc, _ = ANCHOR_PATTERNS[bare_first]
        return bare_first, desc

    # Two-token anchors (כֹּה אָמַר)
    if len(toks) >= 2:
        bare_second = get_anchor_skeleton(toks[1])
        combined = bare_first + bare_second
        if combined == "כהאמר":  # כֹּה אָמַר
            return "כהאמר", "thus says YHWH"

    return None, None


# ---------------------------------------------------------------------------
# Series detection — group consecutive verses by anchor
# ---------------------------------------------------------------------------

def detect_parallel_series(lines: list[str]) -> list[dict]:
    """Detect parallel series in the chapter.

    Returns a list of series dictionaries:
      {
        "anchor": anchor_skeleton,
        "description": description_string,
        "verses": [(chapter, verse, verse_start_line_idx, verse_lines), ...],
      }

    Each verse entry is:
      (chapter, verse, line_idx_of_verse_ref, [content_line_indices])
    """

    # Parse into verses
    verses_list = []
    cur_chapter = None
    cur_verse = None
    cur_verse_ref_idx = None
    cur_content_indices = []

    for i, line in enumerate(lines):
        ref = parse_verse_ref(line)
        if ref is not None:
            # Flush current verse
            if cur_verse is not None:
                verses_list.append((cur_chapter, cur_verse, cur_verse_ref_idx, cur_content_indices[:]))
            cur_chapter, cur_verse = ref
            cur_verse_ref_idx = i
            cur_content_indices = []
            continue
        if not is_skippable(line):
            cur_content_indices.append(i)
    if cur_verse is not None:
        verses_list.append((cur_chapter, cur_verse, cur_verse_ref_idx, cur_content_indices))

    # Group consecutive verses with the same anchor
    series_list = []
    i = 0
    while i < len(verses_list):
        ch, vs, vs_ref_idx, content_idx = verses_list[i]

        # Get first content line of this verse (if any)
        if not content_idx:
            i += 1
            continue

        first_content_line = lines[content_idx[0]]
        anchor, desc = detect_anchor_in_line(first_content_line)

        if anchor is None:
            i += 1
            continue

        # Found an anchor — collect consecutive verses with same anchor
        series_members = [(ch, vs, vs_ref_idx, content_idx)]
        j = i + 1
        while j < len(verses_list):
            ch_j, vs_j, vs_ref_idx_j, content_idx_j = verses_list[j]
            if not content_idx_j:
                j += 1
                continue

            first_line_j = lines[content_idx_j[0]]
            anchor_j, desc_j = detect_anchor_in_line(first_line_j)

            if anchor_j == anchor:
                series_members.append((ch_j, vs_j, vs_ref_idx_j, content_idx_j))
                j += 1
            else:
                break

        # Only emit if N≥3 members
        if len(series_members) >= 3:
            series_list.append({
                "anchor": anchor,
                "description": desc,
                "verses": series_members,
            })

        i = j

    return series_list


# ---------------------------------------------------------------------------
# Line counting within a verse
# ---------------------------------------------------------------------------

def count_verse_content_lines(lines: list[str], content_indices: list[int]) -> int:
    """Count non-empty content lines in a verse."""
    count = 0
    for idx in content_indices:
        if idx < len(lines):
            line = lines[idx].strip()
            if line and not VERSE_REF_RE.match(line):
                count += 1
    return count


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    """Scan a file for parallel series uniformity violations."""
    findings: list[dict] = []

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    book = book_name_from_path(path)
    chapter = chapter_from_path(path)

    # Detect parallel series
    series_list = detect_parallel_series(lines)

    for series in series_list:
        anchor = series["anchor"]
        description = series["description"]
        verses = series["verses"]

        # Count lines for each member
        member_line_counts = []
        for ch, vs, vs_ref_idx, content_idx in verses:
            line_count = count_verse_content_lines(lines, content_idx)
            member_line_counts.append((vs, line_count, content_idx))

        # Check uniformity
        unique_counts = set(count for _, count, _ in member_line_counts)

        if len(unique_counts) > 1:
            # Uniformity violation detected
            first_member_count = member_line_counts[0][1]
            line_counts_str = ", ".join(str(count) for _, count, _ in member_line_counts)

            brief = (
                f"Parallel series ({description}) has non-uniform line counts: {line_counts_str} "
                f"across {len(verses)} members (Deut 27–28, Psalm 119, Prophetic woes, etc.)"
            )

            findings.append({
                "file_path": path,
                "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "anchor": anchor,
                "description": description,
                "num_members": len(verses),
                "member_line_counts": line_counts_str,
                "verses": [vs for vs, _, _ in member_line_counts],
                "verse_range": f"{member_line_counts[0][0]}–{member_line_counts[-1][0]}",
                "rule": "parallel-series-uniformity",
                "severity": "REVIEW-REQUIRED",
                "book": book,
                "chapter": chapter,
                "brief": brief,
            })

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def resolve_book_dir(base_dir: Path, book_arg: str) -> Path:
    """Resolve a --book argument permissively."""
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
        # Fall back to the other tier
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
                "anchor": f["anchor"],
                "description": f["description"],
                "num_members": f["num_members"],
                "verse_range": f["verse_range"],
                "member_line_counts": f["member_line_counts"],
                "book": f["book"],
                "chapter": f["chapter"],
                "rule": f["rule"],
                "severity": f["severity"],
            })

        counts = {"REVIEW-REQUIRED": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        by_anchor: dict[str, int] = {}
        for f in findings_json:
            by_anchor[f["description"]] = by_anchor.get(f["description"], 0) + 1

        doc = {
            "validator": "validate_parallel_series_uniformity",
            "rule": "parallel-series-uniformity",
            "version": "1.0.0",
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
                "by_anchor": by_anchor,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output ---
    print("=" * 80)
    print(f"Parallel-Series Uniformity Principle validator — Tanakh {tier_label}")
    print(f"Reference: 1-method/canon §1 Structural Justification 1 (formally-marked parallel series)")
    print("=" * 80)
    print(f"Files scanned : {len(files)}")
    print(f"Findings      : {len(all_findings)}")

    by_anchor: dict[str, int] = {}
    for f in all_findings:
        desc = f["description"]
        by_anchor[desc] = by_anchor.get(desc, 0) + 1

    if by_anchor:
        print()
        for desc, count in sorted(by_anchor.items()):
            print(f"  {desc}: {count}")
    print()

    if all_findings:
        for f in all_findings:
            print(
                f"[DEVIATION]  {f['file_rel']}:{f['chapter']}:{f['verse_range']}  "
                f"{f['rule']}  {f['severity']}  {f['description']}"
            )
            if args.verbose:
                print(f"    Members: {len(f['verses'])}, Line counts: {f['member_line_counts']}")
                print(f"    {f['brief']}")
                print()
    else:
        print("No findings. Parallel series uniformity is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
