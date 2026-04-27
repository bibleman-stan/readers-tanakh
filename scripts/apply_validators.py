#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apply_validators.py — Single orchestrator for v1/he-baseline → v2/he pipeline.

Runs adopted validators, filters to STRONG findings per the adopted tag-set,
applies mechanical mutations to v1/he-baseline text, and writes v2/he output
plus per-chapter markdown reports.

ADOPTED_VALIDATORS is the single gate: a dict[str, set[str]] mapping
validator name → set of tag strings that are cleared for mechanical
application.  Findings with tags not in the set are demoted to
REVIEW-REQUIRED regardless of the validator's own tag.

Phase 1 adoption set:
  validate_maqqef_integrity        — all STRONG tags
  validate_line_final_tokens       — all STRONG tags
  validate_speech_intro_framing    — STRONG-MERGE-CANDIDATE only
  validate_wayehi_protasis         — STRONG-MERGE-CANDIDATE only

NOT adopted yet:
  validate_construct_chain         — subcase fix pending in parallel agent
  validate_discourse_particles     — needs multi-book evidence
  validate_complement_integrity    — needs multi-book evidence

Safety: if v2/he/<book>/<chapter>.txt already exists, the script diffs
it against what the pipeline would produce.  If the diff contains lines
not derivable from v1 + mechanical apply (i.e., hand-edits), it aborts
unless --force is given.

Sweep-scale audit warning (canon §7): if ≥5 changes are applied in a
single run, a WARNING is printed.

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/apply_validators.py --book 05-jonah
    PYTHONIOENCODING=utf-8 py -3 scripts/apply_validators.py --all-books
    PYTHONIOENCODING=utf-8 py -3 scripts/apply_validators.py --book 05-jonah --dry-run
    PYTHONIOENCODING=utf-8 py -3 scripts/apply_validators.py --book 05-jonah --report-only
    PYTHONIOENCODING=utf-8 py -3 scripts/apply_validators.py --book 05-jonah --force
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Repo layout
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "he"
REPORTS_DIR = REPO_ROOT / "data" / "reports" / "apply"

INPUT_TIER_LABEL = "v1-he-baseline"
OUTPUT_TIER_LABEL = "v2-he"

# ---------------------------------------------------------------------------
# Adoption gate — dict[validator_name, set[allowed_tags]]
#
# Only findings whose (validator_name, tag) pair clears this gate are applied
# mechanically.  All others go to REVIEW-REQUIRED.
#
# Update this dict as validators clear the ≥80% clean-rate adoption protocol
# per canon §7.  Do NOT update validators/.baseline.json from this script;
# run:  PYTHONIOENCODING=utf-8 py -3 validators/run_all.py --update-baseline
# ---------------------------------------------------------------------------

ADOPTED_VALIDATORS: dict[str, set[str]] = {
    "validate_maqqef_integrity": {
        "STRONG-MERGE-CANDIDATE",
        "STRONG-SPLIT-CANDIDATE",
    },
    "validate_line_final_tokens": {
        "STRONG-MERGE-CANDIDATE",
        "STRONG-SPLIT-CANDIDATE",
    },
    "validate_speech_intro_framing": {
        "STRONG-MERGE-CANDIDATE",
        # STRONG-SPLIT-CANDIDATE not yet adopted for this validator
    },
    "validate_wayehi_protasis": {
        "STRONG-MERGE-CANDIDATE",
        # STRONG-SPLIT-CANDIDATE not yet adopted for this validator
    },
}

# ---------------------------------------------------------------------------
# Validator registry — (script_path_relative_to_repo, validator_name_key)
# All validators that this script may run.  Unadopted validators still run
# so their REVIEW-REQUIRED findings appear in reports.
# ---------------------------------------------------------------------------

ALL_VALIDATORS: list[tuple[str, str]] = [
    ("validators/syntax/validate_maqqef_integrity.py",     "validate_maqqef_integrity"),
    ("validators/syntax/validate_line_final_tokens.py",    "validate_line_final_tokens"),
    ("validators/colometry/validate_speech_intro_framing.py", "validate_speech_intro_framing"),
    ("validators/colometry/validate_wayehi_protasis.py",   "validate_wayehi_protasis"),
    # Not yet adopted — run for reporting only:
    ("validators/colometry/validate_construct_chain.py",   "validate_construct_chain"),
    ("validators/syntax/validate_discourse_particles.py",  "validate_discourse_particles"),
    ("validators/syntax/validate_complement_integrity.py", "validate_complement_integrity"),
]


