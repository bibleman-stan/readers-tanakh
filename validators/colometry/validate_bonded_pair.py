#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Rule M1 — Bonded Pair.

M1 (canon §3; Layer 3 editorial rule):
An N=2 noun coordination joined by וְ where the pair functions as a single
unified hendiadys, merism, or bonded rhetorical image. Common examples:
חסד+אמת (loyalty + truth), שמים+ארץ (heaven + earth), יומם+לילה (day + night),
טוב+רע (good + evil), זכר+נקבה (male + female), שרים+שופטים (officials + judges),
אמת+משפט (truth + justice).

Trigger:
  Line N ends with skeleton1; line N+1 starts with וְ + skeleton2,
  where (skeleton1, skeleton2) ∈ HEBREW_BONDED_PAIRS (closed list).

Severity:
  STRONG-MERGE-CANDIDATE (M1 is closed-list per canon §1).

ARCHITECTURAL CONSTRAINT — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. The te'amim
Unicode range (U+0591–U+05AF) does NOT appear in any predicate that decides
whether to fire a finding. Te'amim MAY appear in finding annotations as
informational defensibility-capture — the trigger must remain syntactic.

FORCED-NO-MERGE GUARDS (skip BEFORE emitting):
  1. Poetic register — is_poetic_register(book, chapter, verse) → skip.
  2. Different verse — cross-verse merges forbidden.
  3. One member carries a finite verb — no longer a simple N=2 noun pair.

Output format:
    [DEVIATION]  file:line  M1/bonded-pair  STRONG-MERGE-CANDIDATE  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_bonded_pair.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_bonded_pair.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_bonded_pair.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_bonded_pair.py --json
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

# ---------------------------------------------------------------------------
# M1 Bonded-Pair Lexicon — consonant skeletons (cartouches stripped)
# ---------------------------------------------------------------------------
# Canonical bonded pairs from canon §1 M1 + variants. Each tuple represents
# an ordered pair (skeleton1, skeleton2). The pair is detected when:
#   - Line N ends with skeleton1
#   - Line N+1 starts with וְ + skeleton2
#
# Building the lexicon from canon §1 examples:
#   חֶסֶד וֶאֱמֶת → (חסד, אמת)
#   שָׁמַיִם וָאָרֶץ → (שמים, ארץ)
#   הַטּוֹב וְהָרָע → (טוב, רע)
#   יוֹמָם וָלָיְלָה → (יומם, לילה)
#   שָׂרִים וְשׁוֹפְטִים → (שרים, שופטים)
#   אֱמֶת וּמִשְׁפָּט → (אמת, משפט)
#   זָכָר וּנְקֵבָה → (זכר, נקבה)
#
# Also including reverses (אמת+חסד, ארץ+שמים, etc.) to catch both orderings.
# Symmetric pairs (שמים/ארץ, טוב/רע, etc.) map both directions.

HEBREW_BONDED_PAIRS = {
    # Covenant pair: חסד (loyalty) + אמת (truth)
    ("חסד", "אמת"),
    ("אמת", "חסד"),

    # Cosmic pair: שמים (heaven) + ארץ (earth)
    ("שמים", "ארץ"),
    ("ארץ", "שמים"),

    # Moral totality: טוב (good) + רע (evil)
    ("טוב", "רע"),
    ("רע", "טוב"),

    # Temporal totality: יומם (day) + לילה (night)
    ("יומם", "לילה"),
    ("לילה", "יומם"),

    # Civic pair: שרים (officials) + שופטים (judges)
    ("שרים", "שופטים"),
    ("שופטים", "שרים"),

    # Civic virtue: אמת (truth) + משפט (justice)
    ("אמת", "משפט"),
    ("משפט", "אמת"),

    # Anthropological pair: זכר (male) + נקבה (female)
    ("זכר", "נקבה"),
    ("נקבה", "זכר"),

    # Additional common hendiadys pairs
    ("רחמים", "חן"),        # mercy + grace
    ("עז", "גבורה"),       # strength + might
    ("משפט", "צדקה"),      # judgment + righteousness
    ("שלום", "ברכה"),      # peace + blessing
    ("כבוד", "הדר"),       # glory + splendor
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
# Finite-verb heuristic — detect if token looks like a finite verb
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
    # Common imperatives
    "שמעו", "ראו", "לכו", "קומו", "עשו",
    "לך", "קום", "בא", "קח", "תן",
}


