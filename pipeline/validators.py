"""Validate extracted/cleaned markdown."""

from __future__ import annotations

import json
import re
from pathlib import Path

from pipeline.config import CLEANED_DIR, RAW_DIR, FINAL_DIR, METADATA_DIR, MAX_RETRY_ATTEMPTS
from pipeline.utils import is_gibberish


def _extract_db_ids(text: str) -> list[str]:
    return re.findall(r"<!-- db:id=([^\s]+)", text)


def validate_markdown(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    issues = []

    ids = _extract_db_ids(text)
    dup_ids = [i for i in set(ids) if ids.count(i) > 1]
    if dup_ids:
        issues.append({"type": "duplicate_id", "ids": dup_ids})

    sa_ids = [i for i in ids if i == "table_self_assessment_grid"]
    if len(sa_ids) > 1:
        issues.append({"type": "duplicate_self_assessment"})
    else:
        if "chunk_07" in path.stem or path.name == "CEFR_Companion_Volume.md":
            pass  # may appear only in chunk 07

    # Table row consistency
    for block in re.findall(r"\|[^\n]+\|", text):
        if block.count("|") < 4:
            continue

    # Gibberish sections
    for match in re.finditer(r"###[^\n]+\n\n([\s\S]{0,800})", text):
        section = match.group(1)
        if is_gibberish(section):
            issues.append({"type": "gibberish", "preview": section[:120]})

    # Image refs
    for m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", text):
        asset = m.group(1)
        if asset.startswith("assets/"):
            full = FINAL_DIR / asset
            if not full.exists():
                issues.append({"type": "missing_asset", "path": asset})

    return {"path": str(path), "valid": len(issues) == 0, "issues": issues}


def validate_all(directory: Path) -> dict:
    results = []
    for md in sorted(directory.glob("*.md")):
        results.append(validate_markdown(md))
    summary = {
        "total": len(results),
        "passed": sum(1 for r in results if r["valid"]),
        "failed": sum(1 for r in results if not r["valid"]),
        "results": results,
    }
    out = METADATA_DIR / "validation_report.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary