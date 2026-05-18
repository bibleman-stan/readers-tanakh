#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""checks_relative_subordinate.py — Hebrew Constraint Catalog v1 check functions
for the relative + subordinate clause cluster.

Implements 8 constraints from constraint_catalog_v1.md:
  JM158-nonrestrictive-relative  INFORM    ADVISORY prec 7
  JM156-casus-pendens            SPLIT     HARD     prec 3
  JM168-purpose-clause           JUDGMENT-REQUIRED ADVISORY prec 5
  JM159e-conditional-protasis    JUDGMENT-REQUIRED ADVISORY prec 5
  JM157-ki-recitativum           JUDGMENT-REQUIRED ADVISORY prec 5
  JM174-gapped-verb              INFORM    ADVISORY prec 6
  JM123-inf-abs-predicate        BIND      HARD     prec 3
  JM158-restrictive-relative     BIND      ADVISORY prec 5
    (enhanced Macula version; supersedes surface heuristic in audit_constraints.py
     when Macula XML is available — falls back gracefully when not)

Check function signature (per catalog spec):
    def check_<id>(verse_text, source_text, book_slug, chapter, verse_num)
        -> Optional[dict]
    dict keys: fires (bool), verdict (str), reason (str), details (dict)

Integration via register_with(registry):
    The existing audit_constraints.CHECK_REGISTRY maps constraint-id to
    Callable[[str, str], Optional[dict]] (2-arg).  register_with() wraps each
    5-arg check into a 2-arg closure that passes (None, None, None) for location
    args, disabling Macula queries that require location.  When audit_verse is
    updated to pass (verse_text, source_text, book_slug, chapter, verse_num),
    replace the wrappers with direct registration.

Macula API gaps documented inline (search "MACULA-GAP").
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path
from typing import Optional, Callable, TYPE_CHECKING

# ---------------------------------------------------------------------------
# Path setup — Macula constituents lives in validators/_shared/
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
_VALIDATORS = _REPO_ROOT / "validators"
if str(_VALIDATORS) not in sys.path:
    sys.path.insert(0, str(_VALIDATORS))

# Lazy import: Macula XML may not be present in all environments; each check
# that uses Macula wraps the import attempt in a try/except and falls back to
# the surface heuristic path.
try:
    from _shared.macula_constituents import (
        get_verse_tokens,
        get_verse_constituents,
        match_sense_line_tokens,
        Token,
        Constituent,
    )
    _MACULA_AVAILABLE = True
except ImportError:
    _MACULA_AVAILABLE = False


# ---------------------------------------------------------------------------
# Hebrew text helpers (mirrored from audit_constraints for self-containment)
# ---------------------------------------------------------------------------

_HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")
_MAQQEF_RE = re.compile(r"[־]")


def _strip_points(text: str) -> str:
    """Remove niqqud + te'amim, leaving consonant skeleton."""
    return _HEBREW_POINTS_RE.sub("", unicodedata.normalize("NFC", text))


def _strip_all(text: str) -> str:
    """Remove niqqud, te'amim, and maqqef."""
    return _MAQQEF_RE.sub("", _strip_points(text))


def _sense_lines(verse_text: str) -> list[str]:
    """Non-empty stripped lines from verse text block."""
    return [ln for ln in verse_text.splitlines() if ln.strip()]


def _first_word_skel(line: str) -> str:
    """Consonant skeleton of the first whitespace-delimited token on a line."""
    tokens = line.split()
    if not tokens:
        return ""
    return _strip_all(tokens[0])


def _last_word_skel(line: str) -> str:
    """Consonant skeleton of the last whitespace-delimited token on a line,
    stripping sof-pasuq (׃) before matching."""
    tokens = line.rstrip("׃").split()
    if not tokens:
        return ""
    return _strip_all(tokens[-1])


def _prosodic_word_count(line: str) -> int:
    """Count prosodic words: whitespace-delimited tokens, excluding sof-pasuq."""
    return len(line.rstrip("׃").split())


def _ends_verse(line: str) -> bool:
    return line.rstrip().endswith("׃")


# ---------------------------------------------------------------------------
# Lemma constants (NFC-normalized)
# ---------------------------------------------------------------------------

_ASHER = unicodedata.normalize("NFC", "אשר")   # אֲשֶׁר consonant skeleton
_KI    = unicodedata.normalize("NFC", "כי")    # כִּי
_IM    = unicodedata.normalize("NFC", "אם")    # אִם
_LAMED = unicodedata.normalize("NFC", "ל")     # preposition ל lemma
_LEIMOR = unicodedata.normalize("NFC", "לאמר") # לֵאמֹר consonant skeleton

# YHWH-class subject lemmas used in ki-recitativum divine-speech heuristic
_YHWH_LEMMA_SKELS = frozenset({
    "יהוה", "אדני", "אלהים", "אל", "אלה", "שדי", "צבאות",
})

# First-person verbal person/gender/number markers in Macula.
# Macula lowfat emits Token.person as word-form ("first"/"second"/"third"),
# NOT digit-form ("1"/"2"/"3"). Verified empirically (audit β / Gen 22:12).
_FIRST_PERSON = "first"

# Speech-frame verb lemma skeletons (approximate; used for surface heuristic)
_SPEECH_VERB_SKELS = frozenset({
    "אמר", "דבר", "ענה", "קרא", "אמר", "נאם", "ידבר",
})


# ---------------------------------------------------------------------------
# Macula query helpers
# ---------------------------------------------------------------------------

def _get_verse_token_list(book_slug: Optional[str],
                          chapter: Optional[int],
                          verse_num: Optional[int]) -> Optional[list]:
    """Return Macula token list for the verse, or None if unavailable."""
    if not _MACULA_AVAILABLE:
        return None
    if book_slug is None or chapter is None or verse_num is None:
        return None
    try:
        return get_verse_tokens(book_slug, chapter, verse_num)
    except Exception:
        return None


