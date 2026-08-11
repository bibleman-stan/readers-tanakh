#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""checks_bonded_formula.py — Constraint catalog v1 checks for the
bonded-pair / formula / cross-verse cluster.

Implements four entries:
  JM177-bonded-pair          BIND HARD prec 2
  JM-oath-formula            BIND HARD prec 3
  JM-cross-verse-continuity  BIND HARD prec 4
  JM-wayehi-fef-protasis     BIND/SPLIT HARD prec 4

Each check follows the extended signature used by audit_constraints.py
registry: callable(verse_text, source_text, book_slug, chapter, verse_num)
-> Optional[dict].  The dict has keys:
  fires   : bool
  verdict : "CONFLICT" | "ADVISORY" | "NO-EFFECT"
  reason  : str
  details : dict

The simpler two-argument form (verse_text, source_text) still works because
the extra arguments are keyword-optional; audit_constraints.py can call with
positional-only and the guard just skips Macula cross-verse lookups.

Usage:
  from checks_bonded_formula import register_with
  register_with(CHECK_REGISTRY)   # called from an integration shim

Macula API:
  get_verse_tokens(book_slug, chapter, verse) -> list[Token]
  Token.lemma, .pos, .type_, .state, .is_wayyiqtol, .is_finite_verb,
  .is_construct, .has_maqqef_after()
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path
from typing import Optional, Callable

# ---------------------------------------------------------------------------
# Path bootstrap — allow running directly or imported from audit_constraints
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parent.parent.parent
_VALIDATORS = _REPO_ROOT / "5-machinery/validators"
if str(_VALIDATORS) not in sys.path:
    sys.path.insert(0, str(_VALIDATORS))

try:
    from _shared.macula_constituents import get_verse_tokens, Token
    _MACULA_AVAILABLE = True
except ImportError:
    _MACULA_AVAILABLE = False
    Token = None  # type: ignore[assignment,misc]

# The canonical bonded-pair lookup is `is_bonded_pair(lemma_a, lemma_b)`, but
# JM177's surface-match path needs to query by *consonant skeleton* (no lemma
# is available until Macula tokens are matched). We derive `skel_pair_map`
# fresh from the canonical sets on every invocation, which means any future
# fix to BONDED_NOUN_PAIRS / SELF_PAIR_LEMMAS propagates automatically.
from _shared.bonded_noun_pairs import (
    BONDED_NOUN_PAIRS,
    SELF_PAIR_LEMMAS,
)

# ---------------------------------------------------------------------------
# Closed lists
# ---------------------------------------------------------------------------

# JM177 bonded-pair list and self-pair list now live in the canonical module
# 5-machinery/validators/_shared/bonded_noun_pairs.py. We consult that authoritative source
# via `is_bonded_pair(lemma_a, lemma_b)`. Building a skeleton-pair lookup here
# allows the surface-only fallback path when Macula lemmas are unavailable.

# JM-oath-formula: heads of oath formula
# Catalog: חֵי (oath particle, q.v. Joüon §147) in construct before divine name.
# Lemma in Macula is "חַי" (absolute form); oath use detected via context.
OATH_FORMULA_LEMMAS: frozenset[str] = frozenset({"חַי"})

# Preposition בְּ prefixed to חַי produces the בְּחֵי variant; detected via
# surface skeleton check since lowfat merges prefix morpheme onto host token.
OATH_FORMULA_SURFACE_SKELS: frozenset[str] = frozenset({"חי", "בחי"})

# Divine names and proper nouns that can follow the oath particle
DIVINE_NAMES: frozenset[str] = frozenset({
    "יְהוָה",   # Tetragrammaton (NFC form used in Macula)
    "אֱלֹהִים",
    "אֲדֹנָי",
    "אֵל",
    "שַׁדַּי",
})

# Common proper nouns attested in oath contexts (open set; covers corpus cases)
OATH_PROPER_NOUNS: frozenset[str] = frozenset({
    "פַּרְעֹה",   # Gen 42:15–16 (חֵי פַרְעֹה)
    "נַפְשְׁךָ",  # 1 Sam 20:3 (חֵי נַפְשְׁךָ) — pronominal suffix host
    "נֶפֶשׁ",    # backing lemma for נַפְשְׁךָ
})

# Asseveration-opening tokens: the oath asseveration follows the formula head.
# Typically אִם (sworn negation), כִּי, or a finite verb.
ASSEVERATION_CONJUNCTIONS: frozenset[str] = frozenset({"אִם", "כִּי"})

# JM-cross-verse-continuity: subordinating conjunctions whose verse-final
# position signals a grammatical unit crossing the verse boundary.
SUBORDINATING_CONJUNCTIONS: frozenset[str] = frozenset({
    "כִּי",
    "אֲשֶׁר",
    "אִם",
    "כַּאֲשֶׁר",
    "לְמַעַן",
    "פֶּן",
    "עַד",
    "בַּאֲשֶׁר",
})

