# research/ — third-party corpora (payloads untracked, this manifest tracked)

Nothing in this directory is our work, and nothing here is committed except this
file. Everything listed below is reproducible from its source; if a directory is
missing, restore it with the command given.

**Our own analysis does not live here.** It goes in the numbered tiers —
`2-evidence/` for findings and baselines, `5-machinery/` for scripts. A pilot
study sat in this folder untracked until 2026-08-10 and is now at
`2-evidence/atu-pilot-mechanical-first/`.

## Why the payloads are untracked but this file is

A blanket `research/` ignore leaves nothing behind when a directory disappears.
On 2026-08-10 both Greek corpora were found missing from `readers-gnt` with no
deletion trace — the validators that depended on them had been returning zero,
and one had been emitting roughly ten times its baseline in false candidates.
Neither failure was visible. A tracked manifest makes absence detectable even
though the bytes themselves are upstream's to own.

## Expected contents

| Directory | Source | Pinned |
|---|---|---|
| `macula-hebrew/` | https://github.com/Clear-Bible/macula-hebrew | `47db250` |
| `stepbible-tahot/` | STEPBible TAHOT (Tyndale House) — see below | — |
| `bullinger/` | https://archive.org/details/figuresofspeechu00bull | — |

### macula-hebrew

Syntax trees, morphology, and linguistic annotations for the Hebrew Bible.

    git clone https://github.com/Clear-Bible/macula-hebrew.git

Note the clause-type attribute here is spelled `clausetype`, and in the Greek
Macula it is `ClType` and appears only in the `nodes/` format, not `lowfat/`.

### stepbible-tahot

Translators Amalgamated Hebrew OT, four volumes covering Gen–Deu, Jos–Est,
Job–Sng, Isa–Mal. Released by Tyndale House, Cambridge under CC BY 4.0.
Source: https://github.com/STEPBible/STEPBible-Data

### bullinger

E. W. Bullinger, *Figures of Speech Used in the Bible* (1898) — public domain.
Consumed by `scripts/build_hendiadys_lexicon.py` to extract verse references from
the HENDIADYS chapter into `data/syntax-reference/hendiadys-lexicon.tsv`.
Local `bullinger/README.md` carries the full citation.

## Restoring everything

    cd research
    git clone https://github.com/Clear-Bible/macula-hebrew.git

`stepbible-tahot/` and `bullinger/` are plain file drops rather than clones —
download them from the sources above.
