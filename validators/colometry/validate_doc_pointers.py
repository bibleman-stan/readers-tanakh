#!/usr/bin/env python3
"""
Detect broken file-path / cross-reference pointers in canon, CLAUDE.md,
and handoffs.

Ported 2026-04-30 from `readers-bofm/validators/colometry/validate_doc_pointers.py`.
Adapted for tanakh's directory structure (v0/v1/v2 tier subfolders, v0/morph/
layer, no colab/, etc.) and tanakh-specific historical references.

Approach:
  1. For each .md file in scope, find file-path references using regex.
  2. Resolve each reference relative to the repo root, the source file's
     directory, AND a list of likely subdirs (validators/colometry/,
     data/text-files/, scripts/, etc.) -- since canon and handoffs frequently
     cite bare filenames whose home is a subdir.
  3. Flag references to files that don't exist anywhere checked.

Scope:
  - Canon (private/01-method/*.md)
  - CLAUDE.md
  - handoffs/*.md

Exit code: 0 if no broken pointers, 1 if any found.

Usage:
    py -3 validators/colometry/validate_doc_pointers.py
    py -3 validators/colometry/validate_doc_pointers.py --verbose
"""

import argparse
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

SCAN_PATHS = [
    REPO_ROOT / "private" / "01-method" / "colometry-canon.md",
    REPO_ROOT / "CLAUDE.md",
] + sorted((REPO_ROOT / "handoffs").glob("*.md"))


# Subdirs to try when resolving bare filenames. The canon and handoffs cite
# bare filenames (e.g. `validate_construct_chain.py`, `apply_specs.py`) whose
# home is one of several conventional locations.
SEARCH_SUBDIRS = [
    "",
    "validators",
    "validators/colometry",
    "validators/syntax",
    "validators/_shared",
    "validators/specs",
    "validators/hooks",
    "data",
    "data/text-files",
    "data/text-files/v0",
    "data/text-files/v0/prose",
    "data/text-files/v0/eng-baseline",
    "data/text-files/v0/translit-baseline",
    "data/text-files/v0/morph",
    "data/text-files/v1",
    "data/text-files/v1/he-baseline",
    "data/text-files/v1/eng-interlinear",
    "data/text-files/v1/eng-gloss",
    "data/text-files/v1/translit",
    "data/text-files/v2",
    "data/text-files/v2/he",
    "data/text-files/v2/eng-interlinear",
    "data/text-files/v2/eng-gloss",
    "data/text-files/v2/translit",
    "data/syntax-reference",
    "data/reports",
    "scripts",
    "scripts/archive",
    "books",
    "tests",
    ".claude",
    ".claude/hooks",
    "research/stepbible-tahot",
]


# Regex patterns for file-path references in markdown:
#   - `path/to/file.ext` (backtick-wrapped)
#   - [text](path/to/file.ext) (markdown links)
#   - bare `file.md` mentions in narrative prose
PATH_RE = re.compile(
    r"`((?:[\w./\\-]+/)*[\w.-]+\.(?:md|py|html|js|json|txt|sh|ipynb|tsv|yaml|yml))`"
    r"|"
    r"\]\(((?:[\w./\\-]+/)*[\w.-]+\.(?:md|py|html|js|json|txt|sh|ipynb|tsv|yaml|yml))(?:#[\w-]+)?\)"
    r"|"
    r"\b((?:[\w-]+/)+[\w.-]+\.(?:md|py|html|js|json|txt|sh|ipynb|tsv|yaml|yml))\b"
)


# Exact-match skip set
SKIP_PATHS = {
    # External sibling-project references (siloed publicly; only mentioned in private docs)
    "readers-gnt/handoffs/04-editorial-workflow.md",
    "readers-bofm/handoffs/14-operational-protocols.md",
    "readers-gnt/CLAUDE.md",
    "readers-bofm/CLAUDE.md",
    # Stan's vault paths
    "C:/vaults-nano/my_brain/00_Inbox/claude-brainstorming.md",
    # Synthetic / example paths in canon prose
    "example.md",
    "tmp/file.py",
    # Session-folder convention filenames (described in CLAUDE.md as a
    # pattern, not actual paths -- they live in gitignored session folders)
    "session-notes.md",
    "full-transcript.md",
    "dialogue-notes.md",
    "intra-session-log.md",
    "review-lists",
    # Historical handoff references that were retired in tier-collapse
    # (described as deleted/superseded in canon §8 Update Log and handoffs/00)
    "scripts/apply_v2.py",
    "scripts/apply_v3.py",
    "scripts/apply_v4.py",
    # Pre-cascade-engine references that may appear in older handoff prose
    "v4-editorial",  # collapsed into v2/he 2026-04-27
    "v3-he-colometry",
    "v2-he-syntax",
    # Generated / build artifacts that may not exist on a fresh clone
    "manifest.json",
    "data/reports/apply",
    # External STEPBible source files (in research/, gitignored)
    "TAHOT_Gen-Deu.txt",
    "TAHOT_Jos-Est.txt",
    "TAHOT_Job-Sng.txt",
    "TAHOT_Isa-Mal.txt",
}


