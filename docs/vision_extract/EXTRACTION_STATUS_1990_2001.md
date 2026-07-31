# Extraction status — Threshold, Waystage, CEFR 2001

**Date:** 2026-07-31  
**Method:** **Full-book Vision page overrides** (every PDF page) + assembly.  
**Standard:** Match page structure — paragraphs, headers, lists, tables, intonation marks.

## Deliverables (APPROVED v004)

| Job | MD | Pages | Overrides | Notes |
|-----|-----|------:|----------:|-------|
| cefr-threshold-1990 | `output/cefr-threshold-1990/Threshold_1990.md` | 192 | **192/192** | TOC table; `### 1 Target Group` / `2 Criteria` / `3 Adaptability` as headers; App A tones ˎˋˏˊˇ |
| cefr-waystage-1990 | `output/cefr-waystage-1990/Waystage_1990.md` | 120 | **120/120** | Full Vision (image PDF); same tone system App A |
| cefr-en-2001 | `output/cefr-en-2001/CEFR_EN_2001.md` | 273 | **273/273** | Title/TOC/Prefatory fixed; Ch 3 scales/tables; all chapters via Vision |

## How it works

1. Agent Vision-reads `work/<job>/page_renders/page_NNN.png`
2. Writes `work/<job>/page_overrides/page_NNN.md` (truth for that page)
3. `format_extract.build_book` assembles product MD preferring overrides over OCR soup
4. Snapshot `versions/004/` + `APPROVED.json`

## Nuclear tones (Threshold + Waystage App A)

| Mark | Tone |
|------|------|
| **ˎ** | Low falling (below) |
| **ˋ** | High falling (above) |
| **ˊ** | High rising (above) |
| **ˏ** | Low rising (below) |
| **ˇ** | Falling-rising (v above) |
| **ˈ** | Head |
| **·** | Secondary stress |

## Scripts

- `scripts/vision_extract/format_extract.py` — assemble with overrides
- `scripts/vision_extract/native_page_overrides.py` — layout base (Vision upgrades replace)
- Parallel Vision agents covered all page ranges for three books

## Residual honesty

- Dense two-column notion/grammar index pages may still have residual OCR noise inside Vision-structured shells.
- Companion-class polish continues by rewriting individual `page_overrides/page_NNN.md` and re-running build.
- Re-run: `python -c "import sys; sys.path.insert(0,'scripts/vision_extract'); import format_extract as fe; ..."`

## APPROVED

All three: **`versions/004`**.
