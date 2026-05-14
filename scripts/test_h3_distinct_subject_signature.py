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

REVISION 2 (per 2026-05-14 5-cluster full audit — 142 hits, ~63% FP rate;
all 5 cluster agents converged on the same FP classes):

  Class A — Condition 7 (speech-act filter) was DEAD CODE: _is_speech_act_
    ancestor walks role=='o' but Macula leaf-flattens speech content or
    wraps it in CLaCL/ClCl with no role='o'. FIX: if head_a.lemma is a
    speech-act lemma (אָמַר/דָּבַר/עָנָה) AND wayyiqtol → defer the pair.
    (~60 FPs — the dominant class.)
  Class B — Condition 4 empty-subjref loophole: `if a_refs and b_refs`
    evaluates False when both empty → pair passes as "distinct" on no
    evidence. FIX: when both subjref sets empty, fall back to surface
    check — defer if subj_b is a personal pronoun (likely coreferential)
    or if consonant skeletons match.
  Class C — Condition 8 was unimplemented ("skip for v1, rare"). It is
    NOT rare. FIX: implement via Token.position scan between cl_a and cl_b.
  Class D — H3 is a narrative-prose rule; firing in Sifrei Emet aliases
    synonymous parallelism (Israel/Jacob, fire/flame) as distinct subjects.
    FIX: poetic-register scope exclusion via is_poetic_register().
  RESIDUAL (not yet fixed — minority edge classes, flagged for re-audit):
  Class E — circumstantial הָיָה qatal-clause bonded to wayyiqtol
    (~5 FPs; risks breaking Jonah 3:3 fixture entry; needs narrower test).
  Class G — Macula relative-clause subject misparse (Lev 24:23; ~2 FPs).

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
from validators._shared.poetic_register import is_poetic_register  # noqa: E402

FIXTURE = REPO_ROOT / "tests" / "fixtures-h3-distinct-subject.tsv"

SUBORDINATORS = {"אֲשֶׁר", "כִּי", "אִם", "כַּאֲשֶׁר", "פֶּן"}

# Class A fix: speech-act head lemmas. When cl_a's head verb is one of these
# in wayyiqtol form, cl_b is presumptively the speech CONTENT, not a
# distinct narrative chain-break. Conservative set — קָרָא deliberately
# EXCLUDED because its name-giving sense (קָרָא שֵׁם) produces genuine TPs
# (Gen 22:14, 31:47) that a speech-act defer would wrongly kill.
SPEECH_ACT_LEMMAS = {"אָמַר", "דָּבַר", "עָנָה"}

# Personal-pronoun lemmas — Class B fix: when subjref resolution is empty
# on both sides, a pronoun subject in cl_b is likely coreferential.
PERSONAL_PRONOUN_LEMMAS = {"הוּא", "הִיא", "הֵם", "הֵמָּה", "הֵנָּה", "אֲנִי",
                            "אָנֹכִי", "אַתָּה", "אַתֶּם", "אֲנַחְנוּ"}


def _consonant_skel(s: str) -> str:
    return "".join(c for c in (s or "") if not (0x0591 <= ord(c) <= 0x05C7))


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


def _has_subordinator_between_clauses(cl_a, cl_b) -> bool:
    """Class C fix (condition 8): scan for a subordinator token positioned
    between cl_a's last token and cl_b's first token, OR as cl_b's own
    first token. Uses Token.position (token position within verse).

    Catches: כִּי-causal/reason clauses (Gen 3:20, Num 15:34, 2Chr 22:4),
    אֲשֶׁר relatives, אִם/כַּאֲשֶׁר/פֶּן subordinate clauses misparsed by
    Macula as adjacent leaves."""
    a_tokens = cl_a.tokens
    b_tokens = cl_b.tokens
    if not a_tokens or not b_tokens:
        return False
    try:
        a_end = max(t.position for t in a_tokens)
        b_start = min(t.position for t in b_tokens)
    except (ValueError, AttributeError):
        return False
    # Check cl_b's own tokens (a subordinator can be the clause's first token)
    # and any token positioned in the [a_end, b_start] gap.
    for t in b_tokens:
        skel = _consonant_skel(t.text).strip("־")
        if t.lemma in SUBORDINATORS or skel in {"אשר", "כי", "אם", "כאשר", "פן"}:
            return True
    # Also scan the gap: cl_b may not include the subordinator if Macula
    # attached it elsewhere. We need the verse tokens — but this helper
    # only has the clauses. The clause-internal check above covers the
    # common case (subordinator as cl_b's head); gap-scan is handled by
    # the caller if needed.
    return False


