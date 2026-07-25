# Fix-layer audit (log 01 → log 07)

**Date:** 2026-07-20  
**Purpose:** For every reported fix since log 01, state whether it is **root** (inventory / extract / emit) or **late polish** (postprocess / format), and whether it must be **promoted earlier**.

**Pipeline layers (near → far from PDF):**

| Layer | When | Files (examples) |
|-------|------|------------------|
| **L1 inventory** | RO / types | `inventory.py`, `page_elements.py`, `callout_detect.py` |
| **L2 extract** | Per-page MD emit | `extract_chunk.py`, `page_layout.py`, `id_registry.py` |
| **L3 figures** | Inject / replace | `apply_figures.py`, `figure_inject.py` |
| **L4 postprocess** | Whole-book format | `post_process.py`, `prose_format.py`, `utils.py` |
| **L5 gates** | Fail-closed checks | `adjacent_guard.py`, `contract_validators.py` |

**Legend**

| Tag | Meaning |
|-----|---------|
| **ROOT** | Fix lives at L1–L3; re-extract reapplies it |
| **POLISH** | Fix lives at L4; survives only if format runs after merge |
| **HYBRID** | Root exists + polish safety net (or partial both) |
| **PAGE** | Hardcoded to one page / string (not general) |
| **PATTERN** | Regex/class over whole book (general) |
| **PROMOTE** | Should move or strengthen nearer the root |
| **OK as polish** | Legitimate post-emit formatting (or acceptable safety net) |

---

## 1. Executive summary (read this first)

| Class | Root or polish? | After full re-extract? | Night-risk? |
|-------|-----------------|------------------------|-------------|
| **Callout placement** (inline / top / end) | **ROOT** (`_callout_mixed_order`) | Re-applied if inventory+extract use current code | Low if RO rebuild runs |
| **Callout body title/paras** (p.27, p.35 splits) | **HYBRID** (detect forced splits + polish) | Root path should help; polish still re-applies | Medium |
| **Callout Steps formatting** (p.42–43) | **POLISH** (pattern expand) | Needs format pass | Medium unless emit fixed |
| **p.41 progressive garbage** | **POLISH PAGE** (hardcoded replace) | **Will not fix other progressive boxes** | **High for similar pages** |
| **Figure soup / dual emit** | **HYBRID** (strip at extract/figures + polish) | Mostly re-applied | Medium residual edges |
| **Garbled scale ids** | **HYBRID** (title_fix at emit + polish resync) | MD fixed by polish; inventory clean only with re-slug path | Medium for inventory |
| **Page captions / running head** | **HYBRID** (normalize at emit + PDF resync polish) | Both layers help | Low |
| **URL sanitize / FN glue** | **HYBRID** (utils used in extract+format) | OK if both paths call sanitize | Low |
| **Many log 05 one-string patches** | **POLISH PAGE/PATTERN** | Still run at format; **not** fixed “at source” | High if format skipped |

**Your fear, answered:**  
Placement is **not** “only reported pages.”  
Lost **titles/formatting inside callouts** is **partly polish** — some general, some **page-hardcoded**. Those need root promotion if you want re-extract alone to be enough.

---

## 2. Callouts (your immediate question)

| ID | What you saw | Where fixed | Layer | General? | Promote to root? |
|----|--------------|-------------|-------|----------|------------------|
| **C2-R1 / C2-CO2** | p.30–31 order / incomplete plurilingual | Blue-fill RO + extract emit | **ROOT** | Yes (geometry) | Already root |
| **L05-P41-CO** | Mid-page callout forced bottom | `_callout_mixed_order` inline branch | **ROOT** | Yes | Already root |
| **L07-P43** | Top full-width not at top | `_is_top_fullwidth_callout` + RO | **ROOT** | Yes | Already root |
| **L05-P27-CO** | Title/body 3 paras not 1 | `callout_detect` forced splits **and** polish copy | **HYBRID** | Partial (known text) | Strengthen detect para logic; drop polish when stable |
| **L05-P35-CO** | Can-do 2 paras | Same forced split in detect + polish | **HYBRID** | Partial | Same |
| **L05-P37** | Title “Background… levels” | Polish title rejoin + list glue | **POLISH** (+ some emit) | Pattern-ish | Emit title from first band correctly |
| **L07-P42-CO** | Step 1–4 collapsed | `_expand_step_callout` in post_process | **POLISH PATTERN** | Yes (Step N:) | **PROMOTE:** emit callout with paragraph breaks from PDF textbox |
| **L06-P41** | Progressive-band garbage | Hardcoded `clean_p41` body replace | **POLISH PAGE** | **No** | **PROMOTE urgently:** progressive keep-longest already in detect; make emit use full textbox + real paras — delete page hardcode |
| **L07-P43 lead** | “Very often…” missing | Polish string restore | **POLISH PAGE** | No | Extract must not drop lead prose |
| **C2-CO1 / UV-01** | Blockquote form all callouts | `emit_callout_blockquote` + polish expand | **HYBRID** | Yes | Root emit already aims for this; polish is safety net |
| **Title glue / dup titles** | Title repeated after `> **Title**` | `_dedupe_callout_title_lines`, `_split_glued_title` | **HYBRID** | Yes | Prefer detect split at emit only |

