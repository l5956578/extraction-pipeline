# CEFR Companion Volume — Extraction Pipeline

Extracts all content (prose, tables, figures, appendices) from the CEFR Companion Volume PDF into database-ready Markdown.

## Quick start

```bash
pip install -r requirements.txt
python run_pipeline.py --step all
```

To re-run prose formatting on the final file without a full merge:

```bash
python run_pipeline.py --step postprocess
```

To refresh figure diagrams without re-extracting the PDF:

```bash
python run_pipeline.py --step figures
```

Requires Tesseract OCR (for rotated pages).

## Debug history (persistent across sessions)

**`metadata/EXTRACTION_DEBUG_HISTORY.md`** — canonical notes on what was tried (reading_order overhaul + remaining-fixes), what the audits claimed vs what broke, validator state, and next steps. Update this file after every fix attempt; do not rely on chat memory.

## Output

| Path | Description |
|------|-------------|
| `final_output/CEFR_Companion_Volume.md` | **The** final Markdown deliverable (merge + figures + formatted prose) |
| `final_output/manifest.json` | Website navigation + product catalog |
| `final_output/db_import_registry.json` | Flat artifact registry for SQLite ETL |
| `final_output/assets/figures/` | Figure assets (PNG only for Figure 4 rainbow) |
| `metadata/figures_registry.json` | All 20 figures with `render_as` classification |
| `metadata/figures_handling.md` | Figure policy: text diagrams vs PNG vs mermaid |
| `metadata/post_processing.md` | Formatting rules (integrated into merge) |
| `metadata/last_format_run.txt` | Timestamp and hashes from last format pass |

## Folder structure

- `chunks/` — span-safe PDF chunks
- `inventories/` — per-page content inventories
- `raw_extraction/` — pre-cleanup Markdown per chunk
- `cleaned/` — post-cleanup Markdown
- `metadata/` — span detection, validation, reports

## Key artifacts

- **Base product:** `table_self_assessment_grid` (Appendix 2, pages 177–181)
- **Merged continuation:** `scale_vocabulary_control` (pages 132–133)

See `metadata/sqlite_schema_notes.md` for database import guidance.