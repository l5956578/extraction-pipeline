"""Extract markdown per chunk based on inventory reading_order."""

from __future__ import annotations

import json
import re
from pathlib import Path

import fitz

import pipeline.config as cfg
from pipeline.descriptor_layout import extract_prose_zone
from pipeline.extractors.figures import figures_for_page
from pipeline.extractors.multipage import (
    merge_pdfplumber_tables,
    merge_rotated_pages,
    merge_section_block,
    merge_tables_by_title,
)
from pipeline.extractors.rich_text import extract_rich_page, extract_rich_page_excluding
from pipeline.extractors.rotated import extract_rotated_element, extract_rotated_tables
from pipeline.extractors.table import extract_tables
from pipeline.figures_catalog import FIGURE_CONTENT, figure_block
from pipeline.id_registry import ArtifactMeta, build_registry, registry_by_page
from pipeline.page_layout import (
    _span_text,
    classify_page_zones,
    extract_surgical_rotated_footnotes,
    format_page_footer,
)
from pipeline.pdf_links import append_inline_link_urls
from pipeline.span_detector import detect_spans
from pipeline.title_fix import fix_rotated_title
from pipeline.toc_layout import extract_toc_page
from pipeline.utils import artifact_header, slugify, table_to_markdown

def _is_figure_caption_line(text: str, fig_num: int | None = None) -> bool:
    """True only for real figure captions, not in-prose 'Figure 2, which appeared…'."""
    s = re.sub(r"\s+", " ", text.strip())
    # Captions are often fully bold: **Figure 2 – Title**
    s = re.sub(r"^\*+\s*", "", s)
    s = re.sub(r"\s*\*+$", "", s)
    # Caption form: Figure N – Title   (en-dash/em-dash/hyphen as separator)
    m = re.match(r"^Figure\s+(\d+)\s*[–—\-]\s+\S", s, re.I)
    if not m:
        return False
    if fig_num is not None and int(m.group(1)) != int(fig_num):
        return False
    return True

def _caption_y_on_page(page: fitz.Page, title: str) -> float | None:
    """Y of the real figure caption line (Figure N – …), never prose mentions."""
    mnum = re.search(r"Figure\s+(\d+)", title or "", re.I)
    fig_num = int(mnum.group(1)) if mnum else None
    norm_title = re.sub(r"\s+", " ", (title or "").strip().lower())
    for dash in ("–", "—", "−"):
        norm_title = norm_title.replace(dash, "-")

    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            text = _span_text(line.get("spans", [])).strip()
            if not text or not _is_figure_caption_line(text, fig_num):
                continue
            norm = re.sub(r"\s+", " ", text.lower())
            for dash in ("–", "—", "−"):
                norm = norm.replace(dash, "-")
            # Prefer exact/startswith title match; any valid caption for this N is OK.
            if norm.startswith(norm_title[:40]) or (fig_num and _is_figure_caption_line(text, fig_num)):
                return float(line["bbox"][1])
    return None

def _figure_crop_rect(page: fitz.Page, fig: dict) -> tuple[float, float, float, float] | None:
    """Return clip rect in page coords from registry crop fractions."""
    crop = fig.get("crop")
    if not crop:
        return None
    r = page.rect
    return (
        r.x0 + r.width * float(crop["x0"]),
        r.y0 + r.height * float(crop["y0"]),
        r.x0 + r.width * float(crop["x1"]),
        r.y0 + r.height * float(crop["y1"]),
    )

