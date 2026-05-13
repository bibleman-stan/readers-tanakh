"""Build a closed-list hendiadys/doublet/merism lexicon for the Tanakh validator suite.

# audit-skippable: mechanical ingestion-script change — no classification logic; just plumbing data through layers

Phase A: door43 unfoldingWord Translation Notes
  research/macula-hebrew/sources/door43/UTN-figures-of-speech-OT.tsv
  Filters figs-hendiadys / figs-doublet / figs-merism, normalizes to v2 slugs.

Phase B: Bullinger 1898, *Figures of Speech Used in the Bible*, HENDIADYS chapter
  research/bullinger/figuresofspeechu00bull_djvu.txt
  PD plain-text from Internet Archive; OT-only verse-refs extracted.

Aggregator merges both sources; dedupes on (book, chapter, verse, figure).
Output: data/syntax-reference/hendiadys-lexicon.tsv

Future phases (not in this script):
  Phase C - Stan-side Lillas 2012 PDF + TSK + Logos exports
  Phase D - corpus-derived candidate generator (BHSA rela=Link/Para/Appo +
            Macula coredomain co-occurrence)
"""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_DOOR43 = REPO / "research" / "macula-hebrew" / "sources" / "door43" / "UTN-figures-of-speech-OT.tsv"
SRC_BULLINGER = REPO / "research" / "bullinger" / "figuresofspeechu00bull_djvu.txt"
DST = REPO / "data" / "syntax-reference" / "hendiadys-lexicon.tsv"

DOOR43_TAGS = {"figs-hendiadys", "figs-doublet", "figs-merism"}

# door43 3-letter book codes -> v2/heb book slug
DOOR43_BOOK_SLUGS = {
    "GEN": "01-genesis", "EXO": "02-exodus", "LEV": "03-leviticus",
    "NUM": "04-numbers", "DEU": "05-deuteronomy", "JOS": "06-joshua",
    "JDG": "07-judges", "RUT": "08-ruth", "1SA": "09-1samuel",
    "2SA": "10-2samuel", "1KI": "11-1kings", "2KI": "12-2kings",
    "1CH": "13-1chronicles", "2CH": "14-2chronicles", "EZR": "15-ezra",
    "NEH": "16-nehemiah", "EST": "17-esther", "JOB": "18-job",
    "PSA": "19-psalms", "PRO": "20-proverbs", "ECC": "21-ecclesiastes",
    "SNG": "22-songofsongs", "ISA": "23-isaiah", "JER": "24-jeremiah",
    "LAM": "25-lamentations", "EZK": "26-ezekiel", "DAN": "27-daniel",
    "HOS": "28-hosea", "JOL": "29-joel", "AMO": "30-amos",
    "OBA": "31-obadiah", "JON": "32-jonah", "MIC": "33-micah",
    "NAM": "34-nahum", "HAB": "35-habakkuk", "ZEP": "36-zephaniah",
    "HAG": "37-haggai", "ZEC": "38-zechariah", "MAL": "39-malachi",
}

# Bullinger Victorian-era abbreviations -> v2/heb slug (OT only; NT silently drops)
BULLINGER_BOOK_SLUGS = {
    "Gen": "01-genesis", "Exod": "02-exodus", "Ex": "02-exodus",
    "Lev": "03-leviticus", "Num": "04-numbers",
    "Deut": "05-deuteronomy", "Josh": "06-joshua", "Judg": "07-judges",
    "Ruth": "08-ruth",
    "1 Sam": "09-1samuel", "2 Sam": "10-2samuel",
    "1 Kings": "11-1kings", "2 Kings": "12-2kings",
    "1 Ki": "11-1kings", "2 Ki": "12-2kings",
    "1 Chron": "13-1chronicles", "2 Chron": "14-2chronicles",
    "1 Ch": "13-1chronicles", "2 Ch": "14-2chronicles",
    "Ezra": "15-ezra", "Neh": "16-nehemiah",
    "Est": "17-esther", "Esth": "17-esther",
    "Job": "18-job",
    "Ps": "19-psalms", "Psa": "19-psalms", "Psalm": "19-psalms",
    "Prov": "20-proverbs",
    "Eccl": "21-ecclesiastes", "Eccles": "21-ecclesiastes",
    "Cant": "22-songofsongs", "Song": "22-songofsongs",
    "Isa": "23-isaiah", "Jer": "24-jeremiah", "Lam": "25-lamentations",
    "Ezek": "26-ezekiel", "Ezk": "26-ezekiel",
    "Dan": "27-daniel", "Hos": "28-hosea", "Joel": "29-joel",
    "Amos": "30-amos", "Obad": "31-obadiah", "Jon": "32-jonah",
    "Mic": "33-micah", "Nah": "34-nahum", "Hab": "35-habakkuk",
    "Zeph": "36-zephaniah", "Hag": "37-haggai", "Zech": "38-zechariah",
    "Mal": "39-malachi",
}

# Bullinger HENDIADYS chapter line-range in the IA djvu OCR
BULLINGER_HENDIADYS_LINES = (37509, 38328)


def _normalize_note(note: str) -> str:
    """Strip the trailing rc:// link cruft from door43 translator notes."""
    if "(See:" in note:
        note = note.split("(See:")[0].rstrip()
    return note.strip()


def _roman_to_int(s: str) -> int | None:
    """Lowercase roman numeral -> int. Returns None on parse failure."""
    s = s.lower().strip()
    if not s or not all(c in "ivxlcdm" for c in s):
        return None
    values = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
    total = 0
    prev = 0
    for c in reversed(s):
        v = values[c]
        if v < prev:
            total -= v
        else:
            total += v
        prev = v
    return total if total > 0 else None


