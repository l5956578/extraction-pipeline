# Code quality review — Phase D (business tags / JOB_MANIFEST)

| Field | Value |
|-------|--------|
| **Date** | 2026-07-27 |
| **Scope** | Phase D — job-level product tags into JOB_MANIFEST + product_context; promotion docs; ideas open item |
| **Repo** | extraction-pipeline + parent lang-platform |
| **Commits** | Nested `72e0e11` feat, `2a6179d` fix; parent includes PROMOTION + consolidated open item |
| **Rounds** | 2 → **0 open** |

---

## Verdict

**Phase D accepted.** Job-level business tags come only from `job.json` `product` (not invented). Per-artifact `product_tiers` remain in `db_import_registry.json` as a pure JSON array. Promotion docs and user validation task are in place.

---

## Deliverables

| Path | Role |
|------|------|
| `pipeline/job_manifest.py` | `write_job_manifest(ctx)` |
| `output/<job-id>/JOB_MANIFEST.json` | Job tags + paths + key files + lifecycle `pipeline_output` |
| `output/<job-id>/product_context.json` | Job-level product + pointer to registry |
| `docs/PROMOTION.md` (parent) | Copy path staging/production |
| `ideas/CEFR-Language-Coach-Consolidated.md` | User task: validate registry product_tiers |

Hooks: after merge, post_process/format, production extract (manifest write errors no longer swallowed).

---

## Tag layers (for auditors)

1. **Job-level** — `input/<job>/job.json` → `product` → JOB_MANIFEST / product_context  
2. **Artifact-level** — extraction → each row of `db_import_registry.json` → `product_tiers`

---

*Multi-job plan phases A–D complete. Further holistic review optional.*