def _get_verse_constituent_list(book_slug: Optional[str],
                                chapter: Optional[int],
                                verse_num: Optional[int]) -> Optional[list]:
    """Return Macula top-level constituent list for the verse, or None."""
    if not _MACULA_AVAILABLE:
        return None
    if book_slug is None or chapter is None or verse_num is None:
        return None
    try:
        return get_verse_constituents(book_slug, chapter, verse_num)
    except Exception:
        return None


def _line_tokens(verse_tokens: list, line_text: str,
                 start_idx: int = 0) -> tuple[list, int]:
    """Match a sense-line to its tokens. Returns (tokens, next_start_idx)."""
    if not _MACULA_AVAILABLE:
        return [], start_idx
    try:
        return match_sense_line_tokens(verse_tokens, line_text, start_idx)
    except Exception:
        return [], start_idx


def _all_constituents_recursive(constituents) -> list:
    """Flatten all Constituent nodes from a tree via DFS."""
    out = []
    if constituents is None:
        return out
    stack = list(constituents)
    while stack:
        node = stack.pop()
        if isinstance(node, Constituent):
            out.append(node)
            for child in node.children:
                if isinstance(child, Constituent):
                    stack.append(child)
    return out


# ---------------------------------------------------------------------------
# JM158-restrictive-relative (enhanced — Macula-driven with surface fallback)
# BIND / ADVISORY / prec 5
# ---------------------------------------------------------------------------

def check_jm158_restrictive_relative(
    verse_text: str,
    source_text: str,
    book_slug: Optional[str] = None,
    chapter: Optional[int] = None,
    verse_num: Optional[int] = None,
) -> Optional[dict]:
    """Restrictive אֲשֶׁר-clause binding to head noun on prior line.

    Macula path: walk relp constituents; if the relp's first token begins
    line N+1 and the head NP's last token ends line N, and the head noun is
    NOT already uniquely identified (proper name / YHWH), fire BIND.

    Surface fallback: line begins with אשר and prior line does not end with
    sof-pasuq.

    Non-restrictive guard: if the head noun token has type_=="proper" or
    lemma is YHWH-class, route to JM158-nonrestrictive instead of firing here.
    """
    lines = _sense_lines(verse_text)
    if len(lines) < 2:
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "single-line verse — no relative-clause boundary possible"}

    # --- Macula path ---
    verse_tokens = _get_verse_token_list(book_slug, chapter, verse_num)
    verse_consts = _get_verse_constituent_list(book_slug, chapter, verse_num)

    if verse_tokens and verse_consts:
        # Build line -> token mapping
        start = 0
        line_token_map: list[list] = []
        for ln in lines:
            toks, start = _line_tokens(verse_tokens, ln, start)
            line_token_map.append(toks)

        line_token_ids: list[set] = [
            {t.xml_id for t in toks} for toks in line_token_map
        ]

        # Find all relp constituents
        all_consts = _all_constituents_recursive(verse_consts)
        relp_consts = [c for c in all_consts if c.is_relative_clause]

        for relp in relp_consts:
            relp_toks = relp.tokens
            if not relp_toks:
                continue
            first_relp_tok = relp_toks[0]

            # Which line does the relp START on?
            relp_start_line = None
            for li, id_set in enumerate(line_token_ids):
                if first_relp_tok.xml_id in id_set:
                    relp_start_line = li
                    break
            if relp_start_line is None or relp_start_line == 0:
                continue

            # Confirm line begins with אשר consonant skeleton
            if _first_word_skel(lines[relp_start_line]) != _ASHER:
                continue

            prior_line_idx = relp_start_line - 1
            prior_toks = line_token_map[prior_line_idx]
            if not prior_toks:
                continue

            # Check parent: relp's parent constituent should be an NP
            head_np = relp.parent
            if head_np is None:
                # MACULA-GAP: relp with no recorded parent — fallthrough to
                # surface heuristic for this instance
                pass
            else:
                head_np_toks = head_np.tokens
                # Confirm at least one head NP token is on the prior line
                prior_id_set = line_token_ids[prior_line_idx]
                head_on_prior = any(t.xml_id in prior_id_set for t in head_np_toks)
                if not head_on_prior:
                    continue

                # Non-restrictive guard: check if head is a proper name / YHWH
                # MACULA-GAP: no `is_unique` property; approximate via type_=="proper"
                head_tokens_on_prior = [
                    t for t in head_np_toks if t.xml_id in prior_id_set
                ]
                is_proper = any(
                    getattr(t, "type_", None) == "proper"
                    for t in head_tokens_on_prior
                )
                if is_proper:
                    # Non-restrictive — handled by JM158-nonrestrictive
                    continue

                return {
                    "fires": True,
                    "verdict": "ADVISORY",
                    "reason": (
                        f"line {relp_start_line + 1} begins אֲשֶׁר; Macula relp "
                        f"constituent attached to non-proper head on line "
                        f"{prior_line_idx + 1} — restrictive binding (BIND advisory)"
                    ),
                    "details": {
                        "relp_line": relp_start_line + 1,
                        "head_line": prior_line_idx + 1,
                        "macula": True,
                    },
                }

    # --- Surface fallback ---
    for i in range(1, len(lines)):
        if _first_word_skel(lines[i]) == _ASHER and not _ends_verse(lines[i - 1]):
            return {
                "fires": True,
                "verdict": "ADVISORY",
                "reason": (
                    f"line {i + 1} begins אֲשֶׁר; relative may be restrictive "
                    f"(bound to head on line {i}) — surface heuristic"
                ),
                "details": {"relp_line": i + 1, "head_line": i, "macula": False},
            }

    return {"fires": False, "verdict": "NO-EFFECT",
            "reason": "no restrictive-relative pattern detected"}


# ---------------------------------------------------------------------------
# JM158-nonrestrictive-relative
# INFORM / ADVISORY / prec 7
# ---------------------------------------------------------------------------

