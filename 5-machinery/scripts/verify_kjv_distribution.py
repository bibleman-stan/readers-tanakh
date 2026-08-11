#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_kjv_distribution.py — regression-test fixture for the KJV-distribution
algorithm in atu_method.kjv_alignment.distribute.

Captures the CURRENT line-by-line English-per-Hebrew-cola mapping as a
baseline, then on subsequent runs diffs the regenerated state against the
baseline. Each diff is classified as IMPROVEMENT (e.g., a known
over-break is now corrected) or REGRESSION (e.g., previously-correct
mapping is now broken).

Two modes:
  --baseline    Capture current state as baseline.json (overwrite).
  --check       Re-read current state, diff vs baseline.json, exit 1 if
                any UNCATEGORIZED diff appears (i.e., not in
                expected_improvements list).

Fixture set: read from fixtures-kjv-distribution.tsv with columns
  book        e.g. 02-exodus
  chapter     int
  verse       int
  category    e.g. "verb-bound-suffix" / "and-behold-clause-opener" /
              "translator-italic" / "control"

Output: prints a per-fixture diff with classification.

Usage:
  PYTHONIOENCODING=utf-8 py -3 5-machinery/scripts/verify_kjv_distribution.py --baseline
  PYTHONIOENCODING=utf-8 py -3 5-machinery/scripts/verify_kjv_distribution.py --check
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
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
ENG_KJV_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "eng-kjv"
FIXTURE_TSV = REPO_ROOT / "5-machinery/tests" / "fixtures-kjv-distribution.tsv"
BASELINE_JSON = REPO_ROOT / "5-machinery/tests" / "kjv-distribution-baseline.json"

# Known over-breaks that a successful fix SHOULD correct. List of
# (book, chapter, verse, category, baseline_line_n_text, expected_better_text).
# When a diff matches expected_better_text on the listed line, it counts as
# an IMPROVEMENT (not a regression).
EXPECTED_IMPROVEMENTS: list[dict] = [
    {
        "book": "02-exodus", "chapter": 2, "verse": 6,
        "category": "verb-bound-suffix",
        "note": "Hebrew line 4 (וַתַּחְמֹל עָלָיו) should carry 'on him,' from KJV. "
                "Current baseline puts 'on him,' on Hebrew line 5 (וַתֹּאמֶר). "
                "IMPROVEMENT: 'on him' moves from line 5 to line 4.",
    },
    {
        "book": "02-exodus", "chapter": 2, "verse": 3,
        "category": "verb-bound-suffix",
        "note": "'could not longer hide him' — same verb+suffix pattern as 2:6.",
    },
    {
        "book": "02-exodus", "chapter": 2, "verse": 9,
        "category": "verb-bound-suffix",
        "note": "'said unto her' / 'nurse it for me' — verb+suffix patterns.",
    },
    {
        "book": "02-exodus", "chapter": 2, "verse": 17,
        "category": "verb-bound-suffix",
        "note": "'helped them' — verb+suffix pattern; 'them' moves backward to verb's line.",
    },
]


def read_verse_lines(book: str, chapter: int, verse: int) -> list[str]:
    """Return the English-per-cola lines for the given verse."""
    chap_path = ENG_KJV_DIR / book / f"{book.split('-', 1)[1]}-{chapter:02d}.txt"
    if not chap_path.exists():
        return []
    text = chap_path.read_text(encoding="utf-8")
    lines = text.split("\n")
    in_verse = False
    out = []
    for ln in lines:
        s = ln.strip()
        if s == f"{chapter}:{verse}":
            in_verse = True
            continue
        if in_verse:
            if not s:
                break
            # Skip if we hit the next verse marker
            if ":" in s and s.split(":", 1)[0].isdigit() and s.split(":", 1)[1].isdigit():
                break
            out.append(ln)
    return out


def load_fixtures() -> list[dict]:
    if not FIXTURE_TSV.exists():
        return []
    rows = []
    with FIXTURE_TSV.open(encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            rows.append(r)
    return rows


def capture_current_state(fixtures: list[dict]) -> dict:
    out: dict[str, dict] = {}
    for r in fixtures:
        key = f"{r['book']}|{r['chapter']}|{r['verse']}"
        lines = read_verse_lines(r["book"], int(r["chapter"]), int(r["verse"]))
        out[key] = {
            "category": r.get("category", ""),
            "lines": lines,
            "hash": hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:12],
        }
    return out


def diff_states(baseline: dict, current: dict) -> tuple[list, list, list]:
    """Returns (unchanged, improvements, regressions) lists of per-fixture dicts."""
    unchanged, improvements, regressions = [], [], []
    expected_by_key = {
        f"{e['book']}|{e['chapter']}|{e['verse']}": e
        for e in EXPECTED_IMPROVEMENTS
    }
    for key in sorted(set(baseline) | set(current)):
        b = baseline.get(key)
        c = current.get(key)
        entry = {
            "key": key,
            "category": (c or b or {}).get("category", ""),
            "baseline_lines": (b or {}).get("lines", []),
            "current_lines": (c or {}).get("lines", []),
        }
        if b == c:
            unchanged.append(entry)
        elif key in expected_by_key:
            entry["note"] = expected_by_key[key]["note"]
            improvements.append(entry)
        else:
            regressions.append(entry)
    return unchanged, improvements, regressions


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--baseline", action="store_true",
                    help="Capture current state as baseline.json (overwrite)")
    ap.add_argument("--check", action="store_true",
                    help="Diff current vs baseline; exit 1 on regressions")
    args = ap.parse_args()

    if not (args.baseline or args.check):
        ap.error("Must pass --baseline or --check")

    fixtures = load_fixtures()
    if not fixtures:
        print(f"No fixtures in {FIXTURE_TSV}", file=sys.stderr)
        sys.exit(2)

    print(f"{len(fixtures)} fixture(s) loaded", file=sys.stderr)

    if args.baseline:
        state = capture_current_state(fixtures)
        BASELINE_JSON.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Baseline written to {BASELINE_JSON}", file=sys.stderr)
        print(f"  fixtures: {len(state)}", file=sys.stderr)
        sys.exit(0)

    # --check mode
    if not BASELINE_JSON.exists():
        print(f"No baseline at {BASELINE_JSON} — run --baseline first", file=sys.stderr)
        sys.exit(2)

    baseline = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
    current = capture_current_state(fixtures)
    unchanged, improvements, regressions = diff_states(baseline, current)

    print(f"\nUnchanged:    {len(unchanged)}")
    print(f"Improvements: {len(improvements)}")
    print(f"Regressions:  {len(regressions)}")

    if improvements:
        print("\n=== IMPROVEMENTS ===")
        for e in improvements:
            print(f"\n  [{e['category']}] {e['key']}")
            print(f"    note: {e.get('note', '')}")
            print("    baseline:")
            for ln in e["baseline_lines"]:
                print(f"      | {ln}")
            print("    current:")
            for ln in e["current_lines"]:
                print(f"      | {ln}")

    if regressions:
        print("\n=== REGRESSIONS (UNCATEGORIZED DIFFS — fix is unacceptable) ===")
        for e in regressions:
            print(f"\n  [{e['category']}] {e['key']}")
            print("    baseline:")
            for ln in e["baseline_lines"]:
                print(f"      | {ln}")
            print("    current:")
            for ln in e["current_lines"]:
                print(f"      | {ln}")

    sys.exit(1 if regressions else 0)


if __name__ == "__main__":
    main()
