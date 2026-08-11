#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_constraints.py — Stage 2 of the ATU pipeline. Runs the Hebrew
Constraint Catalog v1 against a Stage-1 proposal per directive 2026-05-17-1500
Item 2.

Architecture revisions per §7.3 pre-build audit β:
  - 3-way verdict taxonomy: CONFLICT / CORROBORATE / ADVISORY (no auto-override)
  - Macula operationalization pre-flight: for each constraint, verify Macula
    primitives are available; mark NOT-YET-IMPLEMENTED if not; report
    "running N of 26 constraints; M not yet operationalized"
  - HARD/ADVISORY tier informs report formatting only; never auto-corrects
  - audit_rendered_output.py is a prompt-formatter, NOT a constraint-checker
    (audit β Finding 7) — this script reuses 5-machinery/validators/_shared/macula_constituents
    for Macula queries, NOT audit_rendered_output.py

Input: per-chapter JSONL from render_atus.py at
       data/reports/atu_pipeline/<book>/chapter-NN.jsonl

Output: per-chapter constraint-violation report at
        data/reports/atu_pipeline/<book>/chapter-NN-audit.jsonl
        with one record per (verse, constraint-id) firing.

Usage:
    PYTHONIOENCODING=utf-8 py -3 5-machinery/scripts/atu_pipeline/audit_constraints.py \\
        --book 19-psalms --chapter 1 [--coverage-only]
"""

from __future__ import annotations

import argparse
import inspect
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable

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
CATALOG_MASTER = REPO_ROOT / "1-method/canon" / "constraint_catalog_v1.md"
CONSTRAINTS_DIR = REPO_ROOT / "1-method/canon" / "constraints"
REPORT_DIR = REPO_ROOT / "data" / "reports" / "atu_pipeline"

# Add 5-machinery/validators/ to sys.path for shared Macula primitive imports.
sys.path.insert(0, str(REPO_ROOT / "5-machinery/validators"))
# Add 5-machinery/scripts/atu_pipeline/ to sys.path so the checks_*.py cluster modules can be imported.
sys.path.insert(0, str(Path(__file__).resolve().parent))

HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")


def strip_points(token: str) -> str:
    """Remove niqqud + te'amim. Used for surface-form lemma checks."""
    return HEBREW_POINTS_RE.sub("", token)


@dataclass
class ConstraintEntry:
    """One catalog constraint."""
    constraint_id: str  # e.g., "JM158-restrictive-relative"
    title: str
    encoded_question: str  # yes/no
    verdict_family: str  # BIND / SPLIT / MERGE / VIOLATION-FLAG / NO-EFFECT / JUDGMENT-REQUIRED / INFORM
    tier: str  # HARD / ADVISORY
    precedence: int  # 1-9
    source: str  # Joüon §X.Y or other
    macula_op: str  # primitive query or "Macula: none — surface heuristic required"
    status: str  # DRAFT / VALIDATED / DEPRECATED
    backward_compat: Optional[str] = None  # G-label from 1100 if any


def parse_catalog_master(path: Path) -> list[ConstraintEntry]:
    """Parse the master catalog markdown into ConstraintEntry objects.

    Actual format (per 1-method/canon/constraint_catalog_v1.md):
      ### {id}

      **{title}**

      - **Encoded question**: ...
      - **Verdict family**: ...
      - **Tier**: ...
      - **Precedence**: ...
      - **Source**: ...
      - **Macula operationalization**: ...
      - **Status**: ...
      - **Backward-compat**: ...
    """
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    entries: list[ConstraintEntry] = []
    # Match `### <id>` where id starts with JM or similar uppercase prefix.
    # The id contains letters, digits, hyphens. Body is everything until the
    # next `### ` or `---` section break.
    # Use a regex that captures the id line and the body up to the next ### or
    # a horizontal rule `---` on its own line.
    pattern = re.compile(
        r"^### (JM[A-Za-z0-9-]+(?:-[a-z0-9-]+)?)\s*$"  # id header
        r"\n+(?:\*\*([^*]+?)\*\*\s*\n+)?"  # optional bold title
        r"(.+?)"  # body
        r"(?=^### JM[A-Za-z0-9-]|^## |\Z)",  # next entry, next H2, or EOF
        re.MULTILINE | re.DOTALL,
    )

    for match in pattern.finditer(text):
        cid = match.group(1).strip()
        title = (match.group(2) or "").strip()
        body = match.group(3)

        def field_value(label: str) -> str:
            m = re.search(
                rf"-\s*\*\*{re.escape(label)}\*\*:\s*(.+?)(?=\n-\s*\*\*|\Z|\n---)",
                body,
                flags=re.DOTALL,
            )
            return m.group(1).strip() if m else ""

        precedence_str = field_value("Precedence")
        prec_match = re.search(r"\d+", precedence_str)
        precedence = int(prec_match.group()) if prec_match else 9

        entries.append(ConstraintEntry(
            constraint_id=cid,
            title=title,
            encoded_question=field_value("Encoded question"),
            verdict_family=field_value("Verdict family") or "JUDGMENT-REQUIRED",
            tier=("HARD" if "HARD" in field_value("Tier").upper() else "ADVISORY"),
            precedence=precedence,
            source=field_value("Source"),
            macula_op=field_value("Macula operationalization"),
            status=field_value("Status") or "DRAFT",
            backward_compat=field_value("Backward-compat") or None,
        ))
    return entries


