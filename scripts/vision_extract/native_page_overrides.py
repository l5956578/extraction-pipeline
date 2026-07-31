#!/usr/bin/env python3
"""Generate well-structured page_overrides from native PDF text for all pages.

Does not overwrite files that already contain '<!-- vision:'.
Used as bulk base; Vision agent rewrites replace these when present.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from format_extract import (  # noqa: E402
    clean_line,
    extract_lines_layout,
    is_bullet_line,
    is_running_chrome,
    is_section_number_heading,
    lines_to_markdown,
    looks_like_heading_line,
    median_body_size,
)


def write_overrides(job: str, only_missing: bool = True) -> int:
    pdf = ROOT / "input" / job / "source.pdf"
    out_dir = ROOT / "work" / job / "page_overrides"
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf)
    n_written = 0
    for i in range(doc.page_count):
        pnum = i + 1
        dest = out_dir / f"page_{pnum:03d}.md"
        if dest.exists():
            existing = dest.read_text(encoding="utf-8", errors="replace")
            if only_missing and "<!-- vision:" in existing:
                continue
            if only_missing and dest.stat().st_size > 150 and "el:start" in existing:
                # keep intentional overrides
                continue
        page = doc[i]
        native = page.get_text("text").strip()
        if len(native) < 20:
            body = (
                f"<!-- el:start type=prose id=prose_p{pnum:03d}_empty page={pnum} -->\n"
                f"<!-- vision-pending: empty or image-only; see work/{job}/page_renders/page_{pnum:03d}.png -->\n"
                f"<!-- el:end id=prose_p{pnum:03d}_empty -->\n"
            )
        else:
            lines = extract_lines_layout(page)
            body = lines_to_markdown(lines, pnum, job)
            # Tag as layout base (not full Vision yet)
            body = body.replace(
                f"id=prose_p{pnum:03d}",
                f"id=prose_p{pnum:03d}",
                1,
            )
            if "<!-- vision:" not in body:
                body = re.sub(
                    r"(<!-- el:start[^>]*-->\n)",
                    rf"\1<!-- layout-base: {job} PDF page {pnum}; upgrade with Vision if soup -->\n",
                    body,
                    count=1,
                )
        dest.write_text(body, encoding="utf-8")
        n_written += 1
        if pnum % 50 == 0:
            print(f"  {job} wrote through {pnum}", flush=True)
    print(f"{job}: wrote/updated {n_written} overrides (vision files preserved)", flush=True)
    return n_written


def main() -> None:
    write_overrides("cefr-en-2001", only_missing=True)
    write_overrides("cefr-threshold-1990", only_missing=True)
    # Waystage: no native text — leave for Vision agents; seed empty placeholders only for missing
    job = "cefr-waystage-1990"
    out_dir = ROOT / "work" / job / "page_overrides"
    out_dir.mkdir(parents=True, exist_ok=True)
    ocr_dir = ROOT / "work" / job / "page_ocr"
    n = 0
    for i in range(1, 121):
        dest = out_dir / f"page_{i:03d}.md"
        if dest.exists() and "<!-- vision:" in dest.read_text(encoding="utf-8", errors="replace"):
            continue
        if dest.exists() and dest.stat().st_size > 200:
            continue
        ocr = ocr_dir / f"page_{i:03d}.txt"
        text = ocr.read_text(encoding="utf-8", errors="replace").strip() if ocr.exists() else ""
        if not text:
            body = (
                f"<!-- el:start type=prose id=prose_p{i:03d}_empty page={i} -->\n"
                f"<!-- vision-pending: image page; work/{job}/page_renders/page_{i:03d}.png -->\n"
                f"<!-- el:end id=prose_p{i:03d}_empty -->\n"
            )
        else:
            from format_extract import extract_lines_ocr, lines_to_markdown

            lines = extract_lines_ocr(ocr)
            body = lines_to_markdown(lines, i, job)
            body = re.sub(
                r"(<!-- el:start[^>]*-->\n)",
                rf"\1<!-- ocr-base: Waystage page {i}; Vision rewrite required -->\n",
                body,
                count=1,
            )
        dest.write_text(body, encoding="utf-8")
        n += 1
    print(f"waystage ocr-base placeholders: {n}", flush=True)


if __name__ == "__main__":
    main()
