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


def is_finite_verb_token(token: str) -> bool:
    """True if the token (raw, with niqqud/te'amim) parses as a finite verb.

    Niqqud-aware participle exclusion: holam after first consonant marks the
    qal active participle (or qal infinitive construct), neither finite —
    rules out עֹשֶׂה, רֹמֵשׂ, יֹשֵׁב, etc. that share skel with their qatal cousins.

    Maqqef-joined compounds: check only the first sub-token. The skel() of a
    full compound like אֶת־כָּל־יֶרֶק collapses to "אתכלירק" which spuriously
    matches the YIQTOL-prefix heuristic via the leading א. Splitting at maqqef
    isolates the head morpheme (here the DO marker את) so the check sees only
    "את", which correctly fails the prefix-verb test (length-2).
    """
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
def is_do_marker_token(token: str) -> bool:
    """True if the token IS the DO marker אֵת — standalone, maqqef-bound, or
    vav-prefixed (וְאֵת).

    Distinguishes DO marker את from אַתָּה (you, ms = "אתה" skeleton),
    אִתִּי (with me = "אתי") etc., which would all start with the same
    consonants but skel as longer strings.
    """
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


def is_numeral_token(token: str) -> bool:
    """True if token is a cardinal numeral stem (with or without vav prefix,
    with or without maqfef-joined material). Strips leading vav so וּמְאַת,
    וּשְׁלֹשִׁים, וְאַרְבָּעִים all match. Does NOT match ordinals.
    """
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


def is_vav_coord_pp_head(token: str) -> bool:
    """True if token is a vav-prefixed PP head — וְאֶל, וְעַל, וְעִם, וּבְ-NN, וּלְ-NN, וּכְ-NN, וּמְ-NN.

    Used by S1 (coordinated-PP enumeration split). A vav-coord PP head
    introduces a new coordinated-PP member in a list.

    Niqqud-aware mem-discrimination (2026-04-29): when prefix is mem, requires
    the מן-prep signature (hireq + dagesh-on-next-consonant) to disambiguate
    מן-prep from vav + mem-noun (proper noun, mem-prefix common noun).
    """
    if MAQQEF in token:
        head = token.split(MAQQEF, 1)[0]
        s = skel(head)
        head_token = head
    else:
        s = skel(token)
        head_token = token
    if len(s) < 2 or s[0] != "ו":
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


def is_bare_prep_head(token: str) -> bool:
    """True if token starts a PP without vav-conjunction — בִדְגַת / לְ-NN / בְּ-NN / מִן /
    אֶל / עַל. Used by S1 to count the FIRST PP in an enumeration (no vav prefix).
    """
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


def coordinated_pp_split_positions(line: str) -> list[int]:
    """Return token indices in `line` where a SPLIT should be inserted to break
    a coordinated-PP enumeration into one-PP-per-line. Returns empty list if
    the line has fewer than 3 PP heads (no enumeration to split).

    Algorithm: walk tokens; tag each as PP-head (initial bare-PP) or
    vav-coord-PP-head; if total PP-heads ≥ 3, return token indices of every
    vav-coord-PP-head (split-before positions).
    """
    toks = tokens(line)
    if len(toks) < 4:
        return []
    pp_indices: list[int] = []
    vav_coord_indices: list[int] = []
    for i, tok in enumerate(toks):
        if is_vav_coord_pp_head(tok):
            pp_indices.append(i)
            vav_coord_indices.append(i)
        elif is_bare_prep_head(tok):
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


def _is_wayyiqtol_skel_at(token: str) -> bool:
    """Helper: True if token's skel matches the wayyiqtol consonant pattern.
    More permissive than is_wayyiqtol_token (no niqqud requirement) since S3
    needs to detect wayyiqtol presence on tokens like וַיְהִי-without-dagesh.
    """
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


def closed_list_clause_boundary_split_positions(line: str) -> list[int]:
    """S3 trigger function: return wayyiqtol token positions where the closed-
    list closer-signature criteria are met. Returns [] if no closer signature
    matches anywhere on the line.

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
        if not _is_wayyiqtol_skel_at(cur):
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


def is_bare_prep_token(token: str) -> bool:
    """True only if the token is a BARE preposition with no maqqef-joined
    complement — i.e., the prep is stranded awaiting its noun on the next line.

    Free preps (אֶל, עַל, מִן, תַּחַת, ...) and vav-prefixed forms (וְאֶל, וְעַל, ...)
    when standing alone (no maqqef) are stranded — line-final or line-only
    occurrences indicate a complement that belongs on the merged line.
    """
    if MAQQEF in token:
        return False
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

BOUND_PREP_STRIPS = ("ב", "ל", "כ", "מ", "ה")  # bound preps + article


def is_construct_head_token(token: str) -> bool:
    """True if token is a construct-state head (algorithmic strip + closed list).

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


def is_definite_adjective_token(token: str) -> bool:
    """True if token is article-marked + adjective stem.

    Pattern: ה + (adjective stem) [+ plural/feminine suffix]. Article-prefix
    distinguishes attributive from predicative position; stem-list keeps the
    heuristic conservative.
    """
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
