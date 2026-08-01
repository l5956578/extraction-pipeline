"""Line-preserving override generator for Threshold function/notion pages.

Two-column: emit left column fully, then right (as on page top→bottom).
Do NOT glue lines into paragraphs on dense list pages.
Prose pages: paragraph join with blank lines.
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
    (r"LeveZ", "Level"),
    (r"ﬁ", "fi"),
    (r"ﬂ", "fl"),
    (r"\u00ad", ""),
    (r"a'fiaid pot", "afraid not"),
    (r"Con'gratuJations", "Congratulations"),
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
    r"PRONUNCIATION AND INTONATION|WRITING"
    r")$",
    re.I,
)
PAGE_ONLY = re.compile(r"^\d{1,3}$")
FN_NUM = re.compile(r"^(\d+(?:\.\d+){0,4})\s+(.*)$")
HEAD_LIKE = re.compile(
    r"^(?:"
    r"\d{1,2}(?:\.\d+){0,2}\s+[a-z].{5,70}$|"  # 2.4 denying statements
    r"factual:|volitional|emotional|moral|"
    r"Introduction|Language functions|General notions|Specific notions|"
    r"Notes for the user|Listening|Reading|Writing"
    r")",
    re.I,
)


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


def collect_columns(page: fitz.Page):
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
            items.append({"y": y0, "x": x0, "t": text, "size": size, "bold": bold})
    if not items:
        return [], False
    xs = [it["x"] for it in items]
    mid = (min(xs) + max(xs)) / 2
    rightish = sum(1 for x in xs if x > mid + 40)
    two_col = rightish > len(items) * 0.22 and (max(xs) - min(xs)) > 180
    if not two_col:
        items.sort(key=lambda it: (round(it["y"] / 2), it["x"]))
        return items, False
    left = [it for it in items if it["x"] < mid + 15]
    right = [it for it in items if it["x"] >= mid + 15]
    left.sort(key=lambda it: (round(it["y"] / 2), it["x"]))
    right.sort(key=lambda it: (round(it["y"] / 2), it["x"]))
    return left + right, True


def is_heading(it, body: float) -> bool:
    t = it["t"]
    if len(t) > 95 or len(t) < 2:
        return False
    # short numbered title
    if re.match(r"^\d{1,2}(?:\.\d+){0,2}\s+[A-Za-z].{2,70}$", t):
        # if looks like function label (lowercase start after num) → heading when size/bold
        rest = re.sub(r"^\d+(?:\.\d+)*\s+", "", t)
        if rest and rest[0].islower() and (it["size"] >= body + 0.5 or it["bold"]):
            return True
        if rest and rest[0].isupper() and not t.endswith((".", ",", ";")) and len(t.split()) <= 12:
            return True
    if re.match(
        r"^(Introduction|Language functions|General notions|Specific notions|"
        r"Listening|Reading|Writing|Notes for the user|"
        r"factual:|volitional|emotional|moral)$",
        t,
        re.I,
    ):
        return True
    if it["size"] >= body + 3.0 and len(t) < 70 and t[0].isupper():
        return True
    return False


def depth_for(t: str) -> int:
    m = re.match(r"^(\d+(?:\.\d+)*)\s+", t)
    if not m:
        return 2
    return min(2 + m.group(1).count("."), 5)


def format_list_page(pnum: int, items, body: float) -> str:
    """Preserve lines; format function numbers."""
    lines: list[str] = []
    for it in items:
        t = it["t"]
        if is_chrome(t):
            continue
        t = re.sub(r"^\d{1,3}\s+(?=[A-Z])", "", t)
        if is_heading(it, body):
            d = depth_for(t)
            lines.append("")
            lines.append("#" * d + " " + t)
            lines.append("")
            continue
        # bullet
        if t[0] in "•●◦▪▫∗∙" or re.match(r"^[-–—]\s+\S", t):
            item = re.sub(r"^[•●◦▪▫∗∙]\s*", "", t)
            item = re.sub(r"^[-–—]\s+", "", item)
            lines.append(f"- {item}")
            continue
        # numbered function entry: "2.1.6.4 text"
        m = FN_NUM.match(t)
        if m and m.group(1).count(".") >= 1:
            num, rest = m.group(1), m.group(2)
            if rest:
                lines.append(f"**{num}** {rest}")
            else:
                lines.append(f"**{num}**")
            continue
        if m and m.group(1).count(".") == 0 and len(t.split()) <= 10:
            # "1 Imparting..." already handled as heading if Title Case
            if is_heading(it, body):
                lines.append("")
                lines.append("## " + t)
                lines.append("")
                continue
        # continuation / example line — indent if starts with quote or lowercase
        if t.startswith(("'", "‘", "\"", "…", "...", "(")) or (t and t[0].islower()):
            lines.append(f"  {t}")
        else:
            lines.append(t)
    body_md = "\n".join(lines)
    body_md = re.sub(r"\n{3,}", "\n\n", body_md).strip() + "\n"
    return wrap(pnum, body_md)


def format_prose_page(pnum: int, items, body: float) -> str:
    out: list[str] = []
    para: list[str] = []
    bullets: list[str] = []

    def flush_p():
        nonlocal para
        if not para:
            return
        text = " ".join(para)
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
        if text:
            out.append(text)
            out.append("")
        para = []

    def flush_b():
        nonlocal bullets
        if not bullets:
            return
        out.extend(bullets)
        out.append("")
        bullets = []

    for it in items:
        t = it["t"]
        if is_chrome(t):
            continue
        t = re.sub(r"^\d{1,3}\s+(?=[A-Z])", "", t)
        if is_heading(it, body):
            flush_b()
            flush_p()
            out.append("#" * depth_for(t) + " " + t)
            out.append("")
            continue
        if t[0] in "•●◦▪▫∗∙" or (
            re.match(r"^[-–—]\s+\S", t)
            and not re.match(r"^[-–—]\s+(and|or|but|the|a|an)\b", t, re.I)
        ):
            flush_p()
            item = re.sub(r"^[•●◦▪▫∗∙]\s*", "", t)
            item = re.sub(r"^[-–—]\s+", "", item)
            bullets.append(f"- {item}")
            continue
        if bullets and t and t[0].islower():
            bullets[-1] += " " + t
            continue
        if bullets:
            flush_b()
        if (
            para == []
            and out
            and out[-1] == ""
            and len(out) >= 2
            and t
            and t[0].islower()
            and out[-2]
            and not out[-2].startswith(("#", "-", "*"))
            and not out[-2].rstrip().endswith((".", "!", "?", ":"))
        ):
            prev = out[-2]
            out.pop()
            out.pop()
            para = [prev, t]
            continue
        para.append(t)
    flush_b()
    flush_p()
    body_md = "\n".join(out).strip() + "\n"
    body_md = re.sub(r"\n{3,}", "\n\n", body_md)
    for title in (
        "Threshold Level 1990",
        "Threshold Level",
        "Waystage 1990",
        "Waystage",
        "Follow Me!",
    ):
        body_md = re.sub(rf"(?<!\*){re.escape(title)}(?!\*)", f"*{title}*", body_md)
    return wrap(pnum, body_md)


def wrap(pnum: int, body: str) -> str:
    return (
        f"<!-- el:start type=prose id=prose_p{pnum:03d} page={pnum} -->\n"
        f"<!-- vision: Threshold PDF page {pnum} -->\n\n"
        f"{body}"
        f"<!-- el:end id=prose_p{pnum:03d} -->\n"
    )


def is_dense_list_page(items) -> bool:
    """Heuristic: many short numbered function lines."""
    if not items:
        return False
    n = 0
    for it in items:
        t = it["t"]
        if re.match(r"^\d+\.\d+", t):
            n += 1
    return n >= 8


def format_page(pnum: int, page: fitz.Page) -> str:
    items, two_col = collect_columns(page)
    if not items:
        return wrap(pnum, "<!-- blank or empty page -->\n")
    sizes = [it["size"] for it in items if not is_chrome(it["t"])]
    body = sorted(sizes)[len(sizes) // 2] if sizes else 11.0
    if two_col or is_dense_list_page(items):
        return format_list_page(pnum, items, body)
    return format_prose_page(pnum, items, body)


def main() -> None:
    doc = fitz.open(PDF)
    # regenerate pages that still need structure: 40-89 (keep hand-written 1-39ish and some)
    # Overwrite 40-89 always; also re-do 36-39 only if flag; keep 1-35 hand vision
    # User asked all 1-96; hand-done 1-39; regenerate 40-96 then vision polish prose
    written = 0
    for i in range(39, 96):  # 40-96
        pnum = i + 1
        md = format_page(pnum, doc[i])
        (OUT / f"page_{pnum:03d}.md").write_text(md, encoding="utf-8")
        written += 1
    print(f"wrote {written} pages 40-96")
    for p in [40, 45, 50, 58, 65, 75, 82, 88, 92, 96]:
        t = (OUT / f"page_{p:03d}.md").read_text(encoding="utf-8")
        print(f"\n===== p{p} {len(t)}b lines={t.count(chr(10))} =====")
        print(t[:1100])


if __name__ == "__main__":
    main()
