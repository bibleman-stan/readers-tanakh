#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate causal כִּי clause split — Layer 3 editorial pattern.

Pattern: Causal כִּי + clause split detection (distinct from H7 complement-כִּי).

Rule: Line ends with content; next line begins with כִּי + finite verb where כִּי is
causal ("because, for") rather than complement ("that"). Disambiguate: causal-כִּי
follows action/statement; complement-כִּי follows cognition/speech verb.

Trigger condition:
  - Prior line ends with some content (typically a transitive action verb, stative
    condition, or other statement)
  - Next line begins with כִּי (bare or with conjunction ו) + finite verb
  - כִּי is causal (semantic test: "because/for"), not complement (semantic test: "that")
  - The line split is mechanically driven by te'amim baseline but not justified by
    Hebrew syntax, complement integrity (H7 guard), or atomic-thought criteria

Severity: REVIEW-REQUIRED — causal-כִּי often justifies own line per generative
justification 5 (substantive adjunct), but editor must judge case-by-case.

Architectural constraint:
  - NO TE'AMIM IN PREDICATES — all trigger logic uses Hebrew morpho-syntactic
    patterns ONLY. Te'amim MAY appear in annotations (informational only).

Forced-skip guards:
  1. Prior line ends with cognition/speech verb (that makes next כִּי a complement-כִּי,
     H7 territory; skip).
  2. Prior line is itself a causal כִּי clause (avoid chaining causal clauses).
  3. Prior line ends in אֲשֶׁר (complement introducer, not action; skip).
  4. Next line's כִּי is maqqef-bound to a preceding noun (nominal appositive, not
     clause introducer; skip).
  5. Causal-כִּי construal fails the "single-image" test — when the prior statement
     and causal reason are tightly coupled semantically (not separable for mental-
     image purposes), it may belong on one line (diagnostic override; flag as
     REVIEW-REQUIRED).

Output format:
    [DEVIATION]  file:line  causal-kі-clause-split  REVIEW-REQUIRED  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_causal_ki.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_causal_ki.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_causal_ki.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_causal_ki.py --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants
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

# Hebrew points (cantillation U+0591–U+05AF + niqqud U+05B0–U+05BC,
# U+05C1–U+05C2, U+05C4–U+05C5, U+05C7). Strip these but PRESERVE maqqef,
# paseq, sof pasuq.
HEBREW_POINTS_RE = re.compile(r"[֑-ׇֽֿׁׂׅׄ]")

# Niqqud-only regex (no te'amim) — used for syntactic vowel inspection.
TEAMIM_ONLY_RE = re.compile(r"[֑-֯]")

# Sof pasuq, maqqef, paseq
SOF_PASUQ = "׃"
MAQQEF = "־"
PASEQ = "׀"

# Niqqud marks
SHEVA = "ְ"
PATAH = "ַ"
QAMATS = "ָ"
HIRIQ = "ִ"
SEGOL = "ֶ"
TSERE = "ֵ"
QUBUTS = "ֻ"
DAGESH = "ּ"

# Hebrew consonants
KAF = "כ"
LAMED = "ל"
MEM = "מ"
SHIN = "ש"


def strip_points(token: str) -> str:
    """Return token with niqqud and te'amim stripped (consonant skeleton + sof pasuq + maqqef)."""
    return HEBREW_POINTS_RE.sub("", token)


def strip_teamim_only(token: str) -> str:
    """Return token with te'amim stripped, niqqud preserved."""
    return TEAMIM_ONLY_RE.sub("", token)


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


def prosodic_word_count(line: str) -> int:
    """Count prosodic words (whitespace-delimited tokens)."""
    return len(content_tokens(line))


# ---------------------------------------------------------------------------
# Finite-verb detection (reused from H18 validator)
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
    # Yiqtol stems
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
    # Imperatives
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
# Cognition/speech verb detection (H7 complement context guard)
# ---------------------------------------------------------------------------

