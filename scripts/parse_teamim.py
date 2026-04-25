"""
parse_teamim.py - Te'amim-driven colometric break generator.

Reads v0-prose chapter files and produces v1-teamim chapter files where each
line break corresponds to a major disjunctive cantillation accent. Two accent
systems are supported:

  - Prose accents (used by 21 books): break at atnach, segolta, zaqef qaton,
    zaqef gadol, tifcha (revia conservatively excluded by default to avoid
    over-breaking; can be enabled per book).

  - Sifrei Emet accents (Psalms, Proverbs, and Job 3:1-42:6): break at atnach,
    oleh, dechi, revia mugrash. Note that tsinor and pazer in poetic position
    are not currently treated as breakers in this minimal parser.

This is a minimal parser. It does not implement the full Wickes hierarchy with
governing-domain logic. It splits on the presence of specific Unicode codepoints
that mark tier-1 and tier-2 disjunctives. Refinement is iterative: as
override-rate hot-spots emerge in v4-editorial review, the parser's break set
is tuned.

The parser preserves all niqqud, te'amim, and inline punctuation. It only
inserts line breaks. Word integrity (including maqqef-joined groups) is never
broken: a break is only inserted at a whitespace boundary AFTER a word whose
final character cluster contains a breaker accent.

Petucha/setuma paragraph markers (the standalone letters Peh and Samekh that
appear after sof-pasuq in the source) are stripped from the v1 output. They
are recorded structurally elsewhere (TODO: paragraph markers file).

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/parse_teamim.py --book jonah
"""

import argparse
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
V0_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v0-prose")
V1_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1-teamim")

# Tier-1/2 disjunctive accents — prose books
PROSE_BREAKERS = {
    "֑",  # ETNAHTA  (atnach) — tier 1, mid-verse
    "֒",  # SEGOL    (segolta) — tier 2
    "֔",  # ZAQEF QATAN — tier 2
    "֕",  # ZAQEF GADOL — tier 2
    "֖",  # TIPEHA   (tifcha) — tier 2
}

# Tier-1/2 disjunctive accents — Sifrei Emet (Psalms, Proverbs, poetic Job)
POETIC_BREAKERS = {
    "֑",  # ETNAHTA — tier 1
    "֫",  # OLE      (component of oleh ve-yored) — tier 2
    "֭",  # DEHI     (dechi) — tier 2
    "֗",  # REVIA    (revia mugrash in poetic position) — tier 2
}

# Petucha / setuma standalone letters that may follow a sof-pasuq in the source.
PARAGRAPH_MARKERS_RE = re.compile(r"\s+[פס]\s*$")  # trailing PEH or SAMEKH

VERSE_REF_RE = re.compile(r"^\d+:\d+$")

BOOK_REGISTRY = {
    "jonah": {
        "subdir": "05-jonah",
        "prefix": "jonah",
        # Jonah 1, 3, 4 are prose; chapter 2 is the Sifrei-Emet prayer.
        "poetic_chapters": [2],
    },
}


def split_verse_at_breakers(text, breakers):
    """Split a verse string into colometric lines at te'amim breakers.

    A break is inserted after any whitespace-separated word whose characters
    include one of the breaker codepoints. Maqqef-joined groups are atomic.
    """
    words = text.split(" ")
    lines = []
    current = []
    for w in words:
        if not w:
            continue
        current.append(w)
        if any(b in w for b in breakers):
            lines.append(" ".join(current))
            current = []
    if current:
        lines.append(" ".join(current))
    return lines


def strip_paragraph_marker(verse_text):
    """Remove trailing standalone Peh / Samekh paragraph marker."""
    return PARAGRAPH_MARKERS_RE.sub("", verse_text)


def parse_chapter_file(in_path, out_path, breakers):
    with open(in_path, "r", encoding="utf-8") as f:
        raw = f.read()

    # The v0-prose format is verse-ref / verse-text / blank line repeating.
    blocks = re.split(r"\n\s*\n", raw.strip())
    out_blocks = []
    for block in blocks:
        block_lines = block.strip().split("\n", 1)
        if len(block_lines) != 2:
            continue
        ref, verse_text = block_lines
        if not VERSE_REF_RE.match(ref.strip()):
            continue
        cleaned = strip_paragraph_marker(verse_text.strip())
        cola = split_verse_at_breakers(cleaned, breakers)
        out_blocks.append(ref.strip() + "\n" + "\n".join(cola))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n\n".join(out_blocks) + "\n")


def parse_book(book_key):
    if book_key not in BOOK_REGISTRY:
        sys.exit(f"Unknown book key: {book_key}")
    spec = BOOK_REGISTRY[book_key]
    in_dir = os.path.join(V0_DIR, spec["subdir"])
    out_dir = os.path.join(V1_DIR, spec["subdir"])

    if not os.path.isdir(in_dir):
        sys.exit(f"v0-prose dir not found: {in_dir}")

    chapter_files = sorted(
        fn for fn in os.listdir(in_dir)
        if fn.startswith(spec["prefix"] + "-") and fn.endswith(".txt")
    )

    poetic_chapters = set(spec.get("poetic_chapters", []))
    total_lines = 0

    for fn in chapter_files:
        chapter_num = int(fn[len(spec["prefix"]) + 1:-4])
        breakers = POETIC_BREAKERS if chapter_num in poetic_chapters else PROSE_BREAKERS
        in_path = os.path.join(in_dir, fn)
        out_path = os.path.join(out_dir, fn)
        parse_chapter_file(in_path, out_path, breakers)

        with open(out_path, "r", encoding="utf-8") as f:
            line_count = sum(1 for line in f if line.strip() and not VERSE_REF_RE.match(line.strip()))
        total_lines += line_count
        accent_label = "Sifrei Emet" if chapter_num in poetic_chapters else "prose"
        print(f"  wrote {out_path}  ({line_count} cola, {accent_label} accents)")

    print(f"\n{book_key}: {total_lines} cola total in v1-teamim/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", required=True)
    args = ap.parse_args()
    parse_book(args.book)


if __name__ == "__main__":
    main()
