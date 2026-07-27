"""Figure extraction — PNG crops for visual figures; skip raster for text diagrams."""

from __future__ import annotations

import json
import re
from pathlib import Path

import fitz

import pipeline.config as _cfg
from pipeline.config import ASSETS_FIGURES, PDF_PATH
from pipeline.utils import ensure_dir


def _registry_path() -> Path:
    return _cfg.METADATA_DIR / "figures_registry.json"


def load_figures_registry() -> list[dict]:
    path = _registry_path()
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("figures", [])


def figures_for_page(page_num: int) -> list[dict]:
    return [f for f in load_figures_registry() if f["page"] == page_num]


def registry_by_id() -> dict[str, dict]:
    return {f["id"]: f for f in load_figures_registry()}


def should_extract_png(fig: dict) -> bool:
    return fig.get("render_as") == "png"


def crop_figure_png(page: fitz.Page, fig: dict, scale: float = 2.0) -> str | None:
    """Render a figure region to assets/figures/{id}.png using registry crop box."""
    if not should_extract_png(fig):
        return None
    ensure_dir(ASSETS_FIGURES)
    rect = page.rect
    crop = fig.get("crop") or {"y0": 0.2, "y1": 0.9, "x0": 0.05, "x1": 0.95}
    clip = fitz.Rect(
        rect.x0 + rect.width * crop["x0"],
        rect.y0 + rect.height * crop["y0"],
        rect.x0 + rect.width * crop["x1"],
        rect.y0 + rect.height * crop["y1"],
    )
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, clip=clip)
    out_path = ASSETS_FIGURES / f"{fig['id']}.png"
    pix.save(out_path)
    return f"assets/figures/{out_path.name}"


def extract_figure_04_embedded(page: fitz.Page) -> str | None:
    imgs = page.get_images(full=True)
    if not imgs:
        return None
    ensure_dir(ASSETS_FIGURES)
    xref = imgs[0][0]
    base = page.parent.extract_image(xref)
    out_path = ASSETS_FIGURES / "figure_04_rainbow.png"
    out_path.write_bytes(base["image"])
    return f"assets/figures/{out_path.name}"


def extract_page_figure_assets(page: fitz.Page, page_num: int) -> dict[str, str]:
    assets: dict[str, str] = {}
    for fig in figures_for_page(page_num):
        if not should_extract_png(fig):
            continue
        if fig["id"] == "figure_04_rainbow":
            path = extract_figure_04_embedded(page)
        else:
            path = crop_figure_png(page, fig)
        if path:
            assets[fig["id"]] = path
    return assets


def find_figure_refs(text: str) -> list[str]:
    return re.findall(r"(Figure\s+\d+[^.\n]*)", text, re.I)
