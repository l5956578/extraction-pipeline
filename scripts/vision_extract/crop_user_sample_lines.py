#!/usr/bin/env python3
"""Crop 10x lines for user-reported wrong samples."""
import fitz
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work/cefr-threshold-1990/intonation_hires/user_samples"
OUT.mkdir(parents=True, exist_ok=True)
pdf = fitz.open(ROOT / "input/cefr-threshold-1990/source.pdf")
mat = fitz.Matrix(10, 10)

targets = {
    36: ["wrong", "horrible", "isn't", "will", "think he"],
    45: ["dance", "walk", "train", "Shall we", "could", "perhaps"],
    47: ["Hallo", "Hello", "4.2.1", "How are"],
    49: ["5.4.1", "pollution", "something about"],
}

for leaf, keys in targets.items():
    page = pdf[leaf - 1]
    pix = page.get_pixmap(matrix=mat, alpha=False)
    full = OUT / f"l{leaf}_10x.png"
    pix.save(str(full))
    img = Image.open(full)
    n = 0
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for l in b.get("lines", []):
            text = "".join(s["text"] for s in l["spans"]).strip()
            if not any(k.lower() in text.lower() for k in keys):
                continue
            x0 = min(s["bbox"][0] for s in l["spans"])
            y0 = min(s["bbox"][1] for s in l["spans"])
            x1 = max(s["bbox"][2] for s in l["spans"])
            y1 = max(s["bbox"][3] for s in l["spans"])
            left = max(0, int((x0 - 15) * 10))
            top = max(0, int((y0 - 12) * 10))
            right = min(img.width, int((x1 + 15) * 10))
            bot = min(img.height, int((y1 + 10) * 10))
            fn = f"l{leaf}_{n:02d}.png"
            img.crop((left, top, right, bot)).save(OUT / fn)
            print(fn, text)
            n += 1
print("out", OUT)
