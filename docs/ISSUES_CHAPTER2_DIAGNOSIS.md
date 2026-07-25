# Chapter 2 QA issues — diagnosis log

**Source of findings:** `user debug/log.txt` (user review while reading Chapter 2; issues are systemic, not Chapter-2-only).  
**Date logged:** 2026-07-15  
**Status key:** `open` | `in_progress` | `resolved` | `deferred`  
**Canonical backlog:** also mirrored in `STATUS.md` §5 as Q/C2-* IDs.

> **Session handoff:** Read this file + `STATUS.md` before fixing prose/tables/figures. Do not treat `docs/archive/**` as current.

---

## Executive summary (root-cause clusters)

Issues group into **six systemic root causes**. Most “worked before / broken now” reports track to the full-book re-run + figure inject path, not random one-offs.

| Cluster | Root cause (pipeline layer) | Blast radius |
|---------|----------------------------|--------------|
| **F** Figures | Multi-figure pages collapsed to one artifact; `figure_page` → full-page rich text soup; `apply_figures` caption match fails → PNG dumped at end of book; text_diagram never injects | Figs 1–11, 12–17 pattern |
| **L** Lists / dingbats | Wingdings bullet `f` converted only at **line start**; mid-line `; f ` after first `-` item never split | p.28, 30, 37, 42, 43, … |
| **H** Hyperlinks | PDF link annotations exist but extract never reads them; only footnotes carry URLs | p.30–32 and any inline CoE/ECML links without fn |
| **T** Tables / callouts | Non-scale tables / prose boxes auto-slug as `scale_*` from first column header; multi-line cells collapsed | Table 3 p.33, callout p.35, Table 4/5 cells |
| **P** Paragraph join/split | y-gap join sometimes under-joins list tails / over-splits mid-bold wraps; list + section heading glue | p.30–32, 37, 41–43 |
| **R** Reading order / missing prose | `figure_page` or artifact bbox swallows adjacent prose; multi-figure page missing elements | missing methodological para p.29; fig pages |

**What regressed vs earlier good output**

| Area | Earlier | Now | Likely trigger |
|------|---------|-----|----------------|
| Figure 1 text tree | `figures_catalog` ` ```text ` tree | Caption+label soup, no tree | `figure_page` rich_page + inject miss |
| PNG figures | Inline `![](assets/figures/…)` near caption | Soup in place; PNGs **appended at document end** (page_ctx NONE) | Caption match fails on polluted `**Figure N – … soup**` lines |
| Multi-fig pages (36, 40) | All figures present | Inventory/reading_order only one `figure_page` id (last wins) | `known_figures_by_page` dict overwrite; single `art` in reading_order |
| Wingdings lists | Partial convert | First item `-`, rest `; f ` glued | Mid-line bullet not in postprocess |

---

## Inventory / extract evidence (chunk_02, pages 28–47)

| Page | Inventory `reading_order` (simplified) | Problem |
|------|----------------------------------------|---------|
| 28 | prose, footer | List glue (L) |
| 29 | prose, artifact `scale_a_reminder…`, footer | Missing methodological prose (R/P) |
| 30–31 | pure_text rich_page | Hyperlinks (H); para glue/split (P); misplaced blocks (R) |
| 32 | **`figure_page` figure_01 only** | Should emit text_diagram + prose; rich soup (F) |
| 33 | prose, **`scale_reception`**, prose | Wrong id/type — is **Table 3**, not a scale (T) |
| 34 | `figure_page` figure_02 | PNG not injected at caption (F) |
| 35 | **`scale_can_do_descriptors…` ×2**, prose | Callout box mis-typed as scale (T); missing pre-table prose (R) |
| 36 | **`figure_page` figure_05 only** | Figs **3,4 missing** from order (F multi) |
| 37 | pure_text | Lists; Background heading glued (L/P) |
| 38–39 | figure_page 06/07 | PNG inject fail (F) |
| 40 | **`figure_page` figure_10 only** | Figs **8,9 missing** (F multi) |
| 41–43 | pure_text | Phase split; lists; Step headings (P/L) |
| 47 | figure_page figure_11 | text_diagram missing (F) |

Confirmed in final MD (2026-07-15):

- `promote and facilitate…countries; f provide…; f assist` (list glue).
- `methodological message` **absent** from deliverable.
- Figure captions like `**Figure 1 – … scheme28 Overall language proficiency…**`.
- PNG embeds: 9 total, all with **page_ctx NONE** (appended at end).
- `text_diagram` markers present in registry path but `` ```text `` trees = **0** in body for Fig 1/11 pattern.
- Table 3 → `### Reception | scale_reception`.

