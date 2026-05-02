"""Hebrew morpho-syntactic helpers — shared by spec-driven validators.

Architectural constraint: NO te'amim Unicode codepoints (U+0591-U+05AF) in any
predicate function. Te'amim may appear only in annotation/output strings.

All trigger logic operates on consonant skeletons (after stripping niqqud +
te'amim) plus niqqud-vowel patterns where binyan / morphology disambiguation
requires it.
"""

import re
from typing import Optional

# ─── unicode helpers ────────────────────────────────────────────────

# strip niqqud + te'amim (U+0591–U+05BD), preserve maqqef (U+05BE), paseq (U+05C0), sof-pasuq (U+05C3)
NIQQUD_TEAMIM_RE = re.compile(r"[֑-ֽֿׁׂׄ-ׇ]")

# Strip ONLY te'amim (cantillation marks U+0591–U+05AF), preserving niqqud (U+05B0+).
# Use when a niqqud-aware morphology regex needs te'amim removed but vowels intact.
TEAMIM_ONLY_RE = re.compile(r"[֑-֯]")
MAQQEF = "־"
PASEQ = "׀"
SOF_PASUQ = "׃"
VERSE_REF_RE = re.compile(r"^\d+:\d+$")


def skel(s: str) -> str:
    """Strip all niqqud + te'amim + apparatus glyphs to bare consonant skeleton."""
    out = NIQQUD_TEAMIM_RE.sub("", s)
    out = out.replace(MAQQEF, "").replace(PASEQ, "").replace(SOF_PASUQ, "")
    return out


def strip_apparatus(s: str) -> str:
    """Strip niqqud + te'amim but PRESERVE maqqef/paseq/sof-pasuq for morphology checks."""
    return NIQQUD_TEAMIM_RE.sub("", s)


def strip_teamim(s: str) -> str:
    """Strip ONLY te'amim, preserving niqqud — for niqqud-aware regex matching."""
    return TEAMIM_ONLY_RE.sub("", s)


# ─── line / token primitives ────────────────────────────────────────

def tokens(line: str) -> list[str]:
    """Whitespace-split tokens on a line."""
    return [t for t in line.split() if t.strip()]


def first_content_token(line: str) -> Optional[str]:
    """First whitespace-separated token on the line."""
    toks = tokens(line)
    return toks[0] if toks else None


def last_content_token(line: str) -> Optional[str]:
    """Last whitespace-separated token on the line."""
    toks = tokens(line)
    return toks[-1] if toks else None


def prosodic_word_count(line: str) -> int:
    """Count prosodic words: whitespace tokens, with maqqef-grouped tokens counted as one."""
    toks = tokens(line)
    # Each whitespace-separated token is already a single prosodic word
    # (maqqef joining is intra-token; tokens on either side of maqqef are
    # already a single prosodic unit).
    return len(toks)


def partition_into_verses(text: str) -> list[tuple[tuple[int, int], list[str]]]:
    """Split chapter text into ((chapter, verse), [content_lines]) blocks.

    Recognizes verse-marker lines like `1:1`, `1:2`. Skips blank lines.
    """
    blocks: list[tuple[tuple[int, int], list[str]]] = []
    cur_ref: Optional[tuple[int, int]] = None
    cur_lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if VERSE_REF_RE.match(line):
            if cur_ref is not None:
                blocks.append((cur_ref, cur_lines))
            ch_s, vs_s = line.split(":")
            cur_ref = (int(ch_s), int(vs_s))
            cur_lines = []
        else:
            cur_lines.append(line)
    if cur_ref is not None:
        blocks.append((cur_ref, cur_lines))
    return blocks


# ─── morphological detectors ────────────────────────────────────────

# Finite-verb skeletons — high-frequency wayyiqtol/qatal/yiqtol/imperative/cohortative
# patterns. Conservative: false-positive verbs cause skipping (safe for guards).
# Drawn from validate_clause_nucleus_split.py corpus tuning.

WAYYIQTOL_PREFIX_RE = re.compile(r"^וי")           # wayyiqtol: ו + י (with dagesh in some)
WAYYIQTOL_PREFIX_RE_WIDE = re.compile(r"^וַי")      # with niqqud preserved
YIQTOL_PREFIXES = ("י", "ת", "א", "נ")              # 3ms/2ms/1cs/1cp
COHORTATIVE_SUFFIX_RE = re.compile(r"ה$")          # 1cs/1cp + final-ה (weak signal)
IMPERATIVE_SHORT_PATTERNS = ("עשה", "ראה", "קום", "לך", "בא", "שמע", "דע", "שב")

# Common qatal-3ms skeletons (CaCaC pattern) — explicit list of high-frequency verbs
# This list is INTENTIONALLY broad; over-detection causes skipping (safe).
QATAL_COMMON = {
    # creation/being
    "ברא", "היה", "היתה", "עשה", "יצר", "כונן",
    # speech
    "אמר", "דבר", "ענה", "קרא", "צוה", "ספר",
    # cognition
    # NOTE: "זכר" excluded — homograph with זָכָר (noun "male"). Skeleton can't
    # disambiguate without niqqud (qamatz-qamatz noun vs. qamatz-patah qatal).
    # Per canon §1 hybrid policy, prefer FN on rare qatal "remembered" 3ms over
    # FP on common noun "male". Wayyiqtol וַיִּזְכֹּר / yiqtol יִזְכֹּר still detected.
    "ידע", "ראה", "שמע", "חשב", "הבין",
    # motion
    "הלך", "בא", "באה", "יצא", "שב", "קם", "ירד", "עלה", "פנה", "סר", "נע", "נד",
    # perception
    "פתח", "סגר", "מצא",
    # action
    "נתן", "לקח", "שלח", "השליך", "הביא", "הוציא", "כתב", "כרת", "ספר",
    # state
    "ישב", "עמד", "שכב", "נח", "מת", "חי", "ילד", "נפל",
    # emotion / inner state
    "חרה", "אהב", "שנא", "שמח", "פחד", "ירא",
    # transactional
    "מכר", "קנה", "בנה", "הרס",
    # blessing/cursing
    "ברך", "ארר", "הקדיש", "טמא",
    # genealogy / proliferation
    "פרה", "רבה", "מלא", "גדל",
    # narrative-frequent action verbs
    "הרג", "גרש", "חטא", "סלח", "חזק", "שלם", "כבד", "תם", "נשא", "ענש",
    "שאה", "שעה", "השע", "שאל",
    # Hifil qatal forms (audited Lev 1:6 'וְהִפְשִׁיט', Lev 16:7 'וְלָקַח').
    # Weqatal pattern ו+verb is detected by checking inner skel against this list
    # in the wayyiqtol/weqatal branch of is_finite_verb_skel.
    "הפשיט", "הוציא", "הוצא", "הודיע", "הניח", "הוסיף", "הקריב", "הציל",
    "הראה", "הזכיר", "הסיר", "הקריב", "הקטיר", "הקדיש", "הסתיר", "הכיר",
    "המית", "החיה", "הכה", "הודה", "הושיע", "הגיד", "השיב", "הוריד",
    "הקים", "הביא", "הוציא", "הסיע",
}


