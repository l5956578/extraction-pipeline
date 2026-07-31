#!/usr/bin/env python3
"""Fix p165 dual-emit; remove garbled reverse-text restores on p178-181."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD_PATH = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"

P165 = """
<!-- el:start type=artifact id=scale_language_awareness_p165_slice page=165 -->
<!-- book-qa: page-slice of multipage scale_language_awareness_and_interpretation (full on p164; pages=164-165) -->
### Language awareness and interpretation (continued)

| | Language awareness and interpretation |
| --- | --- |
| B2 | Can understand conveyed information that is implied, but not explicitly stated in a text (e.g., he went skiing, and I’ll visit him in hospital).<br>Can follow the main points of a text even when the signer also makes digressions.<br>Can recognise whether a signer is delivering a complex text in a relaxed or a tense way.<br>Can recognise whether the signer produces a text in a specific rhythm and describe the effect of various rhythms.<br>Can give reasons why the signer inserts pauses in a text, e.g., because they make sense as a structural element or because the signer has to reflect.<br>Can understand who has what opinion and how these opinions relate to each other.<br>Can recognise when a signer’s personal experiences influence the argumentation and when they do not. |
| | Can determine whether the signing style used is in keeping with the content.<br>Can decide on the basis of the interlocutor’s signs and non-manual cues how certain the signer is about what they are saying (e.g., <undecided> / <uncertain> / <probable>).<br>Can distinguish productive signs with classifier constructions from imitative, iconic signs.<br>Can follow the signs made by an interlocutor even when less use is made of non-manual means.<br>Can describe the effect that the sign speed of a text has on them.<br>Can judge whether a person presents themselves in a way that is in keeping with the context and the type of text concerned (clothing, aura, well-groomed appearance).<br>Can deduce the meaning of unfamiliar signs using comparisons and analogies. |
| B1 | Can understand the sequence of events from the sequence of statements made.<br>Can understand simple “for” and “against” arguments on a particular issue.<br>Can understand what advantages and disadvantages a text mentions on a subject.<br>Can understand the key aspects of conclusions.<br>Can recognise and correctly interpret important elements on the basis of non-manual components used for emphasis (e.g., facial expression, size of movement).<br>Can infer from the classifiers used what general term is being talked about (e.g., “murder” from the handling of a murder weapon).<br>Can distinguish between important and unimportant content in a text. |
| | Can infer the temporal aspect from the movements of the upper body.<br>Can understand a text so well that they are emotionally affected.<br>Can recognise the non-manual elements employed by a signer to produce tension in the text.<br>Can correctly interpret the <palm-up> sign (e.g., to indicate a pause).<br>Can recognise and understand non-manual markers.<br>Can understand explanations so that they can implement instructions. |
| A2 | Can understand an introduction to a subject and reproduce it in their own words.<br>Can grasp the signer’s opinion on a subject.<br>Can relate explanations and examples to one another.<br>Can interpret emotions when the signer communicates these by means of facial expressions. |
| | Can recognise whether or not they are addressed as the recipient.<br>Can understand the main points of signed texts on everyday topics<br>Can grasp and indicate the differences between things.<br>Can identify identical references even if these are expressed in different linguistic ways, e.g., by a lexical sign or by constructed action.<br>Can recognise unfamiliar signs in the continuous flow and ask what they mean. |
| A1 | Can distinguish between positive and negative attitudes on the basis of non-manual cues (e.g., eyebrows together v. high eyebrows).<br>Can understand the direct acceptance or rejection of requests/demands. |
<!-- el:end id=scale_language_awareness_p165_slice -->

*The CEFR Illustrative Descriptor Scales: Signing competences ▶ Page **165***
"""

CHROME = {
    178: "*Page **178** ▶ **CEFR – Companion volume***",
    179: "*Self-assessment grid (expanded with online interaction and mediation) ▶ Page **179***",
    180: "*Page **180** ▶ **CEFR – Companion volume***",
    181: "*Self-assessment grid (expanded with online interaction and mediation) ▶ Page **181***",
}


def replace_page_region(md: str, page: int, new_body: str) -> str:
    marker = f"<!-- page:{page} -->"
    idx = md.find(marker)
    if idx < 0:
        raise SystemExit(f"marker missing page {page}")
    prev = list(re.finditer(r"<!-- page:\d+ -->", md[:idx]))
    start = prev[-1].end() if prev else 0
    return md[:start] + "\n" + new_body.strip() + "\n\n" + md[idx:]


def page_body(md: str, n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return ""


def main() -> None:
    md = MD_PATH.read_text(encoding="utf-8")
    md = replace_page_region(md, 165, P165)
    for p, chrome in CHROME.items():
        md = replace_page_region(md, p, chrome)
    MD_PATH.write_text(md, encoding="utf-8")
    for n in (165, 178, 179, 180, 181):
        b = page_body(md, n)
        print(
            f"p{n} len={len(b)} garbled={'raelc' in b} "
            f"has_table={'|' in b and '---' in b}"
        )
    print("self-assess production present", "Production" in md)
    print("wrote", MD_PATH)


if __name__ == "__main__":
    main()