# Speech-frame tokens whose verse-final position signals cross-verse continuation
SPEECH_FRAME_LEMMAS: frozenset[str] = frozenset({
    "לֵאמֹר",   # infinitive construct of אָמַר used as speech-frame marker
    "אָמַר",    # bare speech verb at verse-end without content
})

# JM-wayehi-fef-protasis: lemma of the FEF trigger verb
HAYAH_LEMMA = "הָיָה"

# Temporal-conjunction heads that introduce FEF protases
FEF_TEMPORAL_CONJUNCTIONS: frozenset[str] = frozenset({
    "כַּאֲשֶׁר",
    "כְּ",       # prefix כ + inf-construct
    "בְּ",       # prefix ב + inf-construct (temporal)
    "עַד",
})

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")


def _strip_points(s: str) -> str:
    """Remove niqqud, te'amim, maqqef from a Hebrew string."""
    return _HEBREW_POINTS_RE.sub("", unicodedata.normalize("NFC", s))


def _consonant_skel(s: str) -> str:
    """Bare consonant skeleton (no points, no maqqef ־, no spaces)."""
    return re.sub(r"[־\s]", "", _strip_points(s))


def _sense_lines(verse_text: str) -> list[str]:
    """Return non-empty stripped sense-lines from a verse block."""
    return [ln.strip() for ln in verse_text.splitlines() if ln.strip()]


def _last_token_skel(line: str) -> str:
    """Consonant skeleton of the last whitespace-separated token on a line."""
    tokens = line.rstrip("׃").split()
    return _consonant_skel(tokens[-1]) if tokens else ""


def _first_token_skel(line: str) -> str:
    """Consonant skeleton of the first whitespace-separated token on a line."""
    tokens = line.split()
    return _consonant_skel(tokens[0]) if tokens else ""


def _first_token_raw(line: str) -> str:
    """First token (with niqqud) of a line."""
    tokens = line.split()
    return tokens[0] if tokens else ""


def _last_token_raw(line: str) -> str:
    """Last token (with niqqud, stripped of sof-pasuq) of a line."""
    tokens = line.rstrip("׃").split()
    return tokens[-1] if tokens else ""


def _line_has_finite_verb_surface(line: str) -> bool:
    """Heuristic: does this line contain a wayyiqtol or similar finite-verb
    marker?  Used only as a guard when Macula is unavailable.

    This is deliberately conservative (false-negative tolerant): we do NOT
    want to suppress bonded-pair firings unless we are confident a finite verb
    is present.  Surface check is: first token starts with וַ / וַּי / וְ
    followed by a consonant cluster consistent with a prefixed verb.
    Accurate detection defers to Macula.
    """
    # Minimal surface heuristic — not used when Macula is available
    return False  # default: assume no finite verb; let Macula guard do real work


def _macula_line_has_finite_verb(tokens: list) -> bool:  # type: ignore[type-arg]
    """Return True if any token in the matched list is a finite verb."""
    return any(t.is_finite_verb for t in tokens)


# ---------------------------------------------------------------------------
# JM177-bonded-pair
# ---------------------------------------------------------------------------

