#!/usr/bin/env python3
"""Keep new line breaks; restore each token's byte-form from HEAD.

WHY THIS EXISTS. Seven v2-pipeline-draft Genesis files carried real colometric
work -- 10 line-structure changes -- with Unicode normalization riding along
that nobody asked for. 36 of 2569 tokens had U+05BC (dagesh) and U+05B6 (segol)
swapped into NFC canonical order.

That is canonically equivalent, so it renders identically and no validator that
normalizes would notice. It is still wrong here, because source parity is the
correctness gate and the source disagrees:

    TAHOT_Gen-Deu.txt   dagesh+segol 7222   segol+dagesh 0
    HEAD                dagesh+segol    5   segol+dagesh 0
    working tree        dagesh+segol    4   segol+dagesh 1

HEAD matched the source. The edit drifted one token away from it. Committing
that would put a byte-level divergence from TAHOT into the corpus for no
editorial gain, and byte-exact comparisons against source would start failing
somewhere far from here.

So: take the working tree's LINE STRUCTURE, and every token's bytes from HEAD.
A token that differs by anything more than normalization is NOT substituted --
that would be silently discarding real editorial work. Those are reported and
the file is left alone.

    python restore_source_normalization.py --calibrate
    python restore_source_normalization.py <path>...      # rewrite
    python restore_source_normalization.py --check <path>...
"""

import argparse
import re
import subprocess
import sys
import unicodedata as ud

TOKEN_SPLIT = re.compile(r"(\s+)")


def head_text(path: str) -> str:
    """Read the committed version. as_posix matters on Windows -- git show does
    not accept backslash paths."""
    p = path.replace("\\", "/")
    r = subprocess.run(["git", "show", f"HEAD:{p}"],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"not in HEAD: {path}")
    return r.stdout


def restore(old_text: str, new_text: str):
    """Return (rewritten, n_restored, real_diffs).

    real_diffs is a list of (index, head_token, new_token) for tokens that are
    NOT canonically equivalent. If it is non-empty the caller must not write --
    the two files disagree about something other than encoding, and this tool
    has no business picking a winner."""
    ow, nw = old_text.split(), new_text.split()
    if len(ow) != len(nw):
        return None, 0, [("<count>", len(ow), len(nw))]

    real, restored = [], 0
    for i, (a, b) in enumerate(zip(ow, nw)):
        if a == b:
            continue
        if ud.normalize("NFC", a) == ud.normalize("NFC", b):
            restored += 1
        else:
            real.append((i, a, b))
    if real:
        return None, restored, real

    # Walk the new text preserving every whitespace run exactly, swapping each
    # token for its HEAD byte-form. Line structure therefore survives intact.
    out, k = [], 0
    for piece in TOKEN_SPLIT.split(new_text):
        if piece and not piece.isspace():
            out.append(ow[k])
            k += 1
        else:
            out.append(piece)
    return "".join(out), restored, []


def calibrate() -> bool:
    """Poles on the substitution. The known-bad ones matter most: this tool
    overwrites corpus text, so it must refuse anything it cannot prove is
    encoding-only."""
    ok = True
    dag, seg = "ּ", "ֶ"
    a = "מִט" + dag + seg          # HEAD order
    b = "מִט" + seg + dag          # NFC order
    cases = [
        (f"x {a} y", f"x\n{b}\ny", True, 1, 0,
         "mark-order diff restored, new line breaks kept"),
        (f"x {a} y", f"x\n{a}\ny", True, 0, 0,
         "identical tokens, only line breaks change"),
        (f"x {a} y", f"x {a} z", False, 0, 1,
         "a genuinely different token is REFUSED, not overwritten"),
        (f"x {a} y", f"x {a} y z", False, 0, 1,
         "differing token count is REFUSED"),
    ]
    for old, new, should_write, want_restored, want_real, why in cases:
        res, n, real = restore(old, new)
        hit = (res is not None) == should_write and n == want_restored and len(real) == want_real
        if hit and res is not None:
            hit = res.split() == old.split() and res.count("\n") == new.count("\n")
        ok &= hit
        print(f"  [{'PASS' if hit else 'FAIL'}] {why}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    args = ap.parse_args()

    if args.calibrate:
        print("calibration -- restore encoding only, refuse everything else")
        ok = calibrate()
        print("\nCALIBRATED" if ok else "\nMISCALIBRATED")
        return 0 if ok else 1

    if not args.paths:
        ap.error("paths required (or --calibrate)")
    if not calibrate():
        print("MISCALIBRATED -- refusing to touch corpus text", file=sys.stderr)
        return 1
    print()

    bad = 0
    for path in args.paths:
        new = open(path, encoding="utf-8").read()
        res, n, real = restore(head_text(path), new)
        name = path.replace("\\", "/").split("/")[-1]
        if real:
            bad += 1
            print(f"    {name:18} REFUSED -- {len(real)} non-encoding difference(s)")
            for i, a, b in real[:3]:
                print(f"        token {i}: HEAD {a!r} vs now {b!r}")
            continue
        if n == 0:
            print(f"    {name:18} nothing to restore")
            continue
        if not args.check:
            open(path, "w", encoding="utf-8", newline="").write(res)
        print(f"    {name:18} {n} token(s) {'would be' if args.check else ''} restored to source form")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
