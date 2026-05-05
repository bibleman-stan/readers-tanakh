#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
measure_validator_fp_rate.py — Phase 2 first commit.

Per CLAUDE.md "Deferred Operational Work" item #1. The script is the
first-commit definition of Phase 2: until it exists and runs clean on a
labeled fixture set, "Phase 2" is a CYA pause, not a pivot.

Two modes:
  --sample : draw a 500-verse stratified sampling frame (100 verses per
             cluster across clusters 1-5; within each cluster, allocate to
             books proportional to chapter count; within each book, sample
             uniformly across (chapter, verse) pairs). Emit a fixture
             template TSV with empty label columns to be filled by editorial
             review.

  --measure : load a labeled fixture TSV, invoke each referenced validator
              against each book in the fixture set with --json, match
              findings to fixture rows by (book, chapter, verse, validator),
              compare actual-action against expected-action, compute
              per-validator TP / FP / FN / uncalibrated counts. Emit
              validators/.fp-baseline.json.

Sampling frame definition (mirrors CLAUDE.md spec):
  - Clusters 1-5 only (Embedded Poetry deferred to its own fixture later)
  - 100 verses per cluster
  - Within each cluster, allocate to books proportional to chapter count
  - Within each book, sample uniformly across (chapter, verse) pairs
  - Stable seed (42) for reproducibility

Fixture file (tests/fp-baseline-fixtures.tsv) columns:
  verse_id            book/chapter:verse, e.g. "01-genesis/1:1"
  validator_name      e.g. "validate_clause_nucleus_split"
  expected_action     APPLY | REVIEW | REJECT
  rationale_brief     one-line note from the labeler

Output (validators/.fp-baseline.json):
  {
    "fixture_count": 500,
    "labeled_count": int,
    "validators": {
      "<validator_name>": {
        "tp": int,                # ground-truth APPLY  + actual STRONG
        "fp": int,                # ground-truth REJECT + actual STRONG
        "fn": int,                # ground-truth APPLY  + actual none/REVIEW
        "uncalibrated": int,      # ground-truth REVIEW + actual STRONG
        "tn": int,                # ground-truth REJECT + actual none/REVIEW
        "review_correct": int,    # ground-truth REVIEW + actual REVIEW
        "labeled_total": int,
        "tp_rate": float,         # tp / (tp + fn) when both ground-truths exist
        "fp_rate": float          # fp / (fp + tn) when both ground-truths exist
      }, ...
    },
    "ground_truth_summary": {"APPLY": int, "REVIEW": int, "REJECT": int}
  }

Usage:
  PYTHONIOENCODING=utf-8 py -3 scripts/measure_validator_fp_rate.py --sample
  PYTHONIOENCODING=utf-8 py -3 scripts/measure_validator_fp_rate.py --measure
  PYTHONIOENCODING=utf-8 py -3 scripts/measure_validator_fp_rate.py --measure --validator validate_short_orphan_line
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
V2_HE_DIR = REPO_ROOT / "data" / "text-files" / "v2" / "he"
VALIDATORS_DIR = REPO_ROOT / "validators"
FIXTURE_FILE = REPO_ROOT / "tests" / "fp-baseline-fixtures.tsv"
OUTPUT_FILE = REPO_ROOT / "validators" / ".fp-baseline.json"

# Per CLAUDE.md "Corpus Cluster Splits" — clusters 1-5 only for this fixture set.
# Cluster 6 (Embedded Poetry) defers to its own fixture per CLAUDE.md item #1
# rationale ("small enough to fixture separately later").
CLUSTERS: dict[str, list[str]] = {
    "torah": ["01-genesis", "02-exodus", "03-leviticus", "04-numbers", "05-deuteronomy"],
    "former_prophets": ["06-joshua", "07-judges", "09-1samuel", "10-2samuel", "11-1kings", "12-2kings"],
    "latter_prophets": [
        "23-isaiah", "24-jeremiah", "26-ezekiel",
        "28-hosea", "29-joel", "30-amos", "31-obadiah", "32-jonah",
        "33-micah", "34-nahum", "35-habakkuk", "36-zephaniah",
        "37-haggai", "38-zechariah", "39-malachi",
    ],
    "writings_prose": [
        "08-ruth", "13-1chronicles", "14-2chronicles", "15-ezra",
        "16-nehemiah", "17-esther", "21-ecclesiastes", "22-songofsongs",
        "25-lamentations", "27-daniel",
    ],
    "sifrei_emet": ["18-job", "19-psalms", "20-proverbs"],
}

VERSES_PER_CLUSTER = 100
SAMPLE_SEED = 42

