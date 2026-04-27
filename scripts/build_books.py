"""
build_books.py - Generate four-layer HTML book fragments from tier sources.

Per-chapter source preference (independent for each layer; falls through):

  Hebrew:       v4-editorial/  >  v3-he-colometry/  >  v2-he-syntax/  >  v1-he-baseline/
  Interlinear:  eng-interlinear/      > v1-eng-interlinear/
  Gloss:        eng-gloss/            > v1-eng-gloss/
  Translit:     translit/             > v1-translit/

The Hebrew cascade reflects the four-tier pipeline (canon §6 + handoffs/03-architecture.md):
v1 = te'amim baseline draft, v2 = Layer 1 syntax-applied, v3 = Layer 3 colometry-applied,
v4 = editorial gold standard. The cascade picks the most-refined version that exists
per chapter, independent across chapters.

Each cola is rendered with per-orthographic-word spans so the four-layer
reader UI can align Hebrew word N with translit word N and interlinear
word N spatially:

    <span class="line">
      <span class="he">
        <span>WORD1</span> <span>WORD2-</span><span>WORD3</span>
      </span>
      <span class="translit"><span class="w">w1</span><span class="w joined">w2</span><span class="w">w3</span></span>
      <span class="en-inter"><span class="w">w1</span><span class="w joined">w2</span><span class="w">w3</span></span>
      <span class="en-gloss">smooth gloss text for the cola</span>
    </span>

The .joined class on a translit/interlinear word means "this Hebrew word
ends in maqqef and is prosodically joined to the next" — CSS uses it to
render a tighter dot rather than the standard arrow between this word
and its right-side visual neighbor.

Hebrew render: each orthographic word is a span. Maqqef-joined words have
NO whitespace between source spans (the maqqef glyph itself bridges them).
Non-joined adjacent words have a whitespace text node between (rendered space).
"""

import argparse
import html
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

V4_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v4-editorial")
V3_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v3-he-colometry")
V2_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v2-he-syntax")
V1_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1-he-baseline")

INTER_HAND_DIR = os.path.join(REPO_ROOT, "data", "text-files", "eng-interlinear")
INTER_V2_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v2-eng-interlinear")
INTER_V1_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1-eng-interlinear")

GLOSS_HAND_DIR = os.path.join(REPO_ROOT, "data", "text-files", "eng-gloss")
GLOSS_V2_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v2-eng-gloss")
GLOSS_V1_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1-eng-gloss")

TRANSLIT_HAND_DIR = os.path.join(REPO_ROOT, "data", "text-files", "translit")
TRANSLIT_V2_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v2-translit")
TRANSLIT_V1_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1-translit")

OUTPUT_DIR = os.path.join(REPO_ROOT, "books")

ENG_WORD_SEP = " | "
MAQQEF = "־"

VERSE_REF_RE = re.compile(r"^\d+:\d+$")

BOOK_REGISTRY = {
    "jonah": {
        "subdir": "05-jonah",
        "prefix": "jonah",
        "out": "jonah.html",
    },
}


def parse_chapter_lines(filepath):
    """Parse a v1/v4 .txt file into [{ref, lines}]."""
    if not filepath or not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    verses = []
    current = None
    for raw in raw_lines:
        line = raw.rstrip("\r\n")
        if VERSE_REF_RE.match(line.strip()):
            if current is not None and current["lines"]:
                verses.append(current)
            current = {"ref": line.strip(), "lines": []}
            continue
        if line.strip() == "":
            if current is not None and current["lines"]:
                verses.append(current)
                current = None
            continue
        if current is not None:
            current["lines"].append(line)
    if current is not None and current["lines"]:
        verses.append(current)
    return verses


def split_hebrew_cola_to_words(cola_line):
    """Split a Hebrew cola into ordered [{he, joins_next}] orthographic-word records."""
    out = []
    pwords = [p for p in cola_line.split(" ") if p]
    for pw in pwords:
        if MAQQEF in pw:
            parts = pw.split(MAQQEF)
            for p in parts[:-1]:
                out.append({"he": p + MAQQEF, "joins_next": True})
            out.append({"he": parts[-1], "joins_next": False})
        else:
            out.append({"he": pw, "joins_next": False})
    return out


def render_he_layer(words):
    parts = ['<span class="he">']
    for i, w in enumerate(words):
        parts.append(f'<span>{html.escape(w["he"])}</span>')
        if i < len(words) - 1 and not w["joins_next"]:
            parts.append(" ")
    parts.append('</span>')
    return "".join(parts)


