#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate coordinated direct-object splits.

Detects coordinated-DO splits where a compound direct object spans two cola
under one shared verb.

Detection signature:
A v2/he line ending in `אֵת` + NP (direct-object phrase) AND the next
within-verse line beginning with `וְאֵת` + NP (conjunction + DO + NP).
This signature catches "X // and-Y" coordinated-object splits where both
halves serve as compound DO of a single verb on a prior line.

Combined ≤8 prosodic words. Both lines should be NP-only (no finite verbs).

Severity:
  - STRONG-MERGE-CANDIDATE — clean coordinated-DO pattern, no guards fire
  - REVIEW-REQUIRED — guards: poetic register (Sifrei Emet / embedded-poetry / acrostic),
                      parallel-list scope (H17), heavy NP on either side
                      (relative clause, ≥2 appositives), combined >8 prosodic words

References:
  - Canon §5 Rule M2 (verb-object clause-nucleus bond)
  - Canon §1 Structural Justification 1 (formally-marked parallel series; compound
    list break signals carve-out for bare "and [noun]" items)
  - Joüon-Muraoka §137 (direct object and את)

ARCHITECTURAL CONSTRAINT — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. The te'amim
Unicode range (U+0591–U+05AF) does NOT appear in any predicate that decides
whether to fire a finding. Te'amim MAY appear in finding annotations as
informational defensibility-capture (Rule H8) — the trigger must remain syntactic.

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_coordinated_object.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_coordinated_object.py --book jonah
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_coordinated_object.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_coordinated_object.py --json
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
# U+05C4–U+05C5, U+05C7).  Strip U+0591-U+05BD (cantillation + niqqud) and U+05BF,
# U+05C1-U+05C2, U+05C4-U+05C5, U+05C7 while PRESERVING maqqef (U+05BE), paseq
# (U+05C0), and sof pasuq (U+05C3).
HEBREW_POINTS_RE = re.compile(r"[֑-ׇֽֿׁׂׅׄ]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"  # ׃
# Maqqef (orthographic word-joiner)
MAQQEF = "־"     # ־

# Direct-object marker
ET = "את"        # את


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
    """Return the book directory name (e.g. '32-jonah')."""
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
# Verb detection heuristic
# ---------------------------------------------------------------------------

# Common finite-verb skeletons (post-strip)
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
}

WAYYIQTOL_PREFIXES = ("וי", "ות", "ונ", "וא")
QATAL_SUFFIXES = ("תי", "ת", "נו", "תם", "תן", "ו")


def looks_like_finite_verb(bare: str) -> bool:
    """Heuristic: does this bare consonant skeleton look like a finite verb?

    Conservative bias: we'd rather over-detect finite verbs (causing guards
    to fire and the finding to be skipped) than under-detect them.
    """
    if not bare:
        return False

    # Direct skeleton match
    if bare in KNOWN_FINITE_VERB_SKELETONS:
        return True

    # Wayyiqtol prefix detection
    if bare.startswith(WAYYIQTOL_PREFIXES):
        if len(bare) >= 4 and bare not in ("ויהוה",):
            return True

    # Maqqef-internal verb check
    if MAQQEF in bare:
        for part in bare.split(MAQQEF):
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
# Direct-object marker detection (אֵת + NP)
# ---------------------------------------------------------------------------

def line_ends_with_et_np(line: str) -> bool:
    """True if line ends with אֵת (direct-object marker) + NP."""
    toks = content_tokens(line)
    if not toks:
        return False
    # Last token must be part of an אֵת-marked object phrase.
    # Heuristic: last token or second-to-last contains אֵת as prefix or standalone.
    bare_last = strip_points(toks[-1]).rstrip(SOF_PASUQ)
    if bare_last == ET or bare_last.startswith(ET):
        return True
    if len(toks) >= 2:
        bare_penult = strip_points(toks[-2]).rstrip(SOF_PASUQ)
        if bare_penult == ET or bare_penult.startswith(ET):
            return True
    return False


def line_starts_with_ve_et_np(line: str) -> bool:
    """True if line begins with וְאֵת (conjunction + direct-object marker) + NP."""
    first = first_content_token(line)
    if not first:
        return False
    bare = strip_points(first).rstrip(SOF_PASUQ)
    # Pattern: starts with ו (vav conjunction) + אֵת (direct-object marker)
    # Bare form after stripping: ואת... or just ואת
    return bare.startswith("וא") and ("את" in bare or bare.startswith("ואת"))


# ---------------------------------------------------------------------------
# Heavy NP detection
# ---------------------------------------------------------------------------

def line_has_heavy_np(line: str) -> bool:
    """True if line contains relative clause or ≥2 appositives (heavy nominal).

    Heuristic: ashur / mi / mah (relative/interrogative), or ≥2 ben/bat (appositives).
    """
    bares = [strip_points(t).rstrip(SOF_PASUQ) for t in content_tokens(line)]
    if not bares:
        return False

    # Check for relative/interrogative
    if "אשר" in bares or "מי" in bares or "מה" in bares:
        return True

    # Check for appositives (ben/bat count)
    appositive_count = sum(1 for b in bares if b in ("בן", "בת"))
    if appositive_count >= 2:
        return True

    return False


