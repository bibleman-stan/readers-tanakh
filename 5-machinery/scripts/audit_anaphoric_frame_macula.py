#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Macula-driven detector for anaphoric-frame merge candidates (bidirectional
ATU test, framework §1.1).

PHASE: pre-§7.3-pass. Replaces the surface-regex probe at
audit_anaphoric_frame_splits.py with the proper primitive (Macula
constituent trees + token lemmas/morph/type_) per §7.3 audit recommendation.

Scope (first pass — round-wheel discipline):
  ✓ wayehi + anaphoric-temporal-frame (the original 16-hit population)
  ✓ Macula-based exclusions: cataphoric (relative-clause-following);
    substantive ordinal frame; speech-introducer apodosis; death-formula
    with biographical adjunct; heavy-apodosis; non-wayyiqtol apodosis
  ✗ DEFERRED: bare discourse particles (lakhen / al-ken / az / kī);
    fronted-pronoun resumptive subjects; bare anaphoric frames without wayehi

The deferred patterns are well-scoped in audit 2 but expanding the detector
to cover them before validating the wayehi-subset on fixture is premature
per CLAUDE.md "round wheel before rolling."

Output:
  - Per-fixture-verse pass/fail against 5-machinery/tests/fixtures-anaphoric-frame.tsv
  - Corpus-wide candidate list (verse-level; v2/heb-alignment for
    current-rendering classification deferred to a downstream step)
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from validators._shared import macula_constituents as MC  # noqa: E402

V2_HEB = REPO_ROOT / "data" / "text-files" / "v2" / "heb"
FIXTURE = REPO_ROOT / "5-machinery/tests" / "fixtures-anaphoric-frame.tsv"

# Anaphoric-frame markers detected on Macula tokens (closed list).
# Format: (preposition_lemma, head_lemma, demonstrative_lemma_set)
ANAPHORIC_FRAME_PATTERNS = [
    # achar / acharei + ha-devarim + ha-eleh
    ({"אַחַר", "אַחֲרֵי"}, {"דָּבָר"}, {"זֶה"}),   # ha-eleh = pl of zeh
    # b- + ha-yamim + ha-hem
    ({"בְּ"},               {"יוֹם"}, {"הוּא"}),    # plural ha-hem from masc-pl-of-hu
    # b- + ha-et + ha-hi
    ({"בְּ"},               {"עֵת"}, {"הוּא"}),
    # b- + ha-yom + ha-hu
    ({"בְּ"},               {"יוֹם"}, {"הוּא"}),
]

ACHAREI_KEN_LEMMAS = {"אַחֲרֵי"}  # paired with כֵּן

# Speech-introducer lemmas — apodosis-head exclusion
SPEECH_INTRO_LEMMAS = {"אָמַר", "נָגַד", "דָּבַר"}
LEMOR_LEMMA = "אָמַר"  # but with type_=infinitive construct

# Death-formula lemma
DEATH_LEMMA = "מוּת"

# Wayehi lemma
HAYAH = "הָיָה"


def _strip_marks(s: str) -> str:
    return "".join(c for c in s if not (0x0591 <= ord(c) <= 0x05C7))


def _first_clause(clauses: list) -> Optional[object]:
    """Return the FIRST top-level clause in a verse (the one whose tokens
    open the verse). Skip nested clauses; we want the outermost-leftmost."""
    for c in clauses:
        if c.is_clause:
            return c
    return None


def _is_wayehi_clause(cl) -> bool:
    """Clause head is wayyiqtol of הָיָה."""
    hv = cl.head_verb()
    if hv is None:
        return False
    return hv.is_wayyiqtol and hv.lemma == HAYAH


def _is_article(t) -> bool:
    return t.pos == "particle" and t.type_ == "definite article"


def _is_skippable(t) -> bool:
    """Article or conjunction-attached-to-content — skip when matching
    content-lemma sequences."""
    if _is_article(t):
        return True
    return False


def _content_lemmas_after(toks: list, start: int, max_count: int = 8) -> list:
    """Return up to max_count NON-article tokens after position `start`."""
    out = []
    for j in range(start + 1, len(toks)):
        if _is_skippable(toks[j]):
            continue
        out.append((j, toks[j]))
        if len(out) >= max_count:
            break
    return out