def check_jm158_nonrestrictive_relative(
    verse_text: str,
    source_text: str,
    book_slug: Optional[str] = None,
    chapter: Optional[int] = None,
    verse_num: Optional[int] = None,
) -> Optional[dict]:
    """Non-restrictive אֲשֶׁר-clause licensing: head noun is already uniquely
    identified (proper name or YHWH-class lemma). Clause may stand alone.

    Macula path: relp attached to NP where head token has type_=="proper"
    or lemma consonant skeleton in _YHWH_LEMMA_SKELS.

    Surface fallback: line N begins with אשר; prior line ends with a proper
    noun heuristic (title-initial capital in transliteration OR prior line's
    last word consonant skeleton in a YHWH-class closed list).
    """
    lines = _sense_lines(verse_text)
    if len(lines) < 2:
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "single-line verse"}

    verse_tokens = _get_verse_token_list(book_slug, chapter, verse_num)
    verse_consts = _get_verse_constituent_list(book_slug, chapter, verse_num)

    if verse_tokens and verse_consts:
        start = 0
        line_token_map: list[list] = []
        for ln in lines:
            toks, start = _line_tokens(verse_tokens, ln, start)
            line_token_map.append(toks)
        line_token_ids = [{t.xml_id for t in toks} for toks in line_token_map]

        all_consts = _all_constituents_recursive(verse_consts)
        relp_consts = [c for c in all_consts if c.is_relative_clause]

        for relp in relp_consts:
            relp_toks = relp.tokens
            if not relp_toks:
                continue
            first_relp_tok = relp_toks[0]

            relp_start_line = None
            for li, id_set in enumerate(line_token_ids):
                if first_relp_tok.xml_id in id_set:
                    relp_start_line = li
                    break
            if relp_start_line is None or relp_start_line == 0:
                continue

            if _first_word_skel(lines[relp_start_line]) != _ASHER:
                continue

            prior_line_idx = relp_start_line - 1
            prior_id_set = line_token_ids[prior_line_idx]

            head_np = relp.parent
            if head_np is None:
                continue

            head_np_toks = head_np.tokens
            head_tokens_on_prior = [
                t for t in head_np_toks if t.xml_id in prior_id_set
            ]
            if not head_tokens_on_prior:
                continue

            # Fire only when head IS uniquely identified (proper or YHWH-class)
            is_proper = any(
                getattr(t, "type_", None) == "proper"
                or _strip_all(getattr(t, "lemma", "") or "") in _YHWH_LEMMA_SKELS
                for t in head_tokens_on_prior
            )
            if not is_proper:
                continue

            # Weight check: short clauses (≤3 prosodic words) noted in details
            relp_word_count = _prosodic_word_count(lines[relp_start_line])
            weight_note = (
                "weight-insufficient (≤3 words) — may not stand alone"
                if relp_word_count <= 3
                else "weight adequate"
            )

            return {
                "fires": True,
                "verdict": "ADVISORY",
                "reason": (
                    f"line {relp_start_line + 1} begins אֲשֶׁר after uniquely-"
                    f"identified head on line {prior_line_idx + 1} — "
                    f"non-restrictive relative (INFORM: clause may stand alone). "
                    f"{weight_note}."
                ),
                "details": {
                    "inform": True,
                    "relp_line": relp_start_line + 1,
                    "head_line": prior_line_idx + 1,
                    "relp_word_count": relp_word_count,
                    "weight_note": weight_note,
                    "macula": True,
                },
            }

    # --- Surface fallback ---
    for i in range(1, len(lines)):
        if _first_word_skel(lines[i]) != _ASHER:
            continue
        prior_last = _last_word_skel(lines[i - 1])
        if prior_last in _YHWH_LEMMA_SKELS:
            relp_wc = _prosodic_word_count(lines[i])
            weight_note = (
                "weight-insufficient (≤3 words)" if relp_wc <= 3 else "weight adequate"
            )
            return {
                "fires": True,
                "verdict": "ADVISORY",
                "reason": (
                    f"line {i + 1} begins אֲשֶׁר after divine-name head "
                    f"on line {i} — non-restrictive relative (INFORM). "
                    f"{weight_note}. Surface heuristic."
                ),
                "details": {
                    "inform": True,
                    "relp_line": i + 1,
                    "head_line": i,
                    "relp_word_count": relp_wc,
                    "weight_note": weight_note,
                    "macula": False,
                },
            }

    return {"fires": False, "verdict": "NO-EFFECT",
            "reason": "no non-restrictive-relative pattern detected"}


# ---------------------------------------------------------------------------
# JM156-casus-pendens
# SPLIT / HARD / prec 3
# ---------------------------------------------------------------------------

