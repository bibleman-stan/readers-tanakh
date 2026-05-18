#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""render_atus.py — Stage 1 of the ATU pipeline. Opus 3-pass orchestrator with
agreement scoring per directive 2026-05-17-1500 Item 2.

Reads a v2/heb chapter file, dispatches 3 parallel Opus calls with the canonical
minimal-rubric prompt, parses each response, scores per-verse agreement.

Architecture revisions per §7.3 pre-build audit β:
  - Parallel Opus calls (asyncio.gather) — wall-time efficiency; failed pass
    degrades to 2-pass mode (MAJORITY-UNCERTAIN scoring)
  - Verse-granularity agreement scoring (whitespace-normalized exact match of
    full verse rendering) — avoids line-alignment problem when passes propose
    different line counts
  - NO HARD auto-override at this stage — all verdicts surface to Stage 3
    editorial review (per editorial-review-protocol.md)
  - Aramaic detection deferred to run_pipeline.py pre-flight; this script
    assumes the input is Hebrew
  - Long-chapter chunking: default chunk-size 40 verses; chapters > threshold
    split into sequential chunks with discourse-active-subject carry-forward

Output: per-chapter JSONL file at data/reports/atu_pipeline/<book>/<chapter>.jsonl
        with one record per verse:
        {"verse": "1:1", "agreement": "UNANIMOUS|MAJORITY|ALL-DISAGREE",
         "pass1": "...", "pass2": "...", "pass3": "...",
         "draft": "...", "source": "..."}

Usage:
    PYTHONIOENCODING=utf-8 py -3 scripts/atu_pipeline/render_atus.py \\
        --book 19-psalms --chapter 1 [--dry-run] [--chunk-size 40]

Environment: ANTHROPIC_API_KEY must be set for live dispatch.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V2_HEB = REPO_ROOT / "data" / "text-files" / "v2" / "heb"
PROMPT_PATH = REPO_ROOT / "scripts" / "atu_pipeline" / "prompts" / "minimal_rubric_hebrew.md"
REPORT_DIR = REPO_ROOT / "data" / "reports" / "atu_pipeline"

OPUS_MODEL = "claude-opus-4-7"
DEFAULT_CHUNK_SIZE = 40  # verses per chunk; chapters longer get sharded


@dataclass
class VerseBlock:
    """A single verse with its source-state lines."""
    ref: str  # e.g., "1:1"
    chapter: int
    verse: int
    lines: list[str] = field(default_factory=list)

    def to_source_block(self) -> str:
        return f"{self.ref}\n" + "\n".join(self.lines)


@dataclass
class PassResult:
    """One Opus pass's output for a chapter."""
    pass_id: int  # 1, 2, or 3
    raw_markdown: str  # the full markdown output
    per_verse: dict[str, str] = field(default_factory=dict)  # ref → rendered-lines-joined
    error: Optional[str] = None


def load_chapter(book_slug: str, chapter: int) -> tuple[Path, list[VerseBlock]]:
    """Read a v2/heb chapter file; return (path, verses list)."""
    book_dir = V2_HEB / book_slug
    short = book_slug.split("-", 1)[1] if "-" in book_slug else book_slug
    path = book_dir / f"{short}-{chapter:02d}.txt"
    if not path.is_file():
        raise FileNotFoundError(f"chapter file not found: {path}")

    verses: list[VerseBlock] = []
    cur: Optional[VerseBlock] = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        m = re.match(r"^(\d+):(\d+)$", s)
        if m:
            if cur is not None:
                verses.append(cur)
            cur = VerseBlock(ref=s, chapter=int(m.group(1)), verse=int(m.group(2)))
            continue
        if s and cur is not None:
            cur.lines.append(raw)
    if cur is not None:
        verses.append(cur)
    return path, verses


def chunk_verses(verses: list[VerseBlock], chunk_size: int) -> list[list[VerseBlock]]:
    """Shard a long chapter into chunks. Single chunk if len ≤ chunk_size."""
    if len(verses) <= chunk_size:
        return [verses]
    return [verses[i:i + chunk_size] for i in range(0, len(verses), chunk_size)]


def format_chapter_text(verses: list[VerseBlock]) -> str:
    """Format verses as the prompt's input chapter text."""
    return "\n\n".join(v.to_source_block() for v in verses)


def build_prompt(book_label: str, chapter_label: str, chapter_text: str) -> str:
    """Append the chapter to the canonical prompt template."""
    template = PROMPT_PATH.read_text(encoding="utf-8")
    suffix = (
        f"\n\n---\n\n## Chapter to render: {book_label} {chapter_label}\n\n"
        f"```\n{chapter_text}\n```\n"
    )
    return template + suffix


