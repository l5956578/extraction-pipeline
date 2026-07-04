# Extraction Debug History — Persistent Session Notes

**Purpose:** Living record of what was tried, what was claimed, what actually happened, and what remains broken.  
**Survives:** Git commits, compaction, new Cursor/Grok sessions.  
**Read this first** before any new extraction fix attempt.

**Last updated:** 2026-07-04  
**Current deliverable commit:** `078f0b8` (worktree + Documents copy)  
**Prior major commit:** `e3d7fbe` (reading_order overhaul)

---

## Where documentation lives

| File | Role |
|------|------|
| **`metadata/EXTRACTION_DEBUG_HISTORY.md`** (this file) | **Canonical** cross-attempt history, honest outcomes, next steps |
| `remaining-fixes.md` | Plan + checklist for attempt 2 (approved 2026-07-03, implemented 2026-07-04) |
| `metadata/extraction_plan.md` | Living operational spec (reading_order contract) |
| `metadata/extraction_emit_log.json` | Per-chunk emit log (added attempt 2) |
| `metadata/output_validation.json` | Latest validator output (`valid: false`, 273 issues @ 078f0b8) |
| `metadata/spanning_tables.json` | 85 span groups after attempt 2 |
| `audit-pack/AUDIT_INDEX.md` | External audit pack index (partially stale — see below) |
| `audit-pack/02_extraction_plan.md` | Snapshot of plan at audit time |
| `audit-pack/03_output_validation.json` | **Stale** — from pre-attempt-2 era |

**Git commits (master):**

```
078f0b8  Fix remaining extraction failures per remaining-fixes plan
e3d7fbe  Implement reading_order extraction contract and rebuild pipeline outputs
a1d72ce  Initial commit
```

**Repos (should match after sync):**

- Worktree: `C:\Users\59565\.grok\worktrees\python-scripts-extraction-pipeline\agent-extraction`
- Documents: `C:\Users\59565\Documents\Python Scripts\extraction-pipeline`
- Remote: `https://github.com/l5956578/extraction-pipeline` (ahead 1 commit as of 2026-07-04)

---

## The five target failure classes (user-confirmed)

These are the problems that motivated both fix attempts:

1. **Trailing prose after Table 2** (pages 24–25, non-rotated span continuation)
2. **Rotated tables** — gibberish titles/cells (e.g. pages 162–163 “Setting and perspectives”; appendix band 183+)
3. **Non-rotated span merge** — pages 106–107 same table name, emitted as two artifacts
4. **Figure pages collapsing** — page 47 figure swallowed section prose/headers
5. **`### 3` header formatting regression** — Ch.3 section headers mis-ordered vs page markers

**Constraints (non-negotiable):** No cropping. OCR not acceptable as primary path for rotated descriptor tables. Non-rotated pdfplumber tables must stay clean.

---

## Attempt 1: reading_order contract overhaul (`e3d7fbe`)

**When:** 2026-07-03 (plan mode → agent implement → full re-extract + merge)  
**Goal:** Replace `content_type` routing with per-page `reading_order` arrays as the extraction contract.

### What was built

| Module | Change |
|--------|--------|
| `pipeline/page_elements.py` | **New** — `build_reading_order()`, prose/table zones, span-start single emit |
| `pipeline/title_fix.py` | **New** — `fix_rotated_title()`, reversed-word detection |
| `pipeline/inventory.py` | Wires `reading_order` on every page |
| `pipeline/extract_chunk.py` | Strict `for el in reading_order` loop |
| `pipeline/descriptor_layout.py` | `extract_prose_zone(bbox)` |
| `pipeline/span_detector.py` | Existing + explicit Table 2 / vocabulary entries |
| `pipeline/output_validator.py` | Element-level rules (reversed_title, span_duplicate_emit, etc.) |

### Post-implementation audit claims vs reality

The audit marked these as **shipped and working** because the code paths exist and re-extraction ran (timestamps 7/3/2026 ~5:28–7:00 PM in `raw_extraction/` and `cleaned/`):

