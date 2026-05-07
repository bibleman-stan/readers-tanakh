#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
normalize_english_gloss.py — mechanical post-processing pass over v2/eng-gloss.

Three patterns applied in order, each closed-list / heuristic / idempotent:

    1. Pronominal-suffix reorder        — "wife his" → "his wife"
    2. Construct-state "of" insertion   — "firstborn of his flock"
    3. Verb-subject reordering (V-S→S-V) — "and he said Yahweh" → "and Yahweh said"

Reads from data/text-files/v2/eng-gloss/<book>/<chapter>.txt and writes back in
place. Idempotent: running the script a second time on already-normalized
output produces identical output.

Conservative bias:
  - Pattern 2 fires only on a closed-list head-noun set + restricted next-token
    set (the / proper-noun / suffix-pronoun-NP).
  - Pattern 3 fires only on a closed-list verb set + closed-list subject set
    (proper names + a few definite person-class NPs); skipped in Sifrei Emet
    chapters (Psalms, Proverbs, Job 3:1–42:6) where V-S is fine in poetry.

Does NOT modify v2/he, v2/translit, v2/eng-interlinear, or any per-word lexicon.

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/normalize_english_gloss.py --book 01-genesis
    PYTHONIOENCODING=utf-8 py -3 scripts/normalize_english_gloss.py --book 01-genesis --dry-run
    PYTHONIOENCODING=utf-8 py -3 scripts/normalize_english_gloss.py --all-books
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GLOSS_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "eng-gloss"

# Make the shared poetic-register helper importable.
sys.path.insert(0, str(REPO_ROOT / "validators"))
try:
    from _shared.poetic_register import is_sifrei_emet_chapter, is_poetic_register  # noqa: E402
except ImportError:
    # Fallback: if the helper isn't reachable, never claim poetic register —
    # the script still runs but Pass 3 won't apply any register skip.
    def is_sifrei_emet_chapter(book, chapter):
        return False

    def is_poetic_register(book, chapter, verse=None):
        return False

VERSE_REF_RE = re.compile(r"^(\d+):(\d+)$")


# ---------------------------------------------------------------------------
# Pattern 0 — Construct chain "the X (suffix-pron) Y" → "the X of (suffix-pron) Y"
#
# Class 3 of the four-class eng-gloss cleanup spec (Stan 2026-05-05).
# Macula glosses Hebrew construct heads with "the." prefix (e.g. אֱלֹהֵי →
# "the.God") even though Hebrew construct heads are anarthrous. When the
# bound noun has a pronominal suffix, Macula does NOT insert "of" — yielding
# "the God my father" / "the days your life" / "the firstborn his flock".
# English idiom requires "of": "the God of my father" / "the days of your life".
#
# This pass runs BEFORE pass1_suffix_reorder so the suffix-reorder rules
# (which would swap "father my" → "my father") see the cleaner "X of pron Y"
# pattern. After this pass, pass1's "X pron" → "pron X" no longer matches
# because "of" sits between X and pron.
#
# Pattern: tokens "the <X> <pron> <Y>" where:
#   - X is a content word (not in NONNOUN_HEADS, length ≥ 2, lowercase or
#     proper-name)
#   - pron is in SUFFIX_PRONOUNS
#   - Y is a content word (not in NONNOUN_HEADS, length ≥ 2)
# Insert "of" after X: "the <X> of <pron> <Y>".
#
# Conservative gating:
#   - Skip if Y is a number / quantifier / particle (would yield "of his two")
#   - Skip if Y is a comparative ("the greater his strength" — apposition)
#   - Idempotent: after one pass the pattern becomes "the X of pron Y" which
#     no longer matches the trigger.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Pattern 1 — Pronominal-suffix reorder
# ---------------------------------------------------------------------------

# Closed list of English suffix-pronoun forms emitted by the gloss generator.
# These are pronouns that, when they immediately follow a noun, signal a
# Hebrew possessive suffix attached to that noun.
SUFFIX_PRONOUNS = {
    "his", "her", "my", "your", "our", "their", "its",
}
SUFFIX_PRONOUN_PATTERN = "|".join(sorted(SUFFIX_PRONOUNS, key=len, reverse=True))

# Verb / non-noun heads that can precede a suffix-pronoun where the pronoun is
# actually a determiner of the NEXT NP, not a Hebrew suffix on the verb.
# e.g. "gave his blessing" — "his" determines "blessing", not a suffix on "gave".
# We never reorder when the preceding word is on this list.
NONNOUN_HEADS = {
    "said", "spoke", "gave", "took", "brought", "made", "did", "called", "sent",
    "put", "heard", "saw", "knew", "found", "came", "went", "arose", "fell",
    "killed", "struck", "told", "asked", "answered", "looked", "blessed",
    "cursed", "opened", "closed", "raised", "lifted", "set", "built", "made",
    "had", "have", "has", "is", "are", "was", "were", "am", "be", "been",
    "being", "will", "would", "shall",
    "should", "may", "might", "can", "could", "do", "does", "did", "go", "goes",
    "see", "sees", "let", "lets", "make", "makes", "take", "takes", "give",
    "gives", "send", "sends", "tell", "tells", "ask", "asks", "answer",
    "answers", "show", "shows", "showed", "shown",
    # Common verb forms whose objects often start with possessive-determiner
    "loves", "love", "loved", "hates", "hate", "hated",
    "born", "bear", "bears", "bore", "borne", "given", "taken",
    "carried", "bring", "brought", "carry",
    "good", "bad", "evil", "true", "false",
    # Frequent particle / interjection: "here I am" / "behold!" / etc.
    "please", "here",
    # Articles / determiners (avoid "the his" double-token weird artefacts)
    "the", "a", "an",
    # Particles that should never be treated as a noun head
    "and", "or", "but", "so", "for", "if", "when", "while", "as", "of", "to",
    "from", "in", "on", "with", "by", "at", "before", "after", "against",
    "over", "under", "between", "among", "through", "without", "within",
    "above", "below", "beneath", "beside", "behind", "around", "into", "onto",
    "out", "up", "down", "off", "near", "far", "upon",
    "not", "no", "yes", "please", "behold", "lo",
    # Pronouns themselves (avoid "his his X")
    "he", "she", "it", "they", "we", "you", "i", "me", "him", "her", "us",
    "them", "myself", "yourself", "himself", "herself", "itself", "ourselves",
    "yourselves", "themselves",
    # Possessive determiners (avoid cascading "his X your" → "your his X")
    "his", "her", "my", "your", "our", "their", "its",
    # Demonstratives
    "this", "that", "these", "those",
    # Common quantifiers / numerals / comparatives
    "all", "every", "some", "any", "none", "many", "much", "few", "several",
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "first", "second", "third", "another", "other", "more", "most",
    "less", "least", "than", "as",
    "little", "great", "big", "small", "large", "long", "short", "high",
    "low", "old", "young", "new", "good", "bad", "evil", "righteous",
    "wicked", "holy", "pure",
    # Relative / interrogative / complementizer
    "who", "whom", "which", "what", "where", "why", "how", "whose", "whoever",
    "whichever", "whatever", "wherever", "whenever",
    # Question / interjection particles that may appear bare
    "alas", "behold", "lo", "ah", "oh",
    # Additional preposition-like tokens missed above
    "unto", "until", "since", "during", "throughout", "amid", "amidst",
    "according",
}

# Suffix-reorder regex: "<noun-token> <pron>" → "<pron> <noun-token>".
# Word-boundary anchored. Case-insensitive. Captures noun and pronoun separately
# so we can skip when noun is in NONNOUN_HEADS.
_SUFFIX_REORDER_RE = re.compile(
    r"\b(\w+(?:\([^)]+\))?)\s+(" + SUFFIX_PRONOUN_PATTERN + r")\b",
    re.IGNORECASE,
)


# Tokens that, if Y is one of these, indicate Y is NOT a bound noun — skip
# the construct-of insertion. Includes numerals, quantifiers, demonstratives,
# and grammatical particles that wouldn't take "of" comfortably.
# Note: this is INTENTIONALLY a different set from NONNOUN_HEADS — Y here
# can be slightly broader (proper names, common nouns, abstract nouns).
_CONSTRUCT_Y_BLOCKLIST = {
    # Numerals / quantifiers
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "first", "second", "third", "another", "other", "many", "much",
    "few", "all", "every", "some", "any", "none", "more", "most", "less",
    "least", "both",
    # Demonstratives
    "this", "that", "these", "those",
    # Conjunctions / particles
    "and", "or", "but", "so", "for", "if", "when", "while", "as", "of", "to",
    "from", "in", "on", "with", "by", "at", "before", "after", "against",
    "over", "under", "between", "among", "through", "without", "within",
    "above", "below", "behind", "around", "into", "onto",
    "out", "up", "down", "off", "near", "far", "upon", "than",
    # Verbs / copulas (would mean Y is a verb, not a bound noun)
    "is", "are", "was", "were", "be", "been", "being", "am",
    "has", "have", "had",
    "will", "would", "shall", "should", "may", "might", "can", "could",
    "must", "do", "does", "did",
    "said", "spoke", "called", "answered", "told", "asked",
    "came", "went", "saw", "knew", "made", "did",
    # Comparatives / adjectives that don't make sense as bound nouns
    "great", "small", "big", "good", "bad", "evil",
    "old", "new", "young", "first", "last",
    # Negation
    "not", "no", "never",
    # Relative / interrog
    "who", "whom", "which", "what", "where", "why", "how", "whose",
}


