#!/usr/bin/env python3
"""Rebuild p.275 sales agents from PDF line extract (multi-column soup fix)."""

from __future__ import annotations

import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "input/cefr-companion-2020/source.pdf"
MD = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"

COUNTRY = re.compile(
    r"^(?:"
    r"[A-Z][A-Z /ÉÈÊÀÂÔÙÛÇ\-]+"
    r"(?:/[A-ZÉÈÊÀÂÔÙÛÇ \-]+)?"
    r")$"
)


def replace_page(md: str, page: int, new_body: str) -> str:
    marker = f"<!-- page:{page} -->"
    idx = md.find(marker)
    prev = list(re.finditer(r"<!-- page:\d+ -->", md[:idx]))
    start = prev[-1].end() if prev else 0
    return md[:start] + "\n" + new_body.strip() + "\n\n" + md[idx:]


def main() -> None:
    doc = fitz.open(PDF)
    lines = [ln.strip() for ln in doc[274].get_text().splitlines() if ln.strip()]
    parts = [
        "<!-- el:start type=prose id=prose_p275_s0 page=275 -->",
        "**Sales agents for publications of the Council of Europe**",
        "",
        "*Agents de vente des publications du Conseil de l’Europe*",
        "",
    ]
    # skip bilingual titles already emitted
    i = 0
    while i < len(lines) and (
        "Sales agents" in lines[i] or "Agents de vente" in lines[i]
    ):
        i += 1
    buf: list[str] = []
    while i < len(lines):
        ln = lines[i]
        # country headers: all caps with optional slash bilingual
        is_country = bool(re.match(r"^[A-ZÉÈÊÀÂÔÙÛÇ][A-ZÉÈÊÀÂÔÙÛÇ /'\-]{2,}$", ln)) and not ln.startswith(
            ("TEL", "FAX", "HTTP", "WWW", "PO BOX", "C/O")
        )
        # refine: has mostly uppercase letters
        letters = [c for c in ln if c.isalpha()]
        upper_ratio = (sum(1 for c in letters if c.isupper()) / len(letters)) if letters else 0
        is_country = is_country and upper_ratio > 0.85 and len(ln) < 50
        if is_country and buf:
            parts.append("\n".join(buf))
            parts.append("")
            buf = []
        if is_country:
            parts.append(f"**{ln}**")
        else:
            buf.append(ln)
        i += 1
    if buf:
        parts.append("\n".join(buf))
        parts.append("")
    parts.append("<!-- el:end id=prose_p275_s0 -->")
    parts.append("")
    parts.append("*Page **275***")
    body = "\n".join(parts)
    md = MD.read_text(encoding="utf-8")
    md = replace_page(md, 275, body)
    MD.write_text(md, encoding="utf-8")
    print("p275 countries", body.count("**"))
    print("belgium", "BELGIUM" in body)
    print("sample", body[:500])


if __name__ == "__main__":
    main()
