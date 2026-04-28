#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate prophetic woe-chain handling — Authorial Asymmetry Principle.

Operationalizes prophetic הוֹי/אוֹי (woe-particle) chain analysis per canon §1
(Authorial Asymmetry Principle) and §4 (Classical Commata, justification 4).

PATTERN:
  Line begins with הוֹי or אוֹי (woe particle); next line(s) form the woe content.
  Woe-chains may have asymmetric expansion (some woes = short classical commata,
  others = expanded 4–6-line oracle blocks) and that asymmetry is intentional.

SEVERITY:
  REVIEW-REQUIRED — judgment-heavy. Detecting woe-particle starts is mechanical;
  assessing asymmetric expansion or classical-comma stand-alone status requires
  editorial context. Per canon §1, do not pressure compact members to expand or
  expanded members to compress.

ARCHITECTURAL CONSTRAINT:
  No te'amim glyph predicates. Trigger logic uses Hebrew morpho-syntactic patterns
  ONLY. Te'amim may appear in annotations as defensibility-capture (Rule H8).

OUTPUT FORMAT:
  [DEVIATION]  file:line  woe-chain/asymmetric-expansion  REVIEW-REQUIRED
    brief description (woe-index, verse range, asymmetry type)

EXIT CODE:
  0 if zero findings, 1 if findings, 2 on setup error.

USAGE:
  PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_woe_chain.py
  PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_woe_chain.py --book isaiah
  PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_woe_chain.py --v2
  PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_woe_chain.py --json
  PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_woe_chain.py --verbose
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants — two-tier layout: v1/he-baseline + v2/he
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "he"

# Make _shared importable when this script is run as __main__.
sys.path.insert(0, str(REPO_ROOT / "validators"))

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers
# ---------------------------------------------------------------------------

