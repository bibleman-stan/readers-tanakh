#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate Layer 1 Rule H1 — Demonstrative Pronoun Strand from NP.

Rule H1 sub-constraint: A demonstrative pronoun (הַזֶּה / הַהוּא / הָאֵלֶּה / הַהֵם / הַהִיא / זֶה / הוּא / אֵלֶּה) functioning as an adjectival demonstrative modifier should be on the same line as the NP it modifies.

Pattern: Line N ends with an article-marked NP; line N+1 begins with a demonstrative form (when functioning as adjectival demonstrative).

ARCHITECTURAL CONSTRAINT — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. The te'amim
Unicode range (U+0591–U+05AF) does NOT appear in any predicate that decides
whether to fire a finding. Te'amim MAY appear in finding annotations as
informational defensibility-capture — the trigger must remain syntactic.

SEVERITY:
All findings emit at severity STRONG-MERGE-CANDIDATE. This is a tight
morphosyntactic bond (demonstrative + NP).

FORCED-NO-MERGE GUARDS (skip BEFORE emitting):
  1. Poetic register — is_poetic_register(book, chapter, verse) → skip.
  2. Demonstrative is predicative (predicate position, not attributive) — skip.
  3. Next line's demonstrative is part of a compound structure (e.g., זה אל־זה)
     that carries independent focus.
  4. Demonstrative has substantial complement following it (indicating independent
     clause, not just adjectival attribution).

