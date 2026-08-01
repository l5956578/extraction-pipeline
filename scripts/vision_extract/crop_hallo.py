#!/usr/bin/env python3
import fitz
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work/cefr-threshold-1990/intonation_hires/user_samples"
pdf = fitz.open(ROOT / "input/cefr-threshold-1990/source.pdf")
page = pdf[46]
mat = fitz.Matrix(10, 10)
pix = page.get_pixmap(matrix=mat, alpha=False)
full = OUT / "l47_10x_full.png"
pix.save(str(full))
img = Image.open(full)
n = 0
for b in page.get_text("dict")["blocks"]:
    if b.get("type") != 0:
        continue
    for l in b.get("lines", []):
        text = "".join(s["text"] for s in l["spans"]).strip()
        if not any(
            k in text for k in ("Hal", "Excuse", "Good", "say", "greeting", "4.1", "4.2")
        ):
            continue
        x0 = min(s["bbox"][0] for s in l["spans"])
        y0 = min(s["bbox"][1] for s in l["spans"])
        x1 = max(s["bbox"][2] for s in l["spans"])
        y1 = max(s["bbox"][3] for s in l["spans"])
        crop = img.crop(
            (
                max(0, int((x0 - 12) * 10)),
                max(0, int((y0 - 12) * 10)),
                min(img.width, int((x1 + 12) * 10)),
                min(img.height, int((y1 + 10) * 10)),
            )
        )
        crop.save(OUT / f"hallo_{n:02d}.png")
        print(n, text)
        n += 1
