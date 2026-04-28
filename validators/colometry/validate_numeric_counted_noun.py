#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate numeric stranded from counted noun pattern.

Pattern: Numeral skeleton ends a line; counted noun (NP, often singular for >2 in Hebrew) begins the next line.

Severity: STRONG-MERGE-CANDIDATE for tight numeric+noun pair.

Numerals recognized (consonant skeletons after stripping niqqud/te'amim):
  Units 1–10: אחד, אחת, שנים, שתים, שלשה, שלש, ארבעה, ארבע, חמשה, חמש, ששה, שש, שבעה, שבע, שמנה, שמנה, תשעה, תשע, עשרה, עשר
  Tens: עשרים, שלשים, ארבעים, חמשים, שישים, שבעים, שמונים, תשעים
  Hundreds: מאה, מאות
  Thousands: אלף, אלפים
  10000s: רבבה

ARCHITECTURAL CONSTRAINT — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. The te'amim
Unicode range (U+0591–U+05AF) does NOT appear in any predicate that decides
whether to fire a finding. Te'amim MAY appear in finding annotations as
informational defensibility-capture — the trigger must remain syntactic.

FORCED-NO-MERGE GUARDS (skip BEFORE emitting):
  1. Poetic register — is_poetic_register(book, chapter, verse) → skip.
  2. Different verse — cross-verse merges forbidden.
  3. Next line has a finite verb — numeral+verb is a new clause, not just noun attachment.

Output format:
    [DEVIATION]  file:line  H11.extended/numeric-counted-noun  STRONG-MERGE-CANDIDATE  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_numeric_counted_noun.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_numeric_counted_noun.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_numeric_counted_noun.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_numeric_counted_noun.py --json
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
# while PRESERVING maqqef (U+05BE), paseq (U+05C0), and sof pasuq (U+05C3).
HEBREW_POINTS_RE = re.compile(r"[֑-ׇֽֿׁׂׅׄ]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"  # ׃
# Maqqef (orthographic word-joiner)
MAQQEF = "־"     # ־

# ---------------------------------------------------------------------------
# Numeral skeleton set (consonants only, post-strip)
# ---------------------------------------------------------------------------

NUMERAL_SKELETONS = {
    # Units 1–10
    "אחד", "אחת",
    "שנים", "שתים",
    "שלשה", "שלש",
    "ארבעה", "ארבע",
    "חמשה", "חמש",
    "ששה", "שש",
    "שבעה", "שבע",
    "שמנה", "שמנה",  # both spellings
    "תשעה", "תשע",
    "עשרה", "עשר",
    # Tens
    "עשרים",
    "שלשים",
    "ארבעים",
    "חמשים",
    "שישים",
    "שבעים",
    "שמונים",
    "תשעים",
    # Hundreds
    "מאה",
    "מאות",
    # Thousands
    "אלף",
    "אלפים",
    # 10,000s
    "רבבה",
}


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


def first_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[0] if toks else None


def last_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[-1] if toks else None


# ---------------------------------------------------------------------------
# Finite-verb heuristic (shared with clause_nucleus_split)
# ---------------------------------------------------------------------------

WAYYIQTOL_PREFIXES = ("וי", "ות", "ונ", "וא")

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
    "יאמר", "תאמר", "יאמרו", "תאמרו", "נאמר",
    "ישמע", "תשמע", "ישמעו",
    "יראה", "תראה", "יראו",
    "יבא", "תבא", "יבאו", "יקם",
    "יעשה", "תעשה", "יעשו",
    "ילך", "תלך", "ילכו",
    "יתן", "תתן", "יתנו", "אתן",
    "יקח", "תקח", "יקחו",
    "ידע", "תדע", "ידעו",
    "יזכר", "תזכר", "יזכרו",
    "שמעו", "ראו", "לכו", "קומו", "עשו",
    "לך", "קום", "בא", "קח", "תן",
}


def looks_like_finite_verb(bare: str) -> bool:
    """Heuristic: does this bare consonant skeleton look like a finite verb?"""
    if not bare:
        return False

    if bare in KNOWN_FINITE_VERB_SKELETONS:
        return True

    if bare.startswith(WAYYIQTOL_PREFIXES):
        if len(bare) >= 4 and bare not in ("ויהוה",):
            return True

    if MAQQEF in bare:
        for part in bare.split(MAQQEF):
            if not part:
                continue
            if part in KNOWN_FINITE_VERB_SKELETONS:
                return True
            if part.startswith(WAYYIQTOL_PREFIXES) and len(part) >= 4:
                return True

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

    # Build verse partitioning for cross-verse guard
    verse_lookup: dict[int, tuple[int | None, int | None]] = {}
    cur_chapter: int | None = None
    cur_verse: int | None = None
    for i, line in enumerate(lines):
        ref = parse_verse_ref(line)
        if ref is not None:
            cur_chapter, cur_verse = ref
        if not is_skippable(line):
            verse_lookup[i] = (cur_chapter, cur_verse)

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        # Determine verse context
        chapter, verse = verse_lookup.get(i, (chapter_from_file, None))
        line_no = i + 1  # 1-based

        # --- Find next content line in the SAME verse (no cross-verse fire) ---
        next_idx: int | None = None
        next_verse_ctx: tuple[int | None, int | None] | None = None
        for j in range(i + 1, len(lines)):
            if is_skippable(lines[j]):
                continue
            next_verse_ctx = verse_lookup.get(j)
            # Cross-verse check
            if verse_ctx := verse_lookup.get(i):
                if next_verse_ctx and next_verse_ctx != verse_ctx:
                    break
            next_idx = j
            break
        if next_idx is None:
            continue
        next_line = lines[next_idx]
        next_line_no = next_idx + 1

        # --- Guard 1: poetic register ---
        if chapter is not None and is_poetic_register(book, chapter, verse):
            continue

        # --- Guard 3: next line has a finite verb ---
        if line_has_finite_verb(next_line):
            continue

        # --- Check if current line ends with a numeral ---
        last_tok = last_content_token(line)
        if not last_tok:
            continue
        last_bare = strip_points(last_tok).rstrip(SOF_PASUQ)
        if last_bare not in NUMERAL_SKELETONS:
            continue

        # --- Check if next line starts with a noun (not finite verb, not preposition) ---
        first_tok = first_content_token(next_line)
        if not first_tok:
            continue
        first_bare = strip_points(first_tok)

        # Skip if next line starts with a finite verb (already checked above for safety)
        if looks_like_finite_verb(first_bare):
            continue

        # Skip if next line starts with a preposition (prep+noun is its own construct)
        if first_bare[0] in ("ב", "ל", "כ", "מ", "ע", "א") and len(first_bare) > 1:
            # Rough heuristic: preposition prefix. This is crude but avoids false positives.
            # More conservative: only skip if it looks like a clear prep pattern
            if first_bare[0] in ("מ", "ב", "ל", "כ"):
                # Likely a preposition; skip
                continue

        # --- Emit finding ---
        prior_text = line.strip()
        next_text = next_line.strip()

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "H11.extended/numeric-counted-noun",
            "severity": "STRONG-MERGE-CANDIDATE",
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "numeral": last_bare,
            "noun_start": first_bare,
            "prior_line": prior_text,
            "next_line": next_text,
            "brief": f"numeral + counted noun — {prior_text} // {next_text}",
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
        # Fall back to the other tier
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
                "numeral": f["numeral"],
                "noun_start": f["noun_start"],
                "prior_line": f["prior_line"],
                "next_line": f["next_line"],
                "next_line_num": f["next_line_num"],
            })

        counts = {"STRONG-MERGE-CANDIDATE": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        doc = {
            "validator": "validate_numeric_counted_noun",
            "rule": "H11.extended",
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
    print(f"Numeric Stranded from Counted Noun validator — Tanakh {tier_label}")
    print(f"Pattern: Line ends with numeral; next line begins with counted noun")
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
        print("No findings. All numerals are properly attached to counted nouns.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
