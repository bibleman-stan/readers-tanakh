"""morph_alignment.py - Map v2/heb (or v1/he-baseline) tokens to TAHOT morph tags.

The v0/morph layer (one tag per orthographic word, " | " separated, one
verse per file-line) is anchored to TAHOT's word inventory. The v1/v2
Hebrew layers re-segment those words into colometric lines but PRESERVE
the underlying ortho-word sequence per verse (1-method/canon §0: editing changes
where lines break, never which words appear).

This module:
  1. Loads `v0/morph/<book>/<book>-NN.txt` for any chapter
  2. Aligns it to a v1/v2 Hebrew chapter file, per verse
  3. Provides per-token tag access (each prosodic-word token may span
     multiple ortho-words via maqqef; the token gets the LIST of tags
     for its ortho components)

If the v0/morph file is missing or the ortho-count alignment fails for
a verse, the loader returns None for that verse — callers should fall
back to skel-heuristics rather than crash.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

# Repo root: this file lives at 5-machinery/validators/_shared/morph_alignment.py
_REPO_ROOT = Path(__file__).resolve().parents[2]
_V0_MORPH_DIR = _REPO_ROOT / "data" / "text-files" / "v0" / "morph"

MAQQEF = "־"
_VERSE_RE = re.compile(r"^(\d+):(\d+)\s*$")
_PIPE_SEP = " | "


# ──────────────────────────────────────────────────────────────────────
# Chapter-level loader
# ──────────────────────────────────────────────────────────────────────

# In-process cache keyed by absolute chapter path: {chapter_path_str: {verse: [tag, ...]}}
_chapter_cache: dict[str, dict[int, list[str]]] = {}


def load_chapter_morph(he_chapter_path: Path) -> Optional[dict[int, list[str]]]:
    """Load v0/morph for the chapter that matches the given v1/v2 he-chapter path.

    Path mapping: replace `data/text-files/v?/he*` with `data/text-files/v0/morph`.

    Returns:
      {verse_num: [ortho_tag_1, ortho_tag_2, ...]} on success
      None if the morph file does not exist (caller falls back)
    """
    morph_path = _morph_path_for(he_chapter_path)
    if morph_path is None:
        return None
    cache_key = str(morph_path)
    if cache_key in _chapter_cache:
        return _chapter_cache[cache_key]
    if not morph_path.exists():
        _chapter_cache[cache_key] = {}
        return None

    by_verse: dict[int, list[str]] = {}
    cur_verse: Optional[int] = None
    for raw in morph_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            cur_verse = None
            continue
        m = _VERSE_RE.match(line)
        if m:
            cur_verse = int(m.group(2))
            continue
        if cur_verse is None:
            continue
        # tag line — split on " | " to get ortho-word tag list
        tags = [t.strip() for t in line.split(_PIPE_SEP)]
        by_verse[cur_verse] = tags
    _chapter_cache[cache_key] = by_verse
    return by_verse


def _morph_path_for(he_chapter_path: Path) -> Optional[Path]:
    """Compute v0/morph path from a v1/v2 he-chapter path.

    Conventions:
      data/text-files/v2/heb/<book>/<book>-NN.txt
        → data/text-files/v0/morph/<book>/<book>-NN.txt
      data/text-files/v1/he-baseline/<book>/<book>-NN.txt
        → same destination
    """
    parts = he_chapter_path.resolve().parts
    # Find the data/text-files/<vN>/<layer>/ prefix
    try:
        i = parts.index("text-files")
    except ValueError:
        return None
    if i + 2 >= len(parts):
        return None
    # parts[i+1] = "v0"|"v1"|"v2", parts[i+2] = layer ("heb"/"he-baseline"/"prose"/"morph"/...)
    book_and_file = parts[i + 3 :]
    if not book_and_file:
        return None
    return _V0_MORPH_DIR.joinpath(*book_and_file)


# ──────────────────────────────────────────────────────────────────────
# Per-verse alignment
# ──────────────────────────────────────────────────────────────────────


def align_verse_tokens_to_tags(
    lines: list[str], ortho_tags: list[str]
) -> Optional[list[list[list[str]]]]:
    """Align v1/v2 Hebrew lines for a verse to ortho-word morph tags.

    Args:
      lines: List of Hebrew content lines for the verse (no verse-ref line).
        Each line contains whitespace-separated PROSODIC-WORD tokens; each
        token may span multiple ORTHOGRAPHIC words via maqqef.
      ortho_tags: List of TAHOT morph tags, one per ortho-word, in the
        ORTHO order TAHOT emits them.

    Returns:
      List parallel to `lines`. Each element is a list of token-tag-lists,
      one entry per token in that line. Each token-tag-list contains the
      tags for the token's ortho components (in left-to-right order).

      Example:
        lines = ['וַיְהִי דְּבַר־יְהוָה', 'אֶל־יוֹנָה']
        ortho_tags = ['Hc/Vqw3ms', 'HNcmsc', 'HNpt', 'HR', 'HNpm']
        result = [
          [['Hc/Vqw3ms'], ['HNcmsc', 'HNpt']],   # line 0: 2 prosodic tokens
          [['HR', 'HNpm']],                       # line 1: 1 prosodic token
        ]

      None on alignment mismatch — caller falls back to skel-heuristics.
    """
    out: list[list[list[str]]] = []
    ortho_idx = 0
    n_ortho = len(ortho_tags)
    for line in lines:
        tokens = line.split()
        line_tags: list[list[str]] = []
        for tok in tokens:
            ortho_count = len(tok.split(MAQQEF))
            end = ortho_idx + ortho_count
            if end > n_ortho:
                return None  # ran past the tag stream — alignment broken
            line_tags.append(ortho_tags[ortho_idx:end])
            ortho_idx = end
        out.append(line_tags)
    if ortho_idx != n_ortho:
        return None  # leftover tags — alignment broken (token under-count)
    return out


# ──────────────────────────────────────────────────────────────────────
# Convenience: token-level access
# ──────────────────────────────────────────────────────────────────────


def head_tag_for_token(token_tags: list[str]) -> Optional[str]:
    """Return the LAST tag in a token's tag list — the syntactic head.

    For a maqqef-joined prosodic word, the rightmost ortho-word usually
    carries the governing morpheme (verb in V+complement, noun in
    construct chains, etc.). For non-maqqef tokens the only tag IS the
    head.
    """
    if not token_tags:
        return None
    return token_tags[-1]


def first_tag_for_token(token_tags: list[str]) -> Optional[str]:
    """Return the FIRST tag — useful for prep-detection on bound forms."""
    if not token_tags:
        return None
    return token_tags[0]
