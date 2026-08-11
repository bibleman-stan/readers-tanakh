#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply H19 anaphoric-frame merges (bidirectional ATU test) to v2/heb.

13-verse registry from Macula detector + §7.3 audit-pass (CLEAR-WITH-
MODIFICATIONS). Each entry collapses a wayehi+anaphoric-frame line with
its apodosis line. 1Ch 19:1 is a special 3-line merge (pre-existing
apodosis-fracture; lines 1+2+3 collapse to match 2 Sa 10:1 parallel).

Word-stream invariant: the script ONLY moves line breaks. No words
added/removed; no token reordering.

After running, run 5-machinery/scripts/propagate_editorial_layers.py + regenerate_english.py
+ build_books.py to refresh the per-word layers and built HTML.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
V2_HEB = REPO_ROOT / "data" / "text-files" / "v2" / "heb"


# Registry: (book, chapter, verse, n_lines_to_merge)
# n_lines_to_merge = 2 (standard frame+apodosis); 3 for 1Ch 19:1 (special)
REGISTRY = [
    ("01-genesis",       22,  1, 2),
    ("01-genesis",       22, 20, 2),
    ("01-genesis",       39,  7, 2),
    ("01-genesis",       40,  1, 2),
    ("07-judges",        16,  4, 2),
    ("09-1samuel",       24,  6, 2),
    ("10-2samuel",        8,  1, 2),
    ("10-2samuel",       10,  1, 2),
    ("10-2samuel",       21, 18, 2),
    ("12-2kings",         6, 24, 2),
    ("13-1chronicles",   18,  1, 2),
    ("13-1chronicles",   19,  1, 3),   # special: merge lines 1+2+3
    ("13-1chronicles",   20,  4, 2),
]


def apply_merge(book: str, chapter: int, verse: int, n_lines: int) -> tuple[bool, str]:
    """Collapse first n_lines of the verse into a single line. Returns
    (success, message)."""
    short = book.split("-", 1)[1]
    chap_path = V2_HEB / book / f"{short}-{chapter:02d}.txt"
    if not chap_path.exists():
        return False, f"chapter file not found: {chap_path}"

    content = chap_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    verse_ref = f"{chapter}:{verse}"

    # Find the verse-ref line
    verse_idx = None
    for i, ln in enumerate(lines):
        if ln.strip() == verse_ref:
            verse_idx = i
            break
    if verse_idx is None:
        return False, f"verse ref {verse_ref} not found"

    # Collect the next n_lines content-lines
    content_starts = []
    j = verse_idx + 1
    while j < len(lines) and len(content_starts) < n_lines:
        s = lines[j].strip()
        if not s:
            break
        # Next verse-ref means we've run out of content lines
        if ":" in s and s.replace(":", "").replace(" ", "").isdigit():
            break
        content_starts.append(j)
        j += 1

    if len(content_starts) != n_lines:
        return False, f"expected {n_lines} content lines, got {len(content_starts)}"

    # Merge the lines (preserve original whitespace structure: join with single space)
    merged = " ".join(lines[idx].rstrip() for idx in content_starts).strip()
    # Replace lines: keep verse_idx (the ref), replace first content line with
    # merged, delete the others
    new_lines = lines[:content_starts[0]] + [merged] + lines[content_starts[-1] + 1:]
    new_content = "\n".join(new_lines)
    # Preserve trailing newline if original had one
    if content.endswith("\n"):
        new_content += "\n"
    chap_path.write_text(new_content, encoding="utf-8")
    return True, f"merged {n_lines} lines → 1"


def main():
    print(f"=== H19 anaphoric-frame merge apply ({len(REGISTRY)} verses) ===\n")
    pass_count = 0
    fail_count = 0
    for book, ch, vs, n in REGISTRY:
        ok, msg = apply_merge(book, ch, vs, n)
        tag = "✓" if ok else "✗"
        print(f"  {tag} {book} {ch}:{vs} (n={n}) — {msg}")
        if ok:
            pass_count += 1
        else:
            fail_count += 1
    print(f"\n=== Results: {pass_count} applied, {fail_count} failed ===")
    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
