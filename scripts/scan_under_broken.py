#!/usr/bin/env python3
"""scan_under_broken.py — Detect over-merged (under-broken) lines in v2/he corpus.

Each colon should carry one proposition (canon §1 atomic thought). This scanner
finds lines that likely carry multiple propositions — a SPLIT was missed where
one should have been inserted.

Pattern classes
---------------
EXCESSIVE_PWC         Line has >12 prosodic words (13-15=MEDIUM, 16-20=HIGH, 21+=CRITICAL)
MULTI_CLAUSE          Finite verb at pos 0-1 AND another finite verb at pos >=4,
                      no S3 closed-list signature in between
SPEECH_INTRO_OVER_MERGED  Line starts with speech-intro verb + content following
                           recipient, PWC > 6
PP_ENUM_MISSED        >=3 PP heads, coordinated_pp_split_positions() returns empty
NP_ENUM_MISSED        >=4 NP heads, coordinated_np_split_positions() returns empty

Usage
-----
    PYTHONIOENCODING=utf-8 py -3 scripts/scan_under_broken.py [--output PATH]
"""

import csv
import os
import re
import sys
from pathlib import Path

# ── repo root ──────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import validators._shared.morphology as M

# ── paths ──────────────────────────────────────────────────────────────────
V2_HE_ROOT = REPO_ROOT / "data" / "text-files" / "v2" / "he"
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "private"
    / "03-sessions"
    / "2026-04-30-wave6-saturation-audit"
    / "under-broken-findings.csv"
)

# ── severity bands for EXCESSIVE_PWC ──────────────────────────────────────
def pwc_severity(count: int) -> str:
    if count >= 21:
        return "CRITICAL"
    if count >= 16:
        return "HIGH"
    if count >= 13:
        return "MEDIUM"
    return ""  # <= 12 → not flagged

# ── speech-intro verb skeletons ───────────────────────────────────────────
SPEECH_VERB_SKELS = {"ויאמר", "וידבר", "ויען", "ויקרא", "ויצו", "וידבר"}

def _is_speech_intro_verb(token: str) -> bool:
    return M.skel(token) in SPEECH_VERB_SKELS

# ── S3 closed-list token helpers (re-use M helpers) ──────────────────────

def _has_s3_signature_between(toks: list[str], start: int, end: int) -> bool:
    """True if any S3 pattern-closer token appears between positions start..end."""
    for i in range(start, min(end + 1, len(toks))):
        t = toks[i]
        if M.is_wayehi_ken_token(t):
            return True
        if M.is_species_formula_token(t):
            return True
        if M.is_year_noun_token(t):
            return True
    return False

# ── PP enumeration: count PP heads without split positions ────────────────

# Skeletons that look like vav+bound-prep but are actually negation/particles.
# is_vav_coord_pp_head mis-classifies ולא (vav-neg), ואל (vav-negation-jussive),
# ואם (vav-cond), ואך, ואף as PP-heads because their inner char is ל/א/etc.
_PP_FALSE_POSITIVES = {"ולא", "ואל", "ואם", "ואך", "ואף", "ואין", "ובל", "ועל"}

def _count_pp_heads(toks: list[str]) -> int:
    count = 0
    for tok in toks:
        s = M.skel(tok.split(M.MAQQEF, 1)[0]) if M.MAQQEF in tok else M.skel(tok)
        if s in _PP_FALSE_POSITIVES:
            continue
        if M.is_finite_verb_token(tok):
            continue
        if M.is_vav_coord_pp_head(tok) or M.is_bare_prep_head(tok):
            count += 1
    return count

# ── NP enumeration: count vav-coord-NP heads ─────────────────────────────

def _count_vav_np_heads(toks: list[str]) -> int:
    return sum(1 for i, tok in enumerate(toks) if i > 0 and M.is_vav_coord_np_head(tok))

# ── per-line checks ────────────────────────────────────────────────────────

