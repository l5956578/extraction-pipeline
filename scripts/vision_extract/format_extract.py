#!/usr/bin/env python3
"""Layout-aware PDF→MD formatter for Threshold / Waystage / CEFR 2001.

Fixes the soup-assembly failure mode:
- real paragraphs (not one glued row)
- bullet / numbered / lettered lists as MD lists
- headers as ## (not spaced running heads, not glued)
- intonation marks using PDF-like Unicode (not [LF] placeholders alone)

Does NOT reimplement Companion multi-week engine.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]

# --- Intonation notation (van Ek–Trim App A; above/below line ≈ Unicode modifiers) ---
# PDF: falling diagonal below = low fall; same above = high fall;
#      rising below = low rise; rising above = high rise; v above = fall-rise.
TONE = {
    "LF": "\u02ce",  # ˎ low grave (below-line fall)
    "HF": "\u02cb",  # ˋ grave (above-line fall)
    "LR": "\u02cf",  # ˏ low acute (below-line rise)
    "HR": "\u02ca",  # ˊ acute (above-line rise)
    "FR": "\u02c7",  # ˇ caron / v-mark (fall-rise above)
    "HEAD": "\u02c8",  # ˈ primary stress / head upright
    "STRESS": "\u00b7",  # · secondary/rhythmic stress (mid-height dot)
    "MINOR": "|",
    "MAJOR": "||",
}

RUNNING_HEAD_RE = re.compile(
    r"^(?:"
    r"P\s*R\s*E\s*F\s*A\s*C\s*E|"
    r"I\s*N\s*T\s*R\s*O\s*D\s*U\s*C\s*T\s*I\s*O\s*N|"
    r"A\s*P\s*P\s*E\s*N\s*D\s*I\s*X\s*A?|"
    r"L\s*A\s*N\s*G\s*U\s*A\s*G\s*E\s*F\s*U\s*N\s*C\s*T\s*I\s*O\s*N\s*S|"
    r"G\s*E\s*N\s*E\s*R\s*A\s*L\s*N\s*O\s*T\s*I\s*O\s*N\s*S|"
    r"S\s*P\s*E\s*C\s*I\s*F\s*I\s*C\s*N\s*O\s*T\s*I\s*O\s*N\s*S|"
    r"P\s*R\s*O\s*N\s*U\s*N\s*C\s*I\s*A\s*T\s*I\s*O\s*N.*"
    r")$",
    re.I,
)
PAGE_ONLY_RE = re.compile(r"^\d{1,3}$")
BULLET_CHARS = "•●◦▪▫·∗∙"


@dataclass
class Line:
    text: str
    size: float = 11.0
    bold: bool = False
    x0: float = 0.0
    y0: float = 0.0
    is_bullet: bool = False


def slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return s[:80] or "section"


def clean_line(t: str) -> str:
    t = t.replace("\u00ad", "")  # soft hyphen
    t = t.replace("\ufb01", "fi").replace("\ufb02", "fl")
    t = t.replace("ﬁ", "fi").replace("ﬂ", "fl")
    t = t.replace("unitlcredit", "unit/credit")
    t = t.replace("person-tu-person", "person-to-person")
    t = t.replace("frameworkfor", "framework for")
    t = t.replace("Objectivesfor", "Objectives for")
    t = t.replace("swalled", "so-called")
    t = t.replace("opensndedness", "open-endedness")
    t = t.replace("aclcnowledge", "acknowledge")
    t = t.replace("Lunguage", "Language")
    t = t.replace("Cmperation", "Co-operation")
    t = t.replace("learningfor", "learning for")
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()


def is_running_chrome(t: str) -> bool:
    s = t.strip()
    if not s:
        return True
    if PAGE_ONLY_RE.match(s):
        return True
    if RUNNING_HEAD_RE.match(s.replace(" ", "") if " " in s and len(s) < 40 else s):
        # spaced letters: P R E F A C E
        if re.match(r"^([A-Z]\s+){3,}[A-Z]\s*$", s):
            return True
    if re.match(r"^([A-Z]\s+){4,}[A-Z]?$", s):  # spaced running head
        return True
    if s in {"APPENDIX A", "PREFACE", "INTRODUCTION"}:
        return True  # mid-page running heads (body titles handled by size)
    return False


def is_bullet_line(t: str) -> bool:
    """True only for real list bullets — NOT mid-sentence em-dashes for emphasis."""
    s = t.strip()
    if not s:
        return False
    # Real bullets: • or dash at start followed by capital or long phrase
    if s[0] in "•●◦▪▫∗∙":
        return True
    # Hyphen/en-dash bullet ONLY if starts line and next char is space + word
    # Reject em-dash emphasis mid-prose already stripped; reject "– and many more –"
    if re.match(r"^[-–—]\s+[A-Za-z“‘\"(]", s):
        # Not a bullet if it looks like continuation dash fragment
        if re.match(r"^[-–—]\s+(and|or|but|the|a|an|to|of|in|on|for|with)\b", s, re.I):
            return False
        return True
    return False


def is_section_number_heading(t: str) -> bool:
    """'1 Target Group', '2 Criteria', '3 Adaptability' — headers, NOT numbered lists."""
    s = t.strip()
    # Short numbered titles: digit(s) + space + Title Case words, no trailing period sentence
    if re.match(r"^\d{1,2}\s+[A-ZÀ-Ö][\w'’\-: ]{1,60}$", s) and not s.endswith((".", ",", ";")):
        # Reject long sentences
        if len(s.split()) <= 10:
            return True
    # "1. Low falling" App A definitions with name after number — still can be list OR heading;
    # prefer heading when pattern is N + Capitalized multiword short title without verb-heavy body
    if re.match(r"^\d{1,2}\.\s+[A-Z][a-z]+(?:\s+[A-Z]?[a-z]+){0,5}$", s):
        return True
    return False


def is_numbered_line(t: str) -> bool | str:
    """Return list marker kind or False. Section heads are NOT lists."""
    s = t.strip()
    if is_section_number_heading(s):
        return False
    if re.match(r"^\d{1,2}[\.\)]\s+\S", s):
        # "1. for factual statements" = list; "1. Target Group" already caught
        rest = re.sub(r"^\d{1,2}[\.\)]\s+", "", s)
        if rest and rest[0].islower():
            return "num"
        if re.match(r"^(for|in|as|to|when|if|with|by|on|at)\b", rest, re.I):
            return "num"
        # Title-like after "1." → not a list item
        if re.match(r"^[A-Z]", rest) and len(rest.split()) <= 8 and not rest.endswith("."):
            return False
        return "num"
    # Do NOT treat "1 Target Group" as num_space list (handled as section heading)
    if re.match(r"^[a-z]\)\s+\S", s):
        return "alpha"
    if re.match(r"^[ivx]+\)\s+\S", s, re.I):
        return "roman"
    if re.match(r"^[ivx]+\.\s+\S", s, re.I) and len(s) < 120:
        return "roman_dot"
    return False


def looks_like_heading_line(t: str, size: float, bold: bool, body_size: float) -> bool:
    s = t.strip()
    if len(s) < 2 or len(s) > 100:
        return False
    if is_bullet_line(s):
        return False
    # Numbered section titles are headings (1 Target Group / 2 Criteria / 3.1 Criteria…)
    if is_section_number_heading(s):
        return True
    if is_numbered_line(s):
        return False
    # Never promote mid-sentence fragments (common PDF span-size false positives)
    if s[0].islower():
        return False
    if s[0] in "\"'“‘([":
        return False
    # Known structural titles
    if re.match(
        r"^(Preface|Introduction|Chapter\s+\d|Appendix\s+[A-D0-9]|"
        r"Language functions|General notions|Specific notions|"
        r"Contents|Table of contents|CONTENTS|Foreword|Acknowledgement|"
        r"PREFATORY NOTE|Notes for the user|Synopsis|"
        r"Pronunciation and intonation|Grammatical summary|"
        r"Common Reference Levels|Description Issues|Measurement Issues|"
        r"\d+(\.\d+)*\s+[A-Z].{3,70})$",
        s,
        re.I,
    ):
        return True
    if re.match(r"^\d+\.\d+(\.\d+)*\s+[A-Z]", s) and len(s) < 90:
        return True
    if re.match(r"^\d{1,2}\s+[A-Z][\w'’\-: ]{1,50}$", s) and len(s.split()) <= 10:
        return True
    # Size-based only if clearly larger AND title-like (Title Case / short)
    if size >= body_size + 4 and len(s) < 70:
        words = s.split()
        if words and words[0][0].isupper() and not s.endswith((",", ";", ":", "and", "of", "the", "to", "a")):
            # reject if looks like sentence continuation (ends mid-phrase without period and long)
            if s.endswith(".") or len(words) <= 8:
                return True
    if bold and size >= body_size + 2.5 and len(s) < 60 and s[0].isupper():
        return True
    return False


def extract_lines_layout(page: fitz.Page) -> list[Line]:
    d = page.get_text("dict")
    raw: list[Line] = []
    for bi, b in enumerate(d.get("blocks", [])):
        if b.get("type") != 0:
            continue
        if raw and raw[-1].text != "":
            # Block boundary = paragraph break (critical for real formatting)
            raw.append(Line(text="", size=11.0, x0=0, y0=b.get("bbox", [0, 0, 0, 0])[1]))
        for l in b.get("lines", []):
            spans = l.get("spans", [])
            if not spans:
                continue
            text = "".join(s["text"] for s in spans)
            text = clean_line(text)
            if not text:
                continue
            # body size = median of span sizes (ignore oversized bullets/dashes)
            sizes = sorted(s["size"] for s in spans)
            size = sizes[len(sizes) // 2]
            bold = any(s.get("flags", 0) & 2 ** 4 for s in spans)
            x0 = l["bbox"][0]
            y0 = l["bbox"][1]
            raw.append(Line(text=text, size=size, bold=bold, x0=x0, y0=y0))
    # Merge orphan bullet-only lines with the following text line
    lines: list[Line] = []
    i = 0
    while i < len(raw):
        ln = raw[i]
        if ln.text.strip() in set(BULLET_CHARS) | {"*", "·"} and i + 1 < len(raw):
            # find next non-empty
            j = i + 1
            while j < len(raw) and not raw[j].text:
                j += 1
            if j < len(raw):
                nxt = raw[j]
                if not is_bullet_line(nxt.text) and not is_running_chrome(nxt.text):
                    merged = f"- {nxt.text.lstrip()}"
                    lines.append(
                        Line(
                            text=merged,
                            size=nxt.size,
                            bold=nxt.bold,
                            x0=ln.x0,
                            y0=ln.y0,
                            is_bullet=True,
                        )
                    )
                    i = j + 1
                    continue
        lines.append(ln)
        i += 1
    return lines


def extract_lines_ocr(ocr_path: Path) -> list[Line]:
    if not ocr_path.exists():
        return []
    raw = ocr_path.read_text(encoding="utf-8", errors="replace")
    lines = []
    for ln in raw.splitlines():
        t = clean_line(ln)
        if not t:
            # keep blank as paragraph break marker
            lines.append(Line(text="", size=11.0))
            continue
        lines.append(Line(text=t, size=11.0))
    return lines


def median_body_size(lines: list[Line]) -> float:
    sizes = sorted(l.size for l in lines if l.text and not is_running_chrome(l.text))
    if not sizes:
        return 11.0
    return sizes[len(sizes) // 2]


def format_bullet_text(t: str) -> str:
    s = t.strip()
    s = re.sub(r"^[•●◦▪▫∗∙]\s*", "", s)
    s = re.sub(r"^[-–—]\s+", "", s)
    return s.strip()


def lines_to_markdown(lines: list[Line], page_num: int, job: str) -> str:
    if not lines:
        return (
            f"<!-- el:start type=prose id=prose_p{page_num:03d}_empty page={page_num} -->\n"
            f"<!-- empty page -->\n"
            f"<!-- el:end id=prose_p{page_num:03d}_empty -->\n"
        )

    body_size = median_body_size(lines)
    out: list[str] = []
    para_buf: list[str] = []
    list_buf: list[tuple[str, str]] = []  # (kind, text) kind: - or 1. or a) etc
    list_kind: str | None = None

    def flush_para() -> None:
        nonlocal para_buf
        if not para_buf:
            return
        text = " ".join(para_buf)
        text = re.sub(r"\s+", " ", text).strip()
        # de-hyphenate line-end hyphens already joined
        text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
        if text:
            out.append(text)
            out.append("")
        para_buf = []

    def flush_list() -> None:
        nonlocal list_buf, list_kind
        if not list_buf:
            return
        for kind, item in list_buf:
            out.append(f"{kind} {item}")
        out.append("")
        list_buf = []
        list_kind = None

    for i, ln in enumerate(lines):
        t = ln.text
        if not t:
            flush_list()
            flush_para()
            continue
        if is_running_chrome(t):
            continue
        # page number glued to text start
        t2 = re.sub(r"^\d{1,3}\s+(?=[A-Z])", "", t)
        if t2 != t and len(t2) > 10:
            t = t2

        # heading?
        if looks_like_heading_line(t, ln.size, ln.bold, body_size):
            flush_list()
            flush_para()
            h = t.strip()
            # numbered section title
            if re.match(r"^\d+(\.\d+)*\s+", h):
                depth = h.split()[0].count(".") + 2  # ## or ###
                depth = min(depth, 4)
                out.append("#" * depth + " " + h)
            else:
                out.append("## " + h)
            out.append("")
            continue

        # list item?
        nk = is_numbered_line(t)
        if is_bullet_line(t):
            flush_para()
            item = format_bullet_text(t)
            # Nest only when clearly more indented (hanging indent / sub-bullet)
            nest = False
            if list_buf and list_kind == "-":
                # sub-bullets in Threshold are dash under bullet; often larger left margin
                nest = ln.x0 > 130 or t.lstrip().startswith(("-", "–")) and t.startswith(" ")
            if nest:
                list_buf.append(("  -", item))
            else:
                if list_kind not in (None, "-"):
                    flush_list()
                list_kind = "-"
                list_buf.append(("-", item))
            continue

        if nk:
            flush_para()
            s = t.strip()
            if nk == "num":
                m = re.match(r"^(\d{1,2})[\.\)]\s+(.*)$", s)
                marker, rest = (f"{m.group(1)}.", m.group(2)) if m else ("1.", s)
            elif nk == "num_space":
                m = re.match(r"^(\d{1,2})\s+(.*)$", s)
                marker, rest = (f"{m.group(1)}.", m.group(2)) if m else ("1.", s)
            elif nk == "alpha":
                m = re.match(r"^([a-z])\)\s+(.*)$", s)
                marker, rest = (f"{m.group(1)})", m.group(2)) if m else ("a)", s)
            else:
                m = re.match(r"^([ivxIVX]+)[\)\.]\s+(.*)$", s)
                marker, rest = (f"{m.group(1)})", m.group(2)) if m else ("i)", s)
            # indent nested under numbered parent
            if nk in ("alpha", "roman", "roman_dot") and list_kind in ("1.", "num", "num_space"):
                list_buf.append((f"   {marker}", rest))
            elif nk in ("roman", "roman_dot") and list_kind in ("a)", "alpha"):
                list_buf.append((f"      {marker}", rest))
            else:
                if list_kind and list_kind not in ("1.", "num", "num_space") and nk.startswith("num"):
                    flush_list()
                list_kind = "1." if str(nk).startswith("num") else nk
                list_buf.append((marker, rest))
            continue

        # continuation of list item only if clearly wrapped (lowercase start or large indent)
        if list_buf and t and (t[0].islower() or ln.x0 > 120):
            kind, prev = list_buf[-1]
            # don't swallow a new section title glued to end of list item
            if re.search(r"\s{2,}[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\s*$", prev):
                flush_list()
            else:
                list_buf[-1] = (kind, (prev + " " + t).strip())
                continue

        # Split glued section headings mid-prose: "3.1 Criteria for … One of the aims"
        msec = re.match(
            r"^((\d+\.\d+(?:\.\d+)*)\s+[A-Z][^.]{3,90}?)(\s+)([A-Z][a-z].{15,})$",
            t,
        )
        if msec:
            flush_list()
            flush_para()
            title = msec.group(1).strip()
            rest = msec.group(4).strip()
            depth = min(title.split()[0].count(".") + 2, 4)
            out.append("#" * depth + " " + title)
            out.append("")
            para_buf.append(rest)
            continue

        # "Description Issues" / "Measurement Issues" mini-heads (exact title case only)
        if re.match(r"^(Description Issues|Measurement Issues)\s*$", t):
            flush_list()
            flush_para()
            out.append(f"### {t.strip()}")
            out.append("")
            continue

        # normal prose — may continue paragraph
        # If list was open and this is a new capitalised sentence, end list first
        if list_buf and t and t[0].isupper() and not t[0].islower():
            # Check if this looks like prose after a list (not a list continuation)
            flush_list()

        flush_list()
        # Join if previous paragraph ended mid-sentence and this continues lowercase
        if (
            out
            and para_buf == []
            and out[-1] == ""
            and len(out) >= 2
            and t
            and t[0].islower()
            and not out[-2].startswith(("#", "-", "*", "|", ">", "1", "2", "3", "4", "5", "6", "7", "8", "9"))
            and out[-2]
            and not out[-2].rstrip().endswith((".", "!", "?", ":", "||", "|"))
        ):
            # re-open previous paragraph
            prev = out[-2]
            out.pop()  # blank
            out.pop()  # prev
            para_buf = [prev, t]
            continue

        # detect mid-prose " - item - item" collapsed lists from OCR
        if " - " in t and t.count(" - ") >= 2 and len(t) < 200:
            flush_para()
            parts = re.split(r"\s+-\s+", t)
            # first part may be lead-in
            lead = parts[0]
            if lead and not lead.endswith(":"):
                # check if lead ends with :
                if ":" in lead:
                    pre, post = lead.rsplit(":", 1)
                    out.append(pre.strip() + ":")
                    out.append("")
                    if post.strip():
                        out.append(f"- {post.strip()}")
                else:
                    para_buf.append(lead)
                    flush_para()
            elif lead.endswith(":") or lead:
                out.append(lead if lead.endswith(":") else lead + ":")
                out.append("")
            for p in parts[1:]:
                p = p.strip(" -")
                if p:
                    out.append(f"- {p}")
            out.append("")
            continue

        para_buf.append(t)

    flush_list()
    flush_para()

    body = "\n".join(out).strip() + "\n"
    # collapse 3+ blanks
    body = re.sub(r"\n{3,}", "\n\n", body)
    # rejoin soft/line-break hyphens left in words
    body = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", body)
    body = re.sub(r"(\w)-\s+(\w)", r"\1\2", body)
    # promote lone numbered section titles left as prose lines
    body = re.sub(
        r"(?m)^(\d+\.\d+(?:\.\d+)*\s+[A-Z][^\n]{4,80})$",
        lambda m: "### " + m.group(1) if not m.group(1).endswith((".", ",", ";")) else m.group(1),
        body,
    )
    # fix orphan punctuation left after bad splits
    body = re.sub(r"(?m)^,\s+", "", body)
    body = re.sub(r"\n\n,\s+", " ", body)

    pid = f"prose_p{page_num:03d}"
    return (
        f"<!-- el:start type=prose id={pid} page={page_num} -->\n"
        f"{body}"
        f"<!-- el:end id={pid} -->\n"
    )


def apply_tone_symbol_pass(text: str) -> str:
    """Normalize intonation mark discussion to PDF-like Unicode + keep names."""
    # Standardize definition blocks if present with [LF] etc.
    repl = {
        r"\*\*\[LF\]\*\*": f"**{TONE['LF']}**",
        r"\*\*\[HF\]\*\*": f"**{TONE['HF']}**",
        r"\*\*\[LR\]\*\*": f"**{TONE['LR']}**",
        r"\*\*\[HR\]\*\*": f"**{TONE['HR']}**",
        r"\*\*\[FR\]\*\*": f"**{TONE['FR']}**",
        r"\[LF\]": TONE["LF"],
        r"\[HF\]": TONE["HF"],
        r"\[LR\]": TONE["LR"],
        r"\[HR\]": TONE["HR"],
        r"\[FR\]": TONE["FR"],
    }
    for a, b in repl.items():
        text = re.sub(a, b, text)
    return text


def nuclear_tones_reference_block(book: str) -> str:
    """Canonical Vision-verified five tones with PDF-like marks."""
    return f"""<!-- el:start type=artifact id={book}_appendix_a_nuclear_tones -->
