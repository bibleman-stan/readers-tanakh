#!/usr/bin/env python3
"""
scan_eng_gloss_readability.py — Minimum Coherent Viability scanner for eng-gloss layer.

Walks data/text-files/v2/eng-gloss/, flags lines that fail readability checks.

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/scan_eng_gloss_readability.py
    PYTHONIOENCODING=utf-8 py -3 scripts/scan_eng_gloss_readability.py --output findings.csv
"""

import re
import csv
import sys
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSE_REF_RE = re.compile(r'^\d+:\d+\s*$')

AUXILIARIES = {
    'was', 'were', 'is', 'are', 'be', 'been', 'being',
    'had', 'has', 'have',
    'do', 'does', 'did',
    'will', 'would', 'should', 'could',
}
PRONOUNS = {'i', 'he', 'she', 'they', 'it', 'we', 'you', 'me', 'him', 'her', 'them', 'us'}
FILLER_WORDS = {'and', 'the', 'a', 'an', 'not', 'no'}
STRANDED_POOL = AUXILIARIES | PRONOUNS | FILLER_WORDS

# Words that are almost never meaningful alone on a colon
SINGLE_STRAND_WORDS = {
    'he', 'she', 'it', 'and', 'to', 'for', 'from', 'of', 'the', 'a', 'an',
    'in', 'on', 'at', 'by', 'with', 'or', 'but',
}

# Pattern: consecutive identical words (case-insensitive)
DOUBLED_TOKEN_RE = re.compile(r'\b(\w+)\s+\1\b', re.IGNORECASE)

# Pattern: "of X of Y of" — repeated construct-of chain
MANGLED_CONSTRUCT_RE = re.compile(r'\bof\s+\w+\s+of\s+\w+\s+of\b', re.IGNORECASE)

# Pattern: line starts with "and Xed <non-article subject-ish>"
# Low-confidence VSO heuristic
VSO_ORDER_RE = re.compile(
    r'^and\s+\w+ed\s+(?!the\b|a\b|an\b|to\b|of\b|with\b|in\b|on\b|by\b|his\b|her\b|their\b|its\b|my\b|your\b|our\b)([A-Z]\w*|\w+)',
    re.IGNORECASE,
)

# Capitalized word (likely proper noun) — simple heuristic
CAPITALIZED_NAME_RE = re.compile(r'\b[A-Z][a-z]{2,}\b')


# ---------------------------------------------------------------------------
# Checkers — each returns (pattern_class, severity) or None
# ---------------------------------------------------------------------------

def check_doubled_token(line: str):
    """Consecutive identical tokens."""
    if DOUBLED_TOKEN_RE.search(line):
        return ('DOUBLED_TOKEN', 'HIGH')
    return None


def check_stranded_auxiliary(line: str):
    """Line consists almost entirely of auxiliaries, pronouns, fillers."""
    tokens = line.lower().split()
    if not tokens:
        return None
    # Only flag if short and all tokens are in the stranded pool
    if len(tokens) <= 5 and all(t in STRANDED_POOL for t in tokens):
        # Must have at least one auxiliary to avoid flagging pure pronoun lines
        if any(t in AUXILIARIES for t in tokens):
            return ('STRANDED_AUXILIARY', 'HIGH')
    return None


def check_mangled_construct(line: str):
    """3+ 'of' tokens OR the of-X-of-Y-of pattern."""
    of_count = len(re.findall(r'\bof\b', line, re.IGNORECASE))
    if of_count >= 3:
        return ('MANGLED_CONSTRUCT', 'HIGH')
    if MANGLED_CONSTRUCT_RE.search(line):
        return ('MANGLED_CONSTRUCT', 'HIGH')
    return None


def check_pronoun_np_confusion(line: str):
    """Line starts with 'and he/she/they' and has a capitalized name in next 4 tokens."""
    tokens = line.split()
    if len(tokens) < 4:
        return None
    first = tokens[0].lower()
    second = tokens[1].lower() if len(tokens) > 1 else ''
    if first == 'and' and second in ('he', 'she', 'they', 'it'):
        # Look at tokens 2..5 for a capitalized name
        window = tokens[2:6]
        for tok in window:
            tok_clean = tok.rstrip('.,;:')
            if tok_clean and tok_clean[0].isupper() and tok_clean[1:].islower() and len(tok_clean) >= 3:
                # Exclude common non-name capitalizations at start of sentence context
                if tok_clean.lower() not in ('yahweh', 'the', 'his', 'her', 'their', 'its', 'my', 'our', 'your'):
                    return ('PRONOUN_NP_CONFUSION', 'MEDIUM')
    return None


