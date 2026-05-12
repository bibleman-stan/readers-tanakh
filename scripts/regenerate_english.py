#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
regenerate_english.py — KJV-verbatim English extractor (Tanakh).

This is the canonical English-layer generator. Wave 6-OT promoted the
KJV-anchored path to default and retired the Macula-Hebrew structural-gloss
predecessor (scripts/generate_english_glosses.py — 614 lines of naturalize
regex rules + 174 hardcoded phrase-map entries) in the same wave.

Thin wrapper over ``atu_method.kjv_alignment`` (Wave 5b universal module).

Substrate
---------
Reads ACTUAL KJV verbatim per ATU cola, via viz.bible's MetaV
(per-KJV-word Strong's tagging, CC BY-SA 3.0). For each Hebrew token in
v2/he, the universal algorithm finds the KJV words in the same verse
whose Strong's match, distributes them to the right ATU cola preserving
KJV reading order within each cola, and attaches translator-supplied
KJV words (no Strong's) to the cola of their nearest non-italic neighbour.

The pipeline:

  1. Walk v2/he/<NN-book>/<book>-<NN>.txt, yielding verses (BHS-numbered).
  2. Stream TAHOT rows for the same verse. TAHOT keys verses by KJV/English
     number primarily; rows whose Hebrew BHS verse differs append the BHS
     ref parenthetically (e.g. ``Gen.31.55(32.1)``). Build a BHS-keyed
     verse index BUT also remember every English ref encountered for that
     BHS verse — this is the ENGLISH NUMBER to call MetaV with (MetaV uses
     KJV versification).
  3. Per Hebrew cola, consume TAHOT tokens positionally (maqqef-aware
     prosodic-word count via build_books.py's canonical reference). Build
     a SourceToken per token: surface from TAHOT col 1, Strong's via
     ``extract_strongs_from_tahot_col(col 4)``.
  4. Pass ``source_atu_lines_with_tokens`` (list-of-lists) +
     book_osis + chapter + ENGLISH verse number to
     ``align_verse(...)``. Receive ``list[str]`` — one KJV verbatim line
     per Hebrew cola.
  5. Write to ``data/text-files/v2/eng-gloss/<NN-book>/<book>-<NN>.txt``
     (verse marker, one English line per Hebrew cola, blank line separator).

What stays
----------
- CLI surface: ``--book``, ``--all``, ``--force``, ``--self-test``
- Book registry: 39 OT books with TAHOT prefix + TAHOT volume file
- The v2/he source directory is read-only (sacrosanct per CLAUDE.md)

CLI
---
    py -3 scripts/regenerate_english.py --book genesis
    py -3 scripts/regenerate_english.py --all --force
    py -3 scripts/regenerate_english.py --self-test

Wave 5c-OT shipped the KJV-anchored substrate (atu-method commit 48f9d42).
Wave 6-OT promoted it to default and retired the Macula-structural legacy.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

# ─── paths ──────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
ATU_METHOD_ROOT = REPO_ROOT.parent / "atu-method"
V2_HE_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "he"
OUT_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "eng-gloss"
TAHOT_DIR = REPO_ROOT / "research" / "stepbible-tahot"
METAV_DIR = ATU_METHOD_ROOT / "data" / "kjv-strongs"

# Make the universal kjv_alignment module importable.
sys.path.insert(0, str(ATU_METHOD_ROOT))

from atu_method.kjv_alignment import (  # noqa: E402
    SourceToken,
    align_verse,
    extract_strongs_from_tahot_col,
    load_kjv_strongs_index,
)

# ─── book registry ──────────────────────────────────────────────────────────

# TAHOT prefix -> MetaV OSIS code. The kjv_alignment.metav_loader's
# OSIS_TO_BOOK_ID dict is the authority; this maps TAHOT's 3-letter codes
# (Exo/Deu/Jos/Jdg/Rut/...) to MetaV's varied-length OSIS codes
# (Exod/Deut/Josh/Judg/Ruth/...).
TAHOT_TO_OSIS = {
    "Gen": "Gen", "Exo": "Exod", "Lev": "Lev", "Num": "Num", "Deu": "Deut",
    "Jos": "Josh", "Jdg": "Judg", "Rut": "Ruth",
    "1Sa": "1Sam", "2Sa": "2Sam", "1Ki": "1Kgs", "2Ki": "2Kgs",
    "1Ch": "1Chr", "2Ch": "2Chr",
    "Ezr": "Ezra", "Neh": "Neh", "Est": "Esth",
    "Job": "Job", "Psa": "Ps", "Pro": "Prov", "Ecc": "Eccl", "Sng": "Song",
    "Isa": "Isa", "Jer": "Jer", "Lam": "Lam", "Ezk": "Ezek", "Dan": "Dan",
    "Hos": "Hos", "Jol": "Joel", "Amo": "Amos", "Oba": "Obad", "Jon": "Jonah",
    "Mic": "Mic", "Nam": "Nah", "Hab": "Hab", "Zep": "Zeph",
    "Hag": "Hag", "Zec": "Zech", "Mal": "Mal",
}

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
VERSE_REF_RE = re.compile(r"^\d+:\d+$")
# Placeholder for cola whose KJV-words got swept onto an adjacent line.
# Must be non-blank so build_books' parse_chapter_lines doesn't treat the
# cola line as a verse separator.
EMPTY_COLA_PLACEHOLDER = "—"
TAHOT_ROW_RE = re.compile(
    r"^([A-Za-z0-9]+)\.(\d+)\.(\d+)"
    r"(?:\((\d+)\.(\d+)\))?"
    r"#(\d+)=([A-Za-z]+)"
)


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
    """Maqqef-aware split (canonical reference: build_books.py L156)."""
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


def count_tahot_tokens_in_cola(cola_line: str) -> int:
    """Count prosodic words (= TAHOT row count for this cola).

    TAHOT emits ONE row per prosodic word — maqqef-joined compounds split
    into separate rows. Match alignment uses this count.
    """
    return len(split_hebrew_cola_to_words(cola_line))


def _decode_tok_idx(tok_idx_str: str, source: str) -> tuple[int, int]:
    """L/Q/R = 2-digit primary index; X = 4-digit (after-Lnn, insert-pos)."""
    if source == "X" and len(tok_idx_str) >= 4:
        primary = int(tok_idx_str[:-2])
        sub = int(tok_idx_str[-2:])
        return (primary, sub)
    return (int(tok_idx_str), 0)


def parse_tahot_file(tahot_path: Path, book_code: str):
    """Parse TAHOT into ``{bhs_ch: {bhs_vs: VerseRec}}``.

    VerseRec = {
        "tokens": list[(surface, strongs_field)] in textual order,
        "english_refs": list[(eng_ch, eng_vs)] in token-order (deduped),
    }

    TAHOT's primary ref is English/KJV; when Hebrew BHS differs, TAHOT
    appends ``(H.V)`` to the ref. We key by BHS so v2/he (which uses BHS
    numbering) reads cleanly; we remember every English (ch, vs) seen so
    we can call MetaV with the correct KJV verse number.
    """
    staging: dict[int, dict[int, list]] = defaultdict(lambda: defaultdict(list))
    target_prefix = book_code + "."

    with tahot_path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\r\n")
            if not line.startswith(target_prefix):
                continue
            cols = line.split("\t")
            if len(cols) < 5:
                continue
            ref_field = cols[0]
            m = TAHOT_ROW_RE.match(ref_field)
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
            # Skip Ketiv (Q row shares tok_idx and replaces it); accept
            # L, L* (LA/LAH/...), Q, R (restored), X (LXX-extra).
            if source == "K":
                continue
            if source not in ("L", "Q", "R", "X") and not source.startswith("L"):
                continue
            primary, sub = _decode_tok_idx(tok_idx_str, source)
            surface = cols[1] if len(cols) > 1 else ""
            strongs_field = cols[4] if len(cols) > 4 else ""

            staging[heb_ch][heb_vs].append(
                ((primary, sub), surface, strongs_field, eng_ch, eng_vs)
            )

    out: dict[int, dict[int, dict]] = defaultdict(dict)
    for ch, verses in staging.items():
        for vs, entries in verses.items():
            entries.sort(key=lambda e: e[0])
            tokens: list[tuple[str, str]] = []
            english_refs_seen: list[tuple[int, int]] = []
            seen_refs: set[tuple[int, int]] = set()
            for _, surface, strongs_field, ech, evs in entries:
                tokens.append((surface, strongs_field))
                key = (ech, evs)
                if key not in seen_refs:
                    seen_refs.add(key)
                    english_refs_seen.append(key)
            out[ch][vs] = {
                "tokens": tokens,
                "english_refs": english_refs_seen,
            }
    return out


# ─── per-verse alignment via universal module ───────────────────────────────

def choose_english_verse_for_metav(
    english_refs: list[tuple[int, int]],
    metav_index,
    book_id: int,
) -> tuple[int, int] | None:
    """Pick the English (ch, vs) that exists in MetaV.

    If multiple English verses map to one BHS verse (Psalms superscription:
    English 23:0 + 23:1 both BHS 23:1), MetaV typically only carries the
    higher-numbered one (KJV folds the superscription into v.1 at
    negative vpos). So prefer the largest English verse first.

    Returns None if no MetaV match exists.
    """
    if not english_refs:
        return None
    candidates = sorted(set(english_refs), key=lambda x: (-x[1], -x[0]))
    for ech, evs in candidates:
        if (book_id, ech, evs) in metav_index:
            return (ech, evs)
    return None


def render_verse(
    book_osis: str,
    book_id: int,
    bhs_ch: int,
    bhs_vs: int,
    cola_lines: list[str],
    verse_rec: dict,
    metav_index,
    diagnostics: dict,
    book_key: str,
) -> list[str]:
    """Render one BHS verse's cola as KJV-verbatim English lines."""
    tokens = verse_rec["tokens"]
    english_refs = verse_rec["english_refs"]

    # Pick the English verse number for MetaV
    metav_key = choose_english_verse_for_metav(english_refs, metav_index, book_id)
    if metav_key is None:
        diagnostics.setdefault("metav_misses", []).append(
            f"{book_key} {bhs_ch}:{bhs_vs}: no MetaV entry for any English ref "
            f"{english_refs}"
        )
        return ["" for _ in cola_lines]

    eng_ch, eng_vs = metav_key

    # Walk cola lines, consume tokens sequentially.
    cursor = 0
    source_lines: list[list[SourceToken]] = []
    for cola in cola_lines:
        n_words = count_tahot_tokens_in_cola(cola)
        cola_tokens = tokens[cursor:cursor + n_words]
        cursor += n_words
        atu_line: list[SourceToken] = []
        for surface, strongs_field in cola_tokens:
            strongs = tuple(extract_strongs_from_tahot_col(strongs_field))
            atu_line.append(SourceToken(text=surface, strongs_list=strongs))
        source_lines.append(atu_line)

    if cursor != len(tokens):
        diagnostics.setdefault("token_count_mismatches", []).append(
            f"{book_key} {bhs_ch}:{bhs_vs}: consumed {cursor}, TAHOT has "
            f"{len(tokens)} (Δ={len(tokens) - cursor})"
        )

    try:
        out = align_verse(book_osis, eng_ch, eng_vs, source_lines, METAV_DIR)
    except KeyError as e:
        diagnostics.setdefault("align_errors", []).append(str(e))
        return [EMPTY_COLA_PLACEHOLDER for _ in cola_lines]

    # Empty cola can occur when the synonymy sweep pulls all of a cola's
    # KJV words onto an adjacent line (e.g. Gen 1:4 "and divided the light
    # from the darkness" — the second cola consumes the third cola's KJV
    # words because they share Strong's). The file format requires ONE
    # non-blank line per cola (blank line = verse separator), so we emit
    # a placeholder. The 4-layer verifier and build_books then see the
    # expected line count.
    return [line if line else EMPTY_COLA_PLACEHOLDER for line in out]


# ─── core generator ─────────────────────────────────────────────────────────

def generate_chapter(
    book_key: str,
    book_osis: str,
    book_id: int,
    chapter_filepath: Path,
    tahot_index: dict,
    metav_index,
    out_path: Path,
    diagnostics: dict,
) -> int:
    """Generate one chapter's KJV-verbatim English file."""
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
        ref = verse["ref"]
        ch_str, vs_str = ref.split(":")
        try:
            ch_num = int(ch_str)
            vs_num = int(vs_str)
        except ValueError:
            continue

        verse_rec = chapter_tahot.get(vs_num)
        if verse_rec is None:
            # No TAHOT data — emit placeholder cola lines.
            cola_english_lines = [EMPTY_COLA_PLACEHOLDER for _ in verse["cola_lines"]]
            diagnostics.setdefault("tahot_misses", []).append(
                f"{book_key} {ref}: no TAHOT rows"
            )
        else:
            cola_english_lines = render_verse(
                book_osis=book_osis,
                book_id=book_id,
                bhs_ch=ch_num,
                bhs_vs=vs_num,
                cola_lines=verse["cola_lines"],
                verse_rec=verse_rec,
                metav_index=metav_index,
                diagnostics=diagnostics,
                book_key=book_key,
            )

        cola_total += len(cola_english_lines)
        out_lines.append(ref)
        out_lines.extend(cola_english_lines)
        out_lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        body = "\n".join(out_lines).rstrip() + "\n"
        f.write(body)
    return cola_total


def generate_book(book_key: str, metav_index, *, force: bool = False) -> dict:
    """Generate eng-gloss for one book (KJV-verbatim). Returns diagnostics."""
    if book_key not in BOOK_REGISTRY:
        return {"error": f"Unknown book: {book_key}"}
    entry = BOOK_REGISTRY[book_key]
    book_subdir = entry["subdir"]
    book_code = entry["code"]
    book_osis = TAHOT_TO_OSIS[book_code]
    tahot_file = TAHOT_DIR / entry["file"]

    # Resolve book_id from OSIS via the kjv_alignment module
    from atu_method.kjv_alignment.metav_loader import OSIS_TO_BOOK_ID
    book_id = OSIS_TO_BOOK_ID[book_osis]

    if not tahot_file.exists():
        return {"error": f"TAHOT file missing: {tahot_file}"}
    he_dir = V2_HE_DIR / book_subdir
    if not he_dir.is_dir():
        return {"error": f"Hebrew source dir missing: {he_dir}"}
    out_dir = OUT_DIR / book_subdir
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[{book_key}] Parsing TAHOT for {book_code} (OSIS={book_osis}, "
          f"BookID={book_id}) from {tahot_file.name}...")
    tahot_index = parse_tahot_file(tahot_file, book_code)
    n_chapters_in_tahot = len(tahot_index)
    print(f"[{book_key}] TAHOT chapters parsed: {n_chapters_in_tahot}")

    diagnostics: dict = {
        "book": book_key, "chapters": 0, "cola_total": 0,
        "token_count_mismatches": [], "errors": [], "metav_misses": [],
        "tahot_misses": [], "align_errors": [],
    }
    chapter_files = sorted(he_dir.glob("*.txt"))
    for cf in chapter_files:
        out_path = out_dir / cf.name
        if out_path.exists() and not force:
            diagnostics["chapters"] += 1
            continue
        cola = generate_chapter(
            book_key=book_key,
            book_osis=book_osis,
            book_id=book_id,
            chapter_filepath=cf,
            tahot_index=tahot_index,
            metav_index=metav_index,
            out_path=out_path,
            diagnostics=diagnostics,
        )
        diagnostics["chapters"] += 1
        diagnostics["cola_total"] += cola
    print(
        f"[{book_key}] Wrote {diagnostics['chapters']} chapter(s), "
        f"{diagnostics['cola_total']} cola. "
        f"Token-count mismatches: {len(diagnostics['token_count_mismatches'])}, "
        f"MetaV misses: {len(diagnostics['metav_misses'])}, "
        f"TAHOT misses: {len(diagnostics['tahot_misses'])}."
    )
    return diagnostics


# ─── self-test ──────────────────────────────────────────────────────────────

def _self_test() -> int:
    """Run Gen 1 generation and assert KJV-verbatim sanity."""
    print("=== self-test: regenerate_english.py / Genesis 1 (KJV) ===")
    metav_index = load_kjv_strongs_index(METAV_DIR)
    diag = generate_book("genesis", metav_index, force=True)
    if diag.get("error"):
        print(f"FAIL: {diag['error']}")
        return 1

    gen1 = OUT_DIR / "01-genesis" / "genesis-01.txt"
    if not gen1.exists():
        print(f"FAIL: output missing: {gen1}")
        return 1

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

    gen_1_1 = " ".join(out_by_ref.get("1:1", []))
    expected_1_1 = "In the beginning God created the heaven and the earth."
    if gen_1_1.strip() != expected_1_1:
        print(f"FAIL: Gen 1:1 mismatch. Got: {gen_1_1!r}; expected: {expected_1_1!r}")
        failed = True
    else:
        print(f"  PASS Gen 1:1: {gen_1_1!r}")

    if failed:
        return 1
    print("PASS: self-test assertions held.")
    return 0


# ─── CLI ────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--book", help="Single book key (e.g. genesis, jonah)")
    p.add_argument("--all", action="store_true", help="Run all books")
    p.add_argument("--force", action="store_true", help="Overwrite existing outputs")
    p.add_argument("--self-test", action="store_true", help="Run Gen 1 self-test")
    args = p.parse_args(argv)

    if args.self_test:
        return _self_test()

    print(f"Loading MetaV index from {METAV_DIR}...")
    metav_index = load_kjv_strongs_index(METAV_DIR)
    print(f"MetaV verses indexed: {len(metav_index)}")

    if args.all:
        had_error = False
        for book in BOOK_REGISTRY:
            diag = generate_book(book, metav_index, force=args.force)
            if diag.get("error"):
                print(f"  ERROR: {diag['error']}")
                had_error = True
        return 1 if had_error else 0

    if not args.book:
        p.print_help()
        return 2

    diag = generate_book(args.book, metav_index, force=args.force)
    if diag.get("error"):
        print(f"ERROR: {diag['error']}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