<!-- db:id={book}_five_nuclear_tones type=section_block product_tier=context -->

### Five nuclear tones

**Critical notation — used throughout {book.title()} (and the paired 1990 book).**  
Marks are placed **before** the nuclear syllable. Position above vs below the line of writing is distinctive.

| # | Name | Mark | Position | Pitch |
|---|------|------|----------|-------|
| **1** | **Low falling** | **{TONE['LF']}** | **Below** the line | Nuclear vowel starts clear **low-mid**; drops to **low creak**; stays low to end of tone group. |
| **2** | **High falling** | **{TONE['HF']}** | **Above** the line | Like low fall, but nuclear vowel starts **above mid**. |
| **3** | **Low rising** | **{TONE['LR']}** | **Below** the line | Starts **low level**; continuous upward glide **not above mid**. With a non-prominent “tail”, nucleus stays low and the **rise spans the tail**. |
| **4** | **High rising** | **{TONE['HR']}** | **Above** the line | Starts between **low and mid**; upward glide extends **well above mid**. |
| **5** | **Falling-rising** | **{TONE['FR']}** | **Above** the line (v-shaped) | High fall + low rise: starts **high-mid**, drops to **low creak**, then upward glide **not above mid**. |

**Other marks in examples**

| Mark | Meaning |
|------|---------|
| **{TONE['HEAD']}** | Head (first prominent syllable; upright mark **above** the line) |
| **{TONE['STRESS']}** | Stressed non-prominent syllable (rhythmic beat; mid-height dot) |
| **{TONE['MINOR']}** | End of minor tone group |
| **{TONE['MAJOR']}** | End of major tone group |

