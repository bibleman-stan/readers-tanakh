"""
ingest_tahot.py - Convert STEPBible TAHOT TSV to v0-prose chapter files.

TAHOT format (one word per line, tab-separated):
    Jon.1.1#01=L    וַֽ/יְהִי֙    va/y.Hi    and/ it came    H9001/{H1961}    Hc/Vqw3ms    ...

We extract:
  - Verse reference (Jon.1.1)
  - Hebrew with niqqud/te'amim (column 2), removing STEP's morphological "/" and
    "\\" prefix/suffix separators while preserving in-text punctuation.

For the v0-prose output, each verse is printed with its reference on one line
followed by the joined Hebrew text on a single line (no editorial line breaks).
This matches the v4-editorial file format used by build_books.py:

    1:1
    {hebrew text of verse 1}

    1:2
    {hebrew text of verse 2}

For MVP shipping, v0-prose is copied to v4-editorial as the starting editorial
state. Real colometric line-breaking happens in v4-editorial as a hand-edit pass.

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/ingest_tahot.py --book jonah
"""

import argparse
import os
import re
import sys
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
TAHOT_DIR = os.path.join(REPO_ROOT, "research", "stepbible-tahot")
V0_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v0-prose")
V0_ENG_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v0-eng-baseline")

# Within v0-eng-baseline, prosodic-word units (which match Hebrew prosodic
# words 1:1, including maqqef-grouped units treated as single words) are
# separated by " | " so the te'amim parser can re-align them at cola
# boundaries derived from the Hebrew accents.
ENG_PWORD_SEP = " | "

BOOK_REGISTRY = {
    "jonah": {
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "tahot_book_code": "Jon",
        "out_subdir": "05-jonah",
        "out_prefix": "jonah",
    },
}

REF_RE = re.compile(
    r"^([A-Za-z0-9]+)\."          # book code
    r"(\d+)\.(\d+)"                # English chapter.verse (NRSV)
    r"(?:\((\d+)\.(\d+)\))?"       # optional (Hebrew chapter.verse) when they differ
    r"#\d+(?:=(.+))?$"             # word index and optional text-type suffix
)


def clean_hebrew(raw):
    """Strip STEP morphological separators while preserving in-text punctuation."""
    cleaned = raw.replace("/", "").replace("\\", "")
    return cleaned


# English-cleanup: TAHOT field 4 carries one English gloss per Hebrew word,
# with morphological structure encoded as:
#   /   separates per-morpheme glosses within one Hebrew word ("and/ it came")
#   \X  punctuation/structural marker after the word ("\link" for maqqef,
#       "\verseEnd" for sof pasuq, "\setuma", "\petucha", etc.)
#   [x] words supplied for translation but not in Hebrew  (KEEP)
#   <x> words in Hebrew that are best omitted in translation (DROP)
ENG_OMIT_BRACKET_RE = re.compile(r"<[^>]*>")


def clean_english(raw):
    """Convert a TAHOT English gloss to a clean per-word string.

    Strips trailing \\marker punctuation annotations, collapses morpheme
    separators, drops <angle-bracketed> words per TAHOT convention, and
    normalizes whitespace. Square-bracketed [supplied] words are preserved.
    """
    if not raw:
        return ""
    head = raw.split("\\", 1)[0]
    head = ENG_OMIT_BRACKET_RE.sub("", head)
    head = head.replace("/", " ")
    return " ".join(head.split())


