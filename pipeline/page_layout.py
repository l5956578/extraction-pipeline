"""Reassemble PDF page text in reading order with footnotes at bottom."""

from __future__ import annotations

import re

import fitz

_BOLD = 2
# Allow markdown bold between "Page" and digits (e.g. Page **25**).
_PAGE_NUM = re.compile(r"Page\s+\*?\*?\d+", re.I)
_CEFR_RUNNING = re.compile(r"^\d+\s+CEFR", re.I)
_FOOTNOTE = re.compile(r"^(\d{1,2})\.(?:\s+|\s*$)")
_COMPANION_FOOTER = re.compile(r"CEFR.*Companion volume", re.I)
_ROW_Y_TOL = 3.0
# CEFR PDF often uses Bold/Semibold fonts without the PDF bold flag bit.
_BOLD_FONT = re.compile(r"(bold|semibold|black|heavy|extrabold)", re.I)
# Symbol fonts encode arrows/bullets as ASCII (e.g. '3' → ▶, 'f' → list bullet).
_DINGBAT_FONT = re.compile(r"(dingbat|wingding|arrows|symbol|zapf)", re.I)
_DINGBAT_MAP = {
    # FFDingbats-ArrowsOne: page-footer triangle before "CEFR – Companion volume"
    "3": "▶",
    # Wingdings3: list bullet used as "f" in PDF text layer
    "f": "f",
}


def _span_is_bold(sp: dict) -> bool:
    font = str(sp.get("font") or "")
    if _DINGBAT_FONT.search(font):
        return False
    if sp.get("flags", 0) & _BOLD:
        return True
    return bool(_BOLD_FONT.search(font))


def _map_dingbat_text(text: str, font: str) -> str:
    if not text or not _DINGBAT_FONT.search(font or ""):
        return text
    return "".join(_DINGBAT_MAP.get(ch, ch) for ch in text)


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
        font = str(sp.get("font") or "")
        t = _map_dingbat_text(t, font)
        # Soft hyphen in PDF footers (CEFR –\xad Companion)
        t = t.replace("\xad", "")
        if not t:
            continue
        # Dingbat-only bullet: ensure a trailing space so "fGuide" → "f Guide"
        if _DINGBAT_FONT.search(font) and t.strip() in ("f", "▶", "•"):
            t = t.strip() + " "
        if _span_is_bold(sp):
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
    # Running head + page number on one footer line (e.g. "Introduction Page 25")
    if re.search(r"Page\s+\*?\*?\d+", s, re.I) and y0 > page_height * 0.88:
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


def first_footer_band_y(page: fitz.Page) -> float:
    """Y of first footnote or page-marker line; else 88% of page height."""
    page_height = page.rect.height
    ys: list[float] = []
    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            text = _span_text(line.get("spans", [])).strip()
            if not text:
                continue
            y0 = line["bbox"][1]
            kind = _classify_line(text, y0, page_height)
            if kind in ("footnote", "page_marker"):
                ys.append(y0)
    return min(ys) if ys else page_height * 0.88


def _is_footnote_continuation(text: str) -> bool:
    s = text.strip()
    if not s:
        return False
    if _FOOTNOTE.match(s):
        return False
    # Never absorb page footers / running heads into footnotes.
    if _PAGE_NUM.search(s) or _COMPANION_FOOTER.search(s):
        return False
    if re.match(r"^\*?\*?Introduction\*?\*?", s, re.I):
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


# Soft-wrapped body lines on CEFR pages sit ~12pt apart; true paragraph
# breaks are ~17–18pt+ (measured page 22). Midpoint threshold:
_PARAGRAPH_Y_GAP = 15.0


def _is_list_or_heading_line(s: str) -> bool:
    return bool(
        s.startswith(("#", "-", "*", "•"))
        or re.match(r"^f\s+", s, re.I)
        or re.match(r"^\d+(?:\.\d+)+\.?\s", s)
        or re.match(r"^\d{1,2}\.\s+\S", s)
    )


