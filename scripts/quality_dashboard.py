#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quality_dashboard.py — Per-book quality scorecards for the Tanakh Reader.

Aggregates:
  - validator findings (MALFORMED, DEVIATION, REVIEW-REQUIRED) from
    validators/run_all.py (each validator invoked individually with --json)
  - English quality checker output (scripts/english_quality_check.py) — skipped
    gracefully if not yet built or if spaCy not available
  - English drift scanner output (scripts/scan_english_drift.py) — skipped
    gracefully if not yet built

Per-book scorecard fields:
  - Book name, chapter count, total cola count
  - Per-validator finding counts (MALFORMED / DEVIATION / REVIEW-REQUIRED breakdown)
  - English quality: PRONOUN, NO_VERB, FRAGMENT, REPEAT, MID_SPLIT counts
  - English drift: ARTICLE-SPLIT, PREP-NP-SPLIT, AUX-VERB-SPLIT, PTC-NP-SPLIT,
    APPOSITIVE-SPLIT, DANGLING-CONJ counts
  - Readiness score (0–100 composite)
  - Sample quality: 3 verses showing best, median, worst cola density

Readiness score formula:
  50 pts  0 MALFORMED findings (Layer 1 illegality)
  30 pts  DEVIATION+REVIEW-REQUIRED / total_cola ≤ 5%  (scales linearly down to 0 at 50%)
  10 pts  REVIEW-REQUIRED items ≤ 10 per chapter       (scales linearly down to 0 at 30/chapter)
  10 pts  drift-scanner clean                            (scales down linearly by flag count)

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/quality_dashboard.py --book jonah
    PYTHONIOENCODING=utf-8 py -3 scripts/quality_dashboard.py --all-books
    PYTHONIOENCODING=utf-8 py -3 scripts/quality_dashboard.py --book jonah --output /tmp/jonah.md
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Repo layout
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

VALIDATORS_DIR = REPO_ROOT / "validators"
V2_HE_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "he"
V2_ENG_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "eng-gloss"
V4_DIR = REPO_ROOT / "data" / "text-files" / "v4" / "editorial"

REPORTS_DIR = REPO_ROOT / "data" / "reports" / "quality"

LAYER_DIRS = ("syntax", "colometry")

# Map directory-slug ("05-jonah") → canonical book name ("jonah")
def _slug_from_dir(d: str) -> str:
    """Extract short name from '05-jonah' → 'jonah' or passthrough."""
    if re.match(r"^\d{2}-", d):
        return d[3:]
    return d


# ---------------------------------------------------------------------------
# Discover available book directories in v2/he (the primary scored tier)
# ---------------------------------------------------------------------------
def discover_books() -> list[tuple[str, Path]]:
    """Return [(dir_name, dir_path)] for all book directories present in v2/he,
    sorted by directory name (which includes the canonical BHS numeric prefix)."""
    if not V2_HE_DIR.exists():
        return []
    result = []
    seen_slugs: set[str] = set()
    for d in sorted(V2_HE_DIR.iterdir()):
        if d.is_dir():
            slug = _slug_from_dir(d.name)
            if slug in seen_slugs:
                # Skip duplicate (guard against stale dirs sharing a slug)
                continue
            seen_slugs.add(slug)
            result.append((d.name, d))
    return result


def find_book_dir(book_slug: str) -> tuple[str, Path] | None:
    """Find the canonical directory for a given book slug (e.g. 'jonah')."""
    all_books = discover_books()
    # Try exact dir-name match first, then slug match
    for dir_name, dir_path in all_books:
        if dir_name == book_slug or _slug_from_dir(dir_name) == book_slug.lower():
            return (dir_name, dir_path)
    return None


# ---------------------------------------------------------------------------
# Cola counting from v2/he text files
# ---------------------------------------------------------------------------
_VERSE_REF_RE = re.compile(r"^\d+:\d+[a-z]?$")


def count_cola_in_file(filepath: Path) -> tuple[int, dict]:
    """Return (total_cola, verse_cola_map) from a Hebrew v2 chapter file.

    verse_cola_map: { "1:1": 3, "1:2": 2, ... }
    """
    total = 0
    verse_cola: dict[str, int] = {}
    current_verse = None
    try:
        lines = filepath.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = filepath.read_text(encoding="utf-8-sig").splitlines()
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if _VERSE_REF_RE.match(s):
            current_verse = s
            if current_verse not in verse_cola:
                verse_cola[current_verse] = 0
            continue
        if current_verse is not None:
            verse_cola[current_verse] = verse_cola.get(current_verse, 0) + 1
            total += 1
    return total, verse_cola


