"""
Sample validator findings stratified by the 6-cluster scheme for audit dispatch.

Reads validator output (one finding per line, must contain a v2/heb path like
`data/text-files/v2/heb/{NN}-{book}/{book}-{NN}.txt:{line}  ...`), routes each
finding to its cluster (1=Torah / 2=Former Prophets / 3=Latter Prophets /
4=Writings prose / 5=Sifrei Emet / 6=Embedded Poetry), and samples N random
findings per cluster (default 5 → 30 total) for parallel-Sonnet audit.

Usage:
    py -3 5-machinery/scripts/sample_findings_by_cluster.py <input-file>
    py -3 5-machinery/scripts/sample_findings_by_cluster.py <input-file> --per-cluster 10
    py -3 5-machinery/scripts/sample_findings_by_cluster.py - < piped-output.txt
"""
import argparse
import random
import re
import sys

CLUSTER6_WHOLE_BOOKS = {22, 25}  # SoS=22, Lam=25

CLUSTER6_CHAPTER_OVERRIDES = {
    (2, 15), (5, 32), (5, 33), (7, 5), (9, 2),
    (10, 22), (23, 12), (35, 3), (21, 3),
}

CLUSTER1_BOOKS = set(range(1, 6))
CLUSTER2_BOOKS = {6, 7, 9, 10, 11, 12}
CLUSTER3_BOOKS = {23, 24, 26, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39}
CLUSTER4_BOOKS = {8, 17, 27, 15, 16, 13, 14, 21}
CLUSTER5_BOOKS = {19, 20, 18}

FINDING_RE = re.compile(
    r"data/text-files/v2/heb/(\d+)-(\w+)/\w+-(\d+)\.txt:(\d+)\s+\S+\s+\S+\s+(.+)"
)


def get_cluster(book_num: int, chapter: int) -> int:
    if book_num in CLUSTER6_WHOLE_BOOKS:
        return 6
    if (book_num, chapter) in CLUSTER6_CHAPTER_OVERRIDES:
        return 6
    if book_num in CLUSTER1_BOOKS:
        return 1
    if book_num in CLUSTER2_BOOKS:
        return 2
    if book_num in CLUSTER3_BOOKS:
        return 3
    if book_num in CLUSTER4_BOOKS:
        return 4
    if book_num in CLUSTER5_BOOKS:
        return 5
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="Path to findings file, or '-' for stdin")
    ap.add_argument("--per-cluster", type=int, default=5, help="Findings to sample per cluster (default 5)")
    ap.add_argument("--seed", type=int, default=42, help="Random seed (default 42)")
    args = ap.parse_args()

    random.seed(args.seed)

    if args.input == "-":
        text = sys.stdin.read()
    else:
        with open(args.input, encoding="utf-8") as f:
            text = f.read()

    findings = []
    for line in text.splitlines():
        m = FINDING_RE.search(line)
        if not m:
            continue
        book_num = int(m.group(1))
        book_name = m.group(2)
        chapter = int(m.group(3))
        line_num = int(m.group(4))
        detail = m.group(5)
        findings.append({
            "book_num": book_num,
            "book": book_name,
            "chapter": chapter,
            "line": line_num,
            "detail": detail,
            "cluster": get_cluster(book_num, chapter),
        })

    by_cluster: dict[int, list] = {}
    for f in findings:
        by_cluster.setdefault(f["cluster"], []).append(f)

    print("=== CLUSTER COUNTS ===")
    for c in sorted(by_cluster.keys()):
        print(f"Cluster {c}: {len(by_cluster[c])} findings")

    print(f"\n=== SAMPLE ({args.per_cluster} per cluster) ===")
    for c in range(1, 7):
        pool = by_cluster.get(c, [])
        n = min(args.per_cluster, len(pool))
        for f in random.sample(pool, n):
            path = f"data/text-files/v2/heb/{f['book_num']:02d}-{f['book']}/{f['book']}-{f['chapter']:02d}.txt"
            print(f"C{c}\t{f['book']}\t{f['chapter']}:{f['line']}\t{path}\t{f['detail']}")


if __name__ == "__main__":
    main()
