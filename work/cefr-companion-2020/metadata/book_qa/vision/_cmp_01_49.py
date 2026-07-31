"""Compare PDF text vs MD slices for pages 1-49 (book vision QA helpers)."""
from __future__ import annotations

import re
from pathlib import Path

try:
    import fitz
except ImportError:
    import pymupdf as fitz

ROOT = Path(__file__).resolve().parents[5]
MD_PATH = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"
PDF_PATH = ROOT / "input/cefr-companion-2020/source.pdf"
OUT = Path(__file__).resolve().parent / "_slices"

STOP = {
    "the", "a", "an", "of", "to", "and", "in", "for", "on", "or", "is", "are",
    "be", "as", "by", "with", "from", "this", "that", "at", "it", "can", "their",
    "they", "them", "than", "then", "when", "which", "who", "what", "how", "not",
    "have", "has", "had", "was", "were", "been", "being", "will", "would", "may",
    "might", "must", "shall", "should", "also", "into", "over", "such", "more",
    "most", "other", "some", "any", "all", "each", "both", "few", "own", "same",
    "page", "cefr", "companion", "volume", "illustrative", "descriptor", "scales",
    "communicative", "language", "activities", "strategies",
}


def page_bodies(md: str) -> dict[int, str]:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    marker_list = [(m.start(), m.end(), int(m.group(1))) for m in markers]
    out = {}
    for i, (s, e, p) in enumerate(marker_list):
        start = 0 if i == 0 else marker_list[i - 1][1]
        out[p] = md[start:s]
    return out


def content_words(t: str) -> set[str]:
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    t = re.sub(r"[|#>*_`\[\]()]", " ", t)
    return {
        w.lower()
        for w in re.findall(r"[A-Za-z']{3,}", t)
        if w.lower() not in STOP
    }


def pdf_content(page) -> str:
    txt = page.get_text("text")
    lines = []
    for ln in txt.splitlines():
        s = ln.strip()
        if not s:
            continue
        if re.match(r"^Page \d+", s):
            continue
        if s.startswith("The CEFR Illustrative"):
            continue
        if re.match(r"^CEFR", s) and "Companion" in s:
            continue
        lines.append(s)
    return "\n".join(lines)


def long_phrases(pdf_text: str, min_len: int = 50) -> list[str]:
    phrases = []
    for ln in pdf_text.splitlines():
        s = re.sub(r"\s+", " ", ln).strip()
        if len(s) >= min_len:
            phrases.append(s)
    return phrases


def main() -> None:
    md = MD_PATH.read_text(encoding="utf-8")
    bodies = page_bodies(md)
    pdf = fitz.open(PDF_PATH)
    OUT.mkdir(parents=True, exist_ok=True)

    for n in range(1, 50):
        body = bodies.get(n, "")
        neigh = body + bodies.get(n - 1, "") + bodies.get(n + 1, "")
        ptxt = pdf_content(pdf[n - 1])
        (OUT / f"page_{n:03d}.md").write_text(body, encoding="utf-8")
        (OUT / f"page_{n:03d}_pdf.txt").write_text(ptxt, encoding="utf-8")

        pw = content_words(ptxt)
        mw = content_words(body)
        mw_n = content_words(neigh)
        missing = sorted(pw - mw)
        missing_n = sorted(pw - mw_n)
        miss_pct = 100 * len(missing) / len(pw) if pw else 0
        miss_n_pct = 100 * len(missing_n) / len(pw) if pw else 0

        phrases = long_phrases(ptxt)
        miss_ph = []
        md_norm = re.sub(r"\s+", " ", body).lower()
        neigh_norm = re.sub(r"\s+", " ", neigh).lower()
        for ph in phrases:
            key = re.sub(r"\s+", " ", ph).lower()[:55]
            if key not in md_norm and key[:40] not in md_norm:
                if key not in neigh_norm and key[:40] not in neigh_norm:
                    miss_ph.append(ph[:100])

        has_pipe_table = bool(re.search(r"^\|.+\|$", body, re.M)) and "---" in body
        has_figure = "![" in body or "text_diagram" in body or "```text" in body
        has_bq = bool(re.search(r"^>", body, re.M))
        soup = []
        for m in re.finditer(r"```\s*\n", body):
            after = body[m.end() : m.end() + 300]
            for ln in after.splitlines():
                if not ln.strip():
                    continue
                if ln.startswith("<!--") or ln.startswith("#") or ln.startswith("*"):
                    break
                if re.match(
                    r"^(Reception|Production|Interaction|Mediation|Oral |Written |"
                    r"Online |Spoken |Signed |A1|A2|B1|B2|C1|C2|Pre-A1|"
                    r"activities|strategies)\b",
                    ln.strip(),
                    re.I,
                ):
                    soup.append(ln.strip()[:60])
                break

        body_core = re.sub(r"<!--.*?-->", "", body, flags=re.S)
        body_core = re.sub(r"\*[^\n]*Page[^\n]*\*", "", body_core).strip()
        chrome = len(body_core) <= 120
        captions = re.findall(r"\*[^\n]*Page \*\*\d+\*\*[^\n]*\*", body)

        flag = ""
        if miss_n_pct >= 25 or miss_ph or soup or (chrome and len(ptxt) > 200):
            flag = " **REVIEW**"

        print(
            f"p{n:03d} miss={miss_pct:4.0f}% neigh={miss_n_pct:4.0f}% "
            f"ph={len(miss_ph)} tab={int(has_pipe_table)} fig={int(has_figure)} "
            f"bq={int(has_bq)} soup={len(soup)} chrome={int(chrome)} "
            f"mdlen={len(body_core)} pdflen={len(ptxt)}{flag}"
        )
        if miss_ph[:3]:
            for p in miss_ph[:3]:
                print("   PH:", p)
        if soup:
            print("   SOUP:", soup)
        if miss_n_pct >= 25:
            print("   miss_words:", missing_n[:15])
        if captions:
            print("   cap:", captions[:1])


if __name__ == "__main__":
    main()
