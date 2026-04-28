#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply STRONG-MERGE findings from the spec-runner to mutate v2/he.

This is the mechanical surface that closes the rule-implementation loop:
specs (YAML) → findings → merge cascade → updated v2/he.

Cascade behavior: applies all STRONG-MERGE findings in the current pass,
re-runs spec-runner against the mutated state, and repeats until no new
STRONG-MERGE findings fire (convergence).

Usage:
  py -3 scripts/apply_specs.py --book genesis
  py -3 scripts/apply_specs.py --book genesis --dry-run
  py -3 scripts/apply_specs.py --all-books

PYTHONIOENCODING=utf-8 mandatory on Windows.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from validators._shared.spec_runner import SpecRunner, Finding  # noqa: E402
from validators._shared import morphology as M  # noqa: E402


def merge_lines(text: str, findings: list[Finding]) -> tuple[str, int]:
    """Apply STRONG-MERGE findings to chapter text. Returns (new_text, n_merges).

    Each finding identifies a within-verse line pair (prior_line, next_line) to
    merge into one line. Re-build the chapter text by walking line-by-line and
    joining at the marked boundaries.
    """
    # Collect per-(chapter, verse, prior_line_text, next_line_text) merge directives
    merge_set: set[tuple[int, int, str, str]] = set()
    for f in findings:
        if f.severity != "STRONG-MERGE-CANDIDATE":
            continue
        merge_set.add((f.chapter, f.verse, f.prior_line, f.next_line))

    if not merge_set:
        return text, 0

    out_lines: list[str] = []
    cur_ref = None
    n_merges = 0
    raw_lines = text.splitlines()
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        stripped = line.strip()
        if not stripped:
            out_lines.append(line)
            i += 1
            continue
        if M.VERSE_REF_RE.match(stripped):
            ch_s, vs_s = stripped.split(":")
            cur_ref = (int(ch_s), int(vs_s))
            out_lines.append(line)
            i += 1
            continue
        # peek next non-blank line
        j = i + 1
        while j < len(raw_lines) and not raw_lines[j].strip():
            j += 1
        if j >= len(raw_lines):
            out_lines.append(line)
            i += 1
            continue
        next_line = raw_lines[j]
        next_stripped = next_line.strip()
        if M.VERSE_REF_RE.match(next_stripped):
            # next is a verse boundary; don't merge across
            out_lines.append(line)
            i += 1
            continue
        if cur_ref is None:
            out_lines.append(line)
            i += 1
            continue
        key = (cur_ref[0], cur_ref[1], stripped, next_stripped)
        if key in merge_set:
            merged = stripped + " " + next_stripped
            out_lines.append(merged)
            n_merges += 1
            i = j + 1
        else:
            out_lines.append(line)
            i += 1

    return "\n".join(out_lines) + ("\n" if text.endswith("\n") else ""), n_merges


def apply_to_book(corpus_dir: Path, runner: SpecRunner, book_dir_name: str,
                  dry_run: bool, verbose: bool) -> tuple[int, int]:
    """Apply spec-driven STRONG merges to a single book until convergence.
    Returns (total_merges, n_passes)."""
    book_dir = corpus_dir / book_dir_name
    if not book_dir.is_dir():
        print(f"[skip] {book_dir_name}: not a directory", file=sys.stderr)
        return (0, 0)

    total_merges = 0
    passes = 0
    while True:
        passes += 1
        findings = runner.run_corpus(corpus_dir, book_filter=book_dir_name,
                                      severity_filter="STRONG-MERGE-CANDIDATE")
        if not findings:
            break
        # group by chapter file
        by_file: dict[Path, list[Finding]] = defaultdict(list)
        for f in findings:
            by_file[Path(f.file)].append(f)

        pass_merges = 0
        for ch_file, ch_findings in by_file.items():
            full_path = ROOT / ch_file
            text = full_path.read_text(encoding="utf-8")
            new_text, n = merge_lines(text, ch_findings)
            if n > 0:
                if not dry_run:
                    full_path.write_text(new_text, encoding="utf-8")
                pass_merges += n
                if verbose:
                    print(f"  pass {passes} {ch_file}: {n} merges", file=sys.stderr)

        total_merges += pass_merges
        if pass_merges == 0:
            break

    return (total_merges, passes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", help="single book (substring match)")
    ap.add_argument("--all-books", action="store_true", help="apply to all books")
    ap.add_argument("--corpus", default="data/text-files/v2/he")
    ap.add_argument("--specs", default="validators/specs")
    ap.add_argument("--dry-run", action="store_true", help="report only, do not write")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if not args.book and not args.all_books:
        ap.error("specify --book NAME or --all-books")

    runner = SpecRunner(args.specs)
    corpus_dir = ROOT / args.corpus

    if args.all_books:
        targets = [d.name for d in sorted(corpus_dir.iterdir()) if d.is_dir()]
    else:
        targets = [args.book]

    grand_total = 0
    for target in targets:
        # support substring match for single-book
        if args.book:
            matched = [d.name for d in corpus_dir.iterdir() if args.book in d.name]
            if not matched:
                print(f"[error] no book matching '{args.book}'", file=sys.stderr)
                return 2
            target = matched[0]
        n_merges, passes = apply_to_book(corpus_dir, runner, target,
                                          args.dry_run, args.verbose)
        grand_total += n_merges
        action = "would merge" if args.dry_run else "merged"
        print(f"{target}: {action} {n_merges} line pairs across {passes} passes")
        if args.book:
            break  # single-book mode

    print(f"\nGrand total: {grand_total} merges {'(dry-run)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
