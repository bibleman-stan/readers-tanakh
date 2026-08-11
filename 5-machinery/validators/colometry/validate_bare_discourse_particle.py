

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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate 1-method/canon Rule M3 (bare-governor indivisibility) + Rule H14 (discourse particles lead content).

Rule M3 + H14 (1-method/canon §1 M3 + §5 H14; Layer 3 editorial rule):
Hebrew discourse particles standing alone on a line with no following content
cannot be atomic thoughts on their own. A bare discourse particle (וְעַתָּה, לָכֵן,
עַל־כֵּן, אָז, עַתָּה, הִנֵּה, אַף, גַּם) that occupies an entire line while its
governed content appears on the immediately following line violates M3
(bare-governor indivisibility — the bare governor cannot stand alone as an
atomic thought) and H14 (particles lead content — the particle should be merged
with its content).

VIOLATION PATTERN:
  Line N consists of a single discourse-particle token with no additional
  content. Line N+1 begins with the content the particle governs. The fix:
  merge the particle and its content onto one line so the atomic thought
  (particle + content) remains together.

ARCHITECTURAL CONSTRAINT — NO TE'AMIM IN TRIGGER:
  The trigger uses Hebrew morpho-syntactic patterns ONLY. Te'amim
  (U+0591–U+05AF) do NOT appear in predicates that decide whether to fire
  a finding. Te'amim MAY appear in findings as defensibility-capture per H8.

