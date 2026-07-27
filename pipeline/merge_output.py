"""Merge cleaned chunks into final deliverables."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pipeline.config as cfg
from pipeline.config import final_markdown_path, load_figures_registry, require_active_job
from pipeline.id_registry import build_registry
from pipeline.utils import slugify


def _document_shell() -> dict:
    """Document H1 / db:id / nav from job.json output (+ source page count).

    Companion values live in the Companion job sidecar — not hardcoded here.
    """
    ctx = require_active_job()
    out = ctx.job_data.get("output") or {}
    source = ctx.job_data.get("source") or {}
    product = ctx.product or {}

    title = out.get("document_title") or ctx.title
    doc_id = out.get("document_id") or slugify(ctx.job_id.replace("-", "_"))
    product_tier = out.get("product_tier") or (
        (product.get("default_product_tiers") or ["context"])[0]
    )
    page_count = out.get("page_count") or source.get("expected_page_count")
    if page_count is not None:
        page_count = int(page_count)
    pages_attr = f" pages=1-{page_count}" if page_count else ""

    return {
        "title": title,
        "document_id": doc_id,
        "product_tier": product_tier,
        "page_count": page_count,
        "pages_attr": pages_attr,
        "navigation": list(out.get("navigation") or []),
        "products": dict(out.get("products") or {}),
    }


def merge_markdown() -> str:
    shell = _document_shell()
    parts = [
        f"# {shell['title']}\n",
        (
            f"<!-- db:id={shell['document_id']} type=document "
            f"product_tier={shell['product_tier']}{shell['pages_attr']} -->\n"
        ),
    ]
    for md in sorted(cfg.CLEANED_DIR.glob("chunk_*.md")):
        text = md.read_text(encoding="utf-8")
        # Strip chunk-level H1
        text = re.sub(r"^# chunk_\d+[^\n]*\n", "", text, count=1)
        parts.append(text.strip())
        parts.append("\n\n---\n\n")

    out = final_markdown_path()
    cfg.FINAL_DIR.mkdir(parents=True, exist_ok=True)
    content = "\n".join(parts)
    out.write_text(content, encoding="utf-8")
    print(f"Wrote {out}")
    return str(out)


def build_manifest() -> dict:
    artifacts = build_registry()
    shell = _document_shell()

    manifest = {
        "title": shell["title"],
        "page_count": shell["page_count"],
        "navigation": shell["navigation"],
        "products": shell["products"],
        "artifact_count": len(artifacts),
        "job_id": require_active_job().job_id,
    }
    path = cfg.FINAL_DIR / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def build_db_registry() -> list[dict]:
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
    path = cfg.FINAL_DIR / "db_import_registry.json"
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
    out_val = cfg.METADATA_DIR / "output_validation.json"
    if not report["valid"]:
        print(
            f"Output validation: {len(report['issues'])} issue(s) — see {out_val}"
        )
    else:
        print("Output validation: passed")
    from pipeline.contract_validators import validate_contracts

    creport = validate_contracts()
    if not creport["valid"]:
        print(
            f"Contract validation: {creport['issue_count']} issue(s) — "
            f"see {cfg.METADATA_DIR / 'contract_validation.json'} "
            "(fail-closed; do not claim resolved)"
        )
    else:
        print("Contract validation: passed")
