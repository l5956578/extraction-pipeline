# Project status — CEFR Companion Volume extraction pipeline

**Canonical status document.**  
Any human or coding agent starting work **must read this file first.**

### Standing rule — log everything the user writes

When the user files feedback (`user debug/log*.txt`, chat, screenshots, rants, suggestions):

1. **Log all of it** in the issues/diagnosis docs and, where ongoing, here in STATUS.
2. Do **not** drop text because it is not a “bug,” not technical, emotional, or process-level.
3. Use categories that fit the content: **defect**, **product requirement**, **process/policy**, **design direction**, **validation expectation**, **trust/claims**, **effort/priority signal**.
4. Bug IDs are for defects only. Non-defect concerns get their own section (see §5a and `docs/ISSUES_CHAPTER2_DIAGNOSIS.md` “User voice”).
5. Prefer the user’s words and intent over agent-friendly paraphrases that erase meaning.

### Standing rule — resolved-issue re-apply (agent memory)

When a new extraction bug looks like something already fixed on another page:

1. **Investigate first** (MD + PDF/snapshot). Do not ask the user to recall prior fixes.
2. Match and re-apply using **[`docs/RESOLVED_EXTRACTION_ISSUES.md`](docs/RESOLVED_EXTRACTION_ISSUES.md)** per **[`docs/RESOLVED_ISSUE_MATCH_PROTOCOL.md`](docs/RESOLVED_ISSUE_MATCH_PROTOCOL.md)**.
3. **CLEAR** → auto-apply + report; **AMBIGUOUS** → short ask; **NOVEL** → fix then append a RIE entry.

This file (`STATUS.md`) remains the **open / partial / fixed status** SoT. The RIE ledger is only the **re-apply playbook** for known-good fixes.

| | |
|--|--|
| **Last updated** | 2026-07-27 (Phase B: JobContext split, `--job` required, layout SoT JSON) |
| **Branch** | `master` |
| **Active job** | `cefr-companion-2020` (`--job` **required** on all CLIs — no silent default) |
| **Deliverable** | `output/cefr-companion-2020/CEFR_Companion_Volume.md` (~977 KB, pages 1–278) |
| **Source PDF** | `input/cefr-companion-2020/source.pdf` (original name: `CEFR Companion Volume_eng.pdf`) |
| **Sidecars** | `input/cefr-companion-2020/job.json`, `profiles/cefr_companion.json` |
| **Deliverables** | `output/<job-id>/` — MD + assets + registries |

---

## 1. Purpose

Extract the full CEFR Companion Volume PDF into **database-ready Markdown** suitable for website import / SQLite ETL (descriptor scales, prose, figures, footnotes, page anchors).

---

## 2. Current system state (summary)

| Area | State |
|------|--------|
| End-to-end pipeline (spans → inventory → extract → cleanup → merge → figures → format) | **Operational** |
| Normal prose / tables / TOC / figures | **Working** (with known residual quality issues) |
| Rotated tables (all inventory-flagged pages) | **Personal deep-audit complete** — **88** pages; 0 pending; 0 geometry fallback |
| Appendix 5 domain examples (pp. 191–241) | **Done** — personal multi-pass; log: `work/cefr-companion-2020/metadata/rotated_from_grok/_DEEP_AUDIT_LOG.txt` |
| Non–Appx5 rotated scales (37 pages) | **Done** — personal multi-pass; log: `work/cefr-companion-2020/metadata/rotated_from_grok/_DEEP_AUDIT_LOG_NON_APPX5.txt`; rewrites: 104, 113, 119, 154, 162 |
| Formatting postprocess | **Integrated** into merge / `iterate_format.py` (~4s) |
| Isolated smoke harness | `../attempt4_rotation_smoke_test/` (historical; main is source of truth) |

---

## 3. Architecture (quick map)

```
PDF (input/<job-id>/source.pdf)
 → spans (span_detector)
 → inventories (work/<job-id>/inventories — reading_order per page)
 → extract_chunk (prose_zone | pdfplumber | rotated agent-vision | multipage)
 → cleanup (chunk-level rules)
 → merge → apply_figures → post_process
 → output/<job-id>/CEFR_Companion_Volume.md   # Companion job markdown name
```

