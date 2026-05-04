"""Macula Hebrew lowfat XML constituent-query layer for Tanakh Reader validators.

Parses lowfat XML on-demand per chapter, builds a typed object graph
(Token / Constituent / Clause / Sentence / Chapter) with parent/child/sibling
navigation, frame-argument resolution, and pre-resolved participantref/subjref
pointers. Caches per-chapter.

The lowfat XML is at research/macula-hebrew/WLC/lowfat/{NN-Abr-CCC-lowfat.xml}.
Each file is one chapter; each <sentence> wraps exactly one verse.

Public API:
    get_chapter(book_slug, chapter)        -> Chapter
    get_verse_sentence(book_slug, ch, vs)  -> Sentence | None
    get_verse_tokens(book_slug, ch, vs)    -> list[Token]
    get_verse_clauses(book_slug, ch, vs)   -> list[Clause]
    match_sense_line_tokens(verse_tokens, line_text) -> list[Token]

Token exposes derived predicates (is_wayyiqtol, is_weqatal, aspect, ...)
computed from lowfat's `type` attribute. Raw `_morph_tag` is available as
an escape hatch for queries lowfat doesn't natively expose; consumers
should prefer the derived predicates.
"""

from __future__ import annotations

import re
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _nfc(s: Optional[str]) -> Optional[str]:
    """NFC-normalize a Hebrew string. Lowfat XML uses dagesh-before-qamatz
    ordering; editorial source files may use qamatz-before-dagesh. NFC
    canonicalizes so consumers can compare strings directly."""
    if s is None:
        return None
    return unicodedata.normalize("NFC", s)

# ---------------------------------------------------------------------------
# Paths and book mapping
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LOWFAT_DIR = _REPO_ROOT / "research" / "macula-hebrew" / "WLC" / "lowfat"

# Project-slug -> (book_num, macula_abbr_in_filename)
# Filename is `{book_num:02d}-{macula_abbr}-{chapter:03d}-lowfat.xml`.
# Note the case inconsistency: most Minor-Prophet abbrs are titlecase
# (e.g. "Mic", "Hab"), but Hosea is uppercase ("HOS"). The mapping below
# uses the exact filename-casing observed in the vendored corpus.
_BOOK_MAP: dict[str, tuple[int, str]] = {
    "01-genesis":         (1,  "Gen"),
    "02-exodus":          (2,  "Exo"),
    "03-leviticus":       (3,  "Lev"),
    "04-numbers":         (4,  "Num"),
    "05-deuteronomy":     (5,  "Deu"),
    "06-joshua":          (6,  "Jos"),
    "07-judges":          (7,  "Jdg"),
    "08-ruth":            (8,  "Rut"),
    "09-1samuel":         (9,  "1Sa"),
    "10-2samuel":        (10,  "2Sa"),
    "11-1kings":         (11,  "1Ki"),
    "12-2kings":         (12,  "2Ki"),
    "13-1chronicles":    (13,  "1Ch"),
    "14-2chronicles":    (14,  "2Ch"),
    "15-ezra":           (15,  "Ezr"),
    "16-nehemiah":       (16,  "Neh"),
    "17-esther":         (17,  "Est"),
    "18-job":            (18,  "Job"),
    "19-psalms":         (19,  "Psa"),
    "20-proverbs":       (20,  "Pro"),
    "21-ecclesiastes":   (21,  "Ecc"),
    "22-songofsongs":    (22,  "Sng"),
    "23-isaiah":         (23,  "Isa"),
    "24-jeremiah":       (24,  "Jer"),
    "25-lamentations":   (25,  "Lam"),
    "26-ezekiel":        (26,  "Ezk"),
    "27-daniel":         (27,  "Dan"),
    "28-hosea":          (28,  "HOS"),
    "29-joel":           (29,  "Jol"),
    "30-amos":           (30,  "Amo"),
    "31-obadiah":        (31,  "Oba"),
    "32-jonah":          (32,  "Jon"),
    "33-micah":          (33,  "Mic"),
    "34-nahum":          (34,  "Nam"),
    "35-habakkuk":       (35,  "Hab"),
    "36-zephaniah":      (36,  "Zep"),
    "37-haggai":         (37,  "Hag"),
    "38-zechariah":      (38,  "Zec"),
    "39-malachi":        (39,  "Mal"),
}