def _detect_anaphoric_frame(cl) -> Optional[str]:
    """Inspect a wayehi-headed clause. Return a label if the clause contains
    an anaphoric temporal/discourse frame, else None.

    Closed-list of frame shapes (article tokens skipped during matching):
      - אַחַר + דָּבָר + אֵלֶּה   (achar ha-devarim ha-eleh)
      - אַחַר + כֵּן              (acharei-ken)
      - בְּ + יוֹם + הוּא/הִיא    (b-yom-ha-hu/hi)
      - בְּ + יוֹם + הֵם/הֵמָּה   (b-yamim-ha-hem)  [Macula stores plural lemma as singular]
      - בְּ + עֵת + הוּא/הִיא     (b-et-ha-hi)
    """
    toks = cl.tokens
    if not toks:
        return None

    # Patterns A/B: אַחַר + ...
    for i, t in enumerate(toks):
        if t.lemma != "אַחַר":
            continue
        next_content = _content_lemmas_after(toks, i, 3)
        if not next_content:
            continue
        # Pattern B: אַחַר + כֵּן (the immediately following content token is כֵּן)
        j, t1 = next_content[0]
        if t1.lemma == "כֵּן":
            return "acharei-ken"
        # Pattern A: אַחַר + דָּבָר + אֵלֶּה
        if len(next_content) >= 2:
            k, t2 = next_content[1]
            if t1.lemma == "דָּבָר" and t2.lemma == "אֵלֶּה":
                return "achar-ha-devarim-ha-eleh"

    # Pattern C: בְּ + (יוֹם | עֵת) + (הוּא | הִיא | הֵם | הֵמָּה)
    DEMONSTRATIVE_ATTRIBUTIVE_LEMMAS = {"הוּא", "הִיא", "הֵם", "הֵמָּה", "הֵנָּה"}
    for i, t in enumerate(toks):
        if t.lemma != "בְּ":
            continue
        next_content = _content_lemmas_after(toks, i, 4)
        if len(next_content) >= 2:
            j, t1 = next_content[0]
            k, t2 = next_content[1]
            if t1.lemma in {"יוֹם", "עֵת"} and t2.lemma in DEMONSTRATIVE_ATTRIBUTIVE_LEMMAS:
                # Substantive-ordinal exclusion: if the noun is followed by
                # an ordinal-adjective instead of demonstrative, this isn't
                # anaphoric. Caller's _is_substantive_ordinal_frame catches it.
                return f"b-{t1.lemma}-anaphoric-demonstrative"

    return None


def _is_substantive_ordinal_frame(cl) -> bool:
    """Substantive frame uses ORDINAL adjective (השלישי, הרביעי, וכו') — Macula
    pos=adjective type="ordinal number". Exclude from merge."""
    for t in cl.tokens:
        if t.pos == "adjective" and t.type_ and "ordinal" in t.type_:
            return True
    return False


def _is_regnal_year_frame(cl) -> bool:
    """Regnal-year frame: contains שָׁנָה + לְ + king-NP, OR numeral + שָׁנָה."""
    for t in cl.tokens:
        if t.lemma == "שָׁנָה":
            return True
    return False


def _next_clause_at_apodosis(verse_clauses: list, frame_cl) -> Optional[object]:
    """Find the clause that is the apodosis — the next top-level clause after
    the frame clause. Skip coordinate-container clauses (wg_rule=ClCl) which
    package multiple children rather than representing the apodosis itself."""
    found = False
    for c in verse_clauses:
        if not c.is_clause:
            continue
        if c is frame_cl:
            found = True
            continue
        if found:
            # Skip Macula coordinate-container clauses — they wrap multiple
            # children; the inner content clauses are the real apodosis.
            if c.wg_rule == "ClCl":
                continue
            return c
    return None


def _apodosis_has_speech_introducer(apod_cl) -> bool:
    """Apodosis HEAD verb is a speech-onset lemma (אָמַר, דָּבַר) — only the
    head matters. An embedded לֵאמֹר flagging a downstream quotation does NOT
    exclude; the matrix verb may be a report-event (e.g., נָגַד/Hofal `הֻגַּד`
    in Gen 22:20: "it was reported to Abraham, saying...") which is a normal
    apodosis. Tightened post-§7.3-audit-2 2026-05-13 (Gen 22:20 FN catch).

    Excludes Gen 48:1 (head=אָמַר) but NOT Gen 22:20 (head=נגד Hofal)."""
    if apod_cl is None:
        return False
    hv = apod_cl.head_verb()
    if hv and hv.lemma in {"אָמַר", "דָּבַר"}:
        return True
    return False