def _strip_figure_diagram_soup(text: str) -> str:
    """Remove flattened diagram labels left after rich_page (keep real prose).

    Never touch fenced code blocks (text_diagram trees use ```text).
    Also drops Fig 11-class activity leaf titles dual-emitted as prose (R1).
    """
    from pipeline.figure_inject import (
        _is_text_diagram_leaf_soup_line,
        strip_text_diagram_leaf_soup_global,
    )

    soup_only = re.compile(
        r"^(?:Linguistic|Sociolinguistic|Pragmatic|Savoir(?:-faire|-être| apprendre)?|"
        r"Reception|Production|Interaction|Mediation|"
        r"C2|C1|B2|B1|A2|A1|Pre-A1|"
        r"General competences|Communicative language (?:competences|activities|strategies)|"
        r"Overall language proficiency|"
        r"Understanding as a member of a live audience|"
        r"Understanding announcements and instructions|"
        r"Understanding audio \(or signed\) media and recordings|"
        r"Reading correspondence|Reading for orientation|"
        r"Reading instructions|Reading as a leisure activity|"
        r"Identifying cues and inferring|Watching TV, film and video|"
        r"Overall oral comprehension|Overall reading comprehension|"
        r"Oral comprehension|Reading comprehension|Audio-visual comprehension)$",
        re.I,
    )
    soup_tokens = {
        "linguistic", "sociolinguistic", "pragmatic", "savoir", "savoir-faire",
        "savoir-être", "savoir apprendre", "reception", "production", "interaction",
        "mediation", "c2", "c1", "b2", "b1", "a2", "a1", "pre-a1",
        "comprehension", "oral", "reading", "audio", "visual", "watching", "tv",
        "film", "video", "correspondence", "orientation", "instructions",
        "identifying", "cues", "inferring", "understanding", "audience", "member",
        "live", "announcements", "media", "recordings", "leisure", "argument",
        "conversation", "people", "signed",
    }
    keep: list[str] = []
    in_fence = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            keep.append(line)
            continue
        if in_fence:
            keep.append(line)
            continue
        if not s:
            keep.append(line)
            continue
        if soup_only.match(s) or _is_text_diagram_leaf_soup_line(line):
            continue
        if any(ch in s for ch in ("├", "└", "│", "─")):
            keep.append(line)
            continue
        words = re.findall(r"[A-Za-zÀ-ÿ0-9+\-]+", s.lower())
        if words and all(
            w in soup_tokens
            or w in {"and", "or", "the", "language", "competences", "activities", "strategies", "overall", "general", "communicative", "of", "a", "as", "for", "between", "other"}
            for w in words
        ) and len(s) < 160:
            continue
        plain_bold = re.sub(r"^\*+|\*+$", "", s).strip()
        if s.startswith("**") and len(s) < 220:
            bw = re.findall(r"[A-Za-zÀ-ÿ0-9+\-]+", plain_bold.lower())
            soup_ext = soup_tokens | {
                "language", "competences", "activities", "strategies",
                "overall", "general", "communicative", "proficiency",
            }
            if bw and all(w in soup_ext or w in {"and", "or", "the", "of"} for w in bw):
                continue
            if sum(
                1
                for k in (
                    "proficiency",
                    "communicative",
                    "competences",
                    "savoir",
                    "reception",
                    "comprehension",
                )
                if k in plain_bold.lower()
            ) >= 2:
                continue
        if re.match(r"^\*\*Figure\s+\d+", s, re.I):
            plain = re.sub(r"^\*+|\*+$", "", s).strip()
            if re.search(
                r"\d{2,}\s+(Overall|Linguistic|Savoir|Reception|Production|General)\b",
                plain,
                re.I,
            ):
                continue
            if plain.count("Savoir") + plain.count("Reception") + plain.count("Production") >= 2:
                continue
        keep.append(line)
    out: list[str] = []
    blank = 0
    for line in keep:
        if not line.strip():
            blank += 1
            if blank <= 2:
                out.append(line)
        else:
            blank = 0
            out.append(line)
    cleaned = "\n".join(out).strip()
    return strip_text_diagram_leaf_soup_global(cleaned)

def _png_figure_stub(fig: dict, page_num: int) -> str:
    fid = fig["id"]
    title = fig["title"]
    render = fig.get("render_as", "png")
    return (
        f"<!-- db:id={fid} type=figure render_as={render} "
        f"product_tier=context pages={page_num} -->\n"
        f"### {title} | {fid}\n"
    )

def _figure_exclusive_rects(
    page: fitz.Page, figs: list[dict]
) -> list[tuple[float, float, float, float]]:
    """Crop rects used for *selective* label filtering (C2-ADJ).

    Only registry crop regions. Do **not** expand upward to caption Y — that
    swallows body prose sharing the band (review #1 p.39–40). text_diagram
    without crop: no exclusive rect; catalog replace + soup strip handle dual emit.
    Filtering is lexicon-aware (keep real sentences inside crop y-band).
    """
    rects: list[tuple[float, float, float, float]] = []
    for fig in figs:
        crop_r = _figure_crop_rect(page, fig)
        if not crop_r:
            continue
        # Use crop interior only (slight inset) so edge-adjacent prose survives
        x0, y0, x1, y1 = crop_r
        pad_y = max(2.0, (y1 - y0) * 0.02)
        pad_x = max(2.0, (x1 - x0) * 0.02)
        rects.append((x0 + pad_x, y0 + pad_y, x1 - pad_x, y1 - pad_y))
    return rects

def _el_fence(etype: str, eid: str, page_num: int, body: str) -> str:
    """Optional RO element fences for postprocess boundary awareness (C2-ADJ P0)."""
    if not body or not body.strip():
        return body
    # Avoid double-fencing
    if "<!-- el:start" in body[:80]:
        return body
    start = f"<!-- el:start type={etype} id={eid} page={page_num} -->\n"
    end = f"\n<!-- el:end id={eid} -->\n"
    return start + body.rstrip() + end

