#!/usr/bin/env python3
"""PreToolUse Bash discipline hook.

Mechanical forcing function that fires at the action site (the moment Claude
Code is about to execute a Bash tool call). Blocks anti-patterns documented
in handoffs/14-operational-protocols.md before they happen, instead of
detecting them after the fact.

Anti-patterns blocked:
  1. Multi-line Python heredocs (>=5 non-empty lines containing Python idioms)
     — per §E1-E2: should be persistent scripts under scripts/, not one-off
     bash heredocs (history shows they break on Windows /tmp ephemerality and
     apostrophe/Hebrew-text heredoc parsing).
  2. Cascade invocations (apply_specs / refresh_book / apply_validators with
     --all-books) on the main thread without parallel-justification — per
     §A2 mandatory two-phase pattern: should be 6 parallel cluster Agent
     dispatches, not one main-thread call.
  3. git status / git diff without summary flags — per §H3 verbose-by-default
     ingestion: default to --shortstat / --numstat / --stat / --porcelain /
     --name-only, or pipe to wc/head/grep for a count.
  4. Cascade invocations without recent adversarial-audit evidence in the
     transcript — per §A3 Step 0: before any non-trivial implementation,
     dispatch ≥2 parallel Agent calls (one message, multiple Agent
     tool_use blocks) OR declare 'Audit-skippable: <reason>'. Hook walks
     recent transcript turns and counts Agent dispatches; if <2 found and
     no '# audit-skippable:' prefix, the cascade is refused.

Override mechanisms (visible in JSONL trace for later audit):
  - Universal:        prefix command body with '# disciplined-allow: <reason>'
  - Cascade-parallel: prefix command body with '# split-justified: <reason>'
  - Audit-skippable:  prefix command body with '# audit-skippable: <reason>'

Output protocol:
  Block: exit code 2, message on stderr (Claude Code surfaces this to the
         model and refuses the tool call).
  Allow: exit code 0, no output.

Hook input (JSON on stdin):
  { "session_id": "...", "transcript_path": "...", "cwd": "...",
    "hook_event_name": "PreToolUse", "tool_name": "Bash",
    "tool_input": { "command": "...", "description": "..." } }
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def _count_recent_agent_dispatches(transcript_path: str, lookback_lines: int = 200) -> int:
    """Count Agent tool_use entries in the most recent N JSONL transcript lines.

    Walks the tail of the JSONL (transcripts grow large; we only care about
    the recent window). Counts every assistant message's tool_use blocks
    where name == "Agent". Returns 0 if path missing / unreadable / malformed
    so a transcript-access failure does not falsely block the gate.
    """
    if not transcript_path:
        return 0
    p = Path(transcript_path)
    if not p.exists():
        return 0
    try:
        with p.open("rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            tail_size = min(size, 5_000_000)  # ~5MB tail
            fh.seek(size - tail_size)
            tail_bytes = fh.read()
        # Decode tolerantly; partial leading line is fine — we'll skip it on parse failure.
        tail_text = tail_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return 0
    lines = tail_text.splitlines()[-lookback_lines:]
    count = 0
    for line in lines:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except Exception:
            continue
        if entry.get("type") != "assistant":
            continue
        msg = entry.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if (
                isinstance(block, dict)
                and block.get("type") == "tool_use"
                and block.get("name") == "Agent"
            ):
                count += 1
    return count


def _violations(command: str, payload: dict | None = None) -> list[str]:
    """Return list of detected anti-pattern violations."""
    payload = payload or {}
    violations: list[str] = []

    # --- Pattern 1: multi-line Python heredoc -------------------------------
    # Match `<<TAG ... TAG` or `<<'TAG' ... TAG` blocks. We need the heredoc
    # to be (a) preceded by a python invocation, (b) ≥5 non-empty body lines,
    # (c) body contains python idioms (import/from/def/class/print/etc.).
    HEREDOC_RE = re.compile(
        r"<<\s*['\"]?(\w+)['\"]?\s*\n(.*?)\n\s*\1\s*$",
        re.DOTALL | re.MULTILINE,
    )
    PY_IDIOM_RE = re.compile(
        r"^\s*(import |from |def |class |print\(|"
        r"for \w+ in |if __name__|with open|"
        r"return |yield |@\w+|sys\.|json\.|os\.|re\.)"
    )
    # The pre-heredoc string must end with a Python invocation pointing at stdin
    # via the `-` marker: `py -3 -`, `py -`, `python3 -`, etc. We strip trailing
    # whitespace and require the stripped pre to end with the invocation pattern.
    PY_INVOCATION_RE = re.compile(
        r"\b(py(?:thon)?3?)\b\s+(?:-3\s+)?-\s*$", re.IGNORECASE
    )

    for m in HEREDOC_RE.finditer(command):
        body = m.group(2)
        body_lines = [ln for ln in body.split("\n") if ln.strip()]
        if len(body_lines) < 5:
            continue
        if not any(PY_IDIOM_RE.search(ln) for ln in body_lines):
            continue
        # Confirm it's a Python invocation (not, say, a git commit message body
        # delivered via `git commit -m "$(cat <<'EOF' ... EOF)"`).
        pre = command[: m.start()].rstrip()
        if not PY_INVOCATION_RE.search(pre):
            continue
        violations.append(
            f"[E1-E2] Multi-line Python heredoc detected ({len(body_lines)} non-empty "
            f"lines, contains Python idioms). Per handoffs/14-operational-protocols.md "
            f"§E1-E2: recurring Python operations must be persistent scripts under "
            f"scripts/, not bash heredocs. Bash heredocs break on Windows /tmp "
            f"ephemerality and on Hebrew/apostrophe-containing text. ACTION: use the "
            f"Write tool to create scripts/<descriptive_name>.py, then run with `py -3 "
            f"scripts/<name>.py`. Reuse next time you need the same operation."
        )
        break  # one heredoc violation surfaces the lesson; don't spam multiple

    # --- Pattern 2: --all-books cascade on main thread ----------------------
    CASCADE_RE = re.compile(
        r"(apply_specs|refresh_book|apply_validators)\.py\b[^\n]*--all-books"
    )
    cascade_match = CASCADE_RE.search(command)
    if cascade_match and "# split-justified:" not in command:
        violations.append(
            "[A2] Cascade invocation '--all-books' on main thread. Per "
            "handoffs/14-operational-protocols.md §A2 (mandatory two-phase pattern): "
            "this should be dispatched as 6 parallel cluster Agent calls in one "
            "message — Torah / Former Prophets / Latter Prophets / Writings prose / "
            "Sifrei Emet / Embedded Poetry. Wall time collapses to max(per-cluster) "
            "instead of sum. ACTION: dispatch 6 Agent tool_use blocks in a single "
            "message, one per cluster. To override (true initial-exploration single "
            "pass only), prefix command with '# split-justified: <reason>'."
        )

    # --- Pattern 4 (A3 Step 0): --all-books without recent audit evidence ---
    # Cascade invocations are batch-boundary signals — the moment substantive
    # implementations get applied corpus-wide. Per §A3 Step 0, these MUST be
    # preceded by adversarial-audit dispatches (≥2 in recent transcript window).
    if cascade_match and "# audit-skippable:" not in command:
        n_dispatches = _count_recent_agent_dispatches(payload.get("transcript_path", ""))
        if n_dispatches < 2:
            violations.append(
                f"[A3-Step0] Cascade invocation '--all-books' with insufficient "
                f"adversarial-audit evidence in recent transcript (found "
                f"{n_dispatches} Agent dispatch(es); need ≥2). Per "
                f"handoffs/14-operational-protocols.md §A3 Step 0: before any "
                f"non-trivial implementation, the FIRST tool call in your response "
                f"must be either (a) parallel Agent dispatches for adversarial "
                f"audit (one message, multiple Agent tool_use blocks), OR (b) a "
                f"one-line declaration 'Audit-skippable: <reason>' citing a "
                f"recognized trivial class (port-of-validated, mechanical-ingest, "
                f"test/fixture, runner/glue, scratch). ACTION: (1) abort, dispatch "
                f"≥2 parallel Agent calls in one message, let their findings inform "
                f"the implementation, then re-run; OR (2) prefix command with "
                f"'# audit-skippable: <reason>'."
            )

    # --- Pattern 3: git status/diff without summary flags ------------------
    GIT_VERBOSE_RE = re.compile(r"\bgit\s+(?:status|diff)\b")
    SUMMARY_FLAG_RE = re.compile(
        r"--(?:shortstat|numstat|stat|porcelain|name-only|name-status|short)\b"
        r"|--cached\s+--stat\b"
    )
    SUMMARY_PIPE_RE = re.compile(r"\|\s*(?:wc\b|head\b|tail\b|grep\b|rg\b)")
    # Split on common shell separators to evaluate per-clause
    clauses = re.split(r"&&|;|\n", command)
    for clause in clauses:
        clause_s = clause.strip()
        if not clause_s or clause_s.startswith("#"):
            continue
        if not GIT_VERBOSE_RE.search(clause_s):
            continue
        if SUMMARY_FLAG_RE.search(clause_s):
            continue
        if SUMMARY_PIPE_RE.search(clause_s):
            continue
        # Allow specific safe patterns: `git status --short | wc` already caught;
        # `git diff path/to/file` (a specific path arg, no `--`-flags) is debatable
        # but safer to flag than miss.
        violations.append(
            f"[H3] git status/diff without summary flag in: '{clause_s[:90]}'. Per "
            f"handoffs/14-operational-protocols.md §H3 (verbose-by-default ingestion): "
            f"bare `git status` and `git diff` ingest verbose output and waste context. "
            f"ACTION: add a summary flag (--shortstat / --numstat / --stat / "
            f"--porcelain / --name-only / --short) or pipe to | wc -l for a count."
        )
        break  # one git violation is enough to surface the lesson

    return violations


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # Malformed input — don't block the tool call.
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = payload.get("tool_input", {}).get("command", "") or ""
    if not command:
        return 0

    # Universal escape hatch — visible in the JSONL for later audit.
    if "# disciplined-allow:" in command:
        return 0

    violations = _violations(command, payload)
    if not violations:
        return 0

    msg = (
        f"\n=== PreToolUse DISCIPLINE GATE — {len(violations)} anti-pattern(s) "
        f"detected ===\n\n"
        + "\n\n".join(f"{i + 1}. {v}" for i, v in enumerate(violations))
        + "\n\nUniversal override (visible in JSONL): prefix command body with "
        "'# disciplined-allow: <reason>' or, for cascade-specific cases, "
        "'# split-justified: <reason>'.\n"
        "These overrides are visible in your tool-call history and reviewable "
        "by Stan; use sparingly.\n"
    )
    print(msg, file=sys.stderr)
    return 2  # blocks the tool call; stderr surfaced to Claude


if __name__ == "__main__":
    sys.exit(main())
