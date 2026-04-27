#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Rule H16 — FEF Wayehi Protasis.

Rule H16 (canon §5 H16; Layer 3 editorial rule):
The Hebrew narrative construction וַיְהִי (wayyehi) + temporal/circumstantial
protasis + main clause is the canonical Front-End Frame (FEF). The wayyiqtol
of הָיָה introduces a temporal frame; the protasis sets the scene; the main
clause resolves.

  **Diagnostic:** the wayehi-protasis is held together as ONE atomic temporal
  frame regardless of length. The main clause that follows opens on its own line.

Three violation patterns are detected:

  STRONG-MERGE-CANDIDATE — protasis split: a line begins with וַיְהִי but the
    temporal frame continues onto the next line(s) without the main clause having
    started. The frame must be held together as one colon.

  STRONG-SPLIT-CANDIDATE — protasis collapsed with main clause: a line
    containing וַיְהִי also contains the main clause's wayyiqtol verb on the
    SAME line. The protasis should be on its own colon; the main clause should
    open the next line.

  REVIEW-REQUIRED — ambiguous case: a וַיְהִי line is present but the validator
    cannot confidently determine whether the main clause has started (e.g., line
    ends without sof pasuq, next line's first word is ambiguous — could be
    continuation of protasis or start of main clause).

