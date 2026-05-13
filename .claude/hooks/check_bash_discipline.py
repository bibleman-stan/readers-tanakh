#!/usr/bin/env python3
"""PreToolUse Bash discipline hook.

Mechanical forcing function that fires at the action site (the moment Claude
Code is about to execute a Bash tool call). Blocks anti-patterns documented
in handoffs/14-operational-protocols.md before they happen, instead of
detecting them after the fact.

Anti-patterns blocked:
  1. Multi-line Python heredocs (>=5 non-empty lines containing Python idioms)
     — per §E1-E2: should be persistent scripts under scripts/, not one-off
     bash heredocs (history shows they break on Windows /tmp ephemerality and
     apostrophe/Hebrew-text heredoc parsing).
  2. Cascade invocations (apply_specs / refresh_book / apply_validators with
     --all-books) on the main thread without parallel-justification — per
     §A2 mandatory two-phase pattern: should be 6 parallel cluster Agent
     dispatches, not one main-thread call.
  3. git status / git diff without summary flags — per §H3 verbose-by-default
     ingestion: default to --shortstat / --numstat / --stat / --porcelain /
     --name-only, or pipe to wc/head/grep for a count.
  4. Cascade invocations without recent adversarial-audit evidence in the
     transcript — per §A3 Step 0: before any non-trivial implementation,
     dispatch ≥2 parallel Agent calls (one message, multiple Agent
     tool_use blocks) OR declare 'Audit-skippable: <reason>'. Hook walks
     recent transcript turns and counts Agent dispatches; if <2 found and
     no '# audit-skippable:' prefix, the cascade is refused.

Override mechanisms (visible in JSONL trace for later audit):
  - Universal:        prefix command body with '# disciplined-allow: <reason>'
  - Cascade-parallel: prefix command body with '# split-justified: <reason>'
  - Audit-skippable:  prefix command body with '# audit-skippable: <reason>'

Output protocol:
  Block: exit code 2, message on stderr (Claude Code surfaces this to the
         model and refuses the tool call).
  Allow: exit code 0, no output.

Hook input (JSON on stdin):
  { "session_id": "...", "transcript_path": "...", "cwd": "...",
    "hook_event_name": "PreToolUse", "tool_name": "Bash",
    "tool_input": { "command": "...", "description": "..." } }
"""

from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path


