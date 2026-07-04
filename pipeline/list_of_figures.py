"""Restore page-9 list of figures from registry."""

from __future__ import annotations

from pipeline.config import load_figures_registry

LIST_START = "LIST OF FIGURES"
LIST_END = "LIST OF TABLES"


def _list_block() -> list[str]:
    lines = [LIST_START, ""]
    for fig in load_figures_registry():
        title = fig["title"].upper()
        lines.append(f"{title}\t")
        lines.append(str(fig["page"]))
    lines.append(LIST_END)
    return lines


def restore_list_of_figures(text: str) -> str:
    lines = text.splitlines()
    start = end = -1
    for i, line in enumerate(lines):
        if LIST_START in line.upper() and start < 0:
            start = i
        if start >= 0 and LIST_END in line.upper():
            end = i
            break
    if start < 0 or end <= start:
        return text
    replacement = _list_block()
    return "\n".join(lines[:start] + replacement + lines[end + 1 :])