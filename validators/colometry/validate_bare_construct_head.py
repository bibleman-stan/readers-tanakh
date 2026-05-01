#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Rule M3 — Bare-Governor Indivisibility: Construct-Chain Case.

Rule M3 (canon §1; Layer 3 editorial rule):
A bare construct-state noun (regens) standing alone on a line without its
rectum (genitive object) violates the atomic-thought test — the bare head is
grammatical machinery awaiting content, not a complete predication. The regens
and rectum must merge onto the same line.

This validator surfaces construct-chain splits (regens on line N, rectum on
line N+1) as STRONG-MERGE-CANDIDATE findings for M3.

ARCHITECTURAL CONSTRAINT — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. The te'amim
Unicode range (U+0591–U+05AF) does NOT appear in any predicate that decides
whether to fire a finding. Te'amim MAY appear in finding annotations as
informational defensibility-capture.

SEVERITY:
All findings emit at severity STRONG-MERGE-CANDIDATE. M3 is a closed-list
merge-override rule codified in the canon; violations are categorically
destructive to the atomic-thought test.

FORCED-NO-MERGE GUARDS (skip BEFORE emitting):
  1. Poetic register — is_poetic_register(book, chapter, verse) → skip.
  2. Intervening modifier — relative clause or PP modifies the construct head
     itself (not the final rectum), keeping the regens with its modifier.
  3. Maqqef-binding — the chain is internally maqqef-joined (already one
     prosodic unit orthographically).
  4. Already-long chain — construct chain ≥3 levels deep with substantial
     final rectum modifier (evaluated under structural justification 5).

Pattern:
Line N ends with a bare construct-state noun from a small closed list of
frequent construct heads (דבר, בית, בן, בת, אלהי, אדני, יהוה, מלך, רוח, יד,
פני, אנשי, נשי, זרע, ימי, שני). Line N+1 begins with a noun (no preposition
in front, no verb) that completes the chain.

Output format:
    [DEVIATION]  file:line  M3/bare-construct-head  STRONG-MERGE-CANDIDATE  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_bare_construct_head.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_bare_construct_head.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_bare_construct_head.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_bare_construct_head.py --json
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
from _shared import morphology as M  # noqa: E402
from _shared import morph_alignment as MA  # noqa: E402

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers
# ---------------------------------------------------------------------------

# Hebrew points (cantillation U+0591–U+05AF + niqqud U+05B0–U+05BC, U+05C1–U+05C2,
# U+05C4–U+05C5, U+05C7).
# This regex strips te'amim + niqqud while PRESERVING maqqef (U+05BE), paseq (U+05C0),
# and sof pasuq (U+05C3).
HEBREW_POINTS_RE = re.compile(r"[֑-ֽֿׁ-ׂׄ-ׇׅ]")  # Preserve maqqef U+05BE, paseq U+05C0, sof pasuq U+05C3

