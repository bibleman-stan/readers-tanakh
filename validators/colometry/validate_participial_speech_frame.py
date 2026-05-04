#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Rule H5d — Participial Speech-Frame Split (REVIEW-REQUIRED).

H5d (canon §5 H5 family extension; Layer 3 editorial rule):
A line containing a predicative active participle of a speech root + optional
locative/recipient complements + a verbatim quoted-content predication
(imperative or finite verb starting a new clause) should split between the
ANNOUNCEMENT FRAME (subject + participle + verb-side complements) and the
QUOTED CONTENT.

  CANONICAL CASE — Isa 40:3:
    קוֹל קוֹרֵא בַּמִּדְבָּר פַּנּוּ דֶּרֶךְ יְהוָה
    →
    קוֹל קוֹרֵא בַּמִּדְבָּר          (announcement: subject + ptcp + locative)
    פַּנּוּ דֶּרֶךְ יְהוָה              (verbatim quote: imperative + DO)

  Stan-corrected reading 2026-05-04: locative `בַּמִּדְבָּר` is the locative of
  the speech-act verb (WHERE the calling is happening), bonded to the
  announcement frame per H18 (clause-nucleus integrity — verb + argument
  structure is one unit). The split goes at the predication boundary.

PATTERN DEFINITION (this validator's scope, conservative initial):
A line where, in TAHOT tag-confirmed order:
  1. A token bears tag `V<stem>r` (active participle, any verb stem)
     AND the bare-skel root matches a SPEECH_PARTICIPLE_ROOTS prefix
     (אמר, דבר, קרא, צעק, זעק).
  2. After that participle position (skipping verb-side complements like
     PPs and bare NPs), an imperative-verb token (V<stem>v aspect).

The split position is BEFORE the imperative.

FP GUARDS (suppress finding):
  - poetic register (Sifrei Emet skip)
  - subordinator before speech verb (אשר, כי, כאשר, לכן, על־כן, למען)
  - naming-construction (token after speech verb is שם/שמו/שמה/שמם)
  - לאמר on the same line (already H5 territory)
  - line starts with wayyiqtol (H5b territory)
  - כה immediately before participle (prophetic-formula territory)
  - both split halves must be ≥ 1 prosodic word (anti-trivial)

SEVERITY:
  REVIEW-REQUIRED only — initial deployment per 2026-05-04 audit verdict.
  Corpus footprint at first-pass design is narrow (~1-handful of confirmed
  TPs); STRONG-promotion gated on §7.4 ≥80%-on-≥5-instances threshold after
  canary review.

ARCHITECTURAL CONSTRAINT:
  Tag-driven (no te'amim glyph predicates). Skel fallback for root match
  only.

Output format:
    [DEVIATION]  file:line  H5d/participial-speech-frame  REVIEW-REQUIRED  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_participial_speech_frame.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_participial_speech_frame.py --book 23-isaiah
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_participial_speech_frame.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_participial_speech_frame.py --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "he"

sys.path.insert(0, str(REPO_ROOT / "validators"))
from _shared.poetic_register import is_poetic_register  # noqa: E402
from _shared import morph_alignment as MA  # noqa: E402

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers
# ---------------------------------------------------------------------------

SOF_PASUQ = "׃"     # U+05C3
MAQQEF = "־"        # U+05BE — preserve as structural separator (split target)
PASEQ = "׀"         # U+05C0
# Strip niqqud + te'amim (U+0591-U+05C7) but preserve maqqef (U+05BE),
# sof pasuq (U+05C3), paseq (U+05C0) — these are structural markers, not points.
HEBREW_POINTS_RE = re.compile(r"[֑-ֽֿ-ֿׁ-ׂׄ-ׇ]")

VERSE_REF_RE = re.compile(r"^(\S+\s+)?\d+:\d+\s*$")


def strip_points(token: str) -> str:
    return HEBREW_POINTS_RE.sub("", token)


def is_skippable(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    if VERSE_REF_RE.match(s):
        return True
    return False


def parse_verse_ref(line: str):
    s = line.strip()
    m = re.match(r"^(?:\S+\s+)?(\d+):(\d+)\s*$", s)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def book_name_from_path(path: Path) -> str:
    return path.parent.name


CHAPTER_FILENAME_RE = re.compile(r"-(\d+)\.txt$", re.IGNORECASE)


def chapter_from_path(path: Path) -> int | None:
    m = CHAPTER_FILENAME_RE.search(path.name)
    if not m:
        return None
    return int(m.group(1))


def content_tokens(line: str) -> list[str]:
    out = []
    for tok in line.split():
        bare = strip_points(tok)
        if bare in ("", SOF_PASUQ):
            continue
        if re.match(r"^\d+:\d+$", bare):
            continue
        out.append(tok)
    return out


def bare_skel(token: str) -> str:
    return strip_points(token).rstrip(SOF_PASUQ)


# ---------------------------------------------------------------------------
# H5d trigger constants
# ---------------------------------------------------------------------------

# Speech-participle FORMS (consonant skeletons of common active-participle
# forms of speech roots). Direct skeleton match — needed because many
# participles have mater-lectionis vav/yod in the surface form (קוֹרֵא →
# skel קורא, root only קרא).
SPEECH_PARTICIPLE_FORMS = frozenset({
    # אמר qal active participle: אֹמֵר / אֹמְרִים / אֹמֶרֶת — skel often retains aleph
    "אמר", "אמרי", "אמרים", "אמרת", "אמרות",
    "ואמר", "ואמרי", "ואמרים", "ואמרת",  # vav-prefixed
    # דבר piel active participle: מְדַבֵּר etc.
    "מדבר", "מדברי", "מדברים", "מדברת", "מדברות",
    "ומדבר", "ומדברי", "ומדברים",
    # דבר qal active participle (rare)
    "דבר", "דברי", "דברים", "דוברי", "דוברים",  # דֹּבֵר / דֹּבְרִי
    # קרא qal active participle: קוֹרֵא / קוֹרְאִים — vav as mater lectionis
    "קורא", "קוראי", "קוראים", "קראת", "קוראות",
    "וקורא", "וקוראים",
    # צעק qal active participle: צֹעֵק (vav as mater)
    "צעק", "צעקי", "צעקים", "צעקת", "צעקות",
    "צועק", "צועקי", "צועקים",  # with vav-mater
    # זעק qal active participle: זֹעֵק (vav as mater)
    "זעק", "זעקי", "זעקים", "זעקת", "זעקות",
    "זועק", "זועקי", "זועקים",  # with vav-mater
})

# Subordinators that disqualify (the speech verb is inside a sub-clause,
# the "quote" is the content of the sub-clause not a standalone announcement).
H5D_SUBORDINATORS = frozenset({
    "אשר", "כי", "כאשר", "לכן", "למען", "פן",
    "עלכן", "על־כן",  # על־כן with maqqef
})

# Naming-construction tokens (קרא + שם = "called the name", not "cried out").
H5D_NAMING_TOKENS = frozenset({
    "שם", "שמו", "שמה", "שמם", "שמן",
})

# Prophetic formula immediately before participle.
H5D_PROPHETIC_FORMULA = frozenset({"כה"})

# לאמר marker — H5 territory, not H5d.
H5D_LEEMOR_SKELS = frozenset({"לאמר", "לאמור"})


def _morpheme_chain(tag: str) -> list[str]:
    """Return morpheme chain stripped of language prefix (H/c)."""
    if not tag or tag == "[—]":
        return []
    # strip leading H, then split on /, then strip leading c from each
    s = tag.lstrip("H")
    return [m for m in s.split("/") if m]


def _has_active_participle(tag_chain: list[str]) -> bool:
    """True if any morpheme is V<stem>r (active participle)."""
    for m in tag_chain:
        ms = m.lstrip("Hc")
        if len(ms) >= 4 and ms[0] == "V" and ms[2] == "r":
            return True
    return False


def _has_imperative(tag_chain: list[str]) -> bool:
    """True if any morpheme is V<stem>v (imperative)."""
    for m in tag_chain:
        ms = m.lstrip("Hc")
        if len(ms) >= 4 and ms[0] == "V" and ms[2] == "v":
            return True
    return False


def compute_h5d_split(
    tokens: list[str],
    bare_tokens: list[str],
    tag_lists: list[list[str]] | None,
) -> tuple[int, str]:
    """Compute split position for H5d participial-speech-frame line.

    Returns (split_pos, mode) where:
      split_pos = 0 → no H5d split applies
      split_pos > 0 → token-index where to split (before the imperative)
      mode → "tag-confirmed" (REVIEW)
    """
    if tag_lists is None:
        return 0, ""
    if len(tokens) < 4:
        return 0, ""

    # Find first participle of speech root.
    ptcp_idx = -1
    for i, tag_list in enumerate(tag_lists):
        if not tag_list:
            continue
        chain_combined = []
        for tag in tag_list:
            chain_combined.extend(_morpheme_chain(tag))
        if not _has_active_participle(chain_combined):
            continue
        # Form match via skel: bare_tokens[i] in closed list of speech-participle
        # forms. Tag confirmed it's an active participle; the form-list confirms
        # the root is a speech root. Check both raw skel and vav-stripped form.
        bare = bare_tokens[i].split(MAQQEF, 1)[0]
        if bare in SPEECH_PARTICIPLE_FORMS or bare.lstrip("ו") in SPEECH_PARTICIPLE_FORMS:
            ptcp_idx = i
            break

    if ptcp_idx < 0:
        return 0, ""

    # FP guard: subordinator anywhere before participle. Check maqqef-bound
    # parts too (e.g., `אֵת אֲשֶׁר־יְהוָה אֹמֵר` Mic 6:1 — אשר is bound to יהוה
    # via maqqef but still functions as a relative-clause introducer).
    pre_ptcp = bare_tokens[:ptcp_idx]
    for t in pre_ptcp:
        for part in t.split(MAQQEF):
            if part in H5D_SUBORDINATORS:
                return 0, ""

    # FP guard: prophetic formula כה immediately before participle.
    # Also check maqqef-bound first part of last pre_ptcp token.
    if pre_ptcp:
        last_first_part = pre_ptcp[-1].split(MAQQEF, 1)[0]
        if last_first_part in H5D_PROPHETIC_FORMULA:
            return 0, ""

    # FP guard: לאמר anywhere on the line (H5 territory).
    if any(bare in H5D_LEEMOR_SKELS for bare in bare_tokens):
        return 0, ""

    # FP guard: token immediately AFTER participle is a naming-construction
    # token (קוֹרֵא שֵׁם = called the name, not crying-then-content).
    if ptcp_idx + 1 < len(bare_tokens):
        post = bare_tokens[ptcp_idx + 1].lstrip("ו").split(MAQQEF, 1)[0]
        if post in H5D_NAMING_TOKENS:
            return 0, ""

    # Find first imperative AFTER participle (skip verb-side complements).
    imp_idx = -1
    for j in range(ptcp_idx + 1, len(tokens)):
        if not tag_lists[j]:
            continue
        chain_combined = []
        for tag in tag_lists[j]:
            chain_combined.extend(_morpheme_chain(tag))
        if _has_imperative(chain_combined):
            imp_idx = j
            break

    if imp_idx < 0:
        return 0, ""

    # Anti-trivial guards: both halves ≥1 prosodic word.
    if imp_idx == 0 or imp_idx >= len(tokens):
        return 0, ""

    return imp_idx, "tag-confirmed"


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path) -> list[dict]:
    findings = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    book = book_name_from_path(path)
    chapter_from_file = chapter_from_path(path)

    chapter_morph = MA.load_chapter_morph(path)
    if chapter_morph is None:
        return findings  # tag-driven only

    # Build verse-context map: line_index → (chapter, verse)
    line_to_verse: dict[int, tuple[int | None, int | None]] = {}
    cur_chapter: int | None = None
    cur_verse: int | None = None
    for i, line in enumerate(lines):
        ref = parse_verse_ref(line)
        if ref is not None:
            cur_chapter, cur_verse = ref
        line_to_verse[i] = (cur_chapter, cur_verse)

    # Group content lines by verse for alignment.
    verse_lines_map: dict[tuple[int | None, int | None], list[tuple[int, str]]] = {}
    for i, line in enumerate(lines):
        if is_skippable(line):
            continue
        v_ctx = line_to_verse.get(i, (None, None))
        verse_lines_map.setdefault(v_ctx, []).append((i, line))

    # Per-verse alignment.
    verse_aligned_map: dict[tuple[int | None, int | None], list | None] = {}
    for v_key, idx_line_pairs in verse_lines_map.items():
        verse_num = v_key[1]
        if verse_num is None:
            verse_aligned_map[v_key] = None
            continue
        ortho_tags = chapter_morph.get(verse_num)
        if ortho_tags is None:
            verse_aligned_map[v_key] = None
            continue
        content_only = [ln for (_, ln) in idx_line_pairs]
        verse_aligned_map[v_key] = MA.align_verse_tokens_to_tags(content_only, ortho_tags)

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue
        v_ctx = line_to_verse.get(i, (None, None))
        chapter = v_ctx[0] if v_ctx[0] is not None else chapter_from_file
        verse = v_ctx[1]

        if chapter is not None and is_poetic_register(book, chapter, verse):
            continue

        toks = content_tokens(line)
        if len(toks) < 4:
            continue

        bare_tokens = [bare_skel(t) for t in toks]

        # Find the line's tag-list within the verse alignment.
        aligned = verse_aligned_map.get(v_ctx)
        if aligned is None:
            continue

        verse_idx_lines = verse_lines_map.get(v_ctx, [])
        line_pos = next(
            (pos for pos, (li, _) in enumerate(verse_idx_lines) if li == i),
            None,
        )
        if line_pos is None or line_pos >= len(aligned):
            continue
        line_tag_lists = aligned[line_pos]
        if not line_tag_lists:
            continue
        if len(line_tag_lists) != len(toks):
            continue  # alignment mismatch — skip

        split_pos, mode = compute_h5d_split(toks, bare_tokens, line_tag_lists)
        if split_pos == 0:
            continue

        line_no = i + 1
        announcement = " ".join(toks[:split_pos])
        quote_content = " ".join(toks[split_pos:])
        findings.append({
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "rule": "H5d/participial-speech-frame",
            "severity": "REVIEW-REQUIRED",
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "split_position": split_pos,
            "announcement": announcement,
            "quote_content": quote_content,
            "brief": (
                f"participial speech-frame at token {split_pos}: "
                f"`{announcement[:40]}...` // `{quote_content[:40]}...`"
            ),
        })

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--book", metavar="BOOK", help="Restrict to one book.")
    parser.add_argument("--v2", action="store_true", help="Scan v2/he.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    base_dir = V2_DIR if args.v2 else V1_DIR
    if not base_dir.exists():
        print(f"ERROR: {base_dir} not found.", file=sys.stderr)
        sys.exit(2)

    if args.book:
        book_dir = base_dir / args.book
        if not book_dir.exists():
            print(f"ERROR: book directory not found: {book_dir}", file=sys.stderr)
            sys.exit(2)
        files = sorted(book_dir.glob("*.txt"))
    else:
        files = sorted(base_dir.rglob("*.txt"))

    all_findings: list[dict] = []
    for path in files:
        all_findings.extend(scan_file(path))

    exit_code = 1 if all_findings else 0

    if args.json:
        findings_json = []
        for f in all_findings:
            findings_json.append({
                "file": f["file_rel"],
                "line": f["line_num"],
                "severity": "DEVIATION",
                "tag": f["severity"],
                "rule_id": "H5d",
                "rule": f["rule"],
                "rule_short": "participial speech-frame split",
                "book": f["book"],
                "chapter": f["chapter"],
                "verse": f["verse"],
                "brief": f["brief"],
                "announcement": f["announcement"],
                "quote_content": f["quote_content"],
                "applied_action": None,  # REVIEW-REQUIRED — no auto-apply
            })
        doc = {
            "validator": "validate_participial_speech_frame",
            "rule": "H5d",
            "version": "1.0.0",
            "layer": 3,
            "book": args.book or "all",
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": findings_json,
            "summary": {
                "total_findings": len(findings_json),
                "by_severity": {"REVIEW-REQUIRED": len(findings_json)},
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    print("=" * 72)
    print(f"Rule H5d Participial Speech-Frame Split validator")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Findings      : {len(all_findings)}")
    print()
    for f in all_findings:
        print(
            f"[DEVIATION]  {f['file_rel']}:{f['line_num']}  {f['rule']}  "
            f"{f['severity']}  {f['brief']}"
        )
        print(f"    Announcement: {f['announcement']}")
        print(f"    Quote:        {f['quote_content']}")
        print()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
