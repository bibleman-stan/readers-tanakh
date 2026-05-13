#!/usr/bin/env python3
"""
Detect carry-forward-inertia residue: active references to retired/
withdrawn/rescinded canon items in canon, CLAUDE.md, and handoffs/.

Ported 2026-04-30 from `readers-bofm/validators/colometry/validate_canon_retirement_residue.py`.
Adapted for tanakh's specific retirement history: tier collapse (5-tier →
v0/v1/v2), apply_v2/apply_v3 retirement, breath-criterion exclusion, and
the te'amim-as-evidence (not authority) reframing.

Approach:
  1. Hardcoded list of retired terms with their retirement markers.
  2. Scan canon + CLAUDE.md + handoffs/ for occurrences of each term.
  3. Filter out:
     - Lines within retirement notices (contain "retired"/"withdrawn"/etc.).
     - Lines in §8 Update Log entries (historical record).
     - Lines explicitly qualified ("withdrawn ...").
  4. Report remaining as RESIDUE candidates.

Maintenance: when adding a new retirement to the canon, add a corresponding
entry to RETIRED_TERMS below. The validator catches future residue without
relying on Claude's memory.

Exit code: 0 if zero residue; 1 if residue found.

Usage:
    py -3 validators/colometry/validate_canon_retirement_residue.py
    py -3 validators/colometry/validate_canon_retirement_residue.py --verbose
"""

import argparse
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

# Files to scan
SCAN_PATHS = [
    REPO_ROOT / "private" / "01-method" / "colometry-canon.md",
    REPO_ROOT / "CLAUDE.md",
] + sorted((REPO_ROOT / "handoffs").glob("*.md"))


