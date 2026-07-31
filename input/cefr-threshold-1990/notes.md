# Job notes — cefr-threshold-1990

**Status:** approved MD deliverable (vision/OCR assembly) — **versions/002**  
**Deliverable:** `output/cefr-threshold-1990/Threshold_1990.md`  
**APPROVED:** `output/cefr-threshold-1990/APPROVED.json` → `versions/002`

## Method

- Not a reimplementation of the Companion multi-week engine.
- Render PDF pages → OCR/native text assembly + **Vision page overrides** for Appendix A.
- Companion conventions: `<!-- page:N -->`, `el:start`/`el:end`, `db:id` on document + key sections.

## Critical: five nuclear tones (App A)

Vision-verified from page renders 124–130. Used throughout the book.

| Code | Name |
|------|------|
| **[LF]** | Low falling (mark below line) |
| **[HF]** | High falling (mark above line) |
| **[LR]** | Low rising (rise mark below) |
| **[HR]** | High rising (rise mark above) |
| **[FR]** | Falling-rising (v-mark above) |

Artifact: `threshold_five_nuclear_tones`  
Overrides: `work/cefr-threshold-1990/page_overrides/page_124.md` … `page_130.md`  
PNGs: `work/cefr-threshold-1990/page_renders/`

## Residual

Body pages outside App A remain OCR/native mix; further `page_overrides` optional.

See `docs/library/EXTRACTION_STATUS_1990_2001.md` and outlines.