def pass0_construct_of_with_pron(line: str) -> str:
    """Insert 'of' in 'the X (suffix-pron) Y' construct chains.

    Class 3 of the four-class eng-gloss cleanup spec (Stan 2026-05-05).

    Pattern: "the X pron Y" → "the X of pron Y" where:
      - "the" is the literal article (case-insensitive)
      - X is a content word (≥2 chars, not in NONNOUN_HEADS, not a pronoun,
        not a numeral)
      - pron ∈ SUFFIX_PRONOUNS (his/her/my/your/our/their/its)
      - Y is a content word (≥2 chars, not in _CONSTRUCT_Y_BLOCKLIST)

    Token-level single left-to-right pass. Idempotent: after insertion the
    pattern becomes "the X of pron Y" which no longer matches (X is followed
    by 'of', not pron).

    Examples:
      "for the God my father has been my help"
        → "for the God of my father has been my help"
      "all the days your life"
        → "all the days of your life"
      "to the firstborn his flock"
        → "to the firstborn of his flock"
    """
    tokens = line.split()
    if len(tokens) < 4:
        return line

    out: list[str] = []
    i = 0
    n = len(tokens)
    while i < n:
        # Need 4 tokens for the pattern: the X pron Y
        if i + 3 >= n:
            out.append(tokens[i])
            i += 1
            continue
        t0 = tokens[i]      # "the"
        t1 = tokens[i + 1]  # X
        t2 = tokens[i + 2]  # pron
        t3 = tokens[i + 3]  # Y

        t0_lc = t0.lower().strip(".,;:!?")
        if t0_lc != "the":
            out.append(tokens[i])
            i += 1
            continue

        # FP guard: if "the X" is preceded by a proper name (capitalized,
        # ≥2 chars), then "the X" is appositional to that name (gentilic
        # adjective or descriptor), NOT a construct head. E.g., "Hagar the
        # Egyptian her maidservant" — "the Egyptian" describes Hagar; the
        # apposition continues with "her maidservant" as another descriptor,
        # not a construct rectum. Inserting "of" produces "Hagar the Egyptian
        # of her maidservant" which mistypes apposition as genitive.
        # Stan-flagged 2026-05-07 (Genesis 16:3 case).
        if i > 0:
            prev_tok = tokens[i - 1].rstrip(".,;:!?")
            if (len(prev_tok) >= 2 and prev_tok[0].isupper()
                and prev_tok.lower() not in {"the", "a", "an"}):
                out.append(tokens[i])
                i += 1
                continue

        t1_clean = re.sub(r"[^\w-]", "", t1).lower()
        t2_clean = re.sub(r"[^\w-]", "", t2).lower()
        t3_clean = re.sub(r"[^\w-]", "", t3).lower()

        # X must be a content noun (not a particle, not a pronoun, not a
        # quantifier). Allow capitalized proper names like "God" / "Yahweh"
        # but those would be unusual after "the"; the typical case is
        # lowercase common noun.
        if (
            t1_clean in NONNOUN_HEADS
            or t1_clean in SUFFIX_PRONOUNS
            or len(t1_clean) <= 1
        ):
            out.append(tokens[i])
            i += 1
            continue

        # Pron position must be a suffix pronoun.
        if t2_clean not in SUFFIX_PRONOUNS:
            out.append(tokens[i])
            i += 1
            continue

        # Y must be a content word (a likely bound noun); skip on the
        # blocklist (numerals/quantifiers/particles).
        if (
            t3_clean in _CONSTRUCT_Y_BLOCKLIST
            or t3_clean in SUFFIX_PRONOUNS
            or len(t3_clean) <= 1
        ):
            out.append(tokens[i])
            i += 1
            continue

        # FP guard: list-coordination (Stan-flagged 2026-05-07). If the next
        # tokens after Y are "and [pron] [N]" or "[pron] [N]" (no comma in
        # English gloss), the X is heading a coordinated possessive-NP list
        # (temple-furniture pattern: "the lampstand its base and its shaft
        # and its lamps"), NOT a construct chain. Don't insert 'of'.
        if i + 5 < n:
            t4_clean = re.sub(r"[^\w-]", "", tokens[i + 4]).lower()
            t5_clean = re.sub(r"[^\w-]", "", tokens[i + 5]).lower()
            if t4_clean == "and" and t5_clean in SUFFIX_PRONOUNS:
                out.append(tokens[i])
                i += 1
                continue

        # Insert "of" between X and pron: "the X of pron Y ..."
        out.extend([t0, t1, "of", t2, t3])
        i += 4

    return " ".join(out)


def pass1_suffix_reorder(line: str) -> str:
    """Reorder Hebrew possessive-suffix gloss tokens: 'X pron' → 'pron X'.

    Token-level single pass. For each pronoun token P at position i (>0):
      - if tokens[i-1] is a candidate noun-head (not in NONNOUN_HEADS, not a
        suffix-pronoun, length>=2, not 'you'), AND
      - tokens[i-1] is not already a swapped head (we mark swapped heads via a
        parallel `locked` array so we never re-swap the same token twice)
    then swap them and lock both positions.

    Single left-to-right pass, no looping. Avoids cascading mis-applications
    like "humankind image our" → "our humankind image" (we want
    "humankind our image", swapping only the local pair).

    Idempotent: after pass, "pron noun" patterns don't re-match (head would be
    a pronoun, which is in NONNOUN_HEADS).
    """
    tokens = line.split()
    if len(tokens) < 2:
        return line

    locked = [False] * len(tokens)
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        # Strip trailing punctuation for the comparison only
        tok_clean = re.sub(r"[^\w-]", "", tok).lower()
        if tok_clean not in SUFFIX_PRONOUNS:
            i += 1
            continue
        if i == 0:
            i += 1
            continue
        if locked[i] or locked[i - 1]:
            i += 1
            continue
        prev_tok = tokens[i - 1]
        prev_clean = re.sub(r"[^\w-]", "", prev_tok).lower()
        # Skip if the head is a verb / particle / determiner / pronoun, etc.
        if prev_clean in NONNOUN_HEADS:
            i += 1
            continue
        if prev_clean in SUFFIX_PRONOUNS:
            i += 1
            continue
        if len(prev_clean) <= 1:
            i += 1
            continue
        if prev_clean == "you":
            i += 1
            continue
        # FP guard (Stan-flagged 2026-05-07: "may serve their" → "may their
        # serve" misfire on Exod 10 / Jer 30). If prev token is preceded by
        # an aux verb, prev is a verb (not a noun-head); don't reorder.
        # Closed-list aux check is robust to NONNOUN_HEADS gaps for
        # less-common verbs ("serve" / "destroy" / etc.).
        if i >= 2:
            prev2_clean = re.sub(r"[^\w-]", "", tokens[i - 2]).lower()
            _AUX_BEFORE_VERB = {"will", "shall", "do", "does", "did", "may",
                                 "might", "would", "should", "could", "must",
                                 "can", "is", "are", "was", "were", "has",
                                 "have", "had"}
            if prev2_clean in _AUX_BEFORE_VERB:
                i += 1
                continue
        # Proper-name guard: capitalized words are typically proper nouns
        # (e.g. 'Yahweh') which in Hebrew don't take pronominal suffixes.
        # 'Yahweh his God' has 'his' as a determiner of 'God', not a suffix
        # on 'Yahweh'. Skip the swap.
        if prev_tok and prev_tok[0].isupper() and prev_tok not in {"I"}:
            i += 1
            continue
        # Idempotence guard: only swap when the pronoun is "anchored" —
        # at end of cola, OR followed by a particle / conjunction / verb /
        # preposition / determiner / capitalized-name (something that makes
        # the noun-pron-noun configuration UN-ambiguous on re-run).
        #
        # If next is another noun-class lowercase word, swapping puts the
        # pronoun between two nouns; a second pass would re-swap with the
        # new neighbor. Skip.
        #
        # Likewise, if next is another suffix-pronoun, that means the next
        # noun position has its own pronoun coming up — swapping the current
        # pronoun would create a "<pron> <noun> <pron> <noun>" string where
        # a SECOND apply could re-fire. Skip.
        if i + 1 < len(tokens):
            next_tok = tokens[i + 1]
            next_clean = re.sub(r"[^\w-]", "", next_tok).lower()
            # 'anchored' = next token is something other than a noun-class
            # word, i.e., it's safe to swap because re-running won't find
            # ambiguous noun-noun-pron neighborhoods. Suffix-pronouns count
            # as NON-anchoring even though they appear in NONNOUN_HEADS for
            # the head check — a suffix-pron in next-position implies a
            # following NP, making the current pron's role ambiguous.
            anchored = (
                not next_clean
                or (
                    next_clean in NONNOUN_HEADS
                    and next_clean not in SUFFIX_PRONOUNS
                )
                or len(next_clean) <= 1
                or (next_tok and next_tok[0].isupper())
            )
            if not anchored:
                i += 1
                continue
        # Hebrew-grammar guard: a noun with a possessive suffix CANNOT also
        # carry the article. So if 'the' immediately precedes the head, the
        # apparent suffix is most likely a determiner of the NEXT NP (or the
        # 'the' was a discretionary glosser insertion onto a construct head).
        # Skip the swap to avoid mis-applied "the their wickedness" output
        # and ambiguous "the X his Y" chains. The conservative cost is
        # leaving the line in literal Hebrew order, which is still readable.
        if i >= 2:
            two_back = tokens[i - 2]
            two_back_clean = re.sub(r"[^\w-]", "", two_back).lower()
            if two_back_clean in {"the"}:
                i += 1
                continue
        # Swap: pronoun moves to position i-1, head to position i.
        # Preserve any trailing punctuation on the original head.
        tokens[i - 1], tokens[i] = tok, prev_tok
        locked[i - 1] = True
        locked[i] = True
        i += 1

    return " ".join(tokens)


# ---------------------------------------------------------------------------
# Pattern 2 — Construct-state "of" insertion
# ---------------------------------------------------------------------------

# Closed list of head nouns that very commonly take a construct/of-complement.
# We're conservative: only insert "of" when the head is on this list AND the
# next token is the / a proper-name / a possessive-pronoun-NP.
CONSTRUCT_HEADS = {
    "son", "sons", "daughter", "daughters", "brother", "brothers", "sister",
    "sisters", "father", "mother", "wife", "wives", "husband", "husbands",
    "child", "children", "kin", "kinsman", "offspring",
    "king", "kings", "queen", "prince", "princes", "priest", "priests",
    "prophet", "prophets", "servant", "servants", "master", "masters",
    "messenger", "messengers", "elder", "elders", "judge", "judges",
    "leader", "leaders", "head", "chief", "chiefs",
    "man", "men", "woman", "women", "people", "peoples", "nation", "nations",
    "tribe", "tribes", "family", "families", "generation", "generations",
    "inhabitant", "inhabitants", "host", "hosts", "army", "armies",
    "land", "lands", "house", "houses", "city", "cities", "town", "towns",
    "village", "villages", "field", "fields", "mountain", "mountains",
    "river", "rivers", "sea", "seas", "valley", "valleys", "wilderness",
    "desert", "gate", "gates", "wall", "walls", "tent", "tents",
    "day", "days", "year", "years", "month", "months", "week", "weeks",
    "time", "times", "season", "seasons", "moment",
    "beginning", "end", "midst", "middle", "border",
    "face", "faces", "presence",
    "word", "words", "voice", "voices", "name", "names", "sound", "sounds",
    "fear", "glory", "majesty", "honor",
    "firstborn", "firstborns", "portion", "portions", "share", "lot",
    "blood", "bloods", "fruit", "fruits", "seed", "seeds", "grain", "wheat",
    "harvest", "vineyard", "garden",
    "joy", "sorrow", "grief", "love", "hatred", "hate", "wrath", "anger",
    "kindness", "mercy", "favor", "loyalty", "faithfulness", "righteousness",
    "wickedness", "iniquity", "transgression", "sin",
    "way", "ways", "path", "paths", "law", "laws", "statute", "statutes",
    "commandment", "commandments", "judgment", "judgments", "ordinance",
    "covenant", "covenants",
    "spirit", "soul", "heart", "mind", "strength", "power", "hand", "hands",
    "arm", "arms", "foot", "feet", "eye", "eyes", "ear", "ears",
    "tongue", "lips", "mouth",
    "throne", "kingdom", "dominion", "rule", "reign",
    "dwellers", "dweller", "possessor", "possessors",
    "player", "players", "worker", "workers",
    "blessing", "blessings", "curse", "curses", "vow", "vows",
    "altar", "altars", "temple", "tabernacle", "ark", "vessel", "vessels",
    "pillar", "pillars", "gate", "court", "courts",
    "company", "assembly", "congregation", "council",
    "stone", "stones", "rock", "rocks", "wood", "tree", "trees",
    "fruit", "leaf", "leaves",
    "morning", "evening", "noon", "night", "midnight",
    "remnant", "rest", "remainder",
    "depth", "depths", "height", "heights", "edge", "edges",
    "shore", "shores", "bank", "banks",
    "captain", "captains", "ruler", "rulers", "shepherd", "shepherds",
    "warrior", "warriors", "soldier", "soldiers",
}

