# User-found QA issues (resolved)

Source files ingested from repo root and deleted after resolution:
- `qa-user-found-issues.txt` (batch 1)
- `zz more issues.txt` (batch 2)

**Standing product lesson:** the automated PDF→MD pipeline got us to a **decent** markdown deliverable. **Near-perfect product MD** required a separate **Vision/PDF ↔ MD comparison pass** (page PNGs + human/agent judgment). Do not treat hard regression green alone as “finished book.” See **`PIPELINE_VS_VISION.md`**.

---

## Batch 1 — `qa-user-found-issues.txt`

### 1. Obsidian: table after HTML comment does not render

**User report:** In Obsidian Reading/Edit, a markdown table immediately after an HTML comment block does not render unless a blank line separates them.

**Fix:** Insert a blank line between `-->` and a following `|` table row, book-wide.

**Script:** `scripts/book_vision_qa/_fix_user_qa_issues.py` (`fix_comment_table_gap`)

**Count applied:** 26 sites (plus re-assert after later stitches).

**Prevention:** Always emit `\n\n` after HTML comments when the next block is a markdown table.

### 2. Figure 16 dual-emit leaf soup (p.129)

**User report:** Trash list **before** the real Figure 16 fence (dual-title + bare leaves).

**Why missed earlier:** Soup scanners only checked **post-fence** dual-emit. Pre-fence dump before `db:id=figure_*` was invisible to that pattern.

**Fix:** Strip dual-title + bare leaf list immediately before figure `db:id` / fence.

**Prevention:** Scan **window before** fence / `db:id=figure_*` for dual-word bold titles and 4+ consecutive bare leaf lines.

---

## Batch 2 — `zz more issues.txt`

### 3. Bare URL + footnote glue (Obsidian autolink)

**User report:** Links in parentheses followed by footnote markers caused Obsidian to eat the footnote (and sometimes intervening chars) into the URL:

```
intercultural education (https://rm.coe.int/16806ae621);5
…
democratic culture (https://go.coe.int/mWYUH).10
…bank-of-supplementary-descriptors)16
CEFR (https://rm.coe.int/168073ff31)”.19
```

**Fix:** Wrap URL in angle brackets inside parens: `(<https://…>);5` so autolink stops at `>`.

**Script:** `scripts/book_vision_qa/_fix_url_footnotes.py`

**Status:** User-listed examples clean; unwrapped `(url)+footnote` count = 0 in live MD.

**Prevention / gate:** After any URL sanitize, scan for `\((https?://[^)<]+)\)[.;”"']?\d{1,2}\b` and reject or auto-wrap. Related RIE-007 (glued multi-fn) is adjacent but different.

### 4. Figures 18–20: mermaid → PDF-cropped PNG

**User report:**
- Fig 18 flow wrong in mermaid (qualitative validation edges / Finalisation order); take PNG.
- Fig 19 take perfectly cropped PNG instead of mermaid.
- Fig 20 take PNG; list any other mermaids.

**Fix:** Crop from source PDF → `assets/figures/figure_{18,19,20}_*.png`; replace mermaid fences with `![…](assets/figures/…)`. Live mermaid count = **0**.

**Scripts:** `scripts/book_vision_qa/_figures_mermaid_to_png.py` (+ crop helpers).

