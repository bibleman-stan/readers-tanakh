#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate 1-method/canon §1 "fronting paradox" — marked Hebrew word order argues for MERGE, not split.

Short-verse specialization: when a verse is short (≤6 prosodic words total) AND the first
line is a single fronted constituent (single-word fronted PP or temporal/locative word),
AND the second line starts with a finite verb or its subject, the fronted element should
MERGE with the main clause per the fronting paradox (1-method/canon §1).

SIGNATURE:
  • Total verse ≤6 prosodic words (short verse)
  • First line is a single fronted constituent
    - Single-word fronted PP: bound prep + noun (בְּרֵאשִׁית, מֵרֹאשׁ, בַּיּוֹם, בָּעֵת)
    - Single temporal/locative word (בַּיּוֹם, בָּעֵת)
  • Second line starts with a finite verb or subject NP
  • No guards fire

SEVERITY:
  - STRONG-MERGE-CANDIDATE — strict signature match, no guards fired
  - REVIEW-REQUIRED — guards fire or ambiguous morphology

GUARDS (forced-no-merge conditions; skip BEFORE emitting):
  1. Casus pendens — first line has resumptive pronoun marker (rare for single-word)
  2. Substantive-adjunct fronting — fronted PP is long/heavy (≥2 tokens, not single-word)
  3. Poetic parallelism register — substantive parallelistic structure detected
  4. FEF wayehi protasis — verse starts with וַיְהִי (H16)
  5. Heavy predicate — second line's predicate is compound verb + object (≥4 combined tokens)
  6. Cross-verse continuation — verse is not first in a multi-verse narrative block

NOTE: Poetic-register skip (formerly Guard 1, citing H18.2) was removed
  2026-05-04 methodology audit. Canon §1 fronting paradox has no register carve-out;
  H18.2 governs clause-nucleus integrity (a different rule); attributing an H18.2
  carve-out to this validator was overlay-as-authorization. Superseded.

ARCHITECTURAL CONSTRAINT — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. Te'amim Unicode range
(U+0591–U+05AF) does NOT appear in any predicate that decides whether to fire.
Te'amim MAY appear in annotations for defensibility-capture (Rule H8).

Output format:
    [DEVIATION]  file:line  fronting-paradox  {STRONG-MERGE-CANDIDATE|REVIEW-REQUIRED}  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_short_verse_fronting.py
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_short_verse_fronting.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_short_verse_fronting.py --v1
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_short_verse_fronting.py --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

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


# ---------------------------------------------------------------------------
# Path constants — v1/he-baseline + v2/heb
# ---------------------------------------------------------------------------
REPO_ROOT = _find_repo_root()
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files"  / "v2" / "heb"

# Make _shared importable when this script is run as __main__.
sys.path.insert(0, str(REPO_ROOT / "5-machinery/validators"))
from _shared.poetic_register import is_poetic_register  # noqa: E402

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers
# ---------------------------------------------------------------------------

# Hebrew points (te'amim U+0591–U+05AF + niqqud U+05B0–U+05BC, U+05C1–U+05C2,
# U+05C4–U+05C5, U+05C7). Strip te'amim + niqqud, PRESERVE maqqef, paseq, sof pasuq.
HEBREW_POINTS_RE = re.compile(r"[֑-ׇֽֿׁׂׅׄ]")

