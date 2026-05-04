#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Rule H18 — Clause-Nucleus Integrity.

Rule H18 (canon §5; Layer 3 editorial rule):
A Hebrew clause-nucleus — verbless predication, participial predicate, or
finite-verb + obligatory-PP-complement — is a single grammatical unit and
should occupy a single colometric line. The mechanical te'amim-derived
v1-baseline frequently splits these nuclei into separate lines; this
validator surfaces the splits as REVIEW-REQUIRED candidates for the editor.

Three sub-cases (canon §5 H18.1 / H18.2 / H18.3):

  verbless_subj_pred_split   — H18.1: NP-ending line (no finite verb anywhere
                               on the line) followed by prep-fronted line
                               (no finite verb anywhere). Verbless subject +
                               PP/locative predicate.

  participial_pred_split     — H18.2: NP-ending line (no finite verb) followed
                               by line that begins with a bare participle
                               (Pi'el/Pu'al/Hifil/Hofal/Hitpael m-prefix
                               participle, or qal active CoCeC participle).

  verb_pp_complement_split   — H18.3 / M2 corpus extension: line ends with a
                               finite verb skeleton from a small high-confidence
                               list of verbs that govern obligatory PP
                               complements (שָׁמַע ל, נָשָׂא ... אֶל, פָּנָה אֶל,
                               etc.); next line begins with a preposition + NP.

ARCHITECTURAL CONSTRAINT — NO TE'AMIM IN PREDICATES:
All trigger logic uses Hebrew morpho-syntactic patterns ONLY. The te'amim
Unicode range (U+0591–U+05AF) does NOT appear in any predicate that decides
whether to fire a finding. Te'amim MAY appear in finding annotations as
informational defensibility-capture (Rule H8) — the trigger must remain
syntactic.

SEVERITY:
H18.1 and H18.2 emit at REVIEW-REQUIRED (awaiting ≥80% editor agreement per
canon §7.4 adoption protocol). H18.3 emits at STRONG-MERGE-CANDIDATE — promoted
via YAML spec validators/specs/h18_3_verb_pp_complement.yaml after 9/9 TP rate
corpus survey (100%) met the §7.4 threshold. The H18.3 branch here is
SUPERSEDED by that spec; it remains for corpus-audit cross-reference only.

FORCED-NO-MERGE GUARDS (skip BEFORE emitting):
  1. Poetic register — is_poetic_register(book, chapter, verse) → skip.
  2. H4 vocative — prior line is a vocative unit (address particle, or short
     line ending in divine vocative).
  3. H14 discourse particle — next line starts with הִנֵּה / אַף / עַל־כֵּן /
     לָכֵן / וְעַתָּה / אָז / עַתָּה.
  4. H15 casus pendens — line AFTER candidate-second contains a 3rd-person
     pronominal suffix possibly coreferential with the prior NP.
  5. H16 FEF wayehi protasis — verse opens with וַיְהִי and לֵאמֹר not yet
     reached.
  6. M3 bare-governing participle — next line is JUST a participle with no
     complement.
  7. Heavy subject — אֲשֶׁר / שֶׁ- / מִי / מָה anywhere on prior line; ≥2
     בֶּן / בַּת appositives; or itself a deep construct chain.
  8. Heavy participial complement — participle followed by both DO (אֵת) AND
     PP, with combined participial-side ≥5 prosodic words.
  9. Both lines have a finite verb anywhere — parallelism territory.
 10. Next-line prep takes לְ + infinitive — purpose-PP territory.
 11. Combined > 8 prosodic words — guardrail against substantive-adjunct
     over-merging.

Output format:
    [DEVIATION]  file:line  H18/clause-nucleus-split  REVIEW-REQUIRED  subcase  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_clause_nucleus_split.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_clause_nucleus_split.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_clause_nucleus_split.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_clause_nucleus_split.py --json
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
from _shared import morph_alignment as MA  # noqa: E402
from _shared import morphology as M  # noqa: E402
from _shared import macula_constituents as MC  # noqa: E402

# ---------------------------------------------------------------------------
# IR-driven helpers (post-2026-05-05 Macula pivot, Wave C)
#
# Replace heuristic predicates with declarative IR queries when per-line
# IR alignment is available. The legacy heuristic helpers remain as
# fallback for chapters where lowfat alignment fails (parser gaps, etc.).
# ---------------------------------------------------------------------------


def line_has_finite_verb_ir(line_ir_tokens: list["MC.Token"]) -> bool:
    """True if any token in the line is a finite verb (qatal/yiqtol/wayyiqtol/
    imperative/jussive/cohortative). Replaces `looks_like_finite_verb` /
    `line_has_finite_verb_tagged` heuristic."""
    return any(t.is_finite_verb for t in line_ir_tokens)


def starts_with_participle_ir(line_ir_tokens: list["MC.Token"]) -> bool:
    """True if the first content token is an active or passive participle.
    Replaces `starts_with_participle` skel-heuristic."""
    for t in line_ir_tokens:
        if not t.text.strip():
            continue
        return t.is_participle
    return False


def starts_with_prep_ir(line_ir_tokens: list["MC.Token"]) -> tuple[bool, str | None]:
    """True if the first content token is a preposition. Returns (is_prep, lemma).
    Replaces `starts_with_prep` skel-heuristic."""
    for t in line_ir_tokens:
        if not t.text.strip():
            continue
        if t.is_preposition:
            return True, t.lemma
        return False, None
    return False, None


def starts_with_le_infinitive_ir(line_ir_tokens: list["MC.Token"]) -> bool:
    """True if the line starts with לְ (preposition lemma 'ל') + infinitive
    construct. Replaces `starts_with_le_infinitive` skel-heuristic."""
    content = [t for t in line_ir_tokens if t.text.strip()]
    if len(content) < 2:
        return False
    if not content[0].is_preposition or content[0].lemma != "ל":
        return False
    return content[1].is_infinitive_construct


def line_is_bare_participle_ir(line_ir_tokens: list["MC.Token"]) -> bool:
    """True if the line consists primarily of a participle predicate with
    no PP/NP complement on the same line. Heuristic but IR-grounded."""
    content = [t for t in line_ir_tokens if t.text.strip()]
    if not content:
        return False
    # Must contain at least one participle
    has_participle = any(t.is_participle for t in content)
    if not has_participle:
        return False
    # No PP-head (preposition that's not the participle's own complement marker)
    # Loosely: bare-ish if no preposition appears anywhere in the line.
    has_prep = any(t.is_preposition for t in content)
    return not has_prep


def line_has_3p_pronominal_suffix_ir(line_ir_tokens: list["MC.Token"]) -> bool:
    """True if any token has a participantref pointing to an antecedent token
    elsewhere in the chapter — i.e., 3rd-person resumptive suffix (casus
    pendens material). IR replaces orthographic suffix-detection."""
    for t in line_ir_tokens:
        if t.is_suffix and t.antecedents:
            return True
    return False


