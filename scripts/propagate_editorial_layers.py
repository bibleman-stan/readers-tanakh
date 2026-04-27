#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
propagate_editorial_layers.py — re-segment v1 per-word layers to the editorial
Hebrew cola structure.

When the editorial Hebrew layer (currently data/text-files/v4/editorial/)
changes cola structure relative to the v1 he-baseline, the per-word layers
(eng-interlinear, translit, eng-gloss) must follow. v1 has 1:1 alignment
between Hebrew orthographic words and per-word tokens; this script slices
those per-word streams by editorial cola word counts and emits new per-word
files keyed to the editorial cola boundaries.

Per-layer behaviour:
  eng-interlinear, translit  — re-segmented mechanically (perfect 1:1).
  eng-gloss                  — flowing English; two cases:
    (a) editorial cola spans one or more *complete* v1 cola
        → space-join the v1 gloss lines (preserves prior gloss quality).
    (b) editorial cola partial-overlaps a v1 cola (split case)
        → fallback: synthesize gloss from interlinear with bracket cleanup.

Word-stream invariant:
  v1 Hebrew word stream MUST equal editorial Hebrew word stream (same words,
  same order, same count). Editorial work only changes line breaks; never
  adds/removes/reorders words. Script exits with error on violation.

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/propagate_editorial_layers.py --book 05-jonah
    PYTHONIOENCODING=utf-8 py -3 scripts/propagate_editorial_layers.py --book 05-jonah --dry-run
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEXT_DIR = REPO_ROOT / "data" / "text-files"

V1_HE_DIR        = TEXT_DIR / "v1" / "he-baseline"
V1_INTER_DIR     = TEXT_DIR / "v1" / "eng-interlinear"
V1_GLOSS_DIR     = TEXT_DIR / "v1" / "eng-gloss"
V1_TRANSLIT_DIR  = TEXT_DIR / "v1" / "translit"

ED_HE_DIR        = TEXT_DIR / "v4" / "editorial"
ED_INTER_DIR     = TEXT_DIR / "v4" / "eng-interlinear"
ED_GLOSS_DIR     = TEXT_DIR / "v4" / "eng-gloss"
ED_TRANSLIT_DIR  = TEXT_DIR / "v4" / "translit"

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


def synth_gloss(inter_tokens: list[str]) -> str:
    """Synthesize flowing gloss from interlinear tokens.

    Strips [bracketed-explanatory] markers to bare words and joins with space.
    Used only when an editorial cola partial-overlaps a v1 cola; v1 gloss
    cannot be cleanly mapped at sub-cola granularity.
    """
    out: list[str] = []
    for tok in inter_tokens:
        cleaned = re.sub(r"\[([^\]]*)\]", r"\1", tok)
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

        if len(v1_inter_stream) != len(v1_word_stream):
            sys.exit(
                f"ERROR {chapter_filename} {vref}: v1 interlinear word count "
                f"({len(v1_inter_stream)}) != Hebrew ({len(v1_word_stream)})"
            )
        if len(v1_translit_stream) != len(v1_word_stream):
            sys.exit(
                f"ERROR {chapter_filename} {vref}: v1 translit word count "
                f"({len(v1_translit_stream)}) != Hebrew ({len(v1_word_stream)})"
            )

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

            ed_gloss_lines.append(gloss_text)
            cursor += n
            stats["ed_cola"] += 1

        out_inter.append(   (vref, ed_inter_lines))
        out_gloss.append(   (vref, ed_gloss_lines))
        out_translit.append((vref, ed_translit_lines))
        stats["verses"] += 1

    if not dry_run:
        write_chapter(out_inter,    ED_INTER_DIR    / book / chapter_filename)
        write_chapter(out_gloss,    ED_GLOSS_DIR    / book / chapter_filename)
        write_chapter(out_translit, ED_TRANSLIT_DIR / book / chapter_filename)

    return True, stats


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--book", required=True, help="Book folder, e.g. '05-jonah'")
    ap.add_argument("--dry-run", action="store_true", help="Do not write files")
    args = ap.parse_args()

    book_dir = ED_HE_DIR / args.book
    if not book_dir.exists():
        sys.exit(f"ERROR: editorial Hebrew folder not found: {book_dir}")

    chapter_files = sorted(book_dir.glob("*.txt"))
    if not chapter_files:
        sys.exit(f"ERROR: no .txt files under {book_dir}")

    print(f"propagate_editorial_layers.py — book: {args.book}")
    print(f"Mode: {'dry-run' if args.dry_run else 'apply'}")
    print(f"Chapters with editorial Hebrew: {len(chapter_files)}\n")

    total = {"verses": 0, "ed_cola": 0, "clean_merge_cola": 0, "split_cola": 0}
    for cf in chapter_files:
        had, stats = propagate_chapter(args.book, cf.name, args.dry_run)
        if not had:
            continue
        for k in total:
            total[k] += stats.get(k, 0)
        print(
            f"  {cf.stem}: {stats['verses']} verses, "
            f"{stats['ed_cola']} cola "
            f"({stats['clean_merge_cola']} clean / {stats['split_cola']} split)"
        )

    print()
    print("=" * 60)
    print(f"Total: {total['verses']} verses, {total['ed_cola']} editorial cola")
    print(f"  Clean (full v1-line spans):   {total['clean_merge_cola']}")
    print(f"  Split (synth gloss fallback): {total['split_cola']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