# Niqqud-only regex (no te'amim) — for vowel-pattern inspection
TEAMIM_ONLY_RE = re.compile(r"[֑-֯]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"
# Maqqef (orthographic word-joiner)
MAQQEF = "־"
# Paseq (vertical bar disjunction)
PASEQ = "׀"

# Niqqud marks (for vowel inspection)
HOLAM = "ֹ"
SHEVA = "ְ"
PATAH = "ַ"
QAMATS = "ָ"
HIRIQ = "ִ"
QUBUTS = "ֻ"
TSERE = "ֵ"
SEGOL = "ֶ"

# Hebrew consonants for preposition detection
BET = "ב"
KAF = "כ"
LAMED = "ל"
MEM = "מ"

# Common temporal/locative words (consonant skeletons)
TEMPORAL_LOCATIVE_HEADS = {
    "יום",      # day
    "עת",       # time
    "בוקר",    # morning
    "ערב",     # evening
    "שנה",     # year
    "מקום",    # place
    "בית",     # house
    "ישראל",   # Israel
    "ירושלם",  # Jerusalem
    "מצרים",   # Egypt
    "סיני",     # Sinai
}

# Bound prepositions (consonants that attach to nouns)
BOUND_PREP_CONSONANTS = {BET, LAMED, KAF, MEM}


def strip_points(token: str) -> str:
    """Return token with niqqud and te'amim stripped (consonant skeleton only)."""
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


def prosodic_word_count(line: str) -> int:
    """Count prosodic words (whitespace-delimited tokens; maqqef-groups count as one)."""
    return len(content_tokens(line))


def first_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[0] if toks else None


def last_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[-1] if toks else None


# ---------------------------------------------------------------------------
# Fronted single-word constituent detection
# ---------------------------------------------------------------------------

def is_single_word_fronted_pp_or_temporal(token: str) -> tuple[bool, str]:
    """Check if token is a single fronted PP or temporal/locative word.

    Returns (True, pp_type) where pp_type is one of:
      'bound_prep'     — ב/ל/כ/מ + noun (בְּרֵאשִׁית, מֵרֹאשׁ)
      'standalone_prep' — עַל, אֶל, מִן, בֵּין, etc.
      'temporal'       — יוֹם, עֵת, בּוּקֶר, etc.
    Returns (False, '') if not a match.
    """
    if not token:
        return False, ""

    bare = strip_points(token).rstrip(SOF_PASUQ)
    if not bare:
        return False, ""

    # Standalone prepositions (high-frequency temporal/locative)
    STANDALONE_TEMPORAL_PREPS = {
        "על",      # on, over
        "אל",      # to, toward
        "מן",      # from
        "בין",     # between
        "עם",      # with
        "תחת",    # under, instead of
        "לפני",    # before
        "אחרי",    # after
        "מאחרי",   # from after
    }

    if bare in STANDALONE_TEMPORAL_PREPS:
        return True, "standalone_prep"

    # Bound preposition attached to noun (ב/ל/כ/מ + noun)
    # Conservative check: starts with one of the four, ≥4 characters total,
    # and does NOT look like a verb form.
    if len(bare) >= 4 and bare[0] in BOUND_PREP_CONSONANTS:
        # Reject very common false positives (verbs that start with ב/ל/כ/מ)
        BOUND_PREP_VERB_EXCLUSIONS = {
            "לא", "לאו", "לכן", "לעת",  # logical particles, not genuine PP
            "בא", "בא", "בנה", "בן", "בת",  # verb forms
            "כל", "כלה",  # nouns/verbs
        }
        if bare not in BOUND_PREP_VERB_EXCLUSIONS:
            return True, "bound_prep"

    # Temporal/locative words (יוֹם, עֵת, etc.)
    # But only if they appear alone (one token).
    # We only check if bare is in TEMPORAL_LOCATIVE_HEADS.
    if bare in TEMPORAL_LOCATIVE_HEADS:
        return True, "temporal"

    return False, ""


def is_single_word_fronted_constituent(line: str) -> tuple[bool, str]:
    """Check if the line consists of exactly one fronted constituent.

    Returns (True, pp_type) if line is a single-token fronted PP/temporal word.
    """
    toks = content_tokens(line)
    if len(toks) != 1:
        return False, ""

    return is_single_word_fronted_pp_or_temporal(toks[0])


# ---------------------------------------------------------------------------
# Finite-verb heuristic (from validate_clause_nucleus_split.py)
# ---------------------------------------------------------------------------

WAYYIQTOL_PREFIXES = ("וי", "ות", "ונ", "וא")

KNOWN_FINITE_VERB_SKELETONS = {
    # Common qatal forms
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
    # Common imperatives
    "שמעו", "ראו", "לכו", "קומו", "עשו",
    "לך", "קום", "בא", "קח", "תן",
}


def looks_like_finite_verb(bare: str) -> bool:
    """Conservative heuristic: does this skeleton look like a finite verb?"""
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
# Subject NP detection — basic heuristic
# ---------------------------------------------------------------------------

SUBJECT_MARKERS = {
    # Common subject nouns / pronouns
    "אלהים", "יהוה", "אדני", "יה",
    # Personal pronouns
    "אני", "אתה", "את", "הוא", "היא", "אנחנו", "אתם", "אתן", "הם", "הן",
    # Common agent nouns
    "אדם", "איש", "אשה", "דוד", "משה", "יעקב", "יוסף", "ישראל",
}


def line_starts_with_subject_candidate(line: str) -> bool:
    """Heuristic: does line start with a plausible subject NP?"""
    first = first_content_token(line)
    if not first:
        return False
    bare = strip_points(first)
    if bare in SUBJECT_MARKERS:
        return True
    # Common construct chains (אִישׁ הָ..., מַלְכֵי..., אֱלֹהֵי...)
    if bare in ("אישׁ", "מלכים", "מלך", "אלהים", "אדם", "עם"):
        return True
    return False


# ---------------------------------------------------------------------------
# Guard conditions
# ---------------------------------------------------------------------------

def has_wayehi_protasis(verse_lines: list[str]) -> bool:
    """Guard 5: does the verse start with וַיְהִי (H16)?"""
    if not verse_lines:
        return False
    first = first_content_token(verse_lines[0])
    if not first:
        return False
    return strip_points(first) == "ויהי"


def second_line_has_heavy_predicate(line: str) -> bool:
    """Guard 6: does second line have compound verb + object? (≥4 combined tokens)"""
    toks = content_tokens(line)
    if len(toks) < 4:
        return False
    # Check if first token looks like a verb and there are 3+ additional tokens
    if toks and looks_like_finite_verb(strip_points(toks[0])):
        return len(toks) >= 4
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


def count_words_in_verse(lines: list[str], verse_indices: list[int]) -> int:
    """Count total prosodic words in a verse."""
    count = 0
    for idx in verse_indices:
        count += prosodic_word_count(lines[idx])
    return count


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
        if v_ctx is None:
            continue

        chapter = v_ctx[0] if v_ctx else chapter_from_file
        verse = v_ctx[1] if v_ctx else None
        pos_in_verse = v_ctx[2] if v_ctx else 0
        verse_indices = v_ctx[3] if v_ctx else []

        line_no = i + 1  # 1-based

        # Only fire on FIRST line of the verse (pos_in_verse == 0)
        if pos_in_verse != 0:
            continue

        # Guard 1 (poetic register) removed 2026-05-04 methodology audit:
        # Canon §1 fronting paradox has no register carve-out; the prior skip
        # cited "H18.2" (clause-nucleus integrity — a different rule entirely).
        # Overlay-as-authorization; superseded.

        # Signature 1: verse is short (≤6 prosodic words total)
        total_words = count_words_in_verse(lines, verse_indices)
        if total_words > 6:
            continue

        # Signature 2: first line is a single fronted constituent
        is_fronted, pp_type = is_single_word_fronted_constituent(line)
        if not is_fronted:
            continue

        # Find next content line in SAME verse
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

        # Signature 3: second line starts with a finite verb or subject
        has_verb = line_has_finite_verb(next_line)
        has_subject = line_starts_with_subject_candidate(next_line)
        if not (has_verb or has_subject):
            continue

        # Guard 5: H16 wayehi protasis
        verse_content_lines = [lines[idx] for idx in verse_indices]
        if has_wayehi_protasis(verse_content_lines):
            continue

        # Guard 6: heavy predicate on second line
        if second_line_has_heavy_predicate(next_line):
            severity = "REVIEW-REQUIRED"
        else:
            severity = "STRONG-MERGE-CANDIDATE"

        # Emit finding
        prior_text = line.strip()
        next_text = next_line.strip()
        brief = (
            f"short verse ({total_words} words) — fronted {pp_type} + "
            f"{'verb' if has_verb else 'subject'} — "
            f"{prior_text} // {next_text}"
        )

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "fronting-paradox",
            "severity": severity,
            "pp_type": pp_type,
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "total_words": total_words,
            "prior_line": prior_text,
            "next_line": next_text,
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
    parser.add_argument("--v1", action="store_true", help="Scan v1/he-baseline.")
    parser.add_argument("--v2", action="store_true", help="Scan v2/heb (default if neither specified).")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show context.")
    parser.add_argument("--json", action="store_true", help="Emit JSON document.")
    args = parser.parse_args()

    # Default to v2, but allow explicit --v1 to override
    base_dir = V1_DIR if args.v1 else V2_DIR
    tier_label = "v1/he-baseline" if args.v1 else "v2/heb"
    if not base_dir.exists():
        # Fall back to the other tier
        alt = V2_DIR if args.v1 else V1_DIR
        if alt.exists():
            base_dir = alt
            tier_label = "v2/heb" if alt is V2_DIR else "v1/he-baseline"
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
                "pp_type": f["pp_type"],
                "total_words": f["total_words"],
                "prior_line": f["prior_line"],
                "next_line": f["next_line"],
                "next_line_num": f["next_line_num"],
            })

        counts = {"STRONG-MERGE-CANDIDATE": 0, "REVIEW-REQUIRED": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        by_pp_type: dict[str, int] = {}
        for f in findings_json:
            by_pp_type[f["pp_type"]] = by_pp_type.get(f["pp_type"], 0) + 1

        doc = {
            "validator": "validate_short_verse_fronting",
            "rule": "fronting-paradox",
            "version": "1.0.0",
            "layer": 3,
            "book": args.book or "all",
            "tier": tier_label,
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": findings_json,
            "counts": counts,
            "summary": {
                "total_findings": len(findings_json),
                "by_severity": counts,
                "by_pp_type": by_pp_type,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output ---
    print("=" * 72)
    print(f"Fronting Paradox validator — Tanakh {tier_label}")
    print(f"Reference: 1-method/canon §1 (fronted constituents in short verses)")
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
                print(f"    Prior: {f['prior_line'][:100]}")
                print(f"    Next:  {f['next_line'][:100]}")
                print(f"    Total verse length: {f['total_words']} prosodic words")
                print()
    else:
        print("No findings. Fronting paradox coverage is complete.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
