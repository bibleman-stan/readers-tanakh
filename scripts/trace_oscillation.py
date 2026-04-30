#!/usr/bin/env python3
"""Diagnostic: simulate post-S1 Gen 1:26 split state and report which merge
specs would fire on each adjacent pair, to identify the oscillation source.

Usage:
  PYTHONIOENCODING=utf-8 py -3 scripts/trace_oscillation.py
"""
from __future__ import annotations
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from validators._shared.spec_runner import SpecRunner  # noqa: E402

# Post-S1 Gen 1:26 — the 5-cola enumeration we WANT to be stable
POST_S1_GEN_1_26 = """1:26
וַיֹּ֣אמֶר אֱלֹהִ֔ים
נַֽעֲשֶׂ֥ה אָדָ֛ם בְּצַלְמֵ֖נוּ כִּדְמוּתֵ֑נוּ
וְיִרְדּוּ֩ בִדְגַ֨ת הַיָּ֜ם
וּבְע֣וֹף הַשָּׁמַ֗יִם
וּבַבְּהֵמָה֙
וּבְכָל־הָאָ֔רֶץ
וּבְכָל־הָרֶ֖מֶשׂ
הָֽרֹמֵ֥שׂ עַל־הָאָֽרֶץ׃
"""

def main():
    # Use a temp dir INSIDE the repo so spec_runner's relative_to(cwd) works
    with tempfile.TemporaryDirectory(dir=str(ROOT)) as tmpdir:
        # Build a minimal v2/he-style corpus with one book one chapter
        corpus = Path(tmpdir) / "corpus"
        book_dir = corpus / "01-genesis"
        book_dir.mkdir(parents=True)
        (book_dir / "genesis-01.txt").write_text(POST_S1_GEN_1_26, encoding="utf-8")

        runner = SpecRunner(ROOT / "validators/specs")

        # All findings
        findings = runner.run_corpus(corpus)

        print(f"Total findings on simulated post-S1 Gen 1:26: {len(findings)}\n")
        for f in findings:
            arrow = "MERGE→" if "MERGE" in f.severity else ("SPLIT→" if "SPLIT" in f.severity else f.severity)
            print(f"  {arrow} {f.rule}/{f.subcase} [{f.severity}]")
            print(f"     L({f.line}) prior: {f.prior_line!r}")
            if f.next_line:
                print(f"            next:  {f.next_line!r}")
            if f.split_positions:
                print(f"            split_positions: {f.split_positions}")
            print(f"     annotation: {f.annotation}")
            print()

if __name__ == "__main__":
    main()
