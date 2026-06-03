"""Render-stage ATU-line override layer for the Tanakh reader.

Sibling to scripts/bofm_generate.py _overrides() / _apply_override() in BoFM,
but architected around Tanakh's BHSA-clause-atom pipeline + Hebrew's two
editorial-discipline invariants:
  (1) the v0 word stream (consonants) is canonical and immutable; and
  (2) niqqud + te'amim are preserved verbatim - "no editorial overlay has
      force" but the marks themselves must round-trip.

Overrides apply at the RENDER stage inside run_full_tanakh.render_v2_heb_format,
per verse, after the mechanical ATU lines for the verse are assembled but before
they are appended to the chapter output. Never at apply_bindings stage - that
keeps the binding fabric pure (regenerable, diffable) and confines adjudication
to the consumer.

Override file: data/text-files/v2/heb-adjudicated/overrides.json
  Schema: {"<book-folder> <chapter>:<verse>": ["ATU line 1", "ATU line 2", ...]}
  Keys use the BHSA folder convention verbatim ("01-genesis 22:1",
  "27-daniel 12:13") - matches the v2/heb/<NN-book>/<book>-<CC>.txt path
  structure. Two-gate parity (see below). Empty initial file - day-1
  user-visible impact is zero.

PARITY (the substantive fix over the mechanical BoFM port):

Gate A - HEBREW-AWARE CONSONANT PARITY.
  NFD normalize -> strip Hebrew points + te'amim (U+0591-05BD + U+05BF +
  U+05C1-05C2 + U+05C4-05C7) -> retain only the WIDER Hebrew letter block
  U+05D0-05F4 (this INCLUDES final-form letters U+05DA ך U+05DD ם U+05DF ן
  U+05E3 ף U+05E5 ץ which the in-pipeline _CONS_ONLY=[א-ת] regex DROPS,
  silently failing parity on every verse ending in a final letter).
  Verse passes Gate A iff `_consonants(" ".join(override_lines))
  == _consonants(v0_verse_text)`.

Gate B - POINTING-STRICT PARITY (the NEW gate the BoFM port did not need).
  NFD normalize -> map maqqef U+05BE to space (a maqqef-bound phrase like
  אֶת־הַשָּׁמַיִם may legitimately split across line breaks as אֶת + הַשָּׁמַיִם) ->
  collapse runs of whitespace -> retain only Hebrew letters + niqqud +
  te'amim + sof-pasuq + paseq. Verse passes Gate B iff `_pointed(" ".join(
  override_lines)) == _pointed(v0_verse_text)`. This rejects any override
  that drops a holam, meteg, atnaḥ, or sof-pasuq - enforcing the Tanakh
  CLAUDE.md invariant.

Both gates must pass. Gate-A failure is logged "CONSONANT FAIL"; Gate-B
failure is logged "POINTING-STRICT FAIL" so an editor knows whether they
dropped a word vs. dropped a diacritic.

ARAMAIC SKIP. Aramaic verses (Dan 2:4-7:28, Ezra 4:8-6:18, 7:12-26) are
SKIPPED entirely - any ref in those ranges short-circuits to mechanical
output without even attempting override application. Prevents a stray
Aramaic override key from silently shipping.

Env bypass: TANAKH_BYPASS_OVERRIDES=1 short-circuits to mechanical for
validators that want raw mechanical output.
"""
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ADJUDICATED = REPO_ROOT / "data" / "text-files" / "v2" / "heb-adjudicated" / "overrides.json"
BYPASS_ENV = "TANAKH_BYPASS_OVERRIDES"


# Aramaic ranges copied from scripts/atu_pipeline/run_pipeline.py (the legacy
# pipeline retains the canonical table). A verse-level check parses the scope
# strings; held Aramaic refs are NEVER eligible for override application.
ARAMAIC_RANGES = {
    "27-daniel": [(2, "from-v4"), (3, "all"), (4, "all"), (5, "all"),
                  (6, "all"), (7, "all")],
    "15-ezra": [(4, "from-v8"), (5, "all"), (6, "to-v18"),
                (7, "from-v12-to-v26")],
}