def looks_like_finite_verb(bare: str) -> bool:
    """Heuristic: does this bare consonant skeleton look like a finite verb?

    Conservative bias: we'd rather over-detect finite verbs (causing the
    guard to fire and skip the finding) than under-detect them.
    """
    if not bare:
        return False

    # Direct skeleton match
    if bare in KNOWN_FINITE_VERB_SKELETONS:
        return True

    # Wayyiqtol prefix
    if bare.startswith(WAYYIQTOL_PREFIXES):
        if len(bare) >= 4 and bare not in ("ויהוה",):
            return True

    # Maqqef-internal: check last segment (head verb)
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

    # Build a lookup: line_index → (chapter, verse)
    line_to_verse: dict[int, tuple[int | None, int | None]] = {}
    current_verse = (chapter_from_file, None)
    for i, line in enumerate(lines):
        ref = parse_verse_ref(line)
        if ref is not None:
            current_verse = ref
        line_to_verse[i] = current_verse

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        # Determine verse context
        chapter, verse = line_to_verse.get(i, (chapter_from_file, None))

        line_no = i + 1  # 1-based

        # --- Find next content line in the SAME verse (no cross-verse fire) ---
        next_idx: int | None = None
        for j in range(i + 1, len(lines)):
            if is_skippable(lines[j]):
                continue
            n_chapter, n_verse = line_to_verse.get(j, (chapter_from_file, None))
            # Same verse?
            if (n_chapter, n_verse) != (chapter, verse):
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

        # --- Guard 3: either line has a finite verb → not a simple noun pair ---
        prior_has_verb = line_has_finite_verb(line)
        next_has_verb = line_has_finite_verb(next_line)
        if prior_has_verb or next_has_verb:
            continue

        # --- M1 trigger: line N ends with skeleton1, line N+1 starts with וְ + skeleton2 ---
        last_tok = last_content_token(line)
        if not last_tok:
            continue

        skeleton1 = strip_points(last_tok).rstrip(SOF_PASUQ)
        if not skeleton1:
            continue

        first_tok = first_content_token(next_line)
        if not first_tok:
            continue

        bare_first = strip_points(first_tok)

        # Check if it starts with וְ (vav-conjunction)
        if not bare_first.startswith("ו"):
            continue

        # Extract skeleton2 after the vav prefix
        skeleton2 = bare_first[1:]  # Remove leading ו
        if not skeleton2:
            continue

        # Check if (skeleton1, skeleton2) is in the bonded-pair lexicon
        if (skeleton1, skeleton2) not in HEBREW_BONDED_PAIRS:
            continue

        # --- All guards passed; emit STRONG-MERGE-CANDIDATE finding ---
        prior_text = line.strip()
        next_text = next_line.strip()

        prior_teamim = teamim_summary(line)
        next_teamim = teamim_summary(next_line)
        teamim_note = ""
        if prior_teamim or next_teamim:
            teamim_note = (
                f" Te'amim placement: {prior_teamim or '(none)'} on prior line, "
                f"{next_teamim or '(none)'} on next line — informational only."
            )

        annotation = (
            f"M1 bonded pair: {skeleton1!r} and {skeleton2!r} — "
            f"hendiadys / merism / bonded rhetorical image (canon §3 M1)."
            + teamim_note
        )
        suggested = "MERGE candidate per M1 (bonded pair)"
        brief = (
            f"M1 bonded pair ({skeleton1} + {skeleton2}) — "
            f"{prior_text} // {next_text}"
        )

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "M1/bonded-pair",
            "severity": "STRONG-MERGE-CANDIDATE",
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "skeleton1": skeleton1,
            "skeleton2": skeleton2,
            "prior_line": prior_text,
            "next_line": next_text,
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
                "skeleton1": f["skeleton1"],
                "skeleton2": f["skeleton2"],
                "prior_line": f["prior_line"],
                "next_line": f["next_line"],
                "next_line_num": f["next_line_num"],
                "annotation": f["annotation"],
                "suggested_action": f["suggested_action"],
            })

        counts = {"STRONG-MERGE-CANDIDATE": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        doc = {
            "validator": "validate_bonded_pair",
            "rule": "M1",
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
    print(f"Rule M1 Bonded-Pair validator — Tanakh {tier_label}")
    print(f"Reference: canon §3 M1 (hendiadys / merism / bonded pair)")
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
        print("No findings. Rule M1 bonded-pair is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
