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
  NOTE: Poetic-register suppression was removed 2026-05-04 (methodology audit:
  overlay-as-authorization violation). Poetic register classification is
  calibration evidence, not authorization to suppress findings. Construct chains
  occur in poetry (e.g. Ps 23:1 רֹעִי); the validator now applies in all registers.
  1. Intervening modifier — relative clause or PP modifies the construct head
     itself (not the final rectum), keeping the regens with its modifier.
  2. Maqqef-binding — the chain is internally maqqef-joined (already one
     prosodic unit orthographically).
  3. Already-long chain — construct chain ≥3 levels deep with substantial
     final rectum modifier (evaluated under structural justification 5).

IR-DRIVEN PATH (post-Wave-C merge):
When Macula lowfat data is available for a chapter, the scanner consults the
IR before emitting:

  IR-confirmed + NPofNP found → the construct_chain validator (H2/construct)
    already covers this edge via its NPofNP split walk. Suppress here to
    avoid double-emit; defer to validate_construct_chain.py.

  IR-confirmed construct state (token.state == "construct") but NO enclosing
    NPofNP in the IR tree → the parser missed the chain (known limitation of
    the Macula NPofNP recall). Emit STRONG-MERGE-CANDIDATE with "(IR-confirmed
    construct, no NPofNP parent — heuristic fallback)" annotation.

  No IR data (lowfat file absent) → heuristic path unchanged; emit STRONG as
    before.

This merge eliminates the ~60-70% of findings that are genuinely redundant
with validate_construct_chain.py, while preserving the ~15-35 parser-missed
cases that only this validator can catch.

Pattern:
Line N ends with a bare construct-state noun (tag-confirmed or closed-list
skel). Line N+1 begins with a noun (no preposition, no verb) that completes
the chain.

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
# Path constants — two-tier layout: v1/he-baseline + v2/heb
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files"  / "v2" / "heb"

# Make _shared importable when this script is run as __main__.
sys.path.insert(0, str(REPO_ROOT / "validators"))
from _shared import morphology as M  # noqa: E402
from _shared import morph_alignment as MA  # noqa: E402
from _shared import macula_constituents as MC  # noqa: E402

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

# Proper-name skeletons that are FP-prone in the closed-list skel-heuristic.
# יהוה and אדני have identical consonant skeletons in absolute and construct
# state, and the closed-list skel-heuristic systematically over-fires when
# these tokens appear vocative, as rectum of an already-completed chain, or
# as subject of the next-line verb. Surfaced by Torah + Sifrei Emet
# cluster-Opus FP-rate verdicts (2026-05-05): 9/10 fixture FPs all on יהוה
# (Psa 5:4, 37:9, 40:12, 115:1, 118:26, 119:108, 121:8 vocative /
# rectum-of-completed-chain / subject-of-next-line). Per agent recommendation,
# proper-name-vs-construct disambiguation requires IR state == "construct"
# confirmation, not skel-only.
#
# When ONLY the skel-heuristic matches (TAHOT tag returns False) AND the skel
# match is in this set AND IR does not confirm construct state, the emission
# is suppressed. See the FP guard in scan_file().
PROPER_NAME_FP_SKELETONS = {"יהוה", "אדני"}


