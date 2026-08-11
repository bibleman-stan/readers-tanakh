

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
Validate 1-method/canon Rule H16 — FEF Wayehi Protasis (IR-driven).

Rule H16 (1-method/canon §5 H16; Layer 3 editorial rule):
The Hebrew narrative construction וַיְהִי (wayyehi) + temporal/circumstantial
protasis + main clause is the canonical Front-End Frame (FEF). The wayyiqtol
of הָיָה introduces a temporal frame; the protasis sets the scene; the main
clause resolves.

  **Diagnostic:** the wayehi-protasis is held together as ONE atomic temporal
  frame regardless of length. The main clause that follows opens on its own line.

Three violation patterns are detected:

  STRONG-MERGE-CANDIDATE — protasis split: a line begins with וַיְהִי but the
    temporal frame continues onto the next line(s) without the main clause having
    started. The frame must be held together as one colon.

  STRONG-SPLIT-CANDIDATE — protasis collapsed with main clause: a line
    containing וַיְהִי also contains the main clause's wayyiqtol (or other
    finite) verb on the SAME line. The protasis should be on its own colon;
    the main clause should open the next line.

  REVIEW-REQUIRED — ambiguous case: a וַיְהִי line is present but the validator
    cannot confidently determine whether the main clause has started (e.g., line
    ends without sof pasuq, next line's first word is ambiguous — could be
    continuation of protasis or start of main clause).

Wayyehi detection (post-2026-05-05 Macula pivot):
  Replaces the consonant-skeleton trigger ('ויהי' bare match at line-initial
  position) with a lemma+aspect IR check: `Token.lemma == "הָיָה"` AND
  `Token.is_wayyiqtol`. The wayehi may be the first OR second IR token on the
  line, since lowfat splits the conjunction `וַ` from the verb stem `יְהִי`
  into separate <w> elements. We accept either position-0 or position-1 (after
  a leading conjunction).

