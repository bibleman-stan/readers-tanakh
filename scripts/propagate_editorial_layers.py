#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
propagate_editorial_layers.py — re-segment v1 per-word layers to the editorial
Hebrew cola structure.

When the editorial Hebrew layer (data/text-files/v2/heb/) changes cola
structure relative to the v1 he-baseline, the per-word layers (eng-interlinear,
translit, eng-gloss) must follow. v1 has 1:1 alignment between Hebrew
orthographic words and per-word tokens; this script slices those per-word
streams by editorial cola word counts and emits new per-word files keyed to
the editorial cola boundaries.

Per-layer behaviour:
  eng-interlinear, translit  — re-segmented mechanically (perfect 1:1).
  eng-gloss                  — DISABLED post-Wave-6 (2026-05-12).
    v2/eng-kjv (renamed from v2/eng-gloss 2026-05-12) is now KJV verbatim
    from atu_method.kjv_alignment (via scripts/regenerate_english.py).
    The legacy v1-derived structural gloss this script formerly produced
    was a Wave-6 retirement artifact; writing it would silently overwrite
    the KJV substrate. The in-memory computation of ed_gloss_lines is
    preserved for the word-stream-invariant check; only the disk write
    is suppressed.

Word-stream invariant:
  v1 Hebrew word stream MUST equal editorial Hebrew word stream (same words,
  same order, same count). Editorial work only changes line breaks; never
  adds/removes/reorders words. Script exits with error on violation.

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/propagate_editorial_layers.py --book 32-jonah
    PYTHONIOENCODING=utf-8 py -3 scripts/propagate_editorial_layers.py --book 32-jonah --dry-run
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

# Local: deduplicate_gloss for defense-in-depth eng-gloss artifact collapse
# + ANNOTATION_BRACKET_DROP for stripping `[obj.]` placeholders when
# synthesizing gloss from interlinear (which preserves [obj.] markers).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_teamim import deduplicate_gloss, ANNOTATION_BRACKET_DROP  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
TEXT_DIR = REPO_ROOT / "data" / "text-files"

V1_HE_DIR        = TEXT_DIR / "v1" / "he-baseline"
V1_INTER_DIR     = TEXT_DIR / "v1" / "eng-interlinear"
V1_GLOSS_DIR     = TEXT_DIR / "v1" / "eng-gloss"
V1_TRANSLIT_DIR  = TEXT_DIR / "v1" / "translit"

ED_HE_DIR        = TEXT_DIR  / "v2" / "heb"
ED_INTER_DIR     = TEXT_DIR / "v2" / "eng-interlinear"
ED_GLOSS_DIR     = TEXT_DIR / "v2" / "eng-kjv"  # write disabled post-Wave-6 (see write_chapter call below)
ED_TRANSLIT_DIR  = TEXT_DIR / "v2" / "translit"

VERSE_REF_RE = re.compile(r"^\d+:\d+$")
ENG_WORD_SEP = " | "
MAQQEF = "־"


def parse_chapter(path: Path) -> list[tuple[str, list[str]]]:
    """Parse a tier text file into [(verse_ref, [content_lines])]."""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    verses: list[tuple[str, list[str]]] = []
    current_ref: str | None = None
    current_lines: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if VERSE_REF_RE.match(stripped):
            if current_ref is not None and current_lines:
                verses.append((current_ref, current_lines))
            current_ref = stripped
            current_lines = []
            continue
        if stripped == "":
            continue
        if current_ref is not None:
            current_lines.append(line)
    if current_ref is not None and current_lines:
        verses.append((current_ref, current_lines))
    return verses


def he_orth_words(cola: str) -> list[str]:
    """Return ordered orthographic words (whitespace-split, then maqqef-split).

    Each word is NFC-normalized so word-stream comparisons are insensitive
    to combining-mark ordering differences between v1 (parser-emitted) and
    editorial (hand-edited or IDE-rewritten) sources.
    """
    out: list[str] = []
    for tok in cola.split():
        if MAQQEF in tok:
            parts = tok.split(MAQQEF)
            for p in parts[:-1]:
                out.append(unicodedata.normalize("NFC", p + MAQQEF))
            out.append(unicodedata.normalize("NFC", parts[-1]))
        else:
            out.append(unicodedata.normalize("NFC", tok))
    return out


