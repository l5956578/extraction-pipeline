#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
md = (ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md").read_text(
    encoding="utf-8"
)
doc = fitz.open(ROOT / "input/cefr-companion-2020/source.pdf")


def page_body(n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return ""


def main() -> None:
    md_l = md.lower()
    for n in [195, 206, 217, 233, 61, 71, 177, 178, 181]:
        pdf = doc[n - 1].get_text()
        b = page_body(n)
        words = re.findall(r"[A-Za-z]{5,}", pdf)
        missing = 0
        checked = 0
        samples = []
        for i in range(0, max(0, len(words) - 4), 12):
            phrase = " ".join(words[i : i + 4])
            if len(phrase) < 20:
                continue
            checked += 1
            if phrase.lower() not in md_l:
                missing += 1
                if len(samples) < 2:
                    samples.append(phrase)
        print(
            f"p{n} checked={checked} missing={missing} "
            f"tables={b.count('| ---')} len={len(b)} samples={samples}"
        )


if __name__ == "__main__":
    main()
