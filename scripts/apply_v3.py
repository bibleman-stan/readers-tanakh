#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apply_v3.py — v2-he-syntax → v3-he-colometry orchestrator.

Consumes Layer 3 colometry-validator JSON output (STRONG-tagged candidates)
and applies them mechanically to produce the v3-he-colometry tier.

Validators consumed:
  - validators/colometry/validate_speech_intro_framing.py  (Rule H5 — speech framing)
  - validators/colometry/validate_construct_chain.py       (Rule H2 — construct chain)

Both validators emit:
  STRONG-MERGE-CANDIDATE  — high-confidence merge (e.g. short speech frame isolated)
  STRONG-SPLIT-CANDIDATE  — high-confidence split (e.g. long speech frame + speech
                             content on same line; split_at_position_N action)
  REVIEW-REQUIRED         — editorial judgment required

Adoption gate (canon §7 proposed-rule adoption protocol):
  Layer 3 validators currently have zero STRONG findings on Jonah that clear
  the ≥80% clean-rate threshold.  ADOPTED_VALIDATORS is intentionally empty.
  When ADOPTED_VALIDATORS is empty, v3-he-colometry files are verbatim copies
  of v2-he-syntax files — the tier-architecture commitment is preserved (v3
  exists as a distinct tier even when it is a passthrough) and the report
  documents explicitly that v3 = v2 pending Layer 3 adoption.

Conflict-resolution note (per canon §1 Decision Procedure, step 4):
  When a Layer 3 split fires on the same line as a previously-applied Layer 1
  merge (which may surface as a REVIEW-REQUIRED item if carried forward), the
  merge wins.  The report surfaces these conflicts explicitly so Stan can
  adjudicate them rather than having the script silently apply the merge.

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/apply_v3.py --book 05-jonah
    PYTHONIOENCODING=utf-8 py -3 scripts/apply_v3.py --book 05-jonah --dry-run
    PYTHONIOENCODING=utf-8 py -3 scripts/apply_v3.py --book 05-jonah --report-only
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
# Layer 3 validators are all currently unadopted.  Update this list as
# validators clear the adoption protocol per canon §7.
# ---------------------------------------------------------------------------
ADOPTED_VALIDATORS: list[str] = [
    # "validate_speech_intro_framing",  # adoption pending clean-rate audit on Jonah
    # "validate_construct_chain",       # adoption pending clean-rate audit on Jonah
]

# ---------------------------------------------------------------------------
# Validator registry — (script_path_relative_to_repo, validator_name_key)
# These are all Layer 3 validators for v3.
# ---------------------------------------------------------------------------
LAYER_3_VALIDATORS: list[tuple[str, str]] = [
    (
        "validators/colometry/validate_speech_intro_framing.py",
        "validate_speech_intro_framing",
    ),
    (
        "validators/colometry/validate_construct_chain.py",
        "validate_construct_chain",
    ),
]

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
V2_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "he-syntax"
V3_DIR = REPO_ROOT / "data" / "text-files" / "v3" / "he-colometry"
REPORTS_DIR = REPO_ROOT / "data" / "reports" / "v3"

INPUT_TIER_LABEL = "v2-he-syntax"
OUTPUT_TIER_LABEL = "v3-he-colometry"
LAYER_LABEL = "Layer 3"


# ---------------------------------------------------------------------------
# Conflict detection — Layer 1 merge vs. Layer 3 split
# ---------------------------------------------------------------------------