# High-confidence cognition/speech verbs that take obligatory כִּי-complement
# (per canon §5 H7 Rule). These are the matrix verbs that make next כִּי a
# complement (H7 territory), not causal.
COGNITION_SPEECH_VERBS = {
    # Cognition verbs
    "ידע", "ידעה", "ידעו", "ידעתי", "ידעת",     # know
    "הבין", "הבינה", "הבינו", "הבינתי",        # understand
    "זכר", "זכרה", "זכרו", "זכרתי",             # remember
    "ראה", "ראתה", "ראו", "ראיתי",              # see
    "שמע", "שמעה", "שמעו", "שמעתי",             # hear
    "חשב", "חשבה", "חשבו", "חשבתי",             # think
    # Speech verbs
    "אמר", "אמרה", "אמרו", "אמרתי", "אמרת",     # say
    "דבר", "דברה", "דברו", "דברתי",             # speak (piel)
    "קרא", "קראה", "קראו", "קראתי",             # call
    "צוה", "צותה", "צוו", "צויתי",              # command
    "אנה", "אנתה", "אנו", "אניתי",              # answer
    # Yiqtol + imperative forms of cognition/speech
    "ידע", "יידע", "תידע", "יידעו", "תידעו",
    "ידע", "וידע", "וידעה", "וידעו",
    "הבין", "יבין", "תבין", "יבינו", "תבינו",
    "זכר", "יזכר", "תזכר", "יזכרו", "תזכרו",
    "אמר", "יאמר", "תאמר", "יאמרו", "תאמרו",
    "דבר", "ידבר", "תדבר", "ידברו", "תדברו",
}


def line_ends_with_cognition_speech_verb(line: str) -> bool:
    """Guard 1: does prior line end with a cognition/speech verb?

    If yes, next כִּי is a complement (H7), not causal. Skip the finding.
    """
    last = last_content_token(line)
    if not last:
        return False
    bare = strip_points(last).rstrip(SOF_PASUQ)
    if bare in COGNITION_SPEECH_VERBS:
        return True
    # Also check with leading conjunction ו
    if bare.startswith("ו") and len(bare) > 1:
        if bare[1:] in COGNITION_SPEECH_VERBS:
            return True
    return False


# ---------------------------------------------------------------------------
# כִּי token detection and classification
# ---------------------------------------------------------------------------

def next_line_starts_with_ki_verb(line: str) -> tuple[bool, bool]:
    """Check if next line begins with כִּי + finite verb.

    Returns (True, is_v_consecutive) if pattern matches, (False, False) otherwise.
    is_v_consecutive is True if כִּי is preceded by vav-consecutive (וְכִּי).
    """
    first = first_content_token(line)
    if not first:
        return False, False
    bare = strip_points(first)
    if not bare:
        return False, False

    # Remove leading ו if present (conjunction)
    has_vav = False
    check_bare = bare
    if check_bare.startswith("ו"):
        has_vav = True
        check_bare = check_bare[1:]

    # Must start with כִּי (transliteration: kaf + yod after stripping points)
    if not check_bare.startswith("כי"):
        return False, False

    # The rest must be or look like nothing (bare כִּי) or be bound to it
    # (e.g., כִּיבֵית = כִּי + בֵית).  But we're looking for כִּי-clause
    # introducer, so the line should have a finite verb somewhere.
    if not line_has_finite_verb(line):
        return False, False

    return True, has_vav


def is_ki_noun_appositive(line: str) -> bool:
    """Guard 4: is כִּי on this line maqqef-bound to a preceding noun?

    E.g., דָּבָר־כִּי would be a noun appositive, not a clause introducer.
    This is rare but possible. Skip if found.
    """
    toks = content_tokens(line)
    if not toks:
        return False
    first_bare = strip_points(toks[0])
    # If first token ends with ־כִּי (maqqef-bound), it's an appositive
    if MAQQEF in first_bare:
        if first_bare.endswith("כי") or first_bare.endswith("כיו") or first_bare.endswith("כיה"):
            return True
    return False


# ---------------------------------------------------------------------------
# Causal vs. complement disambiguation (semantic test — flagged for review)
# ---------------------------------------------------------------------------

