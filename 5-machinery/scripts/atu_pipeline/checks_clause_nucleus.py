#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""checks_clause_nucleus.py — Constraint Catalog v1 checks for the clause-nucleus cluster.

Implements 6 check functions for audit_constraints.py:

  JM125-verb-object-bond        Verb-DO nucleus bond (BIND, HARD, prec 2)
  JM125-coordinated-objects     Coordinated DO integrity (BIND, HARD, prec 2)
  JM157-complement-integrity    Obligatory complement integrity (BIND, HARD, prec 2)
  JM154-verbless-clause-nucleus Verbless-clause nucleus integrity (BIND, HARD, prec 3)
  JM121-participial-predicate   Participial-predicate nucleus integrity (BIND, HARD, prec 3)
  JM133-verb-pp-complement      Verb-PP complement bond (BIND, HARD, prec 3)

Each check follows the signature required by audit_constraints.py:

    def check_<id>(
        verse_text: str,
        source_text: str,
        book_slug: str,
        chapter: int,
        verse_num: int,
    ) -> Optional[dict]:

The returned dict has keys:
    fires   (bool)
    verdict (str)  — CONFLICT | CORROBORATE | ADVISORY | NO-EFFECT
    reason  (str)
    details (dict)

Returns None when NOT-YET-IMPLEMENTED (signals the pipeline to skip).

Macula API used (all from 5-machinery/validators/_shared/macula_constituents.py):
    get_verse_tokens(book_slug, chapter, verse) -> list[Token]
    match_sense_line_tokens(verse_tokens, line_text, start_idx) -> (list[Token], int)
    Token.is_finite_verb, Token.is_participle, Token.is_active_participle,
    Token.is_passive_participle, Token.lemma, Token.role, Token.pos,
    Token.type_, Token.frame_args (dict[str, list[Token]]),
    Token.parent_constituent (Constituent | None)
    Constituent.is_pp, Constituent.is_clause, Constituent.wg_class

Macula API gaps documented inline where a catalog primitive is missing or
unconfirmed. Surface heuristics with caveat annotations are used in those cases.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Macula import — insert 5-machinery/validators/ onto sys.path so _shared resolves.
# audit_constraints.py does the same insertion; we duplicate defensively.
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT / "5-machinery/validators") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "5-machinery/validators"))

try:
    from _shared import macula_constituents as MC
    _MACULA_AVAILABLE = True
except ImportError:
    MC = None  # type: ignore[assignment]
    _MACULA_AVAILABLE = False


# ---------------------------------------------------------------------------
# Hebrew utilities
# ---------------------------------------------------------------------------

_HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")


def _strip(text: str) -> str:
    """Strip niqqud and te'amim; NFC-normalize."""
    return _HEBREW_POINTS_RE.sub("", unicodedata.normalize("NFC", text))


def _consonants(text: str) -> str:
    """Consonant skeleton of a Hebrew string (strips maqqef too)."""
    return _strip(text).replace("־", "").replace("׃", "").replace("׀", "")


def _sense_lines(verse_text: str) -> list[str]:
    """Non-blank sense-lines from verse_text."""
    return [ln for ln in verse_text.splitlines() if ln.strip()]


def _prosodic_word_count(line: str) -> int:
    """Count space-delimited tokens excluding sof-pasuq."""
    return sum(1 for t in line.split() if _strip(t) not in ("", "׃", "׀"))


# ---------------------------------------------------------------------------
# Macula IR helpers
# ---------------------------------------------------------------------------

def _load_verse_tokens(book_slug: str, chapter: int, verse_num: int) -> list:
    """Return verse token list; empty list on any failure."""
    if not _MACULA_AVAILABLE:
        return []
    try:
        tokens = MC.get_verse_tokens(book_slug, chapter, verse_num)
        return tokens or []
    except Exception:
        return []


def _align_lines(verse_tokens: list, lines: list[str]) -> dict[int, list]:
    """Align sense-lines to token slices. Returns {line_index: [Token]}."""
    result: dict[int, list] = {}
    cursor = 0
    for i, ln in enumerate(lines):
        matched, cursor = MC.match_sense_line_tokens(verse_tokens, ln, start_idx=cursor)
        result[i] = matched
    return result


# ---------------------------------------------------------------------------
# Closed lists
# ---------------------------------------------------------------------------

# JM157 — cognition/volition/causative verbs that take obligatory clausal complements
# (כִּי-clause or אֲשֶׁר-clause). Per JM §157.
#
# 2026-05-18 §7.3 retroactive audit on Catalog v1: removed אָמַר and נָגַד.
# Both are SPEECH verbs whose כִּי introduces direct speech (recitativum),
# not a cognition complement. They were causing spurious JM157 firings on
# narrative speech-frames (e.g., Gen 3:14 וַיֹּאמֶר ... כִּי). Routing to
# JM157-ki-recitativum is correct; OBLIGATORY_COMPLEMENT_VERBS is for the
# cognition / volition / causative classes only. JM125-verb-object-bond's
# _SPEECH_VERB_LEMMAS provides the parallel suppression on that side.
OBLIGATORY_COMPLEMENT_VERBS = frozenset({
    "יָדַע",   # know
    "רָאָה",   # see
    "שָׁמַע",  # hear
    "זָכַר",   # remember
    "בִּין",   # understand / discern
    "חָשַׁב",  # think / consider
    "צִוָּה",  # command
    "רָצָה",   # desire / want
    "חָפֵץ",   # delight in / want
    "בִּקֵּשׁ", # seek
    "גָּזַר",  # decree
    "שָׂמַח",  # rejoice (occasionally takes כִּי complement)
    "יָרֵא",   # fear (takes כִּי in complement slot)
})

