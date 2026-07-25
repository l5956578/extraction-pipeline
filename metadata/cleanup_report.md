# Cleanup report

> **Current status:** [`STATUS.md`](../STATUS.md)  
> This file is a short note only; do not treat metrics below as live.

Chunk cleanup rules live in `pipeline/cleanup.py` and run as stage 4 of the pipeline  
(raw → cleaned). Final structure is applied by `pipeline/post_process.py`.

```bash
python iterate_format.py --from-raw   # cleanup all raw + merge + format
python run_pipeline.py --step cleanup
```
