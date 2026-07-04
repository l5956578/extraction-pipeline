"""Merge multi-page tables and section blocks."""

from __future__ import annotations

import fitz
import pdfplumber

from pipeline.extractors.rotated import (
    _reverse_table_cells,
    _table_readable,
    derotated_pdfplumber_tables,
    extract_rotated_tables,
)
from pipeline.title_fix import fix_rotated_title
from pipeline.extractors.table import tables_to_markdown
from pipeline.utils import table_to_markdown


def _merge_rows(all_rows: list[list[list]]) -> list[list]:
    merged: list[list] = []
    header = None
    for table in all_rows:
        if not table:
            continue
        if header is None:
            header = table[0]
            merged.append(header)
            start_idx = 1
        else:
            start_idx = 1 if table[0] == header else 0
        for row in table[start_idx:]:
            if row and any(str(c).strip() for c in row):
                merged.append(row)
    return merged


def merge_tables_by_title(page_indices: list[int], pdf_path, title_match: str) -> str:
    """Merge only tables whose first row contains title_match."""
    matched = []
    with pdfplumber.open(pdf_path) as pdf:
        for idx in page_indices:
            tables = pdf.pages[idx].extract_tables() or []
            for table in tables:
                if not table or not table[0]:
                    continue
                row_text = " ".join(str(c) for c in table[0] if c).lower()
                if title_match.lower() in row_text:
                    matched.append(table)
    merged = _merge_rows(matched)
    return table_to_markdown(merged)


def merge_pdfplumber_tables(page_indices: list[int], pdf_path) -> str:
    all_rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for idx in page_indices:
            tables = pdf.pages[idx].extract_tables() or []
            for table in tables:
                all_rows.append(table)
    merged = _merge_rows(all_rows)
    return table_to_markdown(merged)


def merge_rotated_pages(
    doc: fitz.Document,
    page_nums: list[int],
    pdf_path,
    rotation: int = 90,
) -> str:
    all_tables: list[list[list]] = []
    for page_num in page_nums:
        tables = derotated_pdfplumber_tables(page_num - 1, pdf_path, rotation)
        if tables:
            from pipeline.extractors.rotated import _reverse_table_cells

            for table in _reverse_table_cells(tables):
                fixed = [
                    [
                        fix_rotated_title(str(c)) if c else ""
                        for c in row
                    ]
                    for row in table
                ]
                all_tables.append(fixed)

    if all_tables:
        merged = _merge_rows(all_tables)
        md = table_to_markdown(merged)
        sample = " ".join(str(c) for row in merged[:10] for c in row if c)
        if _table_readable(sample):
            return md

    parts = []
    for page_num in page_nums:
        page = doc[page_num - 1]
        content = extract_rotated_tables(
            page_num - 1, page, pdf_path, rotation=rotation, force_ocr=False
        )
        if content.strip():
            parts.append(content)
    return "\n\n".join(parts)


def merge_section_block(doc: fitz.Document, page_nums: list[int], pdf_path) -> str:
    """Merge self-assessment grid (Appendix 2) into one structured output."""
    section_map = {
        177: "Reception",
        178: "Production",
        179: "Interaction",
        180: "Mediation",
        181: "Mediation",
    }
    sections = []
    for page_num in page_nums:
        label = section_map.get(page_num)
        if label and (not sections or not sections[-1].startswith(f"## {label}")):
            sections.append(f"## {label}\n")

        with pdfplumber.open(pdf_path) as pdf:
            tables = pdf.pages[page_num - 1].extract_tables() or []

        if tables:
            fixed = _reverse_table_cells(tables)
            sections.append(tables_to_markdown(fixed))
        else:
            page = doc[page_num - 1]
            sections.append(extract_rotated_tables(page_num - 1, page, pdf_path))

    return "\n\n".join(sections)