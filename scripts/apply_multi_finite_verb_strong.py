#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_multi_finite_verb_strong.py — Apply Hmfv STRONG-SPLIT-CANDIDATE
findings to v2/heb as forward-compatible cola splits.

Reads data/syntax-reference/multi-finite-verb-candidates.tsv, filters to
SEVERITY == 'STRONG-SPLIT-CANDIDATE', and inserts a line break before
each second-clause's first token. Re-derives the split position via
Macula clause-detection (same primitives as scan_multi_finite_verb_line.py
and validate_parallel_clause_split.py).

The splits are forward-compatible (insert line breaks only; never remove
editorial work), so safe to apply mechanically.

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/apply_multi_finite_verb_strong.py --dry-run
    PYTHONIOENCODING=utf-8 py -3 scripts/apply_multi_finite_verb_strong.py
    PYTHONIOENCODING=utf-8 py -3 scripts/apply_multi_finite_verb_strong.py --book 01-genesis

Post-apply: refresh_book.py per affected book regenerates derived layers.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from validators._shared import macula_constituents as MC


def _normalize_skel(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"[֑-ֿ׀-ׇ־]", "", s)
    s = re.sub(r"\s+", "", s)
    return s


def _is_finite_verb(t) -> bool:
    morph = (t._morph_tag or "").upper()
    if not morph or morph[0] != "V" or len(morph) < 3:
        return False
    return morph[2] in ("Q", "W", "I", "V", "O", "J", "H", "U")


def _is_leaf_clause(cl) -> bool:
    for c in cl.child_constituents:
        if c.is_clause:
            return False
        for gc in c.child_constituents:
            if gc.is_clause:
                return False
    return True


def _clause_head_verb(cl):
    for t in cl.tokens:
        if _is_finite_verb(t):
            return t
    return None


def _clauses_with_heads_in(vclauses, line_tokens):
    line_ids = {id(t) for t in line_tokens}
    out = []
    for cl in vclauses:
        if not _is_leaf_clause(cl):
            continue
        head = _clause_head_verb(cl)
        if head is None:
            continue
        if id(head) in line_ids:
            out.append(cl)
    return out


def _prosodic_word_count(text: str) -> int:
    """Hebrew prosodic-word count: whitespace-separated tokens, with each
    maqqef-bound pair counting as separate prosodic words. Mirrors the
    verifier at validators/4-layer-integrity/verify_4_layer_sync.py."""
    if not text.strip():
        return 0
    pw = 0
    for ws_token in text.split():
        # Each whitespace-separated unit may contain N maqqef-bound prosodic words
        pw += ws_token.count("־") + 1  # maqqef ־ = U+05BE
    return pw