def _extract_figure_page_composed(page: fitz.Page, page_num: int, el: dict) -> str:
    """Figure pages: selective crop filtering + figure stubs (C2-ADJ).

    Contract (inventory → extract → assembly):
    - Crop rects guide **label** exclusion only; real prose in the same y-band is kept.
    - Figures are clean stubs (text_diagram catalog or PNG header); apply_figures attaches assets.
    - Multi-fig pages emit figures in registry number order when unlocated.
    - Caption matching uses only ``Figure N – Title`` lines, not in-prose mentions.
    - Soup strip under images remains load-bearing for residual dual emission.
    """
    figs = figures_for_page(page_num)
    if not figs and el.get("artifact_id"):
        aid = el["artifact_id"]
        if aid in FIGURE_CONTENT:
            one = {
                "id": aid,
                "title": el.get("display_title") or aid,
                "render_as": "text_diagram",
                "page": page_num,
                "num": 0,
            }
            excl = _figure_exclusive_rects(page, [one])
            prose = extract_rich_page_excluding(page, page_num, excl)
            prose = _strip_figure_diagram_soup(prose)
            prose = append_inline_link_urls(page, prose)
            block = figure_block(aid)
            if prose.strip():
                return _compose_prose_with_figures(prose, [(0.0, one, block)])
            return append_inline_link_urls(page, block)
        figs = [
            {
                "id": aid,
                "title": el.get("display_title") or aid,
                "render_as": "png",
                "page": page_num,
                "num": 0,
            }
        ]

    exclude = _figure_exclusive_rects(page, figs) if figs else []
    prose = extract_rich_page_excluding(page, page_num, exclude)
    prose = append_inline_link_urls(page, prose)
    prose = _strip_figure_diagram_soup(prose)

    if not figs:
        return prose + ("\n" if prose and not prose.endswith("\n") else "")

    # Order: caption Y when known, else crop y0, else figure number (multi-fig stable).
    located: list[tuple[float, dict, str]] = []
    for fig in figs:
        y = _caption_y_on_page(page, fig.get("title") or "")
        if y is None:
            crop_r = _figure_crop_rect(page, fig)
            y = crop_r[1] if crop_r else 1e9
        if fig["id"] in FIGURE_CONTENT:
            block = figure_block(fig["id"])
        else:
            block = _png_figure_stub(fig, page_num)
        located.append((y if y is not None else 1e9, fig, block))
    # Prefer figure number for multi-fig so p.40 is 8→9→10 not scrambled
    if len(located) > 1:
        located.sort(key=lambda t: (t[1].get("num") or 0, t[0]))
    else:
        located.sort(key=lambda t: (t[0], t[1].get("num") or 0))

    body = _compose_prose_with_figures(prose, located)

    out_lines = body.splitlines()
    try:
        page_tables = extract_tables(page_num - 1, cfg.PDF_PATH)
    except Exception:  # noqa: BLE001
        page_tables = []
    joined = "\n".join(out_lines)
    # C2-F1 / L07-P38: do not dual-emit figure-as-table under PNG figures.
    # Prefer exclusive crop ownership; keyword match is secondary only.
    has_png_figure = any(
        (f.get("render_as") or "png") != "text_diagram" for f in (figs or [])
    )
    excl_rects = _figure_exclusive_rects(page, figs) if (figs and has_png_figure) else []
    table_bboxes: list[tuple[float, float, float, float]] = []
    if has_png_figure:
        try:
            import pdfplumber
            

            with pdfplumber.open(cfg.PDF_PATH) as _pdf:
                if 0 <= page_num - 1 < len(_pdf.pages):
                    for _t in _pdf.pages[page_num - 1].find_tables() or []:
                        table_bboxes.append(tuple(_t.bbox))  # type: ignore[arg-type]
        except Exception:  # noqa: BLE001
            table_bboxes = []

    def _table_overlaps_figure_crop(ti: int) -> bool:
        if not excl_rects or ti < 0 or ti >= len(table_bboxes):
            return False
        x0, y0, x1, y1 = table_bboxes[ti]
        for ex0, ey0, ex1, ey1 in excl_rects:
            # Axis-aligned overlap
            if x0 < ex1 and x1 > ex0 and y0 < ey1 and y1 > ey0:
                return True
        return False

    for ti, table in enumerate(page_tables or []):
        if not table:
            continue
        if _looks_like_narrative_callout(table):
            callout = _emit_narrative_callout(table)
            if callout and callout.strip() not in joined:
                out_lines.append("")
                out_lines.append(callout.strip())
                joined = "\n".join(out_lines)
            continue
        n_cells = sum(len(r or []) for r in table)
        if n_cells > 40:
            continue
        title = _table_title(table)
        # Skip tables owned by figure crop, or Level/descriptor samples under PNG.
        # Crop overlap is primary; keyword match is secondary for dual-emit samples.
        if has_png_figure and not (title and re.match(r"^Table\s+\d+", title or "", re.I)):
            if _table_overlaps_figure_crop(ti):
                continue
            flat = " ".join(
                str(c) for row in table for c in (row or []) if c
            ).lower()
            if re.search(r"\b(level|illustrative|descriptor|can understand)\b", flat):
                # Secondary: skip sample-level dual-emit (fig 6 class) on PNG pages
                continue
        md = table_to_markdown(table)
        if md.strip() and md.strip() not in joined:
            if title and re.match(r"^Table\s+\d+", title, re.I):
                out_lines.append("")
                out_lines.append(f"**{fix_rotated_title(title)}**")
                out_lines.append("")
                out_lines.append(md)
            else:
                out_lines.append("")
                out_lines.append(md)
            joined = "\n".join(out_lines)

    body = _strip_figure_diagram_soup("\n".join(out_lines))
    try:
        from pipeline.figure_inject import strip_garbage_under_figure_images

        body = strip_garbage_under_figure_images(body)
    except Exception:  # noqa: BLE001
        pass
    return body + ("\n" if body and not body.endswith("\n") else "")

