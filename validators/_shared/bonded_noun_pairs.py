"""Bonded noun pairs for JM177-bonded-pair constraint (Hebrew Constraint Catalog v1).

Per Joüon-Muraoka §177 / Waltke-O'Connor §4.6.5: certain noun pairs function as
single rhetorical-semantic units (hendiadys, merism, or cognate-pair). A line
break between the two elements of such a pair violates the rhetorical unit's
integrity.

This is the **active 13-pair structural list** referenced by the catalog spec.
Distinct from `hendiadys_lemma_pairs.py` (which contains an 88-pair DORMANT
verb-pair list that is reference-only / not mechanically consulted).

Lemmas are NFC-normalized; comparison consumers should also NFC-normalize.

Status: DRAFT v1 — entries to be validated against corpus fixtures before
promotion to settled status per `change-protocol.md` §7.8 proposed-rule
adoption protocol.
"""

from __future__ import annotations

import unicodedata


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


# 13-pair structural bonded-noun list.
#
# Each entry is a frozenset of two NFC-normalized lemmas. frozenset (not tuple)
# because order is irrelevant — חֶסֶד וֶאֱמֶת and אֱמֶת וְחֶסֶד both fire.
#
# Selection criteria: well-attested in BH grammars (JM §177, WO §4.6.5) as
# bonded pairs OR documented as classical merism/hendiadys in the standard
# scholarly literature. Not synonymity-by-similarity; structural pairing only.

BONDED_NOUN_PAIRS: frozenset[frozenset[str]] = frozenset({
    # Cosmic merisms (totality via polar pairs)
    frozenset({_nfc("שָׁמַיִם"), _nfc("אֶרֶץ")}),       # heaven + earth (Gen 1:1)
    frozenset({_nfc("יָם"), _nfc("יַבָּשָׁה")}),        # sea + dry land (Jonah 1:9)
    frozenset({_nfc("בֹּקֶר"), _nfc("עֶרֶב")}),         # morning + evening (narrative cycle)
    frozenset({_nfc("יוֹם"), _nfc("לַיְלָה")}),         # day + night

    # Classical hendiadys (two terms = one concept)
    frozenset({_nfc("תֹּהוּ"), _nfc("בֹּהוּ")}),         # formless + void = chaos (Gen 1:2)
    frozenset({_nfc("חֶסֶד"), _nfc("אֱמֶת")}),          # mercy + truth = covenant-loyalty (Gen 24:27)

    # Vulnerable-class merisms (legal/ethical)
    frozenset({_nfc("יָתוֹם"), _nfc("אַלְמָנָה")}),      # orphan + widow (Deut 27:19)
    frozenset({_nfc("עָנִי"), _nfc("אֶבְיוֹן")}),       # poor + needy (Ps 35:10)
    frozenset({_nfc("גֵּר"), _nfc("תּוֹשָׁב")}),         # sojourner + resident-alien (Gen 23:4)

    # Ethical / forensic pairs
    frozenset({_nfc("צֶדֶק"), _nfc("מִשְׁפָּט")}),       # justice + judgment (Ps 89:14, Isa 9:6)
    frozenset({_nfc("אַף"), _nfc("חֵמָה")}),            # anger + wrath (Ps 78:38)

    # Wealth / material pairs
    frozenset({_nfc("כֶּסֶף"), _nfc("זָהָב")}),         # silver + gold (canonical WO §4.6.5 example)
})


# Degenerate self-pairs: same lemma duplicated for emphasis (Deut 25:13 weights
# differ; Prov 20:10 just/unjust measure). frozenset({x, x}) collapses to {x}
# (cardinality 1), so these can't live in BONDED_NOUN_PAIRS — they need their
# own lookup that detects "both tokens have the same lemma AND that lemma is in
# the self-pair list."
SELF_PAIR_LEMMAS: frozenset[str] = frozenset({
    _nfc("אֶבֶן"),    # stone + stone (Deut 25:13 — diverse weights)
    _nfc("אֵיפָה"),    # ephah + ephah (Prov 20:10 — diverse measures)
})


def is_bonded_pair(lemma_a: str, lemma_b: str) -> bool:
    """Return True if (lemma_a, lemma_b) — in either order — is a bonded pair.

    Handles both regular bonded pairs (two distinct lemmas) and degenerate
    self-pairs (same lemma duplicated for emphasis).

    Inputs MUST be NFC-normalized lemmas (the comparison set uses NFC).
    """
    a, b = _nfc(lemma_a), _nfc(lemma_b)
    # Regular pairs: two distinct lemmas
    if a != b:
        return frozenset({a, b}) in BONDED_NOUN_PAIRS
    # Self-pair: same lemma duplicated
    return a in SELF_PAIR_LEMMAS
