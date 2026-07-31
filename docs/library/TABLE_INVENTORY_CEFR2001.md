# Table inventory — CEFR EN 2001

**Job:** `cefr-en-2001`  
**Sources audited:** `output/cefr-en-2001/CEFR_EN_2001.md`, `work/cefr-en-2001/page_overrides/`  
**Date:** 2026-07-31  
**Page rule (binding):** document page = PDF leaf − 9 for body (Arabic p.1 starts at PDF leaf 10). See `ELEMENT_CATALOG_CONTRACT.md`.  
**Multipage rule (RIE-010):** full grid once on start page; continue pages = `table-continuity` chrome only; single `db:id`.

---

## 1. Formal numbered tables (Tables 1–5)

| # | Title | PDF leaf | **Doc page(s)** | Multipage? | Class | `db:id` | Override stitch status | Product MD status |
|---|-------|---------:|----------------:|------------|-------|---------|------------------------|-------------------|
| **1** | Common Reference Levels: global scale | 33 | **24** | No | Band×Level×Descriptor (vertical **Proficient/Independent/Basic User** band as Band col) | `cefr2001_table_1_common_reference_levels_global_scale` | Full grid on `page_033.md` | Present (single) |
| **2** | Common Reference Levels: self-assessment grid | 35–36 | **26–27** | **Yes** (2 pages) | **vertical_band_table** + multipage | `cefr2001_table_2_self_assessment_grid` | **RIE-010 OK:** full Mode\|Skill\|A1–C2 on `page_035.md`; continuity only on `page_036.md` | **Patched:** full Mode grid + continuity only (no half-table) |
| **3** | Common Reference Levels: qualitative aspects of spoken language use | 37–38 | **28–29** | **Yes** (2 pages) | multipage level split (C2–B2 / B1–A1 in print) | `cefr2001_table_3_qualitative_spoken_language` | **RIE-010 OK:** full C2–A1 on `page_037.md`; continuity only on `page_038.md` | **Patched:** full C2–A1 + continuity only |
| **4** | Levels A2.1 and A2.2 (A2+): listening comprehension | 41 | **32** | No | Plus-level example (two A2 rows) | `cefr2001_table_4_a2_plus_listening` | Full on `page_041.md` | Present (single) |
| **5** | External context of use: descriptive categories | 57–58 | **48–49** | **Yes** (left/right halves in print) | multipage **horizontal** stitch | `cefr2001_table_5_external_context_of_use` | **RIE-010 OK:** full 8-col on `page_057.md`; continuity on `page_058.md` | Full on start; continuity on continue |

### Vertical band (Table 2)

Printed PDF uses a left vertical band: **UNDERSTANDING** / **SPEAKING** / **WRITING**.

| Mode | Skills |
|------|--------|
| UNDERSTANDING | Listening, Reading |
| SPEAKING | Spoken Interaction, Spoken Production |
| WRITING | Writing |

Canonical columns (override): `| Mode | Skill | A1 | A2 | B1 | B2 | C1 | C2 |`

### Multipage stitch detail

| Table | Start override | Continue override | Expected continue content |
|-------|----------------|-------------------|---------------------------|
| 2 | `page_035.md` (doc **26**) full grid | `page_036.md` (doc **27**) | `<!-- table-continuity: … RIE-010 -->` + italic continuity line only |
| 3 | `page_037.md` (doc **28**) full grid | `page_038.md` (doc **29**) | same pattern |
| 5 | `page_057.md` (doc **48**) full 8-col | `page_058.md` (doc **49**) | continuity comment only (right half already merged) |

---

## 2. Illustrative descriptor scales (Ch 4–5)

Single-page Level×Descriptor scales (not multipage halves). Doc pages = PDF − 9.

