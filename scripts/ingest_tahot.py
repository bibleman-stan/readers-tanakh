"""
ingest_tahot.py - Convert STEPBible TAHOT TSV to v0 baseline files.

For each book, produces three parallel chapter files:

  v0-prose/             Hebrew (with maqqef inline; prosodic-word boundaries
                        are space-separated; orthographic-word boundaries
                        within a prosodic word are signaled by maqqef ־ inline)
  v0-eng-baseline/      English glosses, ORTHOGRAPHIC-word per ` | ` separator
                        (each Hebrew word gets one English unit so the
                        four-layer reader can show per-word translit /
                        interlinear under each Hebrew word)
  v0-translit-baseline/ Modern Israeli-style transliteration, same ` | `
                        per-orthographic-word format

Hebrew versification primary (canon §3): when TAHOT lists English (NRSV)
ref with parenthetical Hebrew ref, the Hebrew ref is used for filenames /
verse keys and a crosswalk JSON records the mapping.

Qere-by-default (canon §6): TAHOT's "L" rows are Leningrad with Qere
applied; "K" rows are Ketiv alternates and skipped.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
TAHOT_DIR = os.path.join(REPO_ROOT, "research", "stepbible-tahot")
V0_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v0", "prose")
V0_ENG_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v0", "eng-baseline")
V0_TRANSLIT_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v0", "translit-baseline")

# Separator between orthographic-word units in v0-eng-baseline / v0-translit
# (one Hebrew word -> one English unit -> one translit unit)
ENG_WORD_SEP = " | "

MAQQEF = "־"

# BHS canonical order, 2-digit-prefix subdirs, 3-letter TAHOT book codes.
# Grouped by the four TAHOT source files.
BOOK_REGISTRY = {
    # ── Torah (TAHOT_Gen-Deu.txt) ─────────────────────────────────────────
    "genesis": {
        "tahot_file": "TAHOT_Gen-Deu.txt",
        "tahot_book_code": "Gen",
        "out_subdir": "01-genesis",
        "out_prefix": "genesis",
    },
    "exodus": {
        "tahot_file": "TAHOT_Gen-Deu.txt",
        "tahot_book_code": "Exo",
        "out_subdir": "02-exodus",
        "out_prefix": "exodus",
    },
    "leviticus": {
        "tahot_file": "TAHOT_Gen-Deu.txt",
        "tahot_book_code": "Lev",
        "out_subdir": "03-leviticus",
        "out_prefix": "leviticus",
    },
    "numbers": {
        "tahot_file": "TAHOT_Gen-Deu.txt",
        "tahot_book_code": "Num",
        "out_subdir": "04-numbers",
        "out_prefix": "numbers",
    },
    "deuteronomy": {
        "tahot_file": "TAHOT_Gen-Deu.txt",
        "tahot_book_code": "Deu",
        "out_subdir": "05-deuteronomy",
        "out_prefix": "deuteronomy",
    },
    # ── Former Prophets / Writings (TAHOT_Jos-Est.txt) ───────────────────
    "joshua": {
        "tahot_file": "TAHOT_Jos-Est.txt",
        "tahot_book_code": "Jos",
        "out_subdir": "06-joshua",
        "out_prefix": "joshua",
    },
    "judges": {
        "tahot_file": "TAHOT_Jos-Est.txt",
        "tahot_book_code": "Jdg",
        "out_subdir": "07-judges",
        "out_prefix": "judges",
    },
    "ruth": {
        "tahot_file": "TAHOT_Jos-Est.txt",
        "tahot_book_code": "Rut",
        "out_subdir": "08-ruth",
        "out_prefix": "ruth",
    },
    "1samuel": {
        "tahot_file": "TAHOT_Jos-Est.txt",
        "tahot_book_code": "1Sa",
        "out_subdir": "09-1samuel",
        "out_prefix": "1samuel",
    },
    "2samuel": {
        "tahot_file": "TAHOT_Jos-Est.txt",
        "tahot_book_code": "2Sa",
        "out_subdir": "10-2samuel",
        "out_prefix": "2samuel",
    },
    "1kings": {
        "tahot_file": "TAHOT_Jos-Est.txt",
        "tahot_book_code": "1Ki",
        "out_subdir": "11-1kings",
        "out_prefix": "1kings",
    },
    "2kings": {
        "tahot_file": "TAHOT_Jos-Est.txt",
        "tahot_book_code": "2Ki",
        "out_subdir": "12-2kings",
        "out_prefix": "2kings",
    },
    "1chronicles": {
        "tahot_file": "TAHOT_Jos-Est.txt",
        "tahot_book_code": "1Ch",
        "out_subdir": "13-1chronicles",
        "out_prefix": "1chronicles",
    },
    "2chronicles": {
        "tahot_file": "TAHOT_Jos-Est.txt",
        "tahot_book_code": "2Ch",
        "out_subdir": "14-2chronicles",
        "out_prefix": "2chronicles",
    },
    "ezra": {
        "tahot_file": "TAHOT_Jos-Est.txt",
        "tahot_book_code": "Ezr",
        "out_subdir": "15-ezra",
        "out_prefix": "ezra",
    },
    "nehemiah": {
        "tahot_file": "TAHOT_Jos-Est.txt",
        "tahot_book_code": "Neh",
        "out_subdir": "16-nehemiah",
        "out_prefix": "nehemiah",
    },
    "esther": {
        "tahot_file": "TAHOT_Jos-Est.txt",
        "tahot_book_code": "Est",
        "out_subdir": "17-esther",
        "out_prefix": "esther",
    },
    # ── Sifrei Emet + Megillot (TAHOT_Job-Sng.txt) ───────────────────────
    "job": {
        "tahot_file": "TAHOT_Job-Sng.txt",
        "tahot_book_code": "Job",
        "out_subdir": "18-job",
        "out_prefix": "job",
    },
    "psalms": {
        "tahot_file": "TAHOT_Job-Sng.txt",
        "tahot_book_code": "Psa",
        "out_subdir": "19-psalms",
        "out_prefix": "psalms",
    },
    "proverbs": {
        "tahot_file": "TAHOT_Job-Sng.txt",
        "tahot_book_code": "Pro",
        "out_subdir": "20-proverbs",
        "out_prefix": "proverbs",
    },
    "ecclesiastes": {
        "tahot_file": "TAHOT_Job-Sng.txt",
        "tahot_book_code": "Ecc",
        "out_subdir": "21-ecclesiastes",
        "out_prefix": "ecclesiastes",
    },
    "songofsongs": {
        "tahot_file": "TAHOT_Job-Sng.txt",
        "tahot_book_code": "Sng",
        "out_subdir": "22-songofsongs",
        "out_prefix": "songofsongs",
    },
    # ── Latter Prophets (TAHOT_Isa-Mal.txt) ──────────────────────────────
    "isaiah": {
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "tahot_book_code": "Isa",
        "out_subdir": "23-isaiah",
        "out_prefix": "isaiah",
    },
    "jeremiah": {
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "tahot_book_code": "Jer",
        "out_subdir": "24-jeremiah",
        "out_prefix": "jeremiah",
    },
    "lamentations": {
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "tahot_book_code": "Lam",
        "out_subdir": "25-lamentations",
        "out_prefix": "lamentations",
    },
    "ezekiel": {
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "tahot_book_code": "Ezk",
        "out_subdir": "26-ezekiel",
        "out_prefix": "ezekiel",
    },
    "daniel": {
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "tahot_book_code": "Dan",
        "out_subdir": "27-daniel",
        "out_prefix": "daniel",
    },
    "hosea": {
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "tahot_book_code": "Hos",
        "out_subdir": "28-hosea",
        "out_prefix": "hosea",
    },
    "joel": {
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "tahot_book_code": "Jol",
        "out_subdir": "29-joel",
        "out_prefix": "joel",
    },
    "amos": {
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "tahot_book_code": "Amo",
        "out_subdir": "30-amos",
        "out_prefix": "amos",
    },
    "obadiah": {
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "tahot_book_code": "Oba",
        "out_subdir": "31-obadiah",
        "out_prefix": "obadiah",
    },
    "jonah": {
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "tahot_book_code": "Jon",
        "out_subdir": "32-jonah",
        "out_prefix": "jonah",
    },
    "micah": {
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "tahot_book_code": "Mic",
        "out_subdir": "33-micah",
        "out_prefix": "micah",
    },
    "nahum": {
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "tahot_book_code": "Nam",
        "out_subdir": "34-nahum",
        "out_prefix": "nahum",
    },
    "habakkuk": {
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "tahot_book_code": "Hab",
        "out_subdir": "35-habakkuk",
        "out_prefix": "habakkuk",
    },
    "zephaniah": {
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "tahot_book_code": "Zep",
        "out_subdir": "36-zephaniah",
        "out_prefix": "zephaniah",
    },
    "haggai": {
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "tahot_book_code": "Hag",
        "out_subdir": "37-haggai",
        "out_prefix": "haggai",
    },
    "zechariah": {
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "tahot_book_code": "Zec",
        "out_subdir": "38-zechariah",
        "out_prefix": "zechariah",
    },
    "malachi": {
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "tahot_book_code": "Mal",
        "out_subdir": "39-malachi",
        "out_prefix": "malachi",
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

REF_RE = re.compile(
    r"^([A-Za-z0-9]+)\."
    r"(\d+)\.(\d+)"
    r"(?:\((\d+)\.(\d+)\))?"
    r"#\d+(?:=(.+))?$"
)

ENG_OMIT_BRACKET_RE = re.compile(r"<[^>]*>")
ENG_ANGLE_ONLY_RE = re.compile(r"^(<[^>]*>\s*)+$")  # entire field is <...> tokens


# Strip trailing scribal glyphs from cleaned Hebrew fields.
# The paragraph/section markers פ and ס appear as STANDALONE characters
# preceded by whitespace — they are NOT part of any Hebrew word.
# The Nun hafucha (U+05C6 ׆) is a scribal marker that appears between
# whitespace-separated tokens (always preceded by space).
# Pattern: one or more groups of (optional whitespace + marker) at end of string.
# IMPORTANT: ס (U+05E1 Samekh) is also a normal Hebrew consonant — only strip
# it when it appears as a whitespace-separated standalone token, never when it
# is the final consonant of a Hebrew word (e.g. חָמָס = violence).
# Likewise for פ (U+05E4 Peh).
_SCRIBAL_TAIL_RE = re.compile(
    r"(\s+[׆פס])+\s*$",  # one or more: whitespace + standalone scribal marker
    re.UNICODE,
)


def clean_hebrew(raw):
    """Strip STEP morphological / and \\ separators; preserve in-text punctuation.

    Also strips trailing scribal glyphs that TAHOT embeds in Hebrew fields:
      - Paragraph/section markers פ and ס (section-division glyphs; no Hebrew
        word value; no English/translit counterpart)
      - Nun hafucha / inverted nun (U+05C6 ׆), a rare scribal marker that
        appears in Numbers 10:34–36 around the inverted-nun sections

    Stripping these at the source prevents spurious ortho-word counts when
    the markers appear mid-verse (where the end-of-verse regex in
    parse_teamim cannot reach them) and when they are embedded inside a
    single TAHOT row alongside actual Hebrew.
    """
    cleaned = raw.replace("/", "").replace("\\", "")
    cleaned = _SCRIBAL_TAIL_RE.sub("", cleaned)
    return cleaned.strip()


def clean_english(raw):
    """Convert TAHOT field 4 to a clean per-word string.

    Drops trailing \\marker annotations; collapses morpheme separators.

    Angle-bracketed words (<obj.>, <the>, <into>, <to>, etc.) are TAHOT
    editor-supplied words that have no direct Hebrew anchor.  When the
    ENTIRE field (before \\) consists only of angle-bracket tokens the row
    produces zero English text — which creates a unit-count mismatch when
    parse_teamim counts ortho-words vs English units.

    Fix (quirk a): if the pre-backslash portion is all angle-bracket content
    (after stripping), return the inner text of those brackets as a
    [square-bracket] supplied gloss rather than empty string.  This keeps
    the ortho-word count aligned while clearly marking the supplied word in
    the interlinear layer.  Mixed rows (e.g. "and/ <obj.>") keep their
    non-bracket content and drop the brackets.

    [square-bracketed] words are preserved as-is — the naturalizer in
    parse_teamim strips them for the smooth gloss layer.
    """
    if not raw:
        return ""
    head = raw.split("\\", 1)[0]
    # Quirk (a): entire field is angle-bracket tokens → convert to [square] gloss
    if ENG_ANGLE_ONLY_RE.match(head.strip()):
        inner = ENG_OMIT_BRACKET_RE.sub(lambda m: m.group(0)[1:-1], head).strip()
        inner = inner.replace("/", " ").strip()
        if inner:
            return f"[{inner}]"
        return "[obj.]"
    head = ENG_OMIT_BRACKET_RE.sub("", head)
    head = head.replace("/", " ")
    return " ".join(head.split())


def is_proper_noun(grammar_field):
    """TAHOT morphology code 'Np' marks proper nouns."""
    return bool(grammar_field) and "Np" in grammar_field


def clean_translit(raw, is_proper):
    """Convert TAHOT field 3 transliteration to modern Israeli style.

    - Drops syllable dots and morpheme separators
    - Drops glottal-stop apostrophes at word boundaries (initial/trailing
      aleph is silent in modern reading), keeps mid-word apostrophes
      (ayin / mid-word aleph that mark a real syllable break)
    - Drops trailing maqqef hyphen (the Hebrew side carries the join info)
    - Lowercases; capitalizes first letter for proper nouns
    """
    if not raw:
        return ""
    head = raw.split("\\", 1)[0]
    head = head.replace("/", "")
    head = head.replace(".", "")
    head = head.lower().strip()
    # Strip maqqef hyphen FIRST so a trailing apostrophe behind it gets exposed
    # to the apostrophe-stripping pass (TAHOT writes "halo'-" / "lo'-" with
    # both terminators on words like לא־).
    head = re.sub(r"-$", "", head)
    head = re.sub(r"^'+", "", head)
    head = re.sub(r"'+$", "", head)
    if is_proper and head:
        head = head[0].upper() + head[1:]
    return head


def _count_internal_maqqef(he_clean):
    """Count maqqef chars that are NOT at the end of the string.

    A trailing maqqef means the word joins the next TAHOT row (handled by
    the joins_next flag).  Internal maqqef chars (within the token) mean
    this single TAHOT row encodes more than one orthographic word — the
    intra-row maqqef quirk.
    """
    if not he_clean:
        return 0
    # Strip the trailing maqqef (if any) before counting
    stripped = he_clean[:-1] if he_clean.endswith(MAQQEF) else he_clean
    return stripped.count(MAQQEF)


def parse_tahot_for_book(tahot_path, book_code):
    """Parse TAHOT for a book.

    Returns ({chapter: {verse: [{he, en, translit, joins_next}]}}, crosswalk).
    Each list entry is one ORTHOGRAPHIC word; joins_next=True iff the Hebrew
    word ends in maqqef.

    Three TAHOT formatting quirks are handled here to keep Hebrew
    ortho-word counts aligned with English unit counts:

    (a) Angle-bracket-only English (<obj.>, <to>, etc.) — now handled in
        clean_english() which returns [obj.] instead of empty string.

    (b) Intra-row maqqef: a single TAHOT row whose Hebrew field contains an
        INTERNAL maqqef (not just trailing) encodes multiple ortho-words
        with a single English gloss.  Detect these rows and emit extra
        word entries (one per additional ortho-word) so the English unit
        count matches the ortho count.  The extra entries carry the same
        English gloss for the last sub-word and "[—]" for all earlier ones,
        marking them as continuation units in the interlinear.

    (c) Empty-Hebrew Q(K) rows: bracket-only Qere variants like "[ ]" that
        have no Hebrew content are skipped entirely — they have no Hebrew
        anchor and inflate the English unit count without adding to the
        Hebrew.
    """
    chapters = defaultdict(lambda: defaultdict(list))
    crosswalk = {}

    with open(tahot_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\r\n")
            if not line or "\t" not in line:
                continue
            fields = line.split("\t")
            ref_field = fields[0]
            if not ref_field.startswith(book_code + "."):
                continue
            m = REF_RE.match(ref_field)
            if not m:
                continue

            eng_ch, eng_v = int(m.group(2)), int(m.group(3))
            heb_ch_str, heb_v_str = m.group(4), m.group(5)
            text_type = m.group(6)

            if heb_ch_str is not None:
                heb_ch, heb_v = int(heb_ch_str), int(heb_v_str)
                crosswalk[f"{heb_ch}:{heb_v}"] = f"{eng_ch}:{eng_v}"
            else:
                heb_ch, heb_v = eng_ch, eng_v

            # Skip Ketiv-only rows (Qere is the default reading)
            if text_type and "K" in text_type and "L" not in text_type and "Q" not in text_type:
                continue

            he = clean_hebrew(fields[1]) if len(fields) > 1 else ""
            translit_raw = fields[2] if len(fields) > 2 else ""
            en = clean_english(fields[3]) if len(fields) > 3 else ""
            grammar = fields[5] if len(fields) > 5 else ""
            translit = clean_translit(translit_raw, is_proper_noun(grammar))

            # Quirk (c): skip rows where Hebrew is empty after cleaning.
            # These are Qere/Ketiv bracket-only rows (e.g. "[ ]" English
            # with no Hebrew anchor) — they inflate English unit count.
            if not he:
                continue

            # Quirk (d): internal whitespace in he from TAHOT's " / " separator
            # used as a morpheme-internal boundary within a single orthographic
            # word (e.g. 'פְּדָה/ /צוּר' → after clean_hebrew → 'פְּדָה צוּר').
            # This is one Hebrew word (Pedahzur) on one TAHOT row with one
            # English gloss; the space after stripping slashes is artefactual.
            # Fix: collapse internal whitespace so the token is read back as
            # ONE prosodic-word token (no spurious split in parse_teamim).
            if " " in he:
                he = re.sub(r"\s+", "", he)

            # Quirk (b): intra-row maqqef.
            # A single TAHOT row whose cleaned Hebrew contains an INTERNAL
            # maqqef (not just trailing) represents multiple ortho-words with
            # one English gloss.  Split the row into N+1 entries where N is
            # the internal-maqqef count, so the English unit count matches.
            #
            # Splitting strategy: split `he` on the maqqef character.
            #   sub_words = ['כְּדָרְ', 'לָעֹמֶר'] for 'כְּדָרְ─לָעֹמֶר'
            # The last sub-word carries the English gloss; earlier sub-words
            # get "[—]" (continuation marker).  Each non-final sub-word has
            # joins_next=True to preserve prosodic-word assembly downstream.
            extra_ortho = _count_internal_maqqef(he)
            if extra_ortho > 0:
                # Split he on the internal maqqef chars (preserve trailing maqqef
                # on the final sub-part if the original row had one).
                trailing_maqqef = he.endswith(MAQQEF)
                he_stripped = he[:-1] if trailing_maqqef else he
                sub_parts = he_stripped.split(MAQQEF)
                # Emit one entry per sub-part.
                # Non-final sub-parts: append maqqef to signal join-to-next,
                #   get "[—]" as interlinear placeholder.
                # Final sub-part: restore trailing maqqef if original had one,
                #   gets the actual English gloss and translit.
                for k, sub in enumerate(sub_parts):
                    is_last = (k == len(sub_parts) - 1)
                    if is_last:
                        he_entry = sub + (MAQQEF if trailing_maqqef else "")
                        en_entry = en
                        tr_entry = translit
                        jn = trailing_maqqef
                    else:
                        he_entry = sub + MAQQEF
                        en_entry = "[—]"
                        tr_entry = "[—]"  # placeholder keeps unit counts aligned
                        jn = True  # this sub-part joins into the next
                    chapters[heb_ch][heb_v].append({
                        "he": he_entry,
                        "en": en_entry,
                        "translit": tr_entry,
                        "joins_next": jn,
                    })
            else:
                chapters[heb_ch][heb_v].append({
                    "he": he,
                    "en": en,
                    "translit": translit,
                    "joins_next": he.endswith(MAQQEF),
                })

    return chapters, crosswalk


def write_chapter_files(he_path, en_path, tr_path, chapter_num, verses):
    """Write three parallel v0 files for one chapter.

    Hebrew is grouped at PROSODIC-word level (maqqef-joined orthographic
    words concatenated without space -- the maqqef glyph fills the join
    visually). English and translit are stored at ORTHOGRAPHIC-word level
    so the build can render per-word spans aligned with Hebrew.
    """
    for path in (he_path, en_path, tr_path):
        os.makedirs(os.path.dirname(path), exist_ok=True)

    verse_keys = sorted(verses.keys())
    with open(he_path, "w", encoding="utf-8", newline="\n") as fh, \
         open(en_path, "w", encoding="utf-8", newline="\n") as fe, \
         open(tr_path, "w", encoding="utf-8", newline="\n") as ft:
        for i, v in enumerate(verse_keys):
            words = [w for w in verses[v] if w["he"] or w["en"] or w["translit"]]

            # Hebrew: prosodic-word level. Concatenate maqqef-joined words
            # without space; separate prosodic-words with a single space.
            he_pwords = []
            for j, w in enumerate(words):
                if he_pwords and words[j - 1]["joins_next"]:
                    he_pwords[-1] = he_pwords[-1] + w["he"]
                else:
                    he_pwords.append(w["he"])
            he_text = " ".join(he_pwords)

            # English / translit: orthographic-word level
            en_text = ENG_WORD_SEP.join(w["en"] for w in words)
            tr_text = ENG_WORD_SEP.join(w["translit"] for w in words)

            fh.write(f"{chapter_num}:{v}\n{he_text}\n")
            fe.write(f"{chapter_num}:{v}\n{en_text}\n")
            ft.write(f"{chapter_num}:{v}\n{tr_text}\n")
            if i < len(verse_keys) - 1:
                fh.write("\n")
                fe.write("\n")
                ft.write("\n")


def ingest_book(book_key, fatal_on_missing=True):
    """Ingest a single book.

    Returns (chapter_count, verse_count) on success, or None if the TAHOT
    file is missing and fatal_on_missing=False (warning printed, no exit).
    """
    if book_key not in BOOK_REGISTRY:
        sys.exit(f"Unknown book key: {book_key}")
    spec = BOOK_REGISTRY[book_key]
    tahot_path = os.path.join(TAHOT_DIR, spec["tahot_file"])

    if not os.path.exists(tahot_path):
        msg = f"WARNING: TAHOT file {spec['tahot_file']!r} not vendored; skipping book {book_key!r}"
        print(msg)
        if fatal_on_missing:
            sys.exit(1)
        return None

    chapters, crosswalk = parse_tahot_for_book(tahot_path, spec["tahot_book_code"])
    if not chapters:
        msg = f"No verses found for book code {spec['tahot_book_code']!r} in {spec['tahot_file']!r}"
        print(f"WARNING: {msg}")
        if fatal_on_missing:
            sys.exit(msg)
        return None

    he_dir = os.path.join(V0_DIR, spec["out_subdir"])
    en_dir = os.path.join(V0_ENG_DIR, spec["out_subdir"])
    tr_dir = os.path.join(V0_TRANSLIT_DIR, spec["out_subdir"])

    chapter_count = 0
    verse_count = 0
    for chapter_num in sorted(chapters.keys()):
        fn = f"{spec['out_prefix']}-{chapter_num:02d}.txt"
        write_chapter_files(
            os.path.join(he_dir, fn),
            os.path.join(en_dir, fn),
            os.path.join(tr_dir, fn),
            chapter_num,
            chapters[chapter_num],
        )
        chapter_count += 1
        verse_count += len(chapters[chapter_num])
        print(f"  {fn}: {len(chapters[chapter_num])} verses")

    if crosswalk:
        crosswalk_path = os.path.join(he_dir, f"{spec['out_prefix']}-crosswalk.json")
        with open(crosswalk_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(crosswalk, f, ensure_ascii=False, indent=2, sort_keys=True)
        print(f"  crosswalk: {crosswalk_path} ({len(crosswalk)} verse-numbering differences)")

    print(
        f"  {book_key}: {chapter_count} chapters, {verse_count} verses "
        f"-> v0-prose / v0-eng-baseline / v0-translit-baseline"
    )
    return chapter_count, verse_count


def main():
    ap = argparse.ArgumentParser(
        description="Ingest STEPBible TAHOT TSV files into v0 baseline text files."
    )
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--book",
        metavar="BOOK_KEY",
        help="Ingest a single book by its registry key (e.g. jonah, genesis).",
    )
    group.add_argument(
        "--all-books",
        action="store_true",
        help=(
            "Ingest every book in BOOK_REGISTRY in BHS canonical order. "
            "Books whose TAHOT file is not vendored print a warning and are skipped."
        ),
    )
    args = ap.parse_args()

    if args.book:
        ingest_book(args.book, fatal_on_missing=True)
    else:
        # --all-books
        succeeded = []
        warned = []
        failed = []
        for book_key in BOOK_ORDER:
            print(f"\n=== {book_key} ===")
            result = ingest_book(book_key, fatal_on_missing=False)
            if result is None:
                warned.append(book_key)
            else:
                ch, vs = result
                succeeded.append((book_key, ch, vs))

        print("\n" + "=" * 60)
        print(f"--all-books complete: {len(succeeded)} succeeded, {len(warned)} skipped")
        if succeeded:
            print("\nSucceeded:")
            for book_key, ch, vs in succeeded:
                print(f"  {book_key}: {ch} chapters, {vs} verses")
        if warned:
            print("\nSkipped (TAHOT file not vendored or no verses found):")
            for book_key in warned:
                print(f"  {book_key}")
        if failed:
            print("\nFailed (unexpected errors):")
            for book_key in failed:
                print(f"  {book_key}")


if __name__ == "__main__":
    main()
