"""morph_tags.py - Pure parsers over TAHOT morphology tag strings.

A TAHOT morph tag is a slash-separated chain of morpheme codes, prefixed
once with the language marker 'H' (Hebrew). Examples:

    HR/Ncfsa     bound preposition + noun-common-feminine-singular-absolute
    Hc/Vqw3ms    conjunction + verb-qal-wayyiqtol-3-masc-sing
    HVqp3ms      verb-qal-perfect-3-masc-sing
    HNpt         noun-proper-title (used for YHWH)
    HC/Td/Ncfsa  conjunction + definite-article + noun-common-fem-sg-absolute

The 'H' prefix marks Hebrew (vs. Aramaic 'A'); we strip it for parsing.
The HEAD morpheme (the one that determines syntactic class) is the LAST
slash-separated element. Earlier elements are prefixes (conjunction,
article, preposition, etc.) attached to the orthographic word.

These helpers operate on TAG STRINGS ONLY — no Hebrew tokens, no positional
context. Token→tag mapping happens upstream (spec_runner builds the
alignment from v0/morph/ per chapter/verse). When a tag is available these
helpers are authoritative; when not, callers fall back to skel-heuristics
in morphology.py.
"""

from __future__ import annotations

# ──────────────────────────────────────────────────────────────────────
# Tag chain decomposition
# ──────────────────────────────────────────────────────────────────────


def strip_lang_prefix(tag: str) -> str:
    """Strip leading 'H' (Hebrew) or 'A' (Aramaic) language marker.

    >>> strip_lang_prefix('HR/Ncfsa')
    'R/Ncfsa'
    >>> strip_lang_prefix('Hc/Vqw3ms')
    'c/Vqw3ms'
    >>> strip_lang_prefix('Vqp3ms')
    'Vqp3ms'
    """
    if not tag:
        return ""
    if tag[0] in ("H", "A"):
        return tag[1:]
    return tag


def morpheme_chain(tag: str) -> list[str]:
    """Return list of morpheme codes in the tag (lang prefix stripped).

    >>> morpheme_chain('HR/Ncfsa')
    ['R', 'Ncfsa']
    >>> morpheme_chain('Hc/Vqw3ms')
    ['c', 'Vqw3ms']
    >>> morpheme_chain('HVqp3ms')
    ['Vqp3ms']
    >>> morpheme_chain('')
    []
    >>> morpheme_chain('[—]')
    []
    """
    if not tag or tag == "[—]":
        return []
    stripped = strip_lang_prefix(tag)
    return [m for m in stripped.split("/") if m]


def head_morpheme(tag: str) -> str:
    """Return the LAST morpheme in the chain (the syntactic head).

    The head is what determines the orthographic word's grammatical class.
    Prefixes (conjunction, article, preposition) attach to it.

    >>> head_morpheme('HR/Ncfsa')
    'Ncfsa'
    >>> head_morpheme('Hc/Vqw3ms')
    'Vqw3ms'
    >>> head_morpheme('HNpt')
    'Npt'
    >>> head_morpheme('')
    ''
    """
    chain = morpheme_chain(tag)
    return chain[-1] if chain else ""


def first_morpheme(tag: str) -> str:
    """Return the FIRST morpheme (typically a prefix particle).

    Useful for prep/article/conjunction detection on prefixed words.

    >>> first_morpheme('HR/Ncfsa')
    'R'
    >>> first_morpheme('Hc/Vqw3ms')
    'c'
    >>> first_morpheme('HVqp3ms')
    'Vqp3ms'
    """
    chain = morpheme_chain(tag)
    return chain[0] if chain else ""


# ──────────────────────────────────────────────────────────────────────
# Part-of-speech classification (head-morpheme-based)
# ──────────────────────────────────────────────────────────────────────

# TAHOT POS letters at start of a morpheme code:
#   V  verb
#   N  noun (Nc = common; Np = proper)
#   A  adjective
#   P  pronoun (Pp = personal; Pi = interrogative; Pd = demonstrative; Pr = relative)
#   R  preposition
#   D  adverb
#   T  particle (Td = definite article; Tn = negation; Tc = conjunction;
#                Tj = interjection; Tm = demonstrative; To = direct-obj marker;
#                Tr = relative; Te = exhortation; Ti = interrogative)
#   C  coordinating conjunction (waw)
#   c  vav-consecutive (used in Hc/Vqw chain — wayyiqtol marker)
#   S  pronominal suffix (always attached, never standalone tag)
#   d  directional he (e.g., HRd, HNpl/Sd)