def parse_tahot_for_book(tahot_path, book_code):
    """Parse the TAHOT file and return ({chapter: {verse: [(he, en) tuples]}}, crosswalk).

    Output uses Hebrew chapter:verse (canon §3 — Hebrew versification primary).
    Each per-verse word entry is a (hebrew_word, english_gloss) tuple so the
    two streams stay aligned at the word level for downstream colometric
    splitting.
    crosswalk maps "heb_ch:heb_v" -> "eng_ch:eng_v" for any verse where the
    two traditions disagree.
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

            # We follow Qere by convention (canon §6). TAHOT's L (Leningrad)
            # entries already have Qere applied as the base reading; K (Ketiv)
            # entries are alternates that should be skipped to avoid double
            # counting words.
            if text_type and "K" in text_type and "L" not in text_type and "Q" not in text_type:
                continue

            hebrew = clean_hebrew(fields[1]) if len(fields) > 1 else ""
            english = clean_english(fields[3]) if len(fields) > 3 else ""
            chapters[heb_ch][heb_v].append((hebrew, english))

    return chapters, crosswalk


MAQQEF = "־"  # ־


def group_prosodic_words(word_pairs):
    """Group TAHOT word entries into prosodic-word units (maqqef-joined groups).

    Returns a list of (hebrew_pword, english_pword) tuples where:
      - hebrew_pword joins maqqef-grouped Hebrew words with no space
      - english_pword joins the corresponding English glosses with a space
    """
    groups = []
    for he, en in word_pairs:
        if not he and not en:
            continue
        if groups and groups[-1][0].endswith(MAQQEF):
            prev_he, prev_en = groups[-1]
            merged_he = prev_he + he
            merged_en = (prev_en + " " + en).strip() if (prev_en and en) else (prev_en or en)
            groups[-1] = (merged_he, merged_en)
        else:
            groups.append((he, en))
    return groups


def write_chapter_files(he_path, en_path, chapter_num, verses):
    """Write one v0-prose Hebrew chapter file and one v0-eng-baseline English chapter file.

    Both files use the same verse-ref / content / blank-line structure. Hebrew
    prosodic-words are space-separated; English prosodic-words use the
    ENG_PWORD_SEP delimiter so the te'amim parser can re-align them at the
    same accent-induced cola boundaries.
    """
    os.makedirs(os.path.dirname(he_path), exist_ok=True)
    os.makedirs(os.path.dirname(en_path), exist_ok=True)
    verse_keys = sorted(verses.keys())
    with open(he_path, "w", encoding="utf-8", newline="\n") as fh, \
         open(en_path, "w", encoding="utf-8", newline="\n") as fe:
        for i, v in enumerate(verse_keys):
            groups = group_prosodic_words(verses[v])
            he_text = " ".join(he for he, _ in groups if he)
            en_text = ENG_PWORD_SEP.join(en for _, en in groups)
            fh.write(f"{chapter_num}:{v}\n")
            fh.write(f"{he_text}\n")
            fe.write(f"{chapter_num}:{v}\n")
            fe.write(f"{en_text}\n")
            if i < len(verse_keys) - 1:
                fh.write("\n")
                fe.write("\n")


def ingest_book(book_key):
    if book_key not in BOOK_REGISTRY:
        sys.exit(f"Unknown book key: {book_key}")
    spec = BOOK_REGISTRY[book_key]
    tahot_path = os.path.join(TAHOT_DIR, spec["tahot_file"])
    if not os.path.exists(tahot_path):
        sys.exit(f"TAHOT file not found: {tahot_path}")

    chapters, crosswalk = parse_tahot_for_book(tahot_path, spec["tahot_book_code"])
    if not chapters:
        sys.exit(f"No verses found for book code {spec['tahot_book_code']!r} in {tahot_path}")

    he_out_dir = os.path.join(V0_DIR, spec["out_subdir"])
    en_out_dir = os.path.join(V0_ENG_DIR, spec["out_subdir"])
    chapter_count = 0
    verse_count = 0
    for chapter_num in sorted(chapters.keys()):
        he_path = os.path.join(he_out_dir, f"{spec['out_prefix']}-{chapter_num:02d}.txt")
        en_path = os.path.join(en_out_dir, f"{spec['out_prefix']}-{chapter_num:02d}.txt")
        write_chapter_files(he_path, en_path, chapter_num, chapters[chapter_num])
        chapter_count += 1
        verse_count += len(chapters[chapter_num])
        print(f"  wrote {he_path}  ({len(chapters[chapter_num])} verses)")
        print(f"  wrote {en_path}")

    if crosswalk:
        crosswalk_path = os.path.join(he_out_dir, f"{spec['out_prefix']}-crosswalk.json")
        import json
        with open(crosswalk_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(crosswalk, f, ensure_ascii=False, indent=2, sort_keys=True)
        print(f"  wrote {crosswalk_path}  ({len(crosswalk)} verse-numbering differences)")

    print(f"\n{book_key}: {chapter_count} chapters, {verse_count} verses ingested into v0-prose/ and v0-eng-baseline/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", required=True, help="Book key (e.g. jonah)")
    args = ap.parse_args()
    ingest_book(args.book)


if __name__ == "__main__":
    main()
