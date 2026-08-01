#!/usr/bin/env python3
import fitz
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
out = ROOT / "work/cefr-threshold-1990/intonation_hires/qa_fix"
out.mkdir(parents=True, exist_ok=True)
pdf = fitz.open(ROOT / "input/cefr-threshold-1990/source.pdf")
mat = fitz.Matrix(8, 8)

targets = {
    34: ["bedroom", "train", "owner", "animal", "isn't", "Yes you"],
    35: ["Did you", "saw him", "lost", "didn't", "station", "Please", "When will", "You"],
}

for leaf, keys in targets.items():
    page = pdf[leaf - 1]
    pix = page.get_pixmap(matrix=mat, alpha=False)
    fullp = out / f"l{leaf}_8x.png"
    pix.save(str(fullp))
    img = Image.open(fullp)
    d = page.get_text("dict")
    n = 0
    for b in d["blocks"]:
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
            left = max(0, int((x0 - 20) * 8))
            top = max(0, int((y0 - 14) * 8))
            right = min(img.width, int((x1 + 20) * 8))
            bot = min(img.height, int((y1 + 10) * 8))
            crop = img.crop((left, top, right, bot))
            fname = f"ex_l{leaf}_{n:02d}.png"
            crop.save(out / fname)
            print(f"{fname}\t{text}")
            n += 1
print("out", out)
