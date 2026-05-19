#!/usr/bin/env python3
"""
run_full_tanakh.py — batch ATU pipeline over the entire Tanakh.

Loads BHSA via Text-Fabric ONCE, iterates over all (book, chapter) pairs that
have a v0/prose source file in the repo, applies the binding-rule catalog
(`binding_rules.apply_bindings`), and writes one v2/heb-format file per chapter
to `data/text-files/v2-pipeline-draft/heb/{book-folder}/{book-stem}.txt`.

The output staging directory is DISTINCT from `data/text-files/v2/heb/` (which
holds hand-edited content). This lets us diff pipeline output against existing
hand-edits without overwriting them.

Per-chapter output format:
  {VERSE_PREFIX}1
  <ATU group 1 text>
  <ATU group 2 text>
  ...

  {VERSE_PREFIX}2
  ...

Usage:
  py -3 scripts/atu_pipeline_v2/run_full_tanakh.py [--book FOLDER] [--limit N]

  --book FOLDER : Process a single book (e.g., --book 01-genesis). Default: all 39 books.
  --limit N     : Process only the first N chapters per book (useful for testing).
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

# Make the binding-rules module importable from this script's dir
sys.path.insert(0, str(Path(__file__).parent))
from binding_rules import apply_bindings

from tf.app import use


REPO = Path(r"C:\Users\bibleman\repos\readers-tanakh")
V0_DIR = REPO / "data/text-files/v0/prose"
OUT_DIR = REPO / "data/text-files/v2-pipeline-draft/heb"

# Map repo folder name → BHSA book name (Text-Fabric standard).
BOOK_FOLDER_TO_BHSA = {
    "01-genesis": "Genesis",
    "02-exodus": "Exodus",
    "03-leviticus": "Leviticus",
    "04-numbers": "Numbers",
    "05-deuteronomy": "Deuteronomy",
    "06-joshua": "Joshua",
    "07-judges": "Judges",
    "08-ruth": "Ruth",
    "09-1samuel": "1_Samuel",
    "10-2samuel": "2_Samuel",
    "11-1kings": "1_Kings",
    "12-2kings": "2_Kings",
    "13-1chronicles": "1_Chronicles",
    "14-2chronicles": "2_Chronicles",
    "15-ezra": "Ezra",
    "16-nehemiah": "Nehemiah",
    "17-esther": "Esther",
    "18-job": "Job",
    "19-psalms": "Psalms",
    "20-proverbs": "Proverbs",
    "21-ecclesiastes": "Ecclesiastes",
    "22-songofsongs": "Song_of_songs",
    "23-isaiah": "Isaiah",
    "24-jeremiah": "Jeremiah",
    "25-lamentations": "Lamentations",
    "26-ezekiel": "Ezekiel",
    "27-daniel": "Daniel",
    "28-hosea": "Hosea",
    "29-joel": "Joel",
    "30-amos": "Amos",
    "31-obadiah": "Obadiah",
    "32-jonah": "Jonah",
    "33-micah": "Micah",
    "34-nahum": "Nahum",
    "35-habakkuk": "Habakkuk",
    "36-zephaniah": "Zephaniah",
    "37-haggai": "Haggai",
    "38-zechariah": "Zechariah",
    "39-malachi": "Malachi",
}


def discover_chapters(book_folder: str) -> list[tuple[int, Path]]:
    """Return [(chapter_num, source_path), ...] for a book's v0/prose files."""
    book_dir = V0_DIR / book_folder
    if not book_dir.exists():
        return []
    chapters = []
    for f in sorted(book_dir.glob("*.txt")):
        # filenames look like genesis-22.txt or psalms-150.txt
        stem = f.stem  # e.g. "genesis-22" or "psalms-150"
        if "-" not in stem:
            continue
        # chapter number is the part after the final dash that's all digits
        parts = stem.rsplit("-", 1)
        if len(parts) != 2 or not parts[1].isdigit():
            continue
        chapter_num = int(parts[1])
        chapters.append((chapter_num, f))
    return chapters


