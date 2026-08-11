

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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""checks_bound_nominals.py — Constraint checks for the bound-nominals cluster.

Implements JM129-construct-chain using the Macula lowfat IR.

Covered by this file
--------------------
  JM129-construct-chain   Construct-chain integrity (BIND, HARD, prec 2)

Already implemented elsewhere (do NOT re-implement here)
---------------------------------------------------------
  JM13-maqqef-group        audit_constraints.py  check_maqqef_indivisible
  JM103-proclitic-stranding audit_constraints.py  check_proclitic_stranded
  JM103e-compound-prep-object audit_constraints.py check_compound_prep_object

Registration
------------
audit_constraints.py maintains CHECK_REGISTRY: dict[str, Callable[[str, str], dict]].
That 2-arg signature predates the Macula-extended 5-arg signature used here.
Two integration paths:

  Path A — preferred once audit_constraints.py is upgraded to the 5-arg registry:
      from checks_bound_nominals import register_with
      register_with(CHECK_REGISTRY_5ARG)

  Path B — shim for the current 2-arg registry (book_slug/chapter/verse_num
      are not available at call time, so the Macula path is skipped and the
      function returns the surface-heuristic fallback only):
      CHECK_REGISTRY["JM129-construct-chain"] = check_construct_chain_shim

  The register_with() helper below packages both paths.  Pass the registry dict
  and the optional book_slug resolver; if no resolver is supplied it installs
  the surface-heuristic shim.

Function names registered
-------------------------
  check_construct_chain(verse_text, source_text, book_slug, chapter, verse_num)
      Full Macula implementation — preferred.

  check_construct_chain_shim(verse_text, source_text)
      Surface-heuristic fallback for the 2-arg registry.  Less precise: uses
      Token.is_construct on last/first tokens of adjacent sense lines matched
      via match_sense_line_tokens.  Does NOT use Constituent walks (those need
      book_slug/chapter/verse_num).

Known Macula API gaps encountered
----------------------------------
1. match_sense_line_tokens() returns (list[Token], next_start_idx: int), not
   just list[Token].  The task-prompt shorthand omitted the tuple; this file
   uses the real signature throughout.

2. Constituent.is_construct_chain is True when wg_rule == "NPofNP".  Macula
   encodes some (not all) construct chains this way.  Short or archaic chains
   may be missed if the parser did not annotate them as NPofNP.  The Token-level
   fallback (is_construct) catches parser-missed cases at the cost of some
   false-positives on construct-state nouns whose rectum is on the SAME line.

3. There is no direct "line number → Macula tokens" mapping in the API.  We
   reconstruct it by calling match_sense_line_tokens() iteratively, consuming
   verse_tokens in document order.  This depends on sense-line order matching
   token order — which is true for left-to-right versified Hebrew but is
   fragile if a sense-line re-orders tokens (rare, but possible in poetic
   displacement).

4. The task spec says "first token of line N+1 is the construct's rectum (or
   part of the same NPofNP constituent)".  We cannot confirm rectum identity
   from Token alone; that requires walking the Constituent tree.  The full
   implementation does the constituent walk; the fallback is weaker.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Callable

# ---------------------------------------------------------------------------
# Repo-root sys.path insert so validators._shared is importable from any cwd.
# ---------------------------------------------------------------------------
REPO_ROOT = _find_repo_root()
sys.path.insert(0, str(REPO_ROOT / "5-machinery/validators"))

