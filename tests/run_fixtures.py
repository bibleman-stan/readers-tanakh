#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fixture runner for Tanakh validator regression tests.

For each validator, runs each good/bad fixture and verifies:
  - good-*.txt  → 0 findings (validator exit code 0)
  - bad-*.txt   → ≥1 finding (validator exit code 1)

Usage:
    PYTHONIOENCODING=utf-8 py -3 tests/run_fixtures.py
    PYTHONIOENCODING=utf-8 py -3 tests/run_fixtures.py --validator validate_maqqef_integrity
    PYTHONIOENCODING=utf-8 py -3 tests/run_fixtures.py --verbose

The runner creates a temporary directory that mirrors the expected layout:
    <tmpdir>/v1/he-baseline/<fixture_book_name>/<fixture>.txt

Each validator is invoked with --book <fixture_book_name> pointed at the
temp tree, so the validator can discover the file via its normal glob path.

Exit code: 0 if all pass, 1 if any fail.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
VALIDATORS_SYNTAX = REPO_ROOT / "validators" / "syntax"
VALIDATORS_COLOMETRY = REPO_ROOT / "validators" / "colometry"

# ---------------------------------------------------------------------------
# Validator registry
# Maps validator name → (script path relative to repo root, book_name to use in temp tree)
# ---------------------------------------------------------------------------
VALIDATOR_MAP = {
    "validate_maqqef_integrity": VALIDATORS_SYNTAX / "validate_maqqef_integrity.py",
    "validate_line_final_tokens": VALIDATORS_SYNTAX / "validate_line_final_tokens.py",
    "validate_speech_intro_framing": VALIDATORS_COLOMETRY / "validate_speech_intro_framing.py",
    "validate_construct_chain": VALIDATORS_COLOMETRY / "validate_construct_chain.py",
    "validate_wayehi_protasis": VALIDATORS_COLOMETRY / "validate_wayehi_protasis.py",
    "validate_discourse_particles": VALIDATORS_COLOMETRY / "validate_discourse_particles.py",
    "validate_complement_integrity": VALIDATORS_COLOMETRY / "validate_complement_integrity.py",
    "validate_cross_verse_continuity": VALIDATORS_COLOMETRY / "validate_cross_verse_continuity.py",
}

# ANSI colors (suppress when not a tty)
_tty = sys.stdout.isatty()
RED   = "\033[31m" if _tty else ""
GREEN = "\033[32m" if _tty else ""
YELLOW = "\033[33m" if _tty else ""
RESET = "\033[0m"  if _tty else ""


# ---------------------------------------------------------------------------
# Helper: run validator against a single fixture file
# ---------------------------------------------------------------------------

def run_validator_on_fixture(
    validator_script: Path,
    fixture_path: Path,
    verbose: bool = False,
) -> dict:
    """
    Copy fixture into a temp directory tree, invoke the validator with --json,
    and return a result dict with keys:
        fixture, kind, passed, findings_count, stdout, stderr, returncode
    """
    fixture_name = fixture_path.stem  # e.g. "good-01"
    kind = "good" if fixture_name.startswith("good") else "bad"

    # Build temp dir: <tmpdir>/v1/he-baseline/<fixture_stem>/<fixture>.txt
    # We use the fixture stem as the "book" name so --book points to it.
    book_name = f"fixture-{fixture_name}"

    with tempfile.TemporaryDirectory() as tmpdir:
        # Mirror the expected validator path:
        #   <tmpdir>/data/text-files/v1/he-baseline/<book_name>/<fixture>.txt
        # But the validator derives REPO_ROOT from its own __file__ location,
        # so we can't redirect it to tmpdir.  Instead, we symlink / copy the
        # fixture into the REAL v1/he-baseline/<book_name>/ directory,
        # run the validator, then clean up.

        # Path inside the real repo:
        v1_dir = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
        book_dir = v1_dir / book_name
        target_file = book_dir / fixture_path.name

        try:
            book_dir.mkdir(parents=True, exist_ok=True)
            # Copy fixture file (strip comment lines so validator reads pure Hebrew)
            _copy_fixture_stripped(fixture_path, target_file)

            cmd = [
                sys.executable,
                str(validator_script),
                "--book", book_name,
                "--json",
            ]
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
            )

            # Parse JSON output to count findings
            findings_count = 0
            json_parse_error = None
            try:
                if result.stdout.strip():
                    doc = json.loads(result.stdout)
                    findings_count = doc.get("summary", {}).get("total_findings", 0)
                else:
                    # Some validators may emit nothing on error — use returncode
                    findings_count = 0
            except json.JSONDecodeError as e:
                json_parse_error = str(e)

            # Determine pass/fail:
            # good fixtures → expect 0 findings (exit 0)
            # bad fixtures  → expect ≥1 findings (exit 1)
            if kind == "good":
                passed = (findings_count == 0)
            else:
                passed = (findings_count >= 1)

            return {
                "fixture": fixture_path.name,
                "kind": kind,
                "passed": passed,
                "findings_count": findings_count,
                "returncode": result.returncode,
                "stdout": result.stdout if verbose else "",
                "stderr": result.stderr if verbose else "",
                "json_parse_error": json_parse_error,
            }

        finally:
            # Always clean up the temp book directory
            if book_dir.exists():
                shutil.rmtree(book_dir)


