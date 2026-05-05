#!/usr/bin/env python3
"""Count findings from validate_interrogative_clause across all v1 books."""
import subprocess, json, sys
from pathlib import Path
from collections import Counter

REPO = Path(__file__).resolve().parent.parent
V1_DIR = REPO / "data" / "text-files" / "v1" / "he-baseline"

books = sorted(d.name for d in V1_DIR.iterdir() if d.is_dir())
total = []
for book in books:
    result = subprocess.run(
        ["py", "-3", "validators/colometry/validate_interrogative_clause.py", "--book", book, "--json"],
        capture_output=True, text=True, encoding="utf-8",
        cwd=str(REPO)
    )
    out = result.stdout.strip()
    if out.startswith("{"):
        doc = json.loads(out)
        total.extend(doc.get("findings", []))

print(f"Total findings: {len(total)}")
sev = Counter(f["severity"] for f in total)
for k, v in sev.items():
    print(f"  {k}: {v}")
print("Top books:")
books_c = Counter(f["book"] for f in total)
for k, v in sorted(books_c.items(), key=lambda x: -x[1])[:10]:
    print(f"  {k}: {v}")