# Yiqtol-prefix-conflict nouns — skeletons that LOOK like yiqtol forms
# (start with י/ת/א/נ) but are actually nouns. Per canon §1 hybrid policy
# (2026-04-29): prefer lexical exclusion over niqqud-aware vowel inspection.
# This list is also reused in the wayyiqtol check to filter vav+noun forms
# (וְנָקֵבָה, וְאָדָם, וְתוֹרָה, etc.) that would otherwise look like
# 1cp/1cs/3fs wayyiqtol.
YIQTOL_KNOWN_NOUNS = {
    # י-initial nouns
    "יד", "ים", "יום", "ין", "יין", "יער", "יען", "ימים",
    "ירא", "ירה",  # fear/shoot (can be noun in some forms)
    # ── α-prefix nouns (lexical exclusion per canon §1 hybrid policy)
    # chataf-aleph noun stems
    "אדמה", "אדמת", "אדמתו", "אדמתי", "אדמתך", "אדמתם",
    "אמונה", "אמונת", "אמונתי",
    "אנוש", "אנושי",
    "אלהים", "אלהי", "אלהיו", "אלהיך", "אלהינו", "אלהיכם", "אלהיהם",
    "אלוה",
    "אדון", "אדונים", "אדונו", "אדוני", "אדונך",
    "אדנים", "אדנו", "אדנך",
    "אדני", "אדנינו", "אדניך", "אדניכם", "אדניהם",
    # hireq-aleph noun stems
    "אישה", "אשה", "אשת", "אשתו", "אשתי", "אשתך", "אשתם", "אשתן", "אשתכם", "אשתהם",
    "אישון", "איתן", "איתנים", "אילם", "אילים",
    # tsere-aleph noun stems
    "אמת", "אמתי", "אמתך",
    "אילת", "אילי",
    # other α-prefix nouns
    "אחד", "אחת", "אחור", "אחרי", "אחרית",
    "אחי", "אחיו", "אחיך", "אחינו", "אחיכם", "אחים",
    "אנחנו", "אנכי", "אני",
    # 2nd-person pronouns (אַתָּה / אַתֶּם / אַתֶּן etc. + suffixed forms)
    "אתה", "אתם", "אתן", "אתי", "אתנו", "אתכם", "אתכן",
    # Reflexive / suffixed-possessive forms
    "אבי", "אביו", "אביך", "אבינו", "אביכם", "אביהם", "אבותינו", "אבותיכם", "אבותיהם",
    # Common α-particles / interrogatives
    "איפה", "איככה",
    # Common ת-prefix nouns that match the yiqtol skel heuristic
    "תשוקה", "תשוקת", "תשוקתו", "תשוקתי", "תשוקתך", "תשוקתם",
    "תפוח", "תפוחים", "תועבה", "תועבת", "תועבותם",
    "תרדמה", "תכלית", "תרבית", "תרועה", "תהלוכת",
    "תכלת",  # already covered above; defensive duplicate ok
    "תכונה", "תקופה", "תקופת",
    # ── Design J lexicon expansion (2026-04-30): top-frequency
    # skel-fallback false positives surfaced via corpus scan.
    # Prep+suffix forms (in PREP_SKELETONS but not protected at wayyiqtol-filter):
    "אליו", "אליך", "אליהם", "אלהם", "אליה", "אחריו",
    "תחתיו", "אליכם", "אחריהם", "אלינו", "אחריך",
    # Common nouns:
    "אותם", "אלפים", "אנשי", "אנשים", "ארבע", "ארצה",
    "ארבעים", "אחרים", "נחשת", "ארון", "ארבעה", "תמים",
    "אלוף", "נחלה", "אותה", "אותך", "אבתם", "נשיא",
    "אבנים", "ידיו", "אביה", "אותו", "אותי", "אבותם",
    "אויב", "ארור", "איננו",
    # Particles / adverbs:
    "יחדו", "תמיד", "אולי", "יומם", "אשרי",
    # High-frequency proper nouns (freq ≥34):
    "יהונתן", "איוב", "נפתלי", "יחזקיהו",
    "ארצי", "ארצנו", "ארצו", "ארצם", "ארצך", "ארצכם", "ארצהם",
    "ארץ", "ארצות",
    "אילון", "אכזב", "אכזרי", "אסיר", "אסירי",
    "אדם", "אדמני",
    # נ-initial nouns (vav-prefix would look like 1cp wayyiqtol)
    "נקבה", "נקבות", "נער", "נערה", "נערים", "נערות",
    "נשים", "נשי", "נשיו", "נשיהם",
    "נביא", "נביאים", "נביאי",
    "נחל", "נחלי", "נחלת", "נחלתו",
    "נפש", "נפשו", "נפשי", "נפשך", "נפשם",
    "נשר", "נמר", "נחש", "נשק",
    # ת-initial nouns
    "תורה", "תפלה", "תבל", "תנין", "תפארת", "תקוה", "תרומה",
    "תורת", "תורתו", "תורתך",
    "תהלה", "תהלות", "תפלת", "תפלתי", "תפלתך",
    "תכלת", "תולדות", "תולדת", "תולדתם",
    # ── Biblical proper nouns (α/י/נ/ת-prefix that match wayyiqtol/yiqtol skel)
    # Audit-driven additions 2026-04-30 (Wave 6 — Judg 4:1 וְאֵהוּד etc.)
    # Aleph-prefix proper nouns
    "אהוד", "אברהם", "אברם", "אהרן", "אדם", "אדום", "אסא",
    "אבימלך", "אבישי", "אבנר", "אבשלום", "אחז", "אחאב", "אחזיהו", "אחיה",
    "אילון", "אלעזר", "אליהו", "אלישע", "אליעזר", "אלימלך", "אסיר",
    "אסנת", "אספסף", "אפרים", "ארם", "אשור", "אסתר",
    # The divine name (massive missing — caused has_finite_verb FP on every YHWH instance)
    "יהוה",
    # Yod-prefix proper nouns
    "יעקב", "יצחק", "יוסף", "יהודה", "ישראל", "ירדן", "ירושלם", "ירושלים",
    "יבוס", "יחזקאל", "יואב", "יואל", "יואש", "יואחז", "יוחנן", "יורם",
    "יותם", "יהושע", "יהויקים", "יהויכין", "יהויקין", "יהויעדה", "יהויריב",
    "ירמיהו", "ירמיה", "ישעיהו", "ישעיה", "ירבעם", "יבל", "יבין",
    "יפת", "יוון", "יון", "יהוא", "יהוידע", "יהורם", "יהושפט",
    # Tav-prefix proper nouns
    "תרח", "תרשיש", "תיכון", "תקוע", "תמר", "תימן", "תרגום", "תפסח",
    "תרחקה", "תרבית", "תהום", "תהומות", "תיכן", "תרגומה", "תרגומו",
    "תירס",  # son of Yepheth (Gen 10:2 audit)
    # Nun-prefix proper nouns
    "נח", "נבט", "נבל", "נדב", "נחור", "נחמיה", "נעמי", "נמרוד",
    "נתן", "נחושת", "נחל", "נחלי", "נחלת",
    # ── TAHOT-tag-driven YIQTOL FP sweep (2026-04-30, 459 additions)
    # Source: scripts/sweep_yiqtol_proper_noun_fps.py — uses v0/morph TAHOT
    # tags to enumerate every proper noun whose skel matches the YIQTOL FP
    # shape but isn't already in this set. Frequency-sorted; counts in comments.
    # Audit-driven: extermination of the morphology FP class blocking ~1931
    # corpus instances of legitimate verb+bare-NP merges (per audit D3 2026-04-30).
    "יאשיהו",   # x50 — e.g. יֹאשִׁיָּ֣הוּ
    "ישמעאל",   # x37 — e.g. יִשְׁמָעֵ֔אל
    "אוריה",   # x34 — e.g. אוּרִיָּ֥ה
    "יונתן",   # x32 — e.g. י֣וֹנָתָ֔ן
    "יששכר",   # x32 — e.g. יִשָּׂשכָֽר׃
    "נבוכדנצר",   # x29 — e.g. נְבֽוּכַדְנֶצַּר֙
    "יפתח",   # x28 — e.g. יִפְתַּח
    "אחשורוש",   # x27 — e.g. אֲחַשְׁוֵר֔וֹשׁ
    "נבוכדראצר",   # x27 — e.g. נְבוּכַדְרֶאצַּ֥ר
    "אמציהו",   # x26 — e.g. אֲמַצְיָ֥הוּ
    "יריחו",   # x23 — e.g. יְרִיח֑וֹ
    "אמנון",   # x22 — e.g. אַמְנ֔וֹן
    "אכיש",   # x21 — e.g. אָכִ֖ישׁ
    "נבות",   # x21 — e.g. נָב֣וֹת׀
    "ארנן",   # x20 — e.g. אַרְנֹֽן׃
    "ירחו",   # x20 — e.g. יְרֵחֽוֹ׃
    "אחיקם",   # x19 — e.g. אֲחִיקָ֣ם
    "איזבל",   # x19 — e.g. אִיזֶ֗בֶל
    "אליאב",   # x19 — e.g. אֱלִיאָ֖ב
    "אלקנה",   # x19 — e.g. אֶ֠לְקָנָה
    "יהואחז",   # x19 — e.g. יְהוֹאָחָ֥ז
    "ישוע",   # x19 — e.g. יֵשׁ֡וּעַ
    "אמון",   # x18 — e.g. אָמ֥וֹן
    "יערים",   # x18 — e.g. יְעָרִֽים׃
    "אביתר",   # x17 — e.g. אֶבְיָתָ֑ר
    "אחיתפל",   # x17 — e.g. אֲחִיתֹ֨פֶל
    "יהואש",   # x17 — e.g. יְהוֹאָ֥שׁ
    "יונה",   # x17 — e.g. יוֹנָ֤ה
    "יפנה",   # x16 — e.g. יְפֻנֶּֽה׃
    "יזרעאל",   # x15 — e.g. יִזְרְעֶֽאל׃
    "אלישיב",   # x14 — e.g. אֶלְיָשִׁ֑יב
    "יביש",   # x14 — e.g. יָבֵ֣ישׁ
    "ירבעל",   # x14 — e.g. יְרֻבַּ֣עַל
    "נבוזראדן",   # x14 — e.g. נְבוּזַרְאֲדָ֧ן
    "נבוכדנאצר",   # x14 — e.g. נְבוּכַדְנֶאצַּ֥ר
    "נתניה",   # x14 — e.g. נְתַנְיָ֡ה
    "אדניהו",   # x13 — e.g. אֲדֹנִיָּֽהוּ׃
    "איתמר",   # x13 — e.g. אִֽיתָמָֽר׃
    "אליפז",   # x13 — e.g. אֱלִיפָ֑ז
    "אלישמע",   # x13 — e.g. אֱלִישָׁמָ֖ע
    "אמוץ",   # x13 — e.g. אָמֽוֹץ׃
    "אבינדב",   # x12 — e.g. אֲבִינָדָ֖ב
    "אבשלם",   # x12 — e.g. אַבְשָׁלֹ֥ם
    "אחימעץ",   # x11 — e.g. אֲחִימָ֑עַץ
    "אליקים",   # x11 — e.g. אֶלְיָקִ֥ים
    "יאיר",   # x11 — e.g. יָאִֽיר׃
    "נינוה",   # x11 — e.g. נִ֣ינְוֵ֔ה
    "אחיטוב",   # x10 — e.g. אֲחִיט֜וּב
    "אחימלך",   # x10 — e.g. אֲחִימֶ֖לֶךְ
    "אמריה",   # x10 — e.g. אֲמַרְיָ֔ה
    "ארנון",   # x10 — e.g. אַרְנוֹן֙
    "יעזר",   # x10 — e.g. יַעְזֵ֔ר
    "ירחם",   # x10 — e.g. יְרֹחָ֧ם
    "נעמן",   # x10 — e.g. נַעֲמָֽן׃
    "נתנאל",   # x10 — e.g. נְתַנְאֵ֖ל
    "אמציה",   # x9 — e.g. אֲמַצְיָ֥ה
    "יתרו",   # x9 — e.g. יִתְר֥וֹ
    "ארונה",   # x8 — e.g. אֲרַ֥וְנָה
    "אשקלון",   # x8 — e.g. אַשְׁקְל֖וֹן
    "יובב",   # x8 — e.g. יוֹבָ֑ב
    "יעיאל",   # x8 — e.g. יְעִיאֵ֖ל
    "נחשון",   # x8 — e.g. נַחְשׁ֖וֹן
    "תבור",   # x8 — e.g. תָּב֔וֹר
    "אביעזר",   # x7 — e.g. אֲבִיעֶ֜זֶר
    "אפרתה",   # x7 — e.g. אֶפְרָ֑תָה
    "אשדוד",   # x7 — e.g. אַשְׁדּ֖וֹד
    "ידעיה",   # x7 — e.g. יְדַֽעְיָ֥ה
    "יהוחנן",   # x7 — e.g. יְהוֹחָנָ֣ן
    "יהונדב",   # x7 — e.g. יְה֣וֹנָדָ֔ב
    "יהוצדק",   # x7 — e.g. יְהוֹצָדָֽק׃
    "ירחמאל",   # x7 — e.g. יְרַחְמְאֵ֥ל
    "נבכדנאצר",   # x7 — e.g. נְבֻכַדְנֶאצַּ֖ר
    "נריה",   # x7 — e.g. נֵרִיָּה֮
    "אדניה",   # x6 — e.g. אֲדֹנִיָּ֣ה
    "אהליבמה",   # x6 — e.g. אָהֳלִֽיבָמָה֙
    "אופיר",   # x6 — e.g. אוֹפִ֥יר
    "אחיעזר",   # x6 — e.g. אֲחִיעֶ֖זֶר
    "אליהוא",   # x6 — e.g. אֱלִיה֛וּא
    "אליסף",   # x6 — e.g. אֶלְיָסָ֖ף
    "ידותון",   # x6 — e.g. יְדוּת֑וּן
    "יכניה",   # x6 — e.g. יְכָנְיָ֥ה
    "יעוש",   # x6 — e.g. יְע֥וּשׁ
    "יצהר",   # x6 — e.g. יִצְהָ֑ר
    "ירמות",   # x6 — e.g. יַרְמ֜וּת
    "תענך",   # x6 — e.g. תַּעְנַךְ֙
    "אביגיל",   # x5 — e.g. אֲבִיגַ֡יִל
    "אבידן",   # x5 — e.g. אֲבִידָ֖ן
    "אבים",   # x5 — e.g. אֲבִיָּ֥ם
    "אהלה",   # x5 — e.g. אָהֳלָ֤ה
    "אהליבה",   # x5 — e.g. אָהֳלִיבָֽה׃
    "אורי",   # x5 — e.g. אוּרִ֥י
    "אחזיה",   # x5 — e.g. אֲחַזְיָ֜ה
    "אחילוד",   # x5 — e.g. אֲחִיל֖וּד
    "אחינעם",   # x5 — e.g. אֲחִינֹ֖עַם
    "אחירע",   # x5 — e.g. אֲחִירַ֖ע
    "אליאל",   # x5 — e.g. אֱלִיאֵ֖ל
    "אליצור",   # x5 — e.g. אֱלִיצ֖וּר
    "ארתחשסתא",   # x5 — e.g. אַרְתַּחְשַׁ֣סְתְּא
    "יהוד",   # x5 — e.g. יְה֖וּד
    "יואח",   # x5 — e.g. יוֹאָ֤ח
    "יונדב",   # x5 — e.g. יֽוֹנָדָ֔ב
    "יוצדק",   # x5 — e.g. יֽוֹצָדָ֜ק
    "יחיאל",   # x5 — e.g. יְחִיאֵ֛ל
    "יעקוב",   # x5 — e.g. יַעֲק֑וֹב
    "ישיה",   # x5 — e.g. יִשִּׁיָּ֛ה
    "נבכדנצר",   # x5 — e.g. נְבֻכַדְנֶצַּֽר׃
    "נהרים",   # x5 — e.g. נַֽהֲרַ֖יִם
    "נמשי",   # x5 — e.g. נִמְשִׁ֔י
    "תולע",   # x5 — e.g. תּוֹלָ֥ע
    "תלמי",   # x5 — e.g. תַּלְמַ֔י
    "אביחיל",   # x4 — e.g. אֲבִיחָ֑יִל
    "אבינעם",   # x4 — e.g. אֲבִינֹ֔עַם
    "אבישג",   # x4 — e.g. אֲבִישַׁג֙
    "אבשי",   # x4 — e.g. אַבְשַׁ֣י
    "אולם",   # x4 — e.g. אוּלָ֥ם
    "אחיהו",   # x4 — e.g. אֲחִיָּ֗הוּ
    "אחשורש",   # x4 — e.g. אֲחַשְׁוֵֽרֹשׁ׃
    "אלחנן",   # x4 — e.g. אֶלְחָנָן֩
    "אליועיני",   # x4 — e.g. אֶלְיוֹעֵינַ֧י
    "אליצפן",   # x4 — e.g. אֶלִיצָפָ֖ן
    "אלעשה",   # x4 — e.g. אֶלְעָשָֽׂה׃
    "ארגב",   # x4 — e.g. אַרְגֹּ֔ב
    "אריאל",   # x4 — e.g. אֲרִיאֵל֙
    "אריוך",   # x4 — e.g. אַרְי֖וֹךְ
    "ארפכשד",   # x4 — e.g. אַרְפַּכְשָׁ֑ד
    "אררט",   # x4 — e.g. אֲרָרָֽט׃
    "אשכל",   # x4 — e.g. אֶשְׁכֹּל֙
    "יאור",   # x4 — e.g. יְא֖וֹר
    "ידיעאל",   # x4 — e.g. יְדִיעֲאֵ֖ל
    "יהודי",   # x4 — e.g. יְהוּדִ֡י
    "יוזבד",   # x4 — e.g. יוֹזָבָ֧ד
    "יוידע",   # x4 — e.g. יֽוֹיָדָע֙
    "יעבץ",   # x4 — e.g. יַעְבֵּ֔ץ
    "יעקן",   # x4 — e.g. יַעֲקָֽן׃
    "יקטן",   # x4 — e.g. יָקְטָֽן׃
    "יקנעם",   # x4 — e.g. יָקְנֳעָ֥ם
    "ישעי",   # x4 — e.g. יִשְׁעִ֑י
    "נביות",   # x4 — e.g. נְבָי֛וֹת
    "נעמה",   # x4 — e.g. נַֽעֲמָֽה׃
    "נקודא",   # x4 — e.g. נְקוֹדָ֖א
    "נתניהו",   # x4 — e.g. נְתַנְיָ֔הוּ
    "תמנע",   # x4 — e.g. תִּמְנָֽע׃
    "תתני",   # x4 — e.g. תַּ֠תְּנַי
    "אביאל",   # x3 — e.g. אֲבִיאֵ֞ל
    "אבישוע",   # x3 — e.g. אֲבִישֽׁוּעַ׃
    "אדניקם",   # x3 — e.g. אֲדֹ֣נִיקָ֔ם
    "אהוא",   # x3 — e.g. אַהֲוָ֔א
    "אהליאב",   # x3 — e.g. אָהֳלִיאָ֞ב
    "אוריאל",   # x3 — e.g. אוּרִיאֵ֣ל
    "אוריהו",   # x3 — e.g. אֽוּרִיָּ֙הוּ֙
    "אחטוב",   # x3 — e.g. אֲחִט֡וּב
    "אחימן",   # x3 — e.g. אֲחִימַן֙
    "אחיסמך",   # x3 — e.g. אֲחִֽיסָמָךְ֙
    "אלון",   # x3 — e.g. אַלּ֥וֹן
    "אליפלט",   # x3 — e.g. אֱלִיפֶ֥לֶט
    "אלישה",   # x3 — e.g. אֱלִישָׁ֣ה
    "אלנתן",   # x3 — e.g. אֶלְנָתָ֖ן
    "אלפעל",   # x3 — e.g. אֶלְפָּֽעַל׃
    "אמריהו",   # x3 — e.g. אֲמַרְיָ֙הוּ֙
    "אשתמע",   # x3 — e.g. אֶשְׁתְּמֹ֖עַ
    "יויקים",   # x3 — e.g. יֽוֹיָקִ֑ים
    "יחזיאל",   # x3 — e.g. יַחֲזִיאֵל֙
    "יכין",   # x3 — e.g. יָכִ֔ין
    "ימנה",   # x3 — e.g. יִמְנָ֧ה
    "יעלם",   # x3 — e.g. יַעְלָ֖ם
    "יפלט",   # x3 — e.g. יַפְלֵ֔ט
    "ישוב",   # x3 — e.g. יָשׁ֥וּב
    "ישחק",   # x3 — e.g. יִשְׂחָ֣ק
    "נרגל",   # x3 — e.g. נֵֽרְגַ֑ל
    "נריהו",   # x3 — e.g. נֵרִיָּ֤הוּ
    "תבני",   # x3 — e.g. תִבְנִ֤י
    "תגלת",   # x3 — e.g. תִּגְלַ֣ת
    "תחתון",   # x3 — e.g. תַּחְתּ֖וֹן
    "תלגת",   # x3 — e.g. תִּלְּגַ֥ת
    "תרצה",   # x3 — e.g. תִרְצָ֗ה
    "אביהו",   # x2 — e.g. אֲבִיָּ֑הוּ
    "אביהוא",   # x2 — e.g. אֲבִיה֔וּא
    "אביהיל",   # x2 — e.g. אֲבִיהָ֑יִל
    "אבימאל",   # x2 — e.g. אֲבִֽימָאֵ֖ל
    "אביסף",   # x2 — e.g. אֶבְיָסָ֖ף
    "אבישלום",   # x2 — e.g. אֲבִישָׁלֽוֹם׃
    "אבצן",   # x2 — e.g. אִבְצָ֖ן
    "אדמים",   # x2 — e.g. אֲדֻמִּ֔ים
    "אדרעי",   # x2 — e.g. אֶדְרֶֽעִי׃
    "אוזל",   # x2 — e.g. אוּזָ֖ל
    "אויל",   # x2 — e.g. אֱוִ֣יל
    "אומר",   # x2 — e.g. אוֹמָ֔ר
    "אונו",   # x2 — e.g. אוֹנ֔וֹ
    "אונם",   # x2 — e.g. אוֹנָֽם׃
    "אונן",   # x2 — e.g. אוֹנָֽן׃
    "אחיאם",   # x2 — e.g. אֲחִיאָ֥ם
    "אחלי",   # x2 — e.g. אַחְלָֽי׃
    "אילות",   # x2 — e.g. אֵיל֛וֹת
    "אכזיב",   # x2 — e.g. אַכְזִיב֙
    "אכשף",   # x2 — e.g. אַכְשָֽׁף׃
    "אלדד",   # x2 — e.g. אֶלְדָּ֡ד
    "אלזבד",   # x2 — e.g. אֶלְזָבָ֖ד
    "אלידע",   # x2 — e.g. אֶלְיָדָ֑ע
    "אליהועיני",   # x2 — e.g. אֶלְיְהוֹעֵינַ֖י
    "אליחבא",   # x2 — e.g. אֶלְיַחְבָּא֙
    "אליעם",   # x2 — e.g. אֱלִיעָ֔ם
    "אלמודד",   # x2 — e.g. אַלְמוֹדָ֖ד
    "אלסר",   # x2 — e.g. אֶלָּסָ֑ר
    "אמנה",   # x2 — e.g. אֲמָנָ֨ה
    "אמצי",   # x2 — e.g. אַמְצִ֥י
    "אמרי",   # x2 — e.g. אִמְרִ֣י
    "אפרת",   # x2 — e.g. אֶפְרָ֔ת
    "אצליהו",   # x2 — e.g. אֲצַלְיָ֤הוּ
    "ארפד",   # x2 — e.g. אַרְפָּ֔ד
    "ארתחששת",   # x2 — e.g. אַרְתַּחְשַׁ֖שְׂתְּ
    "ארתחששתא",   # x2 — e.g. אַרְתַּחְשַׁ֗שְׂתָּא
    "אשבעל",   # x2 — e.g. אֶשְׁבָּֽעַל׃
    "אשכול",   # x2 — e.g. אֶשְׁכּ֑וֹל
    "אשכנז",   # x2 — e.g. אַשְׁכֲּנַ֥ז
    "אשריאל",   # x2 — e.g. אַשְׂרִיאֵל֙
    "אשתאל",   # x2 — e.g. אֶשְׁתָּאֹֽל׃
    "יאזניה",   # x2 — e.g. יַאֲזַנְיָ֤ה
    "יבלעם",   # x2 — e.g. יִבְלְעָם֙
    "יגאל",   # x2 — e.g. יִגְאָ֖ל
    "ידוע",   # x2 — e.g. יַדּֽוּעַ׃
    "ידיה",   # x2 — e.g. יְדָיָ֥ה
    "יהוזבד",   # x2 — e.g. יְהוֹזָבָ֣ד
    "יהועדן",   # x2 — e.g. יְהֽוֹעַדָּ֖ן
    "יהושבעת",   # x2 — e.g. יְהוֹשַׁבְעַ֨ת
    "יהושוע",   # x2 — e.g. יְהוֹשׁ֣וּעַ
    "יהללאל",   # x2 — e.g. יְהַלֶּלְאֵ֑ל
    "יויריב",   # x2 — e.g. יוֹיָרִ֛יב
    "יוכבד",   # x2 — e.g. יוֹכֶ֤בֶד
    "יזרחיה",   # x2 — e.g. יִֽזְרַֽחְיָ֑ה
    "יחדיהו",   # x2 — e.g. יֶחְדְּיָֽהוּ׃
    "יחזקיה",   # x2 — e.g. יְחִזְקִיָּ֖ה
    "יטור",   # x2 — e.g. יְט֥וּר
    "ימואל",   # x2 — e.g. יְמוּאֵ֧ל
    "ימלא",   # x2 — e.g. יִמְלָ֑א
    "ימלה",   # x2 — e.g. יִמְלָ֑ה
    "יפיע",   # x2 — e.g. יָפִ֧יעַ
    "יקמיה",   # x2 — e.g. יְקַמְיָ֔ה
    "יקמעם",   # x2 — e.g. יָקְמְעָם֙
    "יקשן",   # x2 — e.g. יָקְשָׁ֔ן
    "יראייה",   # x2 — e.g. יִרְאִיָּ֔יה
    "יריהו",   # x2 — e.g. יְרִיָּ֤הוּ
    "ירימות",   # x2 — e.g. יְרִימ֖וֹת
    "ישבעם",   # x2 — e.g. יָשָׁבְעָ֣ם
    "ישרון",   # x2 — e.g. יְשֻׁרוּן֙
    "יתרעם",   # x2 — e.g. יִתְרְעָ֔ם
    "נהלל",   # x2 — e.g. נַהֲלָ֖ל
    "נחום",   # x2 — e.g. נְח֣וּם
    "נחרי",   # x2 — e.g. נַחְרַי֙
    "ניסן",   # x2 — e.g. נִיסָ֗ן
    "נמואל",   # x2 — e.g. נְמוּאֵ֖ל
    "נמרד",   # x2 — e.g. נִמְרֹ֑ד
    "נמרה",   # x2 — e.g. נִמְרָ֖ה
    "נמרים",   # x2 — e.g. נִמְרִ֖ים
    "נסרך",   # x2 — e.g. נִסְרֹ֣ךְ
    "נפיש",   # x2 — e.g. נָפִ֖ישׁ
    "נפתוח",   # x2 — e.g. נֶפְתּ֔וֹחַ
    "נפתחים",   # x2 — e.g. נַפְתֻּחִֽים׃
    "נציח",   # x2 — e.g. נְצִ֖יחַ
    "תדמר",   # x2 — e.g. תַּדְמֹ֥ר
    "תובל",   # x2 — e.g. תּ֣וּבַל
    "תוגרמה",   # x2 — e.g. תּוֹגַרְמָ֑ה
    "תחפניס",   # x2 — e.g. תַּחְפְּנֵ֥יס
    "תימא",   # x2 — e.g. תֵּימָ֔א
    "תמנה",   # x2 — e.g. תִּמְנָֽה׃
    "תנחמת",   # x2 — e.g. תַּנְחֻ֜מֶת
    "תרהקה",   # x2 — e.g. תִּרְהָ֤קָה
    "אבגיל",   # x1 — e.g. אֲבִגָ֑יִל
    "אביב",   # x1 — e.g. אָ֠בִיב
    "אביגל",   # x1 — e.g. אֲבִיגַ֣ל
    "אביטוב",   # x1 — e.g. אֲבִיט֖וּב
    "אביטל",   # x1 — e.g. אֲבִיטָֽל׃
    "אבינר",   # x1 — e.g. אֲבִינֵ֔ר
    "אבירם",   # x1 — e.g. אֲבִירָֽם׃
    "אבישור",   # x1 — e.g. אֲבִישׁ֖וּר
    "אגור",   # x1 — e.g. אָג֥וּר
    "אגלים",   # x1 — e.g. אֶגְלַ֙יִם֙
    "אדוניה",   # x1 — e.g. אֲדוֹנִיָּ֖ה
    "אדורים",   # x1 — e.g. אֲדוֹרַ֥יִם
    "אדליא",   # x1 — e.g. אֲדַלְיָ֖א
    "אדמתא",   # x1 — e.g. אַדְמָ֣תָא
    "אדרם",   # x1 — e.g. אֲדֹרָם֙
    "אוביל",   # x1 — e.g. אוֹבִ֖יל
    "אוזי",   # x1 — e.g. אוּזַי֮
    "אוני",   # x1 — e.g. אוֹנִ֑י
    "אופז",   # x1 — e.g. אוּפָֽז׃
    "אופר",   # x1 — e.g. אוֹפִ֥ר
    "אזבי",   # x1 — e.g. אֶזְבָּֽי׃
    "אזנות",   # x1 — e.g. אַזְנ֣וֹת
    "אזניה",   # x1 — e.g. אֲזַנְיָ֔ה
    "אחבן",   # x1 — e.g. אַחְבָּ֖ן
    "אחוד",   # x1 — e.g. אֵח֑וּד
    "אחומי",   # x1 — e.g. אֲחוּמַ֖י
    "אחזי",   # x1 — e.g. אַחְזַ֥י
    "אחזם",   # x1 — e.g. אֲחֻזָּ֣ם
    "אחיהוד",   # x1 — e.g. אֲחִיה֖וּד
    "אחיחד",   # x1 — e.g. אֲחִיחֻֽד׃
    "אחין",   # x1 — e.g. אַחְיָ֣ן
    "אחינדב",   # x1 — e.g. אֲחִֽינָדָ֥ב
    "אחלב",   # x1 — e.g. אַחְלָ֤ב
    "אחסבי",   # x1 — e.g. אֲחַסְבַּ֖י
    "אחרחל",   # x1 — e.g. אֲחַרְחֵ֖ל
    "איכבוד",   # x1 — e.g. אִיכָב֣וֹד׀
    "אילן",   # x1 — e.g. אֵילֹ֖ן
    "איעזר",   # x1 — e.g. אִיעֶ֕זֶר
    "אישהוד",   # x1 — e.g. אִישְׁה֔וֹד
    "איתי",   # x1 — e.g. אִיתַ֣י
    "איתיאל",   # x1 — e.g. אִֽיתִיאֵ֖ל
    "אלות",   # x1 — e.g. אֵל֛וֹת
    "אליאתה",   # x1 — e.g. אֱלִיאָ֤תָה
    "אלידד",   # x1 — e.g. אֱלִידָ֖ד
    "אליועני",   # x1 — e.g. אֶלְיוֹעֵנַ֤י
    "אליחרף",   # x1 — e.g. אֱלִיחֹ֧רֶף
    "אליפל",   # x1 — e.g. אֱלִיפַ֥ל
    "אליקא",   # x1 — e.g. אֱלִיקָ֖א
    "אלישבע",   # x1 — e.g. אֱלִישֶׁ֧בַע
    "אלישפט",   # x1 — e.g. אֱלִישָׁפָ֥ט
    "אלנעם",   # x1 — e.g. אֶלְנָ֑עַם
    "אלעוזי",   # x1 — e.g. אֶלְעוּזַ֤י
    "אלעלא",   # x1 — e.g. אֶלְעָלֵ֑א
    "אלעלה",   # x1 — e.g. אֶלְעָלֵ֗ה
    "אלצפן",   # x1 — e.g. אֶלְצָפָ֔ן
    "אלתקא",   # x1 — e.g. אֶלְתְּקֵ֖א
    "אמים",   # x1 — e.g. אֵמִֽים׃
    "אמנן",   # x1 — e.g. אַמְנֹ֗ן
    "אמרפל",   # x1 — e.g. אַמְרָפֶ֣ל
    "אסנה",   # x1 — e.g. אַסְנָ֥ה
    "אסנפר",   # x1 — e.g. אָסְנַפַּר֙
    "אספתא",   # x1 — e.g. אַסְפָּֽתָא׃
    "אפיח",   # x1 — e.g. אֲפִ֖יחַ
    "אפים",   # x1 — e.g. אַפַּ֖יִם
    "אפיק",   # x1 — e.g. אֲפִ֖יק
    "אפלל",   # x1 — e.g. אֶפְלָ֔ל
    "אצבון",   # x1 — e.g. אֶצְבּ֡וֹן
    "אראל",   # x1 — e.g. אֲרִאֵל֙
    "ארבאל",   # x1 — e.g. אַֽרְבֵ֖אל
    "ארדי",   # x1 — e.g. אֲרִדַ֖י
    "ארוד",   # x1 — e.g. אַרְוַ֣ד
    "ארידתא",   # x1 — e.g. אֲרִידָֽתָא׃
    "אריסי",   # x1 — e.g. אֲרִיסַ֔י
    "ארמני",   # x1 — e.g. אַרְמֹנִ֖י
    "ארצא",   # x1 — e.g. אַרְצָ֔א
    "אשבל",   # x1 — e.g. אַשְׁבֵּל֙
    "אשבע",   # x1 — e.g. אַשְׁבֵּֽעַ׃
    "אשחור",   # x1 — e.g. אַשְׁח֖וּר
    "אשימא",   # x1 — e.g. אֲשִׁימָֽא׃
    "אשתאול",   # x1 — e.g. אֶשְׁתָּא֥וֹל
    "אשתון",   # x1 — e.g. אֶשְׁתּֽוֹן׃
    "אתבעל",   # x1 — e.g. אֶתְבַּ֙עַל֙
    "אתני",   # x1 — e.g. אֶתְנִ֥י
    "יאושיהו",   # x1 — e.g. יֹאושִׁיָּ֖הוּ
    "יאשיה",   # x1 — e.g. יֹאשִׁיָּ֣ה
    "יאתרי",   # x1 — e.g. יְאָתְרַ֥י
    "יבנאל",   # x1 — e.g. יַבְנְאֵ֑ל
    "יבנה",   # x1 — e.g. יַבְנֵ֔ה
    "יבניה",   # x1 — e.g. יִבְנִיָּֽה׃
    "יברכיהו",   # x1 — e.g. יְבֶרֶכְיָֽהוּ׃
    "יגדליהו",   # x1 — e.g. יִגְדַּלְיָ֖הוּ
    "יגלי",   # x1 — e.g. יָגְלִֽי׃
    "ידידה",   # x1 — e.g. יְדִידָ֥ה
    "ידידיה",   # x1 — e.g. יְדִ֣ידְיָ֑הּ
    "ידיתון",   # x1 — e.g. יְדִית֛וּן
    "ידלף",   # x1 — e.g. יִדְלָ֑ף
    "יהדי",   # x1 — e.g. יָהְדָּ֑י
    "יהודית",   # x1 — e.g. יְהוּדִ֔ית
    "יהויכן",   # x1 — e.g. יְהוֹיָכִ֣ן
    "יהויקם",   # x1 — e.g. יְהוֹיָקִ֥ם
    "יהוכל",   # x1 — e.g. יְהוּכַ֣ל
    "יהועדה",   # x1 — e.g. יְהוֹעַדָּ֔ה
    "יהושבע",   # x1 — e.g. יְהוֹשֶׁ֣בַע
    "יובל",   # x1 — e.g. יוּבָ֑ל
    "יויכין",   # x1 — e.g. יוֹיָכִֽין׃
    "יוספיה",   # x1 — e.g. יוֹסִפְיָ֑ה
    "יועד",   # x1 — e.g. יוֹעֵ֡ד
    "יועש",   # x1 — e.g. יוֹעָֽשׁ׃
    "יורה",   # x1 — e.g. יוֹרָ֔ה
    "יושב",   # x1 — e.g. י֥וּשַׁב
    "יושביה",   # x1 — e.g. י֣וֹשִׁבְיָ֔ה
    "יזיז",   # x1 — e.g. יָזִ֣יז
    "יחזרה",   # x1 — e.g. יַחְזֵ֛רָה
    "יחצאל",   # x1 — e.g. יַחְצְאֵ֥ל
    "יחציאל",   # x1 — e.g. יַחֲצִיאֵ֧ל
    "יטבה",   # x1 — e.g. יָטְבָֽה׃
    "יטבתה",   # x1 — e.g. יָטְבָ֔תָה
    "יכליה",   # x1 — e.g. יְכָלְיָ֖ה
    "יכליהו",   # x1 — e.g. יְכָלְיָ֖הוּ
    "יכניהו",   # x1 — e.g. יְכָנְיָ֣הוּ
    "ימימה",   # x1 — e.g. יְמִימָ֔ה
    "ימין",   # x1 — e.g. יָמִ֡ין
    "ינוח",   # x1 — e.g. יָ֠נוֹחַ
    "ינוחה",   # x1 — e.g. יָנֽוֹחָה׃
    "יסכה",   # x1 — e.g. יִסְכָּֽה׃
    "יעדו",   # x1 — e.g. יֶעְדּ֣וֹ
    "יעואל",   # x1 — e.g. יְעוּאֵ֑ל
    "יעוץ",   # x1 — e.g. יְע֥וּץ
    "יעזיהו",   # x1 — e.g. יַעֲזִיָּ֥הֽוּ
    "יעזיר",   # x1 — e.g. יַעְזֵ֖יר
    "יעיר",   # x1 — e.g. יָעִ֗יר
    "יעלא",   # x1 — e.g. יַעְלָ֥א
    "יעלה",   # x1 — e.g. יַעְלָ֥ה
    "יערה",   # x1 — e.g. יַעְרָ֔ה
    "יערי",   # x1 — e.g. יַעְרֵ֨י
    "יעשיאל",   # x1 — e.g. יַעֲשִׂיאֵ֖ל
    "יפוא",   # x1 — e.g. יָפ֔וֹא
    "יקותיאל",   # x1 — e.g. יְקֽוּתִיאֵ֖ל
    "יקתאל",   # x1 — e.g. יָקְתְאֵ֔ל
    "ירבשת",   # x1 — e.g. יְרֻבֶּ֗שֶׁת
    "ירואל",   # x1 — e.g. יְרוּאֵֽל׃
    "ירוח",   # x1 — e.g. יָ֠רוֹחַ
    "ירושא",   # x1 — e.g. יְרוּשָׁ֖א
    "ירושה",   # x1 — e.g. יְרוּשָׁ֖ה
    "ירחע",   # x1 — e.g. יַרְחָֽע׃
    "יריב",   # x1 — e.g. יָרִ֖יב
    "יריה",   # x1 — e.g. יְרִיָּ֣ה
    "יריחה",   # x1 — e.g. יְרִיחֹ֑ה
    "יריעות",   # x1 — e.g. יְרִיע֑וֹת
    "ירמי",   # x1 — e.g. יְרֵמַ֥י
    "ירקעם",   # x1 — e.g. יָרְקֳעָ֑ם
    "ישבח",   # x1 — e.g. יִשְׁבָּ֖ח
    "ישבק",   # x1 — e.g. יִשְׁבָּ֖ק
    "ישבקשה",   # x1 — e.g. יָשְׁבְּקָ֣שָׁה
    "ישישי",   # x1 — e.g. יְשִׁישַׁ֥י
    "ישמעיהו",   # x1 — e.g. יִֽשְׁמַֽעְיָ֖הוּ
    "ישנה",   # x1 — e.g. יְשָׁנָ֖ה
    "ישראלה",   # x1 — e.g. יְשַׂרְאֵ֔לָה
    "יתניאל",   # x1 — e.g. יַתְנִיאֵ֖ל
    "יתרא",   # x1 — e.g. יִתְרָ֣א
    "נבוזר",   # x1 — e.g. נְבֽוּזַר
    "נבחז",   # x1 — e.g. נִבְחַ֖ז
    "נבית",   # x1 — e.g. נְבָיֹ֔ת
    "נבלט",   # x1 — e.g. נְבַלָּֽט׃
    "נגוא",   # x1 — e.g. נְג֔וֹא
    "נוחה",   # x1 — e.g. נוֹחָה֙
    "נחבי",   # x1 — e.g. נַחְבִּ֖י
    "נחליאל",   # x1 — e.g. נַחֲלִיאֵ֑ל
    "נחמני",   # x1 — e.g. נַחֲמָ֜נִי
    "נחשתא",   # x1 — e.g. נְחֻשְׁתָּ֥א
    "נחשתן",   # x1 — e.g. נְחֻשְׁתָּֽן׃
    "נטעים",   # x1 — e.g. נְטָעִ֖ים
    "נטפה",   # x1 — e.g. נְטֹפָ֖ה
    "ניבי",   # x1 — e.g. נֵיבָֽי׃
    "ניות",   # x1 — e.g. נָי֖וֹת
    "נכון",   # x1 — e.g. נָכ֑וֹן
    "נערי",   # x1 — e.g. נַעֲרַ֖י
    "נעריה",   # x1 — e.g. נְעַרְיָ֗ה
    "נערן",   # x1 — e.g. נַעֲרָ֔ן
    "נפוסים",   # x1 — e.g. נְפוּסִֽים׃
    "נפישסים",   # x1 — e.g. נְפִֽישְׁסִֽים׃
    "תאנת",   # x1 — e.g. תַּאֲנַ֣ת
    "תבערה",   # x1 — e.g. תַּבְעֵרָ֑ה
    "תחנה",   # x1 — e.g. תְּחִנָּ֖ה
    "תחפנחס",   # x1 — e.g. תַּחְפַּנְחֵֽס׃
    "תחפנס",   # x1 — e.g. תַחְפְּנֵ֔ס
    "תחתים",   # x1 — e.g. תַּחְתִּ֖ים
    "תיריא",   # x1 — e.g. תִּירְיָ֖א
    "תמנת",   # x1 — e.g. תִּמְנַת
    "תקהת",   # x1 — e.g. תָּקְהַ֗ת
    "תרחנה",   # x1 — e.g. תִּרְחֲנָֽה׃
    "תרעתים",   # x1 — e.g. תִּרְעָתִ֥ים
    "תרתק",   # x1 — e.g. תַּרְתָּ֑ק
}


