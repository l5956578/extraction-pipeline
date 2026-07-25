# Resolved extraction issues (re-apply ledger)

**Role:** Playbook for **fixed, re-applicable** defect classes.  
**Not:** Open backlog (that is [`../STATUS.md`](../STATUS.md)).  
**Protocol:** [`RESOLVED_ISSUE_MATCH_PROTOCOL.md`](RESOLVED_ISSUE_MATCH_PROTOCOL.md) — investigate → match → CLEAR auto-apply / AMBIGUOUS ask / NOVEL fix+append.

### Rules for this file

1. Entries are written only after a fix is **evidence-backed** (gates green; visual if applicable).
2. Each entry must be specific enough that a future agent can act **without the user**.
3. Prefer chunk-local re-apply (`iterate_format.py` or re-extract one chunk) over full-book rebuild.
4. Cross-link adjacency package history in [`ADJACENT_ELEMENT_PROTECTION.md`](ADJACENT_ELEMENT_PROTECTION.md) when relevant — do not fork that ledger.
5. On every **novel** successful fix: append a new `RIE-NNN` and update the index.

### Apply surfaces (vocabulary)

| Surface | Meaning |
|---------|---------|
| `postprocess` | `pipeline/post_process.py` / `python iterate_format.py` |
| `extract+RO` | Rebuild inventory reading_order and/or re-extract chunk |
| `title_fix` | `pipeline/title_fix.py` (+ often postprocess rewrite) |
| `figure_inject` | `apply_figures` / extract figure soup strip |
| `utils` | Shared sanitize/repair helpers |

---

## Index (scan first)