**Examples** (mark immediately before the nuclear syllable):

- Low falling: {TONE['HEAD']}This is a {TONE['LF']}door.
- High falling: That's {TONE['HF']}excellent!
- Low rising: There's {TONE['HEAD']}no {TONE['STRESS']}need to be {TONE['LR']}worried.
- High rising: You were {TONE['STRESS']}born in {TONE['HR']}Scotland?
- Falling-rising: That {TONE['STRESS']}jug is {TONE['FR']}hot!

<!-- el:end id={book}_appendix_a_nuclear_tones -->
"""


def inject_nuclear_block(md: str, book: str, after_phrase: str) -> str:
    block = nuclear_tones_reference_block(book)
    # remove old nuclear blocks
    md = re.sub(
        r"<!-- el:start type=artifact id=.*?nuclear_tones.*?-->.*?<!-- el:end id=.*?nuclear_tones\s*-->",
        "",
        md,
        flags=re.S,
    )
    md = re.sub(
        r"<!-- el:start type=artifact id=.*?five_nuclear.*?-->.*?<!-- el:end id=.*?-->",
        "",
        md,
        flags=re.S,
        count=3,
    )
    idx = md.lower().find(after_phrase.lower())
    if idx < 0:
        # fallback: first "nuclear tones"
        idx = md.lower().find("five nuclear tones should be distinguished")
    if idx < 0:
        idx = md.lower().find("nuclear tones")
    if idx >= 0:
        # insert before the sentence
        md = md[:idx] + "\n\n" + block + "\n\n" + md[idx:]
    return md


def extract_tables_md(page: fitz.Page, page_num: int) -> str:
    parts = []
    try:
        tabs = page.find_tables().tables
    except Exception:
        return ""
    for ti, tab in enumerate(tabs, 1):
        data = tab.extract()
        if not data:
            continue
        ncol = max(len(r) for r in data)
        rows = []
        for r in data:
            cells = [(c or "").replace("\n", " ").replace("|", "\\|").strip() for c in r]
            cells += [""] * (ncol - len(cells))
            if any(cells):
                rows.append(cells[:ncol])
        if len(rows) < 2:
            continue
        db = f"table_p{page_num:03d}_{ti:02d}"
        parts.append(f"<!-- el:start type=table id={db} page={page_num} -->")
        parts.append(f"<!-- db:id={db} type=table product_tier=context pages={page_num} -->")
        parts.append("")
        parts.append("| " + " | ".join(rows[0]) + " |")
        parts.append("| " + " | ".join(["---"] * ncol) + " |")
        for r in rows[1:]:
            parts.append("| " + " | ".join(r) + " |")
        parts.append("")
        parts.append(f"<!-- el:end id={db} -->")
        parts.append("")
    return "\n".join(parts)


def load_page_override(job: str, pnum: int) -> str | None:
    """Vision-written page MD wins over auto format. Path: work/<job>/page_overrides/page_NNN.md"""
    p = ROOT / "work" / job / "page_overrides" / f"page_{pnum:03d}.md"
    if p.exists() and p.stat().st_size > 20:
        return p.read_text(encoding="utf-8").strip()
    return None


def build_book(
    job: str,
    title: str,
    out_name: str,
    use_ocr_fallback: bool,
) -> Path:
    pdf = ROOT / "input" / job / "source.pdf"
    ocr_dir = ROOT / "work" / job / "page_ocr"
    out_md = ROOT / "output" / job / out_name
    doc = fitz.open(pdf)
    n = doc.page_count
    n_ov = 0

    parts: list[str] = []
    parts.append(
        f"<!-- el:start type=prose id=prose_p001_doc page=1 -->\n"
        f"<!-- db:id={slug(job)} type=document product_tier=context pages=1-{n} -->\n\n"
        f"# {title}\n\n"
        f"<!-- source: input/{job}/source.pdf -->\n"
        f"<!-- extraction: layout-aware + Vision page_overrides (Companion conventions) -->\n"
        f"<!-- intonation marks: LF={TONE['LF']} HF={TONE['HF']} LR={TONE['LR']} "
        f"HR={TONE['HR']} FR={TONE['FR']} head={TONE['HEAD']} stress={TONE['STRESS']} -->\n"
        f"<!-- el:end id=prose_p001_doc -->\n\n"
    )

    for i in range(n):
        pnum = i + 1
        override = load_page_override(job, pnum)
        if override:
            n_ov += 1
            body = override + "\n"
        else:
            page = doc[i]
            native_len = len(page.get_text("text").strip())
            if native_len >= 40:
                lines = extract_lines_layout(page)
            elif use_ocr_fallback:
                lines = extract_lines_ocr(ocr_dir / f"page_{pnum:03d}.txt")
            else:
                lines = extract_lines_layout(page)
                if sum(1 for l in lines if l.text) < 3:
                    lines = extract_lines_ocr(ocr_dir / f"page_{pnum:03d}.txt")

            body = lines_to_markdown(lines, pnum, job)
            tables = extract_tables_md(page, pnum) if native_len >= 40 else ""
            # skip auto tables if page already has hand-crafted tables in body (unlikely without override)
            if tables and "type=table" not in body:
                body = body.rstrip() + "\n\n" + tables
        parts.append(body)
        parts.append(f"\n*Page **{pnum}***\n\n<!-- page:{pnum} -->\n\n")
        if pnum % 40 == 0:
            print(f"  {job} page {pnum}/{n}", flush=True)
    print(f"  {job}: {n_ov} Vision page overrides applied", flush=True)

    text = "".join(parts)
    text = apply_tone_symbol_pass(text)

    # Nuclear tones injection for 1990 books
    if "threshold" in job:
        text = inject_nuclear_block(text, "threshold", "five nuclear tones should be distinguished")
        # rewrite App A definition numbers into proper lists if soup remains
        text = re.sub(r"(?m)^(\d+)\s+(Low falling|High falling|Low rising|High rising|Falling[- ]?rising)\b",
                      r"\1. **\2**", text)
    if "waystage" in job:
        text = inject_nuclear_block(text, "waystage", "five nuclear tones should be distinguished")
        text = re.sub(r"(?m)^(\d+)\s+(Low falling|High falling|Low rising|High rising|Falling[- ]?rising)\b",
                      r"\1. **\2**", text)

    # CEFR 2001 critical tables (stitched quality)
    if "2001" in job or job.endswith("en-2001"):
        text = inject_cefr2001_critical(text)

    # Fix spaced headers leftover in body
    text = re.sub(r"(?m)^##\s+((?:[A-Z]\s+){2,}[A-Z])\s*$", lambda m: "## " + m.group(1).replace(" ", ""), text)
    text = re.sub(r"(?m)^((?:[A-Z]\s+){3,}[A-Z])\s*$", "", text)

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(text, encoding="utf-8")
    print(f"wrote {out_md} ({out_md.stat().st_size // 1024} KB)", flush=True)
    return out_md


def inject_cefr2001_critical(text: str) -> str:
    """Ensure Table 1 / stitched Table 2 / Figure 1 present with proper formatting."""
    # Import from fix module content inline to avoid broken titles
    t1 = """
