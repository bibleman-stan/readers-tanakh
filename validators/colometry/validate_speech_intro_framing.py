#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate canon Rule H5 + Rule H5b — Direct-Speech Framing & Speech-Act
Announcement Default.

Path 1 canon revision (2026-05-02): the prior "short-framing-default merges"
stance is RETIRED. Per §5 H5b, a finite speech-act verb predicates a complete
speech-event; the quoted content is a distinct atomic thought (§1 SJ3 + §5.0
Propositional Completeness Test). The default is SPLIT between announcement
and content regardless of frame length. The previous merge-default conflated
informational completeness ("reader hasn't been told what was said yet") with
propositional completeness; H5b operationalizes the distinction.

Adoption status (per `apply_validators.py`):
  - STRONG-SPLIT-CANDIDATE  → adopted. Long frame combined with speech content
                              on the same line is a clean split.
  - STRONG-MERGE-CANDIDATE  → RETIRED for the solo-speech-verb arm. The
                              former auto-merge of bare wayyiqtol speech-verbs
                              with their following complement clause now emits
                              REVIEW-REQUIRED only (see solo-speech branch
                              below ~lines 402-428). The narrow §5 H5
                              scope-economy carve-out (dialogue-chain visual
                              rhythm, ≥4 consecutive turns) is editor-judged,
                              Category B per §2.

Rule H5 (canon §5 H5; Layer 3 editorial rule):
When a speech-intro frame ends with לֵאמֹר (the bare infinitive complementizer
marking speech onset), the frame length governs whether framing appears on its
own line or merges with antecedent recipient/location phrase. Splitting between
the speech-act announcement and the quoted content is independently mandated by
H5b regardless of frame length.

  - Long framing (≥ 4 prosodic words, or embedded location/recipient phrase):
    Framing gets its OWN line; speech opens on the NEXT line.
    Violation: frame and speech-opening appear on the SAME line.
    → STRONG-SPLIT-CANDIDATE (adopted).

  - Short framing (≤ 2 prosodic words + לֵאמֹר):
    Historical merge-with-speech-opening default. Per Path 1, this is
    REVIEW-REQUIRED (no longer auto-merged); the editor decides whether
    the H5 scope-economy carve-out applies.

  - Boundary case (exactly 3 prosodic words — judgment territory):
    Flag REVIEW-REQUIRED. The canon marks this as a judgment call.

Detection strategy:
  - Scan for lines containing לֵאמֹר (consonant skeleton: לאמר after point
    stripping). This is the primary speech-intro boundary marker.
  - Also detect bare וַיֹּאמֶר / וַיְדַבֵּר / וַיַּעַן at line end without לֵאמֹר
    immediately followed by speech content on the next line (heuristic; lower
    confidence — flagged REVIEW-REQUIRED).
  - Count prosodic words in the frame line (whitespace-delimited tokens that
    are not empty and not the לֵאמֹר token itself; maqqef-joined groups count
    as ONE prosodic word).
  - Apply short/long/boundary threshold.