def _compose_prose_with_figures(
    prose: str, located: list[tuple[float, dict, str]]
) -> str:
    """Replace caption lines with figure blocks; append missing figures by number."""
    by_num: dict[int, tuple[dict, str]] = {}
    for y, fig, block in located:
        num_m = re.search(r"Figure\s+(\d+)", fig.get("title") or "", re.I)
        if num_m:
            by_num[int(num_m.group(1))] = (fig, block)
        elif fig.get("num"):
            by_num[int(fig["num"])] = (fig, block)

    used_nums: set[int] = set()
    out_lines: list[str] = []
    for line in prose.splitlines():
        s = line.strip()
        s_plain = re.sub(r"^\*+\s*", "", s)
        s_plain = re.sub(r"\s*\*+$", "", s_plain)
        mcap = re.match(r"^Figure\s+(\d+)\s*[–—\-]\s+\S", s_plain, re.I)
        if mcap:
            n = int(mcap.group(1))
            if n in by_num and n not in used_nums:
                _fig, block = by_num[n]
                out_lines.append(block.rstrip())
                out_lines.append("")
                used_nums.add(n)
                continue
            if n in used_nums:
                continue
        out_lines.append(line)

    # Append unlocated figures in ascending figure number (stable multi-fig order)
    missing = sorted(
        (
            (n, fig, block)
            for n, (fig, block) in by_num.items()
            if n not in used_nums
        ),
        key=lambda t: t[0],
    )
    for n, fig, block in missing:
        out_lines.append("")
        out_lines.append(block.rstrip())
        used_nums.add(n)
    # Any leftover without number
    for y, fig, block in located:
        if fig["id"] not in "\n".join(out_lines):
            out_lines.append("")
            out_lines.append(block.rstrip())
    return "\n".join(out_lines)

class _ExtractContext:
    def __init__(self, art_by_id: dict, art_by_title: dict):
        self.art_by_id = art_by_id
        self.art_by_title = art_by_title
        self.emitted_spans: set[str] = set()

def _emit_artifact(art: ArtifactMeta, page_start: int, page_end: int, body: str) -> str:
    pages = f"{page_start}-{page_end}" if page_end > page_start else str(page_start)
    display = fix_rotated_title(art.display_name)
    header = artifact_header(
        art.id,
        display,
        art.artifact_type,
        art.product_tiers,
        pages,
    )
    body = (body or "").lstrip("\n")
    # Blank line before markdown table at emit (L07-TABLE-BLANK root)
    if body.startswith("|"):
        return f"{header}\n{body}\n"
    return f"{header}\n{body}\n" if body else f"{header}\n"

def _emit_artifact_from_element(el: dict, body: str, ctx: _ExtractContext) -> str:
    from pipeline.title_fix import clean_artifact_id

    aid = el.get("artifact_id") or "unknown"
    art = ctx.art_by_id.get(aid)
    display = fix_rotated_title(el.get("display_title") or (art.display_name if art else aid))
    aid = clean_artifact_id(aid, display)
    span = el.get("span") or {}
    pages_list = span.get("pages") or []
    if pages_list:
        p_start, p_end = pages_list[0], pages_list[-1]
        pages = f"{p_start}-{p_end}" if p_end > p_start else str(p_start)
    elif art:
        p_start, p_end = art.page_start, art.page_end
        pages = f"{p_start}-{p_end}" if p_end > p_start else str(p_start)
    else:
        pages = "?"
    tiers = art.product_tiers if art else ["context"]
    atype = el.get("artifact_type") or (art.artifact_type if art else "descriptor_scale")
    header = artifact_header(aid, display, atype, tiers, pages)
    body = (body or "").lstrip("\n")
    if body.startswith("|"):
        return f"{header}\n{body}\n"
    return f"{header}\n{body}\n" if body else f"{header}\n"

def _emit_page_footer(page: fitz.Page, page_num: int, skip_footnotes: bool = False) -> str:
    zones = classify_page_zones(page)
    if skip_footnotes:
        zones = {**zones, "footnotes": []}
    return format_page_footer(page_num, zones)

def _emit_footnote_zone(page: fitz.Page) -> str | None:
    zones = classify_page_zones(page)
    footnotes = zones.get("footnotes") or []
    if not footnotes:
        return None
    return "\n\n".join(footnotes) + "\n"

def _emit_rotated_footnote_zone(page: fitz.Page, table_bbox: list[float]) -> str | None:
    footnotes = extract_surgical_rotated_footnotes(page, tuple(table_bbox))
    if not footnotes:
        return None
    return "\n\n".join(footnotes) + "\n"

