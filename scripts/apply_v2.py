#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apply_v2.py — v1-he-baseline → v2-he-syntax orchestrator.

Consumes Layer 1 syntax-validator JSON output (STRONG-tagged candidates) and
applies them mechanically to produce the v2-he-syntax tier.

Validators consumed:
  - validators/syntax/validate_line_final_tokens.py  (Layer 1 stranded-prefix rules)
  - validators/syntax/validate_maqqef_integrity.py   (Rule H1 maqqef-group integrity)

Adoption gate (canon §7 proposed-rule adoption protocol):
  Validators below the ≥80% clean threshold must NOT have their STRONG output
  applied.  Only validators listed in ADOPTED_VALIDATORS below are active.
  All others run in report-only mode — their findings appear in the report but
  no file mutations are made.

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/apply_v2.py --book 05-jonah
    PYTHONIOENCODING=utf-8 py -3 scripts/apply_v2.py --book 05-jonah --dry-run
    PYTHONIOENCODING=utf-8 py -3 scripts/apply_v2.py --book 05-jonah --report-only
"""

import argparse
import sys
from pathlib import Path

# Shared pipeline logic lives in scripts/lib/apply_pipeline.py.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.apply_pipeline import (
    aggregate_findings,
    apply_mutations_to_lines,
    build_chapter_report,
    build_review_report,
    file_key,
    resolve_chapter_files,
    run_validator,
)

# ---------------------------------------------------------------------------
# Adoption gate — validators approved for mechanical application (≥80% clean).
# Update this list as validators clear the adoption protocol per canon §7.
# ---------------------------------------------------------------------------
ADOPTED_VALIDATORS: list[str] = [
    # Both Layer 1 validators passed adoption gate 2026-04-26 after bug-fix re-run
    # against Jonah. Per validators-jonah-first-run.md re-run section:
    #   - validate_line_final_tokens: 100% real-positive (2/2 STRONG findings on
    #     Jonah 1:3 lines 14, 17 — the canonical מִלִּפְנֵי orphans).
    #   - validate_maqqef_integrity: 0 findings on Jonah (no maqqef-group splits;
    #     trivially passes the false-positive bar).
    "validate_line_final_tokens",
    "validate_maqqef_integrity",
]

# ---------------------------------------------------------------------------
# Validator registry — (script_path_relative_to_repo, validator_name_key)
# These are all Layer 1 validators for v2.
# ---------------------------------------------------------------------------
LAYER_1_VALIDATORS: list[tuple[str, str]] = [
    ("validators/syntax/validate_line_final_tokens.py", "validate_line_final_tokens"),
    ("validators/syntax/validate_maqqef_integrity.py", "validate_maqqef_integrity"),
]

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "he-syntax"
REPORTS_DIR = REPO_ROOT / "data" / "reports" / "v2"

# Parallel per-word layer files were emitted by parse_teamim.py in lockstep
# with v1-he-baseline. When v2 merges Hebrew cola, the parallel layers must
# follow the same line-number mutations to preserve cross-layer alignment.
# Per-word files use " | " as the orthographic-word separator (per
# scripts/ingest_tahot.py ENG_WORD_SEP); Hebrew uses plain space.
PARALLEL_LAYERS: list[tuple[str, str, str]] = [
    # (v1 input path relative to data/text-files/, v2 output path, merge separator)
    ("v1/eng-interlinear", "v2/eng-interlinear", " | "),
    ("v1/eng-gloss",       "v2/eng-gloss",       " "),
    ("v1/translit",        "v2/translit",        " | "),
]

INPUT_TIER_LABEL = "v1-he-baseline"
OUTPUT_TIER_LABEL = "v2-he-syntax"
LAYER_LABEL = "Layer 1"


# ---------------------------------------------------------------------------
# Per-chapter processor
# ---------------------------------------------------------------------------

def process_chapter(
    chapter_file: Path,
    strong_findings: list[dict],
    review_findings: list[dict],
    book: str,
    dry_run: bool,
    report_only: bool,
    all_adopted: bool,
) -> dict:
    """Apply findings to one chapter file; write v2 and reports.

    Returns a stats dict.
    """
    chapter_stem = chapter_file.stem  # e.g. "jonah-01"
    lines = chapter_file.read_text(encoding="utf-8").splitlines()
    input_line_count = len(lines)

    if all_adopted and not report_only and strong_findings:
        mutated_lines, applied_changes = apply_mutations_to_lines(lines, strong_findings)
    else:
        mutated_lines = list(lines)
        applied_changes = []

    output_line_count = len(mutated_lines)

    no_adopted_note = (
        f"All {LAYER_LABEL} validators are currently unadopted "
        f"(below ≥80% clean-rate threshold per canon §7). "
        f"No mutations were applied. The {OUTPUT_TIER_LABEL} file is identical to "
        f"{INPUT_TIER_LABEL}. This preserves tier-architecture integrity until "
        f"validators pass adoption."
    )

    report_text = build_chapter_report(
        book=book,
        chapter_stem=chapter_stem,
        input_tier_label=INPUT_TIER_LABEL,
        output_tier_label=OUTPUT_TIER_LABEL,
        input_line_count=input_line_count,
        output_line_count=output_line_count,
        applied_changes=applied_changes,
        review_items=review_findings,
        all_adopted=all_adopted,
        no_adopted_note=no_adopted_note,
    )
    review_text = build_review_report(
        book=book,
        chapter_stem=chapter_stem,
        review_items=review_findings,
        layer_label=LAYER_LABEL,
    )

    # Propagate the same line-number mutations to parallel per-word layer files
    # (eng-interlinear, eng-gloss, translit) so cross-layer alignment is
    # preserved when the build cascade picks v2 for Hebrew. See PARALLEL_LAYERS.
    parallel_outputs: list[tuple[Path, list[str]]] = []
    if all_adopted and not report_only and applied_changes:
        text_files_root = REPO_ROOT / "data" / "text-files"
        for v1_layer_name, v2_layer_name, sep in PARALLEL_LAYERS:
            parallel_v1_file = (
                text_files_root / v1_layer_name / book / chapter_file.name
            )
            if not parallel_v1_file.exists():
                continue
            parallel_lines = parallel_v1_file.read_text(encoding="utf-8").splitlines()
            parallel_mutated, _ = apply_mutations_to_lines(
                parallel_lines, strong_findings, separator=sep
            )
            parallel_v2_file = (
                text_files_root / v2_layer_name / book / chapter_file.name
            )
            parallel_outputs.append((parallel_v2_file, parallel_mutated))

    if not dry_run and not report_only:
        out_dir = V2_DIR / book
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / chapter_file.name
        out_file.write_text("\n".join(mutated_lines) + "\n", encoding="utf-8")

        for parallel_v2_file, parallel_mutated in parallel_outputs:
            parallel_v2_file.parent.mkdir(parents=True, exist_ok=True)
            parallel_v2_file.write_text(
                "\n".join(parallel_mutated) + "\n", encoding="utf-8"
            )

        report_dir = REPORTS_DIR / book
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / f"{chapter_stem}.md"
        report_file.write_text(report_text, encoding="utf-8")

        if review_text:
            review_file = report_dir / f"{chapter_stem}-review.md"
            review_file.write_text(review_text, encoding="utf-8")

    return {
        "chapter": chapter_stem,
        "input_lines": input_line_count,
        "output_lines": output_line_count,
        "applied": len(applied_changes),
        "review": len(review_findings),
        "report": report_text,
        "review_report": review_text,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--book",
        required=True,
        metavar="BOOK",
        help="Book folder name, e.g. '05-jonah'. Must exist under v1-he-baseline/.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show what would be applied but do not write v2-he-syntax files.",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        default=False,
        help=(
            "Emit markdown report of what would be applied without writing files. "
            "Use for adoption-protocol pre-application review."
        ),
    )
    args = parser.parse_args()

    book = args.book
    dry_run: bool = args.dry_run
    report_only: bool = args.report_only

    # Validate book directory exists in v1-he-baseline.
    book_v1_dir = V1_DIR / book
    if not book_v1_dir.exists():
        print(
            f"ERROR: {INPUT_TIER_LABEL} book directory not found: {book_v1_dir}",
            file=sys.stderr,
        )
        sys.exit(2)

    chapter_files = resolve_chapter_files(V1_DIR, book)
    if not chapter_files:
        print(f"ERROR: No .txt files found under {book_v1_dir}", file=sys.stderr)
        sys.exit(2)

    adopted_set = set(ADOPTED_VALIDATORS)
    all_adopted = len(adopted_set) > 0

    # -----------------------------------------------------------------------
    # Step 1: Run validators and collect JSON.
    # -----------------------------------------------------------------------
    print(f"apply_v2.py — book: {book}")
    print(f"Mode: {'dry-run' if dry_run else 'report-only' if report_only else 'apply'}")
    print(f"Adopted validators: {list(adopted_set) or '(none)'}")
    print()
    print(f"Running {LAYER_LABEL} validators…")

    validator_outputs: list[tuple[str, dict]] = []
    for script_rel, validator_name in LAYER_1_VALIDATORS:
        print(f"  {validator_name}…", end=" ", flush=True)
        result = run_validator(script_rel, book, REPO_ROOT)
        if result is not None:
            for f in result.get("findings", []):
                f["_validator"] = validator_name
            validator_outputs.append((validator_name, result))
            n = result.get("summary", {}).get("total_findings", 0)
            adopted_label = "adopted" if validator_name in adopted_set else "unadopted"
            print(f"{n} findings [{adopted_label}]")
        else:
            print("FAILED (skipped)")

    print()

    # -----------------------------------------------------------------------
    # Step 2: Aggregate findings by file.
    # -----------------------------------------------------------------------
    strong_by_file, review_by_file = aggregate_findings(
        validator_outputs, REPO_ROOT, adopted_set
    )

    # -----------------------------------------------------------------------
    # Step 3: Process each chapter.
    # -----------------------------------------------------------------------
    total_applied = 0
    total_review = 0
    chapter_stats: list[dict] = []

    for chapter_file in chapter_files:
        fkey = file_key(chapter_file, REPO_ROOT)
        ch_strong = strong_by_file.get(fkey, [])
        ch_review = review_by_file.get(fkey, [])

        stats = process_chapter(
            chapter_file=chapter_file,
            strong_findings=ch_strong,
            review_findings=ch_review,
            book=book,
            dry_run=dry_run,
            report_only=report_only,
            all_adopted=all_adopted,
        )
        chapter_stats.append(stats)
        total_applied += stats["applied"]
        total_review += stats["review"]

        action_label = "would apply" if (dry_run or report_only) else "applied"
        print(
            f"  {stats['chapter']}: "
            f"{stats['input_lines']} → {stats['output_lines']} lines, "
            f"{stats['applied']} changes {action_label}, "
            f"{stats['review']} deferred"
        )

        if dry_run or report_only:
            print()
            print(stats["report"])
            if stats["review_report"]:
                print(stats["review_report"])

    # -----------------------------------------------------------------------
    # Step 4: Summary.
    # -----------------------------------------------------------------------
    print()
    print("=" * 60)
    print(f"Summary — {book}")
    print(f"  Chapters processed : {len(chapter_stats)}")
    print(f"  Total changes      : {total_applied}")
    print(f"  Deferred to v4     : {total_review}")
    if dry_run:
        print("  Mode: DRY-RUN — no files written.")
    elif report_only:
        print("  Mode: REPORT-ONLY — no files written.")
    else:
        if all_adopted:
            v2_book_dir = V2_DIR / book
            print(f"  {OUTPUT_TIER_LABEL} output: {v2_book_dir}")
            report_book_dir = REPORTS_DIR / book
            print(f"  Reports written to: {report_book_dir}")
        else:
            print(
                f"  NOTE: All {LAYER_LABEL} validators unadopted — {OUTPUT_TIER_LABEL} files are "
                f"copies of {INPUT_TIER_LABEL} (no mutations). "
                f"Reports written for adoption-protocol review."
            )
            v2_book_dir = V2_DIR / book
            print(f"  {OUTPUT_TIER_LABEL} output: {v2_book_dir}")
            report_book_dir = REPORTS_DIR / book
            print(f"  Reports written to: {report_book_dir}")
    print("=" * 60)

    sys.exit(1 if (total_applied > 0 or total_review > 0) else 0)


if __name__ == "__main__":
    main()