def find_split_offset(line_text: str, target_token) -> int:
    target_skel = target_token.consonant_skel
    if not target_skel:
        return -1
    for m in re.finditer(r"\S+", line_text):
        tok = m.group(0)
        tok_skel = _normalize_skel(tok)
        if not tok_skel:
            continue
        if tok_skel == target_skel:
            return m.start()
        if tok_skel.endswith(target_skel) and len(tok_skel) - len(target_skel) <= 2:
            return m.start()
        if target_skel.startswith(tok_skel) and len(target_skel) - len(tok_skel) <= 4:
            return m.start()
        if len(target_skel) >= 3 and target_skel in tok_skel:
            return m.start()
    return -1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--book", default=None)
    ap.add_argument("--tsv", default=None)
    args = ap.parse_args()

    tsv_path = Path(args.tsv) if args.tsv else (
        REPO_ROOT / "data" / "syntax-reference" / "multi-finite-verb-candidates.tsv"
    )
    he_dir = REPO_ROOT / "data" / "text-files"  / "v2" / "heb"

    findings_by_file: dict[Path, list[dict]] = defaultdict(list)
    skipped_severity = 0
    skipped_book = 0
    with tsv_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if row["severity"] != "STRONG-SPLIT-CANDIDATE":
                skipped_severity += 1
                continue
            book_slug = row["book"]
            if args.book and book_slug != args.book:
                skipped_book += 1
                continue
            file_path = he_dir / book_slug / f"{book_slug.split('-', 1)[1]}-{int(row['chapter']):02d}.txt"
            findings_by_file[file_path].append(row)

    print(f"STRONG findings: {sum(len(v) for v in findings_by_file.values())} "
          f"across {len(findings_by_file)} files", file=sys.stderr)

    applied = 0
    skipped = 0
    affected_books: set[str] = set()

    for file_path, findings in findings_by_file.items():
        if not file_path.exists():
            print(f"[miss] {file_path}", file=sys.stderr)
            continue

        book_slug = file_path.parent.name
        original_text = file_path.read_text(encoding="utf-8")
        lines = original_text.split("\n")

        findings.sort(key=lambda r: (-int(r["verse"]), -int(r["line_idx"])))

        for r in findings:
            chapter = int(r["chapter"])
            verse = int(r["verse"])
            line_idx_in_verse = int(r["line_idx"])
            tsv_hebrew = r["hebrew_line"]

            verse_marker_re = re.compile(rf"^{chapter}:{verse}\s*$")
            file_line_idx = None
            cur_line_in_verse = 0
            in_verse = False
            for i, ln in enumerate(lines):
                if verse_marker_re.match(ln.strip()):
                    in_verse = True
                    cur_line_in_verse = 0
                    continue
                if in_verse:
                    if not ln.strip():
                        in_verse = False
                        continue
                    if re.match(r"^\d+:\d+\s*$", ln.strip()):
                        in_verse = False
                        continue
                    if cur_line_in_verse == line_idx_in_verse:
                        if ln.strip() == tsv_hebrew or ln == tsv_hebrew:
                            file_line_idx = i
                        break
                    cur_line_in_verse += 1

            if file_line_idx is None:
                if args.dry_run:
                    print(f"[skip-line-match] {file_path.name} {chapter}:{verse} idx={line_idx_in_verse}", file=sys.stderr)
                skipped += 1
                continue

            line_text = lines[file_line_idx]

            try:
                vclauses = MC.get_verse_clauses(book_slug, chapter, verse)
                vtokens = MC.get_verse_tokens(book_slug, chapter, verse)
            except Exception as e:
                if args.dry_run:
                    print(f"[skip-macula-load] {file_path.name} {chapter}:{verse}: {e}", file=sys.stderr)
                skipped += 1
                continue

            # Find the verse-marker line; walk only lines AFTER it within the
            # same verse (vtokens is verse-scoped, not chapter-scoped).
            verse_marker_idx = None
            for j in range(file_line_idx - 1, -1, -1):
                if verse_marker_re.match(lines[j].strip()):
                    verse_marker_idx = j
                    break
            cursor = 0
            if verse_marker_idx is not None:
                for j in range(verse_marker_idx + 1, file_line_idx):
                    ln = lines[j]
                    if not ln.strip() or re.match(r"^\d+:\d+\s*$", ln.strip()):
                        continue
                    _, cursor = MC.match_sense_line_tokens(vtokens, ln, cursor)

            line_tokens, _ = MC.match_sense_line_tokens(vtokens, line_text, cursor)
            clauses_here = _clauses_with_heads_in(vclauses, line_tokens)
            if len(clauses_here) < 2:
                if args.dry_run:
                    print(f"[skip-clauses<2] {file_path.name} {chapter}:{verse}: found {len(clauses_here)}", file=sys.stderr)
                skipped += 1
                continue

            cl_b = clauses_here[1]
            cl_b_first_token = cl_b.tokens[0] if cl_b.tokens else _clause_head_verb(cl_b)
            if cl_b_first_token is None:
                if args.dry_run:
                    print(f"[skip-no-cl_b-token] {file_path.name} {chapter}:{verse}", file=sys.stderr)
                skipped += 1
                continue

            offset = find_split_offset(line_text, cl_b_first_token)
            if offset <= 0:
                if args.dry_run:
                    print(f"[skip-no-offset] {file_path.name} {chapter}:{verse}: target={cl_b_first_token.text!r}", file=sys.stderr)
                skipped += 1
                continue

            prior = line_text[:offset].rstrip()
            nxt = line_text[offset:].lstrip()
            if not prior or not nxt:
                if args.dry_run:
                    print(f"[skip-empty-half] {file_path.name} {chapter}:{verse}", file=sys.stderr)
                skipped += 1
                continue

            # 4-layer-integrity preservation check (root-caused 2026-05-12):
            # If the split crosses a maqqef-bound prosodic-word boundary,
            # propagate_editorial_layers can't mirror the new break onto
            # the per-word v1 layers (translit + eng-interlinear). Skip
            # the apply if pw-count doesn't add up.
            pw_orig = _prosodic_word_count(line_text)
            pw_split = _prosodic_word_count(prior) + _prosodic_word_count(nxt)
            if pw_orig != pw_split:
                if args.dry_run:
                    print(f"[skip-pw-parity] {file_path.name} {chapter}:{verse}: "
                          f"orig pw={pw_orig} != split pw={pw_split} "
                          f"(split would cross maqqef-bound pair, breaking 4-layer integrity)",
                          file=sys.stderr)
                skipped += 1
                continue

            lines[file_line_idx] = prior + "\n" + nxt
            applied += 1
            affected_books.add(book_slug)

        new_text = "\n".join(lines)
        if new_text != original_text and not args.dry_run:
            file_path.write_text(new_text, encoding="utf-8")

    print(f"Applied: {applied}", file=sys.stderr)
    print(f"Skipped: {skipped}", file=sys.stderr)
    print(f"Affected books: {len(affected_books)} — {' '.join(sorted(affected_books))}", file=sys.stderr)
    if args.dry_run:
        print("(dry-run — no files written)", file=sys.stderr)


if __name__ == "__main__":
    main()
