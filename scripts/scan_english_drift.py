#!/usr/bin/env python3
"""
scan_english_drift.py — Find probable English-alignment drift sites.

The English text in data/text-files/v2/eng-kjv/ is supposed to have
a 1:1 line correspondence with the Hebrew v2/heb/ files. Mechanical splits
can introduce English phrases broken mid-sentence:

  "and said to them what? is occupation"   <-- line ends with dangling "is"
  "your"                                   <-- line starts with continuation

This scanner uses string-level heuristics to find probable drift sites.
It does NOT verify semantic correctness — that's a separate (agent-
driven) audit. This scanner is fast, deterministic, and catches the
mechanical-split class of bugs.

Heuristics (each flag has a tag):

  1. ARTICLE-SPLIT: line ends with an article (the, a, an).

  2. PREP-NP-SPLIT: line ends with a preposition AND the next line begins
     with an article, possessive, or demonstrative.

  3. AUX-VERB-SPLIT: line ends with an auxiliary verb AND the next line
     begins with a verb-form or negation.

  4. PTC-NP-SPLIT: line ends with a participle (-ing / -ed form) AND the
     next line begins with a noun-phrase starter.

  5. APPOSITIVE-SPLIT: line ends with a capitalized proper noun AND the
     next line begins with a possessive (his/her/their/its/my/our/your).

  6. DANGLING-CONJ: line ends with a coordinating conjunction (low
     confidence; likely legitimate in Hebrew poetry).

Hebrew cross-check: if the Hebrew line N+1 begins with a recognized
Hebrew subordinator or relative-introducer (after stripping any leading
conjunction prefix waw/vav), the English break is legitimate — suppress
the drift flag.

PTC-NP-SPLIT false-positive suppressors (Genesis audit 2026-04-27):
-----------------------------------------------------------------------
Biblical Hebrew's default word order is Verb-Subject-Object (VSO).  The
accent-hierarchy parser (parse_teamim.py) respects this: verb cola and
subject NP cola are frequently split onto separate lines.  When the
English gloss renders a bare past-tense verb on line N and the subject
NP on line N+1, the -ed ending on line N triggers PTC-NP-SPLIT even
though the break is legitimate.  Three suppressors catch this:

  S1 - NOUN-GLOSS-ING: English noun glosses whose surface form ends in
       -ing but are not verbs (e.g. "morning" = בֹּקֶר, "offering" =
       עֹלָה).  These words appear in _NOUN_GLOSSES_ING.

  S2 - VSO-BARE-NP: The next colon is a bare NP (≤5 tokens, no
       auxiliary or copula verb among them).  A bare-NP colon is the
       canonical subject-postposition colon in VSO narrative; a genuine
       English drift site would have a continuation phrase containing
       verbal or prepositional material that belongs with line N.

  S3 - EXISTING: temporal line-opener on line N (_ENGLISH_TEMPORAL_STARTS)
       or intransitive terminal verb on line N (_INTRANSITIVE_TEMPORALS).

After applying S1–S3 the Genesis PTC-NP-SPLIT count dropped from 34 to
approximately 3–5 (cases where the next NP is longer and contains
prepositional structure that could represent genuine drift).

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/scan_english_drift.py
    PYTHONIOENCODING=utf-8 py -3 scripts/scan_english_drift.py --book jonah
    PYTHONIOENCODING=utf-8 py -3 scripts/scan_english_drift.py --all-books
    PYTHONIOENCODING=utf-8 py -3 scripts/scan_english_drift.py --summary-only
    PYTHONIOENCODING=utf-8 py -3 scripts/scan_english_drift.py --min-confidence low
"""
import os
import re
import argparse
import unicodedata as _ud
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
ENG_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v2", "eng-kjv")
HE_DIR  = os.path.join(REPO_ROOT, "data", "text-files", "v2", "heb")

# ---------------------------------------------------------------------------
# Hebrew subordinator / relative-introducer set.
# If Hebrew line N+1 begins with one of these (after stripping a leading
# waw conjunction prefix), the English break at line N is legitimate.
# ---------------------------------------------------------------------------
_HEB_SUBORDINATORS = {
    "אֲשֶׁר",   # relative / subordinate conjunction
    "כִּי",      # causal / temporal / subordinate
    "אִם",       # conditional
    "לְמַעַן",   # purpose "in order that"
    "בַּעֲבוּר", # purpose / cause "on account of"
    "הִנֵּה",    # presentative / attention-getter
    "יַעַן",     # because / since
    "כַּאֲשֶׁר", # just as / when
    # sheba-prefix: handled by prefix stripping below
}

