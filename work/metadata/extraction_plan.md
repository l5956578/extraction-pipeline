# Extraction plan (operational)

> **Status and backlog:** see root [`STATUS.md`](../STATUS.md).  
> **Design detail:** see [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md).  
> This file is the short operational contract for implementers.

---

## Pipeline order

```
spans → inventory → extract → cleanup → merge → figures → post_process → validate
```

| Command | When |
|---------|------|
| `python run_pipeline.py --step all` | Full rebuild (slow) |
| `python -u run_production_extract.py` | Extract through format (no re-span unless inventories stale) |
| `python iterate_format.py` | Format-only (~4s) after `post_process.py` / `prose_format.py` changes |
| `python prepare_rotated_for_grok.py` | Refresh rotated PNG handoffs |
| `python finalize_after_grok.py` | After new `rotated_from_grok/*.md` |

---

## Contracts (must not regress)

1. **`reading_order`** in inventories is the extraction source of truth.
2. Multipage tables emit body once (start page); continuations keep trailing prose + footnotes + markers.
3. Every page 1–278 has a `<!-- page:N -->` marker in final output.
4. **Rotated scales:** prefer `work/metadata/rotated_from_grok/{slug}.md` (agent vision). Geometry is fallback only.
5. Trailing prose must **not** ingest the footnote/page-footer band (`first_footer_band_y`).
6. Paragraph breaks for body use **y-gap**, not capital-after-period alone.
7. Final formatting runs on the **single** deliverable `output/CEFR_Companion_Volume.md`.

---

## Page layout rules

- Body → footnotes → page caption → `<!-- page:N -->`
- Dingbats: footer arrow `3` → `▶`; list bullet `f` → list marker path
- Bold: PDF flag **or** Bold/Semibold font name
- TOC pages 5–9: `toc_layout` only (no left/right column dump)

---

## Rotated tables

| Step | Path |
|------|------|
| PNG prep | `work/metadata/rotated_for_grok/` |
| Vision markdown | `work/metadata/rotated_from_grok/` |
| Module | `pipeline/extractors/rotated_grok_vision.py` |
| Procedure | `work/metadata/ROTATED_TABLES_AGENT_VISION.md` |

**Coverage:** see STATUS §6. Appendix 5 (191–241) still needs vision markdown.

---

## Chunk map

| Chunk | Pages |
|-------|-------|
| 01 | 1–25 |
| 02 | 26–50 |
| 03 | 51–75 |
| 04 | 76–100 |
| 05 | 101–125 |
| 06 | 126–150 |
| 07 | 151–175 |
| 08 | 176–241 |
| 09 | 242–266 |
| 10 | 267–278 |
