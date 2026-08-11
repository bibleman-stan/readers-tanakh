#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_morphology_vs_tahot.py — Systematic FP/FN audit of morphology helpers
against the TAHOT morph-tag oracle.

For each helper in `5-machinery/validators/_shared/morphology.py` that classifies a single
token, this script compares the helper's output against what TAHOT (the
authoritative morphological annotation in `data/text-files/v0/morph/`) says
the token actually is. Disagreements are systematic bug classes.

The same pattern that exterminated the YIQTOL FP class on 2026-04-30
(459 proper nouns silently mis-classified as verbs) — generalized to every
classification helper. Each bug class found is a candidate for the next
extermination cycle: the rules that depend on the helper are SILENTLY BLOCKED
on every FP/FN until the helper agrees with the oracle.

Output:
  Per helper:
    FP count: helper said True, tag oracle said False  (over-fires)
    FN count: helper said False, tag oracle said True  (under-fires)
    Top 10 most-frequent FP/FN tokens with example forms

Helpers audited (single-token classification only; line-level helpers excluded):
  is_finite_verb_token  → tag oracle: head is V[stem][p/w/i/j/h/v/q] (finite verb)
  is_construct_head_token → tag oracle: head is N*c (construct state)
  is_do_marker_token    → tag oracle: head is To (object marker)
  is_bare_prep_token    → tag oracle: head is R (preposition)
  is_definite_adjective_token → tag oracle: head is A (adjective)
  is_numeral_token      → tag oracle: head is Ac* (cardinal) or Ao* (ordinal)
  is_bare_noun_token    → tag oracle: head is N (noun) AND not finite verb / DO / prep / numeral

Skel-side caveats:
  - Helpers operate on prosodic-words (whitespace-split, may contain maqqef-
    joined orthographic words). Tag oracle uses LAST tag for "head" classification
    (the rightmost morpheme determines the syntactic class).
  - Tokens whose morph tag is `[—]` (intra-row maqqef placeholder) are skipped.
  - Tokens with empty/missing morph tags are skipped (rare).

Usage:
    PYTHONIOENCODING=utf-8 py -3 5-machinery/scripts/audit_morphology_vs_tahot.py
    PYTHONIOENCODING=utf-8 py -3 5-machinery/scripts/audit_morphology_vs_tahot.py --verbose
    PYTHONIOENCODING=utf-8 py -3 5-machinery/scripts/audit_morphology_vs_tahot.py --helper is_finite_verb_token
    PYTHONIOENCODING=utf-8 py -3 5-machinery/scripts/audit_morphology_vs_tahot.py --emit-fp-list <helper>
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable

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
sys.path.insert(0, str(ROOT))

from validators._shared import morph_tags as MT  # noqa: E402
from validators._shared import morphology as M  # noqa: E402

V0_PROSE = ROOT / "data" / "text-files" / "v0" / "prose"
V0_MORPH = ROOT / "data" / "text-files" / "v0" / "morph"

VERSE_RE = re.compile(r"^(\d+):(\d+)\s*$")
PIPE_SEP = " | "


# ──────────────────────────────────────────────────────────────────────
# Tag oracles — ground truth from TAHOT for each helper
# ──────────────────────────────────────────────────────────────────────


def oracle_is_finite_verb(tag: str) -> bool:
    return MT.is_finite_verb(tag)


def oracle_is_construct_head(tag: str) -> bool:
    return MT.is_construct_state(tag)


def oracle_is_do_marker(tag: str) -> bool:
    """TAHOT 'To' = direct object marker (אֵת, also as bound prefix in compounds).

    Receives the FIRST ortho's tag (use_first=True in HELPERS). For maqqef
    compounds (אֶת־X) the first tag is HTo — the marker's own entry. For bare
    אֵת the first tag is also HTo. For וְאֵת the chain is [C, To].

    Excludes `R/To` (`מֵאֵת` "from-with") and `R/To/Sp*` (`מֵאוֹתוֹ`):
    the leading R prefix makes these compound PREPOSITIONS that take a
    complement the same way `מֵעַל` does — not DO-markers. The R-exclusion
    is mirrored in `is_do_marker_token`'s tag-driven path.
    """
    chain = MT.morpheme_chain(tag)
    return "To" in chain and "R" not in chain


def oracle_is_bare_prep(tag: str) -> bool:
    """Tag oracle for is_bare_prep_token. Chain must end in `R`
    (preposition) AND contain no `Sp*` (pronominal suffix) AND contain
    no `Td/Td*` (definite article).

    Admits monomorphemic free preps (`["R"]`), vav-coord preps (`[C/c, R]`),
    and compound R+R preps like `מֵעַל` (`["R", "R"]`) — all equally
    stranded when no following complement appears in the token. Excludes
    `R/Nc*` compound preps (`לִפְנֵי`, `אַחֲרֵי`) whose construct head
    is the complement, and `R/Sp*` / `R/Nc*/Sp*` forms whose object is
    the internal pronominal suffix.
    """
    chain = MT.morpheme_chain(tag)
    if not chain or chain[-1] != "R":
        return False
    if any(m.startswith("Sp") for m in chain):
        return False
    if any(m == "Td" or m.startswith("Td") for m in chain):
        return False
    return True


