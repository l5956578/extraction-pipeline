#!/usr/bin/env python3
"""Export MD slices for pages 85-120."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
md = (ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md").read_text(
    encoding="utf-8"
)


def page_body(n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return ""


out = ROOT / "work/cefr-companion-2020/metadata/book_qa/vision/_slices"
out.mkdir(parents=True, exist_ok=True)
for n in range(85, 121):
    body = page_body(n)
    (out / f"page_{n:03d}.md").write_text(body, encoding="utf-8")
    lines = [ln for ln in body.splitlines() if ln.strip()]
    has_table = "|" in body and "---" in body
    has_scale = "descriptor_scale" in body or "scale_" in body
    print(
        f"p{n:03d} lines={len(lines):3d} chars={len(body):5d} "
        f"table={has_table} scale={has_scale}"
    )
print("wrote", out)
