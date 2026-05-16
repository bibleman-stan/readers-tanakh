#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Structural canon-validator alignment check (Tanakh).

Per atu-method/docs/canon-validator-alignment-protocol.md (codified 2026-05-16):
verifies that what canon §5 entries NAME actually EXISTS in the validator code.
Mechanical / structural only — does NOT verify semantic alignment (whether
predicate logic implements what canon prose claims).

Four checks per §5 H-rule entry:
  1. Validator file presence — named detector path resolves to an actual file.
  2. Closed-list presence — every closed-list named in the rule's YAML or
     prose appears as a Python constant (uppercase identifier) in the named
     validator source.
  3. UD signature field consistency — Tanakh-flavor: confirm `detectors:`
     and `closed_lists:` keys present in the YAML block (the field-shape
     check that maps onto the universal template's UD-signature/Closed-lists
     fields per per-corpus-vocabulary conformance).
  4. Multi-valued field branches — N/A for current Tanakh §5 (no multi-valued
     branch syntax in use; placeholder for future).

Verdict taxonomy:
  ALIGNED         — all checks pass
  NO_IMPL         — canon names a validator file that doesn't exist
  DRIFT           — validator file exists; named closed-lists or fields missing
  PARTIAL         — some named items present, others missing
  EDITORIAL_ACK   — canon explicitly declares no auto-applier / dormant lexicon

Structural precedent: validators/colometry/validate_canon_retirement_residue.py
(scans canon prose, applies pattern matching, reports drift candidates).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CANON = REPO_ROOT / "private" / "01-method" / "colometry-canon.md"

# §5 active-rule section header pattern. Excludes "### Rule HN — RETIRED ..."
# entries (covered separately by validate_canon_retirement_residue.py) and the
# parenthetical "(RETIRED H19 placeholder)" wrapper.
RULE_HEADER_RE = re.compile(r"^### Rule (H\d+[a-z]?) — (?!RETIRED)(.+)$")
RETIRED_HEADER_RE = re.compile(r"^### Rule (H\d+) — RETIRED")
PLACEHOLDER_HEADER_RE = re.compile(r"^### \(RETIRED H\d+ placeholder")

# YAML field patterns inside the spec block.
#   list-item form:    "  - validators/foo/bar.py"
#   inline-prose form: "detectors: sub-check inside validators/foo/bar.py"
# Both must be detectable so that the script doesn't false-positive on entries
# whose YAML footers use prose rather than a bullet list (e.g., H5b, H15).
INLINE_PATH_RE = re.compile(r"(validators/[\w/]+\.py)")
CLOSED_LIST_RE = re.compile(r"^\s*-\s*([A-Z][A-Z0-9_]+)")  # Uppercase identifier.

# Editorial-ack markers in entry prose. The explicit YAML key
#   `applier: (none — editorial-judgment rule)`
# is the strongest signal; the longer-prose phrases catch entries pre-dating
# the explicit notation.
EDITORIAL_ACK_MARKERS = (
    "applier: (none",
    "no validator",
    "no direct validator",
    "no auto-applier",
    "editorial-judgment rule",
    "corpus-evidence rule",
    "deliberately dormant",
    "currently dormant",
    "reference-only",
)

# Cross-validator constants frequently live in validators/_shared/*.py rather
# than in a specific detector file. The closed-list check scans this directory
# as a fallback so that, e.g., DISCOURSE_PARTICLES in _shared/morphology.py
# is recognized when H14's detector validate_bare_discourse_particle.py
# imports it.
SHARED_DIR = Path(__file__).resolve().parents[2] / "validators" / "_shared"


def parse_canon_entries(text: str) -> list[dict]:
    """Split the canon by ### Rule HN — ... headers. Return a list of dicts
    with keys: rule_id, title, body (raw text between this header and the
    next ### or ## boundary)."""
    lines = text.splitlines()
    entries = []
    cur = None
    in_section_5 = False
    for ln in lines:
        if ln.startswith("## §5"):
            in_section_5 = True
            continue
        if in_section_5 and ln.startswith("## ") and not ln.startswith("## §5"):
            # Reached the next top-level section (§6); flush + exit.
            if cur is not None:
                entries.append(cur)
                cur = None
            in_section_5 = False
            continue
        if not in_section_5:
            continue
        m = RULE_HEADER_RE.match(ln)
        if m:
            if cur is not None:
                entries.append(cur)
            cur = {"rule_id": m.group(1), "title": m.group(2).strip(), "body": []}
            continue
        if RETIRED_HEADER_RE.match(ln) or PLACEHOLDER_HEADER_RE.match(ln):
            if cur is not None:
                entries.append(cur)
                cur = None
            continue
        if cur is not None:
            cur["body"].append(ln)
    if cur is not None:
        entries.append(cur)
    return entries


def extract_yaml_fields(body_lines: list[str]) -> dict:
    """Find the ```yaml ... ``` block(s) in the entry body and pull out
    detectors paths + closed-list names. Returns a dict with keys
    'detectors' (list[str]) and 'closed_lists' (list[str]).

    Detector paths are matched in two forms:
      (a) list-item form — '  - validators/foo/bar.py'
      (b) inline-prose form — 'detectors: sub-check inside validators/foo/bar.py'
    Both share INLINE_PATH_RE; the section-tracker keeps the prose match
    scoped to the detectors: block."""
    detectors, closed_lists = [], []
    in_yaml = False
    section = None
    for ln in body_lines:
        s = ln.rstrip()
        if s.startswith("```yaml"):
            in_yaml = True
            section = None
            continue
        if in_yaml and s.startswith("```"):
            in_yaml = False
            section = None
            continue
        if not in_yaml:
            continue
        if s.startswith("detectors:"):
            section = "detectors"
            detectors.extend(INLINE_PATH_RE.findall(s))
            continue
        if s.startswith("closed_lists:"):
            section = "closed_lists"
            continue
        if s and not s.startswith(" "):
            # New top-level YAML key — leave the section
            section = None
        if section == "detectors":
            detectors.extend(INLINE_PATH_RE.findall(s))
        elif section == "closed_lists":
            m = CLOSED_LIST_RE.match(s)
            if m:
                closed_lists.append(m.group(1))
    # Deduplicate while preserving order
    seen = set()
    detectors = [d for d in detectors if not (d in seen or seen.add(d))]
    return {"detectors": detectors, "closed_lists": closed_lists}


