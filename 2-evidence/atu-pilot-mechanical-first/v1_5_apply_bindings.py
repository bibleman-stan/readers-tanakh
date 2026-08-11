#!/usr/bin/env python3
"""
v1_5_apply_bindings.py — apply mechanical binding rules grounded in the
bidirectional test rubric to v1 clause-atoms, producing candidate ATU groups.

Binding rules (each tested between LAST clause of current open group and NEW clause):

  B1 — Vocative                  : new clause typ == 'Voct' → bind to prev
                                    (vocatives fail standalone bidirectional test)
  B2 — Appositive / Defective    : new clause typ == 'Defc' → bind to prev
  B3 — Restrictive ʾăšer         : new clause text starts with consonants אשר
                                    → bind to prev (relative-clause modifies head)
  B5 — Wayhi temporal frame      : prev head_verb_lemma == 'היה' AND prev typ in
                                    {Way0, WayX} AND prev text starts with
                                    vayhi/vehaya AND contains temporal anchor
                                    (consonant-stripped prefix אחר or other anchor)
  B6 — Casus pendens resumption  : prev typ == 'CPen' → bind curr to prev
  B7 — Bare wayyiqtol pair       : prev typ == 'Way0' AND prev is single token
                                    AND curr typ in {Way0, WayX} → hendiadys bind
  B8 — Hineh-presentative + asyndetic-qatal attribute
                                  : prev typ == 'NmCl' AND prev text starts with
                                    הנה/והנה AND curr typ == 'ZQt0' → bind
                                    (deictic introduction + descriptive participial)
  B9 — Ne'um authenticating formula
                                  : curr typ == 'NmCl' AND curr text starts with
                                    consonants נאם → bind to prev
                                    (oath/oracle tag binds to speech)
  B10 — Lemor speech-introduction infinitive
                                  : curr typ == 'InfC' AND curr head_verb_lemma
                                    == 'אמר' → bind to prev
                                    (infinitive of saying binds to reporting verb)

REMOVED — B4 (speech-frame to any non-wayyiqtol): replaced by the bidirectional
test principle. Speech-margin is its own ATU EXCEPT when the following clause
fails the bidirectional test (i.e., is a vocative alone — handled by B1).
Speech-margin + complete-clause speech always SPLIT, matching the rubric.

Output: one JSON line per ATU candidate group:
  - group_idx, verse_first/verse_last, n_clauses, bindings_fired,
    clause_cids, clause_typs, text
"""

from __future__ import annotations
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pilot_config as cfg

# Hebrew points + accents + dots — collectively the "pointing" layer.
# Stripping these reduces text to bare consonants, which is robust to
# unicode-order variations of the same vowel/dot combination across sources.
# Range U+0591..U+05C7 covers cantillation (te'amim) + niqqud (vowel marks) +
# shin/sin dots + meteg/rafe/etc.
_POINTING_RE = re.compile(r"[֑-ׇ]")


def strip_pointing(text: str) -> str:
    """Strip all Hebrew pointing (cantillation + vowels + dots) for consonant-level matching."""
    return _POINTING_RE.sub("", text)

OUT_DIR = cfg.PILOT_DIR
IN_JSONL = cfg.V1_JSONL
OUT_JSONL = cfg.V1_5_JSONL
OUT_TXT = cfg.V1_5_TXT

# Temporal anchor CONSONANT prefixes for B5 (matched after pointing strip).
# Covers אַחַר (after), אַחֲרֵי (after-plural), בַּיֹּום (on the day), etc.
WAYHI_ANCHOR_CONSONANT_PREFIXES = ("אחר", "ביום", "בהיות", "כאשר", "כי", "ב")

WAYYIQTOL_TYPES = {"Way0", "WayX"}


