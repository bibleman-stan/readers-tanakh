#!/usr/bin/env python3
"""
v2_llm_atu_judgments.py — Opus 3-pass narrow LLM judgments per v1.5 clause-group.

For each clause-group from v1.5, ask the model:
  - Does this clause-group constitute ONE complete-thought ATU, or could it be
    split into multiple smaller complete-thought ATUs?
  - If split, where (which inter-word position)?

3 independent Opus passes per group. Output JSONL with verdicts + verdict
aggregation (UNANIMOUS / MAJORITY-by-count / ALL-DISAGREE).

Cost: ~77 groups × 3 passes = 231 calls, est. ~$3-5 in API spend.
"""

from __future__ import annotations
import asyncio
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import anthropic


OUT_DIR = Path(
    r"C:\Users\bibleman\repos\readers-tanakh\research\atu-pilot-mechanical-first"
)
IN_JSONL = OUT_DIR / "v1_5_groups.jsonl"
OUT_JSONL = OUT_DIR / "v2_judgments.jsonl"
OUT_TXT = OUT_DIR / "v2_judgments.txt"

MODEL = "claude-opus-4-7"
MAX_CONCURRENT = 6
MAX_TOKENS = 600


PROMPT_TEMPLATE = """You are evaluating Hebrew text for atomic-thought-unit (ATU) granularity in a biblical-Hebrew reading apparatus.

An ATU is one complete thought — a self-contained predication a reader can take in as a single unit before moving on. Atomic-thought boundaries are NOT identical to clause boundaries: some clauses bind together into one ATU (e.g., a speech-intro frame bound to its short reply), while a complex clause-group sometimes contains multiple distinct ATUs (e.g., a sequence of coordinated imperatives, each its own thought).

CONTEXT — the preceding ATU candidates already classified in this chapter:
{context}

CURRENT CLAUSE-GROUP being evaluated (clauses joined mechanically by a syntactic binding rule):
{group_text}

Number of constituent BHSA clauses in this group: {n_clauses}
Mechanical bindings that were applied to merge these clauses: {bindings}

QUESTION: how many ATUs are in this clause-group?

Answer with strict JSON only, no prose before or after:
{{
  "n_atus": <integer 1, 2, or 3+>,
  "splits": [<list of clause indices where each new ATU begins, 0-based within the group; empty list if n_atus == 1>],
  "reasoning": "<one-sentence justification, max 30 words>"
}}

Examples:
- A speech-intro "and he said" bound to a short reply "here I am" = 1 ATU. splits=[].
- A speech-intro "and he said" followed by a long sequence of 3 distinct imperatives ("take your son ... go ... offer") = 4 ATUs. splits=[1, 2, 3] (each imperative is its own ATU, plus the speech-intro).
- A noun phrase bound to a short restrictive relative ("your son whom you love") = 1 ATU. splits=[].
- A complete clause followed by a free-standing restrictive relative ("on one of the mountains" + "which I will tell you") = 2 ATUs. splits=[1]."""


def build_context(prior_groups: list[dict], k: int = 3) -> str:
    """Return the last k prior group texts as plain context."""
    if not prior_groups:
        return "(none — this is the first clause-group in the chapter)"
    lines = []
    for g in prior_groups[-k:]:
        lines.append(f"- v.{g['verse_first']}: {g['text']}")
    return "\n".join(lines)


def build_prompt(group: dict, prior_groups: list[dict]) -> str:
    return PROMPT_TEMPLATE.format(
        context=build_context(prior_groups),
        group_text=group["text"],
        n_clauses=group["n_clauses"],
        bindings=", ".join(group["bindings_fired"]) if group["bindings_fired"] else "(none — single clause)",
    )


async def one_pass(client, prompt: str, pass_id: int) -> dict:
    """Run one Opus pass; return parsed JSON verdict or error dict."""
    try:
        msg = await asyncio.to_thread(
            client.messages.create,
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in msg.content if hasattr(b, "text")).strip()
        # Strip code fences if model added them
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
        verdict = json.loads(text)
        verdict["pass"] = pass_id
        verdict["raw_text"] = text
        return verdict
    except json.JSONDecodeError as e:
        return {"pass": pass_id, "error": f"json_decode: {e}", "raw_text": text if 'text' in locals() else ""}
    except Exception as e:
        return {"pass": pass_id, "error": f"{type(e).__name__}: {e}"}


