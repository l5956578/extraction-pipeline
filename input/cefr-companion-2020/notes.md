# Job notes — cefr-companion-2020

**Source PDF working name:** `source.pdf`  
**Original on-disk name:** `CEFR Companion Volume_eng.pdf`  
**Published / Downloads name:** `4-CEFR-Companion-Volume-EN-2020.pdf` (hash-compare in Phase C)

## Processing notes

- Full pipeline is operational: spans → inventory → extract → cleanup → merge → figures → postprocess.
- Rotated tables use **agent vision** (`work/cefr-companion-2020/metadata/rotated_from_grok/`); geometry is fallback only.
- Inventories under `work/cefr-companion-2020/inventories/` are the extraction source of truth (`reading_order`).
- Deliverable: `output/cefr-companion-2020/CEFR_Companion_Volume.md`.

## Institutional memory

- Project status / open backlog: repo-root `STATUS.md`
- Known-good re-apply fixes: `docs/RESOLVED_EXTRACTION_ISSUES.md` (RIE) + match protocol
- Architecture: `docs/ARCHITECTURE.md`

## CLI (Phase B)

```bash
python run_pipeline.py --job cefr-companion-2020 --step all
python iterate_format.py --job cefr-companion-2020
# --job is required on all entry scripts (no silent default)
```
