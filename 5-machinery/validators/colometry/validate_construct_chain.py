

def _find_repo_root():
    """Repo root by MARKER, not by counting parents.

    Counting encodes this file's depth in the tree, so moving the file silently
    breaks it and no text-based check notices. Anchoring on .git survives any
    move. Added 2026-08-10 after a reorg broke three different counted idioms.
    """
    from pathlib import Path as _P
    _here = _P(__file__).resolve()
    for _p in _here.parents:
        if (_p / ".git").exists():
            return _p
    return _here.parent

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate 1-method/canon Rule H2 — Construct Chain Default (IR-driven, with heuristic fallback).

Rule H2 (1-method/canon §5 H2; Joüon-Muraoka §129; Waltke-O'Connor §9):
A construct chain (nomen regens in construct state + nomen rectum) is a single
bound noun phrase. No line break may occur inside an unmodified construct chain.

Detection (primary: IR-driven; fallback: heuristic for synthetic/missing-XML input):

PRIMARY PATH — Macula lowfat constituent tree:
  Walk each verse's NPofNP constituent nodes. For each, map first/last token
  to editorial sense-lines via match_sense_line_tokens. Cross-line split → finding.

  Subcase classification (IR path):
    divine_name         — head or rectum lemma is a divine-name marker (YHWH,
                          אֲדֹנָי, אֱלֹהִים, צְבָאוֹת, שַׁדַּי, עֶלְיוֹן, יָהּ)
                          frozen-formula compounds; STRONG-MERGE-CANDIDATE.
    npofnp_split        — all other IR-detected NPofNP splits.
                          Short chains (≤4 tokens, no embedded relative clause)
                          with no oscillation-blocker → STRONG-MERGE-CANDIDATE.
                          Longer / complex chains → REVIEW-REQUIRED.
    (article_rectum and common_construct_ending are heuristic-path-only subcases.)

FALLBACK PATH — heuristic-based (fires when IR returns empty for a verse,
  e.g. synthetic fixture text with no Macula XML):
    divine_name         — line ends with YHWH/אדני/אלהים canonical forms;
                          next line starts with a known divine-name follower.
                          STRONG-MERGE-CANDIDATE.
    article_rectum      — non-articulated last token; articulated first token
                          of next line (ה + consonant). REVIEW-REQUIRED.
    common_construct_ending — line-final token is a member of the
                          common-construct-form closed list. REVIEW-REQUIRED.

  Fallback suppression guards (identical to prior heuristic):
    - Last token has sof pasuq (verse-end) → suppress.
    - First token of next line is a clause-starting conjunction (וַ/כִּי/אֲשֶׁר)
      for common_construct_ending → suppress.

Severity summary:
  STRONG-MERGE-CANDIDATE: divine_name (both paths); short npofnp_split (IR path)
  REVIEW-REQUIRED:        article_rectum; common_construct_ending (heuristic);
                          complex/long npofnp_split (IR path)

Sof-pasuq suppression: NPofNPs whose final token sits at verse-end (sof pasuq)
are NOT cross-line splits. Suppressed in both paths.

Architectural constraint:
  No te'amim glyph triggers anywhere. The IR exposes constituent structure,
  morph, role, and frame semantics — none accent-derived.

Output format:
    [DEVIATION]  file:line_number  H2/construct  SEVERITY  brief description

Exit code: 0 if zero violations, 1 if violations found, 2 on setup error.

Usage:
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_construct_chain.py
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_construct_chain.py --book jonah
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_construct_chain.py --v2
    PYTHONIOENCODING=utf-8 py -3 5-machinery/validators/colometry/validate_construct_chain.py --verbose
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants — collapsed two-tier layout: v1/he-baseline + v2/heb
# ---------------------------------------------------------------------------
REPO_ROOT = _find_repo_root()
V1_DIR = REPO_ROOT / "data" / "text-files" / "v1" / "he-baseline"
V2_DIR = REPO_ROOT / "data" / "text-files"  / "v2" / "heb"

# ---------------------------------------------------------------------------
# Macula IR import
# ---------------------------------------------------------------------------
sys.path.insert(0, str(REPO_ROOT / "5-machinery/validators"))
from _shared import macula_constituents as MC  # noqa: E402

# ---------------------------------------------------------------------------
# Hebrew Unicode constants
# ---------------------------------------------------------------------------

# Niqqud / cantillation marks to strip when isolating consonant skeleton
# U+0591–U+05C7: Hebrew cantillation and points
HEBREW_POINTS_RE = re.compile(r"[֑-ׇ]")

# Sof pasuq (verse-end mark)
SOF_PASUQ = "׃"

# He article prefix pattern on a word's consonant skeleton
_HE_ARTICLE_RE = re.compile(r"^ה[^א-ת]*[א-ת]")  # ה + consonant


# ---------------------------------------------------------------------------
# Verse-reference / blank line handling
# ---------------------------------------------------------------------------

VERSE_REF_RE = re.compile(r"^(\S+\s+)?\d+:\d+\s*$")


def is_skippable(line: str) -> bool:
    """Return True for blank lines and verse-reference-only lines."""
    s = line.strip()
    if not s:
        return True
    if VERSE_REF_RE.match(s):
        return True
    return False


def parse_verse_ref(line: str):
    """If `line` is a 'C:V' verse-reference line, return (chapter, verse). Else None."""
    s = line.strip()
    m = re.match(r"^(?:\S+\s+)?(\d+):(\d+)\s*$", s)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


# ---------------------------------------------------------------------------
# Chapter / book name extraction from path
# ---------------------------------------------------------------------------

CHAPTER_FILENAME_RE = re.compile(r"-(\d+)\.txt$", re.IGNORECASE)


def book_name_from_path(path: Path) -> str:
    """Return the book directory name (e.g. '01-genesis')."""
    return path.parent.name


def chapter_from_path(path: Path) -> int | None:
    m = CHAPTER_FILENAME_RE.search(path.name)
    if not m:
        return None
    return int(m.group(1))


# ---------------------------------------------------------------------------
# Verse partitioning
# ---------------------------------------------------------------------------

def partition_into_verses(lines: list[str]) -> list[tuple[int | None, int | None, list[int]]]:
    """Group line indices by verse.

    Returns a list of (chapter, verse, [line_indices]) tuples in source order.
    """
    verses: list[tuple[int | None, int | None, list[int]]] = []
    cur_chapter: int | None = None
    cur_verse: int | None = None
    cur_indices: list[int] = []
    for i, line in enumerate(lines):
        ref = parse_verse_ref(line)
        if ref is not None:
            if cur_indices:
                verses.append((cur_chapter, cur_verse, cur_indices))
            cur_chapter, cur_verse = ref
            cur_indices = []
            continue
        if not line.strip():
            continue
        cur_indices.append(i)
    if cur_indices:
        verses.append((cur_chapter, cur_verse, cur_indices))
    return verses


# ---------------------------------------------------------------------------
# Divine-name vocabulary (for both paths)
# ---------------------------------------------------------------------------

# Lemmas / surface consonant skeletons that flag a divine-name compound.
# Used in the IR path (lemma check) and heuristic path (surface skel check).

# Canonical divine-name lemmas as they appear in Macula lowfat
_DIVINE_NAME_LEMMAS = frozenset({
    "יְהוָה", "יהוה",   # Tetragrammaton (various niqqud forms)
    "אֲדֹנָי", "אדני",   # Adonai
    "אֱלֹהִים", "אלהים",  # Elohim
    "צְבָאוֹת", "צבאות",  # Tsvaot
    "שַׁדַּי", "שדי",    # Shaddai
    "עֶלְיוֹן", "עליון",  # Elyon
    "יָהּ", "יה",        # Yah
    "אֵל", "אל",         # El (construct form)
})

# Consonant skeletons for heuristic-path divine-name surface matching
_DIVINE_NAME_SKELS = frozenset({
    "יהוה",    # YHWH
    "אדני",    # Adonai
    "אלהים",   # Elohim (absolute)
    "אלהי",    # Elohim (construct: אֱלֹהֵי)
    "צבאות",   # Tsvaot
    "שדי",     # Shaddai
    "עליון",   # Elyon
    "יה",      # Yah
})

# Known divine-name followers (the *rectum* in "YHWH + X" compounds).
# These are the tokens that typically follow a divine name to form a frozen formula.
_DIVINE_NAME_FOLLOWERS_SKELS = frozenset({
    "צבאות",   # יְהוָה צְבָאוֹת
    "אלהים",   # יְהוָה אֱלֹהִים / אֲדֹנָי אֱלֹהִים
    "אלהי",    # יְהוָה אֱלֹהֵי ...
    "אדני",    # after preceding divine ref
    "יהוה",    # compound ref
    "עליון",   # אֵל עֶלְיוֹן
    "שדי",     # אֵל שַׁדַּי
    "אבות",    # אֱלֹהֵי אֲבוֹת
    "אבותינו", # אֱלֹהֵי אֲבֹתֵינוּ
    "ישראל",   # יְהוָה אֱלֹהֵי יִשְׂרָאֵל / אֱלֹהֵי יִשְׂרָאֵל
})


# ---------------------------------------------------------------------------
# Heuristic-path helpers (fallback when IR is empty)
# ---------------------------------------------------------------------------

# Common construct-state regens endings / forms (closed list)
_COMMON_CONSTRUCT_SKELS = frozenset({
    "בית",    # בֵּית  house of
    "בני",    # בְּנֵי  sons of
    "בן",     # בֶּן   son of
    "בת",     # בַּת   daughter of
    "עבד",    # עֶבֶד  servant of
    "ארץ",    # אֶרֶץ  land of (some forms)
    "יד",     # יַד   hand of
    "ראש",    # רֹאשׁ  head of
    "לב",     # לֵב   heart of
    "עם",     # עַם   people of
    "כל",     # כֹּל   all of
    "פני",    # פְּנֵי  face of
    "קול",    # קוֹל  voice of
    "ספר",    # סֵפֶר  book of
    "דבר",    # דְּבַר  word of
    "שם",     # שֵׁם   name of
    "יום",    # יֹום   day of
    "עד",     # עַד   witness / until (construct)
    "כף",     # כַּף   palm of
    "חצי",    # חֲצִי  half of
})

# Conjunctions / clause-starters that suppress common_construct_ending findings
_CLAUSE_STARTER_PREFIXES = ("וַ", "כִּ", "אֲשֶׁ", "כַּ", "וְ", "כְּ")

# Verb-type suffixes (consonant skeleton endings) that identify finite verbs.
# article_rectum must not fire when the line-final word is a verb (speech verb,
# wayyiqtol, etc.) — the ה on the next line is not an article on a rectum.
# We check consonant skeleton for common finite-verb endings.
_VERB_SKEL_SUFFIXES = (
    "ר",    # wayyiqtol 3ms ending (e.g., וַיֹּאמֶר → ויאמר)
    "ה",    # 3fs suffix forms — but ה is also article, so handled by broader check
)

# Wayyiqtol prefix check: if last word's skel starts with ו and ends with common
# verb consonant patterns, it's likely a finite verb. Use a more robust approach:
# check if the last word's skel is NOT in any construct-chain indicator set and
# does NOT match the closed-list common-construct forms.
def _last_word_is_likely_verb(line: str) -> bool:
    """Heuristic: return True if the last word on the line is likely a finite verb.

    Checks:
      - Consonant skeleton starts with וי or וא (wayyiqtol prefix pattern)
      - Skeleton starts with וי (common wayyiqtol)
      - Word ends with common verb endings (ר for 3ms, ו for 3mp, etc.)
        AND is not in the common-construct closed list.
    """
    words = line.split()
    if not words:
        return False
    skel = _strip_points(words[-1]).replace(SOF_PASUQ, "")
    # Wayyiqtol: starts with וי (waw-yod) — most common narrative verb form
    if skel.startswith("וי") or skel.startswith("וא"):
        return True
    # Also: starts with ו and ends with ר (wayyiqtol 3ms like ויאמר, וילך, וישב)
    if skel.startswith("ו") and skel.endswith("ר") and skel not in _COMMON_CONSTRUCT_SKELS:
        return True
    return False


def _strip_points(text: str) -> str:
    """Strip niqqud and te'amim, return consonant skeleton."""
    return HEBREW_POINTS_RE.sub("", text).strip()


def _first_word_skel(line: str) -> str:
    """Consonant skeleton of the first whitespace-separated word in a line."""
    words = line.split()
    if not words:
        return ""
    return _strip_points(words[0])


def _last_word_skel(line: str) -> str:
    """Consonant skeleton of the last whitespace-separated word in a line,
    stripping sof pasuq if present."""
    words = line.split()
    if not words:
        return ""
    w = _strip_points(words[-1])
    return w.replace(SOF_PASUQ, "").strip()


def _line_ends_with_sof_pasuq(line: str) -> bool:
    """True if any word on the line contains sof pasuq (verse-end marker)."""
    return SOF_PASUQ in line


def _is_articulated(word_surface: str) -> bool:
    """Return True if the surface word begins with he-article (ה + dagesh/vowel + consonant)."""
    skel = _strip_points(word_surface)
    # A definite article starts with ה followed by more consonants (no maqqef before it)
    return bool(skel) and skel.startswith("ה") and len(skel) > 1


def _next_line_first_word(line: str) -> str:
    """Return the first word of a line (surface form)."""
    words = line.split()
    return words[0] if words else ""


def _classify_heuristic(line: str, next_line: str) -> tuple[str, str] | None:
    """Apply the pre-IR heuristic classifiers.

    Returns (subcase, severity) or None if no heuristic fires.

    Checks in order:
      1. divine_name  — line-final word is a divine name AND next-line first
                        word is a divine-name follower.
      2. article_rectum — line-final word is NOT articulated AND next-line
                          first word IS articulated (article on a noun).
      3. common_construct_ending — line-final consonant skeleton is in the
                                   common-construct closed list, AND next-line
                                   does not start with a clause-starter.

    Pre-condition: caller has already verified sof-pasuq suppression.
    """
    last_skel = _last_word_skel(line)
    first_word = _next_line_first_word(next_line)
    first_skel = _strip_points(first_word).replace(SOF_PASUQ, "")

    # 1. divine_name
    if last_skel in _DIVINE_NAME_SKELS and first_skel in _DIVINE_NAME_FOLLOWERS_SKELS:
        return ("divine_name", "STRONG-MERGE-CANDIDATE")

    # Also check: line-final word is NOT a divine name but NEXT line starts
    # with a divine name (e.g., בֵּית יְהוָה split: בֵּית at end, יְהוָה on next)
    # — treat as divine_name if the last_skel is in common construct forms
    # and first_skel is a divine name:
    if first_skel in _DIVINE_NAME_SKELS and last_skel in _COMMON_CONSTRUCT_SKELS:
        return ("divine_name", "STRONG-MERGE-CANDIDATE")

    # 2. article_rectum — last word lacks article, next line's first word has it.
    # Suppress if the line-final word is a likely finite verb (e.g., wayyiqtol
    # speech verb like וַיֹּאמֶר) — the ה on next line is not a construct rectum.
    if not _is_articulated(line.split()[-1] if line.split() else ""):
        if _is_articulated(first_word) and not _last_word_is_likely_verb(line):
            return ("article_rectum", "REVIEW-REQUIRED")

    # 3. common_construct_ending
    if last_skel in _COMMON_CONSTRUCT_SKELS:
        # Suppress if next line starts with a clause-starter conjunction
        if not any(next_line.strip().startswith(p) for p in _CLAUSE_STARTER_PREFIXES):
            return ("common_construct_ending", "REVIEW-REQUIRED")

    return None


# ---------------------------------------------------------------------------
# IR helpers
# ---------------------------------------------------------------------------

def collect_npofnp_constituents(constituents: list["MC.Constituent"]) -> list["MC.Constituent"]:
    """Recursively gather all Constituent nodes where is_construct_chain == True."""
    out: list["MC.Constituent"] = []

    def walk(node: "MC.Constituent | MC.Token") -> None:
        if isinstance(node, MC.Token):
            return
        if node.is_construct_chain:
            out.append(node)
        for c in node.children:
            walk(c)

    for r in constituents:
        walk(r)
    return out


def token_ends_with_sof_pasuq(tok: "MC.Token") -> bool:
    """Return True if this token's surface form contains the sof pasuq mark."""
    return SOF_PASUQ in tok.text


def _has_embedded_relative_clause(npofnp: "MC.Constituent") -> bool:
    """Return True if the NPofNP constituent contains a relative clause child."""
    for child in npofnp.children:
        if isinstance(child, MC.Constituent) and child.is_relative_clause:
            return True
    return False


def _classify_ir_npofnp(npofnp: "MC.Constituent") -> tuple[str, str]:
    """Classify an IR NPofNP finding into (subcase, severity).

    divine_name: any token in the chain has a divine-name lemma → STRONG
    npofnp_split short: ≤4 tokens, no embedded relcl → STRONG
    npofnp_split complex: else → REVIEW-REQUIRED
    """
    chain_tokens = npofnp.tokens

    # Check divine-name involvement
    for tok in chain_tokens:
        lemma = (tok.lemma or "").strip()
        skel = _strip_points(lemma) if lemma else _strip_points(tok.text)
        if skel in _DIVINE_NAME_SKELS or lemma in _DIVINE_NAME_LEMMAS:
            return ("divine_name", "STRONG-MERGE-CANDIDATE")

    # Short, simple chain → STRONG
    if len(chain_tokens) <= 4 and not _has_embedded_relative_clause(npofnp):
        return ("npofnp_split", "STRONG-MERGE-CANDIDATE")

    # Long or complex → REVIEW
    return ("npofnp_split", "REVIEW-REQUIRED")


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path, verbose: bool = False) -> list[dict]:
    """IR-driven scan for Rule H2, with heuristic fallback for missing-XML verses.

    Per verse:
      1. Pull lowfat verse tokens + top-level constituents.
      2. If IR returns data: greedy-align sense-lines to tokens; collect NPofNP
         constituents; classify and emit findings.
      3. If IR returns empty (missing lowfat XML — e.g., synthetic fixture text):
         run the heuristic fallback across consecutive sense-line pairs.
    """
    violations: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    book_slug = book_name_from_path(path)
    verses = partition_into_verses(lines)

    for ch, vs, indices in verses:
        if ch is None or vs is None:
            continue
        # Sense-lines in this verse, in source order, dropping skippables
        sense_indices = [i for i in indices if not is_skippable(lines[i])]
        if len(sense_indices) < 2:
            continue

        # Try IR path first
        ir_used = False
        try:
            verse_tokens = MC.get_verse_tokens(book_slug, ch, vs)
            verse_constituents = MC.get_verse_constituents(book_slug, ch, vs)
            if verse_tokens and verse_constituents:
                ir_used = True
        except (FileNotFoundError, ValueError, KeyError):
            verse_tokens = []
            verse_constituents = []

        if ir_used:
            # --- IR path ---
            token_to_line: dict[str, int] = {}
            cursor = 0
            for line_idx, src_idx in enumerate(sense_indices):
                matched, cursor = MC.match_sense_line_tokens(
                    verse_tokens, lines[src_idx], start_idx=cursor
                )
                for tok in matched:
                    token_to_line[tok.xml_id] = line_idx

            npofnp_list = collect_npofnp_constituents(verse_constituents)
            if not npofnp_list:
                continue

            for npofnp in npofnp_list:
                chain_tokens = npofnp.tokens
                if len(chain_tokens) < 2:
                    continue

                first_tok = chain_tokens[0]
                last_tok = chain_tokens[-1]

                if token_ends_with_sof_pasuq(last_tok):
                    continue

                first_line_idx = token_to_line.get(first_tok.xml_id)
                last_line_idx = token_to_line.get(last_tok.xml_id)
                if first_line_idx is None or last_line_idx is None:
                    continue
                if first_line_idx == last_line_idx:
                    continue

                subcase, severity = _classify_ir_npofnp(npofnp)

                first_src_idx = sense_indices[first_line_idx]
                last_src_idx = sense_indices[last_line_idx]
                line_n = lines[first_src_idx]
                line_next = lines[last_src_idx]

                chain_text = " ".join(t.text for t in chain_tokens)
                violations.append({
                    "file": path.name,
                    "file_path": path,
                    "line_num": first_src_idx + 1,
                    "rule": "H2/construct",
                    "severity": severity,
                    "subcase": subcase,
                    "brief": (
                        f"NPofNP construct chain split across sense-lines — "
                        f"{first_tok.text!r}…{last_tok.text!r} (chain: {chain_text})"
                    ),
                    "line": line_n.rstrip(),
                    "next_line": line_next.rstrip(),
                    "next_line_num": last_src_idx + 1,
                    "book": book_slug,
                    "chapter": ch,
                    "verse": vs,
                })

        else:
            # --- Heuristic fallback (no Macula XML for this verse) ---
            for i in range(len(sense_indices) - 1):
                src_idx = sense_indices[i]
                next_src_idx = sense_indices[i + 1]
                line_n = lines[src_idx]
                line_next = lines[next_src_idx]

                # Sof-pasuq suppression: verse-end line cannot have a construct split
                if _line_ends_with_sof_pasuq(line_n):
                    continue

                result = _classify_heuristic(line_n, line_next)
                if result is None:
                    continue

                subcase, severity = result
                last_skel = _last_word_skel(line_n)
                first_skel = _first_word_skel(line_next)
                violations.append({
                    "file": path.name,
                    "file_path": path,
                    "line_num": src_idx + 1,
                    "rule": "H2/construct",
                    "severity": severity,
                    "subcase": subcase,
                    "brief": (
                        f"Construct chain split across sense-lines — "
                        f"{last_skel!r}…{first_skel!r} [{subcase}]"
                    ),
                    "line": line_n.rstrip(),
                    "next_line": line_next.rstrip(),
                    "next_line_num": next_src_idx + 1,
                    "book": book_slug,
                    "chapter": ch,
                    "verse": vs,
                })

    return violations


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--book",
        metavar="BOOK",
        help="Restrict scan to one book folder name (e.g. 'jonah'). "
             "Default: all books in the target directory.",
    )
    parser.add_argument(
        "--v2",
        action="store_true",
        help="Scan v2/heb (editorial gold standard) instead of v1/he-baseline.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show next-line context for each violation.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as a single JSON document to STDOUT instead of human-readable lines.",
    )
    args = parser.parse_args()

    base_dir = V2_DIR if args.v2 else V1_DIR
    tier_label = "v2/heb" if args.v2 else "v1/he-baseline"

    if not base_dir.exists():
        print(
            f"ERROR: {base_dir} not found. "
            f"Run the ingest/baseline 5-machinery/scripts first.",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.book:
        book_dir = base_dir / args.book
        if not book_dir.exists():
            print(f"ERROR: book directory not found: {book_dir}", file=sys.stderr)
            sys.exit(2)
        files = sorted(book_dir.glob("*.txt"))
    else:
        files = sorted(base_dir.rglob("*.txt"))

    if not files:
        print(f"No .txt files found under {base_dir}", file=sys.stderr)
        sys.exit(2)

    all_violations: list[dict] = []
    for path in files:
        all_violations.extend(scan_file(path, verbose=args.verbose))

    exit_code = 1 if all_violations else 0

    # --- JSON output mode ---
    if args.json:
        findings = []
        for v in all_violations:
            severity = v["severity"]
            applied_action = "merge_with_next" if severity == "STRONG-MERGE-CANDIDATE" else None
            findings.append({
                "file": str(v["file_path"].relative_to(REPO_ROOT)).replace("\\", "/"),
                "line": v["line_num"],
                "severity": "DEVIATION",
                "tag": severity,
                "subcase": v["subcase"],
                "rule_id": "H2.1",
                "rule_short": "construct chain split across lines",
                "brief": v["brief"],
                "next_line": v.get("next_line_num"),
                "applied_action": applied_action,
            })

        by_severity_json: dict[str, int] = {}
        by_tag: dict[str, int] = {}
        by_subcase: dict[str, int] = {}
        for f in findings:
            by_severity_json[f["severity"]] = by_severity_json.get(f["severity"], 0) + 1
            by_tag[f["tag"]] = by_tag.get(f["tag"], 0) + 1
            by_subcase[f["subcase"]] = by_subcase.get(f["subcase"], 0) + 1

        doc = {
            "validator": "validate_construct_chain",
            "rule": "Rule H2 — Construct Chain Default",
            "layer": 3,
            "book": args.book or "all",
            "files_scanned": [
                str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files
            ],
            "findings": findings,
            "summary": {
                "total_findings": len(findings),
                "by_severity": by_severity_json,
                "by_tag": by_tag,
                "by_subcase": by_subcase,
                "exit_code": exit_code,
            },
        }
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    # --- Human-readable output (default) ---
    print("=" * 72)
    print(f"Rule H2 Construct Chain validator (IR-driven) — Tanakh {tier_label}")
    print(f"Reference: 1-method/canon §5 H2; Joüon-Muraoka §129; Waltke-O'Connor §9")
    print("=" * 72)
    print(f"Files scanned : {len(files)}")
    print(f"Violations    : {len(all_violations)}")

    by_severity: dict[str, int] = {}
    for v in all_violations:
        by_severity[v["severity"]] = by_severity.get(v["severity"], 0) + 1
    if by_severity:
        print()
        for sev, count in sorted(by_severity.items()):
            print(f"  {sev}: {count}")
    print()

    if all_violations:
        for v in all_violations:
            print(
                f"[DEVIATION]  {v['file']}:{v['line_num']}  "
                f"{v['rule']}  {v['severity']}  {v['brief']}"
            )
            print(f"    {v['line'][:120]}")
            if args.verbose and v.get("next_line"):
                print(f"    → {v['next_line'][:120]}")
            print()
    else:
        print("No violations found. Rule H2 construct-chain integrity is clean.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
