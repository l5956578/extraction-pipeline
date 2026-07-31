#!/usr/bin/env python3
"""Split country table: Spain EOI on p19; Sweden–Uruguay on p20."""

from __future__ import annotations

import re
from pathlib import Path

MD = Path(__file__).resolve().parents[2] / "output/cefr-companion-2020/CEFR_Companion_Volume.md"


def replace_page(md: str, page: int, new_body: str) -> str:
    marker = f"<!-- page:{page} -->"
    idx = md.find(marker)
    prev = list(re.finditer(r"<!-- page:\d+ -->", md[:idx]))
    start = prev[-1].end() if prev else 0
    return md[:start] + "\n" + new_body.strip() + "\n\n" + md[idx:]


def page_body(md: str, n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return ""


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    b19 = page_body(md, 19)
    idx = b19.find("| **Sweden**")
    if idx < 0:
        raise SystemExit("Sweden row not found on p19")
    hm = re.search(r"(\|[^\n]+\n\|[-| :\t]+\n)", b19)
    header = (
        hm.group(1)
        if hm
        else "| Country | Institution / Organization |  |\n| --- | --- | --- |\n"
    )
    pre = b19[:idx].rstrip()
    post = b19[idx:]
    m = re.search(r"([\s\S]*?)(<!-- el:end[\s\S]*)", post)
    if not m:
        raise SystemExit("el:end not found after Sweden")
    rows, _tail = m.group(1).rstrip(), m.group(2)
    new19 = (
        pre
        + "\n<!-- el:end id=prose_p019_ack -->\n\n"
        + "*Preface with acknowledgements ▶ Page **19***\n"
    )
    # drop duplicate el:end if pre already closed wrongly
    new19 = re.sub(r"(<!-- el:end id=prose_p019_ack -->\s*){2,}", r"\1", new19)
    # if pre still has open start without end before our end, ok
    p20 = (
        "<!-- el:start type=prose id=prose_p020_ack page=20 -->\n"
        "<!-- book-qa: country table continuation (user temp tables) -->\n"
        f"{header}{rows}\n"
        "<!-- el:end id=prose_p020_ack -->\n\n"
        "*Page **20** ▶ **CEFR – Companion volume***\n"
    )
    md = replace_page(md, 19, new19)
    md = replace_page(md, 20, p20)
    MD.write_text(md, encoding="utf-8")
    md2 = MD.read_text(encoding="utf-8")
    for n in (19, 20):
        b = page_body(md2, n)
        print(
            f"p{n} len={len(b)} Sweden={'Sweden' in b} "
            f"UK={'United Kingdom' in b} EOI={'EOI de Albacete' in b}"
        )


if __name__ == "__main__":
    main()