def lowfat_path(book_slug: str, chapter: int) -> Path:
    if book_slug not in _BOOK_MAP:
        raise ValueError(f"unknown book slug: {book_slug!r}")
    _, abbr = _BOOK_MAP[book_slug]
    return _LOWFAT_DIR / f"{_BOOK_MAP[book_slug][0]:02d}-{abbr}-{chapter:03d}-lowfat.xml"


# ---------------------------------------------------------------------------
# Verse-ref parsing
# ---------------------------------------------------------------------------

# `ref` attribute on <w>: "GEN 40:1!3" -> (book_abbr, chapter, verse, position)
_REF_RE = re.compile(r"^([A-Z0-9]+)\s+(\d+):(\d+)!(\d+)$")


def parse_w_ref(ref: str) -> tuple[str, int, int, int]:
    m = _REF_RE.match(ref)
    if not m:
        raise ValueError(f"unparseable <w ref>: {ref!r}")
    return m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))


def verse_from_xml_id(xml_id: str) -> tuple[int, int, int]:
    """Lowfat xml:id is `o<book:2><chapter:3><verse:3><tokenidx:3>` (12 digits + 'o').

    Returns (book_num, chapter, verse). Used to determine cross-verse
    reference targets without needing the target token's <w ref>.
    """
    s = xml_id[1:] if xml_id.startswith("o") else xml_id
    if len(s) < 11:
        raise ValueError(f"short xml:id: {xml_id!r}")
    return int(s[0:2]), int(s[2:5]), int(s[5:8])


# ---------------------------------------------------------------------------
# Hebrew text normalization (for sense-line ↔ token matching)
# ---------------------------------------------------------------------------

# Strip te'amim (U+0591..U+05AF), niqqud (U+05B0..U+05BD, U+05BF..U+05C7),
# and maqqef (U+05BE). Keeps consonant skeleton.
_HEBREW_POINTS_RE = re.compile(r"[֑-ֿ׀-ׇ־]")


def consonant_skel(text: str) -> str:
    """Strip te'amim/niqqud/maqqef from Hebrew text, leaving bare consonants.

    Normalizes input to NFC first so consonant ordering is consistent regardless
    of the source's combining-mark order.
    """
    return _HEBREW_POINTS_RE.sub("", unicodedata.normalize("NFC", text))


# ---------------------------------------------------------------------------
# Frame-arg parsing
# ---------------------------------------------------------------------------

# Lowfat frame syntax: "A0:tokenID; A1:tokenID;tokenID2; A2:..."
# Empty slot: "A0:;" (e.g., imperatives — implicit subject).
# Always intra-chapter; per-chapter file structure makes cross-chapter impossible.

_FRAME_PART_RE = re.compile(r"\s*([A-Z][A-Z0-9-]*)\s*:\s*([^;]*?)\s*;")


def parse_frame_str(frame_str: str) -> dict[str, list[str]]:
    """Parse a frame attribute into {arg_label: [token_id, ...]}.

    Empty slots ('A0:;') become {'A0': []} — distinguishable from missing slots.
    Multi-token slots ('A1:id1;id2;') split on internal semicolons inside the slot.
    """
    if not frame_str:
        return {}
    result: dict[str, list[str]] = {}
    # Walk label:value; pairs.
    parts = re.findall(r"([A-Z][A-Z0-9-]*)\s*:\s*([^;A-Z]*(?:[A-Z0-9]+[^;A-Z]*)*?);", frame_str)
    # The above is fragile for multi-id values. Use a different strategy:
    # split on whitespace+label-prefix boundaries.
    result = {}
    # Find each "Lx:" label and the content up to the next label or end.
    label_re = re.compile(r"([A-Z][A-Z0-9-]*?):")
    matches = list(label_re.finditer(frame_str))
    for i, m in enumerate(matches):
        label = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(frame_str)
        chunk = frame_str[start:end].strip().rstrip(";").strip()
        if not chunk:
            result[label] = []
            continue
        # Multi-id values are separated by ';' inside the chunk.
        ids = [p.strip() for p in chunk.split(";") if p.strip()]
        result[label] = ids
    return result


