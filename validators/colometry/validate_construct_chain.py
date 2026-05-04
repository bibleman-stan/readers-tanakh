#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Rule H2 — Construct Chain Default (IR-driven).

Rule H2 (canon §5 H2; Joüon-Muraoka §129; Waltke-O'Connor §9):
A construct chain (nomen regens in construct state + nomen rectum) is a single
bound noun phrase. No line break may occur inside an unmodified construct chain.

Detection (IR-driven, post-2026-05-05 Macula pivot):
  Walk each verse's Macula lowfat constituent tree, recursively collecting all
  Constituent nodes whose `is_construct_chain` predicate is True (i.e.,
  wg_rule == "NPofNP" — the parser's authoritative NP-of-NP / construct-chain
  classification). For each NPofNP constituent, map its first and last token to
  v2/he editorial sense-lines via `match_sense_line_tokens`. If first-token's
  sense-line index ≠ last-token's sense-line index, the construct chain is
  split across editorial sense-lines — emit finding.

  This replaces the prior three tag/skel-driven heuristics:
    - DEFINITE-ARTICLE RECTUM (article-prefix on next-line first token)
    - DIVINE NAME COMPOUND (closed-list YHWH/אדני followers)
    - COMMON CONSTRUCT REGENS ENDINGS (closed list of frequent forms)
  All were pre-IR approximations of "is this a construct chain?". The IR
  exposes the constituent parser's direct answer; we ask it instead of guessing.

  KNOWN LIMITATION: The IR's NPofNP recall depends on Macula parser quality.
  Divine-name compounds (יהוה צבאות) are sometimes tagged as apposition or
  flat-NP rather than NPofNP and may not be surfaced. We do NOT add hand-list
  fallback here — that would re-introduce the heuristic noise the port is
  designed to eliminate. If a missing-NPofNP class proves load-bearing, the
  fix is upstream (parser-level) or in a separate, narrowly-scoped validator.

  APPOSITION (NpaNp / Np-Appos) is SEPARATE from construct chains and is NOT
  flagged by this validator (see Constituent.is_apposition).

Severity:
  All findings emit REVIEW-REQUIRED. The IR's finding-set is significantly
  smaller and tighter than the heuristic's (~6553 → expected ~700-1500 per the
  2026-05-05 audit), but parser recall needs editor confirmation before
  promotion to STRONG. Mirrors the verb_object_bond IR-port pattern (commit
  c6bd30576): no STRONG promotions until editorial triage.

Sof-pasuq suppression: NPofNPs whose final token sits at verse-end (sof pasuq)
are NOT cross-line splits — they're verse-end punctuation and the chain
terminates with the verse. Suppressed.

Architectural constraint:
  No te'amim glyph triggers anywhere. The IR exposes constituent structure,
  morph, role, and frame semantics — none accent-derived.

Output format:
    [DEVIATION]  file:line_number  H2/construct  SEVERITY  brief description

JSON `subcase` field is preserved for downstream-orchestrator compatibility,
but the only emitted subcase post-port is "npofnp_split" (the IR's single
declarative class; no longer three separate heuristic-named subcases).

Exit code: 0 if zero violations, 1 if violations found, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_construct_chain.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_construct_chain.py --book jonah
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_construct_chain.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_construct_chain.py --verbose
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants — collapsed two-tier layout: v1/he-baseline + v2/he
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "he"

# ---------------------------------------------------------------------------
# Macula IR import
# ---------------------------------------------------------------------------
sys.path.insert(0, str(REPO_ROOT / "validators"))
from _shared import macula_constituents as MC  # noqa: E402

# ---------------------------------------------------------------------------
# Hebrew Unicode constants
# ---------------------------------------------------------------------------

# Niqqud / cantillation marks to strip when isolating consonant skeleton
# U+0591–U+05C7: Hebrew cantillation and points
HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"


# ---------------------------------------------------------------------------
# Verse-reference / blank line handling
# ---------------------------------------------------------------------------

VERSE_REF_RE = re.compile(r"^(\S+\s+)?\d+:\d+\s*$")


def is_skippable(line: str) -> bool:
    """Return True for blank lines and verse-reference-only lines."""
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
    """Return the book directory name (e.g. '01-genesis')."""
    return path.parent.name


def chapter_from_path(path: Path) -> int | None:
    m = CHAPTER_FILENAME_RE.search(path.name)
    if not m:
        return None
    return int(m.group(1))


