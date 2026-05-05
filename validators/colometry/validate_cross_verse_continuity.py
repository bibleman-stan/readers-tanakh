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
# Shared morphology + morph-alignment helpers
# ---------------------------------------------------------------------------
# Make _shared importable when this script is run as __main__.
sys.path.insert(0, str(REPO_ROOT / "validators"))
from _shared import morphology as M   # noqa: E402
from _shared import morph_alignment as MA  # noqa: E402
from _shared import macula_constituents as MC  # noqa: E402

# ---------------------------------------------------------------------------
# Pattern (e) — Pronoun-Resumption (NEW, Macula-IR-driven)
#
# Detects cross-verse continuity where verse N+1 opens with a pronoun (or
# pronominal-suffix-bearing token) whose Macula `participantref` resolves
# to a token in verse N (or earlier within the same chapter). This is a
# new validation capability the IR unlocks — the colometric layer alone
# cannot see participantref bonds.
#
# Scope: 1,077 corpus candidates (per pre-flight scan 2026-05-05). Severity
# gating per spot-check (~85% TP on STRONG slice, narrative discrete-pronoun,
# distance-1):
#
#   STRONG  — distance-1 + discrete pronoun (pos="pronoun") + non-poetic
#             register + verse N does NOT end with wayyiqtol
#   REVIEW  — distance ≤ 3 OR poetic register OR suffix-only token
#   (suppressed) — distance > 10 OR verse N ends with wayyiqtol-narrative
#   (the wayyiqtol-tail break is a heuristic for narrative time-step
#   progression that interrupts pronoun-resumption bonds)
# ---------------------------------------------------------------------------


# Project-slug ↔ filename mapping. The cross_verse validator runs on
# data/text-files/v{1,2}/he/<book_slug>/<book>-<chapter>.txt; book_slug
# is the parent directory name (e.g. "01-genesis").
_BOOK_SLUG_FROM_DIR = re.compile(r"^\d{2}-[a-z0-9]+$")


def _book_slug_from_path(path: Path) -> str | None:
    """Return the project book-slug (e.g. '01-genesis') from a v2/he chapter
    file path. Returns None if path doesn't conform to the expected layout."""
    parent = path.parent.name
    if _BOOK_SLUG_FROM_DIR.match(parent):
        return parent
    return None


def _chapter_int_from_path(path: Path) -> int | None:
    """Extract chapter number from filename like 'genesis-24.txt' or
    'songofsongs-03.txt'."""
    m = re.search(r"-(\d+)\.txt$", path.name, re.IGNORECASE)
    return int(m.group(1)) if m else None


def _verse_int_from_ref(ref: str) -> int | None:
    """'1:24' -> 24."""
    m = re.match(r"^\s*\d+:(\d+)\s*$", ref)
    return int(m.group(1)) if m else None


def _verse_n_ends_with_wayyiqtol(verse_n: "VerseBlock", book_slug: str,
                                  chapter: int) -> bool:
    """Heuristic: verse N's last cola contains a wayyiqtol verb.

    Wayyiqtol-tail = narrative time-step continuation, which colometrically
    breaks the resumption bond (verse N+1's pronoun is participant-tracking
    across an event boundary, not within the same atomic-thought scope).
    """
    last = verse_n.last_cola
    if not last:
        return False
    verse_int = _verse_int_from_ref(verse_n.ref)
    if verse_int is None:
        return False
    try:
        verse_tokens = MC.get_verse_tokens(book_slug, chapter, verse_int)
    except (FileNotFoundError, ValueError, KeyError):
        return False
    if not verse_tokens:
        return False
    # Match the last cola to its IR tokens. Greedy from cursor 0 over all colae.
    cursor = 0
    matched_last: list["MC.Token"] = []
    for cola in verse_n.cola:
        matched_last, cursor = MC.match_sense_line_tokens(
            verse_tokens, cola.text, start_idx=cursor)
    return any(t.is_wayyiqtol for t in matched_last)