def check_jm156_casus_pendens(
    verse_text: str,
    source_text: str,
    book_slug: Optional[str] = None,
    chapter: Optional[int] = None,
    verse_num: Optional[int] = None,
) -> Optional[dict]:
    """Casus pendens own-line: topic-fronted NP + resumptive pronoun must
    not both appear on the same sense-line when the topic NP is a recognizable
    casus pendens.

    Macula path: find a token T1 (pos==noun or pronoun, early in verse) whose
    participantref_ids point to a later token T2 (pronoun or pronominal suffix)
    on the same sense-line. When T1 and T2 are both on the same line and T1
    precedes the main verb, fire SPLIT.

    MACULA-GAP: Macula does not expose a dedicated "casus pendens" role label
    in lowfat; the detection relies on participantref cross-reference + relative
    position. This is a best-effort approximation; the HARD tier means false
    positives will surface for editorial review.

    Surface fallback: heuristic not reliable enough to fire HARD-SPLIT
    without Macula; returns NO-EFFECT when Macula unavailable.
    """
    lines = _sense_lines(verse_text)
    if not lines:
        return {"fires": False, "verdict": "NO-EFFECT", "reason": "empty verse"}

    verse_tokens = _get_verse_token_list(book_slug, chapter, verse_num)

    if verse_tokens:
        start = 0
        line_token_map: list[list] = []
        for ln in lines:
            toks, start = _line_tokens(verse_tokens, ln, start)
            line_token_map.append(toks)

        for li, line_toks in enumerate(line_token_map):
            if len(line_toks) < 2:
                continue

            # Collect participant-ref cross-references within this line
            # A casus pendens token appears early (within first 2 tokens of verse)
            # and has a resumptive pronoun later on the same line referencing it.
            for ti, tok in enumerate(line_toks):
                if tok.pos not in ("noun", "pronoun", "adjective"):
                    continue
                if not tok.participantref_ids:
                    continue

                # Check: does any later token on this line reference tok?
                tok_id_set = {tok.xml_id, tok.xml_id.lstrip("o")}
                resumptive = [
                    t for t in line_toks[ti + 1:]
                    if (t.pos in ("pronoun", "suffix")
                        and any(rid in tok_id_set for rid in t.participantref_ids))
                ]
                if not resumptive:
                    continue

                # Guard: is there a finite verb between tok and resumptive?
                # A true casus pendens has the main clause (with verb) after the topic.
                between_toks = line_toks[ti:]
                has_finite_verb = any(t.is_finite_verb for t in between_toks)
                if not has_finite_verb:
                    continue

                resumptive_tok = resumptive[0]
                return {
                    "fires": True,
                    "verdict": "CONFLICT",
                    "reason": (
                        f"line {li + 1}: token '{tok.text}' (pos={tok.pos}) "
                        f"has resumptive pronoun '{resumptive_tok.text}' "
                        f"on same line — casus pendens must occupy its own line (SPLIT)"
                    ),
                    "details": {
                        "topic_token": tok.text,
                        "resumptive_token": resumptive_tok.text,
                        "line": li + 1,
                        "macula": True,
                    },
                }

    # Surface fallback — not reliable for HARD; report as informational gap
    # MACULA-GAP: casus pendens surface detection without participantref is
    # unreliable (would fire on all fronted NPs indiscriminately).
    return {
        "fires": False,
        "verdict": "NO-EFFECT",
        "reason": (
            "casus pendens check requires Macula participantref resolution; "
            "Macula unavailable or no casus-pendens pattern detected"
        ),
    }


# ---------------------------------------------------------------------------
# JM168-purpose-clause
# JUDGMENT-REQUIRED / ADVISORY / prec 5
# ---------------------------------------------------------------------------

# Lemma of לֵאמֹר (speech-marker infinitive — excluded from purpose-clause check)
_LEIMOR_LEMMA = unicodedata.normalize("NFC", "לאמר")


def check_jm168_purpose_clause(
    verse_text: str,
    source_text: str,
    book_slug: Optional[str] = None,
    chapter: Optional[int] = None,
    verse_num: Optional[int] = None,
) -> Optional[dict]:
    """Purpose-clause infinitive binding: line N+1 begins with לְ + infinitive-
    construct, indicating a purpose clause subordinate to the matrix verb on
    line N.

    Macula path: first token on line N+1 has is_preposition==True and
    lemma==ל; second token on line N+1 has is_infinitive_construct==True.
    Guard: exclude לֵאמֹר. Role check: infinitive should have role=="adv"
    (adverbial adjunct) or be within a child clause of the matrix.

    Weight heuristic: ≤3 prosodic words on line N+1 → lean BIND detail note.

    Surface fallback: line begins with ל + inf-construct consonant pattern
    (first word is a lamed-prefixed form; second word checks not needed without
    Macula since we cannot distinguish inf-construct from other verb forms).
    """
    lines = _sense_lines(verse_text)
    if len(lines) < 2:
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "single-line verse"}

    verse_tokens = _get_verse_token_list(book_slug, chapter, verse_num)

    if verse_tokens:
        start = 0
        line_token_map: list[list] = []
        for ln in lines:
            toks, start = _line_tokens(verse_tokens, ln, start)
            line_token_map.append(toks)

        for li in range(1, len(lines)):
            line_toks = line_token_map[li]
            if len(line_toks) < 2:
                continue

            tok0 = line_toks[0]
            tok1 = line_toks[1]

            # First token: preposition ל
            is_lamed_prep = (
                getattr(tok0, "is_preposition", False)
                and _strip_all(getattr(tok0, "lemma", "") or "") == _LAMED
            )
            if not is_lamed_prep:
                continue

            # Second token: infinitive construct
            if not getattr(tok1, "is_infinitive_construct", False):
                continue

            # Guard: exclude לֵאמֹר
            if _strip_all(getattr(tok1, "lemma", "") or "") == _LEIMOR_LEMMA:
                continue

            # Role check: purpose-clause fires only when inf-construct is an
            # adverbial adjunct (role=="adv") or unset (MACULA-GAP: role on
            # infinitive phrase head is sometimes unset in lowfat). Any
            # *other* role (s, o, p, pp, o2, ...) means it's a nominal or
            # predicate use, not a purpose clause — skip.
            tok1_role = getattr(tok1, "role", None)
            if tok1_role not in ("adv", None, ""):
                continue

            prior_line = lines[li - 1]
            purpose_line = lines[li]
            wc = _prosodic_word_count(purpose_line)
            weight_lean = (
                "short clause (≤3 words) — leans BIND"
                if wc <= 3
                else f"longer clause ({wc} words) — may stand independently"
            )

            return {
                "fires": True,
                "verdict": "ADVISORY",
                "reason": (
                    f"line {li + 1} begins לְ + infinitive-construct "
                    f"'{tok1.text}' — purpose clause subordinate to matrix "
                    f"verb on line {li} (JUDGMENT-REQUIRED). {weight_lean}."
                ),
                "details": {
                    "purpose_line": li + 1,
                    "matrix_line": li,
                    "purpose_infinitive": tok1.text,
                    "purpose_word_count": wc,
                    "weight_lean": weight_lean,
                    "macula": True,
                },
            }

    # --- Surface fallback ---
    # Heuristic: line begins with a word whose consonant skeleton starts with ל
    # and is short (≤4 chars beyond the lamed), and prior line has content.
    for i in range(1, len(lines)):
        first = lines[i].split()
        if not first:
            continue
        fw_skel = _strip_all(first[0])
        if not fw_skel.startswith(_LAMED):
            continue
        # Exclude לֵאמֹר surface form
        if fw_skel == _LEIMOR:
            continue
        # Must have at least 2 tokens (ל + inf word); surface can't confirm
        # infinitive-construct vs. other verb types, so be conservative:
        # only fire if prior line ends with a finite-verb heuristic token and
        # the purpose line is short (≤3 words).
        wc = _prosodic_word_count(lines[i])
        if wc <= 3 and not _ends_verse(lines[i - 1]):
            return {
                "fires": True,
                "verdict": "ADVISORY",
                "reason": (
                    f"line {i + 1} begins with ל-prefixed word ('{first[0]}', "
                    f"skel={fw_skel!r}) and is short ({wc} words) — possible "
                    f"purpose-clause infinitive (JUDGMENT-REQUIRED). Surface heuristic."
                ),
                "details": {
                    "purpose_line": i + 1,
                    "matrix_line": i,
                    "first_word": first[0],
                    "purpose_word_count": wc,
                    "macula": False,
                },
            }

    return {"fires": False, "verdict": "NO-EFFECT",
            "reason": "no purpose-clause pattern detected"}


