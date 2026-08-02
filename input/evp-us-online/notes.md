# Job notes — evp-us-online (draft)

**Status:** draft registration only  
**Kanban:** **RES-08** (canonical — do not invent a parallel ticket)  
**Capability (scrape code + experimental out/):** monorepo `tools/scrapers/evp/`  
**Catalog:** monorepo `tools/AGENTS.md`

## Intent

American English EVP Online senses with **Details** (definition + learner examples) → future SQL/store for coach diagnostics (aligned with consolidated Open Items / RES-08).

## Capability vs landing

| Layer | Location |
|-------|----------|
| Scrape scripts, raw probes, iterative `out/` | `tools/scrapers/evp/` (parent lang-platform repo) |
| Job registration (this folder) | `input/evp-us-online/` |
| Future work/output | `work/evp-us-online/`, `output/evp-us-online/` when import pipeline exists |

**`source.file` is null** — no local PDF/xlsx registered yet. `load_job` sets `ctx.pdf_path` to `input/evp-us-online/_NO_LOCAL_SOURCE` (sentinel; file does not exist). **Do not** treat `ctx.pdf_path` as a real artifact. Use monorepo paths below (and `capability_path` / notes) until a local `source.*` is copied in and `source.file` is set.

**Do not** move multi-GB `out/audio` into this nested git repo unless intentionally promoting shippable assets.

## Expected source artifacts (when ready to land)

From monorepo paths (relative to lang-platform root):

- `tools/scrapers/evp/out/evp-us-senses.jsonl`
- `tools/scrapers/evp/out/evp-us-senses.csv`
- `tools/scrapers/evp/out/evp-us-meta.json`
- `tools/scrapers/evp/out/evp-us.xlsx` (goal spreadsheet stage)

Profile: `tabular_db` (same family as descriptors/EGP jobs) — not PDF markdown pipeline.

## Honesty

- Scrape **started** under tools; this job is a **landing pointer**, not “product-done.”
- Pipeline `APPROVED` (when it exists) ≠ product-done for vocabulary resources — ticket notes + library honesty still apply.
