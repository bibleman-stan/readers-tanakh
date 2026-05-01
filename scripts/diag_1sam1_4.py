"""Diagnostic: trace m2_verb_bare_np_rebond failure on 1 Sam 1:4 lines 21-22."""
import sys
sys.path.insert(0, '.')
from validators._shared import morphology as M

line_n  = "וַיִּזְבַּ֖ח"
line_n1 = "אֶלְקָנָ֑ה"

print("=== LINE N:", repr(line_n), "===")
print("skel:", M.skel(line_n))
print("is_finite_verb_token:", M.is_finite_verb_token(line_n))
print("is_wayyiqtol_token:", M.is_wayyiqtol_token(line_n))
print("is_finite_verb_skel:", M.is_finite_verb_skel(M.skel(line_n)))
print("has_finite_verb:", M.has_finite_verb(line_n))
print("prosodic_word_count:", M.prosodic_word_count(line_n))

print()
print("=== LINE N+1:", repr(line_n1), "===")
print("skel:", M.skel(line_n1))
print("first_content_token:", repr(M.first_content_token(line_n1)))
print("is_finite_verb_token:", M.is_finite_verb_token(line_n1))
print("is_bare_noun_token:", M.is_bare_noun_token(line_n1))
print("is_vav_coord_np_head:", M.is_vav_coord_np_head(line_n1))
print("has_finite_verb:", M.has_finite_verb(line_n1))
print("prosodic_word_count:", M.prosodic_word_count(line_n1))

combined = M.prosodic_word_count(line_n) + M.prosodic_word_count(line_n1)
print()
print("=== COMBINED PWC:", combined, "(max 8) ===")

first = M.first_content_token(line_n1)
if first and M.MAQQEF in first:
    first_for_guard = first.split(M.MAQQEF, 1)[0]
else:
    first_for_guard = first
s = M.skel(first_for_guard) if first_for_guard else ""
print()
print("=== next_line_is_wayyiqtol guard (applied to line N+1 as the 'next line') ===")
print("skel for guard:", s)
print("len(s)>=4:", len(s) >= 4)
print("s[0]=='ו':", bool(s and s[0] == 'ו'))
print("guard fires:", bool(s and len(s) >= 4 and s[0] == 'ו' and s[1] in M.YIQTOL_PREFIXES))
