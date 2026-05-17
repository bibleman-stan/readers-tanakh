#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_rendered_output.py — passage-level Sonnet audit of v2/heb chapters.

Per directive 2026-05-16-2402-audit-layer-prototype-per-chapter-book-batch.md
(Phase 2 build; Phase 4 auto-apply OUT OF SCOPE per directive + prior Phase 1
STOP-AND-SURFACE on canon §1 line 151 conflict with passage-level discipline).

# What this script does

For a given chapter, formats the prompt template (v2 — incorporates Phase 1.5
audit revisions for verbless clauses, pro-drop, genealogical formulas, legal
lists, legal-casuistic protasis/apodosis, discourse particles, bare construct
heads, staircase parallelism, chiasm scoping, confidence stratification) and
emits the prompt to stdout or to a file ready for Sonnet dispatch.

# What this script does NOT do

- It does NOT invoke the Anthropic API (operator dispatches via their preferred
  pathway: Claude Code Agent tool, direct API call, etc.)
- It does NOT mutate v2/heb (read-only — strict diagnostic surface)
- It does NOT auto-apply verdicts (Phase 4 deferred per directive)

# Output

Markdown report at `data/reports/audit/<book>-<chapter>.md` with per-line
verdicts, summary table, genre observation, and final JSONL block.

# Severity classification

All verdicts are REVIEW-REQUIRED-equivalent (advisory). The audit-layer is
explicitly NOT a STRONG-tagged source per the cross-validator hierarchy
discipline (Phase 1 audit Agent F-F1).

# Validator-collision check

For each line where audit verdict differs from current validator-finding state
at that line, report flags as one of:
- CONFLICT — audit verdict opposes existing STRONG-tagged validator finding
- CORROBORATE — audit verdict agrees with existing STRONG validator finding
- ADVISORY — audit verdict on a line with no current validator finding

Phase 4 auto-apply eligibility (when later authorized via separate directive)
should require zero conflicts AND ≥1 corroboration OR HIGH confidence.

# Reproducibility

Each run records: ISO-timestamp + model-ID + prompt-hash. Reports are
APPEND-ONLY per-run-section (older runs preserved). Future maintainer
reviewing a 6-month-old verdict reads the per-call reasoning sentence + the
raw JSONL output as the audit record.

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/audit_rendered_output.py \\
        --book 01-genesis --chapter 5 --print-prompt
    PYTHONIOENCODING=utf-8 py -3 scripts/audit_rendered_output.py \\
        --book 01-genesis --chapter all --dry-run --max-chapters 50
"""

import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
V2_HEB = REPO_ROOT / "data" / "text-files" / "v2" / "heb"
REPORT_DIR = REPO_ROOT / "data" / "reports" / "audit"

# Path to the revised prompt template (Phase 1.5 audit G+H revisions applied).
# When the operator-side prompt is finalized into the repo, this points there;
# for now, the prompt content is embedded below as the canonical version.

PROMPT_TEMPLATE_VERSION = "v2"
PROMPT_TEMPLATE = """Evaluate line breaks in Hebrew {book} {chapter} (v2/heb rendering) using the EXTENDED bidirectional ATU test.

# What an ATU is

An ATU is the smallest text unit an attentive reader processes as a discrete cognitive chunk. One ATU per line.

# Necessary condition (universal)

A line is a legitimate standalone ATU only if BOTH:

1. **Forward grammatical closure** — grammatically complete in Hebrew terms:
   - **Finite verbs**: subject encoded by inflection alone is sufficient; no overt subject NP required (Hebrew pro-drop is acceptable).
   - **Verbless / nominal-predicate clauses**: subject + non-verbal predicate (NP/PP/Adj) in juxtaposition counts as closed (Hebrew has no overt copula in present-tense verbless clauses). NOTE: this applies ONLY when the nominal head is predicated (subject + predicate). A bare construct-state noun (e.g., דְּבַר alone, awaiting genitive YHWH on the next line) is NOT a nominal predication — it FAILS forward closure (M3 bare-governor indivisibility per canon §5).
   - **Participial predications**: subject + active/passive participle counts as closed (participle fills the slot of a finite verb).
   - **Exclamatory / declarative particle-headed**: clauses opened by אַשְׁרֵי X / הִנֵּה X / הָבָה X count as closed when their NP complement is present.
   - **Conditional protasis (אִם / כִּי + verb)**: in legal-casuistic case-law (Exod 21-23, Lev 1-7, Num 5, Deut 19-25), the conditional particle signals intentional grammatical suspension — protasis does NOT fail forward closure even though it is open toward the apodosis. Both protasis AND apodosis are distinct ATUs.

