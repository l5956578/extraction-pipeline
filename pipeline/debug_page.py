"""CLI for inspecting PDF page layout, zones, and inventory contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import fitz

from pipeline.config import INVENTORIES_DIR, PDF_PATH
from pipeline.id_registry import build_registry, registry_by_page
from pipeline.inventory import classify_page
from pipeline.page_elements import build_reading_order, prose_segments, table_bboxes
from pipeline.page_layout import _classify_line, _span_text, classify_page_zones
from pipeline.span_detector import detect_spans


def _parse_pages(raw: str) -> list[int]:
    pages: list[int] = []
    for part in raw.replace(" ", "").split(","):
        if not part:
            continue
        pages.append(int(part))
    return pages


def _load_inventory_page(page_num: int) -> dict[str, Any] | None:
    if not INVENTORIES_DIR.exists():
        return None
    for path in sorted(INVENTORIES_DIR.glob("*_inventory.json")):
        inv = json.loads(path.read_text(encoding="utf-8"))
        for page in inv.get("pages", []):
            if page.get("page_number") == page_num:
                return page
    return None


def _pdf_lines(page: fitz.Page) -> list[dict[str, Any]]:
    page_height = page.rect.height
    lines: list[dict[str, Any]] = []
    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            text = _span_text(line.get("spans", [])).strip()
            if not text:
                continue
            bbox = line["bbox"]
            y0 = bbox[1]
            lines.append(
                {
                    "y0": round(y0, 1),
                    "x0": round(bbox[0], 1),
                    "kind": _classify_line(text, y0, page_height),
                    "text": text[:120],
                }
            )
    lines.sort(key=lambda item: (item["y0"], item["x0"]))
    return lines


def _span_for_page(page_num: int) -> dict[str, Any] | None:
    spans = detect_spans()
    best: dict[str, Any] | None = None
    best_len = -1
    for span in spans:
        if span.start_page <= page_num <= span.end_page:
            span_len = span.end_page - span.start_page
            if span_len > best_len:
                best_len = span_len
                role = (
                    "start"
                    if page_num == span.start_page
                    else "end"
                    if page_num == span.end_page
                    else "middle"
                )
                best = {
                    "group_id": span.group_id,
                    "span_type": span.span_type,
                    "role": role,
                    "start_page": span.start_page,
                    "end_page": span.end_page,
                    "title": span.title,
                }
    return best


def _live_reading_order(page_num: int, page: fitz.Page) -> list[dict[str, Any]]:
    spans = detect_spans()
    spans_by_page: dict[int, dict] = {}
    for s in spans:
        d = s.__dict__
        span_len = s.end_page - s.start_page
        for p in range(s.start_page, s.end_page + 1):
            existing = spans_by_page.get(p)
            if existing is None or span_len > existing["end_page"] - existing["start_page"]:
                spans_by_page[p] = d

    span = spans_by_page.get(page_num)
    spanning_info = None
    if span:
        role = (
            "start"
            if page_num == span["start_page"]
            else "end"
            if page_num == span["end_page"]
            else "middle"
        )
        spanning_info = {
            "group_id": span["group_id"],
            "span_type": span["span_type"],
            "role": role,
            "start_page": span["start_page"],
            "end_page": span["end_page"],
        }

    entry = classify_page(page_num, page, spans_by_page)
    art = registry_by_page(build_registry(spans)).get(page_num)
    return build_reading_order(
        page_num,
        page,
        PDF_PATH,
        spanning_info,
        art,
        entry["content_type"],
    )


def _print_section(title: str, payload: Any) -> None:
    print(f"\n=== {title} ===")
    print(json.dumps(payload, indent=2))


def debug_page(page_num: int, show: set[str]) -> None:
    doc = fitz.open(PDF_PATH)
    page = doc[page_num - 1]

    print(f"\n{'#' * 72}")
    print(f"PAGE {page_num}")
    print(f"{'#' * 72}")

    if "lines" in show or "zones" in show:
        _print_section("PDF lines (y-positions)", _pdf_lines(page))

    if "zones" in show:
        _print_section("zones", classify_page_zones(page))

    if "footnotes" in show:
        zones = classify_page_zones(page)
        _print_section("footnotes", zones.get("footnotes", []))

    if "prose_segments" in show:
        bboxes = table_bboxes(PDF_PATH, page_num - 1)
        _print_section("prose_segments", prose_segments(page, bboxes))

    if "spanning_info" in show:
        _print_section("spanning_info", _span_for_page(page_num))

    if "reading_order" in show:
        inv_page = _load_inventory_page(page_num)
        if inv_page and inv_page.get("reading_order"):
            _print_section("reading_order (inventory)", inv_page["reading_order"])
        else:
            _print_section("reading_order (live)", _live_reading_order(page_num, page))

    doc.close()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Inspect PDF page layout and inventory.")
    parser.add_argument(
        "pages",
        help="Comma-separated page numbers, e.g. 25 or 25,146,147,148",
    )
    parser.add_argument(
        "--show",
        default="lines,zones,prose_segments,reading_order,spanning_info,footnotes",
        help="Comma-separated sections: lines,zones,prose_segments,reading_order,spanning_info,footnotes",
    )
    args = parser.parse_args(argv)

    show = {part.strip() for part in args.show.split(",") if part.strip()}
    for page_num in _parse_pages(args.pages):
        debug_page(page_num, show)


if __name__ == "__main__":
    main()