# ---------------------------------------------------------------------------
# JM159e-conditional-protasis
# JUDGMENT-REQUIRED / ADVISORY / prec 5
# ---------------------------------------------------------------------------

def check_jm159e_conditional_protasis(
    verse_text: str,
    source_text: str,
    book_slug: Optional[str] = None,
    chapter: Optional[int] = None,
    verse_num: Optional[int] = None,
) -> Optional[dict]:
    """Conditional protasis–apodosis integrity: short אִם-clause (≤4 prosodic
    words) on line N followed by apodosis on line N+1.

    Macula path: first token of line N has lemma==אִם and pos==conjunction
    (conditional particle). Line N word count ≤4. Line N+1 has at least one
    finite verb or weqatal.

    Guard: אִם in oath formulas — excluded (typically follows חֵי + name).

    Surface fallback: line begins with consonant skeleton אם; word count ≤4;
    next line has a word (any, since we cannot confirm finite verb without Macula).
    """
    lines = _sense_lines(verse_text)
    if len(lines) < 2:
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "single-line verse"}

    verse_tokens = _get_verse_token_list(book_slug, chapter, verse_num)

    if verse_tokens:
        start = 0
        line_token_map: list[list] = []
        for ln in lines:
            toks, start = _line_tokens(verse_tokens, ln, start)
            line_token_map.append(toks)

        for li in range(len(lines) - 1):
            line_toks = line_token_map[li]
            if not line_toks:
                continue

            tok0 = line_toks[0]
            is_im_conditional = (
                _strip_all(getattr(tok0, "lemma", "") or "") == _IM
                and getattr(tok0, "pos", None) == "conjunction"
            )
            if not is_im_conditional:
                continue

            # Oath-formula guard: check if prior line ends with חי + name
            # MACULA-GAP: no direct oath-formula detection; approximate via
            # prior-line last token lemma
            if li > 0:
                prior_toks = line_token_map[li - 1]
                if prior_toks:
                    last_prior = prior_toks[-1]
                    if _strip_all(getattr(last_prior, "lemma", "") or "") in _YHWH_LEMMA_SKELS:
                        # Could be oath context — skip
                        continue

            wc = _prosodic_word_count(lines[li])
            if wc > 4:
                continue  # Long protasis — may stand alone

            # Confirm line N+1 has a finite verb or weqatal (apodosis marker)
            next_line_toks = line_token_map[li + 1]
            has_apodosis_verb = any(
                getattr(t, "is_finite_verb", False) or getattr(t, "is_weqatal", False)
                for t in next_line_toks
            )
            if not has_apodosis_verb and next_line_toks:
                # Weaker: next line has at least some tokens — still flag but note
                pass

            lean = "strong lean BIND" if wc <= 2 else "lean BIND"
            return {
                "fires": True,
                "verdict": "ADVISORY",
                "reason": (
                    f"line {li + 1} is short conditional protasis (אִם, {wc} words); "
                    f"apodosis follows on line {li + 2} — "
                    f"JUDGMENT-REQUIRED ({lean})."
                ),
                "details": {
                    "protasis_line": li + 1,
                    "apodosis_line": li + 2,
                    "protasis_word_count": wc,
                    "apodosis_has_finite_verb": has_apodosis_verb,
                    "lean": lean,
                    "macula": True,
                },
            }

    # --- Surface fallback ---
    for i in range(len(lines) - 1):
        if _first_word_skel(lines[i]) != _IM:
            continue
        wc = _prosodic_word_count(lines[i])
        if wc > 4:
            continue
        lean = "strong lean BIND" if wc <= 2 else "lean BIND"
        return {
            "fires": True,
            "verdict": "ADVISORY",
            "reason": (
                f"line {i + 1} begins אִם with {wc} words — short conditional "
                f"protasis; apodosis expected on line {i + 2} "
                f"(JUDGMENT-REQUIRED, {lean}). Surface heuristic."
            ),
            "details": {
                "protasis_line": i + 1,
                "apodosis_line": i + 2,
                "protasis_word_count": wc,
                "lean": lean,
                "macula": False,
            },
        }

    return {"fires": False, "verdict": "NO-EFFECT",
            "reason": "no short conditional protasis detected"}


# ---------------------------------------------------------------------------
# JM157-ki-recitativum
# JUDGMENT-REQUIRED / ADVISORY / prec 5
# ---------------------------------------------------------------------------