def is_finite_verb_skel(skeleton: str) -> bool:
    """Heuristic: True if consonant skeleton looks like a finite Hebrew verb.

    Conservative: prefers false-positive (over-detection causes skip-when-guard,
    not fire-when-shouldn't).
    """
    if not skeleton:
        return False
    if skeleton in QATAL_COMMON:
        return True
    # wayyiqtol prefix — ו + (י|ת|א|נ) + verb stem
    # Covers: וי (3ms/3mp/2fp), ות (3fs/2ms/2fp/2mp), וא (1cs), ון (1cp)
    # Filter: if inner skeleton is in YIQTOL_KNOWN_NOUNS, it's vav+noun, not wayyiqtol.
    # Length floor: shortest real wayyiqtol skel is 4 (וַיְהִי = "ויהי"); len-3 false-
    # matches "ואל" (vav-prep אֶל), "ואת" (vav-DO-marker), etc. as wayyiqtol.
    if (
        len(skeleton) >= 4
        and skeleton[0] == "ו"
        and skeleton[1] in YIQTOL_PREFIXES
    ):
        inner = skeleton[1:]
        if inner in YIQTOL_KNOWN_NOUNS:
            return False
        return True
    # Weqatal — ו + qatal verb stem (audited Lev 1:6 וְהִפְשִׁיט / Lev 16:7 וְלָקַח).
    # If the inner skeleton (without vav) is in QATAL_COMMON, treat as weqatal.
    # Vav-prefixed nouns are filtered via YIQTOL_KNOWN_NOUNS membership above
    # (already handled for the wayyiqtol case).
    if len(skeleton) >= 4 and skeleton[0] == "ו":
        inner = skeleton[1:]
        if inner in QATAL_COMMON:
            return True
    # yiqtol — single-prefix + 3-letter root skeleton
    # Pattern: prefix (י/ת/א/נ) + root consonants ≥ 3 total chars
    # Uses module-level YIQTOL_KNOWN_NOUNS (also reused by wayyiqtol filter above).
    if len(skeleton) >= 3 and skeleton[0] in YIQTOL_PREFIXES:
        if skeleton not in YIQTOL_KNOWN_NOUNS and skeleton != "יש":
            if len(skeleton) >= 4:
                return True
    return False