Second-verb detection (STRONG-SPLIT-CANDIDATE):
  Replaces the surface heuristic `is_wayyiqtol_candidate` (bare token starts
  with 'וי' + length ≥ 4) with `Token.is_finite_verb`. We exclude the wayehi
  itself (lemma הָיָה + wayyiqtol), and skip subsequent lemma-הָיָה wayyiqtol
  tokens (those are coordinated existential-style "and X became Y" cases like
  Gen 1:5's וַיְהִי עֶרֶב וַיְהִי בֹקֶר, not main-clause closure).

Existential ויהי exclusion (not a FEF):
  Standalone וַיְהִי functioning as "there was/became X" (existential) is NOT
  a FEF protasis. Lemma-based heuristic (mirrors the OLD validator's
  `is_fef_token` permissive shape, ported from bare-skel matching to IR
  lemma matching). FEF signals on the wayehi line:
    - complementizer lemma (כִּי / כַּאֲשֶׁר / כְּ-prefix)
    - recipient-PP lemma (אֶל) — prophetic-formula speech-event reception
    - בְּ + closed-list temporal noun (יוֹם / עֵת / לַיְלָה / שָׁנָה)
  Augmented by an IR clause-rule check: when the wayehi's enclosing clause
  has rule 'V-S' (no PP/temporal-frame complement), treat as existential.

Protasis-split detection (STRONG-MERGE-CANDIDATE):
  A line starts with ויהי and ends WITHOUT sof pasuq. The next non-blank,
  non-verse-ref line exists and is not the start of a new verse. This pattern
  represents the protasis split across multiple lines.

Exit code: 0 if zero findings, 1 if findings present, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_wayehi_protasis.py
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_wayehi_protasis.py --book 32-jonah
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_wayehi_protasis.py --v2
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_wayehi_protasis.py --json
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_wayehi_protasis.py --verbose
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants — collapsed two-tier layout: v1/he-baseline + v2/heb
# ---------------------------------------------------------------------------
REPO_ROOT = _find_repo_root()
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files"  / "v2" / "heb"

# ---------------------------------------------------------------------------
# IR helpers
# ---------------------------------------------------------------------------
sys.path.insert(0, str(REPO_ROOT / "5-machinery/validators"))
from _shared import macula_constituents as MC  # noqa: E402

# ---------------------------------------------------------------------------
# Hebrew Unicode helpers (still needed for line-level pre-IR triage and
# sof-pasuq detection)
# ---------------------------------------------------------------------------

# Hebrew points range (U+0591–U+05C7): cantillation + niqqud
HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")

# Sof pasuq U+05C3 — verse-end marker
SOF_PASUQ = "׃"

# Maqqef U+05BE
MAQQEF = "־"

# Consonant skeleton for וַיְהִי — used only as a cheap pre-IR triage filter
# at line-initial position.
WAYEHI_SKELETON = "ויהי"


def strip_points(token: str) -> str:
    """Return token with all niqqud and te'amim stripped."""
    return HEBREW_POINTS_RE.sub("", token)


# ---------------------------------------------------------------------------
# Existential-filter lemma sets (IR-friendly, behavior-preserving)
#
# These mirror the OLD validator's `is_fef_token` permissive check, ported to
# IR lemma matching. The OLD logic was:
#   - any כ-prefix token (length ≥ 2)         → FEF (catches כִּי/כַּאֲשֶׁר/כִּזְרֹחַ/etc.)
#   - any אֶל-prefix token (length ≥ 3)       → FEF (recipient marker)
#   - closed-list ב-temporal skel             → FEF (בִּימֵי, בָּעֵת, ...)
#
# Translating to IR:
#   - lemma in TEMPORAL_COMPLEMENTIZER_LEMMAS → FEF (כִּי / כַּאֲשֶׁר / כְּ-prefix)
#   - lemma == "אֶל"                         → FEF (recipient PP marker)
#   - בְּ preposition followed by lemma in B_TEMPORAL_NOUN_LEMMAS → FEF
# ---------------------------------------------------------------------------

# Complementizer lemmas matched against IR Token.lemma. Mirrors the OLD
# is_fef_token's כ-prefix permissive heuristic by enumerating the closed set
# of lemmas the prefix surfaces with in practice.
TEMPORAL_COMPLEMENTIZER_LEMMAS = frozenset({
    "כִּי",       # when / that — k-prefix complementizer
    "כַּאֲשֶׁר",  # when / as — k-prefix complementizer
    "כְּ",        # k-prefix preposition (כִּזְרֹחַ etc. — k + infinitive)
})

# Recipient-PP lemma — אֶל marks the recipient in prophetic speech-event
# reception formulas (e.g., Jonah 1:1 "the word of YHWH came TO Jonah").
RECIPIENT_LEMMAS = frozenset({"אֶל"})

# Closed-list temporal nouns the OLD `B_TEMPORAL` skel set covered.
# IR-port: the surface tokens like בִּימֵי / בָּעֵת decompose into the
# preposition `בְּ` (lemma) + a noun (lemma in this set). Detection requires
# observing this pattern (preposition + noun, with optional intervening
# definite article, which lowfat splits as a separate <w>).
B_TEMPORAL_NOUN_LEMMAS = frozenset({
    "יוֹם",       # day → בִּימֵי / בְּיוֹם (in the days of, on the day of)
    "עֵת",        # time → בָּעֵת
    "לַיְלָה",    # night → בַּלַּיְלָה
    "שָׁנָה",     # year → בִּשְׁנַת
})

# Verse-reference line pattern: optional word + digits:digits
VERSE_REF_RE = re.compile(r"^(\S+\s+)?\d+:\d+\s*$")

# Bare verse-ref pattern (used by _partition_into_verses)
_VERSE_REF_BARE = re.compile(r"^\d+:\d+\s*$")


# ---------------------------------------------------------------------------
# Verse-grouping helpers
# ---------------------------------------------------------------------------

def _partition_into_verses(lines: list[str]) -> list[tuple[int, list[tuple[int, str]]]]:
    """Partition file lines into per-verse groups.

    Returns list of (verse_num, [(1-based_line_no, line_text), ...]) tuples.
    """
    groups: list[tuple[int, list[tuple[int, str]]]] = []
    cur_verse: int | None = None
    cur_lines: list[tuple[int, str]] = []
    for i, raw in enumerate(lines):
        line_no = i + 1
        s = raw.strip()
        m = _VERSE_REF_BARE.match(s)
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
# Line-level helpers
# ---------------------------------------------------------------------------

def is_skippable(line: str) -> bool:
    """Return True for blank lines and verse-reference-only lines."""
    s = line.strip()
    if not s:
        return True
    if VERSE_REF_RE.match(s):
        return True
    return False


def has_sof_pasuq(line: str) -> bool:
    """Return True if line (or its last token) contains sof pasuq."""
    return SOF_PASUQ in line


def line_starts_with_wayehi_skel(line: str) -> bool:
    """Cheap pre-IR triage: does the line's first token match the consonant
    skeleton 'ויהי'?

    This is a coarse filter to skip non-candidate lines without paying the IR
    alignment cost. The authoritative FEF detection (lemma+aspect via IR) runs
    only on lines that pass this gate.
    """
    tokens = line.split()
    if not tokens:
        return False
    return strip_points(tokens[0]) == WAYEHI_SKELETON


# ---------------------------------------------------------------------------
# Skeleton-heuristic fallback helpers (used when IR alignment is unavailable,
# e.g. synthetic fixture text with no Macula lowfat coverage).
# ---------------------------------------------------------------------------

# Consonant-skeleton prefixes that signal a FEF complementizer (כ-prefix)
_K_PREFIX_SKEL = "כ"

# Consonant-skeleton prefix for recipient-PP marker (אל)
_AL_PREFIX_SKEL = "אל"

# Consonant skeletons of ב + closed-list temporal nouns (בימי, ביום, בעת,
# בלילה, בשנת — matches the OLD B_TEMPORAL skel set).
_B_TEMPORAL_SKELS = frozenset({"ביום", "בימי", "בעת", "בלילה", "בשנת"})

# ב-prefix (matches בְּ / בַּ / בִּ etc. at token start when stripping points)
_B_PREFIX_SKEL = "ב"

# Closed-list temporal noun skeletons (preceded by ב-prefix token)
_TEMPORAL_NOUN_SKELS = frozenset({"יום", "ימי", "עת", "לילה", "שנת", "שנה"})


def _skel_has_fef_signal(line_tokens_raw: list[str]) -> bool:
    """Skeleton-heuristic FEF-signal detector.

    Mirrors is_fef_token's permissive heuristic from the pre-IR validator:
      - any token (after the wayehi) whose consonant skeleton starts with כ
        (length ≥ 2) → complementizer signal
      - any token whose consonant skeleton starts with אל (length ≥ 3)
        → recipient-PP signal
      - skeleton starts with ב and is in B_TEMPORAL_SKELS, OR
        ב-prefix token immediately followed by a temporal-noun-skel token
        → ב + temporal-noun signal
    """
    # Skip index 0 (the wayehi itself)
    for i, raw in enumerate(line_tokens_raw[1:], start=1):
        skel = strip_points(raw).replace(MAQQEF, "")
        if len(skel) >= 2 and skel.startswith(_K_PREFIX_SKEL):
            return True
        if len(skel) >= 3 and skel.startswith(_AL_PREFIX_SKEL):
            return True
        if skel in _B_TEMPORAL_SKELS:
            return True
        # ב-prefix + immediately following temporal noun
        if skel == _B_PREFIX_SKEL and i + 1 < len(line_tokens_raw):
            next_skel = strip_points(line_tokens_raw[i + 1]).replace(MAQQEF, "")
            if next_skel in _TEMPORAL_NOUN_SKELS:
                return True
    return False


def _skel_find_second_wayyiqtol(line_tokens_raw: list[str]) -> int:
    """Return index of the first wayyiqtol-candidate token AFTER the wayehi,
    or -1 if none.

    Heuristic: token starts with 'וי' and length ≥ 4 (bare skeleton),
    AND is not 'ויהי' itself (coordinated existential).
    """
    for i, raw in enumerate(line_tokens_raw[1:], start=1):
        skel = strip_points(raw).replace(MAQQEF, "")
        if (len(skel) >= 4
                and skel.startswith("וי")
                and skel != WAYEHI_SKELETON):
            return i
    return -1


def _skel_is_existential(line_tokens_raw: list[str],
                          next_line_tokens_raw: list[str]) -> bool:
    """Skeleton heuristic: is this a bare existential ויהי (not a FEF)?

    Conservative — returns True only when:
      1. No second wayyiqtol candidate on this line.
      2. No FEF-signal token on this line OR on the leading token of the next.
    """
    if _skel_find_second_wayyiqtol(line_tokens_raw) >= 0:
        return False
    if _skel_has_fef_signal(line_tokens_raw):
        return False
    # Check leading token(s) of next line for recipient-PP or complementizer
    for raw in next_line_tokens_raw[:2]:
        skel = strip_points(raw).replace(MAQQEF, "")
        if len(skel) >= 3 and skel.startswith(_AL_PREFIX_SKEL):
            return False
        if len(skel) >= 2 and skel.startswith(_K_PREFIX_SKEL):
            return False
    return True


# ---------------------------------------------------------------------------
# IR-driven detection helpers
# ---------------------------------------------------------------------------

def find_wayehi_token(line_tokens: list["MC.Token"]) -> int:
    """Return index of the wayehi (lemma הָיָה + wayyiqtol) IR token at the
    head of the line, or -1 if not present at line-initial position.

    The wayehi may be at index 0 (rare) or index 1 (normal — when a leading
    conjunction `וַ` has been split into its own <w> token by lowfat). We
    accept positions 0 and 1; anywhere later is mid-line, not a FEF opener.
    """
    for i in (0, 1):
        if i >= len(line_tokens):
            break
        t = line_tokens[i]
        if t.lemma == "הָיָה" and t.is_wayyiqtol:
            return i
    return -1


def find_second_finite_verb(line_tokens: list["MC.Token"],
                             wayehi_idx: int) -> int:
    """Return index of a finite verb AFTER the wayehi that signals a
    main-clause boundary, or -1 if none.

    Excludes:
      - The wayehi itself (caller passes its index).
      - Subsequent lemma-הָיָה wayyiqtol tokens (e.g., Gen 1:5
        `וַיְהִי עֶרֶב וַיְהִי בֹקֶר` — coordinated existential, not a
        main-clause boundary).
      - Infinitives, participles (not finite).
    """
    for j in range(wayehi_idx + 1, len(line_tokens)):
        t = line_tokens[j]
        if not t.is_finite_verb:
            continue
        # Skip a coordinated wayehi (lemma הָיָה + wayyiqtol again)
        if t.lemma == "הָיָה" and t.is_wayyiqtol:
            continue
        return j
    return -1


def line_has_fef_signal(line_tokens: list["MC.Token"],
                         wayehi_idx: int) -> bool:
    """IR-based FEF-signal detector (behavior-preserving port of OLD
    is_fef_token's permissive heuristic).

    Looks for any of the following AFTER the wayehi token:
      - Complementizer lemma (כִּי / כַּאֲשֶׁר / כְּ-prefix)
      - Recipient lemma (אֶל — prophetic-formula recipient marker)
      - בְּ preposition immediately followed by a closed-list temporal noun
        (יוֹם / עֵת / לַיְלָה / שָׁנָה). Mirrors the OLD B_TEMPORAL skel
        check; deliberately does NOT fire for מִן-headed PPs (e.g.,
        מִקֵּץ יָמִים — preserves OLD behavior of treating those as
        existential and skipping).

    The OLD validator's is_fef_token did NOT flag מִן-headed PPs as FEF
    signals. Behavior-preserving port: match that scope exactly.
    """
    rest = line_tokens[wayehi_idx + 1:]
    for i, t in enumerate(rest):
        if t.lemma in TEMPORAL_COMPLEMENTIZER_LEMMAS:
            return True
        if t.lemma in RECIPIENT_LEMMAS:
            return True
        # בְּ + closed-list temporal noun pattern (with optional definite
        # article between)
        if t.lemma == "בְּ" and i + 1 < len(rest):
            for j in range(i + 1, min(i + 4, len(rest))):
                nxt = rest[j]
                if nxt.lemma in B_TEMPORAL_NOUN_LEMMAS:
                    return True
                # Allow definite article between preposition and noun
                if nxt.lemma == "הַ":
                    continue
                # Any other token type → not the בְּ + temporal-noun pattern
                break
    return False


def wayehi_clause_signals_existential(wayehi_token: "MC.Token") -> bool:
    """IR clause-rule check: does the wayehi's enclosing clause have shape
    'V-S' (verb + subject) with NO PP/temporal-frame complement?

    A clause rule like 'V-S' (Gen 1:5 evening/morning) is the canonical
    existential pattern: ויהי + bare subject NP. A clause rule like 'V-PP'
    (Ruth 1:1) or 'V-S-PP' (Jonah 1:1 — ויהי + word-of-YHWH + recipient PP)
    is NOT bare existential.

    Returns True only when the clause is unambiguously existential (V-S with
    no PP/CL). When ambiguous (no IR clause), returns False — the lemma-level
    FEF-signal check handles those cases.
    """
    cur = wayehi_token.parent_constituent
    while cur is not None:
        if cur.is_clause and cur.wg_rule:
            rule = cur.wg_rule
            # Pure V-S → existential
            if rule == "V-S":
                return True
            # V-S followed by O/Pred (non-PP, non-CL) — still existential
            # in shape (e.g., "and X became Y")
            if rule.startswith("V-S-") and "PP" not in rule and "CL" not in rule:
                return True
            return False
        cur = cur.parent
    return False


def is_existential_wayehi_ir(line_tokens: list["MC.Token"],
                              wayehi_idx: int,
                              next_line_tokens: list["MC.Token"]) -> bool:
    """IR-based existential check (behavior-preserving port of OLD
    is_existential_wayehi).

    Conservative — returns True (skip the line as existential) only when:
      1. There is no second finite verb on the line (would be STRONG-SPLIT
         territory; let caller handle).
      2. No FEF-signal lemmas appear on the current line OR on the leading
         tokens of the next line.
      3. The wayehi's IR clause rule does not signal a temporal/PP frame
         (the V-S clause-rule check is the IR-driven backstop).

    When the wayehi clause has a PP frame OR any FEF lemma signal is
    present, returns False (treat as FEF — flag any split).
    """
    # 1. Second finite verb → defer to caller (STRONG-SPLIT)
    if find_second_finite_verb(line_tokens, wayehi_idx) >= 0:
        return False

    wayehi_token = line_tokens[wayehi_idx]

    # 2. Lemma-based FEF signal on current line
    if line_has_fef_signal(line_tokens, wayehi_idx):
        return False

    # 3. Lemma-based FEF signal on next line (split reception formula:
    #    the recipient PP starting the next line). The OLD validator checked
    #    `is_fef_token(next_line_bare[0])` — the FIRST bare-skel token of the
    #    next line. IR-port: walk a few leading tokens (the IR's split of
    #    prefix-conjunction means the first IR token may be `וַ`/`וְ`).
    if next_line_tokens:
        for t in next_line_tokens[:2]:
            if (t.lemma in TEMPORAL_COMPLEMENTIZER_LEMMAS
                    or t.lemma in RECIPIENT_LEMMAS):
                return False

    # 4. IR clause-rule check — definitively existential
    if wayehi_clause_signals_existential(wayehi_token):
        return True

    # 5. No FEF signals AND clause-rule check inconclusive → conservatively
    #    treat as existential (matches prior heuristic behavior).
    return True


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

CHAPTER_FILENAME_RE = re.compile(r"-(\d+)\.txt$", re.IGNORECASE)


def _chapter_for_path(path: Path) -> int:
    """Extract chapter number from filename (e.g., 'jonah-01.txt' → 1)."""
    m = CHAPTER_FILENAME_RE.search(path.name)
    if not m:
        # Defensive default; should not happen in production
        return 1
    return int(m.group(1))


def _ir_idx_to_raw_idx(line_tokens_ir: list["MC.Token"],
                        line_tokens_raw: list[str],
                        ir_idx: int) -> int:
    """Best-effort mapping from IR-token index back to raw-token index for
    diagnostic split_at.

    Strategy: walk raw tokens, accumulating their consonant skeletons in
    lock-step with the IR-token consonant skeletons up to ir_idx. When the
    accumulated raw-skel covers the IR-skel, return the current raw index.

    Because lowfat splits prefix-conjunctions and articles into their own
    <w>s, multiple IR tokens can correspond to one raw token. This mapping
    is approximate; the diagnostic value is the surface position, not exact
    token equivalence.
    """
    if ir_idx < 0 or ir_idx >= len(line_tokens_ir):
        return ir_idx
    target_skel = "".join(t.consonant_skel for t in line_tokens_ir[:ir_idx + 1])
    accum = ""
    for r_idx, raw in enumerate(line_tokens_raw):
        accum += MC.consonant_skel(raw)
        if len(accum) >= len(target_skel):
            return r_idx
    return len(line_tokens_raw) - 1


def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    """Scan one text file for Rule H16 FEF wayehi protasis violations
    (IR-driven, post-2026-05-05 Macula pivot).

    Per verse, build the IR token alignment via MC.match_sense_line_tokens
    (mirrors verb_object_bond and participial_speech_frame ports). For each
    sense-line beginning with the ויהי skeleton, run the lemma+aspect
    FEF-detection logic.
    """
    findings = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    book_slug = path.parent.name
    chapter_no = _chapter_for_path(path)
    verse_groups = _partition_into_verses(lines)

    # Per-verse IR alignment: line_no -> list[Token] for that sense-line.
    line_to_tokens: dict[int, list["MC.Token"]] = {}

    for verse_num, verse_numbered_lines in verse_groups:
        sense_lines = [
            (ln, raw) for ln, raw in verse_numbered_lines if not is_skippable(raw)
        ]
        if not sense_lines:
            continue

        try:
            verse_tokens = MC.get_verse_tokens(book_slug, chapter_no, verse_num)
        except (FileNotFoundError, ValueError, KeyError):
            verse_tokens = []
        if not verse_tokens:
            # No IR available — skip this verse (graceful no-op; no findings
            # emitted in absence of evidence). Aligns with the verb_object_bond
            # pattern of "IR primary, no fallback to skel-only when alignment
            # fails."
            continue

        cursor = 0
        for ln, raw in sense_lines:
            matched, cursor = MC.match_sense_line_tokens(
                verse_tokens, raw, start_idx=cursor)
            line_to_tokens[ln] = matched

    # Walk lines in source order; only process lines whose first token is
    # the consonant skeleton 'ויהי' (cheap pre-filter), then verify via IR.
    for i, line in enumerate(lines):
        if is_skippable(line):
            continue
        if not line_starts_with_wayehi_skel(line):
            continue

        line_no = i + 1  # 1-based
        line_tokens_raw = line.split()
        line_tokens_ir = line_to_tokens.get(line_no, [])

        if not line_tokens_ir:
            # IR alignment unavailable (e.g. synthetic fixture text with no
            # Macula lowfat coverage). Fall back to skeleton-heuristic detection
            # so that fixture tests and any unsupported books still fire correctly.
            next_line_content = ""
            next_line_num_fb: int | None = None
            for j in range(i + 1, len(lines)):
                if not is_skippable(lines[j]):
                    next_line_content = lines[j].strip()
                    next_line_num_fb = j + 1
                    break

            next_line_raw_tokens = next_line_content.split() if next_line_content else []

            if _skel_is_existential(line_tokens_raw, next_line_raw_tokens):
                continue

            second_verb_raw_idx = _skel_find_second_wayyiqtol(line_tokens_raw)
            if second_verb_raw_idx >= 0:
                main_verb_text = line_tokens_raw[second_verb_raw_idx]
                findings.append({
                    "file": path.name,
                    "file_path": path,
                    "line_num": line_no,
                    "tag": "STRONG-SPLIT-CANDIDATE",
                    "brief": (
                        f"wayehi protasis collapsed with main clause on same line "
                        f"— main-clause verb {main_verb_text!r} should open next line"
                        f" [skel-fallback]"
                    ),
                    "line": line.rstrip(),
                    "next_line": next_line_content,
                    "next_line_num": next_line_num_fb,
                    "split_at": second_verb_raw_idx,
                })
                continue

            if not has_sof_pasuq(line):
                if next_line_content:
                    next_first_bare = strip_points(
                        next_line_content.split()[0]) if next_line_content.split() else ""
                    if next_first_bare == WAYEHI_SKELETON:
                        findings.append({
                            "file": path.name,
                            "file_path": path,
                            "line_num": line_no,
                            "tag": "REVIEW-REQUIRED",
                            "brief": (
                                f"wayehi line without sof pasuq followed by another wayehi — "
                                f"ambiguous protasis boundary; editorial review required"
                                f" [skel-fallback]"
                            ),
                            "line": line.rstrip(),
                            "next_line": next_line_content,
                            "next_line_num": next_line_num_fb,
                            "split_at": None,
                        })
                    else:
                        findings.append({
                            "file": path.name,
                            "file_path": path,
                            "line_num": line_no,
                            "tag": "STRONG-MERGE-CANDIDATE",
                            "brief": (
                                f"wayehi protasis split across lines — "
                                f"merge continuation onto the wayehi line until main clause boundary"
                                f" [skel-fallback]"
                            ),
                            "line": line.rstrip(),
                            "next_line": next_line_content,
                            "next_line_num": next_line_num_fb,
                            "split_at": None,
                        })
                else:
                    findings.append({
                        "file": path.name,
                        "file_path": path,
                        "line_num": line_no,
                        "tag": "REVIEW-REQUIRED",
                        "brief": (
                            f"wayehi line without sof pasuq and no following content — "
                            f"anomalous; editorial review required [skel-fallback]"
                        ),
                        "line": line.rstrip(),
                        "next_line": "",
                        "next_line_num": None,
                        "split_at": None,
                    })
            # sof-pasuq line with FEF signal but no second wayyiqtol → self-contained; no violation
            continue

        # IR-confirmed wayehi position
        wayehi_idx = find_wayehi_token(line_tokens_ir)
        if wayehi_idx < 0:
            # Pre-filter false positive (e.g., a different ויהי-skeleton lemma)
            continue

        # --- Find the next non-skippable content line ---
        next_line_content = ""
        next_line_num: int | None = None
        for j in range(i + 1, len(lines)):
            if not is_skippable(lines[j]):
                next_line_content = lines[j].strip()
                next_line_num = j + 1
                break

        next_line_tokens_ir = (
            line_to_tokens.get(next_line_num, []) if next_line_num else []
        )

        # --- Existential exclusion (IR-driven) ---
        if is_existential_wayehi_ir(line_tokens_ir, wayehi_idx, next_line_tokens_ir):
            continue

        # --- Check for second finite verb on the SAME line (STRONG-SPLIT) ---
        second_verb_idx_ir = find_second_finite_verb(line_tokens_ir, wayehi_idx)

        if second_verb_idx_ir >= 0:
            main_verb_text = line_tokens_ir[second_verb_idx_ir].text
            split_at_raw = _ir_idx_to_raw_idx(
                line_tokens_ir, line_tokens_raw, second_verb_idx_ir)

            findings.append({
                "file": path.name,
                "file_path": path,
                "line_num": line_no,
                "tag": "STRONG-SPLIT-CANDIDATE",
                "brief": (
                    f"wayehi protasis collapsed with main clause on same line "
                    f"— main-clause verb {main_verb_text!r} should open next line"
                ),
                "line": line.rstrip(),
                "next_line": next_line_content,
                "next_line_num": next_line_num,
                "split_at": split_at_raw,
            })
            continue

        # --- Protasis-split detection (STRONG-MERGE-CANDIDATE) ---
        if not has_sof_pasuq(line):
            if next_line_content:
                next_first_raw = next_line_content.split()[0] if next_line_content.split() else ""
                next_first_bare = strip_points(next_first_raw)
                if next_first_bare == WAYEHI_SKELETON:
                    findings.append({
                        "file": path.name,
                        "file_path": path,
                        "line_num": line_no,
                        "tag": "REVIEW-REQUIRED",
                        "brief": (
                            f"wayehi line without sof pasuq followed by another wayehi — "
                            f"ambiguous protasis boundary; editorial review required"
                        ),
                        "line": line.rstrip(),
                        "next_line": next_line_content,
                        "next_line_num": next_line_num,
                        "split_at": None,
                    })
                else:
                    findings.append({
                        "file": path.name,
                        "file_path": path,
                        "line_num": line_no,
                        "tag": "STRONG-MERGE-CANDIDATE",
                        "brief": (
                            f"wayehi protasis split across lines — "
                            f"merge continuation onto the wayehi line until main clause boundary"
                        ),
                        "line": line.rstrip(),
                        "next_line": next_line_content,
                        "next_line_num": next_line_num,
                        "split_at": None,
                    })
            else:
                findings.append({
                    "file": path.name,
                    "file_path": path,
                    "line_num": line_no,
                    "tag": "REVIEW-REQUIRED",
                    "brief": (
                        f"wayehi line without sof pasuq and no following content — "
                        f"anomalous; editorial review required"
                    ),
                    "line": line.rstrip(),
                    "next_line": "",
                    "next_line_num": None,
                    "split_at": None,
                })
            continue

        # --- Line ends with sof pasuq, no second finite verb ---
        # Self-contained ויהי line; no violation. Fall through.

    return findings


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
        help="Scan v2/heb (editorial layer) instead of v1/he-baseline.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show next-line context for each finding.",
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
            f"Run the ingest/baseline 5-machinery/scripts first.",
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

    all_findings: list[dict] = []
    for path in files:
        all_findings.extend(scan_file(path, verbose=args.verbose))

    exit_code = 1 if all_findings else 0

    # --- JSON output mode ---
    if args.json:
        out_findings = []
        for v in all_findings:
            tag = v["tag"]
            if tag == "STRONG-MERGE-CANDIDATE":
                applied_action = "merge_with_next"
            elif tag == "STRONG-SPLIT-CANDIDATE":
                split_at = v.get("split_at")
                applied_action = (
                    f"split_at_position_{split_at}"
                    if split_at is not None
                    else "split_at_position_unknown"
                )
            else:
                applied_action = None

            out_findings.append({
                "file": str(v["file_path"].relative_to(REPO_ROOT)).replace("\\", "/"),
                "line": v["line_num"],
                "severity": "DEVIATION",
                "tag": tag,
                "rule_id": "H16",
                "rule_short": "FEF Wayehi Protasis",
                "brief": v["brief"],
                "next_line": v.get("next_line_num"),
                "applied_action": applied_action,
            })

        by_severity: dict[str, int] = {}
        by_tag: dict[str, int] = {}
        for f in out_findings:
            by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1
            by_tag[f["tag"]] = by_tag.get(f["tag"], 0) + 1

        doc = {
            "validator": "validate_wayehi_protasis",
            "rule": "Layer 3 colometry — Rule H16",
            "version": "2.0.0-ir",
            "layer": 3,
            "book": args.book or "all",
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": out_findings,
            "summary": {
                "total_findings": len(out_findings),
                "by_severity": by_severity,
                "by_tag": by_tag,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output (default) ---
    print("=" * 72)
    print(f"Rule H16 FEF Wayehi Protasis validator (IR-driven) — Tanakh {tier_label}")
    print(f"Reference: 1-method/canon §5 H16 (protasis own line; main clause fresh line)")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Findings      : {len(all_findings)}")

    by_tag_hr: dict[str, int] = {}
    for v in all_findings:
        by_tag_hr[v["tag"]] = by_tag_hr.get(v["tag"], 0) + 1
    if by_tag_hr:
        print()
        for tag, count in sorted(by_tag_hr.items()):
            print(f"  {tag}: {count}")
    print()

    if all_findings:
        for v in all_findings:
            print(
                f"[DEVIATION]  {v['file']}:{v['line_num']}  "
                f"H16/wayehi-protasis  {v['tag']}  {v['brief']}"
            )
            print(f"    {v['line'][:120]}")
            if args.verbose and v.get("next_line"):
                print(f"    → {v['next_line'][:120]}")
            print()
    else:
        print("No findings. Rule H16 FEF wayehi protasis is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
