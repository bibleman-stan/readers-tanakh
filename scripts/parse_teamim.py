"""
parse_teamim.py - Te'amim-driven baseline cola generator (starting draft for v2/he editorial).

Reads v0-prose Hebrew + v0-eng-baseline English + v0-translit-baseline
translit in lockstep. Splits at te'amim cola boundaries derived from the
Hebrew accents. Emits four parallel v1 chapter files per book as a starting
draft for editorial refinement:

  v1-he-baseline/       Hebrew cola (one cola per line; prosodic-words
                        space-separated; orthographic-word boundaries within
                        a prosodic word are signaled by inline maqqef ־)
  v1-eng-interlinear/   Per-orthographic-word English (` | ` separator,
                        brackets KEPT, no naturalize)
  v1-eng-gloss/         Smooth naturalized English (one cola per line, normal
                        text; brackets stripped, possessives/demonstratives
                        reordered, Hebrew adjective-after-noun inverted,
                        compound prepositions collapsed, directional ה
                        prefixed with "toward")
  v1-translit/          Per-orthographic-word translit (` | ` separator,
                        modern Israeli style)

METHODOLOGICAL NOTE: The te'amim (cantillation accents) are EVIDENCE of the
Masoretic tradition's structural understanding, not authority for line-break
decisions. v1-he-baseline is the editor's starting draft (seeded by te'amim
parsing); v2/he (editorial) freely adds, removes, or merges line breaks relative
to this baseline per the colometry canon's atomic-thought and Hebrew-syntax criteria.
See private/01-method/colometry-canon.md §1 "The Te'amim Are Not a Structural
Prior" and Rule H8 "Te'amim as Evidence" for canonical framing.

Two accent systems: prose (21 books) and Sifrei Emet (Pss/Prov/poetic Job).
Per-book registry declares which chapters route through the poetic parser.
"""

import argparse
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

V0_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v0", "prose")
V0_ENG_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v0", "eng-baseline")
V0_TRANSLIT_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v0", "translit-baseline")

V1_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1", "he-baseline")
V1_ENG_INTER_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1", "eng-interlinear")
V1_ENG_GLOSS_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1", "eng-gloss")
V1_TRANSLIT_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1", "translit")

ENG_WORD_SEP = " | "  # must match ingest_tahot.py
MAQQEF = "־"

# Tier-1/2 disjunctives — prose (21 books).
# NOTE: These are draft-generation heuristics for the v1-he-baseline starting
# draft, not canon commitments. v2/he (editorial) applies the colometry canon
# to refine breaks relative to this v1 output.
PROSE_BREAKERS = {
    "֑",  # ETNAHTA
    "֒",  # SEGOL (segolta)
    "֔",  # ZAQEF QATAN
    "֕",  # ZAQEF GADOL
    "֖",  # TIPEHA (see TODO below)
}

# Tier-1/2 disjunctives — Sifrei Emet (Pss / Prov / poetic Job).
# NOTE: Same draft-heuristic caveat as PROSE_BREAKERS — seed for v1-he-baseline.
#
# Sifrei Emet primary disjunctives (Wickes 1881): Silluq (terminal, implicit
# at verse end), Athnah (ETNAHTA U+0591), Ole-weyored (OLE U+05AB), Revia
# Gadol (REVIA U+0597), Gereshayim (GERESHAYIM U+059D).
#
# DEHI (U+05AD) was previously included here but is removed. Dehi is a
# pre-atnach servant accent (Wickes 1881; Yeivin §§260-265): it fires within
# the atnach domain — between a stronger disjunctive and atnach itself —
# marking the immediate pre-atnach approach rather than a stich boundary.
# Treating it as a primary breaker causes 1-word orphan cola (Job 38:7
# בְּרָן/וַיָּרִיעוּ, Pro 3:5 בְּטַח אֶל split). Demoted to
# POETIC_INTERIOR_BREAKERS (future conditional use).
#
# GERESHAYIM (U+059D) is added. It is the 3rd-most-frequent Sifrei Emet
# accent (1,661 in Pss, 658 in Job 3-42, 644 in Pro) and marks genuine
# secondary stich boundaries — sub-stich interior breaks between primary
# disjunctives, not within a primary's immediate approach. Its addition
# eliminates the Job 38:7 and Pro 3:5 orphan patterns that dehi caused.
# Gereshayim (U+059D) is distinct from geresh (U+059C, the revia-mugrash
# component) — no ambiguity risk.
#
# ZAQEF QATAN (U+0594) is retained because some poetic chapters in
# books that carry prose cantillation — notably Jonah 2 (the prayer) — use
# prose accent marks throughout despite being poetic in meter and register.
# In those chapters OLE and DEHI are absent; ZAQEF QATAN provides the
# mid-verse interior breaks that bring cola counts into the 3-4 range
# expected for bicola/tricola verse (verified against Jonah 2:7 before/after).
# The v4 editorial pass remains the authoritative line-break surface.
POETIC_BREAKERS = {
    "֑",  # ETNAHTA (U+0591) — primary disjunctive (both systems)
    "֫",  # OLE (U+05AB) — component of oleh ve-yored (Sifrei Emet)
    "֗",  # REVIA (U+0597) — revia gadol / revia mugrash (Sifrei Emet)
    "֝",  # GERESHAYIM (U+059D) — secondary interior disjunctive (Sifrei Emet);
          #   replaces DEHI; fires at genuine sub-stich boundaries
    "֔",  # ZAQEF QATAN (U+0594) — tier-2 prose disjunctive included for
          #   prose-cantillated poetic chapters (e.g. Jonah 2 prayer)
}

