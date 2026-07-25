"""
Rotated descriptor tables — agent vision extraction (coding agent only).

Geometry/OCR cannot reliably extract rotated CEFR scale tables. Chat/web Grok
drafts are **not** part of the pipeline (optional offline tool only; never required).

Canonical path:
  1. prepare_*  — crop PNG + JSON + handoff → metadata/rotated_for_grok/
  2. **Agent vision (required for quality)** — coding agent re-reads each
       page_*.png in-session with multimodal vision and writes
       metadata/rotated_from_grok/{slug}.md
  3. assemble_* — merge per-page .md into span body
  4. finalize_after_grok.py / full extract — cleanup + merge

If .md is missing, extract_chunk falls back to geometry with an
``AGENT_VISION_PENDING`` HTML comment so the book still builds.

Slug: page_{page:03d}_{span_group_id}

Footnotes on rotated pages stay on geometry surgical path (rotated_footnote_zone).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import fitz
import pdfplumber

from pipeline.config import (
    INVENTORIES_DIR,
    PDF_PATH,
    RENDER_SCALE,
    ROTATED_FOR_GROK_DIR,
    ROTATED_FROM_GROK_DIR,
)

MANIFEST_NAME = "manifest.json"

AGENT_VISION_INSTRUCTIONS = """
AGENT VISION EXTRACTION (rotated tables only — user is out of the loop)
=======================================================================
You (coding agent with vision) are the sole authoritative extractor for rotated
descriptor-scale tables. Do **not** ask the user to upload PNGs to chat/web Grok.

For each pending slug in metadata/rotated_for_grok/manifest.json:

  1. Open metadata/rotated_for_grok/{slug}.png with vision.
  2. Transcribe every descriptor into markdown:
       | Level | Receptive | Productive |
     Blank Level on second row when PDF has a horizontal rule (B2/B1 multi-row).
     Join descriptors in a cell with <br>.
  3. Write metadata/rotated_from_grok/{slug}.md (table only).
  4. After a span is complete (or for a production run with geometry fallback):
       python finalize_after_grok.py

