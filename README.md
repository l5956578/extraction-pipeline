# CEFR Companion Volume — Extraction Pipeline

**Location:** `D:\y\lang-platform\pipelines\extraction-pipeline`  
(Moved from `C:\Users\59565\Documents\Python Scripts\extraction-pipeline`. Nested under the lang-platform monorepo; this folder remains its own git root.)

Extracts the CEFR Companion Volume PDF into **database-ready Markdown**.

| Document | Role |
|----------|------|
| **[`STATUS.md`](STATUS.md)** | **Start here** — work done, open backlog, runbook |
| [`AGENTS.md`](AGENTS.md) | Agent entrypoint (same pointers) |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Pipeline design & contracts |

---

## Quick start

```bash
pip install -r requirements.txt
python run_pipeline.py --step all
```

### Common commands

```bash
# Full production extract (uses current inventories + rotated vision markdown)
python -u run_production_extract.py

# Format-only (~4s) — list spacing, footers, bold, etc.
python iterate_format.py

# Rotated table PNG prep
python prepare_rotated_for_grok.py

# After agent vision markdown is written
python finalize_after_grok.py
```

### Rotated tables

Geometry/OCR are **not** production quality for rotated descriptor scales.  
**Coding-agent vision** writes `metadata/rotated_from_grok/*.md`. See:

- [`STATUS.md`](STATUS.md) §6 (coverage)
- [`metadata/ROTATED_TABLES_AGENT_VISION.md`](metadata/ROTATED_TABLES_AGENT_VISION.md)

**Appendix 5 (pp. 191–241)** still needs vision markdown (open item R1).

---

## Output

| Path | Description |
|------|-------------|
| `final_output/CEFR_Companion_Volume.md` | Final Markdown deliverable |
| `final_output/manifest.json` | Navigation + product catalog |
| `final_output/db_import_registry.json` | Artifact registry for ETL |
| `final_output/assets/figures/` | Figure assets |

---

## Layout

| Path | Role |
|------|------|
| `pipeline/` | Extractors, layout, cleanup, postprocess |
| `inventories/` | Per-chunk `reading_order` contracts |
| `raw_extraction/` / `cleaned/` | Intermediate Markdown |
| `metadata/rotated_for_grok/` | Rotated table PNG handoffs |
| `metadata/rotated_from_grok/` | Agent-vision table markdown |
| `post-processing/` | Thin CLI only (`format_markdown.py`) |
| `docs/archive/` | Historical notes (not current status) |

---

## Requirements

- Python 3.11+ recommended
- `pip install -r requirements.txt`
- Tesseract only if forcing OCR fallback on rotated pages (not the default path)
