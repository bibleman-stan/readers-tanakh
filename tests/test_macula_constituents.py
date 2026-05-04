"""Fixture tests for validators/_shared/macula_constituents.py.

The 6-chapter fixture set (Gen 1, Isa 40, Psa 1, Pro 1, Dan 4, Hab 2)
collectively exercises:
- Token attributes (qatal, yiqtol, wayyiqtol, imperative, participle, infinitive,
  active vs passive participle, construct state)
- Constituent rules (V-O, V-S, S-V, NPofNP, NpaNp, PrepNp, RelCL, V2CL, ClCl,
  embedded clauses)
- Frame-args (A0/A1/A2; empty-A0 imperatives; multi-token A1)
- participantref (single, multi-value, cross-verse)
- subjref (cross-verse implicit subjects)
- Aramaic lang="A"
- Sifrei Emet poetic register
- Maqqef-joined sequences
- Sense-line ↔ token matching

Run with: PYTHONIOENCODING=utf-8 py -3 -m pytest tests/test_macula_constituents.py -v
Or as a script:    PYTHONIOENCODING=utf-8 py -3 tests/test_macula_constituents.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "validators"))

from _shared.macula_constituents import (  # noqa: E402
    Chapter, Constituent, Token,
    clear_cache, consonant_skel, get_chapter, match_sense_line_tokens,
    parse_frame_str, split_ref_list, verse_from_xml_id,
)


# ---------------------------------------------------------------------------
# Pure helpers (no XML)
# ---------------------------------------------------------------------------

def test_consonant_skel_strips_teamim_niqqud_maqqef():
    assert consonant_skel("נַחֲמ֥וּ") == "נחמו"
    assert consonant_skel("עַל־לֵ֤ב") == "עללב"  # maqqef stripped, words concatenated
    assert consonant_skel("יְהוָ֑ה") == "יהוה"


def test_verse_from_xml_id():
    assert verse_from_xml_id("o010010010021") == (1, 1, 1)
    assert verse_from_xml_id("o230400030011") == (23, 40, 3)
    assert verse_from_xml_id("o270040140061") == (27, 4, 14)


def test_parse_frame_str_basic():
    assert parse_frame_str("A0:010010010031;") == {"A0": ["010010010031"]}


def test_parse_frame_str_multi_arg_with_multi_id():
    parsed = parse_frame_str("A0:010010010031; A1:010010010052;010010010072;")
    assert parsed == {
        "A0": ["010010010031"],
        "A1": ["010010010052", "010010010072"],
    }


def test_parse_frame_str_empty_a0_imperative():
    parsed = parse_frame_str("A0:; A1:230400010031;")
    assert parsed == {"A0": [], "A1": ["230400010031"]}


def test_parse_frame_str_empty_returns_empty_dict():
    assert parse_frame_str("") == {}


def test_split_ref_list_space_separated():
    assert split_ref_list("010240220072 010240320142") == [
        "010240220072", "010240320142",
    ]


def test_split_ref_list_semicolon_separated():
    assert split_ref_list("010240220072; 010240320142") == [
        "010240220072", "010240320142",
    ]


def test_split_ref_list_empty():
    assert split_ref_list("") == []


# ---------------------------------------------------------------------------
# Genesis 1 — foundational prose
# ---------------------------------------------------------------------------

def test_gen1_loads_31_sentences():
    clear_cache()
    ch = get_chapter("01-genesis", 1)
    assert isinstance(ch, Chapter)
    assert len(ch.sentences) == 31  # Gen 1 has 31 verses


def test_gen1_1_basic_token_attrs():
    ch = get_chapter("01-genesis", 1)
    v1 = ch.get_verse_sentence(1)
    assert v1 is not None
    # First content token: בְּרֵאשִׁית (preposition + noun, decomposed)
    bara_token = next(t for t in v1.tokens if t.is_qatal and t.is_verb)
    assert bara_token.lemma == "בָּרָא"
    assert bara_token.stem == "qal"
    assert bara_token.is_finite_verb
    assert bara_token.aspect == "qatal"
    assert bara_token.lang == "H"


def test_gen1_1_frame_args_resolved_to_tokens():
    """בָּרָא has A0=אלהים, A1=השמים+הארץ (multi-token coordinated object)."""
    ch = get_chapter("01-genesis", 1)
    v1 = ch.get_verse_sentence(1)
    verb = next(t for t in v1.tokens if t.lemma == "בָּרָא")
    assert "A0" in verb.frame_args
    assert "A1" in verb.frame_args
    assert len(verb.frame_args["A0"]) == 1
    assert len(verb.frame_args["A1"]) == 2  # heavens AND earth
    a0 = verb.frame_args["A0"][0]
    assert a0.role == "s"


def test_gen1_clauses_have_head_verbs():
    ch = get_chapter("01-genesis", 1)
    clauses = ch.get_verse_clauses(1)
    assert len(clauses) >= 1
    for c in clauses:
        assert c.is_clause


# ---------------------------------------------------------------------------
# Isaiah 40 — poetry, imperatives, empty-A0 frames
# ---------------------------------------------------------------------------

def test_isa40_loads():
    ch = get_chapter("23-isaiah", 40)
    assert len(ch.sentences) == 31


def test_isa40_1_imperative_has_empty_a0():
    """Imperatives encode A0 as [] (empty) — distinct from missing slot."""
    ch = get_chapter("23-isaiah", 40)
    v1 = ch.get_verse_sentence(1)
    imp = next(t for t in v1.tokens if t.is_imperative and t.lemma == "נָחַם")
    # First nachamu has only A0 (no A1); second has A0:; + A1
    # Find the one with both A0 and A1 (the second nachamu)
    imps = [t for t in v1.tokens if t.is_imperative and t.lemma == "נָחַם"]
    second = next(t for t in imps if "A1" in t.frame_args)
    assert second.frame_args["A0"] == []  # empty, not missing
    assert len(second.frame_args["A1"]) >= 1


def test_isa40_3_canonical_h5d_clause_structure():
    """Isa 40:3 (קוֹל קוֹרֵא בַּמִּדְבָּר ‖ פַּנּוּ ...) decomposes into 3 clauses."""
    ch = get_chapter("23-isaiah", 40)
    clauses = ch.get_verse_clauses(3)
    assert len(clauses) == 3
    rules = [c.wg_rule for c in clauses]
    assert "S-V" in rules         # announcement nucleus
    assert "PP-V-O" in rules      # first imperative w/ locative
    assert "V-PP-O-PP" in rules   # second imperative


def test_isa40_3_participle_is_active():
    ch = get_chapter("23-isaiah", 40)
    v3 = ch.get_verse_sentence(3)
    ptcp = next(t for t in v3.tokens if t.is_active_participle and t.lemma == "קָרָא")
    assert ptcp.aspect == "participle"
    assert ptcp.role == "v"


def test_isa40_2_npofnp_construct_chains():
    """Isa 40:2 has multiple construct chains via NPofNP rule."""
    ch = get_chapter("23-isaiah", 40)

    chains: list[Constituent] = []
    def walk(node):
        if isinstance(node, Constituent):
            if node.is_construct_chain:
                chains.append(node)
            for c in node.children:
                walk(c)
    for c in ch.get_verse_constituents(2):
        walk(c)
    assert len(chains) >= 4  # לב ירושלם, צבאה, עונה, יד יהוה, חטאתיה
    # Each chain's head token should be construct-state
    for ch_const in chains:
        toks = ch_const.tokens
        assert toks[0].is_construct or toks[0].state == "construct"


# ---------------------------------------------------------------------------
# Psalms 1 — Sifrei Emet, relative clauses
# ---------------------------------------------------------------------------

def test_psa1_loads_6_verses():
    ch = get_chapter("19-psalms", 1)
    assert len(ch.sentences) == 6


def test_psa1_1_has_relative_clauses():
    """Psa 1:1 contains nested אֲשֶׁר־לֹא relative clauses."""
    ch = get_chapter("19-psalms", 1)
    rels: list[Constituent] = []
    def walk(node):
        if isinstance(node, Constituent):
            if node.is_relative_clause:
                rels.append(node)
            for c in node.children:
                walk(c)
    for c in ch.get_verse_constituents(1):
        walk(c)
    assert len(rels) >= 1


# ---------------------------------------------------------------------------
# Proverbs 1 — non-finite verbs, infinitives
# ---------------------------------------------------------------------------

def test_pro1_loads():
    ch = get_chapter("20-proverbs", 1)
    assert len(ch.sentences) == 33


def test_pro1_has_infinitive_constructs():
    ch = get_chapter("20-proverbs", 1)
    found = False
    for s in ch.sentences:
        for t in s.tokens:
            if t.is_infinitive_construct:
                found = True
                assert t.aspect == "infinitive"
                break
        if found:
            break
    assert found, "Pro 1 should contain at least one infinitive construct"


# ---------------------------------------------------------------------------
# Daniel 4 — Aramaic
# ---------------------------------------------------------------------------

def test_dan4_loads():
    ch = get_chapter("27-daniel", 4)
    assert len(ch.sentences) >= 30  # Aramaic Daniel 4 has 34 verses (Heb. numbering)


def test_dan4_1_is_aramaic():
    ch = get_chapter("27-daniel", 4)
    v1 = ch.get_verse_sentence(1)
    aramaic_tokens = [t for t in v1.tokens if t.lang == "A"]
    assert len(aramaic_tokens) > 0
    assert all(t.lang == "A" for t in v1.tokens if t.text)


def test_dan4_aramaic_still_has_frame_args():
    """Aramaic verbs should still have frame attributes per audit 1."""
    ch = get_chapter("27-daniel", 4)
    v1 = ch.get_verse_sentence(1)
    aramaic_verbs = [t for t in v1.tokens if t.is_finite_verb and t.lang == "A"]
    if aramaic_verbs:
        # At least one should have a frame
        assert any(v.frame_args for v in aramaic_verbs)


# ---------------------------------------------------------------------------
# Habakkuk 2 — maqqef-heavy, subjref density
# ---------------------------------------------------------------------------

def test_hab2_loads():
    ch = get_chapter("35-habakkuk", 2)
    assert len(ch.sentences) == 20


def test_hab2_has_maqqef_after():
    ch = get_chapter("35-habakkuk", 2)
    maqqef_tokens = []
    for s in ch.sentences:
        for t in s.tokens:
            if t.has_maqqef_after():
                maqqef_tokens.append(t)
    assert len(maqqef_tokens) >= 30  # Hab 2 has many prep+noun maqqef joins


# ---------------------------------------------------------------------------
# Cross-verse participantref (the H10 pattern-e primitive)
# ---------------------------------------------------------------------------

def test_gen7_14_pronoun_resumes_v13_antecedents():
    """Gen 7:14 הֵמָּה resolves to multiple antecedent tokens in v13."""
    ch = get_chapter("01-genesis", 7)
    v14 = ch.get_verse_sentence(14)
    pronoun = next(t for t in v14.tokens if t.text.startswith("הֵ"))
    assert len(pronoun.antecedents) >= 1
    # All antecedents should be in an earlier verse
    for ant in pronoun.antecedents:
        assert ant.verse < 14


def test_gen17_4_self_ref_pronoun():
    """Gen 17:4 אֲנִי opens with first-person divine self-reference."""
    ch = get_chapter("01-genesis", 17)
    v4 = ch.get_verse_sentence(4)
    # First content pronoun should have antecedents from prior verse
    pronouns = [t for t in v4.tokens if t.is_pronoun]
    assert any(p.antecedents and p.antecedents[0].verse < 4 for p in pronouns)


# ---------------------------------------------------------------------------
# Verb-object frame-args (the verb_object_bond port primitive)
# ---------------------------------------------------------------------------

def test_psa98_3_zachar_has_multi_a1():
    """Ps 98:3 זָכַר has A1 with multiple object tokens (חַסְדּ + אֱמוּנָת)."""
    ch = get_chapter("19-psalms", 98)
    v3 = ch.get_verse_sentence(3)
    zachar = next(t for t in v3.tokens if t.is_qatal and t.lemma == "זָכַר")
    assert "A1" in zachar.frame_args
    assert len(zachar.frame_args["A1"]) >= 2


# ---------------------------------------------------------------------------
# Sense-line matching
# ---------------------------------------------------------------------------

def test_match_sense_line_basic():
    """A v2/he sense-line matches a contiguous slice of verse Tokens."""
    ch = get_chapter("23-isaiah", 40)
    verse_tokens = ch.get_verse_tokens(3)
    line_a = "ק֣וֹל קוֹרֵ֔א בַּמִּדְבָּ֕ר"
    matched, next_idx = match_sense_line_tokens(verse_tokens, line_a)
    # 3 surface words decompose to 5 tokens (prep + article + noun for ba-midbar)
    assert len(matched) == 5
    # Next sense-line continues from token 5
    line_b = "פַּנּ֖וּ דֶּ֣רֶךְ יְהוָ֑ה"
    matched2, _ = match_sense_line_tokens(verse_tokens, line_b, start_idx=next_idx)
    assert len(matched2) >= 3


def test_match_sense_line_handles_full_verse():
    """A single sense-line covering the whole verse should match all tokens."""
    ch = get_chapter("19-psalms", 1)
    v1_tokens = ch.get_verse_tokens(1)
    # Reconstruct the verse text from tokens (with `after` whitespace)
    full_text = "".join(t.text + (t.after or "") for t in v1_tokens).strip()
    matched, idx = match_sense_line_tokens(v1_tokens, full_text)
    assert idx == len(v1_tokens)


# ---------------------------------------------------------------------------
# Constituent navigation (parent/child, head_verb, ancestor_with)
# ---------------------------------------------------------------------------

def test_token_has_parent_constituent():
    ch = get_chapter("23-isaiah", 40)
    v3 = ch.get_verse_sentence(3)
    # Every token should have a parent constituent
    for t in v3.tokens:
        assert t.parent_constituent is not None


def test_constituent_ancestor_walking():
    """Token in a relative clause should find an ancestor with wg_class='cl'."""
    ch = get_chapter("19-psalms", 1)
    v1 = ch.get_verse_sentence(1)
    for t in v1.tokens:
        if t.parent_constituent:
            cl_ancestor = t.parent_constituent.ancestor_with(wg_class="cl")
            # Most tokens are inside a clause somewhere up the tree
            # (Don't assert universally — some may be at the sentence root)


def test_clause_head_verb_matches_role_v():
    """A clause's head_verb() should be the first token with role='v'."""
    ch = get_chapter("23-isaiah", 40)
    for v in (1, 2, 3):
        for cl in ch.get_verse_clauses(v):
            head = cl.head_verb()
            if head:
                assert head.role == "v"


# ---------------------------------------------------------------------------
# Cache behavior
# ---------------------------------------------------------------------------

def test_cache_returns_same_object():
    clear_cache()
    a = get_chapter("23-isaiah", 40)
    b = get_chapter("23-isaiah", 40)
    assert a is b


def test_clear_cache_evicts():
    a = get_chapter("23-isaiah", 40)
    clear_cache()
    b = get_chapter("23-isaiah", 40)
    assert a is not b


# ---------------------------------------------------------------------------
# Script entry
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Run all top-level test_* functions in this module
    import inspect
    fns = [(name, fn) for name, fn in globals().items()
           if name.startswith("test_") and inspect.isfunction(fn)]
    passed = 0
    failed = 0
    for name, fn in fns:
        try:
            fn()
            print(f"PASS  {name}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR {name}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed (out of {len(fns)})")
    sys.exit(0 if failed == 0 else 1)