**Multi-job layout (Phase B):** every document is a **job** under `input|work|output/<job-id>/`.  
Shared engine: `pipeline/` + `profiles/*.json`. Per-PDF knowledge: `input/<job-id>/job.json` (layout SoT) + inventories.  
Load via `pipeline.bootstrap.bootstrap_job` / `load_job(job_id)` — **no import-time auto-load**. Paths: `import pipeline.config as cfg` then `cfg.PDF_PATH` (not frozen name imports).

**Contract:** `work/<job-id>/inventories/*_inventory.json` → `reading_order` is the extraction source of truth.

**Rotated tables (default method `grok_vision`):**

1. `prepare_rotated_for_grok.py` → PNG/JSON/handoff in `work/<job-id>/metadata/rotated_for_grok/`
2. **Coding agent** (multimodal vision) writes `work/<job-id>/metadata/rotated_from_grok/{slug}.md`
3. Extract assembles those files; **if missing** → geometry fallback + `AGENT_VISION_PENDING` HTML comment

Chat/web Grok is **not** a pipeline step. Geometry/OCR are **fallback only**.

Detailed design: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).  
Code-quality audit log: [`docs/reviews/`](docs/reviews/) (e.g. Phase A review 2026-07-27).

---

## 4. Work completed (recent cycle, 2026-07-13 → 2026-07-14)

### 4.1 Rotated table extraction (agent vision)

| Item | Detail |
|------|--------|
| Decision | Geometry + OCR + chat-draft markdown **unreliable** for rotated CEFR scales |
| Port | Smoke-test approach ported to **main** `agent-extraction/` |
| Implementation | `pipeline/extractors/rotated_grok_vision.py`, prepare/finalize CLIs, inventory default `grok_vision` |
| Completed vision tables | **37 pages** — all non–Appendix 5 rotated scales (see §6) |
| Footnotes on rotated pages | Geometry surgical path (`rotated_footnote_zone`), e.g. footnote 46 |

### 4.2 Layout / formatting fixes (code)

| Issue | Root cause | Resolution |
|-------|------------|------------|
| Duplicate `<!-- page:N -->` | `rich_page` emitted footer **and** inventory footer | Body-only rich extract; dedupe in cleanup/postprocess |
| Soft-wrap lists with blank rows | Soft wraps treated as paragraphs | `_repair_list_blocks` + extract join |
| 4 paragraphs where PDF has 2 (e.g. p.22) | Capital-after-period heuristics | **y-gap** join (`_PARAGRAPH_Y_GAP ≈ 15pt`) in `page_layout` |
| Section + prose + table title one line (p.24) | `prose_zone` `_format_rows` ignored structure/y-gap | Section/table-title blocks + y-gap in `descriptor_layout` |
| Footer `3` instead of `▶` | Dingbat font `FFDingbats-ArrowsOne` encodes arrow as ASCII `3` | Dingbat map in `_span_text` + format safety net |
| Inline `f **Guide…**` bullets | Wingdings `f` + join without list detection | Bullet regex + structural list lines |
| Fn20 / Introduction dup on p.25 | Trailing prose bbox included footnote band | `first_footer_band_y`; prose stops above footnotes |
| `Page **N**` glued to footnotes | Bold page tokens not split | Detach trailing page; caption **before** HTML comment |
| OCR thrash on large spans | Geometry fallback forced OCR per page | Prefer pdfplumber reverse; OCR only if forced/no tables |

### 4.3 Tooling

| Tool | Role |
|------|------|
| `run_pipeline.py` | Full/step orchestrator (`--step prepare_rotated`, `postprocess`, …) |
| `run_production_extract.py` | Full extract → cleanup → merge → figures → format |
| `iterate_format.py` | **Fast** format-only (~4s) for MD polish iteration |
| `prepare_rotated_for_grok.py` | Crop all rotated table PNGs |
| `finalize_after_grok.py` | Re-extract after vision `.md` lands |

### 4.4 Full-book re-run (2026-07-14)

- Rebuilt spans + inventories (10 chunks)
- Agent vision for 37 non–Appendix 5 rotated pages
- Full extract of chunks 01–10 + cleanup + merge + figures + postprocess
- Deliverable refreshed: `output/cefr-companion-2020/CEFR_Companion_Volume.md` (path at time of work: flat `output/`; now job-namespaced)

