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
> The ˇanimal over ·there | is my ·dog.
```

- Function numbers bold; grammar gloss italic where PDF emphasizes.  
- Examples in blockquotes, one utterance per line.  
- Do not bold entire example lines (PDF “two kinds of bold” → keep structure, not fake bold soup).

## Multi-pass rule

For any page listed in `INTONATION_PAGE_INDEX.md`:

1. Vision PNG — list every pre-syllable mark and its position (above/below).  
2. Compare MD — fail if any ASCII `'` used as tone or vertical `ˌ` for low fall.  
3. Re-Vision after fix — pass only when sample lines match PNG.

## Worked example (Threshold book p. 28, §1.1.3)

From Vision of PDF leaf 34:

| Syllable | Mark | Role |
|----------|------|------|
| This | `ˈ` | high upright (head) |
| bedroom | `ˎ` | low falling diagonal |
| animal | `ˇ` | falling-rising |
| there | `·` | mid-height secondary |
| dog | `·` | mid-height secondary |