- `reading_order` on every inventory page ✓ (wired)
- `title_fix` in span_detector / id_registry ✓ (wired)
- Strict extract loop ✓ (wired)
- Per-table `table_index` ✓ (wired)
- Span-start single table emit ✓ (wired for *tables*, but broke trailing prose)

**User-confirmed still broken after attempt 1 + re-extract + merge:**

| Issue | Why architecture didn't fix it |
|-------|------------------------------|
| Table 2 trailing prose | `span_start: break` in `page_elements.py` exited loop before trailing/footnote elements; footnotes excluded from `prose_segments` |
| 106–107 not merged | `span_detector` required consecutive `_is_table_page` pages (hlines>10, vlines>5); page 106 failed gate → `spanning_info: null` |
| Rotated tables | `merge_rotated_pages` forced OCR; cell-reversal on un-derotated pdfplumber; weak readability gate |
| Figure page 47 | `art.artifact_type == "figure"` → blanket `figure_page` + `rich_page` dump |
| Header `### 3.x` | Structure lost at extract time; post-process spacing cannot reorder vs page markers |

**Audit correctly marked Partial/No:**

- Rotated OCR path — still gibberish on 162–163, appendix
- `missing_trailing_prose` / `rotated_table_unreadable` validators — rules existed but didn't fire (no trailing elements in inventory; weak gates)
- `reading_order_completeness` / `extraction_emit_log.json` — not implemented

**Critical lesson:** Running `python run_pipeline.py --step merge` alone **cannot** fix extract-time losses. The audit's implication that merge on fresh `cleaned/` would deliver fixes was **only true for code already correctly emitting in raw_extraction** — which these paths were not.

---

## Attempt 2: remaining-fixes plan (`078f0b8`)

**When:** 2026-07-03 plan → 2026-07-04 implement  
**Plan doc:** `remaining-fixes.md`  
**Pipeline run:** Full `spans` + `inventory` (~10–12 min); partial re-extract `chunk_01,02,05,07,08` (~40+ min); `cleanup_all` → `merge` → `postprocess`

### Code changes (attempt 2)

| Module | Change |
|--------|--------|
| `page_elements.py` | Remove `span_start: break` (skip remaining tables instead); `footnote_zone`; mixed figure `prose→figure→footer`; span end pages skip footer footnotes |
| `span_detector.py` | Adjacent-page title matcher; `fix_rotated_title` before `slugify`; explicit 106–107 and 162–163 |
| `extractors/rotated.py` | `derotated_pdfplumber_tables()` via temp upright PDF; pdfplumber-first; `_reverse_table_cells` on derotated output; stricter `_table_readable` |
| `extractors/multipage.py` | `merge_rotated_pages` uses derotated pdfplumber merge, not `force_ocr=True` |
| `extract_chunk.py` | `footnote_zone`, `figure` element, span footnotes in body, `--chunk` CLI, `extraction_emit_log.json` |
| `descriptor_layout.py` | `section_headers` prepended in `extract_prose_zone` |
| `post_process.py` | `_dedupe_page_comments`, `_normalize_section_boundaries`, heading/page spacing tweaks |
| `output_validator.py` | Stricter rotated/trailing checks; `reading_order_completeness`; span-start footnote gap check |
| `id_registry.py` | Explicit artifacts for 106–107 and 162–163 spans |

### Honest outcome per target page (post `078f0b8`)

| Test case | Pass? | Evidence |
|-----------|-------|----------|
| **24–25 footnotes** | **Partial** | Footnotes 19–20 appear after Table 2 body, before page markers (`final_output` ~662–671). **Regression:** footnote 19 duplicated (lines 662–666). |
| **106–107 merge** | **Yes** | Single `db:id` with `pages=106-107` (`final_output` ~3080). Adjacent title detection + explicit span entry worked. |
| **162–163 rotated** | **Partial** | No OCR gibberish (`ainjsod \| Apog` gone). English phrases visible but **not production-quality**: char reversals in short tokens (`fo`/`ro`/`ni`), word-order artifacts, `oN descriptors available`, duplicate header rows in table. |
| **183+ appendix rotated** | **Not verified page-by-page** | `chunk_08` re-extracted with derotation; validator still reports `rotated_table_unreadable: 9`. |
| **46–48 headers** | **No** | `### 3.1. RECEPTION` still before `<!-- page:47 -->`, between page 46–47 markers (~1339–1370). Duplicate `#### 3.1.1.` blocks (~1373–1377). Chapter opener + figure diagram interleaved incorrectly. |
| **Overall validation** | **No** | `metadata/output_validation.json`: `valid: false`, **273 issues** |

