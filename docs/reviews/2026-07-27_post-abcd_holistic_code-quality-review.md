# Holistic code quality review — post multi-job redesign (Phases A–D)

| Field | Value |
|-------|--------|
| **Date** | 2026-07-27 |
| **Scope** | Full extraction-pipeline redesign (A layout → B engine → C jobs → D manifests) vs design intent |
| **Prior reviews** | Phase A–D under `docs/reviews/` (same date) |
| **Design inputs** | `docs/ARCHITECTURE.md`, `STATUS.md`, plan multi-job design, `docs/PROMOTION.md`, ideas CEFR consolidated (product/storehouse) |
| **Review type** | Strict structural + design-alignment (not only smoke) |

---

## 1. Design intent (what “done” should mean)

From architecture, plan, promotion, and business docs:

| Intent | Plain meaning |
|--------|----------------|
| **General engine** | One sophisticated PDF→MD pipeline, not one script per book |
| **Per-document knowledge in data** | `job.json` + inventories + profiles — not forked Python |
| **Multi-job I/O** | `input\|work\|output/<job-id>/` so jobs never clobber each other |
| **Promotion-ready output** | Shippable tree under `output/<job>/` with tags for coach/portal/storehouse |
| **Business tags** | Job-level from `job.json` `product`; artifact-level `product_tiers` in registry |
| **Not a materials peddler** | Digitized CEFR/storehouse content supports coaching; human validate tiers |

---

## 2. Phase-by-phase outcome (against prior reviews)

| Phase | Goal | Prior verdict | **Now** |
|-------|------|---------------|---------|
| **A** | Namespace Companion under job id | Bridge only; global rebind + dual SoT debt | **Superseded by B** for engine; **layout kept** |
| **B** | JobContext, required `--job`, JSON layout SoT | §7 asks closed | **Still holds** on inspection |
| **C** | Register CEFR family draft jobs | Accepted registration | **Holds**; engine-ready gate honest about draft modes |
| **D** | JOB_MANIFEST + product_context + promotion docs + user validation task | Accepted | **Holds** |

**Bottom line vs Phase A review:** the bridge debt that made A “do not approve as finished architecture” was **largely paid in B**. This holistic review does **not** re-litigate A as current HEAD.

---

## 3. Alignment with overall intent

### 3.1 What clearly works

1. **Multi-job product shape matches design**  
   Six jobs under `input/`; Companion production extract under `output/cefr-companion-2020/`; drafts scaffolded without overwriting Companion.

2. **Engine stays general; document knowledge in JSON**  
   Layout/features/product live in `job.json` + `profiles/*.json`. `ARCHITECTURE.md` matches code structure (`job_context`, `bootstrap`, `cfg.*` access pattern).

3. **CLI contract is honest**  
   `--job` required; `page_png` / `tabular_db` / `markdown_import` fail at bootstrap unless `--force-draft`. That matches “don’t pretend every registered job is extractable today.”

4. **Promotion / business tags path exists**  
   - Job-level: `job.json` → `JOB_MANIFEST.json` + `product_context.json`  
   - Artifact-level: `db_import_registry.json` array unchanged (ETL contract)  
   - Parent `docs/PROMOTION.md` documents copy to staging/production  
   - Ideas open item for user to validate `product_tiers`

5. **Phase A §7 checklist still true on HEAD**  
   No import-time `load_job(None)`; no residual `from pipeline.config import PDF_PATH` freeze pattern found; dual `_DEFAULT_*` layout gone; bootstrap shared.

### 3.2 Gaps vs full long-term intent (expected, not “ABCD failed”)

| Intent | Gap today |
|--------|-----------|
| “Sophisticated enough for most anything” | Only **markdown + PDF** path is production-operational; page_png / xlsx / CN md jobs are **registry + scaffolding**, not full pipelines |
| Multi-doc CEFR family fully extracted | Only **Companion** has full inventories + deliverable MD |
| Storehouse + portal consumption | Manifest ready; **no automatic promote tool**; user must validate tiers |
| Coursebook audio linkage | `extras/` concept exists in design; **not populated** (correct for Phase C scope) |

These are **roadmap honesty**, not regressions of A–D.

---

## 4. Structural code quality (current HEAD)

### 4.1 Approve-level strengths

- **Clear module split for multi-job:** `job_context` / `bootstrap` / thin `config` / `job_manifest` earn their keep.  
- **Attribute-style `cfg.*`** is the right pragmatic contract for this codebase size (full `ctx` threading every function would be larger and wasn’t required for intent).  
- **Feature flags** are real (figures, rotated, vision, multipage, callouts), not only declared.  
- **Document shell** driven by job.json reduces Companion hardcodes in merge.  
- **Net complexity direction A→B was deletion** (review B noted 830/−872 style win), not endless accumulation.