_VERSE_REF_RE = re.compile(r"^\d+:\d+[a-z]?$")


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

def enumerate_book_verses(book_dir: Path) -> list[tuple[int, str]]:
    """Return [(chapter_num, verse_ref)] for every verse in book.

    Verse markers are bare lines matching \\d+:\\d+(?:[a-z])?.
    """
    out: list[tuple[int, str]] = []
    for chapter_file in sorted(book_dir.glob("*.txt")):
        # Chapter number is the trailing -NN before .txt
        m = re.search(r"-(\d+)\.txt$", chapter_file.name)
        if not m:
            continue
        chapter_num = int(m.group(1))
        try:
            text = chapter_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = chapter_file.read_text(encoding="utf-8-sig")
        for line in text.splitlines():
            s = line.strip()
            if _VERSE_REF_RE.match(s):
                out.append((chapter_num, s))
    return out


def sample_cluster(cluster_name: str, books: list[str], rng: random.Random) -> list[tuple[str, int, str]]:
    """Sample VERSES_PER_CLUSTER verses from `books`, stratified by book.

    Returns [(book, chapter, verse_ref)].
    """
    # Step 1: count chapters per book
    book_chapters: dict[str, int] = {}
    book_verses: dict[str, list[tuple[int, str]]] = {}
    for book in books:
        bdir = V2_HE_DIR / book
        if not bdir.is_dir():
            continue
        verses = enumerate_book_verses(bdir)
        book_verses[book] = verses
        # Chapter count = distinct chapter numbers seen
        book_chapters[book] = len({c for c, _ in verses})

    total_chapters = sum(book_chapters.values())
    if total_chapters == 0:
        return []

    # Step 2: allocate VERSES_PER_CLUSTER proportional to chapter count;
    # use largest-remainder rounding to ensure integer allocations sum to N.
    raw_alloc = {b: VERSES_PER_CLUSTER * book_chapters[b] / total_chapters for b in book_chapters}
    floor_alloc = {b: int(raw_alloc[b]) for b in raw_alloc}
    remainders = sorted(
        ((raw_alloc[b] - floor_alloc[b], b) for b in raw_alloc),
        reverse=True,
    )
    leftover = VERSES_PER_CLUSTER - sum(floor_alloc.values())
    final_alloc = dict(floor_alloc)
    for i in range(leftover):
        _, b = remainders[i % len(remainders)]
        final_alloc[b] += 1

    # Step 3: sample uniformly within each book
    sampled: list[tuple[str, int, str]] = []
    for book, n in final_alloc.items():
        verses = book_verses.get(book, [])
        if not verses:
            continue
        if len(verses) <= n:
            picks = list(verses)
        else:
            picks = rng.sample(verses, n)
        for ch, vref in sorted(picks):
            sampled.append((book, ch, vref))
    return sampled


def sample_all_clusters() -> dict[str, list[tuple[str, int, str]]]:
    rng = random.Random(SAMPLE_SEED)
    out: dict[str, list[tuple[str, int, str]]] = {}
    for cluster_name, books in CLUSTERS.items():
        out[cluster_name] = sample_cluster(cluster_name, books, rng)
    return out


# ---------------------------------------------------------------------------
# Fixture I/O
# ---------------------------------------------------------------------------

