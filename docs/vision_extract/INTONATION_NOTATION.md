# Intonation notation — Threshold 1990 / Waystage 1990

**Source of truth:** Appendix A + Vision of exponent pages.  
**Never use ASCII `'` (U+0027) as a tone mark** — it is used for contractions (*don't*, *isn't*).

## Marks (Unicode only)

| Role | PDF appearance | Unicode | Code point | MD example |
|------|----------------|---------|------------|------------|
| **Head / high upright** | Vertical mark **above** line before stressed syllable | `ˈ` | U+02C8 | `ˈThis` |
| **Low falling** | Falling diagonal **below** line (upper-left → lower-right stroke, low) | `ˎ` | U+02CE | `the ˎbedroom` |
| **High falling** | Falling diagonal **above** line | `ˋ` | U+02CB | `ˈNo it ˋisn't` |
| **Low rising** | Rising diagonal **below** line | `ˏ` | U+02CF | |
| **High rising** | Rising diagonal **above** line | `ˊ` | U+02CA | |
| **Falling-rising** | V-shaped mark **above** line | `ˇ` | U+02C7 | `The ˇanimal` |
| **Secondary / rhythmic stress** | Mid-height **dot** (not nuclear) | `·` | U+00B7 | `over ·there` |
| Minor tone group | Vertical bar | `\|` | | `there \| is` |
| Major tone group | Double bar | `\|\|` | | |


## PDF text-layer trap (Threshold Paper Capture)

The PDF text layer is a **hint**, not the mark inventory:

| PDF char | Collapses | Must Vision-disambiguate |
|----------|-----------|--------------------------|
| `'` above syllable | head `ˈ` · high fall `ˋ` · high rise `ˊ` | vertical vs falling diagonal vs rising tick on the **PNG** |
| `,` below syllable | low fall `ˎ` · low rise `ˏ` | falling vs rising stroke **on the PNG** — not the section title |
| `"` / v | fall-rise `ˇ` | |
| `.` mid | secondary `·` | |

**Rule (binding priority):**

1. **PNG glyph on crop wins** over PDF text layer and section titles.  
2. PDF text layer is **skeleton / hint only** (`'` collapses head/HF/HR; `,` collapses LF/LR).  
3. Section titles (e.g. “for confirmation”, “high-rising”) never invent `ˏ`/`ˊ` when the crop shows a clear opposite stroke.  
4. **Re-Vision product MD vs crop** after every write. Native convert is not a pass.  
5. **Multi-iteration residual gate** required before done (`scripts/vision_extract/full_md_vs_pdf_intonation.py` + `gold_intonation_locks.py`): loop until hard counts pass (1.1.3 LF bedroom, 1.3.1 contrastive HF, 1.4.1.x, 1.4.2.2, zero bad residual forms). Max ~5 internal iterations; do not stop after one write.

Section-aware **locks** prevent letter-skeleton merge from collapsing 1.1.3 ↔ 1.3.1 bedroom or 1.2.1 ↔ 1.3.1 train.

Word catalogs: `INTONATION_WORD_CATALOG_LEAF034.md`, `INTONATION_WORD_CATALOG_LEAF034_035.md`.  
Driver: `scripts/vision_extract/full_md_vs_pdf_intonation.py` (multi-iter). Locks: `scripts/vision_extract/gold_intonation_locks.py`.

## Forbidden encodings

| Bad | Why |
|-----|-----|
| `'` ASCII apostrophe | Contractions; ambiguous |
| `ˌ` low vertical line (U+02CC) | **Not** the book’s low fall (diagonal) |
| `` ` `` backtick | OCR garbage |
| `[LF]` alone in running examples | OK in legend only; examples must show real marks |

## Formatting style for function/exponent pages

```markdown
##### 1.1 Identifying (defining)

**1.1.3** the + NP/this, that, these, those (+ NP) + *be* + NP

> ˈThis is the ˎbedroom.  
> The ˇanimal over ·there | is my ˎdog.
```

- Function numbers bold; grammar gloss italic where PDF emphasizes.  
- Examples in blockquotes, one utterance per line.  
- Do not bold entire example lines (PDF “two kinds of bold” → keep structure, not fake bold soup).

## Multi-pass rule (binding — no “looks fine” self-pass)

For any intonation exponent page:

1. **Zoom Vision** — high-res crop of each example line (not whole page only).  
2. **Word catalog** — for every word: mark | none | which glyph | above/below. Write catalog **before** writing MD.  
3. **Emit MD** only from the catalog (never from memory of a previous wrong pass).  
4. **Re-Vision** the written MD against the same crop — fail on any mismatch.  
5. Known traps: mid-dot `·` vs low-fall `ˎ` under the nucleus; high-fall `ˋ` vs fall-rise `ˇ` vs head `ˈ`; never ASCII `'`.  
6. **Residual gate** — run multi-iteration assertions (`gold_intonation_locks.residual_assertions`); only exit when residual list is empty. One write without re-assert is not done.

Gold catalog example: `INTONATION_WORD_CATALOG_LEAF034.md`.

## Worked example (Threshold document p. 28, §1.1.3–1.1.4, 1.3.2)

| Item | Correct MD |
|------|------------|
| 1.1.3 | `ˈThis is the ˎbedroom.` / `The ˇanimal over ·there \| is my ˎdog.` |
| 1.1.4 | `ˈHe is the ˎowner of the ·restaurant.` (**owner** = low fall, not mid-dot) |
| 1.3.1 | `ˋThis is the ·bedroom.` / `The ·train ˋhas ·left.` (contrastive: mid on bedroom/left; **high fall** on This/has) |
| 1.3.2 | `ˈNo it ˇisn’t.` (**isn’t** = fall-rise, not high fall) |
