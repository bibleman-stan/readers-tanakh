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
V0_ENG_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v0-eng-baseline")
V1_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1-teamim")
V1_ENG_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1-eng-baseline")

ENG_PWORD_SEP = " | "  # must match ingest_tahot.py

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


# ---- Hebrew structural-gloss naturalizer ---------------------------------
# Modeled on the GNT project's naturalize() in generate_english_glosses.py.
# Wooden-but-legible: preserve Hebrew clause order (VSO etc.) but fix the
# morphological/phrasal artifacts that make English ungrammatical:
#   - Bracketed [supplied] words flattened
#   - Pronominal suffix reorder ("wickedness their" -> "their wickedness")
#   - Demonstrative reorder ("evil this" -> "this evil")
#   - Hebrew adjective-after-noun inversion ("city great" -> "great city")
#   - Common compound-preposition cleanups ("from to before" -> "from before")
#   - Directional he ("Tarshish towards" -> "toward Tarshish")
# All transforms are list-driven, not blanket regex, so adding a Hebrew
# adjective is one entry and false positives are rare. Iterate by extending
# the lists as new patterns surface in editorial review.

POSSESSIVES = ('his', 'her', 'its', 'their', 'your', 'my', 'our')
DEMONSTRATIVES = ('this', 'that', 'these', 'those')

# Words that, if they appear immediately before a possessive/demonstrative,
# mean we should NOT reorder (the suffix is genuinely English-positioned).
# E.g., "in his house" (not Hebrew suffix) vs "house his" (Hebrew suffix).
PREP_OR_FUNCTION = {
    'of', 'in', 'to', 'on', 'at', 'by', 'for', 'with', 'from', 'about',
    'into', 'before', 'after', 'against', 'upon', 'over', 'under',
    'between', 'through', 'around', 'among', 'unto', 'concerning',
    'the', 'a', 'an', 'and', 'or', 'but', 'as', 'than', 'like',
    'is', 'was', 'are', 'were', 'be', 'been', 'am',
    'I', 'you', 'he', 'she', 'we', 'they',
}

# Hebrew adjectives that follow their noun in source order. Inversion is
# required for English. Extend as new patterns appear; false positives are
# rare because these words are unambiguously adjectival in TAHOT glosses.
HEBREW_ADJECTIVES = {
    'great', 'small', 'large', 'little', 'good', 'evil', 'bad', 'holy',
    'innocent', 'wicked', 'righteous', 'pure', 'mighty', 'strong', 'weak',
    'high', 'low', 'wide', 'long', 'short', 'old', 'young', 'new',
    'beloved', 'living', 'dead', 'first', 'last', 'whole', 'broken',
    'open', 'pleasing', 'unleavened', 'precious',
}

_BRACKET_KEEP_RE = re.compile(r'\[([^\]]+)\]')