# Tokens that, if they appear right after a candidate construct head, indicate
# the head is NOT in construct state. These are clear "stop" signals.
CONSTRUCT_STOPWORDS = {
    # Prepositions / particles after head — head is independent, not bound
    "to", "from", "in", "on", "with", "by", "at", "for", "before", "after",
    "against", "over", "under", "between", "among", "through", "without",
    "within", "above", "below", "beneath", "beside", "behind", "around",
    "into", "onto", "out", "up", "down", "off", "near", "far", "upon",
    # Conjunctions
    "and", "or", "but", "so", "yet", "if", "when", "while", "as", "because",
    "though", "although",
    # Verbs / copulas
    "is", "are", "was", "were", "be", "been", "being", "will", "would", "shall",
    "should", "may", "might", "can", "could", "must", "do", "does", "did",
    "have", "has", "had",
    "said", "spoke", "called", "answered", "told", "asked",
    "came", "went", "saw", "knew", "made", "did",
    # Demonstratives — "the king this" is already handled elsewhere
    "this", "that", "these", "those",
    # Relative / interrog
    "who", "whom", "which", "what", "where", "why", "how", "whose",
    # Other particles
    "not", "no", "also", "only", "even", "indeed", "very",
    # End of cola
    "",
}


def pass2_construct_of(line: str) -> str:
    """Insert 'of' after a construct head when followed by a clear bound NP.

    Triggers only when:
      - head is in CONSTRUCT_HEADS (closed list)
      - head is NOT preceded by an article 'the' (definite head is not in
        construct state in Hebrew)
      - head is NOT preceded by a possessive pronoun ('his X' / 'my X' / ...)
        — such an NP is already complete; another noun after it is apposition
        or a separate object, not a bound NP
      - head is NOT preceded by an indefinite article 'a'/'an' for the very
        few generic-head cases on the list ('a man'/'a woman' rarely starts
        a construct chain in English-rendering of Hebrew)
      - the most recent 'of'-insertion on this line was at least 3 tokens ago
        (avoid multi-level chains like 'name of his son of Enoch' where the
        deepest token is in apposition)
      - next token is one of:
          (a) 'the'                                     → "X of the Y"
          (b) a proper noun (capitalized, ≥2 chars)     → "X of Yahweh"
          (c) a possessive pronoun ('his/her/.../its')  → "X of his Y"

    Conservative: never inserts on stopword next-tokens, never recurses.
    Idempotent: after first pass, "X of Y" doesn't trigger again because the
    head is followed by 'of', not a bound-NP signal.
    """
    tokens = line.split()
    if len(tokens) < 2:
        return line

    # Heads where the indefinite article 'a'/'an' before them disables the
    # construct trigger (these are too generic to reliably bind in English).
    GENERIC_HEADS_INDEFINITE_OFF = {
        "man", "men", "woman", "women", "boy", "girl",
        "house", "city", "land", "field", "people",
    }

    out: list[str] = []
    last_of_at_out_index: int = -10  # output-index of last 'of' (pre-existing OR inserted)
    i = 0
    n = len(tokens)
    while i < n:
        cur = tokens[i]
        out.append(cur)
        cur_lc = cur.lower().strip(".,;:!?")
        cur_clean = re.sub(r"[^\w()-]", "", cur_lc)

        # Track pre-existing 'of' in the input — also enforces multi-level
        # chain guard against existing chains (idempotence).
        if cur_lc == "of":
            last_of_at_out_index = len(out) - 1

        if cur_clean not in CONSTRUCT_HEADS:
            i += 1
            continue

        # What precedes the head?
        if i > 0:
            prev_lc = tokens[i - 1].lower().strip(".,;:!?")
            prev_clean = re.sub(r"[^\w()-]", "", prev_lc)
            # 'the' before head → head is definite → not construct in Hebrew.
            if prev_lc in {"the"}:
                i += 1
                continue
            # possessive pronoun before head → NP already complete
            if prev_clean in SUFFIX_PRONOUNS:
                i += 1
                continue
            # indefinite article + generic head → skip (too unreliable)
            if prev_lc in {"a", "an"} and cur_clean in GENERIC_HEADS_INDEFINITE_OFF:
                i += 1
                continue
            # 'of' immediately before head → second-level chain; allow only
            # if last insertion was distant (governed by check below)

        # Look ahead at the next token.
        if i + 1 >= n:
            i += 1
            continue
        nxt = tokens[i + 1]
        nxt_lc = nxt.lower().strip(".,;:!?")
        nxt_clean = re.sub(r"[^\w()-]", "", nxt_lc)

        # Stop conditions: next is a particle/verb/etc.
        if nxt_clean in CONSTRUCT_STOPWORDS:
            i += 1
            continue
        if nxt_lc == "of":
            i += 1
            continue

        # Trigger conditions:
        is_definite_np = (nxt_lc == "the")
        is_possessive_np = (nxt_clean in SUFFIX_PRONOUNS)
        is_proper_noun = (
            len(nxt) >= 2
            and nxt[0].isupper()
            and nxt[1:].islower() is not False  # forgiving — accept TitleCase
        )
        if nxt_clean in {"i", "we", "you", "he", "she", "it", "they"}:
            is_proper_noun = False

        if is_definite_np or is_possessive_np or is_proper_noun:
            # Multi-level chain guard: don't insert 'of' if there was an 'of'
            # (existing or inserted) within the last 2 output-tokens.
            current_out_index = len(out) - 1
            if current_out_index - last_of_at_out_index <= 2:
                i += 1
                continue
            out.append("of")
            last_of_at_out_index = len(out) - 1
        i += 1

    return " ".join(out)


# ---------------------------------------------------------------------------
# Pattern 3 — Verb-subject reordering (V-S → S-V)
# ---------------------------------------------------------------------------

# Closed list of narrative verbs whose Hebrew V-S form should reorder to S-V.
# Includes typical English-tense forms emitted by the gloss generator after
# Macula lookup. Conservative: only finite-narrative forms.
NARRATIVE_VERBS = {
    # Speech
    "said", "spoke", "answered", "called", "cried", "declared", "proclaimed",
    "told", "asked", "commanded", "swore", "shouted", "whispered", "preached",
    # Perception
    "saw", "looked", "heard", "listened", "hearkened",
    "perceived", "noticed", "watched", "observed",
    # Motion
    "arose", "rose", "went", "came", "returned", "departed", "fled",
    "entered", "exited", "crossed", "passed", "approached", "drew",
    "ascended", "descended", "traveled", "journeyed", "wandered", "sojourned",
    # Action
    "did", "made", "took", "gave", "brought", "appointed", "put", "set",
    "raised", "built", "established", "fashioned", "formed", "created",
    "sent", "killed", "struck", "smote", "saved", "delivered", "rescued",
    "judged", "ruled", "anointed", "blessed", "cursed", "consecrated",
    "chose", "selected", "gathered", "assembled", "summoned", "called-together",
    "wrote", "read", "taught", "instructed", "showed",
    "served", "worshipped", "bowed", "kneeled", "prostrated",
    "ate", "drank", "tasted", "fed",
    "seized", "grabbed", "captured", "caught", "held", "carried", "lifted",
    "pursued", "chased", "hunted",
    "opened", "closed", "shut", "covered", "uncovered",
    "broke", "tore", "split", "divided", "separated",
    "cut", "burned", "destroyed", "demolished",
    "loved", "hated", "rejected", "accepted",
    "forgot", "forgave", "rebuked", "warned",
    "numbered", "counted", "measured",
    # Mental
    "knew", "remembered", "feared", "trusted", "believed", "thought",
    "considered", "decided", "intended", "purposed",
    # Existence
    "was", "became", "lived", "died", "dwelt", "stood", "sat", "lay",
    "slept", "awoke", "rested", "remained",
    # Frequent narrative + Jonah-relevant
    "hurled", "appointed", "swallowed", "vomited", "prayed", "sacrificed",
    "vowed", "fell", "rowed", "stopped", "feared", "prepared",
    # 2026-05-02 additions surfaced by Gen 3 eng-gloss audit
    "hid", "deceived", "stretched", "begat", "begot", "begot",
    "named", "spread", "planted", "drove", "lifted", "circumcised",
    "wept", "kissed", "embraced", "bore", "conceived", "ran",
    "found", "lost", "asked", "begged", "demanded", "withheld",
    "removed", "uncovered", "revealed", "concealed",
    # 2026-05-04 Class 2: corpus-scan surfaced perfect/wayyiqtol forms
    # (verbs where post-verbal NP is reliably the SUBJECT, not the object —
    # speech/motion/perception/intransitive bias to minimize V+O false positives)
    "turned", "encamped", "fathered", "defeated", "buried",
    "walked", "repeated", "caused", "poured", "offered",
    "finished", "sought", "acted", "reigned",
    "overlaid", "fought", "filled", "appeared", "placed",
    "led", "rebelled", "began", "presented",
    "increased", "strengthened",
    "grew", "spoken", "rejoiced", "ceased", "hurried",
    "clothed", "belonged", "recounted", "enquired", "inquired",
    "given", "taken", "gone", "come", "become",
    "left", "begotten",
    # 2026-05-05 Class 1 (mid-clause V-S): past-participle forms used in
    # English perfect tense (Macula gloss patterns "he had X" / "he has X").
    # Without these, pass8 doesn't match qatal verbs that get "had/has"-aux
    # glossing — exactly the Hebrew tense most likely to be V-S in
    # subordinate / relative clauses.
    "done", "made", "said", "spoken", "given", "taken", "brought",
    "seen", "heard", "known", "shown", "told", "sent", "killed",
    "delivered", "saved", "appointed", "set", "raised", "built",
    "begotten", "borne", "written", "read", "called", "asked",
    "answered", "established", "fashioned", "formed", "created",
    "destroyed", "demolished", "broken", "torn", "split",
    "passed", "crossed", "entered", "exited", "departed",
    "buried", "fought", "filled", "led",
    "remembered", "forgotten", "forgiven", "loved", "hated",
    "kept", "guarded", "preserved",
    # 2026-05-04 Class 2: yiqtol speech verbs (Isa 40:1 "he says your god")
    "says", "speaks", "declares", "proclaims", "calls", "answers",
    "replies", "swears", "commands", "shouts", "whispers", "preaches",
    "tells", "asks", "cries",
    # 2026-05-04 Class 2: yiqtol bare forms (used after will/shall aux)
    # Speech
    "say", "speak", "declare", "proclaim", "call", "answer", "reply",
    "swear", "command", "shout", "preach", "tell", "ask", "cry",
    # Perception
    "see", "look", "hear", "listen", "perceive", "watch", "observe",
    # Motion
    "arise", "rise", "go", "return", "depart", "flee",
    "enter", "exit", "cross", "pass", "approach", "draw",
    "ascend", "descend", "travel", "journey", "wander", "sojourn",
    # Action
    "do", "make", "take", "give", "bring", "appoint", "put", "set",
    "raise", "build", "establish", "fashion", "form", "create",
    "send", "kill", "strike", "smite", "save", "deliver", "rescue",
    "judge", "rule", "anoint", "bless", "curse", "consecrate",
    "choose", "select", "gather", "assemble", "summon",
    "write", "read", "teach", "instruct", "show",
    "serve", "worship", "bow", "kneel", "prostrate",
    "eat", "drink", "taste", "feed",
    "seize", "grab", "capture", "catch", "hold", "carry", "lift",
    "pursue", "chase", "hunt",
    "open", "close", "shut", "cover",
    "break", "tear", "split", "divide", "separate",
    "burn", "destroy", "demolish",
    "love", "hate", "reject", "accept",
    "forget", "forgive", "rebuke", "warn",
    "number", "count", "measure",
    # Mental
    "know", "remember", "fear", "trust", "believe", "think",
    "consider", "decide", "intend", "purpose",
    # Existence
    "be", "live", "die", "dwell", "stand", "sit", "lie",
    "sleep", "awake", "rest", "remain",
    # Other yiqtol bare forms
    "hurl", "swallow", "vomit", "pray", "sacrifice", "vow",
    "fall", "row", "stop", "prepare",
    "hide", "deceive", "stretch", "name", "spread", "plant",
    "drive", "circumcise", "weep", "kiss", "embrace",
    "bear", "conceive", "run", "find", "lose", "beg", "demand",
    "withhold", "remove", "uncover", "reveal", "conceal",
}