### 4.2 Remaining structural issues (high conviction)

#### Blocker-class for “multi-engine-mode product” (not for Companion day-to-day)

1. **Mode vs engine mismatch is architectural, not just UX**  
   Jobs declare `page_png` / `tabular_db` / `markdown_import` but there is no stage graph per mode—only a gate. That’s correct short-term; long-term either:
   - implement mode-specific stage runners, or  
   - stop calling them “extraction jobs” and call them **catalog entries** until tooling exists.  
   **Risk:** operators think registering a job = pipeline can run it.

#### Maintainability (should track; not emergency)

2. **`post_process.py` (~1914 lines)** still dwarfs the multi-job layer. Multi-job work barely touched it. This remains the largest modularity debt in the repo—unrelated to A–D success, but **the next “code judo” prize** if anything is.

3. **`extract_chunk.py` (~943), `page_elements.py` (~899), `callout_detect.py` (~678)**  
   Companion-era density. Feature flags reduce wrong-path execution; they do **not** decompose these modules. Future profiles will still drag CEFR-specific mass unless extractors are split by concern.

4. **Process-global active job**  
   One job per process is fine for CLI. Still not great for tests or in-process multi-job. Acceptable; document as invariant (already partly done).

5. **Feature checks scattered in extract_chunk / apply_figures / page_elements**  
   Works; a single “stage plan from features” object would delete scattered `if feature_enabled` noise later—optional judo, not required now.

6. **`job_manifest.py` (~293 lines)** for envelope writing is a bit large for JSON assembly but cohesive; no urgent split.

### 4.3 File-size bar

- No Phase A–D change pushed a **new** file over 1k for multi-job infrastructure (`config` ~110, `job_context` ~365).  
- **`post_process.py` already >1k** before redesign—still a standing smell; do not grow it for job logic.

### 4.4 Spaghetti

- Multi-job path is **not** random if-statements in unrelated flows.  
- Remaining tangle is **legacy Companion extract complexity**, not A–D folder wiring.

---

## 5. Design / product alignment checklist

| Checkpoint | Status |
|------------|--------|
| Top-level `input|work|output/<job-id>/` | **Met** |
| `job.json` + profiles, not forks | **Met** |
| `original_filename` provenance | **Met** (Companion + drafts) |
| Inventories under work only | **Met** |
| XLSX / CN grid as separate jobs | **Met** |
| `extras/` reserved for co-media (not misused) | **Met** (empty, correct) |
| JOB_MANIFEST from job.json product | **Met** |
| Registry array contract | **Met** |
| Promotion docs | **Met** |
| User task to validate product_tiers | **Met** (consolidated open item) |
| Engine runs non-Companion CEFR PDFs end-to-end | **Not met** (draft / not engine-ready) — **out of A–D scope** |
| Automatic staging copy tool | **Not met** — docs-only promote is intentional for D |

---

## 6. Approval bar (strict skill)

| Criterion | Holistic ABCD |
|-----------|----------------|
| Structural regression vs pre-redesign single-PDF simplicity | **Tradeoff accepted:** more modules, clearer multi-job model |
| Phase A bridge debt deleted | **Yes (B)** |
| Obvious spaghetti from multi-job | **No** |
| Unjustified 1k file growth for job system | **No** |
| Design intent for multi-job + promotion | **Largely yes** |
| Full “any PDF mode” sophistication | **No — Companion markdown path only** |

### Verdict

**Approve the A–D redesign as meeting its stated multi-job + promotion-readiness intent for the Companion production path.**

**Do not approve** the system as “all registered jobs are fully extractable” — and the code correctly refuses to claim that (bootstrap gate).

**Recommended next engineering (priority order), not re-litigating ABCD:**

1. User validation of Companion `product_tiers` (open item in ideas).  
2. When ready: implement **one** non-markdown mode properly (e.g. page_png for Waystage) *or* keep drafts catalog-only.  
3. Decompose **`post_process.py`** when next touching formatting heavily.  
4. Optional: stage plan / dispatcher from features to centralize `feature_enabled` branches.  
5. Optional: thin `promote_job.py` that copies `output/<id>/` → staging using JOB_MANIFEST (behavior already documented).

---

## 7. Relation to prior phase reviews

| Review | Keep as history of intermediate debt |
|--------|--------------------------------------|
| Phase A | Correctly flagged bridge; **do not treat as current HEAD status** |
| Phase B | Correctly closed §7; **still accurate** |
| Phase C | Registration correct; gate honesty **still accurate** |
| Phase D | Manifest/tag layer **still accurate** |

This document is the **post-ABCD synthesis**. Future work should open new dated reviews (e.g. after page_png implementation) rather than rewrite A–D files.

---

*Holistic review after Phases A–D. Companion production path + multi-job registry approved; full multi-mode engine remains future work.*
