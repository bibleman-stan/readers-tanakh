"""
Extract Hpar findings that score HIGH-CONFIDENCE-TP via the
share-A1 frame-args signal — both clauses target the same object
referent, the canonical synonymous-parallelism pattern (Isa 13:20
"she will not dwell [in it] / nor inhabited [in it]").

Output: data/syntax-reference/hpar-high-confidence.tsv — review list
for editor application.

Usage:
    PYTHONIOENCODING=utf-8 py -3 5-machinery/scripts/extract_hpar_high_confidence.py
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "5-machinery/validators"))

from validators._shared import macula_constituents as MC
from validators.colometry.validate_parallel_clause_split import (
    _is_leaf_clause, _clause_head_verb, _clauses_with_heads_in,
    _split_index, _pw_count, MIN_HALF_PW, _is_wayyiqtol,
    _frame_args_share_object,
)


def main():
    he_dir = REPO_ROOT / "data" / "text-files"  / "v2" / "heb"
    out_path = REPO_ROOT / "data" / "syntax-reference" / "hpar-high-confidence.tsv"

    rows = []
    rows.append("\t".join([
        "book", "chapter", "verse", "file_line",
        "head_a", "head_b", "shared_a1_id",
        "left_pw", "right_pw", "split_position",
        "prior_text", "next_text",
    ]))

    for book_dir in sorted(he_dir.iterdir()):
        if not book_dir.is_dir():
            continue
        book_slug = book_dir.name
        if book_slug not in MC._BOOK_MAP:
            continue
        for ch_file in sorted(book_dir.glob("*.txt")):
            m = re.search(r"-(\d+)\.txt$", ch_file.name)
            if not m:
                continue
            chapter_no = int(m.group(1))
            text = ch_file.read_text(encoding="utf-8")
            lines = text.split("\n")
            cur_verse = None
            vlines, vidx = [], []

            def flush(verse, lines_for, indices):
                if verse is None or not lines_for:
                    return
                try:
                    vtokens = MC.get_verse_tokens(book_slug, chapter_no, verse)
                    vclauses = MC.get_verse_clauses(book_slug, chapter_no, verse)
                except Exception:
                    return
                if not vtokens or not vclauses:
                    return
                cursor = 0
                line_token_lists = []
                for ln in lines_for:
                    matched, next_cursor = MC.match_sense_line_tokens(vtokens, ln, cursor)
                    line_token_lists.append(matched)
                    cursor = next_cursor
                for line_tokens, line_text, file_line_no in zip(
                    line_token_lists, lines_for, indices
                ):
                    if len(line_tokens) < 4:
                        continue
                    clauses_here = _clauses_with_heads_in(vclauses, line_tokens)
                    if len(clauses_here) < 2:
                        continue
                    heads = [_clause_head_verb(c) for c in clauses_here]
                    if all(h is not None and _is_wayyiqtol(h) for h in heads):
                        continue
                    clauses_sorted = sorted(
                        clauses_here,
                        key=lambda c: next(
                            (i for i, t in enumerate(line_tokens)
                             if id(t) in {id(x) for x in c.tokens}),
                            9999,
                        ),
                    )
                    for j in range(len(clauses_sorted) - 1):
                        cl_a = clauses_sorted[j]
                        cl_b = clauses_sorted[j + 1]
                        idx = _split_index(line_tokens, cl_b)
                        if idx is None or idx == 0:
                            continue
                        left = _pw_count(line_tokens[:idx])
                        right = _pw_count(line_tokens[idx:])
                        if left < MIN_HALF_PW or right < MIN_HALF_PW:
                            continue
                        head_a = _clause_head_verb(cl_a)
                        head_b = _clause_head_verb(cl_b)
                        if (head_a and head_b and head_a.lemma and head_b.lemma
                                and head_a.lemma == head_b.lemma):
                            continue
                        if not _frame_args_share_object(head_a, head_b):
                            continue
                        # FP guard 2026-05-07 (Stan-flagged review pass):
                        # if the LINE token immediately before cl_b's first
                        # token is a relativizer (אֲשֶׁר / דִּי), clause B
                        # is a relative-clause modifying cl_a's antecedent,
                        # NOT a parallel cola — even though both target the
                        # same A1 (the antecedent). Caught: Exod 25:22,
                        # Deut 17:15, Esth 1:20, Isa 56:5, Jer 23:40,
                        # Jer 34:14, Dan 2:44.
                        if idx > 0:
                            prev_tok = line_tokens[idx - 1]
                            if prev_tok.consonant_skel in ("אשר", "די"):
                                continue
                        # High-confidence! Record it.
                        a_a1 = head_a.frame_arg_ids.get("A1", [])
                        shared_id = a_a1[0] if a_a1 else "?"
                        prior = " ".join(t.text for t in line_tokens[:idx])
                        nxt = " ".join(t.text for t in line_tokens[idx:])
                        rows.append("\t".join([
                            book_slug, str(chapter_no), str(verse),
                            str(file_line_no),
                            head_a.text if head_a else "?",
                            head_b.text if head_b else "?",
                            shared_id,
                            str(left), str(right), str(idx),
                            prior, nxt,
                        ]))

            for i, line in enumerate(lines):
                mv = re.match(r"^(\d+):(\d+)\s*$", line.strip())
                if mv:
                    if cur_verse is not None and vlines:
                        flush(cur_verse, vlines, vidx)
                    cur_verse = int(mv.group(2))
                    vlines, vidx = [], []
                    continue
                if not line.strip():
                    if cur_verse is not None and vlines:
                        flush(cur_verse, vlines, vidx)
                    vlines, vidx = [], []
                    continue
                if cur_verse is None:
                    continue
                vlines.append(line)
                vidx.append(i + 1)
            if cur_verse is not None and vlines:
                flush(cur_verse, vlines, vidx)

    out_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows) - 1} high-confidence Hpar findings to {out_path}")


if __name__ == "__main__":
    main()
