#!/usr/bin/env python3
"""Render all Companion PDF pages to qa_snapshots for Vision QA (reuse valid PNGs)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main() -> int:
    import fitz
    from pipeline.bootstrap import bootstrap_job
    from pipeline.config import RENDER_SCALE

    parser = argparse.ArgumentParser()
    parser.add_argument("--job", default="cefr-companion-2020")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=0)
    args = parser.parse_args()
    ctx = bootstrap_job(args.job, force_draft=True)
    out = ctx.metadata_dir / "qa_snapshots"
    out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(ctx.pdf_path)
    end = args.end or len(doc)
    scale = float(RENDER_SCALE) if RENDER_SCALE else 2.0
    mat = fitz.Matrix(scale, scale)
    made = reused = 0
    for page in range(args.start, end + 1):
        path = out / f"page_{page:03d}.png"
        if path.is_file() and path.stat().st_size > 2000 and not args.force:
            reused += 1
            continue
        pix = doc[page - 1].get_pixmap(matrix=mat, alpha=False)
        pix.save(str(path))
        made += 1
        if page % 40 == 0:
            print(f"rendered through {page}", flush=True)
    doc.close()
    print(f"done made={made} reused={reused} dir={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