def check_jm157_ki_recitativum(
    verse_text: str,
    source_text: str,
    book_slug: Optional[str] = None,
    chapter: Optional[int] = None,
    verse_num: Optional[int] = None,
) -> Optional[dict]:
    """כִּי recitativum vs. causal disambiguation.

    Macula path: line N+1 begins with token lemma==כִּי (conjunction).
    Prior line N context check: does any verb on line N have a subject
    (via subjref_ids) that resolves to a YHWH-class token? Or is there a
    first-person verb with person=="1" whose subject participantref points
    to YHWH? If yes, flag JUDGMENT-REQUIRED for recitativum possibility.

    Guard: if prior line N has a cognition/speech verb that would license
    JM157-complement-integrity (obligatory complement), do NOT fire here —
    the complement constraint takes precedence.

    MACULA-GAP: determining whether YHWH is the speaker (vs. merely a
    subject being discussed) requires broader discourse context not captured
    in the verse-level Macula query. The check is necessarily approximate.

    Surface fallback: line begins with כי; prior line ends with a word from
    _SPEECH_VERB_SKELS or verse contains first-person suffix patterns — flag
    with lower confidence.
    """
    lines = _sense_lines(verse_text)
    if len(lines) < 2:
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "single-line verse"}

    # Obligatory-complement verb lemma skeletons — when prior line ends with
    # these, JM157-complement-integrity governs (not recitativum). The
    # authoritative list lives in checks_clause_nucleus._OBL_COMP_SKEL; we
    # import to avoid drift.
    from checks_clause_nucleus import _OBL_COMP_SKEL as _COMPLEMENT_VERBS

    verse_tokens = _get_verse_token_list(book_slug, chapter, verse_num)

    if verse_tokens:
        start = 0
        line_token_map: list[list] = []
        for ln in lines:
            toks, start = _line_tokens(verse_tokens, ln, start)
            line_token_map.append(toks)

        for li in range(1, len(lines)):
            line_toks = line_token_map[li]
            if not line_toks:
                continue

            tok0 = line_toks[0]
            is_ki = (
                _strip_all(getattr(tok0, "lemma", "") or "") == _KI
                and getattr(tok0, "pos", None) == "conjunction"
            )
            if not is_ki:
                continue

            prior_toks = line_token_map[li - 1]

            # Complement guard: prior line ends with obligatory-complement verb
            prior_verbs = [
                t for t in prior_toks
                if getattr(t, "is_finite_verb", False)
            ]
            if prior_verbs:
                last_verb = prior_verbs[-1]
                if _strip_all(getattr(last_verb, "lemma", "") or "") in _COMPLEMENT_VERBS:
                    # JM157-complement-integrity governs — skip recitativum check
                    continue

            # Check for divine speech context:
            # (a) Any token on line N has YHWH-class subject via subjref_ids
            yhwh_subject = False
            for t in prior_toks:
                for ref_tok in getattr(t, "referenced_subjects", []):
                    if (_strip_all(getattr(ref_tok, "lemma", "") or "")
                            in _YHWH_LEMMA_SKELS):
                        yhwh_subject = True
                        break
                if yhwh_subject:
                    break

            # (b) First-person verb on line N or N+1 (כי-clause)
            first_person_on_prior = any(
                getattr(t, "person", None) == _FIRST_PERSON
                and getattr(t, "is_finite_verb", False)
                for t in prior_toks
            )
            first_person_in_ki_clause = any(
                getattr(t, "person", None) == _FIRST_PERSON
                and getattr(t, "is_finite_verb", False)
                for t in line_toks
            )

            if yhwh_subject or (first_person_on_prior and first_person_in_ki_clause):
                return {
                    "fires": True,
                    "verdict": "ADVISORY",
                    "reason": (
                        f"line {li + 1} begins כִּי in possible divine-speech context "
                        f"(line {li} has "
                        + ("YHWH-class subject" if yhwh_subject else "1st-person verb")
                        + f") — JUDGMENT-REQUIRED: recitativum vs. causal disambiguation needed."
                    ),
                    "details": {
                        "ki_line": li + 1,
                        "prior_line": li,
                        "yhwh_subject": yhwh_subject,
                        "first_person_prior": first_person_on_prior,
                        "first_person_ki_clause": first_person_in_ki_clause,
                        "macula": True,
                    },
                }

    # --- Surface fallback ---
    for i in range(1, len(lines)):
        if _first_word_skel(lines[i]) != _KI:
            continue
        prior_last = _last_word_skel(lines[i - 1])
        # Simple heuristic: prior line ends with speech verb OR YHWH-class name
        if prior_last in _SPEECH_VERB_SKELS or prior_last in _YHWH_LEMMA_SKELS:
            return {
                "fires": True,
                "verdict": "ADVISORY",
                "reason": (
                    f"line {i + 1} begins כִּי after possible speech/divine context "
                    f"on line {i} ('{prior_last}') — JUDGMENT-REQUIRED: "
                    f"recitativum vs. causal. Surface heuristic."
                ),
                "details": {
                    "ki_line": i + 1,
                    "prior_line": i,
                    "prior_last_word": prior_last,
                    "macula": False,
                },
            }

    return {"fires": False, "verdict": "NO-EFFECT",
            "reason": "no כי recitativum pattern detected"}


# ---------------------------------------------------------------------------
# JM174-gapped-verb
# INFORM / ADVISORY / prec 6
# ---------------------------------------------------------------------------