Prosodic word counting:
  A prosodic word is a whitespace-delimited token (after stripping niqqud/te'amim).
  Maqqef-joined sequences (token contains ־) count as ONE prosodic word,
  regardless of how many orthographic words the maqqef joins.

Output format:
    [DEVIATION]  file:line_number  H5/speech-framing  SEVERITY  brief description

Where SEVERITY is one of:
    STRONG-MERGE-CANDIDATE   — long frame on same line as speech content (merge the frame up)
    STRONG-SPLIT-CANDIDATE   — short frame on its own line (split and merge with speech)
    REVIEW-REQUIRED          — boundary case (3 prosodic words) or bare speech verb at line end

Exit code: 0 if zero violations, 1 if violations found, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_speech_intro_framing.py
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_speech_intro_framing.py --book jonah
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_speech_intro_framing.py --v2
    PYTHONIOENCODING=utf-8 py -3 validators/colometry/validate_speech_intro_framing.py --verbose
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

# Maqqef glyph (U+05BE)
MAQQEF = "־"

# Hebrew points range (U+0591–U+05C7): cantillation + niqqud
HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")


def strip_points(token: str) -> str:
    """Return token with all niqqud and te'amim stripped."""
    return HEBREW_POINTS_RE.sub("", token)


# ---------------------------------------------------------------------------
# Speech-intro markers
# ---------------------------------------------------------------------------

# לֵאמֹר — consonant skeleton after stripping: לאמר
# This is the canonical speech-onset boundary marker (Waltke-O'Connor §36.2.3).
LEEMOR_SKELETON = "לאמר"

# Bare speech verbs that may introduce direct speech without לֵאמֹר.
# Consonant skeletons (stripped): ויאמר ויאמרו ויאמרי וידבר
BARE_SPEECH_VERB_SKELETONS = {
    "ויאמר",    # wayyiqtol qal 3ms — and he said
    "ויאמרו",   # wayyiqtol qal 3mp — and they said
    "וידבר",    # wayyiqtol piel 3ms — and he spoke
    "וידברו",   # wayyiqtol piel 3mp — and they spoke (audit 2026-05-01: missing)
    "ותאמר",    # wayyiqtol qal 3fs — and she said
    "ותאמרו",   # wayyiqtol qal 2/3 fp — and you/they (f) said (missing)
    "ותדבר",    # wayyiqtol piel 3fs — and she spoke (missing)
    "ויען",     # wayyiqtol qal 3ms — and he answered
    "ותען",     # wayyiqtol qal 3fs — and she answered (missing)
    "ויוסף",    # wayyiqtol hiphil 3ms — and he added/continued (idiom: ויוסף לאמר)
}

# Prophetic formula line — these get their OWN line regardless of length.
# Consonant skeletons: כה אמר יהוה, נאם יהוה
PROPHETIC_FORMULA_SKELETONS = {
    "כה",       # כֹּה — particle in כֹּה אָמַר יְהוָה
    "נאם",      # נְאֻם — oracle marker
}


def is_prophetic_formula_line(bare_tokens: list[str]) -> bool:
    """Return True if this line is a prophetic formula that gets its own line always.

    כֹּה אָמַר יְהוָה and נְאֻם יְהוָה are atomic formulaic units per Rule H5
    exception — they always get their own line regardless of word count.
    """
    if not bare_tokens:
        return False
    return bare_tokens[0] in PROPHETIC_FORMULA_SKELETONS


# ---------------------------------------------------------------------------
# H5b short-frame-with-content split (Path 1 retroactive realization)
# ---------------------------------------------------------------------------
# Detects lines where a speech-verb-headed frame is merged with quoted content
# on a single line WITHOUT לֵאמֹר (the long-frame-with-לֵאמֹר case is handled
# by the existing primary-check arm above). Per canon §5 H5b: split.

RECIPIENT_PP_HEAD_SKELS = frozenset({"אל", "ל", "את", "על", "עם"})
PRONOMINAL_RECIPIENT_SKELS = frozenset({
    "אליו", "אליך", "אליכם", "אליהם", "אליה", "אלי", "אלינו",
    "לו", "לך", "לנו", "להם", "לי", "לה", "לכם", "לכן",
    "אתו", "אתי", "אתך", "אתכם", "אתם", "אותו", "אותי", "אותך",
    "עמו", "עמי", "עמך", "עליו", "עלי",
})


def _strip_h_prefix(morpheme: str) -> str:
    return morpheme[1:] if morpheme.startswith("H") else morpheme


def _maqqef_head_skel(tok: str) -> str:
    head = tok.split(M.MAQQEF, 1)[0] if M.MAQQEF in tok else tok
    return strip_points(head)


def _is_recipient_pp(tok: str, tag_list: list[str] | None = None) -> bool:
    """Recipient-PP head from {אל, ל, את, על, עם} (closed list) — bare or
    maqqef-bound (אֶל־מֹשֶׁה) — OR bound-prep + fused content (לַדָּג, לְמֹשֶׁה,
    אֶת־הָאָרֶץ); excludes locative/temporal preps like מן, עד.
    Tag-driven gate when available.
    """
    s_head = _maqqef_head_skel(tok)
    s_full = strip_points(tok)
    # Bare or maqqef-bound recipient prep
    if s_head in RECIPIENT_PP_HEAD_SKELS:
        if tag_list:
            first = _strip_h_prefix(tag_list[0].split("/")[0])
            return first.startswith("R")
        return True
    # Pronominal recipient
    if s_full in PRONOMINAL_RECIPIENT_SKELS:
        return True
    # Bound-prep + fused content (לַדָּג, לְמֹשֶׁה, etc.)
    # Tag-driven gate REQUIRED for fused forms (skel ambiguous):
    if tag_list:
        first = _strip_h_prefix(tag_list[0].split("/")[0])
        # Rd or R as first morpheme + skel starts with recipient-class letter
        if first.startswith("R") and s_full and s_full[0] in {"ל", "א", "ע"}:
            # Exclude מן/עד/אחר/תחת — these would have other first letters
            # and don't start with ל/א/ע anyway. Also exclude אֶת- DO marker
            # if not in recipient context (אֵת variants are already in
            # RECIPIENT_PP_HEAD_SKELS as "את").
            return True
    return False


def _is_frame_subject(tok: str, tag_list: list[str] | None = None) -> bool:
    """Subject NP (Nc/Np), substantive participle, OR proper noun. Excludes
    R-headed and Tj/Ti-headed tokens. Construct chains supported (no maqqef
    block at this level — caller handles continuation).
    """
    if tag_list:
        for tag in tag_list:
            morphemes = tag.split("/")
            first = _strip_h_prefix(morphemes[0])
            if first.startswith("R") or first.startswith("Tj") or first.startswith("Ti"):
                return False
            for morpheme in morphemes:
                m = _strip_h_prefix(morpheme)
                if not m:
                    continue
                if m.startswith("Nc") or m.startswith("Np"):
                    return True
                if len(m) >= 3 and m[0] == "V" and m[2] == "r":
                    return True
        return False
    return False  # tag-required for this validator's H5b arm


def _is_construct_state_substantive(tag_list: list[str] | None) -> bool:
    """Token's substantive morpheme is in construct state (ends in 'c')."""
    if not tag_list:
        return False
    for tag in tag_list:
        for morpheme in tag.split("/"):
            m = _strip_h_prefix(morpheme)
            if not m:
                continue
            if (m.startswith("Nc") or m.startswith("Np")) and m.endswith("c"):
                return True
            if len(m) >= 6 and m[0] == "V" and m[2] == "r" and m.endswith("c"):
                return True
    return False


def _is_apposition_pronoun(tag_list: list[str] | None) -> bool:
    """Possessive-suffixed kinship/role term (אָחִיו, אִישָׁהּ, אֲדֹנִי)."""
    if not tag_list:
        return False
    for tag in tag_list:
        morphemes = tag.split("/")
        if len(morphemes) >= 2:
            first = _strip_h_prefix(morphemes[0])
            last = _strip_h_prefix(morphemes[-1])
            if (first.startswith("Nc") or first.startswith("Np")) and last.startswith("Sp"):
                return True
    return False


def _is_vav_coord_subject_continuation(tag_list: list[str] | None) -> bool:
    """vav-conjunction + noun (וְהַשָּׂרוֹת after כָּל־הַשָּׂרִים)."""
    if not tag_list:
        return False
    for tag in tag_list:
        morphemes = tag.split("/")
        if len(morphemes) >= 2:
            first = _strip_h_prefix(morphemes[0])
            second = _strip_h_prefix(morphemes[1])
            if first == "c" and (second.startswith("Nc") or second.startswith("Np") or second.startswith("Td")):
                return True
    return False


def compute_h5b_short_frame_split(
    tokens: list[str],
    bare_tokens: list[str],
    line_token_tags: list[list[str]] | None,
) -> int:
    """Compute the split position for H5b short-frame-with-content lines.

    Returns the token-index where the split should occur (frame end + 1).
    Returns 0 if no split applies (not a candidate, or frame extends entire line).

    Trigger requires (caller verifies):
      - First token in BARE_SPEECH_VERB_SKELETONS (speech-verb-headed)
      - LEEMOR_SKELETON NOT present (long-frame case handled elsewhere)
      - At least 3 tokens
    """
    if len(tokens) < 3:
        return 0

    def tag_at(i: int) -> list[str] | None:
        if line_token_tags and i < len(line_token_tags):
            return line_token_tags[i]
        return None

    # Walk tokens 1..N-1, admitting up to 5 satellite slots
    idx = 1
    slots_filled = 0
    saw_subject = False
    saw_recipient = False
    while idx < len(tokens) and slots_filled < 5:
        tok = tokens[idx]
        tags = tag_at(idx)

        # Recipient PP slot (admit at most once)
        if not saw_recipient and _is_recipient_pp(tok, tag_list=tags):
            idx += 1
            slots_filled += 1
            saw_recipient = True
            # Construct-chain continuation (אֶל־אִישׁ + הָאֱלֹהִים)
            if _is_construct_state_substantive(tags) and idx < len(tokens):
                if _is_frame_subject(tokens[idx], tag_list=tag_at(idx)):
                    idx += 1
                    slots_filled += 1
            # Apposition pronoun (לְשִׁמְעוֹן + אָחִיו)
            while idx < len(tokens) and slots_filled < 5 and _is_apposition_pronoun(tag_at(idx)):
                idx += 1
                slots_filled += 1
            continue

        # Subject NP slot
        if not saw_subject and _is_frame_subject(tok, tag_list=tags):
            idx += 1
            slots_filled += 1
            saw_subject = True
            # Construct-chain continuation
            prev_tags = tags
            if _is_construct_state_substantive(prev_tags) and idx < len(tokens):
                if _is_frame_subject(tokens[idx], tag_list=tag_at(idx)):
                    idx += 1
                    slots_filled += 1
            # Apposition continuation
            while idx < len(tokens) and slots_filled < 5:
                ntag = tag_at(idx)
                if (_is_frame_subject(tokens[idx], tag_list=ntag)
                        or _is_vav_coord_subject_continuation(ntag)
                        or _is_apposition_pronoun(ntag)):
                    idx += 1
                    slots_filled += 1
                else:
                    break
            continue

        break

    if idx >= len(tokens):
        return 0
    if idx == 1 and len(tokens) - 1 < 1:
        return 0
    return idx


# ---------------------------------------------------------------------------
# H5c trailing-attribution split (Isa 40:1 pattern)
# ---------------------------------------------------------------------------
# Detects lines where speech CONTENT precedes a post-content speech-attribution
# (e.g., `נַחֲמ֥וּ נַחֲמ֖וּ עַמִּ֑י יֹאמַ֖ר אֱלֹהֵיכֶֽם׃`). The trailing
# attribution `<speech-verb> <subject-NP>` is its own ATU (announcement of
# who is speaking) and must be split from the preceding content. Distinct
# from H5b (leading speech-frame) — H5c targets the post-content arm.

# Expanded skeleton set covering qatal + yiqtol + nominal speech forms
# that appear as trailing attributions (vs. the wayyiqtol-only set used
# for leading frames). Includes prophetic oracle marker `נאם`.
H5C_TRAILING_VERB_SKELETONS = frozenset({
    "יאמר",     # yiqtol qal 3ms — he says/will say (Isa 40:1 motivating)
    "אמר",      # qatal qal 3ms — he said
    "יאמרו",    # yiqtol qal 3mp — they say
    "אמרו",     # qatal qal 3mp — they said
    "נאם",      # nominal — oracle of (also a leading prophetic formula)
    "דבר",      # qatal qal 3ms — he spoke (also: noun "word")
    "ידבר",     # yiqtol piel 3ms — he speaks/will speak
})

# Subordinate-clause introducers that disqualify the speech-verb as a
# trailing attribution (it would belong to a subordinate clause instead).
H5C_SUBORDINATE_INTRODUCERS = frozenset({
    "כי", "פן", "למען", "אשר", "כאשר",
})

# Divine-name closed-list fallback when TAHOT subject confirmation is
# unavailable. These are the canonical trailing-attribution subjects.
H5C_DIVINE_NAME_SKELETONS = frozenset({
    "יהוה",
    "אלהים",
    "אלהיכם",
    "אלהינו",
    "אלהי",
    "אדני",
    "צבאות",
})

# Interrogative pronouns/adverbs. When any post-verb token in an H5c-
# candidate line is one of these, the divine name is the topic of a
# rhetorical question inside QUOTED CONTENT, not a trailing speaker.
# Closes Jer 2:8 class FP: הַכֹּהֲנִים לֹא אָמְרוּ אַיֵּה יְהוָה
# ("the priests did not say, 'where is YHWH?'") — no trailing attr.
H5C_INTERROGATIVE_BARE_SKELS = frozenset({
    "אי", "איה", "אנה", "היכן",
    "מה", "מי", "למה", "מתי", "איך", "איככה",
})


def compute_h5c_trailing_attribution_split(
    tokens: list[str],
    bare_tokens: list[str],
    line_token_tags: list[list[str]] | None,
) -> tuple[int, str]:
    """Compute split position for H5c trailing-attribution lines.

    Returns (split_pos, mode) where:
      - split_pos = 0  → no trailing-attribution split applies
      - split_pos > 0  → token-index where to split (verb position)
      - mode           → "tag-confirmed" (STRONG) | "skel-fallback" (REVIEW)

    Trigger pattern (caller verifies basic length):
      <≥2 substantive content tokens> <speech-verb> <subject-NP-tail>
    where the speech verb sits at len(bare_tokens)-2 (1-tok tail) or
    len(bare_tokens)-3 (2-tok tail; e.g., sof-pasuq-bearing subject).
    """
    n = len(bare_tokens)
    if n < 4:
        return 0, ""

    # Strip a trailing sof-pasuq-only token if present (rare, but defensive)
    # The sof-pasuq glyph ׃ is normally attached to the last word's te'amim,
    # so n stays the same; no separate handling required here.

    # Scan candidate verb positions: n-2 (1-tok tail) then n-3 (2-tok tail)
    for verb_idx in (n - 2, n - 3):
        if verb_idx < 2:
            continue  # need ≥2 content tokens before the verb
        verb_skel = bare_tokens[verb_idx]
        if verb_skel not in H5C_TRAILING_VERB_SKELETONS:
            continue

        # FP guard: subordinate-clause introducer in pre-verb tokens.
        pre_verb = bare_tokens[:verb_idx]
        if any(t in H5C_SUBORDINATE_INTRODUCERS for t in pre_verb):
            return 0, ""

        # FP guard: leading speech-verb already handled by H5b — this line
        # would have been routed there instead.
        if pre_verb and pre_verb[0] in BARE_SPEECH_VERB_SKELETONS:
            return 0, ""

        # FP guard: prophetic formula `כה אמר ...` even when not at line start
        # (e.g., `לכן כה אמר אדני יהוה`). When `כה` immediately precedes the
        # verb, it's a leading prophetic frame, not a trailing attribution.
        if verb_idx >= 1 and pre_verb[-1] == "כה":
            return 0, ""

        # FP guard: interrogative particle in post-verb position. When any
        # post-verb token is an interrogative, the divine name is the topic
        # of a quoted rhetorical question, not a trailing speaker.
        # (Jer 2:8 הַכֹּהֲנִים לֹא אָמְרוּ אַיֵּה יְהוָה class.)
        post_bare_check = bare_tokens[verb_idx + 1:]
        if any(
            pb.rstrip("׃") in H5C_INTERROGATIVE_BARE_SKELS for pb in post_bare_check
        ):
            return 0, ""

        # FP guard: pre-verb contains an infinitive-absolute. Inf-abs
        # is a stylistic emphasis device that almost always co-occurs with
        # speech context — its presence pre-verb signals the line is itself
        # a speech-event description, making the trailing verb+subject the
        # CONTENT of the speech, not a trailing attribution.
        # (Jer 23:17 אֹמְרִים אָמוֹר ... דִּבֶּר יְהוָה class.)
        # Tag-driven: V<stem>a aspect (a = infinitive absolute).
        if line_token_tags:
            inf_abs_in_pre_verb = False
            for k in range(verb_idx):
                if k >= len(line_token_tags):
                    break
                ktags = line_token_tags[k]
                if not ktags:
                    continue
                for tag in ktags:
                    if not tag or tag == "[—]":
                        continue
                    for morpheme in tag.split("/"):
                        m = morpheme.lstrip("Hc")
                        # Inf-abs morpheme: V<stem><aspect=a><...>
                        if (
                            len(m) >= 4
                            and m[0] == "V"
                            and m[2] == "a"
                        ):
                            inf_abs_in_pre_verb = True
                            break
                    if inf_abs_in_pre_verb:
                        break
                if inf_abs_in_pre_verb:
                    break
            if inf_abs_in_pre_verb:
                return 0, ""

        # FP guard: recipient PP follows the verb (אל־X / ל־X) — narrative
        # leading-frame pattern (Josh 5:2 `בעת ההיא אמר יהוה אל־יהושע`).
        # If any post-verb token is a recipient PP, this is leading not trailing.
        for k in range(verb_idx + 1, len(tokens)):
            ktags = line_token_tags[k] if (line_token_tags and k < len(line_token_tags)) else None
            if _is_recipient_pp(tokens[k], tag_list=ktags):
                return 0, ""

        # Tag-confirm verb-hood (when available): rules out homograph nouns
        # like `דבר` ("word"), `נאם` borderline cases.
        verb_tags = None
        if line_token_tags and verb_idx < len(line_token_tags):
            verb_tags = line_token_tags[verb_idx]
        if verb_tags is not None:
            # `נאם` is a noun in TAHOT (oracle); accept it as trailing-attr
            # head even without finite-verb confirmation.
            if verb_skel != "נאם" and not M.is_finite_verb_token(
                tokens[verb_idx], tag_list=verb_tags
            ):
                continue

        # FP guard: post-verb tokens contain a finite verb (would be speech
        # content, not subject). Tag-driven test only — skel-fallback would
        # be too noisy here.
        post_verb_tokens = tokens[verb_idx + 1:]
        post_finite = False
        if line_token_tags:
            for k in range(verb_idx + 1, len(tokens)):
                if k < len(line_token_tags):
                    pt = line_token_tags[k]
                    if pt and M.is_finite_verb_token(tokens[k], tag_list=pt):
                        post_finite = True
                        break
        if post_finite:
            continue

        # Subject test: require either (a) a proper-noun (Np) head in the
        # post-verb tail (tag-confirmed → STRONG), or (b) a divine-name skel
        # match in the closed list (→ STRONG when also tag-Nc, REVIEW
        # otherwise). Generic Nc alone is insufficient — too noisy
        # (Isa 45:24 `אָמַר צְדָקוֹת וָעֹז` was a confirmed FP).
        post_bare = bare_tokens[verb_idx + 1:]
        divine_name_match = any(
            pb.rstrip("׃") in H5C_DIVINE_NAME_SKELETONS for pb in post_bare
        )

        np_subject = False
        if line_token_tags:
            for k in range(verb_idx + 1, len(tokens)):
                ktags = line_token_tags[k] if k < len(line_token_tags) else None
                if not ktags:
                    continue
                # Look for an Np (proper noun) head morpheme in the tag chain.
                for tag in ktags:
                    for morpheme in tag.split("/"):
                        m = _strip_h_prefix(morpheme)
                        if m.startswith("Np"):
                            np_subject = True
                            break
                    if np_subject:
                        break
                if np_subject:
                    break

        if np_subject:
            return verb_idx, "tag-confirmed"

        if divine_name_match:
            return verb_idx, "skel-fallback"

        # No subject confirmation — skip this verb_idx, try next.

    return 0, ""


# ---------------------------------------------------------------------------
# Path-1 carve-out classifier (annotation-only — no severity change)
# ---------------------------------------------------------------------------

# Sifrei Emet poetic-register books for meter-protect carve-out.
SIFREI_EMET_BOOK_FRAGMENTS = ("psalms", "proverbs", "job")

# Homograph speech-verb skels — speech sense ambiguous without TAHOT confirmation.
HOMOGRAPH_SPEECH_VERB_SKELETONS = {"ויוסף", "ויען", "וידבר"}


def classify_path1_carveout(
    line: str,
    next_line: str,
    book_path_str: str,
    line_first_token_tags: "list[str] | None" = None,
) -> str | None:
    """Return a Path-1 carve-out tag for a solo-speech-verb finding, or None.

    Carve-outs surface in the brief so the editor can quickly triage
    REVIEW-REQUIRED findings. Categories (per canon §5 H5b + Path 1
    FP/FN audit 2026-05-02):
      - "job-answering-formula" : line N is a 2-token wayyiqtol-answer
        + speaker-name pattern, line N+1 is a verse-end solo speech-verb.
      - "homograph-unconfirmed" : first-token skel is in
        HOMOGRAPH_SPEECH_VERB_SKELETONS and TAHOT tag does not confirm
        speech-verb sense (or no tag is available).
      - "sifrei-emet-meter"     : chapter is in Sifrei Emet poetic register
        and the speech frame is short (≤4 prosodic words).
    """
    n_toks = line.split()
    if not n_toks:
        return None
    first_skel = strip_points(n_toks[0])

    # Job answering-formula: line N = 2 toks, first is wayyiqtol-answer
    # (וַיַּעַן/וַתַּעַן), line N+1 ends with sof-pasuq + solo speech-verb.
    if len(n_toks) == 2 and first_skel in {"ויען", "ותען"}:
        n1_stripped = next_line.rstrip()
        n1_toks = n1_stripped.split()
        if (len(n1_toks) == 1
                and n1_stripped.endswith("׃")
                and strip_points(n1_toks[0]) in {"ויאמר", "ויאמרו", "ותאמר", "ותאמרו"}):
            return "job-answering-formula"

    # Homograph speech-verb without TAHOT confirmation
    if first_skel in HOMOGRAPH_SPEECH_VERB_SKELETONS:
        confirmed = False
        if line_first_token_tags:
            # Best-effort import (only when needed) — validator runs standalone
            try:
                sys.path.insert(0, str(REPO_ROOT / "validators"))
                from _shared import morph_tags as MT  # noqa: WPS433
                for tag in line_first_token_tags:
                    if MT.is_finite_verb(tag):
                        confirmed = True
                        break
            except Exception:
                pass
        if not confirmed:
            return "homograph-unconfirmed"

    # Sifrei Emet meter-protect: book path contains psalms/proverbs/job
    book_str = book_path_str.lower().replace("\\", "/")
    if any(frag in book_str for frag in SIFREI_EMET_BOOK_FRAGMENTS):
        if len(n_toks) <= 4:
            return "sifrei-emet-meter"

    return None


def count_prosodic_words(tokens: list[str]) -> int:
    """Count prosodic words in a token list.

    A whitespace-delimited token is ONE prosodic word.
    If a token contains a maqqef (joining multiple orthographic words),
    the entire maqqef-group is still ONE prosodic word.
    The לֵאמֹר token itself is NOT counted (it is the boundary marker,
    not part of the frame content being measured).
    """
    count = 0
    for tok in tokens:
        bare = strip_points(tok)
        if bare == LEEMOR_SKELETON:
            continue
        if bare:
            count += 1
    return count


# ---------------------------------------------------------------------------
# Skippable lines
# ---------------------------------------------------------------------------

def is_skippable(line: str) -> bool:
    """Return True for blank lines and verse-reference-only lines."""
    s = line.strip()
    if not s:
        return True
    if re.match(r"^(\w+\s+)?\d+:\d+$", s):
        return True
    return False


# ---------------------------------------------------------------------------
# Verse-grouping helper (mirrors validate_construct_chain.py)
# ---------------------------------------------------------------------------

_VERSE_REF_RE = re.compile(r"^\d+:\d+\s*$")


def _partition_into_verses(lines: list[str]) -> list[tuple[int, list[tuple[int, str]]]]:
    """Partition file lines into per-verse groups.

    Returns list of (verse_num, [(1-based line_no, raw_line), ...]) tuples.
    Lines preceding any verse header are discarded (blank preamble only).
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
    """Scan one text file for Rule H5 speech-intro framing violations.

    Uses TAHOT morph tags (via morph_alignment) when available to classify
    speech-verb tokens.  Falls back to the BARE_SPEECH_VERB_SKELETONS skeleton
    heuristic when tags are missing or verse alignment fails.
    """
    violations = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    # Load TAHOT morph alignment for this chapter (None if morph file absent).
    chapter_morph = MA.load_chapter_morph(path)

    # Build a lookup: file_line_index (0-based) → [tag_list_per_token]
    # tag_list_per_token[tok_idx] = list[str] (TAHOT tags for that token)
    # This lets the flat line-scan below look up tags by line index.
    line_token_tags: dict[int, list[list[str]]] = {}
    if chapter_morph is not None:
        verse_groups = _partition_into_verses(lines)
        for verse_num, verse_numbered_lines in verse_groups:
            content = [
                (ln, raw) for ln, raw in verse_numbered_lines
                if not is_skippable(raw)
            ]
            if not content:
                continue
            ortho_tags = chapter_morph.get(verse_num)
            if ortho_tags is None:
                continue
            verse_text_lines = [raw for _, raw in content]
            aligned = MA.align_verse_tokens_to_tags(verse_text_lines, ortho_tags)
            if aligned is None:
                continue
            for ci, (ln, _raw) in enumerate(content):
                # ln is 1-based; store at 0-based index
                line_token_tags[ln - 1] = aligned[ci]

    def _tag_list_for(line_idx: int, tok_idx: int) -> "list[str] | None":
        """Return TAHOT tag list for (line_idx, tok_idx), or None on miss."""
        tl = line_token_tags.get(line_idx)
        if tl is None:
            return None
        if tok_idx < 0 or tok_idx >= len(tl):
            return None
        return tl[tok_idx]

    for i, line in enumerate(lines):
        if is_skippable(line):
            continue

        line_no = i + 1  # 1-based

        tokens = line.split()
        bare_tokens = [strip_points(t) for t in tokens]

        # --- Primary check: line contains לֵאמֹר ---
        if LEEMOR_SKELETON in bare_tokens:
            # Is this a prophetic formula? If so, it should be on its own
            # line — but that's the CORRECT behavior; don't flag those.
            if is_prophetic_formula_line(bare_tokens):
                continue

            leemor_pos = bare_tokens.index(LEEMOR_SKELETON)
            # Tokens in frame = everything before לֵאמֹר
            frame_tokens = tokens[:leemor_pos]
            # Tokens after לֵאמֹר on the SAME line (speech content co-located)
            speech_tokens_same_line = tokens[leemor_pos + 1:]

            # --- EXCEPTION: standalone לֵאמֹר line (Bug 1 fix) ---
            # Canon §1 SJ3 explicitly states: "לֵאמֹר alone — the bare
            # infinitive complementizer is a speech-act-announcement marker,
            # gets its own line at the point of speech-onset."
            # If the ONLY non-sof-pasuq token on the line IS לֵאמֹר itself,
            # this is the correct standalone rendering — do NOT flag.
            non_leemor_bare = [
                b for b in bare_tokens
                if b != LEEMOR_SKELETON and b != "׃" and b != ""
            ]
            if len(non_leemor_bare) == 0:
                # Pure standalone לֵאמֹר line — canonical, not a violation.
                continue

            # Count prosodic words in frame (excluding לֵאמֹר itself)
            prosodic_count = count_prosodic_words(frame_tokens)

            # --- CROSS-LINE BACK-SCAN for multi-line speech frames (Bug 2 fix) ---
            # When frame_tokens is empty or very short (לֵאמֹר is the first or
            # near-first token on the line), the full speech-intro frame may have
            # started on a prior line.  Back-scan up prior non-empty lines
            # (stopping at a verse-reference, blank line, or sof pasuq) to
            # accumulate additional frame tokens.
            if prosodic_count < 4:
                extra_tokens: list[str] = []
                for k in range(i - 1, -1, -1):
                    prev = lines[k]
                    if is_skippable(prev):
                        break  # blank / verse-ref line — frame doesn't continue
                    prev_bare = [strip_points(t) for t in prev.split()]
                    # Stop if prior line contains לֵאמֹר (nested or repeated)
                    if LEEMOR_SKELETON in prev_bare:
                        break
                    # Stop if prior line ends with sof pasuq (previous verse)
                    if prev.rstrip().endswith("׃"):
                        break
                    extra_tokens = list(prev.split()) + extra_tokens
                if extra_tokens:
                    prosodic_count += count_prosodic_words(extra_tokens)

            # Next non-empty line (to check if speech content follows on next line)
            next_content = ""
            next_content_line_num = None
            for j in range(i + 1, len(lines)):
                if not is_skippable(lines[j]):
                    next_content = lines[j].strip()
                    next_content_line_num = j + 1  # 1-based
                    break

            has_speech_on_same_line = bool(speech_tokens_same_line)
            has_speech_on_next_line = bool(next_content)

            if prosodic_count <= 2:
                # SHORT frame (≤ 2 prosodic words plus לֵאמֹר):
                # Per Path 1 (§5 H5b), speech-act announcement is
                # propositionally complete; default is SPLIT (no auto-merge).
                # Surface as REVIEW-REQUIRED so editor can apply the §5 H5
                # scope-economy carve-out (dialogue chain) when warranted.
                if not has_speech_on_same_line and has_speech_on_next_line:
                    carveout = classify_path1_carveout(
                        line=line,
                        next_line=next_content,
                        book_path_str=str(path),
                        line_first_token_tags=_tag_list_for(i, 0),
                    )
                    carveout_suffix = (
                        f" [carve-out: {carveout} — likely no-action]" if carveout else ""
                    )
                    violations.append({
                        "file": path.name,
                        "file_path": path,
                        "line_num": line_no,
                        "rule": "H5/speech-framing",
                        "severity": "REVIEW-REQUIRED",
                        "brief": (
                            f"short frame ({prosodic_count} prosodic words + לֵאמֹר) "
                            f"isolated on its own line — REVIEW for §5 H5 "
                            f"scope-economy carve-out (dialogue chain). Per Path 1 "
                            f"§5 H5b, default is SPLIT."
                            f"{carveout_suffix}"
                        ),
                        "line": line.rstrip(),
                        "next_line": next_content,
                        "next_line_num": next_content_line_num,
                        "leemor_pos": leemor_pos,
                        "path1_carveout": carveout,
                    })

            elif prosodic_count == 3:
                # BOUNDARY case (exactly 3 prosodic words + לֵאמֹר):
                # Judgment territory — flag REVIEW-REQUIRED.
                violations.append({
                    "file": path.name,
                    "file_path": path,
                    "line_num": line_no,
                    "rule": "H5/speech-framing",
                    "severity": "REVIEW-REQUIRED",
                    "brief": (
                        f"boundary case ({prosodic_count} prosodic words + לֵאמֹר) "
                        f"— short/long threshold is 3; editorial judgment required"
                    ),
                    "line": line.rstrip(),
                    "next_line": next_content,
                    "next_line_num": next_content_line_num,
                    "leemor_pos": leemor_pos,
                })

            else:
                # LONG frame (≥ 4 prosodic words + לֵאמֹר):
                # Frame MUST get its OWN line; speech opens on next line.
                if has_speech_on_same_line:
                    # Frame and speech-opening are on the same line. Violation.
                    violations.append({
                        "file": path.name,
                        "file_path": path,
                        "line_num": line_no,
                        "rule": "H5/speech-framing",
                        "severity": "STRONG-SPLIT-CANDIDATE",
                        "brief": (
                            f"long frame ({prosodic_count} prosodic words + לֵאמֹר) "
                            f"combined with speech content on same line — split after לֵאמֹר"
                        ),
                        "line": line.rstrip(),
                        "next_line": "",
                        "next_line_num": None,
                        "leemor_pos": leemor_pos,
                    })

        # --- H5b short-frame-with-content check: speech verb starts line, no לֵאמֹר,
        # frame is merged with quoted content on the same line ---
        # Per canon §5 H5b (Path 1, 2026-05-02): split between announcement
        # frame and quoted content. Mirrors the long-frame STRONG-SPLIT arm
        # above but for the no-לֵאמֹר case (~2,400 historic merges corpus-wide).
        # Tag-driven: requires TAHOT alignment for accurate frame-end detection.
        elif (
            len(bare_tokens) >= 3
            and bare_tokens[0] in BARE_SPEECH_VERB_SKELETONS
            and LEEMOR_SKELETON not in bare_tokens
            and not is_prophetic_formula_line(bare_tokens)
            and (
                _tag_list_for(i, 0) is None
                or M.is_finite_verb_token(tokens[0], tag_list=_tag_list_for(i, 0))
            )
        ):
            # Build per-token tag list for this line (already aligned in
            # line_token_tags dict above).
            line_tags = line_token_tags.get(i)
            split_pos = compute_h5b_short_frame_split(tokens, bare_tokens, line_tags)
            if split_pos > 0:
                # Carve-outs: classify_path1_carveout already handles homograph,
                # Sifrei Emet, Job answering-formula. Apply same logic.
                carveout = classify_path1_carveout(
                    line=line,
                    next_line="",
                    book_path_str=str(path),
                    line_first_token_tags=_tag_list_for(i, 0),
                )
                if carveout:
                    severity = "REVIEW-REQUIRED"
                    suffix = f" [carve-out: {carveout} — likely no-action]"
                else:
                    severity = "STRONG-SPLIT-CANDIDATE"
                    suffix = ""
                violations.append({
                    "file": path.name,
                    "file_path": path,
                    "line_num": line_no,
                    "rule": "H5b/short-frame-content",
                    "severity": severity,
                    "brief": (
                        f"speech-frame ({split_pos} tokens) merged with quoted content "
                        f"on same line — split at token index {split_pos} per Path 1 H5b"
                        f"{suffix}"
                    ),
                    "line": line.rstrip(),
                    "next_line": "",
                    "next_line_num": None,
                    "leemor_pos": None,
                    "split_position": split_pos,
                    "path1_carveout": carveout,
                })

        # --- H5c trailing-attribution check: <content> + <speech-verb> + <subject-NP-tail> ---
        # Per spec (post-Isa-40:1 audit): the post-content speech-frame is its
        # own ATU. Distinct from H5b (leading frame) — this targets lines like
        # `נַחֲמ֥וּ נַחֲמ֖וּ עַמִּ֑י יֹאמַ֖ר אֱלֹהֵיכֶֽם׃` where the attribution
        # tail merges with preceding content. Skips prophetic-formula leads
        # (כה אמר ...) — those are handled by the formula carve-out.
        elif (
            len(bare_tokens) >= 4
            and not is_prophetic_formula_line(bare_tokens)
            and bare_tokens[0] not in BARE_SPEECH_VERB_SKELETONS
            and LEEMOR_SKELETON not in bare_tokens
        ):
            line_tags = line_token_tags.get(i)
            split_pos, mode = compute_h5c_trailing_attribution_split(
                tokens, bare_tokens, line_tags
            )
            if split_pos > 0:
                # Divine-name closed list (יהוה / אלהים / אלהיכם / אדני /
                # צבאות) is a tight sufficient filter for "post-verb token
                # is the speaker" — these are unambiguously YHWH references
                # in nominal-subject position. Promote to STRONG to honor
                # mechanical-apply discipline (vs review-queue accumulation).
                # Tag-confirmed Np remains STRONG.
                if mode == "tag-confirmed":
                    severity = "STRONG-SPLIT-CANDIDATE"
                    mode_note = "tag-confirmed subject"
                else:
                    severity = "STRONG-SPLIT-CANDIDATE"
                    mode_note = "divine-name closed-list subject"
                violations.append({
                    "file": path.name,
                    "file_path": path,
                    "line_num": line_no,
                    "rule": "H5c/trailing-attribution",
                    "severity": severity,
                    "brief": (
                        f"trailing speech-attribution at token {split_pos} "
                        f"({tokens[split_pos]}) merged with preceding content "
                        f"— split before verb per H5c [{mode_note}]"
                    ),
                    "line": line.rstrip(),
                    "next_line": "",
                    "next_line_num": None,
                    "leemor_pos": None,
                    "split_position": split_pos,
                })

        # --- Solo speech-verb check: line is exactly ONE bare speech-verb token ---
        # Per audit 2026-05-01 Class E: when an entire line is just a wayyiqtol
        # speech verb (e.g., 1 Sam 1:18 line 92 'וַתֹּ֕אמֶר' alone), the verb
        # is propositionally empty without its complement clause on the next line.
        # This is STRONG-MERGE-CANDIDATE (not REVIEW): the merge is unambiguously
        # correct — solo speech-verbs are never editorially defensible standalone.
        # Tag-aware path: skeleton membership gates entry; M.is_finite_verb_token
        # with TAHOT tags then confirms the token is truly a finite verb (not a
        # homographic noun). When tags are absent, the skeleton match alone
        # controls (skel-fallback), preserving prior behaviour.
        # Cross-verse guard (2026-05-02): suppress when the verb ends with sof
        # pasuq (׃) — the "next content" is in the FOLLOWING verse and merging
        # would cross the verse boundary, eating the verse-reference label.
        # Job's answering-formula (`וַיַּעַן X / וַיֹּאמַֽר׃` ending verse N,
        # then verse N+1 begins the speech) is the canonical case.
        elif len(bare_tokens) == 1 and bare_tokens[0] in BARE_SPEECH_VERB_SKELETONS and (
            _tag_list_for(i, 0) is None
            or M.is_finite_verb_token(tokens[0], tag_list=_tag_list_for(i, 0))
        ) and not line.rstrip().endswith("׃"):
            next_content = ""
            next_content_line_num = None
            for j in range(i + 1, len(lines)):
                if not is_skippable(lines[j]):
                    next_content = lines[j].strip()
                    next_content_line_num = j + 1  # 1-based
                    break
            if next_content:
                carveout = classify_path1_carveout(
                    line=line,
                    next_line=next_content,
                    book_path_str=str(path),
                    line_first_token_tags=_tag_list_for(i, 0),
                )
                carveout_suffix = (
                    f" [carve-out: {carveout} — likely no-action]" if carveout else ""
                )
                violations.append({
                    "file": path.name,
                    "file_path": path,
                    "line_num": line_no,
                    "rule": "H5/speech-framing",
                    "severity": "REVIEW-REQUIRED",
                    "brief": (
                        f"solo speech verb ({tokens[-1]}) — REVIEW for §5 H5 "
                        f"scope-economy carve-out (dialogue chain). Per Path 1 "
                        f"canon §5 H5b, speech-act announcement is propositionally "
                        f"complete; default is SPLIT, not merge."
                        f"{carveout_suffix}"
                    ),
                    "line": line.rstrip(),
                    "next_line": next_content,
                    "next_line_num": next_content_line_num,
                    "leemor_pos": None,
                    "path1_carveout": carveout,
                })

        # --- Secondary check: bare speech verb at MULTI-WORD line end (no לֵאמֹר) ---
        # If the last token is a bare wayyiqtol speech verb on a multi-token line
        # (e.g., 'וַיַּעַן עֵלִי וַיֹּאמֶר'), this might be a framing situation
        # without לֵאמֹר. Lower confidence — REVIEW-REQUIRED.
        # Tag-aware: skeleton membership gates entry; TAHOT tag confirmation
        # suppresses FPs from non-verb homographs. Skel-fallback when tags absent.
        elif bare_tokens and bare_tokens[-1] in BARE_SPEECH_VERB_SKELETONS and (
            _tag_list_for(i, len(tokens) - 1) is None
            or M.is_finite_verb_token(tokens[-1], tag_list=_tag_list_for(i, len(tokens) - 1))
        ):
            next_content = ""
            next_content_line_num = None
            for j in range(i + 1, len(lines)):
                if not is_skippable(lines[j]):
                    next_content = lines[j].strip()
                    next_content_line_num = j + 1  # 1-based
                    break
            if next_content:
                violations.append({
                    "file": path.name,
                    "file_path": path,
                    "line_num": line_no,
                    "rule": "H5/speech-framing",
                    "severity": "REVIEW-REQUIRED",
                    "brief": (
                        f"bare speech verb at line end ({tokens[-1]}) without לֵאמֹר "
                        f"— check if speech content follows and framing length"
                    ),
                    "line": line.rstrip(),
                    "next_line": next_content,
                    "next_line_num": next_content_line_num,
                    "leemor_pos": None,
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
            # Determine applied_action from severity, לֵאמֹר position, or
            # explicit split_position (H5b short-frame arm).
            leemor_pos = v.get("leemor_pos")
            split_pos = v.get("split_position")
            if severity == "STRONG-MERGE-CANDIDATE":
                applied_action = "merge_with_next"
            elif severity == "STRONG-SPLIT-CANDIDATE":
                # split_at_position_N: apply_validators interprets N as the
                # 0-indexed token AFTER which to split (split happens at N+1
                # boundary). For H5b short-frame, our split_pos is already
                # the boundary index → subtract 1. For לֵאמֹר case, leemor_pos
                # is the index OF לֵאמֹר; split happens after it → subtract 0.
                if split_pos is not None:
                    applied_action = f"split_at_position_{split_pos - 1}"
                elif leemor_pos is not None:
                    applied_action = f"split_at_position_{leemor_pos}"
                else:
                    applied_action = "split_at_position_unknown"
            else:  # REVIEW-REQUIRED
                applied_action = None

            findings.append({
                "file": str(v["file_path"].relative_to(REPO_ROOT)).replace("\\", "/"),
                "line": v["line_num"],
                "severity": "DEVIATION",
                "tag": severity,
                "rule_id": "H5.1",
                "rule_short": "direct-speech framing boundary",
                "brief": v["brief"],
                "next_line": v.get("next_line_num"),
                "applied_action": applied_action,
            })

        by_severity_json: dict[str, int] = {}
        by_tag: dict[str, int] = {}
        for f in findings:
            by_severity_json[f["severity"]] = by_severity_json.get(f["severity"], 0) + 1
            by_tag[f["tag"]] = by_tag.get(f["tag"], 0) + 1

        doc = {
            "validator": "validate_speech_intro_framing",
            "rule": "Rule H5 — Direct-Speech Framing Default",
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
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output (default) ---
    print("=" * 72)
    print(f"Rule H5 Direct-Speech Framing validator — Tanakh {tier_label}")
    print(f"Reference: canon §5 H5 (short ≤3 prosodic words; long ≥4)")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Violations    : {len(all_violations)}")

    # Severity summary
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
        print("No violations found. Rule H5 speech-intro framing is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
