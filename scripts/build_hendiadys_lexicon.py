"""Build a closed-list hendiadys/doublet/merism lexicon for the Tanakh validator suite.

# audit-skippable: mechanical ingestion-script change — no classification logic; just plumbing data through layers

Phase A source: door43 unfoldingWord Translation Notes
(research/macula-hebrew/sources/door43/UTN-figures-of-speech-OT.tsv).

Filters to figs-hendiadys / figs-doublet / figs-merism, normalizes door43
book codes to v2/he book slugs, emits a TSV at
validators/_shared/hendiadys_pairs.tsv.

Future phases (not in this script):
  Phase B - Bullinger 1898 (PD, archive.org) hendiadys chapter scrape
  Phase C - Stan-side Lillas 2012 PDF + TSK + Logos exports
  Phase D - corpus-derived candidate generator (BHSA rela=Link/Para/Appo +
            Macula coredomain co-occurrence)
"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "research" / "macula-hebrew" / "sources" / "door43" / "UTN-figures-of-speech-OT.tsv"
DST = REPO / "validators" / "_shared" / "hendiadys_pairs.tsv"

TARGET_TAGS = {"figs-hendiadys", "figs-doublet", "figs-merism"}

# door43 3-letter book codes -> v2/he book slug
BOOK_SLUGS = {
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


def normalize_note(note: str) -> str:
    """Strip the trailing rc:// link cruft from translator notes."""
    if "(See:" in note:
        note = note.split("(See:")[0].rstrip()
    return note.strip()


def main() -> int:
    if not SRC.exists():
        print(f"ERROR: source TSV not found at {SRC}", file=sys.stderr)
        return 1

    rows_in = list(csv.reader(SRC.open(encoding="utf-8"), delimiter="\t"))
    header = rows_in[0]
    expected = ["Book", "Chapter", "Verse", "ID", "SupportReference",
                "OrigQuote", "Occurrence", "GLQuote", "OccurrenceNote", "VerseId"]
    if header != expected:
        print(f"ERROR: unexpected header schema:\n  got: {header}\n  expected: {expected}",
              file=sys.stderr)
        return 1

    hits = []
    skipped_book = Counter()
    for r in rows_in[1:]:
        if len(r) < 9 or r[4] not in TARGET_TAGS:
            continue
        book_code = r[0]
        slug = BOOK_SLUGS.get(book_code)
        if slug is None:
            skipped_book[book_code] += 1
            continue
        try:
            chapter = int(r[1])
            verse = int(r[2])
        except ValueError:
            continue
        figure = r[4].removeprefix("figs-")
        gl = r[7].strip()
        note = normalize_note(r[8])
        hits.append((slug, chapter, verse, figure, gl, note, "door43_utn"))

    if skipped_book:
        print(f"WARNING: skipped unknown book codes: {dict(skipped_book)}",
              file=sys.stderr)

    hits.sort(key=lambda x: (x[0], x[1], x[2], x[3]))

    DST.parent.mkdir(parents=True, exist_ok=True)
    with DST.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["book", "chapter", "verse", "figure", "english_snippet",
                    "note", "source"])
        w.writerows(hits)

    by_figure = Counter(h[3] for h in hits)
    by_book = Counter(h[0] for h in hits)
    print(f"Wrote {len(hits)} entries to {DST.relative_to(REPO)}")
    print(f"  by figure: {dict(by_figure)}")
    print(f"  books covered: {len(by_book)} / 39")
    return 0


if __name__ == "__main__":
    sys.exit(main())