# ---------------------------------------------------------------------------
# Constraint check registry: id → callable(verse_text, source_text) → verdict
# ---------------------------------------------------------------------------
# Per Audit β Finding 4: only constraints with verified operationalization
# run. Each check returns one of:
#   {"fires": bool, "verdict": "CONFLICT|CORROBORATE|ADVISORY",
#    "reason": str, "details": dict}
# or None if NOT-YET-IMPLEMENTED.

ConstraintCheck = Callable[[str, str], Optional[dict]]
CHECK_REGISTRY: dict[str, ConstraintCheck] = {}


def register_check(constraint_id: str):
    """Decorator to register a Constraint check."""
    def wrap(func: ConstraintCheck) -> ConstraintCheck:
        CHECK_REGISTRY[constraint_id] = func
        return func
    return wrap


# ---------------------------------------------------------------------------
# Concrete checks (surface-form for v1; Macula upgrades documented inline)
# ---------------------------------------------------------------------------


@register_check("JM13-maqqef-group")
def check_maqqef_indivisible(verse_text: str, source_text: str) -> Optional[dict]:
    """Maqqef-group indivisibility: a maqqef-bound prosodic word must not span
    a line break. If two adjacent lines have a maqqef glyph at the boundary
    (last char of line N is ־, OR first char of line N+1 is ־), VIOLATION.

    Macula upgrade (deferred): consult lowfat morphology for maqqef-bound
    constituent membership; current check is surface-glyph-based."""
    lines = [ln for ln in verse_text.splitlines() if ln.strip()]
    for i in range(len(lines) - 1):
        if lines[i].rstrip().endswith("־") or lines[i + 1].lstrip().startswith("־"):
            return {
                "fires": True,
                "verdict": "CONFLICT",
                "reason": "maqqef glyph at line boundary — maqqef-bound prosodic word split",
                "details": {"break_after_line": i + 1},
            }
    return {"fires": False, "verdict": "NO-EFFECT", "reason": "no boundary maqqef detected"}


@register_check("JM103-proclitic-stranding")
def check_proclitic_stranded(verse_text: str, source_text: str) -> Optional[dict]:
    """Proclitic line-final stranding: a line must not end with a bare
    proclitic prefix (ל / ב / כ / מ as a standalone token without its host)."""
    lines = [ln for ln in verse_text.splitlines() if ln.strip()]
    proclitic_tokens = frozenset({"ל", "ב", "כ", "מ", "וְ", "ו"})
    for i, ln in enumerate(lines):
        last_token_match = re.search(r"\S+\s*$", ln.rstrip("׃"))
        if last_token_match:
            last_token_stripped = strip_points(last_token_match.group().strip())
            if last_token_stripped in proclitic_tokens:
                return {
                    "fires": True,
                    "verdict": "CONFLICT",
                    "reason": f"line {i+1} ends with bare proclitic '{last_token_stripped}'",
                    "details": {"line": i + 1, "proclitic": last_token_stripped},
                }
    return {"fires": False, "verdict": "NO-EFFECT", "reason": "no stranded proclitic"}


@register_check("JM103e-compound-prep-object")
def check_compound_prep_object(verse_text: str, source_text: str) -> Optional[dict]:
    """Compound prepositions (לפני / אחרי / מאת / מתחת) cannot strand from
    their object across a line break."""
    lines = [ln for ln in verse_text.splitlines() if ln.strip()]
    compound_preps = frozenset({"לפני", "אחרי", "מאת", "מתחת", "מעל", "מעם", "לפי"})
    for i in range(len(lines) - 1):
        # Check if the line ENDS with a bare compound preposition
        last_token_match = re.search(r"\S+\s*$", lines[i].rstrip("׃"))
        if last_token_match:
            last_stripped = strip_points(last_token_match.group().strip())
            if last_stripped in compound_preps:
                return {
                    "fires": True,
                    "verdict": "CONFLICT",
                    "reason": f"line {i+1} ends with bare compound prep '{last_stripped}'",
                    "details": {"line": i + 1, "prep": last_stripped},
                }
    return {"fires": False, "verdict": "NO-EFFECT", "reason": "no compound-prep stranding"}