| Doc | PDF | Scale title | Override id (if any) |
|----:|----:|-------------|----------------------|
| 58 | 67 | OVERALL ORAL PRODUCTION | `cefr2001_scale_overall_oral_production` |
| 59 | 68 | SUSTAINED MONOLOGUE: Describing experience | `cefr2001_scale_sustained_monologue_describing_experience` |
| 59 | 68 | SUSTAINED MONOLOGUE: Putting a case (e.g. in a debate) | `cefr2001_scale_sustained_monologue_putting_a_case` |
| 60 | 69 | PUBLIC ANNOUNCEMENTS | `cefr2001_scale_public_announcements` |
| 60 | 69 | ADDRESSING AUDIENCES | `cefr2001_scale_addressing_audiences` |
| 61 | 70 | OVERALL WRITTEN PRODUCTION | `cefr2001_scale_overall_written_production` |
| 62 | 71 | CREATIVE WRITING | `cefr2001_scale_creative_writing` |
| 62 | 71 | REPORTS AND ESSAYS | `cefr2001_scale_reports_and_essays` |
| 64 | 73 | PLANNING | `cefr2001_scale_planning` |
| 64 | 73 | COMPENSATING | `cefr2001_scale_compensating` |
| 65 | 74 | MONITORING AND REPAIR | *(title only / no scale id yet)* |
| 66 | 75 | OVERALL LISTENING COMPREHENSION | |
| 66 | 75 | UNDERSTANDING CONVERSATION BETWEEN NATIVE SPEAKERS | |
| 67 | 76 | LISTENING AS A MEMBER OF A LIVE AUDIENCE | |
| 67 | 76 | LISTENING TO ANNOUNCEMENTS AND INSTRUCTIONS | |
| 68 | 77 | LISTENING TO AUDIO MEDIA AND RECORDINGS | |
| 69 | 78 | OVERALL READING COMPREHENSION | |
| 69 | 78 | READING CORRESPONDENCE | |
| 70 | 79 | READING FOR ORIENTATION | |
| 70 | 79 | READING FOR INFORMATION AND ARGUMENT | |
| 71 | 80 | READING INSTRUCTIONS | |
| 71 | 80 | WATCHING TV AND FILM | |
| 74 | 83 | OVERALL SPOKEN INTERACTION | |
| 75 | 84 | UNDERSTANDING A NATIVE SPEAKER INTERLOCUTOR | |
| 76 | 85 | CONVERSATION | |
| 77 | 86 | INFORMAL DISCUSSION (WITH FRIENDS) | |
| 78 | 87 | FORMAL DISCUSSION AND MEETINGS | |
| 79 | 88 | GOAL-ORIENTED CO-OPERATION | |
| 80 | 89 | TRANSACTIONS TO OBTAIN GOODS AND SERVICES | |
| 81 | 90 | INFORMATION EXCHANGE | |
| 82 | 91 | INTERVIEWING AND BEING INTERVIEWED | |
| 83 | 92 | OVERALL WRITTEN INTERACTION | |
| 83 | 92 | CORRESPONDENCE | |
| 84 | 93 | NOTES, MESSAGES & FORMS | |
| 86 | 95 | TAKING THE FLOOR (TURNTAKING) | |
| 86 | 95 | CO-OPERATING | |
| 87 | 96 | ASKING FOR CLARIFICATION | |
| 96 | 105 | NOTE-TAKING (LECTURES, SEMINARS, ETC.) | |
| 96 | 105 | PROCESSING TEXT | |
| 110 | 119 | GENERAL LINGUISTIC RANGE | |
| 112 | 121 | VOCABULARY RANGE | |
| 112 | 121 | VOCABULARY CONTROL | |
| 114 | 123 | GRAMMATICAL ACCURACY | |
| 117 | 126 | PHONOLOGICAL CONTROL | |
| 118 | 127 | ORTHOGRAPHIC CONTROL | |
| 122 | 131 | SOCIOLINGUISTIC APPROPRIATENESS | |
| 124 | 133 | FLEXIBILITY | |
| 124 | 133 | TURNTAKING | |
| 125 | 134 | THEMATIC DEVELOPMENT | |
| 125 | 134 | COHERENCE AND COHESION | |
| 129 | 138 | SPOKEN FLUENCY | |
| 129 | 138 | PROPOSITIONAL PRECISION | |

