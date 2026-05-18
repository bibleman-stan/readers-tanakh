#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""score_and_apply.py — agreement scoring + JSONL emission for Torah render
batches dispatched via Agent (not via render_atus.py live-API path).

Reads three passN.md files per chapter from
data/reports/atu_pipeline/<batch>/, parses each via render_atus.parse_pass_output,
scores per-verse agreement, and emits a Stage-1 JSONL at
data/reports/atu_pipeline/<book>/chapter-NN.jsonl matching the format
audit_constraints.py consumes.

This script NEVER writes to data/text-files/v2/heb/. v2/heb integration is a
separate pilot-branch phase gated on Stan adjudication of the batch
editorial-review surface (see directive 2026-05-17-1700 §12–17).

Draft semantics (per directive 2026-05-17-1700 §5, corrected):
  - UNANIMOUS    : source bytes regrouped per the unanimous line-break decision
  - MAJORITY     : source bytes regrouped per the matching pair's line-break
                   decision
  - ALL-DISAGREE : draft = source (no resolution at Stage 1)
  - INSUFFICIENT : draft = source (one or more passes missing)

Source-byte reassembly preserves the canonical Hebrew character / vowel-point /
te'amim order from v2/heb. LLM output is NFC-normalized and would silently
mutate vowel-mark ordering if used as draft bytes directly — so we use the
LLM's line-break decisions only, applied to source words.

If the source word count and LLM word count diverge (token mismatch), the
verse falls back to source-as-draft and the verdict is downgraded to
INSUFFICIENT-PASSES (with status recorded in the per-pass field).

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/atu_pipeline/score_and_apply.py \\
        --batch torah-batch-gen-01-10 --book 01-genesis --chapter 1
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "atu_pipeline"))

from render_atus import (  # noqa: E402
    V2_HEB,
    REPORT_DIR,
    load_chapter,
    parse_pass_output,
    normalize_for_comparison,
    score_agreement,
)


def source_words(lines: list[str]) -> list[str]:
    """Source-byte words from verse lines (preserving exact bytes, including
    non-canonical Hebrew mark order — TAHOT/WLC fidelity)."""
    out: list[str] = []
    for ln in lines:
        out.extend(ln.split())
    return out


def reassemble_with_source_bytes(
    src_words: list[str], rendered: str
) -> tuple[str | None, str]:
    """Given source-byte word sequence and LLM-rendered state (with line
    breaks), return (reassembled_with_source_bytes, status).

    Status is one of: OK / TOKEN-MISMATCH / WORD-COUNT-MISMATCH.

    The LLM's job is to place line breaks among the source words. We trust
    its line breaks but use source bytes for the words themselves.
    """
    rendered_lines = [ln for ln in rendered.splitlines() if ln.strip()]
    rendered_word_lists = [ln.split() for ln in rendered_lines]
    rendered_flat = [w for grp in rendered_word_lists for w in grp]

    if len(rendered_flat) != len(src_words):
        return None, f"WORD-COUNT-MISMATCH (src={len(src_words)}, rendered={len(rendered_flat)})"

    src_nfc = [unicodedata.normalize("NFC", w) for w in src_words]
    rendered_nfc = [unicodedata.normalize("NFC", w) for w in rendered_flat]
    for i, (s, r) in enumerate(zip(src_nfc, rendered_nfc)):
        if s != r:
            return None, f"TOKEN-MISMATCH at idx {i}: src={src_words[i]!r} rendered={rendered_flat[i]!r}"

    idx = 0
    out_lines: list[str] = []
    for grp in rendered_word_lists:
        n = len(grp)
        out_lines.append(" ".join(src_words[idx:idx + n]))
        idx += n
    return "\n".join(out_lines), "OK"


def read_pass_file(batch_dir: Path, book_slug: str, chapter: int, pass_id: int) -> str:
    short = book_slug.split("-", 1)[1] if "-" in book_slug else book_slug
    path = batch_dir / f"{short}-{chapter:02d}-pass{pass_id}.md"
    if not path.is_file():
        raise FileNotFoundError(f"pass file not found: {path}")
    return path.read_text(encoding="utf-8")


def find_majority_pair(p1: str, p2: str, p3: str) -> str | None:
    """Return one of the matching pair's raw texts (whichever appears first)
    when normalized comparison shows a 2-of-3 majority. None if no 2-of-3."""
    norms = [normalize_for_comparison(p) for p in (p1, p2, p3)]
    raws = [p1, p2, p3]
    for i in range(3):
        for j in range(i + 1, 3):
            if norms[i] and norms[i] == norms[j]:
                return raws[i]
    return None


