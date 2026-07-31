import re
from pathlib import Path

import pdfplumber

md_path = Path("output/cefr-companion-2020/CEFR_Companion_Volume.md")
md = md_path.read_text(encoding="utf-8")
with pdfplumber.open("input/cefr-companion-2020/source.pdf") as pdf:
    ts = pdf.pages[24].extract_tables() or []
chunks = []
for table in ts:
    if not table:
        continue
    rows = [
        [("" if c is None else str(c).replace("\n", "<br>").strip()) for c in row]
        for row in table
    ]
    w = max(len(r) for r in rows)
    rows = [r + [""] * (w - len(r)) for r in rows]
    lines = [
        "| " + " | ".join(rows[0]) + " |",
        "| " + " | ".join(["---"] * w) + " |",
    ] + ["| " + " | ".join(r) + " |" for r in rows[1:]]
    chunks.append("\n".join(lines))
block = "\n\n".join(chunks)
markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
for i, m in enumerate(markers):
    if int(m.group(1)) == 25:
        start = markers[i - 1].end() if i else 0
        end = m.start()
        reg = md[start:end]
        # drop old broken restore if any
        reg = re.sub(
            r"<!-- book-qa p25[\s\S]*?(?=(\*Page|\*Introduction|<!-- page:))",
            "",
            reg,
        )
        new = (
            reg.rstrip()
            + "\n\n<!-- book-qa p25 table restore -->\n"
            + block
            + "\n\n"
        )
        md = md[:start] + new + md[end:]
        print("p25 ok", len(block))
        break
md_path.write_text(md, encoding="utf-8")
print("dialogue", "rather than dialogue" in md)
print("oral", "Oral interaction is understood" in md)
