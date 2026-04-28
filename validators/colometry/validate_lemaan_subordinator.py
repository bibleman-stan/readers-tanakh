#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate purpose subordinator stranding pattern (לְמַעַן).

Pattern: לְמַעַן (purpose subordinator, "in order that / so that / for the sake of")
appears at the end of a line; next line begins with finite verb or other purpose-clause
content. Stranded לְמַעַן should not be separated from its clause.

ARCHITECTURAL CONSTRAINT — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. The te'amim
Unicode range (U+0591–U+05AF) does NOT appear in any predicate that decides
whether to fire a finding. Te'amim MAY appear in finding annotations as
informational defensibility-capture (Rule H8) — the trigger must remain
syntactic.

VIOLATION PATTERN:
  A line ends with לְמַעַן (or לְמַעַן NP); the NEXT line begins with a finite verb
  or remainder of purpose clause content. The bond between subordinator and its
  clause should not be split.

SEVERITY:
  - STRONG-MERGE-CANDIDATE: Stranded לְמַעַן + single-word verb pattern (e.g.,
    "לְמַעַן // יִשְׁמְרוּ"). Conservative and high-confidence.
  - REVIEW-REQUIRED: Purpose clause is substantial (≥6 words on next line, or
    complex NP after לְמַעַן). Merge still appropriate but editor judgment warranted
    on clause boundary.

FORCED-NO-MERGE GUARDS (skip BEFORE emitting):
  1. Line ends at sof-pasuq (verse boundary) — subordinator at clause-end.
  2. Next line is poetic (Psalms, Proverbs, Job 3:1–42:6).
  3. Combined line length >8 prosodic words (guardrail against
     over-aggressive substantive-adjunct merging).

Output format:
    [DEVIATION]  file:line  lemaan-subordinator  SEVERITY  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_lemaan_subordinator.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_lemaan_subordinator.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_lemaan_subordinator.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_lemaan_subordinator.py --json
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_lemaan_subordinator.py --verbose
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
HEBREW_POINTS_RE = re.compile(r"[֑-ׇֽֿׁׂׅׄ]")


