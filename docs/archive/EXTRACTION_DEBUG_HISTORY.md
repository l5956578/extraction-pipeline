# Extraction Debug History — Persistent Session Notes

**Purpose:** Living record of what was tried, what was claimed, what actually happened, and what remains broken.  
**Survives:** Git commits, compaction, new Cursor/Grok sessions.  
**Read this first** before any new extraction fix attempt.

**Last updated:** 2026-07-13 (production run: agent-only vision path + cleanup fixes + full extract)
**Active branch:** `execute-plan/c0b4a280-pr-5-pipeline-re-run-and-documentation`
**Master merge:** **NOT done** — user did not merge; `master` still has attempt-2 commits.

---

## 2026-07-13 — Rotated tables: agent vision handoff (ported)

**Decision:** Geometry + OCR + chat-draft Grok markdown are not reliable for rotated descriptor scales. **Coding agent multimodal vision** (re-read PNGs in-session, write `.md` by hand) is the authoritative extractor for rotated tables only.

**Main pipeline paths:**
- `pipeline/extractors/rotated_grok_vision.py` — prepare PNG, assemble, pending placeholders
- `work/metadata/rotated_for_grok/` — PNG + JSON + handoff + `manifest.json`
- `work/metadata/rotated_from_grok/` — agent-corrected tables (`page_{NNN}_{span_group_id}.md`)
- `prepare_rotated_for_grok.py` / `finalize_after_grok.py`
- `work/metadata/ROTATED_TABLES_AGENT_VISION.md` — session instructions
- Default inventory method: `rotated_extraction_method: grok_vision` (`page_elements.py`)
- Footnote 46 etc.: still geometry `rotated_footnote_zone` (not vision)

**Proven on:** `scale_sign_language_repertoire` pp.146–148 (smoke test → seeded `.md` in main).

**Still open:** agent vision `.md` for remaining rotated spans (this run: 3 ready / ~85 pages; missing use geometry fallback + `AGENT_VISION_PENDING` comment).

### 2026-07-13 production run fixes
- **Chat/web Grok dropped** as pipeline step; coding agent vision only.
- **Duplicate page markers:** root cause was `rich_page` emitting footer + inventory `footer` element → fixed (`extract_rich_page` body-only); cleanup/post_process also dedupe.
- **Bold:** detect Bold/Semibold font names, not only PDF bold flag.
- **Paragraphs:** soft-wrap join in `page_layout._join_body_paragraphs`.
- **OCR thrash:** geometry fallback no longer OCR-forces every rotated page (Appendix 5 was multi-hour).
- **Inventory contract:** sound — `reading_order` drives extractors; defaults fill missing `rotated_extraction_method`. Re-inventory optional for field persistence.

**Review file:** `output/CEFR_Companion_Volume.md` (~943 KB after postprocess).

---

## Where documentation lives

| File | Role |
|------|------|
| **`work/metadata/EXTRACTION_DEBUG_HISTORY.md`** (this file) | **Canonical** bug registry, cross-attempt history, honest outcomes |
| `work/metadata/ROTATED_TABLES_AGENT_VISION.md` | **Agent vision workflow** for rotated tables |
| `work/metadata/rotated_for_grok/` | PNG handoffs + manifest |
| `work/metadata/rotated_from_grok/` | Corrected markdown per table page |
| `work/metadata/attempt3_design.md` | Attempt 3 PR plan (execute-plan) |
| `remaining-fixes.md` | Attempt 2 plan + checklist (mostly superseded; see this file for truth) |
| `work/metadata/extraction_plan.md` | Operational spec (`reading_order` contract) |
| `work/metadata/output_validation.json` | Latest validator output |
| `work/metadata/spanning_tables.json` | Span groups (32 after attempt 3 chain merge) |
| `output/CEFR_Companion_Volume.md` | Deliverable under test |
| `../attempt4_rotation_smoke_test/` | **Isolated** attempt 4 harness (pages 143–149 only) |
| `../attempt4_rotation_smoke_test/work/metadata/smoke_test_results.md` | Attempt 4 run summary |
| `../attempt4_rotation_smoke_test/work/metadata/rotated_table_flags.json` | Inventory-derived rotated-page flags |

