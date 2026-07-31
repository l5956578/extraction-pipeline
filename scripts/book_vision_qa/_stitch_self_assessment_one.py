#!/usr/bin/env python3
"""Put full self-assessment grid on p.177 only; mid pages keep chrome only."""

from __future__ import annotations

import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "input/cefr-companion-2020/source.pdf"
MD = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"

# Import geometry from rebuild module via exec
import importlib.util

spec = importlib.util.spec_from_file_location(
    "rb", ROOT / "scripts/book_vision_qa/_rebuild_self_assessment_grid.py"
)
rb = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(rb)

ARTIFACT = (
    "table_self_assessment_grid_expanded_with_online_interaction_and_mediation"
)


def replace_page(md: str, page: int, new_body: str) -> str:
    marker = f"<!-- page:{page} -->"
    idx = md.find(marker)
    prev = list(re.finditer(r"<!-- page:\d+ -->", md[:idx]))
    start = prev[-1].end() if prev else 0
    return md[:start] + "\n" + new_body.strip() + "\n\n" + md[idx:]


def main() -> None:
    doc = fitz.open(PDF)
    parts = [
        f"<!-- el:start type=artifact id={ARTIFACT} page=177 -->",
        f"<!-- db:id={ARTIFACT} type=section_block product_tier=base pages=177-181 -->",
        f"### Self-Assessment Grid (Expanded with Online Interaction and Mediation) | {ARTIFACT}",
        "",
    ]
    for pidx, geom in rb.PAGE_GEOM.items():
        lines = rb.page_lines(doc[pidx])
        section = geom["section"]
        col_names = [c[0] for c in geom["cols"]]
        parts.append(f"## {section}")
        parts.append("")
        parts.append("| Level | " + " | ".join(col_names) + " |")
        parts.append("| --- | " + " | ".join(["---"] * len(col_names)) + " |")
        for level, y0, y1 in reversed(geom["levels"]):
            cells = []
            for _n, x0, x1 in geom["cols"]:
                cells.append(rb.cell_text(lines, y0, y1, x0, x1).replace("|", "\\|"))
            parts.append("| " + level + " | " + " | ".join(cells) + " |")
        parts.append("")
    parts.append(f"<!-- el:end id={ARTIFACT} -->")
    parts.append("")
    parts.append(
        "*Self-assessment grid (expanded with online interaction and mediation) ▶ Page **177***"
    )
    full = "\n".join(parts)

    md = MD.read_text(encoding="utf-8")
    md = replace_page(md, 177, full)
    for p, chrome in {
        178: "*Page **178** ▶ **CEFR – Companion volume***",
        179: "*Self-assessment grid (expanded with online interaction and mediation) ▶ Page **179***",
        180: "*Page **180** ▶ **CEFR – Companion volume***",
        181: "*Self-assessment grid (expanded with online interaction and mediation) ▶ Page **181***",
    }.items():
        body = (
            f"<!-- table-continuity: full multipage self-assessment grid lives on page 177 "
            f"({ARTIFACT}); page-slice removed for single db:id grep -->\n\n"
            f"{chrome}\n"
        )
        md = replace_page(md, p, body)
    MD.write_text(md, encoding="utf-8")
    print("grid on 177", "I can recognise familiar" in full, "len", len(full))
    print("mediate", "I can mediate effectively" in full)


if __name__ == "__main__":
    main()