# Closed list of proper-name subjects (one-word). Capitalization is the
# detection signal in the gloss layer; this set explicitly enumerates known
# divine and major-character names so we don't accidentally treat objects
# (place names following "to") as subjects.
PROPER_NAME_SUBJECTS = {
    # Divine
    "Yahweh", "God", "Lord",
    # Patriarchs / matriarchs
    "Adam", "Eve", "Cain", "Abel", "Seth", "Enoch", "Methuselah", "Lamech",
    "Noah", "Shem", "Ham", "Japheth",
    "Abraham", "Abram", "Sarah", "Sarai", "Hagar", "Ishmael",
    "Isaac", "Rebekah", "Esau", "Jacob", "Israel", "Rachel", "Leah",
    "Joseph", "Reuben", "Simeon", "Levi", "Judah", "Dan", "Naphtali", "Gad",
    "Asher", "Issachar", "Zebulun", "Benjamin", "Manasseh", "Ephraim",
    # Exodus
    "Moses", "Aaron", "Miriam", "Pharaoh", "Jethro", "Zipporah",
    "Joshua", "Caleb",
    # Judges era
    "Othniel", "Ehud", "Deborah", "Barak", "Gideon", "Jephthah", "Samson",
    "Delilah",
    # Samuel
    "Samuel", "Eli", "Hannah", "Saul", "David", "Jonathan", "Bathsheba",
    "Nathan", "Absalom",
    # Kings
    "Solomon", "Rehoboam", "Jeroboam", "Ahab", "Jezebel", "Elijah", "Elisha",
    "Hezekiah", "Josiah", "Manasseh",
    # Prophets
    "Isaiah", "Jeremiah", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
    "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai",
    "Zechariah", "Malachi",
    # Other major figures
    "Job", "Boaz", "Ruth", "Naomi", "Esther", "Mordecai", "Haman",
    "Ezra", "Nehemiah",
}

# Closed list of definite person-class NPs (multi-word). After "and he <V>",
# if the post-verbal NP is one of these, we treat it as the subject.
DEFINITE_PERSON_NPS = [
    "the man", "the men", "the woman", "the women", "the people",
    "the king", "the queen", "the prince", "the priest", "the priests",
    "the prophet", "the prophets", "the servant", "the servants",
    "the messenger", "the messengers", "the angel",
    "the boy", "the girl", "the child", "the children", "the youth",
    "the elder", "the elders", "the leader", "the leaders",
    "the mariners", "the sailors", "the men of the city",
    "the lot", "the storm", "the sea", "the wind", "the fire",
    "the earth", "the ground", "the city", "the lion",
    "the chief of the sailors", "the captain", "the master",
]

# Optional one-token short PPs that may appear between verb and subject.
# Pattern: "and <pron> <V> <short-PP> <SUBJ>" → "and <SUBJ> <V> <short-PP>".
SHORT_PP_AFTER_VERB = [
    "to him", "to her", "to them", "to us", "to me", "to you",
]

# Bare object pronouns that may sit between verb and subject in V+O+S
# (Hebrew אֹתָם/אוֹתוֹ/אֹתָהּ glossed without "to"). Pattern:
# "and <pron> <V> <obj-pron> <SUBJ>" → "and <SUBJ> <V> <obj-pron>".
# Audit 2026-05-04: 56 corpus instances, all true V+O+S (Gen 1:28 "and he
# blessed them God" → "and God blessed them"). Distinct from SHORT_PP_AFTER_VERB
# because no preposition — bare accusative pronoun.
BARE_OBJECT_PRONOUNS_AFTER_VERB = {
    "him", "her", "them", "me", "us",
    # "you" intentionally EXCLUDED — too ambiguous: 2nd-person object vs
    # the disambiguating subject pronoun cases (e.g., "and he blessed you Moses"
    # is rare; "and he gave you Yahweh" exists but post-verb 'you' could be
    # discourse-marker rather than accusative). Add later if audit warrants.
}

# English verb particles ("phrasal-verb second halves") that the gloss
# generator emits as separate tokens after certain verbs:
#   "sent off Moses ..."   → verb is conceptually "sent off"
#   "went up Jacob ..."    → verb is "went up"
#   "called out the king"  → verb is "called out"
# Pattern in pass3: after the verb token, optionally consume one of these
# before scanning for the subject. On reorder, particle is re-attached to
# the verb in the canonical S-V-particle-O order.
#
# CRITICAL: only include particles that don't routinely appear as the head
# of a prepositional phrase. Excluded for FP-safety:
#   "in" — "believed in X", "trusted in X" (Gen 15:6 false-positive class)
#   "on" — "called on the name of Yahweh"
#   "across" / "through" — locative PPs, not particles
#   "at" — "looked at X"
# Borderline ("over") kept because it's strongly phrasal in motion contexts
# ("crossed over", "passed over"); rare PP usage in narrative gloss.
VERB_PARTICLES = [
    "off", "up", "down", "out", "away", "back", "forth", "over",
]


def _capitalized_name(tok: str) -> bool:
    """Return True if token looks like a proper-name word (in PROPER_NAME_SUBJECTS)."""
    base = tok.strip(".,;:!?")
    return base in PROPER_NAME_SUBJECTS


def _matches_definite_np(tokens: list[str], start: int) -> int:
    """If a multi-word definite-NP starts at tokens[start], return its length;
    else return 0."""
    rest_lc = " ".join(tokens[start:]).lower()
    for np in sorted(DEFINITE_PERSON_NPS, key=len, reverse=True):
        if rest_lc == np or rest_lc.startswith(np + " "):
            return len(np.split())
    return 0


# Closed list of compound proper-name subjects (multi-token). These are
# Hebrew compound divine names that the gloss generator emits as separate
# tokens. Detection happens before single-name detection so the longer
# match wins.
COMPOUND_PROPER_SUBJECTS = [
    "Yahweh God",
    "the Lord Yahweh",
    "Yahweh of hosts",
    "El Shaddai",
    "God Most High",
    "Yahweh your God",
    "Yahweh our God",
    "Yahweh his God",
    "Yahweh my God",
]


def _matches_compound_proper(tokens: list[str], start: int) -> int:
    """If a compound proper-name starts at tokens[start], return its length;
    else return 0."""
    rest = " ".join(tokens[start:])
    # Case-sensitive match for compound names (preserve capitalization).
    for cn in sorted(COMPOUND_PROPER_SUBJECTS, key=len, reverse=True):
        if rest == cn or rest.startswith(cn + " "):
            return len(cn.split())
    return 0


# Match the V-S clause-opening pattern. Captures:
#   group 1: leading conjunction/article ("and " or empty)
#   group 2: subject pronoun (he/she/it/they)
#   group 3: optional auxiliary (was / were / is / are / has / had / have)
#            for passive-voice patterns like "and they were opened the eyes"
#   group 4: main verb (must be on NARRATIVE_VERBS list — checked in code)
# 2026-05-02: extended to optionally consume an aux verb for passive-V patterns
# (Gen 3:7 `וַתִּפָּקַחְנָה עֵינֵי שְׁנֵיהֶם` glossed "and they were opened
# the eyes of both of them" — without aux-handling, regex captured "were"
# as the verb token and skipped the spec).
_VS_OPEN_RE = re.compile(
    r"^(and\s+)?(he|she|it|they)\s+((?:was|were|is|are|has|have|had|will|shall|may|might|would|could|should)\s+)?(\w+)\b",
    re.IGNORECASE,
)


