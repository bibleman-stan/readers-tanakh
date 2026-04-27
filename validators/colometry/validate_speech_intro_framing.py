#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Rule H5 — Direct-Speech Framing Default.

Rule H5 (canon §5 H5; Layer 3 editorial rule):
When a speech-intro frame ends with לֵאמֹר (the bare infinitive complementizer
marking speech onset), the frame length governs whether framing and speech-opening
appear on the same line or separate lines:

  - Short framing (≤ 3 prosodic words in the frame before לֵאמֹר):
    Framing merges with the speech-opening cola on ONE line.
    Violation: frame and speech-opening are on SEPARATE lines.

  - Long framing (≥ 4 prosodic words, or embedded location/recipient phrase):
    Framing gets its OWN line; speech opens on the NEXT line.
    Violation: frame and speech-opening appear on the SAME line.

  - Boundary case (exactly 3 prosodic words — judgment territory):
    Flag REVIEW-REQUIRED. The canon marks this as a judgment call.

Detection strategy:
  - Scan for lines containing לֵאמֹר (consonant skeleton: לאמר after point
    stripping). This is the primary speech-intro boundary marker.
  - Also detect bare וַיֹּאמֶר / וַיְדַבֵּר / וַיַּעַן at line end without לֵאמֹר
    immediately followed by speech content on the next line (heuristic; lower
    confidence — flagged REVIEW-REQUIRED).
  - Count prosodic words in the frame line (whitespace-delimited tokens that
    are not empty and not the לֵאמֹר token itself; maqqef-joined groups count
    as ONE prosodic word).
  - Apply short/long/boundary threshold.