# Soft/conditional interior breakers — NOT used in current v1-he-baseline
# generation. Reserved for a future conditional pass (e.g., fire only when a
# colon is ≥4 orthographic words between two primary breaks).
POETIC_INTERIOR_BREAKERS = {
    "֭",  # DEHI (U+05AD) — pre-atnach servant; fires within atnach domain
    "֮",  # ZINOR/tsinnor (U+05AE) — postpositive minor disjunctive
    "֡",  # PAZER (U+05A1) — weak disjunctive in extended revia domains
}

# TODO(canon-2026-04-26): Tifcha treatment.
# Tifcha is often a "servant of atnach" (Wickes 1887) rather than a primary
# breaker. The current script treats tifcha as a tier-2 default breaker,
# which over-fragments single-thought verses (canonical example: Jonah 1:1
# producing a 3-line widow split). Rule H11 in the colometry canon raises
# tifcha's evidence weight but doesn't override this behavior. Consider tuning
# the parser to reduce tifcha-driven splits in short verses or within atnach
# domains when editorial refinement patterns emerge. Do NOT change now;
# log this for follow-up tuning once v1 → v2 editorial passes yield data.

PARAGRAPH_MARKERS_RE = re.compile(r"\s+[פס]\s*$")
VERSE_REF_RE = re.compile(r"^\d+:\d+$")

