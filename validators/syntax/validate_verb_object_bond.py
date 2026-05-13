#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate Layer 1 + Canon M2 — Verb-Object Clause-Nucleus Bond.

A finite verb and its direct object (frame-arg A1) form an indivisible
clause nucleus; they cannot be split across editorial sense-lines.

Detection (IR-driven, post-2026-05-05 Macula pivot):
  For each finite verb in a verse, check whether any of its frame-arg A1
  tokens land on the NEXT editorial sense-line. A1 references come from
  the Macula Hebrew lowfat XML constituent tree (validators/_shared/
  macula_constituents.py). This replaces the prior `את`-skeleton-trigger
  + tag-driven discriminator approach: frame-args resolution disambiguates
  אֵת (DO marker) from אַתְּ (2fs pronoun) automatically — a verb's A1 is
  what the constituent parser identified as its object, period.

  NB: A1 may resolve to a clause head (role="v") when the verb's object
  is a content-clause (כִּי / אֲשֶׁר / inf-construct). Those are licensed
  splits per H5b/H10 colometric discipline; the clausal-A1 license-guard
  suppresses them.

Severity:
  - STRONG-MERGE-CANDIDATE — finite verb + nominal A1 on next line, prose
    register, no intervening guards, no relp-ancestor on A1 (restrictive
    relative exclusion), N+1 does not open with wayyiqtol. Category A per
    canon §2.
  - REVIEW-REQUIRED — poetic register, A1 has relp ancestor (restrictive
    relative modifies object), A1 is verbal (infinitive construct/absolute),
    or N+1 opens with wayyiqtol.

Fallback (no lowfat alignment):
  When the Macula IR cannot resolve tokens (synthetic fixture text, missing
  lowfat XML), the scanner falls back to the pre-IR skeleton heuristic:
  finite-verb skeleton on line N + אֵת marker starting line N+1. Fallback
  findings are always REVIEW-REQUIRED (skel heuristic has known FPs).

Architectural constraint:
  No te'amim glyph triggers anywhere. The IR exposes morph + role +
  frame semantics, none of which are accent-derived.

Output format:
    [MALFORMED]  file:line_number  rule  brief description

Exit code: 0 if zero violations, 1 if violations found, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/syntax/validate_verb_object_bond.py
    PYTHONIOENCODING=utf-8 py -3 validators/syntax/validate_verb_object_bond.py --book genesis
    PYTHONIOENCODING=utf-8 py -3 validators/syntax/validate_verb_object_bond.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/syntax/validate_verb_object_bond.py --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants — collapsed two-tier layout: v1/he-baseline + v2/heb
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files"  / "v2" / "heb"

# Make _shared importable
sys.path.insert(0, str(REPO_ROOT / "validators"))
from _shared import macula_constituents as MC  # noqa: E402

# Speech-verb lemmas (from Macula lowfat). The canonical Hebrew speech-event
# verbs whose wayyiqtol forms license H5b speech-intro / quoted-content splits.
# Replaces the prior orthographic BARE_SPEECH_VERB_SKELETONS list with a
# lemma-based check against IR Token.lemma — robust to spelling variants.
SPEECH_VERB_LEMMAS = {
    "אָמַר", "דָּבַר", "קָרָא", "עָנָה", "צִוָּה",
    "סִפֵּר", "נָגַד", "שָׁאַל", "צָעַק", "זָעַק",
}

# Clause-introducing complementizers — when an A1 token sits inside a
# content-clause beginning with one of these, the cross-line break is
# H5b/H10-licensed (clausal A1, not stranded NP-A1). Lemma-based.
CONTENT_CLAUSE_COMPLEMENTIZERS = {
    "כִּי",   # כִּי — that / because
    "אֲשֶׁר",  # אֲשֶׁר — that / which
    "אִם",    # אִם — if / whether
    "פֶּן",   # פֶּן — lest
    "ל",      # לְ + infinitive construct (purpose/complement)
}

# ---------------------------------------------------------------------------
# Hebrew Unicode constants
# ---------------------------------------------------------------------------

# Niqqud / cantillation marks to strip when isolating consonant skeleton
# U+0591–U+05C7: Hebrew cantillation and points
HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"  # ׃

