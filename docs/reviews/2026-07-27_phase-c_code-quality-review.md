# Code quality / integration review — Phase C (CEFR job import)

| Field | Value |
|-------|--------|
| **Date** | 2026-07-27 |
| **Scope** | Phase C — register Downloads `in-use/CEFR` as multi-jobs; companion provenance |
| **Repo** | `pipelines/extraction-pipeline` |
| **Commits** | `a500aa6` import; `bd83dcd` review follow-up |
| **Rounds** | 2 (6 suggestions/nits → fixed → 0 open) |

---

## Verdict

**Phase C accepted.** CEFR family jobs registered without overwriting Companion production extract. Downloads originals untouched. `potential-use` not imported.

---

## Jobs registered

| Job id | Source (original_filename) | Status | Mode | Profile |
|--------|----------------------------|--------|------|---------|
| `cefr-companion-2020` | Companion (hash-matched to Downloads 4-…) | active | markdown | cefr_companion |
| `cefr-waystage-1990` | 1-CEFR-Level-Waystage-1990.pdf | draft | page_png | cefr_classic |
| `cefr-threshold-1990` | 2-CEFR-Level-Threshold-1990.pdf | draft | page_png | cefr_classic |
| `cefr-en-2001` | 3-CEFR-EN-2001.pdf | draft | markdown | cefr_classic |
| `cefr-descriptors-2020` | CEFR Descriptors (2020).xlsx | draft | tabular_db | tabular_db |
| `cefr-self-assessment-grid-cn` | cefr-self-assessment-grid-cn.md | draft | markdown_import | markdown_import |

XLSX + CN grid are **separate jobs**, not Companion `extras/`.

Companion SHA256 (Downloads ≡ pipeline source):  
`BFBD8C74090419AC4B9B352D6BA26E180713B31F45265D7D775B7C36DD7AD1B1`

---

## Follow-up fixes (`bd83dcd`)

- Bootstrap rejects non-engine-ready draft modes unless `--force-draft`
- `cefr_classic` features default off (2001 enables figures/multipage at job level)
- STATUS / ARCHITECTURE / AGENTS / family notes clarify readiness and multi-extension sources

---

## Not done (later)

- Full extraction of draft PDF jobs  
- Phase D promotion / JOB_MANIFEST automation  
- `potential-use` import  

---

*Logged for post–Phase D audit. Do not start Phase D until the user says so.*