HOLAM = "ֹ"  # ֹ — niqqud holam (signals qal active participle CōCēC pattern)


def _first_vowel_is_holam(token: str) -> bool:
    """True if the first niqqud after the first Hebrew consonant is holam.

    Distinguishes qal active participle (CōCēC, e.g., עֹשֶׂה "doing/maker")
    from qal qatal (CāCaC, e.g., עָשָׂה "he did") — same consonant skeleton,
    different finite/non-finite status. Holam-first is participle (or infinitive-
    construct without prefix), neither of which is finite.
    """
    found_first_consonant = False
    for ch in token:
        cp = ord(ch)
        if 0x05D0 <= cp <= 0x05EA:  # Hebrew letter
            if found_first_consonant:
                return False  # hit second consonant before any vowel
            found_first_consonant = True
        elif found_first_consonant and 0x05B0 <= cp <= 0x05BD:  # niqqud
            return cp == 0x05B9
    return False


## Note: niqqud-policy per canon §1 (2026-04-29 + extension 2026-04-29-pm).
## Hybrid approach:
##   - Niqqud-AWARE checks are reserved for morpho-lexical patterns that cannot be
##     enumerated lexically (qal active participle CōCēC — every active verb has one,
##     too many to list). _first_vowel_is_holam was the seed; is_mem_prefix_participle
##     and is_wayyiqtol_token extend the same hybrid policy to handle whack-a-mole
##     false-positive classes (mem-prep + adjective; vav-conjunction + alpha-noun).
##   - All other α-/ת-/נ-prefix-noun-vs-verb disambiguations use lexical exclusion
##     via YIQTOL_KNOWN_NOUNS (consonant-skeleton-anchored). Niqqud is NOT a
##     break-licensing criterion at any layer.

# Niqqud codepoint constants (used by mem-prefix + wayyiqtol disambiguation)
SHEVA = "ְ"
HIREQ = "ִ"
PATAH = "ַ"
QAMATS = "ָ"
DAGESH = "ּ"
TAV = "ת"


def _first_vowel_and_next_consonant(token: str) -> tuple[str | None, str | None, bool]:
    """Walk a token; return (first_vowel_after_first_consonant,
    second_consonant, second_consonant_has_dagesh).

    Returns (None, None, False) if the structure isn't found (unpointed,
    too-short, etc.). Used by is_mem_prefix_participle and is_wayyiqtol_token
    to inspect the niqqud signature distinguishing participle/wayyiqtol from
    common false-positive classes.
    """
    found_first_consonant = False
    first_consonant = None
    vowel = None
    next_consonant = None
    next_has_dagesh = False
    i = 0
    while i < len(token):
        ch = token[i]
        cp = ord(ch)
        if 0x05D0 <= cp <= 0x05EA:  # Hebrew letter
            if not found_first_consonant:
                found_first_consonant = True
                first_consonant = ch
            elif vowel is not None and next_consonant is None:
                next_consonant = ch
                # Scan forward for dagesh on this consonant. TAHOT Unicode order
                # is consonant + niqqud + dagesh (vowel-before-dagesh), so peek
                # past niqqud until we find dagesh OR another consonant.
                j = i + 1
                while j < len(token):
                    cp_j = ord(token[j])
                    if cp_j == 0x05BC:  # dagesh
                        next_has_dagesh = True
                        break
                    if 0x05D0 <= cp_j <= 0x05EA:  # next consonant — stop scan
                        break
                    j += 1
                return (vowel, next_consonant, next_has_dagesh)
        elif found_first_consonant and vowel is None and 0x05B0 <= cp <= 0x05BD:
            if cp == 0x05BC:
                # Dagesh: usually gemination of NEXT consonant, NOT a vowel.
                # Exception: vav + dagesh = shuruk (the וּ vowel itself, marking
                # vav-conjunction or "and-" with following labial/sheva). Treat
                # the dagesh AS the vav's vowel so callers don't read past it
                # to the next consonant's vowel.
                if first_consonant == "ו":
                    vowel = ch
                # else: skip — dagesh on non-vav first consonant is gemination
            else:
                vowel = ch
        i += 1
    return (vowel, next_consonant, next_has_dagesh)


def is_mem_prefix_participle(token: str) -> bool:
    """Niqqud-aware: classify a mem-initial token as participle vs noun/prep.

    Replaces the crude `len(skel) >= 4 and starts-with-mem and not finite-verb`
    heuristic that whack-a-moled against מן-prep + adjective (מִקָּטֹן),
    proper nouns (מַתַּנְיָה), and qamats-mem nouns (מָקוֹם).

    Pattern table:
      מ + sheva   + C        → piel/pual ptcp        → True
      מ + patah   + C (with hiphil shape signature)  → True
      מ + qamats  + C (with hophal shape signature)  → True (low confidence)
      מ + hireq   + ת        → hithpael ptcp         → True
      מ + hireq   + C+dagesh → מן-prep + assim. nun  → False (the key fix)
      מ + hireq   + C (no dagesh, non-tav)           → False (mem-noun, fall through)

    Fail-soft: returns False on unpointed / partial-niqqud / structural-bail.
    """
    t = strip_teamim(token)
    if not t or t[0] != "מ":
        return False
    vowel, next_c, next_dagesh = _first_vowel_and_next_consonant(t)
    if vowel is None or next_c is None:
        return False
    # mem-hireq + dagesh = מן-prep with assimilated nun (the false-positive fix)
    if vowel == HIREQ and next_dagesh:
        return False
    # hithpael: mem-hireq + tav root marker
    if vowel == HIREQ and next_c == TAV:
        return True
    # piel/pual: mem-sheva
    if vowel == SHEVA:
        return True
    # hiphil: mem-patah; require ptcp shape (mem + ≥3 root letters)
    if vowel == PATAH:
        return len(skel(t)) >= 4
    # hophal: mem-qamats; narrow guard (suffix shape OR strict length-4)
    # to dodge qamats-mem nouns like מָקוֹם, מָגֵן.
    if vowel == QAMATS:
        s = skel(t)
        if s.endswith(("ת", "ים", "ות")) or len(s) == 4:
            return True
        return False
    # mem-hireq + non-tav, no dagesh: fall through (mem-noun or partial-niqqud)
    return False


def is_wayyiqtol_token(token: str) -> bool:
    """Niqqud-aware: True only if token bears wayyiqtol signature
       vav + patah + (yiqtol-prefix consonant) + dagesh.

    Replaces the bare consonant-skeleton heuristic for wayyiqtol detection,
    which false-matched ואל / ואת / וְאַבְרָהָם / etc. as wayyiqtols.

    Maqqef-joined compounds: check only the first sub-token (vav-prefix
    binds to the first head morpheme).

    Known FN: 1cs wayyiqtol with א-prefix (וָאֹמַר) lengthens vav to qamats
    and rejects dagesh on guttural; this branch returns False. Caller's
    skel-fallback (is_finite_verb_skel) catches it via the YIQTOL_PREFIXES
    consonant pattern.
    """
    t = strip_teamim(token)
    if MAQQEF in t:
        t = t.split(MAQQEF, 1)[0]
    if len(t) < 4 or t[0] != "ו":
        return False
    # vav must carry patah (wayyiqtol) — sheva (vav-conj) and qamats (וּ) reject
    vowel, next_c, next_dagesh = _first_vowel_and_next_consonant(t)
    if vowel != PATAH or next_c is None:
        return False
    # next consonant must be a yiqtol prefix
    if next_c not in YIQTOL_PREFIXES:
        return False
    # dagesh on prefix consonant is definitional for wayyiqtol (excluding the
    # 1cs א-prefix case noted in docstring — already filtered by patah-check
    # because 1cs wayyiqtol uses qamats, not patah)
    if not next_dagesh:
        return False
    return True


