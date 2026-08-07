# atu_pipeline_v2 — Productized mechanical-first ATU pipeline

Productized version of the pilot at `research/atu-pilot-mechanical-first/`. Batch-runs the validated 14-rule binding catalog over the entire Tanakh and produces draft ATU renderings as a staging artifact (`data/text-files/v2-pipeline-draft/heb/`) for diff against hand-edited `data/text-files/v2/heb/`.

Methodology reference: `../../../atu-method/1-method/framework.md` + `../../../atu-method/1-method/binding-rules-hebrew.md`.

---

## Scripts

| Script | Purpose |
|---|---|
| `binding_rules.py` | The 14 validated binding rules (B1-B14, B4 retired) as an importable module |
| `run_full_tanakh.py` | Batch driver — loads BHSA once, processes all 39 books / 929 chapters, writes one v2/heb-format file per chapter |
| `diff_pipeline_vs_handedited.py` | Per-chapter comparison of pipeline draft vs hand-edited; emits markdown report + per-chapter JSONL |

## Usage

```bash
# Full Tanakh batch (~15 min after BHSA cache warm)
py -3 scripts/atu_pipeline_v2/run_full_tanakh.py

# Single book
py -3 scripts/atu_pipeline_v2/run_full_tanakh.py --book 01-genesis

# Single book, first N chapters (testing)
py -3 scripts/atu_pipeline_v2/run_full_tanakh.py --book 01-genesis --limit 3

# Diff vs hand-edited
py -3 scripts/atu_pipeline_v2/diff_pipeline_vs_handedited.py
```

## Output

- **Pipeline draft**: `data/text-files/v2-pipeline-draft/heb/{book-folder}/{book-stem}.txt` (929 files)
  - Format: v2/heb-style — verse headers (`BB:NN`), one ATU per line, blank line between verses
  - Each file is a draft that an editor can compare against the hand-edited `data/text-files/v2/heb/{book-folder}/{book-stem}.txt`
- **Diff report**: `data/text-files/v2-pipeline-draft/_diff_report.md`
  - Corpus-wide totals
  - Per-book summary
  - Top-25 chapters by largest ATU delta
  - Top-25 chapters by lowest verse-match percentage
- **Per-chapter detail**: `data/text-files/v2-pipeline-draft/_diff_per_chapter.jsonl`
  - One record per chapter with per-verse pipeline-vs-handedited ATU counts

## Editorial workflow

The pipeline produces drafts; editorial review handles the residual. Workflow:

1. Run `run_full_tanakh.py` to regenerate the draft (when binding rules change or BHSA updates)
2. Run `diff_pipeline_vs_handedited.py` to surface where the draft diverges from hand-edited
3. Review high-divergence chapters (top of the diff report) first
4. For each divergent verse: decide if pipeline is over-segmenting (accept hand-edit), under-segmenting (accept pipeline), or both have merit (editorial judgment)

The 14-rule catalog produces ATU drafts at 85-91% boundary F1 against discourse-linguistic reference (LDHB) across 4 validated chapter genres. Divergences from hand-edited content concentrate in dense prophetic poetry (Isaiah, Jeremiah, Hosea, Amos, Nahum) and densely casuistic legal lists, per the validation set.

## Productization notes

This pipeline is research-grade productization. Future engineering moves (not required for the apparatus to exist):

- Parallelize across books for faster batch runs (current: serial)
- Add per-chapter audit-trail JSONL (currently only the final ATU rendering is written)
- Optional v2 LLM adjudication on flagged residuals (skipped by default; see `framework.md` §3.4)
- Integration with `refresh_book.py` build cascade
