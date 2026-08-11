

def _find_repo_root():
    """Repo root by MARKER, not by counting parents.

    Counting encodes this file's depth in the tree, so moving the file silently
    breaks it and no text-based check notices. Anchoring on .git survives any
    move. Added 2026-08-10 after a reorg broke three different counted idioms.
    """
    from pathlib import Path as _P
    _here = _P(__file__).resolve()
    for _p in _here.parents:
        if (_p / ".git").exists():
            return _p
    return _here.parent

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate 1-method/canon Rule H5d — Participial Speech-Frame Split.

H5d (1-method/canon §5 H5 family extension; Layer 3 editorial rule):
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

PATTERN DEFINITION (IR-driven; post-2026-05-05 Macula pivot):
A line where, in IR-confirmed order:
  1. A token has `is_active_participle == True` AND `lemma in SPEECH_LEMMAS`.
  2. After that participle position (skipping verb-side complements),
     an `is_imperative == True` token.

The split position is BEFORE the imperative.

FP GUARDS (suppress finding):
  - poetic register (Sifrei Emet skip)
  - participle is inside a relative clause (`Constituent.ancestor_with(wg_class="relp")`)
  - subordinator before speech verb (אֲשֶׁר, כִּי, כַּאֲשֶׁר, לָכֵן, לְמַעַן, פֶּן)
  - naming-construction (token after participle has `lemma == "שֵׁם"`)
  - לאמר on the same line (already H5 territory) — detected as inf-construct
    of אָמַר
  - כה immediately before participle (prophetic-formula territory)
  - both split halves must be ≥ 1 prosodic word (anti-trivial)

SEVERITY CLASSIFICATION:
  STRONG-SPLIT-CANDIDATE — all three STRONG conditions met:
    (a) announcement side ≥ 2 tokens (subject + participle, not bare participle alone)
    (b) no woe-formula (הוֹי) immediately before the participle
    (c) no אֵין immediately before the participle (אֵין + participle is an
        idiomatic "there is none saying X" construction, not a speech frame)
    (d) no finite speech-verb (וַיֹּאמֶר / וַיְדַבֵּר) present earlier on the
        same line (guards quotation-within-quotation nesting)

  REVIEW-REQUIRED — any STRONG condition fails; borderline or embedded case.

