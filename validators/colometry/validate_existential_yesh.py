#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate existential יֵשׁ (there is/are) + subject NP split.

Pattern: יֵשׁ (positive existential) followed by a subject noun phrase that begins
on the NEXT line.

Severity: STRONG-MERGE-CANDIDATE.

Rationale (per canon §5 H18.1 precedent, non-core-predication extenson):
A positive existential יֵשׁ with its associated subject is a verbless-clause nucleus:
יֵשׁ alone is the existential predicate; the NP is the subject. This is Hebrew's
standard way to say "there is X" or "X exists". The yesh + subject forms a single
atomic thought-unit; split across lines, the NP stranded without its predicate is
cognitively incomplete until united. This is a STRONG-MERGE candidate per the
same reasoning that justifies H18.1 (verbless subject + predicate).

Architectural Constraint — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. Te'amim (U+0591–U+05AF)
do NOT appear in any trigger predicate. Te'amim MAY appear in annotations as
defensibility-capture.

FORCED-NO-MERGE GUARDS (skip BEFORE emitting):
  1. Poetic register — is_poetic_register(book, chapter, verse) → skip.
  2. Next line is not a valid subject NP start (e.g. verb-opening, prep-opening).
  3. Line-after-candidate-second contains a resumptive pronoun (H15 casus pendens).
  4. Heavy subject — construct chain ≥3 deep, or complex relative/interrogative modifier.

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_existential_yesh.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_existential_yesh.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_existential_yesh.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_existential_yesh.py --json
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

# Hebrew letters
ALEPH = "א"
BET = "ב"
GIMEL = "ג"
DALET = "ד"
HE = "ה"
VAV = "ו"
ZAYIN = "ז"
CHET = "ח"
TET = "ט"
YOD = "י"
KAPH = "כ"
LAMED = "ל"
MEM = "מ"
NUN = "נ"
SAMECH = "ס"
AYIN = "ע"
PE = "פ"
TSADE = "צ"
QOPH = "ק"
RESH = "ר"
SHIN = "ש"
TAV = "ת"

# Niqqud individual marks
HOLAM = "ֹ"        # ֹ
SHEVA = "ְ"        # ְ
PATAH = "ַ"        # ַ
QAMATS = "ָ"       # ָ
HIRIQ = "ִ"        # ִ
QUBUTS = "ֻ"       # ֻ
TSERE = "ֵ"        # ֵ
SEGOL = "ֶ"        # ֶ
DAGESH = "ּ"       # ּ


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
    """Count prosodic words (whitespace-delimited tokens with maqqef groups as one)."""
    return len(content_tokens(line))


def first_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[0] if toks else None


def last_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[-1] if toks else None


# ---------------------------------------------------------------------------
# Existential יֵשׁ detection
# ---------------------------------------------------------------------------

# The existential יֵשׁ bare skeleton (consonants only after stripping points)
YESH_SKELETON = "יש"  # יֵשׁ → י + ש after stripping


def line_ends_with_yesh(line: str) -> bool:
    """True if the line ends with יֵשׁ (possibly stranded)."""
    last = last_content_token(line)
    if not last:
        return False
    bare = strip_points(last).rstrip(SOF_PASUQ)
    # Match just יש as the final token, or יש as the entire line content
    return bare == YESH_SKELETON


# ---------------------------------------------------------------------------
# Subject NP heuristics
# ---------------------------------------------------------------------------

# Common noun markers and open-class NP starters
# A line starts with a subject NP if:
#  1. First token is not a finite verb or preposition
#  2. First token has consonant skeleton that could be a noun
#  3. Not a known closed-class marker

KNOWN_FINITE_VERBS = {
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
    # yiqtol
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
    # imperatives
    "שמעו", "ראו", "לכו", "קומו", "עשו",
    "לך", "קום", "בא", "קח", "תן",
}

STANDALONE_PREPS = {
    "על", "אל", "מן", "עם", "תחת", "בין",
    "לפני", "אחרי", "מאחרי", "מלפני", "מפני", "מאת",
    "בעד", "נגד", "מעל", "מתחת", "בתוך", "מתוך",
}


def line_starts_with_subject_np(line: str) -> bool:
    """Heuristic: does this line begin with a plausible subject NP?

    True if:
      - First token is NOT a finite verb (high confidence)
      - First token is NOT a standalone preposition (which introduces PP, not NP)
      - First token is NOT a known closed-class marker
      - First token's consonant skeleton is ≥2 consonants (likely noun)
    """
    first = first_content_token(line)
    if not first:
        return False
    bare = strip_points(first).rstrip(SOF_PASUQ)
    if not bare or len(bare) < 2:
        return False

    # Reject finite verbs
    if bare in KNOWN_FINITE_VERBS:
        return False

    # Reject standalone prepositions
    if bare in STANDALONE_PREPS:
        return False

    # Reject bound prep prefixes (ב/ל/כ/מ + noun) — these start with prep, not NP
    if bare[0] in (BET, LAMED, KAPH, MEM):
        # Could be a prep prefix; reject to be safe
        # (we want NP starters, not PP starters)
        return False

    # Reject known closed-class markers
    CLOSED_CLASS = {"היא", "הם", "הן", "הוא", "אתה", "את", "אתם", "אתן",
                    "אני", "אנחנו", "אנו", "זה", "זאת", "אלה", "אלו"}
    if bare in CLOSED_CLASS:
        return False

    # If we reach here, plausible NP start
    return True