def should_bind(prev: dict, curr: dict) -> tuple[bool, str | None]:
    """Decide if curr binds to prev. Return (should_bind, rule_name)."""

    # Global safety: bindings only fire within a single verse.
    # ATU boundaries always coincide with or fall within verse boundaries.
    if prev["verse"] != curr["verse"]:
        return False, None

    # B1 — Vocative
    if curr["typ"] == "Voct":
        return True, "B1-vocative"

    # B2 — Appositive / Defective (refined)
    # BHSA tags Defc for BOTH appositive continuations (e.g., אֶת־יִצְחָק after
    # an object-marker-headed NP) AND fronted-subject NPs (e.g., וְכֹל as
    # subject of a following predicate). Only the appositive flavor binds
    # backward — detected by the object-marker prefix (את / ואת).
    if curr["typ"] == "Defc":
        curr_decant = strip_pointing(curr["text"]).lstrip()
        if curr_decant.startswith("את") or curr_decant.startswith("ואת"):
            return True, "B2-appositive"
        # else: fronted-subject Defc; let it start its own group

    # B3 — Restrictive ʾăšer (relative clause)
    # Match consonants only (אשר) after stripping pointing/cantillation/dots.
    # Robust to unicode-order variations (shin-dot vs segol order, etc.).
    # NOTE: not relying on rela=Attr since BHSA stores rela on `clause`, not `clause_atom`.
    # Excluded by construction: causal יַעַן אֲשֶׁר / עֵקֶב אֲשֶׁר (don't start with אֲשֶׁר).
    curr_consonants = strip_pointing(curr["text"]).lstrip()
    if curr_consonants.startswith("אשר"):
        return True, "B3-restrictive-asher"

    # B5 — Wayhi temporal frame (extended to match consonant prefix)
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

    # B7 — Bare single-word wayyiqtol (hendiadys-like motion pair)
    prev_token_count = len(prev["text"].split())
    if (
        prev["typ"] == "Way0"
        and prev_token_count <= 1
        and curr["typ"] in WAYYIQTOL_TYPES
    ):
        return True, "B7-bare-wayyiqtol-pair"

    # B8 — Hineh-presentative + asyndetic-qatal attribute
    # Deictic-introduction clause (NmCl starting with hineh/vehineh) + asyndetic
    # qatal clause describing the introduced entity form one ATU.
    # Example Gen 22:13: "vehineh ayil achar" + "ne'echaz basevakh bekarnav"
    if (
        prev["typ"] == "NmCl"
        and prev_consonants.startswith(("הנה", "והנה"))
        and curr["typ"] == "ZQt0"
    ):
        return True, "B8-hineh-presentative"

    # B9 — Ne'um authenticating formula
    # The נְאֻם־יהוה formula (and similar oracle tags) binds to its preceding speech.
    curr_consonants = strip_pointing(curr["text"]).lstrip()
    if (
        curr["typ"] == "NmCl"
        and curr_consonants.startswith("נאם")
    ):
        return True, "B9-neum-formula"

    # B10 — Purposive infinitive (broader than just לֵאמֹר)
    # InfC clauses bind to their main verb. Covers:
    #   - לֵאמֹר ("saying") after a speech-reporting verb
    #   - לִשְׁחֹט ("to slaughter") after a verb of action
    #   - Other purposive לְ + InfC patterns
    if curr["typ"] == "InfC":
        return True, "B10-purposive-infc"

    # B11 — Verb-of-cognition + ki-complement
    # A complement כִּי-clause binds to its preceding verb of cognition.
    # Detected by: curr clause starts with consonant prefix "כי" AND
    # prev clause's head verb lemma is in the cognition-verb set.
    COGNITION_VERB_LEMMAS = {"ידע", "ראה", "שׁמע", "חשׁב", "זכר", "בין", "הכיר"}
    if (
        prev["head_verb_lemma"] in COGNITION_VERB_LEMMAS
        and curr_consonants.startswith("כי")
    ):
        return True, "B11-cognition-ki-complement"

    # B12 — Reop (re-opening / discourse-resumption) binds forward
    # BHSA's Reop tag marks a bare conjunction that opens the following clause
    # (e.g., a stand-alone כִּי in oath contexts). The Reop is the "head" of the
    # following content; bind curr to prev.
    if prev["typ"] == "Reop":
        return True, "B12-reop-binding"

    # B13 — Participial ATTRIBUTE binds to prev (refined)
    # BHSA's Ptcp typ covers both attributive participles (Ps 1:3 'shatul' —
    # modifies prior NP, no own subject) and predicative participles (Ps 1:6
    # 'yodea Yahweh derekh tzadikim' — own subject + object). Only the
    # attributive flavor binds. Heuristic: bind only when prev clause's head
    # verb is היה (the canonical "vehayah ke-X + Ptcp-attribute" pattern).
    if curr["typ"] == "Ptcp" and prev["head_verb_lemma"] == "היה":
        return True, "B13-participial-attribute"

    # B14 — Asyndetic yiqtol/qatal predicate binds to prev subject-NP group
    # ZYq0 / ZQt0 are clauses without a waw-conjunction prefix. In subject-NP
    # constructions (Defc + relative + asyndetic-verb), the asyndetic verb is
    # the predicate of the fronted subject NP. Bind it to prev so the full
    # predication forms one ATU.
    # (B8 handles the specific hineh+ZQt0 case separately and earlier.)
    if curr["typ"] in ("ZYq0", "ZQt0"):
        return True, "B14-asyndetic-predicate"

    return False, None