def has_editorial_ack(body_lines: list[str]) -> str | None:
    """Return the matched marker if the entry contains editorial-ack
    language ("no validator", "dormant", "reference-only", etc.), else None."""
    body_text = " ".join(body_lines).lower()
    for marker in EDITORIAL_ACK_MARKERS:
        if marker in body_text:
            return marker
    return None


def check_validator_file(detector_path: str) -> bool:
    return (REPO_ROOT / detector_path).is_file()


def check_closed_list_in_source(detector_path: str, list_name: str) -> bool:
    """Grep the validator source AND validators/_shared/*.py for the closed-list
    constant name. Detector source is checked first; if not found, the shared
    module tree is scanned because many cross-validator constants
    (DISCOURSE_PARTICLES, SIFREI_EMET_BOOKS_FULL, EMBEDDED_POETRY, etc.) live
    in validators/_shared/ rather than in any single detector file.

    Match is prefix-tolerant: `\\bNAME` (word-start boundary, no trailing
    boundary) so that a canon name like SIFREI_EMET_BOOKS matches a source
    variant SIFREI_EMET_BOOKS_FULL. This handles the FULL/PARTIAL/CHAPTERS
    suffix variation pattern observed in poetic_register.py."""
    paths: list[Path] = []
    detector_full = REPO_ROOT / detector_path
    if detector_full.is_file():
        paths.append(detector_full)
    if SHARED_DIR.is_dir():
        paths.extend(sorted(SHARED_DIR.glob("*.py")))
    pattern = rf"\b{re.escape(list_name)}"  # prefix-tolerant
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        if re.search(pattern, text):
            return True
    return False


def classify(entry: dict) -> tuple[str, list[str]]:
    """Return (verdict, evidence_lines)."""
    yaml = extract_yaml_fields(entry["body"])
    detectors = yaml["detectors"]
    closed_lists = yaml["closed_lists"]
    ack_marker = has_editorial_ack(entry["body"])

    evidence: list[str] = []

    # EDITORIAL_ACK path: entry explicitly declares no validator / dormant
    if not detectors and ack_marker:
        evidence.append(f"editorial-ack marker: '{ack_marker}'")
        return "EDITORIAL_ACK", evidence

    if not detectors:
        evidence.append("no detectors named in YAML block")
        return "NO_IMPL", evidence

    # File-presence check
    missing_files = [d for d in detectors if not check_validator_file(d)]
    if missing_files:
        for m in missing_files:
            evidence.append(f"detector named but file missing: {m}")
        # If ALL detectors are missing → NO_IMPL; if SOME → PARTIAL
        if len(missing_files) == len(detectors):
            return "NO_IMPL", evidence
        # else: at least one detector present; treat as PARTIAL with closed-list
        # check on the present detectors only
        detectors = [d for d in detectors if d not in missing_files]

    # Closed-list-presence check on present detectors
    missing_lists: list[str] = []
    for cl in closed_lists:
        if not any(check_closed_list_in_source(d, cl) for d in detectors):
            missing_lists.append(cl)
    if missing_lists:
        for cl in missing_lists:
            evidence.append(f"closed-list '{cl}' named in canon, not found in detector source")

    if missing_files:
        return "PARTIAL", evidence
    if missing_lists:
        return "DRIFT", evidence
    if not evidence:
        evidence.append(
            f"{len(detectors)} detector(s) present; "
            f"{len(closed_lists)} closed-list(s) verified"
        )
    return "ALIGNED", evidence


VERDICT_ORDER = ["NO_IMPL", "DRIFT", "PARTIAL", "EDITORIAL_ACK", "ALIGNED"]


def main():
    text = CANON.read_text(encoding="utf-8")
    entries = parse_canon_entries(text)
    results = []
    for e in entries:
        verdict, evidence = classify(e)
        results.append({**e, "verdict": verdict, "evidence": evidence})

    print(f"Canon-validator alignment check — Tanakh §5\n")
    print(f"Canon path: {CANON.relative_to(REPO_ROOT)}")
    print(f"Active §5 entries: {len(results)}\n")

    # Sort by verdict severity (NO_IMPL first, ALIGNED last)
    results.sort(key=lambda r: VERDICT_ORDER.index(r["verdict"]))

    for r in results:
        label = f"{r['rule_id']} ({r['title']}): {r['verdict']}"
        print(label)
        for ev in r["evidence"]:
            print(f"  - {ev}")
        print()

    # Summary
    from collections import Counter
    counts = Counter(r["verdict"] for r in results)
    print("--- Summary ---")
    for v in VERDICT_ORDER:
        if counts.get(v):
            print(f"  {v}: {counts[v]}")
    # Exit-code semantics: 0 if all ALIGNED or EDITORIAL_ACK; 1 if any drift.
    drift_count = sum(counts.get(v, 0) for v in ("NO_IMPL", "DRIFT", "PARTIAL"))
    sys.exit(0 if drift_count == 0 else 1)


if __name__ == "__main__":
    main()
