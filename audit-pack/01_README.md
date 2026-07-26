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

## Output

| Path | Description |
|------|-------------|
| `output/CEFR_Companion_Volume.md` | **The** final Markdown deliverable (merge + figures + formatted prose) |
| `output/manifest.json` | Website navigation + product catalog |
| `output/db_import_registry.json` | Flat artifact registry for SQLite ETL |
| `output/assets/figures/` | Figure assets (PNG only for Figure 4 rainbow) |
| `work/metadata/figures_registry.json` | All 20 figures with `render_as` classification |
| `work/metadata/figures_handling.md` | Figure policy: text diagrams vs PNG vs mermaid |
| `work/metadata/post_processing.md` | Formatting rules (integrated into merge) |
| `work/metadata/last_format_run.txt` | Timestamp and hashes from last format pass |

## Folder structure

- `work/chunks/` — span-safe PDF chunks
- `inventories/` — per-page content inventories
- `work/raw_extraction/` — pre-cleanup Markdown per chunk
- `work/cleaned/` — post-cleanup Markdown
- `work/metadata/` — span detection, validation, reports

## Key artifacts

- **Base product:** `table_self_assessment_grid` (Appendix 2, pages 177–181)
- **Merged continuation:** `scale_vocabulary_control` (pages 132–133)

See `work/metadata/sqlite_schema_notes.md` for database import guidance.