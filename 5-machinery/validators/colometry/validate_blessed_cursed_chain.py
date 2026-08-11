#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate parallel-list uniformity in Deuteronomy 27-28 blessed/cursed chains.

Specialized validator for Deut 27:15-26 (curses) and Deut 28:3-6, 16-19
(blessings/curses condensed lists). Each אָרוּר (cursed) / בָּרוּךְ (blessed) frame
+ content should be one consolidated line, not fragmented across multiple lines.

PATTERN:
Within the named chapter ranges, when a line begins with אָרוּר or בָּרוּךְ,
all subsequent lines until the next אָרוּר/בָּרוּךְ frame are the same member's
content. The validator surfaces fragmentation patterns where a single blessed/
cursed member is split across 2+ lines without intervening frame markers.

SEVERITY:
STRONG-MERGE-CANDIDATE within Deut 27:15-26 and Deut 28:3-6, 16-19.

ARCHITECTURAL CONSTRAINT — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. The te'amim
Unicode range (U+0591–U+05AF) does NOT appear in any predicate that decides
whether to fire a finding. Te'amim MAY appear in finding annotations as
informational defensibility-capture.

Output format:
    [DEVIATION]  file:line  blessed-cursed-chain/list-uniformity  STRONG-MERGE-CANDIDATE  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_blessed_cursed_chain.py
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_blessed_cursed_chain.py --book deuteronomy
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_blessed_cursed_chain.py --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants — two-tier layout: v1/he-baseline + v2/heb
# ---------------------------------------------------------------------------
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


REPO_ROOT = _find_repo_root()
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files"  / "v2" / "heb"

# ---------------------------------------------------------------------------
# Shared morphology + morph-alignment helpers
# ---------------------------------------------------------------------------
# Make _shared importable when this script is run as __main__.
sys.path.insert(0, str(REPO_ROOT / "5-machinery/validators"))
from _shared import morphology as M  # noqa: E402
from _shared import morph_alignment as MA  # noqa: E402

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers
# ---------------------------------------------------------------------------

