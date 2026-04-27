#!/usr/bin/env python3
"""
english_quality_check.py — Validate English structural glosses for quality issues.

Uses spaCy (en_core_web_sm) and Macula Hebrew TSV to detect:
  1. Pronoun errors   — masculine/feminine Hebrew referent rendered as "its"
  2. Missing verbs    — lines with no VERB or AUX (exceptions: vocatives, list items, triadic stacks)
  3. Nonsense fragments — under 3 words, not vocative or imperative
  4. Repeated words   — same content word appearing twice on one line
  5. Mid-word splits  — line starts lowercase but isn't a conjunction

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/english_quality_check.py              # all files
    PYTHONIOENCODING=utf-8 py -3 scripts/english_quality_check.py --book jonah  # one book
    PYTHONIOENCODING=utf-8 py -3 scripts/english_quality_check.py --all-books   # full corpus
"""

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import spacy

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

ENG_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "eng-gloss"
if not ENG_DIR.exists():
    print("ERROR: Cannot find English gloss directory.", file=sys.stderr)
    sys.exit(1)

MACULA_TSV = REPO_ROOT / "research" / "macula-hebrew" / "WLC" / "tsv" / "macula-hebrew.tsv"

# ---------------------------------------------------------------------------
# Book-name mapping  (directory short-name → Macula 3-letter code)
# Standard ordering / abbreviations drawn from Masoretic canon.
# ---------------------------------------------------------------------------
BOOK_TO_MACULA = {
    # Torah
    "genesis": "GEN", "gen": "GEN",
    "exodus": "EXO", "exo": "EXO",
    "leviticus": "LEV", "lev": "LEV",
    "numbers": "NUM", "num": "NUM",
    "deuteronomy": "DEU", "deu": "DEU",
    # Nevi'im
    "joshua": "JOS", "jos": "JOS",
    "judges": "JDG", "jdg": "JDG",
    "ruth": "RUT", "rut": "RUT",
    "1samuel": "1SA", "1sa": "1SA",
    "2samuel": "2SA", "2sa": "2SA",
    "1kings": "1KI", "1ki": "1KI",
    "2kings": "2KI", "2ki": "2KI",
    "isaiah": "ISA", "isa": "ISA",
    "jeremiah": "JER", "jer": "JER",
    "ezekiel": "EZK", "ezk": "EZK",
    "hosea": "HOS", "hos": "HOS",
    "joel": "JOL", "jol": "JOL",
    "amos": "AMO", "amo": "AMO",
    "obadiah": "OBA", "oba": "OBA",
    "jonah": "JON", "jon": "JON",
    "micah": "MIC", "mic": "MIC",
    "nahum": "NAM", "nam": "NAM",
    "habakkuk": "HAB", "hab": "HAB",
    "zephaniah": "ZEP", "zep": "ZEP",
    "haggai": "HAG", "hag": "HAG",
    "zechariah": "ZEC", "zec": "ZEC",
    "malachi": "MAL", "mal": "MAL",
    # Ketuvim
    "psalms": "PSA", "psa": "PSA",
    "proverbs": "PRO", "pro": "PRO",
    "job": "JOB",
    "songofsolomon": "SNG", "sng": "SNG", "song": "SNG",
    "ecclesiastes": "ECC", "ecc": "ECC",
    "lamentations": "LAM", "lam": "LAM",
    "esther": "EST", "est": "EST",
    "daniel": "DAN", "dan": "DAN",
    "ezra": "EZR", "ezr": "EZR",
    "nehemiah": "NEH", "neh": "NEH",
    "1chronicles": "1CH", "1ch": "1CH",
    "2chronicles": "2CH", "2ch": "2CH",
}


def extract_book_short(dir_name):
    """Extract book short name from directory (handles '05-jonah' → 'jonah' or plain 'jonah')."""
    if re.match(r"^\d{2}-", dir_name):
        return dir_name[3:]
    return dir_name


# Lowercase conjunctions / particles that legitimately start a colon
CONJUNCTIONS = {"and", "but", "for", "or", "nor", "yet", "so", "then",
                "that", "because", "since", "when", "if", "although",
                "while", "though", "until", "unless", "where", "who",
                "whom", "whose", "which", "what", "whether", "than",
                "as", "even", "not", "just", "also", "to", "of", "in",
                "by", "with", "from", "at", "on", "into", "through",
                "all", "no", "neither", "both", "either", "how",
                "lest", "like", "before", "after", "about"}

# Content-word POS tags (for repeated-word check)
CONTENT_POS = {"NOUN", "VERB", "ADJ", "ADV", "PROPN"}

