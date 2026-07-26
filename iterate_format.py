#!/usr/bin/env python3
"""
Fast iteration for markdown formatting only (~3–5s).

Use this after changing pipeline/post_process.py or pipeline/prose_format.py.
Does NOT re-extract the PDF.

  python iterate_format.py              # format output in place
  python iterate_format.py --from-cleaned   # re-merge cleaned chunks then format
  python iterate_format.py --from-raw       # cleanup raw → cleaned → merge → format

Full PDF extract is the slow path (minutes–tens of minutes). Prefer:
  1) iterate_format.py          for list/spacing/bold/page-marker issues
  2) --from-raw                 if cleanup.py changed
  3) re-extract one chunk only  if extract logic changed
  4) full extract               only when inventory/rotated tables change
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def _log(*args) -> None:
    print(*args, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fast format iteration (no full extract)")
    parser.add_argument(
        "--from-cleaned",
        action="store_true",
        help="Re-merge work/cleaned/*.md into final, then postprocess",
    )
    parser.add_argument(
        "--from-raw",
        action="store_true",
        help="Cleanup raw → cleaned, merge, then postprocess",
    )
    args = parser.parse_args()

    t0 = time.perf_counter()

    if args.from_raw:
        from pipeline.cleanup import cleanup_all

        _log("=== cleanup (raw → cleaned) ===")
        cleanup_all()
        args.from_cleaned = True

    if args.from_cleaned:
        from pipeline.merge_output import merge_markdown
        from pipeline.apply_figures import run_apply_figures

        _log("=== merge cleaned → final ===")
        merge_markdown()
        try:
            _log("=== figures ===")
            run_apply_figures()
        except Exception as exc:  # noqa: BLE001
            _log(f"figures skip: {exc}")

    from pipeline.post_process import run_post_process

    _log("=== postprocess (format only) ===")
    result = run_post_process()
    elapsed = time.perf_counter() - t0
    _log(f"Done in {elapsed:.1f}s")
    _log(f"  {result['input_lines']} → {result['output_lines']} lines")
    _log(f"  {result['output_path']}")
    _log("Review: output/CEFR_Companion_Volume.md")


if __name__ == "__main__":
    main()