**Other mermaids:** **None remaining** in live deliverable (only historical version snapshots still contain ```mermaid).

**Fig 18 correct visual flow (from PNG):** Qual. validation → Expert consultation (peer review) → Rework; Finalisation → Separate reference docs → Final updates → new collation. Do not re-author this as mermaid unless user asks.

### 5. Multipage tables: one full table, one db:id, no mid-page dups

**User report (core product requirement):**
- Tables that span pages must be **re-stitched** into continuity.
- Single `db:id` with the **full** level span is required for efficient grep / product use.
- Do **not** leave mid-page slices that **duplicate** parts already on the start page (user called out p.147-class failure).
- Do **not** drop prose, footnotes, or page markers between pages — park them intelligently on the mid page.
- Exception: first table on **page 16** (user-provided country tables) may stay split.
- Appendix 5 domain series is hard; if unsure, list for user help.
- Preserve blank line before tables after comments (batch 1).

**Why pipeline/Vision missed this class:**
1. Earlier “restores” pasted **page-slice** tables onto mid pages for page-parity while the start page already held a full (or upper) grid → **duplicate halves**.
2. Many scales were left as **high-only on start + low-only on next** (true PDF page break) without a merge step → **split without single id**.
3. Strip heuristics that required `prose_len < 200` **kept** mid tables when trailing section prose was long (p86/92/115).
4. Agents treated “table present on both pages” as OK page fidelity instead of **product continuity**.

**Fix applied:**
- Force-merge complementary high+low halves onto start page; strip mid-page table body for that scale only.
- Force-strip pure duplicate lower bands when start already has full levels.
- Self-assessment grid: full grid on p.177 only (prior `_stitch_self_assessment_one.py`).
- Continuity comments on mid pages for grep clarity.

**Scripts:**
- `scripts/book_vision_qa/_stitch_multipage_tables.py` (first pass strip)
- `scripts/book_vision_qa/_restitch_all_multipage.py` (merge + residual strip)
- `scripts/book_vision_qa/_stitch_self_assessment_one.py`

**Merged spans (full levels on start; mid table removed):**

| Start–end | Scale |
|-----------|--------|
| 54–55 | Reading correspondence |
| 55–56 | Reading for orientation |
| 56–57 | Reading for information and argument |
| 62–63 | Sustained monologue: describing experience |
| 65–66 | Addressing audiences |
| 73–74 | Conversation |
| 82–83 | Correspondence |
| 85–86 | Online conversation (start full; strip mid dup) |
| 86–87 | Goal-oriented online transactions |
| 88–89 | Co-operating |
| 91–92 | Overall mediation (start full; strip mid dup) |
| 106–107 | Personal response (start full; strip mid dup) |
| 107–108 | Analysis and criticism of creative texts |
| 114–115 | Facilitating pluricultural space (start full; strip mid dup) |
| 141–142 | Propositional precision |
| + prior continuity strips | 24–25, 94–95, 99–101, 103–104, 110–111, 119–120, 134–135, 146–148, 150–152, 154–156, 158–160, 162–163, 164–165, 168–169, 177–181, 183–185, 187–189, … |

**Prose kept on mid pages (examples):** p.86 goal-oriented intro + full goal table; p.92 §3.4.1.1; p.107 analysis intro + full analysis table; p.115 intermediary intro; p.87 interaction strategies; p.108 mediating concepts matrix; p.63 giving-information scale; p.89 asking-for-clarification; p.142 fluency, etc.

### 6. Needs user decision (not 100% auto-confidence)

| Item | Why |
|------|-----|
| **Appendix 5 domain examples (pp.191–241)** | Same scale titles repeat across pages with **different domain rows** (not level halves). Auto-merge would destroy domain structure. **Left as multipage domain series** with start-page `db:id` where present. If you want one mega-table per scale, that is a product decision — ask and we will stitch to that shape. |
| **Appendix 8 (non-linear levels)** | User noted order is intentional (additions/changes). Borders/PNG help; not force-merged beyond existing full tables. Spot-check if a specific scale still looks split. |
| **Page 16 country / institute tables** | Explicit exception (user-provided). |
| **Turntaking p.88 vs p.139** | Two **separate full** tables in different sections (not one span). Left both. |
| **Cosmetic el:start/end id mismatches** on some mid pages after strip (wrapper ids from earlier chrome restores). Non-blocking for grep; can clean later. |

---

## Status summary

| Issue | Status |
|-------|--------|
| Obsidian comment→table blank line | **resolved** |
| Fig 16 pre-fence leaf soup | **resolved** |
| URL + footnote Obsidian glue | **resolved** |
| Fig 18–20 PNG (no mermaid left) | **resolved** |
| Multipage descriptor scales → single full table | **resolved** (list above) |
| Appendix 5 domain multipage | **needs_user** if mega-table desired |
| Appendix 8 non-linear | **needs_user** only if a named scale looks wrong |
| Page 16 exception | **kept** per user |
# Append to USER_FOUND_ISSUES.md

## Batch 3 — live user review (through Appendix 3 / self-assessment)

**User emphasis:** PNG + Vision exists so formatting is verified, not only text presence. Callouts, headers, tables, and URL sanitization are finite element classes — miss one after hours is process failure.

### 7. URL sanitization (NOT Obsidian-only)

**User correction:** Glued footnotes/punctuation into URL tokens is a **sanitization** defect. Prior framing as “Obsidian render” was incomplete.

**Examples:**
- p.28 RLD cite + fn 22 (`))22` glue)
- p.29 fn 23 after Manual URL
- p.44 inline 34–35 after guide/pathway URLs
- Wrong relex PDF URL injected mid “Highlights from the Manual” title (p.29)
- Space inside bibliography URL (`search.coe.int/cm/ Pages/`)
- Mid-title URL split: `framework and (url) portfolios` (p.45)

**Fix rule:** Catalog every `https?://` token; peel footnote digits and closing punctuation out of the URL; prefer `(<url>).N` / `(<url>);N` for parenthetical + inline footnote. Rebuild wrong mid-title inserts from PDF/PNG.

