"""Build per-chunk page inventories."""

from __future__ import annotations

import json
from pathlib import Path

import fitz

from pipeline.config import (
    KNOWN_TABLES_FIGURES,
    MULTIPAGE_ARTIFACTS,
    PDF_PATH,
    INVENTORIES_DIR,
    METADATA_DIR,
    SECTION_BLOCKS,
    TOC_PAGE_RANGE,
    load_figures_registry,
)
from pipeline.id_registry import build_registry, registry_by_page
from pipeline.descriptor_layout import section_headers_from_page
from pipeline.page_elements import build_reading_order
from pipeline.span_detector import detect_spans
from pipeline.title_fix import clean_artifact_id, fix_rotated_title


def _page_drawings_count(page: fitz.Page) -> tuple[int, int, int]:
    drawings = page.get_drawings()
    h = sum(
        1
        for d in drawings
        if abs(d["rect"].width) > abs(d["rect"].height) * 3 and d["rect"].width > 50
    )
    v = sum(
        1
        for d in drawings
        if abs(d["rect"].height) > abs(d["rect"].width) * 3 and d["rect"].height > 50
    )
    return len(drawings), h, v


def _is_rotated(page: fitz.Page) -> bool:
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            d = line.get("dir", (1, 0))
            if abs(d[1]) > 0.3:
                return True
    return False


def _rotation_label(page: fitz.Page) -> str:
    if not _is_rotated(page):
        return "normal"
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            d = line.get("dir", (1, 0))
            if abs(d[1]) > 0.3:
                return "rotated_270" if d[1] > 0 else "rotated_90"
    return "rotated_90"


def classify_page(page_num: int, page: fitz.Page, spans_by_page: dict) -> dict:
    text = page.get_text("text").strip()
    drawings, hlines, vlines = _page_drawings_count(page)
    rotated = _is_rotated(page)
    span = spans_by_page.get(page_num)

    if page_num in TOC_PAGE_RANGE:
        content_type = "toc"
    elif len(text) < 50 and drawings < 5:
        content_type = "blank"
    elif span and span["span_type"] == "section_block":
        content_type = "section_block"
    elif (
        span
        and span["span_type"] == "continuation"
        and page_num > span["start_page"]
    ):
        content_type = "multi_page_table"
    elif span and span["span_type"] == "series":
        content_type = "mixed" if len(text) > 400 else "single_table"
    elif hlines > 10 and vlines > 5:
        if len(text) > 800:
            content_type = "mixed"
        else:
            content_type = "single_table" if not span else "multi_page_table"
    elif hlines > 5 or vlines > 5:
        content_type = "mixed"
    else:
        content_type = "pure_text"

    spanning_info = None
    if span:
        role = "start" if page_num == span["start_page"] else (
            "end" if page_num == span["end_page"] else "middle"
        )
        # Root L07-ID: never persist garbled reversed tokens in group_id
        clean_gid = clean_artifact_id(span.get("group_id"), span.get("title"))
        spanning_info = {
            "group_id": clean_gid,
            "span_type": span["span_type"],
            "role": role,
            "start_page": span["start_page"],
            "end_page": span["end_page"],
        }

    headers = section_headers_from_page(page)
    has_table = hlines > 5 and vlines > 5
    skip_validation = False
    if span and page_num > span.get("start_page", page_num):
        if span.get("span_type") in ("continuation", "series", "section_block"):
            skip_validation = True
    if content_type in ("pure_text",) and page_num == 1:
        min_chars = 50
    elif content_type in ("mixed", "pure_text"):
        min_chars = max(80, int(len(text) * 0.12))
    elif has_table and len(text) > 500:
        min_chars = max(80, int(len(text) * 0.08))
    else:
        min_chars = 80

    return {
        "page_number": page_num,
        "content_type": content_type,
        "table_orientation": _rotation_label(page),
        "spanning_info": spanning_info,
        "figures": [],
        "prose_blocks": content_type in ("pure_text", "mixed", "figure")
        or bool(headers),
        "text_length": len(text),
        "min_output_chars": min_chars,
        "section_headers": headers,
        "expects_table": has_table and content_type != "pure_text",
        "skip_validation": skip_validation,
        "drawings": drawings,
    }


