import io
import os
import re
import tempfile

import fitz
import pdfplumber
import pytesseract
from PIL import Image

from pipeline.config import RENDER_SCALE
from pipeline.title_fix import fix_rotated_title
from pipeline.utils import english_word_score, table_to_markdown, is_gibberish


def _reverse_word(word: str) -> str:
    leading = ""
    trailing = ""
    core = word
    while core and not core[0].isalnum():
        leading += core[0]
        core = core[1:]
    while core and not core[-1].isalnum():
        trailing = core[-1] + trailing
        core = core[:-1]
    if len(core) > 2 and core.isalpha():
        return leading + core[::-1] + trailing
    return word


def _reverse_line(line: str) -> str:
    words = re.findall(r"\S+|\s+", line)
    tokens = [w for w in words if w.strip()]
    rev = [_reverse_word(w) for w in reversed(tokens)]
    return " ".join(rev)


def _table_readable(text: str) -> bool:
    if not text or len(text.strip()) < 40:
        return False
    score = english_word_score(text)
    if score < 0.12:
        return False
    levels = re.findall(
        r"\b(C2|C1|B2\+?|B1\+?|A2\+?|A1\+?|Pre-A1|Pre A1)\b",
        text,
        re.I,
    )
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text)
    if len(levels) >= 2 and len(words) >= 8:
        return True
    if score > 0.25 and len(words) >= 12:
        return True
    return len(levels) >= 1 and score > 0.18 and len(words) >= 6


def _show_rotation(rotation: int) -> int:
    if rotation == 270:
        return 270
    if rotation == 180:
        return 180
    return 90


def derotated_pdfplumber_tables(
    page_idx: int,
    pdf_path,
    rotation: int = 90,
) -> list[list[list]]:
    """Render page upright in a temp PDF and extract tables with pdfplumber."""
    src = fitz.open(pdf_path)
    if page_idx < 0 or page_idx >= len(src):
        src.close()
        return []
    page = src[page_idx]
    rot = _show_rotation(rotation)
    tmp_doc = fitz.open()
    if rot in (90, 270):
        width, height = page.rect.height, page.rect.width
    else:
        width, height = page.rect.width, page.rect.height
    new_page = tmp_doc.new_page(width=width, height=height)
    new_page.show_pdf_page(new_page.rect, src, page_idx, rotate=rot)
    tmp_path = tempfile.mktemp(suffix=".pdf")
    try:
        tmp_doc.save(tmp_path)
        with pdfplumber.open(tmp_path) as pdf:
            if not pdf.pages:
                return []
            tables = pdf.pages[0].extract_tables() or []
    finally:
        tmp_doc.close()
        src.close()
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    return tables


def extract_rotated_text(page: fitz.Page, rotation: int = 90) -> str:
    """OCR rotated page text with known rotation angle."""
    return ocr_page_to_text(page, rotation)


def render_rotated_page(page: fitz.Page, rotation: int) -> Image.Image:
    mat = fitz.Matrix(RENDER_SCALE, RENDER_SCALE)
    pix = page.get_pixmap(matrix=mat)
    base = Image.open(io.BytesIO(pix.tobytes("png")))
    if rotation:
        return base.rotate(rotation, expand=True)
    return base


def best_rotation_image(page: fitz.Page) -> tuple[Image.Image, int]:
    mat = fitz.Matrix(RENDER_SCALE, RENDER_SCALE)
    pix = page.get_pixmap(matrix=mat)
    base = Image.open(io.BytesIO(pix.tobytes("png")))
    best_img = base
    best_angle = 0
    best_score = -1.0
    for angle in (0, 90, 270):
        img = base.rotate(angle, expand=True)
        text = pytesseract.image_to_string(img)
        score = english_word_score(text)
        if score > best_score:
            best_score = score
            best_img = img
            best_angle = angle
    return best_img, best_angle


def ocr_page_to_text(page: fitz.Page, rotation: int | None = None) -> str:
    if rotation is not None:
        img = render_rotated_page(page, rotation)
    else:
        img, _ = best_rotation_image(page)
    return pytesseract.image_to_string(img)