def fixture_template_rows(samples_by_cluster: dict[str, list[tuple[str, int, str]]]) -> list[str]:
    """Generate fixture rows for the sampling frame, FILTERED to active findings.

    The script runs each validator against each book in the sample, then emits
    one row per (verse, validator) pair where the validator currently fires
    (REVIEW or STRONG). Rows include `current_tag` and `current_brief` columns
    so the labeler sees the validator's actual decision + rationale alongside
    the expected_action slot.

    Excluded: (verse, validator) pairs where the validator emits NONE — they
    yield no FP signal under the current adoption model. Add `--all-rows`
    flag if FN-class measurement (validator missed something) is needed.
    """
    validator_files = sorted(VALIDATORS_DIR.glob("syntax/validate_*.py")) + \
                      sorted(VALIDATORS_DIR.glob("colometry/validate_*.py"))
    validator_names = [f.stem for f in validator_files]

    # Group sampled verses by book so we batch validator invocations
    verses_by_book: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for cluster_name in CLUSTERS:
        for (book, ch, vref) in samples_by_cluster.get(cluster_name, []):
            verses_by_book[book].append((ch, vref))

    rows = ["verse_id\tvalidator_name\tcurrent_tag\tcurrent_brief\texpected_action\trationale_brief"]

    # Per (book, validator), run once, scan all sampled verses in that book
    sampled_books = sorted(verses_by_book.keys())
    n_invocations = len(validator_names) * len(sampled_books)
    print(
        f"Running {n_invocations} validator invocations "
        f"({len(validator_names)} validators × {len(sampled_books)} books) "
        f"to filter fixture rows ...",
        file=sys.stderr,
    )

    for book in sampled_books:
        verses_in_book = verses_by_book[book]
        # Build chapter-verse line maps once per chapter we touch
        chapters_needed = sorted({ch for ch, _ in verses_in_book})
        line_maps: dict[int, dict[str, tuple[int, int]]] = {
            ch: chapter_verse_line_map(book, ch) for ch in chapters_needed
        }

        for vname in validator_names:
            findings = run_validator_for_book(vname, book)
            if not findings:
                continue
            for (ch, vref) in verses_in_book:
                line_map = line_maps.get(ch, {})
                if vref not in line_map:
                    continue
                start, end = line_map[vref]
                # Find the strongest finding in this verse for this validator.
                # Filter by chapter file path FIRST so a line-N finding from
                # genesis-11 isn't matched to genesis-08:line-N.
                in_verse: list[dict] = []
                for f in findings:
                    if not finding_in_chapter(f, book, ch):
                        continue
                    line = f.get("line") or f.get("line_num")
                    if isinstance(line, int) and start <= line <= end:
                        in_verse.append(f)
                if not in_verse:
                    continue
                # Pick the strongest tag observed (STRONG > REVIEW)
                tags = {f.get("tag") or f.get("severity") or "" for f in in_verse}
                if STRONG_TAGS & tags:
                    current_tag = sorted(STRONG_TAGS & tags)[0]
                elif REVIEW_TAGS & tags:
                    current_tag = "REVIEW-REQUIRED"
                else:
                    continue  # any non-classified tag → skip
                # Use the brief from the first matching finding
                brief = (in_verse[0].get("brief") or in_verse[0].get("annotation") or "")[:120].replace("\t", " ").replace("\n", " ")
                rows.append(f"{book}/{vref}\t{vname}\t{current_tag}\t{brief}\t\t")

    return rows


def write_fixture_template(out_path: Path) -> int:
    samples = sample_all_clusters()
    rows = fixture_template_rows(samples)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    n_verses = sum(len(v) for v in samples.values())
    n_rows = len(rows) - 1  # minus header
    n_validators = len([f for f in VALIDATORS_DIR.glob("syntax/validate_*.py")] +
                       [f for f in VALIDATORS_DIR.glob("colometry/validate_*.py")])
    print(
        f"Sampled {n_verses} verses across {len(CLUSTERS)} clusters; "
        f"after filtering to active findings, emitted {n_rows} fixture rows "
        f"({n_validators} validators evaluated) to {out_path.relative_to(REPO_ROOT)}.",
        file=sys.stderr,
    )
    return n_verses


def load_fixture(fixture_path: Path) -> list[dict]:
    """Parse the labeled fixture TSV into a list of row dicts.

    Schema (6 columns; old 4-column schema also accepted):
      verse_id, validator_name, current_tag, current_brief, expected_action, rationale_brief

    Skips header row and any row with empty expected_action (unlabeled).
    """
    rows: list[dict] = []
    if not fixture_path.exists():
        return rows
    text = fixture_path.read_text(encoding="utf-8")
    header_parts: list[str] = []
    for i, line in enumerate(text.splitlines()):
        if i == 0:
            header_parts = line.split("\t")
            continue
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        verse_id, validator_name = parts[0], parts[1]
        # Detect 6-col vs 4-col schema by header
        if len(header_parts) >= 6 and header_parts[2] == "current_tag":
            current_tag = parts[2] if len(parts) > 2 else ""
            expected = (parts[4] if len(parts) > 4 else "").strip().upper()
            rationale = parts[5] if len(parts) > 5 else ""
        else:
            current_tag = ""
            expected = parts[2].strip().upper()
            rationale = parts[3] if len(parts) > 3 else ""
        if expected not in ("APPLY", "REVIEW", "REJECT"):
            continue  # skip unlabeled rows
        rows.append({
            "verse_id": verse_id,
            "validator_name": validator_name,
            "current_tag": current_tag,
            "expected_action": expected,
            "rationale": rationale,
        })
    return rows


# ---------------------------------------------------------------------------
# Validator invocation
# ---------------------------------------------------------------------------

def validator_path(validator_name: str) -> Path | None:
    for layer in ("syntax", "colometry"):
        p = VALIDATORS_DIR / layer / f"{validator_name}.py"
        if p.exists():
            return p
    return None


