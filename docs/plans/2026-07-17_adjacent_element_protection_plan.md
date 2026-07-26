# Plan: Stop adjacent-element damage when fixing one element

**Date:** 2026-07-17  
**Mode:** Plan (analysis + systemic design; implement after approval)  
**User ask:** Analyze logs (esp. log 04 + prior) for how fixing one element damages neighbors; find root causes across figure/table/prose/callout/footnote work; design a system-level fix so this churn ends.

**Orientation:** Builds on prior contract audit (`docs/CONTRACTS.md`, `docs/ARCHITECTURE.md`, earlier plan on inventory SoT). This plan is **not** a re-do of all C2 bugs; it is the **cross-cutting design defect** that turns every element fix into new bugs.

---

## Context (why this is the real blocker)

You reported, repeatedly, that **a fix never stays local**:

| Source | Your words (compressed) |
|--------|-------------------------|
| **log 02** | Figure text diagram fixed → **old figure soup still at page end**; prose **before/after** figure dropped (p.32/34/36). “inventory:extraction:assembly … no guessing.” |
| **log 03** | Prose fixed → **PNG still wrong**; p.35 callout+column works, p.31 same class doesn’t; “don’t fuck that up with your fix.” |
| **log 04 #5** | Fig 1 soup gone, link OK → **`Page **32** glued to footnote**. “You fix something and then the thing around it fails… leftover garbage, same line, duplicative, before/after.” |
| **log 04 #8** | “Make it a PNG” → PNG present **but figure-as-prose garbage left under the PNG**. |
| **log 04 #10** | Fig 11 fixed → **`### 3.1 RECEPTION` after figure missing**. “When you fix something you broke what follows… central piece of code missing.” |
| **log 04 #13** | URL sanitize OK → **blank line before `Page **27**` lost**. |
| **log 04 #0.1–0.2, #3–4** | Callout placement/format work → **mid-paragraph insertion, title twice, partial para merge**. |
| **log 01** | Fig 6/7 “mess”; Fig 7 labels **after normal prose end**; Fig 11 soup **after** prose; A2 as prose. |

This is not “the PDF is hard.” It is **the pipeline has no unit of work that is a whole page with exclusive ownership of bboxes**. Fixes operate as **global string rewrites** or **second layout engines** layered on top of extract, so neighbors are not protected.

---

## Case catalog: fix → adjacent damage

| # | Reported fix target | Adjacent damage (user) | Mechanism class |
|---|---------------------|------------------------|-----------------|
| A | Figure → PNG / diagram | Old figure **text left under** PNG; **duplicate** headers | Dual emission (replace without delete) |
| B | Figure soup strip | Real prose **after** figure dropped (log 02); later soup strip incomplete for radar labels | Over-aggressive strip **or** under-scoped strip |
| C | Figure compose (y-cursor / rich_page) | Prose **before** figure vanished | Second layout engine ≠ inventory RO |
| D | Callout blue-box RO | Callout **into middle of prose**; title **twice**; para fragments merged | Interleave + emit without exclusive bbox; double emit (table + callout) |
| E | Callout / figure format | Footnote + **page number same line**; blank line **before page caption** lost | Postprocess join of adjacent lines |
| F | Figure 11 fixed | **Section header 3.1** after figure gone | Compose/inject path doesn’t re-emit structural prose from RO |
| G | Crop PNG | Prose under figure **included in crop** (Fig 5 “accidentally fine” only because no text below) | Crop is page-fraction, not element-bounded |
| H | Full re-extract for one fix | Unrelated pages regress | No page-level golden / no adjacent gates |

---

## Root thesis (one sentence)

**There is no exclusive, validated ownership of each page region:** extract often emits **all text** (rich_page / full zones), then later stages **add** the correct representation of an element (PNG, callout blockquote, catalog tree) **without removing or fencing the old representation**, and postprocess **rejoins lines across element boundaries**—so every “fix element E” is actually “mutate the whole page string.”

---

## Root causes (system design, not one bug)

### RC1 — Dual layout / dual emission (primary)

| Stage | What happens |
|-------|----------------|
| Inventory claims | `reading_order` lists prose / figure / callout / footer |
| Extract reality | `figure_page` runs **full `rich_page`**, which **includes** diagram labels, captions, and body as one text stream |
| Then | Inserts clean figure block **at** caption **or** inject **adds** PNG under `db:id` |
| Missing step | **Delete or never emit** the text that belongs to the figure bbox |

**Code evidence:**

- `extract_chunk._extract_figure_page_composed`: full rich prose first, then caption insert; soup strip is heuristic and incomplete for radar-style labels (Fig 6–8).
- `figure_inject.inject_png_figure`: Path 1 — if `db:id` exists, **only inserts `![](…png)`** and strips polluted **captions**, **not** following label-soup lines. Exactly: “made PNG, left prior prose underneath.”

Same pattern for callouts: blue-box path can emit blockquote **while** side/intro prose still contains the same text or title.

### RC2 — No exclusive bbox ownership on the page

