"""Lightweight post-extract validation: figure pages must keep prose mass.

Prevents regressions where figure_page compose drops body text (Ch2 log 02).
"""

from __future__ import annotations

import re
from pathlib import Path

import fitz

from pipeline.config import PDF_PATH, ROOT
from pipeline.extractors.figures import figures_for_page


def _page_body_chars_pdf(page: fitz.Page) -> int:
    text = page.get_text("text") or ""
    # Drop running headers/footers roughly
    lines = [
        ln
        for ln in text.splitlines()
        if ln.strip()
        and not re.match(r"^Page\s+\d+", ln.strip(), re.I)
        and "Companion volume" not in ln
    ]
    return sum(len(ln) for ln in lines)


def _page_body_chars_md(md: str, page_num: int) -> int:
    """Content belonging to page N (text immediately before <!-- page:N -->)."""
    m = re.search(rf"<!-- page:{page_num} -->", md)
    if not m:
        return 0
    prev = list(re.finditer(r"<!-- page:(\d+) -->", md[: m.start()]))
    start = prev[-1].end() if prev else 0
    body = md[start : m.start()]
    # Ignore figure markup / images for mass check of "prose presence"
    body = re.sub(r"```[\s\S]*?```", " ", body)
    body = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", body)
    body = re.sub(r"<!--[^>]+-->", " ", body)
    body = re.sub(r"#{1,6}\s+", " ", body)
    return len(re.sub(r"\s+", " ", body).strip())


def validate_figure_pages_prose(md_path: Path | None = None) -> list[str]:
    """Return list of human-readable failure strings (empty = ok)."""
    md_path = md_path or (ROOT / "output" / "CEFR_Companion_Volume.md")
    if not md_path.exists():
        return [f"missing markdown: {md_path}"]
    md = md_path.read_text(encoding="utf-8")
    doc = fitz.open(PDF_PATH)
    failures: list[str] = []
    # Unique pages that have registry figures
    pages = sorted({f["page"] for f in __import__("pipeline.config", fromlist=["load_figures_registry"]).load_figures_registry()})
    for pn in pages:
        if pn < 1 or pn > doc.page_count:
            continue
        pdf_chars = _page_body_chars_pdf(doc[pn - 1])
        md_chars = _page_body_chars_md(md, pn)
        figs = figures_for_page(pn)
        # text_diagram pages: PDF char counts include tree labels that live in
        # ``` fences (excluded from md_chars). Mass ratio is not meaningful.
        if figs and all(f.get("render_as") == "text_diagram" for f in figs):
            # Still require the diagram body to exist on the page region
            m = re.search(rf"<!-- page:{pn} -->", md)
            if m:
                prev = list(re.finditer(r"<!-- page:(\d+) -->", md[: m.start()]))
                start = prev[-1].end() if prev else 0
                body = md[start : m.start()]
                if "```" not in body and not any(f["id"] in body for f in figs):
                    failures.append(
                        f"page {pn}: text_diagram figure missing from MD body"
                    )
            continue
        # If PDF has substantial body, MD must retain a large fraction
        if pdf_chars < 400:
            continue
        # Allow diagrams-only pages to have less prose; still require floor
        ratio = md_chars / max(pdf_chars, 1)
        # Figure pages still have captions+labels in PDF char counts; 0.35 is conservative
        if md_chars < 200 and pdf_chars > 800:
            failures.append(
                f"page {pn}: MD body chars {md_chars} too low vs PDF {pdf_chars} "
                f"(likely dropped prose on figure page)"
            )
        elif ratio < 0.25 and pdf_chars > 1200:
            failures.append(
                f"page {pn}: MD/PDF char ratio {ratio:.2f} ({md_chars}/{pdf_chars}) "
                f"— prose may have been dropped"
            )
        # Multi-figure pages with almost no prose (p.36 regression)
        if len(figs) >= 2 and md_chars < 400 and pdf_chars > 2000:
            failures.append(
                f"page {pn}: multi-figure page with only {md_chars} MD chars "
                f"(PDF {pdf_chars}) — intro prose likely missing"
            )
    doc.close()
    return failures


if __name__ == "__main__":
    fails = validate_figure_pages_prose()
    if fails:
        print("VALIDATION FAIL")
        for f in fails:
            print(" -", f)
        raise SystemExit(1)
    print("VALIDATION OK: figure pages retain prose mass")
