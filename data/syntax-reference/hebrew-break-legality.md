# Hebrew Break Legality Reference

Layer 1 permission/prohibition surface for Hebrew colometry. Each row states whether a candidate break point is grammatically legal, illegal, or unconstrained by generic Hebrew syntax. This file is shape-capped — rules, rationale, and examples live in the colometry canon (`private/01-method/colometry-canon.md`) §4.1, which is the authoritative rule-pointer source. Do not add prose, exceptions, or examples here.

## Legality Vocabulary

| Term | Meaning |
|---|---|
| `REQUIRED-MERGE` | Break forbidden here; units must stay on the same line |
| `PERMITTED-EITHER` | Both split and merge are grammatically legal; editorial judgment governs |
| `REQUIRED-BREAK` | Break mandatory here (no Hebrew cases identified in first-pass inventory) |

## Break Legality Table

| Pattern signature | Legality | Reference |
|---|---|---|
| Maqqef-group split (break inside ־ joined words) | `REQUIRED-MERGE` | Joüon-Muraoka §13 |
| Conjunction-prefix וְ stranded line-final | `REQUIRED-MERGE` | The וְ leads its content |
| Prepositional prefix מ/ב/כ/ל stranded from object | `REQUIRED-MERGE` | Joüon-Muraoka §103 |
| Definite article הַ stranded from noun | `REQUIRED-MERGE` | Joüon-Muraoka §137 |
| Direct-object marker אֵת stranded from object | `REQUIRED-MERGE` | Joüon-Muraoka §125 |
| Construct chain split (no intervening modifier) | `REQUIRED-MERGE` | Joüon-Muraoka §129; Waltke-O'Connor §9 |
| Compound divine name split (יְהוָה צְבָאוֹת, יְהוָה אֱלֹהִים, יְהוָה אֱלֹהֵי הַשָּׁמַיִם) | `REQUIRED-MERGE` | Fixed lexicalized formulas |
| Negation (לֹא, אַל, אַיִן) stranded from negated word | `REQUIRED-MERGE` | Joüon-Muraoka §160 |
| Vocative unit split (multi-word direct-address phrase) | `REQUIRED-MERGE` | — |
| Frozen formula split (כֹּה אָמַר יְהוָה, נְאֻם־יְהוָה, divine-name compounds) | `REQUIRED-MERGE` | Fixed lexicalized formulas |

---

Status: initial population 2026-04-26 from colometry-canon.md §4.1 first-pass inventory; expand as Hebrew break-legality cases surface in editorial work.
