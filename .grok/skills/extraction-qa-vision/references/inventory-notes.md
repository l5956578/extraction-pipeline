# extraction-qa-vision — documentation inventory

**When:** skill creation (Phase A, before SKILL body).  
**Purpose:** list files read and constraints the skill must not violate.

---

## Files read

| Path | Why |
|------|-----|
| `AGENTS.md` | Agent entrypoint: STATUS first, C2-ADJ mandatory, resolved-issue match, fast paths, deliverable |
| `STATUS.md` | SoT backlog; callout rules L05-P41-CO; UV-01–UV-13; rotated 88 vision files; trust/claims |
| `docs/RESOLVED_ISSUE_MATCH_PROTOCOL.md` | Investigate → match RIE → CLEAR auto-apply / AMBIGUOUS ask / NOVEL append |
| `docs/RESOLVED_EXTRACTION_ISSUES.md` | Re-apply ledger for fixed defect classes (not open backlog) |
| `docs/ARCHITECTURE.md` | Pipeline stages; inventory RO SoT; rotated path; validation |
| `docs/CONTRACTS.md` | Binding extract contracts: UV-01 callouts, figures, links, tables, gates, C2-ADJ |
| `docs/ADJACENT_ELEMENT_PROTECTION.md` | Neighbor protection; replace semantics; callout placement (top-left / end-body) |
| `work/cefr-companion-2020/metadata/figures_handling.md` | PNG vs text_diagram vs mermaid; crop policy; apply_figures strip soup |
| `work/cefr-companion-2020/metadata/ROTATED_TABLES_AGENT_VISION.md` | Vision path for rotated tables; never wipe `rotated_from_grok` |
| `skills/init.txt` | User/plan intent for coder↔Vision QA loop |
| `pipeline/config.py` | `ROOT`, `PDF_PATH`, `FINAL_DIR`, `METADATA_DIR`, `RENDER_SCALE=2.0` |
| `pipeline/adjacent_guard.py` | `_page_body` slice (markers at page end); neighbor gates |
| `pipeline/contract_validators.py` | Fail-closed contract gates |
| `output/cefr-companion-2020/CEFR_Companion_Volume.md` | Page marker pattern (spot-check p.40–41) |

**Not treated as current requirements:** `docs/archive/**`

---

## Constraints extracted (skill must respect)

### Architecture / scope

1. **Sit on top of existing pipeline** — do not invent parallel PDF extraction, new element types, or new inventory→extract paths.
2. **Inventory `reading_order` is SoT** for extract order; post_process may format but must not reorder page content arbitrarily.
3. **Deliverable:** `output/cefr-companion-2020/CEFR_Companion_Volume.md` with `<!-- page:N -->` anchors for pages 1–278.
4. **PDF source (read-only):** `CEFR Companion Volume_eng.pdf` via `pipeline.config.PDF_PATH`.

### Page Markdown slicing

5. Page markers are at the **end** of each page body. Body for page **N** is text **after the last preceding** `<!-- page:* -->` marker (or file start) **until** `<!-- page:N -->` — same as `adjacent_guard._page_body` / `contract_validators._page_body`.

### Callouts (UV-01, C2-CO*, L05-P41-CO)

6. Format: blockquote with `> **Title**`, blank `>` between paragraphs, preserve internal formatting.
7. Placement:
   - **Top-left** callout → first in reading order.
   - **Else** → end of body before footnotes (default).
   - **Exception (logged):** when callout is **not** top-left **and** neighbors are full-width prose (no multi-column region before/after) → prefer **inline** placement, not forced end-body.
8. Top full-width callout stays at top; do not force inline.

### Figures / soup (C2-F*, UV-12/13)

9. PNG or text_diagram **replaces** figure-as-prose; no dual emit; strip label/axis soup under figures.
10. Multi-fig pages must include all registry figure ids near captions.
11. Fixing figures must not trash neighbor prose (C2-ADJ / UV-13).

### Tables / IDs

12. Numbered tables use clean `table_NN_…` ids — not garbled scale ids from first column.
13. Markdown tables need a **blank line** after the element/id comment block so renderers produce columns.
14. Empty/junk tables must not emit.
15. Cell `<br>` separates phrases, not mid-phrase soft wraps.
15a. **Garbled slugs (`cfiiceps`, etc.):** inventory rebuild alone does **not** fix them (RIE-005 / L07-ID-REBUILD). Use `title_fix` + postprocess maps / re-slug emit. On any Vision fail, coding agent must match `docs/RESOLVED_EXTRACTION_ISSUES.md` **before** inventing a new patch.

### Prose / footnotes / URLs

16. Prose blocks remain pure; do not incorrectly merge or glue across structural boundaries.
17. Do not glue footnotes to `Page **N**`; blank line before page captions.
18. Sanitize URLs: no internal whitespace in `http(s)://…` tokens; do not invent HTML `<a>`.

### Adjacent protection (C2-ADJ)

19. Before claiming figure/callout/table/footnote fixed: run `python -m pipeline.adjacent_guard` and preferably `python -m pipeline.contract_validators`.
20. Manually check before/after the changed element (and page ±1).
21. Prefer **replace** semantics, not layer-on-top.

### Rotated tables

22. Default path: `work/cefr-companion-2020/metadata/rotated_from_grok/{slug}.md` (88 pages complete). **Never delete or rewrite** those vision files as part of this QA skill.
23. Geometry/OCR is fallback only; footnotes on rotated pages stay geometry.

### Trust / claims (UV-04)

24. Do not mark issues fixed without green gates and visual/PDF match where applicable.
25. Green mass-only checks ≠ fixed for crop quality and residual layout — user PDF QA remains authoritative for some classes.

### Snapshot / skill-specific (from plan + init)

26. Vision QA uses **full-page PNG only** — never crop the QA snapshot.
27. Snapshots only for pages with open bugs; store and **reuse** valid `work/cefr-companion-2020/metadata/qa_snapshots/page_NNN.png` unless `--force` (reject empty/corrupt).
28. Scale locked to `pipeline.config.RENDER_SCALE` (2.0) for determinism.
29. QA agent is **pure observer** — structured pass/fail only; never code, rewrite MD, or design.
30. Coding loop: max **4 fix attempts** (baseline QA free); after each fix **re-slice** MD before re-QA; then escalate.
31. Scope: deterministic extraction defects (placement, soup, merge, IDs, formatting) — not open product redesign.

---

## Related paths (not re-read fully; known from above)

- `docs/ISSUES_CHAPTER2_DIAGNOSIS.md` — issue catalog / user voice detail
- `work/cefr-companion-2020/metadata/page_renders/` — ad-hoc debug renders (distinct from `work/cefr-companion-2020/metadata/qa_snapshots/`)
- `pipeline/extractors/rotated_grok_vision.py` — rotated assemble path
