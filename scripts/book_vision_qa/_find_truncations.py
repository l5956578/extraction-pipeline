#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

md = (
    Path(__file__).resolve().parents[2]
    / "output/cefr-companion-2020/CEFR_Companion_Volume.md"
).read_text(encoding="utf-8")

trunc = []
for m in re.finditer(r"(?m)^.{40,220}[a-zA-Z]{2,}$", md):
    line = m.group().strip()
    if line.startswith(("|", "#", "<!--", "*", "-", ">")):
        continue
    if line.endswith((".", "!", "?", ":", ";", ")", "]", '"', "'", "”", "’", ",")):
        continue
    if "http" in line:
        continue
    page = None
    for mm in re.finditer(r"<!-- page:(\d+) -->", md):
        if mm.start() > m.start():
            page = int(mm.group(1))
            break
    trunc.append((page, line[-70:]))

print("trunc_candidates", len(trunc))
for t in trunc[:40]:
    print(t)
