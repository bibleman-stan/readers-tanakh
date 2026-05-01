#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Rule H2 — Construct Chain Default.

Rule H2 (canon §5 H2; Joüon-Muraoka §129; Waltke-O'Connor §9):
A construct chain (nomen regens in construct state + nomen rectum) is a single
bound noun phrase. No line break may occur inside an unmodified construct chain.

  STRONG-MERGE-CANDIDATE: a construct chain whose nomen regens appears at line
  end and whose nomen rectum (the following word) appears at the start of the
  next line, with no intervening modifier.

  REVIEW-REQUIRED: cases where an intervening element may be present, or the
  detection confidence is lower (e.g., chain with article on rectum might have
  an adjective intervening on the regens — judgment needed).

Detection strategy:
  The Masoretic Text marks construct state morphologically (primarily by vowel
  change) and graphically via maqqef for tightly-bound pairs. Two sub-cases:

  Sub-case 1 — MAQQEF-JOINED at line end:
    The nomen regens ends with a maqqef (word-final ־), meaning the regens and
    its rectum are graphically joined. A line ending in a maqqef-joined token
    is already caught by validate_line_final_tokens.py (Rule H1). This validator
    focuses on the NON-maqqef-joined case.

  Sub-case 2 — NON-MAQQEF construct chain split:
    No maqqef joins the tokens, but the regens is in construct state. This is
    harder to detect without full morphological parsing. We use two heuristics:

    (a) DEFINITE-ARTICLE RECTUM HEURISTIC:
        A line ends with a token (call it T), and the next line begins with a
        token starting with הַ/הָ/הֶ (definite article), suggesting T is the
        regens and the article-bearing word is the rectum. Hebrew construct
        chains frequently appear as BARE_REGENS + ARTICULATED_RECTUM (the
        article licenses the specificity of the whole chain but attaches to
        the rectum, not the regens — Joüon-Muraoka §137).
        Confidence: STRONG if T does not end a complete clause (no sof pasuq
        or major disjunctive accent visible in stripped form).

    (b) DIVINE NAME COMPOUND HEURISTIC:
        Line ends with יְהוָה / יהוה (Tetragrammaton consonantal skeleton יהוה)
        and the next line begins with a word that commonly follows YHWH in
        compound divine names (צְבָאוֹת, אֱלֹהִים, אֱלֹהֵי, אֱלֹהֵינוּ, etc.).
        These compounds are frozen formulae (hebrew-break-legality.md row 7).
        Flag as STRONG-MERGE-CANDIDATE.

    (c) COMMON CONSTRUCT REGENS ENDINGS:
        Hebrew construct state often involves final-syllable reduction. Many
        common nouns have distinctive construct-state forms. A closed list of
        frequently-occurring construct-state endings provides a third heuristic.
        Confidence lower — flag as REVIEW-REQUIRED.

Limitation: Full construct-chain detection requires morphological parsing
(BHSA-style tagging or Hebrew morpheme analyzer). This validator operates on
surface forms with heuristics. False positives are expected for:
  - Nouns that look like construct forms but are absolute state.
  - Clause-final absolute nouns followed by a new clause beginning with הַ.

The REVIEW-REQUIRED tag is appropriate for these cases.

Output format:
    [DEVIATION]  file:line_number  H2/construct  SEVERITY  brief description

Where SEVERITY is:
    STRONG-MERGE-CANDIDATE  — high-confidence unmodified construct chain split
    REVIEW-REQUIRED         — lower confidence; editorial check required

JSON subcase field — distinguishes the three detection heuristics so
downstream orchestrators (e.g., apply_validators.py) can adopt individual
subcases independently without adopting all H2 findings:

    "divine_name"            — Heuristic (b). Line ends with a divine-name
                               skeleton (יהוה, אדני, אל, אלהים) and the next
                               line begins with a recognized compound follower
                               (צבאות, אלהים, אלהי, etc.). Frozen formula per
                               hebrew-break-legality.md row 7.
                               Severity: STRONG-MERGE-CANDIDATE.

    "article_rectum"         — Heuristic (a). Line ends with an unarticulated
                               token (possible nomen regens) and the next line
                               begins with הַ/הָ/הֶ (definite article on rectum).
                               Severity: REVIEW-REQUIRED.

    "common_construct_ending" — Heuristic (c). Line ends with a token whose
                               bare form matches a closed list of high-frequency
                               construct-state forms, and the next-line first
                               token is not an article, conjunction, or particle.
                               Severity: REVIEW-REQUIRED.

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
# Shared morphology + morph-alignment helpers
# ---------------------------------------------------------------------------
# Make _shared importable when this script is run as __main__.
sys.path.insert(0, str(REPO_ROOT / "validators"))
from _shared import morphology as M  # noqa: E402
from _shared import morph_alignment as MA  # noqa: E402

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers
# ---------------------------------------------------------------------------

MAQQEF = "־"  # U+05BE

# Hebrew points: U+0591–U+05C7
HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")

# Sof pasuq U+05C3 (׃) — verse-end marker; signals no cross-line chain here
SOF_PASUQ = "׃"


def strip_points(token: str) -> str:
    """Return token with niqqud and te'amim stripped."""
    return HEBREW_POINTS_RE.sub("", token)


def has_sof_pasuq(token: str) -> bool:
    """Return True if the token contains the sof pasuq (verse-end) mark."""
    return SOF_PASUQ in token


# ---------------------------------------------------------------------------
# Heuristic data
# ---------------------------------------------------------------------------

# Wayyiqtol speech-verb skeletons — lines ending with one of these are speech
# introductions; the next line begins speech content (often starting with ה on
# an adverb like הֵיטֵב or a quotation opener).  Do NOT apply the
# article-rectum heuristic when the current line ends with a speech verb,
# because the ה on the next line is NOT a construct rectum — it opens speech.
SPEECH_VERB_SKELETONS = {
    "ויאמר",   # וַיֹּאמֶר — and he said
    "ויאמרו",  # וַיֹּאמְרוּ — and they said
    "ותאמר",   # וַתֹּאמֶר — and she said
    "וידבר",   # וַיְדַבֵּר — and he spoke
    "ויען",    # וַיַּעַן — and he answered
    "ויענו",   # וַיַּעֲנוּ — and they answered
    "ויקרא",   # וַיִּקְרָא — and he called/cried out (can introduce speech)
    "ויצו",    # וַיְצַו — and he commanded
    "ויצוו",   # וַיְצַוּוּ — and they commanded
    "ויבשר",   # וַיְבַשֵּׂר — and he announced
}

# Divine name consonant skeletons — these form frozen compounds
DIVINE_NAME_SKELETONS = {
    "יהוה",   # Tetragrammaton
    "אדני",   # Adonai (also written as perpetual qere)
    "אל",     # El
    "אלהים",  # Elohim
}

# Common words that follow the Tetragrammaton to form compound divine names
# (hebrew-break-legality.md row 7 — frozen formulae, REQUIRED-MERGE)
YHWH_COMPOUND_FOLLOWERS = {
    "צבאות",   # Sabaoth (צְבָאוֹת)
    "אלהים",   # Elohim (אֱלֹהִים)
    "אלהי",    # construct of Elohim (אֱלֹהֵי)
    "אלהינו",  # our God (אֱלֹהֵינוּ)
    "אלהיך",   # your God (אֱלֹהֶיךָ)
    "אלהיכם",  # your God pl (אֱלֹהֵיכֶם)
    "אלהיהם",  # their God (אֱלֹהֵיהֶם)
    "אלהיו",   # his God (אֱלֹהָיו)
}

# Hebrew definite article consonant (after stripping points, any ה followed
# by a dagesh in the following consonant). Surface detection: first letter is ה
# and it is the article (not he-directional, not ה pronominal suffix).
# We approximate: next-line first bare token starts with ה and is NOT a
# standalone word (i.e., it's attached to a content word via the article).
# Confidence-raising factor: regens does NOT end with ה (avoids he-directional
# false positives on regens side).

# Common construct-state noun endings (consonant skeletons, stripped of points).
# These are forms that very commonly appear in construct state in biblical Hebrew.
# NOT exhaustive — just high-frequency patterns to catch common cases.
# False positives possible; flag as REVIEW-REQUIRED.
COMMON_CONSTRUCT_ENDINGS = {
    "בית",    # בֵּית — construct of בַּיִת (house of)
    "בן",     # בֶּן — construct of בֵּן (son of)
    "בני",    # בְּנֵי — construct of בָּנִים (sons of)
    "בת",     # בַּת — construct of בַּת (daughter of)
    "דבר",    # דְּבַר — construct of דָּבָר (word/matter of)
    "עיר",    # עִיר — less predictable, but frequent in urban contexts
    "ספר",    # סֵפֶר — book of
    "מלך",    # מֶלֶךְ — king of (construct of מֶלֶךְ)
    "ארץ",    # אֶרֶץ — land of
    "עם",     # עַם — people of
    "יום",    # יוֹם — day of
    "שם",     # שֵׁם — name of
    "קול",    # קוֹל — voice of
    "ראש",    # רֹאשׁ — head of / beginning of
    "פני",    # פְּנֵי — face of (very common construct)
    "כל",     # כָּל — all of (construct)
    "בנות",   # בְּנוֹת — daughters of
    "ממלכת",  # מַמְלֶכֶת — kingdom of
    "עבד",    # עֶבֶד — servant of
    "מעי",    # מֵעֵי — entrails of (Jonah 2:2)
    "אנשי",   # אַנְשֵׁי — men of
    "לב",     # לֵב — heart of
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_skippable(line: str) -> bool:
    """Return True for blank lines and verse-reference-only lines."""
    s = line.strip()
    if not s:
        return True
    if re.match(r"^(\w+\s+)?\d+:\d+$", s):
        return True
    return False


def first_bare_token(line: str):
    """Return the stripped first token of a line, or None if empty."""
    tokens = line.split()
    if not tokens:
        return None
    return strip_points(tokens[0])


def starts_with_article(bare_token: str) -> bool:
    """Heuristic: does this bare token (no points) start with ה in article position?

    We check if the token starts with ה and has length > 1 (not standalone ה).
    This catches הַמֶּלֶךְ → המלך, הַדָּגָה → הדגה, etc.
    False positives: he-directional (הָאָרֶץ as locative) and demonstratives.
    Acceptable false-positive rate for REVIEW-REQUIRED flagging.
    """
    if not bare_token:
        return False
    return bare_token.startswith("ה") and len(bare_token) > 1


# ---------------------------------------------------------------------------
# Verse-grouping helper
# ---------------------------------------------------------------------------

_VERSE_REF_RE = re.compile(r"^\d+:\d+\s*$")


def _partition_into_verses(lines: list[str]) -> list[tuple[int, int, list[tuple[int, str]]]]:
    """Partition a list of file lines into per-verse groups.

    Returns list of (verse_num, [(line_no_1based, line_text), ...]) tuples,
    where verse_num is the verse integer from the chapter:verse header.
    Lines that precede any verse header are discarded (blank preamble only).
    """
    groups: list[tuple[int, list[tuple[int, str]]]] = []
    cur_verse: int | None = None
    cur_lines: list[tuple[int, str]] = []
    for i, raw in enumerate(lines):
        line_no = i + 1
        s = raw.strip()
        m = _VERSE_REF_RE.match(s)
        if m:
            if cur_verse is not None and cur_lines:
                groups.append((cur_verse, cur_lines))
            cur_verse = int(s.split(":")[1])
            cur_lines = []
        elif s and cur_verse is not None:
            cur_lines.append((line_no, raw))
    if cur_verse is not None and cur_lines:
        groups.append((cur_verse, cur_lines))
    return groups


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    """Scan one text file for Rule H2 construct-chain split violations.

    Uses TAHOT morph tags (via morph_alignment) when available to classify
    the last token of each content line as a construct-state head.  Falls
    back to the closed-list skel-heuristics when tags are missing or the
    verse alignment fails.
    """
    violations = []
    try:
        raw_text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw_text = path.read_text(encoding="utf-8-sig")

    all_lines = raw_text.splitlines()

    # Load TAHOT morph alignment for this chapter (None if v0/morph file absent).
    chapter_morph = MA.load_chapter_morph(path)

    # Group file lines into per-verse buckets.
    verse_groups = _partition_into_verses(all_lines)

    # Build a flat list of (line_no, line_text, verse_num) for cross-line
    # navigation within a verse (we need prev/next line across verse groups
    # only for the flat scan below — within-verse is the primary case).
    # We'll process verse-by-verse and use verse_content_lines for alignment.

    for verse_num, verse_numbered_lines in verse_groups:
        # verse_numbered_lines: [(1-based line_no, raw_line), ...]
        # Filter to non-empty, non-skippable content lines for alignment.
        content = [(ln, raw) for ln, raw in verse_numbered_lines if not is_skippable(raw)]

        if not content:
            continue

        # Build tag alignment for this verse.
        # MA.align_verse_tokens_to_tags expects bare line strings (no line numbers).
        verse_text_lines = [raw for _, raw in content]
        verse_token_tags: list[list[list[str]]] | None = None
        if chapter_morph is not None:
            ortho_tags = chapter_morph.get(verse_num)
            if ortho_tags is not None:
                verse_token_tags = MA.align_verse_tokens_to_tags(verse_text_lines, ortho_tags)
                # If alignment returned None, fall back to skel-heuristics for
                # the whole verse.

        def _tag_list_for(line_idx: int, tok_idx: int) -> list[str] | None:
            """Return the tag list for a specific token, or None on miss."""
            if verse_token_tags is None:
                return None
            if line_idx < 0 or line_idx >= len(verse_token_tags):
                return None
            tl = verse_token_tags[line_idx]
            if tok_idx < 0 or tok_idx >= len(tl):
                return None
            return tl[tok_idx]

        # Scan each content line within this verse.
        for ci, (line_no, line) in enumerate(content):
            tokens = line.split()
            if not tokens:
                continue

            last_token = tokens[-1]
            bare_last = strip_points(last_token)

            # Skip verse-final lines (sof pasuq) — no cross-line chain here.
            if has_sof_pasuq(last_token):
                continue

            # Skip maqqef-joined line endings — caught by H1 validator.
            if bare_last.endswith(MAQQEF) or last_token.endswith(MAQQEF):
                continue

            # Find next content line (may be in next verse or same verse).
            next_line = ""
            next_line_num = None
            # First look within this verse's content list.
            if ci + 1 < len(content):
                next_line_num, next_line = content[ci + 1]
            else:
                # Cross-verse: scan forward in all_lines from current position.
                for j in range(line_no, len(all_lines)):
                    if not is_skippable(all_lines[j]):
                        next_line = all_lines[j]
                        next_line_num = j + 1
                        break

            if not next_line:
                continue

            next_bare_first = first_bare_token(next_line)
            if not next_bare_first:
                continue

            # Tag list for the LAST token on this line (for construct-head check).
            last_tok_idx = len(tokens) - 1
            last_token_tags = _tag_list_for(ci, last_tok_idx)

            # --- Heuristic (b): Divine name compound ---
            if bare_last in DIVINE_NAME_SKELETONS and next_bare_first in YHWH_COMPOUND_FOLLOWERS:
                violations.append({
                    "file": path.name,
                    "file_path": path,
                    "line_num": line_no,
                    "rule": "H2/construct",
                    "severity": "STRONG-MERGE-CANDIDATE",
                    "subcase": "divine_name",
                    "brief": (
                        f"compound divine name split — "
                        f"{last_token!r} at line end, continuation {next_line.split()[0]!r} below "
                        f"(frozen formula per break-legality.md row 7)"
                    ),
                    "line": line.rstrip(),
                    "next_line": next_line.rstrip(),
                    "next_line_num": next_line_num,
                })
                continue

            # --- Heuristic (a): Definite-article rectum ---
            if starts_with_article(next_bare_first):
                # The next line's first token looks like an articulated noun that
                # could be a rectum. Check that the current line's last token is
                # a plausible regens (not itself articulated, not a particle).
                regens_is_articulated = bare_last.startswith("ה") and len(bare_last) > 1
                # If regens is itself articulated, it can't be in construct state
                # (articulated nouns are in absolute state — Joüon-Muraoka §137a).
                if not regens_is_articulated:
                    # FILTER: if the current line ends with a speech verb, the next
                    # line's ה-initial word is almost certainly speech content (an
                    # adverb like הֵיטֵב, a question particle, or a quoted clause
                    # opener) — NOT a construct rectum.  Skip the article heuristic
                    # entirely for speech-verb-final lines (Bug 3 fix).
                    if bare_last in SPEECH_VERB_SKELETONS:
                        continue

                    # All article-heuristic findings are REVIEW-REQUIRED.
                    # The heuristic cannot distinguish genuine construct rectum from:
                    #   - paragogic/cohortative ה on imperatives (הַגִּידָה)
                    #   - ה on adverbs (הֵיטֵב)
                    #   - appositive NPs following a proper noun (הָעִיר after נִינְוֵה)
                    # Demoting to REVIEW-REQUIRED keeps findings honest and avoids
                    # misleading the apply script with false STRONG-MERGE-CANDIDATEs.
                    severity = "REVIEW-REQUIRED"
                    # Tag-aware regens check: if TAHOT confirms construct state,
                    # note it in the brief for downstream visibility.
                    tag_confirms_construct = M.is_construct_head_token(
                        last_token, tag_list=last_token_tags
                    )
                    if tag_confirms_construct:
                        brief = (
                            f"construct chain split (TAHOT-confirmed regens) — "
                            f"{last_token!r} at line end, articulated word "
                            f"{next_line.split()[0]!r} at next line start"
                        )
                    elif bare_last in COMMON_CONSTRUCT_ENDINGS:
                        brief = (
                            f"possible construct chain split — known regens form {last_token!r} "
                            f"at line end, articulated word {next_line.split()[0]!r} at next line start"
                        )
                    else:
                        brief = (
                            f"possible construct chain split — {last_token!r} at line end, "
                            f"articulated word {next_line.split()[0]!r} at next line start"
                        )
                    violations.append({
                        "file": path.name,
                        "file_path": path,
                        "line_num": line_no,
                        "rule": "H2/construct",
                        "severity": severity,
                        "subcase": "article_rectum",
                        "brief": brief,
                        "line": line.rstrip(),
                        "next_line": next_line.rstrip(),
                        "next_line_num": next_line_num,
                    })
                continue

            # --- Heuristic (c): Construct-head check (non-articulated rectum) ---
            # Tag-driven path (TAHOT oracle): M.is_construct_head_token passes
            # tag_list to TAHOT for authoritative state-letter detection — catches
            # construct nouns absent from the COMMON_CONSTRUCT_ENDINGS closed list
            # (e.g. מְזוּזַת, נְאֻם, אֵין, אֱלֹהֵי).  Skel-fallback fires when tags
            # are unavailable, preserving the original COMMON_CONSTRUCT_ENDINGS coverage.
            is_construct = M.is_construct_head_token(last_token, tag_list=last_token_tags)
            if is_construct:
                # Skip if next token is a conjunction or particle (different clause)
                next_bare_stripped = strip_points(next_bare_first)
                is_next_clause_starter = (
                    next_bare_stripped.startswith("ו")  # vav-consecutive or conjunction
                    or next_bare_stripped in {"כי", "אשר", "אם", "כן", "כה", "הנה"}
                )
                if not is_next_clause_starter:
                    tag_driven = last_token_tags is not None
                    brief_prefix = (
                        "construct chain split (TAHOT-confirmed)"
                        if tag_driven
                        else "possible construct chain split — known construct form"
                    )
                    violations.append({
                        "file": path.name,
                        "file_path": path,
                        "line_num": line_no,
                        "rule": "H2/construct",
                        "severity": "REVIEW-REQUIRED",
                        "subcase": "common_construct_ending",
                        "brief": (
                            f"{brief_prefix} {last_token!r} "
                            f"at line end, next-line first token {next_line.split()[0]!r}"
                        ),
                        "line": line.rstrip(),
                        "next_line": next_line.rstrip(),
                        "next_line_num": next_line_num,
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
    print(f"Rule H2 Construct Chain validator — Tanakh {tier_label}")
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
