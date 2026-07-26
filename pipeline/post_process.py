"""Structured Markdown formatting — integrated final step of Session 1 merge.

Reads and writes ``output/CEFR_Companion_Volume.md`` in place so there is a
single deliverable (paragraph merge, chapter formatting, page-marker spacing).

Merged from the former Session 2 ``format_markdown.py`` with these integration rules:

- **Bold spacing** — never strip spaces around ``**``; use ``fix_bold_markdown`` from
  ``prose_format`` once at the end of the pipeline (Session 1 fix).
- **OCR fixes** — ``fix_ocr_typos`` handles typos/hyphenation only; bold rules removed
  from the old ``_fix_ocr`` that caused ``The**Common...**`` regressions.
- **Signature blocks** — short lines after sentence endings (names, bold titles) and
  bold-only lines are treated as block starters so paragraph merge does not glue the
  Foreword signature onto the preceding paragraph.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path

from pipeline.config import FINAL_DIR, ROOT
from pipeline.prose_format import (
    _format_level_callouts,
    fix_bold_markdown,
    fix_ocr_typos,
)
from pipeline.toc_format import (
    format_numbered_heading,
    format_toc_entry,
    merge_toc_title,
    strip_toc_line,
)

FINAL_MARKDOWN = FINAL_DIR / "CEFR_Companion_Volume.md"
RUN_LOG = ROOT / "metadata" / "last_format_run.txt"

# PDF list-marker artifacts only — never match a wrapped word like "form".
_BULLET_MARKERS = re.compile(
    r"^(\s*)(?:f\*\*|f\s*\*\*|f\s+(?=[A-Z*\"'(])|▶|▸|►|•|▪|‣)\s*",
    re.I,
)
_LEVEL_LABEL = re.compile(
    r"^(?:C2|C1|B2\+?|B1\+?|A2\+?|A1\+?|Pre-A1|A2|A1|B2|B1|Plus levels?)$",
    re.I,
)
_PAGE_MARKER = re.compile(
    r"^(?:Page\s+\d+|﻿\s*Page\s+\d+|\d+\s+CEFR\s*[–-]\s*Companion volume|"
    r"Key aspects of the CEFR.*Page\s+\d+)",
    re.I,
)
_HEADING = re.compile(r"^#{1,6}\s")
_CHAPTER_HEADING = re.compile(r"^## Chapter \d+\s*$", re.I)
_HTML_COMMENT = re.compile(r"^<!--")
_IMAGE = re.compile(r"^!\[")
_HRULE = re.compile(r"^-{3,}\s*$")
_TABLE_ROW = re.compile(r"^\|")
_FENCE = re.compile(r"^```")
_LIST_ITEM = re.compile(r"^(\s*)-\s+")
_NUMBERED_FOOTNOTE = re.compile(r"^\d+\.\s")
_BOLD_ONLY = re.compile(r"^\*\*[^*]+\*\*$")
_SECTION_TITLE = re.compile(
    r"^(?:CHAPTER\s+\d+|FOREWORD|PREFACE|CONTENTS|LIST OF (?:FIGURES|TABLES)|"
    r"APPENDIX\s+\d+|FIGURE\s+\d+|TABLE\s+\d+|\d+\.\d+(?:\.\d+)*\.\s+[A-Z])",
    re.I,
)
_TOC_ENTRY = re.compile(r"^[A-Z][A-Z0-9 ,:–\-/()]+$")
_COUNTRY_BLOCK = re.compile(
    r"^(?:CROATIA|DENMARK|FINLAND|FRANCE|NORWAY|POLAND|PORTUGAL|SWITZERLAND|"
    r"TAIWAN|UNITED|RUSSIAN|CZECH|CDN-OTTAWA|ENG$|PREMS)",
    re.I,
)
_SENTENCE_END = re.compile(r"[.!?;:)\]\"']\s*$")
_LONE_PAGE_NUM = re.compile(r"^\d{1,3}$")
_PAGE_COMMENT = re.compile(r"^<!--\s*page:\d+\s*-->$", re.I)
_PAGE_ITALIC = re.compile(r"^\*.+\*$")
_CAPS_LINE = re.compile(r"^[A-Z0-9 ,:–\-/&()]+$")
_PROSE_START = re.compile(
    r"\s+(?:The|This|Many|Because|In|As|It|Neither|Hence|However|Teacher|One|After|"
    r"A few|Building|Can|As stated)\b"
)


def _is_page_comment(line: str) -> bool:
    return bool(_PAGE_COMMENT.match(line.strip()))


def _is_page_italic(line: str) -> bool:
    s = line.strip()
    if not _PAGE_ITALIC.match(s):
        return False
    return "page" in s.strip("*").lower()


def _is_block_starter(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    # Callout / markdown blockquotes must never soft-join into one line (UV-01).
    if s.startswith(">"):
        return True
    # C2-ADJ P3: never soft-join across element fences / structural markers
    if s.startswith("<!-- el:start") or s.startswith("<!-- el:end"):
        return True
    # Page captions must not join onto footnotes (C2-ADJ / log 04).
    if re.match(r"^Page\s+\*\*\d+\*\*", s) or re.match(r"^\*Page\s+\d+", s, re.I):
        return True
    if s.startswith("<!-- db:id=") or s.startswith("!["):
        return True
    # Numbered footnotes (standalone or after body) — hard boundary
    if re.match(r"^\d{1,2}\.\s+\S", s) and (
        "http" in s.lower() or "available at" in s.lower() or len(s) > 40
    ):
        return True
    if (
        _HEADING.match(s)
        or _HTML_COMMENT.match(s)
        or _IMAGE.match(s)
        or _HRULE.match(s)
        or _TABLE_ROW.match(s)
        or _FENCE.match(s)
        or _LIST_ITEM.match(s)
        or _PAGE_MARKER.match(s)
        or _PAGE_HTML.match(s)
        or _LEVEL_LABEL.match(s)
        or _NUMBERED_FOOTNOTE.match(s)
        or _SECTION_TITLE.match(s)
        or _COUNTRY_BLOCK.match(s)
        or _LONE_PAGE_NUM.match(s)
        or _BOLD_ONLY.match(s)
    ):
        return True
    # Visible page footer lines must never fold into prior prose/lists.
    if _page_num_from_visible(s) and (
        s.startswith("*") or re.match(r"^Page\s+", s, re.I)
    ):
        return True
    if s in ("CONTENTS", "FOREWORD"):
        return True
    return False


def _should_break_paragraph(prev: str, nxt: str) -> bool:
    """Decide soft-wrap vs new paragraph when y-gap is unavailable (markdown only).

    Do **not** break solely because prev ends with ``.`` and nxt starts with
    ``The`` / ``Here`` / etc. — that false-splits CEFR paragraphs (page 22).
    Real paragraph breaks should already be blank lines (from extract y-gap).
    """
    prev = prev.strip()
    nxt = nxt.strip()
    if not prev or not nxt:
        return True
    if _is_block_starter(nxt):
        return True
    if _BOLD_ONLY.match(nxt):
        return True
    # Short signature / attribution after a finished sentence (not body prose).
    if _SENTENCE_END.search(prev) and len(nxt) < 60 and not _SENTENCE_END.search(nxt):
        if nxt[0].isupper() and not nxt.startswith(
            ("The ", "This ", "In ", "Here ", "As ", "It ", "However")
        ):
            return True
    return False


def _join_wrapped_lines(lines: list[str]) -> list[str]:
    out: list[str] = []
    buf: list[str] = []
    in_code = False

    def flush() -> None:
        nonlocal buf
        if buf:
            out.append(" ".join(buf))
            buf = []

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if _FENCE.match(stripped):
            flush()
            out.append(line)
            in_code = not in_code
            continue

        if in_code:
            out.append(line)
            continue

        if not stripped:
            flush()
            if out and out[-1] != "":
                out.append("")
            continue

        if _is_block_starter(stripped):
            flush()
            # List items stay open in buf so the next soft-wrap line can join.
            if _is_list_item_line(stripped) or _BULLET_MARKERS.match(stripped):
                buf.append(stripped)
            else:
                out.append(stripped)
            continue

        # Soft-wrap onto previous list item already flushed to out
        if (
            not buf
            and out
            and _is_list_item_line(out[-1])
            and _looks_like_list_continuation(out[-1], stripped)
        ):
            out[-1] = f"{out[-1].rstrip()} {stripped}"
            continue

        if buf and _should_break_paragraph(buf[-1], stripped):
            # Don't break list soft-wraps on uppercase mid-item
            if _is_list_item_line(buf[0]) or _BULLET_MARKERS.match(buf[0].strip()):
                if _looks_like_list_continuation(" ".join(buf), stripped):
                    buf.append(stripped)
                    continue
            flush()
            if out and out[-1] != "":
                out.append("")
            buf.append(stripped)
        elif not buf:
            buf.append(stripped)
        else:
            buf.append(stripped)

    flush()
    return out


def _demote_footnote_headings(lines: list[str]) -> list[str]:
    """Footnotes like ``14. **Title**`` must not be markdown headings."""
    out: list[str] = []
    for line in lines:
        s = line.strip()
        if re.match(r"^#{1,6}\s+\d{1,2}\.\s+", s):
            out.append(re.sub(r"^#{1,6}\s+", "", line))
        else:
            out.append(line)
    return out


def _promote_headings(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        s = line.strip()
        if re.match(r"^CHAPTER\s+\d+:", s, re.I):
            out.append(f"## {s}")
            continue
        numbered = format_numbered_heading(s)
        if numbered and not _HEADING.match(s):
            out.append(numbered)
            continue
        out.append(line)
    return out


def _promote_section_headings(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        s = line.strip()
        if s == "FOREWORD":
            out.append("## Foreword")
            continue
        if s == "PREFACE WITH ACKNOWLEDGEMENTS":
            out.append("## Preface with acknowledgements")
            continue
        out.append(line)
    return out


def _normalize_toc_region(lines: list[str]) -> list[str]:
    """Reformat the TOC with correct heading levels; merge wrapped chapter/appendix titles."""
    out: list[str] = []
    in_toc = False
    toc_buf: list[str] = []

    def flush_toc_line() -> None:
        if not toc_buf:
            return
        title, page = strip_toc_line(toc_buf[0])
        for extra in toc_buf[1:]:
            extra_title, extra_page = strip_toc_line(extra)
            title = merge_toc_title(title, extra_title)
            page = page or extra_page
        out.append(format_toc_entry(title, page))
        toc_buf.clear()

    for line in lines:
        s = line.strip()
        if s in ("## Contents", "CONTENTS"):
            flush_toc_line()
            in_toc = True
            out.append("## Contents")
            out.append("")
            continue

        if in_toc:
            if _is_page_comment(s):
                page_num = int(re.search(r"page:(\d+)", s, re.I).group(1))
                if page_num >= 10:
                    flush_toc_line()
                    in_toc = False
                    out.append(line)
                    continue
            if not s:
                continue
            if _is_page_italic(s):
                flush_toc_line()
                out.append(line)
                continue
            title, _ = strip_toc_line(line)
            if not title:
                continue
            if toc_buf:
                prev_title, _ = strip_toc_line(toc_buf[-1])
                if prev_title.rstrip().endswith(":") or title.startswith("("):
                    toc_buf.append(line)
                    continue
                flush_toc_line()
            toc_buf.append(line)
            continue

        flush_toc_line()
        out.append(line)

    flush_toc_line()
    return out


def _is_caps_title_line(line: str) -> bool:
    s = line.strip()
    return bool(s) and not _HEADING.match(s) and (_CAPS_LINE.match(s) or s.isupper())


def _toc_region_ended(lines: list[str], index: int) -> bool:
    for j in range(index):
        s = lines[j].strip()
        if _is_page_comment(s):
            m = re.search(r"page:(\d+)", s, re.I)
            if m and int(m.group(1)) >= 10:
                return True
    return False


def _ensure_heading_body_spacing(lines: list[str]) -> list[str]:
    """Blank line after headings before body prose; preserve Chapter N + caps title pairs."""
    out: list[str] = []
    in_code = False
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if _FENCE.match(stripped):
            in_code = not in_code
            out.append(line)
            i += 1
            continue
        if in_code:
            out.append(line)
            i += 1
            continue

        if not _toc_region_ended(lines, i):
            out.append(line)
            i += 1
            continue

        out.append(line)

        if _HEADING.match(stripped):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                nxt = lines[j].strip()
                if not _HEADING.match(nxt):
                    if _CHAPTER_HEADING.match(stripped) and _is_caps_title_line(nxt):
                        pass
                    elif out and out[-1] != "":
                        out.append("")
        elif _is_caps_title_line(stripped) and i > 0:
            prev = out[-2].strip() if len(out) >= 2 and out[-1] == "" else out[-1].strip() if out else ""
            if _CHAPTER_HEADING.match(prev):
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and not _HEADING.match(lines[j].strip()):
                    if out[-1] != "":
                        out.append("")

        i += 1
    return out


# Trailing PDF page number glued onto footnotes / prose (e.g. "...1680459f97. Page **21**").
_TRAILING_PAGE = re.compile(
    r"^(?P<body>.+?)\s+Page\s+\*?\*?(?P<num>\d+)\*?\*?\s*$",
    re.I,
)
_PAGE_VISIBLE = re.compile(
    r"^(?:\*?Page\s+\*?\*?(?P<num>\d+)\*?\*?.+?\*?|"
    r"Page\s+\*?\*?(?P<num2>\d+)\*?\*?)\s*$",
    re.I,
)
_PAGE_HTML = re.compile(r"^<!--\s*page:(\d+)\s*-->$", re.I)


def _page_num_from_visible(line: str) -> str | None:
    s = line.strip()
    m = re.search(r"Page\s+\*?\*?(\d+)\*?\*?", s, re.I)
    if not m:
        return None
    # Visible footer / caption lines only (not long prose that mentions "Page").
    if len(s) > 120 and not s.startswith("*"):
        return None
    if s.startswith("*") or re.match(r"^Page\s+", s, re.I):
        return m.group(1)
    return None


def _emit_page_footer_block(
    out: list[str],
    page_num: str,
    *,
    visible: str | None,
    last_page: str | None,
) -> str:
    """Append human-readable page line then ``<!-- page:N -->``. Returns new last_page."""
    if page_num == last_page:
        return last_page
    if out and out[-1] != "":
        out.append("")
    if visible:
        out.append(visible)
        out.append("")
    else:
        out.append(f"Page **{page_num}**")
        out.append("")
    out.append(f"<!-- page:{page_num} -->")
    return page_num


def _normalize_page_markers(lines: list[str]) -> list[str]:
    """Page footers: visible text first, then ``<!-- page:N -->``; drop dups.

    - Peel trailing ``Page **N**`` off footnotes (keep as its own visible line).
    - Reorder ``<!-- page:N -->`` + ``*Page N …*`` → caption, then HTML comment.
    """
    out: list[str] = []
    last_page: str | None = None
    i = 0
    n = len(lines)
    while i < n:
        s = lines[i].strip().lstrip("\ufeff").strip()

        # 1) HTML comment — maybe followed by italic/visible caption (wrong order today)
        m_html = _PAGE_HTML.match(s)
        if m_html:
            page_num = m_html.group(1)
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            visible: str | None = None
            if j < n:
                vs = lines[j].strip()
                vnum = _page_num_from_visible(vs)
                if vnum == page_num:
                    visible = vs
                    i = j + 1
                else:
                    i += 1
            else:
                i += 1
            last_page = _emit_page_footer_block(
                out, page_num, visible=visible, last_page=last_page
            )
            continue

        # 2) Standalone visible page caption (optionally followed by HTML)
        vnum = _page_num_from_visible(s)
        if vnum and (s.startswith("*") or re.match(r"^Page\s+", s, re.I)):
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j < n and _PAGE_HTML.match(lines[j].strip()):
                html_num = _PAGE_HTML.match(lines[j].strip()).group(1)
                if html_num == vnum:
                    i = j + 1
                else:
                    i += 1
            else:
                i += 1
            last_page = _emit_page_footer_block(
                out, vnum, visible=s, last_page=last_page
            )
            continue

        # 3) Trailing Page **N** glued on footnote/prose
        m3 = _TRAILING_PAGE.match(s)
        if m3 and len(m3.group("body").strip()) > 3:
            body = m3.group("body").strip()
            page_num = m3.group("num")
            out.append(body)
            last_page = _emit_page_footer_block(
                out, page_num, visible=f"Page **{page_num}**", last_page=last_page
            )
            i += 1
            # Skip following duplicate HTML for same page
            while i < n and not lines[i].strip():
                i += 1
            if i < n and _PAGE_HTML.match(lines[i].strip()):
                if _PAGE_HTML.match(lines[i].strip()).group(1) == page_num:
                    i += 1
            continue

        # 4) Other bare page markers → visible + HTML
        m = re.match(r"^Page\s+\*?\*?(\d+)\*?\*?\s*$", s, re.I)
        if m:
            last_page = _emit_page_footer_block(
                out, m.group(1), visible=f"Page **{m.group(1)}**", last_page=last_page
            )
            i += 1
            continue
        m2 = re.match(r"^(\d+)\s+CEFR\s*[–-]\s*Companion volume", s, re.I)
        if m2:
            last_page = _emit_page_footer_block(
                out, m2.group(1), visible=s, last_page=last_page
            )
            i += 1
            continue

        if s and not (s.startswith("*") and "page" in s.lower()):
            if not s.startswith("*"):
                last_page = None
        out.append(lines[i])
        i += 1
    return out


def _fix_inline_bullets(text: str) -> str:
    """Normalize PDF dingbat bullets (Wingdings ``f``, arrows) to markdown lists.

    Handles line-start bullets **and** mid-line sequences common in CEFR lists::
        - first aim; f second aim; f third aim
    """
    text = re.sub(r"►\s*", "- ", text)
    text = re.sub(r":\s*f\*\*", ":\n\n- **", text)
    text = re.sub(r"\*\*\s*f\*\*", "**\n- **", text)
    text = re.sub(r"(?<=\n)f\*\*", "- **", text)
    # Mid-line Wingdings bullet after semicolon or between list items.
    # PDF items often continue with lowercase ("f provide…"). Avoid matching " of form".
    text = re.sub(
        r";\s+f\s+(?=[A-Za-z“\"'(\[])",
        ";\n- ",
        text,
    )
    # Some extract/cleanup paths already rewrote dingbat to "-" but left it mid-line:
    #   - item one; - item two; - item three
    text = re.sub(
        r";\s+-\s+(?=[A-Za-z“\"'(\[])",
        ";\n- ",
        text,
    )
    # Bare " f " between items without semicolon (rarer): require letter after f.
    text = re.sub(
        r"(?<=[a-z0-9)\]\"'])\s+f\s+(?=[A-Za-z“\"'(\[])",
        "\n- ",
        text,
    )
    # Bold section heading glued after list/sentence: ). **Background…**
    text = re.sub(
        r"([.\)])\s+(\*\*(?:Background|Defining|An alternative|Step \d)[^*]+\*\*)",
        r"\1\n\n\2",
        text,
    )
    # **Background to the CEFR levels** The six-level… → heading then paragraph
    text = re.sub(
        r"(\*\*Background to the CEFR levels\*\*)\s+(?=[A-Z])",
        r"\1\n\n",
        text,
    )
    # **Defining curriculum aims…** Step/following prose
    text = re.sub(
        r"(\*\*Defining curriculum aims from a needs profile\*\*)\s+",
        r"\1\n\n",
        text,
    )
    text = re.sub(
        r"(\*\*An alternative approach is to:\*\*)\s*",
        r"\1\n\n",
        text,
    )
    # **Phase**: paragraphs that should break before next **Phase**
    text = re.sub(
        r"(\.)\s+(\*\*(?:Qualitative|Quantitative) phase\*\*:)",
        r"\1\n\n\2",
        text,
    )
    text = re.sub(
        r"(\*\*(?:Qualitative|Quantitative) phase\*\*:)",
        r"\n\n\1",
        text,
    )
    return text


def _convert_bullet_lines(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        m = _BULLET_MARKERS.match(line)
        if m:
            rest = line[m.end() :].lstrip()
            out.append(f"{m.group(1)}- {rest}")
        else:
            out.append(line)
    return out


def _is_list_item_line(line: str) -> bool:
    s = line.strip()
    return bool(_LIST_ITEM.match(s) or _BULLET_MARKERS.match(s))


def _looks_like_list_continuation(prev: str, nxt: str) -> bool:
    """True when nxt is a soft-wrap tail of a bullet/list line (not a new paragraph)."""
    prev = prev.strip()
    nxt = nxt.strip()
    if not prev or not nxt:
        return False
    if _is_block_starter(nxt) or _is_list_item_line(nxt):
        return False
    if _is_page_comment(nxt) or _HEADING.match(nxt) or _TABLE_ROW.match(nxt):
        return False
    if _page_num_from_visible(nxt) and (
        nxt.startswith("*") or re.match(r"^Page\s+", nxt, re.I)
    ):
        return False
    # Clear new paragraph after finished sentence.
    if _SENTENCE_END.search(prev) and nxt[0].isupper() and len(nxt) > 45:
        return False
    # Soft wrap: lowercase start, or mid-phrase after incomplete bullet line.
    if nxt[0].islower():
        return True
    if not _SENTENCE_END.search(prev):
        return True
    return False


def _repair_list_blocks(lines: list[str]) -> list[str]:
    """Fold soft-wrapped bullet tails into one line; drop blank rows inside a list.

    Restores behaviour from the original standalone post-processing pass that
    produced tight ``- item`` runs without blank lines between items (see
    ``post-processing/CEFR_Companion_Volume_structured.md``).
    """
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        s = raw.strip()
        if not _is_list_item_line(s):
            out.append(raw)
            i += 1
            continue

        indent_m = re.match(r"^(\s*)", raw)
        indent = indent_m.group(1) if indent_m else ""
        # Normalize marker to markdown "-"
        m = _BULLET_MARKERS.match(s)
        if m:
            body = s[m.end() :].lstrip()
            item = f"{indent}- {body}"
        elif _LIST_ITEM.match(s):
            item = f"{indent}{s.lstrip()}"
        else:
            item = raw

        i += 1
        while i < n:
            # Skip blanks that sit between a bullet and its wrap / next bullet
            if not lines[i].strip():
                j = i + 1
                while j < n and not lines[j].strip():
                    j += 1
                if j >= n:
                    break
                peek = lines[j].strip()
                if _is_list_item_line(peek):
                    # blank between two list items — drop it
                    i = j
                    break
                if _looks_like_list_continuation(item, peek):
                    i = j
                    continue
                break
            nxt = lines[i].strip()
            if _is_list_item_line(nxt):
                break
            if _looks_like_list_continuation(item, nxt):
                item = f"{item.rstrip()} {nxt}"
                i += 1
                continue
            break
        out.append(item)
    return out


def _dedupe_consecutive_lines(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        if out and line == out[-1] and line.strip():
            continue
        out.append(line)
    return out


def _dedupe_page_comments(lines: list[str]) -> list[str]:
    """Remove consecutive duplicate <!-- page:N --> markers (from original standalone pass).

    Also collapses doubled caption+marker blocks:
    ``Page **N**\\n<!-- page:N -->\\nPage **N**\\n<!-- page:N -->`` → one pair.
    """
    out: list[str] = []
    page_comment_re = re.compile(r"^<!--\s*page:(\d+)\s*-->\s*$", re.I)
    page_caption_re = re.compile(
        r"^(?:\*?Page\s+\*\*\d+\*\*.*|\*?.+▶\s*Page\s+\*\*\d+\*\*.*)$",
        re.I,
    )
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        # Consecutive identical HTML page comments
        if (
            out
            and _is_page_comment(stripped)
            and _is_page_comment(out[-1].strip())
            and stripped.lower() == out[-1].strip().lower()
        ):
            i += 1
            continue
        # Doubled caption + comment for same page number
        m_cap = page_caption_re.match(stripped)
        m_com = (
            page_comment_re.match(lines[i + 1].strip())
            if i + 1 < len(lines)
            else None
        )
        if m_cap and m_com and len(out) >= 2:
            prev_com = page_comment_re.match(out[-1].strip())
            prev_cap = page_caption_re.match(out[-2].strip())
            if (
                prev_com
                and prev_cap
                and prev_com.group(1) == m_com.group(1)
            ):
                # Skip this duplicate pair
                i += 2
                continue
        out.append(line)
        i += 1
    return out


def _normalize_section_boundaries(lines: list[str]) -> list[str]:
    """Move section headings that appear before a page marker to after it (original pass)."""
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if (
            re.match(r"^###\s+\d+\.\d+\.", stripped)
            and i + 1 < len(lines)
            and _is_page_comment(lines[i + 1].strip())
        ):
            page_line = lines[i + 1]
            j = i + 2
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and re.match(r"^#{4,6}\s+\d+\.\d+\.\d+", lines[j].strip()):
                out.append(page_line)
                if out and out[-1] != "":
                    out.append("")
                out.append(line)
                out.append("")
                i = j
                continue
        out.append(line)
        i += 1
    return out


def _is_prose_line(line: str) -> bool:
    return bool(line.strip()) and not _is_block_starter(line)


def _ensure_paragraph_spacing(lines: list[str]) -> list[str]:
    """Blank line between consecutive prose paragraphs — never inside a bullet list."""
    out: list[str] = []
    in_code = False
    for line in lines:
        stripped = line.strip()
        if _FENCE.match(stripped):
            in_code = not in_code
            out.append(line)
            continue
        if in_code:
            out.append(line)
            continue
        if out and _is_page_comment(out[-1]) and _is_page_italic(line):
            out.append(line)
            continue
        if out and _BOLD_ONLY.match(out[-1].strip()) and (_NUMBERED_FOOTNOTE.match(stripped) or stripped):
            out.append("")
        # Do not insert blanks between list items or list → wrap (already repaired).
        if out and _is_list_item_line(out[-1]) and (_is_list_item_line(line) or not stripped):
            out.append(line)
            continue
        if out and _is_prose_line(out[-1]) and _is_prose_line(line):
            out.append("")
        out.append(line)
    return out


def _split_chapter_title_body(text: str) -> tuple[str, str]:
    text = text.strip()
    if not text:
        return "", ""
    if _CAPS_LINE.match(text) or text.isupper():
        return text, ""
    m = _PROSE_START.search(text)
    if m:
        title = text[: m.start()].strip()
        body = text[m.start() :].strip()
        if title and (_CAPS_LINE.match(title) or title.isupper()):
            return title, body
    return text, ""


def _is_chapter_opener_line(line: str) -> bool:
    s = line.strip().removeprefix("-").strip()
    if re.match(r"^CHAPTER\s+\d+:", s, re.I):
        return False
    m = re.match(r"^Chapter\s+(\d+)\s*(.*)$", s, re.I)
    if not m:
        return False
    rest = m.group(2).strip()
    if rest.startswith(":"):
        return False
    if not rest:
        return True
    return not re.search(r"[a-z]", rest)


def _format_chapter_openings(lines: list[str]) -> list[str]:
    """Turn 'Chapter N' + ALL-CAPS title + body into structured chapter blocks."""
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not _is_chapter_opener_line(line):
            out.append(line)
            i += 1
            continue

        s = line.strip().removeprefix("-").strip()
        m = re.match(r"^Chapter\s+(\d+)\s*(.*)$", s, re.I)
        num = m.group(1)
        remainder = m.group(2).strip()

        title_parts: list[str] = []
        body = ""
        j = i + 1

        if remainder:
            title, body = _split_chapter_title_body(remainder)
            if title:
                title_parts.append(title)

        while not title_parts or (not body and j < len(lines)):
            if j >= len(lines):
                break
            ns = lines[j].strip()
            if not ns:
                j += 1
                continue
            if _is_page_comment(ns) or _HTML_COMMENT.match(ns):
                break
            if _HEADING.match(ns) or _FENCE.match(ns):
                break
            title, maybe_body = _split_chapter_title_body(ns)
            if not title or not (_CAPS_LINE.match(title) or title.isupper()):
                break
            title_parts.append(title)
            j += 1
            if maybe_body:
                body = maybe_body
                break

        if out and out[-1] != "":
            out.append("")
        out.append(f"## Chapter {num}")
        title = " ".join(title_parts)
        if title:
            out.append(title)
            out.append("")
        if body:
            out.append(body)
        i = j
    return out


def _format_page_blocks(lines: list[str]) -> list[str]:
    """Keep page caption + ``<!-- page:N -->`` together (caption first); blank lines around."""
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        s = line.strip()

        # Already caption-then-comment (preferred)
        vnum = _page_num_from_visible(s) if s else None
        if vnum and (s.startswith("*") or re.match(r"^Page\s+", s, re.I)):
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j < n and _is_page_comment(lines[j]):
                html = lines[j].strip()
                m = _PAGE_HTML.match(html)
                if m and m.group(1) == vnum:
                    if out and out[-1] != "":
                        out.append("")
                    out.append(s)
                    out.append("")
                    out.append(html)
                    j += 1
                    if j < n:
                        out.append("")
                    i = j
                    continue

        if not _is_page_comment(line):
            out.append(line)
            i += 1
            continue

        # Comment first — pull following caption above it
        m = _PAGE_HTML.match(s)
        page_num = m.group(1) if m else None
        j = i + 1
        while j < n and not lines[j].strip():
            j += 1
        caption: str | None = None
        if j < n and page_num:
            vs = lines[j].strip()
            if _page_num_from_visible(vs) == page_num:
                caption = vs
                j += 1
        if out and out[-1] != "":
            out.append("")
        if caption:
            out.append(caption)
            out.append("")
        out.append(s)
        if j < n:
            out.append("")
        i = j

    return out


def _collapse_blank_lines(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def _split_midline_list_runs(text: str) -> str:
    """Second pass: split remaining ``- item; f item`` runs after other fixes."""
    lines = text.splitlines()
    out: list[str] = []
    for line in lines:
        s = line.strip()
        if s.startswith("- ") and re.search(r";\s+(?:f|-)\s+[A-Za-z]", s):
            # Split entire line on mid-line bullet markers into multiple list items.
            body = s[2:]
            parts = re.split(
                r";\s+(?:f|-)\s+|(?<![;\-])\s+f\s+(?=[A-Za-z“\"'(\[])",
                body,
            )
            for part in parts:
                part = part.strip().rstrip(";")
                if not part:
                    continue
                out.append(f"- {part}")
            continue
        out.append(line)
    return "\n".join(out)


def _join_mid_bold_and_section_wraps(text: str) -> str:
    """Rejoin false paragraph splits from mid-bold wraps and section numbers.

    Examples (Ch2 QA): ``under various\\n\\n**constraints**``;
    ``Sections\\n\\n5.1.1.3``; ``**Step 1**:`` glued runs.
    """
    # word + blank + **continuation** (lowercase after bold open)
    text = re.sub(
        r"([a-z,;:%0-9])\n\n(\*\*[a-z])",
        r"\1 \2",
        text,
    )
    # **word** + blank + continuation lowercase mid-sentence
    text = re.sub(
        r"(\*\*[^*]+\*\*)\n\n([a-z])",
        r"\1 \2",
        text,
    )
    # "Sections" / "Chapter" then numbered ref split across blank
    text = re.sub(
        r"\b(Sections?|Chapters?|Appendix)\n\n(\d+(?:\.\d+)+)",
        r"\1 \2",
        text,
        flags=re.I,
    )
    # Step headings that should stand alone
    text = re.sub(
        r"([^\n])\n(\*\*Step\s+\d+\*\*:)",
        r"\1\n\n\2",
        text,
    )
    text = re.sub(
        r"(\*\*Step\s+\d+\*\*:[^\n]+)\n(?!\n)(\*\*Step\s+\d+\*\*:)",
        r"\1\n\n\2",
        text,
    )
    return text


_SECTION_31_LEAD = (
    "Reception involves receiving and processing input: activating what are "
    "thought to be appropriate schemata in order to build up a representation "
    "of the meaning being expressed and a hypothesis as to the communicative "
    "intention behind it. Incoming co-textual and contextual cues are checked "
    "to see if they “fit” the activated schema – or suggest that an alternative "
    "hypothesis is necessary. In “oral reception”, the language user receives "
    "and processes live or recorded input produced by one or more other people. "
    "In “visual reception” (reading and watching) activities the user receives "
    "and processes as input written and signed texts produced by one or more "
    "people. In “audio-visual comprehension”, for which one scale (watching TV "
    "and film) is provided, the user watches TV, video or a film and uses "
    "multimedia, with or without subtitles, voiceovers or signing."
)


def _ensure_section_31_after_figure_11(text: str) -> str:
    """TEMPORARY safety net: restore ``### 3.1 RECEPTION`` after Figure 11 (log 04 #10).

    Prefer extract RO trailing heading on p.47 long-term; this masks extract
    regressions if over-relied on. Golden V-ADJ-SECTION-AFTER-FIG still required.
    Do not treat TOC lines like ``### 3.1. RECEPTION — 47`` as the body heading.
    Also dedupe duplicate 3.1 headings / lead blocks (replace, don't layer).
    """
    # Dedupe: multiple body-form ### 3.1 RECEPTION (not TOC em-dash) → keep first
    body_h = re.compile(r"^###\s*3\.1\.?\s*RECEPTION\s*$", re.M | re.I)
    matches = list(body_h.finditer(text))
    if len(matches) > 1:
        # Keep first; remove subsequent bare headings (and immediate duplicate lead)
        for m in reversed(matches[1:]):
            end = m.end()
            # Drop following blank + lead if it's the known lead starting again
            rest = text[end:]
            drop = re.match(
                r"\n+(?:Reception involves receiving[\s\S]{0,900}?signing\.)?\n*",
                rest,
                re.I,
            )
            if drop:
                text = text[: m.start()] + text[end + drop.end() :]
            else:
                text = text[: m.start()] + text[end:]

    # Body already has heading + lead (not TOC em-dash page form)
    if re.search(
        r"###\s*3\.1\.?\s*RECEPTION\s*\n+\s*Reception involves receiving",
        text,
        re.I,
    ):
        return text

    _f = chr(96) * 3
    pat = re.compile(
        r"(<!--\s*db:id=figure_11_[^>]+-->\s*\n###[^\n]+\n+"
        + re.escape(_f)
        + r"text\n[\s\S]*?\n"
        + re.escape(_f)
        + r"\s*)",
        re.I,
    )
    m = pat.search(text)
    if not m:
        return text
    insert = "\n### 3.1 RECEPTION\n\n" + _SECTION_31_LEAD + "\n"
    return text[: m.end()] + insert + text[m.end() :]


def _dedupe_callout_title_lines(text: str) -> str:
    """Remove unbolded / glued duplicate callout title after ``> **Title**`` (log 04 #3–4)."""
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        m = re.match(r"^>\s*\*\*(.+?)\*\*\s*$", line.strip())
        if m:
            title = m.group(1).strip()
            title_plain = re.sub(r"^[“\"]|[”\"]$", "", title).strip()
            j = i + 1
            while j < len(lines) and lines[j].strip() in (">", ""):
                out.append(lines[j])
                j += 1
            if j < len(lines):
                raw = lines[j]
                plain = re.sub(r"^>\s*", "", raw.strip())
                plain_unbold = plain.strip("*").strip()
                # Exact duplicate title line
                if plain_unbold.lower() == title.lower() or plain_unbold.lower() == title_plain.lower():
                    j += 1
                # Title glued onto start of body paragraph
                elif plain_unbold.lower().startswith(title_plain.lower()):
                    rest = plain_unbold[len(title_plain) :].lstrip(" :–-")
                    if rest:
                        out.append("> " + rest)
                    j += 1
            i = j
            continue
        i += 1
    return "\n".join(out)


def _resync_page_captions_from_pdf(text: str) -> str:
    """Rewrite visible page captions from the PDF running head (log 07 odd pages).

    Fixes MD that collapsed to bare ``Page **N**`` while the PDF still has
    chapter form (e.g. Key aspects… ▶ Page 29). Uses the same normalizer as
    extract so bold markers around page numbers do not drop the title.
    """
    try:
        import fitz

        from pipeline.config import PDF_PATH
        from pipeline.page_layout import (
            _normalize_page_marker_caption,
            classify_page_zones,
        )
    except Exception:  # noqa: BLE001
        return text

    if not PDF_PATH or not Path(PDF_PATH).exists():
        return text

    doc = fitz.open(str(PDF_PATH))
    lines = text.splitlines()
    n = len(lines)
    i = 0
    while i < n:
        m = re.match(r"^<!--\s*page:(\d+)\s*-->$", lines[i].strip())
        if not m:
            i += 1
            continue
        pn = int(m.group(1))
        if pn < 1 or pn > doc.page_count:
            i += 1
            continue
        j = i - 1
        while j >= 0 and not lines[j].strip():
            j -= 1
        if j < 0:
            i += 1
            continue
        cap = lines[j].strip()
        if not re.search(r"Page\s+\*?\*?\d+", cap, re.I) and not re.search(
            r"page:\s*\d+", cap, re.I
        ):
            # still a caption candidate if it looks like italic page chrome
            if "▶" not in cap and "Page" not in cap:
                i += 1
                continue
        try:
            zones = classify_page_zones(doc[pn - 1])
            markers = zones.get("page_markers") or []
            if not markers:
                i += 1
                continue
            correct = _normalize_page_marker_caption(markers[-1], pn)
            if correct and correct != lines[j].strip():
                lines[j] = correct
        except Exception:  # noqa: BLE001
            pass
        i += 1
    doc.close()
    return "\n".join(lines)


def _ensure_blank_before_page_captions(text: str) -> str:
    """Force a blank line before ``Page **N**`` captions (adjacent-element guard).

    Fixes log 04: footnote or body glued onto the same line / no gap before page number.
    L05-PAGE-AST: do **not** split markdown italic captions (``*Page…``) or chapter
    running heads (``… ▶ Page **N**``).
    """
    # Rejoin orphan italic opener created by older bad splits: "*\n\nPage **N**"
    text = re.sub(
        r"(?m)^\*\s*\n+(Page\s+\*\*\d+\*\*)",
        r"*\1",
        text,
    )
    # Rejoin chapter running head broken across lines: "… ▶\n\nPage **N**"
    text = re.sub(
        r"(▶)\s*\n+\s*(Page\s+\*\*\d+\*\*)",
        r"\1 \2",
        text,
    )
    # Same-line glue: "...url. Page **27**" — never break ``*Page`` or ``▶ Page``
    text = re.sub(
        r"([^\n*▶])([ \t]+)(Page\s+\*\*\d+\*\*)",
        r"\1\n\n\3",
        text,
    )
    # Sentence end immediately before Page (footnote glue)
    text = re.sub(
        r"([.!?\)\]\"'])(Page\s+\*\*\d+\*\*)",
        r"\1\n\n\2",
        text,
    )
    # Previous non-empty line immediately followed by bare Page caption —
    # skip when previous line is a chapter running-head fragment ending in ▶
    text = re.sub(
        r"([^\n▶])\n(Page\s+\*\*\d+\*\*)",
        r"\1\n\n\2",
        text,
    )
    # Collapse 3+ blanks to 2
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text


def _table_title_near_header(text: str, header_end: int) -> str | None:
    """First meaningful title cell in a markdown table shortly after a scale header.

    Does not modify the table — read-only. Used to re-derive artifact ids from
    already-correct table titles when the ### header / db:id is still garbled.
    """
    window = text[header_end : header_end + 1200]
    for line in window.splitlines()[:25]:
        s = line.strip()
        if not s.startswith("|"):
            if s.startswith("### ") or s.startswith("<!-- el:end") or s.startswith("<!-- db:id"):
                break
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        for c in cells:
            if not c or re.match(r"^:?-+:?$", c):
                continue
            if re.match(r"^(Pre-)?[ABC][12]\+?$", c, re.I):
                continue
            if len(c) < 8 or not re.search(r"[A-Za-z]{4,}", c):
                continue
            # Prefer cells that look like scale titles (not long descriptor rows)
            if len(c) > 180:
                continue
            if c.lower().startswith("can "):
                continue
            return re.sub(r"\s+", " ", c)
    return None


def _resync_artifact_ids_from_fixed_titles(text: str) -> str:
    """Re-derive scale/table artifact ids from fixed display titles (RIE-005).

    Policy:
    - Prefer the corrected ### title (token-fix / reverse-fix).
    - If the nearby markdown table already has a cleaner title row, use that
      for the display name and slug (table body left unchanged).
    - Replace old ids globally (db:id, el:start/end, ### | id) so references match.
    - Does not touch figure_* ids or rotated_from_grok file contents.
    """
    from pipeline.title_fix import (
        artifact_id_from_title,
        preferred_display_title,
        title_readability_score,
    )

    header_re = re.compile(
        r"^(### )(.+?)( \| )((?:scale|table)_[a-z0-9_]+)(\s*)$",
        re.M,
    )
    id_map: dict[str, str] = {}
    title_map: list[tuple[str, str, str]] = []  # old_id, old_title, new_title

    for m in header_re.finditer(text):
        old_title = m.group(2).strip()
        old_id = m.group(4)
        prefix = "scale" if old_id.startswith("scale_") else "table"
        table_title = _table_title_near_header(text, m.end())
        new_title = preferred_display_title(old_title, table_title)
        new_id = artifact_id_from_title(new_title, prefix=prefix)
        if not new_id or new_id in ("scale_", "table_", "scale", "table"):
            continue
        # Only rewrite when id changes or title was fixed
        if new_id == old_id and new_title == old_title:
            continue
        # Safety: do not replace with a worse id (more reverse-looking)
        old_score = title_readability_score(old_id.replace("_", " "))
        new_score = title_readability_score(new_id.replace("_", " "))
        if new_id != old_id and new_score + 0.02 < old_score:
            continue
        if new_id != old_id:
            # Avoid collapsing two different scales onto one id accidentally:
            # if new_id already exists as a *different* header, skip id change
            # unless old_id is clearly garbled (contains known reverse tokens).
            from pipeline.title_fix import GARBLED_ID_MARKERS, id_looks_garbled

            garbled_bits = GARBLED_ID_MARKERS + (
                "nettirw",
                "nialpxe",
                "ssenetairporppa",
                "larutluc",
                "erutcurts",
                "stpecnoc",
                "_wen_",
                "ot_nialpxe",
            )
            if (
                id_looks_garbled(old_id)
                or any(b in old_id for b in garbled_bits)
                or new_score > old_score + 0.05
            ):
                id_map[old_id] = new_id
        if new_title != old_title:
            title_map.append((old_id, old_title, new_title))

    # Apply title line rewrites first (using current ids before global id replace)
    for old_id, old_title, new_title in title_map:
        text = text.replace(
            f"### {old_title} | {old_id}",
            f"### {new_title} | {old_id}",
        )
        # db:id blocks do not embed the display title in the comment

    # Global id remap (longest first to avoid partial collisions)
    for old_id, new_id in sorted(id_map.items(), key=lambda kv: -len(kv[0])):
        if old_id == new_id:
            continue
        text = text.replace(old_id, new_id)

    return text


def _repair_log05_markdown(text: str) -> str:
    """Targeted repairs for log 05/06 visual QA (safe, non-adjacent-damaging)."""
    from pipeline.utils import repair_glued_footnotes, sanitize_urls_in_text

    text = sanitize_urls_in_text(text)
    text = repair_glued_footnotes(text)

    # L06 p.27: footnote URL split — trailing hex digit became ``\n1.``
    # ObjectId …2fb + ``1.`` → full id …2fb1. (period is end punctuation)
    text = re.sub(
        r"(https?://[^\s\)\]<>\"']*?[0-9a-fA-F])\n(\d)\.\s*(?=\n|$)",
        r"\1\2.",
        text,
    )

    # L06 p.36/38: section headings glued onto prior paragraph (2nd report of 2.7)
    # "...3). **2.7. CEFR PROFILES**" or "...context. **2.6. THE CEFR…**"
    text = re.sub(
        r"([.!?\)])\s+\*\*(2\.\d+\.\s+[A-Z][A-Z0-9 ,:–\-/&()]+)\*\*",
        r"\1\n\n### \2\n",
        text,
    )
    text = re.sub(
        r"(?m)^\*\*(2\.\d+\.\s+[A-Z][A-Z0-9 ,:–\-/&()]+)\*\*\s*$",
        r"### \1",
        text,
    )

    # L05-P27-SPLIT: rejoin prose fences that split mid-sentence (next starts lowercase).
    # Drop the closing fence of the prior block and the opening fence of the next so the
    # continuation stays inside the prior prose element; keep the full continuation text.
    text = re.sub(
        r"<!-- el:end id=prose_\S+ -->\s*\n+"
        r"<!-- el:start type=prose id=\S+ page=\d+ -->\s*\n+"
        r"([a-zà-öø-ÿ].*)",
        r"\1",
        text,
    )
    # Repair botched earlier join that ate the leading "c" of "cohesion"
    text = re.sub(
        r"(citizenship,\s*social)\s*\n+(?:<!-- el:start type=prose[^>]+-->)?ohesion\b",
        r"\1 cohesion",
        text,
    )
    text = re.sub(r"(?m)^(<!-- el:start type=prose[^>]+-->)ohesion\b", r"\1\ncohesion", text)
    text = text.replace(" social cohesion", " social cohesion")  # no-op anchor
    if "ohesion and intercultural" in text and "cohesion and intercultural" not in text[
        max(0, text.find("ohesion") - 5) : text.find("ohesion") + 40
    ]:
        text = text.replace("ohesion and intercultural", "cohesion and intercultural", 1)

    # L05-P29-CH: join soft-wrapped chapter title lines inside blockquotes
    # e.g. ``> *Chapter 4: Language use and the*\n>\n> language user/learner``
    text = re.sub(
        r"(?m)^(>\s*\*Chapter\s+\d+:[^*]*?)\*\s*\n>\s*\n>\s+([a-z][^\n*]+)\s*$",
        r"\1 \2*",
        text,
    )
    # Same without italics on continuation
    text = re.sub(
        r"(?m)^(>\s*\*Chapter\s+\d+:[^*]*?)\s*\n>\s*\n>\s+([a-z][^\n]+)\s*$",
        lambda m: (
            m.group(1).rstrip("*").rstrip()
            + " "
            + m.group(2).strip().strip("*")
            + ("*" if m.group(1).rstrip().endswith("*") or "*" in m.group(1) else "")
        ),
        text,
    )
    # Cleaner second pass for chapter soft-wraps (continuation not italic)
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(>\s*)(\*?Chapter\s+\d+:.+)(\*?)\s*$", line.strip() and line or line)
        # Use raw line
        m = re.match(r"^(>\s*)(\*?)(Chapter\s+\d+:.*?)(\*?)\s*$", line)
        if m and i + 2 < len(lines):
            blank_q = lines[i + 1].strip() in (">", "")
            cont = lines[i + 2]
            mc = re.match(r"^>\s+([a-z].+?)\s*$", cont)
            # Allow ``> language…`` or ``> *language…*``
            mc = re.match(r"^>\s+\*?([a-z][^<*\n]+?)\*?\s*$", cont)
            if blank_q and mc and "Chapter" not in cont:
                prefix, ital_o, body, ital_c = m.group(1), m.group(2), m.group(3), m.group(4)
                joined = f"{prefix}{ital_o}{body.rstrip()} {mc.group(1).strip()}{ital_c or ital_o}"
                # Prefer closed italics when chapter titles were italic
                if ital_o == "*" and not joined.rstrip().endswith("*"):
                    joined = joined.rstrip() + "*"
                out.append(joined)
                i += 3
                continue
        out.append(line)
        i += 1
    text = "\n".join(out)

    # L05-P27-CO: Background to the CEFR callout → 3 paragraphs (user exact splits)
    text = re.sub(
        r"(> \*\*Background to the CEFR\*\*\n>\n> )"
        r"(The CEFR was developed as a continuation of the Council of Europe’s work in language education during the 1970s and 1980s\. "
        r"The CEFR “action-oriented approach” builds on and goes beyond the communicative approach proposed in the mid-1970s in the publication “The Threshold Level”, the first functional/ notional specification of language needs\. )"
        r"(The CEFR and the related European Language Portfolio \(ELP\) that accompanied it were recommended by an intergovernmental symposium held in Switzerland in 1991\. "
        r"As its subtitle suggests, the CEFR is concerned principally with learning and teaching\. "
        r"It aims to facilitate transparency and coherence between the curriculum, teaching and assessment within an institution and transparency and coherence between institutions, educational sectors, regions and countries\. )"
        r"(The CEFR was piloted in provisional versions in 1996 and 1998 before being published in English \(Cambridge University Press\)\.)",
        r"\1\2\n>\n> \3\n>\n> \4",
        text,
        count=1,
    )

    # L05-P35-CO: Can-do callout → 2 paragraphs after “achievement.”
    text = re.sub(
        r"(> The idea of scientifically calibrating “can do” descriptors to a scale of levels comes originally from the field of professional training for nurses\. "
        r"Tests were not very helpful in assessing a trainee nurse’s competence; what was needed was a systematic, informed observation by an expert nurse, guided by short descriptions of typical nursing competence at different levels of achievement\. )"
        r"(This “can do” approach was transferred)",
        r"\1\n>\n> \2",
        text,
        count=1,
    )

    # L05-P37: Level C2 quote on its own paragraph
    text = re.sub(
        r"(is introduced in the CEFR as follows:)\s+(\*\*Level C2\*\*)",
        r"\1\n\n\2",
        text,
    )
    # L05-P37: list glue after "beginners:"
    text = re.sub(
        r"(useful objectives for beginners:)\s+(-\s+can make)",
        r"\1\n\2",
        text,
    )
    # L05-P37: callout title "Background to the CEFR" + body "levels" → full title
    text = re.sub(
        r"(> \*\*Background to the CEFR\*\*\n>\n> )\s*levels\s*\n>",
        r"> **Background to the CEFR levels**\n>",
        text,
    )

    # L05-P32-LINK: move Guide URL off "language classroom" onto the Guide title
    guide_url = "https://rm.coe.int/16806ae621"
    text = re.sub(
        rf"(tasks in the language classroom)\s*\({re.escape(guide_url)}\)",
        r"\1",
        text,
    )
    # Attach URL after every Guide title that does not already have it within ~80 chars
    guide_title_re = re.compile(
        r"\*\*Guide for the development and implementation of curricula for "
        r"plurilingual and intercultural education\*\*"
        r"|Guide for the development and implementation of curricula for "
        r"plurilingual and intercultural education(?!\*\*)",
        re.I,
    )
    pieces: list[str] = []
    last = 0
    for m in guide_title_re.finditer(text):
        pieces.append(text[last : m.end()])
        after = text[m.end() : m.end() + 90]
        if "16806ae621" not in after and not after.lstrip().startswith("(http"):
            pieces.append(f" ({guide_url})")
        last = m.end()
    pieces.append(text[last:])
    text = "".join(pieces)

    # L05-P41-URL: Section 3.7 missing parenthetical URL (same base as 3.8)
    text = re.sub(
        r"(CEFR 2001 Section 3\.7)(?!\s*\(https?://)",
        r"\1 (https://rm.coe.int/1680459f97#page=36)",
        text,
    )

    # L05-PAGE-AST (running head form): Chapter 2 odd pages use chapter title, not book title.
    # Keep Page and number on the SAME line as the chapter title (never "▶\nPage").
    def _chapter2_caption(n: int) -> str:
        return (
            f"*Key aspects of the CEFR for teaching and learning ▶ Page **{n}***"
        )

    def _page_caption_fix(m: re.Match) -> str:
        n = int(m.group(1))
        if n in range(29, 46, 2):
            return _chapter2_caption(n)
        if n == 25:
            return f"**Introduction** Page **{n}**"
        if n in (27, 47):
            return f"Page **{n}**"
        return m.group(0)

    text = re.sub(
        r"\*Page\s+\*\*(\d+)\*\*\s*▶\s*\*\*CEFR\s*[–-]\s*Companion volume\*\*\*",
        _page_caption_fix,
        text,
    )
    text = re.sub(
        r"(?<!\*)Page\s+\*\*(\d+)\*\*\s*▶\s*\*\*CEFR\s*[–-]\s*Companion volume\*\*",
        lambda m: _page_caption_fix(m)
        if int(m.group(1)) in range(29, 46, 2)
        else m.group(0),
        text,
    )
    # Repair already-broken chapter captions from earlier bad passes (multi-line mess)
    text = re.sub(
        r"\*+\s*\n+\s*\*Key aspects of the CEFR for teaching and learning ▶\s*\n+"
        r"\s*Page\s+\*\*\s*(\d+)\s*(?:\*{0,3})?\s*\n+"
        r"(?:Page\s+\*\*\1\*\*\s*)?(<!--\s*page:\1\s*-->)?",
        lambda m: _chapter2_caption(int(m.group(1)))
        + ("\n\n" + m.group(2) if m.group(2) else ""),
        text,
    )
    text = re.sub(
        r"\*Key aspects of the CEFR for teaching and learning ▶\s*\n+"
        r"\s*Page\s+\*\*\s*(\d+)\s*(?:\*{0,3})?\s*\n+"
        r"(?:Page\s+\*\*\1\*\*\s*)?(<!--\s*page:\1\s*-->)?",
        lambda m: _chapter2_caption(int(m.group(1)))
        + ("\n\n" + m.group(2) if m.group(2) else ""),
        text,
    )
    # Collapse "Page **N**<!-- page:N -->" glued forms
    text = re.sub(
        r"Page\s+\*\*(\d+)\*\*\s*(<!--\s*page:\1\s*-->)",
        r"Page **\1**\n\n\2",
        text,
    )
    # Drop leftover orphan single-asterisk lines before captions
    text = re.sub(r"(?m)^\*\s*\n+(?=[\*P])", "", text)
    # Trailing junk after chapter running heads: ``…Page **41*** **``
    text = re.sub(
        r"(\*Key aspects of the CEFR for teaching and learning ▶ Page \*\*\d+\*\*\*)\s+\*\*",
        r"\1",
        text,
    )

    # L05-P38-A2: convert prose A2 sample into the user-specified markdown table
    # log 04 #7.6: header row Level | Illustrative Descriptors
    a2_table = (
        "| Level | Illustrative Descriptors |\n"
        "| --- | --- |\n"
        "| A2 | Can understand enough to be able to meet needs of a concrete type, "
        "provided people articulate clearly and slowly. |\n"
        "| | Can understand phrases and expressions related to areas of most immediate priority "
        "(e.g. very basic personal and family information, shopping, local geography, employment), "
        "provided people articulate clearly and slowly. |"
    )
    a2_prose = re.compile(
        r"Can understand enough to be able to meet needs of a concrete type, provided people articulate clearly and slowly\.\s*\n\n"
        r"\*\*A2\*\*\s+Can understand phrases and expressions related to areas of most immediate priority "
        r"\(e\.g\. very basic personal and family information, shopping, local geography, employment\), "
        r"provided people articulate clearly and slowly\.\s*",
        re.M,
    )
    if a2_prose.search(text):
        text = a2_prose.sub(a2_table + "\n\n", text, count=1)
    # Upgrade older A2 sample table (no header) to Level | Illustrative Descriptors
    old_a2 = (
        "| A2 | Can understand enough to be able to meet needs of a concrete type, "
        "provided people articulate clearly and slowly. |\n"
        "| --- | --- |\n"
        "| | Can understand phrases and expressions related to areas of most immediate priority "
        "(e.g. very basic personal and family information, shopping, local geography, employment), "
        "provided people articulate clearly and slowly. |"
    )
    if old_a2 in text and a2_table not in text:
        text = text.replace(old_a2, a2_table, 1)
    # Ensure blank line after A2 sample table before following prose
    text = re.sub(
        r"(\| \| Can understand phrases and expressions related to areas of most immediate priority[^\n]+\|)\n(Plus levels)",
        r"\1\n\n\2",
        text,
    )
    # Deduplicate identical A2 sample tables
    while text.count(a2_table) > 1:
        first = text.find(a2_table)
        second = text.find(a2_table, first + len(a2_table))
        if second < 0:
            break
        text = text[:second] + text[second + len(a2_table) :].lstrip("\n")

    # L07 p.41: prose purity — split before "As a user, you are invited"
    text = re.sub(
        r"(not in any way mandatory\.)\s+(As a user, you are invited)",
        r"\1\n\n\2",
        text,
    )

    # L07 p.42/43: callout "Step N:" collapsed onto one line → multi-line blockquote
    def _expand_step_callout(m: re.Match) -> str:
        block = m.group(0)
        # Only operate inside a single-line-ish callout body
        body = re.sub(r"^>\s*", "", block, flags=re.M)
        body = re.sub(r"\s+", " ", body).strip()
        # Split before Step 2..N (keep Step 1 with lead)
        parts = re.split(r"\s+(?=Step\s+[2-9]\s*:)", body)
        if len(parts) < 2:
            # Try Step 1: as first break from title lead
            m1 = re.match(
                r"^(.*?)(Step\s+1\s*:.*)$",
                body,
                re.I | re.S,
            )
            if m1 and m1.group(1).strip():
                lead = m1.group(1).strip()
                rest = m1.group(2).strip()
                steps = re.split(r"\s+(?=Step\s+\d+\s*:)", rest)
                lines = [f"> {lead}", ">"]
                for s in steps:
                    lines.append(f"> {s.strip()}")
                    lines.append(">")
                while lines and lines[-1] == ">":
                    lines.pop()
                return "\n".join(lines)
            return block
        lines: list[str] = []
        for i, p in enumerate(parts):
            p = p.strip()
            if not p:
                continue
            lines.append(f"> {p}")
            lines.append(">")
        while lines and lines[-1] == ">":
            lines.pop()
        return "\n".join(lines)

    # Apply to blockquote regions that contain "Step 1:" and "Step 2:"
    text = re.sub(
        r"(?m)^>(?!\|)(?! \*\*).*(?:Step\s+1\s*:).*(?:Step\s+2\s*:).*$",
        _expand_step_callout,
        text,
    )
    # Title + Step 1 still on one line after multi-step expand
    text = re.sub(
        r"(?m)^(>\s*)((?:Defining curriculum aims from a needs profile|An alternative approach is to:))\s+"
        r"(Step\s+1\s*:.*)$",
        lambda m: (
            f"> **{m.group(2).rstrip(':').strip()}**\n>\n> {m.group(3).strip()}"
            if not m.group(2).startswith("An alternative")
            else f"> {m.group(2).strip()}\n>\n> {m.group(3).strip()}"
        ),
        text,
    )

    # L07 p.43: restore missing lead "Very often, CEFR descriptors..."
    text = re.sub(
        r"(?m)^(course\. In such a case, descriptors from particular scales)",
        r"Very often, CEFR descriptors are referred to for inspiration in adapting or making explicit the aims of an existing course. In such a case, descriptors from particular scales",
        text,
    )

    # L07 p.43: split footnote 2 "The former" onto next paragraph after Chapter 5.
    text = re.sub(
        r"(located in Chapter 5\.)\s+(The former are very suitable)",
        r"\1\n\n\2",
        text,
    )
    text = re.sub(
        r"(action-oriented approach\. \(CEFR 2001 Section 9\.2\.2\))\s+(The latter, descriptors)",
        r"\1\n\n\2",
        text,
    )

    # L07 p.38: drop duplicate A2 sample table under figure (any table shape under PNG)
    text = re.sub(
        r"(figure_06_fictional_profile_clil\.png\)\s*\n)"
        r"((?:\|[^\n]+\|\s*\n){2,6})"
        r"(<!-- el:end id=figure_06_fictional_profile_clil -->)",
        r"\1\3",
        text,
        count=1,
    )
    # legacy pattern (header row Level | Illustrative…)
    text = re.sub(
        r"(figure_06_fictional_profile_clil\.png\)\s*\n)"
        r"(\| Level \| Illustrative Descriptors \|[\s\S]*?\n\| \| Can understand phrases[^\n]+\|\s*\n)",
        r"\1",
        text,
        count=1,
    )

    # Guide title: collapse mid-title / doubled URL injects to clean **title** (url)
    _guide_clean = (
        "**Guide for the development and implementation of curricula for "
        "plurilingual and intercultural education** (https://rm.coe.int/16806ae621)"
    )
    text = re.sub(
        r"\*\*Guide for the development\s+and\s+implementation of curricula for "
        r"plurilingual(?:\s*\(https://rm\.coe\.int/16806ae621\))?\s*"
        r"(?:and\s*(?:\(https://rm\.coe\.int/16806ae621\)\s*)?)?"
        r"intercultural(?:\s*\(https://rm\.coe\.int/16806ae621\))?\s*education\*\*"
        r"(?:\s*\(https://rm\.coe\.int/16806ae621\))?",
        _guide_clean,
        text,
        flags=re.I,
    )
    # List glue: URL);N** f **Next title → URL).\n\n- **Next title
    text = re.sub(
        r"(\(https://rm\.coe\.int/16806ae621\));(\d+)\*\*\s*f\s*\*\*",
        r"\1).\2\n\n- **",
        text,
    )
    text = re.sub(
        r"(\(https://rm\.coe\.int/16806af387\));(\d+)\*\*\s*f\s*\*\*",
        r"\1).\2\n\n- **",
        text,
    )

    # p.29: restore missing footnote 26 (RELANG) after fn 25 when body cites it
    if "RELANG" in text and not re.search(r"(?m)^26\.\s", text):
        fn26 = (
            "26. Relating language curricula, tests and examinations to the Common "
            "European Framework of Reference (RELANG): https://relang.ecml.at/."
        )
        text2, n = re.subn(
            r"(PublicationID/67/Default\.aspx\.)\s*\n",
            rf"\1\n{fn26}\n",
            text,
            count=1,
        )
        if n:
            text = text2
        else:
            # Fallback: after any fn 25 line that mentions Highlights from the Manual
            text = re.sub(
                r"(?m)^(25\.\s+.*Highlights from the Manual.*)$",
                rf"\1\n{fn26}",
                text,
                count=1,
            )

    # L07: garbled reversed tokens in artifact ids / captions (span title bugs)
    # Token map first; then re-derive ids from fixed titles (RIE-005 / user 2026-07-20).
    _GARBLED = {
        "cfiiceps": "specific",
        "smargaid": "diagrams",
        "shparg": "graphs",
        "atad": "data",
        "gnittup": "putting",
        "cilbup": "public",
        "noitacilbup": "publication",
        "nettirw": "written",
        "nialpxe": "explain",
        "ssenetairporppa": "appropriateness",
        "larutluc": "cultural",
        "erutcurts": "structure",
        "stpecnoc": "concepts",
        "cte_smargaid_shparg_ni_atad_explaining": "scale_explaining_data_in_graphs_and_diagrams",
        "scale_cte_smargaid_shparg_ni_atad_explaining": "scale_explaining_data_in_graphs_and_diagrams",
        "scale_relaying_cfiiceps_information": "scale_relaying_specific_information",
        "Relaying cfiiceps information": "Relaying specific information",
        "ni_atad": "data_in",
        "collaborating_ni_a_group": "collaborating_in_a_group",
        "scale_collaborating_ni_a_group": "scale_collaborating_in_a_group",
        "Collaborating ni a group": "Collaborating in a group",
        "scale_sustained_monologue_gnittup_a_case_e_g_in_a_debate": (
            "scale_sustained_monologue_putting_a_case_e_g_in_a_debate"
        ),
        "scale_cilbup_announcements": "scale_public_announcements",
        "Sustained monologue: gnittup a case": "Sustained monologue: putting a case",
        "scale_translating_a_nettirw_text": "scale_translating_a_written_text",
        "Translating a nettirw text": "Translating a written text",
        "scale_strategies_ot_nialpxe_a_wen_concept": "scale_strategies_to_explain_a_new_concept",
        "Strategies ot nialpxe a wen concept": "Strategies to explain a new concept",
        "scale_sociolinguistic_ssenetairporppa_and_larutluc_repertoire": (
            "scale_sociolinguistic_appropriateness_and_cultural_repertoire"
        ),
        "Sociolinguistic ssenetairporppa and larutluc repertoire": (
            "Sociolinguistic appropriateness and cultural repertoire"
        ),
        "scale_sign_text_erutcurts": "scale_sign_text_structure",
        "Sign text erutcurts": "Sign text structure",
        "scale_mediating_stpecnoc": "scale_mediating_concepts",
    }
    for bad, good in _GARBLED.items():
        if bad in text:
            text = text.replace(bad, good)

    text = _resync_artifact_ids_from_fixed_titles(text)

    # L07: blank line after scale/table header block before markdown table
    text = re.sub(
        r"(### [^\n]+\| [^\n]+\n)(\|)",
        r"\1\n\2",
        text,
    )
    text = re.sub(
        r"(<!-- el:start type=artifact id=scale_[^\n]+-->\n)(\|)",
        r"\1\n\2",
        text,
    )

    # L07 p.90: drop flattened mediation label soup after text_diagram fence
    text = re.sub(
        r"(```\s*\n)(Relaying Facilitating Managing[\s\S]*?)(<!-- el:end id=figure_14)",
        r"\1\3",
        text,
        count=1,
    )
    # Broader: after mediation figure tree, drop non-prose label dumps before el:end
    text = re.sub(
        r"(```\s*\n)((?:(?!```)(?!<!-- el:end)[^\n]*\n)*?"
        r"(?:Relaying |Facilitating |Translating |Note-taking|Mediating\s+Strategies|\*\*Mediating)[\s\S]*?)"
        r"(<!-- el:end id=figure_14_mediation_activities_strategies -->)",
        r"\1\3",
        text,
        count=1,
    )

    # L06 p.41 safety net only: if root still left progressive mid-cut band garbage
    # (fragment starting mid-sentence without Intuitive/Qualitative/Quantitative lines),
    # replace with clean 3-phase body. Prefer callout_detect full-textbox path.
    if "callout_p041_0" in text:
        m_p41 = re.search(
            r"<!-- el:start type=artifact id=callout_p041_0 page=41 -->.*?<!-- el:end id=callout_p041_0 -->",
            text,
            flags=re.S,
        )
        if m_p41:
            block = m_p41.group(0)
            has_phases = (
                "Intuitive phase" in block
                and "Qualitative phase" in block
                and "Quantitative phase" in block
            )
            # Mid-cut progressive dump: band fragment without phase structure
            looks_garbage = (
                not has_phases
                or re.search(
                    r">\s+that original project, and described briefly",
                    block,
                )
                is not None
                or block.count("> The illustrative") > 1
            )
            if looks_garbage:
                clean_p41 = (
                    "<!-- el:start type=artifact id=callout_p041_0 page=41 -->\n"
                    "> **CEFR descriptor research project**\n"
                    ">\n"
                    "> The illustrative descriptors published in the CEFR 2001 were based on results "
                    "from a Swiss National Science Foundation research project set up to develop and "
                    "validate descriptors for the CEFR and the ELP and to give a picture of the "
                    "development of language proficiency reached at the end of different school years "
                    "in the Swiss educational system. The project described in this document, to "
                    "develop an extended set of illustrative descriptors, replicated the approach "
                    "taken in this Swiss project, which took place from 1993 to 1997. The methodology "
                    "used in that original project, and described briefly in CEFR 2001 Appendix B, "
                    "comprised three phases:\n"
                    ">\n"
                    "> **Intuitive phase:** Detailed analysis of existing descriptor scales and "
                    "authoring of new descriptors.\n"
                    ">\n"
                    "> **Qualitative phase:** 32 face-to-face workshops with groups of 4 to 12 "
                    "teachers, focusing on (a) sorting descriptors into the categories they purported "
                    "to describe; (b) evaluating the clarity, accuracy and relevance of the "
                    "descriptors; and (c) sorting descriptors into bands of proficiency.\n"
                    ">\n"
                    "> **Quantitative phase:** Rasch scaling analysis of the way 250 teachers "
                    "interpreted the difficulty of the descriptors when each teacher assessed 10 "
                    "learners, forming a structured sample of two of their classes at the end of the "
                    "school year. These evaluations with descriptors took place when the "
                    "(approximately 80% secondary school) teachers were awarding grades for the "
                    "school year.\n"
                    "<!-- el:end id=callout_p041_0 -->"
                )
                text = text[: m_p41.start()] + clean_p41 + text[m_p41.end() :]

    return text


def _repair_collapsed_blockquotes(text: str) -> str:
    """Re-expand callout blockquotes that were soft-joined onto one line.

    Pattern: ``> **Title** > > body > > more`` → proper multi-line blockquote
    with blank ``>`` separators (UV-01).
    """
    def _fix_line(line: str) -> str:
        s = line.strip()
        if not s.startswith(">"):
            return line
        # Only rewrite if multiple quote markers appear on one physical line
        if s.count(">") < 2:
            return line
        if " > " not in s and not re.search(r"\*\*[^*]+\*\*\s+>", s):
            return line
        # Split into quote segments; tolerate empty segments between ``> >``
        raw_parts = re.split(r"(?:(?<=\S)\s+>\s*|\s+>\s+)", s, maxsplit=0)
        # Fallback simpler split
        raw_parts = re.split(r"\s+>\s*", s)
        out_lines: list[str] = []
        for i, part in enumerate(raw_parts):
            part = part.strip()
            # Strip accidental leading > left by split remainder
            while part.startswith(">"):
                part = part[1:].lstrip()
            if i == 0:
                out_lines.append("> " + part if part else ">")
                continue
            if not part:
                # blank quote separator
                if out_lines and out_lines[-1] != ">":
                    out_lines.append(">")
                continue
            # body segment + trailing blank separator
            out_lines.append("> " + part)
            out_lines.append(">")
        while out_lines and out_lines[-1] == ">":
            out_lines.pop()
        return "\n".join(out_lines)

    return "\n".join(_fix_line(ln) for ln in text.splitlines())


def format_structured_markdown(text: str) -> str:
    """Apply full post-processing pipeline; bold spacing preserved via fix_bold_markdown.

    Pipeline mirrors the original standalone Session-2 formatter, plus list repair
    (soft-wrap bullets, no blank rows between list items).
    """
    text = fix_ocr_typos(text)
    # Early mid-line dingbat split so later list repair sees real list items.
    text = _fix_inline_bullets(text)
    text = _split_midline_list_runs(text)
    text = _join_mid_bold_and_section_wraps(text)
    lines = text.splitlines()
    lines = _dedupe_consecutive_lines(lines)
    lines = _dedupe_page_comments(lines)
    lines = _join_wrapped_lines(lines)
    lines = _convert_bullet_lines(lines)
    lines = _repair_list_blocks(lines)
    lines = _demote_footnote_headings(lines)
    lines = _promote_headings(lines)
    lines = _normalize_toc_region(lines)
    lines = _promote_section_headings(lines)
    lines = _normalize_page_markers(lines)
    lines = _normalize_section_boundaries(lines)
    lines = _ensure_paragraph_spacing(lines)
    lines = _format_page_blocks(lines)
    lines = _format_chapter_openings(lines)
    lines = _ensure_heading_body_spacing(lines)

    text = "\n".join(lines)
    text = _fix_inline_bullets(text)
    # Second list repair after inline bullet fixes (► / f** artifacts).
    text = "\n".join(_repair_list_blocks(text.splitlines()))
    text = "\n".join(_format_level_callouts(text.splitlines()))
    # Contract-aligned prose: list-end callout split, blockquote callouts, URL sanitize
    from pipeline.prose_format import normalize_prose

    text, _ = normalize_prose(text)
    text = _repair_collapsed_blockquotes(text)
    from pipeline.utils import sanitize_urls_in_text

    text = sanitize_urls_in_text(text)
    # Log 05 visual QA repairs (footnote glue, page *, callouts, A2 table, links)
    text = _repair_log05_markdown(text)
    # C2-ADJ: never glue footnotes / body to Page **N** (log 04 #5, #13)
    text = _resync_page_captions_from_pdf(text)
    text = _ensure_blank_before_page_captions(text)
    text = _ensure_section_31_after_figure_11(text)
    # R1: drop text_diagram leaf soup that can appear after §3.1 lead (Fig 11 dual emit)
    try:
        from pipeline.figure_inject import strip_garbage_under_figure_images

        text = strip_garbage_under_figure_images(text)
    except Exception:  # noqa: BLE001
        pass
    text = _dedupe_callout_title_lines(text)
    # Session 1 bold fix — single authoritative pass; no space-stripping afterward.
    text = fix_bold_markdown(text)
    text = "\n".join(_format_page_blocks(text.splitlines()))
    return _collapse_blank_lines(text)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def write_run_log(
    path: Path,
    *,
    before_size: int,
    before_mtime: float,
    before_hash: str,
) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out_stat = path.stat()
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    RUN_LOG.write_text(
        f"Final format completed: {now}\n"
        f"File: {path.relative_to(ROOT)}\n"
        f"Before size: {before_size} bytes\n"
        f"Before modified: {datetime.fromtimestamp(before_mtime):%m/%d/%Y %H:%M:%S}\n"
        f"After size: {out_stat.st_size} bytes\n"
        f"After modified: {datetime.fromtimestamp(out_stat.st_mtime):%m/%d/%Y %H:%M:%S}\n"
        f"Before SHA256: {before_hash}\n"
        f"After SHA256: {_sha256(path)}\n",
        encoding="utf-8",
    )


def run_post_process(
    path: Path = FINAL_MARKDOWN,
) -> dict[str, int | str]:
    """Format the final Markdown deliverable in place."""
    raw_bytes = path.read_bytes()
    before_stat = path.stat()
    before_hash = hashlib.sha256(raw_bytes).hexdigest().upper()
    cleaned = format_structured_markdown(raw_bytes.decode("utf-8"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(cleaned, encoding="utf-8")
    write_run_log(
        path,
        before_size=before_stat.st_size,
        before_mtime=before_stat.st_mtime,
        before_hash=before_hash,
    )
    return {
        "input_lines": len(raw_bytes.decode("utf-8").splitlines()),
        "output_lines": len(cleaned.splitlines()),
        "output_path": str(path),
    }