def is_finite_verb_token(token: str, tag_list: "list[str] | None" = None) -> bool:
    """True if the token (raw, with niqqud/te'amim) parses as a finite verb.

    Tag-driven primary path: if `tag_list` is provided (per-ortho TAHOT morph
    tags for this prosodic-word token), the LAST tag's head morpheme is the
    authoritative classifier — `V[stem][p/w/i/j/h/v/q]` heads are finite. This
    eliminates the systematic FP class where common nouns (דבר, ואין, ואיש)
    and weqatal/3p qatal forms get mis-classified by the skel-only heuristic.
    See `scripts/audit_morphology_vs_tahot.py` (2026-05-01 audit) for the
    14K FP / 18K FN class this addresses.

    Skel-fallback (legacy path, used when no tag is supplied):

    Niqqud-aware participle exclusion: holam after first consonant marks the
    qal active participle (or qal infinitive construct), neither finite —
    rules out עֹשֶׂה, רֹמֵשׂ, יֹשֵׁב, etc. that share skel with their qatal cousins.

    Maqqef-joined compounds: check only the first sub-token. The skel() of a
    full compound like אֶת־כָּל־יֶרֶק collapses to "אתכלירק" which spuriously
    matches the YIQTOL-prefix heuristic via the leading א. Splitting at maqqef
    isolates the head morpheme (here the DO marker את) so the check sees only
    "את", which correctly fails the prefix-verb test (length-2).
    """
    # ── Tag-driven primary path (TAHOT oracle) ────────────────────────
    if tag_list:
        # Find the LAST non-placeholder tag (head of the prosodic-word).
        head_tag = None
        for t in reversed(tag_list):
            if t and t != "[—]":
                head_tag = t
                break
        if head_tag is not None:
            from . import morph_tags as _MT
            return _MT.is_finite_verb(head_tag)

    # ── Skel-fallback (when no tag available) ─────────────────────────
    if MAQQEF in token:
        first_sub = token.split(MAQQEF, 1)[0]
        if _first_vowel_is_holam(first_sub):
            return False
        # Niqqud-aware wayyiqtol short-circuit (catches what skel-heuristic misses)
        if is_wayyiqtol_token(first_sub):
            return True
        return is_finite_verb_skel(skel(first_sub))
    if _first_vowel_is_holam(token):
        return False
    if is_wayyiqtol_token(token):
        return True
    return is_finite_verb_skel(skel(token))


def has_finite_verb(line: str) -> bool:
    """True if any token on the line is a finite-verb skeleton."""
    return any(is_finite_verb_token(t) for t in tokens(line))


# ─── prep / participle detection ────────────────────────────────────

PREP_SKELETONS = {
    "על", "אל", "מן", "לפני", "אחרי", "תחת", "בין", "בתוך", "תוך",
    "מעל", "מתחת", "עלפני", "מלפני", "מפני", "מאת", "בעד", "נגד",
    "אצל", "מאחרי", "בקרב", "בעבר", "מנגד", "סביב", "מסביב", "סביבות",
    "עם", "עד", "כמו", "מתוך", "מבין",
    # Prep + pronominal suffix common forms (Num 6:2 'אֲלֵהֶם' audit gap):
    # אֵל-suffix
    "אלי", "אליו", "אליה", "אליך", "אלינו", "אליכם", "אליכן", "אלהם", "אלהן", "אליהם", "אליהן",
    # עַל-suffix
    "עלי", "עליו", "עליה", "עליך", "עלינו", "עליכם", "עליכן", "עלהם", "עליהם", "עליהן",
    # מִן + suffix (rare; usually maqqef-bound)
    "ממני", "ממנו", "ממנה", "ממך", "ממנו", "מכם", "מהם", "מהן",
    # תַחַת-suffix
    "תחתי", "תחתיו", "תחתיה", "תחתיך", "תחתיהם",
    # לִפְנֵי-suffix
    "לפני", "לפניו", "לפניה", "לפניך", "לפנינו", "לפניכם", "לפניהם",
    # אַחֲרֵי-suffix
    "אחרי", "אחריו", "אחריה", "אחריך", "אחרינו", "אחריכם", "אחריהם",
    # בֵּין-suffix
    "ביני", "בינו", "בינה", "בינך", "בינינו", "בינהם", "בינכם",
    # עִם-suffix
    "עמי", "עמו", "עמה", "עמך", "עמנו", "עמכם", "עמהם",
    # עַד-suffix
    "עדי", "עדיו", "עדיה", "עדיך", "עדינו", "עדיכם", "עדיהם",
}

BOUND_PREP_PREFIXES = ("ב", "ל", "כ", "מ")

# Tokens starting with a bound-prep letter that are NOT prep-headed.
# Critical for maqqef-joined tokens like כִּי־טוֹב (subordinator + adj),
# כָּל־הָאָרֶץ (quantifier + NP), בֶּן־אָדָם (construct head + NP).
# Without this, the bound-prep heuristic misclassifies them as PP-headed.
NON_PREP_2CHAR_PREFIX = {"כי", "כל", "כן", "בן", "בת"}


def line_starts_with_prep(line: str) -> tuple[bool, Optional[str]]:
    """True if the first token starts with a preposition (free or bound).
    Returns (matched, prep_skeleton_or_None).
    """
    tok = first_content_token(line)
    if not tok:
        return (False, None)
    s = skel(tok)
    if s in PREP_SKELETONS:
        return (True, s)
    # bound prep: starts with ב/ל/כ/מ + at least 1 more consonant, and is
    # NOT a known finite-verb skeleton (avoids בָּרָא = qatal "create")
    if len(s) >= 2 and s[0] in BOUND_PREP_PREFIXES and not is_finite_verb_skel(s):
        return (True, s[0])
    return (False, None)


# Direct-object marker — אֵת standalone or maqqef-joined (אֶת־...)
def is_do_marker_token(token: str, tag_list: "list[str] | None" = None) -> bool:
    """True if the token IS the DO marker אֵת — standalone, maqqef-bound, or
    vav-prefixed (וְאֵת).

    Tag-driven primary path: FIRST tag's chain contains "To" (TAHOT
    direct-object-marker code). Authoritative when present — eliminates
    skel ambiguity with אַתָּה / אִתִּי / etc. that share consonants. For
    maqqef compounds (`אֶת־X`), the FIRST ortho's tag is the marker; later
    ortho-tags are the complement (Np / Nc / etc.).

    Skel-fallback distinguishes DO marker את from אַתָּה (you, ms = "אתה"
    skeleton), אִתִּי (with me = "אתי") etc.
    """
    # ── Tag-driven primary path (TAHOT oracle) ────────────────────────
    if tag_list:
        first_tag = None
        for t in tag_list:
            if t and t != "[—]":
                first_tag = t
                break
        if first_tag is not None:
            from . import morph_tags as _MT
            return "To" in _MT.morpheme_chain(first_tag)

    # ── Skel-fallback ─────────────────────────────────────────────────
    if MAQQEF in token:
        first_sub = token.split(MAQQEF, 1)[0]
        s = skel(first_sub)
    else:
        s = skel(token)
    return s == "את" or s == "ואת"


def is_bare_do_marker_token(token: str) -> bool:
    """True only if the token is the BARE DO marker אֵת/וְאֵת — no maqqef-joined
    complement. Used by stranded-DO-marker rules where the marker is on its
    own line awaiting forward-merge with its noun.
    """
    if MAQQEF in token:
        return False
    s = skel(token)
    return s == "את" or s == "ואת"


def _mem_after_vav_is_min_prep(token: str) -> bool:
    """True if token's mem (after leading vav) bears the מן-prep niqqud
    signature: hireq + dagesh on next consonant.

    Distinguishes vav-prep (וּמִן-X) from vav-noun (וּמָגוֹג, וּמָדַי, וּמֶלֶךְ).
    Required because skel-only check `s[1]=='מ'` matches both classes; the
    latter triggered S1 false-fires on NP-enumeration lines (Gen 10:2 sons-
    of-Yepheth, etc.).
    """
    t = strip_teamim(token)
    if not t.startswith("ו") or len(t) < 2:
        return False
    # Skip past vav and its niqqud/dagesh (shuruk = vav + dagesh) to reach mem
    i = 1
    while i < len(t):
        cp = ord(t[i])
        if 0x05D0 <= cp <= 0x05EA:
            break
        i += 1
    if i >= len(t) or t[i] != "מ":
        return False
    # Now check mem's niqqud + next-consonant-dagesh
    sub = t[i:]
    vowel, _, next_dagesh = _first_vowel_and_next_consonant(sub)
    return vowel == HIREQ and next_dagesh


# ─── Compound-numeral chain detection (M.num spec) ────────────────────
#
# Wave 6 audit revealed compound numeral phrases (Gen 5 / Gen 11 lifespans,
# Num 1 / Ezra 2 / 1 Chr census counts) fragmented across lines because the
# te'amim baseline imposes disjunctive accents on each numeral component.
# Per canon §1, a compound count is one atomic thought.

CARDINAL_STEMS: frozenset[str] = frozenset({
    # Units 1-10 (m/f pairs)
    "אחד", "אחת", "שנים", "שתים", "שלשה", "שלש", "ארבעה", "ארבע",
    "חמשה", "חמש", "ששה", "שש", "שבעה", "שבע", "שמנה", "תשעה", "תשע",
    "עשרה", "עשר",
    # Tens
    "עשרים", "שלשים", "ארבעים", "חמשים", "ששים", "שבעים", "שמנים", "תשעים",
    # Hundreds / thousands / ten-thousands
    "מאה", "מאות", "מאתים", "אלף", "אלפים", "אלפי", "רבבה", "רבבות",
    # Construct forms
    "חמשת", "שלשת", "ארבעת", "ששת", "שבעת", "שמנת", "תשעת", "עשרת", "מאת",
    "שני", "שתי",  # construct dual forms
})

UNIT_NOUNS: frozenset[str] = frozenset({
    # Time
    "שנה", "שנים", "שנת", "יום", "ימים", "ימי", "חדש", "חדשים", "חדשי",
    # People / census
    "איש", "אנשים", "גבר", "גברים", "נפש", "נפשות",
    # Measurement
    "אמה", "אמות", "אמת", "כר", "כרים", "כור", "סאה",
    # Military / division
    "ראש", "ראשים",
    # Valuables (weight counts)
    "כסף", "זהב", "שקל", "שקלים", "ככר", "ככרים",
})


def is_numeral_token(token: str, tag_list: "list[str] | None" = None) -> bool:
    """True if token is a cardinal numeral stem (with or without vav prefix,
    with or without maqfef-joined material). Does NOT match ordinals.

    Tag-driven primary path: HEAD tag's head-morpheme starts with "Ac"
    (TAHOT cardinal numeral code; ordinals are "Ao"). Authoritative when
    present — eliminates skel false-negatives where the cardinal isn't
    in CARDINAL_STEMS lexicon.

    Skel-fallback strips leading vav so וּמְאַת, וּשְׁלֹשִׁים, וְאַרְבָּעִים all match.
    """
    # ── Tag-driven primary path (TAHOT oracle) ────────────────────────
    if tag_list:
        head_tag = None
        for t in reversed(tag_list):
            if t and t != "[—]":
                head_tag = t
                break
        if head_tag is not None:
            from . import morph_tags as _MT
            return _MT.head_morpheme(head_tag).startswith("Ac")

    # ── Skel-fallback ─────────────────────────────────────────────────
    tok = token.split(MAQQEF, 1)[0] if MAQQEF in token else token
    s = skel(tok)
    if not s:
        return False
    if s in CARDINAL_STEMS:
        return True
    if s.startswith("ו") and s[1:] in CARDINAL_STEMS:
        return True
    return False


def is_numeral_governed_noun(token: str) -> bool:
    """True if token is a unit noun governed by a numeral (שָׁנָה, יוֹם,
    אַמָּה, אִישׁ, שֶׁקֶל, etc.). Maqfef-joined head used for check.
    """
    tok = token.split(MAQQEF, 1)[0] if MAQQEF in token else token
    return skel(tok) in UNIT_NOUNS


# Vav + bound-prep skel patterns that look like PPs but are NOT (particles,
# negations, interrogatives). Audit-driven exclusion list (Wave 6 + scanner
# false-positive sweep 2026-04-30).
VAV_BOUND_PREP_NON_PP_FALSE_POSITIVES = {
    "ולא",      # vav + negation לֹא ("and not")
    "ולכן",     # vav + adverb לָכֵן ("and therefore")
    "ולמה",     # vav + interrogative לָמָּה ("and why")
    "ולוא",     # vav + spelling variant לוֹא (older spelling of לֹא)
    "ולוּ",     # vav + לוּ ("and if/would-that") — particle
}


def is_vav_coord_pp_head(token: str, tag_list: list[str] | None = None) -> bool:
    """True if token is a vav-prefixed PP head — וְאֶל, וְעַל, וְעִם, וּבְ-NN, וּלְ-NN, וּכְ-NN, וּמְ-NN.

    Used by S1 (coordinated-PP enumeration split). A vav-coord PP head
    introduces a new coordinated-PP member in a list.

    Tag-aware path (2026-05-01): when TAHOT tags are available, the token
    must contain an `R` (preposition) marker in its morpheme chain — this
    disambiguates skel collisions like `וְאֵל`/`וְאֶל` (and-to, prep, R)
    vs. `וְאַל` (and-NOT, negation particle, Tn) which both have skel
    "ואל" but differ in tag chain. Without the tag check, S1 over-fires on
    negation+verb compounds (e.g., Obadiah 1:13 `וְאַל־תִּשְׁלַחְנָה`),
    creating an oscillation with M-class merges that re-form the line.

    Niqqud-aware mem-discrimination (2026-04-29): when prefix is mem, requires
    the מן-prep signature (hireq + dagesh-on-next-consonant) to disambiguate
    מן-prep from vav + mem-noun (proper noun, mem-prefix common noun).

    Particle-exclusion (2026-04-30 scanner audit): vav+bound-prep tokens that
    are negations/adverbs/interrogatives (וְלֹא, וְלָכֵן, וְלָמָּה) are not PP
    heads — closed-list exclusion via VAV_BOUND_PREP_NON_PP_FALSE_POSITIVES.
    """
    # Tag-aware authoritative check when available.
    if tag_list:
        from . import morph_tags as MT
        # Token may carry multiple tags (compound). Require at least one tag
        # whose morpheme chain contains R (prep). If no R anywhere → not a PP.
        has_prep = False
        for tag in tag_list:
            chain = MT.morpheme_chain(tag)
            if any(m and m[0] == "R" for m in chain):
                has_prep = True
                break
        if not has_prep:
            return False
    if MAQQEF in token:
        head = token.split(MAQQEF, 1)[0]
        s = skel(head)
        head_token = head
    else:
        s = skel(token)
        head_token = token
    if len(s) < 2 or s[0] != "ו":
        return False
    # Closed-list exclusion: vav+bound-prep+particle (not a PP)
    if s in VAV_BOUND_PREP_NON_PP_FALSE_POSITIVES:
        return False
    # vav + free prep stem (וְאֶל / וְעַל / וְעִם / וְתַחַת / ...)
    if s[1:] in PREP_SKELETONS:
        return True
    # vav + bound prep + 1+ chars (ובדגת / ובעוף / ובכל / ולכל / ...)
    if len(s) >= 3 and s[1] in BOUND_PREP_PREFIXES:
        inner = s[1:]
        if inner in QATAL_COMMON or is_finite_verb_skel(inner):
            return False
        # Mem ambiguity: only count as vav-PP if mem bears the מן-prep signature
        if s[1] == "מ" and not _mem_after_vav_is_min_prep(head_token):
            return False
        return True
    return False


