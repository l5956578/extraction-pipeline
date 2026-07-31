# Extraction status — Threshold, Waystage, CEFR 2001

**Date:** 2026-07-31  
**Method:** Vision-first / OCR assembly (not a reimplementation of the Companion multi-week engine).  
**Standard target:** Companion-class product MD — page markers, section structure, artifact IDs, stitched tables, documented intonation system.

## Deliverables

| Job | MD | Pages | APPROVED | Notes |
|-----|-----|------:|----------|-------|
| cefr-threshold-1990 | `output/cefr-threshold-1990/Threshold_1990.md` | 192 | **versions/002** | Native/OCR body + **Vision-rewritten App A** (pages 124–130): five nuclear tones full definitions + uses; `[LF]/[HF]/[LR]/[HR]/[FR]` encoding |
| cefr-waystage-1990 | `output/cefr-waystage-1990/Waystage_1990.md` | 120 | **versions/002** | Image PDF → full OCR; **Vision-rewritten App A** (pages 77–79) same five-tone model |
| cefr-en-2001 | `output/cefr-en-2001/CEFR_EN_2001.md` | 273 | **versions/002** | Native PDF text + pymupdf tables; **Table 1 global scale** + **Table 2 self-assessment stitched 35–36** + Figure 1 branching tree |

## Companion lessons applied

| Lesson | How applied |
|--------|-------------|
| `<!-- page:N -->` after each page body | All three books |
| Prose `el:start` / `el:end` wrappers | Per-page blocks |
| `db:id` on document + key sections/tables | Nuclear tones, major sections, CEFR tables/figure |
| Multipage tables → one full grid / one `db:id` | CEFR 2001 Table 2 self-assessment stitched |
| Blank line before tables | Polish pass |
| Intonation not left to raw OCR | Vision page overrides for App A both 1990 books |
| Page PNG evidence retained | `work/<job>/page_renders/` |
| Page overrides for Vision rewrites | `work/<job>/page_overrides/page_NNN.md` |

## Nuclear tones (both 1990 books) — Vision verified

| # | Name | Code | Mark position |
|---|------|------|---------------|
| 1 | Low falling | **[LF]** | Falling mark **below** line |
| 2 | High falling | **[HF]** | Falling mark **above** line |
| 3 | Low rising | **[LR]** | Rising mark **below** line |
| 4 | High rising | **[HR]** | Rising mark **above** line |
| 5 | Falling-rising | **[FR]** | V-shaped mark **above** line |

Also documented: nucleus, head, major/minor tone groups (`[||]` / `[|]`), secondary stress dots as `-`.

Uses by sentence type (declarative / yes-no / *wh* / imperative) for each tone are Vision-transcribed into App A body (Threshold fuller set; Waystage selection).

## Scripts

| Script | Role |
|--------|------|
| `scripts/vision_extract/assemble_book_md.py` | Render + OCR + assemble with overrides |
| `scripts/vision_extract/polish_books.py` | Reassemble all three + section IDs + snapshot |
| `scripts/vision_extract/fix_cefr2001_tables.py` | Companion-quality Table 1/2 + Figure 1 |

## Residual honesty

- Threshold body outside App A remains OCR/native mix (Paper Capture noise on some pages).  
- Waystage body outside App A is Tesseract (image PDF) — multi-column list pages may need further Vision overrides.  
- CEFR 2001: auto-extracted tables on other pages vary in quality; **Tables 1–2** and **Figure 1** are product-critical and polished. Table 3 (qualitative aspects of spoken language) remains auto-extract quality.  
- Further polish: drop page_overrides under `work/<job>/page_overrides/` and re-run `assemble_book_md.py --assemble-only` or `polish_books.py`.

## APPROVED

All three jobs: `APPROVED.json` → `versions/002`.
