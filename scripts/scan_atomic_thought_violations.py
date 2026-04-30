"""scan_atomic_thought_violations.py — Atomic-thought scanner for v2/he corpus.

Walks data/text-files/v2/he/<book>/<book>-NN.txt and flags lines that visibly
carry N≥2 propositions (canon §1 violations).  Five pattern classes:

  MULTI_VERB_NO_S3         — ≥2 finite verbs, S3 closed-list doesn't fire
  MID_LINE_SPEECH_INTRO    — speech-verb (וַיֹּאמֶר etc.) at position > 0
  WAYYIQTOL_AFTER_PP       — wayyiqtol immediately after a PP-headed token
  FRONTED_PRONOUN_VERB     — casus-pendens pronoun at pos 0, finite verb later
  TEMPORAL_CLOSER_PLUS_CLAUSE — temporal/locative closer phrase + wayyiqtol

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/scan_atomic_thought_violations.py
    PYTHONIOENCODING=utf-8 py -3 scripts/scan_atomic_thought_violations.py \
        --out private/03-sessions/2026-04-30-wave6-saturation-audit/atomic-thought-findings.csv
"""

import argparse
import csv
import os
import sys
from pathlib import Path

# ── project root on sys.path so validators._shared resolves ─────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

from validators._shared.morphology import (
    MAQQEF,
    PREP_SKELETONS,
    BOUND_PREP_PREFIXES,
    YIQTOL_KNOWN_NOUNS,
    YIQTOL_PREFIXES,
    closed_list_clause_boundary_split_positions,
    is_finite_verb_token,
    is_wayyiqtol_token,
    is_bare_prep_head,
    is_vav_coord_pp_head,
    partition_into_verses,
    skel,
    tokens,
    VERSE_REF_RE,
)

# ── constants ────────────────────────────────────────────────────────────────

V2_HE_ROOT = REPO_ROOT / "data" / "text-files" / "v2" / "he"

# Speech-intro wayyiqtol skeletons (closed list per spec)
SPEECH_INTRO_SKELS = {
    "ויאמר", "וידבר", "ויען", "ויקרא",
    # plural / suffixed forms
    "ויאמרו", "ידברו", "ויענו", "ויקראו",
}

# Fronted personal pronouns that signal casus-pendens (per spec)
FRONTED_PRONOUN_SKELS = {
    "ואתה", "אתה", "הוא", "אני", "אתם",
    # a few additional high-frequency forms
    "אנכי", "היא", "הם", "הן", "אנחנו",
}

# Temporal-closer skeleton sequences (leading tokens checked).
# Each entry is a tuple of ≥1 skeleton strings; all must match consecutive tokens.
TEMPORAL_CLOSER_PATTERNS: list[tuple[str, ...]] = [
    ("בעת", "ההיא"),
    ("ביום", "ההוא"),
    ("אחר", "הדברים", "האלה"),
    ("אחרי", "הדברים", "האלה"),
    ("בשנה",),           # followed by any determiner (heuristic: just flag keyword)
]

# ── helper: is_wayyiqtol_skel_at ────────────────────────────────────────────
# Permissive wayyiqtol test — for scanning mid-line positions where niqqud may
# be sparse or the position logic already provides context.

def _is_wayyiqtol_mid(token: str) -> bool:
    """True if token bears wayyiqtol consonant skeleton (ו + YIQTOL_PREFIX + stem).

    Used for mid-line position checks (position > 0 is already verified by caller).
    Falls back to skeleton check when is_wayyiqtol_token (niqqud-strict) rejects.
    """
    if is_wayyiqtol_token(token):
        return True
    # skeleton fallback
    t = token.split(MAQQEF, 1)[0] if MAQQEF in token else token
    s = skel(t)
    if len(s) < 4 or s[0] != "ו" or s[1] not in YIQTOL_PREFIXES:
        return False
    inner = s[1:]
    if inner in YIQTOL_KNOWN_NOUNS:
        return False
    return True


def _is_speech_intro_skel(token: str) -> bool:
    t = token.split(MAQQEF, 1)[0] if MAQQEF in token else token
    return skel(t) in SPEECH_INTRO_SKELS


