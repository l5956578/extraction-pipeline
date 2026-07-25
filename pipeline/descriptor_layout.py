"""Extract prose and headings above descriptor-scale tables on a PDF page."""

from __future__ import annotations

import re

import fitz
import pdfplumber

from pipeline.page_layout import (
    _PARAGRAPH_Y_GAP,
    _classify_line,
    _span_text,
    first_footer_band_y,
)
from pipeline.toc_format import format_numbered_heading

# Allow outer **bold** wrappers from PDF span flags.
_SECTION_LINE = re.compile(r"^(\d+(?:\.\d+)+)\.\s+(.+)$", re.I)
_TABLE_TITLE = re.compile(
    r"^Table\s+\d+\s*[–—\-]\s+.+$",
    re.I,
)
_LEVEL_ONLY = re.compile(r"^(C2|C1|B2\+?|B1\+?|A2\+?|A1\+?|Pre-A1|Pre A1)$", re.I)
# Wingdings bullet decodes as "f"; may sit tight against bold "**Guide..."
_BULLET = re.compile(r"^f(?:\s+|\*\*\s*|\s*\*\*)", re.I)


def _strip_outer_markdown_bold(text: str) -> str:
    """Remove wrapping ``**…**`` (and stray edge asterisks) for pattern matching."""
    s = text.strip()
    if s.startswith("**") and s.endswith("**") and len(s) > 4:
        inner = s[2:-2].strip()
        # Only unwrap when the whole line is one bold run (no internal ** pairs left unbalanced).
        if "**" not in inner:
            return inner
    s = re.sub(r"^\*+\s*", "", s)
    s = re.sub(r"\s*\*+$", "", s)
    return s.strip()


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
            plain = _strip_outer_markdown_bold(text)
            if _SECTION_LINE.match(plain) or _SECTION_LINE.match(text):
                headers.append((plain if _SECTION_LINE.match(plain) else text, line["bbox"][1]))
    headers.sort(key=lambda item: item[1])
    return headers


def _format_prose_line(text: str, scale_title: str | None = None) -> str:
    stripped = text.strip()
    plain = _strip_outer_markdown_bold(stripped)

    m = _SECTION_LINE.match(plain) or _SECTION_LINE.match(stripped)
    if m:
        numbered = format_numbered_heading(f"{m.group(1)}. {m.group(2).strip()}")
        if numbered:
            return numbered
        # Keep bold section lines as their own block when not mapped to ###.
        return f"**{plain}**" if plain != stripped else stripped

    if _TABLE_TITLE.match(plain) or _TABLE_TITLE.match(stripped):
        # Table caption above the artifact (not the db header line).
        return f"**{plain}**"

    if scale_title:
        st = scale_title.strip()
        if plain.lower() == st.lower() or stripped.lower() == st.lower():
            return f"### {st}"
        if plain.lower().startswith(st.lower()):
            rest = plain[len(st) :].strip()
            if rest:
                return f"### {st}\n\n{rest}"
            return f"### {st}"

    return stripped


def _is_structural_prose_line(raw: str, formatted: str) -> bool:
    """Headings, table captions, bullets — never soft-join into adjacent prose."""
    if formatted.startswith("#"):
        return True
    plain = _strip_outer_markdown_bold(raw)
    if _SECTION_LINE.match(plain) or _SECTION_LINE.match(raw.strip()):
        return True
    if _TABLE_TITLE.match(plain) or _TABLE_TITLE.match(raw.strip()):
        return True
    if formatted.startswith("**Table ") and _TABLE_TITLE.match(
        _strip_outer_markdown_bold(formatted)
    ):
        return True
    return False


def _rows_in_zone(
    page: fitz.Page,
    y_min: float,
    y_max: float,
    x_min: float | None = None,
    x_max: float | None = None,
) -> list[tuple[float, str]]:
    rows: list[tuple[float, str]] = []
    page_h = page.rect.height
    page_w = page.rect.width
    # Even if inventory bbox is stale/wide, never read into the footnote band.
    band_y = first_footer_band_y(page)
    y_max = min(y_max, band_y)
    x0_lim = 0.0 if x_min is None else float(x_min)
    x1_lim = page_w if x_max is None else float(x_max)
    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            y0 = line["bbox"][1]
            lx0 = line["bbox"][0]
            if y0 < y_min or y0 >= y_max:
                continue
            # Side-column prose (Ch2 p.29): respect x bounds so right-column
            # table text is not interleaved into the left column.
            if lx0 < x0_lim - 2 or lx0 >= x1_lim:
                continue
            text = _span_text(line.get("spans", [])).strip()
            if not text or _LEVEL_ONLY.match(text):
                continue
            # Never pull footnotes / page footers into prose zones (spanning table tails).
            kind = _classify_line(text, y0, page_h)
            if kind in ("footnote", "page_marker", "skip"):
                continue
            if text.lower().startswith("page "):
                continue
            # Tab-only / empty bold glitches from dingbat rows
            if re.fullmatch(r"\*+\s*\*+", text) or not re.sub(r"[\*\s\t]", "", text):
                continue
            # Drop a single orphan trailing * from broken bold runs
            if text.endswith("*") and not text.endswith("**") and text.count("*") % 2 == 1:
                text = text.rstrip("*").rstrip()
            rows.append((y0, text))
    rows.sort(key=lambda r: r[0])
    return rows


def _format_rows(rows: list[tuple[float, str]], scale_title: str | None = None) -> str:
    """Join zone lines with y-gap paragraphs; keep section/table titles as own blocks."""
    if not rows:
        return ""

    parts: list[str] = []
    buf: list[str] = []
    prev_y: float | None = None

    def flush() -> None:
        if buf:
            parts.append(" ".join(buf))
            buf.clear()

    title_emitted = False
    for y, text in rows:
        bm = _BULLET.match(text)
        if bm:
            flush()
            rest = text[bm.end() :].lstrip()
            parts.append(f"- {rest}" if rest else "-")
            prev_y = y
            continue

        formatted = _format_prose_line(text, scale_title if not title_emitted else None)
        if formatted.startswith("### "):
            title_emitted = True

        if "\n\n" in formatted:
            flush()
            parts.append(formatted)
            prev_y = y
            continue

        if _is_structural_prose_line(text, formatted) or formatted.startswith("#"):
            flush()
            parts.append(formatted)
            prev_y = y
            continue

        # Soft-wrap tails of a bullet list item (gap < paragraph threshold).
        if (
            parts
            and not buf
            and parts[-1].startswith("- ")
            and prev_y is not None
            and y - prev_y < _PARAGRAPH_Y_GAP
        ):
            parts[-1] = f"{parts[-1].rstrip()} {formatted}"
            prev_y = y
            continue

        # Soft-wrap vs true paragraph: same threshold as full-page body extract.
        if buf and prev_y is not None and y - prev_y >= _PARAGRAPH_Y_GAP:
            flush()

        buf.append(formatted)
        prev_y = y

    flush()
    # Drop empty/junk paragraphs (e.g. leftover **** from dingbat/bold glitches)
    cleaned = []
    for p in parts:
        p2 = re.sub(r"^(?:\*\*\s*)+$", "", p.strip())
        p2 = re.sub(r"\s+\*\*\*\*\s*", " ", p2).strip()
        if p2:
            cleaned.append(p2)
    return "\n\n".join(cleaned)


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
    """Extract prose within an inventory-defined bounding box (x and y)."""
    x_min, y_min, x_max, y_max = bbox[0], bbox[1], bbox[2], bbox[3]
    rows = _rows_in_zone(page, y_min, y_max, x_min=x_min, x_max=x_max)
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