# Waw-prefix forms of the above that sometimes appear fused
# We detect sheba-prefix "שֶׁ-" by checking if the Hebrew token starts
# with שֶׁ (Unicode: שׁ + shewa) — done via simple startswith after
# stripping diacritics.
_SHEBA_BASE = "ש"   # shin without points


def _strip_hebrew_niqqud(w):
    """Remove niqqud (vowel points) and te'amim so consonant comparison
    works regardless of pointing variant."""
    decomposed = _ud.normalize("NFD", w)
    # Keep base letters; drop combining characters in the Hebrew ranges:
    #   U+0591–U+05C7 (Hebrew points and cantillation)
    #   U+FB1D–U+FB4E (presentation forms that carry diacritics)
    stripped = "".join(
        c for c in decomposed
        if not (0x0591 <= ord(c) <= 0x05C7)
    )
    return _ud.normalize("NFC", stripped)


# Waw conjunction prefix in Unicode NFC: וְ / וַ / וָ / וּ / וֹ / וִ etc.
# Consonantally it is always וׄ — just waw (ו).
_WAW = "ו"

# Pre-strip niqqud from subordinator set for accent-insensitive comparison
_HEB_SUBORD_CONSONANTAL = {_strip_hebrew_niqqud(w) for w in _HEB_SUBORDINATORS}


def _heb_first_significant(line):
    """Return the consonantal form of the first significant Hebrew word on
    a line, skipping a leading waw-conjunction prefix if present."""
    words = line.strip().split()
    if not words:
        return ""
    # Take the first token, strip niqqud/te'amim
    first = _strip_hebrew_niqqud(words[0])
    # Strip leading waw-prefix (common in wayyiqtol narrative chains)
    if first.startswith(_WAW) and len(first) > 1:
        first = first[1:]
    return first


def _heb_line_starts_subordinate(line):
    """True if the Hebrew line begins with a subordinator or relative
    introducer (after any leading waw-prefix). Also catches sheba-prefix."""
    first = _heb_first_significant(line)
    if not first:
        return False
    # Exact consonantal match against known subordinators
    if first in _HEB_SUBORD_CONSONANTAL:
        return True
    # sheba-prefix: consonantally שׁ (shin) + next consonant, but since
    # we're working post-niqqud-strip we look for lines whose first real
    # consonant cluster begins with ש and is short (2-4 chars) — but
    # that's too broad.  Instead, look for the pointed form שֶׁ surviving
    # the strip as "ש" alone (sheba attached to next word in the token).
    # The safest check: original words[0] starts with שֶׁ
    raw_first = line.strip().split()[0] if line.strip() else ""
    if raw_first.startswith("שֶׁ") or raw_first.startswith("שׁ"):
        return True
    return False


# ---------------------------------------------------------------------------
# English heuristic sets (ported from GNT scanner, unchanged)
# ---------------------------------------------------------------------------

ARTICLES = {"the", "a", "an"}

PREPS = {
    "of", "in", "to", "for", "from", "by", "with", "at", "on",
    "into", "over", "under", "upon", "through", "against", "before",
    "after", "among", "beside", "between", "without", "within",
    "across", "toward", "towards", "beyond", "around", "about",
    "above", "below", "behind",
}

NEXT_NP_STARTERS = {
    "the", "a", "an",
    "my", "your", "his", "her", "its", "our", "their",
    "this", "that", "these", "those",
}

AUXES = {
    "has", "have", "had", "having",
    "is", "are", "was", "were", "am", "be", "been", "being",
    "will", "can", "may", "might", "should", "would", "must",
    "shall",
}

_VERBY_SUFFIX_RE = re.compile(r'(ed|en|ing|own|ought|orn|aid|old|one)$')

COORD_CONJS = {"and", "or", "but", "nor"}

_END_PUNCT = re.compile(r'[,.\;:!?·—–\-\'\"]+$')

_POSSESSIVES = {"my", "your", "his", "her", "its", "our", "their"}

