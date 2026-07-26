---
name: extraction-qa-vision
description: >
  Closed coder↔Vision-QA loop for CEFR PDF→Markdown extraction defects.
  Use when the user runs /extraction-qa-vision, asks for vision QA on a page,
  extraction visual QA, callout/figure/soup defect loops, or "QA against PDF".
  Coding agent fixes; Vision critic returns structured pass/fail only (never code).
---

# extraction-qa-vision

Closed **coding agent ↔ Vision critic** loop for deterministic PDF→Markdown extraction defects (placement, soup, callouts, tables, IDs, formatting).

**Does not** invent extraction architecture, new element types, or a parallel PDF path. Sits on top of the existing inventory→extract→cleanup→merge→figures→format pipeline.

Before any extract/format change, still follow project entry rules: read `STATUS.md`; for design, `docs/ARCHITECTURE.md` / `docs/CONTRACTS.md`; for neighbors, C2-ADJ.

Before inventing a new coding fix for a defect class, run **resolved-issue matching**:  
[`docs/RESOLVED_ISSUE_MATCH_PROTOCOL.md`](../../../docs/RESOLVED_ISSUE_MATCH_PROTOCOL.md) +  
[`docs/RESOLVED_EXTRACTION_ISSUES.md`](../../../docs/RESOLVED_EXTRACTION_ISSUES.md)  
(CLEAR → auto-apply; AMBIGUOUS → ask once; NOVEL → fix then append RIE).

---

## When to load

Load this skill when:

- User runs `/extraction-qa-vision` or asks for **vision QA**, **QA against PDF**, or **extraction visual QA**
- Fixing callout placement, figure soup, prose merge, table ID/blank-row, page-caption glue, or similar **deterministic** defects from issue logs
- After a meaningful MD/pipeline fix for an open visual bug and you need a structured pass/fail
- **User files a debug log and directs Vision QA / this skill** — mandatory (see binding rule below)

Do **not** use for open product redesign, or as a substitute for `adjacent_guard` / `contract_validators`.

---

## Binding rule — user-reported pages (do not ignore)

When the user reports bugs in a log (or chat) **and** directs Vision QA / this skill:

1. **Enumerate every page number** the user named (and every defect class they listed). That list is the **mandatory work queue**.
2. **Baseline Vision QA every page in that list** (full-page snapshot + MD slice + invariants). No exceptions for “P3”, “later”, “sample only”, or “assumed fixed”.
3. **Do not cancel, deprioritize, or skip** a user-named page because another page is “more interesting.” Reorder for efficiency only after **all** pages have at least a baseline QA YAML on record.
4. **Page chrome is in scope** — running headers/footers (e.g. `Key aspects… ▶ Page 29` vs bare `Page **29**`) are visual defects the critic must catch. Full-page PNG exists so the agent cannot claim “not looking at footer.”
5. Claiming “not re-proven” after the user already pointed at the MD vs PDF is a **process failure**, not a status.

If the coding agent finishes a “Vision QA log run” without baseline YAML for every user-named page, the run is incomplete.

---

## Roles

| Role | May | Must not |
|------|-----|----------|
| **Coding agent** | Fix pipeline/MD; produce/reuse snapshots; invoke Vision QA; run gates; post-loop report | Claim fixed without pass + gates; regenerate snapshots every iteration; **skip user-named log pages** |
| **Vision QA (critic)** | Compare full-page PNG + MD slice + invariants; return YAML pass/fail | Suggest code; rewrite MD; design architecture; crop the page image |

Vision QA is a **pure observer**. See `references/qa-output-contract.md`.

---

## Loop protocol (max 4 fix attempts)

### Attempt counting (binding)

| Term | Definition |
|------|------------|
| **Baseline QA** | First Vision invocation **before any coding fix**. Does **not** consume a fix attempt. |
| **Fix attempt** | One coding fix (or batch of same-page fixes) **followed by** one Vision re-check on the **current** MD slice. |
| **Cap** | Maximum **4** fix attempts. If Vision still returns `status: fail` after the **4th** fix + re-check, **escalate** — do **not** start a 5th fix. |
| **Report `Attempts:`** | Number of **fix attempts** used (0 if baseline already `pass`; 1–4 otherwise). |