def _table_title(table: list[list]) -> str | None:
    if not table or not table[0]:
        return None
    for cell in table[0]:
        if cell and str(cell).strip():
            return re.sub(r"\s+", " ", str(cell).strip())
    return None

def _artifact_for_table_title(
    title: str | None, ctx: _ExtractContext, primary_art: ArtifactMeta | None
) -> ArtifactMeta | None:
    if not title:
        return primary_art
    from pipeline.title_fix import artifact_id_from_title

    fixed = fix_rotated_title(title)
    aid = artifact_id_from_title(fixed, prefix="scale")
    if aid in ctx.art_by_id:
        return ctx.art_by_id[aid]
    by_name = ctx.art_by_title.get(fixed.strip().lower()) or ctx.art_by_title.get(
        title.strip().lower()
    )
    if by_name:
        return by_name
    if primary_art and fix_rotated_title(primary_art.display_name).strip().lower() == fixed.strip().lower():
        return primary_art
    return None

def _merge_multipage_body(gid: str, page_nums: list[int], art: ArtifactMeta | None, pdf_path) -> str:
    from pipeline.config import feature_enabled

    # When multipage_merge is off, extract the first page only (no cross-page join).
    if not feature_enabled("multipage_merge"):
        indices = [page_nums[0] - 1] if page_nums else []
        return merge_pdfplumber_tables(indices, pdf_path) if indices else ""

    if gid in cfg.MULTIPAGE_ARTIFACTS:
        mp = cfg.MULTIPAGE_ARTIFACTS[gid]
        indices = list(range(mp["page_start"] - 1, mp["page_end"]))
        return merge_pdfplumber_tables(indices, pdf_path)
    title_key = art.display_name if art else gid.replace("scale_", "").replace("_", " ")
    indices = [p - 1 for p in page_nums]
    body = merge_tables_by_title(indices, pdf_path, title_key)
    if not body.strip():
        body = merge_pdfplumber_tables(indices, pdf_path)
    return body

def _extract_span_body(
    el: dict,
    doc: fitz.Document,
    ctx: _ExtractContext,
) -> str:
    span = el["span"]
    page_nums = span["pages"]
    gid = span["group_id"]
    art = ctx.art_by_id.get(gid) or ctx.art_by_id.get(el.get("artifact_id", ""))

    from pipeline.config import feature_enabled

    if el.get("extractor") == "section_block_merge":
        if not feature_enabled("multipage_merge"):
            # Single-page geometry for the span start only.
            return merge_section_block(doc, page_nums[:1] or page_nums, cfg.PDF_PATH)
        return merge_section_block(doc, page_nums, cfg.PDF_PATH)

    if el.get("text_direction") == "ocr" or el.get("extractor") == "rotated_table":
        if not feature_enabled("rotated_tables"):
            return (
                f"<!-- ROTATED_TABLES_DISABLED pages="
                f"{page_nums[0]}-{page_nums[-1]} gid={gid} -->\n"
            )
        method = el.get("rotated_extraction_method") or "grok_vision"
        use_vision = method == "grok_vision" and feature_enabled("agent_vision")
        if use_vision:
            from pipeline.extractors.rotated_grok_vision import extract_rotated_span_via_grok

            title = fix_rotated_title(
                el.get("display_title") or (art.display_name if art else "") or gid
            )
            body = extract_rotated_span_via_grok(
                page_nums,
                gid,
                title,
                rotation=el.get("rotation", 90),
            )
            # Prefer agent vision markdown; if still pending, geometry keeps book complete.
            if "GROK_VISION_PENDING" not in body:
                return body
            geo = merge_rotated_pages(
                doc, page_nums, cfg.PDF_PATH, rotation=el.get("rotation", 90)
            )
            return (
                f"<!-- AGENT_VISION_PENDING geometry_fallback pages="
                f"{page_nums[0]}-{page_nums[-1]} gid={gid} -->\n{geo}"
            )
        # Explicit geometry / hybrid override, or agent_vision feature off
        return merge_rotated_pages(doc, page_nums, cfg.PDF_PATH, rotation=el.get("rotation", 90))

    return _merge_multipage_body(gid, page_nums, art, cfg.PDF_PATH)

def _looks_like_narrative_callout(table: list[list]) -> bool:
    """Single-column narrative / sidebar boxes are not descriptor scales.

    Includes p.35 “Can do” callout and p.29 “A reminder of CEFR 2001 chapters”.
    """
    if not table:
        return False
    width = max((len(r) for r in table), default=0)
    filled_cols = 0
    for c in range(width):
        if any((r[c] if c < len(r) and r[c] else None) for r in table):
            filled_cols += 1
    if filled_cols > 1:
        return False
    texts = [
        str(c).strip()
        for r in table
        for c in (r or [])
        if c and str(c).strip()
    ]
    if len(texts) < 2:
        return False
    joined = " ".join(texts).lower()
    if re.search(r"\b(c2|c1|b2|b1|a2|a1|pre-a1)\b", texts[0], re.I) and width >= 2:
        return False
    if "reception" in joined and "production" in joined and "interaction" in joined:
        return False
    # Chapter reminder sidebars: short Chapter N lines
    chapter_hits = sum(1 for t in texts if re.match(r"^Chapter\s+\d+", t, re.I))
    if chapter_hits >= 3:
        return True
    # Title-ish first cell + long body cells
    long_body = sum(1 for t in texts[1:] if len(t) > 60)
    return long_body >= 1

