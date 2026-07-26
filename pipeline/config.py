import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = ROOT / "input" / "CEFR Companion Volume_eng.pdf"
INVENTORIES_DIR = ROOT / "inventories"
# Intermediates under work/ (not promoted)
WORK_DIR = ROOT / "work"
CHUNKS_DIR = WORK_DIR / "chunks"
RAW_DIR = WORK_DIR / "raw_extraction"
CLEANED_DIR = WORK_DIR / "cleaned"
METADATA_DIR = WORK_DIR / "metadata"
# Shippable deliverables only
FINAL_DIR = ROOT / "output"
ASSETS_FIGURES = FINAL_DIR / "assets" / "figures"
ASSETS_TABLES = FINAL_DIR / "assets" / "tables"
ROTATED_FOR_GROK_DIR = METADATA_DIR / "rotated_for_grok"
ROTATED_FROM_GROK_DIR = METADATA_DIR / "rotated_from_grok"

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
    # Chapter 2 taxonomy tables (not descriptor scales).
    33: (
        "table_03_macro_functional_basis",
        "Table 3 – Macro-functional basis of CEFR categories for communicative language activities",
        "table",
    ),
}

# Multi-table pages: (page, table_index) → known table meta (after callouts filtered).
KNOWN_TABLES_BY_INDEX: dict[tuple[int, int], tuple[str, str, str]] = {
    # p.35: index 0 = narrative callout; index 1 = Table 4 strategy matrix
    (35, 0): (
        "callout_can_do_descriptors_as_competence",
        "“Can do” descriptors as competence",
        "callout",
    ),
    (35, 1): (
        "table_04_communicative_language_strategies",
        "Table 4 – Communicative language strategies in the CEFR",
        "table",
    ),
    (29, 0): (
        "callout_a_reminder_of_cefr_2001_chapters",
        "A reminder of CEFR 2001 chapters",
        "callout",
    ),
    (44, 0): (
        "table_05_descriptor_use",
        "Table 5 – The use of CEFR illustrative descriptors for different purposes",
        "table",
    ),
}


def known_figures_list_by_page() -> dict[int, list[tuple[str, str, str]]]:
    """Page → list of (id, caption, type) for multi-figure pages."""
    out: dict[int, list[tuple[str, str, str]]] = {}
    for fig in load_figures_registry():
        out.setdefault(fig["page"], []).append(
            (fig["id"], fig["title"], "figure")
        )
    return out

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
    """Page → (id, caption, type) for inventory hints.

    When multiple figures share a page, returns the **first** by figure number
    (legacy single-slot callers). Prefer ``known_figures_list_by_page`` or
    ``extractors.figures.figures_for_page`` for multi-figure pages.
    """
    out: dict[int, tuple[str, str, str]] = {}
    for fig in sorted(load_figures_registry(), key=lambda f: f["num"]):
        page = fig["page"]
        if page not in out:
            out[page] = (fig["id"], fig["title"], "figure")
    return out