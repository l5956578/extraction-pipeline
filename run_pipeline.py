#!/usr/bin/env python3
"""CEFR PDF extraction pipeline orchestrator."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline.chunker import run_chunking
from pipeline.cleanup import cleanup_all
from pipeline.extract_chunk import extract_all_chunks
from pipeline.inventory import build_inventories
from pipeline.merge_output import run_merge
from pipeline.apply_figures import run_apply_figures
from pipeline.span_detector import detect_spans, save_spans
from pipeline.validators import validate_all
from pipeline.config import CLEANED_DIR, RAW_DIR, METADATA_DIR
from pipeline.post_process import run_post_process
from pipeline.extractors.rotated_grok_vision import prepare_all_rotated_from_inventories


def step_spans():
    spans = detect_spans()
    path = save_spans(spans)
    print(f"Step 0a: {len(spans)} span groups -> {path}")


def step_chunks():
    manifest = run_chunking()
    print(f"Step 0b: {len(manifest)} chunks created")


def step_inventory():
    inv = build_inventories()
    print(f"Step 1: {len(inv)} inventories created")


def step_extract():
    outputs = extract_all_chunks()
    print(f"Step 2: {len(outputs)} raw extractions")


def step_cleanup():
    reports = cleanup_all()
    fixes = sum(len(r["fixes"]) for r in reports)
    print(f"Step 3: cleaned {len(reports)} chunks, {fixes} fix categories applied")


def step_validate():
    summary = validate_all(CLEANED_DIR)
    print(f"Step 4: {summary['passed']}/{summary['total']} passed validation")
    return summary


def step_merge():
    run_merge()
    print("Final: merged output written")


def step_figures():
    result = run_apply_figures()
    print(f"Figures: applied {result['figures_applied']} body placements")


def step_postprocess():
    """Re-run final prose formatting on output/CEFR_Companion_Volume.md in place."""
    result = run_post_process()
    print(f"Formatted: {result['output_path']}")
    print(f"  {result['input_lines']} -> {result['output_lines']} lines")


def step_prepare_rotated():
    """Crop rotated table PNGs for agent vision handoff (does not extract text)."""
    prepared = prepare_all_rotated_from_inventories()
    print(f"Prepare rotated: {len(prepared)} table page(s) → work/metadata/rotated_for_grok/")
    print("Next: agent re-reads PNGs with vision → work/metadata/rotated_from_grok/ → finalize_after_grok.py")


def write_docs():
    report_path = METADATA_DIR / "cleanup_report.md"
    report_path.write_text(
        "# Cleanup Report\n\n"
        "Rule-based cleanup applied: hyphenation fixes, ligature removal, "
        "duplicate line removal, reversed-fragment correction.\n\n"
        "Rotated descriptor tables: agent vision handoff "
        "(`work/metadata/rotated_for_grok/` + `rotated_from_grok/`; see "
        "`ROTATED_TABLES_AGENT_VISION.md`). Footnotes on rotated pages use "
        "geometry surgical path. OCR remains fallback only.\n\n"
        "Continuation merges applied for:\n"
        "- `scale_vocabulary_control` (pages 132-133)\n"
        "- `table_self_assessment_grid` (pages 177-181)\n"
        "- Table 2 (pages 24-25)\n\n"
        "Figures: see `work/metadata/figures_handling.md`. Post-merge `apply_figures` "
        "inserts text diagrams, profile tables, or mermaid per `figures_registry.json`; "
        "only Figure 4 (rainbow photo) is kept as PNG.\n",
        encoding="utf-8",
    )

    sqlite_notes = METADATA_DIR / "sqlite_schema_notes.md"
    sqlite_notes.write_text(
        """# SQLite / Website Import Notes

## Recommended schema

- `content_nodes(id, parent_id, title, anchor, page_start, page_end, node_type)`
- `artifacts(id, display_caption, artifact_type, page_start, page_end, anchor, asset_path)`
- `artifact_product_tiers(artifact_id, product_tier)` — values: `base`, `assessment_action`, `detailed`, `context`
- `scale_rows(artifact_id, cefr_level, descriptor_text, sort_order)`
- `figure_assets(artifact_id, file_path, mime_type, blob optional)`
- `products(id, name, description)` — maps to tiers for your 3 assessment offerings + coaching context

## Import workflow

1. Parse `output/db_import_registry.json` into `artifacts` + `artifact_product_tiers`.
2. Parse `<!-- db:... -->` comments in `CEFR_Companion_Volume.md` for prose blocks → `content_nodes`.
3. Split pipe tables under each artifact into `scale_rows`.
4. Copy `output/assets/` paths into `figure_assets`; optionally store BLOB for portability.

## Product queries

- Base self-assessment: `WHERE product_tier = 'base'` → `table_self_assessment_grid`
- Action plan scales: `WHERE product_tier = 'assessment_action'`
- À-la-carte detailed: `WHERE product_tier = 'detailed'`

## UI pattern

- Sidebar: `manifest.json` → `navigation` tree
- Deep links: `anchor` field per artifact
- Caption format: `Display Name | artifact_id` (searchable in DB)

## Coaching sessions

Keep `products` / `sessions` tables separate from content — link sessions to `product_tier` and user assessment results, not to PDF pages.
""",
        encoding="utf-8",
    )
    print("Wrote documentation")


def main():
    parser = argparse.ArgumentParser(description="CEFR PDF extraction pipeline")
    parser.add_argument(
        "--step",
        choices=[
            "all", "spans", "chunks", "inventory", "extract", "cleanup", "validate",
            "merge", "figures", "postprocess", "docs", "prepare_rotated",
        ],
        default="all",
    )
    args = parser.parse_args()

    steps = {
        "spans": step_spans,
        "chunks": step_chunks,
        "inventory": step_inventory,
        "extract": step_extract,
        "cleanup": step_cleanup,
        "validate": step_validate,
        "merge": step_merge,
        "figures": step_figures,
        "postprocess": step_postprocess,
        "docs": write_docs,
        "prepare_rotated": step_prepare_rotated,
    }

    if args.step == "all":
        for name in [
            "spans", "chunks", "inventory", "extract", "cleanup", "validate",
            "merge", "docs",
        ]:
            steps[name]()
    else:
        steps[args.step]()


if __name__ == "__main__":
    main()