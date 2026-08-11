#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply STRONG-MERGE findings from the spec-runner to mutate v2/heb.

This is the mechanical surface that closes the rule-implementation loop:
specs (YAML) → findings → merge cascade → updated v2/heb.

Cascade behavior: applies all STRONG-MERGE findings in the current pass,
re-runs spec-runner against the mutated state, and repeats until no new
STRONG-MERGE findings fire (convergence).

Usage:
  py -3 5-machinery/scripts/apply_specs.py --book genesis
  py -3 5-machinery/scripts/apply_specs.py --book genesis --dry-run
  py -3 5-machinery/scripts/apply_specs.py --all-books

PYTHONIOENCODING=utf-8 mandatory on Windows.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

def _find_repo_root():
    """Repo root by MARKER, not by counting parents.

    Counting encodes this file's depth in the tree, so moving the file silently
    breaks it and no text-based check notices. Anchoring on .git survives any
    move. Added 2026-08-10 after a reorg broke three different counted idioms.
    """
    from pathlib import Path as _P
    _here = _P(__file__).resolve()
    for _p in _here.parents:
        if (_p / ".git").exists():
            return _p
    return _here.parent


ROOT = _find_repo_root()
MAX_PASSES = 25
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


def split_lines(text: str, findings: list[Finding]) -> tuple[str, int]:
    """Apply STRONG-SPLIT findings to chapter text. Returns (new_text, n_splits).

    Each finding identifies a single line + token positions where new line breaks
    should be inserted, splitting one line into N pieces. Splits operate on
    matching (chapter, verse, line_text) keys.
    """
    split_directives: dict[tuple[int, int, str], list[int]] = {}
    for f in findings:
        if f.severity != "STRONG-SPLIT-CANDIDATE":
            continue
        if not f.split_positions:
            continue
        key = (f.chapter, f.verse, f.prior_line)
        # If multiple specs request splits on the same line, union their positions
        existing = split_directives.get(key, [])
        merged_positions = sorted(set(existing) | set(f.split_positions))
        split_directives[key] = merged_positions

    if not split_directives:
        return text, 0

    out_lines: list[str] = []
    cur_ref = None
    n_splits = 0
    raw_lines = text.splitlines()
    for raw in raw_lines:
        stripped = raw.strip()
        if not stripped:
            out_lines.append(raw)
            continue
        if M.VERSE_REF_RE.match(stripped):
            ch_s, vs_s = stripped.split(":")
            cur_ref = (int(ch_s), int(vs_s))
            out_lines.append(raw)
            continue
        if cur_ref is None:
            out_lines.append(raw)
            continue
        key = (cur_ref[0], cur_ref[1], stripped)
        if key in split_directives:
            positions = split_directives[key]
            toks = stripped.split()
            # Build N new lines by carving at split positions
            chunks: list[list[str]] = []
            start = 0
            for pos in positions:
                if pos <= start or pos >= len(toks):
                    continue
                chunks.append(toks[start:pos])
                start = pos
            chunks.append(toks[start:])
            for chunk in chunks:
                if chunk:
                    out_lines.append(" ".join(chunk))
            n_splits += len(chunks) - 1  # N chunks = N-1 splits
        else:
            out_lines.append(raw)

    return "\n".join(out_lines) + ("\n" if text.endswith("\n") else ""), n_splits


