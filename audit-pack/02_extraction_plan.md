# Extraction reassembly plan

## Page layout (per PDF page)

PyMuPDF returns text blocks in arbitrary order. Footer blocks often appear first in the array while sitting at the bottom of the page visually.

**Rule:** Every page is reassembled in `page_layout.py`:

1. Collect all lines with `(y, kind, text)` from span dict
2. Sort by `y`
3. **Body** — main prose and headings (top → bottom)
4. **Footnotes** — numbered lines (`15. www...`) in lower zone (`y > 62%` page height)
5. **Page marker** — `<!-- page:N -->` + italic footer (`Page N … CEFR – Companion volume`)

## Tables

| Artifact | Pages | Merge |
|---|---|---|
| Table 1 | 23 | single-page pdfplumber |
| Table 2 | 24–25 | `MULTIPAGE_ARTIFACTS` → merge all tables |
| Vocabulary control | 132–133 | multipage merge |

Do **not** match multipage tables by caption string in row 0 (Table 2 first row is "What is addressed…").

## Continuation pages

Pages merged into a multipage artifact (Table 2 p25, vocabulary control p133, self-assessment grid p178–181) still emit **page footers** — footnotes plus `<!-- page:N -->`. Only table/prose body is skipped on continuation pages.

## Table of contents (pages 5–9)

The PDF TOC is **not** two-column prose. Each row has the section title on the left (~x=70) and the page number on the right (~x=513) at the **same y**.

Do **not** use `_order_body_columns` on TOC pages — it dumps all page numbers after all titles.

`toc_layout.py` groups lines by y-band, pairs title + page, merges wrapped titles (e.g. Figure 7), and emits markdown:

```
## Contents
- Foreword — 11
### 1.1. SUMMARY OF CHANGES TO THE ILLUSTRATIVE DESCRIPTORS — 24
```

## Two-column prose

Chapter body pages (not TOC) use left-then-right column order when both sides have ≥5 lines (`page_layout._order_body_columns`).

## Page footers

Footer lines match `Page \d+` anywhere in the line (e.g. `Introduction  Page 25`, `Preface with acknowledgements  Page 15`), not only lines starting with `Page`.

## Inventory

Each chunk inventory lists per page:

- `expected_page_markers` — every page in the chunk must appear in final output
- `required_artifacts` — tables/figures on specific pages
- `section_headers` — numbered headings detected in the PDF (e.g. `3.1.1.1. Oral comprehension`)
- `min_output_chars` — minimum measurable text expected in the page section (from PDF text length)
- `expects_table` — page has table grid lines; output must include pipe-table markdown
- `prose_blocks` — page has non-table prose that must not be table-only extraction

Post-merge `output_validator.py` checks:

- Every required table/figure/section has non-empty body (Table 2 must include rows from page 25)
- All PDF pages 1–278 have `<!-- page:N -->` markers (no gaps)
- **Per-page inventory coverage** — section headers, char minimums, table markdown, and page artifacts
- Footnotes appear after body text, before the page marker

## Figures vs TOC

`apply_figures` must **not** inject `db:id`, images, or diagram blocks inside the TOC (`## Contents` through `<!-- page:10 -->`). TOC figure/table lines stay as `- FIGURE N – … — 32` list entries only. Figure injection matches body captions (e.g. `Figure 11 – …` on page 47), not TOC listings.

## Pipeline order

```
inventory → extract (page_layout + table routing) → cleanup → merge → validate
```

Merge includes `apply_figures` and final prose formatting (`pipeline/post_process.py`), writing a single deliverable: `output/CEFR_Companion_Volume.md`.

- Paragraph merge, chapter formatting, page-marker spacing, bullet cleanup — see `metadata/post_processing.md`
- **Bold spacing** uses `prose_format.fix_bold_markdown()` once at the end; OCR typo fixes never strip spaces around `**`
- Signature blocks (name + bold title + footnotes) stay separate from the preceding paragraph