def verse_is_wayehi_with_open_protasis_ir(
    book_slug: str, chapter: int, verse: int,
    next_line_pos_in_verse: int,
    verse_sense_lines: list[str],
) -> bool:
    """True if the verse opens with a wayehi (וַיְהִי) construction whose
    apodosis hasn't yet appeared by `next_line_pos_in_verse`. Uses IR
    lemma+aspect to identify the wayehi trigger."""
    try:
        verse_tokens = MC.get_verse_tokens(book_slug, chapter, verse)
    except (FileNotFoundError, ValueError, KeyError):
        return False
    if not verse_tokens:
        return False
    first = verse_tokens[0]
    if first.lemma != "הָיָה" or not first.is_wayyiqtol:
        return False
    # Crude: if the next-line-pos-in-verse is small (<=2), assume protasis
    # likely still open. The exact apodosis detection is heuristic; this
    # IR check primarily replaces the wayehi-trigger detection.
    return next_line_pos_in_verse <= 2

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers
# ---------------------------------------------------------------------------

# Hebrew points (cantillation U+0591–U+05AF + niqqud U+05B0–U+05BC, U+05C1–U+05C2,
# U+05C4–U+05C5, U+05C7).  This regex covers the full points range.
# Strip U+0591-U+05BD (cantillation + niqqud) and U+05BF, U+05C1-U+05C2, U+05C4-U+05C5, U+05C7
# while PRESERVING maqqef (U+05BE), paseq (U+05C0), and sof pasuq (U+05C3) so that
# compound prepositions, prosodic word boundaries, and verse ends remain visible.
HEBREW_POINTS_RE = re.compile(r"[֑-ׇֽֿׁׂׅׄ]")

