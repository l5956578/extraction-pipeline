"""Extract page text with bold spans and correct block order."""

from __future__ import annotations

import fitz

from pipeline.page_layout import extract_page_body, extract_page_body_excluding


def extract_rich_text(page: fitz.Page) -> str:
    """Body only — inventory emits footer separately (avoids duplicate page markers)."""
    return extract_page_body(page)


def extract_rich_page(page: fitz.Page, page_num: int) -> str:
    """Body only for reading_order `rich_page` elements.

    Page markers / footnotes come from the inventory ``footer`` element so we
    never double-emit ``<!-- page:N -->``.
    """
    del page_num  # reserved for callers; body path is page-local
    return extract_page_body(page)


def extract_rich_page_excluding(
    page: fitz.Page,
    page_num: int,
    exclude_rects: list[tuple[float, float, float, float]] | None = None,
) -> str:
    """Body text with exclusive-region exclusion (figure/callout bboxes).

    C2-ADJ: when PNG/text_diagram owns a region, prose must not dump that region.
    """
    del page_num
    return extract_page_body_excluding(page, exclude_rects)