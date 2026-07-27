"""JOB_MANIFEST + product_context writers for shippable job output.

Emits job-level business tags (from ``job.json`` ``product``) alongside
pointers to existing shippable files. Does **not** wrap or mutate
``db_import_registry.json`` (that file remains a JSON **array** of
per-artifact rows with ``product_tiers``).

Call ``write_job_manifest(ctx)`` after merge / format so the manifest
stays current for promotion and DB/ETL consumers.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.job_context import JobContext, get_active_job, require_active_job

# Schema version for JOB_MANIFEST.json (bump when breaking field shape).
JOB_MANIFEST_SCHEMA_VERSION = 1

# Promotion lifecycle while still under pipeline output/.
STATUS_PIPELINE_OUTPUT = "pipeline_output"

# Shippable filenames we advertise when present under output/<job-id>/.
_KEY_FILE_CANDIDATES = (
    "JOB_MANIFEST.json",
    "product_context.json",
    "manifest.json",
    "db_import_registry.json",
)


def _rel_under_output(ctx: JobContext, path: Path) -> str:
    """Path relative to job output dir, POSIX-style; fallback to name."""
    try:
        return path.relative_to(ctx.final_dir).as_posix()
    except ValueError:
        return path.name


def _list_asset_paths(ctx: JobContext) -> dict[str, list[str]]:
    figures: list[str] = []
    tables: list[str] = []
    if ctx.assets_figures.is_dir():
        figures = sorted(
            _rel_under_output(ctx, p)
            for p in ctx.assets_figures.rglob("*")
            if p.is_file()
        )
    if ctx.assets_tables.is_dir():
        tables = sorted(
            _rel_under_output(ctx, p)
            for p in ctx.assets_tables.rglob("*")
            if p.is_file()
        )
    return {"figures": figures, "tables": tables}


def _key_files(ctx: JobContext, *, include_pending: bool = False) -> list[str]:
    """List shippable key paths under the job output dir.

    When ``include_pending`` is True, always advertise JOB_MANIFEST.json and
    product_context.json (used while writing them in this pass).
    """
    names: list[str] = []
    md = ctx.final_markdown
    if md.is_file():
        names.append(_rel_under_output(ctx, md))
    for name in _KEY_FILE_CANDIDATES:
        p = ctx.final_dir / name
        if include_pending and name in ("JOB_MANIFEST.json", "product_context.json"):
            if name not in names:
                names.append(name)
            continue
        if p.is_file() and name not in names:
            names.append(name)
    assets = _list_asset_paths(ctx)
    # Summarize asset dirs rather than listing every file in key_files
    if assets["figures"] or ctx.assets_figures.is_dir():
        names.append("assets/figures/")
    if assets["tables"] or ctx.assets_tables.is_dir():
        names.append("assets/tables/")
    # de-dupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def _source_block(ctx: JobContext) -> dict[str, Any]:
    source = (ctx.job_data or {}).get("source") or {}
    block: dict[str, Any] = {
        "file": source.get("file") or ctx.pdf_path.name,
        "original_filename": source.get("original_filename") or ctx.original_filename,
    }
    for key in (
        "published_filename",
        "sha256",
        "hash_verified_against",
        "hash_verified_at",
        "hash_match",
        "expected_page_count",
        "language",
    ):
        if key in source and source[key] is not None:
            block[key] = source[key]
    return block


def _product_block(ctx: JobContext) -> dict[str, Any]:
    """Job-level product tags from job.json (not per-artifact tiers)."""
    product = dict(ctx.product or {})
    # Normalize expected keys so consumers always see a stable shape
    return {
        "framework": product.get("framework"),
        "audiences": list(product.get("audiences") or []),
        "default_product_tiers": list(product.get("default_product_tiers") or []),
        "skill_categories": list(product.get("skill_categories") or []),
        "promotion_target": product.get("promotion_target"),
    }


def build_job_manifest(ctx: JobContext | None = None) -> dict[str, Any]:
    """Build JOB_MANIFEST dict for the active (or given) job without writing."""
    ctx = ctx or require_active_job()
    product = _product_block(ctx)
    assets = _list_asset_paths(ctx)
    md_path = ctx.final_markdown
    registry_path = ctx.final_dir / "db_import_registry.json"
    doc_manifest_path = ctx.final_dir / "manifest.json"
    product_context_path = ctx.final_dir / "product_context.json"

    registry_count: int | None = None
    if registry_path.is_file():
        try:
            data = json.loads(registry_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                registry_count = len(data)
        except (json.JSONDecodeError, OSError):
            registry_count = None

    today = date.today().isoformat()
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    manifest: dict[str, Any] = {
        "schema_version": JOB_MANIFEST_SCHEMA_VERSION,
        "job_id": ctx.job_id,
        "title": ctx.title,
        "status": STATUS_PIPELINE_OUTPUT,
        "job_status": ctx.status,
        "profile": ctx.profile,
        "version": today,
        "generated_at": generated_at,
        "product": product,
        "source": _source_block(ctx),
        "markdown": _rel_under_output(ctx, md_path) if md_path.is_file() else ctx.markdown_name,
        "markdown_exists": md_path.is_file(),
        "assets": {
            "figures_dir": "assets/figures",
            "tables_dir": "assets/tables",
            "figures": assets["figures"],
            "tables": assets["tables"],
            "figure_count": len(assets["figures"]),
            "table_count": len(assets["tables"]),
        },
        "files": {
            "db_import_registry": "db_import_registry.json"
            if registry_path.is_file()
            else None,
            "manifest": "manifest.json" if doc_manifest_path.is_file() else None,
            "product_context": "product_context.json",
            "job_manifest": "JOB_MANIFEST.json",
        },
        "db_import_registry": {
            "path": "db_import_registry.json" if registry_path.is_file() else None,
            "shape": "array",
            "record_count": registry_count,
            "note": (
                "Per-artifact product_tiers live on each registry row. "
                "Job-level tags are under this manifest's product block "
                "(and product_context.json)."
            ),
        },
        "key_files": _key_files(ctx),
        "promotion": {
            "lifecycle_status": STATUS_PIPELINE_OUTPUT,
            "source_output": f"output/{ctx.job_id}/",
            "staging_pending": f"staging/pending/extraction-pipeline/{ctx.job_id}/",
            "promotion_target": product.get("promotion_target"),
            "production_resources": (
                f"production/{product['promotion_target']}"
                if product.get("promotion_target")
                else None
            ),
            "default_action": "copy",
        },
    }
    # Ensure product_context is listed once written; key_files rebuilt after write.
    _ = product_context_path  # shape reserved; written by write_job_manifest
    return manifest


def build_product_context(ctx: JobContext | None = None) -> dict[str, Any]:
    """Sidecar envelope: job-level product + pointer to registry array.

    Keeps ``db_import_registry.json`` as a pure array (ETL contract).
    """
    ctx = ctx or require_active_job()
    product = _product_block(ctx)
    registry_path = ctx.final_dir / "db_import_registry.json"
    record_count: int | None = None
    if registry_path.is_file():
        try:
            data = json.loads(registry_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                record_count = len(data)
        except (json.JSONDecodeError, OSError):
            record_count = None

    return {
        "schema_version": 1,
        "job_id": ctx.job_id,
        "title": ctx.title,
        "product": product,
        "layers": {
            "job_level": {
                "source": f"input/{ctx.job_id}/job.json → product",
                "fields": [
                    "framework",
                    "audiences",
                    "default_product_tiers",
                    "skill_categories",
                    "promotion_target",
                ],
            },
            "artifact_level": {
                "source": f"output/{ctx.job_id}/db_import_registry.json",
                "shape": "array",
                "field": "product_tiers",
                "tier_vocabulary": [
                    "base",
                    "assessment_action",
                    "detailed",
                    "context",
                ],
                "record_count": record_count,
            },
        },
        "db_import_registry": "db_import_registry.json"
        if registry_path.is_file()
        else None,
        "job_manifest": "JOB_MANIFEST.json",
    }


def write_job_manifest(ctx: JobContext | None = None) -> Path:
    """Write ``output/<job-id>/JOB_MANIFEST.json`` (+ ``product_context.json``).

    Returns path to JOB_MANIFEST.json.
    """
    ctx = ctx or get_active_job()
    if ctx is None:
        raise RuntimeError(
            "write_job_manifest requires load_job(job_id) first (no active job)."
        )

    ctx.final_dir.mkdir(parents=True, exist_ok=True)

    product_ctx = build_product_context(ctx)
    product_path = ctx.final_dir / "product_context.json"
    product_path.write_text(
        json.dumps(product_ctx, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    manifest = build_job_manifest(ctx)
    # Include envelope files we are writing this pass
    manifest["key_files"] = _key_files(ctx, include_pending=True)
    manifest["files"]["product_context"] = "product_context.json"
    manifest["files"]["job_manifest"] = "JOB_MANIFEST.json"

    out_path = ctx.final_dir / "JOB_MANIFEST.json"
    out_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {out_path}")
    print(f"Wrote {product_path}")
    return out_path
