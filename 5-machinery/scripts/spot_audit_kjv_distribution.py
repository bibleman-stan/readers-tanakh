#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""spot_audit_kjv_distribution.py — sample N verses corpus-wide, capture
pre-fix vs post-fix English-per-cola mappings, and emit a diff TSV for
hand-classification or agent-driven review.

Used to spot-audit the closed-list trailing-complement fix in
atu-method/distribute.py (commit 57d1a87) — fixture verifies 12 verses
but the change touches ~6,925 pronoun-suffix tokens; we want to confirm
no unexpected regressions across the long tail.

Sampling strategy:
1. For each of the 39 books, list verses likely to fire Pass C
   orphan-attachment under the new closed-list rule (any verse whose
   pre-fix KJV contains a closed-list complement word at non-line-start
   position).
2. Stratified-sample N total: at least 1 per book; remaining biased
   toward books with more candidates.
3. For each sample, read pre-fix (git show HEAD~1:...) and post-fix
   (current) per-cola English. Emit a diff entry only if the two differ.

Output: 5-machinery/tests/spot-audit-results.tsv with columns
  book / chapter / verse / category / pre_fix_lines (\\n-joined) /
  post_fix_lines / diff_summary
"""

from __future__ import annotations

import argparse
import csv
import random
import re
import subprocess
import sys
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
ENG_KJV_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "eng-kjv"
OUT_TSV = REPO_ROOT / "5-machinery/tests" / "spot-audit-results.tsv"

# Closed-list from atu-method/atu_method/kjv_alignment/distribute.py.
TRAILING_COMPLEMENT = {
    "him", "her", "it", "them", "me", "us", "thee", "you",
    "on", "in", "into", "unto", "upon", "with", "by", "from",
    "at", "for", "of", "against", "before", "behind", "under", "over",
    "among", "through", "about",
}

# Cluster routing for stratified sampling (so all clusters covered).
CLUSTERS = {
    "torah": ["01-genesis", "02-exodus", "03-leviticus", "04-numbers", "05-deuteronomy"],
    "former-prophets": ["06-joshua", "07-judges", "09-1samuel", "10-2samuel",
                        "11-1kings", "12-2kings"],
    "latter-prophets": ["23-isaiah", "24-jeremiah", "26-ezekiel",
                        "28-hosea", "29-joel", "30-amos", "31-obadiah",
                        "32-jonah", "33-micah", "34-nahum", "35-habakkuk",
                        "36-zephaniah", "37-haggai", "38-zechariah", "39-malachi"],
    "writings-prose": ["08-ruth", "17-esther", "27-daniel", "15-ezra",
                       "16-nehemiah", "13-1chronicles", "14-2chronicles",
                       "21-ecclesiastes"],
    "sifrei-emet": ["18-job", "19-psalms", "20-proverbs"],
    "embedded-poetry": ["22-songofsongs", "25-lamentations"],
}


def list_book_verses(book: str) -> list[tuple[int, int]]:
    """Return all (chapter, verse) pairs in a book by parsing eng-kjv files."""
    book_dir = ENG_KJV_DIR / book
    if not book_dir.exists():
        return []
    out = []
    for f in sorted(book_dir.glob("*.txt")):
        m = re.search(r"-(\d+)\.txt$", f.name)
        if not m:
            continue
        chapter = int(m.group(1))
        text = f.read_text(encoding="utf-8")
        for ln in text.split("\n"):
            mm = re.match(r"^(\d+):(\d+)\s*$", ln.strip())
            if mm and int(mm.group(1)) == chapter:
                out.append((chapter, int(mm.group(2))))
    return out


def read_verse_lines(book: str, chapter: int, verse: int) -> list[str]:
    chap_path = ENG_KJV_DIR / book / f"{book.split('-', 1)[1]}-{chapter:02d}.txt"
    if not chap_path.exists():
        return []
    return _extract_verse(chap_path.read_text(encoding="utf-8"), chapter, verse)


def read_verse_lines_at_commit(book: str, chapter: int, verse: int,
                                commit: str) -> list[str]:
    rel_path = f"data/text-files/v2/eng-kjv/{book}/{book.split('-', 1)[1]}-{chapter:02d}.txt"
    try:
        result = subprocess.run(
            ["git", "show", f"{commit}:{rel_path}"],
            capture_output=True, text=True, check=False, encoding="utf-8",
        )
        if result.returncode != 0:
            return []
        return _extract_verse(result.stdout, chapter, verse)
    except Exception:
        return []


def _extract_verse(text: str, chapter: int, verse: int) -> list[str]:
    out = []
    in_verse = False
    for ln in text.split("\n"):
        s = ln.strip()
        if s == f"{chapter}:{verse}":
            in_verse = True
            continue
        if in_verse:
            if not s:
                break
            if re.match(r"^\d+:\d+\s*$", s):
                break
            out.append(ln)
    return out


def has_closed_list_candidate(verse_lines: list[str]) -> bool:
    """Return True if verse contains any closed-list complement word at
    non-first-word position on any line — i.e., where Pass C orphan
    attachment likely fired."""
    for ln in verse_lines:
        words = re.findall(r"[A-Za-z]+'?[A-Za-z]*", ln)
        for i, w in enumerate(words):
            if i == 0:
                continue
            if w.lower() in TRAILING_COMPLEMENT:
                return True
    return False


def sample(book: str, n_per_book: int, seed: int) -> list[tuple[int, int]]:
    """Sample n_per_book verses from a book, biased toward closed-list
    candidates. Falls back to random if not enough candidates."""
    all_verses = list_book_verses(book)
    if not all_verses:
        return []

    rng = random.Random(f"{seed}|{book}")
    candidates = []
    for ch, vs in all_verses:
        post_lines = read_verse_lines(book, ch, vs)
        if has_closed_list_candidate(post_lines):
            candidates.append((ch, vs))

    if len(candidates) >= n_per_book:
        return rng.sample(candidates, n_per_book)
    # Fall back: top up with random non-candidates
    rest = [v for v in all_verses if v not in candidates]
    rng.shuffle(rest)
    return candidates + rest[: n_per_book - len(candidates)]


def diff_summary(pre_lines: list[str], post_lines: list[str]) -> str:
    """Short textual summary of how the two differ."""
    if pre_lines == post_lines:
        return "IDENTICAL"
    if len(pre_lines) != len(post_lines):
        return f"LINE-COUNT-DIFF pre={len(pre_lines)} post={len(post_lines)}"
    diffs = []
    for i, (a, b) in enumerate(zip(pre_lines, post_lines)):
        if a != b:
            diffs.append(f"L{i + 1}")
    return f"DIFF on {','.join(diffs)}" if diffs else "IDENTICAL"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=50,
                    help="Total samples (will be split per cluster, min 1 per book)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--pre-fix-commit", default="HEAD~1")
    args = ap.parse_args()

    n_books = sum(len(books) for books in CLUSTERS.values())
    n_per_book = max(1, args.n // n_books)
    print(f"Sampling {n_per_book} per book × {n_books} books "
          f"= {n_per_book * n_books} total candidates", file=sys.stderr)

    rows = []
    for cluster, books in CLUSTERS.items():
        for book in books:
            samples = sample(book, n_per_book, args.seed)
            for ch, vs in samples:
                pre = read_verse_lines_at_commit(book, ch, vs, args.pre_fix_commit)
                post = read_verse_lines(book, ch, vs)
                summary = diff_summary(pre, post)
                if summary == "IDENTICAL":
                    continue
                rows.append({
                    "book": book,
                    "cluster": cluster,
                    "chapter": ch,
                    "verse": vs,
                    "diff_summary": summary,
                    "pre_fix_lines": " ¶ ".join(pre),
                    "post_fix_lines": " ¶ ".join(post),
                })

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_TSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, delimiter="\t",
                            fieldnames=["book", "cluster", "chapter", "verse",
                                        "diff_summary", "pre_fix_lines", "post_fix_lines"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"\nDiff samples: {len(rows)} (out of {n_per_book * n_books} candidates)",
          file=sys.stderr)
    print(f"Output: {OUT_TSV}", file=sys.stderr)


if __name__ == "__main__":
    main()
