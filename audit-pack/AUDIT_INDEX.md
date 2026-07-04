# CEFR Extraction Pipeline — Audit Pack

**Created:** 2026-06-16  
**Project:** extraction-pipeline  
**PDF:** 278 pages → single Markdown deliverable

## ⚠️ Canonical debug history (read first across sessions)

**`../metadata/EXTRACTION_DEBUG_HISTORY.md`** — persistent record of both fix attempts (`e3d7fbe`, `078f0b8`), honest outcomes, validator counts, and what still fails.  
This audit pack is supplementary; several files here are **stale** relative to current `metadata/output_validation.json`.

## How to use this pack

Read **`metadata/EXTRACTION_DEBUG_HISTORY.md` first**, then files in numbered order: design → rules → proof → sample output.

| File | Purpose |
|------|---------|
| `00_ORIGINAL_SESSION_PLAN.md` | Original Grok plan-mode design brief (some items superseded) |
| `01_README.md` | How to run the pipeline, folder layout, deliverables |
| `02_extraction_plan.md` | **Current** operational rules (layout, inventory, validation) |
| `03_output_validation.json` | Last merge validation (`valid`, issues, page count) |
| `04_sample_inventory_chunk_03.json` | Per-page spec for PDF pages 51–75 |
| `05_db_import_registry.json` | All artifacts: IDs, pages, product tiers |
| `06_manifest.json` | Website navigation + product catalog |
| `07_spanning_tables.json` | Multi-page merge groups |
| `08_post_processing.md` | Final formatting step (inside merge) |
| `09_figures_handling.md` | Figure policy |
| `10_chunks.json` | Chunk ↔ page range mapping |
| `11_sample_output_pages_47-56.md` | Deliverable excerpt for spot-check |

## Pipeline flow

```
PDF → spans → chunks → inventory → extract → cleanup → merge → validate
```

**Entry point:** `run_pipeline.py`

## Full deliverable (not in this pack)

`../final_output/CEFR_Companion_Volume.md`

## Re-run validation

```bash
python run_pipeline.py --step merge
```

Check `../metadata/output_validation.json`.

## Plan files

- `00_*` = Grok `/plan-view` session plan
- `02_*` = living spec (authoritative for current behavior)
