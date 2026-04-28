#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate אַשְׁרֵי-formula macarism (classical commata opening).

Structural Justification 4 — Classical Commata (canon §5):
An אַשְׁרֵי-formula macarism opening—a line that ends with אַשְׁרֵי (or אַשְׁרֵי-NP)
followed by a line beginning with content (relative clause, predicate)—MAY stand alone
as classical-comma per justification 4. However, in Masoretic tradition, the macarism
opening is frequently stranded from its content by the te'amim-derived v1-baseline cola.

This validator surfaces these splits as REVIEW-REQUIRED candidates. The editor decides
whether to:
  1. Preserve the macarism as a standalone classical-comma opening (justification 4)
  2. Merge it with the content for a tighter predication

ARCHITECTURAL CONSTRAINT — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. The te'amim
Unicode range (U+0591–U+05AF) does NOT appear in any predicate that decides
whether to fire a finding. Te'amim MAY appear in finding annotations as
informational defensibility-capture (Rule H8) — the trigger must remain syntactic.

SEVERITY:
All findings emit at severity REVIEW-REQUIRED. The macarism is permitted by structure
(classical-comma pattern exists per canon §4 / canon §5) but the isolation may or may
not be intentional. Editor review required.

SCOPE:
The הפעם operator אַשְׁרֵי appears in:
  - Psalms (many occurrences, but Psalms = Sifrei Emet = skipped via poetic_register guard)
  - Deuteronomy 33:29 (Deut 33 blessing, PROSE register)
  - 1 Kings 10:8 (Sheba visit blessing, PROSE register)

This validator checks PROSE registers only. Sifrei Emet אַשְׁרֵי occurrences are skipped.

Output format:
    [DEVIATION]  file:line  macarism-opening-split  REVIEW-REQUIRED  pattern  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_macarism.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_macarism.py --book deuteronomy
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_macarism.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_macarism.py --json
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

# Make _shared importable when this script is run as __main__.
sys.path.insert(0, str(REPO_ROOT / "validators"))
from _shared.poetic_register import is_poetic_register  # noqa: E402

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers
# ---------------------------------------------------------------------------