# Maqqef (orthographic word-joiner)
MAQQEF = "־"     # ־

# Paseq (vertical bar disjunction)
PASEQ = "׀"      # ׀


def strip_points(token: str) -> str:
    """Return token with niqqud and te'amim stripped (consonant skeleton only)."""
    return HEBREW_POINTS_RE.sub("", token)


# ---------------------------------------------------------------------------
# Skeleton-heuristic constants (fallback path when lowfat alignment absent)
# ---------------------------------------------------------------------------

# Wayyiqtol prefix bytes (consonant skeleton) — cover ו+י, ו+ת, ו+א, ו+נ
WAYYIQTOL_PREFIXES = ("וי", "ות", "וא", "ונ")

# High-frequency finite-verb skeletons used by the skel fallback.
# Bias toward over-detection (conservative: rather fire a false positive
# than miss a real violation) — same strategy as the pre-IR validator.
FINITE_VERB_SKELETONS = {
    "אמר", "אמרה", "אמרו", "אמרתי", "אמרת", "אמרנו", "אמרתם",
    "ראה", "ראתה", "ראו", "ראיתי", "ראית", "ראינו",
    "שמע", "שמעה", "שמעו", "שמעתי", "שמענו",
    "ידע", "ידעה", "ידעו", "ידעתי", "ידעת", "ידענו",
    "ברא", "ברך", "ברכה", "ברכו",
    "הלך", "הלכה", "הלכו", "הלכתי",
    "נתן", "נתנה", "נתנו", "נתתי",
    "עשה", "עשתה", "עשו", "עשיתי",
    "היה", "היתה", "היו", "הייתי",
    "בא", "באה", "באו", "באתי",
    "קם", "קמה", "קמו",
    "לקח", "לקחה", "לקחו",
    "כתב", "כתבה", "כתבו",
    "מצא", "מצאה", "מצאו",
    "נשא", "נשאה", "נשאו",
    "ישב", "ישבה", "ישבו",
    "עבר", "עברה", "עברו",
    "אכל", "אכלה", "אכלו",
    "עלה", "עלתה", "עלו",
    "ירד", "ירדה", "ירדו",
    "צוה", "צותה", "צוו",
    "דבר", "דברה", "דברו",
    "יאמר", "תאמר", "יאמרו", "ישמע", "תשמע",
    "יעשה", "תעשה", "יעשו",
    "ילך", "תלך", "ילכו",
    "יתן", "תתן", "יתנו",
    "יקח", "תקח", "יקחו",
    "ישב", "תשב", "ישבו",
    "ידע", "תדע", "ידעו",
}


def _looks_like_finite_verb(bare: str) -> bool:
    """Heuristic: does bare consonant skeleton look like a finite verb?

    Conservative bias: over-detect rather than under-detect.
    Used only in the skel-fallback path when lowfat alignment is absent.
    """
    if not bare:
        return False
    if bare in FINITE_VERB_SKELETONS:
        return True
    # Wayyiqtol prefix (וי, ות, וא, ונ)
    if bare.startswith(WAYYIQTOL_PREFIXES) and len(bare) >= 4 and bare != "ויהוה":
        return True
    # Maqqef-internal — check each segment
    if MAQQEF in bare:
        for part in bare.split(MAQQEF):
            if not part:
                continue
            if part in FINITE_VERB_SKELETONS:
                return True
            if part.startswith(WAYYIQTOL_PREFIXES) and len(part) >= 4:
                return True
    # Qatal-suffix sniff
    for suf in ("תי", "תם", "תן", "נו"):
        if bare.endswith(suf) and len(bare) >= 4:
            return True
    return False


def _line_contains_finite_verb_skel(line: str) -> bool:
    """Skel-fallback: True if any content token on `line` looks like a finite verb."""
    for tok in content_tokens(line):
        bare = strip_points(tok).rstrip(SOF_PASUQ)
        if _looks_like_finite_verb(bare):
            return True
    return False


