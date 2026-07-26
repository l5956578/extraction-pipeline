# Extraction Remaining Fixes Plan

**Status:** Implemented (`078f0b8`) — see honest outcomes in **`metadata/EXTRACTION_DEBUG_HISTORY.md`**  
**Worktree:** `D:\y\lang-platform\pipelines\extraction-pipeline`  
**Deliverable:** `output/CEFR_Companion_Volume.md`

This document captures the diagnosis, constraints, and implementation plan for the five remaining extraction failures (attempt 2). For cross-session history of both attempts, read **`metadata/EXTRACTION_DEBUG_HISTORY.md`** first.

---

## Diagnosis of Current State

### What the audit got right vs wrong

The post-implementation audit correctly observed that the **reading_order architecture is wired and active**: `pipeline/page_elements.py` builds per-page element lists, `pipeline/inventory.py` attaches them to every inventory entry, and `pipeline/extract_chunk.py` iterates `for el in reading_order` without `content_type` routing. Re-extraction on 7/3/2026 did run against this code (timestamps in `raw_extraction/` and `cleaned/`).

What the audit overstated: calling these paths "working" because they **exist and execute**. The failures below are not stale-data artifacts from an old extractor—they are **logic gaps inside the new contract** plus a merge/post-process layer that cannot reconstruct structure lost at extract time.

```
spans (span_detector) → inventory + reading_order → extract_chunk loop
  → raw_extraction → cleanup → merge_output → post_process → final_output

Failure injection points:
  span_detector  — misses 106-107 (no spanning_info)
  page_elements  — span_start break drops trailing; figure_page short-circuit
  extract_chunk  — force_ocr on rotated spans
  post_process   — cannot restore headers lost at extract time
```

### 1. Trailing prose after Table 2 (pages 24–25)

**Observed:** Footnote 20 and post-table content appear orphaned between `<!-- page:24 -->` and `<!-- page:25 -->`. Page 24 `reading_order` has only `intro → artifact(span) → footer` (no trailing element). Confirmed in `inventories/chunk_01_inventory.json`.

**Root causes (two compounding bugs):**

1. **`span_start: break` without trailing flush** — In `page_elements.py` lines 334–335, emitting the span-start table exits the merge loop. The recovery loop (lines 339–355) only runs for `interstitial`/`trailing` segments, but page 24's inventory has **zero** trailing segment because:
2. **Footnote/prose below table bbox never enters `prose_segments`** — `collect_body_lines` only keeps `kind == "body"` lines above `page_height * 0.62`. Footnotes are classified as `footnote` in `page_layout.py` and are excluded. The table bbox (`y1 ≈ 722`) also swallows the footnote band, so no `role: "trailing"` element is ever scheduled.
3. **Page 25 is entirely `span_continuation_skip`** — Only the footer extractor runs; footnote 20 leaks through footer text, not as structured post-table prose.

The `missing_trailing_prose` validator in `output_validator.py` never fires because **no trailing element exists in `reading_order`** to validate against.

Span detection for Table 2 **does work** (`table_02_summary_descriptor_changes` in `metadata/spanning_tables.json`); the merge emits `pages=24-25` correctly. The loss is **post-table zone content**, not span merge itself.

### 2. Non-rotated span merge failure (pages 106–107)

**Observed:** Two separate `db:id=scale_expressing_a_personal_response...` blocks, both `pages=106`, in `output/CEFR_Companion_Volume.md` and `raw_extraction/chunk_05.md`.

**Root cause:** `span_detector.py` only groups continuations inside runs of `_is_table_page` pages (`hlines > 10 AND vlines > 5`). Page 106 has `drawings: 24`, `expects_table: false` — it fails the gate, so `spanning_info: null` in inventory and both pages emit independent single-table artifacts with `span: null`.

This is a **detection gap**, not an extract-loop regression. The reading_order contract never receives span metadata for this pair.

### 3. Rotated tables (including pages 162–163 "Setting and perspectives")

**Observed:** Title sometimes correct (`### Setting and perspectives`) but cell bodies are OCR gibberish (e.g. `ainjsod | Apog` in `raw_extraction/chunk_07.md`).

**Root causes:**

1. **`merge_rotated_pages` always forces OCR** — `pipeline/extractors/multipage.py` line 68: `force_ocr=True` on every page in a rotated span, bypassing pdfplumber even when derotation would make it readable.
2. **OCR table reconstruction is unsuitable** — `pipeline/extractors/rotated.py` `_ocr_page_to_table` buckets words by `top // 20`; this cannot recover descriptor-scale column structure.
3. **Cell-reversal fallback is insufficient** — `_reverse_table_cells` operates on pdfplumber output from **un-derotated** pages; text layers remain scrambled.
4. **Title/slug inconsistency** — `metadata/spanning_tables.json` stores reversed slug `scale_sevitcepsrep_dna_gnittes` while inventory/registry use `scale_setting_and_perspectives`. `title_fix` runs in some paths but **not before `slugify` in span_detector**, causing group_id drift for rotated spans.

