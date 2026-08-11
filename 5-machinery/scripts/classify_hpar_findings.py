"""
Exhaustive Hpar finding classifier — uses Macula's `Constituent.wg_rule` and
related structural attributes to classify every Hpar (validate_parallel_clause_
split) finding into one of:

  COORDINATE-TP    — clause A and clause B are siblings under a coordination
                     parent (wg_rule ∈ COORD_RULES) → genuine parallel cola
  COMPLEMENT-FP    — clause A's structure indicates it takes clause B as
                     complement (wg_rule ∈ COMPLEMENT_RULES) → embedded speech /
                     complement-כִּי / matrix-takes-clausal-object
  SUBORDINATE-FP   — clause B is structurally subordinate (relative clause,
                     CLaCL pattern) → not parallel
  AMBIGUOUS        — wg_rule pattern doesn't match any of the above closed
                     lists; needs further inspection

Output: stratified summary + CSV of per-finding classifications.

This script answers the Hpar audit question exhaustively (3,143 findings) at
the constituent-tree level, replacing the 30-finding Sonnet sample (which
auditor #2 flagged as the wrong tool for structurally-scriptable FP classes).

Usage:
    PYTHONIOENCODING=utf-8 py -3 5-machinery/scripts/classify_hpar_findings.py
    PYTHONIOENCODING=utf-8 py -3 5-machinery/scripts/classify_hpar_findings.py --book 19-psalms
    PYTHONIOENCODING=utf-8 py -3 5-machinery/scripts/classify_hpar_findings.py --csv > C:/tmp/hpar_classified.csv
"""
import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "5-machinery/validators"))

from validators._shared import macula_constituents as MC
from validators.colometry.validate_parallel_clause_split import (
    _is_finite_verb, _is_leaf_clause, _clause_head_verb, _clauses_with_heads_in,
    _split_index, _pw_count, MIN_HALF_PW,
)


# Closed-list wg_rule patterns from auditor #2's analysis + manual diagnostic
# (today's session): clauses whose internal structure indicates the relationship
# between this clause and its surrounding clauses.

# Rules indicating clause B is a COMPLEMENT of clause A's matrix verb.
# V2CL = "verb-to-clause" (matrix takes clausal complement / embedded speech).
# O-V (object-fronted verb) often appears as the complement clause itself.
COMPLEMENT_RULES = frozenset({"V2CL", "Np2CL"})

# Rules indicating clause B is structurally SUBORDINATE to clause A.
# CLaCL = clause-attached-to-clause (subordinate attachment).
# relCL = relative clause (also caught by Constituent.is_relative_clause).
SUBORDINATE_RULES = frozenset({"CLaCL", "relCL"})

# Rules indicating clause-clause COORDINATION (genuine parallel cola candidate).
# ClCl = two-clause coordination. ClClCl = three-clause. Conj3CL = three-way
# conjunction. cjpCLx = conjunction-prefix clause.
COORD_RULES = frozenset({"ClCl", "ClClCl", "Conj3CL", "cjpCLx", "CjpCLx"})


def _book_slug_from_path(path: Path) -> Optional[str]:
    parts = path.parts
    if "v2" in parts:
        idx = parts.index("v2")
        if idx + 2 < len(parts):
            return parts[idx + 2]
    return None


def _chapter_from_filename(name: str) -> Optional[int]:
    import re
    m = re.search(r"-(\d+)\.txt$", name, re.IGNORECASE)
    return int(m.group(1)) if m else None


def classify_finding_for_line(
    book_slug: str,
    chapter_no: int,
    verse: int,
    line_text: str,
    cl_a_idx: int,
    cl_b_idx: int,
) -> dict:
    """Return classification dict for one Hpar finding."""
    try:
        vclauses = MC.get_verse_clauses(book_slug, chapter_no, verse)
    except Exception:
        return {"classification": "ERROR-MACULA", "rationale": "macula load failure"}

    # Walk all leaf clauses in the verse; identify the two that match the finding's heads
    leaves = [c for c in vclauses if _is_leaf_clause(c)]
    if cl_a_idx >= len(leaves) or cl_b_idx >= len(leaves):
        return {"classification": "ERROR-INDEX", "rationale": "clause index out of range"}
    cl_a = leaves[cl_a_idx]
    cl_b = leaves[cl_b_idx]

    rule_a = cl_a.wg_rule or ""
    rule_b = cl_b.wg_rule or ""

    # Quick-check via Constituent.is_relative_clause attribute.
    if cl_b.is_relative_clause or cl_b.ancestor_with(wg_class="relp") is not None:
        return {
            "classification": "SUBORDINATE-FP",
            "rationale": "cl_b is_relative_clause",
            "rule_a": rule_a, "rule_b": rule_b,
        }

    if rule_b in SUBORDINATE_RULES:
        return {
            "classification": "SUBORDINATE-FP",
            "rationale": f"cl_b.wg_rule={rule_b}",
            "rule_a": rule_a, "rule_b": rule_b,
        }

    if rule_a in COMPLEMENT_RULES:
        return {
            "classification": "COMPLEMENT-FP",
            "rationale": f"cl_a.wg_rule={rule_a} (matrix takes clausal complement)",
            "rule_a": rule_a, "rule_b": rule_b,
        }

    # Parent-wg_rule check: if both clauses share parent and parent has a
    # coordination rule, this is genuine parallelism.
    if cl_a.parent is not None and cl_a.parent is cl_b.parent:
        parent_rule = cl_a.parent.wg_rule or ""
        if parent_rule in COORD_RULES:
            return {
                "classification": "COORDINATE-TP",
                "rationale": f"shared parent.wg_rule={parent_rule}",
                "rule_a": rule_a, "rule_b": rule_b,
                "parent_rule": parent_rule,
            }

    # cl_a or cl_b's own wg_rule is a coordination tag (some coordinations are
    # encoded on the clause itself rather than the parent).
    if rule_a in COORD_RULES or rule_b in COORD_RULES:
        return {
            "classification": "COORDINATE-TP",
            "rationale": f"clause wg_rule in COORD_RULES (a={rule_a} b={rule_b})",
            "rule_a": rule_a, "rule_b": rule_b,
        }

    return {
        "classification": "AMBIGUOUS",
        "rationale": f"no closed-list match (a={rule_a} b={rule_b})",
        "rule_a": rule_a, "rule_b": rule_b,
    }


