"""
binding_rules.py — the 14 validated Hebrew binding rules (B1-B14, B4 retired).

Importable module: `from binding_rules import apply_bindings`.

Each rule fires based on BHSA-derived clause features and is justified by the
bidirectional test (see ../atu-method/docs/framework.md §2 and
../atu-method/docs/binding-rules-hebrew.md).

A global same-verse guard refuses any binding across verse boundaries.
"""

from __future__ import annotations
import re

# Hebrew points + accents + dots — collectively the "pointing" layer.
# Stripping reduces text to consonants, robust to Unicode-order variations
# of the same vowel/dot combination across sources.
_POINTING_RE = re.compile(r"[֑-ׇ]")

WAYYIQTOL_TYPES = {"Way0", "WayX"}

# Temporal-anchor consonant prefixes for B5 (matched after pointing strip).
WAYHI_ANCHOR_CONSONANT_PREFIXES = ("אחר", "ביום", "בהיות", "כאשר", "כי", "ב")

# Verbs of cognition (head_verb_lemma) that license B11 ki-complement binding.
COGNITION_VERB_LEMMAS = {"ידע", "ראה", "שׁמע", "חשׁב", "זכר", "בין", "הכיר"}


def strip_pointing(text: str) -> str:
    """Strip Hebrew pointing (cantillation + vowels + dots) for consonant matching."""
    return _POINTING_RE.sub("", text)


def should_bind(prev: dict, curr: dict) -> tuple[bool, str | None]:
    """Decide if curr binds to prev. Return (should_bind, rule_name)."""

    # Global safety: bindings only fire within a single verse.
    if prev["verse"] != curr["verse"]:
        return False, None

    # B1 — Vocative binds backward
    if curr["typ"] == "Voct":
        return True, "B1-vocative"

    # B2 — Appositive / Defective (object-marker check)
    if curr["typ"] == "Defc":
        curr_decant = strip_pointing(curr["text"]).lstrip()
        if curr_decant.startswith("את") or curr_decant.startswith("ואת"):
            return True, "B2-appositive"
        # else: fronted-subject Defc; let it start its own group

    # B3 — Restrictive ʾăšer
    curr_consonants = strip_pointing(curr["text"]).lstrip()
    if curr_consonants.startswith("אשר"):
        return True, "B3-restrictive-asher"

    # B5 — Wayhi temporal frame
    prev_consonants = strip_pointing(prev["text"]).lstrip()
    if (
        prev["head_verb_lemma"] == "היה"
        and prev["typ"] in WAYYIQTOL_TYPES
        and prev_consonants.startswith("ויהי")
        and any(
            anchor in prev_consonants[:30]
            for anchor in WAYHI_ANCHOR_CONSONANT_PREFIXES
        )
    ):
        return True, "B5-wayhi-frame"

    # B6 — Casus pendens resumption
    if prev["typ"] == "CPen":
        return True, "B6-cpen-resumption"

    # B7 — Bare wayyiqtol pair (hendiadys-like)
    prev_token_count = len(prev["text"].split())
    if (
        prev["typ"] == "Way0"
        and prev_token_count <= 1
        and curr["typ"] in WAYYIQTOL_TYPES
    ):
        return True, "B7-bare-wayyiqtol-pair"

    # B8 — Hineh-presentative + asyndetic-qatal attribute
    if (
        prev["typ"] == "NmCl"
        and prev_consonants.startswith(("הנה", "והנה"))
        and curr["typ"] == "ZQt0"
    ):
        return True, "B8-hineh-presentative"

    # B9 — Ne'um authenticating formula
    if (
        curr["typ"] == "NmCl"
        and curr_consonants.startswith("נאם")
    ):
        return True, "B9-neum-formula"

    # B10 — Purposive infinitive construct
    if curr["typ"] == "InfC":
        return True, "B10-purposive-infc"

    # B11 — Verb-of-cognition + ki-complement
    if (
        prev["head_verb_lemma"] in COGNITION_VERB_LEMMAS
        and curr_consonants.startswith("כי")
    ):
        return True, "B11-cognition-ki-complement"

    # B12 — Reop (re-opening / discourse-resumption) binds forward
    if prev["typ"] == "Reop":
        return True, "B12-reop-binding"

    # B13 — Participial ATTRIBUTE binds to prev (refined — only when prev is היה)
    if curr["typ"] == "Ptcp" and prev["head_verb_lemma"] == "היה":
        return True, "B13-participial-attribute"

    # B14 — Asyndetic yiqtol/qatal predicate
    if curr["typ"] in ("ZYq0", "ZQt0"):
        return True, "B14-asyndetic-predicate"

    return False, None


def apply_bindings(clauses: list[dict], book_folder: str = "", chapter: int = 0) -> list[dict]:
    """Group consecutive clause-atoms into ATU candidate groups by applying binding rules.

    Each clause dict must have keys: cid, verse, clause_idx_in_verse, typ, rela,
    head_verb_lemma, head_verb_text, text.

    When book_folder + chapter are provided, Aramaic verses are guarded:
    each Aramaic clause becomes its own group (no binding-rule firing).
    Empirical sweep (Pipeline B Round 2, 2026-06-03): without the guard
    181 silent false-fires across 1,378 Aramaic clause-atoms; with the
    guard, 0. See aramaic_guard.py for the held ranges.

    Returns a list of ATU candidate group dicts.
    """
    if not clauses:
        return []

    from aramaic_guard import is_aramaic_verse

    def _is_aramaic(c: dict) -> bool:
        if not book_folder:
            return False
        return is_aramaic_verse(book_folder, chapter, c["verse"])

    groups: list[dict] = []
    current = {"clauses": [clauses[0]], "bindings_fired": []}

    for c in clauses[1:]:
        prev = current["clauses"][-1]
        # Aramaic guard: refuse cross-clause binding when either side is
        # in a held Aramaic range. Each Aramaic clause-atom becomes its
        # own ATU group regardless of surface morphology.
        if _is_aramaic(prev) or _is_aramaic(c):
            groups.append(current)
            current = {"clauses": [c], "bindings_fired": []}
            continue
        bind, rule = should_bind(prev, c)
        if bind:
            current["clauses"].append(c)
            current["bindings_fired"].append(rule)
        else:
            groups.append(current)
            current = {"clauses": [c], "bindings_fired": []}

    if current:
        groups.append(current)

    # Materialize
    out = []
    for i, g in enumerate(groups):
        clause_cids = [c["cid"] for c in g["clauses"]]
        verses = [c["verse"] for c in g["clauses"]]
        text = " ".join(c["text"] for c in g["clauses"])
        out.append({
            "group_idx": i,
            "verse_first": verses[0],
            "verse_last": verses[-1],
            "n_clauses": len(g["clauses"]),
            "bindings_fired": g["bindings_fired"],
            "clause_cids": clause_cids,
            "clause_typs": [c["typ"] for c in g["clauses"]],
            "text": text,
        })

    return out
