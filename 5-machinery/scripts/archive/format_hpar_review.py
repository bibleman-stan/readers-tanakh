"""
Convert hpar-high-confidence.tsv to a readable markdown review file with
English context pulled from v2/eng-kjv for each verse.

Output: data/syntax-reference/hpar-high-confidence-review.md
"""
import csv
import re
import sys
from pathlib import Path

def _find_repo_root():
    """Repo root by MARKER, not by counting parents.

    Counting encodes this file's depth in the tree, so moving the file silently
    breaks it and no text-based check notices. Anchoring on .git survives any
    move. Added 2026-08-10 after a reorg broke three different counted idioms.
    """
    from pathlib import Path as _P
    _here = _P(__file__).resolve()
    for _p in _here.parents:
        if (_p / ".git").exists():
            return _p
    return _here.parent


REPO_ROOT = _find_repo_root()
def get_english_for_verse(book_slug: str, chapter: int, verse: int) -> str:
    """Read v2/eng-kjv for the given verse; return joined non-blank lines."""
    book_name = book_slug.split("-", 1)[1] if "-" in book_slug else book_slug
    path = REPO_ROOT / "data" / "text-files" / "v2" / "eng-kjv" / book_slug / f"{book_name}-{chapter:02d}.txt"
    if not path.exists():
        return "(no eng-kjv)"
    text = path.read_text(encoding="utf-8")
    in_verse = False
    out_lines = []
    for line in text.split("\n"):
        s = line.strip()
        m = re.match(r"^(\d+):(\d+)\s*$", s)
        if m:
            v = int(m.group(2))
            if v == verse:
                in_verse = True
            elif in_verse:
                break  # next verse — stop
            continue
        if in_verse and s:
            out_lines.append(s)
    return " / ".join(out_lines)


def main():
    tsv_path = REPO_ROOT / "data" / "syntax-reference" / "hpar-high-confidence.tsv"
    md_path = REPO_ROOT / "data" / "syntax-reference" / "hpar-high-confidence-review.md"

    out = []
    out.append("# Hpar high-confidence findings — review list")
    out.append("")
    out.append(f"**{49} candidates** identified via Macula frame-args share-A1 signal "
               "(both clauses target the same object referent — canonical synonymous-")
    out.append("parallelism). Spot-check 5-10 entries; if the TP rate looks ≥80%, run")
    out.append("`5-machinery/scripts/apply_hpar_high_confidence.py` to apply the splits to v2/heb.")
    out.append("")
    out.append("---")
    out.append("")

    with tsv_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    for i, r in enumerate(rows, 1):
        book_slug = r["book"]
        chapter = int(r["chapter"])
        verse = int(r["verse"])
        english = get_english_for_verse(book_slug, chapter, verse)
        # Pretty book name
        book_name = book_slug.split("-", 1)[1].replace("samuel", " Samuel ").replace("kings", " Kings ").replace("chronicles", " Chronicles ")
        out.append(f"### {i}. {book_name.title().strip()} {chapter}:{verse}")
        out.append("")
        out.append(f"**EN:** {english}")
        out.append("")
        out.append(f"**Heads:** `{r['head_a']}` | `{r['head_b']}`  ({r['left_pw']}+{r['right_pw']} pw)")
        out.append("")
        out.append("**Hebrew clause A:**")
        out.append("")
        out.append(f"> {r['prior_text']}")
        out.append("")
        out.append("**Hebrew clause B (split point):**")
        out.append("")
        out.append(f"> {r['next_text']}")
        out.append("")
        out.append("---")
        out.append("")

    md_path.write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote review markdown to {md_path}")


if __name__ == "__main__":
    main()
