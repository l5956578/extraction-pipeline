# Job notes — cefr-en-2001

**Status:** approved MD deliverable (vision/OCR assembly) — **versions/002**  
**Deliverable:** `output/cefr-en-2001/CEFR_EN_2001.md`  
**APPROVED:** `output/cefr-en-2001/APPROVED.json` → `versions/002`

## Method

- Native PDF text primary (digital book).
- pymupdf table extraction for table pages.
- Companion-quality polish on product-critical structures:
  - **Table 1** Common Reference Levels: global scale (`cefr2001_table_1_common_reference_levels_global_scale`)
  - **Table 2** self-assessment grid **stitched** pages 35–36, one `db:id` (`cefr2001_table_2_self_assessment_grid`)
  - **Figure 1** A/B/C branching tree (`cefr2001_figure_01_common_reference_levels`)
- Section `db:id`s for chapters 1–9 + appendices A–D.

## Scripts

- `scripts/vision_extract/assemble_book_md.py`
- `scripts/vision_extract/polish_books.py`
- `scripts/vision_extract/fix_cefr2001_tables.py`

## Residual

Auto-extracted tables outside T1/T2 vary; Table 3 (qualitative spoken aspects) may need further Vision stitch. For **current** can-do wording prefer Companion Volume App 7.

See `docs/library/EXTRACTION_STATUS_1990_2001.md`.
