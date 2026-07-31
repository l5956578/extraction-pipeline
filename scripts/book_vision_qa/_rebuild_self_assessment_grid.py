#!/usr/bin/env python3
"""Rebuild Appendix 2 self-assessment grid (pp.177-181) from PDF line geometry.

Emits **page-local** tables for each of 177–181 (book-page fidelity), not a single
collapsed multipage dump on p.177 only.
"""

from __future__ import annotations

import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "input/cefr-companion-2020/source.pdf"
MD = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"

# PDF geometry: level bands are horizontal (C2 top → A1 bottom);
# activity columns increase in x left→right.
LEVELS = [
    ("C2", 70, 166),
    ("C1", 166, 270),
    ("B2", 270, 372),
    ("B1", 372, 475),
    ("A2", 475, 577),
    ("A1", 577, 690),
]

PAGE_GEOM = {
    176: {  # p177 Reception
        "section": "Reception",
        "levels": LEVELS,
        "cols": [
            ("Oral comprehension", 175, 355),
            ("Reading comprehension", 355, 560),
        ],
        "chrome": "*Self-assessment grid (expanded with online interaction and mediation) ▶ Page **177***",
    },
    177: {  # p178 Production
        "section": "Production",
        "levels": LEVELS,
        "cols": [
            ("Oral production", 100, 305),
            ("Written production", 305, 560),
        ],
        "chrome": "*Page **178** ▶ **CEFR – Companion volume***",
    },
    178: {  # p179 Interaction
        "section": "Interaction",
        "levels": LEVELS,
        "cols": [
            ("Oral interaction", 100, 305),
            ("Written and online interaction", 305, 560),
        ],
        "chrome": "*Self-assessment grid (expanded with online interaction and mediation) ▶ Page **179***",
    },
    179: {  # p180 Mediation text/concepts
        "section": "Mediation",
        "levels": LEVELS,
        "cols": [
            ("Mediating a text", 100, 305),
            ("Mediating concepts", 305, 560),
        ],
        "chrome": "*Page **180** ▶ **CEFR – Companion volume***",
    },
    180: {  # p181 Mediating communication
        "section": "Mediation",
        "levels": LEVELS,
        "cols": [
            ("Mediating communication", 100, 540),
        ],
        "chrome": "*Self-assessment grid (expanded with online interaction and mediation) ▶ Page **181***",
    },
}

ARTIFACT_ID = (
    "table_self_assessment_grid_expanded_with_online_interaction_and_mediation"
)


def page_lines(page: fitz.Page) -> list[tuple[float, float, float, float, str]]:
    out = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            text = "".join(s["text"] for s in line["spans"]).strip()
            if not text:
                continue
            x0, y0, x1, y1 = line["bbox"]
            out.append((y0, x0, y1, x1, text))
    return out


def cell_text(
    lines: list[tuple[float, float, float, float, str]],
    y0: float,
    y1: float,
    x0: float,
    x1: float,
) -> str:
    selected = []
    for ly0, lx0, ly1, lx1, text in lines:
        cy = (ly0 + ly1) / 2
        cx = (lx0 + lx1) / 2
        if y0 <= cy <= y1 and x0 <= cx <= x1:
            selected.append((lx0, ly0, text))
    selected.sort(key=lambda t: (round(t[0], 0), t[1]))
    cleaned = []
    for _x, _y, t in selected:
        if re.fullmatch(r"A1|A2|B1|B2|C1|C2", t):
            continue
        if t in {
            "Reception",
            "Production",
            "Interaction",
            "Mediation",
            "Oral",
            "Reading",
            "Written",
            "comprehension",
            "production",
            "interaction",
            "online",
            "and",
            "a text",
            "concepts",
            "communication",
            "Mediating",
        }:
            continue
        cleaned.append(t)
    text = " ".join(cleaned)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_page_body(doc: fitz.Document, pidx: int, geom: dict, *, lead: bool) -> str:
    lines = page_lines(doc[pidx])
    section = geom["section"]
    col_names = [c[0] for c in geom["cols"]]
    page_num = pidx + 1
    parts: list[str] = []
    if lead:
        parts.extend(
            [
                f"<!-- el:start type=artifact id={ARTIFACT_ID} page=177 -->",
                f"<!-- db:id={ARTIFACT_ID} type=section_block product_tier=base pages=177-181 -->",
                f"### Self-Assessment Grid (Expanded with Online Interaction and Mediation) | {ARTIFACT_ID}",
                "",
            ]
        )
    else:
        parts.append(
            f"<!-- book-qa page-slice of {ARTIFACT_ID} page={page_num} -->"
        )
    parts.append(f"## {section}")
    parts.append("")
    parts.append("| Level | " + " | ".join(col_names) + " |")
    parts.append("| --- | " + " | ".join(["---"] * len(col_names)) + " |")
    for level, y0, y1 in reversed(geom["levels"]):
        cells = []
        for _n, x0, x1 in geom["cols"]:
            cells.append(cell_text(lines, y0, y1, x0, x1).replace("|", "\\|"))
        parts.append("| " + level + " | " + " | ".join(cells) + " |")
    parts.append("")
    if lead:
        # Keep el:end only after last page would orphan — end on final page instead.
        pass
    if page_num == 181:
        parts.append(f"<!-- el:end id={ARTIFACT_ID} -->")
    parts.append(geom["chrome"])
    return "\n".join(parts)


def replace_page_region(md: str, page: int, new_body: str) -> str:
    marker = f"<!-- page:{page} -->"
    idx = md.find(marker)
    if idx < 0:
        raise SystemExit(f"marker missing page {page}")
    prev = list(re.finditer(r"<!-- page:\d+ -->", md[:idx]))
    start = prev[-1].end() if prev else 0
    return md[:start] + "\n" + new_body.strip() + "\n\n" + md[idx:]


def main() -> None:
    doc = fitz.open(PDF)
    md = MD.read_text(encoding="utf-8")
    for pidx, geom in PAGE_GEOM.items():
        page_num = pidx + 1
        body = build_page_body(doc, pidx, geom, lead=(page_num == 177))
        for sample in (
            "I can",
            "I have no difficulty",
        ):
            if sample.lower() not in body.lower() and page_num == 177:
                print("WARN missing", sample, "on", page_num)
        print(
            f"p{page_num} len={len(body)} "
            f"section={geom['section']} "
            f"has_I_can={'I can' in body}"
        )
        md = replace_page_region(md, page_num, body)
    MD.write_text(md, encoding="utf-8")
    # sanity
    md2 = MD.read_text(encoding="utf-8")
    for s in [
        "I can recognise familiar",
        "I have no difficulty",
        "I can present a clear",
        "I can mediate effectively",
        "noitpircsed",
    ]:
        print(s, "->", s in md2 or s.lower() in md2.lower())
    doc.close()


if __name__ == "__main__":
    main()