def _reverse_table_cells(tables: list[list[list]]) -> list[list[list]]:
    out = []
    for table in tables:
        rows = []
        for row in table:
            cells = []
            for cell in row:
                if cell is None:
                    cells.append("")
                else:
                    text = str(cell)
                    rev = "\n".join(_reverse_line(ln) for ln in text.splitlines())
                    cells.append(rev)
            rows.append(cells)
        out.append(rows)
    return out


def _ocr_page_to_table(page: fitz.Page, rotation: int = 90) -> str:
    img = render_rotated_page(page, rotation)
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    rows: dict[int, list[tuple[int, str]]] = {}
    n = len(data["text"])
    for i in range(n):
        txt = (data["text"][i] or "").strip()
        if not txt:
            continue
        top = data["top"][i]
        left = data["left"][i]
        row_key = top // 20
        rows.setdefault(row_key, []).append((left, txt))

    table_rows = []
    for key in sorted(rows.keys()):
        cells = [t for _, t in sorted(rows[key], key=lambda x: x[0])]
        if cells:
            table_rows.append(cells)

    if len(table_rows) < 2:
        return ocr_page_to_text(page, rotation)

    normalized = []
    for row in table_rows:
        if len(row) == 1:
            if re.match(r"^(A1|A2|B1|B2|C1|C2|Pre-A1)$", row[0], re.I):
                normalized.append([row[0], ""])
            else:
                normalized.append(["", row[0]])
        else:
            normalized.append(row[:2] if len(row) > 2 else row)

    return table_to_markdown(normalized)


def _tables_to_markdown(tables: list[list[list]]) -> str:
    parts = []
    for table in tables:
        md = table_to_markdown(table)
        if md.strip():
            parts.append(md)
    return "\n\n".join(parts)


def extract_rotated_tables(
    page_idx: int,
    page: fitz.Page,
    pdf_path,
    rotation: int = 90,
    force_ocr: bool = False,
) -> str:
    if force_ocr:
        return _ocr_with_best_angle(page, rotation)

    tables = derotated_pdfplumber_tables(page_idx, pdf_path, rotation)
    if tables:
        reversed_tables = _reverse_table_cells(tables)
        fixed = [
            [
                [fix_rotated_title(str(c)) if c else "" for c in row]
                for row in table
            ]
            for table in reversed_tables
        ]
        sample = " ".join(str(c) for row in fixed[:8] for c in row if c)
        md = _tables_to_markdown(fixed)
        if _table_readable(sample) and not is_gibberish(sample):
            return md

    with pdfplumber.open(pdf_path) as pdf:
        raw_tables = pdf.pages[page_idx].extract_tables() or []
    if raw_tables:
        fixed = _reverse_table_cells(raw_tables)
        sample = " ".join(str(c) for row in fixed[:5] for c in row if c)
        md = _tables_to_markdown(fixed)
        if _table_readable(sample) and not is_gibberish(sample):
            return md

    return _ocr_with_best_angle(page, rotation)


def _ocr_with_best_angle(page: fitz.Page, preferred_rotation: int = 90) -> str:
    body = _ocr_page_to_table(page, preferred_rotation)
    if _table_readable(body):
        return body
    _, best_angle = best_rotation_image(page)
    if best_angle != preferred_rotation:
        body = _ocr_page_to_table(page, best_angle)
        if _table_readable(body):
            return body
    return body


def extract_rotated_element(
    page_idx: int,
    page: fitz.Page,
    pdf_path,
    el: dict,
) -> str:
    rotation = el.get("rotation") or 90
    force_ocr = el.get("text_direction") == "ocr" and el.get("force_ocr")
    return extract_rotated_tables(
        page_idx, page, pdf_path, rotation=rotation, force_ocr=bool(force_ocr)
    )


def ocr_page_to_table(page: fitz.Page) -> str:
    return _ocr_page_to_table(page, 90)