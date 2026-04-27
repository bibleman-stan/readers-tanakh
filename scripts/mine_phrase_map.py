#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mine_phrase_map.py — Mine Macula Hebrew TSV for high-frequency phrase patterns.

Produces data/lookup/hebrew-phrase-map.json with 200-500 entries covering:
  - Prophetic openers/closers (כה אמר יהוה, נאם יהוה, etc.)
  - Vocative formulas (שמע, אשרי, הוי, etc.)
  - Compound divine names (Rule H9 candidates)
  - Liturgical formulas (ברוך, הללויה, חי יהוה, etc.)
  - Discourse markers (הנה, אל נא, etc.)
  - Genealogical formulas (Rule H17)
  - Temporal formulas
  - Cognate-accusative idioms
  - Blessing/curse formulas
  - Narrative openers/closers

KEY DESIGN NOTE — Word reconstruction:
  Macula splits prefixed particles into separate morpheme rows at the SAME
  word position (same 12-char xml:id prefix). We reconstruct word-level
  surface text by concatenating text fields within each word group (no space),
  then space-join the reconstructed words per verse. This eliminates the
  "אדנ י" split problem and produces correct phrase matching.

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/mine_phrase_map.py
"""

import csv
import json
import re
import sys
import unicodedata
from collections import defaultdict, Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MACULA_TSV = REPO_ROOT / "research" / "macula-hebrew" / "WLC" / "tsv" / "macula-hebrew.tsv"
OUT_FILE   = REPO_ROOT / "data" / "lookup" / "hebrew-phrase-map.json"

# ---------------------------------------------------------------------------
# Unicode helpers
# ---------------------------------------------------------------------------
DIACRITICS_RE = re.compile(r"[֑-ֽֿ-ׂׄ-ׇ]")
MAQQEF = "־"   # ־ U+05BE
SOF_PASUQ = "׃"  # ׃ U+05C3


def strip_pointing(s: str) -> str:
    """Remove niqqud + cantillation; keep maqqef and consonants."""
    s = unicodedata.normalize("NFC", s)
    s = DIACRITICS_RE.sub("", s)
    s = s.replace(SOF_PASUQ, "")
    return s.strip()


def normalize_for_match(text: str) -> str:
    """Strip pointing, collapse maqqef to space, collapse whitespace."""
    t = strip_pointing(text)
    t = t.replace(MAQQEF, " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t


# ---------------------------------------------------------------------------
# Load Macula TSV and build word-level verse text index
#
# Macula xml:id format: o + BOOK(3) + CHAP(3) + VERSE(3) + WORD(2) + MORPH(2)
# = 1 + 3 + 3 + 3 + 2 + 2 = 14 chars total (0-indexed: [0:13])
# Word key = chars [:12] (book + chap + verse + word slots = 1+3+3+3+2 = 12)
# ---------------------------------------------------------------------------

def load_verse_texts(path: Path) -> tuple[dict, int, int]:
    """
    Returns:
        verse_texts: dict[ref_base -> str]  (word-reconstructed consonantal text)
        total_verses: int
        total_morphemes: int
    """
    print(f"Loading {path} ...", flush=True)

    # Pass 1: accumulate morpheme text per word-position, in corpus order
    word_texts: dict[str, list[str]] = {}   # word_key -> [morpheme_texts in order]
    word_to_ref: dict[str, str] = {}        # word_key -> ref_base
    word_order: list[str] = []              # ordered word keys (corpus order, deduplicated)
    seen_words: set[str] = set()

    total_morphemes = 0
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            total_morphemes += 1
            xid = row.get("xml:id", "")
            if not xid:
                continue
            word_key = xid[:12]
            ref_full = row.get("ref", "")
            ref_base = ref_full.split("!")[0].strip()
            text = row.get("text", "")

            if word_key not in seen_words:
                seen_words.add(word_key)
                word_order.append(word_key)
                word_texts[word_key] = []
                word_to_ref[word_key] = ref_base
            word_texts[word_key].append(text)

    # Pass 2: reconstruct word surface forms and group by verse
    # word surface = direct concatenation of morpheme texts (no separator)
    verse_words: dict[str, list[str]] = defaultdict(list)
    for wkey in word_order:
        ref = word_to_ref[wkey]
        reconstructed = "".join(t for t in word_texts[wkey] if t)
        normalized = normalize_for_match(reconstructed)
        if normalized:
            verse_words[ref].append(normalized)

    # Pass 3: join words into verse text string
    verse_texts = {ref: " ".join(words) for ref, words in verse_words.items()}
    total_verses = len(verse_texts)

    print(f"  Loaded {total_morphemes:,} morpheme rows → "
          f"{len(seen_words):,} words → {total_verses:,} verses.", flush=True)
    return verse_texts, total_verses, total_morphemes


# ---------------------------------------------------------------------------
# Seed phrase catalog
# ---------------------------------------------------------------------------

SEED_PHRASES = [
    # =========================================================================
    # PROPHETIC OPENERS
    # =========================================================================
    ("כֹּה אָמַר יְהוָה",              "thus says Yahweh",                        "prophetic-opener"),
    ("כֹּה אָמַר יְהוָה צְבָאוֹת",    "thus says Yahweh of hosts",               "prophetic-opener"),
    ("כֹּה אָמַר אֲדֹנָי יְהוִה",     "thus says the Lord Yahweh",               "prophetic-opener"),
    ("כֹּה אָמַר יְהוָה אֱלֹהֵי יִשְׂרָאֵל", "thus says Yahweh the God of Israel", "prophetic-opener"),
    ("כֹּה אָמַר יְהוָה אֱלֹהִים",    "thus says Yahweh God",                    "prophetic-opener"),
    ("כֹּה אָמַר יְהוָה אֱלֹהֵיכֶם",  "thus says Yahweh your God",               "prophetic-opener"),
    ("כֹּה אָמַר יְהוָה אֱלֹהֵי דָוִד", "thus says Yahweh the God of David",     "prophetic-opener"),
    ("כֹּה אָמַר",                     "thus says",                               "prophetic-opener"),
    ("אָמַר אֲדֹנָי יְהוִה",          "says the Lord Yahweh",                    "prophetic-opener"),
    ("אָמַר יְהוָה",                   "says Yahweh",                             "prophetic-opener"),
    # =========================================================================
    # PROPHETIC CLOSERS / DECLARATION FORMULAS
    # =========================================================================
    ("נְאֻם יְהוָה",                   "declares Yahweh",                         "prophetic-closer"),
    ("נְאֻם יְהוָה צְבָאוֹת",         "declares Yahweh of hosts",               "prophetic-closer"),
    ("נְאֻם אֲדֹנָי יְהוִה",          "declares the Lord Yahweh",               "prophetic-closer"),
    ("נְאֻם יְהוָה אֱלֹהֵיכֶם",       "declares Yahweh your God",               "prophetic-closer"),
    ("נְאֻם יְהוָה אֱלֹהֵי יִשְׂרָאֵל", "declares Yahweh the God of Israel",    "prophetic-closer"),
    ("נְאֻם יְהוָה אֱלֹהֵי הַצְּבָאוֹת", "declares Yahweh God of hosts",       "prophetic-closer"),
    # =========================================================================
    # WORD-OF-YAHWEH FORMULA
    # =========================================================================
    ("וַיְהִי דְבַר יְהוָה אֶל",      "and the word of Yahweh came to",         "word-formula"),
    ("וַיְהִי דְּבַר יְהוָה אֶל",     "and the word of Yahweh came to",         "word-formula"),
    ("וַיְהִי דְבַר יְהוָה",          "and the word of Yahweh came",            "word-formula"),
    ("וַיְהִי דְּבַר יְהוָה",         "and the word of Yahweh came",            "word-formula"),
    ("דְּבַר יְהוָה",                  "the word of Yahweh",                     "word-formula"),
    ("דְבַר יְהוָה",                   "the word of Yahweh",                     "word-formula"),
    ("דְּבַר אֱלֹהִים",               "the word of God",                         "word-formula"),
    # =========================================================================
    # COMPOUND DIVINE NAMES (Rule H9)
    # =========================================================================
    ("יְהוָה אֱלֹהִים",               "Yahweh God",                              "divine-name"),
    ("יְהוָה צְבָאוֹת",               "Yahweh of hosts",                         "divine-name"),
    ("יְהוָה אֱלֹהֵי יִשְׂרָאֵל",    "Yahweh the God of Israel",               "divine-name"),
    ("יְהוָה אֱלֹהֵינוּ",             "Yahweh our God",                          "divine-name"),
    ("יְהוָה אֱלֹהֵיכֶם",             "Yahweh your God",                         "divine-name"),
    ("יְהוָה אֱלֹהֶיךָ",              "Yahweh your God",                         "divine-name"),
    ("יְהוָה אֱלֹהַי",                "Yahweh my God",                           "divine-name"),
    ("יְהוָה אֱלֹהֵיהֶם",             "Yahweh their God",                        "divine-name"),
    ("יְהוָה אֱלֹהֵי הַשָּׁמַיִם",   "Yahweh the God of heaven",               "divine-name"),
    ("יְהוָה אֱלֹהֵי הָאָרֶץ",        "Yahweh the God of the earth",            "divine-name"),
    ("יְהוָה אֱלֹהֵי אֲבֹתֵיכֶם",    "Yahweh the God of your fathers",         "divine-name"),
    ("יְהוָה אֱלֹהֵי אֲבֹתֵינוּ",     "Yahweh the God of our fathers",          "divine-name"),
    ("יְהוָה אֱלֹהֵי דָוִד",          "Yahweh the God of David",                "divine-name"),
    ("אֲדֹנָי יְהוִה",                "the Lord Yahweh",                         "divine-name"),
    ("אֲדֹנָי יְהוָה",                "the Lord Yahweh",                         "divine-name"),
    ("יְהוָה אֲדֹנָי",                "Yahweh the Lord",                         "divine-name"),
    ("אֵל שַׁדַּי",                    "El Shaddai",                              "divine-name"),
    ("אֵל עֶלְיוֹן",                  "God Most High",                           "divine-name"),
    ("אֵל עוֹלָם",                    "the Everlasting God",                      "divine-name"),
    ("אֵל רֳאִי",                      "the God who sees",                        "divine-name"),
    ("אֵל קַנָּא",                     "a jealous God",                           "divine-name"),
    ("אֵל אֱמֶת",                      "the God of truth",                        "divine-name"),
    ("אֱלֹהֵי אַבְרָהָם",             "the God of Abraham",                      "divine-name"),
    ("אֱלֹהֵי יִצְחָק",               "the God of Isaac",                        "divine-name"),
    ("אֱלֹהֵי יַעֲקֹב",               "the God of Jacob",                        "divine-name"),
    ("אֱלֹהֵי אַבְרָהָם יִצְחָק וְיַעֲקֹב", "the God of Abraham, Isaac, and Jacob", "divine-name"),
    ("אֱלֹהֵי יִשְׂרָאֵל",            "the God of Israel",                       "divine-name"),
    ("אֱלֹהֵי הַשָּׁמַיִם",           "the God of heaven",                       "divine-name"),
    ("מֶלֶךְ הַכָּבוֹד",              "the King of glory",                       "divine-name"),
    ("יְהוָה שָׁלוֹם",                "Yahweh is Peace",                         "divine-name"),
    ("יְהוָה יִרְאֶה",                "Yahweh will provide",                     "divine-name"),
    ("יְהוָה נִסִּי",                  "Yahweh is my Banner",                    "divine-name"),
    ("יְהוָה רֹעִי",                   "Yahweh is my Shepherd",                  "divine-name"),
    ("יְהוָה שַׁמָּה",                "Yahweh is there",                         "divine-name"),
    ("יְהוָה צִדְקֵנוּ",              "Yahweh our Righteousness",               "divine-name"),
    ("קְדוֹשׁ יִשְׂרָאֵל",            "the Holy One of Israel",                  "divine-name"),
    ("אֲבִיר יַעֲקֹב",                "the Mighty One of Jacob",                "divine-name"),
    ("צוּר יִשְׂרָאֵל",               "the Rock of Israel",                      "divine-name"),
    # =========================================================================
    # VOCATIVE / CALL FORMULAS
    # =========================================================================
    ("שְׁמַע יִשְׂרָאֵל",             "hear, O Israel",                          "vocative"),
    ("שְׁמַע יִשְׂרָאֵל יְהוָה אֱלֹהֵינוּ", "hear, O Israel, Yahweh our God",  "vocative"),
    ("הוֹי",                           "woe",                                     "vocative"),
    ("הוֹי גּוֹי",                    "woe, O nation",                           "vocative"),
    ("אֲהָהּ אֲדֹנָי יְהוִה",         "alas, Lord Yahweh",                      "vocative"),
    ("אֲהָהּ יְהוָה",                  "alas, Yahweh",                            "vocative"),
    ("עַמִּי",                         "my people",                               "vocative"),
    ("קְרָא",                          "call out / proclaim",                     "vocative"),
    ("שִׁמְעוּ",                       "hear",                                    "vocative"),
    ("הַאֲזִינוּ",                     "give ear",                                "vocative"),
    ("הַאֲזִינִי",                     "give ear",                                "vocative"),
    # =========================================================================
    # BLESSING / PRAISE FORMULAS
    # =========================================================================
    ("הַלְלוּ יָהּ",                   "praise Yahweh",                           "liturgical"),
    # NOTE: In Macula, הַלְלוּיָהּ appears as TWO tokens: הַלְלוּ + יָהּ
    # The two-word form above (הַלְלוּ יָהּ) is the corpus form that matches.
    ("בָּרוּךְ יְהוָה",               "blessed be Yahweh",                       "liturgical"),
    ("בָּרוּךְ יְהוָה אֱלֹהֵי יִשְׂרָאֵל", "blessed be Yahweh the God of Israel", "liturgical"),
    ("בָּרוּךְ יְהוָה אֱלֹהֵינוּ",    "blessed be Yahweh our God",              "liturgical"),
    ("בָּרוּךְ יְהוָה אֱלֹהֵי אֲבֹתֵינוּ", "blessed be Yahweh the God of our fathers", "liturgical"),
    ("בָּרוּךְ אֲדֹנָי",              "blessed be the Lord",                     "liturgical"),
    ("בָּרוּךְ הָאִישׁ",              "blessed is the man",                      "liturgical"),
    ("אַשְׁרֵי הָאִישׁ",              "blessed is the man",                      "liturgical"),
    ("אַשְׁרֵי",                       "blessed/happy are",                       "liturgical"),
    ("אַשְׁרֵי הָעָם",                "blessed is the people",                   "liturgical"),
    ("אַשְׁרֵי הַגֶּבֶר",             "blessed is the man",                      "liturgical"),
    ("אַשְׁרֵי כָּל",                  "blessed is everyone who",                 "liturgical"),
    ("הוֹדוּ לַיהוָה",                "give thanks to Yahweh",                   "liturgical"),
    ("הוֹדוּ לַיהוָה כִּי טוֹב",     "give thanks to Yahweh, for he is good",  "liturgical"),
    ("כִּי לְעוֹלָם חַסְדּוֹ",        "for his steadfast love endures forever", "liturgical"),
    ("שִׁירוּ לַיהוָה",               "sing to Yahweh",                          "liturgical"),
    ("שִׁירוּ לַיהוָה שִׁיר חָדָשׁ",  "sing to Yahweh a new song",              "liturgical"),
    ("רוֹמְמוּ יְהוָה",               "exalt Yahweh",                            "liturgical"),
    ("הַגִּידוּ בַגּוֹיִם",           "declare among the nations",               "liturgical"),
    ("כִּי טוֹב",                      "for he is good",                          "liturgical"),
    ("אָמֵן",                          "amen",                                    "liturgical"),
    ("אָמֵן וְאָמֵן",                  "amen and amen",                          "liturgical"),
    ("סֶלָה",                          "selah",                                   "liturgical"),
    ("שִׁיר הַמַּעֲלוֹת",             "a song of ascents",                       "liturgical"),
    ("לַמְנַצֵּחַ",                    "to the choirmaster",                      "liturgical"),
    ("מִזְמוֹר לְדָוִד",              "a psalm of David",                        "liturgical"),
    ("מַשְׂכִּיל",                     "a maskil",                                "liturgical"),
    # =========================================================================
    # OATH FORMULAS
    # =========================================================================
    ("חַי יְהוָה",                     "as Yahweh lives",                         "oath"),
    ("חַי יְהוָה צְבָאוֹת",           "as Yahweh of hosts lives",               "oath"),
    ("חַי אֲדֹנָי יְהוִה",            "as the Lord Yahweh lives",               "oath"),
    ("חַי נַפְשְׁךָ",                  "as your soul lives",                      "oath"),
    ("חַי נַפְשִׁי",                   "as my soul lives",                        "oath"),
    ("חַי פַּרְעֹה",                   "as Pharaoh lives",                        "oath"),
    ("נִשְׁבַּע יְהוָה",               "Yahweh has sworn",                        "oath"),
    ("נִשְׁבַּעְתִּי בִי",             "I have sworn by myself",                  "oath"),
    # =========================================================================
    # DISCOURSE MARKERS
    # =========================================================================
    ("הִנֵּה",                         "behold",                                  "discourse"),
    ("הִנֵּה נָא",                     "behold now",                              "discourse"),
    ("הִנֵּה אָנֹכִי",                "behold, I",                               "discourse"),
    ("הִנֵּה יְהוָה",                  "behold, Yahweh",                          "discourse"),
    ("וְהִנֵּה",                       "and behold",                              "discourse"),
    ("אַל תִּירָא",                    "do not fear",                             "discourse"),
    ("אַל תִּירְאִי",                  "do not fear",                             "discourse"),
    ("אַל תִּירְאוּ",                  "do not fear",                             "discourse"),
    ("אַל נָא",                        "please do not",                           "discourse"),
    ("אָנָּא",                         "please / we beg",                         "discourse"),
    ("אָנָּא יְהוָה",                  "we beg you, O Yahweh",                   "discourse"),
    ("שׁוּבוּ",                        "return",                                  "discourse"),
    ("שׁוּב",                          "return",                                  "discourse"),
    ("קוּמוּ",                         "arise",                                   "discourse"),
    ("לֵאמֹר",                         "saying",                                  "discourse"),
    ("כָּל הָאָרֶץ",                   "all the earth",                           "discourse"),
    ("מַה",                            "what",                                    "discourse"),
    ("לָמָּה",                         "why",                                     "discourse"),
    ("מִי",                            "who",                                     "discourse"),
    ("אֵי",                            "where",                                   "discourse"),
    ("עַל כֵּן",                       "therefore",                               "discourse"),
    ("לָכֵן",                          "therefore",                               "discourse"),
    ("לָכֵן כֹּה אָמַר יְהוָה",       "therefore thus says Yahweh",             "discourse"),
    # =========================================================================
    # TEMPORAL FORMULAS
    # =========================================================================
    ("בַּיּוֹם הַהוּא",               "on that day",                             "temporal"),
    ("בָּעֵת הַהִיא",                  "at that time",                            "temporal"),
    ("בְּאַחֲרִית הַיָּמִים",         "in the latter days",                      "temporal"),
    ("מֵעוֹלָם וְעַד עוֹלָם",         "from everlasting to everlasting",         "temporal"),
    ("לְעוֹלָם וָעֶד",                "forever and ever",                        "temporal"),
    ("לְעוֹלָם",                       "forever",                                 "temporal"),
    ("מִדּוֹר לְדוֹר",               "from generation to generation",            "temporal"),
    ("מִדֹּר וָדֹר",                  "from generation to generation",            "temporal"),
    ("יוֹם יוֹם",                      "day by day",                              "temporal"),
    ("בַּיּוֹם הַשְּׁלִישִׁי",        "on the third day",                        "temporal"),
    ("עַד עוֹלָם",                     "forever",                                 "temporal"),
    ("בְּרֵאשִׁית",                    "in the beginning",                        "temporal"),
    ("בְּאַחֲרִית הַיָּמִים",         "in the latter days",                      "temporal"),
    ("בַּיּוֹם הַשְּׁמִינִי",         "on the eighth day",                       "temporal"),
    ("בַּיּוֹם הָרִאשׁוֹן",           "on the first day",                        "temporal"),
    ("בַּחֹדֶשׁ הָרִאשׁוֹן",          "in the first month",                      "temporal"),
    # =========================================================================
    # NARRATIVE OPENERS
    # =========================================================================
    ("וַיְהִי",                        "and it came to pass",                     "narrative-opener"),
    ("וַיְהִי כִּי",                   "and when",                                "narrative-opener"),
    ("וַיְהִי כַּאֲשֶׁר",             "and when",                                "narrative-opener"),
    ("וְהָיָה",                        "and it shall be",                         "narrative-opener"),
    ("וְהָיָה אִם",                    "and it shall be, if",                     "narrative-opener"),
    ("וַיִּקְרָא",                     "and he called",                           "narrative-opener"),
    ("וַיְדַבֵּר יְהוָה אֶל",         "and Yahweh spoke to",                    "narrative-opener"),
    ("וַיֹּאמֶר יְהוָה אֶל",          "and Yahweh said to",                     "narrative-opener"),
    ("וַיֹּאמֶר אֱלֹהִים",            "and God said",                            "narrative-opener"),
    ("וַיַּרְא אֱלֹהִים",             "and God saw",                             "narrative-opener"),
    ("וַיַּעַשׂ אֱלֹהִים",            "and God made",                            "narrative-opener"),
    ("וַיִּקְרָא אֱלֹהִים",           "and God called",                          "narrative-opener"),
    ("וַיְבָרֶךְ אֱלֹהִים",           "and God blessed",                         "narrative-opener"),
    ("וַיִּפֶן",                       "and he turned",                           "narrative-opener"),
    ("וַיְדַבֵּר אֱלֹהִים",           "and God spoke",                           "narrative-opener"),
    ("וַיַּרְא יְהוָה",               "and Yahweh saw",                          "narrative-opener"),
    ("וַיֹּאמֶר יְהוָה",              "and Yahweh said",                         "narrative-opener"),
    # =========================================================================
    # GENEALOGICAL FORMULAS (Rule H17)
    # =========================================================================
    ("וַיְחִי",                        "and he lived",                            "genealogical"),
    ("וַיּוֹלֶד בָּנִים וּבָנוֹת",    "and he fathered sons and daughters",     "genealogical"),
    ("וַיּוֹלֶד",                      "and he fathered",                         "genealogical"),
    ("תּוֹלְדֹת",                      "the generations of",                      "genealogical"),
    ("אֵלֶּה תּוֹלְדֹת",              "these are the generations of",            "genealogical"),
    ("זֶה סֵפֶר תּוֹלְדֹת",           "this is the book of the generations of", "genealogical"),
    ("בֶּן שָׁנָה",                    "years old",                               "genealogical"),
    ("כָּל יְמֵי",                     "all the days of",                         "genealogical"),
    ("וַיִּהְיוּ יְמֵי",              "and the days of",                         "genealogical"),
    ("וַיָּמָת",                       "and he died",                             "genealogical"),
    ("וַיָּמָת וַיִּקָּבֵר",          "and he died and was buried",              "genealogical"),
    ("וַיִּקָּבֵר",                    "and he was buried",                       "genealogical"),
    ("אֵלֶּה בְנֵי",                   "these are the sons of",                   "genealogical"),
    ("וְאֵלֶּה שְׁמוֹת",              "and these are the names of",              "genealogical"),
    ("אֵלֶּה שְׁמוֹת",               "these are the names of",                  "genealogical"),
    # =========================================================================
    # COGNATE-ACCUSATIVE IDIOMS
    # =========================================================================
    ("זָבַח זֶבַח",                    "to offer a sacrifice",                    "cognate-acc"),
    ("נָדַר נֵדֶר",                    "to make a vow",                           "cognate-acc"),
    ("חָלַם חֲלוֹם",                   "to dream a dream",                        "cognate-acc"),
    ("יָרֵא יִרְאָה",                  "to be very afraid",                       "cognate-acc"),
    ("יִרְאָה גְדוֹלָה",               "great fear",                              "cognate-acc"),
    ("שָׁמַע שֵׁמַע",                  "to hear / pay close attention",           "cognate-acc"),
    ("קָרָא קְרִיאָה",                 "to proclaim a proclamation",              "cognate-acc"),
    ("חָרָה אַף",                      "anger burned",                            "cognate-acc"),
    ("חָלָה חֳלִי",                    "to be very sick",                         "cognate-acc"),
    ("שָׁבָה שְׁבִי",                  "to take captive",                         "cognate-acc"),
    ("גָּלָה גָלוּת",                  "to go into exile",                        "cognate-acc"),
    ("חָטָא חַטָּאת",                  "to commit sin",                           "cognate-acc"),
    ("שָׁבַע שְׁבוּעָה",               "to swear an oath",                        "cognate-acc"),
    ("רָצַח רֶצַח",                    "to commit murder",                        "cognate-acc"),
    ("גָּנַב גְּנֵבָה",               "to commit theft",                         "cognate-acc"),
    # =========================================================================
    # PRAYER / PETITION FORMULAS
    # =========================================================================
    ("שְׁמַע תְּפִלָּתִי",             "hear my prayer",                          "prayer"),
    ("שְׁמַע קוֹלִי",                  "hear my voice",                           "prayer"),
    ("שְׁמַע יְהוָה",                  "hear, O Yahweh",                          "prayer"),
    ("שְׁמַע אֱלֹהִים",               "hear, O God",                             "prayer"),
    ("חָנֵּנִי יְהוָה",               "have mercy on me, O Yahweh",             "prayer"),
    ("עֲנֵנִי יְהוָה",                "answer me, O Yahweh",                     "prayer"),
    ("הֵקֵץ",                         "awake",                                    "prayer"),
    ("אֶל יְהוָה קָרָאתִי",           "to Yahweh I cried",                       "prayer"),
    ("מִמַּעֲמַקִּים קְרָאתִיךָ",     "out of the depths I cried to you",       "prayer"),
    ("הַצִּילֵנִי",                    "deliver me",                              "prayer"),
    ("הוֹשִׁיעֵנִי",                   "save me",                                 "prayer"),
    ("רְפָאֵנִי יְהוָה",              "heal me, O Yahweh",                       "prayer"),
    # =========================================================================
    # BLESSING / CURSE PATTERNS
    # =========================================================================
    ("בָּרוּךְ אֲשֶׁר",               "blessed is the one who",                  "blessing-curse"),
    ("אָרוּר",                         "cursed",                                  "blessing-curse"),
    ("אָרוּר הָאִישׁ",                "cursed is the man",                       "blessing-curse"),
    ("בָּרוּךְ",                       "blessed",                                 "blessing-curse"),
    ("וַאֲבָרֲכָה מְבָרְכֶיךָ",       "I will bless those who bless you",       "blessing-curse"),
    ("אָאֹר מְקַלְלֶךָ",              "I will curse the one who curses you",    "blessing-curse"),
    # =========================================================================
    # COVENANT FORMULAS
    # =========================================================================
    ("כָּרַת בְּרִית",                 "to cut a covenant",                       "covenant"),
    ("כָּרְתוּ בְּרִית",              "they cut a covenant",                     "covenant"),
    ("וַהֲקִמֹתִי אֶת בְּרִיתִי",    "and I will establish my covenant",       "covenant"),
    ("הֵקִים אֶת הַבְּרִית",         "to establish the covenant",               "covenant"),
    ("בְּרִית עוֹלָם",               "an everlasting covenant",                 "covenant"),
    ("עַם סְגֻלָּה",                   "a treasured people",                      "covenant"),
    ("מַמְלֶכֶת כֹּהֲנִים",           "a kingdom of priests",                    "covenant"),
    ("גּוֹי קָדוֹשׁ",                  "a holy nation",                           "covenant"),
    ("אֲנִי יְהוָה אֱלֹהֵיכֶם",       "I am Yahweh your God",                   "covenant"),
    ("אֲנִי יְהוָה",                   "I am Yahweh",                             "covenant"),
    ("אֲנִי אֱלֹהֵיכֶם",              "I am your God",                           "covenant"),
    ("אַתֶּם עַמִּי",                  "you are my people",                       "covenant"),
    ("וְהָיִיתִי לָהֶם לֵאלֹהִים",    "and I will be their God",                "covenant"),
    ("וְהֵמָּה יִהְיוּ לִי לְעָם",    "and they shall be my people",            "covenant"),
    ("בְּרִית אַבְרָהָם",              "the covenant with Abraham",               "covenant"),
    # =========================================================================
    # COMMISSION FORMULAS
    # =========================================================================
    ("קוּם לֵךְ",                      "arise, go",                               "commission"),
    ("קוּם",                           "arise",                                   "commission"),
    ("לֵךְ",                           "go",                                      "commission"),
    ("שְׁלָחַנִי",                     "has sent me",                             "commission"),
    ("שְׁלָחֲךָ",                      "has sent you",                            "commission"),
    ("וַיִּשְׁלַח יְהוָה",             "and Yahweh sent",                         "commission"),
    ("הָלוֹךְ",                        "going / go",                              "commission"),
    ("לֵךְ אֶל",                       "go to",                                   "commission"),
    # =========================================================================
    # LAMENT / DISTRESS FORMULAS
    # =========================================================================
    ("עַד מָתַי",                      "how long",                                "lament"),
    ("עַד מָתַי יְהוָה",              "how long, O Yahweh",                      "lament"),
    # NOTE: Psalms use עַד אָנָה more commonly than עַד מָתַי for "how long"
    ("עַד אָנָה יְהוָה",              "how long, O Yahweh",                      "lament"),
    ("עַד אָנָה",                      "how long",                                "lament"),
    ("לָמָּה יְהוָה",                  "why, O Yahweh",                           "lament"),
    ("אֵיכָה",                         "how / alas",                              "lament"),
    ("אַף כִּי",                       "how much more",                           "lament"),
    ("אֵי אֱלֹהָיו",                  "where is his God",                        "lament"),
    # =========================================================================
    # SANCTUARY / WORSHIP FORMULAS
    # =========================================================================
    ("בֵּית יְהוָה",                   "the house of Yahweh",                     "sanctuary"),
    ("בֵּית אֱלֹהִים",                "the house of God",                        "sanctuary"),
    ("מִקְדַּשׁ יְהוָה",              "the sanctuary of Yahweh",                 "sanctuary"),
    ("אֹהֶל מוֹעֵד",                  "the tent of meeting",                     "sanctuary"),
    ("אֲרוֹן הַבְּרִית",              "the ark of the covenant",                 "sanctuary"),
    ("אֲרוֹן יְהוָה",                 "the ark of Yahweh",                       "sanctuary"),
    ("אֲרוֹן הָאֱלֹהִים",             "the ark of God",                          "sanctuary"),
    ("הַר יְהוָה",                    "the mountain of Yahweh",                  "sanctuary"),
    ("הַר הַקֹּדֶשׁ",                 "the holy mountain",                       "sanctuary"),
    ("הֵיכַל יְהוָה",                 "the temple of Yahweh",                    "sanctuary"),
    ("צִיּוֹן",                        "Zion",                                    "sanctuary"),
    ("הַר צִיּוֹן",                   "Mount Zion",                              "sanctuary"),
    ("עִיר דָּוִד",                    "the city of David",                       "sanctuary"),
    ("שַׁעֲרֵי צִיּוֹן",              "the gates of Zion",                       "sanctuary"),
    # =========================================================================
    # PRIESTLY / CULTIC FORMULAS
    # =========================================================================
    ("קָדוֹשׁ קָדוֹשׁ קָדוֹשׁ",       "holy, holy, holy",                        "cultic"),
    ("כְּבוֹד יְהוָה",                "the glory of Yahweh",                     "cultic"),
    ("כָּבוֹד יְהוָה",                "the glory of Yahweh",                     "cultic"),
    ("עֹלוֹת וּשְׁלָמִים",            "burnt offerings and peace offerings",     "cultic"),
    ("עֹלָה וּשְׁלָמִים",             "a burnt offering and peace offerings",    "cultic"),
    ("לִפְנֵי יְהוָה",                "before Yahweh",                           "cultic"),
    ("לִפְנֵי אֱלֹהִים",              "before God",                              "cultic"),
    ("קֹדֶשׁ קָדָשִׁים",              "most holy",                               "cultic"),
    ("קֹדֶשׁ לַיהוָה",               "holy to Yahweh",                          "cultic"),
    ("עֹלַת תָּמִיד",                 "the regular burnt offering",              "cultic"),
    ("מִנְחַת תָּמִיד",               "the regular grain offering",              "cultic"),
    ("אִשֶּׁה לַיהוָה",              "a food offering to Yahweh",               "cultic"),
    # =========================================================================
    # WISDOM / BEATITUDE FORMULAS
    # =========================================================================
    ("יִרְאַת יְהוָה",               "the fear of Yahweh",                      "wisdom"),
    ("יִרְאַת יְהוָה רֵאשִׁית חָכְמָה", "the fear of Yahweh is the beginning of wisdom", "wisdom"),
    ("חָכְמָה וּבִינָה",              "wisdom and understanding",                "wisdom"),
    ("אֵין חָדָשׁ תַּחַת הַשֶּׁמֶשׁ", "there is nothing new under the sun",    "wisdom"),
    ("הֶבֶל הֲבָלִים",               "vanity of vanities",                       "wisdom"),
    ("הֶבֶל הֲבָלִים הַכֹּל הֶבֶל",  "vanity of vanities, all is vanity",      "wisdom"),
    ("מֵשַׁל",                         "a proverb",                               "wisdom"),
    ("לְהָבִין מָשָׁל",               "to understand a proverb",                "wisdom"),
    # =========================================================================
    # CREATION FORMULAS
    # =========================================================================
    ("וַיַּרְא אֱלֹהִים כִּי טוֹב",   "and God saw that it was good",           "creation"),
    ("כִּי טוֹב מְאֹד",               "that it was very good",                   "creation"),
    ("וַיְהִי עֶרֶב וַיְהִי בֹקֶר",  "and there was evening and there was morning", "creation"),
    ("בְּצֶלֶם אֱלֹהִים",             "in the image of God",                     "creation"),
    ("זָכָר וּנְקֵבָה",               "male and female",                         "creation"),
    ("פְּרוּ וּרְבוּ",                "be fruitful and multiply",               "creation"),
    ("מִלְאוּ אֶת הָאָרֶץ",          "fill the earth",                          "creation"),
    ("בָּרָא אֱלֹהִים",               "God created",                             "creation"),
    # =========================================================================
    # RESTORATION / ESCHATOLOGICAL FORMULAS
    # =========================================================================
    ("יוֹם יְהוָה",                   "the day of Yahweh",                       "eschatological"),
    # NOTE: EZK uses "גוג ארץ המגוג" not "גוג ומגוג"; the conjoined form is in REV (NT)
    ("גּוֹג אֶרֶץ הַמָּגוֹג",        "Gog of the land of Magog",               "eschatological"),
    ("וְשַׁבְתִּי אֶת שְׁבוּת",      "I will restore the fortunes of",         "eschatological"),
    ("וְנָהֲרוּ אֵלָיו כָּל הַגּוֹיִם", "and all the nations shall stream to it", "eschatological"),
    # =========================================================================
    # CONDITIONAL / LEGAL FORMULAS
    # =========================================================================
    ("אִם שָׁמוֹעַ תִּשְׁמַע",        "if you will diligently obey",            "legal"),
    ("שָׁמֹר תִּשְׁמְרוּן",          "you shall diligently keep",               "legal"),
    ("מוֹעֲדֵי יְהוָה",              "the appointed feasts of Yahweh",          "legal"),
    ("זֹאת הַתּוֹרָה",               "this is the law",                         "legal"),
    ("הַחֻקִּים וְהַמִּשְׁפָּטִים",   "the statutes and the ordinances",        "legal"),
    ("לְדֹרֹתָם",                     "throughout their generations",            "legal"),
    ("לְדֹרֹתֵיכֶם",                  "throughout your generations",             "legal"),
    ("חֻקַּת עוֹלָם",                 "a permanent statute",                     "legal"),
    ("כִּי אֲנִי יְהוָה",             "for I am Yahweh",                         "legal"),
    ("כִּי אֲנִי יְהוָה אֱלֹהֵיכֶם", "for I am Yahweh your God",              "legal"),
    # =========================================================================
    # ANTHROPOMORPHISM / DIVINE ATTRIBUTES
    # =========================================================================
    ("יַד יְהוָה",                    "the hand of Yahweh",                      "anthropomorphism"),
    ("פְּנֵי יְהוָה",                 "the face of Yahweh",                      "anthropomorphism"),
    ("עֵינֵי יְהוָה",                 "the eyes of Yahweh",                      "anthropomorphism"),
    ("רוּחַ יְהוָה",                  "the Spirit of Yahweh",                    "anthropomorphism"),
    ("רוּחַ אֱלֹהִים",               "the Spirit of God",                       "anthropomorphism"),
    # NOTE: רוח הקדש is rare in Hebrew Bible in this exact form (mainly NT);
    # the OT uses רוח יהוה / רוח אלהים / רוח קדשו (Isa 63:10-11)
    ("רוּחַ קָדְשׁוֹ",               "his holy Spirit",                         "anthropomorphism"),
    ("מַלְאַךְ יְהוָה",               "the angel of Yahweh",                     "anthropomorphism"),
    ("מַלְאַךְ אֱלֹהִים",             "the angel of God",                        "anthropomorphism"),
    ("חֶסֶד וֶאֱמֶת",                "steadfast love and faithfulness",         "anthropomorphism"),
    ("חֶסֶד יְהוָה",                  "the steadfast love of Yahweh",            "anthropomorphism"),
    ("חֶסֶד אֱלֹהִים",               "the steadfast love of God",               "anthropomorphism"),
    ("אֶרֶךְ אַפַּיִם",               "slow to anger",                           "anthropomorphism"),
    ("רַב חֶסֶד",                     "abounding in steadfast love",             "anthropomorphism"),
    ("אֶרֶךְ אַפַּיִם וְרַב חֶסֶד",  "slow to anger and abounding in steadfast love", "anthropomorphism"),
    ("כָּבֵד אָזְנָיִם",              "heavy of ear",                            "anthropomorphism"),
    ("קְשֵׁה עֹרֶף",                  "stiff-necked",                            "anthropomorphism"),
    # =========================================================================
    # MERISM / POLAR PAIR FORMULAS
    # =========================================================================
    ("שָׁמַיִם וָאָרֶץ",             "heaven and earth",                        "merism"),
    ("הַשָּׁמַיִם וְהָאָרֶץ",        "the heavens and the earth",               "merism"),
    ("יוֹמָם וָלַיְלָה",             "day and night",                           "merism"),
    ("קָטֹן וְגָדוֹל",               "small and great",                         "merism"),
    ("אִישׁ וְאִשָּׁה",              "man and woman",                           "merism"),
    ("בֵּית אָבִיו",                  "his father's house",                      "merism"),
    ("כֹּל בָּשָׂר",                  "all flesh",                               "merism"),
    ("כֹּל הָאָרֶץ",                  "all the earth",                           "merism"),
    ("כֹּל הַגּוֹיִם",               "all the nations",                         "merism"),
    ("מִזְרָח וָמַעֲרָב",            "east and west",                           "merism"),
    ("צָפוֹן וָנֶגֶב",               "north and south",                         "merism"),
    ("מֵרֹאשׁ",                       "from the beginning",                      "merism"),
    ("אִישׁ וָאִשָּׁה",              "man and woman",                           "merism"),
    ("גָּדוֹל וָקָטֹן",              "great and small",                         "merism"),
    # =========================================================================
    # JONAH-SPECIFIC (preserve existing Jonah-tuned entries)
    # =========================================================================
    ("וַיְהִי דְּבַר יְהוָה אֶל יוֹנָה", "and the word of Yahweh came to Jonah", "narrative-opener"),
    ("בֶּן אֲמִתַּי",                 "son of Amittai",                          "genealogical"),
    ("וַיִּזְבְּחוּ זֶבַח",           "and they offered a sacrifice",            "cognate-acc"),
    ("וַיִּדְּרוּ נְדָרִים",          "and they made vows",                      "cognate-acc"),
    # actual Jonah corpus form has "האנשים" intervening: ויראו האנשים יראה גדולה
    ("יִרְאָה גְדוֹלָה",              "great fear / greatly afraid",            "cognate-acc"),
    ("וַיִּפְּלוּ גוֹרָלוֹת",         "and they cast lots",                      "narrative-opener"),
]


# ---------------------------------------------------------------------------
# Mining engine
# ---------------------------------------------------------------------------

def count_phrase_occurrences(phrase_surface: str, verse_texts: dict) -> tuple[int, list[str]]:
    """Count how many verses contain a given phrase (by consonantal match)."""
    needle = normalize_for_match(phrase_surface)
    if not needle:
        return 0, []
    hits = []
    for ref, full_text in verse_texts.items():
        if needle in full_text:
            hits.append(ref)
    return len(hits), hits


def mine_all_phrases(seed_phrases: list, verse_texts: dict) -> list[dict]:
    """Count occurrences of all seed phrases and return enriched list."""
    results = []
    total = len(seed_phrases)
    print(f"Mining {total} seed phrases...", flush=True)
    for i, entry in enumerate(seed_phrases):
        hebrew, english, category = entry
        count, refs = count_phrase_occurrences(hebrew, verse_texts)
        results.append({
            "hebrew":      hebrew,
            "english":     english,
            "category":   category,
            "occurrences": count,
            "_sample_refs": refs[:5],
        })
        if (i+1) % 50 == 0:
            print(f"  Processed {i+1}/{total} phrases...", flush=True)
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("Macula Hebrew Phrase-Map Miner")
    print("=" * 70)

    verse_texts, total_verses, total_morphemes = load_verse_texts(MACULA_TSV)
    print(f"Total verses in corpus: {total_verses:,}\n")

    results = mine_all_phrases(SEED_PHRASES, verse_texts)

    # Deduplicate: if two Hebrew phrases normalize to the same consonants, keep
    # the one with more occurrences (longer or more specific form).
    seen_normalized: dict[str, dict] = {}
    deduped = []
    for r in sorted(results, key=lambda x: (-x["occurrences"], -len(x["hebrew"]))):
        nk = normalize_for_match(r["hebrew"])
        if nk not in seen_normalized:
            seen_normalized[nk] = r
            deduped.append(r)
        # else: skip duplicate — the higher-count variant already in

    # Sort by occurrences descending
    deduped.sort(key=lambda r: r["occurrences"], reverse=True)

    zero_count = sum(1 for r in deduped if r["occurrences"] == 0)
    print(f"\n{zero_count} phrases had 0 occurrences after word-reconstructed matching.")

    # -----------------------------------------------------------------------
    # Full-corpus coverage estimation
    # -----------------------------------------------------------------------
    print("Running full coverage pass...", flush=True)
    all_matched: set[str] = set()
    for r in deduped:
        if r["occurrences"] == 0:
            continue
        needle = normalize_for_match(r["hebrew"])
        for ref, full_text in verse_texts.items():
            if needle in full_text:
                all_matched.add(ref)
    coverage_pct = 100.0 * len(all_matched) / total_verses if total_verses else 0
    print(f"Verses with ≥1 phrase-map match: {len(all_matched):,} / {total_verses:,} ({coverage_pct:.1f}%)")

    # -----------------------------------------------------------------------
    # Write JSON output — all entries (include zero-count for completeness;
    # the gloss generator can filter by occurrences if desired)
    # -----------------------------------------------------------------------
    output: dict = {}
    for r in deduped:
        output[r["hebrew"]] = {
            "english":     r["english"],
            "occurrences": r["occurrences"],
            "category":    r["category"],
        }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(output, fh, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(output)} entries to {OUT_FILE}")

    # -----------------------------------------------------------------------
    # Top-20 summary
    # -----------------------------------------------------------------------
    print("\nTop 20 patterns by occurrence count:")
    print(f"  {'Hebrew':<50} {'Count':>6}  Category")
    print("  " + "-" * 76)
    for r in deduped[:20]:
        heb = r["hebrew"]
        if len(heb) > 46:
            heb = heb[:43] + "..."
        print(f"  {heb:<50} {r['occurrences']:>6}  {r['category']}")

    print(f"\nSummary:")
    print(f"  Total entries:               {len(deduped)}")
    print(f"  High-value (≥10 occ):        {sum(1 for r in deduped if r['occurrences'] >= 10)}")
    print(f"  Medium (1–9 occ):            {sum(1 for r in deduped if 1 <= r['occurrences'] < 10)}")
    print(f"  Zero occurrences:            {zero_count}")
    print(f"  Corpus coverage:             {coverage_pct:.1f}% of verses")


if __name__ == "__main__":
    main()