---

## Issue catalog

### C2-L1 — Mid-line Wingdings bullets glued (`f` not new list items)

| | |
|--|--|
| **Status** | open |
| **Examples** | p.28 aims list; p.30 paralinguistics tail; p.37 CEFR Table 1/2/3; p.37 A1 can-list; p.42 descriptor bullets; p.43 literature bullets |
| **Symptom** | First item may be `- …; f next; f next` on one line |
| **Root cause** | Dingbat maps Wingdings `f` → literal `f` + space in extract (`page_layout`). Postprocess `_convert_f_bullets` / `_fix_inline_bullets` only fix **line-start** `f` or narrow patterns (`:\s*f**`). Mid-line `; f ` after a real markdown list item is never split. |
| **Proper fix** | Postprocess (and optionally extract): after list context or after `;` / sentence boundary, rewrite `\s+f\s+` / `;\s*f\s+` → new `- ` lines. Avoid converting normal “f ” mid-word. Prefer: within a block that already has `- ` or bullet markers, split on `;?\s+f\s+(?=[A-Za-z“\"])`. |
| **Layer** | `post_process.py` / `prose_format.py` (+ regression tests on Ch2 samples) |

### C2-L2 — Missing prose block (methodological message)

| | |
|--|--|
| **Status** | open |
| **Examples** | p.29 after scale / before next page content |
| **Symptom** | Entire paragraph on action-oriented / criterion-referenced assessment missing |
| **Root cause** | Likely reading-order gap: artifact table zone or page boundary drops trailing/intro prose not in `prose_zone` bbox; or full-page rich extract order wrong after table. Needs per-page bbox audit of inventory vs PDF. |
| **Proper fix** | Rebuild reading_order for mixed pages so **intro + artifact + trailing** prose all scheduled; verify `prose_segments` trailing segment below table. Re-extract chunk_02. |
| **Layer** | `page_elements.prose_segments` / inventory / extract |

### C2-L3 — List item + following paragraph glued

| | |
|--|--|
| **Status** | open |
| **Examples** | p.30 last bullet ends `etc.). The linked concepts…` |
| **Symptom** | New prose paragraph appended to last list item |
| **Root cause** | y-gap join or list soft-wrap logic treats capital-after-period as continuation when gap small; or extract never split at list end. |
| **Proper fix** | After list item ending with `.` / `).`, if next segment is new sentence + paragraph-sized, force paragraph break (not soft-wrap). |
| **Layer** | `descriptor_layout` / `post_process` list repair |

### C2-H1 — Inline hyperlinks without footnotes not emitted

| | |
|--|--|
| **Status** | open |
| **Examples** | p.30 “Plurilingual and pluricultural competence” → `https://rm.coe.int/168069d29b`; p.31 Guide… → `https://rm.coe.int/16806ae621`; p.32 same Guide |
| **Symptom** | Title appears as plain text; URL only in PDF annotation |
| **Root cause** | Extract uses text layer only. **Annotations are available** (`page.get_links()` returns correct URIs + rects). No code maps links onto spans. Footnotes duplicate some URLs; user wants URL in prose **only when no footnote** already carries it (or always parenthetical URL for non-fn links). |
| **Proper fix (systemic)** | During prose/rich extract: load `get_links()`, map rects to character ranges / words, build link spans. Policy: if linked text already followed by fn callout / nearby footnote URL, do not append; else append ` (URL)`. Do not invent HTML `<a>` unless product wants it. Same for all chunks. |
| **Layer** | new helper e.g. `pipeline/pdf_links.py`; wire into `page_layout` / `descriptor_layout` / `extract_rich_page` |

### C2-R1 — Misplaced / reordered prose blocks

| | |
|--|--|
| **Status** | open |
| **Examples** | p.31 mediation / plurilingual research paragraphs appear under wrong preceding block |
| **Root cause** | Reading order or post-merge page assembly; possible figure/list repair moving blocks; need line-level compare to PDF. |
| **Proper fix** | After figure/list fixes, re-audit; if still wrong, fix y-ordered zones in inventory. |
| **Layer** | inventory / extract order |

