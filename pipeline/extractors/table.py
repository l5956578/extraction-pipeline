import pdfplumber

from pipeline.utils import table_to_markdown


def extract_tables(page_idx: int, pdf_path) -> list[list[list]]:
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_idx]
        return page.extract_tables() or []


def tables_to_markdown(tables: list[list[list]]) -> str:
    parts = []
    for table in tables:
        md = table_to_markdown(table)
        if md:
            parts.append(md)
    return "\n\n".join(parts)