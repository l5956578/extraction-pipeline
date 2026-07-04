"""Extract markdown per chunk based on inventory reading_order."""

from __future__ import annotations

import json
import re
from pathlib import Path

import fitz

from pipeline.config import (
    KNOWN_TABLES_FIGURES,
    MULTIPAGE_ARTIFACTS,
    PDF_PATH,
    RAW_DIR,
    INVENTORIES_DIR,
)
from pipeline.descriptor_layout import extract_prose_zone
from pipeline.extractors.multipage import (
    merge_pdfplumber_tables,
    merge_rotated_pages,
    merge_section_block,
    merge_tables_by_title,
)
from pipeline.extractors.rich_text import extract_rich_page
from pipeline.extractors.rotated import extract_rotated_element, extract_rotated_tables
from pipeline.extractors.table import extract_tables
from pipeline.id_registry import ArtifactMeta, build_registry, registry_by_page
from pipeline.page_layout import classify_page_zones, format_page_footer
from pipeline.toc_layout import extract_toc_page
from pipeline.span_detector import detect_spans
from pipeline.figures_catalog import FIGURE_CONTENT, figure_block
from pipeline.utils import artifact_header, slugify, table_to_markdown
from pipeline.title_fix import fix_rotated_title


class _ExtractContext:
    def __init__(self, art_by_id: dict, art_by_title: dict):
        self.art_by_id = art_by_id
        self.art_by_title = art_by_title
        self.emitted_spans: set[str] = set()


def _emit_artifact(art: ArtifactMeta, page_start: int, page_end: int, body: str) -> str:
    pages = f"{page_start}-{page_end}" if page_end > page_start else str(page_start)
    display = fix_rotated_title(art.display_name)
    header = artifact_header(
        art.id,
        display,
        art.artifact_type,
        art.product_tiers,
        pages,
    )
    return f"{header}\n{body}\n"


def _emit_artifact_from_element(el: dict, body: str, ctx: _ExtractContext) -> str:
    aid = el.get("artifact_id") or "unknown"
    art = ctx.art_by_id.get(aid)
    display = fix_rotated_title(el.get("display_title") or (art.display_name if art else aid))
    span = el.get("span") or {}
    pages_list = span.get("pages") or []
    if pages_list:
        p_start, p_end = pages_list[0], pages_list[-1]
        pages = f"{p_start}-{p_end}" if p_end > p_start else str(p_start)
    elif art:
        p_start, p_end = art.page_start, art.page_end
        pages = f"{p_start}-{p_end}" if p_end > p_start else str(p_start)
    else:
        pages = "?"
    tiers = art.product_tiers if art else ["context"]
    atype = el.get("artifact_type") or (art.artifact_type if art else "descriptor_scale")
    header = artifact_header(aid, display, atype, tiers, pages)
    return f"{header}\n{body}\n"


def _emit_page_footer(page: fitz.Page, page_num: int, skip_footnotes: bool = False) -> str:
    zones = classify_page_zones(page)
    if skip_footnotes:
        zones = {**zones, "footnotes": []}
    return format_page_footer(page_num, zones)


def _emit_footnote_zone(page: fitz.Page) -> str | None:
    zones = classify_page_zones(page)
    footnotes = zones.get("footnotes") or []
    if not footnotes:
        return None
    return "\n\n".join(footnotes) + "\n"


def _table_title(table: list[list]) -> str | None:
    if not table or not table[0]:
        return None
    for cell in table[0]:
        if cell and str(cell).strip():
            return re.sub(r"\s+", " ", str(cell).strip())
    return None


def _artifact_for_table_title(
    title: str | None, ctx: _ExtractContext, primary_art: ArtifactMeta | None
) -> ArtifactMeta | None:
    if not title:
        return primary_art
    aid = slugify(title, prefix="scale")
    if aid in ctx.art_by_id:
        return ctx.art_by_id[aid]
    by_name = ctx.art_by_title.get(title.strip().lower())
    if by_name:
        return by_name
    if primary_art and primary_art.display_name.strip().lower() == title.strip().lower():
        return primary_art
    return None