# ---------------------------------------------------------------------------
# Verse partitioning
# ---------------------------------------------------------------------------

def partition_into_verses(lines: list[str]) -> list[tuple[int | None, int | None, list[int]]]:
    """Group line indices by verse.

    Returns a list of (chapter, verse, [line_indices]) tuples in source order.
    """
    verses: list[tuple[int | None, int | None, list[int]]] = []
    cur_chapter: int | None = None
    cur_verse: int | None = None
    cur_indices: list[int] = []
    for i, line in enumerate(lines):
        ref = parse_verse_ref(line)
        if ref is not None:
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


# ---------------------------------------------------------------------------
# IR helpers
# ---------------------------------------------------------------------------

def collect_npofnp_constituents(constituents: list["MC.Constituent"]) -> list["MC.Constituent"]:
    """Recursively gather all Constituent nodes where is_construct_chain == True."""
    out: list["MC.Constituent"] = []

    def walk(node: "MC.Constituent | MC.Token") -> None:
        if isinstance(node, MC.Token):
            return
        if node.is_construct_chain:
            out.append(node)
        for c in node.children:
            walk(c)

    for r in constituents:
        walk(r)
    return out


def token_ends_with_sof_pasuq(tok: "MC.Token") -> bool:
    """Return True if this token's surface form contains the sof pasuq mark."""
    return SOF_PASUQ in tok.text


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    """IR-driven scan for Rule H2 construct-chain (NPofNP) splits across sense-lines.

    Per verse:
      1. Pull lowfat verse tokens + top-level constituents.
      2. Greedy-align each editorial sense-line to its slice of verse tokens,
         building a token_id -> sense_line_index map.
      3. Recursively collect all NPofNP constituents in the verse.
      4. For each NPofNP, look up its first and last token's sense-line indices.
         If they differ, emit a violation. If the last token has sof pasuq,
         skip (verse-end punctuation, not a true split).
    """
    violations: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    book_slug = book_name_from_path(path)
    verses = partition_into_verses(lines)

    for ch, vs, indices in verses:
        if ch is None or vs is None:
            continue
        # Sense-lines in this verse, in source order, dropping skippables
        sense_indices = [i for i in indices if not is_skippable(lines[i])]
        if len(sense_indices) < 2:
            # Need at least two sense-lines for a cross-line split to be possible
            continue

        # Pull lowfat verse tokens + constituents
        try:
            verse_tokens = MC.get_verse_tokens(book_slug, ch, vs)
            verse_constituents = MC.get_verse_constituents(book_slug, ch, vs)
        except (FileNotFoundError, ValueError, KeyError):
            continue
        if not verse_tokens or not verse_constituents:
            continue

        # Greedy-align each sense-line to the verse's tokens, then build
        # token_id -> sense_line_idx map for fast lookup.
        token_to_line: dict[str, int] = {}
        line_to_tokens: dict[int, list["MC.Token"]] = {}
        cursor = 0
        for line_idx, src_idx in enumerate(sense_indices):
            matched, cursor = MC.match_sense_line_tokens(
                verse_tokens, lines[src_idx], start_idx=cursor
            )
            line_to_tokens[src_idx] = matched
            for tok in matched:
                token_to_line[tok.xml_id] = line_idx

        # Recursively gather all NPofNP constituents in this verse
        npofnp_list = collect_npofnp_constituents(verse_constituents)
        if not npofnp_list:
            continue

        for npofnp in npofnp_list:
            chain_tokens = npofnp.tokens
            if len(chain_tokens) < 2:
                continue

            first_tok = chain_tokens[0]
            last_tok = chain_tokens[-1]

            # Sof-pasuq suppression: chain ends at verse-end, not a true split
            if token_ends_with_sof_pasuq(last_tok):
                continue

            first_line_idx = token_to_line.get(first_tok.xml_id)
            last_line_idx = token_to_line.get(last_tok.xml_id)
            # If alignment failed for either endpoint, skip (defensive — can't
            # confirm a cross-line split without both anchors).
            if first_line_idx is None or last_line_idx is None:
                continue
            if first_line_idx == last_line_idx:
                continue

            # Cross-line NPofNP split. Map back to source line numbers.
            first_src_idx = sense_indices[first_line_idx]
            last_src_idx = sense_indices[last_line_idx]
            line_n = lines[first_src_idx]
            line_next = lines[last_src_idx]

            chain_text = " ".join(t.text for t in chain_tokens)
            violations.append({
                "file": path.name,
                "file_path": path,
                "line_num": first_src_idx + 1,
                "rule": "H2/construct",
                "severity": "REVIEW-REQUIRED",
                "subcase": "npofnp_split",
                "brief": (
                    f"NPofNP construct chain split across sense-lines — "
                    f"{first_tok.text!r}…{last_tok.text!r} (chain: {chain_text})"
                ),
                "line": line_n.rstrip(),
                "next_line": line_next.rstrip(),
                "next_line_num": last_src_idx + 1,
                "book": book_slug,
                "chapter": ch,
                "verse": vs,
            })

    return violations


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--book",
        metavar="BOOK",
        help="Restrict scan to one book folder name (e.g. 'jonah'). "
             "Default: all books in the target directory.",
    )
    parser.add_argument(
        "--v2",
        action="store_true",
        help="Scan v2/he (editorial gold standard) instead of v1/he-baseline.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show next-line context for each violation.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as a single JSON document to STDOUT instead of human-readable lines.",
    )
    args = parser.parse_args()

    base_dir = V2_DIR if args.v2 else V1_DIR
    tier_label = "v2/he" if args.v2 else "v1/he-baseline"

    if not base_dir.exists():
        print(
            f"ERROR: {base_dir} not found. "
            f"Run the ingest/baseline scripts first.",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.book:
        book_dir = base_dir / args.book
        if not book_dir.exists():
            print(f"ERROR: book directory not found: {book_dir}", file=sys.stderr)
            sys.exit(2)
        files = sorted(book_dir.glob("*.txt"))
    else:
        files = sorted(base_dir.rglob("*.txt"))

    if not files:
        print(f"No .txt files found under {base_dir}", file=sys.stderr)
        sys.exit(2)

    all_violations: list[dict] = []
    for path in files:
        all_violations.extend(scan_file(path, verbose=args.verbose))

    exit_code = 1 if all_violations else 0

    # --- JSON output mode ---
    if args.json:
        findings = []
        for v in all_violations:
            severity = v["severity"]
            applied_action = "merge_with_next" if severity == "STRONG-MERGE-CANDIDATE" else None
            findings.append({
                "file": str(v["file_path"].relative_to(REPO_ROOT)).replace("\\", "/"),
                "line": v["line_num"],
                "severity": "DEVIATION",
                "tag": severity,
                "subcase": v["subcase"],
                "rule_id": "H2.1",
                "rule_short": "construct chain split across lines",
                "brief": v["brief"],
                "next_line": v.get("next_line_num"),
                "applied_action": applied_action,
            })

        by_severity_json: dict[str, int] = {}
        by_tag: dict[str, int] = {}
        by_subcase: dict[str, int] = {}
        for f in findings:
            by_severity_json[f["severity"]] = by_severity_json.get(f["severity"], 0) + 1
            by_tag[f["tag"]] = by_tag.get(f["tag"], 0) + 1
            by_subcase[f["subcase"]] = by_subcase.get(f["subcase"], 0) + 1

        doc = {
            "validator": "validate_construct_chain",
            "rule": "Rule H2 — Construct Chain Default",
            "layer": 3,
            "book": args.book or "all",
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": findings,
            "summary": {
                "total_findings": len(findings),
                "by_severity": by_severity_json,
                "by_tag": by_tag,
                "by_subcase": by_subcase,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output (default) ---
    print("=" * 72)
    print(f"Rule H2 Construct Chain validator (IR-driven) — Tanakh {tier_label}")
    print(f"Reference: canon §5 H2; Joüon-Muraoka §129; Waltke-O'Connor §9")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Violations    : {len(all_violations)}")

    by_severity: dict[str, int] = {}
    for v in all_violations:
        by_severity[v["severity"]] = by_severity.get(v["severity"], 0) + 1
    if by_severity:
        print()
        for sev, count in sorted(by_severity.items()):
            print(f"  {sev}: {count}")
    print()

    if all_violations:
        for v in all_violations:
            print(
                f"[DEVIATION]  {v['file']}:{v['line_num']}  "
                f"{v['rule']}  {v['severity']}  {v['brief']}"
            )
            print(f"    {v['line'][:120]}")
            if args.verbose and v.get("next_line"):
                print(f"    → {v['next_line'][:120]}")
            print()
    else:
        print("No violations found. Rule H2 construct-chain integrity is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