def _copy_fixture_stripped(src: Path, dst: Path) -> None:
    """Copy fixture file to dst, stripping Python-style comment lines (# ...).

    The validators read plain Hebrew text; comments would produce garbage tokens.
    """
    lines = src.read_text(encoding="utf-8").splitlines(keepends=True)
    cleaned = [ln for ln in lines if not ln.lstrip().startswith("#")]
    dst.write_text("".join(cleaned), encoding="utf-8")


# ---------------------------------------------------------------------------
# Per-validator runner
# ---------------------------------------------------------------------------

def run_validator(
    validator_name: str,
    verbose: bool = False,
) -> dict:
    """Run all fixtures for one validator. Returns summary dict."""
    script = VALIDATOR_MAP.get(validator_name)
    if script is None:
        return {"validator": validator_name, "error": "unknown validator", "pass": 0, "fail": 0}

    if not script.exists():
        return {"validator": validator_name, "error": f"script not found: {script}", "pass": 0, "fail": 0}

    fixture_dir = FIXTURES_DIR / validator_name
    if not fixture_dir.exists():
        return {"validator": validator_name, "error": f"fixture dir not found: {fixture_dir}", "pass": 0, "fail": 0}

    fixtures = sorted(fixture_dir.glob("*.txt"))
    if not fixtures:
        return {"validator": validator_name, "error": "no fixtures found", "pass": 0, "fail": 0}

    pass_count = 0
    fail_count = 0
    results = []

    for fixture_path in fixtures:
        r = run_validator_on_fixture(script, fixture_path, verbose=verbose)
        results.append(r)
        if r["passed"]:
            pass_count += 1
        else:
            fail_count += 1

    return {
        "validator": validator_name,
        "pass": pass_count,
        "fail": fail_count,
        "results": results,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--validator", "-v",
        metavar="NAME",
        help="Run only this validator (e.g. validate_maqqef_integrity). Default: all.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show validator stdout/stderr for each fixture.",
    )
    args = parser.parse_args()

    if args.validator:
        validators_to_run = [args.validator]
    else:
        validators_to_run = list(VALIDATOR_MAP.keys())

    print("=" * 72)
    print("Tanakh validator fixture regression suite")
    print(f"Fixtures dir : {FIXTURES_DIR}")
    print(f"Validators   : {len(validators_to_run)}")
    print("=" * 72)
    print()

    grand_pass = 0
    grand_fail = 0
    any_error = False

    for vname in validators_to_run:
        summary = run_validator(vname, verbose=args.verbose)

        if "error" in summary:
            print(f"{YELLOW}SKIP{RESET}  {vname}: {summary['error']}")
            any_error = True
            continue

        p = summary["pass"]
        f = summary["fail"]
        grand_pass += p
        grand_fail += f

        status = f"{GREEN}PASS{RESET}" if f == 0 else f"{RED}FAIL{RESET}"
        print(f"{status}  {vname}  ({p} passed, {f} failed)")

        # Detail on failures
        for r in summary.get("results", []):
            if not r["passed"]:
                expected = "0 findings" if r["kind"] == "good" else "≥1 findings"
                got = f"{r['findings_count']} findings"
                print(f"       {RED}FAIL{RESET}  {r['fixture']}  expected={expected}  got={got}")
                if r.get("json_parse_error"):
                    print(f"             JSON parse error: {r['json_parse_error']}")
                if args.verbose and r.get("stderr"):
                    print(f"             stderr: {r['stderr'][:200]}")
            elif args.verbose:
                print(f"       {GREEN}ok{RESET}    {r['fixture']}  ({r['findings_count']} findings)")

    print()
    print("=" * 72)
    overall = f"{GREEN}ALL PASS{RESET}" if grand_fail == 0 and not any_error else f"{RED}FAILURES PRESENT{RESET}"
    print(f"Result : {overall}")
    print(f"Passed : {grand_pass}")
    print(f"Failed : {grand_fail}")
    print("=" * 72)

    sys.exit(0 if grand_fail == 0 and not any_error else 1)


if __name__ == "__main__":
    main()