# Consonant skeletons for OBLIGATORY_COMPLEMENT_VERBS — used by skel fallback.
# Mirrors the lemma-list removal of אמר and נגד above.
_OBL_COMP_SKEL = frozenset({
    "ידע", "ראה", "שמע", "זכר", "בין", "חשב",
    "צוה", "רצה", "חפץ", "בקש", "גזר", "שמח", "ירא",
})

# Complementizer lemmas that introduce obligatory clausal complements.
_COMPLEMENT_INTRODUCERS = frozenset({"כִּי", "אֲשֶׁר"})
_COMPLEMENT_SKEL = frozenset({"כי", "אשר"})

# JM133 — verb lemmas that require an obligatory PP complement, and the
# expected preposition lemma (or its consonant skeleton for fallback).
# Per JM §133 and validate_clause_nucleus_split.py H18.3.
OBLIGATORY_PP_VERBS: dict[str, str] = {
    "שָׁמַע": "לְ",    # hear-to / obey
    "פָּנָה": "אֶל",   # turn-toward
    "שׁוּב": "אֶל",   # return-to
    "בָּטַח": "בְּ",   # trust-in
    "חָטָא": "לְ",    # sin-against
    "דָּבַק": "בְּ",   # cling-to
    "אָמַן": "בְּ",   # trust-in / believe-in (hiphil הֶאֱמִין)
    "הִשְׁתַּחֲוָה": "לְ",  # bow-to
    "קִנֵּא": "בְּ",  # be-jealous-of
    "נִשְׁבַּע": "בְּ",  # swear-by
    "צָעַק": "אֶל",   # cry-out-to
    "קָרָא": "אֶל",   # call-to
}

# Skel versions of OBLIGATORY_PP_VERBS keys for fallback.
_OBL_PP_SKEL: dict[str, str] = {
    "שמע": "ל",
    "פנה": "אל",
    "שוב": "אל",
    "בטח": "ב",
    "חטא": "ל",
    "דבק": "ב",
    "אמן": "ב",
    "השתחוה": "ל",
    "קנא": "ב",
    "נשבע": "ב",
    "צעק": "אל",
    "קרא": "אל",
}

# Preposition consonant skeletons.
_PREP_SKEL_LE = {"ל", "לו", "לה", "לי", "לנו", "לכם", "לכן", "להם", "להן"}
_PREP_SKEL_EL = {"אל", "אליו", "אליה", "אלי", "אלינו", "אליכם", "אליהם"}
_PREP_SKEL_BE = {"ב", "בו", "בה", "בי", "בנו", "בכם", "בהם"}

# All expected PP preposition skeletons (union).
_ALL_PP_SKELS = _PREP_SKEL_LE | _PREP_SKEL_EL | _PREP_SKEL_BE | {"מן", "עם", "על", "מעל", "מן"}


# ---------------------------------------------------------------------------
# IR-based alignment helper
# ---------------------------------------------------------------------------

def _try_ir_alignment(
    book_slug: str,
    chapter: int,
    verse_num: int,
    lines: list[str],
) -> tuple[bool, dict[int, list]]:
    """Return (ir_ok, line_map) where line_map[i] = list[Token] for lines[i].

    ir_ok is False when Macula is unavailable or verse has no tokens.
    """
    verse_tokens = _load_verse_tokens(book_slug, chapter, verse_num)
    if not verse_tokens:
        return False, {}
    line_map = _align_lines(verse_tokens, lines)
    return True, line_map


# ---------------------------------------------------------------------------
# Surface-heuristic helpers (skel fallback)
# ---------------------------------------------------------------------------

def _last_skel_token(line: str) -> str:
    """Consonant skeleton of the last non-empty, non-sof-pasuq token on a line."""
    toks = [_consonants(t) for t in line.split() if _consonants(t) not in ("", "׃", "׀")]
    return toks[-1] if toks else ""


def _first_skel_token(line: str) -> str:
    """Consonant skeleton of the first non-empty token on a line."""
    for t in line.split():
        s = _consonants(t)
        if s and s not in ("׃", "׀"):
            return s
    return ""


def _line_has_finite_verb_token(tokens: list) -> bool:
    """True if any Macula Token on the line is a finite verb."""
    return any(t.is_finite_verb for t in tokens)


def _line_has_participle_token(tokens: list) -> bool:
    """True if any Macula Token on the line is a participle."""
    return any(t.is_participle for t in tokens)


def _tokens_on_n_plus_1(stranded: list, n_plus_1_ids: set) -> list:
    """Filter tokens to those whose xml_id falls on line N+1."""
    return [t for t in stranded if t.xml_id in n_plus_1_ids]


# ---------------------------------------------------------------------------
# JM125-verb-object-bond
# ---------------------------------------------------------------------------

