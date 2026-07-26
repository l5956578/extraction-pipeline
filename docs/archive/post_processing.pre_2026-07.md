# Final Markdown formatting (integrated into merge)

## Single deliverable

```
output/CEFR_Companion_Volume.md
```

Paragraph merge, chapter formatting, page-marker spacing, bullet cleanup, and bold
normalization all run automatically at the end of merge. There is no separate
structured output file.

## Pipeline order

```
inventory → extract → cleanup → merge (includes apply_figures + format + validate)
```

Inside `run_merge()`:

1. Concatenate cleaned chunks
2. Build manifest and DB registry
3. `apply_figures` — inject diagrams and PNGs
4. `run_post_process` — format `CEFR_Companion_Volume.md` in place
5. `validate_final_output`

## Re-run formatting without merge

```bash
python run_pipeline.py --step postprocess
```

## Bold markdown

`prose_format.fix_bold_markdown()` runs once at the end of formatting. OCR typo
fixes (`fix_ocr_typos`) never strip spaces around `**`.

## Code

| Module | Role |
|--------|------|
| `pipeline/post_process.py` | Paragraph/chapter/page formatting |
| `pipeline/prose_format.py` | Bold + OCR helpers |
| `pipeline/merge_output.py` | Calls post-process after figures |