def naturalize_hebrew_gloss(text):
    """Convert wooden TAHOT-derived English into structural-but-readable English."""
    # Strip [supplied] brackets, keeping the word(s) inside.
    text = _BRACKET_KEEP_RE.sub(r'\1', text)

    # Compound-preposition cleanups (TAHOT renders Hebrew compound preps
    # morpheme-by-morpheme; English needs them collapsed).
    text = re.sub(r'\bfrom to before\b', 'from before', text)
    text = re.sub(r'\bfrom to upon\b', 'from upon', text)
    text = re.sub(r'\bfrom to under\b', 'from under', text)
    text = re.sub(r'\bto in\b', 'into', text)

    # Directional he: "X towards" -> "toward X". Only the trailing "towards"
    # form (not "towards X") because TAHOT writes the ה-suffix gloss after
    # its host word.
    text = re.sub(r'\b(\w+) towards\b', r'toward \1', text)

    adj_alt = '|'.join(re.escape(a) for a in HEBREW_ADJECTIVES)
    dem_alt = '|'.join(DEMONSTRATIVES)
    poss_alt = '|'.join(POSSESSIVES)

    # Combined Hebrew patterns ("the noun adj dem" etc.) MUST run before the
    # simpler single-swap patterns or the swaps fight each other.
    # "the storm great this" -> "this great storm"
    text = re.sub(
        rf'\b(the|a|an) (\w+) ({adj_alt}) ({dem_alt})\b',
        r'\4 \3 \2', text
    )
    # "the evil this" (article + adj + dem) -> "this evil"
    text = re.sub(
        rf'\b(the|a|an) ({adj_alt}) ({dem_alt})\b',
        r'\3 \2', text
    )
    # "the men that" / "the man this" (article + noun + dem) -> "that men"
    text = re.sub(
        rf'\b(the|a|an) (\w+) ({dem_alt})\b',
        r'\3 \2', text
    )
    # "the noun adj poss" -> "poss adj noun"
    text = re.sub(
        rf'\b(the|a|an) (\w+) ({adj_alt}) ({poss_alt})\b',
        r'\4 \3 \2', text
    )
    # "the noun poss" -> "poss noun"
    text = re.sub(
        rf'\b(the|a|an) (\w+) ({poss_alt})\b',
        r'\3 \2', text
    )

    # Adjective inversion (article + noun + adj) -> (article + adj + noun)
    for adj in HEBREW_ADJECTIVES:
        text = re.sub(rf'\b(the|a|an) (\w+) {adj}\b', rf'\1 {adj} \2', text)

    # No-article single swaps. These run AFTER the combined patterns above so
    # we don't undo a prior multi-token reorder.
    def _swap_after_noun(text, after_word_set):
        for w in after_word_set:
            def repl(m, w=w):
                prev = m.group(1)
                if prev.lower() in PREP_OR_FUNCTION:
                    return m.group(0)
                # Don't re-swap if prev is itself in the same set (the
                # combined pattern already placed things in the right order).
                if prev.lower() in after_word_set:
                    return m.group(0)
                return f'{w} {prev}'
            text = re.sub(rf'\b(\w+) {w}\b', repl, text)
        return text

    text = _swap_after_noun(text, set(POSSESSIVES))
    text = _swap_after_noun(text, set(DEMONSTRATIVES))

    # No-article adjective inversion ("city great" -> "great city")
    for adj in HEBREW_ADJECTIVES:
        def repl(m, adj=adj):
            prev = m.group(1)
            if prev.lower() in PREP_OR_FUNCTION:
                return m.group(0)
            if prev.lower() in DEMONSTRATIVES or prev.lower() in POSSESSIVES:
                return m.group(0)
            return f'{adj} {prev}'
        text = re.sub(rf'\b(\w+) {adj}\b', repl, text)

    # Whitespace cleanup
    text = re.sub(r'\s+', ' ', text).strip()
    return text

BOOK_REGISTRY = {
    "jonah": {
        "subdir": "05-jonah",
        "prefix": "jonah",
        # Jonah 1, 3, 4 are prose; chapter 2 is the Sifrei-Emet prayer.
        "poetic_chapters": [2],
    },
}


def compute_cola_boundaries(he_words, breakers):
    """Return list of (start_idx, end_idx) word-index pairs, one per cola.

    A cola break is inserted after any Hebrew prosodic-word whose characters
    include one of the breaker codepoints. Maqqef-joined groups are atomic
    (already pre-joined into single space-separated tokens by ingest).
    """
    boundaries = [0]
    for i, w in enumerate(he_words):
        if not w:
            continue
        if any(b in w for b in breakers):
            boundaries.append(i + 1)
    if boundaries[-1] != len(he_words):
        boundaries.append(len(he_words))
    return list(zip(boundaries, boundaries[1:]))


def strip_paragraph_marker(verse_text):
    """Remove trailing standalone Peh / Samekh paragraph marker."""
    return PARAGRAPH_MARKERS_RE.sub("", verse_text)


def read_v0_chapter(path):
    """Read a v0-prose / v0-eng-baseline chapter file. Returns [(ref, verse_text), ...]."""
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    blocks = re.split(r"\n\s*\n", raw.strip())
    out = []
    for block in blocks:
        parts = block.strip().split("\n", 1)
        if len(parts) != 2:
            continue
        ref, verse_text = parts
        if not VERSE_REF_RE.match(ref.strip()):
            continue
        out.append((ref.strip(), verse_text.strip()))
    return out


