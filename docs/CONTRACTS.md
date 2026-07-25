# Extraction contracts — binding rules

**Companion to** [`ARCHITECTURE.md`](ARCHITECTURE.md) (design map) and [`STATUS.md`](../STATUS.md) (backlog).  
**These rules are source of truth for inventory → extract → assembly → validation.**  
Agents must not invent parallel layouts that violate them. User voice UV-01–UV-13 in STATUS §5a is product/process requirement, not optional commentary.

---

## 1. Pipeline control plane

```
inventory reading_order  →  extract (dispatch only)  →  cleanup  →  merge
  → apply_figures (attach assets / catalog bodies at captions)
  → post_process (format only; no reorder of page content)
  → contract_validators + adjacent_guard (fail closed)
```

| Layer | May do | Must not do |
|-------|--------|-------------|
| **Inventory** | Schedule every extractable element with type, order, bbox | Leave figures/callouts unscheduled if known |
| **Extract** | Implement each element type from RO | Rebuild full-page layout ignoring RO; dual-emit figure text + PNG |
| **apply_figures** | Insert PNG/text_diagram at matching caption / db:id; **delete** figure-label garbage under the block | Dump orphans at EOF; leave old figure-as-prose under PNG |
| **post_process** | Lists, headings, URL sanitize, blockquote normalize within lines | Drop paragraphs; reorder callout vs body; glue footnote to `Page **N**` |
| **Validation** | Fail closed on known regression classes **and adjacent damage** | Report green when C2-*/UV-*/neighbors still broken |

### Exclusive regions + replace semantics (C2-ADJ)

1. Each page region should be owned by **one** RO element (non-overlapping intent).
2. Fixing an element means **set** its representation, not **append** a second one (e.g. PNG replaces diagram text dump).
3. Global string rewrites must not join across footnote / page caption / figure / heading boundaries.
4. After any figure/callout/table change, run **`pipeline/adjacent_guard.py`** on affected pages before claiming resolved (log 04).

---

## 2. Inventory `reading_order` is SoT

1. Extract iterates `reading_order` **in order** and concatenates non-empty element outputs.
2. Every known figure on a page from `metadata/figures_registry.json` must appear as its own `figure` element (or as an **expanded** multi-element order stored in the inventory JSON — never a silent single `figure_page` that hides siblings).
3. Narrative blue boxes / sidebars must be typed **`callout`** (artifact or dedicated type), never `descriptor_scale`.
4. Side-column prose beside partial-width tables **or** callouts uses role `side` with x-bounded bbox; LTR interleave with the adjacent artifact.
5. `figures: []` in inventory is invalid when the registry has figures for that page — inventory must list them.
6. If geometry cannot detect a callout/box, use **agent-authored** `metadata/callouts_registry.json` (same idea as figures registry). Prefer judgment over brittle heuristics (UV-06).

### Element types

| Type | Extractor | Notes |
|------|-----------|-------|
| `prose` | `prose_zone`, `rich_page` | roles: intro \| side \| interstitial \| trailing \| body |
| `artifact` | table / rotated / section_block | `artifact_type`: descriptor_scale \| table \| **callout** \| section_block |
| `figure` | figure_ref / catalog / png stub | One registry figure per element |
| `figure_page` | **legacy sugar only** | If present, must expand to the same multi-element schedule as explicit RO before emit; multi-fig pages must not collapse to one id |
| `span_continuation_skip` | — | No multipage body re-emit |
| `footnote_zone` | geometry | Not vision |
| `footer` | page_footer | Markers + remaining footnotes |
| `toc` | toc_layout | Pages 5–9 |

---

## 3. Callout / sidebar / feature-box (UV-01, C2-CO1)

Blue-background narrative boxes (chapter reminders, plurilingual callouts, “Can do” boxes, etc.):

```markdown
> **Title**
>
> First paragraph…
>
> Second paragraph…
```

Rules:

