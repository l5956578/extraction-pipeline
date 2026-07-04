"""Merge cleaned chunks into final deliverables."""

from __future__ import annotations

import json
import re
from pathlib import Path

from pipeline.config import CLEANED_DIR, FINAL_DIR, METADATA_DIR, SECTION_BLOCKS
from pipeline.id_registry import build_registry


def merge_markdown() -> str:
    parts = [
        "# CEFR Companion Volume\n",
        "<!-- db:id=cefr_companion_volume type=document product_tier=context pages=1-278 -->\n",
    ]
    for md in sorted(CLEANED_DIR.glob("chunk_*.md")):
        text = md.read_text(encoding="utf-8")
        # Strip chunk-level H1
        text = re.sub(r"^# chunk_\d+[^\n]*\n", "", text, count=1)
        parts.append(text.strip())
        parts.append("\n\n---\n\n")

    out = FINAL_DIR / "CEFR_Companion_Volume.md"
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    content = "\n".join(parts)
    out.write_text(content, encoding="utf-8")
    print(f"Wrote {out}")
    return str(out)


def build_manifest() -> dict:
    artifacts = build_registry()
    navigation = [
        {"id": "foreword", "title": "Foreword", "page": 11},
        {"id": "chapter-1", "title": "Chapter 1: The CEFR in the light of its update", "page": 13},
        {"id": "chapter-2", "title": "Chapter 2: Key aspects of the CEFR", "page": 27},
        {"id": "chapter-3", "title": "Chapter 3: Communicative language activities and strategies", "page": 47},
        {"id": "chapter-4", "title": "Chapter 4: Plurilingual and pluricultural competence", "page": 123},
        {"id": "chapter-5", "title": "Chapter 5: Communicative language competences", "page": 129},
        {"id": "chapter-6", "title": "Chapter 6: Signing competences", "page": 143},
        {"id": "appendices", "title": "Appendices", "page": 171},
    ]

    products = {
        "self_assessment_base": {
            "artifact_id": "table_self_assessment_grid",
            "display_name": "Self-Assessment Grid (Expanded with Online Interaction and Mediation)",
            "pages": [177, 181],
            "product_tier": "base",
        },
        "assessment_action_plan": {
            "description": "Descriptor scales for assessment with action planning",
            "product_tier": "assessment_action",
        },
        "detailed_assessment": {
            "description": "Individual illustrative descriptor scales (à la carte)",
            "product_tier": "detailed",
        },
    }

    manifest = {
        "title": "CEFR Companion Volume",
        "page_count": 278,
        "navigation": navigation,
        "products": products,
        "artifact_count": len(artifacts),
    }
    path = FINAL_DIR / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def build_db_registry() -> list[dict]:
    from pipeline.config import load_figures_registry

    artifacts = build_registry()
    render_by_id = {f["id"]: f["render_as"] for f in load_figures_registry()}
    records = []
    for art in artifacts:
        rec = {
            "id": art.id,
            "display_caption": f"{art.display_name} | {art.id}",
            "type": art.artifact_type,
            "product_tiers": art.product_tiers,
            "page_start": art.page_start,
            "page_end": art.page_end,
            "merged_from_pages": list(range(art.page_start, art.page_end + 1)),
            "anchor": f"#{art.id}",
        }
        if art.id in render_by_id:
            rec["render_as"] = render_by_id[art.id]
        records.append(rec)
    path = FINAL_DIR / "db_import_registry.json"
    path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"Wrote {path} ({len(records)} records)")
    return records


def run_merge():
    merge_markdown()
    build_manifest()
    build_db_registry()
    from pipeline.apply_figures import run_apply_figures
    from pipeline.output_validator import validate_final_output
    from pipeline.post_process import run_post_process

    run_apply_figures()
    result = run_post_process()
    print(
        f"Formatted final Markdown: {result['input_lines']} -> {result['output_lines']} lines"
    )
    report = validate_final_output()
    if not report["valid"]:
        print(f"Output validation: {len(report['issues'])} issue(s) — see metadata/output_validation.json")
    else:
        print("Output validation: passed")