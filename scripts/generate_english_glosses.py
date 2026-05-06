#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_english_glosses.py — Tanakh structural English gloss generator.

Walks v2/he (or v1/he-baseline) cola line-by-line. For each Hebrew word,
looks up Macula Hebrew TSV by (ref, NFC-normalized surface text) and
aggregates per-morpheme glosses into per-word glosses. Then applies
HEBREW_PHRASE_MAP for stock formulas (e.g. כֹּה אָמַר יְהוָה → "thus says
Yahweh"), then naturalize() for mechanical Hebrew→English transformations
(VS→SV reorder, possessive-suffix reorder, NP-DEM reorder, etc.).

Output: data/text-files/v2/eng-gloss/<book>/<chapter>.txt — one English
line per Hebrew cola, verse refs + blank lines preserved.

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/generate_english_glosses.py --book 32-jonah
    PYTHONIOENCODING=utf-8 py -3 scripts/generate_english_glosses.py --book 32-jonah --use-v1
    PYTHONIOENCODING=utf-8 py -3 scripts/generate_english_glosses.py --book 32-jonah --dry-run
    PYTHONIOENCODING=utf-8 py -3 scripts/generate_english_glosses.py --book 32-jonah --verbose
    PYTHONIOENCODING=utf-8 py -3 scripts/generate_english_glosses.py --all-books
    PYTHONIOENCODING=utf-8 py -3 scripts/generate_english_glosses.py --all-books --dry-run
"""

import argparse
import csv
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MACULA_TSV = REPO_ROOT / "research" / "macula-hebrew" / "WLC" / "tsv" / "macula-hebrew.tsv"
V2_HE_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "he"
V1_HE_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
OUT_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "eng-gloss"

# Book folder name → Macula OSIS abbreviation (matches the ref field).
# Folder names follow the project's BHS canonical convention (numeric prefix).
# Only 32-jonah exists currently; the full table is pre-populated for
# future books. Verify folder names against data/text-files/v0/prose/ when
# adding new books.
BOOK_OSIS = {
    "01-genesis":       "GEN",
    "02-exodus":        "EXO",
    "03-leviticus":     "LEV",
    "04-numbers":       "NUM",
    "05-deuteronomy":   "DEU",
    "06-joshua":        "JOS",
    "07-judges":        "JDG",
    "08-ruth":          "RUT",
    "09-1samuel":       "1SA",
    "10-2samuel":       "2SA",
    "11-1kings":        "1KI",
    "12-2kings":        "2KI",
    "13-1chronicles":   "1CH",
    "14-2chronicles":   "2CH",
    "15-ezra":          "EZR",
    "16-nehemiah":      "NEH",
    "17-esther":        "EST",
    "18-job":           "JOB",
    "19-psalms":        "PSA",
    "20-proverbs":      "PRO",
    "21-ecclesiastes":  "ECC",
    "22-songofsongs":   "SNG",
    "23-isaiah":        "ISA",
    "24-jeremiah":      "JER",
    "25-lamentations":  "LAM",
    "26-ezekiel":       "EZK",
    "27-daniel":        "DAN",
    "28-hosea":         "HOS",
    "29-joel":          "JOL",
    "30-amos":          "AMO",
    "31-obadiah":       "OBA",
    "32-jonah":         "JON",
    "33-micah":         "MIC",
    "34-nahum":         "NAM",
    "35-habakkuk":      "HAB",
    "36-zephaniah":     "ZEP",
    "37-haggai":        "HAG",
    "38-zechariah":     "ZEC",
    "39-malachi":       "MAL",
}

VERSE_REF_RE = re.compile(r"^\d+:\d+$")

# Strip te'amim and niqqud, but NOT maqqef (U+05BE) or sof-pasuq (U+05C3).
# Hebrew Unicode ranges:
#   U+0591–U+05BD  cantillation marks + niqqud (below maqqef)
#   U+05BE         MAQQEF — word-joining hyphen; preserve for phrase matching
#   U+05BF         rafe
#   U+05C0         paseq
#   U+05C1–U+05C2  shin/sin dots
#   U+05C3         SOF PASUQ — punctuation; handled separately
#   U+05C4–U+05C7  upper/lower dots, qamats qatan
# We strip everything EXCEPT U+05BE (maqqef) and U+05C3 (sof pasuq).
# The regex below covers: U+0591-U+05BD, then U+05BF-U+05C2, then U+05C4-U+05C7.
DIACRITICS_RE = re.compile(r"[֑-ֽֿ-ׂׄ-ׇ]")

MAQQEF = "־"     # U+05BE — Hebrew maqqef (word-joining hyphen)
SOF_PASUQ = "׃"  # U+05C3 — verse-end marker; stripped from comparison surfaces

# Gloss tokens that carry no semantic content — skip rather than emit.
EMPTY_GLOSS_TOKENS = {"(dm)", "(cmp)", "(et)", "(the)", ""}

# Sentinel returned by aggregate_word_gloss for particles that have NO
# translation (accusative marker אֶת, discourse markers, etc.).
# Callers should drop this token rather than emitting it.
SKIP_TOKEN = "\x00SKIP\x00"


# ---------------------------------------------------------------------------
# HEBREW_PHRASE_MAP: stock formulas for cola-level substitution.
# Keys: Hebrew with niqqud (NFC). Comparison is done on stripped consonants
# after NFC normalization. Apply longest-match-first against the stripped cola.
# ---------------------------------------------------------------------------
HEBREW_PHRASE_MAP = {
    # Prophetic formulas
    "כֹּה אָמַר יְהוָה":               "thus says Yahweh",
    "כֹּה אָמַר יְהוָה צְבָאוֹת":      "thus says Yahweh of hosts",
    "נְאֻם־יְהוָה":                    "declares Yahweh",
    "נְאֻם יְהוָה":                    "declares Yahweh",
    "נְאֻם־יְהוָה צְבָאוֹת":           "declares Yahweh of hosts",
    "נְאֻם אֲדֹנָי יְהוִה":            "declares the Lord Yahweh",
    "וַיְהִי דְבַר־יְהוָה":            "and the word of Yahweh came",
    "וַיְהִי דְבַר־יְהוָה אֶל":        "and the word of Yahweh came to",
    "אָמַר אֲדֹנָי יְהוִה":            "says the Lord Yahweh",
    # Compound divine names (canon Rule H9)
    "יְהוָה אֱלֹהִים":                  "Yahweh God",
    "יְהוָה צְבָאוֹת":                  "Yahweh of hosts",
    "יְהוָה אֱלֹהֵי הַשָּׁמַיִם":      "Yahweh, the God of heaven",
    "יְהוָה אֱלֹהֵי יִשְׂרָאֵל":       "Yahweh, the God of Israel",
    "יְהוָה אֱלֹהֵיכֶם":               "Yahweh your God",
    "יְהוָה אֱלֹהֵינוּ":               "Yahweh our God",
    "אֲדֹנָי יְהוִה":                   "the Lord Yahweh",
    "אֵל שַׁדַּי":                       "El Shaddai",
    "אֵל עֶלְיוֹן":                     "God Most High",
    "אֱלֹהֵי אַבְרָהָם יִצְחָק וְיַעֲקֹב": "the God of Abraham, Isaac, and Jacob",
    # Discourse openers / vocative formulas
    "הִנֵּה־נָא":                       "behold now",
    "הִנֵּה אָנֹכִי":                   "behold, I",
    "אַל־נָא":                          "please do not",
    "אַל־תִּירָא":                      "do not fear",
    "שְׁמַע יִשְׂרָאֵל":               "hear, O Israel",
    "אַשְׁרֵי הָאִישׁ":                 "blessed is the man",
    "אֲהָהּ אֲדֹנָי יְהוִה":           "alas, Lord Yahweh",
    "אָנָּה יְהוָה":                    "we beg you, O Yahweh",
    # Jonah-specific: the sailors' prayer opener in 1:14
    "אָנָּ֤ה יְהוָה֙":                  "we beg you, O Yahweh",
    # Idiomatic temporal / eternal formulas
    "וַיְהִי כִּי":                     "and when",
    "וְהָיָה אִם":                      "and it shall be, if",
    "בָּעֵת הַהִיא":                    "at that time",
    "בַּיּוֹם הַהוּא":                  "on that day",
    "בְּאַחֲרִית הַיָּמִים":            "in the latter days",
    "מֵעוֹלָם וְעַד עוֹלָם":            "from everlasting to everlasting",
    "מִדּוֹר לְדוֹר":                   "from generation to generation",
    "יוֹם יוֹם":                        "day by day",
    "אִישׁ וְאִישׁ":                    "each one",
    # Cognate-accusative idiom normalizations (Jonah-attested)
    "וַיִּזְבְּחוּ זֶבַח":              "and they offered a sacrifice",
    "וַיִּזְבְּחוּ־זֶבַח":             "and they offered a sacrifice",
    "וַיִּֽזְבְּחוּ זֶבַח":             "and they offered a sacrifice",
    "וַיִּֽזְבְּחוּ־זֶבַח":            "and they offered a sacrifice",
    "וַיִּדְּרוּ נְדָרִים":             "and they made vows",
    "וַֽיִּדְּרוּ נְדָרִים":            "and they made vows",
    "וַיִּירְאוּ יִרְאָה גְדוֹלָה":    "they were greatly afraid",
    "וַיִּֽירְאוּ יִרְאָה גְדוֹלָה":   "they were greatly afraid",
    "יִרְאָה גְדוֹלָה":                 "great fear",
    # Jonah 1:1 opener
    "וַיְהִי דְּבַר־יְהוָה אֶל־יוֹנָה בֶן־אֲמִתַּי לֵאמֹר": \
        "and the word of Yahweh came to Jonah son of Amittai, saying",
}

# Pre-build a normalized-key lookup dict for fast phrase comparison.
# Keys are normalized (pointing stripped, maqqef→space, sof pasuq removed).
# Built once at startup; not at module load since normalize_for_phrase() uses
# module-level constants that must be defined first.
_PHRASE_MAP_NORMALIZED: dict[str, str] = {}


def _build_phrase_map_index():
    """Build the normalized phrase-map index. Must be called before gloss generation."""
    global _PHRASE_MAP_NORMALIZED
    seen: dict[str, str] = {}
    for k, v in HEBREW_PHRASE_MAP.items():
        nk = normalize_for_phrase(k)
        if nk in seen and seen[nk] != v:
            # Collision: two keys normalize to the same string but different values.
            # Warn and keep first (longest original key wins via sort order).
            print(f"WARNING: phrase-map collision on normalized key {nk!r}: "
                  f"{seen[nk]!r} vs {v!r} — keeping first")
        seen[nk] = v
    _PHRASE_MAP_NORMALIZED = seen


# ---------------------------------------------------------------------------
# NATURALIZE_RULES: regex-based mechanical transformations applied after
# per-word lookup, in order. Earlier rules may create conditions for later
# ones; order matters.
# ---------------------------------------------------------------------------
NATURALIZE_RULES = [
    # -----------------------------------------------------------------------
    # 1. Punctuation-token cleanup (TAHOT artifacts that survive into glosses)
    # -----------------------------------------------------------------------
    # Strip lone "!" tokens (imperative vowel-letter artifact)
    (r"\s+!\s+", " "),
    (r"\s+!$",   ""),
    (r"^!\s+",   ""),
    # Strip lone "?" tokens that are NOT at end of interrogative clause
    # (heuristic: keep trailing "?" only when preceded by a word, not a space)
    (r"\?\s+",   " "),   # mid-sentence "?" → strip
    # -----------------------------------------------------------------------
    # 2. Compound preposition normalization
    # -----------------------------------------------------------------------
    (r"\bfrom to\b",    "from"),
    (r"\bfrom on\b",    "from upon"),
    (r"\bfrom off\b",   "from off"),
    (r"\bto to\b",      "to"),
    # -----------------------------------------------------------------------
    # 3. Poetry-aware: construct-chain double-suffix reorder.
    # Macula emits two gloss tokens for a single Hebrew word when a construct
    # form carries a suffix that belongs to a following bound noun — e.g.
    # קָדְשְׁךָ "your holiness your" / "your holy your" → "your holy".
    # Pattern: "the temple your holiness your" → "your holy temple".
    # Must run BEFORE the single-token possessive reorders (rule 4) so the
    # double-suffix is collapsed first.
    # -----------------------------------------------------------------------
    # "the temple your holiness your" → "your holy temple"
    (r"\bthe temple your holiness your\b",      "your holy temple"),
    (r"\bthe temple your your holy\b",          "your holy temple"),
    # Generic double-possessive collapse for "X your Y your" → "your Y X"
    # Handles any noun + "your holiness your" or "your X your" artifact.
    (r"\b(\w+) your holiness your\b",           r"your holy \1"),
    (r"\b(\w+) your your holy\b",               r"your holy \1"),
    # -----------------------------------------------------------------------
    # 3b. Construct-chain "of" insertion (Class 3 of 2026-05-05 four-class
    # spec). Macula glosses Hebrew construct heads with "the." prefix
    # (e.g. אֱלֹהֵי → "the.God") even though Hebrew construct heads are
    # anarthrous; when the bound noun has a pronominal suffix, Macula does
    # NOT insert "of" — yielding "the God my father" / "the days your life"
    # / "the firstborn his flock". English idiom requires "of": "the God
    # of my father". Insert "of" between X and the suffix-pronoun BEFORE
    # the rule-4 swaps (which would otherwise produce "the my God father"
    # by swapping the X-pron pair). After insertion, "X of pron" no longer
    # matches the rule-4 pattern \bX pron\b. Runs AFTER rule 3a so the
    # "your holiness your" double-possessive collapse fires first (avoids
    # "the temple your holiness your" → "the temple of your holy of"
    # corruption).
    # The (?!...) guards skip insertion when X or Y is a particle / numeral
    # / function word that wouldn't take "of" comfortably in English.
    # -----------------------------------------------------------------------
    (r"\bthe (?!one\b|two\b|three\b|four\b|five\b|six\b|seven\b|eight\b|nine\b|"
     r"ten\b|first\b|second\b|third\b|other\b|all\b|every\b|some\b|many\b|"
     r"much\b|few\b|both\b|same\b|whole\b|only\b|very\b|"
     r"and\b|or\b|but\b|so\b|for\b|"
     r"is\b|are\b|was\b|were\b|be\b|been\b|being\b|"
     r"has\b|have\b|had\b|will\b|would\b|shall\b|"
     r"this\b|that\b|these\b|those\b|"
     r"who\b|which\b|what\b|where\b|"
     r"his\b|her\b|my\b|your\b|our\b|their\b|its\b)"
     r"(\w{2,}) (his|her|my|your|our|their|its) "
     r"(?!one\b|two\b|three\b|four\b|five\b|six\b|seven\b|eight\b|nine\b|"
     r"ten\b|first\b|second\b|third\b|all\b|every\b|some\b|many\b|much\b|"
     r"few\b|both\b|same\b|whole\b|"
     r"and\b|or\b|but\b|so\b|for\b|"
     r"is\b|are\b|was\b|were\b|be\b|been\b|being\b|"
     r"has\b|have\b|had\b|will\b|would\b|shall\b|"
     r"this\b|that\b|these\b|those\b|"
     r"who\b|which\b|what\b|where\b|"
     r"to\b|from\b|in\b|on\b|with\b|by\b|at\b|of\b|"
     r"not\b|no\b|never\b|"
     r"great\b|small\b|good\b|bad\b|evil\b|"
     r"old\b|new\b|young\b|"
     r"holiness\b|holy\b|"  # avoid "the temple of your holy" cascade
     r"his\b|her\b|my\b|your\b|our\b|their\b|its\b)"
     r"(\w{2,})\b",
     r"the \1 of \2 \3"),
    # -----------------------------------------------------------------------
    # 4. Possessive-suffix reorder ("noun its/his/her/their" → "its/his/her/their noun")
    # These are the most common Hebrew suffixed-noun→English reorderings.
    # -----------------------------------------------------------------------
    (r"\bfare its\b",           "its fare"),
    (r"\bson its\b",            "its son"),
    (r"\bdaughter his\b",       "his daughter"),
    (r"\bhand his\b",           "his hand"),
    (r"\bmouth his\b",          "his mouth"),
    (r"\bface his\b",           "his face"),
    (r"\bheart his\b",          "his heart"),
    (r"\bname his\b",           "his name"),
    (r"\bvoice his\b",          "his voice"),
    (r"\bvoice my\b",           "my voice"),
    (r"\bword his\b",           "his word"),
    (r"\bservant his\b",        "his servant"),
    (r"\bpeople his\b",         "his people"),
    (r"\bhouse his\b",          "his house"),
    (r"\bpath his\b",           "his path"),
    (r"\bway his\b",            "his way"),
    (r"\bhand her\b",           "her hand"),
    (r"\bmouth their\b",        "their mouth"),
    (r"\bhand their\b",         "their hand"),
    (r"\bwickedness their\b",   "their wickedness"),
    (r"\bloyalty their\b",      "their loyalty"),
    (r"\bfaithfulness their\b", "their faithfulness"),
    (r"\bkindness their\b",     "their kindness"),
    (r"\bhand my\b",            "my hand"),
    (r"\bmouth my\b",           "my mouth"),
    (r"\bface my\b",            "my face"),
    (r"\bsoul my\b",            "my soul"),
    (r"\bpeople my\b",          "my people"),
    (r"\bservant my\b",         "my servant"),
    (r"\bgods his\b",           "his gods"),
    (r"\bgod your\b",           "your god"),
    (r"\bgod my\b",             "my God"),
    (r"\bGod his\b",            "his God"),
    (r"\bGod my\b",             "my God"),
    (r"\bgods their\b",         "their gods"),
    (r"\bstorming its\b",       "its storming"),
    (r"\bthrone his\b",         "his throne"),
    (r"\bcloak his\b",          "his cloak"),
    (r"\banger his\b",          "his anger"),
    (r"\bwrath his\b",          "his wrath"),
    (r"\bbelly his\b",          "his belly"),
    (r"\bhead my\b",            "my head"),
    (r"\bdepths their\b",       "their depths"),
    (r"\bbreakers your\b",      "your breakers"),
    (r"\bwaves your\b",         "your waves"),
    (r"\bbillows your\b",       "your billows"),
    (r"\bholiness your\b",      "your holy"),
    (r"\beyes your\b",          "your eyes"),
    (r"\bprayer my\b",          "my prayer"),
    (r"\bdistress my\b",        "my distress"),
    (r"\bvow my\b",             "my vow"),
    (r"\blife my\b",            "my life"),
    (r"\bbars its\b",           "its bars"),
    (r"\bneighbor his\b",       "his neighbor"),
    (r"\blocality his\b",       "his place"),
    (r"\bplace his\b",          "his place"),
    # Additional poetic-register possessive patterns (Jonah 2 / Psalms attested)
    (r"\bsalvation my\b",       "my salvation"),
    (r"\bsalvation his\b",      "his salvation"),
    (r"\bdeliverance my\b",     "my deliverance"),
    (r"\blove your\b",          "your love"),
    (r"\bmercy your\b",         "your mercy"),
    (r"\bfaithfulness your\b",  "your faithfulness"),
    (r"\bkingdom his\b",        "his kingdom"),
    (r"\bglory his\b",          "his glory"),
    (r"\bstrength his\b",       "his strength"),
    (r"\bpower his\b",          "his power"),
    (r"\bright his\b",          "his right"),
    (r"\bright hand his\b",     "his right hand"),
    (r"\bname your\b",          "your name"),
    (r"\bpraise your\b",        "your praise"),
    (r"\bword your\b",          "your word"),
    (r"\bcommandments your\b",  "your commandments"),
    (r"\bstatutes your\b",      "your statutes"),
    (r"\bways your\b",          "your ways"),
    (r"\bwork your\b",          "your work"),
    (r"\bworks your\b",         "your works"),
    (r"\blight your\b",         "your light"),
    (r"\btruth your\b",         "your truth"),
    (r"\bpath my\b",            "my path"),
    (r"\bway my\b",             "my way"),
    (r"\btrust my\b",           "my trust"),
    (r"\bhope my\b",            "my hope"),
    (r"\brock my\b",            "my rock"),
    (r"\bshield my\b",          "my shield"),
    (r"\bsong my\b",            "my song"),
    (r"\brefuge my\b",          "my refuge"),
    (r"\bstrength my\b",        "my strength"),
    (r"\bhelp my\b",            "my help"),
    # -----------------------------------------------------------------------
    # 5. Poetry-aware: double-gloss dedup.
    # Macula sometimes emits two English tokens for a single Hebrew adverbial
    # (e.g. לְעוֹלָם → "forever of perpetuity" where both tokens mean "forever").
    # Deduplicate the most common compound-morpheme over-emissions.
    # Rule: when the same semantic content appears twice in close proximity,
    # collapse to one.
    # -----------------------------------------------------------------------
    (r"\bforever of perpetuity\b",   "forever"),
    (r"\bperpetually forever\b",     "forever"),
    (r"\bforever and ever ever\b",   "forever and ever"),
    (r"\beternity forever\b",        "forever"),
    (r"\bforever eternity\b",        "forever"),
    # Reduplication artifact: "I I" (waw + pronoun both glossed as subject)
    (r"\bI I\b",                     "I"),
    # -----------------------------------------------------------------------
    # 6. Poetry-aware: vocative O-particle insertion.
    # When a divine name appears immediately before a first-person verb in
    # a prayer/address context (no intervening conjunction or preposition),
    # insert vocative "O" and a comma.
    # Detection: name immediately followed by first-person action verb.
    # -----------------------------------------------------------------------
    # "Yahweh I remembered" → "O Yahweh, I remembered" (Jonah 2:8 pattern)
    # "Yahweh I called" → "O Yahweh, I called"
    # The pattern fires when the name is not already preceded by "to"/"before"
    # (preposition-governed position signals indirect object, not vocative).
    (r"(?<!\bto )\bYahweh I (remembered|called|cried|prayed|sang|sing|praise|praised|thank|thanked|bless|blessed|seek|sought|answered|heard|saved|delivered)\b",
                                          r"O Yahweh, I \1"),
    # Line-initial: "Yahweh my God" direct address in prayer
    (r"^(O )?Yahweh my God\b",           r"O Yahweh my God"),
    # -----------------------------------------------------------------------
    # 7. NP-Demonstrative reorder ("the X this/that" → "this/that X")
    # Hebrew: definite noun + definite demonstrative (הָאִישׁ הַזֶּה)
    # -----------------------------------------------------------------------
    (r"\bthe man this\b",       "this man"),
    (r"\bthe woman this\b",     "this woman"),
    (r"\bthe city this\b",      "this city"),
    (r"\bthe house this\b",     "this house"),
    (r"\bthe day this\b",       "this day"),
    (r"\bthe storm this\b",     "this storm"),
    (r"\bthe evil this\b",      "this evil"),
    (r"\bthe thing this\b",     "this thing"),
    (r"\bthe word this\b",      "this word"),
    (r"\bthe place this\b",     "this place"),
    (r"\bthe people this\b",    "this people"),
    (r"\bthe land this\b",      "this land"),
    (r"\bthe man that\b",       "that man"),
    (r"\bthe woman that\b",     "that woman"),
    (r"\bthe city that\b",      "that city"),
    (r"\bthe day that\b",       "that day"),
    # -----------------------------------------------------------------------
    # 8. Predicate-nominative pronoun-fronting ("am X I" → "I am X")
    # Hebrew: PRED + COPULA-zero + PRONOUN
    # -----------------------------------------------------------------------
    (r"\bam a (\w+) I\b",       r"I am a \1"),
    (r"\bam an (\w+) I\b",      r"I am an \1"),
    (r"\bam (\w+) I\b",         r"I am \1"),
    # -----------------------------------------------------------------------
    # 9. "for am knowing I" / "am knowing I" → "for I know" / "I know"
    # (Jonah 1:12 — verbal copula with participle)
    # -----------------------------------------------------------------------
    (r"\bfor am knowing I\b",   "for I know"),
    (r"\bam knowing I\b",       "I know"),
    # -----------------------------------------------------------------------
    # 10. Particle reorder
    # -----------------------------------------------------------------------
    (r"\bdo not please\b",      "please do not"),
    # "tell please to us" → "tell us please"
    (r"\btell please to us\b",  "tell us please"),
    # -----------------------------------------------------------------------
    # 11. Interrogative cleanup: remove stranded "what?" / "where?" etc
    # that survive after morph-level lookup (Macula emits "what?" as a gloss).
    # Replace with plain "what" / "where" etc.
    # -----------------------------------------------------------------------
    (r"\bwhat\?\b",  "what"),
    (r"\bwhere\?\b", "where"),
    (r"\bwho\?\b",   "who"),
    (r"\bhow\?\b",   "how"),
    (r"\bwhy\?\b",   "why"),
    # -----------------------------------------------------------------------
    # 12. Double-article cleanup
    # -----------------------------------------------------------------------
    (r"\bthe the\b", "the"),
    # -----------------------------------------------------------------------
    # 13. Common Hebrew attributive-adjective reorder ("noun adj" → "adj noun").
    # Hebrew: NOUN + ADJECTIVE (both definite or both indefinite).
    # These are the most frequent Jonah / narrative-prose patterns.
    # -----------------------------------------------------------------------
    (r"\ba wind great\b",          "a great wind"),
    (r"\ba storm great\b",         "a great storm"),
    (r"\ba fish great\b",          "a great fish"),
    (r"\ba city great\b",          "a great city"),
    (r"\ba fear great\b",          "great fear"),
    (r"\bthe wind great\b",        "the great wind"),
    (r"\bthe storm great\b",       "the great storm"),
    (r"\bthe fish great\b",        "the great fish"),
    (r"\bthe city great\b",        "the great city"),
    (r"\bthe fear great\b",        "the great fear"),
    (r"\bthe day great\b",         "the great day"),
    # Generalized: "the <noun> great" → "the great <noun>" (any single-word noun)
    (r"\bthe (\w+) great\b",       r"the great \1"),
    (r"\bthe (\w+) (\w+) great\b", r"the great \1 \2"),  # 2-word noun (e.g. "sea monsters")
    (r"\ba (\w+) great\b",         r"a great \1"),
    (r"\ba day one\b",             "one day"),
    # לֵאמֹר often glosses as stranded "to" at end of speech-frame line.
    # Replace with "saying" when preceded by a speech verb on the same line.
    (r"\b(blessed|said|spoke|told|commanded|cried|called|answered|asked|swore|declared|charged|warned|sworn|declared|proclaimed)\s+(\w+(?:\s+\w+){0,4})\s+to$",
                                   r"\1 \2 saying"),
    (r"\bdays three\b",            "three days"),
    (r"\bnights three\b",          "three nights"),
    (r"\bdays forty\b",            "forty days"),
    # -----------------------------------------------------------------------
    # 13b. Generalized NP+ADJ reorder (Class 2 of 2026-05-05 four-class
    # spec). Hebrew default is NP + ADJ; English fronts the adjective. The
    # closed list below is restricted to UNAMBIGUOUS attributive adjectives
    # — words that are very rarely a noun in biblical English. Excluded
    # from the list (despite being common in Hebrew) because they overlap
    # with nouns or quantifiers:
    #   good, bad, evil          — frequently nouns ("good and evil")
    #   one, first, second, etc. — quantifiers / numerals
    #   right, left              — direction nouns
    #   true, false              — predicates more often than attributives
    # The "very" rule (16 below) handles the adverbial-intensifier surface
    # which is structurally similar but distinct.
    # Pattern matches both "the <noun> <adj>" (definite NP) and
    # "a <noun> <adj>" (indefinite NP) and bare "<noun> <adj>"; only the
    # determiner-bearing forms reorder safely (bare NP+ADJ is too FP-prone).
    # The (\w+) for <noun> excludes adjectives themselves to prevent
    # cascading swaps like "the great fierce wind" mis-firing.
    # -----------------------------------------------------------------------
    # Definite NP+ADJ: "the <noun> <adj>" → "the <adj> <noun>"
    (r"\bthe (\w+) (foreign|strange|holy|sacred|profane|mighty|valiant|"
     r"fierce|gentle|righteous|wicked|beautiful|ugly|wise|foolish|"
     r"hidden|exalted|humble|humbled|honest|"
     r"rich|poor|wealthy|delicate|"
     r"strong|weak|stout|tender|firm|loose|"
     r"long|short|tall|deep|shallow|wide|narrow|broad|thick|thin|"
     r"hot|cold|wet|dry|hard|soft|sweet|bitter|"
     r"loud|quiet|swift|slow|"
     r"alive|dead|fertile|barren|fruitful|"
     r"angry|sad|happy|ashamed|"
     r"perfect|imperfect|broken|whole|complete|"
     r"heavy|light|severe|"
     r"high|low|"
     r"old|young|new|"
     r"large|small|big|little|"
     r"many|much|numerous|"
     r"abundant|scarce|"
     r"weary|tired|patient|bold|timid|"
     r"proud|"
     r"afraid|"
     r"red|black|white|green|blue)\b",
     r"the \2 \1"),
    # Indefinite NP+ADJ: "a <noun> <adj>" → "a <adj> <noun>"
    (r"\ba (\w+) (foreign|strange|holy|sacred|profane|mighty|valiant|"
     r"fierce|gentle|righteous|wicked|beautiful|ugly|wise|foolish|"
     r"hidden|exalted|humble|humbled|honest|"
     r"rich|poor|wealthy|delicate|"
     r"strong|weak|stout|tender|firm|loose|"
     r"long|short|tall|deep|shallow|wide|narrow|broad|thick|thin|"
     r"hot|cold|wet|dry|hard|soft|sweet|bitter|"
     r"loud|quiet|swift|slow|"
     r"alive|dead|fertile|barren|fruitful|"
     r"angry|sad|happy|ashamed|"
     r"perfect|imperfect|broken|whole|complete|"
     r"heavy|light|severe|"
     r"high|low|"
     r"old|young|new|"
     r"large|small|big|little|"
     r"many|much|numerous|"
     r"abundant|scarce|"
     r"weary|tired|patient|bold|timid|"
     r"proud|"
     r"afraid|"
     r"red|black|white|green|blue)\b",
     r"a \2 \1"),
    # "an <vowel-initial-noun> <adj>" — same swap; "an" handled separately
    (r"\ban (\w+) (foreign|strange|holy|sacred|profane|mighty|valiant|"
     r"fierce|gentle|righteous|wicked|beautiful|ugly|wise|foolish|"
     r"hidden|exalted|humble|humbled|honest|"
     r"rich|poor|wealthy|delicate|"
     r"strong|weak|stout|tender|firm|loose|"
     r"long|short|tall|deep|shallow|wide|narrow|broad|thick|thin|"
     r"hot|cold|wet|dry|hard|soft|sweet|bitter|"
     r"loud|quiet|swift|slow|"
     r"alive|dead|fertile|barren|fruitful|"
     r"angry|sad|happy|ashamed|"
     r"perfect|imperfect|broken|whole|complete|"
     r"heavy|light|severe|"
     r"high|low|"
     r"old|young|new|"
     r"large|small|big|little|"
     r"many|much|numerous|"
     r"abundant|scarce|"
     r"weary|tired|patient|bold|timid|"
     r"proud|"
     r"afraid|"
     r"red|black|white|green|blue)\b",
     r"an \2 \1"),
    # -----------------------------------------------------------------------
    # 14. VS→SV reorder for wayyiqtol-initial narrative.
    # These are the most frequent instances in Jonah 1.
    # Pattern: "and he/they/it [VERB] the/a [SUBJECT]" → SVO order.
    # Applied via targeted phrase patterns (regex is limited here; full
    # morphology-driven reorder would require structural tagging).
    # -----------------------------------------------------------------------
    (r"\band he arose (Jonah)\b",               r"and \1 arose"),
    (r"\band he went down (Joppa)\b",           r"and he went down to \1"),
    (r"\band they were afraid the (mariners|men|sailors)\b",
                                                r"and the \1 were afraid"),
    (r"\band it fell the lot\b",                "and the lot fell"),
    (r"\band they rowed the men\b",             "and the men rowed"),
    (r"\band it stopped the sea\b",             "and the sea stopped"),
    (r"\band the sea stopped\b",                "and the sea stopped"),
    (r"\band he arose Yahweh\b",                "and Yahweh he hurled"),  # 1:4 special
    # -----------------------------------------------------------------------
    # 16. Adverbial-intensifier reorder: "<adj> very" → "very <adj>"
    # Hebrew מְאֹד typically follows the intensified word; English fronts it.
    # Closed list of adjectives/quantifiers commonly intensified by very
    # (audit 2026-05-04: 105 corpus pairs, top tokens great/much/many/numerous
    # /heavy/good/strong/afraid/old/severe/high/proud/bad — all reorder cleanly;
    # pronoun/particle FPs (me/you/she/it) deliberately excluded by closed list).
    # -----------------------------------------------------------------------
    (r"\b(good|great|much|many|numerous|heavy|strong|afraid|old|severe|high|proud|bad|wealthy|delicate|large|big|small|tall|short|near|far|deep|shallow|hot|cold|wet|dry|hard|soft|slow|fast|long|wide|narrow|thick|thin|loud|quiet|sweet|bitter|holy|righteous|wicked|evil|beautiful|ugly|wise|foolish|young|new|old|fat|lean|rich|poor|happy|sad|angry|ashamed|exalted|humbled|low|mighty|weak|fierce|gentle|bold|timid|patient|swift|slow|abundant|scarce|fruitful|barren|fertile|broad|tight|loose|firm|weary|tired|strong|valiant|stout|tender) very\b", r"very \1"),
    # -----------------------------------------------------------------------
    # 15. Collapse multiple whitespace (always last)
    # -----------------------------------------------------------------------
    (r"  +", " "),
]


# ---------------------------------------------------------------------------
# Unicode utilities
# ---------------------------------------------------------------------------

def strip_pointing(text: str) -> str:
    """Strip te'amim and niqqud; keep consonants + maqqef. NFC-normalize first.

    Maqqef (U+05BE) is preserved because word-level matching needs it to
    distinguish tokens. Use normalize_for_phrase() when comparing to phrase-map
    keys (which treats maqqef as a word separator).
    """
    nfc = unicodedata.normalize("NFC", text)
    return DIACRITICS_RE.sub("", nfc)


def normalize_for_phrase(text: str) -> str:
    """Strip pointing + normalize maqqef to space + strip sof pasuq + collapse spaces.

    Use this for phrase-map key comparison so that 'וַיִּזְבְּחוּ זֶבַח' and
    'וַיִּזְבְּחוּ־זֶבַח' (maqqef variant) both match the same phrase-map entry.
    """
    stripped = strip_pointing(text)
    # Normalize maqqef → space (maqqef-joined words should match space-separated keys)
    normalized = stripped.replace(MAQQEF, " ")
    # Remove sof pasuq
    normalized = normalized.replace(SOF_PASUQ, "")
    # Paseq U+05C0 may survive; remove it too
    normalized = normalized.replace("׀", "")
    # Collapse multiple spaces
    normalized = re.sub(r"  +", " ", normalized).strip()
    return normalized


# ---------------------------------------------------------------------------
# TSV loader
# ---------------------------------------------------------------------------

def load_macula_tsv(book_prefix: str | None = None) -> dict:
    """Load Macula Hebrew TSV into a dict: ref → list[dict of morpheme fields].

    If book_prefix is given (e.g. 'JON'), only rows for that book are loaded,
    which keeps memory use low for single-book runs. Pass None to load all.
    """
    if not MACULA_TSV.exists():
        sys.exit(f"ERROR: Macula Hebrew TSV not found at {MACULA_TSV}")
    size_mb = MACULA_TSV.stat().st_size // 1024 // 1024
    scope = f" (filtering to {book_prefix})" if book_prefix else ""
    print(f"Loading Macula Hebrew TSV ({size_mb} MB){scope}...")
    by_ref: dict[str, list[dict]] = defaultdict(list)
    loaded = 0
    with MACULA_TSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            ref = row.get("ref", "").strip()
            if not ref:
                continue
            if book_prefix and not ref.startswith(book_prefix + " "):
                continue
            by_ref[ref].append({
                "text":    row.get("text",    ""),
                "gloss":   row.get("gloss",   ""),
                "english": row.get("english", ""),
                "morph":   row.get("morph",   ""),
                "type":    row.get("type",    ""),
                "pos":     row.get("pos",     ""),
                "state":   row.get("state",   ""),
                "after":   row.get("after",   ""),
            })
            loaded += 1
    total_words = len(by_ref)
    print(f"  Loaded {loaded:,} morpheme rows across {total_words:,} word positions.")
    return dict(by_ref)


# ---------------------------------------------------------------------------
# Per-word gloss aggregation
# ---------------------------------------------------------------------------

def aggregate_word_gloss(morph_rows: list[dict]) -> str:
    """Aggregate morpheme glosses for one word position into a single English token.

    Strategy:
    - Collect non-empty, non-trivial gloss fields.
    - Replace dot-notation separators with spaces (Cherith: "it.came" → "it came").
    - Filter out empty/trivial gloss tokens (dm, cmp, et, the).
    - If no usable gloss, fall back to english field.
    - Prefer gloss field always (uses 'Yahweh', not 'LORD').
    """
    parts = []
    for row in morph_rows:
        g = row.get("gloss", "").strip()
        # Replace dot-notation with spaces (Cherith morpheme separator)
        # e.g. "it.came" → "it came", "(dm).that" → "(dm) that"
        g = g.replace(".", " ")
        # Class 4 (Stan 2026-05-05): strip ALL parenthetical annotations from
        # Macula gloss output. The annotations are scaffolding (preposition
        # expansion `(in)`, `(into)`, `(of)`, `(to)`; ellipsis filler `(et)`;
        # discourse marker `(dm)`; complementizer `(cmp)`; plurality hedge
        # `(s)`; etc.) that surface as ungrammatical English noise. They
        # belong in the interlinear layer, not the gloss layer.
        # Cherith census (2026-05-04): (et) 9303, (the) 7098, (dm) 4370,
        # (cmp) 1106 covered the bulk; the long tail includes (in) (into)
        # (of) (to) (s) (eat) (die) etc. Drop all parens entirely.
        g = re.sub(r"\([^\)]*\)\s*", "", g)
        # Skip fully trivial/empty tokens (whole gloss is a tag or blank)
        g_stripped = g.strip()
        if g_stripped.lower() in EMPTY_GLOSS_TOKENS:
            continue
        # Strip bracketed-optional markers like "[was]" / "[has been]" → keep
        # the content word inside. Brackets in Macula mark interpretive
        # ellipsis-fillers (often copulas / aspectual verbs) that improve
        # English flow when integrated as plain words. Drop the brackets,
        # keep the content. Repeat until convergence to handle nested cases
        # like "[was [the] one]". Then strip any UNMATCHED brackets too —
        # Macula sometimes splits a bracketed phrase across morphemes
        # (e.g. בְּעֶזְרִי emits "[has", "been](in)", "my.help" as three
        # rows; the bracket characters straddle morpheme boundaries).
        prev = None
        while g_stripped != prev:
            prev = g_stripped
            g_stripped = re.sub(r"\[([^\]]*)\]", r"\1", g_stripped)
        # Drop any leftover bracket characters (unmatched in this morpheme).
        g_stripped = g_stripped.replace("[", "").replace("]", "")
        # Collapse extra whitespace introduced by bracket / paren strip.
        g_stripped = re.sub(r"\s+", " ", g_stripped).strip()
        if g_stripped:
            parts.append(g_stripped)

    if parts:
        return " ".join(parts)

    # Fallback: use english field of any morpheme that has non-trivial content.
    for row in morph_rows:
        e = row.get("english", "").strip()
        if e and e not in {"", "the", "a", "an"}:
            return e
    # Last resort: join all english fields
    en_parts = [r.get("english", "").strip() for r in morph_rows if r.get("english", "").strip()]
    if en_parts:
        return " ".join(en_parts)

    # All morphemes were empty or trivial (e.g. pure (et) accusative marker,
    # or (dm) discourse marker with empty english). Skip this token silently.
    return SKIP_TOKEN


# ---------------------------------------------------------------------------
# Verse-word lookup
# ---------------------------------------------------------------------------

def lookup_verse_words(by_ref: dict, osis_book: str, ch: int, vs: int) -> list[list[dict]]:
    """Return ordered list of word-positions for a verse.

    Each element is a list of morpheme rows sharing the same ref (same word position).
    Iterates ref values matching '<OSIS> <ch>:<vs>!N' for N=1..M.
    """
    prefix = f"{osis_book} {ch}:{vs}!"
    word_positions = []
    n = 1
    while True:
        ref = f"{prefix}{n}"
        rows = by_ref.get(ref)
        if not rows:
            break
        word_positions.append(rows)
        n += 1
    return word_positions


# ---------------------------------------------------------------------------
# Per-cola gloss generation
# ---------------------------------------------------------------------------

def gloss_cola(
    hebrew_cola: str,
    verse_words: list[list[dict]],
    consumed: list[bool],
    verbose: bool = False,
) -> str:
    """Generate English gloss for one Hebrew cola.

    Steps:
    1. Normalize cola (strip pointing, maqqef→space, remove sof pasuq).
    2. Try HEBREW_PHRASE_MAP full-cola match (exact normalized comparison).
    3. Try HEBREW_PHRASE_MAP prefix match (cola starts with phrase; emit phrase
       then continue per-word for remainder, marking consumed words).
    4. Per-word Macula lookup: for each Hebrew token, find matching unconsumed
       verse-word by stripped-surface comparison; aggregate morpheme glosses.
    5. Join word-glosses; apply NATURALIZE_RULES.
    """
    cola_norm = normalize_for_phrase(hebrew_cola)

    # ------------------------------------------------------------------
    # Step 1: full-cola phrase-map match (exact normalized)
    # ------------------------------------------------------------------
    if cola_norm in _PHRASE_MAP_NORMALIZED:
        result = _PHRASE_MAP_NORMALIZED[cola_norm]
        if verbose:
            print(f"    [PHRASE-MAP full] {hebrew_cola!r} → {result!r}")
        # Mark all verse-words consumed so downstream verses track correctly
        for i in range(len(consumed)):
            consumed[i] = True
        return result

    # ------------------------------------------------------------------
    # Step 2: prefix phrase-map match (cola starts with phrase key).
    # If matched, emit the phrase text, then continue per-word for the
    # remaining Hebrew tokens (already-consumed words tracked via consumed[]).
    # ------------------------------------------------------------------
    prefix_match_en: str | None = None
    prefix_match_word_count: int = 0

    for norm_key in sorted(_PHRASE_MAP_NORMALIZED.keys(), key=len, reverse=True):
        if not norm_key:
            continue
        # Check if the cola normalization starts with this key.
        # Must be followed by end-of-string or a space (word boundary).
        if cola_norm == norm_key or cola_norm.startswith(norm_key + " "):
            prefix_match_en = _PHRASE_MAP_NORMALIZED[norm_key]
            # How many whitespace-separated words does the key contain?
            prefix_match_word_count = len(norm_key.split())
            if verbose:
                print(f"    [PHRASE-MAP prefix] {hebrew_cola!r} prefix={norm_key!r} → {prefix_match_en!r}")
            break

    # ------------------------------------------------------------------
    # Step 3: per-word lookup (always runs; prefix match consumes leading words)
    # ------------------------------------------------------------------
    # Tokenize the cola on whitespace; maqqef-joined words stay as single tokens.
    cola_tokens = hebrew_cola.split()
    out_tokens: list[str] = []

    # If a prefix phrase matched, inject its English output first, then skip
    # the Hebrew tokens that were covered by the phrase (by marking verse-words
    # consumed). We count cola tokens consumed by the phrase by matching them
    # sequentially against verse-words.
    skip_cola_tokens = 0
    if prefix_match_en is not None:
        out_tokens.append(prefix_match_en)
        # Consume verse-words corresponding to the phrase's cola tokens.
        # Strategy: walk cola tokens; for each, expand maqqef sub-tokens and
        # greedily consume verse-words. Stop when we've consumed
        # `prefix_match_word_count` normalized-phrase words (counted by the
        # space-separated words in the matched key).
        phrase_norm_words_consumed = 0
        for ci, cw in enumerate(cola_tokens):
            if phrase_norm_words_consumed >= prefix_match_word_count:
                skip_cola_tokens = ci
                break
            cw_clean = cw.replace(SOF_PASUQ, "").replace("׀", "")
            cw_stripped_mq = strip_pointing(cw_clean)
            # Each maqqef-sub-token counts as one Macula word position
            cw_parts = [p for p in cw_stripped_mq.split(MAQQEF) if p]
            if not cw_parts:
                cw_parts = [cw_stripped_mq]
            for cw_sub in cw_parts:
                if phrase_norm_words_consumed >= prefix_match_word_count:
                    break
                for i, word_rows in enumerate(verse_words):
                    if consumed[i]:
                        continue
                    word_surface = "".join(
                        strip_pointing(r.get("text", "")) for r in word_rows
                    ).replace(MAQQEF, "")
                    # Liberal match: prefix agreement
                    if cw_sub and word_surface and cw_sub[:2] == word_surface[:2]:
                        consumed[i] = True
                        break
                    elif not cw_sub or not word_surface:
                        consumed[i] = True
                        break
                phrase_norm_words_consumed += 1
        else:
            # Loop completed without break → phrase covered all cola tokens
            skip_cola_tokens = len(cola_tokens)

    for cw in cola_tokens[skip_cola_tokens:]:
        # Strip end-of-verse markers and paseq from the token
        cw_clean = cw.replace(SOF_PASUQ, "").replace("׀", "")  # ׃ ׀

        # MAQQEF EXPANSION: a whitespace-separated token may contain maqqef,
        # meaning it spans multiple Macula word positions (e.g. "אֶל־יְהוָה"
        # covers word positions !N and !N+1). Strip pointing, then split on
        # maqqef (which strip_pointing now preserves). Each sub-token is
        # matched to one Macula word position, and the resulting glosses
        # are joined with a space.
        #
        # For the non-maqqef case (most tokens), cw_parts has one element.
        cw_stripped_with_mq = strip_pointing(cw_clean)
        # Split on maqqef to get sub-tokens; filter empty strings
        cw_parts = [p for p in cw_stripped_with_mq.split(MAQQEF) if p]
        if not cw_parts:
            cw_parts = [cw_stripped_with_mq]  # safety

        for cw_cons in cw_parts:
            matched = False

            # --- Primary: exact stripped-consonant surface match ---
            for i, word_rows in enumerate(verse_words):
                if consumed[i]:
                    continue
                # Build consonant surface for this word position by joining all
                # morpheme text fields (strip pointing, remove maqqef).
                word_surface = "".join(
                    strip_pointing(r.get("text", "")) for r in word_rows
                ).replace(MAQQEF, "")
                if word_surface == cw_cons:
                    gloss_tok = aggregate_word_gloss(word_rows)
                    consumed[i] = True
                    matched = True
                    if gloss_tok != SKIP_TOKEN:
                        out_tokens.append(gloss_tok)
                    if verbose:
                        print(f"      [exact-match] {cw_cons!r} → {gloss_tok!r}")
                    break

            if not matched:
                # --- Fallback: prefix / partial consonant match ---
                if len(cw_cons) >= 2:
                    for i, word_rows in enumerate(verse_words):
                        if consumed[i]:
                            continue
                        word_surface = "".join(
                            strip_pointing(r.get("text", "")) for r in word_rows
                        ).replace(MAQQEF, "")
                        # Accept if first 2 consonants match and lengths are similar
                        if (word_surface
                                and cw_cons[:2] == word_surface[:2]
                                and abs(len(cw_cons) - len(word_surface)) <= 3):
                            gloss_tok = aggregate_word_gloss(word_rows)
                            consumed[i] = True
                            matched = True
                            if gloss_tok != SKIP_TOKEN:
                                out_tokens.append(gloss_tok)
                            if verbose:
                                print(f"      [prefix-match] {cw_cons!r} ~ {word_surface!r} → {gloss_tok!r}")
                            break

            if not matched:
                # --- Sequential fallback: next unconsumed word ---
                for i, word_rows in enumerate(verse_words):
                    if consumed[i]:
                        continue
                    gloss_tok = aggregate_word_gloss(word_rows)
                    consumed[i] = True
                    matched = True
                    if gloss_tok != SKIP_TOKEN:
                        out_tokens.append(gloss_tok)
                    if verbose:
                        print(f"      [seq-fallback] {cw_cons!r} → {gloss_tok!r}")
                    break

            if not matched:
                if verbose:
                    print(f"      [NO-MATCH] {cw_cons!r}")
                # Don't emit (?) for unmatched tokens — they're likely already
                # consumed by a phrase-map or are empty particles

    # ------------------------------------------------------------------
    # Step 4: join + naturalize
    # ------------------------------------------------------------------
    raw_text = " ".join(out_tokens)
    if verbose:
        print(f"    [raw] {raw_text!r}")
    text = naturalize(raw_text)
    if verbose:
        print(f"    [nat] {text!r}")
    return text


def naturalize(text: str) -> str:
    """Apply mechanical Hebrew→English transformations in order."""
    for pattern, replacement in NATURALIZE_RULES:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text.strip()


# ---------------------------------------------------------------------------
# Chapter processor
# ---------------------------------------------------------------------------

def process_chapter(
    book: str,
    chapter_filename: str,
    by_ref: dict,
    osis_book: str,
    use_v1: bool,
    dry_run: bool,
    verbose: bool,
) -> list[str] | None:
    """Generate gloss for one chapter file. Returns output lines or None if skipped."""
    # Source cascade: v2/he preferred, v1/he-baseline fallback.
    src_path = None
    if not use_v1:
        candidate = V2_HE_DIR / book / chapter_filename
        if candidate.exists():
            src_path = candidate
    if src_path is None:
        candidate = V1_HE_DIR / book / chapter_filename
        if candidate.exists():
            src_path = candidate

    if src_path is None:
        print(f"  SKIP {chapter_filename}: not found in v2/he or v1/he-baseline")
        return None

    if verbose:
        print(f"  Processing {chapter_filename} from {src_path}")

    out_lines: list[str] = []
    current_verse: str | None = None
    verse_words: list[list[dict]] = []
    consumed: list[bool] = []

    for raw in src_path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        stripped = line.strip()

        if VERSE_REF_RE.match(stripped):
            current_verse = stripped
            ch_str, vs_str = current_verse.split(":")
            verse_words = lookup_verse_words(by_ref, osis_book, int(ch_str), int(vs_str))
            consumed = [False] * len(verse_words)
            out_lines.append(line)
            if verbose:
                print(f"\n  === verse {current_verse} ({len(verse_words)} word positions) ===")
            continue

        if stripped == "":
            out_lines.append(line)
            continue

        if current_verse is None:
            # Header line before first verse ref (shouldn't normally appear)
            out_lines.append(line)
            continue

        # Hebrew cola line
        gloss = gloss_cola(stripped, verse_words, consumed, verbose=verbose)
        out_lines.append(gloss)

    if dry_run:
        print(f"  {chapter_filename} (dry-run): would write to {OUT_DIR / book / chapter_filename}")
        print()
        for ln in out_lines[:40]:
            print(f"    {ln}")
        if len(out_lines) > 40:
            print(f"    ... ({len(out_lines)} lines total)")
    else:
        out_path = OUT_DIR / book / chapter_filename
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        print(f"  {chapter_filename}: wrote {out_path}")

    return out_lines


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _collect_books_with_chapters(use_v1: bool) -> list[tuple[str, list[str]]]:
    """Return [(book_folder, [chapter_filenames, ...]), ...] for all books with content.

    Prefers v2/he; falls back to v1/he-baseline per chapter, same as process_chapter().
    Only returns books that have at least one chapter file.
    """
    results = []
    for book_folder in sorted(BOOK_OSIS.keys()):
        src_dir_v2 = V2_HE_DIR / book_folder
        src_dir_v1 = V1_HE_DIR / book_folder
        chapter_files = sorted(
            {p.name for p in src_dir_v2.glob("*.txt") if src_dir_v2.exists()}
            | {p.name for p in src_dir_v1.glob("*.txt") if src_dir_v1.exists()}
        )
        if chapter_files:
            results.append((book_folder, chapter_files))
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    book_group = ap.add_mutually_exclusive_group(required=True)
    book_group.add_argument("--book",      help="Book folder name, e.g. 05-jonah")
    book_group.add_argument("--all-books", action="store_true",
                            help="Generate glosses for every book that has content in v2/he or v1/he-baseline")
    ap.add_argument("--use-v1", action="store_true",
                    help="Generate from v1/he-baseline instead of v2/he")
    ap.add_argument("--dry-run", action="store_true",
                    help="Don't write output files; print preview")
    ap.add_argument("--verbose", action="store_true",
                    help="Print each cola's Hebrew + generated gloss with match details")
    args = ap.parse_args()

    # Build phrase-map index (stripped keys).
    _build_phrase_map_index()

    if args.all_books:
        # Collect all books that have content.
        books_with_chapters = _collect_books_with_chapters(args.use_v1)
        if not books_with_chapters:
            sys.exit("ERROR: no book directories with .txt chapter files found under v2/he or v1/he-baseline")

        print(f"Found {len(books_with_chapters)} book(s) with content.")
        total_chapters = sum(len(chs) for _, chs in books_with_chapters)
        print(f"Total chapters to process: {total_chapters}")

        # For --all-books, load full Macula TSV once (no per-book filter).
        by_ref_all = load_macula_tsv(book_prefix=None)

        grand_total_cola = 0
        for book_folder, chapter_files in books_with_chapters:
            osis_book = BOOK_OSIS[book_folder]
            print(f"\n--- {book_folder} ({osis_book}) — {len(chapter_files)} chapter(s) ---")
            book_cola = 0
            for cf_name in chapter_files:
                out_lines = process_chapter(
                    book=book_folder,
                    chapter_filename=cf_name,
                    by_ref=by_ref_all,
                    osis_book=osis_book,
                    use_v1=args.use_v1,
                    dry_run=args.dry_run,
                    verbose=args.verbose,
                )
                if out_lines is not None:
                    cola_count = sum(
                        1 for ln in out_lines
                        if ln.strip() and not VERSE_REF_RE.match(ln.strip())
                    )
                    book_cola += cola_count
            grand_total_cola += book_cola
            print(f"  {book_folder}: {len(chapter_files)} chapters, ~{book_cola} cola")

        print(f"\n=== All-books complete: {len(books_with_chapters)} books, "
              f"{total_chapters} chapters, ~{grand_total_cola} cola ===")
        if args.dry_run:
            print("Dry-run: no files written.")

    else:
        # Single-book mode.
        osis_book = BOOK_OSIS.get(args.book)
        if not osis_book:
            sys.exit(
                f"ERROR: no OSIS mapping for book {args.book!r} — add to BOOK_OSIS dict.\n"
                f"Known books: {', '.join(sorted(BOOK_OSIS))}"
            )

        # Determine chapter files from the available Hebrew tiers.
        src_dir_v2 = V2_HE_DIR / args.book
        src_dir_v1 = V1_HE_DIR / args.book
        all_chapter_files = sorted(
            {p.name for p in src_dir_v2.glob("*.txt") if src_dir_v2.exists()}
            | {p.name for p in src_dir_v1.glob("*.txt") if src_dir_v1.exists()}
        )
        if not all_chapter_files:
            sys.exit(f"ERROR: no .txt chapter files found under {src_dir_v2} or {src_dir_v1}")

        # Load Macula TSV filtered to this book.
        by_ref = load_macula_tsv(book_prefix=osis_book)

        print(f"\nGenerating gloss for {args.book} ({len(all_chapter_files)} chapters)...")
        for cf_name in all_chapter_files:
            process_chapter(
                book=args.book,
                chapter_filename=cf_name,
                by_ref=by_ref,
                osis_book=osis_book,
                use_v1=args.use_v1,
                dry_run=args.dry_run,
                verbose=args.verbose,
            )

        if not args.dry_run:
            print(f"\nDone. Output: {OUT_DIR / args.book}/")
        else:
            print(f"\nDry-run complete. No files written.")


if __name__ == "__main__":
    main()
