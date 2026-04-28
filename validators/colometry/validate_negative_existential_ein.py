#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate negative existential אֵין negation-stranding split.

Rule: Negative existential אֵין (there is not) + subject NP split across cola.

Trigger: Line ends with אֵין (standalone or after maqqef junction); next line begins
with the subject NP. Or symmetric: line ends with NP, next line begins with
אֵין-clause.

Severity: STRONG-MERGE-CANDIDATE — Layer 1 negation-stranding REQUIRED-MERGE territory
(אֵין is in the negation set, per canon §5 Layer 1 H1 shape-cap table).

Architectural Constraint: NO TE'AMIM GLYPH PREDICATES. Skip poetic register
(Sifrei Emet bicolon parallelism risk).

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_negative_existential_ein.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_negative_existential_ein.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_negative_existential_ein.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_negative_existential_ein.py --json
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

# Niqqud-only regex (no te'amim)
TEAMIM_ONLY_RE = re.compile(r"[֑-֯]")

# Special marks
SOF_PASUQ = "׃"  # verse-end mark
MAQQEF = "־"     # word-joiner
PASEQ = "׀"      # disjunction mark

# Key negation term
EIN_BARE = "אין"  # אֵין without diacritics


def strip_points(token: str) -> str:
    """Return token with niqqud and te'amim stripped (consonant skeleton + marks)."""
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
    """Count prosodic words (whitespace-delimited content tokens)."""
    return len(content_tokens(line))


def first_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[0] if toks else None


def last_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[-1] if toks else None


# ---------------------------------------------------------------------------
# Negation-stranding detection
# ---------------------------------------------------------------------------

def is_ein(bare: str) -> bool:
    """True if the bare consonant skeleton is אֵין (negation existential)."""
    # אֵין after stripping points: אין
    # But check for maqqef-joined compounds: אֵין־X after strip is אין־X
    if bare == EIN_BARE:
        return True
    if bare.startswith(EIN_BARE + MAQQEF):
        return True
    return False


def line_ends_with_ein(line: str) -> tuple[bool, str | None]:
    """Returns (True, token) if last content token is אֵין (standalone or maqqef-bound).

    Returns (False, None) otherwise.
    """
    last = last_content_token(line)
    if not last:
        return False, None
    bare = strip_points(last).rstrip(SOF_PASUQ)
    if is_ein(bare):
        return True, last
    return False, None


def line_starts_with_np(line: str) -> bool:
    """Heuristic: does line begin with a likely noun phrase (subject)?

    Approximation: first token is NOT a preposition, NOT a finite verb, NOT אֵין.
    (If it's אֵין, then we have אֵין on both lines — not the pattern.)
    """
    first = first_content_token(line)
    if not first:
        return False
    bare = strip_points(first)

    # Reject אֵין on the next line too (we want NP on next line)
    if is_ein(bare):
        return False

    # Reject obvious prepositions (ב + noun, ל + noun, etc.)
    if bare and bare[0] in ("ב", "ל", "כ", "מ", "עַל", "אֶל", "מִן"):
        return False

    # If it's a known verb, reject
    KNOWN_VERBS = {"אמר", "ראה", "שמע", "ידע", "עשה", "היה", "בא", "נתן"}
    if bare in KNOWN_VERBS:
        return False

    # Heuristic: likely a noun (subject NP start)
    return True