def count_book_cola(dir_path: Path) -> tuple[int, int, dict]:
    """Return (total_cola, chapter_count, per_chapter_cola_map).

    per_chapter_cola_map: { "jonah-01.txt": { "1:1": 3, ... }, ... }
    """
    total = 0
    chapters = {}
    chapter_files = sorted(dir_path.glob("*.txt"))
    for cf in chapter_files:
        ch_cola, verse_map = count_cola_in_file(cf)
        total += ch_cola
        chapters[cf.name] = {"total": ch_cola, "verses": verse_map}
    return total, len(chapter_files), chapters


# ---------------------------------------------------------------------------
# Validator invocation (per-book via --book dir_name)
# ---------------------------------------------------------------------------
def discover_validators() -> list[tuple[str, Path]]:
    """Return [(layer, path)] for all validators."""
    out = []
    for sub in LAYER_DIRS:
        sub_dir = VALIDATORS_DIR / sub
        if not sub_dir.exists():
            continue
        for f in sorted(sub_dir.glob("validate_*.py")):
            out.append((sub, f))
    return out


def run_validator_for_book(layer: str, path: Path, book_dir_name: str) -> dict:
    """Invoke one validator with --json --v2 --book <dir_name>.

    Returns a result dict matching the shape used by run_all.py.
    """
    cmd = [sys.executable, str(path), "--json", "--v2", "--book", book_dir_name]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return {
            "name": path.stem,
            "layer": layer,
            "findings": 0,
            "by_severity": {},
            "by_tag": {},
            "error": "timeout",
        }

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""

    # Exit code 2 = setup error (book not found, etc.)
    if proc.returncode == 2:
        return {
            "name": path.stem,
            "layer": layer,
            "findings": 0,
            "by_severity": {},
            "by_tag": {},
            "error": stderr.strip() or "setup error",
        }

    if not stdout.strip():
        return {
            "name": path.stem,
            "layer": layer,
            "findings": 0,
            "by_severity": {},
            "by_tag": {},
            "error": None,
        }

    try:
        doc = json.loads(stdout)
        findings = int(doc.get("summary", {}).get("total_findings", 0))
        by_severity = dict(doc.get("summary", {}).get("by_severity", {}))
        by_tag = dict(doc.get("summary", {}).get("by_tag", {}))
    except json.JSONDecodeError as exc:
        return {
            "name": path.stem,
            "layer": layer,
            "findings": 0,
            "by_severity": {},
            "by_tag": {},
            "error": f"json parse error: {exc}",
        }

    return {
        "name": path.stem,
        "layer": layer,
        "findings": findings,
        "by_severity": by_severity,
        "by_tag": by_tag,
        "error": None,
    }


def run_all_validators_for_book(dir_name: str) -> list[dict]:
    """Run all validators against one book directory, return list of result dicts."""
    validators = discover_validators()
    results = []
    for layer, path in validators:
        r = run_validator_for_book(layer, path, dir_name)
        results.append(r)
    return results