def run_validator_for_book(validator_name: str, book: str) -> list[dict]:
    """Invoke a single validator with --json --v2 --book <book>.

    Returns parsed findings list (empty on any failure).
    """
    vp = validator_path(validator_name)
    if vp is None:
        return []
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    cmd = [sys.executable, str(vp), "--json", "--v2", "--book", book]
    try:
        proc = subprocess.run(
            cmd, cwd=REPO_ROOT, capture_output=True,
            text=True, encoding="utf-8", errors="replace",
            timeout=120, env=env,
        )
    except subprocess.TimeoutExpired:
        return []
    if not proc.stdout.strip():
        return []
    try:
        doc = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    return doc.get("findings", []) or []


# ---------------------------------------------------------------------------
# Verse ↔ line mapping
# ---------------------------------------------------------------------------

def chapter_filename_pattern(book: str, chapter_num: int) -> str:
    """Return the relative chapter filename pattern, e.g. 'genesis-08.txt'.

    Used to filter findings (which come back per-book) down to a specific
    chapter — without this filter, a finding at line N of chapter X gets
    incorrectly attributed to a verse at line N of chapter Y.
    """
    book_short = book.split("-", 1)[1] if "-" in book else book
    return f"{book_short}-{chapter_num:02d}.txt"


def finding_in_chapter(f: dict, book: str, chapter_num: int) -> bool:
    """True if finding's file path matches the (book, chapter)."""
    fp = (f.get("file") or "").replace("\\", "/")
    return chapter_filename_pattern(book, chapter_num) in fp


def chapter_verse_line_map(book: str, chapter_num: int) -> dict[str, tuple[int, int]]:
    """Return {verse_ref: (start_line, end_line)} (1-indexed, inclusive) for
    the chapter's content lines following each verse marker."""
    bdir = V2_HE_DIR / book
    chapter_files = list(bdir.glob(f"*-{chapter_num:02d}.txt"))
    if not chapter_files:
        return {}
    text = chapter_files[0].read_text(encoding="utf-8")
    lines = text.splitlines()
    out: dict[str, tuple[int, int]] = {}
    cur_verse: str | None = None
    cur_start: int | None = None
    for i, line in enumerate(lines, start=1):
        s = line.strip()
        if _VERSE_REF_RE.match(s):
            if cur_verse is not None and cur_start is not None:
                out[cur_verse] = (cur_start, i - 1)
            cur_verse = s
            cur_start = i + 1
    if cur_verse is not None and cur_start is not None:
        out[cur_verse] = (cur_start, len(lines))
    return out


# ---------------------------------------------------------------------------
# Action classification
# ---------------------------------------------------------------------------

STRONG_TAGS = {"STRONG-MERGE-CANDIDATE", "STRONG-SPLIT-CANDIDATE"}
REVIEW_TAGS = {"REVIEW-REQUIRED"}


def actual_action_for(findings: list[dict], book: str, chapter: int, verse: str) -> str:
    """Classify the validator's actual decision on the (book, chapter, verse).

    Returns 'STRONG' if any finding emits a STRONG-* tag in this verse;
    'REVIEW' if any REVIEW-REQUIRED finding; 'NONE' otherwise.

    Filters findings by file path FIRST so a finding at line N of one chapter
    isn't matched to a verse at line N of a different chapter.
    """
    line_map = chapter_verse_line_map(book, chapter)
    if verse not in line_map:
        return "NONE"
    start, end = line_map[verse]
    has_strong = False
    has_review = False
    for f in findings:
        if not finding_in_chapter(f, book, chapter):
            continue
        line = f.get("line") or f.get("line_num")
        if not isinstance(line, int):
            continue
        if not (start <= line <= end):
            continue
        tag = f.get("tag") or f.get("severity") or ""
        if tag in STRONG_TAGS:
            has_strong = True
        elif tag in REVIEW_TAGS:
            has_review = True
    if has_strong:
        return "STRONG"
    if has_review:
        return "REVIEW"
    return "NONE"


# ---------------------------------------------------------------------------
# Measure mode
# ---------------------------------------------------------------------------