`_table_readable` gate passes too easily (CEFR level tokens like `C2` in gibberish), so the OCR path is not rejected.

### 4. Figure pages collapsing to `figure_page` (header regression contributor)

**Observed:** Page 47 has `section_headers: ["3.1. RECEPTION"]` but `reading_order` is only `figure_page + footer` (`inventories/chunk_02_inventory.json`). `page_elements.py` lines 264–268 short-circuit when `art.artifact_type == "figure"`.

**Effect:** `extract_rich_page` dumps flat prose; `### 3.1. RECEPTION` appears **before** `<!-- page:47 -->`, then duplicate page markers, then `#### 3.1.1.` from page 48 **after** the markers (`output/CEFR_Companion_Volume.md` ~1388–1400). Section hierarchy is structurally inverted relative to page boundaries.

### 5. `### 3` header formatting regression (merge/post-process + upstream)

**This is a systemic issue**, not merge reading stale data. Re-running `--step merge` alone on 7/3/2026 cleaned data reproduced the regression because the **upstream extract order is wrong**.

| Layer | What happens | Why `### 3.x` separation breaks |
|-------|--------------|----------------------------------|
| Extract | Figure page → single `rich_page` dump; mixed pages emit headings inside prose blobs without guaranteed blank-line separation before next block | Headers not emitted as isolated block starters at correct page position |
| Cleanup | Paragraph joins may glue heading to body | Minor contributor |
| Post-process | `post_process.py` `_promote_headings` / `_ensure_heading_body_spacing` add blank lines **after** headings but do **not** reorder content relative to `<!-- page:N -->`, dedupe consecutive identical page markers, or enforce "heading block before page marker for that page" | Cannot recover structure lost when figure_page swallowed the page |

Post-process can **improve spacing** but cannot fix page-47 header placement without extract emitting structured elements first.

### Can these be fixed without a full pipeline re-extract?

**Yes — targeted partial re-run is sufficient** for all five issue classes, with one caveat:

| Step | Required? | Scope |
|------|-----------|-------|
| Code changes | Yes | Modules listed below |
| `spans` + `inventory` | Yes, full | ~8 min; `reading_order` lives in inventory JSON |
| `extract` | Yes, **affected chunks only** | `chunk_01`, `chunk_02`, `chunk_05`, `chunk_07`, `chunk_08` (rotated appendix band) |
| `cleanup` | Yes, same chunks (or `cleanup_all`) | |
| `merge` + `postprocess` | Yes | Always after extract changes |
| Full re-extract all 10 chunks | **Not required** unless registry `group_id` changes invalidate unaffected chunk `db:id` anchors | Monitor after span_detector slug normalization |

**Merge/post-process alone cannot fix:** rotated bodies, 106–107 merge, Table 2 trailing prose, or figure-page header placement. Those require inventory + extract changes.

**Ensuring latest logic (no stale partial data):**

- Re-run `inventory` (calls `detect_spans()` internally) to overwrite all `inventories/chunk_*_inventory.json`.
- Re-extract only listed chunks; verify file mtimes and `metadata/last_format_run.txt` after run.
- Add `metadata/extraction_emit_log.json` logging per-page element types emitted vs `reading_order` — catches silent skips.

**Not sufficient alone:**

```powershell
python run_pipeline.py --step merge        # cannot fix extract-time losses
python run_pipeline.py --step postprocess  # spacing only; cannot fix 106-107 merge or rotated bodies
```

---

## Key Constraints

- **No cropping** — whole-page temporary derotation only (render rotated pixmap → pdfplumber, or fitz page rotation), never bbox crops.
- **Non-rotated tables stay on pdfplumber** — do not regress working descriptor scales.
- **OCR is fallback only** — after derotation + pdfplumber attempt; reject output when `_table_readable` fails with stricter thresholds.
- **Figure registry stays** — figure pages become **mixed** `reading_order` (prose zones + figure reference), not deleted.

---

## Proposed Approach

### A. Trailing prose protection (pages 24–25)

In `pipeline/page_elements.py`:

1. Replace `if span_start: break` with: emit span-start table, then **continue** to schedule `trailing` / `footnote` elements (do not emit additional tables on continuation pages).
2. Add new element type `footnote_zone` (or extend `prose` with `role: "footnote"`) sourced from `page_layout.py` footnote extraction below last table bbox.
3. On span **end** pages (`role: "end"`), emit `footnote_zone` + any `trailing` prose before `footer` (instead of only `span_continuation_skip`).

