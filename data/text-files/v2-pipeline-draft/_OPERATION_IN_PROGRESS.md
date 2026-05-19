# Operation In Progress — Wholesale v2/heb replacement with pipeline draft

**Status field**: see "Current phase" below.

**Operation**: Replace `data/text-files/v2/heb/` (929 hand-edited chapters) with `data/text-files/v2-pipeline-draft/heb/` (929 pipeline-generated drafts), then run the build cascade for all 39 books, commit + push.

**Stan's decision**: "the painstaking hand-edits were still crap; this gets us much closer - and at scale - than i ever was; this method is the way forward, so let's do the destructive approach." (this session, 2026-05-19)

**Why this is safe to do destructively**: git preserves the prior v2/heb content under prior commits. The pre-destruction state can be restored via `git checkout <pre-commit-SHA> -- data/text-files/v2/heb/` if a chapter regression is identified.

---

## Operation phases

| # | Phase | State | Verification |
|---|---|---|---|
| 1 | Backup acknowledgment (git history is the backup) | DONE | `git log` shows pre-destruction commits including `d11152137` |
| 2 | Wholesale copy `v2-pipeline-draft/heb/*` → `v2/heb/*` | PENDING | `diff -r v2-pipeline-draft/heb v2/heb` would return empty |
| 3 | Commit replaced v2/heb | PENDING | `git log` shows new commit with "wholesale v2/heb replace" subject |
| 4 | Run build cascade for all 39 books | PENDING | `books/*.html` files updated |
| 5 | Commit cascade output | PENDING | `git log` shows new commit |
| 6 | Push to origin/main (triggers tanakh-reader.com deploy) | PENDING | `git status` shows up-to-date with origin |
| 7 | Delete this OPERATION_IN_PROGRESS.md | PENDING | This file removed |

## If compaction happens mid-operation

A fresh Claude on resume should:
1. Run the CLAUDE.md compaction-resume JSONL re-read protocol
2. Read this file to know the operation state
3. Inspect `git status` and `git log` to verify where the operation actually got to
4. Resume from the next PENDING phase
5. Update this file's status fields as phases complete

## Phase-by-phase commands (reproducible)

**Phase 2** — copy:
```bash
cd /c/Users/bibleman/repos/readers-tanakh
cp -r data/text-files/v2-pipeline-draft/heb/* data/text-files/v2/heb/
```

Then verify with:
```bash
diff -r data/text-files/v2-pipeline-draft/heb data/text-files/v2/heb
# Expected: empty diff (identical content)
```

**Phase 3** — commit:
```bash
git add data/text-files/v2/heb/
git commit -m "feat: wholesale replace v2/heb with mechanical-first pipeline draft

Replaces 929 hand-edited chapters with the v2-pipeline-draft output produced by
scripts/atu_pipeline_v2/run_full_tanakh.py (commit d11152137). The pipeline applies
the 14 validated binding rules over BHSA clause-atoms; methodology specified in
atu-method/docs/framework.md + binding-rules-hebrew.md (commit atu-method 1d10aa2).

Prior v2/heb is preserved in git history; specific chapters can be reverted via
git checkout <pre-destruction-SHA> -- data/text-files/v2/heb/<book>/<chapter>.txt
if editorial review identifies regressions."
git push
```

**Phase 4** — build cascade:
```bash
# Per-book loop (39 books)
for book in 01-genesis 02-exodus 03-leviticus 04-numbers 05-deuteronomy 06-joshua 07-judges 08-ruth 09-1samuel 10-2samuel 11-1kings 12-2kings 13-1chronicles 14-2chronicles 15-ezra 16-nehemiah 17-esther 18-job 19-psalms 20-proverbs 21-ecclesiastes 22-songofsongs 23-isaiah 24-jeremiah 25-lamentations 26-ezekiel 27-daniel 28-hosea 29-joel 30-amos 31-obadiah 32-jonah 33-micah 34-nahum 35-habakkuk 36-zephaniah 37-haggai 38-zechariah 39-malachi; do
  echo "=== $book ==="
  PYTHONIOENCODING=utf-8 py -3 scripts/refresh_book.py --book $book --build
done
```

**Phase 5** — commit cascade output:
```bash
git add books/ data/text-files/v2/eng-interlinear/ data/text-files/v2/eng-kjv/ data/text-files/v2/translit/
git commit -m "build: cascade rebuild after wholesale v2/heb replace"
git push
```

**Phase 6 → 7** — verify deploy and delete this file.

## Pre-operation snapshot

| Item | Value |
|---|---|
| Pre-destruction commit (v2/heb hand-edited state) | `d11152137` (also see `922001bc0`, `c9471de13`) |
| Pipeline-draft commit | `d11152137` |
| Source method docs | `atu-method` commit `1d10aa2` |
| Diff report at start | 37.4% verse-count match corpus-wide; pipeline +7,507 ATUs (+11.5% granular) vs hand-edited |
| Chapters being replaced | 929 |
| Books being rebuilt | 39 |
