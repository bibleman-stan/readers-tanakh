#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate Layer 1 + Canon M2 — Verb-Object Clause-Nucleus Bond.

Direct-object marker אֵת stranded from its governing verb across line boundaries.

From Layer 1 (data/syntax-reference/hebrew-break-legality.md):
  "Direct-object marker אֵת stranded from object" — REQUIRED-MERGE.
  A finite verb and its direct object (marked with את) form an indivisible
  clause nucleus; they cannot be split across lines.

From Canon M2 (private/01-method/colometry-canon.md):
  "A finite verb and its direct object (or obligatory complement) on short
  phrases stay on one line, even under split-trigger pressure. The clause
  nucleus is the minimal atomic predication and cannot be fragmented."

Detection signature:
  A line ending with a finite-verb skeleton (qatal / yiqtol / wayyiqtol /
  imperative / cohortative pattern) where the next non-skippable within-verse
  line begins with the direct-object marker אֵת (consonant skeleton: את,
  with or without maqqef-suffix).

Severity:
  - STRONG-MERGE-CANDIDATE — finite verb + את on next line, no intervening
    guards. This is Category A per canon §2 (mechanical-rule authority).
  - REVIEW-REQUIRED — guards fire (e.g., paragraph break, register change).

Architectural constraint:
  NO te'amim glyphs (U+0591-U+05AF) in any trigger predicate. Sof-pasuq
  usage is permitted for verse-scoping only.

Output format:
    [MALFORMED]  file:line_number  rule  brief description

Exit code: 0 if zero violations, 1 if violations found, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/syntax/validate_verb_object_bond.py
    PYTHONIOENCODING=utf-8 py -3 validators/syntax/validate_verb_object_bond.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/syntax/validate_verb_object_bond.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/syntax/validate_verb_object_bond.py --json
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

# Make _shared importable
sys.path.insert(0, str(REPO_ROOT / "validators"))
from _shared.poetic_register import is_poetic_register  # noqa: E402

# ---------------------------------------------------------------------------
# Hebrew Unicode constants
# ---------------------------------------------------------------------------

# Niqqud / cantillation marks to strip when isolating consonant skeleton
# U+0591–U+05C7: Hebrew cantillation and points
HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"  # ׃

# Maqqef (orthographic word-joiner)
MAQQEF = "־"     # ־

# Paseq (vertical bar disjunction)
PASEQ = "׀"      # ׀


def strip_points(token: str) -> str:
    """Return token with niqqud and te'amim stripped (consonant skeleton only)."""
    return HEBREW_POINTS_RE.sub("", token)


# ---------------------------------------------------------------------------
# Verse-reference / blank line handling
# ---------------------------------------------------------------------------

VERSE_REF_RE = re.compile(r"^(\S+\s+)?\d+:\d+\s*$")


def is_skippable(line: str) -> bool:
    """Return True for blank lines and verse-reference-only lines."""
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
# Finite-verb skeleton detection (conservative bias)
# ---------------------------------------------------------------------------

# Strong wayyiqtol prefix patterns (consonants only after stripping niqqud/te'amim)
WAYYIQTOL_PREFIXES = ("וי", "ות", "ונ", "וא")

# Common qatal endings
QATAL_SUFFIXES = (
    "תי",   # 1cs perfect
    "ת",    # 2ms
    "נו",   # 1cp
    "תם",   # 2mp
    "תן",   # 2fp
    "ו",    # 3cp
)

# High-frequency finite-verb skeletons (consonant skeleton post-strip).
# We bias toward over-detecting verbs so the "has finite verb" guard
# fires conservatively.
KNOWN_FINITE_VERB_SKELETONS = {
    # Common qatal 3ms / 3fs / 3cp forms
    "אמר", "אמרה", "אמרו", "אמרתי", "אמרת", "אמרנו", "אמרתם",
    "ראה", "ראתה", "ראו", "ראיתי", "ראית", "ראינו",
    "שמע", "שמעה", "שמעו", "שמעתי", "שמענו",
    "ידע", "ידעה", "ידעו", "ידעתי", "ידעת", "ידענו",
    "ברא", "בראה", "בראו",                       # ברא — created (Gen 1:1)
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
    # Imperatives
    "שמעו", "ראו", "לכו", "קומו", "עשו",
    "לך", "קום", "בא", "קח", "תן",
}


def looks_like_finite_verb(bare: str) -> bool:
    """Heuristic: does this bare consonant skeleton look like a finite verb?

    Conservative bias: we'd rather over-detect finite verbs (causing the
    no-merge guard to fire and the finding to be skipped) than under-detect
    them (emit a finding when there's no actual verb).
    """
    if not bare:
        return False

    # Direct skeleton match
    if bare in KNOWN_FINITE_VERB_SKELETONS:
        return True

    # Wayyiqtol prefix (וי, ות, וא, ונ) — always finite
    if bare.startswith(WAYYIQTOL_PREFIXES):
        if len(bare) >= 4 and bare not in ("ויהוה",):
            return True

    # Maqqef-internal: check segments
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


def line_contains_finite_verb(line: str) -> bool:
    """True if ANY content token on `line` looks like a finite verb.

    Most Hebrew verbs come near the start of the clause (particularly in wayyiqtol
    and yiqtol forms). We check all tokens to be conservative — better to find
    a verb and trigger the merge than miss one and produce false findings.
    """
    for tok in content_tokens(line):
        bare = strip_points(tok).rstrip(SOF_PASUQ)
        if looks_like_finite_verb(bare):
            return True
    return False


