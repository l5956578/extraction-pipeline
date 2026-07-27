"""Assign stable IDs and display names to artifacts."""

from __future__ import annotations

import re
from dataclasses import dataclass

import fitz
import pdfplumber

import pipeline.config as cfg
from pipeline.config import load_figures_registry
from pipeline.span_detector import SpanGroup, detect_spans
from pipeline.title_fix import artifact_id_from_title, clean_artifact_id, fix_rotated_title
from pipeline.utils import slugify

@dataclass
class ArtifactMeta:
    id: str
    display_name: str
    artifact_type: str
    product_tiers: list[str]
    page_start: int
    page_end: int
    group_id: str | None = None

def _parse_toc_entries() -> dict[int, tuple[str, str]]:
    """Parse list of tables/figures from page 9."""
    mapping: dict[int, tuple[str, str]] = {}
    doc = fitz.open(cfg.PDF_PATH)
    text = doc[8].get_text("text")
    doc.close()

    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"^(FIGURE|TABLE)\s+(\d+)\s+[–-]\s+(.+?)\s+(\d+)\s*$", line, re.I)
        if m:
            kind = "figure" if m.group(1).lower() == "figure" else "table"
            num = int(m.group(2))
            title = m.group(3).strip()
            page = int(m.group(4))
            prefix = "figure" if kind == "figure" else "table"
            aid = slugify(f"{prefix}_{num:02d}_{title}")
            mapping[page] = (aid, title, kind)
    return mapping

def _product_tiers_for_page(page: int) -> list[str]:
    if 177 <= page <= 181:
        return ["base"]
    if 173 <= page <= 190:
        return ["assessment_action", "context"]
    if 191 <= page <= 241:
        return ["detailed", "context"]
    if 47 <= page <= 170:
        return ["detessment_action", "detailed"] if False else ["assessment_action", "detailed"]
    if page <= 46:
        return ["context"]
    return ["context"]

def _normalize_title(title: str) -> str:
    """Fix reversed titles from rotated PDF text layers."""
    return fix_rotated_title(title)

def _scale_title_from_page(pdf: pdfplumber.PDF, page_idx: int) -> str | None:
    if page_idx < 0 or page_idx >= len(pdf.pages):
        return None
    tables = pdf.pages[page_idx].extract_tables() or []
    if not tables or not tables[0]:
        return None
    row0 = tables[0][0]
    for cell in row0:
        if cell and str(cell).strip():
            return _normalize_title(re.sub(r"\s+", " ", str(cell).strip()))
    return None

