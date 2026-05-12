"""
build_books.py - Generate three-layer HTML book fragments from tier sources.

Per-chapter source preference (independent for each layer; falls through):

  Hebrew:       v2/he/             > v1/he-baseline/
  Interlinear:  v2/eng-interlinear/ > v1/eng-interlinear/
  KJV English:  v2/eng-kjv/         (no v1 fallback — Wave 6-OT substrate)
  Translit:     v2/translit/        > v1/translit/

The Hebrew cascade reflects the collapsed two-tier pipeline (canon §6 +
handoffs/03-architecture.md): v1 = te'amim baseline draft, v2 = editorial
gold standard. The cascade picks the most-refined version that exists per
chapter, independent across chapters.

Each cola is rendered with per-orthographic-word spans so the multi-layer
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

OUTPUT LAYOUT (per-chapter, deprecating monolithic):
  books/<slug>/manifest.json          — {book_name, chapters: [1,2,...,N]}
  books/<slug>/<slug>-<NN>.html       — single <div class="chapter"> block per chapter

The monolithic books/<slug>.html files are no longer emitted. The client
fetches one chapter at a time via per-chapter URLs, with adjacent-chapter
prefetching for snappy navigation.
"""

import argparse
import html
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

# Wave 3β — atu-method swap module path (sibling repo, sys.path-inserted on
# demand for the kjv build path only; legacy path imports nothing).
ATU_METHOD_ROOT = os.path.normpath(os.path.join(REPO_ROOT, "..", "atu-method"))

V2_HE_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v2", "he")
V1_HE_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1", "he-baseline")

INTER_V2_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v2", "eng-interlinear")
INTER_V1_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1", "eng-interlinear")

GLOSS_V2_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v2", "eng-kjv")
GLOSS_V1_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1", "eng-gloss")

# Wave 6-OT: KJV-anchored English is now the only path. The v2/eng-kjv/
# directory holds KJV-verbatim text emitted by scripts/regenerate_english.py
# (one English line per Hebrew cola, 4-layer-integrity preserved). Renamed
# from v2/eng-gloss → v2/eng-kjv 2026-05-12 to reflect the actual substrate
# (KJV verbatim, not a Macula-style structural gloss). v1/eng-gloss kept
# its name — that tier IS legacy Macula structural gloss.

TRANSLIT_V2_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v2", "translit")
TRANSLIT_V1_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1", "translit")

OUTPUT_DIR = os.path.join(REPO_ROOT, "books")

ENG_WORD_SEP = " | "
MAQQEF = "־"

VERSE_REF_RE = re.compile(r"^\d+:\d+$")

