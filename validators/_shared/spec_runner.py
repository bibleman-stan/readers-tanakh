"""Spec-driven validator engine.

Specs are YAML files in `validators/specs/` declaring trigger conditions,
guards, severity, and annotation per rule. Adding a new colometric rule =
write a new YAML spec; no Python code change.

Usage:
    from validators._shared.spec_runner import SpecRunner
    runner = SpecRunner('validators/specs/')
    findings = runner.run_corpus('data/text-files/v2/he/')

CLI: see scripts/run_validators.py.

Architectural constraint: NO te'amim Unicode codepoints (U+0591-U+05AF) in
trigger predicates. The morphology module enforces this; spec evaluation
delegates trigger logic to that module.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from . import morphology as M
from . import morph_tags as MT
from . import morph_alignment as MA
from .poetic_register import is_poetic_register


# ─── spec data structures ───────────────────────────────────────────


@dataclass
class Finding:
    file: str
    line: int                 # 1-based line index in the chapter file
    rule: str                 # e.g., "M2", "H18.1", "S1"
    subcase: str              # e.g., "verb_et_strand"
    severity: str             # STRONG-MERGE-CANDIDATE | STRONG-SPLIT-CANDIDATE | REVIEW-REQUIRED | MALFORMED
    book: str
    chapter: int
    verse: int
    prior_line: str
    next_line: str
    prosodic_word_count: int
    annotation: str
    suggested_action: str
    # SPLIT-mode only: token indices in prior_line where new line breaks should be inserted.
    # Empty list for MERGE findings.
    split_positions: list = field(default_factory=list)

    def to_text(self) -> str:
        tag = "[MALFORMED]" if self.severity == "MALFORMED" else "[DEVIATION]"
        return (
            f"{tag}  {self.file}:{self.line}  {self.rule}/{self.subcase}  "
            f"{self.severity}  {self.annotation}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "rule": self.rule,
            "subcase": self.subcase,
            "severity": self.severity,
            "book": self.book,
            "chapter": self.chapter,
            "verse": self.verse,
            "prior_line": self.prior_line,
            "next_line": self.next_line,
            "prosodic_word_count": self.prosodic_word_count,
            "annotation": self.annotation,
            "suggested_action": self.suggested_action,
            "split_positions": self.split_positions,
        }


@dataclass
class Spec:
    name: str
    rule: str
    subcase: str
    severity: str
    description: str = ""
    trigger: dict[str, Any] = field(default_factory=dict)
    guards: list = field(default_factory=list)
    annotation_template: str = ""
    suggested_action: str = ""
    mode: str = "pair"  # "pair" (default; line N + line N+1), "line" (single line — splits)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Spec":
        return cls(
            name=d["name"],
            rule=d["rule"],
            subcase=d.get("subcase", d["name"]),
            severity=d["severity"],
            description=d.get("description", ""),
            trigger=d.get("trigger", {}),
            guards=d.get("guards", []),
            annotation_template=d.get("annotation_template", ""),
            suggested_action=d.get("suggested_action", "MERGE"),
            mode=d.get("mode", "pair"),
        )


# ─── spec evaluation ────────────────────────────────────────────────


def _matches_token(
    tok: Optional[str],
    conditions: dict[str, Any],
    tag_list: Optional[list[str]] = None,
) -> bool:
    """Apply token-level conditions: skeleton_in / morphology / morphology_one_of.

    `tag_list` is the per-ortho TAHOT morph tag list for this token (one tag
    per maqqef-joined ortho-word). When present, tag-driven morphology checks
    take precedence over skel-heuristics. None → fall back to skel-only path.
    """
    if not tok:
        return False
    if "skeleton_in" in conditions:
        if M.skel(tok) not in set(conditions["skeleton_in"]):
            return False
    if "morphology" in conditions:
        if not _check_morphology(tok, conditions["morphology"], tag_list):
            return False
    if "morphology_one_of" in conditions:
        if not any(_check_morphology(tok, m, tag_list) for m in conditions["morphology_one_of"]):
            return False
    if "skeleton_starts_with" in conditions:
        prefixes = conditions["skeleton_starts_with"]
        if isinstance(prefixes, str):
            prefixes = [prefixes]
        if not any(M.skel(tok).startswith(p) for p in prefixes):
            return False
    return True


def _check_morphology(tok: str, morph: str, tag_list: Optional[list[str]] = None) -> bool:
    """Single-morphology check by name.

    When `tag_list` is provided AND the morph type has a tag-driven
    implementation, the tag is authoritative. Otherwise falls back to the
    skel-heuristic path.
    """
    if morph == "finite_verb":
        # Tag-driven path now lives IN the helper (morphology.is_finite_verb_token
        # accepts optional tag_list). Pass through; helper does TAHOT-oracle
        # check first, falls back to skel only when no tag available.
        return M.is_finite_verb_token(tok, tag_list=tag_list)
    if morph == "np_head":
        # standalone token check: not a finite verb, not a particle/prep
        return not M.is_finite_verb_token(tok) and not M._matches_prep_only(tok) if hasattr(M, "_matches_prep_only") else not M.is_finite_verb_token(tok)
    if morph == "prep":
        # Maqqef-joined prep+complement (e.g., אֶל־הֶבֶל, מִן־הָאֲדָמָה):
        # check the FIRST sub-token (the prep itself), not the whole compound.
        if M.MAQQEF in tok:
            head = tok.split(M.MAQQEF, 1)[0]
            s_head = M.skel(head)
            if s_head in M.PREP_SKELETONS:
                return True
            # vav-prefixed free prep within maqfef compound (וְאֶל־..., וְעַל־...)
            if len(s_head) >= 3 and s_head[0] == "ו" and s_head[1:] in M.PREP_SKELETONS:
                return True
            # bound-prep on head sub-token
            if len(s_head) >= 2 and s_head[0] in M.BOUND_PREP_PREFIXES and not M.is_finite_verb_skel(s_head):
                if s_head[:2] in M.NON_PREP_2CHAR_PREFIX:
                    return False
                return True
            return False
        s = M.skel(tok)
        if s in M.PREP_SKELETONS:
            return True
        # vav-prefixed free prep (וְאֶל = and-to, וְעַל = and-upon, וְעִם = and-with)
        if len(s) >= 3 and s[0] == "ו" and s[1:] in M.PREP_SKELETONS:
            return True
        if len(s) >= 2 and s[0] in M.BOUND_PREP_PREFIXES and not M.is_finite_verb_skel(s):
            if s[:2] in M.NON_PREP_2CHAR_PREFIX:
                return False
            return True
        # vav-prefix tolerance — וְ + bound-prep + stem (e.g., וְלַחֹשֶׁךְ, וּבֵין)
        # Inner stem must not be a finite verb (rules out vav-conjunction + verb).
        if len(s) >= 3 and s[0] == "ו" and s[1] in M.BOUND_PREP_PREFIXES:
            inner = s[1:]
            if inner not in M.QATAL_COMMON and not M.is_finite_verb_skel(inner):
                if inner[:2] in M.NON_PREP_2CHAR_PREFIX:
                    return False
                return True
        return False
    if morph == "compound_prep":
        return M.skel(tok) in M.PREP_SKELETONS
    if morph == "bare_participle":
        # whole token IS a participle; reuse line-start helper on a one-token line
        return M.line_starts_with_participle(tok)
    if morph == "le_infinitive":
        return M.line_starts_with_le_infinitive(tok)
    if morph == "discourse_particle":
        return M.skel(tok) in M.DISCOURSE_PARTICLES
    if morph == "vocative_particle":
        return M.skel(tok) in M.VOCATIVE_PARTICLES
    if morph == "m2_pp_verb":
        return M.is_m2_pp_verb_token(tok)
    if morph == "motion_locus_verb":
        return M.is_motion_locus_verb_token(tok, tag_list=tag_list)
    if morph == "temporal_frame_opener":
        return M.is_temporal_frame_opener_token(tok, tag_list=tag_list)
    if morph == "do_marker":
        return M.is_do_marker_token(tok, tag_list=tag_list)
    if morph == "bare_do_marker":
        return M.is_bare_do_marker_token(tok)
    if morph == "bare_prep":
        return M.is_bare_prep_token(tok, tag_list=tag_list)
    if morph == "construct_head":
        return M.is_construct_head_token(tok, tag_list=tag_list)
    if morph == "definite_adjective":
        return M.is_definite_adjective_token(tok, tag_list=tag_list)
    if morph == "numeral":
        return M.is_numeral_token(tok, tag_list=tag_list)
    if morph == "numeral_or_unit_noun":
        return M.is_numeral_token(tok, tag_list=tag_list) or M.is_numeral_governed_noun(tok)
    if morph == "bare_noun":
        return M.is_bare_noun_token(tok, tag_list=tag_list)
    if morph == "inf_abs":
        return M.is_inf_abs_token(tok, tag_list=tag_list)
    if morph == "finite_verb":
        return M.is_finite_verb_token(tok, tag_list=tag_list)
    if morph == "cognition_verb_qal":
        return M.is_cognition_verb_qal_token(tok, tag_list=tag_list)
    return False


def _matches_anywhere(
    line: str,
    conditions: dict[str, Any],
    line_tag_lists: Optional[list[list[str]]] = None,
) -> bool:
    """Apply line-level conditions: has_finite_verb, has_resumptive_suffix, ...

    `line_tag_lists` is the per-token tag lists for this line (each token's
    list of ortho-tags). When present, tag-driven checks override skel.
    """
    if "has_finite_verb" in conditions:
        actual = _line_has_finite_verb(line, line_tag_lists)
        if actual != conditions["has_finite_verb"]:
            return False
    if "has_resumptive_suffix" in conditions:
        if M.line_has_resumptive_suffix(line) != conditions["has_resumptive_suffix"]:
            return False
    if "has_cognition_verb_qal" in conditions:
        actual = _line_has_cognition_verb_qal(line, line_tag_lists)
        if actual != conditions["has_cognition_verb_qal"]:
            return False
    return True


def _line_has_cognition_verb_qal(line: str, line_tag_lists: Optional[list[list[str]]]) -> bool:
    """True if any token on the line is a Tier-1 qal cognition/perception
    verb (ידע / שמע / ראה family) per `M.is_cognition_verb_qal_token`.

    Used by m4_e_solo_cognition_verb_clausal — line N must contain a
    cognition verb anywhere (not just first/last position) for the
    `כי + V + S || כי + complement` Gen-3:5 shape.
    """
    tokens = line.split()
    for i, tok in enumerate(tokens):
        tag_list = line_tag_lists[i] if (line_tag_lists and i < len(line_tag_lists)) else None
        if M.is_cognition_verb_qal_token(tok, tag_list=tag_list):
            return True
    return False


def _line_has_finite_verb(line: str, line_tag_lists: Optional[list[list[str]]]) -> bool:
    """Tag-aware line-level finite-verb check.

    If we have tags for the line, scan each token's head tag for a finite
    verb. Otherwise fall back to the skel-based has_finite_verb.
    """
    if line_tag_lists:
        for tt in line_tag_lists:
            head = MA.head_tag_for_token(tt)
            if head and MT.is_finite_verb(head):
                return True
        return False
    return M.has_finite_verb(line)


def _matches_trigger(spec: Spec, l_n: str, l_n1: str, ctx: dict[str, Any]) -> bool:
    t = spec.trigger
    n_tok_tags: list[list[str]] = ctx.get("line_n_token_tags") or []
    n1_tok_tags: list[list[str]] = ctx.get("line_n1_token_tags") or []

    def _last_tag(tag_lists: list[list[str]]) -> Optional[list[str]]:
        return tag_lists[-1] if tag_lists else None

    def _first_tag(tag_lists: list[list[str]]) -> Optional[list[str]]:
        return tag_lists[0] if tag_lists else None

    if "line_n_last_token" in t:
        if not _matches_token(M.last_content_token(l_n), t["line_n_last_token"], _last_tag(n_tok_tags)):
            return False
    if "line_n_first_token" in t:
        if not _matches_token(M.first_content_token(l_n), t["line_n_first_token"], _first_tag(n_tok_tags)):
            return False
    if "line_n1_first_token" in t:
        if not _matches_token(M.first_content_token(l_n1), t["line_n1_first_token"], _first_tag(n1_tok_tags)):
            return False
    if "line_n1_last_token" in t:
        if not _matches_token(M.last_content_token(l_n1), t["line_n1_last_token"], _last_tag(n1_tok_tags)):
            return False
    if "line_n_anywhere" in t:
        if not _matches_anywhere(l_n, t["line_n_anywhere"], n_tok_tags or None):
            return False
    if "line_n1_anywhere" in t:
        if not _matches_anywhere(l_n1, t["line_n1_anywhere"], n1_tok_tags or None):
            return False
    if "combined_max_prosodic_words" in t:
        total = M.prosodic_word_count(l_n) + M.prosodic_word_count(l_n1)
        if total > t["combined_max_prosodic_words"]:
            return False
    if "combined_min_prosodic_words" in t:
        total = M.prosodic_word_count(l_n) + M.prosodic_word_count(l_n1)
        if total < t["combined_min_prosodic_words"]:
            return False
    if "line_n_max_prosodic_words" in t:
        if M.prosodic_word_count(l_n) > t["line_n_max_prosodic_words"]:
            return False
    if "line_n1_max_prosodic_words" in t:
        if M.prosodic_word_count(l_n1) > t["line_n1_max_prosodic_words"]:
            return False
    if "line_n_is_verse_start" in t:
        if t["line_n_is_verse_start"] != (ctx.get("line_idx_in_verse") == 0):
            return False
    return True


# ─── guards ─────────────────────────────────────────────────────────

GUARD_DISPATCH: dict[str, callable] = {}


def _register_guard(name: str):
    def decorator(fn):
        GUARD_DISPATCH[name] = fn
        return fn

    return decorator


@_register_guard("poetic_register")
def _g_poetic(l_n, l_n1, ctx):
    return is_poetic_register(ctx["book"], ctx["chapter"], ctx.get("verse"))


@_register_guard("vocative_position")
def _g_vocative(l_n, l_n1, ctx):
    return M.is_vocative_line(l_n)


@_register_guard("discourse_particle_on_next_line")
def _g_disc(l_n, l_n1, ctx):
    return M.line_starts_with_discourse_particle(l_n1)


@_register_guard("casus_pendens")
def _g_casus(l_n, l_n1, ctx):
    # check the line AFTER the candidate pair for resumptive suffix
    lookahead = ctx.get("lookahead", "")
    return M.line_has_resumptive_suffix(lookahead)


@_register_guard("heavy_subject")
def _g_heavy_subj(l_n, l_n1, ctx):
    return M.is_heavy_subject(l_n)


@_register_guard("heavy_participial_complement")
def _g_heavy_pc(l_n, l_n1, ctx):
    return M.is_heavy_participial_complement(l_n1)


@_register_guard("le_infinitive_on_next_line")
def _g_lei(l_n, l_n1, ctx):
    return M.line_starts_with_le_infinitive(l_n1)


@_register_guard("both_lines_have_finite_verb")
def _g_both_verbs(l_n, l_n1, ctx):
    n_tags = ctx.get("line_n_token_tags")
    n1_tags = ctx.get("line_n1_token_tags")
    return _line_has_finite_verb(l_n, n_tags) and _line_has_finite_verb(l_n1, n1_tags)


@_register_guard("cross_verse")
def _g_cross_verse(l_n, l_n1, ctx):
    # always False — engine already verse-scopes; this guard is a no-op marker
    return False


@_register_guard("line_n_ends_with_sof_pasuq")
def _g_n_sof_pasuq(l_n, l_n1, ctx):
    """Fire (block) if line N ends with sof pasuq (׃ — verse-end marker).

    Sof pasuq on the verb's line is the strongest Masoretic signal that the
    cantillation marked it as clause-final, NOT subject-pending. Used by
    M4.d (intransitive V + postposed S): when `וַיָּמֹֽת׃` ends a verse,
    the next verse begins a fresh clause — the bare-NP on the next content
    line is NOT the postposed subject of the dying-verb. (See 1Kings 16:18
    `וַיָּמֹֽת׃ | עַל־חַטֹּאתָיו` — "and-he-died." closes verse N; verse N+1
    begins "for his sins...".)
    """
    return l_n.rstrip().endswith("׃")


@_register_guard("inf_abs_finite_root_mismatch")
def _g_inf_abs_root_mismatch(l_n, l_n1, ctx):
    """Fire (block) when inf-abs on N's last token + finite-verb on N+1's
    first token have skel-consonant-overlap < 2 (different roots).

    Used by m_inf_abs_finite_pair to enforce the same-root requirement of
    Joüon-Muraoka §123 emphatic construction. Filters Eccl `הַרְבֵּה`
    adverbial cases (TAHOT-tagged Vha but functionally adverbial; next-line
    finite verb is from a different root) and similar.

    For maqqef-bound inf-abs (`לֹא־מוֹת`), uses skel of the LAST
    sub-word (the inf-abs `מות`), not the whole compound.
    """
    n_last = M.last_content_token(l_n)
    n1_first = M.first_content_token(l_n1)
    if not n_last or not n1_first:
        return False
    s1 = M.skel_of_last_sub(n_last)
    s2 = M.skel(n1_first)
    return M.skel_consonant_overlap(s1, s2) < 2


@_register_guard("line_n_starts_with_do_marker")
def _g_n_starts_do(l_n, l_n1, ctx):
    """Fire (block) when line N starts with אֵת / וְאֵת (DO marker).

    Use case: m2_4 (subject NP + verb merge) shouldn't fire when line N is
    a stranded DO continuation of the prior clause, not a new subject NP.
    """
    first = M.first_content_token(l_n)
    if not first:
        return False
    return M.is_do_marker_token(first)


@_register_guard("next_line_is_vav_coord_pp")
def _g_next_vav_coord_pp(l_n, l_n1, ctx):
    """Fire (block emission) if line N+1's first token is a vav-coordinated PP head.

    Use case: prevents merge specs (m2_6, h14, etc.) from re-absorbing
    coordinated-PP members that S1 has just split out of an enumeration.
    Without this guard, splits and merges oscillate (split → merge → split → ...).
    """
    first = M.first_content_token(l_n1)
    if not first:
        return False
    return M.is_vav_coord_pp_head(first)


@_register_guard("next_line_is_wayehi_ken")
def _g_next_wayehi_ken(l_n, l_n1, ctx):
    """Fire (block emission) if line N+1 starts with the discourse formula
    וַיְהִי־כֵן. The formula is its own atomic thought (canon §1, S3 pattern 1)
    and merge specs that legitimately fire on (PP, finite-verb) pairs (e.g.
    h11_2 mid-verse short-fronting) must not absorb it.
    """
    first = M.first_content_token(l_n1)
    if not first:
        return False
    return M.is_wayehi_ken_token(first)


@_register_guard("next_line_is_vav_coord_np")
def _g_next_vav_coord_np(l_n, l_n1, ctx):
    """Fire (block emission) if line N+1's first token is a vav-coord NP head.

    Symmetric counterpart to next_line_is_vav_coord_pp for the S2 split
    direction. Prevents merge specs from re-absorbing post-S2-split
    coordinated-NP enumeration members.
    """
    first = M.first_content_token(l_n1)
    if not first:
        return False
    return M.is_vav_coord_np_head(first)


@_register_guard("next_line_is_vav_coord_do_marker")
def _g_next_vav_coord_do_marker(l_n, l_n1, ctx):
    """Fire (block emission) if line N+1's first token is a vav-coord DO marker
    (וְאֵת / וְאֶת־X / וְאֹתוֹ-suffix forms).

    Symmetric counterpart to next_line_is_vav_coord_pp/np for coordinated
    DO-marker enumeration members. Prevents M2 merge specs (specifically
    m2_3_verb_subj_do_split) from re-absorbing post-S4-split coordinated-DO
    continuation lines and oscillating with S4 multi-wayyiqtol-clause-split
    (Gen 33:2 / 36:6 / 1:25 / 8:1 / 10:11 / 10:14 / 11:31 / 12:5 / 14:5,
    confirmed 2026-05-03).
    """
    first = M.first_content_token(l_n1)
    if not first:
        return False
    return M.skel(first).startswith("ואת")


@_register_guard("next_line_is_wayyiqtol")
def _g_next_wayyiqtol(l_n, l_n1, ctx):
    """Fire (block emission) if line N+1's first token is a wayyiqtol.

    Use case: prevents merge specs from re-absorbing wayyiqtol-headed lines
    that S3/S4 has just split out from cross-clause material. Symmetric
    counterpart to next_line_is_vav_coord_pp for the S3 split direction.

    Implementation: TAHOT-tag-driven primary path (correctly classifies
    forms like וָאֶתֶּן where the skel "ואתן" overlaps with the 2fp pronoun
    `אתן` in YIQTOL_KNOWN_NOUNS, causing skel-only detection to false-
    negative). Skel fallback for tokens without tags. The niqqud-aware
    is_wayyiqtol_token misses dagesh-omitting wayyiqtols like וַיְהִי
    (the most common wayyiqtol form), so the skel fallback is broader
    than is_wayyiqtol_token and mirrors S3's _is_wayyiqtol_skel_at trigger
    (vav + YIQTOL prefix consonant + length-4-floor + YIQTOL_KNOWN_NOUNS
    exclusion).
    """
    # Tag-driven path: check FIRST tag of FIRST token of l_n1
    n1_tag_lists = ctx.get("line_n1_token_tags") or []
    if n1_tag_lists and n1_tag_lists[0]:
        from . import morph_tags as MT
        if any(MT.is_wayyiqtol(tag) for tag in n1_tag_lists[0]):
            return True
        # If we have tags and none are wayyiqtol, trust the tag (don't fall back).
        # The TAHOT tag is authoritative; skel-fallback would re-introduce the
        # very class of FNs this fix exists to remove.
        return False
    # Skel fallback (no tags available)
    first = M.first_content_token(l_n1)
    if not first:
        return False
    if M.MAQQEF in first:
        first = first.split(M.MAQQEF, 1)[0]
    s = M.skel(first)
    if len(s) < 4 or s[0] != "ו" or s[1] not in M.YIQTOL_PREFIXES:
        return False
    inner = s[1:]
    if inner in M.YIQTOL_KNOWN_NOUNS:
        return False
    return True


@_register_guard("next_line_is_verb_initial")
def _g_next_verb_initial(l_n, l_n1, ctx):
    """Fire (block) if the line AFTER the candidate pair (lookahead) starts with
    a finite verb.

    Use case: when line N+1 is a PP and lookahead is verb-initial, line N+1 is
    a fronted PP for the lookahead clause — NOT a recipient/complement of line N.
    Without this guard, m2_6 (verb+subj + PP-recipient) over-merges parallel-
    structure verses like Gen 1:27 (where 'בצלם אלהים' is fronting for 'ברא אתו',
    not a complement of the prior 'ויברא אלהים את־האדם בצלמו').
    """
    lookahead = ctx.get("lookahead", "")
    if not lookahead:
        return False
    first = M.first_content_token(lookahead)
    if not first:
        return False
    la_tags = ctx.get("lookahead_token_tags") or []
    if la_tags:
        head = MA.head_tag_for_token(la_tags[0])
        if head:
            return MT.is_finite_verb(head)
    return M.is_finite_verb_token(first)


@_register_guard("prev_line_incomplete")
def _g_prev_incomplete(l_n, l_n1, ctx):
    """Fire (block emission) if line N-1 lacks a finite verb.

    Use case: distinguishes genuine fronting (prev clause is complete; line N
    is a fronted constituent for the NEXT clause) from stranded modifier
    (prev clause is incomplete; line N is extending it, not fronting).
    Without prev context (verse start), don't block — let other guards decide.
    """
    prev = ctx.get("prev_line", "")
    if not prev:
        return False
    return not _line_has_finite_verb(prev, ctx.get("prev_line_token_tags"))


@_register_guard("m2_pp_prep_mismatch")
def _g_m2_prep(l_n, l_n1, ctx):
    """Block emission when next-line prep is not in the M2 verb's allowed-prep set.

    Fires (True = block) when the first prep of l_n1 is not among the
    prepositions that the M2 verb on the last token of l_n governs.
    """
    last = M.last_content_token(l_n)
    if not last:
        return True  # no verb token found → block
    allowed = M.m2_pp_verb_allowed_preps(last)
    if not allowed:
        return True  # not an M2 verb → block
    first_n1 = M.first_content_token(l_n1)
    if not first_n1:
        return True
    prep_skel = M.skel(first_n1)
    # Standalone prep skeleton match (e.g., "אל")
    if prep_skel in allowed:
        return False  # match → don't block
    # Bound-prep single-letter prefix match (e.g., "ל" from "לְ")
    if prep_skel and prep_skel[0] in allowed:
        return False
    return True  # no match → block


@_register_guard("m2_pp_prep_mismatch_first")
def _g_m2_pp_prep_first(l_n, l_n1, ctx):
    """Block emission when next-line prep is not in the M2-PP (speech) verb's
    allowed-prep set, with the verb anchored at FIRST token of l_n.

    Symmetric to m2_pp_prep_mismatch (which inspects last_content_token —
    correct for h18_3's V→PP shape where the verb IS the last token) but
    anchored to FIRST token for V+S→PP shapes (m2_8 — Exo 18:24
    וַיִּשְׁמַע מֹשֶׁה / לְקוֹל חֹתְנוֹ — last token of l_n is the subject NP,
    not the verb).

    Mirrors motion_locus_prep_mismatch's first-token anchor for the
    motion-verb closed list (M2.7 spec).
    """
    first = M.first_content_token(l_n)
    if not first:
        return True
    allowed = M.m2_pp_verb_allowed_preps(first)
    if not allowed:
        return True  # not an M2-PP verb at first position → block
    first_n1 = M.first_content_token(l_n1)
    if not first_n1:
        return True
    # Maqqef-joined prep+complement (e.g., אֶל־הֶבֶל): test the head sub-token
    if M.MAQQEF in first_n1:
        head = first_n1.split(M.MAQQEF, 1)[0]
        prep_skel = M.skel(head)
    else:
        prep_skel = M.skel(first_n1)
    if prep_skel in allowed:
        return False  # match → don't block
    if prep_skel and prep_skel[0] in allowed:
        return False  # bound-prep prefix match
    return True  # no match → block


@_register_guard("motion_locus_prep_mismatch")
def _g_motion_locus_prep(l_n, l_n1, ctx):
    """Block emission when next-line prep is not in the motion-locus verb's
    allowed locus-prep set.

    Fires (True = block) when the FIRST token of l_n is a motion-locus verb
    but the first prep of l_n1 is not among the locus prepositions the verb
    governs (per MOTION_LOCUS_VERB_SKELETONS). Symmetric to m2_pp_prep_mismatch
    but anchored to FIRST token of l_n (motion wayyiqtols are clause-initial)
    rather than last token (which may be the subject NP in V+S→PP shapes
    like Gen 50:1 וַיִּפֹּל יוֹסֵף).
    """
    first = M.first_content_token(l_n)
    if not first:
        return True
    allowed = M.motion_locus_verb_allowed_preps(first)
    if not allowed:
        return True  # not a motion-locus verb → block
    first_n1 = M.first_content_token(l_n1)
    if not first_n1:
        return True
    # Maqqef-joined prep+complement (e.g., עַל־פְּנֵי): test the head sub-token
    if M.MAQQEF in first_n1:
        head = first_n1.split(M.MAQQEF, 1)[0]
        prep_skel = M.skel(head)
    else:
        prep_skel = M.skel(first_n1)
    if prep_skel in allowed:
        return False  # match → don't block
    if prep_skel and prep_skel[0] in allowed:
        return False  # bound-prep prefix match
    return True  # no match → block


def _guard_fires(guard, l_n: str, l_n1: str, ctx: dict[str, Any]) -> bool:
    """Run a single guard; return True if guard blocks emission."""
    if isinstance(guard, dict):
        kind = guard.get("skip_if")
    else:
        kind = guard
    fn = GUARD_DISPATCH.get(kind)
    if fn is None:
        # unknown guard — treat as not firing (don't silently suppress emission)
        return False
    return fn(l_n, l_n1, ctx)


# ─── spec runner ────────────────────────────────────────────────────


class SpecRunner:
    def __init__(self, specs_dir: str | Path):
        self.specs_dir = Path(specs_dir)
        self.specs: list[Spec] = self._load_specs()

    def _load_specs(self) -> list[Spec]:
        out = []
        for f in sorted(self.specs_dir.glob("*.yaml")):
            doc = yaml.safe_load(f.read_text(encoding="utf-8"))
            if doc is None:
                continue
            out.append(Spec.from_dict(doc))
        return out

    def run_corpus(self, corpus_dir: str | Path,
                   book_filter: Optional[str] = None,
                   rule_filter: Optional[str] = None,
                   severity_filter: Optional[str] = None) -> list[Finding]:
        findings: list[Finding] = []
        corpus_path = Path(corpus_dir)
        for book_dir in sorted(corpus_path.iterdir()):
            if not book_dir.is_dir():
                continue
            if book_filter and book_filter not in book_dir.name:
                continue
            for ch_file in sorted(book_dir.glob("*.txt")):
                findings.extend(self._scan_chapter(book_dir, ch_file,
                                                    rule_filter, severity_filter))
        return findings

    def _scan_chapter(self, book_dir: Path, ch_file: Path,
                      rule_filter: Optional[str],
                      severity_filter: Optional[str]) -> list[Finding]:
        text = ch_file.read_text(encoding="utf-8")
        verses = M.partition_into_verses(text)
        findings: list[Finding] = []
        # Build a flat line index for line-number reporting
        all_lines = text.splitlines()
        line_offsets: dict[tuple[int, int, int], int] = {}
        # map (chapter, verse, line_idx_within_verse) -> 1-based line number in file
        line_no = 0
        cur_ref = None
        within_idx = 0
        for raw in all_lines:
            line_no += 1
            line = raw.strip()
            if not line:
                continue
            if M.VERSE_REF_RE.match(line):
                ch_s, vs_s = line.split(":")
                cur_ref = (int(ch_s), int(vs_s))
                within_idx = 0
            else:
                if cur_ref is not None:
                    line_offsets[(cur_ref[0], cur_ref[1], within_idx)] = line_no
                    within_idx += 1

        # Load TAHOT morph alignment for this chapter (None if unavailable).
        chapter_morph = MA.load_chapter_morph(ch_file)

        for (chapter, verse), lines in verses:
            # Per-verse tag alignment: list[per_line_token_tag_lists] or None on mismatch.
            verse_token_tags: Optional[list[list[list[str]]]] = None
            if chapter_morph is not None:
                ortho_tags = chapter_morph.get(verse)
                if ortho_tags is not None:
                    verse_token_tags = MA.align_verse_tokens_to_tags(lines, ortho_tags)

            def _tags_at(idx: int) -> list[list[str]]:
                if verse_token_tags is None or idx < 0 or idx >= len(verse_token_tags):
                    return []
                return verse_token_tags[idx]

            # Pair-mode pass — line N + line N+1 (existing merge logic)
            for i in range(len(lines) - 1):
                l_n = lines[i]
                l_n1 = lines[i + 1]
                lookahead = lines[i + 2] if i + 2 < len(lines) else ""
                prev_line = lines[i - 1] if i >= 1 else ""
                ctx = {
                    "book": book_dir.name,
                    "chapter": chapter,
                    "verse": verse,
                    "lookahead": lookahead,
                    "prev_line": prev_line,
                    "line_idx_in_verse": i,
                    "line_n_token_tags": _tags_at(i),
                    "line_n1_token_tags": _tags_at(i + 1),
                    "lookahead_token_tags": _tags_at(i + 2),
                    "prev_line_token_tags": _tags_at(i - 1) if i >= 1 else [],
                }
                for spec in self.specs:
                    if spec.mode != "pair":
                        continue  # line-mode specs handled below
                    if rule_filter and spec.rule != rule_filter and spec.name != rule_filter:
                        continue
                    if severity_filter and spec.severity != severity_filter:
                        continue
                    if not _matches_trigger(spec, l_n, l_n1, ctx):
                        continue
                    skipped = False
                    for guard in spec.guards:
                        if _guard_fires(guard, l_n, l_n1, ctx):
                            skipped = True
                            break
                    if skipped:
                        continue
                    pwc = M.prosodic_word_count(l_n) + M.prosodic_word_count(l_n1)
                    annotation = spec.annotation_template or spec.description or spec.subcase
                    annotation = annotation.format(
                        prior=l_n, next=l_n1, pwc=pwc, rule=spec.rule
                    )
                    rel_path = str(ch_file.relative_to(Path.cwd())) if ch_file.is_absolute() else str(ch_file)
                    findings.append(Finding(
                        file=rel_path.replace("\\", "/"),
                        line=line_offsets.get((chapter, verse, i), 0),
                        rule=spec.rule,
                        subcase=spec.subcase,
                        severity=spec.severity,
                        book=book_dir.name,
                        chapter=chapter,
                        verse=verse,
                        prior_line=l_n,
                        next_line=l_n1,
                        prosodic_word_count=pwc,
                        annotation=annotation,
                        suggested_action=spec.suggested_action,
                    ))

            # Line-mode pass — single-line proposition-counting (splits)
            for i, line in enumerate(lines):
                ctx = {
                    "book": book_dir.name,
                    "chapter": chapter,
                    "verse": verse,
                    "line_idx_in_verse": i,
                    "lookahead": lines[i + 1] if i + 1 < len(lines) else "",
                    "prev_line": lines[i - 1] if i >= 1 else "",
                    "line_n_token_tags": _tags_at(i),
                    "line_n1_token_tags": [],
                    "lookahead_token_tags": _tags_at(i + 1),
                    "prev_line_token_tags": _tags_at(i - 1) if i >= 1 else [],
                }
                for spec in self.specs:
                    if spec.mode != "line":
                        continue
                    if rule_filter and spec.rule != rule_filter and spec.name != rule_filter:
                        continue
                    if severity_filter and spec.severity != severity_filter:
                        continue
                    split_positions = _evaluate_line_trigger(spec, line, ctx)
                    if not split_positions:
                        continue
                    # Run guards (line-mode guards receive line, [], ctx)
                    skipped = False
                    for guard in spec.guards:
                        if _guard_fires(guard, line, "", ctx):
                            skipped = True
                            break
                    if skipped:
                        continue
                    pwc = M.prosodic_word_count(line)
                    annotation = spec.annotation_template or spec.description or spec.subcase
                    annotation = annotation.format(
                        prior=line, next="", pwc=pwc, rule=spec.rule
                    )
                    rel_path = str(ch_file.relative_to(Path.cwd())) if ch_file.is_absolute() else str(ch_file)
                    findings.append(Finding(
                        file=rel_path.replace("\\", "/"),
                        line=line_offsets.get((chapter, verse, i), 0),
                        rule=spec.rule,
                        subcase=spec.subcase,
                        severity=spec.severity,
                        book=book_dir.name,
                        chapter=chapter,
                        verse=verse,
                        prior_line=line,
                        next_line="",
                        prosodic_word_count=pwc,
                        annotation=annotation,
                        suggested_action=spec.suggested_action,
                        split_positions=split_positions,
                    ))
        return findings


def _evaluate_line_trigger(spec: Spec, line: str, ctx: dict[str, Any]) -> list[int]:
    """Evaluate a line-mode spec's trigger; return split-position token-indices.

    Returns:
      [] if trigger doesn't fire
      [pos1, pos2, ...] of token indices where new line breaks should be inserted
    """
    t = spec.trigger
    line_anywhere = t.get("line_anywhere", {})

    # coordinated_pp_count: {min: N} — count vav-coord PP heads + initial bare PP
    # Tag-aware: pass per-token tags so PP-head classifiers distinguish
    # negation+verb (וְאַל־VERB) from genuine vav-prep (וְאֶל), avoiding S1
    # over-fire that oscillates with M-class merges (Obadiah 1:13 case).
    if "coordinated_pp_count" in line_anywhere:
        cond = line_anywhere["coordinated_pp_count"]
        positions = M.coordinated_pp_split_positions(line, ctx.get("line_n_token_tags"))
        if "min" in cond and not positions:
            return []
        return positions

    # coordinated_np_count: {min: N} — count vav-coord NP heads (S2 enumeration)
    if "coordinated_np_count" in line_anywhere:
        cond = line_anywhere["coordinated_np_count"]
        positions = M.coordinated_np_split_positions(line)
        if "min" in cond and not positions:
            return []
        return positions

    # wayyiqtol_mid_line: true — split before each wayyiqtol that appears at position > 0
    if line_anywhere.get("wayyiqtol_mid_line"):
        return M.wayyiqtol_mid_line_split_positions(line)

    # closed_list_clause_boundary_wayyiqtol: true — split before each wayyiqtol
    # whose immediate prior token matches one of S3's closed-list closer patterns.
    # Tag-aware: pass per-token TAHOT tag-lists so the helper distinguishes
    # וְאֵת (and-DO-marker, particle) from genuine wayyiqtols (same class as S4).
    if line_anywhere.get("closed_list_clause_boundary_wayyiqtol"):
        return M.closed_list_clause_boundary_split_positions(
            line, ctx.get("line_n_token_tags")
        )

    # multi_wayyiqtol_count: true — split before each non-initial wayyiqtol
    # when the line carries ≥2 wayyiqtols (S4 — see audit-B 2026-05-01).
    # Suppressions encoded in the helper (וַיְהִי frame, hendiadys, shared-DO pair).
    # Tag-aware: pass per-token TAHOT tag-lists so the helper distinguishes
    # וְאֵת (and-DO-marker, particle) from genuine wayyiqtols.
    if line_anywhere.get("multi_wayyiqtol_count"):
        return M.multi_wayyiqtol_clause_split_positions(line, ctx.get("line_n_token_tags"))

    # obligatory_pp_complement_split: true — split a line that starts with a
    # bound-prep PP and contains a mid-line wayyiqtol, ONLY when the prior
    # line's first verb is an obligatory-PP-verb whose allowed-prep set
    # matches the leading prep (S5 — Stan-flagged Exo 18:24, 2026-05-01).
    # Context-aware via prev_line + prev_line_token_tags from ctx.
    if line_anywhere.get("obligatory_pp_complement_split"):
        return M.obligatory_pp_complement_split_positions(
            line,
            prev_line=ctx.get("prev_line", ""),
            prev_line_token_tags=ctx.get("prev_line_token_tags"),
            line_token_tags=ctx.get("line_n_token_tags"),
        )

    return []


# ─── small helpers used by Spec evaluation ──────────────────────────

# Patch morphology with a one-shot helper used above
def _matches_prep_only(tok: str) -> bool:
    s = M.skel(tok)
    return s in M.PREP_SKELETONS


M._matches_prep_only = _matches_prep_only  # type: ignore[attr-defined]