<!-- el:start type=table id=cefr2001_table_1_common_reference_levels_global_scale page=33 -->
<!-- db:id=cefr2001_table_1_common_reference_levels_global_scale type=table product_tier=base pages=33 -->

**Table 1. Common Reference Levels: global scale**

| Band | Level | Descriptor |
| --- | --- | --- |
| **Proficient User** | **C2** | Can understand with ease virtually everything heard or read. Can summarise information from different spoken and written sources, reconstructing arguments and accounts in a coherent presentation. Can express him/herself spontaneously, very fluently and precisely, differentiating finer shades of meaning even in more complex situations. |
|  | **C1** | Can understand a wide range of demanding, longer texts, and recognise implicit meaning. Can express him/herself fluently and spontaneously without much obvious searching for expressions. Can use language flexibly and effectively for social, academic and professional purposes. Can produce clear, well-structured, detailed text on complex subjects, showing controlled use of organisational patterns, connectors and cohesive devices. |
| **Independent User** | **B2** | Can understand the main ideas of complex text on both concrete and abstract topics, including technical discussions in his/her field of specialisation. Can interact with a degree of fluency and spontaneity that makes regular interaction with native speakers quite possible without strain for either party. Can produce clear, detailed text on a wide range of subjects and explain a viewpoint on a topical issue giving the advantages and disadvantages of various options. |
|  | **B1** | Can understand the main points of clear standard input on familiar matters regularly encountered in work, school, leisure, etc. Can deal with most situations likely to arise whilst travelling in an area where the language is spoken. Can produce simple connected text on topics which are familiar or of personal interest. Can describe experiences and events, dreams, hopes and ambitions and briefly give reasons and explanations for opinions and plans. |
| **Basic User** | **A2** | Can understand sentences and frequently used expressions related to areas of most immediate relevance (e.g. very basic personal and family information, shopping, local geography, employment). Can communicate in simple and routine tasks requiring a simple and direct exchange of information on familiar and routine matters. Can describe in simple terms aspects of his/her background, immediate environment and matters in areas of immediate need. |
|  | **A1** | Can understand and use familiar everyday expressions and very basic phrases aimed at the satisfaction of needs of a concrete type. Can introduce him/herself and others and can ask and answer questions about personal details such as where he/she lives, people he/she knows and things he/she has. Can interact in a simple way provided the other person talks slowly and clearly and is prepared to help. |