def parse_v0_prose(path: Path) -> dict[int, str]:
    """Return {verse_num: v0_text} from a v0/prose verse-headed file."""
    if not path.exists():
        return {}
    import re
    verse_header_re = re.compile(r"^\d+:(\d+)\s*$")
    verses: dict[int, str] = {}
    current: int | None = None
    buf: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            if current is not None and buf:
                verses[current] = " ".join(buf).strip()
                current, buf = None, []
            continue
        m = verse_header_re.match(line)
        if m:
            if current is not None and buf:
                verses[current] = " ".join(buf).strip()
            current = int(m.group(1))
            buf = []
        else:
            buf.append(line)
    if current is not None and buf:
        verses[current] = " ".join(buf).strip()
    return verses


def extract_clauses_for_chapter(api, book_name: str, chapter_num: int, v0_text_by_verse: dict[int, str]) -> list[dict]:
    """Query BHSA for clause-atoms in (book, chapter); return clause dicts.

    Each clause-atom records its v0-token-index range within its verse,
    derived by counting whitespace-trailers in BHSA. This lets us emit
    v0/prose-derived text (TAHOT-encoded) instead of BHSA-encoded text
    so downstream cascades that enforce word-stream-invariance pass.
    """
    F = api.F
    L = api.L
    T = api.T

    target_chapters = [
        c for c in F.otype.s("chapter")
        if T.sectionFromNode(c)[:2] == (book_name, chapter_num)
    ]
    if not target_chapters:
        return []
    chapter = target_chapters[0]

    # Precompute v0-token-index per BHSA word within each verse.
    # A v0-token boundary is a BHSA word whose trailer is whitespace
    # (space, newline). Maqaf trailers stay within the same v0-token.
    verses_in_chapter = list(L.d(chapter, otype="verse"))
    word_to_v0_idx: dict[int, int] = {}  # bhsa word node -> v0_token_index in its verse

    for v in verses_in_chapter:
        v0_idx = 0
        verse_words = list(L.d(v, otype="word"))
        for i, w in enumerate(verse_words):
            word_to_v0_idx[w] = v0_idx
            trailer = F.trailer_utf8.v(w) or ""
            # If trailer contains whitespace, this word ends the current v0-token
            if any(ch.isspace() for ch in trailer):
                v0_idx += 1

    clause_atoms = list(L.d(chapter, otype="clause_atom"))
    verse_counters: dict[int, int] = {}
    rows: list[dict] = []

    for ca in clause_atoms:
        words = L.d(ca, otype="word")
        if not words:
            continue
        first_word = words[0]
        _, _, verse_num = T.sectionFromNode(first_word)
        idx_in_verse = verse_counters.get(verse_num, 0)
        verse_counters[verse_num] = idx_in_verse + 1

        # v0-token-index range for this clause-atom
        v0_first = word_to_v0_idx.get(words[0], 0)
        v0_last = word_to_v0_idx.get(words[-1], 0)

        # BHSA-encoded text (kept for diagnostics, NOT for output)
        word_texts = [F.g_word_utf8.v(w) + F.trailer_utf8.v(w) for w in words]
        bhsa_text = "".join(word_texts).strip()

        typ = F.typ.v(ca) or ""
        domain = F.domain.v(ca) or ""
        rela = F.rela.v(ca) or ""

        head_verb_lemma = ""
        head_verb_text = ""
        for w in words:
            if F.pdp.v(w) == "verb":
                head_verb_lemma = F.lex_utf8.v(w) or ""
                head_verb_text = F.g_word_utf8.v(w) or ""
                break

        rows.append({
            "cid": ca,
            "verse": verse_num,
            "clause_idx_in_verse": idx_in_verse,
            "typ": typ,
            "domain": domain,
            "rela": rela,
            "head_verb_lemma": head_verb_lemma,
            "head_verb_text": head_verb_text,
            "text": bhsa_text,  # used by binding rules for consonant matching
            "v0_token_first": v0_first,
            "v0_token_last": v0_last,
        })

    return rows