def line_starts_with_ein(line: str) -> bool:
    """True if first content token is אֵין."""
    first = first_content_token(line)
    if not first:
        return False
    bare = strip_points(first)
    return is_ein(bare)


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

    # Build a lookup: line_index → (chapter, verse, position_within_verse)
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

        # --- Guard: poetic register (Sifrei Emet) ---
        if chapter is not None and is_poetic_register(book, chapter, verse):
            continue

        # --- Check for the split pattern ---

        # Pattern 1: line ends with אֵין, next line starts with NP
        ein_at_end, ein_token = line_ends_with_ein(line)
        if ein_at_end and line_starts_with_np(next_line):
            prior_text = line.strip()
            next_text = next_line.strip()
            combined_words = prosodic_word_count(line) + prosodic_word_count(next_line)

            findings.append({
                "file_path": path,
                "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "line_num": line_no,
                "next_line_num": next_line_no,
                "rule": "neg-existential-ein/split",
                "severity": "STRONG-MERGE-CANDIDATE",
                "pattern": "ein_ends_np_starts",
                "book": book,
                "chapter": chapter,
                "verse": verse,
                "prior_line": prior_text,
                "next_line": next_text,
                "prosodic_word_count": combined_words,
                "annotation": (
                    "Negative existential אֵין + subject NP split — clause-nucleus integrity "
                    "requires merge (Layer 1 negation-stranding boundary). אֵין is a single "
                    "unified negation marker that cannot be separated from its subject."
                ),
                "suggested_action": "MERGE candidate per Layer 1 negation-stranding rule",
                "brief": (
                    f"אֵין + NP negation stranding — {prior_text[:60]} // {next_text[:60]} "
                    f"({combined_words} prosodic words combined)"
                ),
            })
            continue

        # Pattern 2: line ends with NP, next line starts with אֵין (less common but valid)
        if line_starts_with_ein(next_line) and not ein_at_end:
            # Check that current line ends with a likely NP (has content, not a verb)
            last = last_content_token(line)
            if last:
                bare = strip_points(last).rstrip(SOF_PASUQ)
                # Reject if last token is a known finite verb
                KNOWN_VERBS = {"אמר", "ראה", "שמע", "ידע", "עשה", "היה", "בא", "נתן"}
                if bare not in KNOWN_VERBS and not bare.startswith("ו"):
                    prior_text = line.strip()
                    next_text = next_line.strip()
                    combined_words = prosodic_word_count(line) + prosodic_word_count(next_line)

                    findings.append({
                        "file_path": path,
                        "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                        "line_num": line_no,
                        "next_line_num": next_line_no,
                        "rule": "neg-existential-ein/split",
                        "severity": "STRONG-MERGE-CANDIDATE",
                        "pattern": "np_ends_ein_starts",
                        "book": book,
                        "chapter": chapter,
                        "verse": verse,
                        "prior_line": prior_text,
                        "next_line": next_text,
                        "prosodic_word_count": combined_words,
                        "annotation": (
                            "Negation existential אֵין clause-nucleus split with subject NP "
                            "preceding — clause-nucleus integrity requires merge. The NP + אֵין "
                            "pair forms a single unified predication."
                        ),
                        "suggested_action": "MERGE candidate per Layer 1 negation-stranding rule",
                        "brief": (
                            f"NP + אֵין negation stranding — {prior_text[:60]} // {next_text[:60]} "
                            f"({combined_words} prosodic words combined)"
                        ),
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
                "pattern": f["pattern"],
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

        by_pattern: dict[str, int] = {}
        for f in findings_json:
            by_pattern[f["pattern"]] = by_pattern.get(f["pattern"], 0) + 1

        doc = {
            "validator": "validate_negative_existential_ein",
            "rule": "neg-existential-ein",
            "version": "1.0.0",
            "layer": 1,
            "book": args.book or "all",
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": findings_json,
            "counts": counts,
            "summary": {
                "total_findings": len(findings_json),
                "by_severity": counts,
                "by_pattern": by_pattern,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output ---
    print("=" * 72)
    print(f"Negative Existential אֵין Validator — Tanakh {tier_label}")
    print(f"Reference: Layer 1 negation-stranding boundary rule")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Findings      : {len(all_findings)}")

    by_pattern: dict[str, int] = {}
    for f in all_findings:
        by_pattern[f["pattern"]] = by_pattern.get(f["pattern"], 0) + 1
    if by_pattern:
        print()
        for pat, count in sorted(by_pattern.items()):
            print(f"  {pat}: {count}")
    print()

    if all_findings:
        for f in all_findings:
            print(
                f"[STRONG-MERGE-CANDIDATE]  {f['file_rel']}:{f['line_num']}  "
                f"{f['rule']}  {f['pattern']}  {f['brief']}"
            )
            if args.verbose:
                print(f"    {f['prior_line'][:120]}")
                print(f"    → {f['next_line'][:120]}")
                print(f"    {f['annotation']}")
                print()
    else:
        print("No findings. Negative existential אֵין clause-nucleus integrity is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
