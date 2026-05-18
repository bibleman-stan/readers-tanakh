"""checks_particles.py — Hebrew Constraint Catalog v1: particles + negation cluster.

Implements four constraints from constraints/particles_and_particles.md:

    JM155-discourse-particle      BIND   HARD     prec 3
    JM161-interrogative-particle  BIND   HARD     prec 3
    JM160-negation-scope          BIND   HARD     prec 2
    JM147-vocative-extraclausal   INFORM ADVISORY prec 6

Each check function carries the full Macula-aware signature:

    check_<id>(verse_text, source_text, book_slug, chapter, verse_num) -> Optional[dict]

``register_with(registry)`` wraps each check into the two-arg callable shape
expected by audit_constraints.CHECK_REGISTRY and the existing audit_verse runner,
which does not yet thread Macula coordinates to checks.  When the runner is
upgraded to pass those coordinates, replace the shim with a direct registration
of the full-signature function.

Closed lists are defined inline per spec and drawn from constraint_catalog_v1.md.
Macula queries use get_verse_tokens / match_sense_line_tokens from
validators/_shared/macula_constituents.py when book_slug is provided; the
functions degrade gracefully to surface-form heuristics when coordinates are
absent (book_slug == "" or chapter/verse_num == 0).
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path
from typing import Optional, Callable

# ---------------------------------------------------------------------------
# sys.path bootstrap — mirrors audit_constraints.py's pattern
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT / "validators") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "validators"))

try:
    from _shared.macula_constituents import (
        get_verse_tokens,
        match_sense_line_tokens,
    )
    _MACULA_AVAILABLE = True
except ImportError:
    _MACULA_AVAILABLE = False


# ---------------------------------------------------------------------------
# Text normalization helpers  (must precede closed-list skeleton derivations)
# ---------------------------------------------------------------------------

_HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")
_MAQQEF_RE = re.compile(r"[־]")


def consonant_skel(text: str) -> str:
    """Strip niqqud, te'amim, and maqqef; return bare consonants (NFC-normalized)."""
    s = unicodedata.normalize("NFC", text)
    s = _HEBREW_POINTS_RE.sub("", s)
    s = _MAQQEF_RE.sub("", s)
    return s


# ---------------------------------------------------------------------------
# Closed lemma lists (inline per spec, drawn from constraint_catalog_v1.md)
# ---------------------------------------------------------------------------

DISCOURSE_PARTICLE_LEMMAS = frozenset({
    "הנה",      # behold
    "לכן",      # therefore
    "על־כן",    # therefore (compound)
    "אז",       # then
    "ועתה",     # and now
    "הלא",      # is not?
    "אפוא",     # then/now
})

INTERROGATIVE_LEMMAS = frozenset({
    "מי",       # who
    "מה",       # what
    "איה",      # where
    "איך",      # how
    "למה",      # why
    "מדוע",     # why
    "אן",       # whither
})

NEGATION_LEMMAS = frozenset({
    "לא",       # not
    "אל",       # do not (jussive)
    "אין",      # there is not
    "בל",       # not (poetic)
    "לבלתי",    # so as not
})

INTERJECTION_LEMMAS = frozenset({
    "הוי",      # woe
    "אוי",      # alas
    "אח",       # ah
    "הה",       # ah/oh
})

# Pre-computed consonant-skeleton versions for heuristic surface matching.
_DISCOURSE_SKEL = frozenset(consonant_skel(l) for l in DISCOURSE_PARTICLE_LEMMAS)
_INTERROGATIVE_SKEL = frozenset(consonant_skel(l) for l in INTERROGATIVE_LEMMAS)
_NEGATION_SKEL = frozenset(consonant_skel(l) for l in NEGATION_LEMMAS)
_INTERJECTION_SKEL = frozenset(consonant_skel(l) for l in INTERJECTION_LEMMAS)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _tokens_of_line(verse_tokens: list, line_text: str) -> list:
    """Return Macula Token list for *line_text* within *verse_tokens*.

    Returns [] when Macula is unavailable or the match finds nothing.
    match_sense_line_tokens returns (matched_tokens, next_start_idx).
    """
    if not _MACULA_AVAILABLE or not verse_tokens:
        return []
    matched, _ = match_sense_line_tokens(verse_tokens, line_text)
    return matched


