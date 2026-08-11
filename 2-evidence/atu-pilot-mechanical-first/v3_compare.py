#!/usr/bin/env python3
"""
v3_compare.py — compare Stan's cold-eye ATU baseline against the v2 pipeline output.

Inputs:
  research/atu-pilot-mechanical-first/genesis-22-cold-eye-baseline.txt
    (Stan-produced; one ATU per line under verse headers like '22:1')
  research/atu-pilot-mechanical-first/v2_final_atus.jsonl
    (pipeline output, 79 ATUs)

Comparison strategy:
  1. Normalize both renderings to consonant-only sequences (strip cantillation,
     vowels, dots, maqaf, spaces, punctuation).
  2. Per verse, list ATU boundaries as character indices into the consonant
     sequence.
  3. Compute boundary-level precision/recall:
       - True positive: a boundary present in BOTH at the same consonant position
       - False positive: boundary in pipeline only (over-bound vs cold-eye)
       - False negative: boundary in cold-eye only (under-bound vs cold-eye)
  4. Produce a side-by-side markdown report.

Outputs:
  research/atu-pilot-mechanical-first/v3_comparison.md
  research/atu-pilot-mechanical-first/v3_per_verse.jsonl
"""

from __future__ import annotations
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

OUT_DIR = Path(
    r"C:\Users\bibleman\repos\readers-tanakh\research\atu-pilot-mechanical-first"
)
COLD_EYE_PATH = OUT_DIR / "genesis-22-cold-eye-baseline.txt"
PIPELINE_PATH = OUT_DIR / "v2_final_atus.jsonl"

OUT_MD = OUT_DIR / "v3_comparison.md"
OUT_JSONL = OUT_DIR / "v3_per_verse.jsonl"

VERSE_HEADER_RE = re.compile(r"^22:(\d+)\s*$")

# Strip everything except Hebrew consonants for boundary alignment.
# Hebrew consonants: U+05D0..U+05EA
_CONS_ONLY_RE = re.compile(r"[^א-ת]")


def consonants_only(text: str) -> str:
    return _CONS_ONLY_RE.sub("", text)


def parse_cold_eye(path: Path) -> dict[int, list[str]]:
    """Return {verse_num: [atu_text, ...]}."""
    if not path.exists():
        raise SystemExit(
            f"ERROR: cold-eye baseline not found at {path}\n"
            "Save it there in v2/heb format (one ATU per line, '22:N' headers)."
        )
    verses: dict[int, list[str]] = {}
    current: int | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        m = VERSE_HEADER_RE.match(line.strip())
        if m:
            current = int(m.group(1))
            verses[current] = []
        elif current is not None:
            verses[current].append(line.strip())
    return verses