def _line_starts_with_et_marker_skel(line: str) -> bool:
    """Skel-fallback: True if the first content token is the DO-marker אֵת.

    Skel-only — cannot distinguish אֵת (DO marker) from אַתְּ (2fs pronoun);
    that known FP class is why fallback findings are always REVIEW-REQUIRED.

    Note: HEBREW_POINTS_RE (which strip_points uses) includes maqqef (U+05BE),
    so אֶת־X becomes bare 'אתX'. We check: bare exactly 'את', or bare starts
    with 'את' followed by more consonants (maqqef-joined construction), or the
    raw token contains MAQQEF preceded by 'את'.
    """
    toks = content_tokens(line)
    if not toks:
        return False
    raw = toks[0]
    bare = strip_points(raw)
    # Exact match: bare אֵת stripped to 'את'
    if bare == "את":
        return True
    # Maqqef-joined: bare is 'אתX...' (maqqef stripped by strip_points)
    # Also catches raw-token MAQQEF check
    if bare.startswith("את") and len(bare) > 2:
        return True
    # Defensive: check raw token for MAQQEF after את
    if MAQQEF in raw:
        head = raw.split(MAQQEF, 1)[0]
        head_bare = strip_points(head)
        if head_bare == "את":
            return True
    return False


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
# Token helpers (line-level — for sense-line text manipulation only)
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


# ---------------------------------------------------------------------------
# IR-driven guards
# ---------------------------------------------------------------------------

def verb_is_speech_verb(verb: "MC.Token") -> bool:
    """Guard B (H5b speech-frame): suppress when the verb under inspection
    IS itself a speech-event verb. Its 'A1' is the entire quoted content,
    which is licensed to span multiple sense-lines per H5b discipline.

    Note: this is a per-verb guard, not per-line. Other (non-speech) finite
    verbs on the same line — e.g., the inner verbs of the quoted content —
    are still subject to verb-object-bond checking.

    NB: The clausal-A1 guard ALREADY catches most speech-verb cases (a
    speech verb's A1 is the inner clause head, role='v'). This guard is
    a backstop for speech verbs whose A1 is encoded as a content NP rather
    than as a verb-headed clause.
    """
    return verb.is_finite_verb and verb.lemma in SPEECH_VERB_LEMMAS


def a1_is_clausal(verb: "MC.Token", a1_tokens: list["MC.Token"]) -> bool:
    """Clausal-A1 license-guard: A1 is a clausal complement (content-clause
    headed by a complementizer, or A1 IS a clause-head verb), not a stranded
    NP-A1 — the split is H5b/H10-licensed.

    A complementizer between the verb and A1 means A1 is the content-clause
    served by that complementizer. A complementizer ALSO containing the verb
    (i.e., verb is INSIDE the complementizer-clause) does not license A1 —
    that's just the inner clause's normal verb-object bond.
    """
    for a1 in a1_tokens:
        # Case A: A1 IS a verb head — clause-as-object
        if a1.role == "v":
            return True
        # Case B: an enclosing complementizer-clause separates verb and A1
        cur = a1.parent_constituent
        while cur is not None:
            if cur.is_clause and cur.tokens:
                first_lemma = cur.tokens[0].lemma
                if first_lemma in CONTENT_CLAUSE_COMPLEMENTIZERS:
                    cl_token_ids = {t.xml_id for t in cur.tokens}
                    if verb.xml_id not in cl_token_ids:
                        return True
                    # Verb is inside; this complementizer doesn't license A1.
                    # (Don't break — a higher ancestor might still license it.)
            cur = cur.parent
    return False


def a1_has_relp_ancestor(a1_token: "MC.Token") -> bool:
    """STRONG guard: A1 token is inside a restrictive relative clause (wg_class='relp').

    Restrictive-relative-modified objects ('the land that I will show you')
    are a known false-positive class: the object is genuinely stranded, but
    the relative clause's content may legitimately span lines. These are
    ambiguous enough to remain REVIEW-REQUIRED.
    """
    cur = a1_token.parent_constituent
    while cur is not None:
        if cur.wg_class == "relp":
            return True
        cur = cur.parent
    return False