async def evaluate_group(client, group: dict, prior_groups: list[dict], sem: asyncio.Semaphore) -> dict:
    async with sem:
        prompt = build_prompt(group, prior_groups)
        passes = await asyncio.gather(*[one_pass(client, prompt, i + 1) for i in range(3)])

        # Aggregate
        n_atus_values = [p.get("n_atus") for p in passes if "n_atus" in p]
        splits_lists = [tuple(p.get("splits", [])) for p in passes if "n_atus" in p]

        n_atus_counter = Counter(n_atus_values)
        splits_counter = Counter(splits_lists)

        if len(passes) - len(n_atus_values) > 0:
            verdict_class = "ERROR"
            agreed_n_atus = None
            agreed_splits = None
        elif n_atus_counter and n_atus_counter.most_common(1)[0][1] == 3:
            verdict_class = "UNANIMOUS"
            agreed_n_atus = n_atus_counter.most_common(1)[0][0]
            agreed_splits = list(splits_counter.most_common(1)[0][0])
        elif n_atus_counter and n_atus_counter.most_common(1)[0][1] == 2:
            verdict_class = "MAJORITY"
            agreed_n_atus = n_atus_counter.most_common(1)[0][0]
            agreed_splits = list(splits_counter.most_common(1)[0][0])
        else:
            verdict_class = "ALL-DISAGREE"
            agreed_n_atus = None
            agreed_splits = None

        return {
            "group_idx": group["group_idx"],
            "verse_first": group["verse_first"],
            "n_clauses": group["n_clauses"],
            "bindings_fired": group["bindings_fired"],
            "text": group["text"],
            "passes": passes,
            "verdict_class": verdict_class,
            "agreed_n_atus": agreed_n_atus,
            "agreed_splits": agreed_splits,
        }


async def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    # Load groups
    groups: list[dict] = []
    with IN_JSONL.open(encoding="utf-8") as fp:
        for line in fp:
            if line.strip():
                groups.append(json.loads(line))
    print(f"Loaded {len(groups)} v1.5 ATU candidate groups")

    client = anthropic.Anthropic()
    sem = asyncio.Semaphore(MAX_CONCURRENT)

    # Evaluate each group with rolling prior-context
    results: list[dict] = []
    prior_groups: list[dict] = []

    # Run in batches so prior_groups is mostly populated when each fires.
    # For simplicity: run sequentially-revealed but parallel-dispatched.
    print(f"Dispatching {len(groups)} group-evaluations (3 passes each = {len(groups) * 3} Opus calls)...")

    tasks = []
    for i, g in enumerate(groups):
        # Prior context = groups before this one (in JSONL order)
        prior = groups[:i]
        tasks.append(evaluate_group(client, g, prior, sem))

    completed = 0
    for fut in asyncio.as_completed(tasks):
        r = await fut
        results.append(r)
        completed += 1
        if completed % 10 == 0 or completed == len(groups):
            print(f"  ...{completed}/{len(groups)} complete")

    # Reorder by group_idx for output stability
    results.sort(key=lambda r: r["group_idx"])

    # Emit JSONL
    with OUT_JSONL.open("w", encoding="utf-8") as fp:
        for r in results:
            fp.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Human-readable
    with OUT_TXT.open("w", encoding="utf-8") as fp:
        current_verse = None
        for r in results:
            if r["verse_first"] != current_verse:
                if current_verse is not None:
                    fp.write("\n")
                fp.write(f"=== 22:{r['verse_first']} ===\n")
                current_verse = r["verse_first"]
            v = r["verdict_class"]
            n = r["agreed_n_atus"]
            sp = r["agreed_splits"]
            tag = f"[{v} → {n} ATU{'s' if (n or 0) > 1 else ''}"
            if sp:
                tag += f" splits={sp}"
            tag += "]"
            fp.write(f"  g{r['group_idx']:3d} {tag:35s}  {r['text']}\n")

    print(f"\nWrote: {OUT_JSONL}")
    print(f"Wrote: {OUT_TXT}")

    # Summary
    verdict_counter = Counter(r["verdict_class"] for r in results)
    print(f"\n--- Verdict distribution ---")
    for v, c in verdict_counter.most_common():
        print(f"  {v}: {c}")

    n_atus_counter = Counter(r["agreed_n_atus"] for r in results if r["agreed_n_atus"] is not None)
    print(f"\n--- Agreed n_atus distribution ---")
    for n, c in sorted(n_atus_counter.items()):
        print(f"  {n} ATU(s): {c} groups")

    # Effective total ATUs after LLM splits
    total_atus = sum(r["agreed_n_atus"] or r["n_clauses"] for r in results)
    print(f"\n--- Pipeline final ---")
    print(f"  v1 clauses: 104")
    print(f"  v1.5 candidate groups: {len(groups)}")
    print(f"  v2 final ATUs (after LLM splits): {total_atus}")


if __name__ == "__main__":
    asyncio.run(main())
