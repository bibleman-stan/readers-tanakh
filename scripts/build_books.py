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

# Hebrew tier preference: v4-editorial (hand-edited) > v1-teamim (machine).
V4_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v4-editorial")
V1_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1-teamim")

# English tier preference: eng-gloss (hand-edited) > v1-eng-baseline (TAHOT-derived).
ENG_GLOSS_DIR = os.path.join(REPO_ROOT, "data", "text-files", "eng-gloss")
ENG_BASELINE_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1-eng-baseline")

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


def render_chapter(chapter_num, he_verses, en_lookup, he_source, en_source):
    """Render one chapter as HTML.

    he_verses: [{ref, lines}] from the chosen Hebrew source for this chapter
    en_lookup: {ref: [lines]} from the chosen English source for this chapter,
               or {} if no English layer available
    he_source / en_source: provenance strings for the data-source attributes
    """
    out = [
        f'  <div class="chapter" id="ch-{chapter_num}" '
        f'data-he-source="{he_source}" data-en-source="{en_source}">'
    ]
    for v in he_verses:
        ref = v["ref"]
        ch, vn = ref.split(":")
        en_lines = en_lookup.get(ref, [])
        out.append(f'    <div class="verse" id="v-{ch}-{vn}"><span class="verse-num">{ref}</span>')
        for i, he_line in enumerate(v["lines"]):
            he_esc = html.escape(he_line)
            en_esc = html.escape(en_lines[i]) if i < len(en_lines) else ""
            if en_esc:
                out.append(
                    f'      <span class="line">'
                    f'<span class="he">{he_esc}</span>'
                    f'<span class="en">{en_esc}</span>'
                    f'</span>'
                )
            else:
                out.append(f'      <span class="line"><span class="he">{he_esc}</span></span>')
        out.append("    </div>")
    out.append("  </div>")
    return "\n".join(out)


def _files_in(dir_path, prefix):
    if not os.path.isdir(dir_path):
        return set()
    return {
        fn for fn in os.listdir(dir_path)
        if fn.startswith(prefix + "-") and fn.endswith(".txt")
    }


def build_book(book_key):
    if book_key not in BOOK_REGISTRY:
        sys.exit(f"Unknown book key: {book_key}")
    spec = BOOK_REGISTRY[book_key]
    prefix = spec["prefix"]

    v4_dir = os.path.join(V4_DIR, spec["subdir"])
    v1_dir = os.path.join(V1_DIR, spec["subdir"])
    eng_gloss_dir = os.path.join(ENG_GLOSS_DIR, spec["subdir"])
    eng_baseline_dir = os.path.join(ENG_BASELINE_DIR, spec["subdir"])

    v4_files = _files_in(v4_dir, prefix)
    v1_files = _files_in(v1_dir, prefix)
    eng_gloss_files = _files_in(eng_gloss_dir, prefix)
    eng_baseline_files = _files_in(eng_baseline_dir, prefix)
    all_files = sorted(v4_files | v1_files)

    if not all_files:
        sys.exit(f"No chapter files found for {book_key} in v4-editorial/ or v1-teamim/")

    fragments = []
    counts = {"v4": 0, "v1": 0, "eng_gloss": 0, "eng_baseline": 0, "no_en": 0}
    for fn in all_files:
        # Hebrew source (per chapter): prefer v4, fall back to v1-teamim.
        if fn in v4_files:
            he_path = os.path.join(v4_dir, fn)
            he_source = "v4-editorial"
            counts["v4"] += 1
        else:
            he_path = os.path.join(v1_dir, fn)
            he_source = "v1-teamim"
            counts["v1"] += 1

        # English source (per chapter): prefer eng-gloss, fall back to v1-eng-baseline.
        if fn in eng_gloss_files:
            en_path = os.path.join(eng_gloss_dir, fn)
            en_source = "eng-gloss"
            counts["eng_gloss"] += 1
        elif fn in eng_baseline_files:
            en_path = os.path.join(eng_baseline_dir, fn)
            en_source = "v1-eng-baseline"
            counts["eng_baseline"] += 1
        else:
            en_path = None
            en_source = "none"
            counts["no_en"] += 1

        chapter_num, he_verses = parse_chapter(he_path)
        if en_path:
            _, en_verses = parse_chapter(en_path)
            en_lookup = {v["ref"]: v["lines"] for v in en_verses}
        else:
            en_lookup = {}
        fragments.append(render_chapter(chapter_num, he_verses, en_lookup, he_source, en_source))

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, spec["out"])
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(fragments) + "\n")

    print(f"  wrote {out_path}")
    print(f"  Hebrew  — v4-editorial: {counts['v4']}, v1-teamim: {counts['v1']}")
    print(f"  English — eng-gloss:    {counts['eng_gloss']}, v1-eng-baseline: {counts['eng_baseline']}, none: {counts['no_en']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", help="Book key; if omitted, build all")
    args = ap.parse_args()

    keys = [args.book] if args.book else list(BOOK_REGISTRY.keys())
    for k in keys:
        build_book(k)


if __name__ == "__main__":
    main()
