"""Patch output Markdown with correct figure representations."""

from __future__ import annotations

import json
import re
from pathlib import Path

import fitz

import pipeline.config as cfg
from pipeline.config import final_markdown_path
from pipeline.extractors.figures import crop_figure_png, extract_figure_04_embedded, load_figures_registry
from pipeline.figure_inject import inject_png_figure, inject_text_diagram
from pipeline.figure_multipass_crop import VERIFIED_CROPS, apply_verified_crops
from pipeline.figures_catalog import FIGURE_CONTENT, figure_block
from pipeline.toc_zone import strip_toc_figure_artifacts, toc_bounds

def _ensure_png_assets() -> dict[str, str]:
    """Crop PNG figures using multipass-verified registry boxes (C2-F3).

    Prefer ``VERIFIED_CROPS`` (geometry + agent visual loop). Figs with
    ``render_as != png`` are skipped.
    """
    try:
        apply_verified_crops(scale=3.0, write_registry=True)
    except Exception:  # noqa: BLE001
        pass

    doc = fitz.open(cfg.PDF_PATH)
    assets: dict[str, str] = {}
    for fig in load_figures_registry():
        if fig.get("render_as") != "png":
            continue
        page = doc[fig["page"] - 1]
        fid = fig["id"]
        if fid in VERIFIED_CROPS:
            fig = {**fig, "crop": VERIFIED_CROPS[fid]}
        if fid == "figure_04_rainbow":
            path = crop_figure_png(page, fig, scale=3.0)
            if not path:
                path = extract_figure_04_embedded(page)
        else:
            path = crop_figure_png(page, fig, scale=3.0)
        if path:
            assets[fid] = path
    doc.close()
    return assets

def _replace_png_body_with_table(text: str, fid: str, block: str) -> str:
    """Swap legacy PNG inject for fig 9/10 table bodies (log 04 #8 / log 06)."""
    # Match db:id header through optional ### line and image markdown
    pat = re.compile(
        rf"(<!--\s*db:id={re.escape(fid)}\s+type=figure[^>]*-->)\s*\n"
        rf"(###[^\n]+\n)?"
        rf"(?:\s*!\[[^\]]*\]\([^)]+\)\s*\n)?",
        re.I,
    )
    if pat.search(text):
        # Rebuild clean block from catalog
        return pat.sub(block.rstrip() + "\n\n", text, count=1)
    return text

def apply_figures_to_markdown(md_path: Path) -> dict:
    text = md_path.read_text(encoding="utf-8")
    text = strip_toc_figure_artifacts(text)
    # Drop orphan PNG image lines not near a figure db:id (legacy EOF dumps).
    cleaned_lines: list[str] = []
    recent_countdown = 0
    for line in text.splitlines():
        if re.search(r"<!--\s*db:id=figure_\d+", line):
            recent_countdown = 10
            cleaned_lines.append(line)
            continue
        if re.match(r"!\[[^\]]*\]\(assets/figures/figure_", line):
            if recent_countdown > 0:
                cleaned_lines.append(line)
            # else drop orphan
            if recent_countdown > 0:
                recent_countdown -= 1
            continue
        if recent_countdown > 0:
            recent_countdown -= 1
        cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)

    assets = _ensure_png_assets()
    registry = {f["id"]: f for f in load_figures_registry()}
    lines = text.splitlines()
    bounds = toc_bounds(lines)

    for fig in sorted(load_figures_registry(), key=lambda f: (f["page"], f["num"])):
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

    # Final pass: replace-not-layer (C2-ADJ) — clear dual-emitted figure garbage.
    from pipeline.figure_inject import strip_garbage_under_figure_images

    text = strip_garbage_under_figure_images(text)

    md_path.write_text(text, encoding="utf-8")
    return {"path": str(md_path), "png_assets": len(assets), "figures": len(registry)}

def update_db_registry():
    reg_path = cfg.FINAL_DIR / "db_import_registry.json"
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
    from pipeline.config import feature_enabled

    if not feature_enabled("figures"):
        return {
            "figures_applied": 0,
            "skipped": True,
            "reason": "extraction.features.figures is false",
            "path": str(final_markdown_path()),
        }
    md = final_markdown_path()
    result = apply_figures_to_markdown(md)
    update_db_registry()
    return result

if __name__ == "__main__":
    from pipeline.bootstrap import parse_and_load_job

    parse_and_load_job(description="Apply figures to final markdown")
    print(run_apply_figures())