# Prefix-match skips
SKIP_PREFIXES = (
    "C:/", "c:/", "/",
    "readers-",      # sibling projects (siloed)
    "archive/",
    "private/",      # gitignored session folders, sub-method docs
    "research/",     # gitignored vendored sources
    "books/",        # generated; may not be present on fresh clone
    "books\\",
    "github.com/",
    "https://", "http://",
    "tanakh-reader.com",
    # Per-cluster apply_*.py / scan_*.py *templates* mentioned in handoffs/14
    # E5 as discipline patterns (one-tool-per-class), not yet existing files.
    "scripts/scan_<",
    "scripts/apply_<",
    "scripts/your_tool",
)


# Memory files live external to the repo at
# C:\Users\bibleman\.claude\projects\...\memory\. Bare `feedback_*.md`
# references in canon/handoffs are correct as memory pointers.
MEMORY_FILE_RE = re.compile(r"^(?:feedback|user|project|reference)_[\w-]+\.md$")


def is_allowed_skip(path_str: str) -> bool:
    if path_str in SKIP_PATHS:
        return True
    if path_str.startswith(SKIP_PREFIXES):
        return True
    if MEMORY_FILE_RE.match(path_str):
        return True
    return False


def resolve(ref: str, source_file: Path) -> Path | None:
    """Try repo-root, source-dir, and SEARCH_SUBDIRS. Return existing path or None."""
    rel = ref.replace("\\", "/")
    # Source-file directory first (relative imports within a doc tree)
    candidate = source_file.parent / rel
    if candidate.exists():
        return candidate
    # Repo root + each candidate subdir
    for sub in SEARCH_SUBDIRS:
        candidate = REPO_ROOT / sub / rel if sub else REPO_ROOT / rel
        if candidate.exists():
            return candidate
    return None


def scan_file(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    broken = []
    for i, line in enumerate(lines, start=1):
        for m in PATH_RE.finditer(line):
            ref = m.group(1) or m.group(2) or m.group(3)
            if not ref:
                continue
            if is_allowed_skip(ref):
                continue
            if resolve(ref, path) is not None:
                continue
            broken.append({
                "file": path.relative_to(REPO_ROOT),
                "line": i,
                "ref": ref,
                "context": line.strip()[:120],
            })
    return broken


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--json", action="store_true",
                    help="Emit JSON output (for run_all.py compatibility)")
    ap.add_argument("--v2", action="store_true",
                    help="Accepted for run_all.py compatibility (validator scans docs, not corpus tier).")
    args = ap.parse_args()

    all_broken = []
    for path in SCAN_PATHS:
        all_broken.extend(scan_file(path))

    if args.json:
        import json
        out = {
            "validator": "validate_doc_pointers",
            "summary": {
                "files_scanned": len(SCAN_PATHS),
                "total_findings": len(all_broken),
            },
            "findings": [
                {
                    "file": str(b["file"]).replace("\\", "/"),
                    "line": b["line"],
                    "rule": "doc-pointer",
                    "subcase": "broken-path",
                    "severity": "MALFORMED",
                    "annotation": f"Broken path reference: {b['ref']}",
                    "context": b["context"],
                }
                for b in all_broken
            ],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if not all_broken else 1

    print("=" * 72)
    print("Doc-pointer integrity validator")
    print("=" * 72)
    print()
    print(f"Scanning {len(SCAN_PATHS)} files for file-path references...")
    print()

    if not all_broken:
        print(f"Files scanned: {len(SCAN_PATHS)}")
        print("Violations found: 0")
        print()
        print("All file-path references resolve to existing files.")
        return 0

    print(f"Files scanned: {len(SCAN_PATHS)}")
    print(f"Violations found: {len(all_broken)}")
    print()

    by_ref = {}
    for b in all_broken:
        by_ref.setdefault(b["ref"], []).append(b)

    if args.verbose:
        for b in all_broken:
            print(f"[DEVIATION]  {b['file']}:{b['line']} -> {b['ref']}")
            print(f"    {b['context']}")
            print()
    else:
        for ref, bs in by_ref.items():
            print(f"  {ref}: {len(bs)} reference{'s' if len(bs) != 1 else ''}")
            for b in bs[:3]:
                print(f"    {b['file']}:{b['line']}")
            if len(bs) > 3:
                print(f"    ... +{len(bs) - 3} more")
            print()

    print("Each violation is a file-path reference that doesn't resolve.")
    print("Either (a) update to the correct path, OR (b) add to SKIP_PATHS")
    print("if the reference is intentional (external / archive / example).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
