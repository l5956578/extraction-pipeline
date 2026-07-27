"""Validate final output against inventory-required artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pipeline.config as cfg
from pipeline.config import final_markdown_path, load_figures_registry
from pipeline.page_elements import prose_segments, table_bboxes
from pipeline.title_fix import fix_rotated_title, is_probably_reversed
from pipeline.utils import english_word_score

try:
    import fitz
except ImportError:
    fitz = None

def required_artifacts() -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    for _page, (aid, title, atype) in cfg.KNOWN_TABLES_FIGURES.items():
        if aid not in seen:
            items.append({"id": aid, "title": title, "type": atype, "min_body_chars": 80})
            seen.add(aid)
    for gid, mp in cfg.MULTIPAGE_ARTIFACTS.items():
        if gid not in seen:
            items.append(
                {
                    "id": gid,
                    "type": "table",
                    "min_body_chars": 200,
                    "pages": f"{mp['page_start']}-{mp['page_end']}",
                }
            )
            seen.add(gid)
    for block in cfg.SECTION_BLOCKS:
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
    for inv_path in sorted(cfg.INVENTORIES_DIR.glob("chunk_*_inventory.json")):
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

def _page_body_before_marker(text: str, page_num: int) -> str:
    """Body content immediately preceding the first ``<!-- page:N -->`` marker."""
    markers = list(re.finditer(r"<!-- page:(\d+) -->", text))
    first = next((m for m in markers if int(m.group(1)) == page_num), None)
    if not first:
        return ""
    idx = markers.index(first)
    start = markers[idx - 1].end() if idx > 0 else 0
    return text[start : first.start()]

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

def _load_spanning_tables() -> list[dict]:
    path = cfg.METADATA_DIR / "spanning_tables.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))

def _page_ranges_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return not (a_end < b_start or b_end < a_start)

def _validate_span_chain_integrity(issues: list[dict]) -> None:
    """Each group_id in spanning_tables.json must be a single merged chain."""
    spans = _load_spanning_tables()
    if not spans:
        issues.append(
            {
                "type": "span_chain_integrity",
                "detail": "missing or empty spanning_tables.json",
            }
        )
        return

    by_gid: dict[str, list[dict]] = {}
    for span in spans:
        by_gid.setdefault(span["group_id"], []).append(span)

    for gid, entries in by_gid.items():
        if len(entries) > 1:
            for i, left in enumerate(entries):
                for right in entries[i + 1 :]:
                    if _page_ranges_overlap(
                        left["start_page"],
                        left["end_page"],
                        right["start_page"],
                        right["end_page"],
                    ):
                        issues.append(
                            {
                                "type": "span_chain_integrity",
                                "group_id": gid,
                                "detail": "overlapping duplicate spans for group_id",
                                "spans": [
                                    {
                                        "start_page": left["start_page"],
                                        "end_page": left["end_page"],
                                    },
                                    {
                                        "start_page": right["start_page"],
                                        "end_page": right["end_page"],
                                    },
                                ],
                            }
                        )
            issues.append(
                {
                    "type": "span_chain_integrity",
                    "group_id": gid,
                    "detail": "multiple spanning_tables entries for group_id",
                    "count": len(entries),
                }
            )

    expectations = _load_page_expectations()
    start_pages: dict[str, list[int]] = {}
    for page_num, exp in sorted(expectations.items()):
        span_info = exp.get("spanning_info")
        if span_info and span_info.get("role") == "start":
            start_pages.setdefault(span_info["group_id"], []).append(page_num)
        for el in exp.get("reading_order") or []:
            span = el.get("span")
            if span and span.get("role") == "start":
                start_pages.setdefault(span["group_id"], []).append(page_num)

    for gid, pages in start_pages.items():
        unique_pages = sorted(set(pages))
        if len(unique_pages) > 1:
            issues.append(
                {
                    "type": "span_chain_integrity",
                    "group_id": gid,
                    "detail": "merged span chain has duplicate start pages",
                    "pages": unique_pages,
                }
            )

def _validate_span_end_trailing_scheduled(issues: list[dict]) -> None:
    """Span end pages with PDF trailing prose must schedule prose:trailing in reading_order."""
    if fitz is None or not cfg.PDF_PATH.exists():
        return

    expectations = _load_page_expectations()
    doc = fitz.open(cfg.PDF_PATH)
    try:
        for span in _load_spanning_tables():
            if span.get("span_type") != "continuation":
                continue
            end_page = span["end_page"]
            page = doc[end_page - 1]
            bboxes = table_bboxes(cfg.PDF_PATH, end_page - 1)
            has_trailing = any(
                seg["role"] == "trailing" for seg in prose_segments(page, bboxes)
            )
            if not has_trailing:
                continue

            exp = expectations.get(end_page)
            if not exp:
                issues.append(
                    {
                        "type": "span_end_trailing_scheduled",
                        "page": end_page,
                        "group_id": span["group_id"],
                        "detail": "missing inventory for span end page with trailing prose",
                    }
                )
                continue

            reading_order = exp.get("reading_order") or []
            has_trailing_el = any(
                el.get("type") == "prose" and el.get("role") == "trailing"
                for el in reading_order
            )
            if not has_trailing_el:
                issues.append(
                    {
                        "type": "span_end_trailing_scheduled",
                        "page": end_page,
                        "group_id": span["group_id"],
                        "detail": "reading_order missing prose:trailing on span end page",
                    }
                )
    finally:
        doc.close()

def _validate_footnote_single_owner(text: str, issues: list[dict]) -> None:
    """Table 2 span (pages 24-25) must emit footnote 19 exactly once."""
    table_match = re.search(
        r"<!-- db:id=table_02_summary_descriptor_changes[^>]*-->",
        text,
    )
    start = table_match.start() if table_match else text.find("<!-- page:24 -->")
    if start < 0:
        start = 0
    end = text.find("<!-- page:26 -->")
    if end < 0:
        end = len(text)
    region = text[start:end]
    footnote_lines = re.findall(r"^19\.\s", region, re.M)
    count = len(footnote_lines)
    if count != 1:
        issues.append(
            {
                "type": "footnote_single_owner",
                "footnote": "19",
                "count": count,
                "detail": "footnote 19 must appear exactly once in Table 2 span (pages 24-25)",
                "pages": "24-25",
            }
        )

def _validate_bespoke_contract_gates(text: str, issues: list[dict]) -> None:
    """Target-page contract gates from attempt 3 design."""
    page_25 = _page_body_before_marker(text, 25)
    if "In addition to Chapter 2" not in page_25:
        issues.append(
            {
                "type": "missing_page_25_trailing_prose",
                "page": 25,
                "detail": 'trailing prose "In addition to Chapter 2" missing from final output',
            }
        )

    page_47 = _page_body_before_marker(text, 47)
    figure_pos = page_47.find("figure_11_reception_activities_strategies")
    if figure_pos < 0:
        figure_pos = page_47.lower().find("figure 11")
    header_pos = page_47.find("3.1. RECEPTION")
    if header_pos < 0:
        header_pos = page_47.lower().find("3.1. reception")
    if figure_pos >= 0 and header_pos >= 0 and header_pos < figure_pos:
        issues.append(
            {
                "type": "page_47_section_order",
                "page": 47,
                "detail": "section header 3.1. RECEPTION must follow Figure 11 block",
            }
        )
    elif figure_pos < 0 or header_pos < 0:
        issues.append(
            {
                "type": "page_47_section_order",
                "page": 47,
                "detail": "page 47 missing Figure 11 block or 3.1. RECEPTION header",
                "has_figure": figure_pos >= 0,
                "has_header": header_pos >= 0,
            }
        )

    for issue in issues:
        if issue.get("type") == "span_duplicate_emit" and issue.get("page") == 147:
            issues.append(
                {
                    "type": "page_147_span_duplicate",
                    "page": 147,
                    "group_id": issue.get("group_id"),
                    "detail": "page 147 must not appear in span_duplicate_emit issues",
                }
            )
            break

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
    if fitz is None or not cfg.PDF_PATH.exists():
        return 278
    doc = fitz.open(cfg.PDF_PATH)
    count = len(doc)
    doc.close()
    return count

def validate_final_output(md_path: Path | None = None) -> dict:
    

    md_path = md_path or final_markdown_path()
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

    for gid, mp in cfg.MULTIPAGE_ARTIFACTS.items():
        for p in range(mp["page_start"], mp["page_end"] + 1):
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

    _validate_span_chain_integrity(issues)
    _validate_span_end_trailing_scheduled(issues)
    _validate_footnote_single_owner(text, issues)
    _validate_reading_order_elements(text, issues)
    _validate_bespoke_contract_gates(text, issues)
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
    out = cfg.METADATA_DIR / "output_validation.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report