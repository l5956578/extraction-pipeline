"""Shared TOC entry formatting and numbered-section heading depth."""

from __future__ import annotations

import re

_PAGE_SUFFIX = re.compile(r" — (\d{1,3})$")
_NUMBERED = re.compile(r"^(\d+(?:\.\d+)*)\.\s+", re.I)
_HEADING_PREFIX = re.compile(r"^#+\s*")


def strip_toc_line(line: str) -> tuple[str, str | None]:
    """Return (title, page) from a TOC line with optional `` — N`` suffix."""
    s = line.strip()
    s = _HEADING_PREFIX.sub("", s).removeprefix("- ").strip()
    m = _PAGE_SUFFIX.search(s)
    if m:
        return s[: m.start()].strip(), m.group(1)
    return s, None


def heading_depth_for_numbered(title: str) -> int | None:
    """Map ``2.1.`` → 3, ``3.1.1.`` → 4, ``3.1.1.1.`` → 5."""
    m = _NUMBERED.match(title.strip())
    if not m:
        return None
    parts = m.group(1).split(".")
    if len(parts) < 2:
        return None
    return min(len(parts) + 1, 6)


def format_numbered_heading(title: str) -> str | None:
    depth = heading_depth_for_numbered(title)
    if depth is None:
        return None
    return f"{'#' * depth} {title.strip()}"


def is_descriptor_bullet(title: str) -> bool:
    """ALL-CAPS scale names and similar entries stay as list items in the TOC."""
    s = title.strip()
    if _NUMBERED.match(s):
        return False
    if re.match(r"^(?:CHAPTER|APPENDIX|FIGURE|TABLE|LIST OF )\s", s, re.I):
        return False
    if s.upper() in ("CONTENTS", "APPENDICES", "FOREWORD") or s.upper().startswith("PREFACE"):
        return False
    return bool(re.match(r"^[A-Z0-9 ,:()–\-/&.]+$", s)) and len(s) > 3


def format_toc_entry(title: str, page: str | None = None) -> str:
    """Format one table-of-contents row with heading levels matching the PDF."""
    title = title.strip()
    suffix = f" — {page}" if page else ""
    upper = title.upper()

    if upper == "CONTENTS":
        return "## Contents"
    if upper == "LIST OF TABLES AND FIGURES":
        return "## List of tables and figures"
    if upper == "LIST OF FIGURES":
        return "## List of figures"
    if upper == "LIST OF TABLES":
        return "## List of tables"
    if upper.startswith("LIST OF "):
        return f"## {title.title()}"

    if upper in ("FOREWORD",):
        return f"## Foreword{suffix}"
    if upper.startswith("PREFACE"):
        return f"## Preface with acknowledgements{suffix}"

    if re.match(r"^CHAPTER\s+\d+:", title, re.I):
        return f"## {title}{suffix}"

    if upper == "APPENDICES":
        return f"## APPENDICES{suffix}"
    if re.match(r"^APPENDIX\s+\d+:", title, re.I):
        return f"## {title}{suffix}"

    numbered = format_numbered_heading(title)
    if numbered:
        return numbered + suffix

    if re.match(r"^(FIGURE|TABLE)\s+\d+", title, re.I):
        return f"### {title}{suffix}"

    if is_descriptor_bullet(title):
        return f"- {title}{suffix}"

    return title + suffix


def merge_toc_title(prev: str, nxt: str) -> str:
    return f"{prev.rstrip()} {nxt.lstrip()}".strip()