### 4.5 Full-book re-run (2026-07-19) — chunk_02 fixes → whole document

**Why:** Propagate C2-ADJ / log 05–06 quality work (callouts, figures, URL sanitize, soup strip, fences) beyond chunk_02.

**Steps run (did not re-author rotated vision):**
1. `spans` → `chunks` → `inventory` (10 inventories rebuilt)
2. `run_production_extract.py`: extract all chunks → cleanup → merge → figures → postprocess
3. Gates: `adjacent_guard` green; `contract_validators` green

**Rotated tables protection:**
- Pre-run snapshot: **88** `work/cefr-companion-2020/metadata/rotated_from_grok/page_*.md` files (fp `a775bdc69156cb9a`)
- Post-run: same count + fingerprint **unchanged**
- Final MD: `AGENT_VISION_PENDING=0`, `geometry_fallback=0`, sign-language scale id present
- Did **not** re-run `prepare_rotated` or overwrite vision `.md`

**Result:** 278 unique page markers; el fences present book-wide; 9 PNG figure assets re-applied; deliverable ~1.0 MB.

---

## 5. Open work (prioritized backlog)

Statuses: **blocker** | **major** | **minor** | **debt**

### P0 — Rotated tables remaining

| ID | Item | Priority | Notes |
|----|------|----------|-------|
| R1 | ~~Appendix 5 agent vision~~ | **resolved** | 51 pages written 2026-07-14; finalize re-extracted chunk_08 et al. |
| R2 | ~~Appendix 5 personal multi-pass deep-audit~~ | **resolved** | Coding agent personally vision-audited all 51 Appx5 pages (same bar as 146–148). Log: `work/cefr-companion-2020/metadata/rotated_from_grok/_DEEP_AUDIT_LOG.txt`. Structural rewrite p.191; 192–197 rewritten; 198–241 verified match PNG. chunk_08 re-extract + figures + postprocess; PENDING=0, geometry_fallback=0. |
| R3 | Reversed/garbled `span_group_id` / display titles in inventory (e.g. `noitacilbup`) | **improved (final MD)** / debt in inventory | **Final MD:** re-derive id from fixed ### / table title (`title_fix` + `_resync_artifact_ids_from_fixed_titles`, RIE-005). Inventory JSON may still hold old tokens until re-extract — **not** fixed by rebuild alone |

### P1 — Output quality (non-rotated)

| ID | Item | Priority | Notes |
|----|------|----------|-------|
| Q1 | Figure 11 (and similar) missing `### Figure N – … \| id` caption line after `db:id` | major | Historical B2; validate against PDF |
| Q2 | Validator false confidence (narrow gates) | major | Expand gates for rotated completeness, fn ownership, figure captions |
| Q3 | Residual bold glitches (`** word **`, soft-hyphen artifacts) | minor | Ongoing postprocess/OCR typo pass |
| Q4 | Second artifact id / registry duplicates for some scales | major | Historical C4; confirm after full re-run |
| Q5 | Inline footnote callouts (e.g. `…schools”,20`) vs full footnote block | minor | PDF style; may be acceptable |

### P0 — Chapter 2 QA cluster (systemic; see `docs/ISSUES_CHAPTER2_DIAGNOSIS.md`)

Source: `user debug/log 01–06` (log **06** visual pass 2026-07-19).

