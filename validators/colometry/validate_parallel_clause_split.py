#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""validate_parallel_clause_split — Macula-driven SPLIT detector for parallel
clauses merged onto one line.

The Sifrei Emet parallel bicolon (PP+verb // PP+verb, gapped subject; canonical
Psa 23:2) is the motivating class. The detector queries Macula's constituent
tree for clause boundaries and fires when a single v2/he line contains tokens
spanning >=2 distinct clauses, each with its own finite-verb head.

Engine: Macula Hebrew lowfat XML. NO te'amim glyphs in trigger logic
(canon §1 corollary). Severity: STRONG-SPLIT-CANDIDATE. Conservative
trigger (each side >=3 prosodic words) keeps FP rate low.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from validators._shared import macula_constituents as MC


SEVERITY = "STRONG-SPLIT-CANDIDATE"
RULE = "Hpar"
SUBCASE = "parallel_clause_split"
GAPPED_SUBCASE = "parallel_gapped_restatement"
GAPPED_SEVERITY = "REVIEW-REQUIRED"  # FP risk warrants editor confirmation
MIN_HALF_PW = 2  # Hebrew bicola can be 3+2 or 2+3; 2 is the minimum atomic-thought width

# Closed-list suppressions for the gapped-restatement arm (per audit
# 2026-05-05 ab272883f08b465c3 — 6 FP classes covering ~40 of 60 raw
# candidates in SE). Body-part lemmas in particular form paired idioms
# (e.g., יָד ... יָד across PP boundaries) that aren't gapped-restatement.
GAPPED_BODY_PART_LEMMAS = frozenset({
    "יָד", "לֵב", "לֵבָב", "רֹאשׁ", "עַיִן", "נֶפֶשׁ", "פֶּה",
})
GAPPED_DOR_LEMMA = "דּוֹר"  # דּוֹר וָדֹר idiom — vav-between suppressor
GAPPED_KOL_LEMMA = "כֹּל"   # construct-state quantifier


def _is_finite_verb(t: MC.Token) -> bool:
    morph = (t._morph_tag or "").upper()
    if not morph or morph[0] != "V" or len(morph) < 3:
        return False
    return morph[2] in ("Q", "W", "I", "V", "O", "J", "H", "U")


def _is_wayyiqtol(t: MC.Token) -> bool:
    morph = (t._morph_tag or "").upper()
    return bool(morph and morph[0] == "V" and len(morph) >= 3 and morph[2] == "W")


def _clause_head_verb(clause: MC.Constituent) -> Optional[MC.Token]:
    for t in clause.tokens:
        if _is_finite_verb(t):
            return t
    return None


def _is_leaf_clause(cl: MC.Constituent) -> bool:
    """A leaf clause has no descendant Constituents that are themselves clauses."""
    for c in cl.child_constituents:
        if c.is_clause:
            return False
        # recurse one level deeper to catch grand-child clauses
        for gc in c.child_constituents:
            if gc.is_clause:
                return False
    return True


def _clauses_with_heads_in(verse_clauses: list[MC.Constituent],
                           line_tokens: list[MC.Token]) -> list[MC.Constituent]:
    """Return LEAF clauses whose finite-verb head is among line_tokens.
    Wrapper / outer clauses are filtered out so we only emit on the
    innermost actual clause boundaries."""
    line_ids = {id(t) for t in line_tokens}
    out: list[MC.Constituent] = []
    seen: set[int] = set()
    for cl in verse_clauses:
        if not _is_leaf_clause(cl):
            continue
        head = _clause_head_verb(cl)
        if head is None:
            continue
        if id(head) in line_ids and id(cl) not in seen:
            out.append(cl)
            seen.add(id(cl))
    return out


def _split_index(line_tokens: list[MC.Token],
                 clause_b: MC.Constituent) -> Optional[int]:
    cb_ids = {id(t) for t in clause_b.tokens}
    for i, t in enumerate(line_tokens):
        if id(t) in cb_ids:
            return i
    return None


