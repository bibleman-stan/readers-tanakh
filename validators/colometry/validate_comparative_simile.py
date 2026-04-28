#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Rule H19 (provisional) — Comparative Simile Integrity.

Rule H19 (Layer 3 editorial rule):
A comparative simile introduced by כְּ-prefix (meaning "like," "as," forming NP
similes such as כַּמַּיִם "like water," כְּחוֹל־הַיָּם "like the sand of the sea")
may be over-split from its associated predication. When a line ends with a
complete subject/predicate unit and the next line begins with a bare כְּ-prefixed
noun phrase (simile), the simile is a predicative adjunct of the prior line's
predicate and is a REVIEW-REQUIRED merge candidate.

ARCHITECTURAL CONSTRAINT — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. The te'amim
Unicode range (U+0591–U+05AF) does NOT appear in any predicate that decides
whether to fire a finding. Te'amim MAY appear in finding annotations as
informational defensibility-capture — the trigger must remain syntactic.

SEVERITY:
All findings emit at severity REVIEW-REQUIRED. Similes in prose may legitimately
stand as independent cola; in poetry (Sifrei Emet) comparative bicolon
parallelism is the default, so no finding is emitted for poetic books.

HARD SKIPS (no finding emitted):
  1. Poetic register — is_poetic_register(book, chapter, verse) → skip entirely.
  2. Sifrei Emet — Psalms, Proverbs, Job 3:1–42:6 (poetic register) → skip.

Output format:
    [DEVIATION]  file:line  H19/comparative-simile  REVIEW-REQUIRED  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_comparative_simile.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_comparative_simile.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_comparative_simile.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_comparative_simile.py --json
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
# U+05C4–U+05C5, U+05C7). Strip U+0591-U+05BD (cantillation + niqqud) and
# U+05BF, U+05C1-U+05C2, U+05C4-U+05C5, U+05C7 while PRESERVING maqqef (U+05BE),
# paseq (U+05C0), and sof pasuq (U+05C3).
HEBREW_POINTS_RE = re.compile(r"[֑-ׇֽֿׁׂׅׄ]")

# Te'amim only (for te'amim-free trigger checks)
TEAMIM_ONLY_RE = re.compile(r"[֑-֯]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"  # ׃
# Maqqef (orthographic word-joiner)
MAQQEF = "־"     # ־
# Paseq (vertical bar disjunction)
PASEQ = "׀"      # ׀

# Kaf-prefix (comparative marker)
KAF_PREFIX = "כ"
KAF_WITH_PREFIX_DAGESH = "כּ"  # כּ with dagesh (construct marker); treat same as כ


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


def prosodic_word_count(line: str) -> int:
    """Count prosodic words (whitespace-delimited tokens, with maqqef-joining)."""
    return len(content_tokens(line))


# ---------------------------------------------------------------------------
# Comparative כְּ-prefix detection
# ---------------------------------------------------------------------------

# Causal/explanatory particles and other non-simile כ-prefix forms.
# כִּי = "that" (causal, explanatory, or complement clause marker) — introduces clauses, NOT similes.
# כִּי־ = "that" with maqqef-attached following word.
# כֹּה = "thus" — adverbial, NOT a simile.
# כָּל = "all / every" — determiner, NOT a simile.
# כֵּן = "so / thus" — adverbial, NOT a simile.
#
# We explicitly exclude these from simile detection.
EXCLUDED_KAF_PARTICLES = {
    "כי",      # כִּי — causal/explanatory "that"
    "כה",      # כֹּה — thus (adverbial)
    "כל",      # כָּל — all (determiner/quantifier)
    "כן",      # כֵּן — so (adverbial response particle)
}


def starts_with_kaf_simile(line: str) -> bool:
    """True if line begins with כְּ + NP (comparative simile marker).

    Comparative כְּ introduces a noun phrase simile (כְּמַיִם "like water",
    כְּחוֹל־הַיָּם "like the sand of the sea", כִּדְמוּתְךָ "like your likeness").

    CRITICAL: Exclude כִּי (the causal/explanatory particle introducing
    complement clauses). כִּי is NOT a simile marker; it is a conjunction
    introducing a כִּי-clause (causal, explanatory, or complement).

    The test:
      1. First content token's skeleton (after stripping points) starts with כ.
      2. Check if it's an excluded non-simile particle (כִּי, כֹּה, כָּל, כֵּן).
      3. The rest of the token is NOT empty (i.e., the כ is attached to a noun).

    Special handling for כִּי: it appears as "כי" + following letter in stripped form.
    We check if the token starts with "כי" followed by a consonant cluster or
    if it's exactly "כי" (which shouldn't happen as a word boundary, but be safe).
    More reliable: check first 2 letters against "כי", "כה", "כל", "כן".
    """
    first = first_content_token(line)
    if not first:
        return False
    bare = strip_points(first)
    if not bare:
        return False

    # Check if it starts with כ or כּ
    if bare[0] not in (KAF_PREFIX, KAF_WITH_PREFIX_DAGESH):
        return False

    # Exclude non-simile particles by checking the first 2 letters.
    # These particles are all 2-letter skeletons.
    if len(bare) >= 2:
        prefix_2 = bare[:2]
        if prefix_2 in EXCLUDED_KAF_PARTICLES:
            return False

    # Also exclude exact matches for particles longer than 2 letters (unlikely but safe).
    if bare in EXCLUDED_KAF_PARTICLES:
        return False

    # At this point, כ + something that's NOT an excluded particle.
    # Likely a simile NP.
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

        # --- Guard 1: poetic register — skip if Sifrei Emet or embedded poetry ---
        if chapter is not None and is_poetic_register(book, chapter, verse):
            continue

        # --- Guard 2: next line must begin with כְּ-prefix simile ---
        if not starts_with_kaf_simile(next_line):
            continue

        # --- All guards passed; emit REVIEW-REQUIRED finding ---
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
            "Comparative כְּ-prefix simile (like, as): often a predicative adjunct "
            "that merges with the preceding clause when prosodic constraints allow. "
            "Similes in poetry (Sifrei Emet) are typically separate cola per "
            "parallel-bicolon structure, so this finding appears only in prose."
            + teamim_note
        )
        suggested = "REVIEW candidate for potential merge per simile adjunct pattern"
        brief = (
            f"comparative simile כְּ + NP — {prior_text[:60]} // {next_text[:60]}"
        )

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "H19/comparative-simile",
            "severity": "REVIEW-REQUIRED",
            "book": book,
            "chapter": chapter,
            "verse": verse,
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
                "next_line_num": f["next_line_num"],
                "rule": f["rule"],
                "severity": f["severity"],
                "book": f["book"],
                "chapter": f["chapter"],
                "verse": f["verse"],
                "prior_line": f["prior_line"],
                "next_line": f["next_line"],
                "annotation": f["annotation"],
                "suggested_action": f["suggested_action"],
            })

        counts = {"REVIEW-REQUIRED": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        doc = {
            "validator": "validate_comparative_simile",
            "rule": "H19",
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
    print(f"Rule H19 Comparative Simile validator — Tanakh {tier_label}")
    print(f"Reference: כְּ-prefix simile integrity (prose only; poetry skipped)")
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
        print("No findings. Rule H19 comparative-simile integrity is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
