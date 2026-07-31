#!/usr/bin/env python3
"""Clean dual-emit figure soup on p.244 / p.249."""

from __future__ import annotations

import re
from pathlib import Path

MD = Path(__file__).resolve().parents[2] / "output/cefr-companion-2020/CEFR_Companion_Volume.md"


def page_body(md: str, n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return ""


def replace_page(md: str, page: int, new_body: str) -> str:
    marker = f"<!-- page:{page} -->"
    idx = md.find(marker)
    prev = list(re.finditer(r"<!-- page:\d+ -->", md[:idx]))
    start = prev[-1].end() if prev else 0
    return md[:start] + "\n" + new_body.strip() + "\n\n" + md[idx:]


def fix_p244(body: str) -> str:
    end_tag = "<!-- el:end id=figure_18_young_learner_project_design -->"
    # Find end of mermaid fence
    fence_end = body.find("```\n", body.find("```mermaid"))
    if fence_end < 0:
        fence_end = body.find("```", body.find("```mermaid") + 3)
        if fence_end >= 0:
            fence_end = fence_end + 3
    else:
        fence_end = fence_end + 4
    end_pos = body.find(end_tag)
    if fence_end > 0 and end_pos > fence_end:
        # keep prose before fence + mermaid + end tag + footnote after
        after = body[end_pos:]
        body = body[:fence_end].rstrip() + "\n" + after
    # safety: drop residual Initial collation dump if any
    if "**Initial collation" in body:
        body = re.sub(
            r"\n\*\*Initial collation[\s\S]*?(?=<!-- el:end id=figure_18)",
            "\n",
            body,
            count=1,
        )
    return body


P249 = """\
<!-- el:start type=figure_page id=figure_19_multimethod_research_design page=249 -->
<!-- db:id=figure_19_multimethod_research_design type=figure render_as=mermaid product_tier=context pages=249 -->
### Figure 19 – Multimethod developmental research design | figure_19_multimethod_research_design

```mermaid
flowchart TB
  subgraph prep [Preparatory work]
    IC[Initial collection]
    CM[Consultative meeting]
    RV1[Revision]
    EM[Expert meeting]
  end
  subgraph dev [Development]
    MED[Mediation track]
    PLU[Plurilingual track]
    PHO[Phonology track]
  end
  subgraph qual [Qualitative validation]
    WS1[Workshops - 140 workshops, 999 participants]
    RV2[Revision - 60 descriptors dropped]
    OS1[Online survey - 250 responses]
  end
  subgraph quant [Quantitative validation]
    WS2[Workshops - 189 workshops, 1294 responses]
    OS2[Online survey - 3503 responses]
    DA[Data analysis - Rasch scaling and standard-setting]
  end
  subgraph consult [Consultation and Piloting]
    PC[Pre-consultation]
    FC[Formal consultation]
    PIL[Piloting]
    DIS[Dissemination]
  end
  prep --> dev --> qual --> quant --> consult
```
<!-- el:end id=figure_19_multimethod_research_design -->

*Development and validation of the extended illustrative descriptors ▶ Page **249***
"""


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    b244 = fix_p244(page_body(md, 244))
    print(
        "p244",
        len(page_body(md, 244)),
        "->",
        len(b244),
        "soup",
        "**Initial collation" in b244,
        "mermaid",
        "```mermaid" in b244,
        "fn",
        "www.coe.int" in b244,
    )
    md = replace_page(md, 244, b244)
    md = replace_page(md, 249, P249)
    MD.write_text(md, encoding="utf-8")
    md2 = MD.read_text(encoding="utf-8")
    print("p249 soup", "book-qa p249" in page_body(md2, 249))
    print("p244 soup", "**Initial collation" in page_body(md2, 244))


if __name__ == "__main__":
    main()
