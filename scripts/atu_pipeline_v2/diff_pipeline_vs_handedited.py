#!/usr/bin/env python3
"""
diff_pipeline_vs_handedited.py — diff pipeline draft against v2/heb hand-edits.

For each chapter:
  - Parse v2/heb/{book}/{stem}.txt (hand-edited) and v2-pipeline-draft/heb/{book}/{stem}.txt
    (pipeline) into {verse: [atu_text, ...]}
  - Count ATUs per verse in each
  - Surface verses where counts differ as "needs-review"
  - Aggregate per-book and corpus-wide stats

Writes:
  data/text-files/v2-pipeline-draft/_diff_report.md     (per-book summary)
  data/text-files/v2-pipeline-draft/_diff_per_chapter.jsonl  (per-chapter detail)

Usage: py -3 scripts/atu_pipeline_v2/diff_pipeline_vs_handedited.py
"""

from __future__ import annotations
import json
import re
import sys
from pathlib import Path

REPO = Path(r"C:\Users\bibleman\repos\readers-tanakh")
HANDEDITED_DIR = REPO / "data/text-files/v2/heb"
PIPELINE_DIR = REPO / "data/text-files/v2-pipeline-draft/heb"
OUT_DIR = REPO / "data/text-files/v2-pipeline-draft"

VERSE_HEADER_RE = re.compile(r"^(\d+):(\d+)\s*$")


def parse_v2_heb_file(path: Path) -> dict[int, list[str]]:
    """Return {verse_num: [atu_text, ...]} from a v2/heb-format file."""
    if not path.exists():
        return {}
    verses: dict[int, list[str]] = {}
    current_verse: int | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        m = VERSE_HEADER_RE.match(line)
        if m:
            current_verse = int(m.group(2))
            verses[current_verse] = []
        elif current_verse is not None:
            verses[current_verse].append(line)
    return verses