def render_word_layer(cls, units, joins):
    """Render translit/en-inter as per-word .w spans.

    units: list of orthographic-word strings (must match joins length)
    joins: list of bool (joins_next) parallel to units
    """
    if not units:
        return ""
    parts = [f'<span class="{cls}">']
    for i, u in enumerate(units):
        joined_cls = " joined" if i < len(joins) and joins[i] else ""
        parts.append(f'<span class="w{joined_cls}">{html.escape(u)}</span>')
    parts.append('</span>')
    return "".join(parts)


def render_chapter(chapter_num, he_verses, inter_lookup, gloss_lookup, tr_lookup, sources):
    out = [
        f'  <div class="chapter" id="ch-{chapter_num}" '
        f'data-he-source="{sources["he"]}" '
        f'data-inter-source="{sources["inter"]}" '
        f'data-gloss-source="{sources["gloss"]}" '
        f'data-translit-source="{sources["translit"]}">'
    ]

    for v in he_verses:
        ref = v["ref"]
        ch, vn = ref.split(":")
        out.append(f'    <div class="verse" id="v-{ch}-{vn}"><span class="verse-num">{ref}</span>')

        inter_lines = inter_lookup.get(ref, [])
        gloss_lines = gloss_lookup.get(ref, [])
        tr_lines = tr_lookup.get(ref, [])

        for i, he_cola in enumerate(v["lines"]):
            words = split_hebrew_cola_to_words(he_cola)
            joins = [w["joins_next"] for w in words]

            inter_units = (
                [u.strip() for u in inter_lines[i].split(ENG_WORD_SEP)]
                if i < len(inter_lines) else []
            )
            tr_units = (
                [u.strip() for u in tr_lines[i].split(ENG_WORD_SEP)]
                if i < len(tr_lines) else []
            )
            gloss_text = gloss_lines[i] if i < len(gloss_lines) else ""

            out.append('      <span class="line">')
            out.append('        ' + render_he_layer(words))
            if tr_units:
                out.append('        ' + render_word_layer("translit", tr_units, joins))
            if inter_units:
                out.append('        ' + render_word_layer("en-inter", inter_units, joins))
            if gloss_text:
                out.append(f'        <span class="en-gloss">{html.escape(gloss_text)}</span>')
            out.append('      </span>')

        out.append('    </div>')

    out.append('  </div>')
    return "\n".join(out)


def _files_in(dir_path, prefix):
    if not os.path.isdir(dir_path):
        return set()
    return {
        fn for fn in os.listdir(dir_path)
        if fn.startswith(prefix + "-") and fn.endswith(".txt")
    }


def lines_to_lookup(verses):
    return {v["ref"]: v["lines"] for v in verses}


def _pick_source(
    fn,
    hand_dir, hand_files,
    v2_dir, v2_files,
    v1_dir, v1_files,
    hand_label, v2_label, v1_label,
):
    """Return (path, source_label, tier_used) for a file.

    Cascade: hand-edit → v2 (apply_v2 mechanical output) → v1 (parse_teamim baseline).
    tier_used is one of: "hand", "v2", "v1", or "none".
    """
    if fn in hand_files:
        return os.path.join(hand_dir, fn), hand_label, "hand"
    if fn in v2_files:
        return os.path.join(v2_dir, fn), v2_label, "v2"
    if fn in v1_files:
        return os.path.join(v1_dir, fn), v1_label, "v1"
    return None, "none", "none"


