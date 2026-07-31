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


def fix_md(job: str) -> None:
    cfg = JOBS[job]
    path = ROOT / "output" / job / cfg["md"]
    text = path.read_text(encoding="utf-8")

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
