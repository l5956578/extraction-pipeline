#!/usr/bin/env python3
"""Harder gap audit: unique 6+ word PDF lines vs MD presence."""

from __future__ import annotations

import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
MD = (ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md").read_text(
    encoding="utf-8"
).lower()
PDF = ROOT / "input/cefr-companion-2020/source.pdf"

SKIP = re.compile(
    r"^(Page \d+|CEFR|Companion volume|Appendix|Chapter \d|"
    r"Introduction|Preface|Key aspects|Development and validation)",
    re.I,
)


def main() -> None:
    doc = fitz.open(PDF)
    hard_gaps: list[tuple[int, str]] = []
    for n in range(1, 279):
        pdf = doc[n - 1].get_text()
        lines = []
        for ln in pdf.splitlines():
            t = re.sub(r"\s+", " ", ln).strip()
            if len(t) < 55 or SKIP.search(t):
                continue
            words = re.findall(r"[A-Za-z']+", t)
            if len(words) < 8:
                continue
            # take middle 6 words as distinctive
            mid = " ".join(words[1:7])
            if len(mid) < 25:
                continue
            lines.append(mid)
        if not lines:
            continue
        # check up to 6 mid phrases
        miss = []
        for mid in lines[:: max(1, len(lines) // 6)][:6]:
            if mid.lower() not in MD:
                # try without one edge word
                w = mid.split()
                if len(w) >= 5 and " ".join(w[1:]).lower() in MD:
                    continue
                if len(w) >= 5 and " ".join(w[:-1]).lower() in MD:
                    continue
                miss.append(mid)
        if len(miss) >= 3:
            hard_gaps.append((n, "; ".join(miss[:3])))
    print(f"hard_gap_pages={len(hard_gaps)}")
    for n, s in hard_gaps:
        print(f"p{n}: {s}")


if __name__ == "__main__":
    main()
