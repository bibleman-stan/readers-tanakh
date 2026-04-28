#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Rule H9 — Divine-Title Appositives.

Rule H9 (canon §5; Layer 3 editorial rule):
A divine-title appositive following YHWH or Elohim functions either as:
  - INTRODUCING (formal naming or first-occurrence revelation) → stack on own line
  - REFERENCING (already-established identity) → MERGE (default)

This validator detects compound divine name splits across line boundaries
(e.g., יְהוָה || צְבָאוֹת, אֱלֹהִים || אֱלֹהֵי).

TRIGGER:
Line N ends with יהוה, אלהים, or אדני; line N+1 begins with a recognized
divine-title appositive (צבאות, אלהים, אלהי, אלהינו, אלהיך, אלהיכם,
אלהיהם, אלהיו).

SEVERITY:
  STRONG-MERGE-CANDIDATE for compound divine names in REFERENCING context
  (the default case — most divine-title appositives are referencing).

  REVIEW-REQUIRED for INTRODUCING contexts (formal naming formulas,
  first-occurrence contexts, prophetic proclamation frames) — guard via
  contextual analysis of verse structure.

ARCHITECTURAL CONSTRAINT — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. Te'amim
does NOT appear in predicates that decide whether to fire. Te'amim MAY
appear in annotations as informational defensibility-capture.

Output format:
    [DEVIATION]  file:line  H9/divine-title-appositive  SEVERITY  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_divine_title_appositive.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_divine_title_appositive.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_divine_title_appositive.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_divine_title_appositive.py --json
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

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers
# ---------------------------------------------------------------------------