def _has_finite_verb(tokens: list) -> bool:
    """True if any Token in *tokens* is a finite verb."""
    return any(t.is_finite_verb for t in tokens)


def _surface_tokens(line: str) -> list[str]:
    """Split a sense-line into whitespace-delimited surface tokens; strip sof-pasuq."""
    return line.rstrip("׃").split()


# ---------------------------------------------------------------------------
# JM155-discourse-particle
# BIND  HARD  prec 3
# ---------------------------------------------------------------------------

def check_JM155_discourse_particle(
    verse_text: str,
    source_text: str,
    book_slug: str = "",
    chapter: int = 0,
    verse_num: int = 0,
) -> Optional[dict]:
    """BIND HARD prec 3 — Bare discourse-particle indivisibility.

    Fires when:
      (A) A sense-line consists of exactly one token whose lemma is in
          DISCOURSE_PARTICLE_LEMMAS — bare particle with governed clause
          beginning the next line.
      (B) A sense-line has a discourse particle + subject NP (no finite verb)
          while the finite predicate begins the next line — partial
          governed-clause nucleus split.

    Source: JM §155; canon H14 + M3.
    """
    lines = [ln for ln in verse_text.splitlines() if ln.strip()]
    if not lines:
        return {"fires": False, "verdict": "NO-EFFECT", "reason": "empty verse text"}

    use_macula = _MACULA_AVAILABLE and bool(book_slug) and chapter > 0 and verse_num > 0
    verse_tokens: list = []
    if use_macula:
        try:
            verse_tokens = get_verse_tokens(book_slug, chapter, verse_num)
        except Exception:
            use_macula = False

    for i, line in enumerate(lines):
        if use_macula:
            line_tokens = _tokens_of_line(verse_tokens, line)
            if not line_tokens:
                continue

            particle_tokens = [
                t for t in line_tokens
                if t.is_particle
                and consonant_skel(t.lemma or "") in _DISCOURSE_SKEL
            ]
            if not particle_tokens:
                continue

            has_verb = _has_finite_verb(line_tokens)

            # Case A: single-token line is a bare discourse particle.
            if len(line_tokens) == 1:
                return {
                    "fires": True,
                    "verdict": "CONFLICT",
                    "reason": (
                        f"line {i + 1} is a bare discourse particle "
                        f"({line_tokens[0].lemma!r}); governed clause must "
                        f"be on the same line"
                    ),
                    "details": {
                        "line": i + 1,
                        "lemma": line_tokens[0].lemma,
                        "case": "bare-particle",
                    },
                }

            # Case B: particle + NP on this line, finite verb on next line.
            if not has_verb and i + 1 < len(lines):
                next_tokens = _tokens_of_line(verse_tokens, lines[i + 1])
                if _has_finite_verb(next_tokens):
                    return {
                        "fires": True,
                        "verdict": "CONFLICT",
                        "reason": (
                            f"line {i + 1} has discourse particle "
                            f"({particle_tokens[0].lemma!r}) + subject NP "
                            f"but finite predicate is on line {i + 2}; "
                            f"governed-clause nucleus is split"
                        ),
                        "details": {
                            "particle_line": i + 1,
                            "predicate_line": i + 2,
                            "lemma": particle_tokens[0].lemma,
                            "case": "particle-plus-np-split",
                        },
                    }
        else:
            # Surface heuristic fallback.
            surface = _surface_tokens(line)
            if not surface:
                continue
            first_skel = consonant_skel(surface[0])
            if first_skel not in _DISCOURSE_SKEL:
                continue
            # Case A: bare one-token particle line.
            if len(surface) == 1:
                return {
                    "fires": True,
                    "verdict": "CONFLICT",
                    "reason": (
                        f"line {i + 1} is a bare discourse particle "
                        f"({surface[0]!r}); governed clause must be on the "
                        f"same line (surface heuristic — no Macula coords)"
                    ),
                    "details": {
                        "line": i + 1,
                        "token": surface[0],
                        "case": "bare-particle",
                        "heuristic": True,
                    },
                }
            # Case B surface: cannot safely detect finite verb without
            # morphology; skip to avoid false positives.

    return {
        "fires": False,
        "verdict": "NO-EFFECT",
        "reason": "no bare discourse-particle stranding detected",
    }