In `pipeline/extract_chunk.py`: handle `footnote_zone` via `page_layout` footnote lines formatted as numbered footnotes.

### B. Robust continuation detection (pages 106–107 + rotated spans)

In `pipeline/span_detector.py`:

1. Add **adjacent-page title matcher**: for each page with a pdfplumber table, compare `fix_rotated_title(row0)` on page N and N+1; if equal (normalized), register `continuation` even when `_is_table_page` fails on the prose-heavy start page.
2. Apply `fix_rotated_title` **before** `slugify` for `group_id` (fixes `scale_sevitcepsrep_dna_gnittes` drift).
3. Add explicit continuation: `scale_expressing_a_personal_response_to_creative_texts_including_literature` pages 106–107 (same pattern as Table 2 explicit list).
4. Reconcile explicit list `group_id` values with `pipeline/id_registry.py` artifact IDs.

In `pipeline/page_elements.py`: attach `span` metadata to first-table artifact on start page even on mixed pages (same as Table 2).

### C. Rotated table handling without OCR-first

New helper in `pipeline/extractors/rotated.py` (or new `derotate.py`):

1. **`derotate_page_for_extraction(page, rotation)`** — render page at detected angle (90/270) to upright pixmap; run pdfplumber `find_tables` / `extract_tables` on derotated view (via in-memory page or temporary single-page PDF).
2. **Single-page path:** `extract_rotated_tables` tries derotated pdfplumber first; OCR only if readability gate fails.
3. **Span path:** `merge_rotated_pages` merges derotated pdfplumber tables across pages (reuse `multipage.py` `_merge_rows`); remove unconditional `force_ocr=True`.
4. Tighten `_table_readable`: require minimum word count + CEFR level column pattern OR `english_word_score > 0.25`; flag `rotated_table_unreadable` when failing.

Title: always `fix_rotated_title` on row0 before display and registry lookup.

### D. Figure pages → mixed reading_order (pages 46–48)

In `pipeline/page_elements.py`:

1. Remove blanket `figure_page` return when figure art exists on a page with `section_headers` or body text above/below figure bbox.
2. Build mixed order: `prose(intro with section_headers)` → `figure` element (reference existing figure asset, no crop) → `prose(trailing)` → `footer`.
3. In `pipeline/extract_chunk.py`: `figure` element emits figure placeholder / mermaid / registry reference (reuse `apply_figures` contract), not full-page `rich_page` dump.

### E. Header formatting restoration (post-process + extract alignment)

In `pipeline/descriptor_layout.py` / extract:

- When `section_headers` present on intro prose element, prepend `format_numbered_heading` output as first lines of `extract_prose_zone` result (level 3 → `###`, level 4 → `####`).

In `pipeline/post_process.py`:

1. **`_normalize_section_boundaries`**: when `### N.N.` heading immediately precedes `<!-- page:N -->` but sub-heading `#### N.N.N.` follows the marker, move/re-emit so parent `###` sits after page marker with blank line before body (page 47 pattern).
2. **Dedupe consecutive identical `<!-- page:N -->` markers** (extend beyond `_dedupe_consecutive_lines` exact-line match).
3. **`_ensure_heading_body_spacing`**: treat `<!-- page:N -->` blocks as block starters that break paragraph merge with preceding headings.

### F. Validation hardening

In `pipeline/output_validator.py`:

- `missing_trailing_prose`: also check span-start pages where inventory `text_length` implies footnotes below table but no `trailing`/`footnote` element in `reading_order`.
- `rotated_table_unreadable`: run against derotated extract output with stricter gate.
- Add `reading_order_completeness`: every `section_headers` entry must have corresponding heading in chunk output.
- Emit `metadata/extraction_emit_log.json` per extract run.

---

## Files / Modules to Modify

| Module | Changes |
|--------|---------|
| `pipeline/page_elements.py` | Remove span_start break; footnote/trailing elements; mixed figure pages |
| `pipeline/span_detector.py` | Adjacent title matching; title_fix before slugify; explicit 106–107 |
| `pipeline/extractors/rotated.py` | Whole-page derotation; pdfplumber-first; stricter readability |
| `pipeline/extractors/multipage.py` | `merge_rotated_pages` uses derotated pdfplumber merge, not force_ocr |
| `pipeline/extract_chunk.py` | `footnote_zone`, `figure` element handlers; optional `--chunk` CLI flag |
| `pipeline/descriptor_layout.py` | Section header emission in prose zones |
| `pipeline/post_process.py` | Section boundary normalizer; page-marker dedupe; heading/page ordering |
| `pipeline/output_validator.py` | Fix validators to catch real failures; emit log |
| `pipeline/id_registry.py` | Align explicit continuation artifacts with normalized group_ids |