def check_JM125_verb_object_bond(
    verse_text: str,
    source_text: str,
    book_slug: str,
    chapter: int,
    verse_num: int,
) -> Optional[dict]:
    """JM125-verb-object-bond — Verb-DO nucleus bond.

    Encoded question: Does a finite verb's nominal direct object (frame-arg A1)
    begin the next sense-line rather than appearing on the same line as the verb?

    Catalog spec: Token.frame_args["A1"] — if the finite verb token is on line N
    and any A1 token is on line N+1 = BIND CONFLICT.

    Edge-case handling:
    - Speech-verb A1 (לאמר / אמר class): suppressed — clausal A1 is H5b-licensed.
    - Clausal A1 (כי/אשר-introduced content clause): suppressed.
    - Coordinated-object enumeration (וְאֵת opening N+1): suppressed — covered by
      JM125-coordinated-objects.
    - Heavy-A1 guard (>8 prosodic words on N+1): downgraded to ADVISORY.

    Macula API used: Token.frame_args["A1"], Token.is_finite_verb, Token.lemma,
    Token.role, Token.pos.
    Fallback: skel heuristic (finite-verb skel on N + אֵת marker on N+1).
    """
    lines = _sense_lines(verse_text)
    if len(lines) < 2:
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "single-line verse — no cross-line bond possible", "details": {}}

    # --- Speech-verb lemmas to suppress (H5b) ---
    _SPEECH_VERB_LEMMAS = frozenset({
        "אָמַר", "דָּבַר", "קָרָא", "עָנָה", "צִוָּה",
        "סִפֵּר", "נָגַד", "שָׁאַל", "צָעַק", "זָעַק",
    })

    # --- IR path ---
    ir_ok, line_map = _try_ir_alignment(book_slug, chapter, verse_num, lines)

    if ir_ok:
        for k in range(len(lines) - 1):
            n_tokens = line_map.get(k, [])
            n1_tokens = line_map.get(k + 1, [])
            if not n_tokens or not n1_tokens:
                continue
            n1_ids = {t.xml_id for t in n1_tokens}

            for verb in n_tokens:
                if not verb.is_finite_verb:
                    continue
                # Suppress speech verbs (H5b).
                if verb.lemma in _SPEECH_VERB_LEMMAS:
                    continue
                a1_tokens = verb.frame_args.get("A1") or []
                if not a1_tokens:
                    continue
                stranded = [t for t in a1_tokens if t.xml_id in n1_ids]
                if not stranded:
                    continue

                # Guard: clausal A1 (role="v" or complementizer-headed)
                if any(t.role == "v" for t in stranded):
                    continue

                # Guard: coordinated-object pattern (וְאֵת opening N+1)
                first_n1 = n1_tokens[0] if n1_tokens else None
                if first_n1 and first_n1.is_conjunction:
                    # Next non-conjunction token
                    for nt in n1_tokens[1:]:
                        if nt.lemma == "אֵת" and nt.is_particle:
                            # Coordinated DO — suppress, handled by JM125-coordinated-objects
                            stranded = []
                        break
                if not stranded:
                    continue

                # Heavy-A1 guard: N+1 has > 8 prosodic words
                n1_weight = _prosodic_word_count(lines[k + 1])
                if n1_weight > 8:
                    return {
                        "fires": True,
                        "verdict": "ADVISORY",
                        "reason": (
                            f"finite verb {verb.text!r} A1 stranded on next line "
                            f"(heavy DO >{8} words — editorial judgment required)"
                        ),
                        "details": {
                            "line_n": k + 1,
                            "verb": verb.text,
                            "a1_tokens": [t.text for t in stranded],
                            "n1_weight": n1_weight,
                        },
                    }

                return {
                    "fires": True,
                    "verdict": "CONFLICT",
                    "reason": (
                        f"finite verb {verb.text!r} frame-arg A1 "
                        f"{[t.text for t in stranded]!r} stranded on line {k + 2}"
                    ),
                    "details": {
                        "line_n": k + 1,
                        "line_n_plus_1": k + 2,
                        "verb": verb.text,
                        "a1_tokens": [t.text for t in stranded],
                    },
                }
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "IR: no verb-A1 stranding detected", "details": {}}

    # --- Skel fallback ---
    # Heuristic: finite-verb-like skel on N + אֵת-marker on N+1.
    # Caveat: cannot disambiguate אֵת (DO marker) from אַתְּ (2fs pronoun).
    _WAYYIQTOL_PFXS = ("וי", "ות", "וא", "ונ")

    def _skel_looks_finite(skel: str) -> bool:
        if not skel:
            return False
        for pfx in _WAYYIQTOL_PFXS:
            if skel.startswith(pfx) and len(skel) >= 4 and skel != "ויהוה":
                return True
        return False

    for k in range(len(lines) - 1):
        last_n = _last_skel_token(lines[k])
        if not _skel_looks_finite(last_n):
            # Also check all tokens on the line
            all_n_skels = [_consonants(t) for t in lines[k].split()]
            if not any(_skel_looks_finite(s) for s in all_n_skels):
                continue
        first_n1 = _first_skel_token(lines[k + 1])
        if first_n1 == "את" or first_n1.startswith("את"):
            return {
                "fires": True,
                "verdict": "CONFLICT",
                "reason": (
                    "[skel-fallback] finite-verb-like token on line N + "
                    f"אֵת marker opening line {k + 2} — possible verb-A1 stranding"
                ),
                "details": {
                    "line_n": k + 1,
                    "line_n_plus_1": k + 2,
                    "caveat": "skel fallback: אֵת/אַתְּ disambiguation not possible without IR",
                },
            }
    return {"fires": False, "verdict": "NO-EFFECT",
            "reason": "skel fallback: no verb-A1 stranding detected", "details": {}}


# ---------------------------------------------------------------------------
# JM125-coordinated-objects
# ---------------------------------------------------------------------------