### Validator breakdown @ `078f0b8` (new / worsened categories)

```
page_under_extracted: 103
span_duplicate_emit: 49      ← NEW mass issue — adjacent title matcher over-groups?
missing_table_markdown: 49
missing_section_header: 27
reading_order_completeness: 12
rotated_table_unreadable: 9
missing_trailing_prose: 1
```

**Attempt 2 introduced or worsened:**

- **`span_duplicate_emit` (49):** Adjacent-page title matching in `span_detector.py` likely created many spurious continuation groups (85 span groups vs fewer before). Needs audit of `metadata/spanning_tables.json` for false positives.
- **Duplicate footnote 19** on Table 2 span body (dedupe incomplete in one code path).
- **Duplicate section headers** on page 48 (extract + cleanup paragraph merge).

---

## What actually works reliably

- **Non-rotated descriptor tables** on normal pages via pdfplumber (unchanged, still good).
- **Explicit span entries** (Table 2, vocabulary, 106–107 when explicit) — merge emits correct `pages=N-M`.
- **Span-start single table emit** — no duplicate table element on continuation *inventory* pages.
- **Reversed title fix** for many rotated *titles* when `fix_rotated_title` runs before display.
- **Architecture wiring** — `reading_order` loop is real; failures are logic gaps not stale merge.

---

## What does NOT work (do not re-claim without proof)

| Approach | Result |
|----------|--------|
| Merge/post-process only on existing `cleaned/` | Cannot restore dropped extract-time content |
| OCR-first rotated extraction (`force_ocr`, `top//20` grid) | Gibberish descriptor cells |
| `span_start: break` without footnote/trailing flush | Drops post-table content |
| Blanket `figure_page` → `rich_page` | Destroys header/page structure on mixed figure pages |
| `_is_table_page` drawing-count gate alone | Misses prose-heavy span starts (106) |
| Post-process alone for `### 3.x` ordering | Cannot fix content emitted before wrong page markers |
| Claiming validators pass because rules exist | Rules must fire on real failures (inventory must schedule checkable elements) |

---

## Rotated table technical findings (important for attempt 3)

1. **pdfplumber on raw rotated PDF** → reversed character order in cells.
2. **Derotated temp PDF** (`fitz show_pdf_page` rotate 90°) + pdfplumber → still reversed chars **until** `_reverse_table_cells()` applied.
3. **After reversal:** `english_word_score` ~0.27, `_table_readable` passes, but short tokens remain broken (`fo` for `of`) because `_reverse_word` only reverses alpha tokens >2 chars.
4. **OCR path** should remain fallback only; never `force_ocr=True` on span merge by default.

**Prototype command that proved derotation path (page 162):**

```powershell
cd agent-extraction
python -c "
from pipeline.extractors.rotated import derotated_pdfplumber_tables, _reverse_table_cells, _table_readable
from pipeline.title_fix import fix_rotated_title
from pipeline.config import PDF_PATH
tables = derotated_pdfplumber_tables(161, PDF_PATH, 90)
fixed = [[fix_rotated_title(str(c)) if c else '' for c in row] for row in _reverse_table_cells(tables)[0]]
sample = ' '.join(c for row in fixed[:8] for c in row if c)
print('readable', _table_readable(sample))
"
```

---

## Figure / header findings (page 47)