| RIE | Class / rule_ids (short) | Symptoms (one line) | Surface |
|-----|--------------------------|---------------------|---------|
| [RIE-001](#rie-001--odd-page-running-head-collapsed-to-bare-page-n) | `page-caption-running-head` | Odd pages bare `Page **N**` vs chapter title in PDF | postprocess + page_layout |
| [RIE-002](#rie-002--callout-placement-inline--top-fullwidth) | `callout-placement-inline-fullwidth-neighbors`, `callout-top-fullwidth-stay` | Callout forced to bottom or wrong top placement | extract+RO |
| [RIE-003](#rie-003--callout-step-n-collapsed-formatting) | `callout-formatting-preserved`, `callout-format-uv01` | Step 1–N callout one soup line | postprocess |
| [RIE-004](#rie-004--figure--text_diagram-label-soup) | `no-figure-soup`, `figure-replace-not-layer` | Dual-emit labels under PNG / after ``` fence | figure_inject + postprocess |
| [RIE-005](#rie-005--garbled-reversed-tokens-in-ids--captions) | `table-id-clean` | `cfiiceps`, `smargaid`, reversed scale titles | title_fix + postprocess |
| [RIE-006](#rie-006--missing-blank-line-before-markdown-tables) | `table-blank-after-header` | Table renders as prose (no blank before `\|`) | postprocess |
| [RIE-007](#rie-007--footnotes-glued-after-url-sanitize) | `footnote-not-glued-page` | `…url.24.ALTE` or multi-fn on one line | utils + postprocess |
| [RIE-008](#rie-008--progressive-band-callout-garbage-p41-class) | `callout-formatting-preserved`, `replace-semantics` | Progressive blue-band dups / garbage in callout body | postprocess (+ extract) |

---

## Entry template (copy for new RIE)

```markdown
### RIE-NNN — short machine-friendly title

| Field | Content |
|-------|---------|
| **Class / rule_ids** | … |
| **Symptoms** | … |
| **Root cause** | … |
| **Fix location** | … |
| **Apply surface** | … |
| **Chunks/pages verified** | … |
| **Match criteria (CLEAR)** | … |
| **Ambiguous if** | … |
| **Re-apply steps** | 1. … |
| **Do not** | … |
| **Related STATUS IDs** | … |
| **Date resolved** | YYYY-MM-DD |
```

---

## Entries

### RIE-001 — odd-page running head collapsed to bare Page N

| Field | Content |
|-------|---------|
| **Class / rule_ids** | `page-caption-running-head`, `page-caption-blank` |
| **Symptoms** | PDF shows chapter running head (e.g. `Key aspects of the CEFR for teaching and learning ▶ Page 29`); MD shows bare `Page **29**` or caption `*` split onto its own line. Even pages may need `*Page **N** ▶ **CEFR – Companion volume***`. |
| **Root cause** | `_normalize_page_marker_caption` matched only plain digits; markers often arrive as `Title ** Page **29**` (bold around digits), so chapter titles collapsed to bare page. |
| **Fix location** | `pipeline/page_layout.py::_normalize_page_marker_caption` (bold-stripped structural match); `pipeline/post_process.py::_resync_page_captions_from_pdf` (rewrite visible captions from PDF zones); `_ensure_blank_before_page_captions` (do not split `*Page`) |
| **Apply surface** | `postprocess` (also correct at extract footer emit) |
| **Chunks/pages verified** | Chapter 2 odd pages (e.g. 29, 41, …); log 07 L07-ODD-CAPTION; L05-PAGE-AST |
| **Match criteria (CLEAR)** | Visible line immediately before `<!-- page:N -->` is bare `Page **N**` / wrong form while PDF footer/running head has chapter or book-title form; same normalizer path already in tree. |
| **Ambiguous if** | Caption is intentionally bare in PDF; or non-CEFR chrome layout; or marker missing entirely (different defect). |
| **Re-apply steps** | 1. Confirm code paths above still present. 2. `python iterate_format.py` (runs postprocess + PDF resync). 3. Spot-check MD caption for the reported page(s). 4. Run gates. 5. Vision QA full-page if user-named or chrome was the failure. |
| **Do not** | Skip user-named pages (e.g. p.29) because “assumed fixed”. Claim “inventory rebuild fixes captions.” Touch `rotated_from_grok`. |
| **Related STATUS IDs** | L07-ODD-CAPTION, L05-PAGE-AST |
| **Date resolved** | 2026-07-20 |

---

### RIE-002 — callout placement inline / top-fullwidth

| Field | Content |
|-------|---------|
| **Class / rule_ids** | `callout-placement-inline-fullwidth-neighbors`, `callout-top-fullwidth-stay`, `callout-placement-top-left`, `callout-placement-end-body` |
| **Symptoms** | Mid-page full-width callout forced to bottom of page when neighbors are full-width prose (no multi-col); or top full-width callout moved to end-body; or top-left callout not first. |
| **Root cause** | Reading-order placement must classify: top-left → first; top full-width → first; mid full-width + no side column → **inline by y**; else multi-col/sidebar → end-body before footnotes. |
| **Fix location** | `pipeline/page_elements.py::_callout_mixed_order` (placement branches); inventory rebuild for affected pages then re-extract; callout detect/emit for body text |
| **Apply surface** | `extract+RO` |
| **Chunks/pages verified** | p.41 inline (L05-P41-CO); p.43 top_fullwidth (L07-P43); p.30–31 top-left / multi-col path (C2-CO2, C2-R1) |
| **Match criteria (CLEAR)** | Same placement class as a verified page: measure blue box + whether page has side-column prose; RO policy already matches `_callout_mixed_order` rules; only this page’s inventory/extract is stale. |
| **Ambiguous if** | True multi-column sidebar (end-body may be correct); callout is not a blue narrative box; placement conflicts with two different verified patterns on one page; would require rewriting rotated tables. |
| **Re-apply steps** | 1. Inspect inventory `reading_order` for the page and PDF blue-box geometry. 2. Rebuild inventory for the chunk (or page range) if RO wrong. 3. Re-extract that chunk only (e.g. chunk_02 for Ch.2). 4. Merge/figures/postprocess as usual for that path. 5. Gates + Vision on that page. Prefer **not** full-book unless many chunks stale. |
| **Do not** | Hand-edit only the final MD placement without fixing RO if re-extract will wipe it. Ask the user which placement rule to use when PDF geometry clearly matches an existing branch. Wipe `rotated_from_grok`. |
| **Related STATUS IDs** | L05-P41-CO, L07-P43, C2-CO2, C2-R1 |
| **Date resolved** | 2026-07-19 |

---

### RIE-003 — callout Step N collapsed formatting

| Field | Content |
|-------|---------|
| **Class / rule_ids** | `callout-formatting-preserved`, `callout-format-uv01` |
| **Symptoms** | Callout with “Step 1:” … “Step 4:” collapsed to one blockquote line; title not bolded; lost blank `>` between steps. |
| **Root cause** | Extract/postprocess joined step runs; need expand into multi-line blockquote. |
| **Fix location** | `pipeline/post_process.py` — L07 p.42/43 Step N expand (search `Step 1:` / multi-step expand in `_repair_log05_markdown` region ~1512+) |
| **Apply surface** | `postprocess` |
| **Chunks/pages verified** | p.42 (L07-P42-CO); p.43 step callout (L07-P43) |
| **Match criteria (CLEAR)** | Blockquote region contains multiple `Step N:` tokens on one or few lines; same postprocess expand already in tree. |
| **Ambiguous if** | “Steps” are body prose lists outside a callout; or PDF has a different structure (numbered list without Step labels). |
| **Re-apply steps** | 1. Confirm expand logic present. 2. `python iterate_format.py`. 3. Check MD blockquote for Steps. 4. Gates; Vision if user-directed. |
| **Do not** | Invent a new callout type. Ask whether to expand when CLEAR. |
| **Related STATUS IDs** | L07-P42-CO, L07-P43 |
| **Date resolved** | 2026-07-20 |

---

### RIE-004 — figure / text_diagram label soup

| Field | Content |
|-------|---------|
| **Class / rule_ids** | `no-figure-soup`, `figure-replace-not-layer`, `adjacent-protection` |
| **Symptoms** | After PNG or after closing ``` of text_diagram: orphaned axis/level/competence labels, duplicate sample tables, flattened “Relaying Facilitating…” soup before `el:end`. |
| **Root cause** | Dual emission: figure inject adds correct form without fully removing figure-as-prose / leaf labels. |
| **Fix location** | `pipeline/extract_chunk.py::_strip_figure_diagram_soup`; `pipeline/apply_figures.py` replace-not-layer pass; `pipeline/post_process.py` L07 p.38 A2 dedupe under fig 6, p.90 mediation soup strip after ```, R1 leaf soup after §3.1 |
| **Apply surface** | `figure_inject` + `postprocess` |
| **Chunks/pages verified** | p.38 A2 under fig 6 (L07-P38-SOUP); p.90 mediation diagram (L07-P90-SOUP); C2-F1/F2 figure soup gates |
| **Match criteria (CLEAR)** | Soup tokens match known dual-emit patterns under a figure/diagram that already has the correct PNG or fence representation; strip/replace path exists. |
| **Ambiguous if** | Soup is actually body prose the user wants kept; crop is wrong (C2-F3 product issue — not strip); multi-figure page where wrong region would be deleted. |
| **Re-apply steps** | 1. Identify figure id and whether PNG or text_diagram is canonical. 2. Prefer running figures apply + `iterate_format.py` so strip passes run. 3. If extract-level dual emit remains, re-extract that chunk after confirming strip helpers. 4. Gates (`V-FIG-SOUP` / adjacent_guard). 5. Vision full-page. |
| **Do not** | Layer a second PNG on leftover prose. Delete neighbor body prose. Mark C2-F3 crop “resolved” without user confirm. |
| **Related STATUS IDs** | L07-P38-SOUP, L07-P90-SOUP, C2-F1, C2-F2 |
| **Date resolved** | 2026-07-20 |

---

### RIE-005 — garbled reversed tokens in ids / captions

| Field | Content |
|-------|---------|
| **Class / rule_ids** | `table-id-clean` |
| **Symptoms** | Artifact ids/captions contain reversed garbage: `cfiiceps` (specific), `smargaid` (diagrams), `shparg` (graphs), `gnittup` (putting), `cilbup` (public), `collaborating_ni_a_group`, etc. |
| **Root cause** | Rotated/span title bugs; inventory slugs inherit bad tokens. **Inventory rebuild alone does not fix** — rebuild still produced `cfiiceps` in inventory (L07-ID-REBUILD). |
| **Fix location** | `pipeline/title_fix.py` — `_GARBLED_TOKEN_FIX`, `fix_rotated_title`, `preferred_display_title`, `artifact_id_from_title`; `pipeline/post_process.py` — token map + **`_resync_artifact_ids_from_fixed_titles`** (re-derive id from fixed ### title and/or nearby table title row; table body untouched); `pipeline/utils.py::artifact_header` re-slugs garbled ids at emit |
| **Apply surface** | `title_fix` + `postprocess` (+ emit on re-extract) |
| **Chunks/pages verified** | p.64 putting a case; p.65 public announcements; p.110 collaborating in a group; book-wide token map (L07-ID); L07-ID-REBUILD |
| **Match criteria (CLEAR)** | Header or id still has known reverse tokens **or** ### title is clean while `\| id` is garbled (re-derive from title/table title). |
| **Ambiguous if** | New unknown garble not in maps (extend maps carefully); wrong id class (e.g. table typed as scale for content reasons — different RIE/STATUS). |
| **Re-apply steps** | 1. Grep MD for known bad tokens / mismatched ### title vs id. 2. Prefer `python iterate_format.py` (resync from fixed titles). 3. If inventory still garbled after MD is clean: re-slug needs re-extract **after** title_fix maps — **not** rebuild alone. 4. Gates. |
| **Do not** | **Claim inventory rebuild alone fixed garbled slugs.** Wipe rotated vision bodies. Rewrite table body cells when only header/id is wrong. |
| **Related STATUS IDs** | L07-ID, L07-ID-REBUILD, R3 |
| **Date resolved** | 2026-07-20 |

---

### RIE-006 — missing blank line before markdown tables

| Field | Content |
|-------|---------|
| **Class / rule_ids** | `table-blank-after-header` |
| **Symptoms** | Markdown table does not render as columns because `\|` header follows `### … \| id` or `<!-- el:start … -->` with no blank line. |
| **Root cause** | Emit/postprocess omitted required blank after header/el fence before table. |
| **Fix location** | `pipeline/post_process.py` — regex insert blank after `### …\| …` and after `<!-- el:start type=artifact id=scale_… -->` before `\|` |
| **Apply surface** | `postprocess` |
| **Chunks/pages verified** | L07-TABLE-BLANK (scale/table header blocks book-wide) |
| **Match criteria (CLEAR)** | Pattern `### …\| id\n\|` or `el:start…\n\|` without blank line; postprocess insert present. |
| **Ambiguous if** | Non-table pipe use in prose; intentional tight fences in a golden that already has blank elsewhere. |
| **Re-apply steps** | 1. Confirm postprocess regexes present. 2. `python iterate_format.py`. 3. Spot-check page. 4. Gates. |
| **Do not** | Ask user to insert blank lines by hand as the primary fix. |
| **Related STATUS IDs** | L07-TABLE-BLANK |
| **Date resolved** | 2026-07-20 |

---

### RIE-007 — footnotes glued after URL sanitize

| Field | Content |
|-------|---------|
| **Class / rule_ids** | `footnote-not-glued-page`, `page-caption-blank` (neighbor) |
| **Symptoms** | URL sanitize glues next footnote: `…/1680667a2d.24.ALTE` or multiple `N. Author` footnotes on one line after a CoE URL; missing blank before `Page **N**`. |
| **Root cause** | URL join heuristics reattached trailing `N.Title` as path continuation; need split rules + line repair. |
| **Fix location** | `pipeline/utils.py::sanitize_urls_in_text` (L05-FN-GLUE splits); `pipeline/utils.py::repair_glued_footnotes`; invoked from postprocess (`post_process.py` format path) |
| **Apply surface** | `utils` + `postprocess` |
| **Chunks/pages verified** | Footnotes 23–26 class; p.27 URL footnotes (L05-FN-GLUE); CoE links on intro pages |
| **Match criteria (CLEAR)** | URL immediately followed by `.N.` or mid-line `N. Capital` after URL; helpers already in tree. |
| **Ambiguous if** | Intentional decimal in URL path that is not a footnote; non-footnote prose after URL that looks like `N. Title`. |
| **Re-apply steps** | 1. Confirm sanitize + repair helpers. 2. `python iterate_format.py`. 3. Check footnote lines + blank before page caption. 4. Gates (adjacent_guard footnote–page blank). |
| **Do not** | “Fix” by deleting footnotes. Break adjacent page captions (C2-ADJ). |
| **Related STATUS IDs** | L05-FN-GLUE, L05-P32-LINK (related URL placement) |
| **Date resolved** | 2026-07-17 |

---

### RIE-008 — progressive-band callout garbage (p.41-class)

| Field | Content |
|-------|---------|
| **Class / rule_ids** | `callout-formatting-preserved`, `replace-semantics`, `callout-format-uv01` |
| **Symptoms** | Progressive blue-band callout emits duplicated/garbage bands; p.41 research-project callout should be clean 3-phase (Intuitive / Qualitative / Quantitative) blockquote. |
| **Root cause** | Progressive stack detection kept overlapping bands; format pass replaces known broken `callout_p041_0` body with clean text when signature strings present. |
| **Fix location** | `pipeline/callout_detect.py` progressive stack handling; `pipeline/post_process.py` clean_p41 replace for `callout_p041_0` |
| **Apply surface** | `postprocess` (page-specific safety net) + `extract` (detect) |
| **Chunks/pages verified** | p.41 L06-P41 |
| **Match criteria (CLEAR)** | Same callout id / same progressive research-project text on p.41 (or exact same dual-band garbage pattern the clean replace targets). |
| **Ambiguous if** | Different progressive callout on another page (need general detect fix, not p.41 hardcode); user wants different paragraph split than clean_p41. |
| **Re-apply steps** | 1. If p.41-class: `python iterate_format.py` to apply clean replace. 2. If another page with progressive garbage: prefer improving `callout_detect` progressive logic + re-extract chunk — treat as **AMBIGUOUS** or **NOVEL** if not p.41 hardcode. 3. Gates + Vision. |
| **Do not** | Blindly copy clean_p41 text onto a different callout. Layer blockquote on leftover soup without replace. |
| **Related STATUS IDs** | L06-P41 |
| **Date resolved** | 2026-07-19 |

---

## Maintaining this ledger

| Event | Action |
|-------|--------|
| Novel fix passes gates (+ Vision if visual) | Append next `RIE-NNN`; update Index |
| Fix improved but same class | Update existing entry (Fix location, Re-apply steps, pages verified) — do not create a duplicate class without reason |
| STATUS marks item open again | Keep RIE for re-apply history; fix STATUS; do not delete RIE without cause |
| Related to neighbor damage | Link `ADJACENT_ELEMENT_PROTECTION.md` in entry notes |

**Next free id:** RIE-009
