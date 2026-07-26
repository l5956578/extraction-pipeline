# Audit: Adjacent-element protection implementation vs plan

**Date:** 2026-07-17  
**Auditor:** Grok (plan-mode readonly verification)  
**Question:** Was the C2-ADJ work done correctly relative to the approved plan? What should the user do next?

**Sources checked:**  
- Plan: `docs/plans/2026-07-17_adjacent_element_protection_plan.md`  
- Ledger: `docs/ADJACENT_ELEMENT_PROTECTION.md`  
- STATUS C2-ADJ, AGENTS.md, CONTRACTS.md  
- Code: `adjacent_guard`, `page_layout.should_drop_line_for_exclusive`, `extract_chunk`, `figure_inject`, `page_elements` callout placement, `post_process`, `metadata/golden/*`  
- Live deliverable: `output/CEFR_Companion_Volume.md`  
- Inventory: `inventories/chunk_02_inventory.json` (pages **26–50**)  
- Commands: `python -m pipeline.adjacent_guard` → **OK**; `python -m pipeline.contract_validators` → **OK**

---

## Short answer (for a non-developer)

| Question | Answer |
|----------|--------|
| Did they implement the **plan’s packages** (P0–P4)? | **Mostly yes** — the protective machinery is real and wired. |
| Did they achieve the plan’s **ideal end-state** (full exclusive RO, no `figure_page` sugar)? | **No** — that remains optional/later; the plan itself allowed interim approaches. |
| Is the work **correct enough** to trust more than “green validators only”? | **Yes, for chunk_02-class checks** — spot probes on the deliverable match the plan’s success criteria for the pages the work targeted. |
| Was anything **over-claimed**? | Early implementer wording said dual emission was “structurally impossible”; review forced honesty. Current STATUS/ledger language is **more accurate**. |
| What was worked on? | **Chunk 02** (PDF pages **26–50**), rebuilt into the final MD. Other chunks only get new behavior on a full inventory rebuild + re-extract. |

**Bottom line:** This is **not** a fake “docs only” pass. It **does** implement the plan’s core intent (detect neighbor damage, replace figure garbage under PNGs, place callouts, fence postprocess, goldens). It is **not** a complete rewrite of the entire extraction architecture. That residual is documented, not hidden.

---

## Scope clarity (what “it worked on”)

| Item | Fact |
|------|------|
| **Chunk** | **chunk_02** = PDF pages **26–50** (Chapter 2 + start of Ch 3) |
| **Evidence** | Inventory RO rebuilt for callout placement; re-extract + merge path focused on chunk_02 |
| **Deliverable** | Full book MD was refreshed when merge ran, but **callout placement RO** is only guaranteed updated for chunk_02 |
| **Final MD checks** | p.27–29, 32, 35, 38–40, 47 probed programmatically in this audit |

You were right that feedback was fuzzy. Treat the verified surface as: **“adjacent-protection for chunk_02 patterns in the current final MD.”**

---

## Package-by-package: plan vs code vs audit

### P0 — Fences + neighbor validation

| Plan required | Implemented? | Audit notes |
|---------------|--------------|-------------|
| `el:start` / `el:end` (optional) | **Yes** | Present in final MD (~58 starts); extract wraps RO elements |
| `adjacent_guard` gates (soup, dup header, page footer, section after fig, golden) | **Yes** | Module exists; wired into `contract_validators`; both exit 0 |
| Agent rule in AGENTS.md | **Yes** | Adjacent check mandatory before claim fixed |

**Verdict P0: Done correctly for plan intent.** Gates are not exhaustive of every page in the book, but they exist and fail closed for the classes they define.

### P1 — Figure replace, don’t layer

| Plan required | Implemented? | Audit notes |
|---------------|--------------|-------------|
| Don’t leave figure-as-prose under PNG | **Yes (defended)** | Strip under images + selective exclusive drop of diagram labels |
| Prefer exclusive regions / not full dual layout forever | **Partial** | Still uses `figure_page` sugar on p.38/40/47 inventory; exclusive filter is **selective** (keep prose, drop labels) — correct fix after review found over-deletion |
| Multi-fig handling | **Improved** | p.40 figure order 8→9→10 verified in MD |
| text_diagram path | **Strip-based, not exclusive-bbox** | Honest in ledger; p.47 leaf soup was fixed after review and is clean now |

**Deliverable probes:**

- p.38 Fig 6 PNG present; **no** “Understanding conversation between other speakers” after figure id  
- p.39/40 key neighbor prose phrases **present**  
- p.40 no level/language axis dump under images (per golden/must_not_have_after_image intent)

**Verdict P1: Correct enough; not the pure ideal.** Plan said “until full RO rewrite” for interim strip — that path was taken and improved under review. Claiming “structurally impossible dual-emit for every multi-fig edge case” would be **wrong**; current docs mostly avoid that overclaim.

### P2 — Callout exclusive + placement

| Plan required | Implemented? | Audit notes |
|---------------|--------------|-------------|
| Top-left first; else end of body before footnotes | **Yes in RO builder** | `_is_top_left_callout` + `_callout_mixed_order` |
| Inventory reflects policy (chunk_02) | **Yes** | p.27/28: prose then callout then footnotes; p.31: callout first |
| Title once | **Yes for p.29 sample** | Dedupe helpers |

