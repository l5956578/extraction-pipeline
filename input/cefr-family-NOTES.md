# CEFR family — notes (from Downloads `in-use/CEFR`)

Copied/adapted during Phase C (2026-07-27). Originals remain in Downloads.

## Source lineage (user history)

User read file 4 (Companion 2020) and learned it was an update to file 3 (CEFR EN 2001). Reviewing 3 led to files 1–2 (Waystage / Threshold). Numbering prefixes encode publish order for sorting.

| File (under Downloads `in-use/CEFR/`) | Job id | Intended output |
|------|--------|-----------------|
| `1-CEFR-Level-Waystage-1990.pdf` | `cefr-waystage-1990` | `page_png` (intonation markers) |
| `2-CEFR-Level-Threshold-1990.pdf` | `cefr-threshold-1990` | `page_png` |
| `3-CEFR-EN-2001.pdf` | `cefr-en-2001` | `markdown` |
| `4-CEFR-Companion-Volume-EN-2020.pdf` | `cefr-companion-2020` | `markdown` (**active**, extracted) |
| `4-CEFR-related/CEFR Descriptors (2020).xlsx` | `cefr-descriptors-2020` | `tabular_db` (later) |
| `4-CEFR-related/cefr-self-assessment-grid-cn.md` | `cefr-self-assessment-grid-cn` | `markdown_import` (pair with EN grid) |

## Relationship

CEFR 2001 defines six proficiency levels. Waystage relates to early A levels; Threshold to B1. Companion 2020 updates 2001 (mediation, online interaction, expanded self-assessment, etc.).

## Related materials (not Companion extras)

- **Descriptors xlsx:** aggregates many descriptor scales for detailed assessment → database.
- **CN self-assessment grid:** Chinese illustrative descriptors for the generic grid; English counterpart lives in Companion (self-assessment grid block).

## Gating

Only after gated approval may production folders hold extracts. Pipeline `output/<job-id>/` is the shippable lane; promote via staging (see monorepo `docs/PROMOTION.md`).
