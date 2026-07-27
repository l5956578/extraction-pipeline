"""Pipeline engine constants + active-job path/layout attributes.

**Access pattern (Phase B):** always use module attributes so rebinding works::

    import pipeline.config as cfg
    load_job("cefr-companion-2020")   # or CLI bootstrap
    print(cfg.PDF_PATH, cfg.FINAL_DIR, cfg.TOC_PAGE_RANGE)

Do **not** ``from pipeline.config import PDF_PATH`` — that freezes a name at
import time and will not see later ``load_job`` updates.

Layout SoT is ``input/<job>/job.json`` + ``profiles/*.json`` only (no Python
Companion dual-write). Engine-only constants below never come from jobs.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pipeline.job_context import (
    JobContext,
    feature_enabled,
    final_markdown_path,
    get_active_job,
    known_figures_by_page,
    known_figures_list_by_page,
    load_figures_registry,
    load_job,
    require_active_job,
)

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Repo root & engine constants (not per-job)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
PROFILES_DIR = ROOT / "profiles"

TARGET_CHUNK_SIZE = 25  # rebound by load_job from extraction.chunk_size
MAX_RETRY_ATTEMPTS = 3
RENDER_SCALE = 2.0

CEFR_LEVELS: set[str] = {
    "C2",
    "C1",
    "B2",
    "B1",
    "A2",
    "A1",
    "Pre-A1",
    "Pre A1",
}

# ---------------------------------------------------------------------------
# Path / layout attributes — empty until load_job(job_id)
# ---------------------------------------------------------------------------
# Placeholders make accidental use before bootstrap fail loudly (missing PDF).
_UNLOADED = ROOT / "_no_job_loaded"

PDF_PATH: Path = _UNLOADED / "source.pdf"
INVENTORIES_DIR: Path = _UNLOADED / "inventories"
WORK_DIR: Path = _UNLOADED
CHUNKS_DIR: Path = _UNLOADED / "chunks"
RAW_DIR: Path = _UNLOADED / "raw_extraction"
CLEANED_DIR: Path = _UNLOADED / "cleaned"
METADATA_DIR: Path = _UNLOADED / "metadata"
FINAL_DIR: Path = _UNLOADED
ASSETS_FIGURES: Path = _UNLOADED / "assets" / "figures"
ASSETS_TABLES: Path = _UNLOADED / "assets" / "tables"
ROTATED_FOR_GROK_DIR: Path = _UNLOADED / "rotated_for_grok"
ROTATED_FROM_GROK_DIR: Path = _UNLOADED / "rotated_from_grok"

# Layout (from job.json + profile only)
TOC_PAGE_RANGE: range = range(0)
SECTION_BLOCKS: list[dict] = []
KNOWN_TABLES_FIGURES: dict[int, tuple[str, str, str]] = {}
KNOWN_TABLES_BY_INDEX: dict[tuple[int, int], tuple[str, str, str]] = {}
MULTIPAGE_ARTIFACTS: dict[str, dict] = {}

# Active job (set by load_job via job_context._bind_config)
_ACTIVE_CTX: JobContext | None = None
_ACTIVE_JOB_ID: str | None = None

__all__ = [
    "ROOT",
    "PROFILES_DIR",
    "TARGET_CHUNK_SIZE",
    "MAX_RETRY_ATTEMPTS",
    "RENDER_SCALE",
    "CEFR_LEVELS",
    "PDF_PATH",
    "INVENTORIES_DIR",
    "WORK_DIR",
    "CHUNKS_DIR",
    "RAW_DIR",
    "CLEANED_DIR",
    "METADATA_DIR",
    "FINAL_DIR",
    "ASSETS_FIGURES",
    "ASSETS_TABLES",
    "ROTATED_FOR_GROK_DIR",
    "ROTATED_FROM_GROK_DIR",
    "TOC_PAGE_RANGE",
    "SECTION_BLOCKS",
    "KNOWN_TABLES_FIGURES",
    "KNOWN_TABLES_BY_INDEX",
    "MULTIPAGE_ARTIFACTS",
    "JobContext",
    "load_job",
    "get_active_job",
    "require_active_job",
    "feature_enabled",
    "final_markdown_path",
    "load_figures_registry",
    "known_figures_by_page",
    "known_figures_list_by_page",
]