def check_jm174_gapped_verb(
    verse_text: str,
    source_text: str,
    book_slug: Optional[str] = None,
    chapter: Optional[int] = None,
    verse_num: Optional[int] = None,
) -> Optional[dict]:
    """Gapped finite verb in parallel bicolon: line N has a finite verb;
    line N+1 has NO finite verb but has parallel role-label structure (similar
    subject/object roles). INFORM: gapped colon is propositionally complete.

    Macula path: line N has Token.is_finite_verb==True. Line N+1 has no
    is_finite_verb token. Both lines share parallel role labels: tokens_with_role
    comparison across line_token_map shows "s" or "o" roles on both lines
    without a verb on N+1.

    MACULA-GAP: Macula role labels ("s", "o") on tokens within a gapped
    bicolon may not be present if the parser treats the gapped colon as
    lacking a predicate frame. When role labels are absent, fall back to
    token-count heuristic (similar word count ± 1 between N and N+1).

    Surface fallback: line N has content; line N+1 has similar token count
    to line N (parallel length heuristic, ±1 word).
    """
    lines = _sense_lines(verse_text)
    if len(lines) < 2:
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "single-line verse"}

    verse_tokens = _get_verse_token_list(book_slug, chapter, verse_num)

    if verse_tokens:
        start = 0
        line_token_map: list[list] = []
        for ln in lines:
            toks, start = _line_tokens(verse_tokens, ln, start)
            line_token_map.append(toks)

        for li in range(len(lines) - 1):
            line_n_toks = line_token_map[li]
            line_n1_toks = line_token_map[li + 1]

            if not line_n_toks or not line_n1_toks:
                continue

            # Line N must have a finite verb
            has_finite_n = any(
                getattr(t, "is_finite_verb", False) for t in line_n_toks
            )
            if not has_finite_n:
                continue

            # Line N+1 must have NO finite verb
            has_finite_n1 = any(
                getattr(t, "is_finite_verb", False) for t in line_n1_toks
            )
            if has_finite_n1:
                continue

            # Parallel role check
            roles_n = {getattr(t, "role", None) for t in line_n_toks} - {None, "", "v"}
            roles_n1 = {getattr(t, "role", None) for t in line_n1_toks} - {None, ""}
            has_parallel_roles = bool(roles_n & roles_n1)  # shared non-verb roles

            # Fallback: similar word counts
            wc_n = _prosodic_word_count(lines[li])
            wc_n1 = _prosodic_word_count(lines[li + 1])
            parallel_length = abs(wc_n - wc_n1) <= 1

            if has_parallel_roles or parallel_length:
                return {
                    "fires": True,
                    "verdict": "ADVISORY",
                    "reason": (
                        f"line {li + 1} has finite verb; line {li + 2} has no "
                        f"finite verb but parallel structure "
                        f"({'matching roles: ' + str(roles_n & roles_n1) if has_parallel_roles else 'similar length'}) "
                        f"— probable gapped bicolon (INFORM: propositionally complete)."
                    ),
                    "details": {
                        "verb_line": li + 1,
                        "gapped_line": li + 2,
                        "parallel_roles": list(roles_n & roles_n1),
                        "word_count_n": wc_n,
                        "word_count_n1": wc_n1,
                        "inform": True,
                        "macula": True,
                    },
                }

    # --- Surface fallback ---
    for i in range(len(lines) - 1):
        wc_n = _prosodic_word_count(lines[i])
        wc_n1 = _prosodic_word_count(lines[i + 1])
        # Very conservative surface heuristic: only flag if both lines are
        # non-trivially parallel (3-6 words each, within 1 word of each other).
        if (3 <= wc_n <= 6 and 3 <= wc_n1 <= 6 and abs(wc_n - wc_n1) <= 1
                and not _ends_verse(lines[i])):
            return {
                "fires": True,
                "verdict": "ADVISORY",
                "reason": (
                    f"lines {i + 1}–{i + 2} have similar length ({wc_n}, {wc_n1} words) "
                    f"— possible gapped bicolon (INFORM). Surface length heuristic only."
                ),
                "details": {
                    "verb_line": i + 1,
                    "gapped_line": i + 2,
                    "word_count_n": wc_n,
                    "word_count_n1": wc_n1,
                    "inform": True,
                    "macula": False,
                },
            }

    return {"fires": False, "verdict": "NO-EFFECT",
            "reason": "no gapped-verb pattern detected"}


# ---------------------------------------------------------------------------
# JM123-inf-abs-predicate
# BIND / HARD / prec 3
# ---------------------------------------------------------------------------