**Git commits (attempt 3 stack on execute-plan branch):**

```
9526996  PR5 partial pipeline re-run and attempt 3 documentation
1bdd8a1  Validator contract gates
5242160  Page 47 figure zone split
d3f43ad  Span-end trailing prose and footnote ownership
07b4c07  Span chain merge and debug_page tooling
```

---

## Open bug registry (brutal — do not mark resolved without user-visible proof)

Status key: **OPEN** | **PARTIAL** | **RESOLVED**

### A. Table 2 / pages 24–25 (span `table_02_summary_descriptor_changes`)

| ID | Bug | Status | Attempt 3 |
|----|-----|--------|-----------|
| A1 | Trailing prose below Table 2 on page 25 ("In addition to Chapter 2…") missing from output | **RESOLVED** | Inventory schedules `prose:trailing` on page 25; prose appears in `output` ~665 before `<!-- page:25 -->`. User confirmed good. |
| A2 | Footnote **19** duplicated | **RESOLVED** | Single `19.` line in pages 24–25 region (~660). `_extract_span_body` no longer re-collects footnotes. |
| A3 | Footnote **20** duplicated and misplaced | **OPEN** | **Not fixed.** Fn20 embedded inline in trailing prose (~667: `…schools",20 which helped…` plus full fn20 line same paragraph). Orphan `Introduction` + wrong-case marker `<!-- Page 25 -->` (~669–670) from PDF footer bleed. Fn20 repeated again (~672) before canonical `<!-- page:25 -->` (~674). Validator `footnote_single_owner` only checks fn19 — **gate is insufficient**; attempt 3 falsely treated fn20 as non-issue. |
| A4 | Span-end page contract: footnote_zone vs prose both ingest footer band text | **OPEN** | Related to A3. Trailing prose extractor and footnote_zone both pull from page 25 footer band without exclusive ownership. |

### B. Page 47 / Figure 11 / section order (original header regression)

| ID | Bug | Status | Attempt 3 |
|----|-----|--------|-----------|
| B1 | Wrong vertical order (3.1 RECEPTION before Chapter 3 / figure) | **PARTIAL → user accepts** | Order now: `## Chapter 3` → `db:id=figure_11…` → text diagram → `### 3.1. RECEPTION` → body (~1372–1401). User confirmed order correct. |
| B2 | Missing figure caption header between `db:id` and diagram | **OPEN** | **Not fixed.** Expected: `### Figure 11 – Reception activities and strategies \| figure_11_reception_activities_strategies` between db comment and ` ```text ` block (~1375). Only db:id + diagram emitted; **no "Figure 11" string anywhere in final_output**. Validator `page_47_section_order` does not check for this header — false PASS. |
| B3 | Duplicate `<!-- page:N -->` markers (document-wide) | **OPEN** | **Not fixed.** 69 pages have duplicate lowercase markers in `output`. User spot-check: duplicates through ~page 45, singles for 46–47 band. Agent verify: pages 46–89 mostly single; dups resume at 90+ (e.g. 145, 149). Not caused by master merge (merge never done). Likely **merge/postprocess** concatenating chunk boundaries or stale+cleaned chunk overlap — downstream of extract, not inventory. |
| B4 | Stray `<!-- Page N -->` (capital P) inside body | **OPEN** | PDF footer artifacts in prose (~670 page 25, also 5, 7, 9, 33, 61, 71, 127, 133). Not normalized away. |

### C. Spanning tables / rotated extraction (pages 146–148 focus)

| ID | Bug | Status | Attempt 3 |
|----|-----|--------|-----------|
| C1 | `span_duplicate_emit` on page 147 (pairwise spans 146–47 + 147–48) | **RESOLVED** (inventory/validator) | Chain merge → single `scale_sign_language_repertoire` 146–148 in `spanning_tables.json`; page 147 `role: middle`. No `span_duplicate_emit` in validator. **Extraction quality still broken (see C2–C5).** |
| C2 | Rotated span body gibberish | **PARTIAL** (test folder only) | **Main `agent-extraction/` still broken.** Attempt 4a (derotation + pdfplumber): FAIL — `eriotreper\negaugnal\nngiS`. Attempt 4b (PyMuPDF matrix-aware, test folder only): **readable English** in `attempt4_rotation_smoke_test/output/` — no `eriotreper`; CEFR row shows C2/C1/B2; descriptors readable. **Not ported to main.** Remaining: repeated `"Sign language repertoire"` in column 1 per pdfplumber row (no rowspan logic); PDF typos pass through (`scientifci`, `difefrent`). |
| C3 | Span merge emits all continuation pages on start page only; 147–148 markers empty | **OPEN** | `<!-- page:146 -->` has footer; **147 and 148 markers have only footers, no table body** (~4253–4257). Prose after table starts on 148 (~4259) but table rows not distributed per page contract. User confirmed. |
| C4 | Duplicate `scale_sign_language_repertoire` artifact later in document | **OPEN** | Second block at ~10035: `pages=148` only, different `product_tier`. Suggests **id_registry / merge** still emitting a second artifact for same scale — havoc beyond span_detector. |
| C5 | Page 149 duplicate page markers | **OPEN** | Two identical `<!-- page:149 -->` + footers (~4290–4294) before next scale. User spot-check confirmed. |

### D. Pipeline contract / process integrity (user-reported)

| ID | Bug | Status | Notes |
|----|-----|--------|-------|
| D1 | Inventory contract honored at extract time, then violated by later steps | **OPEN** | User observation: extract appears correct (db:id, headers, span metadata), then merge/cleanup/postprocess/merge chunks introduce dup markers, missing headers, duplicate artifacts, empty span pages. Attempt 3 partial re-extract (chunks 01, 02, 06 only) compounds stale+fresh chunk splice. |
| D2 | Bespoke validators pass while user-visible bugs remain | **OPEN** | Gates check narrow strings (fn19 only, figure id substring, header order) — **do not catch** fn20 dup, missing Figure 11 `###` caption, rotated gibberish, empty 147–148, dup page markers. Attempt 3 **over-claimed PASS** on several rows. |
| D3 | `valid: false` (108 issues) with unre-extracted chunks | **OPEN** | Expected noise from chunks 03–05, 07–10 not re-run; do not treat as attempt-3 success metric. |