def line_starts_with_et_marker(line: str) -> bool:
    """True if the first content token is the direct-object marker אֵת.

    Direct-object marker consonant skeleton: את (with or without maqqef-suffix).
    """
    first = first_content_token(line)
    if first is None:
        return False
    bare = strip_points(first)
    # The bare skeleton should start with את (could be את, אתו, אתם, etc. with suffix)
    # But for our purposes, we check if it IS EXACTLY את (bare marker)
    # or את + maqqef (את־).
    if MAQQEF in bare:
        head = bare.split(MAQQEF, 1)[0]
        if head == "את":
            return True
    if bare == "את":
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
# Forced-no-merge guards
# ---------------------------------------------------------------------------

def is_poetic_context(book: str, chapter: int | None, verse: int | None) -> bool:
    """Guard: is this line in a poetic register (Psalms, Proverbs, Job 3:1-42:6)?"""
    if chapter is None or verse is None:
        return False
    return is_poetic_register(book, chapter, verse)


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path) -> list[dict]:
    """Scan one text file for verb-את stranded violations."""
    violations = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    book = book_name_from_path(path)
    chapter_from_file = chapter_from_path(path)
    verses = partition_into_verses(lines)

    # Build a lookup: line_index → (chapter, verse, position_within_verse, verse_line_indices)
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

        # --- Check if this line contains a finite verb ---
        if not line_contains_finite_verb(line):
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

        # --- Check if next line starts with את marker ---
        if not line_starts_with_et_marker(next_line):
            continue

        # --- Guard: poetic register ---
        if chapter is not None and is_poetic_context(book, chapter, verse):
            severity = "REVIEW-REQUIRED"
        else:
            severity = "STRONG-MERGE-CANDIDATE"

        # --- All checks passed; emit finding ---
        prior_text = line.strip()
        next_text = next_line.strip()

        violations.append({
            "file": path.name,
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "next_line": next_text,
            "severity": severity,
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "prior_line": prior_text,
            "rule": "L1.5/M2",
            "brief": f"finite verb + אֵת marker stranded — {prior_text} // {next_text}",
        })

    return violations


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--book",
        metavar="BOOK",
        help="Restrict scan to one book folder name (e.g. 'genesis', 'jonah'). "
             "Default: all books in the target directory.",
    )
    parser.add_argument(
        "--v2",
        action="store_true",
        help="Scan v2/he (editorial gold standard) instead of v1/he-baseline.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as a single JSON document to STDOUT instead of human-readable lines.",
    )
    args = parser.parse_args()

    base_dir = V2_DIR if args.v2 else V1_DIR
    tier_label = "v2/he" if args.v2 else "v1/he-baseline"

    if not base_dir.exists():
        print(
            f"ERROR: {base_dir} not found. "
            f"Run the ingest/baseline scripts first.",
            file=sys.stderr,
        )
        sys.exit(2)

    # Collect files
    if args.book:
        book_dir = base_dir / args.book
        if not book_dir.exists():
            print(f"ERROR: book directory not found: {book_dir}", file=sys.stderr)
            sys.exit(2)
        files = sorted(book_dir.glob("*.txt"))
    else:
        files = sorted(base_dir.rglob("*.txt"))

    if not files:
        print(f"No .txt files found under {base_dir}", file=sys.stderr)
        sys.exit(2)

    all_violations: list[dict] = []
    for path in files:
        all_violations.extend(scan_file(path))

    exit_code = 1 if all_violations else 0

    # --- JSON output mode ---
    if args.json:
        findings = []
        for v in all_violations:
            findings.append({
                "file": v["file_rel"],
                "line": v["line_num"],
                "next_line": v["next_line_num"],
                "severity": v["severity"],
                "tag": v["severity"],
                "rule_id": "L1.5",
                "rule_short": "verb + אֵת stranded",
                "brief": v["brief"],
                "applied_action": "merge_with_next",
            })

        by_severity: dict[str, int] = {}
        by_severity_no_review: dict[str, int] = {}
        for f in findings:
            by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1
            if f["severity"] == "STRONG-MERGE-CANDIDATE":
                by_severity_no_review["STRONG"] = by_severity_no_review.get("STRONG", 0) + 1
            else:
                by_severity_no_review["REVIEW"] = by_severity_no_review.get("REVIEW", 0) + 1

        doc = {
            "validator": "validate_verb_object_bond",
            "rule": "Layer 1 L1.5 + Canon M2",
            "layer": 1,
            "book": args.book or "all",
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": findings,
            "summary": {
                "total_findings": len(findings),
                "by_severity": by_severity,
                "by_severity_no_review": by_severity_no_review,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output (default) ---
    print("=" * 72)
    print(f"Layer 1 L1.5 + Canon M2 — Verb-Object Bond validator")
    print(f"Tanakh {tier_label} corpus")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Violations    : {len(all_violations)}")
    print()

    # Breakdown by severity
    strong_count = sum(1 for v in all_violations if v["severity"] == "STRONG-MERGE-CANDIDATE")
    review_count = sum(1 for v in all_violations if v["severity"] == "REVIEW-REQUIRED")
    if strong_count or review_count:
        print(f"Breakdown:")
        print(f"  STRONG-MERGE-CANDIDATE: {strong_count}")
        print(f"  REVIEW-REQUIRED:        {review_count}")
        print()

    if all_violations:
        for v in all_violations:
            print(f"[MALFORMED]  {v['file']}:{v['line_num']}  {v['rule']}  {v['brief']}")
            print(f"    → next line ({v['next_line_num']}): {v['next_line'][:100]}")
            print()
    else:
        print("No violations found. Verb-object bonds are intact.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
