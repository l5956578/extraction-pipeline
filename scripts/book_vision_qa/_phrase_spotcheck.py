#!/usr/bin/env python3
"""Spot-check distinctive PDF phrases against MD (sample pages)."""

from __future__ import annotations

import random
import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
MD = (ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md").read_text(
    encoding="utf-8"
)
PDF = ROOT / "input/cefr-companion-2020/source.pdf"


def main() -> None:
    doc = fitz.open(PDF)
    md_l = MD.lower()
    random.seed(42)
    missing: list[tuple[int, str]] = []
    for n in sorted(random.sample(range(30, 250), 50)):
        pdf = doc[n - 1].get_text()
        lines = [
            ln.strip()
            for ln in pdf.splitlines()
            if len(ln.strip()) > 40
            and not re.match(r"Page \d+|CEFR|Companion volume|Appendix", ln)
        ]
        for ln in lines[:10]:
            words = re.findall(r"[A-Za-z']+", ln)
            if len(words) < 6:
                continue
            ok = False
            for i in range(0, max(1, len(words) - 3)):
                p2 = " ".join(words[i : i + 4])
                if len(p2) > 15 and p2.lower() in md_l:
                    ok = True
                    break
            if not ok:
                missing.append((n, " ".join(words[1:8])[:90]))
                break
    print(f"phrase_gap_pages={len(missing)}")
    for n, ph in missing[:30]:
        print(f"  p{n}: {ph}")


if __name__ == "__main__":
    main()