def split_ref_list(refs: str) -> list[str]:
    """Split a participantref/subjref attribute into token IDs.

    Observed separators: space (most common), semicolon (rare).
    """
    if not refs:
        return []
    return [r for r in re.split(r"[\s;]+", refs.strip()) if r]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class Token:
    """A single <w> token from lowfat XML, with derived predicates."""

    xml_id: str                 # "o010010010021"
    ref: str                    # "GEN 1:1!2"
    book_num: int
    chapter: int
    verse: int
    position: int               # token position within verse

    text: str                   # surface form (with te'amim, no maqqef)
    lemma: Optional[str]
    pos: Optional[str]          # verb / noun / particle / preposition / pronoun / suffix / adjective / adverb / conjunction / article
    role: Optional[str]         # v / s / o / o2 / p / pp / adv  (None on function words)
    stem: Optional[str]         # qal / piel / niphal / hiphil / ...
    type_: Optional[str]        # qatal / yiqtol / wayyiqtol / imperative / participle active / participle passive / infinitive construct / infinitive absolute / pronominal / proper / common / interrogative / negative / cohortative / jussive
    state: Optional[str]        # absolute / construct / determined
    gender: Optional[str]
    number: Optional[str]
    person: Optional[str]
    lang: str                   # "H" or "A"
    after: str                  # trailing whitespace/punctuation (e.g., " ", "־", "׃")
    gloss: Optional[str]
    english: Optional[str]      # English content gloss (may differ from `gloss`, which is role-specific)
    transliteration: Optional[str]

    # Raw morph tag — escape hatch for queries the IR doesn't natively expose.
    # Prefer derived predicates (is_wayyiqtol, aspect, etc.) at call sites.
    _morph_tag: Optional[str] = None

    # Cross-token references (resolved post-parse)
    participantref_ids: list[str] = field(default_factory=list)
    subjref_ids: list[str] = field(default_factory=list)
    frame_arg_ids: dict[str, list[str]] = field(default_factory=dict)

    # Resolved object references (populated by Chapter.__post_init__)
    antecedents: list["Token"] = field(default_factory=list)
    referenced_subjects: list["Token"] = field(default_factory=list)
    frame_args: dict[str, list["Token"]] = field(default_factory=dict)

    # Structural backpointer
    parent_constituent: Optional["Constituent"] = None

    # ---- derived predicates ----

    @property
    def is_verb(self) -> bool:
        return self.pos == "verb"

    @property
    def is_noun(self) -> bool:
        return self.pos == "noun"

    @property
    def is_pronoun(self) -> bool:
        return self.pos == "pronoun"

    @property
    def is_suffix(self) -> bool:
        return self.pos == "suffix"

    @property
    def is_particle(self) -> bool:
        return self.pos == "particle"

    @property
    def is_preposition(self) -> bool:
        return self.pos == "preposition"

    @property
    def is_conjunction(self) -> bool:
        return self.pos == "conjunction"

    @property
    def is_wayyiqtol(self) -> bool:
        return self.type_ == "wayyiqtol"

    @property
    def is_yiqtol(self) -> bool:
        return self.type_ == "yiqtol"

    @property
    def is_qatal(self) -> bool:
        return self.type_ == "qatal"

    @property
    def is_weqatal(self) -> bool:
        """Vav-consecutive perfect (apodosis-marker). Lowfat encodes this
        natively as type="weqatal" (distinct from type="qatal")."""
        return self.type_ == "weqatal"

    @property
    def is_imperative(self) -> bool:
        return self.type_ == "imperative"

    @property
    def is_jussive(self) -> bool:
        return self.type_ == "jussive"

    @property
    def is_cohortative(self) -> bool:
        return self.type_ == "cohortative"

    @property
    def is_participle(self) -> bool:
        return self.type_ in ("participle active", "participle passive")

    @property
    def is_active_participle(self) -> bool:
        return self.type_ == "participle active"

    @property
    def is_passive_participle(self) -> bool:
        return self.type_ == "participle passive"

    @property
    def is_infinitive(self) -> bool:
        return self.type_ in ("infinitive construct", "infinitive absolute")

    @property
    def is_infinitive_construct(self) -> bool:
        return self.type_ == "infinitive construct"

    @property
    def is_infinitive_absolute(self) -> bool:
        return self.type_ == "infinitive absolute"

    @property
    def is_finite_verb(self) -> bool:
        return self.is_verb and self.type_ in (
            "qatal", "weqatal", "yiqtol", "wayyiqtol", "imperative",
            "jussive", "cohortative",
        )

    @property
    def is_construct(self) -> bool:
        return self.state == "construct"

    @property
    def aspect(self) -> Optional[str]:
        """Verbal aspect (qatal / weqatal / yiqtol / wayyiqtol / imperative /
        participle / infinitive) or None for non-verbs."""
        if not self.is_verb:
            return None
        if self.type_ in ("qatal", "weqatal", "yiqtol", "wayyiqtol",
                          "imperative", "jussive", "cohortative"):
            return self.type_
        if self.is_participle:
            return "participle"
        if self.is_infinitive:
            return "infinitive"
        return None

    def has_maqqef_after(self) -> bool:
        return self.after == "־"

    @property
    def consonant_skel(self) -> str:
        return consonant_skel(self.text)


