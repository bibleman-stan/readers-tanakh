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

Override mechanisms (visible in JSONL trace for later audit):
  - Universal:  prefix command body with '# disciplined-allow: <reason>'
  - Cascade-specific: prefix command body with '# split-justified: <reason>'

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


def _violations(command: str) -> list[str]:
    """Return list of detected anti-pattern violations."""
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
    if CASCADE_RE.search(command) and "# split-justified:" not in command:
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

    violations = _violations(command)
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