**Artifacts:** `URL_CATALOG.md` (full page/status list), `URL_CATALOG_AND_FIXES.md`, script `_fix_user_round3.py`.

**Scan after fix:** 132 URL tokens, residual trail-digit/space flags = 0.

### 8. Callout formatting (Vision PNG ground truth)

| Page | Artifact | Was | Fixed to (from qa_snapshots PNG) |
|-----:|----------|-----|-----------------------------------|
| 29 | `callout_a_reminder_of_cefr_2001_chapters` | One italic soup string (+ wrong URL) | Bold title + Chapters 1–9 each on own line |
| 31 | `callout_p031_0` | 5 single-sentence blockquote lines | **2 paragraphs** (translanguaging; plurilingualism perspectives) |
| 37 | `callout_p037_0` | Bold header + 8 one-liners | Bold header + **2 paragraphs** |

**Prevention:** When Vision/PNG is available, log callout structure (title? N paragraphs? list lines?) in book_qa before declaring page done. Formatting is product content.

### 9. Merged section headers

**User:** p.121 `3.4.2.2. Strategies to simplify a text Amplifying a dense text` must be two lines; same pattern on `3.4.2.1. … Linking to previous knowledge`.

**Fix:** Split both bold headers. Book-wide scan for section-number + second title starting with Linking/Amplifying/… — only these two real cases on this book.

### 10. Table p.175 — 3 columns with user bands

**PNG:** Proficient user | C2/C1; Independent | B2/B1; Basic | A2/A1 — band label on first row of pair, blank first cell on second row (reader looks up).

**Was:** 2-col Level|Descriptor only.

**Fixed:** 3-col band|level|descriptor.

### 11. Self-assessment mediation p.180–181

**User:** Tables on 180 and 181 are one table — add **Mediating communication** column to the first mediation table; remove second table (no duplicate slices).

**Fixed on p.177:** single `| Level | Mediating a text | Mediating concepts | Mediating communication |` grid (content from PDF 180–181). Mid pages stay continuity-only.

---

## Status summary (all batches)

| Issue | Status |
|-------|--------|
| Comment→table blank line | resolved |
| Fig 16 pre-fence soup | resolved |
| URL+fn sanitization (book-wide catalog) | resolved (batch 3 reframe) |
| Fig 18–20 PNG | resolved |
| Multipage scale single db:id | resolved |
| Callouts p29/31/37 structure | resolved |
| Merged headers 3.4.2.1/2 | resolved |
| Table p175 3-col bands | resolved |
| Mediation self-assess one table | resolved |
| Appx5 domain mega-table | needs_user if wanted |


## Batch 4 — Appendix headers dropped on rotated multipage tables

**User report:** p.177 missing **Appendix 2** + subheader (SELF-ASSESSMENT GRID…). Same class on p.183 (**Appendix 3** QUALITATIVE FEATURES OF SPOKEN LANGUAGE (EXPANDED WITH PHONOLOGY)) and p.187 (**Appendix 4** WRITTEN ASSESSMENT GRID). Likely from earlier rotated-page vision that cropped tightly to the table and never reattached the appendix chrome.

**Pattern / prevention:** When injecting rotated table vision (`rotated_from_grok`), always re-check the full-page PNG for:
1. `Appendix N` line
2. Bold ALL-CAPS (or title-case) appendix subheader above the table
Appendix 1 (p.173) is the reference form: prose `Appendix 1` + `**SALIENT FEATURES…**` then body.