# BOOK_REGISTRY — all 39 Tanakh books in BHS canonical order.
#
# Keys:
#   subdir          — directory name under v0/prose, v1/he-baseline, etc.
#                     (must match what ingest_tahot.py produced)
#   prefix          — filename stem (chapter files are {prefix}-{n:02d}.txt
#                     but ingest produces {prefix}-{n}.txt; parse_book uses
#                     startswith(prefix+"-") to glob, so zero-padding is
#                     irrelevant as long as the stem matches)
#   tahot_book_code — 3-letter TAHOT internal code (for reference / future
#                     cross-tool use; not read by parse_teamim.py itself)
#   tahot_file      — which TAHOT source file this book lives in
#   poetic_chapters — list of chapter numbers routed through POETIC_BREAKERS
#
# Sifrei Emet routing:
#   Psalms (all 150) and Proverbs (all 31): full Sifrei Emet accent system.
#   Job chapters 3-42: poetic body; chs 1-2 and 42:7-17 are prose by accents
#     but chapter granularity forces a whole-chapter decision — chs 1-2 & 42
#     are left as prose here; the prose tail of ch 42 is a TODO for v4.
#   Lamentations: carries prose accents in Leningrad despite Sifrei Emet
#     liturgical status — confirmed by accent-inventory inspection; routes prose.
#   Song of Songs: prose accents per Leningrad — routes prose.
#   Jonah 2 (the prayer): poetic meter and register, but the Leningrad text
#     uses prose accent marks (no OLE/DEHI). Routes through POETIC_BREAKERS
#     so ZAQEF QATAN provides interior breaks that OLE/DEHI would in a true
#     Sifrei Emet chapter. See POETIC_BREAKERS comment for details.
#
# Ezekiel note: 26-ezekiel is absent from v0/prose (ingest_tahot.py uses
#   "Eze" as the book code but the TAHOT file uses "Ezk" — a pre-existing
#   ingest bug). parse_book("ezekiel") will fail with a clear error until
#   the ingest bug is resolved. Entry is included so --all-books can skip
#   gracefully rather than hard-exit on a missing entry.
BOOK_REGISTRY = {
    # ── Torah (TAHOT_Gen-Deu.txt) ─────────────────────────────────────────
    "genesis": {
        "subdir": "01-genesis",
        "prefix": "genesis",
        "tahot_book_code": "Gen",
        "tahot_file": "TAHOT_Gen-Deu.txt",
        "poetic_chapters": [],
    },
    "exodus": {
        "subdir": "02-exodus",
        "prefix": "exodus",
        "tahot_book_code": "Exo",
        "tahot_file": "TAHOT_Gen-Deu.txt",
        "poetic_chapters": [],
    },
    "leviticus": {
        "subdir": "03-leviticus",
        "prefix": "leviticus",
        "tahot_book_code": "Lev",
        "tahot_file": "TAHOT_Gen-Deu.txt",
        "poetic_chapters": [],
    },
    "numbers": {
        "subdir": "04-numbers",
        "prefix": "numbers",
        "tahot_book_code": "Num",
        "tahot_file": "TAHOT_Gen-Deu.txt",
        "poetic_chapters": [],
    },
    "deuteronomy": {
        "subdir": "05-deuteronomy",
        "prefix": "deuteronomy",
        "tahot_book_code": "Deu",
        "tahot_file": "TAHOT_Gen-Deu.txt",
        "poetic_chapters": [],
    },
    # ── Former Prophets / Writings (TAHOT_Jos-Est.txt) ───────────────────
    "joshua": {
        "subdir": "06-joshua",
        "prefix": "joshua",
        "tahot_book_code": "Jos",
        "tahot_file": "TAHOT_Jos-Est.txt",
        "poetic_chapters": [],
    },
    "judges": {
        "subdir": "07-judges",
        "prefix": "judges",
        "tahot_book_code": "Jdg",
        "tahot_file": "TAHOT_Jos-Est.txt",
        "poetic_chapters": [],
    },
    "ruth": {
        "subdir": "08-ruth",
        "prefix": "ruth",
        "tahot_book_code": "Rut",
        "tahot_file": "TAHOT_Jos-Est.txt",
        "poetic_chapters": [],
    },
    "1samuel": {
        "subdir": "09-1samuel",
        "prefix": "1samuel",
        "tahot_book_code": "1Sa",
        "tahot_file": "TAHOT_Jos-Est.txt",
        "poetic_chapters": [],
    },
    "2samuel": {
        "subdir": "10-2samuel",
        "prefix": "2samuel",
        "tahot_book_code": "2Sa",
        "tahot_file": "TAHOT_Jos-Est.txt",
        "poetic_chapters": [],
    },
    "1kings": {
        "subdir": "11-1kings",
        "prefix": "1kings",
        "tahot_book_code": "1Ki",
        "tahot_file": "TAHOT_Jos-Est.txt",
        "poetic_chapters": [],
    },
    "2kings": {
        "subdir": "12-2kings",
        "prefix": "2kings",
        "tahot_book_code": "2Ki",
        "tahot_file": "TAHOT_Jos-Est.txt",
        "poetic_chapters": [],
    },
    "1chronicles": {
        "subdir": "13-1chronicles",
        "prefix": "1chronicles",
        "tahot_book_code": "1Ch",
        "tahot_file": "TAHOT_Jos-Est.txt",
        "poetic_chapters": [],
    },
    "2chronicles": {
        "subdir": "14-2chronicles",
        "prefix": "2chronicles",
        "tahot_book_code": "2Ch",
        "tahot_file": "TAHOT_Jos-Est.txt",
        "poetic_chapters": [],
    },
    "ezra": {
        "subdir": "15-ezra",
        "prefix": "ezra",
        "tahot_book_code": "Ezr",
        "tahot_file": "TAHOT_Jos-Est.txt",
        "poetic_chapters": [],
    },
    "nehemiah": {
        "subdir": "16-nehemiah",
        "prefix": "nehemiah",
        "tahot_book_code": "Neh",
        "tahot_file": "TAHOT_Jos-Est.txt",
        "poetic_chapters": [],
    },
    "esther": {
        "subdir": "17-esther",
        "prefix": "esther",
        "tahot_book_code": "Est",
        "tahot_file": "TAHOT_Jos-Est.txt",
        "poetic_chapters": [],
    },
    # ── Sifrei Emet + Wisdom (TAHOT_Job-Sng.txt) ─────────────────────────
    "job": {
        "subdir": "18-job",
        "prefix": "job",
        "tahot_book_code": "Job",
        "tahot_file": "TAHOT_Job-Sng.txt",
        # Poetic body: chs 3-42. Prose frame: chs 1-2 and the epilogue
        # tail 42:7-17. At chapter granularity ch 42 is forced to one
        # decision; routing it prose loses the poetic 3:1-42:6 body.
        # TODO(v4): the prose tail of ch 42 needs editorial attention.
        "poetic_chapters": list(range(3, 43)),
    },
    "psalms": {
        "subdir": "19-psalms",
        "prefix": "psalms",
        "tahot_book_code": "Psa",
        "tahot_file": "TAHOT_Job-Sng.txt",
        "poetic_chapters": list(range(1, 151)),   # all 150 Psalms
    },
    "proverbs": {
        "subdir": "20-proverbs",
        "prefix": "proverbs",
        "tahot_book_code": "Pro",
        "tahot_file": "TAHOT_Job-Sng.txt",
        "poetic_chapters": list(range(1, 32)),   # all 31 chapters
    },
    "ecclesiastes": {
        "subdir": "21-ecclesiastes",
        "prefix": "ecclesiastes",
        "tahot_book_code": "Ecc",
        "tahot_file": "TAHOT_Job-Sng.txt",
        "poetic_chapters": [],   # prose accents in Leningrad
    },
    "songofsongs": {
        "subdir": "22-songofsongs",
        "prefix": "songofsongs",
        "tahot_book_code": "Sng",
        "tahot_file": "TAHOT_Job-Sng.txt",
        "poetic_chapters": [],   # prose accents in Leningrad
    },
    # ── Latter Prophets (TAHOT_Isa-Mal.txt) ──────────────────────────────
    "isaiah": {
        "subdir": "23-isaiah",
        "prefix": "isaiah",
        "tahot_book_code": "Isa",
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "poetic_chapters": [],
    },
    "jeremiah": {
        "subdir": "24-jeremiah",
        "prefix": "jeremiah",
        "tahot_book_code": "Jer",
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "poetic_chapters": [],
    },
    "lamentations": {
        "subdir": "25-lamentations",
        "prefix": "lamentations",
        "tahot_book_code": "Lam",
        "tahot_file": "TAHOT_Isa-Mal.txt",
        # Prose accents in Leningrad despite Sifrei Emet liturgical status.
        "poetic_chapters": [],
    },
    "ezekiel": {
        # NOTE: TAHOT uses book code "Ezk" (not "Eze" as ingest_tahot.py
        # assumed). The v0/prose directory exists but may have alignment
        # failures in some chapters due to the ingest mismatch. The
        # tahot_book_code here is corrected to match TAHOT.
        "subdir": "26-ezekiel",
        "prefix": "ezekiel",
        "tahot_book_code": "Ezk",
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "poetic_chapters": [],
    },
    "daniel": {
        "subdir": "27-daniel",
        "prefix": "daniel",
        "tahot_book_code": "Dan",
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "poetic_chapters": [],
    },
    "hosea": {
        "subdir": "28-hosea",
        "prefix": "hosea",
        "tahot_book_code": "Hos",
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "poetic_chapters": [],
    },
    "joel": {
        "subdir": "29-joel",
        "prefix": "joel",
        "tahot_book_code": "Jol",
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "poetic_chapters": [],
    },
    "amos": {
        "subdir": "30-amos",
        "prefix": "amos",
        "tahot_book_code": "Amo",
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "poetic_chapters": [],
    },
    "obadiah": {
        "subdir": "31-obadiah",
        "prefix": "obadiah",
        "tahot_book_code": "Oba",
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "poetic_chapters": [],
    },
    "jonah": {
        "subdir": "32-jonah",
        "prefix": "jonah",
        "tahot_book_code": "Jon",
        "tahot_file": "TAHOT_Isa-Mal.txt",
        # Ch 2 is the psalm/prayer. Leningrad uses prose accent marks
        # throughout (no OLE/DEHI), so POETIC_BREAKERS fires on ETNAHTA,
        # REVIA, and ZAQEF QATAN — giving 3-4 cola/verse as expected.
        "poetic_chapters": [2],
    },
    "micah": {
        "subdir": "33-micah",
        "prefix": "micah",
        "tahot_book_code": "Mic",
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "poetic_chapters": [],
    },
    "nahum": {
        "subdir": "34-nahum",
        "prefix": "nahum",
        "tahot_book_code": "Nam",
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "poetic_chapters": [],
    },
    "habakkuk": {
        "subdir": "35-habakkuk",
        "prefix": "habakkuk",
        "tahot_book_code": "Hab",
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "poetic_chapters": [],
    },
    "zephaniah": {
        "subdir": "36-zephaniah",
        "prefix": "zephaniah",
        "tahot_book_code": "Zep",
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "poetic_chapters": [],
    },
    "haggai": {
        "subdir": "37-haggai",
        "prefix": "haggai",
        "tahot_book_code": "Hag",
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "poetic_chapters": [],
    },
    "zechariah": {
        "subdir": "38-zechariah",
        "prefix": "zechariah",
        "tahot_book_code": "Zec",
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "poetic_chapters": [],
    },
    "malachi": {
        "subdir": "39-malachi",
        "prefix": "malachi",
        "tahot_book_code": "Mal",
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "poetic_chapters": [],
    },
}