@dataclass
class Constituent:
    """A <wg> word-group element. Children may be Constituents or Tokens (mixed)."""

    wg_class: Optional[str]           # cl / np / pp / adjp / advp / relp / cjp / nump / ij / ...
    wg_rule: Optional[str]            # V-O / V-S / NPofNP / NpaNp / V2CL / ClCl / ...
    role: Optional[str]               # role within parent (e.g., "o", "pp", "adv")
    is_head: bool = False

    children: list["Constituent | Token"] = field(default_factory=list)
    parent: Optional["Constituent"] = None

    @property
    def tokens(self) -> list[Token]:
        """All Token descendants in surface (document) order."""
        out: list[Token] = []
        for c in self.children:
            if isinstance(c, Token):
                out.append(c)
            else:
                out.extend(c.tokens)
        return out

    @property
    def child_constituents(self) -> list["Constituent"]:
        return [c for c in self.children if isinstance(c, Constituent)]

    @property
    def is_clause(self) -> bool:
        return self.wg_class == "cl"

    @property
    def is_np(self) -> bool:
        return self.wg_class == "np"

    @property
    def is_pp(self) -> bool:
        return self.wg_class == "pp"

    @property
    def is_relative_clause(self) -> bool:
        return self.wg_class == "relp" or self.wg_rule == "relCL"

    @property
    def is_construct_chain(self) -> bool:
        return self.wg_rule == "NPofNP"

    @property
    def is_apposition(self) -> bool:
        return self.wg_rule in ("NpaNp", "Np-Appos")

    def head_verb(self) -> Optional[Token]:
        """First token with role == 'v' anywhere in this constituent."""
        for t in self.tokens:
            if t.role == "v":
                return t
        return None

    def tokens_with_role(self, role: str) -> list[Token]:
        return [t for t in self.tokens if t.role == role]

    def ancestor_with(self, **predicates) -> Optional["Constituent"]:
        """Walk up to find an ancestor matching all predicates (e.g., wg_class='cl')."""
        node = self.parent
        while node is not None:
            if all(getattr(node, k, None) == v for k, v in predicates.items()):
                return node
            node = node.parent
        return None


@dataclass
class Sentence:
    """A <sentence> element, scoped to exactly one verse."""

    verse_ref: str                    # "GEN 1:1"
    book_num: int
    chapter: int
    verse: int
    tokens: list[Token]
    constituents: list[Constituent]   # top-level <wg> children of the sentence


@dataclass
class Chapter:
    """One lowfat XML file's worth of structure."""

    book_slug: str
    book_num: int
    chapter: int
    sentences: list[Sentence]
    tokens_by_id: dict[str, Token]    # xml:id -> Token, for ref resolution

    def get_verse_sentence(self, verse: int) -> Optional[Sentence]:
        for s in self.sentences:
            if s.verse == verse:
                return s
        return None

    def get_verse_tokens(self, verse: int) -> list[Token]:
        s = self.get_verse_sentence(verse)
        return s.tokens if s else []

    def get_verse_clauses(self, verse: int) -> list[Clause]:
        s = self.get_verse_sentence(verse)
        if not s:
            return []
        return _all_clauses(s.constituents)

    def get_verse_constituents(self, verse: int) -> list[Constituent]:
        s = self.get_verse_sentence(verse)
        return s.constituents if s else []


# Clause is a thin sugar over Constituent — kept as an alias rather than a
# subclass to avoid dataclass-inheritance friction. Use `c.is_clause` to test.
Clause = Constituent


# ---------------------------------------------------------------------------
# Recursive helpers
# ---------------------------------------------------------------------------


def _all_clauses(roots: list[Constituent]) -> list[Constituent]:
    out: list[Constituent] = []

    def walk(node: Constituent | Token):
        if isinstance(node, Token):
            return
        if node.is_clause:
            out.append(node)
        for c in node.children:
            walk(c)

    for r in roots:
        walk(r)
    return out


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