# Retired/withdrawn/rescinded canon items.
# Each entry: (search-pattern, retirement-date, brief-note).
# Patterns are case-insensitive regex; should match the term as it would
# appear in active prose.
RETIRED_TERMS = [
    # === Tier-architecture retirements (2026-04-27 collapse) ===
    {
        "pattern": r"\bapply_v[234]\.py\b",
        "term": "apply_v2.py / apply_v3.py / apply_v4.py",
        "retired": "2026-04-27 (tier collapse — replaced by apply_specs.py + apply_validators.py)",
        "note": "Auto-apply tiers retired; spec_runner findings feed editorial work queue directly per canon §2 Mechanical-rule authority.",
    },
    {
        "pattern": r"\bv2-he-syntax\b",
        "term": "v2-he-syntax tier",
        "retired": "2026-04-27 (tier collapse)",
        "note": "Old 5-tier scheme had v2 = Layer 1 syntax pass; collapsed pipeline is now v0 → v1 → v2 (where v2/heb is the editorial gold standard).",
    },
    {
        "pattern": r"\bv3-he-colometry\b",
        "term": "v3-he-colometry tier",
        "retired": "2026-04-27 (tier collapse)",
        "note": "Old 5-tier scheme had v3 = Layer 3 colometry pass; collapsed pipeline is now v0 → v1 → v2.",
    },
    {
        "pattern": r"\bv4[-\s]?editorial\b",
        "term": "v4-editorial tier / directory",
        "retired": "2026-04-27 (tier collapse)",
        "note": "Editorial gold standard moved from v4/editorial/ to v2/heb/. Per-word layers moved from v4/ to v2/.",
    },
    {
        "pattern": r"\bfour[-\s]?tier\b|\bfive[-\s]?tier\b|\b5[-\s]?tier\b|\b4[-\s]?tier\b",
        "term": "four-tier / five-tier pipeline framing",
        "retired": "2026-04-27 (tier collapse)",
        "note": "Pipeline is now v0 → v1 → v2 (3 tiers). Earlier 4-tier (v0-v3) and 5-tier (v0-v4) framings are superseded.",
    },
    {
        "pattern": r"\btier[-\s]?diff\s+audit\s+gate\b",
        "term": "tier-diff audit gate",
        "retired": "2026-04-27 (tier collapse)",
        "note": "The tier-diff audit gate was for the auto-apply tiers (v2-he-syntax, v3-he-colometry); replaced by commit-time discipline (pre-commit + commit-msg gates).",
    },
    {
        "pattern": r"\bv1[-\s]?teamim\b",
        "term": "v1-teamim directory name",
        "retired": "2026-04-26 (renamed to v1-he-baseline)",
        "note": "Te'amim-as-evidence framing — v1 baseline is what the te'amim parser emits, not a normative te'amim-as-prior label.",
    },
    # === Methodology retirements ===
    {
        "pattern": r"\b(?:te['’]?amim|teamim)[-\s]+as[-\s]+(?:authority|prior)\b",
        "term": "te'amim-as-authority / te'amim-as-prior framing",
        "retired": "2026-04-26 (te'amim are evidence, not authority — see canon)",
        "note": "Te'amim are the editor's starting draft + most important single piece of evidence, but not deterministic. Atomic thought is the criterion; te'amim inform but don't license breaks.",
    },
    {
        "pattern": r"\bbreath[-\s]+(?:criterion|test|unit|units|tests|criteria)\b",
        "term": "breath criterion / breath test / breath unit",
        "retired": "Excluded from criteria per CLAUDE.md (te'amim already encode Masoretic phrasing; breath is not an additional criterion)",
        "note": "Three criteria are atomic thought, single image, Hebrew syntax. Breath is NOT a fourth criterion — both sibling projects' empirical retirement (2026) confirmed zero cases where breath was the sole deciding factor.",
    },
    {
        "pattern": r"\bproject\s+siloing\s+dropped\b",
        "term": "project siloing dropped (claim)",
        "retired": "Stale memory entry — project siloing IS still in force per CLAUDE.md",
        "note": "CLAUDE.md still has the Project Siloing section. The 2026-04-27 memory entry that claimed siloing was dropped is stale.",
    },
    # === Wave 6 Macula structural-gloss pipeline retirements (2026-05-12) ===
    {
        "pattern": r"\bgenerate_english_glosses\.py\b",
        "term": "generate_english_glosses.py (1208-line Macula structural-gloss generator)",
        "retired": "2026-05-12 (Wave 6 — replaced by scripts/regenerate_english.py thin-wrapper around atu_method.kjv_alignment)",
        "note": "v2/eng-gloss substrate pivoted from Macula structural English to KJV verbatim per Hebrew ATU cola via Strong's matching. See commit aece7a310.",
    },
    {
        "pattern": r"\bnormalize_english_gloss\.py\b",
        "term": "normalize_english_gloss.py (1906-line post-processor)",
        "retired": "2026-05-12 (Wave 6 — consumer gone; KJV verbatim is deterministic, no normalize step needed)",
        "note": "Post-processor for naturalize regex output; obsolete with KJV verbatim substrate.",
    },
    {
        "pattern": r"\bmine_phrase_map\.py\b",
        "term": "mine_phrase_map.py (674-line phrase-map miner)",
        "retired": "2026-05-12 (Wave 6 — phrase-map abandoned)",
        "note": "Macula-anchored phrase-map approach retired with the structural-gloss substrate.",
    },
    {
        "pattern": r"\bscan_eng_gloss_readability\.py\b",
        "term": "scan_eng_gloss_readability.py (268-line readability QA scanner)",
        "retired": "2026-05-12 (Wave 6 — KJV verbatim is deterministic; readability scan unnecessary)",
        "note": "QA scanner for the now-retired naturalized-English output.",
    },
    {
        "pattern": r"\bKJV_MODE\b|\?source=kjv\b",
        "term": "KJV_MODE / ?source=kjv URL gating",
        "retired": "2026-05-12 (Wave 6 — Modern pill always visible; swap always active)",
        "note": "Pre-Wave-6 the KJV-anchored English was URL-gated for staged rollout; post-promotion it's the only path.",
    },
    {
        "pattern": r"\bbooks-kjv/",
        "term": "books-kjv/ parallel HTML tree",
        "retired": "2026-05-12 (Wave 6 — single books/ tree; KJV is default substrate)",
        "note": "Parallel HTML tree for staged KJV rollout; collapsed post-promotion.",
    },
    {
        "pattern": r"\beng-gloss-kjv\b",
        "term": "v2/eng-gloss-kjv/ parallel directory",
        "retired": "2026-05-12 (Wave 6 — v2/eng-gloss is now the KJV substrate)",
        "note": "Parallel directory for staged KJV rollout; promoted into the canonical eng-gloss slot.",
    },
    # Add new entries here when retiring/withdrawing/rescinding canon items.
]


# Markers indicating a line is RETIREMENT CONTEXT (mention of the retired
# term in a discussion of the retirement itself — these are legitimate, not
# residue).
RETIREMENT_MARKERS_RE = re.compile(
    r"\b(retired|retire|retires|withdrawn|withdraw|rescinded|rescind|"
    r"RETRACT(?:ED)?|REJECT(?:ED)?|deprecated|deleted|superseded|supersede|"
    r"collapsed|retirement|carve-out|excluded|stale|"
    r"RETIRED|WITHDRAWN|RESCINDED|SUPERSEDED|DEPRECATED)\b",
    re.IGNORECASE,
)

