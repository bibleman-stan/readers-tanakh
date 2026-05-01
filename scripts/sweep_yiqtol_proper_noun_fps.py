#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sweep_yiqtol_proper_noun_fps.py — TAHOT-tag-driven sweep of YIQTOL false-positive proper nouns.

The skel-based `is_finite_verb_skel` heuristic in `validators/_shared/morphology.py`
returns True for any token whose skeleton starts with י/ת/א/נ + has ≥3 more
characters AND is not in `YIQTOL_KNOWN_NOUNS`. This produces systematic false
positives for Hebrew proper nouns starting with those consonants — e.g.,
`אֶלְקָנָה` (Elkanah) skel = `אלקנה`, classified as 1cs yiqtol verb form.

Each FP blocks downstream merge logic that depends on `is_finite_verb_token`
returning False for the proper noun (e.g., m2_verb_bare_np_rebond, the
both_lines_have_finite_verb guard, etc.). Per audit 2026-04-30 D3, this
class blocks ~350-400 prose merge candidates corpus-wide.

This script uses the `v0/morph/` layer (persisted from TAHOT tags 2026-04-30,
commit b4d90ebe1) to identify ALL proper nouns whose skel matches the YIQTOL
FP pattern but who aren't already in `YIQTOL_KNOWN_NOUNS`. Output is a
deduplicated, frequency-sorted list of additions.

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/sweep_yiqtol_proper_noun_fps.py
    PYTHONIOENCODING=utf-8 py -3 scripts/sweep_yiqtol_proper_noun_fps.py --verbose
    PYTHONIOENCODING=utf-8 py -3 scripts/sweep_yiqtol_proper_noun_fps.py --emit-python
        # Emits Python list literal suitable for paste into morphology.py
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

# Ensure repo importability
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from validators._shared import morph_tags as MT  # noqa: E402
from validators._shared import morphology as M  # noqa: E402

V0_PROSE = ROOT / "data" / "text-files" / "v0" / "prose"
V0_MORPH = ROOT / "data" / "text-files" / "v0" / "morph"

YIQTOL_PREFIXES = M.YIQTOL_PREFIXES  # ("י", "ת", "א", "נ")
KNOWN_NOUNS = M.YIQTOL_KNOWN_NOUNS  # already-covered set


def _match_yiqtol_fp_shape(skel: str) -> bool:
    """Mirror is_finite_verb_skel's yiqtol path — returns True iff the skel
    would be FP-classified as a 1cs/3ms/3fs/3pl yiqtol verb. We invert: any
    proper noun whose skel matches this shape is a candidate FP."""
    if len(skel) < 4:
        return False
    if skel[0] not in YIQTOL_PREFIXES:
        return False
    if skel == "יש":
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--emit-python", action="store_true",
                    help="Print Python list literal for paste into morphology.py")
    ap.add_argument("--min-frequency", type=int, default=1,
                    help="Only emit additions appearing ≥N times in corpus")
    args = ap.parse_args()

    if not V0_MORPH.exists():
        print(f"ERROR: v0/morph layer not found at {V0_MORPH}", file=sys.stderr)
        print("Run: PYTHONIOENCODING=utf-8 py -3 scripts/ingest_tahot.py --all-books",
              file=sys.stderr)
        return 1

    # Walk corpus token-by-token. We need to align v0/prose tokens (for skel)
    # with v0/morph tags (for proper-noun classification). The two layers have
    # the SAME ortho-word count per verse (verified at v0/morph build time),
    # so we can iterate ortho-position by ortho-position.

    fp_counter: Counter[str] = Counter()
    fp_examples: dict[str, str] = {}  # skel -> example surface form

    for book_dir in sorted(V0_PROSE.iterdir()):
        if not book_dir.is_dir():
            continue
        for prose_file in sorted(book_dir.glob("*.txt")):
            morph_file = V0_MORPH / book_dir.name / prose_file.name
            if not morph_file.exists():
                continue

            prose_text = prose_file.read_text(encoding="utf-8")
            morph_text = morph_file.read_text(encoding="utf-8")

            # Both files: alternating "<ref>" / "<content>" / blank.
            # Build per-verse aligned token+tag lists.
            for verse_he, verse_morph in _zip_verses(prose_text, morph_text):
                # Hebrew tokens: prosodic-words (whitespace-split). Each may
                # span multiple ortho words via maqqef.
                he_tokens = verse_he.split()
                # Morph tags: " | "-separated, one per ortho word.
                morph_tags = [t.strip() for t in verse_morph.split(" | ")]

                # Walk ortho-word-by-ortho-word.
                ortho_idx = 0
                for tok in he_tokens:
                    sub_tokens = tok.split(M.MAQQEF)
                    for sub in sub_tokens:
                        if ortho_idx >= len(morph_tags):
                            break
                        tag = morph_tags[ortho_idx]
                        ortho_idx += 1
                        if not MT.is_proper_noun(tag):
                            continue
                        # Strip teamim from sub-token for skel
                        skel = M.skel(sub)
                        if not _match_yiqtol_fp_shape(skel):
                            continue
                        if skel in KNOWN_NOUNS:
                            continue
                        fp_counter[skel] += 1
                        if skel not in fp_examples:
                            fp_examples[skel] = sub

    # Filter by min-frequency
    additions = sorted(
        [(skel, cnt) for skel, cnt in fp_counter.items() if cnt >= args.min_frequency],
        key=lambda x: (-x[1], x[0]),
    )

    if args.emit_python:
        print(f"# {len(additions)} new YIQTOL FP proper-noun skels (TAHOT-tag-driven sweep)")
        print(f"# Each is currently FP-classified as a yiqtol verb by is_finite_verb_skel.")
        for skel, cnt in additions:
            example = fp_examples.get(skel, "?")
            print(f'    "{skel}",   # x{cnt} — e.g. {example}')
        return 0

    print("=" * 72)
    print("YIQTOL false-positive proper-noun sweep (TAHOT-tag-driven)")
    print("=" * 72)
    print(f"v0/morph corpus: {V0_MORPH}")
    print(f"YIQTOL_KNOWN_NOUNS already has: {len(KNOWN_NOUNS)} entries")
    print(f"")
    print(f"New FP proper-noun skels found: {len(additions)}")
    total_instances = sum(cnt for _, cnt in additions)
    print(f"Total corpus instances of these FPs: {total_instances}")
    print()
    print("Top 30 by frequency:")
    for skel, cnt in additions[:30]:
        example = fp_examples.get(skel, "?")
        print(f"  {skel}: {cnt:>4} instances  (e.g. {example})")
    if len(additions) > 30:
        print(f"  ... +{len(additions) - 30} more entries")
    print()
    print("To apply: re-run with --emit-python and paste into")
    print(f"  validators/_shared/morphology.py YIQTOL_KNOWN_NOUNS set")
    return 0


def _zip_verses(prose_text: str, morph_text: str):
    """Yield (he_content, morph_content) pairs per verse, aligned by verse-ref."""
    import re
    VERSE_RE = re.compile(r"^(\d+):(\d+)\s*$")

    def parse(text: str):
        out: dict[str, str] = {}
        cur_ref = None
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                cur_ref = None
                continue
            if VERSE_RE.match(stripped):
                cur_ref = stripped
                continue
            if cur_ref is not None:
                out[cur_ref] = stripped
                cur_ref = None
        return out

    he_verses = parse(prose_text)
    morph_verses = parse(morph_text)
    for ref, he_content in he_verses.items():
        morph_content = morph_verses.get(ref)
        if morph_content is None:
            continue
        yield (he_content, morph_content)


if __name__ == "__main__":
    sys.exit(main())
