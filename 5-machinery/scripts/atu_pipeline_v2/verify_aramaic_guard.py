"""Independent re-verification of the Aramaic-guard 181-false-fires claim.

Hostile-audit prescription #3: re-run the with/without-guard sweep
independently. Don't rely on Pipeline B workflow output.
"""
from __future__ import annotations
import sys
from pathlib import Path

REPO = Path(r"C:/Users/bibleman/repos/readers-tanakh")
sys.path.insert(0, str(REPO / "5-machinery/scripts" / "atu_pipeline_v2"))

from aramaic_guard import ARAMAIC_RANGES, is_aramaic_verse  # noqa: E402
import binding_rules  # noqa: E402

from tf.app import use

print("Loading BHSA via Text-Fabric (etcbc/bhsa)...")
A = use("etcbc/bhsa", silent="deep")
F, L, T = A.api.F, A.api.L, A.api.T

BOOK_NAME = {"27-daniel": "Daniel", "15-ezra": "Ezra"}


def collect_aramaic_clauses(book_folder: str):
    book_name = BOOK_NAME[book_folder]
    book_node = next(b for b in F.otype.s("book") if T.sectionFromNode(b)[0] == book_name)
    for chap_node in L.d(book_node, otype="chapter"):
        _, chap_num = T.sectionFromNode(chap_node)[:2]
        for verse_node in L.d(chap_node, otype="verse"):
            verse_num = T.sectionFromNode(verse_node)[2]
            if not is_aramaic_verse(book_folder, chap_num, verse_num):
                continue
            cas = list(L.d(verse_node, otype="clause_atom"))
            clauses = []
            for ca in cas:
                words = list(L.d(ca, otype="word"))
                bhsa_text = " ".join(F.g_word_utf8.v(w) or "" for w in words)
                head_verb_lemma = ""
                head_verb_text = ""
                for w in words:
                    if F.pdp.v(w) == "verb":
                        head_verb_lemma = F.lex_utf8.v(w) or ""
                        head_verb_text = F.g_word_utf8.v(w) or ""
                        break
                clauses.append({
                    "cid": ca,
                    "verse": verse_num,
                    "clause_idx_in_verse": 0,
                    "typ": F.typ.v(ca) or "",
                    "rela": F.rela.v(ca) or "",
                    "domain": F.domain.v(ca) or "",
                    "head_verb_lemma": head_verb_lemma,
                    "head_verb_text": head_verb_text,
                    "text": bhsa_text,
                    "v0_token_first": 0,
                    "v0_token_last": 0,
                })
            yield chap_num, verse_num, clauses


def main():
    total_aramaic_clauses = 0
    total_aramaic_verses = 0
    pre_guard_fires_by_rule = {}
    pre_guard_total = 0

    for book_folder in ARAMAIC_RANGES:
        print(f"\n=== {book_folder} ===")
        book_clauses = 0
        book_verses = 0
        book_fires = 0
        for chap, verse, clauses in collect_aramaic_clauses(book_folder):
            total_aramaic_clauses += len(clauses)
            book_clauses += len(clauses)
            total_aramaic_verses += 1
            book_verses += 1
            for i in range(1, len(clauses)):
                prev, curr = clauses[i - 1], clauses[i]
                bind, rule = binding_rules.should_bind(prev, curr)
                if bind:
                    pre_guard_total += 1
                    book_fires += 1
                    pre_guard_fires_by_rule[rule] = pre_guard_fires_by_rule.get(rule, 0) + 1
        print(f"  Aramaic verses: {book_verses}")
        print(f"  Aramaic clause-atoms: {book_clauses}")
        print(f"  Pre-guard intra-verse fires: {book_fires}")

    print("\n=== TOTALS ===")
    print(f"Aramaic verses: {total_aramaic_verses}")
    print(f"Aramaic clause-atoms: {total_aramaic_clauses}")
    print(f"Pre-guard fires (would silently fire WITHOUT guard): {pre_guard_total}")
    print("Pre-guard fires by rule:")
    for rule, n in sorted(pre_guard_fires_by_rule.items(), key=lambda kv: -kv[1]):
        print(f"  {rule}: {n}")
    print(f"Post-guard fires (WITH guard active): 0 (by construction)")


if __name__ == "__main__":
    main()
