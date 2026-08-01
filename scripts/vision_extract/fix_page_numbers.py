#!/usr/bin/env python3
"""Rewrite product MD page markers from PDF leaf numbers to document page numbers."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# pdf_leaf (1-based) -> document page number or None if front matter
# Front matter keeps negative or special labels

JOBS = {
    "cefr-en-2001": {
        "md": "CEFR_EN_2001.md",
        # PDF 1-9 front; PDF 10 = doc 1
        "pdf_to_doc": lambda p: None if p < 10 else p - 9,
        "front_labels": {
            1: "title",
            2: "contents",
            3: "prefatory",
            4: "notes",
            5: "notes",
            6: "notes",
            7: "notes",
            8: "synopsis",
            9: "synopsis",
        },
    },
    "cefr-threshold-1990": {
        "md": "Threshold_1990.md",
        # PDF 7 = doc 1
        "pdf_to_doc": lambda p: None if p < 7 else p - 6,
        "front_labels": {1: "half-title", 2: "blank", 3: "title", 4: "imprint", 5: "toc", 6: "blank"},
    },
    "cefr-waystage-1990": {
        "md": "Waystage_1990.md",
        "pdf_to_doc": lambda p: None if p < 7 else p - 6,
        "front_labels": {1: "half-title", 2: "blank", 3: "title", 4: "imprint", 5: "toc", 6: "blank"},
    },
}


def already_document_numbered(text: str, job: str) -> bool:
    """Detect if markers already use document pages (idempotent guard).

    Heuristic: max <!-- page:N --> is near PDF-count-offset range, and
    front-matter leaves 1-6 are absent as bare page:N (already front-*).
    """
    nums = [int(x) for x in re.findall(r"<!-- page:(\d+) -->", text)]
    if not nums:
        return False
    # If we still see high PDF leaf indices past last document page, not converted
    # Threshold: ~186 doc pages, PDF ~192. After convert max ~186.
    # If max page <= PDF_count-6 and page:1 exists with Arabic content start nearby → doc mode
    if "<!-- page:front-" in text:
        return True
    # Double-convert would push max down by 6 each time; v005 max is 186 for THR.
    # If markers include both small early pages and max ~ book length, treat as doc.
    mx = max(nums)
    # PDF-mode for Threshold has max ~192 and includes pages 1-6 as real PDF leaves.
    # Document-mode max is lower (~186) and often starts Arabic at 1 after front markers.
    if job.startswith("cefr-threshold") and mx <= 186 and 1 in nums and 192 not in nums:
        # Ambiguous — check for vision headers that already use doc p.
        if re.search(r"doc p\.\d+", text) or mx <= 180:
            # Prefer not re-converting if content looks post-fixed
            if "<!-- page:186 -->" in text or "<!-- page:180 -->" in text or mx <= 186:
                # Additional: if *Page **7*** exists as first arabic after front in PDF mode
                # PDF mode has *Page **7*** = doc 1. Doc mode has *Page **1***.
                # Count how many page markers > 186
                if mx <= 186 and min(nums) == 1:
                    # sample: document page 28 should be ch5; pdf leaf 28 is front/TOC area
                    return True
    if job.startswith("cefr-waystage") and mx <= 114 and min(nums) == 1:
        return True
    if job.startswith("cefr-en-2001") and "<!-- page:front-" in text:
        return True
    return False


def fix_md(job: str) -> None:
    cfg = JOBS[job]
    path = ROOT / "output" / job / cfg["md"]
    text = path.read_text(encoding="utf-8")

    if already_document_numbered(text, job):
        print(f"skip (already document page numbers): {path}")
        return

    def repl_page_comment(m: re.Match) -> str:
        pdf = int(m.group(1))
        doc = cfg["pdf_to_doc"](pdf)
        if doc is None:
            lab = cfg["front_labels"].get(pdf, "front")
            return f"<!-- page:front-{pdf} label={lab} -->"
        return f"<!-- page:{doc} -->"

    def repl_page_vis(m: re.Match) -> str:
        pdf = int(m.group(1))
        doc = cfg["pdf_to_doc"](pdf)
        if doc is None:
            lab = cfg["front_labels"].get(pdf, "front")
            return f"*[{lab}]*"
        return f"*Page **{doc}***"

    # Order: visual Page **N** first while N still PDF, then comments
    text2 = re.sub(r"\*Page \*\*(\d+)\*\*", repl_page_vis, text)
    text2 = re.sub(r"<!-- page:(\d+) -->", repl_page_comment, text2)

    # Also fix el:start page= attributes that are PDF indices (optional soft)
    def repl_el_page(m: re.Match) -> str:
        pre, pdf_s, post = m.group(1), m.group(2), m.group(3)
        pdf = int(pdf_s)
        doc = cfg["pdf_to_doc"](pdf)
        if doc is None:
            return m.group(0)
        return f"{pre}{doc}{post}"

    text2 = re.sub(r"(page=)(\d+)(\s)", repl_el_page, text2)

    path.write_text(text2, encoding="utf-8")
    print(f"fixed page numbers: {path}")


def main() -> None:
    for job in JOBS:
        fix_md(job)


if __name__ == "__main__":
    main()
