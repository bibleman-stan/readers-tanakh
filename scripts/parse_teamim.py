"""
parse_teamim.py - Te'amim-driven baseline cola generator (starting draft for v4-editorial).

Reads v0-prose Hebrew + v0-eng-baseline English + v0-translit-baseline
translit in lockstep. Splits at te'amim cola boundaries derived from the
Hebrew accents. Emits four parallel v1 chapter files per book as a starting
draft for editorial refinement:

  v1-teamim/            Hebrew cola (one cola per line; prosodic-words
                        space-separated; orthographic-word boundaries within
                        a prosodic word are signaled by inline maqqef ־)
  v1-eng-interlinear/   Per-orthographic-word English (` | ` separator,
                        brackets KEPT, no naturalize)
  v1-eng-gloss/         Smooth naturalized English (one cola per line, normal
                        text; brackets stripped, possessives/demonstratives
                        reordered, Hebrew adjective-after-noun inverted,
                        compound prepositions collapsed, directional ה
                        prefixed with "toward")
  v1-translit/          Per-orthographic-word translit (` | ` separator,
                        modern Israeli style)

METHODOLOGICAL NOTE: The te'amim (cantillation accents) are EVIDENCE of the
Masoretic tradition's structural understanding, not authority for line-break
decisions. v1-teamim is a fast baseline that avoids blank-page work; v4-editorial
freely adds, removes, or merges line breaks relative to v1-teamim per the
colometry canon's atomic-thought and Hebrew-syntax criteria. See
private/01-method/colometry-canon.md §1 "The Te'amim Are Not a Structural Prior"
and Rule H8 "Te'amim as Evidence" for canonical framing.

Two accent systems: prose (21 books) and Sifrei Emet (Pss/Prov/poetic Job).
Per-book registry declares which chapters route through the poetic parser.
"""

import argparse
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

V0_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v0-prose")
V0_ENG_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v0-eng-baseline")
V0_TRANSLIT_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v0-translit-baseline")

V1_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1-teamim")
V1_ENG_INTER_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1-eng-interlinear")
V1_ENG_GLOSS_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1-eng-gloss")
V1_TRANSLIT_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1-translit")

ENG_WORD_SEP = " | "  # must match ingest_tahot.py
MAQQEF = "־"

# Tier-1/2 disjunctives — prose (21 books).
# NOTE: These are draft-generation heuristics for the v1-teamim baseline,
# not canon commitments. v4-editorial applies the colometry canon to refine
# breaks relative to this v1 output.
PROSE_BREAKERS = {
    "֑",  # ETNAHTA
    "֒",  # SEGOL (segolta)
    "֔",  # ZAQEF QATAN
    "֕",  # ZAQEF GADOL
    "֖",  # TIPEHA (see TODO below)
}

# Tier-1/2 disjunctives — Sifrei Emet (Pss / Prov / poetic Job).
# NOTE: Same draft-heuristic caveat as PROSE_BREAKERS.
POETIC_BREAKERS = {
    "֑",  # ETNAHTA
    "֫",  # OLE (component of oleh ve-yored)
    "֭",  # DEHI
    "֗",  # REVIA (revia mugrash in poetic position)
}

# TODO(canon-2026-04-26): Tifcha treatment.
# Tifcha is often a "servant of atnach" (Wickes 1887) rather than a primary
# breaker. The current script treats tifcha as a tier-2 default breaker,
# which over-fragments single-thought verses (canonical example: Jonah 1:1
# producing a 3-line widow split). Rule H11 in the colometry canon raises
# tifcha's evidence weight but doesn't override this behavior. Consider tuning
# the parser to reduce tifcha-driven splits in short verses or within atnach
# domains when editorial refinement patterns emerge. Do NOT change now;
# log this for follow-up tuning once v1 → v4 editorial passes yield data.

PARAGRAPH_MARKERS_RE = re.compile(r"\s+[פס]\s*$")
VERSE_REF_RE = re.compile(r"^\d+:\d+$")

BOOK_REGISTRY = {
    "jonah": {
        "subdir": "05-jonah",
        "prefix": "jonah",
        "poetic_chapters": [2],   # the prayer
    },
}


# ---- Hebrew structural-gloss naturalizer ---------------------------------
# (Same logic as before — modeled on the GNT project's naturalize().)

POSSESSIVES = ('his', 'her', 'its', 'their', 'your', 'my', 'our')
DEMONSTRATIVES = ('this', 'that', 'these', 'those')

# Single-swap demonstratives: only `this`/`these` get the noun-after-X swap
# without article context. `that`/`those` are excluded because TAHOT's English
# uses "that" for both demonstrative AND complementizer (kī "that, because"),
# so single-swap fires false positives like "knew that" -> "that knew".
# The article-aware patterns ("the X that") still handle the demonstrative
# cases that need it.
DEMONSTRATIVES_SINGLE_SWAP = ('this', 'these')