def _join_body_paragraphs(rows: list[tuple[float, str]]) -> list[str]:
    """Join soft-wrapped PDF lines using vertical gap, not capital-after-period.

    Lines with y-gap < ``_PARAGRAPH_Y_GAP`` stay in the same paragraph (even when
    the previous line ends with ``.`` and the next starts with ``The`` / ``Here``).
    Larger gaps insert a paragraph break (blank line in output list via ``""``).
    """
    if not rows:
        return []
    out: list[str] = []
    buf: list[str] = []
    prev_y: float | None = None

    def flush() -> None:
        if buf:
            out.append(" ".join(buf))
            buf.clear()

    for y, text in rows:
        s = text.strip()
        if not s:
            flush()
            if out and out[-1] != "":
                out.append("")
            prev_y = y
            continue

        if _is_list_or_heading_line(s):
            # New list item: close prior prose; keep item open for soft-wrap tails.
            if buf and not _is_list_or_heading_line(buf[0]):
                flush()
            elif buf and _is_list_or_heading_line(buf[0]) and prev_y is not None:
                if y - prev_y >= _PARAGRAPH_Y_GAP:
                    flush()
            buf.append(s)
            prev_y = y
            continue

        if buf and _is_list_or_heading_line(buf[0]):
            # Soft-wrap continuation of a bullet (same gap class as body wraps).
            if prev_y is not None and y - prev_y < _PARAGRAPH_Y_GAP:
                buf.append(s)
                prev_y = y
                continue
            flush()

        if buf and prev_y is not None and y - prev_y >= _PARAGRAPH_Y_GAP:
            flush()
            if out and out[-1] != "":
                out.append("")

        buf.append(s)
        prev_y = y

    flush()
    while out and out[-1] == "":
        out.pop()
    return out


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

    # Pass y + text so paragraph breaks use geometry, not capital-after-period.
    rows = [(y, text) for y, _, text in ordered]
    return _join_body_paragraphs(rows)


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


_TABLE_DEBRIS_LEVELS = re.compile(
    r"\b(C2|C1|B2\+?|B1\+?|A2\+?|A1\+?)\b",
    re.I,
)
_CAN_DESCRIPTOR = re.compile(r"^Can\s", re.I)


def _is_rotated_footnote_continuation(text: str) -> bool:
    s = text.strip()
    if not s:
        return False
    if _FOOTNOTE.match(s):
        return False
    if _CAN_DESCRIPTOR.match(s):
        return False
    levels = _TABLE_DEBRIS_LEVELS.findall(s)
    if levels:
        return False
    if re.search(r"\bCan\s", s, re.I):
        return False
    debris_markers = (
        "ideas or opinions",
        "persons and institutions",
        "B2 C1",
        "sentence.",
        " about.",
    )
    if any(marker in s for marker in debris_markers):
        return False
    return s[0].islower() and len(s) < 120


def extract_surgical_rotated_footnotes(
    page: fitz.Page,
    table_bbox: tuple[float, float, float, float],
    margin: float = 8.0,
) -> list[str]:
    """Footnotes below table + margin zone; numbered lines with validated continuations.

    Used for rotated descriptor pages (e.g. footnote 46 on p.146). Not Grok vision.
    """
    page_height = page.rect.height
    _, _, _, table_bottom = table_bbox
    margin_cut = page_height * 0.62
    entries: list[tuple[float, str]] = []
    buf: list[str] = []
    buf_y = 0.0

    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            y0 = line["bbox"][1]
            direction = line.get("dir", (1.0, 0.0))
            text = _span_text(line.get("spans", [])).strip()
            if not text or _is_page_marker(text, y0, page_height):
                continue
            is_horizontal = abs(direction[1]) <= 0.3
            in_margin = y0 > margin_cut
            below_table = y0 > table_bottom + margin
            if not in_margin and not below_table:
                continue
            if not in_margin and abs(direction[1]) > 0.3 and not _FOOTNOTE.match(text):
                continue
            if _FOOTNOTE.match(text):
                if buf:
                    entries.append((buf_y, re.sub(r"\s+", " ", " ".join(buf))))
                    buf = []
                buf = [text]
                buf_y = y0
            elif buf and (is_horizontal or _is_rotated_footnote_continuation(text)):
                if _is_rotated_footnote_continuation(text):
                    buf.append(text)
                elif buf:
                    entries.append((buf_y, re.sub(r"\s+", " ", " ".join(buf))))
                    buf = []
            elif buf:
                entries.append((buf_y, re.sub(r"\s+", " ", " ".join(buf))))
                buf = []
    if buf:
        entries.append((buf_y, re.sub(r"\s+", " ", " ".join(buf))))
    return [text for _, text in sorted(entries, key=lambda item: item[0])]


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