def a1_is_all_nominal(stranded: list["MC.Token"]) -> bool:
    """STRONG guard: all stranded A1 tokens are nominal (noun/pronoun/suffix/particle).

    Returns False if any A1 token is verbal (pos='verb'), which catches
    infinitive-construct / infinitive-absolute A1 ('cease + to do evil') —
    VP-complement splits that are borderline-licensed and should stay REVIEW.
    The clausal-A1 guard already handles role='v' (clause-head A1); this
    guard catches verbal-pos tokens with other roles (e.g., infinitives
    assigned role='o' or role=None).
    """
    for a in stranded:
        if a.pos == "verb":
            return False
        if a.role == "v":
            return False
    return True


def n_plus_1_opens_wayyiqtol(n_plus_1_tokens: list["MC.Token"]) -> bool:
    """STRONG guard: N+1 line opens with a wayyiqtol finite verb.

    A wayyiqtol opening N+1 signals a new sequential-narrative clause head,
    not a continuation of the verb-object bond on N. These are REVIEW-REQUIRED
    because the stranded 'A1' may actually be an adverbial complement resolved
    across the clause boundary by the parser (frame-arg recall artifact).
    Skips leading conjunction tokens before inspecting the first lexical token.
    """
    for t in n_plus_1_tokens:
        if not t.text.strip():
            continue
        if t.is_conjunction:
            continue
        return t.is_wayyiqtol
    return False


def line_opens_with_coordinated_object(n_plus_1_tokens: list["MC.Token"]) -> bool:
    """Coordinated-object license-guard.

    Hebrew colometry routinely splits multi-object verb constructions onto
    successive sense-lines, with each subsequent object opening with וְאֵת
    (waw + DO marker) or וְ + bare object. This is canonical editorial
    practice, NOT a stranded-A1 violation.

    Detection: line N+1 begins with conjunction ו (lemma 'ו' or 'וְ')
    immediately followed by an את DO marker (lemma 'אֵת', pos 'particle').
    Or: line N+1 begins with conjunction ו immediately followed by a bare
    object token (role='o' or NP-head with implicit DO).
    """
    if not n_plus_1_tokens:
        return False
    # Skip leading non-content tokens (rare; defensive)
    i = 0
    while i < len(n_plus_1_tokens) and not n_plus_1_tokens[i].text.strip():
        i += 1
    if i >= len(n_plus_1_tokens):
        return False
    first = n_plus_1_tokens[i]
    if not first.is_conjunction:
        return False
    # Look for an את-marker or a clear object NP head as the next non-empty token
    for t in n_plus_1_tokens[i + 1:]:
        if not t.text.strip():
            continue
        # Case A: explicit וְאֵת construction
        if t.lemma == "אֵת" and t.is_particle:
            return True
        # Case B: וְ + object-role NP head (object follows directly)
        if t.role in ("o", "o2"):
            return True
        # Stop at the first content token; we only care about the immediate post-conj token
        break
    return False


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