PREP_OR_FUNCTION = {
    'of', 'in', 'to', 'on', 'at', 'by', 'for', 'with', 'from', 'about',
    'into', 'before', 'after', 'against', 'upon', 'over', 'under',
    'between', 'through', 'around', 'among', 'unto', 'concerning',
    'the', 'a', 'an', 'and', 'or', 'but', 'as', 'than', 'like',
    'is', 'was', 'are', 'were', 'be', 'been', 'am',
    'I', 'you', 'he', 'she', 'we', 'they',
}

HEBREW_ADJECTIVES = {
    'great', 'small', 'large', 'little', 'good', 'evil', 'bad', 'holy',
    'innocent', 'wicked', 'righteous', 'pure', 'mighty', 'strong', 'weak',
    'high', 'low', 'wide', 'long', 'short', 'old', 'young', 'new',
    'beloved', 'living', 'dead', 'first', 'last', 'whole', 'broken',
    'open', 'pleasing', 'unleavened', 'precious',
    # Positional / intensifier adjectives that follow Hebrew noun-first order:
    'right', 'left', 'own',
}

_BRACKET_KEEP_RE = re.compile(r'\[([^\]]+)\]')
_VSO_PRONOUN_RE = re.compile(r'^and (he|she|it|they)\s', re.IGNORECASE)


def naturalize_hebrew_gloss(text, word_units=None):
    """Wooden-but-legible naturalizer: see parse_teamim.py docstring.

    word_units: optional list of per-orthographic-word gloss strings for this
    cola (the same list used to build the interlinear row).  When provided,
    the VSO-pronoun-drop rule can inspect the immediately-following word unit
    rather than guessing from the joined string.
    """
    text = _BRACKET_KEEP_RE.sub(r'\1', text)

    # ---- VSO pronoun-drop (SMOOTH GLOSS ONLY) --------------------------------
    # Hebrew wayyiqtol verbs in prose carry an implicit subject pronoun that
    # TAHOT's interlinear exposes (e.g. "and he appointed").  When the very
    # next per-word unit in the same cola is a nominal subject — a proper noun
    # (capitalised word) or a definite noun phrase ("the X" / "[the] X") —
    # the pronoun is spurious in the smooth gloss because the overt noun
    # supplies the reference (Hebrew VSO word order: verb-subject-object).
    # Drop "he/she/it/they" in the smooth layer; the interlinear keeps it.
    #
    # Rule fires only when word_units is passed and has ≥ 2 entries so that
    # the second unit (index 1) can be inspected.  The check is:
    #   unit[0] starts with "and (he|she|it|they) " (wayyiqtol pronoun pattern)
    #   unit[1] (brackets stripped) starts with a capital letter (proper noun)
    #       OR starts with "the " (definite article phrase)
    if word_units and len(word_units) >= 2:
        first_unit = _BRACKET_KEEP_RE.sub(r'\1', word_units[0]).strip()
        second_unit = _BRACKET_KEEP_RE.sub(r'\1', word_units[1]).strip()
        if _VSO_PRONOUN_RE.match(first_unit):
            is_proper_noun = bool(second_unit) and second_unit[0].isupper()
            is_definite = second_unit.startswith('the ') or second_unit == 'the'
            if is_proper_noun or is_definite:
                # Remove the spurious pronoun from the joined smooth-gloss string.
                # Pattern: "^and (he|she|it|they) " at the start of the cola text.
                text = re.sub(
                    r'^and (he|she|it|they) ',
                    'and ',
                    text,
                    flags=re.IGNORECASE,
                )
    # --------------------------------------------------------------------------

    # Rejoin TAHOT's hyphen-split English ("there- -fore" -> "therefore")
    text = re.sub(r'(\w+)-\s+-(\w+)', r'\1\2', text)

    text = re.sub(r'\bfrom to before\b', 'from before', text)
    text = re.sub(r'\bfrom to upon\b', 'from upon', text)
    text = re.sub(r'\bfrom to under\b', 'from under', text)
    text = re.sub(r'\bto in\b', 'into', text)
    text = re.sub(r'\b(\w+) towards\b', r'toward \1', text)

    adj_alt = '|'.join(re.escape(a) for a in HEBREW_ADJECTIVES)
    dem_alt = '|'.join(DEMONSTRATIVES)
    poss_alt = '|'.join(POSSESSIVES)

    # Combined patterns BEFORE single-swap so we don't ping-pong.
    text = re.sub(rf'\b(the|a|an) (\w+) ({adj_alt}) ({dem_alt})\b', r'\4 \3 \2', text)
    text = re.sub(rf'\b(the|a|an) ({adj_alt}) ({dem_alt})\b', r'\3 \2', text)
    text = re.sub(rf'\b(the|a|an) (\w+) ({dem_alt})\b', r'\3 \2', text)
    text = re.sub(rf'\b(the|a|an) (\w+) ({adj_alt}) ({poss_alt})\b', r'\4 \3 \2', text)
    text = re.sub(rf'\b(the|a|an) (\w+) ({poss_alt})\b', r'\3 \2', text)

    # No-article adj+noun+poss -> poss+adj+noun ("right hand his" -> "his right hand";
    # "own land my" -> "my own land"). Must run before the single-swap possessive,
    # which would otherwise produce "right his hand" and stop.
    text = re.sub(rf'\b({adj_alt}) (\w+) ({poss_alt})\b', r'\3 \1 \2', text)

    for adj in HEBREW_ADJECTIVES:
        text = re.sub(rf'\b(the|a|an) (\w+) {adj}\b', rf'\1 {adj} \2', text)

    def _swap_after_noun(text, after_word_set):
        for w in after_word_set:
            def repl(m, w=w):
                prev = m.group(1)
                if prev.lower() in PREP_OR_FUNCTION:
                    return m.group(0)
                if prev.lower() in after_word_set:
                    return m.group(0)
                return f'{w} {prev}'
            text = re.sub(rf'\b(\w+) {w}\b', repl, text)
        return text

    text = _swap_after_noun(text, set(POSSESSIVES))
    # Use the safer subset for single-swap demonstratives (drops `that`/`those`).
    text = _swap_after_noun(text, set(DEMONSTRATIVES_SINGLE_SWAP))

    for adj in HEBREW_ADJECTIVES:
        def repl(m, adj=adj):
            prev = m.group(1)
            if prev.lower() in PREP_OR_FUNCTION:
                return m.group(0)
            if prev.lower() in DEMONSTRATIVES or prev.lower() in POSSESSIVES:
                return m.group(0)
            return f'{adj} {prev}'
        text = re.sub(rf'\b(\w+) {adj}\b', repl, text)

    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ---- Cola splitting -----------------------------------------------------