CONSTRUCT_HEAD_SKELETONS = {
    # Very common construct heads in narrative
    "דבר",     # word, matter
    "בית",     # house
    "בן",      # son
    "בת",      # daughter
    "אדני",    # Lord — proper-name FP-prone, see PROPER_NAME_FP_SKELETONS
    "יהוה",    # YHWH — proper-name FP-prone, see PROPER_NAME_FP_SKELETONS
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

# ---------------------------------------------------------------------------
# IR helpers — Macula lowfat construct-chain detection
# ---------------------------------------------------------------------------

def _collect_npofnp_constituents(constituents: list) -> list:
    """Recursively gather all Constituent nodes where is_construct_chain == True."""
    out: list = []

    def walk(node) -> None:
        if isinstance(node, MC.Token):
            return
        if node.is_construct_chain:
            out.append(node)
        for c in node.children:
            walk(c)

    for r in constituents:
        walk(r)
    return out


def build_ir_construct_sets(
    lines: list[str],
    book_slug: str,
    ch: int,
    vs: int,
    sense_indices: list[int],
) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    """Return (ir_confirmed_edges, npofnp_covered_edges) for one verse.

    ir_confirmed_edges: (line_N_idx, line_N1_idx) pairs where the IR confirms
        the last token on line N has state=="construct" and the next line (in
        the same verse) begins with the token immediately following it in the
        verse token stream.  This means the IR says: yes, the construct head
        is here, its completion is on the next line.

    npofnp_covered_edges: subset of ir_confirmed_edges where the construct
        head's token is also inside an NPofNP constituent that spans across
        the two lines.  validate_construct_chain.py will catch these; we
        suppress bare_construct_head from double-emitting them.

    Both sets are empty if the lowfat file is absent or alignment fails.
    """
    ir_confirmed: set[tuple[int, int]] = set()
    npofnp_covered: set[tuple[int, int]] = set()

    if len(sense_indices) < 2:
        return ir_confirmed, npofnp_covered

    try:
        verse_tokens = MC.get_verse_tokens(book_slug, ch, vs)
        verse_constituents = MC.get_verse_constituents(book_slug, ch, vs)
    except (FileNotFoundError, ValueError, KeyError):
        return ir_confirmed, npofnp_covered
    if not verse_tokens:
        return ir_confirmed, npofnp_covered

    # Build token_id → sense_line_index map (greedy alignment, same as
    # validate_construct_chain.py).
    token_to_line: dict[str, int] = {}
    cursor = 0
    for sl_idx, src_idx in enumerate(sense_indices):
        matched, cursor = MC.match_sense_line_tokens(
            verse_tokens, lines[src_idx], start_idx=cursor
        )
        for tok in matched:
            token_to_line[tok.xml_id] = sl_idx

    # Also build a position-in-verse → Token map for fast next-token lookup.
    # verse_tokens is ordered by position.
    tok_by_pos: dict[int, "MC.Token"] = {t.position: t for t in verse_tokens}
    max_pos = max(tok_by_pos) if tok_by_pos else 0

    # Walk each consecutive sense-line pair and check whether:
    #   (a) the last aligned token of line N is construct-state in the IR,
    #   (b) the first aligned token of line N+1 immediately follows it in
    #       the verse token stream (no gap — the chain is contiguous).
    for sl_idx in range(len(sense_indices) - 1):
        src_n = sense_indices[sl_idx]
        src_n1 = sense_indices[sl_idx + 1]

        # Collect tokens on each line via the token_to_line map.
        toks_n = [t for t in verse_tokens if token_to_line.get(t.xml_id) == sl_idx]
        toks_n1 = [t for t in verse_tokens if token_to_line.get(t.xml_id) == sl_idx + 1]
        if not toks_n or not toks_n1:
            continue

        last_tok_n = toks_n[-1]
        first_tok_n1 = toks_n1[0]

        # IR-confirmed: last token of line N has state == "construct".
        if last_tok_n.state != "construct":
            continue

        # The rectum must immediately follow (no gap between positions).
        if first_tok_n1.position != last_tok_n.position + 1:
            continue

        edge = (src_n, src_n1)
        ir_confirmed.add(edge)

    # NPofNP coverage: find all NPofNP constituents that span across two lines.
    npofnp_list = _collect_npofnp_constituents(verse_constituents)
    for npofnp in npofnp_list:
        chain_tokens = npofnp.tokens
        if len(chain_tokens) < 2:
            continue
        first_chain = chain_tokens[0]
        last_chain = chain_tokens[-1]
        first_sl = token_to_line.get(first_chain.xml_id)
        last_sl = token_to_line.get(last_chain.xml_id)
        if first_sl is None or last_sl is None or first_sl == last_sl:
            continue
        # The NPofNP spans lines first_sl..last_sl. Cover all consecutive
        # pairs in that span — but for our purpose just cover adjacent pairs.
        for sl_idx in range(first_sl, last_sl):
            src_n = sense_indices[sl_idx]
            src_n1 = sense_indices[sl_idx + 1]
            npofnp_covered.add((src_n, src_n1))

    return ir_confirmed, npofnp_covered


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

    # IR construct-edge sets, cached per (chapter, verse) to avoid redundant
    # Macula XML lookups across consecutive lines in the same verse.
    # Each entry: (ir_confirmed_edges, npofnp_covered_edges) — both are
    # sets of (line_N_src_idx, line_N1_src_idx) tuples.
    _ir_cache: dict[tuple, tuple[set, set]] = {}

    def _get_ir_sets(ch, vs, sense_indices):
        key = (ch, vs)
        if key not in _ir_cache:
            _ir_cache[key] = build_ir_construct_sets(lines, book, ch, vs, sense_indices)
        return _ir_cache[key]

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        # Determine verse context
        v_ctx = line_to_verse.get(i)
        chapter = v_ctx[0] if v_ctx else chapter_from_file
        verse = v_ctx[1] if v_ctx else None
        pos_in_verse = v_ctx[2] if v_ctx else 0

        line_no = i + 1  # 1-based

        # --- Guard 1: maqqef-binding ---
        # (Poetic-register guard removed 2026-05-04: overlay-as-authorization
        # violation. Poetic register is calibration evidence, not authorization
        # to suppress. The validator now applies in all registers.
        # Superseded by 2026-05-04 methodology audit.)
        # If the construct head is already maqqef-joined (e.g. דִּבְרֵי־יְהוָה),
        # it is one orthographic prosodic unit and not "bare construct head split."
        if construct_head_maqqef_bound(line):
            continue

        # --- Guard 2: relative clause or modifier PP on same line ---
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

        # --- All guards passed; IR cross-check before emitting ---

        # Pull IR edge sets for this verse (cached).
        ir_confirmed_edges: set[tuple[int, int]] = set()
        npofnp_covered_edges: set[tuple[int, int]] = set()
        if v_ctx and chapter is not None and verse is not None:
            sense_indices_for_verse = v_ctx[3]
            ir_confirmed_edges, npofnp_covered_edges = _get_ir_sets(
                chapter, verse, sense_indices_for_verse
            )

        edge = (i, next_idx)
        ir_confirmed_this = edge in ir_confirmed_edges
        npofnp_covered_this = edge in npofnp_covered_edges

        # Suppress double-emit: if IR confirms NPofNP coverage, validate_construct_chain
        # will emit this. Skip here to avoid redundant STRONG-MERGE-CANDIDATE.
        if npofnp_covered_this:
            continue

        # --- Proper-name FP guard (post-FP-rate audit 2026-05-05) ---
        # When ONLY the skel-heuristic matches (TAHOT tag did not confirm
        # construct state) AND the skel match is a proper name in
        # PROPER_NAME_FP_SKELETONS (יהוה / אדני) AND IR does not confirm
        # construct state for this edge, suppress. The Torah + Sifrei Emet
        # cluster-Opus FP-rate verdicts documented this as a 9/10-FP class:
        # the proper-name consonant skeleton is identical in absolute and
        # construct state, so the closed-list skel match over-fires on
        # vocative, rectum-of-completed-chain, and subject-of-next-line cases.
        if (
            (not is_construct_tag)
            and is_construct_skel
            and construct_skel_local in PROPER_NAME_FP_SKELETONS
            and not ir_confirmed_this
        ):
            continue

        # --- Emit STRONG-MERGE-CANDIDATE finding ---
        prior_text = line.strip()
        next_text = next_line.strip()
        if ir_confirmed_this:
            # IR confirms construct state but no NPofNP parent in the tree —
            # this is a parser-missed case not covered by validate_construct_chain.
            tag_note = " (IR-confirmed construct, no NPofNP parent — parser-missed)"
        elif is_construct_tag:
            tag_note = " (TAHOT-confirmed)"
        else:
            tag_note = " (skel-heuristic)"

        annotation = (
            f"Bare construct-state head {construct_skel!r}{tag_note} without rectum "
            "(M3 Bare-Governor Indivisibility; canon §1; JM §129; WO §9)."
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
            "ir_confirmed": ir_confirmed_this,
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
    parser.add_argument("--v2", action="store_true", help="Scan v2/heb (default if v1 missing).")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show context.")
    parser.add_argument("--json", action="store_true", help="Emit JSON document.")
    args = parser.parse_args()

    base_dir = V2_DIR if args.v2 else V1_DIR
    tier_label = "v2/heb" if args.v2 else "v1/he-baseline"
    if not base_dir.exists():
        alt = V2_DIR if not args.v2 else V1_DIR
        if alt.exists():
            base_dir = alt
            tier_label = "v2/heb" if alt is V2_DIR else "v1/he-baseline"
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
                "ir_confirmed": f.get("ir_confirmed", False),
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
