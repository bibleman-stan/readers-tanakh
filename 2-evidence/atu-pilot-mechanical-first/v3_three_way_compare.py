#!/usr/bin/env python3
"""
v3_three_way_compare.py — three-way comparison of the mechanical-first pipeline
against the principled cold-eye baseline AND the LDHB reference.

Inputs:
  research/atu-pilot-mechanical-first/v1_5_groups.jsonl    (refined pipeline)
  research/atu-pilot-mechanical-first/genesis-22-principled-baseline.txt
  research/atu-pilot-mechanical-first/ldhb_units.jsonl

Comparison:
  - Per verse, normalize each rendering to consonant-only sequences
  - Compute boundary indices (where each unit-after-the-first begins)
  - Three-way pairwise precision/recall on boundary alignment:
       pipeline vs cold-eye
       pipeline vs ldhb
       cold-eye vs ldhb

Outputs:
  v3_three_way_report.md     (markdown report with per-verse tables)
  v3_three_way_per_verse.jsonl
"""

from __future__ import annotations
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pilot_config as cfg

OUT_DIR = cfg.PILOT_DIR
PIPELINE_PATH = cfg.V1_5_JSONL
COLD_EYE_PATH = cfg.PRINCIPLED_TXT
LDHB_PATH = cfg.LDHB_UNITS_JSONL

OUT_MD = cfg.V3_MD
OUT_JSONL = cfg.V3_JSONL

VERSE_HEADER_RE = cfg.VERSE_HEADER_RE
_POINTING_RE = re.compile(r"[֑-ׇ]")
_CONS_ONLY_RE = re.compile(r"[^א-ת]")


def consonants_only_hebrew(text: str) -> str:
    return _CONS_ONLY_RE.sub("", text)


def normalize_translit(text: str) -> str:
    """Strip whitespace and non-letter characters from transliterated text for alignment."""
    return re.sub(r"[^a-zA-Z]", "", text).lower()


