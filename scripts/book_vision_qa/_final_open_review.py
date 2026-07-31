from pathlib import Path
p = Path("work/cefr-companion-2020/metadata/book_qa/OPEN_REVIEW.md")
p.write_text(
"""# Book QA — status

**Soft-issue viewer: stopped / ignored.**

## Gates (final)

| Metric | Value |
|--------|------:|
| Hard regression | **0** |
| Soft regression | **0** |
| Structural critical / major | **0** |
| Structural minor (`md_much_longer_than_pdf`) | 7 (multipage product shape) |
| Vision YAML | 278 pass / 0 fail |
| Pages | 278 |
| **Approved version** | **`versions/052`** |

## Live

`output/cefr-companion-2020/CEFR_Companion_Volume.md`  
`output/cefr-companion-2020/APPROVED.json` → 052

## Applied this grind

- User `temp only 14-20.txt` institute tables (PDF-aligned)
- TOC: live kept; APP5/6 line fix only (`temp only toc.txt` not better overall)
- p.132: split Grammatical accuracy / Vocabulary control
- p.250: restored RELATIONSHIP OF MEDIATION SCALES body
- Appendix 7 dual-struck cleaned to modality-inclusive forms
- Multipage sentence cutoffs; leaf soup; reverse OCR cleared
- Figure/fence dual dumps cleaned

## Residual (non-blocking)

Multipage merge pages only for structural minor flags. See `RESIDUAL.md`.
""",
    encoding="utf-8",
)
print("OPEN_REVIEW final")