def check_JM125_coordinated_objects(
    verse_text: str,
    source_text: str,
    book_slug: str,
    chapter: int,
    verse_num: int,
) -> Optional[dict]:
    """JM125-coordinated-objects — Coordinated DO integrity.

    Encoded question: When a single verb governs multiple coordinated A1 direct
    objects, are those A1 tokens distributed across distinct sense-lines?

    Catalog spec: Token.frame_args["A1"] returns multiple tokens. If A1 tokens
    span two or more distinct sense-lines = BIND CONFLICT.
    Guard: combined token-weight of all A1 tokens <= 8 prosodic words.
    For >= 9 combined words, downgrade to ADVISORY (SJ1 series break licensed).
    For >= 3 members with formal markers, defer to SJ1 (ADVISORY).

    Macula API used: Token.frame_args["A1"] (multiple resolved tokens).
    Fallback: surface pattern — conjunction וְ + אֵת on next line after verb.

    Macula gap: multi-token A1 resolution depends on frame attribute encoding
    multiple IDs in the A1 slot. Confirmed available per parse_frame_str()
    in macula_constituents.py — but empirical A1 multi-token rate varies by corpus.
    """
    lines = _sense_lines(verse_text)
    if len(lines) < 2:
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "single-line verse", "details": {}}

    ir_ok, line_map = _try_ir_alignment(book_slug, chapter, verse_num, lines)

    if ir_ok:
        for k in range(len(lines) - 1):
            n_tokens = line_map.get(k, [])
            n1_tokens = line_map.get(k + 1, [])
            if not n_tokens or not n1_tokens:
                continue
            n1_ids = {t.xml_id for t in n1_tokens}
            # All token ids on line N
            n_ids = {t.xml_id for t in n_tokens}

            for verb in n_tokens:
                if not verb.is_finite_verb:
                    continue
                a1_tokens = verb.frame_args.get("A1") or []
                if len(a1_tokens) < 2:
                    # Single A1 — covered by JM125-verb-object-bond
                    continue

                on_n = [t for t in a1_tokens if t.xml_id in n_ids]
                on_n1 = [t for t in a1_tokens if t.xml_id in n1_ids]
                if not on_n or not on_n1:
                    continue  # All A1 on same line — no violation

                # Combined prosodic weight of all A1 tokens across both lines
                total_a1_text = " ".join(t.text for t in a1_tokens)
                combined_weight = len(a1_tokens)  # token count as proxy
                # Actual word weight: count unique prosodic words
                combined_prose_weight = _prosodic_word_count(
                    " ".join(t.text for t in a1_tokens)
                )

                # Heavy-DO: >= 9 prosodic words → ADVISORY (SJ1 may license)
                if combined_prose_weight >= 9:
                    return {
                        "fires": True,
                        "verdict": "ADVISORY",
                        "reason": (
                            f"verb {verb.text!r} has coordinated A1 split across "
                            f"lines {k+1}/{k+2} with combined weight "
                            f"{combined_prose_weight} >= 9 (SJ1 series break may be licensed)"
                        ),
                        "details": {
                            "line_n": k + 1,
                            "line_n_plus_1": k + 2,
                            "verb": verb.text,
                            "a1_on_n": [t.text for t in on_n],
                            "a1_on_n1": [t.text for t in on_n1],
                            "combined_weight": combined_prose_weight,
                        },
                    }

                return {
                    "fires": True,
                    "verdict": "CONFLICT",
                    "reason": (
                        f"verb {verb.text!r} has coordinated A1 tokens split across "
                        f"lines {k+1} and {k+2} (combined weight {combined_prose_weight} <= 8)"
                    ),
                    "details": {
                        "line_n": k + 1,
                        "line_n_plus_1": k + 2,
                        "verb": verb.text,
                        "a1_on_n": [t.text for t in on_n],
                        "a1_on_n1": [t.text for t in on_n1],
                    },
                }
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "IR: no coordinated-object stranding", "details": {}}

    # --- Skel fallback ---
    # Pattern: line N has finite-verb-like token, line N+1 begins with וְאֵת or
    # וְ immediately followed by object — and line N already had an אֵת object.
    # Caveat: This is a weak heuristic — cannot confirm same-verb governance.
    for k in range(len(lines) - 1):
        n_skel_tokens = [_consonants(t) for t in lines[k].split() if _consonants(t)]
        n1_first = _first_skel_token(lines[k + 1])
        n1_second = ""
        n1_parts = [_consonants(t) for t in lines[k + 1].split() if _consonants(t)]
        if len(n1_parts) >= 2:
            n1_second = n1_parts[1]

        # N has את (object) AND N+1 begins with וְ + את pattern
        if "את" in n1_second and n1_first in ("ו", "ואת"):
            if any("את" in s for s in n_skel_tokens):
                return {
                    "fires": True,
                    "verdict": "CONFLICT",
                    "reason": (
                        f"[skel-fallback] line {k+1} has אֵת-object; "
                        f"line {k+2} opens with וְ+אֵת — possible coordinated-DO split"
                    ),
                    "details": {
                        "line_n": k + 1,
                        "line_n_plus_1": k + 2,
                        "caveat": "skel fallback: governance by same verb not confirmed",
                    },
                }
    return {"fires": False, "verdict": "NO-EFFECT",
            "reason": "skel fallback: no coordinated-DO stranding", "details": {}}


# ---------------------------------------------------------------------------
# JM157-complement-integrity
# ---------------------------------------------------------------------------

