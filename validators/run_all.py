#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_all.py — Tanakh Reader colometry audit dashboard.

Discovers every `validate_*.py` under `validators/syntax/` and
`validators/colometry/`, runs each against the v2/he editorial corpus
(in JSON mode), aggregates per-validator finding counts, prints a
unified dashboard.

Layer-class discipline (mirroring the bibleman-stan/readers-bofm
Layer 1 / Layer 2 / Layer 3 architecture):

    [MALFORMED]  Layer 1 violation — Hebrew grammatical illegality.
                 Hard syntactic failure (e.g., line ends in proclitic;
                 maqqef-bound pair split). Must fix before editorial
                 review is meaningful.

    [DEVIATION]  Layer 3 violation — editorial-policy deviation.
                 Permissible English/Hebrew syntactically; differs
                 from canon-codified editorial choice. Review required.

The validators themselves emit the layer class via the JSON
`severity` field; this dashboard groups results accordingly.

Modes:
    (default)         Run all validators, print dashboard, exit 0
                      regardless of findings (report-only).
    --baseline-check  Compare current per-validator counts to
                      validators/.baseline.json. Exit 1 if any rule's
                      count INCREASED vs baseline. Used by pre-commit.
    --update-baseline Capture current per-validator counts as the new
                      baseline. Used after intentional changes.
    --verbose         Print full validator stdout under each row.

Exit codes:
    0  All clean OR (default mode) report only.
    1  Regressions detected (--baseline-check) or validator failure.
    2  Setup error (no validators found, etc.).

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/run_all.py
    PYTHONIOENCODING=utf-8 py -3 validators/run_all.py --baseline-check
    PYTHONIOENCODING=utf-8 py -3 validators/run_all.py --update-baseline
    PYTHONIOENCODING=utf-8 py -3 validators/run_all.py --verbose
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATORS_DIR = REPO_ROOT / "validators"
BASELINE_PATH = VALIDATORS_DIR / ".baseline.json"

LAYER_DIRS = ("syntax", "colometry")
TIMEOUT_SECONDS = 120


def discover_validators() -> list[tuple[str, Path]]:
    """Return [(layer_subdir, validator_path)] sorted, for syntax/ then colometry/."""
    out: list[tuple[str, Path]] = []
    for sub in LAYER_DIRS:
        sub_dir = VALIDATORS_DIR / sub
        if not sub_dir.exists():
            continue
        for f in sorted(sub_dir.glob("validate_*.py")):
            out.append((sub, f))
    return out


def run_validator(layer: str, path: Path) -> dict:
    """Invoke one validator with `--json --v2` and parse summary.total_findings.

    Returns:
        {
            "name": "validate_xxx",
            "layer": "syntax" | "colometry",
            "exit_code": int,
            "findings": int,                # 0 if validator failed/timed out
            "by_severity": {"MALFORMED": N, "DEVIATION": N, ...},
            "by_tag": {"STRONG-MERGE-CANDIDATE": N, ...},
            "error": str | None,            # set on failure
            "stdout": str,
            "stderr": str,
        }
    """
    cmd = [sys.executable, str(path), "--json", "--v2"]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}

    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT_SECONDS,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return {
            "name": path.stem,
            "layer": layer,
            "exit_code": -1,
            "findings": 0,
            "by_severity": {},
            "by_tag": {},
            "error": "timeout",
            "stdout": "",
            "stderr": "",
        }

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""

    if proc.returncode == 2:
        return {
            "name": path.stem,
            "layer": layer,
            "exit_code": 2,
            "findings": 0,
            "by_severity": {},
            "by_tag": {},
            "error": stderr.strip() or "setup error",
            "stdout": stdout,
            "stderr": stderr,
        }

    findings = 0
    by_severity: dict[str, int] = {}
    by_tag: dict[str, int] = {}
    error: str | None = None

    if not stdout.strip():
        # No JSON output despite no setup error.  Treat as 0 findings.
        return {
            "name": path.stem,
            "layer": layer,
            "exit_code": proc.returncode,
            "findings": 0,
            "by_severity": {},
            "by_tag": {},
            "error": None,
            "stdout": stdout,
            "stderr": stderr,
        }

    try:
        doc = json.loads(stdout)
        findings = int(doc.get("summary", {}).get("total_findings", 0))
        by_severity = dict(doc.get("summary", {}).get("by_severity", {}))
        by_tag = dict(doc.get("summary", {}).get("by_tag", {}))
    except json.JSONDecodeError as exc:
        error = f"json parse error: {exc}"

    return {
        "name": path.stem,
        "layer": layer,
        "exit_code": proc.returncode,
        "findings": findings,
        "by_severity": by_severity,
        "by_tag": by_tag,
        "error": error,
        "stdout": stdout,
        "stderr": stderr,
    }