# ---------------------------------------------------------------------------
# Heavy subject heuristic (forced-no-merge guard)
# ---------------------------------------------------------------------------

def line_has_heavy_subject(line: str) -> bool:
    """True if the line contains indicators of a heavy/complex subject.

    Indicators:
      - אשר (relative pronoun anywhere)
      - מי / מה (interrogative anywhere)
      - ≥2 בן/בת appositives
      - Construct chain ≥3 deep (maqqef count ≥2)
    """
    bares = [strip_points(t) for t in content_tokens(line)]
    if not bares:
        return False

    # אשר / מי / מה anywhere
    for b in bares:
        if b in ("אשר", "מי", "מה"):
            return True

    # ≥2 בן/בת appositives
    bn_count = sum(1 for b in bares if b in ("בן", "בת"))
    if bn_count >= 2:
        return True

    # Construct chain ≥3 deep (≥2 maqqef-joins = 3+ components)
    for tok in content_tokens(line):
        bare = strip_points(tok)
        if bare.count(MAQQEF) >= 2:
            return True

    return False


# ---------------------------------------------------------------------------
# H15 casus pendens — line-after-candidate-second contains 3rd-person suffix
# ---------------------------------------------------------------------------

SUFFIX_CONSONANT_TAILS_3P = ("הו", "הם", "הן")


def line_has_3p_pronominal_suffix(line: str) -> bool:
    """Approximation: any token ends with a 3p pronominal suffix pattern."""
    for tok in content_tokens(line):
        bare = strip_points(tok).rstrip(SOF_PASUQ)
        if not bare or len(bare) < 3:
            continue
        for tail in SUFFIX_CONSONANT_TAILS_3P:
            if bare.endswith(tail):
                return True
    return False


# ---------------------------------------------------------------------------
# Verse partitioning
# ---------------------------------------------------------------------------

def partition_into_verses(lines: list[str]) -> list[tuple[int | None, int | None, list[int]]]:
    """Group line indices by verse."""
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

        # Check: does this line end with יֵשׁ?
        if not line_ends_with_yesh(line):
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

        # --- Guard 1: poetic register ---
        if chapter is not None and is_poetic_register(book, chapter, verse):
            continue

        # --- Guard 2: next line does NOT start with subject NP ---
        if not line_starts_with_subject_np(next_line):
            continue

        # --- Guard 4: heavy subject on next line ---
        if line_has_heavy_subject(next_line):
            continue

        # --- Guard 3: H15 casus pendens (resumptive pronoun on line-after-next) ---
        nb1_idx: int | None = None
        for k in range(next_idx + 1, len(lines)):
            if is_skippable(lines[k]):
                continue
            n2_ctx = line_to_verse.get(k)
            if v_ctx and n2_ctx and (n2_ctx[0], n2_ctx[1]) != (v_ctx[0], v_ctx[1]):
                break
            nb1_idx = k
            break
        if nb1_idx is not None and line_has_3p_pronominal_suffix(lines[nb1_idx]):
            continue

        # --- All guards passed; emit STRONG-MERGE-CANDIDATE finding ---
        prior_text = line.strip()
        next_text = next_line.strip()
        combined_words = prosodic_word_count(line) + prosodic_word_count(next_line)

        brief = (
            f"existential יֵשׁ + subject NP — {prior_text} // {next_text} "
            f"({combined_words} prosodic words combined)"
        )

        annotation = (
            "Positive existential יֵשׁ (there is/are) + subject NP. "
            "Verbless-clause nucleus where יֵשׁ is the predicate and the NP is the subject. "
            "Comparable to H18.1 subject+predicate split (canon §5). "
            "Strong merge candidate per verbless-clause integrity."
        )

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "H18.1-ext/existential-yesh",
            "severity": "STRONG-MERGE-CANDIDATE",
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "prior_line": prior_text,
            "next_line": next_text,
            "prosodic_word_count": combined_words,
            "annotation": annotation,
            "suggested_action": "MERGE candidate per existential-clause integrity",
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
                "prior_line": f["prior_line"],
                "next_line": f["next_line"],
                "next_line_num": f["next_line_num"],
                "prosodic_word_count": f["prosodic_word_count"],
                "annotation": f["annotation"],
                "suggested_action": f["suggested_action"],
            })

        counts = {"STRONG-MERGE-CANDIDATE": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        doc = {
            "validator": "validate_existential_yesh",
            "rule": "H18.1-ext/existential-yesh",
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
    print(f"Existential יֵשׁ Validator — Tanakh {tier_label}")
    print(f"Reference: canon §5 H18.1 extension (existential clause integrity)")
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
                print(f"    {f['annotation']}")
                print()
    else:
        print("No findings. No existential יֵשׁ splits detected.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
