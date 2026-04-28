"""
poetic_register.py — Shared utility for poetic-register detection.

Imported by colometry validators that must skip poetic registers.
Pure-stdlib; no external dependencies.
"""

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Books and chapter ranges that route through Sifrei Emet (poetic accent system).
# Source of truth: scripts/parse_teamim.py BOOK_REGISTRY's poetic_chapters lists.
SIFREI_EMET_BOOKS_FULL = {
    # All chapters in these books are Sifrei Emet:
    "psalms",    # all 150
    "proverbs",  # all 31
}

SIFREI_EMET_BOOKS_PARTIAL = {
    # Subset of chapters route Sifrei Emet:
    "job":   set(range(3, 43)),  # chs 3–42 (poetic body); chs 1, 2, 43+ are prose frame
    "jonah": {2},                 # ch 2 prayer (prose-cantillated but poetic register)
}

# Books/chapters/verse-ranges that ARE poetic but route through PROSE accents.
# These need a separate hard-skip gate from validators that would otherwise
# only check Sifrei Emet routing. Source: 6-agent audit 2026-04-28.
EMBEDDED_POETRY = {
    "exodus":       [(15, None)],                       # ch 15 full (Song of the Sea)
    "deuteronomy":  [(32, None), (33, (2, 29))],        # ch 32 full (Ha'azinu); ch 33 vv 2–29 (Mosaic blessings)
    "judges":       [(5, None)],                        # ch 5 full (Song of Deborah)
    "1samuel":      [(2, (1, 10))],                     # ch 2 vv 1–10 (Hannah's Song)
    "2samuel":      [(22, None)],                       # ch 22 full (≈ Ps 18)
    "isaiah":       [(12, None)],                       # ch 12 (psalm of thanksgiving)
    "habakkuk":     [(3, None)],                        # ch 3 (תְּפִלָּה — Habakkuk's prayer)
    "lamentations": [(1, None), (2, None), (3, None), (4, None), (5, None)],  # all 5 chapters
    "songofsongs":  [(c, None) for c in range(1, 9)],  # all 8 chapters
    "ecclesiastes": [(3, (2, 8))],                     # ch 3 vv 2–8 ("a time to be born…")
    # Optionally extend with prophetic high-poetic blocks (Isa 5:1-7, Isa 14:4b-21,
    # Jer 2-6, Mic 1, etc.) — left out for now pending per-block expert curation.
}

# Acrostic chapters: alphabetic-letter heads correlate with line starts ≥80%.
# Hard-skip for validators that would over-merge across acrostic boundaries.
ACROSTIC_CHAPTERS = {
    "psalms":       {9, 10, 25, 34, 37, 111, 112, 119, 145},
    "proverbs":     [(31, (10, 31))],   # ch 31 vv 10–31 (eshet hayil)
    "lamentations": {1, 2, 3, 4},
    "nahum":        [(1, (2, 8))],      # ch 1 vv 2–8
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _norm(book: str) -> str:
    """Normalize book name: lowercase, strip leading digit-prefix and dash.

    Examples:
        "01-genesis" -> "genesis"
        "Genesis"    -> "genesis"
        "1samuel"    -> "1samuel"   (numeric prefix that is part of the name, kept)
    """
    s = book.strip().lower()
    # Strip leading "NN-" filename prefix (two digits + hyphen).
    if len(s) >= 4 and s[0:2].isdigit() and s[2] == "-":
        s = s[3:]
    return s


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def is_sifrei_emet_chapter(book: str, chapter: int) -> bool:
    """True if (book, chapter) routes through Sifrei Emet accent system."""
    book = _norm(book)
    if book in SIFREI_EMET_BOOKS_FULL:
        return True
    if book in SIFREI_EMET_BOOKS_PARTIAL:
        return chapter in SIFREI_EMET_BOOKS_PARTIAL[book]
    return False


def is_embedded_poetry(book: str, chapter: int, verse: int | None = None) -> bool:
    """True if (book, chapter, verse) is in the embedded-poetry skip-list.

    If verse is None, returns True if any portion of the chapter is embedded poetry.
    If verse is provided, returns True only if the specific verse falls in an
    embedded-poetry range.
    """
    book = _norm(book)
    if book not in EMBEDDED_POETRY:
        return False
    for entry in EMBEDDED_POETRY[book]:
        ch, vrange = entry
        if ch != chapter:
            continue
        if vrange is None:
            return True
        if verse is None:
            return True  # any portion qualifies if we don't know the verse
        lo, hi = vrange
        if lo <= verse <= hi:
            return True
    return False


def is_acrostic_chapter(book: str, chapter: int, verse: int | None = None) -> bool:
    """True if (book, chapter, verse) is in a known acrostic structure."""
    book = _norm(book)
    if book not in ACROSTIC_CHAPTERS:
        return False
    entry = ACROSTIC_CHAPTERS[book]
    if isinstance(entry, set):
        return chapter in entry
    # list-of-tuples form: [(chapter, verse-range), ...]
    for ch, vrange in entry:
        if ch != chapter:
            continue
        if vrange is None:
            return True
        if verse is None:
            return True
        lo, hi = vrange
        if lo <= verse <= hi:
            return True
    return False


def is_poetic_register(book: str, chapter: int, verse: int | None = None) -> bool:
    """Convenience: True if any of the three skip conditions fires.

    Validators that should skip ALL poetic registers can call this single function.
    """
    return (
        is_sifrei_emet_chapter(book, chapter)
        or is_embedded_poetry(book, chapter, verse)
        or is_acrostic_chapter(book, chapter, verse)
    )