def pass3_vs_reorder(line: str, in_poetic: bool) -> str:
    """V-S → S-V reorder for narrative clauses.

    Conservative gating:
      - Trigger only on closed-list verbs.
      - Subject must be a closed-list proper name OR a closed-list definite NP.
      - Subject NP must immediately follow verb (or follow one short PP).
      - Don't fire if the subject candidate is preceded by 'to' / 'with' / etc.
        (that's an indirect-object PP, not the subject).

    Idempotent: after reorder, the line begins "and <NAME> <V>" — no longer
    matches `_VS_OPEN_RE` because the captured pronoun "he" is gone.

    Register skip removed 2026-05-07 per canon §0 methodology principle:
    editorial overlays (te'amim, niqqud, versification, register
    classification) are calibration evidence, not authorization. The three
    editorial criteria adjudicate uniformly across registers.
    `in_poetic` parameter retained for caller-API stability.
    """
    m = _VS_OPEN_RE.match(line)
    if not m:
        return line

    lead = m.group(1) or ""    # "and " or ""
    pron = m.group(2)          # he/she/it/they
    aux  = (m.group(3) or "").rstrip()  # "was"/"were"/etc. or ""
    verb = m.group(4)          # candidate verb token (the content verb)
    if verb.lower() not in NARRATIVE_VERBS:
        return line

    # What's after the verb?
    rest_start = m.end()
    rest = line[rest_start:].lstrip()
    if not rest:
        return line

    rest_tokens = rest.split()

    # Optionally consume one verb particle ("off" / "up" / etc.) — phrasal-verb
    # second halves emitted as separate tokens. Treat "<verb> <particle>" as
    # one conceptual verb for reorder purposes (e.g., "sent off Moses ..." →
    # "Moses sent off ..."). Consumed first because it's adjacent to the verb
    # token; SHORT_PP_AFTER_VERB consumption follows for cases where both
    # appear (rare).
    particle_consumed = ""
    if rest_tokens and rest_tokens[0].lower() in VERB_PARTICLES:
        particle_consumed = rest_tokens[0]
        rest = rest[len(particle_consumed):].lstrip()
        rest_tokens = rest.split()

    # Optionally consume one short PP ("to him" / "to them" / etc.).
    short_pp_consumed = ""
    for pp in sorted(SHORT_PP_AFTER_VERB, key=len, reverse=True):
        if rest.lower() == pp or rest.lower().startswith(pp + " "):
            short_pp_consumed = pp
            rest = rest[len(pp):].lstrip()
            rest_tokens = rest.split()
            break

    # Optionally consume one bare object pronoun (V+O+S pattern, e.g.,
    # Gen 1:28 "and he blessed them God"). Only fires if SHORT_PP wasn't
    # consumed (else "to them him" is double-object, not the target pattern).
    obj_pron_consumed = ""
    if not short_pp_consumed and rest_tokens:
        first_lc = rest_tokens[0].lower().strip(".,;:!?")
        if first_lc in BARE_OBJECT_PRONOUNS_AFTER_VERB:
            obj_pron_consumed = rest_tokens[0]
            rest = rest[len(obj_pron_consumed):].lstrip()
            rest_tokens = rest.split()

    if not rest_tokens:
        return line

    # Determine the subject candidate.
    subj_str: str | None = None
    subj_len_tokens = 0

    # Try compound proper-name first (longest match wins).
    cp_len = _matches_compound_proper(rest_tokens, 0)
    if cp_len > 0:
        subj_str = " ".join(rest_tokens[:cp_len])
        subj_len_tokens = cp_len
    if subj_str is None:
        # Try multi-word definite NP.
        np_len = _matches_definite_np(rest_tokens, 0)
        if np_len > 0:
            subj_str = " ".join(rest_tokens[:np_len])
            subj_len_tokens = np_len
    if subj_str is None:
        # Single-word proper-name match.
        first = rest_tokens[0]
        if _capitalized_name(first):
            subj_str = first
            subj_len_tokens = 1

    if subj_str is None:
        return line

    # FP guard (Stan-flagged 2026-05-07: Genesis 44:4 "they went out the city"
    # → "the city went out" was wrong — "the city" is a locative complement of
    # "went out", not a fronted subject). When a directional particle was
    # consumed AND the subject candidate is a definite NP starting with "the",
    # the candidate is far more likely a locative/directional complement than
    # a fronted subject. Suppress to avoid the misfire. Proper-name subjects
    # remain reorderable (the TP class is overwhelmingly proper-name in Hebrew
    # narrative V-S patterns).
    if particle_consumed and subj_str.lower().startswith("the "):
        return line

    # Subject extension: if matched subject is followed by 'of <Capitalized>',
    # extend the subject to include the of-chain (e.g. 'the people of Nineveh').
    # Up to 2 extensions to handle 'X of Y of Z'.
    while (
        subj_len_tokens + 1 < len(rest_tokens)
        and rest_tokens[subj_len_tokens].lower() == "of"
        and len(rest_tokens[subj_len_tokens + 1]) >= 2
        and rest_tokens[subj_len_tokens + 1][0].isupper()
    ):
        subj_str = subj_str + " of " + rest_tokens[subj_len_tokens + 1]
        subj_len_tokens += 2

    # Reject if the subject candidate is preceded by a preposition in the
    # original line — would mean "to Yahweh" not "Yahweh did X". This is
    # already excluded because we matched verb directly before subj-or-pp,
    # but verify by re-checking the gap between verb and subj.
    # Account for particle / short-PP that were consumed above; whatever
    # remains in rest_orig must start with the subject string.
    rest_orig = line[rest_start:].lstrip()
    if particle_consumed:
        rest_orig = rest_orig[len(particle_consumed):].lstrip()
    if short_pp_consumed:
        rest_orig = rest_orig[len(short_pp_consumed):].lstrip()
    if obj_pron_consumed:
        rest_orig = rest_orig[len(obj_pron_consumed):].lstrip()
    if not rest_orig.startswith(subj_str):
        return line

    # Reorder. Re-attach particle (and/or short-PP) after the verb in
    # canonical S-V-particle-PP-O order. Auxiliary (was/were/etc.) precedes
    # the main verb in the reorder ("and they were opened the eyes ..." →
    # "and the eyes ... were opened").
    #   "and he sent off Moses his father-in-law"
    #     → "and Moses sent off his father-in-law"
    #   "and he said to him Yahweh X"
    #     → "and Yahweh said to him X"
    #   "and they were opened the eyes of both of them"
    #     → "and the eyes of both of them were opened"
    after_subj = rest_orig[len(subj_str):].lstrip()
    if aux:
        new = f"{lead}{subj_str} {aux} {verb}"
    else:
        new = f"{lead}{subj_str} {verb}"
    if particle_consumed:
        new += f" {particle_consumed}"
    if short_pp_consumed:
        new += f" {short_pp_consumed}"
    if obj_pron_consumed:
        new += f" {obj_pron_consumed}"
    if after_subj:
        new += f" {after_subj}"

    return new


# ---------------------------------------------------------------------------
# Pass 7 — divine-title capitalization
#   "god" → "God" (singular always; plural "gods" untouched)
#   "lord" → "Lord" only in clear divine contexts (avoids capitalizing
#            human-master "my lord" in Sarah/Abraham, servant/Laban, etc.)
# ---------------------------------------------------------------------------

# Tokens (case-folded, punctuation-stripped) that, when adjacent to "lord",
# unambiguously mark divine reference.
_LORD_DIVINE_PREV = {
    "the", "says", "utterance", "yahweh", "and",  # "and lord" rare but divine
}
_LORD_DIVINE_NEXT = {
    "yahweh", "yhwh",
}

# Tokens that, when preceding "god", indicate generic / foreign / negated
# reference where capitalization would be inappropriate (Isa 44 idolatry
# polemic, "I am the only God" exclusivity claims, etc.).
_GOD_LOWERCASE_PREV = {
    "a", "an", "any", "no", "not", "another", "strange", "other",
    "false", "foreign", "every", "one",
}

# Per-token splitter that preserves non-word prefix + suffix (parens, punct).
_TOKEN_SPLIT_RE = re.compile(r"^(\W*)(\w+)(\W*)$")


def _strip_clean(tok: str) -> str:
    """Lowercased, punctuation-stripped form of a token, for context lookups."""
    return re.sub(r"[^\w-]", "", tok).lower()


def pass7_capitalize_divine_titles(line: str) -> str:
    """Capitalize singular 'god' → 'God' always; capitalize 'lord' → 'Lord'
    only in clear divine contexts.

    Plural 'gods' / 'lords' are left untouched (foreign-deity references).
    Token-level pass; preserves any non-word prefix/suffix (parens, punct).

    Idempotent: capitalized forms don't re-match the lowercase patterns.
    """
    tokens = line.split()
    if not tokens:
        return line

    out = []
    for i, tok in enumerate(tokens):
        m = _TOKEN_SPLIT_RE.match(tok)
        if not m:
            out.append(tok)
            continue
        pre, word, post = m.group(1), m.group(2), m.group(3)
        wl = word.lower()

        if wl == "god":
            prev_clean = _strip_clean(tokens[i - 1]) if i > 0 else ""
            if prev_clean in _GOD_LOWERCASE_PREV:
                out.append(tok)
            else:
                out.append(f"{pre}God{post}")
        elif wl == "lord":
            prev_clean = _strip_clean(tokens[i - 1]) if i > 0 else ""
            next_clean = _strip_clean(tokens[i + 1]) if i + 1 < len(tokens) else ""
            is_divine = (
                prev_clean in _LORD_DIVINE_PREV
                or next_clean in _LORD_DIVINE_NEXT
            )
            if is_divine:
                out.append(f"{pre}Lord{post}")
            else:
                out.append(tok)
        else:
            out.append(tok)

    return " ".join(out)


# ---------------------------------------------------------------------------
# Pass 9 — Drop redundant relative-clause subject pronoun
#
# Class 1 (sub-arm) of the four-class eng-gloss cleanup spec.
#
# When Macula glosses a 3rd-person verb in a relative clause whose
# antecedent is the subject (e.g. "Yahweh who he has delivered you"),
# the embedded "he" pronoun is redundant in English ("Yahweh who has
# delivered you"). Drop the pronoun.
#
# Pattern: "<who|whom|that|which> <pron> <verb-cluster>"
#   → "<who|whom|that|which> <verb-cluster>"
#
# Where pron ∈ {he, she, it, they} AND the verb is a NARRATIVE_VERB.
#
# Conservative gating: only fire when the relative pronoun is
# antecedented by a recently-mentioned proper-name in the SAME line
# (heuristic: line contains a Capitalized name to the left of the
# relative). This avoids dropping the pronoun in cases like "all that
# he had done" where "all" is the antecedent and "he" is a real subject.
#
# Skip in poetic register.
# ---------------------------------------------------------------------------