def resolve_draft(
    src_words: list[str],
    verdict: str,
    p1: str,
    p2: str,
    p3: str,
    source_text: str,
) -> tuple[str, str]:
    """Compute the draft per directive §5 semantics.

    Returns (draft_text, reassembly_status). reassembly_status is "OK"
    when source-byte reassembly succeeded, "FALLBACK-TO-SOURCE" otherwise.
    """
    if verdict == "UNANIMOUS":
        chosen = p1 if normalize_for_comparison(p1) else (p2 or p3)
        reassembled, status = reassemble_with_source_bytes(src_words, chosen.strip())
        if reassembled is not None:
            return reassembled, "OK"
        return source_text, f"FALLBACK-TO-SOURCE ({status})"
    if verdict == "MAJORITY":
        maj = find_majority_pair(p1, p2, p3)
        if maj is None:
            return source_text, "FALLBACK-TO-SOURCE (no majority pair)"
        reassembled, status = reassemble_with_source_bytes(src_words, maj.strip())
        if reassembled is not None:
            return reassembled, "OK"
        return source_text, f"FALLBACK-TO-SOURCE ({status})"
    # ALL-DISAGREE / INSUFFICIENT-PASSES / MISSING-FROM-PASSES
    return source_text, "SOURCE (no resolution at Stage 1)"


def emit_chapter_jsonl(
    batch_dir: Path,
    book_slug: str,
    chapter: int,
) -> dict:
    chapter_path, verses = load_chapter(book_slug, chapter)
    pass_outputs = [read_pass_file(batch_dir, book_slug, chapter, i) for i in (1, 2, 3)]
    per_verse_passes = [parse_pass_output(p) for p in pass_outputs]

    counts = {
        "UNANIMOUS": 0,
        "MAJORITY": 0,
        "ALL-DISAGREE": 0,
        "MAJORITY-UNCERTAIN": 0,
        "INSUFFICIENT-PASSES": 0,
        "MISSING-FROM-PASSES": 0,
    }

    audit_input_dir = REPORT_DIR / book_slug
    audit_input_dir.mkdir(parents=True, exist_ok=True)
    audit_input_path = audit_input_dir / f"chapter-{chapter:02d}.jsonl"

    with audit_input_path.open("w", encoding="utf-8") as f:
        for vb in verses:
            ref = vb.ref
            p1 = per_verse_passes[0].get(ref, "")
            p2 = per_verse_passes[1].get(ref, "")
            p3 = per_verse_passes[2].get(ref, "")
            source = "\n".join(vb.lines)

            if not (p1 or p2 or p3):
                verdict = "MISSING-FROM-PASSES"
                draft = source
                reassembly_status = "SOURCE (no passes)"
            else:
                verdict = score_agreement(p1, p2, p3)
                src_words = source_words(vb.lines)
                draft, reassembly_status = resolve_draft(
                    src_words, verdict, p1, p2, p3, source
                )

            counts[verdict] = counts.get(verdict, 0) + 1

            record = {
                "verse": ref,
                "source": source,
                "draft": draft,
                "agreement": verdict,
                "reassembly": reassembly_status,
                "pass1": p1.strip(),
                "pass2": p2.strip(),
                "pass3": p3.strip(),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return {
        "book": book_slug,
        "chapter": chapter,
        "verse_count": len(verses),
        "counts": counts,
        "jsonl_path": str(audit_input_path.relative_to(REPO_ROOT)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--batch", required=True, help="batch dir name under data/reports/atu_pipeline/")
    ap.add_argument("--book", required=True, help="book slug, e.g. 01-genesis")
    ap.add_argument("--chapter", type=int, required=True)
    args = ap.parse_args()

    batch_dir = REPORT_DIR / args.batch
    if not batch_dir.is_dir():
        print(f"ERROR: batch dir not found: {batch_dir}", file=sys.stderr)
        return 1

    report = emit_chapter_jsonl(batch_dir, args.book, args.chapter)
    print(f"{args.book} ch {args.chapter}: " + ", ".join(
        f"{k}={v}" for k, v in report["counts"].items() if v
    ) + f" | jsonl={report['jsonl_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
