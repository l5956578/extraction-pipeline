# Extraction status — Threshold, Waystage, CEFR 2001

**Date:** 2026-07-31  
**Method:** Full-book Vision page overrides + **high-precision intonation multipass** (v006).  
**Standard:** Match page structure — paragraphs, headers, lists, tables, intonation marks.

## Deliverables (pipeline iteration **v006** — **not** Companion product approval)

**Track:** **Vision simple ingestion** (`scripts/vision_extract/`), **not** the Companion engine path.  
Pipeline `versions/00N/` + `APPROVED.json` = **extraction iteration markers only** — do **not** treat as production promote or frozen family relationships (kanban RES-04 / RES-14 / RES-16).

| Job | MD | Pages | Intonation pass | Notes |
|-----|-----|------:|-----------------|-------|
| cefr-threshold-1990 | `output/cefr-threshold-1990/Threshold_1990.md` | 192 | **Ch 5–8, 11–12, App A** | Draft MD + multipass; human QA open (RES-15) |
| cefr-waystage-1990 | `output/cefr-waystage-1990/Waystage_1990.md` | 120 | **Ch 3–5, 8–10, App A** | Draft MD; image PDF; human QA open (RES-15) |
| cefr-en-2001 | `output/cefr-en-2001/CEFR_EN_2001.md` | 273 | **out of scope** (no van Ek tones) | Draft MD + table work; polish open (RES-14) |

## Intonation bands (must not limit to Ch 5)

See **`INTONATION_PAGE_INDEX.md`**.

### Threshold 1990 (doc = PDF − 6)

| Doc pages | PDF leaves | Chapter |
|-----------|------------|---------|
| 27–47 | 33–53 | **5** Language functions |
| 48–58 | 54–64 | **6** General notions |
| 59–81 | 65–87 | **7** Specific notions |
| 82–87 | 88–93 | **8** Verbal exchange |
| 94–102 | 100–108 | **11** Sociocultural |
| 103–106 | 109–112 | **12** Compensation |
| 115–124 | 121–130 | **Appendix A** Pronunciation & intonation |

### Waystage 1990 (doc = PDF − 6)

| Doc pages | PDF leaves | Chapter |
|-----------|------------|---------|
| 15–21 | 21–27 | **3** Language functions |
| 22–29 | 28–35 | **4** General notions |
| 30–41 | 36–47 | **5** Themes / specific notions |
| 46–55 | 52–61 | **8–9** Sociocultural / verbal exchange |
| 56–59 | 62–65 | **10** Compensation |
| 68–74 | 74–80 | **Appendix A** |

## High-precision method

1. **Catalogue** mark-bearing leaves (`scan_intonation_pages.py`).
2. **Threshold:** PDF Paper-Capture marks (`'` `,` `.` `"`) → Unicode via `full_intonation_pass.py` / `native_intonation_convert.py` (more reliable than freehand Vision when text layer exists).
3. **Waystage:** image PDF → convert residual OCR marks in MD (`convert_md_ocr_marks.py`) + Vision multipass on overrides.
4. **Gold force:** `force_contrastive_and_midword.py` — 1.1.3 LF vs 1.3.1 contrastive; mid-word `pre'fer` → `preˈfer`.
5. **Never** re-run `fix_page_numbers.py` on already document-numbered MD (idempotent guard added).
6. **Do not** whole-page restitch thin overrides over denser product MD without tone-count audit.

## Nuclear tones

| Mark | Tone |
|------|------|
| **ˎ** | Low falling (below) |
| **ˋ** | High falling (above) |
| **ˊ** | High rising (above) |
| **ˏ** | Low rising (below) |
| **ˇ** | Falling-rising (v above) |
| **ˈ** | Head |
| **·** | Secondary stress |

**Tag questions** inviting agreement use **ˋisn't** (high fall) — not the same as contrastive **ˇisn't** (1.3.2).

## Gold checks (v006)

| Example | Expected |
|---------|----------|
| 1.1.3 | `ˈThis is the ˎbedroom.` / `The ˈtrain has ˎleft.` |
| 1.1.4 | `ˈHe is the ˎowner of the ·restaurant.` |
| animal | `The ˇanimal over ·there \| is my ˎdog.` |
| 1.3.1 contrastive | `ˈThis is the ·bedroom.` / `The ·train ˈhas ·left.` |
| 1.3.2 | `ˈNo it ˇisn't.` / `ˈYes you ˇdid.` |

## Scripts (intonation)

- `scripts/vision_extract/full_intonation_pass.py` — Threshold native multipass all primary leaves
- `scripts/vision_extract/convert_md_ocr_marks.py` — OCR/ASCII marks already in MD → Unicode
- `scripts/vision_extract/force_contrastive_and_midword.py` — section-aware gold + mid-word high
- `scripts/vision_extract/apply_native_intonation_to_md.py` — blockquote skeleton match
- `scripts/vision_extract/audit_intonation_md.py` — residual counts
- `scripts/vision_extract/fix_page_numbers.py` — PDF leaf → doc page (**idempotent**)
- `docs/vision_extract/INTONATION_NATIVE_DUMP_THRESHOLD.md` — full gold dump

## Pipeline snapshot (not product-done)

Threshold + Waystage: live MD + **`versions/006`** iteration snapshot.  
CEFR 2001: live MD + prior table/catalog work.  

**Human QA and relationship-map redo remain open** (kanban RES-14, RES-15, RES-16). Optional future engine-grade extract: RES-17.