def pos_letter(tag: str) -> str:
    """Return the first character of the head morpheme (POS code).

    >>> pos_letter('HR/Ncfsa')
    'N'
    >>> pos_letter('Hc/Vqw3ms')
    'V'
    >>> pos_letter('HNpt')
    'N'
    >>> pos_letter('')
    ''
    """
    head = head_morpheme(tag)
    return head[0] if head else ""


def is_proper_noun(tag: str) -> bool:
    """True if tag head is a proper noun (Np*).

    Used for YHWH (HNpt), personal names (HNpm), place names (HNpl), etc.

    >>> is_proper_noun('HNpt')
    True
    >>> is_proper_noun('HC/Npt')
    True
    >>> is_proper_noun('HNcmsa')
    False
    """
    head = head_morpheme(tag)
    return head.startswith("Np")


# Verb aspects that constitute a FINITE verb (carries inflection for
# person/number/gender). Excludes participles (r/s) and infinitives (c/a).
#   p  perfect (qatal)
#   w  wayyiqtol (consecutive imperfect)
#   q  perfect-with-waw-consecutive (rare, sometimes used for weqatal)
#   i  imperfect (yiqtol)
#   j  jussive (short imperfect)
#   h  cohortative (1st-person volitional)
#   v  imperative
#   u  volitional (TAHOT/OpenScriptures variant for jussive/cohortative-like
#                   short forms — Vqu/Vhu/Vtu/Vpu); occurs in Jonah 1:11,
#                   1:12, 3:8 (`וְיִשְׁתֹּק` Vqu3ms etc.)
_FINITE_VERB_ASPECTS = frozenset({"p", "w", "q", "i", "j", "h", "v", "u"})


def _last_verb_morpheme(tag: str) -> str:
    """Return the last `V*`-headed morpheme in the chain — i.e., the verb
    morpheme itself, ignoring trailing pronominal suffix (`Sp*`) or
    directional-he (`d`) morphemes that come after it.

    Necessary because TAHOT chains for verb+suffix forms place the suffix
    at the END (e.g. `Hc/Vhw3mp/Sp3ms` for `וַיְטִלֻהוּ` — verb buried in
    the middle). Plain `head_morpheme` returns the trailing `Sp*`, which
    misclassifies these as non-verbs.

    Returns empty string if no V-headed morpheme is present.
    """
    for m in reversed(morpheme_chain(tag)):
        if m and m[0] == "V":
            return m
    return ""


def is_finite_verb(tag: str) -> bool:
    """True if tag's verb morpheme has a finite aspect letter.

    Returns False for:
      - Participles (Vqr, Vqs — r=active participle, s=passive participle)
      - Infinitives (Vqc, Vqa — c=construct, a=absolute)
      - Non-verb POS

    >>> is_finite_verb('HVqp3ms')   # qal perfect 3ms — yes
    True
    >>> is_finite_verb('Hc/Vqw3ms') # qal wayyiqtol — yes
    True
    >>> is_finite_verb('HVqv2ms')   # qal imperative — yes
    True
    >>> is_finite_verb('Hc/Vhw3mp/Sp3ms')  # wayyiqtol + suffix DO — yes (verb buried)
    True
    >>> is_finite_verb('HVqu3ms')   # qal volitional (jussive-like) — yes
    True
    >>> is_finite_verb('HVqrmsa')   # qal participle (rāʾā) — no
    False
    >>> is_finite_verb('HR/Vqcc')   # prep + qal infinitive construct — no
    False
    >>> is_finite_verb('HNpt')      # YHWH — definitely no
    False
    """
    verb = _last_verb_morpheme(tag)
    if not verb or len(verb) < 3:
        return False
    return verb[2] in _FINITE_VERB_ASPECTS


def is_wayyiqtol(tag: str) -> bool:
    """True if tag's verb morpheme is wayyiqtol-aspect (V + stem + 'w').

    Wayyiqtol = consecutive imperfect, the narrative-spine verb form of
    biblical Hebrew prose. Aspect letter at index 2 == 'w'.

    Distinct from is_finite_verb (which is True for ALL finite aspects);
    callers needing wayyiqtol-specifically (e.g. multi_wayyiqtol_clause_split)
    should use this rather than skel-heuristic that conflates וְאֵת
    (and-DO-marker) and similar non-verb forms with V+vowel+...

    >>> is_wayyiqtol('Hc/Vqw3ms')      # qal wayyiqtol — yes
    True
    >>> is_wayyiqtol('Hc/Vhw3ms')      # hiphil wayyiqtol — yes
    True
    >>> is_wayyiqtol('Hc/Vhw3mp/Sp3ms') # wayyiqtol + DO-suffix (וַיְטִלֻהוּ) — yes
    True
    >>> is_wayyiqtol('HVqp3ms')        # qal perfect — no
    False
    >>> is_wayyiqtol('HVqi3ms')        # qal imperfect — no
    False
    >>> is_wayyiqtol('Hc/To')          # conjunction + DO-marker (וְאֵת) — no
    False
    >>> is_wayyiqtol('HTo')            # bare DO-marker (אֵת) — no
    False
    """
    verb = _last_verb_morpheme(tag)
    if not verb or len(verb) < 3:
        return False
    return verb[2] == "w"


