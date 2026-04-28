#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate quantifier scope integrity.

Pattern: quantifier stranded from its scope-NP.

Quantifiers: כָּל, רַב, מְעַט, מְאֹד-as-quantifier, יֶתֶר.

TRIGGER:
Line ends with quantifier (often maqqef-bound: כָּל־ stranded); next line begins
with the scope-NP.

SEVERITY:
STRONG-MERGE-CANDIDATE — quantifier+scope is morphosyntactically tight.

ARCHITECTURAL CONSTRAINT — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. The te'amim
Unicode range (U+0591–U+05AF) does NOT appear in any predicate that decides
whether to fire a finding. Te'amim MAY appear in finding annotations as
informational defensibility-capture (Rule H8) — the trigger must remain
syntactic.

SCOPE CONSTRAINT:
Skip poetic register (Psalms, Job 3:1–42:6, Proverbs).

Output format:
    [DEVIATION]  file:line  quantifier-scope-integrity  STRONG-MERGE-CANDIDATE  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_quantifier_scope.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_quantifier_scope.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_quantifier_scope.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_quantifier_scope.py --json
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

# Te'amim-only regex (no niqqud) — used for checking if any te'amim are present
TEAMIM_ONLY_RE = re.compile(r"[֑-֯]")

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


def first_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[0] if toks else None


def last_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[-1] if toks else None


# ---------------------------------------------------------------------------
# Quantifier detection
# ---------------------------------------------------------------------------

# Quantifier skeletons (consonant-only after stripping points)
QUANTIFIER_SKELETONS = {
    "כל",      # כָּל — all
    "רב",      # רַב — many/much
    "מעט",     # מְעַט — little/few
    "מאד",     # מְאֹד — very (when used as quantifier modifying the scope-NP)
    "יתר",     # יֶתֶר — remaining/excess (rare as quantifier, but attested)
}


def last_token_is_quantifier(line: str) -> tuple[bool, str | None]:
    """Check if the last content token on `line` is a quantifier.

    Returns (True, quantifier_skeleton) if quantifier found, (False, None) otherwise.
    """
    last = last_content_token(line)
    if not last:
        return False, None
    bare = strip_points(last).rstrip(SOF_PASUQ)
    if not bare:
        return False, None

    # Direct skeleton match
    if bare in QUANTIFIER_SKELETONS:
        return True, bare

    # Maqqef-bound: כָּל־ → bare form is "כל־" → check after stripping maqqef
    if MAQQEF in bare:
        head = bare.split(MAQQEF)[0]
        if head in QUANTIFIER_SKELETONS:
            return True, head

    return False, None


def first_token_is_noun_phrase(line: str) -> bool:
    """Heuristic: does the first content token on `line` look like a noun phrase?

    Returns True if the first token looks like a noun (not a verb, prep, or particle).
    Conservative: we'd rather under-detect (skip the finding) than over-detect
    (emit a false positive), so we only flag clear noun cases.
    """
    first = first_content_token(line)
    if not first:
        return False
    bare = strip_points(first).rstrip(SOF_PASUQ)
    if not bare:
        return False

    # Reject particles, prepositions, conjunctions
    # (these are common line-openers that are NOT NPs with quantifier scope)
    REJECTED_OPENERS = {
        "ו", "את", "אם", "כי", "אל", "על", "את", "עם", "אחרי", "לפני",
        "מן", "בין", "תחת", "בעד", "נגד", "מעל", "מתחת", "בתוך", "מתוך",
        "הנה", "אף", "לכן", "ועתה", "אז", "עתה", "הוי", "אוי", "אהה", "אנא",
        "זה", "היא", "הוא", "הם", "הן", "אתה", "את", "אתם", "אתן",
        "לא",
    }
    if bare in REJECTED_OPENERS:
        return False

    # Reject known finite verb skeletons (simplified list from template)
    VERB_SKELETONS = {
        "אמר", "ראה", "שמע", "ידע", "ברא", "ברך", "הלך", "נתן", "עשה",
        "היה", "בא", "קם", "בנה", "לקח", "כתב", "כרת", "מצא", "נשא", "נפל",
        "ישב", "עבר", "אכל", "שתה", "מת", "חיה", "סר", "עלה", "ירד", "שב",
        "הכה", "הביא", "הוציא", "הגיד", "הציל", "צוה", "דבר", "פנה", "נסע",
        "יאמר", "תאמר", "ישמע", "יראה", "יבא", "יקם", "יעשה", "ילך", "יתן",
        "יקח", "ישב", "ידע", "ויהי", "ויאמר", "ויראה",
    }
    if bare in VERB_SKELETONS:
        return False

    # If not explicitly rejected, assume it's a noun-like unit.
    # (Nouns, adjectives, construct chains, etc.)
    return True


