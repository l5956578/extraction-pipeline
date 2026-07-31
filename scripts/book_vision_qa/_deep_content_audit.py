#!/usr/bin/env python3
"""Deep content audit: PDF distinctive phrases vs MD; flag real gaps."""

from __future__ import annotations

import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
MD = (ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md").read_text(
    encoding="utf-8"
)
PDF = ROOT / "input/cefr-companion-2020/source.pdf"


def page_body(n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", MD))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return MD[start : m.start()]
    return ""


def main() -> None:
    doc = fitz.open(PDF)
    md_l = MD.lower()
    gaps: list[tuple[int, str, float]] = []
    for n in range(1, 279):
        pdf = doc[n - 1].get_text()
        pdf_words = re.findall(r"[A-Za-z]{4,}", pdf)
        if len(pdf_words) < 40:
            continue
        # sample 4-grams from PDF
        miss = 0
        checked = 0
        samples = []
        for i in range(0, max(0, len(pdf_words) - 4), 8):
            phrase = " ".join(pdf_words[i : i + 4])
            if len(phrase) < 18:
                continue
            # skip chrome
            if re.search(
                r"\b(Page|Companion|CEFR|Appendix|Chapter)\b", phrase, re.I
            ):
                continue
            checked += 1
            if phrase.lower() not in md_l:
                # softer: 3-gram
                ok = False
                for j in range(4):
                    g3 = " ".join(pdf_words[i + j : i + j + 3]) if j < 2 else ""
                    if len(g3) > 14 and g3.lower() in md_l:
                        ok = True
                        break
                if not ok:
                    miss += 1
                    if len(samples) < 2:
                        samples.append(phrase)
        if checked >= 5 and miss / checked > 0.55:
            gaps.append((n, f"{miss}/{checked}", miss / checked))
            print(f"GAP p{n} miss_ratio={miss/checked:.2f} samples={samples}")
    print(f"gap_pages={len(gaps)}")
    for g in gaps[:40]:
        print(g)


if __name__ == "__main__":
    main()
