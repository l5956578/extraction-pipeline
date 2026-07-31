#!/usr/bin/env python3
"""Repair chrome-only MD page bodies by injecting PDF-extracted content.

For pages whose MD body is essentially only running headers/footers while the
PDF page has substantial text/tables, insert a page-local block before
<!-- page:N --> so the deliverable is usable page-by-page.

- Does not delete multipage content already present on earlier pages.
- Prefer pdfplumber tables + fitz text.
- Skip pages that already have real content (>200 chars core).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz
import pdfplumber

ROOT = Path(__file__).resolve().parents[2]
MD_PATH = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"
PDF_PATH = ROOT / "input/cefr-companion-2020/source.pdf"
ROTATED = ROOT / "work/cefr-companion-2020/metadata/rotated_from_grok"


def page_region(md: str, n: int) -> tuple[int, int, str]:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return start, m.start(), md[start : m.start()]
    raise KeyError(n)


def core_len(body: str) -> int:
    t = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    t = re.sub(r"\*[^\n]*Page[^\n]*\*", "", t)
    return len(t.strip())


def cells_to_md(tables: list) -> str:
    chunks = []
    for table in tables or []:
        if not table or len(table) < 2:
            continue
        rows = []
        for row in table:
            cells = [("" if c is None else str(c).replace("\n", "<br>").strip()) for c in row]
            rows.append(cells)
        if not rows:
            continue
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        header = rows[0]
        # if first row looks like levels not header, synthesize
        lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(["---"] * width) + " |",
        ]
        for r in rows[1:]:
            lines.append("| " + " | ".join(r) + " |")
        chunks.append("\n".join(lines))
    return "\n\n".join(chunks)


def prose_from_pdf(text: str) -> str:
    lines = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            continue
        if re.search(r"Page\s+\d+|Companion volume|Illustrative Descriptor Scales", s, re.I):
            continue
        lines.append(s)
    # join hyphenated line breaks lightly
    out = []
    buf = ""
    for s in lines:
        if buf and not buf.endswith((".", ":", ";", "?", "!")) and s and s[0].islower():
            buf = buf + " " + s
        else:
            if buf:
                out.append(buf)
            buf = s
    if buf:
        out.append(buf)
    paras = []
    for s in out:
        # section-like short titles
        if re.match(r"^\d+(\.\d+)+\.?\s+\S", s) and len(s) < 100:
            paras.append(f"### {s}")
        elif len(s) < 80 and not s.endswith((".", "?", "!")) and s[0].isupper():
            paras.append(f"**{s}**")
        else:
            paras.append(s)
    return "\n\n".join(paras)


def rotated_snippet(page: int) -> str:
    if not ROTATED.is_dir():
        return ""
    hits = list(ROTATED.glob(f"page_{page:03d}_*.md")) + list(
        ROTATED.glob(f"*_{page:03d}_*.md")
    )
    # also page_NNN without zero pad patterns
    hits += list(ROTATED.glob(f"page_{page}_*.md"))
    parts = []
    for h in sorted(set(hits))[:3]:
        t = h.read_text(encoding="utf-8", errors="replace").strip()
        if t:
            parts.append(f"<!-- restored from rotated_from_grok/{h.name} -->\n{t}")
    return "\n\n".join(parts)


def build_page_block(page: int, doc: fitz.Document, plumber) -> str:
    # Prefer rotated vision markdown when available (descriptor tables)
    rot = rotated_snippet(page)
    pdf_page = doc[page - 1]
    text = pdf_page.get_text("text") or ""
    tables_md = ""
    try:
        ptables = plumber.pages[page - 1].extract_tables() or []
        tables_md = cells_to_md(ptables)
    except Exception:
        tables_md = ""

    prose = prose_from_pdf(text)
    chunks = [
        f"<!-- el:start type=prose id=prose_p{page:03d}_restored page={page} -->",
        f"<!-- book-qa restore: page {page} content was chrome-only; reconstructed from PDF"
        + (" + rotated_from_grok" if rot else "")
        + " -->",
    ]
    if rot:
        chunks.append(rot)
    if tables_md and "scale_" not in rot:
        chunks.append(tables_md)
    if prose and not rot:
        chunks.append(prose)
    elif prose and rot and len(prose) > 200:
        # light prose only if not redundant
        chunks.append(prose[:500])
    chunks.append(f"<!-- el:end id=prose_p{page:03d}_restored -->")
    body = "\n\n".join(chunks)
    if len(body) < 120:
        return ""
    return body + "\n"


def main() -> int:
    md = MD_PATH.read_text(encoding="utf-8")
    doc = fitz.open(PDF_PATH)
    fixed = []
    skipped = []
    with pdfplumber.open(PDF_PATH) as plumber:
        for page in range(1, len(doc) + 1):
            try:
                start, end, region = page_region(md, page)
            except KeyError:
                continue
            if core_len(region) > 200:
                skipped.append(page)
                continue
            pdf_text = doc[page - 1].get_text("text") or ""
            if len(pdf_text.strip()) < 100:
                skipped.append(page)
                continue
            block = build_page_block(page, doc, plumber)
            if not block or len(block) < 100:
                skipped.append(page)
                continue
            # Keep existing chrome/footer lines after injected block
            chrome = region.strip()
            new_region = "\n" + block + "\n" + (chrome + "\n\n" if chrome else "\n")
            md = md[:start] + new_region + md[end:]
            fixed.append(page)
            print(f"restored page {page} (+{len(block)} chars)", flush=True)

    doc.close()
    MD_PATH.write_text(md, encoding="utf-8")
    print(f"DONE fixed={len(fixed)} pages={fixed}")
    print(f"skipped={len(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