# English temporal/causal line-openers that suppress PTC-NP-SPLIT
_ENGLISH_TEMPORAL_STARTS = {
    "while", "when", "as", "after", "before", "since", "until",
    "once", "now", "then", "meanwhile", "where", "whenever",
}

# Intransitive temporals whose -ing/-ed form at line-end is not a split
_INTRANSITIVE_TEMPORALS = {
    "returned", "arrived", "came", "went",
    "departed", "approached", "entered", "rose",
    "stood", "sat", "slept", "sleeping", "praying",
    "sowing", "sowed", "finished", "coming",
    "happened", "occurred",
    # Speech-intro terminal: "saying" (לֵאמֹר lemor) ends the speech-intro
    # frame colon; the next colon is the reported speech content.  This is
    # a structural break, never drift.
    "saying",
}

# S1 — Suppressor: English noun glosses that surface with -ing or -ed
# endings but are nouns, not participial verbs.  These words should never
# trigger PTC-NP-SPLIT regardless of what follows on the next line.
# Hebrew sources are noted for cross-reference clarity.
_NOUN_GLOSSES_ING = {
    # -ing nouns (noun glosses that coincidentally end in -ing)
    "morning",      # בֹּקֶר boqer
    "evening",      # עֶרֶב 'erev
    "offering",     # עֹלָה / קָרְבָּן
    "offering",     # עֹלָה / מִנְחָה
    "blessing",     # בְּרָכָה
    "dwelling",     # מָשְׁכָּן / מִשְׁכָּן
    "beginning",    # רֵאשִׁית
    "gathering",    # אַסְפָה / קָהָל (noun, not verb form)
    "covering",     # כִּסּוּי (noun)
    "anointing",    # מִשְׁחָה
    "warning",      # אַזְהָרָה
    "wedding",      # חַתֻּנָּה
    "spring",       # אָבִיב (season noun that sometimes glosses as "spring")
    "offspring",    # זֶרַע / צֶאֱצָא — ends in -ing but is a noun
    "hunting",      # צַיִד — "he knew hunting" is a noun complement
    "herding",      # רֹעֶה form sometimes glossed as noun
}

# S2 — Suppressor: VSO bare-NP next colon.
# In Biblical Hebrew VSO order the subject NP often occupies its own colon
# immediately following the verb colon.  A next colon that is a bare NP
# (short, no auxiliary or main verbal token) is the canonical VSO subject-
# postposition pattern, not English drift.
#
# Heuristic: if the next colon has ≤ _VSO_MAX_TOKENS tokens AND none of
# those tokens is an auxiliary/copula verb or subordinating conjunction,
# treat the boundary as a legitimate VSO split and suppress PTC-NP-SPLIT.
_VSO_MAX_TOKENS = 6

# Tokens that, if present in the next colon, disqualify the bare-NP test
# (they suggest the next colon has verbal or clausal material that should
# have stayed on the same colon as line N).
_VSO_DISQUALIFIERS = {
    # auxiliaries / copulas
    "is", "are", "was", "were", "am", "be", "been", "being",
    "has", "have", "had",
    "will", "can", "may", "might", "should", "would", "must", "shall",
    # subordinating conjunctions that introduce clauses, not NPs
    "that", "which", "who", "whom", "whose",
    "because", "since", "although", "though", "if", "when", "while",
    "where", "until", "unless",
}


def _next_colon_is_bare_np(next_line):
    """Return True if next_line looks like a bare subject-NP colon (VSO).

    Conditions:
      - The line (stripped of punctuation) has at most _VSO_MAX_TOKENS words.
      - None of those words is in _VSO_DISQUALIFIERS.
      - At least one word remains after stripping (non-empty).
    """
    cleaned = _END_PUNCT.sub("", next_line).strip()
    if not cleaned:
        return False
    tokens = [t.lower() for t in cleaned.split()]
    if not tokens:
        return False
    if len(tokens) > _VSO_MAX_TOKENS:
        return False
    if any(t in _VSO_DISQUALIFIERS for t in tokens):
        return False
    return True


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

VERSE_REF_RE = re.compile(r"^(\d+):(\d+)")


def _last_word(line):
    line = line.strip()
    line = _END_PUNCT.sub("", line).strip()
    if not line:
        return ("", "")
    parts = line.split()
    if not parts:
        return ("", "")
    raw = parts[-1]
    return (raw.lower(), raw)


