#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_revert_lines.py — engine-plane revert tool for v2/heb cola merges.

Takes a TSV of (book, chapter, verse, line_a_idx, line_b_idx) revert
targets and merges line_a + line_b in v2/heb back into one cola. Use
when an audit identifies that an earlier apply over-split editorially-
bonded cola (e.g., the M1 intensification doublets caught by the 2026-
05-12 audit).

Replaces the per-instance `C:/tmp/rollback_*.py` patches that were
previously written ad-hoc for each rollback batch. This tool is engine-
plane (lives in 5-machinery/scripts/, persistent, reusable across all future audits).

Input TSV format (tab-separated, header row required):
  book           e.g., 11-1kings
  chapter        integer
  verse          integer
  line_a_idx     0-based line-within-verse for the first line of the
                 pair to merge
  line_b_idx     0-based line-within-verse for the second (must be
                 line_a_idx + 1)
  reason         free-text rationale (for git-history audit trail)

Usage:
  PYTHONIOENCODING=utf-8 py -3 5-machinery/scripts/apply_revert_lines.py --tsv reverts.tsv --dry-run
  PYTHONIOENCODING=utf-8 py -3 5-machinery/scripts/apply_revert_lines.py --tsv reverts.tsv

Post-apply: refresh_book.py per affected book regenerates derived layers.
The pre-commit hook does this automatically on commit.
"""

from __future__ import annotations

import argparse
import csv
import re
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


REPO_ROOT = _find_repo_root()
HE_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "heb"

VERSE_RE = re.compile(r"^(\d+):(\d+)\s*$")


def find_verse_lines(file_lines: list[str], verse: int) -> list[int]:
    """Return file-line indices (0-based) of non-blank non-marker lines
    within the given verse."""
    out = []
    in_verse = False
    for i, ln in enumerate(file_lines):
        m = VERSE_RE.match(ln.strip())
        if m:
            in_verse = (int(m.group(2)) == verse)
            continue
        if in_verse:
            if not ln.strip():
                in_verse = False
                continue
            out.append(i)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tsv", required=True,
                    help="Path to revert-targets TSV (book, chapter, verse, line_a_idx, line_b_idx, reason)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tsv_path = Path(args.tsv)
    if not tsv_path.exists():
        print(f"ERROR: TSV not found: {tsv_path}", file=sys.stderr)
        return 2

    by_file: dict[Path, list[dict]] = defaultdict(list)
    with tsv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            book_slug = row["book"]
            file_path = HE_DIR / book_slug / f"{book_slug.split('-', 1)[1]}-{int(row['chapter']):02d}.txt"
            by_file[file_path].append(row)

    applied = 0
    skipped = 0
    affected_books: set[str] = set()

    for file_path, rows in by_file.items():
        if not file_path.exists():
            print(f"[miss] {file_path}", file=sys.stderr)
            skipped += len(rows)
            continue

        original = file_path.read_text(encoding="utf-8")
        lines = original.split("\n")

        # Process in reverse-verse order so line indices don't shift mid-file
        rows.sort(key=lambda r: (-int(r["verse"]), -int(r["line_a_idx"])))

        for r in rows:
            verse = int(r["verse"])
            line_a_idx = int(r["line_a_idx"])
            line_b_idx = int(r["line_b_idx"])
            if line_b_idx != line_a_idx + 1:
                print(f"[skip] {file_path.name} v{verse}: "
                      f"line_b_idx ({line_b_idx}) must equal line_a_idx+1 ({line_a_idx + 1})",
                      file=sys.stderr)
                skipped += 1
                continue

            verse_line_file_idxs = find_verse_lines(lines, verse)
            if line_a_idx >= len(verse_line_file_idxs) or line_b_idx >= len(verse_line_file_idxs):
                print(f"[skip] {file_path.name} v{verse}: line idx out of range "
                      f"(verse has {len(verse_line_file_idxs)} lines)", file=sys.stderr)
                skipped += 1
                continue

            file_a = verse_line_file_idxs[line_a_idx]
            file_b = verse_line_file_idxs[line_b_idx]
            if file_b != file_a + 1:
                print(f"[skip] {file_path.name} v{verse}: target lines not contiguous in file",
                      file=sys.stderr)
                skipped += 1
                continue

            merged = lines[file_a].rstrip() + " " + lines[file_b].lstrip()
            lines[file_a] = merged
            del lines[file_b]
            applied += 1
            affected_books.add(file_path.parent.name)
            print(f"  [reverted] {file_path.parent.name}/{file_path.name} v{verse} "
                  f"lines {line_a_idx}+{line_b_idx} ({r.get('reason', 'no-reason-given')})",
                  file=sys.stderr)

        new_text = "\n".join(lines)
        if new_text != original and not args.dry_run:
            file_path.write_text(new_text, encoding="utf-8")

    print(f"\nApplied: {applied}", file=sys.stderr)
    print(f"Skipped: {skipped}", file=sys.stderr)
    print(f"Affected books: {len(affected_books)} — {' '.join(sorted(affected_books))}",
          file=sys.stderr)
    if args.dry_run:
        print("(dry-run — no files written)", file=sys.stderr)


if __name__ == "__main__":
    main()
