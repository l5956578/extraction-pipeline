#!/usr/bin/env python3
"""Strip dual-emit **Level** / scale-title prose dumps after restored page tables."""

from __future__ import annotations

import re
from pathlib import Path

MD = Path(__file__).resolve().parents[2] / "output/cefr-companion-2020/CEFR_Companion_Volume.md"

# Pages known to carry dual-emit scale dumps after the real table
PAGES = (147, 148, 151, 152, 155, 156, 160, 163)

TITLE_START = re.compile(
    r"\n\*\*(?:"
    r"Sign language repertoire|Diagrammatical accuracy|"
    r"Sociolinguistic appropriateness and cultural repertoire|"
    r"Sign text structure|Setting and perspectives|"
    r"Phonological control|Language awareness|"
    r"Processing speed|Presence and effect|Signing fluency"
    r")\*\*"
)


def page_body(md: str, n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return ""


def replace_page(md: str, page: int, new_body: str) -> str:
    marker = f"<!-- page:{page} -->"
    idx = md.find(marker)
    prev = list(re.finditer(r"<!-- page:\d+ -->", md[:idx]))
    start = prev[-1].end() if prev else 0
    return md[:start] + "\n" + new_body.strip() + "\n\n" + md[idx:]


def strip_dual(body: str) -> str:
    m = TITLE_START.search(body)
    if not m:
        # also: **Receptive** **Productive** dumps
        m = re.search(r"\n\*\*Receptive\*\*\s*\n\*\*Productive\*\*", body)
    if not m:
        return body
    tail = body[m.start() :]
    # keep el:end and page chrome from tail
    keep = ""
    em = re.search(r"(<!-- el:end[\s\S]*)", tail)
    if em:
        keep = em.group(1)
    else:
        cm = re.search(r"(\*[^\n]*Page[^\n]*\*)", tail)
        if cm:
            keep = tail[cm.start() :]
    return body[: m.start()].rstrip() + "\n\n" + keep.lstrip()


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    for n in PAGES:
        b = page_body(md, n)
        b2 = strip_dual(b)
        print(f"p{n} {len(b)} -> {len(b2)} dual_left={bool(TITLE_START.search(b2))}")
        md = replace_page(md, n, b2)
    MD.write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