**Verdict P2: Done for chunk_02 blue-box path.** Table-path callouts (p.35) still use pdfplumber_table typing but shared emit helper. Full-book RO not rebuilt for placement.

### P3 — Postprocess boundaries

| Plan required | Implemented? | Audit notes |
|---------------|--------------|-------------|
| Don’t join across fences / Page / headings | **Yes** | `_is_block_starter` includes el fences, Page, images, db:id |
| Blank before `Page **N**` | **Yes** | Helper + sample OK on p.32 pattern |
| p.47 section after figure | **Yes (safety net)** | Hardcoded restore + golden; not pure RO purity |

**Verdict P3: Done for stated goals.** §3.1 inject is a **safety net** (plan preferred pure RO; this is acceptable interim).

### P4 — Goldens

| Plan required | Implemented? | Audit notes |
|---------------|--------------|-------------|
| Golden suite for log 04 pages | **Partial vs “all 27–47”** | Files: 027, 028, 029, 032, 035, 038, **039, 040**, 047 — not every page in 27–47 |
| Fail if golden fails | **Yes** | Loaded by `adjacent_guard` |

**Verdict P4: Good coverage of critical pages; not full checklist range.** Enough for fail-closed on known regressions.

### Docs

| Plan required | Implemented? |
|---------------|--------------|
| CONTRACTS / AGENTS / STATUS / ledger | **Yes** |

---

## Plan success criteria — pass/fail

| Criterion | Result |
|-----------|--------|
| Fixing X should not routinely break before/after X | **Improved** by design + gates; cannot prove “never” without full visual QA |
| Validators fail if garbage under PNG or next header gone | **Pass** for instrumented cases (Fig 6, p.47, goldens) |
| Workflow: change → adjacent_guard → claim | **Documented** in AGENTS; process still human-enforced |
| p.38–40: PNG, no axis soup, prose kept | **Pass** on current MD probes |
| p.47: Fig 11 + 3.1 + lead | **Pass** |
| p.32: blank before page | **Pass** (pattern) |
| p.29/35 title once | **p.29 pass**; p.35 via golden max_title_count |

---

## Unreported / under-reported items (surfaced for you)

1. **Chunk scope:** Work product claims and rebuilds center on **chunk_02 (26–50)**. Full-book callout placement is **not** guaranteed until inventory rebuild + re-extract of other chunks.  
2. **Ideal architecture incomplete:** Inventory still shows `figure_page` alone for p.38/40/47 — not multi-element RO. Plan’s pure principle is only **partly** realized.  
3. **§3.1 is still a postprocess inject** if extract drops it — works, but can mask extract regressions if golden ever weakened.  
4. **Agent crop loop (C2-F3)** was **never** part of “done” for C2-ADJ; still open.  
5. **Review loop value:** First implementer over-claimed; review forced prose-preserving exclusive filter and stronger goldens. That is healthy, not a failure of the plan.

Nothing found that suggests the team **faked** validators or only edited docs without code.

---

## Overall grade

| Dimension | Grade | Meaning |
|-----------|-------|---------|
| Fidelity to plan packages P0–P4 | **B+ / A−** | Packages implemented; pure exclusive RO end-state still “later” |
| Honesty of status language | **B+** after review | STATUS now says “core packages; chunk_02 verified” not “all visual QA done” |
| Fail-closed protection | **A− for instrumented pages** | Green gates + goldens; not every page 27–47 |
| Risk of neighbor damage on next figure fix | **Lower than before, not zero** | Process + code both needed |

**Was it done correctly?**  
**Yes, as an implementation of the plan’s protective system and interim technical path.**  
**No, if “correct” means the entire pipeline now only ever extracts exclusive RO regions with no sugar and no strip fallbacks.** That deeper rearchitecture is still optional residual work.

---

## What you should do next

### Option A — Recommended: light human QA of chunk_02 only

You do **not** need to re-audit code. Spot-check the PDF vs `output/CEFR_Companion_Volume.md` for:

| Priority | Page | Confirm |
|----------|------|---------|
| 1 | **38–40** | Figures present; real prose around them; **no** garbage text under charts; p.40 order 8 then 9 then 10 |
| 2 | **47** | Fig 11, then **one** `### 3.1 RECEPTION`, then “Reception involves…”, no activity-title junk after |
| 3 | **27–29** | Callouts not mid-paragraph; title once on 29 |
| 4 | **32** | Blank line before page number line |

Search in the MD: `<!-- page:38 -->` (content is **above** that marker).

If those look good, **C2-ADJ for Chapter 2 chunk can be treated as accepted** for human QA.

### Option B — If you skip QA

Next **engineering** work (no need for you to design it):

1. Full-book inventory rebuild + re-extract so callout placement applies outside 26–50  
2. Agent crop QA for remaining bad PNGs (C2-F3)  
3. Optional: true multi-element figure RO (remove `figure_page` sugar)

### Option C — If QA finds a neighbor break

Report: **page number + what broke next to what you fixed**. That is exactly what C2-ADJ is for — and the gates should be extended if they missed it.

---

## Audit conclusion

The adjacent-element protection plan was **implemented substantially and correctly for its stated packages**, with **chunk_02 as the verified surface**, **validators green**, and **honest leftovers** (crops, full-book, optional RO purity). You can proceed to a **short visual check of the pages above**, or authorize the next backlog slice (full-book refresh / crops) without re-opening the whole plan.
