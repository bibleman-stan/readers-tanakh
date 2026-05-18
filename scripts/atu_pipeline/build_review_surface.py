#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_review_surface.py — Generate the per-batch editorial-review surface
from Stage-1 + Stage-2 JSONL outputs.

Per `atu-method/docs/editorial-review-protocol.md` and the corrected per-batch
protocol (auto-accept UNANIMOUS + MAJORITY; surface only ALL-DISAGREE + class-
grouped HARD firings):

  - UNANIMOUS + MAJORITY Stage 1 verdicts: auto-applicable. NOT in the surface.
  - ALL-DISAGREE / INSUFFICIENT-PASSES / MISSING-FROM-PASSES: surfaced per-verse
    with per-pass diffs.
  - HARD Stage 2 firings: grouped by `constraint_id`. One per-class decision
    block (ACCEPT / AMEND / KEEP-SOURCE) with all firing verses listed.
  - ADVISORY firings: rolled up as `constraint_id: count`. No per-verse review.
  - Recurring catalog-revision candidates (≥3 chapters firing same constraint):
    flagged for post-batch follow-up. No mid-run catalog extension.

Input:
  data/reports/atu_pipeline/<book>/chapter-NN.jsonl       (Stage 1)
  data/reports/atu_pipeline/<book>/chapter-NN-audit.jsonl (Stage 2)

Output:
  directives/replies/<directive>-<batch-name>.md

Usage:
  PYTHONIOENCODING=utf-8 py -3 scripts/atu_pipeline/build_review_surface.py \\
      --book 01-genesis \\
      --chapter-range 1-10 \\
      --batch-name torah-batch-genesis-01-10 \\
      --directive 2026-05-17-1700
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_DIR = REPO_ROOT / "data" / "reports" / "atu_pipeline"
REPLY_DIR = REPO_ROOT / "directives" / "replies"


def parse_chapter_range(s: str) -> list[int]:
    if "-" not in s:
        return [int(s)]
    lo, hi = s.split("-", 1)
    return list(range(int(lo), int(hi) + 1))


def load_stage1(book: str, chapter: int) -> list[dict]:
    path = REPORT_DIR / book / f"chapter-{chapter:02d}.jsonl"
    if not path.is_file():
        raise FileNotFoundError(f"Stage 1 JSONL not found: {path}")
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def load_stage2(book: str, chapter: int) -> list[dict]:
    path = REPORT_DIR / book / f"chapter-{chapter:02d}-audit.jsonl"
    if not path.is_file():
        raise FileNotFoundError(f"Stage 2 audit JSONL not found: {path}")
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def book_short(book_slug: str) -> str:
    return book_slug.split("-", 1)[1] if "-" in book_slug else book_slug


def aggregate(
    book: str, chapters: list[int]
) -> tuple[
    dict[str, int],                                # stage1 counts overall
    list[dict],                                    # per-chapter stage1 counts + audit counts
    list[tuple[str, dict]],                        # all-disagree verses: [(ch_verse, stage1_record)]
    dict[str, list[tuple[str, dict]]],             # hard by class: cid -> [(ch_verse, firing)]
    dict[str, int],                                # advisory by class: cid -> count
    dict[str, set[int]],                           # constraint -> chapters fired (for recurring-pattern detection)
]:
    s1_total: dict[str, int] = defaultdict(int)
    per_chapter: list[dict] = []
    all_disagree: list[tuple[str, dict]] = []
    hard_by_class: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    advisory_by_class: dict[str, int] = defaultdict(int)
    chapters_fired: dict[str, set[int]] = defaultdict(set)

    short = book_short(book)
    for ch in chapters:
        s1 = load_stage1(book, ch)
        s2 = load_stage2(book, ch)

        ch_counts = defaultdict(int)
        for r in s1:
            v = r["agreement"]
            ch_counts[v] += 1
            s1_total[v] += 1
            if v in ("ALL-DISAGREE", "INSUFFICIENT-PASSES", "MISSING-FROM-PASSES"):
                all_disagree.append((f"{short.title()} {r['verse']}", r))

        ch_hard = 0
        ch_advisory = 0
        for r in s2:
            for fr in r.get("firings", []):
                tier = fr.get("tier", "")
                cid = fr.get("constraint_id", "unknown")
                chapters_fired[cid].add(ch)
                if tier == "HARD":
                    hard_by_class[cid].append((f"{short.title()} {r['verse']}", fr))
                    ch_hard += 1
                else:
                    advisory_by_class[cid] += 1
                    ch_advisory += 1

        per_chapter.append({
            "chapter": ch,
            "verse_count": len(s1),
            "stage1": dict(ch_counts),
            "hard": ch_hard,
            "advisory": ch_advisory,
        })

    return dict(s1_total), per_chapter, all_disagree, dict(hard_by_class), dict(advisory_by_class), chapters_fired