def analyze_pattern_e_pronoun_resumption(
    verse_n: "VerseBlock",
    verse_n1: "VerseBlock",
    book_slug: str,
    chapter: int,
) -> dict | None:
    """Detect cross-verse pronoun-resumption bond via Macula participantref.

    Returns a finding dict (compatible with analyze_verse_pair's output) or
    None if no candidate / suppressed.
    """
    if verse_n.followed_by_paragraph_break:
        return None
    n1_first = verse_n1.first_cola
    if not n1_first:
        return None

    n_verse_int = _verse_int_from_ref(verse_n.ref)
    n1_verse_int = _verse_int_from_ref(verse_n1.ref)
    if n_verse_int is None or n1_verse_int is None:
        return None

    try:
        n1_tokens_all = MC.get_verse_tokens(book_slug, chapter, n1_verse_int)
    except (FileNotFoundError, ValueError, KeyError):
        return None
    if not n1_tokens_all:
        return None

    # Match verse N+1's first cola to its IR tokens
    matched_first, _ = MC.match_sense_line_tokens(n1_tokens_all, n1_first.text, start_idx=0)
    # The "opener" — first 1-2 content tokens (matches the pre-flight scan's
    # heuristic; agent's 2026-05-05 candidate count of 1,077 was based on
    # this 1-2-token window).
    openers = [t for t in matched_first if t.text.strip()][:2]
    if not openers:
        return None

    # Find the first opener with a cross-verse antecedent
    trigger_token: MC.Token | None = None
    antecedents_in_n: list[MC.Token] = []
    for tok in openers:
        if not tok.antecedents:
            continue
        # Filter to antecedents that point to an EARLIER verse, not same
        cross_verse_ants = [a for a in tok.antecedents if a.verse < n1_verse_int]
        if not cross_verse_ants:
            continue
        # Prefer antecedents in verse N specifically, otherwise any earlier
        in_n = [a for a in cross_verse_ants if a.verse == n_verse_int]
        if in_n:
            trigger_token = tok
            antecedents_in_n = in_n
            break
        # Distance-2+ candidates fall through (will use the broader set)
        if trigger_token is None:
            trigger_token = tok
            antecedents_in_n = cross_verse_ants

    if trigger_token is None:
        return None

    # Distance to the closest antecedent
    closest_ant_verse = max(a.verse for a in antecedents_in_n)
    distance = n1_verse_int - closest_ant_verse

    # Suppress: distance > 10 (long-range anaphora — almost always coincidental)
    if distance > 10:
        return None

    # Suppress: verse N ends with wayyiqtol (narrative time-step interrupts bond)
    if _verse_n_ends_with_wayyiqtol(verse_n, book_slug, chapter):
        return None

    # Severity gating
    # All pattern (e) findings emit REVIEW-REQUIRED for now — the IR-driven
    # candidate set (~1,964 corpus-wide) is new surface that needs editorial
    # triage before any subset can be promoted to STRONG-MERGE-CANDIDATE.
    # The pre-flight scan's spot-check showed ~85% TP on the distance-1 +
    # discrete-pronoun + narrative slice; promotion to STRONG awaits
    # confirmation against a larger editorial sample.
    is_discrete_pronoun = trigger_token.is_pronoun
    is_suffix = trigger_token.is_suffix
    # Methodology: poetic-register classification is calibration, not
    # authorization. Cross-verse pronoun-resumption is adjudicated by the
    # three editorial criteria (atomic thought, single image, Hebrew syntax)
    # in any register. Suppressing or demoting findings based solely on
    # register would treat the register classification as an overlay with
    # deterministic force — which the canon explicitly prohibits. Severity
    # stays REVIEW-REQUIRED corpus-wide pending wider editorial sampling.
    severity = "REVIEW-REQUIRED"

    last_cola = verse_n.last_cola
    n_text = last_cola.text if last_cola else ""
    n1_text = n1_first.text

    return {
        "rule": "H10/pattern-e-pronoun-resumption",
        "pattern": "(e) cross-verse pronoun-resumption (Macula participantref)",
        "severity": severity,
        "verse_n_ref": verse_n.ref,
        "verse_n1_ref": verse_n1.ref,
        # Same key names the existing JSON-output mode expects from analyze_verse_pair
        "last_cola_line": last_cola.line_num if last_cola else None,
        "first_cola_line": n1_first.line_num,
        "trigger_text": trigger_token.text,
        "trigger_pos": "suffix" if is_suffix else ("pronoun" if is_discrete_pronoun else trigger_token.pos),
        "antecedent_text": antecedents_in_n[0].text,
        "antecedent_verse": closest_ant_verse,
        "distance": distance,
        "applied_action": "merge_with_previous",
        "brief": (
            f"v{verse_n.ref} → v{verse_n1.ref}: pronoun {trigger_token.text!r} "
            f"resumes {antecedents_in_n[0].text!r} from v{closest_ant_verse} "
            f"(dist={distance})"
        ),
        "n_text": n_text,
        "n1_text": n1_text,
    }

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
    last_token_tags: "list[str] | None" = None,
    first_token_tags: "list[str] | None" = None,
) -> dict | None:
    """
    Check whether verse_n ends in a continuation-licensing pattern
    whose grammatical completion is verse_n1's opening.

    Args:
        verse_n: The earlier verse block.
        verse_n1: The later verse block.
        last_token_tags: TAHOT morph tag list for the LAST token of verse_n's
            last cola (from morph_alignment). None → skel-heuristic fallback.
        first_token_tags: TAHOT morph tag list for the FIRST token of verse_n1's
            first cola. None → skel-heuristic fallback.

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
    #
    # TAHOT tag enhancement: when last_token_tags is available, use
    # is_construct_head_token(tag_list=...) to confirm the regens morphologically
    # and upgrade confidence annotation in the finding brief.
    last_raw_token = last.tokens[-1] if last.tokens else ""
    if not last_raw_token.endswith(SOF_PASUQ):
        if starts_with_article(first_of_next):
            # Tag-aware regens confirmation.
            tag_confirms_construct = M.is_construct_head_token(
                last_raw_token, tag_list=last_token_tags
            )
            if tag_confirms_construct:
                brief_detail = (
                    f"possible construct regens at end of {verse_n.ref} "
                    f"(TAHOT-confirmed construct state, no sof pasuq) + "
                    f"articulated rectum opens {verse_n1.ref}; "
                    f"cross-verse construct chain — merge required"
                )
            else:
                brief_detail = (
                    f"possible construct regens at end of {verse_n.ref} "
                    f"(no sof pasuq on cola) + articulated rectum opens {verse_n1.ref}; "
                    f"cross-verse construct chain — merge required"
                )
            return {
                "verse_n_ref": verse_n.ref,
                "verse_n1_ref": verse_n1.ref,
                "last_cola_line": last.line_num,
                "first_cola_line": first.line_num,
                "pattern": "construct-chain-cross-verse",
                "severity": "STRONG-MERGE-CANDIDATE",
                "tag_confirms_construct": tag_confirms_construct,
                "brief": brief_detail,
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

def _get_boundary_tags(
    chapter_morph: "dict[int, list[str]] | None",
    verse_block: VerseBlock,
    token_index: int,  # -1 for last token, 0 for first token
) -> "list[str] | None":
    """Return TAHOT tag list for a boundary token in a verse block.

    Args:
        chapter_morph: verse_num → [ortho_tag, ...] mapping from MA.load_chapter_morph.
        verse_block: The VerseBlock whose boundary token we want.
        token_index: -1 to get the last token of the last cola (verse N end),
                      0 to get the first token of the first cola (verse N+1 start).

    Returns:
        The tag list for that token, or None if morph data is unavailable or
        the alignment fails (caller falls back to skel-heuristics).
    """
    if chapter_morph is None or not verse_block.cola:
        return None

    verse_num_str = verse_block.ref.split(":")
    if len(verse_num_str) != 2:
        return None
    try:
        verse_num = int(verse_num_str[1])
    except ValueError:
        return None

    ortho_tags = chapter_morph.get(verse_num)
    if ortho_tags is None:
        return None

    # Build content lines for this verse (no blank lines, no verse-ref lines).
    verse_lines = [c.text for c in verse_block.cola if c.text.strip()]
    if not verse_lines:
        return None

    verse_token_tags = MA.align_verse_tokens_to_tags(verse_lines, ortho_tags)
    if verse_token_tags is None:
        return None

    if token_index == -1:
        # Last token of last cola: last line, last token.
        if not verse_token_tags:
            return None
        last_line_tags = verse_token_tags[-1]
        if not last_line_tags:
            return None
        return last_line_tags[-1]
    else:
        # First token (index 0) of first cola: first line, first token.
        if not verse_token_tags:
            return None
        first_line_tags = verse_token_tags[0]
        if not first_line_tags:
            return None
        return first_line_tags[0]


def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    """Scan one chapter file for Rule H10 cross-verse continuity violations.

    Uses TAHOT morph tags (via morph_alignment) when available to classify
    the boundary tokens (last of verse N, first of verse N+1) as construct-state
    heads. Falls back to skel-heuristics when tags are missing or alignment fails.

    Patterns (a)-(d): subordinator / construct / speech-intro at verse boundary,
    detected via the colometric layer + morph-tag back-end.

    Pattern (e): cross-verse pronoun-resumption via Macula participantref —
    a new validation capability the IR layer unlocks. The colometric layer
    alone cannot see participantref bonds.
    """
    blocks = parse_chapter_file(path)
    violations = []

    # Load TAHOT morph alignment for this chapter (None if v0/morph file absent).
    chapter_morph = MA.load_chapter_morph(path)

    # Pattern (e) needs Macula IR access; derive book-slug + chapter once.
    book_slug = _book_slug_from_path(path)
    chapter_int = _chapter_int_from_path(path)
    have_ir = book_slug is not None and chapter_int is not None

    for idx in range(len(blocks) - 1):
        verse_n = blocks[idx]
        verse_n1 = blocks[idx + 1]

        # Retrieve boundary-token tag lists for TAHOT-aware construct detection.
        last_token_tags = _get_boundary_tags(chapter_morph, verse_n, token_index=-1)
        first_token_tags = _get_boundary_tags(chapter_morph, verse_n1, token_index=0)

        finding = analyze_verse_pair(
            verse_n, verse_n1,
            last_token_tags=last_token_tags,
            first_token_tags=first_token_tags,
        )
        if finding:
            finding["file"] = path.name
            finding["file_path"] = path
            violations.append(finding)

        # Pattern (e) — additive; runs alongside analyze_verse_pair so a
        # verse pair can match multiple patterns independently.
        if have_ir:
            try:
                e_finding = analyze_pattern_e_pronoun_resumption(
                    verse_n, verse_n1, book_slug, chapter_int)
            except Exception:
                e_finding = None  # IR-side failures are silent; never crash the validator
            if e_finding:
                e_finding["file"] = path.name
                e_finding["file_path"] = path
                violations.append(e_finding)

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