def check_JM157_complement_integrity(
    verse_text: str,
    source_text: str,
    book_slug: str,
    chapter: int,
    verse_num: int,
) -> Optional[dict]:
    """JM157-complement-integrity — Obligatory complement integrity.

    Encoded question: Does a cognition/volition/causative verb appear at
    line-end with its obligatory כִּי-clause or אֲשֶׁר-clause beginning the
    next line?

    Catalog spec: Token.lemma membership in OBLIGATORY_COMPLEMENT_VERBS;
    next-line opening token lemma in {"כִּי", "אֲשֶׁר"}.
    Guard: long-complement exception (>= 8 prosodic words on N+1) → ADVISORY.
    Guard: if next-line כִּי is causal (not complement), do not fire —
    distinguish by checking verb is NOT in OBLIGATORY_COMPLEMENT_VERBS context.

    Macula API used: Token.lemma, Token.is_finite_verb, Token.pos.
    Fallback: consonant-skeleton matching for verb + complementizer.

    Macula gap: A2 clausal-complement slot is available in frame_args but
    not consistently populated for all cognition verbs; lemma + next-line
    complementizer is the primary detection path.
    """
    lines = _sense_lines(verse_text)
    if len(lines) < 2:
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "single-line verse", "details": {}}

    ir_ok, line_map = _try_ir_alignment(book_slug, chapter, verse_num, lines)

    if ir_ok:
        for k in range(len(lines) - 1):
            n_tokens = line_map.get(k, [])
            n1_tokens = line_map.get(k + 1, [])
            if not n_tokens or not n1_tokens:
                continue

            # Find cognition/complement verb on line N
            comp_verb = None
            for t in n_tokens:
                if t.is_finite_verb and t.lemma in OBLIGATORY_COMPLEMENT_VERBS:
                    comp_verb = t
                    # Use last-occurring match (complement verb typically last on line)
            if comp_verb is None:
                continue

            # Check N+1 opens with כִּי or אֲשֶׁר
            opening_token = None
            for t in n1_tokens:
                if t.text.strip():
                    opening_token = t
                    break
            if opening_token is None:
                continue
            if opening_token.lemma not in _COMPLEMENT_INTRODUCERS:
                continue

            # Long-complement guard
            n1_weight = _prosodic_word_count(lines[k + 1])
            if n1_weight >= 8:
                return {
                    "fires": True,
                    "verdict": "ADVISORY",
                    "reason": (
                        f"complement verb {comp_verb.text!r} with "
                        f"{opening_token.text!r}-clause on next line "
                        f"(long complement {n1_weight} >= 8 words — may be licensed)"
                    ),
                    "details": {
                        "line_n": k + 1,
                        "line_n_plus_1": k + 2,
                        "verb": comp_verb.text,
                        "verb_lemma": comp_verb.lemma,
                        "complementizer": opening_token.text,
                        "n1_weight": n1_weight,
                    },
                }

            return {
                "fires": True,
                "verdict": "CONFLICT",
                "reason": (
                    f"complement verb {comp_verb.text!r} (lemma {comp_verb.lemma!r}) "
                    f"at line {k+1} with obligatory "
                    f"{opening_token.text!r}-clause beginning line {k+2} — "
                    "BIND: verb + complement must stay on same line"
                ),
                "details": {
                    "line_n": k + 1,
                    "line_n_plus_1": k + 2,
                    "verb": comp_verb.text,
                    "verb_lemma": comp_verb.lemma,
                    "complementizer": opening_token.text,
                },
            }
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "IR: no obligatory-complement stranding", "details": {}}

    # --- Skel fallback ---
    for k in range(len(lines) - 1):
        line_skels = [_consonants(t) for t in lines[k].split() if _consonants(t)]
        # Any token is an obligatory-complement verb skeleton?
        comp_verb_skel = next(
            (s for s in line_skels if s in _OBL_COMP_SKEL), None
        )
        if comp_verb_skel is None:
            continue
        # N+1 opens with כי or אשר
        n1_first = _first_skel_token(lines[k + 1])
        if n1_first not in _COMPLEMENT_SKEL:
            continue

        n1_weight = _prosodic_word_count(lines[k + 1])
        verdict = "ADVISORY" if n1_weight >= 8 else "CONFLICT"
        return {
            "fires": True,
            "verdict": verdict,
            "reason": (
                f"[skel-fallback] complement-verb skeleton {comp_verb_skel!r} "
                f"on line {k+1} + {n1_first!r}-clause on line {k+2}"
            ),
            "details": {
                "line_n": k + 1,
                "line_n_plus_1": k + 2,
                "verb_skel": comp_verb_skel,
                "complementizer_skel": n1_first,
                "n1_weight": n1_weight,
                "caveat": "skel fallback: lemma matching approximate",
            },
        }
    return {"fires": False, "verdict": "NO-EFFECT",
            "reason": "skel fallback: no complement stranding", "details": {}}


# ---------------------------------------------------------------------------
# JM154-verbless-clause-nucleus
# ---------------------------------------------------------------------------

