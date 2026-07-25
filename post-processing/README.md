# Post-processing CLI (thin wrapper)

Formatting logic lives in:

- `pipeline/post_process.py`
- `pipeline/prose_format.py`

It runs automatically after merge and via:

```bash
python iterate_format.py
# or
python run_pipeline.py --step postprocess
# or
python post-processing/format_markdown.py
```

**Do not** maintain a separate post-processing tree of rules.  
Historical standalone snapshot: `docs/archive/CEFR_Companion_Volume_structured.legacy.md`.

Project status: [`STATUS.md`](../STATUS.md).