# BHS canonical order for --all-books iteration
BOOK_ORDER = [
    "genesis", "exodus", "leviticus", "numbers", "deuteronomy",
    "joshua", "judges", "ruth", "1samuel", "2samuel",
    "1kings", "2kings", "1chronicles", "2chronicles", "ezra", "nehemiah", "esther",
    "job", "psalms", "proverbs", "ecclesiastes", "songofsongs",
    "isaiah", "jeremiah", "lamentations", "ezekiel", "daniel",
    "hosea", "joel", "amos", "obadiah", "jonah", "micah",
    "nahum", "habakkuk", "zephaniah", "haggai", "zechariah", "malachi",
]


# ---- Hebrew structural-gloss naturalizer ---------------------------------
# (Same logic as before — modeled on the GNT project's naturalize().)

POSSESSIVES = ('his', 'her', 'its', 'their', 'your', 'my', 'our')
DEMONSTRATIVES = ('this', 'that', 'these', 'those')

# Single-swap demonstratives: only `this`/`these` get the noun-after-X swap
# without article context. `that`/`those` are excluded because TAHOT's English
# uses "that" for both demonstrative AND complementizer (kī "that, because"),
# so single-swap fires false positives like "knew that" -> "that knew".
# The article-aware patterns ("the X that") still handle the demonstrative
# cases that need it.
DEMONSTRATIVES_SINGLE_SWAP = ('this', 'these')

