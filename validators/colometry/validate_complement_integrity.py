#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Rule H7 — Complement Integrity (Hebrew).

Rule H7 (canon §5 H7; Layer 3 editorial rule):
A cognition/volition/causative verb and its clausal complement stay on the
same line. Splitting the matrix verb from its כִּי-clause complement violates
complement integrity.

VIOLATION PATTERN (primary focus — כִּי-clause complements):
  A cognition/volition/causative verb appears at line end (last content token),
  and the NEXT line begins with כִּי (consonant skeleton). The כִּי-clause is the
  complement of that matrix verb; the two must stay on one line.

VIOLATION TAGS:

  STRONG-MERGE-CANDIDATE  — cognition/volition/causative verb at line end +
                            כִּי-clause on next line, short complement (<8
                            prosodic words), no parallel כִּי-series, not
                            divine-speech recitativum context.

  REVIEW-REQUIRED         — same verb+כִּי pattern, but one exception fires:
                            (a) long-complement exception (≥8 prosodic words)
                            (b) parallel כִּי-series (≥2 כִּי-initial lines
                                following the same matrix verb)
                            (c) divine-speech recitativum context

COGNITION/VOLITION/CAUSATIVE VERB SKELETONS (consonant form after stripping
niqqud/te'amim):

  ידע  — know (יָדַע, יָדְעוּ, יָדַעְתִּי, יוֹדֵעַ, etc.)
  ראה  — see (רָאָה, וַיַּרְא, יִרְאֶה, etc.)
  שמע  — hear (שָׁמַע, שָׁמְעוּ, שָׁמַעְתִּי, etc.)
  זכר  — remember (זָכַר, אֶזְכֹּר, etc.)
  בין  — understand (בִּין, יָבִין, etc.; also hifil הֵבִין)
  חשב  — think/consider (חָשַׁב, יַחְשֹׁב, etc.)
  הגד  — tell (הִגִּיד, hifil of נגד; also ויגד wayyiqtol)
  אמר  — say (excluded when divine-speech context; else volition frame)
  דבר  — speak (excluded when divine-speech context)
  רצה  — desire/want (רָצָה, יִרְצֶה, etc.)
  חפץ  — delight/want (חָפֵץ, תֶּחְפָּץ, etc.)
  בקש  — seek (בִּקֵּשׁ, יְבַקֵּשׁ, etc.)
  צוה  — command (צִוָּה, יְצַוֶּה, etc.)
  גזר  — decree (גָּזַר, etc.)

EXCEPTIONS (demote to REVIEW-REQUIRED or skip):
  1. Long-complement: כִּי-line has ≥8 prosodic words → REVIEW-REQUIRED.
  2. Parallel כִּי-series: ≥2 of the next 3 content lines begin with כִּי
     skeleton → REVIEW-REQUIRED (each כִּי-clause earns its own line).
  3. Divine-speech recitativum: matrix verb is אמר or דבר AND יהוה skeleton
     appears within the same prosodic context → no violation (skip).

DELETE-TEST DIAGNOSTIC (per canon §5 H7):
  Remove intervening NP. If "[subject] [verb] כִּי X" is still coherent,
  כִּי is a complement → MERGE. If deletion breaks the clause, כִּי is
  appositive to a noun or causal — not a complement violation.

Output format:
    [DEVIATION]  file:line_number  H7/complement-integrity  SEVERITY  brief

Where SEVERITY is:
    STRONG-MERGE-CANDIDATE  — high-confidence complement split; auto-mergeable
    REVIEW-REQUIRED         — exception condition present; editorial judgment

Exit code: 0 if zero violations, 1 if violations found, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_complement_integrity.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_complement_integrity.py --book jonah
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_complement_integrity.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_complement_integrity.py --verbose
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_complement_integrity.py --json
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
# Shared morphology + morph-alignment helpers
# ---------------------------------------------------------------------------
# Make _shared importable when this script is run as __main__.
sys.path.insert(0, str(REPO_ROOT / "validators"))
from _shared import morphology as M  # noqa: E402
from _shared import morph_alignment as MA  # noqa: E402

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers
# ---------------------------------------------------------------------------

# Hebrew points: U+0591–U+05C7 (cantillation + niqqud)
HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")

# Sof pasuq U+05C3
SOF_PASUQ = "׃"

# Maqqef U+05BE
MAQQEF = "־"


def strip_points(token: str) -> str:
    """Return token with all niqqud and te'amim stripped."""
    return HEBREW_POINTS_RE.sub("", token)


def has_sof_pasuq(token: str) -> bool:
    """Return True if token contains sof pasuq (verse-end mark)."""
    return SOF_PASUQ in token


# ---------------------------------------------------------------------------
# Cognition/volition/causative verb skeletons
#
# These are consonant-only skeletons (after stripping niqqud/te'amim).
# We match the END of the last token's skeleton, because suffixes and
# maqqef-compounds may prepend material. The skeleton list covers the
# most common 3-consonant roots; we do substring matching on the skeleton
# rather than exact equality to handle inflected forms.
# ---------------------------------------------------------------------------

# Roots that take כִּי-clause complements (cognition, volition, causative).
# Each entry is a consonant substring that must appear in the bare (stripped)
# last token of the line.  Weak-verb paradigms produce surface forms that do
# not always contain the 3-letter root; we supplement with the most common
# alternate surface skeletons.
#
# Coverage philosophy: prefer zero false-positives over zero false-negatives.
# Forms that cannot be safely matched without a morphological analyzer are
# left uncovered; they produce no flag (miss) rather than a spurious flag.
COGNITION_ROOTS = {
    # --- KNOW ---
    "ידע",    # ידע root: יָדַע, יָדְעוּ, יָדַעְתִּי, יוֹדֵעַ, דַּעְתִּי, etc.

    # --- SEE ---
    "ראה",    # ראה root: רָאָה, יִרְאֶה, תִּרְאֶה, רָאִיתָ, etc.
    # Wayyiqtol 3ms/3mp of ראה → וַיַּרְא / וַיִּרְאוּ:
    # bare forms: וירא, ויראו — these do NOT contain ראה as substring.
    # We add the partial skeleton "ירא" which appears in those forms AND
    # in forms of ירא (fear), creating some false-positive risk.
    # Acceptable: ירא (fear) rarely governs a כִּי-complement at line end.
    # NOT added to avoid over-flagging — reviewer guidance in brief.

    # --- HEAR ---
    "שמע",    # שמע root: שָׁמַע, שָׁמְעוּ, יִשְׁמַע, שָׁמַעְתָּ, etc.

    # --- REMEMBER ---
    "זכר",    # זכר root: זָכַר, יִזְכֹּר, זָכַרְתִּי, etc.

    # --- UNDERSTAND ---
    "בין",    # בין root: בִּין, יָבִין, etc.
    "הבן",    # hifil הֵבִין → bare הבן (stripped of niqqud); hifil infinitive הָבִין

    # --- THINK / CONSIDER ---
    "חשב",    # חשב root: חָשַׁב, יַחְשֹׁב, חָשַׁבְתָּ, etc.

    # --- TELL (hifil of נגד) ---
    "הגד",    # hifil forms: הִגִּיד → bare הגד; יַגִּיד → bare יגד not matched here
    "נגד",    # qal/other: נָגַד → bare נגד (less common); wayyiqtol וַיַּגֵּד → bare ויגד
    "יגד",    # wayyiqtol 3ms of נגד hifil: וַיַּגֵּד → strip → ויגד; partial יגד present

    # --- DESIRE / WANT ---
    "רצה",    # רצה root: רָצָה, יִרְצֶה, etc.
    "חפץ",    # חפץ root: חָפֵץ, יַחְפֹּץ, חָפַצְתָּ, etc.

    # --- SEEK ---
    "בקש",    # בקש root (piel): בִּקֵּשׁ, יְבַקֵּשׁ, בִּקְשׁוּ, etc.

    # --- COMMAND / DECREE ---
    "צוה",    # צוה root (piel): צִוָּה, יְצַוֶּה, etc.
    "גזר",    # גזר root: גָּזַר, יִגְזֹר, etc.

    # --- SPEECH verbs (included; excluded by divine-speech check when applicable) ---
    "אמר",    # אמר root: אָמַר, יֹאמַר, אָמְרוּ, etc.
    "דבר",    # דבר root (piel): דִּבֶּר, יְדַבֵּר, דִּבְּרוּ, etc.
}

# Speech verbs that trigger the divine-speech recitativum exception
SPEECH_VERB_ROOTS = {"אמר", "דבר"}

# Divine name skeletons — used for divine-speech context detection
DIVINE_NAME_SKELETONS = {"יהוה", "אדני", "אלהים", "אל"}

# כִּי consonant skeleton
KI_SKELETON = "כי"


# ---------------------------------------------------------------------------
# Root matching helpers
# ---------------------------------------------------------------------------


def is_cognition_verb(bare_token: str) -> tuple[bool, str | None]:
    """Return (True, root) if bare_token is a cognition/volition/causative verb.

    Uses substring window matching against COGNITION_ROOTS.
    Returns (False, None) if no match.
    """
    # Generate candidate substrings
    token = bare_token

    # Check 3-char windows: does the token contain any root?
    for root in COGNITION_ROOTS:
        if root in token:
            return True, root

    # Maqqef-compound: take only the last component after last maqqef
    if MAQQEF in token:
        last_part = token.rsplit(MAQQEF, 1)[-1]
        for root in COGNITION_ROOTS:
            if root in last_part:
                return True, root

    return False, None


def is_ki_initial(bare_first: str) -> bool:
    """Return True if the bare first token of a line is כִּי (skeleton כי).

    Handles:
    - Bare כי
    - Maqqef-joined כי at start: כי־X (skeleton כי + maqqef + something)
    - Prefixed forms (rare, but מִכִּי is distinct; we check startswith)
    """
    if bare_first == KI_SKELETON:
        return True
    # Maqqef-joined: כי is the first component before a maqqef
    if bare_first.startswith(KI_SKELETON + MAQQEF) or bare_first.startswith(KI_SKELETON + "־"):
        return True
    # Vowel-bearing כִּי in bare form already stripped; exact match sufficient.
    return False


# ---------------------------------------------------------------------------
# Skippable lines
# ---------------------------------------------------------------------------

def is_skippable(line: str) -> bool:
    """Return True for blank lines and verse-reference-only lines."""
    s = line.strip()
    if not s:
        return True
    # Verse reference pattern: optional book name + N:N (or just N:N)
    if re.match(r"^(\S+\s+)?\d+:\d+$", s):
        return True
    return False


def first_bare_token(line: str) -> str | None:
    """Return the stripped first token of a line, or None."""
    tokens = line.split()
    if not tokens:
        return None
    return strip_points(tokens[0])


def count_prosodic_words(line: str) -> int:
    """Count prosodic words on a line (whitespace-delimited tokens, maqqef groups = 1).

    Excludes verse-reference tokens and sof-pasuq-only tokens.
    """
    count = 0
    for tok in line.split():
        bare = strip_points(tok)
        # Skip pure sof-pasuq
        if bare in ("׃", ""):
            continue
        # Skip verse-reference token (N:N)
        if re.match(r"^\d+:\d+$", bare):
            continue
        count += 1
    return count


# ---------------------------------------------------------------------------
# Divine-speech recitativum detection
# ---------------------------------------------------------------------------

def is_divine_speech_context(
    lines: list[str],
    line_index: int,
    matched_root: str,
) -> bool:
    """Return True if the matrix verb is in a divine-speech recitativum context.

    Per canon §5 H7 exception 3: when the matrix verb is אמר or דבר AND
    יהוה appears within the same prosodic context (same line or previous
    non-empty line), treat as divine-speech recitativum — the כִּי is
    direct-discourse, not a complement כִּי.

    We check:
    - The matched root is in SPEECH_VERB_ROOTS (אמר or דבר).
    - The current line or the immediately preceding content line contains
      a token whose bare form is in DIVINE_NAME_SKELETONS.
    """
    if matched_root not in SPEECH_VERB_ROOTS:
        return False

    # Check current line
    current_bare = [strip_points(t) for t in lines[line_index].split()]
    for bt in current_bare:
        if bt in DIVINE_NAME_SKELETONS:
            return True

    # Check previous content line
    for k in range(line_index - 1, -1, -1):
        if is_skippable(lines[k]):
            continue
        prev_bare = [strip_points(t) for t in lines[k].split()]
        for bt in prev_bare:
            if bt in DIVINE_NAME_SKELETONS:
                return True
        # Only look back one content line
        break

    return False


# ---------------------------------------------------------------------------
# Parallel כִּי-series detection
# ---------------------------------------------------------------------------

def has_parallel_ki_series(
    lines: list[str],
    start_index: int,
) -> bool:
    """Return True if ≥2 of the next 3 content lines begin with כִּי skeleton.

    Canon §5 H7 exception 2: a parallel כִּי-series (N≥2 כִּי-clauses following
    one matrix verb) means each כִּי-clause earns its own line.

    start_index: the index of the NEXT content line (the first כִּי-line).
    We look at start_index and the following 2 content lines (3 total).
    """
    ki_count = 0
    content_seen = 0

    for k in range(start_index, len(lines)):
        if is_skippable(lines[k]):
            continue
        bare_first = first_bare_token(lines[k])
        if bare_first and is_ki_initial(bare_first):
            ki_count += 1
        content_seen += 1
        if content_seen >= 3:
            break

    return ki_count >= 2


# ---------------------------------------------------------------------------
# Verse-grouping helper (mirrors validate_speech_intro_framing.py)
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
    """Scan one text file for Rule H7 complement-integrity violations.

    Uses TAHOT morph tags (via morph_alignment) when available to confirm that
    the last token on a line is actually a finite verb before checking the
    cognition-root membership.  Falls back to skel-only cognition matching when
    tags are absent or verse alignment fails — preserving prior behaviour.
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
        if not tokens:
            continue

        last_token = tokens[-1]
        bare_last = strip_points(last_token)

        # --- Gate 1: line must NOT end with sof pasuq ---
        # (a verse-final line cannot be the matrix of a cross-line complement)
        if has_sof_pasuq(last_token):
            continue

        # --- Gate 2: check if last token is a cognition/volition/causative verb ---
        matched, root = is_cognition_verb(bare_last)
        if not matched:
            continue

        # --- Gate 2b: tag-aware finite-verb confirmation (suppresses FP from
        #     nouns that happen to contain a cognition-root substring, e.g.
        #     דָּבָר "word" containing דבר, יָד "hand" + בין constructs, etc.).
        #     When TAHOT tags are available, we require the token to be a finite
        #     verb before treating it as a matrix verb.  When tags are absent,
        #     we fall through (skel-only path preserved for graceful degradation).
        last_tok_idx = len(tokens) - 1
        last_tok_tags = _tag_list_for(i, last_tok_idx)
        if last_tok_tags is not None and not M.is_finite_verb_token(last_token, tag_list=last_tok_tags):
            continue

        # --- Gate 3: find next content line and check if it begins with כִּי ---
        next_line = ""
        next_line_num = None
        next_line_index = None
        for j in range(i + 1, len(lines)):
            if not is_skippable(lines[j]):
                next_line = lines[j]
                next_line_num = j + 1  # 1-based
                next_line_index = j
                break

        if not next_line:
            continue

        next_bare_first = first_bare_token(next_line)
        if not next_bare_first:
            continue

        if not is_ki_initial(next_bare_first):
            continue

        # --- We have a cognition verb + line-initial כִּי pattern ---

        # --- Exception 3: divine-speech recitativum ---
        if is_divine_speech_context(lines, i, root):
            # Not a complement כִּי — it's recitativum direct discourse. Skip.
            continue

        # --- Exception 1: long-complement ---
        ki_line_word_count = count_prosodic_words(next_line)
        is_long_complement = ki_line_word_count >= 8

        # --- Exception 2: parallel כִּי-series ---
        is_parallel_series = has_parallel_ki_series(lines, next_line_index)

        # --- Determine severity ---
        if is_long_complement or is_parallel_series:
            severity = "REVIEW-REQUIRED"
            if is_long_complement and is_parallel_series:
                exception_note = "long complement AND parallel כִּי-series"
            elif is_long_complement:
                exception_note = f"long complement ({ki_line_word_count} prosodic words ≥ 8)"
            else:
                exception_note = "parallel כִּי-series detected"
            brief = (
                f"cognition verb {last_token!r} (root {root}) at line end + "
                f"כִּי-complement on next line; REVIEW — {exception_note}"
            )
        else:
            severity = "STRONG-MERGE-CANDIDATE"
            brief = (
                f"cognition verb {last_token!r} (root {root}) at line end + "
                f"כִּי-complement on next line ({ki_line_word_count} words); merge"
            )

        violations.append({
            "file": path.name,
            "file_path": path,
            "line_num": line_no,
            "rule": "H7/complement-integrity",
            "severity": severity,
            "brief": brief,
            "line": line.rstrip(),
            "next_line": next_line.rstrip(),
            "next_line_num": next_line_num,
            "root": root,
            "ki_line_word_count": ki_line_word_count,
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
        help="Scan v2/he instead of v1/he-baseline.",
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
        # Support both bare book name and subdir prefix (e.g. "jonah" or "05-jonah")
        book_dir = base_dir / args.book
        if not book_dir.exists():
            # Try searching for a directory containing the book name
            candidates = [d for d in base_dir.iterdir() if d.is_dir() and args.book in d.name]
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
            severity_tag = v["severity"]
            applied_action = "merge_with_next" if severity_tag == "STRONG-MERGE-CANDIDATE" else None
            findings.append({
                "file": str(v["file_path"].relative_to(REPO_ROOT)).replace("\\", "/"),
                "line": v["line_num"],
                "severity": "DEVIATION",
                "tag": severity_tag,
                "rule_id": "H7",
                "rule_short": "Complement Integrity",
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
            "validator": "validate_complement_integrity",
            "rule": "Layer 3 colometry — Rule H7",
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
    print(f"Rule H7 Complement Integrity validator — Tanakh {tier_label}")
    print(f"Reference: canon §5 H7 (cognition/volition/causative verb + כִּי-clause)")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Violations    : {len(all_violations)}")

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
        print("No violations found. Rule H7 complement integrity is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
