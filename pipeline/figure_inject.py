"""Insert figure assets and strip flattened diagram labels without removing prose."""

from __future__ import annotations

import re

from pipeline.toc_zone import in_toc_zone, is_toc_listing_line

_PROSE_START = re.compile(
    r"^(?:The |In |As |It |This |Although |One |A1,|Level |Mastery |Plus |All |Figure \d+,|"
    r"Key aspects|Page \d|Chapter |\d+\.\d+\.)",
)
_LEVEL_ONLY = re.compile(r"^(?:C2|C1|B2|B1|A2|A1|Pre-A1)$")
_CAPS_LABEL = re.compile(r"^[A-Z][A-Z /-]{2,}$")


def _normalize_caption(line: str) -> str:
    s = re.sub(r"\s+", " ", line.strip())
    s = re.sub(r"\d+$", "", s)
    return s.lower()


def _caption_matches(line: str, header: str) -> bool:
    s = line.strip()
    if s.startswith("### ") or s.startswith("<!--"):
        return False
    if is_toc_listing_line(s):
        return False
    norm_header = _normalize_caption(header)
    norm_line = _normalize_caption(s)
    if norm_line == norm_header:
        return True
    if norm_line.startswith("figure ") and norm_line == norm_header:
        return True
    return False


def _is_label_soup_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if re.match(r"^Figure\s+\d+\s*–", s, re.I):
        return False
    if len(s) < 60 and s[0].islower():
        return True
    if _PROSE_START.match(s):
        return False
    if s.startswith("<!--") or s.startswith("!["):
        return False
    if _LEVEL_ONLY.match(s):
        return True
    if _CAPS_LABEL.match(s):
        return True
    if len(s) < 90 and not s.endswith((".", ";", ":", "?", "!")):
        words = s.split()
        if len(words) <= 8:
            return True
    return False


def _strip_soup_after_caption(lines: list[str], start_idx: int) -> int:
    """Return index after label-soup block."""
    i = start_idx
    while i < len(lines) and _is_label_soup_line(lines[i]):
        i += 1
    return i


def _page_region_end(lines: list[str], start_idx: int) -> int:
    i = start_idx
    while i < len(lines) and not lines[i].strip().startswith("<!-- page:"):
        i += 1
    return i


def _emit_page_without_soup(
    lines: list[str],
    out: list[str],
    start_idx: int,
) -> int:
    """Copy lines until next page marker, dropping diagram label soup."""
    end = _page_region_end(lines, start_idx)
    i = start_idx
    while i < end:
        if not _is_label_soup_line(lines[i]):
            out.append(lines[i])
        i += 1
    return i


def inject_png_figure(
    text: str,
    header: str,
    fid: str,
    asset_path: str,
    page: str,
    render_as: str = "png",
    list_section: tuple[int, int] | None = None,
) -> str:
    block = (
        f"<!-- db:id={fid} type=figure render_as={render_as} "
        f"product_tier=context pages={page} -->\n"
        f"### {header} | {fid}\n\n"
        f"![{header}]({asset_path})\n"
    )
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    replaced = False
    while i < len(lines):
        if list_section and list_section[0] <= i < list_section[1]:
            out.append(lines[i])
            i += 1
            continue
        line = lines[i]
        if not replaced and _caption_matches(line, header):
            out.append(block.rstrip())
            out.append("")
            i = _emit_page_without_soup(lines, out, i + 1)
            replaced = True
            continue
        if replaced and _caption_matches(line, header):
            i = _strip_soup_after_caption(lines, i + 1)
            continue
        out.append(line)
        i += 1
    if not replaced:
        out.append(block.rstrip())
    return "\n".join(out)


def inject_text_diagram(
    text: str,
    header: str,
    body_block: str,
    list_section: tuple[int, int] | None = None,
) -> str:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    replaced = False
    while i < len(lines):
        if list_section and list_section[0] <= i < list_section[1]:
            out.append(lines[i])
            i += 1
            continue
        line = lines[i]
        if not replaced and _caption_matches(line, header):
            out.append(body_block.rstrip())
            out.append("")
            i = _emit_page_without_soup(lines, out, i + 1)
            replaced = True
            continue
        if _caption_matches(line, header):
            i = _strip_soup_after_caption(lines, i + 1)
            continue
        out.append(line)
        i += 1
    return "\n".join(out)