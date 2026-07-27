"""Build canonical per-page reading-order element lists for extraction."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import fitz
import pdfplumber

import pipeline.config as cfg
from pipeline.config import load_figures_registry
from pipeline.descriptor_layout import section_headers_from_page, section_headers_with_y
from pipeline.page_layout import (
    _classify_line,
    _span_text,
    classify_page_zones,
    first_footer_band_y,
)
from pipeline.title_fix import (
    artifact_id_from_title,
    clean_artifact_id,
    fix_rotated_title,
)
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

def collect_body_lines(
    page: fitz.Page,
    *,
    y_max: float | None = None,
) -> list[tuple[float, float, str]]:
    page_height = page.rect.height
    cut = y_max if y_max is not None else page_height * _FOOTER_BODY_CUTOFF
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
            if kind == "body" and y0 < cut:
                entries.append((y0, x0, text))
    return entries

def _lines_in_bbox(
    lines: list[tuple[float, float, str]],
    y0: float,
    y1: float,
) -> list[tuple[float, float, str]]:
    return [(y, x, t) for y, x, t in lines if y0 <= y < y1]

def _lines_in_rect(
    lines: list[tuple[float, float, str]],
    x0: float,
    y0: float,
    x1: float,
    y1: float,
) -> list[tuple[float, float, str]]:
    """Lines whose baseline y and left x fall inside the rect (generous x)."""
    out: list[tuple[float, float, str]] = []
    for y, x, t in lines:
        if y0 <= y < y1 and x0 - 2 <= x < x1:
            out.append((y, x, t))
    return out

def prose_segments(
    page: fitz.Page,
    table_bboxes_list: list[tuple[float, float, float, float]],
) -> list[dict[str, Any]]:
    page_h = page.rect.height
    page_w = page.rect.width
    foot_y = first_footer_band_y(page)
    # Body lines up to first real footnote/page-marker (not a fixed 62% cut).
    lines = collect_body_lines(page, y_max=foot_y)

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
                "bbox": [0, y0, page_w, min(y1 + 8, foot_y - 2)],
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

    # Side-column prose beside partial-width tables (e.g. p.29 methodological
    # message left of "A reminder of CEFR 2001 chapters" box).
    for i, tb in enumerate(table_bboxes_list):
        tx0, ty0, tx1, ty1 = tb
        band_y0 = ty0 - 2
        band_y1 = min(ty1 + 6, foot_y - 2)
        if band_y1 <= band_y0:
            continue
        # Table on the right → left column prose
        if tx0 > page_w * 0.28:
            left_x1 = tx0 - 6
            side_lines = _lines_in_rect(lines, 0, band_y0, left_x1, band_y1)
            if side_lines and sum(len(t) for _, _, t in side_lines) > 40:
                segments.append(
                    {
                        "role": "side",
                        "y0": min(y for y, _, _ in side_lines),
                        "y1": max(y for y, _, _ in side_lines) + 12,
                        "bbox": [
                            0.0,
                            min(y for y, _, _ in side_lines) - 2,
                            left_x1,
                            min(max(y for y, _, _ in side_lines) + 14, band_y1),
                        ],
                        "parallel_table_index": i,
                        "x0": 0.0,
                    }
                )
        # Table on the left → right column prose
        if tx1 < page_w * 0.72:
            right_x0 = tx1 + 6
            side_lines = _lines_in_rect(lines, right_x0, band_y0, page_w, band_y1)
            if side_lines and sum(len(t) for _, _, t in side_lines) > 40:
                segments.append(
                    {
                        "role": "side",
                        "y0": min(y for y, _, _ in side_lines),
                        "y1": max(y for y, _, _ in side_lines) + 12,
                        "bbox": [
                            right_x0,
                            min(y for y, _, _ in side_lines) - 2,
                            page_w,
                            min(max(y for y, _, _ in side_lines) + 14, band_y1),
                        ],
                        "parallel_table_index": i,
                        "x0": right_x0,
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

    # Trailing prose: below last table, above first footnote / page footer.
    y0 = table_bboxes_list[-1][3] + 4
    y1 = foot_y - 4
    if y1 > y0:
        seg_lines = _lines_in_bbox(lines, y0, y1)
        if seg_lines:
            y1 = min(max(y for y, _, _ in seg_lines) + 14, foot_y - 2)
            segments.append(
                {
                    "role": "trailing",
                    "y0": y0,
                    "y1": y1,
                    "bbox": [0, y0, page_w, y1],
                }
            )

    # Stable reading order: top-to-bottom, then left-to-right for side bands.
    segments.sort(key=lambda s: (round(s["y0"], 1), float(s.get("x0", s["bbox"][0]))))
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

def _span_dict(span_info: dict | None, display_title: str | None = None) -> dict[str, Any] | None:
    if not span_info:
        return None
    gid = clean_artifact_id(span_info.get("group_id"), display_title)
    return {
        "group_id": gid,
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
    pdf_path: Path | None = None,
    attach_span: bool = False,
) -> dict[str, Any]:
    # Resolve at call time — never freeze cfg.PDF_PATH in the default arg.
    if pdf_path is None:
        pdf_path = cfg.PDF_PATH
    display_title = None
    artifact_id = None
    artifact_type = "descriptor_scale"
    if art:
        display_title = fix_rotated_title(art.display_name)
        artifact_id = clean_artifact_id(art.id, display_title)
        artifact_type = art.artifact_type
    if span_info and span_info.get("group_id") and not artifact_id:
        # Prefer clean id; re-slug garbled span group_ids from title
        artifact_id = clean_artifact_id(span_info["group_id"], display_title)

    # Prefer per-(page, table_index) known map (Table 4 etc.) over page-level sole map.
    known_idx = cfg.KNOWN_TABLES_BY_INDEX.get((page_num, table_index))
    if known_idx:
        artifact_id, display_title, artifact_type = known_idx
    elif page_num in cfg.KNOWN_TABLES_FIGURES and table_index == 0:
        artifact_id, display_title, artifact_type = cfg.KNOWN_TABLES_FIGURES[page_num]

    if not display_title:
        display_title = _table_title_at(pdf_path, page_num - 1, table_index)
    if display_title:
        display_title = fix_rotated_title(display_title)
    if not artifact_id and display_title:
        artifact_id = artifact_id_from_title(display_title, prefix="scale")
    elif artifact_id and display_title:
        artifact_id = clean_artifact_id(artifact_id, display_title)

    # Narrative callouts / sidebars are not descriptor scales (CONTRACTS §2–3).
    callout_titles = (
        "a reminder of cefr 2001 chapters",
        "can do” descriptors as competence",
        'can do" descriptors as competence',
        "can do descriptors as competence",
    )
    dt_l = (display_title or "").lower().replace("“", '"').replace("”", '"')
    if any(t in dt_l for t in callout_titles) or (
        display_title
        and artifact_id
        and "reminder_of_cefr" in (artifact_id or "")
    ):
        artifact_type = "callout"
        if artifact_id and artifact_id.startswith("scale_"):
            artifact_id = "callout_" + artifact_id.removeprefix("scale_")

    extractor = "pdfplumber_table"
    text_direction = "normal"
    rotated_extraction_method = "normal"
    extraction_passes: list[str] = []
    if orientation.startswith("rotated"):
        extractor = "rotated_table"
        text_direction = "ocr"
        # Default: agent vision handoff (prepare PNG → write .md → finalize).
        # Geometry/OCR remain fallbacks via rotated_extraction_method override.
        rotated_extraction_method = "grok_vision"
        extraction_passes = [
            "grok_vision_prepare",
            "agent_vision_correct",
            "grok_vision_assemble",
        ]

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
        "rotated_extraction_method": rotated_extraction_method,
        "extraction_passes": extraction_passes,
        "span": _span_dict(span_info, display_title) if attach_span else None,
    }
    return el

def _normalize_caption_text(text: str) -> str:
    s = re.sub(r"\s+", " ", text.strip()).lower()
    for dash in ("–", "—", "−"):
        s = s.replace(dash, "-")
    return s

def _caption_line_matches(line_text: str, caption: str) -> bool:
    norm_line = _normalize_caption_text(line_text)
    norm_cap = _normalize_caption_text(caption)
    if norm_line == norm_cap:
        return True
    if norm_line.startswith(norm_cap):
        return True
    fig = re.match(r"figure\s+(\d+)", norm_cap)
    if fig and norm_line.startswith(f"figure {fig.group(1)}"):
        return True
    return False

def _figure_caption_y(page: fitz.Page, art: Any | None) -> float | None:
    """Find figure caption y by matching registry/display title in page text."""
    if not art:
        return None

    candidates: list[str] = []
    if art.display_name:
        candidates.append(art.display_name)
    registry = {f["id"]: f["title"] for f in load_figures_registry()}
    reg_title = registry.get(art.id)
    if reg_title and reg_title not in candidates:
        candidates.append(reg_title)

    for cand in candidates:
        m = re.match(r"(Figure\s+\d+)", cand, re.I)
        if m and m.group(1) not in candidates:
            candidates.append(m.group(1))

    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            text = _span_text(line.get("spans", [])).strip()
            if not text:
                continue
            if any(_caption_line_matches(text, cand) for cand in candidates):
                return line["bbox"][1]
    return None

def _section_header_y_below(page: fitz.Page, caption_y: float) -> float | None:
    headers = section_headers_with_y(page)
    below = [y for _, y in headers if y > caption_y + 1]
    return min(below) if below else None

def _figure_mixed_order(
    page_num: int,
    page: fitz.Page,
    art: Any,
) -> list[dict[str, Any]] | None:
    """Split figure pages with intro prose, diagram, and body prose zones."""
    caption_y = _figure_caption_y(page, art)
    if caption_y is None:
        return None

    section_y = _section_header_y_below(page, caption_y)
    if section_y is None:
        return None

    page_h = page.rect.height
    page_w = page.rect.width
    footer_y = page_h - 28

    intro_bbox = [0.0, 0.0, page_w, caption_y - 4]
    figure_bbox = [0.0, caption_y, page_w, section_y - 4]
    body_bbox = [0.0, section_y - 4, page_w, footer_y]

    body_headers = [text for text, y in section_headers_with_y(page) if y >= section_y - 4]

    elements: list[dict[str, Any]] = []
    seq = 0

    intro_chars = expected_chars(page, intro_bbox)
    if intro_chars > 0:
        elements.append(
            {
                "seq": seq,
                "type": "prose",
                "role": "intro",
                "y0": 0.0,
                "y1": caption_y - 4,
                "bbox": intro_bbox,
                "extractor": "prose_zone",
                "expected_chars": intro_chars,
            }
        )
        seq += 1

    elements.append(
        {
            "seq": seq,
            "type": "figure",
            "artifact_id": art.id,
            "display_title": art.display_name,
            "y0": caption_y,
            "y1": section_y - 4,
            "bbox": figure_bbox,
            "extractor": "figure_ref",
        }
    )
    seq += 1

    body_el: dict[str, Any] = {
        "seq": seq,
        "type": "prose",
        "role": "body",
        "y0": section_y - 4,
        "y1": footer_y,
        "bbox": body_bbox,
        "extractor": "prose_zone",
        "expected_chars": expected_chars(page, body_bbox),
    }
    if body_headers:
        body_el["section_headers"] = body_headers
    elements.append(body_el)
    seq += 1

    elements.append({"seq": seq, "type": "footer", "extractor": "page_footer"})
    return elements

def _is_top_left_callout(
    bbox: tuple[float, float, float, float], page: fitz.Page
) -> bool:
    """log 04 placement: top-left feature box → first in reading order.

    Heuristic: upper third of page and predominantly left half (not a right sidebar).
    """
    page_w = float(page.rect.width)
    page_h = float(page.rect.height)
    x0, y0, x1, y1 = bbox
    mid_x = (x0 + x1) / 2.0
    # Top band + center of box on left half + not full-width
    return (
        y0 < page_h * 0.38
        and mid_x < page_w * 0.48
        and (x1 - x0) < page_w * 0.62
    )

def _is_top_fullwidth_callout(
    bbox: tuple[float, float, float, float], page: fitz.Page
) -> bool:
    """log 07 p.43: full-width box already at top → stay first; do not force end_body/inline."""
    page_w = float(page.rect.width)
    page_h = float(page.rect.height)
    x0, y0, x1, y1 = bbox
    return y0 < page_h * 0.42 and (x1 - x0) >= page_w * 0.55

def _callout_element(
    page_num: int,
    idx: int,
    bbox: tuple[float, float, float, float],
    seq: int,
) -> dict[str, Any]:
    return {
        "seq": seq,
        "type": "artifact",
        "artifact_type": "callout",
        "artifact_id": f"callout_p{page_num:03d}_{idx}",
        "display_title": None,
        "y0": bbox[1],
        "y1": bbox[3],
        "bbox": list(bbox),
        "extractor": "callout_bbox",
        "table_index": idx,
        "placement": "end_body",
    }

def _callout_mixed_order(
    page_num: int,
    page: fitz.Page,
    pdf_path,
    blue_boxes: list[tuple[float, float, float, float]],
    include_tables: bool = False,
) -> list[dict[str, Any]] | None:
    """Build RO with exclusive callout regions + log 04/07 placement policy.

    Placement:
    - top-left (partial width) → **first**
    - top full-width → **first** (log 07 p.43 — stay top, not end_body)
    - mid-page full-width neighbors (no side-column prose) → **inline by y**
      (log 07 p.41 — not forced to bottom)
    - else (multi-col / sidebar layout) → **end of body**, before footnotes

    Tables still interleave with prose by y/LTR. Callout text is exclusive via
    obstacle bboxes in prose_segments.
    """
    tboxes = table_bboxes(pdf_path, page_num - 1) if include_tables else []

    # Obstacles for prose exclusive zones: all callouts + tables
    obstacle_bboxes = list(tboxes) + list(blue_boxes)
    prose_segs = prose_segments(page, obstacle_bboxes)
    seen_side: set[tuple] = set()
    deduped: list[dict[str, Any]] = []
    for seg in prose_segs:
        key = (seg["role"], tuple(round(x, 1) for x in seg["bbox"]))
        if key in seen_side:
            continue
        seen_side.add(key)
        deduped.append(seg)
    prose_segs = deduped
    has_side = any(s.get("role") == "side" for s in prose_segs)
    page_w = float(page.rect.width)

    # Classify callouts for placement
    top_first: list[tuple[int, tuple[float, float, float, float], str]] = []
    inline_mid: list[tuple[int, tuple[float, float, float, float]]] = []
    end_body: list[tuple[int, tuple[float, float, float, float]]] = []
    for i, bb in enumerate(blue_boxes):
        x0, y0, x1, y1 = bb
        width = x1 - x0
        if _is_top_left_callout(bb, page):
            top_first.append((i, bb, "top_left"))
        elif _is_top_fullwidth_callout(bb, page):
            top_first.append((i, bb, "top_fullwidth"))
        elif (
            not has_side
            and width >= page_w * 0.50
            and not _is_top_fullwidth_callout(bb, page)
        ):
            # Full-width-ish mid-page, full-width prose neighbors → inline by y
            inline_mid.append((i, bb))
        else:
            end_body.append((i, bb))
    top_first.sort(key=lambda t: (t[1][1], t[1][0]))
    inline_mid.sort(key=lambda t: (t[1][1], t[1][0]))
    end_body.sort(key=lambda t: (t[1][1], t[1][0]))

    headers = section_headers_from_page(page)
    elements: list[dict[str, Any]] = []
    seq = 0

    def _append_prose(seg: dict[str, Any]) -> None:
        nonlocal seq
        el: dict[str, Any] = {
            "seq": seq,
            "type": "prose",
            "role": seg["role"],
            "y0": seg["y0"],
            "y1": seg["y1"],
            "bbox": seg["bbox"],
            "extractor": "prose_zone",
            "expected_chars": expected_chars(page, seg["bbox"]),
        }
        if seg["role"] == "intro" and headers:
            el["section_headers"] = headers
        elements.append(el)
        seq += 1

    def _append_callout(
        idx: int, bbox: tuple[float, float, float, float], placement: str
    ) -> None:
        nonlocal seq
        el = _callout_element(page_num, idx, bbox, seq)
        el["placement"] = placement
        elements.append(el)
        seq += 1

    def _append_table(idx: int, bbox: tuple[float, float, float, float]) -> None:
        nonlocal seq
        orientation, rotation = page_rotation(page)
        art_el = _artifact_element(
            page_num,
            bbox,
            orientation,
            rotation,
            None,
            None,
            table_index=idx,
            pdf_path=pdf_path,
            attach_span=False,
        )
        art_el["seq"] = seq
        art_el["table_index"] = idx
        elements.append(art_el)
        seq += 1

    # 1) Top-left / top-fullwidth callouts first (log 04 + log 07 p.43)
    for idx, bb, place in top_first:
        _append_callout(idx, bb, place)

    # 2) Body: tables + prose + inline callouts interleaved by y
    body_items: list[tuple[float, float, str, Any]] = []
    for seg in prose_segs:
        body_items.append((seg["y0"], seg["bbox"][0], "prose", seg))
    for i, tb in enumerate(tboxes):
        body_items.append((tb[1], tb[0], "table", (i, tb)))
    for idx, bb in inline_mid:
        body_items.append((bb[1], bb[0], "callout", (idx, bb)))
    body_items.sort(key=lambda t: (t[0], t[1]))

    for _y, _x, kind, payload in body_items:
        if kind == "prose":
            _append_prose(payload)
        elif kind == "table":
            _append_table(payload[0], payload[1])
        else:
            _append_callout(payload[0], payload[1], "inline")

    # 3) Sidebar/multi-col residual callouts at end of body, before footnotes
    for idx, bb in end_body:
        _append_callout(idx, bb, "end_body")

    foot_el = _footnote_zone_element(seq, page)
    if foot_el:
        elements.append(foot_el)
        seq += 1
    footer: dict[str, Any] = {"seq": seq, "type": "footer", "extractor": "page_footer"}
    if foot_el:
        footer["skip_footnotes"] = True
    elements.append(footer)
    return elements if any(e.get("artifact_type") == "callout" for e in elements) else None

def _multi_figure_reading_order(
    page_num: int,
    page: fitz.Page,
    reg_figs: list[dict],
) -> list[dict[str, Any]] | None:
    """Emit auditable multi-element RO for registry figure pages (CONTRACTS §2/§4).

    Prefer explicit ``figure`` elements for every registry figure. When caption Y
    positions are available, interleave intro/body prose zones; otherwise emit a
    single ``figure_page`` so extract can compose without dropping prose.
    """
    if not reg_figs:
        return None
    # Always record multi-fig as figure_page sugar with primary id = first by num,
    # plus explicit figure siblings for inventory audit. Extract figure_page path
    # uses figures_for_page; explicit figure elements alone would re-order poorly
    # without reliable caption Y for all. For multi-fig, use figure_page compose
    # but store all figure ids on the element for validation.
    figs_sorted = sorted(reg_figs, key=lambda f: (f.get("num") or 0))
    primary = figs_sorted[0]
    return [
        {
            "seq": 0,
            "type": "figure_page",
            "extractor": "rich_page",
            "artifact_id": primary["id"],
            "figure_ids": [f["id"] for f in figs_sorted],
            "figures": [
                {"id": f["id"], "title": f.get("title"), "num": f.get("num")}
                for f in figs_sorted
            ],
        },
        {"seq": 1, "type": "footer", "extractor": "page_footer"},
    ]

def _footnote_zone_element(seq: int, page: fitz.Page) -> dict[str, Any] | None:
    zones = classify_page_zones(page)
    footnotes = zones.get("footnotes") or []
    if not footnotes:
        return None
    return {
        "seq": seq,
        "type": "footnote_zone",
        "extractor": "footnote_zone",
        "expected_chars": sum(len(f) for f in footnotes),
    }

def _span_continuation_order(
    page_num: int,
    page: fitz.Page,
    pdf_path,
    span_info: dict,
) -> list[dict[str, Any]]:
    """Span continuation pages: skip table re-emit, still schedule trailing prose and footnotes."""
    elements: list[dict[str, Any]] = []
    seq = 0

    elements.append(
        {
            "seq": seq,
            "type": "span_continuation_skip",
            "span": _span_dict(span_info),
        }
    )
    seq += 1

    bboxes = table_bboxes(pdf_path, page_num - 1)
    prose_segs = prose_segments(page, bboxes)
    trailing = next((s for s in prose_segs if s["role"] == "trailing"), None)
    if trailing:
        elements.append(
            {
                "seq": seq,
                "type": "prose",
                "role": "trailing",
                "y0": trailing["y0"],
                "y1": trailing["y1"],
                "bbox": trailing["bbox"],
                "extractor": "prose_zone",
                "expected_chars": expected_chars(page, trailing["bbox"]),
            }
        )
        seq += 1

    foot_el = _footnote_zone_element(seq, page)
    if foot_el:
        elements.append(foot_el)
        seq += 1

    footer: dict[str, Any] = {
        "seq": seq,
        "type": "footer",
        "extractor": "page_footer",
    }
    if foot_el:
        footer["skip_footnotes"] = True
    elements.append(footer)
    return elements

def build_reading_order(
    page_num: int,
    page: fitz.Page,
    pdf_path: Path | None = None,
    span_info: dict | None = None,
    art: Any | None = None,
    content_type: str = "mixed",
) -> list[dict[str, Any]]:
    """Return ordered extractable elements for one PDF page."""
    # Resolve at call time — never freeze cfg.PDF_PATH in the default arg.
    if pdf_path is None:
        pdf_path = cfg.PDF_PATH
    if page_num in cfg.TOC_PAGE_RANGE:
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
        block = next((b for b in cfg.SECTION_BLOCKS if b["id"] == span_info["group_id"]), None)
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

    # Registry figures take precedence over single art id (multi-fig pages).
    reg_figs = [f for f in load_figures_registry() if f.get("page") == page_num]
    if reg_figs:
        multi = _multi_figure_reading_order(page_num, page, reg_figs)
        if multi:
            return multi
        # Fallback: single figure_page sugar (extract expands via figures_for_page).
        primary = sorted(reg_figs, key=lambda f: f.get("num") or 0)[0]
        aid = (art.id if art and art.artifact_type == "figure" else None) or primary["id"]
        return [
            {"seq": 0, "type": "figure_page", "extractor": "rich_page", "artifact_id": aid},
            {"seq": 1, "type": "footer", "extractor": "page_footer"},
        ]

    if art and art.artifact_type == "figure":
        mixed = _figure_mixed_order(page_num, page, art)
        if mixed:
            return mixed
        return [
            {"seq": 0, "type": "figure_page", "extractor": "rich_page", "artifact_id": art.id},
            {"seq": 1, "type": "footer", "extractor": "page_footer"},
        ]

    # Blue feature boxes (often not pdfplumber tables) — same layout class as
    # partial-width tables (p.30–31 ≡ p.35). CONTRACTS §2 / UV-07.
    # Only take this path for pure_text / when tables do not already model the box
    # (avoids double emit: pdfplumber table + callout_bbox for the same rect).
    # Gated by extraction.features.callouts (Companion profile / job.json).
    from pipeline.config import feature_enabled

    blue_boxes: list[tuple[float, float, float, float]] = []
    if feature_enabled("callouts"):
        from pipeline.callout_detect import detect_blue_callout_bboxes

        blue_boxes = detect_blue_callout_bboxes(page)
    if blue_boxes and content_type in ("pure_text", "mixed", "single_table"):
        tboxes = table_bboxes(pdf_path, page_num - 1) if content_type != "pure_text" else []
        # Drop blues that heavily overlap an existing table (table path owns them).
        def _overlap_frac(a, b) -> float:
            ax0, ay0, ax1, ay1 = a
            bx0, by0, bx1, by1 = b
            ix0, iy0 = max(ax0, bx0), max(ay0, by0)
            ix1, iy1 = min(ax1, bx1), min(ay1, by1)
            if ix1 <= ix0 or iy1 <= iy0:
                return 0.0
            inter = (ix1 - ix0) * (iy1 - iy0)
            area = max(1.0, (ax1 - ax0) * (ay1 - ay0))
            return inter / area

        if content_type == "pure_text":
            # pdfplumber may still "see" a table; prefer drawing geometry for pure_text
            # pages so RO is stable (p.30–31).
            mixed_callouts = _callout_mixed_order(
                page_num, page, pdf_path, blue_boxes, include_tables=False
            )
            if mixed_callouts:
                return mixed_callouts
        else:
            orphan_blues = [
                bb
                for bb in blue_boxes
                if not any(_overlap_frac(bb, tb) > 0.4 for tb in tboxes)
            ]
            if orphan_blues:
                mixed_callouts = _callout_mixed_order(
                    page_num, page, pdf_path, orphan_blues, include_tables=True
                )
                if mixed_callouts:
                    return mixed_callouts

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
        return _span_continuation_order(page_num, page, pdf_path, span_info)

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

        # Prefer prose before table when: above it, or side-column to the left (LTR).
        prose_first = False
        if next_prose and not next_table:
            prose_first = True
        elif next_prose and next_table:
            if next_prose["y0"] < next_table[1] - 3:
                prose_first = True
            elif (
                next_prose.get("role") == "side"
                and next_prose["y0"] < next_table[3]
                and next_prose["bbox"][0] < next_table[0]
            ):
                prose_first = True

        if prose_first and next_prose:
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
        if seg["role"] in ("interstitial", "trailing", "side"):
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

    # Footnote 46 etc.: geometry surgical path on rotated start pages — not Grok vision.
    if span_start and orientation.startswith("rotated") and bboxes:
        elements.append(
            {
                "seq": seq,
                "type": "footnote_zone",
                "extractor": "rotated_footnote_zone",
                "table_bbox": list(bboxes[0]),
            }
        )
        seq += 1

    footer: dict[str, Any] = {"seq": seq, "type": "footer", "extractor": "page_footer"}
    if span_start and orientation.startswith("rotated"):
        footer["skip_footnotes"] = True
    elements.append(footer)
    return elements