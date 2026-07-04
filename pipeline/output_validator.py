"""Validate final output against inventory-required artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path

from pipeline.config import (
    FINAL_DIR,
    INVENTORIES_DIR,
    KNOWN_TABLES_FIGURES,
    METADATA_DIR,
    MULTIPAGE_ARTIFACTS,
    PDF_PATH,
    load_figures_registry,
    SECTION_BLOCKS,
)
from pipeline.title_fix import fix_rotated_title, is_probably_reversed
from pipeline.utils import english_word_score

try:
    import fitz
except ImportError:
    fitz = None


def required_artifacts() -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    for _page, (aid, title, atype) in KNOWN_TABLES_FIGURES.items():
        if aid not in seen:
            items.append({"id": aid, "title": title, "type": atype, "min_body_chars": 80})
            seen.add(aid)
    for gid, cfg in MULTIPAGE_ARTIFACTS.items():
        if gid not in seen:
            items.append(
                {
                    "id": gid,
                    "type": "table",
                    "min_body_chars": 200,
                    "pages": f"{cfg['page_start']}-{cfg['page_end']}",
                }
            )
            seen.add(gid)
    for block in SECTION_BLOCKS:
        if block["id"] not in seen:
            items.append({"id": block["id"], "type": block["type"], "min_body_chars": 3000})
            seen.add(block["id"])
    for fig in load_figures_registry():
        if fig["id"] not in seen:
            min_chars = 20 if fig["render_as"] == "png" else 50
            items.append({"id": fig["id"], "type": "figure", "min_body_chars": min_chars})
            seen.add(fig["id"])
    return items


def _artifact_body(text: str, aid: str) -> str:
    pattern = rf"<!-- db:id={re.escape(aid)}[^>]*-->.*?(?=<!-- db:id=|\Z)"
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return ""
    block = m.group(0)
    block = re.sub(r"^###[^\n]+\n", "", block)
    block = re.sub(r"<!--[^>]+-->", "", block)
    return block.strip()


def _load_page_expectations() -> dict[int, dict]:
    expectations: dict[int, dict] = {}
    for inv_path in sorted(INVENTORIES_DIR.glob("chunk_*_inventory.json")):
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
        for page in inv.get("pages", []):
            expectations[page["page_number"]] = page
    return expectations


def _page_sections(text: str) -> dict[int, str]:
    """Map page marker N -> body content emitted for that page (before ``<!-- page:N -->``)."""
    markers = list(re.finditer(r"<!-- page:(\d+) -->", text))
    sections: dict[int, str] = {}
    for i, m in enumerate(markers):
        page_num = int(m.group(1))
        start = markers[i - 1].end() if i > 0 else 0
        sections[page_num] = text[start : m.start()]
    return sections


def _normalize_header(text: str) -> str:
    text = re.sub(r"^#+\s*", "", text.strip())
    text = re.sub(r"\s*—\s*\d{1,3}$", "", text)
    return re.sub(r"\s+", " ", text).lower()


def _measurable_chars(section: str) -> int:
    cleaned = re.sub(r"<!--[^>]+-->", "", section)
    cleaned = re.sub(r"^\*[^*]+\*\s*$", "", cleaned, flags=re.M)
    cleaned = re.sub(r"^#{1,6}\s+[^\n]+\n", "", cleaned, flags=re.M)
    return len(re.sub(r"\s+", "", cleaned))


def _validate_reading_order_elements(text: str, issues: list[dict]) -> None:
    """Element-level checks from per-page reading_order inventories."""
    expectations = _load_page_expectations()
    sections = _page_sections(text)
    emitted_spans: set[str] = set()

    for page_num, exp in sorted(expectations.items()):
        reading_order = exp.get("reading_order") or []
        if not reading_order:
            continue
        section = sections.get(page_num, "")

        for el in reading_order:
            etype = el.get("type")

            if etype == "artifact":
                title = el.get("display_title") or ""
                if title and is_probably_reversed(title):
                    issues.append(
                        {
                            "type": "reversed_title",
                            "page": page_num,
                            "title": title,
                            "fixed": fix_rotated_title(title),
                        }
                    )
                span = el.get("span")
                if span and span.get("role") == "start":
                    gid = span["group_id"]
                    if gid in emitted_spans:
                        issues.append(
                            {
                                "type": "span_duplicate_emit",
                                "page": page_num,
                                "group_id": gid,
                                "artifact_id": el.get("artifact_id"),
                            }
                        )
                        continue
                    if gid not in section and el.get("artifact_id") not in section:
                        issues.append(
                            {
                                "type": "missing_span_artifact",
                                "page": page_num,
                                "group_id": gid,
                            }
                        )
                    else:
                        emitted_spans.add(gid)

                if el.get("extractor") == "rotated_table" or el.get("text_direction") == "ocr":
                    aid = el.get("artifact_id")
                    body = _artifact_body(text, aid) if aid else section
                    if body and not re.search(
                        r"\b(C2|C1|B2|B1|A2|A1|Pre-A1)\b", body, re.I
                    ) and english_word_score(body) < 0.12:
                        issues.append(
                            {
                                "type": "rotated_table_unreadable",
                                "page": page_num,
                                "artifact_id": aid,
                                "score": english_word_score(body),
                            }
                        )

            if etype == "prose" and el.get("role") == "trailing":
                expected = el.get("expected_chars", 0)
                if expected > 40:
                    after_table = section
                    if "|" in section:
                        after_table = section.rsplit("|", 1)[-1]
                    chars = _measurable_chars(after_table)
                    if chars < expected * 0.5:
                        issues.append(
                            {
                                "type": "missing_trailing_prose",
                                "page": page_num,
                                "chars": chars,
                                "expected_chars": expected,
                            }
                        )

            if etype == "prose" and el.get("extractor") == "prose_zone":
                expected = el.get("expected_chars", 0)
                if expected > 60:
                    chars = _measurable_chars(section)
                    if chars < expected * 0.4:
                        issues.append(
                            {
                                "type": "element_under_extracted",
                                "page": page_num,
                                "role": el.get("role"),
                                "chars": chars,
                                "expected_chars": expected,
                            }
                        )


def _validate_page_coverage(text: str, issues: list[dict]) -> None:
    expectations = _load_page_expectations()
    sections = _page_sections(text)
    if not expectations:
        issues.append({"type": "missing_inventories", "detail": "No chunk inventories found"})
        return

    for page_num, exp in sorted(expectations.items()):
        if exp.get("content_type") in ("blank", "toc"):
            continue
        if exp.get("skip_validation"):
            continue
        span = exp.get("spanning_info")
        if span and page_num > span.get("start_page", page_num):
            if span.get("span_type") in ("continuation", "series", "section_block"):
                continue
        section = sections.get(page_num, "")
        if not section.strip():
            if exp.get("text_length", 0) > 100:
                issues.append(
                    {
                        "type": "empty_page_section",
                        "page": page_num,
                        "text_length_pdf": exp.get("text_length"),
                    }
                )
            continue

        chars = _measurable_chars(section)
        min_chars = exp.get("min_output_chars", 80)
        if chars < min_chars:
            issues.append(
                {
                    "type": "page_under_extracted",
                    "page": page_num,
                    "chars": chars,
                    "min_chars": min_chars,
                    "content_type": exp.get("content_type"),
                }
            )

        for header in exp.get("section_headers", []):
            norm = _normalize_header(header)
            section_norm = _normalize_header(section)
            if norm not in section_norm and norm.split(".", 1)[-1].strip() not in section.lower():
                issues.append(
                    {
                        "type": "missing_section_header",
                        "page": page_num,
                        "header": header,
                    }
                )

        if exp.get("expects_table") and not re.search(r"^\|", section, re.M):
            issues.append(
                {
                    "type": "missing_table_markdown",
                    "page": page_num,
                    "artifact_id": exp.get("artifact_id"),
                }
            )

        aid = exp.get("artifact_id")
        if aid and exp.get("expects_table") and aid not in section:
            issues.append(
                {
                    "type": "missing_page_artifact",
                    "page": page_num,
                    "artifact_id": aid,
                }
            )


def _pdf_page_count() -> int:
    if fitz is None or not PDF_PATH.exists():
        return 278
    doc = fitz.open(PDF_PATH)
    count = len(doc)
    doc.close()
    return count


def validate_final_output(md_path: Path | None = None) -> dict:
    md_path = md_path or FINAL_DIR / "CEFR_Companion_Volume.md"
    text = md_path.read_text(encoding="utf-8")
    issues: list[dict] = []

    for req in required_artifacts():
        aid = req["id"]
        body = _artifact_body(text, aid)
        if not body:
            issues.append({"type": "missing_artifact", "id": aid, "title": req.get("title", aid)})
            continue
        if len(body) < req.get("min_body_chars", 1):
            issues.append(
                {
                    "type": "empty_artifact",
                    "id": aid,
                    "chars": len(body),
                    "min": req["min_body_chars"],
                }
            )
        if aid == "table_02_summary_descriptor_changes":
            if "Young learners" not in body or "Parallel project" not in body:
                issues.append(
                    {
                        "type": "incomplete_table",
                        "id": aid,
                        "detail": "Table 2 missing rows from page 25",
                    }
                )

    page_markers = re.findall(r"<!-- page:(\d+) -->", text)
    unique_pages = sorted({int(p) for p in page_markers})
    page_count = _pdf_page_count()
    missing_pages = [p for p in range(1, page_count + 1) if p not in unique_pages]
    if missing_pages:
        issues.append(
            {
                "type": "missing_page_markers",
                "found": len(unique_pages),
                "expected": page_count,
                "missing": missing_pages,
            }
        )

    for gid, cfg in MULTIPAGE_ARTIFACTS.items():
        for p in range(cfg["page_start"], cfg["page_end"] + 1):
            if p not in unique_pages:
                issues.append(
                    {
                        "type": "multipage_span_gap",
                        "artifact": gid,
                        "missing_page": p,
                    }
                )

    toc_block = re.search(
        r"## Contents.*?(?=<!-- page:10 -->|<!-- page:11 -->|\n## Foreword)",
        text,
        re.DOTALL,
    )
    if toc_block:
        lone_nums = re.findall(r"^\d{1,3}$", toc_block.group(0), re.M)
        if len(lone_nums) >= 3:
            issues.append(
                {
                    "type": "toc_orphan_page_numbers",
                    "count": len(lone_nums),
                    "sample": lone_nums[:10],
                }
            )

    _validate_reading_order_elements(text, issues)
    _validate_page_coverage(text, issues)

    sections = re.split(r"(?=<!-- page:\d+ -->)", text)
    for section in sections:
        m = re.search(r"<!-- page:(\d+) -->", section)
        if not m:
            continue
        marker_pos = m.start()
        before = section[:marker_pos].strip()
        if not before:
            continue
        lines = [ln for ln in before.splitlines() if ln.strip()]
        body_idxs = [
            i
            for i, ln in enumerate(lines)
            if len(ln.strip()) > 40 and not re.match(r"^\d{1,2}\.\s+", ln.strip())
        ]
        fn_idxs = [i for i, ln in enumerate(lines) if re.match(r"^\d{1,2}\.\s+", ln.strip())]
        if body_idxs and fn_idxs and min(fn_idxs) < max(body_idxs):
            issues.append(
                {
                    "type": "footnote_before_body",
                    "page": int(m.group(1)),
                }
            )

    issue_counts: dict[str, int] = {}
    for issue in issues:
        issue_counts[issue["type"]] = issue_counts.get(issue["type"], 0) + 1

    report = {
        "path": str(md_path),
        "valid": len(issues) == 0,
        "issues": issues,
        "issue_counts": issue_counts,
        "page_markers": len(unique_pages),
        "required_count": len(required_artifacts()),
        "missing_pages": missing_pages,
    }
    out = METADATA_DIR / "output_validation.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report