#!/usr/bin/env python3
"""Vision-informed page_overrides for CEFR EN 2001 PDF pages 141–273.

Produces work/cefr-en-2001/page_overrides/page_NNN.md with:
  <!-- vision: CEFR 2001 PDF page N -->

Uses font-aware layout (HelveticaNeue headings vs Swift body), table expansion,
and callout-box detection. Agent vision-checks PNGs and may overwrite pages.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
JOB = "cefr-en-2001"
OUT_DIR = ROOT / "work" / JOB / "page_overrides"
PDF = ROOT / "input" / JOB / "source.pdf"

# Full-line running headers only — never short words that appear in body/tables
CHROME_EXACT = {
    "Common European Framework of Reference for Languages: learning, teaching, assessment",
    "Language learning and teaching",
    "Tasks and their role in language teaching",
    "Linguistic diversification and the curriculum",
    "General Bibliography",
    "General bibliography",
    "Appendix A: developing proficiency descriptors",
    "Appendix B: The illustrative scales of descriptors",
    "Appendix C: The DIALANG scales",
    "Appendix D: The ALTE ‘Can Do’ statements",
    "Appendix D: The ALTE 'Can Do' statements",
    "Using the electronic version",
    "Important copyright information",
}
# Short chapter running heads — only strip when the *entire token* matches
CHROME_TOKEN_ONLY = {
    "Assessment",
    "Appendix A",
    "Appendix B",
    "Appendix C",
    "Appendix D",
    "Index",
}


@dataclass
class Tok:
    text: str
    y0: float
    x0: float
    size: float
    font: str
    flags: int
    is_heading_font: bool = False
    is_bullet: bool = False


def clean(t: str) -> str:
    t = t.replace("\u00ad", "")
    t = t.replace("\ufb01", "fi").replace("\ufb02", "fl")
    t = t.replace("ﬁ", "fi").replace("ﬂ", "fl")
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()


def is_heading_font(font: str) -> bool:
    f = font.lower()
    return "helvetica" in f or "neue" in f or "arial" in f or "univers" in f


def is_chrome(t: str) -> bool:
    s = t.strip()
    if not s:
        return True
    if re.fullmatch(r"\d{1,3}", s):
        return True
    if s in CHROME_EXACT or s in CHROME_TOKEN_ONLY:
        return True
    if s in {
        "Appendix A: developing proficiency descriptors",
        "Appendix B: The illustrative scales of descriptors",
        "Appendix C: The DIALANG scales",
        "Appendix D: The ALTE ‘Can Do’ statements",
        "Appendix D: The ALTE 'Can Do' statements",
    }:
        return True
    if re.match(r"^([A-Z]\s+){3,}[A-Z]\s*$", s):
        return True
    return False


def extract_tokens(page: fitz.Page) -> list[Tok]:
    d = page.get_text("dict")
    toks: list[Tok] = []
    for b in d.get("blocks", []):
        if b.get("type") != 0:
            continue
        for l in b.get("lines", []):
            spans = l.get("spans", [])
            if not spans:
                continue
            text = clean("".join(s["text"] for s in spans))
            if not text:
                continue
            sizes = [s["size"] for s in spans]
            size = sorted(sizes)[len(sizes) // 2]
            font = spans[0].get("font", "")
            flags = spans[0].get("flags", 0)
            # prefer any heading-like font in the line
            hf = any(is_heading_font(s.get("font", "")) for s in spans)
            toks.append(
                Tok(
                    text=text,
                    y0=l["bbox"][1],
                    x0=l["bbox"][0],
                    size=size,
                    font=font,
                    flags=flags,
                    is_heading_font=hf,
                    is_bullet=text in {"•", "●", "◦", "▪", "·"} or text.startswith("•"),
                )
            )
    return toks


def callout_rects(page: fitz.Page) -> list[fitz.Rect]:
    rects: list[fitz.Rect] = []
    for d in page.get_drawings():
        r = d.get("rect")
        if not r:
            continue
        if r.width > 280 and 35 < r.height < 280:
            if d.get("type") == "s" or (d.get("color") is not None and d.get("fill") is None):
                rects.append(fitz.Rect(r))
    rects.sort(key=lambda r: (r.y0, r.x0))
    out: list[fitz.Rect] = []
    for r in rects:
        if any(abs(r.y0 - o.y0) < 8 and abs(r.height - o.height) < 12 for o in out):
            continue
        out.append(r)
    return out


def in_rects(y: float, x: float, rects: list[fitz.Rect], pad: float = 2.0) -> bool:
    """True if point is inside a special rect (table/callout). Small pad to avoid
    swallowing preceding captions/intro sentences above tables."""
    for r in rects:
        if (r.y0 + 2) <= y <= (r.y1 + pad) and (r.x0 - pad) <= x <= (r.x1 + pad):
            return True
    return False


def text_in_rect(page: fitz.Page, rect: fitz.Rect) -> str:
    t = page.get_text("text", clip=rect.irect)
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", t)
    return t.strip()


def format_callout(text: str) -> str:
    raw_lines = [clean(ln) for ln in text.splitlines() if clean(ln)]
    # Drop lone bullet glyphs; attach following
    lines: list[str] = []
    i = 0
    while i < len(raw_lines):
        ln = raw_lines[i]
        if ln in {"•", "●", "◦", "-", "–"} and i + 1 < len(raw_lines):
            lines.append("- " + raw_lines[i + 1])
            i += 2
            continue
        if ln.startswith("•"):
            lines.append("- " + ln.lstrip("• ").strip())
            i += 1
            continue
        lines.append(ln)
        i += 1

    # merge soft wraps into paragraphs / list items
    out: list[str] = []
    buf = ""
    for ln in lines:
        if ln.startswith("- "):
            if buf:
                out.append(buf)
                buf = ""
            out.append(ln)
            continue
        if not buf:
            buf = ln
        elif ln[0:1].islower() or not buf.rstrip().endswith((".", ":", "?", "!")):
            buf = buf + " " + ln
        else:
            out.append(buf)
            buf = ln
    if buf:
        out.append(buf)

    # blockquote
    bq = []
    for p in out:
        if p.startswith("- "):
            bq.append("> " + p)
        else:
            bq.append("> " + p)
            bq.append(">")
    # trim trailing empty >
    while bq and bq[-1] == ">":
        bq.pop()
    return "\n".join(bq)


def expand_table(data: list[list]) -> list[list[str]]:
    """Expand cells that contain stacked levels (A1\\nA1\\n...) into one row per statement."""
    if not data:
        return []
    rows: list[list[str]] = []
    header = [("" if c is None else str(c).replace("\n", " ").strip()) for c in data[0]]
    rows.append(header)

    for raw in data[1:]:
        cells = [("" if c is None else str(c).strip()) for c in raw]
        if not any(cells):
            continue
        # If first column has multiple levels stacked and second has multiple sentences
        left = cells[0] if cells else ""
        right = cells[1] if len(cells) > 1 else ""
        left_parts = [p.strip() for p in re.split(r"[\n\r]+", left) if p.strip()]
        # Split right into statements: "I can ..." starts
        if len(left_parts) > 1 and right:
            # Prefer split on "I can" / "Can " boundaries
            stmts = re.split(r"(?=(?:I can |Can |Has |Is |Shows |Produces |Understands |Reads |Writes |Speaks |Listens ))", right)
            stmts = [s.strip().replace("\n", " ") for s in stmts if s.strip()]
            # Also try newline split if count matches
            nl_stmts = [s.strip().replace("\n", " ") for s in re.split(r"[\n\r]+", right) if s.strip()]
            if len(nl_stmts) == len(left_parts):
                stmts = nl_stmts
            elif len(stmts) != len(left_parts):
                # fall back: pair by count when possible
                if len(nl_stmts) > 1:
                    stmts = nl_stmts
            n = max(len(left_parts), len(stmts))
            for i in range(n):
                lv = left_parts[i] if i < len(left_parts) else (left_parts[-1] if left_parts else "")
                st = stmts[i] if i < len(stmts) else ""
                rest = cells[2:] if len(cells) > 2 else []
                rows.append([lv, st] + rest)
        else:
            rows.append([c.replace("\n", " ") for c in cells])
    return rows


def table_to_md(rows: list[list[str]], pnum: int, ti: int) -> str:
    if len(rows) < 1:
        return ""
    ncol = max(len(r) for r in rows)
    rows = [r + [""] * (ncol - len(r)) for r in rows]
    rows = [[clean(c).replace("|", "\\|") for c in r] for r in rows]
    # Known PDF cell truncations
    for r in rows:
        for i, c in enumerate(r):
            if c.strip() == "by others":
                r[i] = "Assessment by others"
            if c.strip() == "Assessment by others" or "Assessment by others" in c:
                pass
    first = rows[0]
    looks_data = bool(first and re.match(r"^\d{1,2}$", first[0].strip()))
    lines = []
    if looks_data:
        headers = [f"Col{c+1}" for c in range(ncol)]
        if ncol == 3:
            headers = ["#", "Left", "Right"]
        elif ncol == 2:
            headers = ["Left", "Right"]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * ncol) + " |")
        for r in rows:
            lines.append("| " + " | ".join(r) + " |")
    else:
        lines.append("| " + " | ".join(rows[0]) + " |")
        lines.append("| " + " | ".join(["---"] * ncol) + " |")
        for r in rows[1:]:
            lines.append("| " + " | ".join(r) + " |")
    body = "\n".join(lines)
    return (
        f"<!-- el:start type=table id=cefr2001_p{pnum:03d}_t{ti} page={pnum} -->\n"
        f"{body}\n"
        f"<!-- el:end id=cefr2001_p{pnum:03d}_t{ti} -->"
    )


def extract_tables(page: fitz.Page, pnum: int) -> list[tuple[fitz.Rect, str]]:
    out: list[tuple[fitz.Rect, str]] = []
    try:
        tf = page.find_tables()
    except Exception:
        return out
    if not tf:
        return out
    for ti, tab in enumerate(tf.tables):
        try:
            data = tab.extract()
        except Exception:
            continue
        if not data:
            continue
        rows = expand_table(data)
        if len(rows) < 2:
            continue
        md = table_to_md(rows, pnum, ti)
        if md:
            out.append((fitz.Rect(tab.bbox), md))
    return out


def is_section_number(t: str) -> bool:
    return bool(re.fullmatch(r"\d+(?:\.\d+)+", t.strip()))


def is_chapter_heading(t: str) -> bool:
    return bool(re.match(r"^(Chapter\s+\d+|Appendix\s+[A-D]|General Bibliography|Index)\b", t, re.I))


def heading_depth(num: str) -> int:
    # 6 -> ##, 6.1 -> ##, 6.1.3 -> ###, 6.1.3.1 -> ####
    dots = num.count(".")
    if dots == 0:
        return 2
    return min(dots + 2, 4)


def format_page(page: fitz.Page, pnum: int) -> str:
    callouts = callout_rects(page)
    tables = extract_tables(page, pnum)
    skip = callouts + [r for r, _ in tables]

    toks = extract_tokens(page)
    # filter chrome + inside specials
    kept: list[Tok] = []
    for t in toks:
        if is_chrome(t.text):
            continue
        if skip and in_rects(t.y0, t.x0, skip):
            continue
        kept.append(t)

    chunks: list[tuple[float, str]] = []  # y, md

    i = 0
    para: list[str] = []
    para_y: float | None = None
    list_items: list[str] = []
    list_y: float | None = None

    def flush_para():
        nonlocal para, para_y
        if not para:
            return
        text = " ".join(para)
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
        # fix "and 5. Whilst" style split from mid-number
        text = re.sub(r"\band\s+(\d+)\.\s+", r"and \1. ", text)
        if text and para_y is not None:
            chunks.append((para_y, text))
        para = []
        para_y = None

    def flush_list():
        nonlocal list_items, list_y
        if not list_items:
            return
        y = list_y if list_y is not None else 0
        chunks.append((y, "\n".join(list_items)))
        list_items = []
        list_y = None

    while i < len(kept):
        tok = kept[i]
        t = tok.text

        # bullet alone → merge with next
        if tok.is_bullet or t in {"•", "●", "◦"}:
            flush_para()
            item = ""
            if t.startswith("•") and len(t) > 1:
                item = t.lstrip("• ").strip()
            elif i + 1 < len(kept) and not kept[i + 1].is_heading_font:
                item = kept[i + 1].text
                i += 1
            if item:
                if list_y is None:
                    list_y = tok.y0
                list_items.append(f"- {item}")
            i += 1
            continue

        # Heading number alone (6.1.3 / 6.1.3.1) + title line(s)
        if is_section_number(t) or (tok.is_heading_font and re.match(r"^\d+(\.\d+)*$", t)):
            flush_list()
            flush_para()
            num = t.strip()
            title_parts: list[str] = []
            j = i + 1
            while j < len(kept):
                nt = kept[j]
                # next heading number stops
                if is_section_number(nt.text):
                    break
                # body font starting a sentence ends title
                if not nt.is_heading_font and not is_heading_font(nt.font):
                    # sometimes title uses Light font already consumed; if first after num is body, title may be missing on separate font line
                    break
                if nt.is_bullet:
                    break
                # heading title line
                if nt.is_heading_font or is_heading_font(nt.font):
                    title_parts.append(nt.text)
                    j += 1
                    # single title line usually enough for short headings
                    if not is_section_number(nt.text):
                        # if next is also heading font and short continuation, take it
                        if j < len(kept) and kept[j].is_heading_font and not is_section_number(kept[j].text):
                            # avoid swallowing long multi-line titles into one; CEFR titles are one line
                            break
                        break
                else:
                    break
            title = " ".join(title_parts).strip()
            depth = heading_depth(num)
            label = f"{num} {title}".strip() if title else num
            chunks.append((tok.y0, "#" * depth + " " + label))
            # j is first non-title token (or end); never skip body lines
            i = j if j > i else i + 1
            continue

        # Heading without number (Chapter 7, Appendix A, Document C1, Table 7…)
        if tok.is_heading_font and not re.match(r"^[a-z]\)", t):
            # short title-like
            if len(t) < 100 and not t.endswith((",", ";")):
                flush_list()
                flush_para()
                # Document / Table labels
                if re.match(r"^(Document|Table|Figure)\s+", t, re.I):
                    chunks.append((tok.y0, f"### {t}"))
                elif is_chapter_heading(t) or re.match(r"^(Appendix|Chapter|Index|General)\b", t, re.I):
                    chunks.append((tok.y0, f"## {t}"))
                elif re.match(r"^\d+(\.\d+)*\s+\S", t):
                    num = t.split()[0]
                    depth = heading_depth(num)
                    chunks.append((tok.y0, "#" * depth + " " + t))
                else:
                    # section titles in italic
                    chunks.append((tok.y0, f"### {t}"))
                i += 1
                continue

        # lettered list a) b) — marker alone or with text
        m = re.match(r"^([a-z])\)\s*(.*)$", t)
        if m and (not m.group(2) or m.group(2)[0:1].islower() or len(m.group(2)) > 20):
            # avoid matching words like "e)specially" — require ) at marker
            if re.match(r"^[a-z]\)$", t) or re.match(r"^[a-z]\)\s+\S", t):
                flush_para()
                rest = m.group(2).strip()
                j = i + 1
                while j < len(kept):
                    nt = kept[j]
                    if nt.is_heading_font or nt.is_bullet or is_section_number(nt.text):
                        break
                    if re.match(r"^[a-z]\)\s*$", nt.text) or re.match(r"^[a-z]\)\s+\S", nt.text):
                        break
                    if not rest:
                        rest = nt.text
                        j += 1
                        continue
                    if nt.text and (nt.text[0].islower() or nt.x0 > 85):
                        # de-hyphenate
                        if rest.endswith("-") and nt.text[0].islower():
                            rest = rest[:-1] + nt.text
                        else:
                            rest = rest + " " + nt.text
                        j += 1
                        continue
                    break
                if list_y is None:
                    list_y = tok.y0
                list_items.append(f"{m.group(1)}) {rest}")
                i = j
                continue

        # numbered list 1. / 1)
        m = re.match(r"^(\d{1,2})[\.\)]\s+(.*)$", t)
        if m and m.group(2) and (m.group(2)[0].islower() or len(m.group(2)) > 40):
            flush_para()
            rest = m.group(2)
            j = i + 1
            while j < len(kept):
                nt = kept[j]
                if nt.is_heading_font or nt.is_bullet or is_section_number(nt.text):
                    break
                if re.match(r"^\d{1,2}[\.\)]\s+", nt.text):
                    break
                if nt.text and nt.text[0].islower():
                    rest = rest + " " + nt.text
                    j += 1
                    continue
                break
            if list_y is None:
                list_y = tok.y0
            list_items.append(f"{m.group(1)}. {rest}")
            i = j
            continue

        # Any non-list body line ends an open list (quotes/capitals/left margin)
        if list_items:
            # only continue list when clearly wrapped indent + lowercase
            if t and t[0].islower() and tok.x0 > 85:
                prev = list_items[-1]
                if prev.endswith("-"):
                    list_items[-1] = prev[:-1] + t
                else:
                    list_items[-1] = prev + " " + t
                i += 1
                continue
            flush_list()

        # Split "confined: a) … b) …" style inline lettered lists
        if re.search(r"\b[a-z]\)\s+\S", t) and not re.match(r"^[a-z]\)\s+", t):
            # lead-in before first a)
            mlead = re.split(r"(?=\b[a-z]\)\s+)", t)
            lead = mlead[0].strip()
            if lead:
                if para_y is None:
                    para_y = tok.y0
                para.append(lead)
                flush_para()
            for part in mlead[1:]:
                mm = re.match(r"^([a-z])\)\s+(.*)$", part.strip())
                if mm:
                    if list_y is None:
                        list_y = tok.y0
                    list_items.append(f"{mm.group(1)}) {mm.group(2).strip()}")
            i += 1
            continue

        # normal prose
        if para_y is None:
            para_y = tok.y0
        # new paragraph on larger vertical gap after sentence end
        if para and t and (t[0].isupper() or t[0] in "‘'“\""):
            if para[-1].rstrip().endswith((".", "?", "!")):
                prev = kept[i - 1] if i > 0 else tok
                if tok.y0 - prev.y0 > 14:
                    flush_para()
                    para_y = tok.y0
        # de-hyphenate across lines: "develop-" + "ment"
        if para and para[-1].endswith("-") and t and t[0].islower():
            para[-1] = para[-1][:-1] + t
        else:
            para.append(t)
        i += 1

    flush_list()
    flush_para()

    # inject callouts and tables by y
    for r in callouts:
        ct = text_in_rect(page, r)
        if ct and len(ct) > 20:
            chunks.append((r.y0, format_callout(ct)))
    for r, md in tables:
        chunks.append((r.y0, md))

    chunks.sort(key=lambda x: x[0])

    # de-dupe near-identical consecutive chunks
    body_parts: list[str] = []
    for _, text in chunks:
        text = text.strip()
        if not text:
            continue
        if body_parts and body_parts[-1] == text:
            continue
        body_parts.append(text)

    body = "\n\n".join(body_parts)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    # join broken "Chapters 4 and\n\n5. Whilst"
    body = re.sub(
        r"(Chapters?\s+\d+\s+and)\s*\n\n(\d+)\.\s+",
        r"\1 \2. ",
        body,
    )
    body = re.sub(r"(\w)-\s+(\w)", r"\1\2", body)
    # fix empty bullet in callouts
    body = re.sub(r">\s*-\s*\n+>\s*", "> - ", body)
    # strip residual full-line chrome only (never substrings inside tables/body)
    lines_out = []
    for ln in body.splitlines():
        if ln.strip() in CHROME_EXACT or ln.strip() in CHROME_TOKEN_ONLY:
            continue
        lines_out.append(ln)
    body = "\n".join(lines_out)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()

    pid = f"prose_p{pnum:03d}"
    return (
        f"<!-- el:start type=prose id={pid} page={pnum} -->\n"
        f"<!-- vision: CEFR 2001 PDF page {pnum} -->\n\n"
        f"{body}\n\n"
        f"<!-- el:end id={pid} -->\n"
    )


def main() -> None:
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 141
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 273
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF)
    for pnum in range(start, end + 1):
        md = format_page(doc[pnum - 1], pnum)
        path = OUT_DIR / f"page_{pnum:03d}.md"
        path.write_text(md, encoding="utf-8")
        if pnum % 20 == 0 or pnum in (start, end):
            print(f"wrote {path.name} ({len(md)} chars)", flush=True)
    print(f"Done pages {start}-{end} → {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