# Hebrew points (cantillation U+0591–U+05AF + niqqud U+05B0–U+05BC, U+05C1–U+05C2,
# U+05C4–U+05C5, U+05C7). Strip these while preserving maqqef (U+05BE), paseq (U+05C0),
# and sof pasuq (U+05C3).
HEBREW_POINTS_RE = re.compile(r"[֑-ׇֽֿׁׂׅׄ]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"  # ׃

# Maqqef (orthographic word-joiner)
MAQQEF = "־"     # ־


def strip_points(token: str) -> str:
    """Return token with niqqud and te'amim stripped (consonant skeleton + sof pasuq + maqqef)."""
    return HEBREW_POINTS_RE.sub("", token)


# ---------------------------------------------------------------------------
# Verse-reference / blank line handling
# ---------------------------------------------------------------------------

VERSE_REF_RE = re.compile(r"^(\S+\s+)?\d+:\d+\s*$")


def is_skippable(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    if VERSE_REF_RE.match(s):
        return True
    return False


def parse_verse_ref(line: str):
    """If `line` is a 'C:V' verse-reference line, return (chapter, verse). Else None."""
    s = line.strip()
    m = re.match(r"^(?:\S+\s+)?(\d+):(\d+)\s*$", s)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


# ---------------------------------------------------------------------------
# Chapter / book name extraction from path
# ---------------------------------------------------------------------------

CHAPTER_FILENAME_RE = re.compile(r"-(\d+)\.txt$", re.IGNORECASE)


def book_name_from_path(path: Path) -> str:
    """Return the book directory name (e.g. '23-isaiah')."""
    return path.parent.name


def chapter_from_path(path: Path) -> int | None:
    m = CHAPTER_FILENAME_RE.search(path.name)
    if not m:
        return None
    return int(m.group(1))


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

def content_tokens(line: str) -> list[str]:
    """Split a line into tokens, dropping pure-sof-pasuq and verse-reference tokens."""
    out = []
    for tok in line.split():
        bare = strip_points(tok)
        if bare in ("", SOF_PASUQ):
            continue
        if re.match(r"^\d+:\d+$", bare):
            continue
        out.append(tok)
    return out


def first_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[0] if toks else None


def prosodic_word_count(line: str) -> int:
    """Count prosodic words (whitespace-delimited tokens with maqqef groups as one)."""
    return len(content_tokens(line))


# ---------------------------------------------------------------------------
# Finite-verb detection (simplified for woe-chain context)
# ---------------------------------------------------------------------------

# Woe-chain woes are typically INTRODUCTORY particles (הוֹי, אוֹי) followed by a
# vocative or minimal object, then expansion. The key signal for "end of one woe"
# is the START of the next woe-particle line. We track woe-particle line indices.

WOE_PARTICLE_SKELETONS = {"הוי", "אוי"}  # consonant skeletons after strip_points


def starts_with_woe_particle(line: str) -> bool:
    """True if the first content token's skeleton is a woe particle."""
    first = first_content_token(line)
    if not first:
        return False
    bare = strip_points(first)
    return bare in WOE_PARTICLE_SKELETONS


# ---------------------------------------------------------------------------
# Verse partitioning and woe-chain grouping
# ---------------------------------------------------------------------------

def partition_into_verses(lines: list[str]) -> list[tuple[int | None, int | None, list[int]]]:
    """Group line indices by verse.

    Returns a list of (chapter, verse, [line_indices]) tuples in source order.
    Verse-reference lines themselves are included as part of their verse but
    are skippable for content scanning.
    """
    verses: list[tuple[int | None, int | None, list[int]]] = []
    cur_chapter: int | None = None
    cur_verse: int | None = None
    cur_indices: list[int] = []
    for i, line in enumerate(lines):
        ref = parse_verse_ref(line)
        if ref is not None:
            # Flush current
            if cur_indices:
                verses.append((cur_chapter, cur_verse, cur_indices))
            cur_chapter, cur_verse = ref
            cur_indices = []
            continue
        if not line.strip():
            continue
        cur_indices.append(i)
    if cur_indices:
        verses.append((cur_chapter, cur_verse, cur_indices))
    return verses


def find_woe_chains(lines: list[str]) -> list[dict]:
    """Identify woe-chains: sequences of verses containing woe-particle-starter lines.

    Returns a list of woe-chain records:
      {
        'verses': [(chapter, verse), ...],
        'woe_starts': [line_index, ...],  # indices of lines starting with הוֹי/אוֹי
        'start_verse': (chapter, verse),
        'end_verse': (chapter, verse),
      }

    A new woe-chain begins when:
    - A verse with a woe-particle-start line appears after a gap (non-woe verses), OR
    - This is the first woe line encountered.

    The chain continues across consecutive verses that contain woe-particle-start lines.
    """
    verses = partition_into_verses(lines)
    woe_chains: list[dict] = []

    current_chain: dict | None = None

    for ch, vs, indices in verses:
        if (ch, vs) is None:
            continue

        # Find any woe-particle-starter lines in this verse
        woe_starts = []
        for idx in indices:
            if starts_with_woe_particle(lines[idx]):
                woe_starts.append(idx)

        if woe_starts:
            # This verse has woe-starter lines
            if current_chain is None:
                # Start a new chain
                current_chain = {
                    'verses': [(ch, vs)],
                    'woe_starts': woe_starts,
                    'start_verse': (ch, vs),
                    'end_verse': (ch, vs),
                }
            else:
                # Extend the current chain
                current_chain['verses'].append((ch, vs))
                current_chain['woe_starts'].extend(woe_starts)
                current_chain['end_verse'] = (ch, vs)
        else:
            # This verse has NO woe-starter lines
            if current_chain is not None:
                # End the current chain and save it
                woe_chains.append(current_chain)
                current_chain = None

    # Flush any remaining chain
    if current_chain is not None:
        woe_chains.append(current_chain)

    return woe_chains


# ---------------------------------------------------------------------------
# Asymmetry detection
# ---------------------------------------------------------------------------

def measure_woe_expansion(
    lines: list[str],
    woe_start_idx: int,
    next_woe_idx: int | None,
) -> dict:
    """Measure the expansion of a single woe (from woe_start_idx to next_woe_idx or EOF).

    Returns a dict with keys:
      'woe_start': line_index of the woe-particle line
      'woe_text': stripped text of the woe-particle line
      'line_count': number of content lines from woe_start to (but not including) next_woe
      'prosodic_word_count': total prosodic words in the woe expansion
      'is_short_classical': heuristic: ≤3 prosodic words → classical comma
      'is_medium': heuristic: 4–7 prosodic words → bicola or short oracle
      'is_long': heuristic: 8+ prosodic words → expanded oracle
    """
    woe_text = lines[woe_start_idx].strip()

    # Count lines and prosodic words from woe_start to next_woe (exclusive)
    end_idx = next_woe_idx if next_woe_idx is not None else len(lines)
    total_prosodic = 0
    line_count = 0

    for i in range(woe_start_idx, end_idx):
        if is_skippable(lines[i]):
            continue
        line_count += 1
        total_prosodic += prosodic_word_count(lines[i])

    # Heuristic thresholds for classical-comma vs. expanded oracle
    is_short_classical = total_prosodic <= 3
    is_medium = 4 <= total_prosodic <= 7
    is_long = total_prosodic >= 8

    return {
        'woe_start': woe_start_idx,
        'woe_text': woe_text,
        'line_count': line_count,
        'prosodic_word_count': total_prosodic,
        'is_short_classical': is_short_classical,
        'is_medium': is_medium,
        'is_long': is_long,
    }


def detect_asymmetric_expansion(woe_measurements: list[dict]) -> list[dict]:
    """Detect asymmetric expansion patterns across woe-chain members.

    The Authorial Asymmetry Principle (canon §1) protects intentional variation
    in series expansion. Flag as REVIEW-REQUIRED when a chain mixes:
      - short classical commata (≤3 words) with expanded oracles (8+ words), OR
      - medium-expansion (4–7 words) with long-expansion (8+ words).

    This is likely intentional but editorial context determines final placement.

    Returns a list of finding dicts for asymmetric patterns detected.
    """
    findings = []

    if len(woe_measurements) < 2:
        # Single woe or no woes: no asymmetry to flag
        return findings

    # Classify each woe by expansion type
    has_short = any(m['is_short_classical'] for m in woe_measurements)
    has_medium = any(m['is_medium'] for m in woe_measurements)
    has_long = any(m['is_long'] for m in woe_measurements)

    # Detect asymmetry: any mixing of expansion sizes (beyond uniform long or uniform medium)
    is_asymmetric = False
    if has_short and (has_medium or has_long):
        is_asymmetric = True
    elif has_medium and has_long:
        is_asymmetric = True

    if not is_asymmetric:
        return findings

    # Emit findings for each asymmetric member
    for i, m in enumerate(woe_measurements):
        if m['is_short_classical']:
            findings.append({
                'woe_index': i,
                'woe_start_line': m['woe_start'],
                'woe_text': m['woe_text'],
                'pattern': 'short_classical_in_mixed_chain',
                'prosodic_word_count': m['prosodic_word_count'],
                'line_count': m['line_count'],
                'annotation': (
                    'Short classical comma in mixed woe-chain. '
                    'Per Authorial Asymmetry Principle (canon §1), do not pressure '
                    'this compact member to expand. Preserve intentional brevity.'
                ),
            })
        elif m['is_medium'] and has_long:
            # Medium woe in chain with long woes
            findings.append({
                'woe_index': i,
                'woe_start_line': m['woe_start'],
                'woe_text': m['woe_text'],
                'pattern': 'medium_expansion_in_mixed_chain',
                'prosodic_word_count': m['prosodic_word_count'],
                'line_count': m['line_count'],
                'annotation': (
                    'Medium-expansion woe in mixed chain with longer expansions. '
                    'Per Authorial Asymmetry Principle (canon §1), preserve this '
                    'variation. Do not compress or expand to match neighboring woes.'
                ),
            })
        elif m['is_long'] and has_medium:
            # Long woe in chain with medium woes
            findings.append({
                'woe_index': i,
                'woe_start_line': m['woe_start'],
                'woe_text': m['woe_text'],
                'pattern': 'long_oracle_in_mixed_chain',
                'prosodic_word_count': m['prosodic_word_count'],
                'line_count': m['line_count'],
                'annotation': (
                    'Expanded oracle in mixed woe-chain with shorter members. '
                    'Per Authorial Asymmetry Principle (canon §1), preserve this '
                    'expansion. Do not compress to match more compact woes.'
                ),
            })

    return findings


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    findings: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    book = book_name_from_path(path)
    chapter_from_file = chapter_from_path(path)

    # Find all woe-chains in the file
    woe_chains = find_woe_chains(lines)

    if not woe_chains:
        return findings

    # For each woe-chain, measure expansion of each woe
    for chain in woe_chains:
        woe_measurements = []
        for i, woe_idx in enumerate(chain['woe_starts']):
            next_woe_idx = chain['woe_starts'][i + 1] if i + 1 < len(chain['woe_starts']) else None
            measurement = measure_woe_expansion(lines, woe_idx, next_woe_idx)
            woe_measurements.append(measurement)

        # Detect asymmetric patterns
        asymmetry_findings = detect_asymmetric_expansion(woe_measurements)
        for f in asymmetry_findings:
            # Enrich with file and verse context
            line_no = f['woe_start_line'] + 1  # 1-based

            # Find verse for this line
            verse_ctx = None
            verses = partition_into_verses(lines)
            for ch, vs, indices in verses:
                if f['woe_start_line'] in indices:
                    verse_ctx = (ch, vs)
                    break

            chapter, verse = verse_ctx if verse_ctx else (chapter_from_file, None)

            findings.append({
                'file_path': path,
                'file_rel': str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                'line_num': line_no,
                'rule': 'woe-chain/asymmetric-expansion',
                'severity': 'REVIEW-REQUIRED',
                'book': book,
                'chapter': chapter,
                'verse': verse,
                'woe_index': f['woe_index'],
                'woe_text': f['woe_text'],
                'pattern': f['pattern'],
                'prosodic_word_count': f['prosodic_word_count'],
                'line_count': f['line_count'],
                'annotation': f['annotation'],
                'brief': (
                    f"woe #{f['woe_index']} ({f['pattern']}) — "
                    f"{f['prosodic_word_count']} prosodic words, "
                    f"{f['line_count']} content lines"
                ),
            })

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def resolve_book_dir(base_dir: Path, book_arg: str) -> Path:
    """Resolve a --book argument permissively."""
    direct = base_dir / book_arg
    if direct.exists():
        return direct
    candidates = [d for d in base_dir.iterdir() if d.is_dir() and book_arg.lower() in d.name.lower()]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        print(
            f"ERROR: ambiguous book name {book_arg!r}; "
            f"matches: {[d.name for d in candidates]}",
            file=sys.stderr,
        )
        sys.exit(2)
    print(f"ERROR: book directory not found: {direct}", file=sys.stderr)
    sys.exit(2)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--book", metavar="BOOK", help="Restrict to one book.")
    parser.add_argument("--v2", action="store_true", help="Scan v2/he (default if v1 missing).")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show context.")
    parser.add_argument("--json", action="store_true", help="Emit JSON document.")
    args = parser.parse_args()

    base_dir = V2_DIR if args.v2 else V1_DIR
    tier_label = "v2/he" if args.v2 else "v1/he-baseline"
    if not base_dir.exists():
        # Fall back to the other tier rather than failing — v1 may be absent.
        alt = V2_DIR if not args.v2 else V1_DIR
        if alt.exists():
            base_dir = alt
            tier_label = "v2/he" if alt is V2_DIR else "v1/he-baseline"
        else:
            print(f"ERROR: neither {V1_DIR} nor {V2_DIR} found.", file=sys.stderr)
            sys.exit(2)

    if args.book:
        book_dir = resolve_book_dir(base_dir, args.book)
        files = sorted(book_dir.glob("*.txt"))
    else:
        files = sorted(base_dir.rglob("*.txt"))

    if not files:
        print(f"No .txt files found under {base_dir}", file=sys.stderr)
        sys.exit(2)

    all_findings: list[dict] = []
    for path in files:
        all_findings.extend(scan_file(path, verbose=args.verbose))

    exit_code = 1 if all_findings else 0

    if args.json:
        findings_json = []
        for f in all_findings:
            findings_json.append({
                "file": f["file_rel"],
                "line": f["line_num"],
                "rule": f["rule"],
                "severity": f["severity"],
                "book": f["book"],
                "chapter": f["chapter"],
                "verse": f["verse"],
                "woe_index": f["woe_index"],
                "woe_text": f["woe_text"],
                "pattern": f["pattern"],
                "prosodic_word_count": f["prosodic_word_count"],
                "line_count": f["line_count"],
                "annotation": f["annotation"],
                "brief": f["brief"],
            })

        by_pattern: dict[str, int] = {}
        for f in findings_json:
            by_pattern[f["pattern"]] = by_pattern.get(f["pattern"], 0) + 1

        doc = {
            "validator": "validate_woe_chain",
            "rule": "Authorial Asymmetry Principle (woe-chains)",
            "version": "1.0.0",
            "layer": 3,
            "book": args.book or "all",
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": findings_json,
            "counts": {"REVIEW-REQUIRED": len(findings_json)},
            "summary": {
                "total_findings": len(findings_json),
                "by_pattern": by_pattern,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output ---
    print("=" * 72)
    print(f"Woe-Chain Validator — Tanakh {tier_label}")
    print("Reference: canon §1 Authorial Asymmetry Principle + §4 Classical Commata")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Findings      : {len(all_findings)}")

    by_pattern: dict[str, int] = {}
    for f in all_findings:
        by_pattern[f["pattern"]] = by_pattern.get(f["pattern"], 0) + 1
    if by_pattern:
        print()
        for pattern, count in sorted(by_pattern.items()):
            print(f"  {pattern}: {count}")
    print()

    if all_findings:
        for f in all_findings:
            print(
                f"[DEVIATION]  {f['file_rel']}:{f['line_num']}  "
                f"{f['rule']}  {f['severity']}  {f['brief']}"
            )
            if args.verbose:
                print(f"    {f['woe_text'][:120]}")
                print(f"    {f['annotation']}")
                print()
    else:
        print("No woe-chain asymmetry findings. Woe-series expansion appears consistent.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
