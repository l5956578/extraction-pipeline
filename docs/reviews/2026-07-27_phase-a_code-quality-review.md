# Code quality review — Phase A (multi-job layout)

| Field | Value |
|-------|--------|
| **Date** | 2026-07-27 |
| **Scope** | Phase A only — multi-job structure + Companion migration + JobContext adapter |
| **Repo** | `pipelines/extraction-pipeline` (nested) + parent docs as noted |
| **Git range** | `bfaebcc` → `d7b516d` (feat `51307b5`, fix `d7b516d`) |
| **Parent docs** | `d1cab1c`, `2135162` |
| **Review type** | Strict code-quality / maintainability (not functional smoke alone) |
| **Phase B status** | **Not started** — do not begin until user directs |

This document is the **audit record** of the post–Phase A review. Re-read before/after Phase B and Phase C to judge whether structural debt was paid down.

---

## Verdict

**Do not treat Phase A as architecturally finished.**

- **Data layout goal:** achieved (job-namespaced `input` / `work` / `output`).
- **Default Companion day-to-day use:** OK (smoke / format path works).
- **Long-term multi-job foundation:** **not yet elegant or safe without discipline**.
- **Accept as a deliberate temporary bridge** only if Phase B deletes the compatibility complexity rather than stacking on it.

---

## Before → after

| | **Before (single job)** | **After Phase A** |
|--|-------------------------|-------------------|
| Paths | Fixed under `input/`, `work/*`, `output/` | `input\|work\|output/<job-id>/` |
| Config | ~96 lines, obvious globals | ~379 lines, `JobContext` + **mutable globals** + JSON loaders |
| Layout SoT | Python only | **Python defaults + `job.json` + `profiles/*.json`** (triple) |
| CLIs | Import config, run | Parse args → `load_job` → **late import** of pipeline modules |
| Multi-job | Impossible | Possible **only if** every entrypoint loads job first |

Layout move of work/output data matches the multi-job plan. The **engine design mid-state** is the problem area.

---

## 1. Structural regressions (blockers for “good architecture”)

### 1.1 Mutable module globals as the public API

`load_job()` rebinds `PDF_PATH`, `FINAL_DIR`, layout tables, etc., and `load_job(None)` runs **at import time**.

That preserves `from pipeline.config import PDF_PATH` for one process / one job, but:

- Importers that bind names once stay frozen across a later `load_job(other)`.
- Fix was “CLI must import after `load_job`” — **entrypoint discipline**, not a sound model.
- Import side effects make tests, scripts, and “just import helpers” unpredictable.

**Code judo (Phase B):** one rule only:

- Either **always** `import pipeline.config as cfg` and use `cfg.FINAL_DIR` (attributes rebind), **or**
- Pass `JobContext` (or a contextvar) into stages and **stop exporting path globals**.

The current hybrid is the worst of both: looks like constants, acts like process state.

### 1.2 Dual (really triple) layout source of truth

Companion layout now lives in:

1. `_DEFAULT_*` in `config.py`
2. `job.json` `layout` / `extraction`
3. `profiles/cefr_companion.json`

With merge + “fallback if missing.” That is **incidental complexity**: drift when someone edits Python but not JSON (or the reverse). Phase A dual-write was intentional for safety; leaving it is **maintainability debt**, not a feature.

**Code judo:** pick **one** SoT for Companion layout:

- Prefer **job.json + profile only**; delete `_DEFAULT_*` once smoke proves JSON is complete, **or**
- Keep Python only until Phase B and don’t pretend JSON is authoritative yet.

### 1.3 CLI late imports paper over the design

`run_pipeline.py` (and prepare/finalize) delay importing half the pipeline so path rebinding works. That is a **hack that works**, not a clean boundary.

Cleaner shape:

```text
main → load_job → run_steps(ctx)
```

with modules reading paths from `ctx` / `cfg` at **call time**, not import-time delayed packages.

---

## 2. Missed simplification (ambitious but fair for Phase A→B)

