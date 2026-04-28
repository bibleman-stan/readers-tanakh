#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate interrogative clause splits — interrogative particle stranded from its clause.

Pattern: Line ends with an interrogative particle (הֲ-, אִם, מִי, מָה, מָתַי, אַיֵּה,
אֵיךְ, לָמָה, מַדּוּעַ). Next line begins with a verb or NP completing the question.

Severity:
  STRONG-MERGE-CANDIDATE — for short interrogative clauses (≤6 prosodic words combined).
  REVIEW-REQUIRED — for longer clauses.

ARCHITECTURAL CONSTRAINT — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. The te'amim
Unicode range (U+0591–U+05AF) does NOT appear in any predicate that decides
whether to fire a finding. Te'amim MAY appear in finding annotations as
informational defensibility-capture.

REGISTER SKIP:
Validators that should skip poetic registers use is_poetic_register(). This
validator calls it at Guard 1 to suppress false positives in Sifrei Emet and
embedded-poetry chapters.

Output format:
    [DEVIATION]  file:line  interrogative-clause-split  STRONG-MERGE-CANDIDATE/REVIEW-REQUIRED  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_interrogative_clause.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_interrogative_clause.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_interrogative_clause.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_interrogative_clause.py --json
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
# U+05C4–U+05C5, U+05C7).
HEBREW_POINTS_RE = re.compile(r"[֑-ׇֽֿׁׂׅׄ]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"  # ׃

# Maqqef (orthographic word-joiner)
MAQQEF = "־"     # ־

# Paseq (vertical bar disjunction)
PASEQ = "׀"      # ׀


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


def last_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[-1] if toks else None


# ---------------------------------------------------------------------------
# Interrogative particle detection
# ---------------------------------------------------------------------------

# Interrogative particles (consonant-only after stripping niqqud + te'amim)
# הֲ / הַ + prefix (often heh interrogative marker)
INTERROGATIVE_PARTICLES = {
    "ה",      # simple heh interrogative (treats as particle when word-final)
    "אם",     # אִם (often in question contexts)
    "מי",     # מִי (who)
    "מה",     # מָה (what)
    "מתי",    # מָתַי (when)
    "איה",    # אַיֵּה (where)
    "איך",    # אֵיךְ (how)
    "למה",    # לָמָה (why / not-what)
    "מדוע",   # מַדּוּעַ (why)
}

# Additional heh patterns — heh as interrogative prefix (common in prose)
# Examples: הִשְׁמַרְתָּ (did you guard), הַיָּשְׁבוּ (did they sit)
# Detection: word starts with heh + consonant + vowel pattern suggesting finite verb


def looks_like_interrogative_particle(bare: str) -> bool:
    """Heuristic: does this bare skeleton look like an interrogative particle?

    Matches:
      - Direct particles: מי, מה, מתי, איה, איך, למה, מדוע, אם
      - Bare heh (word-final or standalone): ה
    """
    if not bare:
        return False
    if bare in INTERROGATIVE_PARTICLES:
        return True
    # Bare heh as standalone interrogative marker (rare but valid)
    if bare == "ה" and len(bare) == 1:
        return True
    return False


def line_ends_with_interrogative_particle(line: str) -> tuple[bool, str | None]:
    """Check if line ends with an interrogative particle.

    Returns (True, particle_skeleton) if match, (False, None) otherwise.
    """
    last = last_content_token(line)
    if not last:
        return False, None
    bare = strip_points(last).rstrip(SOF_PASUQ)
    # Handle maqqef-bound particles: על־מי, אל־איה
    if MAQQEF in bare:
        bare = bare.split(MAQQEF)[-1]  # take the last segment
    if looks_like_interrogative_particle(bare):
        return True, bare
    return False, None


# ---------------------------------------------------------------------------
# Verb / NP detection for next line
# ---------------------------------------------------------------------------

# High-confidence finite-verb skeletons (same list as clause_nucleus_split)
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

WAYYIQTOL_PREFIXES = ("וי", "ות", "ונ", "וא")


def looks_like_finite_verb(bare: str) -> bool:
    """Heuristic: does this bare consonant skeleton look like a finite verb?"""
    if not bare:
        return False
    if bare in KNOWN_FINITE_VERB_SKELETONS:
        return True
    if bare.startswith(WAYYIQTOL_PREFIXES) and len(bare) >= 4 and bare not in ("ויהוה",):
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


def next_line_starts_with_verb_or_np(line: str) -> bool:
    """True if line begins with verb or NP content (completing the question).

    Conservative: returns True if the first token looks like a finite verb
    or is a noun-like word (not obviously a preposition or discourse particle).
    """
    first = first_content_token(line)
    if not first:
        return False
    bare = strip_points(first)
    if not bare:
        return False
    # Direct verb check
    if looks_like_finite_verb(bare):
        return True
    # Noun-phrase-like: not a preposition, not a discourse particle, not a
    # pronoun adverb. Accept most other content words.
    # Hard-exclude only known function words
    FUNCTION_WORDS = {
        "על", "אל", "מן", "עם", "תחת", "בין",
        "לפני", "אחרי", "מאחרי", "מלפני", "מפני", "מאת",
        "בעד", "נגד", "מעל", "מתחת", "בתוך", "מתוך",
        "הנה", "אף", "לכן", "ועתה", "אז", "עתה",
    }
    if bare not in FUNCTION_WORDS:
        return True
    return False


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

    # Build a lookup: line_index → (chapter, verse, position_within_verse, indices)
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

        # --- Check if line ends with interrogative particle ---
        ends_with_interrog, particle = line_ends_with_interrogative_particle(line)
        if not ends_with_interrog:
            continue

        # --- Find next content line in the SAME verse (no cross-verse fire) ---
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

        # --- Check if next line begins with verb or NP completing the question ---
        if not next_line_starts_with_verb_or_np(next_line):
            continue

        # --- Determine severity based on combined prosodic word count ---
        combined_words = prosodic_word_count(line) + prosodic_word_count(next_line)
        if combined_words <= 6:
            severity = "STRONG-MERGE-CANDIDATE"
        else:
            severity = "REVIEW-REQUIRED"

        # --- Emit finding ---
        prior_text = line.strip()
        next_text = next_line.strip()
        brief = (
            f"interrogative particle '{particle}' stranded from completing clause — "
            f"{prior_text} // {next_text} "
            f"({combined_words} prosodic words combined)"
        )

        annotation = (
            f"Interrogative particle '{particle}' (הֲ-, אִם, מִי, מָה, מָתַי, אַיֵּה, אֵיךְ, "
            f"לָמָה, מַדּוּעַ) stranded from its clause. Next line begins with verb or NP completing "
            f"the question. Merge candidate for short interrogative clauses (≤6 words combined)."
        )

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "interrogative-clause-split",
            "severity": severity,
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "prior_line": prior_text,
            "next_line": next_text,
            "particle": particle,
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
                "particle": f["particle"],
                "prior_line": f["prior_line"],
                "next_line": f["next_line"],
                "next_line_num": f["next_line_num"],
                "prosodic_word_count": f["prosodic_word_count"],
                "annotation": f["annotation"],
            })

        counts = {"STRONG-MERGE-CANDIDATE": 0, "REVIEW-REQUIRED": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        doc = {
            "validator": "validate_interrogative_clause",
            "rule": "interrogative-clause-split",
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
    print(f"Interrogative Clause Split validator — Tanakh {tier_label}")
    print("Reference: interrogative particle stranded from its clause")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Findings      : {len(all_findings)}")

    severity_counts = {}
    for f in all_findings:
        sev = f["severity"]
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
    if severity_counts:
        print()
        for sev, count in sorted(severity_counts.items()):
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
        print("No findings. Interrogative clauses are clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