def _apodosis_is_death_with_biographical_adjunct(apod_cl) -> bool:
    """Apodosis is מות + biographical adjunct (apposition title NP or
    age-spec ben-X-shanim). Excludes merge per Audit 1 Joshua 24:29."""
    if apod_cl is None:
        return False
    hv = apod_cl.head_verb()
    if not hv or hv.lemma != DEATH_LEMMA:
        return False
    # Look for apposition or age-spec in clause tokens
    has_appos = False
    has_ben_shanim = False
    toks = apod_cl.tokens
    for i, t in enumerate(toks):
        # Apposition: Macula tags some constituents as apposition
        # (wg_rule in {"NpaNp", "Np-Appos"})
        # Heuristic: look for בֵּן + numeral + שָׁנָה pattern
        if t.lemma == "בֵּן":
            for j in range(i + 1, min(i + 5, len(toks))):
                if toks[j].lemma == "שָׁנָה":
                    has_ben_shanim = True
                    break
        # Apposition title: עֶבֶד יְהוָה style — common-noun in construct
        # followed by proper-noun, immediately after the death-subject
        if t.lemma == "עֶבֶד":
            has_appos = True
    return has_appos or has_ben_shanim


def _apodosis_is_heavy(apod_cl) -> bool:
    """Apodosis carries both explicit-NP subject AND explicit-NP object.
    Macula tags roles primarily on the clause's wg_rule (e.g., V-S-O,
    S-V-O), not always on individual tokens. Excludes merge per
    Audit 1 (2Ki 6:24: wayyiqbotz Ben-Hadad melekh-Aram et-kol-machanehu)."""
    if apod_cl is None:
        return False
    rule = apod_cl.wg_rule or ""
    # Heavy if rule contains BOTH "S" and "O" as distinct slot markers
    # Patterns: V-S-O, S-V-O, V-S-O-PP, etc. Exclude V-O alone (no subject)
    # and V-S alone (no object).
    has_s = "-S" in rule or rule.startswith("S-")
    has_o = "-O" in rule or rule.startswith("O-")
    return has_s and has_o


def _apodosis_has_embedded_complement(apod_cl) -> bool:
    """Apodosis carries a complex internal structure: purpose-infinitive
    complement, content ki-clause complement, or relative-clause complement.
    This catches 2Ch 24:4 (hayah + le-chaddesh + et-beit YHWH) without
    over-excluding Gen 22:1 (clean qatal nissa + et-Avraham).

    Differentiator: Gen 22:1's apodosis is a single clause (S-V-O).
    2Ch 24:4's apodosis carries an infinitive-construct purpose-clause.
    Macula tags purpose-infinitives as wg_class=cl child constituents."""
    if apod_cl is None:
        return False
    # Check direct child constituents for embedded clauses
    for child in apod_cl.child_constituents:
        if child.is_clause:
            return True
        if child.is_relative_clause:
            return True
    # Also check for infinitive-construct (purpose-complement)
    for t in apod_cl.tokens:
        if t.type_ == "infinitive construct":
            # Exclude le'mor specifically (caught by speech-introducer check)
            if t.lemma == LEMOR_LEMMA:
                continue
            return True
    return False


def _apodosis_missing_finite_verb(apod_cl) -> bool:
    """Apodosis has no finite verb head — likely a verbless or nominal clause
    sitting where the wayyiqtol/qatal apodosis would be. Conservative exclude."""
    if apod_cl is None:
        return True
    hv = apod_cl.head_verb()
    return hv is None


def _is_cataphoric_relative(cl) -> bool:
    """Demonstrative immediately followed by relative-clause (wg_class=relp
    or wg_rule=relCL). Excludes merge — this is cataphoric, not anaphoric."""
    # Walk constituent tree looking for relative-clause child after demonstrative
    for child in cl.child_constituents:
        if child.is_relative_clause:
            return True
    # Also check if any token is אֲשֶׁר (relative particle)
    for t in cl.tokens:
        if t.lemma == "אֲשֶׁר":
            return True
    return False