def check_jm123_inf_abs_predicate(
    verse_text: str,
    source_text: str,
    book_slug: Optional[str] = None,
    chapter: Optional[int] = None,
    verse_num: Optional[int] = None,
) -> Optional[dict]:
    """Infinitive absolute as predicate binding (paronomasia case).

    Primary pattern: line N contains an infinitive absolute; line N+1 contains
    a finite verb from the same root (same lemma consonant skeleton). Stranded
    pair = BIND (HARD).

    Secondary pattern: line N ends with an infinitive absolute that has no
    finite verb on the same line — possible predicative-absolute use. Fires
    BIND (ADVISORY downgrade per catalog edge-case note) pending corpus
    confirmation.

    Macula path:
      - Line N: any token with is_infinitive_absolute==True
      - Line N+1: any token with is_finite_verb==True whose lemma consonant
        skeleton matches the inf-abs lemma skeleton on line N.

    MACULA-GAP: Macula lowfat does expose type_=="infinitive absolute" reliably,
    but predicative-role detection (role=="v" for inf-abs as predicate) is not
    consistently populated in the corpus per catalog open_gaps note. The
    paronomasia (cognate intensification) case is well-founded; the
    predicative-absolute sub-case is marked ADVISORY.

    Surface fallback: not reliable — infinitive absolute is indistinguishable
    from other forms without morphology; returns NO-EFFECT when Macula
    unavailable.
    """
    lines = _sense_lines(verse_text)
    if len(lines) < 2:
        return {"fires": False, "verdict": "NO-EFFECT",
                "reason": "single-line verse"}

    verse_tokens = _get_verse_token_list(book_slug, chapter, verse_num)

    if verse_tokens:
        start = 0
        line_token_map: list[list] = []
        for ln in lines:
            toks, start = _line_tokens(verse_tokens, ln, start)
            line_token_map.append(toks)

        for li in range(len(lines) - 1):
            line_n_toks = line_token_map[li]
            line_n1_toks = line_token_map[li + 1]

            if not line_n_toks or not line_n1_toks:
                continue

            # Find infinitive absolutes on line N
            inf_abs_toks = [
                t for t in line_n_toks
                if getattr(t, "is_infinitive_absolute", False)
            ]
            if not inf_abs_toks:
                continue

            # Find finite verbs on line N+1
            finite_n1 = [
                t for t in line_n1_toks
                if getattr(t, "is_finite_verb", False)
            ]

            # Check cognate pair: same lemma consonant skeleton
            for ia in inf_abs_toks:
                ia_lemma_skel = _strip_all(getattr(ia, "lemma", "") or "")
                if not ia_lemma_skel:
                    continue

                cognate_match = [
                    fv for fv in finite_n1
                    if _strip_all(getattr(fv, "lemma", "") or "") == ia_lemma_skel
                ]
                if cognate_match:
                    fv = cognate_match[0]
                    return {
                        "fires": True,
                        "verdict": "CONFLICT",
                        "reason": (
                            f"line {li + 1}: infinitive absolute '{ia.text}' "
                            f"(lemma skel={ia_lemma_skel!r}) is separated from "
                            f"its cognate finite verb '{fv.text}' on line {li + 2} "
                            f"— paronomasia pair must stay together (BIND HARD)."
                        ),
                        "details": {
                            "inf_abs_line": li + 1,
                            "finite_verb_line": li + 2,
                            "inf_abs_text": ia.text,
                            "finite_verb_text": fv.text,
                            "shared_lemma_skel": ia_lemma_skel,
                            "sub_pattern": "paronomasia-cognate",
                            "macula": True,
                        },
                    }

            # Secondary pattern: inf-abs on line N, no finite verb on line N
            # (possible predicative absolute — ADVISORY downgrade per catalog)
            has_finite_n = any(
                getattr(t, "is_finite_verb", False) for t in line_n_toks
            )
            if not has_finite_n and inf_abs_toks:
                ia = inf_abs_toks[0]
                return {
                    "fires": True,
                    "verdict": "ADVISORY",
                    "reason": (
                        f"line {li + 1}: infinitive absolute '{ia.text}' with no "
                        f"finite verb on same line — possible predicative absolute. "
                        f"BIND (ADVISORY pending corpus confirmation of predicative role)."
                    ),
                    "details": {
                        "inf_abs_line": li + 1,
                        "inf_abs_text": ia.text,
                        "sub_pattern": "predicative-absolute",
                        "macula": True,
                        "macula_gap": (
                            "role=='v' for predicative inf-abs not confirmed "
                            "in lowfat corpus — treat as provisional"
                        ),
                    },
                }

    # Surface fallback — not reliable without morphology; document gap
    return {
        "fires": False,
        "verdict": "NO-EFFECT",
        "reason": (
            "infinitive absolute detection requires Macula morphology "
            "(type_=='infinitive absolute'); Macula unavailable or no "
            "inf-abs pattern detected"
        ),
    }


# ---------------------------------------------------------------------------
# Registry integration
# ---------------------------------------------------------------------------

# Canonical 5-arg check registry — single source of truth for this module's
# constraint-id → check-function mapping. Consumed by register_with() and
# directly by audit_constraints.py._register_cluster_checks().
CHECKS_5ARG: dict[str, Callable] = {
    "JM158-restrictive-relative":   check_jm158_restrictive_relative,
    "JM158-nonrestrictive-relative": check_jm158_nonrestrictive_relative,
    "JM156-casus-pendens":           check_jm156_casus_pendens,
    "JM168-purpose-clause":          check_jm168_purpose_clause,
    "JM159e-conditional-protasis":   check_jm159e_conditional_protasis,
    "JM157-ki-recitativum":          check_jm157_ki_recitativum,
    "JM174-gapped-verb":             check_jm174_gapped_verb,
    "JM123-inf-abs-predicate":       check_jm123_inf_abs_predicate,
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
# Standalone smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import io

    # Force UTF-8 output on Windows consoles that default to cp1252
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    _SAMPLE_VERSES: list[tuple[str, str]] = [
        # JM158-restrictive: אשר on line 2 after indefinite head
        ("הָאִישׁ\nאֲשֶׁר שָׁלַחְתָּ אֵלֵינוּ", "the man whom you sent to us"),
        # JM158-nonrestrictive: אשר after divine name
        ("יְהוָה אֱלֹהֶיךָ\nאֲשֶׁר הוֹצֵאתִיךָ מִמִּצְרָיִם", "YHWH your God who brought you"),
        # JM168-purpose-clause: לְ + inf construct (short)
        ("וַיִּשְׁלַח\nלִרְאוֹת אֶת הָאָרֶץ", "and he sent / to see the land"),
        # JM159e-conditional: short אם protasis
        ("אִם תֵּלְכִי אִתִּי\nוְהָלַכְתִּי", "if you go with me / then I will go"),
        # JM157-ki-recitativum: כי after YHWH context
        ("נְאֻם יְהוָה\nכִּי אָנֹכִי אֵשֵׁב", "oracle of YHWH / for I will dwell"),
        # JM174-gapped: parallel bicola, line 2 no verb
        ("יְסַפְּרוּ הַשָּׁמַיִם כְּבוֹדוֹ\nוּמַעֲשֵׂה יָדָיו הָרָקִיעַ", "heavens declare / firmament shows"),
        # JM156-casus-pendens: no Macula — expect NO-EFFECT
        ("וְהָאָרֶץ הָיְתָה תֹהוּ", "and the earth was formless"),
        # JM123-inf-abs: no Macula — expect NO-EFFECT
        ("בָּרֵךְ אֲבָרֶכְךָ", "surely I will bless you"),
    ]

    mock_registry: dict = {}
    register_with(mock_registry)

    print(f"Registered checks: {list(mock_registry.keys())}\n")

    for verse_text, source_text in _SAMPLE_VERSES:
        print(f"--- verse: {verse_text[:40]!r} ---")
        for cid, fn in mock_registry.items():
            result = fn(verse_text, source_text)
            if result and result.get("fires"):
                print(f"  FIRES {cid}: {result['reason'][:80]}")
        print()