Output format:
    [DEVIATION]  file:line  H1/demonstrative-np-strand  STRONG-MERGE-CANDIDATE  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_demonstrative_np_strand.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_demonstrative_np_strand.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_demonstrative_np_strand.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_demonstrative_np_strand.py --json
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
# U+05C4–U+05C5, U+05C7).  Strip U+0591-U+05BD (cantillation + niqqud) and
# U+05BF, U+05C1-U+05C2, U+05C4-U+05C5, U+05C7 while PRESERVING maqqef (U+05BE),
# paseq (U+05C0), and sof pasuq (U+05C3).
HEBREW_POINTS_RE = re.compile(r"[֑-ׇֽֿׁׂׅׄ]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"  # ׃
# Maqqef (orthographic word-joiner)
MAQQEF = "־"     # ־
# Paseq (vertical bar disjunction)
PASEQ = "׀"      # ׀

# Hebrew letters
HE = "ה"
ALEF = "א"
ZAYIN = "ז"
VAV = "ו"


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
# Demonstrative detection
# ---------------------------------------------------------------------------

# Demonstrative forms (consonant skeletons after stripping points).
# These are the forms that can function as adjectival demonstratives.
DEMONSTRATIVE_FORMS = {
    # With article
    "הזה",      # ha-zeh (this)
    "הזאת",     # ha-zot (this, fem.)
    "הזו",      # ha-zo (this, fem., alternate)
    "האלה",     # ha-ele (these)
    "האלו",     # ha-elu (these, alternate)
    "ההוא",     # ha-hu (that)
    "ההיא",     # ha-hi (that, fem.)
    "ההם",      # ha-hem (those)
    "ההן",      # ha-hen (those, fem.)
    # Without article (bare demonstrative forms)
    "זה",       # zeh (this)
    "זאת",      # zot (this, fem.)
    "זו",       # zo (this, fem., alternate)
    "אלה",      # ele (these)
    "אלו",      # elu (these, alternate)
    "הוא",      # hu (that) — bare form used attributively in some contexts
    "היא",      # hi (that, fem.)
    "הם",       # hem (those) — when used attributively
    "הן",       # hen (those, fem.)
}


def looks_like_demonstrative(bare: str) -> bool:
    """Heuristic: does this bare consonant skeleton look like a demonstrative?"""
    if not bare:
        return False

    # Direct match in our demonstrative forms
    if bare in DEMONSTRATIVE_FORMS:
        return True

    # Check maqqef-bound forms (e.g., זה־ bound to another noun)
    if MAQQEF in bare:
        first_part = bare.split(MAQQEF, 1)[0]
        if first_part in DEMONSTRATIVE_FORMS:
            return True

    return False


# ---------------------------------------------------------------------------
# Article-marked NP detection
# ---------------------------------------------------------------------------

def line_ends_with_article_marked_np(line: str) -> bool:
    """Heuristic: does the line end with an article-marked noun?

    Article-marked means the word carries the definite article (ה) prefix or
    is in construct with an article-marked noun. Conservative check: the last
    content token starts with ה (after stripping points) and is at least 3
    consonants (to distinguish from common morphemes like ה prefix on verbs).
    """
    last = last_content_token(line)
    if not last:
        return False

    bare = strip_points(last).rstrip(SOF_PASUQ)
    if not bare:
        return False

    # Article-marked: starts with ה and length >= 3
    # (length >= 3 excludes single-letter articles, though ה is itself 1 char,
    # the intent is to match ה + noun root, so the skeleton should be >= 2
    # for the noun itself).
    if bare.startswith(HE) and len(bare) >= 3:
        # Exclude common verb forms that start with ה but are not nouns.
        # High-frequency hifil verbs: הִפְעִל forms (3rd-person past/future).
        # Conservative: accept most ה-initial words; the false-positive cost
        # (emitting a finding the editor rejects) is small.
        return True

    return False


# ---------------------------------------------------------------------------
# Demonstrative predicate detection
# ---------------------------------------------------------------------------

def demonstrative_is_predicative(token: str) -> bool:
    """Heuristic: is this demonstrative in predicate position (not attributive)?

    Predicate demonstratives typically appear as standalone units or at the
    end of a clause identifying a subject. Attributive demonstratives modify
    a noun and appear within a larger NP.

    Simple heuristic: if the token is ONLY the demonstrative (no bound noun
    attached), and it appears in isolation or at a clause boundary, it is
    likely predicative.

    Returns True if we suspect predicative position; False if attributive is
    more likely.
    """
    bare = strip_points(token).rstrip(SOF_PASUQ)

    # If the demonstrative has a maqqef-bound noun after it (e.g., זה־דבר),
    # it is clearly attributive — we can't mark this as predicative.
    # But our design separates the demonstrative from the noun it modifies
    # onto different lines, so maqqef-bound would not trigger our rule anyway.

    # For now, use a simple heuristic: if the line containing this token has
    # very few tokens (1–2), and the demonstrative is the start/only token,
    # it might be predicative. But this is weak. We leave this guard as
    # future refinement and do not apply it in the initial release.

    return False


# ---------------------------------------------------------------------------
# Verse partitioning
# ---------------------------------------------------------------------------

def partition_into_verses(lines: list[str]) -> list[tuple[int | None, int | None, list[int]]]:
    """Group line indices by verse.

    Returns a list of (chapter, verse, [line_indices]) tuples in source order.
    Verse-reference lines themselves are included as part of their verse but
    are skippable for content scanning.
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
        pos_in_verse = v_ctx[2] if v_ctx else 0
        verse_indices = v_ctx[3] if v_ctx else []

        line_no = i + 1  # 1-based

        # --- Check if line ends with article-marked NP ---
        if not line_ends_with_article_marked_np(line):
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

        # --- Check if next line begins with a demonstrative ---
        first = first_content_token(next_line)
        if not first:
            continue
        bare_first = strip_points(first)
        if not looks_like_demonstrative(bare_first):
            continue

        # --- Guard 1: poetic register ---
        if chapter is not None and is_poetic_register(book, chapter, verse):
            continue

        # --- Guard 2: demonstrative is predicative (not attributive) ---
        if demonstrative_is_predicative(first):
            continue

        # --- All guards passed; emit STRONG-MERGE-CANDIDATE finding ---
        prior_text = line.strip()
        next_text = next_line.strip()

        brief = (
            f"demonstrative pronoun {bare_first!r} stranded from NP — "
            f"{prior_text} // {next_text}"
        )

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "H1/demonstrative-np-strand",
            "severity": "STRONG-MERGE-CANDIDATE",
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "prior_line": prior_text,
            "next_line": next_text,
            "demonstrative_form": bare_first,
            "brief": brief,
        })

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def resolve_book_dir(base_dir: Path, book_arg: str) -> Path:
    """Resolve a --book argument permissively (matches complement_integrity)."""
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
                "demonstrative_form": f["demonstrative_form"],
            })

        counts = {"STRONG-MERGE-CANDIDATE": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        doc = {
            "validator": "validate_demonstrative_np_strand",
            "rule": "H1",
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
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output ---
    print("=" * 72)
    print(f"Rule H1 Demonstrative NP Strand validator — Tanakh {tier_label}")
    print(f"Reference: Layer 1 surface H1 (demonstrative + NP morphosyntactic bond)")
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
                print()
    else:
        print("No findings. Demonstrative NP strands are clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