def parse_pipeline(path: Path) -> dict[int, list[str]]:
    """Return {verse_num: [atu_text, ...]} from v2_final_atus.jsonl."""
    if not path.exists():
        raise SystemExit(f"ERROR: pipeline output not found at {path}")
    verses: dict[int, list[str]] = defaultdict(list)
    with path.open(encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            verses[r["verse_first"]].append(r["text"])
    return dict(verses)


def compute_boundaries(atus: list[str]) -> tuple[str, list[int]]:
    """Given a list of ATU strings for one verse, return:
       - the concatenated consonant-only sequence for the whole verse
       - the list of boundary indices (where each ATU after the first begins)
    """
    consonants_per_atu = [consonants_only(a) for a in atus]
    full = "".join(consonants_per_atu)
    boundaries = []
    pos = 0
    for c in consonants_per_atu[:-1]:
        pos += len(c)
        boundaries.append(pos)
    return full, boundaries


def main() -> None:
    cold = parse_cold_eye(COLD_EYE_PATH)
    pipe = parse_pipeline(PIPELINE_PATH)

    all_verses = sorted(set(cold) & set(pipe))
    cold_only = sorted(set(cold) - set(all_verses))
    pipe_only = sorted(set(pipe) - set(all_verses))

    if cold_only or pipe_only:
        print(f"WARN: verse mismatch — cold-only={cold_only}, pipe-only={pipe_only}")

    # Per-verse comparison
    per_verse_records = []
    total_tp = total_fp = total_fn = 0
    for v in all_verses:
        cold_full, cold_bounds = compute_boundaries(cold[v])
        pipe_full, pipe_bounds = compute_boundaries(pipe[v])

        consonant_match = cold_full == pipe_full
        cold_b_set = set(cold_bounds)
        pipe_b_set = set(pipe_bounds)

        tp = len(cold_b_set & pipe_b_set)
        fp = len(pipe_b_set - cold_b_set)  # pipeline boundary not in cold (over-bound)
        fn = len(cold_b_set - pipe_b_set)  # cold boundary not in pipeline (under-bound)

        total_tp += tp
        total_fp += fp
        total_fn += fn

        per_verse_records.append({
            "verse": v,
            "cold_atu_count": len(cold[v]),
            "pipe_atu_count": len(pipe[v]),
            "boundary_tp": tp,
            "boundary_fp": fp,
            "boundary_fn": fn,
            "consonants_aligned": consonant_match,
            "cold_atus": cold[v],
            "pipe_atus": pipe[v],
        })

    # Write per-verse JSONL
    with OUT_JSONL.open("w", encoding="utf-8") as fp:
        for r in per_verse_records:
            fp.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Build markdown report
    total_cold_atus = sum(len(cold[v]) for v in all_verses)
    total_pipe_atus = sum(len(pipe[v]) for v in all_verses)

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    lines = []
    lines.append("# Gen 22 mechanical-first pilot — v3 comparison report\n")
    lines.append("Comparison of the mechanical-first pipeline (v0 → v1 → v1.5 → v2)\n"
                 "against Stan's cold-eye ATU baseline.\n")

    lines.append("\n## Headline numbers\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Total ATUs — cold-eye | {total_cold_atus} |")
    lines.append(f"| Total ATUs — pipeline | {total_pipe_atus} |")
    lines.append(f"| Boundary TP (match) | {total_tp} |")
    lines.append(f"| Boundary FP (pipeline over-bound) | {total_fp} |")
    lines.append(f"| Boundary FN (pipeline under-bound) | {total_fn} |")
    lines.append(f"| Boundary precision | {precision:.1%} |")
    lines.append(f"| Boundary recall | {recall:.1%} |")
    lines.append(f"| Boundary F1 | {f1:.1%} |\n")

    lines.append("\n## Per-verse comparison\n")
    lines.append(f"| Verse | Cold-eye | Pipeline | TP | FP (over) | FN (under) | Aligned |")
    lines.append(f"|---|---|---|---|---|---|---|")
    for r in per_verse_records:
        aligned_mark = "✓" if r["consonants_aligned"] else "✗"
        lines.append(
            f"| 22:{r['verse']} | {r['cold_atu_count']} | {r['pipe_atu_count']} | "
            f"{r['boundary_tp']} | {r['boundary_fp']} | {r['boundary_fn']} | {aligned_mark} |"
        )

    lines.append("\n## Side-by-side per verse\n")
    for r in per_verse_records:
        lines.append(f"\n### 22:{r['verse']}  ·  cold-eye {r['cold_atu_count']} | pipeline {r['pipe_atu_count']}\n")
        if not r["consonants_aligned"]:
            lines.append("> ⚠ consonants do not align — likely a transcription discrepancy.\n")
        max_len = max(r["cold_atu_count"], r["pipe_atu_count"])
        lines.append("| # | Cold-eye | Pipeline |")
        lines.append("|---|---|---|")
        for i in range(max_len):
            c = r["cold_atus"][i] if i < r["cold_atu_count"] else ""
            p = r["pipe_atus"][i] if i < r["pipe_atu_count"] else ""
            lines.append(f"| {i+1} | {c} | {p} |")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSONL}")
    print()
    print(f"--- Headline ---")
    print(f"  Cold-eye ATUs:  {total_cold_atus}")
    print(f"  Pipeline ATUs:  {total_pipe_atus}")
    print(f"  Boundary precision: {precision:.1%}  (TP={total_tp}, FP={total_fp})")
    print(f"  Boundary recall:    {recall:.1%}  (TP={total_tp}, FN={total_fn})")
    print(f"  Boundary F1:        {f1:.1%}")


if __name__ == "__main__":
    main()
