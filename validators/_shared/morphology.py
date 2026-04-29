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
    "ידע", "ראה", "שמע", "זכר", "חשב", "הבין",
    # motion
    "הלך", "בא", "באה", "יצא", "שב", "קם", "ירד", "עלה", "פנה", "סר",
    # perception
    "פתח", "סגר", "מצא",
    # action
    "נתן", "לקח", "שלח", "השליך", "הביא", "הוציא", "כתב", "כרת", "ספר",
    # state
    "ישב", "עמד", "שכב", "נח", "מת", "חי",
    # transactional
    "מכר", "קנה", "בנה", "הרס",
    # blessing/cursing
    "ברך", "ארר", "הקדיש", "טמא",
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
    # wayyiqtol prefix — וי / וַי / וְ + yiqtol
    if skeleton.startswith("וי") and len(skeleton) >= 3:
        # "וי" + at least one more consonant
        return True
    # yiqtol — single-prefix + 3-letter root skeleton
    # Pattern: prefix (י/ת/א/נ) + root consonants ≥ 3 total chars
    # Guards against common false positives:
    #   - nouns starting with י: יד, ים, יום, ין — excluded by known-noun list
    #   - prepositions starting with ת: — rare false positive, accept
    # This detects תהיו (2mp yiqtol), ישטמנו (3ms + suffix), etc.
    YIQTOL_KNOWN_NOUNS = {
        # י-initial nouns
        "יד", "ים", "יום", "ין", "יין", "יין", "יער", "יען",
        "ירא", "ירה",  # fear/shoot (can be noun in some forms)
        # א-initial common nouns (not verbs)
        "אדני", "אדנינו", "אדניך", "אדניכם", "אדניהם",
        "אחי", "אחיו", "אחיך", "אחינו", "אחיכם",
        "אנחנו", "אנכי", "אני",
        "ארצי", "ארצנו", "ארצו", "ארצם",
        # ת-initial nouns
        "תורה", "תפלה", "תבל", "תנין",
        "תורת", "תורתו", "תורתך",
    }
    if len(skeleton) >= 3 and skeleton[0] in YIQTOL_PREFIXES:
        # Exclude only the 2-char existential יש (skeleton = "יש")
        if skeleton not in YIQTOL_KNOWN_NOUNS and skeleton != "יש":
            # Rough heuristic: accept if it's ≥ 4 chars (prefix + 3-root)
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
        return is_finite_verb_skel(skel(first_sub))
    if _first_vowel_is_holam(token):
        return False
    return is_finite_verb_skel(skel(token))


def has_finite_verb(line: str) -> bool:
    """True if any token on the line is a finite-verb skeleton."""
    return any(is_finite_verb_token(t) for t in tokens(line))


# ─── prep / participle detection ────────────────────────────────────

PREP_SKELETONS = {
    "על", "אל", "מן", "לפני", "אחרי", "תחת", "בין", "בתוך",
    "מעל", "מתחת", "עלפני", "מלפני", "מפני", "מאת", "בעד", "נגד",
    "אצל", "מאחרי", "בקרב", "בעבר", "מנגד", "סביב", "מסביב",
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
}


def line_starts_with_participle(line: str) -> bool:
    """True if first content token bears participial morphology (any binyan)."""
    tok = first_content_token(line)
    if not tok:
        return False
    s = skel(tok)
    if s in M_PREFIX_NON_PARTICIPLE:
        return False
    # m-prefix derived stems
    if s.startswith("מ") and len(s) >= 4 and not is_finite_verb_skel(s):
        return True
    # qal active CoCeC — needs niqqud-aware check
    if QAL_ACTIVE_PARTICIPLE_RE.match(tok):
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