# Hebrew points (cantillation U+0591–U+05AF + niqqud U+05B0–U+05BC, U+05C1–U+05C2,
# U+05C4–U+05C5, U+05C7). Strip all points.
HEBREW_POINTS_RE = re.compile(r"[֑-ׇֽֿׁׂׅׄ]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"  # ׃
# Maqqef (orthographic word-joiner)
MAQQEF = "־"     # ־

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
# Divine-name and appositive heuristics
# ---------------------------------------------------------------------------

# Divine name skeletons that can host an appositive (after stripping points)
DIVINE_NAME_SKELETONS = {
    "יהוה",   # Tetragrammaton — primary
    "אלהים",  # Elohim — primary
    "אדני",   # Adonai (perpetual qere) — secondary
}

# Divine-title appositive skeletons that follow divine names
# (appositive member of the compound, stripped of points)
DIVINE_TITLE_FOLLOWERS = {
    "צבאות",    # צְבָאוֹת — "of hosts" (יְהוָה צְבָאוֹת)
    "אלהים",    # אֱלֹהִים — "God" (יְהוָה אֱלֹהִים)
    "אלהי",     # אֱלֹהֵי — construct "God of" (יְהוָה אֱלֹהֵי + genitive)
    "אלהינו",   # אֱלֹהֵינוּ — "our God"
    "אלהיך",    # אֱלֹהֶיךָ — "your God" (2ms)
    "אלהיכם",   # אֱלֹהֵיכֶם — "your God" (2mp)
    "אלהיהם",   # אֱלֹהֵיהֶם — "their God" (3mp)
    "אלהיו",    # אֱלֹהָיו — "his God"
}

# Heuristic: words that indicate INTRODUCING context (formal naming, first-occurrence)
# These are NOT exhaustive — they're high-confidence markers.
INTRODUCING_MARKERS = {
    "קרא",      # קָרָא "called" — formal naming (וַיִּקְרָא שְׁמוֹ)
    "קראו",     # "called" (pl)
    "ויקרא",    # וַיִּקְרָא "and he called"
    "אמר",      # אָמַר "said" — prophetic proclamation (כֹּה אָמַר יְהוָה)
    "אמרו",     # "said" (pl)
    "ויאמר",    # וַיֹּאמֶר "and he said"
    "כה",       # כֹּה "thus" — prophetic intro pattern (כֹּה אָמַר)
}


def line_ends_with_divine_name(line: str) -> tuple[bool, str | None]:
    """Returns (True, name_skeleton) if last content token is a divine name."""
    last = last_content_token(line)
    if not last:
        return False, None
    bare = strip_points(last).rstrip(SOF_PASUQ)
    if bare in DIVINE_NAME_SKELETONS:
        return True, bare
    return False, None


def line_starts_with_divine_title_follower(line: str) -> tuple[bool, str | None]:
    """Returns (True, follower_skeleton) if first content token is a divine-title appositive."""
    first = first_content_token(line)
    if not first:
        return False, None
    bare = strip_points(first).rstrip(SOF_PASUQ)
    if bare in DIVINE_TITLE_FOLLOWERS:
        return True, bare
    return False, None


def line_has_introducing_marker(line: str) -> bool:
    """Heuristic: does the line contain a formal-naming or prophetic-proclamation marker?"""
    for tok in content_tokens(line):
        bare = strip_points(tok).rstrip(SOF_PASUQ)
        if bare in INTRODUCING_MARKERS:
            return True
    return False


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

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        line_no = i + 1  # 1-based

        # --- Check if this line ends with a divine name ---
        ends_divine, divine_name = line_ends_with_divine_name(line)
        if not ends_divine:
            continue

        # --- Find next content line ---
        next_idx: int | None = None
        for j in range(i + 1, len(lines)):
            if is_skippable(lines[j]):
                continue
            next_idx = j
            break

        if next_idx is None:
            continue

        next_line = lines[next_idx]
        next_line_no = next_idx + 1

        # --- Check if next line starts with a divine-title appositive ---
        starts_follower, follower = line_starts_with_divine_title_follower(next_line)
        if not starts_follower:
            continue

        # --- Determine severity: INTRODUCING vs REFERENCING ---
        # INTRODUCING: line contains formal naming or prophetic-proclamation marker
        is_introducing = line_has_introducing_marker(line)

        if is_introducing:
            severity = "REVIEW-REQUIRED"
            brief = (
                f"INTRODUCING context: {divine_name} || {follower} — "
                f"requires contextual audit (formal naming, first-occurrence, or "
                f"prophetic proclamation frame)"
            )
        else:
            # REFERENCING: default — compound divine name in bound appositive use
            severity = "STRONG-MERGE-CANDIDATE"
            brief = (
                f"REFERENCING context (default): {divine_name} || {follower} — "
                f"compound divine name should MERGE"
            )

        prior_text = line.strip()
        next_text = next_line.strip()

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "H9/divine-title-appositive",
            "severity": severity,
            "divine_name": divine_name,
            "follower": follower,
            "is_introducing": is_introducing,
            "book": book,
            "chapter": chapter_from_file,
            "prior_line": prior_text,
            "next_line": next_text,
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
                "next_line": f["next_line_num"],
                "rule": f["rule"],
                "severity": f["severity"],
                "divine_name": f["divine_name"],
                "follower": f["follower"],
                "is_introducing": f["is_introducing"],
                "book": f["book"],
                "chapter": f["chapter"],
                "prior_text": f["prior_line"],
                "next_text": f["next_line"],
            })

        counts = {"REVIEW-REQUIRED": 0, "STRONG-MERGE-CANDIDATE": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        introducing_count = sum(1 for f in findings_json if f["is_introducing"])
        referencing_count = len(findings_json) - introducing_count

        doc = {
            "validator": "validate_divine_title_appositive",
            "rule": "H9",
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
                "by_context": {
                    "introducing": introducing_count,
                    "referencing": referencing_count,
                },
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output ---
    print("=" * 72)
    print(f"Rule H9 Divine-Title Appositive validator — Tanakh {tier_label}")
    print(f"Reference: canon §5 H9 (compound divine names)")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Findings      : {len(all_findings)}")

    introducing_count = sum(1 for f in all_findings if f["is_introducing"])
    referencing_count = len(all_findings) - introducing_count

    if all_findings:
        print()
        print(f"  INTRODUCING (review required)  : {introducing_count}")
        print(f"  REFERENCING (merge candidate)  : {referencing_count}")
        print()

        for f in all_findings:
            print(
                f"[DEVIATION]  {f['file_rel']}:{f['line_num']}  "
                f"{f['rule']}  {f['severity']}  {f['brief']}"
            )
            if args.verbose:
                print(f"    {f['prior_line'][:100]}")
                print(f"    → {f['next_line'][:100]}")
                print()
    else:
        print("No findings. Rule H9 divine-title appositive integrity is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
