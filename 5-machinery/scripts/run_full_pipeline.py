#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_full_pipeline.py — Full-corpus pipeline orchestrator for the Tanakh Reader.

Runs the complete ingest → parse → validate → propagate → gloss → (build) chain
for every book in BOOK_REGISTRY (imported from ingest_tahot.py).

Steps per book:
  1. ingest_tahot.py    --book <book_key>
     Skip: data/text-files/v0/prose/<out_subdir>/ already exists
  2. parse_teamim.py    --book <book_key>
     Skip: data/text-files/v1/he-baseline/<out_subdir>/ already exists
  3. apply_validators.py --book <out_subdir>
     Skip with warning if script does not exist yet
  4. propagate_editorial_layers.py --book <out_subdir>
     Skip if data/text-files/v2/heb/<out_subdir>/ does not exist
  5. regenerate_english.py --book <book_key> --force  (KJV-verbatim via MetaV)
  6. build_books.py --book <book_key>  (only with --build flag)

Per-book result: success / partial / failure, with per-step status.

Final output: summary table printed to stdout + report file at
  data/reports/pipeline-run-<timestamp>.md

CLI:
  --all-books         Run all books (default when no --book/--start-from)
  --book <key>        Run a single book by BOOK_REGISTRY key (e.g. 'jonah')
  --start-from <key>  Resume from this book in BOOK_REGISTRY order
  --build             Also run build_books.py (HTML rebuild)
  --dry-run           Print what would run; no subprocess invocations

Usage:
  PYTHONIOENCODING=utf-8 py -3 5-machinery/scripts/run_full_pipeline.py --all-books
  PYTHONIOENCODING=utf-8 py -3 5-machinery/scripts/run_full_pipeline.py --book jonah
  PYTHONIOENCODING=utf-8 py -3 5-machinery/scripts/run_full_pipeline.py --start-from ruth
  PYTHONIOENCODING=utf-8 py -3 5-machinery/scripts/run_full_pipeline.py --all-books --build
  PYTHONIOENCODING=utf-8 py -3 5-machinery/scripts/run_full_pipeline.py --all-books --dry-run