**Fix:**
- p.177: restored Appendix 2 + SELF-ASSESSMENT GRID subheader
- p.183: restored Appendix 3 + QUALITATIVE FEATURES…; renamed artifact `scale_phonology` → `table_qualitative_features_of_spoken_language_expanded_with_phonology` (alias `scale_phonology` kept for inventory)
- p.187: restored Appendix 4 + WRITTEN ASSESSMENT GRID; renamed `scale_argument` → `table_written_assessment_grid` (alias `scale_argument` kept)

**Callout catalogue:** yes — `work/cefr-companion-2020/metadata/book_qa/CALLOUT_CATALOG.md` (page, id, title, structure), parallel to `URL_CATALOG.md`.


## Batch 5 — Appendix 5 stitch (user decision)

**User input:** Appendix 5 domain examples may be stitched. Spanning cell **Situation (and roles)** need not be a merged MD cell; state once as prose (p.191). Keep four domain columns. Keep scale names as column headers *and* add inline prose when the activity type changes under each umbrella (Online interaction → Mediating a text → Mediating concepts → Mediating communication), because the PDF under-delineates table groups. Improving on PDF guidance is OK here.

**What we did:**
- Merged each scale’s multipage level slices into **one full table** on the scale’s start page (20 scales, pages 191–241).
- p.191: Appendix 5 chrome + intro + **Situation (and roles)** note for Personal/Public/Occupational/Educational.
- Section prose: Online interaction / Mediating a text / Mediating concepts / Mediating communication.
- Scale-shift blurbs (e.g. conversation → goal-oriented; speech/sign → writing variants).
- Mid-page PDF slices → `table-continuity` notes (no duplicate partial tables).
- Stable ids: `table_app5_<slug>` with `pages=start-end`.

**Script / log:** `scripts/book_vision_qa/_stitch_appendix5.py`, `work/.../book_qa/APPENDIX5_STITCH.md`.

**Not claiming perfect:** cell text is as previously restored from rotated_from_grok; user may still spot domain-cell OCR issues while reviewing Appendix 5.



## Batch 6 — Figures 18–20 crops, p248 callout, p253 list, Appendix 7 markup

**User (App 5 approved; continuing App 6–7):**
- Fig 18 crop was terrible; crops must exclude figure caption text and adjacent prose (Figs 18, 19, 20).
- p.248 callout missing bold header **The Rasch Model**.
- p.253 list numbering broken between Sociolinguistic and Pragmatic groups (must be 1–9 continuous).
- Appendix 7: show PDF strikeouts with ~~double tilde~~; added (red) text with _italics_; instructions before the table.
- List which PNGs reused vs created recently.

**Fixes:**
- Re-cropped Figs 18–20 from source.pdf via PyMuPDF (diagram-only boxes; caption excluded). Fullpage refs retained.
- p248: callout_the_rasch_model with **The Rasch Model**.
- p253: Linguistic 1–2, Sociolinguistic 3, Pragmatic 4–9.
- App 7: instructions + full strike/add table; id `table_appendix_7_substantive_changes_2001`.
- Logs: `FIGURE_PNG_INVENTORY.md`, refreshed `CALLOUT_CATALOG.md` (11 callouts).



## Batch 7 — Figure 19 top borders

**User:** Figure 19 missing top 2 borders (Preparatory work + Consultation & Piloting).

**Fix:** Re-cropped `figure_19_multimethod_research_design.png` from source.pdf so both top column outer frames are complete; caption text excluded from PNG.

**Soft mid-page flags (57, 74, 83, 87, 169):** still present as of regression — not product defects. Inventory still expects per-PDF-page tables that we intentionally merged onto start pages (one `db:id` / full grid). Hard remains 0. Optional future work: update soft inventory golden markers for those mid pages.



## Book complete — user confirmation (2026-07-31)

**User:** Rest of appendices good. **This PDF is done; confirmed.**

Deliverable: `output/cefr-companion-2020/CEFR_Companion_Volume.md`  
Approved: see `APPROVED.json` (latest version after Fig 19 top-border fix / soft mid-page notes).

Do **not** reopen companion book QA unless user files a new defect.

