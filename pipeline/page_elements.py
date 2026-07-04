"""Build canonical per-page reading-order element lists for extraction."""

from __future__ import annotations

import re
from typing import Any

import fitz
import pdfplumber

from pipeline.config import KNOWN_TABLES_FIGURES, PDF_PATH, SECTION_BLOCKS, TOC_PAGE_RANGE
from pipeline.descriptor_layout import section_headers_from_page
from pipeline.page_layout import _classify_line, _span_text
from pipeline.title_fix import fix_rotated_title
from pipeline.utils import slugify

_LEVEL_ONLY = re.compile(r"^(C2|C1|B2\+?|B1\+?|A2\+?|A1\+?|Pre-A1|Pre A1)$", re.I)
_FOOTER_BODY_CUTOFF = 0.62


def page_rotation(page: fitz.Page) -> tuple[str, int]:
    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            d = line.get("dir", (1, 0))
            if abs(d[1]) > 0.3:
                if d[1] > 0:
                    return "rotated_270", 270
                return "rotated_90", 90
    return "normal", 0


def table_bboxes(pdf_path, page_idx: int) -> list[tuple[float, float, float, float]]:
    with pdfplumber.open(pdf_path) as pdf:
        if page_idx < 0 or page_idx >= len(pdf.pages):
            return []
        tables = pdf.pages[page_idx].find_tables()
        return sorted([t.bbox for t in tables], key=lambda b: b[1])


def collect_body_lines(page: fitz.Page) -> list[tuple[float, float, str]]:
    page_height = page.rect.height
    entries: list[tuple[float, float, str]] = []
    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            text = _span_text(line.get("spans", [])).strip()
            if not text or _LEVEL_ONLY.match(text):
                continue
            y0 = line["bbox"][1]
            x0 = line["bbox"][0]
            kind = _classify_line(text, y0, page_height)
            if kind == "body" and y0 < page_height * _FOOTER_BODY_CUTOFF:
                entries.append((y0, x0, text))
    return entries


def _lines_in_bbox(
    lines: list[tuple[float, float, str]],
    y0: float,
    y1: float,
) -> list[tuple[float, float, str]]:
    return [(y, x, t) for y, x, t in lines if y0 <= y < y1]


def prose_segments(
    page: fitz.Page,
    table_bboxes_list: list[tuple[float, float, float, float]],
) -> list[dict[str, Any]]:
    lines = collect_body_lines(page)
    page_h = page.rect.height
    page_w = page.rect.width

    if not table_bboxes_list:
        if not lines:
            return []
        y0 = min(y for y, _, _ in lines)
        y1 = max(y for y, _, _ in lines) + 12
        return [
            {
                "role": "body",
                "y0": y0,
                "y1": y1,
                "bbox": [0, y0, page_w, min(y1 + 8, page_h * _FOOTER_BODY_CUTOFF)],
            }
        ]

    segments: list[dict[str, Any]] = []
    if table_bboxes_list[0][1] > 8:
        y1 = table_bboxes_list[0][1] - 4
        seg_lines = _lines_in_bbox(lines, 0, y1)
        if seg_lines:
            segments.append(
                {
                    "role": "intro",
                    "y0": seg_lines[0][0],
                    "y1": y1,
                    "bbox": [0, 0, page_w, y1],
                }
            )

    for i in range(len(table_bboxes_list) - 1):
        y0 = table_bboxes_list[i][3] + 4
        y1 = table_bboxes_list[i + 1][1] - 4
        seg_lines = _lines_in_bbox(lines, y0, y1)
        if seg_lines:
            segments.append(
                {
                    "role": "interstitial",
                    "y0": y0,
                    "y1": y1,
                    "bbox": [0, y0, page_w, y1],
                    "after_table_index": i,
                }
            )

    y0 = table_bboxes_list[-1][3] + 4
    y1 = page_h - 28
    seg_lines = _lines_in_bbox(lines, y0, y1)
    if seg_lines:
        segments.append(
            {
                "role": "trailing",
                "y0": y0,
                "y1": y1,
                "bbox": [0, y0, page_w, y1],
            }
        )
    return segments


def expected_chars(page: fitz.Page, bbox: list[float]) -> int:
    y0, y1 = bbox[1], bbox[3]
    chars = 0
    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            ly = line["bbox"][1]
            if ly < y0 or ly >= y1:
                continue
            chars += len(_span_text(line.get("spans", [])).strip())
    return max(0, int(chars * 0.85))


def _span_dict(span_info: dict | None) -> dict[str, Any] | None:
    if not span_info:
        return None
    return {
        "group_id": span_info["group_id"],
        "span_type": span_info["span_type"],
        "role": span_info["role"],
        "pages": list(range(span_info["start_page"], span_info["end_page"] + 1)),
        "emit_body_on": span_info["start_page"],
    }


def _table_title_at(pdf_path, page_idx: int, table_index: int) -> str | None:
    with pdfplumber.open(pdf_path) as pdf:
        tables = pdf.pages[page_idx].extract_tables() or []
        if table_index < 0 or table_index >= len(tables):
            return None
        row0 = tables[table_index][0] if tables[table_index] else None
        if not row0:
            return None
        for cell in row0:
            if cell and str(cell).strip():
                return fix_rotated_title(re.sub(r"\s+", " ", str(cell).strip()))
    return None


