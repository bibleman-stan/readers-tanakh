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
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_speech_intro_framing.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_speech_intro_framing.py --verbose
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
# Shared morphology + morph-alignment helpers
# ---------------------------------------------------------------------------
# Make _shared importable when this script is run as __main__.
sys.path.insert(0, str(REPO_ROOT / "validators"))
from _shared import morphology as M  # noqa: E402
from _shared import morph_alignment as MA  # noqa: E402

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
    "וידברו",   # wayyiqtol piel 3mp — and they spoke (audit 2026-05-01: missing)
    "ותאמר",    # wayyiqtol qal 3fs — and she said
    "ותאמרו",   # wayyiqtol qal 2/3 fp — and you/they (f) said (missing)
    "ותדבר",    # wayyiqtol piel 3fs — and she spoke (missing)
    "ויען",     # wayyiqtol qal 3ms — and he answered
    "ותען",     # wayyiqtol qal 3fs — and she answered (missing)
    "ויוסף",    # wayyiqtol hiphil 3ms — and he added/continued (idiom: ויוסף לאמר)
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
# Verse-grouping helper (mirrors validate_construct_chain.py)
# ---------------------------------------------------------------------------

_VERSE_REF_RE = re.compile(r"^\d+:\d+\s*$")


def _partition_into_verses(lines: list[str]) -> list[tuple[int, list[tuple[int, str]]]]:
    """Partition file lines into per-verse groups.

    Returns list of (verse_num, [(1-based line_no, raw_line), ...]) tuples.
    Lines preceding any verse header are discarded (blank preamble only).
    """
    groups: list[tuple[int, list[tuple[int, str]]]] = []
    cur_verse: int | None = None
    cur_lines: list[tuple[int, str]] = []
    for i, raw in enumerate(lines):
        line_no = i + 1
        s = raw.strip()
        m = _VERSE_REF_RE.match(s)
        if m:
            if cur_verse is not None and cur_lines:
                groups.append((cur_verse, cur_lines))
            cur_verse = int(s.split(":")[1])
            cur_lines = []
        elif s and cur_verse is not None:
            cur_lines.append((line_no, raw))
    if cur_verse is not None and cur_lines:
        groups.append((cur_verse, cur_lines))
    return groups


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    """Scan one text file for Rule H5 speech-intro framing violations.

    Uses TAHOT morph tags (via morph_alignment) when available to classify
    speech-verb tokens.  Falls back to the BARE_SPEECH_VERB_SKELETONS skeleton
    heuristic when tags are missing or verse alignment fails.
    """
    violations = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    # Load TAHOT morph alignment for this chapter (None if morph file absent).
    chapter_morph = MA.load_chapter_morph(path)

    # Build a lookup: file_line_index (0-based) → [tag_list_per_token]
    # tag_list_per_token[tok_idx] = list[str] (TAHOT tags for that token)
    # This lets the flat line-scan below look up tags by line index.
    line_token_tags: dict[int, list[list[str]]] = {}
    if chapter_morph is not None:
        verse_groups = _partition_into_verses(lines)
        for verse_num, verse_numbered_lines in verse_groups:
            content = [
                (ln, raw) for ln, raw in verse_numbered_lines
                if not is_skippable(raw)
            ]
            if not content:
                continue
            ortho_tags = chapter_morph.get(verse_num)
            if ortho_tags is None:
                continue
            verse_text_lines = [raw for _, raw in content]
            aligned = MA.align_verse_tokens_to_tags(verse_text_lines, ortho_tags)
            if aligned is None:
                continue
            for ci, (ln, _raw) in enumerate(content):
                # ln is 1-based; store at 0-based index
                line_token_tags[ln - 1] = aligned[ci]

    def _tag_list_for(line_idx: int, tok_idx: int) -> "list[str] | None":
        """Return TAHOT tag list for (line_idx, tok_idx), or None on miss."""
        tl = line_token_tags.get(line_idx)
        if tl is None:
            return None
        if tok_idx < 0 or tok_idx >= len(tl):
            return None
        return tl[tok_idx]

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

            # --- EXCEPTION: standalone לֵאמֹר line (Bug 1 fix) ---
            # Canon §1 SJ3 explicitly states: "לֵאמֹר alone — the bare
            # infinitive complementizer is a speech-act-announcement marker,
            # gets its own line at the point of speech-onset."
            # If the ONLY non-sof-pasuq token on the line IS לֵאמֹר itself,
            # this is the correct standalone rendering — do NOT flag.
            non_leemor_bare = [
                b for b in bare_tokens
                if b != LEEMOR_SKELETON and b != "׃" and b != ""
            ]
            if len(non_leemor_bare) == 0:
                # Pure standalone לֵאמֹר line — canonical, not a violation.
                continue

            # Count prosodic words in frame (excluding לֵאמֹר itself)
            prosodic_count = count_prosodic_words(frame_tokens)

            # --- CROSS-LINE BACK-SCAN for multi-line speech frames (Bug 2 fix) ---
            # When frame_tokens is empty or very short (לֵאמֹר is the first or
            # near-first token on the line), the full speech-intro frame may have
            # started on a prior line.  Back-scan up prior non-empty lines
            # (stopping at a verse-reference, blank line, or sof pasuq) to
            # accumulate additional frame tokens.
            if prosodic_count < 4:
                extra_tokens: list[str] = []
                for k in range(i - 1, -1, -1):
                    prev = lines[k]
                    if is_skippable(prev):
                        break  # blank / verse-ref line — frame doesn't continue
                    prev_bare = [strip_points(t) for t in prev.split()]
                    # Stop if prior line contains לֵאמֹר (nested or repeated)
                    if LEEMOR_SKELETON in prev_bare:
                        break
                    # Stop if prior line ends with sof pasuq (previous verse)
                    if prev.rstrip().endswith("׃"):
                        break
                    extra_tokens = list(prev.split()) + extra_tokens
                if extra_tokens:
                    prosodic_count += count_prosodic_words(extra_tokens)

            # Next non-empty line (to check if speech content follows on next line)
            next_content = ""
            next_content_line_num = None
            for j in range(i + 1, len(lines)):
                if not is_skippable(lines[j]):
                    next_content = lines[j].strip()
                    next_content_line_num = j + 1  # 1-based
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
                        "file_path": path,
                        "line_num": line_no,
                        "rule": "H5/speech-framing",
                        "severity": "STRONG-MERGE-CANDIDATE",
                        "brief": (
                            f"short frame ({prosodic_count} prosodic words + לֵאמֹר) "
                            f"isolated on its own line — merge with speech-opening below"
                        ),
                        "line": line.rstrip(),
                        "next_line": next_content,
                        "next_line_num": next_content_line_num,
                        "leemor_pos": leemor_pos,
                    })

            elif prosodic_count == 3:
                # BOUNDARY case (exactly 3 prosodic words + לֵאמֹר):
                # Judgment territory — flag REVIEW-REQUIRED.
                violations.append({
                    "file": path.name,
                    "file_path": path,
                    "line_num": line_no,
                    "rule": "H5/speech-framing",
                    "severity": "REVIEW-REQUIRED",
                    "brief": (
                        f"boundary case ({prosodic_count} prosodic words + לֵאמֹר) "
                        f"— short/long threshold is 3; editorial judgment required"
                    ),
                    "line": line.rstrip(),
                    "next_line": next_content,
                    "next_line_num": next_content_line_num,
                    "leemor_pos": leemor_pos,
                })

            else:
                # LONG frame (≥ 4 prosodic words + לֵאמֹר):
                # Frame MUST get its OWN line; speech opens on next line.
                if has_speech_on_same_line:
                    # Frame and speech-opening are on the same line. Violation.
                    violations.append({
                        "file": path.name,
                        "file_path": path,
                        "line_num": line_no,
                        "rule": "H5/speech-framing",
                        "severity": "STRONG-SPLIT-CANDIDATE",
                        "brief": (
                            f"long frame ({prosodic_count} prosodic words + לֵאמֹר) "
                            f"combined with speech content on same line — split after לֵאמֹר"
                        ),
                        "line": line.rstrip(),
                        "next_line": "",
                        "next_line_num": None,
                        "leemor_pos": leemor_pos,
                    })

        # --- Solo speech-verb check: line is exactly ONE bare speech-verb token ---
        # Per audit 2026-05-01 Class E: when an entire line is just a wayyiqtol
        # speech verb (e.g., 1 Sam 1:18 line 92 'וַתֹּ֕אמֶר' alone), the verb
        # is propositionally empty without its complement clause on the next line.
        # This is STRONG-MERGE-CANDIDATE (not REVIEW): the merge is unambiguously
        # correct — solo speech-verbs are never editorially defensible standalone.
        # Tag-aware path: skeleton membership gates entry; M.is_finite_verb_token
        # with TAHOT tags then confirms the token is truly a finite verb (not a
        # homographic noun). When tags are absent, the skeleton match alone
        # controls (skel-fallback), preserving prior behaviour.
        elif len(bare_tokens) == 1 and bare_tokens[0] in BARE_SPEECH_VERB_SKELETONS and (
            _tag_list_for(i, 0) is None
            or M.is_finite_verb_token(tokens[0], tag_list=_tag_list_for(i, 0))
        ):
            next_content = ""
            next_content_line_num = None
            for j in range(i + 1, len(lines)):
                if not is_skippable(lines[j]):
                    next_content = lines[j].strip()
                    next_content_line_num = j + 1  # 1-based
                    break
            if next_content:
                violations.append({
                    "file": path.name,
                    "file_path": path,
                    "line_num": line_no,
                    "rule": "H5/speech-framing",
                    "severity": "STRONG-MERGE-CANDIDATE",
                    "brief": (
                        f"solo speech verb ({tokens[-1]}) — propositionally empty; "
                        f"merge with following complement clause"
                    ),
                    "line": line.rstrip(),
                    "next_line": next_content,
                    "next_line_num": next_content_line_num,
                    "leemor_pos": None,
                })

        # --- Secondary check: bare speech verb at MULTI-WORD line end (no לֵאמֹר) ---
        # If the last token is a bare wayyiqtol speech verb on a multi-token line
        # (e.g., 'וַיַּעַן עֵלִי וַיֹּאמֶר'), this might be a framing situation
        # without לֵאמֹר. Lower confidence — REVIEW-REQUIRED.
        # Tag-aware: skeleton membership gates entry; TAHOT tag confirmation
        # suppresses FPs from non-verb homographs. Skel-fallback when tags absent.
        elif bare_tokens and bare_tokens[-1] in BARE_SPEECH_VERB_SKELETONS and (
            _tag_list_for(i, len(tokens) - 1) is None
            or M.is_finite_verb_token(tokens[-1], tag_list=_tag_list_for(i, len(tokens) - 1))
        ):
            next_content = ""
            next_content_line_num = None
            for j in range(i + 1, len(lines)):
                if not is_skippable(lines[j]):
                    next_content = lines[j].strip()
                    next_content_line_num = j + 1  # 1-based
                    break
            if next_content:
                violations.append({
                    "file": path.name,
                    "file_path": path,
                    "line_num": line_no,
                    "rule": "H5/speech-framing",
                    "severity": "REVIEW-REQUIRED",
                    "brief": (
                        f"bare speech verb at line end ({tokens[-1]}) without לֵאמֹר "
                        f"— check if speech content follows and framing length"
                    ),
                    "line": line.rstrip(),
                    "next_line": next_content,
                    "next_line_num": next_content_line_num,
                    "leemor_pos": None,
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
        "--v2",
        action="store_true",
        help="Scan v2/he (editorial gold standard) instead of v1/he-baseline.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show next-line context for each violation.",
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

    all_violations: list[dict] = []
    for path in files:
        all_violations.extend(scan_file(path, verbose=args.verbose))

    exit_code = 1 if all_violations else 0

    # --- JSON output mode ---
    if args.json:
        findings = []
        for v in all_violations:
            severity = v["severity"]
            # Determine applied_action from severity and לֵאמֹר position
            leemor_pos = v.get("leemor_pos")
            if severity == "STRONG-MERGE-CANDIDATE":
                applied_action = "merge_with_next"
            elif severity == "STRONG-SPLIT-CANDIDATE":
                # split_at_position_N where N is the token index of לֵאמֹר
                applied_action = (
                    f"split_at_position_{leemor_pos}"
                    if leemor_pos is not None
                    else "split_at_position_unknown"
                )
            else:  # REVIEW-REQUIRED
                applied_action = None

            findings.append({
                "file": str(v["file_path"].relative_to(REPO_ROOT)).replace("\\", "/"),
                "line": v["line_num"],
                "severity": "DEVIATION",
                "tag": severity,
                "rule_id": "H5.1",
                "rule_short": "direct-speech framing boundary",
                "brief": v["brief"],
                "next_line": v.get("next_line_num"),
                "applied_action": applied_action,
            })

        by_severity_json: dict[str, int] = {}
        by_tag: dict[str, int] = {}
        for f in findings:
            by_severity_json[f["severity"]] = by_severity_json.get(f["severity"], 0) + 1
            by_tag[f["tag"]] = by_tag.get(f["tag"], 0) + 1

        doc = {
            "validator": "validate_speech_intro_framing",
            "rule": "Rule H5 — Direct-Speech Framing Default",
            "layer": 3,
            "book": args.book or "all",
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": findings,
            "summary": {
                "total_findings": len(findings),
                "by_severity": by_severity_json,
                "by_tag": by_tag,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output (default) ---
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

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
