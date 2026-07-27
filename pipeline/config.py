"""Pipeline configuration and multi-job JobContext loader.

Phase A: paths are namespaced by job id under input|work|output/<job-id>/.
Module-level path globals remain for backward compatibility; load_job()
(re)binds them so existing ``from pipeline.config import PDF_PATH`` keeps working
after import (default job auto-loaded at module init).
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PROFILES_DIR = ROOT / "profiles"
DEFAULT_JOB_ID = "cefr-companion-2020"

# ---------------------------------------------------------------------------
# Engine defaults (non-layout)
# ---------------------------------------------------------------------------
TARGET_CHUNK_SIZE = 25
MAX_RETRY_ATTEMPTS = 3
RENDER_SCALE = 2.0

CEFR_LEVELS = {"C2", "C1", "B2", "B1", "A2", "A1", "Pre-A1", "Pre A1"}

# ---------------------------------------------------------------------------
# Companion layout constants — Python fallbacks (job.json overrides when present)
# ---------------------------------------------------------------------------
_DEFAULT_TOC_PAGE_RANGE = range(5, 10)

_DEFAULT_SECTION_BLOCKS: list[dict] = [
    {
        "id": "table_self_assessment_grid",
        "display_name": "Self-Assessment Grid (Expanded with Online Interaction and Mediation)",
        "type": "section_block",
        "product_tiers": ["base"],
        "page_start": 177,
        "page_end": 181,
    },
]

_DEFAULT_KNOWN_TABLES_FIGURES: dict[int, tuple[str, str, str]] = {
    23: (
        "table_01_descriptive_scheme_updates",
        "Table 1 – The CEFR descriptive scheme and illustrative descriptors: updates and additions",
        "table",
    ),
    24: (
        "table_02_summary_descriptor_changes",
        "Table 2 – Summary of changes to the illustrative descriptors",
        "table",
    ),
    33: (
        "table_03_macro_functional_basis",
        "Table 3 – Macro-functional basis of CEFR categories for communicative language activities",
        "table",
    ),
}

_DEFAULT_KNOWN_TABLES_BY_INDEX: dict[tuple[int, int], tuple[str, str, str]] = {
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

_DEFAULT_MULTIPAGE_ARTIFACTS: dict[str, dict] = {
    "table_02_summary_descriptor_changes": {
        "page_start": 24,
        "page_end": 25,
        "merge": "pdfplumber_all",
    },
    "scale_vocabulary_control": {
        "page_start": 132,
        "page_end": 133,
        "merge": "pdfplumber_all",
    },
}

# Active layout (rebound by load_job); start as Python fallbacks.
TOC_PAGE_RANGE = _DEFAULT_TOC_PAGE_RANGE
SECTION_BLOCKS = deepcopy(_DEFAULT_SECTION_BLOCKS)
KNOWN_TABLES_FIGURES = dict(_DEFAULT_KNOWN_TABLES_FIGURES)
KNOWN_TABLES_BY_INDEX: dict[tuple[int, int], tuple[str, str, str]] = dict(
    _DEFAULT_KNOWN_TABLES_BY_INDEX
)
MULTIPAGE_ARTIFACTS: dict[str, dict] = deepcopy(_DEFAULT_MULTIPAGE_ARTIFACTS)

# Path globals — rebound by load_job (placeholders until first load).
PDF_PATH = ROOT / "input" / DEFAULT_JOB_ID / "source.pdf"
INVENTORIES_DIR = ROOT / "work" / DEFAULT_JOB_ID / "inventories"
WORK_DIR = ROOT / "work" / DEFAULT_JOB_ID
CHUNKS_DIR = WORK_DIR / "chunks"
RAW_DIR = WORK_DIR / "raw_extraction"
CLEANED_DIR = WORK_DIR / "cleaned"
METADATA_DIR = WORK_DIR / "metadata"
FINAL_DIR = ROOT / "output" / DEFAULT_JOB_ID
ASSETS_FIGURES = FINAL_DIR / "assets" / "figures"
ASSETS_TABLES = FINAL_DIR / "assets" / "tables"
ROTATED_FOR_GROK_DIR = METADATA_DIR / "rotated_for_grok"
ROTATED_FROM_GROK_DIR = METADATA_DIR / "rotated_from_grok"

# Active job context (set by load_job).
_ACTIVE_CTX: "JobContext | None" = None
_ACTIVE_JOB_ID: str | None = None


@dataclass
class JobContext:
    """Resolved paths and layout for one extraction job."""

    job_id: str
    root: Path
    input_dir: Path
    work_dir: Path
    output_dir: Path
    pdf_path: Path
    inventories_dir: Path
    chunks_dir: Path
    raw_dir: Path
    cleaned_dir: Path
    metadata_dir: Path
    final_dir: Path
    assets_figures: Path
    assets_tables: Path
    rotated_for_grok_dir: Path
    rotated_from_grok_dir: Path
    profile: str
    title: str
    status: str
    markdown_name: str
    original_filename: str
    product: dict[str, Any] = field(default_factory=dict)
    extraction: dict[str, Any] = field(default_factory=dict)
    layout: dict[str, Any] = field(default_factory=dict)
    job_data: dict[str, Any] = field(default_factory=dict)
    profile_data: dict[str, Any] = field(default_factory=dict)

    @property
    def final_markdown(self) -> Path:
        return self.final_dir / self.markdown_name


def _deep_merge(base: dict, override: dict) -> dict:
    out = deepcopy(base)
    for key, val in override.items():
        if key in out and isinstance(out[key], dict) and isinstance(val, dict):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = deepcopy(val)
    return out


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_toc_page_range(raw: Any) -> range:
    """job.json uses inclusive [start, end]; Python range is end-exclusive."""
    if raw is None:
        return _DEFAULT_TOC_PAGE_RANGE
    if isinstance(raw, range):
        return raw
    if isinstance(raw, (list, tuple)) and len(raw) == 2:
        start, end = int(raw[0]), int(raw[1])
        return range(start, end + 1)
    raise ValueError(f"Invalid toc_page_range: {raw!r}")


def _parse_known_tables(raw: Any) -> dict[int, tuple[str, str, str]]:
    if not raw:
        return dict(_DEFAULT_KNOWN_TABLES_FIGURES)
    out: dict[int, tuple[str, str, str]] = {}
    for page_key, meta in raw.items():
        page = int(page_key)
        if isinstance(meta, (list, tuple)) and len(meta) >= 3:
            out[page] = (str(meta[0]), str(meta[1]), str(meta[2]))
        elif isinstance(meta, dict):
            out[page] = (meta["id"], meta["title"], meta.get("type", "table"))
        else:
            raise ValueError(f"Invalid known_tables entry for page {page_key}: {meta!r}")
    return out


def _parse_known_tables_by_index(
    raw: Any,
) -> dict[tuple[int, int], tuple[str, str, str]]:
    if not raw:
        return dict(_DEFAULT_KNOWN_TABLES_BY_INDEX)
    out: dict[tuple[int, int], tuple[str, str, str]] = {}
    if isinstance(raw, dict):
        # Support "35:0" or "35,0" string keys
        for key, meta in raw.items():
            if isinstance(key, str) and (":" in key or "," in key):
                sep = ":" if ":" in key else ","
                page_s, idx_s = key.split(sep, 1)
                page, index = int(page_s), int(idx_s)
            else:
                raise ValueError(f"Invalid known_tables_by_index key: {key!r}")
            if isinstance(meta, dict):
                out[(page, index)] = (
                    meta["id"],
                    meta["title"],
                    meta.get("type", "table"),
                )
            else:
                out[(page, index)] = (str(meta[0]), str(meta[1]), str(meta[2]))
        return out
    if isinstance(raw, list):
        for entry in raw:
            page = int(entry["page"])
            index = int(entry["index"])
            out[(page, index)] = (
                entry["id"],
                entry["title"],
                entry.get("type", "table"),
            )
        return out
    raise ValueError(f"Invalid known_tables_by_index: {type(raw)}")


def _apply_layout_from_job(layout: dict[str, Any], extraction: dict[str, Any]) -> None:
    """Update module-level layout globals from job/profile data (fallback to Python)."""
    global TOC_PAGE_RANGE, SECTION_BLOCKS, KNOWN_TABLES_FIGURES
    global KNOWN_TABLES_BY_INDEX, MULTIPAGE_ARTIFACTS, TARGET_CHUNK_SIZE, CEFR_LEVELS

    toc = extraction.get("toc_page_range")
    if toc is not None:
        TOC_PAGE_RANGE = _parse_toc_page_range(toc)
    else:
        TOC_PAGE_RANGE = _DEFAULT_TOC_PAGE_RANGE

    if layout.get("section_blocks"):
        SECTION_BLOCKS = deepcopy(layout["section_blocks"])
    else:
        SECTION_BLOCKS = deepcopy(_DEFAULT_SECTION_BLOCKS)

    if layout.get("known_tables"):
        KNOWN_TABLES_FIGURES = _parse_known_tables(layout["known_tables"])
    else:
        KNOWN_TABLES_FIGURES = dict(_DEFAULT_KNOWN_TABLES_FIGURES)

    if layout.get("known_tables_by_index") is not None:
        KNOWN_TABLES_BY_INDEX = _parse_known_tables_by_index(
            layout["known_tables_by_index"]
        )
    else:
        KNOWN_TABLES_BY_INDEX = dict(_DEFAULT_KNOWN_TABLES_BY_INDEX)

    if layout.get("multipage_artifacts"):
        MULTIPAGE_ARTIFACTS = deepcopy(layout["multipage_artifacts"])
    else:
        MULTIPAGE_ARTIFACTS = deepcopy(_DEFAULT_MULTIPAGE_ARTIFACTS)

    chunk_size = extraction.get("chunk_size")
    if chunk_size is not None:
        TARGET_CHUNK_SIZE = int(chunk_size)

    levels = extraction.get("levels")
    if levels:
        # Keep "Pre A1" alias used by some extractors
        CEFR_LEVELS = set(levels) | ({"Pre A1"} if "Pre-A1" in levels else set())


def _bind_path_globals(ctx: JobContext) -> None:
    global PDF_PATH, INVENTORIES_DIR, WORK_DIR, CHUNKS_DIR, RAW_DIR, CLEANED_DIR
    global METADATA_DIR, FINAL_DIR, ASSETS_FIGURES, ASSETS_TABLES
    global ROTATED_FOR_GROK_DIR, ROTATED_FROM_GROK_DIR

    PDF_PATH = ctx.pdf_path
    INVENTORIES_DIR = ctx.inventories_dir
    WORK_DIR = ctx.work_dir
    CHUNKS_DIR = ctx.chunks_dir
    RAW_DIR = ctx.raw_dir
    CLEANED_DIR = ctx.cleaned_dir
    METADATA_DIR = ctx.metadata_dir
    FINAL_DIR = ctx.final_dir
    ASSETS_FIGURES = ctx.assets_figures
    ASSETS_TABLES = ctx.assets_tables
    ROTATED_FOR_GROK_DIR = ctx.rotated_for_grok_dir
    ROTATED_FROM_GROK_DIR = ctx.rotated_from_grok_dir


def load_job(job_id: str | None = None, *, reload: bool = False) -> JobContext:
    """Load job sidecar + profile and bind module-level path/layout globals.

    Phase A: ``job_id is None`` defaults to ``cefr-companion-2020``.

    By default the same ``job_id`` returns the cached context without re-reading
    sidecars (one process ≈ one load). Pass ``reload=True`` after editing
    ``job.json`` / profile so layout globals are refreshed from disk.
    """
    global _ACTIVE_CTX, _ACTIVE_JOB_ID

    resolved_id = job_id or DEFAULT_JOB_ID
    if (
        not reload
        and _ACTIVE_CTX is not None
        and _ACTIVE_JOB_ID == resolved_id
    ):
        return _ACTIVE_CTX

    input_dir = ROOT / "input" / resolved_id
    job_path = input_dir / "job.json"
    job_data = _load_json(job_path)
    if not job_data and not (input_dir / "source.pdf").exists():
        raise FileNotFoundError(
            f"Unknown job {resolved_id!r}: missing {job_path} and source.pdf"
        )

    profile_name = job_data.get("profile") or "cefr_companion"
    profile_data = _load_json(PROFILES_DIR / f"{profile_name}.json")

    # Merge profile extraction defaults under job extraction overrides.
    profile_extraction = profile_data.get("extraction") or {}
    job_extraction = job_data.get("extraction") or {}
    extraction = _deep_merge(profile_extraction, job_extraction)

    profile_output = profile_data.get("output") or {}
    job_output = job_data.get("output") or {}
    output_cfg = _deep_merge(profile_output, job_output)

    layout = job_data.get("layout") or {}
    source = job_data.get("source") or {}
    product = job_data.get("product") or {}

    source_file = source.get("file") or "source.pdf"
    work_dir = ROOT / "work" / resolved_id
    output_dir = ROOT / "output" / resolved_id
    metadata_dir = work_dir / "metadata"

    markdown_name = output_cfg.get("markdown_name") or "CEFR_Companion_Volume.md"
    original_filename = (
        source.get("original_filename")
        or source.get("published_filename")
        or source_file
    )

    ctx = JobContext(
        job_id=resolved_id,
        root=ROOT,
        input_dir=input_dir,
        work_dir=work_dir,
        output_dir=output_dir,
        pdf_path=input_dir / source_file,
        inventories_dir=work_dir / "inventories",
        chunks_dir=work_dir / "chunks",
        raw_dir=work_dir / "raw_extraction",
        cleaned_dir=work_dir / "cleaned",
        metadata_dir=metadata_dir,
        final_dir=output_dir,
        assets_figures=output_dir / "assets" / "figures",
        assets_tables=output_dir / "assets" / "tables",
        rotated_for_grok_dir=metadata_dir / "rotated_for_grok",
        rotated_from_grok_dir=metadata_dir / "rotated_from_grok",
        profile=profile_name,
        title=job_data.get("title") or resolved_id,
        status=job_data.get("status") or "draft",
        markdown_name=markdown_name,
        original_filename=original_filename,
        product=product,
        extraction=extraction,
        layout=layout,
        job_data=job_data,
        profile_data=profile_data,
    )

    _apply_layout_from_job(layout, extraction)
    _bind_path_globals(ctx)
    _ACTIVE_CTX = ctx
    _ACTIVE_JOB_ID = resolved_id
    return ctx


def get_active_job() -> JobContext | None:
    """Return the currently loaded JobContext, if any."""
    return _ACTIVE_CTX


def final_markdown_path() -> Path:
    """Resolve the active job's Markdown deliverable path at call time.

    Prefer ``JobContext.final_markdown`` (from job.json ``output.markdown_name``);
    fall back to ``FINAL_DIR / "CEFR_Companion_Volume.md"`` for Companion.
    """
    ctx = _ACTIVE_CTX
    if ctx is not None:
        return ctx.final_markdown
    return FINAL_DIR / "CEFR_Companion_Volume.md"


def load_figures_registry() -> list[dict]:
    path = METADATA_DIR / "figures_registry.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("figures", [])


def known_figures_list_by_page() -> dict[int, list[tuple[str, str, str]]]:
    """Page → list of (id, caption, type) for multi-figure pages."""
    out: dict[int, list[tuple[str, str, str]]] = {}
    for fig in load_figures_registry():
        out.setdefault(fig["page"], []).append(
            (fig["id"], fig["title"], "figure")
        )
    return out


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


# Phase A compatibility: auto-load default job so imports resolve to new paths.
load_job(None)