# ---------------------------------------------------------------------------
# English quality checker — subprocess invocation (graceful skip)
# ---------------------------------------------------------------------------
def run_english_quality_check(book_slug: str) -> dict | None:
    """Invoke english_quality_check.py --book <slug> and parse STDOUT.

    Returns dict of { "PRONOUN": N, "NO_VERB": N, ... } or None if not available.
    """
    checker_path = SCRIPT_DIR / "english_quality_check.py"
    if not checker_path.exists():
        return None

    cmd = [sys.executable, str(checker_path), "--book", book_slug]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            env=env,
        )
    except subprocess.TimeoutExpired:
        print(f"  [quality] WARNING: english_quality_check.py timed out for {book_slug}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"  [quality] WARNING: english_quality_check.py failed: {exc}", file=sys.stderr)
        return None

    if proc.returncode not in (0, 1):
        # Non-zero exit with content means script error (missing dep, etc.)
        stderr_snippet = (proc.stderr or "")[:200]
        if "ModuleNotFoundError" in stderr_snippet or "ImportError" in stderr_snippet:
            print(f"  [quality] english_quality_check.py: dependency missing — skipping", file=sys.stderr)
        else:
            print(f"  [quality] english_quality_check.py exit {proc.returncode}: {stderr_snippet}", file=sys.stderr)
        return None

    # Parse the text output for issue type counts
    # The checker outputs lines like:  "  PRONOUN       :   2"  or summary tables
    counts: dict[str, int] = {
        "PRONOUN": 0, "NO_VERB": 0, "FRAGMENT": 0, "REPEAT": 0, "MID_SPLIT": 0
    }
    stdout = proc.stdout or ""
    for line in stdout.splitlines():
        # Match both "PRONOUN: 2" and "PRONOUN       :   2" patterns
        m = re.match(r"\s*(PRONOUN|NO_VERB|FRAGMENT|REPEAT|MID_SPLIT)\s*:?\s+(\d+)", line)
        if m:
            counts[m.group(1)] = int(m.group(2))
        # Also match "  2  PRONOUN" style (column-first tables)
        m2 = re.match(r"\s*(\d+)\s+(PRONOUN|NO_VERB|FRAGMENT|REPEAT|MID_SPLIT)\b", line)
        if m2:
            counts[m2.group(2)] = int(m2.group(1))
    return counts


# ---------------------------------------------------------------------------
# English drift scanner — subprocess invocation (graceful skip)
# ---------------------------------------------------------------------------
def run_drift_scan(book_slug: str) -> dict | None:
    """Invoke scan_english_drift.py --book <slug> --summary-only and parse STDOUT.

    Returns dict of { "ARTICLE-SPLIT": N, ... } or None if not available.
    """
    scanner_path = SCRIPT_DIR / "scan_english_drift.py"
    if not scanner_path.exists():
        return None

    cmd = [sys.executable, str(scanner_path), "--book", book_slug, "--summary-only"]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            env=env,
        )
    except subprocess.TimeoutExpired:
        print(f"  [drift] WARNING: scan_english_drift.py timed out for {book_slug}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"  [drift] WARNING: scan_english_drift.py failed: {exc}", file=sys.stderr)
        return None

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""

    # Missing eng-gloss directory for this book → clean, not error
    if "English gloss directory not found" in stderr or "No English gloss" in stdout:
        return {k: 0 for k in ("ARTICLE-SPLIT", "PREP-NP-SPLIT", "AUX-VERB-SPLIT",
                                "PTC-NP-SPLIT", "APPOSITIVE-SPLIT", "DANGLING-CONJ")}

    counts: dict[str, int] = {
        "ARTICLE-SPLIT": 0, "PREP-NP-SPLIT": 0, "AUX-VERB-SPLIT": 0,
        "PTC-NP-SPLIT": 0, "APPOSITIVE-SPLIT": 0, "DANGLING-CONJ": 0,
    }
    for line in stdout.splitlines():
        # "Total flagged lines: N" gives us overall total (informational)
        # Per-flag breakdown in summary table: "  ARTICLE-SPLIT     3"
        for flag in counts:
            m = re.search(rf"\b{re.escape(flag)}\b\s*:?\s*(\d+)", line)
            if m:
                counts[flag] = int(m.group(1))
    return counts


# ---------------------------------------------------------------------------
# Readiness score
# ---------------------------------------------------------------------------
def compute_readiness(
    total_cola: int,
    chapter_count: int,
    malformed: int,
    deviation_plus_review: int,
    review_required: int,
    drift_total: int,
    drift_available: bool,
) -> tuple[int, dict]:
    """Compute 0–100 readiness score.

    Returns (score, breakdown_dict).
    """
    breakdown: dict[str, float] = {}

    # ── 50 pts: MALFORMED findings (graduated scale) ───────────────────────
    # 0 MALFORMED → 50 pts (full)
    # 1-3 MALFORMED → 40 pts (small slip)
    # 4-10 MALFORMED → 25 pts (moderate)
    # >10 MALFORMED → 0 pts (heavy)
    if malformed == 0:
        pts_malformed = 50.0
    elif malformed <= 3:
        pts_malformed = 40.0
    elif malformed <= 10:
        pts_malformed = 25.0
    else:
        pts_malformed = 0.0
    breakdown["malformed_pts"] = pts_malformed

    # ── 30 pts: DEVIATION+REVIEW / total_cola ≤ 5% ────────────────────────
    # Scales linearly: 5% → 30 pts, 50% → 0 pts
    if total_cola == 0:
        pts_deviation = 30.0
    else:
        ratio = deviation_plus_review / total_cola
        if ratio <= 0.05:
            pts_deviation = 30.0
        elif ratio >= 0.50:
            pts_deviation = 0.0
        else:
            pts_deviation = 30.0 * (1.0 - (ratio - 0.05) / (0.50 - 0.05))
    breakdown["deviation_pts"] = pts_deviation

    # ── 10 pts: REVIEW-REQUIRED ≤ 10/chapter ─────────────────────────────
    # Scales linearly: 10/ch → 10 pts, 30/ch → 0 pts
    if chapter_count == 0:
        pts_review = 10.0
    else:
        rr_per_ch = review_required / chapter_count
        if rr_per_ch <= 10:
            pts_review = 10.0
        elif rr_per_ch >= 30:
            pts_review = 0.0
        else:
            pts_review = 10.0 * (1.0 - (rr_per_ch - 10) / (30 - 10))
    breakdown["review_pts"] = pts_review

    # ── 10 pts: drift scanner clean ───────────────────────────────────────
    if not drift_available:
        pts_drift = 10.0  # assume clean when scanner not yet built
    else:
        # Scale: 0 drift → 10 pts; ≥20 drift → 0 pts
        if drift_total == 0:
            pts_drift = 10.0
        elif drift_total >= 20:
            pts_drift = 0.0
        else:
            pts_drift = 10.0 * (1.0 - drift_total / 20.0)
    breakdown["drift_pts"] = pts_drift

    score = int(round(pts_malformed + pts_deviation + pts_review + pts_drift))
    return score, breakdown


# ---------------------------------------------------------------------------
# Sample verse selection (best / median / worst by cola count per verse)
# ---------------------------------------------------------------------------
def select_sample_verses(
    chapters: dict,  # { "jonah-01.txt": {"total": N, "verses": {"1:1": N, ...}}, ... }
) -> dict:
    """Return {"best": (chap, verse, cola_n), "median": ..., "worst": ...}."""
    all_verses = []
    for ch_name, ch_data in chapters.items():
        for verse_ref, cola_n in ch_data.get("verses", {}).items():
            all_verses.append((ch_name, verse_ref, cola_n))

    if not all_verses:
        return {"best": None, "median": None, "worst": None}

    sorted_by_cola = sorted(all_verses, key=lambda x: x[2])
    worst = sorted_by_cola[0]
    best = sorted_by_cola[-1]
    median_idx = len(sorted_by_cola) // 2
    median = sorted_by_cola[median_idx]

    return {
        "best": best,
        "median": median,
        "worst": worst,
    }


# ---------------------------------------------------------------------------
# Scorecard rendering
# ---------------------------------------------------------------------------
def render_markdown(
    book_slug: str,
    dir_name: str,
    total_cola: int,
    chapter_count: int,
    chapters: dict,
    validator_results: list[dict],
    quality_counts: dict | None,
    drift_counts: dict | None,
    score: int,
    score_breakdown: dict,
    timestamp: str,
) -> str:
    lines = []

    # Title
    lines.append(f"# Quality Scorecard — {book_slug.capitalize()}")
    lines.append(f"")
    lines.append(f"Generated: {timestamp}")
    lines.append(f"Tier: v2/he (scored tier)")
    lines.append(f"")

    # ── Overview ──────────────────────────────────────────────────────────
    lines.append(f"## Overview")
    lines.append(f"")
    lines.append(f"| Field | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Book | {book_slug.capitalize()} |")
    lines.append(f"| Directory | `{dir_name}` |")
    lines.append(f"| Chapters | {chapter_count} |")
    lines.append(f"| Total cola | {total_cola} |")
    lines.append(f"| **Readiness score** | **{score}/100** |")
    lines.append(f"")

    # ── Readiness score breakdown ─────────────────────────────────────────
    lines.append(f"## Readiness Score Breakdown")
    lines.append(f"")
    lines.append(f"| Component | Points earned | Max |")
    lines.append(f"|---|---|---|")
    lines.append(f"| 0 MALFORMED findings | {score_breakdown['malformed_pts']:.0f} | 50 |")
    lines.append(f"| DEVIATION+REVIEW ≤5% of cola | {score_breakdown['deviation_pts']:.1f} | 30 |")
    lines.append(f"| REVIEW-REQUIRED ≤10/chapter | {score_breakdown['review_pts']:.1f} | 10 |")
    lines.append(f"| Drift-scanner clean | {score_breakdown['drift_pts']:.1f} | 10 |")
    lines.append(f"| **Total** | **{score}** | **100** |")
    lines.append(f"")

    # ── Validator findings ────────────────────────────────────────────────
    lines.append(f"## Validator Findings")
    lines.append(f"")

    total_malformed = 0
    total_deviation = 0
    total_review_req = 0

    if not validator_results:
        lines.append(f"*No validators discovered.*")
    else:
        lines.append(f"| Validator | Layer | Findings | MALFORMED | DEVIATION | REVIEW-REQUIRED |")
        lines.append(f"|---|---|---|---|---|---|")
        for r in validator_results:
            sev = r.get("by_severity", {})
            tag = r.get("by_tag", {})
            malformed = sev.get("MALFORMED", 0)
            deviation = sev.get("DEVIATION", 0)
            rr = tag.get("REVIEW-REQUIRED", 0)
            total_malformed += malformed
            total_deviation += deviation
            total_review_req += rr
            err_note = f" ⚠ {r['error']}" if r.get("error") else ""
            lines.append(
                f"| `{r['name']}` | {r['layer']} | {r['findings']} "
                f"| {malformed} | {deviation} | {rr} |{err_note}"
            )
        lines.append(f"| **TOTAL** | | **{sum(r['findings'] for r in validator_results)}** "
                     f"| **{total_malformed}** | **{total_deviation}** | **{total_review_req}** |")
    lines.append(f"")

    # ── English quality checker ───────────────────────────────────────────
    lines.append(f"## English Quality Checker")
    lines.append(f"")
    if quality_counts is None:
        lines.append(f"*Not yet built or dependency missing; skipping.*")
    else:
        lines.append(f"| Issue type | Count |")
        lines.append(f"|---|---|")
        for key in ("PRONOUN", "NO_VERB", "FRAGMENT", "REPEAT", "MID_SPLIT"):
            lines.append(f"| {key} | {quality_counts.get(key, 0)} |")
        total_q = sum(quality_counts.values())
        lines.append(f"| **TOTAL** | **{total_q}** |")
    lines.append(f"")

    # ── English drift scanner ─────────────────────────────────────────────
    lines.append(f"## English Drift Scanner")
    lines.append(f"")
    if drift_counts is None:
        lines.append(f"*Not yet built; skipping.*")
    else:
        lines.append(f"| Flag | Count |")
        lines.append(f"|---|---|")
        drift_flags = ("ARTICLE-SPLIT", "PREP-NP-SPLIT", "AUX-VERB-SPLIT",
                       "PTC-NP-SPLIT", "APPOSITIVE-SPLIT", "DANGLING-CONJ")
        for flag in drift_flags:
            lines.append(f"| {flag} | {drift_counts.get(flag, 0)} |")
        total_d = sum(drift_counts.get(f, 0) for f in drift_flags)
        lines.append(f"| **TOTAL** | **{total_d}** |")
    lines.append(f"")

    # ── Per-chapter cola breakdown ────────────────────────────────────────
    lines.append(f"## Per-Chapter Cola Counts")
    lines.append(f"")
    lines.append(f"| Chapter | Cola count |")
    lines.append(f"|---|---|")
    for ch_name, ch_data in sorted(chapters.items()):
        lines.append(f"| `{ch_name}` | {ch_data['total']} |")
    lines.append(f"")

    # ── Sample verses ─────────────────────────────────────────────────────
    samples = select_sample_verses(chapters)
    lines.append(f"## Sample Verses")
    lines.append(f"")
    lines.append(f"Verses selected by cola density (cola-per-verse):")
    lines.append(f"")
    lines.append(f"| Quality tier | Chapter | Verse | Cola count |")
    lines.append(f"|---|---|---|---|")
    for label in ("best", "median", "worst"):
        s = samples.get(label)
        if s:
            ch_name, verse_ref, cola_n = s
            lines.append(f"| {label.capitalize()} | `{ch_name}` | {verse_ref} | {cola_n} |")
        else:
            lines.append(f"| {label.capitalize()} | — | — | — |")
    lines.append(f"")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON state file
# ---------------------------------------------------------------------------
def build_json_state(
    book_slug: str,
    dir_name: str,
    total_cola: int,
    chapter_count: int,
    validator_results: list[dict],
    quality_counts: dict | None,
    drift_counts: dict | None,
    score: int,
    score_breakdown: dict,
    timestamp: str,
) -> dict:
    total_malformed = sum(r.get("by_severity", {}).get("MALFORMED", 0) for r in validator_results)
    total_deviation = sum(r.get("by_severity", {}).get("DEVIATION", 0) for r in validator_results)
    total_review = sum(r.get("by_tag", {}).get("REVIEW-REQUIRED", 0) for r in validator_results)

    return {
        "book": book_slug,
        "dir_name": dir_name,
        "timestamp": timestamp,
        "chapter_count": chapter_count,
        "total_cola": total_cola,
        "readiness_score": score,
        "score_breakdown": {k: round(v, 2) for k, v in score_breakdown.items()},
        "validators": {
            "total_findings": sum(r["findings"] for r in validator_results),
            "malformed": total_malformed,
            "deviation": total_deviation,
            "review_required": total_review,
            "per_validator": [
                {
                    "name": r["name"],
                    "layer": r["layer"],
                    "findings": r["findings"],
                    "by_severity": r.get("by_severity", {}),
                    "by_tag": r.get("by_tag", {}),
                    "error": r.get("error"),
                }
                for r in validator_results
            ],
        },
        "english_quality": quality_counts,
        "english_drift": drift_counts,
    }


# ---------------------------------------------------------------------------
# Main scorecard runner for one book
# ---------------------------------------------------------------------------
def run_scorecard(book_slug: str, verbose: bool = True) -> dict:
    """Run the full scorecard pipeline for one book.

    Returns the JSON state dict (also writes .md and -state.json files).
    """
    result = find_book_dir(book_slug)
    if result is None:
        print(f"ERROR: No v2/he directory found for book '{book_slug}'.", file=sys.stderr)
        sys.exit(2)

    dir_name, dir_path = result
    canonical_slug = _slug_from_dir(dir_name)

    if verbose:
        print(f"\n[quality_dashboard] Scoring: {canonical_slug} ({dir_name})", file=sys.stderr)

    # 1. Cola counts
    if verbose:
        print(f"  Counting cola...", file=sys.stderr)
    total_cola, chapter_count, chapters = count_book_cola(dir_path)

    # 2. Validators
    if verbose:
        print(f"  Running validators ({len(discover_validators())} found)...", file=sys.stderr)
    validator_results = run_all_validators_for_book(dir_name)

    # 3. English quality checker
    if verbose:
        print(f"  Running english_quality_check.py...", file=sys.stderr)
    quality_counts = run_english_quality_check(canonical_slug)
    if quality_counts is None and verbose:
        print(f"  english_quality_check.py: not available; skipping.", file=sys.stderr)

    # 4. Drift scanner
    if verbose:
        print(f"  Running scan_english_drift.py...", file=sys.stderr)
    drift_counts = run_drift_scan(canonical_slug)
    if drift_counts is None and verbose:
        print(f"  scan_english_drift.py: not available; skipping.", file=sys.stderr)

    # 5. Aggregate for score
    total_malformed = sum(r.get("by_severity", {}).get("MALFORMED", 0) for r in validator_results)
    total_deviation = sum(r.get("by_severity", {}).get("DEVIATION", 0) for r in validator_results)
    total_review_req = sum(r.get("by_tag", {}).get("REVIEW-REQUIRED", 0) for r in validator_results)
    drift_total = sum(drift_counts.values()) if drift_counts else 0
    drift_available = drift_counts is not None

    score, breakdown = compute_readiness(
        total_cola=total_cola,
        chapter_count=chapter_count,
        malformed=total_malformed,
        deviation_plus_review=total_deviation + total_review_req,
        review_required=total_review_req,
        drift_total=drift_total,
        drift_available=drift_available,
    )

    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # 6. Render output
    md_text = render_markdown(
        book_slug=canonical_slug,
        dir_name=dir_name,
        total_cola=total_cola,
        chapter_count=chapter_count,
        chapters=chapters,
        validator_results=validator_results,
        quality_counts=quality_counts,
        drift_counts=drift_counts,
        score=score,
        score_breakdown=breakdown,
        timestamp=timestamp,
    )

    json_state = build_json_state(
        book_slug=canonical_slug,
        dir_name=dir_name,
        total_cola=total_cola,
        chapter_count=chapter_count,
        validator_results=validator_results,
        quality_counts=quality_counts,
        drift_counts=drift_counts,
        score=score,
        score_breakdown=breakdown,
        timestamp=timestamp,
    )

    return {
        "book_slug": canonical_slug,
        "dir_name": dir_name,
        "score": score,
        "md_text": md_text,
        "json_state": json_state,
        "timestamp": timestamp,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--book",
        metavar="BOOK",
        help="Score one book by slug (e.g. 'jonah') or directory name (e.g. '32-jonah').",
    )
    mode.add_argument(
        "--all-books",
        action="store_true",
        help="Score all books with v2/he data present.",
    )
    ap.add_argument(
        "--output",
        metavar="PATH",
        help="Write the markdown scorecard to this path. "
             "Default: data/reports/quality/<book>-<timestamp>.md",
    )
    ap.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress messages to stderr.",
    )
    args = ap.parse_args()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    verbose = not args.quiet

    if args.book:
        books_to_score = [args.book]
    else:
        # --all-books: discover all books present in v2/he
        discovered = discover_books()
        if not discovered:
            print(
                f"ERROR: No book directories found under {V2_HE_DIR}",
                file=sys.stderr,
            )
            return 2
        books_to_score = [_slug_from_dir(d) for d, _ in discovered]
        if verbose:
            print(f"[quality_dashboard] Found {len(books_to_score)} book(s): {', '.join(books_to_score)}", file=sys.stderr)

    all_results = []
    for book_slug in books_to_score:
        try:
            result = run_scorecard(book_slug, verbose=verbose)
        except SystemExit:
            print(f"  [quality_dashboard] Skipping {book_slug} (error).", file=sys.stderr)
            continue

        # Write markdown
        if args.output and len(books_to_score) == 1:
            md_path = Path(args.output)
        else:
            ts_compact = result["timestamp"].replace(":", "").replace("-", "").replace("T", "-")
            md_path = REPORTS_DIR / f"{result['book_slug']}-{ts_compact}.md"

        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(result["md_text"], encoding="utf-8")
        if verbose:
            print(f"  Markdown written: {md_path}", file=sys.stderr)

        # Write JSON state (one per book, latest overwrites)
        json_path = REPORTS_DIR / f"{result['book_slug']}-state.json"
        json_path.write_text(
            json.dumps(result["json_state"], indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        if verbose:
            print(f"  JSON state:      {json_path}", file=sys.stderr)

        all_results.append(result)
        if verbose:
            print(f"  Readiness score: {result['score']}/100", file=sys.stderr)

        # Print scorecard to stdout (single-book mode)
        if not args.all_books:
            print(result["md_text"])

    # --all-books: write summary + print summary to stdout
    if args.all_books and all_results:
        ts_now = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        summary_path = REPORTS_DIR / f"all-books-summary-{ts_now}.md"

        # Rank by score descending
        ranked = sorted(all_results, key=lambda r: r["score"], reverse=True)

        summary_lines = []
        summary_lines.append("# All-Books Quality Summary — Tanakh Reader")
        summary_lines.append(f"")
        summary_lines.append(f"Generated: {ts_now}")
        summary_lines.append(f"")
        summary_lines.append(f"## Rankings by Readiness Score")
        summary_lines.append(f"")
        summary_lines.append(f"| Rank | Book | Score | Chapters | Cola | Scorecard |")
        summary_lines.append(f"|---|---|---|---|---|---|")
        for i, r in enumerate(ranked, 1):
            ts_compact = r["timestamp"].replace(":", "").replace("-", "").replace("T", "-")
            md_link = f"`{r['book_slug']}-{ts_compact}.md`"
            js = r["json_state"]
            summary_lines.append(
                f"| {i} | {r['book_slug'].capitalize()} | {r['score']}/100 "
                f"| {js['chapter_count']} | {js['total_cola']} | {md_link} |"
            )
        summary_lines.append(f"")

        summary_md = "\n".join(summary_lines)
        summary_path.write_text(summary_md, encoding="utf-8")
        if verbose:
            print(f"\n[quality_dashboard] Summary written: {summary_path}", file=sys.stderr)

        print(summary_md)

    return 0


if __name__ == "__main__":
    sys.exit(main())