def check_JM154_verbless_clause_nucleus(
    verse_text: str,
    source_text: str,
    book_slug: str,
    chapter: int,
    verse_num: int,
) -> Optional[dict]:
    """JM154-verbless-clause-nucleus — Verbless-clause nucleus integrity.

    Encoded question: Is the subject of a verbless clause on line N while
    the predicative PP or nominal predicate begins line N+1, splitting the
    verbless-clause nucleus?

    Catalog spec: line N ends with NP (no finite verb); line N+1 begins with
    wg_class="pp" or nominal predicate (role="p"). Both token sets within the
    same Macula wg_class="cl" constituent.

    Interaction: JM121-participial-predicate takes priority when N+1 opens
    with a participle — check Token.is_participle first; if True, skip here.

    Guard: heavy-predicate exception (>= 6 prosodic words on N+1) → ADVISORY.
    Guard: casus pendens (JM156) and discourse particle (JM155) take priority.

    Macula API used: Token.is_finite_verb, Token.is_participle, Token.role,
    Token.pos, Token.parent_constituent, Constituent.is_clause, Constituent.is_pp.

    Macula gap: detecting that N and N+1 tokens belong to the same Macula "cl"
    constituent is possible via Token.parent_constituent traversal, but the
    ancestor-clause matching is not always resolved across sense-line boundaries
    because sense-line alignment is post-parse. We use a proximity heuristic:
    if line N has no finite verb and N+1 begins with a PP or nominal-predicate
    token, flag as CONFLICT. The shared-clause check is best-effort via
    parent_constituent.is_clause ancestry.
    """
    lines = _sense_lines(verse_text)
    if len(lines) < 2:
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "single-line verse", "details": {}}

    ir_ok, line_map = _try_ir_alignment(book_slug, chapter, verse_num, lines)

    if ir_ok:
        for k in range(len(lines) - 1):
            n_tokens = line_map.get(k, [])
            n1_tokens = line_map.get(k + 1, [])
            if not n_tokens or not n1_tokens:
                continue

            # Line N: must have no finite verb (verbless clause candidate)
            if any(t.is_finite_verb for t in n_tokens):
                continue

            # JM121 takes priority: if N+1 opens with a participle, skip
            first_n1 = next((t for t in n1_tokens if t.text.strip()), None)
            if first_n1 and first_n1.is_participle:
                continue  # Handled by JM121-participial-predicate

            # N+1 must begin with a PP or nominal predicate
            # Macula: Token.parent_constituent.is_pp for PP check
            n1_is_pp = (
                first_n1 is not None and
                first_n1.parent_constituent is not None and
                first_n1.parent_constituent.is_pp
            )
            n1_is_nominal_pred = (
                first_n1 is not None and
                first_n1.role == "p" and
                first_n1.pos in ("noun", "adjective", "pronoun")
            )
            n1_is_preposition = (
                first_n1 is not None and first_n1.is_preposition
            )

            if not (n1_is_pp or n1_is_nominal_pred or n1_is_preposition):
                continue

            # Heavy-predicate guard
            n1_weight = _prosodic_word_count(lines[k + 1])
            if n1_weight >= 6:
                return {
                    "fires": True,
                    "verdict": "ADVISORY",
                    "reason": (
                        f"verbless-clause subject on line {k+1} with "
                        f"predicate on line {k+2} "
                        f"(heavy predicate {n1_weight} >= 6 words — SJ5 may license)"
                    ),
                    "details": {
                        "line_n": k + 1,
                        "line_n_plus_1": k + 2,
                        "n1_weight": n1_weight,
                        "n1_opens_with": first_n1.text if first_n1 else "",
                    },
                }

            return {
                "fires": True,
                "verdict": "CONFLICT",
                "reason": (
                    f"verbless-clause subject on line {k+1} "
                    f"separated from its {'PP' if n1_is_pp or n1_is_preposition else 'nominal'} "
                    f"predicate on line {k+2} — BIND: nucleus must stay together"
                ),
                "details": {
                    "line_n": k + 1,
                    "line_n_plus_1": k + 2,
                    "n1_opens_with": first_n1.text if first_n1 else "",
                    "n1_is_pp": n1_is_pp or n1_is_preposition,
                    "n1_is_nominal_pred": n1_is_nominal_pred,
                },
            }
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "IR: no verbless-nucleus split detected", "details": {}}

    # --- Skel fallback ---
    # Heuristic: line N has no wayyiqtol prefix and no clear finite-verb skel;
    # line N+1 begins with a preposition skeleton (ב/ל/מ/על/אל/עם/בין).
    _PREP_SKELS = frozenset({"ב", "ל", "מ", "על", "אל", "עם", "בין", "אל", "לפני", "מן"})
    _WAYYIQTOL_PFXS = ("וי", "ות", "וא", "ונ")

    def _skel_has_finite(line: str) -> bool:
        for tok in line.split():
            s = _consonants(tok)
            for pfx in _WAYYIQTOL_PFXS:
                if s.startswith(pfx) and len(s) >= 4 and s != "ויהוה":
                    return True
        return False

    for k in range(len(lines) - 1):
        if _skel_has_finite(lines[k]):
            continue
        # N+1 begins with preposition
        first_n1_skel = _first_skel_token(lines[k + 1])
        if first_n1_skel in _PREP_SKELS or (len(first_n1_skel) == 1 and first_n1_skel in "בלמ"):
            n1_weight = _prosodic_word_count(lines[k + 1])
            verdict = "ADVISORY" if n1_weight >= 6 else "CONFLICT"
            return {
                "fires": True,
                "verdict": verdict,
                "reason": (
                    f"[skel-fallback] line {k+1} has no finite-verb marker; "
                    f"line {k+2} opens with preposition {first_n1_skel!r} — "
                    "possible verbless-clause nucleus split"
                ),
                "details": {
                    "line_n": k + 1,
                    "line_n_plus_1": k + 2,
                    "n1_first_skel": first_n1_skel,
                    "n1_weight": n1_weight,
                    "caveat": "skel fallback: high false-positive rate without IR",
                },
            }
    return {"fires": False, "verdict": "NO-EFFECT",
            "reason": "skel fallback: no verbless-nucleus split detected", "details": {}}


# ---------------------------------------------------------------------------
# JM121-participial-predicate
# ---------------------------------------------------------------------------