<!-- el:end id=cefr2001_table_1_common_reference_levels_global_scale -->
""".strip()

    t2 = """
<!-- el:start type=table id=cefr2001_table_2_self_assessment_grid page=35 -->
<!-- db:id=cefr2001_table_2_self_assessment_grid type=table product_tier=base pages=35-36 -->
<!-- book-qa: stitched multipage self-assessment grid (Table 2); one db:id / full grid -->

**Table 2. Common Reference Levels: self-assessment grid** (stitched pages 35–36)

| Skill | A1 | A2 | B1 | B2 | C1 | C2 |
| --- | --- | --- | --- | --- | --- | --- |
| **Listening** | I can recognise familiar words and very basic phrases concerning myself, my family and immediate concrete surroundings when people speak slowly and clearly. | I can understand phrases and the highest frequency vocabulary related to areas of most immediate personal relevance (e.g. very basic personal and family information, shopping, local area, employment). I can catch the main point in short, clear, simple messages and announcements. | I can understand the main points of clear standard speech on familiar matters regularly encountered in work, school, leisure, etc. I can understand the main point of many radio or TV programmes on current affairs or topics of personal or professional interest when the delivery is relatively slow and clear. | I can understand extended speech and lectures and follow even complex lines of argument provided the topic is reasonably familiar. I can understand most TV news and current affairs programmes. I can understand the majority of films in standard dialect. | I can understand extended speech even when it is not clearly structured and when relationships are only implied and not signalled explicitly. I can understand television programmes and films without too much effort. | I have no difficulty in understanding any kind of spoken language, whether live or broadcast, even when delivered at fast native speed, provided I have some time to get familiar with the accent. |
| **Reading** | I can understand familiar names, words and very simple sentences, for example on notices and posters or in catalogues. | I can read very short, simple texts. I can find specific, predictable information in simple everyday material such as advertisements, prospectuses, menus and timetables and I can understand short simple personal letters. | I can understand texts that consist mainly of high frequency everyday or job-related language. I can understand the description of events, feelings and wishes in personal letters. | I can read articles and reports concerned with contemporary problems in which the writers adopt particular attitudes or viewpoints. I can understand contemporary literary prose. | I can understand long and complex factual and literary texts, appreciating distinctions of style. I can understand specialised articles and longer technical instructions, even when they do not relate to my field. | I can read with ease virtually all forms of the written language, including abstract, structurally or linguistically complex texts such as manuals, specialised articles and literary works. |
| **Spoken Interaction** | I can interact in a simple way provided the other person is prepared to repeat or rephrase things at a slower rate of speech and help me formulate what I'm trying to say. I can ask and answer simple questions in areas of immediate need or on very familiar topics. | I can communicate in simple and routine tasks requiring a simple and direct exchange of information on familiar topics and activities. I can handle very short social exchanges, even though I can't usually understand enough to keep the conversation going myself. | I can deal with most situations likely to arise whilst travelling in an area where the language is spoken. I can enter unprepared into conversation on topics that are familiar, of personal interest or pertinent to everyday life (e.g. family, hobbies, work, travel and current events). | I can interact with a degree of fluency and spontaneity that makes regular interaction with native speakers quite possible. I can take an active part in discussion in familiar contexts, accounting for and sustaining my views. | I can express myself fluently and spontaneously without much obvious searching for expressions. I can use language flexibly and effectively for social and professional purposes. I can formulate ideas and opinions with precision and relate my contribution skilfully to those of other speakers. | I can take part effortlessly in any conversation or discussion and have a good familiarity with idiomatic expressions and colloquialisms. I can express myself fluently and convey finer shades of meaning precisely. If I do have a problem I can backtrack and restructure around the difficulty so smoothly that other people are hardly aware of it. |
| **Spoken Production** | I can use simple phrases and sentences to describe where I live and people I know. | I can use a series of phrases and sentences to describe in simple terms my family and other people, living conditions, my educational background and my present or most recent job. | I can connect phrases in a simple way in order to describe experiences and events, my dreams, hopes and ambitions. I can briefly give reasons and explanations for opinions and plans. I can narrate a story or relate the plot of a book or film and describe my reactions. | I can present clear, detailed descriptions on a wide range of subjects related to my field of interest. I can explain a viewpoint on a topical issue giving the advantages and disadvantages of various options. | I can present clear, detailed descriptions of complex subjects integrating sub-themes, developing particular points and rounding off with an appropriate conclusion. | I can present a clear, smoothly flowing description or argument in a style appropriate to the context and with an effective logical structure which helps the recipient to notice and remember significant points. |
| **Writing** | I can write a short, simple postcard, for example sending holiday greetings. I can fill in forms with personal details, for example entering my name, nationality and address on a hotel registration form. | I can write short, simple notes and messages relating to matters in areas of immediate need. I can write a very simple personal letter, for example thanking someone for something. | I can write simple connected text on topics which are familiar or of personal interest. I can write personal letters describing experiences and impressions. | I can write clear, detailed text on a wide range of subjects related to my interests. I can write an essay or report, passing on information or giving reasons in support of or against a particular point of view. I can write letters highlighting the personal significance of events and experiences. | I can express myself in clear, well-structured text, expressing points of view at some length. I can write about complex subjects in a letter, an essay or a report, underlining what I consider to be the salient issues. I can select a style appropriate to the reader in mind. | I can write clear, smoothly flowing text in an appropriate style. I can write complex letters, reports or articles which present a case with an effective logical structure which helps the recipient to notice and remember significant points. I can write summaries and reviews of professional or literary works. |

