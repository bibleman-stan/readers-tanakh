#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scan_multi_finite_verb_line.py — corpus-wide detector for the Gen-1:3 class.

Class definition: a single v2/he cola containing 2+ independent finite-verb
clauses where no merge-override (M1 bonded-pair / M2 verb-object clause-nucleus
/ M3 bare-governor / M4 fragmented atomic-thought / formula integrity) justifies
the merge. Per the canon's generative principle (framework.md §1.1, canon §1):
each proposition splits by default unless syntax forbids.

Motivating exemplar (fixed in commit 123747499):
  Gen 1:3 line 2:  יְהִ֣י א֑וֹר וַֽיְהִי־אֽוֹר׃
       jussive (divine command)  +  wayyiqtol (narrative fulfillment)
       — two distinct propositions, no override applies.

Engine: TAHOT morph tags + Macula lowfat constituent tree (same primitives
as validators/colometry/validate_parallel_clause_split.py — non-parallel
sibling class).

Suppressors implemented (audited 2026-05-12):
  S1 all-wayyiqtol       — defer to S4 spec (s4_multi_wayyiqtol_clause_split)
  S2 complement clause   — cl_a.wg_rule in {V2CL, Np2CL}; cl_b is matrix's
                           clausal complement (FP-4 in audit)
  S3 relative clause     — cl_b.is_relative_clause OR אֲשֶׁר/דִּי/שֶׁ-
                           token between the two finite-verb heads (FP-5)
  S4 discourse-formula   — first verb is a הָיָה discourse-formula opener
                           (וַיְהִי / וְהָיָה / וַתְהִי / וִיהִי / וְהָיוּ) (FP-12)
  S5 cohortative pair    — both verbs are cohortative (aspect h) (FP-7)
  S6 imperative pair     — both verbs are imperative (aspect v) (FP-8)
  S7 negation pair       — both verbs are preceded by לא/אל (FP-6)

Output: data/syntax-reference/multi-finite-verb-candidates.tsv
Columns: book, chapter, verse, line_idx, hebrew_line, kjv_line, severity,
         suppressors_passed, head1_lemma, head1_aspect, head2_lemma, head2_aspect

Severity assignment:
  STRONG-SPLIT-CANDIDATE — passes all suppressors AND both clauses are
                            top-level coordinations (no FP-class fired)
  REVIEW-REQUIRED        — passes mechanical suppressors but the merge
                            could still be M1 (bonded-pair, e.g. cognate
                            verbs) or M3/M4 (per-verse atomic-thought
                            judgment); editor confirms

Usage:
  PYTHONIOENCODING=utf-8 py -3 scripts/scan_multi_finite_verb_line.py
  PYTHONIOENCODING=utf-8 py -3 scripts/scan_multi_finite_verb_line.py --book 01-genesis
  PYTHONIOENCODING=utf-8 py -3 scripts/scan_multi_finite_verb_line.py --severity STRONG-SPLIT-CANDIDATE
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from validators._shared import macula_constituents as MC

try:
    from validators._shared.hendiadys_lemma_pairs import BONDED_LEMMA_PAIRS
except ImportError:
    BONDED_LEMMA_PAIRS = frozenset()

# Reuse the cross-clause structural relationship rules from Hpar.
_COMPLEMENT_RULES = frozenset({"V2CL", "Np2CL"})
_SUBORDINATE_RULES = frozenset({"CLaCL", "relCL"})

# Discourse-formula heads (היה-family openers; Hpar's _DISCOURSE_FORMULA_SKELS).
_DISCOURSE_FORMULA_SKELS = frozenset({
    "ויהי", "והיה", "ויהיו", "ותהי", "והיו", "ויהיה",
})

_NEGATION_SKELS = frozenset({"לא", "אל"})
_RELATIVIZER_SKELS = frozenset({"אשר", "די"})

# Speech-act verb lemmas (per audit FP-3): when the first finite verb is a
# speech-act lemma followed by a second finite verb that's the speech content
# (typically imperative or jussive in direct discourse), the merge is J3
# speech-act announcement framing, not a generative-principle violation.
_SPEECH_ACT_LEMMAS = frozenset({
    "אָמַר", "דָּבַר", "עָנָה", "צִוָּה", "קָרָא", "שָׁאַל", "הִגִּיד",
})

VERSE_REF_RE = re.compile(r"^(\d+):(\d+)\s*$")


