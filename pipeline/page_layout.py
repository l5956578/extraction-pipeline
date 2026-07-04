"""Reassemble PDF page text in reading order with footnotes at bottom."""

from __future__ import annotations

import re

import fitz

_BOLD = 2
_PAGE_NUM = re.compile(r"Page\s+\d+", re.I)
_CEFR_RUNNING = re.compile(r"^\d+\s+CEFR", re.I)
_FOOTNOTE = re.compile(r"^(\d{1,2})\.(?:\s+|\s*$)")
_COMPANION_FOOTER = re.compile(r"CEFR.*Companion volume", re.I)
_ROW_Y_TOL = 3.0


def _span_text(spans: list[dict]) -> str:
    parts: list[str] = []

    def _append_bold(fragment: str) -> None:
        if (
            parts
            and parts[-1].startswith("**")
            and parts[-1].endswith("**")
            and len(parts[-1]) > 4
        ):
            inner = parts[-1][2:-2]
            parts[-1] = f"**{inner}{fragment}**"
        else:
            parts.append(f"**{fragment}**")

    for sp in spans:
        t = sp.get("text", "")
        if not t:
            continue
        if sp.get("flags", 0) & _BOLD:
            _append_bold(t)
        else:
            parts.append(t)
    return "".join(parts)


def _is_page_marker(text: str, y0: float, page_height: float) -> bool:
    s = text.strip()
    if not s:
        return False
    if y0 < page_height * 0.88:
        return False
    if _PAGE_NUM.search(s):
        return True
    if _CEFR_RUNNING.match(s):
        return True
    if _COMPANION_FOOTER.search(s):
        return True
    return False


def _classify_line(text: str, y0: float, page_height: float) -> str:
    s = text.strip()
    if not s:
        return "skip"
    if _is_page_marker(text, y0, page_height):
        return "page_marker"
    if _FOOTNOTE.match(s) and y0 > page_height * 0.62:
        return "footnote"
    return "body"


def _is_footnote_continuation(text: str) -> bool:
    s = text.strip()
    if not s:
        return False
    if _FOOTNOTE.match(s):
        return False
    if s[0].islower():
        return True
    if s.startswith(("www.", "http", "available at", "bank-of", "for educators")):
        return True
    if len(s) < 90 and not s.endswith("."):
        return True
    return False


def _merge_same_row_fragments(
    entries: list[tuple[float, float, str]],
    page_width: float,
) -> list[tuple[float, float, str]]:
    """Join fragments on the same visual row (e.g. footnote number + URL)."""
    if not entries:
        return []
    mid = page_width * 0.48
    sorted_entries = sorted(entries, key=lambda e: (e[0], e[1]))
    merged: list[tuple[float, float, str]] = []
    i = 0
    while i < len(sorted_entries):
        row_y = sorted_entries[i][0]
        row: list[tuple[float, float, str]] = []
        while i < len(sorted_entries) and abs(sorted_entries[i][0] - row_y) <= _ROW_Y_TOL:
            row.append(sorted_entries[i])
            i += 1
        for column_entries in (
            sorted((e for e in row if e[1] < mid), key=lambda e: e[1]),
            sorted((e for e in row if e[1] >= mid), key=lambda e: e[1]),
        ):
            col = list(column_entries)
            if not col:
                continue
            if len(col) == 1:
                merged.append(col[0])
            else:
                y, x = col[0][0], col[0][1]
                text = " ".join(part[2].strip() for part in col if part[2].strip())
                merged.append((y, x, text))
    return merged


def _format_body_lines(
    body_entries: list[tuple[float, float, str]],
    page_width: float,
) -> list[str]:
    merged = _merge_same_row_fragments(body_entries, page_width)
    if not merged:
        return []
    mid = page_width * 0.48
    left = sorted((e for e in merged if e[1] < mid), key=lambda e: e[0])
    right = sorted((e for e in merged if e[1] >= mid), key=lambda e: e[0])
    if len(left) >= 5 and len(right) >= 5:
        ordered = left + right
    else:
        ordered = sorted(merged, key=lambda e: e[0])

    return [text for _, _, text in ordered]


def _partition_zones(
    entries: list[tuple[float, float, str, str]],
    page_width: float,
    page_height: float,
) -> dict[str, list[str]]:
    """Split sorted lines into body (column-ordered), footnotes, and markers."""
    body_entries: list[tuple[float, float, str]] = []
    footnote_entries: list[tuple[float, str]] = []
    markers: list[str] = []
    footnote_buf: list[str] = []
    in_footnote_zone = False

    for y0, x0, kind, text in entries:
        if kind == "page_marker":
            if footnote_buf:
                footnote_entries.append((y0, " ".join(footnote_buf)))
                footnote_buf = []
            markers.append(text)
            in_footnote_zone = False
            continue

        if kind == "footnote" or (
            in_footnote_zone
            and y0 > page_height * 0.65
            and (kind == "body" or _is_footnote_continuation(text))
        ):
            if kind == "footnote" and footnote_buf:
                footnote_entries.append((y0, " ".join(footnote_buf)))
                footnote_buf = []
            footnote_buf.append(text)
            in_footnote_zone = True
            continue

        if footnote_buf:
            footnote_entries.append((y0, " ".join(footnote_buf)))
            footnote_buf = []
        in_footnote_zone = False
        if kind == "body":
            body_entries.append((y0, x0, text))

    if footnote_buf:
        footnote_entries.append((page_height, " ".join(footnote_buf)))

    return {
        "body": _format_body_lines(body_entries, page_width),
        "footnotes": [t for _, t in sorted(footnote_entries, key=lambda e: e[0])],
        "page_markers": markers,
    }


def classify_page_zones(page: fitz.Page) -> dict[str, list[str]]:
    """Return body lines, footnotes, and page markers in reading order."""
    page_height = page.rect.height
    entries: list[tuple[float, float, str, str]] = []

    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            text = _span_text(line.get("spans", [])).strip()
            if not text:
                continue
            y0 = line["bbox"][1]
            x0 = line["bbox"][0]
            kind = _classify_line(text, y0, page_height)
            if kind != "skip":
                entries.append((y0, x0, kind, text))

    entries.sort(key=lambda e: e[0])
    return _partition_zones(entries, page.rect.width, page_height)


def format_page_footer(page_num: int, zones: dict[str, list[str]]) -> str:
    parts: list[str] = []
    if zones["footnotes"]:
        parts.append("\n".join(zones["footnotes"]))
    if zones["page_markers"]:
        marker = zones["page_markers"][-1]
        parts.append(f"<!-- page:{page_num} -->\n*{marker}*")
    elif page_num:
        parts.append(f"<!-- page:{page_num} -->")
    return "\n\n".join(parts)


def extract_body_text(page: fitz.Page) -> str:
    zones = classify_page_zones(page)
    return "\n".join(zones["body"])


def extract_page_content(page: fitz.Page, page_num: int) -> str:
    from pipeline.toc_layout import extract_toc_page, is_toc_page

    if is_toc_page(page_num):
        return extract_toc_page(page, page_num)
    zones = classify_page_zones(page)
    parts: list[str] = []
    if zones["body"]:
        parts.append("\n".join(zones["body"]))
    footer = format_page_footer(page_num, zones)
    if footer:
        parts.append(footer)
    return "\n\n".join(parts)