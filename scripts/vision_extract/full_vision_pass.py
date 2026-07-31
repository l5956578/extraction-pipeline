#!/usr/bin/env python3
"""Full-book Vision-quality assembly for Threshold / Waystage / CEFR 2001.

Strategy:
1. Prefer work/<job>/page_overrides/page_NNN.md when present (Vision-written truth).
2. Else layout-format from PDF text blocks (CEFR/Threshold) or OCR lines (Waystage).
3. Never emit mid-sentence em-dashes as bullets; numbered short titles are headers.
4. Snapshot versions/004.

This script does not call an external Vision API — the agent writes overrides after
reading page PNGs. It *applies* those overrides comprehensively.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Load format_extract as module
spec = importlib.util.spec_from_file_location(
    "format_extract", Path(__file__).resolve().parent / "format_extract.py"
)
fe = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(fe)


def main() -> None:
    # Bump snapshot version
    orig_snapshot = fe.snapshot

    def snapshot_v4(job: str, md_name: str, ver: str = "004") -> None:
        return orig_snapshot(job, md_name, ver=ver)

    fe.snapshot = snapshot_v4  # type: ignore

    print("=== Threshold 1990 ===", flush=True)
    p = fe.build_book(
        "cefr-threshold-1990",
        "Threshold 1990",
        "Threshold_1990.md",
        use_ocr_fallback=True,
    )
    fe.rewrite_app_a_pages_threshold(p)
    fe.snapshot("cefr-threshold-1990", "Threshold_1990.md", ver="004")
    fe.metrics(p)

    print("=== Waystage 1990 ===", flush=True)
    p = fe.build_book(
        "cefr-waystage-1990",
        "Waystage 1990",
        "Waystage_1990.md",
        use_ocr_fallback=True,
    )
    fe.rewrite_app_a_pages_waystage(p)
    fe.snapshot("cefr-waystage-1990", "Waystage_1990.md", ver="004")
    fe.metrics(p)

    print("=== CEFR EN 2001 ===", flush=True)
    p = fe.build_book(
        "cefr-en-2001",
        "Common European Framework of Reference for Languages: Learning, teaching, assessment (2001)",
        "CEFR_EN_2001.md",
        use_ocr_fallback=False,
    )
    # inject critical tables if missing
    text = p.read_text(encoding="utf-8")
    text = fe.inject_cefr2001_critical(text)
    p.write_text(text, encoding="utf-8")
    fe.snapshot("cefr-en-2001", "CEFR_EN_2001.md", ver="004")
    fe.metrics(p)

    # inventory overrides
    for job in ("cefr-threshold-1990", "cefr-waystage-1990", "cefr-en-2001"):
        n = len(list((ROOT / "work" / job / "page_overrides").glob("page_*.md")))
        print(f"overrides {job}: {n}", flush=True)


if __name__ == "__main__":
    main()