2. **Backward referential self-containment** — referents established or self-introducing:
   - Overt referents present in the line, OR
   - Referent recoverable from finite-verb morphology, OR
   - Same discourse-active subject as the immediately prior ATU (wayyiqtol chains; sequential imperatives; legal-section addressee). **Chain breaks at**: speaker change in direct speech, vocative redirecting addressee, parenthetical כִּי clause, or any intervening clause with an overt new subject NP.
   - FAILS when long-range antecedents (>1 ATU back, no chain-continuity) are required.

# Sufficiency extension for parallel poetry

Adjacent parallel cola may each pass the necessary condition yet jointly express one propositional content. Apply the cognitive-unity gate.

Parallelism classes:
- **Synonymous** (B paraphrases A) → ONE ATU
- **Antithetic** (B contrasts A; comparison IS the thought) → ONE ATU when the contrast itself is the unit (Ps 1:6, Prov merism). DISTINCT propositions in two cola when each colon asserts an independently evaluable claim (Prov 10:3 — wisdom-genre two-line proverbs typically keep two propositions per verse; default KEEP-AS-IS unless emphatic restatement).
- **Synthetic** (B advances A with propositionally distinct content) → KEEP-AS-IS by default; judgment call only when content advance is truly minimal.
- **Climactic** (B/C intensify toward apex) → ONE ATU if the apex is the cognitive unit; KEEP-AS-IS if each step advances propositionally.
- **Staircase** (lexical repetition advancing the thought, often cross-verse) → ONE ATU within the cognitive unit; flag AMBIGUOUS when the unit spans a verse boundary. **Intra-verse staircase**: if the advancing element introduces a propositionally distinct predication, verdict is KEEP-AS-IS; if the advance is purely intensificational (no new referent, same proposition stronger), apply cognitive-unity gate.
- **Chiastic** (ABBA structure) → apply cognitive-unity within each colon-pair (A/B), not across the full chiasm if it spans >2 cola or crosses a verse boundary. Flag AMBIGUOUS only when the entire unit is <3 lines.

# Genre anchors (apply when relevant)