# ---------------------------------------------------------------------------
# JM161-interrogative-particle
# BIND  HARD  prec 3
# ---------------------------------------------------------------------------

def check_JM161_interrogative_particle(
    verse_text: str,
    source_text: str,
    book_slug: str = "",
    chapter: int = 0,
    verse_num: int = 0,
) -> Optional[dict]:
    """BIND HARD prec 3 — Bare interrogative-particle indivisibility.

    Fires when a sense-line ends with an interrogative particle (lemma in
    INTERROGATIVE_LEMMAS, or Token.type_ == "interrogative") and the line
    contains no finite verb — the governed interrogative clause begins the
    next line, stranding the particle.

    Source: JM §161; canon M3.
    """
    lines = [ln for ln in verse_text.splitlines() if ln.strip()]
    if not lines:
        return {"fires": False, "verdict": "NO-EFFECT", "reason": "empty verse text"}

    use_macula = _MACULA_AVAILABLE and bool(book_slug) and chapter > 0 and verse_num > 0
    verse_tokens: list = []
    if use_macula:
        try:
            verse_tokens = get_verse_tokens(book_slug, chapter, verse_num)
        except Exception:
            use_macula = False

    for i, line in enumerate(lines):
        if use_macula:
            line_tokens = _tokens_of_line(verse_tokens, line)
            if not line_tokens:
                continue

            last = line_tokens[-1]
            last_lemma_skel = consonant_skel(last.lemma or "")
            is_interrogative = (
                (last.is_particle and last_lemma_skel in _INTERROGATIVE_SKEL)
                or last.type_ == "interrogative"
            )
            if not is_interrogative:
                continue

            if not _has_finite_verb(line_tokens):
                return {
                    "fires": True,
                    "verdict": "CONFLICT",
                    "reason": (
                        f"line {i + 1} ends with bare interrogative particle "
                        f"({last.lemma!r}) and has no finite verb; governed "
                        f"interrogative clause begins next line"
                    ),
                    "details": {
                        "line": i + 1,
                        "lemma": last.lemma,
                        "type_": last.type_,
                    },
                }
        else:
            # Surface heuristic: fire only on single-token lines that are a
            # bare interrogative particle, to avoid false positives.
            surface = _surface_tokens(line)
            if not surface:
                continue
            last_skel = consonant_skel(surface[-1])
            if last_skel not in _INTERROGATIVE_SKEL:
                continue
            if len(surface) == 1:
                return {
                    "fires": True,
                    "verdict": "CONFLICT",
                    "reason": (
                        f"line {i + 1} is a bare interrogative particle "
                        f"({surface[-1]!r}); governed clause on next line "
                        f"(surface heuristic — no Macula coords)"
                    ),
                    "details": {
                        "line": i + 1,
                        "token": surface[-1],
                        "heuristic": True,
                    },
                }

    return {
        "fires": False,
        "verdict": "NO-EFFECT",
        "reason": "no bare interrogative-particle stranding detected",
    }


# ---------------------------------------------------------------------------
# JM160-negation-scope
# BIND  HARD  prec 2
# ---------------------------------------------------------------------------

