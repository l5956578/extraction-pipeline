#!/usr/bin/env python3
"""Fix known glue artifacts in Companion MD (countries, notes, bold spacing)."""

from __future__ import annotations

import re
from pathlib import Path

MD = Path(__file__).resolve().parents[2] / "output/cefr-companion-2020/CEFR_Companion_Volume.md"

FIXES = [
    (
        "Departament d'EnsenyamentGeneralitat de Catalunya",
        "Departament d'Ensenyament, Generalitat de Catalunya",
    ),
    (
        "Departament d’EnsenyamentGeneralitat de Catalunya",
        "Departament d’Ensenyament, Generalitat de Catalunya",
    ),
    ("**2.10.2. Books**Bourguignon", "**2.10.2. Books**\n\nBourguignon"),
    ("**Note:**What", "**Note:** What"),
    ("**Note:** What", "**Note:** What"),  # idempotent
    ("**SOURCES FOR NEW DESCRIPTORS**Abbe", "**SOURCES FOR NEW DESCRIPTORS**\n\nAbbe"),
    ("**Turkey**Çağ", "**Turkey**\nÇağ"),
    ("Can make use of**different languages", "Can make use of **different languages"),
    (
        "in their plurilingual repertoire**during collaborative",
        "in their plurilingual repertoire** during collaborative",
    ),
]


def fix_country_glue(md: str) -> tuple[str, int]:
    """Insert newline between '...place**Country**' glued pairs."""
    # e.g. Paz**Bosnia and Herzegovina**
    pattern = re.compile(
        r"([a-zà-ÿA-Z\)\.])(\*\*(?:[A-ZÀ-ÿ][^*]{1,40})\*\*)"
    )
    n = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal n
        left, country = m.group(1), m.group(2)
        # skip if already newline context handled; only glue if no whitespace
        n += 1
        return f"{left}\n\n{country}"

    # Only apply when **Country** is immediately after non-space (true glue)
    md2, count = re.subn(
        r"(?<=\S)(\*\*(?:Algeria|Argentina|Bolivia|Bosnia and Herzegovina|Brazil|Bulgaria|"
        r"Cameroon|Canada|Chile|China|Colombia|Croatia|Cyprus|Czech Republic|Egypt|Estonia|"
        r"Finland|France|Germany|Greece|Hungary|India|Ireland|Italy|Japan|Latvia|Lebanon|"
        r"Lithuania|Luxembourg|Mexico|Morocco|Netherlands|New Zealand|North Macedonia|"
        r"Norway|Peru|Poland|Portugal|Romania|Russia|Saudi Arabia|Senegal|Serbia|Slovakia|"
        r"Slovenia|Spain|Sweden|Switzerland|Thailand|Turkey|Uganda|Ukraine|"
        r"United Arab Emirates|United Kingdom|United States|Uruguay|Venezuela|"
        r"[A-Z][a-zA-Z\- ]{2,30})\*\*)",
        r"\n\n\1",
        md,
    )
    return md2, count


def fix_bold_spacing(md: str) -> tuple[str, int]:
    """word**bold**word → word **bold** word (conservative)."""
    n = 0

    def left(m: re.Match[str]) -> str:
        nonlocal n
        n += 1
        return f"{m.group(1)} **{m.group(2)}**"

    md, c1 = re.subn(r"([a-zà-ÿ])\*\*([^*]{2,80})\*\*", left, md)

    def right(m: re.Match[str]) -> str:
        nonlocal n
        n += 1
        return f"**{m.group(1)}** {m.group(2)}"

    # **bold**Word where Word is uppercase start (likely new sentence/heading)
    md, c2 = re.subn(r"\*\*([^*]{2,80})\*\*([A-ZÀ-ÿ][a-zà-ÿ])", right, md)
    return md, c1 + c2


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    for a, b in FIXES:
        c = md.count(a)
        if c:
            md = md.replace(a, b)
            print(f"literal {c}x: {a[:50]!r}")

    md, n_country = fix_country_glue(md)
    print("country_glue_inserts", n_country)

    # targeted real glues still present
    extra = [
        (r"La Paz\*\*Bosnia", "La Paz\n\n**Bosnia"),
        (r"\*\*Bosnia and Herzegovina\*\*", "**Bosnia and Herzegovina**"),
    ]
    # fix Note: without space more broadly
    md, n_note = re.subn(r"\*\*Note:\*\*(\S)", r"**Note:** \1", md)
    print("note_space", n_note)

    # bibliography heading glue **TITLE**Author
    md, n_bib = re.subn(
        r"(\*\*[A-Z][^*]{5,80}\*\*)([A-Z][a-zà-ÿ]+ [A-Z]\.)",
        r"\1\n\n\2",
        md,
    )
    print("bib_glue", n_bib)

    # section title glued to body: **Explaining data**This → split only if next is capital sentence
    # skip — too risky

    MD.write_text(md, encoding="utf-8")
    # verify samples
    text = MD.read_text(encoding="utf-8")
    for s in [
        "Ensenyament, Generalitat",
        "La Paz**Bosnia",
        "**Note:** What",
        "**2.10.2. Books**\n\nBourguignon",
        "make use of **different",
    ]:
        print("check", repr(s), "->", s in text or s.replace("\\n", "\n") in text)


if __name__ == "__main__":
    main()