def check_JM177_bonded_pair(
    verse_text: str,
    source_text: str,
    book_slug: str = "",
    chapter: int = 0,
    verse_num: int = 0,
) -> Optional[dict]:
    """JM177: Bonded pair (hendiadys / merism) integrity.

    Fires BIND when:
      - Line N ends with token whose lemma is pair[0]
      - Line N+1 begins with וְ + token whose lemma is pair[1]
      - is_bonded_pair(pair[0], pair[1]) is True (consults canonical
        BONDED_NOUN_PAIRS + SELF_PAIR_LEMMAS in _shared.bonded_noun_pairs)
      - No finite verb on either line (guard against verbal coordination)

    Implementation uses Macula lemma lookup when available; falls back to
    consonant-skeleton matching against the NFC lemma forms in the closed list.

    Macula API gap: `match_sense_line_tokens` requires a `start_idx` return
    value that the audit harness does not currently pass back between lines.
    We use `get_verse_tokens` + consonant-skeleton heuristic for the guard
    when `start_idx` threading is unavailable.
    """
    lines = _sense_lines(verse_text)
    if len(lines) < 2:
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "fewer than 2 sense-lines; no inter-line boundary to check",
                "details": {}}

    # Build consonant-skeleton lookup from the canonical BONDED_NOUN_PAIRS.
    # Each catalog entry is a frozenset({lemma_a, lemma_b}); enter both
    # orderings (surface order is not fixed for commutative merisms).
    # Self-pair lemmas (SELF_PAIR_LEMMAS, e.g. אֶבֶן/אֶבֶן) entered as
    # (skel, skel) -> (lemma, lemma).
    skel_pair_map: dict[tuple[str, str], tuple[str, str]] = {}
    for pair in BONDED_NOUN_PAIRS:
        lemmas = tuple(pair)
        if len(lemmas) != 2:
            continue
        a, b = lemmas
        skel_pair_map[(_consonant_skel(a), _consonant_skel(b))] = (a, b)
        skel_pair_map[(_consonant_skel(b), _consonant_skel(a))] = (b, a)
    for lemma in SELF_PAIR_LEMMAS:
        skel = _consonant_skel(lemma)
        skel_pair_map[(skel, skel)] = (lemma, lemma)

    # Macula path: resolve tokens per line for lemma + finite-verb guard
    verse_tokens: list = []
    if _MACULA_AVAILABLE and book_slug and chapter and verse_num:
        try:
            verse_tokens = get_verse_tokens(book_slug, chapter, verse_num)
        except Exception:
            verse_tokens = []

    for i in range(len(lines) - 1):
        line_n = lines[i]
        line_n1 = lines[i + 1]

        last_skel = _last_token_skel(line_n)
        first_raw = _first_token_raw(line_n1)
        first_skel = _consonant_skel(first_raw)

        # Line N+1 must begin with וְ + something (waw-conjunction prefix)
        if not first_skel.startswith("ו"):
            continue
        following_skel = first_skel[1:]  # strip waw prefix

        # Check pair
        candidate = (last_skel, following_skel)
        if candidate not in skel_pair_map:
            continue

        lemma1, lemma2 = skel_pair_map[candidate]

        # Guard: no finite verb on either line
        # Macula path (preferred)
        if verse_tokens:
            from _shared.macula_constituents import match_sense_line_tokens
            toks_n, _ = match_sense_line_tokens(verse_tokens, line_n)
            toks_n1, _ = match_sense_line_tokens(verse_tokens, line_n1)
            if _macula_line_has_finite_verb(toks_n) or _macula_line_has_finite_verb(toks_n1):
                continue  # verbal coordination, not bonded pair — guard fires
        else:
            # Surface fallback: skeleton-level finite-verb heuristic. A wayyiqtol
            # surface-form typically begins with "וי" / "וַי" / "ויּ" (waw + yod);
            # weqatal often begins with "ו" + qatal-shape. Conservative pattern:
            # any token on either line starting with "וי" (waw-yod) is treated
            # as a probable finite verb and the BIND is suppressed.
            def _line_has_likely_finite_verb(line: str) -> bool:
                for tok in line.split():
                    skel = _consonant_skel(tok)
                    if skel.startswith("וי") or skel.startswith("ויי"):
                        return True
                return False
            if _line_has_likely_finite_verb(line_n) or _line_has_likely_finite_verb(line_n1):
                continue

        return {
            "fires": True,
            "verdict": "CONFLICT",
            "reason": (
                f"bonded pair split across line boundary: "
                f"'{lemma1}' (line {i+1}) / '{lemma2}' (line {i+2}) — "
                f"M1 hendiadys/merism pair must not be separated"
            ),
            "details": {
                "break_after_line": i + 1,
                "pair": (lemma1, lemma2),
                "line_n": line_n,
                "line_n1": line_n1,
                "macula_used": bool(verse_tokens),
            },
        }

    return {"fires": False, "verdict": "NO-EFFECT",
            "reason": "no bonded-pair boundary violation detected",
            "details": {}}


# ---------------------------------------------------------------------------
# JM-oath-formula
# ---------------------------------------------------------------------------

