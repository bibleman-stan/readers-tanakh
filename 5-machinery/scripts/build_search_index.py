#!/usr/bin/env python3
"""
Build a prebuilt search index for tanakh-reader.com.

WHY: the page built its search index in the browser at runtime — a 20-worker
pool fetching all ~929 chapter HTML files and DOMParser-parsing each. Better
mitigated than the GNT freeze (small files, parallel fetches, progress bar),
but still 929 network round-trips + 929 parses on every first search. This
script does it once at build time; the page loads one JSON.

Mirrors the runtime walk exactly: per .verse (id v-CH-VS), join .he text
(with .punct stripped) and the .en-gloss text. Raw text only — the page
derives the diacritic-stripped / lowercased fields at load so stripDiacritics()
stays the single JS source of truth.

Output: data/search_index.json
Usage: PYTHONIOENCODING=utf-8 python 5-machinery/scripts/build_search_index.py
"""
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

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
INDEX_HTML = ROOT / 'index.html'
BOOKS_DIR = ROOT / 'books'
OUT = ROOT / 'data' / 'search_index.json'


def parse_books():
    """slug -> (name, chapters), in order, from index.html's BOOKS literal."""
    html = INDEX_HTML.read_text(encoding='utf-8')
    m = re.search(r'const BOOKS\s*=\s*\{(.*?)\n\};', html, re.S)
    if not m:
        sys.exit('BOOKS literal not found in index.html')
    body = m.group(1)
    books = []
    # match: 'slug': { name: 'X', ... chapters: N
    for row in re.finditer(
            r"'([^']+)':\s*\{\s*name:\s*'([^']+)'[^}]*?chapters:\s*(\d+)", body, re.S):
        books.append((row.group(1), row.group(2), int(row.group(3))))
    if not books:
        sys.exit('parsed zero books')
    return books


def extract(slug, name, html):
    soup = BeautifulSoup(html, 'html.parser')
    out = []
    for verse in soup.select('.verse'):
        m = re.match(r'^v-(\d+)-(\d+)$', verse.get('id', ''))
        if not m:
            continue
        ch, vn = int(m.group(1)), int(m.group(2))
        he_parts, en_parts = [], []
        for line in verse.select('.line'):
            he = line.find('span', class_='he')
            en = line.find('span', class_='en-gloss')
            if he:
                clone = BeautifulSoup(str(he), 'html.parser')
                for p in clone.select('.punct'):
                    p.extract()
                t = clone.get_text(' ').strip()
                t = re.sub(r'\s+', ' ', t)
                if t:
                    he_parts.append(t)
            if en:
                t = en.get_text().strip()
                if t:
                    en_parts.append(t)
        he_text = ' '.join(he_parts)
        en_text = ' '.join(en_parts)
        if he_text or en_text:
            out.append({'book': slug, 'bookName': name,
                        'chapter': ch, 'verse': vn,
                        'text': he_text, 'enText': en_text})
    return out


def main():
    books = parse_books()
    # Compact schema (23k verses): book names/ids once, verses as array rows
    # [bookIdx, chapter, verse, heText, enText]. ~halves the payload vs
    # repeating bookName + object keys per verse. The page expands rows back
    # to objects at load.
    book_ids = [b[0] for b in books]
    book_names = [b[1] for b in books]
    rows = []
    built = 0
    for bi, (slug, name, chapters) in enumerate(books):
        bdir = BOOKS_DIR / slug
        if not bdir.is_dir():
            continue
        for ch in range(1, chapters + 1):
            fp = bdir / f'{slug}-{ch:02d}.html'
            if not fp.exists():
                continue
            for e in extract(slug, name, fp.read_text(encoding='utf-8')):
                rows.append([bi, e['chapter'], e['verse'], e['text'], e['enText']])
            built += 1
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({'version': 1, 'books': book_names,
                               'bookIds': book_ids, 'v': rows},
                              ensure_ascii=False, separators=(',', ':')),
                   encoding='utf-8')
    kb = OUT.stat().st_size / 1024
    print(f'wrote {OUT.relative_to(ROOT)}: {len(rows)} verses '
          f'from {built} chapters, {kb:.0f}KB')


if __name__ == '__main__':
    main()
