"""Structured Markdown formatting — integrated final step of Session 1 merge.

Reads and writes ``final_output/CEFR_Companion_Volume.md`` in place so there is a
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
    r"^(\s*)(?:f\*\*|f\s+(?=[A-Z*\"'])|▶|▸|►|•|▪|‣)\s*",
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
    if (
        _HEADING.match(s)
        or _HTML_COMMENT.match(s)
        or _IMAGE.match(s)
        or _HRULE.match(s)
        or _TABLE_ROW.match(s)
        or _FENCE.match(s)
        or _LIST_ITEM.match(s)
        or _PAGE_MARKER.match(s)
        or _LEVEL_LABEL.match(s)
        or _NUMBERED_FOOTNOTE.match(s)
        or _SECTION_TITLE.match(s)
        or _COUNTRY_BLOCK.match(s)
        or _LONE_PAGE_NUM.match(s)
        or _BOLD_ONLY.match(s)
    ):
        return True
    if s in ("CONTENTS", "FOREWORD"):
        return True
    return False


def _should_break_paragraph(prev: str, nxt: str) -> bool:
    prev = prev.strip()
    nxt = nxt.strip()
    if not prev or not nxt:
        return True
    if _is_block_starter(nxt):
        return True
    if _BOLD_ONLY.match(nxt):
        return True
    if _SENTENCE_END.search(prev):
        if len(nxt) < 70 and not _SENTENCE_END.search(nxt):
            return True
        if nxt[0].isupper():
            starters = (
                "The ", "This ", "In ", "As ", "It ", "However", "Furthermore",
                "Since ", "Much ", "Many ", "A ", "An ", "These ", "Those ",
                "There ", "They ", "We ", "Users ", "Researchers ",
            )
            if nxt.startswith(starters) or (len(nxt) > 50 and not nxt.startswith("CEFR")):
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
            out.append(stripped)
            continue

        if buf and _should_break_paragraph(buf[-1], stripped):
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
                if not _HEADING.match(nxt) and not _is_page_comment(nxt):
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


def _normalize_page_markers(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        s = line.strip()
        s = s.lstrip("\ufeff").strip()
        m = re.match(r"^Page\s+(\d+)", s, re.I)
        if m:
            out.append(f"<!-- Page {m.group(1)} -->")
            continue
        m2 = re.match(r"^(\d+)\s+CEFR\s*[–-]\s*Companion volume", s, re.I)
        if m2:
            out.append(f"<!-- Page {m2.group(1)} -->")
            continue
        m3 = re.match(r"^(.+?)\s+Page\s+(\d+)\s*$", s)
        if m3 and len(m3.group(1)) > 3:
            out.append(m3.group(1).strip())
            out.append(f"<!-- Page {m3.group(2)} -->")
            continue
        out.append(line)
    return out


def _fix_inline_bullets(text: str) -> str:
    text = re.sub(r"►\s*", "- ", text)
    text = re.sub(r":\s*f\*\*", ":\n\n- **", text)
    text = re.sub(r"\*\*\s*f\*\*", "**\n- **", text)
    text = re.sub(r"(?<=\n)f\*\*", "- **", text)
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


def _dedupe_consecutive_lines(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        if out and line == out[-1] and line.strip():
            continue
        out.append(line)
    return out


def _dedupe_page_comments(lines: list[str]) -> list[str]:
    """Remove consecutive duplicate <!-- page:N --> markers."""
    out: list[str] = []
    for line in lines:
        if (
            out
            and _is_page_comment(line.strip())
            and _is_page_comment(out[-1].strip())
            and line.strip().lower() == out[-1].strip().lower()
        ):
            continue
        out.append(line)
    return out


def _normalize_section_boundaries(lines: list[str]) -> list[str]:
    """Move section headings that appear before a page marker to after it."""
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
    """Guarantee a blank line between consecutive prose paragraphs."""
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
    """Keep <!-- page:N --> + italic caption together; blank lines on either side."""
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not _is_page_comment(line):
            out.append(line)
            i += 1
            continue

        block = [line]
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines) and _is_page_italic(lines[j]):
            block.append(lines[j])
            j += 1

        if out and out[-1] != "":
            out.append("")
        out.extend(block)
        if j < len(lines):
            out.append("")
        i = j

    return out


def _collapse_blank_lines(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def format_structured_markdown(text: str) -> str:
    """Apply full post-processing pipeline; bold spacing preserved via fix_bold_markdown."""
    text = fix_ocr_typos(text)
    lines = text.splitlines()
    lines = _dedupe_consecutive_lines(lines)
    lines = _dedupe_page_comments(lines)
    lines = _join_wrapped_lines(lines)
    lines = _convert_bullet_lines(lines)
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
    text = "\n".join(_format_level_callouts(text.splitlines()))
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