# Niqqud-only regex (no te'amim)
TEAMIM_ONLY_RE = re.compile(r"[֑-֯]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"  # ׃
# Maqqef (orthographic word-joiner)
MAQQEF = "־"     # ־
# Paseq (vertical bar disjunction)
PASEQ = "׀"      # ׀

# Niqqud individual marks
HOLAM = "ֹ"        # ֹ  — holam
SHEVA = "ְ"        # ְ  — shewa
PATAH = "ַ"        # ַ  — patah
QAMATS = "ָ"       # ָ  — qamats
HIRIQ = "ִ"        # ִ  — hiriq
QUBUTS = "ֻ"       # ֻ  — qubuts
TSERE = "ֵ"        # ֵ  — tsere
SEGOL = "ֶ"        # ֶ  — segol
DAGESH = "ּ"       # ּ  — dagesh

# Hebrew consonants
BET = "ב"
KAF = "כ"
LAMED = "ל"
MEM = "מ"


def strip_points(token: str) -> str:
    """Return token with niqqud and te'amim stripped (consonant skeleton)."""
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


def prosodic_word_count(line: str) -> int:
    """Count prosodic words (whitespace-delimited tokens)."""
    return len(content_tokens(line))


# ---------------------------------------------------------------------------
# Construct-state detection
# ---------------------------------------------------------------------------

# Closed list of high-frequency construct-state heads. These are consonant
# skeletons. The construct form is marked by:
#   - Loss of final vowel or shortening (דְּבַר → דִּבְרֵי, בַּיִת → בְנֵי)
#   - In bound form, often vowel contraction (בְנֵי, not בָּנִים)
#   - Bound forms with reduced vowels (shewa, segol, tsere under construct)
#
# Strategy: we list the construct skeleton forms that appear BOUND (often
# with maqqef or at line-end directly attached to the next word). For now,
# we use the bare consonant skeleton since construct-form vowel patterns
# are multiple and variable.
#
# Some common heads and their construct forms:
#   דָּבָר (word) → דְּבַר, דִּבְרֵי (construct) — bare: דבר
#   בַּיִת (house) → בֵּית (construct) — bare: בית
#   בֵּן (son) → בְנֵי (construct) — bare: בן
#   בַּת (daughter) → בְנַת (construct) — bare: בת
#   מִלֶּךְ (king) → מַלְךְ (construct) — bare: מלך
#   רוּחַ (spirit) → רוּחַ (construct) — bare: רוח
#   יָד (hand) → יַד (construct) — bare: יד
#   פָּנִים (face) → פְנֵי (construct) — bare: פני
#
# We match the bare skeleton after stripping points, looking for candidates
# whose next word (line N+1) is a noun with no leading preposition.

CONSTRUCT_HEAD_SKELETONS = {
    # Very common construct heads in narrative
    "דבר",     # word, matter
    "בית",     # house
    "בן",      # son
    "בת",      # daughter
    "אדני",    # Lord (construct of אדון)
    "יהוה",    # YHWH (construct form same, but appears as bound head)
    "מלך",     # king
    "רוח",     # spirit
    "יד",      # hand
    "פני",     # face
    "אנשי",    # men (construct, "men of")
    "נשי",     # women (construct, "women of")
    "זרע",     # seed
    "ימי",     # days (construct, "days of")
    "שני",     # year (construct, "year of")
    "אלהי",    # God (construct, "God of")
    "עם",      # people (construct)
    "קול",     # voice (construct)
    "כל",      # all (construct)
    "דרך",     # way (construct)
    "עיר",     # city (construct)
}


def last_token_is_construct_head(line: str) -> tuple[bool, str | None]:
    """Check if the last content token on `line` is a construct-head skeleton.

    Returns (True, skeleton) if yes, (False, None) if no.
    """
    last = last_content_token(line)
    if not last:
        return False, None
    bare = strip_points(last).rstrip(SOF_PASUQ)
    if not bare:
        return False, None
    # Strip maqqef if present (bare constructs often end with maqqef)
    if bare.endswith(MAQQEF):
        bare = bare.rstrip(MAQQEF)
    if bare in CONSTRUCT_HEAD_SKELETONS:
        return True, bare
    return False, None


# ---------------------------------------------------------------------------
# Preposition detection — next line must NOT start with preposition
# ---------------------------------------------------------------------------

STANDALONE_PREPS = {
    "על", "אל", "מן", "עם", "תחת", "בין",
    "לפני", "אחרי", "מאחרי", "מלפני", "מפני", "מאת",
    "בעד", "נגד", "מעל", "מתחת", "בתוך", "מתוך",
}

BOUND_PREP_INITIAL = {BET, LAMED, KAF, MEM}


def starts_with_preposition(line: str) -> tuple[bool, str | None]:
    """Check if the first content token begins with a preposition."""
    first = first_content_token(line)
    if not first:
        return False, None
    bare = strip_points(first)
    if not bare:
        return False, None

    # Maqqef-compound prepositions
    if MAQQEF in bare:
        head = bare.split(MAQQEF, 1)[0]
        if head in STANDALONE_PREPS:
            return True, head

    # Standalone prepositions
    if bare in STANDALONE_PREPS:
        return True, bare

    # Bound prefix prepositions (ב/ל/כ/מ + noun)
    if len(bare) >= 3 and bare[0] in BOUND_PREP_INITIAL:
        if bare in ("לא", "לכן"):
            return False, None
        teamim_stripped = strip_teamim_only(first)
        if len(teamim_stripped) >= 2:
            second_char = teamim_stripped[1]
            if second_char in (SHEVA, PATAH, SEGOL, HIRIQ):
                return True, bare[0]

    if len(bare) >= 3 and bare[0] == MEM:
        teamim_stripped = strip_teamim_only(first)
        if len(teamim_stripped) >= 3 and teamim_stripped[1] == HIRIQ:
            return True, "מ"

    return False, None


# ---------------------------------------------------------------------------
# Verb detection — next line must NOT start with a verb
# ---------------------------------------------------------------------------

WAYYIQTOL_PREFIXES = ("וי", "ות", "ונ", "וא")

KNOWN_FINITE_VERB_SKELETONS = {
    "אמר", "אמרה", "אמרו", "אמרתי", "אמרת", "אמרנו", "אמרתם",
    "ראה", "ראתה", "ראו", "ראיתי", "ראית", "ראינו",
    "שמע", "שמעה", "שמעו", "שמעתי", "שמענו",
    "ידע", "ידעה", "ידעו", "ידעתי", "ידעת", "ידענו",
    "ברא", "בראה", "בראו",
    "ברך", "ברכה", "ברכו", "ברכתי", "ברכת",
    "הלך", "הלכה", "הלכו", "הלכתי", "הלכנו",
    "נתן", "נתנה", "נתנו", "נתתי", "נתת",
    "עשה", "עשתה", "עשו", "עשיתי", "עשית", "עשינו",
    "היה", "היתה", "היו", "הייתי", "היית", "היינו",
    "בא", "באה", "באו", "באתי", "באת", "באנו",
    "קם", "קמה", "קמו", "קמתי", "קמנו",
    "בנה", "בנתה", "בנו", "בניתי",
    "לקח", "לקחה", "לקחו", "לקחתי",
    "כתב", "כתבה", "כתבו", "כתבתי",
    "כרת", "כרתה", "כרתו",
    "מצא", "מצאה", "מצאו", "מצאתי",
    "נשא", "נשאה", "נשאו", "נשאתי",
    "נפל", "נפלה", "נפלו", "נפלתי",
    "ישב", "ישבה", "ישבו", "ישבתי",
    "עבר", "עברה", "עברו",
    "אכל", "אכלה", "אכלו", "אכלתי",
    "שתה", "שתתה", "שתו",
    "מת", "מתה", "מתו", "מתי",
    "חיה", "חיתה", "חיו",
    "סר", "סרה", "סרו",
    "עלה", "עלתה", "עלו", "עליתי",
    "ירד", "ירדה", "ירדו",
    "שב", "שבה", "שבו", "שבתי",
    "הכה", "הכתה", "הכו",
    "הביא", "הביאה", "הביאו",
    "הוציא", "הוציאה", "הוציאו",
    "הגיד", "הגידה", "הגידו",
    "הציל", "הצילה", "הצילו",
    "צוה", "צותה", "צוו",
    "דבר", "דברה", "דברו",
    "פנה", "פנתה", "פנו",
    "נסע", "נסעה", "נסעו",
    "יאמר", "תאמר", "יאמרו", "תאמרו", "נאמר",
    "ישמע", "תשמע", "ישמעו",
    "יראה", "תראה", "יראו",
    "יבא", "תבא", "יבאו", "יקם",
    "יעשה", "תעשה", "יעשו",
    "ילך", "תלך", "ילכו",
    "יתן", "תתן", "יתנו", "אתן",
    "יקח", "תקח", "יקחו",
    "ישב", "תשב", "ישבו",
    "ידע", "תדע", "ידעו",
    "יזכר", "תזכר", "יזכרו",
    "שמעו", "ראו", "לכו", "קומו", "עשו",
    "לך", "קום", "בא", "קח", "תן",
}


def looks_like_finite_verb(bare: str) -> bool:
    """Heuristic: does this bare skeleton look like a finite verb?"""
    if not bare:
        return False
    if bare in KNOWN_FINITE_VERB_SKELETONS:
        return True
    if bare.startswith(WAYYIQTOL_PREFIXES):
        if len(bare) >= 4 and bare not in ("ויהוה",):
            return True
    if MAQQEF in bare:
        for part in bare.split(MAQQEF):
            if not part:
                continue
            if part in KNOWN_FINITE_VERB_SKELETONS:
                return True
            if part.startswith(WAYYIQTOL_PREFIXES) and len(part) >= 4:
                return True
    for suf in ("תי", "תם", "תן", "נו"):
        if bare.endswith(suf) and len(bare) >= 4:
            return True
    return False


def first_token_looks_like_verb(line: str) -> bool:
    """Check if the first content token looks like a verb."""
    first = first_content_token(line)
    if not first:
        return False
    bare = strip_points(first)
    return looks_like_finite_verb(bare)


def line_has_finite_verb(line: str) -> bool:
    """True if any content token on `line` looks like a finite verb."""
    for tok in content_tokens(line):
        bare = strip_points(tok)
        if looks_like_finite_verb(bare):
            return True
    return False


# ---------------------------------------------------------------------------
# Relative clause and PP modifier detection
# ---------------------------------------------------------------------------

RELATIVE_SKELETONS = {"אשר"}


def line_has_relative_clause_or_modifier_pp(line: str) -> bool:
    """Check if `line` has a relative clause (אֲשֶׁר) or PP that might be
    modifying the construct head itself (not the rectum).

    This is a heuristic guard: if the construct head is modified directly
    on its own line, it is not "bare" in the sense of awaiting only the
    rectum, so the guard fires and we skip the finding.
    """
    toks = content_tokens(line)
    bares = [strip_points(t) for t in toks]
    # If אֲשֶׁר appears anywhere, it signals a relative clause modifying the
    # preceding noun. If that noun is our construct head, the head is not bare.
    for b in bares:
        if b in RELATIVE_SKELETONS:
            return True
    # A simple PP on the same line as the construct head (e.g. בֵּית בַּמִּדְבָּר)
    # would also keep the head "bound" to its modifier. Check for a prep token.
    has_prep, _ = starts_with_preposition(line)
    if has_prep:
        return True
    return False


# ---------------------------------------------------------------------------
# Maqqef detection
# ---------------------------------------------------------------------------

def construct_head_maqqef_bound(line: str) -> bool:
    """Check if the last token (the construct head) is maqqef-joined to
    another word (internally compound via maqqef).

    Example: דִּבְרֵי־יְהוָה on the same line is maqqef-bound.
    """
    last = last_content_token(line)
    if not last:
        return False
    bare = strip_points(last)
    return MAQQEF in bare


# ---------------------------------------------------------------------------
# Verse partitioning
# ---------------------------------------------------------------------------

def partition_into_verses(lines: list[str]) -> list[tuple[int | None, int | None, list[int]]]:
    """Group line indices by verse."""
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
# Te'amim annotation helper
# ---------------------------------------------------------------------------

_TEAMIM_NAME_BY_CHAR = {
    "֖": "tipha",
    "֔": "zaqef qatan",
    "֕": "zaqef gadol",
    "֨": "qadma",
    "֩": "telisha qetannah",
    "֫": "geresh",
    "֬": "geresh muqdam",
    "֠": "telisha gedolah",
    "֤": "pashta",
    "֙": "pashta",
    "֡": "darga",
    "֣": "munach",
    "֥": "merkha",
    "֦": "merkha kefulah",
    "֧": "darga",
    "֜": "geresh",
    "֝": "geresh muqdam",
    "֞": "gershayim",
    "֟": "qarne phara",
    "֑": "etnachta",
    "֒": "segol",
    "֓": "shalshelet",
    "֮": "zarka",
    "֭": "dehi",
    "֛": "tevir",
    "֢": "atnach hafukh",
    "֪": "yetiv",
    "֘": "zarka",
    "֗": "revia",
}


def teamim_summary(line: str) -> str:
    """Return a short informational summary of te'amim names present."""
    seen: list[str] = []
    for ch in line:
        if "֑" <= ch <= "֯":
            name = _TEAMIM_NAME_BY_CHAR.get(ch)
            if name and name not in seen:
                seen.append(name)
    if not seen:
        return ""
    return ", ".join(seen)


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    """Scan one text file for Rule M3 bare-construct-head split violations.

    Uses TAHOT morph tags (via morph_alignment) when available to classify
    the last token of each content line as a construct-state head and to
    detect finite-verb tokens on the current line.  Falls back to the local
    closed-list skel-heuristics when tags are missing or verse alignment fails.
    """
    findings: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    book = book_name_from_path(path)
    chapter_from_file = chapter_from_path(path)

    # Load TAHOT morph alignment for this chapter (None if v0/morph file absent).
    chapter_morph = MA.load_chapter_morph(path)

    verses = partition_into_verses(lines)

    # Build a lookup: line_index → (chapter, verse, position_within_verse, verse_indices)
    line_to_verse: dict[int, tuple[int | None, int | None, int, list[int]]] = {}
    for ch, vs, indices in verses:
        for pos, idx in enumerate(indices):
            line_to_verse[idx] = (ch, vs, pos, indices)

    # Build per-verse content-line groupings for morph alignment.
    # verse_key → [(file_line_idx, line_text), ...]
    from collections import defaultdict
    verse_content: dict[tuple, list[tuple[int, str]]] = defaultdict(list)
    for ch, vs, indices in verses:
        key = (ch, vs)
        for idx in indices:
            verse_content[key].append((idx, lines[idx]))

    # Cache of token-tag alignments per verse.
    # verse_key → list[list[list[str]]] | None
    _verse_token_tags: dict[tuple, object] = {}

    def _get_verse_token_tags(ch, vs):
        """Return aligned token-tag grid for (ch, vs), building on first access."""
        key = (ch, vs)
        if key in _verse_token_tags:
            return _verse_token_tags[key]
        result = None
        if chapter_morph is not None:
            ortho_tags = chapter_morph.get(vs)
            if ortho_tags is not None:
                verse_lines = [raw for _, raw in verse_content[key]]
                result = MA.align_verse_tokens_to_tags(verse_lines, ortho_tags)
        _verse_token_tags[key] = result
        return result

    def _tag_list_for(ch, vs, line_pos_in_verse: int, tok_idx: int):
        """Return TAHOT tag list for a specific token, or None on miss."""
        token_tags = _get_verse_token_tags(ch, vs)
        if token_tags is None:
            return None
        if line_pos_in_verse < 0 or line_pos_in_verse >= len(token_tags):
            return None
        tl = token_tags[line_pos_in_verse]
        if tok_idx < 0 or tok_idx >= len(tl):
            return None
        return tl[tok_idx]

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        # Determine verse context
        v_ctx = line_to_verse.get(i)
        chapter = v_ctx[0] if v_ctx else chapter_from_file
        verse = v_ctx[1] if v_ctx else None
        pos_in_verse = v_ctx[2] if v_ctx else 0

        line_no = i + 1  # 1-based

        # --- Guard 1: poetic register ---
        if chapter is not None and is_poetic_register(book, chapter, verse):
            continue

        # --- Guard 2: maqqef-binding ---
        # If the construct head is already maqqef-joined (e.g. דִּבְרֵי־יְהוָה),
        # it is one orthographic prosodic unit and not "bare construct head split."
        if construct_head_maqqef_bound(line):
            continue

        # --- Guard 3: relative clause or modifier PP on same line ---
        if line_has_relative_clause_or_modifier_pp(line):
            continue

        # --- Guard 6: construct head preceded by finite verb (false positive filter) ---
        # If a finite verb appears anywhere on the current line,
        # the line-final token is likely acting as a clause constituent (subject/object),
        # not a construct head. Filter out false positives from divine-name vocatives
        # and objects after speech-act verbs.
        # Tag-aware path: check each token via M.is_finite_verb_token(tok, tag_list=...).
        line_toks = content_tokens(line)
        has_verb_on_line = False
        for tok_i, tok in enumerate(line_toks):
            tag_list = _tag_list_for(chapter, verse, pos_in_verse, tok_i) if v_ctx else None
            if M.is_finite_verb_token(tok, tag_list=tag_list):
                has_verb_on_line = True
                break
        if has_verb_on_line:
            continue

        # --- Check if line ends with a construct head (tag-aware) ---
        if not line_toks:
            continue
        last_tok = line_toks[-1]
        last_tok_idx = len(line_toks) - 1
        last_tok_tags = _tag_list_for(chapter, verse, pos_in_verse, last_tok_idx) if v_ctx else None

        # Tag-driven primary: M.is_construct_head_token with TAHOT oracle.
        # Skel fallback: last_token_is_construct_head (local closed list).
        is_construct_tag = M.is_construct_head_token(last_tok, tag_list=last_tok_tags)
        is_construct_skel, construct_skel_local = last_token_is_construct_head(line)

        if not (is_construct_tag or is_construct_skel):
            continue

        # For the annotation: prefer tag-confirmed skeleton label; fall back to local.
        construct_skel = strip_points(last_tok).rstrip("׃").rstrip("־") if is_construct_tag else construct_skel_local

        # --- Find next content line in the SAME verse ---
        next_idx: int | None = None
        for j in range(i + 1, len(lines)):
            if is_skippable(lines[j]):
                continue
            n_ctx = line_to_verse.get(j)
            if v_ctx and n_ctx and (n_ctx[0], n_ctx[1]) != (v_ctx[0], v_ctx[1]):
                break
            next_idx = j
            break
        if next_idx is None:
            continue
        next_line = lines[next_idx]
        next_line_no = next_idx + 1

        # --- Guard 4: next line must NOT start with a preposition ---
        next_starts_prep, _ = starts_with_preposition(next_line)
        if next_starts_prep:
            continue

        # --- Guard 5: next line must NOT start with a verb ---
        if first_token_looks_like_verb(next_line):
            continue

        # --- Check if next line begins with a noun (rectum candidate) ---
        first = first_content_token(next_line)
        if not first:
            continue

        # The bare skeleton should be non-empty (implies a noun/article).
        bare_first = strip_points(first)
        if not bare_first:
            continue

        # --- All guards passed; emit STRONG-MERGE-CANDIDATE finding ---
        prior_text = line.strip()
        next_text = next_line.strip()

        prior_teamim = teamim_summary(line)
        next_teamim = teamim_summary(next_line)
        teamim_note = ""
        if prior_teamim or next_teamim:
            teamim_note = (
                f" Te'amim placement: {prior_teamim or '(none)'} on construct head, "
                f"{next_teamim or '(none)'} on rectum — informational only."
            )

        tag_note = " (TAHOT-confirmed)" if is_construct_tag else " (skel-heuristic)"
        annotation = (
            f"Bare construct-state head {construct_skel!r}{tag_note} without rectum "
            "(M3 Bare-Governor Indivisibility; canon §1; JM §129; WO §9)."
            + teamim_note
        )

        brief = (
            f"construct chain split: {prior_text} // {next_text}"
        )

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "M3/bare-construct-head",
            "severity": "STRONG-MERGE-CANDIDATE",
            "construct_head": construct_skel,
            "tag_confirmed": is_construct_tag,
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "prior_line": prior_text,
            "next_line": next_text,
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
                "construct_head": f["construct_head"],
                "tag_confirmed": f.get("tag_confirmed", False),
                "book": f["book"],
                "chapter": f["chapter"],
                "verse": f["verse"],
                "prior_line": f["prior_line"],
                "next_line": f["next_line"],
                "next_line_num": f["next_line_num"],
                "annotation": f["annotation"],
            })

        counts = {"STRONG-MERGE-CANDIDATE": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        doc = {
            "validator": "validate_bare_construct_head",
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
    print(f"Rule M3 Bare-Governor Indivisibility (Construct-Chain) validator — Tanakh {tier_label}")
    print(f"Reference: canon §1 M3 (bare construct head awaiting rectum)")
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
                print(f"    Construct head: {f['construct_head']!r}")
                print(f"    {f['prior_line'][:120]}")
                print(f"    → {f['next_line'][:120]}")
                print(f"    {f['annotation']}")
                print()
    else:
        print("No findings. Rule M3 bare-governor indivisibility (construct-chain) is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