<!-- el:end id=cefr2001_table_2_self_assessment_grid -->
""".strip()

    # strip previous auto/broken versions of these ids
    for tid in (
        "cefr2001_table_1_common_reference_levels_global_scale",
        "cefr2001_table_2_self_assessment_grid",
    ):
        text = re.sub(
            rf"<!-- el:start type=table id={tid}[^>]*-->.*?<!-- el:end id={tid} -->",
            "",
            text,
            flags=re.S,
        )

    if "Table 1. Common Reference Levels: global scale" in text:
        text = text.replace(
            "Table 1. Common Reference Levels: global scale",
            t1 + "\n\nTable 1. Common Reference Levels: global scale",
            1,
        )
    elif "<!-- page:33 -->" in text:
        text = text.replace("<!-- page:33 -->", t1 + "\n\n<!-- page:33 -->", 1)

    if "Table 2. Common Reference Levels: self-assessment grid" in text:
        text = text.replace(
            "Table 2. Common Reference Levels: self-assessment grid",
            t2 + "\n\nTable 2. Common Reference Levels: self-assessment grid",
            1,
        )
    elif "<!-- page:35 -->" in text:
        text = text.replace("<!-- page:35 -->", t2 + "\n\n<!-- page:35 -->", 1)

    return text


def snapshot(job: str, md_name: str, ver: str = "003") -> None:
    out = ROOT / "output" / job
    vdir = out / "versions" / ver
    vdir.mkdir(parents=True, exist_ok=True)
    src = out / md_name
    shutil.copy2(src, vdir / md_name)
    meta = {
        "version": ver,
        "created": datetime.now(timezone.utc).isoformat(),
        "method": "layout_aware_format_v3",
        "notes": "paragraphs, lists, headers, Unicode tone marks matching PDF",
    }
    (vdir / "VERSION.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    approved = {
        "approved_version": ver,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "path": f"versions/{ver}/{md_name}",
        "product": job,
        "notes": "Format pass v3: real lists/paragraphs/headers; PDF-like intonation marks",
    }
    (out / "APPROVED.json").write_text(json.dumps(approved, indent=2), encoding="utf-8")
    print(f"snapshot {job} -> {ver}", flush=True)


def metrics(path: Path) -> None:
    c = path.read_text(encoding="utf-8")
    print(
        path.name,
        "KB",
        path.stat().st_size // 1024,
        "pages",
        len(re.findall(r"<!-- page:\d+", c)),
        "h2",
        len(re.findall(r"(?m)^## ", c)),
        "bullets",
        len(re.findall(r"(?m)^- ", c)),
        "nums",
        len(re.findall(r"(?m)^\d+\. ", c)),
        "alpha",
        len(re.findall(r"(?m)^[a-z]\) ", c)),
        "tones",
        sum(c.count(TONE[k]) for k in ("LF", "HF", "LR", "HR", "FR")),
    )


def main() -> None:
    print("=== Threshold 1990 (layout) ===", flush=True)
    p = build_book(
        "cefr-threshold-1990",
        "Threshold 1990",
        "Threshold_1990.md",
        use_ocr_fallback=True,
    )
    # Vision App A overrides for nuclear uses — rewrite with Unicode marks
    rewrite_app_a_pages_threshold(p)
    snapshot("cefr-threshold-1990", "Threshold_1990.md")
    metrics(p)

    print("=== Waystage 1990 (OCR+format) ===", flush=True)
    p = build_book(
        "cefr-waystage-1990",
        "Waystage 1990",
        "Waystage_1990.md",
        use_ocr_fallback=True,
    )
    rewrite_app_a_pages_waystage(p)
    snapshot("cefr-waystage-1990", "Waystage_1990.md")
    metrics(p)

    print("=== CEFR EN 2001 (layout) ===", flush=True)
    p = build_book(
        "cefr-en-2001",
        "Common European Framework of Reference for Languages: Learning, teaching, assessment (2001)",
        "CEFR_EN_2001.md",
        use_ocr_fallback=False,
    )
    snapshot("cefr-en-2001", "CEFR_EN_2001.md")
    metrics(p)


def rewrite_app_a_pages_threshold(md_path: Path) -> None:
    """Replace App A nuclear section with Vision-quality structured lists + marks."""
    text = md_path.read_text(encoding="utf-8")
    # Build complete App A nuclear content from Vision (pages 124-129)
    LF, HF, LR, HR, FR = TONE["LF"], TONE["HF"], TONE["LR"], TONE["HR"], TONE["FR"]
    H, S = TONE["HEAD"], TONE["STRESS"]

    app = f"""
<!-- el:start type=prose id=prose_p124_app_a_nuclear page=124 -->
<!-- db:id=threshold_appendix_a type=section product_tier=context pages=121-130 -->

Threshold Level, two points of pitch prominence are of importance, the *nucleus* and the *head*. The last prominent stressed syllable in a tone group is its **nucleus**, which initiates a pitch pattern which continues to the end of the tone group, including any unstressed or stressed but non-prominent syllables that follow. The pattern used is closely related to the language function of the sentence and its grammatical category.

{nuclear_tones_reference_block("threshold")}

At Threshold Level, five nuclear tones should be distinguished:

1. **Low falling** — Marked by a left-to-right diagonal falling mark, **below** the line of writing, placed before the nuclear syllable (**{LF}**). The next syllable is stressed. Its vowel starts on a clear, level low-mid tone. The voice then drops to a low creaky note and remains on this low pitch until the end of the tone group.

2. **High falling** — Similar to the low fall, except that the nuclear vowel starts on a pitch above the mid point. Marked by placing the mark **above** the line of writing (**{HF}**).

3. **Low rising** — Rising mark placed before the nuclear syllable and **below** the line of writing (**{LR}**). Vowel starts on a clear, low level pitch; continuous upward glide, not rising above mid, until the end of the tone group. With a non-prominent “tail”, the nuclear syllable is spoken on a low level pitch and the rise spans the tail.

4. **High rising** — Rising mark **above** the line of writing (**{HR}**). Nuclear vowel starts somewhere between low and mid-level; upward glide extends well above mid.

5. **Falling-rising** — Sequence of 2 and 3. Nuclear vowel starts high-mid and drops to a low creak; upward glide follows, not above mid. V-shaped mark **above** the line before the nuclear syllable (**{FR}**).

Threshold Level learners should be made aware of the following uses of nuclear tones and be stimulated to use them themselves as appropriate.

### 1. Low falling **{LF}** is used

#### a) in declarative sentences

1. for factual statements e.g. identifying, defining, describing and narrating as well as in answers to *wh* questions (which may be short phrases or single words);

   > {H}This is a {LF}door. They {H}drove to {LF}London. {H}Dogs are {LF}animals.

2. for expressing definite agreement or disagreement, firm denials, firm acceptance or rejection of an offer, definite statements of intention, obligation, granting or withholding permission, etc. In general, it indicates an unambiguous certainty.

   > That's {H}quite {LF}right. You {H}must {S}eat your {LF}dinner.

#### b) in interrogative sentences answerable by *yes* or *no*

1. in interrogation, to indicate that an answer is demanded;

   > {H}Have you {S}seen this {S}man be{LF}fore?

2. in requests to indicate that they are in effect orders;

   > {H}May I {S}see your {S}driving {S}licence, {S}please? {S}Will you {H}please be {LF}quiet.

3. when a series of *yes/no* questions is posed in rapid succession;

   > {H}Is it {LF}red? {H}Can you {LF}eat it? {H}Is it a {LF}cabbage?

4. in tag questions, to invite agreement to a statement that is not in doubt;

   > {H}This {S}tastes {LF}nice, | {LF}doesn't it?

5. in choice questions, to indicate that the list of options is closed.

   > {H}Would you prefer {LF}tea | or {LF}coffee?

#### c) in *wh* questions

as a definite request for a piece of information

> {H}Where is the {LF}toilet, {S}please?

#### d) in imperative sentences

1. as a direct order or prohibition;

   > {H}Sit {LF}down. {H}Don't {S}smoke in {LF}here, {S}please.

2. as an instruction;

   > {LF}Push to {H}open the {LF}door.

3. as a strong form of offer.

   > {H}Have {S}one of {S}my ciga{LF}rettes.

### 2. High falling **{HF}** is used

#### a) in declarative sentences

1. in exclamations to indicate surprise, protest, enthusiasm, emphasis or insistence;

   > That's {HF}excellent! You are {HF}hurting me! {H}Fancy {HF}that!