PREP_OR_FUNCTION = {
    'of', 'in', 'to', 'on', 'at', 'by', 'for', 'with', 'from', 'about',
    'into', 'before', 'after', 'against', 'upon', 'over', 'under',
    'between', 'through', 'around', 'among', 'unto', 'concerning',
    'the', 'a', 'an', 'and', 'or', 'but', 'as', 'than', 'like',
    'is', 'was', 'are', 'were', 'be', 'been', 'am',
    'I', 'you', 'he', 'she', 'we', 'they',
}

HEBREW_ADJECTIVES = {
    'great', 'small', 'large', 'little', 'good', 'evil', 'bad', 'holy',
    'innocent', 'wicked', 'righteous', 'pure', 'mighty', 'strong', 'weak',
    'high', 'low', 'wide', 'long', 'short', 'old', 'young', 'new',
    'beloved', 'living', 'dead', 'first', 'last', 'whole', 'broken',
    'open', 'pleasing', 'unleavened', 'precious',
    # Positional / intensifier adjectives that follow Hebrew noun-first order:
    'right', 'left', 'own',
}

_BRACKET_KEEP_RE = re.compile(r'\[([^\]]+)\]')
_VSO_PRONOUN_RE = re.compile(r'^and (he|she|it|they)\s', re.IGNORECASE)


def naturalize_hebrew_gloss(text, word_units=None):
    """Wooden-but-legible naturalizer: see parse_teamim.py docstring.

    word_units: optional list of per-orthographic-word gloss strings for this
    cola (the same list used to build the interlinear row).  When provided,
    the VSO-pronoun-drop rule can inspect the immediately-following word unit
    rather than guessing from the joined string.
    """
    text = _BRACKET_KEEP_RE.sub(r'\1', text)

    # ---- VSO pronoun-drop (SMOOTH GLOSS ONLY) --------------------------------
    # Hebrew wayyiqtol verbs in prose carry an implicit subject pronoun that
    # TAHOT's interlinear exposes (e.g. "and he appointed").  When the very
    # next per-word unit in the same cola is a nominal subject — a proper noun
    # (capitalised word) or a definite noun phrase ("the X" / "[the] X") —
    # the pronoun is spurious in the smooth gloss because the overt noun
    # supplies the reference (Hebrew VSO word order: verb-subject-object).
    # Drop "he/she/it/they" in the smooth layer; the interlinear keeps it.
    #
    # Rule fires only when word_units is passed and has ≥ 2 entries so that
    # the second unit (index 1) can be inspected.  The check is:
    #   unit[0] starts with "and (he|she|it|they) " (wayyiqtol pronoun pattern)
    #   unit[1] (brackets stripped) starts with a capital letter (proper noun)
    #       OR starts with "the " (definite article phrase)
    if word_units and len(word_units) >= 2:
        first_unit = _BRACKET_KEEP_RE.sub(r'\1', word_units[0]).strip()
        second_unit = _BRACKET_KEEP_RE.sub(r'\1', word_units[1]).strip()
        if _VSO_PRONOUN_RE.match(first_unit):
            is_proper_noun = bool(second_unit) and second_unit[0].isupper()
            is_definite = second_unit.startswith('the ') or second_unit == 'the'
            if is_proper_noun or is_definite:
                # Remove the spurious pronoun from the joined smooth-gloss string.
                # Pattern: "^and (he|she|it|they) " at the start of the cola text.
                text = re.sub(
                    r'^and (he|she|it|they) ',
                    'and ',
                    text,
                    flags=re.IGNORECASE,
                )
    # --------------------------------------------------------------------------

    # Rejoin TAHOT's hyphen-split English ("there- -fore" -> "therefore")
    text = re.sub(r'(\w+)-\s+-(\w+)', r'\1\2', text)

    text = re.sub(r'\bfrom to before\b', 'from before', text)
    text = re.sub(r'\bfrom to upon\b', 'from upon', text)
    text = re.sub(r'\bfrom to under\b', 'from under', text)
    text = re.sub(r'\bto in\b', 'into', text)
    text = re.sub(r'\b(\w+) towards\b', r'toward \1', text)

    adj_alt = '|'.join(re.escape(a) for a in HEBREW_ADJECTIVES)
    dem_alt = '|'.join(DEMONSTRATIVES)
    poss_alt = '|'.join(POSSESSIVES)

    # Combined patterns BEFORE single-swap so we don't ping-pong.
    text = re.sub(rf'\b(the|a|an) (\w+) ({adj_alt}) ({dem_alt})\b', r'\4 \3 \2', text)
    text = re.sub(rf'\b(the|a|an) ({adj_alt}) ({dem_alt})\b', r'\3 \2', text)
    text = re.sub(rf'\b(the|a|an) (\w+) ({dem_alt})\b', r'\3 \2', text)
    text = re.sub(rf'\b(the|a|an) (\w+) ({adj_alt}) ({poss_alt})\b', r'\4 \3 \2', text)
    text = re.sub(rf'\b(the|a|an) (\w+) ({poss_alt})\b', r'\3 \2', text)

    # No-article adj+noun+poss -> poss+adj+noun ("right hand his" -> "his right hand";
    # "own land my" -> "my own land"). Must run before the single-swap possessive,
    # which would otherwise produce "right his hand" and stop.
    text = re.sub(rf'\b({adj_alt}) (\w+) ({poss_alt})\b', r'\3 \1 \2', text)

    for adj in HEBREW_ADJECTIVES:
        text = re.sub(rf'\b(the|a|an) (\w+) {adj}\b', rf'\1 {adj} \2', text)

    def _swap_after_noun(text, after_word_set):
        for w in after_word_set:
            def repl(m, w=w):
                prev = m.group(1)
                if prev.lower() in PREP_OR_FUNCTION:
                    return m.group(0)
                if prev.lower() in after_word_set:
                    return m.group(0)
                return f'{w} {prev}'
            text = re.sub(rf'\b(\w+) {w}\b', repl, text)
        return text

    text = _swap_after_noun(text, set(POSSESSIVES))
    # Use the safer subset for single-swap demonstratives (drops `that`/`those`).
    text = _swap_after_noun(text, set(DEMONSTRATIVES_SINGLE_SWAP))

    for adj in HEBREW_ADJECTIVES:
        def repl(m, adj=adj):
            prev = m.group(1)
            if prev.lower() in PREP_OR_FUNCTION:
                return m.group(0)
            if prev.lower() in DEMONSTRATIVES or prev.lower() in POSSESSIVES:
                return m.group(0)
            return f'{adj} {prev}'
        text = re.sub(rf'\b(\w+) {adj}\b', repl, text)

    text = re.sub(r'\s+', ' ', text).strip()
    text = deduplicate_gloss(text)
    return text


