# Figure handling policy (revised)

## Render types

| `render_as` | Figures | Notes |
|---|---|---|
| `png` | 2–10 | Diagrams, photos, radar/profile charts — must be cropped to `assets/figures/` |
| `text_diagram` | 1, 11–17 | Hierarchical trees; authoritative bodies in `figures_catalog.py`. Each tree is one continuous `` ```text `` block (no blank lines between root and branches). |
| `mermaid` | 18–20 | Process flowcharts in appendices |

**Figure 2** is a crossing-arrow diagram — never approximate with Mermaid.

**Figures 6–7** are radar profiles. PNG is canonical; structured levels for future UI live in `work/metadata/figure_06_profile_data.json` (and figure_07 when verified). Each axis level is the blue polygon edge / filled dot on the outer ring, read per quadrant left-to-right.

## Text extraction

- Prose uses `extract_rich_text()` (PyMuPDF dict mode) to preserve **bold** spans.
- `prose_format.normalize_prose()` converts `f` / triangle bullets to `-`, merges split `-` lines, and bolds sidebar titles like "Background to the CEFR levels".

## Pipeline

1. **Extract** — figure pages emit full page text (no separate artifact block that drops paragraphs).
2. **Cleanup** — bullet/bold normalization.
3. **Merge** — combines chunks.
4. **apply_figures** — inserts PNG or text diagram **at caption only**; strips flattened label soup; never removes surrounding paragraphs.
5. **Post-processing** (`pipeline/post_process.py`) — merges prose paragraphs but must leave fenced text-diagram trees untouched (no blank lines inside `` ```text `` blocks). Bold spacing uses `fix_bold_markdown()`; OCR fixes never strip spaces around `**`.

```bash
python run_pipeline.py --step extract
python run_pipeline.py --step cleanup
python run_pipeline.py --step merge
```