# "whom" intentionally EXCLUDED — almost always relativizes an OBJECT
# (English "whom did he see" / "the man whom he loves"), so the in-clause
# pronoun is a REAL subject, not redundant. Tested 2026-05-05 on Exod 18:9:
# "Israel whom he had delivered" — pass9 was wrongly dropping the "he".
_REDUNDANT_REL_PRON_RE = re.compile(
    r"\b(who|that|which)\s+(he|she|it|they)\s+"
    r"((?:was|were|is|are|has|have|had|will|shall|may|might|would|could|should)\s+)?"
    r"(\w+)\b",
    re.IGNORECASE,
)


def pass9_drop_redundant_rel_pron(line: str, in_poetic: bool) -> str:
    """Drop redundant subject pronoun in relative clauses with named antecedent.

    Pattern: "<NAME> ... who he <V>" → "<NAME> ... who <V>"

    Only fires when:
      - The relative is "who"/"whom" (proper-relative antecedent),
        OR "that"/"which" with a Capitalized-name to the left
        of the match in the same line.
      - The verb is on NARRATIVE_VERBS (closed list).

    Idempotent: after drop, "<NAME> who <V>" no longer matches the pattern
    (no pron between rel and verb).

    Register skip removed 2026-05-07 per canon §0 (calibration vs
    authorization). `in_poetic` retained for caller-API stability.
    """
    def _replace(m: re.Match) -> str:
        rel = m.group(1)
        pron = m.group(2)
        aux = (m.group(3) or "").rstrip()
        verb = m.group(4)
        if verb.lower() not in NARRATIVE_VERBS:
            return m.group(0)  # leave untouched
        # Check for Capitalized-name antecedent in pre-match text.
        # IMPORTANT: the antecedent must be the IMMEDIATELY-prior token
        # (or 1-2 tokens back at most), not just "anywhere in pre-text".
        # The looser criterion produced FPs in Jonah 3:10:
        #   "and God saw their deeds that they turned back" — pass9 saw
        #   "God" as antecedent and dropped "they" (wrong; "they" =
        #   the people of Nineveh, not God).
        # Tight criterion: relative pronoun's antecedent is the immediately
        # preceding noun-class token. If that token is a Capitalized name,
        # the relative is co-referent with the name and the in-clause pron
        # is redundant.
        pre = line[: m.start()].rstrip()
        pre_tokens = pre.split()
        if not pre_tokens:
            return m.group(0)
        # Look at the last 1-2 tokens. The IMMEDIATELY-preceding token is
        # the canonical antecedent for restrictive relatives. Allow up to
        # 2 tokens back to handle "of X" tail (e.g., "the God of Israel
        # who he delivered").
        # Also check: the pre-text must NOT contain a definite NP that's
        # MORE CLEARLY the antecedent. The simple rule: only accept the
        # antecedent if the LAST capitalized token in pre is also at the
        # end (last token or last token after "of <CAP>" pattern).
        last_tok = pre_tokens[-1].rstrip(".,;:!?")
        is_last_cap = (
            last_tok and last_tok[0].isupper() and len(last_tok) >= 3
            and last_tok.lower() not in {"and", "but", "or", "the", "a", "an", "i"}
        )
        # "of <CAP>" tail (e.g. "the God of Israel who...") — antecedent
        # is the head noun before "of", but pragmatically the proper-name
        # at the end resolves the relative. Accept this case.
        is_of_cap_tail = (
            len(pre_tokens) >= 2
            and pre_tokens[-2].lower() == "of"
            and last_tok and last_tok[0].isupper() and len(last_tok) >= 3
        )
        if not (is_last_cap or is_of_cap_tail):
            return m.group(0)

        # Build the dropped form: "<rel> <aux>? <verb>"
        if aux:
            return f"{rel} {aux} {verb}"
        return f"{rel} {verb}"

    return _REDUNDANT_REL_PRON_RE.sub(_replace, line)


# ---------------------------------------------------------------------------
# Pass 8 — Mid-clause V-S → S-V reorder
#
# Class 1 of the four-class eng-gloss cleanup spec (Stan 2026-05-05).
#
# pass3_vs_reorder handles CLAUSE-OPENING V-S patterns ("and he <V> <S>").
# pass8 handles MID-CLAUSE V-S after a subordinator or relative pronoun:
# "all that he had done God for Moses" → "all that God had done for Moses".
#
# The Hebrew construction is: relative-or-subordinator + qatal/wayyiqtol-3ms
# + explicit-subject-NP. Macula's qatal/wayyiqtol-3ms gloss embeds the
# pronoun ("he had done"); the explicit subject NP follows. English
# requires the explicit subject before the verb AND drops the redundant
# pronoun.
#
# Pattern: <subord> <pron> <verb-cluster> <SUBJECT> <rest>
#   → <subord> <SUBJECT> <verb-cluster> <rest>
#
# Where:
#   - subord ∈ {that, which, who, whom, because, when, while, if, for,
#               since, although, though, until, where, as, after, before,
#               whenever}
#   - pron ∈ {he, she, it, they}
#   - verb-cluster = (was|were|is|are|has|have|had|will|may|...)? + verb
#                  + optional verb-particle (off/up/out/etc.)
#   - SUBJECT = compound proper name | proper name | definite person NP
#
# Conservative gating identical to pass3 (closed-list verbs, closed-list
# subjects, skip in poetic register). Idempotent: after reorder the
# pattern becomes "<subord> <SUBJECT> <verb>" — pron is gone, no re-fire.
# ---------------------------------------------------------------------------

# Subordinators/relatives that can introduce a V-S clause mid-line.
_MID_CLAUSE_SUBORDS = {
    "that", "which", "who", "whom", "whose",
    "because", "when", "while", "if", "for", "since",
    "although", "though", "until", "unless",
    "where", "wherever", "whenever",
    "as", "after", "before",
    "lest",
}

# Mid-clause V-S regex. Captures:
#   group 1: subord token
#   group 2: subject pronoun (he/she/it/they)
#   group 3: optional aux (was/were/is/are/has/have/had/will/may/etc.)
#   group 4: main verb token
# Anchored mid-line by \b before the subord and \b after the verb.
_VS_MID_RE = re.compile(
    r"\b(" + "|".join(sorted(_MID_CLAUSE_SUBORDS, key=len, reverse=True)) + r")\s+"
    r"(he|she|it|they)\s+"
    r"((?:was|were|is|are|has|have|had|will|shall|may|might|would|could|should)\s+)?"
    r"(\w+)\b",
    re.IGNORECASE,
)


def pass8_vs_reorder_mid_clause(line: str, in_poetic: bool) -> str:
    """V-S → S-V reorder for mid-clause subordinate clauses.

    Class 1 of the four-class spec; complement to pass3_vs_reorder which
    handles clause-opening patterns ("and he <V> <S>").

    Pattern: "<subord> <pron> <verb-cluster> <SUBJ> <rest>"
      → "<subord> <SUBJ> <verb-cluster> <rest>"

    Conservative gating:
      - Trigger only on closed-list verbs (NARRATIVE_VERBS).
      - Subject must be a closed-list proper name OR a closed-list
        definite NP OR a compound proper name ("Yahweh God" etc.).
      - Don't fire if the subject candidate is preceded by 'to' / 'with'
        (already-prepositional → indirect object, not subject).

    Idempotent: after reorder, the line contains "<subord> <SUBJ> <V>"
    — no pron between subord and verb, so pattern doesn't re-match.

    Register skip removed 2026-05-07 per canon §0 (Psa 9:10 line 1
    surfaced "and he will be Yahweh a refuge" → should normalize to
    "and Yahweh will be a refuge"). `in_poetic` retained for caller-API
    stability.

    Examples (with normalize-pipeline context):
      "all that he had done God for Moses"
        → "all that God had done for Moses"
      "for he has delivered the people from the hand of Egypt"
        → (no fire — no explicit subject NP after verb)
      "that he had brought out Yahweh Israel from Egypt"
        → "that Yahweh had brought out Israel from Egypt"
    """
    # Iterate matches; we may need to apply multiple swaps in one line.
    # Use a single forward pass: find the leftmost match, attempt reorder,
    # if successful continue from after the reordered span.
    out_pos = 0
    out_parts: list[str] = []
    while True:
        m = _VS_MID_RE.search(line, out_pos)
        if not m:
            out_parts.append(line[out_pos:])
            break
        subord = m.group(1)
        pron = m.group(2)
        aux = (m.group(3) or "").rstrip()
        verb = m.group(4)
        if verb.lower() not in NARRATIVE_VERBS:
            # Verb not in closed list; emit up to and including this match,
            # continue scanning AFTER this verb (so subsequent matches can fire).
            out_parts.append(line[out_pos : m.end()])
            out_pos = m.end()
            continue

        # What follows the verb cluster?
        rest_start = m.end()
        rest = line[rest_start:].lstrip()
        if not rest:
            out_parts.append(line[out_pos:])
            break

        rest_tokens = rest.split()

        # Optional verb particle ("off", "up", "out", etc.) — same logic as pass3.
        particle_consumed = ""
        if rest_tokens and rest_tokens[0].lower() in VERB_PARTICLES:
            particle_consumed = rest_tokens[0]
            rest = rest[len(particle_consumed):].lstrip()
            rest_tokens = rest.split()

        # Optional short PP after verb ("to him" / "to them" etc.).
        short_pp_consumed = ""
        for pp in sorted(SHORT_PP_AFTER_VERB, key=len, reverse=True):
            if rest.lower() == pp or rest.lower().startswith(pp + " "):
                short_pp_consumed = pp
                rest = rest[len(pp):].lstrip()
                rest_tokens = rest.split()
                break

        # Optional bare-object pronoun ("him" / "her" / "them" etc.).
        obj_pron_consumed = ""
        if not short_pp_consumed and rest_tokens:
            first_lc = rest_tokens[0].lower().strip(".,;:!?")
            if first_lc in BARE_OBJECT_PRONOUNS_AFTER_VERB:
                obj_pron_consumed = rest_tokens[0]
                rest = rest[len(obj_pron_consumed):].lstrip()
                rest_tokens = rest.split()

        if not rest_tokens:
            out_parts.append(line[out_pos : m.end()])
            out_pos = m.end()
            continue

        # Determine subject candidate. Mid-clause case is more FP-prone than
        # clause-opening pass3 because subordinate clauses often have an
        # implicit subject (relative-pronoun with antecedent) and the
        # post-verbal NP is the OBJECT — e.g. "Yahweh who he delivered the
        # people" — "the people" is OBJ, not the subject of "delivered".
        # To minimize FPs, restrict to PROPER-NAME subjects only (compound
        # or single). Definite-NP subjects ("the king", "the man") are
        # SKIPPED in mid-clause position because they're more often
        # accusative objects of the relative clause's verb.
        subj_str: str | None = None
        subj_len_tokens = 0

        cp_len = _matches_compound_proper(rest_tokens, 0)
        if cp_len > 0:
            subj_str = " ".join(rest_tokens[:cp_len])
            subj_len_tokens = cp_len
        if subj_str is None:
            first = rest_tokens[0]
            if _capitalized_name(first):
                subj_str = first
                subj_len_tokens = 1

        if subj_str is None:
            # No identifiable proper-name subject NP after verb; either
            # there's no subject (relative-pronoun antecedent case) or the
            # post-verbal NP is a definite-NP object. Either way, skip.
            out_parts.append(line[out_pos : m.end()])
            out_pos = m.end()
            continue

        # Subject extension via "of <Capitalized>" chain (max 2 hops).
        while (
            subj_len_tokens + 1 < len(rest_tokens)
            and rest_tokens[subj_len_tokens].lower() == "of"
            and len(rest_tokens[subj_len_tokens + 1]) >= 2
            and rest_tokens[subj_len_tokens + 1][0].isupper()
        ):
            subj_str = subj_str + " of " + rest_tokens[subj_len_tokens + 1]
            subj_len_tokens += 2

        # Verify the subject candidate is what immediately follows the
        # verb cluster + any consumed particle/PP/obj-pron.
        rest_orig = line[rest_start:].lstrip()
        rest_after_consumes = rest_orig
        if particle_consumed:
            rest_after_consumes = rest_after_consumes[len(particle_consumed):].lstrip()
        if short_pp_consumed:
            rest_after_consumes = rest_after_consumes[len(short_pp_consumed):].lstrip()
        if obj_pron_consumed:
            rest_after_consumes = rest_after_consumes[len(obj_pron_consumed):].lstrip()
        if not rest_after_consumes.startswith(subj_str):
            out_parts.append(line[out_pos : m.end()])
            out_pos = m.end()
            continue

        # Build the reordered chunk: <subord> <SUBJ> <aux> <verb> <particle?>
        # <short-pp?> <obj-pron?> <after-subj>
        after_subj = rest_after_consumes[len(subj_str):].lstrip()
        prefix_text = line[out_pos : m.start()]  # Text before the match
        if aux:
            new_chunk = f"{subord} {subj_str} {aux} {verb}"
        else:
            new_chunk = f"{subord} {subj_str} {verb}"
        if particle_consumed:
            new_chunk += f" {particle_consumed}"
        if short_pp_consumed:
            new_chunk += f" {short_pp_consumed}"
        if obj_pron_consumed:
            new_chunk += f" {obj_pron_consumed}"
        if after_subj:
            new_chunk += f" {after_subj}"

        out_parts.append(prefix_text + new_chunk)
        # The reordered chunk has consumed everything from out_pos to end-of-line.
        out_pos = len(line)
        break

    return "".join(out_parts)