def is_bare_prep_head(token: str, tag_list: list[str] | None = None) -> bool:
    """True if token starts a PP without vav-conjunction — בִדְגַת / לְ-NN / בְּ-NN / מִן /
    אֶל / עַל. Used by S1 to count the FIRST PP in an enumeration (no vav prefix).

    Tag-aware path (2026-05-01): when TAHOT tags are available, require
    morpheme chain to contain `R` (preposition). Disambiguates skel
    collisions where a bound-prep-shaped first letter is part of a non-prep
    word (e.g., negation `אַל` skel "אל" vs. preposition `אֶל` skel "אל").
    """
    if tag_list:
        from . import morph_tags as MT
        has_prep = False
        for tag in tag_list:
            chain = MT.morpheme_chain(tag)
            if any(m and m[0] == "R" for m in chain):
                has_prep = True
                break
        if not has_prep:
            return False
    if MAQQEF in token:
        head = token.split(MAQQEF, 1)[0]
        s = skel(head)
    else:
        s = skel(token)
    if not s:
        return False
    if s in PREP_SKELETONS:
        return True
    # bound prep + ≥1 char stem (not a verb)
    if len(s) >= 2 and s[0] in BOUND_PREP_PREFIXES and not is_finite_verb_skel(s):
        if s[:2] in NON_PREP_2CHAR_PREFIX:
            return False
        return True
    return False


def wayyiqtol_mid_line_split_positions(line: str) -> list[int]:
    """Return token indices in `line` where a SPLIT should be inserted before
    a mid-line wayyiqtol (a wayyiqtol token at position > 0).

    Use case: S3 — cross-clause merge on one line. A wayyiqtol always opens a
    new clause; if it appears mid-line, the prior tokens form the previous
    clause's closing material (often a closing formula like 'שָׁנָה' completing
    a year-formula, or content + 'וַיְהִי־כֵן' day-formula closer). Split
    before each non-initial wayyiqtol.

    Returns empty list if no wayyiqtol appears mid-line.
    """
    toks = tokens(line)
    if len(toks) < 2:
        return []
    positions = []
    for i, t in enumerate(toks):
        if i == 0:
            continue
        s = skel(t)
        # wayyiqtol: ו + (י|ת|א|נ) + verb stem
        if (
            len(s) >= 3
            and s[0] == "ו"
            and s[1] in YIQTOL_PREFIXES
        ):
            inner = s[1:]
            if inner in YIQTOL_KNOWN_NOUNS:
                continue  # vav+noun, not wayyiqtol
            positions.append(i)
    return positions


def coordinated_pp_split_positions(
    line: str,
    tag_lists: list[list[str]] | None = None,
) -> list[int]:
    """Return token indices in `line` where a SPLIT should be inserted to break
    a coordinated-PP enumeration into one-PP-per-line. Returns empty list if
    the line has fewer than 3 PP heads (no enumeration to split).

    Algorithm: walk tokens; tag each as PP-head (initial bare-PP) or
    vav-coord-PP-head; if total PP-heads ≥ 3, return token indices of every
    vav-coord-PP-head (split-before positions).

    When `tag_lists` is provided (per-token TAHOT tag-lists), the PP-head
    classifiers consume the tags to disambiguate skel collisions like
    `וְאַל` (and-NOT, not a PP) vs. `וְאֶל` (and-TO, PP). The skel-only
    path mistakenly counts negations + verb compounds as PP heads, producing
    spurious S1 splits and oscillation with M-class merges.
    """
    toks = tokens(line)
    if len(toks) < 4:
        return []
    pp_indices: list[int] = []
    vav_coord_indices: list[int] = []
    for i, tok in enumerate(toks):
        tl = tag_lists[i] if (tag_lists is not None and i < len(tag_lists)) else None
        if is_vav_coord_pp_head(tok, tag_list=tl):
            pp_indices.append(i)
            vav_coord_indices.append(i)
        elif is_bare_prep_head(tok, tag_list=tl):
            pp_indices.append(i)
    if len(pp_indices) < 3:
        return []
    # Filter position 0 — splitting BEFORE the first token of a line is meaningless.
    return [i for i in vav_coord_indices if i > 0]


# Vav-prefixed non-NP particles — exclusion list for is_vav_coord_np_head.
# These are common vav-conjunction + particle/negation/etc. that share the
# vav-prefix shape but are NOT NP heads.
VAV_NON_NP_PARTICLES = {
    "ולא", "וכי", "ואם", "ואך", "ואף", "וגם", "והנה", "והיה",
    "ואיך", "ואין", "ואל", "ואדם",
    # Note: "ואל" is also caught by is_vav_coord_pp_head; the explicit listing
    # here is defensive.
}


def is_vav_coord_np_head(token: str) -> bool:
    """True if token is vav + NP head (proper noun, def-art noun, construct
    head, or bare common noun). Used by S2 (coordinated-NP enumeration split).

    Conservative: relies on negative exclusion of (vav-prep, vav-DO-marker,
    vav-finite-verb, vav-non-NP-particle) plus length floor.
    """
    s = skel(token)
    if not s.startswith("ו") or len(s) < 3:
        return False
    # Exclude vav-prep (S1 territory)
    if is_vav_coord_pp_head(token):
        return False
    # Exclude vav-DO-marker (וְאֵת, with or without maqqef-joined complement)
    if s.startswith("ואת"):
        return False
    # Exclude vav-finite-verb (wayyiqtol, weqatal)
    if is_finite_verb_token(token):
        return False
    # Exclude vav-particles (closed list)
    if s in VAV_NON_NP_PARTICLES:
        return False
    return True


# ─── S3 closed-list clause-boundary helpers (atomic-thought separation) ───
#
# S3 fires only on a closed list of recognized "previous content closes;
# wayyiqtol opens fresh clause" signatures. Per canon §1: Hebrew narrative IS
# a wayyiqtol chain; default-MERGE direction means "do not split chain-internal
# wayyiqtols" (Rule H3 governs at v1→v2 layer). S3 is a line-internal fixer for
# the rare cases where v1 baseline glued a wayyiqtol onto a closing fragment.

# Pattern 1: discourse-formula closer וַיְהִי־כֵן (and-it-was-so) — Gen 1 day-formula
WAYEHI_KEN_SKELS = {"ויהיכן"}

# Pattern 2: year-formula closer + begetting/dying wayyiqtol (Gen 5, Gen 11 genealogies)
YEAR_NOUN_SKELS = {"שנה", "שנים", "שנת"}
BEGETTING_DYING_WAYYIQTOL_SKELS = {"ויולד", "וימת", "ויחי", "וימתו"}

# Pattern 3: species-formula closer לְמִינ-X (Gen 1 creation account)
# Closed list of למין + 3rd-person possessive suffix forms
SPECIES_FORMULA_SKELS = {
    "למינה", "למינו", "למינהו", "למינהם", "למיניהם",
    "למיניה", "למיניהן", "למינך",
}


def _is_wayyiqtol_skel_at(
    token: str,
    tag_list: list[str] | None = None,
) -> bool:
    """Helper: True if token is a wayyiqtol.

    When `tag_list` is provided (TAHOT tags for this orthographic word),
    uses `morph_tags.is_wayyiqtol(tag)` as the authoritative classifier —
    handles וְאֵת (and-DO-marker, "ואת") correctly as a particle, and
    וָאֶתֶּן (wayyiqtol 1cs of נתן) correctly as a verb.  Without tags,
    falls back to the skel-heuristic (more permissive; no niqqud required,
    needed for tokens like וַיְהִי-without-dagesh).
    """
    if tag_list is not None and tag_list:
        from . import morph_tags as MT  # local import to avoid cycles
        return any(MT.is_wayyiqtol(tag) for tag in tag_list)
    # Skel fallback
    if MAQQEF in token:
        s = skel(token.split(MAQQEF, 1)[0])
    else:
        s = skel(token)
    if len(s) < 4 or s[0] != "ו" or s[1] not in YIQTOL_PREFIXES:
        return False
    inner = s[1:]
    if inner in YIQTOL_KNOWN_NOUNS:
        return False
    return True


def _skel_head(token: str) -> str:
    """Skel of the first sub-token (before any maqqef). Used for closed-list
    matches that should ignore maqqef-bound suffixes."""
    if MAQQEF in token:
        return skel(token.split(MAQQEF, 1)[0])
    return skel(token)


def is_wayehi_ken_token(token: str) -> bool:
    """True if token matches the discourse formula וַיְהִי־כֵן.

    Pattern 1: the formula is a single semantic unit ("and-it-was-so") that
    closes a Gen-1-style creation-account day or directive.
    """
    # The full skel including maqfef-joined כן is "ויהיכן"
    s_full = skel(token)
    if s_full in WAYEHI_KEN_SKELS:
        return True
    # Or with sof-pasuq / paseq / other punctuation — strip and re-check
    s_stripped = "".join(c for c in s_full if 0x05D0 <= ord(c) <= 0x05EA)
    return s_stripped in WAYEHI_KEN_SKELS


def is_species_formula_token(token: str) -> bool:
    """True if token is לְמִינָהּ / לְמִינוֹ / לְמִינֵהֶם / etc. — the species-
    closure formula in Gen-1-style creation accounts.

    Pattern 3 closer: when this token immediately precedes a wayyiqtol, the
    wayyiqtol opens a new clause (and the prior content closes the species-
    list).
    """
    return _skel_head(token) in SPECIES_FORMULA_SKELS


def is_year_noun_token(token: str) -> bool:
    """True if token is שָׁנָה / שָׁנִים / שְׁנַת (year noun). Pattern 2 closer
    for genealogical sub-clauses."""
    return _skel_head(token) in YEAR_NOUN_SKELS


def is_begetting_or_dying_wayyiqtol(token: str) -> bool:
    """True if token is a wayyiqtol from the closed lexical set governing
    genealogical clause-heads: וַיּוֹלֶד, וַיָּמָת, וַיְחִי, וַיָּמֻתוּ.
    Pattern 2 opener — when paired with a year-noun closer, marks a fresh
    clause boundary."""
    return _skel_head(token) in BEGETTING_DYING_WAYYIQTOL_SKELS


def closed_list_clause_boundary_split_positions(
    line: str,
    tag_lists: list[list[str]] | None = None,
) -> list[int]:
    """S3 trigger function: return wayyiqtol token positions where the closed-
    list closer-signature criteria are met. Returns [] if no closer signature
    matches anywhere on the line.

    When `tag_lists` is provided (one tag-list per orthographic word in the
    line), the TAHOT tag drives wayyiqtol classification via
    `_is_wayyiqtol_skel_at(token, tag_list)` — distinguishes וְאֵת
    (and-DO-marker, particle) and וָאֶתֶּן (wayyiqtol 1cs) correctly.
    Without tags, falls back to skel-heuristic.

    Closed signatures (split BEFORE the wayyiqtol):
      Pattern 1: current token = וַיְהִי־כֵן (with non-verb prior content)
      Pattern 2: prior token = year noun + current token = begetting/dying wayyiqtol
      Pattern 3: prior token = species formula (לְמִינ-X) + current token = any wayyiqtol

    Empty-list-by-default is the discipline lever that prevents S3 over-firing
    on the wayyiqtol-chain narrative engine.
    """
    toks = tokens(line)
    if len(toks) < 2:
        return []
    positions: list[int] = []
    for i in range(1, len(toks)):
        cur = toks[i]
        prev = toks[i - 1]
        cur_tag_list = tag_lists[i] if tag_lists is not None and i < len(tag_lists) else None
        if not _is_wayyiqtol_skel_at(cur, cur_tag_list):
            continue
        # Pattern 1: ויהי־כן is its own atomic thought; split before it
        if is_wayehi_ken_token(cur):
            positions.append(i)
            continue
        # Pattern 3: species-formula closer + wayyiqtol opens fresh clause
        if is_species_formula_token(prev):
            positions.append(i)
            continue
        # Pattern 2: year-noun closer + begetting/dying wayyiqtol opens
        if is_year_noun_token(prev) and is_begetting_or_dying_wayyiqtol(cur):
            positions.append(i)
            continue
    return positions


def multi_wayyiqtol_clause_split_positions(
    line: str,
    tag_lists: list[list[str]] | None = None,
) -> list[int]:
    """S4 trigger function: return wayyiqtol token positions where a SPLIT
    should be inserted to separate ≥2 wayyiqtols on a single line into
    distinct clause-headed cola.

    When `tag_lists` is provided (one tag-list per orthographic word in the
    line), the TAHOT tag is the authoritative wayyiqtol classifier — the
    skel-heuristic conflates וְאֵת (and-DO-marker, "ואת") with verb forms
    because the skel starts with vav + א (a YIQTOL_PREFIX letter). Without
    tags, falls back to skel.

    Trigger: line carries ≥2 wayyiqtol verbs.
    Split point: before every wayyiqtol that is not line-initial.

    Suppressions (audit-B 2026-05-01; וַיְהִי refinement 2026-05-01):
      - וַיְהִי temporal-frame opener (REFINED): line starts with וַיְהִי. The
        SECOND wayyiqtol on the line is the main clause of the frame — that
        SPLIT POSITION is suppressed (frame + main = one ATU per FEF/H16).
        Splits BETWEEN subsequent wayyiqtols are still allowed (they are
        new coordinate clauses, not part of the frame).
        Example: Gen 29:13
          וַיְהִי כִשְׁמֹעַ לָבָן ... וַיָּרָץ לִקְרָאתוֹ וַיְחַבֶּק־לוֹ וַיְנַשֶּׁק־לוֹ
          wayy positions: [0, p_run, p_chab, p_nash]
          frame+main pair: [0, p_run] — suppressed
          splits returned: [p_chab, p_nash] — 3 cola result
      - Hendiadys / bonded sequence: ALL tokens on the line are wayyiqtols
        (e.g., וַיָּקָם וַיֵּלֶךְ — bonded action pair sharing semantic ATU).
      - Shared-DO 3-token bonded pair: line is exactly W₁ W₂ X (e.g.,
        וַיְגַלַּח וַיְחַלֵּף שִׂמְלֹתָיו — DO attaches to the second verb;
        these are bonded action pairs, not separate ATUs).

    Architectural narrowness ladder:
      - S3 closed-list (Pattern 1-3): tightest, was needed because broad
        mid-line-wayyiqtol caused RUNAWAY at pass 25 in initial S3 trial.
      - S4 (this fn): mid-tightness — count-based with explicit suppressions.
      - wayyiqtol_mid_line_split_positions (legacy): broadest, retained for
        callers that explicitly want the unrestricted form.

    Examples:
      Gen 50:1 line 3 (post-cascade):  עַל־פְּנֵי אָבִיו וַיֵּבְךְּ עָלָיו וַיִּשַּׁק־לוֹ׃
        wayyiqtol positions: [2, 4]
        non-initial split positions: [2, 4]
        result: 3 cola — [PP], [W-A + dep], [W-B + maqpef-PP]
      Gen 41:14 line:                  וַיְגַלַּח וַיְחַלֵּף שִׂמְלֹתָיו
        wayyiqtol positions: [0, 1] (3-token bonded pair)
        suppressed: shared-DO bonded-pair guard
        result: [] (no split)
    """
    toks = tokens(line)
    if len(toks) < 3:
        return []  # too short for the class

    # Find all wayyiqtols. Tag-driven primary path (handles וְאֵת = "and-DO-
    # marker" correctly as a particle, not a phantom wayyiqtol — the skel
    # path can't disambiguate "ואת" without a hard-coded exclusion).
    from . import morph_tags as MT  # local import to avoid cycles
    wayy_positions: list[int] = []
    for i, t in enumerate(toks):
        # Try tag-driven first
        if tag_lists is not None and i < len(tag_lists) and tag_lists[i]:
            if any(MT.is_wayyiqtol(tag) for tag in tag_lists[i]):
                wayy_positions.append(i)
            continue
        # Skel fallback
        s = skel(t)
        if (
            len(s) >= 3
            and s[0] == "ו"
            and s[1] in YIQTOL_PREFIXES
        ):
            inner = s[1:]
            if inner in YIQTOL_KNOWN_NOUNS:
                continue  # vav+noun, not wayyiqtol
            wayy_positions.append(i)

    if len(wayy_positions) < 2:
        return []  # need ≥2 wayyiqtols

    # Suppression: hendiadys / bonded sequence — every token is a wayyiqtol
    if len(wayy_positions) == len(toks):
        return []

    # Suppression: shared-DO 3-token bonded pair (W₁ W₂ X)
    if len(toks) == 3 and wayy_positions == [0, 1]:
        return []

    # Suppression: any wayyiqtol is BARE (no dependent before the next
    # wayyiqtol AND no maqqef-bound complement). Splitting would leave a
    # stranded bare wayyiqtol that some M-spec then re-absorbs → oscillation.
    # Examples this catches:
    #   Gen 22:3 line 4: וַיָּקָם וַיֵּלֶךְ אֶל־הַמָּקוֹם... — וַיָּקָם is bare
    #     (no token between it and וַיֵּלֶךְ, no maqqef); hendiadys pair.
    #   Gen 12:9 (and many): וַיֵּלֶךְ וַיִּסַּע — bonded movement pair.
    #
    # Counter-example NOT suppressed:
    #   Gen 50:1 line 3: ...וַיֵּבְךְּ עָלָיו וַיִּשַּׁק־לוֹ׃ — וַיֵּבְךְּ has
    #     dependent (עָלָיו); וַיִּשַּׁק־לוֹ is maqqef-bound (self-contained).
    for i, pos in enumerate(wayy_positions):
        next_wayy = wayy_positions[i + 1] if i + 1 < len(wayy_positions) else len(toks)
        dep_count = next_wayy - pos - 1
        has_maqqef_complement = MAQQEF in toks[pos]
        if dep_count == 0 and not has_maqqef_complement:
            return []

    # Default split set: before each non-initial wayyiqtol
    candidate_splits = [p for p in wayy_positions if p > 0]

    # Wayehi-frame refinement: when line starts with וַיְהִי, the second
    # wayyiqtol is the frame's main clause (per FEF/H16 — frame + main = one
    # ATU). Suppress that one split; allow splits between subsequent wayyiqtols.
    # See Gen 29:13 example in the docstring above.
    if (
        wayy_positions[0] == 0
        and skel(toks[0]) == "ויהי"
        and len(wayy_positions) >= 2
    ):
        frame_main_position = wayy_positions[1]
        candidate_splits = [p for p in candidate_splits if p != frame_main_position]

    return candidate_splits


