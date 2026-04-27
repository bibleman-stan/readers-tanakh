#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
refresh_book.py — Thin chain wrapper that runs the per-book pipeline end-to-end.

For the given book (or all books with --all-books), runs sequentially:
1. scripts/apply_validators.py --book <book>  (skipped if missing; non-zero exit aborts chain)
2. scripts/propagate_editorial_layers.py --book <book>
3. scripts/generate_english_glosses.py --book <book>
4. (optional) scripts/build_books.py --book <book_short>  (if --build flag passed)

Each subprocess invocation includes PYTHONIOENCODING=utf-8 env var.

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/refresh_book.py --book 32-jonah
    PYTHONIOENCODING=utf-8 py -3 scripts/refresh_book.py --book 32-jonah --build
    PYTHONIOENCODING=utf-8 py -3 scripts/refresh_book.py --all-books --build
    PYTHONIOENCODING=utf-8 py -3 scripts/refresh_book.py --book 32-jonah --dry-run
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
TEXT_DIR = REPO_ROOT / "data" / "text-files"
V1_HE_DIR = TEXT_DIR / "v1" / "he-baseline"

# Env var for Python Unicode on Windows.
ENV = os.environ.copy()
ENV["PYTHONIOENCODING"] = "utf-8"


def discover_books():
    """Discover all books in v1/he-baseline."""
    if not V1_HE_DIR.exists():
        print(f"Error: {V1_HE_DIR} does not exist", file=sys.stderr)
        sys.exit(1)

    books = []
    for item in sorted(V1_HE_DIR.iterdir()):
        if item.is_dir():
            books.append(item.name)

    return books


def book_short_name(book_folder):
    """Extract short name from book folder (e.g. '05-jonah' → 'jonah')."""
    # Format is NN-name; extract the name part.
    if '-' in book_folder:
        return book_folder.split('-', 1)[1]
    return book_folder


def run_step(script_name, book, dry_run, skip_missing=False):
    """
    Run a single step in the pipeline.

    Args:
        script_name: Name of script (e.g. 'apply_validators.py')
        book: Book folder name (e.g. '05-jonah')
        dry_run: If True, print command instead of running it
        skip_missing: If True, don't error if script is missing (for apply_validators)

    Returns:
        True if step succeeded, False if it failed (or was skipped as missing).
    """
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        if skip_missing:
            print(f"  ⊘ {script_name} not found (skipped)")
            return True
        else:
            print(f"  ✗ {script_name} not found", file=sys.stderr)
            return False

    cmd = [
        sys.executable,
        str(script_path),
        "--book", book
    ]

    if dry_run:
        print(f"  [DRY-RUN] {' '.join(cmd)}")
        return True

    print(f"  Running {script_name}...")
    try:
        result = subprocess.run(cmd, env=ENV, check=False)
        if result.returncode != 0:
            # apply_validators returns 1 on findings (non-fatal).
            if script_name == "apply_validators.py" and result.returncode == 1:
                print(f"  ✓ {script_name} completed (findings present, non-fatal)")
                return True
            else:
                print(f"  ✗ {script_name} failed with exit code {result.returncode}", file=sys.stderr)
                return False
        print(f"  ✓ {script_name} completed")
        return True
    except Exception as e:
        print(f"  ✗ {script_name} error: {e}", file=sys.stderr)
        return False


def run_build_step(book, dry_run):
    """
    Run build_books.py with the short book name.

    Args:
        book: Book folder name (e.g. '05-jonah')
        dry_run: If True, print command instead of running it

    Returns:
        True if step succeeded, False if it failed.
    """
    script_path = SCRIPTS_DIR / "build_books.py"
    short_name = book_short_name(book)

    if not script_path.exists():
        print(f"  ✗ build_books.py not found", file=sys.stderr)
        return False

    cmd = [
        sys.executable,
        str(script_path),
        "--book", short_name
    ]

    if dry_run:
        print(f"  [DRY-RUN] {' '.join(cmd)}")
        return True

    print(f"  Running build_books.py...")
    try:
        result = subprocess.run(cmd, env=ENV, check=False)
        if result.returncode != 0:
            print(f"  ✗ build_books.py failed with exit code {result.returncode}", file=sys.stderr)
            return False
        print(f"  ✓ build_books.py completed")
        return True
    except Exception as e:
        print(f"  ✗ build_books.py error: {e}", file=sys.stderr)
        return False


def process_book(book, build=False, dry_run=False):
    """
    Process a single book through the pipeline.

    Returns:
        (success, elapsed_seconds)
    """
    start_time = time.time()
    print(f"\n{book}")

    steps = [
        ("apply_validators.py", True),   # (script_name, skip_missing)
        ("propagate_editorial_layers.py", False),
        ("generate_english_glosses.py", False),
    ]

    for script_name, skip_missing in steps:
        if not run_step(script_name, book, dry_run, skip_missing=skip_missing):
            elapsed = time.time() - start_time
            return (False, elapsed)

    if build:
        if not run_build_step(book, dry_run):
            elapsed = time.time() - start_time
            return (False, elapsed)

    elapsed = time.time() - start_time
    return (True, elapsed)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    book_group = ap.add_mutually_exclusive_group(required=True)
    book_group.add_argument("--book", help="Book folder name, e.g. '32-jonah'")
    book_group.add_argument("--all-books", action="store_true", help="Process all books in v1/he-baseline/")

    ap.add_argument("--build", action="store_true", help="Also rebuild HTML with build_books.py")
    ap.add_argument("--dry-run", action="store_true", help="Do not actually invoke steps; print what would run")

    args = ap.parse_args()

    if args.all_books:
        books = discover_books()
        if not books:
            print("No books found", file=sys.stderr)
            sys.exit(1)
    else:
        books = [args.book]

    print(f"Refresh book pipeline ({len(books)} book(s))")
    print(f"Build HTML: {args.build}")
    print(f"Dry-run: {args.dry_run}")

    total_start = time.time()
    total_success = 0
    total_failed = 0
    failed_books = []
    elapsed_times = []

    for book in books:
        success, elapsed = process_book(book, build=args.build, dry_run=args.dry_run)
        elapsed_times.append(elapsed)

        if success:
            total_success += 1
            status = "✓"
        else:
            total_failed += 1
            failed_books.append(book)
            status = "✗"

        print(f"{status} {book} ({elapsed:.1f}s)")

    total_elapsed = time.time() - total_start

    # Summary
    print(f"\n{'='*60}")
    print(f"Summary: {total_success} succeeded, {total_failed} failed")
    print(f"Total time: {total_elapsed:.1f}s ({sum(elapsed_times):.1f}s step time)")

    if failed_books:
        print(f"Failed books:")
        for book in failed_books:
            print(f"  - {book}")
        sys.exit(1)
    else:
        if not args.dry_run:
            print("All books processed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
