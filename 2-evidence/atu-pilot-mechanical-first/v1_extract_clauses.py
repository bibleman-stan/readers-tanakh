#!/usr/bin/env python3
"""
v1_extract_clauses.py — mechanical clause-atom extraction for Genesis 22 via BHSA/Text-Fabric.

Output: one JSON line per clause-atom (in document order), with fields:
  - cid: integer clause-atom node id
  - verse: int (1..24)
  - clause_idx_in_verse: 0-based position within the verse
  - typ: BHSA clause type (e.g. 'WayX', 'WxQt', 'NmCl', 'xQtX', etc.)
  - domain: BHSA clause domain (V = verbal, N = nominal/verbless, etc.)
  - rela: relation to mother clause ('NoCo' = root; 'Cmpl', 'Resu', 'Adju', 'Attr', etc.)
  - head_verb_lemma: lemma of the finite/predicating verb if any
  - head_verb_text:  surface form of the head verb if any
  - text: pointed Hebrew text of the clause-atom, words space-joined

Also writes a human-readable .txt with one clause per line for quick inspection.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

from tf.app import use

sys.path.insert(0, str(Path(__file__).parent))
import pilot_config as cfg

OUT_DIR = cfg.PILOT_DIR
OUT_JSONL = cfg.V1_JSONL
OUT_TXT = cfg.V1_TXT


def main() -> None:
    print("Loading BHSA via Text-Fabric (first run will download ~100MB)...")
    A = use("etcbc/bhsa", silent="deep")
    api = A.api
    F = api.F
    L = api.L
    T = api.T

    # Locate target chapter node
    target_chapters = [
        c for c in F.otype.s("chapter")
        if T.sectionFromNode(c)[:2] == (cfg.BOOK_NAME, cfg.CHAPTER_NUM)
    ]
    if not target_chapters:
        raise SystemExit(f"ERROR: could not locate {cfg.CHAPTER_DISPLAY} chapter node in BHSA")
    chapter = target_chapters[0]

    # Collect clause_atoms in document order
    clause_atoms = list(L.d(chapter, otype="clause_atom"))
    print(f"Found {len(clause_atoms)} clause_atoms in {cfg.CHAPTER_DISPLAY}")

    # Group by verse for clause_idx_in_verse
    verse_counters: dict[int, int] = {}
    rows: list[dict] = []

    for ca in clause_atoms:
        # Section: (book, chapter, verse) — verse is taken from the FIRST word
        words = L.d(ca, otype="word")
        if not words:
            continue
        first_word = words[0]
        _, _, verse_num = T.sectionFromNode(first_word)
        idx_in_verse = verse_counters.get(verse_num, 0)
        verse_counters[verse_num] = idx_in_verse + 1

        # Surface text — pointed UTF-8 with maqaf etc. preserved
        word_texts = [F.g_word_utf8.v(w) + F.trailer_utf8.v(w) for w in words]
        text = "".join(word_texts).strip()

        # Clause-atom features
        typ = F.typ.v(ca) or ""
        domain = F.domain.v(ca) or ""
        rela = F.rela.v(ca) or ""

        # Identify head verb (first word with pdp == 'verb' inside the clause atom)
        head_verb_lemma = ""
        head_verb_text = ""
        for w in words:
            if F.pdp.v(w) == "verb":
                head_verb_lemma = F.lex_utf8.v(w) or ""
                head_verb_text = F.g_word_utf8.v(w) or ""
                break

        rows.append({
            "cid": ca,
            "verse": verse_num,
            "clause_idx_in_verse": idx_in_verse,
            "typ": typ,
            "domain": domain,
            "rela": rela,
            "head_verb_lemma": head_verb_lemma,
            "head_verb_text": head_verb_text,
            "text": text,
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with OUT_JSONL.open("w", encoding="utf-8") as fp:
        for r in rows:
            fp.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Human-readable companion
    with OUT_TXT.open("w", encoding="utf-8") as fp:
        current_verse = None
        for r in rows:
            if r["verse"] != current_verse:
                if current_verse is not None:
                    fp.write("\n")
                fp.write(f"=== {cfg.VERSE_PREFIX}{r['verse']} ===\n")
                current_verse = r["verse"]
            tags = f"[{r['typ']}/{r['domain']}/{r['rela']}]"
            verb = f" hd={r['head_verb_lemma']}" if r["head_verb_lemma"] else ""
            fp.write(f"  c{r['clause_idx_in_verse']}{verb} {tags}  {r['text']}\n")

    print(f"Wrote: {OUT_JSONL}")
    print(f"Wrote: {OUT_TXT}")

    # Summary
    by_verse = {}
    for r in rows:
        by_verse.setdefault(r["verse"], 0)
        by_verse[r["verse"]] += 1
    print(f"Clauses per verse: " + ", ".join(f"v.{v}={n}" for v, n in sorted(by_verse.items())))
    print(f"Total clauses: {len(rows)}")


if __name__ == "__main__":
    main()
