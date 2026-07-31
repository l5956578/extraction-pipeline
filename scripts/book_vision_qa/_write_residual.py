from pathlib import Path
import json
from datetime import datetime, timezone

Path("work/cefr-companion-2020/metadata/book_qa/RESIDUAL.md").write_text(
"""# Residual inventory (final grind state)

## Gates
- Hard regression: **0**
- Soft regression: **0**
- Structural critical/major: **0**
- Vision YAML: **278 pass / 0 fail**
- Approved version: **052** (`output/cefr-companion-2020/APPROVED.json`)

## Product residuals (not defects)
- 7 minor `md_much_longer_than_pdf` on multipage-merged scale pages (99,146,150,158,183,187,249)
- Appendix 7 shows change-history dual wording cleaned to final modality-inclusive forms
- Participant institute lists use user table layout (temp only 14-20), PDF page-aligned approximately
- TOC kept live; surgical APP5/6 line fix only

## Not done / optional later
- Appendix 7 could be further vision-checked against strikeout layout for exact old/new presentation
- Multipage page-parity product decision for mid-span chrome pages remains merge+slice hybrid

## Live deliverable
`output/cefr-companion-2020/CEFR_Companion_Volume.md`
""",
    encoding="utf-8",
)
print("residual written")
