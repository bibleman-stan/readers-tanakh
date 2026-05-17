#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Rule H17 — List-Formula Peers (curse / blessing / beatitude series).

Rule H17 (canon §5 H17; Layer 3 editorial rule):
Per the Parallel-List Uniformity Principle, when a series of consecutive
verses opens with the same list-formula lemma (אָרוּר curse / בָּרוּךְ blessing /
אַשְׁרֵי beatitude), each member is one atomic unit and the formula token
must be line-leading in its member-verse.

LIST_FORMULA_PEERS (canon-named, distinct from H17 genealogy formulae):
  - ארור (Deut 27:15–26 curse series; scattered curses elsewhere)
  - ברוך (Deut 28:3–6 blessing series; scattered blessings)
  - אשרי (Pss 1, 32, 41, 84, 119, 128, Prov 8:32 — mostly singular beatitudes)

VIOLATION PATTERN:
  A line where a list-formula lemma is non-line-leading (i.e., prior content
  on the same line precedes the formula) AND the line is part of a series
  (consecutive verses opening with the same lemma).

  Single-occurrence uses (the majority — see corpus pre-flight 2026-05-16:
  122 single vs 6 series-of-2) are NOT in scope. The validator targets
  parallel-series uniformity, not standalone formulaic ATUs.

SERIES DETECTION:
  Verse-level: a "series" is N≥2 consecutive verses whose first
  non-skippable line opens with the same list-formula lemma (after
  vav-conjunctive stripping).

VIOLATION TAGS:
  STRONG-SPLIT-CANDIDATE — formula-lemma appears mid-line in a series-member;
                           split needed to give the formula its own line.

CORPUS REALITY (pre-flight 2026-05-16):
  All series instances in current v2/heb are already correctly edited —
  formula tokens are line-leading. Validator role is REGRESSION-AUDIT
  ONLY: catches future un-edits that introduce non-uniform formatting.
  Expected baseline: 0 findings.

  Known series locations:
    - Deut 27:15–26: ארור 12-verse curse series (interrupted by amen
      responses; series boundaries detected per consecutive opener)
    - Deut 28:3–6: ברוך blessing series (run of 4)
    - Deut 28:16–19: ארור curse series (run of 4)
    - 2 Chr 9:7: אשרי beatitude pair
    - Ps 84:5–6: אשרי beatitude pair
    - Ps 119:1–2: אשרי acrostic pair (aleph stanza)
    - Ps 144:15: אשרי beatitude pair

ARCHITECTURAL NOTE (FORK rationale):
  This validator forks from validate_genealogy_uniformity.py per Stan's
  2026-05-16 directive #3. Trigger surface (consecutive-verse formula-
  lemma series across 3 lemmas) is fundamentally-different from
  validate_genealogy_uniformity's year-count + paternity-formula triggers;
  bundling would violate naming-truth.

Output format:
    [DEVIATION]  file:line_number  H17/list-formula  SEVERITY  brief description

Exit code: 0 if zero violations, 1 if violations found, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_list_formula_uniformity.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_list_formula_uniformity.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_list_formula_uniformity.py --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "heb"

HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")
SOF_PASUQ = "׃"
MAQQEF = "־"
_VERSE_REF_RE = re.compile(r"^\d+:\d+\s*$")

# Canon §5 H17 closed list — list-formula opening lemmas (parallel-series uniformity).
LIST_FORMULA_PEERS = frozenset({
    "ארור",   # curse formula (Deut 27:15-26 + scattered)
    "ברוך",   # blessing formula (Deut 28:3-6 + scattered)
    "אשרי",   # beatitude formula (Pss, Prov)
})


def strip_points(token: str) -> str:
    return HEBREW_POINTS_RE.sub("", token)


