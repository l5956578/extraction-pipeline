# Extraction status — Threshold, Waystage, CEFR 2001

**Date:** 2026-07-31  
**Method:** Layout-aware format extract (block paragraphs, real lists/headers) + Vision App A — not Companion multi-week engine.  
**Standard target:** Companion-class product MD — page markers, **real paragraphs**, **bullet/numbered lists**, clean headers, PDF-like intonation marks, stitched tables.

## Deliverables

| Job | MD | Pages | APPROVED | Notes |
|-----|-----|------:|----------|-------|
| cefr-threshold-1990 | `output/cefr-threshold-1990/Threshold_1990.md` | 192 | **versions/003** | Layout blocks → paragraphs; lists as MD lists; App A Vision with Unicode tones **ˎ ˋ ˏ ˊ ˇ** |
| cefr-waystage-1990 | `output/cefr-waystage-1990/Waystage_1990.md` | 120 | **versions/003** | OCR + format pass; same App A five-tone Unicode system |
| cefr-en-2001 | `output/cefr-en-2001/CEFR_EN_2001.md` | 273 | **versions/003** | Layout blocks; bullet lists; Table 1 + stitched Table 2; section heads |

## Companion lessons applied

| Lesson | How applied |
|--------|-------------|
| `<!-- page:N -->` after each page body | All three books |
| Prose `el:start` / `el:end` wrappers | Per-page blocks |
| `db:id` on document + key sections/tables | Nuclear tones, major sections, CEFR tables/figure |
| Multipage tables → one full grid / one `db:id` | CEFR 2001 Table 2 self-assessment stitched |
| Blank line before tables | Polish pass |
| **Real paragraphs** (not wall-of-text) | PDF text **blocks** → paragraph breaks |
| **Bullet / numbered / lettered lists** | Detected and emitted as MD lists |
| Headers not split / not mid-sentence | Size+pattern; reject lowercase mid-sentence “headings” |
| Intonation marks look like the book | Unicode **ˎ ˋ ˏ ˊ ˇ** (above/below) + **ˈ** head + **·** stress |
| Page PNG evidence retained | `work/<job>/page_renders/` |

## Nuclear tones (both 1990 books) — Vision verified

| # | Name | Mark | Position |
|---|------|------|----------|
| 1 | Low falling | **ˎ** | Below line |
| 2 | High falling | **ˋ** | Above line |
| 3 | Low rising | **ˏ** | Below line |
| 4 | High rising | **ˊ** | Above line |
| 5 | Falling-rising | **ˇ** | Above line (v-shape) |

Also: head **ˈ**, secondary stress **·**, minor `|`, major `||`. Full uses by sentence type in App A body.

## Scripts

| Script | Role |
|--------|------|
| `scripts/vision_extract/format_extract.py` | **Primary** layout-aware format → MD v003 |
| `scripts/vision_extract/assemble_book_md.py` | Earlier render/OCR seed |
| `scripts/vision_extract/fix_cefr2001_tables.py` | Table 1/2 stitch helpers |

## Residual honesty

- Waystage remains OCR-based (image PDF); multi-column vocabulary pages can still be imperfect.  
- CEFR 2001 Table 3 auto quality lower than stitched Table 2.  
- A few soft-hyphen artifacts may remain on wrapped PDF lines.  
- Re-run: `python scripts/vision_extract/format_extract.py`

## APPROVED

All three jobs: `APPROVED.json` → **`versions/003`**.
