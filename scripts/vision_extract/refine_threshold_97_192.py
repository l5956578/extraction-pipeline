#!/usr/bin/env python3
"""Second-pass quality refine for Threshold page_overrides 97–192.

Focus: headers vs lists, multi-line indexes, grammar outline cleanup,
blank pages 191–192, prose chapter structure from Vision samples.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image
import pytesseract

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "work" / "cefr-threshold-1990"
OCR = WORK / "page_ocr"
RENDERS = WORK / "page_renders"
OUT = WORK / "page_overrides"

LF, HF, LR, HR, FR = "\u02ce", "\u02cb", "\u02cf", "\u02ca", "\u02c7"
HEAD, STRESS = "\u02c8", "\u00b7"


def wrap(pnum: int, body: str, extra: str = "") -> str:
    body = body.strip() + "\n"
    pid = f"prose_p{pnum:03d}"
    bits = [
        f"<!-- el:start type=prose id={pid} page={pnum} -->",
        f"<!-- vision: Threshold PDF page {pnum} -->",
    ]
    if extra:
        bits.append(extra)
    bits.append("")
    bits.append(body.rstrip())
    bits.append("")
    bits.append(f"<!-- el:end id={pid} -->")
    bits.append("")
    return "\n".join(bits)


def clean(t: str) -> str:
    t = t.replace("\u00ad", "").replace("ﬁ", "fi").replace("ﬂ", "fl")
    t = t.replace("satisfylng", "satisfying")
    t = t.replace("middleclass", "middle-class")
    t = t.replace("adoped", "adopted")
    t = t.replace("AngleSaxon", "Anglo-Saxon")
    t = t.replace("openended", "open-ended")
    t = t.replace("temporaryvisitors", "temporary visitors")
    t = t.replace("useofcapitals", "use of capitals")
    t = t.replace("Ina ", "In a ")
    t = t.replace("Asa ", "As a ")
    t = t.replace("asina ", "as in a ")
    t = t.replace("ina ", "in a ")
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()


def is_chrome(t: str) -> bool:
    s = t.strip()
    if not s or re.match(r"^\d{1,3}$", s):
        return True
    if re.match(r"^([A-Z]\s+){3,}", s):
        return True
    if re.match(r"^\d{1,3}\s+([A-Z]\s+){2,}", s):
        return True
    if re.match(r"^(APPENDIX|SUBJECT INDEX|PRONUNCIATION)\b", s, re.I):
        return True
    if re.match(r"^\d{1,3}\s+\d{1,2}\s+[A-Z]", s):  # "104 12 COMPENSATION"
        return True
    if re.match(r"^\d{1,3}\s+(1[0-6]|[0-9])\s+[A-Z]", s):
        return True
    return False


def ocr_lines(pnum: int) -> list[str]:
    p = OCR / f"page_{pnum:03d}.txt"
    if p.exists():
        raw = p.read_text(encoding="utf-8", errors="replace")
        if len(raw.strip()) > 40:
            return [clean(x) for x in raw.splitlines()]
    im = Image.open(RENDERS / f"page_{pnum:03d}.png")
    t = pytesseract.image_to_string(im, config="--psm 6")
    return [clean(x) for x in t.splitlines()]


def col_ocr(pnum: int, mid: float = 0.50, top: float = 0.08) -> tuple[str, str]:
    im = Image.open(RENDERS / f"page_{pnum:03d}.png")
    w, h = im.size
    m = int(w * mid)
    t0 = int(h * top)
    bot = h - int(h * 0.03)
    L = im.crop((int(w * 0.05), t0, m - 6, bot))
    R = im.crop((m - 6, t0, w - int(w * 0.05), bot))
    return (
        pytesseract.image_to_string(L, config="--psm 6"),
        pytesseract.image_to_string(R, config="--psm 6"),
    )


# ---------- Prose with I/II and numbered lists ----------

def format_prose(pnum: int) -> str:
    lines = ocr_lines(pnum)
    out: list[str] = []
    para: list[str] = []

    def flush() -> None:
        nonlocal para
        if not para:
            return
        t = " ".join(para)
        t = re.sub(r"\s+", " ", t)
        t = re.sub(r"(\w)-\s+(\w)", r"\1\2", t)
        # split glued numbered items: "…list. 2 deduce" → break
        t = re.sub(r"(?<=[.;:])\s+(\d{1,2})\s+(?=[a-z])", r"\n\n\1. ", t)
        if t:
            # if we introduced breaks for numbered items
            for part in t.split("\n\n"):
                part = part.strip()
                if re.match(r"^\d{1,2}\.\s+", part):
                    out.append(part)
                else:
                    out.append(part)
                out.append("")
        para = []

    for raw in lines:
        t = raw
        if is_chrome(t):
            continue
        t = re.sub(r"^\d{1,3}\s+(?=[A-Z*•IVX])", "", t).strip()
        if not t or is_chrome(t):
            continue

        # Chapter title
        m = re.match(
            r"^(1[0-6]|[89])\s+(Writing|Sociocultural competence|Compensation strategies|"
            r"Learning to learn|Degree of skill|Dealing with texts: reading and listening|"
            r"Reading and listening|Verbal exchange patterns)\b(.*)$",
            t,
            re.I,
        )
        if m:
            flush()
            out.append(f"## {m.group(1)} {m.group(2)}")
            out.append("")
            rest = (m.group(3) or "").strip()
            if rest:
                para.append(rest)
            continue

        # Roman major sections: I As a reader / II Social conventions
        m = re.match(r"^(I{1,3}|IV|V|VI|VII|VIII|IX|X)\s+(.+)$", t)
        if m and len(t) < 90:
            flush()
            out.append(f"### {m.group(1)} {m.group(2).strip()}")
            out.append("")
            continue

        # Numbered section heads: "3 interpersonal relations" / "4 major values"
        m = re.match(r"^(\d{1,2})\s+([a-z].{2,50})$", t)
        if m and not t.endswith((".", ";", ",")) and len(t.split()) <= 10:
            flush()
            out.append(f"#### {m.group(1)} {m.group(2)}")
            out.append("")
            continue
        m = re.match(r"^(\d{1,2})\s+([A-Z][a-z].{2,50})$", t)
        if m and not t.endswith((".", ";", ",")) and len(t.split()) <= 10:
            # "1 non-linguistic" style or "3 The present"
            rest = m.group(2)
            if rest[0].islower() or len(rest.split()) <= 6:
                flush()
                out.append(f"#### {m.group(1)} {rest}")
                out.append("")
                continue

        # lettered sub: a) body language
        if re.match(r"^[a-z]\)\s+\S", t):
            flush()
            out.append(f"**{t}**" if len(t) < 40 else t)
            if len(t) < 40:
                out.append("")
            continue

        # numbered list item starting line: "1 deduce" / "2 deduce"
        m = re.match(r"^(\d{1,2})\s+([a-z].+)$", t)
        if m:
            flush()
            out.append(f"{m.group(1)}. {m.group(2)}")
            out.append("")
            continue

        # bullets
        if re.match(r"^[*•·▪]\s*", t) or t.startswith("*"):
            flush()
            item = re.sub(r"^[*•·▪]\s*", "", t).lstrip("* ").strip()
            if item:
                out.append(f"- {item}")
            continue
        if re.match(r"^[-–—]\s+\S", t) and not re.match(r"^[-–—]\s+(and|or|but)\b", t, re.I):
            flush()
            out.append(f"- {re.sub(r'^[-–—]\s+', '', t)}")
            continue

        # continuation of numbered item
        if out and re.match(r"^\d+\.\s", out[-2] if len(out) >= 2 and out[-1] == "" else (out[-1] if out else "")):
            prev_idx = -2 if out[-1] == "" else -1
            if t and t[0].islower():
                if out[prev_idx] == "":
                    # shouldn't
                    pass
                target = -2 if out[-1] == "" else -1
                if out[-1] == "":
                    out.pop()
                out[-1] = out[-1] + " " + t
                out.append("")
                continue

        if para and t and t[0].islower():
            para.append(t)
            continue
        flush()
        para.append(t)

    flush()
    body = "\n".join(out).strip()
    body = re.sub(r"\n{3,}", "\n\n", body)
    # quotes
    body = body.replace("`", "'")
    return body


# ---------- Word index ----------

WORD_ENTRY = re.compile(
    r"^([A-Za-z][A-Za-z'’\-\(\)/\.]*(?:\s+\([^)]+\))?|"
    r"[A-Za-z]\.[A-Za-z]\.?|"
    r"a\.m\.|p\.m\.|o'clock)"
    r"(?:\s+(?:n|vb|adj|adv|prep|pron|conj|art|int|det|num|phr)(?:\s+and\s+(?:n|vb|adj|adv|prep|pron))*)?"
    r"(?::|\s*$)"
)


def format_word_col(text: str) -> list[str]:
    out: list[str] = []
    buf = ""
    for raw in text.splitlines():
        t = clean(raw)
        if not t or is_chrome(t):
            continue
        if re.match(r"^Appendix", t, re.I):
            continue
        if re.match(r"^(Word index|ord index)$", t, re.I):
            continue
        # letter header A [ei] or just A
        if re.match(r"^[A-Z](\s*[\[\(].*)?$", t) and len(t) < 25:
            if buf:
                out.append(f"- {buf}")
                buf = ""
            out.append("")
            out.append(f"### {t}")
            out.append("")
            continue
        # continuation refs only
        if buf and (re.match(r"^[\d,\.\s]+$", t) or (re.match(r"^\d", t) and ":" not in t and not re.match(r"^[a-zA-Z]{3,}", t))):
            buf = buf.rstrip(",") + ", " + t.lstrip(", ")
            continue
        # new entry?
        if re.match(r"^[A-Za-z'’]", t) and (":" in t or re.search(r"\b(n|vb|adj|adv|prep|pron|conj|art|int)\b", t)):
            if buf:
                out.append(f"- {buf}")
            buf = t
            continue
        if re.match(r"^[A-Za-z'’].+:", t):
            if buf:
                out.append(f"- {buf}")
            buf = t
            continue
        # short lemma without colon yet
        if re.match(r"^[a-zA-Z].{0,40}$", t) and not re.search(r"\d{1,2}\.\d", t):
            if buf:
                out.append(f"- {buf}")
            buf = t
            continue
        if buf:
            buf = buf + " " + t
        else:
            out.append(f"- {t}")
    if buf:
        out.append(f"- {buf}")
    return out


def format_word_page(pnum: int) -> str:
    L, R = col_ocr(pnum, top=0.09 if pnum > 163 else 0.12)
    parts: list[str] = []
    if pnum == 163:
        parts += ["## Appendix C — Word index", ""]
    for col in (L, R):
        parts.extend(format_word_col(col))
    body = "\n".join(parts)
    body = re.sub(r"\n{3,}", "\n\n", body)
    # drop garbage single-char bullets
    body = re.sub(r"(?m)^- [A-Za-z]{1,2}$\n?", "", body)
    body = re.sub(r"(?m)^- Aci\n?", "### A [eɪ]\n\n", body)
    return body.strip()


# ---------- Subject index ----------

def format_subject_col(text: str) -> list[str]:
    out: list[str] = []
    for raw in text.splitlines():
        t = clean(raw)
        if not t or is_chrome(t):
            continue
        if re.match(r"^Appendix", t, re.I):
            continue
        if re.match(r"^Subject index", t, re.I):
            continue
        if re.match(r"^Index of language", t, re.I):
            continue
        if re.match(r"^In the following", t, re.I):
            continue
        if re.match(r"^(chapters referred|language functions|beginning with)", t, re.I):
            continue
        if re.match(r"^categories$", t, re.I):
            continue
        # sub-entry heuristics: lower start or known verbs
        if t[0].islower() or re.match(
            r"^(enquiring|expressing|accepting|offering|physical|cost|residential|types|"
            r"while|customer|friend|stranger|someone|for |on |denying|foreign|private|"
            r"public|in |with |asking|order|reference|action)\b",
            t,
            re.I,
        ):
            # continuation of previous sub?
            if out and out[-1].startswith("  - ") and not re.search(r"\d+\.\d+", out[-1]) and re.search(r"\d", t):
                out[-1] = out[-1] + " " + t
            else:
                out.append(f"  - {t}")
        else:
            # main headword
            if re.search(r"\d+\.\d+", t):
                out.append(f"- {t}")
            else:
                out.append(f"- **{t}**")
    return out


def format_subject_page(pnum: int) -> str:
    top = 0.16 if pnum == 184 else 0.08
    L, R = col_ocr(pnum, top=top)
    parts: list[str] = []
    if pnum == 184:
        parts += [
            "## Appendix D — Subject index",
            "",
            "### Index of language functions and notional categories",
            "",
            "In the following index numbers refer to chapters and items or sections. "
            "The chapters referred to are 5, 6 and 7. All references beginning with 5 are to "
            "language functions, those beginning with 6 to general notions and those "
            "beginning with 7 are references to themes or sub-themes.",
            "",
        ]
    for col in (L, R):
        parts.extend(format_subject_col(col))
    body = "\n".join(parts)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


# ---------- Grammar ----------

def format_grammar_page(pnum: int) -> str:
    L, R = col_ocr(pnum, top=0.10 if pnum > 132 else 0.14)
    parts: list[str] = []
    if pnum == 132:
        parts += [
            "The summary is not conceived as a teaching or reference grammar of "
            "English, but as a guide to the resources to which a learner has access as "
            "a result of learning English to *Threshold Level*.",
            "",
            "We trust that with a little experience users will find that the systematic "
            "presentation enables reference to be made quickly and efficiently as a "
            "further aid to curricular planning and course construction.",
            "",
        ]

    def parse_col(text: str) -> list[str]:
        o: list[str] = []
        para: list[str] = []

        def fl() -> None:
            nonlocal para
            if para:
                t = " ".join(para)
                t = re.sub(r"\s+", " ", t)
                t = re.sub(r"(\w)-\s+(\w)", r"\1\2", t)
                # drop tesseract garbage fragments that are too short / broken
                if len(t) > 8 and not re.match(r"^[a-z]{1,3}$", t):
                    o.append(t)
                    o.append("")
                para = []

        for raw in text.splitlines():
            t = clean(raw)
            if not t or is_chrome(t):
                continue
            if re.match(r"^Appendix", t, re.I):
                continue
            if re.match(r"^\.+$", t) or set(t) <= set(".·• "):
                continue
            # strip trailing OCR junk punctuation alone
            if re.match(r"^[;:,\|\\]+$", t):
                continue

            m = re.match(r"^([A-D])\s+([A-Za-z].{2,40})$", t)
            if m and not re.match(r"^[A-D]\d", t):
                fl()
                o.append(f"## {m.group(1)} {m.group(2).strip()}")
                o.append("")
                continue

            m = re.match(r"^([A-D]\d+)\s+(.+)$", t)
            if m and len(t) < 70:
                fl()
                o.append(f"### {m.group(1)} {m.group(2).strip()}")
                o.append("")
                continue

            m = re.match(r"^(\d+(?:\.\d+){0,5})\s+(.+)$", t)
            if m:
                fl()
                num, rest = m.group(1), m.group(2).strip()
                # remove trailing OCR junk
                rest = re.sub(r"\s*[;|\\]+\s*$", "", rest)
                depth = min(num.count(".") + 3, 6)
                # heading-like
                if len(rest) < 75 and (
                    rest[0:1].isupper()
                    or re.match(
                        r"^(proper|common|regular|irregular|abstract|names|types|nouns|verbs|"
                        r"adjectives|adverbs|prepositions|pronouns|articles|forms|usage|"
                        r"number|gender|case|comparison|tense|aspect|voice|modal|interrogative|"
                        r"negative|passive|infinitive|gerund|participle|clause|phrase|sentence|"
                        r"countable|uncountable|mass|verbal|-es |s added)",
                        rest,
                        re.I,
                    )
                ):
                    o.append("#" * depth + f" {num} {rest}")
                    o.append("")
                else:
                    o.append(f"- **{num}** {rest}")
                continue

            # plural ending table rows
            if re.match(r"^(s|x|z|sh|ch|o|y|f|fe)\b", t, re.I) and len(t) < 55:
                fl()
                o.append(f"  - `{t}`")
                continue

            if para and t[0:1].islower():
                para.append(t)
            else:
                fl()
                # skip pure garbage OCR scraps from column bleed
                if len(t) < 4 and not re.match(r"^\d", t):
                    continue
                para.append(t)
        fl()
        return o

    parts.extend(parse_col(L))
    parts.extend(parse_col(R))
    body = "\n".join(parts)
    body = re.sub(r"\n{3,}", "\n\n", body)
    # remove lines that are mostly OCR garbage (random short tokens)
    cleaned_lines = []
    for ln in body.splitlines():
        if re.match(r"^(English, but as|We trust that with a little experiet|presentation enables|further aid to curricular|aresult of learning)", ln):
            continue
        if re.search(r"\b(reso |experiet|Thre$|L phonetic|ofanunfamiliar)\b", ln):
            continue
        cleaned_lines.append(ln)
    return "\n".join(cleaned_lines).strip()


# ---------- App B intro ----------

def format_app_b_intro() -> str:
    lines = ocr_lines(131)
    body_parts: list[str] = ["## Appendix B — Grammatical summary", ""]
    para: list[str] = []
    for t in lines:
        if is_chrome(t):
            continue
        t = re.sub(r"^\d{1,3}\s+", "", t)
        if re.match(r"^Appendix\s*B", t, re.I):
            continue
        if re.match(r"^Grammatical\s*summary$", t, re.I):
            continue
        if not t:
            if para:
                body_parts.append(" ".join(para))
                body_parts.append("")
                para = []
            continue
        if para and t[0].islower():
            para.append(t)
        else:
            if para:
                body_parts.append(" ".join(para))
                body_parts.append("")
            para = [t]
    if para:
        body_parts.append(" ".join(para))
    body = "\n".join(body_parts)
    body = re.sub(r"\s+", " ", body) if False else body
    body = re.sub(r"\n{3,}", "\n\n", body)
    # fix symbol reference
    body = body.replace("The symbol @", "The symbol ●")
    body = body.replace("symbol @", "symbol ●")
    body = body.replace("symbol @ ", "symbol ● ")
    return body.strip()


def main() -> None:
    start, end = 97, 192
    if len(sys.argv) >= 3:
        start, end = int(sys.argv[1]), int(sys.argv[2])

    for pnum in range(start, end + 1):
        print(f"  refine {pnum}", flush=True)
        dest = OUT / f"page_{pnum:03d}.md"

        # Keep hand-crafted App A (Unicode) unless force
        if 121 <= pnum <= 130:
            # ensure vision tag + Unicode already present
            existing = dest.read_text(encoding="utf-8") if dest.exists() else ""
            if "\u02ce" in existing or "Five nuclear tones" in existing:
                if "<!-- vision: Threshold PDF page" not in existing:
                    existing = existing.replace(
                        f"id=prose_p{pnum:03d} page={pnum} -->",
                        f"id=prose_p{pnum:03d} page={pnum} -->\n<!-- vision: Threshold PDF page {pnum} -->",
                        1,
                    )
                    dest.write_text(existing, encoding="utf-8")
                continue

        if pnum in (191, 192):
            dest.write_text(
                wrap(pnum, "<!-- empty / blank page -->", extra="<!-- vision-verified blank -->"),
                encoding="utf-8",
            )
            continue

        if pnum == 131:
            body = format_app_b_intro()
        elif 132 <= pnum <= 162:
            body = format_grammar_page(pnum)
        elif 163 <= pnum <= 183:
            body = format_word_page(pnum)
        elif 184 <= pnum <= 190:
            body = format_subject_page(pnum)
        else:
            body = format_prose(pnum)
            # hand polish known pages from Vision
            if pnum == 97:
                body = (
                    "#### 3\n\n"
                    "The present specification is the specification of an objective, not of "
                    "the content of a learning programme. This is why, apart from those "
                    "listed in the first paragraph of this chapter, no mention is made in "
                    "this chapter of further techniques that may be usefully employed "
                    "towards achieving understanding of a text. These techniques, which "
                    "include segmentation, the establishment of links between segments, "
                    "underlining, note-taking and note-making, etc., may be profitably "
                    "practised in a learning programme designed to enable learners to do "
                    "what is specified in our objective, but they are not presented as "
                    "components of the objective itself because the extent to which each "
                    "individual learner makes use of them in satisfying the requirements "
                    "of the objective is subject to personal variation. In the same way, "
                    "such strategies as inferencing, hypothesising from proper names, "
                    "international words, cognate words in the learner's mother tongue "
                    "or in other languages he or she may have learnt, are all too variable "
                    "to be specified in a general performance objective. However, an "
                    "awareness of such techniques and strategies, and experience in their "
                    "use, form an important aspect of learning to learn (cf. Chapter 13)."
                )
            if pnum == 98:
                from format_threshold_97_192 import polish_writing_pages

                body = polish_writing_pages(98, body)
            if pnum == 99:
                from format_threshold_97_192 import polish_writing_pages

                body = polish_writing_pages(99, body)
            if pnum == 100 and not body.startswith("##"):
                body = "## 11 Sociocultural competence\n\n" + body
            if pnum == 110:
                body = format_prose(pnum)
                if not body.startswith("##") and "Compensation" not in body[:80]:
                    body = body  # already has structure from roman I/II

        dest.write_text(wrap(pnum, body), encoding="utf-8")

    print("refine done", flush=True)


if __name__ == "__main__":
    # allow importing polish helper
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
