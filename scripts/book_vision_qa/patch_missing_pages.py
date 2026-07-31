#!/usr/bin/env python3
"""Insert truly missing page content into the Companion deliverable MD."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"

P51 = r"""
<!-- el:start type=prose id=prose_p051_announcements_intro page=51 -->
### Understanding announcements and instructions

This scale involves a different type of extremely focused comprehension in which the aim is to catch specific information. The situation is complicated by the fact that the announcement or instructions may well be delivered by a (possibly faulty) public address system, or called out/signed some considerable distance away. Key concepts operationalised in the scale include the following:

- understanding directions and detailed instructions;
- catching the main point of announcements;
- degree of clarity, from slow and clear to normal speed with audio and/or visual distortion.
<!-- el:end id=prose_p051_announcements_intro -->

<!-- el:start type=artifact id=scale_understanding_announcements_and_instructions page=51 -->
<!-- db:id=scale_understanding_announcements_and_instructions type=descriptor_scale product_tier=assessment_action,detailed pages=51 -->
### Understanding announcements and instructions | scale_understanding_announcements_and_instructions

| | Understanding announcements and instructions |
| --- | --- |
| C2 | No descriptors available; see C1 |
| C1 | Can extract specific information from poor quality, [audibly and/or visually] distorted public announcements, e.g. in a station or sports stadium, or on an old recording.<br>Can understand complex technical information, such as operating instructions or specifications for familiar products and services. |
| B2 | Can understand announcements and messages on concrete and abstract topics delivered in standard language or a familiar variety at normal speed.<br>Can understand detailed instructions well enough to be able to follow them successfully. |
| B1 | Can understand simple technical information, such as operating instructions for everyday equipment.<br>Can follow detailed directions.<br>Can understand public announcements at airports, stations and on planes, buses and trains, provided these are clearly articulated with minimum interference from [auditory/visual] background noise. |
| A2 | Can understand and follow a series of instructions for familiar everyday activities such as sports, cooking, etc., provided they are delivered slowly and clearly.<br>Can understand straightforward announcements (e.g. of a cinema programme or sports event, that a train has been delayed), provided the delivery is slow and clear.<br>Can catch the main point in short, clear, simple messages and announcements.<br>Can understand simple directions on how to get from X to Y, by foot or public transport.<br>Can understand basic instructions on times, dates and numbers, etc., and on routine tasks and assignments to be carried out. |
| A1 | Can understand instructions addressed carefully and slowly to them and follow short, simple directions.<br>Can understand when someone tells them slowly and clearly where something is, provided the object is in the immediate environment.<br>Can understand figures, prices and times given slowly and clearly in an announcement by loudspeaker, e.g. at a railway station or in a shop. |
| Pre-A1 | Can understand short, simple instructions for actions such as “Stop”, “Close the door”, etc., provided they are delivered slowly face-to-face, accompanied by pictures or manual gestures and repeated if necessary. |
<!-- el:end id=scale_understanding_announcements_and_instructions -->

"""

P131 = r"""
<!-- el:start type=prose id=prose_p131_vocabulary_range page=131 -->
### Vocabulary range

This scale concerns the breadth and variety of expressions used. It is generally acquired through reading widely. Key concepts operationalised in the scale include the following:

- range of settings – from A1 to B2, then unrestricted;
- type of language: from a basic repertoire of words/signs and phrases to a very broad lexical repertoire including idiomatic expressions and colloquialisms.

Note: Vocabulary range is taken to apply to both reception and production. For sign languages, established and productive vocabulary is implied from A2+ to C2, with established vocabulary at A1 and A2.
<!-- el:end id=prose_p131_vocabulary_range -->

<!-- el:start type=artifact id=scale_vocabulary_range page=131 -->
<!-- db:id=scale_vocabulary_range type=descriptor_scale product_tier=assessment_action,detailed pages=131-132 -->
### Vocabulary range | scale_vocabulary_range

| | Vocabulary range |
| --- | --- |
| C2 | Has a good command of a very broad lexical repertoire including idiomatic expressions and colloquialisms; shows awareness of connotative levels of meaning. |
| C1 | Has a good command of a broad lexical repertoire allowing gaps to be readily overcome with circumlocutions; little obvious searching for expressions or avoidance strategies.<br>Can select from several vocabulary options in almost all situations by exploiting synonyms of even words/signs less commonly encountered.<br>Has a good command of common idiomatic expressions and colloquialisms; can play with words/signs fairly well.<br>Can understand and use appropriately the range of technical vocabulary and idiomatic expressions common to their area of specialisation. |
| B2 | Can understand and use the main technical terminology of their field, when discussing their area of specialisation with other specialists.<br>Has a good range of vocabulary for matters connected to their field and most general topics.<br>Can vary formulation to avoid frequent repetition, but lexical gaps can still cause hesitation and circumlocution. |
| B1 | Has a good range of vocabulary related to familiar topics and everyday situations.<br>Has sufficient vocabulary to express themselves with some circumlocutions on most topics pertinent to their everyday life such as family, hobbies and interests, work, travel, and current events. |
| A2 | Has sufficient vocabulary to conduct routine, everyday transactions involving familiar situations and topics.<br>Has a sufficient vocabulary for the expression of basic communicative needs.<br>Has a sufficient vocabulary for coping with simple survival needs. |
| A1 | Has a basic vocabulary repertoire of words/signs and phrases related to particular concrete situations. |
| Pre-A1 | No descriptors available |
<!-- el:end id=scale_vocabulary_range -->

"""


def inject_before_page_marker(md: str, page: int, block: str, chrome_hint: str) -> str:
    """Replace chrome-only region before <!-- page:N --> with block + chrome."""
    marker = f"<!-- page:{page} -->"
    idx = md.find(marker)
    if idx < 0:
        raise SystemExit(f"marker not found page {page}")
    # walk back to previous page marker end
    prev = list(re.finditer(r"<!-- page:\d+ -->", md[:idx]))
    start = prev[-1].end() if prev else 0
    region = md[start:idx]
    if chrome_hint not in region and len(region.strip()) > 200:
        # already has content?
        if f"page={page}" in region or f"pages={page}" in region:
            print(f"p{page}: already has content, skip")
            return md
    new_region = "\n" + block.strip() + "\n\n" + region.lstrip()
    if not new_region.endswith("\n\n"):
        new_region = new_region.rstrip() + "\n\n"
    return md[:start] + new_region + md[idx:]


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    if "scale_understanding_announcements_and_instructions" not in md:
        md = inject_before_page_marker(
            md, 51, P51, "Page **51**"
        )
        print("inserted p51 announcements")
    else:
        print("p51 already has announcements scale")
    if "scale_vocabulary_range" not in md or "breadth and variety of expressions" not in md:
        # only inject if truly missing intro
        if "breadth and variety of expressions" not in md:
            md = inject_before_page_marker(md, 131, P131, "Page **131**")
            print("inserted p131 vocabulary range")
        else:
            print("vocab intro exists")
    else:
        print("p131 vocabulary range present")
    MD.write_text(md, encoding="utf-8")
    print("wrote", MD, "size", MD.stat().st_size)


if __name__ == "__main__":
    main()
