#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Merge-Override M4 — Fragmented Atomic Thought-Unit via short orphan lines.

M4 (canon §4 Merge-overrides; Layer 3 editorial rule):
If splitting a line would produce fragments that individually fail the atomic-thought
test, merge. This validator operationalizes the special case of SINGLE-TOKEN orphan
lines that are not sentence-final verbs, classical commas, or vocatives.

PATTERN DEFINITION (this validator's scope):
A colometric line consisting of exactly 1 prosodic word (excluding maqqef-grouped
tokens counted as one) that is NOT one of the explicitly standalone-permitted
lexical categories:

  1. Sentence-final verb — qatal 3ms / 3fs / 3cp forms that complete a sentence
     (short, high-confidence skeletons: אמר, ראה, שמע, ידע, etc. in qatal-3 forms).

  2. Classical comma — a small closed-list discourse/interjection particle that
     logically stands alone: אַשְׁרֵי ("blessed"), הוֹי ("alas"), אָמֵן ("amen"),
     שָׁלוֹם ("peace"), בְרָכָה ("blessing"), or similar blessing/responsive markers.

  3. Vocative — a direct-address element marked by 2nd-person pronoun, vocative
     particle (הוֹי, אוֹי), or divine-name vocative (יְהוָה, אֱלֹהִים addressed).

TRIGGER:
  prosodic_word_count(line) == 1  AND  token NOT IN standalone-permitted lexicon

SEVERITY:
  REVIEW-REQUIRED — M4 is judgment-heavy; fragments that appear syntactically
  acceptable still need editorial eye. The validator surfaces candidates; the
  editor confirms whether atomic-thought actually breaks.

ARCHITECTURAL CONSTRAINT:
  No te'amim glyph predicates. Skip poetic register (Sifrei Emet chapters).
  Niqqud is allowed (niqqud ≠ te'amim). No reliance on verse-ending or
  cantillation hierarchy.

Output format:
    [DEVIATION]  file:line  M4/orphan-line-atomic-thought  REVIEW-REQUIRED  brief

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_short_orphan_line.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_short_orphan_line.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_short_orphan_line.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_short_orphan_line.py --json
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
from _shared.poetic_register import is_poetic_register  # noqa: E402
from _shared import morph_alignment as MA  # noqa: E402
from _shared import morphology as M  # noqa: E402

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers
# ---------------------------------------------------------------------------

# Hebrew points (cantillation U+0591–U+05AF + niqqud U+05B0–U+05BC, U+05C1–U+05C2,
# U+05C4–U+05C5, U+05C7). Strip all to leave consonant skeleton.
# Preserve maqqef (U+05BE), paseq (U+05C0), sof pasuq (U+05C3) so word boundaries remain.
HEBREW_POINTS_RE = re.compile(r"[֑-ׇֽֿׁׂׅׄ]")

# Sof pasuq, maqqef
SOF_PASUQ = "׃"
MAQQEF = "־"
PASEQ = "׀"


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


# Independent personal pronouns that, when standing alone on a line, are
# subjects requiring merge with their finite-verb predicate on the next line.
# Includes vav-prefixed forms (וְהֵמָּה, וְאַתָּה, etc.).
SUBJECT_PRONOUN_SKELETONS = frozenset({
    "הוא", "היא", "הם", "המה", "הן", "הנה",
    "אני", "אנכי", "אנחנו",
    "אתה", "את", "אתם", "אתן", "אתנה",
    "והוא", "והיא", "והם", "והמה", "והנה", "והן",
    "ואני", "ואנכי", "ואנחנו",
    "ואתה", "ואת", "ואתם", "ואתן",
})


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


def prosodic_word_count(line: str) -> int:
    """Count prosodic words.

    Whitespace-delimited tokens, with maqqef-joined groups counted as one
    prosodic word (canon §5 H1). Since maqqef joins tokens orthographically
    INSIDE a single whitespace-delimited token, each whitespace-delimited
    content token is already one prosodic word.
    """
    return len(content_tokens(line))


def first_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[0] if toks else None


# ---------------------------------------------------------------------------
# Standalone-permitted lexicon
# ---------------------------------------------------------------------------

# Sentence-final verbs: qatal 3ms / 3fs / 3cp forms that commonly stand alone,
# completing a sentence. High-confidence, frequently-isolated skeletons.
SENTENCE_FINAL_VERBS = {
    # Common qatal 3ms forms
    "אמר", "ראה", "שמע", "ידע", "ברא", "ברך", "הלך", "נתן", "עשה",
    "היה", "בא", "קם", "בנה", "לקח", "כתב", "כרת", "מצא", "נשא",
    "נפל", "ישב", "עבר", "אכל", "שתה", "מת", "חיה", "סר", "עלה",
    "ירד", "שב", "הכה", "הביא", "הוציא", "הגיד", "הציל", "צוה",
    "דבר", "פנה", "נסע", "שמר", "שמר", "קרא", "זעק", "התפלל",
    # Common qatal 3fs forms
    "אמרה", "ראתה", "בראה", "ברכה", "הלכה", "נתנה", "עשתה", "היתה",
    "באה", "קמה", "בנתה", "לקחה", "כתבה", "כרתה", "מצאה", "נשאה",
    "נפלה", "ישבה", "עברה", "אכלה", "שתתה", "מתה", "חיתה", "סרה",
    "עלתה", "שבה", "הכתה", "הביאה", "הוציאה", "הגידה", "הצילה",
    "דברה", "פנתה", "נסעה", "קראה",
    # Common qatal 3cp forms
    "אמרו", "ראו", "בראו", "ברכו", "הלכו", "נתנו", "עשו", "היו",
    "באו", "קמו", "בנו", "לקחו", "כתבו", "כרתו", "מצאו", "נשאו",
    "נפלו", "ישבו", "עברו", "אכלו", "שתו", "מתו", "חיו", "סרו",
    "עלו", "ירדו", "שבו", "הכו", "הביאו", "הוציאו", "הגידו",
    "הצילו", "צווו", "דברו", "פנו", "נסעו", "קראו", "זעקו",
}

# Classical comma / interjection / blessing words that logically stand alone.
# These are short, semantically complete, and commonly isolated in discourse.
CLASSICAL_COMMAS = {
    "אשרי",      # אַשְׁרֵי — "blessed (are)"
    "הוי",       # הוֹי — "alas" (vocative particle)
    "אוי",       # אוֹי — "woe" (interjection)
    "אמן",       # אָמֵן — "amen"
    "שלום",      # שָׁלוֹם — "peace" / "hello"
    "טוב",       # טוֹב — "good" (in responsive context)
}

# Divine vocative tails — these mark a divine-address element.
DIVINE_VOCATIVE_TAILS = {"יהוה", "יה", "אלהים", "אדני"}

# Address particles — mark vocative/exclamation position
ADDRESS_PARTICLES = {"הוי", "אוי", "אהה", "אנא"}


def is_standalone_permitted(
    token: str,
    line: str,
    tag_list: "list[str] | None" = None,
) -> bool:
    """Return True if this single-token line is in the standalone-permitted lexicon.

    Three conditions:
      (a) Sentence-final verb — any finite verb form (tag-aware via TAHOT morph
          when available; skel-heuristic fallback when not).
      (b) Classical comma — blessing/interjection from closed list.
      (c) Vocative — divine name, address particle, or 2nd-person marker.

    The `tag_list` parameter, when provided, routes condition (a) through
    M.is_finite_verb_token's tag-driven path (TAHOT oracle), eliminating the
    systematic FP class of nouns that share skeletons with qatal-3 forms.
    """
    bare = strip_points(token).rstrip(SOF_PASUQ)
    if not bare:
        return False

    # (a) Sentence-final (finite) verb check — tag-aware primary, skel fallback
    if M.is_finite_verb_token(token, tag_list=tag_list):
        return True

    # (b) Classical comma check
    if bare in CLASSICAL_COMMAS:
        return True

    # (c) Vocative check
    # Divine vocative tails (יְהוָה, אֱלֹהִים, etc. addressed)
    if bare in DIVINE_VOCATIVE_TAILS:
        return True
    # Address particles (הוֹי, אוֹי, etc.)
    if bare in ADDRESS_PARTICLES:
        return True
    # 2nd-person pronoun or suffix (אַתָּה, אַתֶּם, etc., or -ך suffix)
    if bare in ("אתה", "את", "אתם", "אתן"):
        return True
    if bare.endswith("ך") and len(bare) >= 2:
        return True

    return False


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

    # Load TAHOT morph alignment for this chapter (None if morph file absent).
    chapter_morph = MA.load_chapter_morph(path)

    # Build verse-context map: line_index → (chapter, verse)
    line_to_verse: dict[int, tuple[int | None, int | None]] = {}
    cur_chapter: int | None = None
    cur_verse: int | None = None
    for i, line in enumerate(lines):
        ref = parse_verse_ref(line)
        if ref is not None:
            cur_chapter, cur_verse = ref
            line_to_verse[i] = (cur_chapter, cur_verse)
        else:
            line_to_verse[i] = (cur_chapter, cur_verse)

    # Build per-verse line groupings for alignment (verse → list of (line_idx, line))
    verse_lines_map: dict[tuple[int | None, int | None], list[tuple[int, str]]] = {}
    for i, line in enumerate(lines):
        if is_skippable(line):
            continue
        v_ctx = line_to_verse.get(i, (None, None))
        verse_lines_map.setdefault(v_ctx, []).append((i, line))

    # Build per-verse token-tag mapping:
    # verse_key → list[list[list[str]]]  (line → token → tag_list)
    # None when alignment unavailable.
    verse_token_tags_map: dict[
        tuple[int | None, int | None],
        "list[list[list[str]]] | None"
    ] = {}
    if chapter_morph is not None:
        for v_key, idx_line_pairs in verse_lines_map.items():
            _verse_num = v_key[1]
            if _verse_num is None:
                verse_token_tags_map[v_key] = None
                continue
            ortho_tags = chapter_morph.get(_verse_num)
            if ortho_tags is None:
                verse_token_tags_map[v_key] = None
                continue
            # align_verse_tokens_to_tags expects the content lines only (no ref lines)
            content_only = [ln for (_, ln) in idx_line_pairs]
            aligned = MA.align_verse_tokens_to_tags(content_only, ortho_tags)
            verse_token_tags_map[v_key] = aligned  # may be None on mismatch

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        # Get verse context for poetic-register check
        v_ctx = line_to_verse.get(i, (None, None))
        chapter = v_ctx[0] if v_ctx[0] is not None else chapter_from_file
        verse = v_ctx[1]

        # Skip poetic register
        if chapter is not None and is_poetic_register(book, chapter, verse):
            continue

        # Check if this line is a single-token orphan
        toks = content_tokens(line)
        if len(toks) != 1:
            continue

        token = toks[0]

        # Resolve tag_list for this token within its verse.
        # The line's position within the verse determines which token-tag-list to use.
        tag_list: "list[str] | None" = None
        verse_token_tags = verse_token_tags_map.get(v_ctx)
        if verse_token_tags is not None:
            # Find this line's index within its verse content lines.
            verse_idx_lines = verse_lines_map.get(v_ctx, [])
            line_pos_in_verse = next(
                (pos for pos, (li, _) in enumerate(verse_idx_lines) if li == i),
                None,
            )
            if line_pos_in_verse is not None and line_pos_in_verse < len(verse_token_tags):
                line_tok_tags = verse_token_tags[line_pos_in_verse]
                # Single-token orphan: tok_idx == 0
                if line_tok_tags:
                    tag_list = line_tok_tags[0]  # list[str] for this token's ortho components

        # Check if token is in the standalone-permitted lexicon (tag-aware)
        if is_standalone_permitted(token, line, tag_list=tag_list):
            continue

        # ── STRONG-MERGE arm: subject-pronoun-orphan + finite-verb-next ──
        # Tight pattern: 1-token line that's a subject pronoun, followed by a
        # line whose first token is a tag-confirmed finite verb. Both within
        # the same verse. Typical case: Jer 31:33 וְהֵמָּה / יִהְיוּ־לִי לְעָם
        # ("and they / will be to me a people"). The subject pronoun and verb
        # form a single clause-nucleus and must be co-located per H18.
        bare = strip_points(token).rstrip(SOF_PASUQ).rstrip("׃")
        if bare in SUBJECT_PRONOUN_SKELETONS:
            # Find next non-skippable line within same verse
            next_line_idx = None
            for k in range(i + 1, len(lines)):
                if is_skippable(lines[k]):
                    if parse_verse_ref(lines[k]) is not None:
                        break  # crossed verse boundary; abort
                    continue
                # Same-verse check
                if line_to_verse.get(k, (None, None)) != v_ctx:
                    break
                next_line_idx = k
                break
            if next_line_idx is not None:
                next_toks = content_tokens(lines[next_line_idx])
                if next_toks:
                    # Tag-confirm next-line first token is finite verb
                    next_tag_list = None
                    if verse_token_tags is not None:
                        next_pos = next(
                            (pos for pos, (li, _) in enumerate(verse_lines_map.get(v_ctx, []))
                             if li == next_line_idx),
                            None,
                        )
                        if next_pos is not None and next_pos < len(verse_token_tags):
                            line_tok_tags = verse_token_tags[next_pos]
                            if line_tok_tags:
                                next_tag_list = line_tok_tags[0]
                    # For maqqef-bound tokens (e.g. יִהְיוּ־לִי), the verb is the
                    # FIRST morpheme but is_finite_verb_token's tag-path uses LAST.
                    # Check ANY tag in the list for finite-verb classification.
                    # Also extract verb pgn (person-gender-number) for agreement.
                    next_first_is_verb = False
                    next_first_is_wayyiqtol = False
                    next_first_is_weqatal = False
                    verb_pgn: str | None = None
                    if next_tag_list:
                        from _shared import morph_tags as MT
                        for tag in next_tag_list:
                            if tag and tag != "[—]":
                                if MT.is_finite_verb(tag):
                                    next_first_is_verb = True
                                    # Extract verb pgn from morpheme like "HVqi3mp"
                                    # → last 3 chars before any /Sp suffix
                                    for morpheme in tag.split("/"):
                                        m = morpheme.lstrip("Hc")
                                        if m.startswith("V") and len(m) >= 6:
                                            verb_pgn = m[3:6]
                                            break
                                if MT.is_wayyiqtol(tag):
                                    next_first_is_wayyiqtol = True
                                if MT.is_weqatal(tag):
                                    next_first_is_weqatal = True
                                if (
                                    next_first_is_verb
                                    and next_first_is_wayyiqtol
                                    and next_first_is_weqatal
                                ):
                                    break
                    # Extract pronoun pgn from tag (Pp3mp / Pp1cs / etc.)
                    pron_pgn: str | None = None
                    if tag_list:
                        for tag in tag_list:
                            if tag and tag != "[—]":
                                for morpheme in tag.split("/"):
                                    m = morpheme.lstrip("Hc")
                                    if m.startswith("Pp") and len(m) >= 5:
                                        pron_pgn = m[2:5]
                                        break
                                if pron_pgn:
                                    break
                    # FP guard: wayyiqtol on next line opens a NEW clause
                    # (Gen 20:2 הוא | וַיִּשְׁלַח, Gen 38:16 הִוא | וַתֹּאמֶר etc.).
                    # The pronoun is then a predicate completing a prior verbless
                    # clause, not the subject of the wayyiqtol.
                    # FP guard: weqatal on next line is the apodosis of a protasis
                    # whose predicate is the verbless equation ending in this
                    # pronoun. Catches Lev 13:3 / 13:49 / Num 5:28 / 1Kgs 8:41 etc.
                    # (`נֶגַע צָרַעַת | הוּא וְרָאָהוּ` — pronoun closes verbless
                    # equation "it is a leprous mark"; weqatal `וְרָאָהוּ` opens
                    # apodosis "and the priest shall examine him"). Per
                    # 2026-05-04 borderline-audit verdict (4/6 FPs all share
                    # this pattern; Ezek 27:10/44:29 valid merges have no waw
                    # on next-line verb).
                    # FP guard: pronoun and verb must agree on person/number/gender.
                    # Catches verbless-equation predicates + new-imperative cases:
                    # 1 Kings 18:8 אָנִי | לֵךְ (1cs vs 2ms), 2 Kings 1:12
                    # אָנִי | תֵּרֶד (1cs vs 3fs), etc. Imperative cs/c-marker not
                    # always preserved across morphemes — use loose match where
                    # gender 'b' (epicene) is permissive.
                    # Person + number must match. Gender check skipped because
                    # qatal-3cp is unmarked-gender (verb 'c') and matches both
                    # 3mp and 3fp pronouns (Ezek 27:10 הֵמָּה / נָתְנוּ etc.).
                    pgn_match = True
                    if verb_pgn and pron_pgn:
                        pgn_match = (
                            verb_pgn[0] == pron_pgn[0]      # person matches
                            and verb_pgn[2] == pron_pgn[2]  # number matches
                        )
                    if (
                        next_first_is_verb
                        and not next_first_is_wayyiqtol
                        and not next_first_is_weqatal
                        and pgn_match
                    ):
                        line_no = i + 1
                        findings.append({
                            "file_path": path,
                            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                            "line_num": line_no,
                            "rule": "M4/subject-pronoun-orphan",
                            "severity": "STRONG-MERGE-CANDIDATE",
                            "token": bare,
                            "prior_context": "",
                            "next_context": lines[next_line_idx].strip()[:80],
                            "annotation": (
                                "Subject pronoun on its own line followed by a "
                                "tag-confirmed finite verb on next line — clause-"
                                "nucleus integrity (H18) requires merge."
                            ),
                            "brief": (
                                f"subject-pronoun orphan '{bare}' + finite verb "
                                f"'{strip_points(next_toks[0])}' on next line — merge"
                            ),
                            "book": book,
                            "chapter": chapter,
                            "verse": verse,
                            "text": line.strip(),
                        })
                        continue

        # Emit REVIEW-REQUIRED finding
        line_no = i + 1
        prior_context = ""
        next_context = ""

        # Gather prior and next lines for context
        for j in range(max(0, i - 1), i):
            if not is_skippable(lines[j]):
                prior_context = lines[j].strip()[:80]
        for j in range(i + 1, min(len(lines), i + 2)):
            if not is_skippable(lines[j]):
                next_context = lines[j].strip()[:80]

        brief = f"single-token orphan line: '{bare}' ({bare})"
        annotation = (
            "Single-token line that is not a sentence-final verb, classical comma, "
            "or vocative (M4 Fragmented Atomic Thought-Unit). Candidate for merge "
            "if the token fails to constitute an atomic thought on its own."
        )

        findings.append({
            "file_path": path,
            "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "line_num": line_no,
            "rule": "M4/orphan-line-atomic-thought",
            "severity": "REVIEW-REQUIRED",
            "token": bare,
            "prior_context": prior_context,
            "next_context": next_context,
            "annotation": annotation,
            "brief": brief,
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "text": line.strip(),
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
        # Fall back to the other tier rather than failing
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
            sev = f["severity"]
            applied_action = (
                "merge_with_next" if sev == "STRONG-MERGE-CANDIDATE" else None
            )
            findings_json.append({
                "file": f["file_rel"],
                "line": f["line_num"],
                "severity": "DEVIATION",
                "tag": sev,
                "rule_id": "M4",
                "rule": f["rule"],
                "rule_short": "fragmented atomic thought-unit",
                "token": f["token"],
                "book": f["book"],
                "chapter": f["chapter"],
                "verse": f["verse"],
                "brief": f.get("brief", ""),
                "text": f["text"],
                "applied_action": applied_action,
            })

        counts: dict[str, int] = {}
        for f in findings_json:
            counts[f["tag"]] = counts.get(f["tag"], 0) + 1

        doc = {
            "validator": "validate_short_orphan_line",
            "rule": "M4",
            "version": "1.0.0",
            "layer": 3,
            "book": args.book or "all",
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": findings_json,
            "counts": counts,
            "summary": {
                "total_findings": len(findings_json),
                "by_severity": counts,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output ---
    print("=" * 72)
    print(f"Rule M4 Fragmented Atomic Thought-Unit validator — Tanakh {tier_label}")
    print(f"Reference: canon §4 M4 (short orphan lines)")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Findings      : {len(all_findings)}")
    print()

    if all_findings:
        for f in all_findings:
            print(
                f"[DEVIATION]  {f['file_rel']}:{f['line_num']}  "
                f"{f['rule']}  {f['severity']}  {f['brief']}"
            )
            if args.verbose:
                print(f"    Text: {f['text'][:120]}")
                if f['prior_context']:
                    print(f"    Prior: {f['prior_context']}")
                if f['next_context']:
                    print(f"    Next: {f['next_context']}")
                print(f"    {f['annotation']}")
                print()
    else:
        print("No findings. All single-token lines are in the standalone-permitted lexicon.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