# JM158-restrictive-relative removed from this file 2026-05-17 per §7.3 audit β
# MUST-FIX #3: registered twice (here + in checks_relative_subordinate module),
# producing silent-overwrite collision. The Macula-aware version in
# checks_relative_subordinate.py supersedes this surface heuristic.


# Phantom ID stubs removed 2026-05-17 per §7.3 audit α MUST-FIX #9 + audit β MUST-FIX #2:
#   - "JM150-verbless-clause" — not a catalog ID; real ID is JM154-verbless-clause-nucleus
#   - "JM155-construct-chain" — not a catalog ID; real ID is JM129-construct-chain
# Real implementations land via the cluster-module register_with() calls below.


# ---------------------------------------------------------------------------
# Cluster module registration (wires the 22 Macula-aware checks into CHECK_REGISTRY)
# ---------------------------------------------------------------------------
#
# Per §7.3 audit β MUST-FIX #1 and the design-fix residual-risks audit:
# audit_verse now dispatches by arity, so 5-arg cluster functions can register
# directly. The shim wrappers in checks_*.py modules that pass empty/None
# coordinates are bypassed where possible (the audit_verse arity dispatch will
# invoke the registered callable correctly regardless of whether it's the
# wrapped 2-arg shim or the underlying 5-arg function).


_CLUSTER_MODULES: list[str] = [
    "checks_bound_nominals",
    "checks_clause_nucleus",
    "checks_particles",
    "checks_bonded_formula",
    "checks_relative_subordinate",
]


def _register_cluster_checks() -> None:
    """Import each cluster module and merge its CHECKS_5ARG into CHECK_REGISTRY.

    Single source of truth per module: each cluster file exposes
    CHECKS_5ARG: dict[str, Callable] mapping catalog-id → 5-arg check function,
    and register_with(registry, strict=True) that merges + detects collisions.

    All failures are FATAL — silent skip is the failure mode this refactor
    closes (coding-audit MF-1, 2026-05-17). A module that fails to import,
    lacks CHECKS_5ARG, or registers zero checks is a hard error.
    """
    for mod_name in _CLUSTER_MODULES:
        mod = __import__(mod_name)
        if not hasattr(mod, "CHECKS_5ARG"):
            raise RuntimeError(
                f"{mod_name} missing required CHECKS_5ARG dict — "
                f"all cluster modules must expose this canonical registry"
            )
        if not hasattr(mod, "register_with"):
            raise RuntimeError(
                f"{mod_name} missing required register_with(registry) — "
                f"all cluster modules must expose this function"
            )
        registered = mod.register_with(CHECK_REGISTRY)
        if not registered:
            raise RuntimeError(
                f"{mod_name}.register_with() registered 0 checks — "
                f"CHECKS_5ARG empty or registration silently failed"
            )


# Wire the cluster checks at module import time. coverage_preflight() called
# below will now see all 26 catalog entries either registered or honestly NYI.
_register_cluster_checks()


# ---------------------------------------------------------------------------
# Coverage pre-flight
# ---------------------------------------------------------------------------


def coverage_preflight(entries: list[ConstraintEntry]) -> dict:
    """For each catalog entry, report whether a check is registered."""
    active: list[str] = []
    not_implemented: list[str] = []
    for e in entries:
        if e.constraint_id in CHECK_REGISTRY:
            active.append(e.constraint_id)
        else:
            not_implemented.append(e.constraint_id)
    return {
        "total": len(entries),
        "active": len(active),
        "not_implemented": len(not_implemented),
        "active_ids": active,
        "not_implemented_ids": not_implemented,
    }


# ---------------------------------------------------------------------------
# Audit runner
# ---------------------------------------------------------------------------


# Arity-cached dispatch: inspect each check once, cache its parameter count.
# Replaces the prior try/except TypeError dual-dispatch which silently swallowed
# bugs inside 5-arg checks per §7.3 audit β finding.
_ARITY_CACHE: dict[Callable, int] = {}


def _check_arity(check: Callable) -> int:
    """Return the number of positional parameters the check accepts (cached)."""
    cached = _ARITY_CACHE.get(check)
    if cached is not None:
        return cached
    try:
        sig = inspect.signature(check)
        n = sum(
            1 for p in sig.parameters.values()
            if p.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        )
    except (ValueError, TypeError):
        # Builtins or C-implemented callables — assume 5-arg max.
        n = 5
    _ARITY_CACHE[check] = n
    return n