def _is_pp_headed(token: str) -> bool:
    """True if token heads a PP (free prep, bound-prep-prefix, or vav-coord-PP)."""
    return is_bare_prep_head(token) or is_vav_coord_pp_head(token)


def _tokens_match_pattern(toks: list[str], start: int, pattern: tuple[str, ...]) -> bool:
    """True if `toks[start:start+len(pattern)]` skeletons match `pattern`."""
    if start + len(pattern) > len(toks):
        return False
    for i, p in enumerate(pattern):
        if skel(toks[start + i]) != p:
            return False
    return True


# ── five pattern checks ──────────────────────────────────────────────────────

def check_multi_verb_no_s3(line: str) -> dict | None:
    """MULTI_VERB_NO_S3: ≥2 finite verbs AND S3 closed-list fires nowhere."""
    toks = tokens(line)
    verb_toks = [t for t in toks if is_finite_verb_token(t)]
    if len(verb_toks) < 2:
        return None
    # If S3 has a pattern match anywhere, S3 would handle it — skip
    if closed_list_clause_boundary_split_positions(line):
        return None
    return {
        "pattern_class": "MULTI_VERB_NO_S3",
        "severity": "HIGH",
        "detail": " ".join(verb_toks[:4]),
    }


def check_mid_line_speech_intro(line: str) -> dict | None:
    """MID_LINE_SPEECH_INTRO: speech-verb (וַיֹּאמֶר etc.) at position > 0."""
    toks = tokens(line)
    for i, t in enumerate(toks):
        if i == 0:
            continue
        if _is_speech_intro_skel(t):
            return {
                "pattern_class": "MID_LINE_SPEECH_INTRO",
                "severity": "HIGH",
                "detail": t,
            }
    return None


def check_wayyiqtol_after_pp(line: str) -> dict | None:
    """WAYYIQTOL_AFTER_PP: wayyiqtol immediately after a PP-headed token (pos > 0)."""
    toks = tokens(line)
    for i in range(1, len(toks)):
        if not _is_wayyiqtol_mid(toks[i]):
            continue
        if i == 0:
            continue
        prev = toks[i - 1]
        if _is_pp_headed(prev):
            return {
                "pattern_class": "WAYYIQTOL_AFTER_PP",
                "severity": "MEDIUM",
                "detail": f"{prev} → {toks[i]}",
            }
    return None


def check_fronted_pronoun_verb(line: str) -> dict | None:
    """FRONTED_PRONOUN_VERB: casus-pendens pronoun at pos 0, finite verb at pos > 0."""
    toks = tokens(line)
    if not toks:
        return None
    if skel(toks[0]) not in FRONTED_PRONOUN_SKELS:
        return None
    # Need a finite verb somewhere after position 0
    for t in toks[1:]:
        if is_finite_verb_token(t):
            return {
                "pattern_class": "FRONTED_PRONOUN_VERB",
                "severity": "MEDIUM",
                "detail": f"{toks[0]} + {t}",
            }
    return None


def check_temporal_closer_plus_clause(line: str) -> dict | None:
    """TEMPORAL_CLOSER_PLUS_CLAUSE: temporal/locative closer phrase + wayyiqtol."""
    toks = tokens(line)
    for i, _ in enumerate(toks):
        for pattern in TEMPORAL_CLOSER_PATTERNS:
            if not _tokens_match_pattern(toks, i, pattern):
                continue
            # Need a wayyiqtol AFTER the pattern
            after_start = i + len(pattern)
            for j in range(after_start, len(toks)):
                if _is_wayyiqtol_mid(toks[j]) and j > 0:
                    return {
                        "pattern_class": "TEMPORAL_CLOSER_PLUS_CLAUSE",
                        "severity": "LOW",
                        "detail": " ".join(toks[i:j + 1]),
                    }
    return None


# Check ordering matters: speech-intro before multi-verb so HIGH classes don't
# double-report the same line (first match wins per line).
CHECKS = [
    check_mid_line_speech_intro,
    check_multi_verb_no_s3,
    check_wayyiqtol_after_pp,
    check_fronted_pronoun_verb,
    check_temporal_closer_plus_clause,
]