def scan_file(path: Path) -> list[dict]:
    """IR-driven scan for verb-A1 (direct object) stranded across sense-lines.

    For each verse, walk sense-lines pairwise (N → N+1). For each finite verb
    on line N, check whether any of its frame-arg A1 tokens (per Macula
    lowfat constituent-tree) appears on line N+1. If so, and no guard fires,
    emit a violation.

    Fallback path: when the Macula IR cannot resolve tokens for a verse
    (unknown book slug, missing lowfat XML, empty alignment), falls back to
    the pre-IR skeleton heuristic: finite-verb skel on N + אֵת-marker on N+1.
    Fallback findings are always REVIEW-REQUIRED (skel cannot disambiguate
    אֵת from אַתְּ).
    """
    violations: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    book_slug = book_name_from_path(path)
    chapter_from_file = chapter_from_path(path)
    verses = partition_into_verses(lines)

    for ch, vs, indices in verses:
        if ch is None or vs is None:
            continue
        # Sense-lines in this verse, in source order, dropping skippables
        sense_indices = [i for i in indices if not is_skippable(lines[i])]
        if len(sense_indices) < 2:
            continue

        # --- IR path: attempt to load lowfat verse tokens ---
        verse_tokens: list["MC.Token"] = []
        ir_available = False
        try:
            verse_tokens = MC.get_verse_tokens(book_slug, ch, vs)
            if verse_tokens:
                ir_available = True
        except (FileNotFoundError, ValueError, KeyError):
            pass

        if ir_available:
            # ---- IR-driven detection ----
            # Greedy-align each sense-line to the verse's tokens
            line_to_tokens: dict[int, list["MC.Token"]] = {}
            cursor = 0
            for idx in sense_indices:
                matched, cursor = MC.match_sense_line_tokens(
                    verse_tokens, lines[idx], start_idx=cursor
                )
                line_to_tokens[idx] = matched

            # Walk pairwise (N, N+1)
            for k in range(len(sense_indices) - 1):
                line_n_idx = sense_indices[k]
                line_n_plus_1_idx = sense_indices[k + 1]
                line_n = lines[line_n_idx]
                line_n_plus_1 = lines[line_n_plus_1_idx]

                n_tokens = line_to_tokens.get(line_n_idx, [])
                n_plus_1_tokens = line_to_tokens.get(line_n_plus_1_idx, [])
                if not n_tokens or not n_plus_1_tokens:
                    continue

                n_plus_1_ids = {t.xml_id for t in n_plus_1_tokens}

                # Find finite verbs on line N whose A1 reaches into line N+1
                for verb in n_tokens:
                    if not verb.is_finite_verb:
                        continue
                    a1_tokens = verb.frame_args.get("A1") or []
                    if not a1_tokens:
                        continue
                    stranded = [a1 for a1 in a1_tokens if a1.xml_id in n_plus_1_ids]
                    if not stranded:
                        continue

                    # --- Guard B: H5b speech-frame (per-verb, not per-line) ---
                    if verb_is_speech_verb(verb):
                        continue

                    # --- Guard: clausal-A1 license (כִּי / אֲשֶׁר / inf-construct) ---
                    if a1_is_clausal(verb, stranded):
                        continue

                    # --- Guard: coordinated-object enumeration (וְאֵת / וְ + obj) ---
                    if line_opens_with_coordinated_object(n_plus_1_tokens):
                        continue

                    # --- Severity ---
                    # Superseded by 2026-05-04 methodology audit: poetic register
                    # removed as STRONG-promotion gate. Verb-object stranding is a
                    # clause-nucleus syntactic phenomenon that applies in any register;
                    # IR features (frame-args A1, no relp ancestor, no wayyiqtol-N+1)
                    # already discriminate TP/FP without needing register input.
                    if (
                        a1_is_all_nominal(stranded)
                        and not any(a1_has_relp_ancestor(a) for a in stranded)
                        and not n_plus_1_opens_wayyiqtol(n_plus_1_tokens)
                    ):
                        # All STRONG criteria met:
                        # - all stranded A1 tokens are nominal (not verbal)
                        # - no A1 token is inside a restrictive relative clause
                        # - N+1 does not open with a new wayyiqtol clause head
                        severity = "STRONG-MERGE-CANDIDATE"
                    else:
                        # Ambiguity present: restrictive relative, infinitive A1,
                        # or competing wayyiqtol clause on N+1
                        severity = "REVIEW-REQUIRED"

                    prior_text = line_n.strip()
                    next_text = line_n_plus_1.strip()

                    violations.append({
                        "file": path.name,
                        "file_path": path,
                        "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                        "line_num": line_n_idx + 1,
                        "next_line_num": line_n_plus_1_idx + 1,
                        "next_line": next_text,
                        "severity": severity,
                        "book": book_slug,
                        "chapter": ch,
                        "verse": vs,
                        "prior_line": prior_text,
                        "rule": "L1.5/M2",
                        "brief": (
                            f"finite verb {verb.text!r} A1={[a.text for a in stranded]!r} "
                            f"stranded across sense-lines — {prior_text} // {next_text}"
                        ),
                    })
                    # One finding per (line_n, line_n_plus_1) pair
                    break

        else:
            # ---- Skel fallback: no lowfat alignment for this verse ----
            # Pre-IR heuristic: finite-verb skel on N + אֵת marker on N+1.
            # Always REVIEW-REQUIRED (skel cannot disambiguate אֵת vs אַתְּ).
            for k in range(len(sense_indices) - 1):
                line_n_idx = sense_indices[k]
                line_n_plus_1_idx = sense_indices[k + 1]
                line_n = lines[line_n_idx]
                line_n_plus_1 = lines[line_n_plus_1_idx]

                if not _line_contains_finite_verb_skel(line_n):
                    continue
                if not _line_starts_with_et_marker_skel(line_n_plus_1):
                    continue

                prior_text = line_n.strip()
                next_text = line_n_plus_1.strip()

                violations.append({
                    "file": path.name,
                    "file_path": path,
                    "file_rel": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                    "line_num": line_n_idx + 1,
                    "next_line_num": line_n_plus_1_idx + 1,
                    "next_line": next_text,
                    "severity": "REVIEW-REQUIRED",
                    "book": book_slug,
                    "chapter": ch,
                    "verse": vs,
                    "prior_line": prior_text,
                    "rule": "L1.5/M2",
                    "brief": (
                        f"[skel-fallback] finite verb + אֵת stranded across "
                        f"sense-lines — {prior_text} // {next_text}"
                    ),
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
        help="Restrict scan to one book folder name (e.g. 'genesis', 'jonah'). "
             "Default: all books in the target directory.",
    )
    parser.add_argument(
        "--v2",
        action="store_true",
        help="Scan v2/heb (editorial gold standard) instead of v1/he-baseline.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as a single JSON document to STDOUT instead of human-readable lines.",
    )
    args = parser.parse_args()

    base_dir = V2_DIR if args.v2 else V1_DIR
    tier_label = "v2/heb" if args.v2 else "v1/he-baseline"

    if not base_dir.exists():
        print(
            f"ERROR: {base_dir} not found. "
            f"Run the ingest/baseline scripts first.",
            file=sys.stderr,
        )
        sys.exit(2)

    # Collect files
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
        all_violations.extend(scan_file(path))

    exit_code = 1 if all_violations else 0

    # --- JSON output mode ---
    if args.json:
        findings = []
        for v in all_violations:
            findings.append({
                "file": v["file_rel"],
                "line": v["line_num"],
                "next_line": v["next_line_num"],
                "severity": v["severity"],
                "tag": v["severity"],
                "rule_id": "L1.5",
                "rule_short": "verb + אֵת stranded",
                "brief": v["brief"],
                "applied_action": "merge_with_next",
            })

        by_severity: dict[str, int] = {}
        by_severity_no_review: dict[str, int] = {}
        for f in findings:
            by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1
            if f["severity"] == "STRONG-MERGE-CANDIDATE":
                by_severity_no_review["STRONG"] = by_severity_no_review.get("STRONG", 0) + 1
            else:
                by_severity_no_review["REVIEW"] = by_severity_no_review.get("REVIEW", 0) + 1

        doc = {
            "validator": "validate_verb_object_bond",
            "rule": "Layer 1 L1.5 + Canon M2",
            "layer": 1,
            "book": args.book or "all",
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": findings,
            "summary": {
                "total_findings": len(findings),
                "by_severity": by_severity,
                "by_severity_no_review": by_severity_no_review,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output (default) ---
    print("=" * 72)
    print(f"Layer 1 L1.5 + Canon M2 — Verb-Object Bond validator")
    print(f"Tanakh {tier_label} corpus")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Violations    : {len(all_violations)}")
    print()

    # Breakdown by severity
    strong_count = sum(1 for v in all_violations if v["severity"] == "STRONG-MERGE-CANDIDATE")
    review_count = sum(1 for v in all_violations if v["severity"] == "REVIEW-REQUIRED")
    if strong_count or review_count:
        print(f"Breakdown:")
        print(f"  STRONG-MERGE-CANDIDATE: {strong_count}")
        print(f"  REVIEW-REQUIRED:        {review_count}")
        print()

    if all_violations:
        for v in all_violations:
            print(f"[MALFORMED]  {v['file']}:{v['line_num']}  {v['rule']}  {v['brief']}")
            print(f"    → next line ({v['next_line_num']}): {v['next_line'][:100]}")
            print()
    else:
        print("No violations found. Verb-object bonds are intact.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
