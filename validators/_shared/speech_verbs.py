"""Shared speech-verb skeleton sets for cross-validator use.

The bare speech-verb skeletons (wayyiqtol forms of speech roots) are needed
by multiple validators:
  - validators/colometry/validate_speech_intro_framing.py — H5b leading speech
    frame split logic
  - validators/syntax/validate_verb_object_bond.py — H5b precedence guard
    (suppress verb-object bond fire when prior line is a speech intro frame)

Centralized here to prevent drift. Both validators should import from this
module rather than maintaining parallel copies.
"""

# Wayyiqtol forms of speech roots (אמר/דבר/ענה/יסף + idiomatic ויוסף לאמר).
# Skeletons (consonants only after stripping niqqud/te'amim).
BARE_SPEECH_VERB_SKELETONS = frozenset({
    "ויאמר",    # wayyiqtol qal 3ms — and he said
    "ויאמרו",   # wayyiqtol qal 3mp — and they said
    "וידבר",    # wayyiqtol piel 3ms — and he spoke
    "וידברו",   # wayyiqtol piel 3mp — and they spoke
    "ותאמר",    # wayyiqtol qal 3fs — and she said
    "ותאמרו",   # wayyiqtol qal 2/3 fp — and you/they (f) said
    "ותדבר",    # wayyiqtol piel 3fs — and she spoke
    "ויען",     # wayyiqtol qal 3ms — and he answered
    "ותען",     # wayyiqtol qal 3fs — and she answered
    "ויוסף",    # wayyiqtol hiphil 3ms — and he added/continued
})