def coordinated_np_split_positions(line: str) -> list[int]:
    """Return token indices in `line` where a SPLIT should be inserted to break
    a coordinated-NP enumeration into one-NP-per-line. Returns empty list if
    the line has fewer than 4 NP heads (no enumeration to split — the min:4
    threshold is intentionally one notch more conservative than S1's min:3 to
    dodge triadic bonded-triplet false positives like Patriarchs / heaven and
    earth).

    Algorithm: count vav-coord-NP heads. ≥3 vav-coord-NPs (= ≥4 total NP
    members including the initial governor's first NP) returns the split
    positions; below threshold returns [].
    """
    toks = tokens(line)
    if len(toks) < 4:
        return []
    vav_np_positions: list[int] = []
    for i, tok in enumerate(toks):
        if i > 0 and is_vav_coord_np_head(tok):
            vav_np_positions.append(i)
    # Need ≥3 vav-coord-NPs (= ≥4 total enumeration members)
    if len(vav_np_positions) < 3:
        return []
    return vav_np_positions


def is_bare_prep_token(token: str, tag_list: "list[str] | None" = None) -> bool:
    """True only if the token is a BARE preposition with no maqqef-joined
    complement — i.e., the prep is stranded awaiting its noun on the next line.

    Tag-driven primary path: tag chain is exactly ["R"] (free standalone prep)
    or [C/c, R] (vav-conjunction + free prep). Authoritative when present —
    eliminates skel ambiguity with אַחֲרֵי/אֵלָיו/etc. that have suffix
    morphemes the skel can't disambiguate.

    Skel-fallback: free preps (אֶל, עַל, מִן, תַּחַת, ...) and vav-prefixed
    forms (וְאֶל, וְעַל, ...) when standing alone (no maqqef).
    """
    if MAQQEF in token:
        return False

    # ── Tag-driven primary path (TAHOT oracle) ────────────────────────
    if tag_list:
        head_tag = None
        for t in tag_list:
            if t and t != "[—]":
                head_tag = t
                break
        if head_tag is not None:
            from . import morph_tags as _MT
            chain = _MT.morpheme_chain(head_tag)
            if chain == ["R"]:
                return True
            if len(chain) == 2 and chain[0] in ("C", "c") and chain[1] == "R":
                return True
            return False

    # ── Skel-fallback ─────────────────────────────────────────────────
    s = skel(token)
    if s in PREP_SKELETONS:
        return True
    # vav-prefixed free prep: וְאֶל, וְעַל, וְעִם, ...
    if len(s) >= 3 and s[0] == "ו" and s[1:] in PREP_SKELETONS:
        return True
    return False


# Definite adjective — article-marked single-word adjective (heuristic).
# Common patterns: הַגָּדוֹל, הַגְּדוֹלָה, הַגְּדֹלִים, הַגְּדֹלוֹת.
# Conservative: requires single-token, ה- prefix, no further structure markers.
COMMON_ADJ_STEMS = {
    "גדול", "גדל", "קטן", "קטון", "טוב", "רע", "רב", "מעט", "חדש", "ישן",
    "זקן", "צעיר", "חכם", "סכל", "כסיל", "צדיק", "רשע", "ישר", "תמים",
    "קדוש", "טהור", "טמא", "חזק", "חלש", "אמת", "שקר", "נורא", "יקר",
    "קשה", "קל", "ארך", "קצר", "רחב", "צר", "עמק", "גבה", "נמוך", "שלם",
    "ראשון", "אחרון", "אחר", "שני", "שלישי", "אחד", "מלא", "ריק", "חי", "מת",
    "כבד", "ברוך", "ארור", "פלאי",
}

ADJ_PLURAL_SUFFIXES = ("ים", "ות", "ה")


# Construct-head skeletons — high-frequency words that commonly head a
# construct chain. When such a word ends a line and the nomen rectum is on
# the next line, h16_c fires (Layer-1 stranding violation).
#
# IMPORTANT: list bare skeletons only — vav/bound-prep prefixes are stripped
# algorithmically by is_construct_head_token, so DON'T enumerate prefix variants.
CONSTRUCT_HEAD_SKELETONS = {
    # Plural masc construct (-ei suffix)
    "יושבי", "אנשי", "בני", "ימי", "שני", "אבי", "אחי", "מלכי", "זקני",
    "שרי", "ראשי", "אלוני", "אילני", "מפריסי", "מעלי", "פני",
    "דברי", "מצוי", "חקי", "פקודי", "משפטי", "עדותי", "אהבי",
    "הררי", "מימי", "מעיני", "תהומות", "ערי",
    # Plural fem construct (-ot suffix, e.g. מִצְוֹת construct of plural מצוות)
    "מצות", "תורות", "חקות", "עדות", "ברכות", "מצוותי", "אבותי",
    # Singular fem construct (-t suffix)
    "חמת", "אשת", "בת", "מלכת", "תורת", "עדת", "פחת", "פחות",
    "מלכות", "מקצה", "תחלת", "ראשית", "אחרית",
    "פתח",     # opening of (recurs Lev-Num as 'פתח אהל מועד')
    # Singular masc construct (often = absolute)
    "כל", "בית", "אהל", "יד", "פי", "שם", "דבר", "מקום", "הר", "עם",
    "גוי", "שדה", "יום", "ראש", "ארון", "מצוה", "רוח", "ארץ", "עיר",
    "בן", "אב", "אח", "מלך", "נשיא", "נגיד", "אדון", "אביר", "אלון",
    "אלוה", "כבוד", "פני",
    # Quantifier-construct
    "שני", "שתי", "שלשת", "שלש", "ארבעת", "ארבע", "חמשת", "חמש",
    "ששת", "שש", "שבעת", "שבע", "שמנת", "שמנה", "תשעת", "תשע",
    "עשרת", "עשר",
}

BOUND_PREP_STRIPS = ("ב", "ל", "כ", "מ")  # bound preps only — article ה REMOVED 2026-04-30
# (per Design L diagnosis: stripping ה caused הָאָרֶץ/הָעָם/הַמֶּלֶךְ to test True
# as construct heads. A definite noun cannot be in construct state — basic Hebrew
# grammar; that combination indicates the chain is closed within the token. 186
# of 559 h16_c misses traced to this bug.)


def is_construct_head_token(token: str, tag_list: "list[str] | None" = None) -> bool:
    """True if token is a construct-state head.

    Tag-driven primary path: if `tag_list` is provided (per-ortho TAHOT morph
    tags for this prosodic-word token), the LAST tag's head morpheme is the
    authoritative classifier — TAHOT `Nc[mfb][sdpd]c` (state letter at index 4
    is `c`) marks construct state. This eliminates the systematic FN class
    where construct nouns absent from CONSTRUCT_HEAD_SKELETONS lexicon
    (אלהי, תחת, אין, נאם, מזוזת, etc.) get missed entirely. See
    `scripts/audit_morphology_vs_tahot.py` (2026-05-01 audit) for the
    14K FN class this addresses corpus-wide.

    Skel-fallback (legacy path, used when no tag is supplied):

    Strategy:
      1. Get skeleton; for maqqef compounds, check the LAST sub-token (the
         rightmost element is the awaiting-rectum head, e.g. אֶת־מִצְוֹת = DO+head;
         a closed chain like מִצְוַת־יְהוָה would have יהוה as last → not a head).
      2. Try direct match against CONSTRUCT_HEAD_SKELETONS.
      3. Strip leading vav, retry.
      4. Strip leading bound-prep / article, retry.
      5. Strip leading vav + bound-prep / article, retry.

    This generalization catches בְּבֵית, מִבֵּית, וּבְבֵית, וְאַנְשֵׁי, אֶת־מִצְוֹת, etc.
    without requiring every prefix variant in the closed list.
    """
    # ── Tag-driven primary path (TAHOT oracle) ────────────────────────
    if tag_list:
        head_tag = None
        for t in reversed(tag_list):
            if t and t != "[—]":
                head_tag = t
                break
        if head_tag is not None:
            from . import morph_tags as _MT
            return _MT.is_construct_state(head_tag)

    # ── Skel-fallback (when no tag available) ─────────────────────────
    if MAQQEF in token:
        # Check the LAST sub-token (rightmost = awaiting-rectum head if construct-shaped)
        last = token.rsplit(MAQQEF, 1)[-1]
        s = skel(last)
    else:
        s = skel(token)
    if not s:
        return False
    if s in CONSTRUCT_HEAD_SKELETONS:
        return True
    # Strip leading vav
    if len(s) >= 2 and s[0] == "ו":
        if s[1:] in CONSTRUCT_HEAD_SKELETONS:
            return True
        # Strip vav + bound-prep / article
        if len(s) >= 3 and s[1] in BOUND_PREP_STRIPS and s[2:] in CONSTRUCT_HEAD_SKELETONS:
            return True
    # Strip leading bound-prep / article
    if len(s) >= 2 and s[0] in BOUND_PREP_STRIPS and s[1:] in CONSTRUCT_HEAD_SKELETONS:
        return True
    return False


def is_bare_noun_token(token: str) -> bool:
    """True if token is a noun-like content word (NP head / proper noun /
    pronoun / common noun) — NOT a verb, prep, DO marker, particle, or
    conjunction-only token.

    Used by m2_verb_bare_np_rebond to detect stranded bare-NP direct objects
    or postposed subjects after a verb-line. Excludes tokens already covered
    by other merge specs (PP head → S1/h-rules; vav-coord NP → S2 territory).
    """
    if not token:
        return False
    s = skel(token)
    if not s:
        return False
    if is_finite_verb_token(token):
        return False
    if is_do_marker_token(token):
        return False
    # Direct prep / vav-prep / bound-prep
    if s in PREP_SKELETONS:
        return False
    if len(s) >= 3 and s[0] == "ו" and s[1:] in PREP_SKELETONS:
        return False
    if is_bare_prep_token(token):
        return False
    if is_vav_coord_pp_head(token):
        return False
    if is_vav_coord_np_head(token):
        return False  # let S2-direction guards handle these
    # Particles / discourse markers
    if s in DISCOURSE_PARTICLES:
        return False
    if s in VOCATIVE_PARTICLES:
        return False
    # Bound-prep + content (e.g. בְּעִיר) — not a bare noun
    if len(s) >= 2 and s[0] in BOUND_PREP_PREFIXES and not is_finite_verb_skel(s):
        if s[:2] not in NON_PREP_2CHAR_PREFIX:
            return False
    return True


def is_definite_adjective_token(token: str, tag_list: "list[str] | None" = None) -> bool:
    """True if token is article-marked + adjective stem.

    Tag-driven primary path: HEAD tag's chain has "Td" (definite article)
    morpheme AND head morpheme starts with "A" (adjective). Authoritative
    when present — captures every TAHOT-classified definite adjective,
    not just those whose stem appears in COMMON_ADJ_STEMS lexicon.

    Skel-fallback: pattern ה + (adjective stem) [+ plural/feminine suffix].
    Article-prefix distinguishes attributive from predicative position;
    stem-list keeps the heuristic conservative.
    """
    # ── Tag-driven primary path (TAHOT oracle) ────────────────────────
    if tag_list:
        head_tag = None
        for t in reversed(tag_list):
            if t and t != "[—]":
                head_tag = t
                break
        if head_tag is not None:
            from . import morph_tags as _MT
            chain = _MT.morpheme_chain(head_tag)
            if chain:
                head_morph = chain[-1]
                # Head is adjective (A...) AND chain has Td (def article) prefix
                if head_morph.startswith("A") and any(m == "Td" for m in chain[:-1]):
                    return True
            return False

    # ── Skel-fallback ─────────────────────────────────────────────────
    s = skel(token)
    if not s.startswith("ה") or len(s) < 4:
        return False
    rest = s[1:]
    # Try exact match against adj stems
    if rest in COMMON_ADJ_STEMS:
        return True
    # Try stripping plural/feminine suffix
    for suffix in ADJ_PLURAL_SUFFIXES:
        if rest.endswith(suffix) and rest[:-len(suffix)] in COMMON_ADJ_STEMS:
            return True
    return False


