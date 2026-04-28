#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Rule M3 — Bare-Governor Indivisibility for Participles.

Rule M3 (canon §1, merge-override M3):
A bare governing participle — an active or passive participle standing alone on
a line with NO complement (direct object, PP, or clausal complement) — cannot
stand as its own line without at least one complement. The bare participle fails
the atomic-thought test because it is grammatical machinery awaiting content
(e.g., אוֹמֵר alone without speech, יוֹדֵעַ alone without a כִּי-clause).

This validator surfaces cases where:
  1. Line N is a single bare participle (no complement on the same line)
  2. Line N+1 carries the complement (PP, object, speech, clause)
  3. The two should MERGE per M3 (bare governor + complement = one atomic unit)

ARCHITECTURE CONSTRAINT — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. Te'amim Unicode
range (U+0591–U+05AF) does NOT appear in any predicate that decides whether to
fire a finding. Te'amim MAY appear in finding annotations as informational
defensibility-capture.

SEVERITY:
All findings emit at severity STRONG-MERGE-CANDIDATE. Rule M3 is a closed-list
merge-override with high confidence; the split itself (bare participle alone +
complement) is the violation.

POETIC REGISTER SKIP:
Skips all findings in poetic register (Psalms, Proverbs, Job 3:1-42:6).

Output format:
    [DEVIATION]  file:line  M3/bare-governing-participle  STRONG-MERGE-CANDIDATE  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_bare_governing_participle.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_bare_governing_participle.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_bare_governing_participle.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_bare_governing_participle.py --json
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

