# Extraction Pipeline (multi-job)

**Location:** `D:\y\lang-platform\pipelines\extraction-pipeline`  
Nested under the lang-platform monorepo; this folder remains its own git root.

General PDF→Markdown engine with **per-document jobs**. First production job: **CEFR Companion Volume (EN 2020)**.

| Document | Role |
|----------|------|
| **[`STATUS.md`](STATUS.md)** | **Start here** — work done, open backlog, runbook |
| [`AGENTS.md`](AGENTS.md) | Agent entrypoint (same pointers) |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Pipeline design & contracts |

---

## Quick start

```bash
pip install -r requirements.txt
# Phase A: --job defaults to cefr-companion-2020
python run_pipeline.py --step all
python run_pipeline.py --job cefr-companion-2020 --step postprocess
```

### Common commands

```bash
# Full production extract (uses current inventories + rotated vision markdown)
python -u run_production_extract.py --job cefr-companion-2020

# Format-only (~4s) — list spacing, footers, bold, etc.
python iterate_format.py --job cefr-companion-2020

# Rotated table PNG prep
python prepare_rotated_for_grok.py --job cefr-companion-2020

# After agent vision markdown is written
python finalize_after_grok.py --job cefr-companion-2020
```

### Rotated tables

Geometry/OCR are **not** production quality for rotated descriptor scales.  
**Coding-agent vision** writes `work/<job-id>/metadata/rotated_from_grok/*.md`. See:

- [`STATUS.md`](STATUS.md) §6 (coverage)
- [`work/cefr-companion-2020/metadata/ROTATED_TABLES_AGENT_VISION.md`](work/cefr-companion-2020/metadata/ROTATED_TABLES_AGENT_VISION.md)

---

## Jobs

Each document is a **job id** (kebab-case), e.g. `cefr-companion-2020`:

| Path | Role |
|------|------|
| `input/<job-id>/source.pdf` | Working PDF name |
| `input/<job-id>/job.json` | Required sidecar (`original_filename`, profile, layout) |
| `input/<job-id>/notes.md` | Optional human notes |
| `profiles/<profile>.json` | Shared family defaults (e.g. `cefr_companion`) |
| `work/<job-id>/inventories/` | `reading_order` contracts |
| `work/<job-id>/{chunks,raw_extraction,cleaned,metadata}/` | Intermediates (not promoted) |
| `output/<job-id>/` | Shippable MD + assets + registries |

CLI: `--job <id>` on entry scripts. **Phase A** defaults to `cefr-companion-2020` when omitted; later phases will require `--job`.

---

## Output (shippable) — Companion job

| Path | Description |
|------|-------------|
| `output/cefr-companion-2020/CEFR_Companion_Volume.md` | Final Markdown deliverable |
| `output/cefr-companion-2020/manifest.json` | Navigation + product catalog |
| `output/cefr-companion-2020/db_import_registry.json` | Artifact registry for ETL |
| `output/cefr-companion-2020/assets/figures/` | Figure assets |

Promotion (platform): **copy** from `output/<job-id>/` → `lang-platform/staging/pending/extraction-pipeline/<job-id>/` (see monorepo `docs/PROMOTION.md`). Do not promote intermediates.

---

## Layout (engine + I/O)

| Path | Role |
|------|------|
| `pipeline/` | General engine (JobContext via `pipeline.config.load_job`) |
| `profiles/` | Shared profile JSON |
| `input/<job-id>/` | Source PDF + sidecars |
| `work/<job-id>/` | Inventories + intermediates |
| `output/<job-id>/` | Shippable deliverables only |
| `post-processing/` | Thin CLI only (`format_markdown.py`) |
| `docs/archive/` | Historical notes (not current status) |

---

## Requirements

- Python 3.11+ recommended
- `pip install -r requirements.txt`
- Tesseract only if forcing OCR fallback on rotated pages (not the default path)
