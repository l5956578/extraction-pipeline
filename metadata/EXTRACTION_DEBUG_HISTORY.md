# Extraction Debug History

## Attempt 3 (2026-07-04) — Inventory contract fixes

**Branch:** `execute-plan/c0b4a280-pr-5-pipeline-re-run-and-documentation`  
**Design:** `metadata/attempt3_design.md`  
**Base commits:** PRs 1–4 through `1bdd8a1` (validator contract gates)

### Goal

Fix inventory/extraction contract violations on pages 25, 47, and 146–148 without dedupe band-aids: single zone ownership, merged span chains, span-end trailing prose, figure zone split, and validator bespoke gates.

### Pipeline run (partial re-extract)

```powershell
python run_pipeline.py --step spans
python run_pipeline.py --step inventory
python -m pipeline.extract_chunk chunk_01
python -m pipeline.extract_chunk chunk_02
python -m pipeline.extract_chunk chunk_06
python run_pipeline.py --step cleanup
python run_pipeline.py --step merge
python run_pipeline.py --step postprocess
python -m pipeline.output_validator
```

Chunks 03–05 and 07–10 were **not** re-extracted; they retain prior extraction output.

### PR 5 code fixes discovered during re-run

1. **`pipeline/extract_chunk.py` CLI** — `python -m pipeline.extract_chunk chunk_01` previously called `extract_all_chunks()`. Added argparse so a positional `chunk_id` extracts one chunk only.
2. **`pipeline/extract_chunk.py` figure elements** — `reading_order` `type: figure` entries (e.g. page 47 Figure 11) were silently skipped. Now emit `figure_block()` for catalogued text/mermaid figures.
3. **`pipeline/apply_figures.py`** — `run_merge()` calls `apply_figures`, which stripped pre-injected `db:id=figure_*` blocks then failed to re-inject (caption matcher ignored `###` headers). Fixed to preserve already-injected figure blocks and improved `figure_inject._caption_matches` for `###` captions.

### Target-page verification (`final_output/CEFR_Companion_Volume.md`)

| Page | Criterion | Result | Notes |
|------|-----------|--------|-------|
| **25** | "In addition to Chapter 2…" prose after Table 2 | **PASS** | Trailing prose present in section before `<!-- page:25 -->`; Table 2 span includes page-25 rows. |
| **25** | Footnote 19 exactly once | **PASS** | Single `19.` line in pages 24–25 region; `footnote_single_owner` gate clean. |
| **47** | Chapter 3 → Figure 11 → 3.1. RECEPTION | **PASS** | Order: `## Chapter 3` → `db:id=figure_11_reception_activities_strategies` diagram → `### 3.1. RECEPTION` → body prose before `<!-- page:47 -->`. |
| **147** | Not in `span_duplicate_emit` | **PASS** | No `span_duplicate_emit` issues; merged 146–148 span chain intact. |

### Validator bespoke gates (attempt 3 contract)

| Gate | Result |
|------|--------|
| `missing_page_25_trailing_prose` | **PASS** (0 issues) |
| `footnote_single_owner` | **PASS** (0 issues) |
| `page_47_section_order` | **PASS** (0 issues) |
| `page_147_span_duplicate` / `span_duplicate_emit` @ 147 | **PASS** (0 issues) |
| `span_chain_integrity` | **PASS** (0 issues) |
| `span_end_trailing_scheduled` | **PASS** (0 issues) |

### Overall validator status

**`valid: false`** — 108 issues (`metadata/output_validation.json`), dominated by:

- **18 `missing_artifact`** — PNG figures (Figures 1–10, etc.) not re-injected because partial re-extract did not touch all figure-hosting chunks and PNG injection still depends on caption lines in non-re-extracted regions.
- **57 `page_under_extracted`** — expected for chunks 03–05, 07–10 left stale.
- **25 `missing_section_header`**, **5 `empty_page_section`**, **3 `missing_page_artifact`** — pre-existing gaps outside attempt-3 scope.

Attempt-3 **contract targets are met**; full-document `valid: true` requires a complete re-extract of all chunks (or targeted figure chunk re-runs) plus broader coverage fixes.

### Honest assessment

- **Fixed:** Page-25 trailing prose scheduling, footnote-19 single ownership, page-47 zone ordering (Chapter 3 / Figure 11 / 3.1. RECEPTION), page-147 span duplicate emit, span chain merge 146–148.
- **Still open:** Global figure PNG placement on non-re-extracted pages; duplicate page-45 footer block in merged output; footnote-20 appears twice on page 25 (page marker boundary); full 278-page coverage validation.

### Debug tooling

Use `python -m pipeline.debug_page <page_num>` to inspect PDF zones vs inventory `reading_order` for collaborative verification.