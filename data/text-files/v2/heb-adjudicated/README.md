# Tanakh v2 adjudication overrides

Render-stage ATU-line overrides for residual cases the mechanical v2 binding
fabric (`scripts/atu_pipeline_v2/binding_rules.py` — 14 B-rules) cannot reach:
judgment-residuals where the BHSA clause-atom partition is structurally sound
but the line-break needs editorial finesse.

## File

`overrides.json` — keyed `"<book-folder> <chapter>:<verse>"` using the BHSA
folder convention verbatim:

```json
{
  "01-genesis 22:1": [
    "וַיְהִי אַחַר הַדְּבָרִים הָאֵלֶּה",
    "וְהָאֱלֹהִים נִסָּה אֶת־אַבְרָהָם",
    "וַיֹּאמֶר אֵלָיו אַבְרָהָם וַיֹּאמֶר הִנֵּנִי׃"
  ]
}
```

Book-folder names match the `data/text-files/v2/heb/` directory structure
(`01-genesis`, `02-exodus`, ..., `27-daniel`, `28-hosea`, ..., `38-zechariah`,
`39-malachi`). Values are arrays of strings, one ATU line per element, in
surface (RTL) order, exactly as they would appear in the rendered chapter file.

## Two-gate parity

Every override entry must reassemble to the v0 verse text under **both** gates.
This is the substantive fix over the mechanical BoFM port, whose ASCII-only
`[^a-z0-9]` regex silently accepts ANY Hebrew override (both sides degenerate
to the empty string).

### Gate A — Consonant parity
NFD-normalize → strip Hebrew points + te'amim (U+0591-05BD, U+05BF,
U+05C1-05C2, U+05C4-05C7) → retain only the **wider Hebrew letter block**
U+05D0-05F4. The wider range is critical: the narrow `[א-ת]` (U+05D0-05EA)
that lives in the in-pipeline `_CONS_ONLY` regex **excludes** the final-form
letters ך ם ן ף ץ (U+05DA, U+05DD, U+05DF, U+05E3, U+05E5), so every verse
ending in a final letter would silently fail parity if the override layer
reused that regex.

### Gate B — Pointing-strict parity
NFD-normalize → map maqqef `־` (U+05BE) → space → keep only Hebrew letters +
niqqud + te'amim + sof-pasuq + paseq. The diacritic stream must round-trip
byte-for-byte after NFD; an override that drops a holam, meteg, atnaḥ, or
sof-pasuq is REJECTED with `POINTING-STRICT FAIL`. Enforces the Tanakh
CLAUDE.md invariant: "the source text — v0 forms / consonants / niqqud /
te'amim — is never modified."

The only orthographic transform permitted is maqqef → space, so a
maqqef-bound phrase like אֶת־הַשָּׁמַיִם may legitimately split across line breaks
as אֶת + הַשָּׁמַיִם without failing parity.

**Both gates must pass.** Failures are logged distinctly so an editor knows
whether they dropped a word (Gate A) or a diacritic (Gate B).

## Aramaic skip

Aramaic verses in Daniel 2:4-7:28 and Ezra 4:8, 4:18 (sic — see
`ARAMAIC_RANGES` table), 5:1-6:18, 7:12-26 are **skipped entirely**: any
override key in those ranges short-circuits to mechanical without parity
even being attempted. Prevents an Aramaic ref from silently shipping
through. The table mirrors `scripts/atu_pipeline/run_pipeline.py`.

## When to use an override

- The mechanical fabric over-splits or over-merges a specific verse where
  no general B-rule can be added without regressing elsewhere
- A scholarly editorial choice (e.g. parallelism in Sifrei Emet) the binding
  rules cannot make from BHSA `typ`/`domain`/`rela` features alone
- A Stan-flagged verse where step-1 self-audit (`binding-rules-hebrew.md`)
  confirms the parse is sound but the line-break needs adjustment

## When NOT to use an override

- A class of verses needs the same fix → add or refine a B-rule in
  `scripts/atu_pipeline_v2/binding_rules.py` instead
- The underlying BHSA clause-atom partition is wrong → escalate upstream
  (not generally fixable at our layer, but document the gap)

## Bypass

For validators or raw-mechanical-measurement runs:

```
TANAKH_BYPASS_OVERRIDES=1 PYTHONIOENCODING=utf-8 py -3 scripts/atu_pipeline_v2/run_full_tanakh.py --book 01-genesis
```

## Architecture

Overrides apply at the **render stage** inside `render_v2_heb_format`, per
verse, after the mechanical ATU lines for the verse are assembled but before
they are appended to the chapter output. `apply_bindings` and
`extract_clauses_for_chapter` stay pure — they remain regenerable method
outputs that can be diffed cleanly without override side-effects.

This mirrors the cross-corpus pattern delivered for Vulgate (render-stage
in `build_content.py`) + GNT (render-stage post-`flush()` in `emit_v4`) +
documented in the session-2026-06-02 cross-corpus port redesign work.