---

## Attempt 3 — internal claims vs user verification (2026-07-04)

### What actually worked (keep credit)

- Span chain merge: 85 → 32 groups; `scale_sign_language_repertoire` is **146–148** (one chain).
- Page 25 trailing prose scheduling and emission (A1).
- Footnote 19 single emit (A2).
- Page 47 **zone order** Chapter 3 → figure diagram → 3.1 RECEPTION → body (B1).
- `span_duplicate_emit` cleared for page 147 at inventory/validator level (C1 only).
- `pipeline/debug_page.py` added for PDF vs inventory comparison.
- `extract_chunk` CLI fixed to extract one chunk (was running all chunks).

### What attempt 3 claimed but user verification **rejects or downgrades**

| Claimed PASS | Reality |
|--------------|---------|
| Page 25 fully fixed | **PARTIAL** — prose yes; fn20/footer bleed **OPEN** (A3, A4) |
| `footnote_single_owner` | **Misleading** — fn19 only; fn20 dup **OPEN** |
| Page 47 fixed | **PARTIAL** — order yes; **missing Figure 11 `###` header** (B2) |
| Page 147 / span_duplicate_emit | **PARTIAL** — validator clean; **rotated extraction still garbage; 147–148 empty** (C2, C3) |
| Contract targets met | **Overstated** — bespoke gates green; **user-visible output still wrong** on multiple targets |

### Code modules touched (attempt 3)

`span_detector.py`, `inventory.py`, `page_elements.py`, `extract_chunk.py`, `descriptor_layout.py`, `output_validator.py`, `apply_figures.py`, `debug_page.py` (new).

### Pipeline run (partial)

Re-extracted: `chunk_01`, `chunk_02`, `chunk_06` only. Chunks 03–05, 07–10 stale in merge.

---

## Prior attempts (summary)

### Attempt 1 (`e3d7fbe`) — reading_order architecture

Wired `reading_order` loop; broke trailing prose (`span_start: break`), missed 106–107 spans, figure_page swallowed headers, rotated OCR gibberish.

