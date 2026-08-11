#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corpus scanner — cross-line construct-chain breaks in v2/heb.

Three pattern classes:

  CONSTRUCT_HEAD_STRANDED
    Line N's last token is a construct head; line N+1 is the NEXT line in the
    same verse. ALL such pairs are reported. h16_c may have caught some during
    cascade; this is the full audit sweep.

  CONSTRUCT_HEAD_WITH_RECTUM
    Subset of CONSTRUCT_HEAD_STRANDED where line N+1's first token is
    plausibly the rectum (not vav-coord, not finite verb, not bare particle).
    Cascade SHOULD have merged these — flag as merge failure.

  MID_LINE_CONSTRUCT_BROKEN
    A construct-head token appears in the INTERIOR of a line (not last)
    followed by a token that cannot serve as its rectum (finite verb, vav-
    coordinated NP/PP head, bare particle). The construct chain is split
    mid-line.

Output: CSV to private/03-sessions/2026-04-30-wave6-saturation-audit/
        construct-chain-findings.csv

Usage:
    PYTHONIOENCODING=utf-8 py -3 5-machinery/scripts/scan_construct_chain_breaks.py
"""

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V2_DIR = REPO_ROOT / "data" / "text-files"  / "v2" / "heb"
OUT_DIR = REPO_ROOT / "private" / "03-sessions" / "2026-04-30-wave6-saturation-audit"
OUT_FILE = OUT_DIR / "construct-chain-findings.csv"

# Make 5-machinery/validators._shared importable
sys.path.insert(0, str(REPO_ROOT / "5-machinery/validators"))

from _shared.morphology import (  # noqa: E402
    is_construct_head_token,
    is_finite_verb_token,
    is_vav_coord_np_head,
    is_vav_coord_pp_head,
    partition_into_verses,
    skel,
    tokens,
    DISCOURSE_PARTICLES,
    VOCATIVE_PARTICLES,
    MAQQEF,
)

# ---------------------------------------------------------------------------
# Helper predicates
# ---------------------------------------------------------------------------

BARE_PARTICLES = DISCOURSE_PARTICLES | VOCATIVE_PARTICLES | {
    "לא", "אל", "כי", "אם", "פן", "אך", "רק", "גם", "אף",
    "הן", "הנה", "כן", "אז", "עתה", "הלא",
}


def _is_weak_rectum_start(token: str) -> bool:
    """True if token CANNOT plausibly be a rectum (i.e., blocks rectum-inference).

    A token blocks rectum inference if it is:
      - a vav-coordinated NP head (opens new coord NP, not continuation of chain)
      - a vav-coordinated PP head
      - a finite verb (new clause, not an NP in genitive position)
      - a bare discourse/vocative particle
    """
    if is_finite_verb_token(token):
        return True
    if is_vav_coord_np_head(token):
        return True
    if is_vav_coord_pp_head(token):
        return True
    s = skel(token)
    if s in BARE_PARTICLES:
        return True
    return False


def _is_rectum_blocker_mid_line(token: str) -> bool:
    """True if a token following a construct head mid-line breaks the chain.

    Construct heads may be immediately followed by rectum (normal), but if
    followed by a finite verb, vav-coord head, or bare particle, the chain
    is broken. Returns True only for clear blockers (conservative).
    """
    if is_finite_verb_token(token):
        return True
    if is_vav_coord_np_head(token):
        return True
    if is_vav_coord_pp_head(token):
        return True
    s = skel(token)
    # sof-pasuq alone means end of verse — not really a blocker token issue,
    # but sof-pasuq on the construct head itself signals verse-final head.
    if s in BARE_PARTICLES:
        return True
    return False


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

FIELDNAMES = [
    "book", "verse", "line_n_num", "pattern_class", "severity",
    "line_n_text", "line_n1_text",
]


def scan_file(filepath: Path, book_slug: str, findings: list[dict]) -> None:
    text = filepath.read_text(encoding="utf-8")
    for (ch, vs), lines in partition_into_verses(text):
        verse_ref = f"{ch}:{vs}"
        if not lines:
            continue

        # ── Pattern 1 + 2: cross-line construct-head stranding ──────────────
        for i in range(len(lines) - 1):
            line_n = lines[i]
            line_n1 = lines[i + 1]
            toks_n = tokens(line_n)
            if not toks_n:
                continue
            last_tok = toks_n[-1]
            # Strip sof-pasuq from last token before testing (it attaches to
            # the last word of the verse; the construct check operates on the
            # consonant/niqqud form which skel() handles, but is_construct_head_token
            # operates on the raw token — sof-pasuq doesn't affect the skel).
            if not is_construct_head_token(last_tok):
                continue

            toks_n1 = tokens(line_n1)
            first_n1 = toks_n1[0] if toks_n1 else None

            if first_n1 is not None and not _is_weak_rectum_start(first_n1):
                # Line N+1 first token is plausibly the rectum → merge failure
                findings.append({
                    "book": book_slug,
                    "verse": verse_ref,
                    "line_n_num": i + 1,
                    "pattern_class": "CONSTRUCT_HEAD_WITH_RECTUM",
                    "severity": "HIGH",
                    "line_n_text": line_n,
                    "line_n1_text": line_n1,
                })
            else:
                # First token of N+1 is a blocker (finite verb / vav-coord / particle)
                # or line N+1 is empty → head is stranded with no adjacent rectum
                findings.append({
                    "book": book_slug,
                    "verse": verse_ref,
                    "line_n_num": i + 1,
                    "pattern_class": "CONSTRUCT_HEAD_STRANDED",
                    "severity": "MEDIUM",
                    "line_n_text": line_n,
                    "line_n1_text": line_n1 if line_n1 else "",
                })

        # ── Pattern 3: mid-line construct broken ────────────────────────────
        for i, line in enumerate(lines):
            toks = tokens(line)
            if len(toks) < 2:
                continue
            # Walk every token except the last (last-token case handled by P1/P2)
            for j in range(len(toks) - 1):
                tok = toks[j]
                if not is_construct_head_token(tok):
                    continue
                # The immediately following token should be the rectum.
                # If it's a blocker, the construct chain is broken mid-line.
                next_tok = toks[j + 1]
                if _is_rectum_blocker_mid_line(next_tok):
                    findings.append({
                        "book": book_slug,
                        "verse": verse_ref,
                        "line_n_num": i + 1,
                        "pattern_class": "MID_LINE_CONSTRUCT_BROKEN",
                        "severity": "LOW",
                        "line_n_text": line,
                        "line_n1_text": "",
                    })
                    break  # one finding per line for mid-line pattern


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    findings: list[dict] = []

    book_dirs = sorted(V2_DIR.iterdir()) if V2_DIR.exists() else []
    for book_dir in book_dirs:
        if not book_dir.is_dir():
            continue
        book_slug = book_dir.name
        for chap_file in sorted(book_dir.glob("*.txt")):
            scan_file(chap_file, book_slug, findings)

    # Write CSV
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_FILE.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(findings)

    # Summary
    total = len(findings)
    class_counts: dict[str, int] = {}
    for f in findings:
        class_counts[f["pattern_class"]] = class_counts.get(f["pattern_class"], 0) + 1

    print(f"Total findings: {total}")
    for cls, cnt in sorted(class_counts.items(), key=lambda x: -x[1]):
        print(f"  {cls}: {cnt}")

    # Top 10 by verse (book + verse combo)
    verse_counts: dict[str, int] = {}
    for f in findings:
        key = f"{f['book']} {f['verse']}"
        verse_counts[key] = verse_counts.get(key, 0) + 1
    top10 = sorted(verse_counts.items(), key=lambda x: -x[1])[:10]
    print("\nTop 10 affected verses:")
    for verse, cnt in top10:
        print(f"  {verse}: {cnt} finding(s)")

    print(f"\nOutput written to: {OUT_FILE}")


if __name__ == "__main__":
    main()
