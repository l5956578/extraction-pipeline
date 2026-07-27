"""Fail-closed contract gates for Chapter 2 / document-wide regressions.

See docs/CONTRACTS.md §8. Exit non-zero when high-severity gates fail.
Do not mark STATUS C2-* resolved unless the covering gate is green.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pipeline.config as cfg
from pipeline.config import ROOT, final_markdown_path
from pipeline.extractors.figures import figures_for_page, load_figures_registry

def _page_body(md: str, page_num: int) -> str:
    m = re.search(rf"<!-- page:{page_num} -->", md)
    if not m:
        return ""
    prev = list(re.finditer(r"<!-- page:(\d+) -->", md[: m.start()]))
    start = prev[-1].end() if prev else 0
    return md[start : m.start()]

def _fail(gate: str, detail: str) -> dict:
    return {"gate": gate, "severity": "high", "detail": detail}

def validate_contracts(md_path: Path | None = None) -> dict:
    """Return {valid, issues:[{gate, severity, detail}, ...]}."""
    

    md_path = md_path or final_markdown_path()
    issues: list[dict] = []
    if not md_path.exists():
        return {"valid": False, "issues": [_fail("V-MD-MISSING", str(md_path))], "path": str(md_path)}

    md = md_path.read_text(encoding="utf-8")

    # --- V-URL-SPACE: spaces inside URL tokens (not "URL. Next sentence") ---
    for m in re.finditer(r"https?://\s+\S+", md):
        issues.append(_fail("V-URL-SPACE", f"space after scheme: {m.group(0)[:80]}"))
    # Internal path break: details. aspx (space after dot before extension)
    for m in re.finditer(
        r"https?://[^\s\)\]<>\"']*\.\s+(?:aspx|html?|php|pdf|json)\b",
        md,
        re.I,
    ):
        issues.append(_fail("V-URL-SPACE", f"URL path space after dot: {m.group(0)[:80]}"))
    # Space mid-hex id: /1680 667a
    for m in re.finditer(r"https?://[^\s\)\]<>\"']*\s+[0-9a-fA-F]{4,}\b", md):
        issues.append(_fail("V-URL-SPACE", f"space inside URL path: {m.group(0)[:80]}"))

    # --- V-EMPTY-TABLE ---
    if re.search(r"^\|?\s*\|\s*$\n\|?\s*---\s*\|?\s*$\n\|?\s*\|\s*$", md, re.M):
        issues.append(_fail("V-EMPTY-TABLE", "empty one-column markdown table present"))
    # Common junk: |  |\n| --- |\n|  |
    if re.search(r"\|\s*\|\n\|\s*---\s*\|\n\|\s*\|", md):
        issues.append(_fail("V-EMPTY-TABLE", "empty junk table | | pattern"))

    # --- V-TABLE-ID: Table 3 not scale_reception ---
    if re.search(r"scale_reception\b", md) and re.search(
        r"Table\s+3|Reception.*Production.*Interaction", md[: md.find("<!-- page:40 -->") if "<!-- page:40 -->" in md else 200000]
    ):
        # Hard fail if scale_reception still used near chapter 2 table region
        body33 = _page_body(md, 33)
        if "scale_reception" in body33:
            issues.append(_fail("V-TABLE-ID", "p.33 still has scale_reception (should be table_03)"))

    # --- V-FIG-MULTI ---
    for pn, required in (
        (36, ("figure_03", "figure_04", "figure_05")),
        (40, ("figure_08", "figure_09", "figure_10")),
    ):
        body = _page_body(md, pn)
        missing = [fid for fid in required if fid not in body]
        if missing:
            issues.append(
                _fail("V-FIG-MULTI", f"page {pn} missing figure ids: {', '.join(missing)}")
            )

    # --- V-FIG-PNG-LOC: PNG should be near db:id ---
    for m in re.finditer(r"!\[([^\]]*)\]\((assets/figures/(figure_[^)/]+)\.png)\)", md):
        fid = m.group(3)
        start = max(0, m.start() - 800)
        window = md[start : m.end() + 200]
        if f"db:id={fid}" not in window and f"db:id={fid}" not in md[max(0, m.start() - 2000) : m.start()]:
            # Allow if db:id within 15 lines above
            lines_before = md[max(0, m.start() - 2000) : m.start()].splitlines()[-15:]
            if not any(fid in ln and "db:id=" in ln for ln in lines_before):
                issues.append(
                    _fail("V-FIG-PNG-LOC", f"{fid}.png not near matching db:id (possible EOF orphan)")
                )

    # --- V-FIG-SOUP: soup after text_diagram on figure pages ---
    for fig in load_figures_registry():
        if fig.get("render_as") != "text_diagram":
            continue
        pn = fig["page"]
        body = _page_body(md, pn)
        if not body or fig["id"] not in body:
            # Missing diagram is also a problem for known Ch2 figures
            if pn in (32, 47) or fig["num"] in (1, 11, 12, 13, 14, 15, 16, 17):
                issues.append(
                    _fail("V-FIG-SOUP", f"page {pn}: missing text_diagram id {fig['id']}")
                )
            continue
        # After closing ``` of the diagram, no multi-token competence soup
        fence_end = None
        in_fence = False
        for i, line in enumerate(body.splitlines()):
            if line.strip().startswith("```"):
                if in_fence:
                    fence_end = i
                    in_fence = False
                else:
                    in_fence = True
        if fence_end is not None:
            after = "\n".join(body.splitlines()[fence_end + 1 :])
            # Bold soup of competence labels
            if re.search(
                r"\*\*[^*]*(?:Overall language|Communicative language|General competences|"
                r"Savoir|Reception\s+Production)[^*]*\*\*",
                after,
                re.I,
            ):
                issues.append(
                    _fail(
                        "V-FIG-SOUP",
                        f"page {pn}: label soup after text_diagram fence ({fig['id']})",
                    )
                )

    # --- V-CALLOUT-LEAD (p.30) ---
    body30 = _page_body(md, 30)
    if body30:
        # Only same-line glue (do not let \s match across newlines)
        if re.search(
            r"^- .*(?:etc\.\)\.|etc\.\))[ \t]+The linked concepts of plurilingualism",
            body30,
            re.M | re.I,
        ):
            issues.append(
                _fail("V-CALLOUT-LEAD", "p.30 plurilingual lead still glued to list item")
            )
        if "The linked concepts of plurilingualism" not in body30:
            issues.append(_fail("V-CALLOUT-LEAD", "p.30 missing plurilingual lead sentence"))
        # Must appear inside a blockquote (blue box path)
        if "The linked concepts of plurilingualism" in body30 and not re.search(
            r"^>\s+.*linked concepts of plurilingualism",
            body30,
            re.M | re.I,
        ):
            issues.append(
                _fail(
                    "V-CALLOUT-LEAD",
                    "p.30 plurilingual lead not in blockquote (> …) form",
                )
            )

    # --- V-CALLOUT-FMT: known titles should use blockquote form when present ---
    callout_titles = (
        ("A reminder of CEFR 2001 chapters", 29),
        ('"Can do" descriptors as competence', 35),
        ("“Can do” descriptors as competence", 35),
    )
    for title, pn in callout_titles:
        body = _page_body(md, pn)
        if not body:
            continue
        # Title present but not as > **Title**
        plain = title.replace('"', "").replace("“", "").replace("”", "")
        if plain[:20].lower() in body.lower() or title in body:
            if not re.search(
                rf"^>\s*\*\*.*{re.escape(title[:18])}.*\*\*",
                body,
                re.M | re.I,
            ) and not re.search(r"^>\s*\*\*.*Can do.*\*\*", body, re.M | re.I):
                # reminder page
                if pn == 29 and not re.search(
                    r"^>\s*\*\*.*reminder of CEFR", body, re.M | re.I
                ):
                    issues.append(
                        _fail(
                            "V-CALLOUT-FMT",
                            f"p.{pn}: callout title not in blockquote form (> **…**)",
                        )
                    )
                elif pn == 35 and not re.search(
                    r"^>\s*\*\*.*Can do", body, re.M | re.I
                ):
                    issues.append(
                        _fail(
                            "V-CALLOUT-FMT",
                            f"p.{pn}: Can-do callout not in blockquote form",
                        )
                    )

    # --- V-ORDER-31: top-left callout / columns before main body phrase ---
    body31 = _page_body(md, 31)
    if body31:
        ref_idx = body31.find("Most of the references")
        curious_idx = body31.find("By a curious coincidence")
        if ref_idx < 0:
            issues.append(_fail("V-ORDER-31", "p.31 missing body phrase Most of the references"))
        elif curious_idx < 0:
            issues.append(
                _fail("V-ORDER-31", "p.31 missing top callout lead (By a curious coincidence)")
            )
        elif curious_idx > ref_idx:
            issues.append(
                _fail(
                    "V-ORDER-31",
                    "p.31: callout/top content after 'Most of the references' (order reversed)",
                )
            )
        # Top-left box should be blockquote
        if curious_idx >= 0 and not re.search(
            r"^>\s+.*curious coincidence",
            body31,
            re.M | re.I,
        ):
            issues.append(
                _fail("V-ORDER-31", "p.31 top content not in blockquote form")
            )

    # --- V-LINK-GUIDE ---
    # Guide title should appear near the CoE curricula URL somewhere in Ch2
    guide_pat = re.compile(
        r"Guide for the development and implementation of curricula for plurilingual",
        re.I,
    )
    url_pat = "16806ae621"
    found_near = False
    for pn in range(30, 34):
        body = _page_body(md, pn)
        if not body:
            continue
        for m in guide_pat.finditer(body):
            window = body[m.start() : m.start() + 400]
            if url_pat in window or "rm.coe.int" in window:
                found_near = True
                break
        if found_near:
            break
    if guide_pat.search(md) and not found_near:
        # Title exists but URL not nearby
        if url_pat not in md[md.find("<!-- page:30 -->") : md.find("<!-- page:34 -->") if "<!-- page:34 -->" in md else len(md)]:
            issues.append(
                _fail(
                    "V-LINK-GUIDE",
                    "Guide curricula title without nearby CoE URL (16806ae621) on p.30–33",
                )
            )
        else:
            issues.append(
                _fail(
                    "V-LINK-GUIDE",
                    "Guide title not adjacent to URL parenthetical (link attach failed)",
                )
            )

    # --- V-PROSE-MASS (delegate) ---
    try:
        from pipeline.validate_chunk_prose import validate_figure_pages_prose

        for msg in validate_figure_pages_prose(md_path):
            issues.append(_fail("V-PROSE-MASS", msg))
    except Exception as exc:  # noqa: BLE001
        issues.append(_fail("V-PROSE-MASS", f"validator error: {exc}"))

    # --- C2-ADJ: adjacent-element damage (log 04 systemic) ---
    try:
        from pipeline.adjacent_guard import validate_adjacent

        issues.extend(validate_adjacent(md_path))
    except Exception as exc:  # noqa: BLE001
        issues.append(_fail("V-ADJ", f"adjacent_guard error: {exc}"))

    report = {
        "valid": len(issues) == 0,
        "issue_count": len(issues),
        "issues": issues,
        "path": str(md_path),
    }
    out = cfg.METADATA_DIR / "contract_validation.json"
    try:
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except OSError:
        pass
    return report

def main() -> int:
    from pipeline.bootstrap import parse_and_load_job

    parse_and_load_job(description="Fail-closed contract validators")
    report = validate_contracts()
    if report["valid"]:
        print("CONTRACT VALIDATION OK")
        return 0
    print(f"CONTRACT VALIDATION FAIL ({report['issue_count']} issue(s))")
    for iss in report["issues"]:
        print(f" - [{iss['gate']}] {iss['detail']}")
    print(f"(report: {cfg.METADATA_DIR / 'contract_validation.json'})")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
