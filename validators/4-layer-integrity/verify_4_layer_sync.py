#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_4_layer_sync.py — Tanakh 4-layer integrity verifier.

The Tanakh app stacks four synchronized layers per Hebrew ATU cola:
    1. Hebrew                  — data/text-files/v2/heb/
    2. Transliteration         — data/text-files/v2/translit/
    3. Interlinear (per-word)  — data/text-files/v2/eng-interlinear/
    4. KJV verbatim English    — data/text-files/v2/eng-kjv/
       (renamed from v2/eng-gloss 2026-05-12 to reflect the actual substrate)

The 4-layer integrity invariant: for every Hebrew ATU cola line in v2/heb,
the corresponding translit and eng-interlinear lines must contain the SAME
orthographic-word count (split on " | "), and the eng-kjv layer
must contain exactly ONE English line per cola.

A regression in this invariant means a layer drifted by a token (e.g. an
upstream generator silently merged or split a cola) — the visible app
would render layers misaligned. Per-Hebrew-ATU-cola token-count parity
across all four layers is the single hardest constraint of the Tanakh
migration; this verifier is the gate.

Maqqef-edge case (revised after empirical check)
-------------------------------------------------
The translit and eng-interlinear layers SPLIT maqqef-joined Hebrew
compounds into separate ``|``-delimited tokens (each prosodic word is
its own pipe-separated entry). The layer-alignment invariant is
therefore:

    prosodic_word_count(Hebrew cola) == pipe_token_count(translit cola)
    == pipe_token_count(interlinear cola)

where "prosodic word" = a Hebrew word delimited by either a space OR a
maqqef. The reference splitter lives at ``scripts/build_books.py``
``split_hebrew_cola_to_words()``; this verifier replicates the algorithm
locally so it can run standalone.

(An orthographic-word count — maqqef-joined = one word — is used for
display rendering, not for cross-layer alignment.)

Usage
-----
    py -3 validators/4-layer-integrity/verify_4_layer_sync.py --book genesis
    py -3 validators/4-layer-integrity/verify_4_layer_sync.py --all
    py -3 validators/4-layer-integrity/verify_4_layer_sync.py --book genesis --chapter 1

Exit code: 0 on pass, 1 on any mismatch.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V2_HEB = REPO_ROOT / "data" / "text-files"  / "v2" / "heb"
V2_TRANSLIT = REPO_ROOT / "data" / "text-files" / "v2" / "translit"
V2_INTER = REPO_ROOT / "data" / "text-files" / "v2" / "eng-interlinear"
V2_KJV = REPO_ROOT / "data" / "text-files" / "v2" / "eng-kjv"

MAQQEF = "־"
VERSE_REF_RE = re.compile(r"^\d+:\d+$")

# Mirror of the BOOK_REGISTRY from regenerate_english.py — kept local
# so the verifier has no cross-module dependency.
BOOK_SUBDIRS = [
    "01-genesis", "02-exodus", "03-leviticus", "04-numbers", "05-deuteronomy",
    "06-joshua", "07-judges", "08-ruth", "09-1samuel", "10-2samuel",
    "11-1kings", "12-2kings", "13-1chronicles", "14-2chronicles",
    "15-ezra", "16-nehemiah", "17-esther",
    "18-job", "19-psalms", "20-proverbs", "21-ecclesiastes", "22-songofsongs",
    "23-isaiah", "24-jeremiah", "25-lamentations", "26-ezekiel",
    "27-daniel", "28-hosea", "29-joel", "30-amos", "31-obadiah", "32-jonah",
    "33-micah", "34-nahum", "35-habakkuk", "36-zephaniah", "37-haggai",
    "38-zechariah", "39-malachi",
]


