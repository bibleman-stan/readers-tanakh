#!/usr/bin/env python3
"""Diagnostic: simulate cascade passes on a single verse, report all spec fires per pass.

Usage:
  PYTHONIOENCODING=utf-8 py -3 scripts/trace_verse_cascade.py <book_dir_name> <chapter> <verse> [<max_passes>]

Example:
  py -3 scripts/trace_verse_cascade.py 01-genesis 24 40 5
"""
from __future__ import annotations
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from validators._shared.spec_runner import SpecRunner  # noqa: E402
from validators._shared import morphology as M  # noqa: E402
from scripts.apply_specs import merge_lines, split_lines  # noqa: E402


def extract_verse(corpus_book_dir: Path, chapter: int, verse: int) -> str:
    """Extract a single verse from the v2/heb corpus into a single-verse chapter file."""
    chapter_str = f"{chapter:02d}"
    book_name = corpus_book_dir.name
    suffix = book_name.split("-", 1)[1] if "-" in book_name else book_name
    ch_file = corpus_book_dir / f"{suffix}-{chapter_str}.txt"
    text = ch_file.read_text(encoding="utf-8")
    lines = text.splitlines()
    out = []
    in_target = False
    for line in lines:
        s = line.strip()
        if not s:
            if in_target:
                break
            continue
        if M.VERSE_REF_RE.match(s):
            ch_s, vs_s = s.split(":")
            cur = (int(ch_s), int(vs_s))
            if cur == (chapter, verse):
                in_target = True
                out.append(line)
            elif in_target:
                break
        elif in_target:
            out.append(line)
    return "\n".join(out) + "\n"


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 1
    book_dir_name = sys.argv[1]
    chapter = int(sys.argv[2])
    verse = int(sys.argv[3])
    max_passes = int(sys.argv[4]) if len(sys.argv) >= 5 else 5

    corpus_book_dir = ROOT / "data/text-files/v2/heb" / book_dir_name
    verse_text = extract_verse(corpus_book_dir, chapter, verse)
    print(f"=== Initial state of {book_dir_name} {chapter}:{verse} ===")
    print(verse_text)

    runner = SpecRunner(ROOT / "validators/specs")

    with tempfile.TemporaryDirectory(dir=str(ROOT)) as tmpdir:
        sandbox_corpus = Path(tmpdir) / "corpus"
        sandbox_book = sandbox_corpus / book_dir_name
        sandbox_book.mkdir(parents=True)
        suffix = book_dir_name.split("-", 1)[1] if "-" in book_dir_name else book_dir_name
        sandbox_file = sandbox_book / f"{suffix}-{chapter:02d}.txt"
        sandbox_file.write_text(verse_text, encoding="utf-8")

        for p in range(1, max_passes + 1):
            print(f"\n=== Pass {p} ===")
            split_findings = runner.run_corpus(sandbox_corpus, book_filter=book_dir_name,
                                                severity_filter="STRONG-SPLIT-CANDIDATE")
            split_findings = [f for f in split_findings if f.chapter == chapter and f.verse == verse]
            if split_findings:
                print(f"-- SPLIT findings ({len(split_findings)}):")
                for f in split_findings:
                    print(f"   {f.rule}/{f.subcase}  prior: {f.prior_line!r}")
                    print(f"      split_positions: {f.split_positions}")
            text = sandbox_file.read_text(encoding="utf-8")
            new_text, n_split = split_lines(text, split_findings)
            if n_split:
                sandbox_file.write_text(new_text, encoding="utf-8")
                print(f"   → applied {n_split} splits")

            merge_findings = runner.run_corpus(sandbox_corpus, book_filter=book_dir_name,
                                                severity_filter="STRONG-MERGE-CANDIDATE")
            merge_findings = [f for f in merge_findings if f.chapter == chapter and f.verse == verse]
            if merge_findings:
                print(f"-- MERGE findings ({len(merge_findings)}):")
                for f in merge_findings:
                    print(f"   {f.rule}/{f.subcase}  prior: {f.prior_line!r}")
                    print(f"      next:  {f.next_line!r}")
            text = sandbox_file.read_text(encoding="utf-8")
            new_text, n_merge = merge_lines(text, merge_findings)
            if n_merge:
                sandbox_file.write_text(new_text, encoding="utf-8")
                print(f"   → applied {n_merge} merges")

            current = sandbox_file.read_text(encoding="utf-8")
            print(f"-- State after pass {p}:")
            for ln in current.splitlines():
                print(f"   {ln}")

            if n_split + n_merge == 0:
                print(f"\n=== Converged after {p} passes ===")
                return 0

        print(f"\n=== Did not converge in {max_passes} passes ===")
        return 1


if __name__ == "__main__":
    sys.exit(main())