def apply_to_book(corpus_dir: Path, runner: SpecRunner, book_dir_name: str,
                  dry_run: bool, verbose: bool,
                  ) -> tuple[int, int, dict[tuple[str, int, int], list[tuple[int, str]]]]:
    """Apply spec-driven SPLITS then MERGES to a single book until convergence.

    Per-pass ordering invariant: SPLITS run first within each pass, then MERGES.
    Reasoning: a merge that fires on a cumulatively-merged line cements the
    wrong grouping. Splits decompose first; merges then legitimately re-bond
    bonded pairs / clause-nucleus components on the now-correctly-decomposed lines.

    Returns (total_changes, n_passes, per_verse_touch_count).
    per_verse_touch_count: (book, chapter, verse) → [(pass_num, spec_name), ...]
    """
    book_dir = corpus_dir / book_dir_name
    if not book_dir.is_dir():
        print(f"[skip] {book_dir_name}: not a directory", file=sys.stderr)
        return (0, 0, {})

    # Safety net 1: per-verse mutation history
    per_verse_touch_count: dict[tuple[str, int, int], list[tuple[int, str]]] = defaultdict(list)

    total_changes = 0
    passes = 0
    while True:
        passes += 1

        # Safety net 1: hard cap
        if passes > MAX_PASSES:
            hot = [(k, v) for k, v in per_verse_touch_count.items() if len(v) > 5]
            hot.sort(key=lambda x: -len(x[1]))
            # Surface the RUNAWAY to BOTH stdout and stderr with a prominent
            # banner so dispatchers / cluster agents / log-tailers cannot
            # accidentally miss it. Per H5 carry-forward (handoffs/14):
            # silent-bail on RUNAWAY exit code 2 was the failure mode.
            banner = "=" * 70
            for stream in (sys.stdout, sys.stderr):
                print(banner, file=stream)
                print(f"[RUNAWAY] {book_dir_name}: real oscillation — exceeded MAX_PASSES={MAX_PASSES}",
                      file=stream)
                print(f"  (files were written each pass; these are genuine oscillators, not dry-run artifacts)",
                      file=stream)
                for (book, ch, vs), touches in hot[:10]:
                    last5 = touches[-5:]
                    print(f"  {book} {ch}:{vs} touched {len(touches)}x — last 5: {last5}", file=stream)
                print(banner, file=stream)
            sys.exit(2)

        # ── PHASE A: SPLITS ─────────────────────────────────────────────
        split_findings = runner.run_corpus(corpus_dir, book_filter=book_dir_name,
                                            severity_filter="STRONG-SPLIT-CANDIDATE")
        pass_splits = 0
        if split_findings:
            by_file: dict[Path, list[Finding]] = defaultdict(list)
            for f in split_findings:
                by_file[Path(f.file)].append(f)
                spec_name = getattr(f, "spec_name", getattr(f, "rule", "unknown"))
                per_verse_touch_count[(book_dir_name, f.chapter, f.verse)].append((passes, spec_name))
            for ch_file, ch_findings in by_file.items():
                full_path = ROOT / ch_file
                text = full_path.read_text(encoding="utf-8")
                new_text, n = split_lines(text, ch_findings)
                if n > 0:
                    if not dry_run:
                        full_path.write_text(new_text, encoding="utf-8")
                    pass_splits += n
                    if verbose:
                        print(f"  pass {passes} SPLIT {ch_file}: {n}", file=sys.stderr)

        # ── PHASE B: MERGES ─────────────────────────────────────────────
        merge_findings = runner.run_corpus(corpus_dir, book_filter=book_dir_name,
                                            severity_filter="STRONG-MERGE-CANDIDATE")
        pass_merges = 0
        if merge_findings:
            by_file: dict[Path, list[Finding]] = defaultdict(list)
            for f in merge_findings:
                by_file[Path(f.file)].append(f)
                spec_name = getattr(f, "spec_name", getattr(f, "rule", "unknown"))
                per_verse_touch_count[(book_dir_name, f.chapter, f.verse)].append((passes, spec_name))
            for ch_file, ch_findings in by_file.items():
                full_path = ROOT / ch_file
                text = full_path.read_text(encoding="utf-8")
                new_text, n = merge_lines(text, ch_findings)
                if n > 0:
                    if not dry_run:
                        full_path.write_text(new_text, encoding="utf-8")
                    pass_merges += n
                    if verbose:
                        print(f"  pass {passes} MERGE {ch_file}: {n}", file=sys.stderr)

        pass_total = pass_splits + pass_merges
        total_changes += pass_total
        if pass_total == 0:
            break

        # Dry-run: one pass only.  Cascade convergence requires real writes;
        # without them pass 2 reads the same file as pass 1 and loops forever,
        # triggering a phantom RUNAWAY.  Print a note and exit the loop.
        if dry_run:
            print(
                "[dry-run] pass-1-only: showing what ONE pass would do. "
                "Cannot detect cascade convergence — re-run without --dry-run for full cascade.",
                file=sys.stderr,
            )
            break

    # Safety net 2: post-convergence idempotency assertion.
    # Meaningless in dry-run (files were not written), so skip it.
    if not dry_run:
        leftover_m = runner.run_corpus(corpus_dir, book_filter=book_dir_name,
                                        severity_filter="STRONG-MERGE-CANDIDATE")
        leftover_s = runner.run_corpus(corpus_dir, book_filter=book_dir_name,
                                        severity_filter="STRONG-SPLIT-CANDIDATE")
        leftover = leftover_m + leftover_s
        if leftover:
            print("NON-IDEMPOTENT CONVERGENCE: cascade reported clean but spec re-emits findings",
                  file=sys.stderr)
            for f in leftover[:5]:
                print(f"  file={f.file} line={getattr(f,'line','-')} rule={getattr(f,'rule','-')} "
                      f"prior_line={getattr(f,'prior_line','-')!r}", file=sys.stderr)
            sys.exit(3)

    return (total_changes, passes, dict(per_verse_touch_count))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", help="single book (substring match)")
    ap.add_argument("--all-books", action="store_true", help="apply to all books")
    ap.add_argument("--corpus", default="data/text-files/v2/heb")
    ap.add_argument("--specs", default="5-machinery/validators/specs")
    ap.add_argument("--dry-run", action="store_true", help="report only, do not write")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if not args.book and not args.all_books:
        ap.error("specify --book NAME or --all-books")

    if args.dry_run:
        print("[dry-run] single-pass preview only — cascade convergence requires real writes.",
              file=sys.stderr)

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
        n_changes, passes, touch_map = apply_to_book(corpus_dir, runner, target,
                                                      args.dry_run, args.verbose)
        grand_total += n_changes
        action = "would change" if args.dry_run else "changed"
        max_touches = max((len(v) for v in touch_map.values()), default=0)
        if max_touches:
            hottest = max(touch_map, key=lambda k: len(touch_map[k]))
            _, hch, hvs = hottest
            touch_summary = f"; max verse touches: {max_touches} ({hch}:{hvs})"
        else:
            touch_summary = ""
        print(f"{target}: {action} {n_changes} lines across {passes} passes{touch_summary}")
        if args.book:
            break  # single-book mode

    print(f"\nGrand total: {grand_total} changes {'(dry-run)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