def _normalize_page_marker_caption(marker: str, page_num: int) -> str:
    """Tidy footer caption to the PDF's actual running-header form (L05-PAGE-AST).

    CEFR Companion Volume alternates:
    - even / title pages: ``Page N ▶ CEFR – Companion volume``
    - odd chapter pages: ``Key aspects of the CEFR for teaching and learning  Page N``
    - simple: ``Page N``
    Never force the book-title form when the marker is the chapter running head
    (those strings also contain the word \"CEFR\").

    Log 07 / user QA: markers often arrive as ``Title ** Page **29**`` (bold around
    digits). Match on a bold-stripped form so chapter titles are not collapsed to
    bare ``Page **N**``.
    """
    s = re.sub(r"\s+", " ", marker.replace("\xad", "").strip())
    s = s.replace("3 CEFR", "▶ CEFR").replace(" 3 ", " ▶ ")
    # Bold-insensitive plain text for structural matching only
    plain = re.sub(r"\*+", "", s)
    plain = re.sub(r"\s+", " ", plain).strip()

    # Chapter / section running head: title BEFORE "Page N" (plain form)
    m_ch = re.match(
        r"^(?P<title>.+?)\s+Page\s+(?P<num>\d+)\s*$",
        plain,
        re.I,
    )
    if m_ch and not re.match(r"^Page\s+", m_ch.group("title"), re.I):
        title = m_ch.group("title").strip(" –-\t")
        title = re.sub(r"\s*[▶►3]\s*$", "", title).strip()
        # Not the book-title line mis-parsed as chapter
        if title and not re.search(r"Companion\s+volume", title, re.I):
            if not re.match(r"^Page\b", title, re.I):
                return f"*{title} ▶ Page **{page_num}***"
    # Introduction short form
    if re.search(r"Introduction", plain, re.I) and not re.search(
        r"Page\s+\d+\s*[▶3].*CEFR", plain, re.I
    ):
        if re.search(r"Introduction\s+Page", plain, re.I) or not re.search(
            r"Companion", plain, re.I
        ):
            return f"**Introduction** Page **{page_num}**"
    # Book-title form: "Page N ▶ CEFR – Companion volume"
    if re.search(r"Companion\s+volume", plain, re.I) or (
        re.match(r"^Page\s+\d+", plain, re.I)
        and (re.search(r"CEFR", plain, re.I) or "▶" in plain or re.search(r"\b3\b", plain))
    ):
        return f"*Page **{page_num}** ▶ **CEFR – Companion volume***"
    # Bare page number only (must not match "Chapter Title Page N")
    if re.search(r"^Page\s+\d+\s*$", plain, re.I):
        return f"Page **{page_num}**"
    return f"*{plain}*" if plain else f"Page **{page_num}**"


def format_page_footer(page_num: int, zones: dict[str, list[str]]) -> str:
    """Human-readable page line first, then machine ``<!-- page:N -->`` marker."""
    parts: list[str] = []
    if zones["footnotes"]:
        parts.append("\n".join(zones["footnotes"]))
    if zones["page_markers"]:
        marker = zones["page_markers"][-1]
        parts.append(f"{_normalize_page_marker_caption(marker, page_num)}\n\n<!-- page:{page_num} -->")
    elif page_num:
        parts.append(f"Page **{page_num}**\n\n<!-- page:{page_num} -->")
    return "\n\n".join(parts)


def extract_page_body(page: fitz.Page) -> str:
    """Body text only (bold-aware). Footers are emitted by inventory footer elements."""
    zones = classify_page_zones(page)
    if not zones["body"]:
        return ""
    parts: list[str] = []
    for line in zones["body"]:
        if line == "":
            if parts and parts[-1] != "":
                parts.append("")
            continue
        parts.append(line)
    # Blank list markers already encode paragraph breaks.
    text = "\n\n".join(p for p in parts if p is not None)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


