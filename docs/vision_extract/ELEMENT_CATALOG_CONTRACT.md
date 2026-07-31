# Element catalog contract — Threshold / Waystage / CEFR 2001

**Purpose:** Prevent mechanical regressions (dup tables, failed stitches, wrong page numbers, tone mark collisions).  
**Rule:** Before claiming a book “done”, run checklist against this file. Do **not** ask the human to re-discover these classes.

## Document page numbers (binding)

Product MD must use **printed document page numbers**, not PDF file indices.

| Job | Front matter | Arabic p.1 starts at PDF leaf | Formula (body) |
|-----|--------------|-------------------------------|----------------|
| cefr-en-2001 | title, contents, prefatory, notes, synopsis (no Arabic) | PDF **10** = doc **1** | `doc = pdf - 9` |
| cefr-threshold-1990 | half-title… TOC (roman) | PDF **7** = doc **1** (Preface) | `doc = pdf - 6` |
| cefr-waystage-1990 | half-title… TOC (roman) | PDF **7** = doc **1** (Preface) | `doc = pdf - 6` |

Markers: `<!-- page:{doc} -->` and visible `*Page **{doc}***` (or running-head form).  
Never show PDF leaf numbers as page numbers.

## Element classes (inventory every book)

| Class | Must check | Failure modes |
|-------|------------|---------------|
| `multipage_table` | One full grid + one `db:id`; mid pages = continuity chrome only | Half table on start page **and** again on continue page (dup) |
| `vertical_band_table` | Left vertical band becomes first column (UNDERSTANDING / SPEAKING / WRITING) | Vertical text ignored or spelled letter-by-letter |
| `rotated_table` | Companion path or PNG | Prose soup of cells |
| `figure_tree` | Cropped PNG under `assets/figures/` if text diagram fails | Bad spacing text-diagram pretending to be figure |
| `intonation_exponents` | Unicode tone inventory only (see docs/vision_extract/INTONATION_NOTATION.md) | ASCII `'` used as tone (collides with contractions) |
| `section_header_numbered` | `### 1 Target Group` not `1. list item` | Numbered headers parsed as lists |
| `emdash_emphasis` | Inline `– and many more –` | False bullets |
| `two_column_list` | Multi-pass Vision; reading order left then right or by number | Cut mid-sentence / half page missing |
| `toc` | Table with document page column | Soup single line |

## Multipage stitch rule (RIE-010)

1. Emit **full** table once on **start** document page.  
2. Continuation pages: `<!-- table-continuity: full grid on page N db:id=… -->` only — **no second half of cells**.  
3. Single `db:id` spans all pages.

## Vertical band rule (Table 2 class)

Columns: `| Mode | Skill | A1 | A2 | B1 | B2 | C1 | C2 |`  
Mode values: UNDERSTANDING (Listening, Reading); SPEAKING (Spoken Interaction, Spoken Production); WRITING (Writing).

## Intonation pages (must multi-pass Vision ≥3)

Catalog paths: `docs/vision_extract/INTONATION_PAGE_INDEX.md`  
Any page with nuclear tone exponents: re-read PNG, re-check MD marks vs App A legend.

## QA checklist (agent, not human)

- [ ] Page markers = document pages (spot-check TOC target → MD location)  
- [ ] No duplicate multipage table bodies  
- [ ] Vertical bands encoded as Mode column  
- [ ] Figure trees = PNG crops if text diagram inadequate  
- [ ] No ASCII apostrophe-as-tone on exponent pages  
- [ ] Two-column chapters: no mid-sentence cutoffs  
- [ ] Headers (Politeness conventions, etc.) not body soup  

## Relation to Companion

Reuse lessons in `docs/RESOLVED_EXTRACTION_ISSUES.md` RIE-006/010 and `scripts/book_vision_qa/_stitch_self_assessment_one.py` pattern.