| Missed move | Why it matters |
|-------------|----------------|
| **`config` split** | Job loading + layout defaults + path binding crowded into one module |
| **`final_markdown_path()` everywhere** | Half-done: some call sites fixed; legacy filename still in fallbacks |
| **Profile as data only** | Profile is loaded/merged, but **no feature flags gate** Companion-only code yet |

Phase A *could* have been thinner: **only move dirs + hardcode new path strings**, no JSON dual layout — then introduce JobContext in B. Instead: **migration + half a multi-job framework**. Cost is complexity *now* for multi-job *later*.

Call Phase A a **bridge**, not the target architecture.

---

## 3. Spaghetti / process-level protocol

Not random `if job_id == companion` in extractors (good).

Instead: global mutation + import-order rules + call-time path helpers + import-time defaults = **distributed protocol** every new CLI/script must obey. Next top-level `from pipeline.X import Y` reopens the frozen-import bug class.

---

## 4. File size / decomposition

| File | Before → after | Notes |
|------|----------------|-------|
| `config.py` | ~96 → **~379** | Under 1k; still a sharp jump; loaders + parsers + defaults + JobContext in one file |
| `post_process.py` | already ~1.9k | Phase A touched paths only — **do not grow further** for job logic |
| `run_pipeline.py` | steps nested in `main` | Late imports hurt scanability |

**Ask before Phase B grows further:** split job loading out of `config.py`.

---

## 5. What Phase A did well

- Top-level `input|work|output/<job-id>/` is the right product shape.
- `source.pdf` + `original_filename` is clean provenance.
- `job.json` / profile JSON direction matches the locked plan (not YAML).
- `git mv` of large trees preserved history.
- Default Companion still runs; no silent deliverable loss.
- Follow-up fix commit addressed real CLI load-order bugs.

---

## 6. Approval bar (strict code-quality skill)

| Criterion | Pass? |
|-----------|--------|
| No structural regression | **No** — global rebinding + dual layout hurts clarity |
| No missed simpler structure | **No** — thinner path-only migration or attribute-style `cfg` would be simpler |
| No unjustified 1k crossing | Pass (`config` still &lt; 1k) |
| No spaghetti growth | **Borderline fail** — process/import-order protocol |
| No hacky magic | **Fail** — import-time `load_job(None)` + rebind is magic |
| Architecture boundary | **Weak** — job system living inside “config constants” module |

**Rubber-stamp as clean multi-job foundation:** no.  
**Accept as Phase A bridge with Phase B required:** yes, with eyes open.

---

## 7. Highest-conviction asks for Phase B (ordered)

1. **Delete global rebinding as the contract** — use `ctx` or `config.PDF_PATH` attribute access only.  
2. **Single layout SoT** — job+profile JSON *or* Python, not both long-term.  
3. **No import side effects** — don’t call `load_job(None)` at bottom of `config.py`.  
4. **One entrypoint pattern** — shared `cli.bootstrap(job_id) -> JobContext` for all scripts.  
5. **Split files** — `job_context.py` / `load_job.py` vs thin re-exports if anything must stay in `config` for compatibility.

---

## 8. Bottom line (audit checklist)

| Question | Answer |
|----------|--------|
| Did Phase A achieve the **data layout** goal? | **Yes** |
| Is the **implementation** elegant / inevitable? | **No** — compatibility layer dominates |
| Safe to run Companion day-to-day? | **Yes** (default job) |
| Safe to add a second job without care? | **No** — easy path/import mistakes |
| Approve as finished architecture? | **No** |
| Approve as Phase A bridge? | **Yes** |

**Phase B framing:** delete this complexity; do not stack more helpers on the rebind model.

---

## 9. Related commits (quick index)

| Repo | Commit | Note |
|------|--------|------|
| extraction-pipeline | `51307b5` | feat: multi-job layout for cefr-companion-2020 |
| extraction-pipeline | `d7b516d` | fix: CLI load order, paths, skills |
| lang-platform | `d1cab1c` | docs: extraction multi-job paths |
| lang-platform | `2135162` | docs: extraction-pipeline tree job namespaces |

---

*Logged for post–Phase B / post–Phase C audit. Do not start Phase B until the user says so.*