def detect_merge_split_conflicts(
    strong_findings: list[dict],
    review_findings: list[dict],
) -> list[dict]:
    """Identify lines where a Layer 3 split candidate conflicts with a prior merge.

    A conflict is defined as: a STRONG-SPLIT-CANDIDATE from a Layer 3 validator
    fires on a line that also carries a REVIEW-REQUIRED item whose tag is
    STRONG-MERGE-CANDIDATE from a Layer 1 validator (carried forward through the
    review queue because Layer 1 was unadopted, or because the merge was flagged
    for judgment).

    Per canon §1 Decision Procedure step 4, the merge wins.  This function
    returns the conflicting pairs so they can be surfaced in the report rather
    than silently resolved.

    Returns
    -------
    list[dict]
        Each entry has:
          "line"         : int — the line number where conflict occurs
          "split_finding": dict — the STRONG-SPLIT-CANDIDATE finding
          "merge_finding": dict — the conflicting STRONG-MERGE-CANDIDATE finding
          "resolution"   : str — always "merge_wins" (canon §1 step 4)
    """
    # Collect split-candidate line numbers from strong findings.
    split_lines: dict[int, dict] = {}
    for finding in strong_findings:
        tag = finding.get("tag", "")
        line_no = finding.get("line")
        if tag == "STRONG-SPLIT-CANDIDATE" and line_no is not None:
            split_lines[line_no] = finding

    if not split_lines:
        return []

    # Collect merge-candidate line numbers from review findings.
    # Review findings include unadopted STRONG-MERGE-CANDIDATEs from Layer 1.
    merge_lines: dict[int, dict] = {}
    for finding in review_findings:
        tag = finding.get("tag", "")
        line_no = finding.get("line")
        if tag == "STRONG-MERGE-CANDIDATE" and line_no is not None:
            merge_lines[line_no] = finding

    conflicts: list[dict] = []
    for line_no, split_finding in split_lines.items():
        if line_no in merge_lines:
            conflicts.append({
                "line": line_no,
                "split_finding": split_finding,
                "merge_finding": merge_lines[line_no],
                "resolution": "merge_wins",
            })

    return conflicts