# ---------------------------------------------------------------------------
# Subprocess helper — run one validator
# ---------------------------------------------------------------------------

def run_validator(script_rel: str, book: str) -> dict | None:
    """Invoke a validator with --json --book <book> from v1/he-baseline.

    Returns parsed JSON doc or None on failure.
    Validators exit 0 (clean) or 1 (findings) — both are success.
    Exit 2 is a setup error → None.
    """
    path = REPO_ROOT / script_rel
    if not path.exists():
        print(f"  [WARN] Validator not found: {path}", file=sys.stderr)
        return None

    cmd = [sys.executable, str(path), "--json", "--book", book]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )
    except Exception as exc:
        print(f"  [ERROR] Could not run {script_rel}: {exc}", file=sys.stderr)
        return None

    if result.returncode == 2:
        print(f"  [ERROR] Validator setup error (exit 2): {script_rel}", file=sys.stderr)
        if result.stderr.strip():
            print(f"    stderr: {result.stderr.strip()}", file=sys.stderr)
        return None

    stdout = result.stdout.strip()
    if not stdout:
        return {"validator": script_rel, "findings": [], "summary": {"total_findings": 0}}

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        print(f"  [ERROR] JSON parse failure from {script_rel}: {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Finding aggregation — tag-level filtering via ADOPTED_VALIDATORS
# ---------------------------------------------------------------------------

def aggregate_findings(
    validator_outputs: list[tuple[str, dict]],
    adopted_map: dict[str, set[str]],
) -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
    """Partition findings into STRONG (apply-ready) and REVIEW-REQUIRED queues.

    Parameters
    ----------
    validator_outputs : list of (validator_name, doc)
    adopted_map : dict[str, set[str]]
        Maps validator name → set of tag strings cleared for mechanical apply.
        A finding must BOTH come from an adopted validator AND have an
        adopted tag to enter the strong queue.

    Returns
    -------
    (strong_by_file, review_by_file) : dicts mapping repo-relative file path
        strings to lists of finding dicts (augmented with _validator and
        optionally _unadopted / _unadopted_tag).
    """
    strong_by_file: dict[str, list[dict]] = defaultdict(list)
    review_by_file: dict[str, list[dict]] = defaultdict(list)

    for validator_name, doc in validator_outputs:
        adopted_tags = adopted_map.get(validator_name)  # None if not adopted at all
        findings = doc.get("findings", [])

        for finding in findings:
            file_str = finding.get("file", "")
            if not file_str:
                continue

            # Remap file path from v1/he-baseline → use as-is for lookup key.
            # The key must match what resolve_chapter_files produces via file_key().
            tag = finding.get("tag", "")
            action = finding.get("applied_action")

            is_review = (tag == "REVIEW-REQUIRED") or (action is None)

            if is_review:
                review_by_file[file_str].append({**finding, "_validator": validator_name})
            elif adopted_tags is not None and tag in adopted_tags:
                # Adopted validator + adopted tag → mechanical apply.
                strong_by_file[file_str].append({**finding, "_validator": validator_name})
            elif adopted_tags is None:
                # Validator not adopted at all → demote to review.
                review_by_file[file_str].append(
                    {**finding, "_validator": validator_name, "_unadopted": True}
                )
            else:
                # Validator adopted but this specific tag is not in the adopted set.
                review_by_file[file_str].append(
                    {**finding, "_validator": validator_name, "_unadopted_tag": True}
                )

    return dict(strong_by_file), dict(review_by_file)


# ---------------------------------------------------------------------------
# Mutation engine — apply STRONG findings to line list
# ---------------------------------------------------------------------------

def apply_mutations_to_lines(
    lines: list[str],
    strong_findings: list[dict],
    separator: str = " ",
) -> tuple[list[str], list[dict]]:
    """Apply STRONG-MERGE-CANDIDATE and STRONG-SPLIT-CANDIDATE findings.

    Processing order: HIGH line-number to LOW so earlier mutations don't
    invalidate later line-number references.

    Conflict rule (canon §1 Decision Procedure step 4):
    merge_with_* BEATS split_at_position_N when both fire on the same line.

    Sentinel compaction: consumed lines are replaced with \\x00 so that list
    length is preserved during the reverse pass; compacted out at the end.

    Returns (mutated_lines, applied_changes).
    """
    _CONSUMED = "\x00"

    # Build per-line-number dict: keep highest-priority action only.
    by_line: dict[int, dict] = {}
    for finding in strong_findings:
        line_no = finding.get("line")
        if line_no is None:
            continue
        action = finding.get("applied_action")
        if action is None:
            continue

        existing = by_line.get(line_no)
        if existing is None:
            by_line[line_no] = finding
        else:
            existing_action = existing.get("applied_action", "")
            # Merge beats split at same line.
            if "merge" in action and "merge" not in existing_action:
                by_line[line_no] = finding

    # Sort HIGH to LOW.
    sorted_findings = sorted(by_line.values(), key=lambda f: f["line"], reverse=True)

    work = list(lines)
    applied: list[dict] = []

    for finding in sorted_findings:
        line_no = finding["line"]       # 1-indexed
        action = finding.get("applied_action", "")
        idx = line_no - 1              # 0-indexed

        if idx < 0 or idx >= len(work):
            continue

        if action == "merge_with_next":
            next_idx = idx + 1
            while next_idx < len(work) and work[next_idx] == _CONSUMED:
                next_idx += 1
            if next_idx >= len(work):
                continue

            before_current = work[idx]
            before_next = work[next_idx]
            merged = before_current.rstrip() + separator + before_next.lstrip()
            applied.append({
                "finding": finding,
                "action": action,
                "before_lines": {line_no: before_current, next_idx + 1: before_next},
                "after_lines": {line_no: merged},
            })
            work[idx] = merged
            work[next_idx] = _CONSUMED

        elif action == "merge_with_previous":
            prev_idx = idx - 1
            while prev_idx >= 0 and work[prev_idx] == _CONSUMED:
                prev_idx -= 1
            if prev_idx < 0:
                continue

            before_current = work[idx]
            before_prev = work[prev_idx]
            merged = before_prev.rstrip() + separator + before_current.lstrip()
            applied.append({
                "finding": finding,
                "action": action,
                "before_lines": {prev_idx + 1: before_prev, line_no: before_current},
                "after_lines": {prev_idx + 1: merged},
            })
            work[prev_idx] = merged
            work[idx] = _CONSUMED

        elif action.startswith("split_at_position_"):
            try:
                position = int(action.split("split_at_position_")[1])
            except (IndexError, ValueError):
                continue
            before = work[idx]
            tokens = before.split()
            split_after = position + 1
            if split_after <= 0 or split_after >= len(tokens):
                continue
            line_a = " ".join(tokens[:split_after])
            line_b = " ".join(tokens[split_after:])
            if not line_b.strip():
                continue
            applied.append({
                "finding": finding,
                "action": action,
                "before_lines": {line_no: before},
                "after_lines": {line_no: line_a, line_no + 0.5: line_b},
            })
            work[idx] = line_a
            work.insert(idx + 1, line_b)

    final = [ln for ln in work if ln != _CONSUMED]
    return final, applied


# ---------------------------------------------------------------------------
# Merge-vs-split conflict detection (ported from retired apply_v3.py)
# ---------------------------------------------------------------------------

def detect_merge_split_conflicts(
    strong_findings: list[dict],
    review_findings: list[dict],
) -> list[dict]:
    """Identify lines where a split candidate conflicts with a prior merge finding."""
    split_lines: dict[int, dict] = {}
    for finding in strong_findings:
        tag = finding.get("tag", "")
        line_no = finding.get("line")
        if tag == "STRONG-SPLIT-CANDIDATE" and line_no is not None:
            split_lines[line_no] = finding

    if not split_lines:
        return []

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


# ---------------------------------------------------------------------------
# File-system helpers
# ---------------------------------------------------------------------------

def resolve_chapter_files(book: str) -> list[Path]:
    """Return sorted list of .txt files for a book under v1/he-baseline."""
    book_dir = V1_DIR / book
    if not book_dir.exists():
        return []
    return sorted(book_dir.glob("*.txt"))


def file_key(chapter_file: Path) -> str:
    """Repo-root-relative forward-slash path string — matches validator output."""
    return str(chapter_file.relative_to(REPO_ROOT)).replace("\\", "/")


def v2_path_for(v1_file: Path, book: str) -> Path:
    """Return the v2/he target path for a given v1/he-baseline source file."""
    return V2_DIR / book / v1_file.name


# ---------------------------------------------------------------------------
# Divergence guard
# ---------------------------------------------------------------------------

def check_divergence(
    v2_file: Path,
    candidate_lines: list[str],
    v1_lines: list[str],
    strong_findings: list[dict],
) -> tuple[bool, list[str]]:
    """Return (diverges, divergent_lines).

    A divergence occurs when the existing v2/he file differs from what the
    pipeline would produce AND those differences cannot be explained purely
    by the mechanical apply of strong_findings on v1_lines.

    Strategy: the pipeline output IS candidate_lines.  If the existing v2/he
    content differs from candidate_lines, those lines are hand-edits that
    the script must not silently overwrite.
    """
    existing_text = v2_file.read_text(encoding="utf-8")
    existing_lines = existing_text.splitlines()

    # Strip trailing empty lines for comparison.
    def strip_trailing(lst: list[str]) -> list[str]:
        lst = list(lst)
        while lst and not lst[-1].strip():
            lst.pop()
        return lst

    existing_stripped = strip_trailing(existing_lines)
    candidate_stripped = strip_trailing(candidate_lines)

    if existing_stripped == candidate_stripped:
        return False, []

    # Collect the divergent lines for display.
    divergent: list[str] = []
    max_len = max(len(existing_stripped), len(candidate_stripped))
    for i in range(max_len):
        e = existing_stripped[i] if i < len(existing_stripped) else "<missing>"
        c = candidate_stripped[i] if i < len(candidate_stripped) else "<missing>"
        if e != c:
            divergent.append(f"  line {i+1}:")
            divergent.append(f"    existing : {e}")
            divergent.append(f"    pipeline : {c}")

    return True, divergent


# ---------------------------------------------------------------------------
# Markdown report helpers
# ---------------------------------------------------------------------------

def _format_finding_block(change: dict, change_num: int) -> str:
    finding = change["finding"]
    action = change["action"]
    validator_name = finding.get("_validator", "unknown")
    rule_id = finding.get("rule_id", "?")
    rule_short = finding.get("rule_short", "")
    severity = finding.get("severity", "?")
    tag = finding.get("tag", "?")
    brief = finding.get("brief", "")
    line_no = finding.get("line", "?")

    before_lines = change.get("before_lines", {})
    after_lines = change.get("after_lines", {})

    before_block = "\n".join(
        f"  {ln}: {text}" for ln, text in sorted(before_lines.items())
    )
    after_block = "\n".join(
        f"  {ln}: {text}" for ln, text in sorted(after_lines.items())
    )

    return (
        f"### Change {change_num}: line {line_no} → {action}\n"
        f"- Validator: {validator_name} (rule {rule_id} — {rule_short})\n"
        f"- Severity: {severity}, Tag: {tag}\n"
        f"- Brief: {brief}\n"
        f"- Before:\n"
        f"  ```\n"
        f"{before_block}\n"
        f"  ```\n"
        f"- After:\n"
        f"  ```\n"
        f"{after_block}\n"
        f"  ```\n"
    )


def _format_review_block(finding: dict, item_num: int) -> str:
    validator_name = finding.get("_validator", "unknown")
    unadopted = finding.get("_unadopted", False)
    unadopted_tag = finding.get("_unadopted_tag", False)
    rule_id = finding.get("rule_id", "?")
    rule_short = finding.get("rule_short", "")
    severity = finding.get("severity", "?")
    tag = finding.get("tag", "?")
    brief = finding.get("brief", "")
    line_no = finding.get("line", "?")

    if unadopted:
        reason = "unadopted validator — STRONG output held back pending ≥80% clean-rate audit"
    elif unadopted_tag:
        reason = f"tag '{tag}' not in adopted tag-set for this validator"
    else:
        reason = "REVIEW-REQUIRED — flagged for editorial judgment"

    return (
        f"### Review item {item_num}: line {line_no}\n"
        f"- Validator: {validator_name} (rule {rule_id} — {rule_short})\n"
        f"- Severity: {severity}, Tag: {tag}\n"
        f"- Brief: {brief}\n"
        f"- Reason deferred: {reason}\n"
    )


def _format_conflict_block(conflict: dict, conflict_num: int) -> str:
    line_no = conflict["line"]
    split_f = conflict["split_finding"]
    merge_f = conflict["merge_finding"]
    resolution = conflict["resolution"]

    return (
        f"### Conflict {conflict_num}: line {line_no}\n"
        f"- Split (validator: {split_f.get('_validator', '?')}, "
        f"rule {split_f.get('rule_id', '?')}): {split_f.get('brief', '')}\n"
        f"- Merge (validator: {merge_f.get('_validator', '?')}, "
        f"rule {merge_f.get('rule_id', '?')}): {merge_f.get('brief', '')}\n"
        f"- Resolution: **{resolution}** (canon §1 Decision Procedure step 4)\n"
    )


def build_chapter_report(
    book: str,
    chapter_stem: str,
    v1_line_count: int,
    v2_line_count: int,
    applied_changes: list[dict],
    review_items: list[dict],
    conflicts: list[dict],
    timestamp: str,
) -> str:
    lines_out: list[str] = []
    lines_out.append(
        f"# {INPUT_TIER_LABEL} → {OUTPUT_TIER_LABEL}: {book} / {chapter_stem}"
    )
    lines_out.append(f"_Generated: {timestamp}_\n")
    lines_out.append("## Summary\n")
    lines_out.append(f"- {INPUT_TIER_LABEL} lines: {v1_line_count}")
    lines_out.append(f"- {OUTPUT_TIER_LABEL} lines: {v2_line_count}")
    lines_out.append(f"- Mechanical changes applied: {len(applied_changes)}")
    lines_out.append(f"- REVIEW-REQUIRED items deferred: {len(review_items)}")
    if conflicts:
        lines_out.append(f"- Merge-vs-split conflicts: {len(conflicts)}")
    lines_out.append("")

    lines_out.append("## Applied changes\n")
    if applied_changes:
        for i, change in enumerate(applied_changes, start=1):
            lines_out.append(_format_finding_block(change, i))
    else:
        lines_out.append("_No mechanical changes applied (no adopted STRONG candidates for this chapter)._\n")

    lines_out.append("## Deferred to editorial review\n")
    if review_items:
        for i, finding in enumerate(review_items, start=1):
            lines_out.append(_format_review_block(finding, i))
    else:
        lines_out.append("_No items deferred._\n")

    if conflicts:
        lines_out.append("## Merge-vs-split conflicts (canon §1 step 4)\n")
        lines_out.append(
            "The following lines have a split candidate conflicting with a prior merge. "
            "Merge wins per canon §1 Decision Procedure step 4. Review in v2/he.\n"
        )
        for i, conflict in enumerate(conflicts, start=1):
            lines_out.append(_format_conflict_block(conflict, i))

    return "\n".join(lines_out)


# ---------------------------------------------------------------------------
# Per-chapter processor
# ---------------------------------------------------------------------------

def process_chapter(
    chapter_file: Path,
    book: str,
    strong_findings: list[dict],
    review_findings: list[dict],
    dry_run: bool,
    report_only: bool,
    force: bool,
    timestamp: str,
) -> dict:
    """Apply findings to one chapter; write v2/he and reports if applicable."""
    chapter_stem = chapter_file.stem
    v1_lines = chapter_file.read_text(encoding="utf-8").splitlines()
    v1_line_count = len(v1_lines)

    conflicts = detect_merge_split_conflicts(strong_findings, review_findings)

    mutated_lines, applied_changes = apply_mutations_to_lines(v1_lines, strong_findings)
    v2_line_count = len(mutated_lines)

    # Divergence guard — only relevant when not dry-running and v2/he already exists.
    diverged = False
    divergent_lines: list[str] = []
    v2_file = v2_path_for(chapter_file, book)

    if not dry_run and not report_only and v2_file.exists():
        diverged, divergent_lines = check_divergence(
            v2_file, mutated_lines, v1_lines, strong_findings
        )
        if diverged and not force:
            print(
                f"  [ABORT] {chapter_stem}: v2/he file exists with hand-edits "
                f"not derivable from v1 + mechanical apply.",
                file=sys.stderr,
            )
            print(
                f"    Use --force to override (DESTRUCTIVE — hand-edits will be lost).",
                file=sys.stderr,
            )
            print("    Divergent lines:", file=sys.stderr)
            for dl in divergent_lines[:20]:  # Limit output
                print(dl, file=sys.stderr)
            if len(divergent_lines) > 20:
                print(f"    ... ({len(divergent_lines) - 20} more lines)", file=sys.stderr)
            return {
                "chapter": chapter_stem,
                "v1_lines": v1_line_count,
                "v2_lines": v2_line_count,
                "applied": len(applied_changes),
                "review": len(review_findings),
                "conflicts": len(conflicts),
                "aborted": True,
                "diverged": True,
            }

    report_text = build_chapter_report(
        book=book,
        chapter_stem=chapter_stem,
        v1_line_count=v1_line_count,
        v2_line_count=v2_line_count,
        applied_changes=applied_changes,
        review_items=review_findings,
        conflicts=conflicts,
        timestamp=timestamp,
    )

    if not dry_run and not report_only:
        # Write v2/he output.
        out_dir = V2_DIR / book
        out_dir.mkdir(parents=True, exist_ok=True)
        v2_file.write_text("\n".join(mutated_lines) + "\n", encoding="utf-8")

    if not dry_run:
        # Write report (even in report-only mode).
        report_dir = REPORTS_DIR / book
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / f"{chapter_stem}-{timestamp.replace(':', '-').replace(' ', 'T')}.md"
        report_file.write_text(report_text, encoding="utf-8")

    return {
        "chapter": chapter_stem,
        "v1_lines": v1_line_count,
        "v2_lines": v2_line_count,
        "applied": len(applied_changes),
        "review": len(review_findings),
        "conflicts": len(conflicts),
        "aborted": False,
        "diverged": diverged,
        "report": report_text,
    }


# ---------------------------------------------------------------------------
# Book processor
# ---------------------------------------------------------------------------

def process_book(
    book: str,
    dry_run: bool,
    report_only: bool,
    force: bool,
    timestamp: str,
) -> dict:
    """Run validators and process all chapters in a book."""
    chapter_files = resolve_chapter_files(book)
    if not chapter_files:
        print(f"  [ERROR] No .txt files found under {V1_DIR / book}", file=sys.stderr)
        return {"book": book, "error": "no chapter files", "chapters": []}

    adopted_names = set(ADOPTED_VALIDATORS.keys())
    print(f"\n{'='*60}")
    print(f"Book: {book}")
    print(f"Mode: {'dry-run' if dry_run else 'report-only' if report_only else 'apply'}")
    print(f"Adopted validators: {sorted(adopted_names)}")
    print(f"{'='*60}")

    # -----------------------------------------------------------------------
    # Step 1: Run all validators against v1/he-baseline for this book.
    # -----------------------------------------------------------------------
    print("\nRunning validators...")
    validator_outputs: list[tuple[str, dict]] = []
    for script_rel, validator_name in ALL_VALIDATORS:
        # Skip validators whose scripts don't exist yet — don't abort.
        path = REPO_ROOT / script_rel
        if not path.exists():
            print(f"  {validator_name}: [SKIP — script not found]")
            continue
        print(f"  {validator_name}...", end=" ", flush=True)
        doc = run_validator(script_rel, book)
        if doc is not None:
            for f in doc.get("findings", []):
                f["_validator"] = validator_name
            validator_outputs.append((validator_name, doc))
            n = doc.get("summary", {}).get("total_findings", 0)
            label = "adopted" if validator_name in adopted_names else "unadopted"
            print(f"{n} findings [{label}]")
        else:
            print("FAILED (skipped)")

    print()

    # -----------------------------------------------------------------------
    # Step 2: Aggregate findings by file.
    # -----------------------------------------------------------------------
    strong_by_file, review_by_file = aggregate_findings(validator_outputs, ADOPTED_VALIDATORS)

    # -----------------------------------------------------------------------
    # Step 3: Process each chapter.
    # -----------------------------------------------------------------------
    book_stats: list[dict] = []
    total_applied = 0

    for chapter_file in chapter_files:
        fkey = file_key(chapter_file)
        ch_strong = strong_by_file.get(fkey, [])
        ch_review = review_by_file.get(fkey, [])

        stats = process_chapter(
            chapter_file=chapter_file,
            book=book,
            strong_findings=ch_strong,
            review_findings=ch_review,
            dry_run=dry_run,
            report_only=report_only,
            force=force,
            timestamp=timestamp,
        )
        book_stats.append(stats)
        total_applied += stats.get("applied", 0)

        if stats.get("aborted"):
            status = "ABORTED (hand-edits present — use --force)"
        else:
            action_label = "would apply" if dry_run else "applied"
            conflict_note = (
                f", {stats['conflicts']} merge/split conflict(s)"
                if stats.get("conflicts")
                else ""
            )
            status = (
                f"{stats['v1_lines']} → {stats['v2_lines']} lines, "
                f"{stats['applied']} changes {action_label}, "
                f"{stats['review']} deferred"
                f"{conflict_note}"
            )
        print(f"  {stats['chapter']}: {status}")

        if dry_run and "report" in stats:
            print()
            print(stats["report"])

    # -----------------------------------------------------------------------
    # Step 4: Sweep-scale audit warning (canon §7).
    # -----------------------------------------------------------------------
    if total_applied >= 5:
        print(
            f"\nWARNING (canon §7 sweep-scale audit): {total_applied} changes applied "
            f"in this run. Per canon §7, a sweep of ≥5 instances triggers a mandatory "
            f"audit. Run validators/run_all.py --baseline-check and review the diff "
            f"before committing."
        )

    return {"book": book, "chapters": book_stats, "total_applied": total_applied}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--book",
        metavar="BOOK",
        help="Book folder name, e.g. '05-jonah'. Must exist under v1/he-baseline/.",
    )
    group.add_argument(
        "--all-books",
        action="store_true",
        default=False,
        help="Process all books present in v1/he-baseline/.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help=(
            "Show what would be applied; print reports to stdout. "
            "No files written (neither v2/he nor reports)."
        ),
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        default=False,
        help="Write markdown reports but do not write v2/he files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help=(
            "Override divergence guard — overwrite hand-edited v2/he files. "
            "DESTRUCTIVE: hand-edits in v2/he will be lost."
        ),
    )
    args = parser.parse_args()

    if args.dry_run and args.report_only:
        print("ERROR: --dry-run and --report-only are mutually exclusive.", file=sys.stderr)
        sys.exit(2)

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    if args.all_books:
        if not V1_DIR.exists():
            print(f"ERROR: v1/he-baseline directory not found: {V1_DIR}", file=sys.stderr)
            sys.exit(2)
        books = sorted(d.name for d in V1_DIR.iterdir() if d.is_dir())
        if not books:
            print(f"ERROR: No book directories found under {V1_DIR}", file=sys.stderr)
            sys.exit(2)
        print(f"Processing {len(books)} book(s): {', '.join(books)}")
    else:
        book = args.book
        if not (V1_DIR / book).exists():
            print(
                f"ERROR: v1/he-baseline book directory not found: {V1_DIR / book}",
                file=sys.stderr,
            )
            sys.exit(2)
        books = [book]

    grand_total_applied = 0
    grand_total_aborted = 0
    all_book_stats: list[dict] = []

    for book in books:
        result = process_book(
            book=book,
            dry_run=args.dry_run,
            report_only=args.report_only,
            force=args.force,
            timestamp=timestamp,
        )
        all_book_stats.append(result)
        grand_total_applied += result.get("total_applied", 0)
        for ch in result.get("chapters", []):
            if ch.get("aborted"):
                grand_total_aborted += 1

    # Final summary.
    print()
    print("=" * 60)
    print("RUN SUMMARY")
    print("=" * 60)
    for result in all_book_stats:
        b = result["book"]
        if "error" in result:
            print(f"  {b}: ERROR — {result['error']}")
            continue
        ch_stats = result["chapters"]
        applied = result.get("total_applied", 0)
        aborted = sum(1 for c in ch_stats if c.get("aborted"))
        deferred = sum(c.get("review", 0) for c in ch_stats)
        line_delta = sum(
            c.get("v2_lines", 0) - c.get("v1_lines", 0)
            for c in ch_stats
            if not c.get("aborted")
        )
        print(
            f"  {b}: {applied} applied, {deferred} deferred, "
            f"line delta {line_delta:+d}"
            + (f", {aborted} chapter(s) ABORTED" if aborted else "")
        )

    if not args.dry_run:
        print()
        if not args.report_only:
            print(f"  v2/he output: {V2_DIR}")
        print(f"  Reports:      {REPORTS_DIR}")

    print()
    if grand_total_aborted:
        print(
            f"WARNING: {grand_total_aborted} chapter(s) aborted due to hand-edits "
            f"in v2/he. Run with --force to override (destructive)."
        )
    if grand_total_applied >= 5:
        print(
            f"WARNING (canon §7): {grand_total_applied} total changes applied. "
            f"Mandatory sweep-scale audit required before commit. "
            f"Run: PYTHONIOENCODING=utf-8 py -3 validators/run_all.py --baseline-check"
        )
    elif grand_total_applied == 0 and not grand_total_aborted:
        print("No changes applied (v1 baseline already clean for adopted rules).")

    sys.exit(0)


if __name__ == "__main__":
    main()