BOOK_REGISTRY = {
    "genesis":      {"subdir": "01-genesis",      "prefix": "genesis",      "out": "genesis.html"},
    "exodus":       {"subdir": "02-exodus",        "prefix": "exodus",       "out": "exodus.html"},
    "leviticus":    {"subdir": "03-leviticus",     "prefix": "leviticus",    "out": "leviticus.html"},
    "numbers":      {"subdir": "04-numbers",       "prefix": "numbers",      "out": "numbers.html"},
    "deuteronomy":  {"subdir": "05-deuteronomy",   "prefix": "deuteronomy",  "out": "deuteronomy.html"},
    "joshua":       {"subdir": "06-joshua",        "prefix": "joshua",       "out": "joshua.html"},
    "judges":       {"subdir": "07-judges",        "prefix": "judges",       "out": "judges.html"},
    "ruth":         {"subdir": "08-ruth",          "prefix": "ruth",         "out": "ruth.html"},
    "1samuel":      {"subdir": "09-1samuel",       "prefix": "1samuel",      "out": "1samuel.html"},
    "2samuel":      {"subdir": "10-2samuel",       "prefix": "2samuel",      "out": "2samuel.html"},
    "1kings":       {"subdir": "11-1kings",        "prefix": "1kings",       "out": "1kings.html"},
    "2kings":       {"subdir": "12-2kings",        "prefix": "2kings",       "out": "2kings.html"},
    "1chronicles":  {"subdir": "13-1chronicles",   "prefix": "1chronicles",  "out": "1chronicles.html"},
    "2chronicles":  {"subdir": "14-2chronicles",   "prefix": "2chronicles",  "out": "2chronicles.html"},
    "ezra":         {"subdir": "15-ezra",          "prefix": "ezra",         "out": "ezra.html"},
    "nehemiah":     {"subdir": "16-nehemiah",      "prefix": "nehemiah",     "out": "nehemiah.html"},
    "esther":       {"subdir": "17-esther",        "prefix": "esther",       "out": "esther.html"},
    "job":          {"subdir": "18-job",           "prefix": "job",          "out": "job.html"},
    "psalms":       {"subdir": "19-psalms",        "prefix": "psalms",       "out": "psalms.html"},
    "proverbs":     {"subdir": "20-proverbs",      "prefix": "proverbs",     "out": "proverbs.html"},
    "ecclesiastes": {"subdir": "21-ecclesiastes",  "prefix": "ecclesiastes", "out": "ecclesiastes.html"},
    "songofsongs":  {"subdir": "22-songofsongs",   "prefix": "songofsongs",  "out": "songofsongs.html"},
    "isaiah":       {"subdir": "23-isaiah",        "prefix": "isaiah",       "out": "isaiah.html"},
    "jeremiah":     {"subdir": "24-jeremiah",      "prefix": "jeremiah",     "out": "jeremiah.html"},
    "lamentations": {"subdir": "25-lamentations",  "prefix": "lamentations", "out": "lamentations.html"},
    "ezekiel":      {"subdir": "26-ezekiel",       "prefix": "ezekiel",      "out": "ezekiel.html"},
    "daniel":       {"subdir": "27-daniel",        "prefix": "daniel",       "out": "daniel.html"},
    "hosea":        {"subdir": "28-hosea",         "prefix": "hosea",        "out": "hosea.html"},
    "joel":         {"subdir": "29-joel",          "prefix": "joel",         "out": "joel.html"},
    "amos":         {"subdir": "30-amos",          "prefix": "amos",         "out": "amos.html"},
    "obadiah":      {"subdir": "31-obadiah",       "prefix": "obadiah",      "out": "obadiah.html"},
    "jonah":        {"subdir": "32-jonah",         "prefix": "jonah",        "out": "jonah.html"},
    "micah":        {"subdir": "33-micah",         "prefix": "micah",        "out": "micah.html"},
    "nahum":        {"subdir": "34-nahum",         "prefix": "nahum",        "out": "nahum.html"},
    "habakkuk":     {"subdir": "35-habakkuk",      "prefix": "habakkuk",     "out": "habakkuk.html"},
    "zephaniah":    {"subdir": "36-zephaniah",     "prefix": "zephaniah",    "out": "zephaniah.html"},
    "haggai":       {"subdir": "37-haggai",        "prefix": "haggai",       "out": "haggai.html"},
    "zechariah":    {"subdir": "38-zechariah",     "prefix": "zechariah",    "out": "zechariah.html"},
    "malachi":      {"subdir": "39-malachi",       "prefix": "malachi",      "out": "malachi.html"},
}


def parse_chapter_lines(filepath):
    """Parse a v1/v2 .txt file into [{ref, lines}]."""
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


# ---------------------------------------------------------------------------
# OT swap pipeline — wraps archaic tokens in the .en-gloss row with
# <span class="swap"> markup so the Modern pill can toggle archaic→modern.
# Wave 6-OT: this is unconditional (KJV is the only English path now); the
# atu-method universal swap engine + OT swap list is the substrate.
# ---------------------------------------------------------------------------
_SWAP_CACHE: dict = {}


