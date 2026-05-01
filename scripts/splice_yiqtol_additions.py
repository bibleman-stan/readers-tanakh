#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Splice the TAHOT-tag-driven YIQTOL FP proper-noun additions into morphology.py.

Reads the emitted block at C:/tmp/yiqtol_block.txt and inserts it just
before the closing brace of YIQTOL_KNOWN_NOUNS in
validators/_shared/morphology.py.

Idempotent: detects existing insertion marker and refuses to double-add.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "validators" / "_shared" / "morphology.py"
BLOCK_FILE = Path("C:/tmp/yiqtol_block.txt")
MARKER = "# ── TAHOT-tag-driven YIQTOL FP sweep (2026-04-30, 459 additions)"

if not BLOCK_FILE.exists():
    sys.exit(f"ERROR: block file not found at {BLOCK_FILE}. "
             "Run sweep_yiqtol_proper_noun_fps.py --emit-python first.")

text = TARGET.read_text(encoding="utf-8")

if MARKER in text:
    sys.exit("Already spliced (insertion marker present). Refusing double-add.")

# The closing brace of YIQTOL_KNOWN_NOUNS is the first standalone "}" line
# after the line containing "Nun-prefix proper nouns" comment.
lines = text.splitlines(keepends=True)
nun_marker_idx = None
close_brace_idx = None
for i, line in enumerate(lines):
    if "Nun-prefix proper nouns" in line:
        nun_marker_idx = i
    if nun_marker_idx is not None and line.strip() == "}":
        close_brace_idx = i
        break

if close_brace_idx is None:
    sys.exit("ERROR: could not locate closing brace of YIQTOL_KNOWN_NOUNS")

block = BLOCK_FILE.read_text(encoding="utf-8")
# Each block line already includes a trailing newline.
insert_lines = [
    f"    {MARKER}\n",
    "    # Source: scripts/sweep_yiqtol_proper_noun_fps.py — uses v0/morph TAHOT\n",
    "    # tags to enumerate every proper noun whose skel matches the YIQTOL FP\n",
    "    # shape but isn't already in this set. Frequency-sorted; counts in comments.\n",
    "    # Audit-driven: extermination of the morphology FP class blocking ~1931\n",
    "    # corpus instances of legitimate verb+bare-NP merges (per audit D3 2026-04-30).\n",
]
# block lines already have proper indentation from emit-python (4-space indent + entry)
new_lines = lines[:close_brace_idx] + insert_lines + [block] + [lines[close_brace_idx]] + lines[close_brace_idx + 1:]
new_text = "".join(new_lines)

TARGET.write_text(new_text, encoding="utf-8", newline="\n")
print(f"Spliced {block.count(chr(10))} entries into {TARGET}")
print(f"  insertion point: line {close_brace_idx + 1} (before closing brace)")
