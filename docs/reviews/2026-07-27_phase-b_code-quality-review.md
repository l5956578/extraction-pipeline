# Code quality review — Phase B (JobContext / multi-job engine)

| Field | Value |
|-------|--------|
| **Date** | 2026-07-27 |
| **Scope** | Phase B — JobContext split, required `--job`, JSON layout SoT, feature gates |
| **Repo** | `pipelines/extraction-pipeline` |
| **Commits** | `4f4c1b5` feat; `a5b37dd` review fixes |
| **Baseline review** | [Phase A](2026-07-27_phase-a_code-quality-review.md) §7 highest-conviction asks |
| **Implement rounds** | 2 (6 open → fixed → 0 open) |

---

## Verdict

**Phase B largely deleted the Phase A bridge debt.** Accept as the multi-job engine foundation for Phase C.

| Phase A §7 ask | Status after Phase B |
|----------------|----------------------|
| Delete global rebinding as frozen-import contract | **Done** — `import pipeline.config as cfg` + attribute access |
| Single layout SoT | **Done** — job.json + profiles; `_DEFAULT_*` dual-write removed |
| No import side effects | **Done** — no `load_job(None)` at import; `get_active_job()` is None |
| Shared CLI bootstrap | **Done** — `pipeline/bootstrap.py`, `--job` required |
| Split god config | **Done** — `job_context.py` + thin `config.py` (~104 lines) |

---

## Architecture after Phase B

- `pipeline/job_context.py` — load/merge/layout bind
- `pipeline/config.py` — thin re-exports / module attributes after load
- `pipeline/bootstrap.py` — required `--job`
- Feature flags: `callouts`, `figures`, `rotated_tables`, `agent_vision`, `multipage_merge` (enforced in code, not cosmetic)
- Merge document shell from job.json `output` (+ page count from source)

### Day-to-day

```bash
python iterate_format.py --job cefr-companion-2020
python -u run_production_extract.py --job cefr-companion-2020
python -m pipeline.adjacent_guard --job cefr-companion-2020
```

Missing `--job` → argparse exit 2.

---

## Review findings (resolved in `a5b37dd`)

1. **bug** — `page_elements` default-arg freeze → call-time resolve  
2. **suggestion** — feature flags wired for real skips  
3. **suggestion** — merge shell data-driven from job.json  
4. **nit** — docs no longer claim Phase A default job  
5. **nit** — debug script uses bootstrap  
6. **nit** — missing profile fails loud  

Re-review: **0 open issues**.

---

## Smoke (verified in implement loop)

- Import without load → no active job  
- CLI without `--job` → exit 2  
- `iterate_format.py --job cefr-companion-2020` → OK  
- adjacent_guard with `--job` → OK  

---

## Not in Phase B (still later)

- Phase C: import Downloads CEFR set as additional jobs  
- Phase D: JOB_MANIFEST / promotion automation  
- Full contextvar threading of JobContext into every function signature (attribute-style `cfg` is the chosen contract)  

---

*Logged for post–Phase C audit. Do not start Phase C until the user says so.*
