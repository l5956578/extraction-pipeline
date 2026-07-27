"""Detect multi-page table continuations and section blocks."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict

import fitz
import pdfplumber

import pipeline.config as cfg
from pipeline.title_fix import fix_rotated_title

@dataclass
class SpanGroup:
    group_id: str
    span_type: str  # continuation | series | section_block
    start_page: int
    end_page: int
    title: str
    rotated: bool = False

def _is_table_page(page: fitz.Page) -> bool:
    drawings = page.get_drawings()
    h = sum(
        1
        for d in drawings
        if abs(d["rect"].width) > abs(d["rect"].height) * 3 and d["rect"].width > 50
    )
    v = sum(
        1
        for d in drawings
        if abs(d["rect"].height) > abs(d["rect"].width) * 3 and d["rect"].height > 50
    )
    return h > 10 and v > 5

def _is_rotated(page: fitz.Page) -> bool:
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            d = line.get("dir", (1, 0))
            if abs(d[1]) > 0.3:
                return True
    return False

def _first_table_title(plumber_page) -> str | None:
    tables = plumber_page.extract_tables() or []
    if not tables or not tables[0]:
        return None
    row0 = tables[0][0]
    if not row0:
        return None
    for cell in row0:
        if cell and str(cell).strip():
            raw = re.sub(r"\s+", " ", str(cell).strip())
            return fix_rotated_title(raw)
    return None

def _has_table_caption(text: str) -> bool:
    return bool(re.search(r"\bTable\s+\d+\b", text, re.I))

def _slug_from_title(title: str) -> str:
    from pipeline.utils import slugify

    fixed = fix_rotated_title(title)
    return slugify(fixed, prefix="scale")

def _normalize_title(title: str | None) -> str | None:
    if not title:
        return None
    return re.sub(r"\s+", " ", fix_rotated_title(title).strip()).lower()

def _spans_overlap_or_adjacent(a: SpanGroup, b: SpanGroup) -> bool:
    """True when two spans share a page or touch at a page boundary."""
    return not (a.end_page < b.start_page - 1 or b.end_page < a.start_page - 1)

def _merge_span_pair(a: SpanGroup, b: SpanGroup, doc: fitz.Document) -> SpanGroup:
    start_page = min(a.start_page, b.start_page)
    end_page = max(a.end_page, b.end_page)
    title = a.title if (a.end_page - a.start_page) >= (b.end_page - b.start_page) else b.title
    pages = range(start_page - 1, end_page)
    return SpanGroup(
        group_id=a.group_id,
        span_type=a.span_type,
        start_page=start_page,
        end_page=end_page,
        title=fix_rotated_title(title),
        rotated=any(_is_rotated(doc[p]) for p in pages),
    )

def _add_continuation(
    groups: list[SpanGroup],
    gid: str,
    start_page: int,
    end_page: int,
    title: str,
    doc: fitz.Document,
) -> None:
    """Add or extend a continuation span, merging overlapping/adjacent same-group spans."""
    candidate = SpanGroup(
        group_id=gid,
        span_type="continuation",
        start_page=start_page,
        end_page=end_page,
        title=fix_rotated_title(title),
        rotated=False,
    )
    merged: list[SpanGroup] = []
    absorbed = False
    for g in groups:
        if g.group_id == gid and g.span_type == "continuation" and _spans_overlap_or_adjacent(g, candidate):
            candidate = _merge_span_pair(g, candidate, doc)
            absorbed = True
            continue
        merged.append(g)
    if not absorbed:
        pages = range(start_page - 1, end_page)
        candidate.rotated = any(_is_rotated(doc[p]) for p in pages)
    merged.append(candidate)
    groups[:] = merged

def _merge_continuation_chains(
    groups: list[SpanGroup],
    doc: fitz.Document,
) -> list[SpanGroup]:
    """Collapse pairwise N→N+1 continuation detections into single chains."""
    continuations: list[SpanGroup] = []
    other: list[SpanGroup] = []
    for g in groups:
        if g.span_type == "continuation":
            continuations.append(g)
        else:
            other.append(g)

    by_gid: dict[str, list[SpanGroup]] = {}
    for g in continuations:
        by_gid.setdefault(g.group_id, []).append(g)

    merged_continuations: list[SpanGroup] = []
    for gid, spans in by_gid.items():
        spans.sort(key=lambda s: (s.start_page, s.end_page))
        chain = spans[0]
        for nxt in spans[1:]:
            if _spans_overlap_or_adjacent(chain, nxt):
                chain = _merge_span_pair(chain, nxt, doc)
            else:
                merged_continuations.append(chain)
                chain = nxt
        merged_continuations.append(chain)

    result = other + merged_continuations
    result.sort(key=lambda g: (g.start_page, g.end_page))
    return result

def _detect_adjacent_title_continuations(
    pdf: pdfplumber.PDF,
    doc: fitz.Document,
    groups: list[SpanGroup],
) -> None:
    """Match continuation when page N and N+1 share the same first-table title."""
    for i in range(len(pdf.pages) - 1):
        t1 = _first_table_title(pdf.pages[i])
        t2 = _first_table_title(pdf.pages[i + 1])
        if not t1 or not t2:
            continue
        if _normalize_title(t1) != _normalize_title(t2):
            continue
        gid = _slug_from_title(t1)
        _add_continuation(groups, gid, i + 1, i + 2, t1, doc)

def detect_spans() -> list[SpanGroup]:
    doc = fitz.open(cfg.PDF_PATH)
    groups: list[SpanGroup] = []

    # Hard-coded section blocks from plan/TOC
    for block in cfg.SECTION_BLOCKS:
        pages = range(block["page_start"] - 1, block["page_end"])
        groups.append(
            SpanGroup(
                group_id=block["id"],
                span_type="section_block",
                start_page=block["page_start"],
                end_page=block["page_end"],
                title=block["display_name"],
                rotated=any(_is_rotated(doc[p]) for p in pages),
            )
        )

    with pdfplumber.open(cfg.PDF_PATH) as pdf:
        i = 0
        while i < doc.page_count:
            if not _is_table_page(doc[i]):
                i += 1
                continue

            start = i
            titles: list[str | None] = []
            while i < doc.page_count and _is_table_page(doc[i]):
                titles.append(_first_table_title(pdf.pages[i]))
                i += 1

            if i - start < 2:
                continue

            # Check if this is a continuation chain (same title across pages)
            first_title = titles[0]
            if first_title:
                j = start + 1
                while j < i:
                    if titles[j - start] == first_title:
                        # continuation from start..j
                        gid = _slug_from_title(first_title)
                        if not any(g.group_id == gid for g in groups):
                            groups.append(
                                SpanGroup(
                                    group_id=gid,
                                    span_type="continuation",
                                    start_page=start + 1,
                                    end_page=j + 1,
                                    title=first_title,
                                    rotated=any(_is_rotated(doc[p]) for p in range(start, j + 1)),
                                )
                            )
                    j += 1

            # Long rotated runs only (Appendix 5) — do not group consecutive descriptor-scale pages.
            if i - start >= 10 and all(_is_rotated(doc[p]) for p in range(start, i)):
                groups.append(
                    SpanGroup(
                        group_id="appendix_5_domain_examples",
                        span_type="series",
                        start_page=start + 1,
                        end_page=i,
                        title="Examples of use in different domains",
                        rotated=True,
                    )
                )

        _detect_adjacent_title_continuations(pdf, doc, groups)

    # Explicit known continuations from analysis
    explicit = [
        ("scale_vocabulary_control", "continuation", 132, 133, "Vocabulary control"),
        ("table_02_summary_descriptor_changes", "continuation", 24, 25, "Table 2"),
        (
            "scale_expressing_a_personal_response_to_creative_texts_including_literature",
            "continuation",
            106,
            107,
            "Expressing a personal response to creative texts (including literature)",
        ),
        (
            "scale_setting_and_perspectives",
            "continuation",
            162,
            163,
            "Setting and perspectives",
        ),
        (
            "scale_sign_language_repertoire",
            "continuation",
            146,
            148,
            "Sign language repertoire",
        ),
    ]
    for gid, stype, s, e, title in explicit:
        if stype == "continuation":
            _add_continuation(groups, gid, s, e, title, doc)
        elif not any(g.group_id == gid and g.start_page == s for g in groups):
            pages = range(s - 1, e)
            groups.append(
                SpanGroup(
                    group_id=gid,
                    span_type=stype,
                    start_page=s,
                    end_page=e,
                    title=title,
                    rotated=any(_is_rotated(doc[p]) for p in pages),
                )
            )

    groups = _merge_continuation_chains(groups, doc)
    doc.close()
    return groups

def save_spans(groups: list[SpanGroup]) -> str:
    cfg.METADATA_DIR.mkdir(parents=True, exist_ok=True)
    path = cfg.METADATA_DIR / "spanning_tables.json"
    payload = [asdict(g) for g in groups]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(path)

if __name__ == "__main__":
    from pipeline.bootstrap import parse_and_load_job

    parse_and_load_job(description="Detect multi-page spans")
    spans = detect_spans()
    out = save_spans(spans)
    print(f"Wrote {len(spans)} span groups to {out}")