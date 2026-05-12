#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
regenerate_english_kjv.py — Wave 2 KJV-style English extractor (Tanakh).

Architecture
------------
The legacy ``generate_english_glosses.py`` produces Macula-Hebrew
structural glosses (per-morpheme, mechanically-naturalized). The new
generator anchors the English layer to TAHOT's per-Hebrew-token English
column — STEPBible's already-aligned, KJV-tradition translation gloss
(CC BY 4.0).

Per-Hebrew-ATU-cola algorithm:

  1. Read Hebrew cola lines from ``data/text-files/v2/he/<book>/<chapter>.txt``
     (one ATU cola per line; maqqef-aware splits into orthographic words).
  2. Stream TAHOT rows for the same verse (e.g. ``Gen.1.1#NN=...``).
     Each row carries one orthographic word and its per-token English
     gloss in column 4 (1-indexed) — morphemes joined by ``/``.
  3. Walk Hebrew cola words and TAHOT tokens in lockstep. Token N in the
     verse must correspond to orthographic-word N in v2/he (after maqqef
     joins). Mismatched counts are reported as alignment failures.
  4. For each cola, concatenate the TAHOT English column of its tokens
     with mechanical cleanup:
        - Drop ``<obj.>`` (the direct-object marker אֵת has no English).
        - Drop ``<...>`` angle-bracket "Hebrew but best-not-translated"
          tokens entirely (per TAHOT field-description guidance).
        - Strip ``[...]`` square-bracket markers but KEEP their contents
          (TAHOT square brackets mark "implied; best included").
        - Replace morpheme separator ``/`` with single space.
        - Collapse runs of whitespace.
  5. **Word order: literal (no VSO→SVO reorder).** Stan's directive for
     Wave 2: "be more careful and thoughtful." Reordering rules are risky
     when subjects are pronominal or elided; we emit token order and
     leave reordering for Wave 3 once Stan eye-checks. The modernization
     layer (data-orig→data-mod swap-class) covers archaic→modern phrasing
     at render time; it cannot fix word-order issues — so getting word
     order *right* > getting it *fluent*.

Output
------
``data/text-files/v2/eng-gloss-kjv/<book>/<chapter>.txt`` — parallel to
the legacy ``eng-gloss/`` directory; identical file format (verse
marker, one English line per Hebrew ATU cola, blank line separator).

The legacy ``eng-gloss/`` directory is NOT touched.

CLI
---
    py -3 scripts/regenerate_english_kjv.py --book genesis
    py -3 scripts/regenerate_english_kjv.py --all
    py -3 scripts/regenerate_english_kjv.py --book genesis --force
    py -3 scripts/regenerate_english_kjv.py --self-test

Co-authored-with: Wave 2 pipeline (Claude Code, Opus 4.7).
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

# ─── paths ──────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
V2_HE_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "he"
OUT_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "eng-gloss-kjv"
TAHOT_DIR = REPO_ROOT / "research" / "stepbible-tahot"
TBESH_PATH = (
    REPO_ROOT.parent / "atu-method" / "data" / "lexicons" / "TBESH.txt"
)

# ─── book registry (mirrors parse_teamim.py BOOK_REGISTRY) ─────────────────

BOOK_REGISTRY = {
    "genesis":      {"subdir": "01-genesis",      "code": "Gen", "file": "TAHOT_Gen-Deu.txt"},
    "exodus":       {"subdir": "02-exodus",       "code": "Exo", "file": "TAHOT_Gen-Deu.txt"},
    "leviticus":    {"subdir": "03-leviticus",    "code": "Lev", "file": "TAHOT_Gen-Deu.txt"},
    "numbers":      {"subdir": "04-numbers",      "code": "Num", "file": "TAHOT_Gen-Deu.txt"},
    "deuteronomy":  {"subdir": "05-deuteronomy",  "code": "Deu", "file": "TAHOT_Gen-Deu.txt"},
    "joshua":       {"subdir": "06-joshua",       "code": "Jos", "file": "TAHOT_Jos-Est.txt"},
    "judges":       {"subdir": "07-judges",       "code": "Jdg", "file": "TAHOT_Jos-Est.txt"},
    "ruth":         {"subdir": "08-ruth",         "code": "Rut", "file": "TAHOT_Jos-Est.txt"},
    "1samuel":      {"subdir": "09-1samuel",      "code": "1Sa", "file": "TAHOT_Jos-Est.txt"},
    "2samuel":      {"subdir": "10-2samuel",      "code": "2Sa", "file": "TAHOT_Jos-Est.txt"},
    "1kings":       {"subdir": "11-1kings",       "code": "1Ki", "file": "TAHOT_Jos-Est.txt"},
    "2kings":       {"subdir": "12-2kings",       "code": "2Ki", "file": "TAHOT_Jos-Est.txt"},
    "1chronicles":  {"subdir": "13-1chronicles",  "code": "1Ch", "file": "TAHOT_Jos-Est.txt"},
    "2chronicles":  {"subdir": "14-2chronicles",  "code": "2Ch", "file": "TAHOT_Jos-Est.txt"},
    "ezra":         {"subdir": "15-ezra",         "code": "Ezr", "file": "TAHOT_Jos-Est.txt"},
    "nehemiah":     {"subdir": "16-nehemiah",     "code": "Neh", "file": "TAHOT_Jos-Est.txt"},
    "esther":       {"subdir": "17-esther",       "code": "Est", "file": "TAHOT_Jos-Est.txt"},
    "job":          {"subdir": "18-job",          "code": "Job", "file": "TAHOT_Job-Sng.txt"},
    "psalms":       {"subdir": "19-psalms",       "code": "Psa", "file": "TAHOT_Job-Sng.txt"},
    "proverbs":     {"subdir": "20-proverbs",     "code": "Pro", "file": "TAHOT_Job-Sng.txt"},
    "ecclesiastes": {"subdir": "21-ecclesiastes", "code": "Ecc", "file": "TAHOT_Job-Sng.txt"},
    "songofsongs":  {"subdir": "22-songofsongs",  "code": "Sng", "file": "TAHOT_Job-Sng.txt"},
    "isaiah":       {"subdir": "23-isaiah",       "code": "Isa", "file": "TAHOT_Isa-Mal.txt"},
    "jeremiah":     {"subdir": "24-jeremiah",     "code": "Jer", "file": "TAHOT_Isa-Mal.txt"},
    "lamentations": {"subdir": "25-lamentations", "code": "Lam", "file": "TAHOT_Isa-Mal.txt"},
    "ezekiel":      {"subdir": "26-ezekiel",      "code": "Ezk", "file": "TAHOT_Isa-Mal.txt"},
    "daniel":       {"subdir": "27-daniel",       "code": "Dan", "file": "TAHOT_Isa-Mal.txt"},
    "hosea":        {"subdir": "28-hosea",        "code": "Hos", "file": "TAHOT_Isa-Mal.txt"},
    "joel":         {"subdir": "29-joel",         "code": "Jol", "file": "TAHOT_Isa-Mal.txt"},
    "amos":         {"subdir": "30-amos",         "code": "Amo", "file": "TAHOT_Isa-Mal.txt"},
    "obadiah":      {"subdir": "31-obadiah",      "code": "Oba", "file": "TAHOT_Isa-Mal.txt"},
    "jonah":        {"subdir": "32-jonah",        "code": "Jon", "file": "TAHOT_Isa-Mal.txt"},
    "micah":        {"subdir": "33-micah",        "code": "Mic", "file": "TAHOT_Isa-Mal.txt"},
    "nahum":        {"subdir": "34-nahum",        "code": "Nam", "file": "TAHOT_Isa-Mal.txt"},
    "habakkuk":     {"subdir": "35-habakkuk",     "code": "Hab", "file": "TAHOT_Isa-Mal.txt"},
    "zephaniah":    {"subdir": "36-zephaniah",    "code": "Zep", "file": "TAHOT_Isa-Mal.txt"},
    "haggai":       {"subdir": "37-haggai",       "code": "Hag", "file": "TAHOT_Isa-Mal.txt"},
    "zechariah":    {"subdir": "38-zechariah",    "code": "Zec", "file": "TAHOT_Isa-Mal.txt"},
    "malachi":      {"subdir": "39-malachi",      "code": "Mal", "file": "TAHOT_Isa-Mal.txt"},
}

# ─── constants / regex ──────────────────────────────────────────────────────

MAQQEF = "־"
SOF_PASUQ = "׃"
VERSE_REF_RE = re.compile(r"^\d+:\d+$")
TAHOT_ROW_RE = re.compile(r"^([A-Za-z0-9]+)\.(\d+)\.(\d+)#(\d+)([=A-Za-z\(\)]*)$")
ANGLE_BRACKET_RE = re.compile(r"<[^>]+>")      # drop entirely
SQUARE_BRACKET_RE = re.compile(r"\[([^\]]*)\]")  # keep contents
WHITESPACE_RE = re.compile(r"\s+")


# ─── parsers ────────────────────────────────────────────────────────────────

def parse_chapter_hebrew(filepath: Path):
    """Parse a v2/he chapter file into [{ref, cola_lines}]."""
    verses = []
    current = None
    with filepath.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\r\n")
            if VERSE_REF_RE.match(line.strip()):
                if current is not None and current["cola_lines"]:
                    verses.append(current)
                current = {"ref": line.strip(), "cola_lines": []}
                continue
            if line.strip() == "":
                if current is not None and current["cola_lines"]:
                    verses.append(current)
                    current = None
                continue
            if current is not None:
                current["cola_lines"].append(line)
    if current is not None and current["cola_lines"]:
        verses.append(current)
    return verses


def split_hebrew_cola_to_words(cola_line: str):
    """Maqqef-aware split: returns list of orthographic-word records.

    Each record: {"he": str, "joins_next": bool}. Words joined by maqqef
    count as ONE orthographic word for layer-alignment purposes (per
    build_books.py canonical reference).
    """
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


def count_orthographic_words(cola_line: str) -> int:
    """Count orthographic words in a cola, treating maqqef-joined as one.

    NOTE: used by the 4-layer verifier (per-cola orthographic-word count
    matches translit / eng-interlinear ``|``-token count).
    """
    words = split_hebrew_cola_to_words(cola_line)
    return sum(1 for w in words if not w["joins_next"])


def count_tahot_tokens_in_cola(cola_line: str) -> int:
    """Count TAHOT tokens that correspond to one cola line.

    TAHOT emits ONE row per prosodic word — i.e. it splits maqqef-joined
    compounds into separate rows. So we count prosodic words, not
    orthographic words. This is the key alignment number when walking
    TAHOT verse-token streams against v2/he cola.
    """
    return len(split_hebrew_cola_to_words(cola_line))


def _decode_tok_idx(tok_idx_str: str, source: str) -> tuple[int, int]:
    """Return (primary_idx, sub_idx) for ordering tokens within a verse.

    L/Q/R rows use 2-digit tok_idx (#01, #02, …) — primary index for the
    main token sequence.
    X rows (LXX-restored extras) use 4-digit tok_idx like ``0501`` which
    means "inserted after L-token 05 as the 1st extra" — i.e., the first
    two digits are the L-token AFTER which the X word inserts, and the
    last two digits are the 1-based position within the X-insertion run.
    Returns ``(05, 1)`` so the ordering tuple sorts X tokens after L05
    and before L06.

    (L tokens get sub_idx 0 so they sort BEFORE any X tokens at the same
    primary index.)
    """
    if source == "X" and len(tok_idx_str) >= 4:
        primary = int(tok_idx_str[:-2])
        sub = int(tok_idx_str[-2:])
        return (primary, sub)
    return (int(tok_idx_str), 0)


def parse_tahot_file(tahot_path: Path, book_code: str):
    """Parse TAHOT into {chapter: {verse: [(surface_he, english, strongs), ...]}}.

    Token rows look like:
        Gen.1.1#01=L	בְּ/רֵאשִׁ֖ית	be./re.Shit	in/ beginning	H9003/{H7225G}	HR/Ncfsa	...

    TAHOT's primary verse reference is the **English/NRSV** numbering. When
    Hebrew verse numbering differs, TAHOT appends ``(H.V)`` in parentheses
    to the ref, e.g. ``Gen.31.55(32.1)`` means English 31:55 = Hebrew 32:1.
    The v2/he source files use **Hebrew BHS** numbering, so we key the
    index by the Hebrew ref where one is present. Without the parenthetical
    we use the English ref directly (the two coincide for most of the corpus).

    We collect tokens in textual order; tok_idx (the ``#NN`` suffix) is
    1-based within a verse.
    """
    staging: dict[int, dict[int, list]] = defaultdict(lambda: defaultdict(list))
    target_prefix = book_code + "."
    row_re = re.compile(
        r"^([A-Za-z0-9]+)\.(\d+)\.(\d+)"
        r"(?:\((\d+)\.(\d+)\))?"
        r"#(\d+)=([A-Za-z]+)"
    )
    with tahot_path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\r\n")
            if not line.startswith(target_prefix):
                continue
            cols = line.split("\t")
            if len(cols) < 4:
                continue
            ref_field = cols[0]
            m = row_re.match(ref_field)
            if not m:
                continue
            if m.group(1) != book_code:
                continue
            eng_ch = int(m.group(2))
            eng_vs = int(m.group(3))
            heb_ch = int(m.group(4)) if m.group(4) else eng_ch
            heb_vs = int(m.group(5)) if m.group(5) else eng_vs
            tok_idx_str = m.group(6)
            source = m.group(7)
            # Accepted sources (each row IS a Hebrew word the project
            # treats as base text):
            #   L     — Leningrad
            #   L*    — Leningrad-family (LA, LAH, LBH, LAB, etc.)
            #   Q     — Qere; translators use Qere when differs from K
            #   R     — restored from another verse (Jos.21.36-37, Neh.7.67b)
            #   X     — extra word reconstructed from LXX; present in
            #           v2/he per project's editorial decision. Insertion
            #           position decoded from tok_idx (e.g. ``0501`` = after
            #           L-token 05, position 1 in the insertion).
            # Skip:
            #   K     — Ketiv; shares tok_idx with Q row (would duplicate).
            if source == "K":
                continue
            if source not in ("L", "Q", "R", "X") and not source.startswith("L"):
                continue
            ch, vs = heb_ch, heb_vs
            primary, sub = _decode_tok_idx(tok_idx_str, source)
            surface = cols[1] if len(cols) > 1 else ""
            english = cols[3] if len(cols) > 3 else ""
            strongs = cols[4] if len(cols) > 4 else ""
            staging[ch][vs].append(((primary, sub), surface, english, strongs))

    # Sort each verse's tokens into textual order and emit clean triples.
    out: dict[int, dict[int, list[tuple[str, str, str]]]] = defaultdict(dict)
    for ch, verses in staging.items():
        for vs, entries in verses.items():
            entries.sort(key=lambda e: e[0])
            out[ch][vs] = [(s, e, st) for _, s, e, st in entries]
    return out


# ─── TBESH fallback lexicon (only loaded if a TAHOT English column is empty) ─

_TBESH_CACHE: dict[str, str] | None = None


def load_tbesh() -> dict[str, str]:
    """Load TBESH brief-gloss lexicon keyed by Strong number (e.g. 'H0430').

    Returns dict {strong: short_gloss}. Falls back to empty dict if file
    is missing — the fallback then degrades to empty string for unknown
    tokens, which is acceptable since TAHOT itself covers the corpus.
    """
    global _TBESH_CACHE
    if _TBESH_CACHE is not None:
        return _TBESH_CACHE
    cache: dict[str, str] = {}
    if not TBESH_PATH.exists():
        _TBESH_CACHE = cache
        return cache
    try:
        with TBESH_PATH.open("r", encoding="utf-8") as f:
            for raw in f:
                line = raw.rstrip("\r\n")
                if not line or not line.startswith("H"):
                    continue
                cols = line.split("\t")
                if len(cols) < 7:
                    continue
                # cols: eStrong, dStrong-anno, dStrong, hebrew, transliteration, POS, gloss, def
                key = cols[2].strip()  # dStrong, e.g. "H0430G"
                gloss = cols[6].strip() if len(cols) > 6 else ""
                if key and gloss and key not in cache:
                    cache[key] = gloss
    except Exception:
        pass
    _TBESH_CACHE = cache
    return cache


# ─── cleanup pipeline ───────────────────────────────────────────────────────

def clean_token_english(eng: str) -> str:
    """Apply mechanical cleanup to a single TAHOT English-column value.

    Rules:
      - Replace morpheme separator ``/`` with single space.
      - Drop ``<...>`` angle-bracket markers entirely (TAHOT: "in the
        Hebrew but best not included in translation").
      - Strip ``[...]`` square brackets but KEEP contents (TAHOT: "not in
        the Hebrew but best included").
      - Collapse runs of whitespace.
    """
    if eng is None:
        return ""
    s = eng.replace("/", " ")
    s = ANGLE_BRACKET_RE.sub("", s)
    s = SQUARE_BRACKET_RE.sub(r"\1", s)
    s = WHITESPACE_RE.sub(" ", s).strip()
    return s


def primary_strong(strongs_field: str) -> str:
    """Extract the lexical (curly-braced) Strong from a TAHOT dStrongs cell.

    Example: ``H9003/{H7225G}`` → ``H7225G``. Returns "" if none found.
    """
    if not strongs_field:
        return ""
    m = re.search(r"\{(H\d+[A-Za-z]?)\}", strongs_field)
    return m.group(1) if m else ""


def token_english_with_fallback(eng: str, strongs_field: str) -> str:
    """Get cleaned English for a token, falling back to TBESH if empty.

    IMPORTANT: a TAHOT English column that contains ONLY angle-bracket
    markers (e.g. ``<obj.>``, ``<to>``) is an INTENTIONAL no-translation
    signal, not a missing gloss — TBESH fallback would re-introduce
    ``Obj.`` from the lexicon's bracketed bare label. So we skip fallback
    when the original eng-string was non-empty (i.e. TAHOT *had* a value,
    it's just untranslated by design).
    """
    cleaned = clean_token_english(eng)
    if cleaned:
        return cleaned
    # If TAHOT had ANY content (e.g. "<obj.>"), respect the no-translation
    # signal and emit empty — do not fall back.
    if eng and eng.strip():
        return ""
    strong = primary_strong(strongs_field)
    if not strong:
        return ""
    tbesh = load_tbesh()
    gloss = tbesh.get(strong, "")
    if not gloss:
        # Try without trailing letter (H7225G → H7225)
        gloss = tbesh.get(strong[:-1], "") if strong[-1].isalpha() else ""
    return clean_token_english(gloss)


def assemble_cola_english(cola_tokens_english: list[str]) -> str:
    """Join per-token English values into a smooth cola line.

    No reordering; literal token order (Wave 2 conservative choice).
    """
    parts = [t for t in cola_tokens_english if t]
    s = " ".join(parts)
    s = WHITESPACE_RE.sub(" ", s).strip()
    return s


# ─── core generator ─────────────────────────────────────────────────────────

def generate_chapter(
    book_key: str,
    chapter_filepath: Path,
    tahot_index: dict,
    out_path: Path,
    diagnostics: dict,
) -> int:
    """Generate one chapter's KJV-style English file from TAHOT.

    Returns the number of cola lines written.
    """
    chapter_num_match = re.search(r"-(\d+)\.txt$", chapter_filepath.name)
    if not chapter_num_match:
        diagnostics.setdefault("errors", []).append(
            f"Cannot extract chapter number from {chapter_filepath.name}"
        )
        return 0
    chapter_num = int(chapter_num_match.group(1))
    chapter_tahot = tahot_index.get(chapter_num, {})

    he_verses = parse_chapter_hebrew(chapter_filepath)
    out_lines: list[str] = []
    cola_total = 0

    for verse in he_verses:
        ref = verse["ref"]              # "1:1"
        ch_str, vs_str = ref.split(":")
        try:
            vs_num = int(vs_str)
        except ValueError:
            continue

        verse_tokens = chapter_tahot.get(vs_num, [])
        # Walk cola lines; consume tokens sequentially.
        cursor = 0
        cola_english_lines: list[str] = []
        for cola in verse["cola_lines"]:
            n_words = count_tahot_tokens_in_cola(cola)
            cola_tokens = verse_tokens[cursor:cursor + n_words]
            cursor += n_words
            token_eng = [
                token_english_with_fallback(t[1], t[2]) for t in cola_tokens
            ]
            line = assemble_cola_english(token_eng)
            cola_english_lines.append(line)
            cola_total += 1

        if cursor != len(verse_tokens):
            diagnostics.setdefault("token_count_mismatches", []).append(
                f"{book_key} {ref}: consumed {cursor} tokens, TAHOT has "
                f"{len(verse_tokens)} (Δ={len(verse_tokens) - cursor})"
            )

        out_lines.append(ref)
        out_lines.extend(cola_english_lines)
        out_lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        # Drop trailing blank to match v2/eng-gloss/ convention (one blank
        # between verses, file ends without an extra terminator).
        body = "\n".join(out_lines).rstrip() + "\n"
        f.write(body)
    return cola_total


def generate_book(book_key: str, *, force: bool = False) -> dict:
    """Generate the eng-gloss-kjv layer for one book. Returns diagnostics."""
    if book_key not in BOOK_REGISTRY:
        return {"error": f"Unknown book: {book_key}"}
    entry = BOOK_REGISTRY[book_key]
    book_subdir = entry["subdir"]
    book_code = entry["code"]
    tahot_file = TAHOT_DIR / entry["file"]

    if not tahot_file.exists():
        return {"error": f"TAHOT file missing: {tahot_file}"}
    he_dir = V2_HE_DIR / book_subdir
    if not he_dir.is_dir():
        return {"error": f"Hebrew source dir missing: {he_dir}"}
    out_dir = OUT_DIR / book_subdir
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[{book_key}] Parsing TAHOT for {book_code} from {tahot_file.name}...")
    tahot_index = parse_tahot_file(tahot_file, book_code)
    n_chapters_in_tahot = len(tahot_index)
    print(f"[{book_key}] TAHOT chapters parsed: {n_chapters_in_tahot}")

    diagnostics: dict = {"book": book_key, "chapters": 0, "cola_total": 0,
                         "token_count_mismatches": [], "errors": []}
    chapter_files = sorted(he_dir.glob("*.txt"))
    for cf in chapter_files:
        out_path = out_dir / cf.name
        if out_path.exists() and not force:
            # Skip; user can pass --force to regenerate
            diagnostics["chapters"] += 1
            continue
        cola = generate_chapter(book_key, cf, tahot_index, out_path, diagnostics)
        diagnostics["chapters"] += 1
        diagnostics["cola_total"] += cola
    print(
        f"[{book_key}] Wrote {diagnostics['chapters']} chapter file(s), "
        f"{diagnostics['cola_total']} cola lines. "
        f"Mismatches: {len(diagnostics['token_count_mismatches'])}."
    )
    return diagnostics


# ─── self-test ──────────────────────────────────────────────────────────────

def _self_test() -> int:
    """Run Gen 1 generation and assert sanity properties. Returns exit code."""
    print("=== self-test: regenerate_english_kjv.py / Genesis 1 ===")
    diag = generate_book("genesis", force=True)
    if diag.get("error"):
        print(f"FAIL: {diag['error']}")
        return 1

    gen1 = OUT_DIR / "01-genesis" / "genesis-01.txt"
    if not gen1.exists():
        print(f"FAIL: output missing: {gen1}")
        return 1

    # Parse output and compare line counts per verse to the Hebrew source.
    out_verses = parse_chapter_hebrew(gen1)
    he_verses = parse_chapter_hebrew(V2_HE_DIR / "01-genesis" / "genesis-01.txt")
    out_by_ref = {v["ref"]: v["cola_lines"] for v in out_verses}
    he_by_ref = {v["ref"]: v["cola_lines"] for v in he_verses}

    failed = False
    for ref, he_cola in he_by_ref.items():
        out_cola = out_by_ref.get(ref, [])
        if len(out_cola) != len(he_cola):
            print(f"FAIL: cola-count mismatch {ref}: he={len(he_cola)} en={len(out_cola)}")
            failed = True

    # Content checks
    gen_1_1 = " ".join(out_by_ref.get("1:1", [])).lower()
    for needed in ("god", "created", "heavens", "earth"):
        if needed not in gen_1_1:
            print(f"FAIL: Gen 1:1 missing token '{needed}'. Got: {gen_1_1!r}")
            failed = True

    # 90%-non-empty check
    flat_lines = [l for v in out_verses for l in v["cola_lines"]]
    non_empty = [l for l in flat_lines if l.strip()]
    pct = 100.0 * len(non_empty) / max(1, len(flat_lines))
    if pct < 90:
        print(f"FAIL: only {pct:.1f}% of lines have content")
        failed = True

    print(f"Gen 1 cola lines: {len(flat_lines)} ({pct:.1f}% non-empty)")
    print(f"Gen 1:1 → {gen_1_1!r}")

    if failed:
        return 1
    print("PASS: all self-test assertions held.")
    return 0


# ─── CLI ────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--book", help="Single book key (e.g. genesis, jonah)")
    p.add_argument("--all", action="store_true", help="Run all books in BOOK_REGISTRY")
    p.add_argument("--force", action="store_true", help="Overwrite existing output files")
    p.add_argument("--self-test", action="store_true", help="Run Genesis 1 self-test")
    args = p.parse_args(argv)

    if args.self_test:
        return _self_test()

    if args.all:
        had_error = False
        for book in BOOK_REGISTRY:
            diag = generate_book(book, force=args.force)
            if diag.get("error"):
                print(f"  ERROR: {diag['error']}")
                had_error = True
        return 1 if had_error else 0

    if not args.book:
        p.print_help()
        return 2

    diag = generate_book(args.book, force=args.force)
    if diag.get("error"):
        print(f"ERROR: {diag['error']}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
