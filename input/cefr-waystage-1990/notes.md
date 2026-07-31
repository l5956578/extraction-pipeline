# Job notes — cefr-waystage-1990

**Status:** approved MD deliverable (vision/OCR assembly) — **versions/002**  
**Deliverable:** `output/cefr-waystage-1990/Waystage_1990.md`  
**APPROVED:** `output/cefr-waystage-1990/APPROVED.json` → `versions/002`

## Method

- **Image PDF** (no reliable text layer) → full-page Tesseract OCR + Vision overrides for App A.
- Same product conventions as Threshold / Companion lessons.

## Critical: five nuclear tones (App A)

Same five-tone system as Threshold 1990. Vision-verified from page renders **77–79**.

| Code | Name |
|------|------|
| **[LF]** | Low falling |
| **[HF]** | High falling |
| **[LR]** | Low rising |
| **[HR]** | High rising |
| **[FR]** | Falling-rising |

Artifact: `waystage_five_nuclear_tones`  
Overrides: `work/cefr-waystage-1990/page_overrides/page_077.md` … `page_079.md`  
PNGs: `work/cefr-waystage-1990/page_renders/`

## Residual

Multi-column list pages may still be OCR-noisy; add page_overrides as needed.

See `docs/library/EXTRACTION_STATUS_1990_2001.md`.