# Hebrew geminate constructions that legitimately produce doubled English
# tokens — distributive numerals, emphatic imperatives, superlative
# intensifiers, time-distributives, botanical descriptors. Must NOT be
# collapsed by deduplicate_gloss(). Closed list per Design D 2026-04-30.
GENUINE_DOUBLINGS = frozenset({
    # Distributive numerals (שְׁנַיִם שְׁנַיִם "in pairs", etc.)
    'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
    'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty',
    'hundred', 'thousand',
    # Superlative intensifiers (מְאֹד מְאֹד)
    'very', 'muchness',
    # Emphatic imperatives (לֵךְ לֵךְ, קוּם קוּם, etc.)
    'go', 'arise', 'awake', 'come', 'pass', 'turn', 'return',
    # Distributive time (יוֹם יוֹם "day by day", etc.)
    'day', 'days', 'year', 'years',
    # Botanical distributive (זֶרַע זֶרַע "seed-bearing")
    'seed',
})

_DOUBLED_WORD_RE = re.compile(r'\b(\w+)\b \1\b', re.IGNORECASE)


def deduplicate_gloss(text: str) -> str:
    """Collapse consecutive identical tokens unless they are genuine Hebrew
    geminate constructions (distributive, emphatic, superlative).

    Loop until stable to handle 3+ peat sequences ("he he he said" → "he said").

    Wave 6 audit (2026-04-30): root cause of ~3,154 DOUBLED_TOKEN findings
    in eng-gloss readability scanner. TAHOT interlinear emits both an explicit
    independent pronoun and the verb's inflected-subject gloss in the same
    colon (הִוא נָתְנָה → "she she gave"); naturalize_hebrew_gloss VSO-pronoun-
    drop misses this because the verb is followed by a verb-encoded subject
    rather than a nominal subject.
    """
    def _replace(m):
        tok = m.group(1).lower()
        if tok in GENUINE_DOUBLINGS:
            return m.group(0)   # preserve genuine doubling
        return m.group(1)       # collapse artifact
    while _DOUBLED_WORD_RE.search(text):
        new_text = _DOUBLED_WORD_RE.sub(_replace, text)
        if new_text == text:
            break  # stuck on genuine doublings only
        text = new_text
    return text


# ---- Cola splitting -----------------------------------------------------

def hebrew_orthographic_word_count(prosodic_word):
    """Count orthographic words in a maqqef-joined prosodic-word token."""
    return prosodic_word.count(MAQQEF) + 1


def compute_cola_boundaries(he_pwords, breakers):
    """Return [(start_idx, end_idx), ...] of prosodic-word ranges per cola."""
    boundaries = [0]
    for i, w in enumerate(he_pwords):
        if not w:
            continue
        if any(b in w for b in breakers):
            boundaries.append(i + 1)
    if boundaries[-1] != len(he_pwords):
        boundaries.append(len(he_pwords))
    return list(zip(boundaries, boundaries[1:]))


def strip_paragraph_marker(verse_text):
    """Remove trailing standalone Peh / Samekh paragraph marker."""
    return PARAGRAPH_MARKERS_RE.sub("", verse_text)