def check_JM121_participial_predicate(
    verse_text: str,
    source_text: str,
    book_slug: str,
    chapter: int,
    verse_num: int,
) -> Optional[dict]:
    """JM121-participial-predicate — Participial-predicate nucleus integrity.

    Encoded question: Is a subject NP on line N separated from its predicative
    participle on line N+1, splitting a participial-predicate clause nucleus?

    Catalog spec: Token.is_participle (type_ in "participle active" / "participle
    passive"). Line N ends with NP (no finite verb); line N+1 opens with a token
    where is_participle = True and role = "p" (predicative).

    Guard: attributive participle (role = "a") — do NOT fire.
    Guard: heavy participial complement (>= 6 tokens including PP) → ADVISORY.

    Macula API used: Token.is_participle, Token.is_active_participle,
    Token.is_passive_participle, Token.role, Token.is_finite_verb.

    Macula gap: Token.role = "p" (predicative) vs "a" (attributive) is the key
    discriminator. In lowfat XML, predicative participles in verbless clauses
    often carry role="p" on the wg level but the token-level role attribute may
    be None or "v". Where token.role is ambiguous, this check uses the absence
    of a finite verb on line N as a proxy for verbless clause context (per catalog
    operationalization). This is a documented approximation.
    """
    lines = _sense_lines(verse_text)
    if len(lines) < 2:
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "single-line verse", "details": {}}

    ir_ok, line_map = _try_ir_alignment(book_slug, chapter, verse_num, lines)

    if ir_ok:
        for k in range(len(lines) - 1):
            n_tokens = line_map.get(k, [])
            n1_tokens = line_map.get(k + 1, [])
            if not n_tokens or not n1_tokens:
                continue

            # Line N: no finite verb (verbless predication context)
            if any(t.is_finite_verb for t in n_tokens):
                continue

            # N+1: first lexical token is a participle
            first_n1 = next((t for t in n1_tokens if t.text.strip()), None)
            if first_n1 is None:
                continue
            if not first_n1.is_participle:
                continue

            # Attributive guard: role="a" → skip (modifies noun, not predicative)
            if first_n1.role == "a":
                continue

            # Heavy-complement guard: participle + PP >= 6 prosodic words on N+1
            n1_weight = _prosodic_word_count(lines[k + 1])
            if n1_weight >= 6:
                return {
                    "fires": True,
                    "verdict": "ADVISORY",
                    "reason": (
                        f"subject NP on line {k+1} with predicative participle "
                        f"{first_n1.text!r} on line {k+2} "
                        f"(participial phrase {n1_weight} >= 6 words — SJ5 may license "
                        "split between subject and participial clause, but NOT "
                        "within the participial phrase)"
                    ),
                    "details": {
                        "line_n": k + 1,
                        "line_n_plus_1": k + 2,
                        "participle": first_n1.text,
                        "participle_type": first_n1.type_,
                        "n1_weight": n1_weight,
                    },
                }

            return {
                "fires": True,
                "verdict": "CONFLICT",
                "reason": (
                    f"subject NP on line {k+1} separated from predicative "
                    f"{'active' if first_n1.is_active_participle else 'passive'} "
                    f"participle {first_n1.text!r} on line {k+2} — "
                    "BIND: participial-predicate nucleus must stay together"
                ),
                "details": {
                    "line_n": k + 1,
                    "line_n_plus_1": k + 2,
                    "participle": first_n1.text,
                    "participle_type": first_n1.type_,
                    "participle_role": first_n1.role,
                },
            }
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "IR: no participial-predicate split detected", "details": {}}

    # --- Skel fallback ---
    # Heuristic: line N has no finite-verb marker; line N+1 first token has
    # participial morphology (מ-prefix Pi'el/Pu'al/Hif, or CoCeC Qal pattern).
    # Caveat: skeletal participial detection is approximate.
    _WAYYIQTOL_PFXS = ("וי", "ות", "וא", "ונ")

    def _skel_has_finite_v(line: str) -> bool:
        for tok in line.split():
            s = _consonants(tok)
            for pfx in _WAYYIQTOL_PFXS:
                if s.startswith(pfx) and len(s) >= 4 and s != "ויהוה":
                    return True
        return False

    def _skel_looks_participial(skel: str) -> bool:
        """Heuristic: participial skeletons often start with מ (Pi'el/Pu'al/Hif)."""
        if not skel or len(skel) < 2:
            return False
        # מ-prefix participles (מ + root consonants)
        if skel.startswith("מ") and len(skel) >= 3:
            return True
        return False

    for k in range(len(lines) - 1):
        if _skel_has_finite_v(lines[k]):
            continue
        first_n1_skel = _first_skel_token(lines[k + 1])
        if _skel_looks_participial(first_n1_skel):
            n1_weight = _prosodic_word_count(lines[k + 1])
            verdict = "ADVISORY" if n1_weight >= 6 else "CONFLICT"
            return {
                "fires": True,
                "verdict": verdict,
                "reason": (
                    f"[skel-fallback] line {k+1} has no finite-verb marker; "
                    f"line {k+2} opens with participial-looking token {first_n1_skel!r} — "
                    "possible participial-predicate nucleus split"
                ),
                "details": {
                    "line_n": k + 1,
                    "line_n_plus_1": k + 2,
                    "n1_first_skel": first_n1_skel,
                    "n1_weight": n1_weight,
                    "caveat": (
                        "skel fallback: מ-prefix heuristic catches Pi'el/Hif participles "
                        "but misses Qal active (CoCeC) and may FP on מ-prefix nouns"
                    ),
                },
            }
    return {"fires": False, "verdict": "NO-EFFECT",
            "reason": "skel fallback: no participial-predicate split", "details": {}}


# ---------------------------------------------------------------------------
# JM133-verb-pp-complement
# ---------------------------------------------------------------------------