### Attempt 2 (`078f0b8`) — remaining-fixes plan

Partial improvements; introduced `span_duplicate_emit` mass false positives (85 spans); page 25 trailing still dropped; page 47 still wrong; fn19 dup.

---

## Attempt 4 — rotation smoke test (`attempt4_rotation_smoke_test/`)

**Scope:** Isolated copy of pipeline; pages **143–149** only; main `agent-extraction/` **never written** (read-only PDF). Inventory / span detection / cleanup / merge **unchanged**; only rotated-table **extraction** patched in test folder.

**Harness:** `../attempt4_rotation_smoke_test/run_smoke_test.py`

---

### Attempt 4a — page derotation + pdfplumber (2026-07-05) — **FAIL**

**Approach:** After inventory, `permanent_derotate.py` called `Page.remove_rotation()` on flagged pages; `rotated.py` / `multipage.py` used pdfplumber on `work/metadata/work_derotated.pdf`.

**Outcome:** Table body still gibberish (`eriotreper\negaugnal\nngiS`). **Dead approach** for this PDF band.

---

### Attempt 4b — PyMuPDF matrix-aware cell assembly (2026-07-05) — **PARTIAL PASS** (test folder only)

**Approach:** For `extractor == "rotated_table"` / `text_direction == "ocr"`: PyMuPDF glyphs + pdfplumber **cell bboxes only**; no derotation, no `extract_tables()` text.

**Files changed (test folder only):**

| File | Change |
|------|--------|
| `pipeline/extractors/rotated.py` | `_collect_pymupdf_chars`, `_assemble_cell_text`, `_table_rows_from_structure`; `extract_rotated_tables` uses these |
| `pipeline/extractors/multipage.py` | `merge_rotated_pages` merges via `_table_rows_from_structure` + `_merge_rows` |
| `run_smoke_test.py` | Removed derotation step (steps 4–6 = extract / cleanup / merge) |
| `pipeline/permanent_derotate.py` | **Orphaned** — no longer called; kept on disk from 4a |

**Routing (unchanged):** `extract_chunk.py` → span body → `merge_rotated_pages`; single page → `extract_rotated_element` → `extract_rotated_tables`.

**Outcome in `attempt4_rotation_smoke_test/output/CEFR_Companion_Volume.md`:**

| Check | Result |
|-------|--------|
| Readable English descriptors | **Yes** — e.g. "Can express themselves in abstract, poetic signing…" |
| No reversed gibberish | **Yes** — no `eriotreper` |
| CEFR levels in table | **Yes** — C2, C1, B2 visible in level row |
| Single clean table structure | **PARTIAL** — one merged pipe table; column 1 repeats `"Sign language repertoire"` on continuation rows (pdfplumber row grid, no rowspan) |
| Page 147–148 markers carry table body | **Still OPEN** (C3) — span emits full table on start page |
| Duplicate page markers in slice | **Still OPEN** (B3/C5 in slice) — dup `<!-- page:145 -->`, `<!-- page:149 -->` |

**Do not port to main** until user verifies and remaining C2 structure issues (rowspan / col1 dedup) are addressed.

---

### Current rotated-table reconstruction logic (attempt 4b — for next agent)

**Canonical technical analysis (2026-07-05):**  
`../attempt4_rotation_smoke_test/work/metadata/ROTATED_TABLE_RECONSTRUCTION.md`

Covers: column-order transpose (`Level | Productive | Receptive`), why `_collapse_rowspan_labels` does not create B2/B1 continuation rows, C2 receptive ordering failures, footnote 46 suppression, pages 147–148 fragment mixing, header detection (pdfplumber bbox only vs PyMuPDF geometry), and symptom→root-cause table. **Use that file for plan mode.**

**Superseded summary (pre-logical-grid rewrite):** old path used pdfplumber cell bboxes + per-cell char assembly; current test-folder code uses `_build_logical_descriptor_table`, `_extract_levels_across`, and `_assemble_band_lines` — see doc above.

---

### Inventory (detection only — both 4a and 4b)

Pages **146, 147, 148** flagged `rotated_90`, span `scale_sign_language_repertoire` 146–148. `work/metadata/rotated_table_flags.json` written post-inventory by orchestrator (not `inventory.py`).