- Title in the quote as `> **Title**` when the box has a title.
- Blank `>` between paragraphs.
- Preserve internal formatting (italics, bold, lists).
- Apply **document-wide** to the same visual class (not one page).
- Lead sentences must not remain glued to the preceding list item (C2-CO2).

---

## 4. Figures

| `render_as` | Contract |
|-------------|----------|
| `text_diagram` / `mermaid` | Catalog body from `figures_catalog.py` under `### Figure N – … \| id`. **Zero** flattened label soup outside fences. |
| `png` | Crop from registry; emit relative `assets/figures/{id}.png` under caption/db:id. Never EOF orphan without page context. |

- Multi-figure pages (e.g. 36, 40): all figure ids present in MD near their captions.
- Caption match uses only `Figure N – Title` form — never in-prose “Figure N, which…”.
- Crops must show the **full** diagram (UV-12). Finite set: invest in agent QA loop when fractions fail (UV-06). Fixing crops must not destroy working prose (UV-13).

---

## 5. Hyperlinks (C2-H1, C2-U1)

1. Read PDF link annotations (`page.get_links()`).
2. Merge multi-rect annotations that share the same URI (split titles).
3. Append parenthetical URL after the matching prose phrase when the URL is not already on the page (footnote).
4. Fuzzy-match longest anchor substring present in prose when full anchor fails.
5. **Sanitize** every `http(s)://…` token: strip internal whitespace (`https:// rm…` → `https://rm…`).
6. Do not invent HTML `<a>` tags.

---

## 6. Tables and cells

| Rule | Detail |
|------|--------|
| Numbered tables | `type=table`, stable `table_NN_…` id — not `scale_*` from first column |
| Callout tables | Single-column narrative → callout emit, not scale |
| Empty tables | **Do not emit** empty / whitespace-only markdown tables |
| Cell `<br>` (UV-11) | Separate **phrases**, not mid-phrase soft wraps. Prefer join soft wraps with space; use geometry gap or agent judgment when ambiguous |

---

## 7. Prose zones

- Intro / interstitial / trailing relative to table **and** callout bboxes.
- Side zones: x-filter lines so table/callout text is not interleaved into the opposite column.
- Trailing prose stops at first footnote / page-marker band (`first_footer_band_y`).
- Same layout class (top callout + multi-column body) must use the **same code path** on every page (UV-07) — e.g. p.31 and p.35.

---

## 8. Validation fail-closed (C2-V1, UV-03, UV-04)

`pipeline/contract_validators.py` (and merge/output hooks) must exit non-zero when any high-severity gate fails.

| Gate | Intent |
|------|--------|
| V-FIG-SOUP | No label soup after text_diagram fences |
| V-FIG-MULTI | Multi-fig pages include all registry ids |
| V-FIG-PNG-LOC | PNG lines near matching db:id |
| V-CALLOUT-FMT | Known callouts use blockquote title form |
| V-CALLOUT-LEAD | p.30 plurilingual lead not glued to list |
| V-ORDER-31 | Callout/top content before main body golden phrase |
| V-LINK-GUIDE | Guide title near CoE URL |
| V-URL-SPACE | No spaces inside URL tokens |
| V-EMPTY-TABLE | No empty junk tables |
| V-TABLE-ID | Table 3 not mis-typed as scale |
| V-PROSE-MASS | Figure pages keep prose mass |

**Policy:** Do not mark STATUS C2-* / UV-* **resolved** unless the gate that would have failed on the broken build is green.

---

## 9. Agent-in-the-loop triggers (UV-06)

Stop stacking heuristics and open agent/vision judgment when:

- Callout bounds not detected as tables (drawings only)
- Figure PNG crop still wrong after registry tweak
- Cell phrase breaks ambiguous from geometry alone
- Inventory RO and visual PDF order still disagree after rebuild

Pattern: same as rotated tables — prepare evidence, agent writes authoritative metadata/markdown, extract assembles.

---

## 10. Logging user feedback

Per `AGENTS.md` and STATUS standing rule: log **everything** the user writes (product, process, trust, design), not only code defects. Mirror in STATUS §5a and ISSUES diagnosis.