def oracle_is_definite_adjective(tag: str) -> bool:
    """TAHOT 'A' = adjective. Definite adjective = article-prefix + adjective head."""
    chain = MT.morpheme_chain(tag)
    if not chain:
        return False
    head = chain[-1]
    if not head.startswith("A"):
        return False
    # Definite = has Td (definite article) prefix in the chain
    return any(m == "Td" or m.startswith("Td") for m in chain[:-1])


def oracle_is_numeral(tag: str) -> bool:
    """TAHOT 'Ac' = cardinal number, 'Ao' = ordinal. Both are adjective-class."""
    head = MT.head_morpheme(tag)
    return head.startswith("Ac") or head.startswith("Ao")


def oracle_is_bare_noun(tag: str) -> bool:
    """Tag-oracle for is_bare_noun_token. Mirrors the helper's intent:

    - Head morpheme is N* (noun, common or proper)
    - NOT preceded by a bound-prep prefix (chain[0] == "R") — those are
      preposition + noun fused words (בְּבֵית, לְמֶלֶךְ, etc.) excluded by
      the helper's BOUND_PREP_PREFIXES check.
    - NOT a conjunction-only prefix with a non-noun head (C or c alone).
    - Definite-article prefixed nouns (Td/N*) are still bare nouns — the
      article does not turn a noun into a prep or verb.
    - Common nouns AND proper nouns both qualify.
    """
    chain = MT.morpheme_chain(tag)
    if not chain:
        return False
    head = chain[-1]
    if not head.startswith("N"):
        return False
    # Exclude bound-prep + noun compounds (first morpheme is R = preposition)
    if chain[0] == "R":
        return False
    return True


# ──────────────────────────────────────────────────────────────────────
# Helper registry — (name, helper_fn, oracle_fn)
# ──────────────────────────────────────────────────────────────────────

HELPERS: list[tuple[str, Callable[[str], bool], Callable[[str], bool], bool]] = [
    # (name, helper_fn, oracle_fn, use_first_tag)
    # use_first_tag=True: oracle receives the FIRST ortho's tag (leading morpheme)
    # use_first_tag=False: oracle receives the LAST ortho's tag (syntactic head)
    ("is_finite_verb_token",       M.is_finite_verb_token,        oracle_is_finite_verb,        False),
    ("is_construct_head_token",    M.is_construct_head_token,     oracle_is_construct_head,     False),
    ("is_do_marker_token",         M.is_do_marker_token,          oracle_is_do_marker,          True),
    ("is_bare_prep_token",         M.is_bare_prep_token,          oracle_is_bare_prep,          False),
    ("is_definite_adjective_token", M.is_definite_adjective_token, oracle_is_definite_adjective, False),
    ("is_numeral_token",           M.is_numeral_token,            oracle_is_numeral,            False),
    ("is_bare_noun_token",         M.is_bare_noun_token,          oracle_is_bare_noun,          False),
]


# ──────────────────────────────────────────────────────────────────────
# Token/tag iteration
# ──────────────────────────────────────────────────────────────────────


def _zip_verses(prose_text: str, morph_text: str):
    def parse(text: str):
        out = {}
        cur = None
        for line in text.splitlines():
            s = line.strip()
            if not s:
                cur = None
                continue
            if VERSE_RE.match(s):
                cur = s
                continue
            if cur is not None:
                out[cur] = s
                cur = None
        return out
    he = parse(prose_text)
    mo = parse(morph_text)
    for ref in he:
        if ref in mo:
            yield he[ref], mo[ref]


def iter_corpus_tokens():
    """Yield (tok, first_tag, head_tag) for every token in the corpus.

    first_tag: FIRST non-placeholder tag in the maqqef group (the head
               orthographic word — e.g. אֵת in אֶת־הָאָרֶץ).
    head_tag:  LAST non-placeholder tag in the maqqef group (the syntactic
               head morpheme of the compound — the complement).

    Oracles that classify by the leading morpheme (DO-marker, bare-prep) use
    first_tag; oracles that classify by the governing head use head_tag.
    """
    for book_dir in sorted(V0_PROSE.iterdir()):
        if not book_dir.is_dir():
            continue
        for prose_file in sorted(book_dir.glob("*.txt")):
            morph_file = V0_MORPH / book_dir.name / prose_file.name
            if not morph_file.exists():
                continue
            prose_text = prose_file.read_text(encoding="utf-8")
            morph_text = morph_file.read_text(encoding="utf-8")
            for he_content, morph_content in _zip_verses(prose_text, morph_text):
                he_tokens = he_content.split()
                morph_tags = [t.strip() for t in morph_content.split(PIPE_SEP)]
                ortho_idx = 0
                for tok in he_tokens:
                    sub_count = len(tok.split(M.MAQQEF))
                    end = ortho_idx + sub_count
                    if end > len(morph_tags):
                        ortho_idx = end
                        continue
                    sub = morph_tags[ortho_idx:end]
                    # first_tag = FIRST non-placeholder tag in the group
                    first_tag = None
                    for t in sub:
                        if t and t != "[—]":
                            first_tag = t
                            break
                    # head_tag = LAST non-placeholder tag in the group
                    head_tag = None
                    for t in sub[::-1]:
                        if t and t != "[—]":
                            head_tag = t
                            break
                    ortho_idx = end
                    if head_tag is None:
                        continue
                    yield (tok, first_tag or head_tag, head_tag)


