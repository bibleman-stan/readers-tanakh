#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate relative-pronoun stranding from noun-phrase head.

Pattern: Relative pronoun (אֲשֶׁר / שֶׁ- prefix) stranded from its head NP.

Trigger: Line ends with NP; next line begins with אֲשֶׁר / שֶׁ- + relative-clause body.

Severity: REVIEW-REQUIRED — short relative clauses MAY merge upward per justification 5
(canon §5 H9), but long ones stay separate. The validator surfaces candidates; the editor
judges merge vs. separate per the three forces (generative, subtractive, diagnostic).

Architectural constraint: No te'amim in predicates.

Output format:
    [DEVIATION]  file:line  relative-pronoun-strand  REVIEW-REQUIRED  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_relative_pronoun_strand.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_relative_pronoun_strand.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_relative_pronoun_strand.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_relative_pronoun_strand.py --json
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
# U+05C4–U+05C5, U+05C7).  Strip both.
HEBREW_POINTS_RE = re.compile(r"[֑-ׇֽֿׁׂׅׄ]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"  # ׃
# Maqqef (orthographic word-joiner)
MAQQEF = "־"     # ־

# Hebrew letters used in predicates
SHIN = "ש"
AYIN = "ע"


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
    """Return the book directory name (e.g. '01-genesis')."""
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


def prosodic_word_count(line: str) -> int:
    """Count prosodic words.

    Whitespace-delimited tokens, with maqqef-joined groups counted as one
    prosodic word (canon §5 H1).
    """
    return len(content_tokens(line))


def first_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[0] if toks else None


def last_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[-1] if toks else None


# ---------------------------------------------------------------------------
# Noun-phrase detection (line-ending heuristic)
# ---------------------------------------------------------------------------

# Noun morphology: singular and plural forms, construct forms, absolute forms.
# This is a conservative heuristic that detects lines likely ending in an NP.
# We do NOT require certainty — the line-ending with a pronoun or common noun
# is sufficient.

DEFINITE_ARTICLE_MARKERS = {"ה", "הּ"}  # definite article or articles with dagesh
CONSTRUCT_MARKERS = {"י", "ת", "ן", "ם"}  # construct-like endings (but overlap with verb suffixes)
COMMON_NOUN_ENDINGS = {"ים", "ות", "ות", "יים"}  # plural noun endings


def looks_like_noun(bare: str) -> bool:
    """Heuristic: does this bare consonant skeleton look like a noun?

    Rough checks:
      - NOT starting with obvious finite-verb prefix patterns
      - Likely noun patterns: plural endings (ים, ות), or length ≥ 3 + no verb skeleton
    """
    if not bare or len(bare) < 2:
        return False

    # Exclude obvious finite-verb patterns
    # Wayyiqtol: וי / ות / וא / ונ at start
    if bare.startswith(("וי", "ות", "וא", "ונ")):
        return False
    # Yiqtol patterns: יX, תX, אX, נX + verb skeleton
    YIQTOL_PREFIXES = ("יא", "יה", "יב", "יל", "יע", "יק", "יר", "יש", "יד", "יז", "יכ", "יס", "יפ", "יכ")
    if any(bare.startswith(p) for p in YIQTOL_PREFIXES):
        return False

    # Plural noun endings
    for ending in COMMON_NOUN_ENDINGS:
        if bare.endswith(ending):
            return True

    # Short frequent nouns
    SHORT_NOUNS = {"בן", "בת", "אב", "אם", "אח", "אד", "אדם", "אל", "אלהים",
                   "יום", "ערב", "בוקר", "לילה", "עת", "אנוש", "אדום", "מלך",
                   "עבד", "משה", "אברהם", "יצחק", "יעקב", "גדול", "קטן"}
    if bare in SHORT_NOUNS:
        return True

    # Default: conservative — don't flag unless confidence is high
    return False


def line_ends_with_np(line: str) -> bool:
    """Heuristic: does `line` plausibly end with a noun phrase?

    Checks the last content token's consonant skeleton.  If it looks like a
    noun (by conservative heuristics), return True.
    """
    last = last_content_token(line)
    if not last:
        return False
    bare = strip_points(last).rstrip(SOF_PASUQ)
    return looks_like_noun(bare)


# ---------------------------------------------------------------------------
# Relative pronoun detection (line-initial heuristic)
# ---------------------------------------------------------------------------

# Relative pronouns / relative complementizers in Hebrew:
#   אֲשֶׁר (asher)       — classical relative (attaches postpositively to head noun)
#   שֶׁ-               — construct-relative (shewa + verbal form) — prefix to head of clause
#   מִי (mi)            — interrogative pronoun used as relative (rare pattern)
#   מָה (mah)           — interrogative pronoun used as relative (rare pattern)

ASHER_SKELETON = "אשר"


def starts_with_asher(line: str) -> bool:
    """True if the line begins with אֲשֶׁר (asher, relative pronoun)."""
    first = first_content_token(line)
    if not first:
        return False
    bare = strip_points(first)
    return bare == ASHER_SKELETON


def starts_with_she_prefix(line: str) -> bool:
    """True if the line begins with שֶׁ- construct-relative prefix.

    Pattern: token starts with ש, followed immediately by a consonant.
    Minimum length 3 to avoid matching pure particles like שָׁם (there).
    We check the niqqud-stripped form: after removing te'amim, token[0] is
    ש and token[1] exists.  The vowel under ש (should be shewa for
    construct-relative) is not visible after stripping points, so we rely
    on the form starting with ש + consonant in the skeleton.
    """
    first = first_content_token(line)
    if not first:
        return False
    bare = strip_points(first)
    # Pattern: ש followed by at least 2 more consonants (construct-relative
    # introduces a verb or participle: שׁ + root)
    if len(bare) >= 3 and bare[0] == SHIN:
        # Simple heuristic: not a pure locative/temporal marker
        # (שׁם = there, שׁנה = year, שׁנַיִם = two years)
        if bare not in ("שם", "שמה", "שנה", "שנים", "שנים"):
            return True
    return False


def starts_with_relative_pronoun(line: str) -> bool:
    """True if the line begins with a relative pronoun or complementizer."""
    return starts_with_asher(line) or starts_with_she_prefix(line)


# ---------------------------------------------------------------------------
# Verse partitioning (cross-verse boundary guard)
# ---------------------------------------------------------------------------

def partition_into_verses(lines: list[str]) -> list[tuple[int | None, int | None, list[int]]]:
    """Group line indices by verse.

    Returns a list of (chapter, verse, [line_indices]) tuples in source order.
    """
    verses: list[tuple[int | None, int | None, list[int]]] = []
    cur_chapter: int | None = None
    cur_verse: int | None = None
    cur_indices: list[int] = []
    for i, line in enumerate(lines):
        ref = parse_verse_ref(line)
        if ref is not None:
            # Flush current
            if cur_indices:
                verses.append((cur_chapter, cur_verse, cur_indices))
            cur_chapter, cur_verse = ref
            cur_indices = []
            continue
        if not line.strip():
            continue
        cur_indices.append(i)
    if cur_indices:
        verses.append((cur_chapter, cur_verse, cur_indices))
    return verses


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
    verses = partition_into_verses(lines)

    # Build a lookup: line_index → (chapter, verse)
    line_to_verse: dict[int, tuple[int | None, int | None]] = {}
    for ch, vs, indices in verses:
        for idx in indices:
            line_to_verse[idx] = (ch, vs)

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        # Determine verse context
        v_ctx = line_to_verse.get(i)
        chapter = v_ctx[0] if v_ctx else chapter_from_file
        verse = v_ctx[1] if v_ctx else None

        # Guard: poetic register — different rules apply in poetry
        if chapter is not None and is_poetic_register(book, chapter, verse):
            continue

        line_no = i + 1  # 1-based

        # Guard: does this line end with NP?
        if not line_ends_with_np(line):
            continue

        # Find next content line in the SAME verse (no cross-verse fire)
        next_idx: int | None = None
        for j in range(i + 1, len(lines)):
            if is_skippable(lines[j]):
                continue
            # Same verse?
            n_ctx = line_to_verse.get(j)
            if v_ctx and n_ctx and (n_ctx[0], n_ctx[1]) != (v_ctx[0], v_ctx[1]):
                break
            next_idx = j
            break

        if next_idx is None:
            continue

        next_line = lines[next_idx]
        next_line_no = next_idx + 1

        # Guard: does next line start with relative pronoun?
        if not starts_with_relative_pronoun(next_line):
            continue

        # Guard: combined ≤ 12 prosodic words (relative clauses can be long;
        # over 12 words combined is likely not a short merge candidate)
        combined_words = prosodic_word_count(line) + prosodic_word_count(next_line)
        # NOTE: canon §5 H9 says "short relative clauses MAY merge"; no hard cutoff
        # given, but 12 is a reasonable upper bound. This is informational; the
        # finding is emitted regardless, and the editor judges.

        prior_text = line.strip()
        next_text = next_line.strip()

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "relative-pronoun-strand",
            "severity": "REVIEW-REQUIRED",
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "prior_line": prior_text,
            "next_line": next_text,
            "prosodic_word_count": combined_words,
            "brief": (
                f"relative pronoun stranded from NP head — {prior_text} // {next_text} "
                f"({combined_words} prosodic words combined)"
            ),
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
                "book": f["book"],
                "chapter": f["chapter"],
                "verse": f["verse"],
                "prior_line": f["prior_line"],
                "next_line": f["next_line"],
                "next_line_num": f["next_line_num"],
                "prosodic_word_count": f["prosodic_word_count"],
            })

        counts = {"REVIEW-REQUIRED": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        doc = {
            "validator": "validate_relative_pronoun_strand",
            "rule": "relative-pronoun-strand",
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
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output ---
    print("=" * 72)
    print(f"Relative Pronoun Strand validator — Tanakh {tier_label}")
    print(f"Pattern: relative pronoun (אֲשֶׁר / שֶׁ-) stranded from NP head")
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
                print(f"    {f['prior_line'][:120]}")
                print(f"    → {f['next_line'][:120]}")
                print()
    else:
        print("No findings. Relative-pronoun stranding is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
