# Book-wide PDF ↔ MD Vision QA (CEFR Companion)

**Mode:** Deliverable verification — **not** pipeline re-architecture.  
**Sources:**  
- PDF: `input/cefr-companion-2020/source.pdf` (278 pages)  
- MD: `output/cefr-companion-2020/CEFR_Companion_Volume.md`  
- Snapshots: `work/cefr-companion-2020/metadata/qa_snapshots/page_NNN.png`

## Goal

Near-perfect MD vs PDF: no missing paragraphs, no dual-emit soup after diagrams, correct tables/callouts/figures.  
Anything imperfect is **logged** and **fixed in the MD** (Vision-led), without undoing rotated-table vision work.

## Pass 1 — Structural audit (DONE)

```
python scripts/book_vision_qa/structural_audit.py --job cefr-companion-2020
```

Results: `book_qa/structural_summary.json` + `structural_findings.jsonl`

| Kind | Count | Notes |
|------|------:|-------|
| missing_pdf_vocabulary | 35 | Many are **empty multipage mid-pages** (content only on span start) — real book defect |
| empty_or_near_empty_md | 23 | Chrome-only page bodies (e.g. 86, 95, 147–148, …) |
| missing_required_phrase | 3 | p.61 / p.71 section prose under figures |
| post_diagram_leaf_soup | 1+ | Fig 12/13 dual-emit (fixed in MD for 61/71) |
| md_much_longer_than_pdf | 12 | dual-emit bloat candidates |

## Pass 2 — Full-page snapshots

```
python scripts/book_vision_qa/render_all_pages.py --job cefr-companion-2020
```

Reuse valid PNGs; do not regenerate unless PDF changes.

## Pass 3 — Vision QA (page-by-page)

For each page N:

1. Full-page PNG `qa_snapshots/page_NNN.png`
2. MD slice (content before `<!-- page:N -->`)
3. Vision critic YAML per `.grok/skills/extraction-qa-vision/references/qa-output-contract.md`
4. On fail → fix **MD** (or re-insert from `rotated_from_grok` for table pages) → re-QA
5. Log to `book_qa/vision/page_NNN.yaml`

**Priority order:**

1. Critical empty pages with fat PDF text (missing content)
2. Figure pages with soup / missing trailing prose (61, 71, 47, …)
3. Callout / multi-column pages
4. Remaining pages 1–278 sequential

**Do not** rewrite `rotated_from_grok/*.md` bulk; for empty multipage middle pages, restore per-page content from those files or PDF without destroying merged multipage tables.

## Pass 4 — Catalog for review

`book_qa/OPEN_REVIEW.md` — residual fails after auto-fix, for optional human review only.

## Status log

| Date | Event |
|------|--------|
| 2026-07-30 | Structural audit 278 pages; catalog written |
| 2026-07-30 | MD fix p.61 (soup removed + §3.2.1 prose restored from PDF) |
| 2026-07-30 | MD fix p.71 (soup removed + §3.3.1 prose restored from PDF) |