def measure(fixture_rows: list[dict], validator_filter: str | None = None) -> dict:
    """Run validators per book + compare against ground-truth labels.

    Returns the output document destined for validators/.fp-baseline.json.
    """
    if validator_filter:
        fixture_rows = [r for r in fixture_rows if r["validator_name"] == validator_filter]

    # Group fixture rows by (validator, book) so we batch validator invocations.
    by_validator_book: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in fixture_rows:
        verse_id = row["verse_id"]
        if "/" not in verse_id:
            continue
        book, vref = verse_id.split("/", 1)
        if ":" not in vref:
            continue
        try:
            ch_str, _ = vref.split(":", 1)
            ch = int(ch_str)
        except ValueError:
            continue
        row["_book"] = book
        row["_chapter"] = ch
        row["_verse_ref"] = vref
        by_validator_book[(row["validator_name"], book)].append(row)

    # Per-validator counters
    counters: dict[str, dict] = defaultdict(lambda: {
        "tp": 0, "fp": 0, "fn": 0,
        "uncalibrated": 0, "tn": 0, "review_correct": 0,
        "labeled_total": 0,
    })

    # Cache (validator, book) → findings to avoid re-invoking
    findings_cache: dict[tuple[str, str], list[dict]] = {}

    n_total = len(fixture_rows)
    n_done = 0
    print(f"Measuring {n_total} labeled fixture rows ...", file=sys.stderr)

    for (vname, book), rows in by_validator_book.items():
        key = (vname, book)
        if key not in findings_cache:
            findings_cache[key] = run_validator_for_book(vname, book)
        findings = findings_cache[key]

        for row in rows:
            n_done += 1
            actual = actual_action_for(findings, row["_book"], row["_chapter"], row["_verse_ref"])
            expected = row["expected_action"]
            c = counters[vname]
            c["labeled_total"] += 1

            if actual == "STRONG":
                if expected == "APPLY":
                    c["tp"] += 1
                elif expected == "REJECT":
                    c["fp"] += 1
                elif expected == "REVIEW":
                    c["uncalibrated"] += 1
            elif actual == "REVIEW":
                if expected == "APPLY":
                    c["fn"] += 1
                elif expected == "REJECT":
                    c["tn"] += 1
                elif expected == "REVIEW":
                    c["review_correct"] += 1
            else:  # NONE
                if expected == "APPLY":
                    c["fn"] += 1
                elif expected == "REJECT":
                    c["tn"] += 1
                # REVIEW + NONE = no signal, ignored

    # Compute rates
    out_validators: dict[str, dict] = {}
    for vname, c in counters.items():
        tp_denom = c["tp"] + c["fn"]
        fp_denom = c["fp"] + c["tn"]
        out_validators[vname] = dict(c)
        out_validators[vname]["tp_rate"] = c["tp"] / tp_denom if tp_denom else None
        out_validators[vname]["fp_rate"] = c["fp"] / fp_denom if fp_denom else None

    gt_summary = {"APPLY": 0, "REVIEW": 0, "REJECT": 0}
    for r in fixture_rows:
        if r["expected_action"] in gt_summary:
            gt_summary[r["expected_action"]] += 1

    return {
        "fixture_count": len({r["verse_id"] for r in fixture_rows}),
        "labeled_count": n_total,
        "validators": out_validators,
        "ground_truth_summary": gt_summary,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sample", action="store_true", help="emit fixture template TSV")
    mode.add_argument("--measure", action="store_true", help="measure FP rates against labeled fixture")
    p.add_argument("--fixture", type=Path, default=FIXTURE_FILE, help="path to fixture TSV (default: tests/fp-baseline-fixtures.tsv)")
    p.add_argument("--output", type=Path, default=OUTPUT_FILE, help="path to output JSON (default: validators/.fp-baseline.json)")
    p.add_argument("--validator", default=None, help="restrict --measure to a single validator")
    args = p.parse_args()

    if args.sample:
        if args.fixture.exists():
            print(
                f"ERROR: {args.fixture.relative_to(REPO_ROOT)} already exists; "
                f"refusing to overwrite. Move it aside if you want to re-sample.",
                file=sys.stderr,
            )
            return 2
        write_fixture_template(args.fixture)
        return 0

    if args.measure:
        rows = load_fixture(args.fixture)
        if not rows:
            print(
                f"ERROR: no labeled rows in {args.fixture.relative_to(REPO_ROOT)}. "
                f"Either the file doesn't exist or no row has expected_action set "
                f"to APPLY / REVIEW / REJECT. Generate template with --sample, "
                f"then label the rows that need review.",
                file=sys.stderr,
            )
            return 2
        doc = measure(rows, validator_filter=args.validator)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        # Concise summary to stderr (counts go in commit messages, not status reports per CLAUDE.md)
        n_validators = len(doc["validators"])
        labeled = doc["labeled_count"]
        gt = doc["ground_truth_summary"]
        print(
            f"Measured {labeled} labeled fixture rows across {n_validators} validators; "
            f"ground-truth: APPLY={gt['APPLY']} REVIEW={gt['REVIEW']} REJECT={gt['REJECT']}; "
            f"output {args.output.relative_to(REPO_ROOT)}.",
            file=sys.stderr,
        )
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