### Content-stream forensics (pages 146–147) — evidence before conclusions

**Did `work_derotated.pdf` change content streams?** **No.** Contents xrefs 330 (p146) and 332 (p147) are **byte-identical** to original (SHA256 match). `page.rotation == 0` before and after. `remove_rotation()` was a **no-op** — no `/Rotate` page flag to clear.

**`cm` operators:** All horizontal (`1 0 0 1 tx ty cm`) — used for **table grid line drawing** (`m`/`l`/`S`), not text. Page 146: 43 `cm`, 43 `q`/`Q`. Page 147: 30 `cm`, 30 `q`/`Q`. **Zero** `q`/`Q` blocks contain rotation `cm`.

**`Tm` operators (where rotation actually lives):** Page 146: 13 `Tm` (1 horizontal footer + **12 rotate_90** `0 ±9..10 ∓9..10 0 e f Tm`). Page 147: 6 `Tm` (2 horizontal + **4 rotate_90**). Rotation is **not** in CTM/`cm`; it is in the **text matrix**.

**Group vs per-character in PDF stream:** **~12 column-anchor `Tm` ops per page** + `TJ`/`Tj` strings + `Td` line advances within each rotated frame — **not** thousands of `Tm` in the stream. Example (page 146 xref 330):

```
0 10 -10 0 88.5825 388.9597 Tm
[(Sign language r)8.1 (ep)-3 (er)-21 (t)5 (oir)8 (e)]TJ
-12.991 -2.41 Td
[(Rec)11 (eptiv)15 (e)]TJ
...
0 9 -9 0 131.2768 125.7114 Tm
[(Can understand abstr)...]TJ
0 -1.111 Td
```

pdfplumber reports **one computed matrix per glyph** (2964 unique matrices / 2964 table chars on p146) — parser artifact, not per-glyph `Tm` in source PDF.

**pdfplumber chars in table bbox (p146):** 100% `rotate_90` matrices; `upright=False`. Cell `[0][0]` ("Sign language repertoire"), 24 chars:

| Sort key | Cell text |
|----------|-----------|
| `(top, x0)` — pdfplumber default | `eriotreper egaugnal ngiS` |
| `matrix[5]` ascending — along rotated line | `Sign language repertoire` |
| `extract_tables()` | `eriotreper\negaugnal\nngiS` |

**PyMuPDF `get_text()`:** `Sign language repertoire` with `dir=(0.0, -1.0)` — correct because it walks lines along glyph direction, not page-horizontal sort.

### Root cause (evidence-based)

1. Table rotation is **`Tm` text-matrix rotation** embedded in content stream, **not** page `/Rotate`.
2. `remove_rotation()` only handles page-level `/Rotate` → **cannot fix** this table band.
3. pdfplumber `extract_tables()` assigns chars to cells correctly by bbox, but **assembles cell text sorted by page `(top, x0)`**, which walks **backward** along 90°-rotated lines → reversed strings and wrong line breaks.
4. Prior `_reverse_table_cells` hack in main pipeline was a symptom fix on already-wrong char order; attempt 4 removing it + derotation still fails.

### Inspection scripts (test folder)

`inspect_content_stream.py`, `inspect_tm_groups.py`, `inspect_cell_order.py` — content-stream / pdfplumber char forensics (4a diagnosis).

### Run (attempt 4b)

```powershell
cd attempt4_rotation_smoke_test
python run_smoke_test.py
# or faster re-extract only (inventory already built):
python -c "from pipeline.extract_chunk import extract_chunk; from pipeline.cleanup import cleanup_file; from pipeline.merge_output import merge_markdown; from pipeline.config import RAW_DIR, CLEANED_DIR; extract_chunk('chunk_test_143_149'); cleanup_file(RAW_DIR/'chunk_test_143_149.md', CLEANED_DIR/'chunk_test_143_149.md'); merge_markdown()"
```

---

## Commands reference

```powershell
python -m pipeline.debug_page 25,47,146,147,148
python -m pipeline.output_validator
rg "page:25|page:47|page:146|sign_language_repertoire|Figure 11" output/CEFR_Companion_Volume.md
```

---

