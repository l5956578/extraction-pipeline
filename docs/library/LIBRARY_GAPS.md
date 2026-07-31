# Library gaps & adjacency (honest inventory)

**Date:** 2026-07-31 (RES-05a + **RES-05b** Threshold/Waystage librarian pass)  
**Rule:** Prefer stating a gap over hallucinating coverage.

---

## Level coverage (six CEFR levels A1–C2)

| Level | Companion scales | CEFR 2001 | Waystage 1990 | Threshold 1990 | EVP | EGP |
|-------|------------------|-----------|---------------|----------------|-----|-----|
| Pre-A1 | Yes (many + App 2) | Limited | Partial spirit only | — | — | When ingested |
| A1 | Yes | Yes | **Strong objective adjacency** (selection from Threshold model) | Prerequisite path | Not scraped | XLSX registered |
| A2 | Yes | Yes | **Strong objective adjacency** (~180–200h estimate) | Bridge toward Threshold | Not scraped | XLSX registered |
| B1 | Yes | Yes | Below aim | **Strong objective adjacency** (~375h estimate) | Not scraped | XLSX registered |
| B2 | Yes | Yes | — | Some freer social adjacency; not the book’s ceiling claim | Not scraped | XLSX registered |
| C1–C2 | Yes | Yes | — | — | Not scraped | XLSX registered |

**Clarification:** Waystage/Threshold “adjacency” = **historical communicative objective density**, not “these files contain CEFR can-do scales.”

---

## Extraction / format status

| Item | Status | Next honest step |
|------|--------|------------------|
| Companion MD | **Complete / user-confirmed** | Promote when ready; soft mid-page inventory noise only |
| CEFR 2001 MD | **Not extracted** | Production extract when approved; dump is navigation-only |
| Threshold 1990 | PDF + **OCR dump** + librarian outline | No production MD; `page_png` mode recorded; App A needs Vision |
| Waystage 1990 | PDF **image-based** (no native text) + OCR samples + outline | Same; heavier Vision dependency than Threshold |
| Descriptors xlsx → SQL | Not done | DATA tickets |
| EGP xlsx → SQL | Registered, not done | Import pipeline |
| EVP | **Missing entirely** | Scrape design (RES EVP) |
| CN self-assessment grid | Source MD present | Pair with Companion App 2 |
| Outlines for four books | **Done** (librarian layer) | Expand when other jobs extract |

---

## Newly visible gaps / adjacencies (this pass)

1. **Waystage has no reliable text layer** — full-text dump is empty; librarian work used Tesseract on page renders. Production extract must plan OCR/Vision, not `get_text` alone.  
2. **Threshold OCR exists** (Paper Capture) but is noisy; intonation appendix still visual.  
3. **Same-model path Waystage → Threshold** is explicit in both prefaces — useful for curriculum *hours* and inventory growth; still map to Companion for *level reporting*.  
4. **Function/notion inventories** are a distinct artifact type from CEFR scales — future DB should not force them into `descriptor_scale` only.  
5. **App A (both books)** is the main reason jobs prefer `page_png`.  
6. **No EVP** remains the largest English-lexis hole relative to Threshold/Waystage word indexes (indexes ≠ profile).  
7. Companion soft flags on mid pages 57/74/83/87/169 still **non-blocking** multipage product shape.

---

## Coverage map for coaching claims

| Claim you can make today | Basis |
|--------------------------|--------|
| Full modern can-do system (incl. mediation/online) | Companion approved MD |
| Deep CEFR theory / how to read scales | 2001 PDF (+ dump) |
| Edition-safe CEFR wording vs 2001 | Companion App 7 |
| Online/mediation domain examples | Companion App 5 |
| Early adult English **objective** content (functions/themes) | Waystage outline + OCR/PDF |
| Freer social/travel **objective** content | Threshold dump + PDF |
| Intonation symbols in van Ek–Trim | **Only with page images** (not yet packaged as production PNG set) |
| English grammar by CEFR level | **Not until EGP ingested** |
| English vocab by CEFR level | **Not until EVP scraped** |

---

## Suggested order (does not execute work)

1. Companion approved (done).  
2. CEFR 2001 production extract + Vision QA.  
3. Descriptors xlsx → DB.  
4. EGP → DB.  
5. EVP scrape → DB.  
6. Waystage/Threshold: curated page_png or Vision-aware extract (**RES-03/04** when approved).  
7. RES-05 remainder: registry `nav_path` fields; outlines for remaining jobs.
