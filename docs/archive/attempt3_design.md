# Attempt 3: Inventory Contract Fixes

## Goal

Fix inventory/extraction contract violations causing missing page-25 prose, duplicate footnote 19, page-47 ordering errors, and spurious `span_duplicate_emit` (including page 147). No dedupe band-aids — single ownership per zone.

## Contract Principles

1. Inventory schedules every visible PDF zone once
2. Span end pages skip table re-emit only; still schedule trailing prose and footnote_zone
3. Spans are merged chains (e.g. 146–148), not adjacent pairs
4. Footnotes emit only via footnote_zone elements in reading_order
5. Figure pages split zones by caption y-position

## PR Plan

### PR 1: Span chain merge and debug tooling

- **Description:** Merge adjacent same-group spans into single chains in `span_detector.py`. Fix `inventory.py` to assign start/middle/end roles and prefer longest span per page. Add `pipeline/debug_page.py` for collaborative PDF verification. Add explicit `scale_sign_language_repertoire` 146–148 entry.
- **Files/components affected:** `pipeline/span_detector.py`, `pipeline/inventory.py`, `pipeline/debug_page.py`
- **Dependencies:** None

### PR 2: Span-end trailing prose and footnote ownership

- **Description:** On span continuation end pages, schedule `trailing` prose and `footnote_zone` below table bbox instead of full `span_continuation_skip`. Remove footnote re-collection from `_extract_span_body` in `extract_chunk.py` — footnotes emit only via `footnote_zone` scheduled in reading_order.
- **Files/components affected:** `pipeline/page_elements.py`, `pipeline/extract_chunk.py`
- **Dependencies:** PR 1

### PR 3: Page 47 figure zone split

- **Description:** Split `_figure_mixed_order` by figure caption y-position: intro (Chapter 3 title) → figure ref → body (3.1. RECEPTION + prose at y≈655+). Add `section_headers_with_y()` in `descriptor_layout.py`. Do not prepend section headers to intro zone.
- **Files/components affected:** `pipeline/page_elements.py`, `pipeline/descriptor_layout.py`
- **Dependencies:** PR 2

### PR 4: Validator contract gates

- **Description:** Add `span_chain_integrity`, `span_end_trailing_scheduled`, and `footnote_single_owner` checks to `output_validator.py`. Bespoke gates for pages 25, 47, 146–148.
- **Files/components affected:** `pipeline/output_validator.py`
- **Dependencies:** PR 3

### PR 5: Pipeline re-run and documentation

- **Description:** Run `spans`, `inventory`, partial re-extract (chunk_01, chunk_02, chunk_06), cleanup, merge, postprocess, validator. Update `metadata/EXTRACTION_DEBUG_HISTORY.md` with attempt 3 outcomes.
- **Files/components affected:** `metadata/EXTRACTION_DEBUG_HISTORY.md`, pipeline outputs
- **Dependencies:** PR 4

## Success Criteria

| Page | Pass |
|------|------|
| 25 | "In addition to Chapter 2…" prose after Table 2; footnote 19 once, footnote 20 once |
| 47 | Chapter 3 → Figure 11 → 3.1. RECEPTION → body (per PDF order) |
| 146–148 | Single merged span; page 147 not in span_duplicate_emit |