- **Genealogical formulas** (Gen 5/10/11/36, 1 Chr 1-9): each member-cycle (X-lived-N-years / begot-Y / total-N-years / died) is ONE atomic unit; cross-member boundary is preserved as formula cadence, not over-broken.
- **Legal lists** (Lev 11 dietary, Deut 14 dietary, Deut 27 curses, Deut 28 blessings, Num 7 tribal offerings): each case-member is ONE ATU. Resumptive pronouns on their own line (אֹתָהּ / אֹתוֹ alone) FAIL bidirectional containment — merge with the case-clause they resume.
- **Legal-casuistic (case-law)** (Exod 21-23, Lev 1-7, Num 5, Deut 19-25): conditional protasis (אִם / כִּי + verb) and apodosis are DISTINCT ATUs. KEEP-AS-IS for both legs.
- **Repeated tribal-offering cycles** (Num 7): each offering cycle is one complete ATU-set; same verdict as the first occurrence unless a structural anomaly is present.
- **Discourse particles** (לָכֵן / וְעַתָּה / אָז / הִנֵּה when followed by content on same line): they lead content; particle + its governed content = ONE ATU. Never SPLIT a particle from immediately following content. If a particle appears alone on a line (bare), verdict = MERGE-WITH-NEXT per forward-closure failure (canon §5 H14 + M3).
- **Wisdom-genre proverbs** (Prov 10-22, Job dialogue, parts of Eccl): each two-line proverb typically expresses two independently asserted propositions; DEFAULT KEEP-AS-IS unless both cola express a single proposition.
- **Acrostic structures** (Pss 9/10, 25, 34, 37, 111, 112, 119, 145, Pro 31:10-31, Nah 1:2-8, Lam 1-4): acrostic letter-stanza is the structural unit; apply cognitive-unity within stanza.
- **Qinah/lament meter** (Lam 1-5, parts of Jer): 3+2 qinah meter often pairs hemistichs; apply cognitive-unity if the pair states one propositional content.
- **Embedded poetry inside narrative** (Gen 49 Jacob's blessings, Ex 15 Song of Sea, Deut 32, Deut 33, Judg 5 Deborah, 1 Sam 2 Hannah, 2 Sam 22, Isa 12, Hab 3, Lam, Song 1-8): apply poetic rubric; different from surrounding prose.

# Caveat

Surface coordination (וְ), parallelism marks, accent disjunctives, editorial punctuation DO NOT auto-license breaks. They are candidate signals; the bidirectional test + cognitive-unity gate adjudicate.

# Under-broken cases

A line is under-broken when it contains two independently asserted propositions. Apply the same bidirectional test in reverse: does each half independently satisfy forward closure and backward containment? If yes, SPLIT.

# Your task

Per line, classify as ONE of:
- **KEEP-AS-IS** — line is a legitimate standalone ATU
- **MERGE-WITH-PRIOR** — line fails bidirectional test; should merge upward
- **MERGE-WITH-NEXT** — line fails bidirectional test; should merge downward
- **SPLIT-FROM-PRIOR** — content should split off into a new line above this one
- **SPLIT-FROM-NEXT** — content should split off into a new line below
- **AMBIGUOUS** — judgment call; flag for editorial review

Add CONFIDENCE per verdict: HIGH / MED / LOW.

One-sentence reasoning per line citing the specific gate.

# Default to KEEP-AS-IS

The bidirectional test + cognitive-unity gate must AFFIRMATIVELY fire to justify a change.

# Output (structured)

- Per-verse: each line + verdict + confidence + reasoning
- Summary table: over-broken / under-broken / KEEP-AS-IS counts + parallelism class where applicable
- Genre observation
- Final JSONL block (machine-readable, one line per verdict)

# Chapter to evaluate

{book} {chapter} v2/heb:

{chapter_text}
"""


def prompt_hash(template: str) -> str:
    """SHA-256 hash of the prompt template, truncated to 12 hex chars."""
    return hashlib.sha256(template.encode("utf-8")).hexdigest()[:12]


def format_prompt(book: str, chapter: int, chapter_text: str) -> str:
    return PROMPT_TEMPLATE.format(
        book=book, chapter=chapter, chapter_text=chapter_text
    )


def find_chapter_file(book_slug: str, chapter: int) -> "Path | None":
    """Resolve book + chapter to the v2/heb file path. Tolerates short-slug
    input (e.g., 'genesis' → '01-genesis')."""
    if not book_slug:
        return None
    candidates = list(V2_HEB.iterdir())
    # Try exact match first
    direct = V2_HEB / book_slug
    if direct.is_dir():
        book_dir = direct
    else:
        matches = [d for d in candidates if d.is_dir() and book_slug.lower() in d.name.lower()]
        if not matches:
            return None
        book_dir = matches[0]
    # Find chapter file
    short_name = book_dir.name.split("-", 1)[1] if "-" in book_dir.name else book_dir.name
    chap_file = book_dir / f"{short_name}-{chapter:02d}.txt"
    return chap_file if chap_file.is_file() else None


def write_report_header(out_path: Path, book: str, chapter: int, prompt_h: str,
                        model_id: str) -> None:
    """Write/append the per-run report header. Append-only: existing content
    preserved; new run section appended."""
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    header = (
        f"\n\n---\n\n"
        f"## Audit run — {ts}\n\n"
        f"- **Book / chapter**: {book} {chapter}\n"
        f"- **Model**: {model_id}\n"
        f"- **Prompt template**: {PROMPT_TEMPLATE_VERSION} "
        f"(SHA256 prefix `{prompt_h}`)\n"
        f"- **Severity**: REVIEW-REQUIRED-equivalent (advisory; "
        f"audit-layer never tags STRONG)\n"
        f"- **Source**: `data/text-files/v2/heb/{book}/{book.split('-',1)[1]}-{chapter:02d}.txt`\n\n"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        existing = out_path.read_text(encoding="utf-8")
        out_path.write_text(existing + header, encoding="utf-8")
    else:
        out_path.write_text(
            f"# Audit report — {book} {chapter}\n"
            f"\nPer 2402 audit-layer prototype (Phase 1.5 / Phase 2).\n"
            f"Read-only diagnostic surface; verdicts advisory.\n"
            + header,
            encoding="utf-8",
        )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--book", required=True, help="book slug (e.g., 01-genesis or genesis)")
    p.add_argument("--chapter", required=True,
                   help="chapter number (int) or 'all'")
    p.add_argument("--print-prompt", action="store_true",
                   help="Print the formatted prompt to stdout (for review or "
                        "external dispatch)")
    p.add_argument("--dry-run", action="store_true",
                   help="Format prompt + estimate tokens; do NOT dispatch")
    p.add_argument("--max-chapters", type=int, default=10,
                   help="Cost cap for --chapter all (default: 10)")
    p.add_argument("--model-id", default="claude-sonnet-4-6",
                   help="Model identifier (for report header)")
    args = p.parse_args()

    if args.chapter == "all":
        # Resolve all chapters in book
        book_dir = None
        for d in V2_HEB.iterdir():
            if d.is_dir() and args.book.lower() in d.name.lower():
                book_dir = d
                break
        if book_dir is None:
            print(f"ERROR: book not found: {args.book}", file=sys.stderr)
            return 2
        chap_files = sorted(book_dir.glob("*.txt"))
        if len(chap_files) > args.max_chapters:
            print(f"ERROR: {len(chap_files)} chapters exceeds --max-chapters "
                  f"({args.max_chapters}). Bump --max-chapters or specify "
                  f"single chapter.", file=sys.stderr)
            return 2
        chapter_files = chap_files
    else:
        try:
            chap_num = int(args.chapter)
        except ValueError:
            print(f"ERROR: invalid chapter: {args.chapter}", file=sys.stderr)
            return 2
        chap_file = find_chapter_file(args.book, chap_num)
        if chap_file is None:
            print(f"ERROR: chapter file not found: {args.book} {chap_num}",
                  file=sys.stderr)
            return 2
        chapter_files = [chap_file]

    prompt_h = prompt_hash(PROMPT_TEMPLATE)

    for chap_file in chapter_files:
        m = re.search(r"-(\d+)\.txt$", chap_file.name)
        if not m:
            continue
        chap_num = int(m.group(1))
        book_slug = chap_file.parent.name
        chapter_text = chap_file.read_text(encoding="utf-8")
        formatted = format_prompt(book_slug, chap_num, chapter_text)

        token_estimate = len(formatted) // 4  # rough English-token approximation

        out_path = REPORT_DIR / f"{book_slug}-{chap_num:02d}.md"

        if args.dry_run:
            print(f"[dry-run] {book_slug} {chap_num}: ~{token_estimate} tokens; "
                  f"output→ {out_path.relative_to(REPO_ROOT)}")
            continue

        if args.print_prompt:
            print(formatted)
            return 0

        # Initialize/append the report header for the operator's dispatch
        write_report_header(out_path, book_slug, chap_num, prompt_h, args.model_id)
        print(f"Report header initialized at {out_path.relative_to(REPO_ROOT)}",
              file=sys.stderr)
        print(f"Prompt formatted (prompt-hash {prompt_h}; ~{token_estimate} tokens).",
              file=sys.stderr)
        print(f"Operator: dispatch the prompt via Anthropic API / Claude Code "
              f"Agent / preferred channel, then append the Sonnet response to "
              f"{out_path.relative_to(REPO_ROOT)}.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