# ElementTree drops xmlns prefixes inconsistently; lowfat uses none, so plain
# tag names are fine. The xml:id attribute is qualified, however.
_XML_ID_KEY = "{http://www.w3.org/XML/1998/namespace}id"


def _w_to_token(elem: ET.Element, book_num: int) -> Token:
    xml_id = elem.attrib.get(_XML_ID_KEY) or elem.attrib.get("xml:id") or ""
    ref = elem.attrib.get("ref", "")
    if ref:
        _, ch, vs, pos = parse_w_ref(ref)
    else:
        # Fallback to xml_id-derived
        b, ch, vs = verse_from_xml_id(xml_id)
        pos = int(xml_id[-3:])

    text = (elem.text or "").strip() or elem.attrib.get("unicode", "")

    morph = elem.attrib.get("morph")
    return Token(
        xml_id=xml_id,
        ref=ref,
        book_num=book_num,
        chapter=ch,
        verse=vs,
        position=pos,
        text=_nfc(text) or "",
        lemma=_nfc(elem.attrib.get("lemma")),
        pos=elem.attrib.get("pos") or elem.attrib.get("class"),
        role=elem.attrib.get("role"),
        stem=elem.attrib.get("stem"),
        type_=elem.attrib.get("type"),
        state=elem.attrib.get("state"),
        gender=elem.attrib.get("gender"),
        number=elem.attrib.get("number"),
        person=elem.attrib.get("person"),
        lang=elem.attrib.get("lang", "H"),
        after=elem.attrib.get("after", ""),
        gloss=elem.attrib.get("gloss"),
        english=elem.attrib.get("english"),
        transliteration=elem.attrib.get("transliteration"),
        _morph_tag=morph,
        participantref_ids=split_ref_list(elem.attrib.get("participantref", "")),
        subjref_ids=split_ref_list(elem.attrib.get("subjref", "")),
        frame_arg_ids=parse_frame_str(elem.attrib.get("frame", "")),
    )


def _wg_to_constituent(elem: ET.Element, book_num: int,
                       parent: Optional[Constituent]) -> Constituent:
    cons = Constituent(
        wg_class=elem.attrib.get("class"),
        wg_rule=elem.attrib.get("rule"),
        role=elem.attrib.get("role"),
        is_head=elem.attrib.get("head") == "true",
        parent=parent,
    )
    for child in elem:
        if child.tag == "wg":
            cons.children.append(_wg_to_constituent(child, book_num, cons))
        elif child.tag == "w":
            tok = _w_to_token(child, book_num)
            tok.parent_constituent = cons
            cons.children.append(tok)
        # Other elements (milestone, p) ignored at the constituent level
    return cons


def _parse_sentence(elem: ET.Element, book_num: int) -> Optional[Sentence]:
    """Return None if the sentence contains no <w> tokens (defensive)."""
    sentence_id = elem.attrib.get("id", "")
    if not sentence_id:
        return None
    parts = sentence_id.split()
    if len(parts) != 2:
        return None
    try:
        ch_str, vs_str = parts[1].split(":")
        ch, vs = int(ch_str), int(vs_str)
    except ValueError:
        return None

    constituents: list[Constituent] = []
    # The <sentence>/<p> wrapper structure is variable. Walk recursively until
    # we find <wg> children.
    def collect_wgs(node: ET.Element) -> None:
        for child in node:
            if child.tag == "wg":
                constituents.append(_wg_to_constituent(child, book_num, None))
            elif child.tag in ("p", "sentence"):
                collect_wgs(child)

    collect_wgs(elem)

    tokens: list[Token] = []
    for c in constituents:
        tokens.extend(c.tokens)
    if not tokens:
        return None
    return Sentence(
        verse_ref=sentence_id,
        book_num=book_num,
        chapter=ch,
        verse=vs,
        tokens=tokens,
        constituents=constituents,
    )