def _merge_multipage_body(gid: str, page_nums: list[int], art: ArtifactMeta | None, pdf_path) -> str:
    if gid in MULTIPAGE_ARTIFACTS:
        cfg = MULTIPAGE_ARTIFACTS[gid]
        indices = list(range(cfg["page_start"] - 1, cfg["page_end"]))
        return merge_pdfplumber_tables(indices, pdf_path)
    title_key = art.display_name if art else gid.replace("scale_", "").replace("_", " ")
    indices = [p - 1 for p in page_nums]
    body = merge_tables_by_title(indices, pdf_path, title_key)
    if not body.strip():
        body = merge_pdfplumber_tables(indices, pdf_path)
    return body


def _extract_span_body(
    el: dict,
    doc: fitz.Document,
    ctx: _ExtractContext,
) -> str:
    span = el["span"]
    page_nums = span["pages"]
    gid = span["group_id"]
    art = ctx.art_by_id.get(gid) or ctx.art_by_id.get(el.get("artifact_id", ""))

    if el.get("extractor") == "section_block_merge":
        return merge_section_block(doc, page_nums, PDF_PATH)

    if el.get("text_direction") == "ocr" or el.get("extractor") == "rotated_table":
        return merge_rotated_pages(doc, page_nums, PDF_PATH, rotation=el.get("rotation", 90))

    return _merge_multipage_body(gid, page_nums, art, PDF_PATH)


def _extract_single_table(
    page: fitz.Page,
    page_num: int,
    el: dict,
    art: ArtifactMeta | None,
    ctx: _ExtractContext,
) -> str:
    if el.get("extractor") == "rotated_table" or el.get("text_direction") == "ocr":
        return extract_rotated_element(page_num - 1, page, PDF_PATH, el)

    tables = extract_tables(page_num - 1, PDF_PATH)
    if not tables:
        return ""

    table_index = el.get("table_index", 0)
    if table_index >= len(tables):
        return ""
    table = tables[table_index]
    md = table_to_markdown(table)
    if not md.strip():
        return ""

    title = _table_title(table)
    if page_num in KNOWN_TABLES_FIGURES and table_index == 0:
        known_id = KNOWN_TABLES_FIGURES[page_num][0]
        table_art = ctx.art_by_id.get(known_id) or art
    elif table_index == 0 and art and page_num == art.page_start:
        table_art = art
    else:
        table_art = _artifact_for_table_title(
            title, ctx, art if table_index == 0 else None
        )
    if table_art:
        return _emit_artifact(
            table_art, table_art.page_start, table_art.page_end, md
        )
    return md


def _extract_element(
    el: dict,
    page: fitz.Page,
    page_num: int,
    page_info: dict,
    art: ArtifactMeta | None,
    doc: fitz.Document,
    ctx: _ExtractContext,
) -> str | None:
    etype = el["type"]

    if etype == "toc":
        return extract_toc_page(page, page_num) + "\n"

    if etype == "span_continuation_skip":
        return None

    if etype == "footnote_zone":
        block = _emit_footnote_zone(page)
        return (block + "\n") if block else None

    if etype == "footer":
        return _emit_page_footer(
            page, page_num, skip_footnotes=el.get("skip_footnotes", False)
        ) + "\n"

    if etype == "figure_page":
        return extract_rich_page(page, page_num) + "\n"

    if etype == "figure":
        aid = el.get("artifact_id") or ""
        if aid in FIGURE_CONTENT:
            return figure_block(aid) + "\n"
        art = ctx.art_by_id.get(aid)
        display = fix_rotated_title(
            el.get("display_title") or (art.display_name if art else aid or "Figure")
        )
        tiers = art.product_tiers if art else ["context"]
        atype = art.artifact_type if art else "figure"
        header = artifact_header(aid or "unknown", display, atype, tiers, str(page_num))
        return f"{header}\n"

    if etype == "prose":
        if el.get("extractor") == "rich_page":
            return extract_rich_page(page, page_num) + "\n"
        scale_title = fix_rotated_title(art.display_name) if art else None
        bbox = el.get("bbox")
        if not bbox:
            return None
        text = extract_prose_zone(page, bbox, scale_title=scale_title)
        if text and scale_title:
            text = re.sub(
                rf"\n###\s*{re.escape(scale_title)}\s*$",
                "",
                text,
                flags=re.I,
            ).strip()
            if re.fullmatch(rf"###\s*{re.escape(scale_title)}\s*", text, flags=re.I):
                text = ""
        return (text + "\n") if text else None

    if etype == "artifact":
        span = el.get("span")
        if span:
            gid = span["group_id"]
            if gid in ctx.emitted_spans:
                return None
            ctx.emitted_spans.add(gid)
            body = _extract_span_body(el, doc, ctx)
            art_emit = ctx.art_by_id.get(gid) or art
            if art_emit:
                return _emit_artifact(
                    art_emit, span["pages"][0], span["pages"][-1], body
                )
            return _emit_artifact_from_element(el, body, ctx)

        body = _extract_single_table(page, page_num, el, art, ctx)
        return (body + "\n") if body else None

    return None