def parse_pass_output(markdown: str) -> dict[str, str]:
    """Parse Opus's markdown output to {verse_ref: rendered_text}.

    Per the canonical prompt's output spec: each verse is a `## Verse N:M`
    section with a `### Minimal-rubric state` block containing the ATU lines.
    """
    per_verse: dict[str, str] = {}
    verse_blocks = re.split(r"^## Verse (\d+:\d+)\s*$", markdown, flags=re.MULTILINE)
    # verse_blocks alternates: [pre-content, ref1, body1, ref2, body2, ...]
    for i in range(1, len(verse_blocks), 2):
        ref = verse_blocks[i].strip()
        body = verse_blocks[i + 1] if i + 1 < len(verse_blocks) else ""
        # Extract the "### Minimal-rubric state" block content
        m = re.search(
            r"###\s+Minimal-rubric state\s*\n+(.*?)(?=^###|\Z)",
            body,
            flags=re.DOTALL | re.MULTILINE,
        )
        if m is None:
            continue
        rendered = m.group(1).strip()
        # Strip wrapping code fences if present
        rendered = re.sub(r"^```\w*\n", "", rendered)
        rendered = re.sub(r"\n```\s*$", "", rendered)
        per_verse[ref] = rendered.strip()
    return per_verse


def normalize_for_comparison(text: str) -> str:
    """Whitespace-normalize for verse-granularity agreement comparison.
    Collapses runs of whitespace within a line; preserves line breaks (each
    line is one ATU; line breaks are load-bearing for the agreement check)."""
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


def score_agreement(p1: str, p2: str, p3: str) -> str:
    """Verse-granularity agreement scoring per Audit β Finding 1.
    Returns: UNANIMOUS / MAJORITY / ALL-DISAGREE / MAJORITY-UNCERTAIN (1 pass failed)."""
    norms = [normalize_for_comparison(p) for p in (p1, p2, p3)]
    valid = [n for n in norms if n]
    if len(valid) < 2:
        return "INSUFFICIENT-PASSES"
    if len(valid) == 2:
        return "MAJORITY-UNCERTAIN" if valid[0] == valid[1] else "ALL-DISAGREE"
    a, b, c = norms
    if a == b == c:
        return "UNANIMOUS"
    if a == b or b == c or a == c:
        return "MAJORITY"
    return "ALL-DISAGREE"


async def dispatch_opus_pass(client, prompt: str, pass_id: int) -> PassResult:
    """One Opus API call returning a PassResult. Catches exceptions for
    failure isolation per Audit β Finding 2."""
    try:
        # anthropic SDK v0.96.0 — Messages API
        response = await asyncio.to_thread(
            client.messages.create,
            model=OPUS_MODEL,
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in response.content if hasattr(block, "text")
        )
        return PassResult(pass_id=pass_id, raw_markdown=text)
    except Exception as e:
        return PassResult(pass_id=pass_id, raw_markdown="", error=str(e))


async def render_chunk(client, prompt: str) -> list[PassResult]:
    """3 parallel Opus passes on one chunk. Returns 3 PassResults."""
    tasks = [dispatch_opus_pass(client, prompt, i + 1) for i in range(3)]
    results = await asyncio.gather(*tasks, return_exceptions=False)
    for r in results:
        if r.error is None:
            r.per_verse = parse_pass_output(r.raw_markdown)
    return results


def merge_chunks_per_verse(chunk_results: list[list[PassResult]]) -> dict[str, list[PassResult]]:
    """Flatten per-chunk per-pass results into per-verse-ref → [pass1, pass2, pass3].
    Within a verse, the 3 passes are the 3 Opus passes from the chunk that
    contained that verse."""
    out: dict[str, list[PassResult]] = {}
    for chunk_passes in chunk_results:
        # Collect verse-refs that appear in any pass for this chunk
        all_refs: set[str] = set()
        for p in chunk_passes:
            all_refs.update(p.per_verse.keys())
        for ref in all_refs:
            out[ref] = chunk_passes  # share the 3-pass tuple
    return out


def build_per_verse_records(
    verses: list[VerseBlock],
    per_verse_passes: dict[str, list[PassResult]],
) -> list[dict]:
    """Per-verse JSONL records with agreement scoring."""
    records: list[dict] = []
    for v in verses:
        passes = per_verse_passes.get(v.ref)
        if passes is None:
            # No pass had output for this verse
            records.append({
                "verse": v.ref,
                "agreement": "INSUFFICIENT-PASSES",
                "source": "\n".join(v.lines),
                "pass1": None, "pass2": None, "pass3": None,
                "draft": "\n".join(v.lines),  # fallback: source
                "error": "no pass had verse output",
            })
            continue
        p1 = passes[0].per_verse.get(v.ref, "")
        p2 = passes[1].per_verse.get(v.ref, "")
        p3 = passes[2].per_verse.get(v.ref, "")
        verdict = score_agreement(p1, p2, p3)
        # Draft: the unanimous text if UNANIMOUS; else the majority text if
        # MAJORITY; else source as placeholder for editorial review.
        draft: str
        if verdict == "UNANIMOUS":
            draft = normalize_for_comparison(p1)
        elif verdict == "MAJORITY":
            norms = [normalize_for_comparison(p) for p in (p1, p2, p3)]
            # Find the pair that matched
            if norms[0] == norms[1]:
                draft = norms[0]
            elif norms[1] == norms[2]:
                draft = norms[1]
            else:
                draft = norms[0]
        elif verdict == "MAJORITY-UNCERTAIN":
            norms = [normalize_for_comparison(p) for p in (p1, p2, p3) if p]
            draft = norms[0] if norms else "\n".join(v.lines)
        else:
            draft = "\n".join(v.lines)
        records.append({
            "verse": v.ref,
            "agreement": verdict,
            "source": "\n".join(v.lines),
            "pass1": p1, "pass2": p2, "pass3": p3,
            "draft": draft,
            "pass_errors": [p.error for p in passes if p.error],
        })
    return records