def _format_conflict_block(conflict: dict, conflict_num: int) -> str:
    """Format one merge-vs-split conflict as a markdown block."""
    line_no = conflict["line"]
    split_f = conflict["split_finding"]
    merge_f = conflict["merge_finding"]
    resolution = conflict["resolution"]

    return (
        f"### Conflict {conflict_num}: line {line_no}\n"
        f"- **Layer 3 split** (validator: {split_f.get('_validator', '?')}, "
        f"rule {split_f.get('rule_id', '?')}): {split_f.get('brief', '')}\n"
        f"- **Prior merge** (validator: {merge_f.get('_validator', '?')}, "
        f"rule {merge_f.get('rule_id', '?')}): {merge_f.get('brief', '')}\n"
        f"- Resolution: **{resolution}** (canon §1 Decision Procedure step 4 — "
        f"merge-override beats split-trigger at same line)\n"
        f"- Action required: verify the merge is correct; if the Layer 3 split "
        f"is meritorious, override the Layer 1 merge in v4-editorial.\n"
    )


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
    """Apply findings to one chapter file; write v3 and reports.

    Returns a stats dict.
    """
    chapter_stem = chapter_file.stem  # e.g. "jonah-01"
    lines = chapter_file.read_text(encoding="utf-8").splitlines()
    input_line_count = len(lines)

    # Detect merge-vs-split conflicts before applying mutations.
    conflicts = detect_merge_split_conflicts(strong_findings, review_findings)

    if all_adopted and not report_only and strong_findings:
        mutated_lines, applied_changes = apply_mutations_to_lines(lines, strong_findings)
    else:
        mutated_lines = list(lines)
        applied_changes = []

    output_line_count = len(mutated_lines)

    no_adopted_note = (
        f"All {LAYER_LABEL} validators are currently unadopted "
        f"(below ≥80% clean-rate threshold per canon §7). "
        f"No mutations were applied. The {OUTPUT_TIER_LABEL} file is a verbatim "
        f"copy of {INPUT_TIER_LABEL}. "
        f"This is the intended tier-architecture behavior: v3 exists as a distinct "
        f"tier even when it is a passthrough, preserving the pipeline structure for "
        f"when Layer 3 validators reach adoption."
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

    # Append conflict section to the chapter report if any conflicts exist.
    if conflicts:
        conflict_lines: list[str] = [
            "\n## Merge-vs-split conflicts (canon §1 step 4)\n",
            (
                "The following lines have a Layer 3 split candidate conflicting with "
                "a prior Layer 1 merge.  Per canon §1 Decision Procedure step 4, "
                "merge wins.  Review these in v4-editorial.\n"
            ),
        ]
        for i, conflict in enumerate(conflicts, start=1):
            conflict_lines.append(_format_conflict_block(conflict, i))
        report_text = report_text + "\n" + "\n".join(conflict_lines)

    review_text = build_review_report(
        book=book,
        chapter_stem=chapter_stem,
        review_items=review_findings,
        layer_label=LAYER_LABEL,
    )

    if not dry_run and not report_only:
        out_dir = V3_DIR / book
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / chapter_file.name
        out_file.write_text("\n".join(mutated_lines) + "\n", encoding="utf-8")

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
        "conflicts": len(conflicts),
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
        help=(
            "Book folder name, e.g. '05-jonah'. "
            "Must exist under v2-he-syntax/."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show what would be applied but do not write v3-he-colometry files.",
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

    # Validate book directory exists in v2-he-syntax.
    book_v2_dir = V2_DIR / book
    if not book_v2_dir.exists():
        print(
            f"ERROR: {INPUT_TIER_LABEL} book directory not found: {book_v2_dir}",
            file=sys.stderr,
        )
        sys.exit(2)

    chapter_files = resolve_chapter_files(V2_DIR, book)
    if not chapter_files:
        print(f"ERROR: No .txt files found under {book_v2_dir}", file=sys.stderr)
        sys.exit(2)

    adopted_set = set(ADOPTED_VALIDATORS)
    all_adopted = len(adopted_set) > 0

    # -----------------------------------------------------------------------
    # Step 1: Run validators and collect JSON.
    # -----------------------------------------------------------------------
    print(f"apply_v3.py — book: {book}")
    print(f"Mode: {'dry-run' if dry_run else 'report-only' if report_only else 'apply'}")
    print(f"Adopted validators: {list(adopted_set) or '(none)'}")
    if not all_adopted:
        print(
            f"  (No {LAYER_LABEL} validators adopted — "
            f"{OUTPUT_TIER_LABEL} will be a verbatim copy of {INPUT_TIER_LABEL})"
        )
    print()
    print(f"Running {LAYER_LABEL} validators…")

    validator_outputs: list[tuple[str, dict]] = []
    for script_rel, validator_name in LAYER_3_VALIDATORS:
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
    total_conflicts = 0
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
        total_conflicts += stats["conflicts"]

        action_label = "would apply" if (dry_run or report_only) else "applied"
        conflict_note = (
            f", {stats['conflicts']} merge/split conflict(s)"
            if stats["conflicts"]
            else ""
        )
        print(
            f"  {stats['chapter']}: "
            f"{stats['input_lines']} → {stats['output_lines']} lines, "
            f"{stats['applied']} changes {action_label}, "
            f"{stats['review']} deferred"
            f"{conflict_note}"
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
    print(f"  Chapters processed      : {len(chapter_stats)}")
    print(f"  Total changes           : {total_applied}")
    print(f"  Deferred to v4          : {total_review}")
    print(f"  Merge/split conflicts   : {total_conflicts}")
    if dry_run:
        print("  Mode: DRY-RUN — no files written.")
    elif report_only:
        print("  Mode: REPORT-ONLY — no files written.")
    else:
        if all_adopted:
            v3_book_dir = V3_DIR / book
            print(f"  {OUTPUT_TIER_LABEL} output: {v3_book_dir}")
            report_book_dir = REPORTS_DIR / book
            print(f"  Reports written to: {report_book_dir}")
        else:
            print(
                f"  NOTE: All {LAYER_LABEL} validators unadopted — "
                f"{OUTPUT_TIER_LABEL} files are verbatim copies of {INPUT_TIER_LABEL}. "
                f"Reports written for adoption-protocol review."
            )
            v3_book_dir = V3_DIR / book
            print(f"  {OUTPUT_TIER_LABEL} output: {v3_book_dir}")
            report_book_dir = REPORTS_DIR / book
            print(f"  Reports written to: {report_book_dir}")
    print("=" * 60)

    sys.exit(1 if (total_applied > 0 or total_review > 0) else 0)


if __name__ == "__main__":
    main()
