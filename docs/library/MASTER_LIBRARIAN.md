# Master librarian — CEFR family & lang-platform resource library

**Audience:** Future agents (and the human coach) answering domain questions without reloading whole books.  
**Status:** Draft expanded 2026-07-31 — **RES-05a** (Companion+2001) + **RES-05b** (Threshold+Waystage + 4-way map).  
**Index:** [`README.md`](README.md)

---

## 1. Library inventory (what exists on disk)

| Resource | Job id | Source | Extract status | Primary path |
|----------|--------|--------|----------------|--------------|
| Companion Volume 2020 | `cefr-companion-2020` | PDF | **Done / user-approved MD** | `output/cefr-companion-2020/CEFR_Companion_Volume.md` |
| CEFR EN 2001 | `cefr-en-2001` | PDF | **Draft** (analysis dump only) | `input/…/source.pdf`; `work/cefr-en-2001/CEFR_2001_fulltext_dump.txt` |
| Threshold 1990 | `cefr-threshold-1990` | PDF (OCR text usable) | **Draft**; mode `page_png` | `input/…/source.pdf`; dump `work/cefr-threshold-1990/threshold_fulltext_dump.txt` |
| Waystage 1990 | `cefr-waystage-1990` | PDF (**image-based**) | **Draft**; mode `page_png` | `input/…/source.pdf`; OCR samples `work/cefr-waystage-1990/` |
| Descriptors 2020 xlsx | `cefr-descriptors-2020` | XLSX | Not imported to DB | `input/cefr-descriptors-2020/` |
| Self-assessment grid CN | `cefr-self-assessment-grid-cn` | MD | Import-ready pair | + Companion App 2 EN |
| English Grammar Profile | `cefr-english-grammar-profile-online-202607` | XLSX | Registered, not SQL | `input/…` |
| English Vocabulary Profile (EVP) | — | Web | **Not scraped** | Gap |
| Family notes | — | MD | Living | `input/cefr-family-NOTES.md` |

Promotion: monorepo `docs/PROMOTION.md`; only approved versions → production.

---

## 2. Source preference rules (quick)

| Question class | Prefer | Avoid |
|----------------|--------|-------|
| Current can-do descriptors (spoken/written/online/mediation) | **Companion** scales (`db:id`) | Raw 2001 without App 7; Threshold exponents as if they were CEFR levels |
| What is the CEFR / policy / action-oriented theory | **2001** Ch 1–2 (+ Companion Ch 2 recap) | Exam-band folklore only |
| How to read a scale | **2001** 3.7–3.8 | Jumping straight into a grid |
| Domains & rich **modern** online/mediation situations | Companion **App 5** + 2001 §4.1.1 | App 5 as only domain world |
| Domains & **classic travel/social English situations + exponents** | **Threshold** (fuller) / **Waystage** (early) | Collapsing into CEFR can-do lines alone |
| Language **functions** (invite, complain, arrange…) with English exponents | Threshold ch. 7 / Waystage ch. 3 | Inventing phrase lists |
| Themes / specific notions vocabulary (English objective) | Threshold ch. 9 / Waystage ch. 5 | EVP substitution (EVP still missing) |
| Mediation / online / phonology / signing can-dos | **Companion** | 2001 or Threshold alone |
| “Did CEFR wording change since 2001?” | Companion **App 7** | Guessing |
| Intonation / pronunciation marks in van Ek–Trim | Threshold/Waystage **App A via Vision/PNG** | OCR text only (Waystage has no text layer) |
| Grammar by CEFR level (English) | EGP when ingested | Threshold grammar appendix as full EGP |
| Vocabulary by CEFR level (English) | **EVP** when scraped | Word indexes as EVP |
| Early A / freer social objective path | Waystage → Threshold, then Companion can-dos for reporting | Treating Waystage/Threshold *as* A2/B1 CEFR text |

**Pair maps:**  
- Companion ↔ 2001 → [`RELATIONSHIP_COMPANION_CEFR2001.md`](RELATIONSHIP_COMPANION_CEFR2001.md)  
- Threshold ↔ Waystage → [`RELATIONSHIP_THRESHOLD_WAYSTAGE.md`](RELATIONSHIP_THRESHOLD_WAYSTAGE.md)  
- **All four** → [`RELATIONSHIP_CEFR_FAMILY_4.md`](RELATIONSHIP_CEFR_FAMILY_4.md)