def _load_ot_swap_pipeline():
    """Lazy-load the atu-method swap engine + OT corpus swap list.

    Returns (apply_swaps_fn, swap_pairs, quiet_set). Cached after first call
    so per-line apply_swaps() invocations hit the engine cache too.
    """
    if "loaded" in _SWAP_CACHE:
        return _SWAP_CACHE["loaded"]
    if ATU_METHOD_ROOT not in sys.path:
        sys.path.insert(0, ATU_METHOD_ROOT)
    from atu_method.swaps import apply_swaps, load_corpus_swap_list
    swap_pairs, quiet_set = load_corpus_swap_list("ot")
    _SWAP_CACHE["loaded"] = (apply_swaps, swap_pairs, quiet_set)
    return _SWAP_CACHE["loaded"]


def render_chapter(chapter_num, he_verses, inter_lookup, gloss_lookup, tr_lookup, sources,
                   gloss_html_renderer=None):
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
                # gloss_html_renderer wraps archaic tokens in <span class="swap"> markup
                # when the kjv build path is active; legacy path uses the safe escape.
                # CRITICAL invariant: the .swap spans are emitted INSIDE the .en-gloss
                # wrapper only. The .he / .translit / .en-inter rows render via separate
                # code paths (render_he_layer, render_word_layer) that never touch swaps.
                if gloss_html_renderer is not None:
                    gloss_inner = gloss_html_renderer(gloss_text)
                else:
                    gloss_inner = html.escape(gloss_text)
                out.append(f'        <span class="en-gloss">{gloss_inner}</span>')
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
    v2_dir, v2_files,
    v1_dir, v1_files,
    v2_label, v1_label,
):
    """Return (path, source_label, tier_used) for a per-word layer file.

    Cascade: v2 (editorial / propagator output) → v1 (parse_teamim baseline).
    tier_used is one of: "v2", "v1", or "none".
    """
    if fn in v2_files:
        return os.path.join(v2_dir, fn), v2_label, "v2"
    if fn in v1_files:
        return os.path.join(v1_dir, fn), v1_label, "v1"
    return None, "none", "none"


