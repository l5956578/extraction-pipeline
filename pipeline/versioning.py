"""Versioned snapshots under output/<job-id>/versions/NNN/ after regression passes.

Process (user intent):
1. Pipeline overwrites live files in output/<job-id>/ on each iteration.
2. After a successful write, run regression tests/validators.
3. If and only if they pass → create versions/00N/ (never overwrite prior).
4. User marks a version approved via APPROVED.json pointing at that version.
5. Production promotion should pull from the approved version only.

No top-level staging/pending for pipeline artifacts.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.job_context import JobContext, require_active_job


_VERSION_DIR_RE = re.compile(r"^(\d{3,})$")


def versions_root(ctx: JobContext | None = None) -> Path:
    ctx = ctx or require_active_job()
    return ctx.final_dir / "versions"


def approved_marker_path(ctx: JobContext | None = None) -> Path:
    ctx = ctx or require_active_job()
    return ctx.final_dir / "APPROVED.json"


def list_version_numbers(ctx: JobContext | None = None) -> list[int]:
    root = versions_root(ctx)
    if not root.is_dir():
        return []
    nums: list[int] = []
    for p in root.iterdir():
        if p.is_dir() and _VERSION_DIR_RE.match(p.name):
            nums.append(int(p.name))
    return sorted(nums)


def next_version_number(ctx: JobContext | None = None) -> int:
    nums = list_version_numbers(ctx)
    return (nums[-1] + 1) if nums else 1


def version_dir_name(n: int) -> str:
    return f"{n:03d}"


def _copy_tree(src: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    if src.is_file():
        shutil.copy2(src, dest / src.name)
        return
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        # Never nest versions/ or APPROVED into a version snapshot
        parts = rel.parts
        if parts and parts[0] in {"versions", "APPROVED.json"}:
            continue
        target = dest / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def create_version_snapshot(
    ctx: JobContext | None = None,
    *,
    regression_report: dict[str, Any] | None = None,
) -> Path:
    """Copy live output (except versions/ and APPROVED.json) into versions/NNN/.

    Never overwrites an existing version directory.
    """
    ctx = ctx or require_active_job()
    n = next_version_number(ctx)
    name = version_dir_name(n)
    dest = versions_root(ctx) / name
    if dest.exists():
        raise FileExistsError(f"Version directory already exists: {dest}")

    live = ctx.final_dir
    if not live.is_dir():
        raise FileNotFoundError(f"Live output missing: {live}")

    _copy_tree(live, dest)

    meta = {
        "schema_version": 1,
        "job_id": ctx.job_id,
        "version": name,
        "version_number": n,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_live_output": str(live),
        "regression": regression_report or {},
    }
    (dest / "VERSION.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return dest


def mark_approved(
    version: str | int,
    ctx: JobContext | None = None,
    *,
    notes: str = "",
) -> Path:
    """Write APPROVED.json pointing at versions/NNN/ (does not delete other versions)."""
    ctx = ctx or require_active_job()
    if isinstance(version, int):
        name = version_dir_name(version)
    else:
        name = version.strip()
        if not _VERSION_DIR_RE.match(name):
            # allow "1" or "001"
            name = version_dir_name(int(name))
    vdir = versions_root(ctx) / name
    if not vdir.is_dir():
        raise FileNotFoundError(f"Unknown version directory: {vdir}")

    marker = {
        "schema_version": 1,
        "job_id": ctx.job_id,
        "approved_version": name,
        "approved_path": f"versions/{name}",
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "notes": notes,
        "promotion_note": (
            "Production promotion should copy from this approved version "
            "directory, not from the live output/ root."
        ),
    }
    path = approved_marker_path(ctx)
    path.write_text(json.dumps(marker, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def get_approved_version_dir(ctx: JobContext | None = None) -> Path | None:
    ctx = ctx or require_active_job()
    path = approved_marker_path(ctx)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    name = data.get("approved_version")
    if not name:
        return None
    vdir = versions_root(ctx) / name
    return vdir if vdir.is_dir() else None