def check_JM133_verb_pp_complement(
    verse_text: str,
    source_text: str,
    book_slug: str,
    chapter: int,
    verse_num: int,
) -> Optional[dict]:
    """JM133-verb-pp-complement — Verb-PP complement bond.

    Encoded question: Is a finite verb with an obligatory PP complement
    (שָׁמַע לְ, פָּנָה אֶל, בָּטַח בְּ, etc.) on line N while that PP
    complement begins line N+1?

    Catalog spec: Constituent.is_pp (wg_class="pp") with role="o" or "pp"
    as argument of the verb. Closed-list verb-PP pairs (OBLIGATORY_PP_VERBS).

    Guard: when a PP is adjunct (not obligatory), do NOT fire — default to
    ADVISORY when verb is not in OBLIGATORY_PP_VERBS.

    Macula API used: Token.lemma, Token.is_finite_verb, Token.is_preposition,
    Token.parent_constituent, Constituent.is_pp, Constituent.role.

    Macula gap: Constituent.role ("o" / "pp" / "adv") on the PP constituent is
    the obligatory-vs-adjunct discriminator. In lowfat XML the pp constituent
    carries a role attribute; however, the Token-level role may differ from the
    Constituent-level role. We check both the first token's preposition membership
    and (when available) the parent_constituent.role. Where constituent role is
    unavailable, we fall back to verb-lemma closed-list + preposition-on-N+1
    detection, which has a known elevated FP rate for adjunct PPs — caveat noted.
    """
    lines = _sense_lines(verse_text)
    if len(lines) < 2:
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "single-line verse", "details": {}}

    ir_ok, line_map = _try_ir_alignment(book_slug, chapter, verse_num, lines)

    # Normalize lemma → expected preposition consonant skeleton
    _lemma_to_prep_skel: dict[str, str] = {
        "שָׁמַע": "ל",
        "פָּנָה": "אל",
        "שׁוּב": "אל",
        "בָּטַח": "ב",
        "חָטָא": "ל",
        "דָּבַק": "ב",
        "אָמַן": "ב",
        "הִשְׁתַּחֲוָה": "ל",
        "קִנֵּא": "ב",
        "נִשְׁבַּע": "ב",
        "צָעַק": "אל",
        "קָרָא": "אל",
    }

    if ir_ok:
        for k in range(len(lines) - 1):
            n_tokens = line_map.get(k, [])
            n1_tokens = line_map.get(k + 1, [])
            if not n_tokens or not n1_tokens:
                continue

            # Find obligatory-PP verb on line N
            pp_verb = None
            expected_prep_skel: str = ""
            for t in n_tokens:
                if t.is_finite_verb and t.lemma in _lemma_to_prep_skel:
                    pp_verb = t
                    expected_prep_skel = _lemma_to_prep_skel[t.lemma]

            if pp_verb is None:
                continue

            # Check N+1 begins with the expected preposition
            first_n1 = next((t for t in n1_tokens if t.text.strip()), None)
            if first_n1 is None:
                continue

            if not first_n1.is_preposition:
                continue

            # Check that the PP on N+1 is the obligatory complement, not an adjunct.
            # Primary check: Constituent.is_pp on parent.
            first_n1_in_pp = (
                first_n1.parent_constituent is not None and
                first_n1.parent_constituent.is_pp
            )
            # Secondary: constituent role is "o" or "pp" (oblique-object)
            pp_role = (
                first_n1.parent_constituent.role
                if first_n1.parent_constituent is not None else None
            )
            is_obligatory_pp = first_n1_in_pp and pp_role in ("o", "pp", None)
            # When role is "adv" it's likely an adjunct — downgrade to ADVISORY.
            if pp_role == "adv":
                return {
                    "fires": True,
                    "verdict": "ADVISORY",
                    "reason": (
                        f"verb {pp_verb.text!r} with PP on next line "
                        f"(Constituent.role=adv — likely adjunct, not obligatory complement; "
                        "evaluate manually)"
                    ),
                    "details": {
                        "line_n": k + 1,
                        "line_n_plus_1": k + 2,
                        "verb": pp_verb.text,
                        "verb_lemma": pp_verb.lemma,
                        "pp_first_token": first_n1.text,
                        "pp_role": pp_role,
                    },
                }

            # Verify preposition consonant skeleton matches expected
            prep_skel = _consonants(first_n1.text)
            # Tolerate pronominal suffixes: ב → בו/בה/בי/בנו etc.
            prep_matches = prep_skel.startswith(expected_prep_skel)
            if not prep_matches:
                # Wrong preposition — not the expected obligatory PP
                continue

            return {
                "fires": True,
                "verdict": "CONFLICT",
                "reason": (
                    f"verb {pp_verb.text!r} (lemma {pp_verb.lemma!r}) "
                    f"requires obligatory PP complement {expected_prep_skel!r}; "
                    f"PP {first_n1.text!r} stranded on line {k+2} — "
                    "BIND: verb + obligatory PP must stay on same line"
                ),
                "details": {
                    "line_n": k + 1,
                    "line_n_plus_1": k + 2,
                    "verb": pp_verb.text,
                    "verb_lemma": pp_verb.lemma,
                    "expected_prep": expected_prep_skel,
                    "pp_first_token": first_n1.text,
                },
            }
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "IR: no obligatory-PP stranding detected", "details": {}}

    # --- Skel fallback ---
    for k in range(len(lines) - 1):
        line_skels = [_consonants(t) for t in lines[k].split() if _consonants(t)]
        # Find obligatory-PP verb skeleton on line N
        matched_verb_skel: str = ""
        expected_skel: str = ""
        for s in line_skels:
            if s in _OBL_PP_SKEL:
                matched_verb_skel = s
                expected_skel = _OBL_PP_SKEL[s]
                break
        if not matched_verb_skel:
            continue

        first_n1_skel = _first_skel_token(lines[k + 1])
        if not first_n1_skel.startswith(expected_skel):
            continue

        return {
            "fires": True,
            "verdict": "CONFLICT",
            "reason": (
                f"[skel-fallback] verb skeleton {matched_verb_skel!r} "
                f"on line {k+1} with expected PP {expected_skel!r} "
                f"stranded on line {k+2} (opens with {first_n1_skel!r})"
            ),
            "details": {
                "line_n": k + 1,
                "line_n_plus_1": k + 2,
                "verb_skel": matched_verb_skel,
                "expected_prep_skel": expected_skel,
                "n1_first_skel": first_n1_skel,
                "caveat": (
                    "skel fallback: obligatory vs adjunct PP discrimination "
                    "not possible without Macula constituent role"
                ),
            },
        }
    return {"fires": False, "verdict": "NO-EFFECT",
            "reason": "skel fallback: no obligatory-PP stranding", "details": {}}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

# Canonical 5-arg check registry — single source of truth for this module.
CHECKS_5ARG: dict[str, Callable] = {
    "JM125-verb-object-bond":        check_JM125_verb_object_bond,
    "JM125-coordinated-objects":     check_JM125_coordinated_objects,
    "JM157-complement-integrity":    check_JM157_complement_integrity,
    "JM154-verbless-clause-nucleus": check_JM154_verbless_clause_nucleus,
    "JM121-participial-predicate":   check_JM121_participial_predicate,
    "JM133-verb-pp-complement":      check_JM133_verb_pp_complement,
}


def register_with(registry: dict, strict: bool = True) -> list[str]:
    """Merge this module's 5-arg checks into the runner registry.

    audit_constraints.audit_verse dispatches on callable arity, so 5-arg
    functions register directly. If strict=True (default), raise KeyError on
    collisions where the existing registry entry is a different function.
    Returns the list of constraint IDs registered.
    """
    registered: list[str] = []
    for cid, fn in CHECKS_5ARG.items():
        existing = registry.get(cid)
        if strict and existing is not None and existing is not fn:
            raise KeyError(
                f"register_with collision: '{cid}' already in registry "
                f"with a different function ({getattr(existing, '__name__', repr(existing))!r} vs {fn.__name__!r})"
            )
        registry[cid] = fn
        registered.append(cid)
    return registered
