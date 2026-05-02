#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate interrogative clause splits — interrogative particle stranded from its clause.

Pattern: Line ends with an interrogative particle (הֲ-, אִם, מִי, מָה, מָתַי, אַיֵּה,
אֵיךְ, לָמָה, מַדּוּעַ). Next line begins with a verb or NP completing the question.

Severity:
  STRONG-MERGE-CANDIDATE — for short interrogative clauses (≤6 prosodic words combined).
  REVIEW-REQUIRED — for longer clauses.

ARCHITECTURAL CONSTRAINT — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. The te'amim
Unicode range (U+0591–U+05AF) does NOT appear in any predicate that decides
whether to fire a finding. Te'amim MAY appear in finding annotations as
informational defensibility-capture.

REGISTER SKIP:
Validators that should skip poetic registers use is_poetic_register(). This
validator calls it at Guard 1 to suppress false positives in Sifrei Emet and
embedded-poetry chapters.

Output format:
    [DEVIATION]  file:line  interrogative-clause-split  STRONG-MERGE-CANDIDATE/REVIEW-REQUIRED  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_interrogative_clause.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_interrogative_clause.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_interrogative_clause.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_interrogative_clause.py --json
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
from _shared import morphology as M  # noqa: E402
from _shared import morph_alignment as MA  # noqa: E402

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
# Interrogative particle detection
# ---------------------------------------------------------------------------

# Interrogative particles (consonant-only after stripping niqqud + te'amim)
# Note: bare "ה" is NOT included. The interrogative heh is a prefix morpheme
# attached to the following word (הֲשָׁמַרְתָּ, הֲיֵשׁ etc.) — it never appears
# as a standalone word-final token in prose. Including bare "ה" would fire on
# any maqqef-split token whose last segment is a ה-final form (articles,
# pronominal suffixes, directional he). Removed per overfire audit 2026-04-28.
#
# "אם" is retained but severity is capped at REVIEW-REQUIRED (never STRONG)
# because אם is genuinely ambiguous: interrogative, conditional, and
# asseverative/oath (e.g., Gen 14:23 "אִם מִחוּט וְעַד שְׂרוֹךְ נַעַל").
# The severity cap is applied at finding-emit time below.
INTERROGATIVE_PARTICLES = {
    "אם",     # אִם (often in question contexts — capped at REVIEW-REQUIRED)
    "מי",     # מִי (who)
    "מה",     # מָה (what)
    "מתי",    # מָתַי (when)
    "איה",    # אַיֵּה (where)
    "איך",    # אֵיךְ (how)
    "למה",    # לָמָה (why / not-what)
    "מדוע",   # מַדּוּעַ (why)
}

# Particles for which STRONG-MERGE-CANDIDATE is appropriate (genuine
# interrogative particles with no asseverative/oath ambiguity)
STRONG_ELIGIBLE_PARTICLES = {
    "מי", "מה", "מתי", "איה", "איך", "למה", "מדוע",
}


def looks_like_interrogative_particle(bare: str) -> bool:
    """Heuristic: does this bare skeleton look like an interrogative particle?

    Matches direct particles (מי, מה, מתי, איה, איך, למה, מדוע, אם).
    Bare "ה" is excluded — the interrogative heh is always a prefix morpheme,
    not a standalone token; including it caused maqqef-split overfire.
    """
    if not bare:
        return False
    if bare in INTERROGATIVE_PARTICLES:
        return True
    return False


def line_ends_with_interrogative_particle(line: str) -> tuple[bool, str | None]:
    """Check if line ends with an interrogative particle.

    Returns (True, particle_skeleton) if match, (False, None) otherwise.
    """
    last = last_content_token(line)
    if not last:
        return False, None
    bare = strip_points(last).rstrip(SOF_PASUQ)
    # Handle maqqef-bound particles: על־מי, אל־איה
    if MAQQEF in bare:
        bare = bare.split(MAQQEF)[-1]  # take the last segment
    if looks_like_interrogative_particle(bare):
        return True, bare
    return False, None


# ---------------------------------------------------------------------------
# Verb / NP detection for next line
# ---------------------------------------------------------------------------

# Function words excluded from "NP-like" detection (prepositions + discourse
# particles that would not complete an interrogative clause).
_FUNCTION_WORDS = {
    "על", "אל", "מן", "עם", "תחת", "בין",
    "לפני", "אחרי", "מאחרי", "מלפני", "מפני", "מאת",
    "בעד", "נגד", "מעל", "מתחת", "בתוך", "מתוך",
    "הנה", "אף", "לכן", "ועתה", "אז", "עתה",
}


