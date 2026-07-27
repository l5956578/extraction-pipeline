"""Detect and protect the PDF table-of-contents region in merged markdown."""

from __future__ import annotations

import re
import pipeline.config as cfg
from pipeline.config import load_figures_registry

_TOC_START = re.compile(r"^##\s+Contents$", re.I)
_PAGE_10 = re.compile(r"<!--\s*page:10\s*-->", re.I)
_TOC_LISTING = re.compile(
    r"^-\s+(?:FIGURE|TABLE)\s+\d+.*—\s*\d{1,3}\s*$",
    re.I,
)
_TOC_PAGE_SUFFIX = re.compile(r" — \d{1,3}$")

def toc_bounds(lines: list[str]) -> tuple[int, int] | None:
    start = end = -1
    for i, line in enumerate(lines):
        if _TOC_START.match(line.strip()):
            start = i
        if start >= 0 and _PAGE_10.search(line):
            end = i
            break
    if start >= 0 and end > start:
        return start, end
    return None

def in_toc_zone(index: int, bounds: tuple[int, int] | None) -> bool:
    if not bounds:
        return False
    return bounds[0] <= index < bounds[1]

def is_toc_listing_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if _TOC_LISTING.match(s):
        return True
    if s.startswith("## List of"):
        return True
    if re.match(r"^-\s+FIGURE\s+\d+", s, re.I) and _TOC_PAGE_SUFFIX.search(s):
        return True
    if re.match(r"^-\s+TABLE\s+\d+", s, re.I) and _TOC_PAGE_SUFFIX.search(s):
        return True
    return False

def rebuild_list_of_figures_tables(lines: list[str], bounds: tuple[int, int]) -> list[str]:
    """Replace polluted list-of-figures/tables subsection with plain TOC lines."""
    start, end = bounds
    lof_start = lof_end = -1
    for i in range(start, end):
        s = lines[i].strip().lower()
        if s == "## list of tables and figures":
            lof_start = i
        if lof_start >= 0 and s == "## list of tables":
            lof_end = i
            break
    if lof_start < 0 or lof_end < 0:
        return lines

    fig_lines = ["## List of tables and figures", "## List of figures"]
    for fig in load_figures_registry():
        fig_lines.append(f"- {fig['title'].upper()} — {fig['page']}")

    fig_lines.append("## List of tables")
    table_entries = [
        (23, "TABLE 1 – THE CEFR DESCRIPTIVE SCHEME AND ILLUSTRATIVE DESCRIPTORS: UPDATES AND ADDITIONS"),
        (24, "TABLE 2 – SUMMARY OF CHANGES TO THE ILLUSTRATIVE DESCRIPTORS"),
        (33, "TABLE 3 – MACRO-FUNCTIONAL BASIS OF CEFR CATEGORIES FOR COMMUNICATIVE LANGUAGE ACTIVITIES"),
        (35, "TABLE 4 – COMMUNICATIVE LANGUAGE STRATEGIES IN THE CEFR"),
        (44, "TABLE 5 – THE DIFFERENT PURPOSES OF DESCRIPTORS"),
    ]
    for page, title in table_entries:
        fig_lines.append(f"- {title} — {page}")

    tail = lines[lof_end:end]
    footers = [
        ln
        for ln in tail
        if ln.strip().startswith("<!-- page:") or (ln.strip().startswith("*") and "page" in ln.lower())
    ]

    return lines[:lof_start] + fig_lines + footers + lines[end:]

def strip_toc_figure_artifacts(text: str) -> str:
    lines = text.splitlines()
    bounds = toc_bounds(lines)
    if not bounds:
        return text
    return "\n".join(rebuild_list_of_figures_tables(lines, bounds))