def check_JM_oath_formula(
    verse_text: str,
    source_text: str,
    book_slug: str = "",
    chapter: int = 0,
    verse_num: int = 0,
) -> Optional[dict]:
    """JM-oath-formula: Oath-formula integrity.

    Fires BIND when:
      - Line N ends with [בְּ]חֵי + [maqqef] + divine-name/proper-noun token
        (the complete oath formula head: "חֵי יְהוָה", "חֵי פַרְעֹה", etc.)
        OR ends with just חֵי/בְּחֵי when the divine name is the *first* token
        of line N+1 (atypical split of the formula head itself — also a BIND)
      - Line N+1 begins with asseveration content: אִם / כִּי / finite verb

    Macula operationalization:
      Token.lemma == "חַי" in oath context
      Token.has_maqqef_after() == True → joined to divine name on same token-unit
      Surface skeleton check for בְּחֵי variant (prefix+host in one Macula token)

    Macula API gap:
      Distinguishing oath-use חַי from adjective "living" (הַמַּיִם הַחַיִּים)
      requires pos + context. Macula `pos == "adjective"` for the adjective
      use; oath use has `pos == "particle"` or appears in construct before a
      proper noun. The surface check uses position-in-line (line-final) +
      following-token identity as a proxy; Macula lemma + pos refine this.
    """
    lines = _sense_lines(verse_text)
    if len(lines) < 2:
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "fewer than 2 sense-lines",
                "details": {}}

    # Build skeleton sets for fast lookup
    divine_skels = frozenset(_consonant_skel(d) for d in DIVINE_NAMES)
    proper_skels = frozenset(_consonant_skel(p) for p in OATH_PROPER_NOUNS)
    oath_skels = frozenset(_consonant_skel(o) for o in OATH_FORMULA_SURFACE_SKELS)
    assev_skels = frozenset(_consonant_skel(a) for a in ASSEVERATION_CONJUNCTIONS)

    verse_tokens: list = []
    if _MACULA_AVAILABLE and book_slug and chapter and verse_num:
        try:
            verse_tokens = get_verse_tokens(book_slug, chapter, verse_num)
        except Exception:
            verse_tokens = []

    for i in range(len(lines) - 1):
        line_n = lines[i]
        line_n1 = lines[i + 1]

        tokens_n = line_n.rstrip("׃").split()
        if len(tokens_n) < 1:
            continue

        # --- Pattern A: formula head intact on line N ---
        # Last two tokens of line N should be [oath-particle] + [divine-name/proper]
        # (the two may be maqqef-joined in the source text, appearing as one
        #  surface token: "חֵי־יְהוָה". Handle both cases.)

        formula_found = False
        formula_surface = ""

        if len(tokens_n) >= 2:
            last_raw = tokens_n[-1]
            second_last_raw = tokens_n[-2]
            last_skel = _consonant_skel(last_raw)
            second_last_skel = _consonant_skel(second_last_raw)

            # second-last = oath particle, last = divine/proper name
            if (second_last_skel in oath_skels and
                    (last_skel in divine_skels or last_skel in proper_skels)):
                formula_found = True
                formula_surface = f"{second_last_raw} {last_raw}"

        if not formula_found and len(tokens_n) >= 1:
            # Maqqef-joined case: last token is "חי־יהוה" or "בחי־יהוה"
            last_raw = tokens_n[-1]
            # Split on maqqef glyph (U+05BE ־)
            parts = last_raw.split("־")
            if len(parts) >= 2:
                oath_part_skel = _consonant_skel(parts[0])
                name_part_skel = _consonant_skel(parts[-1])
                if (oath_part_skel in oath_skels and
                        (name_part_skel in divine_skels or name_part_skel in proper_skels)):
                    formula_found = True
                    formula_surface = last_raw

        # --- Pattern B: formula head split (oath particle alone at line-end) ---
        # Rarer: line N ends with bare חֵי/בְּחֵי, line N+1 begins with divine name
        if not formula_found and len(tokens_n) >= 1:
            last_skel = _consonant_skel(tokens_n[-1])
            if last_skel in oath_skels:
                first_skel_n1 = _consonant_skel(_first_token_raw(line_n1))
                if first_skel_n1 in divine_skels or first_skel_n1 in proper_skels:
                    # Formula head itself is split — escalate directly
                    return {
                        "fires": True,
                        "verdict": "CONFLICT",
                        "reason": (
                            f"oath-formula HEAD split: oath particle '{tokens_n[-1]}' "
                            f"(line {i+1}) separated from divine name '{_first_token_raw(line_n1)}' "
                            f"(line {i+2}) — formula unit must not be split"
                        ),
                        "details": {
                            "break_after_line": i + 1,
                            "pattern": "formula-head-split",
                            "line_n": line_n,
                            "line_n1": line_n1,
                        },
                    }

        if not formula_found:
            continue

        # Verify asseveration content on line N+1
        first_skel_n1 = _consonant_skel(_first_token_raw(line_n1))
        # Asseveration: begins with אִם, כִּי, or a finite verb (any Hebrew consonants)
        # We accept any non-empty content as potential asseveration — the key
        # constraint is that formula + asseveration must be bound.
        has_asseveration_marker = first_skel_n1 in assev_skels
        # Even without explicit אִם/כִּי marker, content on N+1 after formula = BIND
        has_any_content = bool(first_skel_n1)

        if has_any_content:
            reason_detail = (
                f"asseveration begins with '{_first_token_raw(line_n1)}' "
                f"({'explicit ' + _first_token_raw(line_n1) if has_asseveration_marker else 'content token'})"
            )
            return {
                "fires": True,
                "verdict": "CONFLICT",
                "reason": (
                    f"oath-formula '{formula_surface}' (line {i+1}) separated from "
                    f"asseveration content (line {i+2}) — {reason_detail}"
                ),
                "details": {
                    "break_after_line": i + 1,
                    "formula_surface": formula_surface,
                    "asseveration_opens_with": _first_token_raw(line_n1),
                    "explicit_asseveration_marker": has_asseveration_marker,
                    "line_n": line_n,
                    "line_n1": line_n1,
                    "macula_used": bool(verse_tokens),
                },
            }

    return {"fires": False, "verdict": "NO-EFFECT",
            "reason": "no oath-formula boundary violation detected",
            "details": {}}