### Attempt 4c — rotated table reconstruction fixes (2026-07-05) — **PARTIAL PASS** (test folder only)

**Scope:** Implemented approved plan in `attempt4_rotation_smoke_test/audit-pack/02_ROTATED_TABLE_FIX_PLAN.md` (all 7 tasks). Main `agent-extraction/` pipeline code **not modified** (this history append only).

**Files changed (test folder):**

| File | Change |
|------|--------|
| `pipeline/extractors/rotated.py` | Widen along bands; perp-row `_assemble_band_lines` with `\n` between descriptors; `DescriptorGrid` (level × subRow × side); empty-band sub-row splits; inherited band hints preferred on 147–148; `_merge_descriptor_grids` by sub-row index |
| `pipeline/extract_chunk.py` | Surgical rotated footnotes on span-start footer via `extract_surgical_rotated_footnotes`; removed blanket `skip_footnotes` auto-detect |
| `pipeline/page_layout.py` | `extract_surgical_rotated_footnotes()` — margin-zone numbered footnotes, debris guards |
| `pipeline/page_elements.py` | Schedule `rotated_footnote_zone` element on span-start (for future inventory regen) |
| `pipeline/utils.py` | `escape_md_cell` preserves descriptor newlines as `<br>` |

**Verification** (`chunk_test_143_149` → `output/CEFR_Companion_Volume.md`):

| Audit check | Result |
|-------------|--------|
| C2 Productive: 4 `Can …` statements incl. formulate abstract / produce with one hand | **PASS** — all four present, `<br>`-separated |
| Distinct descriptors newline-separated (not run-on) | **PASS** — `<br>` in table cells |
| B2 multi-row + rowspan | **PASS** — two rows; blank level on continuation (lines ~113–114) |
| B1 multi-row + rowspan (page 147) | **PASS** — two rows (lines ~115–116) |
| Footnote 46 without table debris | **PASS** — `46. This is also known as "body partitioning".` only |
| No `B2 C1 C2` junk line | **PASS** |
| C2 Receptive sentence order | **PARTIAL** — improved; some wrap-fragment mis-attachment remains |
| C1/B1 orphan fragments mid-cell | **PARTIAL** — perp-row assembly reduced but not eliminated |
| Pages 147–148 continuation merge | **PARTIAL** — sub-row merge by index works; some cross-page fragment mixing remains |

**Do not port to main** until user verifies. Remaining quality issues are fragment-attachment geometry (not band drops or rowspan structure).

---

## Changelog

| Date | Update |
|------|--------|
| 2026-07-05 | **Attempt 4c PARTIAL (test folder):** All 7 plan tasks in `attempt4_rotation_smoke_test/`; C2 completeness, `<br>` descriptors, B2/B1 rowspan, footnote 46 restored; fragment ordering still partial |
| 2026-07-04 | Attempt 3 execute-plan stack; internal PASS claims |
| 2026-07-04 | **User verification pass:** reopened A3, A4, B2–B4, C2–C5, D1–D2; downgraded attempt 3; added open bug registry; noted no master merge |
| 2026-07-05 | **Attempt 4a FAIL:** derotation + pdfplumber; streams byte-identical; rotation in `Tm` not `/Rotate`; pdfplumber `(top,x0)` reverses cells |
| 2026-07-05 | **Attempt 4b PARTIAL (test folder):** PyMuPDF matrix-aware cell assembly in `rotated.py`/`multipage.py`; readable `scale_sign_language_repertoire` text; C2 → PARTIAL test-only; not ported to main; documented reconstruction logic |
| 2026-07-05 | **Approved fix plan (test folder):** `../attempt4_rotation_smoke_test/work/metadata/ROTATED_TABLE_FIX_PLAN.md` — band bounds, descriptor newlines, grid-rule sub-bands, surgical footnotes, continuation-page assembly; builds on `ROTATED_TABLE_RECONSTRUCTION.md` |
| 2026-07-05 | **External audit pack:** `../attempt4_rotation_smoke_test/audit-pack/` — copies of plan, reconstruction, history, code snapshots, output slice, checklist; index `00_AUDIT_README.md` |

**Maintainers:** Append after every fix attempt. Do not mark RESOLVED without user-visible proof in `output`.