2. to indicate contrast with an element previously mentioned or believed to be in the listener's mind.

   > {HF}No, | Mount {HF}Elburz is the {S}highest {S}mountain in {S}Europe.

#### b) in interrogative sentences, both *yes/no* and *wh*

1. to insist on an answer being given;

   > {H}Did you {HF}post {S}that {S}letter?

2. to indicate surprise or irritation;

   > {H}Are you {HF}still {S}not {S}ready?

3. in rhetorical questions of an exclamatory type, to which no answer is sought;

   > {H}Isn't she {HF}beautiful?

4. in tag questions, to insist on the hearer's agreement to a proposition.

   > I {HF}told {S}you | {HF}didn't I?

#### c) in imperative sentences

1. to insist on an order or prohibition where compliance is in doubt;

   > {HF}Stop it, I {S}say. {H}Don't {HF}listen {S}to him.

2. to indicate the urgency of an instruction (e.g. because of imminent danger);

   > {HF}Stop. {H}Don't {HF}move.

3. to insist on the acceptance of an offer.

   > {H}Do let me {HF}help you.

### 3. Low rising **{LR}** is used

#### a) in declarative sentences

1. (with preceding low pitches) to indicate difference or resentment, guardedness, suspicion;

   > It {S}doesn't {LR}matter. You {S}shouldn't {S}blame {LR}me.

2. (with preceding high pitch) to reassure.

   > There's {H}no {S}need to be {LR}worried.

#### b) in interrogative questions answerable by *yes* or *no*

1. to ask politely for confirmation or disconfirmation (also in tag questions);

   > You're {H}French, {LR}aren't you?

2. to make polite requests and offers;

   > {H}Would you {S}please {S}open the {LR}window? {H}Can I do {S}anything to {LR}help?

3. in choice questions, to indicate that the list is open.

   > {H}Would you {S}like {LR}tea | or {LR}coffee | or {S}something {LR}stronger?

#### c) in *wh* questions

1. to indicate polite interest rather than a need for information;

   > {H}Where are you {S}spending your {LR}holidays?

2. to avoid the appearance of interrogation or peremptory questioning.

   > {H}What are you {LR}doing {S}there?

#### d) in imperative sentences

for gentle commands, especially to children, hospital patients, etc.

> {H}Come and {S}have your {S}nice {LR}bath. {H}Just {S}drink this {LR}medicine {S}nicely.

### 4. High rising **{HR}** is used

#### a) in declarative sentences (including isolated phrases and words used instead of full sentences)

1. to convert a statement into a question;

   > You were {S}born in {HR}Scotland?

2. to query what someone has said.

   > You {S}say you're {HR}thirsty?

#### b) in interrogative questions answerable by *yes* or *no*

1. (with preceding low pitch) to indicate a casual enquiry;

   > (Would you) {S}care for a {HR}sandwich?

2. to repeat a question (with change of 1st and 2nd person) before answering.

   > A {HR}sandwich? Would I {S}care for a {HR}sandwich?

#### c) in *wh* questions

1. to repeat a question (with change of 1st and 2nd person) before answering;

   > ({H}Where do you {LR}live?) {S}Where do I {HR}live?

2. (with the *wh* word as nucleus) to ask for repetition of information given but not heard (or understood).

   > (He {S}lives in (unintelligible).)  
   > He {S}lives {HR}where? {H}Where does he {S}live?

#### d) in imperative sentences

to repeat an order, instruction or offer while deciding whether or how to comply

> ({H}Sit {LR}down, {S}please.) {S}Sit {HR}down? | {H}Why {LR}not?

### 5. Falling–rising **{FR}** is used

#### a) in declarative sentences to convey various implications

1. warnings;

   > That {S}jug is {FR}hot!

2. corrections;

   > Her {S}dress {H}is {FR}green, you know. | It {H}isn't {FR}blue.

3. demurral and limited agreement (with implied disagreement on the major issue);

   > I {H}don't {S}know if I a{S}gree with {FR}that.  
   > {FR}Yes, | he {H}is an {FR}active {S}person.

4. mental reservations in making promises;

   > {FR}Yes, | I {FR}will be {S}good. || At {S}least, I'll {FR}try.

5. uncertainty and hesitation;

   > {S}Yes {FR}possibly. | I {H}can't be {FR}certain.

6. to soften the effect of bad news, conflict of views, etc.;

   > You {H}haven't {S}done very {FR}well, I'm a{S}fraid.  
   > You're {FR}wrong, you {S}know.

7. (with attached tag questions) anxious query;

   > You {H}do {FR}love me, {S}don't you?

8. discouragement of a possible course of action;

   > You can {H}go to the {S}cinema if you {FR}like.

9. tentative advice;

   > If {H}I were {FR}you …