# ---------------------------------------------------------------------------
# JM-cross-verse-continuity
# ---------------------------------------------------------------------------

def check_JM_cross_verse_continuity(
    verse_text: str,
    source_text: str,
    book_slug: str = "",
    chapter: int = 0,
    verse_num: int = 0,
) -> Optional[dict]:
    """JM-cross-verse-continuity: Cross-verse grammatical-unit continuity.

    Examines the FINAL token of the current verse against four sub-cases
    (catalog H10):

      Case 1: Bare subordinating conjunction at verse-end
              → BIND (subordinate clause continues into next verse)
      Case 2: Construct-state noun at verse-end (rectum in next verse)
              → BIND (construct chain crosses verse boundary)
      Case 3: Speech-frame token (לֵאמֹר) alone at verse-end
              → BIND (speech content continues into next verse)
      Case 4: Bare proclitic conjunction (וְ/וַ prefix without host) at verse-end
              → BIND (same as JM103 applied cross-verse)

    The check operates on the verse text + Macula token data.  For cases 1
    and 4 the surface skeleton is sufficient; case 2 requires
    Token.is_construct (Macula state attribute); case 3 is lemma-checked.

    Within-verse audit:  the check inspects the LAST line of the verse block,
    which represents the final tokens of that verse, to detect whether any
    of the four conditions hold.

    Macula API gap:
      Case 2 (construct state) requires Macula `state == "construct"` which
      is not recoverable from surface text alone.  When Macula is unavailable,
      case 2 is marked as NOT-CHECKED in the details dict.
      Case 3 (speech-frame) is surface-detectable via לאמר consonant skeleton.
    """
    lines = _sense_lines(verse_text)
    if not lines:
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "empty verse text",
                "details": {}}

    # We examine the last line (= final tokens of the verse)
    last_line = lines[-1]
    tokens_last_line = last_line.rstrip("׃").split()
    if not tokens_last_line:
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "last line empty after stripping",
                "details": {}}

    final_raw = tokens_last_line[-1]
    final_skel = _consonant_skel(final_raw)

    subordinator_skels = frozenset(_consonant_skel(s) for s in SUBORDINATING_CONJUNCTIONS)
    speech_frame_skels = frozenset(_consonant_skel(s) for s in SPEECH_FRAME_LEMMAS)

    # ---- Case 1: bare subordinating conjunction at verse-end ----
    if final_skel in subordinator_skels:
        return {
            "fires": True,
            "verdict": "CONFLICT",
            "reason": (
                f"verse-final token '{final_raw}' is a subordinating conjunction — "
                f"subordinate clause continues into next verse (cross-verse BIND, H10 case 1)"
            ),
            "details": {
                "sub_case": 1,
                "final_token": final_raw,
                "final_token_skel": final_skel,
                "last_line": last_line,
            },
        }

    # ---- Case 4: bare proclitic conjunction at verse-end ----
    # Proclitic conjunction is a single waw (ו) — either standalone or as a
    # prefixed morpheme stripped from its host by a line break.
    # Surface: a token whose consonant skeleton is just "ו"
    if final_skel == "ו":
        return {
            "fires": True,
            "verdict": "CONFLICT",
            "reason": (
                f"verse-final token '{final_raw}' is a bare proclitic conjunction — "
                f"host word continues into next verse (cross-verse BIND, H10 case 4)"
            ),
            "details": {
                "sub_case": 4,
                "final_token": final_raw,
                "last_line": last_line,
            },
        }

    # ---- Case 3: speech-frame at verse-end ----
    if final_skel in speech_frame_skels or _consonant_skel("לֵאמֹר") == final_skel:
        # Additional check: is this the ONLY content on the last line?
        # Bare לאמר alone = BIND; לאמר within a full clause = potentially OK
        is_bare = len(tokens_last_line) == 1
        if is_bare:
            return {
                "fires": True,
                "verdict": "CONFLICT",
                "reason": (
                    f"verse-final token '{final_raw}' is a bare speech-frame marker — "
                    f"speech content continues into next verse (cross-verse BIND, H10 case 3)"
                ),
                "details": {
                    "sub_case": 3,
                    "final_token": final_raw,
                    "bare_frame": True,
                    "last_line": last_line,
                },
            }

    # ---- Case 2: construct-state noun at verse-end ----
    # Requires Macula Token.is_construct; surface heuristic is unreliable.
    case2_fired = False
    case2_macula_used = False
    case2_detail: dict = {}

    case2_cross_chapter_nyi = False
    if _MACULA_AVAILABLE and book_slug and chapter and verse_num:
        try:
            verse_tokens = get_verse_tokens(book_slug, chapter, verse_num)
            if verse_tokens:
                final_tok = verse_tokens[-1]
                if final_tok.is_construct:
                    case2_fired = True
                    case2_macula_used = True
                    # Chapter-final detection: if no verse_num+1 in this chapter,
                    # the rectum (if any) lives in chapter+1. We do NOT currently
                    # load chapter+1; flag NYI so the downstream consumer knows
                    # the rectum-verification step was skipped.
                    next_verse_toks: list = []
                    try:
                        next_verse_toks = get_verse_tokens(
                            book_slug, chapter, verse_num + 1
                        ) or []
                    except Exception:
                        next_verse_toks = []
                    if not next_verse_toks:
                        case2_cross_chapter_nyi = True
                    case2_detail = {
                        "sub_case": 2,
                        "final_token_lemma": final_tok.lemma,
                        "final_token_text": final_tok.text,
                        "state": "construct",
                        "last_line": last_line,
                        "cross_chapter_nyi": case2_cross_chapter_nyi,
                    }
        except Exception:
            pass

    if case2_fired:
        return {
            "fires": True,
            "verdict": "CONFLICT",
            "reason": (
                f"verse-final token is in construct state — "
                f"rectum continues into next verse (cross-verse BIND, H10 case 2)"
            ),
            "details": {**case2_detail, "macula_used": case2_macula_used},
        }

    return {
        "fires": False,
        "verdict": "NO-EFFECT",
        "reason": "no cross-verse grammatical-unit dependency detected",
        "details": {
            "case2_checked": case2_macula_used,
            "case2_skipped_no_macula": (not case2_macula_used),
        },
    }


