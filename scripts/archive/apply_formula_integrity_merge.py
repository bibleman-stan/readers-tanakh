#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_formula_integrity_merge.py — corpus-wide enforcement of M1
bonded-pair / formula-integrity merges for named Hebrew formulae.

The framework's M1 bonded-pair (framework.md §1.5) and formula-integrity
(§1.2.3) overrides identify multi-word lexicalized frames that read as a
single ATU. When such a frame is currently split across two adjacent v2/heb
cola, this script merges them.

Engine-plane infrastructure: the FORMULA registry below holds named
patterns; scanner walks the corpus, detects each unmerged instance, and
applies the merge. Adding a new bonded-pair formula = adding one entry
to the registry.

CURRENTLY REGISTERED FORMULAE:

  day_formula — Gen 1 day-formula bipartite merism
    Pattern: line N ends with `וַיְהִי־עֶרֶב` AND next line opens with
             `וַיְהִי־בֹקֶר` (with optional `יוֹם N` completion).
    Justification: M1 bonded-pair (evening+morning = one complete day,
    bipartite Hebrew expression of a temporal whole). Same shape as
    `שָׁמַיִם וָאָרֶץ`, `יוֹמָם וָלָיְלָה`. Both verbs share lemma `הָיָה`
    in wayyiqtol; the two clauses share an implicit copular subject.

  (Future entries: speech-intro merism `וַיַּעַן ... וַיֹּאמֶר`,
  continuation `וַיֹּסֶף לְדַבֵּר`, etc. — added as identified.)

Usage:
  PYTHONIOENCODING=utf-8 py -3 scripts/apply_formula_integrity_merge.py --dry-run
  PYTHONIOENCODING=utf-8 py -3 scripts/apply_formula_integrity_merge.py
  PYTHONIOENCODING=utf-8 py -3 scripts/apply_formula_integrity_merge.py --book 01-genesis
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata as _ud
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

VERSE_REF_RE = re.compile(r"^\d+:\d+\s*$")


def _consonants(s: str) -> str:
    """Strip te'amim, niqqud, maqqef, and whitespace; return bare consonants."""
    s = _ud.normalize("NFC", s)
    s = re.sub(r"[֑-ׇ־]", "", s)  # all Hebrew points + maqqef
    s = re.sub(r"\s+", "", s)
    return s


# --- FORMULA REGISTRY ---
#
# Each entry: name → {
#   "line_a_predicate": callable(stripped_consonants_str) → bool,
#   "line_b_predicate": callable(stripped_consonants_str) → bool,
#   "comment": "...",
# }
# Predicates inspect consonant-only forms (te'amim/niqqud-stripped) so
# variant pointing doesn't break detection.

def _ends_with_vayhi_erev(line: str) -> bool:
    """True if the line ENDS with the consonant signature of `וַיְהִי־עֶרֶב`."""
    cons = _consonants(line)
    # ויהיערב suffix; allow optional trailing sof passuq (already stripped)
    return cons.endswith("ויהיערב")


def _starts_with_vayhi_voker(line: str) -> bool:
    """True if the line STARTS with the consonant signature of `וַיְהִי־בֹקֶר`."""
    cons = _consonants(line)
    return cons.startswith("ויהיבקר")


FORMULAE = {
    "day_formula": {
        "line_a_predicate": _ends_with_vayhi_erev,
        "line_b_predicate": _starts_with_vayhi_voker,
        "comment": "M1 bonded-pair: evening+morning = one complete day (bipartite merism)",
    },
}


def find_merges_in_chapter(text: str) -> list[tuple[int, int, str]]:
    """Walk a chapter file's lines; return (line_a_idx, line_b_idx, formula_name)
    for each adjacent-cola pair (within one verse, no blank line between)
    matching any registered formula.
    """
    lines = text.split("\n")
    matches = []

    cur_verse = None
    in_verse_lines: list[int] = []  # 0-based file line indices

    def flush():
        if len(in_verse_lines) < 2:
            return
        # Walk consecutive pairs within this verse
        for j in range(len(in_verse_lines) - 1):
            a_idx = in_verse_lines[j]
            b_idx = in_verse_lines[j + 1]
            a_line = lines[a_idx]
            b_line = lines[b_idx]
            for name, spec in FORMULAE.items():
                if spec["line_a_predicate"](a_line) and spec["line_b_predicate"](b_line):
                    matches.append((a_idx, b_idx, name))
                    break

    for i, ln in enumerate(lines):
        if VERSE_REF_RE.match(ln.strip()):
            flush()
            cur_verse = int(ln.strip().split(":")[1])
            in_verse_lines = []
            continue
        if not ln.strip():
            flush()
            in_verse_lines = []
            continue
        if cur_verse is None:
            continue
        in_verse_lines.append(i)
    flush()

    return matches


def apply_merges_to_chapter(text: str, matches: list[tuple[int, int, str]]) -> str:
    """Apply the identified merges. Process in REVERSE order so line-index
    shifts don't invalidate later matches."""
    if not matches:
        return text
    lines = text.split("\n")
    for a_idx, b_idx, _name in sorted(matches, key=lambda m: -m[0]):
        if b_idx != a_idx + 1:
            continue  # safety: only contiguous pairs
        lines[a_idx] = lines[a_idx].rstrip() + " " + lines[b_idx].lstrip()
        del lines[b_idx]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--book", default=None)
    args = ap.parse_args()

    he_root = REPO_ROOT / "data" / "text-files" / "v2" / "heb"
    if args.book:
        books = [args.book]
    else:
        books = sorted([d.name for d in he_root.iterdir() if d.is_dir()])

    total_merges = 0
    affected_books: set[str] = set()
    by_formula: dict[str, int] = defaultdict(int)

    for book in books:
        book_dir = he_root / book
        if not book_dir.is_dir():
            continue
        for ch_path in sorted(book_dir.glob("*.txt")):
            text = ch_path.read_text(encoding="utf-8")
            matches = find_merges_in_chapter(text)
            if not matches:
                continue
            for _, _, name in matches:
                by_formula[name] += 1
            total_merges += len(matches)
            affected_books.add(book)
            for a_idx, b_idx, name in matches:
                print(f"  {book}/{ch_path.name}:{a_idx+1}-{b_idx+1}  [{name}]", file=sys.stderr)
            new_text = apply_merges_to_chapter(text, matches)
            if not args.dry_run and new_text != text:
                ch_path.write_text(new_text, encoding="utf-8")

    print(f"\nTotal merges: {total_merges}", file=sys.stderr)
    for name, count in sorted(by_formula.items()):
        print(f"  {name}: {count}", file=sys.stderr)
    print(f"Affected books: {len(affected_books)}", file=sys.stderr)
    if args.dry_run:
        print("(dry-run — no files written)", file=sys.stderr)


if __name__ == "__main__":
    main()
