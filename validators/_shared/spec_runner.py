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


def _matches_token(tok: Optional[str], conditions: dict[str, Any]) -> bool:
    """Apply token-level conditions: skeleton_in / morphology / morphology_one_of."""
    if not tok:
        return False
    if "skeleton_in" in conditions:
        if M.skel(tok) not in set(conditions["skeleton_in"]):
            return False
    if "morphology" in conditions:
        if not _check_morphology(tok, conditions["morphology"]):
            return False
    if "morphology_one_of" in conditions:
        if not any(_check_morphology(tok, m) for m in conditions["morphology_one_of"]):
            return False
    if "skeleton_starts_with" in conditions:
        prefixes = conditions["skeleton_starts_with"]
        if isinstance(prefixes, str):
            prefixes = [prefixes]
        if not any(M.skel(tok).startswith(p) for p in prefixes):
            return False
    return True


def _check_morphology(tok: str, morph: str) -> bool:
    """Single-morphology check by name."""
    if morph == "finite_verb":
        return M.is_finite_verb_token(tok)
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
    if morph == "do_marker":
        return M.is_do_marker_token(tok)
    if morph == "bare_do_marker":
        return M.is_bare_do_marker_token(tok)
    if morph == "bare_prep":
        return M.is_bare_prep_token(tok)
    if morph == "construct_head":
        return M.is_construct_head_token(tok)
    if morph == "definite_adjective":
        return M.is_definite_adjective_token(tok)
    return False


def _matches_anywhere(line: str, conditions: dict[str, Any]) -> bool:
    """Apply line-level conditions: has_finite_verb, has_resumptive_suffix, ..."""
    if "has_finite_verb" in conditions:
        if M.has_finite_verb(line) != conditions["has_finite_verb"]:
            return False
    if "has_resumptive_suffix" in conditions:
        if M.line_has_resumptive_suffix(line) != conditions["has_resumptive_suffix"]:
            return False
    return True


def _matches_trigger(spec: Spec, l_n: str, l_n1: str, ctx: dict[str, Any]) -> bool:
    t = spec.trigger
    if "line_n_last_token" in t:
        if not _matches_token(M.last_content_token(l_n), t["line_n_last_token"]):
            return False
    if "line_n_first_token" in t:
        if not _matches_token(M.first_content_token(l_n), t["line_n_first_token"]):
            return False
    if "line_n1_first_token" in t:
        if not _matches_token(M.first_content_token(l_n1), t["line_n1_first_token"]):
            return False
    if "line_n1_last_token" in t:
        if not _matches_token(M.last_content_token(l_n1), t["line_n1_last_token"]):
            return False
    if "line_n_anywhere" in t:
        if not _matches_anywhere(l_n, t["line_n_anywhere"]):
            return False
    if "line_n1_anywhere" in t:
        if not _matches_anywhere(l_n1, t["line_n1_anywhere"]):
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
    return M.has_finite_verb(l_n) and M.has_finite_verb(l_n1)


@_register_guard("cross_verse")
def _g_cross_verse(l_n, l_n1, ctx):
    # always False — engine already verse-scopes; this guard is a no-op marker
    return False


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


@_register_guard("next_line_is_wayyiqtol")
def _g_next_wayyiqtol(l_n, l_n1, ctx):
    """Fire (block emission) if line N+1's first token is a wayyiqtol.

    Use case: prevents merge specs (m5, m4, m2_4, m2_6, etc.) from
    re-absorbing wayyiqtol-headed lines that S3 has just split out from
    cross-clause material. Symmetric counterpart to next_line_is_vav_coord_pp
    for the S3 split direction.

    Implementation: reuses M.YIQTOL_PREFIXES and M.YIQTOL_KNOWN_NOUNS
    so the guard is symmetric-by-construction with S3's trigger
    (wayyiqtol_mid_line_split_positions) — both move together when the
    lexicon is updated.
    """
    first = M.first_content_token(l_n1)
    if not first:
        return False
    s = M.skel(first)
    if len(s) < 3 or s[0] != "ו" or s[1] not in M.YIQTOL_PREFIXES:
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
    return not M.has_finite_verb(prev)


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

        for (chapter, verse), lines in verses:
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
    if "coordinated_pp_count" in line_anywhere:
        cond = line_anywhere["coordinated_pp_count"]
        positions = M.coordinated_pp_split_positions(line)
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

    return []


# ─── small helpers used by Spec evaluation ──────────────────────────

# Patch morphology with a one-shot helper used above
def _matches_prep_only(tok: str) -> bool:
    s = M.skel(tok)
    return s in M.PREP_SKELETONS


M._matches_prep_only = _matches_prep_only  # type: ignore[attr-defined]