# ---------------------------------------------------------------------------
# JM-wayehi-fef-protasis
# ---------------------------------------------------------------------------

def check_JM_wayehi_fef_protasis(
    verse_text: str,
    source_text: str,
    book_slug: str = "",
    chapter: int = 0,
    verse_num: int = 0,
) -> Optional[dict]:
    """JM-wayehi-fef-protasis: Wayehi-FEF protasis integrity.

    Trigger: וַיְהִי (wayyiqtol of הָיָה) introducing a Frame-Establishing
    Formula with a temporal expression.

    BIND arm: protasis temporal expression is split across two lines before
    the main clause arrives (fragmentation).

    SPLIT arm: the entire protasis + main clause collapsed onto a single line
    (the protasis and its following main clause must be on separate lines).

    Detection strategy:
      1. Locate וַיְהִי via Macula (Token.is_wayyiqtol + Token.lemma == "הָיָה")
         or surface skeleton "ויהי".
      2. Identify whether a temporal expression follows on the same or next line:
         - כַּאֲשֶׁר-clause
         - Temporal PP (preposition + time-noun)
         - Infinitive construct phrase (בְּ/כְּ + inf-constr)
      3. BIND arm: trigger + temporal expression span line N and N+1
         (wayehi on N, temporal clause continues on N+1 and is incomplete
         before a main clause appears).
      4. SPLIT arm: trigger + full protasis + main clause on one line.

    Macula API:
      Token.is_wayyiqtol, Token.lemma for precise trigger detection.
      Token.is_finite_verb for identifying main clause arrival.
      Token.is_infinitive_construct for inf-constr temporal phrases.

    Macula API gap:
      Identifying the exact boundary of the protasis (where the temporal
      clause ends and the main clause begins) requires clause-level
      constituent analysis (Constituent.is_clause + role traversal) that
      the current per-verse token-list API does not directly expose.
      We use a finite-verb count heuristic as a proxy:
        - 1 finite verb on a line → wayehi only (protasis incomplete)
        - 2+ finite verbs on a line → wayehi + main clause collapsed (SPLIT arm)
      Surface fallback uses "ויהי" skeleton detection + line structure.
    """
    lines = _sense_lines(verse_text)
    if not lines:
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "empty verse text",
                "details": {}}

    wayehi_skel = _consonant_skel("וַיְהִי")   # "ויהי"
    hayah_skel = _consonant_skel("הָיָה")       # "היה"

    # FEF temporal-conjunction skeletons
    fef_temporal_skels = frozenset(_consonant_skel(s) for s in FEF_TEMPORAL_CONJUNCTIONS)

    # ---- Locate וַיְהִי ----
    # Check each line for the trigger; then inspect whether it introduces a FEF.
    verse_tokens: list = []
    if _MACULA_AVAILABLE and book_slug and chapter and verse_num:
        try:
            verse_tokens = get_verse_tokens(book_slug, chapter, verse_num)
        except Exception:
            verse_tokens = []

    # Find which line(s) contain וַיְהִי
    wayehi_line_indices: list[int] = []
    for idx, line in enumerate(lines):
        token_skels = [_consonant_skel(t) for t in line.split()]
        if wayehi_skel in token_skels:
            wayehi_line_indices.append(idx)

    if not wayehi_line_indices:
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "no וַיְהִי trigger found in verse",
                "details": {}}

    # For each וַיְהִי found, assess FEF pattern
    for wi in wayehi_line_indices:
        line_wi = lines[wi]

        # Is this a FEF wayehi?  Look for temporal expression immediately
        # following on the same line or on line wi+1.
        # Temporal indicators: כַּאֲשֶׁר, בְּ+inf, כְּ+inf, PP with time-noun
        tokens_wi = line_wi.split()
        skels_wi = [_consonant_skel(t) for t in tokens_wi]

        # Count finite verbs on this line (Macula preferred)
        if verse_tokens:
            from _shared.macula_constituents import match_sense_line_tokens
            toks_wi_macula, _ = match_sense_line_tokens(verse_tokens, line_wi)
            finite_count_wi = sum(1 for t in toks_wi_macula if t.is_finite_verb)
            has_inf_construct_wi = any(t.is_infinitive_construct for t in toks_wi_macula)
        else:
            # Surface: count tokens starting with וי / ויש etc. — very rough
            finite_count_wi = 1  # assume at least wayehi itself
            has_inf_construct_wi = False

        # Check for temporal conjunction on same line
        temporal_on_same_line = any(s in fef_temporal_skels for s in skels_wi
                                    if _consonant_skel("ויהי") != s)

        # Check if next line has temporal/protasis content before main clause
        has_next_line = (wi + 1) < len(lines)
        line_next = lines[wi + 1] if has_next_line else ""
        skels_next = [_consonant_skel(t) for t in line_next.split()] if line_next else []

        temporal_on_next_line = any(s in fef_temporal_skels for s in skels_next)

        if verse_tokens and has_next_line:
            toks_next_macula, _ = match_sense_line_tokens(verse_tokens, line_next)
            finite_count_next = sum(1 for t in toks_next_macula if t.is_finite_verb)
            has_inf_construct_next = any(t.is_infinitive_construct for t in toks_next_macula)
        else:
            finite_count_next = 0
            has_inf_construct_next = False

        # ---- Is this a FEF wayehi? ----
        # A FEF wayehi must be followed by a temporal expression.
        # If neither the same line nor the next line has temporal content,
        # treat as narrative wayehi (H3 policy) and skip.
        is_fef = (temporal_on_same_line or temporal_on_next_line or
                  has_inf_construct_wi or has_inf_construct_next)

        if not is_fef:
            continue  # narrative wayehi, not FEF; skip

        # ---- SPLIT arm: protasis + main clause on same line ----
        # Heuristic: 2+ finite verbs on the wayehi line indicates collapse
        # (wayehi + at least one more finite verb = main clause arrived on same line).
        if finite_count_wi >= 2:
            return {
                "fires": True,
                "verdict": "CONFLICT",
                "reason": (
                    f"wayehi-FEF SPLIT required: וַיְהִי + protasis + main clause "
                    f"appear collapsed on line {wi+1} — protasis and main clause "
                    f"must occupy separate sense-lines"
                ),
                "details": {
                    "arm": "SPLIT",
                    "wayehi_line": wi + 1,
                    "finite_verb_count_on_line": finite_count_wi,
                    "line": line_wi,
                    "macula_used": bool(verse_tokens),
                },
            }

        # ---- BIND arm: protasis fragmented across lines ----
        # Pattern: wayehi on line N, temporal expression incomplete (no main
        # clause) extends to line N+1 but the temporal clause is not closed
        # before the main clause appears on line N+2 (or later).
        # Simpler detection: wayehi on line N AND temporal content on N+1 AND
        # no finite verb on N+1 (protasis still open, no main clause yet).
        if has_next_line and temporal_on_next_line and finite_count_next == 0:
            return {
                "fires": True,
                "verdict": "CONFLICT",
                "reason": (
                    f"wayehi-FEF BIND: protasis temporal expression fragmented — "
                    f"וַיְהִי on line {wi+1}, temporal clause extends to line {wi+2} "
                    f"without main-clause arrival; protasis must not be split"
                ),
                "details": {
                    "arm": "BIND",
                    "wayehi_line": wi + 1,
                    "protasis_continues_line": wi + 2,
                    "line_wi": line_wi,
                    "line_next": line_next,
                    "macula_used": bool(verse_tokens),
                },
            }

        # Wayehi + temporal on same line + main clause on next = correct structure
        # (no violation)

    return {
        "fires": False,
        "verdict": "NO-EFFECT",
        "reason": "wayehi-FEF pattern present but no protasis violation detected",
        "details": {"wayehi_lines_checked": wayehi_line_indices},
    }