10. implying that something has been left unsaid, which contrasts with, or contradicts what has been overtly stated;

    > Your o{S}pinion is {FR}interesting. (implying: but I {H}don't a{LR}gree with it).

11. to query what has been said, implying that it is mistaken or untrue.

    > {H}Seven {S}eights are {S}fifty {FR}four?

#### b) in interrogative questions answered by *yes* or *no*

1. to add a note of warning or doubt;

   > Are you {FR}sure you {S}locked the {S}door?

2. when giving the answer to the question may be unwelcome to the person giving it.

   > {H}Have you {S}thought what might {S}happen if you {FR}did?

#### c) in *wh* questions

1. to repeat a question, focusing on the key issue in contrast with other possible issues;

   > {H}What did I {S}do on {FR}Friday of {S}last {S}week?

2. (with the *wh* word as nucleus) to query a statement, implying scepticism regarding the element queried by the *wh* word employed.

   > {FR}Where did he {S}find your {S}purse?

#### d) in imperative sentences

1. for issuing warnings rather than commands or instructions;

   > {H}Watch where you're {FR}going. {H}Don't {S}try to {S}pull the {FR}door {S}open.

2. (with the imperative as nucleus) for pleading.

   > {FR}Do {S}try to be a {S}little more {S}careful.

Every tone group contains a **nucleus**. Many short utterances will comprise a single tone group, containing only one prominent syllable, which is then the nucleus of the tone group. Where there is more than one prominent syllable, the last of these is the nucleus and the first is the **head**. The head is usually marked by a jump up in pitch to a high-mid level and by an upright mark before the syllable, **above** the line (**{H}**).

Stressed non-prominent syllables are marked by a mid-height dot (**{S}**). Minor tone groups end with **|**; major tone groups with **||**.

| Pattern | Non-final | Final | Example |
| --- | --- | --- | --- |
| Unemphatic, non-contrastive | low rising | low falling | {H}When you {S}see John \\| {H}tell him to {LF}phone me.\\|\\| |
| Contrasting | falling-rising | high falling | But {H}when you see {FR}Harry \\| {H}tell him I've {S}left the {HF}country.\\|\\| |
| Main statement + modifier | low falling | low rising | I'm {H}leaving for {HF}Germany \\| on {LR}Friday.\\|\\| |
| Main statement + supplement | low fall | low fall | He {S}lives in {LF}London \\| in a {H}semi-de{S}tached {S}house in {LF}Peckham.\\|\\| |

In all cases of apposition, the same nuclear tone is used for both tone groups. The word *too* similarly repeats the tone of its antecedent nucleus.

> John {LF}Smith, | a com{LF}puter {S}programmer | {S}lives in {LF}Cambridge, | a university {LF}city.||  
> His {H}brother {S}lives {LF}there, | {LF}too.||

**Note.** In this document, **||** is omitted at the end of examples consisting of a single sentence.

<!-- el:end id=prose_p124_app_a_nuclear -->
"""

    # Replace pages 124-130 body: from after page:123 through page:130
    # Strategy: find <!-- page:123 --> ... replace content until <!-- page:130 -->
    m123 = re.search(r"<!-- page:123 -->", text)
    m130 = re.search(r"<!-- page:130 -->", text)
    if m123 and m130:
        # Keep page markers structure: insert app content as pages 124-130 block
        # Replace from first content after 123 to end of 130 section
        # Actually replace from start of p124 content through p130 marker
        start = m123.end()
        # find page:130 end - keep marker
        new = (
            text[:start]
            + "\n\n"
            + app
            + "\n\n*Page **124***\n\n<!-- page:124 -->\n\n"
            + "*Page **125***\n\n<!-- page:125 -->\n\n"
            + "*Page **126***\n\n<!-- page:126 -->\n\n"
            + "*Page **127***\n\n<!-- page:127 -->\n\n"
            + "*Page **128***\n\n<!-- page:128 -->\n\n"
            + "*Page **129***\n\n<!-- page:129 -->\n\n"
            + text[m130.start() :]
        )
        # Remove duplicate garbage between old 124-129 if still present
        # The slice above drops old 124-129 content (between 123 and 130) — good.
        text = new
        # But we may have left old p130 body - ok
    else:
        text = inject_nuclear_block(text, "threshold", "five nuclear tones")

    text = apply_tone_symbol_pass(text)
    md_path.write_text(text, encoding="utf-8")
    print("rewrote Threshold App A nuclear section", flush=True)


def rewrite_app_a_pages_waystage(md_path: Path) -> None:
    text = md_path.read_text(encoding="utf-8")
    LF, HF, LR, HR, FR = TONE["LF"], TONE["HF"], TONE["LR"], TONE["HR"], TONE["FR"]
    H, S = TONE["HEAD"], TONE["STRESS"]

    app = f"""
<!-- el:start type=prose id=prose_p077_app_a_nuclear page=77 -->
<!-- db:id=waystage_appendix_a type=section product_tier=context pages=68-80 -->

At Waystage, two points of pitch prominence are of importance, the *nucleus* and the *head*. The last prominent stressed syllable in a tone group is its **nucleus**, which initiates a pitch pattern which continues to the end of the tone group, including any unstressed or stressed but non-prominent syllables that follow. The pattern used is closely related to the language function of the sentence and its grammatical category.

{nuclear_tones_reference_block("waystage")}

At Waystage, five nuclear tones should be distinguished:

1. **Low falling** — Falling mark **below** the line before the nuclear syllable (**{LF}**). Starts low-mid; drops to low creak; stays low to end of tone group.

2. **High falling** — Same falling mark **above** the line (**{HF}**). Nuclear vowel starts above mid.

3. **Low rising** — Rising mark **below** the line (**{LR}**). Starts low; upward glide not above mid; rise may span the tail.

4. **High rising** — Rising mark **above** the line (**{HR}**). Starts between low and mid; glide well above mid.

5. **Falling-rising** — V-shaped mark **above** the line (**{FR}**). High-mid → low creak → upward glide not above mid.

Waystage learners should be made aware of the following uses and be stimulated to use them as appropriate.

### 1. Low falling **{LF}** is used

#### a) in declarative sentences

1. for factual statements e.g. identifying, defining, describing and narrating as well as in answers to *wh* questions;

   > {H}This is a {LF}door. They {H}drove to {LF}London. {H}Dogs are {LF}animals.

2. for expressing definite agreement or disagreement, firm denials, firm acceptance or rejection of an offer, definite statements of intention, obligation, granting or withholding permission, etc. In general, it indicates an unambiguous certainty.

   > That's {H}quite {LF}right. You {H}must {S}eat your {LF}dinner.

#### b) in interrogative sentences answerable by *yes* or *no*

1. in tag questions, to invite agreement to a statement that is not in doubt;

   > {H}This {S}tastes {LF}nice, | {LF}doesn't it?

2. in choice questions, to indicate that the list of options is closed.

   > {H}Would you prefer {LF}tea | or {LF}coffee?

#### c) in *wh* questions

as a definite request for a piece of information

> {H}Where is the {LF}toilet, {S}please?

#### d) in imperative sentences

1. as a direct order or prohibition;

   > {H}Sit {LF}down. {H}Don't {S}smoke in {S}here, {S}please.

2. as an instruction;

   > {LF}Push | to {H}open the {LF}door.

3. as a strong form of offer.

   > {H}Have {S}one of {S}my ciga{LF}rettes.

### 2. High falling **{HF}** is used

#### a) in declarative sentences

1. in exclamations to indicate surprise, protest, enthusiasm, emphasis or insistence;

   > That's {HF}excellent! You are {HF}hurting me! {H}Fancy {HF}that!

2. to indicate contrast with an element previously mentioned or believed to be in the listener's mind.

   > {HF}Elbruz is the {S}highest {S}mountain in {S}Europe (not Mont Blanc).

#### b) in rhetorical questions of an exclamatory type

> {H}Isn't she {HF}beautiful?

#### c) in imperative sentences

to indicate the urgency of an instruction (e.g. because of imminent danger)

> {HF}Stop. {H}Don't {HF}move.

### 3. Low rising **{LR}** is used

#### a) in interrogative questions answerable by *yes* or *no*

1. to ask politely for confirmation or disconfirmation (also in tag questions);

   > You're {H}French, | {LR}aren't you?

2. to make polite requests and offers;

   > {H}Would you {S}please {S}open the {LR}window? {H}Can I do {S}anything to {LR}help?

3. in choice questions, to indicate that the list is open.

   > {H}Would you {S}like {LR}tea | or {LR}coffee | or {H}something {LR}stronger?

### 4. High rising **{HR}** is used

#### a) in declarative sentences

1. to convert a statement into a question;

   > You were {S}born in {HR}Scotland?

2. to query what someone has said.

   > You {S}say you're {HR}thirsty?

#### b) with the *wh* word as nucleus

to ask for repetition of information given but not heard (or understood)

> (He {S}lives in (unintelligible).)  
> He {S}lives {HR}where? {H}Where does he {S}live?

### 5. Falling–rising **{FR}** is used

#### a) in declarative sentences to convey various implications

1. warnings;

   > That {S}jug is {FR}hot!

2. corrections;

   > Her {S}dress {H}isn't {FR}blue, | it's {FR}green.

3. implying that something has been left unsaid, which contrasts with, or contradicts what has been overtly stated.

   > Your o{S}pinion is {FR}interesting. (implying: but I {H}don't {LF}agree with it)

#### b) in imperative sentences

for issuing warnings rather than commands or instructions

> {H}Watch where you're {FR}going. {H}Don't {S}try to {FR}pull the {S}door {S}open.

Every tone group contains a **nucleus**. Where there is more than one prominent syllable, the last is the nucleus and the first is the **head** (mark **{H}** above the line). Stressed non-prominent syllables use **{S}**.

<!-- el:end id=prose_p077_app_a_nuclear -->
"""

    m76 = re.search(r"<!-- page:76 -->", text)
    m80 = re.search(r"<!-- page:80 -->", text)
    if m76 and m80:
        text = (
            text[: m76.end()]
            + "\n\n"
            + app
            + "\n\n*Page **77***\n\n<!-- page:77 -->\n\n"
            + "*Page **78***\n\n<!-- page:78 -->\n\n"
            + "*Page **79***\n\n<!-- page:79 -->\n\n"
            + text[m80.start() :]
        )
    else:
        text = inject_nuclear_block(text, "waystage", "five nuclear tones")

    text = apply_tone_symbol_pass(text)
    md_path.write_text(text, encoding="utf-8")
    print("rewrote Waystage App A nuclear section", flush=True)


if __name__ == "__main__":
    main()