def main() -> None:
    clauses: list[dict] = []
    with IN_JSONL.open(encoding="utf-8") as fp:
        for line in fp:
            if line.strip():
                clauses.append(json.loads(line))

    if not clauses:
        raise SystemExit("ERROR: no clauses found in v1_clauses.jsonl")

    print(f"Loaded {len(clauses)} clause-atoms from v1")

    # Build groups
    groups: list[dict] = []
    current: dict | None = None

    for c in clauses:
        if current is None:
            current = {
                "clauses": [c],
                "bindings_fired": [],
            }
            continue

        prev = current["clauses"][-1]
        bind, rule = should_bind(prev, c)
        if bind:
            current["clauses"].append(c)
            current["bindings_fired"].append(rule)
        else:
            groups.append(current)
            current = {"clauses": [c], "bindings_fired": []}

    if current is not None:
        groups.append(current)

    # Emit JSON
    out_rows: list[dict] = []
    for i, g in enumerate(groups):
        clause_cids = [c["cid"] for c in g["clauses"]]
        verses = [c["verse"] for c in g["clauses"]]
        text = " ".join(c["text"] for c in g["clauses"])
        out_rows.append({
            "group_idx": i,
            "verse_first": verses[0],
            "verse_last": verses[-1],
            "n_clauses": len(g["clauses"]),
            "bindings_fired": g["bindings_fired"],
            "clause_cids": clause_cids,
            "clause_typs": [c["typ"] for c in g["clauses"]],
            "text": text,
        })

    with OUT_JSONL.open("w", encoding="utf-8") as fp:
        for r in out_rows:
            fp.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Human-readable
    with OUT_TXT.open("w", encoding="utf-8") as fp:
        current_verse = None
        for r in out_rows:
            if r["verse_first"] != current_verse:
                if current_verse is not None:
                    fp.write("\n")
                if r["verse_first"] == r["verse_last"]:
                    fp.write(f"=== {cfg.VERSE_PREFIX}{r['verse_first']} ===\n")
                else:
                    fp.write(f"=== {cfg.VERSE_PREFIX}{r['verse_first']}-{r['verse_last']} ===\n")
                current_verse = r["verse_first"]
            tag = f"[{r['n_clauses']}c"
            if r["bindings_fired"]:
                tag += " <- " + ",".join(b.split("-")[0] for b in r["bindings_fired"])
            tag += "]"
            fp.write(f"  g{r['group_idx']:3d} {tag:20s}  {r['text']}\n")

    print(f"Wrote: {OUT_JSONL}")
    print(f"Wrote: {OUT_TXT}")

    # Stats
    n_groups = len(out_rows)
    n_with_binding = sum(1 for r in out_rows if r["bindings_fired"])
    binding_counts: dict[str, int] = {}
    for r in out_rows:
        for b in r["bindings_fired"]:
            binding_counts[b] = binding_counts.get(b, 0) + 1

    print(f"\n--- Pipeline reduction ---")
    print(f"  v1 clauses: {len(clauses)}")
    print(f"  v1.5 ATU candidate groups: {n_groups}  ({len(clauses) - n_groups} clauses bound away)")
    print(f"  Groups with binding(s) fired: {n_with_binding}")
    print(f"\n--- Bindings fired ---")
    for rule, count in sorted(binding_counts.items()):
        print(f"  {rule}: {count}")

    # Per-verse group counts
    by_verse: dict[int, int] = {}
    for r in out_rows:
        v = r["verse_first"]
        by_verse[v] = by_verse.get(v, 0) + 1
    print(f"\n--- Groups per verse ---")
    print("  " + ", ".join(f"v.{v}={n}" for v, n in sorted(by_verse.items())))


if __name__ == "__main__":
    main()