# ---------------------------------------------------------------------------
# Load Macula data (verse-level gender info)
# ---------------------------------------------------------------------------
def load_macula_gender(book_code):
    """Return dict: verse_ref (e.g. '1:1') → list of token dicts with gender field."""
    verse_genders = defaultdict(list)
    if not MACULA_TSV.exists():
        return verse_genders
    with open(MACULA_TSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            ref = row.get("ref", "")
            if not ref.startswith(book_code + " "):
                continue
            # ref format: "JON 1:1!1"  → extract "1:1"
            parts = ref.split(" ", 1)
            if len(parts) < 2:
                continue
            verse_part = parts[1].split("!")[0]  # "1:1"
            gender = row.get("gender", "")
            text = row.get("text", "")
            morph = row.get("morph", "")
            lemma = row.get("lemma", "")
            if gender:
                verse_genders[verse_part].append({
                    "text": text, "gender": gender, "morph": morph, "lemma": lemma
                })
    return verse_genders


def has_noun_with_gender(verse_words, target_gender):
    """Check if any noun or pronoun in verse has given gender (masculine/feminine)."""
    for w in verse_words:
        morph = w.get("morph", "")
        gender = w.get("gender", "")
        # Only nouns and pronouns — skip conjunctions, particles, prepositions
        # Macula Hebrew morph: Nc* = common noun, Np = proper noun, Pd* = demonstrative etc.
        pos_class = morph[:2] if len(morph) >= 2 else ""
        if pos_class in ("Nc", "Np", "Pd", "Pp", "Pi", "Pr"):
            if gender == target_gender:
                return True
    return False


# ---------------------------------------------------------------------------
# Issue dataclass
# ---------------------------------------------------------------------------
class Issue:
    def __init__(self, file, verse, line_num, line_text, issue_type, detail):
        self.file = file
        self.verse = verse
        self.line_num = line_num
        self.line_text = line_text
        self.issue_type = issue_type
        self.detail = detail

    def __str__(self):
        return (f"  [{self.issue_type}] {self.file} {self.verse} (line {self.line_num})\n"
                f"    \"{self.line_text}\"\n"
                f"    → {self.detail}")


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------
def check_pronoun_errors(line, verse_ref, verse_genders, issues_out, file_rel, line_num):
    """Flag 'its' when Hebrew verse has masculine/feminine noun referent."""
    if " its " not in f" {line} " and not line.startswith("its ") and not line.endswith(" its"):
        return
    verse_words = verse_genders.get(verse_ref, [])
    if not verse_words:
        return
    if has_noun_with_gender(verse_words, "masculine") or has_noun_with_gender(verse_words, "feminine"):
        gender_found = "masculine" if has_noun_with_gender(verse_words, "masculine") else "feminine"
        issues_out.append(Issue(
            file_rel, verse_ref, line_num, line,
            "PRONOUN", f"'its' used but Hebrew verse has {gender_found} referent — should be 'his'/'her'?"
        ))


def check_missing_verb(doc, line, verse_ref, issues_out, file_rel, line_num, context_lines):
    """Flag lines with no verb/aux. Skip vocatives, list items, triadic stacks."""
    tokens = [t for t in doc if not t.is_punct and not t.is_space]
    if len(tokens) < 2:
        return  # handled by fragment check

    has_verb = any(t.pos_ in ("VERB", "AUX") for t in doc)
    if has_verb:
        return

    stripped = line.strip()

    # Exception: vocative lines (all caps)
    if stripped.isupper():
        return

    # Exception: lines starting with coordinating/subordinating conjunctions
    if stripped.lower().startswith(("and ", "or ", "both ", "neither ")):
        return

    # Exception: prepositional phrases, subordinate clause starters
    if tokens and tokens[0].pos_ in ("ADP", "SCONJ"):
        return

    # Exception: noun phrase continuations / appositional phrases
    if stripped.endswith(",") or stripped.endswith(";"):
        return

    # Exception: lines clearly beginning a noun phrase (articles, possessives, determiners)
    first_word = stripped.split()[0].lower() if stripped.split() else ""
    if first_word in ("the", "a", "an", "his", "her", "their", "its", "my", "our", "your",
                      "this", "that", "these", "those", "every", "each", "all", "some"):
        return

    issues_out.append(Issue(
        file_rel, verse_ref, line_num, line,
        "NO_VERB", "No verb or auxiliary detected in this line"
    ))


def check_fragment(line, doc, verse_ref, issues_out, file_rel, line_num):
    """Flag lines under 3 words that aren't vocatives or imperatives."""
    tokens = [t for t in doc if not t.is_punct and not t.is_space]
    if len(tokens) >= 3:
        return
    if len(tokens) == 0:
        return

    stripped = line.strip()

    # Exception: vocatives (all caps, or ending with comma/exclamation)
    if stripped.isupper():
        return
    if stripped.endswith(",") or stripped.endswith("!"):
        return

    # Exception: imperatives
    has_imperative = any(t.pos_ == "VERB" and "Imp" in t.morph.get("Mood", [""]) for t in doc)
    if has_imperative:
        return

    # Exception: common short valid phrases (including Hebrew liturgical terms)
    if stripped.lower() in ("amen", "amen.", "yes.", "selah", "hallelujah", "maranatha",
                             "abba", "selah.", "hosanna"):
        return

    # Exception: single-word proper names or interjections
    if len(tokens) == 1 and tokens[0].pos_ in ("INTJ", "PROPN"):
        return

    # Exception: "Yes. Amen." type two-word exclamation pairs
    if re.match(r"^[A-Z][a-z]*\.\s*[A-Z][a-z]*\.$", stripped):
        return

    issues_out.append(Issue(
        file_rel, verse_ref, line_num, line,
        "FRAGMENT", f"Only {len(tokens)} content word(s) — possible nonsense fragment"
    ))


def check_repeated_words(line, doc, verse_ref, issues_out, file_rel, line_num):
    """Flag lines where the same content word appears twice."""
    content_words = [t.text.lower() for t in doc if t.pos_ in CONTENT_POS and len(t.text) > 2]
    counts = Counter(content_words)
    repeats = {w: c for w, c in counts.items() if c >= 2}
    if repeats:
        # Filter out common legitimate repeats (including Tanakh-specific idioms)
        legit = {"lord", "god", "holy", "amen", "come", "great", "said", "say",
                 "one", "first", "good", "day", "man", "son", "spirit", "father",
                 "king", "name", "life", "word", "death", "water", "fire", "land",
                 "heaven", "earth", "right", "left", "true", "people", "house",
                 "yahweh", "israel", "servant", "heart", "hand"}
        flagged = {w: c for w, c in repeats.items() if w not in legit}
        if flagged:
            words_str = ", ".join(f"'{w}'×{c}" for w, c in flagged.items())
            issues_out.append(Issue(
                file_rel, verse_ref, line_num, line,
                "REPEAT", f"Repeated content word(s): {words_str}"
            ))


def check_mid_word_split(line, verse_ref, nlp, issues_out, file_rel, line_num):
    """Flag lines that appear to start with a word fragment from a bad split.

    In colometric text, lowercase-starting lines are normal (participial phrases,
    pronouns, articles, etc.). We only flag lines where the first word:
      - Is not recognized by spaCy as a real English word (OOV and short)
      - Looks like a suffix fragment (e.g. 'tion', 'ing' without a stem)
    """
    stripped = line.strip()
    if not stripped:
        return
    first_char = stripped[0]
    # Only check lowercase starts
    if not first_char.islower():
        return
    first_word = stripped.split()[0].rstrip(",.;:!?")
    if not first_word:
        return

    doc = nlp(first_word)
    token = doc[0] if doc else None

    # If spaCy assigns a real POS (not X=unknown), it's fine
    if token and token.pos_ != "X":
        return

    # Only flag very short OOV fragments
    if len(first_word) <= 3 and token and token.is_oov:
        issues_out.append(Issue(
            file_rel, verse_ref, line_num, line,
            "MID_SPLIT", f"Line starts with possible word fragment: '{first_word}'"
        ))
    elif token and token.is_oov and not first_word[0].isupper():
        # OOV lowercase word — only flag if it looks like a suffix
        suffix_patterns = re.compile(
            r"^(tion|sion|ment|ness|ance|ence|ible|able|ious|eous|ting|ning|ling|ght)s?$", re.I
        )
        if suffix_patterns.match(first_word):
            issues_out.append(Issue(
                file_rel, verse_ref, line_num, line,
                "MID_SPLIT", f"Line starts with possible word fragment: '{first_word}'"
            ))


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------
def process_file(filepath, book_dir_name, nlp, macula_genders):
    """Process one English gloss file, return list of Issues."""
    issues = []
    file_rel = f"{book_dir_name}/{filepath.name}"

    lines = filepath.read_text(encoding="utf-8").splitlines()
    current_verse = "?"
    content_lines = []  # (line_num, verse_ref, text)

    for i, raw_line in enumerate(lines, 1):
        stripped = raw_line.strip()
        if not stripped:
            continue
        # Verse reference line
        if re.match(r"^\d+:\d+[a-z]?$", stripped):
            current_verse = stripped
            continue
        content_lines.append((i, current_verse, stripped))

    # Process with spaCy in batches for performance
    texts = [cl[2] for cl in content_lines]
    docs = list(nlp.pipe(texts, batch_size=64))

    for idx, (line_num, verse_ref, line_text) in enumerate(content_lines):
        doc = docs[idx]

        # Context lines for stack detection (2 before, 2 after)
        ctx_start = max(0, idx - 2)
        ctx_end = min(len(content_lines), idx + 3)
        context = [content_lines[j][2] for j in range(ctx_start, ctx_end) if j != idx]

        # Run checks
        check_pronoun_errors(line_text, verse_ref, macula_genders, issues, file_rel, line_num)
        check_missing_verb(doc, line_text, verse_ref, issues, file_rel, line_num, context)
        check_fragment(line_text, doc, verse_ref, issues, file_rel, line_num)
        check_repeated_words(line_text, doc, verse_ref, issues, file_rel, line_num)
        check_mid_word_split(line_text, verse_ref, nlp, issues, file_rel, line_num)

    return issues


def get_book_dirs(book_filter=None):
    """Return list of (dir_path, dir_name) for books to process.

    --book accepts either the full dir name ('05-jonah') or the short name ('jonah').
    """
    dirs = []
    for d in sorted(ENG_DIR.iterdir()):
        if d.is_dir():
            if book_filter:
                short = extract_book_short(d.name)
                if d.name != book_filter and short != book_filter:
                    continue
            dirs.append((d, d.name))
    return dirs


def main():
    parser = argparse.ArgumentParser(description="English gloss quality checker")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--book", type=str, default=None,
                       help="Process only this book (directory name or short name, e.g. 'jonah')")
    group.add_argument("--all-books", action="store_true",
                       help="Process all books (same as omitting --book)")
    args = parser.parse_args()

    print("Loading spaCy model...", file=sys.stderr)
    nlp = spacy.load("en_core_web_sm")

    book_filter = args.book if not args.all_books else None
    book_dirs = get_book_dirs(book_filter)
    if not book_dirs:
        print(f"ERROR: No book directories found (filter={args.book})", file=sys.stderr)
        sys.exit(1)

    all_issues = []
    file_issue_counts = Counter()
    type_counts = Counter()

    for book_dir, book_name in book_dirs:
        book_short = extract_book_short(book_name)
        macula_code = BOOK_TO_MACULA.get(book_short)
        print(f"Processing {book_name}...", file=sys.stderr)

        # Load Macula gender data for this book
        macula_genders = {}
        if macula_code and MACULA_TSV.exists():
            macula_genders = load_macula_gender(macula_code)

        # Process each chapter file
        chapter_files = sorted(book_dir.glob("*.txt"))
        for cf in chapter_files:
            issues = process_file(cf, book_name, nlp, macula_genders)
            all_issues.extend(issues)
            if issues:
                file_issue_counts[f"{book_name}/{cf.name}"] += len(issues)
                for iss in issues:
                    type_counts[iss.issue_type] += 1

    # ---------------------------------------------------------------------------
    # Report
    # ---------------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("ENGLISH QUALITY CHECK REPORT")
    print("=" * 72)

    if not all_issues:
        print("\nNo issues found!")
        return

    # Group by type
    by_type = defaultdict(list)
    for iss in all_issues:
        by_type[iss.issue_type].append(iss)

    type_labels = {
        "PRONOUN": "Pronoun Errors (its → his/her)",
        "NO_VERB": "Missing Verbs",
        "FRAGMENT": "Nonsense Fragments",
        "REPEAT": "Repeated Words",
        "MID_SPLIT": "Mid-Sentence Splits",
    }

    for itype in ("PRONOUN", "NO_VERB", "FRAGMENT", "REPEAT", "MID_SPLIT"):
        items = by_type.get(itype, [])
        if not items:
            continue
        label = type_labels.get(itype, itype)
        print(f"\n--- {label} ({len(items)} issues) ---\n")
        for iss in items:
            print(iss)
        print()

    # Summary
    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"\nTotal issues: {len(all_issues)}\n")
    print("By type:")
    for itype in ("PRONOUN", "NO_VERB", "FRAGMENT", "REPEAT", "MID_SPLIT"):
        label = type_labels.get(itype, itype)
        count = type_counts.get(itype, 0)
        if count:
            print(f"  {label:45s} {count:5d}")

    print(f"\nWorst files (top 15):")
    for fname, count in file_issue_counts.most_common(15):
        print(f"  {fname:50s} {count:4d} issues")


if __name__ == "__main__":
    main()