def _gapped_restatement_findings(
    line_tokens: list[MC.Token],
    clauses_here: list[MC.Constituent],
    line_text: str,
    file_line_no: int,
    rel_path: str,
    chapter_no: int,
    verse: int,
) -> list[dict[str, Any]]:
    """Hpar-gapped arm — detect verbless second clause restating the first
    clause's predicate noun (e.g., Psa 9:10 'Yahweh refuge for-X | refuge
    for-Y'). Per audit ab272883f08b465c3 design proposal."""
    out: list[dict[str, Any]] = []
    if len(clauses_here) < 2:
        return out
    # Need exactly one clause with finite-verb head + at least one verbless
    finite_clauses = [c for c in clauses_here if _clause_head_verb(c) is not None]
    verbless_clauses = [c for c in clauses_here if _clause_head_verb(c) is None]
    if not finite_clauses or not verbless_clauses:
        return out
    # Surface order: finite first, verbless second (left-to-right gapping only)
    line_id_pos = {id(t): i for i, t in enumerate(line_tokens)}

    def _first_pos(cl: MC.Constituent) -> int:
        for t in cl.tokens:
            if id(t) in line_id_pos:
                return line_id_pos[id(t)]
        return 9999

    finite_first = min(finite_clauses, key=_first_pos)
    verbless_after = [c for c in verbless_clauses if _first_pos(c) > _first_pos(finite_first)]
    if not verbless_after:
        return out
    verbless_first = min(verbless_after, key=_first_pos)

    # Find shared noun lemma between finite and verbless clauses
    finite_noun_lemmas = {
        t.lemma for t in finite_first.tokens
        if t.pos == "noun" and t.lemma and t.type_ != "proper"
    }
    verbless_noun_lemmas = {
        t.lemma for t in verbless_first.tokens
        if t.pos == "noun" and t.lemma and t.type_ != "proper"
    }
    shared = finite_noun_lemmas & verbless_noun_lemmas
    if not shared:
        return out

    # Suppressions per audit
    for shared_lemma in shared:
        if shared_lemma == GAPPED_KOL_LEMMA:
            continue  # quantifier
        if shared_lemma in GAPPED_BODY_PART_LEMMAS:
            continue  # paired body-part idiom
        # Get token instances of shared lemma in line
        shared_toks = [t for t in line_tokens if t.lemma == shared_lemma]
        if len(shared_toks) < 2:
            continue
        # Vav-between suppressor (דּוֹר וָדֹר idiom)
        if shared_lemma == GAPPED_DOR_LEMMA:
            tok_positions = [line_id_pos[id(t)] for t in shared_toks]
            tok_positions.sort()
            mid_tokens = line_tokens[tok_positions[0] + 1 : tok_positions[1]]
            if any(t.pos == "conjunction" and t.lemma in ("וְ", "ו") for t in mid_tokens):
                continue
        # Both-construct suppressor
        if all(t.state == "construct" for t in shared_toks if t.state):
            continue
        # Distributive-adv suppressor
        if any(t.role == "adv" for t in shared_toks):
            continue
        # Passed all suppressors — emit
        idx = _split_index(line_tokens, verbless_first)
        if idx is None or idx == 0:
            continue
        left = _pw_count(line_tokens[:idx])
        right = _pw_count(line_tokens[idx:])
        if left < MIN_HALF_PW or right < MIN_HALF_PW:
            continue
        out.append({
            "file": rel_path,
            "line": file_line_no,
            "rule": RULE,
            "subcase": GAPPED_SUBCASE,
            "severity": GAPPED_SEVERITY,
            "verse": f"{chapter_no}:{verse}",
            "annotation": (
                f"Hpar gapped-restatement: predicate-noun '{shared_lemma}' "
                f"repeated across finite clause + verbless restatement; "
                f"split before token {idx} ({left}+{right} pw)"
            ),
            "suggested_action": "SPLIT_AT_GAPPED_BOUNDARY",
            "split_positions": [idx],
            "prior_line": line_text,
        })
        return out  # one finding per line (first shared lemma wins)
    return out


def _line_token_spans(verse_tokens: list[MC.Token],
                      v2_lines: list[str]) -> list[list[MC.Token]]:
    out = []
    cursor = 0
    for ln in v2_lines:
        if not ln.strip():
            continue
        matched, next_cursor = MC.match_sense_line_tokens(verse_tokens, ln, cursor)
        out.append(matched)
        cursor = next_cursor
    return out


def _pw_count(tokens: list[MC.Token]) -> int:
    """Count prosodic words by walking the previous token's `after` field;
    if it contains whitespace, the current token starts a new prosodic word.
    Maqqef-bonded morphemes have no whitespace in after → bonded into one pw."""
    if not tokens:
        return 0
    pw = 1
    for i in range(1, len(tokens)):
        prev_after = (getattr(tokens[i - 1], "after", "") or "")
        if any(c.isspace() for c in prev_after):
            pw += 1
    return pw


