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

BOOK_REGISTRY = {
    "jonah": {
        "tahot_file": "TAHOT_Isa-Mal.txt",
        "tahot_book_code": "Jon",
        "out_subdir": "05-jonah",
        "out_prefix": "jonah",
    },
}

REF_RE = re.compile(
    r"^([A-Za-z0-9]+)\."
    r"(\d+)\.(\d+)"
    r"(?:\((\d+)\.(\d+)\))?"
    r"#\d+(?:=(.+))?$"
)

ENG_OMIT_BRACKET_RE = re.compile(r"<[^>]*>")


def clean_hebrew(raw):
    """Strip STEP morphological / and \\ separators; preserve in-text punctuation."""
    return raw.replace("/", "").replace("\\", "")


def clean_english(raw):
    """Convert TAHOT field 4 to a clean per-word string.

    Drops trailing \\marker annotations; collapses morpheme separators;
    drops <angle-bracketed> words per TAHOT convention; preserves
    [square-bracketed] supplied words for the interlinear layer (the
    naturalizer in parse_teamim strips them downstream for the smooth
    gloss).
    """
    if not raw:
        return ""
    head = raw.split("\\", 1)[0]
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
    # both terminators on words like לֹא־).
    head = re.sub(r"-$", "", head)
    head = re.sub(r"^'+", "", head)
    head = re.sub(r"'+$", "", head)
    if is_proper and head:
        head = head[0].upper() + head[1:]
    return head


def parse_tahot_for_book(tahot_path, book_code):
    """Parse TAHOT for a book.

    Returns ({chapter: {verse: [{he, en, translit, joins_next}]}}, crosswalk).
    Each list entry is one ORTHOGRAPHIC word; joins_next=True iff the Hebrew
    word ends in maqqef.
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
    words concatenated without space — the maqqef glyph fills the join
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


def ingest_book(book_key):
    if book_key not in BOOK_REGISTRY:
        sys.exit(f"Unknown book key: {book_key}")
    spec = BOOK_REGISTRY[book_key]
    tahot_path = os.path.join(TAHOT_DIR, spec["tahot_file"])
    if not os.path.exists(tahot_path):
        sys.exit(f"TAHOT file not found: {tahot_path}")

    chapters, crosswalk = parse_tahot_for_book(tahot_path, spec["tahot_book_code"])
    if not chapters:
        sys.exit(f"No verses found for book code {spec['tahot_book_code']!r}")

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
        print(f"  wrote {crosswalk_path} ({len(crosswalk)} verse-numbering differences)")

    print(
        f"\n{book_key}: {chapter_count} chapters, {verse_count} verses "
        f"-> v0-prose / v0-eng-baseline / v0-translit-baseline"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", required=True)
    args = ap.parse_args()
    ingest_book(args.book)


if __name__ == "__main__":
    main()