# Hebrew points (cantillation U+0591–U+05AF + niqqud U+05B0–U+05BC, U+05C1–U+05C2,
# U+05C4–U+05C5, U+05C7).  Strip U+0591-U+05BD and U+05BF, U+05C1-U+05C2, U+05C4-U+05C5, U+05C7
# while PRESERVING maqqef (U+05BE), paseq (U+05C0), and sof pasuq (U+05C3).
HEBREW_POINTS_RE = re.compile(r"[֑-ׇֽֿׁׂׅׄ]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"  # ׃

# Hebrew consonants for blessed/cursed frame markers
BLESSED_SKELETON = "ברוך"    # בָּרוּךְ
CURSED_SKELETON = "ארור"     # אָרוּר


def strip_points(token: str) -> str:
    """Return token with niqqud and te'amim stripped (consonant skeleton + sof pasuq + maqqef)."""
    return HEBREW_POINTS_RE.sub("", token)


# ---------------------------------------------------------------------------
# Verse-reference / blank line handling
# ---------------------------------------------------------------------------

VERSE_REF_RE = re.compile(r"^(\S+\s+)?\d+:\d+\s*$")
_VERSE_REF_SIMPLE_RE = re.compile(r"^\d+:\d+\s*$")


def is_skippable(line: str) -> bool:
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
# Verse-grouping helper (mirrors validate_speech_intro_framing.py)
# ---------------------------------------------------------------------------

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
        m = _VERSE_REF_SIMPLE_RE.match(s)
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
# Token helpers
# ---------------------------------------------------------------------------

def content_tokens(line: str) -> list[str]:
    """Split a line into tokens, dropping pure-sof-pasuq and verse-reference tokens."""
    out = []
    for tok in line.split():
        bare = strip_points(tok)
        if bare in ("", SOF_PASUQ):
            continue
        if re.match(r"^\d+:\d+$", bare):
            continue
        out.append(tok)
    return out


def first_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[0] if toks else None


def _is_adjective_or_participle_tag(tag_list: "list[str] | None") -> bool:
    """Return True if TAHOT tag confirms this token is adjective or qal passive participle.

    בָּרוּךְ and אָרוּר appear in TAHOT tagged as:
      - HVqsmsa — Verb, qal, suffix-conjugation (= qatal / QalPassPtcp), masc-sg-absolute
      - HAamsa  — Adjective, absolute, masc-sg-absolute (less common TAHOT rendering)

    The "s" in position 2 of the verb tag is TAHOT's suffix-conjugation code, which
    covers both qatal 3ms and qal-passive-participle used predicatively.

    When tags are absent, returns True so that skel-based detection controls.
    """
    if not tag_list:
        return True  # no tags → skel-only path
    from _shared import morph_tags as _MT
    for tag in reversed(tag_list):
        if not tag or tag == "[—]":
            continue
        chain = _MT.morpheme_chain(tag)
        if not chain:
            continue
        head = chain[-1]
        # Adjective (A...) OR qal-suffix-conjugation (Vqs...) — both valid for ברוך/ארור
        if head.startswith("A") or head.startswith("Vqs"):
            return True
        return False
    return True  # no parseable tag → allow skel


def line_starts_with_frame(line: str, first_tok_tags: "list[str] | None" = None) -> str | None:
    """Return frame marker ('blessed' or 'cursed') if line starts with בָּרוּךְ or אָרוּר.

    Tag-aware primary path: skeleton membership gates entry; TAHOT tag then
    confirms token is an adjective or qal passive participle (not a homograph
    verbal form). Falls back to skeleton-only when tags are absent.
    """
    first = first_content_token(line)
    if not first:
        return None
    bare = strip_points(first)
    if bare == BLESSED_SKELETON:
        if _is_adjective_or_participle_tag(first_tok_tags):
            return "blessed"
    if bare == CURSED_SKELETON:
        if _is_adjective_or_participle_tag(first_tok_tags):
            return "cursed"
    return None


# ---------------------------------------------------------------------------
# Scope definition: Deut 27:15-26, Deut 28:3-6, Deut 28:16-19
# ---------------------------------------------------------------------------

SCOPE_RANGES = {
    27: [(15, 26)],      # Deut 27:15-26 (curses)
    28: [(3, 6), (16, 19)],  # Deut 28:3-6 (blessings), 28:16-19 (curses)
}


def is_in_scope(chapter: int | None, verse: int | None) -> bool:
    """Return True if (chapter, verse) is within one of the scope ranges."""
    if chapter is None or verse is None:
        return False
    if chapter not in SCOPE_RANGES:
        return False
    ranges = SCOPE_RANGES[chapter]
    for (start, end) in ranges:
        if start <= verse <= end:
            return True
    return False


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    """Scan one Deuteronomy text file for blessed/cursed chain fragmentation.

    Uses TAHOT morph tags (via morph_alignment) when available to confirm that
    אָרוּר/בָּרוּךְ tokens are adjective/passive-participle forms, not homographic
    verbal forms. Falls back to skeleton-only heuristic when tags absent.
    """
    findings: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    book = book_name_from_path(path)
    chapter_from_file = chapter_from_path(path)

    # Only process Deuteronomy
    if "05-deuteronomy" not in book.lower() and "deuteronomy" not in book.lower():
        return findings

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

    def _first_tok_tags(line_idx: int) -> "list[str] | None":
        """Return TAHOT tag list for first token of line_idx, or None on miss."""
        tl = line_token_tags.get(line_idx)
        if tl is None or len(tl) == 0:
            return None
        return tl[0]

    # Build a lookup: line_index → (chapter, verse)
    line_to_verse: dict[int, tuple[int | None, int | None]] = {}
    current_chapter: int | None = None
    current_verse: int | None = None

    for i, line in enumerate(lines):
        ref = parse_verse_ref(line)
        if ref is not None:
            current_chapter, current_verse = ref
        line_to_verse[i] = (current_chapter, current_verse)

    # Partition lines by frame: group each frame + its content lines together
    frame_groups: list[tuple[int, str, list[int]]] = []  # (start_line_idx, frame_type, content_line_indices)

    i = 0
    while i < len(lines):
        line = lines[i]
        if is_skippable(line):
            i += 1
            continue

        # Check if this line is a frame marker (blessed/cursed)
        # Tag-aware: passes TAHOT tags for first token when available; skel fallback automatic.
        frame_type = line_starts_with_frame(line, first_tok_tags=_first_tok_tags(i))
        if frame_type is None:
            i += 1
            continue

        # Get verse context
        ch, vs = line_to_verse.get(i, (None, None))

        # Check if we're in scope
        if not is_in_scope(ch, vs):
            i += 1
            continue

        # Found a frame marker. Collect all content lines until the next frame marker
        frame_start = i
        content_indices = [i]
        i += 1

        while i < len(lines):
            if is_skippable(lines[i]):
                i += 1
                continue
            # Check if this line is another frame marker
            # Tag-aware: pass TAHOT tags for first token when available.
            if line_starts_with_frame(lines[i], first_tok_tags=_first_tok_tags(i)) is not None:
                # Next frame marker found; this content belongs to the previous frame
                break
            # This is a content line; include it
            content_indices.append(i)
            i += 1

        frame_groups.append((frame_start, frame_type, content_indices))

    # Now check for fragmentation within each frame group
    for frame_start_idx, frame_type, all_indices in frame_groups:
        # Separate the frame line from the content lines
        frame_line_idx = all_indices[0]
        content_line_indices = all_indices[1:]

        if len(content_line_indices) <= 1:
            # Only one content line after the frame, or none — no fragmentation
            continue

        # We have multiple content lines. Check if they should be on a single line.
        # In a parallel list (blessed/cursed chains), each member should be one line:
        # אָרוּר + [content] on a single line.
        # If content spans multiple lines, that's fragmentation.

        frame_line = lines[frame_line_idx]
        ch, vs = line_to_verse.get(frame_line_idx, (None, None))

        # Emit a STRONG-MERGE-CANDIDATE finding
        frame_text = frame_line.strip()[:80]
        content_text = " // ".join(lines[idx].strip()[:60] for idx in content_line_indices[:2])
        if len(content_line_indices) > 2:
            content_text += f" ... (+{len(content_line_indices) - 2} more lines)"

        brief = f"Frame '{frame_type}' at {ch}:{vs} line {frame_start_idx + 1} split across {len(content_line_indices) + 1} lines ({frame_text}) — content: {content_text}"

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": frame_start_idx + 1,
            "content_line_nums": [idx + 1 for idx in content_line_indices],
            "rule": "blessed-cursed-chain/list-uniformity",
            "severity": "STRONG-MERGE-CANDIDATE",
            "book": book,
            "chapter": ch,
            "verse": vs,
            "frame_type": frame_type,
            "frame_line": frame_text,
            "num_content_lines": len(content_line_indices),
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
        # Fall back to the other tier rather than failing — v1 may be absent.
        alt = V2_DIR if not args.v2 else V1_DIR
        if alt.exists():
            base_dir = alt
            tier_label = "v2/heb" if alt is V2_DIR else "v1/he-baseline"
        else:
            print(f"ERROR: neither {V1_DIR} nor {V2_DIR} found.", file=sys.stderr)
            sys.exit(2)

    # Always scan Deuteronomy only
    book_dir = resolve_book_dir(base_dir, "deuteronomy")
    files = sorted(book_dir.glob("deuteronomy-2[78].txt"))

    if not files:
        print(f"No Deut 27-28 files found under {book_dir}", file=sys.stderr)
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
                "line": f["line_num"],
                "content_lines": f["content_line_nums"],
                "rule": f["rule"],
                "severity": f["severity"],
                "book": f["book"],
                "chapter": f["chapter"],
                "verse": f["verse"],
                "frame_type": f["frame_type"],
                "frame_line": f["frame_line"],
                "num_content_lines": f["num_content_lines"],
            })

        counts = {"STRONG-MERGE-CANDIDATE": len(findings_json)}

        doc = {
            "validator": "validate_blessed_cursed_chain",
            "rule": "blessed-cursed-chain/list-uniformity",
            "version": "1.0.0",
            "layer": 3,
            "scope": "Deut 27:15-26, Deut 28:3-6, Deut 28:16-19",
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": findings_json,
            "counts": counts,
            "summary": {
                "total_findings": len(findings_json),
                "by_severity": counts,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output ---
    print("=" * 72)
    print(f"Blessed-Cursed Chain Uniformity validator — Tanakh {tier_label}")
    print("Scope: Deut 27:15-26, 28:3-6, 28:16-19 parallel lists")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Findings      : {len(all_findings)}")
    print()

    if all_findings:
        for f in all_findings:
            print(
                f"[DEVIATION]  {f['file_rel']}:{f['line_num']}  "
                f"{f['rule']}  {f['severity']}  {f['brief']}"
            )
            if args.verbose:
                print(f"    {f['frame_line']}")
                print(f"    Content lines: {f['content_line_nums']}")
                print()
    else:
        print("No findings. Blessed-cursed chain uniformity is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