def next_line_starts_with_verb_or_np(
    line: str,
    tag_list: "list[list[str]] | None" = None,
) -> bool:
    """True if line begins with verb or NP content (completing the question).

    Tag-aware primary path: if `tag_list` (aligned per-token tags for this
    line) is provided, passes the first token's tags into M.is_finite_verb_token
    for authoritative verb classification (eliminates skel-heuristic FPs from
    noun homographs).  Skel-fallback automatic when tags absent.

    Conservative: returns True if the first token looks like a finite verb
    or is a noun-like word (not obviously a preposition or discourse particle).
    """
    first = first_content_token(line)
    if not first:
        return False
    # Tag-aware verb check for first token
    first_tags = tag_list[0] if (tag_list and len(tag_list) > 0) else None
    if M.is_finite_verb_token(first, tag_list=first_tags):
        return True
    # Noun-phrase-like: not a preposition, not a discourse particle.
    # Accept most other content words (bare skel check).
    bare = strip_points(first).replace(MAQQEF, "").replace(SOF_PASUQ, "").replace(PASEQ, "")
    if bare not in _FUNCTION_WORDS:
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

    # Build a lookup: line_index → (chapter, verse, position_within_verse, indices)
    line_to_verse: dict[int, tuple[int | None, int | None, int, list[int]]] = {}
    for ch, vs, indices in verses:
        for pos, idx in enumerate(indices):
            line_to_verse[idx] = (ch, vs, pos, indices)

    # ---------------------------------------------------------------------------
    # Morph alignment: load TAHOT morph tags for this chapter (None if absent).
    # Builds line_token_tags: {0-based line_idx → [tag_list_per_token]}.
    # Falls back to skel-heuristics on miss (no crash on absent morph files).
    # ---------------------------------------------------------------------------
    chapter_morph = MA.load_chapter_morph(path)

    # verse-partitioning needed for alignment — reuse verses list above.
    # Build a per-verse lookup: verse_num → [(1-based line_no, raw_line)]
    line_token_tags: dict[int, list[list[str]]] = {}
    if chapter_morph is not None:
        # Group lines by verse for alignment (need only content lines, not skippable).
        _verse_lines: dict[int | None, list[tuple[int, str]]] = {}
        for ch, vs, indices in verses:
            pairs = [(idx + 1, lines[idx]) for idx in indices]
            _verse_lines[vs] = pairs
        for vs, numbered_lines in _verse_lines.items():
            content = [(ln, raw) for ln, raw in numbered_lines if not is_skippable(raw)]
            if not content:
                continue
            ortho_tags = chapter_morph.get(vs)
            if ortho_tags is None:
                continue
            verse_text_lines = [raw for _, raw in content]
            aligned = MA.align_verse_tokens_to_tags(verse_text_lines, ortho_tags)
            if aligned is None:
                continue
            for ci, (ln, _raw) in enumerate(content):
                line_token_tags[ln - 1] = aligned[ci]  # store at 0-based index

    def _tag_list_for(line_idx: int) -> "list[list[str]] | None":
        """Return per-token tag lists for line_idx (0-based), or None on miss."""
        return line_token_tags.get(line_idx)

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

        # --- Guard 1: poetic register ---
        if chapter is not None and is_poetic_register(book, chapter, verse):
            continue

        # --- Check if line ends with interrogative particle ---
        ends_with_interrog, particle = line_ends_with_interrogative_particle(line)
        if not ends_with_interrog:
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

        # --- Check if next line begins with verb or NP completing the question ---
        next_tags = _tag_list_for(next_idx)
        if not next_line_starts_with_verb_or_np(next_line, tag_list=next_tags):
            continue

        # --- Determine severity based on combined prosodic word count ---
        combined_words = prosodic_word_count(line) + prosodic_word_count(next_line)
        if combined_words <= 6 and particle in STRONG_ELIGIBLE_PARTICLES:
            # STRONG only for unambiguous interrogative particles (מי, מה, etc.).
            # "אם" is capped at REVIEW-REQUIRED because it is genuinely ambiguous:
            # conditional, asseverative/oath (Gen 14:23), and interrogative uses
            # are all attested and not distinguishable by surface syntax alone.
            severity = "STRONG-MERGE-CANDIDATE"
        else:
            severity = "REVIEW-REQUIRED"

        # --- Emit finding ---
        prior_text = line.strip()
        next_text = next_line.strip()
        brief = (
            f"interrogative particle '{particle}' stranded from completing clause — "
            f"{prior_text} // {next_text} "
            f"({combined_words} prosodic words combined)"
        )

        annotation = (
            f"Interrogative particle '{particle}' (הֲ-, אִם, מִי, מָה, מָתַי, אַיֵּה, אֵיךְ, "
            f"לָמָה, מַדּוּעַ) stranded from its clause. Next line begins with verb or NP completing "
            f"the question. Merge candidate for short interrogative clauses (≤6 words combined)."
        )

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "interrogative-clause-split",
            "severity": severity,
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "prior_line": prior_text,
            "next_line": next_text,
            "particle": particle,
            "prosodic_word_count": combined_words,
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
                "particle": f["particle"],
                "prior_line": f["prior_line"],
                "next_line": f["next_line"],
                "next_line_num": f["next_line_num"],
                "prosodic_word_count": f["prosodic_word_count"],
                "annotation": f["annotation"],
            })

        counts = {"STRONG-MERGE-CANDIDATE": 0, "REVIEW-REQUIRED": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        doc = {
            "validator": "validate_interrogative_clause",
            "rule": "interrogative-clause-split",
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
    print(f"Interrogative Clause Split validator — Tanakh {tier_label}")
    print("Reference: interrogative particle stranded from its clause")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Findings      : {len(all_findings)}")

    severity_counts = {}
    for f in all_findings:
        sev = f["severity"]
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
    if severity_counts:
        print()
        for sev, count in sorted(severity_counts.items()):
            print(f"  {sev}: {count}")
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
        print("No findings. Interrogative clauses are clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