### C2-P1 — False paragraph splits (mid-sentence / mid-bold)

| | |
|--|--|
| **Status** | open |
| **Examples** | p.31 “Sections\n\n5.1.1.3”; p.32 “under various\n\n**constraints**”; p.41 Qualitative/Quantitative; p.41 quote split; p.43 “2. Descriptors…\n\nThe former…” |
| **Root cause** | Soft line wrap treated as paragraph boundary when gap ≥ threshold **or** bold span forces new line that later becomes `\n\n`. Inverse of glue problems. |
| **Proper fix** | Join rules: if previous line has no sentence end and next continues (digit/lowercase/**word** mid-phrase), join with space; special-case bold-only first token. |
| **Layer** | `page_layout` y-gap + `post_process` join pass |

### C2-F1 — Figures rendered as text soup / PNGs at document end

| | |
|--|--|
| **Status** | open (blocker for Ch2+) |
| **Examples** | Fig 1 (p.32), 2 (p.34), 3–5 (p.36), 6–10 (p.38–40), 11 (p.47), same pattern later chapters |
| **Symptom** | Polluted bold caption + diagram labels as prose; no proper `### Figure N \| id` + body; PNGs only at file end |
| **Root cause** | 1) `build_reading_order` for figures falls back to `figure_page` + `rich_page` when mixed order fails (no section header below caption). 2) Even with `type=figure`, extract may not emit catalog body. 3) `inject_png_figure` / `inject_text_diagram` require near-exact caption match; polluted captions fail → append PNG at end; text_diagram has **no** append fallback. 4) **Multi-figure pages**: only one figure id in reading_order (last registry entry for page). |
| **Proper fix** | See implementation plan §A below. Prefer: registry-driven multi-figure reading order by caption y; extract emits **clean** figure blocks (catalog or placeholder); inject matches `Figure\s+N` and replaces caption+soup through next prose/page. PNG path: `assets/figures/{id}.png` relative for Obsidian **and** standard MD (no wiki links). |
| **Layer** | `page_elements`, `extract_chunk`, `figure_inject`, `apply_figures`, `config.known_figures_by_page` |

### C2-F2 — Multi-figure pages drop figures

| | |
|--|--|
| **Status** | open |
| **Examples** | p.36 (3,4,5) only 5 in RO; p.40 (8,9,10) only 10 |
| **Root cause** | Single artifact pointer per page + dict `page → one figure` patterns |
| **Proper fix** | `figures_on_page(page) -> list[fig]` sorted by caption y; reading_order interleaves prose + each figure |

### C2-T1 — Table misclassified as descriptor_scale (wrong ### name / id)

| | |
|--|--|
| **Status** | open |
| **Examples** | p.33 Table 3 → `scale_reception` / `### Reception` |
| **Root cause** | Auto title from first cell / first column header; not in `KNOWN_TABLES_FIGURES` (only Table 1–2 known) |
| **Proper fix** | Extend known tables registry (Table 3–5 etc.) with `type=table` and correct titles/ids matching Table 2 style; do not slugify first column as scale name for non-level tables. Heuristic: if title line matches `Table N –`, force table type. |
| **Layer** | `config.KNOWN_TABLES_FIGURES` or `tables_registry.json`; `id_registry`; `_artifact_element` |

### C2-T2 — Prose callout box extracted as scale/table

| | |
|--|--|
| **Status** | open |
| **Examples** | p.35 “Can do” descriptors as competence box |
| **Root cause** | pdfplumber table on single-column tinted box → artifact `descriptor_scale` |
| **Proper fix** | Detect single-column narrative boxes → `callout` / prose with blockquote or fenced note, not scale header+empty table rows |
| **Layer** | inventory classification + table extractor |

### C2-R2 — Missing prose before table

| | |
|--|--|
| **Status** | open |
| **Examples** | p.35 paragraph before Table 4 |
| **Root cause** | Callout/table bbox claim full page strip; intro prose not scheduled |
| **Proper fix** | prose_segments intro above first table after callout is separate element |

### C2-T3 — Multi-line table cells flattened (need line breaks)

| | |
|--|--|
| **Status** | open / design |
| **Examples** | Table 4 Mediation/Execution 5 lines; Table 5 “Curriculum designers Teachers” |
| **Root cause** | Cell text joined with spaces; PDF lines not preserved |
| **Proper fix** | Within cell, join pdfplumber/cell lines with `<br>` when y-gap indicates separate visual lines (or known multi-label cells). Prefer extract-time not post-hoc guess. |
| **Layer** | table extractor / multipage |

### C2-P2 — Section / step headings glued to previous list or run-on

| | |
|--|--|
| **Status** | open |
| **Examples** | p.37 `…postcard…). **Background to the CEFR levels** The six-level…`; p.42 list then `**Defining curriculum…**`; p.43 `**An alternative approach is to: Step 1**:` |
| **Root cause** | Bold headings not treated as block starters when following list/prose without blank line in extract |
| **Proper fix** | Detect `**…**` heading patterns and `Step N` / numbered curriculum steps; force `\n\n` before. |

### C2-T4 — Level example table as prose (p.38 A2)

| | |
|--|--|
| **Status** | open |
| **Examples** | A2 overall oral comprehension sample as free prose |
| **Root cause** | Small 2-row table not detected or extracted as rich text |
| **Proper fix** | Ensure table detection + markdown table emit; or intentional callout format |

### C2-F3 — Figure 11+ text_diagram dropped

| | |
|--|--|
| **Status** | open |
| **Examples** | p.47 Fig 11; also 12–17 later |
| **Root cause** | Same as F1; catalog exists in `figures_catalog.py` but inject never attaches |
| **Proper fix** | extract `type=figure` → `figure_block(aid)` when in FIGURE_CONTENT (code path exists but RO uses figure_page) |

---

## Implementation plan (ordered; prefer rewrite over patch)

### A. Figures (do first — highest user impact)

1. Replace one-figure-per-page assumptions with `figures_for_page(n) -> list`.
2. `build_reading_order`: for pages with registry figures, emit multi-element order (prose zones by caption y, each figure element).
3. `extract_chunk` for `figure` / `figure_page`:
   - if id in FIGURE_CONTENT → `figure_block` (text_diagram/mermaid);
   - else emit clean `<!-- db:id=… type=figure render_as=png -->` + `### title | id` only (no soup).
4. Rewrite `figure_inject`:
   - match lines with `Figure\s+N` (optional bold) even with trailing garbage;
   - replace from caption through label-soup until real prose / next page / next figure;
   - never append all PNGs at EOF without page context;
   - use relative path `assets/figures/{id}.png` (standard MD; Obsidian-compatible if wiki links off).
5. Rebuild inventories for affected chunks + re-extract + apply_figures.

### B. Lists / dingbats

1. Systemic mid-line bullet splitter in postprocess.
2. Detach bold section headings after list items.

### C. Hyperlinks

1. Annotation → prose URL policy as above.

### D. Tables / callouts

1. Known registry for numbered Tables + type=table.
2. Callout detection for single-column narrative boxes.
3. Cell multi-line → `<br>`.

### E. Paragraph join/split

1. Tuned join rules for mid-bold wraps and list-end paragraph starts.

---

## Verification checklist (after fixes)

- [ ] p.28 aims list = 3 separate `-` items  
- [ ] p.29 methodological paragraph present  
- [ ] p.30–32 non-fn links show URL once  
- [ ] Fig 1 = text tree under correct `###` / db:id on page 32  
- [ ] Figs 2–10 PNGs inline under captions; **0** orphan PNGs at EOF  
- [ ] p.36 has figures 3, 4, and 5  
- [ ] p.40 has figures 8, 9, and 10  
- [ ] Table 3 has table id/title pattern like Table 2  
- [ ] p.35 callout is not `scale_*` empty table  
- [ ] Fig 11 text_diagram present on p.47  
- [ ] chunk_01–03 re-extract + full figures + postprocess metrics clean  

---

## Implementation progress (2026-07-15)

| Area | Change | Files |
|------|--------|-------|
| Figures | `figure_page` no longer full-page rich soup; composes prose zones + text_diagram catalog / PNG stubs; multi-figure via `figures_for_page` | `extract_chunk.py` |
| Figure inject | Prefix-tolerant `Figure N` match; attach PNG under existing `db:id`; strip polluted captions; drop EOF orphans | `figure_inject.py`, `apply_figures.py` |
| Lists | Mid-line `; f` / `; -` → new list items; Background heading not forced into bullets | `post_process.py`, `prose_format.py` |
| Links | PDF annotations → parenthetical URL when URL not already on page | `pdf_links.py` wired in extract |
| Tables | Table 3 known id/title as `type=table` | `config.py` `KNOWN_TABLES_FIGURES` |

**Applied so far:** re-extract **chunk_02** + cleanup + merge + figures + postprocess (multiple iterations).

### Second-wave fixes (same day)

| Area | Change | Files |
|------|--------|-------|
| Side-column prose | `prose_segments` emits `side` zones for partial-width tables; LTR interleave with tables | `page_elements.py` |
| X-filtered prose | `extract_prose_zone` / `_rows_in_zone` honor bbox x0–x1 (stops column interleave) | `descriptor_layout.py` |
| Callouts | Single-column narrative tables → bold title + body, not `scale_*` | `extract_chunk.py` |
| Table 4 | `KNOWN_TABLES_BY_INDEX[(35,1)]` | `config.py`, `extract_chunk.py` |
| Cell breaks | `\n` in cells → `<br>` | `utils.escape_md_cell` |
| Mid-bold wraps | postprocess rejoin false `\n\n` mid-sentence | `post_process.py` |

**Verified OK on final MD (chunk_02):** methodological para clean; callout not scale; table_03/04; cell `<br>`; lists; fig1 tree; links.

**Still open / partial:** C2-T4 p.38 A2 sample verify; residual P1 splits; full-book re-extract for chunks 03+; optional full inventory rebuild (slow; chunk_02 surgically patched).

---

## User voice (log 03) — not only bugs

**Standing rule:** Log everything the user writes. The user is not technical by requirement; agents must not discard or “translate away” process, product, design, or trust concerns just to fit defect language. Mirror: `STATUS.md` § standing rule + §5a (UV-01…).

| ID | Kind | User intent (faithful summary) |
|----|------|--------------------------------|
| UV-01 | Product | Format blue-background callouts/sidebars/feature boxes consistently as blockquotes: title in `> **…**`, body on `>` lines, blank `>` between paragraphs, keep internal formatting; entire document. |
| UV-02 | Product / naming | User will say “callout” until the project confirms the official name; content still counts. |
| UV-03 | Process | User should not be the regression detector for URL breaks, missing callout text, figure trash, empty tables. Validation must catch prior-fixed classes of failure. |
| UV-04 | Trust / claims | Do not claim fixed when the same failure is still in the deliverable (explicitly: p.30 callout lead, p.31 order, figure crops, links). |
| UV-05 | Design | Prefer less brittle solutions aligned with inventory→extract→assembly; stop isolated patches that re-break structure. |
| UV-06 | Method | User suggested blue-background detection and/or **agent-in-the-loop** for hard visual cases; do not ignore those options and only double down on paths that already failed. |
| UV-07 | Consistency | Same layout pattern must work on every page (p.31 vs p.35 callout+columns) — not spot-fix one page. |
| UV-08 | Contract | Agents said they understood inventory→extract→assembly and then produced output that shows otherwise; honor the contract in code and checks. |
| UV-09 | Problem class | Content drop/misplace around figures, tables, spans, multipage, rotated tables is a **serious recurring class**, not random one-offs. |
| UV-10 | Effort | High effort means do the hard items the user listed, not skip them while spending tokens on easier pages. |
| UV-11 | Table meaning | `<br>` separates phrases that belong as separate units; mid-word/mid-phrase wraps should not get `<br>`; PDF spacing may signal phrase breaks — use judgment/loop if needed. |
| UV-12 | Figures | Few figures exist; each crop must be correct; invest in getting them right. |
| UV-13 | Safety | Fixing p.36 figures must not destroy prose that is finally correct. |

---

## Log 03 defect catalog (`user debug/log 03.txt`, 2026-07-16)

User QA after prior “fixed” pass. Defects below; **non-defect concerns above (User voice)**. Mirror: `STATUS.md` §5 P0 + §5a.

### C2-CO1 — Callout / sidebar / feature-box format standard

| | |
|--|--|
| **Status** | open |
| **Source** | log 03 (global) |
| **Symptom** | Blue-background callouts/sidebars not in a consistent markdown form |
| **Required format** | Blockquote: `> **Title**` (when present), blank `>` between paragraphs, body under `>`, preserve internal formatting; document-wide |
| **Related** | C2-T2 (type detection); p.29 chapter reminder; p.30 plurilingual callout; p.35 Can-do callout |
| **Layer** | extract callout emitter + postprocess consistency |

### C2-CO2 — p.30 plurilingual callout incomplete (**reopened**)

| | |
|--|--|
| **Status** | reopened |
| **Source** | log 03 (also log.txt / prior) |
| **Symptom** | Missing lead sentence: “The linked concepts of plurilingualism/ pluriculturalism and partial competences were introduced… 1996.” Remaining paras present but not blockquote-formatted |
| **Notes** | User reports prior fix claim was wrong; validation did not catch |
| **Related** | C2-CO1 |

### C2-R1 — p.31 multi-column / callout prose order (**reopened, major**)

| | |
|--|--|
| **Status** | reopened |
| **Source** | log 03 (same as prior reports) |
| **Symptom** | Top-left callout + multi-column prose: mediation / research blocks appear after body instead of at top; p.35 side layout worked but p.31 did not (inconsistent) |
| **Required order** | Callout/top-left content first; then “Most of the references…” body as in PDF |
| **Related** | inventory/reading_order; side-column assembly |

### C2-H1 — p.32 embedded Guide hyperlink (**reopened**)

| | |
|--|--|
| **Status** | reopened |
| **Source** | log 03 p.32 |
| **Symptom** | “Guide for the development and implementation of curricula for plurilingual and intercultural education” still without URL from PDF annotation |
| **Related** | C2-H1 original; `pdf_links.py` incomplete coverage |

### C2-F1 — p.32 diagram-label trash after figure (**reopened partial**)

| | |
|--|--|
| **Status** | open / regression |
| **Source** | log 03 p.32 |
| **Symptom** | Before footnote: `**Overall language proficiency Communicative General competences…**` soup still present |
| **Related** | C2-F1 soup strip; must be systemic not page-local |

### C2-F3 — Figure PNG crops wrong (**open / regression**)

| | |
|--|--|
| **Status** | open |
| **Source** | log 03 p.34, p.36 |
| **Symptom** | Fig 2 still half image; Fig 3 wrong; Fig 5 wrong (user believes Fig 5 was OK before) |
| **Notes** | Prose on p.34/36 must not be broken while fixing crops. Prefer agent-in-loop or robust crop detection over fragile registry fractions |
| **Layer** | `figures_registry.json` crop + `crop_figure_png` / apply_figures |

### C2-U1 — Broken URLs with inserted spaces

| | |
|--|--|
| **Status** | open |
| **Source** | log 03 p.27 fn21, p.29 fn23 |
| **Examples** | `result_details. aspx`; `https:// rm.coe.int/1680667a2d` |
| **Proper fix** | Sanitize all extracted URLs (strip internal whitespace); validate every `http(s)://` in final MD |
| **Related** | C2-V1 |

### C2-T3 — Table 4 `<br>` over-application (**reopened**)

| | |
|--|--|
| **Status** | reopened |
| **Source** | log 03 p.35 Table 4 |
| **Symptom** | Soft-wraps became `<br>`: “previous\<br\>knowledge”, “Breaking down\<br\>complicated”, “Evaluation\<br\>and Repair”. Want `<br>` only between **distinct phrases**, not mid-phrase PDF wraps |
| **Notes** | Authors may use extra visual gap between phrases — use geometry/gap if coding, else agent judgment |
| **Layer** | `escape_md_cell` / table extract line-join policy |

### C2-G1 — Empty junk table at page end

| | |
|--|--|
| **Status** | open |
| **Source** | log 03 p.36 (pattern may recur) |
| **Symptom** | Empty markdown table `\| \|\n\| --- \|\n\| \|` before page footer |
| **Proper fix** | Do not emit empty tables; strip in cleanup/validate |
| **Related** | C2-V1 |

### C2-V1 — Validation insufficient

| | |
|--|--|
| **Status** | open |
| **Source** | log 03 commentary |
| **Symptom** | Prose-mass check did not catch missing callout lead sentence, broken URLs, figure crop quality, leftover soup, empty tables |
| **Proper fix** | Expand `validate_chunk_prose` (or sibling) to URL integrity, soup patterns, empty tables, optional callout lead phrases; fail closed before “resolved” claims |
| **Related** | E5 contract drift |

---

## Change log for this diagnosis file

| Date | Note |
|------|------|
| 2026-07-15 | Initial diagnosis from `user debug/log.txt` + inventory/final MD/PDF link probe |
| 2026-07-15 | Systemic figure/list/link/table3 implementation started; chunk_02 re-run |
| 2026-07-15 | Side-column prose, callout detector, Table 4, cell `<br>`, x-filter; most C2 P0 items resolved on chunk_02 |
| 2026-07-16 | **log 02 red flags:** figure_page y-cursor compose dropped prose (p32/34/36); caption match treated “Figure N, which…” as caption; inject stripped prose; Fig2 crop too tight. **Fix:** figure_page = full `rich_page` prose + caption-line insert; caption only `Figure N –`; inject never strips prose mentions; crop fig2 `0.42–0.61`; chapter sidebar italics; prose-mass validation (`validate_chunk_prose.py`) |
| 2026-07-16 | **log 03:** defects reopened/added (C2-*); **User voice UV-01–UV-13** logged for non-bug concerns; STATUS standing rule + §5a; AGENTS.md logging rule. No code in voice-logging step |
| 2026-07-16 | **Contract hardening (Grok 4.5 audit):** `docs/CONTRACTS.md`; `contract_validators.py` fail-closed (wired merge); callout blockquote emit + postprocess protect/repair; multi-fig RO `figure_ids`; inventory callout types p.29/35; pdf_links multi-rect + known titles; URL sanitize; smart cell soft-wrap; empty table suppress; soup strip extended; chunk_02 inventory rebuild + re-extract. **Still open:** p.30–31 pure_text (drawing callouts), C2-R1 order, C2-F3 crops, full-book re-run |
| 2026-07-16 | **Pass 2:** `callout_detect.py` blue-fill detection; pure_text pages use callout+side RO (p.30–31); extract `callout_bbox`; gates V-ORDER-31 + blockquote lead; progressive-para dedupe (p.43); chunk_02 re-extract×2. Progress log: `metadata/CONTRACT_HARDENING_PROGRESS.md`. **Still open:** Phase 5 full book |
| 2026-07-16 | **User QA:** p.30–31 appear resolved. STATUS C2-CO2 + C2-R1 marked resolved (chunk_02); gates retained fail-closed |
| 2026-07-17 | **C2-ADJ (adjacent-element damage):** plan archived `docs/plans/2026-07-17_adjacent_element_protection_plan.md`; implementation ledger `docs/ADJACENT_ELEMENT_PROTECTION.md`. Partial ship: adjacent_guard, strip under PNG, p.47 3.1 restore. Remains: exclusive RO extract, callout placement, goldens |
| 2026-07-17 | **log 05 visual QA:** Logged L05-* IDs in STATUS. Implemented: FN glue (sanitize + repair), page `*` caption + chapter running heads, p.27 fence/callout, p.29 chapter soft-wrap, Guide URL attach, problemsolving, p.35/p.37 callout/prose, p.38 A2 table, p.41 §3.7 URL, figure crop agent-loop (registry 3/5/6/7/8/9/10). Gates: adjacent_guard + contract_validators **green**. **Still open:** C2-F3 user visual confirm; L05-P41-CO placement rule (inline when no multi-col); UV-* process/product; full-book inventory rebuild outside chunk_02; callout content quality residuals (e.g. p.41 research callout band stitch) |
| 2026-07-19 | **log 06:** User: single-pass figure crops still fail; fig 9/10 must be tables; ignored prior flags (2.7 heading, p.41 bottom). **Response:** multipass crop module (`figure_multipass_crop.py`) + 3× scale geometry crops for figs 2–8 with pass-2/3 visual re-read; figs 9–10 → markdown tables in `figures_catalog`; A2 sample table headers Level/Illustrative Descriptors; §2.6/2.7 detangled; fn21 URL rejoin; situation-specific; p.41 callout rebuilt from full textbox. Gates green. **C2-F3 still open** pending user visual confirm |