def _is_finite_verb(t: MC.Token) -> bool:
    morph = (t._morph_tag or "").upper()
    if not morph or morph[0] != "V" or len(morph) < 3:
        return False
    return morph[2] in ("Q", "W", "I", "V", "O", "J", "H", "U")


def _is_wayyiqtol(t: MC.Token) -> bool:
    morph = (t._morph_tag or "").upper()
    return bool(morph and morph[0] == "V" and len(morph) >= 3 and morph[2] == "W")


def _verb_aspect(t: MC.Token) -> str:
    morph = (t._morph_tag or "").upper()
    if not morph or morph[0] != "V" or len(morph) < 3:
        return ""
    return morph[2]


def _pw_count(tokens) -> int:
    """Count prosodic words by walking each token's `after` field; whitespace
    in `after` ends a prosodic word. Maqqef-bonded morphemes have no whitespace
    in after → bonded into one pw. Same algorithm as Hpar's _pw_count."""
    if not tokens:
        return 0
    pw = 1
    for i in range(1, len(tokens)):
        prev_after = (getattr(tokens[i - 1], "after", "") or "")
        if any(c.isspace() for c in prev_after):
            pw += 1
    return pw


def _is_leaf_clause(cl: MC.Constituent) -> bool:
    """A leaf clause has no descendant Constituents that are themselves clauses."""
    for c in cl.child_constituents:
        if c.is_clause:
            return False
        for gc in c.child_constituents:
            if gc.is_clause:
                return False
    return True


def _clause_head_verb(cl: MC.Constituent) -> MC.Token | None:
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


def _has_negation_before(cl: MC.Constituent, head_id: int) -> bool:
    for t in cl.tokens:
        if id(t) == head_id:
            return False
        if t.consonant_skel in _NEGATION_SKELS:
            return True
    return False


def _suppressor_cascade(line_tokens, clauses) -> tuple[str, list[str]]:
    """Apply suppressors; return (severity, suppressor-trace).
    Severity: SUPPRESSED if any FP class fires; otherwise STRONG-SPLIT-CANDIDATE
    (clean class) or REVIEW-REQUIRED (residual ambiguity).
    """
    if len(clauses) < 2:
        return "SUPPRESSED", ["fewer-than-2-clauses"]

    heads = [_clause_head_verb(c) for c in clauses]

    # S1: all-wayyiqtol → defer to S4 spec
    if all(h is not None and _is_wayyiqtol(h) for h in heads):
        return "SUPPRESSED", ["S1-all-wayyiqtol-defer-to-S4"]

    # Operate on the first two clauses for binary classification
    cl_a, cl_b = clauses[0], clauses[1]
    head_a, head_b = heads[0], heads[1]

    # S2: complement-clause (cl_b is the clausal complement of cl_a's matrix)
    if cl_a.wg_rule in _COMPLEMENT_RULES:
        return "SUPPRESSED", ["S2-complement-V2CL/Np2CL"]

    # S3a: cl_b is a relative clause
    if getattr(cl_b, "is_relative_clause", False):
        return "SUPPRESSED", ["S3a-relative-clause"]
    if cl_b.wg_rule == "relCL":
        return "SUPPRESSED", ["S3a-relCL-rule"]

    # S3b: relativizer (אשר/די/שׁ-) appears between the two heads in the line
    if head_a is not None and head_b is not None:
        in_between = False
        seen_head_a = False
        for t in line_tokens:
            if id(t) == id(head_a):
                seen_head_a = True
                continue
            if id(t) == id(head_b):
                if in_between:
                    return "SUPPRESSED", ["S3b-relativizer-between-heads"]
                break
            if seen_head_a and t.consonant_skel in _RELATIVIZER_SKELS:
                in_between = True

    # S4: first verb is a הָיָה-family discourse-formula opener
    if head_a is not None and head_a.consonant_skel in _DISCOURSE_FORMULA_SKELS:
        return "SUPPRESSED", ["S4-discourse-formula-opener"]

    # S5: both verbs cohortative (aspect h)
    if head_a is not None and head_b is not None:
        if _verb_aspect(head_a) == "H" and _verb_aspect(head_b) == "H":
            return "SUPPRESSED", ["S5-cohortative-pair"]

    # S6: both verbs imperative (aspect v) AND combined ≤4 prosodic words
    if head_a is not None and head_b is not None:
        if _verb_aspect(head_a) == "V" and _verb_aspect(head_b) == "V":
            if _pw_count(line_tokens) <= 4:
                return "SUPPRESSED", ["S6-imperative-pair-short"]

    # S7: both verbs preceded by negation
    if head_a is not None and head_b is not None:
        head_a_id, head_b_id = id(head_a), id(head_b)
        # Negation before head_a anywhere from line-start; negation before
        # head_b anywhere between head_a and head_b
        before_a_neg = False
        between_neg = False
        seen_a = False
        for t in line_tokens:
            if id(t) == head_a_id:
                seen_a = True
                continue
            if id(t) == head_b_id:
                break
            if not seen_a:
                if t.consonant_skel in _NEGATION_SKELS:
                    before_a_neg = True
            else:
                if t.consonant_skel in _NEGATION_SKELS:
                    between_neg = True
        if before_a_neg and between_neg:
            return "SUPPRESSED", ["S7-negation-pair"]

    # S8: speech-intro frame — head_a is a speech-act verb lemma. The
    # second finite verb is the speech content (typically imperative or
    # jussive in direct discourse). J3 announcement-frame, not a
    # generative-principle violation. Hpar covers this via the speech-
    # intro framing rule (H5/H5b); this scanner mirrors the discriminator.
    if head_a is not None and head_a.lemma in _SPEECH_ACT_LEMMAS:
        return "SUPPRESSED", ["S8-speech-intro-frame"]

    # S9: cognate-lemma hendiadys — both heads' lemmas form a bonded pair
    # per validators/_shared/hendiadys_lemma_pairs.py (M1-class merge).
    if head_a is not None and head_b is not None:
        lemma_a, lemma_b = head_a.lemma, head_b.lemma
        if lemma_a and lemma_b:
            pair_fwd = (lemma_a, lemma_b)
            pair_rev = (lemma_b, lemma_a)
            if pair_fwd in BONDED_LEMMA_PAIRS or pair_rev in BONDED_LEMMA_PAIRS:
                return "SUPPRESSED", ["S9-cognate-lemma-hendiadys"]

    # All mechanical suppressors passed.
    # Default: REVIEW-REQUIRED (Stan-confirms editorial intent vs M3/M4
    # fragmented-atomic-thought / M1 bonded-pair lemma residue). Only
    # promote to STRONG when both clauses are top-level coordinations
    # (LCA in COORD_RULES) — but we lack the full Hpar LCA machinery
    # here, so default to REVIEW-REQUIRED for safety.
    return "REVIEW-REQUIRED", ["mechanical-clean"]