def parse_chapter(filepath: Path):
    """Parse a v2 layered chapter file into [{ref, lines}].

    Lines are kept VERBATIM (no further splitting). Verses are demarcated
    by ``N:N`` ref headers and blank-line separators.
    """
    verses = []
    current = None
    if not filepath.exists():
        return verses
    with filepath.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\r\n")
            if VERSE_REF_RE.match(line.strip()):
                if current is not None and current["lines"]:
                    verses.append(current)
                current = {"ref": line.strip(), "lines": []}
                continue
            if line.strip() == "":
                if current is not None and current["lines"]:
                    verses.append(current)
                    current = None
                continue
            if current is not None:
                current["lines"].append(line)
    if current is not None and current["lines"]:
        verses.append(current)
    return verses


def hebrew_cola_prosodic_count(cola: str) -> int:
    """Count prosodic words in a Hebrew cola (maqqef-joined = N parts).

    This matches the alignment that translit / eng-interlinear emit:
    each prosodic word becomes one ``|``-delimited token.
    """
    pwords = [p for p in cola.split(" ") if p]
    n = 0
    for pw in pwords:
        if MAQQEF in pw:
            n += len(pw.split(MAQQEF))
        else:
            n += 1
    return n


def pipe_layer_word_count(line: str) -> int:
    """Count |-separated POSITIONS in a translit/interlinear cola line.

    Counts positions (including empty ones), not just non-empty tokens —
    TAHOT's source data has empty English entries for some Hebrew words
    (e.g., maqqef-bound וְאֶת prefix at 2Sam 5:8 / Isa 10:15), and those
    empty positions are valid alignment slots. The 4-layer integrity
    invariant is *positional* parity (slot N in translit lines up with
    slot N in interlinear and Hebrew prosodic word N), not non-empty-
    token parity.

    Pre-2026-05-12 the function filtered empties, producing false-positive
    drift reports on the 2 stubborn 2Sam 5:8 + Isa 10:15 chapters.
    """
    if not line.strip():
        return 0
    return len(line.split("|"))