def _count_recent_agent_dispatches(transcript_path: str, lookback_lines: int = 200) -> int:
    """Count Agent tool_use entries in the most recent N JSONL transcript lines.

    Walks the tail of the JSONL (transcripts grow large; we only care about
    the recent window). Counts every assistant message's tool_use blocks
    where name == "Agent". Returns 0 if path missing / unreadable / malformed
    so a transcript-access failure does not falsely block the gate.
    """
    if not transcript_path:
        return 0
    p = Path(transcript_path)
    if not p.exists():
        return 0
    try:
        with p.open("rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            tail_size = min(size, 5_000_000)  # ~5MB tail
            fh.seek(size - tail_size)
            tail_bytes = fh.read()
        # Decode tolerantly; partial leading line is fine — we'll skip it on parse failure.
        tail_text = tail_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return 0
    lines = tail_text.splitlines()[-lookback_lines:]
    count = 0
    for line in lines:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except Exception:
            continue
        if entry.get("type") != "assistant":
            continue
        msg = entry.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if (
                isinstance(block, dict)
                and block.get("type") == "tool_use"
                and block.get("name") == "Agent"
            ):
                count += 1
    return count


_QUOTED_PHRASE_RE = re.compile(r'"([^"]{20,})"')
_OVERRIDE_TOKENS = (
    "# disciplined-allow:",
    "# split-justified:",
    "# audit-skippable:",
    "# judgment-required:",  # Agent tool bypass
    "# validator-extension-justified:",  # Write tool bypass
    "# instance-fix-justified:",  # Cascade-iteration bypass
)

# Bypass-substance validation (per 2026-05-05 meta-audit Hook-(ii) verdict §C).
# Override comments may pass quote validation but still be substantively
# vacuous ("# judgment-required: I need to" / "# validator-extension-justified:
# this is needed"). Require the reason to name a recognized criterion.
_JUDGMENT_SUBSTANCE_RE = re.compile(
    r"\b(classif|synthesi[sz]|hostile.audit|adversarial|precedence|edge.case|"
    r"ambigu|multi.source|cross.rule|cross.lens|methodology|FP.rate|"
    r"hand.review|per.item|judgment.call)\b",
    re.IGNORECASE,
)
_VALIDATOR_EXT_SUBSTANCE_RE = re.compile(
    r"\b(extend|new.arm|new.subcase|distinct.failure|orthogonal|cannot.be.added|"
    r"existing.validator.misses|fundamentally.different)\b",
    re.IGNORECASE,
)
_INSTANCE_FIX_SUBSTANCE_RE = re.compile(
    r"\b(engine.tried|unrelated.bugs|stan.directed|cross.helper|"
    r"revert.rerun|walkback|verify|verification)\b",
    re.IGNORECASE,
)
# Macula-checked bypass for atu-method/atu_method/* edits. Per CLAUDE.md
# "Use the primitive, not the heuristic" rule (codified 2026-05-12 after
# the distribute.py iteration cycle): edits to cross-corpus shared
# infrastructure require evidence in recent assistant text that Macula
# constituent-tree query was considered — OR a closed-vocab bypass naming
# why Macula doesn't apply.
_MACULA_CHECKED_SUBSTANCE_RE = re.compile(
    r"\b(macula.checked|macula.queried|macula.extended|macula.consulted|"
    r"macula.doesn.?t.cover|macula.does.not.cover|"
    r"not.applicable.greek.side|greek.side.only|"
    r"primitive.already.in.use|trivial.non.structural|"
    r"audit.dispatched.with.macula.named|docstring.only|formatting.only)\b",
    re.IGNORECASE,
)

# Cascade-invocation iteration tripwire (per 2026-05-05 Sifrei-Emet purge
# arc + Opus hook audit). Detects the SECOND `apply_specs.py --book <X>`
# / `apply_validators.py --book <X>` / `refresh_book.py --book <X>` against
# the same `<X>` in the session window, when no Edit between the two
# invocations touched engine-level files. The pattern is: cascade reveals
# FP class → fix per-spec → re-cascade → same FP class → fix per-spec →
# re-cascade ... vs. cascade reveals FP class → fix engine → re-cascade.
# The hook fires at the moment of the second cascade with no engine fix
# in between — exactly when the class-vs-instance question should fire.
_CASCADE_BOOK_RE = re.compile(
    r"\b(apply_specs|apply_validators|refresh_book)\.py\b[^|;&\n]*?--book\s+(\S+)"
)
_ENGINE_FILE_RE = re.compile(
    r"(scripts/spec_runner\.py|scripts/apply_validators\.py|"
    r"scripts/apply_specs\.py|validators/_shared/[\w.]+\.py|"
    r"scripts/regenerate_english\.py|"
    r"scripts/propagate_editorial_layers\.py)"
)
_INSTANCE_FIX_BYPASS = "# instance-fix-justified:"

# Agent-tool mechanical-vocabulary trigger (per 2026-05-04 colonoscopy audit
# §3.2 Hook (ii) — scripts-default-vs-agents). Matches prompts that describe
# a count/list/glob/scan/check deliverable — exactly the failure surface
# where `feedback_scripts_default_agents_only_for_judgment.md` is repeatedly
# violated. Initial regex (2026-05-05 audit verdict) was too narrow on the
# verb side; widened post-audit to include extraction verbs (scan, check,
# read, look up, pull, return, retrieve) that the colonoscopy memory
# explicitly cites as Agent-vs-script anti-patterns. Still NOT included:
# the broader "find Z" / "tell me about Z" which routinely tag judgment
# calls.
_AGENT_MECHANICAL_VOCAB_RE = re.compile(
    r"\b(count(?:\s+(?:of|all|the))?|list\s+all|list\s+every|how\s+many|"
    r"find\s+all|glob\s+for|enumerate(?:\s+all)?|"
    r"scan\s+(?:every|all|each|the)|"
    r"check\s+whether|check\s+if|"
    r"look\s+up|pull\s+(?:every|all|each|the)|"
    r"return\s+(?:every|all|each|the))\b",
    re.IGNORECASE,
)
_AGENT_PROMPT_LENGTH_THRESHOLD = 2000  # characters, not tokens
_AGENT_BYPASS_TOKEN = "# judgment-required:"


def _extract_recent_user_turns(transcript_path: str, lookback_lines: int = 500) -> list[str]:
    """Return text content of recent user-typed turns from JSONL transcript tail.

    Stream-reads the last ~5MB of the JSONL, filters to entries with type=user
    and extracts text content. Returns [] on any access failure.
    """
    if not transcript_path:
        return []
    p = Path(transcript_path)
    if not p.exists():
        return []
    try:
        with p.open("rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            tail_size = min(size, 5_000_000)
            fh.seek(size - tail_size)
            tail_bytes = fh.read()
        tail_text = tail_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return []
    user_texts: list[str] = []
    for line in tail_text.splitlines()[-lookback_lines:]:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except Exception:
            continue
        if entry.get("type") != "user":
            continue
        msg = entry.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if isinstance(content, str):
            user_texts.append(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")
                    if isinstance(text, str):
                        user_texts.append(text)
                elif isinstance(block, str):
                    user_texts.append(block)
    return user_texts


def _validate_override_quotes(command: str, transcript_path: str) -> str | None:
    """If override comment cites a quoted phrase, validate it against recent user turns.

    Applies to ALL override tokens (`# disciplined-allow:`, `# split-justified:`,
    `# audit-skippable:`, `# judgment-required:`, `# validator-extension-justified:`).
    The 2026-05-04 colonoscopy audit named the hallucinated-citation pattern as
    the central bypass exploit; same validator extends to all override surfaces.

    Returns an error message (str) if validation fails (override should be REFUSED).
    Returns None if no quote OR all cited quotes pass validation.
    """
    # Only count override tokens that appear at the START of a line (real
    # override comments live on their own line as shell preamble). Tokens
    # appearing inside a heredoc body (e.g., a commit message describing
    # the override mechanism) are not real overrides — skip them.
    has_real_override = any(
        re.search(r"(?m)^\s*" + re.escape(tok), command) for tok in _OVERRIDE_TOKENS
    )
    if not has_real_override:
        return None  # No real override comment present
    # Limit quote scan to the actual override-comment lines, not the whole
    # command (which may include heredoc-body strings that aren't overrides).
    override_lines: list[str] = []
    for line in command.splitlines():
        stripped = line.lstrip()
        if any(stripped.startswith(tok) for tok in _OVERRIDE_TOKENS):
            override_lines.append(stripped)
    scan_text = "\n".join(override_lines)
    quotes = _QUOTED_PHRASE_RE.findall(scan_text)
    if not quotes:
        return None  # Override has no quoted-phrase citation; nothing to validate
    user_turns = _extract_recent_user_turns(transcript_path)
    if not user_turns:
        return (
            "Override cites a quoted phrase but the transcript is unreadable; "
            "cannot validate the citation. Rewrite the override reason WITHOUT "
            "quotation marks (use paraphrase) or fix transcript_path access."
        )
    haystack = "\n".join(user_turns).lower()
    for quote in quotes:
        needle = quote.strip().lower()
        if len(needle) < 20:
            continue
        if needle in haystack:
            continue  # Verbatim match — pass
        # Fuzzy match via difflib.SequenceMatcher (Levenshtein-equivalent at high ratio)
        # Sliding window across haystack for performance.
        passed_fuzzy = False
        window_size = len(needle) + 10
        step = max(1, len(needle) // 4)
        for offset in range(0, max(1, len(haystack) - window_size + 1), step):
            window = haystack[offset:offset + window_size]
            if difflib.SequenceMatcher(None, needle, window).ratio() >= 0.92:
                passed_fuzzy = True
                break
        if not passed_fuzzy:
            preview = quote[:80] + ("..." if len(quote) > 80 else "")
            return (
                f"=== OVERRIDE QUOTE VALIDATION FAILED ===\n\n"
                f"Override comment cites Stan phrase: \"{preview}\"\n\n"
                f"This phrase is NOT present in the recent {len(user_turns)} user turns "
                f"of the transcript (no exact match, no fuzzy match at SequenceMatcher "
                f"ratio >= 0.92). The override mechanism does NOT accept unverifiable "
                f"Stan citations as of the 2026-05-04 colonoscopy audit hardening.\n\n"
                f"Either:\n"
                f"  (a) the phrase is paraphrased — REWRITE the override reason WITHOUT "
                f"quotation marks; OR\n"
                f"  (b) the phrase is hallucinated — ABORT the override, DROP the "
                f"comment, and use the un-overridden cluster-dispatch / fully-disciplined "
                f"path the gate is steering you toward.\n\n"
                f"Self-test before retrying: open the JSONL transcript, locate the actual "
                f"Stan turn you want to cite, copy-paste the verbatim text. If you can't "
                f"find it, the citation does not exist; do not override."
            )
    return None


def _validate_bypass_substance(text: str, token: str, substance_re: re.Pattern) -> str | None:
    """Verify an override comment's <reason> names a recognized criterion.

    Per 2026-05-05 meta-audit §C: override comments can pass quote validation
    yet be substantively vacuous. Require the reason text to match a closed
    list of recognized criteria. Skips validation if quoted phrases were
    used (those are validated separately by `_validate_override_quotes`).

    Only fires on tokens at line-start; tokens appearing inside heredoc
    bodies (e.g., a commit message describing the override mechanism) are
    not real overrides.
    """
    line_start_match = re.search(r"(?m)^\s*" + re.escape(token), text)
    if not line_start_match:
        return None
    idx = line_start_match.start()
    while idx < len(text) and text[idx] in " \t":
        idx += 1
    # Extract the rest of that line (the <reason>).
    line_end = text.find("\n", idx)
    reason = text[idx + len(token) : line_end if line_end > 0 else len(text)].strip()
    if not reason:
        return (
            f"Override token '{token}' is present with no reason. Provide a "
            f"<reason> after the colon describing why the bypass is justified."
        )
    # If reason contains a quoted phrase, defer to quote-validation.
    if _QUOTED_PHRASE_RE.search(reason):
        return None
    if not substance_re.search(reason):
        criteria_examples = {
            "# judgment-required:": "classify, synthesis, hostile-audit, adversarial, precedence, edge-case, ambiguous, multi-source, cross-rule, methodology, FP-rate, hand-review, per-item, judgment-call",
            "# validator-extension-justified:": "extend (existing), new-arm, new-subcase, distinct-failure, orthogonal, cannot-be-added (to existing), existing-validator-misses, fundamentally-different",
        }
        examples = criteria_examples.get(token, "(see hook source for accepted vocabulary)")
        return (
            f"=== BYPASS SUBSTANCE VALIDATION FAILED ===\n\n"
            f"Override comment '{token} {reason[:80]}' does not name a recognized "
            f"justification criterion. The bypass mechanism trusts your "
            f"self-report; this gate checks that the self-report names a "
            f"specific reason from a closed vocabulary, not just the word "
            f"'judgment' or 'extension'.\n\n"
            f"Accepted criteria (case-insensitive substring match):\n"
            f"  {examples}\n\n"
            f"ACTION: rewrite the bypass reason to name a specific criterion. "
            f"If the deliverable doesn't fit any of these, the bypass is "
            f"probably not the right move — re-think whether the gate is "
            f"actually wrong for this case."
        )
    return None


def _extract_last_assistant_text(transcript_path: str) -> str:
    """Return concatenated text content of the most recent assistant message.

    Used by Stop-hook gates that need to inspect the message Claude is about
    to send. Empty string on any access failure or if no assistant message
    is found in the JSONL tail.
    """
    if not transcript_path:
        return ""
    p = Path(transcript_path)
    if not p.exists():
        return ""
    try:
        with p.open("rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            tail_size = min(size, 5_000_000)
            fh.seek(size - tail_size)
            tail_bytes = fh.read()
        tail_text = tail_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return ""
    # Walk backwards through lines, find the most recent assistant message.
    lines = tail_text.splitlines()
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except Exception:
            continue
        if entry.get("type") != "assistant":
            continue
        msg = entry.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")
                    if isinstance(text, str):
                        parts.append(text)
            if parts:
                return "\n".join(parts)
    return ""


def _has_pending_todos(transcript_path: str) -> bool:
    """Heuristic: does the recent transcript show any pending (non-completed) TodoWrite todos?

    Walks JSONL tail backwards; the FIRST TodoWrite encountered is the
    current state of the todo list. If any todo has status != "completed",
    return True.

    Imperfect (no structured todo-state API per Claude Code; this is a
    JSONL-walk inference). False negatives possible if TodoWrite isn't
    being used. False positives possible if the most recent TodoWrite
    has stale "in_progress" entries that should be "completed."
    """
    if not transcript_path:
        return False
    p = Path(transcript_path)
    if not p.exists():
        return False
    try:
        with p.open("rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            tail_size = min(size, 5_000_000)
            fh.seek(size - tail_size)
            tail_bytes = fh.read()
        tail_text = tail_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return False
    for line in reversed(tail_text.splitlines()):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except Exception:
            continue
        if entry.get("type") != "assistant":
            continue
        msg = entry.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if (
                isinstance(block, dict)
                and block.get("type") == "tool_use"
                and block.get("name") == "TodoWrite"
            ):
                todos = block.get("input", {}).get("todos", [])
                if not isinstance(todos, list):
                    return False
                # Found the most recent TodoWrite; inspect its state.
                for todo in todos:
                    if isinstance(todo, dict):
                        status = todo.get("status", "")
                        if status and status != "completed":
                            return True
                return False  # All todos in latest TodoWrite are completed
    return False  # No TodoWrite found in recent window


# Permission-loop trigger: outgoing message ends with '?' (whitespace-trimmed).
_PERMISSION_LOOP_BYPASS = "<!-- question-required:"

# Counts-headline trigger: first paragraph contains a "leading" integer >= 100
# that is not immediately contextualized as a verse/chapter/line/word/file/book
# reference.
_COUNTS_HEADLINE_BYPASS = "<!-- counts-ok:"

# Pattern: an integer (possibly with thousands separators) that appears in
# context where it's clearly a quantity-as-headline rather than a reference.
# We catch numbers >= 100 that are NOT immediately preceded by reference
# vocabulary and NOT immediately followed by reference units.
_HEADLINE_NUMERIC_RE = re.compile(
    r"(?<![:.\-\d/])"   # not part of a verse-ref or version-ref
    r"\b(\d{1,3}(?:,\d{3})+|\d{3,})\b"  # 100+ (with or without commas)
    r"(?!\s*(?:[:.]\d|/))"  # not "1234:5" or "12.34" or "100/200"
)
# Reference-unit nouns that contextualize a number as not-a-headline.
_REFERENCE_UNIT_RE = re.compile(
    r"\s*(?:verse|verses|chapter|chapters|book|books|line|lines|word|words|"
    r"file|files|token|tokens|year|years|page|pages|day|days|"
    r"BCE|CE|AD|BC|test|tests|second|seconds|minute|minutes|"
    r"px|em|rem|%|line\b)",
    re.IGNORECASE,
)
# Reference-prefix vocabulary (e.g., "verse 119" or "Psalm 119").
_REFERENCE_PREFIX_RE = re.compile(
    r"\b(verse|chapter|book|line|word|token|file|psalm|gen|exod|lev|num|deut|"
    r"josh|judg|ruth|sam|kings|kgs|chron|chr|ezra|neh|esth|job|psa|ps|prov|"
    r"prv|eccl|qoh|song|sos|isa|jer|lam|ezek|dan|hos|joel|amos|obad|jon|"
    r"jonah|mic|nah|hab|zeph|hag|zech|mal|year|day|page|test|stage|item|"
    r"step|level|round|wave|tier|version|v|phase|round)\b\s*$",
    re.IGNORECASE,
)


def _stop_violations(transcript_path: str) -> list[str]:
    """Detect outgoing-message anti-patterns at Stop time.

    Two gates per 2026-05-04 colonoscopy audit §3.2:
      (i)  Permission-loop coda: message ends with '?' and pending todos exist.
      (iii) Counts-headline: first paragraph contains a leading integer >= 100
            not contextualized as a reference.

    Both are bypassable via leading HTML comment tokens (invisible in rendered
    markdown but visible to the hook):
      <!-- question-required: <reason> -->
      <!-- counts-ok: <reason> -->
    """
    text = _extract_last_assistant_text(transcript_path)
    if not text:
        return []  # Can't read message → don't block (avoid spurious blocking)
    violations: list[str] = []

    # --- (i) Permission-loop coda ---
    has_question_bypass = _PERMISSION_LOOP_BYPASS in text
    if not has_question_bypass:
        stripped = text.rstrip()
        if stripped.endswith("?") and _has_pending_todos(transcript_path):
            violations.append(
                f"[PERMISSION-LOOP] Outgoing message ends with '?' AND the "
                f"recent TodoWrite shows pending (non-completed) todos. Per "
                f"`feedback_no_permission_loop_on_authorized_work.md` (8 days "
                f"old, violated 326 times across 8 sessions per the 2026-05-04 "
                f"prior-sessions audit): when status reports contain a non-"
                f"empty pending-todo queue and Stan has not blocked the next "
                f"item, the next message IS the next item — not a question "
                f"about whether to start it.\n\n"
                f"ACTION: rewrite the trailing question as 'Continuing on "
                f"[next item from queue]' and proceed. If the question is "
                f"genuinely necessary (Stan-decision required, ambiguous "
                f"input, destructive action confirmation), bypass with "
                f"leading HTML comment: '{_PERMISSION_LOOP_BYPASS} <reason> "
                f"-->' (renders invisible in markdown; visible to the hook)."
            )

    # --- (iii) Counts-headline ---
    has_counts_bypass = _COUNTS_HEADLINE_BYPASS in text
    if not has_counts_bypass:
        # First paragraph = text up to first \n\n
        first_para = text.split("\n\n", 1)[0] if text else ""
        # Skip leading HTML comments and bypass-token markers when measuring.
        first_para_clean = re.sub(r"^\s*(?:<!--[\s\S]*?-->\s*)+", "", first_para).strip()
        if first_para_clean:
            for m in _HEADLINE_NUMERIC_RE.finditer(first_para_clean):
                num_str = m.group(1).replace(",", "")
                try:
                    n = int(num_str)
                except ValueError:
                    continue
                if n < 100:
                    continue
                # Check before-context: is this a reference-prefixed number?
                before = first_para_clean[: m.start()][-40:]
                if _REFERENCE_PREFIX_RE.search(before):
                    continue
                # Check after-context: is the number followed by a reference-unit?
                after = first_para_clean[m.end() : m.end() + 30]
                if _REFERENCE_UNIT_RE.match(after):
                    continue
                # Bare number ≥100 in first paragraph not contextualized → block.
                violations.append(
                    f"[COUNTS-HEADLINE] First paragraph of outgoing message "
                    f"contains a bare integer {n} not contextualized as a "
                    f"reference (verse, chapter, line, word, file, etc.). Per "
                    f"`feedback_counts_belong_in_commit_messages.md` and the "
                    f"2026-05-04 process-waste audit pattern #8: status "
                    f"reports lead with WHAT changed in the corpus (named "
                    f"verses, named files), not HOW MANY findings shifted. "
                    f"Counts go in commit messages where Stan can pull them "
                    f"on demand.\n\n"
                    f"ACTION: rewrite the first paragraph to lead with the "
                    f"editorial change, not the count. If the count IS the "
                    f"reportable item (e.g., a build-summary message that's "
                    f"genuinely number-led), bypass with leading HTML "
                    f"comment: '{_COUNTS_HEADLINE_BYPASS} <reason> -->'."
                )
                break  # one violation per message is enough
    return violations


def _write_violations(payload: dict) -> list[str]:
    """Detect new-validator-creation Write-tool calls without bypass token.

    Per 2026-05-04 colonoscopy + 2026-05-03 Stan instruction
    ("stop making new validators... proliferation creates conflicts"):
    creating a new `validators/(syntax|colometry)/validate_*.py` file should
    require an explicit justification token in a recent assistant message
    naming why this is a NEW validator and not an extension to an existing one.

    Bypass: a recent assistant message must contain the marker
    `# validator-extension-justified: <reason>` with a substantive reason
    (per `_validate_bypass_substance`).
    """
    file_path = payload.get("tool_input", {}).get("file_path", "") or ""
    if not file_path:
        return []
    # Normalize to forward slashes for matching.
    norm = file_path.replace("\\", "/")
    if not re.search(
        r"validators/(?:syntax|colometry)/validate_[\w]+\.py$", norm
    ):
        return []  # Not a validator file — pass through

    # Check if the file already exists. If yes, this is editing not creating.
    if Path(file_path).exists():
        return []  # Editing existing validator is fine

    # New validator file. Require bypass token in recent assistant messages.
    transcript_path = payload.get("transcript_path", "")
    asst_text = ""
    if transcript_path:
        # Concatenate the last few assistant messages to find the bypass token.
        p = Path(transcript_path)
        if p.exists():
            try:
                with p.open("rb") as fh:
                    fh.seek(0, 2)
                    size = fh.tell()
                    tail_size = min(size, 5_000_000)
                    fh.seek(size - tail_size)
                    tail_bytes = fh.read()
                tail_text = tail_bytes.decode("utf-8", errors="ignore")
            except Exception:
                tail_text = ""
            collected: list[str] = []
            for line in reversed(tail_text.splitlines()):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                if entry.get("type") != "assistant":
                    continue
                msg = entry.get("message")
                if not isinstance(msg, dict):
                    continue
                content = msg.get("content")
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            t = block.get("text", "")
                            if isinstance(t, str):
                                collected.append(t)
                if len(collected) >= 5:
                    break
            asst_text = "\n".join(collected)

    bypass_token = "# validator-extension-justified:"
    if bypass_token in asst_text:
        # Validate substance.
        substance_err = _validate_bypass_substance(
            asst_text, bypass_token, _VALIDATOR_EXT_SUBSTANCE_RE
        )
        if substance_err:
            return [substance_err]
        return []  # Bypass present and substantive — allow

    return [
        f"[VALIDATOR-PROLIFERATION] Write tool is creating a new validator "
        f"file at {norm}. Per the 2026-05-03 Stan instruction "
        f"(\"stop making new validators... the dataset is finite, the grammar "
        f"is finite. proliferation creates conflicts.\") and the 2026-05-05 "
        f"path-forward Deferred Work item 4: new validators face an O(N) "
        f"interaction surface against the existing N validators. Default "
        f"action is to extend an existing validator with a new arm/subcase, "
        f"not create a new file.\n\n"
        f"ACTION (in priority order):\n"
        f"  (a) Identify which existing validator in `scripts/apply_validators.py` "
        f"ADOPTED_VALIDATORS could carry this as a new arm or subcase. "
        f"Extend that file instead.\n"
        f"  (b) If extension is genuinely impossible (the new validator's "
        f"trigger surface is fundamentally different from any existing "
        f"validator), include in your message-before-this-Write a marker:\n"
        f"      # validator-extension-justified: <reason from accepted "
        f"vocabulary>\n"
        f"    Accepted reasons name an explicit criterion: "
        f"extend / new-arm / new-subcase / distinct-failure / orthogonal / "
        f"cannot-be-added / existing-validator-misses / fundamentally-different. "
        f"Substance is validated.\n"
        f"  (c) If you're working on a fixture or test file (not a real "
        f"validator), name it under `tests/` not `validators/`."
    ]


def _atu_method_edit_violations(payload: dict) -> list[str]:
    """Detect Edit/Write to atu-method/atu_method/* without Macula evidence.

    Per CLAUDE.md "Use the primitive, not the heuristic" rule (codified
    2026-05-12 after the distribute.py iteration cycle that burned 4
    iterations + 3 cascades + 5 audit waves on closed-list KJV-surface
    heuristics when Macula constituent membership was the right primitive
    from the start):

    Edits to atu-method/atu_method/* (cross-corpus shared infrastructure
    for KJV alignment, distribution, Strong's normalization) require
    evidence in recent assistant text that the Macula primitive was
    consulted before reaching for surface-form heuristics.

    Bypass: a recent assistant message must contain the marker
    `# macula-checked: <verdict>` with substance from the closed vocab.
    """
    file_path = payload.get("tool_input", {}).get("file_path", "") or ""
    if not file_path:
        return []
    norm = file_path.replace("\\", "/")
    # Trigger only on atu-method/atu_method/* engine code (not docs, tests,
    # or other top-level repo files). The kjv_alignment, audit, and other
    # algorithm modules under atu_method/ are the cross-corpus engine.
    if not re.search(r"/atu-method/atu_method/[^/]+/.*\.py$", norm):
        return []

    transcript_path = payload.get("transcript_path", "")
    asst_text = ""
    if transcript_path:
        p = Path(transcript_path)
        if p.exists():
            try:
                with p.open("rb") as fh:
                    fh.seek(0, 2)
                    size = fh.tell()
                    tail_size = min(size, 5_000_000)
                    fh.seek(size - tail_size)
                    tail_bytes = fh.read()
                tail_text = tail_bytes.decode("utf-8", errors="ignore")
            except Exception:
                tail_text = ""
            collected: list[str] = []
            for line in reversed(tail_text.splitlines()):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                if entry.get("type") != "assistant":
                    continue
                msg = entry.get("message")
                if not isinstance(msg, dict):
                    continue
                content = msg.get("content")
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            t = block.get("text", "")
                            if isinstance(t, str):
                                collected.append(t)
                if len(collected) >= 5:
                    break
            asst_text = "\n".join(collected)

    bypass_token = "# macula-checked:"
    if bypass_token in asst_text:
        substance_err = _validate_bypass_substance(
            asst_text, bypass_token, _MACULA_CHECKED_SUBSTANCE_RE
        )
        if substance_err:
            return [substance_err]
        return []

    return [
        f"[MACULA-PRIMITIVE-CHECK] Edit/Write to atu-method/atu_method/* "
        f"engine file ({norm}) without Macula-checked evidence in recent "
        f"assistant message.\n\n"
        f"Per CLAUDE.md \"Use the primitive, not the heuristic\" rule: "
        f"edits to cross-corpus shared infrastructure for Hebrew-side or "
        f"Hebrew-derived processing (KJV distribution, Strong's normalization, "
        f"alignment) MUST first consult Macula constituent membership "
        f"(validators/_shared/macula_constituents.py) before reaching for "
        f"surface-form heuristics. Past failure (2026-05-12 distribute.py): "
        f"4 iterations + 3 corpus cascades + 5 audit waves on closed-list "
        f"KJV-surface heuristics when Macula constituent membership was the "
        f"right primitive from the start.\n\n"
        f"ACTION (in priority order):\n"
        f"  (a) Skim validators/_shared/macula_constituents.py — the "
        f"Token / Constituent / Clause API + get_verse_* query functions. "
        f"Determine: does the question I'm trying to answer with this Edit "
        f"reduce to a Macula query (constituent membership, clause boundary, "
        f"role label, frame-arg)? If yes — use it; the heuristic is wrong.\n"
        f"  (b) If Macula genuinely doesn't apply, include in your "
        f"message-before-this-Edit a marker:\n"
        f"      # macula-checked: <reason from accepted vocabulary>\n"
        f"    Accepted reasons: macula-checked / macula-queried / "
        f"macula-extended / macula-consulted / macula-doesnt-cover / "
        f"not-applicable-greek-side / greek-side-only / "
        f"primitive-already-in-use / trivial-non-structural / "
        f"audit-dispatched-with-macula-named / docstring-only / "
        f"formatting-only. Substance is validated.\n"
        f"  (c) If you're iterating an engine heuristic across multiple "
        f"revert/re-apply cycles in this session, STOP. Heuristic iteration "
        f"= wrong primitive. Pivot to Macula."
    ]


def _agent_violations(prompt: str) -> list[str]:
    """Detect Agent dispatches that describe script-able mechanical lookups.

    Per the 2026-05-04 colonoscopy audit §3.2 Hook (ii): the memory
    `feedback_scripts_default_agents_only_for_judgment.md` was the
    highest-recidivism memory in the inventory — violated three times
    within 24 hours of creation. This hook converts the prose discipline
    into a runtime gate.

    Trigger: Agent prompt body length <= 2000 chars AND mechanical-vocabulary
    regex matches (count / list all / how many / find all / glob for /
    enumerate). Bypass: prompt body starts with `# judgment-required:
    <reason>` — visible in the JSONL for later audit.
    """
    if not prompt:
        return []
    stripped = prompt.lstrip()
    if stripped.startswith(_AGENT_BYPASS_TOKEN):
        # Validate substance of bypass reason.
        substance_err = _validate_bypass_substance(
            prompt, _AGENT_BYPASS_TOKEN, _JUDGMENT_SUBSTANCE_RE
        )
        if substance_err:
            return [substance_err]
        return []  # Bypass token present and substantive — agent dispatch authorized
    if len(prompt) > _AGENT_PROMPT_LENGTH_THRESHOLD:
        return []  # Long prompt body = likely judgment-heavy synthesis
    m = _AGENT_MECHANICAL_VOCAB_RE.search(prompt)
    if not m:
        return []
    sample = m.group(0)
    return [
        f"[SCRIPTS-DEFAULT] Agent dispatch with short prompt body "
        f"({len(prompt)} chars) matches mechanical-vocabulary trigger "
        f"('{sample}'). Per `feedback_scripts_default_agents_only_for_judgment.md` "
        f"and the 2026-05-04 colonoscopy audit §3.2: agents are for tasks "
        f"where judgment can't be expressed as a regex/structured query. "
        f"Counts, lists, globs, set-membership tests are deterministic and "
        f"should be answered by Bash/Glob/Grep or a 30-line script in "
        f"seconds — not dispatched to a Sonnet/Haiku agent at $0.05-0.15 "
        f"+ 60-180s wall-clock.\n\n"
        f"ACTION: (a) re-write the deliverable as a Bash/Glob/Grep call or "
        f"a small persistent script under `scripts/scan_*.py`; OR (b) if "
        f"the deliverable genuinely requires judgment that regex can't "
        f"enumerate (e.g., classifying edge cases, multi-source synthesis, "
        f"hostile audit), prefix the prompt body with "
        f"`{_AGENT_BYPASS_TOKEN} <reason>` explaining what judgment is "
        f"needed. The bypass token is visible in the JSONL trace and "
        f"reviewable by Stan; use sparingly."
    ]


def _cascade_invocation_violations(command: str, transcript_path: str) -> list[str]:
    """Detect 2nd same-book cascade invocation without engine-level Edit between.

    Per 2026-05-05 Sifrei-Emet purge arc: iterating cascade against the same
    book without an engine-level fix is the whack-a-mole signal. Three
    iterations of per-spec guards landed before the engine fix at
    `_check_morphology("prep")` — and only after Stan's escalation. The
    hook fires at the moment of the second cascade with no engine fix
    between, exactly when the class-vs-instance question should be asked.
    """
    m = _CASCADE_BOOK_RE.search(command)
    if not m:
        return []  # Not a per-book cascade invocation
    # Only treat the bypass token as real if it appears at line-start
    # (token strings in heredoc bodies / commit messages are not bypasses).
    bypass_at_linestart = re.search(
        r"(?m)^\s*" + re.escape(_INSTANCE_FIX_BYPASS), command
    )
    if bypass_at_linestart:
        substance_err = _validate_bypass_substance(
            command, _INSTANCE_FIX_BYPASS, _INSTANCE_FIX_SUBSTANCE_RE
        )
        if substance_err:
            return [substance_err]
        return []  # Bypass present and substantive
    current_book = m.group(2)
    if not transcript_path:
        return []  # Can't walk transcript — don't false-block
    p = Path(transcript_path)
    if not p.exists():
        return []
    try:
        with p.open("rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            tail_size = min(size, 5_000_000)
            fh.seek(size - tail_size)
            tail_bytes = fh.read()
        tail_text = tail_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return []
    prior_same_book = 0
    engine_edit_after_first = False
    first_seen = False
    for line in tail_text.splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except Exception:
            continue
        if entry.get("type") != "assistant":
            continue
        msg = entry.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "tool_use":
                continue
            name = block.get("name")
            tool_input = block.get("input", {})
            if not isinstance(tool_input, dict):
                continue
            if name == "Bash":
                cmd = tool_input.get("command", "") or ""
                if not isinstance(cmd, str):
                    continue
                cmd_match = _CASCADE_BOOK_RE.search(cmd)
                if cmd_match and cmd_match.group(2) == current_book:
                    prior_same_book += 1
                    first_seen = True
            elif name in ("Edit", "Write") and first_seen:
                file_path = tool_input.get("file_path", "") or ""
                if isinstance(file_path, str) and _ENGINE_FILE_RE.search(
                    file_path.replace("\\", "/")
                ):
                    engine_edit_after_first = True
    if prior_same_book < 1:
        return []  # First invocation of cascade against this book; no signal
    if engine_edit_after_first:
        return []  # Engine fix landed between cascades; correct workflow
    return [
        f"[CASCADE-ITERATION] About to invoke cascade against book "
        f"'{current_book}' for the {prior_same_book + 1}th time in this "
        f"session, with NO Edit to engine-level files "
        f"(scripts/spec_runner.py, scripts/apply_*.py, validators/_shared/) "
        f"between cascades. Per the 2026-05-05 Sifrei-Emet purge: re-running "
        f"cascade after instance-level fixes (per-spec guards, per-validator "
        f"tweaks) without addressing the engine-level class is the whack-a-"
        f"mole pattern that took three iterations before the engine fix at "
        f"`_check_morphology(\"prep\")` landed — and only after Stan's "
        f"escalation. Stan's mantra: \"swat the bug class, not the instance.\"\n\n"
        f"ACTION: STOP. Look at the per-spec/per-validator fixes between "
        f"the prior cascade and now. Are they addressing the same conceptual "
        f"FP class? If yes → fix at the engine level (scripts/spec_runner.py "
        f"or validators/_shared/) before re-cascading.\n\n"
        f"BYPASS (use only with substantive justification): prefix command "
        f"with '{_INSTANCE_FIX_BYPASS} <reason>' where <reason> names a "
        f"closed-vocabulary criterion: engine-tried / unrelated-bugs / "
        f"stan-directed / cross-helper / revert-rerun / walkback / verify."
    ]


def _violations(command: str, payload: dict | None = None) -> list[str]:
    """Return list of detected anti-pattern violations."""
    payload = payload or {}
    violations: list[str] = []
    transcript_path = payload.get("transcript_path", "") or ""

    # --- Pattern 5: cascade-iteration tripwire ------------------------------
    # Detects whack-a-mole: 2nd `--book <X>` cascade without engine-level Edit.
    cascade_iter = _cascade_invocation_violations(command, transcript_path)
    if cascade_iter:
        violations.extend(cascade_iter)

    # --- Pattern 1: multi-line Python heredoc -------------------------------
    # Match `<<TAG ... TAG` or `<<'TAG' ... TAG` blocks. We need the heredoc
    # to be (a) preceded by a python invocation, (b) ≥5 non-empty body lines,
    # (c) body contains python idioms (import/from/def/class/print/etc.).
    HEREDOC_RE = re.compile(
        r"<<\s*['\"]?(\w+)['\"]?\s*\n(.*?)\n\s*\1\s*$",
        re.DOTALL | re.MULTILINE,
    )
    PY_IDIOM_RE = re.compile(
        r"^\s*(import |from |def |class |print\(|"
        r"for \w+ in |if __name__|with open|"
        r"return |yield |@\w+|sys\.|json\.|os\.|re\.)"
    )
    # The pre-heredoc string must end with a Python invocation pointing at stdin
    # via the `-` marker: `py -3 -`, `py -`, `python3 -`, etc. We strip trailing
    # whitespace and require the stripped pre to end with the invocation pattern.
    PY_INVOCATION_RE = re.compile(
        r"\b(py(?:thon)?3?)\b\s+(?:-3\s+)?-\s*$", re.IGNORECASE
    )

    for m in HEREDOC_RE.finditer(command):
        body = m.group(2)
        body_lines = [ln for ln in body.split("\n") if ln.strip()]
        if len(body_lines) < 5:
            continue
        if not any(PY_IDIOM_RE.search(ln) for ln in body_lines):
            continue
        # Confirm it's a Python invocation (not, say, a git commit message body
        # delivered via `git commit -m "$(cat <<'EOF' ... EOF)"`).
        pre = command[: m.start()].rstrip()
        if not PY_INVOCATION_RE.search(pre):
            continue
        violations.append(
            f"[E1-E2] Multi-line Python heredoc detected ({len(body_lines)} non-empty "
            f"lines, contains Python idioms). Per handoffs/14-operational-protocols.md "
            f"§E1-E2: recurring Python operations must be persistent scripts under "
            f"scripts/, not bash heredocs. Bash heredocs break on Windows /tmp "
            f"ephemerality and on Hebrew/apostrophe-containing text. ACTION: use the "
            f"Write tool to create scripts/<descriptive_name>.py, then run with `py -3 "
            f"scripts/<name>.py`. Reuse next time you need the same operation."
        )
        break  # one heredoc violation surfaces the lesson; don't spam multiple

    # --- Pattern 2: --all-books cascade on main thread ----------------------
    CASCADE_RE = re.compile(
        r"(apply_specs|refresh_book|apply_validators)\.py\b[^\n]*--all-books"
    )
    cascade_match = CASCADE_RE.search(command)
    if cascade_match and "# split-justified:" not in command:
        violations.append(
            "[A2] Cascade invocation '--all-books' on main thread. Per "
            "handoffs/14-operational-protocols.md §A2 (mandatory two-phase pattern): "
            "this should be dispatched as 6 parallel cluster Agent calls in one "
            "message — Torah / Former Prophets / Latter Prophets / Writings prose / "
            "Sifrei Emet / Embedded Poetry. Wall time collapses to max(per-cluster) "
            "instead of sum. ACTION: dispatch 6 Agent tool_use blocks in a single "
            "message, one per cluster. To override (true initial-exploration single "
            "pass only), prefix command with '# split-justified: <reason>'."
        )

    # --- Pattern 4 (A3 Step 0): --all-books without recent audit evidence ---
    # Cascade invocations are batch-boundary signals — the moment substantive
    # implementations get applied corpus-wide. Per §A3 Step 0, these MUST be
    # preceded by adversarial-audit dispatches (≥2 in recent transcript window).
    if cascade_match and "# audit-skippable:" not in command:
        n_dispatches = _count_recent_agent_dispatches(payload.get("transcript_path", ""))
        if n_dispatches < 2:
            violations.append(
                f"[A3-Step0] Cascade invocation '--all-books' with insufficient "
                f"adversarial-audit evidence in recent transcript (found "
                f"{n_dispatches} Agent dispatch(es); need ≥2). Per "
                f"handoffs/14-operational-protocols.md §A3 Step 0: before any "
                f"non-trivial implementation, the FIRST tool call in your response "
                f"must be either (a) parallel Agent dispatches for adversarial "
                f"audit (one message, multiple Agent tool_use blocks), OR (b) a "
                f"one-line declaration 'Audit-skippable: <reason>' citing a "
                f"recognized trivial class (port-of-validated, mechanical-ingest, "
                f"test/fixture, runner/glue, scratch). ACTION: (1) abort, dispatch "
                f"≥2 parallel Agent calls in one message, let their findings inform "
                f"the implementation, then re-run; OR (2) prefix command with "
                f"'# audit-skippable: <reason>'."
            )

    # --- Pattern 3: git status/diff without summary flags ------------------
    GIT_VERBOSE_RE = re.compile(r"\bgit\s+(?:status|diff)\b")
    SUMMARY_FLAG_RE = re.compile(
        r"--(?:shortstat|numstat|stat|porcelain|name-only|name-status|short)\b"
        r"|--cached\s+--stat\b"
    )
    SUMMARY_PIPE_RE = re.compile(r"\|\s*(?:wc\b|head\b|tail\b|grep\b|rg\b)")
    # Split on common shell separators to evaluate per-clause
    clauses = re.split(r"&&|;|\n", command)
    for clause in clauses:
        clause_s = clause.strip()
        if not clause_s or clause_s.startswith("#"):
            continue
        if not GIT_VERBOSE_RE.search(clause_s):
            continue
        if SUMMARY_FLAG_RE.search(clause_s):
            continue
        if SUMMARY_PIPE_RE.search(clause_s):
            continue
        # Allow specific safe patterns: `git status --short | wc` already caught;
        # `git diff path/to/file` (a specific path arg, no `--`-flags) is debatable
        # but safer to flag than miss.
        violations.append(
            f"[H3] git status/diff without summary flag in: '{clause_s[:90]}'. Per "
            f"handoffs/14-operational-protocols.md §H3 (verbose-by-default ingestion): "
            f"bare `git status` and `git diff` ingest verbose output and waste context. "
            f"ACTION: add a summary flag (--shortstat / --numstat / --stat / "
            f"--porcelain / --name-only / --short) or pipe to | wc -l for a count."
        )
        break  # one git violation is enough to surface the lesson

    return violations


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # Malformed input — don't block the tool call.
        return 0

    event = payload.get("hook_event_name", "")
    tool_name = payload.get("tool_name")

    # ── Stop event: outgoing-message gates (permission-loop + counts-headline) ──
    if event == "Stop":
        violations = _stop_violations(payload.get("transcript_path", ""))
        if not violations:
            return 0
        msg = (
            f"\n=== Stop DISCIPLINE GATE — {len(violations)} anti-pattern(s) "
            f"detected on outgoing message ===\n\n"
            + "\n\n".join(f"{i + 1}. {v}" for i, v in enumerate(violations))
            + "\n\nBypasses are leading HTML comments (invisible in markdown):\n"
            "  '<!-- question-required: <reason> -->' for permission-loop\n"
            "  '<!-- counts-ok: <reason> -->' for counts-headline\n"
        )
        print(msg, file=sys.stderr)
        return 2

    # ── Agent tool: scripts-default-vs-agents gate ──────────────────────────
    if tool_name == "Agent":
        prompt = payload.get("tool_input", {}).get("prompt", "") or ""
        if not prompt:
            return 0
        violations = _agent_violations(prompt)
        if not violations:
            return 0
        msg = (
            f"\n=== PreToolUse DISCIPLINE GATE — {len(violations)} "
            f"anti-pattern(s) detected on Agent dispatch ===\n\n"
            + "\n\n".join(f"{i + 1}. {v}" for i, v in enumerate(violations))
            + f"\n\nBypass (visible in JSONL): prefix the Agent prompt body with "
            f"'{_AGENT_BYPASS_TOKEN} <reason>'.\n"
            "Use sparingly — every override is reviewable by Stan.\n"
        )
        print(msg, file=sys.stderr)
        return 2

    # ── Write tool: validator-creation guard + atu-method Macula-check ──────
    if tool_name == "Write":
        violations = _write_violations(payload) + _atu_method_edit_violations(payload)
        if not violations:
            return 0
        msg = (
            f"\n=== PreToolUse DISCIPLINE GATE — {len(violations)} "
            f"anti-pattern(s) detected on Write dispatch ===\n\n"
            + "\n\n".join(f"{i + 1}. {v}" for i, v in enumerate(violations))
        )
        print(msg, file=sys.stderr)
        return 2

    # ── Edit tool: atu-method Macula-primitive-check gate ───────────────────
    if tool_name == "Edit":
        violations = _atu_method_edit_violations(payload)
        if not violations:
            return 0
        msg = (
            f"\n=== PreToolUse DISCIPLINE GATE — {len(violations)} "
            f"anti-pattern(s) detected on Edit dispatch ===\n\n"
            + "\n\n".join(f"{i + 1}. {v}" for i, v in enumerate(violations))
        )
        print(msg, file=sys.stderr)
        return 2

    # ── Bash tool: existing heredoc / cascade / git-verbose / A3-Step0 gates ──
    if tool_name != "Bash":
        return 0

    command = payload.get("tool_input", {}).get("command", "") or ""
    if not command:
        return 0

    # ── Override quote-validation gate (colonoscopy audit 2026-05-04 §2.3a) ──
    # Before honoring ANY override comment (`# disciplined-allow:`,
    # `# split-justified:`, `# audit-skippable:`), if the override comment cites
    # a quoted phrase as Stan-said-X, validate that the phrase is verbatim (or
    # near-verbatim) in the recent transcript. Refuse the override if the cited
    # quote is hallucinated. Closes the structural hole that allowed bypassing
    # the discipline gate four times on 2026-05-04 with confabulated citations.
    quote_err = _validate_override_quotes(command, payload.get("transcript_path", ""))
    if quote_err:
        print(quote_err, file=sys.stderr)
        return 2  # Refuse the tool call — override comment cites a non-existent quote

    # Universal escape hatch — visible in the JSONL for later audit.
    if "# disciplined-allow:" in command:
        return 0

    violations = _violations(command, payload)
    if not violations:
        return 0

    msg = (
        f"\n=== PreToolUse DISCIPLINE GATE — {len(violations)} anti-pattern(s) "
        f"detected ===\n\n"
        + "\n\n".join(f"{i + 1}. {v}" for i, v in enumerate(violations))
        + "\n\nUniversal override (visible in JSONL): prefix command body with "
        "'# disciplined-allow: <reason>' or, for cascade-specific cases, "
        "'# split-justified: <reason>'.\n"
        "These overrides are visible in your tool-call history and reviewable "
        "by Stan; use sparingly.\n"
    )
    print(msg, file=sys.stderr)
    return 2  # blocks the tool call; stderr surfaced to Claude


if __name__ == "__main__":
    sys.exit(main())