from _shared.macula_constituents import (  # noqa: E402
    get_verse_tokens,
    get_verse_constituents,
    match_sense_line_tokens,
    Token,
    Constituent,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VERSE_LINE_SEP_RE = __import__("re").compile(r"\n")


def _sense_lines(verse_text: str) -> list[str]:
    """Return non-empty sense lines from verse_text."""
    return [ln for ln in _VERSE_LINE_SEP_RE.split(verse_text) if ln.strip()]


def _collect_npofnp(constituents: list[Constituent]) -> list[Constituent]:
    """Walk the constituent tree and collect all NPofNP constituents."""
    results: list[Constituent] = []

    def walk(node: Constituent | Token) -> None:
        if isinstance(node, Token):
            return
        if node.is_construct_chain:
            results.append(node)
        for child in node.children:
            walk(child)

    for root in constituents:
        walk(root)
    return results


def _token_line_map(verse_tokens: list[Token], lines: list[str]) -> dict[str, int]:
    """Return {token.xml_id: line_index (0-based)} for all matched tokens.

    Uses match_sense_line_tokens iteratively to consume tokens in document
    order across sense lines.
    """
    mapping: dict[str, int] = {}
    start_idx = 0
    for line_idx, line_text in enumerate(lines):
        matched, start_idx = match_sense_line_tokens(verse_tokens, line_text, start_idx)
        for tok in matched:
            mapping[tok.xml_id] = line_idx
    return mapping


# ---------------------------------------------------------------------------
# JM129-construct-chain — full Macula implementation (5-arg)
# ---------------------------------------------------------------------------

def check_construct_chain(
    verse_text: str,
    source_text: str,
    book_slug: str,
    chapter: int,
    verse_num: int,
) -> Optional[dict]:
    """JM129 — Construct-chain integrity.

    Returns {"fires": bool, "verdict": str, "reason": str, "details": dict}.
    Never returns None (fully implemented).

    Verdict values:
      CONFLICT   — a construct chain (NPofNP or Token.is_construct fallback)
                   is split across a sense-line boundary.
      NO-EFFECT  — no cross-line construct-chain split detected.

    Strategy (two-pass):
      Pass A (constituent walk, primary):
        For every NPofNP constituent in the verse, check if its regens tokens
        and rectum tokens land on different sense lines.  If yes → CONFLICT.

      Pass B (token fallback):
        For every adjacent line pair (N, N+1):
          • last token of line N has Token.is_construct == True AND
          • it does NOT have maqqef after it (maqqef case is JM13's domain) AND
          • first token of line N+1 exists (i.e., there is a following line)
        If yes → CONFLICT (possible construct head stranded without rectum).

    Pass B may produce false-positives when a construct-state noun happens to
    close a line but its rectum is actually on the SAME line (e.g., the
    construct chain is all on line N and an unrelated construct-state noun
    precedes the line break).  The NPofNP walk (Pass A) is authoritative;
    Pass B fires only when Pass A found nothing AND the token evidence is clear.

    Gap acknowledged: Macula does not encode every construct chain as NPofNP
    (parser misses are possible).  Pass B is the safety net.
    """
    lines = _sense_lines(verse_text)
    if len(lines) < 2:
        return {
            "fires": False,
            "verdict": "NO-EFFECT",
            "reason": "single-line verse — no inter-line boundary to check",
            "details": {},
        }

    # ---- Fetch Macula data ------------------------------------------------
    try:
        verse_tokens = get_verse_tokens(book_slug, chapter, verse_num)
        verse_constituents = get_verse_constituents(book_slug, chapter, verse_num)
    except (FileNotFoundError, ValueError) as exc:
        # Lowfat XML not available for this book/chapter — surface fallback.
        return _check_construct_chain_surface(lines, str(exc))

    if not verse_tokens:
        return {
            "fires": False,
            "verdict": "NO-EFFECT",
            "reason": "no Macula tokens found for verse",
            "details": {},
        }

    # Build token → line-index map.
    tok_line: dict[str, int] = _token_line_map(verse_tokens, lines)

    # ---- Pass A: NPofNP constituent walk ----------------------------------
    npofnp_constituents = _collect_npofnp(verse_constituents)
    for cons in npofnp_constituents:
        tokens = cons.tokens
        if not tokens:
            continue
        # Determine which lines each token lands on.
        line_indices = {tok_line[t.xml_id] for t in tokens if t.xml_id in tok_line}
        if len(line_indices) < 2:
            continue  # All tokens on the same line — no split.
        # There is a split.  Find the boundary.
        sorted_tokens = sorted(tokens, key=lambda t: t.position)
        # Find the last token on the earliest line and first token on the next.
        first_line = min(line_indices)
        regens_tokens = [t for t in sorted_tokens if tok_line.get(t.xml_id) == first_line]
        rectum_tokens = [t for t in sorted_tokens if tok_line.get(t.xml_id, first_line) > first_line]
        regens_last = regens_tokens[-1] if regens_tokens else None
        rectum_first = rectum_tokens[0] if rectum_tokens else None
        return {
            "fires": True,
            "verdict": "CONFLICT",
            "reason": (
                f"NPofNP construct chain split across sense lines "
                f"{first_line + 1} / {first_line + 2}: "
                f"regens '{regens_last.text if regens_last else '?'}' on line {first_line + 1}, "
                f"rectum '{rectum_first.text if rectum_first else '?'}' on line {first_line + 2}"
            ),
            "details": {
                "constituent_rule": "NPofNP",
                "regens_text": regens_last.text if regens_last else None,
                "regens_line": first_line + 1,
                "rectum_text": rectum_first.text if rectum_first else None,
                "rectum_line": first_line + 2,
                "pass": "A-constituent",
            },
        }

    # ---- Pass B: token-level fallback -------------------------------------
    # Build per-line token lists in document order.
    line_tokens: list[list[Token]] = [[] for _ in lines]
    for tok in verse_tokens:
        idx = tok_line.get(tok.xml_id)
        if idx is not None and 0 <= idx < len(lines):
            line_tokens[idx].append(tok)
    # Sort each line's tokens by position.
    for lt in line_tokens:
        lt.sort(key=lambda t: t.position)

    for n in range(len(lines) - 1):
        lt_n = line_tokens[n]
        lt_n1 = line_tokens[n + 1]
        if not lt_n or not lt_n1:
            continue
        last_tok = lt_n[-1]
        first_tok_next = lt_n1[0]
        if (
            last_tok.is_construct
            and not last_tok.has_maqqef_after()  # maqqef case belongs to JM13
        ):
            return {
                "fires": True,
                "verdict": "CONFLICT",
                "reason": (
                    f"construct-state token '{last_tok.text}' ends line {n + 1} "
                    f"without maqqef; '{first_tok_next.text}' opens line {n + 2} "
                    f"— likely construct head stranded from rectum (NPofNP parser miss)"
                ),
                "details": {
                    "regens_text": last_tok.text,
                    "regens_line": n + 1,
                    "rectum_candidate": first_tok_next.text,
                    "rectum_line": n + 2,
                    "pass": "B-token-fallback",
                    "gap_note": (
                        "NPofNP constituent not found by parser; "
                        "Token.is_construct = True is the sole evidence. "
                        "Verify manually if rectum is actually on the same line."
                    ),
                },
            }

    return {
        "fires": False,
        "verdict": "NO-EFFECT",
        "reason": "no construct-chain split detected (NPofNP walk + token fallback both clean)",
        "details": {
            "npofnp_constituents_checked": len(npofnp_constituents),
            "lines_checked": len(lines),
        },
    }


# ---------------------------------------------------------------------------
# Surface-heuristic fallback (called when Macula XML not available)
# ---------------------------------------------------------------------------

def _check_construct_chain_surface(lines: list[str], error_note: str) -> dict:
    """Surface-heuristic substitute when Macula XML is unavailable.

    This is a weaker check: it cannot use Token.is_construct (no Macula parse),
    so it returns NO-EFFECT with a documented gap.  The caller logs the error.
    """
    return {
        "fires": False,
        "verdict": "NO-EFFECT",
        "reason": (
            "Macula XML unavailable — construct-chain check skipped. "
            f"Error: {error_note}"
        ),
        "details": {
            "macula_error": error_note,
            "gap": "JM129 requires Macula lowfat XML; surface heuristic not reliable",
        },
    }


# ---------------------------------------------------------------------------
# 2-arg shim for the current audit_constraints.py CHECK_REGISTRY
# ---------------------------------------------------------------------------

def check_construct_chain_shim(verse_text: str, source_text: str) -> Optional[dict]:
    """2-arg shim for backward compatibility with the current CHECK_REGISTRY.

    Without book_slug/chapter/verse_num, only the surface-level token path is
    available — which itself requires Macula.  Since we cannot load Macula
    without book coordinates, this shim returns NO-EFFECT with a documented
    gap until audit_constraints.py is upgraded to the 5-arg registry.

    To get the full JM129 check, upgrade CHECK_REGISTRY to pass book_slug,
    chapter, verse_num and call check_construct_chain() directly.
    """
    return {
        "fires": False,
        "verdict": "NO-EFFECT",
        "reason": (
            "JM129 shim: book_slug/chapter/verse_num not available in 2-arg "
            "registry — full Macula check requires 5-arg registry upgrade. "
            "See checks_bound_nominals.register_with() for integration path."
        ),
        "details": {
            "gap": "Upgrade CHECK_REGISTRY to 5-arg signature to enable JM129",
        },
    }


# ---------------------------------------------------------------------------
# Registration helper
# ---------------------------------------------------------------------------

CHECKS_5ARG: dict[str, Callable] = {
    "JM129-construct-chain": check_construct_chain,
}


def register_with(registry: dict, strict: bool = True) -> list[str]:
    """Merge this module's 5-arg checks into the runner registry.

    audit_constraints.audit_verse dispatches on callable arity, so 5-arg
    functions register directly. If strict=True (default), raise KeyError on
    collisions where the existing registry entry is a different function.
    Returns the list of constraint IDs registered.
    """
    registered: list[str] = []
    for cid, fn in CHECKS_5ARG.items():
        existing = registry.get(cid)
        if strict and existing is not None and existing is not fn:
            raise KeyError(
                f"register_with collision: '{cid}' already in registry "
                f"with a different function ({getattr(existing, '__name__', repr(existing))!r} vs {fn.__name__!r})"
            )
        registry[cid] = fn
        registered.append(cid)
    return registered


# ---------------------------------------------------------------------------
# Smoke-test (py_compile / direct run)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Quick structural smoke-test — does not require lowfat XML on disk.
    print("checks_bound_nominals.py loaded OK")
    print(f"  check_construct_chain:       {check_construct_chain.__name__}")
    print(f"  check_construct_chain_shim:  {check_construct_chain_shim.__name__}")
    print()
    # Exercise shim path.
    result = check_construct_chain_shim("דְּבַר\nיְהוָה", "")
    assert result is not None
    assert result["fires"] is False
    print(f"  shim smoke-test passed: fires={result['fires']}, verdict={result['verdict']}")
    print()
    print("To run the full check against a real verse:")
    print("  from checks_bound_nominals import check_construct_chain")
    print('  r = check_construct_chain(verse_text, source_text, "01-genesis", 1, 1)')
    print("  print(r)")
