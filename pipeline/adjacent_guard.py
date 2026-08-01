"""Adjacent-element regression gates (C2-ADJ).

When a figure/callout/table is "fixed", neighbors must not silently break.
See docs/CONTRACTS.md § adjacent-element protection and user debug/log 04.md.

Fail closed: these issues used to ship green while the user found them.

Golden suite: work/<job-id>/metadata/golden/page_NNN.json
(must_have / must_not_have / counts).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
import pipeline.config as cfg
from pipeline.config import feature_enabled, final_markdown_path, get_active_job


def _golden_dir() -> Path:
    """Active job golden suite — resolve at call time (not import-time freeze)."""
    return cfg.METADATA_DIR / "golden"


def _companion_snippet_gates() -> bool:
    """Hard-coded Companion page/title checks — off for non-Companion jobs."""
    ctx = get_active_job()
    if ctx is None:
        return False
    if ctx.profile == "cefr_companion":
        return True
    return feature_enabled("adjacent_companion_snippets", default=False)

def _page_body(md: str, page_num: int) -> str:
    m = re.search(rf"<!-- page:{page_num} -->", md)
    if not m:
        return ""
    prev = list(re.finditer(r"<!-- page:(\d+) -->", md[: m.start()]))
    start = prev[-1].end() if prev else 0
    return md[start : m.start()]

def _fail(gate: str, detail: str) -> dict:
    return {"gate": gate, "severity": "high", "detail": detail}

# Radar / profile diagram axis fragments (Figs 6–10) left as "prose" under PNG.
_RADAR_AXIS = re.compile(
    r"(Understanding conversation between other|Expressing a personal response|"
    r"Relaying specific information|Processing text in speech|"
    r"Collaborating to construct meaning|Facilitating collaborative|"
    r"Sustained monologue|Reading for orientation|Reading for information|"
    r"Goal-oriented co-operation|Informal discussion \(with friends\)|"
    r"Formal discussion \(meetings\)|Understanding an interlocutor|"
    r"Watching TV, film and video|Creative writing|Reports and essays)",
    re.I,
)
_MODE_LABEL = re.compile(
    r"^\*{0,2}\s*(RECEPTION|PRODUCTION|INTERACTION|MEDIATION)\s*\*{0,2}"
    r"(?:\s|$|[A-Za-z*])",
    re.I,
)

def _lines_after_figure_image(body: str, fig_id_prefix: str = "figure_") -> list[str]:
    """Lines after a figure PNG until next structural boundary."""
    out: list[str] = []
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        if re.search(rf"!\[[^\]]*\]\([^)]*{fig_id_prefix}[^)]*\.png\)", lines[i]):
            j = i + 1
            while j < len(lines):
                s = lines[j].strip()
                if not s:
                    j += 1
                    continue
                if s.startswith(
                    ("<!-- page:", "<!-- db:id=", "<!-- el:", "### ", "## ", "| ", "> ")
                ) or re.match(r"^\d+\.\t", s) or re.match(r"^\*Page\s+\*\*", s) or re.match(
                    r"^Page\s+\*\*", s
                ):
                    break
                # Real sentence prose: long line ending with period
                if len(s) > 80 and s.endswith((".", "?", "!")) and not _RADAR_AXIS.search(s):
                    break
                out.append(s)
                j += 1
            i = j
            continue
        i += 1
    return out

def _load_goldens() -> list[dict]:
    golden_dir = _golden_dir()
    if not golden_dir.is_dir():
        return []
    out: list[dict] = []
    for path in sorted(golden_dir.glob("page_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_path"] = str(path)
            out.append(data)
        except (OSError, json.JSONDecodeError) as exc:
            out.append({"page": -1, "_error": f"{path.name}: {exc}", "_path": str(path)})
    return out

def _validate_golden_file(body: str, g: dict, page_num: int) -> list[dict]:
    issues: list[dict] = []
    if g.get("_error"):
        issues.append(_fail("V-ADJ-GOLDEN", g["_error"]))
        return issues
    for phrase in g.get("must_have") or []:
        if phrase not in body:
            issues.append(
                _fail(
                    "V-ADJ-GOLDEN",
                    f"page {page_num}: must_have missing {phrase!r} ({Path(g.get('_path','')).name})",
                )
            )
    for phrase in g.get("must_not_have") or []:
        if phrase and phrase in body:
            issues.append(
                _fail(
                    "V-ADJ-GOLDEN",
                    f"page {page_num}: must_not_have present {phrase!r}",
                )
            )
    # Phrases forbidden only after first figure image/db:id
    img_pos = -1
    for m in re.finditer(r"(!\[[^\]]*\]\([^)]*figure_\d+[^)]*\.png\)|<!--\s*db:id=figure_)", body):
        img_pos = m.start()
        break
    if img_pos >= 0:
        after = body[img_pos:]
        for phrase in g.get("must_not_have_after_image") or g.get("must_not_have_after_figure") or []:
            if phrase and phrase in after:
                issues.append(
                    _fail(
                        "V-ADJ-GOLDEN",
                        f"page {page_num}: after figure must_not_have {phrase!r}",
                    )
                )
    # After text_diagram closing fence only (leaf titles may legitimately appear inside ```text)
    fence_end = -1
    in_text = False
    for m in re.finditer(r"^```(.*)$", body, re.M):
        info = (m.group(1) or "").strip()
        if not in_text and info.startswith("text"):
            in_text = True
            continue
        if in_text and info == "":
            fence_end = m.end()
            in_text = False
    if fence_end >= 0:
        after_fence = body[fence_end:]
        for phrase in g.get("must_not_have_after_diagram_fence") or []:
            if phrase and phrase in after_fence:
                issues.append(
                    _fail(
                        "V-ADJ-GOLDEN",
                        f"page {page_num}: after text_diagram fence must_not_have {phrase!r} "
                        "(dual-emitted leaf soup)",
                    )
                )
    for phrase, max_n in (g.get("max_title_count") or {}).items():
        # Prefer counting blockquote title lines when phrase looks like a callout title
        n = body.count(phrase)
        if n > int(max_n):
            issues.append(
                _fail(
                    "V-ADJ-GOLDEN",
                    f"page {page_num}: {phrase!r} count {n} > max {max_n}",
                )
            )
    for phrase, max_n in (g.get("max_heading_count") or {}).items():
        n = len(re.findall(re.escape(phrase), body))
        if phrase.startswith("###"):
            n = len(
                re.findall(
                    r"^" + re.escape(phrase.rstrip()) + r"\s*$",
                    body,
                    re.M | re.I,
                )
            )
        if n > int(max_n):
            issues.append(
                _fail(
                    "V-ADJ-GOLDEN",
                    f"page {page_num}: heading {phrase!r} count {n} > max {max_n}",
                )
            )
    # Multi-fig order: list of figure numbers in expected emission order
    order = g.get("figure_order")
    if order:
        found: list[int] = []
        for m in re.finditer(
            r"<!--\s*db:id=figure_(\d+)_|###\s+Figure\s+(\d+)\b",
            body,
            re.I,
        ):
            n = int(m.group(1) or m.group(2))
            if not found or found[-1] != n:
                found.append(n)
        # Unique stable order of first appearance
        uniq: list[int] = []
        for n in found:
            if n not in uniq:
                uniq.append(n)
        expected = [int(x) for x in order]
        # Only compare the expected subset order among those present
        present_expected = [n for n in expected if n in uniq]
        actual = [n for n in uniq if n in expected]
        if present_expected and actual != present_expected:
            issues.append(
                _fail(
                    "V-ADJ-GOLDEN",
                    f"page {page_num}: figure_order expected {present_expected}, got {actual}",
                )
            )
    # Callout placement policy asserts (log 04 / review #6)
    placement = g.get("callout_placement")
    if placement == "end_body":
        # Blockquote title should appear after last substantial prose and before footnotes/Page
        bq = re.search(r"^>\s*\*\*", body, re.M)
        if bq:
            after_bq = body[bq.start() :]
            # Footnote or Page should still be after callout
            if not re.search(r"(?:^\d{1,2}\.\s|Page\s+\*\*)", after_bq, re.M):
                # page may use only Page line
                if f"Page **{page_num}**" not in after_bq and f"*Page **{page_num}**" not in after_bq:
                    issues.append(
                        _fail(
                            "V-ADJ-CALLOUT-PLACE",
                            f"page {page_num}: end_body callout not before page footer",
                        )
                    )
            # Mid-body: long prose paragraph after callout blockquote before footnotes = bad
            # Strip footnotes/page from after_bq and look for long non-quote prose
            rest = after_bq
            rest = re.split(r"\n\d{1,2}\.\s", rest, maxsplit=1)[0]
            rest = re.split(r"\nPage\s+\*\*", rest, maxsplit=1)[0]
            long_prose = [
                ln
                for ln in rest.splitlines()
                if ln.strip()
                and not ln.strip().startswith((">", "<!--", "#", "*", "|"))
                and len(ln.strip()) > 120
            ]
            if long_prose:
                issues.append(
                    _fail(
                        "V-ADJ-CALLOUT-PLACE",
                        f"page {page_num}: long prose after end_body callout "
                        f"(should be last body element): {long_prose[0][:60]!r}",
                    )
                )
    elif placement == "top_left":
        bq = re.search(r"^>\s*\*\*", body, re.M)
        if bq and bq.start() > len(body) * 0.45:
            issues.append(
                _fail(
                    "V-ADJ-CALLOUT-PLACE",
                    f"page {page_num}: top_left callout appears late in page body",
                )
            )
    return issues

def validate_adjacent(md_path: Path | None = None) -> list[dict]:
    """Return list of high-severity adjacent-damage issues."""
    md_path = md_path or final_markdown_path()
    issues: list[dict] = []
    if not md_path.exists():
        return [_fail("V-ADJ-MD-MISSING", str(md_path))]

    md = md_path.read_text(encoding="utf-8")

    # File-based golden suite is job-local data — always run when present.
    for g in _load_goldens():
        pn = int(g.get("page") or -1)
        if pn < 0:
            issues.extend(_validate_golden_file("", g, pn))
            continue
        body = _page_body(md, pn)
        if not body:
            issues.append(_fail("V-ADJ-GOLDEN", f"page {pn}: page body missing for golden"))
            continue
        issues.extend(_validate_golden_file(body, g, pn))

    # Remaining gates hard-code Companion page numbers / titles.
    if not _companion_snippet_gates():
        return issues

    # --- V-ADJ-FIGURE-SOUP: garbage under PNG (log 04 #8, log 01 Fig 6–8, review #2) ---
    _LEVEL_LANG_ROW = re.compile(
        r"(Pre-A1|A1|A2\+?|B1\+?|B2\+?|C1|C2).{0,40}(A1|A2|B1|B2|C1|C2).{0,80}"
        r"(English|German|French|Spanish|Italian)",
        re.I,
    )
    _MULTI_LEVEL = re.compile(
        r"(?:Pre-A1|A1|A2\+?|B1\+?|B2\+?|C1|C2|Above C2)(?:\s+(?:Pre-A1|A1|A2\+?|B1\+?|B2\+?|C1|C2|Above C2)){3,}",
        re.I,
    )
    for pn in (34, 36, 38, 39, 40):
        body = _page_body(md, pn)
        if not body:
            continue
        after = _lines_after_figure_image(body)
        for line in after:
            if (
                _RADAR_AXIS.search(line)
                or _MODE_LABEL.match(line)
                or _LEVEL_LANG_ROW.search(line)
                or _MULTI_LEVEL.search(line)
            ):
                issues.append(
                    _fail(
                        "V-ADJ-FIGURE-SOUP",
                        f"page {pn}: figure-label garbage under PNG: {line[:70]!r}",
                    )
                )
                break
            # Short axis-only lines
            if (
                len(line) < 90
                and not line.endswith((".", "?", "!"))
                and not line.startswith(("#", "!", "<!--", "|", ">"))
                and re.search(
                    r"\b(RECEPTION|PRODUCTION|INTERACTION|MEDIATION|Listening|Reading)\b",
                    line,
                    re.I,
                )
            ):
                issues.append(
                    _fail(
                        "V-ADJ-FIGURE-SOUP",
                        f"page {pn}: likely diagram label under PNG: {line[:70]!r}",
                    )
                )
                break
        # Also scan any post-image region for multi-level language rows (Fig 10 form)
        for m in re.finditer(
            r"!\[[^\]]*\]\([^)]*figure_\d+[^)]*\.png\)", body
        ):
            frag = body[m.end() : m.end() + 400]
            if _LEVEL_LANG_ROW.search(frag) or _MULTI_LEVEL.search(frag):
                issues.append(
                    _fail(
                        "V-ADJ-FIGURE-SOUP",
                        f"page {pn}: level/language axis row under PNG",
                    )
                )
                break

    # --- V-ADJ-DUP-HEADER: consecutive ### Figure N or callout title twice ---
    for pn in (29, 32, 34, 35, 38, 39, 47):
        body = _page_body(md, pn)
        figs = re.findall(r"^###\s+(Figure\s+\d+[^\n|]*)", body, re.M | re.I)
        seen: dict[str, int] = {}
        for f in figs:
            key = re.sub(r"\s+", " ", f.lower())[:40]
            seen[key] = seen.get(key, 0) + 1
        for k, n in seen.items():
            if n > 1:
                issues.append(
                    _fail("V-ADJ-DUP-HEADER", f"page {pn}: duplicate figure header {k!r} x{n}")
                )
        # Callout title bold twice (log 04 #3)
        if pn in (29, 35):
            if body.count("A reminder of CEFR 2001 chapters") > 1:
                issues.append(
                    _fail("V-ADJ-DUP-HEADER", f"page {pn}: callout title repeated")
                )
            if len(re.findall(r"Can do.? descriptors as competence", body, re.I)) > 1:
                issues.append(
                    _fail("V-ADJ-DUP-HEADER", f"page {pn}: Can-do title repeated")
                )

    # --- V-ADJ-PAGE-FOOTER: footnote not glued to Page **N** (log 04 #5, #13) ---
    for pn in range(26, 48):
        body = _page_body(md, pn)
        if not body:
            continue
        # Page caption glued to previous non-empty line.
        # OK forms (L05-PAGE-AST): italic ``*Page **N** …`` and chapter
        # ``… ▶ Page **N**`` — the char immediately before "Page" is * or ▶.
        if re.search(rf"[^\n\s*▶][ \t]*Page\s+\*\*{pn}\*\*", body):
            issues.append(
                _fail(
                    "V-ADJ-PAGE-FOOTER",
                    f"page {pn}: Page **{pn}** glued to previous line (no blank before)",
                )
            )
        # Explicit: footnote digit line immediately followed by bare Page without blank
        # (not italic *Page or chapter ▶ Page)
        if re.search(rf"https?://[^\n]+\nPage\s+\*\*{pn}\*\*", body):
            issues.append(
                _fail(
                    "V-ADJ-PAGE-FOOTER",
                    f"page {pn}: missing blank line between footnote URL and Page **{pn}**",
                )
            )

    # --- V-ADJ-SECTION-AFTER-FIG: p.47 ### 3.1 RECEPTION (log 04 #10) ---
    body47 = _page_body(md, 47)
    if body47 and "figure_11" in body47:
        # Require body heading (not TOC "— 47") after figure
        if not re.search(r"###\s*3\.1\.?\s*RECEPTION\s*$", body47, re.M | re.I) and not re.search(
            r"###\s*3\.1\.?\s*RECEPTION\s*\n", body47, re.I
        ):
            issues.append(
                _fail(
                    "V-ADJ-SECTION-AFTER-FIG",
                    "page 47: missing ### 3.1 RECEPTION after Figure 11 "
                    "(adjacent damage class — fix figure without dropping next header)",
                )
            )
        elif "Reception involves receiving" not in body47:
            issues.append(
                _fail(
                    "V-ADJ-SECTION-AFTER-FIG",
                    "page 47: 3.1 present but lead prose after Figure 11 missing",
                )
            )
        # Exactly one body heading
        n31 = len(re.findall(r"^###\s*3\.1\.?\s*RECEPTION\s*$", body47, re.M | re.I))
        if n31 > 1:
            issues.append(
                _fail(
                    "V-ADJ-SECTION-AFTER-FIG",
                    f"page 47: ### 3.1 RECEPTION appears {n31} times (duplicate heading)",
                )
            )

    # --- V-ADJ-GOLDEN: hard-coded p.38 axis check (file goldens already ran above) ---
    body38 = _page_body(md, 38)
    if body38 and "figure_06" in body38:
        if "Understanding conversation between other speakers" in body38:
            img = body38.find("figure_06")
            frag = body38.find("Understanding conversation between other speakers")
            if img >= 0 and frag > img:
                issues.append(
                    _fail(
                        "V-ADJ-GOLDEN",
                        "page 38: radar axis text under/after Figure 6 PNG "
                        "(replace semantics failed — dual emission)",
                    )
                )

    # log 04 critical: callout mid-paragraph glue on 27–28
    for pn in (27, 28):
        body = _page_body(md, pn)
        if not body:
            continue
        if re.search(r"[a-z]\s*\n\n?>\s*\*\*", body):
            issues.append(
                _fail(
                    "V-ADJ-CALLOUT-PLACE",
                    f"page {pn}: callout appears after mid-sentence prose "
                    "(placement policy: non-top-left → end of body)",
                )
            )

    # p.39–40 neighbor prose must exist (fail closed if exclusive crop ate body)
    body39 = _page_body(md, 39)
    if body39 and "figure_07" in body39:
        if "However, for a personal profile of proficiency" not in body39:
            issues.append(
                _fail(
                    "V-ADJ-PROSE-AFTER-FIG",
                    "page 39: missing trailing prose about personal profile "
                    "(exclusive crop must not delete neighbor body)",
                )
            )
    body40 = _page_body(md, 40)
    if body40 and "figure_08" in body40:
        if "Graphic profiles have been associated with the CEFR" not in body40:
            issues.append(
                _fail(
                    "V-ADJ-PROSE-AFTER-FIG",
                    "page 40: missing 'Graphic profiles have been associated…' "
                    "(exclusive crop / dual-layout neighbor loss)",
                )
            )

    # Fig 12 p.61: no dual-emit leaf soup; trailing §3.2.1 prose must survive
    body61 = _page_body(md, 61)
    if body61 and "figure_12" in body61:
        for trash in (
            "\nPublic announcements\n",
            "\nPlanning\n",
            "\nCompensating\n",
            "\nMonitoring and repair\n",
        ):
            # only fail if appears *outside* fence after diagram
            fence = body61.find("```")
            fence_end = body61.find("```", fence + 3) if fence >= 0 else -1
            after = body61[fence_end + 3 :] if fence_end >= 0 else body61
            if trash.strip() in after and f"├── {trash.strip()}" not in after:
                # bare line soup (not tree)
                if re.search(
                    rf"(?m)^(?:\*\*)?{re.escape(trash.strip())}(?:\*\*)?\s*$", after
                ):
                    issues.append(
                        _fail(
                            "V-ADJ-FIG12-SOUP",
                            f"page 61: dual-emit leaf soup after Figure 12 fence: {trash.strip()!r}",
                        )
                    )
                    break
        if "rather than dialogue" not in body61.lower():
            issues.append(
                _fail(
                    "V-ADJ-FIG12-TRAIL",
                    "page 61: missing trailing oral-production prose "
                    "ending 'rather than dialogue' (after Figure 12)",
                )
            )
        if not re.search(r"3\.2\.1\.?\s*Production activities", body61, re.I):
            issues.append(
                _fail(
                    "V-ADJ-FIG12-SEC",
                    "page 61: missing §3.2.1 Production activities after Figure 12",
                )
            )

    # R1: p.47 text_diagram leaf soup after fence / after 3.1 lead
    if body47 and "figure_11" in body47:
        # Region after closing ``` of text_diagram
        after_fence = ""
        in_text = False
        for m in re.finditer(r"^```(.*)$", body47, re.M):
            info = (m.group(1) or "").strip()
            if not in_text and info.startswith("text"):
                in_text = True
                continue
            if in_text and info == "":
                after_fence = body47[m.end() :]
                break
        soup_markers = (
            "comprehension comprehension",
            "Overall oral Watching TV",
            "Overall reading Identifying cues",
        )
        for sm in soup_markers:
            if sm in after_fence:
                issues.append(
                    _fail(
                        "V-ADJ-FIGURE-SOUP",
                        f"page 47: text_diagram dual-emit residue after fence: {sm!r}",
                    )
                )
                break
        # Leaf title outside fence (exact activity line after 3.1)
        for leaf in (
            "Understanding as a member of a live audience",
            "Understanding announcements and instructions",
            "Reading correspondence",
        ):
            # Allow only inside ``` fence — if appears after fence, fail
            if leaf in after_fence:
                issues.append(
                    _fail(
                        "V-ADJ-FIGURE-SOUP",
                        f"page 47: leaf title dual-emitted after text_diagram: {leaf!r}",
                    )
                )
                break

    return issues

def validate_adjacent_report(md_path: Path | None = None) -> dict:
    issues = validate_adjacent(md_path)
    report = {
        "valid": len(issues) == 0,
        "issue_count": len(issues),
        "issues": issues,
        "path": str(md_path or final_markdown_path()),
        "golden_dir": str(_golden_dir()),
    }
    out = cfg.METADATA_DIR / "adjacent_validation.json"
    try:
        out.write_text(
            json.dumps(report, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass
    return report

if __name__ == "__main__":
    from pipeline.bootstrap import parse_and_load_job

    parse_and_load_job(description="Adjacent-element regression gates (C2-ADJ)")
    r = validate_adjacent_report()
    if r["valid"]:
        print("ADJACENT VALIDATION OK")
        raise SystemExit(0)
    print(f"ADJACENT VALIDATION FAIL ({r['issue_count']})")
    for iss in r["issues"]:
        print(f" - [{iss['gate']}] {iss['detail']}")
    raise SystemExit(1)