def line_starts_with_le_infinitive(line: str) -> bool:
    """True if first token is לְ + infinitive-construct.

    Heuristic: ל + 3-letter root in infinitive-construct pattern.
    Conservative; misses some.
    """
    tok = first_content_token(line)
    if not tok:
        return False
    s = skel(tok)
    if not s.startswith("ל") or len(s) < 4:
        return False
    # rough infinitive-construct pattern: ל + 3 root consonants
    # avoids ל + noun (which would be ל + article-marked, e.g., לַ + noun)
    rest = s[1:]
    # if rest is exactly 3 consonants, likely infinitive-construct
    if len(rest) in (3, 4) and not rest.startswith("ה"):  # not ל + article
        return True
    return False


# Participle morphology: m-prefix derived stems + qal active/passive patterns.
# Heuristic relies on niqqud where preserved; falls back to consonant-prefix patterns.

M_PREFIX_PARTICIPLE_RE = re.compile(r"^(מ[ְַָֻֻ]?)")  # mem prefix with vowel
QAL_ACTIVE_PARTICIPLE_RE = re.compile(r"^[א-ת][וֹ][א-ת][ֵֶ][א-ת]")  # CoCeC pattern

# Closed-list mem-prefix tokens that are NOT participles (nouns, particles)
M_PREFIX_NON_PARTICIPLE = {
    "מה", "מי", "מן", "מתי", "מאד", "מאז", "מבית", "מחוץ",
    "מעם", "מאת", "מצרים", "מואב", "משה", "מלך", "מקום", "מדבר",
    "מים", "מים", "מעי", "מעיים", "מאד", "מלאך", "מצוה", "מעל",
    # מן-prep + adjective (1 Sam 5:9 audited 2026-04-29):
    "מקטן", "מגדול", "מטף", "מזקן", "מקצה",
}


def line_starts_with_participle(line: str) -> bool:
    """True if first content token bears participial morphology (any binyan).

    2026-04-29 rewrite: delegates to niqqud-aware is_mem_prefix_participle for
    the mem-prefix branch (was crude `len ≥ 4 + starts-with-mem + not-verb`,
    which whack-a-moled). M_PREFIX_NON_PARTICIPLE retained as fail-soft fallback
    for unpointed/partial-niqqud edge cases.
    """
    tok = first_content_token(line)
    if not tok:
        return False
    s = skel(tok)
    if s in M_PREFIX_NON_PARTICIPLE:
        return False
    # mem-prefix: niqqud-aware classification
    if s.startswith("מ"):
        if is_mem_prefix_participle(tok):
            return True
        # else fall through (could still be qal-active by holam — but unusual
        # for mem-prefix; the next check handles non-mem qal active anyway)
    # qal active CoCeC — niqqud-aware check; te'amim stripped, vowels preserved
    if QAL_ACTIVE_PARTICIPLE_RE.match(strip_teamim(tok)):
        return True
    return False


def line_ends_in_np(line: str) -> bool:
    """True if the last content token is an NP head (not a finite verb,
    not a particle, not a bare prep).
    """
    tok = last_content_token(line)
    if not tok:
        return False
    s = skel(tok)
    if not s:
        return False
    if is_finite_verb_skel(s):
        return False
    if s in PREP_SKELETONS:
        return False
    # closed-class non-NP enders
    NON_NP_ENDERS = {"לא", "אל", "כי", "אם", "פן", "אך", "רק", "גם", "אף", "הן", "הנה"}
    if s in NON_NP_ENDERS:
        return False
    return True


# ─── guard helpers ──────────────────────────────────────────────────

DISCOURSE_PARTICLES = {"הנה", "אף", "עלכן", "לכן", "ועתה", "אז", "עתה", "גם", "רק", "אכן"}

VOCATIVE_PARTICLES = {"הוי", "אוי", "אהה", "אנא"}

# Clause-completing adverbial / temporal particles. Distinct from
# DISCOURSE_PARTICLES (which are sentence-introducing/topic-shifting):
# these particles attach BACKWARD, completing the predication on line N.
# Audit 2026-05-01 D4 Class G: e.g., 1 Sam 1:18 "וּפָנֶיהָ לֹא־הָיוּ־לָהּ" / "עוֹד".
# Closed list — high-precision detection.
ADVERBIAL_PARTICLES = {
    "עוד",       # still / anymore / again
    "שם",        # there (locative)
    "שמה",       # thither (directional)
    "מאד",       # very / exceedingly
    "יחדו",      # together
    "יחד",       # together (alt form)
    "תמיד",      # always / continually
    "אחר",       # afterward
    "ככה",       # thus / so
    "כן",        # so / thus (adverbial — distinguish from כן "yes" particle context)
    "פה",        # here
    "פתאם",      # suddenly
    "מהר",       # quickly
    "חנם",       # for nothing / in vain
    "טרם",       # not yet / before (adverbial form, not the conjunctive)
    "ריקם",      # empty-handed
    "אמנם",      # indeed / truly
}


def line_starts_with_discourse_particle(line: str) -> bool:
    tok = first_content_token(line)
    if not tok:
        return False
    return skel(tok) in DISCOURSE_PARTICLES


def is_vocative_line(line: str) -> bool:
    """True if the line is a vocative unit (address particle + NP, or bare vocative)."""
    tok = first_content_token(line)
    if not tok:
        return False
    if skel(tok) in VOCATIVE_PARTICLES:
        return True
    return False


# Resumptive pronoun heuristic: 3rd-person pronominal suffixes that signal
# casus-pendens resumption. Look at line AFTER the candidate pair.
RESUMPTIVE_SUFFIX_RE = re.compile(r"(הו|הם|הן)$")


def line_has_resumptive_suffix(line: str) -> bool:
    for tok in tokens(line):
        s = skel(tok)
        if RESUMPTIVE_SUFFIX_RE.search(s):
            return True
    return False


# Heavy subject heuristic: relative pronoun or ≥2 appositives or deep construct
RELATIVE_MARKERS = {"אשר", "ש"}


def is_heavy_subject(line: str) -> bool:
    """True if the line's NP is heavy: contains relative pronoun, multiple
    appositives, or deep construct chain.
    """
    line_tokens = [skel(t) for t in tokens(line)]
    if not line_tokens:
        return False
    if any(t in RELATIVE_MARKERS for t in line_tokens):
        return True
    # ≥2 appositive nouns starting with בן/בת
    appositives = sum(1 for t in line_tokens if t.startswith(("בן", "בת")))
    if appositives >= 2:
        return True
    return False


def is_heavy_participial_complement(line: str) -> bool:
    """True if next-line participle has both DO (אֵת) and PP, ≥5 words combined."""
    line_tokens = [skel(t) for t in tokens(line)]
    if len(line_tokens) < 5:
        return False
    has_et = "את" in line_tokens
    has_prep = any(t in PREP_SKELETONS or (len(t) >= 2 and t[0] in BOUND_PREP_PREFIXES)
                   for t in line_tokens[1:])  # skip first token (the participle itself)
    return has_et and has_prep


# ─── H18.3 / M2: verb + obligatory PP-complement ────────────────────

# Finite-verb skeletons that govern an obligatory PP-complement
# (H18.3 / M2 corpus extension). Maps bare consonant skeleton →
# tuple of allowed preposition skeletons for the complement.
# Conservative closed list: only high-confidence cases included.
# Ported from validate_clause_nucleus_split.py M2_PP_VERBS.
# Audit basis: 9/9 TP rate corpus-wide — meets canon §7.4 ≥80% threshold.
M2_PP_VERB_SKELETONS: dict[str, tuple[str, ...]] = {
    # שָׁמַע ל / אֶל
    "שמע":     ("ל", "אל"),
    "שמעו":    ("ל", "אל"),
    "ישמע":    ("ל", "אל"),
    "וישמע":   ("ל", "אל"),
    # נָשָׂא ... אֶל (raise eyes/voice to)
    "נשא":     ("אל",),
    "נשאו":    ("אל",),
    "וישא":    ("אל",),
    "ישא":     ("אל",),
    # פָּנָה אֶל
    "פנה":     ("אל",),
    "פנו":     ("אל",),
    "ויפן":    ("אל",),
    # קָרָא אֶל / ל
    "קרא":     ("אל", "ל"),
    "קראו":    ("אל", "ל"),
    "ויקרא":   ("אל", "ל"),
    # זָעַק אֶל
    "זעק":     ("אל",),
    "זעקו":    ("אל",),
    "ויזעק":   ("אל",),
    # פָּלַל / הִתְפַּלֵּל אֶל
    "התפלל":   ("אל",),
    "ויתפלל":  ("אל",),
}


def is_m2_pp_verb_token(token: str) -> bool:
    """True if token is a verb from the M2_PP_VERB_SKELETONS closed list.

    Used by the spec-runner _check_morphology('m2_pp_verb') hook to test
    the last token of line N in the H18.3 trigger.
    """
    return skel(token) in M2_PP_VERB_SKELETONS


def m2_pp_verb_allowed_preps(token: str) -> tuple[str, ...]:
    """Return allowed prep skeletons for the given M2 verb token, or empty tuple."""
    return M2_PP_VERB_SKELETONS.get(skel(token), ())


# ─── M2.7: motion-locus verbs taking obligatory locus PP ───────────
#
# Distinct from M2_PP_VERB_SKELETONS (speech verbs taking RECIPIENT PP).
# These are MOTION/POSITION verbs whose meaning requires a LOCUS PP
# (you can't "fall" without specifying where; you can't "be placed"
# without specifying where). Conservative closed list — start with
# נָפַל wayyiqtol forms only (Gen 50:1 prototype). Expand iteratively
# after cascade-FP audit.
#
# Critical distinction from "optional locative" verbs (ישב / עמד / הלך):
# the verb here is INCOMPLETE without the PP, not just enriched by it.
# Audit basis: prototype Gen 50:1 (וַיִּפֹּל יוֹסֵף + עַל־פְּנֵי). Sweep TBD.
MOTION_LOCUS_VERB_SKELETONS: dict[str, tuple[str, ...]] = {
    # נָפַל + עַל / אֶל (fall onto / fall toward — obligatory locus)
    "ויפל":    ("על", "אל"),
    "ויפלו":   ("על", "אל"),
    "תפל":     ("על", "אל"),
    "תפלי":    ("על", "אל"),
    "נפל":     ("על", "אל"),
    "נפלו":    ("על", "אל"),
    "נפלה":    ("על", "אל"),
    # Future expansion candidates (not yet activated — need FP audit):
    #   נָתַן + עַל / ב / לפני (place onto)
    #   שָׂם / יָשֶׂם + עַל / ב / לפני (place upon)
    #   בּוֹא + אֶל (when transitive arrival; intransitive "come" is too broad)
}


def is_motion_locus_verb_token(token: str, tag_list: list[str] | None = None) -> bool:
    """True if token is a motion-locus verb requiring obligatory PP-complement
    of LOCATION (as distinct from speech-verbs taking recipient PP, which is
    the M2_PP_VERB_SKELETONS class).

    Used by spec-runner _check_morphology('motion_locus_verb') hook to gate
    the m2_7 motion-verb-locus-PP merge spec.
    """
    return skel(token) in MOTION_LOCUS_VERB_SKELETONS


def motion_locus_verb_allowed_preps(token: str) -> tuple[str, ...]:
    """Return allowed locus-prep skeletons for the given motion verb, or empty tuple."""
    return MOTION_LOCUS_VERB_SKELETONS.get(skel(token), ())


# ─── M5.b: temporal-frame opener (bound-prep + temporal-noun, OR temporal connective) ─
#
# A bare temporal frame (grammatically incomplete: no finite verb anywhere
# on the line) is the first half of an atomic thought unit. Its main verb
# completes the thought on the next line. Per Stan 2026-05-01: "as the ATU
# concept came into focus, it also became clear these actually COULDN'T be
# split" — frame and main clause are indivisible regardless of length.
#
# Sibling concept: m5_bare_wayehi_attached covers single-token bare ויהי.
# This covers MULTI-token bare temporal frames without ויהי.
#
# Closed lexicons start tight; expand iteratively after FP audit.

# Temporal-noun skels — must be paired with a bound-prep prefix to qualify.
TEMPORAL_NOUN_SKELS: frozenset[str] = frozenset({
    "יום", "ימים", "יומים", "יומם",
    "חדש", "חדשים", "חדשי",
    "שנה", "שנת", "שנים", "שני",
    "שבת", "שבתות", "שבתון",
    "מועד", "מועדים", "מועדי",
    "בקר", "בקרים",
    "ערב", "ערבים", "ערבית",
    "לילה", "ליל", "לילות",
    "צהרים",
    "עת", "עתים", "עתות", "עתי",
    "חצות", "חצי",  # midnight / half (temporal use)
})

# Standalone temporal connectives (already include their own preposition or
# function as time-clause openers). Closed list — exclude ambiguous tokens
# like כי (also "because", "that") and עד (also locative).
TEMPORAL_CONNECTIVE_SKELS: frozenset[str] = frozenset({
    "אחרי", "אחר", "אחריכן", "אחרכן",
    "טרם", "בטרם",
    "מקץ", "מקצה",
    "כאשר",
    "לפנות",  # "toward [the time of]"
    "בעוד",   # "while still"
    "מאז",    # "since"
})

# Bound-prep prefixes that combine with a temporal noun to form a temporal frame.
# Single-character; appear as the first consonant of the skeleton.
TEMPORAL_BOUND_PREPS: frozenset[str] = frozenset({"ב", "כ", "מ", "ל"})


def is_temporal_frame_opener_token(
    token: str,
    tag_list: list[str] | None = None,
) -> bool:
    """True if token is a bound-prep + temporal-noun (e.g., בַּחֹדֶשׁ, בַּיּוֹם, מִקֵּץ)
    OR a standalone temporal connective (אַחֲרֵי, כַּאֲשֶׁר, etc.).

    Used by spec-runner _check_morphology('temporal_frame_opener') to gate
    the m5_b temporal-frame-attached merge spec.

    Tag-aware path (when available): when the TAHOT tag head is `N*` (noun)
    AND the morpheme chain contains an `R` (preposition) marker, the skel
    after stripping the bound-prep prefix is checked against the closed
    temporal-noun lexicon. The tag distinguishes a true bound-prep+noun
    pattern from look-alikes (e.g., a verb form whose skel happens to start
    with vav+letter that resembles a bound-prep).
    """
    # Maqqef-bound: only inspect the head sub-token (the prep+noun half).
    if MAQQEF in token:
        s = skel(token.split(MAQQEF, 1)[0])
    else:
        s = skel(token)

    # Standalone temporal connective (skel match — these are unambiguous).
    if s in TEMPORAL_CONNECTIVE_SKELS:
        return True

    # Bound-prep + temporal-noun shape
    if len(s) >= 2 and s[0] in TEMPORAL_BOUND_PREPS:
        inner = s[1:]
        if inner in TEMPORAL_NOUN_SKELS:
            # Tag-aware confirmation when available: head should be a noun.
            # When tags absent, accept the skel pattern (the closed noun
            # lexicon makes this safe — "חדש" / "יום" are not verbs).
            if tag_list:
                from . import morph_tags as MT
                head = MT.head_morpheme(tag_list[0]) if tag_list[0] else ""
                if head and head[0] != "N":
                    return False
            return True

    return False
