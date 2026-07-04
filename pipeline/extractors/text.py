import fitz

from pipeline.utils import clean_running_headers


def extract_text(page: fitz.Page) -> str:
    return clean_running_headers(page.get_text("text"))