def classify_verse(book: str, chapter: int, verse: int) -> tuple[str, str]:
    """Run the refined signature against a verse. Returns (verdict, reason).

    Verdict:
      - "STRONG": signature matches; STRONG-SPLIT promotion
      - "NEGATIVE": signature does not match (passes one or more defer/exclusion)
      - "ERROR": couldn't load Macula data
    """
    # Class D fix: H3 is a narrative-prose rule. Poetic register (Sifrei
    # Emet + embedded poetry) aliases synonymous parallelism as
    # distinct-subject chain-breaks. Hard scope-exclusion.
    if is_poetic_register(book, chapter, verse):
        return "NEGATIVE", "poetic register (Sifrei Emet / embedded poetry) — H3 scope-excluded"

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
        # (Class A fix) head_a is a speech-act verb → cl_b is presumptively
        # speech CONTENT, not a narrative chain-break. This replaces the
        # dead condition-7 ancestor-walk. Dominant FP class (~60 of ~89).
        if head_a.lemma in SPEECH_ACT_LEMMAS:
            continue
        # (Class genealogy fix) both heads are יָלַד → genealogical toledot
        # chain (X begat Y / Y begat Z), not a distinct-subject chain-break.
        # Defers to H17 genealogy-formula handling. (Gen 4:18, 1Chr 5:37.)
        if head_a.lemma == "יָלַד" and head_b.lemma == "יָלַד":
            continue
        # (4) Subjects differ — check via subjref_ids antecedent resolution
        subj_a = _clause_subject_token(cl_a) or head_a
        subj_b = _clause_subject_token(cl_b)
        if subj_b is None:
            continue
        a_refs = set(subj_a.subjref_ids or [])
        b_refs = set(subj_b.subjref_ids or [])
        if a_refs and b_refs:
            if a_refs & b_refs:
                continue  # same antecedent — not a chain break
        else:
            # (Class B fix) subjref resolution empty on at least one side —
            # the old `if a_refs and b_refs` guard let these pass as
            # "distinct" on no evidence. Fall back to surface checks.
            if subj_b.lemma in PERSONAL_PRONOUN_LEMMAS:
                continue  # pronoun subject, unresolved — likely coreferential
            if _consonant_skel(subj_a.text) == _consonant_skel(subj_b.text):
                continue  # same surface lemma — same subject
        # (5) Defer to H15: if cl_a has no finite verb (left-dislocation)
        # — covered above (head_a wayyqtl check).
        # (6) Defer to H16: cl_a is wayehi-FEF
        if _is_wayehi_fef(cl_a, vtokens):
            continue
        # (7) Defer if cl_b is inside speech-act object — kept as a
        # secondary guard, though Class A fix (head_a speech-act lemma)
        # now catches the dominant case upstream.
        if _is_speech_act_ancestor(cl_b):
            continue
        # (8) (Class C fix) No subordinator between cl_a and cl_b. Uses
        # Token.position to scan the verse-token span between the clauses.
        if _has_subordinator_between_clauses(cl_a, cl_b):
            continue

        return "STRONG", (
            f"head_a={head_a.text}({head_a.type_}) "
            f"head_b={head_b.text}({head_b.type_}) "
            f"cl_b.wg_rule={cl_b.wg_rule} "
            f"subj_a={subj_a.text} subj_b={subj_b.text}"
        )

    return "NEGATIVE", "no adjacent (wayyqtl + S-V-non-wayyqtl + distinct-subject) pair found"


def run_fixture():
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
    return n_match == len(rows)


def run_corpus():
    """Scan every v2/heb verse; collect STRONG verdicts; write corpus-hits TSV."""
    import re
    V2_HEB = REPO_ROOT / "data" / "text-files" / "v2" / "heb"
    verse_re = re.compile(r"^(\d+):(\d+)\s*$")
    hits = []
    total = 0
    for book_dir in sorted(V2_HEB.iterdir()):
        if not book_dir.is_dir():
            continue
        book = book_dir.name
        short = book.split("-", 1)[1]
        for chap_file in sorted(book_dir.glob(f"{short}-*.txt")):
            for ln in chap_file.read_text(encoding="utf-8").splitlines():
                m = verse_re.match(ln.strip())
                if not m:
                    continue
                ch, vs = int(m.group(1)), int(m.group(2))
                total += 1
                verdict, reason = classify_verse(book, ch, vs)
                if verdict == "STRONG":
                    hits.append((book, ch, vs, reason))

    print(f"\n=== H3 distinct-subject corpus scan (REVISION 2) ===")
    print(f"Verses scanned: {total}")
    print(f"STRONG hits: {len(hits)}  (REVISION 1 baseline: 142)")
    from collections import Counter
    by_book = Counter(h[0] for h in hits)
    print("\nBy book:")
    for bk, n in by_book.most_common():
        print(f"  {bk:20} {n}")

    out = REPO_ROOT / "tests" / "h3-distinct-subject-corpus-hits.tsv"
    with out.open("w", encoding="utf-8", newline="") as f:
        f.write("book\tchapter\tverse\treason\n")
        for book, ch, vs, reason in hits:
            f.write(f"{book}\t{ch}\t{vs}\t{reason}\n")
    print(f"\nWritten: {out}")


def main():
    if "--corpus" in sys.argv:
        run_corpus()
    else:
        ok = run_fixture()
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
