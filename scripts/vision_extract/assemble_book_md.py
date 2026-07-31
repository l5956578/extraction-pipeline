#!/usr/bin/env python3
"""Assemble high-quality book MD from PDF via render + Tesseract OCR + optional page overrides.

Does NOT reimplement the Companion extraction engine. Uses Vision/OCR lessons:
page markers <!-- page:N -->, prose el blocks, db:ids on major sections, blank line before tables.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]


def slug(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")[:80] or "section"


def render_pdf(pdf: Path, out_dir: Path, zoom: float = 2.0, force: bool = False) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf)
    mat = fitz.Matrix(zoom, zoom)
    n = 0
    for i in range(doc.page_count):
        dest = out_dir / f"page_{i + 1:03d}.png"
        if dest.exists() and not force and dest.stat().st_size > 1000:
            n += 1
            continue
        pix = doc[i].get_pixmap(matrix=mat, alpha=False)
        pix.save(str(dest))
        n += 1
        if (i + 1) % 25 == 0:
            print(f"  rendered {i + 1}/{doc.page_count}", flush=True)
    print(f"render done {doc.page_count} pages -> {out_dir}", flush=True)
    return doc.page_count


def ocr_page(png: Path) -> str:
    r = subprocess.run(
        ["tesseract", str(png), "stdout", "-l", "eng", "--psm", "6"],
        capture_output=True,
        text=True,
        timeout=180,
        encoding="utf-8",
        errors="replace",
    )
    return (r.stdout or "").strip()


def clean_ocr(text: str) -> str:
    # Normalize whitespace; keep paragraph breaks
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", ln).rstrip() for ln in text.split("\n")]
    # Drop near-empty runs
    out: list[str] = []
    blank = 0
    for ln in lines:
        if not ln.strip():
            blank += 1
            if blank <= 1:
                out.append("")
            continue
        blank = 0
        out.append(ln)
    return "\n".join(out).strip()


def looks_like_heading(ln: str) -> bool:
    s = ln.strip()
    if len(s) < 3 or len(s) > 90:
        return False
    if re.match(r"^\d+(\.\d+)*\s+\S", s):
        return True
    if s.isupper() and sum(c.isalpha() for c in s) >= 4:
        return True
    if re.match(
        r"^(Preface|Introduction|Chapter|Appendix|Language functions|General notions|"
        r"Specific notions|Verbal exchange|Sociocultural|Compensation|Learning to learn|"
        r"Degree of skill|Pronunciation|Grammatical|Contents|Table of contents)\b",
        s,
        re.I,
    ):
        return True
    return False


def format_page_body(page_num: int, text: str, job_id: str) -> str:
    text = clean_ocr(text)
    if not text:
        return (
            f"<!-- el:start type=prose id=prose_p{page_num:03d}_empty page={page_num} -->\n"
            f"<!-- empty or image-only page; see work/{job_id}/page_renders/page_{page_num:03d}.png -->\n"
            f"<!-- el:end id=prose_p{page_num:03d}_empty -->\n\n"
            f"*Page **{page_num}***\n"
        )
    lines = text.split("\n")
    blocks: list[str] = []
    para: list[str] = []

    def flush_para() -> None:
        nonlocal para
        if not para:
            return
        body = " ".join(para).strip()
        para = []
        if not body:
            return
        # light heading promotion
        if looks_like_heading(body) and len(body) < 80:
            if re.match(r"^\d+\s+", body) or body.isupper() or body[:1].isupper():
                blocks.append(f"## {body.title() if body.isupper() else body}")
                return
        blocks.append(body)

    for ln in lines:
        if not ln.strip():
            flush_para()
            continue
        if looks_like_heading(ln) and not para:
            flush_para()
            h = ln.strip()
            if h.isupper() and len(h) > 4:
                h = h.title()
            blocks.append(f"## {h}")
            continue
        para.append(ln.strip())
    flush_para()

    content = "\n\n".join(blocks)
    pid = f"prose_p{page_num:03d}"
    return (
        f"<!-- el:start type=prose id={pid} page={page_num} -->\n"
        f"{content}\n"
        f"<!-- el:end id={pid} -->\n\n"
        f"*Page **{page_num}***\n"
    )


def assemble(
    job_id: str,
    title: str,
    pdf_name: str,
    n_pages: int,
    ocr_dir: Path,
    override_dir: Path | None,
    out_md: Path,
) -> None:
    parts: list[str] = []
    parts.append(
        f"<!-- el:start type=prose id=prose_p001_doc page=1 -->\n"
        f"<!-- db:id={slug(job_id)} type=document product_tier=context pages=1-{n_pages} -->\n\n"
        f"# {title}\n\n"
        f"<!-- source: input/{job_id}/{pdf_name} -->\n"
        f"<!-- extraction: vision+OCR assembly (Companion-quality product conventions) -->\n"
        f"<!-- el:end id=prose_p001_doc -->\n\n"
    )

    for p in range(1, n_pages + 1):
        override = None
        if override_dir:
            op = override_dir / f"page_{p:03d}.md"
            if op.exists():
                override = op.read_text(encoding="utf-8").strip()
        if override:
            body = override + "\n\n" + f"*Page **{p}***\n"
        else:
            ocr_file = ocr_dir / f"page_{p:03d}.txt"
            text = ocr_file.read_text(encoding="utf-8", errors="replace") if ocr_file.exists() else ""
            # Prefer native PDF text if OCR empty and pdf has text
            body = format_page_body(p, text, job_id)
        parts.append(body)
        parts.append(f"\n<!-- page:{p} -->\n\n")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("".join(parts), encoding="utf-8")
    print(f"wrote {out_md} chars={out_md.stat().st_size}", flush=True)


def ocr_all(render_dir: Path, ocr_dir: Path, force: bool = False) -> None:
    ocr_dir.mkdir(parents=True, exist_ok=True)
    pages = sorted(render_dir.glob("page_*.png"))
    for i, png in enumerate(pages, 1):
        dest = ocr_dir / (png.stem + ".txt")
        if dest.exists() and not force and dest.stat().st_size > 20:
            continue
        text = ocr_page(png)
        dest.write_text(text, encoding="utf-8")
        if i % 20 == 0:
            print(f"  ocr {i}/{len(pages)}", flush=True)
    print(f"ocr done {len(pages)} -> {ocr_dir}", flush=True)


def native_pdf_text_pages(pdf: Path, ocr_dir: Path) -> int:
    """If PDF has native text, seed OCR files from it (faster/better than tesseract)."""
    ocr_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf)
    seeded = 0
    for i in range(doc.page_count):
        t = doc[i].get_text("text").strip()
        if len(t) < 40:
            continue
        dest = ocr_dir / f"page_{i + 1:03d}.txt"
        # Prefer native when longer than existing OCR
        if dest.exists() and dest.stat().st_size > len(t.encode("utf-8")):
            continue
        dest.write_text(t, encoding="utf-8")
        seeded += 1
    print(f"native text seeded {seeded}/{doc.page_count}", flush=True)
    return doc.page_count


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--render-only", action="store_true")
    ap.add_argument("--ocr-only", action="store_true")
    ap.add_argument("--assemble-only", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--zoom", type=float, default=2.0)
    args = ap.parse_args()

    job = args.job
    pdf = ROOT / "input" / job / "source.pdf"
    if not pdf.exists():
        sys.exit(f"missing {pdf}")
    render_dir = ROOT / "work" / job / "page_renders"
    ocr_dir = ROOT / "work" / job / "page_ocr"
    override_dir = ROOT / "work" / job / "page_overrides"
    out_md = ROOT / "output" / job / {
        "cefr-threshold-1990": "Threshold_1990.md",
        "cefr-waystage-1990": "Waystage_1990.md",
        "cefr-en-2001": "CEFR_EN_2001.md",
    }.get(job, f"{job}.md")

    if not args.ocr_only and not args.assemble_only:
        n = render_pdf(pdf, render_dir, zoom=args.zoom, force=args.force)
    else:
        n = len(list(render_dir.glob("page_*.png"))) or fitz.open(pdf).page_count

    if args.render_only:
        return

    if not args.assemble_only:
        native_pdf_text_pages(pdf, ocr_dir)
        # OCR only pages still weak
        for png in sorted(render_dir.glob("page_*.png")):
            dest = ocr_dir / (png.stem + ".txt")
            if dest.exists() and dest.stat().st_size > 80 and not args.force:
                continue
            text = ocr_page(png)
            if not dest.exists() or len(text) > dest.stat().st_size:
                dest.write_text(text, encoding="utf-8")
        print("ocr pass complete", flush=True)

    if args.ocr_only:
        return

    assemble(job, args.title, "source.pdf", n, ocr_dir, override_dir if override_dir.exists() else None, out_md)


if __name__ == "__main__":
    main()
