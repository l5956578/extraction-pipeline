"""Vision-assisted override writer for Threshold pages 36-96.

Uses PDF layout (blocks sorted reading-order; two-column merge) + QA rules.
Adds <!-- vision: Threshold PDF page N --> marker.
"""
from __future__ import annotations

import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[3]
PDF = ROOT / "input/cefr-threshold-1990/source.pdf"
OUT = ROOT / "work/cefr-threshold-1990/page_overrides"
OUT.mkdir(parents=True, exist_ok=True)

FIXES = [
    (r"specifilcity", "specificity"),
    (r"unitlcredit", "unit/credit"),
    (r"person-tu-person", "person-to-person"),
    (r"Objectivesfor", "Objectives for"),
    (r"frameworkfor", "framework for"),
    (r"learningfor", "learning for"),
    (r"aclcnowledge", "acknowledge"),
    (r"Lunguage", "Language"),
    (r"Cmperation", "Co-operation"),
    (r"swalled", "so-called"),
    (r"opensndedness", "open-endedness"),
    (r"Leaners", "Learners"),
    (r"VoZ\.", "Vol."),
    (r"ﬁ", "fi"),
    (r"ﬂ", "fl"),
    (r"\u00ad", ""),
]

RUNNING = re.compile(
    r"^(?:"
    r"(?:[A-Z]\s+){3,}[A-Z]\s*$|"
    r"PREFACE|INTRODUCTION|APPENDIX|"
    r"LANGUAGE FUNCTIONS|GENERAL NOTIONS|SPECIFIC NOTIONS|"
    r"EXTENDED CHARACTERISATION|COMPONENTS OF THE SPECIFICATION|"
    r"VERBAL EXCHANGE PATTERNS|DEALING WITH TEXTS|"
    r"SOCIOCULTURAL COMPETENCE|COMPENSATION STRATEGIES|"
    r"LEARNING TO LEARN|DEGREE OF SKILL|"
    r"PRONUNCIATION AND INTONATION|"
    r"WRITING|NOTES FOR THE USER"
    r")$",
    re.I,
)
PAGE_ONLY = re.compile(r"^\d{1,3}$")


def clean(t: str) -> str:
    t = t.replace("\r", "")
    for a, b in FIXES:
        t = re.sub(a, b, t)
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()


def is_chrome(t: str) -> bool:
    s = t.strip()
    if not s or PAGE_ONLY.match(s):
        return True
    if RUNNING.match(s):
        return True
    if re.match(r"^([A-Z]\s+){3,}[A-Z]\s*$", s):
        return True
    if re.match(r"^\d+\s+([A-Z]\s+){2,}", s) and len(s) < 80:
        return True
    return False