def is_aramaic_verse(book_folder, chapter, verse):
    """True if (book_folder, chapter, verse) is in a held Aramaic range."""
    ranges = ARAMAIC_RANGES.get(book_folder, [])
    for chap, scope in ranges:
        if chap != chapter:
            continue
        if scope == "all":
            return True
        m = re.match(r"from-v(\d+)$", scope)
        if m:
            if verse >= int(m.group(1)):
                return True
            continue
        m = re.match(r"to-v(\d+)$", scope)
        if m:
            if verse <= int(m.group(1)):
                return True
            continue
        m = re.match(r"from-v(\d+)-to-v(\d+)$", scope)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            if lo <= verse <= hi:
                return True
            continue
    return False


_OVERRIDES = None


def _overrides():
    """Cached singleton loader. Honors TANAKH_BYPASS_OVERRIDES."""
    global _OVERRIDES
    if os.environ.get(BYPASS_ENV):
        return {}
    if _OVERRIDES is None:
        if ADJUDICATED.exists():
            _OVERRIDES = json.loads(ADJUDICATED.read_text(encoding="utf-8"))
        else:
            _OVERRIDES = {}
    return _OVERRIDES


# Hebrew points + te'amim Unicode ranges. NFD does NOT decompose Hebrew
# precomposed forms (BHSA / TAHOT supply already-decomposed text), so a single
# pass strips these directly.
_POINTS_TEAMIM = re.compile(
    r"[֑-ׇֽֿׁׂׅׄ]"
)
# WIDER Hebrew letter block, INCLUDING final-form letters which the narrow
# [א-ת] (U+05D0-U+05EA) regex misses. Goes through U+05F4 to keep the
# ligature characters (װ U+05F0, ױ U+05F1, ײ U+05F2) and geresh/gershayim.
_HEBREW_LETTERS_KEEP = re.compile(r"[^א-״]")

# For Gate B: keep Hebrew letters + niqqud + te'amim + sof-pasuq + paseq.
# Drop everything else (Latin, punctuation, whitespace AFTER the maqqef -> space
# transform has already been collapsed).
_POINTED_KEEP = re.compile(
    r"[^֑-ׇֽֿׁׂׅׄא-״]"
)
_MAQQEF = "־"


def _consonants(s):
    """Gate A: NFD -> strip points + te'amim -> retain wider Hebrew letter
    block (incl. final-form letters)."""
    nfd = unicodedata.normalize("NFD", s)
    stripped = _POINTS_TEAMIM.sub("", nfd)
    return _HEBREW_LETTERS_KEEP.sub("", stripped)


def _pointed(s):
    """Gate B: NFD -> maqqef U+05BE -> space -> drop everything outside
    {Hebrew letters U+05D0-U+05F4, niqqud + te'amim ranges}. Whitespace
    collapses out by exclusion from the keep set. This preserves the
    diacritic stream byte-for-byte after NFD while tolerating the one
    permitted orthographic transform (maqqef-bound phrase split across
    line breaks)."""
    nfd = unicodedata.normalize("NFD", s)
    no_maqqef = nfd.replace(_MAQQEF, " ")
    return _POINTED_KEEP.sub("", no_maqqef)


def ref_for(book_folder, chapter, verse):
    """Build the override-lookup key, e.g. '01-genesis 22:1'."""
    return f"{book_folder} {chapter}:{verse}"


def apply_override(ref, v0_verse_text, mechanical_lines, book_folder, chapter, verse):
    """Return adjudicated ATU lines for `ref` iff:
      (a) the verse is NOT in a held Aramaic range,
      (b) an override exists for `ref`,
      (c) Gate A (consonant parity) passes against v0_verse_text, and
      (d) Gate B (pointing-strict parity) passes against v0_verse_text.

    Otherwise returns None; on a gate failure prints a stderr warning
    distinguishing CONSONANT FAIL vs POINTING-STRICT FAIL so an editor
    knows whether they dropped a word vs. dropped a diacritic.

    `mechanical_lines` is accepted but not consulted - parity is judged
    against the v0 verse text (the canonical anchor), not against the
    mechanical output.
    """
    if is_aramaic_verse(book_folder, chapter, verse):
        return None
    ov = _overrides().get(ref)
    if not ov:
        return None
    joined = " ".join(ov)
    if _consonants(joined) != _consonants(v0_verse_text):
        print(f"  !! adjudication override REJECTED (CONSONANT FAIL): {ref}",
              file=sys.stderr, flush=True)
        return None
    if _pointed(joined) != _pointed(v0_verse_text):
        print(f"  !! adjudication override REJECTED (POINTING-STRICT FAIL): {ref}",
              file=sys.stderr, flush=True)
        return None
    return ov
