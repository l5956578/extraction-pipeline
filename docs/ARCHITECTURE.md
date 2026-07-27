# Architecture — multi-job extraction pipeline

**Companion to [`STATUS.md`](../STATUS.md)** (project status and backlog).  
This document describes **how the system is designed**, not day-to-day status.

---

## 1. Goals

- Multi-document: one **job** per PDF under `input|work|output/<job-id>/`
- Shared general engine in `pipeline/`; per-PDF knowledge in `job.json` + inventories
- Companion deliverable: `output/cefr-companion-2020/CEFR_Companion_Volume.md`
- Stable `<!-- db:id=… -->` artifact headers for ETL
- Page anchors `<!-- page:N -->` for every PDF page 1–278 (Companion)
- Faithful prose, tables, footnotes, and figures (with explicit figure policy)

---

## 1b. Job layout & JobContext

```
extraction-pipeline/
├── pipeline/                 # general engine
├── profiles/<profile>.json   # shared family defaults
├── input/<job-id>/
│   ├── source.pdf
│   ├── job.json              # required (original_filename, profile, layout)
│   └── notes.md              # optional
├── work/<job-id>/
│   ├── inventories/
│   ├── chunks/, raw_extraction/, cleaned/, metadata/
└── output/<job-id>/          # shippable only
```

- **`pipeline/job_context.py`:** `JobContext`, `load_job(job_id)`, JSON merge, layout parse (job + profile only).
- **`pipeline/config.py`:** engine constants + **module attributes** for paths/layout after load.
- **`pipeline/bootstrap.py`:** shared CLI helper — required `--job`, then `load_job`.
- **`--job` is required** on all entry scripts (no default to Companion).
- **No import-time load** — importing `pipeline.config` does not select a job (`get_active_job()` is `None` until bootstrap).
- **Access pattern:** `import pipeline.config as cfg` then `cfg.PDF_PATH` / `cfg.FINAL_DIR` / `cfg.TOC_PAGE_RANGE` at **call time**. Do not `from pipeline.config import PDF_PATH` (freezes the binding).
- **Layout SoT:** `input/<job>/job.json` + `profiles/<profile>.json` only (no Python `_DEFAULT_*` dual-write).
- **Feature flags:** `extraction.features` (e.g. `callouts`) via `feature_enabled("callouts")`; Companion-hardcoded adjacent gates skip for other profiles.
- **One process ≈ one load:** same `job_id` returns a cached context; pass `load_job(id, reload=True)` after editing sidecars.

CLI: `run_pipeline.py --job <id>`, `run_production_extract.py --job <id>`, `iterate_format.py --job <id>`.

---

## 2. Pipeline stages

Paths below are relative to the **active job** (`work/<job-id>/`, `output/<job-id>/`).

```
0. spans      span_detector → work/<job>/metadata/spanning_tables.json
1. chunker    optional PDF chunks under work/<job>/chunks/
2. inventory  work/<job>/inventories/*_inventory.json (reading_order)
3. extract    work/<job>/raw_extraction/chunk_*.md
4. cleanup    work/<job>/cleaned/chunk_*.md
5. merge      output/<job>/<markdown_name> (+ registry, manifest)
6. figures    apply_figures (inject diagrams / PNG refs)
7. format     pipeline/post_process.py (in-place on final MD)
8. validate   output_validator / validators
```

Orchestration: `run_pipeline.py`  
Full production convenience: `run_production_extract.py`  
Format-only loop: `iterate_format.py`

---

## 3. Extraction contract

> **Binding detail:** [`docs/CONTRACTS.md`](CONTRACTS.md) — inventory SoT, callout format (UV-01), figures, hyperlinks, cell `<br>`, validation fail-closed, agent-in-loop triggers.  
> Do not invent parallel layouts that fight those rules (STATUS E5 / UV-05 / UV-08).  
> **Adjacent-element damage (C2-ADJ):** plan + done/remains ledger — [`docs/ADJACENT_ELEMENT_PROTECTION.md`](ADJACENT_ELEMENT_PROTECTION.md).

### 3.1 Inventory `reading_order`

Each page lists ordered elements. Extract iterates this list **strictly**.

| Element type | Typical extractor | Role |
|--------------|-------------------|------|
| `prose` | `prose_zone`, `rich_page` | Intro / interstitial / trailing / side / body |
| `artifact` | `pdfplumber_table`, `rotated_table`, `section_block_merge` | Tables / scales / **callouts** (`artifact_type=callout`) |
| `span_continuation_skip` | — | Continuation page: no re-emit of multipage body |
| `footnote_zone` | `footnote_zone`, `rotated_footnote_zone` | Numbered notes |
| `footer` | `page_footer` | Footnotes (if not already emitted) + page marker |
| `toc` | `toc_layout` | Pages 5–9 |
| `figure` / `figure_page` | figure stub + inject; multi-fig must list all registry figures | Figures |

