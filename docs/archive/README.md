# Archive (historical)

Documents here are **not** the project source of truth. They are engineering snapshots that crop up during pipeline redesigns—kept so we can reconstruct past diagnosis without confusing agents about what is current.

**Current status:** [`../../STATUS.md`](../../STATUS.md)  
**Current architecture:** [`../ARCHITECTURE.md`](../ARCHITECTURE.md)  
**Current deliverable:** [`../../final_output/CEFR_Companion_Volume.md`](../../final_output/CEFR_Companion_Volume.md)

| File | What it was | Why archived |
|------|-------------|--------------|
| `EXTRACTION_DEBUG_HISTORY.md` | Attempt 2–4 append-only debug log | Open items rolled into STATUS §5 |
| `attempt3_design.md` | Attempt 3 execute-plan design | Superseded by STATUS / ARCHITECTURE |
| `extraction_plan.pre_2026-07.md` | Pre-restructure operational plan | Old pipeline shape |
| `post_processing.pre_2026-07.md` | Pre-restructure formatting notes | Format is integrated into merge/`iterate_format.py` |
| `CEFR_Companion_Volume_structured.legacy.md` | June 2026 standalone Session-2 formatter output | Deliverable is only `final_output/CEFR_Companion_Volume.md` |
| `last_post_process_run.txt` | June 2026 run stamp for that standalone formatter | Current stamp: `metadata/last_format_run.txt` |
| `ROTATED_TABLES_AGENT_VISION.snapshot.md` | Early vision handoff text | Live policy: `metadata/ROTATED_TABLES_AGENT_VISION.md` |
| `remaining-fixes.md` | Attempt 2 (early July) remaining-failures plan | Superseded by STATUS + later root-promotion work; do not treat as open checklist |
| `extraction_emit_log.2026-07-04.json` | One-off per-page emit/RO debug dump from extract debugging | Not used by production pipeline; not a registry |

When a similar engineering-only file appears again (one-off logs, obsolete dual-output MD, attempt plans), **move it here** rather than deleting, and add a row to this table.