def check_line(line: str) -> list[tuple[str, str]]:
    """Return list of (pattern_class, severity) for a content line."""
    findings: list[tuple[str, str]] = []
    toks = M.tokens(line)
    if not toks:
        return findings

    pwc = M.prosodic_word_count(line)

    # 1. EXCESSIVE_PWC
    sev = pwc_severity(pwc)
    if sev:
        findings.append(("EXCESSIVE_PWC", sev))

    # 2. MULTI_CLAUSE: finite verb at pos 0 or 1, AND another finite verb at pos >=4
    #    with no S3 closer in between
    if len(toks) >= 5:
        verb_at_head = (
            M.is_finite_verb_token(toks[0])
            or (len(toks) > 1 and M.is_finite_verb_token(toks[1]))
        )
        if verb_at_head:
            # find second finite verb at pos >= 4
            for j in range(4, len(toks)):
                if M.is_finite_verb_token(toks[j]):
                    # check S3 signature between pos 1 and j-1
                    if not _has_s3_signature_between(toks, 1, j - 1):
                        findings.append(("MULTI_CLAUSE", "HIGH"))
                    break

    # 3. SPEECH_INTRO_OVER_MERGED
    if toks and _is_speech_intro_verb(toks[0]) and pwc > 6:
        findings.append(("SPEECH_INTRO_OVER_MERGED", "HIGH"))

    # 4. PP_ENUM_MISSED: >=3 PP heads but coordinated_pp_split_positions returns empty
    if _count_pp_heads(toks) >= 3:
        if not M.coordinated_pp_split_positions(line):
            findings.append(("PP_ENUM_MISSED", "MEDIUM"))

    # 5. NP_ENUM_MISSED: >=3 vav-coord-NP heads but coordinated_np_split_positions
    #    returns empty (the S2 threshold is >=3 vav-coord = >=4 total, so mirror it)
    if _count_vav_np_heads(toks) >= 3:
        if not M.coordinated_np_split_positions(line):
            findings.append(("NP_ENUM_MISSED", "MEDIUM"))

    return findings

# ── file walker ────────────────────────────────────────────────────────────

VERSE_REF_RE = re.compile(r"^\d+:\d+$")


def scan_file(path: Path, book_slug: str) -> list[dict]:
    """Scan one v2/he chapter file; return list of finding dicts."""
    text = path.read_text(encoding="utf-8")
    rows: list[dict] = []
    cur_ref = ""
    line_num = 0
    for raw in text.splitlines():
        line_num += 1
        line = raw.strip()
        if not line:
            continue
        if VERSE_REF_RE.match(line):
            cur_ref = line
            continue
        findings = check_line(line)
        for pattern_class, severity in findings:
            rows.append(
                {
                    "book": book_slug,
                    "verse": cur_ref,
                    "line_num": line_num,
                    "pattern_class": pattern_class,
                    "severity": severity,
                    "line_text": line,
                }
            )
    return rows


def scan_corpus(v2_root: Path) -> list[dict]:
    all_rows: list[dict] = []
    for book_dir in sorted(v2_root.iterdir()):
        if not book_dir.is_dir():
            continue
        book_slug = book_dir.name
        for chapter_file in sorted(book_dir.glob("*.txt")):
            all_rows.extend(scan_file(chapter_file, book_slug))
    return all_rows

# ── main ───────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Scan v2/he for over-merged lines.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="CSV output path")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Scanning {V2_HE_ROOT} ...", file=sys.stderr)
    rows = scan_corpus(V2_HE_ROOT)

    # Write CSV
    fieldnames = ["book", "verse", "line_num", "pattern_class", "severity", "line_text"]
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    total = len(rows)
    from collections import Counter

    class_counts = Counter(r["pattern_class"] for r in rows)
    sev_counts = Counter(r["severity"] for r in rows)

    # Top 5 verses by finding density
    verse_counts: Counter = Counter()
    for r in rows:
        verse_counts[(r["book"], r["verse"])] += 1
    top5 = verse_counts.most_common(5)

    print(f"\nDone. {total} findings across {len(class_counts)} classes.\n")
    print("By class:")
    for cls, cnt in sorted(class_counts.items(), key=lambda x: -x[1]):
        print(f"  {cls:<30} {cnt}")
    print("\nBy severity:")
    for sev in ("CRITICAL", "HIGH", "MEDIUM"):
        print(f"  {sev:<10} {sev_counts.get(sev, 0)}")
    print("\nTop affected verses:")
    for (book, verse), cnt in top5:
        print(f"  {book}  {verse}  ({cnt} findings)")

    print(f"\nOutput: {output_path}")


if __name__ == "__main__":
    main()
