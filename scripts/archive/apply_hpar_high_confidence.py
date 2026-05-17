"""
Apply the ULTRA-STRONG high-confidence Hpar splits to v2/heb.

Reads data/syntax-reference/hpar-high-confidence.tsv (the share-A1 frame-args
subset = canonical synonymous-parallelism), splits each affected v2/heb line
at the recorded clause boundary using Macula token positions for accurate
character-offset computation.

Implements the ULTRA-STRONG tier from today's docket — the high-confidence
subset that bypasses apply_validators.py's divergence guard because the
operation is forward-compatible (insert line break only; never removes
editorial work).

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/apply_hpar_high_confidence.py
    PYTHONIOENCODING=utf-8 py -3 scripts/apply_hpar_high_confidence.py --dry-run
"""
import argparse
import csv
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "validators"))

from validators._shared import macula_constituents as MC


def _normalize_skel(s: str) -> str:
    """Strip te'amim/niqqud/maqqef + whitespace for fuzzy matching."""
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"[֑-ֿ׀-ׇ־]", "", s)
    s = re.sub(r"\s+", "", s)
    return s


def find_split_offset(line_text: str, cl_b_first_token: MC.Token,
                      preceding_skel_accum: str = "") -> int:
    """Walk line_text whitespace-tokens; find the position where cl_b's first
    token begins. Returns the character offset (0-based) of the split point.

    Strategy: walk whitespace-tokens with running consonant-skel accumulator.
    The split happens BEFORE the token whose contribution starts matching
    cl_b's first token's skel.

    `preceding_skel_accum` is unused at offset-search time; kept for caller-
    API stability (eventually for context-aware multi-finding handling).
    """
    target_skel = cl_b_first_token.consonant_skel
    if not target_skel:
        return -1

    # Find the FIRST whitespace-token whose stripped skel starts with the
    # target's first 2-3 consonants (close-enough match for line/word boundary).
    # Walk tokens via re.finditer to get accurate character positions.
    for m in re.finditer(r"\S+", line_text):
        tok = m.group(0)
        tok_skel = _normalize_skel(tok)
        if not tok_skel:
            continue
        # Three matching strategies (any wins):
        # (a) exact equality
        if tok_skel == target_skel:
            return m.start()
        # (b) tok ends with target (tok includes leading vav-prefix etc.)
        if tok_skel.endswith(target_skel) and len(tok_skel) - len(target_skel) <= 2:
            # Adjust offset to skip the leading prefix
            # but for simplicity just return the token start
            return m.start()
        # (c) target ends with tok (tok is a maqqef-bound prefix; need next token too)
        if target_skel.startswith(tok_skel) and len(target_skel) - len(tok_skel) <= 4:
            return m.start()
        # (d) tok contains target as substring of length ≥3
        if len(target_skel) >= 3 and target_skel in tok_skel:
            return m.start()

    return -1