def _first_word(line):
    line = line.strip()
    if not line:
        return ("", "")
    parts = line.split()
    if not parts:
        return ("", "")
    w = parts[0]
    w = re.sub(r'^[\"\'\(\[—–\-]+', "", w)
    return (w.lower(), w)


# ---------------------------------------------------------------------------
# File parsing
# ---------------------------------------------------------------------------

def _parse_chapter(filepath):
    """Return list of verses, each {ref, chapter, verse, lines}."""
    verses = []
    current = None
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n").rstrip("\r")
            stripped = line.strip()
            if not stripped:
                continue
            m = VERSE_REF_RE.match(stripped)
            if m and stripped == m.group(0):
                if current:
                    verses.append(current)
                current = {
                    "ref": stripped,
                    "chapter": int(m.group(1)),
                    "verse": int(m.group(2)),
                    "lines": [],
                }
                continue
            if current is None:
                continue
            current["lines"].append(line)
    if current:
        verses.append(current)
    return verses


def _load_hebrew_chapter(eng_file_rel):
    """Given an eng-kjv relative path ('05-jonah/jonah-01.txt'), load the
    corresponding Hebrew chapter from v2/heb/. Returns dict: verse_ref -> list."""
    he_path = os.path.join(HE_DIR, *eng_file_rel.split("/"))
    if not os.path.exists(he_path):
        return {}
    result = {}
    current = None
    with open(he_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n").rstrip("\r")
            stripped = line.strip()
            if not stripped:
                continue
            m = VERSE_REF_RE.match(stripped)
            if m and stripped == m.group(0):
                current = stripped
                result[current] = []
                continue
            if current is None:
                continue
            result[current].append(line)
    return result


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def _classify_drift(last, last_raw, next_first, next_first_raw):
    """Return (flag, confidence) or None if not drift.

    `last` / `next_first` are lowercased and punctuation-stripped.
    `last_raw` / `next_first_raw` retain original casing for proper-noun
    detection.
    """
    if not last or not next_first:
        return None

    # Article at line end — always broken
    if last in ARTICLES:
        return ("ARTICLE-SPLIT", "high")

    # Preposition + article/possessive/demonstrative on next line
    if last in PREPS and next_first in NEXT_NP_STARTERS:
        return ("PREP-NP-SPLIT", "high")

    # Auxiliary + verb-form or negation on next line
    if last in AUXES:
        if _VERBY_SUFFIX_RE.search(next_first) or next_first in {"not", "no", "never"}:
            return ("AUX-VERB-SPLIT", "high")

    # Participle (-ing / -ed form) at line end + NP-starter on next line
    _PTC_NP_STARTERS = NEXT_NP_STARTERS - {"that"}
    if (last.endswith("ing") or last.endswith("ed")) and next_first in _PTC_NP_STARTERS:
        if len(last) > 4 and last not in {"being", "having", "doing"}:
            return ("PTC-NP-SPLIT", "high")
        if last in {"being", "having", "doing"}:
            return ("PTC-NP-SPLIT", "high")

    # Proper noun at line end + possessive on next line — appositive split
    if (last_raw and last_raw[0].isupper() and last_raw.lower() == last
            and next_first in _POSSESSIVES):
        return ("APPOSITIVE-SPLIT", "high")

    # Coordinating conjunction dangling — low confidence
    if last in COORD_CONJS:
        return ("DANGLING-CONJ", "low")

    return None


# ---------------------------------------------------------------------------
# Main scanner
# ---------------------------------------------------------------------------

def scan_all(book_filter=None, min_confidence="high"):
    results = []
    conf_rank = {"low": 0, "med": 1, "high": 2}
    threshold = conf_rank.get(min_confidence, 2)

    if not os.path.isdir(ENG_DIR):
        print(f"[ERROR] English gloss directory not found: {ENG_DIR}")
        return results

    for book_entry in sorted(os.listdir(ENG_DIR)):
        book_path = os.path.join(ENG_DIR, book_entry)
        if not os.path.isdir(book_path):
            continue
        # Derive slug: '05-jonah' -> 'jonah'
        parts = book_entry.split("-", 1)
        book_slug = parts[1] if len(parts) == 2 and parts[0].isdigit() else book_entry

        if book_filter and book_slug.lower() != book_filter.lower():
            continue

        for fname in sorted(os.listdir(book_path)):
            if not fname.endswith(".txt"):
                continue
            filepath = os.path.join(book_path, fname)
            verses = _parse_chapter(filepath)
            file_rel = f"{book_entry}/{fname}"
            heb_chapter = _load_hebrew_chapter(file_rel)

            for v in verses:
                n = len(v["lines"])
                if n < 2:
                    continue
                heb_lines = heb_chapter.get(v["ref"], [])
                for i in range(n - 1):
                    line = v["lines"][i]
                    # Skip lines that end with clear sentence-terminal punctuation
                    if line.rstrip().endswith((",", ".", ";", ":", "!", "?", "—", "–", "·")):
                        continue
                    last, last_raw = _last_word(line)
                    next_first, next_first_raw = _first_word(v["lines"][i + 1])
                    classification = _classify_drift(last, last_raw, next_first, next_first_raw)
                    if classification is None:
                        continue
                    flag, confidence = classification
                    if conf_rank[confidence] < threshold:
                        continue

                    # Hebrew cross-check: if Hebrew line N+1 starts with a
                    # subordinator or relative introducer, the English break
                    # mirrors a legitimate Hebrew subordinate-clause boundary.
                    if i + 1 < len(heb_lines):
                        if _heb_line_starts_subordinate(heb_lines[i + 1]):
                            continue

                    # PTC-NP-SPLIT suppressors
                    if flag == "PTC-NP-SPLIT":
                        # S3 (pre-existing): temporal frame opener on this line
                        line_first, _ = _first_word(line)
                        if line_first in _ENGLISH_TEMPORAL_STARTS:
                            continue
                        # S3 (pre-existing): known intransitive terminal verb
                        if last in _INTRANSITIVE_TEMPORALS:
                            continue
                        # S1: noun gloss that ends in -ing/-ed but is a noun
                        if last in _NOUN_GLOSSES_ING:
                            continue
                        # S2: VSO bare-NP next colon (subject-postposing)
                        if _next_colon_is_bare_np(v["lines"][i + 1]):
                            continue

                    results.append({
                        "file": file_rel,
                        "ref": v["ref"],
                        "line_idx": i,
                        "total_lines": n,
                        "line_text": line,
                        "next_line": v["lines"][i + 1],
                        "flag": flag,
                        "confidence": confidence,
                        "detail": f"ends with '{last}' + next starts with '{next_first}'",
                    })
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Scan English glosses for mechanical drift vs Hebrew cola."
    )
    ap.add_argument("--book", default=None,
                    help="Scan a single book by slug (e.g. 'jonah')")
    ap.add_argument("--all-books", action="store_true",
                    help="Scan all books (default when --book is omitted)")
    ap.add_argument("--summary-only", action="store_true",
                    help="Print totals only; suppress per-finding detail")
    ap.add_argument("--context", action="store_true",
                    help="(reserved) Print full verse context — not yet implemented")
    ap.add_argument("--min-confidence", default="high",
                    choices=["low", "med", "high"],
                    help="Minimum confidence level to report (default: high)")
    args = ap.parse_args()

    book_filter = args.book if args.book else None
    findings = scan_all(book_filter=book_filter, min_confidence=args.min_confidence)

    print("=== ENGLISH DRIFT SCAN ===\n")
    print(f"Total flagged lines: {len(findings)}\n")

    by_book = defaultdict(int)
    by_flag = defaultdict(int)
    for f in findings:
        by_book[f["file"].split("/")[0]] += 1
        by_flag[f["flag"]] += 1

    for book, n in sorted(by_book.items()):
        print(f"  {book}: {n}")
    print()
    print("By category:")
    for flag, n in sorted(by_flag.items()):
        print(f"  {flag}: {n}")
    print()

    if args.summary_only:
        return

    for f in findings[:200]:
        print(f"{f['file']} {f['ref']} (line {f['line_idx']+1}/{f['total_lines']}):")
        print(f"  >>> {f['line_text']}")
        print(f"      {f['next_line']}")
        print(f"  [{f['flag']}: {f['detail']}]")
        print()

    if len(findings) > 200:
        print(f"... ({len(findings) - 200} more)")


if __name__ == "__main__":
    main()
