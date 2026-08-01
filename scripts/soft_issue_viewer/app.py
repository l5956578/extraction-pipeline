#!/usr/bin/env python3
"""Local soft-issue inspector: side-by-side old vs new markdown around regression soft_issues.

Launch (from extraction-pipeline root or any cwd):
  python scripts/soft_issue_viewer/app.py
  python scripts/soft_issue_viewer/app.py --port 8765

Defaults (Companion job — remaining soft issues after hard pins):
  report  work/cefr-companion-2020/metadata/regression_report.json
  old     work/.../baseline_pre_full_rerun/  (else baseline_pre_rerun, else versions/001)
  new     output/cefr-companion-2020/CEFR_Companion_Volume.md
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template_string

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]  # extraction-pipeline/

DEFAULT_REPORT = (
    ROOT / "work" / "cefr-companion-2020" / "metadata" / "regression_report.json"
)
DEFAULT_NEW = ROOT / "output" / "cefr-companion-2020" / "CEFR_Companion_Volume.md"

# Prefer latest pre-full-rerun baseline, then older pre-rerun, then version 001
_BASELINE_CANDIDATES = [
    ROOT
    / "work"
    / "cefr-companion-2020"
    / "metadata"
    / "baseline_pre_full_rerun"
    / "CEFR_Companion_Volume.md",
    ROOT
    / "work"
    / "cefr-companion-2020"
    / "metadata"
    / "baseline_pre_rerun"
    / "CEFR_Companion_Volume.md",
    ROOT
    / "output"
    / "cefr-companion-2020"
    / "versions"
    / "001"
    / "CEFR_Companion_Volume.md",
]

TEMP_OLD = (
    Path.home()
    / "AppData"
    / "Local"
    / "Temp"
    / "cefr-companion-baseline-pre-rerun"
    / "CEFR_Companion_Volume.md"
)

CONTEXT_BEFORE = 30
CONTEXT_AFTER = 60

app = Flask(__name__)
CFG: dict = {}


# ---------------------------------------------------------------------------
# Soft-issue verdicts — so you know whether to inspect content or skip
# ---------------------------------------------------------------------------
#
# Soft issues are NOT always "something is broken in the MD."
# Many are: inventory/validator expected string A; deliverable has correct content as B.
# Verdicts:
#   skip     (green)  — content OK under a known better form; old/new may match; safe to skip
#   review   (yellow) — content present but maybe wrong shape; one look, then decide
#   check    (red)    — expected signal missing; compare panes / read NEW carefully
#   info     (blue)   — meta/noise; no visual confirmation needed

# Layout pins that supersede stale inventory scale/table ids
_KNOWN_PIN_ON_PAGE: dict[int, str] = {
    23: "table_01_descriptive_scheme_updates",
    24: "table_02_summary_descriptor_changes",
    33: "table_03_macro_functional_basis",
}


def _page_text(lines: list[str], page: int | None) -> str:
    if page is None:
        return "\n".join(lines)
    rng = _page_body_range(lines, page)
    if not rng:
        return ""
    return "\n".join(lines[rng[0] : rng[1]])


def _default_old() -> Path:
    for p in _BASELINE_CANDIDATES:
        if p.is_file():
            return p
    return TEMP_OLD


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _page_line_index(lines: list[str], page: int) -> int | None:
    needle = f"<!-- page:{page} -->"
    for i, ln in enumerate(lines):
        if needle in ln:
            return i
    return None


def _page_body_range(lines: list[str], page: int) -> tuple[int, int] | None:
    """0-based [start, end) line range for content of page N (before page:N marker)."""
    markers: list[tuple[int, int]] = []
    for i, ln in enumerate(lines):
        m = re.search(r"<!-- page:(\d+) -->", ln)
        if m:
            markers.append((i, int(m.group(1))))
    for j, (li, pn) in enumerate(markers):
        if pn == page:
            start = markers[j - 1][0] + 1 if j > 0 else 0
            return start, li
    return None


def _header_variants(header: str) -> list[str]:
    """Inventory headers often differ slightly from emitted ### lines."""
    h = (header or "").strip()
    if not h:
        return []
    out = [h]
    out.append(re.sub(r"(\d)\.\s+", r"\1 ", h))  # 3.1. X → 3.1 X
    out.append(re.sub(r"\.\s+", " ", h))
    # phrase without numbering: "Oral production"
    phrase = re.sub(r"^[\d.\s]+", "", h).strip()
    if phrase:
        out.append(phrase)
    # last dotted segment only if longer than 2 chars
    if "." in h:
        tail = h.split(".")[-1].strip()
        if len(tail) > 2:
            out.append(tail)
    for base in list(out):
        if base:
            out.append(f"### {base}")
            out.append(f"#### {base}")
    seen: set[str] = set()
    uniq: list[str] = []
    for x in out:
        k = x.lower()
        if x and k not in seen and len(x) >= 3:
            seen.add(k)
            uniq.append(x)
    return uniq


def _primary_phrase(header: str | None) -> str:
    if not header:
        return ""
    return re.sub(r"^[\d.\s]+", "", str(header)).strip()


def _line_matches_phrase(line: str, phrase: str) -> bool:
    """True if line contains phrase as a meaningful unit (not only inside a longer label)."""
    if not phrase or len(phrase) < 3:
        return False
    low = line.lower()
    p = phrase.lower()
    if p not in low:
        return False
    # Prefer exact-ish tree/heading labels over "Overall oral production" when phrase is "Oral production"
    # Score later; here just membership.
    return True