# Diagram-label lexicon for exclusive-region filtering (C2-ADJ).
# Real prose sentences in a crop y-band are KEPT; only label-like lines drop.
_DIAGRAM_LABEL_RE = re.compile(
    r"(Understanding conversation between other|Expressing a personal response|"
    r"Relaying specific information|Processing text in (?:speech|writing)|"
    r"Collaborating to construct meaning|Facilitating collaborative|"
    r"Facilitating pluricultural|Sustained monologue|Reading for orientation|"
    r"Reading for information|Reading as a leisure|Reading instructions|"
    r"Goal-oriented (?:co-operation|online)|Informal discussion|"
    r"Formal discussion|Understanding an interlocutor|"
    r"Watching TV, film and video|Creative writing|Reports and essays|"
    r"Addressing audiences|Encouraging conceptual|Explaining data|"
    r"Note-taking \(lectures|Online conversation and discussion|"
    r"Information exchange|"
    r"^\s*\*{0,2}\s*(RECEPTION|PRODUCTION|INTERACTION|MEDIATION)\b|"
    r"\b(Pre-A1|A1|A2\+?|B1\+?|B2\+?|C1|C2|Above C2)\b.*\b(A1|A2|B1|B2|C1|C2)\b|"
    r"\b(English|German|French|Spanish|Italian)\b.*\b(English|German|French|Spanish|Italian)\b)",
    re.I,
)
_REAL_PROSE_START = re.compile(
    r"^(?:The |In |As |It |This |Although |One |However|Seeing |To |For |An |When |"
    r"After |Before |By |Most |Mediation |At |Graphic |Profiles |Neither |Language |"
    r"Such |Stakeholders |Figure \d+ |Levels |Descriptor |Plus |All |Key |With |"
    r"Web |In practice|Since |These |Those |Their |Our |We |You |There )",
    re.I,
)


def _line_overlap_frac(
    line_bbox: tuple[float, float, float, float],
    exclude: list[tuple[float, float, float, float]],
) -> float:
    """Max fraction of line area overlapping any exclude rect."""
    lx0, ly0, lx1, ly1 = line_bbox
    larea = max(1.0, (lx1 - lx0) * (ly1 - ly0))
    best = 0.0
    for ex0, ey0, ex1, ey1 in exclude:
        ix0, iy0 = max(lx0, ex0), max(ly0, ey0)
        ix1, iy1 = min(lx1, ex1), min(ly1, ey1)
        if ix1 <= ix0 or iy1 <= iy0:
            continue
        inter = (ix1 - ix0) * (iy1 - iy0)
        best = max(best, inter / larea)
    return best


def _is_diagram_label_text(text: str) -> bool:
    """True for radar/axis/level-row dumps that belong to a figure crop, not body prose."""
    s = re.sub(r"\s+", " ", text.strip())
    if not s:
        return False
    # Real captions stay so compose can replace them
    if re.match(r"^\*{0,2}\s*Figure\s+\d+\s*[–—\-]", s, re.I):
        return False
    plain = re.sub(r"^\*+|\*+$", "", s).strip()
    if _DIAGRAM_LABEL_RE.search(plain) or _DIAGRAM_LABEL_RE.search(s):
        return True
    # Level-only or multi-level row (e.g. Pre-A1 A1 A2 … C2)
    if re.fullmatch(
        r"(?:\*{0,2}(?:Pre-A1|A1|A2\+?|B1\+?|B2\+?|C1|C2|Above C2)\*{0,2}[\s,;]*)+",
        plain,
        re.I,
    ):
        return True
    # Language-axis row under plurilingual profiles
    langs = re.findall(
        r"\b(English|German|French|Spanish|Italian|Portuguese|Dutch|Russian)\b",
        plain,
        re.I,
    )
    levels = re.findall(r"\b(Pre-A1|A1|A2\+?|B1\+?|B2\+?|C1|C2|Above C2)\b", plain, re.I)
    if len(langs) >= 2 and len(levels) >= 2:
        return True
    if len(levels) >= 4 and not plain.endswith((".", "?", "!")):
        return True
    # ALL-CAPS mode / short axis token
    if re.fullmatch(r"\*{0,2}(RECEPTION|PRODUCTION|INTERACTION|MEDIATION)\*{0,2}", s, re.I):
        return True
    # Short Title-Case multi-token without sentence end inside crop → axis-ish
    if (
        not plain.endswith((".", "?", "!"))
        and 3 <= len(plain.split()) <= 8
        and len(plain) < 90
        and plain[0].isupper()
        and not _REAL_PROSE_START.match(plain)
        and re.search(
            r"(Reading|Understanding|Listening|Speaking|Writing|Monologue|"
            r"Discussion|Interaction|Mediation|Reception|Production)",
            plain,
            re.I,
        )
    ):
        return True
    return False