def render_v2_heb_format(groups: list[dict], v0_text_by_verse: dict[int, str], chapter_num: int) -> str:
    """Render ATU groups as v2/heb-format text using v0/prose word forms.

    Each group's text is reconstructed by taking v0/prose tokens at the
    v0-token-index range derived from BHSA. This preserves TAHOT-encoded
    word forms (matching v1/he-baseline) so downstream cascades pass the
    word-stream-invariance integrity gate.
    """
    by_verse: dict[int, list[dict]] = {}
    for g in groups:
        by_verse.setdefault(g["verse_first"], []).append(g)

    lines: list[str] = []
    for v in sorted(by_verse.keys()):
        v0_text = v0_text_by_verse.get(v, "")
        v0_tokens = v0_text.split()
        lines.append(f"{chapter_num}:{v}")
        for g in by_verse[v]:
            # Take v0-token range from min(v0_token_first) to max(v0_token_last)
            # across all clauses in this group
            v0_first = min(c.get("v0_token_first", 0) for c in g["clauses_full"])
            v0_last = max(c.get("v0_token_last", 0) for c in g["clauses_full"])
            atu_tokens = v0_tokens[v0_first : v0_last + 1]
            if atu_tokens:
                lines.append(" ".join(atu_tokens))
            else:
                # Fallback: BHSA text if v0 mapping failed
                lines.append(g["text"])
        lines.append("")  # blank line between verses

    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--book", default=None, help="Single book folder (e.g., 01-genesis); default all 39")
    p.add_argument("--limit", type=int, default=None, help="Limit chapters per book")
    args = p.parse_args()

    # Determine book list
    if args.book:
        if args.book not in BOOK_FOLDER_TO_BHSA:
            print(f"ERROR: unknown book folder '{args.book}'", file=sys.stderr)
            sys.exit(1)
        book_folders = [args.book]
    else:
        book_folders = list(BOOK_FOLDER_TO_BHSA.keys())

    print(f"Loading BHSA via Text-Fabric (first run downloads ~100MB)...")
    A = use("etcbc/bhsa", silent="deep")
    api = A.api
    print("BHSA loaded.")

    total_chapters = 0
    total_clauses = 0
    total_groups = 0
    skipped_chapters = []

    for book_folder in book_folders:
        book_name = BOOK_FOLDER_TO_BHSA[book_folder]
        chapters = discover_chapters(book_folder)
        if args.limit:
            chapters = chapters[:args.limit]
        if not chapters:
            print(f"  {book_folder}: no source files found, skipping")
            continue

        book_out_dir = OUT_DIR / book_folder
        book_out_dir.mkdir(parents=True, exist_ok=True)

        print(f"  {book_folder} ({book_name}): {len(chapters)} chapters", end=" ", flush=True)

        for chapter_num, source_path in chapters:
            v0_text_by_verse = parse_v0_prose(source_path)
            clauses = extract_clauses_for_chapter(api, book_name, chapter_num, v0_text_by_verse)
            if not clauses:
                skipped_chapters.append((book_folder, chapter_num))
                print(".", end="", flush=True)
                continue

            groups_raw = apply_bindings(clauses)

            # Attach the original clause records to each group so render step has v0_token spans
            for g in groups_raw:
                clauses_full = [c for c in clauses if c["cid"] in g["clause_cids"]]
                g["clauses_full"] = clauses_full

            rendered = render_v2_heb_format(groups_raw, v0_text_by_verse, chapter_num)
            out_path = book_out_dir / source_path.name
            out_path.write_text(rendered, encoding="utf-8")
            total_chapters += 1
            total_clauses += len(clauses)
            total_groups += len(groups_raw)
            print(".", end="", flush=True)
        print()

    print()
    print(f"--- Batch summary ---")
    print(f"  Chapters processed: {total_chapters}")
    print(f"  Clause atoms extracted: {total_clauses}")
    print(f"  ATU candidate groups produced: {total_groups}")
    print(f"  Chapters skipped (no BHSA data): {len(skipped_chapters)}")
    if skipped_chapters:
        print(f"  Skipped: {skipped_chapters[:10]}{'...' if len(skipped_chapters) > 10 else ''}")
    print()
    print(f"Output staging dir: {OUT_DIR}")
    print(f"Format: v2/heb-style (verse-headed, one ATU per line)")
    print(f"Compare against hand-edits: diff with data/text-files/v2/heb/")


if __name__ == "__main__":
    main()