def _score_focus_line(line: str, phrase: str, needles: list[str]) -> int:
    """Higher = better focus line for this issue."""
    s = line.strip()
    low = s.lower()
    score = 0
    p = (phrase or "").lower()
    if p and p in low:
        score += 50
        # Prefer tree leaf "├── Oral production" over "Overall oral production"
        if re.search(rf"(?:^|[│├└\s]){re.escape(p)}(?:\s|$)", low):
            score += 40
        if low.strip().endswith(p) or re.search(rf"├──\s*{re.escape(p)}\s*$", low):
            score += 30
        # Penalize longer labels that merely contain the phrase
        if p and f"overall {p}" in low:
            score -= 35
        if p and low.startswith("###") and p in low and f"figure" in low:
            score += 10  # figure title mentioning production activities
    for n in needles:
        if n and len(n) >= 6 and n.lower() in low:
            score += min(20, len(n) // 2)
    if re.match(r"^#{1,4}\s+", s):
        score += 15
    if "├" in s or "└" in s or "│" in s:
        score += 10
    if "db:id=" in s or "el:start" in s:
        score += 5
    return score


def _best_focus_in_range(
    lines: list[str], start: int, end: int, phrase: str, needles: list[str]
) -> tuple[int | None, str]:
    best_i: int | None = None
    best_sc = -1
    for i in range(start, min(end, len(lines))):
        sc = _score_focus_line(lines[i], phrase, needles)
        if sc > best_sc:
            best_sc = sc
            best_i = i
    if best_sc < 20:
        return None, "no_confident_hit"
    return best_i, f"score={best_sc}"


def _issue_needles(issue: dict) -> list[str]:
    code = str(issue.get("code") or "")
    needles: list[str] = []
    header = issue.get("header")
    if header:
        needles.extend(_header_variants(str(header)))
        phrase = _primary_phrase(str(header))
        if phrase:
            needles.insert(0, phrase)
    for key in ("actual_id", "expected_id", "artifact_id", "group_id", "id", "found_as"):
        if issue.get(key) and isinstance(issue[key], str):
            needles.append(str(issue[key]))
    if code == "page_47_section_order":
        needles = [
            "### 3.1 RECEPTION",
            "3.1 RECEPTION",
            "figure_11_reception_activities_strategies",
            "Figure 11",
            "Reception involves",
        ] + needles
    if code == "missing_span_artifact":
        page = issue.get("page") if isinstance(issue.get("page"), int) else 24
        pin = _KNOWN_PIN_ON_PAGE.get(page, "table_02_summary_descriptor_changes")
        needles = [
            pin,
            "Table 2 – Summary of changes",
            "Table 2",
            str(issue.get("group_id") or "scale_what_is_addressed_in_this_publication"),
        ] + needles
    # dedupe
    seen: set[str] = set()
    out: list[str] = []
    for n in needles:
        k = n.lower()
        if n and k not in seen:
            seen.add(k)
            out.append(n)
    return out[:16]


def resolve_focus(issue: dict, lines: list[str], *, side: str = "new") -> dict:
    """Pick the best focus line for this issue on this side's text."""
    code = str(issue.get("code") or "")
    page = issue.get("page") if isinstance(issue.get("page"), int) else None
    header = issue.get("header")
    phrase = _primary_phrase(str(header) if header else "")
    needles = _issue_needles(issue)

    if code == "page_47_section_order":
        page = page or 47
        phrase = phrase or "3.1 RECEPTION"
    if code == "missing_span_artifact":
        page = page or 24
        phrase = phrase or "Table 2"

    # Search range: prefer page body
    if page is not None:
        rng = _page_body_range(lines, page)
        if rng:
            start, end = rng
        else:
            pi = _page_line_index(lines, page)
            start = max(0, (pi or 0) - 80)
            end = min(len(lines), (pi or 0) + 20)
    else:
        start, end = 0, len(lines)

    hit, why = _best_focus_in_range(lines, start, end, phrase, needles)
    if hit is not None:
        return {
            "page": page,
            "line0": hit,
            "line1": hit + 1,
            "needle": phrase or (needles[0] if needles else None),
            "needles": needles,
            "phrase": phrase,
            "reason": f"{side}:{why}",
        }

    # Fallback: report line (often weak) or page middle
    if side == "new" and isinstance(issue.get("line"), int) and issue["line"] >= 1:
        line0 = min(issue["line"] - 1, max(0, len(lines) - 1))
        return {
            "page": page,
            "line0": line0,
            "line1": line0 + 1,
            "needle": phrase or (needles[0] if needles else None),
            "needles": needles,
            "phrase": phrase,
            "reason": "fallback:report.line",
        }

    line0 = max(0, (start + end) // 2 - 5) if end > start else 0
    return {
        "page": page,
        "line0": line0,
        "line1": line0 + 1,
        "needle": phrase or (needles[0] if needles else None),
        "needles": needles,
        "phrase": phrase,
        "reason": f"fallback:page_mid:{page}",
    }


def window_lines(
    lines: list[str],
    center0: int,
    before: int = CONTEXT_BEFORE,
    after: int = CONTEXT_AFTER,
) -> tuple[list[dict], int, int]:
    start = max(0, center0 - before)
    end = min(len(lines), center0 + after + 1)
    rows = [{"n": i + 1, "text": lines[i]} for i in range(start, end)]
    return rows, start, end


def aligned_diff(
    old_win: list[dict], new_win: list[dict]
) -> tuple[list[dict], list[dict]]:
    a = [r["text"] for r in old_win]
    b = [r["text"] for r in new_win]
    sm = SequenceMatcher(a=a, b=b, autojunk=False)
    old_out: list[dict] = []
    new_out: list[dict] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i1, i2):
                old_out.append({**old_win[k], "cls": "eq"})
            for k in range(j1, j2):
                new_out.append({**new_win[k], "cls": "eq"})
        elif tag == "replace":
            for k in range(i1, i2):
                old_out.append({**old_win[k], "cls": "del"})
            for k in range(j1, j2):
                new_out.append({**new_win[k], "cls": "ins"})
        elif tag == "delete":
            for k in range(i1, i2):
                old_out.append({**old_win[k], "cls": "del"})
        elif tag == "insert":
            for k in range(j1, j2):
                new_out.append({**new_win[k], "cls": "ins"})
    return old_out, new_out


def _mark_rows(
    rows: list[dict], *, phrase: str, needles: list[str], focus_line1: int
) -> list[dict]:
    """Highlight focus line + true phrase/needle hits (avoid over-highlight)."""
    primary = [phrase] if phrase else []
    # Only use longer needles for hit highlight (avoid tiny false hits)
    extra = [n for n in needles if n and len(n) >= 8][:8]
    out = []
    for r in rows:
        low = r["text"].lower()
        hit = False
        if phrase and _line_matches_phrase(r["text"], phrase):
            # Don't mark "Overall oral production" as primary hit for "Oral production"
            if f"overall {phrase.lower()}" in low and not re.search(
                rf"(?:├──|└──)\s*{re.escape(phrase.lower())}\s*$", low
            ):
                hit = False
            else:
                hit = True
        if not hit:
            for n in extra:
                if n.lower() in low:
                    hit = True
                    break
        is_focus = r["n"] == focus_line1
        cls = r.get("cls") or "eq"
        if is_focus:
            cls = f"{cls} focus-line"
        if hit:
            cls = f"{cls} hit"
        out.append({**r, "cls": cls, "hit": hit, "is_focus": is_focus})
    return out


def _scan_from_rows(
    rows: list[dict], *, phrase: str, needles: list[str], focus_line1: int, issue_index: int
) -> dict:
    """Bottom panel data — always rebuilt from the current issue's window rows."""
    window = "\n".join(r["text"] for r in rows)
    window_l = window.lower()
    checks: list[dict] = []
    # Primary phrase first
    if phrase:
        checks.append(
            {
                "needle": phrase,
                "found": phrase.lower() in window_l,
                "role": "primary",
            }
        )
    for n in needles:
        if not n or (phrase and n.lower() == phrase.lower()):
            continue
        if len(n) < 4:
            continue
        checks.append({"needle": n, "found": n.lower() in window_l, "role": "extra"})
        if len(checks) >= 10:
            break
    headings = [
        {"line": r["n"], "text": r["text"][:120]}
        for r in rows
        if re.match(r"^#{1,4}\s+", r["text"])
    ][:15]
    tree_hits = [
        {"line": r["n"], "text": r["text"][:120]}
        for r in rows
        if phrase and phrase.lower() in r["text"].lower() and ("├" in r["text"] or "│" in r["text"])
    ][:8]
    return {
        "issue_index": issue_index,
        "focus_line": focus_line1,
        "phrase": phrase,
        "needle_hits": checks,
        "headings_in_window": headings,
        "tree_hits": tree_hits,
        "window_line_start": rows[0]["n"] if rows else None,
        "window_line_end": rows[-1]["n"] if rows else None,
    }

def load_state() -> dict:
    report_path = Path(CFG["report"])
    old_path = Path(CFG["old"])
    new_path = Path(CFG["new"])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    soft = report.get("soft_issues") or []
    hard = report.get("issues") or []
    return {
        "report": report,
        "soft": soft,
        "hard": hard,
        "old_lines": _read_lines(old_path),
        "new_lines": _read_lines(new_path),
        "old_path": str(old_path),
        "new_path": str(new_path),
        "report_path": str(report_path),
    }


def _human_title(issue: dict) -> str:
    code = str(issue.get("code") or "")
    if code == "missing_section_header" and issue.get("header"):
        return f"header? {issue['header']}"
    if code == "page_47_section_order":
        return "p.47 Fig11 / 3.1 RECEPTION order"
    if code == "missing_span_artifact":
        gid = issue.get("group_id") or "stale span id"
        return f"stale span id ({gid})" if gid != "stale span id" else "stale span id"
    return code


def _classify_soft_issue(issue: dict, new_lines: list[str]) -> dict[str, Any]:
    """Decide skip / review / check and write plain-English confirmation instructions."""
    code = str(issue.get("code") or "")
    page = issue.get("page") if isinstance(issue.get("page"), int) else None
    body = _page_text(new_lines, page)
    body_l = body.lower()
    full = "\n".join(new_lines)

    verdict = "check"
    label = "NEEDS CHECK"
    why = ""
    you_do = ""
    compare = "Focus NEW. Old may look identical — that is normal for soft inventory issues."
    found_as: str | None = None

    # --- missing_span_artifact: often stale scale id for Table 2 ---
    if code == "missing_span_artifact":
        gid = str(issue.get("group_id") or "")
        pin = _KNOWN_PIN_ON_PAGE.get(page or -1, "")
        if pin and pin in full:
            verdict, label = "skip", "SKIP — inventory lag"
            found_as = pin
            why = (
                f"Validator still looks for span/scale id {gid or '…'!r}, but this page "
                f"already has the correct layout pin {pin!r}."
            )
            you_do = (
                "You do NOT need an old/new difference. In NEW, confirm Table 2 / pin id is "
                f"present ({pin}). If yes → skip. Soft only; does not block versioning."
            )
            compare = "Old ≈ New is expected. This is not a regression between versions."
        else:
            why = f"Expected span group {gid!r} not found under that id."
            you_do = "In NEW, search for the table/span content on this page. If content is gone → real issue."

    # --- section headers ---
    elif code == "missing_section_header":
        header = str(issue.get("header") or "")
        variants = _header_variants(header)
        hit_heading = None
        hit_tree = None
        rng = _page_body_range(new_lines, page) if page else None
        if rng:
            for i in range(rng[0], rng[1]):
                line = new_lines[i]
                for v in variants:
                    if v.lower() in line.lower():
                        if re.match(r"^#{1,4}\s+", line.strip()):
                            hit_heading = (i + 1, line.strip())
                            break
                        if hit_tree is None:
                            hit_tree = (i + 1, line.strip())
                if hit_heading:
                    break
        if hit_heading:
            verdict, label = "skip", "SKIP — near-match header"
            found_as = f"L{hit_heading[0]}: {hit_heading[1][:80]}"
            why = (
                f"Inventory wants exact string {header!r}. Deliverable has a heading "
                f"that matches a normal variant (punctuation/spacing)."
            )
            you_do = (
                "Glance at the gold-highlighted line in NEW. If it is clearly the same section "
                "title → skip. Soft false positive on exact string match."
            )
            compare = "Old ≈ New is fine. You are not hunting a diff."
        elif hit_tree:
            verdict, label = "review", "REVIEW — in figure tree only"
            found_as = f"L{hit_tree[0]}: {hit_tree[1][:80]}"
            why = (
                f"Phrase for {header!r} appears inside a diagram/tree line, not as a ### section header."
            )
            you_do = (
                "Look at NEW: is a full ### section header required, or is the figure tree enough? "
                "If tree is intentional (Figures 12/13 style) → skip after one look. "
                "If you want a real ### heading in the MD → real content gap."
            )
            compare = "Diff rarely matters; judge product intent on NEW."
        else:
            verdict, label = "check", "CHECK — header not found"
            why = f"No near-match for {header!r} on page {page}."
            you_do = "Scroll NEW on this page for the section. If truly absent → content issue."

    # --- page 47 order ---
    elif code == "page_47_section_order":
        has_fig = "figure_11" in body_l or "figure 11" in body_l
        has_h = bool(
            re.search(r"###\s*3\.1\.?\s*RECEPTION", body, re.I)
            or re.search(r"3\.1\.?\s*RECEPTION", body, re.I)
        )
        if has_fig and has_h:
            verdict, label = "skip", "SKIP — present under variant"
            found_as = "figure_11 + ### 3.1 RECEPTION (validator wants '3.1. RECEPTION' with period)"
            why = (
                "Gate text is picky about exact '3.1. RECEPTION'. "
                "Figure 11 and a 3.1 RECEPTION heading are both present."
            )
            you_do = (
                "In NEW: confirm Figure 11 block, then ### 3.1 RECEPTION under/near it. "
                "If both there → skip. Soft string-match false positive."
            )
            compare = "Old ≈ New expected."
        elif has_fig and not has_h:
            verdict, label = "check", "CHECK — figure without 3.1 header"
            why = "Figure 11 found but 3.1 RECEPTION heading not found."
            you_do = "Confirm whether 3.1 section header is missing after Figure 11."
        else:
            verdict, label = "check", "CHECK — figure/header missing"
            why = f"has_figure={has_fig}, header-like={has_h}."
            you_do = "Inspect p.47 in NEW for Figure 11 and 3.1 RECEPTION."

    # --- missing_page_artifact / missing_artifact ---
    elif code in ("missing_page_artifact", "missing_artifact"):
        aid = str(issue.get("artifact_id") or issue.get("id") or issue.get("expected_id") or "")
        pin = _KNOWN_PIN_ON_PAGE.get(page or -1, "")
        if pin and pin in full and (
            aid.startswith("table_table_") or aid != pin
        ):
            verdict, label = "skip", "SKIP — layout pin present"
            found_as = pin
            why = f"Inventory wants {aid!r}; deliverable has layout pin {pin!r}."
            you_do = f"Confirm {pin} on this page in NEW → skip."
            compare = "Old ≈ New expected."
        elif issue.get("actual_id") and issue["actual_id"] in full:
            verdict, label = "skip", "SKIP — renamed id"
            found_as = str(issue["actual_id"])
            why = f"Expected {aid!r}; content under {found_as!r}."
            you_do = "Confirm actual_id block in NEW → skip."
        else:
            why = f"Artifact {aid!r} not found under that id."
            you_do = "Search NEW for the content; if gone → real issue."

    else:
        why = "Soft validator note — not a hard regression failure."
        you_do = "Read detail; if unclear, treat as review once."

    return {
        "verdict": verdict,  # skip | review | check | info
        "verdict_label": label,
        "why": why,
        "you_do": you_do,
        "compare_hint": compare,
        "found_as": found_as,
    }


def _annotate_issue(issue: dict, new_lines: list[str] | None = None) -> dict:
    out = dict(issue)
    code = str(out.get("code") or "")
    lines = new_lines or []
    if not lines and CFG.get("new"):
        try:
            lines = _read_lines(Path(CFG["new"]))
        except OSError:
            lines = []

    cls = _classify_soft_issue(out, lines) if lines else {
        "verdict": "check",
        "verdict_label": "NEEDS CHECK",
        "why": "Could not load NEW markdown for classification.",
        "you_do": "Open the report issue and inspect output MD manually.",
        "compare_hint": "",
        "found_as": None,
    }
    out.update(cls)

    out["guidance"] = out["you_do"]  # primary instruction line in UI
    out["look_for"] = _issue_needles(out)
    out["short_title"] = _human_title(out)
    return out
# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Soft issue inspector</title>
<style>
  :root {
    --bg: #0f1419; --panel: #1a2332; --border: #2d3a4d; --text: #e7ecf3;
    --muted: #8b9bb4; --accent: #3d8bfd; --del: #3d1f1f; --del-border: #c45c5c;
    --ins: #1a3324; --ins-border: #3d9a6a; --eq-hover: #243044; --focus: #c9a227;
    --hit: #3a2f10; --hit-border: #e0b84a;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; overflow: hidden; }
  body {
    font-family: "Segoe UI", system-ui, sans-serif;
    background: var(--bg); color: var(--text);
    display: flex; flex-direction: column;
  }
  header {
    flex: 0 0 auto; display: flex; flex-wrap: wrap; gap: 12px; align-items: center;
    padding: 10px 16px; background: var(--panel); border-bottom: 1px solid var(--border);
  }
  header h1 { font-size: 1rem; margin: 0; font-weight: 600; }
  .meta { color: var(--muted); font-size: 0.8rem; }
  .nav { display: flex; gap: 8px; align-items: center; margin-left: auto; }
  button {
    background: var(--accent); color: #fff; border: none; border-radius: 6px;
    padding: 10px 18px; font-size: 0.95rem; font-weight: 600; cursor: pointer;
  }
  button:hover { filter: brightness(1.1); }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
  button.secondary { background: #3a4a63; }
  .counter { font-variant-numeric: tabular-nums; font-weight: 700; min-width: 4.5rem; text-align: center; }
  .issue-bar {
    flex: 0 0 7.5rem; height: 7.5rem; padding: 8px 16px;
    background: #15202b; border-bottom: 1px solid var(--border);
    overflow: hidden; display: flex; flex-direction: column; justify-content: center; gap: 2px;
  }
  .issue-bar .primary { display: flex; align-items: baseline; gap: 8px; min-width: 0; }
  .issue-bar .code {
    flex: 0 0 auto; display: inline-block; background: #2a3f5f; color: #9ecbff;
    padding: 2px 8px; border-radius: 4px; font-family: ui-monospace, Consolas, monospace; font-size: 0.85rem;
  }
  .badge {
    flex: 0 0 auto; font-size: 0.72rem; font-weight: 700; padding: 3px 8px; border-radius: 4px;
    letter-spacing: 0.02em;
  }
  .badge.skip { background: #1a3d2a; color: #7ddea8; }
  .badge.review { background: #3d3518; color: #e6c86a; }
  .badge.check { background: #3d1f1f; color: #f0a0a0; }
  .badge.info { background: #1a2a40; color: #9ecbff; }
  .filter-bar {
    flex: 0 0 auto; padding: 6px 16px; background: #121a24; border-bottom: 1px solid var(--border);
    display: flex; gap: 12px; align-items: center; font-size: 0.78rem; color: var(--muted);
  }
  .filter-bar label { cursor: pointer; user-select: none; }
  .filter-bar input { margin-right: 4px; }
  .howto {
    flex: 0 0 auto; padding: 6px 16px; background: #0d1520; border-bottom: 1px solid var(--border);
    font-size: 0.75rem; color: #a8b8cc; line-height: 1.35;
  }
  .issue-bar .detail {
    flex: 1 1 auto; min-width: 0; color: var(--text); font-size: 0.9rem;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .issue-bar .guide, .issue-bar .focus {
    color: var(--muted); font-size: 0.72rem;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .issue-bar .guide { color: #b8c5d9; }
  main { flex: 1 1 auto; display: flex; min-height: 0; overflow: hidden; }
  aside {
    flex: 0 0 280px; width: 280px; overflow-x: hidden; overflow-y: auto;
    border-right: 1px solid var(--border); background: var(--panel); padding: 8px 0;
    align-self: stretch;
  }
  aside .aside-head {
    padding: 4px 12px 8px; font-size: 0.72rem; color: var(--muted); border-bottom: 1px solid var(--border);
    margin-bottom: 4px;
  }
  aside button.item {
    display: block; width: 100%; text-align: left; background: transparent;
    color: var(--text); font-weight: 400; padding: 8px 12px; border-radius: 0;
    border-left: 3px solid transparent; font-size: 0.78rem;
  }
  aside button.item:hover { background: var(--eq-hover); }
  aside button.item.active { border-left-color: var(--accent); background: #1e2d44; }
  aside .item .i-code { color: #9ecbff; font-family: ui-monospace, Consolas, monospace; }
  aside .item .i-sub { color: var(--muted); font-size: 0.72rem; }
  .panes {
    flex: 1 1 auto; display: grid; grid-template-columns: 1fr 1fr;
    min-width: 0; min-height: 0; overflow: hidden;
  }
  .pane {
    display: flex; flex-direction: column; min-width: 0; min-height: 0;
    overflow: hidden; border-right: 1px solid var(--border);
  }
  .pane:last-child { border-right: none; }
  .pane-head {
    flex: 0 0 auto; padding: 6px 12px; font-size: 0.8rem; color: var(--muted);
    background: #121a24; border-bottom: 1px solid var(--border);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .pane-head strong { color: var(--text); }
  .codeview {
    flex: 1 1 auto; min-height: 0; overflow: auto;
    font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
    font-size: 12.5px; line-height: 1.45; tab-size: 2;
  }
  .row { display: flex; min-height: 1.45em; border-left: 3px solid transparent; }
  .row.eq:hover { background: var(--eq-hover); }
  .row.del { background: var(--del); border-left-color: var(--del-border); }
  .row.ins { background: var(--ins); border-left-color: var(--ins-border); }
  .row.hit { background: var(--hit); border-left-color: var(--hit-border); }
  .row.focus-line { outline: 1px solid var(--focus); outline-offset: -1px; }
  .ln {
    flex: 0 0 3.2rem; text-align: right; padding: 0 8px 0 4px;
    color: var(--muted); user-select: none; background: rgba(0,0,0,0.15);
  }
  .tx { flex: 1; white-space: pre-wrap; word-break: break-word; padding-right: 8px; }
  .empty { color: var(--muted); padding: 24px; }
  .scan {
    flex: 0 0 auto; max-height: 7rem; overflow: auto; padding: 6px 12px;
    font-size: 0.72rem; color: var(--muted); background: #101820;
    border-top: 1px solid var(--border);
  }
  .scan .ok { color: #6dcea0; }
  .scan .no { color: #d08080; }
  .scan code { color: #c5d4e8; font-family: ui-monospace, Consolas, monospace; }
  @media (max-width: 900px) {
    aside { display: none; }
    .panes { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>
<header>
  <h1>Soft issue inspector</h1>
  <span class="meta" id="paths"></span>
  <div class="nav">
    <button type="button" class="secondary" id="btnReload" title="Re-read regression_report.json">Reload report</button>
    <button type="button" class="secondary" id="btnPrev">← Previous</button>
    <span class="counter" id="counter">– / –</span>
    <button type="button" id="btnNext">Next →</button>
  </div>
</header>
<div class="howto" id="howto">
  <b>How to use:</b> Soft ≠ “broken in the MD.” Many are inventory string mismatches.
  <span class="badge skip">SKIP</span> = content OK, old/new may match — glance once or skip.
  <span class="badge review">REVIEW</span> = one look, decide product intent.
  <span class="badge check">CHECK</span> = expected signal missing — inspect NEW carefully.
  Diff panes help only when content changed; identical panes are normal for SKIP items.
</div>
<div class="filter-bar">
  <label><input type="checkbox" id="hideSkip" checked /> Hide SKIP (show only REVIEW + CHECK)</label>
  <span id="filterCounts"></span>
</div>
<div class="issue-bar">
  <div class="primary">
    <span class="badge" id="iverdict">—</span>
    <span class="code" id="icode">—</span>
    <span class="detail" id="idetail" title=""></span>
  </div>
  <div class="guide" id="iwhy" title=""></div>
  <div class="guide" id="iguide" title=""></div>
  <div class="focus" id="ifocus" title=""></div>
</div>
<main>
  <aside>
    <div class="aside-head" id="asideHead">Soft issues (do not block versioning)</div>
    <div id="sidebar"></div>
  </aside>
  <div class="panes">
    <section class="pane">
      <div class="pane-head"><strong>OLD / baseline</strong> · <span id="oldLabel"></span></div>
      <div class="codeview" id="oldView"></div>
      <div class="scan" id="oldScan"></div>
    </section>
    <section class="pane">
      <div class="pane-head"><strong>NEW / current</strong> · <span id="newLabel"></span></div>
      <div class="codeview" id="newView"></div>
      <div class="scan" id="newScan"></div>
    </section>
  </div>
</main>
<script>
let allIssues = [];
let visible = [];  // indices into allIssues
let vpos = 0;      // position in visible

function esc(s) {
  return String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

function hideSkipOn() {
  return document.getElementById("hideSkip").checked;
}

function rebuildVisible() {
  visible = [];
  allIssues.forEach((iss, i) => {
    if (hideSkipOn() && iss.verdict === "skip") return;
    visible.push(i);
  });
  if (vpos >= visible.length) vpos = Math.max(0, visible.length - 1);
  const skipN = allIssues.filter(x => x.verdict === "skip").length;
  const revN = allIssues.filter(x => x.verdict === "review").length;
  const chkN = allIssues.filter(x => x.verdict === "check").length;
  document.getElementById("filterCounts").textContent =
    "total " + allIssues.length + " · skip " + skipN + " · review " + revN + " · check " + chkN +
    " · showing " + visible.length;
}

function renderRows(viewEl, rows, focusN) {
  if (!rows || !rows.length) {
    viewEl.innerHTML = '<div class="empty">No lines in window</div>';
    return;
  }
  const frag = document.createDocumentFragment();
  let focusEl = null;
  for (const r of rows) {
    const div = document.createElement("div");
    let cls = "row " + (r.cls || "eq");
    if (r.hit) cls += " hit";
    div.className = cls;
    if (focusN && r.n === focusN) {
      div.classList.add("focus-line");
      focusEl = div;
    }
    div.innerHTML = '<span class="ln">' + r.n + '</span><span class="tx">' + esc(r.text) + '</span>';
    frag.appendChild(div);
  }
  viewEl.innerHTML = "";
  viewEl.appendChild(frag);
  if (focusEl) {
    const top = focusEl.offsetTop - (viewEl.clientHeight / 2) + (focusEl.offsetHeight / 2);
    viewEl.scrollTop = Math.max(0, top);
  } else {
    viewEl.scrollTop = 0;
  }
}

function renderScan(el, scan, sideLabel) {
  if (!el) return;
  if (!scan) {
    el.innerHTML = '<div class="empty">No scan data</div>';
    return;
  }
  const hits = (scan.needle_hits || []).map(h => {
    const mark = h.found ? '✓' : '✗';
    const cls = h.found ? 'ok' : 'no';
    const role = h.role === 'primary' ? ' <b>(primary)</b>' : '';
    return '<span class="' + cls + '">' + mark + ' <code>' + esc(String(h.needle).slice(0, 48)) +
      '</code>' + role + '</span>';
  }).join(' · ');
  const heads = (scan.headings_in_window || []).map(h =>
    'L' + h.line + ' ' + esc(h.text)
  ).join('<br>');
  const trees = (scan.tree_hits || []).map(h =>
    'L' + h.line + ' ' + esc(h.text)
  ).join('<br>');
  el.innerHTML =
    '<div><b>' + esc(sideLabel || 'Scan') + '</b> · issue #' +
    (scan.issue_index != null ? (scan.issue_index + 1) : '?') +
    ' · focus L' + (scan.focus_line || '?') +
    ' · window L' + (scan.window_line_start || '?') + '–' + (scan.window_line_end || '?') +
    '</div>' +
    '<div style="margin-top:3px"><b>Look-for</b>: ' + (hits || '—') + '</div>' +
    (trees ? '<div style="margin-top:3px"><b>Tree/phrase hits</b><br>' + trees + '</div>' : '') +
    (heads ? '<div style="margin-top:3px"><b>### headings</b><br>' + heads + '</div>' : '');
}

function renderSidebar() {
  const side = document.getElementById("sidebar");
  side.innerHTML = "";
  visible.forEach((realIdx, vi) => {
    const iss = allIssues[realIdx];
    const b = document.createElement("button");
    b.type = "button";
    b.className = "item" + (vi === vpos ? " active" : "");
    const loc = "p." + (iss.page != null ? iss.page : "?") + " L" + (iss.line != null ? iss.line : "?");
    const title = iss.short_title || iss.code;
    const v = iss.verdict || "check";
    b.innerHTML =
      '<span class="badge ' + v + '">' + esc(iss.verdict_label || v) + '</span> ' +
      '<span class="i-code">' + (realIdx+1) + ". " + esc(title) + '</span><br>' +
      '<span class="i-sub">' + esc(iss.code) + " · " + loc + '</span><br>' +
      esc(String(iss.you_do || iss.detail || "").slice(0, 90));
    b.onclick = () => { vpos = vi; loadIssue(); };
    side.appendChild(b);
  });
}

async function loadIssue() {
  if (!visible.length) {
    document.getElementById("idetail").textContent =
      hideSkipOn()
        ? "All remaining soft issues are SKIP (inventory/string near-matches). Uncheck Hide SKIP to browse them."
        : "No soft issues in report.";
    document.getElementById("iverdict").textContent = "—";
    document.getElementById("iverdict").className = "badge";
    document.getElementById("oldView").innerHTML = '<div class="empty">Nothing that needs your review</div>';
    document.getElementById("newView").innerHTML = '<div class="empty">Nothing that needs your review</div>';
    document.getElementById("iwhy").textContent = "";
    document.getElementById("iguide").textContent = "";
    document.getElementById("ifocus").textContent = "";
    document.getElementById("counter").textContent = "0 / 0";
    renderSidebar();
    return;
  }
  vpos = Math.max(0, Math.min(vpos, visible.length - 1));
  const realIdx = visible[vpos];
  document.getElementById("counter").textContent = (vpos + 1) + " / " + visible.length +
    "  (#" + (realIdx + 1) + " of " + allIssues.length + ")";
  document.getElementById("btnPrev").disabled = vpos <= 0;
  document.getElementById("btnNext").disabled = vpos >= visible.length - 1;
  renderSidebar();

  const res = await fetch("/api/issue/" + realIdx);
  const data = await res.json();
  if (data.error) {
    document.getElementById("idetail").textContent = data.error;
    return;
  }
  const iss = data.issue;
  const vb = document.getElementById("iverdict");
  vb.textContent = iss.verdict_label || iss.verdict || "—";
  vb.className = "badge " + (iss.verdict || "check");
  document.getElementById("icode").textContent = iss.code;
  const det = document.getElementById("idetail");
  det.textContent = iss.detail || "";
  det.title = iss.detail || "";
  const why = document.getElementById("iwhy");
  why.textContent = (iss.why || "") + (iss.found_as ? "  → Found as: " + iss.found_as : "");
  why.title = why.textContent;
  const guide = document.getElementById("iguide");
  guide.textContent = "YOU DO: " + (iss.you_do || iss.guidance || "");
  guide.title = guide.textContent;

  const focusText =
    (iss.compare_hint || "") +
    " · NEW L" + data.new.focus.line1 + " · OLD L" + data.old.focus.line1 +
    (iss.page != null ? " · page " + iss.page : "");
  const foc = document.getElementById("ifocus");
  foc.textContent = focusText;
  foc.title = focusText;

  // Clear then redraw so bottom panels never stick on a previous issue
  const oldScanEl = document.getElementById("oldScan");
  const newScanEl = document.getElementById("newScan");
  oldScanEl.innerHTML = "Loading…";
  newScanEl.innerHTML = "Loading…";
  renderRows(document.getElementById("oldView"), data.old.rows, data.old.focus.line1);
  renderRows(document.getElementById("newView"), data.new.rows, data.new.focus.line1);
  renderScan(oldScanEl, data.old.scan, "OLD");
  renderScan(newScanEl, data.new.scan, "NEW");
}

async function loadMetaAndIssues() {
  const meta = await (await fetch("/api/meta")).json();
  document.getElementById("paths").textContent =
    meta.soft_count + " soft · hard " + meta.hard_count +
    (meta.passed ? " · regression PASS" : " · regression FAIL") +
    " · " + meta.job_id;
  document.getElementById("asideHead").textContent =
    "Soft only — hard gates already protect versions";
  document.getElementById("oldLabel").textContent = meta.old_path;
  document.getElementById("newLabel").textContent = meta.new_path;
  allIssues = (await (await fetch("/api/issues")).json()).soft_issues || [];
  rebuildVisible();
}

async function init() {
  await loadMetaAndIssues();
  document.getElementById("hideSkip").onchange = () => {
    rebuildVisible();
    loadIssue();
  };
  document.getElementById("btnPrev").onclick = () => { vpos--; loadIssue(); };
  document.getElementById("btnNext").onclick = () => { vpos++; loadIssue(); };
  document.getElementById("btnReload").onclick = async () => {
    await loadMetaAndIssues();
    await loadIssue();
  };
  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight" || e.key === "n") { vpos++; loadIssue(); }
    if (e.key === "ArrowLeft" || e.key === "p") { vpos--; loadIssue(); }
  });
  await loadIssue();
}
init();
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/meta")
def api_meta():
    st = load_state()
    return jsonify(
        {
            "job_id": st["report"].get("job_id"),
            "passed": st["report"].get("passed"),
            "soft_count": len(st["soft"]),
            "hard_count": len(st["hard"]),
            "old_path": st["old_path"],
            "new_path": st["new_path"],
            "report_path": st["report_path"],
            "old_lines": len(st["old_lines"]),
            "new_lines": len(st["new_lines"]),
            "stats": st["report"].get("stats") or {},
        }
    )


@app.route("/api/issues")
def api_issues():
    st = load_state()
    soft = [_annotate_issue(x, st["new_lines"]) for x in st["soft"]]
    return jsonify({"soft_issues": soft, "hard_issues": st["hard"]})


@app.route("/api/issue/<int:i>")
def api_issue(i: int):
    st = load_state()
    soft = st["soft"]
    if i < 0 or i >= len(soft):
        return jsonify({"error": f"index {i} out of range 0..{len(soft)-1}"}), 404
    issue = _annotate_issue(soft[i], st["new_lines"])
    # Preserve group_id from raw validator when missing in report
    if issue.get("code") == "missing_span_artifact" and not issue.get("group_id"):
        issue["group_id"] = "scale_what_is_addressed_in_this_publication"

    old_focus = resolve_focus(issue, st["old_lines"], side="old")
    new_focus = resolve_focus(issue, st["new_lines"], side="new")
    phrase = str(new_focus.get("phrase") or issue.get("header") or "")
    phrase = _primary_phrase(phrase) if phrase and phrase[0].isdigit() else phrase
    if issue.get("header"):
        phrase = _primary_phrase(str(issue["header"]))
    n_needles = list(new_focus.get("needles") or _issue_needles(issue))
    o_needles = list(old_focus.get("needles") or n_needles)

    old_win, _, _ = window_lines(st["old_lines"], old_focus["line0"])
    new_win, _, _ = window_lines(st["new_lines"], new_focus["line0"])
    old_rows, new_rows = aligned_diff(old_win, new_win)
    old_rows = _mark_rows(
        old_rows, phrase=phrase, needles=o_needles, focus_line1=old_focus["line1"]
    )
    new_rows = _mark_rows(
        new_rows, phrase=phrase, needles=n_needles, focus_line1=new_focus["line1"]
    )

    old_scan = _scan_from_rows(
        old_rows,
        phrase=phrase,
        needles=o_needles,
        focus_line1=old_focus["line1"],
        issue_index=i,
    )
    new_scan = _scan_from_rows(
        new_rows,
        phrase=phrase,
        needles=n_needles,
        focus_line1=new_focus["line1"],
        issue_index=i,
    )

    return jsonify(
        {
            "index": i,
            "total": len(soft),
            "issue": issue,
            "old": {
                "focus": old_focus,
                "rows": old_rows,
                "path": st["old_path"],
                "scan": old_scan,
            },
            "new": {
                "focus": new_focus,
                "rows": new_rows,
                "path": st["new_path"],
                "scan": new_scan,
            },
        }
    )

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Soft-issue side-by-side markdown viewer")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--old", type=Path, default=None, help="Baseline / old markdown")
    parser.add_argument("--new", type=Path, default=None, help="Current / new markdown")
    args = parser.parse_args(argv)

    old = args.old or _default_old()
    new = args.new or DEFAULT_NEW

    for label, p in ("report", args.report), ("old", old), ("new", new):
        if not Path(p).is_file():
            print(f"ERROR: {label} file not found: {p}", file=sys.stderr)
            return 1

    CFG["report"] = str(args.report.resolve())
    CFG["old"] = str(Path(old).resolve())
    CFG["new"] = str(Path(new).resolve())

    print("Soft issue inspector (remaining soft issues)")
    print(f"  report: {CFG['report']}")
    print(f"  old:    {CFG['old']}")
    print(f"  new:    {CFG['new']}")
    # preview count
    try:
        rep = json.loads(Path(CFG["report"]).read_text(encoding="utf-8"))
        print(f"  soft:   {len(rep.get('soft_issues') or [])}  hard: {len(rep.get('issues') or [])}")
    except OSError:
        pass
    url = f"http://{args.host}:{args.port}/"
    print(f"\nOpen: {url}\n")
    app.run(host=args.host, port=args.port, debug=False, use_reloader=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