def _is_real_prose_line(text: str) -> bool:
    """Prefer keep: body sentences that must not be deleted by exclusive crop (C2-ADJ)."""
    s = re.sub(r"\s+", " ", text.strip())
    if not s:
        return False
    if re.match(r"^\*{0,2}\s*Figure\s+\d+\s*[–—\-]", s, re.I):
        return True  # caption — keep for compose replace
    plain = re.sub(r"^\*+|\*+$", "", s).strip()
    if _is_diagram_label_text(s):
        return False
    if len(plain) > 70 and plain.endswith((".", "?", "!")):
        return True
    if _REAL_PROSE_START.match(plain) and len(plain) > 40:
        return True
    # Mid-sentence continuation (lowercase start) of real body — keep
    if plain and plain[0].islower() and len(plain) > 30:
        return True
    return False


def should_drop_line_for_exclusive(
    text: str,
    line_bbox: tuple[float, float, float, float],
    exclude: list[tuple[float, float, float, float]],
    page_width: float,
) -> bool:
    """Drop only figure-label-like lines inside crop; keep real prose (review #1/#10).

    Wide crops often share y with body paragraphs. Dropping every overlapping
    line deletes neighbors (p.39–40). Prefer lexicon + geometry for labels only.
    """
    if not exclude:
        return False
    frac = _line_overlap_frac(line_bbox, exclude)
    if frac < 0.15:
        return False
    # Always drop clear diagram labels when any meaningful overlap
    if _is_diagram_label_text(text):
        return True
    # Always keep real prose sentences / captions
    if _is_real_prose_line(text):
        return False
    # Short non-sentence fragment deep inside crop → likely label debris
    s = text.strip()
    plain = re.sub(r"^\*+|\*+$", "", s).strip()
    if frac >= 0.55 and len(plain) < 100 and not plain.endswith((".", "?", "!")):
        # Require diagram-ish tokens so we don't delete "See also" / short notes
        if _is_diagram_label_text(s) or re.search(
            r"\b(A1|A2|B1|B2|C1|C2|RECEPTION|PRODUCTION|INTERACTION|MEDIATION|"
            r"English|German|French|Spanish|Italian)\b",
            plain,
            re.I,
        ):
            return True
    # High area overlap on non-prose short line without sentence end
    if frac >= 0.75 and len(plain) < 60 and not plain.endswith((".", "?", "!")):
        if not _REAL_PROSE_START.match(plain):
            return True
    return False


def extract_page_body_excluding(
    page: fitz.Page,
    exclude_rects: list[tuple[float, float, float, float]] | None = None,
) -> str:
    """Body text with selective exclusive-region filtering (C2-ADJ).

    Drops **diagram labels** inside figure crops; keeps real prose that shares
    a y-band with an oversized crop (neighbor protection, log 04 / review #1).
    """
    if not exclude_rects:
        return extract_page_body(page)

    page_height = page.rect.height
    page_width = page.rect.width
    entries: list[tuple[float, float, str, str]] = []

    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            text = _span_text(line.get("spans", [])).strip()
            if not text:
                continue
            bb = line["bbox"]
            y0 = bb[1]
            x0 = bb[0]
            kind = _classify_line(text, y0, page_height)
            if kind == "skip":
                continue
            if kind == "body" and should_drop_line_for_exclusive(
                text,
                (bb[0], bb[1], bb[2], bb[3]),
                exclude_rects,
                page_width,
            ):
                continue
            entries.append((y0, x0, kind, text))

    entries.sort(key=lambda e: e[0])
    zones = _partition_zones(entries, page_width, page_height)
    if not zones["body"]:
        return ""
    parts: list[str] = []
    for line in zones["body"]:
        if line == "":
            if parts and parts[-1] != "":
                parts.append("")
            continue
        parts.append(line)
    text = "\n\n".join(p for p in parts if p is not None)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract_body_text(page: fitz.Page) -> str:
    return extract_page_body(page)


def extract_page_content(page: fitz.Page, page_num: int) -> str:
    """Full page (body + footer). Prefer inventory split: body via rich_page, footer separate."""
    from pipeline.toc_layout import extract_toc_page, is_toc_page

    if is_toc_page(page_num):
        return extract_toc_page(page, page_num)
    zones = classify_page_zones(page)
    parts: list[str] = []
    body = extract_page_body(page)
    if body:
        parts.append(body)
    footer = format_page_footer(page_num, zones)
    if footer:
        parts.append(footer)
    return "\n\n".join(parts)