def is_skippable(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    if _VERSE_REF_RE.match(s):
        return True
    return False


def _strip_vav_prefix(skel: str) -> str:
    """Strip leading vav-conjunctive (ו) if present."""
    if skel.startswith("ו") and len(skel) > 1:
        return skel[1:]
    return skel


def _opener_lemma(line: str) -> "str | None":
    """Return the list-formula lemma opening this line (with vav-prefix
    stripped), or None if the line doesn't open with a peer lemma."""
    tokens = line.split()
    if not tokens:
        return None
    first_skel = strip_points(tokens[0])
    if MAQQEF in first_skel:
        first_skel = first_skel.split(MAQQEF, 1)[0]
    candidate = _strip_vav_prefix(first_skel)
    if candidate in LIST_FORMULA_PEERS:
        return candidate
    return None


def _partition_into_verses(lines: list[str]) -> list[tuple[int, list[tuple[int, str]]]]:
    """Partition file lines into per-verse groups."""
    groups: list[tuple[int, list[tuple[int, str]]]] = []
    cur_verse: "int | None" = None
    cur_lines: list[tuple[int, str]] = []
    for i, raw in enumerate(lines):
        line_no = i + 1
        s = raw.strip()
        m = _VERSE_REF_RE.match(s)
        if m:
            if cur_verse is not None and cur_lines:
                groups.append((cur_verse, cur_lines))
            cur_verse = int(s.split(":")[1])
            cur_lines = []
        elif s and cur_verse is not None:
            cur_lines.append((line_no, raw))
    if cur_verse is not None and cur_lines:
        groups.append((cur_verse, cur_lines))
    return groups


def scan_file(path: Path) -> list[dict]:
    """Scan one chapter file for Rule H17 list-formula-uniformity violations."""
    violations: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    verse_groups = _partition_into_verses(lines)
    if not verse_groups:
        return violations

    verse_openers: list[tuple[int, "str | None", int, str]] = []
    for verse_num, verse_lines in verse_groups:
        first_content = next(
            ((ln, raw) for ln, raw in verse_lines if not is_skippable(raw)),
            None,
        )
        if first_content is None:
            verse_openers.append((verse_num, None, 0, ""))
            continue
        ln, raw = first_content
        verse_openers.append((verse_num, _opener_lemma(raw), ln, raw))

    i = 0
    while i < len(verse_openers):
        _, lemma, _, _ = verse_openers[i]
        if lemma is None:
            i += 1
            continue
        j = i + 1
        while j < len(verse_openers) and verse_openers[j][1] == lemma:
            j += 1
        run_len = j - i
        if run_len >= 2:
            for k in range(i, j):
                _, _, line_no, first_line = verse_openers[k]
                tokens = first_line.split()
                if not tokens:
                    continue
                lemma_position = None
                for tok_idx, tok in enumerate(tokens):
                    skel = strip_points(tok)
                    if MAQQEF in skel:
                        skel = skel.split(MAQQEF, 1)[0]
                    if _strip_vav_prefix(skel) == lemma:
                        lemma_position = tok_idx
                        break
                if lemma_position is None or lemma_position == 0:
                    continue
                violations.append({
                    "file": path.name,
                    "file_path": path,
                    "line_num": line_no,
                    "rule": "H17/list-formula",
                    "severity": "STRONG-SPLIT-CANDIDATE",
                    "brief": (
                        f"list-formula series member ({lemma}, series of {run_len}) "
                        f"has lemma at token {lemma_position}, not line-leading — "
                        f"split per canon §5 H17 Parallel-List Uniformity"
                    ),
                    "line": first_line.rstrip(),
                    "series_lemma": lemma,
                    "series_length": run_len,
                })
        i = j
    return violations


def format_finding(v: dict) -> str:
    return (
        f"[DEVIATION]  {v['file']}:{v['line_num']}  {v['rule']}  "
        f"{v['severity']}  {v['brief']}\n  {v['line']}"
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--book", help="book slug (e.g., 05-deuteronomy)")
    p.add_argument("--v1", action="store_true",
                   help="scan v1/he-baseline (legacy; default is v2/heb)")
    p.add_argument("--v2", action="store_true",
                   help="explicit v2/heb (default; flag kept for backward-compat)")
    p.add_argument("--json", action="store_true", help="emit JSON")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    # Default to V2 (source of truth); --v1 explicit legacy access.
    # Must-fix #4 in 2400 directive — was V1_DIR default; flipped to
    # match regression-audit semantic contract (v2/heb is source of truth).
    root = V1_DIR if args.v1 else V2_DIR
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 2

    books = [args.book] if args.book else sorted(d.name for d in root.iterdir() if d.is_dir())
    all_findings: list[dict] = []
    for book in books:
        book_dir = root / book
        if not book_dir.is_dir():
            continue
        for chapter_file in sorted(book_dir.glob("*.txt")):
            findings = scan_file(chapter_file)
            all_findings.extend(findings)

    if args.json:
        output = {
            "validator": "validate_list_formula_uniformity",
            "rule": "Layer 3 colometry — Rule H17 (list-formula peers)",
            "layer": 3,
            "book": args.book or "all",
            "findings": [
                {
                    "file": str(f["file_path"]),
                    "line": f["line_num"],
                    "rule": f["rule"],
                    "severity": f["severity"],
                    "annotation": f["brief"],
                    "context": f.get("line", ""),
                }
                for f in all_findings
            ],
            "summary": {
                "total_findings": len(all_findings),
            },
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for f in all_findings:
            print(format_finding(f))
    return 0 if not all_findings else 1


if __name__ == "__main__":
    sys.exit(main())
