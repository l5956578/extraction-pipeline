# Cleanup Report

## Pipeline summary

- **Source:** CEFR Companion Volume_eng.pdf (278 pages)
- **Chunks:** 10 span-safe PDF chunks
- **Output:** `final_output/CEFR_Companion_Volume.md` (~795 KB, 10,298 lines)
- **Artifacts registered:** 105 in `db_import_registry.json`
- **Figures extracted:** 6 PNGs in `final_output/assets/figures/`

## Fixes applied

### Extraction
- Span-aware chunking preserved multi-page tables (e.g. Appendix 2 pages 177–181, vocabulary control 132–133)
- Rotated PDF text corrected via word-order + character reversal before OCR fallback
- Self-assessment grid merged as single `table_self_assessment_grid` section block
- Vocabulary control continuation merged into one table (pages 132–133)

### Cleanup
- Hyphenation across line breaks repaired
- Soft-hyphen / ligature artifacts removed
- Duplicate consecutive lines removed
- Reversal applied only to detected gibberish table cells (conservative pass)

### Validation
- Final pass: **10/10 chunks passed**
- Self-assessment grid: single `<!-- db:id=table_self_assessment_grid -->` block
- No duplicate artifact IDs for continuation groups

## Known remaining artifacts

- Some rotated descriptor scales (e.g. phonological control, Appendix 5 domain tables) retain partial OCR scrambling; these pages use inverted PDF text layers. Re-run with `--step extract` on specific chunks after tuning if needed.
- All 20 figures classified in `metadata/figures_registry.json`; post-merge `apply_figures` inserts text diagrams, profile tables, or mermaid. Only Figure 4 is PNG.

## Re-run commands

```bash
python run_pipeline.py --step all          # full pipeline
python run_pipeline.py --step extract      # re-extract only
python run_pipeline.py --step cleanup      # cleanup raw → cleaned
python run_pipeline.py --step merge        # build final deliverables
```