# ---------------------------------------------------------------------------
# Verse partitioning
# ---------------------------------------------------------------------------

def partition_into_verses(lines: list[str]) -> dict[int, tuple[int | None, int | None, list[int]]]:
    """Group line indices by verse.

    Returns a dict: line_index → (chapter, verse, [all_line_indices_in_this_verse])
    """
    result: dict[int, tuple[int | None, int | None, list[int]]] = {}
    cur_chapter: int | None = None
    cur_verse: int | None = None
    cur_indices: list[int] = []
    for i, line in enumerate(lines):
        ref = parse_verse_ref(line)
        if ref is not None:
            # Flush current
            if cur_indices:
                for idx in cur_indices:
                    result[idx] = (cur_chapter, cur_verse, cur_indices)
            cur_chapter, cur_verse = ref
            cur_indices = []
            continue
        if not line.strip():
            continue
        cur_indices.append(i)
    if cur_indices:
        for idx in cur_indices:
            result[idx] = (cur_chapter, cur_verse, cur_indices)
    return result


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
    findings: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    book = book_name_from_path(path)
    chapter_from_file = chapter_from_path(path)
    line_to_verse = partition_into_verses(lines)

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        # Determine verse context
        v_ctx = line_to_verse.get(i)
        chapter = v_ctx[0] if v_ctx else chapter_from_file
        verse = v_ctx[1] if v_ctx else None
        verse_indices = v_ctx[2] if v_ctx else []

        line_no = i + 1  # 1-based

        # --- Guard: skip poetic register ---
        if chapter is not None and is_poetic_register(book, chapter, verse):
            continue

        # --- Check if this line ends with a quantifier ---
        is_quant, quant_skeleton = last_token_is_quantifier(line)
        if not is_quant:
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

        # --- Check if next line begins with an NP (scope of quantifier) ---
        if not first_token_is_noun_phrase(next_line):
            continue

        # --- All triggers passed; emit STRONG-MERGE-CANDIDATE finding ---
        prior_text = line.strip()
        next_text = next_line.strip()

        prior_teamim = teamim_summary(line)
        next_teamim = teamim_summary(next_line)
        teamim_note = ""
        if prior_teamim or next_teamim:
            teamim_note = (
                f" Te'amim: {prior_teamim or '(none)'} on quantifier line, "
                f"{next_teamim or '(none)'} on scope-NP line — informational only."
            )

        annotation = (
            f"Quantifier {quant_skeleton!r} stranded from scope-NP. "
            f"Quantifier and its scope-noun form a single morphosyntactic unit."
            + teamim_note
        )

        brief = (
            f"quantifier {quant_skeleton!r} stranded from scope — "
            f"{prior_text} // {next_text}"
        )

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "quantifier-scope-integrity",
            "severity": "STRONG-MERGE-CANDIDATE",
            "quantifier": quant_skeleton,
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "prior_line": prior_text,
            "next_line": next_text,
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
                "quantifier": f["quantifier"],
                "book": f["book"],
                "chapter": f["chapter"],
                "verse": f["verse"],
                "prior_line": f["prior_line"],
                "next_line": f["next_line"],
                "next_line_num": f["next_line_num"],
                "annotation": f["annotation"],
            })

        counts = {"STRONG-MERGE-CANDIDATE": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        by_quantifier: dict[str, int] = {}
        for f in findings_json:
            q = f["quantifier"]
            by_quantifier[q] = by_quantifier.get(q, 0) + 1

        doc = {
            "validator": "validate_quantifier_scope",
            "rule": "quantifier-scope-integrity",
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
                "by_quantifier": by_quantifier,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output ---
    print("=" * 72)
    print(f"Quantifier Scope Integrity validator — Tanakh {tier_label}")
    print(f"Pattern: quantifier stranded from scope-NP (כָּל, רַב, מְעַט, מְאֹד, יֶתֶר)")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Findings      : {len(all_findings)}")

    by_quantifier: dict[str, int] = {}
    for f in all_findings:
        q = f["quantifier"]
        by_quantifier[q] = by_quantifier.get(q, 0) + 1
    if by_quantifier:
        print()
        for q, count in sorted(by_quantifier.items()):
            print(f"  {q}: {count}")
    print()

    if all_findings:
        for f in all_findings:
            print(
                f"[DEVIATION]  {f['file_rel']}:{f['line_num']}  "
                f"{f['rule']}  {f['severity']}  {f['quantifier']}  {f['brief']}"
            )
            if args.verbose:
                print(f"    {f['prior_line'][:120]}")
                print(f"    → {f['next_line'][:120]}")
                print(f"    {f['annotation']}")
                print()
    else:
        print("No findings. Quantifier scope integrity is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