# ──────────────────────────────────────────────────────────────────────
# Audit
# ──────────────────────────────────────────────────────────────────────


def audit_helpers(helper_filter: str | None = None):
    fp_counts: dict[str, Counter[str]] = defaultdict(Counter)  # helper → skel → count
    fn_counts: dict[str, Counter[str]] = defaultdict(Counter)
    fp_examples: dict[str, dict[str, str]] = defaultdict(dict)
    fn_examples: dict[str, dict[str, str]] = defaultdict(dict)
    total_tokens = 0

    for tok, first_tag, head_tag in iter_corpus_tokens():
        total_tokens += 1
        skel = M.skel(tok)
        if not skel:
            continue
        for name, helper_fn, oracle_fn, use_first in HELPERS:
            if helper_filter and name != helper_filter:
                continue
            try:
                helper_result = helper_fn(tok)
            except Exception:
                continue
            oracle_tag = first_tag if use_first else head_tag
            try:
                oracle_result = oracle_fn(oracle_tag)
            except Exception:
                continue
            if helper_result == oracle_result:
                continue
            if helper_result and not oracle_result:
                fp_counts[name][skel] += 1
                if skel not in fp_examples[name]:
                    fp_examples[name][skel] = tok
            else:
                fn_counts[name][skel] += 1
                if skel not in fn_examples[name]:
                    fn_examples[name][skel] = tok

    return total_tokens, fp_counts, fn_counts, fp_examples, fn_examples


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--helper", default=None,
                    help="Audit only this helper (e.g. is_finite_verb_token)")
    ap.add_argument("--verbose", action="store_true",
                    help="Show full disagreement examples")
    ap.add_argument("--top", type=int, default=15,
                    help="Top N FP/FN skels per helper to show (default 15)")
    ap.add_argument("--emit-fp-list", default=None, metavar="HELPER",
                    help="Emit just the FP skel list for one helper (frequency-sorted)")
    args = ap.parse_args()

    if not V0_MORPH.exists():
        sys.exit(f"ERROR: {V0_MORPH} not found. Run ingest_tahot.py --all-books first.")

    total, fp_counts, fn_counts, fp_examples, fn_examples = audit_helpers(args.helper)

    if args.emit_fp_list:
        h = args.emit_fp_list
        for skel, cnt in fp_counts[h].most_common():
            print(f'{skel}\t{cnt}\t{fp_examples[h].get(skel, "?")}')
        return 0

    print("=" * 78)
    print("Morphology helpers vs. TAHOT tag oracle — systematic audit")
    print("=" * 78)
    print(f"Tokens scanned: {total:,}")
    print()

    # Rank helpers by total disagreements
    ranked = []
    for name, _, _, _ in HELPERS:
        if args.helper and name != args.helper:
            continue
        fp_total = sum(fp_counts[name].values())
        fn_total = sum(fn_counts[name].values())
        fp_unique = len(fp_counts[name])
        fn_unique = len(fn_counts[name])
        ranked.append((name, fp_total, fn_total, fp_unique, fn_unique))
    ranked.sort(key=lambda r: -(r[1] + r[2]))

    print(f"{'Helper':<35} {'FP-total':>10} {'FN-total':>10} {'FP-skels':>10} {'FN-skels':>10}")
    print("-" * 78)
    for name, fp, fn, fpu, fnu in ranked:
        print(f"{name:<35} {fp:>10,} {fn:>10,} {fpu:>10,} {fnu:>10,}")
    print()

    for name, fp, fn, fpu, fnu in ranked:
        if fp == 0 and fn == 0:
            continue
        print()
        print("─" * 78)
        print(f"{name}")
        print("─" * 78)
        if fp:
            print(f"  FALSE POSITIVES ({fp:,} tokens, {fpu:,} unique skels)")
            print(f"  helper said True, TAHOT tag says False")
            for skel, cnt in fp_counts[name].most_common(args.top):
                ex = fp_examples[name].get(skel, "?")
                print(f"    {skel}: {cnt:,}  e.g. {ex}")
            if fpu > args.top:
                print(f"    ... +{fpu - args.top:,} more skels")
            print()
        if fn:
            print(f"  FALSE NEGATIVES ({fn:,} tokens, {fnu:,} unique skels)")
            print(f"  helper said False, TAHOT tag says True")
            for skel, cnt in fn_counts[name].most_common(args.top):
                ex = fn_examples[name].get(skel, "?")
                print(f"    {skel}: {cnt:,}  e.g. {ex}")
            if fnu > args.top:
                print(f"    ... +{fnu - args.top:,} more skels")
            print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