def scan_file(path: Path, book_slug: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    current_verse: Optional[int] = None
    chapter_no: Optional[int] = None
    vlines: list[str] = []
    vline_indices: list[int] = []

    def _flush(verse: int, lines_for: list[str], indices: list[int]):
        if verse is None or chapter_no is None or not lines_for:
            return
        try:
            vtokens = MC.get_verse_tokens(book_slug, chapter_no, verse)
            vclauses = MC.get_verse_clauses(book_slug, chapter_no, verse)
        except Exception:
            return
        if not vtokens or not vclauses:
            return
        line_token_lists = _line_token_spans(vtokens, lines_for)
        non_blank_lines = [l for l in lines_for if l.strip()]
        for line_tokens, line_text, file_line_no in zip(
            line_token_lists, non_blank_lines, indices
        ):
            if len(line_tokens) < 4:
                continue
            # Gapped-restatement arm runs against ALL leaf clauses (including
            # verbless ones), so collect those separately.
            line_ids = {id(t) for t in line_tokens}
            all_leaf_in_line: list[MC.Constituent] = []
            seen: set[int] = set()
            for cl in vclauses:
                if not _is_leaf_clause(cl):
                    continue
                if id(cl) in seen:
                    continue
                if any(id(t) in line_ids for t in cl.tokens):
                    all_leaf_in_line.append(cl)
                    seen.add(id(cl))
            findings.extend(_gapped_restatement_findings(
                line_tokens, all_leaf_in_line, line_text, file_line_no,
                str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                chapter_no, verse,
            ))

            clauses_here = _clauses_with_heads_in(vclauses, line_tokens)
            if len(clauses_here) < 2:
                continue
            # Defer-to-S4 guard: if ALL clause heads on this line are
            # wayyiqtols, S4 (multi_wayyiqtol_clause_split spec) already
            # handles the case with its specialized hendiadys / shared-DO /
            # bare-verb suppressions. Avoid double-fire.
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
                cl_b = clauses_sorted[j + 1]
                idx = _split_index(line_tokens, cl_b)
                if idx is None or idx == 0:
                    continue
                left = _pw_count(line_tokens[:idx])
                right = _pw_count(line_tokens[idx:])
                if left < MIN_HALF_PW or right < MIN_HALF_PW:
                    continue
                head_a = _clause_head_verb(clauses_sorted[j])
                head_b = _clause_head_verb(cl_b)
                # FP-overcount guard (2026-05-05 FP audit #1, ~9 of 13 sampled
                # FPs): when both clause heads share the same lemma, the second
                # is almost always the matrix verb's own occurrence inside an
                # אֲשֶׁר / כַּאֲשֶׁר / כִּי relative clause that Macula's leaf
                # partition split as a separate clause. The relative-clause
                # verb is subordinate to the matrix, not a coordinate
                # proposition. Examples: Lev 9:6 + 2Ki 11:5 (תַּעֲשׂוּ matrix +
                # תַּעֲשׂוּן relative); Jdg 7:5 (יָלֹק × 2 across relative +
                # simile); Isa 41:13 (תִּירָא × 2 with embedded quote).
                if (
                    head_a is not None and head_b is not None
                    and head_a.lemma and head_b.lemma
                    and head_a.lemma == head_b.lemma
                ):
                    continue
                findings.append({
                    "file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                    "line": file_line_no,
                    "rule": RULE,
                    "subcase": SUBCASE,
                    "severity": SEVERITY,
                    "verse": f"{chapter_no}:{verse}",
                    "annotation": (
                        f"Hpar parallel-clause split: heads "
                        f"{head_a.text if head_a else '?'} | "
                        f"{head_b.text if head_b else '?'}; split before "
                        f"token {idx} ({left}+{right} pw)"
                    ),
                    "suggested_action": "SPLIT_AT_CLAUSE_BOUNDARY",
                    "split_positions": [idx],
                    "prior_line": line_text,
                })

    for idx, raw in enumerate(lines, start=1):
        s = raw.strip()
        if not s:
            if current_verse is not None and vlines:
                _flush(current_verse, vlines, vline_indices)
                vlines, vline_indices = [], []
            continue
        if ":" in s and all(p.isdigit() for p in s.split(":")):
            ch_str, vs_str = s.split(":")
            chapter_no = int(ch_str)
            if current_verse is not None and vlines:
                _flush(current_verse, vlines, vline_indices)
            current_verse = int(vs_str)
            vlines, vline_indices = [], []
            continue
        vlines.append(s)
        vline_indices.append(idx)

    if current_verse is not None and vlines:
        _flush(current_verse, vlines, vline_indices)

    return findings


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--v2", action="store_true")
    p.add_argument("--book", help="restrict to book slug")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    base = REPO_ROOT / "data" / "text-files" / "v2" / "he"
    books = sorted(base.iterdir()) if base.exists() else []
    if args.book:
        books = [b for b in books if b.name == args.book]

    all_findings: list[dict[str, Any]] = []
    for book_dir in books:
        if not book_dir.is_dir():
            continue
        slug = book_dir.name
        for ch_file in sorted(book_dir.glob("*.txt")):
            try:
                fnd = scan_file(ch_file, slug)
                all_findings.extend(fnd)
            except Exception as e:
                print(f"[{slug}/{ch_file.name}] error: {e}", file=sys.stderr)

    if args.json:
        print(json.dumps({
            "validator": "validate_parallel_clause_split",
            "summary": {"total_findings": len(all_findings)},
            "findings": all_findings,
        }, ensure_ascii=False, indent=2))
    else:
        for f in all_findings:
            print(f"  {f['file']}:{f['line']}  {f['verse']}  {f['annotation']}")
        print(f"\nTotal: {len(all_findings)} parallel-clause-split candidates")

    return 0


if __name__ == "__main__":
    sys.exit(main())