def main():
    if not HANDEDITED_DIR.exists():
        print(f"ERROR: hand-edited dir not found: {HANDEDITED_DIR}", file=sys.stderr)
        sys.exit(1)

    book_folders = sorted([d.name for d in PIPELINE_DIR.iterdir() if d.is_dir()])

    per_chapter_records = []
    book_summaries: dict[str, dict] = {}

    for book_folder in book_folders:
        pipeline_book_dir = PIPELINE_DIR / book_folder
        handedited_book_dir = HANDEDITED_DIR / book_folder

        book_total_chapters = 0
        book_chapters_with_match = 0
        book_total_verses = 0
        book_verses_match = 0
        book_handedited_atus = 0
        book_pipeline_atus = 0

        for pipeline_file in sorted(pipeline_book_dir.glob("*.txt")):
            handedited_file = handedited_book_dir / pipeline_file.name
            if not handedited_file.exists():
                continue

            pipeline_verses = parse_v2_heb_file(pipeline_file)
            handedited_verses = parse_v2_heb_file(handedited_file)

            shared_verses = sorted(set(pipeline_verses) & set(handedited_verses))
            if not shared_verses:
                continue

            verse_records = []
            verses_match_count = 0
            for v in shared_verses:
                n_pipe = len(pipeline_verses[v])
                n_hand = len(handedited_verses[v])
                match = n_pipe == n_hand
                if match:
                    verses_match_count += 1
                verse_records.append({
                    "verse": v,
                    "pipeline": n_pipe,
                    "handedited": n_hand,
                    "match": match,
                    "delta": n_pipe - n_hand,
                })

            n_verses = len(shared_verses)
            chapter_n_pipe = sum(len(pipeline_verses[v]) for v in shared_verses)
            chapter_n_hand = sum(len(handedited_verses[v]) for v in shared_verses)
            chapter_all_match = (verses_match_count == n_verses)

            per_chapter_records.append({
                "book_folder": book_folder,
                "chapter": int(pipeline_file.stem.rsplit("-", 1)[1]),
                "stem": pipeline_file.stem,
                "n_verses": n_verses,
                "verses_match": verses_match_count,
                "pct_verses_match": verses_match_count / n_verses if n_verses else 0,
                "pipeline_total_atus": chapter_n_pipe,
                "handedited_total_atus": chapter_n_hand,
                "atu_delta": chapter_n_pipe - chapter_n_hand,
                "all_verses_match": chapter_all_match,
                "verses": verse_records,
            })

            book_total_chapters += 1
            if chapter_all_match:
                book_chapters_with_match += 1
            book_total_verses += n_verses
            book_verses_match += verses_match_count
            book_handedited_atus += chapter_n_hand
            book_pipeline_atus += chapter_n_pipe

        book_summaries[book_folder] = {
            "total_chapters": book_total_chapters,
            "chapters_all_verses_match": book_chapters_with_match,
            "total_verses": book_total_verses,
            "verses_match": book_verses_match,
            "pct_verses_match": book_verses_match / book_total_verses if book_total_verses else 0,
            "pipeline_total_atus": book_pipeline_atus,
            "handedited_total_atus": book_handedited_atus,
            "atu_delta": book_pipeline_atus - book_handedited_atus,
        }

    # Write per-chapter JSONL
    out_jsonl = OUT_DIR / "_diff_per_chapter.jsonl"
    with out_jsonl.open("w", encoding="utf-8") as fp:
        for r in per_chapter_records:
            fp.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Write markdown report
    lines: list[str] = []
    lines.append("# Tanakh pipeline draft vs hand-edited diff report\n")
    lines.append(f"Comparison of pipeline output (`data/text-files/v2-pipeline-draft/heb/`)")
    lines.append(f"against hand-edited renderings (`data/text-files/v2/heb/`).\n")
    lines.append(f"Granularity: per-verse ATU count comparison.\n")

    # Corpus totals
    total_chapters = sum(b["total_chapters"] for b in book_summaries.values())
    total_verses = sum(b["total_verses"] for b in book_summaries.values())
    total_verses_match = sum(b["verses_match"] for b in book_summaries.values())
    total_pipeline_atus = sum(b["pipeline_total_atus"] for b in book_summaries.values())
    total_handedited_atus = sum(b["handedited_total_atus"] for b in book_summaries.values())
    total_chapters_all_match = sum(b["chapters_all_verses_match"] for b in book_summaries.values())

    lines.append("## Corpus-wide\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Chapters compared | {total_chapters} |")
    lines.append(f"| Chapters where ALL verses match count | {total_chapters_all_match} ({total_chapters_all_match/total_chapters:.1%}) |")
    lines.append(f"| Verses compared | {total_verses} |")
    lines.append(f"| Verses with matching ATU count | {total_verses_match} ({total_verses_match/total_verses:.1%}) |")
    lines.append(f"| Pipeline total ATUs | {total_pipeline_atus} |")
    lines.append(f"| Hand-edited total ATUs | {total_handedited_atus} |")
    lines.append(f"| ATU count delta (pipeline − handedited) | {total_pipeline_atus - total_handedited_atus:+d} |\n")

    # Per-book summary
    lines.append("## Per-book summary\n")
    lines.append(f"| Book | Chapters | Verses matching count | % match | Pipeline ATUs | Hand ATUs | Delta |")
    lines.append(f"|---|---|---|---|---|---|---|")
    for book_folder in sorted(book_summaries.keys()):
        b = book_summaries[book_folder]
        if b["total_chapters"] == 0:
            continue
        lines.append(
            f"| {book_folder} | {b['total_chapters']} | "
            f"{b['verses_match']}/{b['total_verses']} | {b['pct_verses_match']:.1%} | "
            f"{b['pipeline_total_atus']} | {b['handedited_total_atus']} | "
            f"{b['atu_delta']:+d} |"
        )

    # Chapters most needing review (largest absolute ATU delta or lowest match %)
    lines.append("\n## Top 25 chapters by ATU delta (largest divergence)\n")
    lines.append(f"| Chapter | Verses | % match | Pipeline | Hand | Delta |")
    lines.append(f"|---|---|---|---|---|---|")
    by_delta = sorted(per_chapter_records, key=lambda r: -abs(r["atu_delta"]))
    for r in by_delta[:25]:
        lines.append(
            f"| {r['stem']} | {r['n_verses']} | {r['pct_verses_match']:.1%} | "
            f"{r['pipeline_total_atus']} | {r['handedited_total_atus']} | {r['atu_delta']:+d} |"
        )

    lines.append("\n## Top 25 chapters by lowest verse-match percentage\n")
    lines.append(f"| Chapter | Verses | % match | Pipeline | Hand | Delta |")
    lines.append(f"|---|---|---|---|---|---|")
    by_match_pct = sorted(per_chapter_records, key=lambda r: r["pct_verses_match"])
    for r in by_match_pct[:25]:
        lines.append(
            f"| {r['stem']} | {r['n_verses']} | {r['pct_verses_match']:.1%} | "
            f"{r['pipeline_total_atus']} | {r['handedited_total_atus']} | {r['atu_delta']:+d} |"
        )

    out_md = OUT_DIR / "_diff_report.md"
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote: {out_md}")
    print(f"Wrote: {out_jsonl}")
    print()
    print(f"--- Corpus headline ---")
    print(f"  Chapters compared: {total_chapters}")
    print(f"  Chapters all-verses-match: {total_chapters_all_match} ({total_chapters_all_match/total_chapters:.1%})")
    print(f"  Verses with matching count: {total_verses_match}/{total_verses} ({total_verses_match/total_verses:.1%})")
    print(f"  Pipeline ATUs: {total_pipeline_atus}")
    print(f"  Hand-edited ATUs: {total_handedited_atus}")
    print(f"  Delta: {total_pipeline_atus - total_handedited_atus:+d}")


if __name__ == "__main__":
    main()