def parse_pipeline() -> dict[int, list[str]]:
    """Return {verse: [hebrew_text per group, ...]}."""
    verses: dict[int, list[str]] = defaultdict(list)
    with PIPELINE_PATH.open(encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            verses[r["verse_first"]].append(r["text"])
    return dict(verses)


def parse_cold_eye() -> dict[int, list[str]]:
    """Return {verse: [translit_text per ATU, ...]} from principled baseline (transliteration)."""
    verses: dict[int, list[str]] = {}
    current: int | None = None
    for raw in COLD_EYE_PATH.read_text(encoding="utf-8").splitlines():
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


def parse_ldhb() -> dict[int, list[str]]:
    """Return {verse: [hebrew_text per LDHB unit, ...]}."""
    verses: dict[int, list[str]] = defaultdict(list)
    with LDHB_PATH.open(encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            u = json.loads(line)
            if u["verse"] is not None:
                verses[u["verse"]].append(u["text"])
    return dict(verses)


def boundary_positions(units: list[str], normalize) -> tuple[str, set[int]]:
    """Given a list of unit texts for one verse and a normalize-fn, return:
       - full normalized verse string
       - set of boundary positions (character indices where new unit starts)
    """
    normalized = [normalize(u) for u in units]
    full = "".join(normalized)
    boundaries = set()
    pos = 0
    for n in normalized[:-1]:
        pos += len(n)
        if pos > 0:
            boundaries.add(pos)
    return full, boundaries


def pair_metrics(a: set[int], b: set[int]) -> dict:
    """Compute precision/recall/F1 of set a against b (b as reference).
       precision = TP / (TP + FP); how often a's boundaries hit b's
       recall    = TP / (TP + FN); how many of b's boundaries a found
    """
    tp = len(a & b)
    fp = len(a - b)
    fn = len(b - a)
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "p": p, "r": r, "f1": f1}


def main() -> None:
    pipe = parse_pipeline()
    cold = parse_cold_eye()
    # LDHB is optional — if no markup file for this chapter, fall back to two-way.
    if cfg.LDHB_UNITS_JSONL.exists():
        ldhb = parse_ldhb()
        all_verses = sorted(set(pipe) & set(cold) & set(ldhb))
        have_ldhb = True
    else:
        print(f"NOTE: no LDHB units file at {cfg.LDHB_UNITS_JSONL} — running two-way (pipeline vs cold-eye only)")
        ldhb = {v: [] for v in pipe}
        all_verses = sorted(set(pipe) & set(cold))
        have_ldhb = False

    # For each verse: align by character-position boundary sets.
    # Pipeline and LDHB are in Hebrew → use consonants_only_hebrew.
    # Cold-eye is in transliteration → use normalize_translit.
    # We CANNOT directly compare across normalizations within one set, but
    # since boundary counts (number of breaks) is what we care about, we
    # compute boundary COUNTS per source per verse and report alignment at
    # the verse-count level. Pairwise boundary-alignment in the SAME
    # normalization space is also computed where possible.
    #
    # Two comparable comparisons within a normalization:
    #  - Pipeline (Hebrew) vs LDHB (Hebrew): both Hebrew, boundary indices align
    #  - Cold-eye (translit) is a separate axis; we use boundary COUNTS only
    #
    # For pipeline vs cold-eye, we approximate by verse-count match.

    per_verse_records = []
    pl_total_atus = sum(len(pipe[v]) for v in all_verses)
    co_total_atus = sum(len(cold[v]) for v in all_verses)
    ld_total_atus = sum(len(ldhb[v]) for v in all_verses)

    # Aggregate pipeline-vs-LDHB at boundary level (same Hebrew normalization)
    total_pl_vs_ld = {"tp": 0, "fp": 0, "fn": 0}

    for v in all_verses:
        pipe_full, pipe_b = boundary_positions(pipe[v], consonants_only_hebrew)
        ldhb_full, ldhb_b = boundary_positions(ldhb[v], consonants_only_hebrew)
        # Cold-eye boundary positions in translit space — not directly comparable
        # to Hebrew positions; for count-level analysis only.

        # Boundary-level comparison: pipeline vs LDHB
        pl_vs_ld = pair_metrics(pipe_b, ldhb_b)
        for k in ("tp", "fp", "fn"):
            total_pl_vs_ld[k] += pl_vs_ld[k]

        # Count-level alignment (does each source produce the same number of ATUs?)
        n_pl = len(pipe[v])
        n_co = len(cold[v])
        n_ld = len(ldhb[v])

        per_verse_records.append({
            "verse": v,
            "n_pipeline": n_pl,
            "n_cold_eye": n_co,
            "n_ldhb": n_ld,
            "consonant_aligned_pl_vs_ld": pipe_full == ldhb_full,
            "pl_vs_ld_boundaries": pl_vs_ld,
            "pipeline_atus": pipe[v],
            "cold_eye_atus": cold[v],
            "ldhb_atus": ldhb[v],
        })

    with OUT_JSONL.open("w", encoding="utf-8") as fp:
        for r in per_verse_records:
            fp.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Total pipeline-vs-LDHB boundary-alignment summary
    tot = total_pl_vs_ld
    p = tot["tp"] / (tot["tp"] + tot["fp"]) if (tot["tp"] + tot["fp"]) else 0.0
    r = tot["tp"] / (tot["tp"] + tot["fn"]) if (tot["tp"] + tot["fn"]) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0

    # Count-level alignment summary
    n_count_match_all_three = sum(
        1 for rec in per_verse_records
        if rec["n_pipeline"] == rec["n_cold_eye"] == rec["n_ldhb"]
    )
    n_count_pl_vs_co = sum(
        1 for rec in per_verse_records if rec["n_pipeline"] == rec["n_cold_eye"]
    )
    n_count_pl_vs_ld = sum(
        1 for rec in per_verse_records if rec["n_pipeline"] == rec["n_ldhb"]
    )
    n_count_co_vs_ld = sum(
        1 for rec in per_verse_records if rec["n_cold_eye"] == rec["n_ldhb"]
    )

    # Build markdown
    lines = []
    comparison_kind = "three-way" if have_ldhb else "two-way"
    ref_phrase = "principled cold-eye baseline AND Lexham Discourse Hebrew Bible (LDHB)" if have_ldhb else "principled cold-eye baseline"
    lines.append(f"# {cfg.CHAPTER_DISPLAY} mechanical-first pilot — v3 {comparison_kind} comparison\n")
    lines.append(f"Comparison of refined v1.5 pipeline against {ref_phrase}.\n")

    lines.append("\n## Headline\n")
    lines.append(f"| Source | Total ATUs / units |")
    lines.append(f"|---|---|")
    lines.append(f"| Refined pipeline (v1.5 only) | {pl_total_atus} |")
    lines.append(f"| Principled cold-eye | {co_total_atus} |")
    lines.append(f"| LDHB | {ld_total_atus} |")

    lines.append("\n## Verse-count agreement\n")
    lines.append(f"| Comparison | Verses with same ATU count |")
    lines.append(f"|---|---|")
    lines.append(f"| All three agree | {n_count_match_all_three} / {len(all_verses)} |")
    lines.append(f"| Pipeline = cold-eye | {n_count_pl_vs_co} / {len(all_verses)} |")
    lines.append(f"| Pipeline = LDHB | {n_count_pl_vs_ld} / {len(all_verses)} |")
    lines.append(f"| Cold-eye = LDHB | {n_count_co_vs_ld} / {len(all_verses)} |")

    lines.append("\n## Boundary-level alignment (pipeline vs LDHB, Hebrew normalization)\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Boundary TP (both place a break) | {tot['tp']} |")
    lines.append(f"| Boundary FP (pipeline break LDHB doesn't have) | {tot['fp']} |")
    lines.append(f"| Boundary FN (LDHB break pipeline doesn't have) | {tot['fn']} |")
    lines.append(f"| Boundary precision (pipeline against LDHB) | {p:.1%} |")
    lines.append(f"| Boundary recall (LDHB coverage by pipeline) | {r:.1%} |")
    lines.append(f"| Boundary F1 | {f1:.1%} |")

    lines.append("\n## Per-verse ATU counts\n")
    lines.append(f"| Verse | Pipeline | Cold-eye | LDHB | All match? |")
    lines.append(f"|---|---|---|---|---|")
    for rec in per_verse_records:
        if have_ldhb:
            match = "✓" if rec["n_pipeline"] == rec["n_cold_eye"] == rec["n_ldhb"] else ""
        else:
            match = "✓" if rec["n_pipeline"] == rec["n_cold_eye"] else ""
        lines.append(
            f"| {cfg.VERSE_PREFIX}{rec['verse']} | {rec['n_pipeline']} | {rec['n_cold_eye']} | {rec['n_ldhb']} | {match} |"
        )

    lines.append("\n## Per-verse side-by-side (divergent verses only)\n")
    for rec in per_verse_records:
        if have_ldhb:
            if rec["n_pipeline"] == rec["n_cold_eye"] == rec["n_ldhb"]:
                continue
            lines.append(f"\n### {cfg.VERSE_PREFIX}{rec['verse']}  ·  pipeline {rec['n_pipeline']} / cold-eye {rec['n_cold_eye']} / LDHB {rec['n_ldhb']}\n")
        else:
            if rec["n_pipeline"] == rec["n_cold_eye"]:
                continue
            lines.append(f"\n### {cfg.VERSE_PREFIX}{rec['verse']}  ·  pipeline {rec['n_pipeline']} / cold-eye {rec['n_cold_eye']}\n")
        max_len = max(rec["n_pipeline"], rec["n_cold_eye"], rec["n_ldhb"])
        lines.append("| # | Pipeline (Hebrew) | Cold-eye (translit) | LDHB (Hebrew) |")
        lines.append("|---|---|---|---|")
        for i in range(max_len):
            pl = rec["pipeline_atus"][i] if i < rec["n_pipeline"] else ""
            co = rec["cold_eye_atus"][i] if i < rec["n_cold_eye"] else ""
            ld = rec["ldhb_atus"][i] if i < rec["n_ldhb"] else ""
            lines.append(f"| {i+1} | {pl} | {co} | {ld} |")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSONL}")
    print()
    print(f"--- Headline ---")
    print(f"  Pipeline total:  {pl_total_atus}")
    print(f"  Cold-eye total:  {co_total_atus}")
    print(f"  LDHB total:      {ld_total_atus}")
    print(f"\n--- Verse-count agreement (of {len(all_verses)} verses) ---")
    print(f"  All three match: {n_count_match_all_three}")
    print(f"  Pipeline = cold-eye: {n_count_pl_vs_co}")
    print(f"  Pipeline = LDHB:     {n_count_pl_vs_ld}")
    print(f"  Cold-eye = LDHB:     {n_count_co_vs_ld}")
    print(f"\n--- Boundary alignment (pipeline vs LDHB) ---")
    print(f"  Precision: {p:.1%}  Recall: {r:.1%}  F1: {f1:.1%}")


if __name__ == "__main__":
    main()