def _parse_chapter(book_slug: str, chapter: int) -> Chapter:
    path = lowfat_path(book_slug, chapter)
    if not path.exists():
        raise FileNotFoundError(f"lowfat XML not found: {path}")
    book_num, _ = _BOOK_MAP[book_slug]

    tree = ET.parse(path)
    root = tree.getroot()

    sentences: list[Sentence] = []
    for elem in root.iter("sentence"):
        s = _parse_sentence(elem, book_num)
        if s is not None:
            sentences.append(s)

    # Build xml_id -> Token map and resolve cross-token references in pass 2.
    tokens_by_id: dict[str, Token] = {}
    for s in sentences:
        for t in s.tokens:
            tokens_by_id[t.xml_id] = t

    # Resolve references. Lowfat token IDs in participantref/subjref/frame
    # do NOT carry the leading 'o', but xml:id does. Normalize.
    def lookup(rid: str) -> Optional[Token]:
        return tokens_by_id.get(rid) or tokens_by_id.get("o" + rid)

    for s in sentences:
        for t in s.tokens:
            t.antecedents = [tok for tok in (lookup(r) for r in t.participantref_ids) if tok is not None]
            t.referenced_subjects = [tok for tok in (lookup(r) for r in t.subjref_ids) if tok is not None]
            t.frame_args = {
                label: [tok for tok in (lookup(r) for r in ids) if tok is not None]
                for label, ids in t.frame_arg_ids.items()
            }

    return Chapter(
        book_slug=book_slug,
        book_num=book_num,
        chapter=chapter,
        sentences=sentences,
        tokens_by_id=tokens_by_id,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# Two-level cache: {book_slug: {chapter: Chapter}}.
# Per-chapter granularity (per audit recommendation): scales to multi-book
# corpora and avoids paying full-book parse cost when only one chapter is needed.
_CACHE: dict[str, dict[int, Chapter]] = {}


def get_chapter(book_slug: str, chapter: int) -> Chapter:
    book = _CACHE.setdefault(book_slug, {})
    if chapter not in book:
        book[chapter] = _parse_chapter(book_slug, chapter)
    return book[chapter]


def get_verse_sentence(book_slug: str, chapter: int, verse: int) -> Optional[Sentence]:
    return get_chapter(book_slug, chapter).get_verse_sentence(verse)


def get_verse_tokens(book_slug: str, chapter: int, verse: int) -> list[Token]:
    return get_chapter(book_slug, chapter).get_verse_tokens(verse)


def get_verse_clauses(book_slug: str, chapter: int, verse: int) -> list[Clause]:
    return get_chapter(book_slug, chapter).get_verse_clauses(verse)


def get_verse_constituents(book_slug: str, chapter: int, verse: int) -> list[Constituent]:
    return get_chapter(book_slug, chapter).get_verse_constituents(verse)


def clear_cache() -> None:
    """Reset the per-chapter cache. Primarily for tests."""
    _CACHE.clear()


# ---------------------------------------------------------------------------
# Sense-line ↔ Token matching
# ---------------------------------------------------------------------------
#
# Validators operate on editorial sense-lines (v2/he), not on lowfat verses.
# To use IR queries from a sense-line context, we need to map a sense-line's
# Hebrew text to the subset of verse Tokens it contains.
#
# Strategy: greedy left-to-right consonant-skeleton matching against verse
# tokens in document order. This mirrors gnt-reader's _match_line_words.
# Robust to te'amim/niqqud/maqqef differences between editorial text and
# Macula source.


def match_sense_line_tokens(verse_tokens: list[Token],
                            sense_line_text: str,
                            start_idx: int = 0) -> tuple[list[Token], int]:
    """Match a sense-line's text to a contiguous slice of verse Tokens.

    Returns (matched_tokens, next_start_idx). next_start_idx can be passed back
    in for the next sense-line of the same verse to avoid re-scanning matched
    tokens.

    Greedy: walks tokens from start_idx, accumulating consonants, until the
    accumulated consonant string equals (or exceeds) the sense-line's
    consonant skeleton. Tolerates the line containing extra punctuation
    (verse-end marker, etc.) by matching the line's bare consonants.
    """
    line_skel = consonant_skel(sense_line_text).replace(" ", "")
    if not line_skel:
        return [], start_idx
    matched: list[Token] = []
    accum = ""
    i = start_idx
    while i < len(verse_tokens) and len(accum) < len(line_skel):
        t = verse_tokens[i]
        accum += t.consonant_skel
        matched.append(t)
        i += 1
        if accum == line_skel:
            return matched, i
    # If accum overshoots (line ended mid-token-pair), accept the match if the
    # line_skel is a prefix of accum.
    if accum.startswith(line_skel):
        return matched, i
    # No clean match. Return what we got; caller can decide.
    return matched, i