def scan_book(book_slug: str) -> list[dict]:
    """Run Hpar's per-line scan with classification on each finding."""
    book_dir = REPO_ROOT / "data" / "text-files"  / "v2" / "heb" / book_slug
    if not book_dir.is_dir():
        return []
    out: list[dict] = []
    for ch_file in sorted(book_dir.glob("*.txt")):
        chapter_no = _chapter_from_filename(ch_file.name)
        if chapter_no is None:
            continue
        try:
            results = scan_chapter(book_slug, chapter_no, ch_file)
            out.extend(results)
        except Exception as e:
            print(f"  ERR {ch_file.name}: {e}", file=sys.stderr)
    return out


def scan_chapter(book_slug: str, chapter_no: int, ch_file: Path) -> list[dict]:
    """Per-chapter scan: replicate Hpar's verse-loop, classify each finding."""
    text = ch_file.read_text(encoding="utf-8")
    lines = text.split("\n")

    # Group lines by verse (replicates the validator's verse-partition).
    import re
    VERSE_REF_RE = re.compile(r"^(\d+):(\d+)\s*$")
    cur_verse: Optional[int] = None
    verse_line_indices: dict[int, list[int]] = {}
    verse_line_texts: dict[int, list[str]] = {}
    for i, line in enumerate(lines):
        m = VERSE_REF_RE.match(line.strip())
        if m:
            cur_verse = int(m.group(2))
            continue
        if not line.strip():
            continue
        if cur_verse is None:
            continue
        verse_line_indices.setdefault(cur_verse, []).append(i)
        verse_line_texts.setdefault(cur_verse, []).append(line)

    out: list[dict] = []
    for verse, indices in verse_line_indices.items():
        try:
            vtokens = MC.get_verse_tokens(book_slug, chapter_no, verse)
            vclauses = MC.get_verse_clauses(book_slug, chapter_no, verse)
        except Exception:
            continue
        if not vtokens or not vclauses:
            continue

        # Leaves indexed for cl_a_idx / cl_b_idx mapping.
        leaves = [c for c in vclauses if _is_leaf_clause(c)]
        if not leaves:
            continue

        # Match v2/heb lines to verse-token slices (per-line greedy match).
        cursor = 0
        line_token_lists = []
        for ln in verse_line_texts[verse]:
            matched, next_cursor = MC.match_sense_line_tokens(vtokens, ln, cursor)
            line_token_lists.append(matched)
            cursor = next_cursor

        for line_tokens, line_text, file_line_no in zip(
            line_token_lists, verse_line_texts[verse], indices
        ):
            if len(line_tokens) < 4:
                continue
            clauses_here = _clauses_with_heads_in(vclauses, line_tokens)
            if len(clauses_here) < 2:
                continue
            heads = [_clause_head_verb(c) for c in clauses_here]
            if all(h is not None and h.is_wayyiqtol for h in heads):
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
                if (
                    head_a is not None and head_b is not None
                    and head_a.lemma and head_b.lemma
                    and head_a.lemma == head_b.lemma
                ):
                    continue
                # Classify via Macula constituent attributes (extended: walk
                # parent chain to find LCA's wg_rule, which encodes the
                # cross-clause relationship).
                rule_a = cl_a.wg_rule or ""
                rule_b = cl_b.wg_rule or ""

                # Walk up cl_a's ancestor chain to collect all ancestors (including self).
                a_ancestors = [cl_a]
                node = cl_a.parent
                while node is not None:
                    a_ancestors.append(node)
                    node = node.parent
                # Walk up cl_b's ancestor chain to find LCA.
                lca = None
                node = cl_b
                while node is not None:
                    if node in a_ancestors:
                        lca = node
                        break
                    node = node.parent
                lca_rule = (lca.wg_rule or "") if lca else ""
                lca_class = (lca.wg_class or "") if lca else ""

                # Decision tree (priority order):
                if cl_b.is_relative_clause or cl_b.ancestor_with(wg_class="relp") is not None:
                    classification = "SUBORDINATE-FP"
                    rationale = "cl_b is_relative_clause"
                elif rule_b in SUBORDINATE_RULES:
                    classification = "SUBORDINATE-FP"
                    rationale = f"cl_b.wg_rule={rule_b}"
                elif lca is cl_a or lca is cl_b:
                    # One clause is an ancestor of the other → strict subordination
                    classification = "SUBORDINATE-FP"
                    rationale = f"cl_{'a' if lca is cl_a else 'b'} is ancestor of cl_{'b' if lca is cl_a else 'a'}"
                elif rule_a in COMPLEMENT_RULES:
                    classification = "COMPLEMENT-FP"
                    rationale = f"cl_a.wg_rule={rule_a}"
                elif lca_rule in COMPLEMENT_RULES:
                    classification = "COMPLEMENT-FP"
                    rationale = f"LCA.wg_rule={lca_rule}"
                elif lca_rule in COORD_RULES:
                    classification = "COORDINATE-TP"
                    rationale = f"LCA.wg_rule={lca_rule}"
                elif rule_a in COORD_RULES or rule_b in COORD_RULES:
                    classification = "COORDINATE-TP"
                    rationale = f"clause wg_rule in COORD_RULES (a={rule_a} b={rule_b})"
                elif cl_a.parent is None and cl_b.parent is None:
                    # Both clauses are top-level siblings under the verse's
                    # Sentence wrapper (Macula doesn't expose Sentence as a
                    # Constituent; top-level wg children get parent=None).
                    # This is the canonical bicolon parallelism case — two
                    # independent clauses sharing only the verse as parent.
                    classification = "COORDINATE-TP"
                    rationale = "both top-level siblings under Sentence"
                elif lca_rule == "CLaCL":
                    # Common LCA is a clause-attached-to-clause structure.
                    # Less clear than coordination; bias toward subordinate
                    # since CLaCL is the auditor-named subordinate-attachment
                    # tag.
                    classification = "SUBORDINATE-FP"
                    rationale = f"LCA.wg_rule={lca_rule}"
                else:
                    classification = "AMBIGUOUS"
                    rationale = f"no match (a={rule_a} b={rule_b} lca={lca_rule!r})"
                out.append({
                    "book": book_slug,
                    "chapter": chapter_no,
                    "verse": verse,
                    "file_line": file_line_no + 1,
                    "head_a": (head_a.text if head_a else "?"),
                    "head_b": (head_b.text if head_b else "?"),
                    "rule_a": rule_a,
                    "rule_b": rule_b,
                    "classification": classification,
                    "rationale": rationale,
                })
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--book", help="Restrict to one book slug (e.g. 19-psalms)")
    ap.add_argument("--csv", action="store_true", help="Emit CSV to stdout")
    args = ap.parse_args()

    he_dir = REPO_ROOT / "data" / "text-files"  / "v2" / "heb"
    if args.book:
        books = [args.book]
    else:
        books = [d.name for d in sorted(he_dir.iterdir()) if d.is_dir()]

    all_results: list[dict] = []
    for book_slug in books:
        results = scan_book(book_slug)
        all_results.extend(results)

    if args.csv:
        import csv
        writer = csv.DictWriter(
            sys.stdout,
            fieldnames=["book", "chapter", "verse", "file_line", "head_a", "head_b",
                        "rule_a", "rule_b", "classification", "rationale"],
        )
        writer.writeheader()
        for r in all_results:
            writer.writerow(r)
        return

    counter = Counter(r["classification"] for r in all_results)
    print(f"Total Hpar findings classified: {len(all_results)}")
    print()
    print("By classification:")
    for cls, n in counter.most_common():
        pct = (n / len(all_results) * 100) if all_results else 0
        print(f"  {cls:20s} {n:5d}  ({pct:5.1f}%)")

    # Per-cluster breakdown
    print()
    print("By classification × cluster (sample):")
    cluster_map = {
        1: list(range(1, 6)),
        2: [6, 7, 9, 10, 11, 12],
        3: [23, 24, 26, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39],
        4: [8, 13, 14, 15, 16, 17, 21, 27],
        5: [18, 19, 20],
        6: [22, 25],  # SoS, Lam (whole-book cluster-6); ignore embedded-poetry chapters here
    }
    for cluster, books_in_cluster in cluster_map.items():
        cluster_results = [
            r for r in all_results
            if int(r["book"].split("-")[0]) in books_in_cluster
        ]
        if not cluster_results:
            continue
        cls_counter = Counter(r["classification"] for r in cluster_results)
        print(f"  Cluster {cluster}: {len(cluster_results)} findings")
        for cls in ("COORDINATE-TP", "AMBIGUOUS", "COMPLEMENT-FP", "SUBORDINATE-FP", "ERROR-MACULA"):
            n = cls_counter.get(cls, 0)
            if n:
                print(f"    {cls:20s} {n:5d}")


if __name__ == "__main__":
    main()
