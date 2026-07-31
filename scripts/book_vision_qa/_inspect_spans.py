#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

MD = Path(__file__).resolve().parents[2] / "output/cefr-companion-2020/CEFR_Companion_Volume.md"
md = MD.read_text(encoding="utf-8")


def page_body(n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return ""


for n in [146, 147, 148, 99, 100, 101, 177, 178, 169, 184, 185, 25, 92, 95]:
    b = page_body(n)
    levels = re.findall(r"\| (C2|C1|B2\+?|B1\+?|A2\+?|A1|Pre-A1) \|", b)
    has_table = "|" in b and "---" in b
    flags = []
    if "page-slice" in b:
        flags.append("slice")
    if "continuation" in b:
        flags.append("cont")
    if "book-qa" in b:
        flags.append("bookqa")
    if re.search(r"db:id=", b):
        flags.append("dbid")
    print(
        f"p{n} len={len(b)} table={has_table} levels={levels} flags={flags}"
    )
    # first heading
    for ln in b.splitlines():
        if ln.startswith("###") or ln.startswith("**") and "scale" not in ln.lower():
            if "Page" not in ln:
                print("  ", ln[:100])
                break