# Hebrew points (cantillation U+0591–U+05AF + niqqud U+05B0–U+05BC, U+05C1–U+05C2,
# U+05C4–U+05C5, U+05C7).  This regex covers the full points range.
# Strip U+0591-U+05BD (cantillation + niqqud) and U+05BF, U+05C1-U+05C2, U+05C4-U+05C5, U+05C7
# while PRESERVING maqqef (U+05BE), paseq (U+05C0), and sof pasuq (U+05C3) so that
# compound prepositions, prosodic word boundaries, and verse ends remain visible.
HEBREW_POINTS_RE = re.compile(r"[֑-ׇֽֿׁׂׅׄ]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"  # ׃
# Maqqef (orthographic word-joiner)
MAQQEF = "־"     # ־

# The macarism opening word
ASHREI = "אשרי"  # consonant skeleton


def strip_points(token: str) -> str:
    """Return token with niqqud and te'amim stripped (consonant skeleton + sof pasuq + maqqef)."""
    return HEBREW_POINTS_RE.sub("", token)


# ---------------------------------------------------------------------------
# Verse-reference / blank line handling
# ---------------------------------------------------------------------------

VERSE_REF_RE = re.compile(r"^(\S+\s+)?\d+:\d+\s*$")


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


def last_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[-1] if toks else None


def first_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[0] if toks else None


def prosodic_word_count(line: str) -> int:
    """Count prosodic words (whitespace-delimited, with maqqef-joined groups counted as one)."""
    return len(content_tokens(line))


# ---------------------------------------------------------------------------
# Macarism detection
# ---------------------------------------------------------------------------

def line_ends_with_ashrei(line: str) -> bool:
    """True if the line's last content token is אַשְׁרֵי or אַשְׁרֵי-NP (macarism opening)."""
    last = last_content_token(line)
    if not last:
        return False
    bare = strip_points(last).rstrip(SOF_PASUQ)
    if bare == ASHREI:
        return True
    # אַשְׁרֵי-NP compound (maqqef-joined)
    if MAQQEF in bare:
        head = bare.split(MAQQEF, 1)[0]
        if head == ASHREI:
            return True
    return False


def line_begins_with_content(line: str) -> bool:
    """True if the line begins with non-formula content (not just another אַשְׁרֵי).

    A content line is one that starts with a relative clause, predicate, or
    substantive noun phrase (not a second macarism opening).
    """
    first = first_content_token(line)
    if not first:
        return False
    bare = strip_points(first)
    # Exclude lines that just repeat the macarism opening formula
    if bare in (ASHREI, ASHREI + SOF_PASUQ):
        return False
    return True


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    findings: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    book = book_name_from_path(path)
    chapter_from_file = chapter_from_path(path)

    # Build a lookup: line_index → (chapter, verse)
    line_to_verse: dict[int, tuple[int | None, int | None]] = {}
    for i, line in enumerate(lines):
        ref = parse_verse_ref(line)
        if ref is not None:
            ch, vs = ref
            line_to_verse[i] = (ch, vs)

    # Carry forward chapter/verse context as we scan
    cur_chapter: int | None = chapter_from_file
    cur_verse: int | None = None

    for i, line in enumerate(lines):
        if is_skippable(line):
            # Update verse context
            ref = parse_verse_ref(line)
            if ref is not None:
                cur_chapter, cur_verse = ref
            continue

        # Determine verse context from lookup or current state
        v_ctx = line_to_verse.get(i)
        if v_ctx:
            cur_chapter, cur_verse = v_ctx

        line_no = i + 1  # 1-based

        # --- Guard: poetic register (skip Psalms, Proverbs, Job 3:1–42:6) ---
        if cur_chapter is not None and is_poetic_register(book, cur_chapter, cur_verse):
            continue

        # --- Check if this line ends with אַשְׁרֵי macarism ---
        if not line_ends_with_ashrei(line):
            continue

        # --- Find next content line in the SAME verse (no cross-verse fire) ---
        next_idx: int | None = None
        for j in range(i + 1, len(lines)):
            if is_skippable(lines[j]):
                # Check if we've crossed into a different verse
                ref = parse_verse_ref(lines[j])
                if ref is not None and cur_verse is not None:
                    next_ch, next_vs = ref
                    if (next_ch, next_vs) != (cur_chapter, cur_verse):
                        # Crossed verse boundary; don't fire
                        break
                continue
            next_idx = j
            break

        if next_idx is None:
            continue

        next_line = lines[next_idx]
        next_line_no = next_idx + 1

        # --- Check if next line begins with content (not another אַשְׁרֵי formula) ---
        if not line_begins_with_content(next_line):
            continue

        # --- All checks passed; emit REVIEW-REQUIRED finding ---
        prior_text = line.strip()
        next_text = next_line.strip()

        combined_words = prosodic_word_count(line) + prosodic_word_count(next_line)
        pattern = "ashrei_formula_followed_by_content"
        brief = (
            f"אַשְׁרֵי-formula macarism opening stranded from content — "
            f"{prior_text[:80]} // {next_text[:80]}"
        )

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "macarism-opening-split",
            "severity": "REVIEW-REQUIRED",
            "pattern": pattern,
            "book": book,
            "chapter": cur_chapter,
            "verse": cur_verse,
            "prior_line": prior_text,
            "next_line": next_text,
            "prosodic_word_count": combined_words,
            "annotation": (
                "Macarism opening (אַשְׁרֵי) permits classical-comma pattern (justification 4). "
                "The opening MAY stand alone or merge with content — editor's choice per §5."
            ),
            "suggested_action": "Review: merge for tighter predication OR preserve for classical-comma effect",
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
    parser.add_argument("--v2", action="store_true", help="Scan v2/he (default if v1 missing).")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show context.")
    parser.add_argument("--json", action="store_true", help="Emit JSON document.")
    args = parser.parse_args()

    base_dir = V2_DIR if args.v2 else V1_DIR
    tier_label = "v2/he" if args.v2 else "v1/he-baseline"
    if not base_dir.exists():
        # Fall back to the other tier rather than failing — v1 may be absent.
        alt = V2_DIR if not args.v2 else V1_DIR
        if alt.exists():
            base_dir = alt
            tier_label = "v2/he" if alt is V2_DIR else "v1/he-baseline"
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
                "line": f["line_num"],
                "rule": f["rule"],
                "severity": f["severity"],
                "pattern": f["pattern"],
                "book": f["book"],
                "chapter": f["chapter"],
                "verse": f["verse"],
                "prior_line": f["prior_line"],
                "next_line": f["next_line"],
                "next_line_num": f["next_line_num"],
                "prosodic_word_count": f["prosodic_word_count"],
                "annotation": f["annotation"],
                "suggested_action": f["suggested_action"],
            })

        counts = {"REVIEW-REQUIRED": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        by_pattern: dict[str, int] = {}
        for f in findings_json:
            by_pattern[f["pattern"]] = by_pattern.get(f["pattern"], 0) + 1

        doc = {
            "validator": "validate_macarism",
            "rule": "macarism-opening-split",
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
                "by_pattern": by_pattern,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output ---
    print("=" * 72)
    print(f"Macarism Opening Validator — Tanakh {tier_label}")
    print(f"Reference: canon §5 justification 4 (classical commata)")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Findings      : {len(all_findings)}")

    by_pattern: dict[str, int] = {}
    for f in all_findings:
        by_pattern[f["pattern"]] = by_pattern.get(f["pattern"], 0) + 1
    if by_pattern:
        print()
        for pat, count in sorted(by_pattern.items()):
            print(f"  {pat}: {count}")
    print()

    if all_findings:
        for f in all_findings:
            print(
                f"[DEVIATION]  {f['file_rel']}:{f['line_num']}  "
                f"{f['rule']}  {f['severity']}  {f['pattern']}  {f['brief']}"
            )
            if args.verbose:
                print(f"    {f['prior_line'][:120]}")
                print(f"    → {f['next_line'][:120]}")
                print(f"    {f['annotation']}")
                print()
    else:
        print("No macarism-opening splits found. All אַשְׁרֵי formulas are handled cleanly.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
