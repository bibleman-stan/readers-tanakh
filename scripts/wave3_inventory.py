"""Wave 3 inventory script — collect REVIEW-REQUIRED findings per book across all validators."""
import sys
import json
import subprocess
from collections import defaultdict, Counter
import os

VALIDATORS = [
    'validators/colometry/validate_construct_chain.py',
    'validators/colometry/validate_speech_intro_framing.py',
    'validators/colometry/validate_cross_verse_continuity.py',
    'validators/colometry/validate_complement_integrity.py',
    'validators/colometry/validate_wayehi_protasis.py',
]

def extract_book(filepath):
    """Extract book directory name from filepath like data/text-files/v2/he/01-genesis/..."""
    parts = filepath.replace('\\', '/').split('/')
    # Look for the tier-leaf directory ('he' or 'he-baseline'), then book is the next part
    for i, p in enumerate(parts):
        if p in ('he', 'he-baseline'):
            if i + 1 < len(parts):
                return parts[i + 1]
    return None

def main():
    all_rr = []
    all_strong = []

    for v in VALIDATORS:
        vname = os.path.basename(v).replace('.py', '')
        result = subprocess.run(
            ['py', '-3', v, '--json', '--v2'],
            capture_output=True, text=True, encoding='utf-8'
        )
        # Exit code 1 = findings found (expected), 2 = setup error
        if result.returncode == 2:
            print(f"WARNING: {vname} setup error: {result.stderr[:200]}", file=sys.stderr)
            continue
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"WARNING: {vname} JSON parse error: {e}", file=sys.stderr)
            continue

        findings = data.get('findings', [])
        for f in findings:
            tag = f.get('tag', '')
            sev = f.get('severity', '')
            f['_validator'] = vname
            if tag == 'REVIEW-REQUIRED' or sev == 'REVIEW-REQUIRED':
                all_rr.append(f)
            elif 'STRONG' in tag or 'STRONG' in sev:
                all_strong.append(f)

    print(f"Total REVIEW-REQUIRED: {len(all_rr)}")
    print(f"Total STRONG candidates: {len(all_strong)}")

    # By book
    by_book_rr = Counter()
    for f in all_rr:
        book = extract_book(f.get('file', ''))
        if book:
            by_book_rr[book] += 1

    print()
    print("REVIEW-REQUIRED by book:")
    for book, cnt in sorted(by_book_rr.items()):
        print(f"  {book}: {cnt}")

    # By validator
    by_v_rr = Counter(f['_validator'] for f in all_rr)
    print()
    print("REVIEW-REQUIRED by validator:")
    for v, cnt in by_v_rr.most_common():
        print(f"  {v}: {cnt}")

    # By subcase (construct chain)
    cc_rr = [f for f in all_rr if f['_validator'] == 'validate_construct_chain']
    cc_subcases = Counter(f.get('subcase', '?') for f in cc_rr)
    print()
    print("Construct chain REVIEW-REQUIRED subcases:")
    for sc, cnt in cc_subcases.most_common():
        print(f"  {sc}: {cnt}")

    # Speech intro subcases
    si_rr = [f for f in all_rr if f['_validator'] == 'validate_speech_intro_framing']
    si_subcases = Counter(f.get('subcase', '?') for f in si_rr)
    print()
    print("Speech intro REVIEW-REQUIRED subcases:")
    for sc, cnt in si_subcases.most_common():
        print(f"  {sc}: {cnt}")

    # Return data for use in other analysis
    return all_rr, all_strong, by_book_rr

if __name__ == '__main__':
    main()