def build_registry(spans: list[SpanGroup] | None = None) -> list[ArtifactMeta]:
    spans = spans or detect_spans()
    toc = _parse_toc_entries()
    continuation_pages: dict[int, str] = {}
    for span in spans:
        if span.span_type in ("continuation", "section_block"):
            for p in range(span.start_page, span.end_page + 1):
                continuation_pages[p] = span.group_id

    artifacts: list[ArtifactMeta] = []
    seen_ids: set[str] = set()

    for fig in load_figures_registry():
        if fig["id"] not in seen_ids:
            artifacts.append(
                ArtifactMeta(
                    id=fig["id"],
                    display_name=fig["title"],
                    artifact_type="figure",
                    product_tiers=["context"],
                    page_start=fig["page"],
                    page_end=fig["page"],
                )
            )
            seen_ids.add(fig["id"])

    # Section blocks
    for block in cfg.SECTION_BLOCKS:
        meta = ArtifactMeta(
            id=block["id"],
            display_name=block["display_name"],
            artifact_type=block["type"],
            product_tiers=block["product_tiers"],
            page_start=block["page_start"],
            page_end=block["page_end"],
            group_id=block["id"],
        )
        artifacts.append(meta)
        seen_ids.add(meta.id)

    figure_pages = {fig["page"] for fig in load_figures_registry()}
    with pdfplumber.open(cfg.PDF_PATH) as pdf:
        page_count = len(pdf.pages)
        for page_num in range(1, page_count + 1):
            if page_num in continuation_pages:
                gid = continuation_pages[page_num]
                if any(a.id == gid for a in artifacts):
                    continue

            if page_num in cfg.KNOWN_TABLES_FIGURES:
                aid, title, atype = cfg.KNOWN_TABLES_FIGURES[page_num]
                if aid not in seen_ids:
                    artifacts.append(
                        ArtifactMeta(
                            id=aid,
                            display_name=title,
                            artifact_type=atype,
                            product_tiers=_product_tiers_for_page(page_num),
                            page_start=page_num,
                            page_end=page_num,
                        )
                    )
                    seen_ids.add(aid)
                continue

            if page_num in toc:
                aid, title, atype = toc[page_num]
                if aid not in seen_ids:
                    end_page = page_num
                    for span in spans:
                        if span.group_id == aid and span.span_type == "continuation":
                            end_page = span.end_page
                    artifacts.append(
                        ArtifactMeta(
                            id=aid,
                            display_name=title,
                            artifact_type=atype,
                            product_tiers=_product_tiers_for_page(page_num),
                            page_start=page_num,
                            page_end=end_page,
                            group_id=aid if end_page > page_num else None,
                        )
                    )
                    seen_ids.add(aid)
                continue

            if page_num in figure_pages:
                continue

            title = _scale_title_from_page(pdf, page_num - 1)
            if title and page_num not in continuation_pages:
                # Root: always slug from fix_rotated_title (L07-ID / R3)
                title = fix_rotated_title(title)
                aid = artifact_id_from_title(title, prefix="scale")
                if aid not in seen_ids:
                    end_page = page_num
                    for span in spans:
                        # Match either clean id or legacy garbled group_id after fix
                        span_gid = span.group_id or ""
                        if span_gid == aid or (
                            fix_rotated_title(span.title or "").strip().lower()
                            == title.strip().lower()
                        ):
                            end_page = max(end_page, span.end_page)
                    artifacts.append(
                        ArtifactMeta(
                            id=aid,
                            display_name=title,
                            artifact_type="descriptor_scale",
                            product_tiers=_product_tiers_for_page(page_num),
                            page_start=page_num,
                            page_end=end_page,
                            group_id=aid if end_page > page_num else None,
                        )
                    )
                    seen_ids.add(aid)

    explicit_artifacts = [
        ArtifactMeta(
            id="scale_vocabulary_control",
            display_name="Vocabulary control",
            artifact_type="descriptor_scale",
            product_tiers=["assessment_action", "detailed"],
            page_start=132,
            page_end=133,
            group_id="scale_vocabulary_control",
        ),
    ]
    for art in explicit_artifacts:
        if art.id not in seen_ids:
            artifacts.append(art)
            seen_ids.add(art.id)

    # Ensure continuation spans from span_detector become artifacts even when
    # pdfplumber title extraction fails on rotated pages (L07-ID root).
    for span in spans:
        if span.span_type != "continuation":
            continue
        title = fix_rotated_title(span.title or "")
        aid = clean_artifact_id(span.group_id, title) if span.group_id else (
            artifact_id_from_title(title, prefix="scale") if title else None
        )
        if not aid or aid in seen_ids:
            continue
        if not aid.startswith("scale_") and not aid.startswith("table_"):
            continue
        display = title or aid.removeprefix("scale_").replace("_", " ")
        artifacts.append(
            ArtifactMeta(
                id=aid,
                display_name=display,
                artifact_type="descriptor_scale" if aid.startswith("scale_") else "table",
                product_tiers=_product_tiers_for_page(span.start_page),
                page_start=span.start_page,
                page_end=span.end_page,
                group_id=aid,
            )
        )
        seen_ids.add(aid)

    artifacts.sort(key=lambda a: (a.page_start, a.id))
    return artifacts

def registry_by_page(artifacts: list[ArtifactMeta]) -> dict[int, ArtifactMeta]:
    by_page: dict[int, ArtifactMeta] = {}
    for art in artifacts:
        for p in range(art.page_start, art.page_end + 1):
            by_page[p] = art
    return by_page