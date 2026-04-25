"""
build_books.py - Generate HTML book fragments from colometric Hebrew sources.

Reads chapter files from v4-editorial/{NN-book}/ (preferred) or v1-teamim/{NN-book}/
(fallback) and writes one HTML fragment per book into books/.

The fallback is per-chapter: a chapter that exists in v4-editorial uses that;
chapters that don't fall back to v1-teamim. This means hand-editorial work in
v4 takes effect chapter-by-chapter as it's produced; the rest of the book
ships from the te'amim-parsed baseline.

Each verse becomes a <div class="verse"> with one or more <span class="line">
children, each containing a <span class="he"> for the Hebrew text. No English
layer in the MVP build.

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/build_books.py             # build all books
    PYTHONIOENCODING=utf-8 py -3 scripts/build_books.py --book jonah
"""

import argparse
import html
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
V4_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v4-editorial")
V1_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1-teamim")
OUTPUT_DIR = os.path.join(REPO_ROOT, "books")

VERSE_REF_RE = re.compile(r"^\d+:\d+$")

BOOK_REGISTRY = {
    "jonah": {
        "subdir": "05-jonah",
        "prefix": "jonah",
        "out": "jonah.html",
    },
}


def parse_chapter(filepath):
    """Parse a colometric chapter file into list of verse dicts.

    Returns:
        chapter_num (int)
        verses (list of {"ref": "1:1", "lines": ["...", ...]})
    """
    with open(filepath, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    verses = []
    current = None
    chapter_num = None
    in_verse = False

    for raw in raw_lines:
        line = raw.rstrip("\r\n")
        if VERSE_REF_RE.match(line.strip()):
            if current is not None and current["lines"]:
                verses.append(current)
            ref = line.strip()
            if chapter_num is None:
                chapter_num = int(ref.split(":")[0])
            current = {"ref": ref, "lines": []}
            in_verse = True
            continue
        if line.strip() == "":
            if current is not None and current["lines"]:
                verses.append(current)
                current = None
            continue
        if not in_verse:
            continue
        if current is not None:
            current["lines"].append(line)

    if current is not None and current["lines"]:
        verses.append(current)

    return chapter_num, verses


def render_chapter(chapter_num, verses, source_label):
    out = [f'  <div class="chapter" id="ch-{chapter_num}" data-source="{source_label}">']
    for v in verses:
        ref = v["ref"]
        ch, vn = ref.split(":")
        out.append(f'    <div class="verse" id="v-{ch}-{vn}"><span class="verse-num">{ref}</span>')
        for line in v["lines"]:
            escaped = html.escape(line)
            out.append(f'      <span class="line"><span class="he">{escaped}</span></span>')
        out.append("    </div>")
    out.append("  </div>")
    return "\n".join(out)


def build_book(book_key):
    if book_key not in BOOK_REGISTRY:
        sys.exit(f"Unknown book key: {book_key}")
    spec = BOOK_REGISTRY[book_key]

    v4_dir = os.path.join(V4_DIR, spec["subdir"])
    v1_dir = os.path.join(V1_DIR, spec["subdir"])

    # Discover chapters from whichever tier has them; v4 wins per chapter.
    v4_files = set(
        fn for fn in (os.listdir(v4_dir) if os.path.isdir(v4_dir) else [])
        if fn.startswith(spec["prefix"] + "-") and fn.endswith(".txt")
    )
    v1_files = set(
        fn for fn in (os.listdir(v1_dir) if os.path.isdir(v1_dir) else [])
        if fn.startswith(spec["prefix"] + "-") and fn.endswith(".txt")
    )
    all_files = sorted(v4_files | v1_files)

    if not all_files:
        sys.exit(f"No chapter files found for {book_key} in v4-editorial/ or v1-teamim/")

    fragments = []
    v4_count = 0
    v1_count = 0
    for fn in all_files:
        if fn in v4_files:
            path = os.path.join(v4_dir, fn)
            source_label = "v4-editorial"
            v4_count += 1
        else:
            path = os.path.join(v1_dir, fn)
            source_label = "v1-teamim"
            v1_count += 1
        chapter_num, verses = parse_chapter(path)
        fragments.append(render_chapter(chapter_num, verses, source_label))

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, spec["out"])
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(fragments) + "\n")

    print(f"  wrote {out_path}")
    print(f"  chapters from v4-editorial: {v4_count}")
    print(f"  chapters from v1-teamim:    {v1_count}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", help="Book key; if omitted, build all")
    args = ap.parse_args()

    keys = [args.book] if args.book else list(BOOK_REGISTRY.keys())
    for k in keys:
        build_book(k)


if __name__ == "__main__":
    main()
