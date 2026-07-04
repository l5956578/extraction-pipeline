"""Extract prose and headings above descriptor-scale tables on a PDF page."""

from __future__ import annotations

import re

import fitz
import pdfplumber

from pipeline.page_layout import _span_text
from pipeline.toc_format import format_numbered_heading

_SECTION_LINE = re.compile(r"^(\d+(?:\.\d+)+)\.\s+(.+)$", re.I)
_LEVEL_ONLY = re.compile(r"^(C2|C1|B2\+?|B1\+?|A2\+?|A1\+?|Pre-A1|Pre A1)$", re.I)
_BULLET = re.compile(r"^f\s+", re.I)


def _table_bboxes(pdf_path, page_idx: int) -> list[tuple[float, float, float, float]]:
    with pdfplumber.open(pdf_path) as pdf:
        if page_idx < 0 or page_idx >= len(pdf.pages):
            return []
        tables = pdf.pages[page_idx].find_tables()
        return sorted([t.bbox for t in tables], key=lambda b: b[1])


def _prose_zones(
    page: fitz.Page, bboxes: list[tuple[float, float, float, float]]
) -> list[tuple[float, float]]:
    if not bboxes:
        return [(0.0, page.rect.height * 0.55)]
    zones: list[tuple[float, float]] = [(0.0, bboxes[0][1] - 4)]
    for i in range(len(bboxes) - 1):
        zones.append((bboxes[i][3] + 4, bboxes[i + 1][1] - 4))
    return zones


def section_headers_from_page(page: fitz.Page) -> list[str]:
    """Numbered section headings present on this PDF page (for inventory/validation)."""
    return [text for text, _ in section_headers_with_y(page)]


def section_headers_with_y(page: fitz.Page) -> list[tuple[str, float]]:
    """Numbered section headings with y-position on this PDF page."""
    headers: list[tuple[str, float]] = []
    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            text = "".join(sp.get("text", "") for sp in line.get("spans", [])).strip()
            if _SECTION_LINE.match(text):
                headers.append((text, line["bbox"][1]))
    headers.sort(key=lambda item: item[1])
    return headers


def _format_prose_line(text: str, scale_title: str | None = None) -> str:
    m = _SECTION_LINE.match(text.strip())
    if m:
        numbered = format_numbered_heading(f"{m.group(1)}. {m.group(2).strip()}")
        if numbered:
            return numbered
    stripped = text.strip()
    if scale_title and stripped.lower() == scale_title.strip().lower():
        return f"### {stripped}"
    if scale_title and stripped.lower().startswith(scale_title.strip().lower()):
        rest = stripped[len(scale_title.strip()) :].strip()
        if rest:
            return f"### {scale_title.strip()}\n\n{rest}"
        return f"### {stripped}"
    return stripped


def _rows_in_zone(page: fitz.Page, y_min: float, y_max: float) -> list[tuple[float, str]]:
    rows: list[tuple[float, str]] = []
    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            y0 = line["bbox"][1]
            if y0 < y_min or y0 >= y_max:
                continue
            text = _span_text(line.get("spans", [])).strip()
            if not text or _LEVEL_ONLY.match(text):
                continue
            if text.lower().startswith("page "):
                continue
            rows.append((y0, text))
    rows.sort(key=lambda r: r[0])
    return rows


def _format_rows(rows: list[tuple[float, str]], scale_title: str | None = None) -> str:
    if not rows:
        return ""

    parts: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        if buf:
            parts.append(" ".join(buf))
            buf.clear()

    title_emitted = False
    for _, text in rows:
        if _BULLET.match(text):
            flush()
            parts.append(f"- {text[1:].strip()}")
            continue
        formatted = _format_prose_line(text, scale_title if not title_emitted else None)
        if formatted.startswith("### "):
            title_emitted = True
        if formatted.startswith("#"):
            flush()
            parts.append(formatted)
            continue
        if "\n\n" in formatted:
            flush()
            parts.append(formatted)
            continue
        if buf and formatted[0].isupper() and buf[-1].endswith((".", ":", ";")):
            flush()
        buf.append(formatted)

    flush()
    return "\n\n".join(parts)


def extract_descriptor_prose(
    page: fitz.Page,
    page_num: int,
    pdf_path,
    scale_title: str | None = None,
    zone_index: int | None = None,
) -> str:
    """Return prose/headings above descriptor table(s), not table row content."""
    bboxes = _table_bboxes(pdf_path, page_num - 1)
    zones = _prose_zones(page, bboxes)
    if zone_index is not None:
        zones = [zones[zone_index]] if 0 <= zone_index < len(zones) else []

    chunks: list[str] = []
    for y_min, y_max in zones:
        rows = _rows_in_zone(page, y_min, y_max)
        block = _format_rows(rows, scale_title)
        if block:
            chunks.append(block)
    return "\n\n".join(chunks)


def _title_from_pdf_table(pdf_path, page_idx: int, table_index: int) -> str | None:
    with pdfplumber.open(pdf_path) as pdf:
        tables = pdf.pages[page_idx].extract_tables() or []
        if table_index < 0 or table_index >= len(tables):
            return None
        row0 = tables[table_index][0] if tables[table_index] else None
        if not row0:
            return None
        for cell in row0:
            if cell and str(cell).strip():
                return re.sub(r"\s+", " ", str(cell).strip())
    return None


def extract_prose_zone(
    page: fitz.Page,
    bbox: list[float],
    scale_title: str | None = None,
) -> str:
    """Extract prose within an inventory-defined bounding box."""
    y_min, y_max = bbox[1], bbox[3]
    rows = _rows_in_zone(page, y_min, y_max)
    return _format_rows(rows, scale_title)


def extract_trailing_prose(page: fitz.Page, page_num: int, pdf_path) -> str:
    """Prose below the last table (next section header, scale intro) before the footer."""
    bboxes = _table_bboxes(pdf_path, page_num - 1)
    if not bboxes:
        return ""
    y_min = bboxes[-1][3] + 4
    y_max = page.rect.height - 30
    rows = _rows_in_zone(page, y_min, y_max)
    return _format_rows(rows)


def interstitial_prose_blocks(
    page: fitz.Page, page_num: int, pdf_path
) -> list[tuple[int, str]]:
    """Prose between consecutive tables: (table_index, markdown)."""
    bboxes = _table_bboxes(pdf_path, page_num - 1)
    if len(bboxes) < 2:
        return []
    blocks: list[tuple[int, str]] = []
    for i in range(len(bboxes) - 1):
        rows = _rows_in_zone(page, bboxes[i][3] + 4, bboxes[i + 1][1] - 4)
        next_title = _title_from_pdf_table(pdf_path, page_num - 1, i + 1)
        block = _format_rows(rows, next_title)
        if block:
            blocks.append((i + 1, block))
    return blocks