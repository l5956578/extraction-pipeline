# Adjacent-element protection (C2-ADJ)

**Logged:** 2026-07-17  
**Completed pass:** 2026-07-17 (full remaining packages)  
**User problem:** When one page element is fixed (figure, callout, table, footnote, …), **neighbors are damaged** — leftover garbage, duplicates, dropped headers/prose, glued lines. Untenable churn.

**Full approved plan (verbatim source of “expected” work):**  
[`docs/plans/2026-07-17_adjacent_element_protection_plan.md`](plans/2026-07-17_adjacent_element_protection_plan.md)

**User evidence:** `user debug/log 01.txt` … `log 04.md` (especially log 04 #5, #8, #10, #13 and systemic notes).

**STATUS backlog ID:** **C2-ADJ** (also relates to UV-03, UV-05, UV-08, UV-09, E5).

---

## 1. What the plan said was expected

### Root thesis (from plan)

There is **no exclusive, validated ownership** of each page region: extract often emits **all text**, then later stages **add** the correct representation (PNG, diagram, blockquote) **without removing** the old one; postprocess **rejoins across boundaries**. So every “fix element E” is really “mutate the whole page string.”

### Root causes named in the plan

| ID | Cause |
|----|--------|
| RC1 | **Dual layout / dual emission** (rich_page + inject PNG without delete) |
| RC2 | **No exclusive bbox ownership** (overlapping extract regions) |
| RC3 | **String-global** apply_figures / post_process |
| RC4 | **No adjacent regression gates** (user finds neighbor breaks) |
| RC5 | **Agent rework without replace semantics** (“add PNG” not “replace figure region”) |
| RC6 | Spans/chunks **amplify** the same single-page pattern |

### Planned work packages (execution order in plan)

| Package | Intent |
|---------|--------|
| **P0** | Element fences (optional) + **neighbor validation fail-closed** + agent rule to run them |
| **P1** | Figure path: **replace, don’t layer** (strip figure garbage under PNG/diagram) |
| **P2** | Callout path: exclusive region, single emit, placement policy (top-left first / else before footnotes) |
| **P3** | Postprocess respects boundaries (no glue footnote↔`Page **N**`; no cross-fence joins) |
| **P4** | Golden page snapshots for log 04 checklist pages |
| **Docs** | CONTRACTS + AGENTS + STATUS |
| **Later** | Exclusive RO extract end-state (deprecate full-page `figure_page` dual layout); re-extract as needed |

### Success criteria (from plan)

- Fixing X should not routinely break the line before/after X.
- Validators fail if garbage remains under PNG or next header disappears.
- Workflow: change element → run adjacent guard → only then claim progress.

---

## 2. What is coded now (full remaining packages, 2026-07-17)

| Package | Status | What landed |
|---------|--------|-------------|
| **P0** | **Done** | `pipeline/adjacent_guard.py` fail-closed gates + **`<!-- el:start/end -->` fences** around RO elements at extract (except footer/skip). Agent rule in AGENTS.md. |
| **P1** | **Done with selective exclusive filter** | Crop rects guide **diagram-label** exclusion only (`should_drop_line_for_exclusive`): real prose sentences in the same y-band are **kept** (fixes p.39–40 neighbor loss). Level/language axis rows stripped under PNG. Multi-fig emit order by figure number. text_diagram: catalog replace + soup strip (not exclusive bbox). Soup strip remains load-bearing for residual dual emit — not “structurally impossible” for every multi-fig edge case. |
| **P2** | **Done** | Callout placement policy (log 04): **top-left → first in RO**; **else → end of body before footnotes**. Exclusive obstacles for prose_segments. Single title emit via `emit_callout_blockquote` (title split, partial-para dedupe, known titles). Table-path callouts use same emit helper. |
| **P3** | **Done** | `_is_block_starter` includes `el:start/end`, footnotes, images, `Page **N**`, headings, db:id, blockquotes. `_ensure_blank_before_page_captions`. p.47 `### 3.1` restore + **dedupe** (one heading). Callout title dedupe. |
| **P4** | **Done** | `metadata/golden/page_{027,028,029,032,035,038,047}.json` with must_have / must_not_have / counts; wired into `adjacent_guard`. |
| **Docs** | **Done** | This file, STATUS C2-ADJ, CONTRACT_HARDENING_PROGRESS, CONTRACTS C2-ADJ (prior). |

### Concrete product effects verified

| Check | Result |
|-------|--------|
| `python -m pipeline.adjacent_guard` | **OK** |
| `python -m pipeline.contract_validators` | **OK** |
| p.38 no radar axis text after figure_06 PNG | **OK** |
| p.47 `### 3.1 RECEPTION` + `Reception involves…` once | **OK** |
| No dual `### Figure N` headers (sample pages) | **OK** |
| Blank line before `Page **N**` (sample) | **OK** |
| p.27/28 callout at end of body (not mid-sentence) | **OK** |
| p.29 callout title once | **OK** |

### Key files

- `pipeline/page_layout.py` — `extract_page_body_excluding`
- `pipeline/extractors/rich_text.py` — `extract_rich_page_excluding`
- `pipeline/extract_chunk.py` — exclusive figure compose, el fences, narrative callout → shared emit
- `pipeline/figure_inject.py` — strip under PNG (safety net)
- `pipeline/page_elements.py` — callout placement policy
- `pipeline/callout_detect.py` — exclusive band stitch + single-title blockquote
- `pipeline/post_process.py` — fence-aware joins, page blank, 3.1 restore/dedupe
- `pipeline/adjacent_guard.py` — gates + golden suite
- `metadata/golden/*.json`

---

## 3. What remains (honest leftover)

| Remaining item | Notes |
|----------------|--------|
| **Full multi-element RO for every figure page** | `figure_page` sugar remains; selective exclusive filter + soup strip handle PNG dual-emit / neighbor keep. Optional polish. |
| **Agent crop loop for wrong PNGs** (UV-06 / C2-F3) | Still required when crops include prose or miss diagram. |
| **Callout internal paragraph breaks** | Some boxes may still be one continuous blockquote body; placement + title-once fixed. |
| **Full-book inventory rebuild** | chunk_02 RO updated; other chunks need `build_inventories` + re-extract. |
| **§3.1 postprocess restore** | Temporary safety net; golden/gate still required. |

---

## 4. How to read this as a user

| Question | Answer |
|----------|--------|
| Where is the **plan**? | `docs/plans/2026-07-17_adjacent_element_protection_plan.md` |
| What did the plan **expect**? | §1 above + that full plan file |
| What did we **code**? | §2 above — packages **complete** for the adjacent-damage meta-bug |
| What is **left**? | §3 — crop QA and optional RO sugar removal, not dual-emission |
| How do I know guards work? | `python -m pipeline.adjacent_guard` and `python -m pipeline.contract_validators` |

**Bottom line:** Neighbor prose must not be deleted when excluding figure labels; dual emission under PNG is reduced by selective exclusive filter + soup strip + goldens for p.38–40. Callouts follow the log 04 placement rule. Residual work: agent crop QA, full multi-element figure RO, full-book inventory refresh.

---

## 5. Independent audit (2026-07-17)

Full audit of plan vs code vs deliverable:  
[`docs/plans/2026-07-17_C2_ADJ_implementation_audit.md`](plans/2026-07-17_C2_ADJ_implementation_audit.md)

**Summary grade:** packages P0–P4 **mostly correct** for **chunk_02 (pages 26–50)**; ideal exclusive-RO end-state still optional. Validators green; key MD probes pass. Not a docs-only pass.