def hebrew_orthographic_word_count(prosodic_word):
    """Count orthographic words in a maqqef-joined prosodic-word token."""
    return prosodic_word.count(MAQQEF) + 1


def compute_cola_boundaries(he_pwords, breakers):
    """Return [(start_idx, end_idx), ...] of prosodic-word ranges per cola."""
    boundaries = [0]
    for i, w in enumerate(he_pwords):
        if not w:
            continue
        if any(b in w for b in breakers):
            boundaries.append(i + 1)
    if boundaries[-1] != len(he_pwords):
        boundaries.append(len(he_pwords))
    return list(zip(boundaries, boundaries[1:]))


def strip_paragraph_marker(verse_text):
    """Remove trailing standalone Peh / Samekh paragraph marker."""
    return PARAGRAPH_MARKERS_RE.sub("", verse_text)


def read_v0_chapter(path):
    """Read a v0-style .txt chapter file. Returns [(ref, verse_text), ...]."""
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    blocks = re.split(r"\n\s*\n", raw.strip())
    out = []
    for block in blocks:
        parts = block.strip().split("\n", 1)
        if len(parts) != 2:
            continue
        ref, text = parts
        if not VERSE_REF_RE.match(ref.strip()):
            continue
        out.append((ref.strip(), text.strip()))
    return out


