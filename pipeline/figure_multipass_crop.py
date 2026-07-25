"""Multi-pass agent-in-the-loop figure crop helper (C2-F3 / UV-06 / UV-12).

Policy (user logs 03–06): never ship a single-pass fractional crop.
1. Derive candidate box from PDF drawings / embedded images / caption text.
2. Render crop at high resolution.
3. Agent re-reads PNG; if any surrounding prose/caption/footer remains, tighten.
4. Repeat until crop is figure-only.

This module is the machine side of that loop: geometry candidates + crop write.
The agent must still *visually* re-read each PNG before marking C2-F3 resolved.
"""

from __future__ import annotations

import json
from pathlib import Path

import fitz

from pipeline.config import ASSETS_FIGURES, METADATA_DIR, PDF_PATH
from pipeline.utils import ensure_dir

# Drawing-geometry crops (normalized 0–1). Tuned by multipass visual review
# against page renders + user screenshots (log 02 p.34, log 04 #6–8, log 06).
# Rule: include full figure artwork; exclude caption above and body prose below.
VERIFIED_CROPS: dict[str, dict[str, float]] = {
    # Border box 0.438–0.596 × 0.118–0.883 — pad slightly so stroke not clipped
    "figure_02_reception_production_interaction_mediation": {
        "y0": 0.435,
        "y1": 0.600,
        "x0": 0.112,
        "x1": 0.888,
    },
    # Concentric disks only (outer fill 0.538–0.673 × 0.405–0.595)
    "figure_03_cefr_common_reference_levels": {
        "y0": 0.530,
        "y1": 0.678,
        "x0": 0.390,
        "x1": 0.610,
    },
    # Embedded photo rect 0.779–0.895 × 0.118–0.408
    "figure_04_rainbow": {
        "y0": 0.775,
        "y1": 0.900,
        "x0": 0.110,
        "x1": 0.415,
    },
    # Six colour bars 0.779–0.895 × 0.599–0.882 (no caption, no white waste)
    "figure_05_conventional_six_colours": {
        "y0": 0.775,
        "y1": 0.900,
        "x0": 0.590,
        "x1": 0.890,
    },
    # Radar + axis labels; caption at 0.603, footer ~0.95
    "figure_06_fictional_profile_clil": {
        "y0": 0.618,
        "y1": 0.935,
        "x0": 0.05,
        "x1": 0.95,
    },
    # Radar; caption 0.256, prose resumes ~0.643
    "figure_07_profile_postgraduate_sciences": {
        "y0": 0.272,
        "y1": 0.630,
        "x0": 0.05,
        "x1": 0.95,
    },
    # Radar; caption 0.124, prose ~0.503
    # Pass 3: y0 raised past caption line (0.124); legend starts ~0.147
    "figure_08_plurilingual_proficiency_fewer_categories": {
        "y0": 0.145,
        "y1": 0.498,
        "x0": 0.18,
        "x1": 0.82,
    },
}


def crop_with_box(
    page: fitz.Page,
    fig_id: str,
    crop: dict[str, float],
    *,
    scale: float = 3.0,
    out_dir: Path | None = None,
) -> Path:
    """Render ``crop`` box of ``page`` to PNG at ``scale``."""
    out_dir = out_dir or ASSETS_FIGURES
    ensure_dir(out_dir)
    rect = page.rect
    clip = fitz.Rect(
        rect.x0 + rect.width * crop["x0"],
        rect.y0 + rect.height * crop["y0"],
        rect.x0 + rect.width * crop["x1"],
        rect.y0 + rect.height * crop["y1"],
    )
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip)
    path = out_dir / f"{fig_id}.png"
    pix.save(str(path))
    return path


def apply_verified_crops(
    *,
    scale: float = 3.0,
    write_registry: bool = True,
) -> dict[str, str]:
    """Apply VERIFIED_CROPS, optionally persist into figures_registry.json."""
    reg_path = METADATA_DIR / "figures_registry.json"
    data = json.loads(reg_path.read_text(encoding="utf-8"))
    by_id = {f["id"]: f for f in data["figures"]}

    doc = fitz.open(PDF_PATH)
    written: dict[str, str] = {}
    for fid, crop in VERIFIED_CROPS.items():
        fig = by_id.get(fid)
        if not fig:
            continue
        page = doc[fig["page"] - 1]
        path = crop_with_box(page, fid, crop, scale=scale)
        written[fid] = str(path)
        fig["crop"] = dict(crop)
        # Figs 9–10 are tables — leave render_as alone here
        if fig.get("render_as") == "png":
            pass
    doc.close()

    if write_registry:
        reg_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return written


if __name__ == "__main__":
    result = apply_verified_crops()
    for k, v in result.items():
        print(k, "->", v)
