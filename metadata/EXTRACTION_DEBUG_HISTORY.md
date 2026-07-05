# Extraction Debug History — Persistent Session Notes

**Purpose:** Living record of what was tried, what was claimed, what actually happened, and what remains broken.  
**Survives:** Git commits, compaction, new Cursor/Grok sessions.  
**Read this first** before any new extraction fix attempt.

**Last updated:** 2026-07-04 (post user verification of attempt 3)  
**Active branch:** `execute-plan/c0b4a280-pr-5-pipeline-re-run-and-documentation` @ `9526996`  
**Master merge:** **NOT done** — user did not merge; `master` still has attempt-2 commits. No merge-conflict corruption risk to current deliverable; attempt-3 output lives on the execute-plan branch only.

---

## Where documentation lives

| File | Role |
|------|------|
| **`metadata/EXTRACTION_DEBUG_HISTORY.md`** (this file) | **Canonical** bug registry, cross-attempt history, honest outcomes |
| `metadata/attempt3_design.md` | Attempt 3 PR plan (execute-plan) |
| `remaining-fixes.md` | Attempt 2 plan + checklist (mostly superseded; see this file for truth) |
| `metadata/extraction_plan.md` | Operational spec (`reading_order` contract) |
| `metadata/output_validation.json` | Latest validator output |
| `metadata/spanning_tables.json` | Span groups (32 after attempt 3 chain merge) |
| `final_output/CEFR_Companion_Volume.md` | Deliverable under test |

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
| A1 | Trailing prose below Table 2 on page 25 ("In addition to Chapter 2…") missing from output | **RESOLVED** | Inventory schedules `prose:trailing` on page 25; prose appears in `final_output` ~665 before `<!-- page:25 -->`. User confirmed good. |
| A2 | Footnote **19** duplicated | **RESOLVED** | Single `19.` line in pages 24–25 region (~660). `_extract_span_body` no longer re-collects footnotes. |
| A3 | Footnote **20** duplicated and misplaced | **OPEN** | **Not fixed.** Fn20 embedded inline in trailing prose (~667: `…schools",20 which helped…` plus full fn20 line same paragraph). Orphan `Introduction` + wrong-case marker `<!-- Page 25 -->` (~669–670) from PDF footer bleed. Fn20 repeated again (~672) before canonical `<!-- page:25 -->` (~674). Validator `footnote_single_owner` only checks fn19 — **gate is insufficient**; attempt 3 falsely treated fn20 as non-issue. |
| A4 | Span-end page contract: footnote_zone vs prose both ingest footer band text | **OPEN** | Related to A3. Trailing prose extractor and footnote_zone both pull from page 25 footer band without exclusive ownership. |

### B. Page 47 / Figure 11 / section order (original header regression)

| ID | Bug | Status | Attempt 3 |
|----|-----|--------|-----------|
| B1 | Wrong vertical order (3.1 RECEPTION before Chapter 3 / figure) | **PARTIAL → user accepts** | Order now: `## Chapter 3` → `db:id=figure_11…` → text diagram → `### 3.1. RECEPTION` → body (~1372–1401). User confirmed order correct. |
| B2 | Missing figure caption header between `db:id` and diagram | **OPEN** | **Not fixed.** Expected: `### Figure 11 – Reception activities and strategies \| figure_11_reception_activities_strategies` between db comment and ` ```text ` block (~1375). Only db:id + diagram emitted; **no "Figure 11" string anywhere in final_output**. Validator `page_47_section_order` does not check for this header — false PASS. |
| B3 | Duplicate `<!-- page:N -->` markers (document-wide) | **OPEN** | **Not fixed.** 69 pages have duplicate lowercase markers in `final_output`. User spot-check: duplicates through ~page 45, singles for 46–47 band. Agent verify: pages 46–89 mostly single; dups resume at 90+ (e.g. 145, 149). Not caused by master merge (merge never done). Likely **merge/postprocess** concatenating chunk boundaries or stale+cleaned chunk overlap — downstream of extract, not inventory. |
| B4 | Stray `<!-- Page N -->` (capital P) inside body | **OPEN** | PDF footer artifacts in prose (~670 page 25, also 5, 7, 9, 33, 61, 71, 127, 133). Not normalized away. |

### C. Spanning tables / rotated extraction (pages 146–148 focus)

| ID | Bug | Status | Attempt 3 |
|----|-----|--------|-----------|
| C1 | `span_duplicate_emit` on page 147 (pairwise spans 146–47 + 147–48) | **RESOLVED** (inventory/validator) | Chain merge → single `scale_sign_language_repertoire` 146–148 in `spanning_tables.json`; page 147 `role: middle`. No `span_duplicate_emit` in validator. **Extraction quality still broken (see C2–C5).** |
| C2 | Rotated span body gibberish | **OPEN** | **Not in scope for attempt 3 fix; still broken.** Single db:id block (~4131) but **three pipe-table blocks** of OCR/reversal garbage (~4134–4246). User: "3 tables with gibberish" — confirmed in output. |
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

## Attempt 4 — scope (NOT STARTED)

**User directive:** Focus **solely on rotated tables**, likely **`scale_sign_language_repertoire` pages 146–148**. Do not plan until bugs above are logged (done). Collaborative PDF verification required before claiming fix.

---

## Commands reference

```powershell
python -m pipeline.debug_page 25,47,146,147,148
python -m pipeline.output_validator
rg "page:25|page:47|page:146|sign_language_repertoire|Figure 11" final_output/CEFR_Companion_Volume.md
```

---

## Changelog

| Date | Update |
|------|--------|
| 2026-07-04 | Attempt 3 execute-plan stack; internal PASS claims |
| 2026-07-04 | **User verification pass:** reopened A3, A4, B2–B4, C2–C5, D1–D2; downgraded attempt 3; added open bug registry; noted no master merge |

**Maintainers:** Append after every fix attempt. Do not mark RESOLVED without user-visible proof in `final_output`.