def build_book(book_key, skip_missing=False):
    """Build per-chapter HTML files and a manifest for a single book.

    Wave 6-OT: the English layer is KJV-verbatim (read from v2/eng-kjv/,
    emitted by scripts/regenerate_english.py). The atu-method universal
    swap pipeline wraps archaic tokens in <span class="swap"> markup so the
    Modern pill can toggle archaic→modern at runtime — the .swap markup
    is emitted ONLY inside the .en-gloss row. Hebrew / transliteration /
    interlinear layers render via separate code paths that never emit
    .swap spans; this is the 4-layer integrity invariant.

    The Macula-Hebrew structural-gloss path (legacy English-source) and the
    sibling books-kjv/ output tree were retired in the same wave.

    Emits:
      books/<slug>/manifest.json              — {book_name, chapters: [...]}
      books/<slug>/<slug>-<NN>.html           — one file per chapter

    Returns True on success, False when source files are absent and
    skip_missing=True (used by --all-books).  With skip_missing=False
    (default, --book mode) a missing book exits the process.
    """
    if book_key not in BOOK_REGISTRY:
        sys.exit(f"Unknown book key: {book_key}")
    spec = BOOK_REGISTRY[book_key]
    prefix = spec["prefix"]
    sub = spec["subdir"]

    # Discover chapters by Hebrew layer (Hebrew is required). Cascade
    # picks the most-refined available tier per chapter independently.
    v2_he_dir = os.path.join(V2_HE_DIR, sub)
    v1_he_dir = os.path.join(V1_HE_DIR, sub)
    v2_he_files = _files_in(v2_he_dir, prefix)
    v1_he_files = _files_in(v1_he_dir, prefix)
    all_files = sorted(v2_he_files | v1_he_files)

    if not all_files:
        if skip_missing:
            return False
        sys.exit(f"No Hebrew chapter files for {book_key}")

    inter_v2 = os.path.join(INTER_V2_DIR, sub)
    inter_v1 = os.path.join(INTER_V1_DIR, sub)
    # English layer is KJV-verbatim from v2/eng-kjv/. No v1 fallback —
    # the KJV substrate is a Wave-5c/6 deliverable that has no v1 tier.
    gloss_v2 = os.path.join(GLOSS_V2_DIR, sub)
    gloss_v1 = os.path.join(GLOSS_V1_DIR, sub)  # unused (no v1 KJV tier)
    tr_v2 = os.path.join(TRANSLIT_V2_DIR, sub)
    tr_v1 = os.path.join(TRANSLIT_V1_DIR, sub)

    inter_v2_files = _files_in(inter_v2, prefix)
    inter_v1_files = _files_in(inter_v1, prefix)
    gloss_v2_files = _files_in(gloss_v2, prefix)
    gloss_v1_files = set()  # no v1 fallback for the KJV gloss substrate
    tr_v2_files = _files_in(tr_v2, prefix)
    tr_v1_files = _files_in(tr_v1, prefix)

    counts = {
        "he_v2": 0, "he_v1": 0,
        "inter_v2": 0, "inter_v1": 0, "inter_none": 0,
        "gloss_v2": 0, "gloss_v1": 0, "gloss_none": 0,
        "tr_v2": 0, "tr_v1": 0, "tr_none": 0,
    }

    # Per-chapter output directory: books/<slug>/.
    book_out_dir = os.path.join(OUTPUT_DIR, book_key)
    os.makedirs(book_out_dir, exist_ok=True)

    # Build the gloss HTML renderer once per book. Wraps archaic words
    # with <span class="swap" data-orig=".." data-mod="..">..</span>;
    # the Modern pill toggle (index.html) flips between data-orig and
    # data-mod values at runtime.
    apply_swaps_fn, swap_pairs, quiet_set = _load_ot_swap_pipeline()

    def _gloss_html_renderer(text: str) -> str:
        # apply_swaps does not pre-escape; the OT gloss source has no
        # raw HTML so this is safe, and the inserted spans use plain
        # ASCII attributes (no characters needing escaping). Any future
        # change to gloss content with HTML-special chars (<, >, &)
        # would need escape-then-swap discipline.
        return apply_swaps_fn(text, swap_pairs, quiet_set)
    gloss_renderer = _gloss_html_renderer

    chapter_nums = []

    for fn in all_files:
        # Hebrew (required). Cascade through tiers in canonical order.
        if fn in v2_he_files:
            he_path, he_source = os.path.join(v2_he_dir, fn), "v2-he"
            counts["he_v2"] += 1
        else:
            he_path, he_source = os.path.join(v1_he_dir, fn), "v1-he-baseline"
            counts["he_v1"] += 1

        inter_path, inter_source, inter_tier = _pick_source(
            fn,
            inter_v2, inter_v2_files,
            inter_v1, inter_v1_files,
            "v2-eng-interlinear", "v1-eng-interlinear",
        )
        counts[f"inter_{inter_tier if inter_tier != 'none' else 'none'}"] += 1

        # Wave 6-OT: the v2 KJV tier (v2/eng-kjv/) is the only English source
        # post-Wave-6 (regenerate_english.py emits KJV verbatim). No v1
        # fallback. Variable name "gloss_*" preserved for backward
        # compatibility within the build pipeline; semantics are KJV-verbatim.
        gloss_path, gloss_source, gloss_tier = _pick_source(
            fn,
            gloss_v2, gloss_v2_files,
            gloss_v1, gloss_v1_files,
            "v2-eng-kjv", "v1-eng-gloss",
        )
        counts[f"gloss_{gloss_tier if gloss_tier != 'none' else 'none'}"] += 1

        tr_path, tr_source, tr_tier = _pick_source(
            fn,
            tr_v2, tr_v2_files,
            tr_v1, tr_v1_files,
            "v2-translit", "v1-translit",
        )
        counts[f"tr_{tr_tier if tr_tier != 'none' else 'none'}"] += 1

        he_verses = parse_chapter_lines(he_path)
        chapter_num = int(he_verses[0]["ref"].split(":")[0]) if he_verses else 0
        if not chapter_num:
            continue

        inter_lookup = lines_to_lookup(parse_chapter_lines(inter_path)) if inter_path else {}
        gloss_lookup = lines_to_lookup(parse_chapter_lines(gloss_path)) if gloss_path else {}
        tr_lookup = lines_to_lookup(parse_chapter_lines(tr_path)) if tr_path else {}

        sources = {
            "he": he_source, "inter": inter_source,
            "gloss": gloss_source, "translit": tr_source,
        }
        fragment = render_chapter(
            chapter_num, he_verses, inter_lookup, gloss_lookup, tr_lookup, sources,
            gloss_html_renderer=gloss_renderer,
        )

        # Write per-chapter file: books/<slug>/<slug>-<NN>.html
        ch_filename = f"{book_key}-{chapter_num:02d}.html"
        ch_path = os.path.join(book_out_dir, ch_filename)
        with open(ch_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(fragment + "\n")

        chapter_nums.append(chapter_num)

    # Write manifest: books/<slug>/manifest.json
    # book_key.replace with title-casing is a reasonable display name fallback;
    # the JS client uses its own BOOKS registry for display names, so the
    # manifest name is informational only.
    manifest = {
        "book_name": book_key.replace("1", "1 ").replace("2", "2 ").title().strip(),
        "slug": book_key,
        "chapters": sorted(chapter_nums),
    }
    manifest_path = os.path.join(book_out_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False)
        f.write("\n")

    print(f"  wrote {book_out_dir}/ ({len(chapter_nums)} chapters + manifest.json)")
    print(f"  Hebrew      v2: {counts['he_v2']}  v1: {counts['he_v1']}")
    print(f"  Interlinear v2: {counts['inter_v2']}  v1: {counts['inter_v1']}  none: {counts['inter_none']}")
    print(f"  Gloss       v2: {counts['gloss_v2']}  v1: {counts['gloss_v1']}  none: {counts['gloss_none']}")
    print(f"  Translit    v2: {counts['tr_v2']}  v1: {counts['tr_v1']}  none: {counts['tr_none']}")
    return True


def main():
    ap = argparse.ArgumentParser(
        description="Generate HTML book fragments from tier sources."
    )
    group = ap.add_mutually_exclusive_group()
    group.add_argument(
        "--book",
        metavar="KEY",
        help="Build a single book by registry key (e.g. jonah). "
             "Exits with an error if source files are missing.",
    )
    group.add_argument(
        "--all-books",
        action="store_true",
        help="Attempt to build every book in BOOK_REGISTRY. "
             "Books whose Hebrew source files are absent are skipped with a "
             "status line; only books with source data are built.",
    )
    args = ap.parse_args()

    if args.book:
        print(f"Building {args.book} ...")
        build_book(args.book, skip_missing=False)
    elif args.all_books:
        built = []
        skipped = []
        for key in BOOK_REGISTRY:
            ok = build_book(key, skip_missing=True)
            if ok:
                built.append(key)
                print()
            else:
                skipped.append(key)
        print(f"\n--- all-books summary ---")
        print(f"  built   ({len(built)}): {', '.join(built) if built else 'none'}")
        print(f"  skipped ({len(skipped)}): no source files")
        if skipped:
            for s in skipped:
                print(f"    {s}")
    else:
        # Default: build all books that have source files.
        print("No --book or --all-books flag; building all books with source files ...")
        built = []
        skipped = []
        for key in BOOK_REGISTRY:
            ok = build_book(key, skip_missing=True)
            if ok:
                built.append(key)
                print()
            else:
                skipped.append(key)
        print(f"\n--- summary ---")
        print(f"  built   ({len(built)}): {', '.join(built) if built else 'none'}")
        print(f"  skipped ({len(skipped)}): no source files")


if __name__ == "__main__":
    main()
