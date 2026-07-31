# Library gaps & adjacency (honest inventory)

**Date:** 2026-07-31 (librarian pass RES-05a)  
**Rule:** Prefer stating a gap over hallucinating coverage.

---

## Level coverage (six CEFR levels A1–C2)

| Level | Companion scales | CEFR 2001 | Waystage 1990 | Threshold 1990 | EVP | EGP |
|-------|------------------|-----------|---------------|----------------|-----|-----|
| Pre-A1 | Yes (many scales + App 2) | Limited / pre-formal | Partial adjacency | — | — | When ingested |
| A1 | Yes | Yes | **Strong historical** (early A) | — | Not scraped | XLSX registered |
| A2 | Yes | Yes | Partial | — | Not scraped | XLSX registered |
| B1 | Yes | Yes | — | **Strong historical** (B1) | Not scraped | XLSX registered |
| B2 | Yes | Yes | — | Some adjacency | Not scraped | XLSX registered |
| C1 | Yes | Yes | — | — | Not scraped | XLSX registered |
| C2 | Yes | Yes | — | — | Not scraped | XLSX registered |

**User-visible gap:** historical/spec-style depth for early A and B1 is helped by Waystage/Threshold PDFs, but those jobs are **not** clean MD extracts yet (and may need PNG for intonation symbols).  
**English lexis gap:** **EVP not scraped** — Companion/2001 do not replace a frequency/level vocabulary profile.

---

## Extraction / format status

| Item | Status | Next honest step |
|------|--------|------------------|
| Companion MD | **Complete / user-confirmed** | Promote approved version when ready; soft mid-page inventory noise only |
| CEFR 2001 MD | **Not extracted** | Production extract job when user approves; use librarian dump only for navigation |
| Descriptors xlsx → SQL | Not done | DATA import tickets |
| EGP xlsx → SQL | Registered job, not done | Scrape/import pipeline |
| EVP (AmE + details) | **Missing entirely** | RES EVP ticket / scrape design |
| Waystage | Draft job; PNG mode preferred | Extract or curated PNGs |
| Threshold | Draft job | Extract or curated PNGs |
| CN self-assessment grid | Source MD present | Pair with Companion App 2 at import |
| Sign language scales | In Companion | No separate PDF job |

---

## Adjacency (fills library without being “the six levels pack”)

1. **Waystage / Threshold** — Same author family; complementary specifications; subtle prose distinctions vs Companion (ticket RES-03/04 area).  
2. **Descriptors xlsx** — Aggregated scales for DB; may overlap Companion text; import must preserve full can-do strings.  
3. **EGP** — Grammar constructions by level (English-specific), not CEFR can-dos.  
4. **EVP** — Vocabulary by level (English-specific); critical for Flag-it / student vocab plans.  
5. **CoE external guides** linked from Companion (curriculum, Manual, FREPA, RELANG) — not stored as jobs yet.  
6. **Soft regression mid-pages (Companion)** — Pages 57, 74, 83, 87, 169 soft flags = inventory expecting per-page tables after multipage stitch; **not content defects**.

---

## Coverage map for coaching claims

| Claim you can make today | Basis |
|--------------------------|--------|
| Full modern can-do system (incl. mediation/online) | Companion approved MD |
| Deep theory of action-oriented CEFR | 2001 PDF (+ dump) |
| Edition-safe wording vs 2001 | Companion App 7 |
| Domain examples for online/mediation | Companion App 5 |
| English grammar by CEFR level | **Not until EGP ingested** |
| English vocab by CEFR level | **Not until EVP scraped** |
| Intonation-symbol pedagogy from Waystage | **Not until PNG/extract path done** |

---

## Suggested order (does not execute work)

1. Keep Companion approved; optional soft-inventory cleanup.  
2. CEFR 2001 production extract + Vision QA (reuse Companion lessons: multipage tables, URLs, figures, callouts).  
3. Descriptors xlsx → DB.  
4. EGP → DB.  
5. EVP scrape → DB.  
6. Waystage/Threshold PNG-aware extract.  
7. Expand outlines per book (RES-05 remainder).
