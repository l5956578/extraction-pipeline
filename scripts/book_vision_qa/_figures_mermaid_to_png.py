#!/usr/bin/env python3
"""Replace mermaid diagrams for Figures 18–20 with cropped PDF PNGs."""

from __future__ import annotations

import re
from pathlib import Path

MD = Path(__file__).resolve().parents[2] / "output/cefr-companion-2020/CEFR_Companion_Volume.md"

FIGS = [
    (18, "figure_18_young_learner_project_design.png"),
    (19, "figure_19_multimethod_research_design.png"),
    (20, "figure_20_sign_language_project_phases.png"),
]


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    for num, asset in FIGS:
        pat = re.compile(
            rf"(### Figure {num}[^\n]*\n)([\s\S]*?)(```mermaid[\s\S]*?```)",
            re.M,
        )
        m = pat.search(md)
        if not m:
            print(f"fig {num}: mermaid not found")
            continue
        title = m.group(1).strip().lstrip("#").strip()
        # drop trailing | id if present in heading line for alt text
        alt = re.sub(r"\s*\|\s*figure_.*$", "", title).strip()
        replacement = (
            m.group(1)
            + "\n"
            + f"![{alt}](assets/figures/{asset})\n\n"
            + f"<!-- figure render: png assets/figures/{asset} "
            f"(user request: replace mermaid; PDF-cropped) -->\n"
        )
        md = md[: m.start()] + replacement + md[m.end() :]
        print(f"fig {num}: png {asset}")
    print("mermaid remaining", len(re.findall(r"```mermaid", md)))
    MD.write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