def check_vso_order(line: str):
    """Low-confidence VSO: 'and Xed <apparent-subject>'."""
    if VSO_ORDER_RE.match(line):
        # Extra filter: line shouldn't just be a common verbal clause without ambiguity
        return ('VSO_ORDER', 'LOW')
    return None


def check_single_word_strand(line: str):
    """1-2 token lines that are semantically empty."""
    tokens = line.lower().split()
    if len(tokens) == 0:
        return None
    if len(tokens) <= 2 and all(t in SINGLE_STRAND_WORDS for t in tokens):
        return ('SINGLE_WORD_STRAND', 'MEDIUM')
    return None


CHECKERS = [
    check_doubled_suffix_pronoun,  # specific subclass — fires before generic
    check_doubled_token,
    check_stranded_auxiliary,
    check_mangled_construct,
    check_pronoun_np_confusion,
    check_vso_order,
    check_single_word_strand,
]


# ---------------------------------------------------------------------------
# File parser
# ---------------------------------------------------------------------------

def parse_gloss_file(path: Path):
    """
    Yield (verse_ref, line_num_in_file, content_line) for every non-empty,
    non-verse-ref line.
    """
    current_verse = 'unknown'
    with path.open(encoding='utf-8') as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.rstrip('\n')
            stripped = line.strip()
            if not stripped:
                continue
            if VERSE_REF_RE.match(stripped):
                current_verse = stripped.strip()
                continue
            yield current_verse, lineno, stripped


# ---------------------------------------------------------------------------
# Main scanner
# ---------------------------------------------------------------------------

def scan_corpus(gloss_root: Path):
    """Walk all eng-gloss files; return list of finding dicts."""
    findings = []
    for book_dir in sorted(gloss_root.iterdir()):
        if not book_dir.is_dir():
            continue
        book_slug = book_dir.name
        for gloss_file in sorted(book_dir.glob('*.txt')):
            for verse_ref, lineno, line_text in parse_gloss_file(gloss_file):
                for checker in CHECKERS:
                    result = checker(line_text)
                    if result:
                        pattern_class, severity = result
                        findings.append({
                            'book': book_slug,
                            'verse': verse_ref,
                            'line_num': lineno,
                            'pattern_class': pattern_class,
                            'severity': severity,
                            'line_text': line_text,
                        })
                        break  # one finding per line (highest-priority checker wins)
    return findings


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(findings, file=sys.stderr):
    from collections import Counter
    total = len(findings)
    print(f"\nTotal findings: {total}", file=file)

    class_counts = Counter(f['pattern_class'] for f in findings)
    print("\nPer-class counts:", file=file)
    for cls, cnt in class_counts.most_common():
        print(f"  {cls}: {cnt}", file=file)

    verse_counts = Counter(f"{f['book']}  {f['verse']}" for f in findings)
    print("\nTop 10 most-affected verses:", file=file)
    for verse, cnt in verse_counts.most_common(10):
        print(f"  {verse}  ({cnt} finding{'s' if cnt > 1 else ''})", file=file)
    print("", file=file)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Scan eng-gloss corpus for minimum coherent viability failures."
    )
    parser.add_argument(
        '--gloss-root',
        default=None,
        help="Path to eng-gloss root. Defaults to data/text-files/v2/eng-gloss/ "
             "relative to the repo root (two levels up from scripts/).",
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help="Write CSV findings to this file instead of (or in addition to) stdout.",
    )
    args = parser.parse_args()

    # Resolve gloss root
    if args.gloss_root:
        gloss_root = Path(args.gloss_root)
    else:
        script_dir = Path(__file__).resolve().parent
        repo_root = script_dir.parent
        gloss_root = repo_root / 'data' / 'text-files' / 'v2' / 'eng-gloss'

    if not gloss_root.exists():
        print(f"ERROR: eng-gloss root not found: {gloss_root}", file=sys.stderr)
        sys.exit(1)

    findings = scan_corpus(gloss_root)

    # CSV fieldnames
    fieldnames = ['book', 'verse', 'line_num', 'pattern_class', 'severity', 'line_text']

    # Write to stdout
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(findings)

    # Optionally write to file as well
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open('w', newline='', encoding='utf-8') as fh:
            file_writer = csv.DictWriter(fh, fieldnames=fieldnames)
            file_writer.writeheader()
            file_writer.writerows(findings)
        print(f"Findings written to: {out_path}", file=sys.stderr)

    print_summary(findings)


if __name__ == '__main__':
    main()
