"""Extract page text with bold spans and correct block order."""

from __future__ import annotations

import fitz

from pipeline.page_layout import extract_body_text, extract_page_content


def extract_rich_text(page: fitz.Page) -> str:
    return extract_body_text(page)


def extract_rich_page(page: fitz.Page, page_num: int) -> str:
    return extract_page_content(page, page_num)