# ---------------------------------------------------------------------------
# Verse partitioning
# ---------------------------------------------------------------------------

def partition_into_verses(lines: list[str]) -> list[tuple[int | None, int | None, list[int]]]:
    """Group line indices by verse.

    Returns a list of (chapter, verse, [line_indices]) tuples in source order.
    Verse-reference lines themselves are included but are skippable for content scanning.
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

    # Build a lookup: line_index → (chapter, verse, position_within_verse, all verse indices)
    line_to_verse: dict[int, tuple[int | None, int | None, int, list[int]]] = {}
    for ch, vs, indices in verses:
        for pos, idx in enumerate(indices):
            line_to_verse[idx] = (ch, vs, pos, indices)

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        # Check if line ends with אֵת + NP
        if not line_ends_with_et_np(line):
            continue

        # Determine verse context
        v_ctx = line_to_verse.get(i)
        chapter = v_ctx[0] if v_ctx else chapter_from_file
        verse = v_ctx[1] if v_ctx else None
        pos_in_verse = v_ctx[2] if v_ctx else 0
        verse_indices = v_ctx[3] if v_ctx else []

        line_no = i + 1  # 1-based

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

        # Check if next line starts with וְאֵת + NP
        if not line_starts_with_ve_et_np(next_line):
            continue

        # --- GUARD 1: poetic register ---
        if chapter is not None and is_poetic_register(book, chapter, verse):
            severity = "REVIEW-REQUIRED"
            guard_reason = "poetic register (Sifrei Emet / embedded poetry / acrostic)"
        else:
            guard_reason = None

        # --- GUARD 2: both lines are NP-only (no finite verbs) ---
        prior_has_verb = line_has_finite_verb(line)
        next_has_verb = line_has_finite_verb(next_line)
        if prior_has_verb or next_has_verb:
            continue

        # --- GUARD 3: combined ≤8 prosodic words ---
        combined_words = prosodic_word_count(line) + prosodic_word_count(next_line)
        if combined_words > 8:
            if guard_reason is None:
                guard_reason = "combined > 8 prosodic words"
                severity = "REVIEW-REQUIRED"
        else:
            if guard_reason is None:
                severity = "STRONG-MERGE-CANDIDATE"

        # --- GUARD 4: heavy NP on either side ---
        if guard_reason is None:
            prior_heavy = line_has_heavy_np(line)
            next_heavy = line_has_heavy_np(next_line)
            if prior_heavy or next_heavy:
                guard_reason = "heavy NP (relative clause or appositives)"
                severity = "REVIEW-REQUIRED"

        # If we haven't determined severity yet (all guards passed or only poetic-register fired)
        if guard_reason is None:
            severity = "STRONG-MERGE-CANDIDATE"
        elif guard_reason == "poetic register (Sifrei Emet / embedded poetry / acrostic)":
            # Poetic-register guard alone makes it REVIEW-REQUIRED
            severity = "REVIEW-REQUIRED"

        prior_text = line.strip()
        next_text = next_line.strip()

        annotation = (
            "Coordinated direct object (compound DO of shared verb): "
            "אֵת + NP // וְאֵת + NP. Canon §5 M2 (verb-object clause-nucleus bond) "
            "and §1 Structural Justification 1 (compound list break signals) apply — "
            "bare 'and [noun]' items merge without elided-verb signal. "
            "(Per Joüon-Muraoka §137; Waltke-O'Connor §9.5.2.)"
        )

        if guard_reason:
            annotation += f" Guard fired: {guard_reason}."

        brief = (
            f"coordinated DO split — {prior_text} // {next_text} "
            f"({combined_words} prosodic words combined)"
        )

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "M2/coordinated-object",
            "severity": severity,
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "prior_line": prior_text,
            "next_line": next_text,
            "prosodic_word_count": combined_words,
            "annotation": annotation,
            "suggested_action": "MERGE candidate per M2 + compound-list rule",
            "brief": brief,
            "guard_reason": guard_reason,
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
                "prior_line": f["prior_line"],
                "next_line": f["next_line"],
                "next_line_num": f["next_line_num"],
                "prosodic_word_count": f["prosodic_word_count"],
                "annotation": f["annotation"],
                "suggested_action": f["suggested_action"],
            })

        counts = {"REVIEW-REQUIRED": 0, "STRONG-MERGE-CANDIDATE": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        doc = {
            "validator": "validate_coordinated_object",
            "rule": "M2/coordinated-object",
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
    print(f"Coordinated-Object Validator — Tanakh {tier_label}")
    print(f"Reference: canon §5 M2 (verb-object clause-nucleus bond)")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Findings      : {len(all_findings)}")

    strong_count = sum(1 for f in all_findings if f["severity"] == "STRONG-MERGE-CANDIDATE")
    review_count = sum(1 for f in all_findings if f["severity"] == "REVIEW-REQUIRED")
    if strong_count or review_count:
        print()
        print(f"  STRONG-MERGE-CANDIDATE: {strong_count}")
        print(f"  REVIEW-REQUIRED       : {review_count}")
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
                if f.get("guard_reason"):
                    print(f"    Guard: {f['guard_reason']}")
                print()
    else:
        print("No findings. Coordinated-object rule is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
