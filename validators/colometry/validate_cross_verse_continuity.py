#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Rule H10 — Cross-Verse Continuity Merge.

Rule H10 (canon §5 H10; Layer 3 editorial rule):
When a single atomic thought crosses an MT verse boundary, the sense-line
stays intact in the EARLIER verse's block, with a superscript verse-number
marker preserving the versification reference.

  VIOLATION PATTERN: a verse ends with a token sequence whose grammatical
  completion is the next verse's opening. Detected cases:

    (a) Verse N ends with a SUBORDINATOR whose clause begins in verse N+1.
        Subordinators: אֲשֶׁר (relative/purposive), כִּי (causal/recitative),
        אִם (conditional), לְמַעַן (purposive), פֶּן (lest).
        — Severity: STRONG-MERGE-CANDIDATE when final token is bare
          subordinator; REVIEW-REQUIRED when subordinator is prefixed.

    (b) Verse N ends with a CONJUNCTION-PREFIX token (waw-prefix + single
        word, detached from the next clause).
        A lone וְ / וּ / וַ prefix token at verse-end is rare but possible
        in split-line editing. More common: a token ending in a waw-serial
        continuation that leaves its clause head in the next verse.
        — Severity: REVIEW-REQUIRED (rarely mechanical).

    (c) Verse N ends with a CONSTRUCT-STATE noun (nomen regens) whose
        nomen rectum is the opening token of verse N+1 — specifically:
        the definite-article heuristic from validate_construct_chain:
        final token looks like a construct (no sof pasuq on the COLA, and
        the first token of the next verse's first cola begins with הַ/הָ/הֶ).
        — Severity: STRONG-MERGE-CANDIDATE (matches the H2 cross-line
          construct heuristic applied across verse boundary).

    (d) Verse N's last cola ends with a speech-intro word (וַיֹּאמֶר etc.)
        WITHOUT לֵאמֹר on the same cola, and the next verse opens directly
        with speech content (not another speech-intro cola).
        — Severity: REVIEW-REQUIRED.

  EDGE CASES:
    - Petucha (פ) or setuma (ס) marker present between the two verses:
      these are Masoretic paragraph divisions — explicit author breaks.
      Do NOT fire across a פ/ס boundary.
    - Book boundaries: never compare last verse of one book to first of
      another (impossible within a single chapter file; each file is one
      chapter of one book).
    - A verse that ends with sof pasuq (׃) followed immediately by a
      verse-reference line and then a new verse whose first cola is
      syntactically independent: no firing.

Detection algorithm (per chapter file):
  1. Parse the file into verse blocks: each block starts with a verse-ref
     line (e.g. "1:2") and contains zero or more cola lines, ending with
     the last cola bearing sof pasuq (׃).
  2. For each consecutive verse pair (N, N+1), check whether a
     petucha/setuma separator is present between them (inline in v0 text
     or as a blank-line indicator in v1/v2). If so, skip.
  3. Examine the last cola of verse N:
       - Strip niqqud/te'amim from each token.
       - Check bare final token(s) against pattern sets (a)–(d).
  4. Examine the first cola of verse N+1 for confirmation heuristics.
  5. Emit finding with appropriate severity and applied_action.

Output format:
    [DEVIATION]  file:line_number  H10/cross-verse  SEVERITY  brief description

Where SEVERITY is one of:
    STRONG-MERGE-CANDIDATE   — high-confidence cross-verse continuity
    REVIEW-REQUIRED          — ambiguous; editorial judgment required

Exit code: 0 if zero violations, 1 if violations found, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_cross_verse_continuity.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_cross_verse_continuity.py --book jonah
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_cross_verse_continuity.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_cross_verse_continuity.py --verbose
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_cross_verse_continuity.py --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "he"

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers
# ---------------------------------------------------------------------------

# Maqqef glyph (U+05BE)
MAQQEF = "־"  # ־

# Hebrew points range (U+0591–U+05C7): cantillation + niqqud
HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")

# Sof pasuq (U+05C3) — verse-end marker
SOF_PASUQ = "׃"  # ׃

# Paseq (U+05C0) — used in some disambiguation contexts; not a verse-end
PASEQ = "׀"  # ׀


def strip_points(token: str) -> str:
    """Return token with all niqqud and te'amim stripped (bare consonants + matres)."""
    return HEBREW_POINTS_RE.sub("", token)


def bare_consonants(token: str) -> str:
    """Return bare consonants: strip points AND maqqef."""
    return strip_points(token).replace(MAQQEF, "")


# ---------------------------------------------------------------------------
# Verse-reference line detection
# ---------------------------------------------------------------------------

VERSE_REF_RE = re.compile(r"^\s*\d+:\d+\s*$")


def is_verse_ref(line: str) -> bool:
    """Return True if line is a bare verse-reference (e.g. '1:2')."""
    return bool(VERSE_REF_RE.match(line))


def is_blank(line: str) -> bool:
    return not line.strip()


# ---------------------------------------------------------------------------
# Petucha / Setuma detection
#
# In v0 prose files the markers appear inline: " פ " or " ס " within a line.
# In v1/v2 colometric files they appear as standalone lines or inline tokens.
# We check both formats.
# ---------------------------------------------------------------------------

PETUCHA_BARE = "פ"   # peh — open paragraph
SETUMA_BARE = "ס"    # samekh — closed paragraph

# Inline in v0: "... פ ..." or at end of a verse-content line
PARAGRAPH_MARKER_RE = re.compile(r"\bפ\b|\bס\b")


def line_has_paragraph_marker(line: str) -> bool:
    """Return True if line contains a petucha (פ) or setuma (ס) marker."""
    # Strip points first, then check for standalone peh or samekh
    bare = strip_points(line)
    return bool(PARAGRAPH_MARKER_RE.search(bare))


def is_standalone_paragraph_marker(line: str) -> bool:
    """Return True if the line IS the paragraph marker (standalone פ or ס line)."""
    s = strip_points(line).strip()
    return s in (PETUCHA_BARE, SETUMA_BARE)


# ---------------------------------------------------------------------------
# Continuation-licensing patterns
# (bare consonant skeletons after strip_points + maqqef removal)
# ---------------------------------------------------------------------------

# (a) Subordinators: tokens whose bare form is one of these, at the end of the
#     last cola of a verse, strongly signal cross-verse continuation.
SUBORDINATOR_SKELETONS_STRONG = {
    "אשר",    # אֲשֶׁר — relative / purposive
    "כי",     # כִּי  — causal / recitative / conditional
    "אם",     # אִם  — conditional / oath
    "למען",   # לְמַעַן — purposive
    "פן",     # פֶּן — lest / negative purpose
    "אחרי",   # אַחֲרֵי — after (temporal)
    "בטרם",   # בְּטֶרֶם — before (temporal, takes clause)
    "עד",     # עַד — until (takes clause with אֲשֶׁר or bare)
    "בעבור",  # בַּעֲבוּר — for the sake of / in order that
}

# Subordinators with prefix — lower confidence (often discourse markers)
SUBORDINATOR_SKELETONS_REVIEW = {
    "כיאשר",  # כַּאֲשֶׁר — as/when
    "כאשר",   # כַּאֲשֶׁר (alternate normalization)
    "מאשר",   # מֵאֲשֶׁר — from which
    "באשר",   # בַּאֲשֶׁר — inasmuch as
}

# (b) Speech-intro verbs (bare consonant skeletons) without לאמר —
#     when at end of verse, the next verse may open with speech content.
SPEECH_INTRO_SKELETONS = {
    "ויאמר",   # wayyiqtol qal 3ms — and he said
    "ויאמרו",  # wayyiqtol qal 3mp — and they said
    "וידבר",   # wayyiqtol piel 3ms — and he spoke
    "ותאמר",   # wayyiqtol qal 3fs — and she said
    "ויען",    # wayyiqtol qal 3ms — and he answered
    "ויענו",   # wayyiqtol qal 3mp — and they answered
    "ויצו",    # wayyiqtol piel 3ms — and he commanded
    "ויקרא",   # wayyiqtol qal 3ms — and he called (can introduce speech)
}

# לאמר (the speech-onset complementizer): if present on the verse-end cola,
# the next verse almost certainly opens with the speech content.
LEEMOR_SKELETON = "לאמר"

# (c) Definite article prefixes (bare) for construct-chain heuristic
DEFINITE_ARTICLE_PREFIXES = ("ה", "ה")  # הַ / הָ / הֶ — all bare to ה


def starts_with_article(bare_token: str) -> bool:
    """Return True if bare_token starts with definite article prefix ה."""
    if not bare_token:
        return False
    return bare_token.startswith("ה") and len(bare_token) > 1


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class Cola:
    """One line of colometric text in a chapter file."""
    def __init__(self, text: str, line_num: int):
        self.text = text.rstrip()
        self.line_num = line_num  # 1-based

    @property
    def tokens(self) -> list:
        return self.text.split()

    @property
    def bare_tokens(self) -> list:
        return [strip_points(t) for t in self.tokens]

    @property
    def bare_consonant_tokens(self) -> list:
        return [bare_consonants(t) for t in self.tokens]

    @property
    def ends_with_sof_pasuq(self) -> bool:
        """Return True if the cola's last non-empty token ends with ׃."""
        t = self.text.rstrip()
        return t.endswith(SOF_PASUQ) or t.endswith(SOF_PASUQ + PASEQ)

    @property
    def has_paragraph_marker(self) -> bool:
        return line_has_paragraph_marker(self.text)

    def __repr__(self):
        return f"Cola(line={self.line_num}, text={self.text[:60]!r})"


class VerseBlock:
    """One verse: a ref line + its cola lines."""
    def __init__(self, ref: str, ref_line_num: int):
        self.ref = ref.strip()          # e.g. "1:2"
        self.ref_line_num = ref_line_num
        self.cola: list[Cola] = []
        # True if a paragraph marker (פ/ס) appears anywhere in or between this verse
        # and the next (detected post-parsing from raw lines between verse refs)
        self.followed_by_paragraph_break: bool = False

    @property
    def last_cola(self) -> Cola | None:
        return self.cola[-1] if self.cola else None

    @property
    def first_cola(self) -> Cola | None:
        return self.cola[0] if self.cola else None

    def __repr__(self):
        return f"VerseBlock(ref={self.ref}, cola_count={len(self.cola)})"


# ---------------------------------------------------------------------------
# File parser
# ---------------------------------------------------------------------------

def parse_chapter_file(path: Path) -> list[VerseBlock]:
    """Parse a chapter file into VerseBlock objects."""
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw = path.read_text(encoding="utf-8-sig")

    lines = raw.splitlines()
    blocks: list[VerseBlock] = []
    current: VerseBlock | None = None

    for i, line in enumerate(lines):
        line_num = i + 1  # 1-based

        if is_verse_ref(line):
            current = VerseBlock(line.strip(), line_num)
            blocks.append(current)
            continue

        if current is None:
            # Pre-verse-ref content (shouldn't exist but be safe)
            continue

        if is_blank(line):
            # Blank lines between verses are just spacing; skip.
            continue

        # Non-blank, non-verse-ref: it's a cola (or paragraph marker line)
        cola = Cola(line, line_num)
        current.cola.append(cola)

    # Second pass: detect paragraph breaks BETWEEN verse blocks.
    # We look at the raw lines between consecutive verse-ref lines.
    # A paragraph break between verse N and verse N+1 means we should NOT flag.
    for idx in range(len(blocks) - 1):
        block_a = blocks[idx]
        block_b = blocks[idx + 1]
        # Collect raw lines between the end of block_a's last cola and the
        # start of block_b's ref line.
        start_line = block_a.ref_line_num  # 0-based index = ref_line_num - 1
        end_line = block_b.ref_line_num    # 0-based index = ref_line_num - 1

        # Raw text between the two verse-ref lines:
        between = lines[start_line:end_line - 1]  # excludes the ref line itself

        has_break = any(line_has_paragraph_marker(ln) for ln in between)
        block_a.followed_by_paragraph_break = has_break

    return blocks


# ---------------------------------------------------------------------------
# Cross-verse analysis
# ---------------------------------------------------------------------------

def analyze_verse_pair(
    verse_n: VerseBlock,
    verse_n1: VerseBlock,
) -> dict | None:
    """
    Check whether verse_n ends in a continuation-licensing pattern
    whose grammatical completion is verse_n1's opening.

    Returns a finding dict if a violation is detected, else None.
    """
    # Guard: paragraph break between verses — skip.
    if verse_n.followed_by_paragraph_break:
        return None

    last = verse_n.last_cola
    first = verse_n1.first_cola

    if last is None or first is None:
        return None

    bare_last = last.bare_consonant_tokens
    bare_first = first.bare_consonant_tokens

    if not bare_last or not bare_first:
        return None

    final_token = bare_last[-1]
    second_final = bare_last[-2] if len(bare_last) >= 2 else ""
    first_of_next = bare_first[0]

    # -----------------------------------------------------------------------
    # Pattern (a-1): Last token is לאמר — next verse opens with speech content.
    # This is the cross-verse לאמר case: the speech-intro complementizer sits
    # at the end of the verse, the speech itself starts in the next verse.
    # High confidence.
    # -----------------------------------------------------------------------
    if final_token == LEEMOR_SKELETON:
        # לאמר at verse end is a STRONG signal if the next verse opens with
        # non-speech-intro content (speech content, not another framing clause).
        first_of_next_is_speech_verb = (first_of_next in SPEECH_INTRO_SKELETONS)
        severity = "REVIEW-REQUIRED" if first_of_next_is_speech_verb else "STRONG-MERGE-CANDIDATE"
        return {
            "verse_n_ref": verse_n.ref,
            "verse_n1_ref": verse_n1.ref,
            "last_cola_line": last.line_num,
            "first_cola_line": first.line_num,
            "pattern": "leemor-cross-verse",
            "severity": severity,
            "brief": (
                f"לֵאמֹר at end of {verse_n.ref} — "
                f"speech content opens {verse_n1.ref}; "
                f"cross-verse לֵאמֹר merge required"
            ),
            "last_cola_text": last.text,
            "first_cola_text": first.text,
        }

    # -----------------------------------------------------------------------
    # Pattern (a-2): Last token is a STRONG subordinator.
    # The subordinating clause begins in the next verse.
    # -----------------------------------------------------------------------
    if final_token in SUBORDINATOR_SKELETONS_STRONG:
        return {
            "verse_n_ref": verse_n.ref,
            "verse_n1_ref": verse_n1.ref,
            "last_cola_line": last.line_num,
            "first_cola_line": first.line_num,
            "pattern": "subordinator-cross-verse",
            "severity": "STRONG-MERGE-CANDIDATE",
            "brief": (
                f"subordinator '{last.tokens[-1]}' at end of {verse_n.ref} "
                f"— subordinate clause begins {verse_n1.ref}; merge required"
            ),
            "last_cola_text": last.text,
            "first_cola_text": first.text,
        }

    # -----------------------------------------------------------------------
    # Pattern (a-3): Last token is a REVIEW subordinator.
    # -----------------------------------------------------------------------
    if final_token in SUBORDINATOR_SKELETONS_REVIEW:
        return {
            "verse_n_ref": verse_n.ref,
            "verse_n1_ref": verse_n1.ref,
            "last_cola_line": last.line_num,
            "first_cola_line": first.line_num,
            "pattern": "subordinator-cross-verse-review",
            "severity": "REVIEW-REQUIRED",
            "brief": (
                f"possible subordinator '{last.tokens[-1]}' at end of {verse_n.ref} "
                f"— may be discourse particle; check whether clause begins {verse_n1.ref}"
            ),
            "last_cola_text": last.text,
            "first_cola_text": first.text,
        }

    # -----------------------------------------------------------------------
    # Pattern (c): Construct-chain cross-verse (definite-article heuristic).
    # Last token of verse N has no sof pasuq (i.e., verse ends mid-construct),
    # and the first token of verse N+1 begins with the definite article.
    # -----------------------------------------------------------------------
    # NOTE: In well-formed colometric text the verse's LAST cola always ends
    # in sof pasuq at the MT level (the MT boundary is always ׃). If the
    # cola's last token does NOT carry ׃ AND the next verse starts with an
    # articulated noun, we have a cross-verse construct chain split.
    last_raw_token = last.tokens[-1] if last.tokens else ""
    if not last_raw_token.endswith(SOF_PASUQ):
        if starts_with_article(first_of_next):
            return {
                "verse_n_ref": verse_n.ref,
                "verse_n1_ref": verse_n1.ref,
                "last_cola_line": last.line_num,
                "first_cola_line": first.line_num,
                "pattern": "construct-chain-cross-verse",
                "severity": "STRONG-MERGE-CANDIDATE",
                "brief": (
                    f"possible construct regens at end of {verse_n.ref} "
                    f"(no sof pasuq on cola) + articulated rectum opens {verse_n1.ref}; "
                    f"cross-verse construct chain — merge required"
                ),
                "last_cola_text": last.text,
                "first_cola_text": first.text,
            }

    # -----------------------------------------------------------------------
    # Pattern (d): Speech-intro verb at verse end WITHOUT לאמר.
    # The next verse probably opens with the speech content.
    # -----------------------------------------------------------------------
    if final_token in SPEECH_INTRO_SKELETONS:
        # Confirm: next verse's first cola does NOT itself begin with a speech
        # verb (that would be sequential framing, not cross-verse continuation).
        next_starts_with_speech = (first_of_next in SPEECH_INTRO_SKELETONS)
        if not next_starts_with_speech:
            return {
                "verse_n_ref": verse_n.ref,
                "verse_n1_ref": verse_n1.ref,
                "last_cola_line": last.line_num,
                "first_cola_line": first.line_num,
                "pattern": "speech-intro-cross-verse",
                "severity": "REVIEW-REQUIRED",
                "brief": (
                    f"speech-intro verb '{last.tokens[-1]}' at end of {verse_n.ref} "
                    f"without לֵאמֹר — check if speech opens {verse_n1.ref}"
                ),
                "last_cola_text": last.text,
                "first_cola_text": first.text,
            }

    # -----------------------------------------------------------------------
    # Pattern (b): Waw-prefix conjunction token that is the entire last cola.
    # This is extremely rare but worth catching: a cola consisting of ONLY
    # a waw-prefix word (וְ/וַ/וּ + single word) ending the verse, whose
    # referent clause is in the next verse.
    # Detection: last cola has exactly one token, that token starts with waw
    # after stripping points, and the token is not itself a complete clause.
    # We use a length heuristic: a one-token cola is rarely a complete thought.
    # -----------------------------------------------------------------------
    if len(last.tokens) == 1 and len(last.cola if hasattr(last, "cola") else []) == 0:
        # Just the single-token cola check
        ft = bare_last[0] if bare_last else ""
        if ft.startswith("ו") and len(ft) > 1 and not last_raw_token.endswith(SOF_PASUQ):
            return {
                "verse_n_ref": verse_n.ref,
                "verse_n1_ref": verse_n1.ref,
                "last_cola_line": last.line_num,
                "first_cola_line": first.line_num,
                "pattern": "waw-prefix-cross-verse",
                "severity": "REVIEW-REQUIRED",
                "brief": (
                    f"single waw-prefix token '{last.tokens[0]}' is entire last cola "
                    f"of {verse_n.ref} without sof pasuq — may continue into {verse_n1.ref}"
                ),
                "last_cola_text": last.text,
                "first_cola_text": first.text,
            }

    return None


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    """Scan one chapter file for Rule H10 cross-verse continuity violations."""
    blocks = parse_chapter_file(path)
    violations = []

    for idx in range(len(blocks) - 1):
        verse_n = blocks[idx]
        verse_n1 = blocks[idx + 1]

        finding = analyze_verse_pair(verse_n, verse_n1)
        if finding:
            finding["file"] = path.name
            finding["file_path"] = path
            violations.append(finding)

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
        help="Scan v2/he (colometry-pass tier) instead of v1/he-baseline.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show last/first cola text for each violation.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as a single JSON document to STDOUT.",
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
        # Support both "jonah" (no prefix) and "05-jonah" style
        book_dir = base_dir / args.book
        if not book_dir.exists():
            # Try with numeric prefix scan
            candidates = [d for d in base_dir.iterdir()
                          if d.is_dir() and d.name.endswith(args.book)]
            if candidates:
                book_dir = candidates[0]
            else:
                print(f"ERROR: book directory not found: {base_dir / args.book}", file=sys.stderr)
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
            # Cross-verse merges always produce "merge_with_next" action when STRONG
            applied_action = "merge_with_next" if severity == "STRONG-MERGE-CANDIDATE" else None

            findings.append({
                "file": str(v["file_path"].relative_to(REPO_ROOT)).replace("\\", "/"),
                "line": v["last_cola_line"],
                "severity": "DEVIATION",
                "tag": severity,
                "rule_id": "H10.1",
                "rule_short": "cross-verse continuity merge",
                "brief": v["brief"],
                "pattern": v["pattern"],
                "verse_n": v["verse_n_ref"],
                "verse_n1": v["verse_n1_ref"],
                "next_line": v["first_cola_line"],
                "applied_action": applied_action,
            })

        by_severity_json: dict[str, int] = {}
        by_tag: dict[str, int] = {}
        by_pattern: dict[str, int] = {}
        for f in findings:
            by_severity_json[f["severity"]] = by_severity_json.get(f["severity"], 0) + 1
            by_tag[f["tag"]] = by_tag.get(f["tag"], 0) + 1
            by_pattern[f["pattern"]] = by_pattern.get(f["pattern"], 0) + 1

        doc = {
            "validator": "validate_cross_verse_continuity",
            "rule": "Rule H10 — Cross-Verse Continuity Merge",
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
                "by_pattern": by_pattern,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output (default) ---
    print("=" * 72)
    print(f"Rule H10 Cross-Verse Continuity validator — Tanakh {tier_label}")
    print(f"Reference: canon §5 H10 (cross-verse atomic-thought merge)")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Violations    : {len(all_violations)}")

    # Severity summary
    by_severity: dict[str, int] = {}
    by_pattern_counts: dict[str, int] = {}
    for v in all_violations:
        by_severity[v["severity"]] = by_severity.get(v["severity"], 0) + 1
        by_pattern_counts[v["pattern"]] = by_pattern_counts.get(v["pattern"], 0) + 1
    if by_severity:
        print()
        for sev, count in sorted(by_severity.items()):
            print(f"  {sev}: {count}")
        print()
        for pat, count in sorted(by_pattern_counts.items()):
            print(f"  pattern={pat}: {count}")
    print()

    if all_violations:
        for v in all_violations:
            print(
                f"[DEVIATION]  {v['file']}:{v['last_cola_line']}  "
                f"H10/cross-verse  {v['severity']}  {v['brief']}"
            )
            print(f"    verse {v['verse_n_ref']} last cola:  {v['last_cola_text'][:100]}")
            if args.verbose:
                print(f"    verse {v['verse_n1_ref']} first cola: {v['first_cola_text'][:100]}")
            print()
    else:
        print("No violations found. Rule H10 cross-verse continuity is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
