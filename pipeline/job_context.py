"""JobContext loader — multi-job path/layout from job.json + profiles/*.json.

Single source of truth for Companion (and other) layout is JSON, not Python
defaults. Call ``load_job(job_id)`` once per process before reading
``pipeline.config`` path/layout attributes.

Preferred access after load::

    import pipeline.config as cfg
    cfg.PDF_PATH, cfg.FINAL_DIR, cfg.TOC_PAGE_RANGE, ...

Do not ``from pipeline.config import PDF_PATH`` — that freezes the name binding.
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PROFILES_DIR = ROOT / "profiles"

# Engine defaults (non-layout; not per-job knowledge)
TARGET_CHUNK_SIZE_DEFAULT = 25
MAX_RETRY_ATTEMPTS = 3
RENDER_SCALE = 2.0
CEFR_LEVELS_DEFAULT = frozenset(
    {"C2", "C1", "B2", "B1", "A2", "A1", "Pre-A1", "Pre A1"}
)

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

    def feature(self, name: str, default: bool = False) -> bool:
        """Return extraction.features[name] (profile merged under job)."""
        features = (self.extraction or {}).get("features") or {}
        if name not in features:
            return default
        return bool(features[name])


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
        return range(0)  # empty — no TOC pages unless job/profile declares them
    if isinstance(raw, range):
        return raw
    if isinstance(raw, (list, tuple)) and len(raw) == 2:
        start, end = int(raw[0]), int(raw[1])
        return range(start, end + 1)
    raise ValueError(f"Invalid toc_page_range: {raw!r}")


def _parse_known_tables(raw: Any) -> dict[int, tuple[str, str, str]]:
    if not raw:
        return {}
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
        return {}
    out: dict[tuple[int, int], tuple[str, str, str]] = {}
    if isinstance(raw, dict):
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


def _layout_state(layout: dict[str, Any], extraction: dict[str, Any]) -> dict[str, Any]:
    """Derive layout globals from job+profile JSON only (no Python Companion SoT)."""
    toc = extraction.get("toc_page_range")
    toc_range = _parse_toc_page_range(toc)

    section_blocks = deepcopy(layout.get("section_blocks") or [])
    known_tables = _parse_known_tables(layout.get("known_tables"))
    known_by_index = _parse_known_tables_by_index(layout.get("known_tables_by_index"))
    multipage = deepcopy(layout.get("multipage_artifacts") or {})

    chunk_size = extraction.get("chunk_size")
    target_chunk = int(chunk_size) if chunk_size is not None else TARGET_CHUNK_SIZE_DEFAULT

    levels = extraction.get("levels")
    if levels:
        cefr_levels = set(levels) | ({"Pre A1"} if "Pre-A1" in levels else set())
    else:
        cefr_levels = set(CEFR_LEVELS_DEFAULT)

    return {
        "TOC_PAGE_RANGE": toc_range,
        "SECTION_BLOCKS": section_blocks,
        "KNOWN_TABLES_FIGURES": known_tables,
        "KNOWN_TABLES_BY_INDEX": known_by_index,
        "MULTIPAGE_ARTIFACTS": multipage,
        "TARGET_CHUNK_SIZE": target_chunk,
        "CEFR_LEVELS": cefr_levels,
    }


def _bind_config(ctx: JobContext, layout_state: dict[str, Any]) -> None:
    """Push active job paths + layout onto pipeline.config attributes."""
    import pipeline.config as cfg

    cfg.PDF_PATH = ctx.pdf_path
    cfg.INVENTORIES_DIR = ctx.inventories_dir
    cfg.WORK_DIR = ctx.work_dir
    cfg.CHUNKS_DIR = ctx.chunks_dir
    cfg.RAW_DIR = ctx.raw_dir
    cfg.CLEANED_DIR = ctx.cleaned_dir
    cfg.METADATA_DIR = ctx.metadata_dir
    cfg.FINAL_DIR = ctx.final_dir
    cfg.ASSETS_FIGURES = ctx.assets_figures
    cfg.ASSETS_TABLES = ctx.assets_tables
    cfg.ROTATED_FOR_GROK_DIR = ctx.rotated_for_grok_dir
    cfg.ROTATED_FROM_GROK_DIR = ctx.rotated_from_grok_dir

    cfg.TOC_PAGE_RANGE = layout_state["TOC_PAGE_RANGE"]
    cfg.SECTION_BLOCKS = layout_state["SECTION_BLOCKS"]
    cfg.KNOWN_TABLES_FIGURES = layout_state["KNOWN_TABLES_FIGURES"]
    cfg.KNOWN_TABLES_BY_INDEX = layout_state["KNOWN_TABLES_BY_INDEX"]
    cfg.MULTIPAGE_ARTIFACTS = layout_state["MULTIPAGE_ARTIFACTS"]
    cfg.TARGET_CHUNK_SIZE = layout_state["TARGET_CHUNK_SIZE"]
    cfg.CEFR_LEVELS = layout_state["CEFR_LEVELS"]

    cfg._ACTIVE_CTX = ctx  # noqa: SLF001 — intentional module binding
    cfg._ACTIVE_JOB_ID = ctx.job_id  # noqa: SLF001


def load_job(job_id: str, *, reload: bool = False) -> JobContext:
    """Load job sidecar + profile and bind ``pipeline.config`` path/layout attrs.

    ``job_id`` is required (Phase B: no silent default to Companion).

    By default the same ``job_id`` returns the cached context without re-reading
    sidecars. Pass ``reload=True`` after editing ``job.json`` / profile mid-process.
    """
    global _ACTIVE_CTX, _ACTIVE_JOB_ID

    if not job_id or not str(job_id).strip():
        raise ValueError("load_job requires a non-empty job_id (pass --job <id>)")

    resolved_id = str(job_id).strip()
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
    if not job_data:
        raise FileNotFoundError(
            f"Job {resolved_id!r} has source.pdf but missing required {job_path}"
        )

    profile_name = job_data.get("profile") or "cefr_companion"
    profile_path = PROFILES_DIR / f"{profile_name}.json"
    profile_data = _load_json(profile_path)
    if not profile_data and not profile_path.exists():
        # Soft: empty profile is ok if job is self-contained
        profile_data = {}

    profile_extraction = profile_data.get("extraction") or {}
    job_extraction = job_data.get("extraction") or {}
    extraction = _deep_merge(profile_extraction, job_extraction)

    profile_output = profile_data.get("output") or {}
    job_output = job_data.get("output") or {}
    output_cfg = _deep_merge(profile_output, job_output)

    layout = job_data.get("layout") or {}
    # Optional profile-level layout defaults under job layout
    profile_layout = profile_data.get("layout") or {}
    if profile_layout:
        layout = _deep_merge(profile_layout, layout)

    source = job_data.get("source") or {}
    product = job_data.get("product") or {}

    source_file = source.get("file") or "source.pdf"
    work_dir = ROOT / "work" / resolved_id
    output_dir = ROOT / "output" / resolved_id
    metadata_dir = work_dir / "metadata"

    markdown_name = output_cfg.get("markdown_name") or f"{resolved_id}.md"
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

    layout_state = _layout_state(layout, extraction)
    _bind_config(ctx, layout_state)
    _ACTIVE_CTX = ctx
    _ACTIVE_JOB_ID = resolved_id
    return ctx


def get_active_job() -> JobContext | None:
    """Return the currently loaded JobContext, if any."""
    return _ACTIVE_CTX


def require_active_job() -> JobContext:
    """Return active JobContext or raise if load_job was never called."""
    if _ACTIVE_CTX is None:
        raise RuntimeError(
            "No job loaded. Call load_job(job_id) or pass --job <id> on the CLI first."
        )
    return _ACTIVE_CTX


def feature_enabled(name: str, default: bool = False) -> bool:
    """Whether extraction.features[name] is true for the active job.

    When no job is loaded, returns ``default`` (usually False so Companion-only
    detectors stay off until a job is bootstrapped).
    """
    ctx = _ACTIVE_CTX
    if ctx is None:
        return default
    return ctx.feature(name, default=default)


def final_markdown_path() -> Path:
    """Resolve the active job's Markdown deliverable path at call time."""
    ctx = _ACTIVE_CTX
    if ctx is not None:
        return ctx.final_markdown
    raise RuntimeError(
        "final_markdown_path() requires load_job(job_id) first (no default job)."
    )


def load_figures_registry() -> list[dict]:
    """Load figures_registry.json from the active job's metadata dir."""
    import pipeline.config as cfg

    path = cfg.METADATA_DIR / "figures_registry.json"
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
    """Page → (id, caption, type) for inventory hints (first figure only)."""
    out: dict[int, tuple[str, str, str]] = {}
    for fig in sorted(load_figures_registry(), key=lambda f: f["num"]):
        page = fig["page"]
        if page not in out:
            out[page] = (fig["id"], fig["title"], "figure")
    return out