- Page 46 inventory: `blank` (footer only). Page 47: figure registry + `section_headers: ["3.1. RECEPTION"]`.
- Attempt 2 mixed order: `prose(body) → figure_ref → footer` but prose zone bbox captures figure diagram text + chapter opener together.
- `page:46` marker with empty body, then `### 3.1. RECEPTION`, then `## Chapter 3` title, then figure diagram — **wrong reading order relative to PDF**.
- `_normalize_section_boundaries` only triggers when `###` immediately precedes `<!-- page:N -->`; here content between them prevents fix.

**Needed (not done):** Split page 47 into zones above figure bbox vs figure reference; emit chapter/section headers in correct page section; page 46 may need content from PDF or explicit carry-forward rules.

---

## Span detection findings

- **Table 2 (24–25):** Explicit entry — worked before and after attempt 2.
- **106–107:** Failed attempt 1 (drawing gate). Fixed attempt 2 via adjacent title match + explicit registry entry.
- **Side effect:** 85 span groups — investigate false adjacent-title matches causing `span_duplicate_emit: 49`.
- **Rotated span slugs:** Attempt 1 had `scale_sevitcepsrep_dna_gnittes`; attempt 2 applies `fix_rotated_title` before `slugify` + explicit `scale_setting_and_perspectives`.

---

## Commands reference

### Full pipeline

```powershell
python run_pipeline.py --step all
```

### After code changes (minimal partial re-run)

```powershell
python run_pipeline.py --step spans
python run_pipeline.py --step inventory          # ~10 min
python -m pipeline.extract_chunk chunk_01        # affected chunks only
python -m pipeline.extract_chunk chunk_02
python -m pipeline.extract_chunk chunk_05
python -m pipeline.extract_chunk chunk_07
python -m pipeline.extract_chunk chunk_08
python run_pipeline.py --step cleanup
python run_pipeline.py --step merge
python run_pipeline.py --step postprocess
python -m pipeline.output_validator
```

### Spot-check greps

```powershell
rg "page:24|page:25|19\.|20\." final_output/CEFR_Companion_Volume.md
rg "scale_expressing_a_personal_response" final_output/CEFR_Companion_Volume.md
rg "scale_setting_and_perspectives" final_output/CEFR_Companion_Volume.md
rg "### 3\.1\. RECEPTION|#### 3\.1\.1\.|page:47" final_output/CEFR_Companion_Volume.md
```

---

## Suggested next steps (attempt 3 — not started)

1. **Audit `spanning_tables.json`** — list all 85 groups; diff vs known-good; remove false adjacent-title matches; re-run inventory only; check `span_duplicate_emit` drops.
2. **Rotated tables** — improve token-level reversal (short words `of`/`or`/`in`); validate column structure (level column + descriptor column); test pages 162, 177+, one appendix page.
3. **Page 47** — explicit zone split using figure bbox from `figures_registry` / pdfplumber drawings; separate chapter opener (page 46/47 boundary) from diagram text.
4. **Table 2 footnote dedupe** — single footnote collection path in span body; remove duplicate fn19.
5. **Validators as gates** — fail merge if target pages 24–25, 106–107, 162–163, 47 fail bespoke checks (not just aggregate 273-issue count).
6. **Update `audit-pack/`** — refresh `03_output_validation.json` and sample outputs after any fix.

---

## Session / cost notes

- **Attempt 1:** Full architecture + full re-extract all chunks + merge.
- **Attempt 2:** Targeted code + full inventory + partial re-extract 5 chunks (`chunk_08` alone ~28 min) + merge.
- **Inventory step:** ~10–12 minutes per run — budget for any attempt 3.
- **User assessment:** Both attempts expensive; **neither fully resolved** the five target failures. Partial wins: 106–107 merge, footnotes mostly on 24–25, rotated tables no longer pure gibberish. Headers/page 47 and production-quality rotated cells remain open.

---

## Changelog for this document

| Date | Update |
|------|--------|
| 2026-07-04 | Initial comprehensive history after attempt 2 commit `078f0b8` |

**Maintainers:** Append to this file after every fix attempt. Do not rely on chat session memory or compaction summaries.