Wayyehi detection:
  Consonant skeleton ויהי (after stripping niqqud + te'amim) at line-initial
  position. Only the FIRST token of the line triggers the check; a ויהי that
  appears mid-line (after another wayyiqtol) is not a FEF opener.

Main-clause boundary heuristics:
  The main clause typically begins with another wayyiqtol verb. Surface
  heuristic: a token whose consonant skeleton starts with וי followed by at
  least two more consonants is likely a wayyiqtol (prefix וי + root consonants).
  When ANOTHER wayyiqtol appears after the initial וַיְהִי on the SAME line →
  STRONG-SPLIT-CANDIDATE (protasis and main clause collapsed on one line).

Existential ויהי exclusion (not a FEF):
  Standalone וַיְהִי functioning as "there was/became X" (existential) is NOT
  a FEF protasis. We distinguish it by checking: does the line consist only of
  ויהי + a subject NP with no temporal-marker tokens and end in sof pasuq?
  If so, the ויהי is existential — skip.
  Common temporal markers that confirm FEF status: כי, כאשר, and preposition-
  prefix tokens (בְּ, לְ) suggesting a temporal/circumstantial phrase.

Protasis-split detection (STRONG-MERGE-CANDIDATE):
  A line starts with ויהי and ends WITHOUT sof pasuq. The next non-blank,
  non-verse-ref line exists and is not the start of a new verse. This pattern
  represents the protasis split across multiple lines.

Exit code: 0 if zero findings, 1 if findings present, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_wayehi_protasis.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_wayehi_protasis.py --book jonah
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_wayehi_protasis.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_wayehi_protasis.py --json
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_wayehi_protasis.py --verbose
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

# Hebrew points range (U+0591–U+05C7): cantillation + niqqud
HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")

# Sof pasuq U+05C3 — verse-end marker
SOF_PASUQ = "׃"

# Maqqef U+05BE
MAQQEF = "־"


def strip_points(token: str) -> str:
    """Return token with all niqqud and te'amim stripped."""
    return HEBREW_POINTS_RE.sub("", token)


def bare_line(line: str) -> list[str]:
    """Return list of bare (point-stripped) tokens for a line."""
    return [strip_points(t) for t in line.split() if strip_points(t)]


# ---------------------------------------------------------------------------
# FEF-detection constants
# ---------------------------------------------------------------------------

# Consonant skeleton for וַיְהִי after stripping — exact match required at
# first-token position.
WAYEHI_SKELETON = "ויהי"

# Consonant prefix that identifies a wayyiqtol verb (וי + root consonants).
# A token is a wayyiqtol candidate if its bare form starts with וי and has
# length ≥ 4 (וי + at least 2 root consonants — avoids matching two-letter
# particles that happen to start with וי).
WAYYIQTOL_PREFIX = "וי"
WAYYIQTOL_MIN_LEN = 4

# Tokens that are themselves וַיְהִי (and NOT a different wayyiqtol) — we
# need to detect the SECOND wayyiqtol on a line, so we must NOT count the
# initial ויהי as the "second" verb.
#
# Tokens to exclude when scanning for the second wayyiqtol:
# the initial wayehi itself and its rare spelling variants.
WAYEHI_SPELLINGS = {"ויהי", "ויהיו"}

# Common temporal-marker consonant skeletons that confirm FEF (protasis)
# status rather than bare existential.
#   כִּי / כַּאֲשֶׁר / בְּ-prefix / לְ-prefix tokens
#   We use a prefix check for prepositional tokens since they fuse with nouns.
TEMPORAL_MARKERS = {"כי", "כאשר", "כעת", "בעת"}

# Prepositional prefixes (bare) that often begin temporal phrases.
# A token starting with one of these prefix consonants (after strip_points)
# that has length ≥ 2 may be a temporal PP.
TEMPORAL_PREFIXES = ("ב", "ל", "מ")

# Verse-reference line pattern: optional word + digits:digits
VERSE_REF_RE = re.compile(r"^(\S+\s+)?\d+:\d+\s*$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_skippable(line: str) -> bool:
    """Return True for blank lines and verse-reference-only lines."""
    s = line.strip()
    if not s:
        return True
    if VERSE_REF_RE.match(s):
        return True
    return False


def has_sof_pasuq(line: str) -> bool:
    """Return True if line (or its last token) contains sof pasuq."""
    return SOF_PASUQ in line


def is_wayyiqtol_candidate(bare_token: str) -> bool:
    """Heuristic: does this bare token look like a wayyiqtol verb?

    Wayyiqtol prefix: וי + root consonants.
    Minimum length 4 to exclude particles that start with וי.
    Excludes the ויהי skeleton itself (already the trigger; what we look for
    is a SECOND, different wayyiqtol on the same line).
    """
    if bare_token in WAYEHI_SPELLINGS:
        return False
    return (
        bare_token.startswith(WAYYIQTOL_PREFIX)
        and len(bare_token) >= WAYYIQTOL_MIN_LEN
    )


def has_temporal_marker(bare_tokens: list[str]) -> bool:
    """Return True if any token in the bare-token list looks like a temporal
    marker that would confirm this is a FEF protasis (not bare existential).

    Checks:
    - Exact match against TEMPORAL_MARKERS set.
    - Token starts with a temporal prepositional prefix (ב, ל, מ) and has
      length ≥ 2 (i.e., something is attached to the prefix).
    - Token contains a maqqef (bound prepositional phrase is a strong cue).
    """
    for tok in bare_tokens:
        if tok in TEMPORAL_MARKERS:
            return True
        # Maqqef-bound token — common in temporal phrases like בְּיוֹם־
        if MAQQEF in tok:
            return True
        # Prepositional-prefix token that is not a bare particle
        if len(tok) >= 2 and tok[0] in TEMPORAL_PREFIXES:
            return True
    return False


def is_fef_token(bare_token: str) -> bool:
    """Return True if this token is a strong FEF indicator.

    Strong FEF markers that appear immediately after ויהי:

    1. כ-prefix temporal connectors:
         כִּי (when/that), כַּאֲשֶׁר (when/as), כִּזְרֹחַ (when X rose)
         Surface: bare token starts with כ, length ≥ 2.

    2. Closed-list ב-temporal phrases (in the days of / at the time of):
         בִּימֵי, בָּעֵת, בְּיוֹם — these appear in the FEF "in the days of X"
         construction. Distinguished from locative בַּיָּם (at sea) by lexeme.

    3. אֶל-preposition introducing a recipient (prophetic reception formula):
         "The word of YHWH came to X" — אֶל marks the recipient of the speech
         event, confirming this is a FEF speech-intro frame.
         Surface: bare token starts with אל and length ≥ 3.

    The ב-prefix alone is ambiguous (both FEF temporal and locative), so only
    the closed-list ב-temporal tokens are treated as strong FEF markers.
    """
    # כ-prefix: כִּי, כַּאֲשֶׁר, כִּזְרֹחַ, כְּלוֹת, etc.
    if bare_token.startswith("כ") and len(bare_token) >= 2:
        return True
    # Closed-list ב-temporal
    B_TEMPORAL = {"בימי", "בעת", "ביום", "ביומו", "ביומה", "בלילה", "בשנת"}
    if bare_token in B_TEMPORAL:
        return True
    # אֶל-preposition (to / toward) — recipient marker in prophetic formula
    if bare_token.startswith("אל") and len(bare_token) >= 3:
        return True
    return False


def is_existential_wayehi(bare_tokens: list[str], next_line_bare: list[str]) -> bool:
    """Return True if this line looks like an existential ויהי, NOT a FEF.

    An existential ויהי is "there was/became X" — the verb introduces a new
    entity (subject NP) rather than a temporal frame.

    Detection logic (conservative — False means "flag it"):
    1. If there is a second wayyiqtol on the line → not existential (collapsed
       FEF + main clause; caller handles as STRONG-SPLIT-CANDIDATE).
    2. If any token on the line is a strong FEF indicator → not existential.
    3. If the first token of the NEXT line is a strong FEF indicator (e.g., אֶל
       starting the recipient phrase of a split reception formula) → not existential.
    4. Otherwise → likely existential (ויהי + bare subject NP); skip.

    We receive bare_tokens (stripped) for the current line and next_line_bare
    for the first token of the following content line.
    """
    # Skip first token (ויהי itself)
    rest = bare_tokens[1:]

    # Second wayyiqtol → STRONG-SPLIT-CANDIDATE territory; caller handles
    for tok in rest:
        if is_wayyiqtol_candidate(tok):
            return False

    # Any FEF-indicator token on the current line
    for tok in rest:
        if is_fef_token(tok):
            return False

    # FEF indicator on the next line (e.g., split reception formula where
    # "אֶל X" continuation is on the following line)
    if next_line_bare and is_fef_token(next_line_bare[0]):
        return False

    # No FEF signals; treat as existential.
    return True


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    """Scan one text file for Rule H16 FEF wayehi protasis violations."""
    findings = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        tokens = line.split()
        if not tokens:
            continue

        first_bare = strip_points(tokens[0])

        # --- Only process lines whose FIRST token is ויהי ---
        if first_bare != WAYEHI_SKELETON:
            continue

        line_no = i + 1  # 1-based
        all_bare = [strip_points(t) for t in tokens]

        # --- Find the next non-skippable content line (needed for existential check) ---
        next_line_content = ""
        next_line_num = None
        for j in range(i + 1, len(lines)):
            if not is_skippable(lines[j]):
                next_line_content = lines[j].strip()
                next_line_num = j + 1
                break

        next_bare = [strip_points(t) for t in next_line_content.split() if strip_points(t)]

        # --- Existential exclusion ---
        # If there is no strong FEF indicator on the current line or immediately
        # following line, and no second wayyiqtol → existential "there was/became X".
        # Existential ויהי (e.g., "there was a great storm") is NOT an H16 FEF;
        # skip it. Any split of an existential clause is an H2/H3 issue, not H16.
        if is_existential_wayehi(all_bare, next_bare):
            continue

        # --- Check for second wayyiqtol on the SAME line (STRONG-SPLIT-CANDIDATE) ---
        # Rest of tokens after the initial ויהי
        rest_bare = all_bare[1:]
        second_wayyiqtol_idx = None
        for k, tok in enumerate(rest_bare):
            if is_wayyiqtol_candidate(tok):
                second_wayyiqtol_idx = k + 1  # index in all_bare
                break

        if second_wayyiqtol_idx is not None:
            # There is a second wayyiqtol on the same line as ויהי.
            # The protasis and main clause are collapsed — flag STRONG-SPLIT.
            main_verb_token = tokens[second_wayyiqtol_idx]
            findings.append({
                "file": path.name,
                "file_path": path,
                "line_num": line_no,
                "tag": "STRONG-SPLIT-CANDIDATE",
                "brief": (
                    f"wayehi protasis collapsed with main clause on same line "
                    f"— main-clause verb {main_verb_token!r} should open next line"
                ),
                "line": line.rstrip(),
                "next_line": next_line_content,
                "next_line_num": next_line_num,
                "split_at": second_wayyiqtol_idx,
            })
            continue

        # --- Protasis-split detection (STRONG-MERGE-CANDIDATE) ---
        # The line starts with ויהי and does NOT end with sof pasuq.
        # The next line continues the frame (no new verse has started, no
        # sof pasuq closed the current verse on this line).
        # This represents the protasis split across multiple cola.
        if not has_sof_pasuq(line):
            # Confirm the next line is not a verse reference or blank.
            if next_line_content:
                # Check if the next line itself starts a new ויהי (unlikely,
                # but would be a separate FEF — not a continuation here).
                next_bare_first = strip_points(next_line_content.split()[0]) if next_line_content.split() else ""
                if next_bare_first == WAYEHI_SKELETON:
                    # The next line is a fresh ויהי — ambiguous. Flag REVIEW-REQUIRED.
                    findings.append({
                        "file": path.name,
                        "file_path": path,
                        "line_num": line_no,
                        "tag": "REVIEW-REQUIRED",
                        "brief": (
                            f"wayehi line without sof pasuq followed by another wayehi — "
                            f"ambiguous protasis boundary; editorial review required"
                        ),
                        "line": line.rstrip(),
                        "next_line": next_line_content,
                        "next_line_num": next_line_num,
                        "split_at": None,
                    })
                else:
                    findings.append({
                        "file": path.name,
                        "file_path": path,
                        "line_num": line_no,
                        "tag": "STRONG-MERGE-CANDIDATE",
                        "brief": (
                            f"wayehi protasis split across lines — "
                            f"merge continuation onto the wayehi line until main clause boundary"
                        ),
                        "line": line.rstrip(),
                        "next_line": next_line_content,
                        "next_line_num": next_line_num,
                        "split_at": None,
                    })
            else:
                # No next line — wayehi at end of file without sof pasuq.
                # This is probably a structural anomaly; flag REVIEW-REQUIRED.
                findings.append({
                    "file": path.name,
                    "file_path": path,
                    "line_num": line_no,
                    "tag": "REVIEW-REQUIRED",
                    "brief": (
                        f"wayehi line without sof pasuq and no following content — "
                        f"anomalous; editorial review required"
                    ),
                    "line": line.rstrip(),
                    "next_line": "",
                    "next_line_num": None,
                    "split_at": None,
                })
            continue

        # --- Line ends with sof pasuq, no second wayyiqtol ---
        # The ויהי line is self-contained (ends the verse).  This is the
        # CORRECT pattern for Jonah 1:1 in v2/he: the entire FEF protasis +
        # לֵאמֹר is on one line, closed with sof pasuq. No violation.
        # Fall through: no finding emitted.

    return findings


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
        help="Restrict scan to one book folder name (e.g. 'jonah'). "
             "Default: all books in the target directory.",
    )
    parser.add_argument(
        "--v2",
        action="store_true",
        help="Scan v2/he (editorial layer) instead of v1/he-baseline.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show next-line context for each finding.",
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

    all_findings: list[dict] = []
    for path in files:
        all_findings.extend(scan_file(path, verbose=args.verbose))

    exit_code = 1 if all_findings else 0

    # --- JSON output mode ---
    if args.json:
        out_findings = []
        for v in all_findings:
            tag = v["tag"]
            if tag == "STRONG-MERGE-CANDIDATE":
                applied_action = "merge_with_next"
            elif tag == "STRONG-SPLIT-CANDIDATE":
                split_at = v.get("split_at")
                applied_action = (
                    f"split_at_position_{split_at}"
                    if split_at is not None
                    else "split_at_position_unknown"
                )
            else:
                applied_action = None

            out_findings.append({
                "file": str(v["file_path"].relative_to(REPO_ROOT)).replace("\\", "/"),
                "line": v["line_num"],
                "severity": "DEVIATION",
                "tag": tag,
                "rule_id": "H16",
                "rule_short": "FEF Wayehi Protasis",
                "brief": v["brief"],
                "next_line": v.get("next_line_num"),
                "applied_action": applied_action,
            })

        by_severity: dict[str, int] = {}
        by_tag: dict[str, int] = {}
        for f in out_findings:
            by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1
            by_tag[f["tag"]] = by_tag.get(f["tag"], 0) + 1

        doc = {
            "validator": "validate_wayehi_protasis",
            "rule": "Layer 3 colometry — Rule H16",
            "layer": 3,
            "book": args.book or "all",
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": out_findings,
            "summary": {
                "total_findings": len(out_findings),
                "by_severity": by_severity,
                "by_tag": by_tag,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output (default) ---
    print("=" * 72)
    print(f"Rule H16 FEF Wayehi Protasis validator — Tanakh {tier_label}")
    print(f"Reference: canon §5 H16 (protasis own line; main clause fresh line)")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Findings      : {len(all_findings)}")

    by_tag_hr: dict[str, int] = {}
    for v in all_findings:
        by_tag_hr[v["tag"]] = by_tag_hr.get(v["tag"], 0) + 1
    if by_tag_hr:
        print()
        for tag, count in sorted(by_tag_hr.items()):
            print(f"  {tag}: {count}")
    print()

    if all_findings:
        for v in all_findings:
            print(
                f"[DEVIATION]  {v['file']}:{v['line_num']}  "
                f"H16/wayehi-protasis  {v['tag']}  {v['brief']}"
            )
            print(f"    {v['line'][:120]}")
            if args.verbose and v.get("next_line"):
                print(f"    → {v['next_line'][:120]}")
            print()
    else:
        print("No findings. Rule H16 FEF wayehi protasis is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