def extract_chunk(chunk_id: str) -> str:
    inv_path = INVENTORIES_DIR / f"{chunk_id}_inventory.json"
    inventory = json.loads(inv_path.read_text(encoding="utf-8"))
    _, artifacts = _get_spans_and_artifacts()
    art_by_id = {a.id: a for a in artifacts}
    art_by_page = registry_by_page(artifacts)
    art_by_title = {a.display_name.strip().lower(): a for a in artifacts}
    ctx = _ExtractContext(art_by_id, art_by_title)

    doc = fitz.open(PDF_PATH)
    parts: list[str] = []
    parts.append(f"# {chunk_id} (pages {inventory['start_page']}-{inventory['end_page']})\n")

    for page_info in inventory["pages"]:
        page_num = page_info["page_number"]
        page = doc[page_num - 1]
        art = art_by_page.get(page_num)
        reading_order = page_info.get("reading_order") or []

        for el in reading_order:
            block = _extract_element(el, page, page_num, page_info, art, doc, ctx)
            if block:
                parts.append(block)

    doc.close()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = RAW_DIR / f"{chunk_id}.md"
    content = "\n".join(parts)
    out.write_text(content, encoding="utf-8")
    print(f"Extracted {out.name} ({len(content)} chars)")
    return str(out)


_CACHED_SPANS = None
_CACHED_ARTIFACTS = None


def _get_spans_and_artifacts():
    global _CACHED_SPANS, _CACHED_ARTIFACTS
    if _CACHED_SPANS is None:
        _CACHED_SPANS = detect_spans()
        _CACHED_ARTIFACTS = build_registry(_CACHED_SPANS)
    return _CACHED_SPANS, _CACHED_ARTIFACTS


def extract_all_chunks(skip_existing: bool = False) -> list[str]:
    outputs = []
    for inv in sorted(INVENTORIES_DIR.glob("chunk_*_inventory.json")):
        chunk_id = inv.stem.replace("_inventory", "")
        out_path = RAW_DIR / f"{chunk_id}.md"
        if skip_existing and out_path.exists() and out_path.stat().st_size > 500:
            print(f"Skipping {chunk_id} (already extracted)")
            outputs.append(str(out_path))
            continue
        outputs.append(extract_chunk(chunk_id))
    return outputs


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract markdown for one or all chunks")
    parser.add_argument(
        "chunk_id",
        nargs="?",
        help="Chunk id to extract (e.g. chunk_01). Omit to extract all chunks.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Extract all chunks (default when chunk_id is omitted)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip chunks whose raw output already exists and is non-trivial",
    )
    args = parser.parse_args()

    if args.chunk_id:
        extract_chunk(args.chunk_id)
    else:
        extract_all_chunks(skip_existing=args.skip_existing)