### 3.2 Multipage artifacts

Configured in `input/<job-id>/job.json` layout (`MULTIPAGE_ARTIFACTS`, `SECTION_BLOCKS`, known tables) and `work/<job-id>/metadata/spanning_tables.json`.

- Emit full table body on **start** page only.
- Continuation pages: trailing prose + footnotes + page footer only.

### 3.3 Page layout

`page_layout.py`:

- Sort lines by `y`; classify body / footnote / page_marker
- **Paragraph join by vertical gap** (`_PARAGRAPH_Y_GAP ≈ 15pt`), not capital-after-period alone
- Dingbat fonts mapped (e.g. footer arrow `3` → `▶`, list bullet `f` kept for list detection)
- Bold via PDF flag **or** Bold/Semibold font name
- Page caption **before** `<!-- page:N -->`

### 3.4 Prose above/below tables

`descriptor_layout.py` + `page_elements.prose_segments`:

- Zones: intro / interstitial / trailing relative to table bboxes
- Trailing prose **stops at first footnote/page-marker y** (`first_footer_band_y`) so multipage table tails do not ingest footnotes
- Section lines (`N.N. …`) and `Table N – …` captions are structural blocks (own paragraphs)

---

## 4. Rotated tables

### 4.1 Why a special path

Rotated descriptor scales (~90° text) are not reliable via pdfplumber geometry or Tesseract OCR (column order, multi-row levels, dropped “Can …” lines, continuation mixing).

### 4.2 Design

| Stage | Location |
|-------|----------|
| Detect | Inventory `table_orientation: rotated_*`, `extractor: rotated_table` |
| Prepare | `prepare_rotated_for_grok.py` → `work/<job>/metadata/rotated_for_grok/` |
| Authoritative extract | Coding agent vision → `work/<job>/metadata/rotated_from_grok/{slug}.md` |
| Assemble | `rotated_grok_vision.assemble_grok_rotated_span` |
| Fallback | Geometry (no forced OCR thrash); HTML `AGENT_VISION_PENDING` |

Slug: `page_{NNN}_{span_group_id}`  
Procedure: `work/cefr-companion-2020/metadata/ROTATED_TABLES_AGENT_VISION.md`

### 4.3 Footnotes on rotated pages

Remain on **geometry** path (`rotated_footnote_zone` / surgical extract). Not vision.

---

## 5. Cleanup vs postprocess

| Layer | Module | Scope |
|-------|--------|-------|
| Chunk cleanup | `pipeline/cleanup.py` | Hyphenation, ligatures, reverse-gibberish cells, page-marker dedupe, `prose_format.normalize_prose` |
| Final format | `pipeline/post_process.py` + `prose_format.py` | List repair, page footers, chapters, TOC, bold normalize |

**Legacy:** Standalone Session-2 lived under `post-processing/`. Logic is integrated.  
`post-processing/format_markdown.py` is a thin CLI alias for `run_post_process`.  
Historical snapshot: `docs/archive/CEFR_Companion_Volume_structured.legacy.md`.

---

## 6. Figures

- Policy: `work/cefr-companion-2020/metadata/figures_handling.md`
- Registry: `work/cefr-companion-2020/metadata/figures_registry.json`
- Inject: `apply_figures` after merge; skip TOC region

---

## 7. Validation

- Per-chunk: `validators.py` (during pipeline)
- Final: `output_validator.py` → `work/cefr-companion-2020/metadata/output_validation.json`
- **Contract gates (fail closed):** `pipeline/contract_validators.py` — soup, multi-fig, callouts, links, URLs, empty tables (see CONTRACTS §8)

**Policy:** Green mass-only checks ≠ fixed. STATUS “resolved” requires the named contract gate green. User PDF QA remains authoritative for crop quality and residual layout.

---

## 8. Key modules

| Path | Responsibility |
|------|----------------|
| `pipeline/extract_chunk.py` | reading_order dispatch |
| `pipeline/page_elements.py` | inventory reading_order builder |
| `pipeline/page_layout.py` | body/footnote/marker + y-gap paragraphs |
| `pipeline/descriptor_layout.py` | prose zones around tables |
| `pipeline/extractors/rotated_grok_vision.py` | rotated PNG handoff + assemble |
| `pipeline/extractors/rotated.py` | geometry/OCR fallback |
| `pipeline/post_process.py` | final MD structure |
| `pipeline/merge_output.py` | concatenate cleaned chunks |

---

## 9. Related historical docs

See `docs/archive/` for attempt 2–4 debug history and pre-restructure plans.  
**Do not** treat archive as current status.
