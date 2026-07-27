"""Extract table-of-contents pages with title/page pairs on the same row."""

from __future__ import annotations

import re

import fitz

import pipeline.config as cfg
from pipeline.toc_format import format_toc_entry, merge_toc_title

_PAGE_NUM = re.compile(r"Page\s+\d+", re.I)
_CEFR_RUNNING = re.compile(r"^\d+\s+CEFR", re.I)
_COMPANION_FOOTER = re.compile(r"CEFR.*Companion volume", re.I)
_TOC_PAGE_NUM = re.compile(r"^\d{1,3}$")
_Y_BAND = 7.0

def is_toc_page(page_num: int) -> bool:
    return page_num in cfg.TOC_PAGE_RANGE

def _is_footer(text: str, y0: float, page_height: float) -> bool:
    if y0 < page_height * 0.88:
        return False
    if _PAGE_NUM.search(text):
        return True
    if _CEFR_RUNNING.match(text.strip()):
        return True
    if _COMPANION_FOOTER.search(text):
        return True
    return False

def _collect_lines(page: fitz.Page) -> tuple[list[tuple[float, float, str]], list[str]]:
    page_height = page.rect.height
    body: list[tuple[float, float, str]] = []
    markers: list[str] = []
    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            text = "".join(sp.get("text", "") for sp in line.get("spans", [])).strip()
            if not text:
                continue
            y0 = line["bbox"][1]
            x0 = line["bbox"][0]
            if _is_footer(text, y0, page_height):
                markers.append(text)
            else:
                body.append((y0, x0, text))
    return body, markers

def _group_rows(
    lines: list[tuple[float, float, str]],
    page_width: float,
) -> list[tuple[str, str | None]]:
    if not lines:
        return []
    num_x = page_width * 0.82
    lines.sort(key=lambda e: e[0])
    bands: list[list[tuple[float, float, str]]] = []
    current: list[tuple[float, float, str]] = []
    band_y = -999.0
    for y0, x0, text in lines:
        if not current or abs(y0 - band_y) <= _Y_BAND:
            current.append((y0, x0, text))
            if not current or band_y < 0:
                band_y = y0
        else:
            bands.append(current)
            current = [(y0, x0, text)]
            band_y = y0
    if current:
        bands.append(current)

    rows: list[tuple[str, str | None]] = []
    for band in bands:
        left_parts = [t for _, x, t in sorted(band, key=lambda e: e[1]) if x < num_x]
        right_parts = [t for _, x, t in sorted(band, key=lambda e: e[1]) if x >= num_x]
        title = " ".join(left_parts).strip()
        page = None
        for part in right_parts:
            if _TOC_PAGE_NUM.match(part.strip()):
                page = part.strip()
                break
        if title or page:
            rows.append((title, page))
    return _merge_wrapped_rows(rows)

def _is_section_banner(title: str) -> bool:
    upper = title.strip().upper()
    return upper == "CONTENTS" or upper.startswith("LIST OF ")

def _is_entry_start(title: str) -> bool:
    return bool(
        re.match(
            r"^(?:FOREWORD|PREFACE|CHAPTER\s+\d+:|APPENDIX\s+\d+:|FIGURE\s+\d+|TABLE\s+\d+|\d+\.\d+)",
            title.strip(),
            re.I,
        )
    )

def _should_merge(prev_title: str, title: str) -> bool:
    prev = prev_title.strip()
    if _is_section_banner(prev):
        return False
    if prev.rstrip().endswith(":"):
        return True
    if title.strip().startswith("("):
        return True
    if _is_entry_start(title) and not prev.rstrip().endswith(":"):
        return False
    if prev.rstrip().endswith(("–", "-", "—")):
        return True
    if title and title[0].islower():
        return True
    return False

def _merge_wrapped_rows(rows: list[tuple[str, str | None]]) -> list[tuple[str, str | None]]:
    merged: list[tuple[str, str | None]] = []
    for title, page in rows:
        if not title and page:
            continue
        if page and merged and merged[-1][1] is None:
            prev_title, _ = merged.pop()
            if _should_merge(prev_title, title):
                merged.append((merge_toc_title(prev_title, title), page))
            else:
                merged.append((prev_title, None))
                merged.append((title, page))
        elif not page and merged and merged[-1][1] is None:
            prev_title, _ = merged.pop()
            if _should_merge(prev_title, title):
                merged.append((f"{prev_title} {title}".strip(), None))
            else:
                merged.append((prev_title, None))
                merged.append((title, None))
        else:
            merged.append((title, page))
    return merged

def extract_toc_page(page: fitz.Page, page_num: int) -> str:
    body_lines, markers = _collect_lines(page)
    rows = _group_rows(body_lines, page.rect.width)
    formatted = [format_toc_entry(title, page) for title, page in rows if title]
    parts: list[str] = []
    if formatted:
        parts.append("\n".join(formatted))
    if markers:
        parts.append(f"*{markers[-1]}*\n\n<!-- page:{page_num} -->")
    else:
        parts.append(f"Page **{page_num}**\n\n<!-- page:{page_num} -->")
    return "\n\n".join(parts)