Chat/web Grok is NOT a pipeline step.
""".strip()


def rotated_table_slug(page_num: int, span_group_id: str) -> str:
    """Canonical basename for PNG / JSON / handoff / agent markdown."""
    safe_gid = re.sub(r"[^a-zA-Z0-9_+-]", "_", span_group_id).strip("_") or "unknown"
    return f"page_{page_num:03d}_{safe_gid}"


def _paths_for_slug(slug: str) -> dict[str, Path]:
    return {
        "png": ROTATED_FOR_GROK_DIR / f"{slug}.png",
        "json": ROTATED_FOR_GROK_DIR / f"{slug}.json",
        "handoff": ROTATED_FOR_GROK_DIR / f"{slug}.handoff.txt",
        "md": ROTATED_FROM_GROK_DIR / f"{slug}.md",
    }


def _legacy_garbled_gid_candidates(span_group_id: str) -> list[str]:
    """Known pre-fix slug forms so vision .md is found after id re-slug (RIE-005).

    Never renames or deletes rotated_from_grok files — only alias lookup.
    """
    clean = (span_group_id or "").strip()
    # Bidirectional known maps (clean ↔ historical garbled inventory slugs)
    pairs = (
        ("scale_relaying_specific_information", "scale_relaying_cfiiceps_information"),
        ("scale_collaborating_in_a_group", "scale_collaborating_ni_a_group"),
        (
            "scale_explaining_data_in_graphs_and_diagrams",
            "scale_cte_smargaid_shparg_ni_atad_explaining",
        ),
        (
            "scale_explaining_data_in_graphs_diagrams_etc",
            "scale_cte_smargaid_shparg_ni_atad_explaining",
        ),
        (
            "scale_sustained_monologue_putting_a_case_e_g_in_a_debate",
            "scale_sustained_monologue_gnittup_a_case_e_g_in_a_debate",
        ),
        ("scale_public_announcements", "scale_cilbup_announcements"),
        (
            "scale_what_is_addressed_in_this_publication",
            "scale_what_is_addressed_in_this_noitacilbup",
        ),
        ("scale_translating_a_written_text", "scale_translating_a_nettirw_text"),
        (
            "scale_strategies_to_explain_a_new_concept",
            "scale_strategies_ot_nialpxe_a_wen_concept",
        ),
        (
            "scale_sociolinguistic_appropriateness_and_cultural_repertoire",
            "scale_sociolinguistic_ssenetairporppa_and_larutluc_repertoire",
        ),
        ("scale_sign_text_structure", "scale_sign_text_erutcurts"),
        ("scale_mediating_concepts", "scale_mediating_stpecnoc"),
    )
    out: list[str] = []
    for a, b in pairs:
        if clean == a:
            out.append(b)
        elif clean == b:
            out.append(a)
    # Token-level reverse of known garbled fragments inside the id
    from pipeline.title_fix import _GARBLED_TOKEN_FIX

    rev = {v: k for k, v in _GARBLED_TOKEN_FIX.items()}
    # Prefer longer keys first (publication before in)
    for good, bad in sorted(rev.items(), key=lambda kv: -len(kv[0])):
        if good in clean and bad not in clean:
            candidate = clean.replace(good, bad)
            if candidate != clean and candidate not in out:
                out.append(candidate)
    return out


def resolve_grok_md_path(page_num: int, span_group_id: str) -> Path | None:
    """Find vision markdown for this page/id, including legacy garbled slugs.

    Fail-closed for unrelated page files. Appendix 5 (pp. 191–241) is a special
    case: agent vision is stored under ``appendix_5_domain_examples`` while
    inventory may label the page with a domain-scale id (Online interaction, …).
    """
    primary = ROTATED_FROM_GROK_DIR / f"{rotated_table_slug(page_num, span_group_id)}.md"
    if primary.exists() and primary.stat().st_size > 20:
        return primary
    for leg in _legacy_garbled_gid_candidates(span_group_id):
        cand = ROTATED_FROM_GROK_DIR / f"{rotated_table_slug(page_num, leg)}.md"
        if cand.exists() and cand.stat().st_size > 20:
            return cand
    # Appendix 5 domain-example pages: vision markdown is always under the series slug
    if 191 <= page_num <= 241:
        appx = ROTATED_FROM_GROK_DIR / f"{rotated_table_slug(page_num, 'appendix_5_domain_examples')}.md"
        if appx.exists() and appx.stat().st_size > 20:
            return appx
    # Constrained last resort: only if the candidate stem shares a meaningful
    # token with the group_id (not merely "only file on this page number").
    tokens = [
        t
        for t in re.split(r"[_\W]+", (span_group_id or "").lower())
        if len(t) >= 5 and t not in {"scale", "table", "page"}
    ]
    if not tokens:
        return None
    matches = [
        p
        for p in ROTATED_FROM_GROK_DIR.glob(f"page_{page_num:03d}_*.md")
        if p.stat().st_size > 20
        and any(t in p.stem.lower() for t in tokens)
    ]
    if len(matches) == 1:
        return matches[0]
    return None


def resolve_rotated_asset_slug(page_num: int, span_group_id: str) -> str:
    """Slug whose PNG/JSON/MD exist (prefer clean id, fall back to legacy)."""
    clean_slug = rotated_table_slug(page_num, span_group_id)
    md = resolve_grok_md_path(page_num, span_group_id)
    if md is not None:
        return md.stem
    # Prefer existing PNG under clean or legacy slug
    for gid in [span_group_id, *_legacy_garbled_gid_candidates(span_group_id)]:
        slug = rotated_table_slug(page_num, gid)
        if (ROTATED_FOR_GROK_DIR / f"{slug}.png").exists():
            return slug
    return clean_slug


def _get_table_bbox(pdf_path: str | Path, page_idx: int) -> tuple[float, float, float, float] | None:
    with pdfplumber.open(pdf_path) as pdf:
        if page_idx < 0 or page_idx >= len(pdf.pages):
            return None
        tables = pdf.pages[page_idx].find_tables()
        if not tables:
            return None
        return tables[0].bbox


def _span_role(page_num: int, span_pages: list[int]) -> str:
    if not span_pages:
        return "single"
    if page_num == span_pages[0]:
        return "start"
    if page_num == span_pages[-1]:
        return "end"
    return "middle"


def _handoff_text(meta: dict[str, Any]) -> str:
    pages = meta.get("span_pages") or [meta["page"]]
    page_range = f"{pages[0]}-{pages[-1]}" if len(pages) > 1 else str(pages[0])
    return (
        f"Page: {meta['page']}\n"
        f"Span: {meta['span_group_id']} (pages {page_range})\n"
        f"Title: {meta.get('display_title', meta['span_group_id'])}\n"
        f"Role: {meta.get('span_role', 'single')}\n"
        f"Rotation: {meta.get('rotation', 90)}\n"
        f"Slug: {meta['slug']}\n"
        f"PNG: metadata/rotated_for_grok/{meta['slug']}.png\n"
        f"Write markdown: metadata/rotated_from_grok/{meta['slug']}.md\n"
        f"\n"
        f"AUTHORITY: coding agent vision only (no chat/web Grok step).\n"
        f"Schema: | Level | Receptive | Productive |  multi-row: blank Level.\n"
        f"Then: python finalize_after_grok.py\n"
    )


def prepare_rotated_table_for_grok(
    page_num: int,
    span_group_id: str,
    display_title: str,
    *,
    span_pages: list[int] | None = None,
    rotation: int = 90,
    pdf_path: str | Path = PDF_PATH,
    force: bool = False,
) -> dict[str, Any]:
    """Crop rotated table region; write PNG + JSON + handoff txt. Idempotent unless force=True.

    Prefer existing legacy (garbled-slug) assets so re-slug never orphans vision .md.
    """
    ROTATED_FOR_GROK_DIR.mkdir(parents=True, exist_ok=True)
    ROTATED_FROM_GROK_DIR.mkdir(parents=True, exist_ok=True)
    # Use legacy slug when assets already exist under the pre-fix id
    slug = resolve_rotated_asset_slug(page_num, span_group_id)
    paths = _paths_for_slug(slug)

    span_pages = span_pages or [page_num]
    meta: dict[str, Any] = {
        "slug": slug,
        "page": page_num,
        "span_group_id": span_group_id,
        "display_title": display_title,
        "span_pages": span_pages,
        "span_role": _span_role(page_num, span_pages),
        "rotation": rotation,
        "image_path": str(paths["png"]),
        "metadata_path": str(paths["json"]),
        "expected_md_path": str(paths["md"]),
        "handoff_path": str(paths["handoff"]),
        "status": "pending_agent_vision",
        "extraction_authority": "agent_vision",
    }

    if paths["json"].exists() and paths["png"].exists() and not force:
        existing = json.loads(paths["json"].read_text(encoding="utf-8"))
        existing["status"] = _status_for_slug(slug)
        existing.setdefault("extraction_authority", "agent_vision")
        paths["handoff"].write_text(_handoff_text({**existing, **meta, "slug": slug}), encoding="utf-8")
        _update_manifest_entry({**existing, "slug": slug})
        return existing

    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]
    bbox = _get_table_bbox(pdf_path, page_num - 1)
    if not bbox:
        doc.close()
        raise ValueError(f"No table bbox on page {page_num}")

    meta["table_bbox"] = list(bbox)
    x0, top, x1, bottom = bbox
    clip = fitz.Rect(x0, top, x1, bottom)
    mat = fitz.Matrix(RENDER_SCALE, RENDER_SCALE)
    pix = page.get_pixmap(matrix=mat, clip=clip)
    pix.save(str(paths["png"]))
    doc.close()

    paths["json"].write_text(json.dumps(meta, indent=2), encoding="utf-8")
    paths["handoff"].write_text(_handoff_text(meta), encoding="utf-8")
    meta["status"] = _status_for_slug(slug)
    _update_manifest_entry(meta)
    return meta


def prepare_span_for_grok(
    page_nums: list[int],
    span_group_id: str,
    display_title: str,
    *,
    rotation: int = 90,
    pdf_path: str | Path = PDF_PATH,
    force: bool = False,
) -> list[dict[str, Any]]:
    """Prepare one PNG per page in a multi-page rotated span."""
    return [
        prepare_rotated_table_for_grok(
            page_num,
            span_group_id,
            display_title,
            span_pages=page_nums,
            rotation=rotation,
            pdf_path=pdf_path,
            force=force,
        )
        for page_num in page_nums
    ]


def _status_for_slug(slug: str) -> str:
    md_path = ROTATED_FROM_GROK_DIR / f"{slug}.md"
    if md_path.exists() and md_path.stat().st_size > 20:
        return "agent_md_ready"
    return "pending_agent_vision"


def _update_manifest_entry(meta: dict[str, Any]) -> None:
    ROTATED_FOR_GROK_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = ROTATED_FOR_GROK_DIR / MANIFEST_NAME
    manifest: dict[str, Any] = {"tables": []}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    tables: list[dict] = manifest.setdefault("tables", [])
    meta = {**meta, "status": _status_for_slug(meta["slug"])}
    replaced = False
    for i, row in enumerate(tables):
        if row.get("slug") == meta["slug"]:
            tables[i] = meta
            replaced = True
            break
    if not replaced:
        tables.append(meta)
    tables.sort(key=lambda r: (r.get("page", 0), r.get("slug", "")))
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def refresh_manifest_statuses() -> dict[str, Any]:
    """Re-scan rotated_from_grok and update manifest statuses."""
    manifest_path = ROTATED_FOR_GROK_DIR / MANIFEST_NAME
    if not manifest_path.exists():
        return {"tables": [], "pending": 0, "received": 0}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pending = received = 0
    for row in manifest.get("tables", []):
        slug = row.get("slug", "")
        row["status"] = _status_for_slug(slug)
        if row["status"] == "agent_md_ready":
            received += 1
        else:
            pending += 1
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest["pending"] = pending
    manifest["received"] = received
    return manifest


def get_pending_rotated_tables() -> list[dict[str, Any]]:
    refresh_manifest_statuses()
    manifest_path = ROTATED_FOR_GROK_DIR / MANIFEST_NAME
    if not manifest_path.exists():
        return []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return [t for t in manifest.get("tables", []) if t.get("status") == "pending_agent_vision"]


def grok_md_path(page_num: int, span_group_id: str) -> Path:
    """Primary (clean-id) path; may not exist if only legacy garbled slug is on disk."""
    resolved = resolve_grok_md_path(page_num, span_group_id)
    if resolved is not None:
        return resolved
    return ROTATED_FROM_GROK_DIR / f"{rotated_table_slug(page_num, span_group_id)}.md"


def has_grok_markdown(page_num: int, span_group_id: str) -> bool:
    path = resolve_grok_md_path(page_num, span_group_id)
    return path is not None


def span_grok_complete(page_nums: list[int], span_group_id: str) -> bool:
    return all(has_grok_markdown(p, span_group_id) for p in page_nums)


def _strip_table_header(md: str) -> str:
    """Remove markdown table header + separator from continuation pages."""
    lines = md.strip().splitlines()
    out: list[str] = []
    past_sep = False
    for line in lines:
        if not past_sep:
            if re.match(r"^\|\s*---", line):
                past_sep = True
            continue
        out.append(line)
    return "\n".join(out).strip()


def _merge_grok_page_markdowns(md_paths: list[Path]) -> str:
    if not md_paths:
        return ""
    parts: list[str] = []
    for i, path in enumerate(md_paths):
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        if i == 0:
            parts.append(text)
        else:
            body = _strip_table_header(text)
            if body:
                parts.append(body)
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return parts[0] + "\n" + "\n".join(parts[1:])


def assemble_grok_rotated_span(
    span_group_id: str,
    page_nums: list[int],
) -> str | None:
    """Merge per-page agent vision markdown into one table body."""
    ROTATED_FROM_GROK_DIR.mkdir(parents=True, exist_ok=True)
    if not span_grok_complete(page_nums, span_group_id):
        return None
    paths: list[Path] = []
    for p in sorted(page_nums):
        md = resolve_grok_md_path(p, span_group_id)
        if md is None:
            return None
        paths.append(md)
    merged = _merge_grok_page_markdowns(paths)
    return merged.strip() if merged.strip() else None


def pending_placeholder(span_group_id: str, page_nums: list[int]) -> str:
    slugs = [rotated_table_slug(p, span_group_id) for p in sorted(page_nums)]
    lines = [
        f"<!-- GROK_VISION_PENDING: {span_group_id} pages={page_nums[0]}-{page_nums[-1]} -->",
        "<!-- Rotated table: agent vision .md missing; extract may use geometry fallback. -->",
        "<!-- Agent: re-read PNGs in metadata/rotated_for_grok/ and write rotated_from_grok/ -->",
    ]
    for slug in slugs:
        lines.append(f"<!--   - {slug}.png → metadata/rotated_from_grok/{slug}.md -->")
    lines.append("<!-- Then: python finalize_after_grok.py -->")
    return "\n".join(lines)


def extract_rotated_span_via_grok(
    page_nums: list[int],
    span_group_id: str,
    display_title: str,
    *,
    rotation: int = 90,
) -> str:
    """Prepare handoff assets, then return assembled markdown or pending placeholder."""
    prepare_span_for_grok(page_nums, span_group_id, display_title, rotation=rotation)
    body = assemble_grok_rotated_span(span_group_id, page_nums)
    if body:
        refresh_manifest_statuses()
        return body
    return pending_placeholder(span_group_id, page_nums)


def extract_single_rotated_via_grok(
    page_num: int,
    span_group_id: str,
    display_title: str,
    *,
    rotation: int = 90,
) -> str:
    prepare_rotated_table_for_grok(
        page_num, span_group_id, display_title, span_pages=[page_num], rotation=rotation
    )
    body = assemble_grok_rotated_span(span_group_id, [page_num])
    if body:
        refresh_manifest_statuses()
        return body
    return pending_placeholder(span_group_id, [page_num])


def _collect_rotated_spans_from_inventory(inv: dict) -> list[dict[str, Any]]:
    """Gather span definitions from start-page artifacts (continuation pages skip body)."""
    spans: list[dict[str, Any]] = []
    seen_gids: set[str] = set()
    for page_info in inv.get("pages", []):
        orient = page_info.get("table_orientation") or "normal"
        if not str(orient).startswith("rotated"):
            continue
        span_info = page_info.get("spanning_info") or {}
        for el in page_info.get("reading_order") or []:
            if el.get("extractor") != "rotated_table":
                continue
            span = el.get("span") or {}
            gid = span.get("group_id") or span_info.get("group_id") or el.get("artifact_id")
            if not gid or gid in seen_gids:
                break
            seen_gids.add(gid)
            page_num = page_info["page_number"]
            span_pages = span.get("pages") or _span_pages_from_info(span_info, page_num)
            spans.append(
                {
                    "group_id": gid,
                    "display_title": el.get("display_title") or gid,
                    "span_pages": span_pages,
                    "rotation": el.get("rotation", 90),
                }
            )
            break
    return spans


def prepare_all_rotated_from_inventories(
    inventories_dir: Path | None = None,
    *,
    force: bool = False,
) -> list[dict[str, Any]]:
    """Scan inventories; prepare PNG handoff for every page in each rotated span."""
    inv_dir = inventories_dir or INVENTORIES_DIR
    prepared: list[dict[str, Any]] = []
    seen_slugs: set[str] = set()
    errors: list[str] = []

    for inv_path in sorted(inv_dir.glob("*_inventory.json")):
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
        for span_def in _collect_rotated_spans_from_inventory(inv):
            gid = span_def["group_id"]
            title = span_def["display_title"]
            span_pages = span_def["span_pages"]
            rotation = span_def["rotation"]
            for page_num in span_pages:
                slug = rotated_table_slug(page_num, gid)
                if slug in seen_slugs:
                    continue
                seen_slugs.add(slug)
                try:
                    meta = prepare_rotated_table_for_grok(
                        page_num,
                        gid,
                        title,
                        span_pages=span_pages,
                        rotation=rotation,
                        force=force,
                    )
                    prepared.append(meta)
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{slug}: {exc}")

    write_handoff_readme(errors=errors)
    refresh_manifest_statuses()
    return prepared


def write_handoff_readme(*, errors: list[str] | None = None) -> Path:
    """Write metadata/rotated_for_grok/README.txt with agent vision workflow."""
    ROTATED_FOR_GROK_DIR.mkdir(parents=True, exist_ok=True)
    pending = get_pending_rotated_tables()
    received = refresh_manifest_statuses().get("received", 0)
    lines = [
        "Rotated table agent vision handoff",
        "==================================",
        "",
        AGENT_VISION_INSTRUCTIONS,
        "",
        "Commands",
        "--------",
        "  python prepare_rotated_for_grok.py",
        "  python finalize_after_grok.py",
        "",
        f"Pending agent .md: {len(pending)}",
        f"Ready: {received}",
        f"Manifest: {ROTATED_FOR_GROK_DIR / MANIFEST_NAME}",
        f"Output dir: {ROTATED_FROM_GROK_DIR}",
    ]
    if errors:
        lines.extend(["", "Prepare errors:", *[f"  - {e}" for e in errors]])
    path = ROTATED_FOR_GROK_DIR / "README.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    brief = ROTATED_FOR_GROK_DIR.parent / "ROTATED_TABLES_AGENT_VISION.md"
    brief.write_text(
        "# Rotated tables — agent vision (user out of the loop)\n\n"
        + AGENT_VISION_INSTRUCTIONS
        + "\n\n## Paths\n\n"
        "- PNG / JSON / handoff: `metadata/rotated_for_grok/`\n"
        "- Agent markdown: `metadata/rotated_from_grok/{slug}.md`\n"
        "- Module: `pipeline/extractors/rotated_grok_vision.py`\n"
        "- Footnotes: geometry `rotated_footnote_zone` (not vision)\n"
        "- Missing .md at extract time: geometry fallback + HTML comment\n"
        "\n## Not a pipeline step\n\n"
        "Chat/web Grok upload is **not** required and is not automated.\n",
        encoding="utf-8",
    )
    return path


def _span_pages_from_info(span_info: dict, page_num: int) -> list[int]:
    start = span_info.get("start_page")
    end = span_info.get("end_page")
    if start and end:
        return list(range(start, end + 1))
    return [page_num]


def chunk_has_pending_grok(chunk_id: str) -> bool:
    """True if this chunk has rotated tables still missing agent vision markdown."""
    inv_path = INVENTORIES_DIR / f"{chunk_id}_inventory.json"
    if not inv_path.exists():
        return False
    inv = json.loads(inv_path.read_text(encoding="utf-8"))
    emitted_spans: set[str] = set()
    for page_info in inv.get("pages", []):
        orient = page_info.get("table_orientation") or "normal"
        if not str(orient).startswith("rotated"):
            continue
        for el in page_info.get("reading_order") or []:
            if el.get("type") != "artifact" or el.get("extractor") != "rotated_table":
                continue
            span = el.get("span")
            if not span:
                gid = el.get("artifact_id") or "unknown"
                if not has_grok_markdown(page_info["page_number"], gid):
                    return True
                continue
            gid = span["group_id"]
            if gid in emitted_spans:
                continue
            emitted_spans.add(gid)
            if not span_grok_complete(span["pages"], gid):
                return True
    return False


def chunks_with_rotated_tables() -> list[str]:
    out: list[str] = []
    for inv_path in sorted(INVENTORIES_DIR.glob("*_inventory.json")):
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
        for page_info in inv.get("pages", []):
            if any(
                el.get("extractor") == "rotated_table"
                for el in (page_info.get("reading_order") or [])
            ):
                out.append(inv_path.stem.replace("_inventory", ""))
                break
    return out


def all_grok_ready() -> bool:
    refresh_manifest_statuses()
    return len(get_pending_rotated_tables()) == 0
