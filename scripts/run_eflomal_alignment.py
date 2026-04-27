"""
run_eflomal_alignment.py — Run eflomal bilingual alignment on Hebrew
verses paired with eng-gloss English verses.

Usage:
    py -3.12 scripts/run_eflomal_alignment.py --books jonah --output data/alignment/corpus-alignment.json
    py -3.12 scripts/run_eflomal_alignment.py --all --output data/alignment/corpus-alignment.json

Output JSON shape:
    {
        "jonah": {
            "1:1": [[hi, ei], [hi, ei], ...],
            "1:2": [...],
            ...
        },
        "genesis": {...},
        ...
    }
    — hi is Hebrew token index, ei is English token index (both 0-based,
      after niqqud/te'amim strip + NFC normalize + whitespace-split).

Source preference (per tier cascade used by build_books.py):
    Hebrew:  v2/he/<subdir>/  >  v1/he-baseline/<subdir>/
    English: v2/eng-gloss/<subdir>/  >  v1/eng-gloss/<subdir>/

Hebrew preprocessing:
    1. NFC normalize
    2. Strip niqqud + te'amim (U+0591–U+05C7) leaving consonant skeleton
    3. Strip sof-pasuq (׃ U+05C3), paseq (׀ U+05C0), maqaf (־ U+05BE joins
       words into single alignment token — not split, preserving prosodic unit)
    4. Lowercase not applicable (Hebrew is caseless); whitespace-split

English preprocessing:
    Strip ASCII + Unicode punctuation, lowercase, whitespace split.

Requires:
    - Python 3.12 (eflomal built against 3.12; call as py -3.12)
    - eflomal installed: CC=gcc py -3.12 -m pip install eflomal
    - Hebrew and English text files present under data/text-files/

Windows note: forward-only alignment only (eflomal binary segfaults on reverse
alignment writes on Windows — same constraint as the GNT sibling pipeline).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import Optional

try:
    from eflomal import Aligner
except ImportError:
    sys.exit(
        "eflomal is not installed on this Python interpreter.\n"
        "Run: CC=gcc py -3.12 -m pip install eflomal\n"
        "(Python 3.12 required; eflomal is not yet packaged for 3.13+)"
    )

# ---------------------------------------------------------------------------
# Repo layout
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent

_V2_HE_ROOT   = _REPO_ROOT / "data" / "text-files" / "v2" / "he"
_V1_HE_ROOT   = _REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
_V2_ENG_ROOT  = _REPO_ROOT / "data" / "text-files" / "v2" / "eng-gloss"
_V1_ENG_ROOT  = _REPO_ROOT / "data" / "text-files" / "v1" / "eng-gloss"

# ---------------------------------------------------------------------------
# Book registry — mirrors build_books.py BOOK_REGISTRY (slug → subdir)
# ---------------------------------------------------------------------------

BOOK_REGISTRY: dict[str, str] = {
    "genesis":      "01-genesis",
    "exodus":       "02-exodus",
    "leviticus":    "03-leviticus",
    "numbers":      "04-numbers",
    "deuteronomy":  "05-deuteronomy",
    "joshua":       "06-joshua",
    "judges":       "07-judges",
    "ruth":         "08-ruth",
    "1samuel":      "09-1samuel",
    "2samuel":      "10-2samuel",
    "1kings":       "11-1kings",
    "2kings":       "12-2kings",
    "1chronicles":  "13-1chronicles",
    "2chronicles":  "14-2chronicles",
    "ezra":         "15-ezra",
    "nehemiah":     "16-nehemiah",
    "esther":       "17-esther",
    "job":          "18-job",
    "psalms":       "19-psalms",
    "proverbs":     "20-proverbs",
    "ecclesiastes": "21-ecclesiastes",
    "songofsongs":  "22-songofsongs",
    "isaiah":       "23-isaiah",
    "jeremiah":     "24-jeremiah",
    "lamentations": "25-lamentations",
    "ezekiel":      "26-ezekiel",
    "daniel":       "27-daniel",
    "hosea":        "28-hosea",
    "joel":         "29-joel",
    "amos":         "30-amos",
    "obadiah":      "31-obadiah",
    "jonah":        "32-jonah",
    "micah":        "33-micah",
    "nahum":        "34-nahum",
    "habakkuk":     "35-habakkuk",
    "zephaniah":    "36-zephaniah",
    "haggai":       "37-haggai",
    "zechariah":    "38-zechariah",
    "malachi":      "39-malachi",
}

BOOK_SLUGS: list[str] = list(BOOK_REGISTRY.keys())

# ---------------------------------------------------------------------------
# Text preprocessing
# ---------------------------------------------------------------------------

# Hebrew diacritic range: cantillation accents + niqqud (U+0591–U+05C7)
# Also strip: sof-pasuq ׃ (U+05C3), paseq ׀ (U+05C0)
# Maqqef ־ (U+05BE) is kept as a hyphen-equivalent so that
# maqqef-joined words form one alignment token (a prosodic unit).
_HE_DIACRITIC_RE = re.compile(
    "["
    "֑-ׇ"  # Hebrew combining marks: te'amim + niqqud
    "׀"         # paseq ׀
    "׃"         # sof-pasuq ׃
    "]"
)

# English punctuation to strip
_ENG_PUNCT_CHARS = "".join([
    ".", ",", ";", ":", "?", "!",
    "(", ")", "[", "]", "{", "}",
    "—", "–", "-",      # em dash, en dash, hyphen
    '"', "'", "`",
    "‘", "’",           # curly single quotes
    "“", "”",           # curly double quotes
    "ʼ",                     # modifier letter apostrophe
])
_ENG_PUNCT_RE = re.compile("[" + re.escape(_ENG_PUNCT_CHARS) + "]")
_WS_RE = re.compile(r"\s+")

_VERSE_REF_RE = re.compile(r"^\d+:\d+$")


def normalize_hebrew(text: str) -> str:
    """NFC-normalize then strip niqqud/te'amim/sof-pasuq/paseq.

    Maqqef is kept so maqqef-bound pairs become a single space-separated
    token (e.g. 'כִּי־אִם' becomes 'כי־אם', one token). This preserves
    prosodic-unit identity and prevents false alignment splits.
    """
    text = unicodedata.normalize("NFC", text)
    text = _HE_DIACRITIC_RE.sub("", text)
    text = _WS_RE.sub(" ", text).strip()
    return text


def normalize_english(text: str) -> str:
    """Strip punctuation, lowercase, collapse whitespace."""
    text = _ENG_PUNCT_RE.sub(" ", text)
    text = text.lower()
    text = _WS_RE.sub(" ", text).strip()
    return text


# ---------------------------------------------------------------------------
# File parsing
# ---------------------------------------------------------------------------

def _read_text_file(path: Path) -> str:
    """Read a text file, trying UTF-8 then UTF-8-SIG."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def parse_chapter_file(path: Path) -> list[dict]:
    """Parse one chapter .txt into a list of {ref, lines} dicts.

    Format expected:
        1:1
        line1 of verse 1
        line2 of verse 1

        1:2
        line1 of verse 2
        ...

    Returns [{"ref": "1:1", "lines": ["line1", "line2"]}, ...]
    """
    raw_lines = _read_text_file(path).splitlines()
    verses: list[dict] = []
    current: Optional[dict] = None

    for raw in raw_lines:
        line = raw.rstrip("\r\n")
        stripped = line.strip()

        if _VERSE_REF_RE.match(stripped):
            if current is not None and current["lines"]:
                verses.append(current)
            current = {"ref": stripped, "lines": []}
            continue

        if stripped == "":
            if current is not None and current["lines"]:
                verses.append(current)
                current = None
            continue

        if current is not None:
            current["lines"].append(line)

    if current is not None and current["lines"]:
        verses.append(current)

    return verses


