#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Rule H14 — Discourse Particles.

Rule H14 (canon §5 H14; Layer 3 editorial rule):
Hebrew discourse particles (הִנֵּה, וְעַתָּה, לָכֵן, עַל־כֵּן, אָז, אַף, גַּם, רַק, אָכֵן)
are sentence-introducing or topic-shifting markers that "lead content."
They should appear at the START of the cola whose content they govern,
not stranded at the END of the previous cola.

Because Hebrew grammar PERMITS either placement (PERMITTED-EITHER at Layer 1),
this is a Layer 3 editorial policy violation — emit [DEVIATION] not [MALFORMED].

VIOLATION PATTERN:
  A line ends with a discourse-particle token and the particle's governed
  content begins on the next line. The fix: merge the particle onto the
  next line so the particle leads its content.

DETECTION HEURISTICS:
  - Last-token check: the last NON-PUNCTUATION token on a line (after
    stripping niqqud + te'amim → consonant skeleton) matches a
    discourse-particle skeleton.
  - Sof-pasuq guard: if the line ends at a clause boundary (last
    character of stripped line is ׃), do NOT flag — clause-end
    positioning is a different editorial question.
  - Maqqef guard: if the particle skeleton appears mid-line (i.e. is
    not the final non-punctuation token), no violation.

PARTICLE SKELETON LIST (consonants only, after stripping points):
  הנה    — hinneh    "behold"
  ועתה   — ve'attah  "and now"
  עתה    — attah     "now" (standalone, non-prefixed form)
  לכן    — lakhen    "therefore"
  עלכן   — al-ken    "therefore / for this reason" (maqqef joins to one token)
  אז     — az        "then"
  אף     — af        "also / even"
  גם     — gam       "also"
  רק     — raq       "only"
  אכן    — akhen     "indeed"

Output format:
    [DEVIATION]  file:line_number  H14/discourse-particles  TAG  brief description

Exit code: 0 if zero violations, 1 if violations found, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_discourse_particles.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_discourse_particles.py --book jonah
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_discourse_particles.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_discourse_particles.py --json
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_discourse_particles.py --verbose
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

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers
# ---------------------------------------------------------------------------

# Maqqef glyph (U+05BE ־)
MAQQEF = "־"

# Sof pasuq glyph (U+05C3 ׃)
SOF_PASUQ = "׃"

# Hebrew points range U+0591–U+05C7: cantillation accents + niqqud vowels
HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")


def strip_points(token: str) -> str:
    """Return token with all niqqud and te'amim stripped (consonant skeleton only)."""
    return HEBREW_POINTS_RE.sub("", token)


# ---------------------------------------------------------------------------
# Discourse-particle skeleton set
# ---------------------------------------------------------------------------
#
# These are the consonant skeletons we match after strip_points().
# Maqqef-joined forms (e.g. עַל־כֵּן which appears as one whitespace token
# עַל־כֵּן) are handled by also stripping maqqef from the skeleton before
# matching. The MAQQEF glyph is NOT a pointing — it passes through
# strip_points unchanged. So for maqqef-joined particles we include the
# skeleton WITH maqqef (עלכן) as well as a separate entry in case the
# maqqef is absent in some witnesses.
#
# נָא (na, politeness particle) is excluded from line-final violation
# detection: it attaches to imperatives as a suffix-style particle and
# trailing na on a line is a different pattern than the topic-shifting
# particles. The canon explicitly distinguishes na-on-imperative from the
# sentence-initial particles.

DISCOURSE_PARTICLE_SKELETONS: set[str] = {
    "הנה",    # הִנֵּה  — hinneh "behold" (sentence-initial deictic)
    "ועתה",   # וְעַתָּה — ve'attah "and now" (discourse pivot, prefixed)
    "עתה",    # עַתָּה  — attah "now" (standalone, no vav)
    "לכן",    # לָכֵן  — lakhen "therefore"
    "עלכן",   # עַל־כֵּן — al-ken (maqqef-joined, appears as one token)
    "אז",     # אָז   — az "then" (temporal pivot)
    "אף",     # אַף   — af "also / even"
    "גם",     # גַּם  — gam "also"
    "רק",     # רַק   — raq "only"
    "אכן",    # אָכֵן  — akhen "indeed"
}

# Punctuation-only tokens to skip when looking for the last content token.
# We treat sof-pasuq as punctuation; maqqef is NOT punctuation (it bonds
# content tokens) but maqqef alone (bare ־ with no consonants) is skipped.
PUNCTUATION_SKELETONS: set[str] = {
    "׃",   # sof pasuq
    "׀",   # paseq
    "ס",   # setuma paragraph marker (bare ס in some TAHOT lines)
    "פ",   # petucha paragraph marker (bare פ)
    "",    # empty after stripping — skip
}


def is_punctuation_only(skeleton: str) -> bool:
    """Return True if this token's skeleton is pure punctuation / empty."""
    return skeleton in PUNCTUATION_SKELETONS or skeleton == MAQQEF


# ---------------------------------------------------------------------------
# Line helpers
# ---------------------------------------------------------------------------

def is_skippable(line: str) -> bool:
    """Return True for blank lines and verse-reference-only lines."""
    s = line.strip()
    if not s:
        return True
    # Verse reference lines: e.g. "1:1" or "Jonah 1:1"
    if re.match(r"^(\w+\s+)?\d+:\d+$", s):
        return True
    return False


def last_content_token(line: str) -> str | None:
    """Return the skeleton of the last non-punctuation, non-empty token on the line.

    Iterates from the end of the whitespace-split token list, stripping
    points from each token, until a non-punctuation skeleton is found.
    Returns None if all tokens are punctuation or the line is empty.
    """
    tokens = line.rstrip().split()
    for tok in reversed(tokens):
        skel = strip_points(tok)
        if not is_punctuation_only(skel):
            return skel
    return None


def line_ends_at_clause_boundary(line: str) -> bool:
    """Return True if the last non-whitespace CHARACTER of the line is sof-pasuq.

    Sof-pasuq (׃) marks the end of a Masoretic verse — a clause-end
    positioning is a different editorial question from particle stranding.
    Do not flag particles at clause-end even if they are the last content token.
    """
    stripped = line.rstrip()
    if not stripped:
        return False
    return stripped[-1] == SOF_PASUQ


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    """Scan one text file for Rule H14 discourse-particle stranding violations."""
    violations: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        line_no = i + 1  # 1-based

        # Guard 1: clause-boundary — particle at verse-end is not stranded.
        if line_ends_at_clause_boundary(line):
            continue

        # Find the last non-punctuation consonant skeleton on this line.
        skeleton = last_content_token(line)
        if skeleton is None:
            continue

        # Guard 2: only flag if this skeleton is a discourse particle.
        if skeleton not in DISCOURSE_PARTICLE_SKELETONS:
            continue

        # Find next non-empty content line (the line whose content the
        # particle should lead).
        next_content = ""
        next_content_line_num: int | None = None
        for j in range(i + 1, len(lines)):
            if not is_skippable(lines[j]):
                next_content = lines[j].strip()
                next_content_line_num = j + 1  # 1-based
                break

        # Only report if there IS a next line (the particle is genuinely
        # stranded with governed content below it).
        if not next_content:
            continue

        # Identify the original token (with pointing) for display.
        tokens = line.rstrip().split()
        display_token = tokens[-1] if tokens else skeleton  # raw form for display

        violations.append({
            "file": path.name,
            "file_path": path,
            "line_num": line_no,
            "rule": "H14/discourse-particles",
            "severity": "STRONG-MERGE-CANDIDATE",
            "skeleton": skeleton,
            "display_token": display_token,
            "brief": (
                f"discourse particle ‫{display_token}‬ stranded at line end; "
                f"merge with next line so particle leads content"
            ),
            "line": line.rstrip(),
            "next_line": next_content,
            "next_line_num": next_content_line_num,
        })

    return violations


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--book",
        metavar="BOOK",
        help="Restrict scan to one book folder name (e.g. 'jonah'). "
             "Default: all books in the target directory.",
    )
    parser.add_argument(
        "--v2",
        action="store_true",
        help="Scan v2/he (post-syntax-pass tier) instead of v1/he-baseline.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show next-line context for each violation.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as a single JSON document to STDOUT instead of "
             "human-readable lines.",
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
            print(
                f"ERROR: book directory not found: {book_dir}",
                file=sys.stderr,
            )
            sys.exit(2)
        files = sorted(book_dir.glob("*.txt"))
    else:
        files = sorted(base_dir.rglob("*.txt"))

    if not files:
        print(f"No .txt files found under {base_dir}", file=sys.stderr)
        sys.exit(2)

    all_violations: list[dict] = []
    for path in files:
        all_violations.extend(scan_file(path, verbose=args.verbose))

    exit_code = 1 if all_violations else 0

    # --- JSON output mode ---
    if args.json:
        findings = []
        for v in all_violations:
            findings.append({
                "file": str(v["file_path"].relative_to(REPO_ROOT)).replace("\\", "/"),
                "line": v["line_num"],
                "severity": "DEVIATION",
                "tag": v["severity"],       # "STRONG-MERGE-CANDIDATE"
                "rule_id": "H14",
                "rule_short": "Discourse Particles",
                "brief": v["brief"],
                "next_line": v.get("next_line_num"),
                "applied_action": "merge_with_next",
            })

        by_severity: dict[str, int] = {}
        by_tag: dict[str, int] = {}
        for f in findings:
            by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1
            by_tag[f["tag"]] = by_tag.get(f["tag"], 0) + 1

        doc = {
            "validator": "validate_discourse_particles",
            "rule": "Layer 3 colometry — Rule H14",
            "layer": 3,
            "book": args.book or "all",
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": findings,
            "summary": {
                "total_findings": len(findings),
                "by_severity": by_severity,
                "by_tag": by_tag,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output (default) ---
    print("=" * 72)
    print(f"Rule H14 Discourse Particles validator — Tanakh {tier_label}")
    print(
        "Particles: הִנֵה עַתָה וְעַתָה "
        "לָכֵן עַל־כֵן "
        "אָז אַף גַּם רַק אָכֵן"
    )
    print("Reference: canon §5 H14 — particles lead content, never trail prior clause")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Violations    : {len(all_violations)}")

    # Severity summary
    by_sev_human: dict[str, int] = {}
    for v in all_violations:
        by_sev_human[v["severity"]] = by_sev_human.get(v["severity"], 0) + 1
    if by_sev_human:
        print()
        for sev, count in sorted(by_sev_human.items()):
            print(f"  {sev}: {count}")
    print()

    if all_violations:
        for v in all_violations:
            print(
                f"[DEVIATION]  {v['file']}:{v['line_num']}  "
                f"{v['rule']}  {v['severity']}  {v['brief']}"
            )
            print(f"    {v['line'][:120]}")
            if args.verbose and v.get("next_line"):
                print(f"    → {v['next_line'][:120]}")
            print()
    else:
        print(
            "No violations found. Rule H14 discourse-particle leading is clean."
        )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
