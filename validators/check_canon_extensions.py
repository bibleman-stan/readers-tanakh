#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_canon_extensions.py — content-aware canon-diff gate for commit-msg hook.

Detects canon extensions (canon §7-style triggers) in staged colometry-canon
diffs and blocks commits that introduce them without audit evidence in the
commit message.

Closes the gap that the regression-baseline pre-commit hook can't:
new closed-list additions, new rule sections, new merge-overrides, etc., that
do not increase any existing rule's violation count and would otherwise slip
through.

This script:
  1. Reads staged canon diffs (private/01-method/colometry-canon.md).
  2. Detects canon-extension patterns in the additions.
  3. Checks the proposed commit message (passed as argv[1]) for audit-
     evidence keywords or skip-safe claims.
  4. Exits 0 if no extension OR extension + audit evidence present.
  5. Exits 1 if extension detected without audit evidence.

Override (Stan-only, explicit decision):
    git commit --no-verify -m '...'

Usage (called from commit-msg hook):
    python3 validators/check_canon_extensions.py <commit-msg-file>
"""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
# Both the Layer-3 methodology canon AND the Layer-1 grammar surface table need
# the same audit gate: closed-list extensions to either are scope-changing
# additions per canon §7. Imported from GNT-Reader sibling 2026-05-05.
CANON_FILES = [
    "private/01-method/colometry-canon.md",
    "data/syntax-reference/hebrew-break-legality.md",
]

# ---------------------------------------------------------------------------
# Canon-extension patterns (anchored to lines added by the diff)
# ---------------------------------------------------------------------------

# (a) New rule section: "### Rule H1 — title", "### Rule H17 — title"
NEW_RULE_RE = re.compile(r"^### Rule H\d+\b")

# (b) New merge-override: "#### M1. title", "#### M5. title"
NEW_MERGE_OVERRIDE_RE = re.compile(r"^#### M\d+\.")

# (c) New §1 principle / sub-clause with explicit "(added DATE)" provenance
NEW_DATED_PRINCIPLE_RE = re.compile(r"^### .+\(added 20\d\d-\d\d-\d\d")

# (c-bis) Catch-all: any new H3 heading that isn't structural (§-numbered,
# Rule HN, Mn., or Part I/II/III). Catches new principle subsections like
# "### Mission", "### Container-Not-Originator" without requiring the
# explicit "(added DATE)" marker (most edits won't carry it).
NEW_PRINCIPLE_HEADING_RE = re.compile(
    r"^### (?!§|Rule\s+H?\d+|M\d+\.|Part\s+[IVX]+)[A-Z]"
)

# (d) Closed-list table row — pipe-leading row with 3+ cells, last cell Yes/No
CLOSED_LIST_TABLE_ROW_RE = re.compile(
    r"^\|\s*[A-Z][^|]+\|.+\|\s*(?:Yes|No)\s*\|\s*$"
)

# (e) New §7 (change protocol) trigger entry — numbered bold trigger
NEW_TRIGGER_ENTRY_RE = re.compile(r"^\s*\d+\.\s+\*\*[A-Z][^*]+\*\*\s+—")

# (f) New SCOPE-exclusion / scope bullet under a rule
NEW_SCOPE_EXCLUSION_RE = re.compile(r"^-\s+\*\*[A-Z][^*]+\*\*\s+—")

# (g) New bullet item with bolded label (any sub-list addition under a rule)
# Looser than (f) — doesn't require em-dash; catches more bullet-list extensions.
NEW_BULLET_LABEL_RE = re.compile(r"^-\s+\*\*[A-Z][^*]{2,}\*\*")

# ---------------------------------------------------------------------------
# Commit-message gate keywords
# ---------------------------------------------------------------------------

# Audit-evidence keywords — at least one must appear if extension detected.
#
# IMPORTANT: bare "audit" is too loose — it false-passes messages like
# "fake commit without audit evidence" (substring match catches the negation).
# Require either a strong-signal keyword (specific section ref, named pattern)
# OR an audit phrase that includes a completion verb / verdict word.
AUDIT_KEYWORDS = [
    "hostile audit",
    "trigger #",
    "§7",
    "retract",
    "retracted",
    "post-codification",
    "post-detection",
    "corpus-fit",
    "§8 update log",
    "§8 entry",
    "update log",
    "stan-authorized",
    "stan-direct",
    # Audit + completion-verb phrases (paired so bare "audit" doesn't false-pass)
    "audit complete",
    "audit completed",
    "audit passed",
    "audit verified",
    "audit verdict",
    "audit clean",
    "audit ok",
    "audit done",
    "audit found",
    "audit run",
    "ran audit",
    "ran the audit",
    "completed audit",
    "performed audit",
]

# Negation guards — if any of these appear, fail regardless of any audit
# keyword above. Defends against "fake commit without audit evidence" et al.
NEGATION_PATTERNS = [
    "no audit",
    "without audit",
    "needs audit",
    "needs an audit",
    "audit pending",
    "audit later",
    "skip audit",
    "skipped audit",
    "no §7",
    "no trigger",
    "no update log",
    "todo: audit",
    "todo audit",
    "fake commit",
]

# Skip-safe signals — explicit non-extension claims (typo, formatting, ...)
SKIP_SAFE_KEYWORDS = [
    "typo fix",
    "typo",
    "formatting",
    "defensibility-capture",
    "cross-reference update",
    "cross-ref update",
    "audit-skippable",
    "skip-safe",
]


def get_canon_diff() -> str:
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--unified=0"] + CANON_FILES,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout
    except Exception:
        return ""


def detect_extensions(diff: str) -> list[tuple[str, str]]:
    """Return list of (trigger-name, matched-line) tuples found in the
    additions of the diff."""
    indicators: list[tuple[str, str]] = []
    for line in diff.split("\n"):
        if not line.startswith("+") or line.startswith("+++"):
            continue
        body = line[1:].rstrip()
        if not body.strip():
            continue
        if NEW_RULE_RE.match(body):
            indicators.append(("new-rule", body[:80]))
        if NEW_MERGE_OVERRIDE_RE.match(body):
            indicators.append(("new-merge-override", body[:80]))
        if NEW_DATED_PRINCIPLE_RE.match(body):
            indicators.append(("new-dated-principle", body[:80]))
        elif NEW_PRINCIPLE_HEADING_RE.match(body):
            # Only report (c-bis) when (c) didn't already match — same line shouldn't
            # double-trigger.
            indicators.append(("new-principle-heading", body[:80]))
        if CLOSED_LIST_TABLE_ROW_RE.match(body):
            indicators.append(("closed-list-table-row", body[:80]))
        if NEW_TRIGGER_ENTRY_RE.match(body):
            indicators.append(("new-trigger-entry", body[:80]))
        if NEW_SCOPE_EXCLUSION_RE.match(body):
            indicators.append(("new-scope-exclusion", body[:80]))
        elif NEW_BULLET_LABEL_RE.match(body):
            # Only report (g) when (f) didn't already match.
            indicators.append(("new-bullet-label", body[:80]))
    return indicators


def has_audit_evidence(message: str) -> bool:
    """True if message contains a positive audit-evidence signal AND no
    negation guard (e.g., "without audit") is present."""
    msg_lower = message.lower()
    if any(neg in msg_lower for neg in NEGATION_PATTERNS):
        return False
    return any(k in msg_lower for k in AUDIT_KEYWORDS)


def has_skip_safe_claim(message: str) -> bool:
    msg_lower = message.lower()
    if any(neg in msg_lower for neg in NEGATION_PATTERNS):
        return False
    return any(k in msg_lower for k in SKIP_SAFE_KEYWORDS)


def main() -> int:
    if len(sys.argv) != 2:
        print(
            "Usage: check_canon_extensions.py <commit-msg-file>",
            file=sys.stderr,
        )
        return 0  # don't block on usage errors
    msg_path = Path(sys.argv[1])
    if not msg_path.exists():
        return 0
    message = msg_path.read_text(encoding="utf-8", errors="replace")

    # Skip empty, merge, and squash messages
    if (
        not message.strip()
        or message.startswith("Merge ")
        or message.startswith("Squashed ")
    ):
        return 0

    diff = get_canon_diff()
    if not diff:
        return 0  # no canon changes staged

    indicators = detect_extensions(diff)
    if not indicators:
        return 0  # no extension detected

    if has_audit_evidence(message):
        print(
            f"[canon-extension-check] Detected {len(indicators)} extension "
            f"indicator(s); audit evidence found in commit message. PASS."
        )
        return 0

    if has_skip_safe_claim(message):
        print(
            f"[canon-extension-check] Detected {len(indicators)} extension "
            f"indicator(s); commit claims skip-safe. Allowing — verify the "
            f"claim is accurate."
        )
        return 0

    # Extension detected, no audit evidence, no skip-safe claim → BLOCK
    print()
    print("=" * 72, file=sys.stderr)
    print("CANON EXTENSION DETECTED — AUDIT EVIDENCE REQUIRED", file=sys.stderr)
    print("=" * 72, file=sys.stderr)
    print(file=sys.stderr)
    print(
        "Per canon §7 mandatory-audit triggers (and the BoFM-precedent "
        "smuggling case), this commit introduces canon extensions that "
        "require an adversarial audit before landing.",
        file=sys.stderr,
    )
    print(file=sys.stderr)
    print("Detected extension indicators:", file=sys.stderr)
    for trigger, line in indicators[:10]:
        print(f"  [{trigger}] {line}", file=sys.stderr)
    if len(indicators) > 10:
        print(f"  ... and {len(indicators) - 10} more", file=sys.stderr)
    print(file=sys.stderr)
    print("To proceed, the commit message MUST contain ONE of:", file=sys.stderr)
    print(
        "  - An audit-evidence keyword (e.g., 'audit', 'hostile audit', "
        "'trigger #', 'post-codification', '§7', '§8 update log').",
        file=sys.stderr,
    )
    print(
        "  - A skip-safe claim (e.g., 'typo fix', 'cross-reference update', "
        "'defensibility-capture', 'audit-skippable') if the change qualifies.",
        file=sys.stderr,
    )
    print(
        "  - 'stan-authorized' or 'stan-direct' if Stan explicitly directed "
        "the change without audit (rare).",
        file=sys.stderr,
    )
    print(file=sys.stderr)
    print(
        "To bypass entirely (Stan-only, explicit decision):",
        file=sys.stderr,
    )
    print("    git commit --no-verify -m '...'", file=sys.stderr)
    print(file=sys.stderr)
    print(
        "Reformulate the commit message OR run the audit and document its "
        "verdict in the message before retrying.",
        file=sys.stderr,
    )
    print("=" * 72, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