def scan_book(book_slug: str, out_rows: list[str]) -> dict:
    he_dir = REPO_ROOT / "data" / "text-files" / "v2" / "he" / book_slug
    if not he_dir.exists():
        return {"chapters": 0, "candidates": 0}

    stats = {"chapters": 0, "candidates": 0, "suppressed": 0, "review": 0, "strong": 0}

    for ch_path in sorted(he_dir.glob("*.txt")):
        m = re.search(r"-(\d+)\.txt$", ch_path.name)
        if not m:
            continue
        ch_num = int(m.group(1))
        stats["chapters"] += 1

        # Load KJV layer for context
        kjv_path = REPO_ROOT / "data" / "text-files" / "v2" / "eng-gloss" / book_slug / ch_path.name
        kjv_lines_by_verse: dict[int, list[str]] = {}
        if kjv_path.exists():
            cur_v = None
            for ln in kjv_path.read_text(encoding="utf-8").split("\n"):
                mv = VERSE_REF_RE.match(ln.strip())
                if mv:
                    cur_v = int(mv.group(2))
                    kjv_lines_by_verse[cur_v] = []
                elif cur_v is not None and ln.strip():
                    kjv_lines_by_verse[cur_v].append(ln)

        # Walk the Hebrew chapter
        text = ch_path.read_text(encoding="utf-8")
        lines = text.split("\n")
        cur_verse = None
        verse_line_idx = 0  # 0-based index within the verse
        verse_lines: list[tuple[int, str]] = []  # (verse_line_idx, hebrew_line)

        def flush_verse(verse: int, vlines: list[tuple[int, str]]):
            if not vlines:
                return
            try:
                vtokens = MC.get_verse_tokens(book_slug, ch_num, verse)
                vclauses = MC.get_verse_clauses(book_slug, ch_num, verse)
            except Exception:
                return
            if not vtokens or not vclauses:
                return

            cursor = 0
            for verse_line_idx, hebrew_line in vlines:
                matched, cursor = MC.match_sense_line_tokens(vtokens, hebrew_line, cursor)
                if len(matched) < 3:
                    continue
                # Count finite verbs on the line
                fv = [t for t in matched if _is_finite_verb(t)]
                if len(fv) < 2:
                    continue
                # Find leaf clauses with heads on this line
                clauses_here = _clauses_with_heads_in(vclauses, matched)
                if len(clauses_here) < 2:
                    continue

                severity, trace = _suppressor_cascade(matched, clauses_here)
                if severity == "SUPPRESSED":
                    stats["suppressed"] += 1
                    continue

                head_a = _clause_head_verb(clauses_here[0])
                head_b = _clause_head_verb(clauses_here[1])
                head_a_lemma = head_a.lemma if head_a else "?"
                head_b_lemma = head_b.lemma if head_b else "?"
                head_a_asp = _verb_aspect(head_a) if head_a else "?"
                head_b_asp = _verb_aspect(head_b) if head_b else "?"

                kjv_for_v = " | ".join(kjv_lines_by_verse.get(verse, []))
                # Use the KJV line at the same verse_line_idx if available
                kjv_at_idx = ""
                kvl = kjv_lines_by_verse.get(verse, [])
                if verse_line_idx < len(kvl):
                    kjv_at_idx = kvl[verse_line_idx]

                stats["candidates"] += 1
                if severity == "STRONG-SPLIT-CANDIDATE":
                    stats["strong"] += 1
                else:
                    stats["review"] += 1

                out_rows.append("\t".join([
                    book_slug, str(ch_num), str(verse), str(verse_line_idx),
                    hebrew_line.strip(),
                    kjv_at_idx,
                    severity,
                    ";".join(trace),
                    head_a_lemma, head_a_asp,
                    head_b_lemma, head_b_asp,
                ]))

        for line in lines:
            mv = VERSE_REF_RE.match(line.strip())
            if mv:
                if cur_verse is not None:
                    flush_verse(cur_verse, verse_lines)
                cur_verse = int(mv.group(2))
                verse_lines = []
                verse_line_idx = 0
                continue
            if not line.strip():
                if cur_verse is not None:
                    flush_verse(cur_verse, verse_lines)
                    verse_lines = []
                    verse_line_idx = 0
                continue
            if cur_verse is None:
                continue
            verse_lines.append((verse_line_idx, line))
            verse_line_idx += 1

        if cur_verse is not None and verse_lines:
            flush_verse(cur_verse, verse_lines)

    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--book", default=None, help="Single book slug (e.g. 01-genesis)")
    ap.add_argument("--out", default=None,
                    help="Output TSV path (default: data/syntax-reference/multi-finite-verb-candidates.tsv)")
    args = ap.parse_args()

    out_path = Path(args.out) if args.out else (
        REPO_ROOT / "data" / "syntax-reference" / "multi-finite-verb-candidates.tsv"
    )

    rows = []
    rows.append("\t".join([
        "book", "chapter", "verse", "line_idx",
        "hebrew_line", "kjv_line",
        "severity", "suppressors_trace",
        "head1_lemma", "head1_aspect",
        "head2_lemma", "head2_aspect",
    ]))

    he_root = REPO_ROOT / "data" / "text-files" / "v2" / "he"
    if args.book:
        books = [args.book]
    else:
        books = sorted([d.name for d in he_root.iterdir() if d.is_dir()])

    totals = {"chapters": 0, "candidates": 0, "suppressed": 0, "strong": 0, "review": 0}
    for book in books:
        if book not in MC._BOOK_MAP:
            continue
        s = scan_book(book, rows)
        for k in totals:
            totals[k] += s.get(k, 0)
        print(f"  {book}: chapters={s['chapters']} candidates={s['candidates']} "
              f"(strong={s['strong']} review={s['review']}) suppressed={s['suppressed']}",
              file=sys.stderr)

    out_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"\nWrote {len(rows) - 1} candidates to {out_path}", file=sys.stderr)
    print(f"Totals: chapters={totals['chapters']} candidates={totals['candidates']} "
          f"(strong={totals['strong']} review={totals['review']}) "
          f"suppressed={totals['suppressed']}", file=sys.stderr)


if __name__ == "__main__":
    main()