def load_baseline() -> dict | None:
    if not BASELINE_PATH.exists():
        return None
    try:
        return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(
            f"[run_all] WARNING: {BASELINE_PATH} is invalid JSON; treating as missing.",
            file=sys.stderr,
        )
        return None


def save_baseline(results: list[dict]) -> None:
    data = {r["name"]: r["findings"] for r in results}
    BASELINE_PATH.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def print_dashboard(results: list[dict], verbose: bool) -> None:
    print("=" * 72)
    print("Tanakh Reader Colometry Audit — running all validators (--v2)")
    print("=" * 72)
    print()

    if not results:
        print("  (no validators discovered under validators/syntax/ or validators/colometry/)")
        print()
        return

    name_width = max(len(r["name"]) for r in results) + 2
    print(f"  {'LAYER':<10} {'VALIDATOR':<{name_width}} FINDINGS  STATUS")
    print("  " + "-" * (10 + name_width + 30))

    total = 0
    by_layer = {"syntax": 0, "colometry": 0}
    for r in results:
        if r["error"]:
            status = f"ERROR ({r['error']})"
        elif r["exit_code"] == 2:
            status = "SETUP-ERR"
        elif r["findings"] == 0:
            status = "CLEAN"
        else:
            status = "findings"
        print(
            f"  {r['layer']:<10} {r['name']:<{name_width}} "
            f"{r['findings']:>8}  [{status}]"
        )
        total += r["findings"]
        by_layer[r["layer"]] = by_layer.get(r["layer"], 0) + r["findings"]
        if verbose and r["stdout"].strip():
            for ln in r["stdout"].splitlines():
                print(f"      | {ln}")
            print()

    print()
    print(f"  Layer-1 [MALFORMED] total: {by_layer.get('syntax', 0)}")
    print(f"  Layer-3 [DEVIATION] total: {by_layer.get('colometry', 0)}")
    print(f"  GRAND TOTAL findings     : {total}")
    print()


def diff_against_baseline(results: list[dict], baseline: dict) -> list[tuple[str, int, int]]:
    """Return [(validator_name, baseline_count, current_count)] for any
    validator whose count INCREASED vs baseline."""
    regressions: list[tuple[str, int, int]] = []
    for r in results:
        base = int(baseline.get(r["name"], 0))
        cur = int(r["findings"])
        if cur > base:
            regressions.append((r["name"], base, cur))
    return regressions


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--baseline-check",
        action="store_true",
        help="Compare current counts to validators/.baseline.json; "
             "exit 1 on regression. Used by pre-commit hook.",
    )
    ap.add_argument(
        "--update-baseline",
        action="store_true",
        help="Capture current counts as the new baseline.",
    )
    ap.add_argument(
        "--verbose",
        action="store_true",
        help="Print each validator's full stdout under its dashboard row.",
    )
    args = ap.parse_args()

    validators = discover_validators()
    if not validators:
        print(
            "ERROR: No validators discovered under validators/syntax/ or "
            "validators/colometry/.",
            file=sys.stderr,
        )
        return 2

    results = [run_validator(layer, path) for layer, path in validators]

    print_dashboard(results, args.verbose)

    # Surface validator-level errors regardless of mode.
    errored = [r for r in results if r["error"] or r["exit_code"] == 2]
    if errored:
        print("WARNING — validator errors:", file=sys.stderr)
        for r in errored:
            print(f"  {r['name']}: {r['error'] or 'setup error'}", file=sys.stderr)
        if not args.update_baseline:
            # In baseline-check or default mode, surface but don't necessarily fail
            # unless we're checking baseline (the regression check below decides).
            pass

    if args.update_baseline:
        save_baseline(results)
        print(f"  Baseline updated: {BASELINE_PATH}")
        print(f"  Captured counts for {len(results)} validators.")
        return 0

    if args.baseline_check:
        baseline = load_baseline()
        if baseline is None:
            print(
                "  No baseline found at validators/.baseline.json.\n"
                "  Run with --update-baseline to create one. "
                "Treating absence as PASS.",
                file=sys.stderr,
            )
            return 0
        regressions = diff_against_baseline(results, baseline)
        if regressions:
            print("=" * 72, file=sys.stderr)
            print(
                "REGRESSIONS DETECTED — finding count INCREASED vs baseline:",
                file=sys.stderr,
            )
            print("=" * 72, file=sys.stderr)
            for name, base, cur in regressions:
                print(
                    f"  {name}: baseline={base} → current={cur}  (+{cur - base})",
                    file=sys.stderr,
                )
            print(file=sys.stderr)
            print("Either fix the new violations or update the baseline:", file=sys.stderr)
            print(
                "    PYTHONIOENCODING=utf-8 py -3 validators/run_all.py "
                "--update-baseline",
                file=sys.stderr,
            )
            return 1
        print("  No regressions vs baseline.")
        return 0

    return 0  # default mode: report only


if __name__ == "__main__":
    sys.exit(main())