Prosodic word counting:
  A prosodic word is a whitespace-delimited token (after stripping niqqud/te'amim).
  Maqqef-joined sequences (token contains ־) count as ONE prosodic word,
  regardless of how many orthographic words the maqqef joins.

Output format:
    [DEVIATION]  file:line_number  H5/speech-framing  SEVERITY  brief description

Where SEVERITY is one of:
    STRONG-MERGE-CANDIDATE   — long frame on same line as speech content (merge the frame up)
    STRONG-SPLIT-CANDIDATE   — short frame on its own line (split and merge with speech)
    REVIEW-REQUIRED          — boundary case (3 prosodic words) or bare speech verb at line end

Exit code: 0 if zero violations, 1 if violations found, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_speech_intro_framing.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_speech_intro_framing.py --book jonah
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_speech_intro_framing.py --v4
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_speech_intro_framing.py --verbose
"""

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1-he-baseline"
V4_DIR = REPO_ROOT / "data" / "text-files" / "v4-editorial"

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers
# ---------------------------------------------------------------------------

# Maqqef glyph (U+05BE)
MAQQEF = "־"

# Hebrew points range (U+0591–U+05C7): cantillation + niqqud
HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")


def strip_points(token: str) -> str:
    """Return token with all niqqud and te'amim stripped."""
    return HEBREW_POINTS_RE.sub("", token)


# ---------------------------------------------------------------------------
# Speech-intro markers
# ---------------------------------------------------------------------------

# לֵאמֹר — consonant skeleton after stripping: לאמר
# This is the canonical speech-onset boundary marker (Waltke-O'Connor §36.2.3).
LEEMOR_SKELETON = "לאמר"

# Bare speech verbs that may introduce direct speech without לֵאמֹר.
# Consonant skeletons (stripped): ויאמר ויאמרו ויאמרי וידבר
BARE_SPEECH_VERB_SKELETONS = {
    "ויאמר",    # wayyiqtol qal 3ms — and he said
    "ויאמרו",   # wayyiqtol qal 3mp — and they said
    "וידבר",    # wayyiqtol piel 3ms — and he spoke
    "ותאמר",    # wayyiqtol qal 3fs — and she said
    "ויען",     # wayyiqtol qal 3ms — and he answered
}

# Prophetic formula line — these get their OWN line regardless of length.
# Consonant skeletons: כה אמר יהוה, נאם יהוה
PROPHETIC_FORMULA_SKELETONS = {
    "כה",       # כֹּה — particle in כֹּה אָמַר יְהוָה
    "נאם",      # נְאֻם — oracle marker
}


def is_prophetic_formula_line(bare_tokens: list[str]) -> bool:
    """Return True if this line is a prophetic formula that gets its own line always.

    כֹּה אָמַר יְהוָה and נְאֻם יְהוָה are atomic formulaic units per Rule H5
    exception — they always get their own line regardless of word count.
    """
    if not bare_tokens:
        return False
    return bare_tokens[0] in PROPHETIC_FORMULA_SKELETONS


def count_prosodic_words(tokens: list[str]) -> int:
    """Count prosodic words in a token list.

    A whitespace-delimited token is ONE prosodic word.
    If a token contains a maqqef (joining multiple orthographic words),
    the entire maqqef-group is still ONE prosodic word.
    The לֵאמֹר token itself is NOT counted (it is the boundary marker,
    not part of the frame content being measured).
    """
    count = 0
    for tok in tokens:
        bare = strip_points(tok)
        if bare == LEEMOR_SKELETON:
            continue
        if bare:
            count += 1
    return count


# ---------------------------------------------------------------------------
# Skippable lines
# ---------------------------------------------------------------------------

def is_skippable(line: str) -> bool:
    """Return True for blank lines and verse-reference-only lines."""
    s = line.strip()
    if not s:
        return True
    if re.match(r"^(\w+\s+)?\d+:\d+$", s):
        return True
    return False


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    """Scan one text file for Rule H5 speech-intro framing violations."""
    violations = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        line_no = i + 1  # 1-based

        tokens = line.split()
        bare_tokens = [strip_points(t) for t in tokens]

        # --- Primary check: line contains לֵאמֹר ---
        if LEEMOR_SKELETON in bare_tokens:
            # Is this a prophetic formula? If so, it should be on its own
            # line — but that's the CORRECT behavior; don't flag those.
            if is_prophetic_formula_line(bare_tokens):
                continue

            leemor_pos = bare_tokens.index(LEEMOR_SKELETON)
            # Tokens in frame = everything before לֵאמֹר
            frame_tokens = tokens[:leemor_pos]
            # Tokens after לֵאמֹר on the SAME line (speech content co-located)
            speech_tokens_same_line = tokens[leemor_pos + 1:]

            # Count prosodic words in frame (excluding לֵאמֹר itself)
            prosodic_count = count_prosodic_words(frame_tokens)

            # Next non-empty line (to check if speech content follows on next line)
            next_content = ""
            for j in range(i + 1, len(lines)):
                if not is_skippable(lines[j]):
                    next_content = lines[j].strip()
                    break

            has_speech_on_same_line = bool(speech_tokens_same_line)
            has_speech_on_next_line = bool(next_content)

            if prosodic_count <= 2:
                # SHORT frame (≤ 2 prosodic words plus לֵאמֹר):
                # Frame MUST merge with speech-opening on one line.
                if not has_speech_on_same_line and has_speech_on_next_line:
                    # Frame is isolated — speech is on next line. Violation.
                    violations.append({
                        "file": path.name,
                        "line_num": line_no,
                        "rule": "H5/speech-framing",
                        "severity": "STRONG-MERGE-CANDIDATE",
                        "brief": (
                            f"short frame ({prosodic_count} prosodic words + לֵאמֹר) "
                            f"isolated on its own line — merge with speech-opening below"
                        ),
                        "line": line.rstrip(),
                        "next_line": next_content,
                    })

            elif prosodic_count == 3:
                # BOUNDARY case (exactly 3 prosodic words + לֵאמֹר):
                # Judgment territory — flag REVIEW-REQUIRED.
                violations.append({
                    "file": path.name,
                    "line_num": line_no,
                    "rule": "H5/speech-framing",
                    "severity": "REVIEW-REQUIRED",
                    "brief": (
                        f"boundary case ({prosodic_count} prosodic words + לֵאמֹר) "
                        f"— short/long threshold is 3; editorial judgment required"
                    ),
                    "line": line.rstrip(),
                    "next_line": next_content,
                })

            else:
                # LONG frame (≥ 4 prosodic words + לֵאמֹר):
                # Frame MUST get its OWN line; speech opens on next line.
                if has_speech_on_same_line:
                    # Frame and speech-opening are on the same line. Violation.
                    violations.append({
                        "file": path.name,
                        "line_num": line_no,
                        "rule": "H5/speech-framing",
                        "severity": "STRONG-SPLIT-CANDIDATE",
                        "brief": (
                            f"long frame ({prosodic_count} prosodic words + לֵאמֹר) "
                            f"combined with speech content on same line — split after לֵאמֹר"
                        ),
                        "line": line.rstrip(),
                        "next_line": "",
                    })

        # --- Secondary check: bare speech verb at line end (no לֵאמֹר) ---
        # If the last token is a bare wayyiqtol speech verb and the next line
        # has content, this might be a framing situation without לֵאמֹר.
        # Low confidence — REVIEW-REQUIRED only.
        elif bare_tokens and bare_tokens[-1] in BARE_SPEECH_VERB_SKELETONS:
            next_content = ""
            for j in range(i + 1, len(lines)):
                if not is_skippable(lines[j]):
                    next_content = lines[j].strip()
                    break
            if next_content:
                violations.append({
                    "file": path.name,
                    "line_num": line_no,
                    "rule": "H5/speech-framing",
                    "severity": "REVIEW-REQUIRED",
                    "brief": (
                        f"bare speech verb at line end ({tokens[-1]}) without לֵאמֹר "
                        f"— check if speech content follows and framing length"
                    ),
                    "line": line.rstrip(),
                    "next_line": next_content,
                })

    return violations


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
        "--v4",
        action="store_true",
        help="Scan v4-editorial files instead of v1-he-baseline.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show next-line context for each violation.",
    )
    args = parser.parse_args()

    base_dir = V4_DIR if args.v4 else V1_DIR
    tier_label = "v4-editorial" if args.v4 else "v1-he-baseline"

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

    all_violations: list[dict] = []
    for path in files:
        all_violations.extend(scan_file(path, verbose=args.verbose))

    # Report
    print("=" * 72)
    print(f"Rule H5 Direct-Speech Framing validator — Tanakh {tier_label}")
    print(f"Reference: canon §5 H5 (short ≤3 prosodic words; long ≥4)")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Violations    : {len(all_violations)}")

    # Severity summary
    by_severity: dict[str, int] = {}
    for v in all_violations:
        by_severity[v["severity"]] = by_severity.get(v["severity"], 0) + 1
    if by_severity:
        print()
        for sev, count in sorted(by_severity.items()):
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
        print("No violations found. Rule H5 speech-intro framing is clean.")

    sys.exit(1 if all_violations else 0)


if __name__ == "__main__":
    main()