Typical sequence: baseline QA → (fail → fix #1 → re-slice → QA) → … → at most fix #4 → QA → pass or escalate.

### Steps

For each open issue (or same-page batch — see efficiency):

1. **Identify** page number(s) and element class from the bug report.
2. **Snapshot** full-page PNG once via `scripts/render_page_png.py` (reuse thereafter).
3. **Load** `references/extraction-invariants.md` and `references/qa-output-contract.md` (once per issue is enough; keep in context).
4. **Prepare current MD slice** — re-read `output/CEFR_Companion_Volume.md` and slice page N **now** (see Page Markdown slice). **Never** reuse a stale pre-fix slice for a later Vision invocation.
5. **Invoke Vision QA** with: full-page PNG + **current** MD slice + full invariants text. Demand YAML only per contract.
6. If `status: pass`:
   - If this was baseline (0 fixes) or any fix attempt → go to **After pass** (gates + report). Stop loop for this issue.
7. If `status: fail`:
   - If this was a re-check after fix attempt **4** → **escalate** (step 9). Do not start fix #5.
   - If fewer than 4 fix attempts have been completed → coding agent applies a fix **without** asking Vision for implementation advice. Count this as the next fix attempt (1…4).
   - **Before each coding fix attempt — resolved-issue match (mandatory):**
     1. Follow [`docs/RESOLVED_ISSUE_MATCH_PROTOCOL.md`](../../../docs/RESOLVED_ISSUE_MATCH_PROTOCOL.md).
     2. Open [`docs/RESOLVED_EXTRACTION_ISSUES.md`](../../../docs/RESOLVED_EXTRACTION_ISSUES.md); match Class / `rule_violated` / symptoms.
     3. **CLEAR** → auto-apply that entry’s **Re-apply steps** as this fix attempt (do not invent a parallel one-off when the ledger path applies). Do **not** ask the user.
     4. **AMBIGUOUS** → stop the silent loop for this issue; present ≤5-bullet comparison and ask the user **once** (this is not a Vision code suggestion).
     5. **NOVEL** → implement the smallest correct fix; after pass + gates, **append** a new RIE entry same session before claiming done.
     6. Emit a short **Investigation** note (pages, candidates, verdict, action) in the post-loop report.
8. After each fix: **re-slice current page MD (step 4)** → invoke Vision again (step 5) using the **same** snapshot file (do not regenerate unless `--force` is justified). Do **not** jump to step 5 with the old MD.
9. After the 4th fix still yields Vision `fail` → **escalate to user** with the post-loop report (do not silent-continue).

While inside the loop: do not stop for partial status theater; complete attempt → QA → next or escalate. Prefer **auto-apply CLEAR** ledger matches over inventing patches or questioning the user.

---

## Full-page snapshots (non-negotiable)

| Rule | Detail |
|------|--------|
| Full page only | Never crop the QA page image |
| Open bugs only | Generate PNG only for pages with an open defect |
| Reuse | Store and reuse exact file on later iterations |
| Path | `metadata/qa_snapshots/page_NNN.png` (zero-padded, e.g. `page_041.png`) |
| Scale | Fixed to project `pipeline.config.RENDER_SCALE` (**2.0**). Not a free per-run knob; changing scale requires intentional `--force` re-render and invalidates prior Vision judgments on that file. |
| Force | Regenerate only with `--force` (PDF change, corrupt/empty file — script also auto-rerenders tiny/invalid PNGs) |

### Produce / reuse

From workspace root:

```bash
python .grok/skills/extraction-qa-vision/scripts/render_page_png.py --page 41
```

- Uses `pipeline.config.PDF_PATH` or `CEFR Companion Volume_eng.pdf`
- Full-page `get_pixmap` at `RENDER_SCALE` (2.0); no clip
- If a **valid** `page_NNN.png` exists and no `--force`: prints path and exits 0 **without** regenerating
- Empty, tiny, or non-PNG files are treated as missing and re-rendered

```bash
python .grok/skills/extraction-qa-vision/scripts/render_page_png.py --page 41 --force
```

---

## Page Markdown slice

Deliverable: `output/CEFR_Companion_Volume.md`

Page markers are at the **END** of each page. Match `pipeline.adjacent_guard._page_body` / `contract_validators._page_body` exactly:

- Body for page **N** = content **after the previous** `<!-- page:… -->` marker in the file (the last `<!-- page:* -->` before `<!-- page:N -->`), **or** from file start if none, **until** `<!-- page:N -->`
- For a normal contiguous book this is the region after `<!-- page:N-1 -->` through `<!-- page:N -->`; if a marker is missing/out of order, still use **last preceding** marker, not a hard-coded N−1 assumption

**Every** Vision QA invocation must use a **fresh** slice from the deliverable on disk after any fix. Stale in-memory MD is a protocol bug (false fail/pass).

Hand Vision QA the slice for the page under review (not the entire book unless necessary for multi-page span context — prefer single page + note if multipage).

---

## Inputs to Vision QA (every invocation)

1. **Full-page PNG** — `metadata/qa_snapshots/page_NNN.png` (same file across attempts)
2. **Page MD slice** — **re-read and re-slice** from current deliverable (step 4)
3. **Full invariants** — entire `references/extraction-invariants.md`

Instruct the critic to return **only** YAML per `references/qa-output-contract.md`.

---

## After pass

1. Run:

```bash
python -m pipeline.adjacent_guard
python -m pipeline.contract_validators
```

2. Manually sanity-check before/after the fixed element (and page ±1) per C2-ADJ.
3. Emit the **post-loop report** (below).
4. Only then update STATUS / issue catalogs if claims change.

If gates fail after Vision `pass`, treat as not done — fix gate failures or re-open QA; do not claim resolved.

---

## Post-loop report (required)

After resolution **or** after 4 fix attempts still failing / escalation:

```markdown
## extraction-qa-vision report

- **Issue:** <short description>
- **Page + element:** <N> / <callout|prose-block|table|figure|…>
- **Attempts:** <0–4 fix attempts; baseline QA separate>
- **Snapshot:** metadata/qa_snapshots/page_NNN.png (reused: yes/no)
- **Matched:** RIE-xxx | none
- **Action:** auto-applied | asked user | novel
- **Investigation:** <one-liner: MD/PDF check + verdict>
- **Resolution:** <how fixed> | **Escalated:** <why user needed; last YAML failures summary>
- **Gates:** adjacent_guard <ok|fail>; contract_validators <ok|fail>
```

After a **novel** fix that passes Vision + gates: append a full entry to  
`docs/RESOLVED_EXTRACTION_ISSUES.md` (next free RIE id + index row) before claiming done.

---

## Hard constraints (project)

- Respect `AGENTS.md`, `STATUS.md`, `docs/CONTRACTS.md`, C2-ADJ
- **Resolved match before inventing patches** — CLEAR → auto-apply; never offload obvious re-apply to the user
- **Never** delete/rewrite bulk `metadata/rotated_from_grok/*.md` (88 vision tables)
- Do not invent element types beyond invariants / contract enums
- Prefer replace semantics over dual emit
- Do not mark fixed without gates + honest visual match
- Inventory rebuild alone does **not** fix garbled ids (see RIE-005 / L07-ID-REBUILD)

---

## Optional efficiency improvements

These must **never** override full-page snapshots, fresh MD slices, or pure-observer QA:

1. **Cache snapshots** — always reuse valid `page_NNN.png` across attempts and same-page bugs.
2. **Batch same-page defects** — one Vision pass can list multiple `failures[]` for one page; fix in priority order (critical → major → minor); still one re-slice before the re-check.
3. **Skip QA** only for pure typo edits with zero layout impact **and** user agreement; default is QA after meaningful layout/format fixes.
4. **Do not** use high-DPI region crops for this skill’s QA image (user: full-page only).
5. Existing `metadata/page_renders/` is **not** a substitute unless copied into `qa_snapshots` as the stable path for the loop.

---

## File map

```
.grok/skills/extraction-qa-vision/
  SKILL.md
  references/
    extraction-invariants.md
    qa-output-contract.md
    inventory-notes.md
  scripts/
    render_page_png.py

# Project protocol (coding agent; not Vision critic)
docs/RESOLVED_ISSUE_MATCH_PROTOCOL.md
docs/RESOLVED_EXTRACTION_ISSUES.md
```