# Niqqud-only regex (no te'amim) — used for syntactic vowel inspection in the
# participial heuristic.  Stripping te'amim leaves vowels intact so we can read
# the vowel pattern under each consonant.
TEAMIM_ONLY_RE = re.compile(r"[֑-֯]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"  # ׃
# Maqqef (orthographic word-joiner)
MAQQEF = "־"     # ־
# Paseq (vertical bar disjunction)
PASEQ = "׀"      # ׀

# Niqqud individual marks (for vowel-pattern detection on participles).
# Holam haser (no waw) and holam male require slightly different handling.
HOLAM = "ֹ"        # ֹ  — holam (above the consonant)
SHEVA = "ְ"        # ְ  — shewa
PATAH = "ַ"        # ַ  — patah
QAMATS = "ָ"       # ָ  — qamats
HIRIQ = "ִ"        # ִ  — hiriq
QUBUTS = "ֻ"       # ֻ  — qubuts
TSERE = "ֵ"        # ֵ  — tsere
SEGOL = "ֶ"        # ֶ  — segol
DAGESH = "ּ"       # ּ  — dagesh / shuruq mark on waw

# Hebrew letters used in heuristic predicates.
BET = "ב"
KAF = "כ"
LAMED = "ל"
MEM = "מ"


def strip_points(token: str) -> str:
    """Return token with niqqud and te'amim stripped (consonant skeleton + sof pasuq + maqqef)."""
    return HEBREW_POINTS_RE.sub("", token)


def strip_teamim_only(token: str) -> str:
    """Return token with te'amim stripped, niqqud preserved.

    Used by the participial heuristic, which inspects vowel patterns and
    must NOT use te'amim in its predicate.
    """
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


def prosodic_word_count(line: str) -> int:
    """Count prosodic words.

    Whitespace-delimited tokens, with maqqef-joined groups counted as one
    prosodic word (canon §5 H1).  Since maqqef joins tokens orthographically
    INSIDE a single whitespace-delimited token (Hebrew text uses no spaces
    around maqqef), each whitespace-delimited content token is already one
    prosodic word.
    """
    return len(content_tokens(line))


def first_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[0] if toks else None


def last_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[-1] if toks else None


# ---------------------------------------------------------------------------
# Finite-verb skeleton heuristic
# ---------------------------------------------------------------------------

# Strong wayyiqtol prefix (consonants only): tokens starting with וי or ות or וא or ונ or וי
# in conjunction with a dagesh on the second-radical consonant pattern.  Surface
# detection on the bare skeleton: "וי", "ות", "וא" (less common), "ונ" — the
# וַיִּ / וַתִּ / וָאֶ / וַנִּ patterns.
WAYYIQTOL_PREFIXES = ("וי", "ות", "ונ", "וא")

# Yiqtol prefix consonants (after stripping niqqud + te'amim): י / ת / א / נ
# But this overlaps with many noun forms.  We use a conservative test: the
# token starts with one of these consonants AND has a 3-consonant skeleton
# matching a verb pattern (3 root consonants after the prefix).  Since
# the heuristic is allowed to miss (false-negatives only cause emit, which is
# REVIEW-REQUIRED), we keep it tight.
#
# Approach: maintain a closed list of "high-confidence finite-verb prefix +
# core-consonant" patterns.  For the trigger we mainly need NEGATIVE evidence
# — "no finite verb anywhere" — so we err on the side of detecting MORE
# finite-verb candidates (which causes us to skip the finding, the safe side).

# Common qatal endings (consonant skeletons after te'amim stripped):
QATAL_SUFFIXES = (
    "תי",   # 1cs perfect — קָטַלְתִּי → קטלתי
    "תָ",   # 2ms — but qamats; we strip points, so we can't see this
    "ת",    # 2ms (after strip) — overlaps with feminine noun ending; risky
    "נו",   # 1cp — קָטַלְנוּ → קטלנו (overlaps with our pronoun)
    "תם",   # 2mp
    "תן",   # 2fp
    "ו",    # 3cp — קָטְלוּ (overlaps with vav-conjunction trailing — we use it carefully)
)

# Imperative skeletons commonly start with verb root.  Hard to detect reliably.

# Specific high-frequency finite-verb skeletons we recognize directly.
# These are consonant-only, post-strip.  We bias toward over-detecting verbs
# so the "no finite verb anywhere" guard fires conservatively (skipping a
# real candidate is acceptable; emitting a false-positive is not).
KNOWN_FINITE_VERB_SKELETONS = {
    # Common qatal 3ms / 3fs / 3cp forms
    "אמר", "אמרה", "אמרו", "אמרתי", "אמרת", "אמרנו", "אמרתם",
    "ראה", "ראתה", "ראו", "ראיתי", "ראית", "ראינו",
    "שמע", "שמעה", "שמעו", "שמעתי", "שמענו",
    "ידע", "ידעה", "ידעו", "ידעתי", "ידעת", "ידענו",
    "ברא", "בראה", "בראו",                       # ברא — created (Gen 1:1)
    "ברך", "ברכה", "ברכו", "ברכתי", "ברכת",
    "הלך", "הלכה", "הלכו", "הלכתי", "הלכנו",
    "נתן", "נתנה", "נתנו", "נתתי", "נתת",
    "עשה", "עשתה", "עשו", "עשיתי", "עשית", "עשינו",
    "היה", "היתה", "היו", "הייתי", "היית", "היינו",
    "בא", "באה", "באו", "באתי", "באת", "באנו",
    "קם", "קמה", "קמו", "קמתי", "קמנו",
    "בנה", "בנתה", "בנו", "בניתי",               # בנה — built
    "לקח", "לקחה", "לקחו", "לקחתי",              # לקח — took
    "כתב", "כתבה", "כתבו", "כתבתי",              # כתב — wrote
    "כרת", "כרתה", "כרתו",                       # כרת — cut
    "מצא", "מצאה", "מצאו", "מצאתי",              # מצא — found
    "נשא", "נשאה", "נשאו", "נשאתי",              # נשא — lifted
    "נפל", "נפלה", "נפלו", "נפלתי",              # נפל — fell
    "ישב", "ישבה", "ישבו", "ישבתי",              # ישב — sat
    "עבר", "עברה", "עברו",                       # עבר — passed
    "אכל", "אכלה", "אכלו", "אכלתי",              # אכל — ate
    "שתה", "שתתה", "שתו",                        # שתה — drank
    "מת", "מתה", "מתו", "מתי",                   # מת — died
    "חיה", "חיתה", "חיו",                        # חיה — lived
    "סר", "סרה", "סרו",                          # סר — turned
    "עלה", "עלתה", "עלו", "עליתי",               # עלה — went up
    "ירד", "ירדה", "ירדו",                       # ירד — went down
    "שב", "שבה", "שבו", "שבתי",                  # שב — returned
    "הכה", "הכתה", "הכו",                        # הכה — struck
    "הביא", "הביאה", "הביאו",                     # הביא — brought
    "הוציא", "הוציאה", "הוציאו",                  # הוציא — brought out
    "הגיד", "הגידה", "הגידו",                     # הגיד — told
    "הציל", "הצילה", "הצילו",                     # הציל — delivered
    "צוה", "צותה", "צוו",                        # צוה — commanded
    "דבר", "דברה", "דברו",                       # דבר piel — spoke
    "פנה", "פנתה", "פנו",                        # פנה — turned
    "נסע", "נסעה", "נסעו",                       # נסע — journeyed
    # Common yiqtol stems (3rd person, qal active).
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
    # Common imperatives (distinctive forms)
    "שמעו", "ראו", "לכו", "קומו", "עשו",
    "לך", "קום", "בא", "קח", "תן",
}


def looks_like_finite_verb(bare: str) -> bool:
    """Heuristic: does this bare consonant skeleton look like a finite verb?

    Conservative bias: we'd rather over-detect finite verbs (causing the
    no-merge guard to fire and the finding to be skipped) than under-detect
    them (emit a finding the editor would reject).
    """
    if not bare:
        return False

    # Direct skeleton match
    if bare in KNOWN_FINITE_VERB_SKELETONS:
        return True

    # Strip leading conjunction ו (vav-consecutive or simple conjunction)
    # before checking known skeletons.  Don't strip if it's a wayyiqtol
    # prefix (which we want to recognize).
    if bare.startswith(WAYYIQTOL_PREFIXES):
        # Wayyiqtol — ALWAYS finite.
        # Pattern: וי / ות / וא / ונ + 2+ consonants → finite verb.
        # Length check avoids matching "ויהוה" (which is just YHWH with
        # vav-prefix — a noun, not a verb).
        if len(bare) >= 4 and bare not in ("ויהוה",):
            return True

    # Maqqef-internal: take the last segment (the head verb may be at end)
    if MAQQEF in bare:
        for part in bare.split(MAQQEF):
            if not part:
                continue
            if part in KNOWN_FINITE_VERB_SKELETONS:
                return True
            if part.startswith(WAYYIQTOL_PREFIXES) and len(part) >= 4:
                return True

    # Qatal-suffix sniff: bare skeleton ending in one of the distinctive
    # 1cs/1cp/2mp/2fp/2fs perfect endings AND length ≥ 4 → likely finite.
    for suf in ("תי", "תם", "תן", "נו"):
        if bare.endswith(suf) and len(bare) >= 4:
            return True

    return False


def line_has_finite_verb(line: str) -> bool:
    """True if any content token on `line` looks like a finite verb (skel-heuristic only).

    Used by sub-functions that lack per-line tag context (e.g., vocative guard,
    participle-complement look-ahead).  The main scan loop uses
    `line_has_finite_verb_tagged` instead.
    """
    for tok in content_tokens(line):
        bare = strip_points(tok)
        if looks_like_finite_verb(bare):
            return True
    return False


def line_has_finite_verb_tagged(
    line: str, token_tags: "list[list[str]] | None" = None
) -> bool:
    """Tag-aware finite-verb test for a full line.

    If `token_tags` is provided (parallel to `content_tokens(line)`), each
    token is tested via the TAHOT-tag primary path in M.is_finite_verb_token.
    Falls back to skel-heuristic when token_tags is None or alignment is off.

    `token_tags` is the per-token list from MA.align_verse_tokens_to_tags:
    a list[list[str]] where index i holds the ortho-morph tag list for the
    i-th content token on the line.
    """
    toks = content_tokens(line)
    for tok_idx, tok in enumerate(toks):
        tag_list: "list[str] | None" = None
        if token_tags is not None and tok_idx < len(token_tags):
            tag_list = token_tags[tok_idx]
        if M.is_finite_verb_token(tok, tag_list=tag_list):
            return True
    return False


# ---------------------------------------------------------------------------
# Preposition heuristic — does the line start with a preposition?
# ---------------------------------------------------------------------------

# Standalone prepositions (consonant skeletons after stripping)
STANDALONE_PREPS = {
    "על", "אל", "מן", "עם", "תחת", "בין",
    "לפני", "אחרי", "מאחרי", "מלפני", "מפני", "מאת",
    "בעד", "נגד", "מעל", "מתחת", "בתוך", "מתוך",
}

# Compound prepositions joined by maqqef (e.g. על־פני, אל־תוך)
COMPOUND_PREP_HEADS = {"על", "אל", "מן", "עד", "מעל", "מתחת", "בין", "בתוך", "מתוך"}


def starts_with_prep(line: str) -> tuple[bool, str | None]:
    """Heuristic: does the first content token of `line` begin with a preposition?

    Returns (True, prep_skeleton) on match, (False, None) otherwise.

    Recognizes:
      - Standalone prepositions: על, אל, מן, etc.
      - Maqqef-compound: על־פני, אל־תוך, etc.
      - Bound prefix prepositions: ב + bound, ל + bound, כ + bound, מ + bound
        (the prefix consonant attaches to the next noun without space).
    """
    first = first_content_token(line)
    if not first:
        return False, None
    bare = strip_points(first)
    if not bare:
        return False, None

    # Maqqef-compound: split on first maqqef, check head
    if MAQQEF in bare:
        head = bare.split(MAQQEF, 1)[0]
        if head in COMPOUND_PREP_HEADS:
            return True, head
        if head in STANDALONE_PREPS:
            return True, head

    # Standalone preposition word
    if bare in STANDALONE_PREPS:
        return True, bare

    # Bound prefix prepositions (ב/ל/כ/מ + bound noun).
    # Identify by leading consonant + vowel pattern on the prefix.  The risk
    # of false positives is real: בָּרָא ("created", qatal of ברא) starts
    # with ב + qamats, so does the prep+definite "in the [X]" pattern with
    # assimilated article.  Disambiguation:
    #   - Bound prep ב/ל/כ takes SHEWA most often (indefinite); also patah,
    #     segol, hiriq for definite/special cases.  We accept those four.
    #   - QAMATS under bound prep is grammatically possible but collides with
    #     too many qatal-3ms verb forms (בָּרָא, בָּנָה, לָקַח, כָּתַב,
    #     כָּרַת).  We exclude qamats to keep precision; the cost is missing
    #     some prep+definite cases (acceptable since they're still definite
    #     PPs that only occur in specific phonological contexts).
    #   - Bound prep מ is מִ + dagesh (assimilated min-) — vowel hiriq on מ.
    #
    # We also use a small known-verb-skeleton exclusion list for high-frequency
    # verbs whose qal qatal forms start with ב/ל/כ + vowel.
    teamim_stripped = strip_teamim_only(first)
    if len(bare) >= 3 and bare[0] in (BET, LAMED, KAF):
        # Reject very common false positives first:
        if bare in ("לא", "לכן"):
            return False, None
        if len(teamim_stripped) >= 2:
            second_char = teamim_stripped[1]
            # Allowed prefix vowels: shewa, patah, segol, hiriq.
            # (Qamats and tsere excluded — they too often signal qatal verbs.)
            if second_char in (SHEVA, PATAH, SEGOL, HIRIQ):
                return True, bare[0]

    if len(bare) >= 3 and bare[0] == MEM:
        # מִ + dagesh (assimilated min-) — vowel under מ is hiriq, dagesh on next consonant
        if len(teamim_stripped) >= 3:
            if teamim_stripped[1] == HIRIQ:
                return True, "מ"

    return False, None


def starts_with_le_infinitive(line: str) -> bool:
    """True if line begins with ל + infinitive-construct (purpose-PP territory)."""
    first = first_content_token(line)
    if not first:
        return False
    bare = strip_points(first)
    if not bare or bare[0] != LAMED or len(bare) < 4:
        return False
    teamim_stripped = strip_teamim_only(first)
    if len(teamim_stripped) < 2:
        return False
    # Infinitive-construct with ל almost always has shewa under the ל
    # (לִשְׁמֹר etc., shewa or hiriq).  This is partial — purpose-infinitive
    # is morphologically distinct from prep+noun by the bound-form pattern of
    # the verb root.  We approximate: ל + shewa + 3-consonant skeleton ending
    # in a holam-bearing C₂ (qal lamed-pattern).  If unsure → return False
    # (we'd rather emit and let editor judge than skip a real candidate).
    if teamim_stripped[1] != SHEVA:
        return False
    # Look for a holam in the rest of the token (qal infinitive C₁əC₂oC₃)
    if HOLAM in teamim_stripped[2:]:
        return True
    return False


# ---------------------------------------------------------------------------
# Participial morphology heuristic
# ---------------------------------------------------------------------------

# Participles in derived stems (Pi'el, Pu'al, Hifil, Hofal, Hitpael) all begin
# with a מ prefix.  Qal active participle (CoCeC) does NOT begin with מ — its
# distinctive feature is HOLAM under the first root consonant.  Qal passive
# participle (CaCuC) features QAMATS under C1 + QUBUTS or shuruq between C2/C3.
#
# Discipline: we want the participial signature WITHOUT consulting te'amim.
# Niqqud is allowed (per spec — niqqud ≠ te'amim).  Niqqud range U+05B0–U+05BC.

def looks_like_participle(token: str) -> bool:
    """Heuristic: does this token bear participial morphology?

    Three patterns:
      1. M-prefix participles: token starts with מ + (shewa/patah/qamats/qubuts) +
         consonant (Pi'el meCaCeC, Pu'al meCuCaC, Hifil maCCiC, Hofal muCCaC,
         Hitpael mitCaCeC).
      2. Qal active participle: CoCeC — first consonant carries HOLAM, third
         consonant carries TSERE or SEGOL.
      3. Qal passive participle: CaCuC — first consonant carries QAMATS,
         middle consonant carries QUBUTS/SHURUQ-mark, third bare.
    """
    if not token:
        return False
    bare = strip_points(token)
    teamim_stripped = strip_teamim_only(token)
    if len(bare) < 2:
        return False

    # ---- Pattern 1: M-prefix participle ----
    if bare[0] == MEM and len(bare) >= 3:
        # Reject the very common מ-initial closed-class words and frequent
        # nouns that share the m-prefix shape but are NOT participles.
        # Strip leading maqqef-bound first segment for membership tests.
        head_segment = bare.split(MAQQEF, 1)[0] if MAQQEF in bare else bare
        NOT_PARTICIPLE_M_HEADS = {
            # Closed-class
            "מן", "מי", "מה", "מאד", "מאז", "מתי", "מבלי", "מאין",
            # Common m-prefix nouns
            "מים", "מות", "מאה", "מקום", "מלך", "מלכים", "מצרים", "מואב",
            "משה", "מרים", "מצוה", "מצות", "מנחה", "מזבח", "מצרי", "מדבר",
            "משכן", "מסלה", "מפלה", "מטה", "מנשה", "מנוחה", "מספר",
            "משפחה", "משפט", "משפטים", "מעשה", "מעשי", "מקנה", "מצרף",
            "מחנה", "מחוז", "מבוא", "מערב", "מזרח", "מלאך", "מלאכי",
            "מולדת", "מאכל", "מתנה", "מחשבת", "מחשבה",
        }
        if head_segment in NOT_PARTICIPLE_M_HEADS or bare in NOT_PARTICIPLE_M_HEADS:
            return False
        # Look at the vowel under the prefix מ
        if len(teamim_stripped) >= 2:
            v = teamim_stripped[1]
            # Pi'el meCaCeC: shewa under מ (most common)
            # Hifil maCCiC: patah under מ
            # Hofal muCCaC: qubuts under מ
            # Hitpael mitCaCeC: hiriq under מ + tav as second consonant
            # Qal participles do NOT take מ-prefix.
            if v in (SHEVA, PATAH, QAMATS, QUBUTS, HIRIQ):
                return True

    # ---- Pattern 2: Qal active participle CoCeC ----
    # First consonant carries HOLAM.  E.g., רֹעֶה (shepherd), הֹלֵךְ (going),
    # שֹׁמֵר (keeping), אֹמֵר (saying), כֹּתֵב (writing).
    # Must check that the holam is on the FIRST consonant.  After te'amim strip,
    # token[0] is the first consonant; token[1] should be HOLAM (or SIN/SHIN dot
    # then HOLAM at token[2]).
    if len(teamim_stripped) >= 2:
        # Skip past possible sin/shin dot and dagesh
        idx = 1
        # Skip dagesh on first letter
        if idx < len(teamim_stripped) and teamim_stripped[idx] == DAGESH:
            idx += 1
        # Skip sin/shin dot
        if idx < len(teamim_stripped) and teamim_stripped[idx] in ("ׁ", "ׂ"):
            idx += 1
        if idx < len(teamim_stripped) and teamim_stripped[idx] == HOLAM:
            # Looks like first-consonant-holam pattern.  Verify length ≥ 3
            # consonants (CoCeC needs 3 root consonants).
            if len(bare) >= 3:
                # Reject some common holam-initial nouns.
                if bare in ("יום", "אור", "כל", "טוב", "קדש", "ראש", "מות", "כהן",
                            "אהל", "אהלי", "אחד", "אזן", "אשר", "כתב"):
                    return False
                return True

    # ---- Pattern 3: Qal passive participle CaCuC ----
    # First consonant qamats, third consonant qubuts or shuruq.
    # We check token[1] == QAMATS AND QUBUTS appears somewhere later.
    if len(teamim_stripped) >= 4 and teamim_stripped[1] == QAMATS:
        if QUBUTS in teamim_stripped[2:]:
            # Reject "כל" (all) and other non-participle qamats-initial nouns.
            if bare in ("ארץ", "אדם", "דבר", "בא", "אב", "אם", "אח", "כל"):
                return False
            return True

    return False


def starts_with_participle(line: str) -> bool:
    first = first_content_token(line)
    if not first:
        return False
    return looks_like_participle(first)


# ---------------------------------------------------------------------------
# H4 vocative heuristic
# ---------------------------------------------------------------------------

ADDRESS_PARTICLES = {"הוי", "אוי", "אהה", "אנא"}  # bare consonant skeletons
DIVINE_VOCATIVE_TAILS = {"יהוה", "יה", "אלהים", "אדני"}


def line_is_vocative(line: str) -> bool:
    """Heuristic: is `line` plausibly a vocative unit?

    Two patterns:
      (a) Line begins with an address particle (הוֹי, אוֹי, אֲהָהּ, אָנָּא).
      (b) Line is short (≤3 words) and ends in a divine name AND shows a
          vocative marker — either a 2nd-person pronoun, a 2nd-person
          possessive suffix, or some other direct-address signal.  Without
          such a marker the divine name is almost certainly part of a
          construct-chain subject (רוּחַ אֱלֹהִים, יִרְאַת יְהוָה),
          NOT a vocative.
    """
    toks = content_tokens(line)
    if not toks:
        return False
    bares = [strip_points(t) for t in toks]
    if bares[0] in ADDRESS_PARTICLES:
        return True
    # Short line ending in divine name — additional vocative-signal required.
    if (len(bares) <= 3
            and bares[-1] in DIVINE_VOCATIVE_TAILS
            and not line_has_finite_verb(line)):
        # Look for direct-address markers anywhere on the line:
        # - 2nd-person pronouns: אתה / את / אתם / אתן
        # - 2nd-person possessive suffix: token ends in ך (kaph), ך־, ֶיךָ, etc.
        DIRECT_ADDRESS_PRONOUNS = {"אתה", "את", "אתם", "אתן"}
        for b in bares:
            if b in DIRECT_ADDRESS_PRONOUNS:
                return True
            # 2nd-person suffix ending in ך (preserved after stripping points)
            stripped = b.rstrip(SOF_PASUQ)
            if stripped.endswith("ך") and len(stripped) >= 2:
                return True
        return False
    return False


# ---------------------------------------------------------------------------
# H14 discourse particles
# ---------------------------------------------------------------------------

DISCOURSE_PARTICLE_HEADS = {
    "הנה", "אף", "לכן", "ועתה", "אז", "עתה",
}
# על־כן needs to be checked as compound
COMPOUND_DISCOURSE_HEADS = {("על", "כן")}


def starts_with_discourse_particle(line: str) -> bool:
    first = first_content_token(line)
    if not first:
        return False
    bare = strip_points(first)
    if bare in DISCOURSE_PARTICLE_HEADS:
        return True
    # Compound על־כן
    if MAQQEF in bare:
        parts = bare.split(MAQQEF)
        if len(parts) >= 2 and (parts[0], parts[1]) in COMPOUND_DISCOURSE_HEADS:
            return True
    return False


# ---------------------------------------------------------------------------
# H15 casus pendens — line-after-candidate-second contains 3rd-person suffix
# ---------------------------------------------------------------------------

# 3rd-person pronominal suffix consonant patterns (after stripping vowels):
#   ו   — 3ms (-o, -aw)
#   הו  — 3ms (-ehu)
#   ה   — 3fs (-ah) — overlaps with locative-he and root, conservative match
#   ם   — 3mp (-am) when at word end on a suffix-bearing host
#   הם  — 3mp (-hem)
#   ן   — 3fp
#   הן  — 3fp
SUFFIX_CONSONANT_TAILS_3P = ("הו", "הם", "הן")


def line_has_3p_pronominal_suffix(line: str) -> bool:
    """Approximation: any content token ends with a 3p pronominal suffix pattern.

    Conservative match — only the unambiguous הו / הם / הן suffix endings (which
    all begin with ה, a clearer pronominal marker than the bare letter
    ם/ן which collide with the masculine/feminine plural noun ending -ים/-ין).
    The naked-letter check would over-fire on every plural noun (e.g.,
    אֱלֹהִים, שָׁמַיִם), making the H15 guard skip almost everything.
    """
    for tok in content_tokens(line):
        bare = strip_points(tok).rstrip(SOF_PASUQ)
        if not bare:
            continue
        if len(bare) < 3:
            continue
        # Multi-letter ה-initial pronominal suffixes (3ms הו, 3mp הם, 3fp הן)
        for tail in SUFFIX_CONSONANT_TAILS_3P:
            if bare.endswith(tail):
                return True
    return False


# ---------------------------------------------------------------------------
# H16 wayehi protasis open
# ---------------------------------------------------------------------------

WAYEHI_SKELETON = "ויהי"
LEEMOR_SKELETON = "לאמר"


def verse_is_wayehi_with_open_protasis(verse_lines: list[str], next_line_idx_in_verse: int) -> bool:
    """Returns True if the verse begins with וַיְהִי and לֵאמֹר has not yet appeared.

    `verse_lines` is the list of content lines belonging to the current verse.
    `next_line_idx_in_verse` is the index of the candidate-second line within
    that list (0-based).
    """
    if not verse_lines:
        return False
    first_tok = first_content_token(verse_lines[0])
    if not first_tok:
        return False
    if strip_points(first_tok) != WAYEHI_SKELETON:
        return False
    # Check whether לֵאמֹר has already appeared in the verse up through the
    # candidate-second line.
    for k in range(0, min(next_line_idx_in_verse + 1, len(verse_lines))):
        for tok in content_tokens(verse_lines[k]):
            if strip_points(tok) == LEEMOR_SKELETON:
                return False
    return True


# ---------------------------------------------------------------------------
# M3 bare-governing participle — next line is JUST a participle, no complement
# ---------------------------------------------------------------------------

def line_is_bare_participle(line: str) -> bool:
    """True if `line` is a single bare participle (no complement on this line)."""
    toks = content_tokens(line)
    if not toks:
        return False
    if not looks_like_participle(toks[0]):
        return False
    # Single-token line, OR all tokens are maqqef-bound clitics on the participle
    if len(toks) == 1:
        return True
    # If the participle token itself contains maqqef (ie. it's bound to another
    # word as a single prosodic unit), and the line has only that one token, OK.
    # If there are extra tokens, the participle has a complement → NOT bare.
    return False


def participle_has_following_complement(
    lines: list[str],
    verse_indices: list[int],
    bare_participle_pos: int,
) -> bool:
    """True if the bare participle on the line at `bare_participle_pos` (within
    the verse's content-line indices) has its PP-complement on the immediately
    following content line of the same verse.

    M3 says a bare governing participle "cannot stand on its own line without at
    least one complement."  When the complement IS available on the next line,
    the proper merge is (participle + complement), and the (subject + bare
    participle) split should NOT be skipped — surfacing it as a candidate gives
    the editor the chance to merge all three lines into one verbless-with-
    participial-predicate colon (canon §5 H18.2 example: וְרוּחַ אֱלֹהִים
    מְרַחֶפֶת // עַל־פְּנֵי הַמָּיִם).
    """
    if bare_participle_pos + 1 >= len(verse_indices):
        return False
    next_idx = verse_indices[bare_participle_pos + 1]
    next_line = lines[next_idx]
    is_prep, _ = starts_with_prep(next_line)
    if is_prep and not line_has_finite_verb(next_line):
        return True
    return False


# ---------------------------------------------------------------------------
# Heavy subject heuristic (forced-no-merge guard 7)
# ---------------------------------------------------------------------------

RELATIVE_SKELETONS = {"אשר"}
INTERROGATIVE_SKELETONS = {"מי", "מה"}


def line_has_heavy_subject(line: str) -> bool:
    bares = [strip_points(t) for t in content_tokens(line)]
    if not bares:
        return False
    # אשר / מי / מה anywhere
    for b in bares:
        if b in RELATIVE_SKELETONS:
            return True
        if b in INTERROGATIVE_SKELETONS:
            return True
        # שֶׁ- prefix (relative): bare token starts with ש followed by content
        # Stripped form: שX where X is a verb.  Conservative match: begin with
        # ש and length >= 4 AND the token isn't a known noun head.
        # Risk: too many false positives. Skip this one.

    # ≥2 בן/בת appositives
    bn_count = sum(1 for b in bares if b in ("בן", "בת"))
    if bn_count >= 2:
        return True

    # Construct chain ≥3 deep — heuristic via maqqef-joined tokens with construct
    # noun heads.  We approximate: ≥3 consecutive content tokens that look like
    # bound-form nouns (carry tsere/segol patterns).  Cheap proxy: the token
    # itself has 3+ maqqef-joined components.
    for tok in content_tokens(line):
        bare = strip_points(tok)
        if bare.count(MAQQEF) >= 2:
            return True

    return False


# ---------------------------------------------------------------------------
# Heavy participial complement (forced-no-merge guard 8)
# ---------------------------------------------------------------------------

def line_has_heavy_participial_complement(line: str) -> bool:
    """True if next line's participle has DO (אֵת) AND PP, combined ≥5 prosodic words."""
    toks = content_tokens(line)
    if len(toks) < 5:
        return False
    if not looks_like_participle(toks[0]):
        return False
    bares = [strip_points(t) for t in toks]
    has_do = any(
        b == "את" or b.startswith("את" + MAQQEF) or b == "אתי" or b == "אתו"
        for b in bares
    )
    has_pp, _ = starts_with_prep(" ".join(toks[1:]))
    if has_do and has_pp:
        return True
    return False


# ---------------------------------------------------------------------------
# H18.3 — verb_pp_complement_split: small explicit verb-skeleton list
# ---------------------------------------------------------------------------

# Verbs that govern an obligatory PP-complement.  Surface form (consonant
# skeleton AFTER stripping points).  We keep this list conservative and small
# per the spec ("start with a small explicit verb-skeleton list of high-
# confidence cases").  Each entry pairs a verb skeleton with the prep that
# governs its complement.
M2_PP_VERBS = {
    # שָׁמַע ל / אֶל
    "שמע":  ("ל", "אל"),
    "שמעו": ("ל", "אל"),
    "ישמע": ("ל", "אל"),
    "וישמע": ("ל", "אל"),
    # נָשָׂא ... אֶל (raise eyes/voice to)
    "נשא":  ("אל",),
    "נשאו": ("אל",),
    "וישא": ("אל",),
    "ישא":  ("אל",),
    # פָּנָה אֶל
    "פנה":  ("אל",),
    "פנו":  ("אל",),
    "ויפן": ("אל",),
    # קָרָא אֶל / ל
    "קרא":  ("אל", "ל"),
    "קראו": ("אל", "ל"),
    "ויקרא": ("אל", "ל"),
    # זָעַק אֶל
    "זעק":  ("אל",),
    "זעקו": ("אל",),
    "ויזעק": ("אל",),
    # פָּלַל אֶל
    "התפלל": ("אל",),
    "ויתפלל": ("אל",),
}


def line_ends_with_m2_verb(line: str) -> tuple[bool, str | None, tuple]:
    """Returns (True, verb_skeleton, allowed_preps) if last content token is an M2-class verb."""
    last = last_content_token(line)
    if not last:
        return False, None, ()
    bare = strip_points(last).rstrip(SOF_PASUQ)
    if bare in M2_PP_VERBS:
        return True, bare, M2_PP_VERBS[bare]
    return False, None, ()


# ---------------------------------------------------------------------------
# Verse partitioning
# ---------------------------------------------------------------------------

def partition_into_verses(lines: list[str]) -> list[tuple[int | None, int | None, list[int]]]:
    """Group line indices by verse.

    Returns a list of (chapter, verse, [line_indices]) tuples in source order.
    Verse-reference lines themselves are included as part of their verse but
    are skippable for content scanning.
    """
    verses: list[tuple[int | None, int | None, list[int]]] = []
    cur_chapter: int | None = None
    cur_verse: int | None = None
    cur_indices: list[int] = []
    for i, line in enumerate(lines):
        ref = parse_verse_ref(line)
        if ref is not None:
            # Flush current
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
# Te'amim annotation helper (informational only — NOT in trigger predicates)
# ---------------------------------------------------------------------------

# Common te'amim by Unicode codepoint, used ONLY for annotation strings.
# This dict is referenced solely from the annotation builder; trigger logic
# never imports or compares against te'amim.
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
    """Return a short informational summary of te'amim names present on `line`.

    INFORMATIONAL ONLY — never consulted by trigger predicates.
    """
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
    findings: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    book = book_name_from_path(path)
    chapter_from_file = chapter_from_path(path)
    verses = partition_into_verses(lines)

    # Build a lookup: line_index → (chapter, verse, position_within_verse)
    line_to_verse: dict[int, tuple[int | None, int | None, int, list[int]]] = {}
    for ch, vs, indices in verses:
        for pos, idx in enumerate(indices):
            line_to_verse[idx] = (ch, vs, pos, indices)

    # ── TAHOT morph alignment ────────────────────────────────────────────
    # Load once per chapter file; None when v0/morph is missing (graceful fallback).
    chapter_morph = MA.load_chapter_morph(path)

    # Build per-line-index token-tag mapping:
    #   line_token_tags[line_idx] = list[list[str]]  (one entry per content token)
    # Used by line_has_finite_verb_tagged to pass tag_list per token.
    line_token_tags: dict[int, list[list[str]]] = {}
    if chapter_morph is not None:
        for _ch, vs, indices in verses:
            if vs is None:
                continue
            ortho_tags = chapter_morph.get(vs)
            if ortho_tags is None:
                continue
            verse_lines = [lines[idx] for idx in indices]
            aligned = MA.align_verse_tokens_to_tags(verse_lines, ortho_tags)
            if aligned is None:
                continue  # alignment mismatch — leave these lines without tags
            for pos, idx in enumerate(indices):
                if pos < len(aligned):
                    line_token_tags[idx] = aligned[pos]
    # ─────────────────────────────────────────────────────────────────────

    # ── Macula IR alignment (post-2026-05-05 Wave C) ─────────────────────
    # Build per-line-index IR-token mapping alongside line_token_tags:
    #   line_ir_tokens[line_idx] = list[MC.Token]
    # IR-driven helpers take precedence over heuristic ones when the line
    # has IR tokens; legacy helpers serve as fallback otherwise.
    line_ir_tokens: dict[int, list["MC.Token"]] = {}
    chap_match = re.search(r"-(\d+)\.txt$", path.name, re.IGNORECASE)
    chap_int = int(chap_match.group(1)) if chap_match else None
    if chap_int is not None:
        for _ch, vs, indices in verses:
            if vs is None:
                continue
            try:
                verse_tokens = MC.get_verse_tokens(book, chap_int, vs)
            except (FileNotFoundError, ValueError, KeyError):
                continue
            if not verse_tokens:
                continue
            cursor = 0
            for idx in indices:
                if is_skippable(lines[idx]):
                    continue
                matched, cursor = MC.match_sense_line_tokens(
                    verse_tokens, lines[idx], start_idx=cursor)
                line_ir_tokens[idx] = matched
    # ─────────────────────────────────────────────────────────────────────

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        # Determine verse context
        v_ctx = line_to_verse.get(i)
        chapter = v_ctx[0] if v_ctx else chapter_from_file
        verse = v_ctx[1] if v_ctx else None
        pos_in_verse = v_ctx[2] if v_ctx else 0
        verse_indices = v_ctx[3] if v_ctx else []

        line_no = i + 1  # 1-based

        # --- Find next content line in the SAME verse (no cross-verse fire) ---
        next_idx: int | None = None
        for j in range(i + 1, len(lines)):
            if is_skippable(lines[j]):
                continue
            # Same verse?
            n_ctx = line_to_verse.get(j)
            if v_ctx and n_ctx and (n_ctx[0], n_ctx[1]) != (v_ctx[0], v_ctx[1]):
                break
            next_idx = j
            break
        if next_idx is None:
            continue
        next_line = lines[next_idx]
        next_line_no = next_idx + 1

        # --- Guard 1: poetic register ---
        if chapter is not None and is_poetic_register(book, chapter, verse):
            continue

        # IR token slices for line and next_line (post-2026-05-05 Wave C).
        ir_line = line_ir_tokens.get(i, [])
        ir_next = line_ir_tokens.get(next_idx, [])

        # --- Guard 9: both lines have a finite verb anywhere ---
        # IR-driven when alignment is available; heuristic fallback otherwise.
        if ir_line:
            prior_has_verb = line_has_finite_verb_ir(ir_line)
        else:
            prior_has_verb = line_has_finite_verb_tagged(
                line, token_tags=line_token_tags.get(i)
            )
        if ir_next:
            next_has_verb = line_has_finite_verb_ir(ir_next)
        else:
            next_has_verb = line_has_finite_verb_tagged(
                next_line, token_tags=line_token_tags.get(next_idx)
            )
        if prior_has_verb and next_has_verb:
            continue

        # --- Guard 11: combined > 8 prosodic words ---
        combined_words = prosodic_word_count(line) + prosodic_word_count(next_line)
        if combined_words > 8:
            continue

        # --- Guard 10: next-line prep takes ל + infinitive ---
        if ir_next:
            if starts_with_le_infinitive_ir(ir_next):
                continue
        else:
            if starts_with_le_infinitive(next_line):
                continue

        # --- Guard 2: H4 vocative position (prior line is vocative unit) ---
        # Vocative is editorial/contextual — IR doesn't expose; keep heuristic.
        if line_is_vocative(line):
            continue

        # --- Guard 3: H14 discourse particle on next line ---
        # Discourse-particle detection is closed-list lemma matching; the
        # existing skel-helper is precise enough.
        if starts_with_discourse_particle(next_line):
            continue

        # --- Guard 5: H16 FEF wayehi protasis open ---
        if v_ctx is not None:
            if verse and chap_int is not None:
                if verse_is_wayehi_with_open_protasis_ir(
                    book, chap_int, verse, pos_in_verse + 1,
                    [lines[idx] for idx in verse_indices],
                ):
                    continue
            else:
                verse_content_lines = [lines[idx] for idx in verse_indices]
                if verse_is_wayehi_with_open_protasis(verse_content_lines, pos_in_verse + 1):
                    continue

        # --- Guard 7: heavy subject on prior line ---
        if line_has_heavy_subject(line):
            continue

        # --- Determine subcase ---
        if ir_next:
            next_is_prep, prep_skel = starts_with_prep_ir(ir_next)
            next_is_part = starts_with_participle_ir(ir_next)
        else:
            next_is_prep, prep_skel = starts_with_prep(next_line)
            next_is_part = starts_with_participle(next_line)

        subcase: str | None = None
        verb_root: str | None = None

        if not prior_has_verb:
            if next_is_prep and not next_has_verb:
                subcase = "verbless_subj_pred_split"
            elif next_is_part:
                # Guard 6: M3 bare-governing participle.
                # Skip ONLY if the next line is a bare participle AND lacks a
                # PP-complement on the line after it.  When the complement IS
                # available on the line after, the participle is not "M3 bare-
                # governing in isolation" — it has a complement; surface the
                # finding so the editor can merge subject+participle+complement.
                if line_is_bare_participle(next_line):
                    next_pos_in_verse = pos_in_verse + 1
                    if not participle_has_following_complement(
                        lines, verse_indices, next_pos_in_verse
                    ):
                        continue
                # Guard 8: heavy participial complement
                if line_has_heavy_participial_complement(next_line):
                    continue
                subcase = "participial_pred_split"
        else:
            # Prior line has a finite verb: check for H18.3 verb_pp_complement_split.
            is_m2, vroot, allowed_preps = line_ends_with_m2_verb(line)
            if is_m2 and next_is_prep and not next_has_verb:
                # Verify that the prep is one of the allowed preps for this verb
                if prep_skel in allowed_preps:
                    subcase = "verb_pp_complement_split"
                    verb_root = vroot

        if subcase is None:
            continue

        # --- Guard 4: H15 casus pendens on line AFTER candidate-second ---
        # Look for next-but-one content line within the same verse.
        nb1_idx: int | None = None
        for k in range(next_idx + 1, len(lines)):
            if is_skippable(lines[k]):
                continue
            n2_ctx = line_to_verse.get(k)
            if v_ctx and n2_ctx and (n2_ctx[0], n2_ctx[1]) != (v_ctx[0], v_ctx[1]):
                break
            nb1_idx = k
            break
        if nb1_idx is not None:
            ir_nb1 = line_ir_tokens.get(nb1_idx, [])
            if ir_nb1:
                if line_has_3p_pronominal_suffix_ir(ir_nb1):
                    continue
            else:
                if line_has_3p_pronominal_suffix(lines[nb1_idx]):
                    continue

        # --- All guards passed; emit REVIEW-REQUIRED finding ---
        prior_text = line.strip()
        next_text = next_line.strip()

        prior_teamim = teamim_summary(line)
        next_teamim = teamim_summary(next_line)
        teamim_note = ""
        if prior_teamim or next_teamim:
            teamim_note = (
                f" Te'amim placement: {prior_teamim or '(none)'} on prior line, "
                f"{next_teamim or '(none)'} on next line — informational only."
            )

        if subcase == "verbless_subj_pred_split":
            annotation = (
                "Verbless subject + locative/PP predicate (H18.1; JM §154; WO §8.4)."
                + teamim_note
            )
            suggested = "MERGE candidate per H18.1"
            brief = (
                f"verbless subject + PP predicate — {prior_text} // {next_text} "
                f"({combined_words} prosodic words combined)"
            )
        elif subcase == "participial_pred_split":
            annotation = (
                "Subject + participial predicate (H18.2; JM §121; WO §37.6 — "
                "participle fills the slot of a finite verb)."
                + teamim_note
            )
            suggested = "MERGE candidate per H18.2"
            brief = (
                f"subject + participial predicate — {prior_text} // {next_text} "
                f"({combined_words} prosodic words combined)"
            )
        else:  # verb_pp_complement_split
            annotation = (
                f"Finite verb {verb_root!r} with obligatory PP-complement "
                "(H18.3 / M2 corpus extension)."
                + teamim_note
            )
            suggested = "MERGE candidate per H18.3"
            brief = (
                f"verb + obligatory PP-complement — {prior_text} // {next_text} "
                f"({combined_words} prosodic words combined)"
            )

        # H18.3 is promoted to STRONG-MERGE-CANDIDATE (YAML spec h18_3_verb_pp_complement.yaml);
        # H18.1 and H18.2 remain REVIEW-REQUIRED pending further adoption measurement.
        finding_severity = (
            "STRONG-MERGE-CANDIDATE" if subcase == "verb_pp_complement_split"
            else "REVIEW-REQUIRED"
        )

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "next_line_num": next_line_no,
            "rule": "H18/clause-nucleus-split",
            "severity": finding_severity,
            "subcase": subcase,
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "prior_line": prior_text,
            "next_line": next_text,
            "prosodic_word_count": combined_words,
            "annotation": annotation,
            "suggested_action": suggested,
            "brief": brief,
        })

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def resolve_book_dir(base_dir: Path, book_arg: str) -> Path:
    """Resolve a --book argument permissively (matches complement_integrity)."""
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
                "rule": f["rule"],
                "severity": f["severity"],
                "subcase": f["subcase"],
                "book": f["book"],
                "chapter": f["chapter"],
                "verse": f["verse"],
                "prior_line": f["prior_line"],
                "next_line": f["next_line"],
                "next_line_num": f["next_line_num"],
                "prosodic_word_count": f["prosodic_word_count"],
                "annotation": f["annotation"],
                "suggested_action": f["suggested_action"],
            })

        counts = {"REVIEW-REQUIRED": 0, "STRONG-MERGE-CANDIDATE": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        by_subcase: dict[str, int] = {}
        for f in findings_json:
            by_subcase[f["subcase"]] = by_subcase.get(f["subcase"], 0) + 1

        doc = {
            "validator": "validate_clause_nucleus_split",
            "rule": "H18",
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
                "by_subcase": by_subcase,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output ---
    print("=" * 72)
    print(f"Rule H18 Clause-Nucleus Integrity validator — Tanakh {tier_label}")
    print(f"Reference: canon §5 H18 (verbless / participial / verb-PP predication)")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Findings      : {len(all_findings)}")

    by_subcase: dict[str, int] = {}
    for f in all_findings:
        by_subcase[f["subcase"]] = by_subcase.get(f["subcase"], 0) + 1
    if by_subcase:
        print()
        for sub, count in sorted(by_subcase.items()):
            print(f"  {sub}: {count}")
    print()

    if all_findings:
        for f in all_findings:
            print(
                f"[DEVIATION]  {f['file_rel']}:{f['line_num']}  "
                f"{f['rule']}  {f['severity']}  {f['subcase']}  {f['brief']}"
            )
            if args.verbose:
                print(f"    {f['prior_line'][:120]}")
                print(f"    → {f['next_line'][:120]}")
                print(f"    {f['annotation']}")
                print()
    else:
        print("No findings. Rule H18 clause-nucleus integrity is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
