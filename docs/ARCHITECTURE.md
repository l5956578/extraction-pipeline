# Architecture — CEFR Companion Volume extraction pipeline

**Companion to [`STATUS.md`](../STATUS.md)** (project status and backlog).  
This document describes **how the system is designed**, not day-to-day status.

---

## 1. Goals

- One Markdown deliverable: `output/CEFR_Companion_Volume.md`
- Stable `<!-- db:id=… -->` artifact headers for ETL
- Page anchors `<!-- page:N -->` for every PDF page 1–278
- Faithful prose, tables, footnotes, and figures (with explicit figure policy)

---

## 2. Pipeline stages

```
0. spans      span_detector → metadata/spanning_tables.json
1. chunker    optional PDF chunks under chunks/
2. inventory  per-chunk inventories/*_inventory.json (reading_order)
3. extract    raw_extraction/chunk_*.md
4. cleanup    cleaned/chunk_*.md
5. merge      output/CEFR_Companion_Volume.md (+ registry, manifest)
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

Configured in `pipeline/config.py` (`MULTIPAGE_ARTIFACTS`, `SECTION_BLOCKS`) and `metadata/spanning_tables.json`.

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
| Prepare | `prepare_rotated_for_grok.py` → `metadata/rotated_for_grok/` |
| Authoritative extract | Coding agent vision → `metadata/rotated_from_grok/{slug}.md` |
| Assemble | `rotated_grok_vision.assemble_grok_rotated_span` |
| Fallback | Geometry (no forced OCR thrash); HTML `AGENT_VISION_PENDING` |

Slug: `page_{NNN}_{span_group_id}`  
Procedure: `metadata/ROTATED_TABLES_AGENT_VISION.md`

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

- Policy: `metadata/figures_handling.md`
- Registry: `metadata/figures_registry.json`
- Inject: `apply_figures` after merge; skip TOC region

---

## 7. Validation

- Per-chunk: `validators.py` (during pipeline)
- Final: `output_validator.py` → `metadata/output_validation.json`
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
