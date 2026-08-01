#!/usr/bin/env python3
"""
Glyph-audit infrastructure: every tone example line → ≥8× crop + manifest.

Books: Threshold + Waystage primary intonation leaves.
Does not invent marks — only produces crops for Vision and a machine-readable
manifest of MD lines to check/fix.

Usage:
  python glyph_audit_all_tones.py              # render all missing crops
  python glyph_audit_all_tones.py --book thr   # Threshold only
  python glyph_audit_all_tones.py --stats      # count only
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]

BOOKS = {
    "thr": {
        "pdf": ROOT / "input/cefr-threshold-1990/source.pdf",
        "md": ROOT / "output/cefr-threshold-1990/Threshold_1990.md",
        "out": ROOT / "work/cefr-threshold-1990/intonation_hires/glyph_audit",
        "leaves": (
            list(range(34, 65))
            + list(range(66, 91))
            + list(range(104, 113))
            + list(range(124, 131))
        ),
        "doc_offset": 6,
    },
    "way": {
        "pdf": ROOT / "input/cefr-waystage-1990/source.pdf",
        "md": ROOT / "output/cefr-waystage-1990/Waystage_1990.md",
        "out": ROOT / "work/cefr-waystage-1990/intonation_hires/glyph_audit",
        "leaves": (
            list(range(22, 36))
            + list(range(38, 48))
            + list(range(56, 66))
            + list(range(77, 81))
        ),
        "doc_offset": 6,
    },
}

TONE_RE = re.compile(r"[ˈˎˋˏˊˇ·]")
ZOOM = 8.0


def page_bodies(md: str) -> dict[int, str]:
    bodies: dict[int, str] = {}
    for m in re.finditer(r"<!-- page:(\d+) -->", md):
        doc = int(m.group(1))
        prev = list(re.finditer(r"<!-- page:(\d+|front-[^\s]+) -->", md[: m.start()]))
        start = prev[-1].end() if prev else 0
        bodies[doc] = md[start : m.start()]
    return bodies


def tone_lines_from_body(body: str) -> list[str]:
    out = []
    for ln in body.splitlines():
        s = ln.strip()
        if not s or s.startswith("<!--"):
            continue
        if TONE_RE.search(s):
            # strip blockquote
            s = re.sub(r"^>\s*", "", s)
            # skip pure headers that only have tones in section numbers? keep all
            if len(s) >= 3:
                out.append(s)
    return out


def letters(s: str) -> str:
    s = re.sub(r"[ˈˎˋˏˊˇ·ˌ'`´,.\"|\$]+", "", s)
    s = re.sub(r"[^A-Za-z0-9]+", " ", s).lower().strip()
    return re.sub(r"\s+", " ", s)


def crop_page_lines(page: fitz.Page, img: Image.Image, zoom: float, keys: list[str]) -> list[dict]:
    """Crop PDF text lines that match tone-line letter skeletons."""
    keyset = {letters(k) for k in keys if len(letters(k)) >= 4}
    results = []
    n = 0
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for l in b.get("lines", []):
            text = "".join(s["text"] for s in l["spans"]).strip()
            if len(text) < 3:
                continue
            sk = letters(text)
            if len(sk) < 4:
                continue
            # match if skeleton equals or is contained in a tone line skeleton
            matched = None
            for k in keyset:
                if sk == k or (len(sk) > 6 and (sk in k or k in sk)):
                    matched = k
                    break
            if not matched:
                # also crop lines that look mark-encoded even if not in MD yet
                if not re.search(r"['`,\.\"][A-Za-z]|[A-Za-z]['\",.]", text):
                    continue
                matched = sk
            x0 = min(s["bbox"][0] for s in l["spans"])
            y0 = min(s["bbox"][1] for s in l["spans"])
            x1 = max(s["bbox"][2] for s in l["spans"])
            y1 = max(s["bbox"][3] for s in l["spans"])
            pad_x, pad_y = 12, 10
            left = max(0, int((x0 - pad_x) * zoom))
            top = max(0, int((y0 - pad_y) * zoom))
            right = min(img.width, int((x1 + pad_x) * zoom))
            bot = min(img.height, int((y1 + pad_y) * zoom))
            # room for diacritics
            top = max(0, top - int(8 * zoom))
            bot = min(img.height, bot + int(6 * zoom))
            results.append(
                {
                    "n": n,
                    "pdf_text": text,
                    "skel": matched,
                    "bbox": [left, top, right, bot],
                }
            )
            n += 1
    return results


def process_book(book: str, force: bool = False) -> dict:
    cfg = BOOKS[book]
    out: Path = cfg["out"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "crops").mkdir(exist_ok=True)
    md = cfg["md"].read_text(encoding="utf-8")
    bodies = page_bodies(md)
    doc = fitz.open(cfg["pdf"])
    mat = fitz.Matrix(ZOOM, ZOOM)
    manifest = []
    total_md = 0
    total_crops = 0

    for leaf in cfg["leaves"]:
        docp = leaf - cfg["doc_offset"]
        body = bodies.get(docp, "")
        md_tones = tone_lines_from_body(body)
        total_md += len(md_tones)
        leaf_dir = out / "crops" / f"leaf_{leaf:03d}"
        leaf_dir.mkdir(exist_ok=True)

        page = doc[leaf - 1]
        full_path = out / f"leaf_{leaf:03d}_full{int(ZOOM)}.png"
        if force or not full_path.exists() or full_path.stat().st_size < 10_000:
            pix = page.get_pixmap(matrix=mat, alpha=False)
            pix.save(str(full_path))
        img = Image.open(full_path)

        # Always also save 6 horizontal strips for Vision when lines sparse
        h, w = img.height, img.width
        for si in range(8):
            y0 = max(0, int(h * si / 8) - 20)
            y1 = min(h, int(h * (si + 1) / 8) + 40)
            strip = leaf_dir / f"strip_{si}.png"
            if force or not strip.exists():
                img.crop((int(w * 0.04), y0, int(w * 0.96), y1)).save(strip)

        crops_meta = crop_page_lines(page, img, ZOOM, md_tones)
        # Image PDFs / weak text layer: no line boxes — still register strips as crops
        if not crops_meta and md_tones:
            for si in range(8):
                crops_meta.append(
                    {
                        "n": si,
                        "pdf_text": f"[strip_{si}]",
                        "skel": f"strip_{si}",
                        "bbox": None,
                        "is_strip": True,
                    }
                )
        for c in crops_meta:
            if c.get("is_strip"):
                fpath = leaf_dir / f"strip_{c['n']}.png"
                total_crops += 1
                manifest.append(
                    {
                        "book": book,
                        "leaf": leaf,
                        "doc": docp,
                        "crop": str(fpath.relative_to(out)),
                        "pdf_text": c["pdf_text"],
                        "md_line": "\n".join(md_tones),
                        "skel": c["skel"],
                        "mode": "strip",
                    }
                )
                continue
            fname = f"ex_{c['n']:03d}.png"
            fpath = leaf_dir / fname
            if force or not fpath.exists():
                box = c["bbox"]
                img.crop(tuple(box)).save(fpath)
            total_crops += 1
            # find MD line with same skel
            md_line = ""
            for mt in md_tones:
                if letters(mt) == c["skel"] or c["skel"] in letters(mt):
                    md_line = mt
                    break
            manifest.append(
                {
                    "book": book,
                    "leaf": leaf,
                    "doc": docp,
                    "crop": str(fpath.relative_to(out)),
                    "pdf_text": c["pdf_text"],
                    "md_line": md_line,
                    "skel": c["skel"],
                    "mode": "line",
                }
            )

        # write md tones for leaf
        (leaf_dir / "md_tones.txt").write_text(
            "\n".join(md_tones) + "\n", encoding="utf-8"
        )
        print(f"{book} leaf {leaf} doc {docp}: md_tones={len(md_tones)} crops={len(crops_meta)}")

    doc.close()
    man_path = out / "manifest.jsonl"
    with man_path.open("w", encoding="utf-8") as f:
        for row in manifest:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    stats = {
        "book": book,
        "leaves": len(cfg["leaves"]),
        "md_tone_lines": total_md,
        "crops": total_crops,
        "manifest": str(man_path),
    }
    (out / "STATS.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print("STATS", stats)
    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", choices=["thr", "way", "both"], default="both")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args()
    books = ["thr", "way"] if args.book == "both" else [args.book]
    if args.stats:
        for b in books:
            cfg = BOOKS[b]
            md = cfg["md"].read_text(encoding="utf-8")
            bodies = page_bodies(md)
            n = 0
            for leaf in cfg["leaves"]:
                n += len(tone_lines_from_body(bodies.get(leaf - cfg["doc_offset"], "")))
            print(f"{b}: leaves={len(cfg['leaves'])} md_tone_lines={n}")
        return
    all_stats = []
    for b in books:
        all_stats.append(process_book(b, force=args.force))
    print("DONE", all_stats)


if __name__ == "__main__":
    main()
