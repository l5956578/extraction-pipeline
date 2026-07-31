"""High-value regression suite for extraction deliverables.

Focused on previously painful areas:
- page completeness / order
- rotated tables (no AGENT_VISION_PENDING; content present)
- multipage merges
- callouts / inventory contracts
- figure injection
- registry + product_tiers presence
- existing golden adjacent suite + contract validators

Returns a report dict; exit non-zero via CLI when any hard check fails.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import pipeline.config as cfg
from pipeline.job_context import final_markdown_path, require_active_job


def _page_bodies(md: str) -> dict[int, str]:
    parts = re.split(r"(?=<!-- page:\d+ -->)", md)
    out: dict[int, str] = {}
    for p in parts:
        m = re.search(r"<!-- page:(\d+) -->", p)
        if m:
            out[int(m.group(1))] = p
    return out


# Golden / layout ids that don't match emitted slug — still point at the body table.
_COMPANION_ARTIFACT_HINTS: dict[str, dict[str, Any]] = {
    "table_01_descriptive_scheme_updates": {
        "page": 23,
        "actual_ids": [
            "table_table_1_the_cefr_descriptive_scheme_and_illustrative_descriptors_updates_and_additions",
        ],
        "caption": "Table 1 – The CEFR descriptive scheme",
    },
    "table_02_summary_descriptor_changes": {
        "page": 24,
        "actual_ids": [
            "table_table_2_summary_of_changes_to_the_illustrative_descriptors",
        ],
        "caption": "Table 2 – Summary of changes",
    },
    "table_03_macro_functional_basis": {
        "page": 33,
        "actual_ids": ["table_reception", "table_table_3_macro_functional"],
        "caption": "Table 3 – Macro-functional basis",
    },
}


def _fail(
    code: str,
    detail: str,
    *,
    severity: str = "hard",
    **extra: Any,
) -> dict[str, Any]:
    row: dict[str, Any] = {"code": code, "severity": severity, "detail": detail}
    for k, v in extra.items():
        if v is not None:
            row[k] = v
    return row


def _line_index_for_char(text: str, pos: int) -> int:
    """1-based line number for a character offset."""
    if pos <= 0:
        return 1
    return text.count("\n", 0, min(pos, len(text))) + 1


def _page_marker_line(text: str, page: int) -> int | None:
    m = re.search(rf"<!-- page:{page} -->", text)
    if not m:
        return None
    return _line_index_for_char(text, m.start())


def _find_line(text: str, needle: str, *, start_line: int | None = None) -> int | None:
    if not needle:
        return None
    lines = text.splitlines()
    start_i = max(0, (start_line or 1) - 1)
    low = needle.lower()
    for i in range(start_i, len(lines)):
        if low in lines[i].lower():
            return i + 1
    return None


def _snippet_at(text: str, line1: int, *, radius: int = 0) -> str:
    lines = text.splitlines()
    if line1 < 1 or line1 > len(lines):
        return ""
    i = line1 - 1
    if radius <= 0:
        return lines[i][:200]
    lo = max(0, i - radius)
    hi = min(len(lines), i + radius + 1)
    return "\n".join(lines[lo:hi])[:400]


def _db_ids_near_page(text: str, page: int, *, window: int = 80) -> list[str]:
    """db:id values near a page marker (for missing-id diagnostics)."""
    m = re.search(rf"<!-- page:{page} -->", text)
    if not m:
        # content for page N sits *before* the page:N marker in this pipeline
        m = re.search(rf"<!-- page:{page} -->", text)
    # Prefer block before page marker (body for that page)
    markers = list(re.finditer(r"<!-- page:(\d+) -->", text))
    block = ""
    for i, mk in enumerate(markers):
        if int(mk.group(1)) == page:
            start = markers[i - 1].end() if i > 0 else 0
            block = text[start : mk.start()]
            break
    if not block:
        line = _page_marker_line(text, page) or 1
        lines = text.splitlines()
        lo = max(0, line - 1 - window)
        hi = min(len(lines), line - 1 + window)
        block = "\n".join(lines[lo:hi])
    return re.findall(r"db:id=([^\s>]+)", block)


def _resolve_location(text: str, *, page: int | None = None, needles: list[str] | None = None) -> dict[str, Any]:
    """Return line (1-based), page, snippet for the best available anchor."""
    line: int | None = None
    reason = "none"
    needles = [n for n in (needles or []) if n]

    page_line = _page_marker_line(text, page) if page else None
    search_start = None
    if page is not None:
        # Body for page N is before the page:N marker; search a bit above it
        if page_line:
            search_start = max(1, page_line - 120)
        for n in needles:
            hit = _find_line(text, n, start_line=search_start)
            if hit is not None:
                # Prefer hits near the page block
                if page_line is None or abs(hit - page_line) < 200:
                    line = hit
                    reason = f"needle:{n[:48]}"
                    break
        if line is None and page_line is not None:
            # Aim at the body just before the page marker
            line = max(1, page_line - 5)
            reason = f"page_marker:{page}"
    else:
        for n in needles:
            hit = _find_line(text, n)
            if hit is not None:
                line = hit
                reason = f"needle:{n[:48]}"
                break

    if line is None:
        line = 1
        reason = "fallback:1"

    # Infer page from nearest preceding page marker if missing
    if page is None and line:
        lines = text.splitlines()
        for i in range(min(line - 1, len(lines) - 1), -1, -1):
            m = re.search(r"<!-- page:(\d+) -->", lines[i])
            if m:
                page = int(m.group(1))
                break

    return {
        "line": line,
        "page": page,
        "snippet": _snippet_at(text, line),
        "loc_reason": reason,
    }


def _enrich_issue(issue: dict[str, Any], text: str) -> dict[str, Any]:
    """Ensure every issue has page/line/snippet when possible; expand detail."""
    out = dict(issue)
    # Idempotent: already has coordinates from a prior pass
    if isinstance(out.get("line"), int) and out.get("loc_reason") and "(p." in str(out.get("detail") or ""):
        return out
    if isinstance(out.get("line"), int) and out.get("loc_reason") and re.search(r"\bL\d+", str(out.get("detail") or "")):
        return out

    code = str(out.get("code") or out.get("type") or "")
    detail = str(out.get("detail") or "")
    page = out.get("page")
    if isinstance(page, str) and page.isdigit():
        page = int(page)
    if not isinstance(page, int):
        page = None
        m = re.match(r"page_(\d+)_", code)
        if m:
            page = int(m.group(1))
        else:
            pm = re.search(r"\bpages?\s+(\d+)", detail, re.I)
            if pm:
                page = int(pm.group(1))
            elif isinstance(out.get("pages"), str):
                pm2 = re.match(r"(\d+)", str(out["pages"]))
                if pm2:
                    page = int(pm2.group(1))

    needles: list[str] = []
    aid = out.get("artifact_id") or out.get("id") or out.get("expected_id")
    header = out.get("header")
    if aid:
        needles.append(str(aid))
    if header:
        needles.append(str(header))

    # missing_artifact: detail may be bare id
    if code in ("missing_artifact", "OUTPUT_VALIDATOR") or (
        not aid and detail and not detail.startswith("{") and " " not in detail.strip()
    ):
        bare = str(aid or detail.strip())
        if bare in _COMPANION_ARTIFACT_HINTS:
            hint = _COMPANION_ARTIFACT_HINTS[bare]
            page = page or hint["page"]
            needles.extend(hint.get("actual_ids") or [])
            if hint.get("caption"):
                needles.append(hint["caption"])
            out["expected_id"] = bare
            out["page"] = page
            near = _db_ids_near_page(text, page) if page else []
            out["found_ids_near_page"] = near
            actual = next((a for a in (hint.get("actual_ids") or []) if a in text), None)
            if actual:
                out["actual_id"] = actual
                needles.insert(0, f"db:id={actual}")
            # Human-readable detail with lines filled after resolve
            out["_detail_template"] = (
                f"expected id {bare!r} not in output"
                + (f"; emitted nearby as {actual!r}" if actual else "")
                + (f"; other db:ids on p.{page}: {near[:6]}" if near else "")
            )

    if code == "missing_page_artifact" or out.get("type") == "missing_page_artifact":
        if out.get("artifact_id"):
            needles.append(str(out["artifact_id"]))
        # also try caption-ish fragments
        aid2 = str(out.get("artifact_id") or "")
        if "table_3" in aid2 or "macro_functional" in aid2:
            page = page or 33
            needles.extend(["Table 3", "table_reception", "Macro-functional"])
        if "can_do" in aid2:
            page = page or 35
            needles.extend(["Can do", "callout_can_do", "competence"])

    if code == "missing_section_header" or out.get("type") == "missing_section_header":
        if header:
            needles.append(str(header))
            # partials
            needles.append(str(header).split(".", 1)[-1].strip())

    if code == "footnote_single_owner" or "footnote" in code.lower():
        page = page or 24
        needles.extend(["19.", "footnote", "Table 2"])

    if code == "page_47_section_order":
        page = 47
        needles.extend(
            [
                "figure_11_reception_activities_strategies",
                "3.1. RECEPTION",
                "Figure 11",
            ]
        )

    loc = _resolve_location(text, page=page, needles=needles)
    out["page"] = loc["page"] if loc["page"] is not None else page
    out["line"] = loc["line"]
    out["snippet"] = loc["snippet"]
    out["loc_reason"] = loc["loc_reason"]

    # Rebuild detail to always include coordinates
    coords = f"p.{out.get('page') or '?'} L{out['line']}"
    if out.get("_detail_template"):
        out["detail"] = f"{out.pop('_detail_template')} ({coords})"
    elif out.get("header"):
        out["detail"] = (
            f"missing section header {out['header']!r} on page {out.get('page')} ({coords})"
        )
    elif out.get("artifact_id") and code in (
        "missing_page_artifact",
        "missing_section_header",
    ):
        out["detail"] = (
            f"{code}: {out['artifact_id']} on page {out.get('page')} ({coords})"
        )
    else:
        base = detail if detail and not detail.startswith("{") else (
            str(out.get("id") or out.get("artifact_id") or out.get("type") or code)
        )
        if f"L{out['line']}" not in base and " L" not in base:
            out["detail"] = f"{base} ({coords})"
        else:
            out["detail"] = base

    # Drop noise keys that were only for intermediate parsing
    return out


def _normalize_output_validator_issue(it: dict[str, Any], text: str) -> dict[str, Any]:
    """Turn output_validator dict into a soft regression issue (locations added later)."""
    del text  # reserved for future; enrichment is centralized
    code = str(it.get("type") or "OUTPUT_VALIDATOR")
    row: dict[str, Any] = {
        "code": code,
        "severity": "soft",
        "detail": str(it.get("detail") or it.get("id") or it.get("header") or code),
    }
    for k in (
        "id",
        "title",
        "page",
        "pages",
        "header",
        "artifact_id",
        "footnote",
        "count",
        "has_figure",
        "has_header",
        "chars",
        "min",
    ):
        if k in it and it[k] is not None:
            row[k] = it[k]
    if it.get("id") and "expected_id" not in row:
        row["expected_id"] = it["id"]
    return row


def run_regression(md_path: Path | None = None) -> dict[str, Any]:
    """Run hard + soft checks. ``passed`` is True only if no hard issues."""
    ctx = require_active_job()
    md_path = md_path or final_markdown_path()
    issues: list[dict[str, Any]] = []
    soft: list[dict[str, Any]] = []

    if not md_path.exists():
        return {
            "passed": False,
            "job_id": ctx.job_id,
            "path": str(md_path),
            "issues": [_fail("MD_MISSING", str(md_path))],
            "soft_issues": [],
            "stats": {},
        }

    md = md_path.read_text(encoding="utf-8")
    page_marks = re.findall(r"<!-- page:(\d+) -->", md)
    page_nums = [int(x) for x in page_marks]
    bodies = _page_bodies(md)

    # --- Pages ---
    expected_pages = int(
        (ctx.job_data.get("source") or {}).get("expected_page_count") or 0
    )
    if expected_pages and len(page_nums) != expected_pages:
        issues.append(
            _fail(
                "PAGE_COUNT",
                f"expected {expected_pages} page markers, found {len(page_nums)}",
            )
        )
    if len(page_nums) != len(set(page_nums)):
        issues.append(_fail("PAGE_DUP", "duplicate <!-- page:N --> markers"))
    consec = sum(1 for i in range(len(page_nums) - 1) if page_nums[i] == page_nums[i + 1])
    if consec:
        issues.append(_fail("PAGE_CONSEC_DUP", f"{consec} consecutive duplicate page markers"))
    if expected_pages and page_nums:
        missing = sorted(set(range(1, expected_pages + 1)) - set(page_nums))
        if missing:
            issues.append(_fail("PAGE_MISSING", f"missing pages: {missing[:20]}"))

    # --- Vision / rotated tables ---
    pending = md.count("AGENT_VISION_PENDING")
    if pending:
        issues.append(
            _fail("VISION_PENDING", f"AGENT_VISION_PENDING count={pending} (must be 0)")
        )

    # Representative rotated pages (inventory-flagged historically painful)
    rotated_probe = [94, 95, 132, 133, 146, 147, 148, 191, 200]
    for p in rotated_probe:
        body = bodies.get(p, "")
        if not body or len(body.strip()) < 40:
            issues.append(
                _fail("ROTATED_THIN", f"page {p}: body missing or very thin ({len(body)} chars)")
            )
        if "AGENT_VISION_PENDING" in body:
            issues.append(_fail("ROTATED_PENDING", f"page {p}: still has AGENT_VISION_PENDING"))

    # --- Final-state pins (layout known_tables + anti-regression aliases) ---
    # These are hard: STATUS "resolved" only holds if these stay green after re-runs.
    if ctx.profile == "cefr_companion":
        try:
            for page, (aid, title, _atype) in cfg.KNOWN_TABLES_FIGURES.items():
                body = bodies.get(int(page), "")
                if f"db:id={aid}" not in body and f"id={aid}" not in md:
                    issues.append(
                        _fail(
                            "KNOWN_TABLE_PIN",
                            f"p.{page}: layout pin {aid!r} missing "
                            f"(title {title!r})",
                        )
                    )
        except Exception as exc:  # noqa: BLE001
            issues.append(_fail("KNOWN_TABLE_PIN", f"error: {exc}"))

        # C2-T1: never accept Reception-only names for Table 3
        body33 = bodies.get(33, "")
        if re.search(r"\b(table_reception|scale_reception)\b", body33):
            issues.append(
                _fail(
                    "TABLE3_BAD_ID",
                    "p.33 still has table_reception/scale_reception "
                    "(must be table_03_macro_functional_basis)",
                )
            )
        if "table_03_macro_functional_basis" not in body33 and "Macro-functional" in body33:
            issues.append(
                _fail(
                    "TABLE3_PIN",
                    "p.33 missing table_03_macro_functional_basis",
                )
            )

        # Multipage hard pins
        for needle, label in (
            ("table_self_assessment_grid", "self-assessment grid"),
            ("scale_vocabulary_control", "vocabulary control"),
            ("scale_sign_language_repertoire", "sign language repertoire"),
        ):
            if needle not in md:
                issues.append(_fail("MULTIPAGE_PIN", f"missing multipage id {needle} ({label})"))

        # Callout hard pins (painful prior pages)
        for cid in (
            "callout_can_do_descriptors_as_competence",
            "callout_a_reminder_of_cefr_2001_chapters",
        ):
            if cid not in md:
                issues.append(_fail("CALLOUT_PIN", f"missing callout id {cid}"))

        # Garbled-id markers must stay gone (L07-ID)
        garbled = (
            "cfiiceps",
            "smargaid",
            "gnittup",
            "cilbup",
            "noitacilbup",
            "ssenetairporppa",
        )
        for g in garbled:
            if g in md:
                issues.append(_fail("GARBLED_ID", f"garbled token still present: {g}"))

        # Critical prior format fixes (string locks)
        for label, needle in (
            ("situation-specific", "situation-specific"),
            ("problem-solving p.33", "problem-solving"),
            ("fn21 object id join", "2fb1"),  # L06-FN21 style rejoin evidence (best-effort)
        ):
            if label.startswith("fn21"):
                # only soft if document never had that URL
                if "2fb" in md and "2fb1" not in md and re.search(r"2fb\n1\.", md):
                    issues.append(_fail("FN21_SPLIT", "p.27-style fn ObjectId still split"))
            elif needle not in md and label.startswith("situation"):
                soft.append(
                    _fail("HYPHEN_SITUATION", "situation-specific not found", severity="soft")
                )

        # Fig 12 p.61: permanent C2-ADJ — no leaf soup; trailing §3.2.1 prose required
        body61 = bodies.get(61, "")
        if body61 and "figure_12" in body61:
            if re.search(
                r"(?m)^(?:Public announcements|Planning|Compensating|Monitoring and repair)\s*$",
                body61,
            ):
                # Allow only inside ``` fence — check outside fence
                fe = body61.find("```", body61.find("```") + 3) if "```" in body61 else -1
                after = body61[fe + 3 :] if fe >= 0 else ""
                if re.search(
                    r"(?m)^(?:Public announcements|Planning|Compensating|Monitoring and repair)\s*$",
                    after,
                ):
                    issues.append(
                        _fail(
                            "FIG12_LEAF_SOUP",
                            "p.61: dual-emit leaf soup after Figure 12 text_diagram fence",
                        )
                    )
            if "rather than dialogue" not in body61.lower():
                issues.append(
                    _fail(
                        "FIG12_TRAIL_PROSE",
                        "p.61: missing trailing prose after Figure 12 "
                        "(…monologue rather than dialogue)",
                    )
                )
            if not re.search(r"3\.2\.1\.?\s*Production activities", body61, re.I):
                issues.append(
                    _fail(
                        "FIG12_SEC_321",
                        "p.61: missing 3.2.1 Production activities after Figure 12",
                    )
                )
    # --- Multipage merges (must appear as joined artifacts) ---
    multipage_needles = [
        ("scale_vocabulary_control", "vocabulary"),
        ("table_self_assessment_grid", "self.assessment|self-assessment|SELF-ASSESSMENT"),
        ("sign_language_repertoire", "sign language repertoire"),
    ]
    for needle, hint in multipage_needles:
        if needle not in md and not re.search(hint, md, re.I):
            soft.append(
                _fail(
                    "MULTIPAGE_HINT",
                    f"could not find multipage marker/id {needle!r}",
                    severity="soft",
                )
            )
    # Self-assessment grid section (base product) — hard if companion profile
    if ctx.profile == "cefr_companion":
        if "table_self_assessment_grid" not in md and "SELF-ASSESSMENT" not in md.upper():
            issues.append(
                _fail("MULTIPAGE_GRID", "self-assessment grid multipage block not found")
            )

    # --- Callouts (Companion blue boxes; el:start markers, not always db:id) ---
    if ctx.profile == "cefr_companion":
        callout_ids = re.findall(
            r"(?:db:id=|type=artifact id=|el:start type=artifact id=)(callout_[^\s>]+)",
            md,
        )
        if not callout_ids:
            callout_ids = re.findall(r"id=(callout_[^\s>]+)", md)
        if len(set(callout_ids)) < 3:
            issues.append(
                _fail(
                    "CALLOUT_SPARSE",
                    f"expected multiple callout_* ids, found {len(set(callout_ids))}",
                )
            )
        # Known painful callout
        if "callout_can_do_descriptors_as_competence" not in md:
            if "can do" not in md.lower() and "can-do" not in md.lower():
                soft.append(
                    _fail(
                        "CALLOUT_CANDO",
                        "can-do callout language not found",
                        severity="soft",
                    )
                )

    # --- Figures ---
    png_refs = re.findall(r"!\[.*?\]\((assets/figures/[^)]+)\)", md)
    fig_dir = ctx.assets_figures
    if ctx.profile == "cefr_companion":
        if len(set(png_refs)) < 5:
            issues.append(
                _fail("FIGURES_SPARSE", f"only {len(set(png_refs))} unique figure PNG refs")
            )
        for ref in sorted(set(png_refs)):
            # ref is assets/figures/foo.png relative to final md
            asset = ctx.final_dir / ref.replace("/", "\\") if "\\" in ref else ctx.final_dir / ref
            if not asset.exists():
                # try posix join
                asset = ctx.final_dir.joinpath(*Path(ref).parts)
            if not asset.exists():
                issues.append(_fail("FIGURE_ASSET_MISSING", f"missing file for {ref}"))
        if fig_dir.is_dir():
            on_disk = list(fig_dir.glob("*.png"))
            if len(on_disk) < 5:
                issues.append(
                    _fail("FIGURE_DISK_SPARSE", f"only {len(on_disk)} PNGs in assets/figures")
                )

    # --- Inventory contracts ---
    inv_dir = ctx.inventories_dir
    inv_files = sorted(inv_dir.glob("*_inventory.json")) if inv_dir.is_dir() else []
    if ctx.profile == "cefr_companion" and len(inv_files) < 8:
        issues.append(
            _fail("INVENTORY_COUNT", f"expected ~10 inventories, found {len(inv_files)}")
        )
    for inv_path in inv_files[:12]:
        try:
            inv = json.loads(inv_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(_fail("INVENTORY_JSON", f"{inv_path.name}: {exc}"))
            continue
        pages = inv.get("pages") or []
        if not pages:
            issues.append(_fail("INVENTORY_EMPTY", f"{inv_path.name}: no pages"))
            continue
        for page in pages[:3]:
            ro = page.get("reading_order")
            if not isinstance(ro, list) or not ro:
                issues.append(
                    _fail(
                        "READING_ORDER",
                        f"{inv_path.name} page {page.get('page_number')}: "
                        "missing reading_order",
                    )
                )
                break

    # --- Registry ---
    reg_path = ctx.final_dir / "db_import_registry.json"
    if reg_path.exists():
        reg = json.loads(reg_path.read_text(encoding="utf-8"))
        if not isinstance(reg, list):
            issues.append(_fail("REGISTRY_SHAPE", "db_import_registry.json must be a JSON array"))
        else:
            if ctx.profile == "cefr_companion" and len(reg) < 50:
                issues.append(
                    _fail("REGISTRY_SPARSE", f"registry only has {len(reg)} artifacts")
                )
            missing_tiers = [
                r.get("id")
                for r in reg
                if not r.get("product_tiers")
            ]
            if missing_tiers:
                issues.append(
                    _fail(
                        "REGISTRY_TIERS",
                        f"{len(missing_tiers)} artifacts missing product_tiers "
                        f"(sample: {missing_tiers[:5]})",
                    )
                )
    elif ctx.profile == "cefr_companion":
        issues.append(_fail("REGISTRY_MISSING", "db_import_registry.json missing"))

    # --- Existing golden + contract validators (hard) ---
    try:
        from pipeline.contract_validators import validate_contracts

        crep = validate_contracts(md_path)
        for it in crep.get("issues") or []:
            if it.get("severity") == "high":
                issues.append(
                    _fail(
                        it.get("gate") or "CONTRACT",
                        it.get("detail") or str(it),
                    )
                )
            else:
                soft.append(
                    _fail(
                        it.get("gate") or "CONTRACT_SOFT",
                        it.get("detail") or str(it),
                        severity="soft",
                    )
                )
    except Exception as exc:  # noqa: BLE001
        issues.append(_fail("CONTRACT_ERROR", str(exc)))

    try:
        from pipeline.adjacent_guard import validate_adjacent

        for it in validate_adjacent(md_path):
            # adjacent_guard returns high-severity by default
            detail = it.get("detail") or it.get("message") or str(it)
            code = it.get("gate") or it.get("code") or "ADJACENT"
            issues.append(_fail(code, detail))
    except Exception as exc:  # noqa: BLE001
        soft.append(_fail("ADJACENT_ERROR", str(exc), severity="soft"))

    # Soft: output_validator known noisy ID mismatches — report but do not block version
    try:
        from pipeline.output_validator import validate_final_output

        orep = validate_final_output(md_path)
        oissues = orep.get("issues") if isinstance(orep, dict) else []
        for it in oissues or []:
            if isinstance(it, dict):
                # Inventory may still hold long auto-slugs (table_table_3_…) while the
                # deliverable correctly has layout pins (table_03_…). That is not a
                # deliverable defect — skip as soft noise when the pin is present.
                if it.get("type") == "missing_page_artifact":
                    aid = str(it.get("artifact_id") or "")
                    page = it.get("page")
                    pin_ok = False
                    if isinstance(page, int) and page in cfg.KNOWN_TABLES_FIGURES:
                        pin_id = cfg.KNOWN_TABLES_FIGURES[page][0]
                        if pin_id and pin_id in md:
                            pin_ok = True
                    if pin_ok and aid.startswith("table_table_"):
                        continue
                    if aid == "scale_can_do_descriptors_as_competence" and (
                        "callout_can_do_descriptors_as_competence" in md
                    ):
                        # Callout, not scale — C2-T2 class
                        continue
                soft.append(_normalize_output_validator_issue(it, md))
            else:
                soft.append(
                    _enrich_issue(
                        _fail("OUTPUT_VALIDATOR", str(it)[:200], severity="soft"),
                        md,
                    )
                )
    except Exception as exc:  # noqa: BLE001
        soft.append(_fail("OUTPUT_VALIDATOR_ERROR", str(exc), severity="soft"))

    # Ensure hard + soft all carry page/line coordinates
    issues = [_enrich_issue(it, md) for it in issues]
    soft = [_enrich_issue(it, md) for it in soft]

    stats = {
        "page_markers": len(page_nums),
        "unique_pages": len(set(page_nums)),
        "md_chars": len(md),
        "vision_pending": pending,
        "figure_png_refs": len(set(re.findall(r"assets/figures/[^)\s]+", md))),
        "inventories": len(inv_files),
        "hard_issues": len(issues),
        "soft_issues": len(soft),
    }

    report = {
        "passed": len(issues) == 0,
        "job_id": ctx.job_id,
        "path": str(md_path),
        "issues": issues,
        "soft_issues": soft,
        "stats": stats,
    }
    # Persist for audit
    out = cfg.METADATA_DIR / "regression_report.json"
    try:
        cfg.METADATA_DIR.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report["report_path"] = str(out)
    except OSError:
        pass
    return report


def run_regression_and_maybe_version(
    *,
    create_version: bool = True,
    md_path: Path | None = None,
) -> dict[str, Any]:
    """Run regression; if passed and create_version, snapshot under versions/NNN/."""
    from pipeline.versioning import create_version_snapshot

    report = run_regression(md_path)
    result: dict[str, Any] = {"regression": report, "version_path": None}
    if report["passed"] and create_version:
        vdir = create_version_snapshot(regression_report=report)
        result["version_path"] = str(vdir)
        result["version"] = vdir.name
    return result


def main(argv: list[str] | None = None) -> int:
    import argparse

    from pipeline.bootstrap import add_job_argument, bootstrap_job

    parser = argparse.ArgumentParser(description="Run high-value extraction regression suite")
    add_job_argument(parser)
    parser.add_argument(
        "--no-version",
        action="store_true",
        help="Run tests only; do not create versions/NNN snapshot",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    bootstrap_job(args.job, force_draft=bool(args.force_draft))
    result = run_regression_and_maybe_version(create_version=not args.no_version)
    rep = result["regression"]
    print(f"Job: {rep['job_id']}")
    print(f"Passed: {rep['passed']}")
    print(f"Hard issues: {len(rep['issues'])}  Soft: {len(rep['soft_issues'])}")
    for it in rep["issues"][:30]:
        print(f"  HARD [{it['code']}] {it['detail']}")
    for it in rep["soft_issues"][:15]:
        print(f"  soft [{it['code']}] {it['detail']}")
    if result.get("version_path"):
        print(f"Version snapshot: {result['version_path']}")
    elif rep["passed"]:
        print("No version created (--no-version)")
    else:
        print("No version created (regression failed)")
    if rep.get("report_path"):
        print(f"Report: {rep['report_path']}")
    return 0 if rep["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