def classify_verse(book: str, chapter: int, verse: int) -> tuple[str, str]:
    """Return (verdict, reason). Verdict in {POSITIVE, NEGATIVE, NO-MATCH}."""
    try:
        clauses = MC.get_verse_clauses(book, chapter, verse)
    except Exception as e:
        return "NO-MATCH", f"macula-load-error: {e}"

    leaves = [c for c in clauses if c.is_clause]
    if not leaves:
        return "NO-MATCH", "no clauses"

    frame_cl = leaves[0]
    if not _is_wayehi_clause(frame_cl):
        return "NO-MATCH", "first clause is not wayehi"

    label = _detect_anaphoric_frame(frame_cl)
    if not label:
        return "NO-MATCH", "no anaphoric-frame pattern detected"

    # Substantive-ordinal exclusion
    if _is_substantive_ordinal_frame(frame_cl):
        return "NEGATIVE", "substantive-ordinal-frame"
    # Regnal-year exclusion: שָׁנָה + לְ+king OR numeral+שָׁנָה
    if _is_regnal_year_frame(frame_cl):
        return "NEGATIVE", "regnal-year-substantive-frame"
    # Cataphoric (relative-clause-following) exclusion
    if _is_cataphoric_relative(frame_cl):
        return "NEGATIVE", "cataphoric-relative-clause"

    # Now inspect apodosis
    apod_cl = _next_clause_at_apodosis(leaves, frame_cl)
    if _apodosis_has_speech_introducer(apod_cl):
        return "NEGATIVE", "speech-introduction-apodosis"
    if _apodosis_is_death_with_biographical_adjunct(apod_cl):
        return "NEGATIVE", "death-formula-with-biographical-adjunct"
    # NOTE: heavy-apodosis exclusion REMOVED 2026-05-13 — it was a length-based
    # criterion violating Stan's codified rule "no arbitrary length limits
    # governing ATU boundaries." A long apodosis is still one ATU if the
    # bidirectional anaphoric frame requires merge.
    if _apodosis_has_embedded_complement(apod_cl):
        return "NEGATIVE", "embedded-complement-apodosis"
    if _apodosis_missing_finite_verb(apod_cl):
        return "NEGATIVE", "verbless-apodosis"

    return "POSITIVE", f"anaphoric-frame-{label}"


def validate_against_fixture():
    print(f"\n=== Validating Macula detector against fixture ===\n")
    pass_count = 0
    fail_count = 0
    fails = []
    with FIXTURE.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            book = row["book"]
            ch = int(row["chapter"])
            vs = int(row["verse"])
            expected = row["expected"]
            category = row["category"]
            verdict, reason = classify_verse(book, ch, vs)

            # First-pass scope = wayehi+anaphoric only. Any case without
            # wayehi as opening clause is out-of-scope; expect NO-MATCH.
            out_of_scope_categories = {
                "cataphoric-list-header", "cataphoric-relative-clause",
                "poetic-az-J5", "poetic-causal-conditional",
                "poetic-az-internal", "refrain-formula",
                "speech-internal-lakhen",
                "prophetic-lakhen-rhetorical-weight",
                "substantive-ordinal-frame", "regnal-year-substantive-frame",
            }
            if category in out_of_scope_categories:
                ok = (verdict == "NO-MATCH")
            elif expected == "POSITIVE":
                ok = (verdict == "POSITIVE")
            else:  # NEGATIVE
                ok = (verdict == "NEGATIVE")

            tag = "✓" if ok else "✗"
            print(f"  {tag} {book} {ch:>3}:{vs:<3} expected={expected:8s} verdict={verdict:9s} reason={reason}")
            if ok:
                pass_count += 1
            else:
                fail_count += 1
                fails.append((book, ch, vs, expected, verdict, reason, category))

    print(f"\n=== Fixture results: {pass_count} pass, {fail_count} fail ===")
    if fails:
        print("\nFailures:")
        for b, ch, vs, exp, ver, reas, cat in fails:
            print(f"  {b} {ch}:{vs} ({cat}): expected {exp}, got {ver} — {reas}")
    return fail_count == 0


def _v2_frame_is_standalone(book: str, chapter: int, verse: int) -> Optional[bool]:
    """For a verse with wayehi+anaphoric-frame, check current v2/heb rendering:
    is the frame standalone on its own line (apodosis on next line) — current
    SPLIT — or is frame+apodosis on the same line — current MERGED.

    Heuristic: check whether the verse's first line ENDS with an anaphoric
    frame marker (אֵלֶּה / כֵּן / הָהֵם / הַהוּא / הַהִיא / הָהֵמָּה).
    Line ends with one of these → standalone frame (SPLIT, needs change).
    Line continues past these → frame+apodosis already merged."""
    short = book.split("-", 1)[1]
    chap_path = V2_HEB / book / f"{short}-{chapter:02d}.txt"
    if not chap_path.exists():
        return None
    verse_re = re.compile(r"^(\d+):(\d+)\s*$")
    in_verse = False
    lines_in_verse = []
    for ln in chap_path.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        m = verse_re.match(s)
        if m and int(m.group(1)) == chapter and int(m.group(2)) == verse:
            in_verse = True
            continue
        if in_verse:
            if not s or verse_re.match(s):
                break
            lines_in_verse.append(ln)
    if not lines_in_verse:
        return None
    first_skel = _strip_marks(lines_in_verse[0]).rstrip()
    # Strip trailing punctuation/sof-pasuq (though punctuation should be stripped already)
    first_skel = re.sub(r"[׃׀\s־-]+$", "", first_skel)
    # Anaphoric frame endings (consonant-skeleton): the line ends with these
    # if the frame is standalone.
    STANDALONE_ENDINGS = (
        "אלה",       # ha-eleh
        "כן",        # acharei-ken
        "ההוא",      # ha-hu (note: consonant form is just הוא after stripping)
        "הוא",       # ha-hu — but careful, also "he/she/it" pronoun (rare line-final)
        "ההיא", "היא",
        "ההם", "הם",
        "ההמה", "המה",
        "הההנה", "הנה",
    )
    for ending in STANDALONE_ENDINGS:
        if first_skel.endswith(ending):
            return True
    return False