def build_inventories() -> list[dict]:
    spans = detect_spans()
    spans_by_page: dict[int, dict] = {}
    for s in spans:
        d = s.__dict__
        span_len = s.end_page - s.start_page
        for p in range(s.start_page, s.end_page + 1):
            existing = spans_by_page.get(p)
            if existing is None or span_len > existing["end_page"] - existing["start_page"]:
                spans_by_page[p] = d

    artifacts = build_registry(spans)
    art_by_page = registry_by_page(artifacts)

    chunks_path = METADATA_DIR / "chunks.json"
    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    INVENTORIES_DIR.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(PDF_PATH)
    all_inventories = []

    for chunk in chunks:
        pages = []
        for page_num in range(chunk["start_page"], chunk["end_page"] + 1):
            page = doc[page_num - 1]
            entry = classify_page(page_num, page, spans_by_page)
            art = art_by_page.get(page_num)
            if art:
                section_title = fix_rotated_title(art.display_name)
                entry["artifact_id"] = clean_artifact_id(art.id, section_title)
                entry["section_title"] = section_title
                entry["product_tier"] = art.product_tiers
                if art.artifact_type == "figure":
                    entry["expects_table"] = False
            # Continuation spans: ensure clean group_id is also page artifact_id
            # when registry missed the scale (rotated multi-page titles).
            si = entry.get("spanning_info") or {}
            if si.get("group_id") and not entry.get("artifact_id"):
                entry["artifact_id"] = clean_artifact_id(si["group_id"])
                if not entry.get("section_title"):
                    # Prefer human title from reading_order later; seed from id
                    entry["section_title"] = (
                        si["group_id"].removeprefix("scale_").replace("_", " ")
                    )
            # CONTRACTS §2: always record registry figures for this page
            from pipeline.extractors.figures import figures_for_page

            page_figs = figures_for_page(page_num)
            entry["figures"] = [
                {"id": f["id"], "title": f.get("title"), "num": f.get("num"), "render_as": f.get("render_as")}
                for f in page_figs
            ]
            # Prefer figure primary id when multi-fig (first by num), not last-wins alone
            if page_figs:
                primary = sorted(page_figs, key=lambda f: f.get("num") or 0)[0]
                entry["artifact_id"] = primary["id"]
                entry["section_title"] = primary.get("title") or primary["id"]
                entry["expects_table"] = False
            entry["reading_order"] = build_reading_order(
                page_num,
                page,
                PDF_PATH,
                entry.get("spanning_info"),
                art,
                entry["content_type"],
            )
            pages.append(entry)

        required = []
        for p in pages:
            if p.get("artifact_id"):
                required.append(
                    {
                        "id": p["artifact_id"],
                        "page": p["page_number"],
                        "type": "artifact",
                    }
                )
        inv = {
            "chunk_id": chunk["chunk_id"],
            "start_page": chunk["start_page"],
            "end_page": chunk["end_page"],
            "expected_page_markers": list(
                range(chunk["start_page"], chunk["end_page"] + 1)
            ),
            "required_artifacts": required,
            "expected_tables": list(KNOWN_TABLES_FIGURES.values()),
            "expected_multipage": list(MULTIPAGE_ARTIFACTS.keys()),
            "pages": pages,
        }
        out = INVENTORIES_DIR / f"{chunk['chunk_id']}_inventory.json"
        out.write_text(json.dumps(inv, indent=2), encoding="utf-8")
        all_inventories.append(inv)
        print(f"Wrote {out.name}")

    doc.close()
    return all_inventories


if __name__ == "__main__":
    build_inventories()