def read_v0_chapter(path):
    """Read a v0-style .txt chapter file. Returns [(ref, verse_text), ...]."""
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    blocks = re.split(r"\n\s*\n", raw.strip())
    out = []
    for block in blocks:
        parts = block.strip().split("\n", 1)
        if len(parts) != 2:
            continue
        ref, text = parts
        if not VERSE_REF_RE.match(ref.strip()):
            continue
        out.append((ref.strip(), text.strip()))
    return out


def parse_chapter(he_in, en_in, tr_in,
                  he_out, en_inter_out, en_gloss_out, tr_out,
                  breakers):
    """Parse one chapter into the four v1 outputs.

    Alignment mismatches between Hebrew orthographic-word count and
    English/translit unit count are treated as warnings rather than fatal
    errors.  The root cause is TAHOT formatting quirks:

      (a) Angle-bracketed English-only words (<obj.>, <the>, <into>, <to>)
          are stripped by clean_english() → that TAHOT row contributes 1
          Hebrew orthographic word but 0 English units.
      (b) Intra-row maqqef entries (e.g. מַה/־/זֶּ֣ה) — one TAHOT row,
          one English gloss, but the Hebrew side contains the maqqef
          character making it count as 2 orthographic words.
      (c) Qere/Ketiv bracket-only rows ([ ]) that survive the skip filter
          and skew counts in one direction.

    On a mismatch the Hebrew cola are still emitted (the primary output).
    The English/translit interlinear is skipped for the misaligned verse
    so we never emit a misaligned interlinear file.  A per-chapter warning
    line is printed; the caller accumulates the mismatch count.

    Returns the number of verses with alignment mismatches in this chapter.
    """
    he_verses = read_v0_chapter(he_in)
    en_lookup = {ref: text for ref, text in read_v0_chapter(en_in)}
    tr_lookup = {ref: text for ref, text in read_v0_chapter(tr_in)}

    he_blocks, inter_blocks, gloss_blocks, tr_blocks = [], [], [], []
    mismatch_count = 0

    for ref, he_text in he_verses:
        he_clean = strip_paragraph_marker(he_text)
        he_pwords = [w for w in he_clean.split(" ") if w]

        # Total orthographic words for this verse
        ortho_count = sum(hebrew_orthographic_word_count(w) for w in he_pwords)

        en_text = en_lookup.get(ref, "")
        en_words = [w.strip() for w in en_text.split(ENG_WORD_SEP)] if en_text else []
        tr_text = tr_lookup.get(ref, "")
        tr_words = [w.strip() for w in tr_text.split(ENG_WORD_SEP)] if tr_text else []

        en_aligned = True
        tr_aligned = True

        if en_words and len(en_words) != ortho_count:
            print(
                f"  WARNING: alignment mismatch at {ref}: "
                f"{ortho_count} Hebrew ortho-words vs {len(en_words)} English units "
                f"(TAHOT formatting quirk — Hebrew cola emitted; interlinear skipped for this verse)"
            )
            en_aligned = False
            tr_aligned = False  # skip translit too when English is misaligned
            mismatch_count += 1
        elif tr_words and len(tr_words) != ortho_count:
            print(
                f"  WARNING: alignment mismatch at {ref}: "
                f"{ortho_count} Hebrew ortho-words vs {len(tr_words)} translit units "
                f"(TAHOT formatting quirk — Hebrew cola emitted; translit skipped for this verse)"
            )
            tr_aligned = False
            mismatch_count += 1

        # Cola boundaries (v1-he-baseline starting draft) are at PROSODIC-word level.
        # Te'amim sit on prosodic units; v2/he editorial refines these baseline breaks
        # per the colometry canon's atomic-thought and syntax criteria.
        boundaries = compute_cola_boundaries(he_pwords, breakers)

        # Map prosodic-word index -> orthographic-word start index
        ortho_starts = [0]
        for c in (hebrew_orthographic_word_count(w) for w in he_pwords):
            ortho_starts.append(ortho_starts[-1] + c)

        he_cola, inter_cola, gloss_cola, trans_cola = [], [], [], []
        for pa, pb in boundaries:
            he_cola.append(" ".join(he_pwords[pa:pb]))

            oa = ortho_starts[pa]
            ob = ortho_starts[pb]

            if en_words and en_aligned:
                inter_words = en_words[oa:ob]
                inter_cola.append(ENG_WORD_SEP.join(inter_words))
                gloss_input = " ".join(w for w in inter_words if w)
                gloss_cola.append(naturalize_hebrew_gloss(gloss_input, word_units=inter_words))

            if tr_words and tr_aligned:
                trans_cola.append(ENG_WORD_SEP.join(tr_words[oa:ob]))

        he_blocks.append(ref + "\n" + "\n".join(he_cola))
        if inter_cola:
            inter_blocks.append(ref + "\n" + "\n".join(inter_cola))
            gloss_blocks.append(ref + "\n" + "\n".join(gloss_cola))
        if trans_cola:
            tr_blocks.append(ref + "\n" + "\n".join(trans_cola))

    for path in (he_out, en_inter_out, en_gloss_out, tr_out):
        os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(he_out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n\n".join(he_blocks) + "\n")
    if inter_blocks:
        with open(en_inter_out, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n\n".join(inter_blocks) + "\n")
        with open(en_gloss_out, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n\n".join(gloss_blocks) + "\n")
    if tr_blocks:
        with open(tr_out, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n\n".join(tr_blocks) + "\n")

    return mismatch_count


def parse_book(book_key):
    if book_key not in BOOK_REGISTRY:
        sys.exit(f"Unknown book key: {book_key}")
    spec = BOOK_REGISTRY[book_key]

    he_in_dir = os.path.join(V0_DIR, spec["subdir"])
    en_in_dir = os.path.join(V0_ENG_DIR, spec["subdir"])
    tr_in_dir = os.path.join(V0_TRANSLIT_DIR, spec["subdir"])

    he_out_dir = os.path.join(V1_DIR, spec["subdir"])
    inter_out_dir = os.path.join(V1_ENG_INTER_DIR, spec["subdir"])
    gloss_out_dir = os.path.join(V1_ENG_GLOSS_DIR, spec["subdir"])
    tr_out_dir = os.path.join(V1_TRANSLIT_DIR, spec["subdir"])

    if not os.path.isdir(he_in_dir):
        sys.exit(f"v0/prose dir not found: {he_in_dir}")

    chapter_files = sorted(
        fn for fn in os.listdir(he_in_dir)
        if fn.startswith(spec["prefix"] + "-") and fn.endswith(".txt")
    )

    poetic_chapters = set(spec.get("poetic_chapters", []))
    total_lines = 0
    total_mismatches = 0

    for fn in chapter_files:
        chapter_num = int(fn[len(spec["prefix"]) + 1:-4])
        breakers = POETIC_BREAKERS if chapter_num in poetic_chapters else PROSE_BREAKERS

        chapter_mismatches = parse_chapter(
            os.path.join(he_in_dir, fn),
            os.path.join(en_in_dir, fn),
            os.path.join(tr_in_dir, fn),
            os.path.join(he_out_dir, fn),
            os.path.join(inter_out_dir, fn),
            os.path.join(gloss_out_dir, fn),
            os.path.join(tr_out_dir, fn),
            breakers,
        )
        total_mismatches += chapter_mismatches

        with open(os.path.join(he_out_dir, fn), "r", encoding="utf-8") as f:
            line_count = sum(
                1 for line in f
                if line.strip() and not VERSE_REF_RE.match(line.strip())
            )
        total_lines += line_count
        accent_label = "Sifrei Emet" if chapter_num in poetic_chapters else "prose"
        print(f"  {fn}: {line_count} cola, {accent_label}")

    mismatch_note = (
        f", {total_mismatches} verse(s) with alignment warnings (interlinear skipped for those)"
        if total_mismatches else ""
    )
    print(
        f"\n{book_key}: {total_lines} cola "
        f"-> v1-he-baseline / v1-eng-interlinear / v1-eng-gloss / v1-translit"
        f"{mismatch_note}"
    )
    return total_mismatches


def parse_all_books():
    """Iterate every book in BOOK_REGISTRY in BHS canonical order.

    Prints per-book status (parse OK / errors / cola count).
    Books whose v0/prose directory does not exist are skipped with a warning
    rather than hard-exiting.  Alignment mismatches are treated as warnings;
    books with mismatches are still counted as parsed (Hebrew cola emitted).
    """
    grand_total = 0
    ok_count = 0
    skip_count = 0
    total_mismatch_verses = 0

    for book_key in BOOK_ORDER:
        spec = BOOK_REGISTRY[book_key]
        he_in_dir = os.path.join(V0_DIR, spec["subdir"])
        if not os.path.isdir(he_in_dir):
            print(f"  SKIP {book_key}: v0/prose dir not found ({spec['subdir']})")
            skip_count += 1
            continue
        try:
            print(f"\n--- {book_key} ---")
            book_mismatches = parse_book(book_key)
            ok_count += 1
            total_mismatch_verses += book_mismatches
        except SystemExit as exc:
            print(f"  ERROR {book_key}: {exc}")
            skip_count += 1

    mismatch_note = (
        f"; {total_mismatch_verses} verse(s) across corpus with alignment warnings "
        f"(interlinear skipped for those — TAHOT formatting quirks)"
        if total_mismatch_verses else ""
    )
    print(
        f"\n=== --all-books complete: {ok_count} parsed, {skip_count} skipped/errored"
        f"{mismatch_note} ==="
    )


def main():
    ap = argparse.ArgumentParser(
        description="Te'amim-driven baseline cola generator (v1-he-baseline)."
    )
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument(
        "--book",
        metavar="BOOK_KEY",
        help="Parse a single book by registry key (e.g. 'jonah', 'genesis').",
    )
    grp.add_argument(
        "--all-books",
        action="store_true",
        help=(
            "Parse every book in BOOK_REGISTRY in BHS canonical order. "
            "Prints per-book status. Books with missing v0/prose dirs are "
            "skipped with a warning."
        ),
    )
    args = ap.parse_args()

    if args.all_books:
        parse_all_books()
    else:
        parse_book(args.book)


if __name__ == "__main__":
    main()