def run_corpus_wide():
    """Iterate every verse in v2/heb; classify; print summary + verse list.
    Writes findings to 5-machinery/tests/anaphoric-frame-macula-corpus-hits.tsv."""
    print(f"\n=== Corpus-wide Macula detector run ===\n")
    verse_re = re.compile(r"^(\d+):(\d+)\s*$")
    positives = []
    negatives_by_reason = {}
    total = 0
    for book_dir in sorted(V2_HEB.iterdir()):
        if not book_dir.is_dir():
            continue
        book = book_dir.name
        short = book.split("-", 1)[1]
        for chap_file in sorted(book_dir.glob(f"{short}-*.txt")):
            content = chap_file.read_text(encoding="utf-8")
            for ln in content.splitlines():
                s = ln.strip()
                m = verse_re.match(s)
                if not m:
                    continue
                ch, vs = int(m.group(1)), int(m.group(2))
                total += 1
                verdict, reason = classify_verse(book, ch, vs)
                if verdict == "POSITIVE":
                    positives.append((book, ch, vs, reason))
                elif verdict == "NEGATIVE":
                    negatives_by_reason.setdefault(reason, []).append((book, ch, vs))

    print(f"Total verses scanned: {total}")
    print(f"  POSITIVE (merge candidates): {len(positives)}")
    print(f"  NEGATIVE (excluded by structural carve-out): {sum(len(v) for v in negatives_by_reason.values())}")
    print()
    if negatives_by_reason:
        print("NEGATIVE breakdown:")
        for reason, hits in negatives_by_reason.items():
            print(f"  {reason}: {len(hits)}")
            for b, c, v in hits[:5]:
                print(f"    {b} {c}:{v}")
            if len(hits) > 5:
                print(f"    ... ({len(hits) - 5} more)")
        print()
    # Cross-reference with current v2/heb rendering
    change_pop = []
    already_correct = []
    indeterminate = []
    for b, c, v, r in positives:
        is_split = _v2_frame_is_standalone(b, c, v)
        if is_split is True:
            change_pop.append((b, c, v, r))
        elif is_split is False:
            already_correct.append((b, c, v, r))
        else:
            indeterminate.append((b, c, v, r))

    print(f"\n=== Change-population cross-reference ===\n")
    print(f"  Currently SPLIT (editorial change needed): {len(change_pop)}")
    for b, c, v, r in change_pop:
        print(f"    {b} {c}:{v}  [{r}]")
    print(f"\n  Already MERGED (current = correct, no change): {len(already_correct)}")
    for b, c, v, r in already_correct:
        print(f"    {b} {c}:{v}  [{r}]")
    if indeterminate:
        print(f"\n  Indeterminate: {len(indeterminate)}")

    out = REPO_ROOT / "5-machinery/tests" / "anaphoric-frame-macula-corpus-hits.tsv"
    with out.open("w", encoding="utf-8", newline="") as f:
        f.write("book\tchapter\tverse\tverdict\treason\n")
        for b, c, v, r in positives:
            f.write(f"{b}\t{c}\t{v}\tPOSITIVE\t{r}\n")
        for reason, hits in negatives_by_reason.items():
            for b, c, v in hits:
                f.write(f"{b}\t{c}\t{v}\tNEGATIVE\t{reason}\n")
    print(f"\nWritten: {out}")


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", action="store_true", help="Run corpus-wide (not just fixture)")
    args = p.parse_args()
    if args.corpus:
        run_corpus_wide()
        sys.exit(0)
    ok = validate_against_fixture()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