def check_JM160_negation_scope(
    verse_text: str,
    source_text: str,
    book_slug: str = "",
    chapter: int = 0,
    verse_num: int = 0,
) -> Optional[dict]:
    """BIND HARD prec 2 — Negation-particle scope binding.

    Fires when a sense-line ends with a negation particle (lemma in
    NEGATION_LEMMAS) and the line contains no following verb or predicate
    adjective — the negated expression begins the next line, stranding the
    particle and leaving scope undefined.

    Edge-case guards encoded:
    - אֵין + pronominal suffix is a complete predication; if Macula shows
      no separate verb token, the particle alone is bare and fires.
    - Oath-formula context (אַל in an oath) is not detected here;
      the surface check fires conservatively; editorial adjudication per
      JM-oath-formula resolves the edge case.

    Source: JM §160; WO §39.3.3.
    """
    lines = [ln for ln in verse_text.splitlines() if ln.strip()]
    if not lines:
        return {"fires": False, "verdict": "NO-EFFECT", "reason": "empty verse text"}

    use_macula = _MACULA_AVAILABLE and bool(book_slug) and chapter > 0 and verse_num > 0
    verse_tokens: list = []
    if use_macula:
        try:
            verse_tokens = get_verse_tokens(book_slug, chapter, verse_num)
        except Exception:
            use_macula = False

    for i, line in enumerate(lines):
        if use_macula:
            line_tokens = _tokens_of_line(verse_tokens, line)
            if not line_tokens:
                continue

            last = line_tokens[-1]
            last_lemma_skel = consonant_skel(last.lemma or "")
            if not (last.is_particle and last_lemma_skel in _NEGATION_SKEL):
                continue

            # Check whether any other token on this line is a verb, adjective,
            # or participle that could be the negated predicate.
            has_predicate = any(
                t.is_finite_verb or t.pos == "adjective" or t.is_participle
                for t in line_tokens
                if t is not last
            )
            if not has_predicate:
                return {
                    "fires": True,
                    "verdict": "CONFLICT",
                    "reason": (
                        f"line {i + 1} ends with negation particle "
                        f"({last.lemma!r}) with no verb or predicate "
                        f"adjective on the same line; negated expression "
                        f"begins next line"
                    ),
                    "details": {
                        "line": i + 1,
                        "lemma": last.lemma,
                        "pos": last.pos,
                    },
                }
        else:
            # Surface heuristic: single-token negation line only.
            surface = _surface_tokens(line)
            if not surface:
                continue
            last_skel = consonant_skel(surface[-1])
            if last_skel not in _NEGATION_SKEL:
                continue
            if len(surface) == 1:
                return {
                    "fires": True,
                    "verdict": "CONFLICT",
                    "reason": (
                        f"line {i + 1} is a bare negation particle "
                        f"({surface[-1]!r}); negated verb/adjective begins "
                        f"next line (surface heuristic — no Macula coords)"
                    ),
                    "details": {
                        "line": i + 1,
                        "token": surface[-1],
                        "heuristic": True,
                    },
                }

    return {
        "fires": False,
        "verdict": "NO-EFFECT",
        "reason": "no stranded negation particle detected",
    }


# ---------------------------------------------------------------------------
# JM147-vocative-extraclausal
# INFORM  ADVISORY  prec 6
# ---------------------------------------------------------------------------