Elements are not treated as **partitions** of the page:

```
Page = union of non-overlapping regions
  each region → exactly one RO element → exactly one emit
```

Instead:

- Prose zones and figure regions **overlap** in text extraction (full page text + figure crop).
- Callout fill bbox and “side” prose can **double-cover** or **wrong-order** content.
- Tables and callouts both claimed the same visual box → **title twice**.

Without partition + exclusive extract, “fix figure” always risks touching prose in the same y-band.

### RC3 — String-global post-assembly stages

| Stage | Blast radius |
|-------|----------------|
| `apply_figures` | Whole MD file, caption match, soup heuristics |
| `post_process` / `prose_format` | Whole file line joins, list repair, blockquote repair |
| Callout/list fixes | Can glue footnote + `Page N`, drop blank lines, merge paragraphs |

These layers **do not know** “this line is owned by footnote vs page_footer vs figure.” So a join rule that helps lists **breaks** footnote/page spacing (log 04 #5, #13).

### RC4 — No adjacent-element regression gate (process + code)

CONTRACTS say fail-closed for some classes, but **nothing requires**:

- Before claiming figure fixed: **no** figure-label soup under PNG; **no** duplicate `### Figure`; **real** trailing prose / next section header still present.
- Snapshot of **neighbors** (N lines before/after element) before vs after a change.

Agents (and tools) optimize the **reported** symptom; neighbors are untested. You become the adjacent-element detector (log 04 #5, #10 — said explicitly).

### RC5 — Agent rework without replace semantics

When agent/user says “not prose, make PNG”:

- Correct: **replace** figure region content with figure artifact only.
- Actual: **add** PNG path, leave old rich-text emission.

That is an **operation semantics** bug: fix means “set representation,” not “append representation.”

### RC6 — Spans / chunks amplify (same root, wider blast)

Multipage spans and chunk boundaries already need careful RO. Dual emission + global postprocess means a figure fix on page N can also disturb footer, next section, or continuation prose—even on a **single** page, the same pattern holds.

---

## What must change (system design)

### Principle: **Page as ordered exclusive regions**

```
1. Inventory RO = ordered list of regions {type, id, bbox, expected_chars}
2. Extract(region) uses ONLY that bbox (never full-page text for figure pages)
3. Assembly = concat(extract(r) for r in RO)  — no second layout
4. apply_figures attaches assets INTO the figure region only; must DELETE competing text in that region
5. post_process may reformat within a region; must not join across region markers
6. Validate neighbors: for each fixed region, gates on prev/next RO elements
```

This aligns with CONTRACTS §1–2 but **enforces** what code currently violates.

### Design pieces (implementation plan)

#### P0 — Element fence markers + neighbor validation (stop the bleeding)

**Goal:** Make adjacent damage **detectable** and **fail-closed** before “resolved.”

1. Emit optional HTML comments around each RO element at extract time:
   ```html
   <!-- el:start type=figure id=figure_06 page=38 -->
   ...
   <!-- el:end id=figure_06 -->
   ```
   (Or reuse `db:id` + page markers; prefer explicit fences for prose zones too.)

2. New module `pipeline/adjacent_guard.py` (or extend `contract_validators.py`):
   - **V-ADJ-FIGURE-SOUP:** after `![...](…figure_N….png)` / text_diagram fence, until next `el:start` / section heading / footnote: no radar/diagram label soup patterns.
   - **V-ADJ-DUP-HEADER:** no two consecutive `### Figure N` or duplicate callout titles.
   - **V-ADJ-PAGE-FOOTER:** `Page **N**` not glued to previous footnote line (blank line required).
   - **V-ADJ-SECTION-AFTER-FIG:** for known pages (e.g. p.47 → `### 3.1 RECEPTION` before body prose).
   - **V-ADJ-GOLDEN-SNIPPET:** optional short “must contain” / “must not contain” per page from log 04 checklist.

3. **Agent rule (AGENTS.md / CONTRACTS):** Any change to figures/callouts/tables requires running adjacent_guard on **that page ±1** before claim fixed.

#### P1 — Figure path: replace, don’t layer

**Files:** `extract_chunk.py`, `figure_inject.py`, `page_elements.py`

1. **Deprecate dual layout:** Inventory expands multi-fig + prose zones with bboxes; extract `figure` only emits stub/catalog **from figure bbox**, not full rich_page labels.
2. Until full RO rewrite: in `_extract_figure_page_composed` / inject:
   - When attaching PNG or text_diagram, **strip figure-label soup from caption through next real prose** (expand soup detector for radar labels: “Understanding conversation…”, axis names, **MEDIATION**/RECEPTION blocks after image).
   - inject Path 1 (`db:id` exists): after inserting image, run **same strip** under that figure, not only `_strip_polluted_captions`.
3. **Registry crop** remains agent-in-loop (log 04 final call); crop must not include prose under figure (y1 above next prose baseline).

#### P2 — Callout path: exclusive region + single emit

**Files:** `callout_detect.py`, `page_elements.py`, `extract_chunk.py`

1. Callout text **only** from callout bbox; side/intro zones must **exclude** that x/y (already partial).
2. Never emit callout twice (table + callout_bbox).
3. Title once in blockquote (log 04 #3, #4).
4. Placement policy per your log 04 rule (confirm in implementation):
   - Top-left callout → first in RO  
   - Else callout → end of body, before footnotes  

#### P3 — Postprocess must respect fences

**Files:** `post_process.py`, `prose_format.py`

1. Do not soft-join lines across `el:end` / footnote / `Page **N**` / `###` / `db:id`.
2. Blockquote repair must not merge partial paragraphs (log 04 #0.1 duplication).
3. Footnote ↔ page caption: force blank line (log 04 #5, #13).

#### P4 — Golden page snapshots (process)

For pages in log 04 checklist (27–47):

- Store `work/metadata/golden/page_NNN.snippet.md` or phrase sets: must_have / must_not_have.
- On any extract of chunk_02, fail if golden fails.
- Stops “Fig 11 fixed, 3.1 gone” from shipping green.

---

## Mapping log 04 systemic notes → design

| Your log 04 demand | Plan response |
|--------------------|---------------|
| Test fix against before/after neighbors | P0 adjacent_guard + golden |
| Leftover garbage under PNG | P1 replace + soup strip under image |
| Duplicate headers / titles | V-ADJ-DUP-HEADER; single emit |
| Footer glued / blank lost | P3 fence-aware postprocess |
| Section after figure dropped | RO exclusive zones + golden for 3.1 |
| Agent in loop for figures | Unchanged UV-06; crop QA; not string hacks alone |
| System comment / reminder | CONTRACTS + AGENTS.md adjacent-damage rule |

---

## Critical files

| Path | Role |
|------|------|
| `docs/CONTRACTS.md` | Add “exclusive regions + replace semantics + adjacent validation” |
| `AGENTS.md` | Mandatory adjacent check after element work |
| `pipeline/extract_chunk.py` | Stop full-page figure dual emit; strip under figure |
| `pipeline/figure_inject.py` | PNG attach must clear figure garbage under block |
| `pipeline/page_elements.py` | RO as exclusive regions |
| `pipeline/callout_detect.py` / extract callout | Single emit, placement policy |
| `pipeline/post_process.py` | No cross-fence joins |
| `pipeline/contract_validators.py` | Adjacent gates |
| `work/metadata/golden/` | Page neighbor snippets |
| `user debug/log 04.md` | Checklist source of truth for goldens |
| `STATUS.md` | New backlog ID e.g. **C2-ADJ** / **E6** |

## Reuse

- Existing `db:id`, `<!-- page:N -->`, soup helpers (extend, don’t throw away).
- `figures_registry` / `callouts_registry`.
- Contract validator wiring in `merge_output`.

---

## Verification (measurable)

After implementation, these must **fail closed** if regressed:

1. p.38–40: PNG/table figures present; **no** axis-label soup under Fig 6–8; real prose after figures kept.  
2. p.47: Fig 11 tree + **`### 3.1 RECEPTION`** before “Reception involves…”.  
3. p.32: no soup; footnote not glued to `Page **32**`.  
4. p.27: blank line before `Page **27**` after footnotes.  
5. p.29/35: callout title **once**.  
6. Changing only fig crop + re-apply_figures must **not** change neighbor golden snippets.

Manual: re-walk log 04 FIXED? column after one chunk_02 cycle.

---

## Execution order (post-approval)

1. **P0** adjacent_guard + goldens from log 04 (even before perfect extract) — stops silent churn.  
2. **P1** figure inject/extract **replace** semantics (Fig 6–8 garbage under PNG).  
3. **P3** postprocess fence rules (footer/page glue).  
4. **P2** callout exclusive emit + placement policy.  
5. Document CONTRACTS/AGENTS; STATUS **C2-ADJ**.  
6. Re-extract chunk_02; only then broader book.

---

## What this is not

- Not “another spot fix for Fig 6.”  
- Not a request for a new full audit from you.  
- Not re-litigating every C2 item—**adjacent-damage is the meta-bug** that multiplies all of them.

---

## Executive summary

| Question | Answer |
|----------|--------|
| Why does fixing one thing break neighbors? | Dual emission + full-page text + global postprocess + no neighbor validation. |
| Is it PDF spanning? | Spans make it worse; **same bug on single pages**. |
| Why “PNG left prose underneath”? | Inject **adds** image without **removing** figure-region text (RC1). |
| Systemic fix? | Exclusive RO regions, **replace** not layer, fence-aware postprocess, **adjacent fail-closed gates** + goldens. |
| First ship? | P0 gates + P1 figure replace/strip under PNG—stops the worst churn class. |

---

## Success criteria

- You no longer find “fixed X, broke line after X” as the default outcome on Ch2 figure/callout work.  
- Validators fail when garbage remains under PNG or next header disappears.  
- Agent workflow: change element → run adjacent_guard on page → only then claim progress.