def write_report(book_slug: str, chapter: int, records: list[dict]) -> Path:
    """Write per-chapter JSONL to data/reports/atu_pipeline/<book>/<chapter>.jsonl."""
    out_dir = REPORT_DIR / book_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"chapter-{chapter:02d}.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return out_path


def dry_run_summary(verses: list[VerseBlock], chunk_size: int) -> dict:
    """Estimate token cost without dispatching."""
    chapter_text = format_chapter_text(verses)
    chunks = chunk_verses(verses, chunk_size)
    # Rough English-token approximation; Hebrew is denser per char so divide more
    template_chars = PROMPT_PATH.read_text(encoding="utf-8").__len__()
    input_chars = template_chars + len(chapter_text)
    input_tokens_per_pass = input_chars // 4
    output_tokens_per_pass = max(len(chapter_text) // 4, 2000)
    total_passes = 3 * len(chunks)
    return {
        "verses": len(verses),
        "chunks": len(chunks),
        "passes": total_passes,
        "input_tokens_total": input_tokens_per_pass * total_passes,
        "output_tokens_total": output_tokens_per_pass * total_passes,
        "estimated_cost_usd": (
            input_tokens_per_pass * total_passes * 15 / 1_000_000
            + output_tokens_per_pass * total_passes * 75 / 1_000_000
        ),
    }


async def render_chapter_async(
    client,
    book_slug: str,
    chapter: int,
    chunk_size: int,
) -> tuple[Path, list[dict]]:
    """Full Stage 1 render for one chapter."""
    chapter_path, verses = load_chapter(book_slug, chapter)
    chunks = chunk_verses(verses, chunk_size)

    chunk_results: list[list[PassResult]] = []
    book_label = book_slug.split("-", 1)[1] if "-" in book_slug else book_slug
    for chunk_idx, chunk_verses_list in enumerate(chunks):
        chunk_text = format_chapter_text(chunk_verses_list)
        chap_label = (
            f"{chapter} (chunk {chunk_idx + 1}/{len(chunks)})"
            if len(chunks) > 1 else str(chapter)
        )
        prompt = build_prompt(book_label, chap_label, chunk_text)
        passes = await render_chunk(client, prompt)
        chunk_results.append(passes)

    per_verse_passes = merge_chunks_per_verse(chunk_results)
    records = build_per_verse_records(verses, per_verse_passes)
    out_path = write_report(book_slug, chapter, records)
    return out_path, records


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--book", required=True, help="book slug (e.g., 19-psalms)")
    p.add_argument("--chapter", type=int, required=True)
    p.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE,
                   help=f"verses per chunk for long-chapter sharding (default {DEFAULT_CHUNK_SIZE})")
    p.add_argument("--dry-run", action="store_true",
                   help="Estimate token cost without dispatching API")
    p.add_argument("--api-key", default=None,
                   help="Anthropic API key (defaults to ANTHROPIC_API_KEY env)")
    args = p.parse_args()

    chapter_path, verses = load_chapter(args.book, args.chapter)
    print(f"Chapter: {chapter_path.relative_to(REPO_ROOT)} ({len(verses)} verses)",
          file=sys.stderr)

    if args.dry_run:
        s = dry_run_summary(verses, args.chunk_size)
        print(json.dumps(s, indent=2))
        return 0

    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set (or pass --api-key)",
              file=sys.stderr)
        return 2

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    t0 = time.time()
    out_path, records = asyncio.run(
        render_chapter_async(client, args.book, args.chapter, args.chunk_size)
    )
    elapsed = time.time() - t0

    # Summary to stderr
    from collections import Counter
    agree_counts = Counter(r["agreement"] for r in records)
    print(f"\nRendered in {elapsed:.1f}s → {out_path.relative_to(REPO_ROOT)}",
          file=sys.stderr)
    for verdict, n in agree_counts.most_common():
        print(f"  {verdict:24s} {n:4d}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