**Multipage audit:** consecutive-page level-split scan (C2-only then A1-only pairs) → **0** incomplete pairs among overrides. These scales are **not** multipage RIE-010 candidates.

---

## 3. Appendix / self-assessment checklist tables (selected multipage)

| Doc | PDF | Content | Multipage note |
|----:|----:|---------|----------------|
| 231–232 | 240–241 | DIALANG READING statements | Sequential levels A1… (page-local); not a half-grid dup of Table 2 |
| 233–234 | 242–243 | DIALANG LISTENING; **LISTENING (continued)** on 243 | Intentional checklist continue (different rows, not duplicate of 242) |
| 235–237 | 244–246 | Further DIALANG / checklist blocks | Single-page grids |
| 238–243 | 247–252 | Document C3 skill grids (READING/WRITING/LISTENING pairs) | Paired continue pages by skill; content complementary |
| 249–257 | 258–266 | Appendix-style grids | Single-page unless marked continued |

**RIE-010 half-table dups:** none found between consecutive override pages for appendix checklists (continue pages hold **new** rows, not re-emits of the prior page’s full body).

---

## 4. Audit findings (2026-07-31)

### Confirmed OK (overrides)

| Pair | Pattern |
|------|---------|
| `page_035` / `page_036` | Full Table 2 + Mode vertical band → continuity only |
| `page_037` / `page_038` | Full Table 3 C2–A1 → continuity only |
| `page_057` / `page_058` | Full Table 5 8-col → continuity only |

### Product MD (this audit)

| Issue | Status |
|-------|--------|
| Table 2 full + B2–C2 half dup; no Mode | **Fixed** — Mode full grid + continuity |
| Table 3 half + half | **Fixed** — full C2–A1 + continuity |
| Table 5 stitch | **OK** (metadata → doc 48–49) |
| Book-wide page markers PDF leaf vs document | **Still open** outside table zones |
| `inject_cefr2001_critical` rebuild risk | **Open residual** — can re-inject Table 2 without Mode / PDF pages |

### Other multipage still broken

| Item | Status |
|------|--------|
| Numbered Tables 1–5 in **overrides** | **No remaining RIE-010 dups** |
| Numbered Tables 2–3–5 in **product MD** | **RIE-010 satisfied** after this audit |
| Illustrative Ch 4–5 scales | No multipage half-dups detected |
| Appendix checklist “continued” series | Complementary rows (OK); not formal single-`db:id` multipage product objects |
| Document page numbers in product MD book-wide | **Still largely PDF-index markers** — run `scripts/vision_extract/fix_page_numbers.py` after any full rebuild |
| Scale tables without `db:id` (many mid-book) | Catalog gap, not multipage-dup class |

---

## 5. QA checklist (this book)

- [x] Table 1 single full grid  
- [x] Table 2 override: full + continuity; Mode column  
- [x] Table 3 override: full + continuity  
- [x] Table 4 single  
- [x] Table 5 full stitch + continuity  
- [x] No consecutive-page duplicate table bodies in overrides  
- [ ] Product MD page markers = document pages book-wide (open)  
- [ ] Rebuild-safe inject path (`inject_cefr2001_critical`) aligned with Mode + doc pages (open residual)

---

## 6. Related docs

- `docs/library/ELEMENT_CATALOG_CONTRACT.md` — page formula + RIE-010 + vertical band  
- `docs/RESOLVED_EXTRACTION_ISSUES.md` — RIE-010  
- `work/cefr-en-2001/page_overrides/page_03{5,6,7,8}.md`, `page_05{7,8}.md`