---

## Validation Steps

### Minimal test pages

| Pages | Issue | Pass criteria |
|-------|-------|---------------|
| **24–25** | Trailing prose / footnotes | Footnotes 19–20 appear after merged Table 2 body, not orphaned between page markers; `reading_order` on page 24 includes footnote/trailing element |
| **106–107** | Non-rotated span merge | Single `db:id=scale_expressing_a_personal_response...` with `pages=106-107`; B1/A2 rows from page 107 in same table as C1/C2 from page 106 |
| **162–163** | Rotated "Setting and perspectives" | Title readable; cells contain English descriptor phrases and CEFR levels, not OCR fragments |
| **183+** (one appendix table) | Rotated non-spanning | Same readability gate passes |
| **46–48** | Header hierarchy | `### 3.1. RECEPTION` after `<!-- page:47 -->` with blank line before body; `#### 3.1.1.` before `<!-- page:48 -->`; no duplicate `<!-- page:47 -->` |

### Automated checks

```powershell
python -m pipeline.output_validator
python run_pipeline.py --step validate
```

Expect `metadata/output_validation.json` → `valid: true` (or zero hits on the five issue types above).

### Manual diff commands

```powershell
rg "page:24|page:25|footnote|Table 2" output/CEFR_Companion_Volume.md
rg "scale_expressing_a_personal_response" output/CEFR_Companion_Volume.md
rg "Setting and perspectives" output/CEFR_Companion_Volume.md
rg "### 3\.1\. RECEPTION|#### 3\.1\.1\." output/CEFR_Companion_Volume.md
```

---

## Recommended Next Commands

**After code changes are implemented:**

```powershell
# 1. Regenerate spans + inventories (reading_order)
python run_pipeline.py --step spans
python run_pipeline.py --step inventory

# 2. Re-extract affected chunks only
python -m pipeline.extract_chunk chunk_01
python -m pipeline.extract_chunk chunk_02
python -m pipeline.extract_chunk chunk_05
python -m pipeline.extract_chunk chunk_07
python -m pipeline.extract_chunk chunk_08

# 3. Cleanup those chunks
python -m pipeline.cleanup chunk_01
python -m pipeline.cleanup chunk_02
python -m pipeline.cleanup chunk_05
python -m pipeline.cleanup chunk_07
python -m pipeline.cleanup chunk_08

# 4. Validate + merge + post-process
python run_pipeline.py --step validate
python run_pipeline.py --step merge
python run_pipeline.py --step postprocess
python -m pipeline.output_validator
```

If `extract_chunk` CLI only supports `extract_all`, add a `--chunk` flag to `pipeline/extract_chunk.py` or temporarily filter in a one-line orchestrator—worth doing to avoid re-extracting chunks 03, 04, 06, 09, 10.

---

## Implementation Checklist

- [x] Fix span_start break + add footnote/trailing elements in `page_elements.py`; wire `extract_chunk` handler
- [x] Adjacent-page title matching in `span_detector.py`; `fix_rotated_title` before slugify; explicit 106–107 entry
- [x] Whole-page derotation in `rotated.py`/`multipage.py`; pdfplumber-first + `_reverse_table_cells`; remove `force_ocr` default; tighten readability gate
- [x] Replace `figure_page` short-circuit with mixed prose+figure `reading_order` on pages like 47
- [x] Section boundary normalizer + page-marker dedupe + heading emission in prose zones
- [x] Fix `missing_trailing_prose` and `rotated_table_unreadable`; add `reading_order_completeness` + `extraction_emit_log.json`
- [x] Add `--chunk` flag to extract; run inventory + extract chunks 01,02,05,07,08 + merge + postprocess

### Post-implementation notes (2026-07-04)

- **24–25:** Footnotes 19–20 now appear in span body before page markers (correct order).
- **106–107:** Single merged artifact with `pages=106-107`.
- **162–163:** Rotated tables use derotated pdfplumber + cell reversal; readable English (minor `fo`/`ro` char artifacts remain in short tokens).
- **47:** Mixed `prose → figure → footer` with `### 3.1. RECEPTION`; page-boundary ordering improved but Ch.3 opener still interleaves with figure block between page 46–47 markers (further tuning possible).
- **Validation:** `metadata/output_validation.json` still reports issues (273); many are pre-existing `page_under_extracted` on pure-text pages, not the five target failures.