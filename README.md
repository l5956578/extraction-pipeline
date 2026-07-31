# Extraction Pipeline (multi-job)

**Location:** `D:\y\lang-platform\pipelines\extraction-pipeline`  
Nested under the lang-platform monorepo; this folder remains its own git root.

General PDF→Markdown engine with **per-document jobs**. First **active** production job: **CEFR Companion Volume (EN 2020)**. Additional CEFR-family jobs are registered as **draft** (sources + sidecars only).

| Document | Role |
|----------|------|
| **[`STATUS.md`](STATUS.md)** | **Start here** — work done, open backlog, job registry, runbook |
| [`AGENTS.md`](AGENTS.md) | Agent entrypoint (same pointers) |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Pipeline design & contracts |
| [`input/cefr-family-NOTES.md`](input/cefr-family-NOTES.md) | CEFR source lineage / output-mode intent |

---

## Quick start

```bash
pip install -r requirements.txt
# --job is required (Phase B)
python run_pipeline.py --job cefr-companion-2020 --step all
python run_pipeline.py --job cefr-companion-2020 --step postprocess
```

After any path that writes shippable live output, the suite **automatically**:

1. Runs high-value regression (`pipeline/regression.py`)
2. On hard-pass → creates `output/<job-id>/versions/00N/` (never overwrites prior)

### Common commands

```bash
# Full production extract (uses current inventories + rotated vision markdown)
# → live output → regression → versions/00N if pass
python -u run_production_extract.py --job cefr-companion-2020

# Format-only (~4s) — list spacing, footers, bold, etc. (same auto-version hook)
python iterate_format.py --job cefr-companion-2020
python iterate_format.py --job cefr-companion-2020 --skip-regression

# Manual regression / version snapshot
python -m pipeline.regression --job cefr-companion-2020
python -m pipeline.regression --job cefr-companion-2020 --no-version

# Approve a version for production promotion
python -m pipeline.approve --job cefr-companion-2020 --list
python -m pipeline.approve --job cefr-companion-2020 --version 001

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

Each document is a **job id** (kebab-case). Working source is always `source.<ext>` with provenance in `job.json` (`source.original_filename`, optional `sha256`).

### Registry

| Job id | Status | Profile | Output mode |
|--------|--------|---------|-------------|
| `cefr-companion-2020` | **active** | `cefr_companion` | `markdown` |
| `cefr-en-2001` | **draft** | `cefr_classic` | `markdown` |
| `cefr-waystage-1990` | **draft** | `cefr_classic` | `page_png` |
| `cefr-threshold-1990` | **draft** | `cefr_classic` | `page_png` |
| `cefr-descriptors-2020` | **draft** | `tabular_db` | `tabular_db` |
| `cefr-english-grammar-profile-online-202607` | **draft** | `tabular_db` | `tabular_db` |
| `cefr-self-assessment-grid-cn` | **draft** | `markdown_import` | `markdown_import` |

Full detail: [`STATUS.md` §1a](STATUS.md). Draft jobs have sources + empty `work/` scaffolding only — **not** production-extracted.

### Paths

| Path | Role |
|------|------|
| `input/<job-id>/source.pdf` (or `.xlsx` / `.md`) | Working source name (`source.file` in job.json) |
| `input/<job-id>/job.json` | Required sidecar (`original_filename`, profile, layout, output.mode) |
| `input/<job-id>/notes.md` | Optional human notes |
| `profiles/<profile>.json` | Shared family defaults (`cefr_companion`, `cefr_classic`, `tabular_db`, `markdown_import`) |
| `work/<job-id>/inventories/` | `reading_order` contracts |
| `work/<job-id>/{chunks,raw_extraction,cleaned,metadata}/` | Intermediates (not promoted) |
| `output/<job-id>/` | **Live** shippable MD + assets + registries (overwritten on iterate) |
| `output/<job-id>/versions/00N/` | Append-only snapshots after regression pass |
| `output/<job-id>/APPROVED.json` | Points at the version allowed for production promote |

CLI: `--job <id>` is **required** on all entry scripts (Phase B). Layout lives in `job.json` + `profiles/*.json`.

---

## Output (shippable) — Companion job

| Path | Description |
|------|-------------|
| `output/cefr-companion-2020/CEFR_Companion_Volume.md` | Final Markdown deliverable |
| `output/cefr-companion-2020/manifest.json` | Navigation + product catalog |
| `output/cefr-companion-2020/db_import_registry.json` | Artifact registry for ETL (JSON **array**; per-row `product_tiers`) |
| `output/cefr-companion-2020/JOB_MANIFEST.json` | Job-level promotion envelope + business tags (`product` from job.json) |
| `output/cefr-companion-2020/product_context.json` | Job-level product + pointer to registry (does not wrap the array) |
| `output/cefr-companion-2020/assets/figures/` | Figure assets |

**Phase D business tags:** job-level tags live in `input/<job-id>/job.json` → `product` (framework, audiences, default_product_tiers, skill_categories, promotion_target) and are re-emitted into `JOB_MANIFEST.json` / `product_context.json` by `pipeline/job_manifest.write_job_manifest`. Per-artifact `product_tiers` stay on each `db_import_registry.json` row. Regenerated after merge / format / production extract.

Promotion (platform): **copy** from `output/<job-id>/` (including JOB_MANIFEST) → `lang-platform/staging/pending/extraction-pipeline/<job-id>/`; then to `production/<product.promotion_target>/` (Companion: `resources/cefr` → `production/resources/cefr/`). See monorepo `docs/PROMOTION.md`. Do not promote intermediates. Default action is **copy**.

---

## Layout (engine + I/O)

| Path | Role |
|------|------|
| `pipeline/` | General engine (`job_context.load_job`, `bootstrap`, thin `config`) |
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
