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


def parse_tahot_for_book(tahot_path, book_code):
    """Parse the TAHOT file and return ({chapter: {verse: [words]}}, crosswalk).

    Output uses Hebrew chapter:verse (canon §3 — Hebrew versification primary).
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
            chapters[heb_ch][heb_v].append(hebrew)

    return chapters, crosswalk


MAQQEF = "־"  # ־


def join_words(words):
    """Join words with spaces, except no space after a maqqef."""
    out = []
    for i, w in enumerate(words):
        if not w:
            continue
        if i == 0:
            out.append(w)
        elif out and out[-1].endswith(MAQQEF):
            out[-1] = out[-1] + w
        else:
            out.append(w)
    return " ".join(out)


def write_chapter_file(out_path, chapter_num, verses):
    """Write one v0-prose chapter file."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        verse_keys = sorted(verses.keys())
        for i, v in enumerate(verse_keys):
            words = verses[v]
            hebrew_text = join_words(words)
            f.write(f"{chapter_num}:{v}\n")
            f.write(f"{hebrew_text}\n")
            if i < len(verse_keys) - 1:
                f.write("\n")


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

    out_dir = os.path.join(V0_DIR, spec["out_subdir"])
    chapter_count = 0
    verse_count = 0
    for chapter_num in sorted(chapters.keys()):
        out_path = os.path.join(out_dir, f"{spec['out_prefix']}-{chapter_num:02d}.txt")
        write_chapter_file(out_path, chapter_num, chapters[chapter_num])
        chapter_count += 1
        verse_count += len(chapters[chapter_num])
        print(f"  wrote {out_path}  ({len(chapters[chapter_num])} verses)")

    if crosswalk:
        crosswalk_path = os.path.join(out_dir, f"{spec['out_prefix']}-crosswalk.json")
        import json
        with open(crosswalk_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(crosswalk, f, ensure_ascii=False, indent=2, sort_keys=True)
        print(f"  wrote {crosswalk_path}  ({len(crosswalk)} verse-numbering differences)")

    print(f"\n{book_key}: {chapter_count} chapters, {verse_count} verses ingested into v0-prose/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", required=True, help="Book key (e.g. jonah)")
    args = ap.parse_args()
    ingest_book(args.book)


if __name__ == "__main__":
    main()
