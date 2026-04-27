#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apply_pipeline.py — shared orchestration logic for apply_v2 and apply_v3.

Both v2 (Layer 1 syntax-validator → v2-he-syntax) and v3 (Layer 3
colometry-validator → v3-he-colometry) follow the same shape:

    run validators → aggregate findings → apply mutations → write files + reports

This module provides that shape so each orchestrator script only carries
tier-specific configuration (which validators, which directories, which
adoption list).

Public API
----------
run_validator(script_path, book, repo_root)
aggregate_findings(validator_outputs, repo_root, adopted_set)
apply_mutations_to_lines(lines, strong_findings)
build_chapter_report(...)
build_review_report(...)
resolve_chapter_files(input_dir, book)

Internal helpers (_format_finding_block, _format_review_block) are prefixed
with underscore but importable if needed for testing.
"""

import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Subprocess helper
# ---------------------------------------------------------------------------

def run_validator(script_path: str | Path, book: str, repo_root: Path) -> dict | None:
    """Invoke a validator script with --json --book <book>.

    Parameters
    ----------
    script_path : str or Path
        Path to the validator script, relative to repo_root OR absolute.
    book : str
        Book folder name, e.g. '05-jonah'.
    repo_root : Path
        Absolute path to the repository root.

    Returns
    -------
    dict | None
        Parsed JSON document from the validator, or None on failure.

    Validators exit 0 (clean) or 1 (findings present) — both are success;
    exit 2 is a setup error and causes a None return.
    """
    path = Path(script_path)
    if not path.is_absolute():
        path = repo_root / path
    if not path.exists():
        print(
            f"  [WARN] Validator script not found: {path}",
            file=sys.stderr,
        )
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
        print(f"  [ERROR] Could not run {script_path}: {exc}", file=sys.stderr)
        return None

    if result.returncode == 2:
        print(
            f"  [ERROR] Validator setup error (exit 2): {script_path}",
            file=sys.stderr,
        )
        if result.stderr.strip():
            print(f"    stderr: {result.stderr.strip()}", file=sys.stderr)
        return None

    stdout = result.stdout.strip()
    if not stdout:
        # Exit 0 with no output means no findings — return an empty doc.
        return {
            "validator": str(script_path),
            "findings": [],
            "summary": {"total_findings": 0},
        }

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        print(
            f"  [ERROR] JSON parse failure from {script_path}: {exc}",
            file=sys.stderr,
        )
        return None


# ---------------------------------------------------------------------------
# Finding aggregation
# ---------------------------------------------------------------------------

def aggregate_findings(
    validator_outputs: list[tuple[str, dict]],
    repo_root: Path,
    adopted_set: set[str],
) -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
    """Partition validator findings into STRONG (apply-ready) and REVIEW-REQUIRED queues.

    Parameters
    ----------
    validator_outputs : list of (validator_name, doc) tuples
        Each doc is the parsed JSON from a validator run (keyed as returned by
        run_validator, with a "findings" list).
    repo_root : Path
        Repo root — used only if relative file keys need resolving (not mutated).
    adopted_set : set[str]
        Validator names (keys) that have passed the ≥80% clean-rate adoption
        threshold and may have their STRONG output applied mechanically.

    Returns
    -------
    (strong_by_file, review_by_file) : (dict, dict)
        Both dicts map file-path strings (forward-slash, repo-root-relative) to
        lists of finding dicts.  Each finding is augmented with:
          _validator : str   — the validator name key
          _unadopted : bool  — True when the finding came from an unadopted
                               validator (present only when True, absent otherwise)

    Rules:
      - STRONG-MERGE-CANDIDATE / STRONG-SPLIT-CANDIDATE findings from ADOPTED
        validators → strong_by_file.
      - STRONG candidates from UNADOPTED validators → review_by_file with
        _unadopted=True (held back; not applied).
      - REVIEW-REQUIRED findings (from any validator) → review_by_file.
    """
    strong_by_file: dict[str, list[dict]] = defaultdict(list)
    review_by_file: dict[str, list[dict]] = defaultdict(list)

    for validator_name, doc in validator_outputs:
        is_adopted = validator_name in adopted_set
        findings = doc.get("findings", [])

        for finding in findings:
            file_str = finding.get("file", "")
            if not file_str:
                continue

            tag = finding.get("tag", "")
            action = finding.get("applied_action")

            if tag == "REVIEW-REQUIRED" or action is None:
                review_by_file[file_str].append(
                    {**finding, "_validator": validator_name}
                )
            elif tag in ("STRONG-MERGE-CANDIDATE", "STRONG-SPLIT-CANDIDATE"):
                if is_adopted:
                    strong_by_file[file_str].append(
                        {**finding, "_validator": validator_name}
                    )
                else:
                    # Unadopted: demote to review — not applied.
                    review_by_file[file_str].append(
                        {
                            **finding,
                            "_validator": validator_name,
                            "_unadopted": True,
                        }
                    )

    return dict(strong_by_file), dict(review_by_file)


# ---------------------------------------------------------------------------
# Mutation engine
# ---------------------------------------------------------------------------

def apply_mutations_to_lines(
    lines: list[str],
    strong_findings: list[dict],
    separator: str = " ",
) -> tuple[list[str], list[dict]]:
    """Apply STRONG-MERGE-CANDIDATE and STRONG-SPLIT-CANDIDATE findings to lines.

    This function handles both merges (Layer 1 and some Layer 3 rules) and splits
    (Layer 3 Rule H5 long-frame case).

    Parameters
    ----------
    lines : list[str]
        Raw line list (1-indexed in findings; 0-indexed internally here).
    strong_findings : list[dict]
        Findings with an applied_action set — one of:
          "merge_with_next"
          "merge_with_previous"
          "split_at_position_N"   (N is an integer token index, 0-based)

    Returns
    -------
    (mutated_lines, applied_changes) : (list[str], list[dict])

    Conflict-resolution rules (canon §1 Decision Procedure, step 4):
      - merge_with_next / merge_with_previous BEATS split_at_position_N when
        both fire on the same line number.  The split is silently dropped
        (the applied_changes list records only what was actually applied).
      - When two merges conflict on the same line, the first encountered is kept
        (they should not conflict in practice — each finding carries its own line).

    Processing order:
      HIGH line-number to LOW, so earlier mutations do not invalidate later
      line-number references.  Splits insert a new line via list.insert(), so
      they are handled last within the same logical position to keep indices
      stable.

    Sentinel compaction:
      After merge_with_next / merge_with_previous, the consumed line is replaced
      with the sentinel \\x00 so that the list length is preserved and subsequent
      line-number references (from findings with higher-numbered lines processed
      earlier in the reverse pass) remain valid.  The sentinel is stripped in a
      final compaction pass.
    """
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
            # Merge beats split at the same line (canon §1 Decision Procedure).
            if "merge" in action and "merge" not in existing_action:
                by_line[line_no] = finding
            # If both are merges (shouldn't happen), keep existing.

    # Sort HIGH to LOW so mutations don't shift subsequent indices.
    sorted_findings = sorted(by_line.values(), key=lambda f: f["line"], reverse=True)

    # Work on a mutable copy (0-indexed internally; findings are 1-indexed).
    work = list(lines)
    applied: list[dict] = []

    _CONSUMED = "\x00"  # Sentinel for consumed (merged-away) lines.

    for finding in sorted_findings:
        line_no = finding["line"]           # 1-indexed
        action = finding.get("applied_action", "")
        idx = line_no - 1                   # 0-indexed

        if idx < 0 or idx >= len(work):
            continue

        if action == "merge_with_next":
            # Find next non-consumed line.
            next_idx = idx + 1
            while next_idx < len(work) and work[next_idx] == _CONSUMED:
                next_idx += 1
            if next_idx >= len(work):
                continue  # Nothing to merge with; skip.

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
            # Find previous non-consumed line.
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
            # Layer 3 H5 long-frame splits: split_at_position_N where N is the
            # 0-based token index of לֵאמֹר (split after position N).
            try:
                position = int(action.split("split_at_position_")[1])
            except (IndexError, ValueError):
                continue
            before = work[idx]
            tokens = before.split()
            # Split AFTER position N: first part = tokens[:position+1],
            # second part = tokens[position+1:].
            # (The validator emits split_at_position_N where N is the index of
            # לֵאמֹר; the frame includes לֵאמֹר on the first line per Rule H5.)
            split_after = position + 1
            if split_after <= 0 or split_after >= len(tokens):
                continue
            line_a = " ".join(tokens[:split_after])
            line_b = " ".join(tokens[split_after:])
            if not line_b.strip():
                continue  # Nothing after the split point; skip.
            applied.append({
                "finding": finding,
                "action": action,
                "before_lines": {line_no: before},
                "after_lines": {line_no: line_a, line_no + 0.5: line_b},
            })
            work[idx] = line_a
            work.insert(idx + 1, line_b)

    # Compaction: remove _CONSUMED sentinels.
    final = [ln for ln in work if ln != _CONSUMED]
    return final, applied


# ---------------------------------------------------------------------------
# Markdown report helpers
# ---------------------------------------------------------------------------

def _format_finding_block(change: dict, change_num: int) -> str:
    """Format one applied change as a markdown block."""
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
    """Format one REVIEW-REQUIRED finding as a markdown block."""
    validator_name = finding.get("_validator", "unknown")
    unadopted = finding.get("_unadopted", False)
    rule_id = finding.get("rule_id", "?")
    rule_short = finding.get("rule_short", "")
    severity = finding.get("severity", "?")
    tag = finding.get("tag", "?")
    brief = finding.get("brief", "")
    line_no = finding.get("line", "?")

    reason = (
        "unadopted validator — STRONG output held back pending ≥80% clean-rate audit"
        if unadopted
        else "REVIEW-REQUIRED — validator flagged for editorial judgment"
    )

    return (
        f"### Review item {item_num}: line {line_no}\n"
        f"- Validator: {validator_name} (rule {rule_id} — {rule_short})\n"
        f"- Severity: {severity}, Tag: {tag}\n"
        f"- Brief: {brief}\n"
        f"- Reason deferred: {reason}\n"
    )


# ---------------------------------------------------------------------------
# Report builders
# ---------------------------------------------------------------------------

def build_chapter_report(
    book: str,
    chapter_stem: str,
    input_tier_label: str,
    output_tier_label: str,
    input_line_count: int,
    output_line_count: int,
    applied_changes: list[dict],
    review_items: list[dict],
    all_adopted: bool,
    no_adopted_note: str = "",
) -> str:
    """Build the per-chapter markdown report string.

    Parameters
    ----------
    book : str
        Book folder name, e.g. '05-jonah'.
    chapter_stem : str
        Chapter file stem, e.g. 'jonah-01'.
    input_tier_label : str
        Human-readable name of the input tier (e.g. 'v1-he-baseline').
    output_tier_label : str
        Human-readable name of the output tier (e.g. 'v2-he-syntax').
    input_line_count : int
        Line count before mutations.
    output_line_count : int
        Line count after mutations.
    applied_changes : list[dict]
        Records from apply_mutations_to_lines.
    review_items : list[dict]
        Findings routed to the REVIEW-REQUIRED queue.
    all_adopted : bool
        True if at least one adopted validator is active.
    no_adopted_note : str
        Tier-specific explanatory sentence shown in the blockquote when
        all_adopted is False.  Defaults to a generic message if empty.
    """
    if not no_adopted_note:
        no_adopted_note = (
            "No mutations were applied. "
            f"The {output_tier_label} file is identical to {input_tier_label}. "
            "This preserves tier-architecture integrity until validators pass adoption."
        )

    lines_out: list[str] = []
    lines_out.append(
        f"# {input_tier_label} → {output_tier_label}: {book} / {chapter_stem}\n"
    )
    lines_out.append("## Summary\n")
    lines_out.append(f"- {input_tier_label} lines: {input_line_count}")
    lines_out.append(f"- {output_tier_label} lines: {output_line_count}")
    lines_out.append(f"- Mechanical changes applied: {len(applied_changes)}")
    lines_out.append(f"- REVIEW-REQUIRED items deferred to v4: {len(review_items)}")

    if not all_adopted:
        lines_out.append(f"\n> **NOTE:** {no_adopted_note}")

    lines_out.append("\n## Applied changes\n")
    if applied_changes:
        for i, change in enumerate(applied_changes, start=1):
            lines_out.append(_format_finding_block(change, i))
    else:
        lines_out.append(
            "_No mechanical changes applied "
            + (
                "(validators unadopted — see note above)."
                if not all_adopted
                else "(no STRONG candidates found for this chapter)."
            )
            + "_\n"
        )

    lines_out.append("## Deferred to v4 editorial review\n")
    if review_items:
        for i, finding in enumerate(review_items, start=1):
            lines_out.append(_format_review_block(finding, i))
    else:
        lines_out.append("_No items deferred._\n")

    return "\n".join(lines_out)


def build_review_report(
    book: str,
    chapter_stem: str,
    review_items: list[dict],
    layer_label: str = "Layer",
) -> str | None:
    """Build the per-chapter -review.md report, or None if no items.

    Parameters
    ----------
    book : str
        Book folder name.
    chapter_stem : str
        Chapter file stem.
    review_items : list[dict]
        Findings from the REVIEW-REQUIRED queue.
    layer_label : str
        Human-readable layer label for the preamble, e.g. 'Layer 1' or 'Layer 3'.
    """
    if not review_items:
        return None

    lines_out: list[str] = []
    lines_out.append(
        f"# v4 Editorial Work Queue: {book} / {chapter_stem} — REVIEW-REQUIRED\n"
    )
    lines_out.append(
        f"These items require per-item editorial judgment before applying. "
        f"They were flagged by {layer_label} validators but could not be mechanically "
        f"resolved (REVIEW-REQUIRED tag or unadopted validator).\n"
    )
    for i, finding in enumerate(review_items, start=1):
        lines_out.append(_format_review_block(finding, i))

    return "\n".join(lines_out)


# ---------------------------------------------------------------------------
# File-system helpers
# ---------------------------------------------------------------------------

def resolve_chapter_files(input_dir: Path, book: str) -> list[Path]:
    """Return sorted list of .txt chapter files for a book under input_dir.

    Returns an empty list (not raising) if the book directory does not exist,
    so callers can emit a clean error message.
    """
    book_dir = input_dir / book
    if not book_dir.exists():
        return []
    return sorted(book_dir.glob("*.txt"))


def file_key(chapter_file: Path, repo_root: Path) -> str:
    """Return a forward-slash repo-root-relative path string for a chapter file.

    Validators emit findings keyed by this format; apply scripts use it to
    look up per-chapter findings in the strong_by_file / review_by_file dicts.
    """
    return str(chapter_file.relative_to(repo_root)).replace("\\", "/")
