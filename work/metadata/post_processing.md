# Final Markdown formatting

> **Status:** [`STATUS.md`](../STATUS.md)  
> **Architecture:** [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) §5

## Deliverable

`output/CEFR_Companion_Volume.md` (single file; format in place).

## When to run

| Situation | Command |
|-----------|---------|
| Changed `post_process.py` / `prose_format.py` | `python iterate_format.py` (~4s) |
| Changed `cleanup.py` | `python iterate_format.py --from-raw` |
| Full extract already done | Format runs at end of merge / `run_production_extract.py` |

## Responsibilities

- List soft-wrap repair (`_repair_list_blocks`)
- Page footer order (visible caption then `<!-- page:N -->`)
- Dingbat footer arrow residual (`3` → `▶`)
- Chapter / TOC / bold normalization
- Collapse excess blank lines

## Modules

| Module | Role |
|--------|------|
| `pipeline/post_process.py` | Structure |
| `pipeline/prose_format.py` | Bold + OCR typos + dingbat residual |
| `pipeline/cleanup.py` | Per-chunk pre-merge cleanup |