**Bottom line for callouts**

| Concern | Verdict |
|---------|---------|
| “Inline vs top vs bottom only fixed on pages I reported” | **False** for placement — root classifier is book-wide |
| “Lost formatting/titles will stay wrong elsewhere after re-extract” | **True risk** for **Step collapse**, **progressive garbage**, and **string-level** body fixes unless root emit is improved |
| Will full re-extract alone fix p.41-class progressive mess on other pages? | **No** — only the hardcoded p.41 polish (and detect progressive longest, which may still be one blob) |

---

## 3. Full fix register (log 01–07 era)

### 3.1 Placement / structure / adjacency (mostly root)

| ID | Symptom | Primary code | Layer | Promote? |
|----|---------|--------------|-------|----------|
| C2-ADJ packages | Neighbor damage dual-emit | el fences, exclusive crop, soup strip, gates | **ROOT + L5** | Done core |
| C2-R1 / C2-CO2 | Callout + multi-col order | `page_elements` blue RO | **ROOT** | Done |
| L05-P41-CO / L07-P43 | Placement classes | `_callout_mixed_order` | **ROOT** | Done |
| C2-F1/F2 | Figure soup / multi-fig | `extract_chunk` strip + `apply_figures` replace | **HYBRID** | Keep strip at inject; polish residual OK |
| C2-F3 | Wrong PNG crops | multipass crop registry | **ROOT-ish** (assets) | User confirm |
| C2-T1 / T4b | Table vs scale id | `KNOWN_TABLES_*` / registry | **ROOT** | Done |
| C2-T3 | Cell `<br>` | `utils.escape_md_cell` | **ROOT** | Improve if residual |
| C2-G1 | Empty tables | table emit suppress | **ROOT** | Done |
| C2-H1 | Inline links | `pdf_links` | **HYBRID** | More root attach; polish Guide attach is net |
| C2-U1 | Spaces in URLs | `sanitize_urls_in_text` | **HYBRID** | Keep both extract+format |
| L05-FN-GLUE | FN glued to URL | sanitize + `repair_glued_footnotes` | **HYBRID** | Keep both |
| L07-ODD-CAPTION / L05-PAGE-AST | Running head / `*` split | `page_layout` normalize + resync polish | **HYBRID** | Emit correct first; keep resync |
| L07-ID / R3 | Garbled ids | `title_fix` + resync from title | **HYBRID** | **PROMOTE:** slug only from fixed title at inventory+emit; inventory still lags |
| L07-TABLE-BLANK | Blank before `\|` | postprocess insert | **POLISH PATTERN** | **PROMOTE:** emit blank in `artifact_header` / table writers |
| Footer ▶ / dingbat | `3` vs ▶ | span map + format net | **HYBRID** | Root map primary |
| y-gap paras / p.22 | False para splits | `page_layout` y-gap | **ROOT** | Residual C2-P1 |

### 3.2 Late polish — general patterns (OK short-term, promote when cheap)

| ID | What polish does | Promote to |
|----|------------------|------------|
| L07-P42-CO Step expand | Split `Step N:` in blockquotes | `emit_callout_blockquote` / textbox newlines |
| L07-TABLE-BLANK | Blank before tables | artifact/table emit |
| C2-L1 mid-line dingbat lists | Split mid-line list glue | list detection in extract |
| `_repair_collapsed_blockquotes` | `> a > b` → multi-line | don’t join in cleanup |
| Guide URL attach (general) | Parenthetical after Guide title | `pdf_links` only |
| Token garbled map | String replace ids | inventory slug from `fix_rotated_title` |
| `_resync_artifact_ids_from_fixed_titles` | Re-id from ### / table title | same at L2 emit only |
| `_resync_page_captions_from_pdf` | Rewrite captions from PDF | emit from zones only |

### 3.3 Late polish — page/string-specific (highest night-risk)

These **will not** magically fix “the same class” on unreported pages. Full re-extract **without** format still leaves them wrong if extract is wrong; with format they only fix the **named** instances.

