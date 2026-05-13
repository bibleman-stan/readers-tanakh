#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""triage_validator_findings.py — sample REVIEW-REQUIRED findings into a
human-readable ballot for editorial TP/FP marking.

Workflow:
  1. Run a validator with --json --v2 to get all current findings.
  2. Stratify by rule_id (each arm of the validator gets representative coverage).
  3. Random-sample N per stratum (seedable for reproducibility).
  4. Emit a Markdown ballot to data/reports/triage/<validator>-<date>.md.
     - Each finding gets a one-keystroke verdict slot: replace `[ ]` with T/F/?.
  5. Editor reviews the file in any markdown editor.
  6. (Future) An aggregator parses the marked ballot back into per-rule_id TP rate
     and recommends STRONG promotion when ≥80% TP per canon §7.

Usage:
  PYTHONIOENCODING=utf-8 py -3 scripts/triage_validator_findings.py \\
      --validator verb_object_bond --n 50 --seed 42

  PYTHONIOENCODING=utf-8 py -3 scripts/triage_validator_findings.py \\
      --validator coordinated_object --n 30 --cluster torah --seed 1

Output goes to data/reports/triage/ (gitignored per data/reports/ in .gitignore).
"""

import argparse
import json
import os
import random
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
VALIDATORS_DIR = REPO_ROOT / "validators"
TRIAGE_OUT_DIR = REPO_ROOT / "data" / "reports" / "triage"

LAYER_DIRS = ("syntax", "colometry")

# 6 cluster groups (from CLAUDE.md / handoffs/14-operational-protocols.md).
# Maps cluster name → set of book directory slugs (post-prefix-strip).
CLUSTERS: dict[str, set[str]] = {
    "torah": {"genesis", "exodus", "leviticus", "numbers", "deuteronomy"},
    "former_prophets": {"joshua", "judges", "1samuel", "2samuel", "1kings", "2kings"},
    "latter_prophets": {
        "isaiah", "jeremiah", "ezekiel",
        "hosea", "joel", "amos", "obadiah", "jonah", "micah",
        "nahum", "habakkuk", "zephaniah", "haggai", "zechariah", "malachi",
    },
    "writings_prose": {
        "ruth", "esther", "daniel", "ezra", "nehemiah",
        "1chronicles", "2chronicles", "ecclesiastes",
    },
    "sifrei_emet": {"psalms", "proverbs", "job"},
    # Embedded poetry routed via prose books — no cluster-filter equivalent
    # at the file level (would need verse-range filtering); deferred.
}

_PREFIX_RE = re.compile(r"^\d{2}-")
_FILE_PATH_RE = re.compile(r"data/text-files/v2/heb/(\d{2}-)?([a-z0-9]+)/[a-z0-9]+-(\d+)\.txt")
_VERSE_REF_RE = re.compile(r"^\d+:\d+[a-z]?$")


def slug_from_filepath(filepath: str) -> tuple[str, str]:
    """Extract (book_slug, chapter) from a v2/heb file path.

    'data/text-files/v2/heb/01-genesis/genesis-03.txt' → ('genesis', '03')
    """
    m = _FILE_PATH_RE.match(filepath.replace("\\", "/"))
    if not m:
        return ("?", "?")
    return (m.group(2), m.group(3))


_LINE_TO_VERSE_CACHE: dict[str, dict[int, str]] = {}


def line_to_verse_map(filepath_rel: str) -> dict[int, str]:
    """Build {line_number: verse_ref} map for a v2/heb chapter file.

    Verse markers are bare lines matching \\d+:\\d+(?:[a-z])? (e.g. '1:1', '3:5a').
    Each cola line gets the verse_ref of the most recent preceding marker.
    Cached per filepath since multiple findings may target the same chapter.
    """
    if filepath_rel in _LINE_TO_VERSE_CACHE:
        return _LINE_TO_VERSE_CACHE[filepath_rel]
    abs_path = REPO_ROOT / filepath_rel.replace("\\", "/")
    mapping: dict[int, str] = {}
    if not abs_path.exists():
        _LINE_TO_VERSE_CACHE[filepath_rel] = mapping
        return mapping
    current_verse = "?"
    for lineno, raw in enumerate(abs_path.read_text(encoding="utf-8").splitlines(), start=1):
        s = raw.strip()
        if not s:
            mapping[lineno] = current_verse
            continue
        if _VERSE_REF_RE.match(s):
            current_verse = s
        mapping[lineno] = current_verse
    _LINE_TO_VERSE_CACHE[filepath_rel] = mapping
    return mapping


def verse_for_finding(f: dict) -> str:
    fp = f.get("file", "")
    line = f.get("line")
    if not fp or line is None:
        return "?"
    return line_to_verse_map(fp).get(int(line), "?")


def discover_validator(name: str) -> Path | None:
    """Find validate_<name>.py under validators/syntax or validators/colometry."""
    candidates = [
        VALIDATORS_DIR / "syntax" / f"validate_{name}.py",
        VALIDATORS_DIR / "colometry" / f"validate_{name}.py",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def run_validator(validator_path: Path) -> dict:
    """Invoke validator with --json --v2; return parsed dict."""
    cmd = [sys.executable, str(validator_path), "--json", "--v2"]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        env=env,
    )
    # Validators exit 1 when they emit findings; that's expected.
    if not proc.stdout.strip():
        raise RuntimeError(
            f"validator {validator_path.name} produced no JSON output\n"
            f"stderr: {proc.stderr[:500]}"
        )
    return json.loads(proc.stdout)


def filter_by_cluster(findings: list[dict], cluster: str | None) -> list[dict]:
    if cluster is None:
        return findings
    if cluster not in CLUSTERS:
        raise SystemExit(
            f"unknown cluster '{cluster}'; valid: {sorted(CLUSTERS)}"
        )
    book_set = CLUSTERS[cluster]
    return [f for f in findings if slug_from_filepath(f.get("file", ""))[0] in book_set]


def normalize_finding(f: dict) -> dict:
    """Normalize finding to a uniform shape across validator schemas.

    Standard shape (most validators): file, line, next_line, severity, rule_id,
    rule_short, brief, applied_action, optional pattern/subcase/verse_n.

    Legacy shape (coordinated_object): file, line, rule, severity, book, chapter,
    verse, prior_line (text), next_line (text!), next_line_num (int),
    prosodic_word_count, annotation, suggested_action.

    Returns dict with: file, line, next_line, verse, rule_short, brief,
    applied_action, severity, _strata (list of (label, value) candidates).
    """
    out = {}
    out["file"] = f.get("file", "")
    out["severity"] = f.get("severity", "")

    # Detect legacy schema by presence of 'annotation' + 'next_line_num' (without 'brief').
    is_legacy = "annotation" in f and "next_line_num" in f and "brief" not in f

    if is_legacy:
        out["line"] = f.get("line")
        out["next_line"] = f.get("next_line_num")
        # For legacy: verse is directly available; build chapter:verse string.
        ch = f.get("chapter")
        v = f.get("verse")
        out["verse"] = f"{ch}:{v}" if ch is not None and v is not None else "?"
        # Build brief from prior_line + next_line text.
        prior_text = f.get("prior_line", "").strip()
        next_text = f.get("next_line", "").strip()
        ann = f.get("annotation", "").strip()
        sep = " // " if prior_text and next_text else ""
        text_pair = f"{prior_text}{sep}{next_text}" if (prior_text or next_text) else ""
        out["brief"] = f"{ann}\n\n{text_pair}".strip() if text_pair else ann
        out["rule_short"] = f.get("rule", "?")
        out["applied_action"] = f.get("suggested_action", "")
        out["_strata"] = [("rule", str(f.get("rule", "?")))]
    else:
        out["line"] = f.get("line")
        out["next_line"] = f.get("next_line")
        out["brief"] = f.get("brief", "")
        out["rule_short"] = f.get("rule_short", "?")
        out["applied_action"] = f.get("applied_action") or ""
        # verse computed lazily downstream from line_to_verse_map
        out["verse"] = None
        # Stratum candidates in priority order — caller picks the most discriminating.
        candidates = []
        if "pattern" in f:
            candidates.append(("pattern", str(f["pattern"])))
        if "subcase" in f:
            candidates.append(("subcase", str(f["subcase"])))
        candidates.append(("rule_id", str(f.get("rule_id", "?"))))
        out["_strata"] = candidates

    return out


def pick_stratum_key(normalized: list[dict]) -> str:
    """Return the stratum dimension name (e.g. 'pattern', 'rule_id') with the
    most distinct values across the corpus. Ties broken by candidate priority order
    (pattern > subcase > rule_id, per normalize_finding).
    """
    # All findings share the same set of candidate dimension names (since they
    # come from one validator). Inspect the first finding's candidates.
    if not normalized:
        return "rule_id"
    candidates = [name for (name, _) in normalized[0]["_strata"]]
    best_name = candidates[0]
    best_distinct = 0
    for name in candidates:
        distinct = len({_lookup_stratum(n, name) for n in normalized})
        if distinct > best_distinct:
            best_distinct = distinct
            best_name = name
    return best_name


def _lookup_stratum(n: dict, dim_name: str) -> str:
    for name, value in n["_strata"]:
        if name == dim_name:
            return value
    return "?"


def stratify(normalized: list[dict], stratum_key: str) -> dict[str, list[dict]]:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for n in normalized:
        buckets[_lookup_stratum(n, stratum_key)].append(n)
    return dict(buckets)


def sample_per_stratum(buckets: dict[str, list[dict]], n: int, seed: int) -> dict[str, list[dict]]:
    rng = random.Random(seed)
    out: dict[str, list[dict]] = {}
    for k, fs in buckets.items():
        if len(fs) <= n:
            out[k] = list(fs)
        else:
            out[k] = rng.sample(fs, n)
    return out


def render_finding(n: dict, idx: int, stratum_key: str) -> str:
    fp = n["file"]
    book, chapter = slug_from_filepath(fp)
    line = n["line"]
    nl = n["next_line"]
    verse = n["verse"] or verse_for_finding({"file": fp, "line": line})
    rule_short = n["rule_short"]
    brief = n["brief"]
    applied = n["applied_action"]
    sev = n["severity"]
    stratum_value = _lookup_stratum(n, stratum_key)

    # Clickable link to the v2/heb chapter at the finding's first line.
    rel_link = fp.replace("\\", "/")
    if nl is not None:
        line_anchor = f"{rel_link}#L{line}-L{nl}"
        line_ref = f"{line}→{nl}"
    else:
        line_anchor = f"{rel_link}#L{line}"
        line_ref = str(line)
    file_link = f"[{book}-{chapter} {verse}]({line_anchor})"

    head = f"### {idx}. {file_link}  line {line_ref}  [{stratum_value}] {rule_short}".rstrip()
    body = brief
    meta_bits = []
    if applied:
        meta_bits.append(f"action={applied}")
    if sev and sev != "REVIEW-REQUIRED":
        meta_bits.append(f"sev={sev}")
    meta = "  ".join(meta_bits)
    parts = [head, "", body]
    if meta:
        parts.append("")
        parts.append(f"_{meta}_")
    parts.append("")
    parts.append("**verdict:** [ ]   _notes:_")
    return "\n".join(parts)


def render_ballot(
    validator_name: str,
    rule: str,
    layer: int,
    total_findings: int,
    cluster: str | None,
    sampled: dict[str, list[dict]],
    bucket_totals: dict[str, int],
    stratum_key: str,
    n_per_stratum: int,
    seed: int,
) -> str:
    today = date.today().isoformat()
    lines = []
    lines.append(f"# Triage — `validate_{validator_name}` — {today}")
    lines.append("")
    lines.append(f"- **Validator:** `validate_{validator_name}` (Layer {layer})")
    lines.append(f"- **Rule:** {rule}")
    lines.append(f"- **Total findings (after cluster filter):** {total_findings}")
    if cluster:
        lines.append(f"- **Cluster filter:** `{cluster}`")
    lines.append(f"- **Stratification dimension:** `{stratum_key}`")
    lines.append(f"- **Sample size:** {n_per_stratum} per stratum (seed={seed})")
    lines.append("")
    lines.append("## How to mark")
    lines.append("Replace each `[ ]` with one of:")
    lines.append("- `[T]` — True positive (real candidate; merge/split as proposed)")
    lines.append("- `[F]` — False positive (validator wrong; should NOT fire here)")
    lines.append("- `[?]` — Uncertain (need second look or context beyond brief)")
    lines.append("")
    lines.append(f"Optionally add a short note after `_notes:_`. Save the file. Aggregator (future) will compute per-`{stratum_key}` TP rate and recommend STRONG promotion if ≥80%.")
    lines.append("")
    lines.append("## Stratification")
    lines.append("")
    lines.append(f"| {stratum_key} | total | sampled |")
    lines.append("|---|---|---|")
    for k in sorted(sampled):
        lines.append(f"| `{k}` | {bucket_totals.get(k, '?')} | {len(sampled[k])} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    idx = 0
    for k in sorted(sampled):
        if len(sampled) > 1:
            lines.append(f"### Stratum: `{k}` ({len(sampled[k])} of {bucket_totals.get(k, '?')} sampled)")
            lines.append("")
        for n in sampled[k]:
            idx += 1
            lines.append(render_finding(n, idx, stratum_key))
            lines.append("")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--validator", required=True, help="validator name (without 'validate_' prefix), e.g. 'verb_object_bond'")
    p.add_argument("--n", type=int, default=50, help="findings per rule_id stratum (default: 50)")
    p.add_argument("--seed", type=int, default=42, help="random seed for reproducibility (default: 42)")
    p.add_argument("--cluster", default=None, choices=sorted(CLUSTERS) + [None], help="optional cluster filter")
    p.add_argument("--output", type=Path, default=None, help="output path (default: data/reports/triage/<validator>-<date>.md)")
    args = p.parse_args()

    vp = discover_validator(args.validator)
    if vp is None:
        return _err(f"validator not found: validate_{args.validator}.py under validators/{{syntax,colometry}}/")

    print(f"running {vp.relative_to(REPO_ROOT)} ...", file=sys.stderr)
    result = run_validator(vp)
    rule = result.get("rule", "?")
    layer = result.get("layer", "?")
    findings = result.get("findings", [])
    total_unfiltered = len(findings)

    findings = filter_by_cluster(findings, args.cluster)
    after_cluster = len(findings)

    if after_cluster == 0:
        msg = f"no findings"
        if args.cluster:
            msg += f" in cluster '{args.cluster}' (total {total_unfiltered} unfiltered)"
        return _err(msg)

    normalized = [normalize_finding(f) for f in findings]
    stratum_key = pick_stratum_key(normalized)
    buckets = stratify(normalized, stratum_key)
    bucket_totals = {k: len(v) for k, v in buckets.items()}
    sampled = sample_per_stratum(buckets, args.n, args.seed)
    n_sampled = sum(len(v) for v in sampled.values())

    print(f"  total: {total_unfiltered}  after cluster: {after_cluster}  stratum_key: {stratum_key}  strata: {len(buckets)}  sampled: {n_sampled}", file=sys.stderr)

    md = render_ballot(
        validator_name=args.validator,
        rule=rule,
        layer=layer,
        total_findings=after_cluster,
        cluster=args.cluster,
        sampled=sampled,
        bucket_totals=bucket_totals,
        stratum_key=stratum_key,
        n_per_stratum=args.n,
        seed=args.seed,
    )

    if args.output:
        out_path = args.output
    else:
        suffix = f"-{args.cluster}" if args.cluster else ""
        out_path = TRIAGE_OUT_DIR / f"{args.validator}{suffix}-{date.today().isoformat()}.md"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8", newline="\n")
    print(f"wrote {out_path.relative_to(REPO_ROOT)}  ({n_sampled} findings)", file=sys.stderr)
    return 0


def _err(msg: str) -> int:
    print(f"triage: {msg}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