# Niqqud-only regex (no te'amim) — used for syntactic vowel inspection.
TEAMIM_ONLY_RE = re.compile(r"[֑-֯]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"
# Maqqef (orthographic word-joiner)
MAQQEF = "־"
# Paseq (vertical bar disjunction)
PASEQ = "׀"

# Niqqud individual marks
HOLAM = "ֹ"
SHEVA = "ְ"
PATAH = "ַ"
QAMATS = "ָ"
HIRIQ = "ִ"
QUBUTS = "ֻ"
TSERE = "ֵ"
SEGOL = "ֶ"
DAGESH = "ּ"

# Hebrew letters
BET = "ב"
KAF = "כ"
LAMED = "ל"
MEM = "מ"


def strip_points(token: str) -> str:
    """Return token with niqqud and te'amim stripped."""
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


# ---------------------------------------------------------------------------
# Participial morphology heuristic
# ---------------------------------------------------------------------------

def looks_like_participle(token: str) -> bool:
    """Heuristic: does this token bear participial morphology?

    Three patterns:
      1. M-prefix participles: token starts with מ + vowel + consonant
         (Pi'el meCaCeC, Pu'al meCuCaC, Hifil maCCiC, Hofal muCCaC,
         Hitpael mitCaCeC).
      2. Qal active participle: CoCeC — first consonant carries HOLAM, third
         consonant carries TSERE or SEGOL.
      3. Qal passive participle: CaCuC — first consonant carries QAMATS,
         middle consonant carries QUBUTS/SHURUQ-mark.
    """
    if not token:
        return False
    bare = strip_points(token)
    teamim_stripped = strip_teamim_only(token)
    if len(bare) < 2:
        return False

    # ---- Pattern 1: M-prefix participle ----
    if bare[0] == MEM and len(bare) >= 3:
        # Reject common מ-initial non-participles
        head_segment = bare.split(MAQQEF, 1)[0] if MAQQEF in bare else bare
        NOT_PARTICIPLE_M_HEADS = {
            "מן", "מי", "מה", "מאד", "מאז", "מתי", "מבלי", "מאין", "מאום", "מאומה",
            "מים", "מות", "מאה", "מקום", "מלך", "מלכים", "מצרים", "מואב",
            "משה", "מרים", "מצוה", "מצות", "מנחה", "מזבח", "מצרי", "מדבר",
            "משכן", "מסלה", "מפלה", "מטה", "מנשה", "מנוחה", "מספר",
            "משפחה", "משפט", "משפטים", "מעשה", "מעשי", "מקנה", "מצרף",
            "מחנה", "מחוז", "מבוא", "מערב", "מזרח", "מלאך", "מלאכי",
            "מולדת", "מאכל", "מתנה", "מחשבת", "מחשבה",
        }
        if head_segment in NOT_PARTICIPLE_M_HEADS or bare in NOT_PARTICIPLE_M_HEADS:
            return False
        if len(teamim_stripped) >= 2:
            v = teamim_stripped[1]
            # Participle-bearing prefix vowels
            if v in (SHEVA, PATAH, QAMATS, QUBUTS, HIRIQ):
                return True

    # ---- Pattern 2: Qal active participle CoCeC ----
    if len(teamim_stripped) >= 2:
        idx = 1
        if idx < len(teamim_stripped) and teamim_stripped[idx] == DAGESH:
            idx += 1
        if idx < len(teamim_stripped) and teamim_stripped[idx] in ("ׁ", "ׂ"):
            idx += 1
        if idx < len(teamim_stripped) and teamim_stripped[idx] == HOLAM:
            if len(bare) >= 3:
                # Reject common holam-initial nouns and other non-participles
                # את (pronoun) is a common false positive; אתו too
                if bare in ("יום", "אור", "כל", "טוב", "קדש", "ראש", "מות", "כהן",
                            "אהל", "אהלי", "אחד", "אזן", "אשר", "כתב", "את", "אתו", "אתה", "אתם", "אתן"):
                    return False
                # Also reject if the bare form is too short (participles are typically 3+ consonants
                # in a meaningful root pattern, not 2-letter pronouns or words)
                if len(bare) == 2:
                    return False
                # Qal active participles typically have tsere/segol on the third consonant.
                # Check for this pattern to avoid misidentifying nouns with holam on C1.
                # A true qal participle CoCeC should have a third consonant bearing tsere/segol.
                if len(teamim_stripped) >= 3:
                    # C1 has holam (confirmed by reaching this line)
                    # C3 should have tsere or segol for a qal participle
                    last_consonant_idx = len(teamim_stripped) - 1
                    if last_consonant_idx >= 2:
                        c3_vowel_after = None
                        # Look backward from end for the last vowel
                        for k in range(len(teamim_stripped) - 1, 0, -1):
                            if teamim_stripped[k] in (TSERE, SEGOL):
                                c3_vowel_after = teamim_stripped[k]
                                break
                        # If C3 doesn't have tsere/segol, it's less likely a qal participle
                        if c3_vowel_after not in (TSERE, SEGOL):
                            return False
                return True

    # ---- Pattern 3: Qal passive participle CaCuC ----
    if len(teamim_stripped) >= 4 and teamim_stripped[1] == QAMATS:
        if QUBUTS in teamim_stripped[2:]:
            if bare in ("ארץ", "אדם", "דבר", "בא", "אב", "אם", "אח", "כל"):
                return False
            return True

    return False


# ---------------------------------------------------------------------------
# Preposition heuristic
# ---------------------------------------------------------------------------

STANDALONE_PREPS = {
    "על", "אל", "מן", "עם", "תחת", "בין",
    "לפני", "אחרי", "מאחרי", "מלפני", "מפני", "מאת",
    "בעד", "נגד", "מעל", "מתחת", "בתוך", "מתוך",
}

COMPOUND_PREP_HEADS = {"על", "אל", "מן", "עד", "מעל", "מתחת", "בין", "בתוך", "מתוך"}


def starts_with_prep(line: str) -> tuple[bool, str | None]:
    """Does the first content token begin with a preposition?

    Returns (True, prep_skeleton) on match, (False, None) otherwise.
    """
    first = first_content_token(line)
    if not first:
        return False, None
    bare = strip_points(first)
    if not bare:
        return False, None

    # Maqqef-compound
    if MAQQEF in bare:
        head = bare.split(MAQQEF, 1)[0]
        if head in COMPOUND_PREP_HEADS or head in STANDALONE_PREPS:
            return True, head

    # Standalone preposition word
    if bare in STANDALONE_PREPS:
        return True, bare

    # Bound prefix prepositions (ב/ל/כ/מ + bound noun)
    teamim_stripped = strip_teamim_only(first)
    if len(bare) >= 3 and bare[0] in (BET, LAMED, KAF):
        if bare in ("לא", "לכן"):
            return False, None
        if len(teamim_stripped) >= 2:
            second_char = teamim_stripped[1]
            if second_char in (SHEVA, PATAH, SEGOL, HIRIQ):
                return True, bare[0]

    if len(bare) >= 3 and bare[0] == MEM:
        if len(teamim_stripped) >= 3:
            if teamim_stripped[1] == HIRIQ:
                return True, "מ"

    return False, None


def line_has_finite_verb(line: str) -> bool:
    """True if any content token on `line` looks like a finite verb."""
    # Simple heuristic: look for wayyiqtol patterns (וי, ות) or known verb skeletons
    for tok in content_tokens(line):
        bare = strip_points(tok)
        if not bare:
            continue
        # Wayyiqtol — simple check
        if bare.startswith(("וי", "ות", "ונ", "וא")) and len(bare) >= 4:
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

        # --- Guard: poetic register ---
        if chapter is not None and is_poetic_register(book, chapter, verse):
            continue

        # --- Check if line is a bare participle ---
        toks = content_tokens(line)
        if not toks:
            continue

        # Line must have exactly 1 token to be "bare"
        if len(toks) != 1:
            continue

        first_tok = toks[0]
        bare_first = strip_points(first_tok)

        # Reject tokens that are PPs (start with preposition prefix)
        # A bare participle won't start with prep prefix (those are on the complement line)
        if len(bare_first) >= 2 and bare_first[0] in (BET, LAMED, KAF, MEM):
            # Additional check: if it looks like a prep+noun, skip it
            is_prep, _ = starts_with_prep(line)
            if is_prep:
                continue

        if not looks_like_participle(first_tok):
            continue

        # Now we have a bare participle on line i.
        # Find the next content line in the same verse.
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
            # No next line in same verse → bare participle hangs without complement
            continue

        next_line = lines[next_idx]
        next_line_no = next_idx + 1

        # --- Check if next line starts with complement (PP or object) ---
        # For M3, we're looking for a complement that should have been on the same line
        # as the participle. Common cases:
        #   1. Next line starts with a preposition (PP complement)
        #   2. Next line starts with a direct object marker (את)
        #   3. Next line starts with a speech marker (speech after participle אוֹמֵר)
        #   4. Next line is a clause (כִּי, that, etc.)

        next_first_tok = first_content_token(next_line)
        if not next_first_tok:
            continue

        next_bare = strip_points(next_first_tok)
        complement_found = False
        complement_type = None

        # Check for preposition (PP complement)
        is_prep, prep_skel = starts_with_prep(next_line)
        if is_prep:
            complement_found = True
            complement_type = f"PP ({prep_skel})"

        # Check for direct object marker (את)
        if next_bare.startswith("את"):
            complement_found = True
            complement_type = "direct object (את)"

        # Check for speech/discourse markers (לֵאמֹר, etc.)
        # These are common complements to participles like אוֹמֵר
        if next_bare in ("לאמר", "אמר", "לאמר"):
            complement_found = True
            complement_type = "speech marker"

        # Check for כִּי clause (complement for יוֹדֵעַ, etc.)
        if next_bare in ("כי", "כן"):
            complement_found = True
            complement_type = "clause marker"

        if not complement_found:
            continue

        # --- Emit finding ---
        prior_text = line.strip()
        next_text = next_line.strip()

        brief = (
            f"bare governing participle + complement on next line — "
            f"{prior_text} // {next_text} "
            f"({complement_type})"
        )

        annotation = (
            f"Bare governing participle '{strip_points(first_tok)}' without complement "
            f"(M3 Bare-Governor Indivisibility). Complement type: {complement_type}. "
            f"Should merge: participle + complement form one atomic unit."
        )

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "M3/bare-governing-participle",
            "severity": "STRONG-MERGE-CANDIDATE",
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "prior_line": prior_text,
            "next_line": next_text,
            "complement_type": complement_type,
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
                "prior_line": f["prior_line"],
                "next_line": f["next_line"],
                "next_line_num": f["next_line_num"],
                "complement_type": f["complement_type"],
                "annotation": f["annotation"],
            })

        counts = {"STRONG-MERGE-CANDIDATE": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        doc = {
            "validator": "validate_bare_governing_participle",
            "rule": "M3",
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
    print(f"Rule M3 Bare-Governor Indivisibility validator — Tanakh {tier_label}")
    print(f"Reference: canon §1 M3 (participles awaiting complement)")
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
        print("No findings. Rule M3 bare-governor indivisibility is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
