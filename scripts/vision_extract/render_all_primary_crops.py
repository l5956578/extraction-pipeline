#!/usr/bin/env python3
"""Render full-page 4x + L/R + 4 bands for every Threshold primary intonation leaf."""
from __future__ import annotations

from pathlib import Path

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "input/cefr-threshold-1990/source.pdf"
OUT = ROOT / "work/cefr-threshold-1990/intonation_hires/primary_all"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "bands").mkdir(exist_ok=True)

LEAVES = (
    list(range(34, 65))
    + list(range(66, 91))
    + list(range(104, 113))
    + list(range(124, 131))
)

def main() -> None:
    doc = fitz.open(PDF)
    mat = fitz.Matrix(4, 4)
    for leaf in LEAVES:
        page = doc[leaf - 1]
        dest = OUT / f"leaf_{leaf:03d}_full4.png"
        if dest.exists() and dest.stat().st_size > 50_000:
            print(f"skip existing {leaf}")
            continue
        pix = page.get_pixmap(matrix=mat, alpha=False)
        pix.save(str(dest))
        img = Image.open(dest)
        w, h = img.size
        mid = w // 2
        img.crop((0, 0, mid + 30, h)).save(OUT / f"leaf_{leaf:03d}_L.png")
        img.crop((mid - 30, 0, w, h)).save(OUT / f"leaf_{leaf:03d}_R.png")
        for bi in range(4):
            y0 = int(h * bi / 4)
            y1 = min(h, int(h * (bi + 1) / 4) + 40)
            img.crop((0, y0, w, y1)).save(OUT / "bands" / f"leaf_{leaf:03d}_b{bi}.png")
        print(f"leaf {leaf} ok {w}x{h}")
    doc.close()
    print(f"TOTAL leaves {len(LEAVES)} dir {OUT}")


if __name__ == "__main__":
    main()