def verify_book(book_subdir: str, *, only_chapter: int | None = None):
    """Run the verifier on one book. Returns (n_chapters, n_pass, n_fail, fails)."""
    he_dir = V2_HEB / book_subdir
    if not he_dir.is_dir():
        return (0, 0, 0, [(book_subdir, "missing he/ dir")])

    chapter_files = sorted(he_dir.glob("*.txt"))
    n_chapters = 0
    n_pass = 0
    n_fail = 0
    fails: list[tuple[str, str]] = []

    for cf in chapter_files:
        if only_chapter is not None:
            m = re.search(r"-(\d+)\.txt$", cf.name)
            if not m or int(m.group(1)) != only_chapter:
                continue
        n_chapters += 1
        chapter_id = f"{book_subdir}/{cf.name}"

        he_verses = parse_chapter(cf)
        tr_verses = parse_chapter(V2_TRANSLIT / book_subdir / cf.name)
        in_verses = parse_chapter(V2_INTER / book_subdir / cf.name)
        kjv_verses = parse_chapter(V2_KJV / book_subdir / cf.name)

        tr_by_ref = {v["ref"]: v["lines"] for v in tr_verses}
        in_by_ref = {v["ref"]: v["lines"] for v in in_verses}
        kjv_by_ref = {v["ref"]: v["lines"] for v in kjv_verses}

        chapter_failed = False
        for verse in he_verses:
            ref = verse["ref"]
            he_cola = verse["lines"]
            tr_cola = tr_by_ref.get(ref, [])
            in_cola = in_by_ref.get(ref, [])
            kjv_cola = kjv_by_ref.get(ref, [])

            # Check 1: cola count parity across layers.
            counts = {
                "he": len(he_cola),
                "translit": len(tr_cola),
                "interlinear": len(in_cola),
            }
            kjv_present = bool(kjv_cola)
            if kjv_present:
                counts["kjv"] = len(kjv_cola)
            unique = set(counts.values())
            if len(unique) > 1:
                chapter_failed = True
                fails.append((
                    chapter_id,
                    f"{ref}: cola-count mismatch — {counts}"
                ))
                continue

            # Check 2: per-cola word-count parity (he vs translit vs interlinear).
            for i, (h, t, n) in enumerate(zip(he_cola, tr_cola, in_cola)):
                he_n = hebrew_cola_prosodic_count(h)
                tr_n = pipe_layer_word_count(t)
                in_n = pipe_layer_word_count(n)
                if not (he_n == tr_n == in_n):
                    chapter_failed = True
                    fails.append((
                        chapter_id,
                        f"{ref}:cola{i + 1} — he={he_n} translit={tr_n} interlinear={in_n}"
                    ))

            # Check 3: KJV layer (if present) is one line per cola — already
            # implied by the cola-count check above, but assert explicit
            # 1-to-1 line correspondence when KJV is present.
            if kjv_present and len(kjv_cola) != len(he_cola):
                chapter_failed = True
                fails.append((
                    chapter_id,
                    f"{ref}: kjv cola count {len(kjv_cola)} != he {len(he_cola)}"
                ))

        if chapter_failed:
            n_fail += 1
        else:
            n_pass += 1

    return n_chapters, n_pass, n_fail, fails


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--book", help="Book key (e.g. genesis, jonah) or subdir (01-genesis)")
    p.add_argument("--all", action="store_true", help="Verify every book")
    p.add_argument("--chapter", type=int, help="Restrict to one chapter number")
    p.add_argument("--quiet", action="store_true", help="Suppress per-fail detail; print only summary")
    p.add_argument("--json", action="store_true",
                   help="Emit run_all.py-compatible JSON summary on stdout (one fail = one finding)")
    p.add_argument("--v2", action="store_true",
                   help="Reserved for run_all.py compatibility (this verifier always uses v2)")
    args = p.parse_args(argv)

    # Resolve book → subdir
    book_to_subdir = {sub.split("-", 1)[1]: sub for sub in BOOK_SUBDIRS}
    book_to_subdir.update({sub: sub for sub in BOOK_SUBDIRS})

    if args.book:
        if args.book not in book_to_subdir:
            if args.json:
                import json as _j
                print(_j.dumps({"summary": {"total_findings": 0}, "error": f"unknown book {args.book}"}))
            else:
                print(f"ERROR: unknown book key: {args.book}")
                print(f"Valid keys: {sorted(book_to_subdir.keys())}")
            return 2
        targets = [book_to_subdir[args.book]]
    elif args.all or args.json:
        # JSON mode (used by run_all.py) defaults to all-books — there's no
        # meaningful per-book invocation in the dashboard context.
        targets = BOOK_SUBDIRS
    else:
        p.print_help()
        return 2

    total_chapters = 0
    total_pass = 0
    total_fail = 0
    all_fails: list[tuple[str, str]] = []

    for subdir in targets:
        n_ch, n_p, n_f, fails = verify_book(subdir, only_chapter=args.chapter)
        total_chapters += n_ch
        total_pass += n_p
        total_fail += n_f
        all_fails.extend(fails)
        if not args.json:
            print(f"[{subdir}] chapters={n_ch} pass={n_p} fail={n_f}")

    if args.json:
        import json as _j
        # run_all.py-compatible JSON: each fail = one finding, severity
        # MALFORMED (Layer 1 — structural drift across the 4-layer alignment).
        findings = [
            {"verse": ch, "severity": "MALFORMED", "tag": "4-LAYER-DRIFT", "msg": msg}
            for ch, msg in all_fails
        ]
        print(_j.dumps({
            "summary": {
                "total_findings": total_fail,
                "by_severity": {"MALFORMED": total_fail} if total_fail else {},
                "by_tag": {"4-LAYER-DRIFT": total_fail} if total_fail else {},
            },
            "findings": findings,
        }))
        return 0

    if all_fails and not args.quiet:
        print()
        print("─── failures ─────────────────────────────────────────────────")
        for ch, msg in all_fails[:50]:
            print(f"  {ch}: {msg}")
        if len(all_fails) > 50:
            print(f"  ... and {len(all_fails) - 50} more")

    print()
    print(f"TOTAL: chapters={total_chapters} pass={total_pass} fail={total_fail}")
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