POST-PIVOT NOTES:
  Replaces TAHOT morpheme-chain walking (`_morpheme_chain` / `_has_active_participle`
  / `_has_imperative`) with declarative IR Token predicates. Replaces the
  closed-list `SPEECH_PARTICIPLE_FORMS` skel set with lemma-based detection
  (robust to mater-lectionis and orthographic variants the form list missed).
  Replaces hand-built subordinator-via-maqqef-split logic with IR's
  `Constituent.ancestor_with(wg_class="relp")` (catches nested cases the
  skel-walk couldn't).

Output format:
    [DEVIATION]  file:line  H5d/participial-speech-frame  STRONG-SPLIT-CANDIDATE  brief
    [DEVIATION]  file:line  H5d/participial-speech-frame  REVIEW-REQUIRED          brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_participial_speech_frame.py
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_participial_speech_frame.py --book 23-isaiah
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_participial_speech_frame.py --v2
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_participial_speech_frame.py --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
REPO_ROOT = _find_repo_root()
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files"  / "v2" / "heb"

sys.path.insert(0, str(REPO_ROOT / "5-machinery/validators"))
from _shared.poetic_register import is_poetic_register  # noqa: E402
from _shared import macula_constituents as MC  # noqa: E402

# ---------------------------------------------------------------------------
# H5d trigger constants — lemma-based (post-IR-pivot)
# ---------------------------------------------------------------------------

# Speech-root lemmas (replaces SPEECH_PARTICIPLE_FORMS skel set). Matched
# against Token.lemma when Token.is_active_participle is True.
SPEECH_LEMMAS = frozenset({
    "אָמַר",   # say
    "דָּבַר",  # speak
    "קָרָא",   # call / cry out
    "צָעַק",   # cry out
    "זָעַק",   # cry out
})

# Subordinator lemmas — if any of these precedes the participle on the same
# line, the speech verb is inside a sub-clause (the "quote" is the content
# of that sub-clause, not a standalone announcement).
H5D_SUBORDINATOR_LEMMAS = frozenset({
    "אֲשֶׁר", "כִּי", "כַּאֲשֶׁר", "לָכֵן", "לְמַעַן", "פֶּן", "עַל־כֵּן",
})

# Naming-construction: קרא + שם = "called the name", not "cried out".
H5D_NAMING_LEMMAS = frozenset({"שֵׁם"})

# Prophetic formula immediately before participle.
H5D_PROPHETIC_FORMULA_LEMMAS = frozenset({"כֹּה"})

# Woe-formula token — הוֹי immediately before participle downgrades to
# REVIEW-REQUIRED (the participle is attributive in a woe-oracle address,
# not a standalone predicative announcement frame).
H5D_WOE_LEMMAS = frozenset({"הֽוֹי", "הוֹי", "אוֹי"})

# אֵין immediately before participle — idiomatic "there is none saying X"
# (existential negation + participle), not a speech-announcement frame;
# splitting would be destructive to the idiom.
H5D_EXISTENTIAL_NEG_LEMMAS = frozenset({"אַיִן", "אֵין"})

# Finite speech-verb lemmas — if one of these appears BEFORE the participle
# on the same line (as a wayyiqtol / qatal quotation introducer), the
# participle is embedded inside a quotation-within-quotation.  Downgrade to
# REVIEW-REQUIRED.
H5D_FINITE_SPEECH_LEMMAS = frozenset({
    "אָמַר",   # וַיֹּאמֶר / וַתֹּאמֶר / יֹּאמֶר etc.
    "דָּבַר",  # וַיְדַבֵּר etc.
})

# ---------------------------------------------------------------------------
# Sense-line / verse parsing helpers
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


# ---------------------------------------------------------------------------
# IR-driven detection
# ---------------------------------------------------------------------------

def line_has_leemor(tokens: list["MC.Token"]) -> bool:
    """True if any token is an inf-construct of אָמַר (= לֵאמֹר construction).

    The לֵ prefix (preposition) and the inf-construct are separate tokens
    in lowfat; the inf-construct itself carries lemma 'אָמַר' + type
    'infinitive construct'.
    """
    for t in tokens:
        if t.lemma == "אָמַר" and t.is_infinitive_construct:
            return True
    return False


def participle_is_in_relative_clause(participle: "MC.Token") -> bool:
    """True if the participle's enclosing constituent tree includes a
    relative-clause ancestor (wg_class='relp' or wg_rule='relCL').

    Catches nested cases that the prior skel-token-walk's maqqef-split
    subordinator detection couldn't see — e.g., אֵת אֲשֶׁר־יְהוָה אֹמֵר where
    the participle אֹמֵר is inside the relative clause headed by אֲשֶׁר.
    """
    cur = participle.parent_constituent
    while cur is not None:
        if cur.is_relative_clause:
            return True
        cur = cur.parent
    return False


def compute_h5d_split(tokens: list["MC.Token"]) -> tuple[int, str, str, "MC.Token | None", "MC.Token | None"]:
    """Compute split position for H5d participial-speech-frame line.

    Returns (split_pos, mode, severity, participle, imperative) where:
      split_pos = 0 → no H5d split applies
      split_pos > 0 → token-INDEX (within `tokens`) before which to split
                      (i.e., tokens[:split_pos] = announcement,
                             tokens[split_pos:] = quoted content)
      mode → "ir-driven"
      severity → "STRONG-SPLIT-CANDIDATE" or "REVIEW-REQUIRED"
      participle, imperative → the trigger tokens, for diagnostics
    """
    if len(tokens) < 4:
        return 0, "", "", None, None

    # 1) Find first active participle of a speech root.
    ptcp_idx = -1
    participle: MC.Token | None = None
    for i, t in enumerate(tokens):
        if t.is_active_participle and t.lemma in SPEECH_LEMMAS:
            ptcp_idx = i
            participle = t
            break
    if ptcp_idx < 0 or participle is None:
        return 0, "", "", None, None

    # 2) FP guard: participle is inside a relative clause.
    if participle_is_in_relative_clause(participle):
        return 0, "", "", None, None

    # 3) FP guard: subordinator lemma anywhere before the participle.
    pre_ptcp = tokens[:ptcp_idx]
    if any(t.lemma in H5D_SUBORDINATOR_LEMMAS for t in pre_ptcp):
        return 0, "", "", None, None

    # 4) FP guard: prophetic formula כֹּה immediately before the participle.
    if pre_ptcp and pre_ptcp[-1].lemma in H5D_PROPHETIC_FORMULA_LEMMAS:
        return 0, "", "", None, None

    # 5) FP guard: לאמר marker on the line (already H5 territory).
    if line_has_leemor(tokens):
        return 0, "", "", None, None

    # 6) FP guard: token immediately AFTER participle is a naming-construction
    #    token (קוֹרֵא שֵׁם = called the name, not crying-then-content).
    if ptcp_idx + 1 < len(tokens):
        next_tok = tokens[ptcp_idx + 1]
        if next_tok.lemma in H5D_NAMING_LEMMAS:
            return 0, "", "", None, None

    # 7) Find first imperative AFTER the participle.
    imp_idx = -1
    imperative: MC.Token | None = None
    for j in range(ptcp_idx + 1, len(tokens)):
        if tokens[j].is_imperative:
            imp_idx = j
            imperative = tokens[j]
            break
    if imp_idx < 0 or imperative is None:
        return 0, "", "", None, None

    # 8) Anti-trivial: both halves ≥1 token. (imp_idx > 0 by construction; just
    #    confirm the announcement side is non-empty after the participle.)
    if imp_idx == 0 or imp_idx >= len(tokens):
        return 0, "", "", None, None

    # -----------------------------------------------------------------------
    # SEVERITY CLASSIFICATION
    # STRONG-SPLIT-CANDIDATE when ALL four conditions are satisfied; otherwise
    # REVIEW-REQUIRED.
    # -----------------------------------------------------------------------
    strong = True

    # STRONG condition (a): announcement side must have ≥ 2 tokens (subject +
    # participle minimum).  A bare single-token announcement (e.g. the
    # participle alone) is a less clear-cut predication boundary.
    if imp_idx < 2:
        strong = False

    # STRONG condition (b): woe-formula (הוֹי/אוֹי) immediately before the
    # participle → attributive-in-woe-oracle, not standalone announcement.
    if strong and pre_ptcp and pre_ptcp[-1].lemma in H5D_WOE_LEMMAS:
        strong = False

    # STRONG condition (b2): definite article (הַ/הָ, lemma הַ) immediately
    # before the participle AND a content noun earlier in pre_ptcp → article-
    # marked attributive use (e.g. יְהוָה הָאֹמֵר אֵלַי "YHWH the-one-saying
    # to me"), not a predicative announcement frame.
    # Distinguish from the nominalizer case: הָאֹמְרִים "those-who-say" where
    # the article+ptcp IS the subject (no prior head noun on the line).
    # Note: lowfat encodes the article as pos="particle" + lemma="הַ".
    if strong and pre_ptcp and pre_ptcp[-1].lemma == "הַ":
        # If there is a content noun (noun/pronoun) before the article, the
        # participle is attributive to that noun → REVIEW-REQUIRED.
        has_prior_head = any(
            t.pos in ("noun", "pronoun")
            for t in pre_ptcp[:-1]  # exclude the article token itself
        )
        if has_prior_head:
            strong = False

    # STRONG condition (c): existential negation (אֵין) immediately before
    # the participle → idiomatic "there is none saying X", not a frame.
    if strong and pre_ptcp and pre_ptcp[-1].lemma in H5D_EXISTENTIAL_NEG_LEMMAS:
        strong = False

    # STRONG condition (d): finite speech-verb earlier on the line → the
    # participle is embedded inside a quotation-within-quotation.
    if strong and any(
        (t.lemma in H5D_FINITE_SPEECH_LEMMAS and not t.is_active_participle)
        for t in pre_ptcp
    ):
        strong = False

    severity = "STRONG-SPLIT-CANDIDATE" if strong else "REVIEW-REQUIRED"
    return imp_idx, "ir-driven", severity, participle, imperative


# ---------------------------------------------------------------------------
# Sense-line position-mapping
#
# We need to map IR-detected split-position (which is a TOKEN INDEX within
# the verse's flat token list) back to a SENSE-LINE INDEX in the v2/heb file
# (which is what an editor reads). The trigger fires when an editorial
# sense-line spans BOTH the participle and the imperative — i.e., the split
# would happen WITHIN a single sense-line.
# ---------------------------------------------------------------------------

def sense_line_for_token(token: "MC.Token",
                         line_to_tokens: dict[int, list["MC.Token"]]) -> int | None:
    """Return the line-index containing the given token, or None if not found."""
    for line_idx, line_toks in line_to_tokens.items():
        if any(t.xml_id == token.xml_id for t in line_toks):
            return line_idx
    return None


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

def _partition_into_verses(lines: list[str]) -> list[tuple[int | None, int | None, list[int]]]:
    """Group line indices by verse. Returns [(chapter, verse, [line_indices]), ...]."""
    out: list[tuple[int | None, int | None, list[int]]] = []
    cur_ch: int | None = None
    cur_vs: int | None = None
    cur_idx: list[int] = []
    for i, line in enumerate(lines):
        ref = parse_verse_ref(line)
        if ref is not None:
            if cur_idx:
                out.append((cur_ch, cur_vs, cur_idx))
            cur_ch, cur_vs = ref
            cur_idx = []
            continue
        if not line.strip():
            continue
        cur_idx.append(i)
    if cur_idx:
        out.append((cur_ch, cur_vs, cur_idx))
    return out


def scan_file(path: Path) -> list[dict]:
    """IR-driven scan: per verse, look for the H5d announcement/quote split
    pattern within a SINGLE sense-line."""
    findings: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    book_slug = book_name_from_path(path)
    chapter_from_file = chapter_from_path(path)
    verses = _partition_into_verses(lines)

    for ch, vs, indices in verses:
        if ch is None or vs is None:
            continue

        # NOTE: poetic-register skip removed (methodology fix).
        # is_poetic_register() was used as overlay-as-authorization: it suppressed
        # all verses in Sifrei Emet / embedded-poetry chapters, treating register
        # as a license to skip rather than as a calibration signal. Active-participle
        # speech-frames (e.g. הָאֹמֵר) appear in poetry and produce real SPLIT
        # candidates governed by the same three editorial criteria (atomic thought,
        # single image, Hebrew syntax). Register is evidence, not a skip gate.

        # Pull lowfat verse tokens.
        try:
            verse_tokens = MC.get_verse_tokens(book_slug, ch, vs)
        except (FileNotFoundError, ValueError, KeyError):
            continue
        if not verse_tokens:
            continue

        # Greedy-align each sense-line to the verse's tokens, building a
        # per-line token list.
        sense_indices = [i for i in indices if not is_skippable(lines[i])]
        line_to_tokens: dict[int, list["MC.Token"]] = {}
        cursor = 0
        for idx in sense_indices:
            matched, cursor = MC.match_sense_line_tokens(
                verse_tokens, lines[idx], start_idx=cursor)
            line_to_tokens[idx] = matched

        # Per sense-line: run H5d detection on its IR tokens.
        for line_idx, line_tokens in line_to_tokens.items():
            if len(line_tokens) < 4:
                continue
            split_pos, mode, severity, participle, imperative = compute_h5d_split(line_tokens)
            if split_pos == 0 or participle is None or imperative is None:
                continue

            # Verify the participle and imperative are BOTH on this sense-line
            # (they will be by construction since compute_h5d_split walked
            # only line_tokens, but defensive — and confirms a within-line
            # split would change the file, not a no-op cross-line case).
            ptcp_line = sense_line_for_token(participle, line_to_tokens)
            imp_line = sense_line_for_token(imperative, line_to_tokens)
            if ptcp_line != line_idx or imp_line != line_idx:
                continue

            line_no = line_idx + 1
            announcement_tokens = line_tokens[:split_pos]
            quote_tokens = line_tokens[split_pos:]
            announcement = " ".join(t.text for t in announcement_tokens if t.text)
            quote_content = " ".join(t.text for t in quote_tokens if t.text)

            findings.append({
                "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "line_num": line_no,
                "rule": "H5d/participial-speech-frame",
                "severity": severity,
                "book": book_slug,
                "chapter": ch,
                "verse": vs,
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
    parser.add_argument("--v2", action="store_true", help="Scan v2/heb.")
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
                "applied_action": None,  # STRONG → split candidate; no auto-apply yet
            })
        n_strong = sum(1 for f in all_findings if f["severity"] == "STRONG-SPLIT-CANDIDATE")
        n_review = sum(1 for f in all_findings if f["severity"] == "REVIEW-REQUIRED")
        doc = {
            "validator": "validate_participial_speech_frame",
            "rule": "H5d",
            "version": "2.1.0-ir",
            "layer": 3,
            "book": args.book or "all",
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": findings_json,
            "summary": {
                "total_findings": len(findings_json),
                "by_severity": {
                    "STRONG-SPLIT-CANDIDATE": n_strong,
                    "REVIEW-REQUIRED": n_review,
                },
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    n_strong = sum(1 for f in all_findings if f["severity"] == "STRONG-SPLIT-CANDIDATE")
    n_review = sum(1 for f in all_findings if f["severity"] == "REVIEW-REQUIRED")
    print("=" * 72)
    print(f"Rule H5d Participial Speech-Frame Split validator (IR-driven)")
    print("=" * 72)
    print(f"Files scanned         : {len(files)}")
    print(f"Findings              : {len(all_findings)}")
    print(f"  STRONG-SPLIT-CANDIDATE : {n_strong}")
    print(f"  REVIEW-REQUIRED        : {n_review}")
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
