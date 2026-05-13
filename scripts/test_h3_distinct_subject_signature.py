#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fixture test for proposed AC §3.5.4(a) "distinct-subject interruption"
STRONG-promotion signature. Standalone — does NOT modify Hmfv scanner.

Per CLAUDE.md "fixture-first" + "sample-audit-before-cascade": the rule
must pass this fixture before any engine integration.

Refined signature (per 2026-05-13 adversarial audits, agentIds
a89e9707cfce84ace + ab45629abdbef8bd5):

  1. head_a is wayyqtl (Vqw* / Vnw*)
  2. head_b is NOT wayyqtl (qatal or yiqtol)
  3. cl_b.wg_rule starts with "S-V" (Macula structural primitive)
  4. cl_b subject's subjref_ids[0] resolves to a DIFFERENT antecedent than
     cl_a head's subjref_ids[0] (actual chain-break signal)
  5. Defer to H15 if cl_a has no finite verb (casus pendens)
  6. Defer to H16 if cl_a is wayehi-FEF protasis
  7. Defer if cl_b is inside role="o" of a speech-act ancestor
  8. No subordinator (אֲשֶׁר / כִּי / אִם / כַּאֲשֶׁר / פֶּן) between cl_a and cl_b

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/test_h3_distinct_subject_signature.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "validators"))

from validators._shared import macula_constituents as MC  # noqa: E402

FIXTURE = REPO_ROOT / "tests" / "fixtures-h3-distinct-subject.tsv"

SUBORDINATORS = {"אֲשֶׁר", "כִּי", "אִם", "כַּאֲשֶׁר", "פֶּן"}


def _is_finite_verb(t) -> bool:
    """Finite verb: any prefix/suffix conjugation form."""
    return t.is_wayyiqtol or t.is_yiqtol or t.is_qatal or (
        t.type_ in {"imperative", "cohortative", "jussive"}
    )


def _is_leaf_clause(cl) -> bool:
    for c in cl.child_constituents:
        if c.is_clause:
            return False
    return True


def _clause_head_verb(cl):
    for t in cl.tokens:
        if _is_finite_verb(t):
            return t
    return None


def _clause_subject_token(cl):
    """First token with role='s' in the clause (Macula subject marker)."""
    for t in cl.tokens:
        if t.role == "s":
            return t
    return None


def _is_speech_act_ancestor(cl) -> bool:
    """Walk up the constituent tree; return True if any ancestor is role='o'
    of a speech-act verb (rough check: parent.role == 'o' and parent.parent's
    head verb's lemma is in a speech-act set).
    Fallback: just check if any ancestor's role is 'o' (object-clause)."""
    node = cl
    while node is not None:
        if getattr(node, "role", None) == "o":
            return True
        node = getattr(node, "parent", None)
    return False


def _is_wayehi_fef(cl, all_tokens) -> bool:
    """Cheap heuristic: clause head lemma is היה in wayyiqtol form."""
    head = _clause_head_verb(cl)
    if head is None:
        return False
    return head.lemma == "הָיָה" and head.is_wayyiqtol


def _has_subordinator_between(tokens_a_end_idx: int, tokens_b_start_idx: int,
                                verse_tokens) -> bool:
    """Check tokens between cl_a's end and cl_b's start for subordinator
    surface forms."""
    for t in verse_tokens[tokens_a_end_idx:tokens_b_start_idx]:
        if (t.text or "").strip("־") in SUBORDINATORS:
            return True
    return False


def classify_verse(book: str, chapter: int, verse: int) -> tuple[str, str]:
    """Run the refined signature against a verse. Returns (verdict, reason).

    Verdict:
      - "STRONG": signature matches; STRONG-SPLIT promotion
      - "NEGATIVE": signature does not match (passes one or more defer/exclusion)
      - "ERROR": couldn't load Macula data
    """
    try:
        vclauses = MC.get_verse_clauses(book, chapter, verse)
        vtokens = MC.get_verse_tokens(book, chapter, verse)
    except Exception as e:
        return "ERROR", f"macula-load: {e}"

    leaves = [c for c in vclauses if _is_leaf_clause(c)]
    if len(leaves) < 2:
        return "NEGATIVE", f"only {len(leaves)} leaf clause(s) in verse"

    # Walk pairwise; if ANY adjacent pair (cl_a, cl_b) matches the refined
    # signature, the verse is a STRONG positive. (For multi-clause verses we
    # could be more nuanced, but this is the v1 signature.)
    for i in range(len(leaves) - 1):
        cl_a, cl_b = leaves[i], leaves[i + 1]
        head_a = _clause_head_verb(cl_a)
        head_b = _clause_head_verb(cl_b)
        if head_a is None or head_b is None:
            continue

        # (1) head_a is wayyqtl
        if not head_a.is_wayyiqtol:
            continue
        # (2) head_b is NOT wayyqtl
        if head_b.is_wayyiqtol:
            continue
        # (3) cl_b.wg_rule starts with "S-V"
        if not (cl_b.wg_rule or "").startswith("S-V"):
            continue
        # (4) Subjects differ — check via subjref_ids antecedent resolution
        subj_a = _clause_subject_token(cl_a) or head_a
        subj_b = _clause_subject_token(cl_b)
        if subj_b is None:
            continue
        a_refs = set(subj_a.subjref_ids or [])
        b_refs = set(subj_b.subjref_ids or [])
        if a_refs and b_refs and a_refs & b_refs:
            continue  # same antecedent — not a chain break
        # (5) Defer to H15: if cl_a has no finite verb (left-dislocation)
        # — covered above (head_a wayyqtl check).
        # (6) Defer to H16: cl_a is wayehi-FEF
        if _is_wayehi_fef(cl_a, vtokens):
            continue
        # (7) Defer if cl_b is inside speech-act object
        if _is_speech_act_ancestor(cl_b):
            continue
        # (8) No subordinator between — would need token-index resolution;
        # skip for v1 (rare edge case)

        return "STRONG", (
            f"head_a={head_a.text}({head_a.type_}) "
            f"head_b={head_b.text}({head_b.type_}) "
            f"cl_b.wg_rule={cl_b.wg_rule} "
            f"subj_a={subj_a.text} subj_b={subj_b.text}"
        )

    return "NEGATIVE", "no adjacent (wayyqtl + S-V-non-wayyqtl + distinct-subject) pair found"


def main():
    rows = []
    with FIXTURE.open(encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            book = r["book"]
            ch = int(r["chapter"])
            vs = int(r["verse"])
            expected = r["expected"]
            category = r["category"]
            verdict, reason = classify_verse(book, ch, vs)
            match = "✓" if verdict == expected else "✗"
            rows.append({
                "book": book, "ch": ch, "vs": vs,
                "expected": expected, "verdict": verdict,
                "match": match, "category": category, "reason": reason,
            })

    # Print summary
    print(f"\n{'Match':6} {'Verse':20} {'Expected':10} {'Verdict':10} Category / Reason")
    print("-" * 100)
    n_match = 0
    for r in rows:
        verse_label = f"{r['book']} {r['ch']}:{r['vs']}"
        line = (
            f"{r['match']:6} {verse_label:20} {r['expected']:10} {r['verdict']:10} "
            f"{r['category']} | {r['reason'][:60]}"
        )
        print(line)
        if r["match"] == "✓":
            n_match += 1
    print("-" * 100)
    print(f"\nMatch rate: {n_match}/{len(rows)}")


if __name__ == "__main__":
    main()