| ID | Hardcode nature | Root fix needed |
|----|-----------------|-----------------|
| **L06-P41** | Full callout body replacement for `callout_p041_0` | Progressive: full textbox + para split; no band dump |
| **L05-P27-CO** (polish half) | Exact 3-way string split | Keep detect forced split; verify emit |
| **L05-P35-CO** (polish half) | Split after “achievement.” | Same |
| **L05-P38-A2** | Prose→table conversion of A2 sample | Inventory type table + extract table path |
| **L07-P38-SOUP** (regex under fig6) | figure_06-specific strip | Exclusive region so dual table never emits |
| **L07-P90-SOUP** (mediation labels) | figure_14-specific strip | Exclusive figure region / RO |
| **L07-P43 lead** | Insert “Very often…” | Don’t drop lead in extract |
| **L05-P41-URL** | Section 3.7 URL inject | Link attach from PDF annots |
| **L06-FN21** | ObjectId trailing digit rejoin | URL sanitize edge |
| **fn26 missing** | Insert RELANG footnote | Footnote zone extract complete |
| **§3.1 after Fig 11** | Temporary heading restore | RO trailing heading |
| **L05-P29-CH** | Soft-wrap chapter titles in callout | Callout line join in emit |
| **L05-P37** list/title glue | Several string repairs | Emit from bands cleanly |
| **L06-SEC** | `### 2.6/2.7` unglue | Heading detection in extract |
| **L06-HY / L05-P33-HY** | Typo map | OCR map OK as polish |

---

## 4. Priority promotion list (do these if you want root safety)

### P0 — without this, re-extract alone fails the class

1. **Callout progressive stacks (L06-P41 class)**  
   - Today: page hardcode in post_process.  
   - Root: `callout_paragraphs_from_bbox` must emit clean multi-para from full textbox; never dump progressive band garbage.

2. **Callout Step N formatting (L07-P42)**  
   - Today: polish expand.  
   - Root: preserve newlines / list structure when emitting blockquote.

3. **Figure dual-emit soup (C2-F1, L07-P38/P90)**  
   - Today: inject strip + page regexes.  
   - Root: exclusive ownership so second representation never lands.

4. **Garbled ids at inventory (L07-ID / R3)**  
   - Today: polish re-derive in final MD.  
   - Root: `fix_rotated_title` + slug at span/inventory time so re-extract doesn’t reintroduce.

### P1 — safe polish nets, promote when touching emit

5. Table blank line before `|`  
6. Page caption normalize (keep PDF resync as backup)  
7. URL/FN sanitize (already shared utils — ensure extract always calls them)  
8. Callout para splits p.27/p.35 (detect already has forced paths — verify emit uses them, delete polish copy)

### P2 — acceptable as polish

9. Typo maps (`problemsolving`, `situationspecific`)  
10. Collapsed blockquote re-expand  
11. Bold spacing cleanup  

---

## 5. What a full re-inventory / re-extract actually does

| If you run full inventory + extract + merge + figures + **format** | Result |
|-------------------------------------------------------------------|--------|
| Placement rules | Applied book-wide (ROOT) |
| General polish patterns | Applied book-wide (Step expand, id resync, captions, sanitizer) |
| Page hardcodes | Only those exact pages/strings |
| Inventory cleanliness for ids | Only if title_fix runs at inventory build |

| If you run full extract but **skip format** | Result |
|---------------------------------------------|--------|
| Placement | Still good (in extract) |
| Steps / table blanks / id resync / p.41 body hardcode / many log05 patches | **Lost or degraded** |

---

## 6. Direct answers

**Q: Callout placement — only my pages?**  
**A: No.** Root classifier. Full re-extract with current code reapplies it.

**Q: Callout lost titles/formatting — root or polish?**  
**A: Split.** Placement = root. Many title/para/Step/progressive body fixes = **polish**, some **page-hardcoded**.

**Q: Will other pages stay broken after full re-extract for the same class?**  
**A:**  
- Same **placement** class → should be OK.  
- Same **progressive garbage / Step collapse / string body** class → **yes risk** until root promotion above.

**Q: Am I about to have a terrible night of page-by-page polish forever?**  
**A: Only if we keep adding PAGE hardcodes instead of promoting P0 items.** Placement is already the right architecture. The scary pile is **L4 page-specific** callout/figure string patches — those need root work, not more log pages.

---

## 7. Suggested next engineering order (when you authorize implementation)

1. Progressive callout emit (kill `clean_p41` hardcode).  
2. Step-preserving callout emit.  
3. Inventory/emit slug from `fix_rotated_title` only.  
4. Figure exclusive replace so P38/P90 regexes become unnecessary.  
5. Emit blank line before tables.  
6. Delete duplicate polish once gates+Vision prove root.

---

*Sources: `STATUS.md` §5, `pipeline/post_process.py` `_repair_log05_markdown`, `page_elements._callout_mixed_order`, `callout_detect.py`, `docs/RESOLVED_EXTRACTION_ISSUES.md`.*