# §8 Update Log entries are historical record — references to retired
# terms there are legitimate. Match Update Log section markers.
UPDATE_LOG_MARKERS_RE = re.compile(
    r"^(?:## (?:8|10)\.\s+Update Log|### \d{4}-\d{2}-\d{2}|See `archive/|Prior history|"
    r"\*\*\d{4}-\d{2}-\d{2} update)",
    re.IGNORECASE,
)


def is_retirement_context_line(line: str) -> bool:
    """Line is retirement-context if it contains a retirement marker."""
    return bool(RETIREMENT_MARKERS_RE.search(line))


def find_update_log_ranges(lines: list[str]) -> list[tuple[int, int]]:
    """Return (start_line, end_line) ranges for §8 Update Log sections.
    These are historical record; references inside them are legitimate."""
    ranges = []
    in_log = False
    log_start = 0
    for i, line in enumerate(lines):
        if re.match(r"^## (?:8|10)\.\s+Update Log", line):
            in_log = True
            log_start = i
        elif in_log and re.match(r"^## \d+\.\s+", line):
            # New §N. section; log ends here
            ranges.append((log_start, i - 1))
            in_log = False
    if in_log:
        ranges.append((log_start, len(lines) - 1))
    return ranges


def scan_file(path: Path) -> list[dict]:
    """Find residue references in path."""
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    log_ranges = find_update_log_ranges(lines)

    def in_log(i):
        return any(start <= i <= end for start, end in log_ranges)

    residue = []
    for entry in RETIRED_TERMS:
        pat = re.compile(entry["pattern"], re.IGNORECASE)
        for i, line in enumerate(lines):
            if not pat.search(line):
                continue
            if is_retirement_context_line(line):
                continue
            if in_log(i):
                continue
            residue.append({
                "file": path.relative_to(REPO_ROOT),
                "line": i + 1,
                "term": entry["term"],
                "retired": entry["retired"],
                "text": line.rstrip(),
            })
    return residue


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--json", action="store_true",
                    help="Emit JSON output (for run_all.py compatibility)")
    ap.add_argument("--v2", action="store_true",
                    help="Accepted for run_all.py compatibility (validator scans docs, not corpus tier).")
    args = ap.parse_args()

    all_residue = []
    for path in SCAN_PATHS:
        all_residue.extend(scan_file(path))

    if args.json:
        import json
        out = {
            "validator": "validate_canon_retirement_residue",
            "summary": {
                "files_scanned": len(SCAN_PATHS),
                "total_findings": len(all_residue),
            },
            "findings": [
                {
                    "file": str(r["file"]).replace("\\", "/"),
                    "line": r["line"],
                    "rule": "retirement-residue",
                    "subcase": r["term"],
                    "severity": "MALFORMED",
                    "annotation": f"Active reference to retired term: {r['term']}",
                    "context": r["text"][:200],
                }
                for r in all_residue
            ],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if not all_residue else 1

    print("=" * 72)
    print("Canon-retirement residue validator")
    print("=" * 72)
    print()
    print(f"Scanning {len(SCAN_PATHS)} files for active references to "
          f"{len(RETIRED_TERMS)} retired terms...")
    print()

    if not all_residue:
        print("Files scanned: " + str(len(SCAN_PATHS)))
        print("Violations found: 0")
        print()
        print("No residue. All retired terms are confined to retirement notices "
              "and §8 Update Log entries.")
        return 0

    print(f"Files scanned: {len(SCAN_PATHS)}")
    print(f"Violations found: {len(all_residue)}")
    print()

    if args.verbose:
        for r in all_residue:
            print(f"[DEVIATION]  {r['file']}:{r['line']} [{r['term']}]")
            print(f"    {r['text'][:120]}")
            print(f"    Retired: {r['retired']}")
            print()
    else:
        # Group by term
        by_term = {}
        for r in all_residue:
            by_term.setdefault(r["term"], []).append(r)
        for term, rs in by_term.items():
            print(f"  {term}: {len(rs)} residue reference{'s' if len(rs) != 1 else ''}")
            for r in rs[:3]:
                print(f"    {r['file']}:{r['line']}")
            if len(rs) > 3:
                print(f"    ... +{len(rs) - 3} more")
            print()
        print("Re-run with --verbose for full context.")

    print("Each violation is an active reference to a term that was retired/")
    print("withdrawn/rescinded in canon. Either:")
    print("  (a) Update the line to reflect the retirement (preferred), OR")
    print("  (b) Mark the line as retirement-context if it discusses the")
    print("      retirement itself (not as if the term were active).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