def _load_door43() -> list[tuple]:
    """Phase A: read door43 figures-of-speech TSV, return list of lexicon rows."""
    rows_in = list(csv.reader(SRC_DOOR43.open(encoding="utf-8"), delimiter="\t"))
    expected = ["Book", "Chapter", "Verse", "ID", "SupportReference",
                "OrigQuote", "Occurrence", "GLQuote", "OccurrenceNote", "VerseId"]
    if rows_in[0] != expected:
        raise RuntimeError(f"door43 schema drift: got {rows_in[0]}")

    out = []
    skipped_book = Counter()
    for r in rows_in[1:]:
        if len(r) < 9 or r[4] not in DOOR43_TAGS:
            continue
        slug = DOOR43_BOOK_SLUGS.get(r[0])
        if slug is None:
            skipped_book[r[0]] += 1
            continue
        try:
            chapter = int(r[1])
            verse = int(r[2])
        except ValueError:
            continue
        figure = r[4].removeprefix("figs-")
        gl = r[7].strip()
        note = _normalize_note(r[8])
        out.append((slug, chapter, verse, figure, gl, note, "door43_utn"))
    if skipped_book:
        print(f"  door43 skipped book codes: {dict(skipped_book)}", file=sys.stderr)
    return out


def _load_bullinger() -> list[tuple]:
    """Phase B: parse Bullinger 1898 HENDIADYS chapter, return list of lexicon rows.

    Pattern: book-abbrev + roman-chapter + arabic-verse, optionally followed within
    a short window by a quoted English snippet. NT refs are silently dropped via
    the OT-only book mapping.
    """
    text = SRC_BULLINGER.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    start, end = BULLINGER_HENDIADYS_LINES
    chapter = "\n".join(lines[start:end])
    chapter = re.sub(r"[ \t]+", " ", chapter)

    # Sort book abbreviations longest-first so "1 Sam" matches before "Sam" etc.
    abbrevs = sorted(BULLINGER_BOOK_SLUGS.keys(), key=len, reverse=True)
    book_alt = "|".join(re.escape(a) for a in abbrevs)
    # ref pattern: (book) "." (roman) "." (verse). Optional snippet within ~400 chars.
    ref_re = re.compile(
        r"(?P<book>" + book_alt + r")\.?\s+(?P<roman>[ivxlc]+)\.\s*(?P<verse>\d+)"
        r"(?P<after>(?:\.[^\"]{0,400}\"(?P<snippet>[^\"]{1,200})\")?)",
        re.S,
    )

    out = []
    for m in ref_re.finditer(chapter):
        book_abbrev = m.group("book")
        slug = BULLINGER_BOOK_SLUGS.get(book_abbrev)
        if slug is None:
            continue
        roman = m.group("roman")
        ch_int = _roman_to_int(roman)
        if ch_int is None:
            continue
        try:
            v_int = int(m.group("verse"))
        except (TypeError, ValueError):
            continue
        snippet = m.group("snippet") or ""
        snippet = re.sub(r"\s+", " ", snippet).strip()
        # Bullinger's HENDIADYS chapter classifies every entry as hendiadys.
        out.append((slug, ch_int, v_int, "hendiadys", snippet, "", "bullinger_1898"))
    return out


def main() -> int:
    if not SRC_DOOR43.exists():
        print(f"ERROR: door43 source not found at {SRC_DOOR43}", file=sys.stderr)
        return 1
    if not SRC_BULLINGER.exists():
        print(f"ERROR: bullinger source not found at {SRC_BULLINGER}", file=sys.stderr)
        print(f"  fetch with:", file=sys.stderr)
        print(f"    mkdir -p {SRC_BULLINGER.parent.relative_to(REPO)}", file=sys.stderr)
        print(f"    curl -sL -o {SRC_BULLINGER.relative_to(REPO)} \\", file=sys.stderr)
        print(f"      https://archive.org/download/figuresofspeechu00bull/figuresofspeechu00bull_djvu.txt",
              file=sys.stderr)
        print(f"  (PD plain-text DjVu OCR; license: NOT_IN_COPYRIGHT per IA metadata)",
              file=sys.stderr)
        return 1

    door43 = _load_door43()
    bullinger = _load_bullinger()
    print(f"  door43 entries: {len(door43)}")
    print(f"  bullinger entries (raw): {len(bullinger)}")

    # Dedup on (book, chapter, verse, figure). When the same key appears in
    # both sources, prefer door43 (richer translator note + GLQuote anchor)
    # but keep both source labels so coverage attribution is preserved.
    by_key: dict[tuple, tuple] = {}
    cross_attrib = 0
    for row in door43 + bullinger:
        key = (row[0], row[1], row[2], row[3])
        if key in by_key:
            existing = by_key[key]
            if existing[6] != row[6]:
                src_combined = "+".join(sorted({existing[6], row[6]}))
                by_key[key] = existing[:6] + (src_combined,)
                cross_attrib += 1
        else:
            by_key[key] = row

    hits = sorted(by_key.values(), key=lambda x: (x[0], x[1], x[2], x[3]))

    DST.parent.mkdir(parents=True, exist_ok=True)
    with DST.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["book", "chapter", "verse", "figure", "english_snippet",
                    "note", "source"])
        w.writerows(hits)

    by_figure = Counter(h[3] for h in hits)
    by_book = Counter(h[0] for h in hits)
    by_source = Counter(h[6] for h in hits)
    print(f"Wrote {len(hits)} unique entries to {DST.relative_to(REPO)}")
    print(f"  by figure: {dict(by_figure)}")
    print(f"  by source: {dict(by_source)}")
    print(f"  cross-attributed (both sources): {cross_attrib}")
    print(f"  books covered: {len(by_book)} / 39")
    return 0


if __name__ == "__main__":
    sys.exit(main())
