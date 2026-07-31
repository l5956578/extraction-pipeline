# Master librarian — CEFR family & lang-platform resource library

**Audience:** Future agents (and the human coach) answering domain questions without reloading whole books.  
**Status:** First substantial draft (RES-06 partial). Companion + CEFR 2001 relationship work: **RES-05a**.  
**Index:** [`README.md`](README.md)

---

## 1. Library inventory (what exists on disk)

| Resource | Job id | Source | Extract status | Primary path |
|----------|--------|--------|----------------|--------------|
| Companion Volume 2020 | `cefr-companion-2020` | PDF | **Done / user-approved MD** | `output/cefr-companion-2020/CEFR_Companion_Volume.md` |
| CEFR EN 2001 | `cefr-en-2001` | PDF | **Draft only** (text dump for analysis) | `input/…/source.pdf`; dump `work/cefr-en-2001/CEFR_2001_fulltext_dump.txt` |
| Descriptors 2020 xlsx | `cefr-descriptors-2020` | XLSX | Not imported to DB | `input/cefr-descriptors-2020/` |
| Self-assessment grid CN | `cefr-self-assessment-grid-cn` | MD | Import-ready pair | `input/…` + Companion App 2 EN |
| Waystage 1990 | `cefr-waystage-1990` | PDF | Draft; prefer `page_png` (intonation) | `input/cefr-waystage-1990/` |
| Threshold 1990 | `cefr-threshold-1990` | PDF | Draft; `page_png` | `input/cefr-threshold-1990/` |
| English Grammar Profile | `cefr-english-grammar-profile-online-202607` | XLSX | Registered, not scraped/SQL | `input/cefr-english-grammar-profile-online-202607/` |
| English Vocabulary Profile (EVP) | — | Web | **Not scraped** | Gap |
| Family notes | — | MD | Living | `input/cefr-family-NOTES.md` |

Promotion rules: monorepo `docs/PROMOTION.md`; only approved versions → production.

---

## 2. Source preference rules (quick)

| Question class | Prefer | Avoid |
|----------------|--------|-------|
| Current can-do descriptors (spoken/written/online/mediation) | **Companion** scales (`db:id`) | Raw 2001 without App 7 check |
| What is the CEFR / policy / action-oriented theory | **2001** Ch 1–2 (+ Companion Ch 2 recap) | Using only exam-band folklore |
| How to read a scale | **2001** 3.7–3.8 | Jumping straight into a grid |
| Domains & rich situations | **2001** Ch 4; Companion App 5 for online/mediation examples | App 5 as the only domain inventory |
| Mediation / online / phonology / signing | **Companion** | 2001 alone |
| “Did wording change since 2001?” | Companion **App 7** | Guessing |
| Grammar by level (English) | EGP xlsx (when ingested) | Inventing grammar lists from CEFR prose |
| Vocabulary by level (English) | **EVP** (when scraped) | — |
| Early A / B1 historical specs | Waystage / Threshold (PNG-aware) | Treating them as full CEFR replacements |

Full correspondence: [`RELATIONSHIP_COMPANION_CEFR2001.md`](RELATIONSHIP_COMPANION_CEFR2001.md).

---

## 3. Query playbook (agent patterns)

### 3.1 Locate then quote
1. Classify need (philosophy / can-do / situation design / assessment grid / methodology).  
2. Open the **outline** for the right book.  
3. Grep MD (Companion) or PDF dump (2001) with **section + level + skill keywords**.  
4. Prefer `db:id=scale_…` blocks for can-dos.  
5. If citing 2001 descriptor text for *current* teaching, open Companion App 7.

### 3.2 Multi-book answers
Structure answers as:
- **Operational can-do** (Companion)  
- **Design frame** (2001 domains/tasks if relevant)  
- **Caveat** (edition / App 7 / missing EVP etc.)

### 3.3 Explanatory prose is not fluff
Companion progression paragraphs, mediation definitions, and 2001 Notes for the User / 3.7 “how to read scales” change *how* can-dos are used. Include them when the user asks “what does this level mean?” or “how should I use this scale?”

### 3.4 Figures and tables
- Figures: use PNG assets + MD caption; do not re-OCR figure text as prose.  
- Multipage scales: one full table / one `db:id` on start page (Companion product rule).

---

## 4. Anti-patterns

1. **Edition collapse** — Treating Companion and 2001 as interchangeable.  
2. **Level-only coaching** — Ignoring profiles (Companion 2.7) and 2001 branching.  
3. **Mediation from 2001 memory** — Incomplete.  
4. **App 5 as entire world of domains** — Only online/mediation examples.  
5. **Full-book reload every query** — Use outlines + registry + targeted grep.  
6. **Silent gaps** — Answering as if EVP/EGP/Waystage extracts exist when they do not.  
7. **Destructive edits** to consolidated product docs without user confirmation (`ideas/AGENTS.md`).

---

## 5. Navigation conventions

| Convention | Meaning |
|------------|---------|
| `Companion §3.4.1` | Companion chapter/section prose or scale cluster |
| `2001 §4.1.1` | CEFR 2001 section |
| `db:id=scale_…` | Stable artifact id in Companion MD / registry |
| `product_tier=base` | Core self-assessment style surfaces |
| `product_tier=assessment_action` | Session/actionable can-dos |
| `product_tier=detailed` | Finer grain |
| `product_tier=context` | Framing, figures, methodology |

Registry field proposal (for RES-05 remainder): add optional `nav_path` (e.g. `3.4.1/mediating_a_text/relaying_specific_information`) and `cefr_2001_anchors[]` on artifacts when DB import lands.

---

## 6. Relationship to coaching product (lang-platform ideas)

- Consolidated coach product: `ideas/CEFR-Language-Coach-Consolidated.md` (business + schema intent).  
- Librarian docs feed: descriptor import (DATA-*), Flag-it, session recaps, storehouse activities.  
- Kanban: RES epic; this draft advances **RES-05a** and partially **RES-06**.

---

## 7. Maintenance

When a new CEFR-family extract is approved:
1. Add outline file under `docs/library/`.  
2. Update `LIBRARY_GAPS.md` and this inventory table.  
3. Extend relationship notes if it maps to 2001/Companion.  
4. Tick RES-05/06 checklists; do not mark parents done until family-wide scope is truly finished.