def _emit_narrative_callout(table: list[list]) -> str:
    """Emit callout/sidebar as blockquote (docs/CONTRACTS.md §3 / UV-01).

    Single title, no double-emit (C2-ADJ P2). Format::
        > **Title**
        >
        > Paragraph…
    """
    from pipeline.config import feature_enabled

    if not feature_enabled("callouts"):
        return ""
    from pipeline.callout_detect import emit_callout_blockquote

    texts = [
        re.sub(r"\s+", " ", str(c).replace("\n", " ")).strip()
        for r in table
        for c in (r or [])
        if c and str(c).strip()
    ]
    if not texts:
        return ""
    # First cell may glue title + body; emit_callout_blockquote splits + dedupes.
    return emit_callout_blockquote(texts, title=None)

def _table_title_is_numbered(title: str | None) -> re.Match | None:
    if not title:
        return None
    return re.match(r"^Table\s+(\d+)\s*[–—\-]\s+(.+)$", title.strip(), re.I)

def _extract_single_table(
    page: fitz.Page,
    page_num: int,
    el: dict,
    art: ArtifactMeta | None,
    ctx: _ExtractContext,
) -> str:
    if el.get("extractor") == "rotated_table" or el.get("text_direction") == "ocr":
        from pipeline.config import feature_enabled

        if not feature_enabled("rotated_tables"):
            gid = el.get("artifact_id") or "unknown"
            return f"<!-- ROTATED_TABLES_DISABLED page={page_num} gid={gid} -->\n"
        method = el.get("rotated_extraction_method") or "grok_vision"
        use_vision = method == "grok_vision" and feature_enabled("agent_vision")
        if use_vision:
            from pipeline.extractors.rotated_grok_vision import extract_single_rotated_via_grok

            gid = el.get("artifact_id") or "unknown"
            title = fix_rotated_title(el.get("display_title") or gid)
            body = extract_single_rotated_via_grok(
                page_num,
                gid,
                title,
                rotation=el.get("rotation", 90),
            )
            if "GROK_VISION_PENDING" not in body:
                return body
            geo = extract_rotated_element(page_num - 1, page, cfg.PDF_PATH, el)
            return (
                f"<!-- AGENT_VISION_PENDING geometry_fallback page={page_num} gid={gid} -->\n{geo}"
            )
        return extract_rotated_element(page_num - 1, page, cfg.PDF_PATH, el)

    tables = extract_tables(page_num - 1, cfg.PDF_PATH)
    if not tables:
        return ""

    table_index = el.get("table_index", 0)
    if table_index >= len(tables):
        return ""
    table = tables[table_index]

    # Narrative callout boxes → prose, not descriptor_scale tables.
    if _looks_like_narrative_callout(table):
        return _emit_narrative_callout(table)

    md = table_to_markdown(table)
    if not md.strip():
        return ""

    title = _table_title(table)
    # Prefer numbered Table N titles / explicit index map over auto scale_* ids.
    numbered = _table_title_is_numbered(title)
    known_by_idx = cfg.KNOWN_TABLES_BY_INDEX.get((page_num, table_index))
    if known_by_idx:
        known_id, known_title, known_type = known_by_idx
        table_art = ctx.art_by_id.get(known_id) or ArtifactMeta(
            id=known_id,
            display_name=known_title,
            artifact_type=known_type,
            product_tiers=["context"],
            page_start=page_num,
            page_end=page_num,
        )
        return _emit_artifact(table_art, page_num, page_num, md)

    if page_num in cfg.KNOWN_TABLES_FIGURES and (
        table_index == 0 or numbered
    ):
        known_id, known_title, known_type = cfg.KNOWN_TABLES_FIGURES[page_num]
        # Only apply known when this table is the known one (title match or sole table).
        if numbered or len(tables) == 1 or table_index == 0 and not any(
            _table_title_is_numbered(_table_title(t)) for t in tables if t is not table
        ):
            table_art = ctx.art_by_id.get(known_id) or ArtifactMeta(
                id=known_id,
                display_name=known_title,
                artifact_type=known_type,
                product_tiers=["context"],
                page_start=page_num,
                page_end=page_num,
            )
            return _emit_artifact(
                table_art, table_art.page_start, table_art.page_end, md
            )

    if numbered:
        num, rest = numbered.group(1), numbered.group(2).strip()
        aid = slugify(f"table_{int(num):02d}_{rest}")
        table_art = ctx.art_by_id.get(aid) or ArtifactMeta(
            id=aid,
            display_name=fix_rotated_title(title),
            artifact_type="table",
            product_tiers=["context"],
            page_start=page_num,
            page_end=page_num,
        )
        return _emit_artifact(table_art, page_num, page_num, md)

    if table_index == 0 and art and page_num == art.page_start:
        # Do not promote narrative callouts / wrong first-column titles to scale.
        if art.artifact_type == "descriptor_scale" and _looks_like_narrative_callout(table):
            return _emit_narrative_callout(table)
        table_art = art
    else:
        table_art = _artifact_for_table_title(
            title, ctx, art if table_index == 0 else None
        )
    if table_art:
        # Guard: first-column header "Reception" etc. should not become scale id
        # when the table is a multi-column strategy matrix.
        if (
            table_art.artifact_type == "descriptor_scale"
            and table
            and max(len(r) for r in table) >= 3
            and not re.match(r"^(Overall |Can |scale_)", table_art.display_name or "", re.I)
        ):
            # Prefer table type with a stable slug from display/title if Table N missing.
            header_cells = [str(c).strip() for c in table[0] if c and str(c).strip()]
            if header_cells and not re.match(r"^Table\s+\d+", header_cells[0], re.I):
                # Strategy matrices often have empty corner + mode headers.
                modes = " ".join(header_cells).lower()
                if any(k in modes for k in ("reception", "production", "interaction", "mediation")):
                    aid = f"table_p{page_num:03d}_{slugify(header_cells[0] if header_cells else 'grid')}"
                    # Prefer known Table 4 title when on p.35
                    if page_num == 35:
                        aid = "table_04_communicative_language_strategies"
                        disp = "Table 4 – Communicative language strategies in the CEFR"
                    else:
                        disp = fix_rotated_title(
                            el.get("display_title") or " | ".join(header_cells[:4])
                        )
                    table_art = ArtifactMeta(
                        id=aid,
                        display_name=disp,
                        artifact_type="table",
                        product_tiers=["context"],
                        page_start=page_num,
                        page_end=page_num,
                    )
        return _emit_artifact(
            table_art, table_art.page_start, table_art.page_end, md
        )
    return md