DETECTION HEURISTICS:
  1. Content-token check: the line consists of a single non-punctuation token
     (after stripping niqqud + te'amim → consonant skeleton) that matches a
     discourse-particle skeleton.
  2. Next-line check: the next non-empty line is not blank and is not itself
     purely punctuation (must have actual content for the particle to govern).
  3. Maqqef-bound exclusion: if the line contains maqqef-joined tokens (prosodic
     word + clitic), it's not a "bare" particle — skip it.

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

SEVERITY:
  STRONG-MERGE-CANDIDATE per M3 + H14.

Output format:
    [DEVIATION]  file:line  M3+H14/bare-discourse-particle  STRONG-MERGE-CANDIDATE  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_bare_discourse_particle.py
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_bare_discourse_particle.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_bare_discourse_particle.py --v2
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_bare_discourse_particle.py --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants — two-tier layout: v1/he-baseline + v2/heb
# ---------------------------------------------------------------------------
REPO_ROOT = _find_repo_root()
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files"  / "v2" / "heb"

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


# ---------------------------------------------------------------------------
# Discourse-particle skeleton set
# ---------------------------------------------------------------------------

DISCOURSE_PARTICLE_SKELETONS: set[str] = {
    "הנה",    # הִנֵּה  — hinneh "behold"
    "ועתה",   # וְעַתָּה — ve'attah "and now"
    "עתה",    # עַתָּה  — attah "now"
    "לכן",    # לָכֵן  — lakhen "therefore"
    "עלכן",   # עַל־כֵּן — al-ken (maqqef-joined, appears as one token)
    "אז",     # אָז   — az "then"
    "אף",     # אַף   — af "also / even"
    "גם",     # גַּם  — gam "also"
    "רק",     # רַק   — raq "only"
    "אכן",    # אָכֵן  — akhen "indeed"
}

# Punctuation-only tokens to skip when determining if a line is "bare".
PUNCTUATION_SKELETONS: set[str] = {
    "׃",   # sof pasuq
    "׀",   # paseq
    "ס",   # setuma paragraph marker
    "פ",   # petucha paragraph marker
    "",    # empty after stripping
}


def is_punctuation_only(skeleton: str) -> bool:
    """Return True if this token's skeleton is pure punctuation / empty."""
    return skeleton in PUNCTUATION_SKELETONS or skeleton == MAQQEF


# ---------------------------------------------------------------------------
# Content-token helpers
# ---------------------------------------------------------------------------

def content_tokens(line: str) -> list[str]:
    """Return all non-punctuation tokens on the line (with points intact)."""
    out = []
    for tok in line.split():
        skel = strip_points(tok)
        if not is_punctuation_only(skel):
            out.append(tok)
    return out


def first_and_only_content_token(line: str) -> str | None:
    """Return the (raw) token if line has exactly one non-punctuation token, else None."""
    toks = content_tokens(line)
    if len(toks) == 1:
        return toks[0]
    return None


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    """Scan one text file for bare discourse-particle violations (M3 + H14)."""
    findings: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    book = path.parent.name
    chapter_match = re.search(r"-(\d+)\.txt$", path.name)
    chapter = int(chapter_match.group(1)) if chapter_match else None

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        line_no = i + 1  # 1-based

        # Check if this line has exactly one content token (a bare particle candidate).
        sole_token = first_and_only_content_token(line)
        if sole_token is None:
            continue

        # Check if that token is a discourse particle.
        sole_skeleton = strip_points(sole_token)
        if sole_skeleton not in DISCOURSE_PARTICLE_SKELETONS:
            continue

        # Find the next non-empty, non-skippable line.
        next_idx: int | None = None
        for j in range(i + 1, len(lines)):
            if not is_skippable(lines[j]):
                next_idx = j
                break

        # Only flag if there IS a next line with content (the particle governs something).
        if next_idx is None:
            continue

        next_line = lines[next_idx]
        next_line_no = next_idx + 1

        # Extra safety: verify next line has actual content tokens (not just punctuation).
        next_toks = content_tokens(next_line)
        if not next_toks:
            continue

        # All checks passed: bare particle on line N, content on line N+1.
        findings.append({
            "file": path.name,
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "M3+H14/bare-discourse-particle",
            "severity": "STRONG-MERGE-CANDIDATE",
            "book": book,
            "chapter": chapter,
            "particle_skeleton": sole_skeleton,
            "particle_display": sole_token,
            "line": line.rstrip(),
            "next_line": next_line.rstrip(),
            "brief": (
                f"bare discourse particle ‫{sole_token}‬ on own line; "
                f"merge with next line (M3 bare-governor indivisibility + H14 particles lead content)"
            ),
        })

    return findings


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
        help="Restrict scan to one book folder name (e.g. 'genesis'). Default: all books.",
    )
    parser.add_argument(
        "--v2",
        action="store_true",
        help="Scan v2/heb (post-editorial tier) instead of v1/he-baseline.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show next-line context for each finding.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as a single JSON document to STDOUT.",
    )
    args = parser.parse_args()

    base_dir = V2_DIR if args.v2 else V1_DIR
    tier_label = "v2/heb" if args.v2 else "v1/he-baseline"

    if not base_dir.exists():
        # Fall back to the other tier if the requested one doesn't exist
        alt = V2_DIR if not args.v2 else V1_DIR
        if alt.exists():
            base_dir = alt
            tier_label = "v2/heb" if alt is V2_DIR else "v1/he-baseline"
        else:
            print(f"ERROR: neither {V1_DIR} nor {V2_DIR} found.", file=sys.stderr)
            sys.exit(2)

    # Collect files
    if args.book:
        book_dir = base_dir / args.book
        if not book_dir.exists():
            # Try permissive match
            candidates = [d for d in base_dir.iterdir()
                         if d.is_dir() and args.book.lower() in d.name.lower()]
            if len(candidates) == 1:
                book_dir = candidates[0]
            elif len(candidates) > 1:
                print(
                    f"ERROR: ambiguous book name {args.book!r}; "
                    f"matches: {[d.name for d in candidates]}",
                    file=sys.stderr,
                )
                sys.exit(2)
            else:
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

    all_findings: list[dict] = []
    for path in files:
        all_findings.extend(scan_file(path, verbose=args.verbose))

    exit_code = 1 if all_findings else 0

    # --- JSON output mode ---
    if args.json:
        findings_json = []
        for f in all_findings:
            findings_json.append({
                "file": f["file_rel"],
                "line": f["line_num"],
                "next_line": f["next_line_num"],
                "severity": "DEVIATION",
                "tag": f["severity"],       # "STRONG-MERGE-CANDIDATE"
                "rule_id": "M3+H14",
                "rule_short": "Bare Discourse Particle",
                "book": f["book"],
                "chapter": f["chapter"],
                "particle": f["particle_skeleton"],
                "brief": f["brief"],
            })

        by_tag: dict[str, int] = {}
        for f in findings_json:
            by_tag[f["tag"]] = by_tag.get(f["tag"], 0) + 1

        doc = {
            "validator": "validate_bare_discourse_particle",
            "rule": "M3 + H14",
            "version": "1.0.0",
            "layer": 3,
            "book": args.book or "all",
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": findings_json,
            "counts": by_tag,
            "summary": {
                "total_findings": len(findings_json),
                "by_tag": by_tag,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output (default) ---
    print("=" * 72)
    print(f"Rule M3+H14 Bare Discourse Particle validator — Tanakh {tier_label}")
    print(
        "Particles: הִנֵה עַתָה וְעַתָה "
        "לָכֵן עַל־כֵן "
        "אָז אַף גַּם רַק אָכֵן"
    )
    print("Reference: 1-method/canon §1 M3 (bare-governor indivisibility) + §5 H14 (discourse particles)")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Findings      : {len(all_findings)}")

    # Tag summary
    by_tag: dict[str, int] = {}
    for f in all_findings:
        by_tag[f["severity"]] = by_tag.get(f["severity"], 0) + 1
    if by_tag:
        print()
        for tag, count in sorted(by_tag.items()):
            print(f"  {tag}: {count}")
    print()

    if all_findings:
        for f in all_findings:
            print(
                f"[DEVIATION]  {f['file_rel']}:{f['line_num']}  "
                f"{f['rule']}  {f['severity']}  {f['brief']}"
            )
            if args.verbose:
                print(f"    {f['line'][:120]}")
                print(f"    → {f['next_line'][:120]}")
            print()
    else:
        print(
            "No findings. Rule M3 bare-governor + H14 discourse-particle merge is clean."
        )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