def build_surface(
    book: str,
    chapters: list[int],
    batch_name: str,
    directive: str,
    output_path: Path,
) -> dict:
    s1_total, per_chapter, all_disagree, hard_by_class, advisory_by_class, chapters_fired = aggregate(book, chapters)

    short = book_short(book)
    total_verses = sum(p["verse_count"] for p in per_chapter)
    total_hard = sum(len(v) for v in hard_by_class.values())
    total_advisory = sum(advisory_by_class.values())

    auto_applicable = s1_total.get("UNANIMOUS", 0) + s1_total.get("MAJORITY", 0)
    review_decisions = len(all_disagree) + len(hard_by_class)

    lines: list[str] = []

    # --- Header ---
    lines.append(f"# Editorial Review — {short.title()} chapters {chapters[0]:02d}–{chapters[-1]:02d}")
    lines.append("")
    lines.append(f"**Directive:** `{directive}-{batch_name}`")
    lines.append(f"**Book:** `{book}`")
    lines.append(f"**Chapters:** {chapters[0]}–{chapters[-1]} ({len(chapters)} chapters, {total_verses} verses)")
    lines.append(f"**Generated from:** `data/reports/atu_pipeline/{book}/chapter-NN.jsonl` + `chapter-NN-audit.jsonl`")
    lines.append("")
    lines.append("**Auto-applicable** (UNANIMOUS + MAJORITY Stage 1, no Stage 2 HARD conflict): "
                 f"**{auto_applicable}/{total_verses} verses ({100 * auto_applicable / total_verses:.1f}%).** "
                 "These integrate to v2/heb verbatim from the JSONL `draft` field.")
    lines.append("")
    lines.append(f"**Decisions required:** **{review_decisions}** "
                 f"= {len(all_disagree)} ALL-DISAGREE verses + {len(hard_by_class)} HARD-firing classes.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # --- Stage 1 summary ---
    lines.append("## Stage 1 — agreement summary")
    lines.append("")
    lines.append("| Ch | Verses | UNANIMOUS | MAJORITY | ALL-DISAGREE | HARD | ADVISORY |")
    lines.append("|---|---|---|---|---|---|---|")
    for p in per_chapter:
        ch = p["chapter"]
        vc = p["verse_count"]
        s = p["stage1"]
        u = s.get("UNANIMOUS", 0)
        m = s.get("MAJORITY", 0)
        d = s.get("ALL-DISAGREE", 0) + s.get("INSUFFICIENT-PASSES", 0) + s.get("MISSING-FROM-PASSES", 0)
        lines.append(f"| {ch} | {vc} | {u} ({100*u/vc:.0f}%) | {m} | {d} | {p['hard']} | {p['advisory']} |")
    lines.append("")
    lines.append(f"**Aggregate:** UNANIMOUS {s1_total.get('UNANIMOUS',0)} · MAJORITY {s1_total.get('MAJORITY',0)} "
                 f"· ALL-DISAGREE {s1_total.get('ALL-DISAGREE',0)} "
                 f"· HARD {total_hard} · ADVISORY {total_advisory}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # --- HARD-firing classes (the action items) ---
    lines.append(f"## HARD-firing constraint classes ({len(hard_by_class)} classes, {total_hard} firings)")
    lines.append("")
    lines.append("**Per-class adjudication required.** One decision applies to all listed instances in this batch.")
    lines.append("")
    lines.append("Decision options per class:")
    lines.append("- `ACCEPT` — override the constraint for these verses (Stage-1 draft stands)")
    lines.append("- `AMEND` — re-render the listed verses with the corrective line-break pattern (specify pattern)")
    lines.append("- `KEEP-SOURCE` — drop the Stage-1 draft for these verses; preserve source line breaks")
    lines.append("")

    for i, (cid, firings) in enumerate(sorted(hard_by_class.items(), key=lambda kv: -len(kv[1])), 1):
        first_firing = firings[0][1]
        title = first_firing.get("title", "")
        precedence = first_firing.get("precedence", "?")
        lines.append(f"### {i}. `{cid}` — {title} (precedence {precedence})")
        lines.append("")
        lines.append(f"**Instances:** {len(firings)}")
        lines.append("")
        for verse_ref, fr in firings:
            reason = fr.get("reason", "").replace("\n", " ")
            lines.append(f"- **{verse_ref}** — {reason}")
            details = fr.get("details", {})
            if details:
                # Compact details rendering
                detail_str = ", ".join(f"`{k}`: {v}" for k, v in details.items() if not isinstance(v, (dict, list)))
                if detail_str:
                    lines.append(f"  - {detail_str}")
        lines.append("")
        lines.append(f"**Decision (class `{cid}`):** _BLANK_")
        lines.append("")
        lines.append("---")
        lines.append("")

    # --- ALL-DISAGREE verses (per-verse decisions) ---
    if all_disagree:
        lines.append(f"## ALL-DISAGREE verses ({len(all_disagree)} verses)")
        lines.append("")
        lines.append("**Per-verse adjudication required.** All three Opus passes diverged.")
        lines.append("")
        lines.append("Decision options per verse:")
        lines.append("- `ACCEPT-PASS-N` (1/2/3) — adopt that pass's rendering")
        lines.append("- `KEEP-SOURCE` — preserve source line breaks")
        lines.append("- `AMEND` — specify your own line-break layout")
        lines.append("")

        for verse_ref, r in all_disagree:
            lines.append(f"### {verse_ref} — `{r['agreement']}`")
            lines.append("")
            lines.append("**Source:**")
            lines.append("```")
            lines.append(r["source"])
            lines.append("```")
            for n, key in enumerate(("pass1", "pass2", "pass3"), 1):
                content = r.get(key, "").strip()
                if content:
                    # Show just the minimal-rubric-state block of the pass output
                    lines.append(f"**Pass {n}:**")
                    lines.append("```")
                    # Truncate to keep file manageable
                    if len(content) > 800:
                        content = content[:800] + "\n... [truncated]"
                    lines.append(content)
                    lines.append("```")
            lines.append(f"**Decision ({verse_ref}):** _BLANK_")
            lines.append("")
            lines.append("---")
            lines.append("")

    # --- ADVISORY rollup ---
    if advisory_by_class:
        lines.append("## ADVISORY firings (rollup, no per-verse action)")
        lines.append("")
        lines.append("| Constraint | Count | Chapters fired |")
        lines.append("|---|---|---|")
        for cid, count in sorted(advisory_by_class.items(), key=lambda kv: -kv[1]):
            chs = sorted(chapters_fired.get(cid, set()))
            chs_str = ", ".join(str(c) for c in chs)
            lines.append(f"| `{cid}` | {count} | {chs_str} |")
        lines.append("")

    # --- Catalog-revision candidates (recurring patterns) ---
    recurring = [(cid, chs) for cid, chs in chapters_fired.items() if len(chs) >= 3]
    if recurring:
        lines.append("---")
        lines.append("")
        lines.append("## Catalog-revision candidates (recurring patterns — ≥3 chapters)")
        lines.append("")
        lines.append("Per `feedback_three_lens_default_for_plans`: surface only, do NOT extend canon mid-run. Queue for post-batch §7.3 audit cycle.")
        lines.append("")
        for cid, chs in sorted(recurring, key=lambda kv: -len(kv[1])):
            chs_str = ", ".join(str(c) for c in sorted(chs))
            hard_count = len(hard_by_class.get(cid, []))
            adv_count = advisory_by_class.get(cid, 0)
            lines.append(f"- `{cid}` — HARD {hard_count} / ADVISORY {adv_count} across chapters {chs_str}")
        lines.append("")

    # --- Footer ---
    lines.append("---")
    lines.append("")
    lines.append("## Integration path (after adjudication)")
    lines.append("")
    lines.append("1. Fill `_BLANK_` decisions above.")
    lines.append("2. Tanakh-Claude reads this file, applies decisions.")
    lines.append(f"3. Auto-applicable verses ({auto_applicable}) + adjudicated decisions integrate to "
                 f"`data/text-files/v2/heb/{book}/{short}-NN.txt` on pilot branch.")
    lines.append("4. Pre-commit hook cascades (refresh_book → propagate_editorial_layers → "
                 "regenerate_english → build_books → baseline-check).")
    lines.append("5. Merge to main; push; tanakh-reader.com rebuilds.")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "verses_total": total_verses,
        "auto_applicable": auto_applicable,
        "review_decisions": review_decisions,
        "all_disagree_count": len(all_disagree),
        "hard_class_count": len(hard_by_class),
        "hard_firing_count": total_hard,
        "advisory_firing_count": total_advisory,
        "output_path": str(output_path.relative_to(REPO_ROOT)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--book", required=True, help="book slug, e.g. 01-genesis")
    ap.add_argument("--chapter-range", required=True, help="e.g. 1-10 or 5")
    ap.add_argument("--batch-name", required=True, help="e.g. torah-batch-genesis-01-10")
    ap.add_argument("--directive", required=True, help="e.g. 2026-05-17-1700")
    args = ap.parse_args()

    chapters = parse_chapter_range(args.chapter_range)
    output_path = REPLY_DIR / f"{args.directive}-{args.batch_name}.md"

    report = build_surface(args.book, chapters, args.batch_name, args.directive, output_path)
    print(f"Built: {report['output_path']}")
    print(f"  Verses: {report['verses_total']} ({report['auto_applicable']} auto-applicable)")
    print(f"  Decisions required: {report['review_decisions']} "
          f"({report['all_disagree_count']} ALL-DISAGREE verses + {report['hard_class_count']} HARD classes)")
    print(f"  HARD firings: {report['hard_firing_count']} · ADVISORY: {report['advisory_firing_count']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
