

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
Validate coordinated direct-object splits (IR-driven).

Detects coordinated-DO splits where a single finite verb governs multiple
direct-object tokens (Macula frame-arg A1) that themselves span multiple
editorial sense-lines.

This is the INVERSE of `validate_verb_object_bond`'s coordinated-object
license-guard. verb_object_bond SUPPRESSES verb-A1-stranding findings when
the next sense-line opens with a coordinated וְאֵת enumeration (because
the A1 was never on line N to begin with — it's a coordinate continuation).
This validator surfaces those same coordinated-object enumerations and
EVALUATES whether they are colometrically appropriate (combined-weight guard, heavy-NP guard).
[Poetic-register guard removed 2026-05-04 — not a structural discriminant.]

Detection (IR-driven, post-2026-05-06 Macula pivot):
  For each finite verb V in a verse:
    A1 = V.frame_args["A1"]                                   (Macula lowfat)
    Map each A1 token to its editorial sense-line index.
    Distinct-line A1 tokens with >=2 distinct line indices ->
        coordinated-object split. Emit a finding for the first
        adjacent line-pair (N, N+1) that hosts split A1 tokens.

  Frame-args resolution disambiguates אֵת (DO marker) from אַתְּ (2fs pronoun)
  automatically -- the IR knows what the constituent parser identified as
  the verb's object. No skel-trigger; no closed-list verb skeletons; no
  orthographic heuristics.

Severity (post-STRONG-promotion 2026-05-05):
  Findings with NO guard fired -> STRONG-MERGE-CANDIDATE (cascade-applicable).
  Findings with ANY guard fired -> REVIEW-REQUIRED (editorial triage required).

  Guard conditions that demote to REVIEW-REQUIRED:
    1. Combined prosodic-word count > 8 -- merged line would exceed colon
       ceiling; editorial judgement needed on where the true break belongs.
    2. Heavy NP on A1 (relative clause or apposition) -- the A1 constituent
       is structurally complex; merge may collapse meaningful sub-structure.

  [Poetic-register guard removed 2026-05-04 per methodology audit: coordinated
  DO is a clause-nucleus syntactic phenomenon in every register; demoting STRONG
  findings in Sifrei Emet / embedded poetry was overlay-as-authorization.
  Structural guards (weight, heavy-NP) alone discriminate genuinely ambiguous
  cases.]

  STRONG findings are safe to auto-apply because:
    - IR frame-args have already disambiguated DO vs. other אֵת uses.
    - Combined weight is within the 8-word colon ceiling.
    - No embedded complexity (relative clause / apposition) on the A1 span.

  Fallback: when lowfat XML is absent (synthetic fixture text, pre-alignment
  chapters), MC.get_verse_tokens raises FileNotFoundError/ValueError and
  scan_file silently skips the verse (no finding). There is NO pre-port
  heuristic path to restore here -- the pre-pivot orthographic skel-trigger
  (line_ends_with_et_np / line_starts_with_ve_et_np) detected only 20
  instances vs. ~600 for the IR, and its FP rate was significantly higher;
  restoring it as a fallback would re-introduce the FP surface the IR-pivot
  was intended to eliminate. Fixtures for this validator must use real
  verse refs that have lowfat coverage, or mock MC.get_verse_tokens.

References:
  - Canon §5 Rule M2 (verb-object clause-nucleus bond)
  - Canon §1 Structural Justification 1 (compound list break carve-out)
  - Joüon-Muraoka §137 (direct object and את)
  - Reference IR ports: verb_object_bond (c6bd30576),
    construct_chain (5bc7d88a8), participial_speech_frame (07974d52b)

Architectural constraint:
  No te'amim glyph triggers anywhere. The IR exposes morph + role + frame
  semantics — none accent-derived.

Legacy helpers (line_ends_with_et_np, line_starts_with_ve_et_np,
line_has_heavy_np, looks_like_finite_verb, KNOWN_FINITE_VERB_SKELETONS,
WAYYIQTOL_PREFIXES, QATAL_SUFFIXES) remain in this file as DEAD code from
the pre-pivot orthographic-trigger implementation; scan_file no longer
calls them. They are retained against the (low-but-nonzero) probability
that the IR-port misses a class the orthographic trigger uniquely caught
(8/20 of the prior 20 baseline findings transfer cleanly via lemma-A1;
the 12 misses are typically passive verbs and imperatives whose A1 is
encoded as a separate clause rather than a frame-arg list — see commit
log for details).

Exit code: 0 if zero findings, 1 if findings, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_coordinated_object.py
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_coordinated_object.py --book jonah
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_coordinated_object.py --v2
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_coordinated_object.py --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants — two-tier layout: v1/he-baseline + v2/heb
# ---------------------------------------------------------------------------
REPO_ROOT = _find_repo_root()
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files"  / "v2" / "heb"

# Make _shared importable when this script is run as __main__.
sys.path.insert(0, str(REPO_ROOT / "5-machinery/validators"))
# is_poetic_register import removed 2026-05-04: poetic register is no longer a
# STRONG-promotion guard — structural guards (weight, heavy-NP) alone discriminate.
# Superseded by 2026-05-04 methodology audit.
from _shared import macula_constituents as MC  # noqa: E402

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers
# ---------------------------------------------------------------------------

# Hebrew points (cantillation U+0591–U+05AF + niqqud U+05B0–U+05BC, U+05C1–U+05C2,
# U+05C4–U+05C5, U+05C7).  Strip U+0591-U+05BD (cantillation + niqqud) and U+05BF,
# U+05C1-U+05C2, U+05C4-U+05C5, U+05C7 while PRESERVING maqqef (U+05BE), paseq
# (U+05C0), and sof pasuq (U+05C3).
HEBREW_POINTS_RE = re.compile(r"[֑-ׇֽֿׁׂׅׄ]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"  # ׃
# Maqqef (orthographic word-joiner)
MAQQEF = "־"     # ־

# Direct-object marker
ET = "את"        # את


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
    """Return the book directory name (e.g. '32-jonah')."""
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
    prosodic word (1-method/canon §5 H1).  Since maqqef joins tokens orthographically
    INSIDE a single whitespace-delimited token, each whitespace-delimited
    content token is already one prosodic word.
    """
    return len(content_tokens(line))


def first_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[0] if toks else None


def last_content_token(line: str) -> str | None:
    toks = content_tokens(line)
    return toks[-1] if toks else None


# ---------------------------------------------------------------------------
# Verb detection heuristic
# ---------------------------------------------------------------------------

# Common finite-verb skeletons (post-strip)
KNOWN_FINITE_VERB_SKELETONS = {
    # Common qatal 3ms / 3fs / 3cp forms
    "אמר", "אמרה", "אמרו", "אמרתי", "אמרת", "אמרנו", "אמרתם",
    "ראה", "ראתה", "ראו", "ראיתי", "ראית", "ראינו",
    "שמע", "שמעה", "שמעו", "שמעתי", "שמענו",
    "ידע", "ידעה", "ידעו", "ידעתי", "ידעת", "ידענו",
    "ברא", "בראה", "בראו",
    "ברך", "ברכה", "ברכו", "ברכתי", "ברכת",
    "הלך", "הלכה", "הלכו", "הלכתי", "הלכנו",
    "נתן", "נתנה", "נתנו", "נתתי", "נתת",
    "עשה", "עשתה", "עשו", "עשיתי", "עשית", "עשינו",
    "היה", "היתה", "היו", "הייתי", "היית", "היינו",
    "בא", "באה", "באו", "באתי", "באת", "באנו",
    "קם", "קמה", "קמו", "קמתי", "קמנו",
    "בנה", "בנתה", "בנו", "בניתי",
    "לקח", "לקחה", "לקחו", "לקחתי",
    "כתב", "כתבה", "כתבו", "כתבתי",
    "כרת", "כרתה", "כרתו",
    "מצא", "מצאה", "מצאו", "מצאתי",
    "נשא", "נשאה", "נשאו", "נשאתי",
    "נפל", "נפלה", "נפלו", "נפלתי",
    "ישב", "ישבה", "ישבו", "ישבתי",
    "עבר", "עברה", "עברו",
    "אכל", "אכלה", "אכלו", "אכלתי",
    "שתה", "שתתה", "שתו",
    "מת", "מתה", "מתו", "מתי",
    "חיה", "חיתה", "חיו",
    "סר", "סרה", "סרו",
    "עלה", "עלתה", "עלו", "עליתי",
    "ירד", "ירדה", "ירדו",
    "שב", "שבה", "שבו", "שבתי",
    "הכה", "הכתה", "הכו",
    "הביא", "הביאה", "הביאו",
    "הוציא", "הוציאה", "הוציאו",
    "הגיד", "הגידה", "הגידו",
    "הציל", "הצילה", "הצילו",
    "צוה", "צותה", "צוו",
    "דבר", "דברה", "דברו",
    "פנה", "פנתה", "פנו",
    "נסע", "נסעה", "נסעו",
    # Common yiqtol stems
    "יאמר", "תאמר", "יאמרו", "תאמרו", "נאמר",
    "ישמע", "תשמע", "ישמעו",
    "יראה", "תראה", "יראו",
    "יבא", "תבא", "יבאו", "יקם",
    "יעשה", "תעשה", "יעשו",
    "ילך", "תלך", "ילכו",
    "יתן", "תתן", "יתנו", "אתן",
    "יקח", "תקח", "יקחו",
    "ישב", "תשב", "ישבו",
    "ידע", "תדע", "ידעו",
    "יזכר", "תזכר", "יזכרו",
}

WAYYIQTOL_PREFIXES = ("וי", "ות", "ונ", "וא")
QATAL_SUFFIXES = ("תי", "ת", "נו", "תם", "תן", "ו")


def looks_like_finite_verb(bare: str) -> bool:
    """Heuristic: does this bare consonant skeleton look like a finite verb?

    Conservative bias: we'd rather over-detect finite verbs (causing guards
    to fire and the finding to be skipped) than under-detect them.
    """
    if not bare:
        return False

    # Direct skeleton match
    if bare in KNOWN_FINITE_VERB_SKELETONS:
        return True

    # Wayyiqtol prefix detection
    if bare.startswith(WAYYIQTOL_PREFIXES):
        if len(bare) >= 4 and bare not in ("ויהוה",):
            return True

    # Maqqef-internal verb check
    if MAQQEF in bare:
        for part in bare.split(MAQQEF):
            if part in KNOWN_FINITE_VERB_SKELETONS:
                return True
            if part.startswith(WAYYIQTOL_PREFIXES) and len(part) >= 4:
                return True

    # Qatal-suffix sniff
    for suf in ("תי", "תם", "תן", "נו"):
        if bare.endswith(suf) and len(bare) >= 4:
            return True

    return False


def line_has_finite_verb(line: str) -> bool:
    """True if any content token on `line` looks like a finite verb."""
    for tok in content_tokens(line):
        bare = strip_points(tok)
        if looks_like_finite_verb(bare):
            return True
    return False


# ---------------------------------------------------------------------------
# Direct-object marker detection (אֵת + NP)
# ---------------------------------------------------------------------------

def line_ends_with_et_np(line: str) -> bool:
    """True if line ends with אֵת (direct-object marker) + NP."""
    toks = content_tokens(line)
    if not toks:
        return False
    # Last token must be part of an אֵת-marked object phrase.
    # Heuristic: last token or second-to-last contains אֵת as prefix or standalone.
    bare_last = strip_points(toks[-1]).rstrip(SOF_PASUQ)
    if bare_last == ET or bare_last.startswith(ET):
        return True
    if len(toks) >= 2:
        bare_penult = strip_points(toks[-2]).rstrip(SOF_PASUQ)
        if bare_penult == ET or bare_penult.startswith(ET):
            return True
    return False


def line_starts_with_ve_et_np(line: str) -> bool:
    """True if line begins with וְאֵת (conjunction + direct-object marker) + NP."""
    first = first_content_token(line)
    if not first:
        return False
    bare = strip_points(first).rstrip(SOF_PASUQ)
    # Pattern: starts with ו (vav conjunction) + אֵת (direct-object marker)
    # Bare form after stripping: ואת... or just ואת
    return bare.startswith("וא") and ("את" in bare or bare.startswith("ואת"))


# ---------------------------------------------------------------------------
# Heavy NP detection
# ---------------------------------------------------------------------------

def line_has_heavy_np(line: str) -> bool:
    """True if line contains relative clause or ≥2 appositives (heavy nominal).

    Heuristic: ashur / mi / mah (relative/interrogative), or ≥2 ben/bat (appositives).
    """
    bares = [strip_points(t).rstrip(SOF_PASUQ) for t in content_tokens(line)]
    if not bares:
        return False

    # Check for relative/interrogative
    if "אשר" in bares or "מי" in bares or "מה" in bares:
        return True

    # Check for appositives (ben/bat count)
    appositive_count = sum(1 for b in bares if b in ("בן", "בת"))
    if appositive_count >= 2:
        return True

    return False


# ---------------------------------------------------------------------------
# Verse partitioning
# ---------------------------------------------------------------------------

def partition_into_verses(lines: list[str]) -> list[tuple[int | None, int | None, list[int]]]:
    """Group line indices by verse.

    Returns a list of (chapter, verse, [line_indices]) tuples in source order.
    Verse-reference lines themselves are included but are skippable for content scanning.
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


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def _a1_has_heavy_np_ir(a1_tokens: list) -> bool:
    """Heavy-NP guard (IR-driven): any A1 token sits inside a relative clause
    or apposition. Uses the IR's Constituent.is_relative_clause and
    is_apposition predicates via ancestor walk -- replaces the prior
    orthographic skel-list heuristic.
    """
    for tok in a1_tokens:
        cur = tok.parent_constituent
        while cur is not None:
            if cur.is_relative_clause or cur.is_apposition:
                return True
            cur = cur.parent
    return False


def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    """IR-driven scan for coordinated-DO splits across editorial sense-lines.

    Per verse:
      1. Pull Macula lowfat verse tokens.
      2. Greedy-align each editorial sense-line to its slice of verse tokens,
         building a token_id -> sense_line_index map.
      3. For each finite verb V in the verse, gather V.frame_args["A1"]. If A1
         tokens span >=2 distinct sense-lines, locate the FIRST adjacent
         line-pair (N, N+1) that both host A1 tokens and emit one finding
         (matches the prior validator's per-pair semantics).
      4. Apply guards (poetic register, combined > 8 prosodic words, heavy NP).

    Severity: STRONG-MERGE-CANDIDATE when no guard fires; REVIEW-REQUIRED
    when any guard fires (poetic register, combined > 8 prosodic words, or
    heavy NP). Guard reasons are recorded in the `guard_reason` field for
    downstream triage. The `tag` field mirrors `severity` for cascade dispatch.
    """
    findings: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    book_slug = book_name_from_path(path)
    verses = partition_into_verses(lines)

    for ch, vs, indices in verses:
        if ch is None or vs is None:
            continue
        sense_indices = [i for i in indices if not is_skippable(lines[i])]
        if len(sense_indices) < 2:
            continue

        try:
            verse_tokens = MC.get_verse_tokens(book_slug, ch, vs)
        except (FileNotFoundError, ValueError, KeyError):
            continue
        if not verse_tokens:
            continue

        # Greedy-align each sense-line to the verse's tokens; build
        # token_id -> sense_line_idx (index INTO sense_indices).
        token_to_line: dict[str, int] = {}
        cursor = 0
        for line_idx, src_idx in enumerate(sense_indices):
            matched, cursor = MC.match_sense_line_tokens(
                verse_tokens, lines[src_idx], start_idx=cursor
            )
            for tok in matched:
                token_to_line[tok.xml_id] = line_idx

        emitted_pairs: set[tuple[int, int]] = set()

        for verb in verse_tokens:
            if not verb.is_finite_verb:
                continue
            a1_tokens = verb.frame_args.get("A1") or []
            if len(a1_tokens) < 2:
                # Need >=2 A1 tokens for a coordinated-object enumeration
                continue

            a1_lines: list[tuple[int, "MC.Token"]] = []
            for a1 in a1_tokens:
                li = token_to_line.get(a1.xml_id)
                if li is not None:
                    a1_lines.append((li, a1))

            distinct_lines = {li for li, _ in a1_lines}
            if len(distinct_lines) < 2:
                continue

            # Find FIRST adjacent line-pair (N, N+1) where both lines host
            # at least one A1 token. Matches the prior validator's per-pair
            # detection signature (et + NP // waw-et + NP on adjacent lines).
            line_pair: tuple[int, int] | None = None
            for k in range(len(sense_indices) - 1):
                if k in distinct_lines and (k + 1) in distinct_lines:
                    line_pair = (k, k + 1)
                    break
            if line_pair is None:
                # A1 tokens span non-adjacent lines -- defer to verb_object_bond
                # / clause_nucleus_split coverage; this validator's contract is
                # the adjacent-pair coordinated-DO pattern.
                continue

            n_line_idx, n1_line_idx = line_pair
            n_src_idx = sense_indices[n_line_idx]
            n1_src_idx = sense_indices[n1_line_idx]
            if (n_src_idx, n1_src_idx) in emitted_pairs:
                continue
            emitted_pairs.add((n_src_idx, n1_src_idx))

            line_n = lines[n_src_idx]
            line_n1 = lines[n1_src_idx]

            # ----- guards -----
            guard_reason: str | None = None

            # Poetic-register guard removed 2026-05-04: superseded by methodology audit.
            # Coordinated DO is a clause-nucleus syntactic fact in any register;
            # weight + heavy-NP guards already discriminate genuinely ambiguous cases.
            # overlay-as-authorization failure mode closed here.

            combined_words = prosodic_word_count(line_n) + prosodic_word_count(line_n1)
            if guard_reason is None and combined_words > 8:
                guard_reason = "combined > 8 prosodic words"

            if guard_reason is None and _a1_has_heavy_np_ir([a for _, a in a1_lines]):
                guard_reason = "heavy NP (relative clause or apposition)"

            # Severity: STRONG when no guard fired; REVIEW-REQUIRED otherwise.
            # Guards: combined > 8 prosodic words, heavy NP.
            # (poetic-register guard removed 2026-05-04 — not a structural discriminant)
            severity = "REVIEW-REQUIRED" if guard_reason else "STRONG-MERGE-CANDIDATE"

            a1_texts = [a.text for _, a in a1_lines]
            prior_text = line_n.strip()
            next_text = line_n1.strip()

            annotation = (
                "Coordinated direct object (compound DO of shared verb): "
                f"verb {verb.text!r} governs A1={a1_texts!r} spanning multiple "
                "sense-lines. Canon §5 M2 (verb-object clause-nucleus bond) "
                "and §1 Structural Justification 1 (compound list break "
                "signals) apply — bare 'and [noun]' items merge without "
                "elided-verb signal. (Per Joüon-Muraoka §137; "
                "Waltke-O'Connor §9.5.2.)"
            )
            if guard_reason:
                annotation += f" Guard fired: {guard_reason}."

            brief = (
                f"coordinated DO split — verb {verb.text!r} A1={a1_texts!r} — "
                f"{prior_text} // {next_text} ({combined_words} prosodic words combined)"
            )

            findings.append({
                "file_path": path,
                "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "line_num": n_src_idx + 1,
                "next_line_num": n1_src_idx + 1,
                "rule": "M2/coordinated-object",
                "severity": severity,
                "tag": severity,  # explicit tag field for cascade dispatch
                "book": book_slug,
                "chapter": ch,
                "verse": vs,
                "prior_line": prior_text,
                "next_line": next_text,
                "prosodic_word_count": combined_words,
                "annotation": annotation,
                "suggested_action": "MERGE candidate per M2 + compound-list rule",
                "brief": brief,
                "guard_reason": guard_reason,
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
    parser.add_argument("--v2", action="store_true", help="Scan v2/heb (default if v1 missing).")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show context.")
    parser.add_argument("--json", action="store_true", help="Emit JSON document.")
    args = parser.parse_args()

    base_dir = V2_DIR if args.v2 else V1_DIR
    tier_label = "v2/heb" if args.v2 else "v1/he-baseline"
    if not base_dir.exists():
        # Fall back to the other tier
        alt = V2_DIR if not args.v2 else V1_DIR
        if alt.exists():
            base_dir = alt
            tier_label = "v2/heb" if alt is V2_DIR else "v1/he-baseline"
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
                "tag": f.get("tag", f["severity"]),
                "book": f["book"],
                "chapter": f["chapter"],
                "verse": f["verse"],
                "prior_line": f["prior_line"],
                "next_line": f["next_line"],
                "next_line_num": f["next_line_num"],
                "prosodic_word_count": f["prosodic_word_count"],
                "annotation": f["annotation"],
                "suggested_action": f["suggested_action"],
                "guard_reason": f.get("guard_reason"),
            })

        counts = {"REVIEW-REQUIRED": 0, "STRONG-MERGE-CANDIDATE": 0}
        for f in findings_json:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1

        doc = {
            "validator": "validate_coordinated_object",
            "rule": "M2/coordinated-object",
            "version": "2.0.0",
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
    print(f"Coordinated-Object Validator (IR-driven) — Tanakh {tier_label}")
    print(f"Reference: 1-method/canon §5 M2 (verb-object clause-nucleus bond)")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Findings      : {len(all_findings)}")

    strong_count = sum(1 for f in all_findings if f["severity"] == "STRONG-MERGE-CANDIDATE")
    review_count = sum(1 for f in all_findings if f["severity"] == "REVIEW-REQUIRED")
    if strong_count or review_count:
        print()
        print(f"  STRONG-MERGE-CANDIDATE: {strong_count}")
        print(f"  REVIEW-REQUIRED       : {review_count}")
    print()

    if all_findings:
        for f in all_findings:
            print(
                f"[DEVIATION]  {f['file_rel']}:{f['line_num']}  "
                f"{f['rule']}  {f['severity']}  {f['brief']}"
            )
            if args.verbose:
                print(f"    {f['prior_line'][:120]}")
                print(f"    → {f['next_line'][:120]}")
                print(f"    {f['annotation']}")
                if f.get("guard_reason"):
                    print(f"    Guard: {f['guard_reason']}")
                print()
    else:
        print("No findings. Coordinated-object rule is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