def parse_chapter(he_in, en_in, tr_in,
                  he_out, en_inter_out, en_gloss_out, tr_out,
                  breakers):
    """Parse one chapter into the four v1 outputs."""
    he_verses = read_v0_chapter(he_in)
    en_lookup = {ref: text for ref, text in read_v0_chapter(en_in)}
    tr_lookup = {ref: text for ref, text in read_v0_chapter(tr_in)}

    he_blocks, inter_blocks, gloss_blocks, tr_blocks = [], [], [], []

    for ref, he_text in he_verses:
        he_clean = strip_paragraph_marker(he_text)
        he_pwords = [w for w in he_clean.split(" ") if w]

        # Total orthographic words for this verse
        ortho_count = sum(hebrew_orthographic_word_count(w) for w in he_pwords)

        en_text = en_lookup.get(ref, "")
        en_words = [w.strip() for w in en_text.split(ENG_WORD_SEP)] if en_text else []
        tr_text = tr_lookup.get(ref, "")
        tr_words = [w.strip() for w in tr_text.split(ENG_WORD_SEP)] if tr_text else []

        if en_words and len(en_words) != ortho_count:
            sys.exit(
                f"Alignment failure at {ref}: "
                f"{ortho_count} Hebrew orthographic-words vs {len(en_words)} English units"
            )
        if tr_words and len(tr_words) != ortho_count:
            sys.exit(
                f"Alignment failure at {ref}: "
                f"{ortho_count} Hebrew orthographic-words vs {len(tr_words)} translit units"
            )

        # Cola boundaries (v1-teamim baseline) are at PROSODIC-word level.
        # Te'amim sit on prosodic units; v4-editorial refines these baseline breaks
        # per the colometry canon's atomic-thought and syntax criteria.
        boundaries = compute_cola_boundaries(he_pwords, breakers)

        # Map prosodic-word index -> orthographic-word start index
        ortho_starts = [0]
        for c in (hebrew_orthographic_word_count(w) for w in he_pwords):
            ortho_starts.append(ortho_starts[-1] + c)

        he_cola, inter_cola, gloss_cola, trans_cola = [], [], [], []
        for pa, pb in boundaries:
            he_cola.append(" ".join(he_pwords[pa:pb]))

            oa = ortho_starts[pa]
            ob = ortho_starts[pb]

            if en_words:
                inter_words = en_words[oa:ob]
                inter_cola.append(ENG_WORD_SEP.join(inter_words))
                gloss_input = " ".join(w for w in inter_words if w)
                gloss_cola.append(naturalize_hebrew_gloss(gloss_input, word_units=inter_words))

            if tr_words:
                trans_cola.append(ENG_WORD_SEP.join(tr_words[oa:ob]))

        he_blocks.append(ref + "\n" + "\n".join(he_cola))
        if inter_cola:
            inter_blocks.append(ref + "\n" + "\n".join(inter_cola))
            gloss_blocks.append(ref + "\n" + "\n".join(gloss_cola))
        if trans_cola:
            tr_blocks.append(ref + "\n" + "\n".join(trans_cola))

    for path in (he_out, en_inter_out, en_gloss_out, tr_out):
        os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(he_out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n\n".join(he_blocks) + "\n")
    if inter_blocks:
        with open(en_inter_out, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n\n".join(inter_blocks) + "\n")
        with open(en_gloss_out, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n\n".join(gloss_blocks) + "\n")
    if tr_blocks:
        with open(tr_out, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n\n".join(tr_blocks) + "\n")


def parse_book(book_key):
    if book_key not in BOOK_REGISTRY:
        sys.exit(f"Unknown book key: {book_key}")
    spec = BOOK_REGISTRY[book_key]

    he_in_dir = os.path.join(V0_DIR, spec["subdir"])
    en_in_dir = os.path.join(V0_ENG_DIR, spec["subdir"])
    tr_in_dir = os.path.join(V0_TRANSLIT_DIR, spec["subdir"])

    he_out_dir = os.path.join(V1_DIR, spec["subdir"])
    inter_out_dir = os.path.join(V1_ENG_INTER_DIR, spec["subdir"])
    gloss_out_dir = os.path.join(V1_ENG_GLOSS_DIR, spec["subdir"])
    tr_out_dir = os.path.join(V1_TRANSLIT_DIR, spec["subdir"])

    if not os.path.isdir(he_in_dir):
        sys.exit(f"v0-prose dir not found: {he_in_dir}")

    chapter_files = sorted(
        fn for fn in os.listdir(he_in_dir)
        if fn.startswith(spec["prefix"] + "-") and fn.endswith(".txt")
    )

    poetic_chapters = set(spec.get("poetic_chapters", []))
    total_lines = 0

    for fn in chapter_files:
        chapter_num = int(fn[len(spec["prefix"]) + 1:-4])
        breakers = POETIC_BREAKERS if chapter_num in poetic_chapters else PROSE_BREAKERS

        parse_chapter(
            os.path.join(he_in_dir, fn),
            os.path.join(en_in_dir, fn),
            os.path.join(tr_in_dir, fn),
            os.path.join(he_out_dir, fn),
            os.path.join(inter_out_dir, fn),
            os.path.join(gloss_out_dir, fn),
            os.path.join(tr_out_dir, fn),
            breakers,
        )

        with open(os.path.join(he_out_dir, fn), "r", encoding="utf-8") as f:
            line_count = sum(
                1 for line in f
                if line.strip() and not VERSE_REF_RE.match(line.strip())
            )
        total_lines += line_count
        accent_label = "Sifrei Emet" if chapter_num in poetic_chapters else "prose"
        print(f"  {fn}: {line_count} cola, {accent_label}")

    print(
        f"\n{book_key}: {total_lines} cola "
        f"-> v1-teamim / v1-eng-interlinear / v1-eng-gloss / v1-translit"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", required=True)
    args = ap.parse_args()
    parse_book(args.book)


if __name__ == "__main__":
    main()
