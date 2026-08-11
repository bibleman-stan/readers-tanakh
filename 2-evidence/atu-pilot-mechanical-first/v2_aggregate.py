#!/usr/bin/env python3
"""
v2_aggregate.py — aggregate the 3 independent agent passes into UNANIMOUS /
MAJORITY / ALL-DISAGREE verdicts per group, then expand splits into a final
ATU list.

Inputs:
  C:\\tmp\\v2_pass_1.jsonl
  C:\\tmp\\v2_pass_2.jsonl
  C:\\tmp\\v2_pass_3.jsonl
  research/atu-pilot-mechanical-first/v1_5_groups.jsonl

Outputs:
  research/atu-pilot-mechanical-first/v2_aggregated.jsonl  — per-group verdict
  research/atu-pilot-mechanical-first/v2_final_atus.jsonl  — expanded ATU list
  research/atu-pilot-mechanical-first/v2_final_atus.txt    — human-readable
"""

from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

OUT_DIR = Path(
    r"C:\Users\bibleman\repos\readers-tanakh\research\atu-pilot-mechanical-first"
)
GROUPS_PATH = OUT_DIR / "v1_5_groups.jsonl"
PASS_PATHS = [Path(rf"C:\tmp\v2_pass_{i}.jsonl") for i in (1, 2, 3)]