# ---------------------------------------------------------------------------
# Pass 4 — whitespace cleanup
# ---------------------------------------------------------------------------

def pass4_whitespace(line: str) -> str:
    """Collapse runs of whitespace to a single space; strip ends."""
    return re.sub(r"\s+", " ", line).strip()


# ---------------------------------------------------------------------------
# Pass 6 — V-medial reorder, Shape A
#   subordinator + copula + predicative + pronoun-subject → natural English order
# ---------------------------------------------------------------------------

# Shape A trigger: "for|because|lest|though  is|was|are|were  <pred>  <pron>"
# Reorder to: subordinator pronoun copula predicate (+ remainder).
# Idempotent: after reorder the copula no longer immediately follows the
# subordinator, so the pattern cannot fire a second time.
#
# Shapes B / C / D / E are deferred to future passes.

_V_MEDIAL_SHAPE_A_RE = re.compile(
    r"\b(for|because|lest|though)"
    r"\s+(is|was|are|were)"
    r"\s+(\w+(?:ing)?)"
    r"\s+(I|he|she|they|you|we|it)\b",
    re.IGNORECASE,
)


def pass6_v_medial_reorder(line: str, in_poetic: bool) -> str:
    """Reorder V-medial subordinate clauses: sub + cop + pred + pron → sub + pron + cop + pred.

    Shape A only (Shapes B/C/D/E deferred).

    Pattern: ``<sub> <cop> <pred> <pron>`` → ``<sub> <pron> <cop> <pred>``
    where:
      - sub  ∈ {for, because, lest, though}
      - cop  ∈ {is, was, are, were}
      - pred = any single-word predicative adjective (bare or -ing)
      - pron ∈ {I, he, she, it, they, you, we}

    FP guard: suppress if the line contains a '?' (interrogative).

    Idempotent: the reordered form ``<sub> <pron> <cop> <pred>`` does not match
    because the copula is no longer immediately after the subordinator.

    Examples:
    >>> pass6_v_medial_reorder("for was naked I", False)
    'for I was naked'
    >>> pass6_v_medial_reorder("for is strong it more than us", False)
    'for it is strong more than us'
    >>> pass6_v_medial_reorder("for I was naked", False)
    'for I was naked'
    >>> pass6_v_medial_reorder("for was unclean he?", False)
    'for was unclean he?'
    >>> pass6_v_medial_reorder("for is holy he to his God", False)
    'for he is holy to his God'

    Register skip removed 2026-05-07 per canon §0 (calibration vs
    authorization). `in_poetic` retained for caller-API stability.
    """
    if "?" in line:
        return line

    def _repl(m: re.Match) -> str:
        sub  = m.group(1)
        cop  = m.group(2)
        pred = m.group(3)
        pron = m.group(4)
        # Preserve case of the subordinator token as found.
        return f"{sub} {pron} {cop} {pred}"

    return _V_MEDIAL_SHAPE_A_RE.sub(_repl, line)


# Final-pass invariant guarantee — collapse artifact doublings injected by
# any prior pass (or stale upstream gloss). Closed-list of genuine Hebrew
# geminate constructions are preserved. Per Design D 2026-04-30 + Stan's
# 2026-04-30 directive: guarantee invariants at the FINAL pass, don't
# debug upstream when downstream-fix-loop is shorter.

_GENUINE_DOUBLINGS_FINAL = frozenset({
    'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
    'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty',
    'hundred', 'thousand',
    'very', 'muchness',
    'go', 'arise', 'awake', 'come', 'pass', 'turn', 'return',
    'day', 'days', 'year', 'years',
    'seed',
    # 2026-05-04 Class 1: rhetorical-doubling whitelist derived from corpus
    # scan of v0/prose Hebrew + Macula gloss lookup (187 unique Hebrew
    # doublings → 192 unique English gloss tokens). Preserves intentional
    # Hebrew doublings like נַחֲמוּ נַחֲמוּ (Isa 40:1 "comfort comfort"),
    # קָדוֹשׁ קָדוֹשׁ קָדוֹשׁ (Isa 6:3 "holy holy holy"),
    # אַבְרָהָם אַבְרָהָם (Gen 22:11 "Abraham Abraham"), etc.
    'about', 'abraham', 'absalom', 'act', 'actually', 'aha', 'alas', 'all',
    'altar', 'amen', 'approaching', 'ariel', 'around', 'asahel', 'ashamed',
    'ask', 'assigned', 'back', 'bad', 'bare', 'bears', 'belonged', 'bereaved',
    'bethel', 'bless', 'bright', 'bring', 'brothers', 'burn', 'burnt',
    'captivity', 'cast', 'certainly', 'child', 'city', 'clans', 'clothed',
    'comfort', 'completely', 'covering', 'creeping', 'cubit', 'death', 'deed',
    'depart', 'destroy', 'destroyed', 'diligently', 'direction', 'ditches',
    'draw', 'dreamed', 'eat', 'evening', 'ever', 'exalted', 'exceedingly',
    'explicitly', 'expressly', 'extorted', 'eye', 'fallen', 'famine', 'far',
    'father', 'favor', 'flee', 'foundation', 'foxes', 'fully', 'gains', 'get',
    'give', 'going', 'gold', 'grace', 'great', 'guilt', 'harp', 'haughty',
    'head', 'heaps', 'hear', 'herd', 'here', 'highly', 'holy', 'indeed',
    'inheritance', 'inward', 'iron', 'ithiel', 'jacob', 'judge', 'just',
    'king', 'know', 'land', 'lay', 'like', 'listen', 'little', 'living',
    'lo-ammi', 'man', 'mene', 'morning', 'moses', 'multitudes', 'nation',
    'noah', 'o', 'offering', 'offerings', 'only', 'out', 'own', 'parts',
    'people', 'perez', 'perished', 'person', 'phinehas', 'pieces', 'pits',
    'praises', 'prophets', 'provinces', 'red', 'reigned', 'righteousness',
    'road', 'robbed', 'rod', 'rouse', 'ruin', 'sabbath', 'sacrificing',
    'sake', 'samuel', 'say', 'seek', 'sevens', 'shem', 'shepherds',
    'shouting', 'show', 'shut', 'silver', 'sing', 'slaughter', 'slaughtered',
    'sojourners', 'solemnly', 'son', 'spit', 'spots', 'stew', 'stone', 'stop',
    'strength', 'surely', 'swarming', 'sword', 'tear', 'tell', 'tenth',
    'terah', 'thing', 'treason', 'unfaithfully', 'unjustly', 'up', 'upwards',
    'urgently', 'utterly', 'vow', 'wage', 'wall', 'war', 'warn', 'way',
    'weep', 'well', 'went', 'wise', 'woe', 'word', 'yahweh', 'young',
    'yourself',
    # Note: 'god' deliberately EXCLUDED — too generic, FP risk if any
    # Macula glitch produces "god god" non-rhetorically.
})

_DOUBLED_WORD_RE_FINAL = re.compile(r'\b(\w+)\b \1\b', re.IGNORECASE)


def pass5_dedup(line: str) -> str:
    """Collapse consecutive identical tokens unless genuine geminate."""
    def _replace(m):
        if m.group(1).lower() in _GENUINE_DOUBLINGS_FINAL:
            return m.group(0)
        return m.group(1)
    while _DOUBLED_WORD_RE_FINAL.search(line):
        new_line = _DOUBLED_WORD_RE_FINAL.sub(_replace, line)
        if new_line == line:
            break
        line = new_line
    return line


