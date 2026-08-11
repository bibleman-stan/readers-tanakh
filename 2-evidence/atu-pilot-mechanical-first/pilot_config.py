"""
pilot_config.py — single source of truth for the chapter under pilot.

To switch chapters: edit the CHAPTER block below; all scripts will follow.
"""

from pathlib import Path

# === CURRENT CHAPTER ===

# BHSA-side names (used by Text-Fabric queries)
BOOK_NAME = "Leviticus"
CHAPTER_NUM = 11

# Tanakh-repo-side names (used for reading v0 layer files)
BOOK_FOLDER = "03-leviticus"   # subdir under data/text-files/v0/...
BOOK_FILE_STEM = "leviticus-11"  # filename stem (no .txt)

# Human-readable labels (titles, headings, log output)
CHAPTER_DISPLAY = "Leviticus 11"
VERSE_PREFIX = "11:"           # used in v0 layer files as "11:1" verse markers

# Output stem (filenames in pilot dir)
OUT_STEM = "leviticus-11"

# === PATHS (derived from above) ===

TANAKH = Path(r"C:\Users\bibleman\repos\readers-tanakh")
PILOT_DIR = TANAKH / "research/atu-pilot-mechanical-first"

# v0 layer inputs (verse-level base layers in the tanakh repo)
HE_PATH       = TANAKH / f"data/text-files/v0/prose/{BOOK_FOLDER}/{BOOK_FILE_STEM}.txt"
TRANSLIT_PATH = TANAKH / f"data/text-files/v0/translit-baseline/{BOOK_FOLDER}/{BOOK_FILE_STEM}.txt"
ENG_PATH      = TANAKH / f"data/text-files/v2/eng-kjv/{BOOK_FOLDER}/{BOOK_FILE_STEM}.txt"

# Pilot artifacts (chapter-suffixed for parallel chapters)
COLD_EYE_DOCX       = PILOT_DIR / f"{OUT_STEM}-cold-eye-baseline.docx"
COLD_EYE_EXTRACTED  = PILOT_DIR / f"{OUT_STEM}-cold-eye-baseline-EXTRACTED.txt"
PRINCIPLED_TXT      = PILOT_DIR / f"{OUT_STEM}-principled-baseline.txt"

V1_JSONL   = PILOT_DIR / f"v1_clauses_{OUT_STEM}.jsonl"
V1_TXT     = PILOT_DIR / f"v1_clauses_{OUT_STEM}.txt"
V1_5_JSONL = PILOT_DIR / f"v1_5_groups_{OUT_STEM}.jsonl"
V1_5_TXT   = PILOT_DIR / f"v1_5_groups_{OUT_STEM}.txt"

V3_MD    = PILOT_DIR / f"v3_three_way_report_{OUT_STEM}.md"
V3_JSONL = PILOT_DIR / f"v3_three_way_per_verse_{OUT_STEM}.jsonl"

LDHB_TXT          = PILOT_DIR / f"ldhb_{OUT_STEM}.txt"
LDHB_UNITS_JSONL  = PILOT_DIR / f"ldhb_units_{OUT_STEM}.jsonl"
LDHB_UNITS_TXT    = PILOT_DIR / f"ldhb_units_{OUT_STEM}.txt"

# Verse header regex pattern (matches "1:1" for Psalm 1, "22:1" for Gen 22, etc.)
import re
VERSE_HEADER_RE = re.compile(rf"^{re.escape(VERSE_PREFIX)}(\d+)\s*$")
