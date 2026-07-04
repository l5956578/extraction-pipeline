# Post-processing (integrated into merge)

Formatting logic lives in `pipeline/post_process.py` and runs automatically at the
end of `run_pipeline.py --step merge`. There is **one deliverable**:

`final_output/CEFR_Companion_Volume.md`

## Re-run formatting only

```bash
python post-processing/format_markdown.py
# or
python run_pipeline.py --step postprocess
```

Run log: `metadata/last_format_run.txt`

## Do not edit here

Change `pipeline/post_process.py` or `pipeline/prose_format.py` for formatting rules.