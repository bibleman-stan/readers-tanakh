"""Aramaic-verse guard for the Tanakh binding pipeline.

BHSA does NOT tag `language=arc` at the clause_atom level (only at the
*word* level returns None for clause_atoms). The Aramaic ranges therefore
must be HARDCODED as verse-range guards. The canonical ranges live here;
they originated in scripts/atu_pipeline/run_pipeline.py and were copied
into scripts/atu_pipeline_v2/tanakh_overrides.py at module-build time.
This module is the single source of truth for the v2 binding pipeline.

Empirical (Pipeline B Round 2, 2026-06-03): corpus-wide sweep of 1,378
Aramaic clause-atoms across 268 verses found 181 silent false-fires
WITHOUT this guard (B1=34, B6=25, B10=78, B14=43) and 0 fires WITH the
guard. The mechanism is precision=1.0 recall=1.0 against ground-truth
Aramaic adjacencies.

Held Aramaic ranges:
  Daniel 2:4-7:28
  Ezra 4:8, 5:1-6:18, 7:12-26
"""

import re

ARAMAIC_RANGES = {
    "27-daniel": [(2, "from-v4"), (3, "all"), (4, "all"), (5, "all"),
                  (6, "all"), (7, "all")],
    "15-ezra": [(4, "from-v8"), (5, "all"), (6, "to-v18"),
                (7, "from-v12-to-v26")],
}


def is_aramaic_verse(book_folder: str, chapter: int, verse: int) -> bool:
    """True if (book_folder, chapter, verse) is in a held Aramaic range."""
    ranges = ARAMAIC_RANGES.get(book_folder, [])
    for chap, scope in ranges:
        if chap != chapter:
            continue
        if scope == "all":
            return True
        m = re.match(r"from-v(\d+)$", scope)
        if m:
            if verse >= int(m.group(1)):
                return True
            continue
        m = re.match(r"to-v(\d+)$", scope)
        if m:
            if verse <= int(m.group(1)):
                return True
            continue
        m = re.match(r"from-v(\d+)-to-v(\d+)$", scope)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            if lo <= verse <= hi:
                return True
            continue
    return False


def is_aramaic_clause(clause: dict, book_folder: str, chapter: int) -> bool:
    """True if the clause dict's verse is in a held Aramaic range.

    Convenience wrapper for the binding-rule call site.
    """
    return is_aramaic_verse(book_folder, chapter, clause["verse"])