def _find_book_dir(root: Path, subdir: str) -> Optional[Path]:
    """Resolve the book directory under root.

    Tries exact subdir match first (e.g. '32-jonah'), then
    falls back to a suffix match so legacy '05-jonah'-style
    artifacts are skipped when the canonical subdir exists.
    """
    candidate = root / subdir
    if candidate.is_dir():
        return candidate
    # Secondary: scan for any dir whose name ends in the book name part
    book_name = subdir.split("-", 1)[-1] if "-" in subdir else subdir
    for entry in sorted(root.iterdir()):
        if entry.is_dir() and entry.name.endswith(f"-{book_name}"):
            return entry
    return None


def load_book_verses(
    book: str,
    he_preferred: Path,
    he_fallback: Path,
    eng_preferred: Path,
    eng_fallback: Path,
) -> tuple[dict[tuple[int, int], str], dict[tuple[int, int], str]]:
    """Load all verses for a book from the appropriate tier dirs.

    Returns two dicts keyed by (chapter, verse):
        (hebrew_verses, english_verses)
    Each value is the verse's cola joined into one flat string (verse-level
    alignment granularity).

    Tier preference: preferred tier dir if the book subdir exists there,
    otherwise fallback.
    """
    subdir = BOOK_REGISTRY[book]

    # Resolve Hebrew source dir
    he_dir = _find_book_dir(he_preferred, subdir) or _find_book_dir(he_fallback, subdir)
    if he_dir is None:
        raise FileNotFoundError(
            f"Hebrew dir not found for '{book}' (subdir '{subdir}') "
            f"under {he_preferred} or {he_fallback}"
        )

    # Resolve English source dir
    eng_dir = (
        _find_book_dir(eng_preferred, subdir) or _find_book_dir(eng_fallback, subdir)
    )
    if eng_dir is None:
        raise FileNotFoundError(
            f"English gloss dir not found for '{book}' (subdir '{subdir}') "
            f"under {eng_preferred} or {eng_fallback}"
        )

    def _load_dir(d: Path) -> dict[tuple[int, int], str]:
        result: dict[tuple[int, int], str] = {}
        for chapter_file in sorted(d.iterdir()):
            if not chapter_file.name.endswith(".txt"):
                continue
            for v in parse_chapter_file(chapter_file):
                ref = v["ref"]
                ch_s, vs_s = ref.split(":", 1)
                key = (int(ch_s), int(vs_s))
                # Join cola with a space: verse-level alignment unit
                result[key] = " ".join(v["lines"])
        return result

    return _load_dir(he_dir), _load_dir(eng_dir)