# Skip-list: per-entry (book, chapter, verse) tuples flagged in 2026-05-07
# editorial review as borderline / likely-FP outside the relative-clause class
# (which is now caught mechanically by the extractor's אֲשֶׁר/דִּי end guard).
# Each entry has a one-line rationale; surface for editorial decision before
# adding to or removing from this list.
_EDITORIAL_SKIP = frozenset({
    # Stan editorial review 2026-05-07: these two stay skipped.
    ("09-1samuel", 2, 22),      # sequential narrative (Eli was old AND he heard) — relative-clause-via-A1 misfire
    ("19-psalms", 51, 18),      # protasis-then-consequence (do not desire / would I give) — one logical unit
    # Other 5 cleared by Stan; entries below were previously skipped pending
    # editorial review and now apply:
    #   ("07-judges", 5, 30),    SPLIT — rhetorical-Q bicolon (Song of Deborah)
    #   ("09-1samuel", 9, 13),   SPLIT — temporal-sequential, each its own ATU
    #   ("11-1kings", 18, 25),   SPLIT — coordinated imperatives within speech
    #   ("20-proverbs", 23, 23), SPLIT — antithetic Wisdom-Lit imperative bicolon
    #   ("24-jeremiah", 49, 11), SPLIT — prophetic-oracle command/promise bicolon
})


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="Don't write changes; just report")
    ap.add_argument("--tsv", default=None, help="Override input TSV path")
    args = ap.parse_args()

    tsv_path = Path(args.tsv) if args.tsv else (
        REPO_ROOT / "data" / "syntax-reference" / "hpar-high-confidence.tsv"
    )
    he_dir = REPO_ROOT / "data" / "text-files"  / "v2" / "heb"

    # Group findings by file (excluding skip-list)
    findings_by_file: dict[Path, list[dict]] = defaultdict(list)
    skipped_by_editorial = 0
    with tsv_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            key = (row["book"], int(row["chapter"]), int(row["verse"]))
            if key in _EDITORIAL_SKIP:
                skipped_by_editorial += 1
                continue
            book_slug = row["book"]
            file_path = he_dir / book_slug / f"{book_slug.split('-', 1)[1]}-{int(row['chapter']):02d}.txt"
            findings_by_file[file_path].append(row)
    if skipped_by_editorial:
        print(f"[editorial-skip] {skipped_by_editorial} findings skipped per editorial review", file=sys.stderr)

    applied = 0
    skipped = 0
    misses = 0

    for file_path, findings in findings_by_file.items():
        if not file_path.exists():
            print(f"[miss] {file_path} not found", file=sys.stderr)
            misses += len(findings)
            continue

        original_text = file_path.read_text(encoding="utf-8")
        lines = original_text.split("\n")
        # Sort findings by file_line descending so later splits don't shift earlier line indices
        findings.sort(key=lambda r: -int(r["file_line"]))

        for r in findings:
            file_line_idx = int(r["file_line"]) - 1  # 1-based to 0-based
            book_slug = r["book"]
            chapter = int(r["chapter"])
            verse = int(r["verse"])

            if file_line_idx >= len(lines):
                print(f"[skip] {file_path.name}:{file_line_idx+1} out of range", file=sys.stderr)
                skipped += 1
                continue

            line_text = lines[file_line_idx]
            if not line_text.strip():
                print(f"[skip] {file_path.name}:{file_line_idx+1} empty", file=sys.stderr)
                skipped += 1
                continue

            # Re-load Macula clauses to get cl_b's first token for offset
            try:
                vclauses = MC.get_verse_clauses(book_slug, chapter, verse)
                vtokens = MC.get_verse_tokens(book_slug, chapter, verse)
            except Exception as e:
                print(f"[skip] {file_path.name}:{file_line_idx+1} macula error: {e}", file=sys.stderr)
                skipped += 1
                continue

            # Match line to verse-token slice
            cursor = 0
            verse_lines = []
            for i, ln in enumerate(lines):
                if i >= file_line_idx:
                    break
                if ln.strip() and not re.match(r"^\d+:\d+\s*$", ln.strip()):
                    matched, cursor = MC.match_sense_line_tokens(vtokens, ln, cursor)
            line_tokens, _ = MC.match_sense_line_tokens(vtokens, line_text, cursor)

            # Find cl_b by head text match (heads in TSV)
            head_b_text = r["head_b"]
            head_b_skel = _normalize_skel(head_b_text)
            cl_b_first_token = None
            from validators.colometry.validate_parallel_clause_split import (
                _is_leaf_clause, _clause_head_verb,
            )
            for cl in vclauses:
                if not _is_leaf_clause(cl):
                    continue
                head = _clause_head_verb(cl)
                if head and _normalize_skel(head.text) == head_b_skel:
                    cl_b_first_token = cl.tokens[0] if cl.tokens else head
                    break

            if cl_b_first_token is None:
                print(f"[skip] {file_path.name}:{file_line_idx+1} can't locate cl_b for head {head_b_text}", file=sys.stderr)
                skipped += 1
                continue

            offset = find_split_offset(line_text, cl_b_first_token)
            if offset < 0:
                print(f"[skip] {file_path.name}:{file_line_idx+1} can't compute offset for {cl_b_first_token.text}", file=sys.stderr)
                skipped += 1
                continue

            prior = line_text[:offset].rstrip()
            nxt = line_text[offset:].lstrip()
            if not prior or not nxt:
                print(f"[skip] {file_path.name}:{file_line_idx+1} split would produce empty half", file=sys.stderr)
                skipped += 1
                continue

            lines[file_line_idx] = prior + "\n" + nxt
            applied += 1

        new_text = "\n".join(lines)
        if new_text != original_text and not args.dry_run:
            file_path.write_text(new_text, encoding="utf-8")

    print(f"Applied: {applied}")
    print(f"Skipped: {skipped}")
    print(f"Misses: {misses}")
    if args.dry_run:
        print("(dry-run — no files written)")


if __name__ == "__main__":
    main()