OUT_AGG = OUT_DIR / "v2_aggregated.jsonl"
OUT_ATUS = OUT_DIR / "v2_final_atus.jsonl"
OUT_TXT = OUT_DIR / "v2_final_atus.txt"


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> None:
    groups = load_jsonl(GROUPS_PATH)
    groups_by_idx = {g["group_idx"]: g for g in groups}

    passes = []
    for path in PASS_PATHS:
        if not path.exists():
            raise SystemExit(f"ERROR: pass file missing: {path}")
        passes.append({r["group_idx"]: r for r in load_jsonl(path)})

    print(f"Loaded {len(groups)} groups + {len(passes)} pass files")

    # Aggregate per group
    aggregated = []
    for gi in sorted(groups_by_idx.keys()):
        g = groups_by_idx[gi]
        pass_verdicts = []
        for pi, p in enumerate(passes, 1):
            v = p.get(gi)
            if v is None:
                pass_verdicts.append({"pass": pi, "n_atus": None, "splits": [], "reasoning": "(missing)"})
            else:
                pass_verdicts.append({
                    "pass": pi,
                    "n_atus": v.get("n_atus"),
                    "splits": v.get("splits", []),
                    "reasoning": v.get("reasoning", ""),
                })

        # Count agreement on n_atus
        n_atus_values = [pv["n_atus"] for pv in pass_verdicts if pv["n_atus"] is not None]
        splits_values = [tuple(pv["splits"]) for pv in pass_verdicts if pv["n_atus"] is not None]

        n_counter = Counter(n_atus_values)
        splits_counter = Counter(splits_values)

        if len(n_atus_values) < 3:
            verdict_class = "ERROR"
            agreed_n_atus = None
            agreed_splits = None
        elif n_counter.most_common(1)[0][1] == 3:
            verdict_class = "UNANIMOUS"
            agreed_n_atus = n_counter.most_common(1)[0][0]
            agreed_splits = list(splits_counter.most_common(1)[0][0])
        elif n_counter.most_common(1)[0][1] == 2:
            verdict_class = "MAJORITY"
            agreed_n_atus = n_counter.most_common(1)[0][0]
            agreed_splits = list(splits_counter.most_common(1)[0][0])
        else:
            verdict_class = "ALL-DISAGREE"
            agreed_n_atus = None
            agreed_splits = None

        aggregated.append({
            "group_idx": gi,
            "verse_first": g["verse_first"],
            "n_clauses": g["n_clauses"],
            "bindings_fired": g["bindings_fired"],
            "text": g["text"],
            "verdict_class": verdict_class,
            "agreed_n_atus": agreed_n_atus,
            "agreed_splits": agreed_splits,
            "passes": pass_verdicts,
        })

    # Write aggregated
    with OUT_AGG.open("w", encoding="utf-8") as fp:
        for r in aggregated:
            fp.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Expand to final ATU list per agreed-verdict
    # For each group: if agreed_n_atus == 1, the whole group is one ATU.
    # Otherwise, split the constituent clauses by agreed_splits.
    final_atus = []
    atu_idx = 0
    for r in aggregated:
        g = groups_by_idx[r["group_idx"]]
        # Reconstruct per-clause texts from v1 — but we only kept joined `text` in v1_5.
        # We need per-clause splits inside the group. Read v1 to recover.
        pass  # Will fill in after reading v1

    # Re-read v1 clauses to split groups appropriately
    v1_clauses = load_jsonl(OUT_DIR / "v1_clauses.jsonl")
    # Map cid -> v1 clause
    cid_to_clause = {c["cid"]: c for c in v1_clauses}

    final_atus = []
    atu_idx = 0
    for r in aggregated:
        cids = groups_by_idx[r["group_idx"]]["clause_cids"]
        n_atus = r["agreed_n_atus"]
        splits = r["agreed_splits"] or []

        if n_atus is None or n_atus == 1 or not splits:
            # One ATU = whole group
            text = " ".join(cid_to_clause[c]["text"] for c in cids)
            final_atus.append({
                "atu_idx": atu_idx,
                "verse_first": r["verse_first"],
                "from_group": r["group_idx"],
                "verdict_class": r["verdict_class"],
                "clause_cids": cids,
                "text": text,
            })
            atu_idx += 1
        else:
            # Split the group's clauses at split points
            split_points = [0] + sorted(splits) + [len(cids)]
            for i in range(len(split_points) - 1):
                start = split_points[i]
                end = split_points[i + 1]
                sub_cids = cids[start:end]
                text = " ".join(cid_to_clause[c]["text"] for c in sub_cids)
                final_atus.append({
                    "atu_idx": atu_idx,
                    "verse_first": r["verse_first"],
                    "from_group": r["group_idx"],
                    "from_group_sub": f"{i+1}/{n_atus}",
                    "verdict_class": r["verdict_class"],
                    "clause_cids": sub_cids,
                    "text": text,
                })
                atu_idx += 1

    with OUT_ATUS.open("w", encoding="utf-8") as fp:
        for a in final_atus:
            fp.write(json.dumps(a, ensure_ascii=False) + "\n")

    # Human-readable
    with OUT_TXT.open("w", encoding="utf-8") as fp:
        current_verse = None
        for a in final_atus:
            if a["verse_first"] != current_verse:
                if current_verse is not None:
                    fp.write("\n")
                fp.write(f"=== 22:{a['verse_first']} ===\n")
                current_verse = a["verse_first"]
            sub = f" {a.get('from_group_sub', '')}" if "from_group_sub" in a else ""
            fp.write(f"  atu{a['atu_idx']:3d} (g{a['from_group']}{sub}, {a['verdict_class']:12s})  {a['text']}\n")

    # Summary
    print(f"\nWrote: {OUT_AGG}")
    print(f"Wrote: {OUT_ATUS}")
    print(f"Wrote: {OUT_TXT}")

    verdict_counter = Counter(r["verdict_class"] for r in aggregated)
    print(f"\n--- Verdict-class distribution ---")
    for v, c in verdict_counter.most_common():
        print(f"  {v}: {c}")

    n_atus_counter = Counter(r["agreed_n_atus"] for r in aggregated if r["agreed_n_atus"] is not None)
    print(f"\n--- Agreed n_atus distribution ---")
    for n, c in sorted(n_atus_counter.items()):
        print(f"  {n} ATU(s) per group: {c} groups")

    # ATUs added by LLM splits
    n_split_groups = sum(1 for r in aggregated if (r["agreed_n_atus"] or 1) > 1)
    n_extra_atus = sum((r["agreed_n_atus"] or 1) - 1 for r in aggregated if r["agreed_n_atus"])
    print(f"\n--- LLM split impact ---")
    print(f"  Groups split by LLM: {n_split_groups}")
    print(f"  Extra ATUs added: {n_extra_atus}")
    print(f"\n--- Pipeline totals ---")
    print(f"  v1 clauses: {len(v1_clauses)}")
    print(f"  v1.5 candidate groups: {len(groups)}")
    print(f"  v2 final ATUs: {len(final_atus)}")


if __name__ == "__main__":
    main()