def is_weqatal(tag: str) -> bool:
    """True if tag is waw-conjunction + perfect-aspect verb (weqatal).

    Weqatal = waw-consecutive perfect. Apodosis-of-protasis or sequential
    modal/future continuation. Signals a NEW clause boundary (like wayyiqtol),
    so callers using next-line tests to detect predicate-of-pronoun vs.
    new-clause should treat weqatal next-line as new-clause.

    Detected by: first morpheme is `c` (waw-conjunction; the lang-prefix
    `H` is stripped by morpheme_chain) AND verb morpheme has aspect letter
    'p' (perfect) or 'q' (weqatal-explicit).

    Both `p` and `q` are accepted: TAHOT inconsistently tags waw-perfect
    forms as either Vqp (plain perfect with conj prefix) or Vqq (weqatal-
    explicit). Functionally indistinguishable in narrative discourse.

    >>> is_weqatal('Hc/Vqq3ms')      # qal weqatal explicit — yes
    True
    >>> is_weqatal('Hc/Vqp3ms')      # qal perfect with vav — yes (functionally weqatal)
    True
    >>> is_weqatal('Hc/VNq3fs')      # niphal weqatal — yes
    True
    >>> is_weqatal('Hc/VHq3ms')      # hiphil weqatal — yes
    True
    >>> is_weqatal('HVqp3ms')        # qal perfect WITHOUT vav — no
    False
    >>> is_weqatal('Hc/Vqw3ms')      # wayyiqtol — no (different aspect)
    False
    >>> is_weqatal('Hc/Vqi3mp')      # waw + yiqtol — no
    False
    """
    morphemes = morpheme_chain(tag)
    if not morphemes or morphemes[0] != "c":
        return False
    verb = _last_verb_morpheme(tag)
    if not verb or len(verb) < 3:
        return False
    return verb[2] in ("p", "q")


def is_construct_state(tag: str) -> bool:
    """True if tag head is a noun in CONSTRUCT state (Nc*c, Np*c).

    Construct state means the noun governs a following genitive ('the
    word OF the LORD' — דְּבַר־יְהוָה — דְּבַר is construct).

    Noun head structure: N + c/p (common/proper) + gender + number + state
    State letter at index 4: a=absolute, c=construct, d=determined.

    >>> is_construct_state('HNcmsc')   # noun-common-masc-sing-construct
    True
    >>> is_construct_state('HNcmsa')   # noun-common-masc-sing-absolute
    False
    >>> is_construct_state('HNcfpc')   # noun-common-fem-pl-construct
    True
    >>> is_construct_state('HNpm')     # proper noun masc (no state) — no
    False
    """
    head = head_morpheme(tag)
    if not head.startswith("N"):
        return False
    if len(head) < 5:
        return False
    return head[4] == "c"


def is_participle(tag: str) -> bool:
    """True if tag head is a participle (Vqr, Vqs, Vnr, Vps, etc.).

    >>> is_participle('HVqrmsa')  # qal active participle masc-sing-abs
    True
    >>> is_participle('HVprfsa')  # piel passive participle fem-sg-abs
    True
    >>> is_participle('HVqp3ms')  # finite — no
    False
    """
    head = head_morpheme(tag)
    if not head or head[0] != "V" or len(head) < 3:
        return False
    return head[2] in ("r", "s")


def is_infinitive(tag: str) -> bool:
    """True if tag head is an infinitive (Vqc, Vqa).

    >>> is_infinitive('HVqcc')      # qal infinitive construct
    True
    >>> is_infinitive('HR/Vqcc')    # prep + inf construct
    True
    >>> is_infinitive('HVqa')       # qal infinitive absolute
    True
    >>> is_infinitive('HVqp3ms')    # finite — no
    False
    """
    head = head_morpheme(tag)
    if not head or head[0] != "V" or len(head) < 3:
        return False
    return head[2] in ("c", "a")
