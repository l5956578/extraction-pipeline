"""Post-fix chapter titles + rebuild ALTE skill summary tables from PDF text."""
import re, sys
from pathlib import Path
import fitz

ROOT = Path(".")
PDF = ROOT / "input/cefr-en-2001/source.pdf"
OV = ROOT / "work/cefr-en-2001/page_overrides"
doc = fitz.open(PDF)

CHAPTER_PAGES = {
    166: ("7", "Tasks and their role in language teaching"),
    177: ("8", "Linguistic diversification and the curriculum"),
    186: ("9", "Assessment"),
}

def fix_chapter(pnum, num, title):
    path = OV / f"page_{pnum:03d}.md"
    t = path.read_text(encoding="utf-8")
    # inject chapter heading after vision tag if missing
    if f"## {num} {title}" in t or f"# {num} {title}" in t:
        return
    # ensure first heading isn't only 7.1
    insert = f"## {num} {title}\n\n"
    t2 = re.sub(
        r"(<!-- vision: CEFR 2001 PDF page \d+ -->\n\n)",
        r"\1" + insert,
        t,
        count=1,
    )
    path.write_text(t2, encoding="utf-8")
    print("chapter fixed", pnum)

for p, (n, title) in CHAPTER_PAGES.items():
    fix_chapter(p, n, title)

# --- ALTE summary tables: D1 p260, D2 p261, D4 p263, D6 p265 ---
# Parse get_text for structure Level / 3 skill columns

ALTE_SUMMARY = {
    260: ("Document D1", "ALTE skill level summaries"),
    261: ("Document D2", "ALTE social and tourist statements summary"),
    263: ("Document D4", "ALTE work statements summary"),
    265: ("Document D6", "ALTE study statements summary"),
}

LEVELS = [
    "ALTE Level 5",
    "ALTE Level 4",
    "ALTE Level 3",
    "ALTE Level 2",
    "ALTE Level 1",
    "ALTE Breakthrough Level",
]

def rebuild_alte_summary(pnum, doc_title, subtitle):
    page = doc[pnum - 1]
    text = page.get_text("text")
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
    # strip chrome
    for ch in ["Appendix D: The ALTE 'Can Do' statements",
               "Appendix D: The ALTE ‘Can Do’ statements", str(pnum-9)]:
        pass
    # Find sections by level markers
    # Pattern: ALTE Level N ... text until next ALTE Level
    body = text
    # Remove headers
    for h in [doc_title, subtitle, "ALTE Level", "Listening/Speaking", "Reading", "Writing"]:
        # only remove first occurrence headers carefully
        pass

    rows = []
    # Split by level labels
    pattern = r"(ALTE Level [1-5]|ALTE Breakthrough Level)"
    parts = re.split(pattern, body)
    # parts[0] is preamble, then label, content, label, content...
    i = 1
    while i + 1 < len(parts):
        label = parts[i].strip()
        content = parts[i + 1]
        # stop content at Document or page number only lines
        content = re.split(r"\nDocument |\n\d{3}\s*$", content)[0]
        # content has 3 columns of CAN statements mixed by line - use find_tables differently
        rows.append((label, content))
        i += 2

    # Better: use table extract but transpose if needed
    tabs = page.find_tables()
    if not tabs or not tabs.tables:
        print("no table", pnum)
        return
    data = tabs.tables[0].extract()
    # data often is: rows = skills, cols = levels OR rotated
    # From p260 earlier extract: first row Writing | CAN...x6, last row ALTE Level | Level5... 
    # So it's transposed: we want rows=levels, cols=skills
    # Detect orientation
    flat0 = " ".join(str(c) or "" for c in data[0])
    if "Writing" in flat0 or "Reading" in flat0 or "Listening" in flat0:
        # rows are skills, last row may be levels
        # Transpose to levels x skills
        # data shape: [Writing, c1, c2, ... c6], [Reading, ...], [Listening, ...], [ALTE Level, L5, L4, ...]
        skill_rows = []
        level_headers = None
        for row in data:
            cells = [("" if c is None else str(c).replace("\n", " ").strip()) for c in row]
            if not any(cells):
                continue
            key = cells[0]
            if "ALTE Level" in key and "Level 5" not in key:
                level_headers = cells[1:]
            else:
                skill_rows.append(cells)
        if not level_headers:
            # invent from count
            n = max(len(r) for r in skill_rows) - 1
            level_headers = LEVELS[:n]
        # build matrix skill -> list of cells
        skills = {}
        for r in skill_rows:
            skills[r[0]] = r[1:]
        # order skills
        order = []
        for k in skills:
            if "Listening" in k:
                order.append(k)
        for k in skills:
            if "Reading" in k and k not in order:
                order.append(k)
        for k in skills:
            if "Writing" in k and k not in order:
                order.append(k)
        for k in skills:
            if k not in order:
                order.append(k)
        # normalize lengths
        nlev = len(level_headers)
        md = []
        md.append("| ALTE Level | " + " | ".join(order) + " |")
        md.append("| --- | " + " | ".join(["---"] * len(order)) + " |")
        for li, lev in enumerate(level_headers):
            cells = [lev]
            for sk in order:
                vals = skills[sk]
                cells.append(vals[li] if li < len(vals) else "")
            md.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
        table_md = "\n".join(md)
    else:
        # already level-first
        rows2 = [[("" if c is None else str(c).replace("\n"," ").strip()) for c in r] for r in data]
        ncol = max(len(r) for r in rows2)
        rows2 = [r+[""]*(ncol-len(r)) for r in rows2]
        md = []
        md.append("| " + " | ".join(rows2[0]) + " |")
        md.append("| " + " | ".join(["---"]*ncol) + " |")
        for r in rows2[1:]:
            md.append("| " + " | ".join(r) + " |")
        table_md = "\n".join(md)

    table_md = table_md.replace("ﬁ","fi").replace("ﬂ","fl")
    out = (
        f"<!-- el:start type=prose id=prose_p{pnum:03d} page={pnum} -->\n"
        f"<!-- vision: CEFR 2001 PDF page {pnum} -->\n\n"
        f"### {doc_title} {subtitle}\n\n"
        f"<!-- el:start type=table id=cefr2001_p{pnum:03d}_t0 page={pnum} -->\n"
        f"{table_md}\n"
        f"<!-- el:end id=cefr2001_p{pnum:03d}_t0 -->\n\n"
        f"<!-- el:end id=prose_p{pnum:03d} -->\n"
    )
    (OV / f"page_{pnum:03d}.md").write_text(out, encoding="utf-8")
    print("ALTE summary fixed", pnum, "rows", table_md.count("\n"))

for p, (dt, st) in ALTE_SUMMARY.items():
    rebuild_alte_summary(p, dt, st)

print("done")