def per_word_tokens(line: str) -> list[str]:
    """Split a per-word layer line on ENG_WORD_SEP, preserving empty cells."""
    return [t.strip() for t in line.split(ENG_WORD_SEP)]


_ANNOT_DROP_RE = re.compile(
    r"\[(" + "|".join(re.escape(t) for t in ANNOTATION_BRACKET_DROP) + r")\]\s*"
)


def synth_gloss(inter_tokens: list[str]) -> str:
    """Synthesize flowing gloss from interlinear tokens.

    Strips [bracketed-explanatory] markers to bare words and joins with space.
    Used only when an editorial cola partial-overlaps a v1 cola; v1 gloss
    cannot be cleanly mapped at sub-cola granularity.

    Two-step bracket handling matches the smooth-gloss naturalizer in
    parse_teamim: (1) drop pure-annotation brackets like `[obj.]` entirely,
    (2) iterate-unbracket the rest until convergence (handles nested cases
    like `[is [the] one]` that single-pass `re.sub` leaves as `is [the one]`).
    """
    out: list[str] = []
    for tok in inter_tokens:
        cleaned = _ANNOT_DROP_RE.sub("", tok)
        prev = None
        while cleaned != prev:
            prev = cleaned
            cleaned = re.sub(r"\[([^\]]*)\]", r"\1", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if cleaned:
            out.append(cleaned)
    return " ".join(out)


def write_chapter(verses: list[tuple[str, list[str]]], outpath: Path) -> None:
    outpath.parent.mkdir(parents=True, exist_ok=True)
    parts: list[str] = []
    for vref, lines in verses:
        parts.append(vref)
        parts.extend(lines)
        parts.append("")
    text = "\n".join(parts).rstrip() + "\n"
    outpath.write_text(text, encoding="utf-8")


def propagate_chapter(book: str, chapter_filename: str, dry_run: bool) -> tuple[bool, dict]:
    """Process one chapter; write per-word layer files unless dry_run."""
    ed_he_path = ED_HE_DIR / book / chapter_filename
    if not ed_he_path.exists():
        return False, {}

    v1_he       = parse_chapter(V1_HE_DIR       / book / chapter_filename)
    v1_inter    = parse_chapter(V1_INTER_DIR    / book / chapter_filename)
    v1_gloss    = parse_chapter(V1_GLOSS_DIR    / book / chapter_filename)
    v1_translit = parse_chapter(V1_TRANSLIT_DIR / book / chapter_filename)
    ed_he       = parse_chapter(ed_he_path)

    v1_he_d       = dict(v1_he)
    v1_inter_d    = dict(v1_inter)
    v1_gloss_d    = dict(v1_gloss)
    v1_translit_d = dict(v1_translit)

    out_inter:    list[tuple[str, list[str]]] = []
    out_gloss:    list[tuple[str, list[str]]] = []
    out_translit: list[tuple[str, list[str]]] = []

    stats = {"verses": 0, "ed_cola": 0, "clean_merge_cola": 0, "split_cola": 0}

    for vref, ed_he_lines in ed_he:
        if vref not in v1_he_d:
            sys.exit(f"ERROR {chapter_filename} {vref}: verse missing in v1 he-baseline")

        v1_he_lines       = v1_he_d[vref]
        v1_inter_lines    = v1_inter_d.get(vref, [])
        v1_gloss_lines    = v1_gloss_d.get(vref, [])
        v1_translit_lines = v1_translit_d.get(vref, [])

        v1_word_stream:   list[tuple[int, int, str]] = []
        v1_line_lengths:  list[int] = []
        for li, line in enumerate(v1_he_lines):
            words = he_orth_words(line)
            v1_line_lengths.append(len(words))
            for wi, w in enumerate(words):
                v1_word_stream.append((li, wi, w))

        ed_word_stream:  list[str] = []
        ed_line_lengths: list[int] = []
        for line in ed_he_lines:
            words = he_orth_words(line)
            ed_line_lengths.append(len(words))
            ed_word_stream.extend(words)

        if len(v1_word_stream) != len(ed_word_stream):
            sys.exit(
                f"ERROR {chapter_filename} {vref}: word count mismatch "
                f"(v1={len(v1_word_stream)}, editorial={len(ed_word_stream)})"
            )
        for i, (v1tup, ew) in enumerate(zip(v1_word_stream, ed_word_stream)):
            if v1tup[2] != ew:
                sys.exit(
                    f"ERROR {chapter_filename} {vref}: word #{i} differs "
                    f"(v1={v1tup[2]!r}, editorial={ew!r})"
                )

        v1_inter_stream:    list[str] = []
        v1_translit_stream: list[str] = []
        for line in v1_inter_lines:
            v1_inter_stream.extend(per_word_tokens(line))
        for line in v1_translit_lines:
            v1_translit_stream.extend(per_word_tokens(line))

        n_he = len(v1_word_stream)
        if len(v1_inter_stream) != n_he:
            # Alignment-warning verse: parse_teamim skipped interlinear for this
            # verse due to TAHOT formatting quirks. Pad with "???" placeholders
            # so propagation can continue for the remaining chapters.
            print(
                f"  WARN {chapter_filename} {vref}: interlinear skipped by parser "
                f"({len(v1_inter_stream)} tokens vs {n_he} Hebrew words) — "
                f"padding with placeholders",
                file=sys.stderr,
            )
            v1_inter_stream = ["???"] * n_he
        if len(v1_translit_stream) != n_he:
            # Same alignment-warning case for translit.
            print(
                f"  WARN {chapter_filename} {vref}: translit skipped by parser "
                f"({len(v1_translit_stream)} tokens vs {n_he} Hebrew words) — "
                f"padding with placeholders",
                file=sys.stderr,
            )
            v1_translit_stream = ["???"] * n_he

        cursor = 0
        ed_inter_lines:    list[str] = []
        ed_translit_lines: list[str] = []
        ed_gloss_lines:    list[str] = []

        for n in ed_line_lengths:
            inter_slice    = v1_inter_stream   [cursor : cursor + n]
            translit_slice = v1_translit_stream[cursor : cursor + n]

            ed_inter_lines.append(   ENG_WORD_SEP.join(inter_slice))
            ed_translit_lines.append(ENG_WORD_SEP.join(translit_slice))

            first_v1_li, first_v1_wi, _ = v1_word_stream[cursor]
            last_v1_li,  last_v1_wi,  _ = v1_word_stream[cursor + n - 1]
            last_v1_li_total = v1_line_lengths[last_v1_li]

            spans_complete = (
                first_v1_wi == 0 and last_v1_wi == last_v1_li_total - 1
            )
            if spans_complete:
                gloss_text = " ".join(v1_gloss_lines[first_v1_li : last_v1_li + 1])
                stats["clean_merge_cola"] += 1
            else:
                gloss_text = synth_gloss(inter_slice)
                stats["split_cola"] += 1

            # Defense-in-depth: collapse artifact doublings created by
            # cross-cola joins or stale v1 files (Design D 2026-04-30).
            gloss_text = deduplicate_gloss(gloss_text)
            ed_gloss_lines.append(gloss_text)
            cursor += n
            stats["ed_cola"] += 1

        out_inter.append(   (vref, ed_inter_lines))
        out_gloss.append(   (vref, ed_gloss_lines))
        out_translit.append((vref, ed_translit_lines))
        stats["verses"] += 1

    if not dry_run:
        write_chapter(out_inter,    ED_INTER_DIR    / book / chapter_filename)
        # Wave 6 (2026-05-12): v2/eng-gloss is now KJV verbatim, produced by
        # scripts/regenerate_english.py (atu_method.kjv_alignment). Writing
        # the v1-derived legacy gloss here would silently overwrite the KJV
        # substrate with stale Macula-era English. The propagation loop above
        # still computes ed_gloss_lines as a no-op safety (preserves the
        # word-stream invariant check); the WRITE is suppressed.
        # write_chapter(out_gloss, ED_GLOSS_DIR / book / chapter_filename)
        write_chapter(out_translit, ED_TRANSLIT_DIR / book / chapter_filename)

    return True, stats


def process_book(book: str, dry_run: bool) -> dict:
    """Process all chapters in a single book. Return aggregate stats."""
    book_dir = ED_HE_DIR / book
    if not book_dir.exists():
        return None  # Signal: book not found

    chapter_files = sorted(book_dir.glob("*.txt"))
    if not chapter_files:
        return {}  # Empty book

    book_stats = {"verses": 0, "ed_cola": 0, "clean_merge_cola": 0, "split_cola": 0}
    for cf in chapter_files:
        had, stats = propagate_chapter(book, cf.name, dry_run)
        if not had:
            continue
        for k in book_stats:
            book_stats[k] += stats.get(k, 0)
        print(
            f"    {cf.stem}: {stats['verses']} verses, "
            f"{stats['ed_cola']} cola "
            f"({stats['clean_merge_cola']} clean / {stats['split_cola']} split)"
        )

    return book_stats


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    book_group = ap.add_mutually_exclusive_group(required=True)
    book_group.add_argument("--book", help="Book folder, e.g. '32-jonah'")
    book_group.add_argument("--all-books", action="store_true", help="Process all books in v2/heb/")
    ap.add_argument("--dry-run", action="store_true", help="Do not write files")
    args = ap.parse_args()

    books_to_process: list[str] = []

    if args.all_books:
        # Discover all book directories in ED_HE_DIR
        if not ED_HE_DIR.exists():
            print(f"INFO: editorial Hebrew root not found: {ED_HE_DIR}")
            print("No books to process.")
            return
        book_dirs = sorted([d.name for d in ED_HE_DIR.iterdir() if d.is_dir()])
        if not book_dirs:
            print(f"INFO: no book directories found in {ED_HE_DIR}")
            return
        books_to_process = book_dirs
        print(f"propagate_editorial_layers.py — --all-books")
        print(f"Mode: {'dry-run' if args.dry_run else 'apply'}")
        print(f"Books to process: {', '.join(books_to_process)}\n")
    else:
        books_to_process = [args.book]
        print(f"propagate_editorial_layers.py — book: {args.book}")
        print(f"Mode: {'dry-run' if args.dry_run else 'apply'}\n")

    total = {"verses": 0, "ed_cola": 0, "clean_merge_cola": 0, "split_cola": 0}
    books_processed = 0
    books_not_found = []

    for book in books_to_process:
        book_stats = process_book(book, args.dry_run)

        if book_stats is None:
            # Book directory doesn't exist
            if args.all_books:
                print(f"  {book}: skipped (no v2/heb directory)")
                books_not_found.append(book)
            else:
                # Single-book mode with missing directory
                print(f"INFO: editorial Hebrew folder not found: {ED_HE_DIR / book}")
                print("No chapters to process.")
                return
            continue

        if not book_stats:
            # Book directory exists but no chapter files
            print(f"  {book}: no .txt files")
            continue

        books_processed += 1
        for k in total:
            total[k] += book_stats.get(k, 0)
        print(f"  {book}: {book_stats['verses']} verses, {book_stats['ed_cola']} cola\n")

    print("=" * 60)
    print(f"Books processed: {books_processed}")
    if args.all_books and books_not_found:
        print(f"Books skipped (missing): {', '.join(books_not_found)}")
    print(f"Total: {total['verses']} verses, {total['ed_cola']} editorial cola")
    print(f"  Clean (full v1-line spans):   {total['clean_merge_cola']}")
    print(f"  Split (synth gloss fallback): {total['split_cola']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
