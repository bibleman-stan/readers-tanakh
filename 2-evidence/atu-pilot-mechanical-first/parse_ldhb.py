#!/usr/bin/env python3
"""
parse_ldhb.py — extract LDHB SENTENCE/SUB-POINT/SUPPORT/COMPLEX units from
the bracketed markup format for use as a comparison reference (NOT a runtime
dependency — see methodology notes).

Strategy: each line beginning with one of the unit tags is a separate discourse
unit. We strip the embedded brackets (TM/TP/LD/RR/T/SP/!.../+.../›‹/″‶) and
extract just the Hebrew text, then optionally strip cantillation/vowels for
boundary alignment with other reference sequences.

Verse numbers appear embedded in the unit text (digits at the start of the
content after the unit-tag). We split unit text on a leading-digit pattern.

Output: one JSON line per unit:
  - tag: one of SENTENCE / SUB-POINT / SUPPORT / COMPLEX
  - verse: the verse number this unit belongs to (inherited from the most
    recent leading-digit number observed)
  - text: cleaned Hebrew text
  - consonants: text with all pointing/cantillation stripped
"""

from __future__ import annotations
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pilot_config as cfg

OUT_DIR = cfg.PILOT_DIR
IN_TXT = cfg.LDHB_TXT
OUT_JSONL = cfg.LDHB_UNITS_JSONL
OUT_TXT = cfg.LDHB_UNITS_TXT

# Recognized unit tags at line start.
# Set is extensible; see van der Merwe LDHB tag inventory.
UNIT_TAG_RE = re.compile(
    r"^(SENTENCE|SUB-POINT|SUPPORT|COMPLEX|PRINCIPLE|ELABORATION|BULLET)\s+(.*)$"
)

# Bracketed markup: TM]...[TM, TP]...[TP, LD]...[LD, RR]...[RR, T]...[T, SP]...[SP
# Plus paired ›‹, ″‶, !›‹!, +›‹+ etc.
# Strategy: strip the bracketed tags and decorations, leaving Hebrew text.

# Drop all marker characters: brackets, quotes, special markup
_DROP_CHARS_RE = re.compile(r"[\[\]›‹″‶!+|]")
# Drop tag fragments like TM, TP, LD, RR, T, SP between brackets — match
# 1-3 uppercase Latin letters preceded by space or start
_TAG_FRAG_RE = re.compile(r"\b(?:TM|TP|LD|RR|SP|T)\b")
# Drop trailing asterisks (footnote markers in the Lexham text)
_ASTERISK_RE = re.compile(r"\*")
# Leading verse number (e.g., "1" or "20" at start of line content)
_LEADING_NUMBER_RE = re.compile(r"^(\d+)\s*")

# Hebrew pointing range for consonant extraction
_POINTING_RE = re.compile(r"[֑-ׇ]")
_CONS_ONLY_RE = re.compile(r"[^א-ת]")


def strip_pointing(text: str) -> str:
    return _POINTING_RE.sub("", text)


def consonants_only(text: str) -> str:
    return _CONS_ONLY_RE.sub("", text)


def clean_line(content: str) -> tuple[int | None, str]:
    """Strip markup, return (leading_verse_num_if_present, cleaned_text)."""
    # Remove tag fragments first
    s = _TAG_FRAG_RE.sub("", content)
    # Remove bracketed markers and special chars
    s = _DROP_CHARS_RE.sub("", s)
    s = _ASTERISK_RE.sub("", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    # Extract leading verse number if present
    m = _LEADING_NUMBER_RE.match(s)
    verse_num = None
    if m:
        verse_num = int(m.group(1))
        s = s[m.end():].strip()
    return verse_num, s


def main() -> None:
    if not IN_TXT.exists():
        raise SystemExit(f"ERROR: LDHB markup not found at {IN_TXT}")

    units = []
    current_verse: int | None = None

    for raw_line in IN_TXT.read_text(encoding="utf-8").splitlines():
        raw_line = raw_line.rstrip()
        if not raw_line.strip():
            continue

        # Detect unit-tag prefix
        m = UNIT_TAG_RE.match(raw_line)
        if m:
            tag = m.group(1)
            content = m.group(2)
        else:
            # Lines without a unit tag (e.g., bare verse-number lines like "21..." in
            # the input file) — these are continuations of the previous verse's
            # last unit's namelist content. We absorb them as SENTENCE units
            # under their own verse number.
            tag = "SENTENCE"
            content = raw_line.strip()

        leading_verse, cleaned = clean_line(content)
        if leading_verse is not None:
            current_verse = leading_verse

        if not cleaned:
            continue

        units.append({
            "tag": tag,
            "verse": current_verse,
            "text": cleaned,
            "consonants": consonants_only(cleaned),
        })

    # Emit JSONL
    with OUT_JSONL.open("w", encoding="utf-8") as fp:
        for u in units:
            fp.write(json.dumps(u, ensure_ascii=False) + "\n")

    # Human-readable
    with OUT_TXT.open("w", encoding="utf-8") as fp:
        current_v = None
        for u in units:
            if u["verse"] != current_v:
                if current_v is not None:
                    fp.write("\n")
                fp.write(f"=== {cfg.VERSE_PREFIX}{u['verse']} ===\n")
                current_v = u["verse"]
            fp.write(f"  [{u['tag']:10s}] {u['text']}\n")

    print(f"Wrote: {OUT_JSONL}")
    print(f"Wrote: {OUT_TXT}")

    # Summary
    from collections import Counter
    tag_counter = Counter(u["tag"] for u in units)
    verse_counter = Counter(u["verse"] for u in units)
    print(f"\n--- Tag distribution ---")
    for t, c in tag_counter.most_common():
        print(f"  {t}: {c}")
    print(f"\n--- Units per verse ---")
    print("  " + ", ".join(f"v.{v}={n}" for v, n in sorted(verse_counter.items()) if v is not None))
    print(f"\nTotal LDHB units: {len(units)}")


if __name__ == "__main__":
    main()