def _artifact_element(
    page_num: int,
    bbox: tuple[float, float, float, float],
    orientation: str,
    rotation: int,
    art: Any | None,
    span_info: dict | None,
    table_index: int = 0,
    pdf_path=PDF_PATH,
    attach_span: bool = False,
) -> dict[str, Any]:
    display_title = None
    artifact_id = None
    artifact_type = "descriptor_scale"
    if art:
        display_title = fix_rotated_title(art.display_name)
        artifact_id = art.id
        artifact_type = art.artifact_type
    if span_info and span_info.get("group_id"):
        artifact_id = artifact_id or span_info["group_id"]

    if page_num in KNOWN_TABLES_FIGURES:
        artifact_id, display_title, artifact_type = KNOWN_TABLES_FIGURES[page_num]

    if not display_title:
        display_title = _table_title_at(pdf_path, page_num - 1, table_index)
    if not artifact_id and display_title:
        artifact_id = slugify(display_title, prefix="scale")

    extractor = "pdfplumber_table"
    text_direction = "normal"
    if orientation.startswith("rotated"):
        extractor = "rotated_table"
        text_direction = "ocr"

    el: dict[str, Any] = {
        "type": "artifact",
        "artifact_type": artifact_type,
        "artifact_id": artifact_id,
        "display_title": display_title,
        "y0": bbox[1],
        "y1": bbox[3],
        "bbox": list(bbox),
        "extractor": extractor,
        "rotation": rotation,
        "text_direction": text_direction,
        "span": _span_dict(span_info) if attach_span else None,
    }
    return el


def build_reading_order(
    page_num: int,
    page: fitz.Page,
    pdf_path=PDF_PATH,
    span_info: dict | None = None,
    art: Any | None = None,
    content_type: str = "mixed",
) -> list[dict[str, Any]]:
    """Return ordered extractable elements for one PDF page."""
    if page_num in TOC_PAGE_RANGE:
        return [{"seq": 0, "type": "toc", "extractor": "toc_layout"}]

    if content_type == "blank":
        return [{"seq": 0, "type": "footer", "extractor": "page_footer"}]

    orientation, rotation = page_rotation(page)

    if span_info and span_info.get("span_type") == "section_block":
        if page_num > span_info["start_page"]:
            return [
                {"seq": 0, "type": "span_continuation_skip", "span": _span_dict(span_info)},
                {"seq": 1, "type": "footer", "extractor": "page_footer"},
            ]
        block = next((b for b in SECTION_BLOCKS if b["id"] == span_info["group_id"]), None)
        return [
            {
                "seq": 0,
                "type": "artifact",
                "artifact_type": "section_block",
                "artifact_id": span_info["group_id"],
                "display_title": block["display_name"] if block else span_info["group_id"],
                "extractor": "section_block_merge",
                "rotation": rotation,
                "text_direction": "ocr" if orientation.startswith("rotated") else "normal",
                "span": _span_dict(span_info),
            },
            {"seq": 1, "type": "footer", "extractor": "page_footer"},
        ]

    if art and art.artifact_type == "figure":
        return [
            {"seq": 0, "type": "figure_page", "extractor": "rich_page", "artifact_id": art.id},
            {"seq": 1, "type": "footer", "extractor": "page_footer"},
        ]

    if content_type == "pure_text":
        return [
            {"seq": 0, "type": "prose", "role": "body", "extractor": "rich_page"},
            {"seq": 1, "type": "footer", "extractor": "page_footer"},
        ]

    if (
        span_info
        and span_info.get("span_type") == "continuation"
        and page_num > span_info["start_page"]
    ):
        return [
            {"seq": 0, "type": "span_continuation_skip", "span": _span_dict(span_info)},
            {"seq": 1, "type": "footer", "extractor": "page_footer"},
        ]

    bboxes = table_bboxes(pdf_path, page_num - 1)
    prose_segs = prose_segments(page, bboxes)
    headers = section_headers_from_page(page)

    elements: list[dict[str, Any]] = []
    seq = 0
    prose_idx = 0
    table_idx = 0
    span_start = span_info and span_info.get("role") == "start"

    while prose_idx < len(prose_segs) or table_idx < len(bboxes):
        next_prose = prose_segs[prose_idx] if prose_idx < len(prose_segs) else None
        next_table = bboxes[table_idx] if table_idx < len(bboxes) else None

        if next_prose and (not next_table or next_prose["y0"] < next_table[1]):
            expected = expected_chars(page, next_prose["bbox"])
            el: dict[str, Any] = {
                "seq": seq,
                "type": "prose",
                "role": next_prose["role"],
                "y0": next_prose["y0"],
                "y1": next_prose["y1"],
                "bbox": next_prose["bbox"],
                "extractor": "prose_zone",
                "expected_chars": expected,
            }
            if next_prose["role"] == "intro" and headers:
                el["section_headers"] = headers
            elements.append(el)
            seq += 1
            prose_idx += 1
        elif next_table:
            art_el = _artifact_element(
                page_num,
                next_table,
                orientation,
                rotation,
                art,
                span_info,
                table_index=table_idx,
                pdf_path=pdf_path,
                attach_span=bool(span_start and table_idx == 0),
            )
            art_el["seq"] = seq
            art_el["table_index"] = table_idx
            elements.append(art_el)
            seq += 1
            table_idx += 1
            if span_start:
                break
        else:
            break

    while prose_idx < len(prose_segs):
        seg = prose_segs[prose_idx]
        if seg["role"] in ("interstitial", "trailing"):
            elements.append(
                {
                    "seq": seq,
                    "type": "prose",
                    "role": seg["role"],
                    "y0": seg["y0"],
                    "y1": seg["y1"],
                    "bbox": seg["bbox"],
                    "extractor": "prose_zone",
                    "expected_chars": expected_chars(page, seg["bbox"]),
                }
            )
            seq += 1
        prose_idx += 1

    elements.append({"seq": seq, "type": "footer", "extractor": "page_footer"})
    return elements