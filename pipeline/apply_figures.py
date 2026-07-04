"""Patch final_output Markdown with correct figure representations."""

from __future__ import annotations

import json
import re
from pathlib import Path

import fitz

from pipeline.config import FINAL_DIR, PDF_PATH, METADATA_DIR
from pipeline.extractors.figures import crop_figure_png, extract_figure_04_embedded, load_figures_registry
from pipeline.figure_inject import inject_png_figure, inject_text_diagram
from pipeline.figures_catalog import FIGURE_CONTENT, figure_block
from pipeline.toc_zone import strip_toc_figure_artifacts, toc_bounds


def _ensure_png_assets() -> dict[str, str]:
    doc = fitz.open(PDF_PATH)
    assets: dict[str, str] = {}
    for fig in load_figures_registry():
        if fig.get("render_as") != "png":
            continue
        page = doc[fig["page"] - 1]
        if fig["id"] == "figure_04_rainbow":
            path = extract_figure_04_embedded(page)
        else:
            path = crop_figure_png(page, fig)
        if path:
            assets[fig["id"]] = path
    doc.close()
    return assets


def apply_figures_to_markdown(md_path: Path) -> dict:
    text = md_path.read_text(encoding="utf-8")
    text = strip_toc_figure_artifacts(text)
    text = re.sub(r"!\[[^\]]*\]\(assets/figures/figure_\d+[^)]+\)\n?", "", text)
    for fid in FIGURE_CONTENT:
        text = re.sub(
            rf"<!-- db:id={re.escape(fid)}[^>]*-->\s*###[^\n]+\n(?:```[\s\S]*?```\s*)?",
            "",
            text,
        )

    assets = _ensure_png_assets()
    registry = {f["id"]: f for f in load_figures_registry()}
    lines = text.splitlines()
    bounds = toc_bounds(lines)

    for fig in sorted(load_figures_registry(), key=lambda f: f["page"]):
        fid = fig["id"]
        header = fig["title"]
        page = str(fig["page"])
        render_as = fig["render_as"]

        if render_as == "png":
            asset = assets.get(fid, "")
            if asset:
                text = inject_png_figure(text, header, fid, asset, page, render_as, bounds)
        elif render_as in ("text_diagram", "mermaid") and fid in FIGURE_CONTENT:
            block = figure_block(fid)
            text = inject_text_diagram(text, header, block, bounds)

    md_path.write_text(text, encoding="utf-8")
    return {"path": str(md_path), "png_assets": len(assets), "figures": len(registry)}


def update_db_registry():
    reg_path = FINAL_DIR / "db_import_registry.json"
    if not reg_path.exists():
        return
    records = json.loads(reg_path.read_text(encoding="utf-8"))
    existing_ids = {r["id"] for r in records}
    registry = load_figures_registry()

    for fig in registry:
        if fig["id"] in existing_ids:
            for r in records:
                if r["id"] == fig["id"]:
                    r["render_as"] = fig["render_as"]
                    r["type"] = "figure"
                    if fig.get("profile_data"):
                        r["profile_data"] = fig["profile_data"]
        else:
            rec = {
                "id": fig["id"],
                "display_caption": f"{fig['title']} | {fig['id']}",
                "type": "figure",
                "product_tiers": ["context"],
                "page_start": fig["page"],
                "page_end": fig["page"],
                "render_as": fig["render_as"],
                "anchor": f"#{fig['id']}",
            }
            if fig.get("profile_data"):
                rec["profile_data"] = fig["profile_data"]
            records.append(rec)
    records.sort(key=lambda r: (r.get("page_start", 0), r["id"]))
    reg_path.write_text(json.dumps(records, indent=2), encoding="utf-8")


def run_apply_figures():
    md = FINAL_DIR / "CEFR_Companion_Volume.md"
    result = apply_figures_to_markdown(md)
    update_db_registry()
    return result


if __name__ == "__main__":
    print(run_apply_figures())