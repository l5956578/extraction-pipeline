# Extraction invariants (QA single source of truth)

**Scope:** rules Vision QA and the coding agent use when judging PDF page vs Markdown.  
**Source:** consolidated from `docs/CONTRACTS.md`, `docs/ADJACENT_ELEMENT_PROTECTION.md`, `STATUS.md`, `metadata/figures_handling.md`, `metadata/ROTATED_TABLES_AGENT_VISION.md`, `AGENTS.md`.  
**Do not invent** new element types or parallel architecture.

Short IDs in `rule_violated` fields should use the **rule-id** tokens in backticks below.

---

## Pipeline / trust

| rule-id | Invariant |
|---------|-----------|
| `inventory-ro-sot` | Inventory `reading_order` is the extract source of truth; do not invent a parallel layout path. |
| `replace-semantics` | Correct representation **replaces** the old one; do not layer PNG/blockquote on leftover dual emit. |
| `adjacent-protection` | Fixing one element must not trash neighbors (garbage under PNG, glued `Page **N**`, dropped headers, duplicate titles). |
| `gates-before-claim` | Do not claim fixed without `python -m pipeline.adjacent_guard` and `python -m pipeline.contract_validators` green (plus visual check of neighbors). |
| `no-false-resolved` | Green mass-only checks ≠ fixed when visual/PDF still wrong (trust / UV-04). |

---

## Callouts / sidebars (UV-01)

| rule-id | Invariant |
|---------|-----------|
| `callout-format-uv01` | Narrative blue boxes use blockquote form: `> **Title**`, blank `>` between paragraphs; preserve bold/italics/lists inside. |
| `callout-placement-top-left` | Callout in top-left of page → emit first in page order (before main body). |
| `callout-placement-end-body` | Callout not top-left → default end of body, before footnotes (when multi-col / sidebar layout applies). |
| `callout-placement-inline-fullwidth-neighbors` | When callout is **not** top-left **and** immediate before/after neighbors are full-width prose (no multi-column region before and after the box) → place **inline** in flow, not forced to bottom. |
| `callout-top-fullwidth-stay` | Full-width callout already at top stays at top; do not force inline. |
| `callout-lead-not-glued` | Callout lead sentence must not remain glued to the preceding list item. |
| `callout-not-scale` | Callouts are not `descriptor_scale`; use callout type / blockquote emit. |
| `callout-formatting-preserved` | Internal callout formatting (paragraphs, emphasis) must not be lost as one soup line. |

---

## Prose

| rule-id | Invariant |
|---------|-----------|
| `prose-purity` | Prose blocks stay pure body text; do not merge adjacent independent prose blocks into one, or split mid-sentence with fences incorrectly. |
| `prose-no-heading-glue` | Section titles must not glue to the prior paragraph; headings on their own lines. |
| `prose-mass-retained` | Figure/callout fixes must not delete working body prose on the same page. |
| `missing-lead-content` | Moving/reordering elements must not drop leading sentences of the element or neighbors. |

---

## Figures

| rule-id | Invariant |
|---------|-----------|
| `no-figure-soup` | No trash soup after figures (orphaned headings, scale/axis/level labels, flattened diagram text under PNG or outside text_diagram fences). |
| `figure-replace-not-layer` | PNG / text_diagram replaces figure-as-prose; dual emission is a defect. |
| `figure-multi-ids` | Multi-figure pages include all registry figure ids near matching captions. |
| `figure-caption-form` | Caption match is `Figure N – Title` form (or `### Figure N – … \| id`); not in-prose “Figure N, which…”. |
| `figure-png-location` | PNG markdown lines near matching `<!-- db:id=… -->` / caption — not EOF orphans without page context. |
| `figure-crop-full` | Crop quality (full diagram) is a product concern; Vision QA may flag obvious crop truncation when visible on full page. |

---

## Tables / IDs

| rule-id | Invariant |
|---------|-----------|
| `table-id-clean` | Table artifact IDs and headers are clean (`table_NN_…`); no garbled leftovers (e.g. reversed gibberish, wrong `scale_*` for numbered tables). |
| `table-blank-after-header` | Markdown tables require a **blank line** after the element/id comment (and caption) block so renderers produce actual columns. |
| `table-no-empty` | Do not emit empty / whitespace-only markdown tables. |
| `table-cell-br-phrases` | Cell `<br>` separates phrases, not mid-phrase soft wraps. |

---

## Footnotes / page chrome

| rule-id | Invariant |
|---------|-----------|
| `footnote-not-glued-page` | Footnotes must not glue to `Page **N**` / page caption. |
| `page-caption-blank` | Blank line before page caption / `Page **N**` as required by format gates. |
| `page-caption-running-head` | Visible caption must match the PDF running head form: chapter title pages use `*Chapter title ▶ Page **N***` (e.g. Key aspects…), not a bare `Page **N**` when the PDF shows a chapter line. Even pages often use `*Page **N** ▶ **CEFR – Companion volume***`. |
| `page-marker-once` | One `<!-- page:N -->` end-marker per page; markers at end of page body. |
| `footnote-ownership` | Footnotes belong to the page’s footnote band; prose must stop above the footnote band. |

---

## Hyperlinks / URLs

| rule-id | Invariant |
|---------|-----------|
| `url-no-internal-space` | No spaces inside `http(s)://…` tokens. |
| `url-attach-anchor` | Parenthetical URLs attach after the matching prose phrase/title when that is the document pattern; do not invent HTML `<a>`. |
| `url-not-glue-footnote` | URL sanitize must not glue the next footnote number onto the URL. |

---

## Rotated tables (do not break)

| rule-id | Invariant |
|---------|-----------|
| `rotated-vision-path` | Rotated scales use `metadata/rotated_from_grok/{slug}.md`; do not wipe or mass-rewrite the 88 vision files in this QA skill. |
| `rotated-footnotes-geometry` | Footnotes on rotated pages stay on geometry path, not vision rewrite of the whole page. |

---

## Element types (existing only)

Allowed types to reference in QA `element` field (no new inventions):

`callout` | `prose-block` | `table` | `figure` | `figure-caption` | `footnote` | `page-caption` | `other`

Inventory-side names (`prose`, `artifact`, `figure`, `footnote_zone`, `footer`, `toc`) map into the above for QA reporting.

---

## Severity guidance (for Vision QA)

| severity | When |
|----------|------|
| `critical` | Missing major content, wrong element type that breaks ETL, dual figure emission / heavy soup, broken table structure (no columns), callout entirely wrong place with body loss |
| `major` | Placement wrong but content present; formatting loss; ID wrong but content ok; URL broken; neighbor glue |
| `minor` | Soft hyphens, bold spacing glitches, residual punctuation/OCR noise that does not change meaning |

---

## Out of scope for this QA loop

- Product redesign of the pipeline architecture
- Cropping the **QA full-page snapshot** (never)
- Using chat/web Grok as a pipeline extract step
- Treating `docs/archive/**` as current requirements
