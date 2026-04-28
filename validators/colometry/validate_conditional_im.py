#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate conditional protasis-apodosis structure split.

Pattern: Line begins with אִם / לוּ / לוּלֵי (conditional particles); the protasis
spans to first finite verb; apodosis follows.

Trigger condition:
  Conditional particle (אִם, לוּ, לוּלֵי) at line start, protasis extends to first
  finite verb somewhere on the line, and apodosis continues on the next content line
  within the same verse.

Severity: REVIEW-REQUIRED — conditional structure often warrants protasis on own
line per justification 5 (atomicity within a major clause); merge only when both
parts ≤6 prosodic words combined.

ARCHITECTURAL CONSTRAINT — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. The te'amim
Unicode range (U+0591–U+05AF) does NOT appear in any predicate that decides
whether to fire a finding. Te'amim MAY appear in finding annotations as
informational defensibility-capture (Rule H8) — the trigger must remain syntactic.

Output format:
    [DEVIATION]  file:line  H20/conditional-split  REVIEW-REQUIRED  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_conditional_im.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_conditional_im.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_conditional_im.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_conditional_im.py --json
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

# Teamim-only regex (no niqqud) — used for accent scanning.
TEAMIM_ONLY_RE = re.compile(r"[֑-֯]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"  # ׃
# Maqqef (orthographic word-joiner)
MAQQEF = "־"     # ־
# Paseq (vertical bar disjunction)
PASEQ = "׀"      # ׀

# Hebrew letters used in heuristics
BET = "ב"
KAF = "כ"
LAMED = "ל"
MEM = "מ"

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
    prosodic word (canon §5 H1).  Since maqqef joins tokens orthographically
    INSIDE a single whitespace-delimited token, each whitespace-delimited
    content token is already one prosodic word.
    """
    return len(content_tokens(line))


def first_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[0] if toks else None


# ---------------------------------------------------------------------------
# Conditional particle detection
# ---------------------------------------------------------------------------

CONDITIONAL_PARTICLES = {
    "אם",      # אִם — if
    "לו",      # לוּ — if (conditional)
    "לולא",    # לוּלֵא / לוּלוֹ — if not, unless
    "לולי",    # לוּלֵי — if not
}


def line_starts_with_conditional(line: str) -> bool:
    """Return True if line's first content token is a conditional particle."""
    first = first_content_token(line)
    if not first:
        return False
    bare = strip_points(first)
    return bare in CONDITIONAL_PARTICLES


# ---------------------------------------------------------------------------
# Finite-verb skeleton heuristic (re-used from clause_nucleus_split)
# ---------------------------------------------------------------------------

# Strong wayyiqtol prefix (consonants only)
WAYYIQTOL_PREFIXES = ("וי", "ות", "ונ", "וא")

# Common qatal endings (consonant skeletons after te'amim stripped)
QATAL_SUFFIXES = (
    "תי",   # 1cs perfect
    "ת",    # 2ms (after strip)
    "נו",   # 1cp
    "תם",   # 2mp
    "תן",   # 2fp
    "ו",    # 3cp
)

# Specific high-frequency finite-verb skeletons we recognize directly.
KNOWN_FINITE_VERB_SKELETONS = {
    # Common qatal 3ms / 3fs / 3cp forms
    "אמר", "אמרה", "אמרו", "אמרתי", "אמרת", "אמרנו", "אמרתם",
    "ראה", "ראתה", "ראו", "ראיתי", "ראית", "ראינו",
    "שמע", "שמעה", "שמעו", "שמעתי", "שמענו",
    "ידע", "ידעה", "ידעו", "ידעתי", "ידעת", "ידענו",
    "ברא", "בראה", "בראו",
    "ברך", "ברכה", "ברכו", "ברכתי", "ברכת",
    "הלך", "הלכה", "הלכו", "הלכתי", "הלכנו",
    "נתן", "נתנה", "נתנו", "נתתי", "נתת",
    "עשה", "עשתה", "עשו", "עשיתי", "עשית", "עשינו",
    "היה", "היתה", "היו", "הייתי", "היית", "היינו",
    "בא", "באה", "באו", "באתי", "באת", "באנו",
    "קם", "קמה", "קמו", "קמתי", "קמנו",
    "בנה", "בנתה", "בנו", "בניתי",
    "לקח", "לקחה", "לקחו", "לקחתי",
    "כתב", "כתבה", "כתבו", "כתבתי",
    "כרת", "כרתה", "כרתו",
    "מצא", "מצאה", "מצאו", "מצאתי",
    "נשא", "נשאה", "נשאו", "נשאתי",
    "נפל", "נפלה", "נפלו", "נפלתי",
    "ישב", "ישבה", "ישבו", "ישבתי",
    "עבר", "עברה", "עברו",
    "אכל", "אכלה", "אכלו", "אכלתי",
    "שתה", "שתתה", "שתו",
    "מת", "מתה", "מתו", "מתי",
    "חיה", "חיתה", "חיו",
    "סר", "סרה", "סרו",
    "עלה", "עלתה", "עלו", "עליתי",
    "ירד", "ירדה", "ירדו",
    "שב", "שבה", "שבו", "שבתי",
    "הכה", "הכתה", "הכו",
    "הביא", "הביאה", "הביאו",
    "הוציא", "הוציאה", "הוציאו",
    "הגיד", "הגידה", "הגידו",
    "הציל", "הצילה", "הצילו",
    "צוה", "צותה", "צוו",
    "דבר", "דברה", "דברו",
    "פנה", "פנתה", "פנו",
    "נסע", "נסעה", "נסעו",
    # Common yiqtol stems
    "יאמר", "תאמר", "יאמרו", "תאמרו", "נאמר",
    "ישמע", "תשמע", "ישמעו",
    "יראה", "תראה", "יראו",
    "יבא", "תבא", "יבאו", "יקם",
    "יעשה", "תעשה", "יעשו",
    "ילך", "תלך", "ילכו",
    "יתן", "תתן", "יתנו", "אתן",
    "יקח", "תקח", "יקחו",
    "ישב", "תשב", "ישבו",
    "ידע", "תדע", "ידעו",
    "יזכר", "תזכר", "יזכרו",
    # Common imperatives
    "שמעו", "ראו", "לכו", "קומו", "עשו",
    "לך", "קום", "בא", "קח", "תן",
}


def looks_like_finite_verb(bare: str) -> bool:
    """Heuristic: does this bare consonant skeleton look like a finite verb?"""
    if not bare:
        return False

    # Direct skeleton match
    if bare in KNOWN_FINITE_VERB_SKELETONS:
        return True

    # Wayyiqtol prefix
    if bare.startswith(WAYYIQTOL_PREFIXES):
        if len(bare) >= 4 and bare not in ("ויהוה",):
            return True

    # Maqqef-internal
    if MAQQEF in bare:
        for part in bare.split(MAQQEF):
            if not part:
                continue
            if part in KNOWN_FINITE_VERB_SKELETONS:
                return True
            if part.startswith(WAYYIQTOL_PREFIXES) and len(part) >= 4:
                return True

    # Qatal-suffix sniff
    for suf in ("תי", "תם", "תן", "נו"):
        if bare.endswith(suf) and len(bare) >= 4:
            return True

    return False


def line_has_finite_verb(line: str) -> bool:
    """True if any content token on `line` looks like a finite verb."""
    for tok in content_tokens(line):
        bare = strip_points(tok)
        if looks_like_finite_verb(bare):
            return True
    return False


def find_first_finite_verb_position(line: str) -> int | None:
    """Return the index (0-based token position) of the first finite verb, or None."""
    toks = content_tokens(line)
    for idx, tok in enumerate(toks):
        bare = strip_points(tok)
        if looks_like_finite_verb(bare):
            return idx
    return None


# ---------------------------------------------------------------------------
# Te'amim annotation helper (informational only — NOT in trigger predicates)
# ---------------------------------------------------------------------------

_TEAMIM_NAME_BY_CHAR = {
    "֖": "tipha",
    "֔": "zaqef qatan",
    "֕": "zaqef gadol",
    "֨": "qadma",
    "֩": "telisha qetannah",
    "֫": "geresh",
    "֬": "geresh muqdam",
    "֠": "telisha gedolah",
    "֤": "pashta",
    "֙": "pashta",
    "֡": "darga",
    "֣": "munach",
    "֥": "merkha",
    "֦": "merkha kefulah",
    "֧": "darga",
    "֜": "geresh",
    "֝": "geresh muqdam",
    "֞": "gershayim",
    "֟": "qarne phara",
    "֑": "etnachta",
    "֒": "segol",
    "֓": "shalshelet",
    "֮": "zarka",
    "֭": "dehi",
    "֛": "tevir",
    "֢": "atnach hafukh",
    "֪": "yetiv",
    "֘": "zarka",
    "֗": "revia",
}


def teamim_summary(line: str) -> str:
    """Return a short informational summary of te'amim names present on `line`."""
    seen: list[str] = []
    for ch in line:
        if "֑" <= ch <= "֯":
            name = _TEAMIM_NAME_BY_CHAR.get(ch)
            if name and name not in seen:
                seen.append(name)
    if not seen:
        return ""
    return ", ".join(seen)


# ---------------------------------------------------------------------------
# Verse partitioning
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

    # Build a lookup: line_index → (chapter, verse, position_within_verse, verse_indices)
    line_to_verse: dict[int, tuple[int | None, int | None, int, list[int]]] = {}
    for ch, vs, indices in verses:
        for pos, idx in enumerate(indices):
            line_to_verse[idx] = (ch, vs, pos, indices)

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        # Determine verse context
        v_ctx = line_to_verse.get(i)
        chapter = v_ctx[0] if v_ctx else chapter_from_file
        verse = v_ctx[1] if v_ctx else None
        pos_in_verse = v_ctx[2] if v_ctx else 0
        verse_indices = v_ctx[3] if v_ctx else []

        line_no = i + 1  # 1-based

        # --- Guard 1: poetic register ---
        if chapter is not None and is_poetic_register(book, chapter, verse):
            continue

        # --- Trigger: line starts with conditional particle ---
        if not line_starts_with_conditional(line):
            continue

        # --- Find next content line in the SAME verse ---
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

        # --- Check: both lines < 8 prosodic words combined ---
        combined_words = prosodic_word_count(line) + prosodic_word_count(next_line)
        if combined_words > 8:
            continue

        # --- Check: protasis (current line) has a finite verb ---
        # If no finite verb in current line, this isn't a well-formed conditional
        if not line_has_finite_verb(line):
            continue

        # --- Check: apodosis (next line) does NOT have a finite verb ---
        # If next line also has a finite verb, it's apodosis + new clause
        if line_has_finite_verb(next_line):
            continue

        # --- Emit REVIEW-REQUIRED finding ---
        prior_text = line.strip()
        next_text = next_line.strip()

        prior_teamim = teamim_summary(line)
        next_teamim = teamim_summary(next_line)
        teamim_note = ""
        if prior_teamim or next_teamim:
            teamim_note = (
                f" Te'amim placement: {prior_teamim or '(none)'} on protasis, "
                f"{next_teamim or '(none)'} on apodosis — informational only."
            )

        annotation = (
            "Conditional protasis-apodosis structure (justification 5 — atomic clause)."
            + teamim_note
        )
        brief = (
            f"conditional: {prior_text[:80]} // {next_text[:80]} "
            f"({combined_words} prosodic words combined)"
        )

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "H20/conditional-split",
            "severity": "REVIEW-REQUIRED",
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "prior_line": prior_text,
            "next_line": next_text,
            "prosodic_word_count": combined_words,
            "annotation": annotation,
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
        # Fall back to the other tier rather than failing
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
                "annotation": f["annotation"],
            })

        counts = {"REVIEW-REQUIRED": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        doc = {
            "validator": "validate_conditional_im",
            "rule": "H20",
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
    print(f"Rule H20 Conditional-Split validator — Tanakh {tier_label}")
    print(f"Reference: conditional protasis-apodosis structure (אִם / לוּ / לוּלֵי)")
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
                print(f"    Protasis : {f['prior_line'][:120]}")
                print(f"    Apodosis : {f['next_line'][:120]}")
                print(f"    {f['annotation']}")
                print()
    else:
        print("No findings. Rule H20 conditional-split structure is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