"""

import argparse
import datetime
import os
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Repo layout
# ---------------------------------------------------------------------------

SCRIPT_DIR  = Path(__file__).resolve().parent
REPO_ROOT   = SCRIPT_DIR.parent
TEXT_DIR    = REPO_ROOT / "data" / "text-files"
REPORTS_DIR = REPO_ROOT / "data" / "reports"

V0_PROSE_DIR  = TEXT_DIR / "v0" / "prose"
V1_HE_DIR     = TEXT_DIR / "v1" / "he-baseline"
V2_HEB_DIR     = TEXT_DIR  / "v2" / "heb"
V4_ED_DIR     = TEXT_DIR / "v4" / "editorial"

# ---------------------------------------------------------------------------
# Import BOOK_REGISTRY from ingest_tahot — single source of truth.
# ---------------------------------------------------------------------------

sys.path.insert(0, str(SCRIPT_DIR))
try:
    from ingest_tahot import BOOK_REGISTRY as _INGEST_REGISTRY
except ImportError as exc:
    sys.exit(f"ERROR: cannot import BOOK_REGISTRY from ingest_tahot.py: {exc}")

# BOOK_REGISTRY: ordered dict of book_key → spec.
# Preserve insertion order (Python 3.7+) = BHS canonical order.
BOOK_REGISTRY: dict = _INGEST_REGISTRY

# ---------------------------------------------------------------------------
# Environment — PYTHONIOENCODING=utf-8 mandatory on Windows for Hebrew Unicode.
# ---------------------------------------------------------------------------

ENV = os.environ.copy()
ENV["PYTHONIOENCODING"] = "utf-8"

# ---------------------------------------------------------------------------
# Step status sentinels
# ---------------------------------------------------------------------------

OK       = "OK"
SKIP     = "SKIP"
WARN     = "WARN"   # skipped with a warning (e.g. missing script)
FAIL     = "FAIL"
NA       = "N/A"    # step cannot apply (e.g. no v2/heb/ → propagate is irrelevant)

# ---------------------------------------------------------------------------
# Subprocess helpers
# ---------------------------------------------------------------------------


def _run(cmd: list[str], dry_run: bool) -> tuple[int, str, str]:
    """Invoke cmd with the project env. Returns (returncode, stdout, stderr)."""
    if dry_run:
        return 0, f"[DRY-RUN] {' '.join(str(c) for c in cmd)}", ""
    try:
        result = subprocess.run(
            cmd,
            env=ENV,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as exc:
        return -1, "", str(exc)


def _script(name: str) -> Path:
    return SCRIPT_DIR / name


def _script_exists(name: str) -> bool:
    return _script(name).is_file()


# ---------------------------------------------------------------------------
# Step runners
# ---------------------------------------------------------------------------


def run_ingest(book_key: str, spec: dict, dry_run: bool) -> tuple[str, str]:
    """Step 1 — ingest_tahot.py.

    Returns (status, detail_message).
    Skip if v0/prose/<out_subdir>/ already exists and has at least one .txt file.
    """
    out_dir = V0_PROSE_DIR / spec["out_subdir"]
    if out_dir.is_dir() and any(out_dir.glob("*.txt")):
        return SKIP, f"v0/prose/{spec['out_subdir']}/ exists"

    if not _script_exists("ingest_tahot.py"):
        return FAIL, "ingest_tahot.py not found"

    cmd = [sys.executable, str(_script("ingest_tahot.py")), "--book", book_key]
    rc, out, err = _run(cmd, dry_run)
    if dry_run:
        return SKIP, out
    if rc == 0:
        return OK, out.strip().splitlines()[-1] if out.strip() else "done"
    return FAIL, (err or out).strip()[:200]


def run_parse(book_key: str, spec: dict, dry_run: bool) -> tuple[str, str]:
    """Step 2 — parse_teamim.py.

    Skip if v1/he-baseline/<out_subdir>/ already exists and has at least one .txt file.
    """
    out_dir = V1_HE_DIR / spec["out_subdir"]
    if out_dir.is_dir() and any(out_dir.glob("*.txt")):
        return SKIP, f"v1/he-baseline/{spec['out_subdir']}/ exists"

    if not _script_exists("parse_teamim.py"):
        return FAIL, "parse_teamim.py not found"

    # Prerequisite: v0 must exist (ingest may have just run, or was already done).
    v0_dir = V0_PROSE_DIR / spec["out_subdir"]
    if not (v0_dir.is_dir() and any(v0_dir.glob("*.txt"))):
        return FAIL, f"v0/prose/{spec['out_subdir']}/ missing — ingest must succeed first"

    cmd = [sys.executable, str(_script("parse_teamim.py")), "--book", book_key]
    rc, out, err = _run(cmd, dry_run)
    if dry_run:
        return SKIP, out
    if rc == 0:
        return OK, out.strip().splitlines()[-1] if out.strip() else "done"
    return FAIL, (err or out).strip()[:200]


def run_apply_validators(spec: dict, dry_run: bool) -> tuple[str, str]:
    """Step 3 — apply_validators.py --book <out_subdir>.

    Skip with WARN if the script does not exist yet (planned but not yet written).
    """
    script = "apply_validators.py"
    if not _script_exists(script):
        return WARN, f"{script} not yet implemented — skipped"

    cmd = [sys.executable, str(_script(script)), "--book", spec["out_subdir"]]
    rc, out, err = _run(cmd, dry_run)
    if dry_run:
        return SKIP, out
    if rc in (0, 1):
        # rc=1 means findings present, which is non-fatal (same convention as refresh_book.py)
        return OK, out.strip().splitlines()[-1] if out.strip() else "done"
    return FAIL, (err or out).strip()[:200]


def run_propagate(spec: dict, dry_run: bool) -> tuple[str, str]:
    """Step 4 — propagate_editorial_layers.py --book <out_subdir>.

    Skip (N/A) if v2/heb/<out_subdir>/ does not exist — nothing to propagate.
    """
    v2_dir = V2_HEB_DIR / spec["out_subdir"]
    if not (v2_dir.is_dir() and any(v2_dir.glob("*.txt"))):
        return NA, f"v2/heb/{spec['out_subdir']}/ missing — nothing to propagate"

    if not _script_exists("propagate_editorial_layers.py"):
        return FAIL, "propagate_editorial_layers.py not found"

    cmd = [sys.executable, str(_script("propagate_editorial_layers.py")), "--book", spec["out_subdir"]]
    rc, out, err = _run(cmd, dry_run)
    if dry_run:
        return SKIP, out
    if rc == 0:
        return OK, out.strip().splitlines()[-1] if out.strip() else "done"
    return FAIL, (err or out).strip()[:200]


def run_gloss(book_key: str, dry_run: bool) -> tuple[str, str]:
    """Step 5 — regenerate_english.py --book <book_key> --force.

    Wave 6-OT change: the Macula-Hebrew structural-gloss generator
    (generate_english_glosses.py) was retired. regenerate_english.py is
    the canonical KJV-verbatim English-layer generator (thin wrapper over
    atu_method.kjv_alignment + MetaV). It takes the short book key
    (e.g. 'genesis'), not the folder form ('01-genesis').
    """
    if not _script_exists("regenerate_english.py"):
        return FAIL, "regenerate_english.py not found"

    cmd = [sys.executable, str(_script("regenerate_english.py")), "--book", book_key, "--force"]
    rc, out, err = _run(cmd, dry_run)
    if dry_run:
        return SKIP, out
    if rc == 0:
        return OK, out.strip().splitlines()[-1] if out.strip() else "done"
    return FAIL, (err or out).strip()[:200]


def run_build(book_key: str, dry_run: bool) -> tuple[str, str]:
    """Step 6 (optional) — build_books.py --book <book_key>."""
    if not _script_exists("build_books.py"):
        return FAIL, "build_books.py not found"

    cmd = [sys.executable, str(_script("build_books.py")), "--book", book_key]
    rc, out, err = _run(cmd, dry_run)
    if dry_run:
        return SKIP, out
    if rc == 0:
        return OK, out.strip().splitlines()[-1] if out.strip() else "done"
    return FAIL, (err or out).strip()[:200]


# ---------------------------------------------------------------------------
# REVIEW-Q counter
# ---------------------------------------------------------------------------


def count_review_queue(spec: dict) -> int:
    """Count REVIEW-REQUIRED cola lines in v4/editorial/<out_subdir>/.

    Falls back to counting cola lines in v2/heb/<out_subdir>/ when v4 does not
    exist (since the full v4 editorial pass may not yet have happened).

    A "REVIEW-REQUIRED" count is the total number of Hebrew cola lines across
    all chapter files in the best available editorial tier: v4 preferred, then
    v2, then v1. Returns -1 if none of the tiers have data.
    """
    for tier_dir in (V4_ED_DIR, V2_HEB_DIR, V1_HE_DIR):
        book_dir = tier_dir / spec["out_subdir"]
        if not book_dir.is_dir():
            continue
        txt_files = sorted(book_dir.glob("*.txt"))
        if not txt_files:
            continue
        total = 0
        import re as _re
        verse_ref_re = _re.compile(r"^\d+:\d+$")
        for p in txt_files:
            try:
                for raw in p.read_text(encoding="utf-8").splitlines():
                    line = raw.strip()
                    if line and not verse_ref_re.match(line):
                        total += 1
            except Exception:
                pass
        return total
    return -1


# ---------------------------------------------------------------------------
# Per-book orchestrator
# ---------------------------------------------------------------------------


class BookResult:
    __slots__ = (
        "book_key", "spec",
        "ingest", "parse", "apply", "propag", "gloss", "build",
        "review_q",
        "ingest_detail", "parse_detail", "apply_detail",
        "propag_detail", "gloss_detail", "build_detail",
        "elapsed",
    )

    def __init__(self, book_key: str, spec: dict):
        self.book_key    = book_key
        self.spec        = spec
        self.ingest      = NA
        self.parse       = NA
        self.apply       = NA
        self.propag      = NA
        self.gloss       = NA
        self.build       = NA
        self.review_q    = -1
        self.ingest_detail  = ""
        self.parse_detail   = ""
        self.apply_detail   = ""
        self.propag_detail  = ""
        self.gloss_detail   = ""
        self.build_detail   = ""
        self.elapsed     = 0.0

    @property
    def overall(self) -> str:
        """success / partial / failure based on step statuses."""
        critical = [self.ingest, self.parse, self.gloss]
        if FAIL in critical:
            return "failure"
        steps_with_data = [s for s in (self.ingest, self.parse, self.apply, self.propag, self.gloss, self.build) if s != NA]
        if FAIL in steps_with_data:
            return "partial"
        return "success"


def process_book(book_key: str, spec: dict, build: bool, dry_run: bool) -> BookResult:
    t0 = time.time()
    r = BookResult(book_key, spec)
    print(f"\n  [{book_key}]")

    # Step 1: ingest
    r.ingest, r.ingest_detail = run_ingest(book_key, spec, dry_run)
    _print_step("ingest", r.ingest, r.ingest_detail)
    if r.ingest == FAIL:
        r.elapsed = time.time() - t0
        return r

    # Step 2: parse
    r.parse, r.parse_detail = run_parse(book_key, spec, dry_run)
    _print_step("parse ", r.parse, r.parse_detail)
    if r.parse == FAIL:
        r.elapsed = time.time() - t0
        return r

    # Step 3: apply_validators (warn-only on script-absent)
    r.apply, r.apply_detail = run_apply_validators(spec, dry_run)
    _print_step("apply ", r.apply, r.apply_detail)
    # WARN does not abort the chain

    # Step 4: propagate (N/A is fine; FAIL does not abort)
    r.propag, r.propag_detail = run_propagate(spec, dry_run)
    _print_step("propag", r.propag, r.propag_detail)

    # Step 5: gloss (Wave 6-OT: KJV-verbatim via regenerate_english.py;
    # takes the short book_key, not the folder-form spec["out_subdir"])
    r.gloss, r.gloss_detail = run_gloss(book_key, dry_run)
    _print_step("gloss ", r.gloss, r.gloss_detail)

    # Step 6: build (optional)
    if build:
        r.build, r.build_detail = run_build(book_key, dry_run)
        _print_step("build ", r.build, r.build_detail)

    # REVIEW-Q count
    r.review_q = count_review_queue(spec)

    r.elapsed = time.time() - t0
    return r


def _print_step(label: str, status: str, detail: str) -> None:
    icon = {"OK": "OK  ", "SKIP": "SKIP", "WARN": "WARN", "FAIL": "FAIL", "N/A": "N/A "}.get(status, status)
    truncated = (detail[:100] + "…") if len(detail) > 100 else detail
    print(f"    {icon}  {label}: {truncated}")


# ---------------------------------------------------------------------------
# Summary table + report
# ---------------------------------------------------------------------------

_COL_W = 18  # book name column width


def _status_cell(s: str) -> str:
    """Return a fixed-width cell string."""
    return s.ljust(6)


def _review_q_cell(n: int) -> str:
    return str(n) if n >= 0 else "-"


def format_summary_table(results: list[BookResult], build: bool) -> str:
    header_parts = [
        "BOOK".ljust(_COL_W),
        "INGEST", "PARSE ", "APPLY ", "PROPAG", "GLOSS ",
    ]
    if build:
        header_parts.append("BUILD ")
    header_parts.append("REVIEW-Q")
    header = "  ".join(header_parts)
    sep = "-" * len(header)

    lines = [header, sep]
    for r in results:
        row_parts = [
            r.spec["out_subdir"].ljust(_COL_W),
            _status_cell(r.ingest),
            _status_cell(r.parse),
            _status_cell(r.apply),
            _status_cell(r.propag),
            _status_cell(r.gloss),
        ]
        if build:
            row_parts.append(_status_cell(r.build))
        row_parts.append(_review_q_cell(r.review_q))
        lines.append("  ".join(row_parts))

    return "\n".join(lines)


def format_report_md(
    results: list[BookResult],
    build: bool,
    started_at: datetime.datetime,
    elapsed_total: float,
) -> str:
    ts = started_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        f"# Pipeline Run Report",
        f"",
        f"**Started:** {ts}  ",
        f"**Total elapsed:** {elapsed_total:.1f}s  ",
        f"**Books processed:** {len(results)}",
        f"",
        "## Summary Table",
        "",
        "```",
        format_summary_table(results, build),
        "```",
        "",
        "## Per-Book Detail",
        "",
    ]

    for r in results:
        lines.append(f"### {r.spec['out_subdir']}  ({r.book_key})  — {r.overall}  [{r.elapsed:.1f}s]")
        lines.append("")
        steps = [
            ("ingest",  r.ingest,  r.ingest_detail),
            ("parse",   r.parse,   r.parse_detail),
            ("apply",   r.apply,   r.apply_detail),
            ("propag",  r.propag,  r.propag_detail),
            ("gloss",   r.gloss,   r.gloss_detail),
        ]
        if build:
            steps.append(("build", r.build, r.build_detail))
        for name, status, detail in steps:
            lines.append(f"- **{name}**: {status}  — {detail}")
        lines.append(f"- **review-q**: {_review_q_cell(r.review_q)}")
        lines.append("")

    return "\n".join(lines)


def write_report(content: str, started_at: datetime.datetime) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = started_at.strftime("%Y%m%d-%H%M%S")
    path = REPORTS_DIR / f"pipeline-run-{ts}.md"
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Book list resolution
# ---------------------------------------------------------------------------


def resolve_books(args) -> list[tuple[str, dict]]:
    """Return ordered list of (book_key, spec) to process."""
    all_books = list(BOOK_REGISTRY.items())  # insertion order = BHS order

    if args.book:
        key = args.book
        if key not in BOOK_REGISTRY:
            sys.exit(f"ERROR: {key!r} not in BOOK_REGISTRY. Known keys: {', '.join(BOOK_REGISTRY)}")
        return [(key, BOOK_REGISTRY[key])]

    if args.start_from:
        key = args.start_from
        if key not in BOOK_REGISTRY:
            sys.exit(f"ERROR: {key!r} not in BOOK_REGISTRY. Known keys: {', '.join(BOOK_REGISTRY)}")
        keys_in_order = list(BOOK_REGISTRY.keys())
        idx = keys_in_order.index(key)
        return all_books[idx:]

    # default: --all-books
    return all_books


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    book_group = ap.add_mutually_exclusive_group()
    book_group.add_argument(
        "--book", metavar="BOOK_KEY",
        help="Run a single book by BOOK_REGISTRY key (e.g. 'jonah')"
    )
    book_group.add_argument(
        "--all-books", action="store_true", default=False,
        help="Run all books in BOOK_REGISTRY order (default)"
    )
    book_group.add_argument(
        "--start-from", metavar="BOOK_KEY",
        help="Run from this book to end of BOOK_REGISTRY (resume support)"
    )

    ap.add_argument(
        "--build", action="store_true", default=False,
        help="Also run build_books.py to regenerate HTML fragments"
    )
    ap.add_argument(
        "--dry-run", action="store_true", default=False,
        help="Show what would run; no subprocess invocations"
    )

    args = ap.parse_args()

    # Default: --all-books when no scope flag given
    if not args.book and not args.start_from:
        args.all_books = True

    books = resolve_books(args)

    started_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    print(f"run_full_pipeline.py — {started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Books: {len(books)}  |  build-HTML: {args.build}  |  dry-run: {args.dry_run}")
    print()

    t_total_start = time.time()
    results: list[BookResult] = []

    for book_key, spec in books:
        result = process_book(book_key, spec, args.build, args.dry_run)
        results.append(result)

    elapsed_total = time.time() - t_total_start

    # Print summary table
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(format_summary_table(results, args.build))
    print()

    # Count outcomes
    n_success = sum(1 for r in results if r.overall == "success")
    n_partial  = sum(1 for r in results if r.overall == "partial")
    n_failure  = sum(1 for r in results if r.overall == "failure")
    print(f"Results: {n_success} success, {n_partial} partial, {n_failure} failure")
    print(f"Total elapsed: {elapsed_total:.1f}s")

    # Write report
    if not args.dry_run:
        report_content = format_report_md(results, args.build, started_at, elapsed_total)
        report_path = write_report(report_content, started_at)
        print(f"\nReport: {report_path}")

    # Exit code: 0 if all success or partial; 1 if any failure
    if n_failure > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
