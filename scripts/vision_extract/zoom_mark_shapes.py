#!/usr/bin/env python3
import fitz
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
out = ROOT / "work/cefr-threshold-1990/intonation_hires/qa_fix"
out.mkdir(parents=True, exist_ok=True)
pdf = fitz.open(ROOT / "input/cefr-threshold-1990/source.pdf")
mat = fitz.Matrix(12, 12)


def crop_lines(leaf: int, keys: list[str], prefix: str) -> None:
    page = pdf[leaf - 1]
    pix = page.get_pixmap(matrix=mat, alpha=False)
    full = out / f"full_{prefix}.png"
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
            # full line with room for diacritics
            left = max(0, int((x0 - 12) * 12))
            top = max(0, int((y0 - 12) * 12))
            right = min(img.width, int((x1 + 12) * 12))
            bot = min(img.height, int((y1 + 10) * 12))
            img.crop((left, top, right, bot)).save(out / f"{prefix}_{n:02d}_line.png")
            # first 3 chars only for mark shape
            right2 = min(img.width, int((x0 + 55) * 12))
            img.crop((left, top, right2, bot)).save(out / f"{prefix}_{n:02d}_mark.png")
            print(f"{prefix}_{n:02d}", text)
            n += 1


crop_lines(34, ["This is the", "train", "owner", "animal", "No it", "Yes you"], "p34")
crop_lines(
    35,
    ["Did you", "saw him", "lost", "didn't", "Please can", "station", "When will"],
    "p35",
)
print("done", out)