---

## 3. Query playbook (agent patterns)

### 3.1 Locate then quote
1. Classify need: philosophy | can-do level | situation/exponent design | assessment grid | methodology | intonation.  
2. Open the **outline** for the right book(s).  
3. For multi-book questions, open **RELATIONSHIP_CEFR_FAMILY_4** decision table first.  
4. Grep Companion MD (`db:id`) / 2001 dump / Threshold dump; Waystage via OCR samples or page images.  
5. If citing 2001 can-do wording for *current* teaching → Companion App 7.

### 3.2 Multi-book answers (recommended shape)
- **Levelled can-do** (Companion; optionally 2001 ancestor)  
- **Objective content** (Waystage/Threshold functions, notions, situations) when designing *what to teach*  
- **Theory/domain frame** (2001) when designing *why / how to scale*  
- **Caveat** (artifact type: specification vs CEFR scale; missing EVP; image-only App A)

### 3.3 Explanatory prose is not fluff
- Companion progression / mediation definitions  
- 2001 Notes for the User / §3.7 how to read scales  
- Threshold/Waystage prefaces (objective ≠ syllabus; adapt lists)  
- Threshold components chapter (functions vs notions limits)

### 3.4 Figures, tables, scans
- Companion figures: diagram PNGs + MD captions.  
- Companion multipage scales: one full table / one `db:id`.  
- Waystage: **assume scan** — structure from Contents + OCR; production still `page_png`.  
- Threshold App A / Waystage App A: **Vision** for intonation symbols.

### 3.5 Example routes

| Ask | Route |
|-----|--------|
| B1 oral interaction can-do | Companion scale → optional 2001 3.7 literacy |
| Hotel check-in exponents early | Waystage functions + themes |
| Hotel check-in freer / fuller | Threshold situations + functions + specific notions |
| Mediation can-do + classroom situation | Companion 3.4 + App 5 (not Threshold) |
| What is action-oriented? | 2001 Ch 2 → Companion 2.1–2.2 |
| Path A2→B1 content then CEFR report | Waystage→Threshold inventories + Companion can-dos |

---

## 4. Anti-patterns

1. **Edition collapse** — Companion ≡ 2001.  
2. **Type collapse** — Threshold/Waystage ≡ CEFR descriptor scales.  
3. **Level-only coaching** — Ignoring profiles (Companion 2.7) and 2001 branching.  
4. **Mediation from 2001 or Threshold** — Incomplete / wrong artifact.  
5. **App 5 as entire domain world** — Miss Threshold situations.  
6. **Ignoring van Ek–Trim once Companion exists** — Lose exponent wealth.  
7. **OCR-only intonation** from App A.  
8. **Silent gaps** — Fake EVP/EGP/Waystage-MD coverage.  
9. **Full-book reload every query** — Use outlines + targeted grep.  
10. **Destructive edits** to consolidated product docs without confirmation.

---

## 5. Navigation conventions

| Convention | Meaning |
|------------|---------|
| `Companion §3.4.1` | Companion section / scale cluster |
| `2001 §4.1.1` | CEFR 2001 section |
| `Threshold §functions` / book p.27 | Threshold 1990 language functions chapter |
| `Waystage §1` | Waystage objective description |
| `db:id=scale_…` | Companion registry artifact |
| `objective_function` / `objective_notion_*` | Future DB kinds for van Ek–Trim (see family-4 map) |

Registry proposal (RES-05 remainder): `nav_path`, `cefr_2001_anchors[]`, optional links from companion scales to threshold situations.

---

## 6. Relationship to coaching product

- Living product/business doc: `ideas/CEFR-Language-Coach-Consolidated.md`.  
- Librarian layer feeds DATA import, Flag-it, recaps, storehouse.  
- Kanban: **RES-05a** done; **RES-05b** this pass; parents **RES-05/06** still open; **RES-03/04** for extract/registry when approved.

---

## 7. Maintenance

When a new CEFR-family extract is approved:
1. Add `OUTLINE_*.md`.  
2. Update `LIBRARY_GAPS.md` + this inventory.  
3. Extend pair or family relationship maps.  
4. Update RES-05/06 checklists; keep parents open until family-wide scope is finished.