def strip_points(token: str) -> str:
    """Return token with all niqqud and te'amim stripped (consonant skeleton only)."""
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
    INSIDE a single whitespace-delimited token (Hebrew text uses no spaces
    around maqqef), each whitespace-delimited content token is already one
    prosodic word.
    """
    return len(content_tokens(line))


def last_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[-1] if toks else None


def first_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[0] if toks else None


# ---------------------------------------------------------------------------
# Finite-verb skeleton heuristic
# ---------------------------------------------------------------------------

# Strong wayyiqtol prefix (consonants only): tokens starting with וי, ות, וא, ונ
WAYYIQTOL_PREFIXES = ("וי", "ות", "ונ", "וא")

# Specific high-frequency finite-verb skeletons we recognize directly.
# These are consonant-only, post-strip.
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
    # Common yiqtol stems (3rd person, qal active).
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
}


def looks_like_finite_verb(bare: str) -> bool:
    """Heuristic: does this bare consonant skeleton look like a finite verb?"""
    if not bare:
        return False

    # Direct skeleton match
    if bare in KNOWN_FINITE_VERB_SKELETONS:
        return True

    # Wayyiqtol prefix (וי / ות / וא / ונ)
    if bare.startswith(WAYYIQTOL_PREFIXES):
        if len(bare) >= 4 and bare not in ("ויהוה",):
            return True

    # Maqqef-internal: take the last segment
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
    """Return a short informational summary of te'amim names present on `line`.

    INFORMATIONAL ONLY — never consulted by trigger predicates.
    """
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
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    """Scan one text file for לְמַעַן subordinator stranding violations."""
    findings: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    book = book_name_from_path(path)
    chapter_from_file = chapter_from_path(path)

    # Build verse lookup: line_index → (chapter, verse)
    line_to_verse: dict[int, tuple[int | None, int | None]] = {}
    for i, line in enumerate(lines):
        ref = parse_verse_ref(line)
        if ref is not None:
            cur_chapter, cur_verse = ref
            line_to_verse[i] = (cur_chapter, cur_verse)
    # Forward-fill: each content line gets the current verse context
    cur_chapter = chapter_from_file
    cur_verse = None
    for i, line in enumerate(lines):
        if i in line_to_verse:
            cur_chapter, cur_verse = line_to_verse[i]
        else:
            line_to_verse[i] = (cur_chapter, cur_verse)

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        # Get chapter and verse context
        chapter, verse = line_to_verse.get(i, (chapter_from_file, None))

        line_no = i + 1  # 1-based

        # --- Guard 1: line ends at sof-pasuq (verse boundary) ---
        stripped = line.rstrip()
        if stripped and stripped[-1] == SOF_PASUQ:
            continue

        # Find the last non-punctuation consonant skeleton on this line.
        last_tok = last_content_token(line)
        if last_tok is None:
            continue

        # Check if it's לְמַעַן (or למען with various pointing).
        # Strip points to consonant skeleton.
        skeleton = strip_points(last_tok).rstrip(SOF_PASUQ)
        if skeleton != "למען":
            continue

        # Find next non-empty content line
        next_idx: int | None = None
        for j in range(i + 1, len(lines)):
            if is_skippable(lines[j]):
                continue
            next_idx = j
            break

        if next_idx is None:
            continue

        next_line = lines[next_idx]
        next_line_no = next_idx + 1

        # --- Guard 2: next line is poetic register ---
        next_chapter, next_verse = line_to_verse.get(next_idx, (chapter_from_file, None))
        if next_chapter is not None and is_poetic_register(book, next_chapter, next_verse):
            continue

        # --- Compute prosodic word counts for guard 3 ---
        prior_word_count = prosodic_word_count(line)
        next_word_count = prosodic_word_count(next_line)
        combined_words = prior_word_count + next_word_count

        # --- Guard 3: combined > 8 prosodic words ---
        if combined_words > 8:
            continue

        # Determine severity
        next_has_verb = line_has_finite_verb(next_line)

        # STRONG-MERGE-CANDIDATE: next line is a single verb or verb + one/two args
        # Conservative: next line starts with verb AND is ≤4 words
        severity = "REVIEW-REQUIRED"  # default
        if next_has_verb and next_word_count <= 4:
            severity = "STRONG-MERGE-CANDIDATE"

        # Prepare annotation with te'amim summary (informational only)
        prior_teamim = teamim_summary(line)
        next_teamim = teamim_summary(next_line)
        teamim_note = ""
        if prior_teamim or next_teamim:
            teamim_note = (
                f" Te'amim placement: {prior_teamim or '(none)'} on prior line, "
                f"{next_teamim or '(none)'} on next line — informational only."
            )

        annotation = (
            f"Purpose subordinator לְמַעַן at line end; "
            f"next line contains purpose clause content. "
            f"Merge subordinator with clause.{teamim_note}"
        )

        prior_text = line.strip()
        next_text = next_line.strip()
        brief = (
            f"לְמַעַן stranded at line end; next line has purpose clause "
            f"({next_word_count} words)"
        )

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "lemaan-subordinator",
            "severity": severity,
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "prior_line": prior_text,
            "next_line": next_text,
            "prosodic_word_count": combined_words,
            "next_line_word_count": next_word_count,
            "next_has_verb": next_has_verb,
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
                "next_line_word_count": f["next_line_word_count"],
                "has_next_verb": f["next_has_verb"],
                "annotation": f["annotation"],
            })

        counts = {"REVIEW-REQUIRED": 0, "STRONG-MERGE-CANDIDATE": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        doc = {
            "validator": "validate_lemaan_subordinator",
            "rule": "lemaan-subordinator",
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
    print(f"Purpose Subordinator (לְמַעַן) validator — Tanakh {tier_label}")
    print("Pattern: לְמַעַן + clause as purpose subordinator")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Findings      : {len(all_findings)}")

    by_severity: dict[str, int] = {}
    for f in all_findings:
        by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1
    if by_severity:
        print()
        for sev, count in sorted(by_severity.items()):
            print(f"  {sev}: {count}")
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
                print(f"    {f['annotation']}")
                print()
    else:
        print("No findings. לְמַעַן subordinator stranding is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
