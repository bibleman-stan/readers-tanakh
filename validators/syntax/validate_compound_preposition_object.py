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
# Shared morphology + morph-alignment helpers
# ---------------------------------------------------------------------------
# Make _shared importable when this script is run as __main__.
sys.path.insert(0, str(REPO_ROOT / "validators"))
from _shared import morphology as M  # noqa: E402
from _shared import morph_alignment as MA  # noqa: E402

# ---------------------------------------------------------------------------
# Hebrew Unicode constants
# ---------------------------------------------------------------------------

# Niqqud / cantillation marks to strip when isolating consonant skeleton
# U+0591–U+05C7: Hebrew cantillation and points
HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")

# Compound preposition consonant skeletons (after point-stripping)
# These are multi-consonant orthographic words that must govern an object NP
# on the same line.
# Used as the skel-fallback when TAHOT morph tags are absent (tag path uses
# M.is_bare_prep_token which classifies via tag chain ["R"] = standalone bare
# prep with no pronominal suffix, eliminating FPs from suffixed forms).
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
# Verse-grouping helper (mirrors validate_speech_intro_framing.py)
# ---------------------------------------------------------------------------

_VERSE_REF_RE = re.compile(r"^\d+:\d+\s*$")


def _partition_into_verses(lines: list[str]) -> list[tuple[int, list[tuple[int, str]]]]:
    """Partition file lines into per-verse groups.

    Returns list of (verse_num, [(1-based line_no, raw_line), ...]) tuples.
    Lines preceding any verse header are discarded (blank preamble only).
    """
    groups: list[tuple[int, list[tuple[int, str]]]] = []
    cur_verse: int | None = None
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


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path) -> list[dict]:
    """Scan one text file for compound-preposition object-stranding violations.

    Uses TAHOT morph tags (via morph_alignment) when available to classify the
    last-token on each line as a bare preposition (tag chain ["R"]) vs. a
    suffixed/non-prep form.  This eliminates FPs from prepositions with
    pronominal suffixes (e.g., לְפָנַי "before me") that skeleton-match a
    compound prep skeleton but are NOT stranded.  Falls back to COMPOUND_PREP_SKELETONS
    skeleton membership when tags are absent.
    """
    violations = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    # Load TAHOT morph alignment for this chapter (None if morph file absent).
    chapter_morph = MA.load_chapter_morph(path)

    # Build a lookup: file_line_index (0-based) → [tag_list_per_token]
    # tag_list_per_token[tok_idx] = list[str] (TAHOT tags for that token)
    line_token_tags: dict[int, list[list[str]]] = {}
    if chapter_morph is not None:
        verse_groups = _partition_into_verses(lines)
        for verse_num, verse_numbered_lines in verse_groups:
            content = [
                (ln, raw) for ln, raw in verse_numbered_lines
                if not is_skippable(raw)
            ]
            if not content:
                continue
            ortho_tags = chapter_morph.get(verse_num)
            if ortho_tags is None:
                continue
            verse_text_lines = [raw for _, raw in content]
            aligned = MA.align_verse_tokens_to_tags(verse_text_lines, ortho_tags)
            if aligned is None:
                continue
            for ci, (ln, _raw) in enumerate(content):
                # ln is 1-based; store at 0-based index
                line_token_tags[ln - 1] = aligned[ci]

    def _tag_list_for(line_idx: int, tok_idx: int) -> "list[str] | None":
        """Return TAHOT tag list for (line_idx, tok_idx), or None on miss."""
        tl = line_token_tags.get(line_idx)
        if tl is None:
            return None
        if tok_idx < 0 or tok_idx >= len(tl):
            return None
        return tl[tok_idx]

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        line_no = i + 1  # 1-based

        # Check if this line ends with a compound preposition
        token = _last_token(line)
        if token is None:
            continue

        bare = strip_points(token)

        # --- Tag-aware preposition check ---
        # Primary path: use TAHOT tag via M.is_bare_prep_token.
        #   - Returns True  → token is a standalone bare prep (tag chain ["R"]);
        #                     the prep IS stranded — proceed to violation check.
        #   - Returns False → token has a pronominal suffix, is not a prep, or is
        #                     otherwise not bare-stranded; skip this line.
        # Skel-fallback (tag absent): skeleton membership in COMPOUND_PREP_SKELETONS
        # (preserves prior behaviour; covers בלתי and other non-PREP_SKELETONS items).
        raw_tokens = line.rstrip().split()
        last_tok_idx = len(raw_tokens) - 1 if raw_tokens else -1
        tag_list = _tag_list_for(i, last_tok_idx)

        if tag_list is not None:
            # Tag-driven path — authoritative
            if not M.is_bare_prep_token(token, tag_list=tag_list):
                continue
        else:
            # Skel-fallback — check skeleton membership
            if bare not in COMPOUND_PREP_SKELETONS:
                continue

        # Check if there's a next non-empty line (scan forward past skippable lines)
        next_line_idx = i + 1  # 0-based
        next_line = None
        next_line_no = None
        for j in range(next_line_idx, len(lines)):
            if not is_skippable(lines[j]):
                next_line = lines[j]
                next_line_no = j + 1  # 1-based
                break

        if next_line is None:
            # No next content line; preposition at EOF — not our concern
            continue

        # Does the next line look like it could be the object NP?
        if not is_noun_phrase_start(next_line):
            continue

        # We have a bare compound preposition at line end followed by a potential NP
        violations.append(
            {
                "file": path.name,
                "file_path": path,
                "line_num": line_no,
                "rule": "L1/compound-prep-object",
                "brief": f"stranded compound preposition at line end: {token!r}",
                "line": line.rstrip(),
                "next_line_num": next_line_no,
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
