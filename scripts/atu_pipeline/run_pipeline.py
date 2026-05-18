#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_pipeline.py — Stage 3 orchestrator. Render → audit → editorial review
surface per directive 2026-05-17-1500 Item 2.

Pipeline:
  1. Pre-flight: detect Aramaic sections (Audit α Must-Fix Finding 7); skip
     Aramaic chapters with explicit BAIL marker
  2. Stage 1: render_atus.py — Opus 3-pass with agreement scoring
  3. Stage 2: audit_constraints.py — catalog audit on Stage-1 draft
  4. Stage 3: merge results into editorial-review-surface markdown per
     atu-method/docs/editorial-review-protocol.md

Architecture revisions per §7.3 pre-build audit β:
  - --pipeline-mode flag for legacy-validator coexistence (suppresses legacy
    cascade when set; Audit β Must-Fix Finding 8)
  - Auto-applied verses (UNANIMOUS Stage 1 + zero constraint violations) NOT
    in review surface (per protocol noise-reduction discipline)
  - Append-only review file when running multiple chapters into same batch
  - Constraint-violation flag surfaces verse even if Stage 1 unanimous (per
    editorial-review-protocol.md line 138)

Aramaic-detection heuristic (Audit α Must-Fix):
  Daniel 2:4b–7:28; Ezra 4:8–6:18, 7:12–26. Detected by chapter range.

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/atu_pipeline/run_pipeline.py \\
        --book 19-psalms --chapter 1 \\
        --batch-name ps-1-test [--dry-run] [--pipeline-mode]
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RENDER_SCRIPT = REPO_ROOT / "scripts" / "atu_pipeline" / "render_atus.py"
AUDIT_SCRIPT = REPO_ROOT / "scripts" / "atu_pipeline" / "audit_constraints.py"
V2_HEB = REPO_ROOT / "data" / "text-files" / "v2" / "heb"
REPORT_DIR = REPO_ROOT / "data" / "reports" / "atu_pipeline"
REPLY_DIR = REPO_ROOT / "directives" / "replies"

# Aramaic section ranges (per Audit α Must-Fix Finding 7)
ARAMAIC_RANGES = {
    "27-daniel": [(2, "from-v4"), (3, "all"), (4, "all"), (5, "all"),
                  (6, "all"), (7, "all")],
    "15-ezra": [(4, "from-v8"), (5, "all"), (6, "to-v18"), (7, "from-v12-to-v26")],
}


def is_aramaic_chapter(book_slug: str, chapter: int) -> bool:
    """Quick check: is this chapter entirely or partially Aramaic?"""
    ranges = ARAMAIC_RANGES.get(book_slug, [])
    for chap, _scope in ranges:
        if chap == chapter:
            return True
    return False


