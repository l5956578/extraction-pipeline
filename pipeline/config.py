import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = ROOT / "CEFR Companion Volume_eng.pdf"
CHUNKS_DIR = ROOT / "chunks"
INVENTORIES_DIR = ROOT / "inventories"
RAW_DIR = ROOT / "raw_extraction"
CLEANED_DIR = ROOT / "cleaned"
FINAL_DIR = ROOT / "final_output"
ASSETS_FIGURES = FINAL_DIR / "assets" / "figures"
ASSETS_TABLES = FINAL_DIR / "assets" / "tables"
METADATA_DIR = ROOT / "metadata"

TARGET_CHUNK_SIZE = 25
MAX_RETRY_ATTEMPTS = 3
RENDER_SCALE = 2.0

CEFR_LEVELS = {"C2", "C1", "B2", "B1", "A2", "A1", "Pre-A1", "Pre A1"}

# PDF pages with dot-leader TOC (title left, page number right on same row).
TOC_PAGE_RANGE = range(5, 10)

SECTION_BLOCKS = [
    {
        "id": "table_self_assessment_grid",
        "display_name": "Self-Assessment Grid (Expanded with Online Interaction and Mediation)",
        "type": "section_block",
        "product_tiers": ["base"],
        "page_start": 177,
        "page_end": 181,
    },
]

KNOWN_TABLES_FIGURES = {
    23: ("table_01_descriptive_scheme_updates", "Table 1 – The CEFR descriptive scheme and illustrative descriptors: updates and additions", "table"),
    24: ("table_02_summary_descriptor_changes", "Table 2 – Summary of changes to the illustrative descriptors", "table"),
}

MULTIPAGE_ARTIFACTS: dict[str, dict] = {
    "table_02_summary_descriptor_changes": {"page_start": 24, "page_end": 25, "merge": "pdfplumber_all"},
    "scale_vocabulary_control": {"page_start": 132, "page_end": 133, "merge": "pdfplumber_all"},
}


def load_figures_registry() -> list[dict]:
    path = METADATA_DIR / "figures_registry.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("figures", [])


def known_figures_by_page() -> dict[int, tuple[str, str, str]]:
    """Page → (id, caption, type) for inventory hints."""
    out: dict[int, tuple[str, str, str]] = {}
    for fig in load_figures_registry():
        out[fig["page"]] = (fig["id"], fig["title"], "figure")
    return out