def could_be_causal_ki(prior_verb_bare: str | None) -> bool:
    """Heuristic: is prior_verb_bare a verb that takes CAUSAL כִּי rather than COMPLEMENT כִּי?

    Causal כִּי typically follows transitive action verbs, stative verbs, or
    statements that set up a reason/cause relationship.

    Complement כִּי typically follows cognition/speech verbs (ידע כִּי, אמר כִּי).

    This is a heuristic — the real test is semantic (cannot be done mechanically).
    We return True if prior_verb_bare is NOT in the cognition/speech list.
    If prior_verb_bare is None (no finite verb on prior line), we conservatively
    return True (the prior statement might justify causal כִּי on next line).
    """
    if prior_verb_bare is None:
        return True  # No verb on prior line — could be causal
    if prior_verb_bare in COGNITION_SPEECH_VERBS:
        return False  # Cognition/speech verb → complement כִּי
    # Any other verb → could be causal
    return True


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
# Te'amim annotation helper (informational only)
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

        line_no = i + 1  # 1-based

        # --- Find next content line in the SAME verse ---
        next_idx: int | None = None
        for j in range(i + 1, len(lines)):
            if is_skippable(lines[j]):
                continue
            n_ctx = line_to_verse.get(j)
            if v_ctx and n_ctx and (n_ctx[0], n_ctx[1]) != (v_ctx[0], v_ctx[1]):
                break
            next_idx = j
            break
        if next_idx is None:
            continue
        next_line = lines[next_idx]
        next_line_no = next_idx + 1

        # --- Guard: poetic register ---
        if chapter is not None and is_poetic_register(book, chapter, verse):
            continue

        # --- Trigger: does next line start with כִּי + finite verb? ---
        ki_with_verb, has_vav = next_line_starts_with_ki_verb(next_line)
        if not ki_with_verb:
            continue

        # --- Guard 1: prior line ends with cognition/speech verb ---
        # This makes next כִּי a complement (H7), not causal.
        if line_ends_with_cognition_speech_verb(line):
            continue

        # --- Guard 2: prior line is itself a causal כִּי clause ---
        # Avoid chaining causal clauses.
        first = first_content_token(line)
        if first:
            bare = strip_points(first)
            if bare.startswith("ו"):
                bare = bare[1:]
            if bare.startswith("כי"):
                continue

        # --- Guard 3: prior line ends in אֲשֶׁר ---
        # Complement introducer, not action verb → skip.
        last = last_content_token(line)
        if last:
            bare = strip_points(last).rstrip(SOF_PASUQ)
            if bare == "אשר" or bare.endswith("אשר" + MAQQEF):
                continue

        # --- Guard 4: כִּי is maqqef-bound noun appositive ---
        if is_ki_noun_appositive(next_line):
            continue

        # --- Semantic test: could be causal כִּי? ---
        # Extract last token's verb from prior line
        prior_verb_bare = None
        if last:
            prior_verb_bare = strip_points(last).rstrip(SOF_PASUQ)
            if prior_verb_bare.startswith("ו"):
                prior_verb_bare = prior_verb_bare[1:]

        if not could_be_causal_ki(prior_verb_bare):
            continue

        # --- All guards passed; emit REVIEW-REQUIRED finding ---
        prior_text = line.strip()
        next_text = next_line.strip()
        combined_words = prosodic_word_count(line) + prosodic_word_count(next_line)

        prior_teamim = teamim_summary(line)
        next_teamim = teamim_summary(next_line)
        teamim_note = ""
        if prior_teamim or next_teamim:
            teamim_note = (
                f" Te'amim placement: {prior_teamim or '(none)'} on prior line, "
                f"{next_teamim or '(none)'} on next line — informational only."
            )

        annotation = (
            f"Causal כִּי clause. Prior statement: {prior_text[:80]}; "
            f"reason clause: {next_text[:80]} — "
            "may justify own line per generative justification 5 (substantive adjunct) "
            f"or merge per atomic-thought / single-image test.{teamim_note}"
        )
        suggested = "REVIEW candidate — editor judges causal coherence + single-image"

        brief = (
            f"causal כִּי clause split — {prior_text[:60]} // {next_text[:60]} "
            f"({combined_words} prosodic words combined)"
        )

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "causal-כִּי-clause-split",
            "severity": "REVIEW-REQUIRED",
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "prior_line": prior_text,
            "next_line": next_text,
            "prosodic_word_count": combined_words,
            "annotation": annotation,
            "suggested_action": suggested,
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

        doc = {
            "validator": "validate_causal_ki",
            "rule": "causal-כִּי-clause-split",
            "version": "1.0.0",
            "layer": 3,
            "book": args.book or "all",
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": findings_json,
            "counts": {"REVIEW-REQUIRED": len(findings_json)},
            "summary": {
                "total_findings": len(findings_json),
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output ---
    print("=" * 72)
    print(f"Causal כִּי Clause-Split Validator — Tanakh {tier_label}")
    print("Reference: causal כִּי pattern (distinct from H7 complement-כִּי)")
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
        print("No findings. Causal כִּי clause splits are clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