# ── corpus walker ────────────────────────────────────────────────────────────

def walk_corpus(v2_root: Path):
    """Yield (book_slug, verse_ref, line_num, line_text) for every content line."""
    for book_dir in sorted(v2_root.iterdir()):
        if not book_dir.is_dir():
            continue
        book_slug = book_dir.name
        for chapter_file in sorted(book_dir.glob("*.txt")):
            text = chapter_file.read_text(encoding="utf-8")
            cur_verse = "0:0"
            line_num = 0
            for raw in text.splitlines():
                line_num += 1
                stripped = raw.strip()
                if not stripped:
                    continue
                if VERSE_REF_RE.match(stripped):
                    cur_verse = stripped
                    continue
                yield book_slug, cur_verse, line_num, stripped


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Scan v2/he corpus for atomic-thought violations.")
    parser.add_argument("--out", default=None, help="CSV output file path (default: stdout only)")
    parser.add_argument("--book", default=None, help="Limit scan to one book slug (e.g. 32-jonah)")
    args = parser.parse_args()

    v2_root = V2_HE_ROOT
    if not v2_root.exists():
        print(f"ERROR: v2/he root not found: {v2_root}", file=sys.stderr)
        sys.exit(1)

    findings: list[dict] = []

    for book_slug, verse, line_num, line_text in walk_corpus(v2_root):
        if args.book and book_slug != args.book:
            continue
        for check in CHECKS:
            result = check(line_text)
            if result:
                findings.append({
                    "book": book_slug,
                    "verse": verse,
                    "line_num": line_num,
                    "pattern_class": result["pattern_class"],
                    "severity": result["severity"],
                    "line_text": line_text,
                    "detail": result.get("detail", ""),
                })
                break  # first match wins per line

    # ── summary ─────────────────────────────────────────────────────────────
    from collections import Counter
    class_counts = Counter(f["pattern_class"] for f in findings)
    verse_counts = Counter(f["book"] + " " + f["verse"] for f in findings)
    top_verses = verse_counts.most_common(10)

    print(f"\n{'='*60}")
    print(f"Atomic-thought violation scan  —  v2/he corpus")
    print(f"{'='*60}")
    print(f"Total findings: {len(findings)}")
    print(f"\nPer-class counts:")
    for cls in ["MULTI_VERB_NO_S3", "MID_LINE_SPEECH_INTRO", "WAYYIQTOL_AFTER_PP",
                "FRONTED_PRONOUN_VERB", "TEMPORAL_CLOSER_PLUS_CLAUSE"]:
        print(f"  {cls:<35} {class_counts.get(cls, 0):>5}")

    print(f"\nTop 10 affected verses:")
    for verse_key, cnt in top_verses:
        print(f"  {verse_key:<35} {cnt:>3} finding(s)")

    print(f"\nSample lines per class:")
    shown: set[str] = set()
    for cls in ["MULTI_VERB_NO_S3", "MID_LINE_SPEECH_INTRO", "WAYYIQTOL_AFTER_PP",
                "FRONTED_PRONOUN_VERB", "TEMPORAL_CLOSER_PLUS_CLAUSE"]:
        for f in findings:
            if f["pattern_class"] == cls and cls not in shown:
                line_display = f["line_text"][:90] + ("…" if len(f["line_text"]) > 90 else "")
                print(f"  [{cls}] {f['book']} {f['verse']}:")
                print(f"    {line_display}")
                shown.add(cls)
                break

    # ── CSV output ───────────────────────────────────────────────────────────
    fieldnames = ["book", "verse", "line_num", "pattern_class", "severity", "line_text"]

    # Always write to stdout
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, extrasaction="ignore",
                            lineterminator="\n")
    writer.writeheader()
    writer.writerows(findings)

    # Optionally also write to file
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8", newline="") as fh:
            fw = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore",
                                lineterminator="\n")
            fw.writeheader()
            fw.writerows(findings)
        print(f"\nCSV written → {out_path}", file=sys.stderr)

    print(f"\nDone. {len(findings)} findings across {len(class_counts)} classes.", file=sys.stderr)


if __name__ == "__main__":
    main()
