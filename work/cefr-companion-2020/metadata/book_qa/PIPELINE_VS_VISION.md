# Pipeline vs Vision/MD finalize — permanent lesson

**Job:** `cefr-companion-2020`  
**Date locked:** 2026-07-30  
**Audience:** every future extraction job + agent session

---

## What the pipeline achieved

The automated path (inventory → extract → assembly → postprocess → regression → versioning) took us **very far**:

- Full-book markdown with page markers, scales, prose, footnotes, figure hooks
- Hard regression green / soft inventory clean after grind
- Structural audit critical = 0
- A deliverable that is **usable** and **decent** as an intermediate product

That work must not be undervalued — and must not be mistaken for “finished book.”

---

## What only Vision / MD comparison finished

Near-perfect product MD required a **second lane**:

| Lane | Role |
|------|------|
| **Pipeline** | Bulk structure, OCR/layout emit, registry, gates, snapshots |
| **Vision + MD (book_qa)** | Page PNG ↔ live MD judgment, multipage continuity, Obsidian render, figure crop fidelity, dual-emit soup, user paste overrides |

User product bar: **grep-friendly single `db:id` tables**, correct figure assets, no Obsidian autolink traps, no mid-page duplicate scale halves.

These are **product-shape** requirements. Regression gates that only check soft inventory markers / structural length **do not** encode them unless we add explicit scanners.

---

## Miss taxonomy (do not recur on next extract)

When starting a **new** job, assume these will appear unless prevented:

### A. Multipage tables (highest impact)

| Failure | Symptom | Prevention |
|---------|---------|------------|
| Mid-page **duplicate** slice | Full table on start + lower band again on mid (p.147-class) | After building full multipage body on start, **delete** mid-page table body for that scale; keep prose/fn/chrome only |
| Unmerged high/low halves | C2–B2 on pN, B1–Pre-A1 on pN+1, two partial tables | Merge into one table on start; single `db:id` with `pages=N-M` |
| Strip heuristic too shy | Mid table kept because trailing prose_len large | Match by **scale title + incomplete level set**, not prose_len alone |
| Domain series (Appx 5) | Same title, different domain rows per page | Do **not** auto-merge levels; product decision for mega-table vs domain pages |

**Grep rule (user):** one `db:id` → one full table. Duplicates or prose-labeled scale rows poison retrieval.

### B. URL / footnote / Obsidian render

| Failure | Prevention |
|---------|------------|
| Bare `(https://…);5` eats footnote into URL | Always emit `(<https://…>);N` when footnote trail follows |
| `-->` immediately followed by `\|` table | Always blank line after HTML comments before tables |
| Soft-wrap vs phrase `<br>` in cells | Prefer intelligent phrase breaks; do not flood `<br>` |

### C. Figures / diagrams

| Failure | Prevention |
|---------|------------|
| Post-fence leaf soup only scanned | Also scan **pre-fence** window before `db:id=figure_*` |
| Mermaid for complex process figures (18–20) | Prefer **PDF-cropped PNG** when flow accuracy matters; list residual mermaids |
| Wrong mermaid edges | Do not “fix flow” by editing mermaid without PNG ground truth |

### D. Dual-struck / change-history text (Appx 7)

| Failure | Prevention |
|---------|------------|
| Dual old+new wording left as OCR soup | Resolve to final modality-inclusive product text; log if strikeout layout still needed |

### E. Process / agent failures (meta)

| Failure | Prevention |
|---------|------------|
| Declaring done on hard=0 alone | Book QA checklist: multipage scales, URL footnotes, figure assets, comment→table gaps |
| Soft-issue viewer thrash | Prefer hard gates + structured residual list; user rejected soft-viewer pitstops |
| Touching `rotated_from_grok` bulk | Protect; inject carefully; never bulk rewrite vision source |
| Skipping user-named pages | Forbidden (STATUS / skill rule) |

---

## Definition of done (next extract)

Before calling a book **product-ready**:

1. Hard regression **0**, soft **0** (or logged exceptions).
2. Multipage descriptor scales: **no** high-only/low-only complementary pairs left (except documented domain series / user exceptions).
3. Scan: unwrapped `(https://…)footnote` = 0; `-->\n\|` table gaps = 0.
4. Mermaid inventory reviewed; process figures PNG if user cares about flow.
5. Pre- and post-fence figure soup scan clean.
6. User issue file (if any) logged under `metadata/book_qa/` then deleted from repo root.
7. Version snapshot + `APPROVED.json` only after the above.

---

## Scripts worth reusing (this job)

| Script | Purpose |
|--------|---------|
| `_fix_url_footnotes.py` | Angle-bracket wrap URL+fn |
| `_fix_user_qa_issues.py` | Comment→table blank; fig16 soup |
| `_figures_mermaid_to_png.py` | Mermaid → PNG embeds |
| `_stitch_multipage_tables.py` | Strip obvious mid slices |
| `_restitch_all_multipage.py` | Merge halves + residual strip |
| `_stitch_self_assessment_one.py` | Self-assessment single grid |

Promote scanners into pipeline hard gates when a second job proves they are stable.

---

## Formatting is product (batch 3 lesson)

Vision PNGs are not decoration. For every callout / table / header / list:

1. **Extracted text** must be present.
2. **Structure/formatting** must match the page: paragraph count, line breaks in lists, column layout, section headers not merged.

Missing callout paragraph structure after hours of work means the agent treated Vision as a text-presence check only. That is wrong.

**URL lesson (user correction):** glued footnotes into URL tokens are a **sanitization** defect class — not “Obsidian render only.” Catalog all URLs with page + status; fix until residual scan is clean.

## One-line summary for agents

**Pipeline built decent MD. Vision/MD comparison finalizes product MD (text *and* formatting). Multipage tables, URL sanitization, callout/header structure, and figure PNG fidelity must be on the checklist — finite element classes, no excuse to leave them dirty.**
