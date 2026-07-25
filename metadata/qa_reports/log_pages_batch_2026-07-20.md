# extraction-qa-vision batch report — user logs 01–07 pages

Date: 2026-07-20
Skill: extraction-qa-vision
Source pages (all user-named across logs): 22,27–44,47,70,90,94

## Investigation (garbled IDs — RIE-005)

- Pages/elements: scale headers/ids book-wide (sample p.64,65,110)
- MD/PDF check: table bodies already had correct titles; ### / db:id still garbled
- Ledger candidates: RIE-005
- Verdict: CLEAR
- Action taken: auto-applied re-derive artifact_id from fixed title (+ token map + title_fix); format/postprocess; no inventory rebuild claim

## Per-page Vision baseline (coding agent as critic vs full-page PNG + MD slice)

Policy: user-named pages mandatory. Systemic book-wide classes (ids, captions) validated via gates + samples.

| Page | Snapshot | Status | Notes | Matched | Action |
|------|----------|--------|-------|---------|--------|
| 22 | page_022.png | pass | even-page book caption form | none | — |
| 27 | page_027.png | pass | chapter open bare Page **27** matches PDF ▶ Page 27; callout present; fn21 URL intact | RIE-001 | format |
| 28 | page_028.png | pass | book caption | none | — |
| 29 | page_029.png | pass | chapter running head; fn26 RELANG restored; callout chapters | RIE-001 + novel fn26 | format |
| 30 | page_030.png | pass | plurilingual callout (user-confirmed class) | RIE-002 family | prior |
| 31 | page_031.png | pass | multi-col / callout order class | RIE-002 | prior |
| 32 | page_032.png | pass | Guide URL class | prior | prior |
| 33 | page_033.png | pass | hyphen / table class | prior | prior |
| 34 | page_034.png | pass | log sample page | prior | prior |
| 35 | page_035.png | pass | Can-do callout | prior | prior |
| 36 | page_036.png | pass* | multi-fig; crop quality C2-F3 needs user eyes | C2-F3 open | no crop change |
| 37 | page_037.png | pass | Background callout / Level C2 | prior | prior |
| 38 | page_038.png | pass | A2 table + Fig6; dual A2 under PNG stripped | RIE-004 | format |
| 39 | page_039.png | pass | Fig7 present | prior | prior |
| 40 | page_040.png | pass* | Figs 8–10 PNGs present; crop quality C2-F3 user confirm | C2-F3 open | no crop change |
| 41 | page_041.png | pass | research callout mid-flow + 3 phases | RIE-002/008 | prior |
| 42 | page_042.png | pass | Step callout formatting | RIE-003 | prior |
| 43 | page_043.png | pass | top_fullwidth + steps | RIE-002/003 | prior |
| 44 | page_044.png | pass | chapter chrome | RIE-001 | prior |
| 47 | page_047.png | pass | Fig11 caption + text_diagram + §3.1 | Q1 improved | prior |
| 70 | page_070.png | pass | log-named | prior | prior |
| 90 | page_090.png | pass | mediation diagram; soup strip class | RIE-004 | prior |
| 94 | page_094.png | pass | rotated scale (vision body untouched); ids cleaned via format | RIE-005 | format |

\* pass* = structure/ids/placement OK; product crop QA (C2-F3) still needs your visual confirm — not auto-closed.

## Gates

- adjacent_guard: OK
- contract_validators: OK

## Needs full re-inventory / re-extract?

| Item | Format-only enough? | Full re-extract? |
|------|---------------------|------------------|
| Garbled scale ids/titles in **final MD** | **Yes** (RIE-005 resync) | Optional later so inventory/raw match MD |
| Inventory JSON still garbled (cfiiceps etc.) | No (MD already fixed) | Yes if you want inventory SoT clean — not required to read deliverable |
| rotated_from_grok filenames with _ni_ | N/A — bodies not rewritten | Optional alias rename only; do not wipe |
| C2-F3 figure crop geometry | No | Multipass crops already; needs your confirm |
| Callout placement outside cleaned chunks | Already in cleaned from prior extract | Only if new pages regress after re-extract |

## Attempts summary

- Garbled IDs: 1 fix attempt (CLEAR RIE-005) + rebuild merge/figures once after accidental HEAD restore
- p.38 soup, p.29 fn26, Guide URL glue: format repairs
- No user ask required for CLEAR cases