def run_render(book_slug: str, chapter: int, chunk_size: int, dry_run: bool) -> int:
    """Invoke render_atus.py as subprocess."""
    cmd = [
        sys.executable, str(RENDER_SCRIPT),
        "--book", book_slug,
        "--chapter", str(chapter),
        "--chunk-size", str(chunk_size),
    ]
    if dry_run:
        cmd.append("--dry-run")
    result = subprocess.run(cmd, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return result.returncode


def run_audit(book_slug: str, chapter: int) -> int:
    """Invoke audit_constraints.py as subprocess."""
    cmd = [
        sys.executable, str(AUDIT_SCRIPT),
        "--book", book_slug,
        "--chapter", str(chapter),
    ]
    result = subprocess.run(cmd, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return result.returncode


def load_stage1(book_slug: str, chapter: int) -> list[dict]:
    """Load per-verse JSONL from Stage 1 output."""
    path = REPORT_DIR / book_slug / f"chapter-{chapter:02d}.jsonl"
    if not path.is_file():
        return []
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def load_stage2(book_slug: str, chapter: int) -> dict[str, list[dict]]:
    """Load per-verse audit firings from Stage 2 output. Returns {verse_ref: firings}."""
    path = REPORT_DIR / book_slug / f"chapter-{chapter:02d}-audit.jsonl"
    if not path.is_file():
        return {}
    out: dict[str, list[dict]] = {}
    for ln in path.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        rec = json.loads(ln)
        out[rec["verse"]] = rec.get("firings", [])
    return out


def needs_review(stage1_rec: dict, stage2_firings: list[dict]) -> bool:
    """Per editorial-review-protocol.md:
       - Auto-apply if UNANIMOUS Stage-1 AND zero constraint violations (NO-EFFECT only firings)
       - Otherwise: surface to review
    """
    agreement = stage1_rec.get("agreement", "")
    if agreement != "UNANIMOUS":
        return True
    # Check if any firing produced a non-NO-EFFECT verdict
    for f in stage2_firings:
        if f.get("verdict") != "NO-EFFECT":
            return True
    return False


def format_review_surface(
    batch_name: str,
    chapter_results: list[tuple[str, int, list[dict], dict[str, list[dict]]]],
    pipeline_sha: str,
    catalog_sha: str,
) -> str:
    """Build the per-batch markdown review file per editorial-review-protocol.md."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    # Compute book/chapter summary across the batch
    books = sorted({bs for bs, _, _, _ in chapter_results})
    book_label = books[0] if len(books) == 1 else "+".join(books)
    chapter_nums = sorted([ch for _, ch, _, _ in chapter_results])
    chapter_label = (
        f"{chapter_nums[0]:02d}–{chapter_nums[-1]:02d}"
        if len(chapter_nums) > 1 else f"{chapter_nums[0]:02d}"
    )

    total_verses = sum(len(s1) for _, _, s1, _ in chapter_results)
    auto_applied = 0
    review_count = 0
    non_unanim = 0
    flagged = 0
    both = 0
    for _, _, s1, s2 in chapter_results:
        for r in s1:
            firings = s2.get(r["verse"], [])
            non_no_effect = [f for f in firings if f.get("verdict") != "NO-EFFECT"]
            is_unanim = r.get("agreement") == "UNANIMOUS"
            if is_unanim and not non_no_effect:
                auto_applied += 1
            else:
                review_count += 1
                if not is_unanim:
                    non_unanim += 1
                if non_no_effect:
                    flagged += 1
                if not is_unanim and non_no_effect:
                    both += 1

    pct = lambda n: f"{100*n/total_verses:.1f}%" if total_verses else "0.0%"

    out = [
        f"# Editorial Review — {book_label} chapter{'s' if len(chapter_nums)>1 else ''} {chapter_label}",
        "",
        f"**Directive:** 2026-05-17-1500-ground-up-rebuild-architecture",
        f"**Pipeline version:** {pipeline_sha}",
        f"**Constraint catalog version:** {catalog_sha}",
        f"**Generated:** {today}",
        "",
        "## Batch summary",
        "",
        f"- Chapters processed: {len(chapter_results)}",
        f"- Total verses: {total_verses}",
        f"- Auto-applied (unanimous, no constraint violation): {auto_applied} ({pct(auto_applied)})",
        f"- Editorial review surface: {review_count} ({pct(review_count)})",
        f"  - Non-unanimous: {non_unanim}",
        f"  - Constraint-violation flagged: {flagged}",
        f"  - Both (overlap): {both}",
        "",
        "## Per-chapter agreement summary",
        "",
        "| Chapter | Verses | Unanim % | Majority % | All-disagree % | Constraint flags |",
        "|---|---|---|---|---|---|",
    ]
    for bs, ch, s1, s2 in chapter_results:
        n = len(s1)
        agree_counts = {"UNANIMOUS": 0, "MAJORITY": 0, "ALL-DISAGREE": 0,
                        "MAJORITY-UNCERTAIN": 0, "INSUFFICIENT-PASSES": 0}
        for r in s1:
            a = r.get("agreement", "INSUFFICIENT-PASSES")
            agree_counts[a] = agree_counts.get(a, 0) + 1
        flagged_chap = sum(
            1 for r in s1
            if any(f.get("verdict") != "NO-EFFECT" for f in s2.get(r["verse"], []))
        )
        unanim_pct = f"{100*agree_counts['UNANIMOUS']/n:.0f}%" if n else "—"
        maj_pct = f"{100*agree_counts['MAJORITY']/n:.0f}%" if n else "—"
        dis_pct = f"{100*agree_counts['ALL-DISAGREE']/n:.0f}%" if n else "—"
        out.append(
            f"| {bs} {ch:02d} | {n} | {unanim_pct} | {maj_pct} | {dis_pct} | {flagged_chap} |"
        )
    out.append("")
    out.append("## Editorial review surface")
    out.append("")

    for bs, ch, s1, s2 in chapter_results:
        for r in s1:
            firings = s2.get(r["verse"], [])
            if not needs_review(r, firings):
                continue
            out.append(f"### {bs} {ch}:{r['verse'].split(':')[1] if ':' in r['verse'] else r['verse']}")
            out.append("")
            out.append("**Source:**")
            out.append("```")
            out.append(r.get("source", ""))
            out.append("```")
            out.append("")
            for pid in ("pass1", "pass2", "pass3"):
                out.append(f"**Pass {pid[-1]} verdict:**")
                out.append("```")
                out.append(r.get(pid) or "(no output from this pass)")
                out.append("```")
                out.append("")
            out.append(f"**Agreement:** {r.get('agreement', 'UNKNOWN')}")
            out.append("")
            non_no = [f for f in firings if f.get("verdict") != "NO-EFFECT"]
            if non_no:
                out.append("**Constraint catalog audit:**")
                for f in non_no:
                    out.append(
                        f"- `{f['constraint_id']}` ({f.get('tier','')}, "
                        f"prec={f.get('precedence','')}): **{f['verdict']}**"
                    )
                    out.append(f"  - Reason: {f.get('reason','')}")
                out.append("")
            out.append("**Editorial decision:** _[BLANK]_")
            out.append("")
            out.append("**Editor notes:** _[BLANK]_")
            out.append("")
            out.append("---")
            out.append("")

    return "\n".join(out)


def get_git_sha(path: Path) -> str:
    """Latest git SHA touching this file, short form."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h", "--", str(path)],
            cwd=str(REPO_ROOT), capture_output=True, text=True, check=False,
        )
        return result.stdout.strip() or "uncommitted"
    except Exception:
        return "unknown"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--book", required=True, help="book slug (e.g., 19-psalms)")
    p.add_argument("--chapter", type=int, required=True)
    p.add_argument("--batch-name", default=None,
                   help="batch name for review file (default: <book>-<chap>)")
    p.add_argument("--chunk-size", type=int, default=40)
    p.add_argument("--dry-run", action="store_true",
                   help="Estimate cost; skip Stage 1 dispatch and Stage 2 audit")
    p.add_argument("--pipeline-mode", action="store_true",
                   help="Set ATU_PIPELINE_MODE=1 env var to suppress legacy "
                        "validator cascade in pre-commit hooks (Audit β Finding 8)")
    p.add_argument("--skip-render", action="store_true",
                   help="Skip Stage 1; use existing JSONL (for re-running Stage 2/3)")
    p.add_argument("--skip-audit", action="store_true",
                   help="Skip Stage 2 audit; use existing audit JSONL")
    args = p.parse_args()

    if args.pipeline_mode:
        os.environ["ATU_PIPELINE_MODE"] = "1"

    # Pre-flight: Aramaic detection
    if is_aramaic_chapter(args.book, args.chapter):
        print(
            f"BAIL: {args.book} {args.chapter} is an Aramaic section; "
            f"Hebrew minimal-rubric does not apply.",
            file=sys.stderr,
        )
        return 0

    # Stage 1: render
    if not args.skip_render:
        rc = run_render(args.book, args.chapter, args.chunk_size, args.dry_run)
        if rc != 0:
            print(f"ERROR: Stage 1 render failed (exit {rc})", file=sys.stderr)
            return rc
    if args.dry_run:
        print("(dry-run: Stage 2/3 skipped)", file=sys.stderr)
        return 0

    # Stage 2: audit
    if not args.skip_audit:
        rc = run_audit(args.book, args.chapter)
        if rc != 0:
            print(f"ERROR: Stage 2 audit failed (exit {rc})", file=sys.stderr)
            return rc

    # Stage 3: editorial-review-surface
    stage1 = load_stage1(args.book, args.chapter)
    stage2 = load_stage2(args.book, args.chapter)

    pipeline_sha = get_git_sha(Path(__file__))
    catalog_sha = get_git_sha(REPO_ROOT / "canon" / "constraint_catalog_v1.md")

    batch_name = args.batch_name or f"{args.book}-{args.chapter:02d}"
    review_path = REPLY_DIR / f"2026-05-17-1500-pipeline-batch-{batch_name}.md"
    review_content = format_review_surface(
        batch_name,
        [(args.book, args.chapter, stage1, stage2)],
        pipeline_sha=pipeline_sha,
        catalog_sha=catalog_sha,
    )
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(review_content, encoding="utf-8")

    auto_applied = sum(
        1 for r in stage1
        if not needs_review(r, stage2.get(r["verse"], []))
    )
    review_count = len(stage1) - auto_applied
    print(f"\nPipeline complete → {review_path.relative_to(REPO_ROOT)}",
          file=sys.stderr)
    print(f"  Total verses: {len(stage1)}", file=sys.stderr)
    print(f"  Auto-applied (UNANIMOUS + clean audit): {auto_applied}", file=sys.stderr)
    print(f"  Editorial review surface: {review_count}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