def _extract_element(
    el: dict,
    page: fitz.Page,
    page_num: int,
    page_info: dict,
    art: ArtifactMeta | None,
    doc: fitz.Document,
    ctx: _ExtractContext,
) -> str | None:
    etype = el["type"]

    if etype == "toc":
        return extract_toc_page(page, page_num) + "\n"

    if etype == "span_continuation_skip":
        return None

    if etype == "footnote_zone":
        if el.get("extractor") == "rotated_footnote_zone" and el.get("table_bbox"):
            block = _emit_rotated_footnote_zone(page, el["table_bbox"])
        else:
            block = _emit_footnote_zone(page)
        return (block + "\n") if block else None

    if etype == "footer":
        # Rotated start pages: footnotes come from rotated_footnote_zone only.
        skip_footnotes = el.get("skip_footnotes", False)
        reading_order = page_info.get("reading_order") or []
        has_rotated_footnote_zone = any(
            item.get("type") == "footnote_zone"
            and item.get("extractor") == "rotated_footnote_zone"
            for item in reading_order
        )
        if has_rotated_footnote_zone:
            skip_footnotes = True
        return _emit_page_footer(
            page, page_num, skip_footnotes=skip_footnotes
        ) + "\n"

    if etype == "figure_page":
        return _extract_figure_page_composed(page, page_num, el) + "\n"

    if etype == "figure":
        aid = el.get("artifact_id") or ""
        if aid in FIGURE_CONTENT:
            return append_inline_link_urls(page, figure_block(aid)) + "\n"
        # Prefer registry compose when multiple figures share the page.
        if len(figures_for_page(page_num)) > 1:
            return _extract_figure_page_composed(page, page_num, el) + "\n"
        reg = next((f for f in figures_for_page(page_num) if f["id"] == aid), None)
        if reg and reg.get("render_as") != "text_diagram":
            return append_inline_link_urls(page, _png_figure_stub(reg, page_num)) + "\n"
        art_meta = ctx.art_by_id.get(aid)
        display = fix_rotated_title(
            el.get("display_title") or (art_meta.display_name if art_meta else aid or "Figure")
        )
        tiers = art_meta.product_tiers if art_meta else ["context"]
        atype = art_meta.artifact_type if art_meta else "figure"
        header = artifact_header(aid or "unknown", display, atype, tiers, str(page_num))
        return append_inline_link_urls(page, header) + "\n"

    if etype == "prose":
        if el.get("extractor") == "rich_page":
            return append_inline_link_urls(page, extract_rich_page(page, page_num)) + "\n"
        scale_title = fix_rotated_title(art.display_name) if art else None
        bbox = el.get("bbox")
        if not bbox:
            return None
        text = extract_prose_zone(page, bbox, scale_title=scale_title)
        if text and scale_title:
            text = re.sub(
                rf"\n###\s*{re.escape(scale_title)}\s*$",
                "",
                text,
                flags=re.I,
            ).strip()
            if re.fullmatch(rf"###\s*{re.escape(scale_title)}\s*", text, flags=re.I):
                text = ""
        if text:
            text = append_inline_link_urls(page, text)
        return (text + "\n") if text else None

    if etype == "artifact" and (
        el.get("artifact_type") == "callout" or el.get("extractor") == "callout_bbox"
    ):
        from pipeline.config import feature_enabled

        if not feature_enabled("callouts"):
            return None
        from pipeline.callout_detect import (
            callout_paragraphs_from_bbox,
            emit_callout_blockquote,
            registry_callouts_for_page,
        )

        bbox = el.get("bbox")
        if not bbox:
            return None
        paras = callout_paragraphs_from_bbox(page, tuple(bbox))
        title = el.get("display_title")
        # Optional registry title / lead for this page
        for reg in registry_callouts_for_page(page_num):
            if reg.get("title") and not title:
                title = reg["title"]
        body = emit_callout_blockquote(paras, title=title if title else None)
        if body:
            body = append_inline_link_urls(page, body)
        return (body + "\n") if body else None

    if etype == "artifact":
        span = el.get("span")
        if span:
            gid = span["group_id"]
            if gid in ctx.emitted_spans:
                return None
            ctx.emitted_spans.add(gid)
            body = _extract_span_body(el, doc, ctx)
            art_emit = ctx.art_by_id.get(gid) or art
            if art_emit:
                return _emit_artifact(
                    art_emit, span["pages"][0], span["pages"][-1], body
                )
            return _emit_artifact_from_element(el, body, ctx)

        body = _extract_single_table(page, page_num, el, art, ctx)
        return (body + "\n") if body else None

    return None

