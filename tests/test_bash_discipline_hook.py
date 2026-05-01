#!/usr/bin/env python3
"""Tests for .claude/hooks/check_bash_discipline.py.

Encodes the gate invariants as fixtures so future changes to the hook can
be validated without manual Bash experimentation. Each test pipes a JSON
payload to the hook script as Claude Code would, and asserts the exit code
+ stderr classification.

Run:
    py -3 tests/test_bash_discipline_hook.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "check_bash_discipline.py"


def run_hook(command: str, transcript_path: str = "") -> tuple[int, str]:
    """Pipe a Bash tool_input.command to the hook; return (exit_code, stderr)."""
    payload = {
        "session_id": "test",
        "transcript_path": transcript_path,
        "cwd": str(Path.cwd()),
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command, "description": "test"},
    }
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.returncode, proc.stderr


def _make_fake_transcript(n_agent_dispatches: int) -> str:
    """Write a fake JSONL transcript containing N Agent tool_use entries.

    Returns the path to the temp file (caller is responsible for keeping it
    until the test finishes; tempfile-managed dir auto-cleans on test exit).
    """
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
    )
    # A few user/assistant turns interleaved with Agent dispatches.
    for i in range(3):
        f.write(json.dumps({"type": "user", "message": {"content": f"prompt {i}"}}) + "\n")
        f.write(
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {"type": "text", "text": f"response {i}"}
                        ]
                    },
                }
            )
            + "\n"
        )
    # The Agent dispatches in one assistant turn (mimics parallel dispatch).
    if n_agent_dispatches > 0:
        f.write(
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "Agent",
                                "input": {
                                    "description": f"audit dim {k}",
                                    "prompt": "...",
                                },
                            }
                            for k in range(n_agent_dispatches)
                        ]
                    },
                }
            )
            + "\n"
        )
    f.close()
    return f.name


# ------------------------------------------------------------------
# Test fixtures: (label, command, expected_block, expected_pattern_id)
# expected_pattern_id is a substring of the stderr msg if blocked.
# ------------------------------------------------------------------

TESTS = [
    # === ALLOWS (exit 0) ===
    (
        "simple echo allowed",
        "echo hello",
        False,
        "",
    ),
    (
        "git status with --short allowed",
        "git status --short",
        False,
        "",
    ),
    (
        "git diff with --shortstat allowed",
        "git diff --shortstat",
        False,
        "",
    ),
    (
        "git status piped to wc allowed",
        "git status --porcelain | wc -l",
        False,
        "",
    ),
    (
        "single-line python -c allowed",
        'py -3 -c "print(1+1)"',
        False,
        "",
    ),
    (
        "short heredoc (under 5 lines) allowed",
        "py -3 - <<'PY'\nimport os\nprint(os.getcwd())\nPY",
        False,
        "",
    ),
    (
        "non-python heredoc allowed (e.g. SQL, plain text)",
        "cat > out.txt <<'EOF'\nline 1\nline 2\nline 3\nline 4\nline 5\nline 6\nEOF",
        False,
        "",
    ),
    (
        "git commit with HEREDOC for message body allowed",
        "git commit -m \"$(cat <<'EOF'\nfix: import the missing module\n\nThis was discovered when running tests.\nCo-Authored-By: x\nEOF\n)\"",
        False,
        "",
    ),
    (
        "explicit override prefix allowed for big py heredoc",
        "# disciplined-allow: one-shot exploratory check for token alignment\npy -3 - <<'PY'\nimport sys\nfrom pathlib import Path\nfor p in Path('.').iterdir():\n    print(p)\nfor i in range(5):\n    print(i)\nPY",
        False,
        "",
    ),
    (
        "split-justified + audit-skippable allows --all-books (initial ingest)",
        "# split-justified: initial v0/morph layer ingest, single-pass deterministic\n"
        "# audit-skippable: mechanical-ingest, no classification logic\n"
        "py -3 scripts/ingest_tahot.py --all-books",
        False,
        "",
    ),
    # === BLOCKS (exit 2) ===
    (
        "5-line python heredoc blocks",
        "py -3 - <<'PY'\nimport sys\nfrom pathlib import Path\nfor p in Path('.').iterdir():\n    print(p)\nprint('done')\nPY",
        True,
        "[E1-E2]",
    ),
    (
        "10-line python heredoc with json blocks",
        "py -3 - <<'PY'\nimport json\nimport sys\nfor i in range(10):\n    obj = {'k': i}\n    print(json.dumps(obj))\nfor j in range(5):\n    print(j*2)\nprint('summary')\nPY",
        True,
        "[E1-E2]",
    ),
    (
        "apply_specs --all-books on main thread blocks",
        "py -3 scripts/apply_specs.py --all-books",
        True,
        "[A2]",
    ),
    (
        "refresh_book --all-books on main thread blocks",
        "PYTHONIOENCODING=utf-8 py -3 scripts/refresh_book.py --all-books --build",
        True,
        "[A2]",
    ),
    (
        "bare git status blocks",
        "git status",
        True,
        "[H3]",
    ),
    (
        "bare git diff blocks",
        "git diff",
        True,
        "[H3]",
    ),
    (
        "git diff with no flag in chained command blocks",
        "git add foo.py && git diff",
        True,
        "[H3]",
    ),
]


# ------------------------------------------------------------------
# A3-Step0 (audit-evidence) fixtures — these need a fake transcript
# so the hook can count Agent dispatches.
# Each fixture: (label, command, n_dispatches_in_transcript, expect_block, expected_pattern)
# ------------------------------------------------------------------

TRANSCRIPT_TESTS = [
    (
        "split-justified --all-books with 0 audits blocks on A3-Step0",
        "# split-justified: testing\npy -3 scripts/apply_specs.py --all-books",
        0,
        True,
        "[A3-Step0]",
    ),
    (
        "split-justified --all-books with 1 audit blocks on A3-Step0",
        "# split-justified: testing\npy -3 scripts/apply_specs.py --all-books",
        1,
        True,
        "[A3-Step0]",
    ),
    (
        "split-justified --all-books with 2 audits allows",
        "# split-justified: testing\npy -3 scripts/apply_specs.py --all-books",
        2,
        False,
        "",
    ),
    (
        "split-justified --all-books with 5 audits allows",
        "# split-justified: testing\npy -3 scripts/apply_specs.py --all-books",
        5,
        False,
        "",
    ),
    (
        "audit-skippable bypasses A3-Step0 (split-justified also present)",
        "# split-justified: testing\n"
        "# audit-skippable: port of validated bofm code, no novel logic\n"
        "py -3 scripts/apply_specs.py --all-books",
        0,
        False,
        "",
    ),
    (
        "disciplined-allow universal override bypasses both A2 and A3-Step0",
        "# disciplined-allow: emergency one-off corpus repair\n"
        "py -3 scripts/apply_specs.py --all-books",
        0,
        False,
        "",
    ),
    (
        "refresh_book --all-books with 2 audits + split-justified allows",
        "# split-justified: gold-standard rebuild\n"
        "py -3 scripts/refresh_book.py --all-books --build",
        2,
        False,
        "",
    ),
    (
        "non-cascade command with no audits is unaffected by A3-Step0",
        "echo hello",
        0,
        False,
        "",
    ),
]


def main() -> int:
    passed = 0
    failed = 0
    failures: list[str] = []

    for label, command, expect_block, pattern_id in TESTS:
        code, err = run_hook(command)
        was_blocked = code == 2

        ok = True
        if was_blocked != expect_block:
            ok = False
            failures.append(
                f"  [{label}] expected {'BLOCK' if expect_block else 'ALLOW'} "
                f"but got {'BLOCK' if was_blocked else 'ALLOW'} (exit {code}). "
                f"stderr={err.strip()[:200]!r}"
            )
        elif expect_block and pattern_id and pattern_id not in err:
            ok = False
            failures.append(
                f"  [{label}] blocked correctly but pattern_id {pattern_id!r} not in "
                f"stderr. stderr={err.strip()[:200]!r}"
            )

        if ok:
            passed += 1
            print(f"  PASS  {label}")
        else:
            failed += 1
            print(f"  FAIL  {label}")

    # A3-Step0 transcript-dependent fixtures
    print()
    print("--- A3-Step0 transcript fixtures ---")
    transcript_files: list[str] = []
    try:
        for label, command, n_disp, expect_block, pattern_id in TRANSCRIPT_TESTS:
            tpath = _make_fake_transcript(n_disp)
            transcript_files.append(tpath)
            code, err = run_hook(command, transcript_path=tpath)
            was_blocked = code == 2

            ok = True
            if was_blocked != expect_block:
                ok = False
                failures.append(
                    f"  [{label}] expected {'BLOCK' if expect_block else 'ALLOW'} "
                    f"but got {'BLOCK' if was_blocked else 'ALLOW'} (exit {code}). "
                    f"transcript_dispatches={n_disp}. "
                    f"stderr={err.strip()[:300]!r}"
                )
            elif expect_block and pattern_id and pattern_id not in err:
                ok = False
                failures.append(
                    f"  [{label}] blocked correctly but pattern_id {pattern_id!r} not in "
                    f"stderr. stderr={err.strip()[:300]!r}"
                )

            if ok:
                passed += 1
                print(f"  PASS  {label}")
            else:
                failed += 1
                print(f"  FAIL  {label}")
    finally:
        for tp in transcript_files:
            try:
                Path(tp).unlink()
            except Exception:
                pass

    print(f"\n=== {passed}/{passed + failed} tests passed ===")
    if failures:
        print("\nFailures:")
        for f in failures:
            print(f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
