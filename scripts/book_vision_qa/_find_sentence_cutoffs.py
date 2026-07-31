#!/usr/bin/env python3
"""Find page bodies ending mid-sentence (likely multipage cut)."""

from __future__ import annotations

import re
from pathlib import Path

md = (
    Path(__file__).resolve().parents[2]
    / "output/cefr-companion-2020/CEFR_Companion_Volume.md"
).read_text(encoding="utf-8")


def page_body(n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return ""


def main() -> None:
    cuts = []
    for n in range(1, 279):
        b = page_body(n)
        clean = re.sub(r"<!--.*?-->", "", b, flags=re.S)
        clean = re.sub(r"\*[^\n]*Page[^\n]*\*", "", clean)
        lines = [
            ln.strip()
            for ln in clean.splitlines()
            if ln.strip()
            and not ln.strip().startswith("|")
            and not ln.strip().startswith("#")
            and not ln.strip().startswith("```")
            and not ln.strip().startswith("-")
        ]
        if not lines:
            continue
        last = lines[-1]
        if last.endswith((".", "!", "?", ":", ")", "]", '"', "”", "’", "…")):
            continue
        if last.startswith("*") or last.startswith(">"):
            continue
        if len(last) < 25:
            continue
        if re.search(r"[a-z,;]$", last) or last.endswith(
            (" the", " and", " of", " to", " in", " for", " with", " on", " a")
        ):
            cuts.append((n, last[-90:]))
    print("cutoff_count", len(cuts))
    for c in cuts:
        print(c)


if __name__ == "__main__":
    main()