def build_book(book_key):
    if book_key not in BOOK_REGISTRY:
        sys.exit(f"Unknown book key: {book_key}")
    spec = BOOK_REGISTRY[book_key]
    prefix = spec["prefix"]
    sub = spec["subdir"]

    # Discover chapters by Hebrew layer (Hebrew is required). Cascade
    # picks the most-refined available tier per chapter independently.
    v4_dir = os.path.join(V4_DIR, sub)
    v3_dir = os.path.join(V3_DIR, sub)
    v2_dir = os.path.join(V2_DIR, sub)
    v1_dir = os.path.join(V1_DIR, sub)
    v4_files = _files_in(v4_dir, prefix)
    v3_files = _files_in(v3_dir, prefix)
    v2_files = _files_in(v2_dir, prefix)
    v1_files = _files_in(v1_dir, prefix)
    all_files = sorted(v4_files | v3_files | v2_files | v1_files)

    if not all_files:
        sys.exit(f"No Hebrew chapter files for {book_key}")

    inter_hand = os.path.join(INTER_HAND_DIR, sub)
    inter_v2 = os.path.join(INTER_V2_DIR, sub)
    inter_v1 = os.path.join(INTER_V1_DIR, sub)
    gloss_hand = os.path.join(GLOSS_HAND_DIR, sub)
    gloss_v2 = os.path.join(GLOSS_V2_DIR, sub)
    gloss_v1 = os.path.join(GLOSS_V1_DIR, sub)
    tr_hand = os.path.join(TRANSLIT_HAND_DIR, sub)
    tr_v2 = os.path.join(TRANSLIT_V2_DIR, sub)
    tr_v1 = os.path.join(TRANSLIT_V1_DIR, sub)

    inter_hand_files = _files_in(inter_hand, prefix)
    inter_v2_files = _files_in(inter_v2, prefix)
    inter_v1_files = _files_in(inter_v1, prefix)
    gloss_hand_files = _files_in(gloss_hand, prefix)
    gloss_v2_files = _files_in(gloss_v2, prefix)
    gloss_v1_files = _files_in(gloss_v1, prefix)
    tr_hand_files = _files_in(tr_hand, prefix)
    tr_v2_files = _files_in(tr_v2, prefix)
    tr_v1_files = _files_in(tr_v1, prefix)

    fragments = []
    counts = {
        "he_v4": 0, "he_v3": 0, "he_v2": 0, "he_v1": 0,
        "inter_hand": 0, "inter_v2": 0, "inter_v1": 0, "inter_none": 0,
        "gloss_hand": 0, "gloss_v2": 0, "gloss_v1": 0, "gloss_none": 0,
        "tr_hand": 0, "tr_v2": 0, "tr_v1": 0, "tr_none": 0,
    }

    for fn in all_files:
        # Hebrew (required). Cascade through tiers in canonical order.
        if fn in v4_files:
            he_path, he_source = os.path.join(v4_dir, fn), "v4-editorial"
            counts["he_v4"] += 1
        elif fn in v3_files:
            he_path, he_source = os.path.join(v3_dir, fn), "v3-he-colometry"
            counts["he_v3"] += 1
        elif fn in v2_files:
            he_path, he_source = os.path.join(v2_dir, fn), "v2-he-syntax"
            counts["he_v2"] += 1
        else:
            he_path, he_source = os.path.join(v1_dir, fn), "v1-he-baseline"
            counts["he_v1"] += 1

        inter_path, inter_source, inter_tier = _pick_source(
            fn,
            inter_hand, inter_hand_files,
            inter_v2, inter_v2_files,
            inter_v1, inter_v1_files,
            "eng-interlinear", "v2-eng-interlinear", "v1-eng-interlinear",
        )
        counts[f"inter_{inter_tier if inter_tier != 'none' else 'none'}"] += 1

        gloss_path, gloss_source, gloss_tier = _pick_source(
            fn,
            gloss_hand, gloss_hand_files,
            gloss_v2, gloss_v2_files,
            gloss_v1, gloss_v1_files,
            "eng-gloss", "v2-eng-gloss", "v1-eng-gloss",
        )
        counts[f"gloss_{gloss_tier if gloss_tier != 'none' else 'none'}"] += 1

        tr_path, tr_source, tr_tier = _pick_source(
            fn,
            tr_hand, tr_hand_files,
            tr_v2, tr_v2_files,
            tr_v1, tr_v1_files,
            "translit", "v2-translit", "v1-translit",
        )
        counts[f"tr_{tr_tier if tr_tier != 'none' else 'none'}"] += 1

        he_verses = parse_chapter_lines(he_path)
        chapter_num = int(he_verses[0]["ref"].split(":")[0]) if he_verses else 0

        inter_lookup = lines_to_lookup(parse_chapter_lines(inter_path)) if inter_path else {}
        gloss_lookup = lines_to_lookup(parse_chapter_lines(gloss_path)) if gloss_path else {}
        tr_lookup = lines_to_lookup(parse_chapter_lines(tr_path)) if tr_path else {}

        sources = {
            "he": he_source, "inter": inter_source,
            "gloss": gloss_source, "translit": tr_source,
        }
        fragments.append(
            render_chapter(chapter_num, he_verses, inter_lookup, gloss_lookup, tr_lookup, sources)
        )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, spec["out"])
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(fragments) + "\n")

    print(f"  wrote {out_path}")
    print(f"  Hebrew      v4: {counts['he_v4']}  v3: {counts['he_v3']}  v2: {counts['he_v2']}  v1: {counts['he_v1']}")
    print(f"  Interlinear hand: {counts['inter_hand']}  v2: {counts['inter_v2']}  v1: {counts['inter_v1']}  none: {counts['inter_none']}")
    print(f"  Gloss       hand: {counts['gloss_hand']}  v2: {counts['gloss_v2']}  v1: {counts['gloss_v1']}  none: {counts['gloss_none']}")
    print(f"  Translit    hand: {counts['tr_hand']}  v2: {counts['tr_v2']}  v1: {counts['tr_v1']}  none: {counts['tr_none']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", help="Book key; if omitted, build all")
    args = ap.parse_args()
    keys = [args.book] if args.book else list(BOOK_REGISTRY.keys())
    for k in keys:
        build_book(k)


if __name__ == "__main__":
    main()