# ---------------------------------------------------------------------------
# Registry integration
# ---------------------------------------------------------------------------

# Map constraint-catalog IDs to check functions.
# This dict mirrors the CHECK_REGISTRY pattern in audit_constraints.py but
# does NOT modify that module's global.  Call register_with() to integrate.

CHECKS_5ARG: dict[str, Callable] = {
    "JM177-bonded-pair":         check_JM177_bonded_pair,
    "JM-oath-formula":           check_JM_oath_formula,
    "JM-cross-verse-continuity": check_JM_cross_verse_continuity,
    "JM-wayehi-fef-protasis":    check_JM_wayehi_fef_protasis,
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


# ---------------------------------------------------------------------------
# Self-test (run directly: py -3 checks_bonded_formula.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    print("=== checks_bonded_formula.py self-test ===\n")

    # --- JM177 bonded-pair ---
    print("JM177-bonded-pair")
    # Positive: חֶסֶד / וֶאֱמֶת across lines (bare lemma forms, no suffix)
    # Surface skeleton of "חֶסֶד" = "חסד"; "וֶאֱמֶת" = "ואמת" → stripping ו → "אמת"
    r = check_JM177_bonded_pair("חֶסֶד\nוֶאֱמֶת יְהוָה", "")
    assert r and r["fires"], f"Expected BIND, got {r}"
    print(f"  POSITIVE fires={r['fires']} reason={r['reason'][:60]}")
    # Positive: שָׁמַיִם / וָאָרֶץ (merism pair)
    r = check_JM177_bonded_pair("עֹשֵׂה שָׁמַיִם\nוָאָרֶץ", "")
    assert r and r["fires"], f"Expected BIND for shamayim/aretz, got {r}"
    print(f"  POSITIVE (merism) fires={r['fires']} reason={r['reason'][:50]}")
    # Negative: pair on same line — no inter-line split possible
    r = check_JM177_bonded_pair("חֶסֶד וֶאֱמֶת יְהוָה", "")
    assert r and not r["fires"], f"Expected no-fire, got {r}"
    print(f"  NEGATIVE (same line) fires={r['fires']}")
    # Negative: pair not in closed list
    r = check_JM177_bonded_pair("טוֹב\nוְרָע", "")
    assert r and not r["fires"], f"Expected no-fire for non-pair, got {r}"
    print(f"  NEGATIVE (non-pair) fires={r['fires']}")
    print()

    # --- JM-oath-formula ---
    print("JM-oath-formula")
    # Positive: חֵי יְהוָה / כִּי asseveration
    r = check_JM_oath_formula("וְאָמַר חֵי יְהוָה\nכִּי אֶת־הַדָּבָר הַזֶּה לֹא", "")
    assert r and r["fires"], f"Expected BIND, got {r}"
    print(f"  POSITIVE fires={r['fires']} reason={r['reason'][:60]}")
    # Negative: formula + asseveration on same line
    r = check_JM_oath_formula("חֵי יְהוָה כִּי יוּמַת הָאִישׁ", "")
    assert r and not r["fires"], f"Expected no-fire, got {r}"
    print(f"  NEGATIVE fires={r['fires']}")
    print()

    # --- JM-cross-verse-continuity ---
    print("JM-cross-verse-continuity")
    # Positive case 1: verse ends with כִּי
    r = check_JM_cross_verse_continuity("וַיַּרְא אֱלֹהִים כִּי", "")
    assert r and r["fires"], f"Expected BIND, got {r}"
    print(f"  POSITIVE (case1) fires={r['fires']} sub_case={r['details'].get('sub_case')}")
    # Positive case 3: bare לֵאמֹר at verse-end
    r = check_JM_cross_verse_continuity("וַיְדַבֵּר יְהוָה אֶל־מֹשֶׁה\nלֵאמֹר", "")
    assert r and r["fires"], f"Expected BIND, got {r}"
    print(f"  POSITIVE (case3) fires={r['fires']} sub_case={r['details'].get('sub_case')}")
    # Negative: verse ends with complete clause
    r = check_JM_cross_verse_continuity("וַיִּבְרָא אֱלֹהִים אֶת הָאָדָם", "")
    assert r and not r["fires"], f"Expected no-fire, got {r}"
    print(f"  NEGATIVE fires={r['fires']}")
    print()

    # --- JM-wayehi-fef-protasis ---
    print("JM-wayehi-fef-protasis")
    # Positive BIND: wayehi on line 1, temporal content on line 2 with no main clause
    r = check_JM_wayehi_fef_protasis("וַיְהִי בַּיּוֹם\nכַּאֲשֶׁר", "")
    # The temporal "כאשר" appears on next line, no finite verb there
    print(f"  BIND arm fires={r['fires'] if r else None} details={r.get('details',{}).get('arm') if r else None}")
    # Negative: narrative wayehi (no temporal expression)
    r = check_JM_wayehi_fef_protasis("וַיְהִי כֵן\nוַיִּשְׁמַע אֱלֹהִים", "")
    print(f"  NEGATIVE (narrative) fires={r['fires'] if r else None}")
    print()

    # Registry test
    print("register_with() test")
    test_registry: dict = {}
    ids = register_with(test_registry)
    assert set(ids) == set(CHECKS_5ARG.keys()), f"Mismatch: {ids}"
    print(f"  Registered: {ids}")
    print("\nAll self-tests passed.")
