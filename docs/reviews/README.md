# Extraction-pipeline code reviews (audit log)

Dated, written reviews of structural / quality work on this pipeline.  
Use them when auditing **after Phase B, Phase C, etc.** — not day-to-day STATUS.

| Date | File | Scope |
|------|------|--------|
| 2026-07-27 | [2026-07-27_phase-a_code-quality-review.md](2026-07-27_phase-a_code-quality-review.md) | Multi-job Phase A (`bfaebcc` → `d7b516d`) |

**Phase B (2026-07-27):** implementation landed — `job_context.py` + thin `config.py` + `bootstrap.py`; `--job` required; no import auto-load; layout SoT = job+profile JSON; attribute-style `cfg.*` access; feature-gated callouts / Companion adjacent snippets. Full post–Phase B code-quality review still pending if desired.

**Convention:** `YYYY-MM-DD_<phase-or-topic>_code-quality-review.md`
