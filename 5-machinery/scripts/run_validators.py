#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Spec-driven validator runner.

Iterates all YAML specs in `5-machinery/validators/specs/` over the v2/heb corpus and emits
findings. Replaces the per-rule `validate_*.py` build pattern with declarative
specs.

Usage:
  py -3 5-machinery/scripts/run_validators.py
  py -3 5-machinery/scripts/run_validators.py --book genesis
  py -3 5-machinery/scripts/run_validators.py --rule M2
  py -3 5-machinery/scripts/run_validators.py --severity STRONG-MERGE-CANDIDATE
  py -3 5-machinery/scripts/run_validators.py --json
  py -3 5-machinery/scripts/run_validators.py --json --book genesis --rule H18.1

PYTHONIOENCODING=utf-8 mandatory on Windows for Hebrew Unicode.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure project root is on path
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


ROOT = _find_repo_root()
sys.path.insert(0, str(ROOT))

from validators._shared.spec_runner import SpecRunner  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Spec-driven Tanakh validator runner")
    ap.add_argument("--book", help="filter to book (substring match on directory name)")
    ap.add_argument("--rule", help="filter to rule (e.g., 'M2', 'H18.1')")
    ap.add_argument("--severity",
                    choices=["STRONG-MERGE-CANDIDATE", "REVIEW-REQUIRED", "MALFORMED"],
                    help="filter to severity")
    ap.add_argument("--corpus", default="data/text-files/v2/heb",
                    help="corpus directory (default: v2/heb)")
    ap.add_argument("--specs", default="5-machinery/validators/specs",
                    help="specs directory (default: 5-machinery/validators/specs)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--summary", action="store_true",
                    help="emit only counts per spec, no per-finding output")
    args = ap.parse_args()

    runner = SpecRunner(args.specs)
    findings = runner.run_corpus(
        args.corpus,
        book_filter=args.book,
        rule_filter=args.rule,
        severity_filter=args.severity,
    )

    if args.summary:
        per_spec: dict[str, dict[str, int]] = {}
        for f in findings:
            d = per_spec.setdefault(f"{f.rule}/{f.subcase}", {})
            d[f.severity] = d.get(f.severity, 0) + 1
        if args.json:
            print(json.dumps({
                "specs_loaded": len(runner.specs),
                "total_findings": len(findings),
                "per_spec": per_spec,
            }, ensure_ascii=False, indent=2))
        else:
            print(f"Specs loaded: {len(runner.specs)}")
            print(f"Total findings: {len(findings)}")
            for spec_name, by_sev in sorted(per_spec.items()):
                bits = ", ".join(f"{k}={v}" for k, v in sorted(by_sev.items()))
                print(f"  {spec_name}  {bits}")
        return 0 if not findings else 1

    if args.json:
        out = {
            "specs_loaded": len(runner.specs),
            "total_findings": len(findings),
            "findings": [f.to_dict() for f in findings],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for f in findings:
            print(f.to_text())
        print(f"\n--- {len(findings)} findings across {len(runner.specs)} specs ---",
              file=sys.stderr)

    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