def extract_chunk(chunk_id: str) -> str:
    inv_path = cfg.INVENTORIES_DIR / f"{chunk_id}_inventory.json"
    inventory = json.loads(inv_path.read_text(encoding="utf-8"))
    _, artifacts = _get_spans_and_artifacts()
    art_by_id = {a.id: a for a in artifacts}
    art_by_page = registry_by_page(artifacts)
    art_by_title = {a.display_name.strip().lower(): a for a in artifacts}
    ctx = _ExtractContext(art_by_id, art_by_title)

    doc = fitz.open(cfg.PDF_PATH)
    parts: list[str] = []
    parts.append(f"# {chunk_id} (pages {inventory['start_page']}-{inventory['end_page']})\n")

    for page_info in inventory["pages"]:
        page_num = page_info["page_number"]
        page = doc[page_num - 1]
        art = art_by_page.get(page_num)
        reading_order = page_info.get("reading_order") or []

        for el in reading_order:
            block = _extract_element(el, page, page_num, page_info, art, doc, ctx)
            if not block:
                continue
            # C2-ADJ P0: fence RO elements so postprocess never soft-joins across them
            etype = el.get("type") or "unknown"
            if etype not in ("footer", "span_continuation_skip"):
                eid = (
                    el.get("artifact_id")
                    or el.get("id")
                    or f"{etype}_p{page_num:03d}_s{el.get('seq', 0)}"
                )
                block = _el_fence(etype, str(eid), page_num, block)
            parts.append(block)

    doc.close()
    cfg.RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = cfg.RAW_DIR / f"{chunk_id}.md"
    content = "\n".join(parts)
    out.write_text(content, encoding="utf-8")
    print(f"Extracted {out.name} ({len(content)} chars)")
    return str(out)

_CACHED_SPANS = None
_CACHED_ARTIFACTS = None

def _get_spans_and_artifacts():
    global _CACHED_SPANS, _CACHED_ARTIFACTS
    if _CACHED_SPANS is None:
        _CACHED_SPANS = detect_spans()
        _CACHED_ARTIFACTS = build_registry(_CACHED_SPANS)
    return _CACHED_SPANS, _CACHED_ARTIFACTS

def extract_all_chunks(skip_existing: bool = False) -> list[str]:
    outputs = []
    for inv in sorted(cfg.INVENTORIES_DIR.glob("chunk_*_inventory.json")):
        chunk_id = inv.stem.replace("_inventory", "")
        out_path = cfg.RAW_DIR / f"{chunk_id}.md"
        if skip_existing and out_path.exists() and out_path.stat().st_size > 500:
            print(f"Skipping {chunk_id} (already extracted)")
            outputs.append(str(out_path))
            continue
        outputs.append(extract_chunk(chunk_id))
    return outputs

if __name__ == "__main__":
    import argparse

    from pipeline.bootstrap import add_job_argument, bootstrap_job

    parser = argparse.ArgumentParser(description="Extract markdown for one or all chunks")
    add_job_argument(parser)
    parser.add_argument(
        "chunk_id",
        nargs="?",
        help="Chunk id to extract (e.g. chunk_01). Omit to extract all chunks.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Extract all chunks (default when chunk_id is omitted)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip chunks whose raw output already exists and is non-trivial",
    )
    args = parser.parse_args()
    bootstrap_job(args.job)

    if args.chunk_id:
        extract_chunk(args.chunk_id)
    else:
        extract_all_chunks(skip_existing=args.skip_existing)