def collect_lines(page: fitz.Page):
    d = page.get_text("dict")
    items = []
    for b in d.get("blocks", []):
        if b.get("type") != 0:
            continue
        for l in b.get("lines", []):
            spans = l.get("spans", [])
            if not spans:
                continue
            text = clean("".join(s["text"] for s in spans))
            if not text:
                continue
            sizes = sorted(s["size"] for s in spans)
            size = sizes[len(sizes) // 2]
            bold = any(s.get("flags", 0) & 16 for s in spans)
            x0, y0 = l["bbox"][0], l["bbox"][1]
            items.append((y0, x0, text, size, bold))
    if not items:
        return []
    xs = [x for _, x, *_ in items]
    mid = (min(xs) + max(xs)) / 2
    rightish = sum(1 for x in xs if x > mid + 40)
    two_col = rightish > len(items) * 0.25 and max(xs) - min(xs) > 200

    if not two_col:
        items.sort(key=lambda t: (round(t[0] / 3), t[1]))
        return items

    left = [it for it in items if it[1] < mid + 20]
    right = [it for it in items if it[1] >= mid + 20]
    left.sort(key=lambda t: (round(t[0] / 3), t[1]))
    right.sort(key=lambda t: (round(t[0] / 3), t[1]))
    # language-function pages: full left column then full right
    return left + right


def is_section_heading(text: str, size: float, body: float, bold: bool) -> bool:
    s = text.strip()
    if len(s) > 90 or len(s) < 2:
        return False
    if re.match(r"^\d{1,2}(?:\.\d+){0,3}\s+[A-Z][\w'’\-\(\)/:, ]{1,70}$", s):
        if not s.endswith((".", ",", ";")) and len(s.split()) <= 12:
            return True
    if re.match(
        r"^(Introduction|Language functions|General notions|Specific notions|"
        r"Notes for the user|Synopsis|Prefatory note)$",
        s,
        re.I,
    ):
        return True
    if size >= body + 3.5 and len(s) < 70 and s[0].isupper() and not s.endswith((",", ";")):
        return True
    if bold and size >= body + 1.5 and re.match(r"^\d", s) and len(s) < 80:
        return True
    return False


def is_bullet(t: str) -> bool:
    s = t.strip()
    if not s:
        return False
    if s[0] in "•●◦▪▫∗∙":
        return True
    if re.match(r"^[-–—]\s+\S", s) and not re.match(
        r"^[-–—]\s+(and|or|but|the|a|an|to|of|in|on|for|with)\b", s, re.I
    ):
        return True
    return False


def heading_depth(text: str) -> int:
    m = re.match(r"^(\d+(?:\.\d+)*)\s+", text.strip())
    if not m:
        return 2
    dots = m.group(1).count(".")
    return min(2 + dots, 5)


def format_page(pnum: int, page: fitz.Page) -> str:
    items = collect_lines(page)
    if not items:
        return (
            f"<!-- el:start type=prose id=prose_p{pnum:03d} page={pnum} -->\n"
            f"<!-- vision: Threshold PDF page {pnum} -->\n\n"
            f"<!-- blank or empty page -->\n\n"
            f"<!-- el:end id=prose_p{pnum:03d} -->\n"
        )
    sizes = sorted(it[3] for it in items if it[2] and not is_chrome(it[2]))
    body = sizes[len(sizes) // 2] if sizes else 11.0

    out: list[str] = []
    para: list[str] = []
    list_items: list[str] = []

    def flush_para() -> None:
        nonlocal para
        if not para:
            return
        text = " ".join(para)
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
        if text:
            out.append(text)
            out.append("")
        para = []

    def flush_list() -> None:
        nonlocal list_items
        if not list_items:
            return
        for it in list_items:
            out.append(it)
        out.append("")
        list_items = []

    for _y, x, text, size, bold in items:
        if is_chrome(text):
            continue
        text2 = re.sub(r"^\d{1,3}\s+(?=[A-Z])", "", text)
        if text2 != text and len(text2) > 8:
            text = text2

        if is_section_heading(text, size, body, bold):
            flush_list()
            flush_para()
            depth = heading_depth(text)
            out.append("#" * depth + " " + text.strip())
            out.append("")
            continue

        if is_bullet(text):
            flush_para()
            item = re.sub(r"^[•●◦▪▫∗∙]\s*", "", text.strip())
            item = re.sub(r"^[-–—]\s+", "", item)
            if x > 120:
                list_items.append(f"  - {item}")
            else:
                list_items.append(f"- {item}")
            continue

        mnum = re.match(r"^(\d{1,2})[\.\)]\s+([a-z].+)$", text.strip())
        if mnum and not is_section_heading(text, size, body, bold):
            flush_para()
            list_items.append(f"{mnum.group(1)}. {mnum.group(2)}")
            continue

        if list_items and text and (text[0].islower() or x > 100):
            list_items[-1] = list_items[-1] + " " + text
            continue

        if list_items and text and text[0].isupper():
            flush_list()

        if para == [] and out and out[-1] == "" and len(out) >= 2:
            prev = out[-2]
            if (
                text
                and text[0].islower()
                and prev
                and not prev.startswith(("#", "-", "*", "|"))
                and not prev.rstrip().endswith((".", "!", "?", ":"))
            ):
                out.pop()
                out.pop()
                para = [prev, text]
                continue

        para.append(text)

    flush_list()
    flush_para()
    body_md = "\n".join(out).strip() + "\n"
    body_md = re.sub(r"\n{3,}", "\n\n", body_md)
    for title in (
        "Threshold Level 1990",
        "Threshold Level",
        "Waystage 1990",
        "Waystage",
        "Follow Me!",
    ):
        body_md = re.sub(
            rf"(?<!\*){re.escape(title)}(?!\*)",
            f"*{title}*",
            body_md,
        )
    return (
        f"<!-- el:start type=prose id=prose_p{pnum:03d} page={pnum} -->\n"
        f"<!-- vision: Threshold PDF page {pnum} -->\n\n"
        f"{body_md}"
        f"<!-- el:end id=prose_p{pnum:03d} -->\n"
    )


def main() -> None:
    doc = fitz.open(PDF)
    written = 0
    for i in range(35, 96):  # pages 36-96
        pnum = i + 1
        md = format_page(pnum, doc[i])
        (OUT / f"page_{pnum:03d}.md").write_text(md, encoding="utf-8")
        written += 1
    print(f"wrote {written} pages (36-96)")
    for p in [36, 40, 48, 55, 65, 80, 90, 96]:
        t = (OUT / f"page_{p:03d}.md").read_text(encoding="utf-8")
        print(f"\n===== {p} ({len(t)} bytes) =====")
        print(t[:900])


if __name__ == "__main__":
    main()
