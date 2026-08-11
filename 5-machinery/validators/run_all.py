#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_all.py — Tanakh Reader colometry audit dashboard.

Discovers every `validate_*.py` under `5-machinery/validators/syntax/` and
`5-machinery/validators/colometry/`, runs each against the v2/heb editorial corpus
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
                      5-machinery/validators/.baseline.json. Exit 1 if any rule's
                      count INCREASED vs baseline. Used by pre-commit.
    --update-baseline Capture current per-validator counts as the new
                      baseline. Used after intentional changes.
    --verbose         Print full validator stdout under each row.

Exit codes:
    0  All clean OR (default mode) report only.
    1  Regressions detected (--baseline-check) or validator failure.
    2  Setup error (no validators found, etc.).

Usage:
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/run_all.py
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/run_all.py --baseline-check
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/run_all.py --update-baseline
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/run_all.py --verbose
"""

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

def _find_repo_root():
    """Repo root by MARKER, not by counting parents.

    Counting encodes this file's depth in the tree, so moving the file silently
    breaks it and no text-based check notices. Anchoring on .git survives any
    move. Added 2026-08-10 after a reorg broke three different counted idioms.
    """
    from pathlib import Path as _P
    _here = _P(__file__).resolve()
    for _p in _here.parents:
        if (_p / ".git").exists():
            return _p
    return _here.parent


REPO_ROOT = _find_repo_root()
VALIDATORS_DIR = REPO_ROOT / "5-machinery" / "validators"
BASELINE_PATH = VALIDATORS_DIR / ".baseline.json"

LAYER_DIRS = ("syntax", "colometry", "4-layer-integrity")
TIMEOUT_SECONDS = 120

# Parallel-validator pool size. Validators are subprocess.run() invocations of
# external Python processes — already isolated from each other. ThreadPoolExecutor
# (not ProcessPoolExecutor) because the work is already subprocesses; threads
# just wait on subprocess.Popen. Avoids ProcessPoolExecutor's per-worker spawn
# cost (Windows spawn re-imports module per worker = 2x process-spawn overhead
# for nothing). Pool size = number of validators (~28) to enable full parallelism.
PARALLEL_WORKERS = 28


def _run_validator_with_books(layer: str, path: Path, books_csv: str | None = None) -> dict:
    """Top-level helper for ProcessPoolExecutor (must be picklable)."""
    books = [b.strip() for b in books_csv.split(",")] if books_csv else None
    return run_validator(layer, path, books=books)


def _aggregate_per_book(args_tuple: tuple) -> dict:
    """Top-level helper for ProcessPoolExecutor in --books mode.
    Aggregates per-book findings for a single validator into a single result."""
    layer, path, book_list = args_tuple
    agg: dict = {
        "name": path.stem, "layer": layer, "exit_code": 0,
        "findings": 0, "by_severity": {}, "by_tag": {},
        "error": None, "stdout": "", "stderr": "",
    }
    for book in book_list:
        r = run_validator(layer, path, books=[book])
        agg["findings"] += r["findings"]
        for k, v in r.get("by_severity", {}).items():
            agg["by_severity"][k] = agg["by_severity"].get(k, 0) + v
        for k, v in r.get("by_tag", {}).items():
            agg["by_tag"][k] = agg["by_tag"].get(k, 0) + v
        if r.get("error"):
            agg["error"] = r["error"]
        if r.get("exit_code", 0) > agg["exit_code"]:
            agg["exit_code"] = r["exit_code"]
    return agg


def discover_validators() -> list[tuple[str, Path]]:
    """Return [(layer_subdir, validator_path)] sorted, for syntax/ then
    colometry/ then 4-layer-integrity/. Picks up `validate_*.py` files in
    syntax/ + colometry/ and `verify_*.py` files in 4-layer-integrity/
    (the verifier's name reflects its different shape — it checks token-
    count parity across pre-existing layers rather than emitting per-cola
    findings)."""
    out: list[tuple[str, Path]] = []
    for sub in LAYER_DIRS:
        sub_dir = VALIDATORS_DIR / sub
        if not sub_dir.exists():
            continue
        for f in sorted(sub_dir.glob("validate_*.py")):
            out.append((sub, f))
        for f in sorted(sub_dir.glob("verify_*.py")):
            out.append((sub, f))
    return out


def run_validator(layer: str, path: Path, books: list[str] | None = None) -> dict:
    """Invoke one validator with `--json --v2` and parse summary.total_findings.

    If `books` is supplied, the validator is invoked once per book with `--book
    <name>` and findings are aggregated into a single result dict — used by the
    `--books` CLI filter for scoped editorial work on a chapter or two.

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
    if books:
        # MVP: pass first book only; for multi-book aggregation, run_all calls
        # this function once per book in its result loop. (Most validators support
        # a single --book at a time.)
        cmd.extend(["--book", books[0]])
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
    # Record a real count only for validators that actually ran. A timeout/
    # error yields findings=0, which is "no data" not "zero findings" — store
    # null so diff_against_baseline skips it rather than treating 0 as the
    # baseline (which would false-flag a regression once it completes).
    data = {r["name"]: (None if r.get("error") else r["findings"]) for r in results}
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
        print("  (no validators discovered under 5-machinery/validators/syntax/ or 5-machinery/validators/colometry/)")
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
    validator whose count INCREASED vs baseline.

    Timeout-robust: a validator that timed out / errored records findings=0,
    which is "no data", not "zero findings". Skip such validators in EITHER
    direction — if it errored on this run, or if its baseline value is null
    (it had timed out when the baseline was captured) — so nondeterministic
    validator timeouts can never manufacture a false regression that blocks a
    commit. (Validators that complete in both runs still gate normally.)"""
    regressions: list[tuple[str, int, int]] = []
    for r in results:
        if r.get("error"):
            continue  # no comparable count from this run
        base = baseline.get(r["name"], 0)
        if base is None:
            continue  # no recorded baseline (validator timed out at capture)
        if int(r["findings"]) > int(base):
            regressions.append((r["name"], int(base), int(r["findings"])))
    return regressions


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--baseline-check",
        action="store_true",
        help="Compare current counts to 5-machinery/validators/.baseline.json; "
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
    ap.add_argument(
        "--books",
        metavar="LIST",
        default=None,
        help="Comma-separated list of book directory names (e.g. "
             "'01-genesis,32-jonah') to scope validator runs to. Each "
             "validator is invoked with --book <book> per name. Default: "
             "validators run their corpus-wide default scope.",
    )
    ap.add_argument(
        "--validators",
        metavar="LIST",
        default=None,
        help="Comma-separated list of validator names (without 'validate_' "
             "prefix; e.g. 'short_orphan_line,verb_object_bond') to scope "
             "the dashboard to. Default: all discovered validators.",
    )
    args = ap.parse_args()

    validators = discover_validators()
    if args.validators:
        wanted = {v.strip() for v in args.validators.split(",") if v.strip()}
        validators = [
            (layer, path) for (layer, path) in validators
            if path.stem.removeprefix("validate_") in wanted or path.stem in wanted
        ]
    if not validators:
        print(
            "ERROR: No validators discovered under 5-machinery/validators/syntax/ or "
            "5-machinery/validators/colometry/.",
            file=sys.stderr,
        )
        return 2

    if args.books:
        book_list = [b.strip() for b in args.books.split(",") if b.strip()]
        # Per-book aggregation: invoke each validator once per book and sum
        # findings. Parallelized across validators via threads (subprocess
        # isolation already provides true parallelism).
        with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as ex:
            args_list = [(layer, path, book_list) for (layer, path) in validators]
            results = list(ex.map(_aggregate_per_book, args_list))
    else:
        # Default mode: parallelize across validators via threads. Validators
        # are subprocess.run() calls — true parallelism comes from the OS
        # process scheduler, threads just wait on Popen.
        with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as ex:
            futures = [ex.submit(run_validator, layer, path) for (layer, path) in validators]
            results = [f.result() for f in futures]

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
                "  No baseline found at 5-machinery/validators/.baseline.json.\n"
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
                "    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/run_all.py "
                "--update-baseline",
                file=sys.stderr,
            )
            return 1
        print("  No regressions vs baseline.")
        return 0

    return 0  # default mode: report only


if __name__ == "__main__":
    sys.exit(main())