def audit_verse(
    verse_text: str,
    source_text: str,
    entries: list[ConstraintEntry],
    book_slug: str = "",
    chapter: int = 0,
    verse_num: int = 0,
) -> list[dict]:
    """Run all registered checks against one verse. Return per-firing records.

    `book_slug`, `chapter`, `verse_num` are threaded to checks that need Macula
    coordinates. Dispatch by parameter count (cached): 2-arg checks get
    (verse_text, source_text); 5+-arg checks get the full tuple.
    """
    firings: list[dict] = []
    # Sort by precedence (lowest int = highest priority)
    for entry in sorted(entries, key=lambda e: e.precedence):
        check = CHECK_REGISTRY.get(entry.constraint_id)
        if check is None:
            continue
        arity = _check_arity(check)
        if arity >= 5:
            result = check(verse_text, source_text, book_slug, chapter, verse_num)
        else:
            result = check(verse_text, source_text)
        if result is None:
            continue
        if not result.get("fires"):
            continue
        firings.append({
            "constraint_id": entry.constraint_id,
            "title": entry.title,
            "tier": entry.tier,
            "precedence": entry.precedence,
            "verdict": result["verdict"],
            "reason": result["reason"],
            "details": result.get("details", {}),
        })
    return firings


def _parse_verse_num(verse_ref: str) -> int:
    """Parse 'chapter:verse' format into verse_num. Returns 0 on parse failure."""
    if not verse_ref or ":" not in verse_ref:
        return 0
    parts = verse_ref.split(":")
    if len(parts) < 2:
        return 0
    try:
        return int(parts[-1])
    except ValueError:
        return 0


def audit_chapter(
    book_slug: str,
    chapter: int,
    entries: list[ConstraintEntry],
) -> tuple[Path, list[dict]]:
    """Read Stage-1 JSONL and audit each verse's draft rendering."""
    stage1_path = REPORT_DIR / book_slug / f"chapter-{chapter:02d}.jsonl"
    if not stage1_path.is_file():
        raise FileNotFoundError(
            f"Stage-1 output not found: {stage1_path}. Run render_atus.py first."
        )

    audit_records: list[dict] = []
    for raw in stage1_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        rec = json.loads(raw)
        verse_text = rec.get("draft", "") or ""
        source_text = rec.get("source", "") or ""
        verse_num = _parse_verse_num(rec.get("verse", ""))
        firings = audit_verse(
            verse_text, source_text, entries,
            book_slug=book_slug, chapter=chapter, verse_num=verse_num,
        )
        audit_records.append({
            "verse": rec["verse"],
            "agreement": rec.get("agreement"),
            "firings": firings,
        })

    out_path = REPORT_DIR / book_slug / f"chapter-{chapter:02d}-audit.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in audit_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return out_path, audit_records


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--book", required=True, help="book slug (e.g., 19-psalms)")
    p.add_argument("--chapter", type=int, required=False)
    p.add_argument("--coverage-only", action="store_true",
                   help="Print pre-flight coverage report; do not run audit")
    args = p.parse_args()

    entries = parse_catalog_master(CATALOG_MASTER)
    print(f"Loaded {len(entries)} constraint entries from {CATALOG_MASTER.relative_to(REPO_ROOT)}",
          file=sys.stderr)

    coverage = coverage_preflight(entries)
    print(f"\nCoverage pre-flight:", file=sys.stderr)
    print(f"  Total in catalog:   {coverage['total']}", file=sys.stderr)
    print(f"  Active (check reg): {coverage['active']}", file=sys.stderr)
    print(f"  Not-yet-impl:       {coverage['not_implemented']}", file=sys.stderr)
    print(f"\nActive constraint IDs:", file=sys.stderr)
    for cid in coverage["active_ids"]:
        print(f"  ✓ {cid}", file=sys.stderr)
    if coverage["not_implemented_ids"][:10]:
        print(f"\nNot-yet-implemented (first 10):", file=sys.stderr)
        for cid in coverage["not_implemented_ids"][:10]:
            print(f"  ○ {cid}", file=sys.stderr)
        if len(coverage["not_implemented_ids"]) > 10:
            print(f"  ... and {len(coverage['not_implemented_ids']) - 10} more",
                  file=sys.stderr)

    if args.coverage_only:
        return 0
    if args.chapter is None:
        print("ERROR: --chapter required unless --coverage-only", file=sys.stderr)
        return 2

    out_path, records = audit_chapter(args.book, args.chapter, entries)
    total_firings = sum(len(r["firings"]) for r in records)
    by_verdict: dict[str, int] = {}
    for r in records:
        for f in r["firings"]:
            by_verdict[f["verdict"]] = by_verdict.get(f["verdict"], 0) + 1
    print(f"\nAudit complete → {out_path.relative_to(REPO_ROOT)}", file=sys.stderr)
    print(f"  Verses audited: {len(records)}", file=sys.stderr)
    print(f"  Total firings:  {total_firings}", file=sys.stderr)
    for verdict, n in sorted(by_verdict.items()):
        print(f"    {verdict:12s} {n}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