def parse_chapter_pair(he_in_path, en_in_path, he_out_path, en_out_path, breakers):
    """Parse Hebrew + English v0 chapter files into aligned v1 cola files."""
    he_verses = read_v0_chapter(he_in_path)
    en_verses_lookup = {ref: text for ref, text in read_v0_chapter(en_in_path)}

    he_blocks = []
    en_blocks = []
    for ref, he_text in he_verses:
        he_clean = strip_paragraph_marker(he_text)
        he_pwords = [w for w in he_clean.split(" ") if w]

        en_text = en_verses_lookup.get(ref, "")
        en_pwords = [u.strip() for u in en_text.split(ENG_PWORD_SEP)] if en_text else []

        # If the prosodic-word counts disagree, the alignment broke somewhere
        # in ingest. Bail loudly rather than silently emit misaligned cola.
        if en_pwords and len(en_pwords) != len(he_pwords):
            sys.exit(
                f"Alignment failure at {ref}: "
                f"{len(he_pwords)} Hebrew prosodic-words vs {len(en_pwords)} English units"
            )

        boundaries = compute_cola_boundaries(he_pwords, breakers)
        he_cola = [" ".join(he_pwords[a:b]) for a, b in boundaries]
        en_cola = [naturalize_hebrew_gloss(" ".join(en_pwords[a:b])) for a, b in boundaries] if en_pwords else []

        he_blocks.append(ref + "\n" + "\n".join(he_cola))
        if en_cola:
            en_blocks.append(ref + "\n" + "\n".join(en_cola))

    os.makedirs(os.path.dirname(he_out_path), exist_ok=True)
    os.makedirs(os.path.dirname(en_out_path), exist_ok=True)
    with open(he_out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n\n".join(he_blocks) + "\n")
    with open(en_out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n\n".join(en_blocks) + "\n")


def parse_book(book_key):
    if book_key not in BOOK_REGISTRY:
        sys.exit(f"Unknown book key: {book_key}")
    spec = BOOK_REGISTRY[book_key]
    he_in_dir = os.path.join(V0_DIR, spec["subdir"])
    en_in_dir = os.path.join(V0_ENG_DIR, spec["subdir"])
    he_out_dir = os.path.join(V1_DIR, spec["subdir"])
    en_out_dir = os.path.join(V1_ENG_DIR, spec["subdir"])

    if not os.path.isdir(he_in_dir):
        sys.exit(f"v0-prose dir not found: {he_in_dir}")
    if not os.path.isdir(en_in_dir):
        sys.exit(f"v0-eng-baseline dir not found: {en_in_dir}")

    chapter_files = sorted(
        fn for fn in os.listdir(he_in_dir)
        if fn.startswith(spec["prefix"] + "-") and fn.endswith(".txt")
    )

    poetic_chapters = set(spec.get("poetic_chapters", []))
    total_lines = 0

    for fn in chapter_files:
        chapter_num = int(fn[len(spec["prefix"]) + 1:-4])
        breakers = POETIC_BREAKERS if chapter_num in poetic_chapters else PROSE_BREAKERS
        he_in_path = os.path.join(he_in_dir, fn)
        en_in_path = os.path.join(en_in_dir, fn)
        he_out_path = os.path.join(he_out_dir, fn)
        en_out_path = os.path.join(en_out_dir, fn)
        parse_chapter_pair(he_in_path, en_in_path, he_out_path, en_out_path, breakers)

        with open(he_out_path, "r", encoding="utf-8") as f:
            line_count = sum(1 for line in f if line.strip() and not VERSE_REF_RE.match(line.strip()))
        total_lines += line_count
        accent_label = "Sifrei Emet" if chapter_num in poetic_chapters else "prose"
        print(f"  wrote {he_out_path}  ({line_count} cola, {accent_label} accents)")
        print(f"  wrote {en_out_path}")

    print(f"\n{book_key}: {total_lines} cola total in v1-teamim/ and v1-eng-baseline/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", required=True)
    args = ap.parse_args()
    parse_book(args.book)


if __name__ == "__main__":
    main()
