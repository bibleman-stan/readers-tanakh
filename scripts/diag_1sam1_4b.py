"""Trace why אֶלְקָנָה is classified as a finite verb."""
import sys
sys.path.insert(0, '.')
from validators._shared import morphology as M

tok = "אֶלְקָנָ֑ה"
s = M.skel(tok)
print("token:", repr(tok))
print("skel:", repr(s))
print("len(s):", len(s))
print("s[0]:", s[0])
print("s[0] in YIQTOL_PREFIXES:", s[0] in M.YIQTOL_PREFIXES)
print("s in QATAL_COMMON:", s in M.QATAL_COMMON)
print("s not in YIQTOL_KNOWN_NOUNS:", s not in M.YIQTOL_KNOWN_NOUNS)

# Reproduce is_finite_verb_skel path
print()
print("--- is_finite_verb_skel path ---")
print("in QATAL_COMMON:", s in M.QATAL_COMMON)
# wayyiqtol path: starts with ו
print("starts with ו:", s[0] == "ו")
# weqatal path: starts with ו, inner in QATAL_COMMON
# yiqtol path: prefix (י/ת/א/נ) + ≥3 total chars
print("s[0] in YIQTOL_PREFIXES:", s[0] in M.YIQTOL_PREFIXES)
print("len(s) >= 3:", len(s) >= 3)
print("s not in YIQTOL_KNOWN_NOUNS:", s not in M.YIQTOL_KNOWN_NOUNS)
print("s != 'יש':", s != "יש")
print("len(s) >= 4:", len(s) >= 4)
print("=> yiqtol path returns True:", s[0] in M.YIQTOL_PREFIXES and len(s) >= 3 and s not in M.YIQTOL_KNOWN_NOUNS and s != "יש" and len(s) >= 4)

print()
print("is 'אלקנה' in YIQTOL_KNOWN_NOUNS:", "אלקנה" in M.YIQTOL_KNOWN_NOUNS)