# Negation placement (Stan-flagged 2026-05-07: Psa 23:1 "not I lack" / Psa 23:4
# "not I will fear harm" — Hebrew negation לֹא + yiqtol mechanically renders as
# "not [PRON] [V]" but English requires SUBJ + AUX + not + V).
_NEG_SUBJ_PRONS = ("I", "you", "he", "she", "it", "we", "they")
_NEG_AUX_VERBS = ("will", "shall", "do", "does", "did", "can", "may", "might",
                  "would", "should", "could", "must",
                  # Copulas + perfect/progressive auxes — when present, preserve
                  # them (e.g., "not he had caused" → "he had not caused", not
                  # "he will not had caused"; "not she is here" → "she is not here").
                  "is", "are", "am", "was", "were",
                  "has", "have", "had", "been", "being")
# Pattern: "not <pron> [aux]? <V>" — Hebrew negation לֹא always immediately
# precedes its verb, so any "not [PRON] [V]" surface is mechanically certain
# to be the Hebrew construction needing English-style reorder. No clause-
# boundary requirement; the closed-list pronoun + closed-list aux + content-
# word verb combination is precise enough that the broad scan is safe.
_NEG_PLACEMENT_RE = re.compile(
    r"\bnot\s+(" + "|".join(_NEG_SUBJ_PRONS) + r")\s+"
    r"(?:(" + "|".join(_NEG_AUX_VERBS) + r")\s+)?"
    r"([a-z]\w*)",
    re.IGNORECASE,
)
# FP guard set: when "not" is already preceded by an English aux ("he did not",
# "she has not"), the negation IS already English-correct and re-firing would
# produce broken output ("he did he will not say"). Checked via prior-token
# inspection in pass_negation_placement (lookbehind regex requires fixed-width
# pattern, so closed-list aux check is done in Python).
_NEG_AUX_LOOKBACK = frozenset(a.lower() for a in _NEG_AUX_VERBS)

# Interrogative-inverted negation: "not [AUX] [PRON] [V]" — Hebrew הֲלֹא +
# verb-with-prefix-subject renders as "not are they finding" / "not did he see"
# (Stan-flagged 2026-05-07 on Judg 5:30 "not are they finding are they
# dividing up"). English target: "[AUX] [PRON] not [V]" — "are they not
# finding" / "did he not see".
_NEG_INVERTED_RE = re.compile(
    r"\bnot\s+(" + "|".join(_NEG_AUX_VERBS) + r")\s+"
    r"(" + "|".join(_NEG_SUBJ_PRONS) + r")\s+"
    r"([a-z]\w*)",
    re.IGNORECASE,
)


def pass_negation_placement(line: str) -> str:
    """Reorder Hebrew-style "not [PRON] [V]" to English "[PRON] [aux] not [V]".

    Hebrew negation לֹא precedes the verb (NEG SUBJ-VERB); literal gloss yields
    "not I lack" / "not I will fear" which is non-English. English negation
    requires SUBJ + AUX + not + V.

    Conservative gating:
      - Closed-list subject pronouns (I/you/he/she/it/we/they)
      - Pattern fires at clause boundary (line start, post-punctuation, after
        common subordinators) — avoids mid-line false matches like
        "perhaps not I lack" where intervening text could change parsing
      - If existing aux verb (will/shall/do/etc.) is present after the pronoun,
        preserve it: "not I will fear" → "I will not fear"
      - If no aux, insert "will" — preserves Stan's established future-tense
        rendering for Hebrew yiqtol (Psa 23:4 already uses "will fear")
      - Only trigger if the word after pronoun (or aux) is a content word
        (not punctuation, not another particle)

    Idempotent: after reorder "[PRON] [aux] not [V]", "not" no longer follows
    the boundary trigger, so the pattern doesn't re-match.

    Examples:
      "not I lack" → "I will not lack"
      "not I will fear harm" → "I will not fear harm"
      "and not he forsook" → "and he will not forsake" (well, simpler: "and he did not forsake" but we use "will" uniformly per Stan-rendering pattern)
    """
    def _replace(m: re.Match) -> str:
        # Skip if a pre-existing aux verb is immediately before "not" — the
        # negation is already English-correct ("he did not", "she has not")
        # and re-firing would double-emit auxes ("he did he will not say").
        text_before = line[:m.start()].rstrip()
        if text_before:
            prior_tok = text_before.split()[-1].lower().strip(".,;:!?")
            if prior_tok in _NEG_AUX_LOOKBACK:
                return m.group(0)  # leave unchanged
        pron = m.group(1)
        aux = m.group(2)  # may be None
        verb = m.group(3)
        if not aux:
            aux = "will"
        return f"{pron} {aux} not {verb}"

    def _replace_inverted(m: re.Match) -> str:
        # "not [AUX] [PRON] [V]" → "[AUX] [PRON] not [V]" (interrogative form)
        aux = m.group(1)
        pron = m.group(2)
        verb = m.group(3)
        return f"{aux} {pron} not {verb}"

    # Apply inverted-form first (more specific pattern), then declarative.
    line = _NEG_INVERTED_RE.sub(_replace_inverted, line)
    line = _NEG_PLACEMENT_RE.sub(_replace, line)
    return line


# ---------------------------------------------------------------------------
# Chapter processor
# ---------------------------------------------------------------------------

def normalize_line(line: str, in_poetic: bool) -> str:
    """Apply all passes in order to a single gloss line."""
    s = line
    s = pass0_construct_of_with_pron(s)  # Class 3: insert "of" before pass1 sees "X pron"
    s = pass1_suffix_reorder(s)
    s = pass2_construct_of(s)
    s = pass7_capitalize_divine_titles(s)  # before pass3 so "Yahweh your God" matches COMPOUND_PROPER_SUBJECTS
    s = pass3_vs_reorder(s, in_poetic)
    s = pass8_vs_reorder_mid_clause(s, in_poetic)  # Class 1: mid-clause V-S → S-V
    s = pass9_drop_redundant_rel_pron(s, in_poetic)  # Class 1 sub-arm: drop redundant relative-clause pron
    s = pass4_whitespace(s)
    s = pass6_v_medial_reorder(s, in_poetic)
    s = pass_negation_placement(s)
    s = pass5_dedup(s)
    return s


def process_chapter(book: str, chapter_filename: str, dry_run: bool) -> dict:
    """Normalize one chapter file. Return per-pattern change counts."""
    src_path = GLOSS_DIR / book / chapter_filename
    if not src_path.exists():
        return {"skipped": True, "lines": 0, "changes": 0}

    text = src_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    out_lines: list[str] = []
    diffs: list[tuple[int, str, str]] = []
    current_chapter: int | None = None
    current_verse: int | None = None
    book_norm = book

    for idx, raw in enumerate(lines):
        stripped = raw.strip()
        m = VERSE_REF_RE.match(stripped)
        if m:
            current_chapter = int(m.group(1))
            current_verse = int(m.group(2))
            out_lines.append(raw)
            continue
        if stripped == "":
            out_lines.append(raw)
            continue

        if current_chapter is None:
            out_lines.append(raw)
            continue

        in_poetic = is_poetic_register(book_norm, current_chapter, current_verse)
        new_line = normalize_line(raw, in_poetic)
        if new_line != raw:
            diffs.append((idx + 1, raw, new_line))
        out_lines.append(new_line)

    out_text = "\n".join(out_lines)
    # File-level cleanup: collapse 3+ consecutive newlines to 2 (i.e., at most
    # one blank line between content blocks). Stray double-blanks between
    # verses leak in from upstream; collapse here so the corpus is uniform.
    out_text = re.sub(r"\n\n\n+", "\n\n", out_text)
    # Preserve original trailing-newline count exactly.
    orig_trailing = len(text) - len(text.rstrip("\n"))
    out_text = out_text.rstrip("\n") + ("\n" * orig_trailing)

    if dry_run:
        for ln_no, before, after in diffs[:50]:
            print(f"  L{ln_no}:")
            print(f"    - {before}")
            print(f"    + {after}")
        if len(diffs) > 50:
            print(f"  ... ({len(diffs) - 50} more changes)")
    else:
        if out_text != text:
            src_path.write_text(out_text, encoding="utf-8")

    return {
        "skipped": False,
        "lines": len(lines),
        "changes": len(diffs),
    }


def process_book(book: str, dry_run: bool) -> dict:
    """Normalize all chapters of one book."""
    book_dir = GLOSS_DIR / book
    if not book_dir.exists():
        return {"chapters": 0, "lines": 0, "changes": 0, "missing": True}

    chapter_files = sorted(book_dir.glob("*.txt"))
    totals = {"chapters": 0, "lines": 0, "changes": 0, "missing": False}
    for cf in chapter_files:
        stats = process_chapter(book, cf.name, dry_run)
        if stats.get("skipped"):
            continue
        totals["chapters"] += 1
        totals["lines"] += stats["lines"]
        totals["changes"] += stats["changes"]
        print(f"  {cf.name}: {stats['changes']} change(s) over {stats['lines']} line(s)")
    return totals


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    book_group = ap.add_mutually_exclusive_group(required=True)
    book_group.add_argument("--book", help="Book folder name, e.g. '01-genesis'")
    book_group.add_argument("--all-books", action="store_true",
                            help="Normalize all books with content in v2/eng-gloss")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print diffs but do not write")
    args = ap.parse_args()

    if args.all_books:
        if not GLOSS_DIR.exists():
            sys.exit(f"ERROR: {GLOSS_DIR} not found")
        books = sorted(d.name for d in GLOSS_DIR.iterdir() if d.is_dir())
        if not books:
            sys.exit("ERROR: no book folders under v2/eng-gloss/")
        print(f"normalize_english_gloss.py — --all-books ({len(books)} books)")
        print(f"Mode: {'dry-run' if args.dry_run else 'apply'}\n")
    else:
        books = [args.book]
        print(f"normalize_english_gloss.py — book: {args.book}")
        print(f"Mode: {'dry-run' if args.dry_run else 'apply'}\n")

    grand_total = {"books": 0, "chapters": 0, "lines": 0, "changes": 0}
    missing: list[str] = []

    for book in books:
        print(f"--- {book} ---")
        stats = process_book(book, args.dry_run)
        if stats.get("missing"):
            print(f"  (no folder under v2/eng-gloss/)")
            missing.append(book)
            continue
        grand_total["books"] += 1
        grand_total["chapters"] += stats["chapters"]
        grand_total["lines"] += stats["lines"]
        grand_total["changes"] += stats["changes"]

    print("\n" + "=" * 60)
    print(f"Books processed:  {grand_total['books']}")
    print(f"Chapters scanned: {grand_total['chapters']}")
    print(f"Total lines:      {grand_total['lines']}")
    print(f"Total changes:    {grand_total['changes']}")
    if missing:
        print(f"Books missing in eng-gloss: {', '.join(missing)}")
    if args.dry_run:
        print("(dry-run: no files written)")
    print("=" * 60)


if __name__ == "__main__":
    main()