| ID | Item | Status | Notes |
|----|------|--------|-------|
| C2-F1/F2 | Figure soup / multi-fig / inject | **partial** | Soup strip + gates. A2 sample table with Level/Illustrative Descriptors headers (log 04 #7.6) |
| C2-F3 | Figure PNG crops wrong | **improved — multipass; needs user confirm** | Multipass crops for figs **2–10** as PNG (user: 9–10 are PNGs not tables). Full-page fallback reverted. **Do not mark resolved** until user confirms |
| L06-FN21 | p.27 fn21 URL split (`…2fb` / `1.`) | **fixed** | Rejoin trailing hex digit onto ObjectId |
| L06-SEC | p.36/38 section titles glued to prior para | **fixed** | `### 2.6…` / `### 2.7…` on own lines (2nd report of 2.7 addressed) |
| L06-HY | situationspecific | **fixed** | situation-specific |
| L06-P41 | p.41 callout bottom garbage | **fixed (format)** | Progressive-band dups replaced with clean 3-phase blockquote from full textbox |
| L05-P27-SPLIT | p.27 prose fence splits mid-sentence | **fixed (format)** | Joined mid-sentence fence; `social cohesion…` continuous. Gate: verify string in final MD |
| L05-P27-CO | p.27 callout 3 paras not 1 | **fixed (format)** | User’s 3-block split applied; callout_detect also forces known split on re-extract |
| L05-PAGE-AST | Page caption `*` split onto own line | **fixed (format)** | Root cause: `_ensure_blank_before_page_captions` split `*Page`. Fixed + rejoin. Chapter-2 odd pages use `*Key aspects… ▶ Page **N***` form |
| L05-P29-CH | p.29 chapter reminder soft-wrap splits | **fixed (format)** | Soft-wraps rejoined (Ch 4/8 complete). Ch 1 still has a stray annotation URL on the title line (pre-existing link attach — not closed as perfect) |
| L05-FN-GLUE | Footnotes glued after URL sanitize | **fixed (priority)** | `sanitize_urls_in_text` + `repair_glued_footnotes`: fn 23–26 on separate lines. adjacent_guard + contract_validators green |
| L05-P32-LINK | Guide URL placement wrong | **fixed** | URL no longer after “language classroom”; attached after Guide title. V-LINK-GUIDE green |
| L05-P33-HY | problemsolving → problem-solving | **fixed** | `fix_ocr_typos` |
| L05-P35-CO | p.35 Can-do callout 2 paras | **fixed (format)** | Split after “achievement.” |
| L05-P37 | p.37 Level C2 break; list glue; callout title | **fixed (format)** | Level C2 on own para; list after beginners:; title **Background to the CEFR levels** |
| L05-P38-A2 | p.38 A2 as table not prose | **fixed (priority)** | User’s markdown table; prose form removed. Blank before “Plus levels” |
| L05-P41-URL | p.41 Section 3.7 missing URL | **fixed** | Parenthetical `https://rm.coe.int/1680459f97#page=36` after Section 3.7 |
| L05-P41-CO | p.41 callout mid-flow when no multi-col | **fixed (log 07)** | Inline when no side-column + full-width box; top full-width stays first (p.43). RO rebuild chunk_02 + extract |
| L07-P42-CO | p.42 callout steps lost formatting | **fixed (format)** | Step 1–4 expanded; title bolded |
| L07-P43 | p.43 top callout + lead prose + list glue | **fixed (partial→strong)** | top_fullwidth placement; Very often lead restored; Step callout format; FN 1/2 split |
| L07-P38-SOUP | p.38 duplicate A2 under fig 6 | **fixed** | Deduped sample table under PNG |
| L07-P90-SOUP | p.90 mediation label soup after text diagram | **fixed (format)** | Stripped flattened dual-emit after ``` fence |
| L07-ID | garbled scale ids (cfiiceps, smargaid, gnittup, cilbup, ni…) | **fixed (final MD)** | Re-derive artifact_id from fixed title/table title (RIE-005); token maps; emit-time re-slug. Inventory may lag until re-extract |
| L07-TABLE-BLANK | blank line before MD tables | **fixed (format)** | postprocess inserts blank after ### / el:start before `\|` |
| L07-ODD-CAPTION | Odd-page running head collapsed to bare `Page **N**` | **fixed** | Root: `_normalize_page_marker_caption` failed on `Page **29**` bold digits; fixed + `_resync_page_captions_from_pdf`. Process failure: Vision QA skipped p.29 despite log 07 — skill/AGENTS now **forbid** skipping user-named pages |
| L07-ID-REBUILD | Claim that inventory rebuild fixes garbled slugs | **false — do not claim** | Inventory after full rebuild still had `cfiiceps`; fix requires re-slug + vision alias, not rebuild alone |
| C2-L1 | Mid-line dingbat list glue | **resolved** | postprocess mid-line split (not re-reported in log 03) |
| C2-H1 | Inline hyperlinks without footnotes | **partial** | Multi-rect merge + known Guide/CARAP titles; parenthetical URLs attach when title in prose. Gate V-LINK-GUIDE green after chunk_02. Spot-check remaining pages later |
| C2-U1 | Broken URLs (spaces inside URLs) | **partial** | `sanitize_urls_in_text` + V-URL-SPACE. **log 05:** also no longer glues next footnote (`…a2d.24.ALTE` fixed). Keep gate on every merge |
| C2-T1 | Table 3 mis-id as scale | **resolved** | `table_03_…` (not re-reported) |
| C2-T2 | Callout as scale / wrong type | **partial** | Inventory types p.29/p.35 as `callout` via KNOWN_TABLES_BY_INDEX; extract emits blockquote |
| C2-CO1 | Callout / sidebar format standard | **improved** | Blue-fill path in RO book-wide (inventories rebuilt). Chunks 03–09 re-extracted 2026-07-16. Residual QA possible |
| C2-CO2 | p.30 plurilingual callout incomplete | **resolved** | **User confirmed 2026-07-16:** p.30–31 appear resolved. Full 4-para blockquote from blue fills; lead not list-glued. Gate V-CALLOUT-LEAD |
| C2-L2 | Missing methodological prose p.29 | **resolved** | present (not re-reported as missing in log 03) |
| C2-T3 | Table cell `<br>` policy | **improved** | Phrase heuristic: lowercase continuation → space; capital new line → `<br>` (Table 4 Turntaking/Co-operating etc.). User can still flag residual cells |
| C2-T4 | Small level tables as prose | **resolved** | not re-reported in log 03 |
| C2-T4b | Table 4 id/title | **resolved** | id ok; content breaks → C2-T3 |
| C2-P1/P2 | False para splits; heading glue | **partial** | residual possible |
| C2-R1 | Misplaced multi-column / callout prose | **resolved (chunk_02 / p.30–31)** | **User confirmed 2026-07-16:** p.30–31 appear resolved. Blue-fill RO + V-ORDER-31. Propagate same path on full-book re-run (Phase 5) |
| C2-G1 | Empty / junk table artifacts | **partial** | `table_to_markdown` suppresses empty tables; V-EMPTY-TABLE gate. Green after re-run |
| C2-V1 | Validation gaps | **partial** | **`pipeline/contract_validators.py`** fail-closed; wired in `merge_output`. Green on current deliverable. Expand as more golden pages land |
| C2-ADJ | Adjacent-element damage on fix | **done (core packages; chunk_02 verified)** | **Plan:** `docs/plans/2026-07-17_adjacent_element_protection_plan.md`. **Status log:** `docs/ADJACENT_ELEMENT_PROTECTION.md`. Shipped: el fences (assembly markers, retained in MD), selective exclusive crop filter (drop labels, keep prose), soup strip for level/language rows, callout placement (top-left / end-body), fence-aware postprocess, goldens incl. p.39–40. Not “structurally impossible dual-emit” for every multi-fig edge — gates fail closed on known residual classes. Leftover: agent crop QA (C2-F3), optional multi-element figure RO, **full-book inventory rebuild + re-extract** for callout placement outside chunk_02 |

### 5a. User voice / non-defect concerns (log 03 and ongoing)

These are **not** optional commentary. They are logged requirements, policy, and design direction. Full prose: `docs/ISSUES_CHAPTER2_DIAGNOSIS.md` § “User voice (log 03)”.

| ID | Kind | What the user asked for / stated | Status |
|----|------|----------------------------------|--------|
| UV-01 | **Product** | Callouts/sidebars/feature boxes (blue-background): standard markdown blockquote form with title in the quote, blank `>` between paragraphs, preserve internal formatting, apply to **all** such boxes in the document | open |
| UV-02 | **Product / naming** | User does not own the code name (“callout”); agents must confirm terminology and still treat the visual element consistently | open |
| UV-03 | **Process** | User should not have to find URL breaks, missing callout leads, figure trash, etc.; **validation** must catch regressions after a claimed fix | open (→ C2-V1) |
| UV-04 | **Process / trust** | Do not mark issues fixed when they are not; prior “resolved” claims for p.30 callout and p.31 order were wrong from the user’s view | open |
| UV-05 | **Design** | Stop brittle, isolated patches that fight inventory→extract→assembly; prefer structure that matches the pipeline contract | open (→ E5) |
| UV-06 | **Design / method** | When geometry/code is unreliable (callout bounds, figure crops, phrase-level `<br>`), **use agent-in-the-loop / multimodal judgment** rather than more fragile heuristics alone; user offered blue-background detection + agent loop — do not ignore | open |
| UV-07 | **Consistency** | Same class of layout (e.g. top-left callout + multi-column prose) must work the same on p.31 as on p.35 — not spot-fixed one page | improved on p.30–31/35 (user OK on 30–31); still open document-wide |
| UV-08 | **Contract** | Agents claimed to understand inventory→extract→assembly yet output shows they did not honor it; contract is binding for all figure/table/callout/span work | open (→ E5) |
| UV-09 | **Scope of care** | Dropped/misplaced content around figures, tables, multipage spans, rotated tables is a **serious recurring class of problem**, not a series of one-offs | open |
| UV-10 | **Effort signal** | High-effort mode: do not skip hard items (e.g. p.30/p.31) while “fixing” easier pages; do not burn the user’s tokens without addressing what they spelled out | standing expectation |
| UV-11 | **Table semantics** | `<br>` in cells is for phrases that “go together” as separate units; markdown soft-wrap is fine for long lines; extra space in the PDF may signal phrase breaks — if code cannot see that, use intelligence/loop, not wrong `<br>` everywhere | open (→ C2-T3) |
| UV-12 | **Figure assets** | Finite number of figures; crops must be correct (full diagram); “there aren’t 500 images” — invest in getting each right (loop or better method) | open (→ C2-F3) |
| UV-13 | **Regression caution** | When fixing figures on p.36, **do not break prose that is finally working** | standing constraint |

### P2 — Process / engineering debt

| ID | Item | Priority | Notes |
|----|------|----------|-------|
| E1 | Optional: drop geometry fallback once Appendix 5 vision complete | debt | Or keep as safety net with loud markers |
| E2 | Smoke-test folder vs main drift | debt | Prefer main; smoke is historical prototype |
| E3 | Garbled artifact ids from reversed PDF titles | debt | Fix at span_detector / title_fix |
| E4 | Master branch not merged with execute-plan work | debt | Repo process |
| E5 | inventory→extract→assembly contract drift | major | Hardening started 2026-07-16. Adjacent-damage meta-bug tracked as **C2-ADJ** → `docs/ADJACENT_ELEMENT_PROTECTION.md`. Residual dual layouts still open |

### Resolved (do not re-open without new evidence)

| ID | Item |
|----|------|
| ~~A1~~ | Table 2 p.25 trailing prose scheduled |
| ~~B3~~ (as of 2026-07-14 full run) | Consecutive duplicate page markers: **0** on last full postprocess metrics |
| ~~C2~~ (descriptor scales excl. Appx 5) | Rotated body via agent vision, not gibberish |
| ~~p.22 para split~~ | y-gap paragraph join |
| ~~p.24 section/table glue~~ | prose_zone structure |
| ~~Footer `3` vs `▶`~~ | dingbat map |
| ~~p.25 fn20 double from prose+footer band~~ | footer band ownership |

---

## 6. Rotated table inventory (authoritative method)

### Agent vision complete (`work/cefr-companion-2020/metadata/rotated_from_grok/`, 37 files)

| Pages | Scale / artifact (group id may be garbled) |
|-------|-----------------------------------------------|
| 94–95 | Relaying specific information |
| 97 | Explaining data (graphs, etc.) |
| 99–101 | Processing text |
| 103–104 | Translating a written text |
| 110–111 | Collaborating in a group |
| 113 | Leading group work |
| 119–120 | Strategies to explain a new concept |
| 122 | Strategies to simplify a text |
| 134–135 | Phonological control |
| **146–148** | **Sign language repertoire** |
| **150–152** | **Diagrammatical accuracy** |
| 154–156 | Sociolinguistic / cultural repertoire |
| 158–160 | Sign text structure |
| 162–163 | Setting and perspectives |
| 175 | Proficient user / global |
| 183–185 | Phonology (qualitative features) |
| 187–189 | Argument / written assessment criteria |

### Appendix 5 personal multi-pass deep-audit complete

| Pages | Item |
|-------|------|
| **191–241** | Domain examples (`appendix_5_domain_examples`) — **51** `.md` files; **personal** vision audit (not batch/subagent-only) |

**Standard:** same as pages 146–148 — coding agent multi-pass: read PNG with vision → rewrite or verify MD → re-check structure (level bands, multi-can `<br>` cells, blank domains, `[not applicable]`, split domain rows).

**Audit log:** `work/cefr-companion-2020/metadata/rotated_from_grok/_DEEP_AUDIT_LOG.txt`

PNG prep for all **88** rotated pages: `work/cefr-companion-2020/metadata/rotated_for_grok/`.  
Vision markdown for all **88**: `work/cefr-companion-2020/metadata/rotated_from_grok/`. **Pending: 0. Geometry fallback in final: 0.**

---

## 7. Chunk map

| Chunk | PDF pages |
|-------|-----------|
| chunk_01 | 1–25 |
| chunk_02 | 26–50 |
| chunk_03 | 51–75 |
| chunk_04 | 76–100 |
| chunk_05 | 101–125 |
| chunk_06 | 126–150 |
| chunk_07 | 151–175 |
| chunk_08 | 176–241 (includes Appendix 5) |
| chunk_09 | 242–266 |
| chunk_10 | 267–278 |

---

## 8. Operator runbook

### Full rebuild (slow: minutes–tens of minutes)

Default job is `cefr-companion-2020` when `--job` is omitted (Phase A). Paths below use that job id.

```bash
python run_pipeline.py --job cefr-companion-2020 --step spans
python run_pipeline.py --job cefr-companion-2020 --step inventory
python prepare_rotated_for_grok.py --job cefr-companion-2020
# Agent: vision-write any missing work/cefr-companion-2020/metadata/rotated_from_grok/*.md
python -u run_production_extract.py --job cefr-companion-2020
```

### Format-only iteration (fast: ~4s)

```bash
python iterate_format.py --job cefr-companion-2020
# or: python run_pipeline.py --job cefr-companion-2020 --step postprocess
```

### After adding rotated vision markdown

```bash
python finalize_after_grok.py --job cefr-companion-2020
# or re-extract affected chunks only, then merge + postprocess
```

---

## 9. Documentation map (what to read)

| Document | Role |
|----------|------|
| **`STATUS.md` (this file)** | **Single source of truth** — done / open / how to run |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Pipeline design & contracts |
| [`README.md`](README.md) | Quick start |
| [`work/cefr-companion-2020/metadata/ROTATED_TABLES_AGENT_VISION.md`](work/cefr-companion-2020/metadata/ROTATED_TABLES_AGENT_VISION.md) | Rotated vision procedure |
| [`work/cefr-companion-2020/metadata/figures_handling.md`](work/cefr-companion-2020/metadata/figures_handling.md) | Figure render policy |
| [`work/cefr-companion-2020/metadata/sqlite_schema_notes.md`](work/cefr-companion-2020/metadata/sqlite_schema_notes.md) | Downstream DB notes |
| [`docs/archive/`](docs/archive/) | **Historical only** — attempts 2–4 debug logs, old plans |

**Deprecated as source of truth:** `docs/archive/EXTRACTION_DEBUG_HISTORY.md` (history preserved; open bugs rolled into §5 here).

---

## 10. Recommended next actions

1. User PDF QA pass on final MD if desired.
2. Validator hardening (Q2).
3. Figure caption headers (Q1) if product requires them.
4. Optional: tighten garbled span IDs (R3).

---

## 11. Change log (high level)

| Date | Event |
|------|--------|
| 2026-07-14 | Non–Appx5 **personal multi-pass deep-audit** (37 pages); rewrites 104/113/119/154/162; chunk_05+07 re-extract |
| 2026-07-14 | Appendix 5 **personal multi-pass deep-audit** (191–241); chunk_08 re-extract; figures+postprocess; PENDING=0 |
| 2026-07-14 | Appendix 5 agent vision (51 pages) + finalize; **all 88** rotated pages vision-complete |
| 2026-07-14 | Full-book re-inventory + extract; agent vision for 37 non-Appx5 scales; STATUS/docs restructure |
| 2026-07-13–14 | Formatting/layout fixes; agent vision port; dingbat/bullet/footer-band fixes |
| 2026-07 | Attempt 4 smoke test (isolated) for rotated tables |
| earlier | Attempts 1–3: spans, inventory contract, figures, validators |
