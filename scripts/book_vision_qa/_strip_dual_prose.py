#!/usr/bin/env python3
"""Remove dual-emit **Level** prose dumps after page-slice tables."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD_PATH = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"


def page_body(md: str, n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return ""


def replace_page_region(md: str, page: int, new_body: str) -> str:
    marker = f"<!-- page:{page} -->"
    idx = md.find(marker)
    prev = list(re.finditer(r"<!-- page:\d+ -->", md[:idx]))
    start = prev[-1].end() if prev else 0
    return md[:start] + "\n" + new_body.strip() + "\n\n" + md[idx:]


def strip_dual_prose(body: str) -> str:
    if not re.search(r"^\*\*(?:C2|C1|B2|B1|A2|A1)\+?\*\*", body, re.M):
        return body
    parts = re.split(r"\n(?=\*\*(?:C2|C1|B2|B1|A2|A1)\+?\*\*)", body, maxsplit=1)
    if len(parts) == 1:
        return body
    head, tail = parts[0], parts[1]
    m2 = re.search(r"(<!-- el:end.*)", tail, re.S)
    if m2:
        return head.rstrip() + "\n\n" + m2.group(1)
    m3 = re.search(r"(\*[^\n]*Page[^\n]*\*)", tail)
    if m3:
        return head.rstrip() + "\n\n" + m3.group(1) + "\n"
    return head


def main() -> None:
    md = MD_PATH.read_text(encoding="utf-8")
    for n in (159, 184, 188):
        b = page_body(md, n)
        new_b = strip_dual_prose(b)
        print(
            f"p{n} before={len(b)} after={len(new_b)} "
            f"star_B2={'**B2**' in new_b} table={'|' in new_b}"
        )
        md = replace_page_region(md, n, new_b)
    MD_PATH.write_text(md, encoding="utf-8")
    print("processing parallel", "enacted in parallel" in md)
    print("self assess difficulty", "I have no difficulty in understanding" in md)
    print("signing fluency hold", "extended hold of a sign" in md)


if __name__ == "__main__":
    main()