def check_JM147_vocative_extraclausal(
    verse_text: str,
    source_text: str,
    book_slug: str = "",
    chapter: int = 0,
    verse_num: int = 0,
) -> Optional[dict]:
    """INFORM ADVISORY prec 6 — Vocative and extra-clausal element placement.

    Does not block.  Surfaces for editorial review:
      (A) An interjection lemma (INTERJECTION_LEMMAS / type_=="interjection")
          at line head — woe/lament particle that may need its own line per
          canon H4.
      (B) A proper-name token in address position — proper name adjacent to
          second-person verbal morphology on the same line, suggesting a
          vocative that canon H4 may require on its own line.

    Returns fires=True / verdict="ADVISORY" with a findings list; does not
    mandate any specific edit.

    Source: JM §147; WO §4.7; canon H4.
    """
    lines = [ln for ln in verse_text.splitlines() if ln.strip()]
    if not lines:
        return {"fires": False, "verdict": "NO-EFFECT", "reason": "empty verse text"}

    use_macula = _MACULA_AVAILABLE and bool(book_slug) and chapter > 0 and verse_num > 0
    verse_tokens: list = []
    if use_macula:
        try:
            verse_tokens = get_verse_tokens(book_slug, chapter, verse_num)
        except Exception:
            use_macula = False

    findings: list[dict] = []

    for i, line in enumerate(lines):
        if use_macula:
            line_tokens = _tokens_of_line(verse_tokens, line)
            if not line_tokens:
                continue

            first = line_tokens[0]

            # Pattern A: interjection at clause head.
            if (
                first.is_particle
                and first.type_ == "interjection"
                and consonant_skel(first.lemma or "") in _INTERJECTION_SKEL
            ):
                findings.append({
                    "line": i + 1,
                    "lemma": first.lemma,
                    "pattern": "interjection-at-clause-head",
                })

            # Pattern B: proper name in address position (proper name token +
            # second-person verbal morphology on the same line).
            proper_names = [t for t in line_tokens if t.type_ == "proper"]
            second_person_verbs = [
                t for t in line_tokens
                if t.is_verb and t.person == "second"
            ]
            if proper_names and second_person_verbs:
                findings.append({
                    "line": i + 1,
                    "proper_name": proper_names[0].text,
                    "verb_lemma": second_person_verbs[0].lemma,
                    "pattern": "proper-name-address-position",
                })
        else:
            # Surface heuristic: line begins with a known interjection skeleton.
            surface = _surface_tokens(line)
            if not surface:
                continue
            first_skel = consonant_skel(surface[0])
            if first_skel in _INTERJECTION_SKEL:
                findings.append({
                    "line": i + 1,
                    "token": surface[0],
                    "pattern": "interjection-at-clause-head",
                    "heuristic": True,
                })

    if findings:
        return {
            "fires": True,
            "verdict": "ADVISORY",
            "reason": (
                f"vocative/extra-clausal element detected on "
                f"{len(findings)} line(s); review placement per canon H4"
            ),
            "details": {"findings": findings},
        }

    return {
        "fires": False,
        "verdict": "NO-EFFECT",
        "reason": "no vocative or extra-clausal element detected",
    }


# ---------------------------------------------------------------------------
# Registry integration
# ---------------------------------------------------------------------------

# Ordered map: constraint ID → full-signature check function.
_PARTICLE_CHECKS: dict[str, Callable] = {
    "JM160-negation-scope":         check_JM160_negation_scope,         # prec 2
    "JM155-discourse-particle":     check_JM155_discourse_particle,      # prec 3
    "JM161-interrogative-particle": check_JM161_interrogative_particle,  # prec 3
    "JM147-vocative-extraclausal":  check_JM147_vocative_extraclausal,   # prec 6
}


def register_with(registry: dict) -> None:
    """Register all four particle/negation checks into *registry*.

    The registry (audit_constraints.CHECK_REGISTRY) expects the two-arg
    callable shape::

        check(verse_text: str, source_text: str) -> Optional[dict]

    Each full-signature check is wrapped with a shim that passes empty Macula
    coordinates, so the existing audit_verse runner (which does not yet thread
    book_slug/chapter/verse_num) works unchanged.

    Upgrade path: when audit_verse is extended to pass coordinates, remove the
    shim and register each function from ``_PARTICLE_CHECKS`` directly.
    """
    def _make_shim(f: Callable) -> Callable:
        def shim(verse_text: str, source_text: str) -> Optional[dict]:
            return f(verse_text, source_text, "", 0, 0)
        shim.__name__ = f.__name__ + "_shim"
        shim.__doc__ = f.__doc__
        return shim

    for constraint_id, fn in _PARTICLE_CHECKS.items():
        registry[constraint_id] = _make_shim(fn)