# ---------------------------------------------------------------------------
# Alignment
# ---------------------------------------------------------------------------

def align_book(book: str) -> dict[str, list[list[int]]]:
    """Run eflomal alignment for one book's Hebrew ↔ English verses.

    Returns {"ch:vs": [[hi, ei], ...]} for every verse pair present
    in both Hebrew and English corpora.
    """
    print(f"  Loading '{book}'...", file=sys.stderr, flush=True)

    hebrew_verses, english_verses = load_book_verses(
        book,
        he_preferred=_V2_HE_ROOT,
        he_fallback=_V1_HE_ROOT,
        eng_preferred=_V2_ENG_ROOT,
        eng_fallback=_V1_ENG_ROOT,
    )

    # Pair verses present in both corpora
    shared_keys = sorted(set(hebrew_verses.keys()) & set(english_verses.keys()))
    pairs: list[tuple[tuple[int, int], str, str]] = []

    for key in shared_keys:
        h = normalize_hebrew(hebrew_verses[key])
        e = normalize_english(english_verses[key])
        if h and e:
            pairs.append((key, h, e))

    if not pairs:
        print(f"  WARNING: no verse pairs found for '{book}'", file=sys.stderr)
        return {}

    # Write src/trg sentence files for eflomal
    tmp_dir = Path(tempfile.mkdtemp(prefix=f"eflomal_{book}_"))
    src_path = tmp_dir / "src.txt"   # Hebrew (source)
    trg_path = tmp_dir / "trg.txt"   # English (target)
    fwd_path = tmp_dir / "fwd.align"

    try:
        with src_path.open("w", encoding="utf-8") as fsrc, \
             trg_path.open("w", encoding="utf-8") as ftrg:
            for _, h, e in pairs:
                fsrc.write(h + "\n")
                ftrg.write(e + "\n")

        aligner = Aligner()
        with src_path.open(encoding="utf-8") as fsrc, \
             trg_path.open(encoding="utf-8") as ftrg:
            aligner.align(
                fsrc,
                ftrg,
                links_filename_fwd=str(fwd_path),
                # Reverse alignment skipped — eflomal binary segfaults on
                # Windows when writing rev.align (0xC0000005 access violation).
                # Forward-only (Hebrew→English) is sufficient for the
                # gloss-redistribution use case.
                links_filename_rev=None,
                quiet=True,
            )

        result: dict[str, list[list[int]]] = {}

        with fwd_path.open(encoding="utf-8") as f:
            alignment_lines = f.readlines()

        if len(alignment_lines) != len(pairs):
            print(
                f"  WARNING {book}: pair count {len(pairs)} != "
                f"alignment line count {len(alignment_lines)}",
                file=sys.stderr,
            )

        for (key, _, _), line in zip(pairs, alignment_lines):
            pair_list: list[list[int]] = []
            for tok in line.strip().split():
                if "-" in tok:
                    h_s, e_s = tok.split("-", 1)
                    try:
                        pair_list.append([int(h_s), int(e_s)])
                    except ValueError:
                        continue
            result[f"{key[0]}:{key[1]}"] = pair_list

        return result

    finally:
        for p in [src_path, trg_path, fwd_path]:
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass
        try:
            tmp_dir.rmdir()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run eflomal bilingual alignment on Hebrew ↔ English verse pairs.\n"
            "Requires Python 3.12 and eflomal: CC=gcc py -3.12 -m pip install eflomal"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--books",
        nargs="+",
        metavar="BOOK",
        help=(
            "One or more book slugs to align (e.g. jonah genesis). "
            "Use --all for all 39 books."
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Align all 39 books.",
    )
    parser.add_argument(
        "--output",
        required=True,
        metavar="PATH",
        help="Output JSON path (e.g. data/alignment/corpus-alignment.json).",
    )
    args = parser.parse_args()

    if args.all:
        books = BOOK_SLUGS
    elif args.books:
        unknown = [b for b in args.books if b not in BOOK_REGISTRY]
        if unknown:
            parser.error(
                f"Unknown book slug(s): {unknown!r}. "
                f"Valid slugs: {BOOK_SLUGS}"
            )
        books = args.books
    else:
        parser.error("Specify either --books <slug ...> or --all")

    result: dict[str, dict[str, list[list[int]]]] = {}

    for book in books:
        print(f"Aligning {book}...", file=sys.stderr, flush=True)
        try:
            book_alignment = align_book(book)
            result[book] = book_alignment
            print(
                f"  {book}: {len(book_alignment)} verse alignments",
                file=sys.stderr,
                flush=True,
            )
        except FileNotFoundError as exc:
            print(f"  {book}: SKIPPED — {exc}", file=sys.stderr)
            result[book] = {}
        except Exception as exc:
            print(f"  {book}: FAILED — {exc}", file=sys.stderr)
            result[book] = {}

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    total_verses = sum(len(v) for v in result.values())
    print(
        f"\nWrote alignments for {len(result)} book(s) "
        f"({total_verses} verses total) → {output_path}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
